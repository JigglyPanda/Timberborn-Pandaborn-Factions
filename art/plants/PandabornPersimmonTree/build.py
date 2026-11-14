"""Persimmon tree: an orchard tree with a dark, blocky trunk, a rounded open crown of broad glossy leaves, and orange
fruit hanging on the outside of the crown when there is a harvest to gather.

Blueprint basis ChestnutTree (1x1x3, Forester, gathered for persimmons, cut for logs). The fruit are cards whose
albedo is the blank texel and whose detail (uv2) is a persimmon sprite: invisible until the gatherable has its yield
(GatherableModel sets _EnableDetail on the Mature renderers), exactly like vanilla chestnuts and blueberries.
    E:\\PandabornDev\\tools\\venv\\Scripts\\python.exe -I art/plants/PandabornPersimmonTree/build.py
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "src", "pipeline", "plants"))
import atlas as A  # noqa: E402
from plant import Plant, card, stem, state_tint, jitter, ambient, auto_sway, upright, shingle  # noqa: E402

ID = "PandabornPersimmonTree"
LEAF = np.array([0.22, 0.33, 0.11])
LEAF_LIGHT = np.array([0.28, 0.40, 0.13])
BARK = np.array([0.92, 0.9, 0.88])
C = np.array([0.5, 0.0, 0.5])
BLANK = (A.BLANK_UV[0], A.BLANK_UV[1], A.BLANK_UV[0] + 0.001, A.BLANK_UV[1] + 0.001)
LEAVES = ["persimmon_leaves_a", "persimmon_leaves_b", "persimmon_leaves_c"]


def leaf_colour(rng, state, light=False):
    c = jitter(rng, LEAF_LIGHT if light else LEAF, 0.1, 0.05)
    return state_tint(c, state, dry_to=jitter(rng, [0.60, 0.50, 0.22], 0.08), dead_to=jitter(rng, [0.45, 0.36, 0.26], 0.05))


def trunk(m, rng, state, H, r, limbs):
    """A short dark trunk forking into limbs that spread wide and up at different heights: the open, irregular frame
    that stays visible between the leaf lobes."""
    bark = state_tint(BARK, state, dry_to=[0.95, 0.9, 0.85], dead_to=[0.85, 0.82, 0.8])
    top = C + np.array([0.04, H, -0.03])
    stem(m, C, top, r, r * 0.75, A.uv("bark"), bark, sides=6, segments=2, bend=(0.015, 0, 0.01), v_range=(0.0, H / 1.4))
    ends = []
    for k in range(limbs):
        a = 2 * math.pi * (k + rng.uniform(-0.2, 0.2)) / limbs
        reach = rng.uniform(0.32, 0.48)
        rise = rng.uniform(0.38, 0.72)
        end = top + np.array([math.cos(a) * reach, rise, math.sin(a) * reach])
        stem(m, top, end, r * 0.6, r * 0.28, A.uv("bark"), bark, sides=4, segments=1,
             bend=(0, 0.06, 0), v_range=(0.3, 0.6))
        ends.append((end, a))
    return top, ends


def lobe(m, rng, state, centre, radii, fruit, light):
    """One leaf lobe at a limb end: shingled puffs over a small ellipsoid; fruit cards on its top and upper outer side
    (where the game camera sees them), lying nearly flat so the persimmons face up."""
    cards = []
    for phi, k in ((0.12, 2), (0.65, 5), (1.2, 6)):
        for j in range(k):
            cards.append((phi + rng.uniform(-0.12, 0.12), 2 * math.pi * (j + rng.uniform(-0.3, 0.3)) / k + phi * 2))
    cards.sort(key=lambda c: -c[0])
    for phi, th in cards:
        size = radii[0] * rng.uniform(1.05, 1.3)
        spr = LEAVES[0] if rng.random() < 0.6 else LEAVES[int(rng.integers(1, 3))]
        shingle(m, centre, radii, phi, th, size, size, A.uv(spr), leaf_colour(rng, state, light=light and phi < 0.7),
                inset=0.45, sway=(0.6, 1.0))
    if fruit:
        for k in range(6):
            phi = rng.uniform(0.15, 1.05)
            th = 2 * math.pi * (k + rng.uniform(-0.25, 0.25)) / 6
            spr = ["persimmon_fruit_a", "persimmon_fruit_b", "persimmon_fruit_c"][k % 3]
            s = rng.uniform(0.34, 0.42) * (0.75 if spr == "persimmon_fruit_c" else 1.0)
            shingle(m, centre, (radii[0] * 1.06, radii[1] * 1.12, radii[2] * 1.06), phi, th, s, s, BLANK, [1, 1, 1],
                    uv2=A.duv(spr), inset=0.2, droop=0.15, lift_normal=0.6, sway=(0.7, 0.9))


def mature(m, state):
    rng = np.random.default_rng(5)
    top, ends = trunk(m, rng, state, 1.0, 0.09, 4)
    if state == "dead":
        for end, a in ends:
            upright(m, end - np.array([0, 0.25, 0]), a + math.pi / 2, 0.6, 0.6, A.uv("persimmon_branch"),
                    [0.9, 0.88, 0.85], two_sided=True)
    else:
        # dark twigs showing through the gaps between the lobes
        upright(m, top + np.array([0, 0.05, 0]), rng.uniform(0, 3), 0.85, 0.8, A.uv("persimmon_branch"),
                [0.9, 0.88, 0.85], two_sided=True)
        for i, (end, a) in enumerate(ends):
            rr = rng.uniform(0.27, 0.33)
            lobe(m, rng, state, end + np.array([0, 0.1, 0]), (rr, rr * 0.72, rr), fruit=state == "alive", light=i % 2 == 0)
    ambient(m, 1.5, floor=0.5)
    auto_sway(m, 2.1, seed=1)


def seedling(m, state):
    """A sapling: a thin dark stem forking into three twigs, each with a few broad leaves."""
    rng = np.random.default_rng(9)
    bark = state_tint(BARK, state, dry_to=[0.95, 0.9, 0.85], dead_to=[0.85, 0.82, 0.8])
    fork = C + np.array([0.01, 0.38, 0.0])
    stem(m, C, fork, 0.032, 0.022, A.uv("bark"), bark, sides=5, segments=1, v_range=(0.0, 0.3))
    for k in range(3):
        a = 2 * math.pi * k / 3 + rng.uniform(-0.3, 0.3)
        tip = fork + np.array([math.cos(a) * 0.14, rng.uniform(0.2, 0.3), math.sin(a) * 0.14])
        stem(m, fork, tip, 0.016, 0.007, A.uv("bark"), bark, sides=4, segments=1, v_range=(0.3, 0.5))
        if state == "dead":
            continue
        for j in range(3):
            th = a + (j - 1) * 0.9 + rng.uniform(-0.2, 0.2)
            s = rng.uniform(0.2, 0.26)
            card(m, tip - np.array([0, 0.05 * j, 0]), th, rng.uniform(-0.35, 0.2), s, s,
                 A.uv(LEAVES[int(rng.integers(1, 3))]), leaf_colour(rng, state, light=j == 0), back_offset=0.03,
                 sway=(0.5, 1.0))
    if state == "dead":
        upright(m, fork - np.array([0, 0.1, 0]), 0.4, 0.45, 0.4, A.uv("persimmon_branch"), [0.9, 0.88, 0.85])
    ambient(m, 0.6, floor=0.6)
    auto_sway(m, 0.8, seed=2)


def stump(m, state):
    stem(m, C, C + np.array([0, 0.24, 0]), 0.095, 0.088, A.uv("bark"), [0.9, 0.88, 0.86], sides=7, segments=1,
         v_range=(0.0, 0.2), cap=A.disc("persimmon_discs", 0))
    ambient(m, 0.3, floor=0.7)
    auto_sway(m, 3.0, seed=3)


p = Plant(ID, kind="Trees", script_dir=HERE)
p.stage("Seedling", seedling)
p.stage("Mature", mature)
p.stump(stump)
p.extra = {
    "basis": "ChestnutTree",
    "gatherableDetail": "24 persimmon cards on the tops of the four leaf lobes (detail sheet persimmon_fruit_*), shown while the tree has fruit",
    "blockHeight": 3,
    "treeCuttingRadius": 0.145,
    "randomizer": {"ConstrainProportion": True, "MinHeightScaleFactor": 0.9, "MaxHeightScaleFactor": 1.1,
                   "MinWidthScaleFactor": 0.9, "MaxWidthScaleFactor": 1.1, "RandomizedRotation": "BetweenMinAndMax",
                   "MinRotation": 0.0, "MaxRotation": 360.0},
    "colliders": {"Seedling": {"capsule": {"center": [0.5, 0.3, 0.5], "radius": 0.2, "height": 0.7}},
                  "Mature": {"capsule": {"center": [0.5, 1.4, 0.5], "radius": 0.6, "height": 1.4}},
                  "Mature/#Dead": {"capsule": {"center": [0.5, 0.75, 0.5], "radius": 0.22, "height": 1.6}},
                  "#Leftover": {"capsule": {"center": [0.5, 0.12, 0.5], "radius": 0.12, "height": 0.3}}},
}
if __name__ == "__main__":
    p.build()
