#!/usr/bin/env python3
"""cari-momen: pindai SELURUH live/VOD YouTube Windah lalu beri daftar kandidat momen.

Cara kerjanya meniru ide Clips Kitty (github.com/ColinGPT9/clips-studio, AGPL) - kodenya
ditulis ulang, tidak disalin:
  1. Sinyal per detik di sepanjang video, diukur RELATIF terhadap video ini sendiri
     (persentil), jadi stream yang selalu berisik tetap punya puncak:
       - audio: lonjakan keras vs median 30 dtk sekitarnya + kepadatan "onset" (tawa/teriak)
       - chat replay: ledakan pesan (penulis unik) vs 45 dtk sebelumnya, digeser 6 dtk ke
         belakang (chat telat), plus JENIS reaksinya (lucu/epic/gagal/sus/minta klip)
       - heatmap "paling sering diputar ulang" YouTube (bila ada)
  2. Kandidat = puncak sinyal gabungan (berjarak >= 90 dtk), lengkap dengan transkrip
     konteks 90 dtk sebelum s.d. 30 dtk sesudahnya.
  3. timeline.txt = transkrip per menit yang ditandai kejadian (SUARA/CHAT) supaya juri
     (Claude) juga bisa menemukan momen yang sinyalnya biasa tapi ucapannya kuat.
Penilaian akhir (skor, rerank, tanda sensitif) dilakukan Claude - lihat SKILL.md.

Pakai: cari_momen.py URL FOLDER [--top 15]
Unduhan ringan: audio saja (kualitas rendah), subtitle otomatis id, chat replay, info JSON.
"""
import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np

SR = 8000           # audio cukup 8 kHz untuk energi
FRAME = SR // 20    # 50 ms
CHAT_LAG = 6        # chat bereaksi ~6 dtk setelah kejadian
JENDELA, DASAR = 5, 45
JARAK_KANDIDAT = 90

KELAS_CHAT = {
    "lucu": ["wkwk", "awkwk", "kwkw", "kekw", "lul", "lol", "ngakak", "kocak", "😂", "🤣", "haha"],
    "epic": ["gg", "gila", "anjir", "anjay", "pog", "keren", "goat", "🔥"],
    "gagal": ["f", "l", "rip", "ngakak mati", "💀", "kasian", "kasihan"],
    "sus": ["🤨", "sus", "sensor", "astagfirullah", "astaghfirullah", "😳"],
    "minta klip": ["clip", "klip", "jadiin short", "clipper"],
}
# kata pendek yang harus cocok utuh (bukan potongan kata lain); sisanya cukup terkandung
KATA_UTUH = {"f", "l", "gg", "lol", "lul", "rip", "sus", "pog", "goat"}


def jam(t):
    t = int(t)
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}"


def menit(t):
    """'jam 3 menit 26 detik 40' - format yang diminta pengguna untuk daftar kandidat."""
    t = int(t)
    return f"jam {t // 3600} menit {t % 3600 // 60} detik {t % 60}"


# ---------------------------------------------------------------- unduh
def unduh(url, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    info_p = out / "live.info.json"
    if not info_p.exists():
        subprocess.run(["yt-dlp", "--skip-download", "--write-info-json", "-o", str(out / "live.%(ext)s"), url],
                       check=True)
    info = json.loads(info_p.read_text(encoding="utf-8"))
    if not list(out.glob("live.id*.vtt")):
        subprocess.run(["yt-dlp", "--skip-download", "--write-subs", "--write-auto-subs", "--sub-langs", "id",
                        "--sub-format", "vtt", "-o", str(out / "live.%(ext)s"), url])
    if not (out / "live.live_chat.json").exists():
        print("Mengunduh chat replay (live panjang bisa 10-30 menit)...", file=sys.stderr)
        subprocess.run(["yt-dlp", "--skip-download", "--write-subs", "--sub-langs", "live_chat",
                        "-o", str(out / "live.%(ext)s"), url])
    if not list(out.glob("live.audio.*")):
        print("Mengunduh audio (kualitas rendah, cukup untuk sinyal)...", file=sys.stderr)
        subprocess.run(["yt-dlp", "-f", "worstaudio[acodec!=none]/bestaudio", "-o", str(out / "live.audio.%(ext)s"),
                        url], check=True)
    return info


# ---------------------------------------------------------------- audio
def fitur_audio(path: Path, durasi: int):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         stdout=subprocess.PIPE)
    rms = []
    blok = SR * 60 * 2
    sisa = b""
    while True:
        data = p.stdout.read(blok)
        if not data:
            break
        data = sisa + data
        n = len(data) // (FRAME * 2) * FRAME * 2
        sisa = data[n:]
        a = np.frombuffer(data[:n], dtype=np.int16).astype(np.float32) / 32768
        rms.append(np.sqrt((a.reshape(-1, FRAME) ** 2).mean(axis=1)))
    p.wait()
    fr = np.concatenate(rms) if rms else np.zeros(1)
    n = len(fr) // 20
    per = fr[: n * 20].reshape(n, 20)
    keras = per.mean(axis=1)
    db = 20 * np.log10(keras + 1e-6)
    med = median_bergulir(db, 30)
    lonjak = np.clip(db - med, 0, 20)
    onset = np.concatenate([[False], fr[1:] > 2.0 * np.maximum(fr[:-1], 1e-4)])
    ledak = onset[: n * 20].reshape(n, 20).sum(axis=1).astype(np.float32)
    return pad(lonjak, durasi), pad(ledak, durasi), pad(db - np.median(db), durasi)


