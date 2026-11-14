"""Memorial Arch: the first monument. 2x2x5 on the vanilla Brazier of Bonding (its ranged effect, and its 'Fire'
attachment, which burns here in an iron lantern cage hanging under the arch).

A rural memorial gatehouse, not a palace one (and not a single-beam gate: no beam ends past the posts): four
slim dark-timber posts on stone drums, flush tie beams, carved corbels, a blank lacquered name board in a red frame
(no writing) hung under the front beam, a light two-tier roof (a thin hipped eave and a small raised gable); under it an iron lantern cage holding the flame; indigo banners hanging from the lower beam; lanterns
and potted bamboo at the feet.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("MemorialArch", size=(2, 2, 5), seed=263, stand_in="BrazierOfBonding.Folktails", overhang=0.4)
g = m.geo
K.box(g, (0.0, 0.0, 0.3), (2.0, 0.12, 1.7), PLASTER, (0.1, 0.1, 0.9, 0.9), skip=(3,), tags={"base"})
g.parts[-1].C = np.tile([0.6, 0.6, 0.57, 1.0], (len(g.parts[-1].P), 1))
H = 3.4
# a gatehouse frame, not a single-beam gate: four posts (a front and a back pair) on stone drums, every beam
# ending flush in a post (no beam ends overhanging the posts), carved corbel brackets under the eaves
for x in (0.22, 1.78):
    for z in (0.62, 1.38):
        K.lathe(g, [(0.0, 0.0), (0.15, 0.0), (0.16, 0.22), (0.12, 0.3), (0.0, 0.32)], (x, 0.12, z), 8, PLASTER,
                uv_region=(0.1, 0.1, 0.9, 0.9))
        g.parts[-1].C = np.tile([0.58, 0.58, 0.56, 1.0], (len(g.parts[-1].P), 1))
        K.beam(g, (x, 0.4, z), (x, H, z), w=0.11, caps="end", tags={"frame"})
        for sx in (-1, 1):   # corbel brackets
            K.beam(g, (x, H - 0.3, z), (x + sx * 0.22, H - 0.04, z), w=0.07, caps=False)
    for y in (2.25, H - 0.08):
        K.beam(g, (x, y, 0.62), (x, y, 1.38), w=0.12, caps=False, tags={"frame"})
for z in (0.62, 1.38):
    for y in (2.25, H - 0.08):
        K.beam(g, (0.22, y, z), (1.78, y, z), w=0.09, h=0.13, caps=False, tags={"frame"})
# the name board under the front top beam: a plain lacquered board in a red frame (blank: no writing), hung a
# little forward on two iron rings
NB = (1.0, 2.82, 0.56)
K.box(g, (NB[0] - 0.42, NB[1] - 0.2, NB[2] - 0.03), (NB[0] + 0.42, NB[1] + 0.2, NB[2] + 0.03), DETAILS, DET_RED)
K.box(g, (NB[0] - 0.36, NB[1] - 0.15, NB[2] - 0.045), (NB[0] + 0.36, NB[1] + 0.15, NB[2] - 0.03), PLASTER,
      (0.1, 0.1, 0.9, 0.9))
g.parts[-1].C = np.tile([0.2, 0.16, 0.12, 1.0], (len(g.parts[-1].P), 1))
for x in (NB[0] - 0.3, NB[0] + 0.3):
    K.beam(g, (x, NB[1] + 0.2, NB[2]), (x, H - 0.16, 0.62), w=0.02, material=IRON, caps=False)
# a light two-tier roof: a thin lower eave all round on the corbels, and above it, on short posts, a small gable
K.roof(g, 0.1, 0.5, 1.9, 1.5, H, H + 0.32, kind="hip", hip_inset=0.55, overhang=0.2, sag=0.06, lift=0.06, thick=0.05,
       ridge=False, tile=0.24, course=0.24)
for x in (0.55, 1.45):
    for z in (0.82, 1.18):
        K.beam(g, (x, H + 0.15, z), (x, H + 0.5, z), w=0.06, caps=False)
K.roof(g, 0.5, 0.78, 1.5, 1.22, H + 0.5, H + 0.82, kind="gable", overhang=0.16, sag=0.05, lift=0.05, thick=0.05,
       ridge_ends=0.06, tile=0.22, course=0.22)
# the lantern cage for the flame, hung from the lower beam
FC = np.array([1.0, 1.75, 1.0])
K.beam(g, (1.0, 2.25, 0.62), (1.0, 2.25, 1.38), w=0.08, caps=False)
K.beam(g, (1.0, 2.26, 1.0), FC + [0, 0.42, 0], w=0.02, material=IRON, caps=False)
for k in range(4):
    a = math.pi / 4 + k * math.pi / 2
    K.beam(g, FC + [math.cos(a) * 0.16, -0.05, math.sin(a) * 0.16], FC + [math.cos(a) * 0.12, 0.42, math.sin(a) * 0.12],
           w=0.025, material=IRON, caps=False)
K.lathe(g, [(0.0, 0.0), (0.18, 0.0), (0.18, 0.05)], FC + [0, -0.06, 0], 8, IRON, cap_top=False)
# banners from the lower beam, lanterns and bamboo at the feet
for x in (0.45, 1.55):
    K.cloth(g, [(x - 0.14, 1.45, 0.55), (x + 0.14, 1.45, 0.55), (x + 0.14, 2.17, 0.55), (x - 0.14, 2.17, 0.55)], DETAILS,
            DET_BANNER, sag=0.0, nu=2, nv=3, wave=0.02)
for x in (0.0, 2.0):
    K.standing_lantern(g, (x, 0.12, 0.45), h=0.9)
    K.lathe(g, [(0.0, 0.0), (0.1, 0.0), (0.12, 0.15)], (x, 0.12, 1.55), 7, EARTH)
    for k in range(4):
        K.pole(g, (x, 0.27, 1.55), (x + 0.06 * (k - 1.5), 1.0 + 0.1 * k, 1.55), r=0.013, material=BAMBOO_GREEN,
               sides=3, bend=0.03, caps=False)
m.attach("Fire", tuple(FC + [0, 0.06, 0]), "the vanilla brazier flame burns in the lantern cage under the arch")
m.collider((1.0, 2.0, 1.0), (1.8, 4.0, 1.0))
m.stage_height = 2.5
m.notes += ["Blocks and effects as the vanilla Brazier of Bonding; one construction stage (thresholds [0.0])."]
m.build()
