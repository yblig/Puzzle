"""Narration: one WAV per shot + per-word timing, fully offline.

Engine order (first one installed wins; force one with --voice):
  1. Kokoro (kokoro-onnx, 82M neural TTS) - the most natural; default voice am_michael.
     Exact word times from the model's phoneme durations.
  2. Piper TTS, voice en_US-ryan-high (word times from Piper's phoneme alignments)
  3. espeak-ng with the MBROLA us2 voice - last resort, robotic; word times estimated
     from the audio's pauses and syllable counts.

Files: ~/.cache/zds/kokoro/{kokoro-v1.0.onnx,voices-v1.0.bin} (the v1.1 release of the
model, which reports durations), ~/.cache/zds/voices/en_US-ryan-high.onnx(.json), or
$ZDS_KOKORO_DIR / $ZDS_VOICE. scripts/setup.sh downloads them from GitHub releases.

A story can set VOICE = "am_michael" (any Kokoro voice) and VOICE_SPEED = 1.05.
"""
import json
import os
import re
import shutil
import subprocess
import wave

import numpy as np

VOICE_NAME = "en_US-ryan-high"
SEARCH = [os.environ.get("ZDS_VOICE", ""),
          os.path.expanduser(f"~/.cache/zds/voices/{VOICE_NAME}.onnx"),
          os.path.expanduser(f"~/.cache/zds/{VOICE_NAME}.onnx")]


KOKORO_DIR = os.environ.get("ZDS_KOKORO_DIR", os.path.expanduser("~/.cache/zds/kokoro"))
KOKORO_VOICES = {  # good narrator picks (Kokoro has more: am_*, bm_*, af_*, bf_*)
    "am_michael": "US male, warm and calm (default)",
    "am_fenrir": "US male, deeper, more dramatic",
    "am_puck": "US male, brighter and energetic",
    "am_onyx": "US male, low and slow",
    "bm_george": "UK male, documentary feel",
    "af_heart": "US female, very natural",
}


def find_kokoro():
    m = os.path.join(KOKORO_DIR, "kokoro-v1.0.onnx")
    v = os.path.join(KOKORO_DIR, "voices-v1.0.bin")
    if os.path.exists(m) and os.path.exists(v):
        try:
            import kokoro_onnx  # noqa: F401
            return m, v
        except ImportError:
            return None
    return None


def find_voice():
    for p in SEARCH:
        if p and os.path.exists(p) and os.path.exists(p + ".json"):
            return p
    return None


def words_of(line):
    return line.split()


def _syll(w):
    w = re.sub(r"[^a-z]", "", w.lower())
    if not w:
        return 1  # numbers/symbols: treat as one beat each digit group
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and n > 1 and not w.endswith("le"):
        n -= 1
    return max(1, n)


def estimate_words(audio, sr, line):
    """Word timings from pauses + syllables (used when no aligner is available)."""
    words = words_of(line)
    hop = int(0.01 * sr)
    rms = np.array([np.sqrt(np.mean(audio[i:i + hop] ** 2)) for i in range(0, len(audio) - hop, hop)])
    if not len(rms):
        return [(w, 0.0, 0.0) for w in words]
    thr = 0.06 * rms.max()
    voiced = np.where(rms > thr)[0]
    a, b = voiced[0] * 0.01, (voiced[-1] + 1) * 0.01
    # pauses = unvoiced runs >= 90 ms inside the speech span
    pauses, run = [], None
    for i in range(voiced[0], voiced[-1]):
        if rms[i] <= thr:
            run = i if run is None else run
        elif run is not None:
            if i - run >= 9:
                pauses.append((run * 0.01, i * 0.01))
            run = None
    punct = [i for i, w in enumerate(words[:-1]) if re.search(r"[,.;:!?—-]$", w)]
    # split into phrases at pauses when they line up with punctuation
    bounds = [0] + [i + 1 for i in punct] + [len(words)]
    if len(pauses) == len(punct):
        spans = [a] + [x for p in pauses for x in p] + [b]
        segs = [(spans[2 * k], spans[2 * k + 1]) for k in range(len(bounds) - 1)]
    else:
        segs = [(a, b)]
        bounds = [0, len(words)]
    out = []
    for k, (s0, s1) in enumerate(segs):
        ws = words[bounds[k]:bounds[k + 1]]
        wts = [_syll(w) + 0.35 for w in ws]
        tot = sum(wts) or 1
        t = s0
        for w, wt in zip(ws, wts):
            d = (s1 - s0) * wt / tot
            out.append((w, round(t, 3), round(t + d, 3)))
            t += d
    return out


