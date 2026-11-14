"""Scene setup, materials and primitive builders for zds shorts.

Everything here works in the Workbench engine (fast previews and default renders)
and in Cycles (optional high quality). Materials set both the Workbench viewport
colour and a Principled BSDF so the same story renders in either engine.
"""
import math
import os
import random

import bmesh
import bpy
from mathutils import Vector

FONT_DIRS = [
    os.environ.get("ZDS_FONT_DIR", ""),
    os.path.expanduser("~/.cache/zds"),
    os.path.join(os.path.dirname(__file__), "..", "..", "assets"),
]

# A small, saturated palette that reads well in Workbench (linear RGB).
PALETTE = {
    "skin": (0.80, 0.50, 0.36),
    "skin_dark": (0.45, 0.25, 0.16),
    "shirt": (0.10, 0.32, 0.75),
    "pants": (0.12, 0.12, 0.16),
    "shoe": (0.05, 0.05, 0.06),
    "hair": (0.10, 0.06, 0.03),
    "bone": (0.92, 0.88, 0.78),
    "cartilage": (0.70, 0.85, 0.95),
    "blood": (0.65, 0.02, 0.02),
    "muscle": (0.60, 0.08, 0.08),
    "organ": (0.85, 0.35, 0.40),
    "fluid": (0.55, 0.85, 1.00),
    "gas": (0.95, 0.98, 1.00),
    "germ": (0.25, 0.75, 0.15),
    "nerve": (1.00, 0.85, 0.20),
    "fat": (1.00, 0.85, 0.45),
    "white": (0.95, 0.95, 0.95),
    "black": (0.01, 0.01, 0.01),
    "yellow": (1.00, 0.80, 0.02),
    "red": (0.85, 0.03, 0.03),
    "green": (0.10, 0.65, 0.12),
    "blue": (0.05, 0.25, 0.90),
    "orange": (1.00, 0.35, 0.02),
}

_MAT_CACHE = {}
STATE = {"quality": "fast"}


def color(c):
    """Accept a palette name, an (r,g,b) tuple or a '#rrggbb' hex string."""
    if isinstance(c, str):
        if c.startswith("#"):
            h = c.lstrip("#")
            srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
            return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in srgb)
        return PALETTE[c]
    return tuple(c[:3])


# ---------------------------------------------------------------- scene setup

def reset(fps=30, res=(720, 1280), quality="fast"):
    """Start an empty scene and configure the render engine.

    quality="fast"  -> Workbench (seconds per shot), the default.
    quality="hq"    -> Cycles with denoising (minutes per shot).
    """
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _MAT_CACHE.clear()
    LABELS.clear()
    STATE["quality"] = quality
    sc = bpy.context.scene
    sc.render.fps = fps
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "Standard"
    try:
        sc.view_settings.look = "Medium High Contrast"
    except TypeError:
        pass
    world = bpy.data.worlds.new("World")
    sc.world = world
    world.color = (0.8, 0.8, 0.8)
    if quality == "hq":
        sc.render.engine = "CYCLES"
        sc.cycles.device = "CPU"
        sc.cycles.samples = int(os.environ.get("ZDS_CYCLES_SAMPLES", "48"))
        sc.cycles.use_denoising = True
        sc.cycles.max_bounces = 6
        sc.render.film_transparent = False
    else:
        sc.render.engine = "BLENDER_WORKBENCH"
        d = sc.display
        try:
            d.render_aa = "8"
        except TypeError:
            pass
        sh = d.shading
        sh.light = "STUDIO"
        sh.studio_light = "studio.sl"
        sh.color_type = "MATERIAL"
        sh.background_type = "WORLD"
        sh.show_shadows = True
        sh.shadow_intensity = 0.45
        sh.show_cavity = True
        sh.cavity_type = "BOTH"
        sh.cavity_ridge_factor = 0.6
        sh.cavity_valley_factor = 1.0
        sh.show_specular_highlight = True
        sh.show_object_outline = False
        d.light_direction = (0.45, -0.55, 0.70)
        d.shadow_shift = 0.05
        d.shadow_focus = 0.6
    return sc


