"""Flume Drop: steps a flume down one level. Water enters the upper cell (0, 0, 1) and pours into the lower cell
(0, 1, 0) one tile further along; the cell under the upper half (0, 0, 0) is solid (a rammed-earth block faced with
river stones), as in the water prototype's sealed drop.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
from building import Model, block  # noqa: E402
import parts as K  # noqa: E402
import waterworks as W  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("FlumeDrop", size=(1, 2, 2), seed=47, stand_in="ThrottlingValve.Folktails")
g = m.geo
# the solid block under the upper channel
K.box(g, (0.06, 0.0, 0.02), (0.94, 0.96, 0.98), EARTH, (0.02, 0.02, 0.98, 0.98), skip=(3,), tags={"base"})
K.stones(g, 0.08, 0.04, 0.92, 0.96, y=-0.01, size=0.24, h=0.22, tags={"base"})
# upper channel, tipping down at its end
W.straight(g, 0.0, 1.08, 1.0, tilt=0.06)
# lower channel and a splash board where the water lands
W.straight(g, 1.0, 2.0, 0.0, sleeve=False)
K.box(g, (0.1, 0.0, 0.98), (0.9, 0.12, 1.06), TIMBER, WOOD_STRIPS[2])
for x in (0.12, 0.88):
    K.pole(g, (x, 0.0, 1.12), (x, 1.05, 1.1), r=0.03, material=BAMBOO_GOLD, sides=5, bend=0.01)
K.pole(g, (0.08, 1.0, 1.1), (0.92, 1.0, 1.1), r=0.024, material=BAMBOO_GOLD, sides=4, bend=0.0)
W.stakes(g, 1.82)
m.blocks = [block("GroundOrStackable", "Bottom, Top, Corners, Path, Middle", "None"),
            block("GroundOrStackable", "Bottom, Top, Corners, Path, Middle", "None"),
            block("Any", "Bottom, Top, Corners, Path, Middle", "None"),
            block("Any", "None", "None")]
m.extra["waterCells"] = [{"X": 0, "Y": 0, "Z": 1}, {"X": 0, "Y": 1, "Z": 0}]
m.extra["solidCells"] = [{"X": 0, "Y": 0}]
m.stage_height = 1.0
m.collider((0.5, 0.65, 0.5), (0.9, 1.3, 1.0))
m.collider((0.5, 0.2, 1.5), (0.9, 0.4, 1.0))
m.build()
