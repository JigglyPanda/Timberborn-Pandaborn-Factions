"""Great Sitting Panda: the top monument. 5x5x3 on the vanilla Hall of Abundance (its blocks and monument specs).

A free-standing outcrop of grey river cliff with a big friendly panda carved out of its face, sitting with its legs
out in front, holding a bamboo stalk to its mouth, the carving painted in the folk way (white body, black ears, eye
patches, arms and legs, the stalk green); a little red panda carved sitting on its knee, waving. At its feet a still
pool in a stone kerb with stepping stones, red lanterns on posts either side. No religious imagery: no halo, no
offerings, no incense; a village landmark, not a shrine.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("GreatSittingPanda", size=(5, 5, 3), seed=197, stand_in="HallOfAbundance.Folktails", overhang=0.3)
g = m.geo
WHITE, BLACK, STONE = (0.9, 0.89, 0.85), (0.16, 0.16, 0.17), (0.6, 0.6, 0.58)
GREEN, RED = (0.42, 0.55, 0.3), (0.62, 0.3, 0.16)


def blob(c, rx, ry, rz, col, sides=10, rings=6, R=None):
    """An ellipsoid of carved stone (lime sheet painted by vertex colour)."""
    prof = [(math.sin(math.pi * k / rings), -math.cos(math.pi * k / rings)) for k in range(rings + 1)]
    n0 = len(g.parts)
    K.lathe(g, prof, (0, 0, 0), sides, PLASTER, uv_region=(0.1, 0.1, 0.9, 0.9), cap_top=False)
    p = g.parts[-1]
    S = np.diag([rx, ry, rz])
    M = S if R is None else R @ S
    p.P = p.P @ M.T + np.asarray(c, float)
    p.N = p.N @ np.linalg.inv(M)
    p.N /= np.linalg.norm(p.N, axis=1, keepdims=True)
    p.T = fix_winding(p.P, p.N, p.T)
    p.C = np.tile(list(col) + [1.0], (len(p.P), 1))
    return g.parts[n0:]


def limb(a, b, r0, r1, col):
    n0 = len(g.parts)
    K.tube(g, [a, b], [r0, r1], PLASTER, sides=8, caps=True, strips=[(0.1, 0.1, 0.9, 0.9)])
    for p in g.parts[n0:]:
        p.C = np.tile(list(col) + [1.0], (len(p.P), 1))


# the cliff: a heap of big irregular stone blocks across the back, rising behind the panda's shoulders
rng = np.random.default_rng(7)
for k in range(16):
    x = 0.3 + 4.4 * (k % 8) / 7 + rng.uniform(-0.15, 0.15)
    z = 3.6 + 0.8 * (k // 8) + rng.uniform(-0.1, 0.1)
    h = 1.6 + 1.6 * math.sin(math.pi * (x / 5.0)) * (1.0 if k // 8 else 0.85) + rng.uniform(0, 0.4)
    w = rng.uniform(0.45, 0.7)
    K.box(g, (-w, 0, -0.45), (w, h, 0.45), PLASTER, (0.1, 0.1, 0.9, 0.9), R=rot_axis((0, 1, 0), rng.uniform(-0.3, 0.3)),
          t=(x, 0, z), skip=(3,), jitter=0.06)
    t = rng.uniform(0.85, 1.05)
    g.parts[-1].C = np.tile([STONE[0] * t, STONE[1] * t, STONE[2] * t * 1.03, 1.0], (len(g.parts[-1].P), 1))
K.box(g, (0.2, 0.0, 1.4), (4.8, 0.45, 3.9), EARTH, (0.02, 0.02, 0.98, 0.98), skip=(3,), tags={"base"})
K.stones(g, 0.2, 1.4, 4.8, 3.9, y=-0.01, size=0.35, h=0.42, skip=0.1, tags={"base"})
# moss in the cliff's top and a few bamboo culms growing out of it
for (x, z) in ((0.8, 4.1), (4.2, 4.0), (1.2, 4.6), (3.9, 4.6)):
    for k in range(4):
        K.pole(g, (x + 0.05 * k, 1.8, z), (x + 0.15 * k - 0.2, 3.4 + 0.3 * (k % 2), z + 0.1), r=0.025,
               material=BAMBOO_GREEN, sides=4, bend=0.03, segs=2)
# the panda, seated on the ledge facing front
P0 = np.array([2.5, 0.45, 2.7])
blob(P0 + [0, 0.95, 0], 1.05, 1.0, 0.85, WHITE, sides=12, rings=7)                    # body
blob(P0 + [0, 0.75, -0.55], 0.75, 0.55, 0.35, WHITE)                                   # belly front
blob(P0 + [0, 1.75, -0.2], 1.0, 0.32, 0.72, BLACK)                                     # shoulder band
blob(P0 + [0, 2.55, -0.1], 0.72, 0.62, 0.66, WHITE, sides=12, rings=7)                 # head
for sx in (-1, 1):
    blob(P0 + [sx * 0.52, 3.05, -0.05], 0.22, 0.2, 0.12, BLACK)                         # ears
    R = rot_axis((0, 0, 1), sx * 0.5)
    blob(P0 + [sx * 0.26, 2.62, -0.62], 0.14, 0.2, 0.07, BLACK, R=R)                    # eye patches
    blob(P0 + [sx * 0.26, 2.66, -0.68], 0.045, 0.045, 0.03, WHITE)                      # eye glints
    limb(P0 + [sx * 0.55, 0.25, -0.35], P0 + [sx * 0.75, 0.25, -1.25], 0.34, 0.3, BLACK)  # legs out front
    blob(P0 + [sx * 0.78, 0.3, -1.38], 0.3, 0.28, 0.22, BLACK)                          # feet
blob(P0 + [0, 2.4, -0.7], 0.26, 0.2, 0.18, WHITE)                                      # muzzle
blob(P0 + [0, 2.48, -0.86], 0.08, 0.06, 0.05, BLACK)                                   # nose
# arms: both hands bring the bamboo stalk up to the mouth
limb(P0 + [-0.85, 1.65, -0.25], P0 + [-0.35, 1.95, -0.85], 0.3, 0.24, BLACK)
limb(P0 + [0.85, 1.65, -0.25], P0 + [0.4, 2.1, -0.85], 0.3, 0.24, BLACK)
limb(P0 + [-0.15, 1.1, -0.95], P0 + [0.25, 3.3, -0.95], 0.08, 0.07, GREEN)            # the stalk
for (y, sx) in ((2.9, 1), (3.15, -1)):
    blob(P0 + [0.2 + sx * 0.18, y, -0.95], 0.22, 0.05, 0.08, GREEN, R=rot_axis((0, 0, 1), sx * 0.5))  # leaves
# the little red panda sitting on its right knee, waving
RP = P0 + np.array([0.8, 0.62, -1.15])
blob(RP + [0, 0.22, 0], 0.18, 0.24, 0.16, RED)
blob(RP + [0, 0.55, -0.02], 0.16, 0.14, 0.14, RED)
blob(RP + [0, 0.52, -0.14], 0.08, 0.06, 0.05, WHITE)
limb(RP + [0.12, 0.35, 0], RP + [0.26, 0.62, -0.05], 0.05, 0.045, BLACK)
limb(RP + [-0.05, 0.1, 0.12], RP + [-0.3, 0.05, 0.3], 0.08, 0.06, RED)                  # the ringed tail
# the pool at its feet: a stone kerb round still water (lime sheet painted deep teal), stepping stones
K.box(g, (0.5, 0.0, 0.15), (4.5, 0.06, 1.35), PLASTER, (0.1, 0.1, 0.9, 0.9), skip=(3,))
g.parts[-1].C = np.tile([0.22, 0.36, 0.4, 1.0], (len(g.parts[-1].P), 1))
K.stones(g, 0.45, 0.1, 4.55, 1.4, y=-0.01, size=0.32, h=0.2, skip=0.0)
K.stones(g, 2.2, 0.35, 2.8, 1.2, y=0.0, size=0.3, h=0.1, ring=False, skip=0.0, tone=(0.55, 0.55, 0.52))
for x in (0.3, 4.7):
    K.standing_lantern(g, (x, 0.0, 0.6), h=0.95)
m.blocks = None
m.collider((2.5, 1.5, 3.2), (4.8, 3.0, 3.4))
m.collider((2.5, 0.1, 0.75), (4.2, 0.2, 1.3))
m.stage_height = 2.0
m.notes += ["Blocks and monument specs as the vanilla Hall of Abundance (no entrance). One construction stage: set "
            "ConstructionSiteProgressVisualizerSpec.ProgressThresholds to [0.0] (the vanilla has two)."]
m.build()
