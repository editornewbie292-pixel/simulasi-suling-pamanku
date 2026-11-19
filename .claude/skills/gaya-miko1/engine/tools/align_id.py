# Align an Indonesian (or any language) voiceover to script.json word by word with faster-whisper.
# Run from a reel folder:  align_id.py audio/vo.wav
# Writes audio/words.json, web/words.js (WORDS + NAMES for caption highlighting).
# The Whisper model is cached in kit/models/hf (needs huggingface.co the first time).
import json, re, difflib, os, sys, numpy as np, soundfile as sf
ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
KIT = os.environ.get('KIT') or os.path.realpath(os.path.join(ROOT, '..', '..', '..', 'kit'))
if not os.path.isdir(os.path.join(KIT, 'node_modules', 'three')) and not os.environ.get('KIT'): KIT = os.path.expanduser('~/.cache/gaya-miko1/kit')
os.environ.setdefault('HF_HOME', os.path.join(KIT, 'models', 'hf'))
from faster_whisper import WhisperModel

src = sys.argv[1] if len(sys.argv) > 1 else 'audio/vo.wav'
LANG = os.environ.get('LANG_VO', 'id')
MODEL = os.environ.get('WHISPER_MODEL', 'small')
a, sr = sf.read(src, dtype='float32')
if a.ndim > 1: a = a.mean(1)
if sr != 16000:
    n = int(len(a) * 16000 / sr); a = np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a).astype(np.float32); sr = 16000
model = WhisperModel(MODEL, device='cpu', compute_type='int8')
lines = json.load(open('script.json'))
cap = json.load(open('captions.json')) if os.path.exists('captions.json') else {}
SWAP, NAMES = cap.get('swap', {}), cap.get('names', [])
segs, _ = model.transcribe(a, language=LANG, word_timestamps=True, initial_prompt=' '.join(lines)[:600], vad_filter=False)
asr = [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]

norm = lambda w: re.sub(r"[^0-9a-zà-ÿ]", "", w.lower())
script = []
for li, L in enumerate(lines):
    for w in L.split(): script.append((w, li))
S = [norm(w) for w, _ in script]
# whisper may split or join words differently: match on characters, then map back
def charmap(words):
    s, idx = '', []
    for i, w in enumerate(words): s += w; idx += [i] * len(w)
    return s, idx
sS, iS = charmap(S); sA, iA = charmap([norm(w[0]) for w in asr])
sm = difflib.SequenceMatcher(a=sS, b=sA, autojunk=False)
start, end = [None] * len(script), [None] * len(script)
for blk in sm.get_matching_blocks():
    for k in range(blk.size):
        si, ai = iS[blk.a + k], iA[blk.b + k]
        if start[si] is None: start[si] = asr[ai][1]
        end[si] = asr[ai][2]
matched = sum(1 for x in start if x is not None)
dur = len(a) / sr
for i in range(len(script)):
    if start[i] is None:
        lo = next((j for j in range(i - 1, -1, -1) if start[j] is not None), None)
        hi = next((j for j in range(i + 1, len(script)) if start[j] is not None), None)
        if lo is not None and hi is not None: start[i] = start[lo] + (start[hi] - start[lo]) * (i - lo) / (hi - lo)
        elif lo is not None: start[i] = start[lo] + .3
        else: start[i] = 0
for i in range(1, len(script)):  # keep monotonic
    start[i] = max(start[i], start[i - 1] + .02)
words = []
for i, (w, li) in enumerate(script):
    nxt = start[i + 1] if i + 1 < len(script) else dur
    e = end[i] if end[i] is not None and end[i] > start[i] else nxt
    shown = w
    for k, v in SWAP.items():
        if norm(w) == norm(k): shown = v
    words.append({'w': shown, 's': round(start[i], 3), 'e': round(min(max(e, start[i] + .12), nxt + .05, start[i] + 1.4), 3), 'line': li})
os.makedirs('audio', exist_ok=True)
json.dump(words, open('audio/words.json', 'w'), indent=0)
open('web/words.js', 'w').write('window.WORDS=' + json.dumps(words) + ';window.NAMES=' + json.dumps(NAMES) + ';window.VO_DUR=' + str(round(dur, 3)) + ';')
print(f'matched {matched} of {len(script)} words, voice {dur:.2f}s')
for li in range(len(lines)):
    ws = [w for w in words if w['line'] == li]
    if ws: print(f"{ws[0]['s']:6.2f}-{ws[-1]['e']:6.2f}  " + ' '.join(f"{w['w']}@{w['s']:.2f}" for w in ws))
