"""Flume Bridge: a flume piece one block up on a bamboo trestle. The water cell is (0, 0, 1) (floor at y = 1); the
lower cell is legs at the four corners only (Occupations 'Corners'), so a path can pass underneath.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
from building import Model, block  # noqa: E402
import waterworks as W  # noqa: E402

m = Model("FlumeBridge", size=(1, 1, 2), seed=43, stand_in="ThrottlingValve.Folktails")
g = m.geo
with g.tagged("frame"):
    W.leg_frame(g, 0.98, z_pairs=((0.1, 0.9),))
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
