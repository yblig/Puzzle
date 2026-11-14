"""Ready-made environments. Each returns a dict of the objects it made.

    env.studio()          clean seamless backdrop (default explainer look)
    env.dark()            near-black void with a soft floor: drama, x-ray, space
    env.medical()         teal "inside the body / lab" look with floating particles
    env.outdoor()         sky, grass, trees, clouds
    env.room()            floor, two walls, window, couch, rug, lamp
    env.inside_body()     dark red tunnel-like interior (blood vessel / gut)
"""
import math
import random

import bmesh
import bpy

from . import core
from .core import ball, blob, box, capsule, cylinder, mat, set_world, light_rig


def cyclorama(c=(0.8, 0.8, 0.82), width=80, depth=40, curve_r=6, height=40, y_wall=8,
              name="backdrop", z=0.0):
    """Seamless floor-to-wall curve (photo-studio sweep). Floor at z=0, wall at +Y."""
    prof = [(-depth, 0.0)]
    y0 = y_wall - curve_r
    prof.append((y0, 0.0))
    for i in range(1, 12):
        a = i / 12 * math.pi / 2
        prof.append((y0 + curve_r * math.sin(a), curve_r - curve_r * math.cos(a)))
    prof += [(y_wall, curve_r), (y_wall, height)]
    bm = bmesh.new()
    rows = []
    for x in (-width / 2, width / 2):
        rows.append([bm.verts.new((x, y, z)) for y, z in prof])
    for i in range(len(prof) - 1):
        bm.faces.new((rows[0][i], rows[1][i], rows[1][i + 1], rows[0][i + 1]))
    return core._finish(name, bm, (0, 0, z), (0, 0, 0), 1, c, None, None, True)


# z = floor height. Use a negative z (e.g. -2) for floating close-ups, so the floor
# doesn't slice through objects built around the origin.

def studio(c=(0.78, 0.80, 0.84), world=None, z=0.0):
    set_world(world or tuple(v * 0.9 for v in core.color(c)))
    light_rig("studio")
    return {"backdrop": cyclorama(c, z=z)}


def dark(c=(0.035, 0.04, 0.05), world=(0.005, 0.006, 0.008), z=0.0):
    set_world(world)
    light_rig("rim")
    sc = bpy.context.scene
    if sc.render.engine == "BLENDER_WORKBENCH":
        sc.display.shading.shadow_intensity = 0.7
    return {"backdrop": cyclorama(c, z=z)}


def medical(c=(0.02, 0.16, 0.22), particles=40, seed=2, z=0.0):
    set_world((0.01, 0.07, 0.10))
    light_rig("studio")
    bd = cyclorama(c, z=z)
    pm = mat((0.45, 0.85, 1.0), alpha=0.35, emit=2.0)
    parts = core.scatter(lambda i, p, r: ball(r.uniform(0.01, 0.035), loc=p, m=pm, seg=10,
                                              name="particle"),
                         particles, center=(0, 1, z + 2.0), size=(8, 4, 4), seed=seed)
    return {"backdrop": bd, "particles": parts}


def outdoor(trees=6, seed=4, grass=(0.18, 0.45, 0.10), sky=(0.38, 0.62, 0.95)):
    set_world(sky)
    light_rig("outdoor")
    rnd = random.Random(seed)
    ground = cylinder(60, 0.2, loc=(0, 0, -0.1), c=grass, seg=64, name="ground")
    out = {"ground": ground, "trees": [], "clouds": []}
    for i in range(trees):
        side = -1 if i % 2 else 1
        x = side * rnd.uniform(3, 9)
        y = rnd.uniform(3, 14)
        h = rnd.uniform(1.6, 2.6)
        trunk = cylinder(0.14, h, loc=(x, y, h / 2), c=(0.30, 0.17, 0.07), seg=12, name="trunk")
        crown = blob(rnd.uniform(0.9, 1.4), loc=(x, y, h + 0.6), c=(0.10, 0.38, 0.08),
                     lump=0.15, seed=i, subdiv=3, name="crown")
        out["trees"].append((trunk, crown))
    for i in range(4):
        cl = blob(rnd.uniform(1.2, 2.0), loc=(rnd.uniform(-12, 12), rnd.uniform(25, 35),
                                             rnd.uniform(9, 14)),
                  c="white", lump=0.25, seed=10 + i, subdiv=3, scale=(1.8, 0.8, 0.6),
                  name="cloud")
        out["clouds"].append(cl)
    return out


