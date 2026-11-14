"""Shoot bamboo: the starter field crop. A low clump of thin green culms with small leaf fans on a soil mound, and at
harvest three or four fat, sheathed shoots (tan with dark speckles, yellow-green tips) pushing up around it: the food.

Blueprint basis Carrot (1x1x1, Farmhouse, cut and removed).
    E:\\PandabornDev\\tools\\venv\\Scripts\\python.exe -I art/plants/PandabornShootBamboo/build.py
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "src", "pipeline", "plants"))
import atlas as A  # noqa: E402
from plant import Plant, card, stem, state_tint, jitter, ambient, auto_sway, mound  # noqa: E402

ID = "PandabornShootBamboo"
CULM = np.array([0.50, 0.66, 0.30])
LEAF = np.array([0.36, 0.50, 0.18])
C = np.array([0.5, 0.0, 0.5])


def leaf_col(rng, state):
    return state_tint(jitter(rng, LEAF, 0.1, 0.06), state, dry_to=jitter(rng, [0.64, 0.56, 0.27], 0.07),
                      dead_to=jitter(rng, [0.5, 0.42, 0.3], 0.05))


def shoot(m, p, h, r, state, lean=(0.0, 0.0)):
    tint = state_tint([1, 1, 1], state, dry_to=[0.92, 0.82, 0.66], dead_to=[0.66, 0.6, 0.55])
    m.tube([p, p + np.array([lean[0] * 0.4, h * 0.45, lean[1] * 0.4]), p + np.array([lean[0], h, lean[1]])],
           [r, r * 0.72, r * 0.08], 6, A.uv("sheath"), sway=[0, 0.1, 0.2], color=tint)


def clump(m, rng, state, culms, h_range, leaves, shoots, shoot_size):
    soil = "soil_mound" if state == "alive" else "soil_mound_dry"
    mound(m, C, 0.4, 0.012, A.uv(soil), [1, 1, 1])
    for i in range(culms):
        a = 2 * math.pi * i / culms + rng.uniform(-0.4, 0.4)
        b = C + np.array([math.cos(a) * 0.06, 0.03, math.sin(a) * 0.06])
        H = rng.uniform(*h_range) * (0.6 if state == "dead" else 1.0)
        top = b + np.array([math.cos(a) * 0.08, H, math.sin(a) * 0.08])
        c = state_tint(jitter(rng, CULM, 0.07, 0.05), state, dry_to=[0.78, 0.7, 0.42], dead_to=[0.62, 0.58, 0.5])
        stem(m, b, top, 0.016, 0.009, A.uv("culm_thin"), c, sides=4, segments=1, v_range=(0.1, 0.1 + H / 3))
        nl = leaves if state != "dead" else 1
        for j in range(nl):
            f = 0.55 + 0.45 * (j + 0.5) / nl
            p = b + (top - b) * f
            az = a + rng.uniform(-1.6, 1.6)
            s = rng.uniform(0.22, 0.3)
            card(m, p, az, rng.uniform(0.2, 0.6), s, s, A.uv(["bamboo_spray_c", "bamboo_spray_d", "bamboo_spray_e"][j % 3]
                                                               if state != "dead" else "bamboo_dry"),
                 leaf_col(rng, state), back_offset=0.03, sway=(0.5, 1.0))
    for k in range(4):        # low leaf fans on the ground around the clump
        a = 2 * math.pi * k / 4 + rng.uniform(-0.3, 0.3)
        p = C + np.array([math.cos(a) * 0.12, 0.05, math.sin(a) * 0.12])
        card(m, p, a, rng.uniform(0.35, 0.6), 0.26, 0.3, A.uv("shoot_leaves") if state != "dead" else A.uv("withered"),
             leaf_col(rng, state), sway=(0.1, 0.6))
    for k in range(shoots):
        a = 2 * math.pi * (k + 0.3) / shoots + rng.uniform(-0.25, 0.25)
        rr = rng.uniform(0.22, 0.3)
        p = C + np.array([math.cos(a) * rr, 0.0, math.sin(a) * rr])
        h = shoot_size * rng.uniform(0.85, 1.15)
        shoot(m, p, h, h * 0.22, state, lean=(math.cos(a) * 0.05, math.sin(a) * 0.05))


def mature(m, state):
    rng = np.random.default_rng(4)
    clump(m, rng, state, culms=4, h_range=(0.42, 0.62), leaves=2, shoots=3, shoot_size=0.3)
    ambient(m, 0.45, floor=0.55)
    auto_sway(m, 0.65, seed=1)


def seedling(m, state):
    rng = np.random.default_rng(6)
    clump(m, rng, state, culms=2, h_range=(0.2, 0.3), leaves=1, shoots=2, shoot_size=0.12)
    ambient(m, 0.25, floor=0.6)
    auto_sway(m, 0.35, seed=2)


p = Plant(ID, kind="Crops", script_dir=HERE)
p.stage("Seedling", seedling)
p.stage("Mature", mature)
p.extra = {
    "basis": "Carrot",
    "blockHeight": 1,
    "randomizer": {"ConstrainProportion": True, "MinHeightScaleFactor": 0.92, "MaxHeightScaleFactor": 1.08,
                   "MinWidthScaleFactor": 0.95, "MaxWidthScaleFactor": 1.05, "RandomizedRotation": "BetweenMinAndMax",
                   "MinRotation": 0.0, "MaxRotation": 360.0,
                   "note": "Carrot has no randomizer; add this one (NaturalResourceModelRandomizerSpec) so a field is not a stamp"},
    "colliders": {"Seedling": {"box": {"center": [0.5, 0.1, 0.5], "size": [1.0, 0.2, 1.0]}},
                  "Mature": {"box": {"center": [0.5, 0.25, 0.5], "size": [1.0, 0.5, 1.0]}}},
}
if __name__ == "__main__":
    p.build()
