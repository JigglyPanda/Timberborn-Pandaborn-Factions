"""Flume Gate: the intake of a flume. A flume cell under a timber sluice frame: two posts, a lintel, a plank gate
raised on a rope from a long bamboo lever with a stone counterweight; it caps the water at one block (lidded) and
sets the flow.
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
# the lever: a long bamboo arm pivoted on a post behind the gate, its front end on a rope to the board, a river
# stone lashed to its back end as the counterweight
K.beam(g, (0.5, -0.02, 0.86), (0.5, 1.3, 0.86), w=0.07, caps="end")
K.pole(g, (0.5, 1.42, 0.4), (0.5, 1.12, 1.25), r=0.026, material=BAMBOO_GOLD, sides=5, bend=0.0)
K.lashing(g, (0.5, 1.27, 0.84), (0, 0, 1), r=0.04)
K.beam(g, (0.5, 1.4, 0.42), (0.5, 0.6, Z), w=0.012, material=DETAILS, caps=False)
K.stones(g, 0.42, 1.12, 0.58, 1.3, y=0.98, size=0.16, h=0.15, ring=False)
# iron bands across the sluice board
for y in (0.3, 0.5):
    K.beam(g, (0.13, y, Z - 0.035), (0.87, y, Z - 0.035), w=0.02, material=IRON, caps=False)
m.blocks = [block("GroundOrStackable", "Bottom, Top, Corners, Path, Middle", "None")]
m.extra["waterCells"] = [{"X": 0, "Y": 0, "Z": 0}]
m.extra["flow"] = "along +Y (grid) for orientation Cw0; fixed inflow limit (0.3 in the water prototype)"
m.collider((0.5, 0.55, 0.5), (1.0, 1.1, 1.0))
m.build()
