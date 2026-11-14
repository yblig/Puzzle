"""A posable cartoon person (and a detailed standalone hand).

    p = Person(loc=(0, 0, 0), shirt="#2f6fd6", xray=False)
    p.pose("stand", 1); p.pose("hands_front", 20)   # named poses, keyed
    p.face("shock", 30)                             # facial expression
    p.talk(1, 40)                                   # mouth flaps
    p.walk(1, 60, (0, 0), (2, 0))                   # walk cycle between two points
    p.fall(70, 20)                                  # topple over backwards
    p.anchor("heart")                               # empty at the heart (follows body)
    p.add_organs(["heart", "lungs", "stomach"])     # default organs at anchors
    p.joint("el_R")                                 # any joint empty, for custom keys

Coordinates: the person stands on z=0 facing -Y (toward a camera placed at -Y).
Their left hand is on +X. Joint rotations are degrees (x, y, z) in "left-side
convention": the same numbers mean the mirrored motion on the right side, so
poses stay symmetric. x<0 swings a limb forward, y<0 lifts an arm sideways.
"""
import math

import bpy
from mathutils import Vector

from . import anim, core
from .core import ball, box, capsule, empty, mat, tube

H = {  # body measurements (meters)
    "hip_z": 0.92, "hip_x": 0.095, "thigh": 0.40, "shin": 0.40, "leg_r": 0.062,
    "torso": 0.40, "torso_r": 0.165, "neck_z": 0.50, "head_r": 0.17,
    "sh_x": 0.195, "sh_z": 0.43, "upper": 0.28, "fore": 0.25, "arm_r": 0.048,
}

POSES = {
    "stand": {"sh_L": (4, -9, 0), "el_L": (-12, 0, 0), "sh_R": (4, -9, 0), "el_R": (-12, 0, 0)},
    "relaxed": {"sh_L": (2, -6, 0), "el_L": (-8, 0, 0), "sh_R": (2, -6, 0), "el_R": (-8, 0, 0),
                "spine": (2, 0, 0), "head": (3, 0, 4)},
    "t_pose": {"sh_L": (0, -90, 0), "sh_R": (0, -90, 0)},
    "arms_up": {"sh_L": (0, -160, 0), "sh_R": (0, -160, 0), "el_L": (0, 10, 0), "el_R": (0, 10, 0),
                "head": (-10, 0, 0)},
    "wave": {"sh_L": (4, -9, 0), "el_L": (-12, 0, 0), "sh_R": (0, -135, 0), "el_R": (0, -40, 0)},
    "point": {"sh_L": (4, -9, 0), "el_L": (-12, 0, 0), "sh_R": (-85, -10, 15), "el_R": (-5, 0, 0)},
    "think": {"sh_L": (-35, -10, -30), "el_L": (-95, 0, 0), "sh_R": (-55, -15, -10),
              "el_R": (-135, 0, 0), "head": (6, 0, 8), "wr_R": (-20, 0, 0)},
    "shrug": {"sh_L": (5, -30, 0), "el_L": (-85, 0, -30), "sh_R": (5, -30, 0), "el_R": (-85, 0, -30),
              "head": (0, 10, 0), "neck": (0, 0, 0)},
    "hands_front": {"sh_L": (-38, -6, -28), "el_L": (-78, 0, 0), "sh_R": (-38, -6, -28),
                    "el_R": (-78, 0, 0), "head": (14, 0, 0), "wr_L": (0, 0, 0), "wr_R": (0, 0, 0)},
    "clutch_chest": {"sh_L": (-30, -5, -35), "el_L": (-115, 0, 0), "sh_R": (-30, -5, -35),
                     "el_R": (-115, 0, 0), "spine": (12, 0, 0), "head": (12, 0, 0)},
    "clutch_stomach": {"sh_L": (-20, -5, -25), "el_L": (-80, 0, 0), "sh_R": (-20, -5, -25),
                       "el_R": (-80, 0, 0), "spine": (22, 0, 0), "head": (5, 0, 0),
                       "hip_L": (-10, 0, 0), "hip_R": (-10, 0, 0), "kn_L": (15, 0, 0), "kn_R": (15, 0, 0)},
    "facepalm": {"sh_R": (-60, -10, -35), "el_R": (-140, 0, 0), "head": (18, 0, -6),
                 "sh_L": (4, -9, 0), "el_L": (-12, 0, 0)},
    "hands_on_head": {"sh_L": (-10, -125, 0), "el_L": (-30, -100, 0), "sh_R": (-10, -125, 0),
                      "el_R": (-30, -100, 0)},
    "sit": {"hip_L": (-90, 0, 0), "hip_R": (-90, 0, 0), "kn_L": (90, 0, 0), "kn_R": (90, 0, 0),
            "sh_L": (-30, -8, 0), "el_L": (-50, 0, 0), "sh_R": (-30, -8, 0), "el_R": (-50, 0, 0),
            "_drop": 0.45},
    "crouch": {"hip_L": (-70, -8, 0), "hip_R": (-70, -8, 0), "kn_L": (120, 0, 0), "kn_R": (120, 0, 0),
               "an_L": (-45, 0, 0), "an_R": (-45, 0, 0), "spine": (30, 0, 0),
               "sh_L": (-60, -10, 0), "el_L": (-40, 0, 0), "sh_R": (-60, -10, 0), "el_R": (-40, 0, 0),
               "_drop": 0.33},
    "lying": {"sh_L": (0, -40, 0), "sh_R": (0, -40, 0), "el_L": (-20, 0, 0), "el_R": (-20, 0, 0),
              "hip_L": (0, -6, 0), "hip_R": (0, -6, 0)},
    "run_a": {"hip_L": (-40, 0, 0), "kn_L": (40, 0, 0), "hip_R": (30, 0, 0), "kn_R": (70, 0, 0),
              "sh_L": (40, -10, 0), "el_L": (-80, 0, 0), "sh_R": (-50, -10, 0), "el_R": (-80, 0, 0),
              "spine": (10, 0, 0)},
}

