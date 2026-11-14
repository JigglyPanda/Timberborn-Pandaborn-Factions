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

m = Model("FlumeGate", size=(1, 1, 2), seed=59, stand_in="ThrottlingValve.Folktails")
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
# the lever (its silhouette tells the gate from every other flume piece at game zoom): a tall post at the back of the
# cell and a long sweep pole pivoted on it, its high front end on a rope to the sluice board, a net of river stones
# hanging from its low back end as the counterweight
K.beam(g, (0.5, -0.02, 0.95), (0.5, 2.25, 0.95), w=0.08, caps="end")
for sx in (-1, 1):
    K.beam(g, (0.5 + sx * 0.3, -0.02, 0.98), (0.5, 1.2, 0.95), w=0.04, caps=False)
PV = (0.5, 2.15, 0.95)
K.pole(g, (0.5, 2.75, 0.12), (0.5, 1.82, 1.55), r=0.032, material=BAMBOO_GOLD, sides=5, bend=0.0)
K.lashing(g, PV, (0, 0, 1), r=0.05)
K.beam(g, (0.5, 2.73, 0.13), (0.5, 0.6, Z - 0.01), w=0.012, material=DETAILS, caps=False)
K.beam(g, (0.5, 1.84, 1.52), (0.5, 1.45, 1.52), w=0.012, material=DETAILS, caps=False)
K.stones(g, 0.38, 1.4, 0.62, 1.64, y=1.2, size=0.2, h=0.24, ring=False)
# iron bands across the sluice board
for y in (0.3, 0.5):
    K.beam(g, (0.13, y, Z - 0.035), (0.87, y, Z - 0.035), w=0.02, material=IRON, caps=False)
# the cap block (0, 0, 1): the gate posts run on up to a small tiled hood over the sluice, so the water module's
# obstacle over the channel is inside the building and a backed-up line cannot run over the top
for x in (0.08, 0.92):
    K.beam(g, (x, 1.1, Z), (x, 1.45, Z), w=0.07, caps=False)
    K.beam(g, (x, 1.1, 0.12), (x, 1.45, 0.12), w=0.05, caps=False)
K.beam(g, (0.04, 1.45, 0.1), (0.04, 1.45, 0.82), w=0.05)
K.beam(g, (0.96, 1.45, 0.1), (0.96, 1.45, 0.82), w=0.05)
K.roof(g, 0.04, 0.08, 0.96, 0.82, 1.45, 1.66, kind="gable", axis="z", overhang=0.08, sag=0.03, lift=0.03, thick=0.05,
       tile=0.2, course=0.2, ridge_ends=0.04)
m.blocks = [block("GroundOrStackable", "Bottom, Top, Corners, Path, Middle", "None"),
            block("Any", "Bottom, Top, Corners, Path, Middle", "None")]
m.extra["capCells"] = [{"X": 0, "Y": 0, "Z": 1}]
m.extra["waterCells"] = [{"X": 0, "Y": 0, "Z": 0}]
m.extra["flow"] = "along +Y (grid) for orientation Cw0; fixed inflow limit (0.3 in the water prototype)"
m.collider((0.5, 0.55, 0.5), (1.0, 1.1, 1.0))
m.collider((0.5, 1.55, 0.45), (1.0, 0.25, 0.8))
m.stage_height = 1.0
m.build()
