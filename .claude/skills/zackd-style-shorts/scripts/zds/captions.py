"""Word-by-word captions as an ASS subtitle file (burned in with ffmpeg/libass).

Poppins Bold, white with a thick black outline, the word being spoken in yellow
with a small pop. Words are grouped into short chunks (max 3 words, breaking at
punctuation) like typical shorts captions.
"""
import json
import os
import re


def _ts(t):
    t = max(0.0, t)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def chunks(words, max_words=3, max_chars=16):
    out, cur = [], []
    for w in words:
        cur.append(w)
        text = " ".join(x[0] for x in cur)
        if len(cur) >= max_words or len(text) >= max_chars or re.search(r"[,.;:!?]$", w[0]):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def fit_size(text, size, W, H, char_w=0.68, max_frac=0.9):
    """Font px for a label: cap height = size*H, shrunk so the widest line fits 90% of W."""
    fs = size * H / 0.72
    longest = max((len(l) for l in text.split("\n")), default=1)
    return int(min(fs, max_frac * W / (char_w * max(1, longest))))


def _ass_color(hexrgb):
    h = hexrgb.lstrip("#")
    return f"&H{h[4:6]}{h[2:4]}{h[0:2]}&".upper()


def label_events(plan, work, fps):
    """ASS events for on-screen labels recorded by screen_text() during rendering."""
    out = []
    for shot in plan:
        p = os.path.join(work, "labels", shot["id"] + ".json")
        if not os.path.exists(p):
            continue
        with open(p) as fh:
            labels = json.load(fh)["labels"]
        for lb in labels:
            a = shot["start"] + (lb["show"] - 1) / fps
            b = shot["start"] + ((lb["hide"] - 1) / fps if lb["hide"] else shot["dur"])
            x = int(540 + lb["pos"][0] * 1080)
            y = int(960 - lb["pos"][1] * 1920)
            fs = fit_size(lb["text"], lb["size"], 1080, 1920)
            tags = f"\\an5\\pos({x},{y})\\fs{fs}\\c{_ass_color(lb['color'])}"
            if lb["outline"]:
                tags += f"\\3c{_ass_color(lb['outline'])}\\bord{max(4, fs // 11)}"
            else:
                tags += "\\bord0"
            if lb.get("tilt"):
                tags += f"\\frz{-lb['tilt']}"
            if lb["pop"]:
                tags += "\\fscx0\\fscy0\\t(0,110,\\fscx118\\fscy118)\\t(110,200,\\fscx100\\fscy100)"
            txt = lb["text"].replace("{", "(").replace("}", ")").replace("\n", "\\N")
            out.append(f"Dialogue: 1,{_ts(a)},{_ts(b)},Label,,0,0,0,,{{{tags}}}{txt}")
    return out


def build_ass(plan, path, upper=True, font="Poppins", size=96, y_frac=0.70, max_words=3,
              work=None, fps=30):
    """plan: list of shot dicts (start, words) from story.plan()."""
    margin_v = int(1920 * (1 - y_frac))
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{font},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,-1,0,0,0,100,100,1,0,1,8,4,2,60,60,{margin_v},1
Style: Label,{font},80,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,-1,0,0,0,100,100,1,0,1,7,3,5,40,40,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    all_chunks = []  # (chunk, shot_end) across the whole video, in time order
    for shot in plan:
        ws = [(w, shot["start"] + a, shot["start"] + b) for w, a, b in shot["words"]]
        all_chunks += [(ch, shot["start"] + shot["dur"]) for ch in chunks(ws, max_words)]
    for k, (ch, shot_end) in enumerate(all_chunks):
        nxt = all_chunks[k + 1][0][0][1] if k + 1 < len(all_chunks) else shot_end
        for i, (w, a, b) in enumerate(ch):
            # never overlap the next word/chunk: one caption on screen at a time
            end = ch[i + 1][1] if i + 1 < len(ch) else min(b + 0.25, shot_end, nxt)
            a = round(a, 2)
            end = max(a + 0.04, round(end, 2))
            parts = []
            for j, (w2, _, _) in enumerate(ch):
                t = w2.upper() if upper else w2
                t = t.replace("{", "(").replace("}", ")")
                if j == i:
                    parts.append("{\\c&H00E5FF&\\fscx112\\fscy112\\t(0,90,\\fscx100\\fscy100)}"
                                 + t + "{\\c&HFFFFFF&\\fscx100\\fscy100}")
                else:
                    parts.append(t)
            lines.append(f"Dialogue: 0,{_ts(a)},{_ts(end)},Cap,,0,0,0,,{' '.join(parts)}")
    if work:
        lines += label_events(plan, work, fps)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(head + "\n".join(lines) + "\n")
    return path