EXPRESSIONS = {
    #          mouth     brow_tilt  brow_h  eye_open  pupil_scale
    "neutral": ("flat", 0, 0.0, 1.0, 1.0),
    "happy": ("smile", -8, 0.012, 0.85, 1.0),
    "smile": ("smile", 0, 0.006, 1.0, 1.0),
    "sad": ("frown", 18, 0.0, 0.8, 1.0),
    "shock": ("open", -5, 0.03, 1.35, 0.75),
    "scared": ("o", 22, 0.022, 1.3, 0.7),
    "pain": ("grit", -22, -0.012, 0.25, 1.0),
    "worried": ("flat", 20, 0.012, 1.05, 1.0),
    "angry": ("frown", -25, -0.012, 0.75, 1.0),
    "smirk": ("smirk", -10, 0.006, 0.8, 1.0),
    "relief": ("smile", 12, 0.008, 0.45, 1.0),
    "sick": ("grit", 15, 0.0, 0.6, 1.0),
    "wince": ("grit", -15, -0.006, 0.45, 1.0),
}

ORGANS = {  # anchor name: (parent joint, local offset)
    "brain": ("head", (0, 0.0, 0.035)), "mouth": ("head", (0, -0.16, -0.07)),
    "eyes": ("head", (0, -0.15, 0.02)), "throat": ("neck", (0, -0.02, 0.03)),
    "heart": ("chest", (0.045, -0.05, 0.22)), "lung_L": ("chest", (0.075, -0.01, 0.25)),
    "lung_R": ("chest", (-0.075, -0.01, 0.25)), "liver": ("chest", (-0.06, -0.05, 0.10)),
    "stomach": ("chest", (0.05, -0.06, 0.08)), "intestines": ("spine", (0, -0.05, 0.05)),
    "bladder": ("hips", (0, -0.05, -0.02)), "kidneys": ("spine", (0, 0.06, 0.12)),
    "spine_mid": ("chest", (0, 0.1, 0.15)),
    "knee_L": ("kn_L", (0, 0, 0)), "knee_R": ("kn_R", (0, 0, 0)),
    "elbow_L": ("el_L", (0, 0, 0)), "elbow_R": ("el_R", (0, 0, 0)),
    "hand_L": ("wr_L", (0, 0, -0.06)), "hand_R": ("wr_R", (0, 0, -0.06)),
    "foot_L": ("an_L", (0, -0.05, -0.04)), "foot_R": ("an_R", (0, -0.05, -0.04)),
}


