#!/usr/bin/env python3
"""klip-windah: rekaman layar klip GTA VI Windah Basudara -> editan siap posting.

Perintah:
  analisis VIDEO [--transkrip]     info, lembar frame bergrid, usulan kotak cam, puncak suara, transkrip
  pratinjau RENCANA.json           gambar diam tata letak di beberapa detik (cek crop sebelum render)
  render RENCANA.json              video akhir 1080x1920
  sfx                              buat ulang SFX bawaan
"""
import argparse
import json
import math
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SKILL = Path(__file__).resolve().parent.parent
FONT_JUDUL = SKILL / "assets/fonts/Anton-Regular.ttf"
FONT_TEKS = SKILL / "assets/fonts/Inter.ttf"
SFX_DIR = SKILL / "sfx"
SFX_BAWAAN = SFX_DIR / "bawaan"
W, H, FPS = 1080, 1920, 30
WATERMARK = SKILL / "assets/watermark/motionklip.png"
ENDCARD_DIR = SKILL / "assets/endcard"  # template 3 detik dari program clipper
SAFE_ATAS, SAFE_BAWAH = 150, H - 480  # batas aman UI TikTok/Reels/Shorts


# ---------------------------------------------------------------- util
def run(cmd, quiet=False):
    cmd = [str(c) for c in cmd]
    if not quiet:
        print("  $", " ".join(cmd)[:400], flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-4000:])
        raise SystemExit(f"Perintah gagal: {cmd[0]}")
    return r.stdout


def probe(path):
    out = run(["ffprobe", "-v", "error", "-show_entries",
               "format=duration:stream=codec_type,width,height,avg_frame_rate:stream_side_data=rotation",
               "-of", "json", path], quiet=True)
    j = json.loads(out)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    num, den = v.get("avg_frame_rate", "30/1").split("/")
    w, h = int(v["width"]), int(v["height"])
    # rekaman layar ponsel sering menyimpan rotasi di metadata; ffmpeg & OpenCV memutarnya otomatis
    rot = next((int(sd.get("rotation", 0)) for sd in v.get("side_data_list", []) if "rotation" in sd), 0)
    if abs(rot) % 180 == 90:
        w, h = h, w
    return {"w": w, "h": h, "rotasi": rot,
            "fps": round(int(num) / max(1, int(den)), 2),
            "durasi": round(float(j["format"]["duration"]), 2),
            "audio": any(s["codec_type"] == "audio" for s in j["streams"])}


def even(x):
    return int(round(x / 2)) * 2


def font(path, size, bold=True):
    f = ImageFont.truetype(str(path), size)
    if bold:
        try:
            f.set_variation_by_name("Bold")
        except Exception:
            pass
    return f


def ambil_frame(path, t):
    import cv2
    cap = cv2.VideoCapture(str(path))
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ok, f = cap.read()
    cap.release()
    return f if ok else None


# ---------------------------------------------------------------- analisis
def analisis(video, outdir, transkrip=False):
    import cv2
    video = Path(video)
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    info = probe(video)
    print(f"Video {info['w']}x{info['h']} {info['fps']} fps, {info['durasi']} detik")

    # 1. lembar frame bergrid (koordinat piksel sumber)
    n = 12
    times = [info["durasi"] * (i + 0.5) / n for i in range(n)]
    tw = 480
    th = int(tw * info["h"] / info["w"])
    sheet = Image.new("RGB", (tw * 4, th * 3), "black")
    small = font(FONT_TEKS, 16)
    for i, t in enumerate(times):
        f = ambil_frame(video, t)
        if f is None:
            continue
        im = Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)).resize((tw, th))
        d = ImageDraw.Draw(im)
        for k in range(1, 10):
            x = tw * k / 10
            y = th * k / 10
            d.line([(x, 0), (x, th)], fill=(255, 255, 0), width=1)
            d.line([(0, y), (tw, y)], fill=(255, 255, 0), width=1)
            d.text((x + 2, 2), str(int(info["w"] * k / 10)), fill=(255, 255, 0), font=small)
            d.text((2, y + 2), str(int(info["h"] * k / 10)), fill=(255, 255, 0), font=small)
        d.rectangle([0, th - 24, 90, th], fill=(0, 0, 0))
        d.text((4, th - 22), f"{t:5.1f}s", fill="white", font=small)
        sheet.paste(im, ((i % 4) * tw, (i // 4) * th))
    sheet.save(outdir / "lembar.jpg", quality=88)

    # 2. area konten (buang bar hitam) via cropdetect
    out = subprocess.run(["ffmpeg", "-i", str(video), "-vf", "fps=2,cropdetect=24:2:0",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    crops = [c.split("=")[1] for c in out.split() if c.startswith("crop=")]
    konten = None
    if crops:
        best = max(set(crops), key=crops.count)
        cw, ch, cx, cy = map(int, best.split(":"))
        konten = [cx, cy, cw, ch]

    # 3. wajah (usulan kotak cam)
    casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = []
    step = max(0.5, info["durasi"] / 60)
    t = 0.0
    while t < info["durasi"]:
        f = ambil_frame(video, t)
        if f is not None:
            g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
            mins = max(24, int(min(info["w"], info["h"]) * 0.04))
            for (x, y, w, h) in casc.detectMultiScale(g, 1.1, 6, minSize=(mins, mins)):
                faces.append((t, int(x), int(y), int(w), int(h)))
        t += step
    klaster = []
    for t, x, y, w, h in faces:
        cx, cy = x + w / 2, y + h / 2
        for k in klaster:
            if abs(k["cx"] - cx) < k["w"] and abs(k["cy"] - cy) < k["w"] and 0.5 < w / k["w"] < 2:
                k["n"] += 1
                k["box"].append((x, y, w, h))
                k["t"].append(t)
                break
        else:
            klaster.append({"cx": cx, "cy": cy, "w": w, "n": 1, "box": [(x, y, w, h)], "t": [t]})
    usulan = []
    for k in sorted(klaster, key=lambda k: -k["n"])[:4]:
        x, y, w, h = np.median(np.array(k["box"]), axis=0)
        # cam = wajah diperluas (kepala + bahu)
        bw, bh = w * 2.8, h * 2.6
        bx = max(0, x + w / 2 - bw / 2)
        by = max(0, y - h * 0.7)
        bw = min(bw, info["w"] - bx)
        bh = min(bh, info["h"] - by)
        usulan.append({"jumlah_deteksi": k["n"], "wajah": [int(x), int(y), int(w), int(h)],
                       "usulan_cam_box": [even(bx), even(by), even(bw), even(bh)],
                       "dari_detik": round(min(k["t"]), 1), "sampai_detik": round(max(k["t"]), 1)})

    # 4. puncak suara (teriak / momen heboh)
    puncak = []
    if info["audio"]:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-ac", "1", "-ar", "16000",
                              "-f", "f32le", "-"], capture_output=True).stdout
        a = np.frombuffer(raw, dtype=np.float32)
        win = 8000  # 0,5 detik
        if len(a) > win:
            rms = np.sqrt(np.array([np.mean(a[i:i + win] ** 2) for i in range(0, len(a) - win, win)]) + 1e-12)
            db = 20 * np.log10(rms)
            med = float(np.median(db))
            idx = np.argsort(-db)
            for i in idx:
                tt = i * 0.5
                if all(abs(tt - p["detik"]) > 3 for p in puncak):
                    puncak.append({"detik": tt, "db_di_atas_median": round(float(db[i]) - med, 1)})
                if len(puncak) >= 6:
                    break
            puncak.sort(key=lambda p: p["detik"])

    hasil = {"video": str(video), "info": info, "area_konten": konten,
             "cam_usulan": usulan, "puncak_suara": puncak,
             "lembar": str(outdir / "lembar.jpg")}

    # 5. transkrip
    if transkrip and info["audio"]:
        from faster_whisper import WhisperModel
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-ac", "1", "-ar", "16000",
                              "-f", "f32le", "-"], capture_output=True).stdout
        a = np.frombuffer(raw, dtype=np.float32).copy()
        m = WhisperModel("small", device="cpu", compute_type="int8")
        segs, _ = m.transcribe(a, language="id", vad_filter=True)
        baris = [f"[{s.start:6.1f} - {s.end:6.1f}] {s.text.strip()}" for s in segs]
        (outdir / "transkrip.txt").write_text("\n".join(baris), encoding="utf-8")
        hasil["transkrip"] = str(outdir / "transkrip.txt")
        print("\n".join(baris))

    (outdir / "analisis.json").write_text(json.dumps(hasil, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in hasil.items() if k != "video"}, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------- aset grafis
EMOJI_FONT_CALON = [
    SKILL / "assets/fonts/NotoColorEmoji.ttf",
    Path("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"),
    Path("/usr/share/fonts/noto/NotoColorEmoji.ttf"),
    Path("C:/Windows/Fonts/seguiemj.ttf"),
]
_emoji_cache = {}


def is_emoji(ch):
    o = ord(ch)
    return o >= 0x1F000 or 0x2600 <= o <= 0x27BF or o in (0x200D, 0xFE0F)


def potong_emoji(teks):
    """Pecah teks jadi [(segmen, adalah_emoji)]; rangkaian ZWJ/VS16 digabung ke emoji."""
    seg = []
    for ch in teks:
        e = is_emoji(ch)
        if seg and seg[-1][1] == e and (not e or ord(ch) in (0x200D, 0xFE0F) or (seg[-1][0] and ord(seg[-1][0][-1]) == 0x200D)):
            seg[-1] = (seg[-1][0] + ch, e)
        else:
            seg.append((ch, e))
    return seg


def emoji_img(e, size):
    key = (e, size)
    if key in _emoji_cache:
        return _emoji_cache[key]
    im = None
    for p in EMOJI_FONT_CALON:
        if not p.exists():
            continue
        try:
            ef = ImageFont.truetype(str(p), 109)  # Noto Color Emoji hanya punya ukuran 109
        except OSError:
            try:
                ef = ImageFont.truetype(str(p), size)
            except OSError:
                continue
        c = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
        ImageDraw.Draw(c).text((10, 10), e, font=ef, embedded_color=True)
        bb = c.getbbox()
        if bb:
            im = c.crop(bb)
            im = im.resize((int(size * im.width / im.height), size), Image.LANCZOS)
            break
    if im is None:
        print(f"  (peringatan: font emoji tidak ditemukan, emoji {e!r} dilewati)")
    _emoji_cache[key] = im
    return im


def ukur(teks, f, size):
    w = 0
    for seg, e in potong_emoji(teks):
        if e:
            im = emoji_img(seg, int(size * 0.82))
            w += (im.width + int(size * 0.06)) if im else 0
        else:
            w += f.getlength(seg)
    return w


def tulis(img, xy, teks, f, size, fill="white", stroke=0, stroke_fill="black", warna_kata=None):
    """Tulis satu baris (boleh berisi emoji). warna_kata: {KATA: warna} untuk menyorot kata tertentu."""
    d = ImageDraw.Draw(img)
    x, y = xy
    for seg, e in potong_emoji(teks):
        if e:
            im = emoji_img(seg, int(size * 0.82))
            if im:
                img.alpha_composite(im, (int(x), int(y + size * 0.2)))
                x += im.width + int(size * 0.06)
            continue
        for i, kata in enumerate(seg.split(" ")):
            if i:
                x += f.getlength(" ")
            if not kata:
                continue
            warna = (warna_kata or {}).get(kata.strip(".,!?:").upper(), fill)
            d.text((x, y), kata, font=f, fill=warna, stroke_width=stroke, stroke_fill=stroke_fill)
            x += f.getlength(kata)


def bungkus(teks, f, size, maxw):
    kata, baris, cur = teks.split(), [], ""
    for k in kata:
        coba = (cur + " " + k).strip()
        if ukur(coba, f, size) <= maxw or not cur:
            cur = coba
        else:
            baris.append(cur)
            cur = k
    baris.append(cur)
    # emoji sendirian di baris terakhir -> gabung ke baris sebelumnya
    if len(baris) > 1 and all(e for _, e in potong_emoji(baris[-1].replace(" ", ""))):
        baris[-2] += " " + baris.pop()
    return baris


def gambar_judul(teks, sub, path, lebar=W - 80):
    """Kotak judul gaya referensi: gelap transparan, tepi gradasi ungu->pink, huruf Anton kapital."""
    teks = teks.upper().strip()
    pad, border, rad = 30, 7, 26
    size = 74
    while True:
        f = font(FONT_JUDUL, size, bold=False)
        maxw = lebar - 2 * pad - 2 * border
        baris = bungkus(teks, f, size, maxw)
        if len(baris) <= 3 or size <= 50:
            break
        size -= 4
    lh = int(size * 1.08)
    fs = font(FONT_TEKS, 22)
    sub_h = 30 if sub else 0
    tinggi = 2 * pad + lh * len(baris) + sub_h + 2 * border
    lebar_isi = max(ukur(b, f, size) for b in baris)
    lebar = int(min(lebar, lebar_isi + 2 * pad + 2 * border + 10))
    img = Image.new("RGBA", (lebar, tinggi), (0, 0, 0, 0))
    # tepi gradasi
    grad = Image.new("RGBA", (lebar, tinggi))
    gd = ImageDraw.Draw(grad)
    for x in range(lebar):
        u = x / max(1, lebar - 1)
        c = (int(124 + (255 - 124) * u), int(58 + (63 - 58) * u), int(255 + (164 - 255) * u), 255)
        gd.line([(x, 0), (x, tinggi)], fill=c)
    mask = Image.new("L", (lebar, tinggi), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, lebar - 1, tinggi - 1], rad, fill=255)
    img.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([border, border, lebar - 1 - border, tinggi - 1 - border], rad - border,
                        fill=(14, 10, 26, 235))
    y = border + pad - int(size * 0.08)
    for b in baris:
        tulis(img, (border + pad, y), b, f, size)
        y += lh
    if sub:
        d.text((border + pad, y + 2), sub.upper(), font=fs, fill=(235, 235, 235))
    img.save(path)
    return img.size


def gambar_caption(teks, path, size=46):
    f = font(FONT_TEKS, size)
    tw = int(f.getlength(teks)) + 40
    th = int(size * 1.6)
    img = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for dx, dy in [(2, 2), (3, 3), (1, 2)]:
        d.text((20 + dx, 6 + dy), teks, font=f, fill=(0, 0, 0, 200))
    d.text((20, 6), teks, font=f, fill="white", stroke_width=2, stroke_fill=(0, 0, 0, 160))
    img.save(path)
    return img.size


def gambar_speedlines(folder, tebal, n_frame=6, seed=7):
    """Garis kecepatan ala anime: baji putih dari tepi menuju tengah."""
    folder.mkdir(parents=True, exist_ok=True)
    rnd = random.Random(seed + (100 if tebal else 0))
    cx, cy = W / 2, H / 2
    R = math.hypot(W, H) / 2 + 40
    for i in range(n_frame):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        jumlah = 42 if tebal else 16
        for _ in range(jumlah):
            a = rnd.uniform(0, 2 * math.pi)
            dalam = R * rnd.uniform(0.38, 0.62) if tebal else R * rnd.uniform(0.62, 0.85)
            lebar = rnd.uniform(8, 22) if tebal else rnd.uniform(4, 10)
            ox, oy = cx + R * math.cos(a), cy + R * math.sin(a)
            px, py = -math.sin(a) * lebar, math.cos(a) * lebar
            ix, iy = cx + dalam * math.cos(a), cy + dalam * math.sin(a)
            d.polygon([(ox + px, oy + py), (ox - px, oy - py), (ix, iy)], fill=(255, 255, 255, 235))
        img.save(folder / f"{i:02d}.png")
    return folder / "%02d.png"


# ---------------------------------------------------------------- SFX
SFX_RESEP = {
    "whoosh": ("anoisesrc=d=0.6:c=pink:a=0.9", "highpass=f=250,lowpass=f=6000,afade=t=in:d=0.38:curve=exp,afade=t=out:st=0.38:d=0.22,volume=1.4"),
    "riser": ("aevalsrc='0.35*sin(2*PI*(180*t+520*t*t))+0.25*(random(0)-0.5)*t':d=1.0", "highpass=f=120,afade=t=in:d=0.95:curve=exp,afade=t=out:st=0.95:d=0.05"),
    "boom": ("aevalsrc='0.95*sin(2*PI*(58-30*t)*t)*exp(-3.2*t)+0.5*(random(0)-0.5)*exp(-25*t)':d=1.3", "lowpass=f=900,volume=1.6"),
    "glitch": ("aevalsrc='0.45*sin(2*PI*(700+500*floor(mod(t*40,4)))*t)*lt(mod(t,0.06),0.035)+0.3*(random(0)-0.5)':d=0.32", "acrusher=bits=6:samples=8:mix=1,afade=t=out:st=0.25:d=0.07"),
    "klik": ("aevalsrc='0.9*sin(2*PI*2200*t)*exp(-140*t)+0.4*(random(0)-0.5)*exp(-400*t)':d=0.06", "highpass=f=600"),
}


def buat_sfx():
    SFX_BAWAAN.mkdir(parents=True, exist_ok=True)
    for nama, (src, fx) in SFX_RESEP.items():
        run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", src, "-af", fx,
             "-ar", "44100", "-ac", "2", SFX_BAWAAN / f"{nama}.wav"], quiet=True)
    print("SFX bawaan dibuat di", SFX_BAWAAN)