def room(wall=(0.75, 0.68, 0.58), floor=(0.40, 0.24, 0.12), couch=True):
    set_world((0.6, 0.6, 0.62))
    light_rig("studio")
    out = {}
    out["floor"] = box((14, 14, 0.1), loc=(0, 2, -0.05), c=floor, name="floor")
    out["back_wall"] = box((14, 0.2, 6), loc=(0, 4, 3), c=wall, name="back_wall")
    out["side_wall"] = box((0.2, 14, 6), loc=(-4.5, 2, 3), c=tuple(v * 0.9 for v in wall),
                           name="side_wall")
    fr = (0.95, 0.95, 0.95)
    out["window"] = [
        box((1.8, 0.05, 1.3), loc=(1.6, 3.88, 2.2), c=(0.55, 0.78, 1.0), name="glass"),
        box((1.95, 0.12, 0.08), loc=(1.6, 3.85, 2.88), c=fr),
        box((1.95, 0.12, 0.08), loc=(1.6, 3.85, 1.52), c=fr),
        box((0.08, 0.12, 1.4), loc=(0.63, 3.85, 2.2), c=fr),
        box((0.08, 0.12, 1.4), loc=(2.57, 3.85, 2.2), c=fr),
        box((0.06, 0.12, 1.3), loc=(1.6, 3.85, 2.2), c=fr),
    ]
    out["rug"] = cylinder(1.6, 0.02, loc=(0, 0.8, 0.01), c=(0.6, 0.12, 0.12), seg=48, name="rug")
    if couch:
        cc = (0.20, 0.30, 0.45)
        out["couch"] = [
            box((2.4, 0.9, 0.45), loc=(-1.6, 3.2, 0.3), c=cc, bevel=0.06, name="couch_seat"),
            box((2.4, 0.25, 0.9), loc=(-1.6, 3.6, 0.75), c=cc, bevel=0.08, name="couch_back"),
            box((0.25, 0.9, 0.65), loc=(-2.75, 3.2, 0.45), c=cc, bevel=0.08),
            box((0.25, 0.9, 0.65), loc=(-0.45, 3.2, 0.45), c=cc, bevel=0.08),
        ]
    out["lamp"] = [cylinder(0.03, 1.5, loc=(3.2, 3.2, 0.75), c="black", seg=12),
                   cylinder(0.25, 0.35, r2=0.15, loc=(3.2, 3.2, 1.6), c=(1, 0.9, 0.7), seg=24)]
    return out


def inside_body(c=(0.35, 0.02, 0.03), radius=2.5, length=30, cells=30, seed=7):
    """A big tube you sit inside (vessel, gut, airway), with floating red cells."""
    set_world((0.05, 0.0, 0.0))
    light_rig("studio")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=48, radius1=radius, radius2=radius,
                          depth=length)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    wall = core._finish("vessel", bm, (0, length / 2 - 5, 0), (90, 0, 0), 1, c, None, None, True)
    rbc = mat((0.75, 0.04, 0.04), rough=0.4)
    def cell(i, p, r):
        o = cylinder(0.22, 0.08, loc=p, m=rbc, seg=20, name="rbc")
        o.rotation_euler = (r.uniform(0, 3), r.uniform(0, 3), 0)
        return o
    cs = core.scatter(cell, cells, center=(0, length / 2 - 5, 0), size=(radius * 1.2, length, radius * 1.2),
                      seed=seed)
    return {"wall": wall, "cells": cs}
