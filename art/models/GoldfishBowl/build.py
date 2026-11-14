"""Goldfish Bowl (decoration): a big celadon-glazed fish bowl on a timber stand, water lilies on the water and a
couple of goldfish. 1x1x2 on the vanilla Shrub."""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403


def blob(g, c, rx, ry, rz, col, sides=10, rings=6, material=PLASTER):
    """An ellipsoid of lime sheet painted by vertex colour (carved, painted or glazed surfaces)."""
    prof = [(math.sin(math.pi * k / rings), -math.cos(math.pi * k / rings)) for k in range(rings + 1)]
    K.lathe(g, prof, (0, 0, 0), sides, material, uv_region=(0.1, 0.1, 0.9, 0.9), cap_top=False)
    p = g.parts[-1]
    S = np.diag([rx, ry, rz])
    p.P = p.P @ S.T + np.asarray(c, float)
    p.N = p.N @ np.linalg.inv(S)
    p.N /= np.linalg.norm(p.N, axis=1, keepdims=True)
    p.T = fix_winding(p.P, p.N, p.T)
    p.C = np.tile(list(col) + [1.0], (len(p.P), 1))


m = Model("GoldfishBowl", size=(1, 1, 2), seed=245, stand_in="Shrub.Folktails")
g = m.geo
for (x, z) in ((0.25, 0.25), (0.75, 0.25), (0.75, 0.75), (0.25, 0.75)):
    K.beam(g, (x, 0.0, z), (x, 0.3, z), w=0.06, caps="end")
K.box(g, (0.18, 0.3, 0.18), (0.82, 0.35, 0.82), TIMBER, WOOD_BLOCK, skip=(3,))
K.lathe(g, [(0.2, 0.35), (0.38, 0.45), (0.42, 0.62), (0.36, 0.74), (0.38, 0.77)], (0.5, 0.0, 0.5), 12, PLASTER,
        cap_top=False)
g.parts[-1].C = np.tile([0.36, 0.46, 0.4, 1.0], (len(g.parts[-1].P), 1))
K.lathe(g, [(0.35, 0.72), (0.0, 0.72)], (0.5, 0.0, 0.5), 12, PLASTER, cap_top=False)
water = g.parts[-1]
water.N[:] = (0, 1, 0)
water.T = fix_winding(water.P, water.N, water.T)
water.C = np.tile([0.2, 0.33, 0.36, 1.0], (len(water.P), 1))
for (x, z) in ((0.42, 0.45), (0.6, 0.58)):
    blob(g, (x, 0.725, z), 0.08, 0.008, 0.08, (0.4, 0.62, 0.3))
for (x, z) in ((0.55, 0.4), (0.38, 0.6)):
    blob(g, (x, 0.715, z), 0.05, 0.012, 0.022, (1.0, 0.5, 0.15))
m.collider((0.5, 0.4, 0.5), (0.85, 0.8, 0.85))
m.build()
