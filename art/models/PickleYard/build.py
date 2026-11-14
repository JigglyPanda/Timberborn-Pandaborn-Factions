"""Pickle Yard: one cabbage makes several jars of pickles. 2x3, one worker, on the vanilla Bakery's workshop
blueprint (smoke attachment moved to the brine stove's flue).

A yard of big glazed pickle jars in rows, their mouths tied over in red cloth, cabbages drying on a bamboo rack, a worktable
with a knife and a heap of cabbages, and at the back a small plastered shed with a grey-tile gable roof, a lattice
window and a brine stove whose flue smokes.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, solid_blocks  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("PickleYard", size=(2, 3, 2), seed=103, stand_in="Bakery.Folktails")
g = m.geo
B = 0.08
K.plinth(g, 0.04, 0.05, 1.96, 2.95, h=B)
# back shed
SZ0, SZ1 = 1.75, 2.85
with g.tagged("walls"):
    K.wall(g, (0.12, SZ0), (1.88, SZ0), B, 1.05, openings=[("door", 0.3, 0.34, 0.0, 0.62), ("window", 0.72, 0.34, 0.32, 0.6)])
    K.wall(g, (1.88, SZ0), (1.88, SZ1), B, 1.05)
    K.wall(g, (1.88, SZ1), (0.12, SZ1), B, 1.05)
    K.wall(g, (0.12, SZ1), (0.12, SZ0), B, 1.05)
    K.gable_end(g, 0.12, SZ0, SZ1, 1.05, 1.55, outward=-1)
    K.gable_end(g, 1.88, SZ0, SZ1, 1.05, 1.55, outward=1)
K.roof(g, 0.12, SZ0, 1.88, SZ1, 1.05, 1.55, kind="gable", overhang=0.18, sag=0.06, lift=0.05, ridge_ends=0.06,
       tile=0.28, course=0.3)
K.tube(g, [(1.55, 1.0, 2.55), (1.57, 1.8, 2.6)], [0.07, 0.06], EARTH, sides=6)
SMOKE = (1.57, 1.82, 2.6)
GLAZE = [0.3, 0.2, 0.13, 1.0]
# big brown pickle jars in rows, each with its mouth tied over in red cloth (from the game camera: a yard of fat brown
# jars with red tops, the Pickle Yard's mark), a stone weight on some
for row, z in enumerate((0.42, 0.98)):
    for col, x in enumerate((0.36, 0.92, 1.5)):
        h = 0.5 + 0.05 * ((row + col) % 2)
        r = 0.23
        prof = [(r * 0.62, 0.0), (r, h * 0.42), (r * 0.92, h * 0.78), (r * 0.6, h * 0.95), (r * 0.62, h)]
        n0 = len(g.parts)
        K.lathe(g, prof, (x, B, z), 8, PLASTER, cap_top=True)
        for part in g.parts[n0:]:      # glazed brown, each jar a little different
            part.C = np.tile(np.array(GLAZE) * (0.9 + 0.2 * ((row * 3 + col) % 3) / 2), (len(part.P), 1))
            part.C[:, 3] = 1
        K.lathe(g, [(r * 0.7, -0.03), (r * 0.72, 0.02), (r * 0.5, 0.05), (0.0, 0.06)], (x, B + h, z), 8, DETAILS,
                uv_region=DET_RED, cap_top=False)
        K.lathe(g, [(r * 0.64, -0.03), (r * 0.65, 0.0)], (x, B + h, z), 8, DETAILS, uv_region=DET_ROPE, cap_top=False)
# worktable with cabbages, and a drying rack of cabbages on strings
K.box(g, (1.3, 0.42, 1.38), (1.72, 0.47, 1.62), TIMBER, WOOD_BLOCK, skip=(3,))
for x in (1.34, 1.68):
    for z in (1.42, 1.58):
        K.beam(g, (x, B, z), (x, 0.42, z), w=0.035, caps=False)
for k in range(5):
    K.lathe(g, [(0.0, 0.0), (0.06, 0.02), (0.065, 0.06), (0.03, 0.1), (0.0, 0.1)],
            (1.37 + 0.08 * k, 0.47, 1.45 + 0.08 * (k % 2)), 6, MOSS)
for x in (0.08, 1.92):
    K.pole(g, (x, B, 0.12), (x, 1.0, 0.12), r=0.028, material=BAMBOO_GOLD, sides=5, bend=0.01)
K.pole(g, (0.04, 0.95, 0.12), (1.96, 0.95, 0.12), r=0.022, material=BAMBOO_GOLD, sides=4, bend=0.0)
for k in range(6):
    x = 0.3 + 0.27 * k
    K.beam(g, (x, 0.95, 0.12), (x, 0.8, 0.12), w=0.01, material=DETAILS, caps=False)
    K.lathe(g, [(0.0, 0.0), (0.05, 0.02), (0.055, 0.07), (0.0, 0.1)], (x, 0.7, 0.12), 5, MOSS)
K.lantern(g, (1.8, 1.0, 1.68), r=0.06, h=0.14)
m.blocks = solid_blocks(2, 3, 2)
m.entrance(0, -1, 0)
m.slot("Entrance", (0.5, B, 0.3), yaw=180)
m.attach("Smoke", SMOKE, "brine stove flue")
m.extra["access"] = {"X": 0.5, "Y": B, "Z": 0.4}
m.collider((1.0, 0.4, 1.0), (1.9, 0.8, 1.6))
m.collider((1.0, 0.8, 2.3), (1.9, 1.5, 1.2))
m.build()
