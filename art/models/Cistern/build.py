"""Cistern (small): a great brown-glazed earthen water jar on a stone ring, hooped with cane, its woven lid tipped
aside and a bamboo ladle on the rim. 1x1x2 as the vanilla Small Tank; the stored water's surface (the vanilla
StockpilePlaneVisualizer, rising from y 0.55 to 1.42) shows inside the open mouth.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
from building import Model  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("Cistern", size=(1, 1, 2), seed=71, stand_in="SmallTank.Folktails")
g = m.geo
C = (0.5, 0.0, 0.5)
K.stones(g, 0.06, 0.06, 0.94, 0.94, y=-0.01, size=0.2, h=0.13)
K.box(g, (0.1, 0.0, 0.1), (0.9, 0.1, 0.9), EARTH, (0.05, 0.05, 0.95, 0.95), skip=(3,))
# the jar: outside profile, then the inside down to the water's lowest level
outside = [(0.27, 0.1), (0.4, 0.3), (0.46, 0.7), (0.45, 1.05), (0.42, 1.36), (0.44, 1.46), (0.45, 1.5)]
inside = [(0.41, 1.5), (0.39, 1.44), (0.42, 1.2), (0.42, 0.8), (0.3, 0.56), (0.0, 0.54)]
K.lathe(g, outside, C, 10, PLASTER, uv_region=(0.05, 0.05, 0.95, 0.95), cap_top=False)
GLAZE = np.array([0.34, 0.22, 0.14, 1.0])     # dark brown glaze: white lime plaster painted by vertex colour
jar = g.parts[-1]
jar.C = np.tile(GLAZE, (len(jar.P), 1)) * np.clip(0.75 + 0.35 * (jar.P[:, 1:2] / 1.5), 0, 1.2)
jar.C[:, 3] = 1.0
K.lathe(g, inside, C, 10, IRON, uv_region=(0.1, 0.1, 0.4, 0.4), cap_top=False)
K.lathe(g, [(0.45, 1.5), (0.41, 1.5)], C, 10, PLASTER, uv_region=(0.05, 0.05, 0.95, 0.95), cap_top=False)
g.parts[-1].C = np.tile([0.5, 0.36, 0.25, 1.0], (len(g.parts[-1].P), 1))
# cane hoops
for y, r in ((0.45, 0.43), (1.1, 0.455)):
    K.lathe(g, [(r, y - 0.03), (r + 0.012, y), (r, y + 0.03)], C, 10, BAMBOO_GOLD, cap_top=False)
# woven lid tipped against the jar, ladle on the rim
K.lathe(g, [(0.0, 0.0), (0.4, 0.0), (0.42, 0.04), (0.0, 0.06)], (0.0, 0.0, 0.0), 8, WEAVE_GOLD, cap_top=False)
lid = g.parts[-1]
R = rot_axis((1, 0, 0), -1.25)
lid.P = lid.P @ R.T + np.array([0.5, 0.42, 0.02])
lid.N = lid.N @ R.T
K.pole(g, (0.2, 1.52, 0.48), (0.78, 1.58, 0.6), r=0.016, material=BAMBOO_GOLD, sides=4, bend=0.0)
K.lathe(g, [(0.0, 0.0), (0.05, 0.0), (0.055, 0.08)], (0.18, 1.45, 0.47), 6, BAMBOO_GREEN, cap_top=False)
m.extra["access"] = {"X": 0.5, "Y": 0.0, "Z": 0.1}
m.extra["liquidPlane"] = "vanilla SmallTank StockpilePlaneVisualizer: y 0.546 to 1.42; jar mouth radius 0.39"
m.collider((0.5, 0.75, 0.5), (0.9, 1.5, 0.9))
m.notes += ["Blocks as the vanilla Small Tank (1x1x2)."]
m.build()
