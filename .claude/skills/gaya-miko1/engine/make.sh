#!/usr/bin/env bash
# Build a /gaya-miko1 reel end to end: voice -> word timings -> ambience + SFX -> 3D picture -> <reel>/<name>.mp4
#   make.sh <reel-folder> [path/to/voiceover.mp3 | draft]
#   make.sh ~/reels/mbah ~/Downloads/elevenlabs.mp3   # the user's Indonesian voiceover (recommended)
#   make.sh ~/reels/mbah draft                        # free draft voice, for testing timing only
#   make.sh ~/reels/mbah                              # reuse audio/vo.wav
#   FPS=60 make.sh ...      smoother motion (twice the render time)
#   WORKERS=8 make.sh ...   more parallel renderers on a bigger machine
#   AUDIO_ONLY=1 make.sh .. remix the sound only (reuses the last picture)
set -euo pipefail
ENGINE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# kit (node packages, Python venv, models): $KIT, else a repo-level .claude/kit, else ~/.cache/gaya-miko1/kit
if [ -z "${KIT:-}" ]; then
  KIT="$(cd "$ENGINE/../../../kit" 2>/dev/null && pwd || true)"
  [ -d "$KIT/node_modules/three" ] || KIT="$HOME/.cache/gaya-miko1/kit"
fi
export KIT
[ -d "$KIT/node_modules/three" ] && [ -x "$KIT/.venv/bin/python" ] || bash "$ENGINE/../kit/setup.sh"
[ -z "${CHROME:-}" ] && [ -x /opt/pw-browsers/chromium ] && export CHROME=/opt/pw-browsers/chromium
DIR="$(cd "${1:?usage: make.sh <reel-folder> [voiceover-file|draft]}" && pwd)"
VOICE="${2:-keep}"
WORKERS="${WORKERS:-4}"
export FPS="${FPS:-30}"
PY="$KIT/.venv/bin/python"
export NODE_PATH="$KIT/node_modules"
NAME="$(basename "$DIR")"
cd "$DIR"; mkdir -p audio

echo "== voice: $VOICE"
case "$VOICE" in
  keep)  [ -f audio/vo.wav ] || { echo "no audio/vo.wav yet: pass the voiceover file (or 'draft')"; exit 1; } ;;
  draft) [ -s "$KIT/models/kokoro-v1.0.onnx" ] || bash "$ENGINE/../kit/setup.sh" --draft
         "$PY" "$ENGINE/tools/tts_draft.py"; cp audio/vo_draft.wav audio/vo.wav ;;
  *)     ffmpeg -v error -y -i "$VOICE" -ac 1 -ar 44100 audio/vo.wav ;;
esac
ffmpeg -v error -y -i audio/vo.wav -af "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse" audio/vo_trim.wav && mv audio/vo_trim.wav audio/vo.wav

echo "== aligning words (Whisper)"
"$PY" "$ENGINE/tools/align_id.py" audio/vo.wav

echo "== ambience + sfx mix"
"$PY" audio.py

if [ "${AUDIO_ONLY:-0}" != "1" ] || [ ! -f silent.mp4 ]; then
  N=$(grep -c "^shot(" web/shots.js)
  echo "== rendering $N shots at ${FPS} fps with $WORKERS workers"
  rm -rf seg; mkdir -p seg
  pids=()
  for ((w = 0; w < WORKERS; w++)); do
    ids=""; for ((i = w; i < N; i += WORKERS)); do ids="${ids:+$ids,}$i"; done
    [ -n "$ids" ] && { node "$ENGINE/tools/render.js" segments "$ids" > "seg/log$w.txt" 2>&1 & pids+=($!); }
  done
  for p in "${pids[@]}"; do wait "$p"; done
  [ "$(ls seg/shot_??.mp4 | wc -l)" -eq "$N" ] || { echo "a shot failed to render, see $DIR/seg/log*.txt"; exit 1; }
  HERE="$PWD"; command -v cygpath >/dev/null && HERE="$(cygpath -m "$PWD")"
  for f in seg/shot_??.mp4; do echo "file '$HERE/$f'"; done > seg/list.txt
  ffmpeg -v error -y -f concat -safe 0 -i seg/list.txt -c copy silent.mp4
fi

echo "== final mux"
ffmpeg -v error -y -i silent.mp4 -i audio/mix.wav -map 0:v -map 1:a -c:v copy \
  -af "alimiter=limit=0.8:attack=2:release=60,loudnorm=I=-14:TP=-1.5:LRA=9" \
  -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart "$NAME.part.mp4"
mv "$NAME.part.mp4" "$NAME.mp4"
echo "done: $DIR/$NAME.mp4"
