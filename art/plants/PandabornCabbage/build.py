"""Napa cabbage: four tall, barrel-shaped heads per tile, pale yellow-green crinkled leaves with broad white midribs
wrapped tight, a skirt of darker spreading outer leaves. Planted fields read as neat rows of pale barrels.

Blueprint basis Carrot (1x1x1, Farmhouse, cut and removed). Recommended randomizer: rotation by 90 degrees (rows stay
rows), scale 0.92..1.08.
    E:\\PandabornDev\\tools\\venv\\Scripts\\python.exe -I art/plants/PandabornCabbage/build.py
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "src", "pipeline", "plants"))
import atlas as A  # noqa: E402
from plant import Plant, card, state_tint, jitter, ambient, auto_sway, mound  # noqa: E402

ID = "PandabornCabbage"
INNER = np.array([0.74, 0.84, 0.46])
OUTER = np.array([0.38, 0.56, 0.24])
HEADS = [(0.27, 0.27), (0.73, 0.29), (0.29, 0.73), (0.71, 0.71)]


def col(rng, base, state):
    return state_tint(jitter(rng, base, 0.06, 0.04), state, dry_to=jitter(rng, [0.80, 0.72, 0.40], 0.05),
                      dead_to=jitter(rng, [0.55, 0.46, 0.33], 0.05))


def head(m, rng, c, H, r, state):
    leaf = A.uv("cabbage_leaf")
    sag = {"alive": 0.0, "dry": 0.25, "dead": 0.7}[state]
    # spreading outer leaves first (underneath)
    for k in range(4):
        a = 2 * math.pi * (k + 0.5) / 4 + rng.uniform(-0.3, 0.3)
        o = np.array([math.cos(a), 0, math.sin(a)])
        reach = r * rng.uniform(2.0, 2.5) * (1 + 0.3 * sag)
        spine = [c + o * r * 0.3 + [0, 0.02, 0], c + o * reach * 0.55 + [0, H * (0.42 - 0.3 * sag), 0],
                 c + o * reach + [0, H * (0.22 - 0.2 * sag), 0]]
        nrm = [o * -0.3 + [0, 1, 0], o * 0.3 + [0, 1, 0], o * 0.6 + [0, 1, 0]]
        m.strip(spine, [r * 0.9, r * 2.0, r * 1.7], nrm, leaf, [0, 0.4, 0.8], color=col(rng, OUTER, state),
                two_sided=False)
    # the head: inner leaves wrapping a barrel, overlapping
    n = 5
    for k in range(n):
        a = 2 * math.pi * k / n + rng.uniform(-0.15, 0.15)
        o = np.array([math.cos(a), 0, math.sin(a)])
        h = H * rng.uniform(0.9, 1.05) * (1 - 0.45 * sag)
        bulge = r * (1 + 0.3 * sag)
        spine = [c + o * r * 0.55, c + o * bulge * 1.02 + [0, h * 0.5, 0], c + o * r * 0.55 * (1 + sag) + [0, h, 0]]
        nrm = [o + [0, -0.2, 0], o + [0, 0.15, 0], o * 0.6 + [0, 1, 0]]
        w = 2 * math.pi * r / n * 1.55
        m.strip(spine, [w * 0.6, w * 1.0, w * 0.85], nrm, leaf, [0, 0.4, 0.75],
                color=col(rng, INNER if k % 2 else INNER * 0.92, state), two_sided=False)
    # the folded leaf tips closing the top
    top = c + [0, H * (1 - 0.45 * sag) * 0.97, 0]
    card(m, top - [r * 0.5, 0, 0], 0.0 + rng.uniform(-0.3, 0.3), 0.25, r * 1.2, r * 1.3, A.sub(leaf, 0.1, 0.55, 0.9, 1.0),
         col(rng, INNER, state), sway=(0.5, 0.6))


def mature(m, state):
    rng = np.random.default_rng(12)
    mound(m, np.array([0.5, 0, 0.5]), 0.5, 0.04, A.uv("soil_mound" if state == "alive" else "soil_mound_dry"), [1, 1, 1], 8)
    for (x, z) in HEADS:
        c = np.array([x + rng.uniform(-0.03, 0.03), 0.02, z + rng.uniform(-0.03, 0.03)])
        head(m, rng, c, rng.uniform(0.32, 0.38), rng.uniform(0.095, 0.11), state)
    ambient(m, 0.35, floor=0.55)
    auto_sway(m, 0.45, seed=1)


def seedling(m, state):
    rng = np.random.default_rng(13)
    mound(m, np.array([0.5, 0, 0.5]), 0.5, 0.04, A.uv("soil_mound" if state == "alive" else "soil_mound_dry"), [1, 1, 1], 8)
    droop = {"alive": 0.0, "dry": 0.25, "dead": 0.5}[state]
    for (x, z) in HEADS:
        c = np.array([x, 0.03, z])
        for k in range(4):
            a = 2 * math.pi * k / 4 + rng.uniform(-0.4, 0.4)
            s = rng.uniform(0.13, 0.17)
            card(m, c, a, math.radians(rng.uniform(40, 60)) - droop, s, s * 0.8,
                 A.uv("cabbage_young") if state != "dead" else A.uv("withered"), col(rng, OUTER * 1.15, state),
                 sway=(0.0, 0.8))
    ambient(m, 0.15, floor=0.6)
    auto_sway(m, 0.25, seed=2)


p = Plant(ID, kind="Crops", script_dir=HERE)
p.stage("Seedling", seedling)
p.stage("Mature", mature)
p.extra = {
    "basis": "Carrot",
    "blockHeight": 1,
    "randomizer": {"ConstrainProportion": True, "MinHeightScaleFactor": 0.92, "MaxHeightScaleFactor": 1.08,
                   "MinWidthScaleFactor": 1.0, "MaxWidthScaleFactor": 1.0, "RandomizedRotation": "By90Degree",
                   "MinRotation": 0.0, "MaxRotation": 360.0},
    "colliders": {"Seedling": {"box": {"center": [0.5, 0.1, 0.5], "size": [1.0, 0.2, 1.0]}},
                  "Mature": {"box": {"center": [0.5, 0.2, 0.5], "size": [1.0, 0.4, 1.0]}}},
}
if __name__ == "__main__":
    p.build()