class Hand:
    """A hand with jointed fingers. Fingers point down -Z, palm faces -Y.

    hand.fingers[i] = [mcp, pip, dip] joint empties (i: 0 index .. 3 pinky),
    hand.thumb = [cmc, mcp, ip]. hand.knuckles = list of mcp empties.
    """

    def __init__(self, parent=None, side="L", scale=1.0, skin=None, xray=False, loc=(0, 0, 0),
                 rot=(0, 0, 0), bone_m=None, name="hand"):
        s = scale
        sign = 1 if side == "L" else -1
        self.root = empty(name + "_root", loc=loc, rot=rot, parent=parent)
        skin = skin or mat("skin", rough=0.55)
        bone_m = bone_m or mat("bone", rough=0.4)
        self.xray = xray
        self.palm = box((0.085 * s, 0.032 * s, 0.09 * s), loc=(0, 0, -0.05 * s), m=skin,
                        bevel=0.012 * s, parent=self.root, name=name + "_palm")
        self.fingers, self.knuckles, self.bones = [], [], []
        lens = [(0.044, 0.026, 0.022), (0.048, 0.029, 0.024), (0.045, 0.027, 0.022),
                (0.036, 0.021, 0.019)]
        for i in range(4):
            x = sign * (-0.03 + 0.02 * i) * s * -1
            j = empty(f"{name}_f{i}_mcp", loc=(x, 0, -0.095 * s), parent=self.root)
            chain, parent_j = [j], j
            r = (0.0105 - 0.0007 * i) * s
            for k, L in enumerate(lens[i]):
                L *= s
                capsule(r, L, m=skin, offset=-L / 2, parent=parent_j, name=f"{name}_f{i}_{k}", seg=14)
                if xray:
                    self.bones.append(capsule(r * 0.45, L * 0.9, m=bone_m, offset=-L / 2,
                                              parent=parent_j, seg=10, name="phalanx"))
                if k < 2:
                    parent_j = empty(f"{name}_f{i}_{k + 1}", loc=(0, 0, -L), parent=parent_j)
                    chain.append(parent_j)
            self.fingers.append(chain)
            self.knuckles.append(j)
            ball(r * 1.05, m=skin, parent=j, seg=14, name=f"{name}_knuckle{i}")
        tj = empty(name + "_thumb", loc=(sign * 0.045 * s, -0.005 * s, -0.035 * s),
                   rot=(0, sign * 35, 0), parent=self.root)
        chain, pj = [tj], tj
        for k, L in enumerate((0.03, 0.028, 0.024)):
            L *= s
            capsule(0.012 * s, L, m=skin, offset=-L / 2, parent=pj, seg=14, name=name + "_thumbseg")
            if k < 2:
                pj = empty(name + "_thumbj", loc=(0, 0, -L), parent=pj)
                chain.append(pj)
        self.thumb = chain
        if xray:
            for i in range(4):
                x = sign * (-0.03 + 0.02 * i) * s * -1
                self.bones.append(capsule(0.005 * s, 0.07 * s, loc=(x, 0, -0.055 * s), m=bone_m,
                                          parent=self.root, seg=10, name="metacarpal"))

    def curl(self, frame, amount=1.0, fingers=(0, 1, 2, 3), thumb=True, ease="smooth"):
        """0 = flat, 1 = fist. Keys the finger joints at frame."""
        for i in fingers:
            for k, j in enumerate(self.fingers[i]):
                anim.key(j, "rotation_euler", frame, (-amount * (80, 95, 70)[k], 0, 0), ease=ease)
        if thumb:
            for k, j in enumerate(self.thumb[1:]):
                anim.key(j, "rotation_euler", frame, (-amount * 40, 0, 0), ease=ease)

    def interlock(self, frame, ease="smooth"):
        """Fingers bent back (palm out) — the classic 'stretch and crack all' pose."""
        for chain in self.fingers:
            for k, j in enumerate(chain):
                anim.key(j, "rotation_euler", frame, ((25, 5, 0)[k], 0, 0), ease=ease)


