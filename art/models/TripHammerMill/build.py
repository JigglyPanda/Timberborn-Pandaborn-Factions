"""Trip-Hammer Mill: water pounds rice into rice flour. 3x2x3 on the vanilla Gristmill's blueprint (workshop,
entrance (2, -1, 0); its WorkshopAnimationController plays every animated node while the mill works).

The water-driven trip hammer of the Sichuan valleys: on the left a stone-lined race (the two cells at x = 0) with a
bamboo-and-timber paddle wheel turning in it; its axle runs right under a tiled lean-to, and pegs on the axle press
down the tails of two long timber hammer beams, so their heads rise and fall into stone mortars of rice at the open
front. Sacks of rice and flour, sieves, a lantern. From the game camera: the wheel and the two long beams nodding
over their mortars beside a small tiled roof.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, solid_blocks  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("TripHammerMill", size=(3, 2, 3), seed=341, stand_in="Gristmill.Folktails")
g = m.geo
B = 0.1
AX_Y, AX_Z = 0.62, 1.42           # the axle
WC = np.array([0.5, AX_Y, AX_Z])  # the wheel's centre
# the race: a stone-lined channel along the left cells, its floor sunk below ground
K.box(g, (0.06, -0.12, 0.0), (0.94, -0.08, 2.0), EARTH, (0.05, 0.05, 0.95, 0.95), skip=(3,))
for x0 in (0.0, 0.88):
    K.stones(g, x0, 0.02, x0 + 0.12, 1.98, y=-0.1, size=0.2, h=0.26, ring=False)
# the mill floor: a plinth under the shed and the hammer yard
K.plinth(g, 1.04, 0.05, 2.96, 1.95, h=B)
# the lean-to over the axle and the hammer tails
for x in (1.06, 2.0, 2.94):
    K.pole(g, (x, B, 0.95), (x, 1.3, 0.95), r=0.05, material=TIMBER, sides=6, bend=0.008, taper=0.92, tags={"frame"})
with g.tagged("walls"):
    K.wall(g, (2.94, 1.9), (1.06, 1.9), B, 1.62, openings=[("window", 0.62, 0.55, 0.45, 0.85)])
K.beam(g, (1.0, 1.3, 0.95), (3.0, 1.3, 0.95), w=0.08, sag=0.015, segs=2, tags={"frame"})
K.roof(g, 1.06, 0.95, 2.94, 1.9, 1.3, 1.62, kind="lean", overhang=0.18, sag=0.03, lift=0.03, ridge=False, tile=0.28,
       course=0.3)
# axle bearings: two timber trestles, one each side of the race wall
for x in (1.0, 2.75):
    K.beam(g, (x, B, AX_Z), (x, AX_Y + 0.08, AX_Z), w=0.1, caps="end")
# the wheel, its axle and the pegs that trip the hammers (one node, turning about x)
HX = (1.42, 2.08)
with g.node("#MillWheel"):
    K.wheel(g, WC, (1, 0, 0), 0.56, width=0.32, spokes=8, rim_r=0.035, material=BAMBOO_GOLD, paddles=8,
            paddle_depth=0.22)
    K.tube(g, [WC + [-0.25, 0, 0], (2.85, AX_Y, AX_Z)], [0.07, 0.07], TIMBER, sides=8)
    for x in HX:
        for k in range(2):
            a = math.pi * k
            d = np.array([0, math.cos(a), math.sin(a)])
            K.beam(g, (x, AX_Y, AX_Z) + d * 0.04, (x, AX_Y, AX_Z) + d * 0.2, w=0.05, caps="end")
m.animate("#MillWheel", WC, (1, 0, 0), turns=1, direction=-1,
          driver="WorkshopAnimationControllerSpec (plays while the mill works)")
# the hammers: long beams pivoted on a low frame, tails over the axle pegs, heads over stone mortars at the front
PZ, PY = 0.98, 0.5
for x in HX:
    K.beam(g, (x - 0.12, B, PZ), (x - 0.12, PY, PZ), w=0.06, caps="end")
    K.beam(g, (x + 0.12, B, PZ), (x + 0.12, PY, PZ), w=0.06, caps="end")
    K.beam(g, (x - 0.15, PY, PZ), (x + 0.15, PY, PZ), w=0.03, material=IRON, caps=False)
    K.lathe(g, [(0.0, 0.0), (0.2, 0.0), (0.22, 0.24), (0.12, 0.26), (0.1, 0.12), (0.0, 0.12)], (x, B, 0.3), 8,
            PLASTER, uv_region=(0.1, 0.1, 0.9, 0.9))
    g.parts[-1].C = np.tile([0.6, 0.6, 0.58, 1.0], (len(g.parts[-1].P), 1))
    K.lathe(g, [(0.0, 0.0), (0.1, 0.01), (0.0, 0.02)], (x, B + 0.13, 0.3), 6, WEAVE)   # rice in the mortar
for i, x in enumerate(HX):
    node = f"#Hammer{i + 1}"
    with g.node(node):
        K.beam(g, (x, PY + 0.06, AX_Z + 0.1), (x, PY + 0.02, 0.32), w=0.1, h=0.09)
        K.beam(g, (x, PY + 0.02, 0.32), (x, B + 0.36, 0.3), w=0.12, caps="end")   # the pestle head
        K.lathe(g, [(0.07, 0.0), (0.07, 0.03)], (x, B + 0.36, 0.3), 6, IRON, cap_top=False)
    m.animate(node, (x, PY, PZ), (1, 0, 0), kind="trip", turns=2, amplitude=0.32, phase=0.5 * i,
              driver="WorkshopAnimationControllerSpec (plays while the mill works)")
# sacks of rice and flour, sieves, a lantern
for k, (x, z) in enumerate(((2.55, 0.35), (2.75, 0.55), (2.6, 0.75))):
    K.lathe(g, [(0.0, 0.0), (0.13, 0.02), (0.14, 0.18), (0.08, 0.3), (0.0, 0.31)], (x, B, z), 6, DETAILS,
            uv_region=(0.53, 0.55, 0.72, 0.95))
K.tray(g, (2.6, B + 0.02, 1.35), r=0.22, leaf=WEAVE, fill=0.7)
K.tray(g, (2.6, B + 0.06, 1.35), r=0.2, leaf=None)
K.lantern(g, (2.94, 1.22, 0.92), r=0.07, h=0.16)
m.blocks = solid_blocks(3, 2, 3)
m.entrance(2, -1, 0)
m.slot("Entrance", (2.5, B, 0.15), yaw=180)
m.extra["access"] = {"X": 2.5, "Y": B, "Z": 0.05}
m.extra["wheelCells"] = [{"X": 0, "Y": 0, "Z": 0}, {"X": 0, "Y": 1, "Z": 0}]
m.extra["waterPoweredGeneratorBlocks"] = "the wheel turns in the race over cells (0, 0, 0) and (0, 1, 0); either can be the WaterPoweredGeneratorSpec block standing in the current (the wheel's lowest paddles are at (0.5, 0.06, 1.42), cell (0, 1))"
m.collider((2.0, 0.8, 1.42), (2.0, 1.4, 1.0))
m.collider((0.5, 0.6, 1.42), (0.4, 1.2, 1.2))
m.collider((1.75, 0.4, 0.5), (1.4, 0.7, 0.9))
m.notes += ["On the Gristmill's blocks (all solid) until the water module decides which cell stands in the current.",
            "Animated nodes: #MillWheel turns once per loop; #Hammer1/#Hammer2 trip twice per loop, half a lift apart."]
m.build()
