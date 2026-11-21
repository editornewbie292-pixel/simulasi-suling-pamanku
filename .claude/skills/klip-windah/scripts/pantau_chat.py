"""Pantau live chat YouTube (YouTube Data API v3) dan tandai lonjakan yang berpotensi jadi momen klip.

API key TIDAK ada di skrip: proxy environment menyisipkan header X-Goog-Api-Key untuk www.googleapis.com
(Network secrets). Jalankan:  python3 -I pantau_chat.py VIDEO_ID_ATAU_URL [--jendela 20] [--keluar folder]

Tiap jendela (bawaan 20 dtk) dihitung: kecepatan chat vs rata-rata bergerak, pesan yang sama dari banyak orang,
tawa (wkwk/haha/emoji), dan kata yang mendadak naik dibanding biasanya (pola dipelajari dari chat itu sendiri).
Baris "MOMEN ..." dicetak saat skor tinggi -> dipantau Claude (Monitor) lalu dikirim sebagai notifikasi.
Semua jendela juga disimpan ke <keluar>/chat_<id>.jsonl untuk dianalisis setelah live.
"""
import argparse
import collections
import json
import math
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://www.googleapis.com/youtube/v3/"
TAWA = re.compile(r"(wk){2,}|(ha){2,}|(he){3,}|(xi){2,}|😂|🤣|😹|ngakak|kocak|lol\b|lmao", re.I)
KATA_PANTAU = {
    "sus": ["sus", "🤨", "😳", "🥵", "astaghfirullah", "astagfirullah", "istighfar", "dosa", "nakal", "sensor",
            "18+", "tobat", "bahaya", "aduh bang", "bang?", "hah?", "eh"],
    "gagal": ["wasted", "mati", "rip", "f ", "gg", "skill issue", "noob", "ampas", "nyungsep", "jatoh", "jatuh"],
    "wow": ["gila", "anjir", "anjay", "bjir", "buset", "keren", "gokil", "wow", "goat", "🔥", "😱"],
    "banding": ["beda", "streamer lain", "miawaug", "reza", "jess", "speed", "kayak", "mirip", "sama kayak"],
}


