"""Tea Roastery: tea leaves into tea. 2x3 on the vanilla Bakery's workshop footprint (one worker, the bakery smoke
rising from the roasting stove).

An open-fronted plastered workshop under a grey-tile gable: two big iron roasting woks set in a clay stove; in front
of the roofline a rack of two stepped tiers of wide, shallow, pale bamboo trays of green and roasted leaf, tilted
toward the street (the one thing that tells it from every other workshop from the game camera); trays drying on the
side shelf, a basket of fresh leaves, clay tea jars on a shelf, a lantern.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, solid_blocks  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("TeaRoastery", size=(2, 3, 4), seed=271, stand_in="Bakery.Folktails")
g = m.geo
B = 0.1
K.plinth(g, 0.04, 0.05, 1.96, 2.95, h=B)
WZ0 = 1.3
with g.tagged("walls"):
    K.wall(g, (1.88, WZ0), (1.88, 2.85), B, 1.25)
    K.wall(g, (1.88, 2.85), (0.12, 2.85), B, 1.25, openings=[("window", 0.3, 0.4, 0.42, 0.78)])
    K.wall(g, (0.12, 2.85), (0.12, WZ0), B, 1.25)
for x in (0.12, 1.88):
    K.pole(g, (x, B, WZ0), (x, 1.25, WZ0), r=0.05, material=TIMBER, sides=6, bend=0.01, taper=0.92, tags={"frame"})
K.beam(g, (0.05, 1.25, WZ0), (1.95, 1.25, WZ0), w=0.08, sag=0.015, segs=2, tags={"frame"})
K.gable_end(g, 0.12, WZ0, 2.85, 1.25, 1.85, outward=-1)
K.gable_end(g, 1.88, WZ0, 2.85, 1.25, 1.85, outward=1)
K.roof(g, 0.12, WZ0, 1.88, 2.85, 1.25, 1.85, kind="gable", overhang=0.22, sag=0.08, lift=0.05, ridge_ends=0.06)
# the stove with two woks and its flue
K.box(g, (0.35, B, 2.05), (1.65, 0.55, 2.6), EARTH, (0.05, 0.05, 0.95, 0.95), skip=(3,))
for x in (0.7, 1.3):
    K.lathe(g, [(0.0, 0.0), (0.2, 0.05), (0.26, 0.11)], (x, 0.48, 2.32), 8, IRON, cap_top=False)
    K.lathe(g, [(0.0, 0.0), (0.18, 0.02), (0.0, 0.04)], (x, 0.5, 2.32), 8, MOSS, cap_top=False)
K.tube(g, [(1.55, 0.55, 2.55), (1.57, 1.95, 2.6)], [0.07, 0.06], EARTH, sides=6)
# the drying rack in the yard, out from under the roof: two stepped tiers of wide, shallow, pale bamboo trays of
# leaf, tilted toward the street (and the camera), green fresh leaf and brown roasted leaf
for x in (0.1, 1.9):
    for z, top in ((0.18, 0.62), (0.78, 1.02)):
        K.pole(g, (x, B, z), (x, top, z), r=0.03, material=BAMBOO_GOLD, sides=5, bend=0.0)
    K.pole(g, (x, 0.5, 0.18), (x, 0.92, 0.78), r=0.022, material=BAMBOO_GOLD, sides=4, bend=0.0, caps=False)
for z, y in ((0.18, 0.55), (0.78, 0.95)):
    K.pole(g, (0.04, y, z), (1.96, y, z), r=0.02, material=BAMBOO_GOLD, sides=4, bend=0.0)
for row, (z, y) in enumerate(((0.36, 0.6), (0.92, 1.0))):
    for k, x in enumerate((0.36, 1.0, 1.64)):
        n0 = len(g.parts)
        K.tray(g, (x, y, z), r=0.31, tilt=(-0.5, 0.0), leaf=MOSS, fill=0.85)
        if (row + k) % 2:
            leaf = g.parts[-1]
            leaf.C = np.tile([0.55, 0.38, 0.22, 1.0], (len(leaf.P), 1))
# two more trays drying flat on the shelf over the stove room's side
for z in (1.75, 2.35):
    K.tray(g, (0.0, 1.32, z), r=0.24, tilt=(0.0, 0.25), leaf=MOSS)
# baskets of fresh leaves, tea jars on a shelf, lantern
K.basket(g, (1.72, B, 1.12), h=0.16, r=0.14)
K.lathe(g, [(0.0, 0.14), (0.12, 0.16)], (1.72, B, 1.12), 7, MOSS, cap_top=False)
K.box(g, (1.5, 0.6, 1.4), (1.85, 0.64, 1.95), TIMBER, WOOD_STRIPS[0])
for k in range(3):
    K.jar(g, (1.62 + 0.1 * (k % 2), 0.64, 1.5 + 0.18 * k), h=0.18, r=0.06, material=PLASTER)
    g.parts[-2].C = np.tile([0.3, 0.22, 0.15, 1.0], (len(g.parts[-2].P), 1))
K.lantern(g, (1.88, 1.18, WZ0 - 0.1), r=0.07, h=0.16)
m.blocks = solid_blocks(2, 3, 4)
m.entrance(1, -1, 0)
m.slot("Entrance", (1.0, B, 1.6), yaw=180)
m.attach("Smoke", (1.57, 2.0, 2.6), "the vanilla bakery smoke from the stove flue")
m.extra["access"] = {"X": 1.0, "Y": B, "Z": 1.5}
m.collider((1.0, 0.7, 2.1), (1.9, 1.4, 1.6))
m.collider((1.0, 0.55, 0.6), (1.9, 1.0, 0.9))
m.build()
