"""Village Hall: the Inkpaws' district centre. 3x3, the vanilla District Center's blocks, entrance and attachments.

A broad farmstead hall on a stone platform: a grey-tile gable roof with a lean-to over a front veranda, a bamboo
signal mast at the back corner holding the district fire (the vanilla 'Fire' attachment) in an iron basket, indigo banners with the ink
bamboo either side of the steps, red lanterns at the veranda corners, goods stacked by the walls.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("VillageHall", size=(3, 3, 5), seed=23, stand_in="DistrictCenter.Folktails")
g = m.geo

B = 0.18                      # platform top
X0, X1 = 0.22, 2.78           # hall walls
Z0, Z1 = 0.78, 2.72
TOP = 1.42                    # hall wall plate
RIDGE = 2.38
VZ = 0.24                     # veranda front line

# stone platform with steps at the front centre
K.plinth(g, 0.04, 0.06, 2.96, 2.94, h=B)
for i, (z, y) in enumerate(((-0.12, 0.06), (-0.02, 0.12))):
    K.box(g, (1.05, 0, z), (1.95, y, z + 0.14), PLASTER, (0.1, 0.1, 0.9, 0.9), tags={"stone"})
    g.parts[-1].C = np.tile([0.64, 0.64, 0.62, 1], (len(g.parts[-1].P), 1))

with g.tagged("walls"):
    K.wall(g, (X0, Z0), (X1, Z0), B, TOP,
           openings=[("panes", 0.2, 0.5, 0.38, 0.72), ("door", 0.5, 0.56, 0.0, 0.86), ("panes", 0.8, 0.5, 0.38, 0.72)])
    K.wall(g, (X1, Z0), (X1, Z1), B, TOP, openings=[("window", 0.35, 0.4, 0.38, 0.8), ("window", 0.75, 0.4, 0.38, 0.8)])
    K.wall(g, (X1, Z1), (X0, Z1), B, TOP, openings=[("window", 0.3, 0.4, 0.4, 0.8), ("window", 0.7, 0.4, 0.4, 0.8)])
    K.wall(g, (X0, Z1), (X0, Z0), B, TOP, openings=[("window", 0.5, 0.42, 0.38, 0.8)], braces=True)

# main roof: hip-and-gable over the hall (the rural Chengdu-plain hall roof), small plastered gables on top
K.roof(g, X0, Z0, X1, Z1, TOP, RIDGE, kind="xieshan", overhang=0.26, sag=0.1, lift=0.08, ridge_ends=0.1, tile=0.3,
       course=0.34, hip_inset=0.42)
# a small stacked-tile ornament at the middle of the ridge
K.lathe(g, [(0.0, 0.0), (0.09, 0.0), (0.1, 0.06), (0.06, 0.12), (0.08, 0.17), (0.0, 0.2)], (1.5, RIDGE + 0.1, (Z0 + Z1) / 2),
        6, TILE, uv_region=(0.0, TILE_COURSES[1][0], 0.25, TILE_COURSES[1][1]))
# veranda: posts and a lean-to roof
for x in (0.3, 1.0, 2.0, 2.7):
    K.pole(g, (x, B, VZ), (x, 1.12, VZ), r=0.05, material=TIMBER, sides=6, bend=0.01, taper=0.92)
K.beam(g, (0.18, 1.12, VZ), (2.82, 1.12, VZ), w=0.08, sag=0.02, segs=2)
K.roof(g, 0.24, VZ, 2.76, Z0 - 0.02, 1.13, TOP - 0.02, kind="lean", overhang=0.16, sag=0.03, lift=0.03, ridge=False)
# veranda floor boards
K.boards(g, (0.25, B + 0.005, VZ - 0.06), (1, 0, 0), (0, 0, 1), 2.5, Z0 - VZ + 0.04, 4, TIMBER, thick=0.02)

# signal mast at the back right corner: three lashed bamboo poles carrying the district fire in an iron basket
CX, CZ, CY = 2.62, 2.86, 3.1
for k, (dx, dz) in enumerate(((-0.07, 0.0), (0.05, -0.05), (0.04, 0.06))):
    K.pole(g, (CX + dx * 1.6, B, CZ + dz * 1.6), (CX + dx * 0.6, CY, CZ + dz * 0.6), r=0.04,
           material=BAMBOO_GOLD if k else BAMBOO_GREEN, sides=6, bend=0.008)
for y in (0.9, 1.9, 2.8):
    K.lashing(g, (CX, y, CZ), (0, 1, 0), r=0.09)
K.lathe(g, [(0.0, 0.0), (0.06, 0.0), (0.16, 0.12), (0.18, 0.16)], (CX, CY, CZ), 7, IRON, cap_top=False)
for a_ in range(3):
    K.beam(g, (CX, CY - 0.2, CZ), (CX + 0.15 * np.cos(a_ * 2.1), CY + 0.12, CZ + 0.15 * np.sin(a_ * 2.1)), w=0.025,
           material=IRON, caps=False)
# banners on bamboo poles either side of the steps
for x in (0.62, 2.38):
    K.pole(g, (x, B, 0.06), (x, 1.55, 0.06), r=0.035, material=BAMBOO_GOLD, sides=5, bend=0.01)
    K.beam(g, (x - 0.2, 1.45, 0.06), (x + 0.2, 1.45, 0.06), w=0.025, caps=True, material=BAMBOO_GOLD)
    K.cloth(g, [(x - 0.17, 0.82, 0.03), (x + 0.17, 0.82, 0.03), (x + 0.17, 1.44, 0.03), (x - 0.17, 1.44, 0.03)],
            DETAILS, DET_BANNER, sag=0.0, nu=2, nv=3, wave=0.015)
# lanterns at the veranda corners, chillies by the door
for x in (0.3, 2.7):
    K.lantern(g, (x, 1.08, VZ - 0.04), r=0.08, h=0.18)
K.chilli_string(g, (1.15, 1.1, VZ + 0.05), length=0.36)
# goods by the walls: jars, sacks (baskets), a stack of poles
K.jar(g, (2.86, B, 1.2), h=0.3, r=0.11)
K.jar(g, (2.88, B, 1.48), h=0.24, r=0.09, material=TIMBER)
K.basket(g, (0.1, B, 1.3), h=0.14, r=0.12)
K.basket(g, (0.12, B, 1.6), h=0.12, r=0.1, material=WEAVE)
for k in range(4):
    K.pole(g, (0.08 + 0.065 * (k % 2), B + 0.035 + 0.06 * (k // 2), 1.95), (0.1 + 0.065 * (k % 2), B + 0.035 + 0.06 * (k // 2), 2.75),
           r=0.032, material=BAMBOO_GREEN if k % 3 else BAMBOO_GOLD, sides=5, bend=0.0)

m.entrance(1, -1, 0)
m.slot("Entrance", (1.5, B, VZ + 0.2), yaw=180)
m.attach("Fire", (CX, CY + 0.06, CZ), "district fire burns in the iron basket on the signal mast")
m.extra["access"] = {"X": 1.5, "Y": B, "Z": 0.9}
m.extra["connectionAnchor"] = {"X": CX, "Y": CY + 0.2, "Z": CZ}
m.collider((1.5, 0.8, 1.75), (2.6, 1.3, 2.0))
m.collider((1.5, 1.9, 1.75), (2.4, 0.9, 1.8))
m.collider((CX, 1.7, CZ), (0.3, 3.0, 0.3))
m.notes += ["Blocks as the vanilla District Center (3x3x5); the model rises to about 3.2.",
            "The Fire attachment moves to the signal mast's basket; ConnectionAnchorPoint should move to connectionAnchor."]
m.build()
