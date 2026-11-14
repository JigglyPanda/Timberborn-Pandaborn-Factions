"""Large Kite Windmill: more wind power. 3x3x5 with the vanilla Large Wind Turbine's blocks, shaft output and wind specs.
The small Kite Windmill grown up: ten taller sails, a higher post with a tiled cap and a stone two-step base with a
gear house roof at the post's foot, so the two read apart at game zoom (the large one's sails reach twice as high).

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

m = Model("LargeKiteWindmill", size=(3, 3, 5), seed=331, stand_in="LargeWindTurbine.Folktails")
g = m.geo
C = np.array([1.5, 0.0, 1.5])
K.plinth(g, 0.06, 0.06, 2.94, 2.94, h=0.12)
K.plinth(g, 0.75, 0.75, 2.25, 2.25, h=0.22)
# the gear house at the post's foot: a low round wall with a little tiled roof the rotor's lower arms turn above
K.lathe(g, [(0.42, 0.22), (0.42, 0.55), (0.0, 0.55)], (1.5, 0.0, 1.5), 10, PLASTER_LATH, cap_top=False)
K.round_roof(g, (1.5, 0.0, 1.5), 0.55, 0.55, 0.78, sides=8, sag=0.03, thick=0.05)
# the gear pit at the foot of the post (power goes down the shaft at the centre cell)
K.lathe(g, [(0.0, 0.12), (0.34, 0.12), (0.36, 0.3), (0.3, 0.32), (0.0, 0.32)], (1.5, 0.0, 1.5), 8, TIMBER,
        strips=[WOOD_BLOCK])
with g.node("#KiteTower"):
    K.tube(g, [C + [0, 0.3, 0], C + [0, 4.55, 0]], [0.12, 0.09], TIMBER, sides=8)
    for y in (0.95, 4.4):
        K.lathe(g, [(0.12, -0.04), (0.13, 0.0), (0.12, 0.04)], C + [0, y, 0], 8, BANDED, cap_top=False,
                uv_region=(0.03, 0.05, 0.08, 0.95))
    K.lathe(g, [(0.0, 0.0), (0.1, 0.0), (0.02, 0.18), (0.0, 0.2)], C + [0, 4.55, 0], 6, TILE,
            uv_region=(0.0, TILE_COURSES[1][0], 0.25, TILE_COURSES[1][1]))
with g.node("#KiteRotor"):
    R = 1.3
    for k in range(10):
        a = 2 * math.pi * k / 10
        d = np.array([math.cos(a), 0, math.sin(a)])
        t = np.array([-math.sin(a), 0, math.cos(a)])
        base = C + d * R
        for y in (0.95, 4.15):
            K.pole(g, C + [0, y, 0] + d * 0.09, base + [0, y, 0], r=0.024, material=BAMBOO_GOLD, sides=4, bend=0.0,
                   caps=False)
        K.pole(g, base + [0, 0.85, 0], base + [0, 4.3, 0], r=0.034, material=BAMBOO_GOLD, sides=5, bend=0.008)
        # the sail: hemp cloth hanging from the mast, cut by bamboo battens, slightly twisted
        w = 0.6
        sail = [base + [0, 1.1, 0] - t * 0.02, base + [0, 1.1, 0] - t * w, base + [0, 4.1, 0] - t * (w * 0.8),
                base + [0, 4.1, 0] - t * 0.02]
        K.cloth(g, sail, DETAILS, (0.03, 0.54, 0.09, 0.98), sag=0.0, nu=1,   # all indigo: dark from above, unlike the small one
                nv=3, wave=0.03)
        for j in range(5):
            y = 1.15 + 0.72 * j
            K.pole(g, base + [0, y, 0] - t * 0.01, base + [0, y, 0] - t * (w * (1 - 0.06 * j) + 0.03), r=0.012,
                   material=BAMBOO_GREEN, sides=3, bend=0.0, caps=False)
    K.lathe(g, [(0.0, -0.06), (0.16, -0.06), (0.16, 0.06), (0.0, 0.06)], C + [0, 0.95, 0], 8, TIMBER)
    K.lathe(g, [(0.0, -0.06), (0.15, -0.06), (0.15, 0.06), (0.0, 0.06)], C + [0, 4.15, 0], 8, TIMBER)
m.animate("#KiteTower", C, (0, 1, 0), kind="static", driver="WindRotationAnimatorSpec.Tower (yaws to the wind)")
m.animate("#KiteRotor", C + [0, 1.0, 0], (0, 1, 0), kind="static", parent="#KiteTower",
          driver="WindRotationAnimatorSpec.WindRotators (turns about y)")
m.extra["windRotationAnimator"] = {
    "WindRotators": [{"TransformName": "#KiteRotor", "RotationAxis": {"X": 0.0, "Y": 1.0, "Z": 0.0},
                      "RotationSpeed": 55.0}],
    "Tower": {"TransformName": "#KiteTower", "RotationAxis": {"X": 0.0, "Y": 1.0, "Z": 0.0}, "RotationSpeed": 75.0}}
m.stage_height = 2.2
m.collider((1.5, 2.4, 1.5), (2.8, 3.8, 2.8))
m.notes += ["Blocks, transput and wind specs as the vanilla Large Wind Turbine (3x3x5).",
            "A vertical-axis sail windmill: it turns the same whichever way the wind blows."]
m.build()
