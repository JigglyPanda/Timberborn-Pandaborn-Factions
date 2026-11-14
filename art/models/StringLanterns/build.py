"""String Lanterns (decoration): a sagging rope of small red lanterns between two leaning bamboo poles. Lit at night by
the vanilla Lantern's night-light controller.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("StringLanterns", size=(1, 1, 2), seed=151, stand_in="Lantern.Folktails")
g = m.geo
for (x, lean) in ((0.06, -0.04), (0.94, 0.04)):
    K.pole(g, (x, 0.0, 0.5), (x + lean, 1.6, 0.5), r=0.025, material=BAMBOO_GREEN, sides=5, bend=0.015)
K.lantern_string(g, (0.04, 1.52, 0.5), (0.96, 1.52, 0.5), n=4, sag=0.22)
m.collider((0.5, 0.75, 0.5), (0.5, 1.5, 0.5))
m.notes += ["Blocks as the vanilla Lantern (1x1x2); NightTimeLightControllerSpec lights the paper (WindowsAtlas glow "
            "region) at night with nobody needed."]
m.build()