def median_bergulir(x, w):
    h = w // 2
    return np.array([np.median(x[max(0, i - h): i + h + 1]) for i in range(len(x))])


def pad(x, n):
    y = np.zeros(n, dtype=np.float32)
    m = min(n, len(x))
    y[:m] = x[:m]
    return y


# ---------------------------------------------------------------- chat
def baca_chat(path: Path):
    pesan = []  # (detik, penulis, teks)
    if not path.exists():
        return pesan
    for baris in path.open(encoding="utf-8"):
        try:
            d = json.loads(baris)
        except ValueError:
            continue
        r = d.get("replayChatItemAction", {})
        t = int(r.get("videoOffsetTimeMsec", 0)) / 1000
        for act in r.get("actions", []):
            item = act.get("addChatItemAction", {}).get("item", {})
            m = item.get("liveChatTextMessageRenderer") or item.get("liveChatPaidMessageRenderer")
            if not m:
                continue
            teks = ""
            for run in m.get("message", {}).get("runs", []):
                if "text" in run:
                    teks += run["text"]
                elif "emoji" in run:
                    e = run["emoji"]
                    teks += e.get("emojiId", "") if len(e.get("emojiId", "")) <= 2 else \
                        " " + (e.get("shortcuts") or [""])[0] + " "
            pesan.append((t, m.get("authorExternalChannelId", ""), teks.strip()))
    return pesan


def kelas_pesan(teks):
    low = teks.lower()
    kata = set(re.findall(r"[a-z]+", low))
    hasil = []
    for k, daftar in KELAS_CHAT.items():
        for w in daftar:
            if (w in KATA_UTUH and w in kata) or (w not in KATA_UTUH and w in low):
                hasil.append(k)
                break
    return hasil


def sinyal_chat(pesan, durasi):
    unik = [set() for _ in range(durasi)]
    for t, a, _ in pesan:
        i = int(t) - CHAT_LAG
        if 0 <= i < durasi:
            unik[i].add(a)
    cnt = np.array([len(s) for s in unik], dtype=np.float32)
    cs = np.concatenate([[0], np.cumsum(cnt)])
    rasio = np.zeros(durasi, dtype=np.float32)
    for i in range(durasi):
        b = min(durasi, i + JENDELA)
        now = cs[b] - cs[i]
        a0 = max(0, i - DASAR)
        base = (cs[i] - cs[a0]) / max(1, i - a0) * JENDELA
        if now >= 4:
            rasio[i] = now / max(base, 1.0)
    return cnt, rasio


# ---------------------------------------------------------------- transkrip
def baca_vtt(path):
    if path is None:
        return []
    t = path.read_text(encoding="utf-8")
    seen, out = set(), []
    for b in t.split("\n\n"):
        m = re.search(r"(\d+):(\d+):(\d+\.\d+) -->", b)
        if not m:
            continue
        s = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
        for l in b.split("\n")[1:]:
            l = re.sub(r"<[^>]+>", "", l).strip()
            if l and "-->" not in l and l not in seen:
                seen.add(l)
                out.append((s, l))
    return out


def teks_antara(tr, a, b):
    return " ".join(x for s, x in tr if a <= s < b)


# ---------------------------------------------------------------- gabung
def persentil(x):
    if x.max() <= 0:
        return np.zeros_like(x)
    order = x.argsort().argsort().astype(np.float32)
    p = order / max(1, len(x) - 1)
    p[x <= 0] = 0
    return p


