#!/usr/bin/env python3
"""kata-waktu: waktu PER KATA dari subtitle otomatis YouTube (.vtt) untuk satu rentang live.

Dipakai untuk memilih titik potong yang rapi (di jeda antar-kalimat) sebelum video bagiannya
diunduh/dianalisis. Waktu dicetak RELATIF terhadap MULAI, jadi langsung cocok dengan file hasil
`ambil-link URL '' MULAI-SELESAI` (detik 0 = MULAI).

Pakai: kata_waktu.py FILE.vtt MULAI SELESAI     (MULAI/SELESAI: 1:52:30 atau detik)
Contoh keluaran:  11.4 Kalian [11.6] bakal [11.8] terkagum-kagum ...
"""
import re
import sys


def detik(s):
    s = str(s)
    if ":" not in s:
        return float(s)
    d = 0.0
    for bagian in s.split(":"):
        d = d * 60 + float(bagian)
    return d


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    vtt, a, b = sys.argv[1], detik(sys.argv[2]), detik(sys.argv[3])
    teks = open(vtt, encoding="utf-8").read()
    ada = False
    for blk in teks.split("\n\n"):
        m = re.search(r"(\d+):(\d+):(\d+\.\d+) -->", blk)
        if not m:
            continue
        s = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
        if not (a <= s <= b):
            continue
        for baris in blk.split("\n")[1:]:
            if "<c>" not in baris:
                continue
            kata = re.findall(r"<(\d+):(\d+):(\d+\.\d+)><c>([^<]*)</c>", baris)
            awal = re.sub(r"<.*", "", baris)
            sisa = " ".join(f"[{int(h) * 3600 + int(mn) * 60 + float(dt) - a:.1f}]{w}" for h, mn, dt, w in kata)
            print(f"{s - a:6.1f} {awal} {sisa}")
            ada = True
    if not ada:
        print("(tidak ada kata di rentang ini - cek file .vtt / rentang)", file=sys.stderr)


if __name__ == "__main__":
    main()
