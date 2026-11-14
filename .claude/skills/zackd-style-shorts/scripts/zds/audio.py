"""Procedural sound effects + suspense music bed + mixing (numpy/scipy, offline).

SFX names: whoosh pop impact ding heartbeat rumble riser splat tick crack
           sizzle glug  (+ aliases: boom=impact, thud=impact, swoosh=whoosh)
"""
import math
import wave

import numpy as np
from scipy import signal

SR = 44100


def _t(dur):
    return np.arange(int(dur * SR)) / SR


def _env(n, a=0.005, d=None, curve=4.0):
    """Attack then exponential-ish decay over n samples."""
    na = max(1, int(a * SR))
    e = np.ones(n)
    e[:na] = np.linspace(0, 1, na)
    rest = n - na
    if rest > 0:
        e[na:] = np.exp(-curve * np.linspace(0, 1, rest))
    return e


def _noise(n, seed=0):
    return np.random.default_rng(seed).standard_normal(n)


def _bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, min(hi, SR / 2 - 100)], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def _lp(x, f, order=2):
    sos = signal.butter(order, min(f, SR / 2 - 100), btype="low", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def _hp(x, f, order=2):
    sos = signal.butter(order, f, btype="high", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def _norm(x, peak=0.9):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def _sweep_filter(x, f0, f1, q=3.0, block=512):
    """Time-varying band-pass (for whooshes/risers)."""
    out = np.zeros_like(x)
    n = len(x)
    zi = None
    for i in range(0, n, block):
        f = f0 * (f1 / f0) ** (i / max(1, n))
        bw = f / q
        sos = signal.butter(2, [max(20, f - bw), min(SR / 2 - 200, f + bw)], btype="band",
                            fs=SR, output="sos")
        if zi is None:
            zi = signal.sosfilt_zi(sos) * 0
        out[i:i + block], zi = signal.sosfilt(sos, x[i:i + block], zi=zi)
    return out


# ---------------------------------------------------------------- sfx

def whoosh(dur=0.45, seed=1, up=True):
    n = int(dur * SR)
    x = _noise(n, seed)
    x = _sweep_filter(x, 300 if up else 2500, 2500 if up else 300, q=2.0)
    e = np.sin(np.linspace(0, math.pi, n)) ** 1.6
    return _norm(x * e, 0.7)


def pop(dur=0.12, f0=900, f1=250):
    t = _t(dur)
    f = f1 + (f0 - f1) * np.exp(-t * 40)
    ph = 2 * math.pi * np.cumsum(f) / SR
    x = np.sin(ph) * _env(len(t), 0.002, curve=6)
    return _norm(x, 0.8)


def impact(dur=0.9, seed=2):
    t = _t(dur)
    f = 45 + 90 * np.exp(-t * 18)
    body = np.sin(2 * math.pi * np.cumsum(f) / SR) * _env(len(t), 0.002, curve=5)
    hit = _lp(_noise(len(t), seed), 3000) * _env(len(t), 0.001, curve=30)
    return _norm(body * 1.0 + hit * 0.5, 0.95)


def ding(dur=1.4, f=1318.5):
    t = _t(dur)
    x = sum(a * np.sin(2 * math.pi * f * k * t) * np.exp(-t * d)
            for k, a, d in ((1, 1, 3), (2.76, 0.4, 5), (5.4, 0.2, 8), (0.5, 0.25, 2.5)))
    return _norm(x * _env(len(t), 0.002, curve=0.1), 0.6)


def heartbeat(beats=2, bpm=70):
    period = 60 / bpm
    out = np.zeros(int(beats * period * SR) + SR // 2)
    for b in range(beats):
        for off, g in ((0.0, 1.0), (0.22, 0.7)):
            t = _t(0.18)
            th = np.sin(2 * math.pi * (55 + 30 * np.exp(-t * 30)) * t) * _env(len(t), 0.004, curve=7)
            i = int((b * period + off) * SR)
            out[i:i + len(th)] += th * g
    return _norm(_lp(out, 400), 0.9)


def rumble(dur=2.0, seed=3):
    n = int(dur * SR)
    x = _lp(_noise(n, seed), 120, order=4)
    lfo = 0.6 + 0.4 * np.sin(2 * math.pi * 3.0 * _t(dur))
    e = np.minimum(1, np.linspace(0, 4, n)) * np.minimum(1, np.linspace(4, 0, n))
    return _norm(x * lfo * e, 0.85)


def riser(dur=1.6, seed=4):
    n = int(dur * SR)
    x = _sweep_filter(_noise(n, seed), 200, 6000, q=4.0)
    t = _t(dur)
    tone = np.sin(2 * math.pi * np.cumsum(200 * (8 ** (t / dur))) / SR)
    e = np.linspace(0, 1, n) ** 2.2
    return _norm((x + 0.25 * tone) * e, 0.7)


def splat(dur=0.5, seed=5):
    n = int(dur * SR)
    x = _lp(_noise(n, seed), 1200) * _env(n, 0.002, curve=9)
    t = _t(dur)
    sq = np.sin(2 * math.pi * np.cumsum(300 * np.exp(-t * 8) + 80) / SR) * _env(n, 0.01, curve=6)
    return _norm(x + 0.6 * sq, 0.85)


def tick(dur=0.05):
    n = int(dur * SR)
    x = _hp(_noise(n, 6), 3000) * _env(n, 0.0005, curve=40)
    x += 0.4 * np.sin(2 * math.pi * 2200 * _t(dur)) * _env(n, 0.0005, curve=30)
    return _norm(x, 0.6)


def crack(dur=0.25, seed=7, snaps=3):
    """Knuckle/bone crack: a few sharp, close transients."""
    n = int(dur * SR)
    rnd = np.random.default_rng(seed)
    out = np.zeros(n)
    t0 = 0
    for k in range(snaps):
        m = int(0.03 * SR)
        burst = _bp(_noise(m, seed + k), 900, 6000) * _env(m, 0.0003, curve=35)
        out[t0:t0 + m] += burst[: n - t0] * (1.0 if k == 0 else 0.6)
        t0 += int(rnd.uniform(0.012, 0.035) * SR)
        if t0 >= n:
            break
    body = np.sin(2 * math.pi * 180 * _t(dur)) * _env(n, 0.0005, curve=25)
    return _norm(out + 0.3 * body, 0.95)


def sizzle(dur=1.2, seed=8):
    n = int(dur * SR)
    rnd = np.random.default_rng(seed)
    hiss = _hp(_noise(n, seed), 4000) * 0.3
    crackle = np.zeros(n)
    for i in rnd.integers(0, n - 200, size=int(dur * 60)):
        crackle[i:i + 120] += _hp(_noise(120, int(i)), 2000) * rnd.uniform(0.3, 1)
    e = np.minimum(1, np.linspace(0, 6, n)) * np.minimum(1, np.linspace(5, 0, n))
    return _norm((hiss + crackle) * e, 0.6)


def glug(dur=0.9, bubbles=4, seed=9):
    rnd = np.random.default_rng(seed)
    out = np.zeros(int(dur * SR))
    for b in range(bubbles):
        d = rnd.uniform(0.07, 0.12)
        t = _t(d)
        f0 = rnd.uniform(250, 450)
        x = np.sin(2 * math.pi * np.cumsum(f0 * (1 + 1.5 * t / d)) / SR) * _env(len(t), 0.004, curve=5)
        i = int(b * dur / bubbles * SR)
        out[i:i + len(x)] += x[: len(out) - i]
    return _norm(_lp(out, 2500), 0.8)


def bubble(dur=0.15):
    t = _t(dur)
    x = np.sin(2 * math.pi * np.cumsum(500 + 1500 * t / dur) / SR) * _env(len(t), 0.003, curve=6)
    return _norm(x, 0.6)


SFX = {"whoosh": whoosh, "swoosh": whoosh, "pop": pop, "impact": impact, "boom": impact,
       "thud": lambda: impact(0.5), "ding": ding, "heartbeat": heartbeat, "rumble": rumble,
       "riser": riser, "splat": splat, "tick": tick, "crack": crack, "sizzle": sizzle,
       "glug": glug, "bubble": bubble}


def sfx(name):
    return SFX[name]()


# ---------------------------------------------------------------- music

def _reverb(x, secs=1.8, mix=0.3, seed=11):
    n = int(secs * SR)
    ir = _noise(n, seed) * np.exp(-np.linspace(0, 7, n))
    ir = _lp(ir, 5000)
    wet = signal.fftconvolve(x, ir)[: len(x)]
    wet = wet / (np.max(np.abs(wet)) or 1) * (np.max(np.abs(x)) or 1)
    return x * (1 - mix) + wet * mix


def suspense_bed(dur, bpm=84, root=55.0, seed=12):
    """Dark, pulsing tension bed in A minor: drone + sub pulse + sparse plucks + ticks."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    rnd = np.random.default_rng(seed)
    beat = 60 / bpm
    # drone: detuned saws, low-passed, slow swell
    drone = np.zeros(n)
    for f, g in ((root, 1), (root * 1.5, 0.5), (root * 2.003, 0.4), (root * 0.998, 0.8)):
        drone += g * signal.sawtooth(2 * math.pi * f * t)
    drone = _lp(drone, 380, order=4) * (0.75 + 0.25 * np.sin(2 * math.pi * t / 7.0))
    # sub pulse on every beat
    pulse = np.zeros(n)
    pt = _t(0.35)
    th = np.sin(2 * math.pi * (root + 25 * np.exp(-pt * 25)) * pt) * _env(len(pt), 0.004, curve=6)
    for k in range(int(dur / beat) + 1):
        i = int(k * beat * SR)
        if i < n:
            pulse[i:i + len(th)] += th[: n - i] * (1.0 if k % 4 == 0 else 0.55)
    # plucks: minor arpeggio, every half bar
    notes = [220.0, 261.63, 329.63, 246.94, 220.0, 196.0, 329.63, 293.66]
    pl = np.zeros(n)
    for k in range(int(dur / (beat * 2)) + 1):
        f = notes[k % len(notes)] * (2 if rnd.random() < 0.2 else 1)
        d = _t(1.2)
        x = (np.sin(2 * math.pi * f * d) + 0.3 * np.sin(2 * math.pi * 2 * f * d)) * np.exp(-d * 4)
        i = int(k * beat * 2 * SR)
        if i < n:
            pl[i:i + len(x)] += x[: n - i]
    pl = _reverb(pl, 2.2, 0.45)
    # hi ticks on off-beats (clock-like tension)
    tk = np.zeros(n)
    one = tick()
    for k in range(int(dur / (beat / 2)) + 1):
        if k % 2 == 1:
            i = int(k * beat / 2 * SR)
            if i < n:
                tk[i:i + len(one)] += one[: n - i]
    # high string that slowly fades in
    vib = 1 + 0.004 * np.sin(2 * math.pi * 5 * t)
    string = np.sin(2 * math.pi * np.cumsum(880 * vib) / SR) * np.minimum(1, t / max(dur * 0.8, 1)) * 0.15
    mix = 0.35 * _norm(drone) + 0.45 * _norm(pulse) + 0.25 * _norm(pl) + 0.12 * _norm(tk) + string
    fade = np.minimum(1, t / 0.8) * np.minimum(1, (dur - t) / 1.2).clip(0, 1)
    return _norm(mix * fade, 0.8)


# ---------------------------------------------------------------- mixing

def read_wav(path):
    with wave.open(path) as w:
        sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(w.getnframes())
    x = np.frombuffer(raw, dtype={2: np.int16, 4: np.int32}[sw]).astype(np.float64)
    x /= float(2 ** (8 * sw - 1))
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    if sr != SR:
        g = math.gcd(sr, SR)
        x = signal.resample_poly(x, SR // g, sr // g)
    return x


def write_wav(path, x, stereo=True):
    x = np.clip(x, -1, 1)
    pcm = (x * 32767).astype(np.int16)
    if stereo:
        pcm = np.repeat(pcm[:, None], 2, axis=1).reshape(-1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2 if stereo else 1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def place(track, clip, at, gain=1.0):
    i = int(max(0, at) * SR)
    if i >= len(track):
        return
    seg = clip[: len(track) - i]
    track[i:i + len(seg)] += seg * gain


def duck_gain(voice, depth=0.72):
    """Gain curve that drops the music under the voice (sidechain style, vectorised)."""
    env = np.abs(voice)
    win = int(0.03 * SR)
    env = np.convolve(env, np.ones(win) / win, mode="same")
    on = (env > 0.02).astype(float)
    # attack: max-filter forward 50 ms; release: smooth 350 ms
    k = int(0.35 * SR)
    held = np.convolve(on, np.ones(int(0.12 * SR)), mode="same") > 0
    sm = np.convolve(held.astype(float), np.hanning(k) / np.hanning(k).sum(), mode="same")
    return 1 - depth * np.clip(sm * 1.4, 0, 1)


def master(x, peak=0.89):
    """Gentle soft-clip limiter + normalise."""
    x = np.tanh(x * 1.2) / np.tanh(1.2)
    return _norm(x, peak)
