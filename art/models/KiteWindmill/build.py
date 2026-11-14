"""Kite Windmill (small): wind power. 3x3 with the vanilla Wind Turbine's blocks, shaft output and wind specs.

The traditional Chinese sail windmill turns about a vertical axis: eight bamboo masts in a ring, each carrying a
batten sail of hemp cloth (a "kite"), on arms from a thick central post, over a stone-edged earth platform. The
rotor and tower are separate nodes, turned by the vanilla WindRotationAnimator by transform name
('#KiteRotor' about y; '#KiteTower' yaws toward the wind), so the blueprint's WindRotationAnimatorSpec must name them.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("KiteWindmill", size=(3, 3, 4), seed=97, stand_in="WindTurbine.Folktails")
g = m.geo
C = np.array([1.5, 0.0, 1.5])
K.plinth(g, 0.12, 0.12, 2.88, 2.88, h=0.12)
# the gear pit at the foot of the post (power goes down the shaft at the centre cell)
K.lathe(g, [(0.0, 0.12), (0.34, 0.12), (0.36, 0.3), (0.3, 0.32), (0.0, 0.32)], (1.5, 0.0, 1.5), 8, TIMBER,
        strips=[WOOD_BLOCK])
with g.node("#KiteTower"):
    K.tube(g, [C + [0, 0.3, 0], C + [0, 3.45, 0]], [0.09, 0.075], TIMBER, sides=8)
    for y in (0.5, 3.3):
        K.lathe(g, [(0.12, -0.04), (0.13, 0.0), (0.12, 0.04)], C + [0, y, 0], 8, BANDED, cap_top=False,
                uv_region=(0.03, 0.05, 0.08, 0.95))
    K.lathe(g, [(0.0, 0.0), (0.1, 0.0), (0.02, 0.18), (0.0, 0.2)], C + [0, 3.45, 0], 6, TILE,
            uv_region=(0.0, TILE_COURSES[1][0], 0.25, TILE_COURSES[1][1]))
with g.node("#KiteRotor"):
    R = 1.12
    for k in range(8):
        a = 2 * math.pi * k / 8
        d = np.array([math.cos(a), 0, math.sin(a)])
        t = np.array([-math.sin(a), 0, math.cos(a)])
        base = C + d * R
        for y in (0.62, 3.05):
            K.pole(g, C + [0, y, 0] + d * 0.09, base + [0, y, 0], r=0.024, material=BAMBOO_GOLD, sides=4, bend=0.0,
                   caps=False)
        K.pole(g, base + [0, 0.5, 0], base + [0, 3.2, 0], r=0.03, material=BAMBOO_GOLD, sides=5, bend=0.008)
        # the sail: hemp cloth hanging from the mast, cut by bamboo battens, slightly twisted
        w = 0.55
        sail = [base + [0, 0.8, 0] - t * 0.02, base + [0, 0.8, 0] - t * w, base + [0, 3.0, 0] - t * (w * 0.8),
                base + [0, 3.0, 0] - t * 0.02]
        K.cloth(g, sail, DETAILS, (0.53, 0.55, 0.72, 0.95) if k % 2 else (0.03, 0.54, 0.09, 0.98), sag=0.0, nu=1,
                nv=3, wave=0.03)
        for j in range(4):
            y = 0.85 + 0.7 * j
            K.pole(g, base + [0, y, 0] - t * 0.01, base + [0, y, 0] - t * (w * (1 - 0.06 * j) + 0.03), r=0.012,
                   material=BAMBOO_GREEN, sides=3, bend=0.0, caps=False)
    K.lathe(g, [(0.0, -0.06), (0.16, -0.06), (0.16, 0.06), (0.0, 0.06)], C + [0, 0.62, 0], 8, TIMBER)
    K.lathe(g, [(0.0, -0.06), (0.15, -0.06), (0.15, 0.06), (0.0, 0.06)], C + [0, 3.05, 0], 8, TIMBER)
m.animate("#KiteTower", C, (0, 1, 0), kind="static", driver="WindRotationAnimatorSpec.Tower (yaws to the wind)")
m.animate("#KiteRotor", C + [0, 1.0, 0], (0, 1, 0), kind="static", parent="#KiteTower",
          driver="WindRotationAnimatorSpec.WindRotators (turns about y)")
m.extra["windRotationAnimator"] = {
    "WindRotators": [{"TransformName": "#KiteRotor", "RotationAxis": {"X": 0.0, "Y": 1.0, "Z": 0.0},
                      "RotationSpeed": 70.0}],
    "Tower": {"TransformName": "#KiteTower", "RotationAxis": {"X": 0.0, "Y": 1.0, "Z": 0.0}, "RotationSpeed": 75.0}}
m.stage_height = 1.8
m.collider((1.5, 1.8, 1.5), (2.6, 3.0, 2.6))
m.notes += ["Blocks, transput and wind specs as the vanilla Wind Turbine (3x3x4).",
            "A vertical-axis sail windmill: it turns the same whichever way the wind blows."]
m.build()
