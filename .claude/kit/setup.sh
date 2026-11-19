#!/usr/bin/env bash
# Linux/macOS setup for /stick-figure (Node packages, plus voice tools with --voice).
#   bash .claude/kit/setup.sh --voice
# Safe to run again. Needs python3, node/npm and ffmpeg on PATH.
set -euo pipefail
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$KIT"
npm install --no-audit --no-fund --loglevel=error
# Use a preinstalled Chromium if CHROME points to one; otherwise fetch Playwright's.
[ -n "${CHROME:-}" ] || npx --yes playwright install chromium
if [ "${1:-}" = "--voice" ]; then
  [ -x .venv/bin/python ] || python3 -m venv .venv
  .venv/bin/python -m pip install -q --upgrade pip
  .venv/bin/python -m pip install -q numpy scipy soundfile kokoro-onnx sherpa-onnx faster-whisper
  M="$KIT/models"; mkdir -p "$M"
  [ -s "$M/kokoro-v1.0.onnx" ] || curl -fL -o "$M/kokoro-v1.0.onnx" https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
  [ -s "$M/voices-v1.0.bin" ]  || curl -fL -o "$M/voices-v1.0.bin"  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
  if ! ls -d "$M"/sherpa-onnx-nemo-parakeet* >/dev/null 2>&1; then
    curl -fL -o "$M/p.tar.bz2" https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.tar.bz2
    (cd "$M" && tar xjf p.tar.bz2 && rm -f p.tar.bz2)
  fi
  .venv/bin/python -c "import kokoro_onnx, sherpa_onnx" && echo "voice tools ready"
fi
echo "kit ready"
