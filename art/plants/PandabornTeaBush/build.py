"""Tea bush: a clipped, rounded mound of small dark glossy leaves with a flat plucking table on top. Planted in rows the
mounds touch and read as the hedgerows of a tea garden. When there are leaves to pick, bright yellow-green young
tips (two leaves and a bud) show across the top (detail sheet, like vanilla blueberries).

Blueprint basis BlueberryBush (1x1x1, gathered), planted by the Farmhouse, arid (dies on wet roots).
Recommended randomizer: rotation by 90 degrees and scale 0.95..1.05, so rows stay even.
    E:\\PandabornDev\\tools\\venv\\Scripts\\python.exe -I art/plants/PandabornTeaBush/build.py
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "src", "pipeline", "plants"))
import atlas as A  # noqa: E402
from plant import Plant, card, stem, state_tint, jitter, ambient, auto_sway, crossed  # noqa: E402

ID = "PandabornTeaBush"
LEAF = np.array([0.24, 0.36, 0.15])
TOP = np.array([0.30, 0.42, 0.17])
C = np.array([0.5, 0.0, 0.5])


def col(rng, base, state):
    return state_tint(jitter(rng, base, 0.08, 0.05), state, dry_to=jitter(rng, [0.55, 0.47, 0.22], 0.06),
                      dead_to=jitter(rng, [0.42, 0.33, 0.24], 0.05))


def table(m, rng, state, y, half, uv, uv2, colour):
    """The clipped top: a 3x3 grid slightly domed, edges rolled down."""
    n = 3
    u0, v0, u1, v1 = uv
    for i in range(n):
        for j in range(n):
            xs = [-half + 2 * half * (i + a) / n for a in (0, 1)]
            zs = [-half + 2 * half * (j + b) / n for b in (0, 1)]
            corners = []
            for (xx, zz) in ((xs[0], zs[0]), (xs[1], zs[0]), (xs[1], zs[1]), (xs[0], zs[1])):
                r = max(abs(xx), abs(zz)) / half
                corners.append(C + np.array([xx, y - 0.06 * r ** 2 + rng.uniform(-0.01, 0.01), zz]))
            uvq = (u0 + (u1 - u0) * i / n, v0 + (v1 - v0) * j / n, u0 + (u1 - u0) * (i + 1) / n, v0 + (v1 - v0) * (j + 1) / n)
            uv2q = None
            if uv2 is not None:
                a0, b0, a1, b1 = uv2
                uv2q = (a0 + (a1 - a0) * i / n, b0 + (b1 - b0) * j / n, a0 + (a1 - a0) * (i + 1) / n, b0 + (b1 - b0) * (j + 1) / n)
            m.quad(corners, uvq, normal=(0, 1, 0), sway=(0.8, 0.8, 0.9, 0.9), uv2=uv2q, color=colour, bend=0.25)


def mature(m, state):
    rng = np.random.default_rng(3)
    H, R = 0.5, 0.47
    ripe = state == "alive"
    # lower skirt: leaf masses leaning out
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8 + rng.uniform(-0.1, 0.1)
        p = C + np.array([math.cos(a) * R * 0.45, 0.02, math.sin(a) * R * 0.45])
        card(m, p, a, math.radians(rng.uniform(58, 66)), H * 0.95, 0.52, A.uv("tea_leaves"), col(rng, LEAF, state),
             back_offset=0.0, sway=(0.0, 0.7))
    # shoulders: the upper ring, tilted further over, carrying the young tips
    for k in range(8):
        a = 2 * math.pi * k / 8 + rng.uniform(-0.1, 0.1)
        p = C + np.array([math.cos(a) * R * 0.5, H * 0.66, math.sin(a) * R * 0.5])
        card(m, p, a, math.radians(rng.uniform(22, 32)), 0.3, 0.5, A.sub(A.uv("tea_leaves"), 0, 0.5, 1, 1),
             col(rng, TOP, state), uv2=A.sub(A.duv("tea_flush"), 0, 0.5, 1, 1) if ripe else None, back_offset=0.1,
             sway=(0.7, 0.9))
    table(m, rng, state, H, R * 0.62, A.uv("tea_top"), A.duv("tea_flush_top") if ripe else None, col(rng, TOP, state))
    ambient(m, H, floor=0.5, power=0.8)
    auto_sway(m, 0.6, seed=1)


def seedling(m, state):
    rng = np.random.default_rng(8)
    stem(m, C, C + np.array([0, 0.18, 0]), 0.012, 0.008, A.uv("culm_thin"), [0.5, 0.42, 0.32], sides=4, segments=1)
    for k in range(5):
        a = 2 * math.pi * k / 5 + rng.uniform(-0.2, 0.2)
        p = C + np.array([0, 0.08 + 0.03 * k, 0])
        card(m, p, a, math.radians(rng.uniform(30, 55)), 0.22, 0.2, A.uv("tea_leaves"), col(rng, LEAF, state),
             back_offset=0.03, sway=(0.3, 0.9))
    if state != "dead":
        crossed(m, C, rng.uniform(0, 3), 0.26, 0.2, A.uv("seedling_sprig"), col(rng, TOP, state))
    ambient(m, 0.3, floor=0.6)
    auto_sway(m, 0.4, seed=2)


p = Plant(ID, kind="Bushes", script_dir=HERE)
p.stage("Seedling", seedling)
p.stage("Mature", mature)
p.extra = {
    "basis": "BlueberryBush",
    "gatherableDetail": "young tips on the clipped top and upper ring (detail sheet tea_flush*), shown while there is tea to pick",
    "blockHeight": 1,
    "randomizer": {"ConstrainProportion": False, "MinHeightScaleFactor": 0.95, "MaxHeightScaleFactor": 1.05,
                   "MinWidthScaleFactor": 0.95, "MaxWidthScaleFactor": 1.05, "RandomizedRotation": "By90Degree",
                   "MinRotation": 0.0, "MaxRotation": 360.0},
    "colliders": "keep the basis's (BlueberryBush has none)",
}
if __name__ == "__main__":
    p.build()
