# Ambience, music and SFX for a /gaya-miko1 reel, all synthesised and placed by the voice's word times.
# Cue helpers: T('kata') / L(i) work like in shots.js (audio/words.json comes from align_id.py).
import json, re, numpy as np, soundfile as sf
from scipy import signal
SR = 44100
WORDS = json.load(open('audio/words.json'))
vo, vsr = sf.read('audio/vo.wav')
if vo.ndim > 1: vo = vo.mean(1)
VO_DUR = len(vo) / vsr
DUR = VO_DUR + .7
N = int(DUR * SR)
rng = np.random.default_rng(3)
norm = lambda s: re.sub(r'[^0-9a-zà-ÿ]', '', s.lower())
def T(w, n=1):
    k = 0
    for x in WORDS:
        if norm(x['w']) == norm(w):
            k += 1
            if k == n: return x['s']
    raise SystemExit(f'T(): word not found: {w}')
def L(i, pre=.12): return max(0, next(x['s'] for x in WORDS if x['line'] == i) - pre)
def Tt(n): return np.arange(n) / SR
def place(buf, x, at, g=1.0):
    i = int(at * SR); j = min(len(buf), i + len(x))
    if 0 <= i < len(buf): buf[i:j] += x[:j - i] * g
def bp(x, lo, hi): b, a = signal.butter(2, [lo / (SR / 2), min(hi / (SR / 2), .99)], 'band'); return signal.lfilter(b, a, x)
def lp(x, f): b, a = signal.butter(2, f / (SR / 2), 'low'); return signal.lfilter(b, a, x)
def hp(x, f): b, a = signal.butter(2, f / (SR / 2), 'high'); return signal.lfilter(b, a, x)

# ---------- sound kit ----------
def chime(f, dur=1.2): t = Tt(int(dur * SR)); return (np.sin(2 * np.pi * f * t) + .4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 6)) * np.exp(-t * 3) * np.minimum(1, t / .003) * .5
def gong(f=98, dur=3.5): t = Tt(int(dur * SR)); return (np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 2.02 * t) * np.exp(-t) + .3 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t * 2)) * np.exp(-t * .9) * np.minimum(1, t / .01) * .6
def saron(f, dur=.9): t = Tt(int(dur * SR)); return (np.sin(2 * np.pi * f * t) + .6 * np.sin(2 * np.pi * f * 2.4 * t) * np.exp(-t * 8) + .25 * np.sin(2 * np.pi * f * 3.9 * t) * np.exp(-t * 14)) * np.exp(-t * 4) * np.minimum(1, t / .002) * .45
def crickets(dur):
    n = int(dur * SR); t = Tt(n); out = np.zeros(n)
    for f, rate, ph in [(4300, 18, 0), (4700, 22, 1.3), (3900, 15, 2.1)]:
        gate = (np.sin(2 * np.pi * rate * t + ph) > .6) * (np.sin(2 * np.pi * .45 * t + ph * 3) > -.2)
        out += np.sin(2 * np.pi * f * t) * lp(gate.astype(float), 300) * .08
    return out
def wind(dur): n = int(dur * SR); t = Tt(n); return lp(rng.standard_normal(n), 500) * (.6 + .4 * np.sin(2 * np.pi * t / 7)) * .25
def click(): n = int(.05 * SR); t = Tt(n); return hp(rng.standard_normal(n), 1500) * np.exp(-t * 120) * .8 + np.sin(2 * np.pi * 120 * t) * np.exp(-t * 60) * .6
def shimmer(dur=1.5):
    out = np.zeros(int(dur * SR))
    for i, f in enumerate([1568, 1760, 2093, 2349, 2637, 3136]): place(out, chime(f, .9) * .4, i * .09)
    return out
def pad(freqs, dur, g=.2):
    n = int(dur * SR); t = Tt(n); x = np.zeros(n)
    for f in freqs:
        for d in (-.003, 0, .004): ph = np.cumsum(f * (1 + d) * (1 + .002 * np.sin(2 * np.pi * 4.5 * t))) / SR; x += np.sin(2 * np.pi * ph) + .3 * np.sin(4 * np.pi * ph)
    x = lp(x / (len(freqs) * 3), 1800); return x * np.minimum(1, t / 1.2) * np.minimum(1, (dur - t) / 1.2) * g

# ---------- cues for the example reel ----------
sfx = np.zeros(N); music = np.zeros(N)
place(sfx, crickets(DUR), 0, .9); place(sfx, wind(DUR), 0, .5)
place(sfx, click(), T('padam'), .9); place(sfx, gong(73, 3), T('padam') + .05, .35)
place(sfx, shimmer(2.0), T('berkedip') - .2, .45)
place(sfx, shimmer(1.5), T('oksigen'), .35)
for k in range(8): place(sfx, chime([2093, 2637][k % 2], .5) * .4, L(6) + .2 + k * .52, .5)
place(sfx, shimmer(2.0), T('menunggu'), .4)
# gentle slendro-ish underscore: saron notes over a soft pad, darker before the fireflies, brighter after
SL = [293.7, 329.6, 392.0, 440.0, 523.3]
place(music, pad([146.8, 220.0], L(2) + .5, .22), 0)
place(music, pad([196.0, 293.7, 392.0], DUR - L(2), .25), L(2))
t, i = L(2), 0
pat = [0, 2, 3, 2, 4, 3, 2, 1]
while t < DUR - 1:
    place(music, saron(SL[pat[i % 8]], .9), t, .55 if i % 4 else .75); t += .42; i += 1
place(music, gong(98, 3.5), L(2), .5); place(music, gong(98, 3.5), DUR - 3.2, .5)
music = lp(music, 7000)

# ---------- mix: duck under the voice ----------
v = signal.resample_poly(vo, SR, vsr); v = hp(v, 80); v = v / (np.max(np.abs(v)) + 1e-9) * .9
VO = np.zeros(N); VO[:min(N, len(v))] = v[:N]
duck = 1 - .5 * np.clip(lp(np.abs(VO), 6) / .05, 0, 1)
mix = VO + music * .32 * duck + sfx * .6
fl = int(.7 * SR); mix[-fl:] *= np.linspace(1, 0, fl)
mix = mix / (np.max(np.abs(mix)) + 1e-9) * .89
sf.write('audio/mix.wav', np.stack([mix, mix], 1), SR)
print('mix', round(DUR, 2), 's')
