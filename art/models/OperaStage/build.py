"""Opera Stage: face-changing opera put on by the Ringtails for whoever is off duty. 5x5 on the vanilla Dance Hall
(twenty audience spots; its 'Light' attachment lights the stage).

An open-air village theatre: a raised timber stage at the back under a hip-and-gable grey-tile roof, red-lacquer
only on the small curtain valance and lanterns; a painted backdrop screen (the ink bamboo banner art, no writing);
two drum stands at the wings; in front a paved yard with benches for the audience; the Ringtail moon plaque on the
stage roof.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, block  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("OperaStage", size=(5, 5, 2), seed=227, stand_in="DanceHall.Folktails")
g = m.geo
# the yard
K.box(g, (0.03, 0.0, 0.03), (4.97, 0.05, 4.97), EARTH, (0.02, 0.02, 0.98, 0.98), skip=(3,))
K.stones(g, 0.05, 0.05, 4.95, 4.95, y=-0.01, size=0.36, h=0.12, skip=0.1)
# the stage: platform, posts, roof
SZ0, SZ1, SH = 3.0, 4.85, 0.6
K.box(g, (0.6, 0.0, SZ0), (4.4, SH, SZ1), EARTH, (0.02, 0.02, 0.98, 0.98), skip=(3,), tags={"base"})
K.stones(g, 0.62, SZ0 + 0.02, 4.38, SZ1 - 0.02, y=-0.01, size=0.32, h=SH * 0.9, skip=0.0, tags={"base"})
K.boards(g, (0.6, SH, SZ0), (0, 0, 1), (1, 0, 0), SZ1 - SZ0, 3.8, 8, TIMBER, thick=0.03)
for x in (0.7, 4.3):
    for z in (SZ0 + 0.08, SZ1 - 0.08):
        K.pole(g, (x, SH, z), (x, 2.2, z), r=0.07, material=TIMBER, sides=6, bend=0.005, taper=0.92, tags={"frame"})
K.beam(g, (0.55, 2.2, SZ0 + 0.08), (4.45, 2.2, SZ0 + 0.08), w=0.1, sag=0.02, segs=2, tags={"frame"})
K.roof(g, 0.7, SZ0 + 0.08, 4.3, SZ1 - 0.08, 2.22, 3.1, kind="xieshan", overhang=0.3, sag=0.1, lift=0.08,
       ridge_ends=0.09, tile=0.3, course=0.34, hip_inset=0.42)
# backdrop screen, valance with red trim, lanterns at the front posts
K.screen(g, (0.75, SZ1 - 0.12), (4.25, SZ1 - 0.12), SH + 0.02, 2.15, material=WEAVE)
K.cloth(g, [(1.6, SH + 0.35, SZ1 - 0.16), (3.4, SH + 0.35, SZ1 - 0.16), (3.4, 1.95, SZ1 - 0.16),
            (1.6, 1.95, SZ1 - 0.16)], DETAILS, DET_BANNER, sag=0.0, nu=3, nv=2, wave=0.01)
K.cloth(g, [(0.7, 1.95, SZ0 + 0.05), (4.3, 1.95, SZ0 + 0.05), (4.3, 2.15, SZ0 + 0.05), (0.7, 2.15, SZ0 + 0.05)],
        DETAILS, DET_RED, sag=0.04, nu=6, nv=1, wave=0.02)
for x in (0.7, 4.3):
    K.lantern(g, (x, 1.9, SZ0 - 0.06), r=0.11, h=0.25)
# drums at the wings
for x in (1.0, 4.0):
    K.lathe(g, [(0.0, 0.0), (0.2, 0.0), (0.24, 0.16), (0.2, 0.32), (0.0, 0.32)], (x, SH, SZ0 + 0.45), 10, DETAILS,
            uv_region=DET_RED)
# the Ringtail moon plaque on the roof's front ridge end
K.moon_window(g, (2.5, 2.75, SZ0 + 0.55), (0, 0.3, -1), r=0.24)
# audience benches in the yard
for row, z in enumerate((0.7, 1.45, 2.2)):
    for (x0, x1) in ((0.5, 2.1), (2.9, 4.5)):
        K.beam(g, (x0, 0.28, z), (x1, 0.28, z), w=0.16, h=0.04)
        for x in (x0 + 0.1, x1 - 0.1):
            K.beam(g, (x, 0.0, z), (x, 0.27, z), w=0.05, caps=False)
spots = []
for z in (0.85, 1.6, 2.35):
    for x in np.linspace(0.65, 1.95, 3).tolist() + np.linspace(3.05, 4.35, 3).tolist():
        spots.append((x, 0.3, z - 0.1))
for x in (1.6, 2.2, 2.8, 3.4):
    spots.append((x, SH + 0.03, SZ0 + 0.8))
for i, p in enumerate(spots[:20]):
    m.slot(f"Spot{i + 1}", p, yaw=180.0 if p[1] < SH else 0.0)
m.blocks = [block("GroundOrStackable", "Floor, Bottom, Corners, Path, Middle", "None") for _ in range(25)] + \
           [block("Any", "Bottom, Top, Corners, Path, Middle", "None") if (i // 5) >= 3 else block("Any", "None", "None")
            for i in range(25)]
m.entrance(2, -1, 0)
m.extra["access"] = {"X": 2.5, "Y": 0.05, "Z": 0.4}
m.attach("Light", (2.5, 2.0, SZ0 + 0.9), "the vanilla dance-hall light, hung under the stage roof")
m.collider((2.5, 0.05, 2.5), (5.0, 0.1, 5.0))
m.collider((2.5, 1.5, 3.9), (3.9, 3.0, 1.9))
m.notes += ["Twenty Spot slots: eighteen on the benches (audience) and four on the stage (players). The vanilla "
            "animation is 'Dancing' for all; a 'Sitting' keyword for the benches would suit better."]
m.build()
