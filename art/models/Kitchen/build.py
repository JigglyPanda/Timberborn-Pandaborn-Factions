"""Kitchen: sweet rice balls and bamboo seed cakes from rice flour. 2x3 on the vanilla Bakery (one cook; the Bakery's
smoke from the chimney).

A plastered farm kitchen at the back, its tiled gable turned end-on to the street (unlike the long workshops) with a
tall white chimney; in the front yard a grey stone hand mill on a stone table with its long push-pole, and a low table
spread with round trays of white rice balls and golden cakes under a striped awning; a water jar, firewood, a
lantern. From the game camera: the round grey millstone, the white dots of the rice balls and the tall chimney.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, solid_blocks  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("Kitchen", size=(2, 3, 4), seed=347, stand_in="Bakery.Folktails")
g = m.geo
B = 0.1
K.plinth(g, 0.04, 0.05, 1.96, 2.95, h=B)
# the kitchen house: end-on gable (ridge running back from the street), door and window in the front gable wall
KZ0, KZ1, TOP, RIDGE = 1.45, 2.85, 1.2, 1.95
with g.tagged("walls"):
    K.wall(g, (0.2, KZ0), (1.8, KZ0), B, TOP, openings=[("door", 0.32, 0.4, 0.0, 0.68), ("window", 0.72, 0.42, 0.36, 0.78)])
    K.wall(g, (1.8, KZ0), (1.8, KZ1), B, TOP, openings=[("window", 0.5, 0.45, 0.38, 0.8)])
    K.wall(g, (1.8, KZ1), (0.2, KZ1), B, TOP)
    K.wall(g, (0.2, KZ1), (0.2, KZ0), B, TOP)
K.roof(g, 0.2, KZ0, 1.8, KZ1, TOP, RIDGE, kind="gable", axis="z", overhang=0.2, sag=0.08, lift=0.05, ridge_ends=0.06)
# gable triangles front and back (the roof runs along z, so the gables face the street and the back)
for z, sg in ((KZ0, -1), (KZ1, 1)):
    K.panel(g, [(1.8, TOP, z + sg * 0.005), (0.2, TOP, z + sg * 0.005), (1.0, RIDGE - 0.04, z + sg * 0.005),
                (1.0, RIDGE - 0.04, z + sg * 0.005 + 0.0001)] if sg < 0 else
            [(0.2, TOP, z + 0.005), (1.8, TOP, z + 0.005), (1.0, RIDGE - 0.04, z + 0.005), (1.0001, RIDGE - 0.04, z + 0.005)],
            PLASTER_LATH, (0.1, 0.1, 0.9, 0.9))
# the tall white chimney at the back corner
K.box(g, (1.32, B, 2.45), (1.62, 2.55, 2.75), PLASTER, (0.1, 0.1, 0.9, 0.9), skip=(3,))
K.box(g, (1.28, 2.55, 2.41), (1.66, 2.62, 2.79), TILE, (0.0, TILE_COURSES[0][0], 0.3, TILE_COURSES[0][1]), skip=(3,))
# the stone hand mill on a stone table: two grey discs, a spout, a long push-pole hung from a cord
MC = np.array([0.55, 0.0, 0.62])
K.lathe(g, [(0.0, B), (0.42, B), (0.42, 0.42), (0.0, 0.42)], MC, 10, PLASTER, uv_region=(0.1, 0.1, 0.9, 0.9))
g.parts[-1].C = np.tile([0.56, 0.57, 0.55, 1.0], (len(g.parts[-1].P), 1))
for y0, h, r in ((0.42, 0.14, 0.33), (0.56, 0.15, 0.31)):
    K.lathe(g, [(0.0, y0), (r, y0), (r, y0 + h), (0.0, y0 + h)], MC, 12, PLASTER, uv_region=(0.1, 0.1, 0.9, 0.9))
    g.parts[-1].C = np.tile([0.66, 0.66, 0.63, 1.0], (len(g.parts[-1].P), 1))
K.beam(g, MC + [0.2, 0.66, 0.1], MC + [0.2, 0.82, 0.1], w=0.04, caps="end")   # the handle peg
K.pole(g, MC + [0.2, 0.8, 0.1], MC + [1.05, 0.95, -0.35], r=0.025, material=BAMBOO_GOLD, sides=5, bend=0.0)
K.beam(g, MC + [1.05, 0.95, -0.35], MC + [1.05, 1.0, -0.35], w=0.08, caps=False)
K.pole(g, (1.62, B, 0.18), (1.62, 1.35, 0.2), r=0.03, material=BAMBOO_GOLD, sides=5, bend=0.01)
K.beam(g, MC + [1.05, 1.0, -0.35], (1.62, 1.3, 0.2), w=0.01, material=DETAILS, caps=False)
K.lathe(g, [(0.0, 0.0), (0.12, 0.0), (0.12, 0.05)], MC + [0.0, B, -0.52], 8, WEAVE, cap_top=False)   # catch tray
# the low table of round trays: white rice balls and golden cakes, under an awning from the house's front
K.box(g, (0.95, 0.42, 0.75), (1.85, 0.47, 1.3), TIMBER, WOOD_BLOCK, skip=(3,))
for x in (1.0, 1.8):
    for z in (0.8, 1.25):
        K.beam(g, (x, B, z), (x, 0.42, z), w=0.04, caps=False)
for k, (x, z) in enumerate(((1.18, 0.92), (1.6, 0.92), (1.18, 1.16), (1.6, 1.16))):
    K.tray(g, (x, 0.48, z), r=0.17, leaf=None, sides=9)
    for j in range(7):
        a = j * 2 * math.pi / 7
        rr = 0.0 if j == 0 else 0.09
        c = (x + rr * math.cos(a), 0.51, z + rr * math.sin(a))
        if k % 2 == 0:
            K.lathe(g, [(0.0, 0.0), (0.035, 0.012), (0.03, 0.035), (0.0, 0.045)], c, 5, PLASTER,
                    uv_region=(0.1, 0.1, 0.9, 0.9))
            g.parts[-1].C = np.tile([0.97, 0.96, 0.92, 1.0], (len(g.parts[-1].P), 1))
        else:
            K.lathe(g, [(0.0, 0.0), (0.04, 0.0), (0.04, 0.02), (0.0, 0.022)], c, 6, WEAVE_GOLD)
for x in (0.95, 1.85):
    K.pole(g, (x, B, 0.7), (x, 1.05, 0.7), r=0.025, material=BAMBOO_GOLD, sides=4, bend=0.0)
K.cloth(g, [(0.9, 1.02, 0.66), (1.9, 1.02, 0.66), (1.9, 1.18, KZ0 - 0.02), (0.9, 1.18, KZ0 - 0.02)], DETAILS,
        (0.53, 0.55, 0.72, 0.95), sag=0.04, nu=2, nv=2, wave=0.01)
# water jar, firewood, lantern
K.jar(g, (0.35, B, 1.3), h=0.36, r=0.13)
for k in range(4):
    K.pole(g, (0.3, B + 0.04 + 0.06 * (k // 2), 2.95 - 0.08 * (k % 2)), (0.9, B + 0.04 + 0.06 * (k // 2),
           2.93 - 0.08 * (k % 2)), r=0.035, material=TIMBER, sides=5, bend=0.0)
K.lantern(g, (0.2, 1.12, KZ0 - 0.12), r=0.07, h=0.16)
m.blocks = solid_blocks(2, 3, 4)
m.entrance(1, -1, 0)
m.slot("Entrance", (0.68, B, 1.32), yaw=180)
m.attach("Smoke", (1.47, 2.62, 2.6), "the vanilla bakery smoke from the tall chimney")
m.extra["access"] = {"X": 1.0, "Y": B, "Z": 0.2}
m.collider((1.0, 0.8, 2.15), (1.7, 1.6, 1.5))
m.collider((0.55, 0.35, 0.62), (0.9, 0.7, 0.9))
m.notes += ["On the Bakery footprint (2x3x4) with its smoke moved to the chimney."]
m.build()
