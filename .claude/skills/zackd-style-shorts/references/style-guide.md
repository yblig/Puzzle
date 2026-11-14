# Style guide: Zack-D-style explainer shorts

What the format is, as described by creators and freelancers who make it (there
is no official write-up from Zack D Films): short vertical 3D animations, mostly
"what happens when..." and "what happens inside your body" scenarios, smooth
camera motion, cinematic lighting, x-ray / cutaway views, quick zooms, fast
second-person narration, 30-60 seconds. Ours: 25-50 s.

## Script rules (enforced by `make_short.py check`)

| Rule | Why |
|---|---|
| Line 1 is the hook — the event itself, no greeting | Viewers decide in ~1 s whether to swipe |
| Second person ("you"), present tense | Puts the viewer in the body on screen |
| One idea per line, one line per shot | Each picture explains one thing; cuts keep pace |
| 7-12 shots, 70-120 words | ≈ 25-50 s at a brisk narration pace |
| Ends on a payoff / myth-bust / twist | The last line is what gets the share and rewatch |
| Every claim checked, listed in `FACTS` with a source | Wrong facts get called out in comments |

### Hooks that work
- Start mid-action: "You swallow a piece of gum." / "You pull on your finger, and your knuckle goes crack."
- Start with a stake: "You have about three minutes after this happens."
- Avoid: "Have you ever wondered...", "Today we're looking at...", "Did you know...".

### Story shape (typical 10 shots)
1. Hook — the moment, on a person (exterior).
2. Go inside — x-ray / cutaway, name the part ("Inside, the joint sits in a capsule...").
3-6. The mechanism, one step per shot, each with a visual change you can see
    (gap widens, bubble forms, cells rush in). Escalate music/sfx.
7. A turn — "Try it again, and nothing happens." / "But here's the problem."
8-9. Consequence or the common belief ("Everyone says it gives you arthritis.").
10. Payoff — the surprising truth, short and punchy ("Neither hand has arthritis. Crack away.").

### Line writing
- 6-14 words per line. Short words. Numbers spelled the way they're said ("twenty minutes").
- Put the key word near the end of the line: that's where the visual beat lands
  (use `c.at("word")` to time it).
- Hedge only where the science is unsettled, and do it in plain words ("probably", "scientists think").

## Visual grammar

- **Every shot moves**: slow push-in (`cam.push`), orbit, dolly, or at least `cam.drift`.
- **Beats on words**: a pop-in, shake, zoom punch or expression change on the key word.
- **Exterior -> interior**: alternate shots of the person with x-ray/cutaway close-ups.
- **Colour coding**: bone cream, cartilage pale blue, fluid pale yellow, blood/inflammation
  red, gas/air white, germs green, nerves yellow. Dark teal (`env.medical`) for "inside",
  light grey studio for the person, near-black (`env.dark`) for drama and the big reveal.
- **Labels**: 1-3 words, caps, top third (`screen_text(..., pos=(0, 0.3..0.4))`). Big single
  words ("POP!", "CRACK!") with a small tilt for impact beats.
- **Captions**: lower third, 1-3 words at a time, current word yellow — handled automatically.

## Sound

- Whoosh on every cut (automatic). One sfx per beat, not a constant barrage.
- Music: suspense bed (drone + sub pulse + plucks + ticks) ducked under the voice;
  `MUSIC_GAIN` / `MUSIC_BPM` at module level in the story tune it.
- Sfx vocabulary: whoosh, pop, impact (=boom/thud), ding, heartbeat, rumble, riser,
  splat, tick, crack, sizzle, glug, bubble.
  - crack: bones/knuckles; pop: bubbles, things appearing; impact: reveals and hits;
    riser: tension before a reveal; heartbeat: danger/fear; ding: a fact lands / the payoff;
    sizzle: fizz, burning, acid; glug/bubble: liquid; splat: gross reveals; tick: time passing.