def set_world(rgb, strength=1.0):
    """Background colour for both engines."""
    w = bpy.context.scene.world
    rgb = color(rgb)
    w.color = rgb
    if STATE["quality"] == "hq":
        if hasattr(w, "use_nodes"):
            try:
                w.use_nodes = True
            except Exception:
                pass
        if w.node_tree:
            bg = w.node_tree.nodes.get("Background")
            if bg:
                bg.inputs["Color"].default_value = (*rgb, 1)
                bg.inputs["Strength"].default_value = strength


def light_rig(kind="studio"):
    """Workbench studio-light preset + matching real lights for Cycles."""
    sc = bpy.context.scene
    presets = {"studio": "studio.sl", "rim": "rim.sl", "outdoor": "outdoor.sl",
               "paint": "paint.sl", "basic": "basic.sl"}
    if sc.render.engine == "BLENDER_WORKBENCH":
        sc.display.shading.studio_light = presets.get(kind, "studio.sl")
        return
    def add(name, ltype, energy, loc, rot, size=4, rgb=(1, 1, 1)):
        ld = bpy.data.lights.new(name, ltype)
        ld.energy = energy
        ld.color = rgb
        if ltype == "AREA":
            ld.size = size
        o = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(o)
        o.location = loc
        o.rotation_euler = [math.radians(a) for a in rot]
        return o
    add("key", "AREA", 900, (3, -4, 5), (50, 0, 35), 4)
    add("fill", "AREA", 300, (-4, -3, 3), (65, 0, -50), 6, (0.8, 0.9, 1))
    add("rim", "AREA", 700, (0, 5, 4), (-55, 0, 180), 3)
    if kind == "outdoor":
        add("sun", "SUN", 4, (0, 0, 10), (40, 10, 30))


# ---------------------------------------------------------------- materials

def mat(c="white", rough=0.5, metal=0.0, alpha=1.0, emit=0.0, name=None, unique=False):
    """Material that looks the same in Workbench and Cycles. Cached by args.

    unique=True always makes a new material (needed when you animate it, e.g. fades).
    """
    rgb = color(c)
    key = (rgb, rough, metal, alpha, emit) if not unique else object()
    if key in _MAT_CACHE:
        return _MAT_CACHE[key]
    m = bpy.data.materials.new(name or "m%d" % len(_MAT_CACHE))
    # Workbench has no emission: brighten the viewport colour instead so "glowing"
    # things (labels, sparks, inflamed spots) still pop.
    boost = 1 + 0.35 * emit
    m.diffuse_color = (*(v * boost for v in rgb), alpha)
    m.roughness = rough
    m.metallic = metal
    if alpha < 1:
        m.surface_render_method = "BLENDED"
        try:
            m.use_backface_culling = False
            m.show_transparent_back = False  # avoids sorting artefacts on x-ray skin
        except AttributeError:
            pass
    if STATE["quality"] == "hq":
        if m.node_tree is None and hasattr(m, "use_nodes"):
            m.use_nodes = True
        nt = m.node_tree
        if nt:
            p = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
            if p:
                p.inputs["Base Color"].default_value = (*rgb, 1)
                p.inputs["Roughness"].default_value = rough
                p.inputs["Metallic"].default_value = metal
                p.inputs["Alpha"].default_value = alpha
                if emit:
                    p.inputs["Emission Color"].default_value = (*rgb, 1)
                    p.inputs["Emission Strength"].default_value = emit
                if "Subsurface Weight" in p.inputs and c in ("skin", "organ", "muscle"):
                    p.inputs["Subsurface Weight"].default_value = 0.15
    if not unique:
        _MAT_CACHE[key] = m
    return m


