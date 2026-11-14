"""Slide and Swing: play by the water. 4x3x2 on the vanilla Lido (BaseZ 1: the front row is a deck on the bank, the
two back rows a pool reaching one block down into the water; seven players: four sitting on the deck, three floating,
two swimming laps between marker nodes).

A plank deck on the bank with a bamboo railing; from a little lashed bamboo tower at its left a split-bamboo slide
curves down into the pool; over the pool's right side a tall bamboo swing frame with a plank seat on ropes; the pool
lined with timber and stones; a red lantern and a towel rail.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, block  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("SlideAndSwing", size=(4, 3, 2), seed=229, stand_in="Lido.Folktails", overhang=0.3)
g = m.geo
# deck on the bank (front row), y = 0 is the bank's surface
K.box(g, (0.0, -0.25, 0.0), (4.0, 0.0, 0.95), EARTH, (0.02, 0.02, 0.98, 0.98), skip=(3,))
K.boards(g, (0.02, 0.0, 0.02), (1, 0, 0), (0, 0, 1), 3.96, 0.95, 4, TIMBER, thick=0.03)
for x in np.linspace(0.05, 3.95, 9):
    if 1.2 < x < 2.4:
        continue
    K.pole(g, (x, 0.0, 0.92), (x, 0.4, 0.92), r=0.018, material=BAMBOO_GOLD, sides=4, bend=0.0)
for (a, b) in ((0.05, 1.2), (2.4, 3.95)):
    K.pole(g, (a, 0.38, 0.92), (b, 0.38, 0.92), r=0.02, material=BAMBOO_GOLD, sides=4, bend=0.0, caps=False)
# the pool behind: timber-lined sides going down to the water, stones on the rim
for (lo, hi) in (((0.0, -1.0, 0.95), (0.08, 0.05, 3.0)), ((3.92, -1.0, 0.95), (4.0, 0.05, 3.0)),
                 ((0.0, -1.0, 2.92), (4.0, 0.05, 3.0))):
    K.box(g, lo, hi, TIMBER, WOOD_BLOCK, skip=(3,))
K.stones(g, 0.04, 2.9, 3.96, 3.04, y=0.0, size=0.3, h=0.08, ring=False, skip=0.1)
# slide tower and slide at the left
for (x, z) in ((0.15, 0.15), (0.7, 0.15), (0.7, 0.7), (0.15, 0.7)):
    K.pole(g, (x, 0.0, z), (x, 1.3, z), r=0.035, material=BAMBOO_GOLD, sides=5, bend=0.005)
K.box(g, (0.1, 1.05, 0.1), (0.75, 1.1, 0.75), TIMBER, WOOD_BLOCK, skip=(3,))
K.ladder(g, (0.42, 0.0, -0.15), (0.42, 1.08, 0.1), width=0.24, rungs=5)
K.roof(g, 0.1, 0.1, 0.75, 0.75, 1.3, 1.6, kind="pyramid", overhang=0.1, sag=0.02, lift=0.04, tile=0.2, course=0.2)
K.channel(g, 0.75, 2.4, -0.45, 0.42, r_in=0.2, wall=0.03, material=BAMBOO_GREEN, around=5, sleeve=False, tilt=1.4)
for z in (1.2, 1.8):
    K.pole(g, (0.42, -1.0, z), (0.42, 0.72 - (z - 1.2) * 0.8, z), r=0.025, material=BAMBOO_GOLD, sides=4, bend=0.0)
# swing frame over the pool's right side
for z in (1.4, 2.7):
    for dx in (-0.25, 0.25):
        K.pole(g, (3.5 + dx * 1.6, -1.0, z), (3.5, 1.5, z), r=0.035, material=BAMBOO_GOLD, sides=5, bend=0.005)
K.pole(g, (3.5, 1.48, 1.3), (3.5, 1.48, 2.8), r=0.04, material=BAMBOO_GOLD, sides=5, bend=0.0)
for z in (1.85, 2.25):
    K.beam(g, (3.5, 1.46, z), (3.5, 0.3, z), w=0.012, material=DETAILS, caps=False)
K.box(g, (3.35, 0.27, 1.8), (3.65, 0.31, 2.3), TIMBER, WOOD_STRIPS[1])
# towel rail and lantern on the deck
K.pole(g, (2.6, 0.55, 0.15), (3.3, 0.55, 0.15), r=0.016, material=BAMBOO_GOLD, sides=4, bend=0.0)
for x in (2.62, 3.28):
    K.pole(g, (x, 0.0, 0.15), (x, 0.58, 0.15), r=0.018, material=BAMBOO_GOLD, sides=4, bend=0.0)
K.cloth(g, [(2.75, 0.25, 0.15), (2.95, 0.25, 0.15), (2.95, 0.55, 0.15), (2.75, 0.55, 0.15)], DETAILS, DET_CLOTH,
        sag=0.0, nu=1, nv=1, wave=0.0)
K.standing_lantern(g, (3.85, 0.0, 0.2), h=0.8)
# slots and marker nodes at the vanilla Lido's positions
for i, p in enumerate(((3.35, 0.03, 0.55), (2.51, 0.03, 0.5), (1.6, 0.03, 0.5), (1.0, 0.03, 0.55))):
    m.slot(f"Seat{i + 1}", p, yaw=180)
for i, p in enumerate(((2.53, -0.5, 1.33), (0.73, -0.5, 2.01), (3.34, -0.5, 2.55))):
    m.slot(f"Floating{i + 1}", p, yaw=60.0 * i)
for name, p in (("#Slot#Swimming1", (0.82, -0.5, 1.52)), ("#MiscStart1", (0.82, -0.5, 1.52)),
                ("#MiscEnd1", (3.19, -0.5, 1.7)), ("#Slot#Swimming2", (3.15, -0.5, 2.13)),
                ("#MiscStart2", (3.15, -0.5, 2.13)), ("#MiscEnd2", (0.78, -0.5, 2.44))):
    m.slots.append({"name": name, "raw": True, "local_pos": p})
cells = [block("Any", "None", "None") for _ in range(4)] + \
        [block("Any", "Bottom, Top, Corners, Path, Middle", "None") for _ in range(8)] + \
        [block("GroundOrStackable", "Bottom, Top, Corners, Path, Middle", "None") for _ in range(4)] + \
        [block("Any", "Bottom", "None") for _ in range(8)]
m.blocks = cells
m.entrance(1, -1, 1)
m.extra["access"] = {"X": 1.5, "Y": 0.0, "Z": 0.3}
m.extra["baseZ"] = 1
m.collider((2.0, -0.1, 0.5), (4.0, 0.2, 1.0))
m.collider((0.42, 0.6, 0.42), (0.7, 1.2, 0.7))
m.collider((3.5, 0.3, 2.05), (0.9, 2.4, 1.5))
m.notes += ["Blocks, BaseZ 1, entrance (1, -1, 1), water cell and slots as the vanilla Lido; the swimming patrols run "
            "between #MiscStart/#MiscEnd markers named as vanilla's."]
m.build()
