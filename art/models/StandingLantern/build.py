"""Standing Lantern (decoration): a red paper lantern hanging from the arm of a dark timber post on a river-stone
foot, a little clay hat over it against the rain. Lit at night by the vanilla Lantern's night-light controller.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("StandingLantern", size=(1, 1, 2), seed=139, stand_in="Lantern.Folktails")
g = m.geo
K.stones(g, 0.28, 0.28, 0.72, 0.72, y=-0.01, size=0.2, h=0.1, ring=False)
K.beam(g, (0.45, 0.06, 0.5), (0.45, 1.5, 0.5), w=0.08, caps="end")
K.beam(g, (0.4, 1.38, 0.5), (0.86, 1.36, 0.5), w=0.05)
K.beam(g, (0.45, 1.05, 0.5), (0.7, 1.36, 0.5), w=0.035)
K.lathe(g, [(0.0, 0.0), (0.16, 0.0), (0.06, 0.08), (0.0, 0.1)], (0.77, 1.38, 0.5), 6, TILE,
        uv_region=(0.0, TILE_COURSES[1][0], 0.25, TILE_COURSES[1][1]))
K.lantern(g, (0.77, 1.36, 0.5), r=0.11, h=0.25)
m.collider((0.5, 0.75, 0.5), (0.5, 1.5, 0.5))
m.notes += ["Blocks as the vanilla Lantern (1x1x2); NightTimeLightControllerSpec lights the paper (WindowsAtlas glow "
            "region) at night with nobody needed."]
m.build()
