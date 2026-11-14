"""Night Gatherers' Post: mushrooms and wild food gathered by night. 1x1 on the vanilla Gatherer Flag. The moon
mark: a round moon plaque glowing on a bamboo pole with a crescent at its top and a red lantern on an arm; a basket
of bamboo mushrooms and a back-basket at its foot.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("NightForagersPost", size=(1, 1, 2), seed=179, stand_in="GathererFlag.Folktails")
g = m.geo
K.stones(g, 0.25, 0.42, 0.75, 0.82, y=-0.01, size=0.2, h=0.1, ring=False)
K.pole(g, (0.5, 0.0, 0.62), (0.5, 1.75, 0.6), r=0.04, material=BAMBOO_GOLD, sides=6, bend=0.01)
K.moon_window(g, (0.5, 1.2, 0.555), (0, 0, -1), r=0.2)
arc = [(0.5 + 0.13 * math.cos(t), 1.83 + 0.13 * math.sin(t), 0.6) for t in np.linspace(-1.9, 1.9, 7)]
K.tube(g, arc, [0.01, 0.025, 0.032, 0.035, 0.032, 0.025, 0.01], BAMBOO_GOLD, sides=5, caps=False)
K.beam(g, (0.5, 0.86, 0.6), (0.8, 0.86, 0.6), w=0.03)
K.lantern(g, (0.78, 0.84, 0.6), r=0.06, h=0.13)
K.basket(g, (0.3, 0.0, 0.32), h=0.12, r=0.12)
for k in range(5):
    a = k * 1.25
    K.lathe(g, [(0.0, 0.0), (0.012, 0.0), (0.012, 0.05), (0.04, 0.06), (0.0, 0.08)],
            (0.3 + 0.05 * math.cos(a), 0.1, 0.32 + 0.05 * math.sin(a)), 5, PLASTER, cap_top=False)
K.basket(g, (0.74, 0.0, 0.3), h=0.32, r=0.1, material=WEAVE_GOLD)
m.slot("Seat", (0.5, 0.0, 0.3), yaw=180)
m.extra["access"] = {"X": 0.5, "Y": 0.0, "Z": 0.2}
m.collider((0.5, 0.9, 0.6), (0.3, 1.8, 0.3))
m.notes += ["Blocks, entrance and the Seat slot as the vanilla Gatherer Flag. Ringtail mark: the moon plaque."]
m.build()
