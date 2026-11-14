"""Steamer: steamed shoots, then steamed rice. 2x2, one worker, on the vanilla Grill's workshop blueprint.

A rammed-earth kitchen stove (zao) in front of a grey-tile lean-to, open to the sky so the steam rises free, a woven sunshade over the side bench: an iron wok under a tower of five big bamboo
steamer baskets and a cone lid, taller than the roof, breathing steam (the vanilla 'Smoke' attachment sits on the stack), a firing hole glowing at
night, a back wall of plaster with a lattice window, firewood and a basket of shoots, a water jar.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
from building import Model, solid_blocks  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("Steamer", size=(2, 2, 2), seed=79, stand_in="Grill.Folktails")
g = m.geo
B = 0.1
K.plinth(g, 0.04, 0.06, 1.96, 1.94, h=B)
# back wall (plaster, timber frame) with a lattice window, side posts
with g.tagged("walls"):
    K.wall(g, (1.86, 1.78), (0.14, 1.78), B, 1.25, openings=[("window", 0.3, 0.36, 0.45, 0.8)])
for x, z in ((0.16, 1.02), (1.84, 1.02)):
    K.pole(g, (x, B, z), (x, 1.12, z), r=0.05, material=TIMBER, sides=6, bend=0.01, taper=0.9, tags={"frame"})
K.beam(g, (0.06, 1.12, 1.02), (1.94, 1.12, 1.02), w=0.08, sag=0.02, segs=2, tags={"frame"})
for x in (0.16, 1.84):
    K.beam(g, (x, 1.14, 1.02), (x, 1.25, 1.78), w=0.06, tags={"frame"})
K.roof(g, 0.14, 1.02, 1.86, 1.78, 1.14, 1.42, kind="lean", overhang=0.18, sag=0.03, lift=0.04, ridge=False,
       tile=0.28, course=0.32)
# a woven-mat sunshade on bamboo poles over the front work area
for x in (1.4, 1.86):
    K.pole(g, (x, B, 0.12), (x, 1.0, 0.14), r=0.03, material=BAMBOO_GOLD, sides=5, bend=0.015)
K.cloth(g, [(1.34, 0.98, 0.1), (1.92, 0.98, 0.1), (1.92, 1.1, 0.95), (1.34, 1.1, 0.95)], WEAVE_GOLD,
        (0.05, 0.05, 0.95, 0.95), sag=0.04, nu=2, nv=2, wave=0.01)
# the stove: an earthen block with a firing hole, a wok and the steamer stack
SX, SZ = 0.95, 0.98
K.box(g, (0.45, B, 0.66), (1.45, 0.62, 1.3), EARTH, (0.05, 0.05, 0.95, 0.95), skip=(3,))
K.box(g, (0.43, 0.62, 0.64), (1.47, 0.66, 1.32), PLASTER, (0.1, 0.1, 0.9, 0.9), skip=(3,))
K.window(g, (SX, 0.3, 0.645), (0, 0, -1), 0.2, 0.16, frame=0.03, region=WIN_DARK, sill=False)
K.lathe(g, [(0.0, 0.0), (0.3, 0.06), (0.38, 0.12)], (SX, 0.6, SZ), 9, IRON, cap_top=False)
# the steamer tower: five big woven bamboo baskets, a tall cone lid with a vent, taller than the roof (the stack is
# the Steamer's mark from the game camera)
y = 0.7
for k, h in enumerate((0.2, 0.19, 0.19, 0.18, 0.18)):
    K.lathe(g, [(0.3, 0.0), (0.315, 0.025), (0.315, h - 0.025), (0.3, h)], (SX, y, SZ), 10,
            BAMBOO_GOLD if k % 2 else WEAVE_GOLD, cap_top=False)
    K.lathe(g, [(0.32, 0.02), (0.33, 0.035), (0.32, 0.05)], (SX, y, SZ), 10, BAMBOO_GOLD, cap_top=False)
    y += h
K.lathe(g, [(0.33, 0.0), (0.24, 0.12), (0.08, 0.26), (0.08, 0.32)], (SX, y, SZ), 10, WEAVE_GOLD, cap_top=False)
y += 0.19
STEAM_Y = y + 0.13   # the open vent at the top of the cone
# flue at the back of the stove through the roof
K.tube(g, [(1.3, 0.62, 1.2), (1.32, 1.6, 1.3)], [0.07, 0.06], EARTH, sides=6)
# firewood, a basket of shoots, a water jar, a ladle hanging on the post
for k in range(4):
    K.pole(g, (0.12, B + 0.04 + 0.06 * (k // 2), 1.4 + 0.08 * (k % 2)), (0.42, B + 0.04 + 0.06 * (k // 2), 1.45 + 0.08 * (k % 2)),
           r=0.035, material=TIMBER, sides=5, bend=0.0)
K.basket(g, (1.66, B, 0.4), h=0.14, r=0.13)
for k in range(5):
    a = k * 1.25
    K.lathe(g, [(0.0, 0.0), (0.03, 0.0), (0.0, 0.12)], (1.66 + 0.06 * np.cos(a), B + 0.12, 0.4 + 0.06 * np.sin(a)), 4,
            BAMBOO_GREEN)
K.jar(g, (1.68, B, 1.0), h=0.34, r=0.12)
K.lantern(g, (1.8, 1.04, 0.95), r=0.07, h=0.16)
m.blocks = solid_blocks(2, 2, 2)
m.entrance(1, -1, 0)
m.slot("Entrance", (1.0, B, 0.4), yaw=180)
m.attach("Smoke", (SX, STEAM_Y, SZ), "steam rises from the top of the steamer stack")
m.extra["access"] = {"X": 1.0, "Y": B, "Z": 0.7}
m.collider((1.0, 0.65, 1.2), (1.9, 1.3, 1.4))
m.notes += ["Smoke attachment (vanilla GrillSmoke prefab) placed on the steamer stack: reads as steam."]
m.build()
