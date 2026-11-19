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
               "format=duration:stream=codec_type,width,height,r_frame_rate",
               "-of", "json", path], quiet=True)
    j = json.loads(out)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    num, den = v["r_frame_rate"].split("/")
    return {"w": int(v["width"]), "h": int(v["height"]),
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
def gambar_judul(teks, sub, path, lebar=W - 80):
    """Kotak judul gaya referensi: gelap transparan, tepi gradasi ungu->pink, huruf Anton kapital."""
    teks = teks.upper().strip()
    pad, border, rad = 30, 7, 26
    size = 74
    while True:
        f = font(FONT_JUDUL, size, bold=False)
        maxw = lebar - 2 * pad - 2 * border
        kata, baris, cur = teks.split(), [], ""
        for k in kata:
            coba = (cur + " " + k).strip()
            if f.getlength(coba) <= maxw:
                cur = coba
            else:
                baris.append(cur)
                cur = k
        baris.append(cur)
        if len(baris) <= 3 or size <= 50:
            break
        size -= 4
    lh = int(size * 1.08)
    fs = font(FONT_TEKS, 22)
    sub_h = 30 if sub else 0
    tinggi = 2 * pad + lh * len(baris) + sub_h + 2 * border
    lebar_isi = max(f.getlength(b) for b in baris)
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
        d.text((border + pad, y), b, font=f, fill="white")
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


def sfx_path(nama):
    for ext in ("wav", "mp3", "m4a", "ogg"):
        p = SFX_DIR / f"{nama}.{ext}"
        if p.exists():
            return p  # SFX milik pengguna menang
    p = SFX_BAWAAN / f"{nama}.wav"
    if not p.exists():
        buat_sfx()
    return p


# ---------------------------------------------------------------- render
def cover(label_in, box, tw, th, label_out):
    x, y, w, h = map(int, box)
    return (f"[{label_in}]crop={even(w)}:{even(h)}:{x}:{y},"
            f"scale={tw}:{th}:force_original_aspect_ratio=increase,crop={tw}:{th}[{label_out}]")


def antara(segs):
    return "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in segs) or "0"


def bangun(rencana, tmp, pratinjau=None):
    src = rencana["input"]
    info = probe(src)
    t0, t1 = rencana.get("potong") or [0, info["durasi"]]
    dur = round(t1 - t0, 3)
    fmt = rencana.get("format", "tiktok")
    stream = rencana.get("stream_box") or [0, 0, info["w"], info["h"]]
    cam = rencana.get("cam_box")
    efek = True  # efek visual juga tampil di pratinjau; audio hanya saat render
    geser = f"+{pratinjau:.3f}/TB" if pratinjau is not None else ""

    inputs, f = [], []
    if pratinjau is not None:
        inputs += ["-ss", f"{t0 + pratinjau:.3f}", "-t", "0.2", "-i", src]
    else:
        inputs += ["-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", src]
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
    if butuh > 1:
        f.append(f"[0:v]fps={FPS},setpts=PTS-STARTPTS{geser},split={butuh}" + "".join(f"[s{i}]" for i in range(butuh)))
    else:
        f.append(f"[0:v]fps={FPS},setpts=PTS-STARTPTS{geser}[s0]")

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
        f.append(cover("s1", cam, W, ch, "cam"))
        atas = rencana.get("posisi_cam", "bawah") == "atas"
        f.append("[cam][game]vstack[base0]" if atas else "[game][cam]vstack[base0]")
        seam = ch if atas else gh
        konten_y, konten_h = 0, H
        nxt = 2
    else:  # kotak
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

    if penuh and cam:
        th = H if fmt == "tiktok" else konten_h
        ty = 0 if fmt == "tiktok" else konten_y
        f.append(cover(f"s{nxt}", cam, W, th, "campenuh"))
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
            sfx += [("glitch", max(0, g - 0.12), 0.7) for g in glitch]
        # impact: getar + kilat putih
        impact = rencana.get("impact", [])
        if impact:
            gx = "+".join(f"if(between(t,{a:.3f},{a + 0.4:.3f}),22*sin((t-{a:.3f})*95)*(1-(t-{a:.3f})/0.4),0)" for a in impact)
            gy = "+".join(f"if(between(t,{a:.3f},{a + 0.4:.3f}),16*cos((t-{a:.3f})*80)*(1-(t-{a:.3f})/0.4),0)" for a in impact)
            f.append(f"[{cur}]scale={even(W * 1.05)}:{even(H * 1.05)},"
                     f"crop={W}:{H}:x='(iw-ow)/2+{gx}':y='(ih-oh)/2+{gy}',"
                     f"eq=brightness=0.28:enable='{antara([(a, a + 0.07) for a in impact])}'[b3]")
            cur = "b3"
            sfx += [("boom", a, 0.9) for a in impact]
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

    # judul (hook)
    if rencana.get("judul"):
        jd = float(rencana.get("judul_durasi", 2.5))
        jw, jh = gambar_judul(rencana["judul"], rencana.get("judul_sub"), tmp / "judul.png")
        if fmt == "tiktok":
            jy = even(seam - jh / 2)
        else:
            jy = even(max(40, konten_y - jh - 40))
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


def render(rencana_path, pratinjau=False):
    rencana = json.loads(Path(rencana_path).read_text(encoding="utf-8"))
    out = Path(rencana.get("output") or Path(rencana_path).with_suffix(".mp4"))
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        if pratinjau:
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
        inputs, f, amap, dur = bangun(rencana, tmp)
        utama = tmp / "utama.mp4" if rencana.get("endcard") else out
        run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(f),
             "-map", "[vout]", *amap, "-r", FPS, "-c:v", "libx264", "-preset", "medium", "-crf", "19",
             "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", utama])
        if rencana.get("endcard"):
            ec = rencana["endcard"]
            ei = probe(ec)
            extra = []
            if ei["audio"]:
                a1 = "[1:a]aresample=44100,aformat=channel_layouts=stereo[ea]"
            else:
                extra = ["-f", "lavfi", "-t", f"{ei['durasi']:.3f}", "-i", "anullsrc=r=44100:cl=stereo"]
                a1 = "[2:a]anull[ea]"
            fc = (f"[0:v]setsar=1[v0];[1:v]scale={W}:{H}:force_original_aspect_ratio=decrease,"
                  f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,fps={FPS},setsar=1,format=yuv420p[v1];"
                  f"[0:a]aformat=channel_layouts=stereo[a0];{a1};"
                  f"[v0][a0][v1][ea]concat=n=2:v=1:a=1[v][a]")
            run(["ffmpeg", "-v", "error", "-y", "-i", utama, "-i", ec, *extra, "-filter_complex", fc,
                 "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                 "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])
    print(f"Selesai: {out} ({dur:.1f} detik + endcard)" if rencana.get("endcard") else f"Selesai: {out} ({dur:.1f} detik)")


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
    args = ap.parse_args()
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
