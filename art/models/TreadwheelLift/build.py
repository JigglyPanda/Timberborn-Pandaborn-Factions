"""Treadwheel Lift: lifts water by walking. 2x3x3 on the vanilla Water Pump (BaseZ 1: the model's y = 0 is the
ground the house stands on, one level above the water; cell (0, 2) is the intake column over the water, where the
vanilla pump hangs its pipe).

The square-pallet chain pump of the Sichuan paddies (the "dragon's backbone"): a long covered wooden trough slopes
from the water at the back up to a sprocket on a horizontal axle, which the worker turns by treading the pegged
spokes of a treadle drum while leaning on a rail under a small tiled roof; the water spills into a wooden tub at the
front. The treadle drum and sprocket turn ('#TreadAxle', played by WorkshopAnimationController while it works).
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("TreadwheelLift", size=(2, 3, 3), seed=359, stand_in="WaterPump.Folktails", overhang=0.3)
g = m.geo
B = 0.1
K.plinth(g, 0.04, 0.04, 1.96, 1.96, h=B)
AY, AZ = 0.82, 1.55
# frame: four posts, the lean rail, a little tiled roof
for (x, z) in ((0.12, 1.05), (1.88, 1.05), (0.12, 1.95), (1.88, 1.95)):
    K.pole(g, (x, B, z), (x, 1.85, z), r=0.05, material=TIMBER, sides=6, bend=0.006, taper=0.92, tags={"frame"})
K.beam(g, (0.12, 1.45, 1.05), (1.88, 1.45, 1.05), w=0.05, caps=False)       # the rail the treader leans on
K.roof(g, 0.12, 1.05, 1.88, 1.95, 1.85, 2.15, kind="gable", overhang=0.16, sag=0.04, lift=0.04, ridge_ends=0.05,
       tile=0.26, course=0.26)
for x in (0.12, 1.88):
    K.beam(g, (x, AY, 1.05), (x, AY, 1.95), w=0.07)
# the axle with the treadle drum (pegged spokes in two rows) and the sprocket for the chain
with g.node("#TreadAxle"):
    K.tube(g, [(0.08, AY, AZ), (1.92, AY, AZ)], [0.07, 0.07], TIMBER, sides=8)
    for x in (1.15, 1.6):
        K.lathe(g, [(0.12, -0.08), (0.14, 0.0), (0.12, 0.08)], (x, AY, AZ), 8, TIMBER, axis=(1, 0, 0), cap_top=False)
        for k in range(6):
            a = 2 * math.pi * k / 6 + (0.5 if x > 1.3 else 0.0)
            d = np.array([0, math.cos(a), math.sin(a)])
            K.beam(g, np.array([x, AY, AZ]) + d * 0.1, np.array([x, AY, AZ]) + d * 0.42, w=0.045, caps="end")
            K.beam(g, np.array([x - 0.1, AY, AZ]) + d * 0.42, np.array([x + 0.1, AY, AZ]) + d * 0.42, w=0.07,
                   h=0.04, material=BAMBOO_GOLD)
    K.wheel(g, (0.5, AY, AZ), (1, 0, 0), 0.3, width=0.12, spokes=6, rim_r=0.03, material=TIMBER)
m.animate("#TreadAxle", (1.0, AY, AZ), (1, 0, 0), turns=1, direction=-1,
          driver="WorkshopAnimationControllerSpec (plays while the lift works)")
# the chain trough: from the sprocket down the back into the water at the intake column (0, 2)
TOPP = np.array([0.5, AY - 0.05, AZ + 0.05])
BOT = np.array([0.5, -1.05, 2.85])
d = (BOT - TOPP) / np.linalg.norm(BOT - TOPP)
side = np.array([1.0, 0, 0])
up = np.cross(d, side)
L = np.linalg.norm(BOT - TOPP)
for sx in (-0.13, 0.13):
    K.beam(g, TOPP + side * sx, BOT + side * sx, w=0.03, h=0.2, material=TIMBER, up=tuple(up))
K.beam(g, TOPP - up * 0.1, BOT - up * 0.1, w=0.28, h=0.025, material=TIMBER, up=tuple(up))
for k in range(int(L / 0.14)):   # the square pallets of the chain, riding up the trough
    p = TOPP + d * (0.1 + k * 0.14)
    K.box(g, p - side * 0.11 - up * 0.08, p + side * 0.11 + up * 0.06 + d * 0.025, WEAVE_GOLD, (0.1, 0.1, 0.9, 0.9))
for t in (0.45, 0.85):           # stakes holding the trough over the bank and in the water
    p = TOPP + (BOT - TOPP) * t
    for sx in (-0.18, 0.18):
        K.pole(g, p + side * sx, (p[0] + sx, -1.2, p[2]), r=0.03, material=BAMBOO_GOLD, sides=4, bend=0.0)
# the tub the water spills into, buckets, a lantern
K.lathe(g, [(0.0, 0.0), (0.3, 0.0), (0.33, 0.36), (0.31, 0.38), (0.0, 0.3)], (0.5, B, 0.62), 10, WEAVE_GOLD,
        cap_top=False)
K.lathe(g, [(0.3, 0.3), (0.0, 0.3)], (0.5, B, 0.62), 10, WINDOWS, uv_region=LANTERN_GLOW, cap_top=False)
g.parts[-1].C = np.tile([0.35, 0.5, 0.55, 1.0], (len(g.parts[-1].P), 1))
K.channel(g, 0.92, AZ - 0.05, AY - 0.25, 0.5, r_in=0.08, wall=0.02, material=BAMBOO_GREEN, around=5, sleeve=False,
          tilt=0.35)
for k, (x, z) in enumerate(((1.2, 0.35), (1.45, 0.42))):
    K.barrel(g, (x, B, z), h=0.26, r=0.11, material=BAMBOO_GOLD)
K.lantern(g, (1.88, 1.78, 1.0), r=0.06, h=0.14)
m.entrance(1, -1, 1)
m.slot("Entrance", (1.4, B, 1.2), yaw=0)
m.extra["access"] = {"X": 1.0, "Y": B, "Z": 0.1}
m.extra["intake"] = "the trough's foot stands in the intake column, cell (0, 2), at y = -1 (one level down, in the water)"
m.collider((1.0, 1.0, 1.5), (1.9, 1.9, 1.0))
m.collider((0.5, -0.1, 2.2), (0.4, 2.0, 1.6))
m.notes += ["Blocks, BaseZ 1, entrance (1, -1, 1) and water input as the vanilla Water Pump (2x3x3). Its "
            "WaterInputPipeSpec still hangs the vanilla pipe segments: drop that spec when adopting (the trough is "
            "the intake)."]
m.build()
