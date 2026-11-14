"""Flume Gate: the intake of a flume. A flume cell under a timber sluice frame: two posts, a lintel, a plank gate
raised on a rope over a little windlass, a counterweight stone; it caps the water at one block (lidded) and sets
the flow.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
from building import Model, block  # noqa: E402
import parts as K  # noqa: E402
import waterworks as W  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("FlumeGate", size=(1, 1, 1), seed=59, stand_in="ThrottlingValve.Folktails")
g = m.geo
W.straight(g, 0.0, 1.0, 0.0, material=BAMBOO_GOLD)
Z = 0.45
for x in (0.08, 0.92):
    K.beam(g, (x, -0.02, Z), (x, 1.12, Z), w=0.085, caps="end")
K.beam(g, (0.0, 1.06, Z), (1.0, 1.06, Z), w=0.09, h=0.08)
K.beam(g, (0.02, 0.62, Z), (0.98, 0.62, Z), w=0.06)
# the gate leaf, raised a little, sliding between the posts
K.boards(g, (0.14, 0.18, Z - 0.015), (0, 1, 0), (1, 0, 0), 0.4, 0.72, 3, TIMBER, thick=0.03)
K.beam(g, (0.5, 0.58, Z), (0.5, 1.05, Z), w=0.015, material=DETAILS, caps=False)
# windlass on the lintel with a crank
K.tube(g, [(0.2, 1.17, Z), (0.8, 1.17, Z)], [0.04, 0.04], TIMBER, sides=6)
K.beam(g, (0.82, 1.17, Z), (0.86, 1.06, Z - 0.1), w=0.02)
# counterweight stone on a rope at the side
K.beam(g, (0.95, 1.0, Z + 0.08), (0.95, 0.55, Z + 0.08), w=0.012, material=DETAILS, caps=False)
K.stones(g, 0.88, Z, 1.02, Z + 0.16, y=0.4, size=0.12, h=0.13, ring=False)
m.blocks = [block("GroundOrStackable", "Bottom, Top, Corners, Path, Middle", "None")]
m.extra["waterCells"] = [{"X": 0, "Y": 0, "Z": 0}]
m.extra["flow"] = "along +Y (grid) for orientation Cw0; fixed inflow limit (0.3 in the water prototype)"
m.collider((0.5, 0.55, 0.5), (1.0, 1.1, 1.0))
m.build()
