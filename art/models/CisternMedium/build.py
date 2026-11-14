"""Cistern (medium): a celadon-grey glazed stoneware vat on a stone plinth, 2x2x3 on the vanilla Medium Tank (liquid
plane 0.55 to 2.3), a planked lid over the back of the mouth, a bamboo ladder up the front, a bucket at its foot.
"""
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
W.vat(g, 1.0, 1.0, 0.96, 2.36, floor=0.52, glaze=W.GLAZE_CELADON, sides=14, lid=0.4, plinth=0.16)
K.ladder(g, (0.42, 0.0, -0.04), (0.5, 2.46, 0.2), width=0.32, rungs=8)
K.lathe(g, [(0.0, 0.0), (0.09, 0.0), (0.11, 0.16)], (1.62, 0.0, 0.0), 7, TIMBER, cap_top=False)
K.lathe(g, [(0.1, 0.07), (0.115, 0.08), (0.1, 0.09)], (1.62, 0.0, 0.0), 7, BAMBOO_GOLD, cap_top=False)
m.blocks = solid_blocks(2, 2, 3)
m.entrance(0, -1, 0)
m.extra["access"] = {"X": 0.5, "Y": 0.0, "Z": 0.15}
m.extra["liquidPlane"] = "vanilla MediumTank StockpilePlaneVisualizer (2x2): y 0.546 to 2.3; mouth radius 0.8"
m.collider((1.0, 1.2, 1.0), (1.95, 2.4, 1.95))
m.notes += ["Entrance and access as the vanilla Medium Tank (front-left cell)."]
m.build()
