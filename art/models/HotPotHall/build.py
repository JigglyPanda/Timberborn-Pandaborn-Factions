"""Hot Pot Hall: the best everyday meal. 2x3 on the vanilla Bakery (one cook; the Bakery's smoke rises from the pot's
vent as steam).

Pass 4 (the pot was hidden under one big roof): the hall is open on the entrance side. At the front the great red hot
pot stands on its clay stove under its own raised "lantern roof": a small tiled pyramid on four tall posts with a
second little roof lifted over the vent, where the steam leaves; its eaves and the hall's front eave hung thick with
strings of dried red chillies; benches round the pot. Behind it the hall: a plastered back room under a grey-tile
gable with a lattice window, baskets of greens and mushrooms, lanterns. From the game camera: the red pot and its
steam under a tiered little roof, ringed with red chillies.
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
# the back hall: plastered walls on three sides, open toward the pot
HZ0, HZ1, TOP, RIDGE = 1.65, 2.85, 1.3, 1.95
with g.tagged("walls"):
    K.wall(g, (1.88, HZ1), (0.12, HZ1), B, TOP, openings=[("window", 0.5, 0.5, 0.5, 0.85)])
    K.wall(g, (0.12, HZ1), (0.12, HZ0), B, TOP, openings=[("window", 0.5, 0.45, 0.42, 0.8)])
    K.wall(g, (1.88, HZ0), (1.88, HZ1), B, TOP)
for x in (0.12, 1.88):
    K.pole(g, (x, B, HZ0), (x, TOP, HZ0), r=0.055, material=TIMBER, sides=6, bend=0.008, taper=0.92, tags={"frame"})
K.beam(g, (0.05, TOP, HZ0), (1.95, TOP, HZ0), w=0.08, sag=0.015, segs=2, tags={"frame"})
K.gable_end(g, 0.12, HZ0, HZ1, TOP, RIDGE, outward=-1)
K.gable_end(g, 1.88, HZ0, HZ1, TOP, RIDGE, outward=1)
K.roof(g, 0.12, HZ0, 1.88, HZ1, TOP, RIDGE, kind="gable", overhang=0.22, sag=0.08, lift=0.05, ridge_ends=0.06)
for k in range(6):   # chillies on the hall's front eave
    K.chilli_string(g, (0.2 + 0.32 * k, TOP - 0.02, HZ0 - 0.22), length=0.36 + 0.06 * (k % 2), n=6)
# the hot pot: clay stove, a big red-lacquered pot, the yin-yang broth (red / pale), the divider
PC = np.array([1.0, B, 0.92])
K.lathe(g, [(0.0, 0.0), (0.5, 0.0), (0.53, 0.32), (0.48, 0.36)], PC, 12, EARTH, cap_top=True)
K.lathe(g, [(0.34, 0.0), (0.5, 0.07), (0.53, 0.27), (0.57, 0.3)], PC + [0, 0.36, 0], 14, PLASTER, cap_top=False)
g.parts[-1].C = np.tile([0.55, 0.1, 0.06, 1.0], (len(g.parts[-1].P), 1))
for side, col in ((1, (0.85, 0.2, 0.08)), (-1, (0.93, 0.86, 0.68))):
    pts = [PC + [0, 0.6, 0]]
    for a in np.linspace(-math.pi / 2, math.pi / 2, 8):
        pts.append(PC + [side * math.cos(a) * 0.52, 0.6, math.sin(a) * 0.52])
    P = np.array(pts)
    N = np.tile([0, 1.0, 0], (len(P), 1))
    T = np.array([(0, k, k + 1) for k in range(1, len(P) - 1)])
    g.add(Part(PLASTER, P, N, np.full((len(P), 2), 0.5), fix_winding(P, N, T)), {"noshade"})
    g.parts[-1].C = np.tile(list(col) + [1.0], (len(P), 1))
# an S-shaped divider: a thin iron band across the middle
K.beam(g, PC + [0, 0.61, -0.52], PC + [0, 0.61, 0.52], w=0.025, material=IRON, caps=False)
for k in range(5):   # chillies and slices floating in the red half
    K.lathe(g, [(0.0, 0.0), (0.03, 0.01), (0.0, 0.02)], PC + [0.12 + 0.07 * k, 0.6, -0.2 + 0.1 * k], 4, DETAILS,
            uv_region=DET_RED)
# the lantern roof over the pot: four tall posts, a pyramid of tile, a little roof lifted over the vent
PX0, PX1, PZ0, PZ1, PE = 0.4, 1.6, 0.35, 1.5, 2.0
for (x, z) in ((PX0, PZ0), (PX1, PZ0), (PX0, PZ1), (PX1, PZ1)):
    K.pole(g, (x, B, z), (x, PE, z), r=0.05, material=TIMBER, sides=6, bend=0.006, taper=0.92, tags={"frame"})
for (a, b) in (((PX0, PZ0), (PX1, PZ0)), ((PX0, PZ1), (PX1, PZ1)), ((PX0, PZ0), (PX0, PZ1)), ((PX1, PZ0), (PX1, PZ1))):
    K.beam(g, (a[0], PE, a[1]), (b[0], PE, b[1]), w=0.07, tags={"frame"})
K.roof(g, PX0, PZ0, PX1, PZ1, PE, 2.3, kind="hip", hip_inset=0.42, overhang=0.16, sag=0.05, lift=0.05, ridge=False,
       tile=0.26, course=0.26)
for (x, z) in ((0.75, 0.75), (1.25, 0.75), (0.75, 1.1), (1.25, 1.1)):   # the vent's short posts
    K.pole(g, (x, 2.18, z), (x, 2.45, z), r=0.03, material=TIMBER, sides=5, bend=0.0)
K.roof(g, 0.72, 0.72, 1.28, 1.13, 2.45, 2.62, kind="pyramid", overhang=0.1, sag=0.03, lift=0.04, tile=0.2, course=0.2)
for (a, b) in (((PX0 - 0.16, PZ0 - 0.16), (PX1 + 0.16, PZ0 - 0.16)), ((PX0 - 0.16, PZ0 - 0.16), (PX0 - 0.16, PZ1)),
               ((PX1 + 0.16, PZ0 - 0.16), (PX1 + 0.16, PZ1))):
    a, b = np.array(a), np.array(b)
    n = max(3, int(np.linalg.norm(b - a) / 0.3))
    for k in range(n):
        p = a + (b - a) * (k + 0.5) / n
        K.chilli_string(g, (p[0], PE + 0.02, p[1]), length=0.34 + 0.08 * (k % 2), n=6)
# benches round the pot (left, right, front-left gap for the cook), baskets of greens and mushrooms, lanterns
for (a, b) in (((0.28, 0.32, 0.4), (0.28, 0.32, 1.45)), ((1.72, 0.32, 0.4), (1.72, 0.32, 1.45))):
    K.beam(g, a, b, w=0.16, h=0.04)
    for p in (a, b):
        K.beam(g, (p[0], B, p[2]), (p[0], 0.31, p[2]), w=0.04, caps=False)
K.basket(g, (0.35, B, 2.4), h=0.14, r=0.14)
for k in range(4):
    K.lathe(g, [(0.0, 0.0), (0.06, 0.02), (0.065, 0.07), (0.0, 0.09)], (0.35 + 0.05 * math.cos(k * 1.6), B + 0.12,
            2.4 + 0.05 * math.sin(k * 1.6)), 5, MOSS)
K.basket(g, (1.65, B, 2.4), h=0.12, r=0.13, material=WEAVE)
for x in (PX0, PX1):
    K.lantern(g, (x, PE - 0.06, PZ0 - 0.02), r=0.08, h=0.18)
m.blocks = solid_blocks(2, 3, 4)
m.entrance(1, -1, 0)
m.slot("Entrance", (1.0, B, 0.25), yaw=180)
m.attach("Smoke", (1.0, 2.5, 0.92), "the vanilla bakery smoke leaving the lantern roof's vent: the pot's steam")
m.extra["access"] = {"X": 1.0, "Y": B, "Z": 0.2}
m.collider((1.0, 1.0, 2.25), (1.9, 2.0, 1.3))
m.collider((1.0, 0.4, 0.92), (1.1, 0.75, 1.1))
m.notes += ["Blocks as the vanilla Bakery (2x3x4); the lantern roof's vent cap reaches 2.7."]
m.build()
