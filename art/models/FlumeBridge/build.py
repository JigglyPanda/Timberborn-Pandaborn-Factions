"""Flume Bridge: a flume piece one block up on a bamboo trestle. The water cell is (0, 0, 1) (floor at y = 1); the
lower cell holds two lashed bamboo X-trestles at the cell's front and back edges (Occupations 'Corners'), so a
path can still pass underneath across the trestles.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
from building import Model, block  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403
import waterworks as W  # noqa: E402

m = Model("FlumeBridge", size=(1, 1, 2), seed=43, stand_in="ThrottlingValve.Folktails")
g = m.geo
# two X-trestles of lashed bamboo at the cell's front and back edges, a head beam under the channel on each
with g.tagged("frame"):
    for z in (0.1, 0.9):
        for (xa, xb) in ((0.02, 0.98), (0.98, 0.02)):
            K.pole(g, (xa, -0.02, z), (xb + (0.06 if xb < 0.5 else -0.06), 1.06, z), r=0.034, material=BAMBOO_GOLD,
                   sides=5, bend=0.01)
        K.lashing(g, (0.5, 0.5, z), (0, 0, 1), r=0.05)
        K.beam(g, (-0.02, 0.97, z), (1.02, 0.97, z), w=0.07)
        for x in (0.1, 0.9):
            K.lashing(g, (x, 0.95, z), (1, 0, 0), r=0.045)
W.straight(g, 0.0, 1.0, 1.0)
m.blocks = [block("GroundOrStackable", "Corners", "None"),
            block("Any", "Bottom, Top, Corners, Path, Middle", "None")]
m.extra["waterCells"] = [{"X": 0, "Y": 0, "Z": 1}]
m.extra["flow"] = "along +Y (grid) for orientation Cw0"
m.stage_height = 1.0
m.collider((0.5, 1.2, 0.5), (0.9, 0.45, 1.0))
m.collider((0.5, 0.5, 0.5), (1.0, 1.0, 1.0))
m.notes += ["Walk-under: the lower block only occupies Corners, as the vanilla DoublePlatform's lower block."]
m.build()
