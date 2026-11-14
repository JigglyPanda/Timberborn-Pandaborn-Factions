"""Hanging Lantern (decoration): a big round red lantern swinging from a bamboo gallows with a lashed cross-bar and a
tassel, the kind hung at a farmstead gate. Lit at night by the vanilla Lantern's night-light controller.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("HangingLantern", size=(1, 1, 2), seed=149, stand_in="Lantern.Folktails")
g = m.geo
for x in (0.18, 0.82):
    K.pole(g, (x, 0.0, 0.5), (x + g.jitter(0.02), 1.62, 0.5), r=0.035, material=BAMBOO_GOLD, sides=6, bend=0.01)
K.pole(g, (0.1, 1.55, 0.5), (0.9, 1.57, 0.5), r=0.028, material=BAMBOO_GOLD, sides=5, bend=0.0)
for x in (0.18, 0.82):
    K.lashing(g, (x, 1.55, 0.5), (0, 1, 0), r=0.045)
K.lantern(g, (0.5, 1.5, 0.5), r=0.17, h=0.36)
K.beam(g, (0.5, 1.14, 0.5), (0.5, 0.98, 0.5), w=0.02, material=DETAILS, caps=False)
m.collider((0.5, 0.75, 0.5), (0.5, 1.5, 0.5))
m.notes += ["Blocks as the vanilla Lantern (1x1x2); NightTimeLightControllerSpec lights the paper (WindowsAtlas glow "
            "region) at night with nobody needed."]
m.build()
