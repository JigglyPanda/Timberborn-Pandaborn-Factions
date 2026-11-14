"""Sichuan pepper: a low, open, thorny shrub of grey-brown stems with sprays of small pinnate leaves; at harvest small
clusters of red husked berries sit at the branch tips. Red stays a small accent: berries only, under a dark green
canopy.

Blueprint basis Sunflower (1x1x2, Farmhouse, cut and removed, arid: dies on wet roots).
    E:\\PandabornDev\\tools\\venv\\Scripts\\python.exe -I art/plants/PandabornSichuanPepper/build.py
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "src", "pipeline", "plants"))
import atlas as A  # noqa: E402
from plant import Plant, card, stem, state_tint, jitter, ambient, auto_sway, crossed, mound  # noqa: E402

ID = "PandabornSichuanPepper"
LEAF = np.array([0.28, 0.40, 0.15])
STEM = np.array([0.95, 0.93, 0.9])
C = np.array([0.5, 0.0, 0.5])


def col(rng, base, state):
    return state_tint(jitter(rng, base, 0.08, 0.05), state, dry_to=jitter(rng, [0.58, 0.48, 0.22], 0.06),
                      dead_to=jitter(rng, [0.45, 0.37, 0.27], 0.05))


def shrub(m, rng, state, stems, H, crown_r, berries, leaf_cards):
    mound(m, C, 0.22, 0.01, A.uv("soil_mound_dry"), [0.95, 0.95, 0.95], 7)
    tips = []
    for k in range(stems):
        a = 2 * math.pi * k / stems + rng.uniform(-0.3, 0.3)
        h = H * rng.uniform(0.75, 1.0) * (0.85 if state == "dead" else 1.0)
        top = C + np.array([math.cos(a) * crown_r * 0.7, h, math.sin(a) * crown_r * 0.7])
        stem(m, C + np.array([0, 0.02, 0]), top, 0.022, 0.009, A.uv("pepper_stem"),
             state_tint(STEM, state, dry_to=[0.95, 0.9, 0.85], dead_to=[0.8, 0.78, 0.76]), sides=4, segments=2,
             bend=(math.cos(a) * 0.05, -0.04, math.sin(a) * 0.05))
        tips.append((top, a))
    crossed(m, C, rng.uniform(0, 3), H * 1.05, crown_r * 2.0, A.uv("pepper_branch"),
            state_tint(STEM, state, dry_to=[0.9, 0.85, 0.8], dead_to=[0.8, 0.78, 0.76]), sway=(0.0, 0.8))
    if state != "dead":
        for j in range(leaf_cards):
            top, a = tips[j % len(tips)]
            az = a + rng.uniform(-0.9, 0.9)
            p = top - np.array([0, rng.uniform(0.08, 0.2), 0]) * (j // len(tips))
            s = rng.uniform(0.42, 0.52)
            card(m, p, az, math.radians(rng.uniform(-25, 30)), s, s, A.uv("pepper_leaves"), col(rng, LEAF, state),
                 back_offset=s * 0.45, sway=(0.6, 1.0))
        for j in range(berries):
            top, a = tips[j % len(tips)]
            az = a + rng.uniform(-1.0, 1.0)
            s = rng.uniform(0.18, 0.24)
            card(m, top + np.array([0, 0.02, 0]), az, math.radians(rng.uniform(25, 45)), s, s,
                 A.uv("pepper_berries_a" if j % 2 == 0 else "pepper_berries_b"),
                 state_tint([1, 1, 1], state, dry_to=[0.8, 0.62, 0.55], dead_to=[0.55, 0.45, 0.4]),
                 back_offset=s * 0.4, sway=(0.8, 1.0))
    else:
        for top, a in tips[:2]:
            card(m, top - np.array([0, 0.1, 0]), a, 0.3, 0.3, 0.3, A.uv("withered"), col(rng, LEAF, state), sway=(0.5, 0.8))


def mature(m, state):
    rng = np.random.default_rng(31)
    shrub(m, rng, state, stems=4, H=0.8, crown_r=0.36, berries=6 if state != "dead" else 0, leaf_cards=12)
    ambient(m, 0.7, floor=0.55)
    auto_sway(m, 0.9, seed=1)


def seedling(m, state):
    rng = np.random.default_rng(32)
    mound(m, C, 0.2, 0.01, A.uv("soil_mound_dry"), [0.95, 0.95, 0.95], 7)
    stem(m, C, C + np.array([0.01, 0.3, 0]), 0.012, 0.006, A.uv("pepper_stem"), STEM, sides=4, segments=1)
    if state != "dead":
        crossed(m, C, rng.uniform(0, 3), 0.32, 0.26, A.uv("seedling_sprig"), col(rng, LEAF * 1.15, state))
        for k in range(3):
            a = 2 * math.pi * k / 3 + rng.uniform(-0.3, 0.3)
            card(m, C + np.array([0, 0.22, 0]), a, math.radians(rng.uniform(20, 40)), 0.24, 0.24, A.uv("pepper_leaves"),
                 col(rng, LEAF, state), back_offset=0.1, sway=(0.4, 1.0))
    else:
        card(m, C + np.array([0, 0.05, 0]), 0.5, 0.2, 0.24, 0.24, A.uv("withered"), col(rng, LEAF, state))
    ambient(m, 0.3, floor=0.6)
    auto_sway(m, 0.4, seed=2)


p = Plant(ID, kind="Crops", script_dir=HERE)
p.stage("Seedling", seedling)
p.stage("Mature", mature)
p.extra = {
    "basis": "Sunflower",
    "blockHeight": 2,
    "randomizer": {"ConstrainProportion": True, "MinHeightScaleFactor": 0.9, "MaxHeightScaleFactor": 1.1,
                   "MinWidthScaleFactor": 0.9, "MaxWidthScaleFactor": 1.1, "RandomizedRotation": "BetweenMinAndMax",
                   "MinRotation": 0.0, "MaxRotation": 360.0,
                   "note": "Sunflower turns only -40..40 degrees (its heads face the sun); the shrub can turn freely"},
    "colliders": {"Seedling": {"box": {"center": [0.5, 0.15, 0.5], "size": [1.0, 0.3, 1.0]}},
                  "Mature": {"box": {"center": [0.5, 0.4, 0.5], "size": [1.0, 0.8, 1.0]}}},
}
if __name__ == "__main__":
    p.build()
