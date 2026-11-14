# zds API reference

`from zds import *` gives everything below. Units are meters, angles degrees,
time in frames (30 fps) unless noted. The person stands on z=0 facing **-Y**, so
put cameras at negative Y. Colours: palette name, `(r, g, b)` linear, or `"#rrggbb"`.

Contents: 1 Story & Ctx · 2 Primitives · 3 Materials · 4 Animation · 5 Camera ·
6 Environments · 7 Person · 8 Hand · 9 Sound effects · 10 CLI

## 1. Story file and Ctx

```python
TITLE = "..."; FPS = 30
FACTS = [("claim", "source"), ...]          # required by `check`
MUSIC_GAIN = 0.32; MUSIC_BPM = 84           # optional
VOICE = "am_michael"; VOICE_SPEED = 1.1    # optional, Kokoro voice name + speed
CAPTION_UPPER = True                        # optional
SHOTS = [Shot(id, line, build, sfx=[], min_len=2.0, hold=0.35, still=None)]
```
- `sfx` items: `(name, when)` or `(name, when, gain)`; `when` = seconds from shot
  start, `"w3"` (start of word 3, 0-based), `"end"` / `"end-0.4"`.
- `hold`: seconds after the line before the cut (give the payoff ~1 s).
- `still`: time (s) of the contact-sheet frame (default 60% of the shot).

`Ctx` (the `c` passed to build functions):
| | |
|---|---|
| `c.frames`, `c.dur`, `c.fps` | shot length in frames / seconds |
| `c.f(t)` | seconds -> frame (negative = from the end) |
| `c.at("word", nth=0)` | frame where that word is spoken (case/punctuation-insensitive) |
| `c.wf(i)`, `c.w(i)`, `c.we(i)` | frame / start s / end s of word i |
| `c.vo_start`, `c.vo_end` | narration start/end (s) |
| `c.words` | list of (word, t0, t1) |

## 2. Primitives (all return the object; common kwargs `loc rot scale c m parent name`)

| function | notes |
|---|---|
| `ball(r)` | UV sphere |
| `capsule(r, length, axis="Z", offset=0)` | pill; `offset=-length/2` hangs it below its origin (limb on a joint) |
| `box(size=(x,y,z), bevel=0)` | rounded when bevel > 0 |
| `cylinder(r, depth, r2=None)` | `r2=0` makes a cone (arrow heads) |
| `blob(r, lump=0.18, freq=2.5, seed, spikes=0)` | lumpy organ/germ/rock/cloud; `spikes=12` = virus |
| `tube(points, r)` | pipe through points (veins, nerves, guts, wires); grow with `anim.grow` |
| `coil(center, radius, turns, height)` | point list for intestine-like tangles -> `tube(coil(...))` |
| `text3d(txt, size, outline="black", glow=2)` | extruded 3D text, faces -Y by default (rot 90,0,0) |
| `screen_text(cam, txt, pos=(0,0.32), size=0.06, c, outline, tilt)` | 2D label drawn in post, auto-fit width. `pos` = screen fractions (0,0 centre, y +0.5 top). Animate with `anim.pop_in/pop_out/show/hide` only |
| `scatter(make, n, center, size, seed, shape="box"/"sphere"/"disc", min_dist)` | calls `make(i, loc, rnd)` n times |
| `empty(name, loc, rot, parent)` | pivot / group |
| `aim(obj, direction, axis="Z")` | point an axis along a vector |
| `look_at(obj, target)` | point -Z at a target |

## 3. Materials

`mat(c, rough=0.5, metal=0, alpha=1, emit=0, unique=False)` — works in Workbench and
Cycles. `alpha<1` = see-through (x-ray skin ~0.2-0.3, capsules ~0.2, fluids ~0.3).
`emit>0` = glows in Cycles and is brightened in Workbench. Cached: pass
`unique=True` if you animate it (`anim.fade_alpha`). Palette names: skin skin_dark
shirt pants shoe hair bone cartilage blood muscle organ fluid gas germ nerve fat white
black yellow red green blue orange.

## 4. Animation (`anim.`)

| function | |
|---|---|
| `key(obj, path, frame, value, ease)` | generic; path e.g. `"location"`, `"rotation_euler"` (deg), `"scale"`, `"data.lens"` |
| `pop_in(obj, frame, dur=8, scale=None, ease="back")` / `pop_out(obj, frame, dur=6)` | springy appear/disappear |
| `show(obj, frame)` / `hide(obj, frame)` | hard cut visibility (children too) |
| `move(obj, f0, f1, to, frm=None)` · `rotate(obj, f0, f1, to)` · `scale_to(obj, f0, f1, to)` | |
| `spin(obj, f0, f1, axis="Z", turns=1)` | linear |
| `wobble(obj, f0, f1, amp, period)` | jelly squash/stretch |
| `pulse(obj, f0, f1, amp, period)` | heartbeat double pulse |
| `jitter(obj, f0, f1, amp, every)` | nervous shaking / fizzing |
| `grow(tube, f0, f1, start=0, end=1)` | tube grows along its length |
| `fade_alpha(material, f0, f1, a0, a1)` | |
| `follow_path(obj, points, f0, f1)` | |

