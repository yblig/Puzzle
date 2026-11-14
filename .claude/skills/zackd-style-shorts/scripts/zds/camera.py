"""Camera rig: a camera that always looks at a target empty, inside a shake rig.

    cam = Cam(loc=(0, -4, 1.6), target=(0, 0, 1.2), lens=40)
    cam.dolly(1, 60, (0, -2.5, 1.5))         # push in
    cam.orbit(1, 90, center=(0,0,1), radius=3, height=1.4, a0=-20, a1=25)
    cam.zoom(40, 55, 70)                      # lens change = zoom
    cam.shake(30, 42, amp=0.04)               # impact shake
    cam.track(1, 60, (0, 0, 1.0))             # move what we look at
"""
import math
import random

import bpy
from mathutils import Vector

from . import anim
from .core import empty, link


class Cam:
    def __init__(self, loc=(0, -5, 1.5), target=(0, 0, 1), lens=40, dof=None, clip=0.01):
        sc = bpy.context.scene
        self.rig = empty("cam_rig")
        cd = bpy.data.cameras.new("cam")
        cd.lens = lens
        cd.sensor_fit = "VERTICAL"
        cd.sensor_height = 24.0
        cd.clip_start = clip
        cd.clip_end = 500
        self.obj = bpy.data.objects.new("cam", cd)
        link(self.obj, self.rig)
        self.obj.location = loc
        self.target = empty("cam_target", loc=target)
        c = self.obj.constraints.new("TRACK_TO")
        c.target = self.target
        c.track_axis = "TRACK_NEGATIVE_Z"
        c.up_axis = "UP_Y"
        sc.camera = self.obj
        if dof:
            cd.dof.use_dof = True
            cd.dof.focus_object = self.target
            cd.dof.aperture_fstop = dof

    # ------------------------------------------------------------ basic keys
    def set(self, frame, loc=None, target=None, lens=None, ease="smooth"):
        if loc is not None:
            anim.key(self.obj, "location", frame, tuple(loc), ease=ease)
        if target is not None:
            anim.key(self.target, "location", frame, tuple(target), ease=ease)
        if lens is not None:
            anim.key(self.obj, "data.lens", frame, lens, ease=ease)

    def dolly(self, f0, f1, to, frm=None, ease="smooth"):
        """Move the camera (it keeps looking at the target)."""
        anim.move(self.obj, f0, f1, to, frm=frm, ease=ease)

    def track(self, f0, f1, to, frm=None, ease="smooth"):
        """Move the look-at point (pan/tilt toward something)."""
        anim.move(self.target, f0, f1, to, frm=frm, ease=ease)

    def zoom(self, f0, f1, lens, ease="smooth"):
        anim.key(self.obj, "data.lens", f0, self.obj.data.lens, ease=ease)
        anim.key(self.obj, "data.lens", f1, lens)

    def push(self, f0, f1, amount=0.35, ease="smooth"):
        """Slow push toward the target by a fraction of the distance (classic ZD move)."""
        p = Vector(self.obj.location)
        t = Vector(self.target.location)
        self.dolly(f0, f1, p.lerp(t, amount), ease=ease)

    def orbit(self, f0, f1, center=None, radius=None, height=None, a0=-30, a1=30, step=3):
        """Circle around center. Angles in degrees; 0 = in front (on -Y)."""
        c = Vector(center if center is not None else self.target.location)
        rel = Vector(self.obj.location) - c
        if radius is None:
            radius = Vector((rel.x, rel.y)).length
        if height is None:
            height = self.obj.location.z
        if center is not None:
            anim.key(self.target, "location", f0, tuple(c))
        n = max(2, (f1 - f0) // step)
        for i in range(n + 1):
            t = i / n
            t = t * t * (3 - 2 * t)  # ease in/out
            a = math.radians(a0 + (a1 - a0) * t)
            p = (c.x + radius * math.sin(a), c.y - radius * math.cos(a), height)
            anim.key(self.obj, "location", f0 + round((f1 - f0) * i / n), p, ease="linear")

    def shake(self, f0, f1, amp=0.05, every=2, seed=3, decay=True):
        """Handheld/impact shake on the rig (does not disturb other moves)."""
        rnd = random.Random(seed)
        anim.key(self.rig, "location", f0, (0, 0, 0), ease="linear")
        n = max(1, (f1 - f0) // every)
        for i in range(1, n):
            k = (1 - i / n) if decay else 1
            anim.key(self.rig, "location", f0 + i * every,
                     tuple(rnd.uniform(-amp, amp) * k for _ in range(3)), ease="linear")
        anim.key(self.rig, "location", f1, (0, 0, 0))

    def drift(self, f0, f1, amp=0.03, period=45, seed=5):
        """Very slow floaty motion so 'static' shots never feel frozen."""
        rnd = random.Random(seed)
        f = f0
        while f <= f1:
            anim.key(self.rig, "location", f, tuple(rnd.uniform(-amp, amp) for _ in range(3)),
                     ease="sine")
            f += period // 2
