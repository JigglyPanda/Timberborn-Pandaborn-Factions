"""Dew Collector: a little drinking water each dawn. 1x1x2 on the vanilla Small Tank's storage blueprint.

A wide funnel of fine green bamboo mesh held up on four leaning bamboo poles, drips gathering into a glazed jar
under it; a ladle and a split-bamboo spout. The funnel's open cone is the silhouette: nothing else in the village
looks like it.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("DewCollector", size=(1, 1, 2), seed=101, stand_in="SmallTank.Folktails")
g = m.geo
C = np.array([0.5, 0.0, 0.5])
K.stones(g, 0.08, 0.08, 0.92, 0.92, y=-0.01, size=0.18, h=0.1, skip=0.2)
# jar
outside = [(0.18, 0.06), (0.28, 0.2), (0.31, 0.45), (0.25, 0.68), (0.27, 0.74)]
K.lathe(g, outside, C, 9, PLASTER, cap_top=False)
jar = g.parts[-1]
jar.C = np.tile([0.32, 0.22, 0.15, 1.0], (len(jar.P), 1))
K.lathe(g, [(0.24, 0.74), (0.22, 0.66), (0.0, 0.6)], C, 9, IRON, uv_region=(0.1, 0.1, 0.4, 0.4), cap_top=False)
# four leaning poles and the mesh funnel
for k in range(4):
    a = math.pi / 4 + k * math.pi / 2
    d = np.array([math.cos(a), 0, math.sin(a)])
    K.pole(g, C + d * 0.42, C + d * 0.5 + [0, 1.95, 0], r=0.025, material=BAMBOO_GOLD, sides=5, bend=0.015)
    K.lashing(g, C + d * 0.49 + [0, 1.62, 0], (0, 1, 0), r=0.035)
cone = [(0.06, 1.08), (0.2, 1.3), (0.36, 1.55), (0.5, 1.82), (0.53, 1.86)]
K.lathe(g, cone, C, 10, WEAVE_GREEN, uv_region=(0.05, 0.05, 0.95, 0.95), cap_top=False)
inner = [(r - 0.012, y + 0.004) for r, y in reversed(cone)]
K.lathe(g, inner, C, 10, WEAVE_GREEN, uv_region=(0.05, 0.05, 0.95, 0.95), cap_top=False)
K.lathe(g, [(0.53, 1.84), (0.55, 1.87), (0.53, 1.9)], C, 10, BAMBOO_GOLD, cap_top=False)
# the drip spout from the funnel's tip into the jar, a ladle hanging on a pole
K.tube(g, [C + [0, 1.1, 0], C + [0, 0.8, 0]], [0.035, 0.03], BAMBOO_GREEN, sides=5, caps=False)
K.pole(g, C + [0.3, 0.75, -0.3], C + [0.36, 1.05, -0.36], r=0.012, material=BAMBOO_GOLD, sides=3, bend=0.0)
K.lathe(g, [(0.0, 0.0), (0.04, 0.0), (0.045, 0.05)], C + [0.29, 0.68, -0.29], 6, BAMBOO_GREEN, cap_top=False)
m.extra["access"] = {"X": 0.5, "Y": 0.0, "Z": 0.1}
m.collider((0.5, 0.95, 0.5), (0.9, 1.9, 0.9))
m.notes += ["Stand-in Small Tank for the model check only; the dew mechanic (water prototype) is a workshop."]
m.build()
