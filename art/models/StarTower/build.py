"""Star Tower: the Ringtails' night-sky science. 3x3x5 on the vanilla Observatory (its blocks, entrance, workplace).

A slender timber-and-bamboo watchtower on a stone platform: a plastered ground room with a lattice window and a
lantern, a ladder up to a gallery, and at the top an open round platform behind a bamboo railing that turns slowly
(the vanilla ObservatoryAnimator's dome) carrying a long bamboo telescope on a yoke that tilts up and down (its
telescope), under a crescent-moon finial on a pole.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("StarTower", size=(3, 3, 5), seed=157, stand_in="Observatory.Folktails")
g = m.geo
B = 0.14
K.plinth(g, 0.08, 0.1, 2.92, 2.9, h=B)
# ground room
with g.tagged("walls"):
    K.wall(g, (0.6, 0.65), (2.4, 0.65), B, 1.1, openings=[("door", 0.5, 0.36, 0.0, 0.62)])
    K.wall(g, (2.4, 0.65), (2.4, 2.35), B, 1.1, openings=[("window", 0.5, 0.36, 0.38, 0.72)])
    K.wall(g, (2.4, 2.35), (0.6, 2.35), B, 1.1)
    K.wall(g, (0.6, 2.35), (0.6, 0.65), B, 1.1, openings=[("window", 0.5, 0.36, 0.38, 0.72)])
K.roof(g, 0.6, 0.65, 2.4, 2.35, 1.1, 1.45, kind="hip", overhang=0.2, sag=0.04, lift=0.05, ridge=False, tile=0.3,
       course=0.3, hip_inset=0.5)
# the tower: four leaning posts from the roof up to the platform, braced
TOP = 3.05
with g.tagged("frame"):
    for (x, z) in ((0.85, 0.9), (2.15, 0.9), (2.15, 2.1), (0.85, 2.1)):
        K.beam(g, (x, 0.9, z), (1.5 + (x - 1.5) * 0.62, TOP, 1.5 + (z - 1.5) * 0.62), w=0.09, caps=False)
    for y, f in ((1.9, 0.8), (2.55, 0.7)):
        pts = [(1.5 + (x - 1.5) * f, y, 1.5 + (z - 1.5) * f) for (x, z) in ((0.85, 0.9), (2.15, 0.9), (2.15, 2.1),
                                                                          (0.85, 2.1))]
        for i in range(4):
            K.pole(g, pts[i], pts[(i + 1) % 4], r=0.025, material=BAMBOO_GOLD, sides=4, bend=0.0, caps=False)
K.ladder(g, (1.5, 1.45, 0.62), (1.5, TOP, 1.12), width=0.26, rungs=7)
K.box(g, (0.95, TOP - 0.06, 0.95), (2.05, TOP, 2.05), TIMBER, WOOD_BLOCK, skip=(3,))
K.lantern(g, (2.55, 1.0, 0.5), r=0.07, h=0.16)
C = np.array([1.5, TOP, 1.5])
with g.node("#StarDome"):
    # a turning round platform: plank disc, bamboo railing, a stool for the watcher
    K.lathe(g, [(0.0, 0.0), (0.62, 0.0), (0.62, 0.05)], C, 12, TIMBER, strips=[WOOD_BLOCK])
    for k in range(10):
        a = 2 * math.pi * k / 10
        p = C + np.array([math.cos(a) * 0.58, 0.05, math.sin(a) * 0.58])
        K.pole(g, p, p + [0, 0.42, 0], r=0.018, material=BAMBOO_GOLD, sides=4, bend=0.0)
    ring = [C + np.array([math.cos(a) * 0.58, 0.45, math.sin(a) * 0.58]) for a in np.linspace(0, 2 * math.pi, 13)]
    K.tube(g, ring, [0.022] * len(ring), BAMBOO_GOLD, sides=4, caps=False)
    K.lathe(g, [(0.0, 0.0), (0.1, 0.0), (0.1, 0.22), (0.0, 0.22)], C + [0.25, 0.05, -0.2], 6, TIMBER)
    # the yoke for the telescope
    for sx in (-1, 1):
        K.beam(g, C + [sx * 0.16, 0.05, 0.1], C + [sx * 0.16, 0.62, 0.1], w=0.05)
    # crescent-moon finial on a pole at the back of the platform
    K.pole(g, C + [0, 0.05, 0.52], C + [0, 1.05, 0.52], r=0.022, material=BAMBOO_GOLD, sides=4, bend=0.0)
    arc = [C + [0.18 * math.cos(t), 1.18 + 0.18 * math.sin(t), 0.52] for t in np.linspace(-1.9, 1.9, 7)]
    K.tube(g, arc, [0.012, 0.03, 0.04, 0.045, 0.04, 0.03, 0.012], BAMBOO_GOLD, sides=5, caps=False)
TP = C + np.array([0.0, 0.6, 0.1])
with g.node("#StarTelescope"):
    K.tube(g, [TP + [0, 0, -0.5], TP + [0, 0, 0.7]], [0.07, 0.05], BAMBOO_GREEN, sides=8)
    for zz in (-0.3, 0.15, 0.55):
        K.lashing(g, TP + [0, 0, zz], (0, 0, 1), r=0.07)
    K.tube(g, [TP + [0, 0, 0.7], TP + [0, 0, 0.78]], [0.065, 0.065], IRON, sides=8)
m.animate("#StarDome", C, (0, 1, 0), kind="static", driver="ObservatoryAnimatorSpec.DomeName (turns about y)")
m.animate("#StarTelescope", TP, (1, 0, 0), kind="static", parent="#StarDome",
          driver="ObservatoryAnimatorSpec.TelescopeName (tilts about x)")
m.extra["observatoryAnimator"] = {"DomeName": "#StarDome", "TelescopeName": "#StarTelescope"}
m.entrance(1, -1, 0)
m.slot("Entrance", (1.5, B, 0.5), yaw=180)
m.extra["access"] = {"X": 1.5, "Y": B, "Z": 0.75}
m.stage_height = 2.0
m.collider((1.5, 0.6, 1.5), (2.0, 1.2, 1.9))
m.collider((1.5, 2.3, 1.5), (1.3, 1.6, 1.3))
m.collider((1.5, 3.4, 1.5), (1.3, 0.8, 1.3))
m.notes += ["Blocks and workplace as the vanilla Observatory; its ObservatoryAnimatorSpec must name #StarDome and "
            "#StarTelescope (observatoryAnimator). Windows light at night while the Ringtail watchers work."]
m.build()
