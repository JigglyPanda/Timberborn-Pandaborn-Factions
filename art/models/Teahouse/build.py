"""Teahouse: the daily cup of tea and company. 3x3, on the vanilla Campfire's attraction blueprint (five seats).

An open hall on a stone platform under a hipped grey-tile roof, and in front of it a terrace under an indigo awning
with a string of red lanterns: dark timber posts, a woven screen with a lattice window along the back, two low
tables with teapots and cups, cushions to sit on, a clay tea stove with a kettle, a tea shrub in a pot; out
front in the open (seen from the game camera) a clay brazier with a big iron kettle and a tea stand with a big
teapot and a ring of cups on a round tray.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, block  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("Teahouse", size=(3, 3, 2), seed=73, stand_in="Campfire.Folktails")
g = m.geo
B = 0.14
TOP = 1.3
RIDGE = 2.05
K.plinth(g, 0.06, 0.08, 2.94, 2.92, h=B)
K.boards(g, (0.15, B + 0.004, 0.2), (1, 0, 0), (0, 0, 1), 2.7, 2.6, 6, TIMBER, thick=0.02)
# posts: corners and mid-sides, all round timber with a little lean
ZF = 1.05      # front of the roofed hall; the terrace is in front of it
posts = [(0.22, ZF), (1.5, ZF), (2.78, ZF), (0.22, 2.75), (1.5, 2.78), (2.78, 2.75), (0.2, 1.9), (2.8, 1.9)]
with g.tagged("frame"):
    for x, z in posts:
        K.pole(g, (x, B, z), (x + g.jitter(0.02), TOP - 0.05, z + g.jitter(0.02)), r=0.055, material=TIMBER, sides=6,
               bend=0.008, taper=0.92)
    for (ax, az, bx, bz) in ((0.15, ZF, 2.85, ZF), (0.15, 2.75, 2.85, 2.75)):
        K.beam(g, (ax, TOP - 0.06, az), (bx, TOP - 0.06, bz), w=0.09, sag=0.015, segs=2)
    for x in (0.2, 2.8):
        K.beam(g, (x, TOP - 0.06, ZF - 0.05), (x, TOP - 0.06, 2.8), w=0.08)
K.roof(g, 0.2, ZF, 2.8, 2.75, TOP, RIDGE, kind="hip", overhang=0.26, sag=0.09, lift=0.1, ridge_ends=0.08,
       tile=0.3, course=0.32)
# terrace awning: indigo cloth on bamboo poles, a string of lanterns along its edge
for x in (0.25, 2.75):
    K.pole(g, (x, B, 0.52), (x, 1.12, 0.5), r=0.035, material=BAMBOO_GOLD, sides=5, bend=0.015)
K.cloth(g, [(0.2, 1.08, 0.48), (2.8, 1.08, 0.48), (2.8, TOP - 0.1, ZF - 0.02), (0.2, TOP - 0.1, ZF - 0.02)], DETAILS,
        (0.03, 0.54, 0.09, 0.98), sag=0.06, nu=5, nv=2, wave=0.012)
K.lantern_string(g, (0.25, 1.06, 0.46), (2.75, 1.06, 0.46), n=5, sag=0.1)
# back: woven screen with a lattice window in the middle; low rail on the sides
K.panel(g, [(2.75, B, 2.73), (0.25, B, 2.73), (0.25, TOP - 0.12, 2.73), (2.75, TOP - 0.12, 2.73)], WEAVE, both=True)
K.window(g, (1.5, 0.72, 2.71), (0, 0, -1), 0.6, 0.42)
for x in (0.2, 2.8):
    K.beam(g, (x, 0.42, 0.3), (x, 0.42, 2.7), w=0.045)
# two low tables with tea things, cushions around them
seats = []
for tx, tz in ((0.95, 0.62), (2.05, 1.75)):
    K.box(g, (tx - 0.3, 0.3, tz - 0.22), (tx + 0.3, 0.36, tz + 0.22), TIMBER, WOOD_BLOCK, skip=(3,))
    for dx in (-0.24, 0.24):
        for dz in (-0.16, 0.16):
            K.beam(g, (tx + dx, B, tz + dz), (tx + dx, 0.3, tz + dz), w=0.04, caps=False)
    K.lathe(g, [(0.0, 0.0), (0.05, 0.0), (0.07, 0.04), (0.05, 0.09), (0.0, 0.1)], (tx - 0.08, 0.36, tz), 6, EARTH)
    for k in range(3):
        K.lathe(g, [(0.0, 0.0), (0.022, 0.0), (0.026, 0.03)], (tx + 0.1 + 0.06 * k, 0.36, tz - 0.08 + 0.08 * (k % 2)),
                5, PLASTER, cap_top=False)
    for (dx, dz, yaw) in ((-0.5, 0.0, 90), (0.5, 0.0, -90), (0.0, 0.42, 180)):
        cx, cz = tx + dx, tz + dz
        K.box(g, (cx - 0.13, B, cz - 0.13), (cx + 0.13, B + 0.07, cz + 0.13), DETAILS, DET_CLOTH, skip=(3,))
        seats.append(((cx, B + 0.07, cz), yaw))
# tea stove with a kettle at the back right, its little chimney
K.box(g, (2.25, B, 2.25), (2.65, 0.52, 2.62), EARTH, (0.05, 0.05, 0.95, 0.95), skip=(3,))
K.box(g, (2.27, 0.52, 2.27), (2.63, 0.55, 2.6), TIMBER, WOOD_BLOCK, skip=(3,))
K.lathe(g, [(0.0, 0.0), (0.08, 0.0), (0.1, 0.07), (0.07, 0.13), (0.03, 0.15), (0.0, 0.16)], (2.45, 0.55, 2.42), 7, IRON)
K.tube(g, [(2.56, 0.52, 2.55), (2.56, 1.5, 2.6)], [0.05, 0.045], EARTH, sides=6)
# out front, in the open where the game camera sees them (the teahouse serves tea): a clay brazier with a big iron
# kettle on it, and a low tea stand with a big teapot and a ring of cups on a round tray
K.lathe(g, [(0.0, 0.0), (0.16, 0.0), (0.19, 0.2), (0.15, 0.3), (0.12, 0.31)], (0.45, B, 0.27), 8, EARTH, cap_top=True)
K.lathe(g, [(0.0, 0.0), (0.14, 0.02), (0.16, 0.1), (0.12, 0.18), (0.05, 0.21), (0.0, 0.22)], (0.45, B + 0.31, 0.27), 8, IRON)
K.tube(g, [(0.57, B + 0.42, 0.27), (0.7, B + 0.5, 0.27)], [0.025, 0.015], IRON, sides=4)
K.beam(g, (0.33, B + 0.55, 0.27), (0.57, B + 0.55, 0.27), w=0.02, material=BAMBOO_GOLD, caps=False)
K.box(g, (1.75, 0.26, 0.1), (2.3, 0.31, 0.45), TIMBER, WOOD_BLOCK, skip=(3,))
for x in (1.8, 2.25):
    for z in (0.14, 0.41):
        K.beam(g, (x, B, z), (x, 0.26, z), w=0.035, caps=False)
K.tray(g, (2.02, 0.31, 0.28), r=0.17, leaf=None, sides=9)
K.lathe(g, [(0.0, 0.0), (0.08, 0.0), (0.1, 0.06), (0.07, 0.12), (0.03, 0.14), (0.0, 0.15)], (2.02, 0.33, 0.28), 7, EARTH)
g.parts[-1].C = np.tile([0.45, 0.24, 0.14, 1.0], (len(g.parts[-1].P), 1))
K.tube(g, [(2.1, 0.39, 0.28), (2.17, 0.45, 0.28)], [0.016, 0.01], EARTH, sides=4)
for k in range(6):
    a = 2 * np.pi * k / 6
    K.lathe(g, [(0.0, 0.0), (0.025, 0.0), (0.03, 0.035)], (2.02 + 0.13 * np.cos(a), 0.33, 0.28 + 0.13 * np.sin(a)), 5,
            PLASTER, cap_top=False)
# lanterns at the front eave corners, a tea shrub in a pot by the steps
K.lathe(g, [(0.0, 0.0), (0.12, 0.0), (0.15, 0.18), (0.16, 0.2)], (2.65, B, 0.3), 7, EARTH)
for k in range(3):
    a = k * 2.1
    K.lathe(g, [(0.0, 0.0), (0.11, 0.05), (0.07, 0.16), (0.0, 0.2)], (2.65 + 0.06 * np.cos(a), B + 0.22, 0.3 + 0.06 * np.sin(a)),
            5, MOSS)
# five seats for the attraction (Campfire.Folktails has CapacityFinished 5)
for i, (p, yaw) in enumerate(seats[:5]):
    m.slot(f"Seat{i + 1}", p, yaw)
m.blocks = [block("Ground", "Floor, Bottom, Corners, Path, Middle", "None") for _ in range(9)] + \
           [block("Any", "Top, Corners", "None") for _ in range(9)]
m.entrance(1, -1, 0)
m.extra["access"] = {"X": 1.5, "Y": B, "Z": 0.7}
m.extra["removeSpecs"] = ["AttractionFireSpec", "FireSpec", "IlluminatorLightObjectsSpec", "TemplateAttachmentsSpec"]
m.extra["addSpecs"] = {"EnterableIlluminatorSpec": {}}
m.collider((1.5, 0.07, 1.5), (3.0, 0.14, 3.0))
m.collider((1.5, 1.6, 1.5), (3.0, 0.6, 3.0))
m.notes += ["Campfire's fire specs dropped (no fire node); windows and lanterns lit by EnterableIlluminatorSpec.",
            "Upper blocks are the roof only (Top, Corners), the floor blocks walkable as the Campfire's."]
m.build()