def set_mat(obj, m):
    if obj.data is not None and hasattr(obj.data, "materials"):
        obj.data.materials.clear()
        obj.data.materials.append(m)
    return obj


# ---------------------------------------------------------------- objects

def link(obj, parent=None):
    bpy.context.scene.collection.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


def empty(name="empty", loc=(0, 0, 0), rot=(0, 0, 0), parent=None, size=0.1):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = size
    link(e, parent)
    e.location = loc
    e.rotation_euler = [math.radians(a) for a in rot]
    return e


def _finish(name, bm, loc, rot, scale, c, m, parent, smooth):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    o = bpy.data.objects.new(name, me)
    link(o, parent)
    o.location = loc
    o.rotation_euler = [math.radians(a) for a in rot]
    o.scale = (scale,) * 3 if isinstance(scale, (int, float)) else scale
    set_mat(o, m if m is not None else mat(c))
    return o


def ball(r=0.5, loc=(0, 0, 0), c="white", m=None, rot=(0, 0, 0), scale=1, parent=None,
         name="ball", seg=32):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r)
    return _finish(name, bm, loc, rot, scale, c, m, parent, True)


def capsule(r=0.2, length=1.0, loc=(0, 0, 0), c="white", m=None, rot=(0, 0, 0), scale=1,
            parent=None, name="capsule", axis="Z", offset=0.0, seg=24):
    """Pill shape along Z (length = straight middle part, total = length + 2r).

    offset shifts the geometry along the axis, e.g. offset=-length/2 makes a limb
    that hangs below its origin (handy when the origin is a joint).
    """
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2 + 1, radius=r)
    half = length / 2
    for v in bm.verts:
        v.co.z += (half if v.co.z > 1e-6 else -half if v.co.z < -1e-6 else 0) + offset
    if axis == "X":
        bmesh.ops.rotate(bm, verts=bm.verts, matrix=_rot_matrix("Y", 90))
    elif axis == "Y":
        bmesh.ops.rotate(bm, verts=bm.verts, matrix=_rot_matrix("X", 90))
    return _finish(name, bm, loc, rot, scale, c, m, parent, True)


def box(size=(1, 1, 1), loc=(0, 0, 0), c="white", m=None, rot=(0, 0, 0), bevel=0.0,
        parent=None, name="box", offset=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0] + offset[0], v.co.y * size[1] + offset[1],
                       v.co.z * size[2] + offset[2]))
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges) + list(bm.verts), offset=bevel,
                        segments=3, affect="EDGES", profile=0.5)
    o = _finish(name, bm, loc, rot, 1, c, m, parent, bevel > 0)
    return o


def cylinder(r=0.5, depth=1.0, loc=(0, 0, 0), c="white", m=None, rot=(0, 0, 0), r2=None,
             parent=None, name="cylinder", seg=32, offset=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r,
                          radius2=r if r2 is None else r2, depth=depth)
    for v in bm.verts:
        v.co.z += offset
    o = _finish(name, bm, loc, rot, 1, c, m, parent, True)
    # flat caps, smooth sides
    for p in o.data.polygons:
        if abs(p.normal.z) > 0.99:
            p.use_smooth = False
    return o


def blob(r=0.5, loc=(0, 0, 0), c="organ", m=None, lump=0.18, freq=2.5, seed=0,
         rot=(0, 0, 0), scale=1, parent=None, name="blob", subdiv=4, spikes=0, spike_len=0.35):
    """Lumpy organic shape: organs, germs, cells, rocks, clouds.

    lump  = how bumpy (0 = sphere), freq = how many bumps.
    spikes > 0 adds that many little spikes (viruses / germs).
    """
    rnd = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    waves = [(Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized(),
              rnd.uniform(0.6, 1.4) * freq, rnd.uniform(0, 6.28)) for _ in range(6)]
    for v in bm.verts:
        n = v.co.normalized()
        d = sum(math.sin(k * n.dot(a) * 3.0 + ph) for a, k, ph in waves) / len(waves)
        v.co = n * r * (1 + lump * d)
    o = _finish(name, bm, loc, rot, scale, c, m, parent, True)
    for i in range(spikes):
        u = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized()
        s = capsule(r * 0.07, r * spike_len, loc=u * r * (1 + spike_len / 2), c=c, m=m,
                    parent=o, name=name + "_spike", seg=10)
        s.rotation_mode = "QUATERNION"
        s.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(u)
        ball(r * 0.12, loc=u * r * (1 + spike_len), c=c, m=m, parent=o, seg=10)
    return o


