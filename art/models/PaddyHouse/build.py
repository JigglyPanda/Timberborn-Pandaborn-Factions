"""Paddy House: the rice farmers' house. 3x2x2 on the vanilla Aquatic Farmhouse (its blocks, entrance, workplace).

A long low farmhouse on a stone plinth under a thick rice-straw thatch roof (gold from above: the Paddy House's
mark), its front open as a work porch: sheaves of rice
drying on a bamboo rack, conical rice hats hung on the posts, seedling trays, a rice-threshing tub, a water buffalo
yoke against the wall; a lattice window and a lantern.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("PaddyHouse", size=(3, 2, 2), seed=181, stand_in="AquaticFarmhouse.Folktails")
g = m.geo
B = 0.12
K.plinth(g, 0.04, 0.06, 2.96, 1.94, h=B)
WZ0, WZ1, TOP, RIDGE = 0.95, 1.85, 1.05, 1.72
with g.tagged("walls"):
    K.wall(g, (0.12, WZ0), (2.88, WZ0), B, TOP, openings=[("window", 0.2, 0.4, 0.3, 0.62),
                                                         ("door", 0.5, 0.4, 0.0, 0.66), ("window", 0.8, 0.4, 0.3, 0.62)])
    K.wall(g, (2.88, WZ0), (2.88, WZ1), B, TOP)
    K.wall(g, (2.88, WZ1), (0.12, WZ1), B, TOP)
    K.wall(g, (0.12, WZ1), (0.12, WZ0), B, TOP)
    K.gable_end(g, 0.12, 0.25, WZ1, TOP, RIDGE, outward=-1)
    K.gable_end(g, 2.88, 0.25, WZ1, TOP, RIDGE, outward=1)
# roof over house and porch together: the front slope runs down over the porch posts
# rice-straw thatch, the farm roof of the Sichuan plain: gold from the game camera where workshops read charcoal tile
K.thatch_roof(g, 0.12, 0.25, 2.88, WZ1, TOP, RIDGE + 0.08, overhang=0.22, thick=0.14, bulge=0.06)
for x in (0.14, 1.0, 2.0, 2.86):
    K.pole(g, (x, B, 0.28), (x, TOP - 0.02, 0.28), r=0.045, material=TIMBER, sides=6, bend=0.01, taper=0.92,
           tags={"frame"})
K.beam(g, (0.06, TOP - 0.02, 0.28), (2.94, TOP - 0.02, 0.28), w=0.07, sag=0.015, segs=2, tags={"frame"})
# drying rack of rice sheaves along the porch
K.pole(g, (0.2, 0.78, 0.5), (1.4, 0.78, 0.5), r=0.02, material=BAMBOO_GOLD, sides=4, bend=0.0)
for x in (0.24, 1.36):
    K.pole(g, (x, B, 0.5), (x, 0.8, 0.5), r=0.022, material=BAMBOO_GOLD, sides=4, bend=0.0)
for k in range(7):
    x = 0.32 + 0.16 * k
    n0 = len(g.parts)
    K.lathe(g, [(0.0, 0.0), (0.05, 0.04), (0.035, 0.22), (0.015, 0.3)], (x, 0.46, 0.5), 5, BAMBOO_GOLD)
    for p in g.parts[n0:]:
        p.C = np.tile([1.0, 0.88, 0.5, 1.0], (len(p.P), 1))   # golden straw
# conical rice hats on the posts
for x in (1.0, 2.0):
    K.lathe(g, [(0.0, 0.0), (0.16, -0.0), (0.0, 0.08)], (x, 0.7, 0.22), 8, WEAVE_GOLD)
# seedling trays and a threshing tub on the right of the porch
for k in range(3):
    K.box(g, (2.1 + 0.22 * (k % 2), B + 0.12 * (k // 2), 0.4), (2.3 + 0.22 * (k % 2), B + 0.12 * (k // 2) + 0.06, 0.62),
          WEAVE, (0.05, 0.05, 0.95, 0.95), skip=(3,))
    K.box(g, (2.11 + 0.22 * (k % 2), B + 0.12 * (k // 2) + 0.06, 0.41),
          (2.29 + 0.22 * (k % 2), B + 0.12 * (k // 2) + 0.075, 0.61), MOSS, (0.1, 0.1, 0.9, 0.9), skip=(3,))
K.lathe(g, [(0.0, 0.0), (0.2, 0.0), (0.24, 0.24), (0.21, 0.24), (0.17, 0.04)], (2.55, B, 0.75), 9, TIMBER,
        cap_top=False, strips=[WOOD_BLOCK])
# yoke leaning on the wall, lantern by the door
K.beam(g, (2.6, B, WZ0 - 0.06), (2.4, 0.72, WZ0 - 0.04), w=0.04)
K.lantern(g, (1.75, TOP - 0.1, 0.36), r=0.065, h=0.15)
cells = []
from building import block  # noqa: E402
for z in range(2):
    for y in range(2):
        for x in range(3):
            cells.append(block("GroundOrStackable" if z == 0 else "Any",
                               "Bottom, Top, Corners, Path, Middle" if z == 0 else "Floor, Bottom, Corners, Path, Middle",
                               "None"))
m.blocks = cells
m.entrance(1, -1, 0)
m.slot("Entrance", (1.5, B, 0.6), yaw=180)
m.extra["access"] = {"X": 1.5, "Y": B, "Z": 1.0}
m.collider((1.5, 0.6, 1.1), (2.9, 1.2, 1.7))
m.notes += ["Blocks, entrance and workplace as the vanilla Aquatic Farmhouse; access moved to the house door (z 1.0)."]
m.build()
