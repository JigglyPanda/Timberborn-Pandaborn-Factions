"""Flowering shoot bamboo: the twin a grown shoot bamboo becomes in a Great Flowering (docs/tech/events.md). The same
low clump, culms and leaves yellowing, no new shoots, and over it pale straw-gold plumes of seed heads arching out and
hanging from every culm top, so a flowering field reads as a pale, feathery straw carpet from the game camera.
#Dying: straw culms, tan plumes; #Dead: bleached stalks slumped on dry soil, grey plumes, withered leaves.

Blueprint: the catalogue's PandabornShootBambooInFlower (basis Carrot, no planting tool). A twin is spawned grown; the
Seedling stage is the ordinary shoot bamboo's (never seen). Harvested (cut) for bamboo seed like the shoots.
    E:\\PandabornDev\\tools\\venv\\Scripts\\python.exe -I art/plants/PandabornShootBambooInFlower/build.py
"""
import importlib.util
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "src", "pipeline", "plants"))
import atlas as A  # noqa: E402
from plant import Plant, card, jitter, ambient, auto_sway  # noqa: E402

_spec = importlib.util.spec_from_file_location("shoot_bamboo", os.path.join(HERE, "..", "PandabornShootBamboo", "build.py"))
SB = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(SB)

ID = "PandabornShootBambooInFlower"
PLUMES = ["bamboo_flower_a", "bamboo_flower_b"]


def culm(rng, state):
    if state == "dead":
        return jitter(rng, [0.84, 0.82, 0.76], 0.05, 0.02)
    if state == "dry":
        return jitter(rng, [0.84, 0.74, 0.44], 0.05, 0.03)
    return jitter(rng, [0.66, 0.70, 0.34], 0.06, 0.04)


def leaf(rng, state):
    if state == "dead":
        return jitter(rng, [0.56, 0.48, 0.34], 0.05, 0.03)
    if state == "dry":
        return jitter(rng, [0.66, 0.54, 0.26], 0.08, 0.05)
    return jitter(rng, [0.54, 0.56, 0.22] if rng.random() < 0.6 else [0.42, 0.50, 0.19], 0.08, 0.05)


def plume(m, rng, state, top, a, H):
    """Three plumes per culm top, arching out all round and hanging."""
    tint = {"alive": [1.0, 0.98, 0.92], "dry": [0.86, 0.74, 0.54], "dead": [0.72, 0.69, 0.62]}[state]
    for k in range(3):
        s = rng.uniform(0.38, 0.46) * (0.8 if state == "dead" else 1.0)
        az = a + (k - 1) * 2.1 + rng.uniform(-0.4, 0.4)
        card(m, top, az, rng.uniform(-0.25, 0.3) - (0.5 if state == "dead" else 0.0), s, s,
             A.uv(PLUMES[int(rng.integers(0, 2))]), jitter(rng, tint, 0.04, 0.02), sway=(0.8, 1.0), back_offset=0.02)


LOOK = {"culm": culm, "leaf": leaf, "plume": plume}


def mature(m, state):
    rng = np.random.default_rng(4)
    SB.clump(m, rng, state, culms=5, h_range=(0.5, 0.68), leaves=2, shoots=0, shoot_size=0.3, look=LOOK)
    ambient(m, 0.45, floor=0.55)
    auto_sway(m, 0.75, seed=1)


p = Plant(ID, kind="Crops", material="PandabornShootBamboo", script_dir=HERE)
p.stage("Seedling", SB.seedling)
p.stage("Mature", mature)
p.extra = {
    "basis": "Carrot",
    "blockHeight": 1,
    "randomizer": SB.p.extra["randomizer"],
    "colliders": SB.p.extra["colliders"],
}
if __name__ == "__main__":
    p.build()
