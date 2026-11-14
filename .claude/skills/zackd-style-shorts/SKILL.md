---
name: zackd-style-shorts
description: Turn a short topic or idea into a finished vertical MP4 (1080x1920, 30 fps, 25-50 s) 3D-animated explainer short in the style of Zack D Films (YouTube Shorts / TikTok / Reels). Writes the hook-first, second-person script with checked facts, builds and animates the 3D scenes in Blender (bpy, offline) with a posable cartoon person, x-ray body and organs, narrates with a natural neural voice (Kokoro, or Piper), generates the music and sound effects in numpy, and burns in word-by-word captions. Use this whenever someone asks for a Zack D / Zach D Films style video, a "what happens when you..." or "what happens inside your body" animated short, a 3D explainer short, a faceless animated YouTube Short from an idea, or an x-ray/body/science animated short, even if they only give a one-line topic and never mention Blender.
---

# Zack-D-style 3D explainer shorts

You turn a topic ("what happens when you crack your knuckles") into a finished
vertical video: a 25-50 second 3D explainer with a narrator speaking to "you",
dramatic close-ups (often x-ray views inside the body), punchy sound effects, a
tense music bed and big word-by-word captions. Everything runs offline in Python.

## What makes the style (keep these in mind for every decision)

- **Hook first.** Line one *is* the event ("You swallow a piece of gum."). No
  greeting, no "have you ever wondered", no title card.
- **"You" are the subject**, in the present tense: the viewer is the person on screen.
- **One idea per line, one line per shot.** A new picture every 2-5 seconds, each
  cut marked by a whoosh. 7-12 shots, 70-120 words.
- **Show, inside.** The camera goes where you can't: x-ray skin, cutaway joints,
  inside a vessel. Simple, saturated, toy-like 3D; clear labels on screen.
- **Escalate, then pay off.** Build tension (music, heartbeat, rumble), end on a
  twist, a myth-bust or a satisfying answer — not a summary or "like and subscribe".
- **True.** Every claim is checked. These videos travel; a wrong "fact" is the
  fastest way to lose trust. Keep a `FACTS` list with sources in the story file.

More detail and examples: `references/style-guide.md`.

## Setup (once per machine — and once per Claude Code cloud session)

Cloud sessions (claude.ai/code, the Claude app) start in a fresh container, so run
`doctor` first and, if anything is missing, `setup.sh` (about 3-5 minutes; it installs
packages and downloads ~470 MB of voice models from GitHub).

```bash
bash <skill>/scripts/setup.sh        # pip bpy kokoro-onnx piper-tts ...; apt ffmpeg, EGL; voice models
python <skill>/scripts/make_short.py doctor
```

`doctor` lists anything missing. Notes:
- **Voice.** Narration uses the first engine installed: **Kokoro** (natural neural
  voice, default `am_michael`; exact word timing) -> **Piper** `en_US-ryan-high` ->
  espeak-ng (robotic, last resort). setup.sh downloads Kokoro and Piper from GitHub
  releases (~470 MB in `~/.cache/zds`). If only espeak-ng ended up available, say so
  plainly to the user; it sounds stiff and is not good enough to publish.
- **Picking a voice.** `make_short.py voices -w samples/` writes a short WAV per
  narrator voice (am_michael, am_fenrir, am_puck, am_onyx, bm_george, af_heart, Piper).
  Set `VOICE = "am_fenrir"` and optionally `VOICE_SPEED = 1.1` in the story file.
  Use the user's choice if they gave one; otherwise am_michael.
- Workbench needs EGL (`libegl1 libegl-mesa0 libgl1-mesa-dri`); on a headless box
  Mesa's software renderer works. The "EGL_BAD_MATCH" lines in logs are harmless.

## Workflow

Work in a folder of your choice; `WORK` holds every intermediate file.

1. **Research + script.** Look the topic up (web search if available) and write
   7-12 lines following the rules above. Note each claim with its source.
2. **Story file.** Write `STORY.py` (copy the structure of `examples/knuckles.py`):
   `TITLE`, `FACTS`, and `SHOTS = [Shot(id, line, build_fn, sfx=[...], min_len, hold)]`.
   Each `build_fn(ctx)` builds and animates one shot with the `zds` helpers.
   Run `python scripts/make_short.py check STORY.py` — it enforces the script rules.