def api(path, **q):
    url = API + path + "?" + urllib.parse.urlencode(q)
    req = urllib.request.Request(url, headers={"User-Agent": "klip-windah-pantau/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        isi = e.read().decode("utf-8", "replace")[:400]
        raise SystemExit(f"API error {e.code}: {isi}\n(403 'API key not valid/missing' = key belum disimpan di "
                         f"Network secrets atau YouTube Data API v3 belum diaktifkan)")


def video_id(s):
    m = re.search(r"(?:v=|/live/|youtu\.be/|/shorts/)([A-Za-z0-9_-]{11})", s)
    return m.group(1) if m else s


def norm(t):
    t = t.lower()
    t = re.sub(r"(.)\1{2,}", r"\1\1", t)  # "wkwkwkwk"/"anjirrrr" -> dipendekkan
    return re.sub(r"\s+", " ", t).strip()


def jam(detik):
    detik = max(0, int(detik))
    return f"{detik // 3600:d}:{detik % 3600 // 60:02d}:{detik % 60:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--jendela", type=float, default=20.0)
    ap.add_argument("--keluar", default="hasil-klip/pantau_live")
    ap.add_argument("--ambang", type=float, default=3.0, help="skor minimal untuk baris MOMEN")
    a = ap.parse_args()
    vid = video_id(a.video)
    out = Path(a.keluar)
    out.mkdir(parents=True, exist_ok=True)
    log = (out / f"chat_{vid}.jsonl").open("a", encoding="utf-8")

    v = api("videos", part="liveStreamingDetails,snippet", id=vid)
    if not v.get("items"):
        raise SystemExit("Video tidak ditemukan.")
    it = v["items"][0]
    lsd = it.get("liveStreamingDetails", {})
    chat_id = lsd.get("activeLiveChatId")
    if not chat_id:
        raise SystemExit("Live chat tidak aktif (live belum mulai / sudah selesai).")
    mulai = lsd.get("actualStartTime")
    t_mulai = datetime.fromisoformat(mulai.replace("Z", "+00:00")).timestamp() if mulai else time.time()
    print(f"Memantau: {it['snippet']['title']} | mulai {mulai} | jendela {a.jendela:.0f} dtk", flush=True)

    token = None
    seen = set()
    rate_hist = collections.deque(maxlen=45)  # ~15 menit
    df = collections.Counter()  # frekuensi kata (berapa jendela memuatnya) -> "kata biasa" vs lonjakan
    n_jendela = 0
    buf = []
    t_jendela = time.time()
    while True:
        r = api("liveChat/messages", liveChatId=chat_id, part="snippet,authorDetails", maxResults=2000,
                **({"pageToken": token} if token else {}))
        token = r.get("nextPageToken")
        for m in r.get("items", []):
            if m["id"] in seen:
                continue
            seen.add(m["id"])
            sn = m["snippet"]
            teks = sn.get("displayMessage") or sn.get("textMessageDetails", {}).get("messageText", "")
            ts = datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00")).timestamp()
            buf.append((ts, m["authorDetails"].get("channelId", ""), teks))
        if len(seen) > 20000:
            seen = set(list(seen)[-5000:])

        if time.time() - t_jendela >= a.jendela and buf:
            t_jendela = time.time()
            pesan, buf = buf, []
            n_jendela += 1
            rate = len(pesan) / a.jendela
            base = sorted(rate_hist)[len(rate_hist) // 2] if rate_hist else rate
            rate_hist.append(rate)
            # pesan sama dari banyak orang
            sama = collections.defaultdict(set)
            for _, au, t in pesan:
                sama[norm(t)].add(au)
            top_sama = sorted(((len(s), t) for t, s in sama.items() if len(t) > 1), reverse=True)[:3]
            tawa = sum(1 for *_, t in pesan if TAWA.search(t)) / max(1, len(pesan))
            kat = {k: sum(1 for *_, t in pesan if any(w in t.lower() for w in ws)) for k, ws in KATA_PANTAU.items()}
            # kata yang mendadak naik (dipelajari dari chat ini sendiri)
            kata_j = collections.Counter(w for *_, t in pesan for w in set(re.findall(r"[\w\U0001F300-\U0001FAFF]+", norm(t))))
            naik = []
            for w, c in kata_j.items():
                frac = c / len(pesan)
                biasa = df[w] / max(1, n_jendela - 1)
                if c >= 3 and frac > 0.08 and frac > 4 * max(biasa * 0.05, 0.01):
                    naik.append((round(frac, 2), w))
            for w in kata_j:
                df[w] += 1
            naik.sort(reverse=True)
            z_rate = (rate - base) / max(0.15, base * 0.35)
            skor = max(0.0, z_rate) + 4 * tawa + (top_sama[0][0] / 4 if top_sama else 0) + 0.6 * len(naik[:3])
            skor += 0.5 * min(4, kat["sus"]) + 0.3 * min(4, kat["gagal"])
            t_awal = min(p[0] for p in pesan)
            rec = {"jam_live": jam(t_awal - t_mulai), "detik_live": round(t_awal - t_mulai), "pesan": len(pesan),
                   "kecepatan": round(rate, 2), "dasar": round(base, 2), "tawa": round(tawa, 2), "kategori": kat,
                   "sama": top_sama, "naik": naik[:5], "skor": round(skor, 1),
                   "contoh": [t for *_, t in pesan[:6]]}
            log.write(json.dumps(rec, ensure_ascii=False) + "\n")
            log.flush()
            if skor >= a.ambang and n_jendela > 3:
                jenis = max(kat, key=kat.get) if max(kat.values()) else ("lucu" if tawa > 0.2 else "rame")
                # chat telat ±10-30 dtk dari kejadian -> usul rekam mulai 60 dtk sebelum jendela
                print(f"MOMEN {rec['jam_live']} skor {rec['skor']} [{jenis}] chat {rate:.1f}/dtk (biasa {base:.1f}) "
                      f"tawa {tawa:.0%} sama {top_sama[:2]} naik {[w for _, w in naik[:3]]} "
                      f"| rekam {jam(t_awal - t_mulai - 60)}-{jam(t_awal - t_mulai + 30)}", flush=True)
            elif n_jendela % 15 == 0:
                print(f"status {rec['jam_live']} chat {rate:.1f}/dtk", flush=True)
        # 1 panggilan per jendela (5 unit kuota): 20 dtk = ~900 unit/jam -> kuota gratis 10.000/hari cukup ~11 jam
        time.sleep(max(a.jendela, r.get("pollingIntervalMillis", 5000) / 1000))


if __name__ == "__main__":
    main()
