"""Halaman HTML berpemutar audio untuk aset lokal di aset/ (akar repo), supaya PENGGUNA yang mendengarkan dan
memilih (Claude tidak bisa mendengar). Audio disematkan (base64), jadi halamannya bisa dibuka di HP tanpa server.
Tiap baris menampilkan path yang tinggal ditulis di rencana ("sfx_pilihan", "sfx_tambahan", "musik").

python3 -I katalog_aset.py OUT.html [folder-di-aset ...]
  bawaan: sfx/mp3 dan kenney-cc0/{impact-sounds,interface-sounds,digital-audio}
  contoh BGM: python3 -I katalog_aset.py hasil-klip/katalog_bgm.html bgm/mp3 kenney-cc0/music-jingles
"""
import base64
import html
import sys
from pathlib import Path

ASET = Path(__file__).resolve().parents[4] / "aset"
BAWAAN = ["sfx/mp3", "kenney-cc0/impact-sounds", "kenney-cc0/interface-sounds", "kenney-cc0/digital-audio"]
MIME = {".mp3": "audio/mpeg", ".ogg": "audio/ogg", ".wav": "audio/wav"}


def path_rencana(f):
    """Path yang dipakai di rencana: relatif aset/, tanpa ekstensi; versi mp3 menunjuk ke WAV aslinya."""
    rel = f.relative_to(ASET).with_suffix("")
    if rel.parts[1:2] == ("mp3",):
        rel = Path(rel.parts[0], *rel.parts[2:])
    return rel.as_posix()


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    out = Path(sys.argv[1])
    folder = sys.argv[2:] or BAWAAN
    bagian = []
    total = 0
    for d in folder:
        files = sorted(p for p in (ASET / d).glob("*") if p.suffix.lower() in MIME)
        baris = []
        for p in files:
            b64 = base64.b64encode(p.read_bytes()).decode()
            total += len(b64)
            baris.append(f"<li><code>{html.escape(path_rencana(p))}</code>"
                         f"<audio controls preload='none' src='data:{MIME[p.suffix.lower()]};base64,{b64}'></audio></li>")
        bagian.append(f"<h2>{html.escape(d)} <span>({len(files)})</span></h2><ul>{''.join(baris) or '<li>kosong</li>'}</ul>")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f"""<!doctype html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Katalog aset</title>
<style>
:root{{--bg:#fff;--fg:#1a1a1a;--mut:#666;--line:#e4e4e4;--code:#f3f0ff}}
@media (prefers-color-scheme:dark){{:root{{--bg:#151515;--fg:#eee;--mut:#999;--line:#2c2c2c;--code:#2a2440}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.4 system-ui,sans-serif;margin:0 auto;padding:16px;max-width:760px}}
h1{{font-size:20px}} h2{{font-size:16px;margin-top:28px}} h2 span,p{{color:var(--mut);font-weight:400}}
ul{{list-style:none;padding:0}} li{{border-bottom:1px solid var(--line);padding:8px 0}}
code{{background:var(--code);padding:2px 6px;border-radius:4px;font-size:13px;word-break:break-all;user-select:all}}
audio{{display:block;width:100%;margin-top:6px;height:36px}}
</style></head><body><h1>Katalog aset (CC0)</h1>
<p>Dengarkan, lalu kirim path pilihan Anda beserta kegunaannya (mis. <code>boom = sfx/impact_deep</code>).
Semua file di sini CC0 - aman dimonetisasi, tanpa kredit.</p>{''.join(bagian)}</body></html>""", encoding="utf-8")
    print(f"Katalog: {out} ({out.stat().st_size / 1048576:.1f} MB)")


if __name__ == "__main__":
    main()
