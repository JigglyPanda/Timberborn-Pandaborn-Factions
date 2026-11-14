"""Flowering timber bamboo: the twin a grown timber bamboo becomes in a Great Flowering (docs/tech/events.md). The same
clump of culms, turning yellow, with pale straw-gold plumes of seed heads hanging from every spray and from the tops;
the leaves thin and yellow. It dies standing: #Dying = straw culms, tan plumes, brown leaves; #Dead = bleached
silver-white culms, no leaves, a few grey plumes still hanging. Cut for bamboo seed, it leaves the bamboo's stump.

Blueprint: the catalogue's PandabornTimberBambooInFlower (basis ChestnutTree, no planting, no reproduction, no
gatherable). A twin is spawned grown; the Seedling stage is the ordinary bamboo's (it is never seen).
    E:\\PandabornDev\\tools\\venv\\Scripts\\python.exe -I art/plants/PandabornTimberBambooInFlower/build.py
"""
import importlib.util
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "src", "pipeline", "plants"))
import atlas as A  # noqa: E402
from plant import Plant, card, jitter, ambient, auto_sway  # noqa: E402

_spec = importlib.util.spec_from_file_location("timber_bamboo", os.path.join(HERE, "..", "PandabornTimberBamboo", "build.py"))
TB = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(TB)

ID = "PandabornTimberBambooInFlower"
PLUMES = ["bamboo_flower_a", "bamboo_flower_b"]


def culm(rng, state, old=False):
    if state == "dead":
        return jitter(rng, [0.88, 0.87, 0.82], 0.05, 0.02)          # bleached
    if state == "dry":
        return jitter(rng, [0.84, 0.74, 0.44], 0.05, 0.03)          # straw
    return jitter(rng, [0.74, 0.74, 0.38] if old else [0.64, 0.70, 0.34], 0.06, 0.04)   # yellowing green


def leaf(rng, state):
    if state == "dry":
        return jitter(rng, [0.64, 0.52, 0.26], 0.08, 0.05)
    return jitter(rng, [0.52, 0.54, 0.21] if rng.random() < 0.6 else [0.40, 0.47, 0.18], 0.08, 0.05)


def plume(m, rng, state, p, az, size, f):
    """Seed heads hanging from a spray or the culm top: a drooping card with the flower sprite."""
    if state == "dead" and rng.random() < 0.5:
        return
    tint = {"alive": [1.0, 0.98, 0.92], "dry": [0.86, 0.74, 0.54], "dead": [0.74, 0.71, 0.64]}[state]
    s = size * rng.uniform(0.8, 1.0)
    card(m, p, az, rng.uniform(-0.45, 0.15), s, s, A.uv(PLUMES[int(rng.integers(0, 2))]), jitter(rng, tint, 0.04, 0.02),
         sway=(0.7, 1.0), back_offset=s * 0.05)


LOOK = {"culm": culm, "leaf": leaf, "plume": plume,
        "sprays": lambda st: {"alive": 4, "dry": 3, "dead": 3}[st], "leaves": lambda st: st != "dead"}


def mature(m, state):
    rng = np.random.default_rng(7)
    TB.clump(m, rng, state, n=6, h_range=(2.35, 2.95), r_range=(0.036, 0.05), spread=0.2, sprays_per=4, spray_size=0.62,
             look=LOOK)
    ambient(m, 1.6, floor=0.6)
    auto_sway(m, 2.9, seed=1)


p = Plant(ID, kind="Trees", material="PandabornTimberBamboo", script_dir=HERE)
p.stage("Seedling", TB.seedling)
p.stage("Mature", mature)
p.stump(TB.stump)
p.extra = {
    "basis": "ChestnutTree",
    "blockHeight": 3,
    "treeCuttingRadius": 0.22,
    "randomizer": TB.p.extra["randomizer"],
    "colliders": TB.p.extra["colliders"],
}
if __name__ == "__main__":
    p.build()