def tube(points, r=0.05, c="blood", m=None, parent=None, name="tube", smooth=True,
         caps=True, res=4):
    """A pipe through 3D points: veins, nerves, intestines, cables, straws.

    Animate growth with anim.grow(tube, f0, f1). Bezier with auto handles
    when smooth=True so a few points give a soft curve.
    """
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = res
    cu.use_fill_caps = caps
    if smooth:
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(len(points) - 1)
        for bp, p in zip(sp.bezier_points, points):
            bp.co = p
            bp.handle_left_type = bp.handle_right_type = "AUTO"
    else:
        sp = cu.splines.new("POLY")
        sp.points.add(len(points) - 1)
        for pt, p in zip(sp.points, points):
            pt.co = (*p, 1)
    o = bpy.data.objects.new(name, cu)
    link(o, parent)
    set_mat(o, m if m is not None else mat(c))
    return o


def coil(center=(0, 0, 0), radius=0.3, turns=4, height=0.5, wiggle=0.06, n=80, seed=1):
    """Point list for a tangled, intestine-like coil (feed it to tube())."""
    rnd = random.Random(seed)
    pts = []
    for i in range(n):
        t = i / (n - 1)
        a = t * turns * 2 * math.pi
        rr = radius * (0.55 + 0.45 * math.sin(a * 0.5 + 1.0))
        pts.append((center[0] + rr * math.cos(a) + rnd.uniform(-wiggle, wiggle),
                    center[1] + rnd.uniform(-wiggle, wiggle) * 0.5,
                    center[2] + height * (0.5 - t) + rr * 0.35 * math.sin(a)))
    return pts


def _font():
    if "zds_font" in bpy.data.fonts:
        return bpy.data.fonts["zds_font"]
    for d in FONT_DIRS:
        p = os.path.join(d, "Poppins-Bold.ttf") if d else ""
        if p and os.path.exists(p):
            f = bpy.data.fonts.load(p)
            f.name = "zds_font"
            return f
    return None


def text3d(txt, size=0.5, loc=(0, 0, 0), rot=(90, 0, 0), c="white", m=None, extrude=0.06,
           parent=None, name="text", align="CENTER", bevel=0.01, outline=None, glow=2.0):
    """3D extruded text. Default rotation stands it up facing -Y (the camera).

    outline="black" adds a thicker dark copy behind for readability.
    """
    def make(nm, off, mm, z):
        cu = bpy.data.curves.new(nm, "FONT")
        cu.body = txt
        f = _font()
        if f:
            cu.font = f
        cu.size = size
        cu.extrude = extrude
        cu.bevel_depth = bevel
        cu.offset = off
        cu.align_x = align
        cu.align_y = "CENTER"
        o = bpy.data.objects.new(nm, cu)
        link(o, parent)
        o.location = loc
        o.rotation_euler = [math.radians(a) for a in rot]
        set_mat(o, mm)
        if z:
            o.location = Vector(loc) + o.matrix_world.to_3x3() @ Vector((0, 0, -z))
        return o
    o = make(name, 0.0, m if m is not None else mat(c, rough=0.35, emit=glow), 0)
    if outline:
        back = make(name + "_outline", size * 0.06, mat(outline), extrude + 0.01)
        back.parent = o
        back.location = (0, 0, -extrude - 0.01)
        back.rotation_euler = (0, 0, 0)
        back.matrix_parent_inverse.identity()
    return o


