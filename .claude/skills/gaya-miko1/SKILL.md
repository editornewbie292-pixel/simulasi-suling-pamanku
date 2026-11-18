---
name: gaya-miko1
description: Makes a vertical (9:16, 1080x1920) Indonesian story-explainer reel in the "gaya-miko1" look - flat cartoon people with wide pillow heads, thick ink and hair sheen, living in low-poly 3D kampung worlds with mood lighting (day, sunset, night, glowing green), smooth dolly cameras and 1-2 word captions with names in yellow - narrated by the user's Indonesian voiceover. Use when the user runs /gaya-miko1 or asks for a video in gaya miko / this 3D-kartun kampung style.
---

# /gaya-miko1

A reel is a short Indonesian story that explains something (why, how, what if), told through everyday
kampung characters. Everything is generated in code: three.js builds the 3D world, the characters are
drawn in 2D and stand in it as camera-facing cards that take the scene's light and cast real shadows.

`engine/template` is a finished example: "Kunang-kunang" (8 shots, about 25 s).

## Setup (once per machine)
```bash
SKILL_DIR="<base directory of this skill>"; ENGINE="$SKILL_DIR/engine"
KIT=$(python -c 'import os,sys;print(os.path.realpath(os.path.join(sys.argv[1],"..","..","kit")))' "$SKILL_DIR")
[ -x "$KIT/.venv/bin/python" ] && [ -d "$KIT/models" ] || bash "$KIT/setup.sh" --voice
"$KIT/.venv/bin/python" -c "import faster_whisper" 2>/dev/null || "$KIT/.venv/bin/python" -m pip install -q faster-whisper
PY="$KIT/.venv/bin/python"; export NODE_PATH="$KIT/node_modules"
```
- Word timing uses faster-whisper (`small`, Indonesian). The first run downloads the model from
  huggingface.co into `$KIT/models/hf`. In a cloud session, the network must allow huggingface.co,
  cas-server.xethub.hf.co, cas-bridge.xethub.hf.co and us.aws.cdn.hf.co.
- Rendering uses WebGL through SwiftShader. In this container set `CHROME=/opt/pw-browsers/chromium`.
- Needs ffmpeg, Node and Python 3.9+.

## Voice
- **Final reels use the user's Indonesian voiceover** (ElevenLabs or a recording). Ask for the file.
- For timing drafts before the voiceover exists: `make.sh <reel> draft` (free Kokoro voice reading
  Indonesian with a foreign accent). Say clearly that it's a placeholder.
- Shots are timed with `T('kata')` / `L(i)` from the aligned words, so when the real voiceover arrives,
  `make.sh <reel> voice.mp3` re-times every shot by itself. The script text must match the voiceover.

## Steps
1. **Script.** Indonesian, 110-200 words (40-80 s), one idea per sentence, spoken style. Structure:
   a character-driven hook ("Mbah X tidak pernah salah..."), the everyday situation, a turn, the
   explanation shown through the story, a warm payoff. Names of people get highlighted in yellow.
   Show the script to the user before animating.
2. **Facts.** Check every factual claim; hedge theories ("katanya", "para ahli menduga").
3. **Folder.** `cp -r "$ENGINE/template" <reel>`, empty `audio/`, write `script.json` (one sentence per
   entry) and `captions.json` (`{"swap": {"dua puluh": "20"}, "names": ["Bima", "Kakek"]}`).
4. **Voice + timing.** Put the voiceover in place and align:
   `ffmpeg -i vo.mp3 -ac 1 -ar 44100 audio/vo.wav && "$PY" "$ENGINE/tools/align_id.py" audio/vo.wav`.
   It prints each line's word times; the matched count should be close to the total.
5. **Shots.** Rewrite `web/shots.js`: one `shot(start, end, build, opt)` per setup, a new setup every
   2-4 s (about one per sentence, close-ups between wides). Keep every `shot(` at the start of a line.
6. **Stills.** From the reel folder: `node "$ENGINE/tools/render.js" stills 1.5,6.2,12.0` writes
   `stills/`. Check the busiest moments, faces clear of the caption band, before the full render.
7. **Sound.** Edit the cues in `audio.py` (`T('kata')`, `L(i)`): ambience, gamelan-ish underscore, SFX.
8. **Build.** `bash "$ENGINE/make.sh" <reel> [voice.mp3|draft]`. `FPS=60` for extra-smooth motion
   (about 2x render time), `WORKERS=8` on a bigger machine, `AUDIO_ONLY=1` to remix sound only.
   An 80 s reel at 30 fps takes roughly 10-20 minutes with 4 workers.
9. **Hand over** `<reel>/<name>.mp4`.