SFX_ALIAS = {"glitch": ["glitch", "shutter"]}
# SFX untuk TRANSISI (potongan/glitch, keluar kartu hook). Pengguna tidak suka shutter/glitch di transisi -> whoosh.
# Bisa diganti per klip: "sfx_transisi": "nama" (file di sfx/). Selalu tanyakan ke pengguna.
SFX_TRANSISI = "whoosh"


def sfx_path(nama):
    for n in SFX_ALIAS.get(nama, [nama]):
        for ext in ("wav", "mp3", "m4a", "ogg"):
            p = SFX_DIR / f"{n}.{ext}"
            if p.exists():
                return p  # SFX milik pengguna menang
    p = SFX_BAWAAN / f"{nama}.wav"
    if not p.exists():
        buat_sfx()
    return p


# ---------------------------------------------------------------- render
def cover(label_in, box, tw, th, label_out):
    """Crop lalu perbesar (Lanczos) + penajaman sesuai faktor perbesaran (cam kecil diperbesar ~4x)."""
    x, y, w, h = map(int, box)
    faktor = max(tw / max(1, w), th / max(1, h))
    tajam = ""
    if faktor > 1.2:
        kuat = min(1.3, 0.35 + 0.25 * faktor)
        tajam = f",unsharp=5:5:{kuat:.2f}:5:5:0.0"
    return (f"[{label_in}]crop={even(w)}:{even(h)}:{x}:{y},"
            f"scale={tw}:{th}:force_original_aspect_ratio=increase:flags=lanczos,crop={tw}:{th}{tajam}[{label_out}]")


def antara(segs):
    return "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in segs) or "0"


