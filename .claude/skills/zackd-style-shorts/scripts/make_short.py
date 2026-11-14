#!/usr/bin/env python3
"""Zack-D-style short pipeline.

    python make_short.py doctor                       # check dependencies
    python make_short.py voices -w samples/           # hear each narrator voice
    python make_short.py check    STORY.py            # lint the script against the rules
    python make_short.py narrate  STORY.py -w WORK    # TTS + word timing
    python make_short.py sheet    STORY.py -w WORK    # one still per shot -> contact_sheet.png
    python make_short.py render   STORY.py -w WORK [--shots a,b] [--hq] [-j 2]
    python make_short.py assemble STORY.py -w WORK [-o final.mp4]
    python make_short.py all      STORY.py -w WORK    # everything, in order

WORK defaults to ./work_<story-name>. Output: WORK/final.mp4 (1080x1920, 30 fps).
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

OUT_W, OUT_H = 1080, 1920
FONT_DIR = os.path.expanduser("~/.cache/zds")


def log(msg):
    print(f"[zds] {msg}", flush=True)


def load_story(path):
    from zds import story
    return story.load(path)


# ------------------------------------------------------------------ doctor

def cmd_doctor(a):
    ok = True
    def chk(name, cond, fix):
        nonlocal ok
        print(f"  {'OK ' if cond else 'MISSING'}  {name}" + ("" if cond else f"   -> {fix}"))
        ok &= bool(cond)
    try:
        import bpy
        chk(f"bpy {bpy.app.version_string}", True, "")
    except Exception as e:  # noqa: BLE001
        chk("bpy (Blender as a Python module)", False, f"pip install bpy  ({e})")
    for mod in ("numpy", "scipy", "PIL"):
        try:
            __import__(mod)
            chk(mod, True, "")
        except ImportError:
            chk(mod, False, f"pip install {mod if mod != 'PIL' else 'pillow'}")
    chk("ffmpeg (with libass)", shutil.which("ffmpeg") and b"libass" in subprocess.run(
        ["ffmpeg", "-hide_banner", "-buildconf"], capture_output=True).stdout, "apt-get install ffmpeg")
    from zds import narrate
    kk = narrate.find_kokoro()
    v = narrate.find_voice()
    chk("Kokoro TTS (main voice)", kk, "bash scripts/setup.sh (pip kokoro-onnx + model from GitHub)")
    print(f"  {'OK ' if v else '-- '}  Piper voice {narrate.VOICE_NAME} (second choice)")
    fb = shutil.which("espeak-ng")
    print(f"  {'OK ' if fb else '-- '}  espeak-ng (last-resort robotic voice)")
    chk("Poppins-Bold.ttf", os.path.exists(os.path.join(FONT_DIR, "Poppins-Bold.ttf")),
        "bash scripts/setup.sh")
    chk("EGL for Workbench (libEGL.so.1)", any(os.path.exists(p) for p in (
        "/usr/lib/x86_64-linux-gnu/libEGL.so.1", "/usr/lib/aarch64-linux-gnu/libEGL.so.1",
        "/usr/lib64/libEGL.so.1")), "apt-get install libegl1 libegl-mesa0 libgl1-mesa-dri")
    print("ready" if ok else "some pieces are missing (see above)")
    return 0 if ok else 1


# ------------------------------------------------------------------ check

GREETING = re.compile(r"^(hi|hey|hello|welcome|what'?s up|yo|today|in this video|let'?s talk|"
                      r"did you know|so,|okay|ok)\b", re.I)
PAST = re.compile(r"\b(was|were|had|did|went|became|happened|cracked|felt)\b", re.I)


def cmd_check(a):
    st = load_story(a.story)
    lines = [s.line for s in st.SHOTS]
    words = sum(len(l.split()) for l in lines)
    errs, warns = [], []
    n = len(st.SHOTS)
    if not 7 <= n <= 12:
        errs.append(f"{n} shots — need 7-12 (one line per shot)")
    if not 70 <= words <= 120:
        errs.append(f"{words} words — need 70-120")
    if lines and GREETING.search(lines[0].strip()):
        errs.append(f"first line is a greeting/warm-up, not a hook: {lines[0]!r}")
    if lines and lines[0].lower().startswith("have you ever"):
        warns.append("'Have you ever...' is a weak hook — open on the event itself")
    you = sum(1 for l in lines if re.search(r"\byou(r|'re|'ll)?\b", l, re.I))
    if you < n * 0.6:
        warns.append(f"only {you}/{n} lines speak to 'you' — keep it second person")
    for s in st.SHOTS:
        wc = len(s.line.split())
        if re.search(r"\b(I|we|my|our)\b", s.line):
            warns.append(f"[{s.id}] first person — use 'you': {s.line!r}")
        if PAST.search(s.line):
            warns.append(f"[{s.id}] past tense? keep it present: {s.line!r}")
        if wc > 20:
            warns.append(f"[{s.id}] {wc} words — likely more than one idea, split it")
        if len(re.findall(r"[.!?](\s|$)", s.line.strip())) > 2:
            warns.append(f"[{s.id}] more than two sentences in one shot")
    facts = getattr(st, "FACTS", None)
    if not facts:
        errs.append("FACTS list is empty — every claim needs a checked source")
    est = words / 2.8 + n * 0.45  # ~2.8 words/s + lead-in/holds
    if not 25 <= est <= 50:
        warns.append(f"estimated length {est:.0f}s (target 25-50s)")
    print(f"shots={n} words={words} est≈{est:.0f}s facts={len(facts or [])}")
    for e in errs:
        print("  ERROR ", e)
    for w in warns:
        print("  warn  ", w)
    if not errs:
        print("  script OK")
    return 1 if errs else 0


# ------------------------------------------------------------------ narrate

def cmd_narrate(a):
    st = load_story(a.story)
    from zds import narrate, story
    t = narrate.narrate(st, a.work, prefer=a.voice)
    plan = story.plan(st, t)
    total = sum(p["dur"] for p in plan)
    log(f"voice: {t['voice']}")
    if t["voice"].startswith("espeak"):
        log("WARNING: no neural voice installed — used the robotic espeak-ng fallback. "
            "Run scripts/setup.sh to get Kokoro (and Piper) from GitHub releases.")
    for p in plan:
        log(f"  {p['id']:<14} {p['dur']:5.2f}s  {len(p['words'])} words")
    log(f"total {total:.1f}s" + ("" if 25 <= total <= 50 else "  <-- outside 25-50s, adjust script/holds"))
    return 0


# ------------------------------------------------------------------ render helpers

def _run_shot(story_path, shot_id, work, mode, out, quality, res, frame=None):
    cmd = [sys.executable, "-m", "zds.render", story_path, shot_id, work, "--mode", mode,
           "--quality", quality, "--res", res, "--out", out]
    if frame:
        cmd += ["--frame", str(frame)]
    env = dict(os.environ, PYTHONPATH=HERE + os.pathsep + os.environ.get("PYTHONPATH", ""))
    r = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=HERE)
    if r.returncode != 0:
        tail = "\n".join(l for l in (r.stderr + r.stdout).splitlines()
                         if "EGL" not in l and "vulkan" not in l)[-3000:]
        raise RuntimeError(f"shot {shot_id} failed:\n{tail}")
    return out


def _need_timing(a):
    if not os.path.exists(os.path.join(a.work, "timing.json")):
        log("no timing.json yet — narrating first")
        cmd_narrate(a)


def draw_labels(im, path):
    """Draw the on-screen labels visible at the still frame (contact sheet preview)."""
    from PIL import ImageDraw, ImageFont
    if not os.path.exists(path):
        return
    with open(path) as fh:
        d = json.load(fh)
    fr = d.get("still_frame") or 1
    W, H = im.size
    dr = ImageDraw.Draw(im)
    for lb in d["labels"]:
        if lb["show"] > fr or (lb["hide"] and lb["hide"] <= fr):
            continue
        from zds.captions import fit_size
        px = max(8, fit_size(lb["text"], lb["size"], W, H))
        try:
            font = ImageFont.truetype(os.path.join(FONT_DIR, "Poppins-Bold.ttf"), px)
        except OSError:
            font = ImageFont.load_default()
        x = W / 2 + lb["pos"][0] * W
        y = H / 2 - lb["pos"][1] * H
        dr.text((x, y), lb["text"], font=font, fill=lb["color"], anchor="mm",
                stroke_width=max(1, px // 11) if lb["outline"] else 0,
                stroke_fill=lb["outline"] or lb["color"])


def cmd_sheet(a):
    _need_timing(a)
    st = load_story(a.story)
    from zds import story
    plan = {p["id"]: p for p in story.load_plan(st, a.work)}
    sdir = os.path.join(a.work, "stills")
    os.makedirs(sdir, exist_ok=True)
    ids = [s.id for s in st.SHOTS]
    t0 = time.time()
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        futs = {ex.submit(_run_shot, os.path.abspath(a.story), i, os.path.abspath(a.work), "still",
                          os.path.join(os.path.abspath(sdir), f"{i}.png"), "fast", "360x640"): i
                for i in ids}
        for f in cf.as_completed(futs):
            f.result()
    from PIL import Image, ImageDraw, ImageFont
    cols = min(4, len(ids))
    rows = (len(ids) + cols - 1) // cols
    W, Hh, cap = 360, 640, 90
    sheet = Image.new("RGB", (cols * W, rows * (Hh + cap)), (20, 20, 22))
    try:
        font = ImageFont.truetype(os.path.join(FONT_DIR, "Poppins-Bold.ttf"), 17)
    except OSError:
        font = ImageFont.load_default()
    dr = ImageDraw.Draw(sheet)
    for k, s in enumerate(st.SHOTS):
        x, y = (k % cols) * W, (k // cols) * (Hh + cap)
        im = Image.open(os.path.join(sdir, f"{s.id}.png")).convert("RGB")
        draw_labels(im, os.path.join(a.work, "labels", f"{s.id}.json"))
        sheet.paste(im, (x, y))
        dr.text((x + 8, y + Hh + 4), f"{k + 1}. {s.id}  ({plan[s.id]['dur']:.1f}s)", fill=(255, 220, 0), font=font)
        words, line, yy = s.line.split(), "", y + Hh + 26
        for w in words:
            if dr.textlength(line + " " + w, font=font) > W - 16:
                dr.text((x + 8, yy), line, fill=(235, 235, 235), font=font)
                yy += 20
                line = w
            else:
                line = (line + " " + w).strip()
        dr.text((x + 8, yy), line, fill=(235, 235, 235), font=font)
    out = os.path.join(a.work, "contact_sheet.png")
    sheet.save(out)
    log(f"contact sheet: {out}  ({time.time() - t0:.0f}s)")
    return 0


def cmd_render(a):
    _need_timing(a)
    st = load_story(a.story)
    ids = a.shots.split(",") if a.shots else [s.id for s in st.SHOTS]
    quality = "hq" if a.hq else "fast"
    res = a.res or "720x1280"
    sdir = os.path.join(a.work, "shots")
    os.makedirs(sdir, exist_ok=True)
    t0 = time.time()

    def one(i):
        fdir = os.path.join(os.path.abspath(a.work), "frames", i)
        shutil.rmtree(fdir, ignore_errors=True)
        ts = time.time()
        _run_shot(os.path.abspath(a.story), i, os.path.abspath(a.work), "frames", fdir, quality, res)
        mp4 = os.path.join(sdir, f"{i}.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(st.FPS),
                        "-i", os.path.join(fdir, "f_%04d.png"),
                        "-vf", f"scale={OUT_W}:{OUT_H}:flags=lanczos,format=yuv420p",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-r", str(st.FPS), mp4],
                       check=True)
        if not a.keep_frames:
            shutil.rmtree(fdir, ignore_errors=True)
        log(f"  rendered {i} in {time.time() - ts:.0f}s")
        return mp4

    with cf.ThreadPoolExecutor(a.jobs) as ex:
        for f in cf.as_completed([ex.submit(one, i) for i in ids]):
            f.result()
    log(f"render done in {time.time() - t0:.0f}s ({quality})")
    return 0


# ------------------------------------------------------------------ assemble

def _when(spec, p):
    """sfx time spec -> seconds from shot start."""
    if isinstance(spec, (int, float)):
        return float(spec) if spec >= 0 else p["dur"] + spec
    s = str(spec)
    if s.startswith("w"):
        i = int(s[1:])
        return p["words"][min(i, len(p["words"]) - 1)][1] if p["words"] else p["vo_start"]
    if s.startswith("end"):
        return p["dur"] + (float(s[3:]) if len(s) > 3 else -0.2)
    return float(s)


def build_audio(st, plan, work):
    import numpy as np
    from zds import audio as au
    total = sum(p["dur"] for p in plan)
    n = int(total * au.SR) + au.SR
    voice = np.zeros(n)
    fx = np.zeros(n)
    for k, p in enumerate(plan):
        if p["wav"] and os.path.exists(p["wav"]):
            au.place(voice, au.read_wav(p["wav"]), p["start"] + p["vo_start"])
        if k > 0:  # whoosh on every cut, peaking at the cut
            au.place(fx, au.sfx("whoosh"), p["start"] - 0.22, 0.55)
    shots = {s.id: s for s in st.SHOTS}
    for p in plan:
        for item in shots[p["id"]].sfx:
            name, when = item[0], item[1]
            gain = item[2] if len(item) > 2 else 0.8
            au.place(fx, au.sfx(name), p["start"] + _when(when, p), gain)
    music = au.suspense_bed(total + 1.0, bpm=getattr(st, "MUSIC_BPM", 84))[:n]
    music = np.pad(music, (0, n - len(music)))
    music *= au.duck_gain(voice, depth=0.7) * getattr(st, "MUSIC_GAIN", 0.32)
    mix = voice * 1.0 + fx * 0.6 + music
    mix = au.master(mix)[: int(total * au.SR)]
    out = os.path.join(work, "mix.wav")
    au.write_wav(out, mix)
    return out


def cmd_assemble(a):
    st = load_story(a.story)
    from zds import captions, story
    plan = story.load_plan(st, a.work)
    sdir = os.path.join(a.work, "shots")
    missing = [p["id"] for p in plan if not os.path.exists(os.path.join(sdir, p["id"] + ".mp4"))]
    if missing:
        log(f"missing shot videos: {missing} — run render first")
        return 1
    lst = os.path.join(a.work, "concat.txt")
    with open(lst, "w") as fh:
        for p in plan:
            fh.write(f"file '{os.path.abspath(os.path.join(sdir, p['id'] + '.mp4'))}'\n")
    log("mixing audio (voice + sfx + ducked music)")
    mix = build_audio(st, plan, a.work)
    ass = captions.build_ass(plan, os.path.join(a.work, "captions.ass"),
                             upper=getattr(st, "CAPTION_UPPER", True), work=a.work, fps=st.FPS)
    out = a.output or os.path.join(a.work, "final.mp4")
    vf = f"ass={ass}:fontsdir={FONT_DIR}" if not a.no_captions else "null"
    log("joining shots + burning captions")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-i", mix, "-vf", vf, "-map", "0:v", "-map", "1:a",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",  # platform loudness
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-r", str(st.FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height,r_frame_rate",
                         "-of", "json", out], capture_output=True, text=True)
    info = json.loads(pr.stdout)
    v = next(s for s in info["streams"] if "width" in s)
    log(f"final: {out}  {v['width']}x{v['height']} @ {v['r_frame_rate']}  "
        f"{float(info['format']['duration']):.1f}s")
    return 0


def cmd_voices(a):
    """Write one sample WAV per narrator voice so you can pick by ear."""
    from zds import narrate
    out = a.work or "voice_samples"
    os.makedirs(out, exist_ok=True)
    line = a.story_text or ("You pull on your finger, and your knuckle goes crack. "
                            "But what actually makes that sound?")
    made = []
    if narrate.find_kokoro():
        for vname, desc in narrate.KOKORO_VOICES.items():
            p = os.path.join(out, f"kokoro_{vname}.wav")
            narrate.Kokoro(vname).say(line, p)
            made.append((p, desc))
    if narrate.find_voice():
        p = os.path.join(out, "piper_ryan_high.wav")
        narrate.Piper(narrate.find_voice()).say(line, p)
        made.append((p, "Piper ryan-high"))
    if shutil.which("espeak-ng"):
        p = os.path.join(out, "espeak_fallback.wav")
        narrate.Espeak().say(line, p)
        made.append((p, "espeak-ng fallback (robotic)"))
    for p, d in made:
        log(f"  {p}  — {d}")
    log("pick one and set VOICE = \"<name>\" in the story (Kokoro names, e.g. am_fenrir)")
    return 0


def cmd_all(a):
    for step in (cmd_check, cmd_narrate, cmd_sheet, cmd_render, cmd_assemble):
        r = step(a)
        if r and step is cmd_check and not a.force:
            log("script check failed — fix the story (or pass --force)")
            return r
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["doctor", "voices", "check", "narrate", "sheet", "render",
                                    "assemble", "all"])
    ap.add_argument("story", nargs="?")
    ap.add_argument("-w", "--work")
    ap.add_argument("-o", "--output")
    ap.add_argument("-j", "--jobs", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    ap.add_argument("--shots", help="comma-separated shot ids (render only those)")
    ap.add_argument("--hq", action="store_true", help="Cycles instead of Workbench (slow)")
    ap.add_argument("--res", help="render resolution, default 720x1280 (upscaled to 1080x1920)")
    ap.add_argument("--voice", default="auto", choices=["auto", "kokoro", "piper", "espeak"])
    ap.add_argument("--text", dest="story_text", help="voices: sample sentence")
    ap.add_argument("--keep-frames", action="store_true")
    ap.add_argument("--no-captions", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.cmd == "doctor":
        sys.exit(cmd_doctor(a))
    if a.cmd == "voices":
        sys.exit(cmd_voices(a))
    if not a.story:
        ap.error("story file required")
    a.work = a.work or "work_" + os.path.splitext(os.path.basename(a.story))[0]
    os.makedirs(a.work, exist_ok=True)
    sys.exit({"check": cmd_check, "narrate": cmd_narrate, "sheet": cmd_sheet, "render": cmd_render,
              "assemble": cmd_assemble, "all": cmd_all}[a.cmd](a))


if __name__ == "__main__":
    main()
