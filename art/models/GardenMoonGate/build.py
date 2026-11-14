"""Garden Moon Gate (decoration): a short length of white garden wall with grey-tile coping, pierced by a round moon
gate one can see through, a potted bamboo at its foot. 1x1x2 on the vanilla Shrub."""
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


m = Model("GardenMoonGate", size=(1, 1, 2), seed=247, stand_in="Shrub.Folktails")
g = m.geo
WZ, H, R, T = 0.5, 1.45, 0.36, 0.07
CY = 0.08 + R + 0.05
for (x0, x1) in ((0.0, 0.5 - R), (0.5 + R, 1.0)):
    K.box(g, (x0, 0.0, WZ - T), (x1, H, WZ + T), PLASTER, (0.05, 0.05, 0.95, 0.95), skip=(3,))
K.box(g, (0.5 - R, CY + R, WZ - T), (0.5 + R, H, WZ + T), PLASTER, (0.05, 0.05, 0.95, 0.95), skip=(3,))
K.box(g, (0.5 - R, 0.0, WZ - T), (0.5 + R, CY - R, WZ + T), PLASTER, (0.05, 0.05, 0.95, 0.95), skip=(3,))
for sx in (-1, 1):
    for zz, nz in ((WZ - T - 0.001, -1.0), (WZ + T + 0.001, 1.0)):
        for sy in (-1, 1):
            pts = [(0.5 + sx * R, CY, zz), (0.5 + sx * R, CY + sy * R, zz)]
            for a in np.linspace(math.pi / 2, 0, 5):
                pts.append((0.5 + sx * R * math.cos(a), CY + sy * R * math.sin(a), zz))
            P = np.array(pts)
            Nn = np.tile([0.0, 0.0, nz], (len(P), 1))
            Tt = np.array([(1, k, k + 1) for k in range(2, len(P) - 1)] + [(0, 1, len(P) - 1)])
            g.add(Part(PLASTER, P, Nn, np.clip(0.1 + 0.4 * (P[:, :2] - P[:, :2].min(0)), 0, 1), fix_winding(P, Nn, Tt)))
ring = [(0.5 + math.cos(a) * (R + 0.02), CY + math.sin(a) * (R + 0.02)) for a in np.linspace(0, 2 * math.pi, 17)]
for dz in (-T - 0.01, T + 0.01):
    K.tube(g, [(x, y, WZ + dz) for x, y in ring], [0.03] * len(ring), TIMBER, sides=4, caps=False)
K.box(g, (-0.03, H, WZ - T - 0.05), (1.03, H + 0.05, WZ + T + 0.05), TILE,
      (0.0, TILE_COURSES[0][0], 0.4, TILE_COURSES[0][1]), skip=(3,))
K.lathe(g, [(0.0, 0.0), (0.09, 0.0), (0.11, 0.14)], (0.85, 0.0, 0.25), 7, EARTH)
for k in range(4):
    K.pole(g, (0.85, 0.14, 0.25), (0.85 + 0.06 * (k - 1.5), 0.8 + 0.08 * k, 0.25), r=0.012, material=BAMBOO_GREEN,
           sides=3, bend=0.03, caps=False)
m.collider((0.5, 0.75, 0.5), (1.0, 1.5, 0.2))
m.build()
