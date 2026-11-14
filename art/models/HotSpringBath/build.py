"""Hot Spring Bath: a soak every few days. 3x3 on the vanilla Mud Pit (eight bathers: five on the rim, three
floating; the pit's surface node rises and falls with the stored supply and its bubbles become rising steam).

A round rock pool lined with river stones, its warm water a milky green-teal surface (lime sheet painted by vertex
colour) on the node the vanilla surface controller moves, a bamboo screen and a small tiled shelter on one side with
towels on a rail, a bamboo spout feeding the pool, wooden buckets and a red lantern.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, block  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("HotSpringBath", size=(3, 3, 1), seed=199, stand_in="MudPit.Folktails")
g = m.geo
C = np.array([1.45, 0.0, 1.55])
R = 1.12
# the pool basin: a dark lining below, a ring of big rim stones, the ground around it
K.lathe(g, [(R * 1.02, 0.18), (R * 0.95, 0.0), (R * 0.7, -0.1), (0.0, -0.12)], C, 16, EARTH,
        uv_region=(0.05, 0.05, 0.95, 0.95), cap_top=False)
for k in range(15):
    a = 2 * math.pi * k / 15 + 0.1
    p = C + np.array([math.cos(a) * (R + 0.12), 0.0, math.sin(a) * (R + 0.12)])
    K.stones(g, p[0] - 0.1, p[2] - 0.1, p[0] + 0.1, p[2] + 0.1, y=-0.02, size=0.34, h=0.26, ring=False, skip=0.0)
with g.node("#SpringWater"):
    K.lathe(g, [(R * 0.99, 0.0), (0.0, 0.0)], C + [0, 0.13, 0], 16, PLASTER, uv_region=(0.1, 0.1, 0.9, 0.9),
            cap_top=False)
    water = g.parts[-1]
    water.N[:] = (0, 1, 0)
    water.T = fix_winding(water.P, water.N, water.T)
    water.C = np.tile([0.5, 0.68, 0.64, 1.0], (len(water.P), 1))
    water.tags.add("noshade")
# the shelter and screen at the back right
for (x, z) in ((2.25, 2.3), (2.9, 2.3), (2.9, 2.95), (2.25, 2.95)):
    K.beam(g, (x, 0.0, z), (x, 1.05, z), w=0.06, caps="end")
K.roof(g, 2.2, 2.25, 2.95, 3.0, 1.05, 1.32, kind="pyramid", overhang=0.12, sag=0.03, lift=0.04, tile=0.24, course=0.26)
K.screen(g, (0.15, 2.95), (2.2, 2.95), 0.0, 0.9)
K.screen(g, (0.08, 2.9), (0.08, 1.6), 0.0, 0.8, material=WEAVE)
K.pole(g, (2.3, 0.62, 2.35), (2.85, 0.62, 2.35), r=0.02, material=BAMBOO_GOLD, sides=4, bend=0.0)
for k, reg in enumerate((DET_CLOTH, DET_SACK)):
    x = 2.4 + 0.25 * k
    K.cloth(g, [(x - 0.09, 0.3, 2.35), (x + 0.09, 0.3, 2.35), (x + 0.09, 0.62, 2.35), (x - 0.09, 0.62, 2.35)],
            DETAILS, reg, sag=0.0, nu=1, nv=1, wave=0.01)
# a bamboo spout feeding the pool from the back left, buckets, a lantern
K.channel(g, 2.75, 2.25, 0.32, 0.6, r_in=0.06, wall=0.018, material=BAMBOO_GREEN, around=4, sleeve=False, tilt=0.12)
K.pole(g, (0.6, 0.0, 2.7), (0.6, 0.5, 2.7), r=0.025, material=BAMBOO_GOLD, sides=4, bend=0.0)
for (x, z) in ((2.7, 0.35), (2.45, 0.25)):
    K.lathe(g, [(0.0, 0.0), (0.09, 0.0), (0.11, 0.15)], (x, 0.0, z), 7, TIMBER, cap_top=False, strips=[WOOD_BLOCK])
K.standing_lantern(g, (0.25, 0.0, 0.3), h=0.85)
# seats on the rim (sitting with feet in the water) and three floating spots in the middle
for i in range(5):
    a = math.pi * (0.95 + 0.3 * i)
    m.slot(f"Seat{i + 1}", tuple(C + [math.cos(a) * (R + 0.05), 0.15, math.sin(a) * (R + 0.05)]),
           yaw=math.degrees(math.atan2(-math.cos(a), -math.sin(a))))
for i, (dx, dz) in enumerate(((-0.35, 0.1), (0.3, -0.25), (0.2, 0.4))):
    m.slot(f"Floating{i + 1}", tuple(C + [dx, 0.12, dz]), yaw=60.0 * i)
m.animate("#SpringWater", C + [0, 0.13, 0], (0, 1, 0), kind="static",
          driver="GoodConsumingAttractionSurfaceControllerSpec.SurfaceName (rises and falls with the supply)")
m.extra["surfaceName"] = "#SpringWater"
m.attach("Bubbles", (C[0], 0.24, C[2]), "the vanilla bubbles rise from the pool centre as steam")
m.blocks = [block("GroundOrStackable", "Bottom, Corners, Path, Middle", "None") for _ in range(9)]
m.entrance(1, -1, 0)
m.extra["access"] = {"X": 1.5, "Y": 0.0, "Z": 0.35}
m.collider((1.5, 0.12, 1.5), (3.0, 0.25, 3.0))
m.collider((2.6, 0.6, 2.6), (0.8, 1.2, 0.8))
m.notes += ["GoodConsumingAttractionSurfaceControllerSpec.SurfaceName must be '#SpringWater' (surfaceName)."]
m.build()
