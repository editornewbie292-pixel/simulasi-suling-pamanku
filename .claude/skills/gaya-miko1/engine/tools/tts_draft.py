# Draft voice for testing only (free, offline): reads script.json and writes audio/vo_draft.wav.
# Uses Kokoro with Indonesian phonemes; the accent is foreign, so the final reel should use the user's
# ElevenLabs (or recorded) Indonesian voiceover.   tts_draft.py [voice=ef_dora] [speed=1.0]
import json, sys, os, shutil, tempfile, numpy as np, soundfile as sf
ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
KIT = os.environ.get('KIT') or os.path.realpath(os.path.join(ROOT, "..", "..", "..", "kit"))
kp = os.path.join(ROOT, 'kitpath.txt')
if not os.path.isdir(os.path.join(KIT, 'models')) and os.path.exists(kp): KIT = open(kp).read().strip()
from kokoro_onnx import Kokoro, EspeakConfig
import espeakng_loader
data = espeakng_loader.get_data_path()
if len(data) > 100:
    short = os.path.join(tempfile.gettempdir(), "kokoro-espeak-ng-data")
    if not os.path.exists(os.path.join(short, "phontab")):
        shutil.rmtree(short, ignore_errors=True); shutil.copytree(data, short)
    data = short
voice = sys.argv[1] if len(sys.argv) > 1 else 'ef_dora'
speed = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
k = Kokoro(os.path.join(KIT, 'models/kokoro-v1.0.onnx'), os.path.join(KIT, 'models/voices-v1.0.bin'),
           espeak_config=EspeakConfig(lib_path=espeakng_loader.get_library_path(), data_path=data))
out = []
for i, line in enumerate(json.load(open('script.json'))):
    s, sr = k.create(line, voice=voice, speed=speed, lang='id')
    idx = np.where(np.abs(s) > .01)[0]; s = s[max(0, idx[0] - 400): idx[-1] + 1200]
    out += [s, np.zeros(int(.28 * sr), dtype=s.dtype)]
os.makedirs('audio', exist_ok=True)
sf.write('audio/vo_draft.wav', np.concatenate(out), sr)
print('audio/vo_draft.wav', round(sum(len(x) for x in out) / sr, 2), 's')
