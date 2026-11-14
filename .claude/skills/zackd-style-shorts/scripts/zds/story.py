"""Story file model: Shot list -> timed plan.

A story is a Python file defining:

    TITLE = "What happens when you crack your knuckles"
    FACTS = [("claim", "source"), ...]     # every factual claim, checked
    SHOTS = [Shot("hook", "line...", build_hook, sfx=[("pop", "w2")]), ...]

Each build function receives a Ctx and builds + animates the whole shot.
"""
import importlib.util
import json
import math
import os
import re

LEAD = 0.15  # seconds of picture before the narration starts in every shot


class Shot:
    def __init__(self, id, line, build, sfx=(), min_len=2.0, hold=0.35, still=None, music=True):
        """
        id      short unique name ("hook", "x_ray", "payoff")
        line    the narration line for this shot (one idea, one sentence)
        build   function(ctx) that builds and animates the shot
        sfx     list of (name, when[, gain]) — when is seconds from shot start,
                "w3" = start of word 3 (0-based), "end" or "end-0.4" = before the cut
        min_len minimum shot length in seconds (for silent beats / long animations)
        hold    extra seconds after the line ends before the cut
        still   time (s) used for the contact-sheet frame (default: 60% of the shot)
        """
        self.id, self.line, self.build = id, line, build
        self.sfx, self.min_len, self.hold, self.still, self.music = list(sfx), min_len, hold, still, music


class Ctx:
    """What a build function gets: timing helpers for one shot."""

    def __init__(self, shot, plan_entry, fps, quality="fast"):
        self.shot = shot
        self.fps = fps
        self.dur = plan_entry["dur"]
        self.frames = plan_entry["frames"]
        self.words = [tuple(w) for w in plan_entry["words"]]  # (word, t0, t1) shot-relative
        self.vo_start = plan_entry["vo_start"]
        self.vo_end = plan_entry["vo_end"]
        self.quality = quality
        self.start, self.end = 1, self.frames

    def f(self, t):
        """Seconds (shot-relative) -> frame number (1-based, clamped). Negative t counts from the end."""
        if t < 0:
            t = self.dur + t
        return int(max(1, min(self.frames, 1 + round(t * self.fps))))

    def w(self, i):
        """Start time (s) of word i (0-based; negative indexes from the end)."""
        if not self.words:
            return self.vo_start
        return self.words[max(-len(self.words), min(i, len(self.words) - 1))][1]

    def we(self, i):
        if not self.words:
            return self.vo_end
        return self.words[max(-len(self.words), min(i, len(self.words) - 1))][2]

    def wf(self, i):
        """Frame where word i starts — sync visuals to the narration with this."""
        return self.f(self.w(i))

    def find(self, word, nth=0):
        """Index of the nth word matching (case/punctuation-insensitive)."""
        target = _norm(word)
        hits = [i for i, (wd, _, _) in enumerate(self.words) if _norm(wd) == target]
        if len(hits) <= nth:
            raise KeyError(f"word {word!r} not in line {self.shot.line!r}")
        return hits[nth]

    def at(self, word, nth=0):
        """Frame where a given word is spoken: ctx.at("crack")."""
        return self.wf(self.find(word, nth))


def _norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower())


def load(path):
    spec = importlib.util.spec_from_file_location("zds_story", os.path.abspath(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ids = [s.id for s in mod.SHOTS]
    if len(set(ids)) != len(ids):
        raise ValueError("shot ids must be unique")
    mod.FPS = getattr(mod, "FPS", 30)
    return mod


def plan(story, timing):
    """Combine shots with narration timing -> list of dicts with start/dur/frames."""
    fps = story.FPS
    by_id = {t["id"]: t for t in timing["shots"]}
    out, t0 = [], 0.0
    for s in story.SHOTS:
        tm = by_id.get(s.id, {"vo_dur": 0, "words": [], "wav": None})
        vo = tm["vo_dur"]
        dur = max(s.min_len, LEAD + vo + s.hold)
        frames = int(math.ceil(dur * fps))
        dur = frames / fps
        words = [(w, a + LEAD, b + LEAD) for w, a, b in tm["words"]]
        out.append({"id": s.id, "start": t0, "dur": dur, "frames": frames, "words": words,
                    "vo_start": LEAD, "vo_end": LEAD + vo, "wav": tm.get("wav")})
        t0 += dur
    return out


def load_plan(story, work):
    with open(os.path.join(work, "timing.json")) as fh:
        return plan(story, json.load(fh))