## Building shots (web/shots.js)
```js
import { THREE, shot, makeScene, camera, camMove, focusSun, kf, lerp, clamp, smooth, L, T, M, mat, glowMat, start } from './core.js';
import { Person, LOOKS, SKIN, blinkAt } from './chars.js';
import * as w from './world.js';

shot(L(0), L(1), () => {
  const S = makeScene('sunset'), cam = camera(36), { scene } = S;        // moods: day morning sunset storm night glow indoor
  w.ground(scene, { kind: 'tile' });                                      // tile grass dirt plank sand
  w.houseRow(scene, { side: -1 }); w.houseRow(scene, { side: 1 });        // a kontrakan alley along z
  const mbah = new Person(scene, LOOKS.nenek, { x: 0, z: 0, h: 1.5 });
  return { scene, cam, update(lt, t) {                                    // lt = time in shot, t = voice time
    mbah.set({ eyes: 'open', mouth: 'smile', talk: t < T.end('hujan') ? 1 : 0, t, blink: blinkAt(t) });
    const f = mbah.face3();
    camMove(cam, lt, [[0, [0, 1.3, 4], f], [3, [.3, 1.25, 2.6], f]]);     // smooth dolly + gentle float
  } };
}, { tr: 'cut' });                                                        // 'cut' (default) or 'fade'
start();                                                                  // last line of shots.js
```
- **Timing:** `L(i)` = start of script line i (minus 0.12 s), `T('kata', n)` = the n-th "kata", `T.end(...)`.
  The last shot's end can be any big number; the reel ends 0.7 s after the voice.
- **Camera (`camMove`):** keys `[t, [x,y,z], [lookX,lookY,lookZ], fov?]`, smootherstep between keys,
  plus a slow float (`drift`, default 0.025 m). Always moving, never jerky. In 9:16 the frame is narrow:
  at 4 m and fov 36 it is only about 1.5 m wide, so keep subjects near the centre line.
- **People (`Person`):** looks in `LOOKS` (nenek, ibu, gadis, pegawai, bapak, pemuda, anak) or your own
  spec: `skin, hair ('bun'|'bob'|'short'|'spiky'|'peci'|'hijab'|'long'|'bald'), hairCol, hijabCol, old,
  eyes ('dot'|'iris'), shirt, shirtStyle ('plain'|'office'|'kebaya'|'koko'|'kaos'|'apron'), sleeve,
  sarong + motif ('ring'|'stripe'|'kawung'), pants, kid`. Pose each frame with `set({...})`: `eyes`
  (open closed happy wide half shock), `mouth` (smile flat o grin smirk frown wavy teeth), `brows`
  (flat up angry worried one), `look:[x,y]`, `blink`, `talk` (+ `t`), `armL/armR:[a1,a2]` (0 = hanging,
  ~2.5 = raised), `walk` (phase), `lean`, `tilt`, `flip`, `sweat`, `tears`. `h` = height in metres
  (adult 1.5-1.65, child about 1.05). `face3()` gives the face position for aiming the camera.
- **World (`world.js`):** `ground, houseRow, clothesline, bamboo (glow option), tree, bush, mountain,
  hills, rice, glowShrooms, specks (fireflies/spores), rain, moon, sunDisc, clouds, lamp, table,
  basket, bucket, stool, logs, box, wallRoom`. For anything else, build from `M(geometry, colour, pos)`
  (adds ink edges) or `M(..., { hull: true })` for round shapes; `glowMat(colour)` for things that shine.
- **Light:** `makeScene(mood, overrides)` sets sky gradient, fog, hemisphere + sun with soft shadows and
  the tint the characters take. `glow` turns on bloom. Point lights (`lamp`) add warm pools at night.

## Style spec (from the reference reels)
- **Format:** 1080x1920, 30 fps (60 optional), mostly cuts, a shot every 2-3 s, wides then close-ups.
- **Characters:** wide pillow-shaped heads (about 1.2x wider than tall) on bean bodies, sleeve-tube arms
  and short legs; sawo matang skin (#b67a50) with pink blush; thick dark-plum ink (#1e1021, ~20 px at
  full size); hair or hijab with a white sheen streak; small oval eyes with a highlight, or big white eyes
  with blue irises for older people; thick brows doing most of the acting; a single hooked nose line.
  Local clothes: sarong with ring/stripe motif, koko, kebaya, office blazer with red lanyard + ID card.
- **Worlds:** low-poly kampung places (gang kontrakan, sawah, rumpun bambu, gunung, warung) with ink
  edges on hard shapes, silhouette ink on round ones, soft shadows and distance fog.
- **Light moods:** clear blue day, warm golden sunset, deep blue night with warm bulbs, stormy grey,
  and a dark green glow world with bloom for mysterious or magical beats. Characters take the tint.
- **Camera:** always gliding: slow push-ins on faces, gentle side tracks on walks, small orbits on
  objects. No whip pans, no shake (except a hit).
- **Captions:** 1-2 words, Poppins Bold, white with a dark outline and soft shadow, about 70% down
  (y 1350); sentence case kept, punctuation dropped except ! and ?; character names in yellow (#ffd23a).
  Keep faces out of y 1290-1410 when a caption is up.
- **Sound:** the voiceover leads; a quiet gamelan-ish underscore (saron + soft pad + gong on turns),
  night crickets / wind ambience, light chimes for magic moments, ducked under the voice.
- **Don't:** copy characters or stories from the reference creator; use bright saturated cartoon
  backgrounds without lighting; leave the camera static; put the caption over a face; whip-pan.
