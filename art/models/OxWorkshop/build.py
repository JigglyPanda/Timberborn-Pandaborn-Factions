"""Ox Workshop: builds the Wooden Oxen. 3x3x1 on the vanilla Bot Assembler (its blocks, driveway out of the front
centre, power input and BotManufactoryAnimationController, which turns the transform named by RingName about its
up axis and the one named by DrillName about its forward axis while an ox is being built).

A low carpenters' yard: in the middle a great round timber turntable with a red-lacquered rim (the RingName node,
'#OxTurntable') carrying a stout cradle of trestles where the ox is put together; at the back a tiled lean-to over a
workbench with a carpenter's auger turning in a vise (the DrillName node, '#OxAuger'), racks of tools, stacks of
squared timber and finished wheels; the front centre left clear for the driveway. From the game camera: the big red
ring in a yard of timber. (The Wooden Ox itself is the bot body, not part of this model.)
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, solid_blocks  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("OxWorkshop", size=(3, 3, 1), seed=353, stand_in="BotAssembler.Folktails", overhang=0.4)
g = m.geo
B = 0.08
K.plinth(g, 0.04, 0.04, 2.96, 2.96, h=B)
K.boards(g, (0.25, B, 0.3), (0, 0, 1), (1, 0, 0), 1.9, 2.5, 10, TIMBER, thick=0.03)
TC = np.array([1.5, B + 0.03, 1.35])
with g.node("#OxTurntable"):
    K.lathe(g, [(0.0, 0.0), (0.98, 0.0), (1.0, 0.06), (0.0, 0.06)], TC, 16, TIMBER, uv_region=WOOD_BLOCK)
    K.lathe(g, [(0.96, 0.0), (1.02, 0.02), (1.02, 0.07), (0.94, 0.075)], TC, 16, DETAILS, uv_region=DET_RED,
            cap_top=False)
    for k in range(8):    # spokes of the turntable's planking, painted
        a = 2 * math.pi * k / 8
        K.beam(g, TC + [math.cos(a) * 0.2, 0.065, math.sin(a) * 0.2], TC + [math.cos(a) * 0.92, 0.065, math.sin(a) * 0.92],
               w=0.04, h=0.012, material=DETAILS, caps=False)
        g.parts[-1].C = np.tile([0.55, 0.16, 0.1, 1.0], (len(g.parts[-1].P), 1))
    # the cradle: two trestles and a yoke beam
    for dz in (-0.35, 0.35):
        for dx in (-0.25, 0.25):
            K.beam(g, TC + [dx * 1.3, 0.06, dz], TC + [dx * 0.6, 0.5, dz], w=0.06)
        K.beam(g, TC + [-0.35, 0.5, dz], TC + [0.35, 0.5, dz], w=0.08, h=0.07)
    K.beam(g, TC + [0, 0.56, -0.5], TC + [0, 0.56, 0.5], w=0.09, h=0.07)
m.animate("#OxTurntable", TC, (0, 1, 0), kind="static",
          driver="BotManufactoryAnimationControllerSpec.RingName (turns about its up axis)")
# the back lean-to and the workbench with the auger
for x in (0.1, 1.5, 2.9):
    K.pole(g, (x, B, 2.35), (x, 0.98, 2.35), r=0.045, material=TIMBER, sides=6, bend=0.008, taper=0.92)
with g.tagged("walls"):
    K.wall(g, (2.9, 2.9), (0.1, 2.9), B, 1.25)
K.roof(g, 0.1, 2.35, 2.9, 2.9, 0.98, 1.25, kind="lean", overhang=0.14, sag=0.02, lift=0.02, ridge=False, tile=0.26,
       course=0.26)
K.box(g, (1.75, 0.45, 2.45), (2.75, 0.5, 2.8), TIMBER, WOOD_BLOCK, skip=(3,))
for x in (1.8, 2.7):
    for z in (2.5, 2.75):
        K.beam(g, (x, B, z), (x, 0.45, z), w=0.045, caps=False)
K.box(g, (2.2, 0.5, 2.55), (2.32, 0.66, 2.75), IRON, (0.1, 0.1, 0.9, 0.9))
AC = np.array([2.26, 0.62, 2.45])
with g.node("#OxAuger"):
    K.tube(g, [AC + [0, 0, 0.05], AC + [0, 0, -0.38]], [0.022, 0.01], IRON, sides=5)
    K.beam(g, AC + [-0.14, 0, 0.0], AC + [0.14, 0, 0.0], w=0.035, caps="end")
m.animate("#OxAuger", AC, (0, 0, 1), kind="static",
          driver="BotManufactoryAnimationControllerSpec.DrillName (turns about its forward axis)")
# tool rack, squared timber, finished wheels and legs waiting
for k in range(5):
    x = 0.3 + 0.18 * k
    K.beam(g, (x, 0.5, 2.82), (x, 1.0, 2.84), w=0.03, caps="end")
for k in range(3):
    for j in range(2):
        K.beam(g, (0.15 + 0.13 * j, B + 0.05 + 0.1 * k, 0.4), (0.15 + 0.13 * j, B + 0.05 + 0.1 * k, 1.9), w=0.1, h=0.09)
for k, z in enumerate((0.55, 0.95)):
    K.wheel(g, (2.75, 0.3, z), (1, 0, 0), 0.24, width=0.06, spokes=6, rim_r=0.03, material=TIMBER)
K.lantern(g, (0.1, 0.92, 2.3), r=0.06, h=0.14)
m.blocks = solid_blocks(3, 3, 1)
m.entrance(1, -1, 0)
m.slot("Entrance", (2.0, B, 2.2), yaw=0)
m.extra["access"] = {"X": 1.5, "Y": B, "Z": 0.1}
m.extra["botManufactoryAnimation"] = {"RingName": "#OxTurntable", "DrillName": "#OxAuger"}
m.attach("Smoke", (1.5, 0.6, 1.4), "the vanilla bot-assembler smoke (sawdust) over the turntable")
m.collider((1.5, 0.3, 1.5), (2.8, 0.6, 2.8))
m.collider((1.5, 0.8, 2.65), (2.8, 0.6, 0.6))
m.notes += ["Blocks and driveway as the vanilla Bot Assembler (3x3x1, NarrowCenter driveway); the front centre is kept "
            "clear. Set BotManufactoryAnimationControllerSpec RingName/DrillName from botManufactoryAnimation."]
m.build()
