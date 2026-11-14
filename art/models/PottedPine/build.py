"""Potted Pine (decoration): a little windswept pine in a glazed pot on a stone stool. 1x1x2 on the vanilla Shrub."""
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


m = Model("PottedPine", size=(1, 1, 2), seed=243, stand_in="Shrub.Folktails")
g = m.geo
K.lathe(g, [(0.0, 0.0), (0.16, 0.0), (0.18, 0.28), (0.0, 0.28)], (0.5, 0.0, 0.5), 7, PLASTER, cap_top=False)
g.parts[-1].C = np.tile([0.58, 0.58, 0.56, 1.0], (len(g.parts[-1].P), 1))
K.lathe(g, [(0.12, 0.0), (0.24, 0.04), (0.26, 0.2), (0.24, 0.22)], (0.5, 0.28, 0.5), 9, PLASTER, cap_top=True)
g.parts[-1].C = np.tile([0.26, 0.34, 0.3, 1.0], (len(g.parts[-1].P), 1))
pts = [(0.5, 0.48, 0.5), (0.47, 0.75, 0.52), (0.58, 1.0, 0.48), (0.7, 1.15, 0.46)]
K.tube(g, pts, [0.05, 0.04, 0.03, 0.02], TIMBER, sides=5)
for (x, y, z, r) in ((0.42, 0.8, 0.55, 0.2), (0.62, 1.08, 0.46, 0.22), (0.78, 1.2, 0.44, 0.15), (0.5, 1.25, 0.52, 0.16)):
    blob(g, (x, y, z), r, r * 0.4, r * 0.85, (1.0, 1.0, 1.0), material=MOSS)
m.collider((0.5, 0.7, 0.5), (0.6, 1.4, 0.6))
m.build()
