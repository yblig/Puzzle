"""Keyframe helpers. Frames are ints (use ctx.f(seconds) to convert)."""
import math
import random

import bpy
from mathutils import Vector

EASE = {"smooth": "BEZIER", "linear": "LINEAR", "snap": "CONSTANT", "back": "BACK",
        "bounce": "BOUNCE", "elastic": "ELASTIC", "expo": "EXPO", "sine": "SINE",
        "quad": "QUAD", "cubic": "CUBIC"}


def _interp(kind):
    bpy.context.preferences.edit.keyframe_new_interpolation_type = EASE.get(kind, kind)


def _is_label(obj):
    return obj.__class__.__name__ == "Label"


def key(obj, path, frame, value=None, ease="smooth", index=-1):
    """Set obj.<path> = value (if given) and keyframe it at frame.

    path: "location", "rotation_euler", "scale", "hide_render", or any
    animatable property path (e.g. data.lens, data.bevel_factor_end).
    Rotations are given in degrees when path == "rotation_euler".
    """
    if _is_label(obj):
        return
    target, attr = obj, path
    if "." in path:
        parts = path.split(".")
        for p in parts[:-1]:
            target = getattr(target, p)
        attr = parts[-1]
    if value is not None:
        if attr == "rotation_euler":
            value = [math.radians(v) for v in value]
        if attr == "scale" and isinstance(value, (int, float)):
            value = (value,) * 3
        if index >= 0:
            getattr(target, attr)[index] = value
        else:
            setattr(target, attr, value)
    _interp(ease)
    target.keyframe_insert(attr, frame=frame, index=index)
    _interp("smooth")


def show(obj, frame, recursive=True):
    """Make obj visible from frame on (render visibility is keyed, constant)."""
    _vis(obj, frame, False, recursive)


def hide(obj, frame, recursive=True):
    _vis(obj, frame, True, recursive)


def _vis(obj, frame, hidden, recursive):
    if _is_label(obj):
        if hidden:
            obj.hide = frame
        else:
            obj.show = frame
        return
    objs = [obj] + (list(obj.children_recursive) if recursive else [])
    for o in objs:
        o.hide_render = hidden
        o.keyframe_insert("hide_render", frame=frame)
        o.hide_viewport = hidden
        o.keyframe_insert("hide_viewport", frame=frame)


def pop_in(obj, frame, dur=8, scale=None, ease="back"):
    """Scale from 0 to its current (or given) scale with a springy overshoot."""
    if _is_label(obj):
        obj.show, obj.pop = frame, True
        return
    s = tuple(obj.scale) if scale is None else ((scale,) * 3 if isinstance(scale, (int, float)) else scale)
    key(obj, "scale", max(frame - 1, 0), (0.0001,) * 3, ease="snap")
    key(obj, "scale", frame, (0.0001,) * 3, ease=ease)
    key(obj, "scale", frame + dur, s)


def pop_out(obj, frame, dur=6):
    if _is_label(obj):
        obj.hide = frame + dur
        return
    key(obj, "scale", frame, tuple(obj.scale), ease="quad")
    key(obj, "scale", frame + dur, (0.0001,) * 3)


def move(obj, f0, f1, to, frm=None, ease="smooth"):
    """Move obj from frm (default: where it is) to `to` between f0 and f1."""
    if frm is not None:
        obj.location = frm
    key(obj, "location", f0, tuple(obj.location), ease=ease)
    key(obj, "location", f1, tuple(to))


def rotate(obj, f0, f1, to, frm=None, ease="smooth"):
    """Rotate to an (x, y, z) euler in degrees."""
    if frm is None:
        frm = [math.degrees(a) for a in obj.rotation_euler]
    key(obj, "rotation_euler", f0, frm, ease=ease)
    key(obj, "rotation_euler", f1, to)


def scale_to(obj, f0, f1, to, ease="smooth"):
    key(obj, "scale", f0, tuple(obj.scale), ease=ease)
    key(obj, "scale", f1, to)


def spin(obj, f0, f1, axis="Z", turns=1.0):
    """Constant-speed spin (linear keys)."""
    i = "XYZ".index(axis)
    r0 = list(obj.rotation_euler)
    obj.rotation_euler[i] = r0[i]
    _interp("linear")
    obj.keyframe_insert("rotation_euler", frame=f0, index=i)
    obj.rotation_euler[i] = r0[i] + turns * 2 * math.pi
    obj.keyframe_insert("rotation_euler", frame=f1, index=i)
    _interp("smooth")


def wobble(obj, f0, f1, amp=0.08, period=8, axis=None):
    """Jelly squash-and-stretch (keeps volume) — great for organs, blobs, germs.

    axis=None squashes Z vs XY; "X"/"Y"/"Z" picks the stretch axis.
    """
    if _is_label(obj):
        return
    base = Vector(obj.scale)
    i = "XYZ".index(axis or "Z")
    f, k = f0, 0
    while f <= f1:
        s = 1 + amp * math.sin(k * math.pi / 2)
        v = [b / math.sqrt(s) for b in base]
        v[i] = base[i] * s
        key(obj, "scale", f, v, ease="sine")
        f += max(1, period // 4)
        k += 1
    key(obj, "scale", f, tuple(base))


def pulse(obj, f0, f1, amp=0.15, period=20):
    """Heartbeat-like double pulse in scale."""
    if _is_label(obj):
        return
    base = Vector(obj.scale)
    f = f0
    while f < f1:
        for df, s in ((0, 1), (3, 1 + amp), (6, 1), (9, 1 + amp * 0.6), (13, 1)):
            key(obj, "scale", f + df, tuple(b * s for b in base), ease="quad")
        f += period


def jitter(obj, f0, f1, amp=0.02, every=2, seed=0, path="location"):
    """Random small offsets (nervous shaking, vibrating bubbles)."""
    rnd = random.Random(seed)
    base = Vector(getattr(obj, path))
    for f in range(f0, f1, every):
        key(obj, path, f, tuple(b + rnd.uniform(-amp, amp) for b in base), ease="linear")
    key(obj, path, f1, tuple(base))


def grow(obj, f0, f1, start=0.0, end=1.0, ease="smooth"):
    """Grow a tube()/curve along its length (veins spreading, intestines filling)."""
    obj.data.bevel_factor_mapping_end = "SPLINE"
    key(obj, "data.bevel_factor_end", f0, start, ease=ease)
    key(obj, "data.bevel_factor_end", f1, end)


def fade_alpha(material, f0, f1, a0, a1):
    """Fade a material's alpha (Workbench uses diffuse_color[3])."""
    material.diffuse_color[3] = a0
    material.keyframe_insert("diffuse_color", frame=f0, index=3)
    material.diffuse_color[3] = a1
    material.keyframe_insert("diffuse_color", frame=f1, index=3)


def follow_path(obj, points, f0, f1, ease="smooth"):
    """Move through a list of points with evenly spaced keys."""
    n = len(points)
    for i, p in enumerate(points):
        f = f0 + round((f1 - f0) * i / (n - 1))
        key(obj, "location", f, tuple(p), ease=ease)
