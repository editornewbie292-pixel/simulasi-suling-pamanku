"""Upscale x4 (Real-ESRGAN General x4v3, ONNX) untuk panel cam kecil. Ubin 128x128 bertumpuk."""
import time
from pathlib import Path
import numpy as np

MODEL = Path.home() / ".cache/klip-windah/realesr-general-x4v3.onnx"
MODEL_URL = "https://huggingface.co/tamnvcc/Real-ESRGAN-General-x4v3_float/resolve/main/onnx/model.onnx"
T, PAD = 128, 12
_sesi = None


def sesi():
    global _sesi
    if _sesi is None:
        import onnxruntime as ort
        if not MODEL.exists():
            import urllib.request
            MODEL.parent.mkdir(parents=True, exist_ok=True)
            print("  mengunduh model upscale (4,8 MB) ...")
            urllib.request.urlretrieve(MODEL_URL, MODEL)
        so = ort.SessionOptions()
        so.intra_op_num_threads = 0
        _sesi = ort.InferenceSession(str(MODEL), so, providers=["CPUExecutionProvider"])
    return _sesi


def upscale(img):
    """img: uint8 HxWx3 RGB -> uint8 (4H)x(4W)x3."""
    s = sesi()
    h, w, _ = img.shape
    x = img.astype(np.float32) / 255.0
    out = np.zeros((h * 4, w * 4, 3), np.float32)
    step = T - 2 * PAD
    ys = list(range(0, max(1, h - T) + 1, step)) or [0]
    xs = list(range(0, max(1, w - T) + 1, step)) or [0]
    if ys[-1] + T < h:
        ys.append(h - T)
    if xs[-1] + T < w:
        xs.append(w - T)
    tiles, pos = [], []
    for yy in ys:
        for xx in xs:
            t = np.zeros((T, T, 3), np.float32)
            p = x[yy:yy + T, xx:xx + T]
            t[:p.shape[0], :p.shape[1]] = p
            tiles.append(t.transpose(2, 0, 1))
            pos.append((yy, xx))
    batch = np.stack(tiles)
    hasil = np.concatenate([s.run(None, {"image": batch[i:i + 1]})[0] for i in range(len(batch))])
    for (yy, xx), r in zip(pos, hasil):
        r = r.transpose(1, 2, 0)
        y0 = 0 if yy == 0 else PAD
        x0 = 0 if xx == 0 else PAD
        out[(yy + y0) * 4:(yy + T) * 4, (xx + x0) * 4:(xx + T) * 4] = r[y0 * 4:, x0 * 4:][: (h - yy - y0) * 4, : (w - xx - x0) * 4]
    return (np.clip(out, 0, 1) * 255).round().astype(np.uint8)


if __name__ == "__main__":
    import sys
    from PIL import Image
    im = np.array(Image.open(sys.argv[1]).convert("RGB"))
    t = time.time()
    up = upscale(im)
    print(f"{im.shape} -> {up.shape} dalam {time.time() - t:.2f} dtk")
    Image.fromarray(up).save(sys.argv[2])