# ---------------------------------------------------------------- engines

class Piper:
    name = "piper:" + VOICE_NAME

    def __init__(self, model, length_scale=0.95):
        from piper import PiperVoice, SynthesisConfig
        try:
            self.voice = PiperVoice.load(model, include_alignments=True)
        except TypeError:
            self.voice = PiperVoice.load(model)
        self.cfg = SynthesisConfig(length_scale=length_scale, noise_scale=0.6, noise_w_scale=0.7)

    def say(self, line, out_wav):
        chunks, groups = [], []
        offset = 0
        aligned = True
        for ch in self.voice.synthesize(line, syn_config=self.cfg, include_alignments=True):
            sr = ch.sample_rate
            chunks.append(ch.audio_float_array)
            al = ch.phoneme_alignments
            if not al:
                aligned = False
            else:
                cur, pos = None, offset
                for a in al:
                    if a.phoneme == " " or a.phoneme in ("^", "$"):
                        if cur:
                            groups.append(cur)
                        cur = None
                    elif re.fullmatch(r"[,.;:!?—\-\"']+", a.phoneme):
                        if cur:
                            cur[2] = pos
                    else:
                        if cur is None:
                            cur = [a.phoneme, pos, pos + a.num_samples]
                        else:
                            cur[0] += a.phoneme
                            cur[2] = pos + a.num_samples
                    pos += a.num_samples
                if cur:
                    groups.append(cur)
            offset += len(ch.audio_float_array)
        audio = np.concatenate(chunks)
        _write(out_wav, audio, sr)
        if aligned:
            res = align_words(words_of(line), [[g[1] / sr, g[2] / sr, len(g[0])] for g in groups])
            if res:
                return res
        return estimate_words(audio, sr, line)


def _group_words(phones, sr=None):
    """[(phoneme, start, end)] -> list of [start, end] per word (space-separated)."""
    groups, cur = [], None
    for ph, a, b in phones:
        if ph.strip() == "" or ph in ("^", "$"):
            if cur:
                groups.append(cur)
            cur = None
        elif re.fullmatch(r"[,.;:!?\u2014\u2026\-\"'\u201c\u201d()]+", ph):
            continue
        elif cur is None:
            cur = [a, b, 1]
        else:
            cur[1] = b
            cur[2] += 1
    if cur:
        groups.append(cur)
    return groups


def align_words(words, groups):
    """Map words onto phoneme groups [start, end, n_phonemes].

    The phonemizer sometimes fuses short words ("for the" -> one group), so a group
    may hold several consecutive words. A small DP picks the split whose phoneme
    counts best match the words' letter counts, then shares each group's time by
    letters. Returns None when the text has fewer words than groups (e.g. digits).
    """
    W, G = len(words), len(groups)
    if G == 0 or G > W:
        return None
    L = [max(1, len(re.sub(r"[^A-Za-z0-9']", "", w))) for w in words]
    INF = float("inf")
    best = [[INF] * (W + 1) for _ in range(G + 1)]
    back = [[0] * (W + 1) for _ in range(G + 1)]
    best[0][0] = 0.0
    for g in range(1, G + 1):
        n = groups[g - 1][2]
        for j in range(g, W - (G - g) + 1):
            for i in range(g - 1, j):
                if best[g - 1][i] == INF:
                    continue
                exp = sum(L[i:j]) * 0.85
                c = best[g - 1][i] + abs(n - exp) / max(n, exp) + 0.15 * (j - i - 1)
                if c < best[g][j]:
                    best[g][j], back[g][j] = c, i
    out, j = [], W
    spans = []
    for g in range(G, 0, -1):
        i = back[g][j]
        spans.append((i, j, groups[g - 1]))
        j = i
    for i, j, (a, b, _) in reversed(spans):
        tot = sum(L[i:j])
        t = a
        for k in range(i, j):
            d = (b - a) * L[k] / tot
            out.append((words[k], round(t, 3), round(t + d, 3)))
            t += d
    return out


