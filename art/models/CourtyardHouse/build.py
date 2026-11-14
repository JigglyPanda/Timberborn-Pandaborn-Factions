"""Courtyard House: the larger Sichuan farmstead home. 2x2x2 on the Double Lodge's dwelling (six beds), entered at
ground level through a courtyard gate.

An L of two tiled wings around a tiny courtyard: the main hall along the back, two storeys, its upper gallery under
the eave; a lower side wing on the right; a whitewashed courtyard wall with a round gate at the front left; a water
jar, a persimmon-coloured lantern and a bamboo drying rack in the courtyard.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, solid_blocks  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("CourtyardHouse", size=(2, 2, 2), seed=131, stand_in="DoubleLodge.Folktails")
g = m.geo
B = 0.1
K.plinth(g, 0.04, 0.05, 1.96, 1.95, h=B)
# main hall along the back: two storeys, gallery under the front eave
MZ0, MZ1, MTOP, MRIDGE = 1.0, 1.85, 1.3, 1.95
with g.tagged("walls"):
    K.wall(g, (0.12, MZ0), (1.88, MZ0), B, 0.68, openings=[("door", 0.3, 0.32, 0.0, 0.52), ("window", 0.7, 0.3, 0.2, 0.46)])
    K.wall(g, (0.12, MZ0 + 0.06), (1.88, MZ0 + 0.06), 0.68, MTOP, openings=[("panes", 0.3, 0.36, 0.14, 0.4),
                                                                      ("panes", 0.72, 0.36, 0.14, 0.4)], rail=False)
    K.wall(g, (1.88, MZ1), (0.12, MZ1), B, MTOP)
    K.wall(g, (0.12, MZ1), (0.12, MZ0), B, MTOP, openings=[("window", 0.5, 0.26, 0.85, 1.05)])
    K.gable_end(g, 0.12, MZ0, MZ1, MTOP, MRIDGE, outward=-1)
    K.gable_end(g, 1.88, MZ0, MZ1, MTOP, MRIDGE, outward=1)
K.boards(g, (0.08, 0.68, MZ0 - 0.22), (1, 0, 0), (0, 0, 1), 1.84, 0.24, 2, TIMBER, thick=0.03)
K.beam(g, (0.08, 0.92, MZ0 - 0.2), (1.92, 0.92, MZ0 - 0.2), w=0.035)
for x in (0.12, 0.7, 1.3, 1.88):
    K.beam(g, (x, 0.7, MZ0 - 0.2), (x, 0.93, MZ0 - 0.2), w=0.03, caps=False)
K.roof(g, 0.12, MZ0, 1.88, MZ1, MTOP, MRIDGE, kind="gable", overhang=0.22, sag=0.08, lift=0.05, ridge_ends=0.07)
# side wing on the right, lower, ridge running front to back
SX0, SX1 = 1.1, 1.88
with g.tagged("walls"):
    K.wall(g, (SX0, 0.18), (SX1, 0.18), B, 0.9, openings=[("window", 0.5, 0.32, 0.25, 0.55)])
    K.wall(g, (SX0, MZ0), (SX0, 0.18), B, 0.9, openings=[("door", 0.45, 0.3, 0.0, 0.56)])
K.roof(g, SX0, 0.18, SX1, MZ0, 0.9, 1.35, kind="gable", axis="z", overhang=0.18, sag=0.06, lift=0.04, ridge_ends=0.05,
       tile=0.28, course=0.32)
# courtyard wall with a round gate, front left
CW = 0.1
K.box(g, (0.08, B, 0.08), (0.22, 0.62, 0.95), PLASTER, (0.1, 0.1, 0.9, 0.9), skip=(3,))
for (x0, x1) in ((0.08, 0.3), (0.72, 1.1)):
    K.box(g, (x0, B, 0.08), (x1, 0.62, 0.08 + CW), PLASTER, (0.1, 0.1, 0.9, 0.9), skip=(3,))
K.box(g, (0.3, 0.5, 0.08), (0.72, 0.62, 0.08 + CW), PLASTER, (0.1, 0.1, 0.9, 0.9), skip=(3,))
for (x0, x1, z0, z1) in ((0.06, 1.12, 0.06, 0.2), (0.06, 0.24, 0.06, 0.97)):
    K.box(g, (x0, 0.62, z0), (x1, 0.67, z1), TILE, (0.0, TILE_COURSES[0][0], 0.3, TILE_COURSES[0][1]), skip=(3,))
K.lathe(g, [(0.2, 0.0), (0.21, 0.4)], (0.51, B, 0.13), 10, TIMBER, cap_top=False, axis=(0, 0, 1))
# the courtyard: water jar, drying rack, lantern by the hall door
K.jar(g, (0.38, B, 0.75), h=0.26, r=0.1)
for x in (0.55, 0.95):
    K.pole(g, (x, B, 0.45), (x, 0.62, 0.45), r=0.018, material=BAMBOO_GOLD, sides=4, bend=0.0)
K.pole(g, (0.5, 0.6, 0.45), (1.0, 0.6, 0.45), r=0.015, material=BAMBOO_GOLD, sides=4, bend=0.0, caps=False)
K.cloth(g, [(0.62, 0.36, 0.45), (0.88, 0.36, 0.45), (0.88, 0.6, 0.45), (0.62, 0.6, 0.45)], DETAILS, DET_CLOTH, sag=0.0,
        nu=1, nv=1, wave=0.01)
K.lantern(g, (0.25, MTOP - 0.12, MZ0 - 0.28), r=0.06, h=0.14)
K.chilli_string(g, (1.5, 0.66, MZ0 - 0.24), length=0.3, n=5)
cells = solid_blocks(2, 2, 2)
m.blocks = cells
m.entrance(0, -1, 0)
m.extra["access"] = {"X": 0.5, "Y": B, "Z": 0.55}
m.collider((1.0, 0.65, 1.42), (1.9, 1.3, 0.9))
m.collider((1.5, 0.5, 0.6), (0.8, 1.0, 0.85))
m.notes += ["Six beds as the Double Lodge, but entered at ground level through the courtyard gate (the vanilla "
            "Double Lodge enters at z = 1) and not stackable: the second block holds the tiled roofs."]
m.build()
