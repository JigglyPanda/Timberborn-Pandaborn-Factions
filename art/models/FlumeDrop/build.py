"""Flume Drop: steps a flume down one level as a little cascade. Water enters the upper cell (0, 0, 1) and pours into
the lower cell (0, 1, 0) one tile further along; the cell under the upper half (0, 0, 0) is solid, as in the water
prototype's sealed drop.

The upper culm runs out over a dry-stone step and narrows into a lipped spout that overhangs the lower run; under it
a stone splash basin, and the lower culm carries on from there.
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
# the solid step: rammed-earth core faced with two courses of dry-laid river stones
K.box(g, (0.1, 0.0, 0.04), (0.9, 0.96, 0.96), EARTH, (0.02, 0.02, 0.98, 0.98), skip=(3,), tags={"base"})
K.stones(g, 0.08, 0.04, 0.92, 0.96, y=-0.01, size=0.3, h=0.46, skip=0.0, tags={"base"})
K.stones(g, 0.1, 0.06, 0.9, 0.94, y=0.44, size=0.28, h=0.44, skip=0.1, tags={"base"}, tone=(0.58, 0.6, 0.58))
# upper culm, then a narrowing spout tipping down over the lower run
W.straight(g, 0.0, 0.96, 1.0, tilt=0.03, nodes=(0.45,))
K.channel(g, 0.92, 1.3, 0.93, 0.5, r_in=0.16, wall=0.03, material=BAMBOO_GREEN, around=5, sleeve=False, tilt=0.12)
K.lashing(g, (0.5, 1.05, 0.96), (0, 0, 1), r=0.2)
# splash basin of flat stones where the water lands, and the lower run
K.stones(g, 0.16, 1.02, 0.84, 1.4, y=-0.02, size=0.2, h=0.05, ring=False, skip=0.0, tone=(0.52, 0.54, 0.52))
W.straight(g, 1.0, 2.0, 0.0, sleeve=False, nodes=(0.55,))
W.x_stakes(g, 1.75, y_top=0.56)
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
