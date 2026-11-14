"""Nap Platform: a nap in the sun for several at once. 3x2x1 on the vanilla Rooftop Terrace's attraction, now standing
on the ground or on a roof (blocks MatterBelow GroundOrStackable) and taking five nappers.

A bamboo-slat deck raised on short timber legs over flat stone pads (so it sits right on grass or on a roof deck),
five woven sleeping mats each with an indigo or hemp cushion, two bamboo frames holding a sagging sunshade cloth over
the back half, a pot of bamboo at one corner and a teapot on a low tray.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, block  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("NapPlatform", size=(3, 2, 1), seed=163, stand_in="RooftopTerrace.Folktails")
g = m.geo
D = 0.26
# short legs on flat stone pads, two bearers, the slat deck, a bamboo rail
for x in (0.15, 1.5, 2.85):
    for z in (0.25, 1.75):
        K.box(g, (x - 0.1, 0.0, z - 0.1), (x + 0.1, 0.05, z + 0.1), PLASTER, (0.1, 0.1, 0.9, 0.9))
        g.parts[-1].C = np.tile([0.58, 0.6, 0.58, 1.0], (len(g.parts[-1].P), 1))
        K.beam(g, (x, 0.05, z), (x, D - 0.08, z), w=0.08, caps=False)
for z in (0.25, 1.75):
    K.beam(g, (0.08, D - 0.08, z), (2.92, D - 0.08, z), w=0.07, h=0.06)
K.boards(g, (0.06, D - 0.03, 0.08), (0, 0, 1), (1, 0, 0), 1.84, 2.88, 16, BAMBOO_GOLD, thick=0.025, warp=0.005)
for z in (0.06, 1.94):
    K.pole(g, (0.04, D + 0.02, z), (2.96, D + 0.02, z), r=0.02, material=BAMBOO_GOLD, sides=4, bend=0.0)
# mats and cushions where the nappers lie (the vanilla seat positions, nudged onto the mats)
seats = [(0.5, 0.5), (1.5, 0.5), (2.5, 0.5), (0.85, 1.45), (2.15, 1.45)]
for i, (x, z) in enumerate(seats):
    w, d = 0.5, 0.36
    K.panel(g, [(x - w / 2, D + 0.005, z - d), (x + w / 2, D + 0.005, z - d), (x + w / 2, D + 0.005, z + d),
                (x - w / 2, D + 0.005, z + d)], WEAVE if i % 2 else WEAVE_GOLD)
    reg = DET_CLOTH if i % 3 else DET_SACK
    K.box(g, (x - 0.17, D, z + d - 0.17), (x + 0.17, D + 0.09, z + d - 0.03), DETAILS, reg, skip=(3,))
    m.slot(f"Seat{i + 1}", (x, D + 0.02, z), yaw=180 if z < 1 else 0)
# sunshade over the back half: two bamboo frames, a sagging cloth
for x in (0.12, 2.88):
    for z in (1.0, 1.9):
        K.pole(g, (x, D, z), (x, 1.16 if z > 1.5 else 1.06, z), r=0.025, material=BAMBOO_GOLD, sides=5, bend=0.01)
    K.pole(g, (x, 1.06, 1.0), (x, 1.16, 1.9), r=0.02, material=BAMBOO_GOLD, sides=4, bend=0.0, caps=False)
K.cloth(g, [(0.12, 1.04, 1.0), (2.88, 1.04, 1.0), (2.88, 1.14, 1.9), (0.12, 1.14, 1.9)], DETAILS, (0.53, 0.55, 0.72, 0.95),
        sag=0.08, nu=5, nv=2, wave=0.012)
# pot of bamboo, tray with teapot
K.lathe(g, [(0.0, 0.0), (0.1, 0.0), (0.13, 0.15)], (2.85, D, 1.85), 7, EARTH)
for k in range(5):
    K.pole(g, (2.85 + 0.04 * math.cos(k), D + 0.15, 1.85 + 0.04 * math.sin(k)),
           (2.85 + 0.1 * math.cos(k), D + 0.75 + 0.1 * (k % 2), 1.85 + 0.1 * math.sin(k)), r=0.012,
           material=BAMBOO_GREEN, sides=3, bend=0.03, caps=False)
K.box(g, (1.35, D, 1.3), (1.65, D + 0.04, 1.5), TIMBER, WOOD_BLOCK, skip=(3,))
K.lathe(g, [(0.0, 0.0), (0.04, 0.0), (0.05, 0.04), (0.0, 0.07)], (1.5, D + 0.04, 1.4), 6, EARTH)
m.entrance(1, -1, 0)
m.extra["access"] = {"X": 1.5, "Y": D, "Z": 0.4}
m.blocks = [block("GroundOrStackable", "Bottom, Corners, Path, Middle", "None") for _ in range(6)]
m.collider((1.5, 0.13, 1.0), (3.0, 0.26, 2.0))
m.notes += ["Blocks as the vanilla Rooftop Terrace but MatterBelow GroundOrStackable (ground or roof); five Seat slots on "
            "the mats (Sitting, as vanilla): set the attraction's capacity and FixedSlotManagerSpec to five."]
m.build()
