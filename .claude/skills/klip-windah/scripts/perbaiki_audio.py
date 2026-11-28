#!/usr/bin/env python3
"""perbaiki-audio: tambal audio yang terpotong pada unduhan BAGIAN live YouTube.

Unduhan `--download-sections` dari VOD live kadang audionya berhenti lebih awal dari videonya
(26 Nov 2026: 57/320 dtk; 27 Nov 2026: 90,7/110 dtk -> klip salto sunyi di akhir). Skrip ini:
  1. mengunduh ulang AUDIO SAJA untuk bagian itu, dilebarkan 15 dtk di kedua sisi (kecil, ±2 MB);
  2. mencari selisih waktunya terhadap audio yang sudah ada dengan korelasi silang selubung (envelope)
     di beberapa jendela - YouTube membulatkan awal bagian ke segmen, jadi selisihnya TIDAK bisa ditebak
     dari angka (contoh nyata: minta -10 dtk, hasilnya -19,98 dtk);
  3. memasang audio baru ke video (`-c:v copy`), file lama disimpan sebagai `*_audiopotong.mp4`.
Gagal (selisih antar-jendela tidak konsisten / audio lama terlalu pendek) = berhenti dengan pesan, file tidak diubah.

Pakai: perbaiki_audio.py VIDEO.mp4 URL MULAI-SELESAI     (sama dengan BAGIAN di ambil-link)
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

SR = 8000
PAD = 15


def detik(s):
    d = 0.0
    for b in str(s).split(":"):
        d = d * 60 + float(b)
    return d


def jam(t):
    t = max(0, int(t))
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}"


def durasi(f, stream):
    # durasi stream; .webm sering tidak menyimpannya -> pakai durasi format
    for q in (["-select_streams", stream, "-show_entries", "stream=duration"], ["-show_entries", "format=duration"]):
        r = subprocess.run(["ffprobe", "-v", "error", *q, "-of", "csv=p=0", str(f)],
                           capture_output=True, text=True).stdout
        try:
            return float(r.strip().splitlines()[0])
        except (ValueError, IndexError):
            continue
    return 0.0


def selubung(f):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-vn", "-ac", "1", "-ar", str(SR),
                          "-f", "s16le", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
    n = len(a) // 80
    return np.abs(a[: n * 80]).reshape(n, 80).mean(axis=1)  # 10 ms per titik


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    video, url, bagian = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    mulai, selesai = (detik(x) for x in bagian.split("-"))
    vd, ad = durasi(video, "v:0"), durasi(video, "a:0")
    if ad >= vd * 0.98:
        print(f"Audio sudah utuh ({ad:.1f}/{vd:.1f} dtk).")
        return
    if ad < 12:
        sys.exit(f"Audio lama hanya {ad:.1f} dtk - terlalu pendek untuk diselaraskan otomatis.")
    tmp = Path(tempfile.mkdtemp(prefix="audio_"))
    try:
        rentang = f"{jam(mulai - PAD)}-{jam(selesai + PAD)}"
        subprocess.run(["yt-dlp", "-f", "ba", "--download-sections", f"*{rentang}", "-q", "--no-warnings",
                        "-o", str(tmp / "a.%(ext)s"), url], check=True)
        baru = next(tmp.glob("a.*"))
        e_lama, e_baru = selubung(video), selubung(baru)
        # jendela 8 dtk dari audio lama yang masih ada, cari posisinya di audio baru
        hasil = []
        for awal in np.linspace(2, max(2, ad - 10), 4):
            i = int(awal * 100)
            jnd = e_lama[i:i + 800]
            if len(jnd) < 800 or jnd.std() < 1e-4:
                continue
            c = np.correlate(e_baru - e_baru.mean(), jnd - jnd.mean(), "valid")
            hasil.append(c.argmax() * 0.01 - awal)
        if len(hasil) < 2 or max(hasil) - min(hasil) > 0.05:
            sys.exit(f"Selisih tidak konsisten {[round(h, 2) for h in hasil]} - selaraskan manual.")
        off = float(np.median(hasil))
        if durasi(baru, "a:0") - off < vd - 0.5:
            sys.exit(f"Audio baru juga kurang panjang (selisih {off:.2f} dtk) - coba lagi nanti.")
        cadangan = video.with_name(video.stem + "_audiopotong.mp4")
        shutil.move(video, cadangan)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(cadangan), "-ss", f"{off:.3f}", "-i", str(baru),
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                        "-t", f"{vd:.3f}", str(video)], check=True)
        print(f"Audio ditambal: {ad:.1f} -> {durasi(video, 'a:0'):.1f} dtk (selisih {off:.2f} dtk). "
              f"Cadangan: {cadangan.name}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
