"""Night Builders' Post: the Ringtails' first workplace (builders from the bell to dawn). 3x2 on the vanilla Builders'
Hut. The moon mark of the Ringtail buildings: a big round moon window glowing in a white back wall. An open timber
shed under a grey-tile lean-to, tall bamboo shear legs with a hoisted bundle of poles over the yard (its mark from the
game camera): stacks of poles and planks, a sawhorse, baskets of lashing rope, a ladder, lanterns.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, solid_blocks  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("NightBuildersPost", size=(3, 2, 2), seed=167, stand_in="BuildersHut.Folktails")
g = m.geo
B = 0.1
K.plinth(g, 0.04, 0.06, 2.96, 1.94, h=B)
with g.tagged("walls"):
    K.wall(g, (2.86, 1.78), (0.14, 1.78), B, 1.35, rail=False)
K.moon_window(g, (1.5, 0.82, 1.75), (0, 0, -1), r=0.36)
# a plastered end wall on the right closes the shed; the moon window there faces out, clear of the eave
with g.tagged("walls"):
    K.wall(g, (2.86, 0.3), (2.86, 1.78), B, 1.2, rail=False)
K.moon_window(g, (2.9, 0.72, 1.04), (1, 0, 0), r=0.32)
for x in (0.16, 1.5, 2.84):
    K.pole(g, (x, B, 0.3), (x, 1.15, 0.3), r=0.05, material=TIMBER, sides=6, bend=0.01, taper=0.9, tags={"frame"})
K.beam(g, (0.06, 1.15, 0.3), (2.94, 1.15, 0.3), w=0.08, sag=0.02, segs=2, tags={"frame"})
for x in (0.16, 2.84):
    K.beam(g, (x, 1.17, 0.3), (x, 1.36, 1.78), w=0.06, tags={"frame"})
K.roof(g, 0.14, 0.3, 2.86, 1.78, 1.17, 1.48, kind="lean", overhang=0.16, sag=0.03, lift=0.04, ridge=False,
       tile=0.3, course=0.32)
# building stores: poles, planks on trestles, a sawhorse, rope baskets, a ladder leaning on a post
for k in range(6):
    K.pole(g, (0.3, B + 0.035 + 0.06 * (k // 3), 1.2 + 0.07 * (k % 3)),
           (1.2, B + 0.035 + 0.06 * (k // 3), 1.22 + 0.07 * (k % 3)), r=0.032,
           material=BAMBOO_GOLD if k % 2 else BAMBOO_GREEN, sides=5, bend=0.0)
K.boards(g, (1.85, 0.42, 1.0), (1, 0, 0), (0, 0, 1), 0.9, 0.5, 3, TIMBER, thick=0.03)
for x in (1.9, 2.65):
    K.beam(g, (x, B, 1.25), (x, 0.4, 1.25), w=0.05, caps=False)
K.beam(g, (0.55, 0.35, 0.65), (1.05, 0.35, 0.65), w=0.06)
for x in (0.6, 1.0):
    for dz in (-0.1, 0.1):
        K.beam(g, (x, B, 0.65 + dz), (x, 0.33, 0.65), w=0.03, caps=False)
K.basket(g, (2.55, B, 0.55), h=0.15, r=0.13)
K.basket(g, (2.25, B, 0.5), h=0.12, r=0.1, material=WEAVE)
K.ladder(g, (1.62, B, 0.36), (1.56, 1.1, 0.32), width=0.26, rungs=5)
for x in (0.16, 2.84):
    K.lantern(g, (x, 1.08, 0.22), r=0.07, h=0.16)
# the builders' mark from the game camera: tall bamboo shear legs over the yard, a pulley and a rope with a bundle of
# poles hanging from it, taller than the roof
TOPH = np.array([0.45, 2.6, 0.05])
for foot in ((-0.05, B, -0.15), (1.0, B, -0.15), (0.4, B, 0.85)):
    K.pole(g, foot, tuple(TOPH), r=0.035, material=BAMBOO_GOLD, sides=5, bend=0.008)
K.lashing(g, tuple(TOPH - [0, 0.08, 0]), (0, 1, 0), r=0.07)
K.wheel(g, tuple(TOPH - [0, 0.2, 0]), (1, 0, 0), 0.09, width=0.04, spokes=4, rim_r=0.015, material=TIMBER)
K.beam(g, tuple(TOPH - [0, 0.2, 0.09]), (0.55, 0.95, 0.11), w=0.012, material=DETAILS, caps=False)
for k in range(5):
    K.pole(g, (0.3, 0.9 - 0.05 * (k % 2), 0.08 + 0.04 * k), (0.8, 0.95 - 0.05 * (k % 2), 0.1 + 0.04 * k), r=0.025,
           material=BAMBOO_GREEN, sides=4, bend=0.0)
PX, PZ, PH = 2.6, 1.86, 1.55
# the moon mark seen from the high camera: a glowing moon plaque on a bamboo pole above the roof, a crescent on top
K.pole(g, (PX, 0.0, PZ), (PX, PH + 0.55, PZ), r=0.035, material=BAMBOO_GOLD, sides=5, bend=0.005)
K.moon_window(g, (PX, PH + 0.2, PZ - 0.045), (0, 0, -1), r=0.2)
arc = [(PX + 0.13 * math.cos(t), PH + 0.65 + 0.13 * math.sin(t), PZ) for t in np.linspace(-1.9, 1.9, 7)]
K.tube(g, arc, [0.01, 0.025, 0.032, 0.035, 0.032, 0.025, 0.01], BAMBOO_GOLD, sides=5, caps=False)
m.blocks = solid_blocks(3, 2, 2)
m.entrance(1, -1, 0)
m.slot("Entrance", (1.5, B, 0.5), yaw=180)
m.extra["access"] = {"X": 1.5, "Y": B, "Z": 0.6}
m.collider((1.5, 0.7, 1.0), (2.9, 1.4, 1.9))
m.notes += ["Ringtail mark: the round moon window (kit moon_window), lit by WorkplaceIlluminatorSpec on the night shift."]
m.build()