class Kokoro:
    def __init__(self, voice=None, speed=None):
        from kokoro_onnx import Kokoro as K
        m, v = find_kokoro()
        self.k = K(m, v)
        self.voice = voice or os.environ.get("ZDS_KOKORO_VOICE", "am_michael")
        self.speed = speed or float(os.environ.get("ZDS_VOICE_SPEED", "1.1"))
        self.name = f"kokoro:{self.voice}"

    def say(self, line, out_wav):
        audio, sr, timing = self.k.create_timed(line, self.voice, speed=self.speed, lang="en-us",
                                                sentence_pause=0.22, clause_pause=0.08)
        audio = np.asarray(audio, dtype=np.float64)
        audio, cut = _trim_lead(audio, sr)
        audio = _polish(audio, sr)
        _write(out_wav, audio, sr)
        groups = _group_words([(t.phoneme, t.start - cut, t.end - cut) for t in timing])
        groups = [[max(0.0, g[0]), max(0.0, g[1]), g[2]] for g in groups]
        return align_words(words_of(line), groups) or estimate_words(audio, sr, line)


def _trim_lead(x, sr, pad=0.03):
    """Cut leading/trailing silence; returns (audio, seconds cut from the start)."""
    thr = 0.015 * (np.max(np.abs(x)) or 1)
    idx = np.where(np.abs(x) > thr)[0]
    if not len(idx):
        return x, 0.0
    a = max(0, idx[0] - int(pad * sr))
    b = min(len(x), idx[-1] + int(0.06 * sr))
    return x[a:b], a / sr


def _polish(x, sr):
    """Light voice clean-up: remove rumble, even out level, normalise."""
    from scipy import signal
    sos = signal.butter(2, 70, btype="high", fs=sr, output="sos")
    x = signal.sosfilt(sos, x)
    peak = np.max(np.abs(x)) or 1
    x = x / peak
    x = np.tanh(x * 1.6) / np.tanh(1.6)  # gentle compression
    return x * 0.92


class Espeak:
    def __init__(self, rate=168, pitch=38):
        exe = shutil.which("espeak-ng") or shutil.which("espeak")
        if not exe:
            raise RuntimeError("no TTS available: install the Piper voice or espeak-ng")
        self.exe, self.rate, self.pitch = exe, rate, pitch
        self.voice = "mb-us2" if os.path.isdir("/usr/share/mbrola/us2") else "en-us+m3"
        self.name = "espeak-ng:" + self.voice

    def say(self, line, out_wav):
        subprocess.run([self.exe, "-v", self.voice, "-s", str(self.rate), "-p", str(self.pitch),
                        "-w", out_wav, line], check=True, capture_output=True)
        audio, sr = _read(out_wav)
        audio = _trim(audio, sr)
        _write(out_wav, audio / (np.max(np.abs(audio)) or 1) * 0.9, sr)
        return estimate_words(audio, sr, line)


def engine(prefer="auto", voice=None, speed=None):
    if prefer in ("auto", "kokoro") and find_kokoro():
        return Kokoro(voice, speed)
    if prefer == "kokoro":
        raise RuntimeError(f"Kokoro model not found in {KOKORO_DIR} (run scripts/setup.sh)")
    v = find_voice()
    if prefer in ("auto", "piper") and v:
        return Piper(v)
    if prefer == "piper":
        raise RuntimeError(f"Piper voice {VOICE_NAME} not found in {SEARCH}")
    return Espeak()


# ---------------------------------------------------------------- io

def _trim(x, sr, pad=0.04):
    idx = np.where(np.abs(x) > 0.02 * (np.max(np.abs(x)) or 1))[0]
    if not len(idx):
        return x
    a = max(0, idx[0] - int(pad * sr))
    b = min(len(x), idx[-1] + int(pad * sr))
    return x[a:b]


def _read(path):
    with wave.open(path) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
        if w.getnchannels() > 1:
            x = x.reshape(-1, w.getnchannels()).mean(axis=1)
    return x, sr


def _write(path, x, sr):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def narrate(story, work, prefer="auto"):
    """Write WORK/voice/<id>.wav and WORK/timing.json for every shot."""
    eng = engine(prefer, getattr(story, "VOICE", None), getattr(story, "VOICE_SPEED", None))
    vdir = os.path.join(work, "voice")
    os.makedirs(vdir, exist_ok=True)
    shots = []
    for s in story.SHOTS:
        wav = os.path.join(vdir, f"{s.id}.wav")
        if s.line.strip():
            words = eng.say(s.line, wav)
            x, sr = _read(wav)
            dur = len(x) / sr
        else:
            words, dur, wav = [], 0.0, None
        shots.append({"id": s.id, "line": s.line, "wav": wav, "vo_dur": round(dur, 3),
                      "words": words})
    timing = {"voice": eng.name, "shots": shots}
    with open(os.path.join(work, "timing.json"), "w") as fh:
        json.dump(timing, fh, indent=1)
    return timing
