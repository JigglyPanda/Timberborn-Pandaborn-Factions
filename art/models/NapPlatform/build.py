"""Nap Platform: a nap in the sun for several at once. 3x2x1 on the vanilla Rooftop Terrace (it stands on roofs and
other stackable tops; eight seats).

A low bamboo-slat deck with woven sleeping mats and cushions in indigo and hemp, two bamboo frames holding a sagging
sunshade cloth over half of it, a pot of bamboo at one corner and a teapot on a low tray.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("NapPlatform", size=(3, 2, 1), seed=163, stand_in="RooftopTerrace.Folktails")
g = m.geo
D = 0.12
# deck: slats on two bearers, edged with a bamboo rail
for z in (0.25, 1.75):
    K.beam(g, (0.08, 0.03, z), (2.92, 0.03, z), w=0.06)
K.boards(g, (0.06, D - 0.03, 0.08), (0, 0, 1), (1, 0, 0), 1.84, 2.88, 16, BAMBOO_GOLD, thick=0.025, warp=0.005)
for z in (0.06, 1.94):
    K.pole(g, (0.04, D + 0.02, z), (2.96, D + 0.02, z), r=0.02, material=BAMBOO_GOLD, sides=4, bend=0.0)
# mats and cushions where the nappers lie (the vanilla seat positions, nudged onto the mats)
seats = [(0.45, 0.45), (1.05, 0.45), (1.9, 0.45), (2.45, 0.5), (0.5, 1.4), (1.05, 1.55), (1.8, 1.55), (2.45, 1.4)]
for i, (x, z) in enumerate(seats):
    w, d = 0.42, 0.3
    K.panel(g, [(x - w / 2, D + 0.005, z - d), (x + w / 2, D + 0.005, z - d), (x + w / 2, D + 0.005, z + d),
                (x - w / 2, D + 0.005, z + d)], WEAVE if i % 2 else WEAVE_GOLD)
    reg = DET_CLOTH if i % 3 else DET_SACK
    K.box(g, (x - 0.12, D, z + d - 0.14), (x + 0.12, D + 0.06, z + d - 0.02), DETAILS, reg, skip=(3,))
    m.slot(f"Seat{i + 1}", (x, D + 0.02, z), yaw=180 if z < 1 else 0)
# sunshade over the back half: two bamboo frames, a sagging cloth
for x in (0.12, 2.88):
    for z in (1.0, 1.9):
        K.pole(g, (x, D, z), (x, 0.92 if z > 1.5 else 0.82, z), r=0.025, material=BAMBOO_GOLD, sides=5, bend=0.01)
    K.pole(g, (x, 0.82, 1.0), (x, 0.92, 1.9), r=0.02, material=BAMBOO_GOLD, sides=4, bend=0.0, caps=False)
K.cloth(g, [(0.12, 0.8, 1.0), (2.88, 0.8, 1.0), (2.88, 0.9, 1.9), (0.12, 0.9, 1.9)], DETAILS, (0.53, 0.55, 0.72, 0.95),
        sag=0.08, nu=5, nv=2, wave=0.012)
# pot of bamboo, tray with teapot
K.lathe(g, [(0.0, 0.0), (0.1, 0.0), (0.13, 0.15)], (2.85, D, 0.15), 7, EARTH)
for k in range(5):
    K.pole(g, (2.85 + 0.04 * math.cos(k), D + 0.15, 0.15 + 0.04 * math.sin(k)),
           (2.85 + 0.1 * math.cos(k), D + 0.75 + 0.1 * (k % 2), 0.15 + 0.1 * math.sin(k)), r=0.012,
           material=BAMBOO_GREEN, sides=3, bend=0.03, caps=False)
K.box(g, (1.35, D, 0.9), (1.65, D + 0.04, 1.1), TIMBER, WOOD_BLOCK, skip=(3,))
K.lathe(g, [(0.0, 0.0), (0.04, 0.0), (0.05, 0.04), (0.0, 0.07)], (1.5, D + 0.04, 1.0), 6, EARTH)
m.entrance(1, -1, 0)
m.extra["access"] = {"X": 1.5, "Y": D, "Z": 0.4}
m.collider((1.5, 0.08, 1.0), (3.0, 0.16, 2.0))
m.notes += ["Blocks as the vanilla Rooftop Terrace (MatterBelow Stackable: it goes on roofs, e.g. a Terrace House); "
            "eight Seat slots on the mats (Sitting, as vanilla)."]
m.build()
