"""Cistern (large): the village's great dark-glazed stoneware vat, 3x3x3 on the vanilla Large Tank (liquid plane 0.57
to 2.45), on a stone plinth, a planked lid over the back third with a small grey-tile shelter and windlass over it, a
bamboo stair up the front and a stone trough at its foot.
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
H = 2.5
W.vat(g, 1.5, 1.5, 1.44, H, floor=0.56, glaze=W.GLAZE_BROWN, sides=16, lid=0.33, plinth=0.18)
for x in (1.05, 1.95):
    for z in (2.45, 2.85):
        K.beam(g, (x, H + 0.06, z), (x, H + 0.66, z), w=0.06)
K.roof(g, 1.05, 2.45, 1.95, 2.85, H + 0.66, H + 0.94, kind="gable", overhang=0.12, sag=0.03, lift=0.03,
       ridge_ends=0.04, tile=0.24, course=0.26)
K.tube(g, [(1.08, H + 0.46, 2.65), (1.92, H + 0.46, 2.65)], [0.05, 0.05], TIMBER, sides=6)
K.beam(g, (1.5, H + 0.44, 2.62), (1.5, H - 0.3, 2.25), w=0.012, material=DETAILS, caps=False)
K.lathe(g, [(0.0, 0.0), (0.08, 0.0), (0.1, 0.14)], (1.5, H - 0.44, 2.23), 7, TIMBER, cap_top=False)
K.stairs(g, (1.5, 0.0, -0.14), (1.5, H + 0.05, 0.28), width=0.45, steps=8, material=BAMBOO_GOLD)
K.box(g, (2.3, 0.0, 0.02), (2.95, 0.3, 0.42), PLASTER, (0.1, 0.1, 0.9, 0.9), skip=(3,), tags={"stone"})
g.parts[-1].C = np.tile([0.6, 0.6, 0.57, 1.0], (len(g.parts[-1].P), 1))
m.blocks = solid_blocks(3, 3, 3)
m.entrance(1, -1, 0)
m.extra["access"] = {"X": 1.5, "Y": 0.0, "Z": 0.2}
m.extra["liquidPlane"] = "vanilla LargeTank StockpilePlaneVisualizer (3x3): y 0.566 to 2.45; mouth radius 1.24"
m.collider((1.5, 1.3, 1.5), (2.9, 2.6, 2.9))
m.notes += ["Entrance and access as the vanilla Large Tank (front middle cell)."]
m.build()
