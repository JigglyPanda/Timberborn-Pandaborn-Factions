"""Cistern (large): water storage on the vanilla Large Tank (3x3x3, liquid plane rising 0.57 to 2.45).

The village's great cistern: a broad round stone-footed, plastered vessel with a timber rim, a small grey-tile roof on
four posts over a windlass at the back edge (rope and bucket hanging into the water), a bamboo stair up the front,
and a stone trough at its foot.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, solid_blocks  # noqa: E402
import parts as K  # noqa: E402
import waterworks as W  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("CisternLarge", size=(3, 3, 3), seed=127, stand_in="LargeTank.Folktails")
g = m.geo
CX, CZ, R, H = 1.5, 1.5, 1.42, 2.5
W.cistern_vessel(g, CX, CZ, R, H, floor=0.52, sides=16)
# windlass shelter on the back rim
for x in (1.05, 1.95):
    for z in (2.55, 2.95):
        K.beam(g, (x, H, z), (x, H + 0.62, z), w=0.06)
K.roof(g, 1.05, 2.55, 1.95, 2.95, H + 0.62, H + 0.9, kind="gable", overhang=0.12, sag=0.03, lift=0.03,
       ridge_ends=0.04, tile=0.24, course=0.26)
K.tube(g, [(1.08, H + 0.42, 2.75), (1.92, H + 0.42, 2.75)], [0.05, 0.05], TIMBER, sides=6)
K.beam(g, (1.5, H + 0.4, 2.72), (1.5, H - 0.35, 2.3), w=0.012, material=DETAILS, caps=False)
K.lathe(g, [(0.0, 0.0), (0.08, 0.0), (0.1, 0.14)], (1.5, H - 0.49, 2.28), 7, TIMBER, cap_top=False)
# stair up the front
K.stairs(g, (1.5, 0.0, -0.12), (1.5, H + 0.05, 0.3), width=0.45, steps=8, material=BAMBOO_GOLD)
# stone trough at the foot, right side
K.box(g, (2.35, 0.0, 0.05), (2.95, 0.3, 0.45), PLASTER, (0.1, 0.1, 0.9, 0.9), skip=(3,), tags={"stone"})
g.parts[-1].C = np.tile([0.6, 0.6, 0.57, 1.0], (len(g.parts[-1].P), 1))
m.blocks = solid_blocks(3, 3, 3)
m.entrance(1, -1, 0)
m.extra["access"] = {"X": 1.5, "Y": 0.0, "Z": 0.2}
m.extra["liquidPlane"] = "vanilla LargeTank StockpilePlaneVisualizer (3x3): y 0.566 to 2.45; mouth radius 1.33"
m.collider((1.5, 1.3, 1.5), (2.9, 2.6, 2.9))
m.notes += ["Entrance and access as the vanilla Large Tank (front middle cell)."]
m.build()
