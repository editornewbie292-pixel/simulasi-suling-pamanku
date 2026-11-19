#!/usr/bin/env bash
# One-time setup for /gaya-miko1 (safe to run again). Installs into $KIT, default ~/.cache/gaya-miko1/kit,
# so the skill folder itself can stay read-only.
#   bash <skill>/kit/setup.sh           three.js + Playwright + faster-whisper (word timing)
#   bash <skill>/kit/setup.sh --draft   + the free draft voice (Kokoro, about 340 MB)
# Needs node/npm, python3 and ffmpeg. The Whisper model downloads from huggingface.co on first align.
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIT="${KIT:-$HOME/.cache/gaya-miko1/kit}"
mkdir -p "$KIT/models"; cp "$SRC/package.json" "$KIT/package.json"
cd "$KIT"
if [ ! -d node_modules/three ] || [ ! -d node_modules/playwright ]; then npm install --no-audit --no-fund --loglevel=error; fi
# a preinstalled Chromium (CHROME, or the cloud image's /opt/pw-browsers) saves a download
if [ -z "${CHROME:-}" ] && [ ! -x /opt/pw-browsers/chromium ]; then npx --yes playwright install chromium; fi
[ -x .venv/bin/python ] || python3 -m venv .venv
.venv/bin/python -c "import faster_whisper, scipy, soundfile" 2>/dev/null || { .venv/bin/python -m pip install -q --upgrade pip; .venv/bin/python -m pip install -q numpy scipy soundfile faster-whisper; }
if [ "${1:-}" = "--draft" ]; then
  .venv/bin/python -c "import kokoro_onnx" 2>/dev/null || .venv/bin/python -m pip install -q kokoro-onnx
  [ -s models/kokoro-v1.0.onnx ] || curl -fL -o models/kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
  [ -s models/voices-v1.0.bin ] || curl -fL -o models/voices-v1.0.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
fi
echo "gaya-miko1 kit ready: $KIT"
