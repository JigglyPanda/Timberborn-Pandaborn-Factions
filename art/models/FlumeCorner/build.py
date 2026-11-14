"""Flume Corner: a 2x2 turning box, built as an open junction. Cell (0, 0) holds the water, open on its -x and -z
faces where flumes join; the other three cells are solid (water obstacles), here a low heap of dry-laid river
stones banked against the basin with a bamboo clump and a lantern post, so nothing reads as a closed crate.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, solid_blocks  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("FlumeCorner", size=(2, 2, 2), seed=53, stand_in="ThrottlingValve.Folktails")
g = m.geo
# the basin: a floor of flat stones, a kerb of stones on its two inner sides, split-culm lips on the open faces
K.box(g, (0.02, -0.02, 0.02), (0.98, 0.012, 0.98), EARTH, (0.05, 0.05, 0.95, 0.95), skip=(3,))
K.stones(g, 0.08, 0.08, 0.92, 0.92, y=0.0, size=0.22, h=0.03, ring=False, skip=0.15, tone=(0.45, 0.48, 0.45))
for (x0, z0, x1, z1) in ((0.98, 0.0, 1.1, 1.1), (0.0, 0.98, 1.1, 1.1)):
    K.stones(g, x0, z0, x1, z1, y=-0.01, size=0.2, h=0.4, ring=False, skip=0.0)
for (a, b) in (((0.0, 0.03, 0.04), (0.0, 0.03, 0.96)), ((0.04, 0.03, 0.0), (0.96, 0.03, 0.0))):
    K.tube(g, [a, b], [0.03, 0.03], BAMBOO_GOLD, sides=4)
for (x, z) in ((0.04, 0.04), (0.98, 0.04), (0.04, 0.98), (0.98, 0.98)):
    K.pole(g, (x, -0.02, z), (x, 1.6, z), r=0.04, material=BAMBOO_GOLD, sides=5, bend=0.0)
    K.lashing(g, (x, 0.32, z), (0, 1, 0), r=0.05)
# the cap block over the basin: a little four-post pavilion roof (the water module's obstacle sits inside it)
for (a, b) in (((0.0, 1.6, 0.04), (1.02, 1.6, 0.04)), ((0.0, 1.6, 0.98), (1.02, 1.6, 0.98))):
    K.beam(g, a, b, w=0.05)
K.roof(g, 0.04, 0.04, 0.98, 0.98, 1.6, 1.92, kind="pyramid", overhang=0.12, sag=0.04, lift=0.04, thick=0.05,
       tile=0.22, course=0.22)
# the solid L: two courses of rubble stones over an earth core, moss in the top
# (an earth core only under the moss, so the heap reads as stones, not a box)
K.box(g, (1.2, 0.0, 1.2), (1.95, 0.4, 1.95), EARTH, (0.02, 0.02, 0.98, 0.98), skip=(3,), tags={"base"})
K.stones(g, 1.12, 0.04, 1.96, 1.96, y=-0.01, size=0.28, h=0.26, skip=0.0, tags={"base"})
K.stones(g, 0.04, 1.12, 1.08, 1.96, y=-0.01, size=0.28, h=0.26, skip=0.0, tags={"base"})
K.stones(g, 1.16, 0.1, 1.9, 1.15, y=0.0, size=0.24, h=0.38, ring=False, skip=0.05, tags={"base"}, tone=(0.58, 0.6, 0.57))
K.stones(g, 0.1, 1.16, 1.15, 1.9, y=0.0, size=0.24, h=0.38, ring=False, skip=0.05, tags={"base"}, tone=(0.6, 0.6, 0.58))
K.box(g, (1.25, 0.41, 1.25), (1.9, 0.44, 1.9), MOSS, (0.05, 0.05, 0.95, 0.95), skip=(3,))
for k in range(7):
    x, z = 1.58 + 0.12 * np.cos(k * 1.3), 1.58 + 0.12 * np.sin(k * 1.3)
    top = (x + 0.16 * np.cos(k), 1.6 + 0.15 * (k % 3), z + 0.16 * np.sin(k))
    K.pole(g, (x, 0.42, z), top, r=0.022, material=BAMBOO_GREEN, sides=4, bend=0.04, segs=2)
K.beam(g, (0.55, 0.42, 1.55), (0.55, 1.0, 1.55), w=0.05)
K.beam(g, (0.55, 0.97, 1.55), (0.55, 0.97, 1.3), w=0.035)
K.lantern(g, (0.55, 0.95, 1.32), r=0.06, h=0.14)
m.blocks = solid_blocks(2, 2, 2)
m.extra["capCells"] = [{"X": 0, "Y": 0, "Z": 1}]
m.stage_height = 1.0
m.extra["waterCells"] = [{"X": 0, "Y": 0, "Z": 0}]
m.extra["solidCells"] = [{"X": 1, "Y": 0}, {"X": 0, "Y": 1}, {"X": 1, "Y": 1}]   # two blocks tall
m.collider((1.0, 0.25, 1.0), (2.0, 0.5, 2.0))
m.build()
