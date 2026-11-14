"""Cistern (medium): water storage on the vanilla Medium Tank (2x2x3, liquid plane rising 0.55 to 2.3).

A round village cistern: river-stone foot, rammed-earth lower wall, lime-plastered upper wall with cane hoops and a
dark timber rim, open to the sky so the stored water shows; a bamboo ladder up the front, a woven cover over a third
of the mouth, a split-bamboo spout with a bucket on a hook.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, solid_blocks  # noqa: E402
import parts as K  # noqa: E402
import waterworks as W  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("CisternMedium", size=(2, 2, 3), seed=113, stand_in="MediumTank.Folktails")
g = m.geo
CX, CZ, R, H = 1.0, 1.0, 0.94, 2.36
W.cistern_vessel(g, CX, CZ, R, H, floor=0.5)
# ladder up the front-left, a woven cover over the back third of the mouth
K.ladder(g, (0.42, 0.0, 0.0), (0.5, H + 0.12, 0.2), width=0.32, rungs=7)
K.lathe(g, [(0.0, 0.0), (R * 0.45, 0.0), (R * 0.47, 0.03)], (0.0, 0.0, 0.0), 8, WEAVE_GOLD, cap_top=False)
cover = g.parts[-1]
cover.P = cover.P + np.array([CX + 0.35, H + 0.04, CZ + 0.4])
# spout and bucket at the front right
K.channel(g, 0.12, -0.18, 0.62, 1.55, r_in=0.07, wall=0.02, material=BAMBOO_GREEN, around=4, sleeve=False, tilt=0.04)
K.lathe(g, [(0.0, 0.0), (0.09, 0.0), (0.11, 0.16)], (1.55, 0.0, -0.12), 7, TIMBER, cap_top=False)
K.lathe(g, [(0.1, 0.07), (0.115, 0.08), (0.1, 0.09)], (1.55, 0.0, -0.12), 7, BAMBOO_GOLD, cap_top=False)
m.blocks = solid_blocks(2, 2, 3)
m.entrance(0, -1, 0)
m.extra["access"] = {"X": 0.5, "Y": 0.0, "Z": 0.15}
m.extra["liquidPlane"] = "vanilla MediumTank StockpilePlaneVisualizer (2x2): y 0.546 to 2.3; mouth radius 0.85"
m.collider((1.0, 1.2, 1.0), (1.9, 2.4, 1.9))
m.notes += ["Entrance and access as the vanilla Medium Tank (front-left cell)."]
m.build()