3. **Narrate.** `make_short.py narrate STORY.py -w WORK` -> one WAV per shot and
   per-word timing (it prints which voice it used). Shot length = narration + hold (or `min_len`). Check the printed
   total is 25-50 s; trim lines or holds if not.
4. **Contact sheet.** `make_short.py sheet STORY.py -w WORK` renders one small
   still per shot into `WORK/contact_sheet.png` (about 10 s). **Look at it** (open
   the image) before the full render: subject cut off, floor slicing through
   objects, labels overflowing, a dark unreadable frame — fix them now, it costs
   seconds here and many minutes later. Pass `still=` on a Shot to pick its frame.
5. **Render.** `make_short.py render STORY.py -w WORK -j 4` -> one MP4 per shot
   (Workbench at 720x1280, upscaled to 1080x1920). Re-render single shots with
   `--shots id1,id2`. `--hq` switches to Cycles (much slower; only when asked).
6. **Assemble.** `make_short.py assemble STORY.py -w WORK` joins the shots, mixes
   voice + sound effects + music that ducks under the voice, and burns in the
   captions and on-screen labels -> `WORK/final.mp4`.
7. **Verify** (don't skip): extract 3-4 frames from `final.mp4` with ffmpeg and
   look at them (captions legible, labels on screen), and check `ffprobe` says
   1080x1920, 30 fps, 25-50 s. Then hand over the video.

`make_short.py all STORY.py -w WORK` runs check -> narrate -> sheet -> render ->
assemble in one go, but the contact-sheet review in step 4 is where most quality
comes from, so prefer the separate steps for a new story.

Timing on a 4-core CPU box: contact sheet ~10 s; full render ~1-2 s per frame per
job (a 40 s video is ~1200 frames, roughly 15-30 min with `-j 4`). Run long renders
in the background and keep working (or report progress) meanwhile.

## Writing build functions

```python
from zds import *   # ball capsule box cylinder blob tube coil text3d screen_text scatter
                    # mat aim empty anim env Cam Person Hand Shot

def s_hook(c):                       # c = Ctx for this shot
    env.studio()                     # or dark / medical / outdoor / room / inside_body
    p = Person(shirt="#2f6fd6")      # posable cartoon person, faces the camera (-Y)
    p.pose("hands_front", 1); p.face("smirk", 1)
    cam = Cam(loc=(0.5, -2.7, 1.4), target=(0, 0, 1.2), lens=38)
    cam.push(1, c.frames, 0.25)      # slow push-in: almost every shot should move
    k = c.at("crack")                # frame where the word "crack" is spoken
    p.face("wince", k); cam.shake(k, k + 12)
    lab = screen_text(cam, "CRACK!", pos=(0, 0.3), size=0.11, c="yellow", tilt=-8)
    anim.pop_in(lab, k)

SHOTS = [Shot("hook", "You pull on your finger, and your knuckle goes crack.", s_hook,
              sfx=[("crack", "w9"), ("impact", "w9", 0.5)])]
```

The full API (every helper, its arguments, pose and expression names, anchors,
environments, sound effect names) is in `references/api.md`. Read it before
writing a story. Things that matter most:

- **Sync to words**: `c.at("word")` / `c.wf(i)` give frames; sfx accept `"w3"`
  (word index), seconds, or `"end-0.4"`.
- **Floor**: environments put the floor at z=0. For floating close-ups (organs,
  joints, cells built around the origin) use `env.medical(z=-1.8)` so the floor
  doesn't cut through them.
- **On-screen text**: `screen_text()` is drawn in post (sharp, bright, auto-fit to
  width). Keep it in the top two thirds; captions own the lower third. Use
  `text3d()` only for text that belongs in the 3D world.
- **x-ray**: `Person(xray=True)` + `p.add_organs([...])`, or `Hand(xray=True)`;
  use `p.anchor("heart")` to attach your own props so they follow the body.
- **Animated materials** (fades) need `mat(..., unique=True)`.
- Every shot should move: a push, orbit, drift or shake. A dead-still frame reads
  as a slideshow.

## Deliver

Give the user `final.mp4`, the story file, and a one-line summary (length, shot
count, voice used). If the espeak fallback voice was used, say so plainly.
