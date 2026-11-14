"""Village Hall: the Inkpaws' district centre. 3x3, the vanilla District Center's blocks, entrance and attachments.

A broad farmstead hall filling its stone platform, under a hip-and-gable grey-tile roof with a lean-to over the front
veranda; at the front left an open timber bell tower, one small tiled roof on top, holding the bronze afternoon bell
(the faction's one rule, DESIGN Pillar 3) with its rope hanging to the veranda; at the back right a bamboo signal mast
with the district fire in an iron basket (the vanilla 'Fire' attachment); indigo banners with the ink bamboo either
side of the steps, red lanterns, goods stacked by the walls.
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

B = 0.2                       # platform top
X0, X1 = 0.12, 2.88           # hall walls: the whole width
Z0, Z1 = 0.9, 2.86
TOP = 1.62                    # hall wall plate
RIDGE = 2.7
VZ = 0.2                      # veranda front line

# stone platform with steps at the front centre
K.plinth(g, 0.02, 0.04, 2.98, 2.96, h=B)
for i, (z, y) in enumerate(((-0.14, 0.07), (-0.03, 0.14))):
    K.box(g, (1.0, 0, z), (2.0, y, z + 0.14), PLASTER, (0.1, 0.1, 0.9, 0.9), tags={"stone"})
    g.parts[-1].C = np.tile([0.64, 0.64, 0.62, 1], (len(g.parts[-1].P), 1))

with g.tagged("walls"):
    K.wall(g, (X0, Z0), (X1, Z0), B, TOP,
           openings=[("panes", 0.17, 0.52, 0.45, 0.82), ("door", 0.5, 0.6, 0.0, 0.94), ("panes", 0.83, 0.52, 0.45, 0.82)])
    K.wall(g, (X1, Z0), (X1, Z1), B, TOP, openings=[("window", 0.32, 0.44, 0.42, 0.88), ("window", 0.74, 0.44, 0.42, 0.88)])
    K.wall(g, (X1, Z1), (X0, Z1), B, TOP, openings=[("window", 0.3, 0.44, 0.45, 0.88), ("window", 0.7, 0.44, 0.45, 0.88)])
    K.wall(g, (X0, Z1), (X0, Z0), B, TOP, openings=[("window", 0.55, 0.44, 0.42, 0.88)], braces=True)

# main roof: hip-and-gable over the hall, a stacked-tile ornament on the ridge
K.roof(g, X0, Z0, X1, Z1, TOP, RIDGE, kind="xieshan", overhang=0.24, sag=0.11, lift=0.08, ridge_ends=0.1, tile=0.3,
       course=0.34, hip_inset=0.45)
K.lathe(g, [(0.0, 0.0), (0.11, 0.0), (0.12, 0.07), (0.07, 0.14), (0.1, 0.2), (0.0, 0.24)],
        (1.6, RIDGE + 0.1, (Z0 + Z1) / 2), 6, TILE, uv_region=(0.0, TILE_COURSES[1][0], 0.25, TILE_COURSES[1][1]))
# veranda: posts, beam, lean-to, floor
for x in (1.0, 2.0, 2.8):
    K.pole(g, (x, B, VZ), (x, 1.24, VZ), r=0.055, material=TIMBER, sides=6, bend=0.01, taper=0.92)
K.beam(g, (0.1, 1.24, VZ), (2.9, 1.24, VZ), w=0.09, sag=0.02, segs=2)
K.roof(g, 0.12, VZ, 2.88, Z0 - 0.02, 1.25, TOP - 0.02, kind="lean", overhang=0.14, sag=0.03, lift=0.03, ridge=False)
K.boards(g, (0.14, B + 0.005, VZ - 0.06), (1, 0, 0), (0, 0, 1), 2.72, Z0 - VZ + 0.04, 4, TIMBER, thick=0.02)

# the bell tower: four timber legs at the front-left corner, braced, a bell frame, one small tiled roof
TX0, TX1, TZ0, TZ1 = 0.08, 0.78, 0.04, 0.74
TB = 3.35                     # roof eave of the tower
with g.tagged("frame"):
    for x in (TX0, TX1):
        for z in (TZ0, TZ1):
            K.beam(g, (x, 0.0, z), (x + (0.03 if x < 0.5 else -0.03), TB, z + (0.03 if z < 0.4 else -0.03)), w=0.1,
                   caps=False)
    for y in (1.9, TB - 0.05):
        for (a, b) in (((TX0, TZ0), (TX1, TZ0)), ((TX1, TZ0), (TX1, TZ1)), ((TX1, TZ1), (TX0, TZ1)), ((TX0, TZ1), (TX0, TZ0))):
            K.beam(g, (a[0], y, a[1]), (b[0], y, b[1]), w=0.075, caps=False)
    for (a, b) in (((TX0, TZ0), (TX1, TZ0)), ((TX0, TZ1), (TX1, TZ1))):
        K.beam(g, (a[0], 1.9, a[1]), (b[0], 2.6, b[1]), w=0.05, caps=False)
# a railing round the bell floor and the floor itself
K.box(g, (TX0, 2.33, TZ0), (TX1, 2.38, TZ1), TIMBER, WOOD_BLOCK, skip=(3,))
for (a, b) in (((TX0, TZ0), (TX1, TZ0)), ((TX1, TZ0), (TX1, TZ1)), ((TX0, TZ1), (TX0, TZ0))):
    K.pole(g, (a[0], 2.62, a[1]), (b[0], 2.62, b[1]), r=0.022, material=BAMBOO_GOLD, sides=4, bend=0.0, caps=False)
K.roof(g, TX0, TZ0, TX1, TZ1, TB, TB + 0.5, kind="pyramid", overhang=0.1, sag=0.05, lift=0.06, tile=0.24, course=0.26)
# the bronze bell (plaster sheet painted bronze), its yoke and the rope down to the veranda
BX, BZ = (TX0 + TX1) / 2, (TZ0 + TZ1) / 2
K.beam(g, (TX0, TB - 0.12, BZ), (TX1, TB - 0.12, BZ), w=0.07)
bell = [(0.25, 0.0), (0.26, 0.04), (0.21, 0.12), (0.18, 0.3), (0.13, 0.41), (0.0, 0.45)]
n0 = len(g.parts)
K.lathe(g, bell, (BX, TB - 0.85, BZ), 10, PLASTER, uv_region=(0.05, 0.05, 0.95, 0.95), cap_top=False)
K.lathe(g, [(0.22, 0.0), (0.0, 0.02)], (BX, TB - 0.845, BZ), 10, PLASTER, uv_region=(0.05, 0.05, 0.95, 0.95),
        cap_top=False)
for p in g.parts[n0:]:
    p.C = np.tile([0.78, 0.52, 0.24, 1.0], (len(p.P), 1))    # bronze: lime-white sheet painted by vertex colour
K.beam(g, (BX, TB - 0.4, BZ), (BX, TB - 0.12, BZ), w=0.04, material=IRON, caps=False)
K.beam(g, (BX + 0.12, TB - 0.75, BZ), (BX + 0.12, 1.2, BZ - 0.05), w=0.014, material=DETAILS, caps=False)
K.lathe(g, [(0.0, 0.0), (0.03, 0.0), (0.0, 0.05)], (BX + 0.12, 1.15, BZ - 0.05), 5, DETAILS, uv_region=DET_RED)

# signal mast at the back right corner: three lashed bamboo poles carrying the district fire in an iron basket
CX, CZ, CY = 2.66, 2.88, 3.45
for k, (dx, dz) in enumerate(((-0.07, 0.0), (0.05, -0.05), (0.04, 0.06))):
    K.pole(g, (CX + dx * 1.6, B, CZ + dz * 1.6), (CX + dx * 0.6, CY, CZ + dz * 0.6), r=0.045,
           material=BAMBOO_GOLD if k else BAMBOO_GREEN, sides=6, bend=0.008)
for y in (1.0, 2.1, 3.1):
    K.lashing(g, (CX, y, CZ), (0, 1, 0), r=0.1)
K.lathe(g, [(0.0, 0.0), (0.07, 0.0), (0.18, 0.13), (0.2, 0.17)], (CX, CY, CZ), 7, IRON, cap_top=False)
for a_ in range(3):
    K.beam(g, (CX, CY - 0.2, CZ), (CX + 0.16 * np.cos(a_ * 2.1), CY + 0.13, CZ + 0.16 * np.sin(a_ * 2.1)), w=0.025,
           material=IRON, caps=False)
# banners on bamboo poles either side of the steps
for x in (0.92, 2.08):
    K.pole(g, (x, B, 0.02), (x, 1.7, 0.02), r=0.035, material=BAMBOO_GOLD, sides=5, bend=0.01)
    K.beam(g, (x - 0.2, 1.6, 0.02), (x + 0.2, 1.6, 0.02), w=0.025, caps=True, material=BAMBOO_GOLD)
    K.cloth(g, [(x - 0.17, 0.92, -0.01), (x + 0.17, 0.92, -0.01), (x + 0.17, 1.59, -0.01), (x - 0.17, 1.59, -0.01)],
            DETAILS, DET_BANNER, sag=0.0, nu=2, nv=3, wave=0.015)
# lanterns at the veranda, chillies by the door
for x in (1.0, 2.8):
    K.lantern(g, (x, 1.2, VZ - 0.04), r=0.08, h=0.18)
K.chilli_string(g, (1.25, 1.2, VZ + 0.05), length=0.4)
# goods by the walls: jars, baskets, a stack of poles
K.jar(g, (2.92, B, 1.25), h=0.3, r=0.1)
K.jar(g, (2.93, B, 1.52), h=0.24, r=0.08, material=TIMBER)
K.basket(g, (0.1, B, 1.45), h=0.14, r=0.1)
for k in range(4):
    K.pole(g, (0.06 + 0.06 * (k % 2), B + 0.035 + 0.06 * (k // 2), 1.85),
           (0.08 + 0.06 * (k % 2), B + 0.035 + 0.06 * (k // 2), 2.7), r=0.03,
           material=BAMBOO_GREEN if k % 3 else BAMBOO_GOLD, sides=5, bend=0.0)

m.entrance(1, -1, 0)
m.slot("Entrance", (1.5, B, VZ + 0.2), yaw=180)
m.attach("Fire", (CX, CY + 0.06, CZ), "district fire burns in the iron basket on the signal mast")
m.extra["access"] = {"X": 1.5, "Y": B, "Z": 1.0}
m.extra["connectionAnchor"] = {"X": CX, "Y": CY + 0.2, "Z": CZ}
m.extra["bell"] = {"X": BX, "Y": TB - 0.6, "Z": BZ, "note": "the afternoon bell; a sound or swing can hang here"}
m.collider((1.5, 0.9, 1.88), (2.9, 1.4, 2.0))
m.collider((1.5, 2.1, 1.88), (2.6, 1.0, 1.8))
m.collider((0.43, 1.8, 0.39), (0.75, 3.6, 0.75))
m.collider((CX, 1.8, CZ), (0.3, 3.3, 0.3))
m.notes += ["Blocks as the vanilla District Center (3x3x5); the bell tower rises to about 3.9, the mast to 3.6.",
            "The Fire attachment moves to the signal mast's basket; ConnectionAnchorPoint should move to connectionAnchor."]
m.build()
