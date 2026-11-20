"""Cari SFX CC0 lewat API Openverse (open source, tanpa login) dan buat halaman HTML berpemutar audio
supaya PENGGUNA yang mendengarkan dan memilih. Unduhan otomatis dari Freesound diblokir (403) dari
container ini, jadi pengguna mengunduh pilihannya sendiri dari halaman sumber, lalu mengirim filenya."""
import html
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

UA = {"User-Agent": "klip-windah-sfx/0.1"}


def cari(q, maks_detik=4.0, n=12):
    url = "https://api.openverse.org/v1/audio/?" + urllib.parse.urlencode(
        {"q": q, "license": "cc0", "page_size": 20})
    d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))
    hasil = []
    for r in d.get("results", []):
        dur = (r.get("duration") or 0) / 1000
        judul = r.get("title") or ""
        if r.get("source") == "wikimedia_audio" and judul.startswith("LL-"):
            continue  # rekaman pelafalan kata, bukan SFX
        if 0 < dur <= maks_detik:
            hasil.append({"judul": judul, "durasi": round(dur, 2), "pembuat": r.get("creator"),
                          "audio": r["url"], "halaman": r.get("foreign_landing_url"), "id": r["id"]})
        if len(hasil) >= n:
            break
    return hasil


def halaman(data, out):
    bagian = []
    for q, items in data.items():
        baris = "".join(
            f"<li><div class='t'>{html.escape(i['judul'])} <span>{i['durasi']} dtk · {html.escape(i['pembuat'] or '-')}</span></div>"
            f"<audio controls preload='none' src='{html.escape(i['audio'])}'></audio>"
            f"<a href='{html.escape(i['halaman'] or i['audio'])}' target='_blank'>halaman unduh</a></li>"
            for i in items) or "<li>tidak ada hasil</li>"
        bagian.append(f"<h2>{html.escape(q)}</h2><ul>{baris}</ul>")
    doc = f"""<!doctype html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Pilihan SFX CC0</title>
<style>body{{font-family:system-ui,sans-serif;margin:0 auto;max-width:760px;padding:16px;background:#111;color:#eee}}
h1{{font-size:20px}}h2{{margin-top:28px;color:#ffcd00;text-transform:uppercase;font-size:16px}}
ul{{list-style:none;padding:0}}li{{background:#1d1d1d;border-radius:10px;padding:10px;margin:8px 0}}
.t{{font-weight:600;margin-bottom:6px}}.t span{{font-weight:400;color:#aaa;font-size:13px}}
audio{{width:100%;height:36px}}a{{color:#7fb3ff;font-size:13px}}p{{color:#bbb;font-size:14px}}</style></head><body>
<h1>Pilihan SFX CC0 (bebas dipakai, tanpa kredit)</h1>
<p>Dengarkan, pilih yang cocok, lalu unduh dari "halaman unduh" (Freesound butuh akun gratis).
Kirim filenya dengan nama sesuai fungsinya (whoosh, boom, glitch, ...).</p>{''.join(bagian)}</body></html>"""
    Path(out).write_text(doc, encoding="utf-8")


if __name__ == "__main__":
    out = sys.argv[1]
    kata = sys.argv[2:] or ["whoosh", "impact", "glitch", "riser"]
    data = {q: cari(q) for q in kata}
    halaman(data, out)
    print(f"{out}: " + ", ".join(f"{q} {len(v)}" for q, v in data.items()))
