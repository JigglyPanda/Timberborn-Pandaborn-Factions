"""Ink Studio: a quiet hour of ink painting, weekly. 1x1 on the vanilla Contemplation Spot (one visitor; its 'Fire'
attachment becomes the glow of a little brazier warming the inkstone water).

A low painting table on a woven mat under a small tile-roofed bamboo pavilion: paper weighted with river stones, a
brush rest, an inkstone and a water jar; a scroll of ink-painted bamboo hanging on the back screen (a picture, no
writing); a potted bamboo.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("InkStudio", size=(1, 1, 1), seed=211, stand_in="ContemplationSpot.Folktails")
g = m.geo
K.panel(g, [(0.1, 0.01, 0.1), (0.9, 0.01, 0.1), (0.9, 0.01, 0.9), (0.1, 0.01, 0.9)], WEAVE_GOLD)
for (x, z) in ((0.08, 0.08), (0.92, 0.08), (0.92, 0.92), (0.08, 0.92)):
    K.pole(g, (x, 0.0, z), (x, 0.92, z), r=0.03, material=BAMBOO_GOLD, sides=5, bend=0.005)
K.roof(g, 0.08, 0.08, 0.92, 0.92, 0.92, 1.22, kind="pyramid", overhang=0.12, sag=0.03, lift=0.05, tile=0.22, course=0.24)
K.screen(g, (0.08, 0.9), (0.92, 0.9), 0.02, 0.78, material=WEAVE)
# the hanging painting: indigo-and-pale banner art (the ink bamboo in a disc), framed by two bamboo rods
K.cloth(g, [(0.32, 0.3, 0.87), (0.68, 0.3, 0.87), (0.68, 0.74, 0.87), (0.32, 0.74, 0.87)], DETAILS,
        (0.14, 0.62, 0.36, 0.9), sag=0.0, nu=1, nv=2, wave=0.0)
for y in (0.29, 0.75):
    K.pole(g, (0.29, y, 0.86), (0.71, y, 0.86), r=0.01, material=BAMBOO_GOLD, sides=3, bend=0.0)
# low table with paper, inkstone, brushes, water jar
K.box(g, (0.25, 0.16, 0.42), (0.75, 0.2, 0.7), TIMBER, WOOD_BLOCK, skip=(3,))
for x in (0.28, 0.72):
    K.beam(g, (x, 0.0, 0.56), (x, 0.16, 0.56), w=0.04, caps=False)
K.panel(g, [(0.3, 0.205, 0.45), (0.6, 0.205, 0.45), (0.6, 0.205, 0.66), (0.3, 0.205, 0.66)], PAPER, (0.36, 0.05, 0.6, 0.6))
K.box(g, (0.62, 0.2, 0.5), (0.72, 0.23, 0.62), PLASTER, (0.1, 0.1, 0.9, 0.9))
g.parts[-1].C = np.tile([0.18, 0.18, 0.2, 1.0], (len(g.parts[-1].P), 1))
for k in range(3):
    K.beam(g, (0.36 + 0.06 * k, 0.215, 0.47), (0.4 + 0.06 * k, 0.215, 0.64), w=0.012, material=BAMBOO_GOLD, caps=False)
K.lathe(g, [(0.0, 0.0), (0.03, 0.0), (0.035, 0.05), (0.02, 0.07)], (0.68, 0.2, 0.67), 6, EARTH)
K.lathe(g, [(0.0, 0.0), (0.06, 0.0), (0.07, 0.07)], (0.84, 0.0, 0.2), 6, EARTH)
for k in range(3):
    K.pole(g, (0.84, 0.07, 0.2), (0.84 + 0.04 * (k - 1), 0.5 + 0.05 * k, 0.2), r=0.01, material=BAMBOO_GREEN, sides=3,
           bend=0.02, caps=False)
m.slot("Spot", (0.5, 0.0, 0.3), yaw=0.0)
m.entrance(0, -1, 0)
m.extra["access"] = {"X": 0.5, "Y": 0.0, "Z": 0.2}
m.attach("Fire", (0.84, 0.05, 0.75), "the vanilla small fire, as a brazier warming the ink water")
m.collider((0.5, 0.5, 0.5), (0.95, 1.0, 0.95))
m.build()
