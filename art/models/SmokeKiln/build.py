"""Smoke Kiln: cures poles in smoke. 2x4 on the vanilla Wood Workshop (one worker).

A long rammed-earth kiln vault running back from a timber firing shed: poles stacked into the vault's mouth, a squat
plastered chimney at the far end, a grey-tile lean-to over the stoking pit with firewood and a pile of cured,
smoke-darkened poles waiting by the door.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, solid_blocks  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("SmokeKiln", size=(2, 4, 4), seed=269, stand_in="WoodWorkshop.Folktails")
g = m.geo
B = 0.1
K.plinth(g, 0.04, 0.05, 1.96, 3.95, h=B)
# the kiln vault: a half-cylinder of rammed earth along z from 1.4 to 3.7, plastered ends
VZ0, VZ1, R = 1.35, 3.7, 0.8
n0 = len(g.parts)
K.channel(g, VZ0, VZ1, B + 0.02 - R, 1.0, r_in=R - 0.1, wall=0.1, material=EARTH, around=8, rim_y=B + 0.0, sleeve=False)
for p in g.parts[n0:]:      # turn the trough over into a vault: mirror y about the plinth top
    p.P[:, 1] = 2 * B - p.P[:, 1]
    p.N[:, 1] = -p.N[:, 1]
    p.T = fix_winding(p.P, p.N, p.T)
K.lathe(g, [(0.0, 0.0), (R + 0.02, 0.0)], (1.0, B, VZ1), 10, PLASTER, uv_region=(0.1, 0.1, 0.9, 0.9), axis=(0, 0, 1),
        cap_top=False)
for k in range(5):   # the stacked ends of poles in the vault's mouth
    a = math.pi * (0.15 + 0.7 * k / 4)
    for rr in (0.25, 0.5):
        c = np.array([1.0 + math.cos(a) * rr, B + math.sin(a) * rr, VZ0 - 0.02])
        K.tube(g, [c, c + [0, 0, 0.12]], [0.05, 0.05], BAMBOO_GOLD, sides=5, caps="start")
K.box(g, (0.75, B + 0.6, 3.35), (1.25, 1.75, 3.65), PLASTER, (0.05, 0.05, 0.95, 0.95), skip=(3,))
K.box(g, (0.7, 1.75, 3.3), (1.3, 1.8, 3.7), TILE, (0.0, TILE_COURSES[0][0], 0.3, TILE_COURSES[0][1]), skip=(3,))
# firing shed over the stoking pit at the front
for (x, z) in ((0.12, 0.15), (1.88, 0.15), (0.12, 1.3), (1.88, 1.3)):
    K.pole(g, (x, B, z), (x, 1.2, z), r=0.05, material=TIMBER, sides=6, bend=0.01, taper=0.92, tags={"frame"})
K.beam(g, (0.05, 1.2, 0.15), (1.95, 1.2, 0.15), w=0.07, tags={"frame"})
K.roof(g, 0.12, 0.15, 1.88, 1.3, 1.2, 1.5, kind="lean", overhang=0.15, sag=0.03, lift=0.03, ridge=False, tile=0.28,
       course=0.3)
for k in range(4):
    K.pole(g, (0.2, B + 0.04 + 0.06 * (k // 2), 0.5 + 0.08 * (k % 2)), (0.6, B + 0.04 + 0.06 * (k // 2),
           0.55 + 0.08 * (k % 2)), r=0.035, material=TIMBER, sides=5, bend=0.0)
for k in range(6):   # cured poles, smoke-darkened, waiting by the door
    n1 = len(g.parts)
    K.pole(g, (1.25, B + 0.03 + 0.055 * (k // 3), 0.35 + 0.07 * (k % 3)), (1.9, B + 0.03 + 0.055 * (k // 3),
           0.38 + 0.07 * (k % 3)), r=0.03, material=BAMBOO_GOLD, sides=5, bend=0.0)
    for p in g.parts[n1:]:
        p.C = np.tile([0.62, 0.5, 0.36, 1.0], (len(p.P), 1))
# the stoker's box bellows at the vault's mouth: its push handle rocks while the kiln works (the Wood Workshop's
# WorkshopAnimationController needs an animated node: without one it throws when the building is finished)
K.box(g, (0.25, B, 1.05), (0.55, 0.3, 1.3), TIMBER, WOOD_BLOCK, skip=(3,))
K.tube(g, [(0.55, 0.2, 1.18), (0.72, 0.18, 1.25)], [0.03, 0.025], IRON, sides=5)
BP = np.array([0.4, 0.32, 1.05])
with g.node("#BellowsHandle"):
    K.beam(g, BP, BP + [0.0, 0.0, -0.42], w=0.035, caps="end")
    K.beam(g, BP + [-0.12, 0.0, -0.42], BP + [0.12, 0.0, -0.42], w=0.03, caps="end")
m.animate("#BellowsHandle", BP, (1, 0, 0), kind="swing", amplitude=0.35, turns=1,
          driver="WorkshopAnimationControllerSpec (plays while the kiln works)")
m.blocks = solid_blocks(2, 4, 4)
m.entrance(1, -1, 0)
m.slot("Entrance", (1.0, B, 0.6), yaw=180)
m.attach("Smoke", (1.0, 1.85, 3.5), "chimney smoke, if the blueprint gives the kiln a smoke attachment")
m.extra["access"] = {"X": 1.0, "Y": B, "Z": 0.8}
m.collider((1.0, 0.5, 2.5), (1.8, 1.0, 2.4))
m.collider((1.0, 0.7, 0.7), (1.9, 1.4, 1.2))
m.build()
