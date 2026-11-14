"""Hot Pot Hall: the best everyday meal. 2x3 on the vanilla Bakery (one cook; the Bakery's smoke rises from the pot's
flue as steam).

An open-sided timber hall under a grey-tile gable roof with the eaves hung thick with strings of dried red chillies:
in the middle a great iron hot pot on a clay stove, its broth split in two (a red and a pale half, the yin-yang pot),
low benches around it, a back wall of plaster with a lattice window, baskets of greens and mushrooms, lanterns.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, solid_blocks  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("HotPotHall", size=(2, 3, 4), seed=251, stand_in="Bakery.Folktails")
g = m.geo
B = 0.12
K.plinth(g, 0.04, 0.05, 1.96, 2.95, h=B)
with g.tagged("walls"):
    K.wall(g, (1.88, 2.8), (0.12, 2.8), B, 1.3, openings=[("window", 0.5, 0.5, 0.42, 0.85)])
for (x, z) in ((0.12, 0.15), (1.88, 0.15), (0.12, 1.45), (1.88, 1.45)):
    K.pole(g, (x, B, z), (x, 1.3, z), r=0.055, material=TIMBER, sides=6, bend=0.008, taper=0.92, tags={"frame"})
for x in (0.12, 1.88):
    K.beam(g, (x, 1.3, 0.1), (x, 1.3, 2.85), w=0.08, tags={"frame"})
K.beam(g, (0.05, 1.3, 0.15), (1.95, 1.3, 0.15), w=0.08, sag=0.015, segs=2, tags={"frame"})
K.gable_end(g, 0.12, 0.15, 2.8, 1.3, 2.05, outward=-1, infill=WEAVE_GOLD)
K.gable_end(g, 1.88, 0.15, 2.8, 1.3, 2.05, outward=1, infill=WEAVE_GOLD)
K.roof(g, 0.12, 0.15, 1.88, 2.8, 1.3, 2.05, kind="gable", axis="z", overhang=0.24, sag=0.09, lift=0.06,
       ridge_ends=0.07)
# chilli strings all along both eaves
for x in (-0.06, 2.06):
    for k in range(7):
        K.chilli_string(g, (x, 1.22, 0.3 + 0.38 * k), length=0.32 + 0.06 * (k % 2), n=5)
# the hot pot: clay stove, iron pot, a divided broth (red / pale), a flue
PC = np.array([1.0, B, 1.15])
K.lathe(g, [(0.0, 0.0), (0.42, 0.0), (0.45, 0.35), (0.4, 0.38)], PC, 10, EARTH, cap_top=True)
K.lathe(g, [(0.3, 0.0), (0.42, 0.06), (0.44, 0.24), (0.47, 0.26)], PC + [0, 0.38, 0], 12, IRON, cap_top=False)
for side, col in ((1, (0.82, 0.22, 0.1)), (-1, (0.92, 0.85, 0.7))):
    pts = [PC + [0, 0.6, 0]]
    for a in np.linspace(-math.pi / 2, math.pi / 2, 7):
        pts.append(PC + [side * math.cos(a) * 0.42, 0.6, math.sin(a) * 0.42])
    P = np.array(pts)
    N = np.tile([0, 1.0, 0], (len(P), 1))
    T = np.array([(0, k, k + 1) for k in range(1, len(P) - 1)])
    g.add(Part(PLASTER, P, N, np.full((len(P), 2), 0.5), fix_winding(P, N, T)), {"noshade"})
    g.parts[-1].C = np.tile(list(col) + [1.0], (len(P), 1))
K.beam(g, PC + [0, 0.605, -0.42], PC + [0, 0.605, 0.42], w=0.02, material=IRON, caps=False)
K.tube(g, [PC + [0.36, 0.3, 0.3], PC + [0.4, 2.3, 0.4]], [0.07, 0.06], EARTH, sides=6)
# benches round the pot, baskets of greens and mushrooms, lanterns
for (a, b) in (((0.35, 0.35, 0.45), (1.65, 0.35, 0.45)), ((0.35, 0.35, 1.85), (1.65, 0.35, 1.85))):
    K.beam(g, a, b, w=0.16, h=0.04)
    for p in (a, b):
        K.beam(g, (p[0], B, p[2]), (p[0], 0.34, p[2]), w=0.04, caps=False)
K.basket(g, (0.3, B, 2.45), h=0.14, r=0.13)
for k in range(4):
    K.lathe(g, [(0.0, 0.0), (0.06, 0.02), (0.065, 0.07), (0.0, 0.09)], (0.3 + 0.05 * math.cos(k * 1.6), B + 0.12,
            2.45 + 0.05 * math.sin(k * 1.6)), 5, MOSS)
K.basket(g, (1.7, B, 2.45), h=0.12, r=0.12, material=WEAVE)
for x in (0.12, 1.88):
    K.lantern(g, (x, 1.22, 0.05), r=0.075, h=0.17)
m.blocks = solid_blocks(2, 3, 4)
m.entrance(1, -1, 0)
m.slot("Entrance", (1.0, B, 0.7), yaw=180)
m.attach("Smoke", tuple(PC + [0.4, 2.35, 0.4]), "the vanilla bakery smoke from the stove flue")
m.extra["access"] = {"X": 1.0, "Y": B, "Z": 0.6}
m.collider((1.0, 1.0, 1.5), (1.9, 2.0, 2.8))
m.notes += ["Blocks as the vanilla Bakery (2x3x4) though the model only rises to about 2.4."]
m.build()
