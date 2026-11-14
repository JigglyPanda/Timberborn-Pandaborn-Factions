"""Panda Statue (decoration): a stone panda sitting on a plinth, painted in the folk way, munching a bamboo shoot.
1x1x2 on the vanilla Beaver Statue."""
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


m = Model("PandaStatue", size=(1, 1, 2), seed=241, stand_in="BeaverStatue.Folktails")
g = m.geo
K.box(g, (0.18, 0.0, 0.18), (0.82, 0.32, 0.82), PLASTER, (0.1, 0.1, 0.9, 0.9), skip=(3,), jitter=0.02)
g.parts[-1].C = np.tile([0.58, 0.58, 0.56, 1.0], (len(g.parts[-1].P), 1))
K.box(g, (0.14, 0.32, 0.14), (0.86, 0.38, 0.86), PLASTER, (0.1, 0.1, 0.9, 0.9), skip=(3,))
g.parts[-1].C = np.tile([0.5, 0.5, 0.48, 1.0], (len(g.parts[-1].P), 1))
W, B = (0.9, 0.89, 0.85), (0.16, 0.16, 0.17)
blob(g, (0.5, 0.68, 0.52), 0.28, 0.3, 0.24, W)
blob(g, (0.5, 0.8, 0.5), 0.29, 0.1, 0.22, B)
blob(g, (0.5, 1.08, 0.5), 0.2, 0.18, 0.18, W)
for sx in (-1, 1):
    blob(g, (0.5 + sx * 0.15, 1.24, 0.5), 0.06, 0.06, 0.04, B)
    blob(g, (0.5 + sx * 0.075, 1.1, 0.33), 0.04, 0.055, 0.02, B)
    blob(g, (0.5 + sx * 0.16, 0.45, 0.32), 0.09, 0.08, 0.13, B)
    blob(g, (0.5 + sx * 0.2, 0.8, 0.36), 0.07, 0.15, 0.07, B)
blob(g, (0.5, 1.04, 0.33), 0.07, 0.05, 0.05, W)
K.pole(g, (0.45, 0.72, 0.28), (0.55, 1.02, 0.3), r=0.018, material=BAMBOO_GREEN, sides=4, bend=0.0)
m.collider((0.5, 0.65, 0.5), (0.7, 1.3, 0.7))
m.build()
