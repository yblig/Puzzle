"""zds: helpers for Zack-D-style 3D explainer shorts (Blender bpy, offline).

Story build functions usually start with:

    from zds import *            # core primitives, anim, Cam, env, Person, Hand
"""
from . import anim, core, env  # noqa: F401
from .camera import Cam  # noqa: F401
from .core import (PALETTE, ball, blob, box, capsule, coil, color, cylinder, empty, aim,  # noqa: F401
                   look_at, mat, scatter, screen_text, set_mat, set_world, text3d, tube)
from .person import EXPRESSIONS, POSES, Hand, Person  # noqa: F401
from .story import Shot  # noqa: F401