`ease`: smooth (default), linear, snap, back, bounce, elastic, expo, sine, quad, cubic.
The ease is set on the *first* key of a segment.

## 5. Camera

`cam = Cam(loc, target, lens=40, dof=None)` — always looks at `cam.target`.
`cam.push(f0, f1, amount=0.35)` · `cam.dolly(f0, f1, to)` · `cam.track(f0, f1, to)` (move
the look-at point) · `cam.orbit(f0, f1, center, radius, height, a0, a1)` · `cam.zoom(f0, f1,
lens)` · `cam.shake(f0, f1, amp=0.05)` · `cam.drift(f0, f1, amp)` · `cam.set(frame, loc,
target, lens)`. Shake and drift both use the rig; don't overlap them in time.
Framing guide (lens 38): full person ≈ distance 4.2, waist-up ≈ 2.7, face ≈ 1.2.

## 6. Environments (`env.`)

`studio(c, z=0)` light sweep · `dark(z=0)` near-black · `medical(z=0, particles=40)` teal
with floating particles · `outdoor()` sky, grass, trees, clouds · `room()` floor, walls,
window, couch, rug, lamp · `inside_body()` red vessel tunnel with blood cells.
`z` = floor height; use `z=-1.8` for close-ups built around the origin.
`cyclorama(c, z)` for a custom backdrop; `set_world(rgb)` for the background colour.

## 7. Person

`p = Person(loc, rot_z=0, shirt, pants, skin, hair, shoes, xray=False, skin_alpha=0.22,
hands=True, scale=1, bald=False)`

- `p.pose(name_or_dict, frame, ease, base="stand", **joint_overrides)` — poses:
  stand relaxed t_pose arms_up wave point think shrug hands_front clutch_chest
  clutch_stomach facepalm hands_on_head sit crouch lying run_a.
  Overrides: `p.pose("stand", f, sh_L=(-30, -75, 0), head=(0, 0, 15))`.
- Joints: root hips spine chest neck head, sh/el/wr _L/_R, hip/kn/an _L/_R.
  Angles in left-side convention (same numbers mirror on _R). x<0 swings forward;
  sh y<0 raises the arm sideways; kn x>0 bends the knee; spine/head x>0 bends forward.
  `p.set_joint(name, frame, rot)`, `p.joint(name)` for the empty.
- `p.face(expr, frame)` — neutral happy smile sad shock scared pain worried angry
  smirk relief sick wince. `p.look(frame, dx, dz)`, `p.blink(frame)`.
- `p.talk(f0, f1)` mouth flaps · `p.walk(f0, f1, (x0,y0), (x1,y1), run=False)` ·
  `p.fall(f0, dur=18, direction="back")`.
- X-ray: `Person(xray=True)` shows bones (skull, spine, ribs, pelvis, limbs);
  `p.add_organs(["heart","lungs","brain","stomach","liver","intestines","bladder","kidneys"])`.
- Anchors (empties that follow the body): brain mouth eyes throat heart lung_L lung_R
  liver stomach intestines bladder kidneys spine_mid knee_L/R elbow_L/R hand_L/R foot_L/R.
  `obj.parent = p.anchor("stomach")` attaches a prop; `p.world("heart")` = world position.
- Hands: `p.hand_L` / `p.hand_R` are `Hand` objects (curl, interlock).

## 8. Hand (standalone, for close-ups)

`h = Hand(side="L", scale=5, xray=True, skin=mat(...,alpha=0.3), loc, rot=(0,180,0))` —
fingers point down by default; `rot=(0,180,0)` points them up, palm to camera.
`h.curl(frame, amount)` 0 flat .. 1 fist · `h.interlock(frame)` fingers bent back ·
`h.knuckles` (MCP joint empties), `h.fingers[i]` = [mcp, pip, dip], `h.thumb`.

## 9. Sound effects (numpy, `zds.audio`)

whoosh swoosh pop impact boom thud ding heartbeat rumble riser splat tick crack
sizzle glug bubble. `suspense_bed(dur)` music; `duck_gain(voice)` sidechain.
Add a new one by writing a function returning a mono float array at 44.1 kHz and
registering it in `audio.SFX`.

## 10. CLI (`scripts/make_short.py`)

`doctor` · `voices -w DIR [--text "..."]` (one sample per narrator voice) · `check STORY` ·
`narrate STORY -w WORK [--voice auto|kokoro|piper|espeak]` ·
`sheet STORY -w WORK` · `render STORY -w WORK [--shots a,b] [--hq] [--res 720x1280] [-j N]
[--keep-frames]` · `assemble STORY -w WORK [-o out.mp4] [--no-captions]` · `all ...`.
Work dir: `voice/*.wav`, `timing.json`, `stills/`, `contact_sheet.png`, `labels/*.json`,
`shots/*.mp4`, `mix.wav`, `captions.ass`, `final.mp4`.
Single-shot debugging: `cd scripts && python -m zds.render STORY ID WORK --mode still
--res 360x640 --frame 40 --out /tmp/x.png`.