def halus(x, w):
    return np.convolve(x, np.ones(w) / w, mode="same")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("folder")
    ap.add_argument("--top", type=int, default=15)
    a = ap.parse_args()
    out = Path(a.folder)
    info = unduh(a.url, out)
    durasi = int(info.get("duration") or 0)
    if "windah" not in (info.get("uploader", "") + info.get("channel", "")).lower():
        print(f"PERINGATAN: uploader '{info.get('uploader')}' bukan channel Windah Basudara.", file=sys.stderr)

    audio_p = next(out.glob("live.audio.*"))
    print("Menghitung sinyal audio...", file=sys.stderr)
    lonjak, ledak, db_rel = fitur_audio(audio_p, durasi)
    pesan = baca_chat(out / "live.live_chat.json")
    cnt, rasio = sinyal_chat(pesan, durasi)
    heat = np.zeros(durasi, dtype=np.float32)
    for h in info.get("heatmap") or []:
        heat[int(h["start_time"]):int(h["end_time"]) + 1] = h["value"]
    tr = baca_vtt(next(iter(sorted(out.glob("live.id*.vtt"))), None))

    s_audio = halus(np.maximum(persentil(lonjak), persentil(ledak)), 3)
    s_chat = halus(persentil(rasio), 5)
    s_heat = persentil(heat) if heat.max() > 0 else None
    bobot = {"audio": 0.45, "chat": 0.40 if pesan else 0.0, "heat": 0.15 if s_heat is not None else 0.0}
    tot = sum(bobot.values())
    gab = (bobot["audio"] * s_audio + bobot["chat"] * s_chat +
           (bobot["heat"] * s_heat if s_heat is not None else 0)) / tot
    gab = halus(gab, 5)

    # kelas chat per detik (sudah digeser lag)
    kelas = [Counter() for _ in range(durasi)]
    for t, _, teks in pesan:
        i = int(t) - CHAT_LAG
        if 0 <= i < durasi:
            for k in kelas_pesan(teks):
                kelas[i][k] += 1

    ambang = np.percentile(gab, 85)
    dipilih = []
    for i in np.argsort(-gab):
        if gab[i] < ambang or len(dipilih) >= a.top:
            break
        if i < 30 or i > durasi - 20:
            continue
        if all(abs(int(i) - d) >= JARAK_KANDIDAT for d in dipilih):
            dipilih.append(int(i))

    kandidat = []
    for p in sorted(dipilih):
        k = Counter()
        for j in range(max(0, p - 10), min(durasi, p + 20)):
            k.update(kelas[j])
        contoh = Counter(x.lower() for t, _, x in pesan if p - 10 <= t - CHAT_LAG < p + 20 and 0 < len(x) <= 40)
        kandidat.append({
            "puncak": jam(p), "puncak_menit": menit(p), "puncak_detik": p,
            "skor_sinyal": round(float(gab[p]) * 100),
            "audio": round(float(s_audio[max(0, p - 5):p + 5].max()) * 100),
            "chat": round(float(s_chat[max(0, p - 5):p + 5].max()) * 100),
            "heatmap": round(float(s_heat[p]) * 100) if s_heat is not None else None,
            "suara_db_di_atas_median": round(float(db_rel[max(0, p - 5):p + 5].max()), 1),
            "chat_penulis_unik_30dtk": int(cnt[max(0, p - 10):p + 20].sum()),
            "chat_kelas": dict(k.most_common()),
            "chat_contoh": [m for m, _ in contoh.most_common(8)],
            "konteks_mulai": jam(max(0, p - 90)), "konteks_selesai": jam(min(durasi, p + 30)),
            "transkrip_sebelum": teks_antara(tr, p - 90, p - 10),
            "transkrip_puncak": teks_antara(tr, p - 10, p + 30),
        })

    # timeline per menit untuk dibaca juri
    with (out / "timeline.txt").open("w", encoding="utf-8") as f:
        f.write(f"# {info.get('title')} | {info.get('uploader')} | {jam(durasi)}\n")
        f.write("# Tanda: [SUARA +dB] lonjakan suara, [CHAT n: kelas] ledakan chat, [*] puncak kandidat\n")
        for m0 in range(0, durasi, 60):
            m1 = min(durasi, m0 + 60)
            tanda = []
            d = float(db_rel[m0:m1].max()) if m1 > m0 else 0
            if d >= 9:
                tanda.append(f"[SUARA +{d:.0f}dB @{jam(m0 + int(db_rel[m0:m1].argmax()))}]")
            if pesan and rasio[m0:m1].max() >= 3:
                kk = Counter()
                for j in range(m0, m1):
                    kk.update(kelas[j])
                ks = ",".join(f"{x}:{n}" for x, n in kk.most_common(3))
                tanda.append(f"[CHAT x{rasio[m0:m1].max():.0f} @{jam(m0 + int(rasio[m0:m1].argmax()))} {ks}]")
            if any(m0 <= p < m1 for p in dipilih):
                tanda.append("[*]")
            f.write(f"[{jam(m0)}] {' '.join(tanda)} {teks_antara(tr, m0, m1)}\n")

    hasil = {"video": info.get("webpage_url"), "judul": info.get("title"), "uploader": info.get("uploader"),
             "durasi": jam(durasi), "jumlah_chat": len(pesan), "ada_heatmap": s_heat is not None,
             "bobot": bobot, "kandidat": kandidat, "timeline": str(out / "timeline.txt")}
    (out / "kandidat.json").write_text(json.dumps(hasil, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in hasil.items() if k != "kandidat"}, ensure_ascii=False))
    for c in kandidat:
        print(f"{c['puncak']} = {c['puncak_menit']}  sinyal {c['skor_sinyal']:3d}  audio {c['audio']:3d} chat {c['chat']:3d}  "
              f"{c['chat_kelas']}  | {c['transkrip_puncak'][:90]}")


if __name__ == "__main__":
    main()