class Person:
    def __init__(self, loc=(0, 0, 0), rot_z=0, shirt="shirt", pants="pants", skin="skin",
                 hair="hair", shoes="shoe", xray=False, skin_alpha=0.22, name="person",
                 hands=True, scale=1.0, bald=False):
        self.name = name
        self.xray = xray
        a = skin_alpha if xray else 1.0
        self.m_skin = mat(skin, rough=0.55, alpha=a)
        self.m_shirt = mat(shirt, rough=0.7, alpha=a)
        self.m_pants = mat(pants, rough=0.8, alpha=a)
        self.m_shoe = mat(shoes, rough=0.5, alpha=a)
        self.m_hair = mat(hair, rough=0.8, alpha=a)
        self.m_bone = mat("bone", rough=0.45)
        self.j = {}
        self.anchors = {}
        self.mouths = {}
        self.root = empty(name + "_root", loc=loc, rot=(0, 0, rot_z))
        self.root.scale = (scale,) * 3
        self.j["root"] = self.root
        self._build(hands, bald)
        self.current_expr = None
        self.pose("stand", 1)
        self.face("neutral", 1)

    # ------------------------------------------------------------ build
    def _J(self, name, loc, parent):
        e = empty(f"{self.name}_{name}", loc=loc, parent=self.j[parent] if isinstance(parent, str) else parent)
        self.j[name] = e
        return e

    def _limb(self, joint, length, r, m, name, bone=True):
        capsule(r, length, m=m, offset=-length / 2, parent=self.j[joint], name=f"{self.name}_{name}")
        if self.xray and bone:
            capsule(r * 0.32, length * 0.95, m=self.m_bone, offset=-length / 2,
                    parent=self.j[joint], name=f"{self.name}_{name}_bone", seg=12)

    def _build(self, hands, bald):
        h = H
        self._J("hips", (0, 0, h["hip_z"]), "root")
        box((0.30, 0.19, 0.16), loc=(0, 0, 0.0), m=self.m_pants, bevel=0.06,
            parent=self.j["hips"], name=self.name + "_pelvis")
        self._J("spine", (0, 0, 0.04), "hips")
        self._J("chest", (0, 0, 0.0), "spine")
        capsule(h["torso_r"], h["torso"] - 2 * h["torso_r"] + 0.16, loc=(0, 0, h["torso"] / 2 + 0.02),
                m=self.m_shirt, parent=self.j["chest"], scale=(1.12, 0.74, 1.0), name=self.name + "_torso")
        self._J("neck", (0, 0, h["neck_z"]), "chest")
        capsule(0.05, 0.06, loc=(0, 0, 0.02), m=self.m_skin, parent=self.j["neck"], name=self.name + "_neck")
        self._J("head", (0, 0, 0.08), "neck")
        hd = self.j["head"]
        hr = h["head_r"]
        ball(hr, loc=(0, 0, hr * 0.85), m=self.m_skin, parent=hd, scale=(0.95, 0.95, 1.05),
             name=self.name + "_skull")
        self.face_root = empty(self.name + "_face", loc=(0, 0, hr * 0.85), parent=hd)
        fr = self.face_root
        if not bald:
            cap = ball(hr * 1.04, loc=(0, 0.02, 0.045), m=self.m_hair, parent=fr,
                       scale=(0.97, 0.97, 0.80), name=self.name + "_hair")
            cap.rotation_euler = (math.radians(-30), 0, 0)
        ball(0.028, loc=(0, -hr * 0.97, -0.01), m=self.m_skin, parent=fr, name=self.name + "_nose")
        for sx in (1, -1):
            ball(0.035, loc=(sx * hr * 0.93, 0, -0.005), m=self.m_skin, parent=fr,
                 scale=(0.5, 1, 1), name=self.name + "_ear")
        # eyes
        self.eyes, self.pupils, self.brows = [], [], []
        white = mat("white", rough=0.2)
        black = mat("black", rough=0.2)
        for sx in (1, -1):
            e = empty(self.name + "_eye", loc=(sx * 0.062, -hr * 0.83, 0.03), parent=fr)
            ball(0.038, m=white, parent=e, name=self.name + "_eyeball", seg=24)
            p = ball(0.019, loc=(0, -0.031, 0), m=black, parent=e, name=self.name + "_pupil",
                     scale=(1, 0.5, 1), seg=16)
            b = box((0.055, 0.012, 0.012), loc=(sx * 0.062, -hr * 0.97, 0.075), m=self.m_hair,
                    bevel=0.005, parent=fr, name=self.name + "_brow")
            self.eyes.append(e)
            self.pupils.append(p)
            self.brows.append((b, sx))
        # mouths (one shown at a time)
        mm = mat((0.35, 0.05, 0.06), rough=0.4)
        mz, my = -0.075, -hr * 0.9
        def arc(name, curve, width=0.06, sag=0.02, tilt=0.0):
            pts = []
            for i in range(9):
                t = i / 8 * 2 - 1
                pts.append((t * width, my + abs(t) * 0.012, mz + curve * sag * (t * t - 1) * -1 + tilt * t))
            o = tube(pts, r=0.008, m=mm, parent=fr, name=f"{self.name}_mouth_{name}")
            return o
        self.mouths["smile"] = arc("smile", -1)
        self.mouths["frown"] = arc("frown", 1, sag=0.018)
        self.mouths["flat"] = arc("flat", 0.15, width=0.045)
        self.mouths["smirk"] = arc("smirk", -0.6, width=0.045, tilt=0.012)
        self.mouths["open"] = ball(0.05, loc=(0, my + 0.01, mz - 0.01), m=mm, parent=fr,
                                   scale=(0.9, 0.35, 0.8), name=self.name + "_mouth_open")
        self.mouths["o"] = ball(0.028, loc=(0, my + 0.008, mz - 0.005), m=mm, parent=fr,
                                scale=(1, 0.4, 1.2), name=self.name + "_mouth_o")
        grit = box((0.085, 0.02, 0.028), loc=(0, my + 0.006, mz), m=white, bevel=0.008,
                   parent=fr, name=self.name + "_mouth_grit")
        box((0.09, 0.012, 0.004), loc=(0, -0.008, 0), m=black, parent=grit)
        self.mouths["grit"] = grit
        self.talk_mouth = ball(0.045, loc=(0, my + 0.01, mz - 0.008), m=mm, parent=fr,
                               scale=(0.9, 0.35, 0.5), name=self.name + "_mouth_talk")
        # arms
        for side, sx in (("L", 1), ("R", -1)):
            self._J("sh_" + side, (sx * h["sh_x"], 0, h["sh_z"]), "chest")
            ball(h["arm_r"] * 1.25, m=self.m_shirt, parent=self.j["sh_" + side], name=self.name + "_shoulder")
            self._limb("sh_" + side, h["upper"], h["arm_r"] * 1.1, self.m_shirt, "upper_" + side)
            self._J("el_" + side, (0, 0, -h["upper"]), "sh_" + side)
            self._limb("el_" + side, h["fore"], h["arm_r"], self.m_skin, "fore_" + side)
            self._J("wr_" + side, (0, 0, -h["fore"]), "el_" + side)
            if hands:
                hand = Hand(parent=self.j["wr_" + side], side=side, scale=1.0, skin=self.m_skin,
                            xray=self.xray, rot=(0, 0, -sx * 90), name=f"{self.name}_hand{side}",
                            bone_m=self.m_bone)
                setattr(self, "hand_" + side, hand)
            else:
                ball(0.05, loc=(0, 0, -0.04), m=self.m_skin, parent=self.j["wr_" + side])
            # legs
            self._J("hip_" + side, (sx * h["hip_x"], 0, -0.03), "hips")
            self._limb("hip_" + side, h["thigh"], h["leg_r"] * 1.15, self.m_pants, "thigh_" + side)
            self._J("kn_" + side, (0, 0, -h["thigh"]), "hip_" + side)
            self._limb("kn_" + side, h["shin"], h["leg_r"], self.m_pants, "shin_" + side)
            self._J("an_" + side, (0, 0, -h["shin"]), "kn_" + side)
            box((0.10, 0.22, 0.075), loc=(0, -0.05, -0.045), m=self.m_shoe, bevel=0.03,
                parent=self.j["an_" + side], name=self.name + "_shoe")
        if self.xray:
            self._skeleton()
        for nm, (jn, off) in ORGANS.items():
            self.anchors[nm] = empty(f"{self.name}_{nm}", loc=off, parent=self.j[jn])

    def _skeleton(self):
        b = self.m_bone
        ball(H["head_r"] * 0.78, loc=(0, 0.01, H["head_r"] * 0.9), m=b, parent=self.j["head"],
             name=self.name + "_skull_bone")
        for i in range(9):  # spine
            box((0.035, 0.035, 0.03), loc=(0, 0.07, 0.04 + i * 0.052), m=b, bevel=0.008,
                parent=self.j["chest"], name=self.name + "_vertebra")
        for i in range(6):  # ribs: arcs around the chest
            z = 0.16 + i * 0.04
            w = 0.13 - abs(i - 2.5) * 0.008
            pts = [(w * math.sin(a), -0.075 * math.cos(a) + 0.01, z - 0.02 * abs(math.sin(a)))
                   for a in [math.radians(d) for d in range(-160, 161, 20)]]
            tube(pts, r=0.007, m=b, parent=self.j["chest"], name=self.name + "_rib")
        box((0.26, 0.10, 0.09), loc=(0, 0.01, 0.0), m=b, bevel=0.04, parent=self.j["hips"],
            name=self.name + "_pelvis_bone")

    # ------------------------------------------------------------ access
    def joint(self, name):
        return self.j[name]

    def anchor(self, name):
        return self.anchors[name]

    def world(self, name):
        """World position (Vector) of a joint or anchor, at the current frame state."""
        bpy.context.view_layer.update()
        o = self.anchors.get(name) or self.j[name]
        return o.matrix_world.translation.copy()

    def add_organs(self, names=("heart", "lungs", "stomach", "brain"), alpha=1.0):
        """Default organ meshes parented to anchors. Returns dict name -> object."""
        out = {}
        for n in names:
            if n == "heart":
                out[n] = core.blob(0.055, m=mat((0.75, 0.05, 0.08), alpha=alpha), lump=0.12,
                                   parent=self.anchors["heart"], seed=3, name="heart",
                                   scale=(1, 0.85, 1.1))
            elif n == "lungs":
                out[n] = [core.blob(0.07, m=mat((0.95, 0.5, 0.55), alpha=alpha), lump=0.1,
                                    parent=self.anchors[k], seed=i, scale=(0.75, 0.7, 1.35), name=k)
                          for i, k in enumerate(("lung_L", "lung_R"))]
            elif n == "brain":
                out[n] = core.blob(0.115, m=mat((0.95, 0.6, 0.65), alpha=alpha), lump=0.06, freq=7,
                                   parent=self.anchors["brain"], seed=5, scale=(0.9, 1.1, 0.8),
                                   name="brain")
            elif n == "stomach":
                out[n] = core.blob(0.065, m=mat((0.9, 0.45, 0.4), alpha=alpha), lump=0.15,
                                   parent=self.anchors["stomach"], seed=8, scale=(1.3, 0.8, 0.9),
                                   name="stomach")
            elif n == "liver":
                out[n] = core.blob(0.07, m=mat((0.45, 0.06, 0.05), alpha=alpha), lump=0.1,
                                   parent=self.anchors["liver"], seed=9, scale=(1.4, 0.7, 0.7),
                                   name="liver")
            elif n == "intestines":
                out[n] = tube(core.coil((0, 0, 0), 0.09, turns=5, height=0.12, wiggle=0.01),
                              r=0.016, m=mat((0.92, 0.55, 0.5), alpha=alpha),
                              parent=self.anchors["intestines"], name="intestines")
            elif n == "bladder":
                out[n] = core.blob(0.04, m=mat((0.95, 0.85, 0.3), alpha=alpha), lump=0.05,
                                   parent=self.anchors["bladder"], seed=2, name="bladder")
            elif n == "kidneys":
                out[n] = [core.blob(0.035, loc=(sx * 0.07, 0, 0), m=mat((0.55, 0.1, 0.1), alpha=alpha),
                                    lump=0.08, parent=self.anchors["kidneys"], seed=4,
                                    scale=(0.7, 0.7, 1.2), name="kidney") for sx in (1, -1)]
        return out

    # ------------------------------------------------------------ animation
    def pose(self, name, frame, ease="smooth", base="stand", **over):
        """Key a named pose (or a dict) at frame. Unlisted joints return to `base`.

        over: per-joint overrides, e.g. pose("stand", 10, head=(0, 0, 25)).
        """
        p = dict(POSES.get(base, {}))
        p.update(POSES[name] if isinstance(name, str) else name)
        p.update(over)
        drop = p.pop("_drop", 0.0)
        for jn in ("spine", "neck", "head", "sh_L", "el_L", "wr_L", "sh_R", "el_R", "wr_R",
                   "hip_L", "kn_L", "an_L", "hip_R", "kn_R", "an_R"):
            x, y, z = p.get(jn, (0, 0, 0))
            if jn.endswith("_R"):
                y, z = -y, -z
            anim.key(self.j[jn], "rotation_euler", frame, (x, y, z), ease=ease)
        anim.key(self.j["hips"], "location", frame, (0, 0, H["hip_z"] - drop), ease=ease)

    def set_joint(self, jn, frame, rot, ease="smooth"):
        x, y, z = rot
        if jn.endswith("_R"):
            y, z = -y, -z
        anim.key(self.j[jn], "rotation_euler", frame, (x, y, z), ease=ease)

    def face(self, expr, frame):
        """Switch facial expression at frame (snaps, like a cartoon)."""
        mouth, tilt, bh, eye, pup = EXPRESSIONS[expr]
        for k, o in self.mouths.items():
            (anim.show if k == mouth else anim.hide)(o, frame)
        anim.hide(self.talk_mouth, frame)
        for b, sx in self.brows:
            anim.key(b, "rotation_euler", frame, (0, sx * -tilt, 0), ease="snap")
            anim.key(b, "location", frame, (b.location.x, b.location.y, 0.075 + bh), ease="snap")
        for e in self.eyes:
            anim.key(e, "scale", frame, (1, 1, eye), ease="snap")
        for p in self.pupils:
            anim.key(p, "scale", frame, (pup, 0.5, pup), ease="snap")
        self.current_expr = expr

    def look(self, frame, dx=0.0, dz=0.0):
        """Shift pupils: dx>0 = the person's left (+X), dz>0 = up. Range about ±1."""
        for p in self.pupils:
            anim.key(p, "location", frame, (dx * 0.014, -0.031, dz * 0.012), ease="smooth")

    def blink(self, frame):
        for e in self.eyes:
            z = e.scale.z
            anim.key(e, "scale", frame, (1, 1, z), ease="linear")
            anim.key(e, "scale", frame + 2, (1, 1, 0.08), ease="linear")
            anim.key(e, "scale", frame + 5, (1, 1, z))

    def talk(self, f0, f1, rate=4, seed=0):
        """Mouth flaps between f0 and f1, then returns to the current expression."""
        import random
        rnd = random.Random(seed)
        expr = self.current_expr or "neutral"
        mouth = EXPRESSIONS[expr][0]
        anim.hide(self.mouths[mouth], f0)
        anim.show(self.talk_mouth, f0)
        base = (0.9, 0.35, 0.5)
        f = f0
        while f < f1:
            anim.key(self.talk_mouth, "scale", f, (0.9, 0.35, rnd.uniform(0.15, 0.9)), ease="linear")
            f += rate
        anim.key(self.talk_mouth, "scale", f1, base)
        anim.hide(self.talk_mouth, f1)
        anim.show(self.mouths[mouth], f1)

    def walk(self, f0, f1, start, end, step=14, face_dir=True, run=False):
        """Walk (or run) from start (x, y) to end (x, y) on the floor."""
        sx, sy = start
        ex, ey = end
        z = self.root.location.z
        if face_dir:
            ang = math.degrees(math.atan2(ex - sx, -(ey - sy))) if (ex, ey) != (sx, sy) else 0
            anim.key(self.root, "rotation_euler", f0, (0, 0, -ang + 0), ease="smooth")
        anim.key(self.root, "location", f0, (sx, sy, z), ease="linear")
        anim.key(self.root, "location", f1, (ex, ey, z))
        sw = 38 if run else 24
        arm = 35 if run else 18
        f, k = f0, 0
        while f < f1:
            s = 1 if k % 2 == 0 else -1
            d = {"hip_L": (-sw * s, 0, 0), "hip_R": (sw * s, 0, 0),
                 "kn_L": (10 if s > 0 else 35, 0, 0), "kn_R": (35 if s > 0 else 10, 0, 0),
                 "sh_L": (arm * s, -8, 0), "sh_R": (-arm * s, -8, 0),
                 "el_L": (-25 if not run else -80, 0, 0), "el_R": (-25 if not run else -80, 0, 0),
                 "spine": (8 if run else 2, 0, 0)}
            self.pose(d, f, base="stand")
            anim.key(self.j["hips"], "location", f + step // 2, (0, 0, H["hip_z"] + 0.025), ease="sine")
            f += step
            k += 1
        self.pose("stand", f1 + 4)

    def fall(self, f0, dur=18, direction="back"):
        """Topple to the floor (pivot at the feet). Ends lying down."""
        sgn = -1 if direction == "back" else 1
        r0 = [math.degrees(a) for a in self.root.rotation_euler]
        anim.key(self.root, "rotation_euler", f0, r0, ease="quad")
        anim.key(self.root, "rotation_euler", f0 + dur, (sgn * 88, r0[1], r0[2]), ease="bounce")
        anim.key(self.root, "rotation_euler", f0 + dur + 6, (sgn * 90, r0[1], r0[2]))
        loc = tuple(self.root.location)
        anim.key(self.root, "location", f0 + dur, (loc[0], loc[1], loc[2] + 0.12))
        self.pose("arms_up", f0 + dur // 2)
        self.pose("lying", f0 + dur + 6)
        self.face("shock", f0)
