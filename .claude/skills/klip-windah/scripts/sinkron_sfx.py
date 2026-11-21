"""sinkron-sfx: unduh SFX & backsound dari folder Google Drive pengguna lalu olah ke sfx/ dan musik/.

Link folder TIDAK disimpan di repo (repo publik; file SFX berlisensi). Urutan sumber link:
  1. argumen --folder URL
  2. env KLIP_SFX_DRIVE (diset di environment cloud pengguna)
  3. sfx/drive.local.txt (di-gitignore)
File yang sudah pernah diolah (ID Drive sama) dilewati, kecuali --ulang.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

import numpy as np

SKILL = Path(__file__).resolve().parent.parent
SFX = SKILL / "sfx"
MUSIK = SKILL / "musik"
MANIFEST = SFX / ".sinkron.json"
SR = 44100

# nama fungsi (dipakai render) -> kata kunci di nama file. Urutan penting: yang lebih spesifik dulu.
PERAN = [
    ("musik", ["musik", "music", "backsound", "bgm", "tiktok audio", "tiktok-audio", "lofi", "phonk", "beat"]),
    ("boom_sinematik", ["cinematic-boom", "cinematic boom", "boom_sinematik"]),
    ("sting", ["sting", "orchestra-hit", "orchestra hit", "intro-hit", "logo"]),
    ("boom", ["vine-boom", "vine boom", "boom", "impact"]),
    ("whoosh", ["whoosh", "swoosh", "swish"]),
    ("glitch", ["glitch"]),
    ("shutter", ["shutter", "camera"]),
    ("riser", ["riser"]),
    ("klik", ["klik", "click"]),
    ("bruh", ["bruh"]),
    ("getout", ["get-out", "get out", "getout", "get_out"]),
    ("fatality", ["fatality"]),
    ("awkward", ["awkward"]),
    ("bonecrack", ["bone-crack", "bone crack", "bonecrack"]),
    ("scratch", ["scratch"]),
]
MAKS_DETIK = {"sting": 2.0, "boom": 1.6, "boom_sinematik": 3.0, "whoosh": 1.0, "glitch": 1.2,
              "shutter": 1.0, "riser": 3.0, "klik": 0.4, "bruh": 1.2, "scratch": 1.5,
              "getout": 3.0, "fatality": 3.0, "awkward": 4.0, "bonecrack": 1.5}


def tebak_peran(nama):
    n = nama.lower()
    stem = re.sub(r"\.[a-z0-9]+$", "", n)
    for peran, kunci in PERAN:
        if stem == peran or stem.startswith(peran + "_") or stem.startswith(peran + "-"):
            return peran
    for peran, kunci in PERAN:
        if any(k in n for k in kunci):
            return peran
    return None


def slug(nama):
    s = re.sub(r"\.[a-z0-9]+$", "", nama.lower())
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s[:40] or "tanpa_nama"


def daftar_folder(url):
    """Kembalikan [(id, nama)] tanpa mengunduh (gdown hanya untuk membaca isi folder)."""
    import gdown
    files = gdown.download_folder(url, skip_download=True, quiet=True, use_cookies=False)
    if not files:
        raise SystemExit("Folder Drive kosong / tidak bisa dibaca. Pastikan aksesnya 'siapa saja yang memiliki link'.")
    return [(f.id, Path(f.path).name) for f in files]


def unduh(fid, out):
    url = f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t"
    req = urllib.request.Request(url, headers={"User-Agent": "klip-windah/0.1"})
    with urllib.request.urlopen(req, timeout=300) as r, open(out, "wb") as f:
        f.write(r.read())


def baca(path, ch=2):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch).copy()


def tulis(x, out, af=None):
    with tempfile.NamedTemporaryFile(suffix=".f32", delete=False) as t:
        x.astype(np.float32).tofile(t.name)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", t.name]
    if af:
        cmd += ["-af", af]
    subprocess.run(cmd + ["-ar", str(SR), str(out)], check=True)
    os.unlink(t.name)


def olah_sfx(src, out, peran):
    """Buang hening awal, ambil bunyi pertama (berhenti di jeda hening >0,15 dtk), batasi durasi,
    fade out 50 ms, normalisasi puncak -2 dBFS."""
    x = baca(src)
    env = np.abs(x).max(1)
    amb = 10 ** (-45 / 20)
    on = np.where(env > amb)[0]
    if len(on) == 0:
        raise ValueError("isinya hening")
    a = max(0, on[0] - int(0.005 * SR))
    win = int(0.01 * SR)
    lv = np.array([env[i:i + win].max() for i in range(a, len(env) - win, win)])
    b = len(env)
    sepi = 0
    akhir_amb = 10 ** (-60 / 20)  # ekor pelan (mis. whoosh) jangan terpotong
    for k, v in enumerate(lv):
        sepi = sepi + 1 if v < akhir_amb else 0
        if sepi >= 15 and k * 0.01 > 0.1:  # jeda 0,15 dtk = akhir bunyi pertama
            b = a + (k - 14) * win
            break
    b = min(b, a + int(MAKS_DETIK.get(peran, 2.0) * SR))
    y = x[a:b]
    fo = min(len(y), int(0.05 * SR))
    y[-fo:] *= np.linspace(1, 0, fo)[:, None]
    pk = np.abs(y).max()
    if pk > 0:
        y *= (10 ** (-2 / 20)) / pk
    tulis(y, out)
    return len(y) / SR


def olah_musik(src, out):
    """Ambil BAGIAN PERTAMA lagu (sampai jeda hening pertama, maks 10 dtk) lalu loop 1 bar tanpa sambungan
    janggal: cari awal & panjang bar yang sambungannya paling mirip secara spektral, crossfade 60 ms."""
    st = baca(src)
    a = st.mean(1)
    env = np.abs(a)
    win = int(0.01 * SR)
    lv = np.array([env[i:i + win].max() for i in range(0, len(env) - win, win)])
    akhir = min(len(a) / SR, 10.0)
    sepi = 0
    for k, v in enumerate(lv):
        sepi = sepi + 1 if v < 10 ** (-45 / 20) else 0
        if sepi >= 10 and k * 0.01 > 1.5:
            akhir = (k - 9) * 0.01
            break

    def spek(t, d):
        x = a[int(t * SR):int((t + d) * SR)]
        n, h = 1024, 256
        return np.log1p(np.array([np.abs(np.fft.rfft(x[i:i + n] * np.hanning(n)))[:300]
                                  for i in range(0, len(x) - n, h)]))

    def mirip(t1, t2, d=0.35):
        A, B = spek(t1, d), spek(t2, d)
        m = min(len(A), len(B))
        A, B = A[:m].ravel(), B[:m].ravel()
        return float(np.dot(A, B) / (np.linalg.norm(A) * np.linalg.norm(B) + 1e-9))

    # onset kuat pertama sebagai calon awal bar
    hop = int(0.01 * SR)
    e = np.array([np.sqrt(np.mean(a[i:i + hop] ** 2)) for i in range(0, len(a) - hop, hop)])
    on = np.maximum(0, np.diff(np.log(e + 1e-6)))
    calon = [i * 0.01 for i in range(5, min(len(on), 200)) if on[i] > 1.2 and on[i] == on[max(0, i - 5):i + 6].max()]
    s0 = calon[0] if calon else 0.5
    # 1) panjang bar kasar: bandingkan isi ~1,2 dtk setelah awal vs setelah awal+L, L = 1 bar 4/4 antara
    #    67-150 BPM (1,6-3,6 dtk). Jendela panjang menghindari loop pendek yang hanya "mirip di sambungan".
    kasar = []
    for L in np.arange(1.6, 3.6, 0.01):
        d = min(1.2, akhir - s0 - L - 0.05)
        if d < 0.6:
            break
        kasar.append((mirip(s0, s0 + L, d), L))
    if not kasar:
        raise ValueError("bagian pertama terlalu pendek untuk di-loop (butuh > 1 bar + 0,6 dtk)")
    bar = max(kasar)[1]
    # 2) halus: awal & panjang yang sambungannya paling mulus, di sekitar bar kasar
    terbaik = None
    for s in np.arange(max(0.0, s0 - 0.1), s0 + 0.1, 0.005):
        for L in np.arange(bar * 0.97, bar * 1.03, 0.002):
            if s + L + 0.4 > akhir:
                break
            sc = mirip(s, s + L)
            if terbaik is None or sc > terbaik[0]:
                terbaik = (sc, s, L)
    if terbaik is None:
        raise ValueError("bagian pertama terlalu pendek untuk di-loop")
    sc, s, L = terbaik
    xf = int(0.06 * SR)
    i0 = int(s * SR) - xf // 2
    n = int(round(L * SR))
    seg = st[i0:i0 + n + xf].copy()
    fi = np.sin(np.linspace(0, np.pi / 2, xf))[:, None]
    fo = np.cos(np.linspace(0, np.pi / 2, xf))[:, None]
    total = int(150 * SR)
    buf = np.zeros((total + n + xf, 2), np.float32)
    pos = 0
    while pos < total:
        b = seg.copy()
        b[:xf] *= fi
        b[-xf:] *= fo
        buf[pos:pos + len(b)] += b
        pos += n
    tulis(buf[xf:total + xf], out, "loudnorm=I=-14:TP=-1.5:LRA=11")
    return {"bagian_pertama_sampai": round(akhir, 2), "mulai": round(s, 3), "panjang_bar": round(L, 3),
            "bpm": round(240 / L, 2), "kemiripan_sambungan": round(sc, 3)}


def main():
    ap = argparse.ArgumentParser(prog="klip-windah sinkron-sfx")
    ap.add_argument("--folder", help="link folder Google Drive")
    ap.add_argument("--ulang", action="store_true", help="olah ulang semua file")
    args = ap.parse_args(sys.argv[2:] if len(sys.argv) > 1 and sys.argv[1] == "sinkron-sfx" else sys.argv[1:])
    lokal = SFX / "drive.local.txt"
    url = args.folder or os.environ.get("KLIP_SFX_DRIVE") or (lokal.read_text().strip() if lokal.exists() else "")
    if not url:
        raise SystemExit("Belum ada link folder Drive SFX. Minta pengguna mengirimnya, lalu jalankan dengan --folder URL.")
    if args.folder:
        lokal.write_text(args.folder.strip() + "\n")
    SFX.mkdir(exist_ok=True)
    MUSIK.mkdir(exist_ok=True)
    man = json.loads(MANIFEST.read_text()) if MANIFEST.exists() and not args.ulang else {}
    berkas = daftar_folder(url)
    print(f"Folder Drive: {len(berkas)} file")
    hasil, asing = [], []
    dipakai = {v_["keluaran"] and Path(v_["keluaran"]).stem: k_ for k_, v_ in man.items() if v_.get("peran") != "musik"}
    with tempfile.TemporaryDirectory() as td:
        for fid, nama in berkas:
            peran = tebak_peran(nama)
            if peran is None:
                asing.append(nama)
                continue
            if peran == "musik":
                out = MUSIK / f"{slug(nama)}_loop.wav"
            else:
                # nama file = fungsinya ("boom.mp3") atau varian ("boom_2.mp3" -> boom_2.wav); dua file dengan
                # fungsi sama tidak saling timpa: yang kedua jadi <peran>_<nama>
                st_ = slug(nama)
                nama_out = st_ if st_ == peran or st_.startswith(peran + "_") else peran
                if nama_out in dipakai and dipakai[nama_out] != fid:
                    nama_out = f"{peran}_{st_}"
                out = SFX / f"{nama_out}.wav"
            dipakai[out.stem] = fid
            lama = man.get(fid)
            if lama and Path(lama["keluaran"]).exists() and not args.ulang:
                hasil.append(f"  = {nama} -> {Path(lama['keluaran']).relative_to(SKILL)} (sudah ada)")
                continue
            src = Path(td) / (fid + "_" + re.sub(r"[^A-Za-z0-9._-]", "_", nama))
            unduh(fid, src)
            try:
                if peran == "musik":
                    info = olah_musik(src, out)
                    ket = f"loop {info['panjang_bar']} dtk ({info['bpm']} BPM), sambungan {info['kemiripan_sambungan']}"
                else:
                    info = {"durasi": round(olah_sfx(src, out, peran), 2)}
                    ket = f"{info['durasi']} dtk"
            except Exception as e:  # file rusak / bukan audio
                hasil.append(f"  ! {nama}: gagal diolah ({e})")
                continue
            man[fid] = {"nama": nama, "peran": peran, "keluaran": str(out), **info}
            hasil.append(f"  + {nama} -> {out.relative_to(SKILL)} [{peran}] {ket}")
    MANIFEST.write_text(json.dumps(man, indent=1, ensure_ascii=False))
    print("\n".join(hasil))
    if asing:
        print("Belum dikenali (tanya pengguna fungsinya, lalu minta ganti nama file di Drive, mis. 'bruh_2.mp3'):")
        print("\n".join(f"  ? {n}" for n in asing))
    musik = sorted(MUSIK.glob("*_loop.wav"))
    if musik:
        print("Backsound tersedia:", ", ".join(p.name for p in musik))


if __name__ == "__main__":
    main()
