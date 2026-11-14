"""Flume Corner: a 2x2 turning box. Cell (0, 0) holds the water (open on its -x and -z faces, where flumes join);
the other three cells are solid: a low rammed-earth block paved with river stones, a potted bamboo clump in moss and a
lantern on it.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, solid_blocks  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("FlumeCorner", size=(2, 2, 1), seed=53, stand_in="ThrottlingValve.Folktails")
g = m.geo
# the basin: a squat timber tub in cell (0,0), walls on its two inner sides, open mouths on -x and -z
H = 0.42
K.box(g, (0.02, -0.02, 0.02), (0.98, 0.012, 0.98), TIMBER, WOOD_BLOCK, skip=(3,))
for (lo, hi) in (((0.96, 0.0, 0.0), (1.06, H, 1.06)), ((0.0, 0.0, 0.96), (0.96, H, 1.06))):
    K.box(g, lo, hi, TIMBER, WOOD_STRIPS[2], skip=(3,))
for x, z in ((0.02, 0.02), (1.0, 0.02), (0.02, 1.0)):
    K.beam(g, (x, 0.0, z), (x, H + 0.08, z), w=0.07)
# mouths: bamboo lips where the flumes slot in
K.beam(g, (0.0, 0.02, 0.06), (0.0, 0.02, 0.94), w=0.05, material=BAMBOO_GOLD)
K.beam(g, (0.06, 0.02, 0.0), (0.94, 0.02, 0.0), w=0.05, material=BAMBOO_GOLD)
# the solid L: rammed earth faced with stones, a potted bamboo and a lantern on top
for lo, hi in (((1.06, 0.0, 0.0), (2.0, 0.62, 2.0)), ((0.0, 0.0, 1.06), (1.06, 0.62, 2.0))):
    K.box(g, lo, hi, EARTH, (0.02, 0.02, 0.98, 0.98), skip=(2, 3), tags={"base"})
    K.box(g, (lo[0] + 0.02, 0.6, lo[2] + 0.02), (hi[0] - 0.02, 0.62, hi[2] - 0.02), EARTH, (0.05, 0.05, 0.95, 0.95),
          skip=(3,))
# a paving of big river stones on top, moss in the gaps round the bamboo
K.stones(g, 1.12, 0.06, 1.94, 0.98, y=0.6, size=0.22, h=0.06, ring=False, skip=0.1, tone=(0.66, 0.66, 0.63))
K.stones(g, 0.06, 1.12, 0.98, 1.94, y=0.6, size=0.22, h=0.06, ring=False, skip=0.1, tone=(0.66, 0.66, 0.63))
K.box(g, (1.2, 0.61, 1.2), (1.92, 0.65, 1.92), MOSS, (0.05, 0.05, 0.95, 0.95), skip=(3,))
K.stones(g, 1.1, 0.04, 1.96, 1.96, y=-0.01, size=0.25, h=0.2, tags={"base"})
K.stones(g, 0.04, 1.1, 1.0, 1.96, y=-0.01, size=0.25, h=0.2, tags={"base"})
K.lathe(g, [(0.0, 0.0), (0.16, 0.0), (0.2, 0.2), (0.22, 0.22)], (1.55, 0.62, 1.5), 7, EARTH, cap_top=True)
for k in range(7):
    x, z = 1.55 + 0.09 * np.cos(k * 1.3), 1.5 + 0.09 * np.sin(k * 1.3)
    top = (x + 0.12 * np.cos(k), 1.5 + 0.18 * (k % 3), z + 0.12 * np.sin(k))
    K.pole(g, (x, 0.8, z), top, r=0.02, material=BAMBOO_GREEN, sides=4, bend=0.04, segs=2)
# a few river stones set in the moss and a bamboo ladle resting on the basin wall
K.pole(g, (0.3, H + 0.02, 1.0), (0.9, H + 0.05, 1.01), r=0.015, material=BAMBOO_GOLD, sides=4, bend=0.0)
K.lathe(g, [(0.0, 0.0), (0.05, 0.0), (0.05, 0.06)], (0.27, H - 0.02, 1.0), 6, BAMBOO_GOLD, cap_top=False)
K.beam(g, (0.55, 0.62, 1.6), (0.55, 1.05, 1.6), w=0.05)
K.beam(g, (0.55, 1.02, 1.6), (0.55, 1.02, 1.36), w=0.035)
K.lantern(g, (0.55, 1.0, 1.38), r=0.06, h=0.14)
m.blocks = solid_blocks(2, 2, 1)
m.extra["waterCells"] = [{"X": 0, "Y": 0, "Z": 0}]
m.extra["solidCells"] = [{"X": 1, "Y": 0}, {"X": 0, "Y": 1}, {"X": 1, "Y": 1}]
m.collider((1.0, 0.31, 1.0), (2.0, 0.62, 2.0))
m.build()
