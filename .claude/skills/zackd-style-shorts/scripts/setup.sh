#!/usr/bin/env bash
# One-time setup for zackd-style-shorts. Safe to re-run.
# Installs: bpy (Blender as a Python module), kokoro-onnx + piper-tts, numpy/scipy/pillow,
# ffmpeg, Mesa EGL (headless Workbench), espeak-ng (last-resort voice), and downloads
# into ~/.cache/zds: the Kokoro model + voices, the Piper voice en_US-ryan-high,
# and the Poppins Bold font. All downloads come from GitHub releases / npm, so a
# network that blocks huggingface.co still works.
set -u
CACHE="${HOME}/.cache/zds"
mkdir -p "$CACHE/voices" "$CACHE/kokoro"
PKGS="bpy kokoro-onnx piper-tts onnx onnxruntime numpy scipy pillow fonttools brotli"
python3 -m pip install -q $PKGS 2>/dev/null || python3 -m pip install -q --break-system-packages $PKGS

if command -v apt-get >/dev/null; then
  SUDO=""; [ "$(id -u)" != 0 ] && SUDO="sudo"
  $SUDO apt-get update -qq || true
  DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y -qq ffmpeg libegl1 libegl-mesa0 \
    libgl1-mesa-dri espeak-ng mbrola-us2 >/dev/null 2>&1 \
    || echo "[setup] apt install failed for some packages (ffmpeg/EGL/espeak-ng)"
elif command -v brew >/dev/null; then
  brew install ffmpeg espeak-ng >/dev/null 2>&1 || true   # macOS: Workbench uses Metal, no EGL needed
fi

fetch() {  # fetch URL DEST  (skips when DEST exists and is non-empty)
  [ -s "$2" ] && return 0
  curl -fsSL --retry 3 -o "$2.part" "$1" && mv "$2.part" "$2" || { rm -f "$2.part"; return 1; }
}

# Kokoro (main voice). v1.1 release of the model = the export that reports phoneme
# durations, which gives exact word timing for captions.
KR="https://github.com/thewh1teagle/kokoro-onnx/releases/download"
fetch "$KR/model-files-v1.1/kokoro-v1.0.onnx" "$CACHE/kokoro/kokoro-v1.0.onnx" \
  && fetch "$KR/model-files-v1.0/voices-v1.0.bin" "$CACHE/kokoro/voices-v1.0.bin" \
  && echo "[setup] Kokoro ready" || echo "[setup] Kokoro download failed (github.com blocked?)"

# Piper ryan-high (second choice): GitHub release first, Hugging Face as a fallback.
V=en_US-ryan-high
if [ ! -s "$CACHE/voices/$V.onnx" ]; then
  TMP=$(mktemp -d)
  if curl -fsSL --retry 3 "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-en-us-ryan-high.tar.gz" \
       | tar xz -C "$TMP" 2>/dev/null && [ -s "$TMP/en-us-ryan-high.onnx" ]; then
    mv "$TMP/en-us-ryan-high.onnx" "$CACHE/voices/$V.onnx"
    mv "$TMP/en-us-ryan-high.onnx.json" "$CACHE/voices/$V.onnx.json"
  else
    HF="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high"
    fetch "$HF/$V.onnx" "$CACHE/voices/$V.onnx" && fetch "$HF/$V.onnx.json" "$CACHE/voices/$V.onnx.json" \
      || rm -f "$CACHE/voices/$V.onnx"*
  fi
  rm -rf "$TMP"
  [ -s "$CACHE/voices/$V.onnx" ] && echo "[setup] Piper voice ready" || echo "[setup] Piper voice not downloaded (optional)"
fi

# Poppins Bold: Google Fonts on GitHub, else the @fontsource npm package (woff2 -> ttf).
if ! python3 -c "from PIL import ImageFont; ImageFont.truetype('$CACHE/Poppins-Bold.ttf', 20)" 2>/dev/null; then
  rm -f "$CACHE/Poppins-Bold.ttf"
  if ! fetch "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf" "$CACHE/Poppins-Bold.ttf" \
      || ! python3 -c "from PIL import ImageFont; ImageFont.truetype('$CACHE/Poppins-Bold.ttf', 20)" 2>/dev/null; then
    rm -f "$CACHE/Poppins-Bold.ttf"
    TMP=$(mktemp -d)
    curl -fsSL https://registry.npmjs.org/@fontsource/poppins/-/poppins-5.3.0.tgz | tar xz -C "$TMP" \
     && python3 -c "
from fontTools.ttLib import TTFont
f = TTFont('$TMP/package/files/poppins-latin-700-normal.woff2'); f.flavor = None
f.save('$CACHE/Poppins-Bold.ttf')" && echo "[setup] Poppins installed (fontsource)"
    rm -rf "$TMP"
  fi
fi
python3 "$(dirname "$0")/make_short.py" doctor
