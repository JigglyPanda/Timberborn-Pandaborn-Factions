"""Festival Square: where the Lantern Festival is called and its goods are kept. 3x3 (a storage until the festival
code exists; the catalogue's stand-in is the Small Warehouse, so the blueprint takes size and blocks from here).

A paved square framed by a timber gateway with a small grey-tile roof at the front (two posts, a lintel, red lanterns,
no inscription); in the middle a tall lantern pole with strings of red lanterns running out to bamboo poles at the
corners; a raised drum stand with a big drum at the back; stacks of lantern boxes, baskets and rolled paper by the
sides; indigo banners. The postcard of the faction's festival.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, block  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("FestivalSquare", size=(3, 3, 2), seed=223, stand_in="SmallWarehouse.Folktails")
g = m.geo
# paving: flat stones over earth, a stone kerb
K.box(g, (0.03, 0.0, 0.03), (2.97, 0.06, 2.97), EARTH, (0.02, 0.02, 0.98, 0.98), skip=(3,))
K.stones(g, 0.12, 0.12, 2.88, 2.88, y=0.02, size=0.3, h=0.04, ring=False, skip=0.05, tone=(0.66, 0.65, 0.6))
K.stones(g, 0.04, 0.04, 2.96, 2.96, y=-0.01, size=0.32, h=0.12, skip=0.05)
# the gateway at the front
for x in (0.75, 2.25):
    K.box(g, (x - 0.12, 0.0, 0.0), (x + 0.12, 0.16, 0.24), PLASTER, (0.1, 0.1, 0.9, 0.9), skip=(3,), tags={"stone"})
    g.parts[-1].C = np.tile([0.6, 0.6, 0.58, 1.0], (len(g.parts[-1].P), 1))
    K.beam(g, (x, 0.1, 0.12), (x, 1.65, 0.12), w=0.12, caps="end", tags={"frame"})
K.beam(g, (0.45, 1.45, 0.12), (2.55, 1.45, 0.12), w=0.11, h=0.14, tags={"frame"})
K.beam(g, (0.6, 1.2, 0.12), (2.4, 1.2, 0.12), w=0.07, tags={"frame"})
K.cloth(g, [(1.05, 1.22, 0.08), (1.95, 1.22, 0.08), (1.95, 1.43, 0.08), (1.05, 1.43, 0.08)], DETAILS, DET_CLOTH,
        sag=0.0, nu=2, nv=1, wave=0.0)
K.roof(g, 0.5, 0.0, 2.5, 0.26, 1.55, 1.82, kind="gable", overhang=0.16, sag=0.03, lift=0.05, ridge_ends=0.06,
       tile=0.22, course=0.2)
for x in (0.75, 2.25):
    K.lantern(g, (x + (0.25 if x > 1.5 else -0.25), 1.43, 0.12), r=0.09, h=0.2)
# the lantern pole and its strings to the corner poles
P = (1.5, 0.0, 1.6)
K.pole(g, P, (1.5, 2.75, 1.6), r=0.06, material=TIMBER, sides=6, bend=0.003, taper=0.85)
K.lathe(g, [(0.0, 0.0), (0.18, 0.0), (0.12, 0.06), (0.0, 0.08)], (1.5, 2.72, 1.6), 8, TILE,
        uv_region=(0.0, TILE_COURSES[1][0], 0.25, TILE_COURSES[1][1]))
K.lantern(g, (1.5, 2.6, 1.6), r=0.14, h=0.32)
for (x, z) in ((0.15, 0.7), (2.85, 0.7), (2.85, 2.85), (0.15, 2.85)):
    K.pole(g, (x, 0.0, z), (x, 1.75, z), r=0.035, material=BAMBOO_GOLD, sides=5, bend=0.01)
    K.lantern_string(g, (1.5, 2.2, 1.6), (x, 1.7, z), n=3, sag=0.25)
# drum stand at the back
K.box(g, (1.05, 0.06, 2.45), (1.95, 0.32, 2.92), TIMBER, WOOD_BLOCK, skip=(3,))
for x in (1.25, 1.75):
    K.beam(g, (x, 0.32, 2.7), (x, 0.95, 2.7), w=0.05)
K.lathe(g, [(0.0, -0.18), (0.24, -0.18), (0.27, 0.0), (0.24, 0.18), (0.0, 0.18)], (1.5, 0.75, 2.7), 12, DETAILS,
        uv_region=DET_RED, axis=(1, 0, 0))
for sx in (-1, 1):
    K.lathe(g, [(0.0, 0.0), (0.25, 0.0)], (1.5 + sx * 0.181, 0.75, 2.7), 12, DETAILS, uv_region=DET_SACK,
            axis=(sx, 0, 0), cap_top=False)
# festival goods: lantern boxes, baskets, rolled paper
for k in range(4):
    x, z, y = 0.3 + 0.32 * (k % 2), 1.3 + 0.36 * (k // 2), 0.06
    K.box(g, (x - 0.14, y, z - 0.14), (x + 0.14, y + 0.26, z + 0.14), DETAILS, DET_CRATE, skip=(3,))
K.box(g, (0.32, 0.32, 1.32), (0.58, 0.56, 1.58), DETAILS, DET_CRATE, skip=(3,))
K.basket(g, (2.55, 0.06, 1.35), h=0.2, r=0.16)
K.basket(g, (2.65, 0.06, 1.75), h=0.16, r=0.13, material=WEAVE)
for k in range(3):
    K.tube(g, [(2.35 + 0.08 * k, 0.1, 2.05), (2.35 + 0.08 * k, 0.1, 2.4)], [0.04, 0.04], PAPER, sides=6,
           strips=[(0.36, 0.05, 0.6, 0.6)])
m.blocks = [block("GroundOrStackable", "Floor, Bottom, Corners, Path, Middle", "None") for _ in range(9)] + \
           [block("Any", "None", "None") for _ in range(9)]
m.entrance(1, -1, 0)
m.extra["access"] = {"X": 1.5, "Y": 0.06, "Z": 0.6}
m.collider((1.5, 0.1, 1.5), (3.0, 0.2, 3.0))
m.collider((1.5, 1.4, 0.12), (2.3, 0.6, 0.4))
m.collider((1.5, 1.4, 1.6), (0.3, 2.8, 0.3))
m.notes += ["Stand-in Small Warehouse is 1x1: take size, blocks (walkable floor, open above), entrance and access from "
            "this file. Lanterns glow at night with an illuminator (StockpileIlluminatorSpec or EnterableIlluminatorSpec)."]
m.build()