def bangun(rencana, tmp, pratinjau=None):
    src = rencana["input"]
    info = probe(src)
    t0, t1 = rencana.get("potong") or [0, info["durasi"]]
    durasi_src = round(t1 - t0, 3)
    # buang: [[a, b], ...] detik relatif awal potong (timeline SUMBER). Semua detik efek lain memakai
    # timeline HASIL (setelah dibuang). Sambungan tanpa transisi = "perfect cut".
    buang = sorted([float(a), float(b)] for a, b in rencana.get("buang", []))
    simpan, pos = [], 0.0
    for a, b in buang:
        if a > pos:
            simpan.append((pos, a))
        pos = max(pos, b)
    if pos < durasi_src:
        simpan.append((pos, durasi_src))
    dur = round(sum(b - a for a, b in simpan), 3)
    fmt = rencana.get("format", "tiktok")
    stream = rencana.get("stream_box") or [0, 0, info["w"], info["h"]]
    cam = rencana.get("cam_box")
    efek = True  # efek visual juga tampil di pratinjau; audio hanya saat render
    geser = f"+{pratinjau:.3f}/TB" if pratinjau is not None else ""

    inputs, f = [], []
    if pratinjau is not None:
        sisa, src_t = pratinjau, simpan[-1][1]
        for a, b in simpan:
            if sisa <= b - a:
                src_t = a + sisa
                break
            sisa -= b - a
        inputs += ["-ss", f"{t0 + src_t:.3f}", "-t", "0.2", "-i", src]
    else:
        inputs += ["-ss", f"{t0:.3f}", "-t", f"{durasi_src:.3f}", "-i", src]
    n_in = 1

    def tambah(*args):
        nonlocal n_in
        inputs.extend(map(str, args))
        n_in += 1
        return n_in - 1

    penuh = rencana.get("cam_penuh", [])  # potong ke cam layar penuh (punch-in reaksi)
    butuh = 2 if fmt == "tiktok" else 1
    if penuh and cam:
        butuh += 1
    zoom = rencana.get("zoom", [])  # [[mulai, selesai, x, y, w, h], ...] punch-in panel game ke area sumber
    i_zoom0 = butuh
    butuh += len(zoom)
    stiker = [st if isinstance(st, dict) else {"mulai": st[0], "selesai": st[1], "teks": st[2] if len(st) > 2 else ""}
              for st in rencana.get("stiker", [])] if rencana.get("cam_box") else []
    i_stk0 = butuh
    butuh += len(stiker)
    cam_asli = rencana.get("cam_box")
    if pratinjau is None and len(simpan) > 1:
        n = len(simpan)
        f.append(f"[0:v]fps={FPS},setpts=PTS-STARTPTS,split={n}" + "".join(f"[vs{k}]" for k in range(n)))
        for k, (a, b) in enumerate(simpan):
            f.append(f"[vs{k}]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[vt{k}]")
        f.append("".join(f"[vt{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=0[pre0]")
    else:
        f.append(f"[0:v]fps={FPS},setpts=PTS-STARTPTS{geser}[pre0]")
    pre = "pre0"
    # tutup: buramkan area sumber (notifikasi ponsel, UI) [x, y, w, h, mulai, selesai]
    for k, (x, y, w, h, a, b) in enumerate(rencana.get("tutup", [])):
        x, y, w, h = map(even, (x, y, w, h))
        f.append(f"[{pre}]split[tm{k}][tc{k}];[tc{k}]crop={w}:{h}:{x}:{y},boxblur=24:3[tb{k}];"
                 f"[tm{k}][tb{k}]overlay={x}:{y}:enable='between(t,{a:.3f},{b:.3f})'[pre{k + 1}]")
        pre = f"pre{k + 1}"
    if butuh > 1:
        f.append(f"[{pre}]split={butuh}" + "".join(f"[s{i}]" for i in range(butuh)))
    else:
        f.append(f"[{pre}]null[s0]")

    cam_hd = rencana.get("cam_hd")
    if cam_hd is True:
        cam_hd = str(Path(rencana.get("_rencana_path", "x.json")).with_name(Path(rencana.get("_rencana_path", "x.json")).stem + "_camhd.mp4"))
    if cam_hd and Path(cam_hd).exists() and cam:
        # sumber cam = video hasil upscale AI (sudah di timeline hasil); kotaknya = seluruh frame
        if pratinjau is not None:
            i_hd = tambah("-ss", f"{pratinjau:.3f}", "-t", "0.2", "-i", cam_hd)
        else:
            i_hd = tambah("-i", cam_hd)
        f.append(f"[{i_hd}:v]fps={FPS},setpts=PTS-STARTPTS{geser},split=2[hd1][hd2]")
        cam_src = ["hd1", "hd2"]
        cam = [0, 0, even(cam[2]) * 4, even(cam[3]) * 4]
    else:
        cam_src = None

    if fmt == "tiktok":
        if not cam:
            raise SystemExit("format tiktok butuh cam_box")
        gh = even(H * rencana.get("porsi_game", 0.57))
        ch = H - gh
        game = rencana.get("game_box")
        if not game:  # tengah stream, rasio panel game
            sx, sy, sw, sh = stream
            gw = min(sw, sh * W / gh)
            game = [sx + (sw - gw) / 2, sy, gw, sh]
        f.append(cover("s0", game, W, gh, "game"))
        f.append(cover(cam_src[0] if cam_src else "s1", cam, W, ch, "cam"))
        atas = rencana.get("posisi_cam", "bawah") == "atas"
        f.append("[cam][game]vstack[base0]" if atas else "[game][cam]vstack[base0]")
        seam = ch if atas else gh
        konten_y, konten_h = 0, H
        nxt = 2
    else:  # kotak
        atas = False
        sx, sy, sw, sh = stream
        rasio = rencana.get("rasio_kotak")  # lebar/tinggi; None = utuh
        if rasio and sw / sh > rasio:
            nw = sh * rasio
            nx = sx + (sw - nw) / 2
            if cam:  # pastikan cam asli tetap kelihatan
                cx0, _, cw0, _ = cam
                nx = min(max(nx, cx0 + cw0 - nw), cx0)
                nx = min(max(nx, sx), sx + sw - nw)
            sx, sw = nx, nw
        konten_h = even(W * sh / sw)
        konten_y = even((H - konten_h) / 2)
        f.append(cover("s0", [sx, sy, sw, sh], W, konten_h, "isi"))
        f.append(f"[isi]pad={W}:{H}:0:{konten_y}:black[base0]")
        seam = konten_y
        nxt = 1
    cur = "base0"

    for k, (za, zb, zx, zy, zw, zh) in enumerate(zoom):
        if fmt == "tiktok":
            pw, ph, py = W, gh, (ch if atas else 0)
        else:
            pw, ph, py = W, konten_h, konten_y
        f.append(cover(f"s{i_zoom0 + k}", [zx, zy, zw, zh], pw, ph, f"zm{k}"))
        f.append(f"[{cur}][zm{k}]overlay=0:{py}:enable='between(t,{za:.3f},{zb:.3f})'[bz{k}]")
        cur = f"bz{k}"

    if penuh and cam:
        th = H if fmt == "tiktok" else konten_h
        ty = 0 if fmt == "tiktok" else konten_y
        f.append(cover(cam_src[1] if cam_src else f"s{nxt}", cam, W, th, "campenuh"))
        f.append(f"[{cur}][campenuh]overlay=0:{ty}:enable='{antara(penuh)}'[b1]")
        cur = "b1"

    sfx = []  # (nama, detik, volume)
    if efek:
        # glitch di titik transisi
        glitch = rencana.get("glitch", [])
        if glitch:
            en = antara([(max(0, g - 0.12), g + 0.16) for g in glitch])
            f.append(f"[{cur}]rgbashift=rh=-18:bh=18:gv=6:enable='{en}',"
                     f"noise=alls=55:allf=t:enable='{en}'[b2]")
            cur = "b2"
            tr = rencana.get("sfx_transisi", SFX_TRANSISI)
            sfx += [(tr, max(0, g - 0.2), 0.8) for g in glitch]
        # impact: getar + kilat putih
        impact = rencana.get("impact", [])
        if impact:
            gx = "+".join(f"if(between(t,{a:.3f},{a + 0.4:.3f}),22*sin((t-{a:.3f})*95)*(1-(t-{a:.3f})/0.4),0)" for a in impact)
            gy = "+".join(f"if(between(t,{a:.3f},{a + 0.4:.3f}),16*cos((t-{a:.3f})*80)*(1-(t-{a:.3f})/0.4),0)" for a in impact)
            f.append(f"[{cur}]scale={even(W * 1.05)}:{even(H * 1.05)},"
                     f"crop={W}:{H}:x='(iw-ow)/2+{gx}':y='(ih-oh)/2+{gy}',"
                     f"eq=brightness=0.28:enable='{antara([(a, a + 0.07) for a in impact])}'[b3]")
            cur = "b3"
            sfx += [(rencana.get("sfx_impact", "boom"), a, 0.9) for a in impact]
        # speed lines
        for jenis in ("tipis", "tebal"):
            segs = [(s[0], s[1]) for s in rencana.get("speedlines", []) if (s[2] if len(s) > 2 else "tipis") == jenis]
            if not segs:
                continue
            pola = gambar_speedlines(tmp / f"sl_{jenis}", jenis == "tebal")
            i = tambah("-stream_loop", "-1", "-framerate", "12", "-t", f"{dur:.3f}", "-i", pola)
            f.append(f"[{i}:v]fps={FPS},format=rgba[sl{jenis}]")
            f.append(f"[{cur}][sl{jenis}]overlay=0:0:eof_action=pass:enable='{antara(segs)}'[b{jenis}]")
            cur = f"b{jenis}"
            if jenis == "tebal":
                sfx += [("whoosh", max(0, a - 0.35), 0.8) for a, _ in segs]

    # watermark program clipper - selalu di safe zone TikTok/Shorts
    # (tidak di 150 px teratas, tidak di 480 px terbawah tempat caption/username/tombol).
    # TikTok: di sela facecam & gameplay (tengah sambungan), 68% lebar, opacity 0.88.
    # Kotak: tepat di atas gambar, di latar hitam.
    wm = rencana.get("watermark", str(WATERMARK) if WATERMARK.exists() else None)
    if wm:
        wim = Image.open(wm)
        ww = int(rencana.get("watermark_lebar", W * 0.68 if fmt == "tiktok" else W))
        wh = even(wim.height * ww / wim.width)
        if "watermark_y" in rencana:  # titik tengah watermark
            wy = rencana["watermark_y"] - wh / 2
        elif fmt == "tiktok":
            wy = seam - wh / 2  # di sela facecam & gameplay
        elif rencana.get("bar_judul"):  # bar judul di atas gambar -> watermark di bawah gambar
            wy = konten_y + konten_h + 24
        else:
            wy = konten_y - wh - 24
        wy = even(min(max(wy, SAFE_ATAS), SAFE_BAWAH - wh))

    # judul (hook)
    if rencana.get("judul"):
        jd = float(rencana.get("judul_durasi", 2.5))
        jw, jh = gambar_judul(rencana["judul"], rencana.get("judul_sub"), tmp / "judul.png")
        if fmt == "tiktok":
            jy = seam - jh / 2
            if wm:  # geser ke sisi cam supaya tidak menumpuk watermark
                jy = (seam - wh / 2 - jh - 8) if atas else (seam + wh / 2 + 8)
        else:
            jy = konten_y - jh - 40 if not wm else konten_y + konten_h + 40
        jy = even(min(max(jy, SAFE_ATAS), SAFE_BAWAH - jh))
        jx = even(rencana.get("judul_x", 40))
        i = tambah("-loop", "1", "-framerate", str(FPS), "-t", f"{jd:.2f}", "-i", tmp / "judul.png")
        f.append(f"[{i}:v]format=rgba,fade=in:st=0:d=0.15:alpha=1,fade=out:st={max(0, jd - 0.3):.2f}:d=0.3:alpha=1[jud]")
        f.append(f"[{cur}][jud]overlay={jx}:{jy}:eof_action=pass[bj]")
        cur = "bj"

    # caption punchline statis (gaya kotak)
    if rencana.get("caption"):
        cw, chh = gambar_caption(rencana["caption"], tmp / "caption.png", rencana.get("caption_ukuran", 46))
        pos = rencana.get("caption_y", 0.5)
        cy = even(konten_y + konten_h * pos - chh / 2)
        i = tambah("-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", tmp / "caption.png")
        f.append(f"[{i}:v]format=rgba[cap]")
        f.append(f"[{cur}][cap]overlay=(W-w)/2:{cy}:eof_action=pass[bc]")
        cur = "bc"

    # caption per frasa (gaya referensi): di sisi cam dekat sambungan (TikTok) / tepi bawah gambar (kotak)
    capf = rencana.get("_caption") or []
    if capf:
        jd_end = float(rencana.get("judul_durasi", 2.5)) if rencana.get("judul") else 0
        for k, (a, b, teks) in enumerate(capf):
            if b <= jd_end:
                continue
            a = max(a, jd_end)
            if rencana.get("caption_mode") == "kata":  # caption 1 kata berwarna (gaya akun4)
                urut = rencana.get("caption_warna", ["kuning", "putih", "hijau"])
                cw_, ch_ = gambar_caption_frasa(kata_kunci(teks), tmp / f"cf{k}.png",
                                                int(rencana.get("caption_frasa_ukuran", 76)),
                                                warna=WARNA.get(urut[k % len(urut)], (255, 255, 255)))
            else:
                cw_, ch_ = gambar_caption_frasa(teks, tmp / f"cf{k}.png", int(rencana.get("caption_frasa_ukuran", 64)))
            if "caption_frasa_y" in rencana:
                cy_ = rencana["caption_frasa_y"] - ch_ / 2
            elif fmt == "tiktok":
                tepi = wh / 2 + 10 if wm else 10
                cy_ = (seam - tepi - ch_) if atas else (seam + tepi)
            elif rencana.get("bar_judul") and wm:  # watermark di bawah gambar -> caption di dalam gambar
                cy_ = konten_y + konten_h - ch_ - 10
            else:
                cy_ = konten_y + konten_h - ch_ * 0.6
            cy_ = even(min(max(cy_, SAFE_ATAS), SAFE_BAWAH - ch_))
            i = tambah("-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", tmp / f"cf{k}.png")
            f.append(f"[{i}:v]format=rgba[cf{k}]")
            f.append(f"[{cur}][cf{k}]overlay=(W-w)/2:{cy_}:eof_action=pass:enable='between(t,{a:.3f},{b:.3f})'[bcf{k}]")
            cur = f"bcf{k}"

    # stiker reaksi (gaya akun5 "melongo"): wajah Windah diperbesar berbingkai putih + teks reaksi
    for k, st in enumerate(stiker):
        cx_, cy_, cw0_, ch0_ = cam_asli
        zm = float(st.get("zoom", 1.35))
        bw_, bh_ = cw0_ / zm, ch0_ / zm
        fy = float(st.get("fokus_y", 0.42))
        box_ = [cx_ + (cw0_ - bw_) / 2, cy_ + (ch0_ - bh_) * fy, bw_, bh_]
        lw = even(W * float(st.get("lebar", 0.5)))
        lh_ = even(lw * bh_ / bw_)
        f.append(cover(f"s{i_stk0 + k}", box_, lw, lh_, f"stk{k}r"))
        f.append(f"[stk{k}r]pad={lw + 12}:{lh_ + 12}:6:6:white[stk{k}]")
        if fmt == "tiktok":
            pyc = (ch + gh / 2) if atas else gh / 2
        else:
            pyc = konten_y + konten_h / 2
        px_ = even(W * float(st.get("x", 0.5)) - (lw + 12) / 2)
        py_ = even(float(st["y"]) * H - (lh_ + 12) / 2) if "y" in st else even(pyc - (lh_ + 12) / 2)
        en = f"between(t,{float(st['mulai']):.3f},{float(st['selesai']):.3f})"
        f.append(f"[{cur}][stk{k}]overlay={px_}:{py_}:enable='{en}'[bstk{k}]")
        cur = f"bstk{k}"
        if st.get("teks"):
            tw_, th_ = gambar_label(st["teks"], tmp / f"stklab{k}.png", int(st.get("ukuran", 64)))
            i = tambah("-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", tmp / f"stklab{k}.png")
            f.append(f"[{i}:v]format=rgba[stl{k}]")
            f.append(f"[{cur}][stl{k}]overlay={even(px_ + (lw + 12 - tw_) / 2)}:{even(py_ + lh_ + 12 - th_ * 0.9)}:"
                     f"eof_action=pass:enable='{en}'[bstl{k}]")
            cur = f"bstl{k}"
    if not stiker and "stiker" in rencana and not rencana.get("cam_box"):
        print("  PERINGATAN: stiker butuh cam_box - dilewati.")

    if rencana.get("popup"):
        cur = overlay_popup(rencana["popup"], tmp, tambah, cur, f, W, H)

    # bar judul statis (gaya viral: bar putih di atas gambar sepanjang video, pengganti kartu hook)
    if rencana.get("bar_judul"):
        bw2, bh2 = gambar_bar_judul(rencana["bar_judul"], tmp / "bar.png", W, rencana.get("bar_gaya", "hitam"),
                                    int(rencana.get("bar_ukuran", 56)))
        if "bar_y" in rencana:
            by2 = rencana["bar_y"]
        elif fmt == "tiktok":
            by2 = SAFE_ATAS - 30
        else:
            by2 = max(SAFE_ATAS - 60, konten_y - bh2)
        i = tambah("-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", tmp / "bar.png")
        f.append(f"[{i}:v]format=rgba[barj]")
        f.append(f"[{cur}][barj]overlay=0:{even(by2)}:eof_action=pass[bbar]")
        cur = "bbar"

    if rencana.get("flash_awal") or rencana.get("hook"):  # sambungan dari kartu hook: putih memudar
        f.append(f"[{cur}]fade=t=in:st=0:d=0.3:color=white[bfl]")
        cur = "bfl"

    if wm:
        i = tambah("-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", wm)
        op = float(rencana.get("watermark_opacity", 0.88))
        f.append(f"[{i}:v]format=rgba,scale={even(ww)}:{wh},colorchannelmixer=aa={op:.2f}[wm]")
        f.append(f"[{cur}][wm]overlay=(W-w)/2:{wy}:eof_action=pass[bw]")
        cur = "bw"

    if cam_src:
        if not (penuh and cam):
            f.append(f"[{cam_src[1]}]nullsink")
        # keluaran split sumber untuk cam tidak terpakai (cam diambil dari video HD)
        if fmt == "tiktok":
            f.append("[s1]nullsink")
        if penuh:
            f.append(f"[s{nxt}]nullsink")
    f.append(f"[{cur}]format=yuv420p[vout]")

    # audio
    amap = []
    if pratinjau is None:
        for nama, t, vol in rencana.get("sfx_tambahan", []):
            sfx.append((nama, t, vol))
        if rencana.get("tanpa_sfx"):
            sfx = []
        skala = float(rencana.get("volume_sfx", 1.0))
        if info["audio"]:
            if len(simpan) > 1:
                n = len(simpan)
                f.append(f"[0:a]aresample=44100,asetpts=PTS-STARTPTS,asplit={n}" + "".join(f"[as{k}]" for k in range(n)))
                for k, (a, b) in enumerate(simpan):  # fade 15 ms supaya sambungan tidak "klik"
                    f.append(f"[as{k}]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS,"
                             f"afade=t=in:d=0.015,afade=t=out:st={max(0, b - a - 0.015):.3f}:d=0.015[at{k}]")
                f.append("".join(f"[at{k}]" for k in range(n)) + f"concat=n={n}:v=0:a=1[a0]")
            else:
                f.append("[0:a]aresample=44100,asetpts=PTS-STARTPTS[a0]")
        else:
            i = tambah("-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=44100:cl=stereo")
            f.append(f"[{i}:a]anull[a0]")
        lab = ["a0"]
        for k, (nama, t, vol) in enumerate(sfx):
            i = tambah("-i", sfx_path(nama))
            ms = int(t * 1000)
            f.append(f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo,adelay={ms}|{ms},volume={vol * skala:.2f}[x{k}]")
            lab.append(f"x{k}")
        if len(lab) > 1:
            f.append("".join(f"[{l}]" for l in lab) + f"amix=inputs={len(lab)}:normalize=0:duration=first[am]")
        else:
            f.append("[a0]anull[am]")
        f.append("[am]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100[aout]")
        amap = ["-map", "[aout]"]
    return inputs, f, amap, dur


def buat_get_out(rencana, cfg, tmp):
    """Ending meme "get out": tepat setelah momen lucu/sus/sarkas (akhir `potong`) suara asli + musik dipotong
    dan SFX get out diputar UTUH, sementara VIDEO TETAP MENGALIR (lanjutan rekaman, tanpa efek/caption).
    Bila rekaman habis, sisanya layar hitam. Lalu endcard.
    Rencana: "get_out": true atau {"sfx": "getout", "volume": 1.0, "ekor": 0.15, "hitam": false}."""
    cfg = cfg if isinstance(cfg, dict) else {}
    sfx = sfx_path(cfg.get("sfx", "getout"))
    if not sfx:
        raise SystemExit("SFX get out tidak ada di sfx/ - jalankan sinkron-sfx dulu.")
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                              str(sfx)], capture_output=True, text=True).stdout.strip()) + float(cfg.get("ekor", 0.15))
    KW, KH = kanvas(rencana)
    banding = rencana.get("format") in FORMAT_BANDING
    if banding:
        lanjut = 0.0 if cfg.get("hitam") else d
    else:
        akhir = rencana["potong"][1]
        sisa = max(0.0, probe(rencana["input"])["durasi"] - akhir - 0.05)
        lanjut = 0.0 if cfg.get("hitam") else min(d, sisa)
    vid = tmp / "getout_v.mp4"
    bk = cfg.get("beku")
    if bk:  # frame beku (detik SUMBER absolut) + punch-zoom ke "box" [x,y,w,h], sinkron dengan get out
        fr = tmp / "getout_beku.png"
        src_bk = bk.get("input") or rencana.get("input") or rencana.get("sumber", [{}])[-1].get("input")
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{float(bk['detik']):.3f}", "-i", src_bk,
             "-frames:v", "1", "-update", "1", fr], quiet=True)
        iw, ih = Image.open(fr).size
        bx, by, bw, bh = bk["box"]
        cx, cy = bx + bw / 2, by + bh / 2
        sx, sy, sw, sh = bk.get("stream_box") or rencana.get("stream_box") or [0, 0, iw, ih]
        h0 = sh; w0 = h0 * KW / KH                    # awal: irisan setinggi stream, rasio kanvas
        h1 = max(bh, bw * KH / KW); w1 = h1 * KW / KH  # akhir: kotak kerusakan
        tz = float(bk.get("waktu_zoom", 0.3))
        img = Image.open(fr).convert("RGB")
        x0 = min(max(cx - w0 / 2, sx), sx + sw - w0); y0 = sy
        x1 = min(max(cx - w1 / 2, sx), sx + sw - w1); y1 = min(max(cy - h1 / 2, sy), sy + sh - h1)
        fdir = tmp / "getout_fr"
        fdir.mkdir(exist_ok=True)
        n = int(round(d * float(FPS)))
        for k in range(n):
            u = 1 - (1 - min(k / float(FPS) / tz, 1)) ** 3   # ease-out cubic: punch-zoom cepat lalu diam
            cw, ch = w0 + (w1 - w0) * u, h0 + (h1 - h0) * u
            px, py = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
            img.crop((int(px), int(py), int(px + cw), int(py + ch))).resize((KW, KH), Image.LANCZOS).save(
                fdir / f"{k:04d}.png")
        vf = "[0:v]unsharp=5:5:0.5,setsar=1,format=yuv420p[v]"
        vin = ["-framerate", FPS, "-i", fdir / "%04d.png"]
        lanjut = 0.0
    elif lanjut >= 0.1 and banding:
        ekor_banding(rencana, tmp, lanjut + 0.1, vid)
        vf = f"[0:v]fps={FPS},tpad=stop_mode=clone:stop_duration={d:.3f},trim=duration={d:.3f},setsar=1,format=yuv420p[v]"
        vin = ["-i", vid]
    elif lanjut >= 0.1:  # lanjutan rekaman, layout sama, tanpa efek/caption/sfx
        r2 = {k: v for k, v in rencana.items() if k not in (
            "buang", "glitch", "speedlines", "impact", "cam_penuh", "tutup", "zoom", "sfx_tambahan", "hook",
            "flash_awal", "judul", "caption", "caption_frasa", "_caption", "cam_hd", "get_out")}
        r2["potong"] = [akhir, akhir + lanjut]
        r2["tanpa_sfx"] = True
        inputs, f, amap2, _ = bangun(r2, tmp)
        if amap2:
            f.append("[aout]anullsink")
        run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(f), "-map", "[vout]",
             "-t", f"{lanjut:.3f}", "-r", FPS, "-c:v", "libx264", "-preset", "medium", "-crf", "17", vid],
            quiet=True)
        vf = f"[0:v]fps={FPS},tpad=stop_mode=add:stop_duration={d:.3f}:color=black,trim=duration={d:.3f},setsar=1,format=yuv420p[v]"
        vin = ["-i", vid]
    elif not bk:
        vf = f"[0:v]setsar=1,format=yuv420p[v]"
        vin = ["-f", "lavfi", "-t", f"{d:.3f}", "-i", f"color=black:s={KW}x{KH}:r={FPS}"]
    out = tmp / "getout.mp4"
    run(["ffmpeg", "-v", "error", "-y", *vin, "-i", sfx, "-filter_complex",
         vf + f";[1:a]aresample=44100,aformat=channel_layouts=stereo,volume={float(cfg.get('volume', 1.0)):.2f},"
         f"apad=whole_dur={d:.3f}[a]",
         "-map", "[v]", "-map", "[a]", "-t", f"{d:.3f}", "-r", FPS, "-c:v", "libx264", "-preset", "medium",
         "-crf", "17", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", out], quiet=True)
    print(f"  get out: {d:.2f} dtk ({'frame beku + zoom' if bk else f'video mengalir {lanjut:.2f} dtk'}, {Path(sfx).name})")
    return out


def render(rencana_path, pratinjau=False):
    rencana = json.loads(Path(rencana_path).read_text(encoding="utf-8"))
    rencana["_rencana_path"] = str(rencana_path)
    out = Path(rencana.get("output") or Path(rencana_path).with_suffix(".mp4"))
    out.parent.mkdir(parents=True, exist_ok=True)
    banding = rencana.get("format") in FORMAT_BANDING
    KW, KH = kanvas(rencana)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        if pratinjau and banding:  # gambar diam di beberapa detik (render potongan 0,2 dtk)
            titik = rencana.get("pratinjau_detik") or [round(durasi_banding(rencana) * u, 1) for u in (0.1, 0.5, 0.9)]
            gambar = []
            for t in titik:
                v = tmp / f"pv_{t}.mp4"
                bg = {}
                if rencana["format"] == "banding":
                    _render_bersamaan(rencana, tmp, float(t), 0.3, v, audio=False)
                else:
                    sisa, bgp = float(t), None
                    for k, bg in enumerate(rencana["bagian"]):
                        dd = float(bg.get("durasi", 2.5)) if bg.get("kartu") else bg["potong"][1] - bg["potong"][0]
                        if sisa < dd or k == len(rencana["bagian"]) - 1:
                            bgp = (k, bg, sisa)
                            break
                        sisa -= dd
                    k, bg, sisa = bgp
                    pot = None if bg.get("kartu") else [bg["potong"][0] + sisa, bg["potong"][0] + sisa + 0.3]
                    _render_bagian(rencana, bg, tmp, k, v, potong=pot, audio=False)
                p = tmp / f"p_{t}.png"
                seek = ["-ss", "0.4"] if rencana["format"] == "berurutan" and bg.get("kartu") else []
                run(["ffmpeg", "-v", "error", "-y", *seek, "-i", v, "-frames:v", "1", p], quiet=True)
                gambar.append(Image.open(p).convert("RGB").resize((360, int(360 * KH / KW))))
            lembar = Image.new("RGB", (360 * len(gambar), int(360 * KH / KW)))
            for i, g in enumerate(gambar):
                lembar.paste(g, (360 * i, 0))
            pp = out.with_name(out.stem + "_pratinjau.jpg")
            lembar.save(pp, quality=90)
            print("Pratinjau:", pp, "detik", titik)
            return
        if pratinjau:
            cf = rencana.get("caption_frasa")  # caption ikut tampil di pratinjau bila sudah ada
            cpath = Path(cf) if isinstance(cf, str) else Path(rencana_path).with_name(Path(rencana_path).stem + "_caption.json")
            if isinstance(cf, list):
                rencana["_caption"] = cf
            elif cf and cpath.exists():
                rencana["_caption"] = json.loads(cpath.read_text(encoding="utf-8"))
            info = probe(rencana["input"])
            t0, t1 = rencana.get("potong") or [0, info["durasi"]]
            titik = rencana.get("pratinjau_detik") or [round((t1 - t0) * u, 1) for u in (0.1, 0.5, 0.9)]
            gambar = []
            for t in titik:
                inputs, f, _, _ = bangun(rencana, tmp, pratinjau=t)
                p = tmp / f"p_{t}.png"
                run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(f),
                     "-map", "[vout]", "-frames:v", "1", p], quiet=True)
                gambar.append(Image.open(p).convert("RGB").resize((360, 640)))
            lembar = Image.new("RGB", (360 * len(gambar), 640))
            for i, g in enumerate(gambar):
                lembar.paste(g, (360 * i, 0))
            pp = out.with_name(out.stem + "_pratinjau.jpg")
            lembar.save(pp, quality=90)
            print("Pratinjau:", pp, "detik", titik)
            return
        # caption per frasa: transkrip otomatis ke <rencana>_caption.json (bisa dikoreksi lalu render ulang)
        cf = rencana.get("caption_frasa")
        if cf is True or isinstance(cf, str):
            cpath = Path(cf) if isinstance(cf, str) else Path(rencana_path).with_name(Path(rencana_path).stem + "_caption.json")
            if not cpath.exists():
                buat_caption_frasa(rencana, cpath)
            rencana["_caption"] = json.loads(cpath.read_text(encoding="utf-8"))
            print(f"  caption: {cpath} ({len(rencana['_caption'])} frasa)")
        elif isinstance(cf, list):
            rencana["_caption"] = cf
        cek_aman(rencana)
        if not banding:
            inputs, f, amap, dur = bangun(rencana, tmp)
        # endcard template program WAJIB di akhir setiap video, utuh tanpa efek/filter
        if "endcard" not in rencana:
            calon = sorted(p for p in ENDCARD_DIR.glob("*") if p.suffix.lower() in (".mp4", ".mov")) if ENDCARD_DIR.exists() else []
            rencana["endcard"] = str(calon[0]) if calon else None
        if not rencana.get("endcard"):
            print("  PERINGATAN: belum ada endcard template 3 detik (assets/endcard/). Video ini BELUM memenuhi "
                  "aturan program - jangan diposting sebelum endcard dipasang.")
        bagian = []
        if rencana.get("hook"):
            bagian.append(buat_hook(rencana, tmp))
        utama = tmp / "utama.mp4"
        if banding:
            render_banding(rencana, tmp, utama)
            dur = durasi_banding(rencana)
        else:
            run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(f),
                 "-map", "[vout]", *amap, "-r", FPS, "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                 "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", utama])
        bagian.append(utama)
        if rencana.get("musik"):
            isi = tmp / "isi.mp4"
            sambung(bagian, isi, tmp, (KW, KH))
            isi_m = tmp / "isi_musik.mp4"
            pasang_musik(isi, isi_m, rencana["musik"])
            bagian = [isi_m]
        if rencana.get("get_out"):
            bagian.append(buat_get_out(rencana, rencana["get_out"], tmp))
        if rencana.get("endcard"):
            bagian.append(rencana["endcard"])
        sambung(bagian, out, tmp, (KW, KH))
    # versi siap upload: 1080x1920 (atau 1080x1080 untuk kanvas 1:1), bitrate maks 4,5 Mbps (sekitar 20-30 MB) - mudah disimpan di HP
    up = Path(rencana.get("output_upload") or out.with_name(out.stem + "_upload.mp4"))
    run(["ffmpeg", "-v", "error", "-y", "-i", out, "-c:v", "libx264", "-preset", "slow", "-crf", "21",
         "-maxrate", "4500k", "-bufsize", "9000k", "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-movflags", "+faststart", up], quiet=True)
    print(f"Siap upload: {up} ({up.stat().st_size / 1048576:.0f} MB)")
    total = sum(probe(b)["durasi"] for b in [out])
    print(f"Selesai: {out} (klip {dur:.1f} dtk, total {total:.1f} dtk"
          + (", + kartu hook" if rencana.get("hook") else "") + (", + endcard)" if rencana.get("endcard") else ")"))


