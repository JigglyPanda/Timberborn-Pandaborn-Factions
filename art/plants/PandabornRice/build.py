"""Rice: transplanted hills on a 3x3 grid per tile standing in shallow paddy water (the Paddy Spout's 0.3), fresh
bright-green upright tufts when young, at harvest arching yellow-green leaves under drooping golden panicles.

Blueprint basis Cattail (1x1x2, AquaticFarmhouse, cut and removed, water 0 < depth <= 1). The hills sit on the
paddy floor; seedlings rise about 0.5 above it and mature plants about 0.9, so both stay well clear of 0.3 m water and
still show at a full block of water. The grid (spacing 1/3 tile) continues across tiles, so a field reads as rows.
Recommended randomizer: rotation by 90 degrees, scale 0.95..1.05 (the vanilla Cattail one spins freely and would break
the rows).
    E:\\PandabornDev\\tools\\venv\\Scripts\\python.exe -I art/plants/PandabornRice/build.py
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "src", "pipeline", "plants"))
import atlas as A  # noqa: E402
from plant import Plant, card, state_tint, jitter, ambient, auto_sway, upright  # noqa: E402

ID = "PandabornRice"
YOUNG = np.array([0.42, 0.66, 0.22])
RIPE = np.array([0.66, 0.68, 0.30])
GOLD = np.array([1.0, 0.97, 0.9])
GRID = [(1 / 6 + i / 3, 1 / 6 + j / 3) for i in range(3) for j in range(3)]


def col(rng, base, state):
    return state_tint(jitter(rng, base, 0.07, 0.04), state, dry_to=jitter(rng, [0.76, 0.66, 0.36], 0.05),
                      dead_to=jitter(rng, [0.55, 0.47, 0.34], 0.05))


def hill(m, rng, p, H, W, tuft, colour, yaw):
    # two crossed tuft cards; the sprite's blades fan out from the hill
    for k in range(2):
        upright(m, p, yaw + k * math.pi / 2, H, W, A.uv(tuft), colour, two_sided=True,
                lean=(rng.uniform(-0.03, 0.03), rng.uniform(-0.03, 0.03)), sway=(0.0, 1.0))


def mature(m, state):
    rng = np.random.default_rng(21)
    tuft = "rice_tuft_a" if state != "dead" else "rice_tuft_dry"
    for i, (x, z) in enumerate(GRID):
        p = np.array([x + rng.uniform(-0.025, 0.025), 0.0, z + rng.uniform(-0.025, 0.025)])
        H = rng.uniform(0.78, 0.9) * (0.75 if state == "dead" else 1.0)
        yaw = rng.uniform(0, math.pi)
        hill(m, rng, p, H, 0.42, tuft, col(rng, RIPE, state), yaw)
        if state != "dead":     # drooping golden panicles over the hill, seen from above
            for k in range(2):
                a = yaw + k * math.pi + rng.uniform(-0.5, 0.5)
                s = rng.uniform(0.26, 0.32)
                card(m, p + np.array([0, H * 0.72, 0]), a, math.radians(rng.uniform(15, 35)), s, s,
                     A.uv("rice_panicle_a" if k == 0 else "rice_panicle_b"),
                     state_tint(GOLD, state, dry_to=[0.95, 0.85, 0.6], dead_to=[0.7, 0.62, 0.5]),
                     sway=(0.8, 1.0), back_offset=0.04)
    ambient(m, 0.6, floor=0.65)
    auto_sway(m, 0.95, seed=1)


def seedling(m, state):
    rng = np.random.default_rng(22)
    tuft = "rice_tuft_b" if state != "dead" else "rice_tuft_dry"
    for i, (x, z) in enumerate(GRID):
        p = np.array([x + rng.uniform(-0.02, 0.02), 0.0, z + rng.uniform(-0.02, 0.02)])
        H = rng.uniform(0.48, 0.56) * (0.7 if state == "dead" else 1.0)
        hill(m, rng, p, H, 0.24, tuft, col(rng, YOUNG, state), rng.uniform(0, math.pi))
    ambient(m, 0.4, floor=0.7)
    auto_sway(m, 0.6, seed=2)


p = Plant(ID, kind="Crops", script_dir=HERE)
p.stage("Seedling", seedling)
p.stage("Mature", mature)
p.extra = {
    "basis": "Cattail",
    "blockHeight": 2,
    "water": "stands on the paddy floor; designed for 0.3 deep water (Paddy Spout), readable up to 1.0",
    "randomizer": {"ConstrainProportion": True, "MinHeightScaleFactor": 0.95, "MaxHeightScaleFactor": 1.05,
                   "MinWidthScaleFactor": 1.0, "MaxWidthScaleFactor": 1.0, "RandomizedRotation": "By90Degree",
                   "MinRotation": 0.0, "MaxRotation": 360.0},
    "colliders": {"Seedling": {"box": {"center": [0.5, 0.25, 0.5], "size": [1.0, 0.5, 1.0]}},
                  "Mature": {"box": {"center": [0.5, 0.45, 0.5], "size": [1.0, 0.9, 1.0]}}},
}
if __name__ == "__main__":
    p.build()
