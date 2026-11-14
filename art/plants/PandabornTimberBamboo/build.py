"""Timber bamboo: the Inkpaws' forest tree. A clump of tall, straight green culms with feathery leaf sprays in the upper
half, the tops arching out; bamboo fungus (white lace veils) at the culm bases when the grove has mushrooms to forage.

Blueprint basis ChestnutTree (1x1x3, Forester, cut for poles, gathered for mushrooms). Stages: Seedling (a young clump
with a fat shoot), Mature, their Dry and Dead variants, and the stump (cut culms with hollow tops).
    E:\\PandabornDev\\tools\\venv\\Scripts\\python.exe -I art/plants/PandabornTimberBamboo/build.py
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "src", "pipeline", "plants"))
import atlas as A  # noqa: E402
from plant import Plant, card, stem, state_tint, jitter, ambient, auto_sway, upright  # noqa: E402

ID = "PandabornTimberBamboo"
CULM = np.array([0.50, 0.68, 0.30])      # fresh culm (times the 0.86 culm strip)
CULM_OLD = np.array([0.58, 0.66, 0.32])
LEAF = np.array([0.34, 0.48, 0.17])
LEAF_OLD = np.array([0.25, 0.37, 0.13])       # leaf sprays (times ~0.82)
SPRAYS = ["bamboo_spray_a", "bamboo_spray_b", "bamboo_spray_c", "bamboo_spray_d", "bamboo_spray_e"]
C = (0.5, 0.0, 0.5)


def culm_colour(rng, state, old=False):
    base = CULM_OLD if old else CULM
    c = jitter(rng, base, 0.07, 0.05)
    return state_tint(c, state, dry_to=jitter(rng, [0.80, 0.72, 0.40], 0.05),
                      dead_to=jitter(rng, [0.66, 0.62, 0.52], 0.06))


def leaf_colour(rng, state):
    c = jitter(rng, LEAF if rng.random() > 0.35 else LEAF_OLD, 0.1, 0.06)
    return state_tint(c, state, dry_to=jitter(rng, [0.66, 0.58, 0.28], 0.08), dead_to=jitter(rng, [0.52, 0.45, 0.33], 0.06))


def clump(m, rng, state, n, h_range, r_range, spread, sprays_per, spray_size, broken=0, mushrooms=False, shoot=False):
    culm_uv = A.uv("culm")
    thin_uv = A.uv("culm_thin")
    angles = np.sort(rng.uniform(0, 2 * math.pi, n)) + rng.uniform(0, 1)
    for i in range(n):
        a = angles[i] + rng.uniform(-0.2, 0.2)
        rb = spread * math.sqrt(rng.uniform(0.15, 1.0))
        base = np.array([C[0] + math.cos(a) * rb, 0.0, C[2] + math.sin(a) * rb])
        H = rng.uniform(*h_range)
        r = rng.uniform(*r_range)
        lean = rng.uniform(0.08, 0.2) * H / 3
        top = base + np.array([math.cos(a) * lean, H, math.sin(a) * lean])
        is_broken = i < broken
        if is_broken:
            top = base + (top - base) * rng.uniform(0.35, 0.6)
        bow = np.array([math.cos(a), 0, math.sin(a)]) * (0.05 * H / 3)
        v0 = rng.uniform(0.0, 0.25)
        stem(m, base, top, r, r * 0.55, culm_uv if r > 0.025 else thin_uv, culm_colour(rng, state, old=i % 3 == 0),
             sides=5, segments=3, bend=bow, v_range=(v0, v0 + min(0.75, H / 3.2)))
        if is_broken:
            continue
        # leaf sprays along the upper half, fanning outward, lowest ones largest
        k = sprays_per if state != "dead" else max(1, sprays_per // 3)
        for j in range(k):
            f = 0.5 + 0.5 * (j + rng.uniform(0.2, 0.8)) / k
            p = base + (top - base) * f + bow * 4 * f * (1 - f)
            az = a + rng.uniform(-1.4, 1.4) + (math.pi if rng.random() < 0.25 else 0)
            size = spray_size * rng.uniform(0.75, 1.1) * (1.15 - 0.45 * (f - 0.5) * 2)
            spr = SPRAYS[int(rng.integers(0, 2 if size > 0.5 else 5))] if state != "dead" else "bamboo_dry"
            tilt = rng.uniform(-0.15, 0.45) if f < 0.92 else rng.uniform(0.45, 0.7)
            card(m, p, az, tilt, size, size, A.uv(spr), leaf_colour(rng, state), sway=(0.6 * f, 1.0),
                 back_offset=size * 0.08)
        # the arching top: a spray standing up off the tip
        if state != "dead":
            card(m, top, a + rng.uniform(-0.5, 0.5), rng.uniform(0.55, 0.75), spray_size * 0.8, spray_size * 0.7,
                 A.uv(SPRAYS[int(rng.integers(2, 5))]), leaf_colour(rng, state), sway=(0.9, 1.0), back_offset=0.05)
    if mushrooms:
        for k in range(3):
            a = rng.uniform(0, 2 * math.pi)
            p = np.array([C[0] + math.cos(a) * 0.36, 0.0, C[2] + math.sin(a) * 0.36])
            # invisible card (blank albedo) that shows bamboo fungus when the grove has mushrooms to gather
            upright(m, p, a + math.pi / 2, 0.24, 0.26, (A.BLANK_UV[0], A.BLANK_UV[1], A.BLANK_UV[0] + 0.001, A.BLANK_UV[1] + 0.001),
                    [1, 1, 1], uv2=A.duv("mushrooms" if k % 2 == 0 else "mushrooms_b"), two_sided=True)
    if shoot:
        a = rng.uniform(0, 2 * math.pi)
        p = np.array([C[0] + math.cos(a) * 0.18, 0.0, C[2] + math.sin(a) * 0.18])
        m.tube([p, p + np.array([0, 0.14, 0]), p + np.array([0.01, 0.26, 0])], [0.05, 0.035, 0.004], 5, A.uv("sheath"),
               sway=[0, 0.1, 0.2], color=state_tint([1, 1, 1], state, dry_to=[0.9, 0.8, 0.6], dead_to=[0.7, 0.65, 0.6]))


def mature(m, state):
    rng = np.random.default_rng(7)
    clump(m, rng, state, n=6, h_range=(2.35, 2.95), r_range=(0.036, 0.05), spread=0.2, sprays_per=4, spray_size=0.62,
          broken=2 if state == "dead" else 0, mushrooms=state == "alive")
    ambient(m, 1.6, floor=0.6)
    auto_sway(m, 2.9, seed=1)


def seedling(m, state):
    rng = np.random.default_rng(11)
    clump(m, rng, state, n=3, h_range=(0.6, 0.95), r_range=(0.016, 0.022), spread=0.12, sprays_per=2, spray_size=0.32,
          shoot=True)
    ambient(m, 0.5, floor=0.6)
    auto_sway(m, 1.0, seed=2)


def stump(m, state):
    rng = np.random.default_rng(7)
    angles = np.sort(rng.uniform(0, 2 * math.pi, 4)) + rng.uniform(0, 1)
    for i in range(4):
        a = angles[i]
        rb = 0.2 * math.sqrt(rng.uniform(0.15, 1.0))
        base = np.array([C[0] + math.cos(a) * rb, 0.0, C[2] + math.sin(a) * rb])
        r = rng.uniform(0.036, 0.05)
        h = rng.uniform(0.1, 0.26)
        stem(m, base, base + np.array([0, h, 0]), r, r * 0.97, A.uv("culm"),
             jitter(rng, [0.62, 0.66, 0.36], 0.06), sides=5, segments=1, v_range=(0.02, 0.02 + h / 3.2),
             cap=A.disc("culm_discs", 0))
    ambient(m, 0.3, floor=0.7)
    auto_sway(m, 3.0, seed=3)


p = Plant(ID, kind="Trees", script_dir=HERE)
p.stage("Seedling", seedling)
p.stage("Mature", mature)
p.stump(stump)
p.extra = {
    "basis": "ChestnutTree",
    "gatherableDetail": "bamboo fungus at the culm bases (detail sheet 'mushrooms'), shown while the grove has mushrooms",
    "blockHeight": 3,
    "treeCuttingRadius": 0.22,
    "randomizer": {"ConstrainProportion": True, "MinHeightScaleFactor": 0.9, "MaxHeightScaleFactor": 1.08,
                   "MinWidthScaleFactor": 0.9, "MaxWidthScaleFactor": 1.1, "RandomizedRotation": "BetweenMinAndMax",
                   "MinRotation": 0.0, "MaxRotation": 360.0},
    "colliders": {"Seedling": {"capsule": {"center": [0.5, 0.35, 0.5], "radius": 0.2, "height": 0.9}},
                  "Mature": {"capsule": {"center": [0.5, 1.3, 0.5], "radius": 0.28, "height": 2.7}},
                  "#Leftover": {"capsule": {"center": [0.5, 0.12, 0.5], "radius": 0.25, "height": 0.3}}},
}
if __name__ == "__main__":
    p.build()
