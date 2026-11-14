"""Cistern (small): a great dark-brown glazed stoneware jar in the Sichuan pickle-jar tradition on a stone plinth,
a planked lid over half its mouth, a bamboo ladle hooked on the rim. 1x1x2 on the vanilla Small Tank; the stored
water's surface (StockpilePlaneVisualizer, 0.55 to 1.42) shows in the open half of the mouth.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, solid_blocks  # noqa: E402
import parts as K  # noqa: E402
import waterworks as W  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("Cistern", size=(1, 1, 2), seed=71, stand_in="SmallTank.Folktails")
g = m.geo
W.vat(g, 0.5, 0.5, 0.46, 1.46, floor=0.54, glaze=W.GLAZE_BROWN, sides=12, lid=0.45, plinth=0.12)
K.pole(g, (0.18, 1.5, 0.3), (0.62, 1.56, 0.12), r=0.014, material=BAMBOO_GOLD, sides=4, bend=0.0)
K.lathe(g, [(0.0, 0.0), (0.05, 0.0), (0.055, 0.08)], (0.16, 1.43, 0.31), 6, BAMBOO_GREEN, cap_top=False)
m.blocks = None
m.extra["access"] = {"X": 0.5, "Y": 0.0, "Z": 0.1}
m.extra["liquidPlane"] = "vanilla SmallTank StockpilePlaneVisualizer: y 0.546 to 1.42; mouth radius 0.37, front half open"
m.collider((0.5, 0.75, 0.5), (0.95, 1.5, 0.95))
m.notes += ["Blocks as the vanilla Small Tank (1x1x2)."]
m.build()
