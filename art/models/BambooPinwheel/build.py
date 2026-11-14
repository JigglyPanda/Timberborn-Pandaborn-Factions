"""Bamboo Pinwheel (decoration): a paper pinwheel of four red and cream sails on a bamboo pole, turning in the wind
(the vanilla Weathervane's WindRotationAnimator: '#PinRotor' spins, '#PinHead' turns to the wind). 1x1x2."""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403


def blob(g, c, rx, ry, rz, col, sides=10, rings=6, material=PLASTER):
    """An ellipsoid of lime sheet painted by vertex colour (carved, painted or glazed surfaces)."""
    prof = [(math.sin(math.pi * k / rings), -math.cos(math.pi * k / rings)) for k in range(rings + 1)]
    K.lathe(g, prof, (0, 0, 0), sides, material, uv_region=(0.1, 0.1, 0.9, 0.9), cap_top=False)
    p = g.parts[-1]
    S = np.diag([rx, ry, rz])
    p.P = p.P @ S.T + np.asarray(c, float)
    p.N = p.N @ np.linalg.inv(S)
    p.N /= np.linalg.norm(p.N, axis=1, keepdims=True)
    p.T = fix_winding(p.P, p.N, p.T)
    p.C = np.tile(list(col) + [1.0], (len(p.P), 1))


m = Model("BambooPinwheel", size=(1, 1, 2), seed=249, stand_in="Weathervane.Folktails")
g = m.geo
K.stones(g, 0.35, 0.35, 0.65, 0.65, y=-0.01, size=0.18, h=0.08, ring=False)
K.pole(g, (0.5, 0.0, 0.5), (0.5, 1.15, 0.5), r=0.025, material=BAMBOO_GOLD, sides=5, bend=0.01)
HC = np.array([0.5, 1.15, 0.5])
with g.node("#PinHead"):
    K.beam(g, HC, HC + [0, 0.0, -0.14], w=0.03)
RC = HC + np.array([0.0, 0.0, -0.16])
with g.node("#PinRotor"):
    for k in range(4):
        a = math.pi / 2 * k
        d = np.array([math.cos(a), math.sin(a), 0.0])
        e = np.array([-math.sin(a), math.cos(a), 0.0])
        q = [RC, RC + d * 0.28, RC + d * 0.28 + e * 0.14 + [0, 0, 0.04], RC + e * 0.05]
        K.panel(g, q, DETAILS if k % 2 else PAPER, DET_RED if k % 2 else (0.36, 0.05, 0.6, 0.6), both=True)
    K.lathe(g, [(0.0, 0.0), (0.03, 0.0), (0.0, 0.03)], RC, 6, BAMBOO_GOLD, axis=(0, 0, -1))
m.animate("#PinHead", HC, (0, 1, 0), kind="static", driver="WindRotationAnimatorSpec.Tower")
m.animate("#PinRotor", RC, (0, 0, 1), kind="static", parent="#PinHead", driver="WindRotationAnimatorSpec.WindRotators")
m.extra["windRotationAnimator"] = {
    "WindRotators": [{"TransformName": "#PinRotor", "RotationAxis": {"X": 0.0, "Y": 0.0, "Z": 1.0},
                      "RotationSpeed": 400.0}],
    "Tower": {"TransformName": "#PinHead", "RotationAxis": {"X": 0.0, "Y": 1.0, "Z": 0.0}, "RotationSpeed": 200.0}}
m.collider((0.5, 0.65, 0.5), (0.3, 1.3, 0.3))
m.build()