LABELS = []  # on-screen labels of the shot being built (see screen_text)


def _srgb_hex(c):
    out = []
    for v in color(c):
        v = max(0.0, min(1.0, v))
        v = 1.055 * v ** (1 / 2.4) - 0.055 if v > 0.0031308 else v * 12.92
        out.append(int(round(v * 255)))
    return "#%02x%02x%02x" % tuple(out)


class Label:
    """A 2D on-screen label, drawn crisp in post (ffmpeg/libass, Poppins Bold).

    Created by screen_text(); animate with anim.pop_in / pop_out / show / hide
    (other anim calls ignore it). Visible from frame 1 unless popped in later.
    """

    def __init__(self, txt, pos, size, c, outline, tilt=0.0):
        self.text, self.pos, self.size, self.tilt = txt, tuple(pos), size, tilt
        self.color = _srgb_hex(c)
        self.outline = _srgb_hex(outline) if outline else None
        self.show, self.hide, self.pop = 1, None, False
        LABELS.append(self)

    def as_dict(self):
        return {"text": self.text, "pos": self.pos, "size": self.size, "color": self.color,
                "outline": self.outline, "show": self.show, "hide": self.hide, "pop": self.pop,
                "tilt": self.tilt}


def screen_text(cam, txt, pos=(0.0, 0.32), size=0.06, c="white", outline="black", tilt=0.0,
                **_ignored):
    """Text fixed on the screen (title cards, labels like "SYNOVIAL FLUID", "POP!").

    pos  = (x, y) screen fractions: (0, 0) centre, y=+0.5 top edge, x=+0.5 right edge.
    size = letter height as a fraction of screen height (0.06 = label, 0.12 = big word).
    tilt = rotation in degrees (a little tilt reads as "punchy").
    Drawn in post, not by Blender, so it is always sharp and bright; keep labels
    out of the bottom third (captions live there). cam is accepted for API symmetry.
    """
    return Label(txt, pos, size, c, outline, tilt)


def scatter(make, n=20, center=(0, 0, 0), size=(2, 2, 2), seed=0, shape="box", min_dist=0.0):
    """Call make(i, loc, rnd) n times at random spots; returns the list of objects.

    shape="box" (size = full extents) or "sphere" (size[0] = radius) or "disc".
    min_dist keeps items apart (simple rejection sampling).
    """
    rnd = random.Random(seed)
    out, spots = [], []
    tries = 0
    while len(out) < n and tries < n * 50:
        tries += 1
        if shape == "sphere":
            v = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized()
            p = Vector(center) + v * size[0] * rnd.random() ** (1 / 3)
        elif shape == "disc":
            a, rr = rnd.uniform(0, 6.283), size[0] * math.sqrt(rnd.random())
            p = Vector(center) + Vector((rr * math.cos(a), rr * math.sin(a), 0))
        else:
            p = Vector(center) + Vector([rnd.uniform(-s / 2, s / 2) for s in size])
        if min_dist and any((p - q).length < min_dist for q in spots):
            continue
        spots.append(p)
        out.append(make(len(out), tuple(p), rnd))
    return out


def look_at(obj, target):
    """Rotate obj so its -Z axis points at target (the camera/light convention)."""
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def aim(obj, direction, axis="Z"):
    """Point the object's local axis (default +Z) along a direction vector."""
    obj.rotation_mode = "QUATERNION"
    base = {"X": Vector((1, 0, 0)), "Y": Vector((0, 1, 0)), "Z": Vector((0, 0, 1))}[axis]
    obj.rotation_quaternion = base.rotation_difference(Vector(direction).normalized())
    return obj


def _rot_matrix(axis, deg):
    from mathutils import Matrix
    return Matrix.Rotation(math.radians(deg), 3, axis)