def pasang_musik(inp, out, mus):
    """Musik latar di bawah suara (kartu hook + klip; endcard tidak disentuh). Ducking otomatis:
    musik turun saat ada suara Windah/game, naik lagi saat sepi."""
    if mus is True:
        mus = {}
    if isinstance(mus, str):
        mus = {"file": mus}
    if not mus.get("file"):  # "musik": true -> backsound hasil sinkron-sfx (yang terbaru)
        calon = sorted((SKILL / "musik").glob("*_loop.wav"), key=lambda p: p.stat().st_mtime)
        if not calon:
            raise SystemExit("Belum ada backsound: jalankan `klip-windah sinkron-sfx` dulu.")
        mus = {**mus, "file": str(calon[-1])}
    f = Path(mus["file"])
    if not f.is_absolute() and not f.exists():
        f = SKILL / f
    dur = probe(inp)["durasi"]
    vol = float(mus.get("volume_db", -15))
    fc = (f"[1:a]aresample=44100,aformat=channel_layouts=stereo,atrim=0:{dur:.3f},asetpts=PTS-STARTPTS,"
          f"volume={vol}dB,afade=t=in:d=0.3,afade=t=out:st={max(0, dur - 0.8):.3f}:d=0.8[m];"
          f"[0:a]aresample=44100,aformat=channel_layouts=stereo,asplit=2[v][sc];"
          f"[m][sc]sidechaincompress=threshold=0.03:ratio={float(mus.get('duck_ratio', 6))}:attack=15:release=400[md];"
          f"[v][md]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95,"
          f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100[a]")
    run(["ffmpeg", "-v", "error", "-y", "-i", inp, "-stream_loop", "-1", "-i", f, "-filter_complex", fc,
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])


def sambung(bagian, out, tmp, ukuran=None):
    """Sambung beberapa video jadi satu. Bagian tidak diubah selain disamakan ukuran/fps/audio
    (endcard tetap utuh tanpa efek)."""
    if len(bagian) == 1:
        shutil.copy(bagian[0], out)
        return
    args, fc, lab = [], [], ""
    k = 0
    for i, b in enumerate(bagian):
        args += ["-i", str(b)]
    extra = len(bagian)
    for i, b in enumerate(bagian):
        bi = probe(b)
        KW, KH = ukuran or (W, H)
        fc.append(f"[{i}:v]scale={KW}:{KH}:force_original_aspect_ratio=decrease,pad={KW}:{KH}:(ow-iw)/2:(oh-ih)/2:black,"
                  f"fps={FPS},setsar=1,format=yuv420p[v{i}]")
        if bi["audio"]:
            fc.append(f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo[a{i}]")
        else:
            args += ["-f", "lavfi", "-t", f"{bi['durasi']:.3f}", "-i", "anullsrc=r=44100:cl=stereo"]
            fc.append(f"[{extra}:a]anull[a{i}]")
            extra += 1
        lab += f"[v{i}][a{i}]"
    fc.append(f"{lab}concat=n={len(bagian)}:v=1:a=1[v][a]")
    run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", ";".join(fc),
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])


