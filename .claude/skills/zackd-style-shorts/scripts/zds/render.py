"""Render one shot in a fresh Blender scene (run as a subprocess by make_short.py).

python -m zds.render STORY SHOT_ID WORK --mode frames|still [--quality fast|hq]
       [--res 720x1280] [--out DIR_OR_PNG]
"""
import argparse
import os
import sys
import time


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("story")
    ap.add_argument("shot")
    ap.add_argument("work")
    ap.add_argument("--mode", default="frames", choices=["frames", "still"])
    ap.add_argument("--quality", default="fast", choices=["fast", "hq"])
    ap.add_argument("--res", default="720x1280")
    ap.add_argument("--out", required=True)
    ap.add_argument("--frame", type=int, default=None)
    a = ap.parse_args(argv)

    import bpy
    from zds import core, story as st

    story = st.load(a.story)
    plan = {p["id"]: p for p in st.load_plan(story, a.work)}
    shot = next(s for s in story.SHOTS if s.id == a.shot)
    p = plan[shot.id]
    res = tuple(int(v) for v in a.res.lower().split("x"))
    sc = core.reset(fps=story.FPS, res=res, quality=a.quality)
    ctx = st.Ctx(shot, p, story.FPS, a.quality)
    t = time.time()
    shot.build(ctx)
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, p["frames"]
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    fr = None
    if a.mode == "still":
        fr = a.frame or ctx.f(shot.still if shot.still is not None else p["dur"] * 0.6)
        sc.frame_set(fr)
        sc.render.filepath = a.out
        bpy.ops.render.render(write_still=True)
    else:
        os.makedirs(a.out, exist_ok=True)
        sc.render.filepath = os.path.join(a.out, "f_####")
        bpy.ops.render.render(animation=True)
    import json
    os.makedirs(os.path.join(a.work, "labels"), exist_ok=True)
    with open(os.path.join(a.work, "labels", f"{shot.id}.json"), "w") as fh:
        json.dump({"still_frame": fr if a.mode == "still" else None,
                   "labels": [l.as_dict() for l in core.LABELS]}, fh)
    print(f"[zds] {shot.id}: built+rendered in {time.time() - t:.1f}s", file=sys.stderr)


if __name__ == "__main__":
    main()
