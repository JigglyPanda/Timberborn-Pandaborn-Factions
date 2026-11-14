"""Flume: an open split-bamboo channel one tile wide, on the ground. Water runs one way along +z (the grid's +Y),
in the single water cell whose floor is the ground; the channel's inner floor sits on it so the water shows.

A green giant-bamboo half-pipe held by a pair of lashed stakes with a tie across, a rope sleeve at the upstream end so a run of
pieces reads as nested in the direction of flow.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
from building import Model, block  # noqa: E402
import waterworks as W  # noqa: E402

m = Model("Flume", size=(1, 1, 1), seed=41, stand_in="ThrottlingValve.Folktails")
g = m.geo
W.stakes(g, 0.82)
W.straight(g, 0.0, 1.0, 0.0)
m.blocks = [block("GroundOrStackable", "Bottom, Top, Corners, Path, Middle", "None")]
m.extra["waterCells"] = [{"X": 0, "Y": 0, "Z": 0}]
m.extra["flow"] = "along +Y (grid) for orientation Cw0; upstream end at Y = 0"
m.collider((0.5, 0.2, 0.5), (0.9, 0.4, 1.0))
m.notes += ["Inner channel floor at y = 0.012, rims at about 0.36: water up to that depth shows in the channel."]
m.build()