# ---------------------------------------------------------------- caption per frasa
def segmen_simpan(rencana):
    info = probe(rencana["input"])
    t0, t1 = rencana.get("potong") or [0, info["durasi"]]
    dsrc = t1 - t0
    simpan, pos = [], 0.0
    for a, b in sorted([float(a), float(b)] for a, b in rencana.get("buang", [])):
        if a > pos:
            simpan.append((pos, a))
        pos = max(pos, b)
    if pos < dsrc:
        simpan.append((pos, dsrc))
    return t0, dsrc, simpan


def buat_caption_frasa(rencana, cpath, maks_kata=4):
    """Transkrip audio timeline HASIL (setelah potong+buang) dengan waktu per kata, lalu kelompokkan
    jadi frasa 2-4 kata. Hasil: [[mulai, selesai, "TEKS"], ...] di cpath."""
    from faster_whisper import WhisperModel
    t0, dsrc, simpan = segmen_simpan(rencana)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{dsrc:.3f}", "-i", rencana["input"],
                          "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
    # transkrip audio UTUH (menggabung potongan membuat Whisper bingung), lalu petakan waktu kata
    # ke timeline hasil; kata di bagian yang dibuang ikut dibuang
    a = np.frombuffer(raw, dtype=np.float32).copy()

    def ke_hasil(t):
        pos = 0.0
        for x, y in simpan:
            if x <= t <= y:
                return pos + t - x
            pos += y - x
        return None

    m = WhisperModel(rencana.get("model_caption", "small"), device="cpu", compute_type="int8")
    # tanpa initial_prompt & tanpa konteks sebelumnya: mencegah halusinasi kata berulang
    # VAD peka (suara Windah sering pelan di bawah suara game)
    segs, _ = m.transcribe(a, language="id", word_timestamps=True, vad_filter=True,
                           vad_parameters=dict(threshold=0.25, min_silence_duration_ms=300),
                           condition_on_previous_text=False, no_speech_threshold=0.9)
    frasa, cur = [], []
    for s_ in segs:
        for w in s_.words:
            kata = w.word.strip()
            ws, we = ke_hasil(w.start), ke_hasil(w.end)
            if not kata or ws is None:
                continue
            w = type("K", (), {"start": ws, "end": we if we is not None else ws + 0.3})
            if cur and (len(cur) >= maks_kata or w.start - cur[-1][1] > 0.45):
                frasa.append(cur)
                cur = []
            cur.append((w.start, w.end, kata))
            if kata[-1] in ".,!?":
                frasa.append(cur)
                cur = []
    if cur:
        frasa.append(cur)
    hasil, sblm = [], None
    for fr in frasa:
        teks = " ".join(k for _, _, k in fr).strip(" .,").upper()
        if teks == sblm or len(set(k.lower().strip(".,!?") for _, _, k in fr)) == 1 and len(fr) > 2:
            continue  # buang pengulangan (tanda halusinasi / tidak terbaca)
        sblm = teks
        mulai, selesai = fr[0][0], min(max(fr[-1][1], fr[0][0] + 0.6), fr[0][0] + 2.5)
        hasil.append([round(mulai, 2), round(selesai, 2), teks])
    for i in range(len(hasil) - 1):  # tahan sampai frasa berikut (maks 0,6 dtk jeda)
        hasil[i][1] = round(min(max(hasil[i][1], hasil[i + 1][0] - 0.6), hasil[i + 1][0]), 2)
    cpath.write_text(json.dumps(hasil, indent=1, ensure_ascii=False), encoding="utf-8")
    print("  transkrip caption:")
    for h in hasil:
        print(f"    {h[0]:6.2f}-{h[1]:6.2f}  {h[2]}")


def gambar_caption_frasa(teks, path, size=64, maxw=W - 140, warna="white"):
    """Gaya referensi: kapital, condensed tebal (Anton), putih, outline hitam + bayangan."""
    f = font(FONT_JUDUL, size, bold=False)
    baris = bungkus(teks.upper(), f, size, maxw)
    lh = int(size * 1.12)
    lebar = int(max(ukur(b, f, size) for b in baris)) + 40
    tinggi = lh * len(baris) + 30
    img = Image.new("RGBA", (lebar, tinggi), (0, 0, 0, 0))
    bay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    for i, b in enumerate(baris):
        x = (lebar - ukur(b, f, size)) / 2
        tulis(bay, (x + 4, 12 + i * lh + 5), b, f, size, fill=(0, 0, 0, 170), stroke=6, stroke_fill=(0, 0, 0, 170))
    img.alpha_composite(bay)
    for i, b in enumerate(baris):
        x = (lebar - ukur(b, f, size)) / 2
        tulis(img, (x, 12 + i * lh), b, f, size, fill=warna, stroke=6, stroke_fill="black")
    img.save(path)
    return img.size


# ---------------------------------------------------------------- gaya viral (analisis 5 video >100 rb, 21 Nov 2026)
WARNA = {"putih": (255, 255, 255), "merah": (255, 48, 48), "kuning": (255, 205, 0), "oranye": (255, 140, 0),
         "hijau": (80, 230, 90), "pink": (255, 70, 170), "hitam": (0, 0, 0)}
KATA_SAMBUNG = set("""yang dan di ke dari ini itu aja aj sih deh dong kok kan lah nih tuh ya yah gue gua lu lo
aku kamu kita kami mereka dia ada udah sudah mau bisa jadi buat sama juga lagi gak nggak ga enggak tidak
apa kenapa gimana kayak kaya terus trus pas saat kalo kalau tapi karena biar the a to and is it you i""".split())


def kata_kunci(teks):
    """Caption 1 kata (gaya akun4): kata terpanjang yang bukan kata sambung."""
    kata = [k.strip(".,!?\"'") for k in teks.split()]
    calon = [k for k in kata if k and k.lower() not in KATA_SAMBUNG] or [k for k in kata if k] or [teks]
    return max(calon, key=len).upper()


def gambar_bar_judul(teks, path, lebar=W, gaya="hitam", size=56):
    """Bar judul statis gaya referensi viral: bar putih selebar layar, teks kapital tebal.
    gaya "hitam" = teks hitam (akun5/akun1); "outline" = teks putih outline hitam (akun3)."""
    if gaya == "outline":
        f = font(FONT_JUDUL, int(size * 1.15), bold=False)
        size = int(size * 1.15)
    else:
        f = font(FONT_TEKS, size, bold=False)
        for v in ("Black", "ExtraBold", "Bold"):
            try:
                f.set_variation_by_name(v)
                break
            except Exception:
                pass
    baris = bungkus(teks.upper(), f, size, lebar - 70)
    lh = int(size * 1.18)
    pad = int(size * 0.42)
    img = Image.new("RGBA", (lebar, lh * len(baris) + 2 * pad), (255, 255, 255, 255))
    for i, b in enumerate(baris):
        x = (lebar - ukur(b, f, size)) / 2
        if gaya == "outline":
            tulis(img, (x, pad + i * lh - size * 0.05), b, f, size, fill="white", stroke=6, stroke_fill="black")
        else:
            tulis(img, (x, pad + i * lh - size * 0.12), b, f, size, fill=(0, 0, 0))
    img.save(path)
    return img.size


