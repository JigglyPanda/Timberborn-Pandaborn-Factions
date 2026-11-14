"""Night Courier Post: hauling through the evening and night. 3x2 on the vanilla Hauling Post. The moon mark: a white
lime wall pierced by a round moon gate rimmed in dark timber, a little grey-tile gable roof along it; behind it the
couriers' back-baskets on a rack, carrying poles, a bench, and lanterns either side of the gate.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, solid_blocks  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("NightCourierPost", size=(3, 2, 3), seed=173, stand_in="HaulingPost.Folktails")
g = m.geo
B = 0.1
K.plinth(g, 0.04, 0.06, 2.96, 1.94, h=B)
WZ, H, R = 0.55, 1.6, 0.55
CY = B + R + 0.06            # centre of the round opening
# the wall: two piers, a lintel block over the circle, and the four spandrels filled in with plaster
for (x0, x1) in ((0.12, 1.5 - R), (1.5 + R, 2.88)):
    K.box(g, (x0, B, WZ - 0.08), (x1, H, WZ + 0.08), PLASTER_LATH, (0.05, 0.05, 0.95, 0.95), skip=(3,))
K.box(g, (1.5 - R, CY + R, WZ - 0.08), (1.5 + R, H, WZ + 0.08), PLASTER_LATH, (0.05, 0.05, 0.95, 0.95), skip=(3,))
for sx in (-1, 1):
    for zz, nz in ((WZ - 0.081, -1.0), (WZ + 0.081, 1.0)):
        pts = [(1.5 + sx * R, CY, zz), (1.5 + sx * R, CY + R, zz)]
        for a in np.linspace(math.pi / 2, 0, 5):
            pts.append((1.5 + sx * R * math.cos(a), CY + R * math.sin(a), zz))
        P = np.array(pts)
        Nn = np.tile([0.0, 0.0, nz], (len(P), 1))
        T = np.array([(1, k, k + 1) for k in range(2, len(P) - 1)] + [(0, 1, len(P) - 1)])
        UV = np.clip(0.1 + 0.4 * (P[:, :2] - P[:, :2].min(0)), 0, 1)
        g.add(Part(PLASTER_LATH, P, Nn, UV, fix_winding(P, Nn, T)))
# the timber rim of the moon gate, on both faces
ring = [(1.5 + math.cos(a) * R, CY + math.sin(a) * R) for a in np.linspace(-0.3, math.pi + 0.3, 13)]
for dz in (-0.09, 0.09):
    K.tube(g, [(x, y, WZ + dz) for x, y in ring], [0.05] * len(ring), TIMBER, sides=5, caps=False)
K.roof(g, 0.12, WZ - 0.1, 2.88, WZ + 0.1, H, H + 0.32, kind="gable", overhang=0.2, sag=0.03, lift=0.04,
       ridge_ends=0.05, tile=0.28, course=0.26)
# the yard behind: a rack of back-baskets, carrying poles, a bench
for x in (0.35, 1.0):
    K.pole(g, (x, B, 1.7), (x, 1.05, 1.7), r=0.03, material=BAMBOO_GOLD, sides=5, bend=0.0)
K.pole(g, (0.25, 0.95, 1.7), (1.1, 0.95, 1.7), r=0.025, material=BAMBOO_GOLD, sides=4, bend=0.0)
for k in range(3):
    K.basket(g, (0.45 + 0.27 * k, 0.45, 1.62), h=0.38, r=0.12, material=WEAVE_GOLD if k % 2 else WEAVE)
for k in range(3):
    K.pole(g, (1.9, B + 0.03 + 0.05 * k, 1.2 + 0.1 * k), (2.8, B + 0.03 + 0.05 * k, 1.25 + 0.1 * k), r=0.022,
           material=BAMBOO_GOLD, sides=4, bend=0.0)
K.boards(g, (1.8, 0.36, 1.7), (1, 0, 0), (0, 0, 1), 0.9, 0.2, 2, TIMBER, thick=0.03)
for x in (1.85, 2.7):
    K.beam(g, (x, B, 1.8), (x, 0.36, 1.8), w=0.04, caps=False)
for x in (0.75, 2.25):
    K.beam(g, (x, H - 0.04, WZ - 0.09), (x, H - 0.04, WZ - 0.24), w=0.03)
    K.lantern(g, (x, H - 0.06, WZ - 0.22), r=0.075, h=0.17)
PX, PZ, PH = 2.75, 0.72, 1.95
# the moon mark seen from the high camera: a glowing moon plaque on a bamboo pole above the roof, a crescent on top
K.pole(g, (PX, 0.0, PZ), (PX, PH + 0.55, PZ), r=0.035, material=BAMBOO_GOLD, sides=5, bend=0.005)
K.moon_window(g, (PX, PH + 0.2, PZ - 0.045), (0, 0, -1), r=0.2)
arc = [(PX + 0.13 * math.cos(t), PH + 0.65 + 0.13 * math.sin(t), PZ) for t in np.linspace(-1.9, 1.9, 7)]
K.tube(g, arc, [0.01, 0.025, 0.032, 0.035, 0.032, 0.025, 0.01], BAMBOO_GOLD, sides=5, caps=False)
m.blocks = solid_blocks(3, 2, 3)
m.entrance(1, -1, 0)
m.slot("Entrance", (1.5, B, 0.85), yaw=180)
m.extra["access"] = {"X": 1.5, "Y": B, "Z": 0.9}
m.collider((1.5, 0.85, WZ), (2.9, 1.6, 0.3))
m.collider((1.5, 0.5, 1.4), (2.9, 1.0, 1.0))
m.notes += ["Ringtail mark: the moon gate. Couriers walk through the round opening to the access point behind it."]
m.build()
