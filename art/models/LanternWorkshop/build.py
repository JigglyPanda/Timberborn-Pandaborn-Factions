"""Lantern Workshop: paper lanterns for the festival. 2x3 on the vanilla Bakery's workshop footprint (one worker).

A plastered workshop with a grey-tile gable roof, its long front open as a shop: inside, a workbench with a split-
bamboo lantern frame half covered in red paper, rolls of paper and pots of glue; outside, a bamboo drying rack hung
with finished red lanterns (they glow at night with the workplace lit) and bundles of thin canes leaning on the wall.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, solid_blocks  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("LanternWorkshop", size=(2, 3, 4), seed=257, stand_in="Bakery.Folktails")
g = m.geo
B = 0.1
K.plinth(g, 0.04, 0.05, 1.96, 2.95, h=B)
WZ0 = 1.2
with g.tagged("walls"):
    K.wall(g, (1.88, WZ0), (1.88, 2.85), B, 1.25, openings=[("window", 0.5, 0.42, 0.4, 0.75)])
    K.wall(g, (1.88, 2.85), (0.12, 2.85), B, 1.25)
    K.wall(g, (0.12, 2.85), (0.12, WZ0), B, 1.25, openings=[("window", 0.5, 0.42, 0.4, 0.75)])
for x in (0.12, 1.0, 1.88):
    K.pole(g, (x, B, WZ0), (x, 1.25, WZ0), r=0.05, material=TIMBER, sides=6, bend=0.01, taper=0.92, tags={"frame"})
K.beam(g, (0.05, 1.25, WZ0), (1.95, 1.25, WZ0), w=0.08, sag=0.015, segs=2, tags={"frame"})
K.gable_end(g, 0.12, WZ0, 2.85, 1.25, 1.85, outward=-1)
K.gable_end(g, 1.88, WZ0, 2.85, 1.25, 1.85, outward=1)
K.roof(g, 0.12, WZ0, 1.88, 2.85, 1.25, 1.85, kind="gable", overhang=0.22, sag=0.08, lift=0.05, ridge_ends=0.06)
# workbench inside with a half-papered lantern frame, paper rolls, glue pots
K.box(g, (0.35, 0.5, 1.6), (1.65, 0.55, 2.0), TIMBER, WOOD_BLOCK, skip=(3,))
for x in (0.4, 1.6):
    for z in (1.65, 1.95):
        K.beam(g, (x, B, z), (x, 0.5, z), w=0.04, caps=False)
FC = np.array([0.8, 0.55, 1.8])
for k in range(6):
    a = 2 * math.pi * k / 6
    rib = [FC + [math.cos(a) * r, y, math.sin(a) * r] for r, y in ((0.05, 0.0), (0.16, 0.08), (0.17, 0.2), (0.05, 0.3))]
    K.tube(g, rib, [0.008] * len(rib), BAMBOO_GOLD, sides=3, caps=False)
K.lathe(g, [(0.05, 0.0), (0.16, 0.08), (0.17, 0.2)], FC, 6, DETAILS, uv_region=DET_RED, cap_top=False)
for k in range(3):
    K.tube(g, [(1.2 + 0.08 * k, 0.58, 1.7), (1.2 + 0.08 * k, 0.58, 1.95)], [0.035, 0.035], PAPER, sides=6,
           strips=[(0.36, 0.05, 0.6, 0.6)])
K.lathe(g, [(0.0, 0.0), (0.04, 0.0), (0.045, 0.06)], (1.5, 0.55, 1.65), 6, EARTH, cap_top=False)
# the drying rack out front, hung with finished lanterns
for x in (0.15, 1.85):
    K.pole(g, (x, B, 0.35), (x, 1.05, 0.35), r=0.03, material=BAMBOO_GOLD, sides=5, bend=0.01)
K.pole(g, (0.08, 1.0, 0.35), (1.92, 1.0, 0.35), r=0.025, material=BAMBOO_GOLD, sides=4, bend=0.0)
for k in range(5):
    x = 0.38 + 0.31 * k
    K.lantern(g, (x, 0.98 - 0.02 * (k % 2), 0.35), r=0.07 + 0.01 * (k % 3), h=0.17)
# bundles of thin canes leaning on the side wall
for k in range(5):
    K.pole(g, (1.95 + 0.01 * k, B, 1.4 + 0.04 * k), (1.92, 1.1, 1.55 + 0.04 * k), r=0.01, material=BAMBOO_GREEN,
           sides=3, bend=0.0, caps=False)
m.blocks = solid_blocks(2, 3, 4)
m.entrance(1, -1, 0)
m.slot("Entrance", (1.0, B, 1.4), yaw=180)
m.extra["access"] = {"X": 1.0, "Y": B, "Z": 1.3}
m.extra["removeSpecs"] = ["TemplateAttachmentsSpec", "WorkshopParticleControllerSpec", "WindParticleControllerSpec"]
m.collider((1.0, 0.7, 2.0), (1.9, 1.4, 1.7))
m.notes += ["On the Bakery footprint (2x3x4) without its oven smoke (removeSpecs). The rack's lanterns glow with the "
            "workplace lit (WorkplaceIlluminatorSpec)."]
m.build()