def gambar_label(teks, path, size=62, warna="white"):
    """Label nama di panel banding ("MIAWAUG :") / teks stiker reaksi: tebal, outline hitam."""
    f = font(FONT_TEKS, size, bold=False)
    for v in ("Black", "ExtraBold", "Bold"):
        try:
            f.set_variation_by_name(v)
            break
        except Exception:
            pass
    lebar = int(ukur(teks, f, size)) + 30
    img = Image.new("RGBA", (lebar, int(size * 1.45)), (0, 0, 0, 0))
    tulis(img, (15, size * 0.1), teks, f, size, fill=WARNA.get(warna, warna), stroke=max(4, size // 11),
          stroke_fill="black")
    img.save(path)
    return img.size


KATA_EKSPLISIT = ["telanjang", "bugil", "ngentot", "ngewe", "porno", "bokep", "coli", "memek", "kontol", "toket",
                  "payudara", "sange", "horny", "nude", "naked", "sex", "seks", "nenen", "vagina", "penis"]


def cek_aman(rencana):
    """Peringatan bila teks di layar terlalu eksplisit (konten sus harus sindiran, bukan vulgar)."""
    teks = []
    for k in ("judul", "bar_judul", "caption", "judul_sub"):
        if isinstance(rencana.get(k), str):
            teks.append(rencana[k])
    hk = rencana.get("hook") or {}
    teks += hk.get("teks", [])
    for sb in rencana.get("sumber", []) + [b for b in rencana.get("bagian", []) if isinstance(b, dict)]:
        teks += [str(sb.get("label", "")), str(sb.get("kartu", "")), str(sb.get("sub", ""))]
    teks += [str(s_[2]) for s_ in rencana.get("stiker", []) if isinstance(s_, list) and len(s_) > 2]
    teks += [c[2] for c in rencana.get("_caption") or []]
    kena = sorted({k for t in teks for k in KATA_EKSPLISIT if re.search(rf"\b{k}", t.lower())})
    if kena:
        print(f"  PERINGATAN: teks di layar terlalu eksplisit ({', '.join(kena)}). Konten sus harus sindiran -"
              f" TikTok bisa membatasi/menghapus video. Ganti kata-katanya sebelum posting.")
    return kena


# ---------------------------------------------------------------- kartu hook
_rembg_sesi = {}


def cutout(img, model="u2net_human_seg"):
    """Hapus latar (rembg u2net_human_seg, sekitar 170 MB diunduh sekali)."""
    from rembg import remove, new_session
    if model not in _rembg_sesi:
        _rembg_sesi[model] = new_session(model)
    return remove(img.convert("RGB"), session=_rembg_sesi[model]).convert("RGBA")


def buat_elemen(src, t, el):
    """Elemen pendukung kartu hook (mis. Bigfoot, pesawat): 'cutout' (latar dihapus, bingkai putih)
    atau 'kartu' (foto berbingkai putih, sedikit miring). Hasil RGBA dengan bayangan."""
    from PIL import ImageFilter
    if el.get("gambar"):  # file gambar dari pengguna (mis. foto streamer lain), bukan frame video
        gp = Path(el["gambar"])
        fr = Image.open(gp if gp.exists() else SKILL / gp).convert("RGB")
        x, y, w, h = el.get("box") or [0, 0, fr.width, fr.height]
    else:
        fr = ambil_frame_sumber(src, t)
        x, y, w, h = el["box"]
    im = fr.crop((x, y, x + w, y + h))
    lebar = int(el.get("lebar", 560))
    if el.get("gaya", "cutout") == "cutout":
        im = cutout(im, el.get("model", "isnet-general-use"))
        # alpha tegas + hanya objek terbesar (tanpa sisa latar transparan seperti hantu)
        import cv2
        a = np.array(im.getchannel("A"))
        biner = (a > int(el.get("ambang", 100))).astype(np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(biner, 8)
        if n > 1:
            terbesar = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
            biner = (lab == terbesar).astype(np.uint8)
        biner = cv2.morphologyEx(biner, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        im.putalpha(Image.fromarray((biner * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1)))
        bb = im.getchannel("A").getbbox()
        if bb:
            im = im.crop(bb)
        im = im.resize((lebar, int(im.height * lebar / im.width)), Image.LANCZOS)
        a = im.getchannel("A")
        garis = a.filter(ImageFilter.MaxFilter(13))
        lap = Image.new("RGBA", (im.width + 50, im.height + 50), (0, 0, 0, 0))
        bay = Image.new("RGBA", lap.size, (0, 0, 0, 0))
        bay.paste((0, 0, 0, 160), (31, 37), garis)
        lap.alpha_composite(bay.filter(ImageFilter.GaussianBlur(12)))
        lap.paste((255, 255, 255, 255), (25, 25), garis)
        lap.alpha_composite(im, (25, 25))
    else:
        im = im.convert("RGBA").resize((lebar, int(h * lebar / w)), Image.LANCZOS)
        b = 12
        kartu = Image.new("RGBA", (im.width + 2 * b, im.height + 2 * b), (255, 255, 255, 255))
        kartu.alpha_composite(im, (b, b))
        m = Image.new("L", kartu.size, 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, kartu.width - 1, kartu.height - 1], 22, fill=255)
        kartu.putalpha(m)
        lap = Image.new("RGBA", (kartu.width + 60, kartu.height + 60), (0, 0, 0, 0))
        bay = Image.new("RGBA", lap.size, (0, 0, 0, 0))
        bay.paste((0, 0, 0, 170), (36, 42), m)
        lap.alpha_composite(bay.filter(ImageFilter.GaussianBlur(14)))
        lap.alpha_composite(kartu, (30, 30))
    sudut = float(el.get("miring", 4 if el.get("gaya") == "kartu" else 0))
    if sudut:
        lap = lap.rotate(sudut, resample=Image.BICUBIC, expand=True)
    return lap



def overlay_popup(popup, tmp, tambah, cur, f, kw, kh, awal="pp"):
    """Gambar pop-up di atas video (mis. foto Reza Arap saat namanya disebut): cutout/kartu berbingkai putih,
    muncul dengan fade cepat. popup: [{"gambar", "mulai", "selesai", "gaya": "cutout"|"kartu",
    "model": "u2net_human_seg", "lebar": px, "x": 0-1, "y": 0-1 (titik tengah), "miring": derajat}]."""
    for k, el in enumerate(popup):
        img = buat_elemen(None, 0, {"gaya": "kartu", "model": "u2net_human_seg", **el})
        pth = tmp / f"{awal}{k}.png"
        img.save(pth)
        a, b = float(el["mulai"]), float(el["selesai"])
        px = even(kw * float(el.get("x", 0.75)) - img.width / 2)
        py = even(kh * float(el.get("y", 0.45)) - img.height / 2)
        i = tambah("-loop", "1", "-framerate", str(FPS), "-t", f"{b + 0.5:.3f}", "-i", pth)
        f.append(f"[{i}:v]format=rgba,fade=in:st={a:.3f}:d=0.12:alpha=1,fade=out:st={max(a, b - 0.15):.3f}:d=0.15:alpha=1[{awal}i{k}]")
        f.append(f"[{cur}][{awal}i{k}]overlay={px}:{py}:eof_action=pass:enable='between(t,{a:.3f},{b:.3f})'[{awal}o{k}]")
        cur = f"{awal}o{k}"
    return cur


def ambil_frame_sumber(src, t):
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "f.png"
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", src, "-frames:v", "1", p], quiet=True)
        return Image.open(p).convert("RGB")


def buat_hook(rencana, tmp):
    """Kartu hook ala thumbnail (gaya referensi): latar game diburamkan, cutout wajah Windah besar
    berbingkai putih, teks 3 baris kontras (putih/merah/kuning, outline tebal), watermark di safe zone.
    Animasi: blur->tajam + punch-zoom masuk, zoom pelan, glitch RGB, flash putih keluar. SFX otomatis."""
    from PIL import ImageFilter, ImageEnhance, ImageChops
    hk = rencana["hook"]
    src = rencana["input"]
    t0 = (rencana.get("potong") or [0, 0])[0]
    dur = float(hk.get("durasi", 2.6))
    stream = rencana.get("stream_box")
    cam = rencana["cam_box"]

    # latar: frame game penuh layar, blur, sedikit gelap + gradasi bawah
    fg = ambil_frame_sumber(src, t0 + hk.get("detik_latar", 0))
    sx, sy, sw, sh = stream or [0, 0, fg.width, fg.height]
    cw = min(sw, sh * W / H)
    lat = fg.crop((int(sx + (sw - cw) / 2), sy, int(sx + (sw + cw) / 2), sy + sh)).resize((W, H), Image.LANCZOS)
    lat = ImageEnhance.Brightness(lat.filter(ImageFilter.GaussianBlur(float(hk.get("blur_latar", 18))))).enhance(0.75).convert("RGBA")
    grad = Image.new("RGBA", (W, 900), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for yy in range(900):
        gd.line([(0, yy), (W, yy)], fill=(0, 0, 0, int(220 * (yy / 900) ** 1.5)))
    lat.alpha_composite(grad, (0, H - 900))

    # teks 3 baris: baris tengah paling besar; kata dalam "sorot" diwarnai
    baris = hk["teks"]
    warna_baris = hk.get("warna", ["putih", "putih", "kuning"])
    peta = {"putih": (255, 255, 255), "merah": (255, 48, 48), "kuning": (255, 205, 0), "oranye": (255, 140, 0),
            "hijau": (80, 230, 90), "pink": (255, 70, 170)}
    skala = hk.get("skala", [0.8, 1.0, 0.72])
    sorot = {k.upper(): peta.get(v, (255, 48, 48)) for k, v in hk.get("sorot", {}).items()}
    besar = int(hk.get("ukuran_teks", 150))
    blok = []
    for i, b in enumerate(baris):
        sz = int(besar * (skala[i] if i < len(skala) else 0.8))
        while True:
            ft = font(FONT_JUDUL, sz, bold=False)
            if ukur(b.upper(), ft, sz) <= W - 90 or sz < 50:
                break
            sz -= 4
        blok.append((b.upper(), ft, sz, peta.get(warna_baris[i] if i < len(warna_baris) else "putih", (255, 255, 255))))
    tinggi_blok = sum(int(sz * 1.02) for _, _, sz, _ in blok)
    ty = int(hk.get("y_teks", 1430 - tinggi_blok))
    teks_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    yy = ty
    for b, ft, sz, wr in blok:
        x = (W - ukur(b, ft, sz)) / 2
        bay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        tulis(bay, (x + 6, yy + 8), b, ft, sz, fill=(0, 0, 0, 200), stroke=max(8, sz // 11), stroke_fill=(0, 0, 0, 200))
        teks_img.alpha_composite(bay.filter(ImageFilter.GaussianBlur(4)))
        tulis(teks_img, (x, yy), b, ft, sz, fill=wr, stroke=max(8, sz // 11), stroke_fill="black", warna_kata=sorot)
        yy += int(sz * 1.02)

    # wajah: cutout dari cam, diperbesar, bingkai putih + bayangan
    fc = ambil_frame_sumber(src, t0 + hk.get("detik_wajah", hk.get("detik_latar", 0)))
    x, y, w, h = cam
    wj = cutout(fc.crop((x, y, x + w, y + h)))
    bb = wj.getchannel("A").getbbox()
    if bb:
        wj = wj.crop(bb)
    el = hk.get("elemen")
    lebar_wajah = int(hk.get("lebar_wajah", 640 if el else 880))
    wj = wj.resize((lebar_wajah, int(wj.height * lebar_wajah / wj.width)), Image.LANCZOS)
    # bagian bawah memudar (potongan cam lurus tidak terlihat kaku)
    pudar = Image.linear_gradient("L").resize((wj.width, wj.height))
    pudar = pudar.point(lambda v: 255 if v < 160 else int(255 * (255 - v) / 95))
    wj.putalpha(ImageChops.multiply(wj.getchannel("A"), pudar))
    alpha = wj.getchannel("A")
    garis = alpha.filter(ImageFilter.MaxFilter(17))
    lapis = Image.new("RGBA", (wj.width + 60, wj.height + 60), (0, 0, 0, 0))
    bay = Image.new("RGBA", lapis.size, (0, 0, 0, 0))
    bay.paste((0, 0, 0, 150), (36, 44), garis)
    lapis.alpha_composite(bay.filter(ImageFilter.GaussianBlur(14)))
    lapis.paste((255, 255, 255, 255), (30, 30), garis)
    lapis.alpha_composite(wj, (30, 30))
    depan = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # wajah di atas teks: teks hanya menutupi dada/tangan (seperti referensi)
    wy_wajah = int(hk.get("y_wajah", ty - lapis.height * float(hk.get("naik_wajah", 0.74))))
    if el:
        # dua gambar: elemen pendukung di kanan (di belakang), Windah di kiri (di depan)
        eimg = buat_elemen(src, t0 + float(el.get("detik", hk.get("detik_latar", 0))), el)
        ex = int(W * float(el.get("x", 0.70)) - eimg.width / 2)
        ey = int(el.get("y", ty - eimg.height * float(el.get("naik", 0.8))))
        depan.alpha_composite(eimg, (max(-40, min(W - eimg.width + 40, ex)), max(260, ey)))
        wx = int(W * float(hk.get("x_wajah", 0.30)) - lapis.width / 2)
        depan.alpha_composite(lapis, (max(-30, wx), max(300, wy_wajah)))
    else:
        depan.alpha_composite(lapis, ((W - lapis.width) // 2, max(300, wy_wajah)))
    depan.alpha_composite(teks_img)

    # watermark program (wajib) di safe zone atas
    wm = rencana.get("watermark", str(WATERMARK) if WATERMARK.exists() else None)
    wm_img = None
    if wm:
        wi = Image.open(wm).convert("RGBA")
        ww = int(W * 0.68)
        wm_img = wi.resize((ww, int(wi.height * ww / wi.width)), Image.LANCZOS)

    # animasi per frame
    fdir = tmp / "hook"
    fdir.mkdir(exist_ok=True)
    n = int(round(dur * FPS))
    for i in range(n):
        t = i / FPS
        if t < 0.3:  # masuk: blur -> tajam, zoom 1.18 -> 1.0
            u = 1 - (1 - t / 0.3) ** 3
            zoom, blur = 1.18 - 0.18 * u, 22 * (1 - u)
        else:
            zoom, blur = 1.0 + 0.035 * (t - 0.3) / max(0.1, dur - 0.3), 0
        bg = lat.resize((int(W * (1 + 0.04 * t / dur)), int(H * (1 + 0.04 * t / dur))))
        bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
        fz = depan.resize((int(W * zoom), int(H * zoom)), Image.BILINEAR)
        fz = fz.crop(((fz.width - W) // 2, (fz.height - H) // 2, (fz.width - W) // 2 + W, (fz.height - H) // 2 + H))
        fr = bg.copy()
        fr.alpha_composite(fz)
        if wm_img:
            fr.alpha_composite(wm_img, ((W - wm_img.width) // 2, 170))
        fr = fr.convert("RGB")
        if blur:
            fr = fr.filter(ImageFilter.GaussianBlur(blur))
        if dur - 0.45 <= t < dur - 0.25:  # glitch RGB
            r, g, b_ = fr.split()
            fr = Image.merge("RGB", (ImageChops.offset(r, -18, 0), g, ImageChops.offset(b_, 18, 4)))
        if t >= dur - 0.25:  # flash putih keluar
            u = (t - (dur - 0.25)) / 0.25
            fr = Image.blend(fr.filter(ImageFilter.GaussianBlur(10 * u)), Image.new("RGB", (W, H), "white"), min(1, u * 1.1))
        fr.save(fdir / f"{i:04d}.png")

    # audio: SFX + (opsional) cuplikan suara asli
    out = tmp / "hook.mp4"
    args = ["-framerate", str(FPS), "-i", fdir / "%04d.png"]
    fc = []
    lab = []
    if any((SFX_DIR / f"sting.{e}").exists() for e in ("wav", "mp3")):
        sfx = [("sting", 0.0, 0.9), (rencana.get("sfx_transisi", SFX_TRANSISI), dur - 0.35, 0.8)]
    else:
        sfx = [("whoosh", 0.0, 0.9), ("boom", 0.22, 0.8), (rencana.get("sfx_transisi", SFX_TRANSISI), dur - 0.35, 0.8)]
    for k, (nama, t, vol) in enumerate(sfx):
        args += ["-i", sfx_path(nama)]
        ms = int(t * 1000)
        fc.append(f"[{k + 1}:a]aresample=44100,aformat=channel_layouts=stereo,adelay={ms}|{ms},volume={vol}[s{k}]")
        lab.append(f"[s{k}]")
    if hk.get("audio_asli"):
        a, b = hk["audio_asli"]
        args += ["-ss", f"{t0 + a:.3f}", "-t", f"{b - a:.3f}", "-i", src]
        k = len(sfx) + 1
        fc.append(f"[{k}:a]aresample=44100,aformat=channel_layouts=stereo,volume=0.9[asli]")
        lab.append("[asli]")
    fc.append("".join(lab) + f"amix=inputs={len(lab)}:normalize=0:duration=longest,atrim=0:{dur:.3f},"
              f"apad=whole_dur={dur:.3f},loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100[a]")
    run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[a]",
         "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-ar", "44100", out])
    print(f"  kartu hook: {dur:.1f} dtk")
    return out


def buat_cam_hd(rencana, out_path):
    """Upscale AI x4 panel cam di timeline HASIL (setelah potong+buang), dicampur dengan Lanczos agar natural.
    Lambat (~1 dtk/frame di CPU): jalankan di background."""
    import time
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from upscale import upscale
    t0, dsrc, simpan = segmen_simpan(rencana)
    x, y, w, h = map(even, rencana["cam_box"])
    campur = float(rencana.get("cam_hd_campur", 0.75))
    n_seg = len(simpan)
    fc = [f"[0:v]crop={w}:{h}:{x}:{y},fps={FPS},setpts=PTS-STARTPTS,split={n_seg}" + "".join(f"[c{k}]" for k in range(n_seg))]
    for k, (a, b) in enumerate(simpan):
        fc.append(f"[c{k}]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[t{k}]")
    fc.append("".join(f"[t{k}]" for k in range(n_seg)) + f"concat=n={n_seg}:v=1:a=0,format=rgb24[o]")
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{dsrc:.3f}", "-i", rencana["input"],
                            "-filter_complex", ";".join(fc), "-map", "[o]", "-f", "rawvideo", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w * 4}x{h * 4}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "14",
                            "-pix_fmt", "yuv420p", str(out_path)], stdin=subprocess.PIPE)
    ukuran = w * h * 3
    n, mulai = 0, time.time()
    total = int(sum(b - a for a, b in simpan) * FPS)
    while True:
        buf = dec.stdout.read(ukuran)
        if len(buf) < ukuran:
            break
        fr = np.frombuffer(buf, np.uint8).reshape(h, w, 3)
        ai = upscale(fr).astype(np.float32)
        lz = np.asarray(Image.fromarray(fr).resize((w * 4, h * 4), Image.LANCZOS), np.float32)
        enc.stdin.write(np.clip(ai * campur + lz * (1 - campur), 0, 255).astype(np.uint8).tobytes())
        n += 1
        if n % 60 == 0:
            el = time.time() - mulai
            print(f"  cam HD {n}/{total} frame, sisa ~{el / n * (total - n) / 60:.1f} menit", flush=True)
    enc.stdin.close()
    enc.wait()
    dec.wait()
    print(f"Cam HD selesai: {out_path} ({n} frame)")


def thumbnail(rencana_path):
    """Cover 9:16: frame game (mis. WASTED) + wajah Windah besar + teks besar ber-outline."""
    from PIL import ImageEnhance
    r = json.loads(Path(rencana_path).read_text(encoding="utf-8"))
    th = r["thumbnail"]
    src = r["input"]
    t0 = (r.get("potong") or [0, 0])[0]
    stream = r.get("stream_box")
    cam = r["cam_box"]
    out = Path(th.get("output") or Path(rencana_path).with_name(Path(rencana_path).stem + "_thumbnail.jpg"))

    def frame(t):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "f.png"
            run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0 + t:.3f}", "-i", src, "-frames:v", "1", p], quiet=True)
            return Image.open(p).convert("RGB")

    def cover_img(im, box, tw, th_, fokus_x=0.5, fokus_y=0.5, zoom=1.0):
        x, y, w, h = box
        cw = min(w, h * tw / th_) / zoom
        chh = cw * th_ / tw
        cx = x + (w - cw) * fokus_x
        cy = y + (h - chh) * fokus_y
        return im.crop((int(cx), int(cy), int(cx + cw), int(cy + chh))).resize((tw, th_), Image.LANCZOS)

    fg = frame(th.get("detik_game", 0))
    fc = frame(th.get("detik_cam", th.get("detik_game", 0)))
    if not stream:
        stream = [0, 0, fg.width, fg.height]
    gh = even(H * th.get("porsi_game", 0.58))
    ch = H - gh
    game = cover_img(fg, stream, W, gh, th.get("fokus_game_x", 0.5), th.get("fokus_game_y", 0.5),
                     th.get("zoom_game", 1.0))
    wajah = cover_img(fc, cam, W, ch, 0.5, th.get("fokus_cam_y", 0.4), th.get("zoom_cam", 1.0))
    game = ImageEnhance.Contrast(ImageEnhance.Color(game).enhance(1.25)).enhance(1.1)
    wajah = ImageEnhance.Contrast(ImageEnhance.Color(wajah).enhance(1.15)).enhance(1.08)
    kanvas = Image.new("RGBA", (W, H), "black")
    cam_atas = th.get("posisi_cam", "bawah") == "atas"
    kanvas.paste(wajah, (0, 0) if cam_atas else (0, gh))
    kanvas.paste(game, (0, ch) if cam_atas else (0, 0))

    # gelapkan area teks supaya terbaca
    teks_atas = th.get("posisi_teks", "atas") == "atas"
    grad = Image.new("RGBA", (W, 620), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for yy in range(620):
        a = int(190 * (1 - yy / 620) ** 1.6)
        gd.line([(0, yy), (W, yy)], fill=(0, 0, 0, a))
    if teks_atas:
        kanvas.alpha_composite(grad, (0, 0))
    else:
        kanvas.alpha_composite(grad.transpose(Image.FLIP_TOP_BOTTOM), (0, H - 620))

    teks = th["teks"].upper()
    sorot = {k.upper(): (255, 214, 0) for k in th.get("sorot", [])}
    size = int(th.get("ukuran_teks", 170))
    while True:
        f = font(FONT_JUDUL, size, bold=False)
        baris = bungkus(teks, f, size, W - 100)
        if len(baris) <= 3 and max(ukur(b, f, size) for b in baris) <= W - 100 or size <= 80:
            break
        size -= 6
    lh = int(size * 1.05)
    total = lh * len(baris)
    y = 80 if teks_atas else H - total - 110
    for b in baris:
        x = (W - ukur(b, f, size)) / 2
        tulis(kanvas, (x, y), b, f, size, fill="white", stroke=max(6, size // 14), stroke_fill="black",
              warna_kata=sorot)
        y += lh
    out.parent.mkdir(parents=True, exist_ok=True)
    kanvas.convert("RGB").save(out, quality=95)
    print("Thumbnail:", out)


# ---------------------------------------------------------------- format banding (perbandingan streamer)
FORMAT_BANDING = ("banding", "berurutan")


def kanvas(rencana):
    """Ukuran kanvas: format banding default 1:1 (seperti video 2,1 jt), selain itu 9:16."""
    k = rencana.get("kanvas", "1:1" if rencana.get("format") in FORMAT_BANDING else "9:16")
    return (1080, 1080) if k == "1:1" else (W, H)


def _wm_img(rencana, lebar):
    wm = rencana.get("watermark", str(WATERMARK) if WATERMARK.exists() else None)
    if not wm:
        return None, 0, 0
    wim = Image.open(wm)
    ww = even(lebar)
    return wm, ww, even(wim.height * ww / wim.width)


def _render_bersamaan(rencana, tmp, offset, durasi, out, audio=True):
    """Dua rekaman bertumpuk (atas/bawah), adegan sama berjalan bersamaan, label "NAMA :" di kiri atas panel."""
    KW, KH = kanvas(rencana)
    A, B = rencana["sumber"][:2]
    t0a = A["potong"][0] + offset
    t0b = float(B["mulai"]) + float(B.get("geser", 0)) + offset
    barh = 0
    if rencana.get("bar_judul"):
        _, barh = gambar_bar_judul(rencana["bar_judul"], tmp / "bar.png", KW, rencana.get("bar_gaya", "hitam"),
                                   int(rencana.get("bar_ukuran", 50 if KH == KW else 56)))
    wm, ww, wh = _wm_img(rencana, KW * float(rencana.get("watermark_skala", 0.6)))
    if KH == KW:  # 1:1: bar di atas, dua panel mengisi sisa tinggi; watermark di bawah panel bawah
        ph = even((KH - barh) / 2)
        y_bar, y_a = 0, barh
        y_b = y_a + ph
        wy = KH - wh - 14
    else:  # 9:16: blok (bar + watermark + 2 panel 16:9) di tengah
        ph = even(KW * 9 / 16)
        blok_h = barh + (wh + 24 if wm else 0) + 2 * ph
        y_bar = even(max(SAFE_ATAS - 60, (KH - blok_h) / 2))
        wy = y_bar + barh + 12
        y_a = y_bar + barh + (wh + 24 if wm else 0)
        y_b = y_a + ph
    args = ["-ss", f"{t0a:.3f}", "-t", f"{durasi:.3f}", "-i", A["input"],
            "-ss", f"{t0b:.3f}", "-t", f"{durasi:.3f}", "-i", B["input"]]
    n = 2
    fc = []
    for i, sb in enumerate((A, B)):
        info = probe(sb["input"])
        box = sb.get("stream_box") or [0, 0, info["w"], info["h"]]
        fc.append(f"[{i}:v]fps={FPS},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=5[r{i}]")
        fc.append(cover(f"r{i}", box, KW, ph, f"p{i}"))
    fc.append(f"color=black:s={KW}x{KH}:r={FPS}:d={durasi:.3f}[bg]")
    fc.append(f"[bg][p0]overlay=0:{y_a}[c0];[c0][p1]overlay=0:{y_b}:shortest=0[c1]")
    cur = "c1"
    for i, sb in enumerate((A, B)):
        if sb.get("label"):
            gambar_label(sb["label"], tmp / f"lab{i}.png", int(sb.get("label_ukuran", 58 if KH == KW else 62)))
            args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{durasi:.3f}", "-i", str(tmp / f"lab{i}.png")]
            fc.append(f"[{cur}][{n}:v]overlay=14:{(y_a if i == 0 else y_b) + 8}[cl{i}]")
            cur, n = f"cl{i}", n + 1
    if barh:
        args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{durasi:.3f}", "-i", str(tmp / "bar.png")]
        fc.append(f"[{cur}][{n}:v]overlay=0:{y_bar}[cb]")
        cur, n = "cb", n + 1
    if wm:
        args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{durasi:.3f}", "-i", str(wm)]
        op = float(rencana.get("watermark_opacity", 0.9))
        fc.append(f"[{n}:v]format=rgba,scale={ww}:{wh},colorchannelmixer=aa={op:.2f}[wmb];"
                  f"[{cur}][wmb]overlay=(W-w)/2:{even(rencana.get('watermark_y', wy))}[cw]")
        cur, n = "cw", n + 1
    fc.append(f"[{cur}]trim=duration={durasi:.3f},format=yuv420p[vout]")
    amap = []
    if audio:
        mode = rencana.get("audio", "campur")
        segs = mode if isinstance(mode, list) else [[0, 9999, mode]]
        for i, sb in enumerate((A, B)):
            nama = ("atas", "a") if i == 0 else ("bawah", "b")
            on = [(a - offset, b - offset) for a, b, m in segs if m in nama or m == "campur"]
            vol = float(sb.get("volume", 1.0))
            ex = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in on) or "0"
            fc.append(f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS,"
                      f"volume='{vol}*min(1,{ex})':eval=frame,apad=whole_dur={durasi:.3f}[au{i}]")
        fc.append(f"[au0][au1]amix=inputs=2:normalize=0:duration=longest,atrim=0:{durasi:.3f},"
                  f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100[aout]")
        amap = ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"]
    run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", ";".join(fc), "-map", "[vout]", *amap,
         "-t", f"{durasi:.3f}", "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "17", out])
    return out


def _render_bagian(rencana, bg, tmp, k, out, potong=None, audio=True):
    """Satu bagian format berurutan: rekaman (16:9 / cover 1:1 di bawah bar judul) atau kartu MEANWHILE."""
    KW, KH = kanvas(rencana)
    barh = 0
    if rencana.get("bar_judul") and not bg.get("kartu"):
        _, barh = gambar_bar_judul(rencana["bar_judul"], tmp / "bar.png", KW, rencana.get("bar_gaya", "hitam"),
                                   int(rencana.get("bar_ukuran", 50 if KH == KW else 56)))
    wm, ww, wh = _wm_img(rencana, KW * float(rencana.get("watermark_skala", 0.6)))
    if bg.get("kartu"):  # kartu hitam "MEANWHILE / in our universe" (akun1 200 rb)
        d = float(bg.get("durasi", 2.5))
        img = Image.new("RGBA", (KW, KH), (0, 0, 0, 255))
        fj = font(FONT_JUDUL, int(bg.get("ukuran", 150)), bold=False)
        teks = bg["kartu"].upper()
        size = int(bg.get("ukuran", 150))
        while ukur(teks, fj, size) > KW - 100:
            size -= 6
            fj = font(FONT_JUDUL, size, bold=False)
        tulis(img, ((KW - ukur(teks, fj, size)) / 2, KH / 2 - size * 0.75), teks, fj, size)
        if bg.get("sub"):
            fs = font(FONT_TEKS, int(size * 0.3))
            tulis(img, ((KW - ukur(bg["sub"], fs, size * 0.3)) / 2, KH / 2 + size * 0.42), bg["sub"], fs,
                  size * 0.3)
        img.save(tmp / f"kartu{k}.png")
        args = ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.3f}", "-i", str(tmp / f"kartu{k}.png")]
        fc = [f"[0:v]format=rgba,fade=in:st=0:d=0.12[c]"]
        cur, n = "c", 1
        sfx = sfx_path(bg["sfx"]) if bg.get("sfx") else None
        if sfx:
            args += ["-i", str(sfx)]
            fc.append(f"[1:a]aresample=44100,aformat=channel_layouts=stereo,apad=whole_dur={d:.3f}[aout]")
            n = 2
        else:
            args += ["-f", "lavfi", "-t", f"{d:.3f}", "-i", "anullsrc=r=44100:cl=stereo"]
            fc.append("[1:a]anull[aout]")
            n = 2
        wy = KH - wh - 14 if KH == KW else even(KH / 2 + 260)
    else:
        a, b = potong or bg["potong"]
        d = b - a
        info = probe(bg["input"])
        box = bg.get("stream_box") or [0, 0, info["w"], info["h"]]
        args = ["-ss", f"{a:.3f}", "-t", f"{d:.3f}", "-i", bg["input"]]
        if KH == KW:  # 1:1: gambar mengisi area di bawah bar (cover, crop tengah / fokus_x)
            ah, ay = KH - barh, barh
            bx, by_, bw_, bh_ = box
            r = KW / ah
            if bw_ / bh_ > r:
                nw = bh_ * r
                fx = float(bg.get("fokus_x", 0.5))
                box = [bx + (bw_ - nw) * fx, by_, nw, bh_]
            wy = KH - wh - 14
        else:  # 9:16: gambar 16:9 utuh di tengah, bar tepat di atasnya, watermark di bawahnya
            ah = even(KW * box[3] / box[2])
            ay = even((KH - ah) / 2)
            wy = ay + ah + 24
        fc = [f"[0:v]fps={FPS},setpts=PTS-STARTPTS[r]", cover("r", box, KW, ah, "p"),
              f"color=black:s={KW}x{KH}:r={FPS}:d={d:.3f}[bg]", f"[bg][p]overlay=0:{ay}[c]"]
        cur, n = "c", 1
        if barh:
            args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.3f}", "-i", str(tmp / "bar.png")]
            fc.append(f"[{cur}][{n}:v]overlay=0:{max(0, ay - barh) if KH != KW else 0}[cb]")
            cur, n = "cb", n + 1
        if bg.get("label"):
            gambar_label(bg["label"], tmp / f"lab{k}.png", int(bg.get("label_ukuran", 58)))
            args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.3f}", "-i", str(tmp / f"lab{k}.png")]
            fc.append(f"[{cur}][{n}:v]overlay=14:{ay + 8}[cl]")
            cur, n = "cl", n + 1
        if bg.get("popup") and potong is None:
            nn = [n]

            def tambah_(*xs):
                args.extend(map(str, xs))
                nn[0] += 1
                return nn[0] - 1
            cur = overlay_popup(bg["popup"], tmp, tambah_, cur, fc, KW, KH, awal=f"pb{k}_")
            n = nn[0]
        if audio and info["audio"]:
            fc.append(f"[0:a]aresample=44100,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS,"
                      f"volume={float(bg.get('volume', 1.0))},apad=whole_dur={d:.3f}[aout]")
        else:
            args += ["-f", "lavfi", "-t", f"{d:.3f}", "-i", "anullsrc=r=44100:cl=stereo"]
            fc.append(f"[{n}:a]anull[aout]")
            n += 1
    if wm:
        args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.3f}", "-i", str(wm)]
        op = float(rencana.get("watermark_opacity", 0.9))
        fc.append(f"[{n}:v]format=rgba,scale={ww}:{wh},colorchannelmixer=aa={op:.2f}[wmb];"
                  f"[{cur}][wmb]overlay=(W-w)/2:{even(rencana.get('watermark_y', wy))}[cw]")
        cur = "cw"
    fc.append(f"[{cur}]trim=duration={d:.3f},format=yuv420p[vout]")
    run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
         "-t", f"{d:.3f}", "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "17",
         "-c:a", "aac", "-b:a", "192k", "-ar", "44100", out])
    return out


def durasi_banding(rencana):
    if rencana["format"] == "banding":
        a, b = rencana["sumber"][0]["potong"]
        return b - a
    return sum(float(bg.get("durasi", 2.5)) if bg.get("kartu") else bg["potong"][1] - bg["potong"][0]
               for bg in rencana["bagian"])


def render_banding(rencana, tmp, out):
    """Klip utama format banding/berurutan (tanpa endcard), audio -14 LUFS."""
    KW, KH = kanvas(rencana)
    if rencana["format"] == "banding":
        return _render_bersamaan(rencana, tmp, 0.0, durasi_banding(rencana), out)
    bag = [_render_bagian(rencana, bg, tmp, k, tmp / f"bag{k}.mp4") for k, bg in enumerate(rencana["bagian"])]
    gab = tmp / "bagian_gabung.mp4"
    sambung(bag, gab, tmp, (KW, KH))
    run(["ffmpeg", "-v", "error", "-y", "-i", gab, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", out])
    return out


def ekor_banding(rencana, tmp, d, out):
    """Lanjutan video (tanpa suara) setelah titik potong, untuk ending get out format banding."""
    if rencana["format"] == "banding":
        return _render_bersamaan(rencana, tmp, durasi_banding(rencana), d, out, audio=False)
    akhir = [bg for bg in rencana["bagian"] if not bg.get("kartu")][-1]
    b = akhir["potong"][1]
    return _render_bagian(rencana, akhir, tmp, 99, out, potong=[b, b + d], audio=False)


def amplop(path, t0, dur, sr=8000):
    """Amplop onset (perubahan energi positif, 100 Hz) untuk sinkron dua rekaman lewat suara game."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0, t0):.3f}", "-t", f"{dur:.3f}", "-i", str(path),
                          "-ac", "1", "-ar", str(sr), "-af", "highpass=f=200", "-f", "f32le", "-"],
                         capture_output=True).stdout
    a = np.frombuffer(raw, dtype=np.float32)
    hop = sr // 100
    n = len(a) // hop
    e = np.log1p(1000 * np.sqrt((a[:n * hop].reshape(n, hop) ** 2).mean(1)))
    on = np.maximum(0, np.diff(e, prepend=e[:1]))
    return (on - on.mean()) / (on.std() + 1e-9)


def sinkron(rencana_path, cari=30.0):
    """Cari detik mulai rekaman B (streamer lain) yang paling cocok dengan potongan A lewat korelasi suara game.
    Perkiraan awal: sumber[1]["mulai"] (dari AI pencari momen / Prompt B). Hasil ditulis ke rencana."""
    r = json.loads(Path(rencana_path).read_text(encoding="utf-8"))
    A, B = r["sumber"][:2]
    a0, a1 = A["potong"]
    dur = min(a1 - a0, 40.0)
    kira = float(B.get("mulai", a0))
    ea = amplop(A["input"], a0, dur)
    mulai_cari = max(0.0, kira - cari)
    eb = amplop(B["input"], mulai_cari, dur + 2 * cari)
    if len(eb) <= len(ea):
        raise SystemExit("Rekaman B terlalu pendek untuk dicari.")
    c = np.correlate(eb, ea, mode="valid") / len(ea)
    i = int(np.argmax(c))
    z = (c[i] - c.mean()) / (c.std() + 1e-9)
    hasil = round(mulai_cari + i / 100.0, 2)
    B["mulai"], B["geser"] = hasil, 0
    r["_sinkron"] = {"skor_z": round(float(z), 1), "keyakinan": "tinggi" if z > 6 else "sedang" if z > 4 else "rendah"}
    Path(rencana_path).write_text(json.dumps(r, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Sinkron: B mulai di {hasil:.2f} dtk (z={z:.1f}, keyakinan {r['_sinkron']['keyakinan']}).")
    if z <= 4:
        print("  Keyakinan rendah: cek pratinjau, atur manual dengan \"geser\" (detik, + = B lebih lambat).")


# ---------------------------------------------------------------- pencari momen sus
KATA_SUS = ["bikini", "pipa", "basah", "masuk", "keras", "belakang", "pegang", "goyang", "joget", "seksi", "sexy",
            "cewek", "cewe", "tante", "mbak", "kamar", "ranjang", "kasur", "mandi", "baju", "celana", "dada", "paha",
            "pantat", "bokong", "cium", "peluk", "pacar", "mommy", "daddy", "club", "klub", "strip", "nari",
            "astaghfirullah", "astagfirullah", "istighfar", "sensor", "tutup mata", "jangan liat", "anak kecil",
            "dosa", "puasa", "halal", "nakal", "genit", "godain", "naik", "buka", "lubang", "panas"]
KATA_REAKSI = ["anjir", "duh", "wah", "anjing", "astaga", "gila", "woi", "loh", "waduh", "aduh", "ih", "hah", "buset", "bjir"]


def cari_sus(video, out_json=None):
    """Pindai ucapan (Whisper, waktu per kata) untuk momen sus/sindiran 18+. Hasil: kandidat rentang potong."""
    from faster_whisper import WhisperModel
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True).stdout
    a = np.frombuffer(raw, dtype=np.float32).copy()
    m = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = m.transcribe(a, language="id", word_timestamps=True, vad_filter=True,
                           vad_parameters=dict(threshold=0.25, min_silence_duration_ms=300),
                           condition_on_previous_text=False)
    kata = [(w.start, w.end, w.word.strip().lower().strip(".,!?")) for sg in segs for w in sg.words]
    teks = " ".join(k for _, _, k in kata)
    hit = []
    for i, (t, _, k) in enumerate(kata):
        dua = k + " " + (kata[i + 1][2] if i + 1 < len(kata) else "")
        sus = [w for w in KATA_SUS if (w in dua if " " in w else k.startswith(w))]
        if sus:
            dekat = [kk for tt, _, kk in kata if t - 3 <= tt <= t + 6 and kk in KATA_REAKSI]
            hit.append({"detik": round(t, 1), "kata": sus, "reaksi": sorted(set(dekat)),
                        "kutipan": " ".join(kk for tt, _, kk in kata if t - 4 <= tt <= t + 6)})
    # gabung yang berdekatan jadi kandidat
    kand = []
    for h in hit:
        if kand and h["detik"] - kand[-1]["akhir"] < 12:
            kand[-1]["akhir"] = h["detik"]
            kand[-1]["kata"] = sorted(set(kand[-1]["kata"] + h["kata"]))
            kand[-1]["reaksi"] = sorted(set(kand[-1]["reaksi"] + h["reaksi"]))
            kand[-1]["kutipan"] += " / " + h["kutipan"]
        else:
            kand.append({"mulai": h["detik"], "akhir": h["detik"], **{k: h[k] for k in ("kata", "reaksi", "kutipan")}})
    for c in kand:
        c["skor"] = len(c["kata"]) * 2 + len(c["reaksi"])
        c["usul_potong"] = [round(max(0, c["mulai"] - 15), 1), round(c["akhir"] + 12, 1)]
        c["eksplisit"] = [k for k in KATA_EKSPLISIT if k in c["kutipan"]]
    kand.sort(key=lambda c: -c["skor"])
    out_json = Path(out_json or Path(video).with_suffix("").as_posix() + "_sus.json")
    out_json.write_text(json.dumps({"video": str(video), "kandidat": kand, "transkrip": teks}, indent=1,
                                   ensure_ascii=False), encoding="utf-8")
    print(f"{len(kand)} kandidat sus -> {out_json}")
    for c in kand[:8]:
        print(f"  {c['mulai']:7.1f}-{c['akhir']:7.1f} skor {c['skor']:2d} {c['kata']} reaksi {c['reaksi']}"
              + (f"  EKSPLISIT {c['eksplisit']}" if c["eksplisit"] else ""))
        print(f"      \"{c['kutipan'][:160]}\"")
    return kand


def main():
    ap = argparse.ArgumentParser(prog="klip-windah")
    sp = ap.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("analisis")
    a.add_argument("video")
    a.add_argument("--keluar", default=None)
    a.add_argument("--transkrip", action="store_true")
    p = sp.add_parser("pratinjau")
    p.add_argument("rencana")
    r = sp.add_parser("render")
    r.add_argument("rencana")
    sp.add_parser("sfx")
    hk_ = sp.add_parser("hook")
    hk_.add_argument("rencana")
    c = sp.add_parser("camhd")
    c.add_argument("rencana")
    t = sp.add_parser("thumbnail")
    t.add_argument("rencana")
    sk = sp.add_parser("sinkron")
    sk.add_argument("rencana")
    sk.add_argument("--cari", type=float, default=30.0)
    cs = sp.add_parser("cari-sus")
    cs.add_argument("video")
    args = ap.parse_args()
    if args.cmd == "sinkron":
        return sinkron(args.rencana, args.cari)
    if args.cmd == "cari-sus":
        return cari_sus(args.video)
    if args.cmd == "hook":  # pratinjau kartu hook saja (gambar di detik 1,3)
        r = json.loads(Path(args.rencana).read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as td:
            v = buat_hook(r, Path(td))
            out = Path(args.rencana).with_name(Path(args.rencana).stem + "_hook.jpg")
            run(["ffmpeg", "-v", "error", "-y", "-ss", "1.3", "-i", v, "-frames:v", "1", "-q:v", "3", out], quiet=True)
        print("Pratinjau hook:", out)
        return
    if args.cmd == "camhd":
        r = json.loads(Path(args.rencana).read_text(encoding="utf-8"))
        return buat_cam_hd(r, Path(args.rencana).with_name(Path(args.rencana).stem + "_camhd.mp4"))
    if args.cmd == "thumbnail":
        return thumbnail(args.rencana)
    if args.cmd == "analisis":
        out = args.keluar or str(Path(args.video).with_suffix("")) + "_analisis"
        analisis(args.video, out, args.transkrip)
    elif args.cmd == "pratinjau":
        render(args.rencana, pratinjau=True)
    elif args.cmd == "render":
        render(args.rencana)
    elif args.cmd == "sfx":
        buat_sfx()


if __name__ == "__main__":
    main()
