"""Hammock: a daily nap in the sun. 1x1, the vanilla Hammock's blueprint, pivot, swing and lying slot.

A woven-cloth hammock slung between a tall forked bamboo post at the back and a short stake at the front, swaying
when someone naps in it (the vanilla '#Hammock#Animated' node, played by EnterableAnimationController), on a woven
mat, with a stump table, a teapot and a cup beside it.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, block  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("Hammock", size=(1, 1, 1), seed=31, stand_in="Hammock.Folktails")
g = m.geo

# the vanilla pivot: the swing axis runs from low at the front to high at the back (30 degrees)
PIVOT = np.array([0.499, 0.616, 0.47])
QP = (-0.26, 0.0, 0.0, 0.966)
R = quat_mat(QP)
AX = R @ np.array([0, 0, 1.0])


def W(x, y, z):
    """world position of a point given in the swing frame (z along the axis, y up from it)"""
    return PIVOT + R @ np.array([x, y, z])


hi, lo = W(0, 0, 0.6), W(0, 0, -0.62)
# back post: two lashed bamboo poles forking at the top; front stake
K.pole(g, (0.42, 0.0, 0.97), (0.5, hi[1] + 0.12, hi[2] - 0.02), r=0.035, material=BAMBOO_GOLD, sides=6, bend=0.02)
K.pole(g, (0.6, 0.0, 0.95), (0.47, hi[1] + 0.08, hi[2]), r=0.03, material=BAMBOO_GREEN, sides=5, bend=0.02)
K.lashing(g, (0.48, hi[1] - 0.05, hi[2]), (0, 1, 0), r=0.05)
K.pole(g, (0.5, 0.0, 0.03), (0.5, lo[1] + 0.06, max(lo[2], 0.0) + 0.02), r=0.03, material=TIMBER, sides=5, bend=0.0)
# woven mat under it
K.panel(g, [(0.12, 0.01, 0.12), (0.88, 0.01, 0.12), (0.88, 0.01, 0.86), (0.12, 0.01, 0.86)], WEAVE_GOLD)
# stump table with a teapot and cup
K.lathe(g, [(0.0, 0.0), (0.09, 0.0), (0.08, 0.16), (0.0, 0.16)], (0.86, 0.0, 0.32), 6, TIMBER, cap_top=False)
K.lathe(g, [(0.0, 0.0), (0.03, 0.0), (0.045, 0.03), (0.03, 0.06), (0.0, 0.065)], (0.86, 0.16, 0.3), 6, EARTH)
K.lathe(g, [(0.0, 0.0), (0.018, 0.0), (0.02, 0.025)], (0.82, 0.16, 0.37), 5, PLASTER, cap_top=False)

with g.node("#Hammock#Animated"):
    # the sling: a sagging cloth in the swing frame, edges curled up
    nu, nv = 3, 6
    corners = []
    pts = []
    for j in range(nv + 1):
        t = j / nv
        z = -0.5 + 0.98 * t
        sag = 0.42 + 0.1 * math.sin(math.pi * t)
        row = []
        for i in range(nu + 1):
            s = i / nu
            x = (s - 0.5) * 0.46 * (0.75 + 0.25 * math.sin(math.pi * t))
            y = -sag + 0.12 * (2 * abs(s - 0.5)) ** 2
            row.append(W(x, y, z))
        pts.append(row)
    for j in range(nv):
        for i in range(nu):
            q = [pts[j][i], pts[j][i + 1], pts[j + 1][i + 1], pts[j + 1][i]]
            # striped: indigo cloth and hemp in alternate bands along the sling
            if j % 2:
                uv = np.array([[0.03, 0.54], [0.08, 0.54], [0.08, 0.62], [0.03, 0.62]])
            else:
                uv = np.array([[0.53 + 0.06 * i, 0.6], [0.59 + 0.06 * i, 0.6], [0.59 + 0.06 * i, 0.7],
                               [0.53 + 0.06 * i, 0.7]])
            n = np.cross(q[1] - q[0], q[3] - q[0])
            n = n / np.linalg.norm(n) * (1 if n[1] > 0 else -1)
            g.add(quad_part(DETAILS, q, uvs=uv, normal=n))
            g.add(quad_part(DETAILS, [q[1], q[0], q[3], q[2]], uvs=uv[[1, 0, 3, 2]], normal=-n))
    # spreader bars and ropes up to the two ends of the axis
    for z, end in ((-0.5, lo), (0.48, hi)):
        a, b = pts[0 if z < 0 else nv][0], pts[0 if z < 0 else nv][nu]
        K.pole(g, a + (a - b) * 0.12, b + (b - a) * 0.12, r=0.018, material=BAMBOO_GOLD, sides=4, bend=0.0)
        for e in (a, b):
            K.beam(g, e, end, w=0.012, material=DETAILS, caps=False)
    # a folded indigo blanket at the foot
    f0 = W(-0.14, -0.43, -0.38)
    K.box(g, (-0.13, 0, -0.07), (0.13, 0.05, 0.07), DETAILS, DET_CLOTH, R=R, t=f0)

m.animate("#Hammock#Animated", PIVOT, (0, 0, 1), kind="swing", amplitude=0.26, pivot_rot=QP,
          driver="EnterableAnimationControllerSpec (plays while someone lies in it)")
# the vanilla lying slot, parented to the swinging node
m.slots.append({"name": "Spot", "parent": "#Hammock#Animated", "local_pos": (0.0, -0.359, -0.178),
                "local_rot": (0.0, -0.966, -0.26, 0.0)})
m.blocks = [block("GroundOrStackable", "Bottom, Path, Middle", "None")]
m.entrance(0, -1, 0)
m.extra["access"] = {"X": 0.5, "Y": 0.0, "Z": 0.0}
m.collider((0.5, 0.05, 0.5), (0.8, 0.1, 0.8))
m.collider((0.5, 0.35, 0.5), (0.5, 0.3, 0.9))
m.collider((0.5, 0.6, 0.95), (0.25, 1.2, 0.15))
m.notes += ["Pivot, swing axis, amplitude and the Spot slot copy the vanilla Hammock so the Swinging pose fits."]
m.build()
