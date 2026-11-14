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
from plant import Plant, card, stem, state_tint, jitter, ambient, auto_sway, crossed, shingle  # noqa: E402

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
    H, R = 0.5, 0.48
    ripe = state == "alive"
    dome = (C + np.array([0, 0.06, 0]), (R, H - 0.06, R))
    # sides: two rings of leaf masses laid like tiles down a squat dome, lower ring first
    for ring, (phi, n, size) in enumerate(((1.45, 9, 0.3), (1.12, 9, 0.36), (0.72, 8, 0.32))):
        for k in range(n):
            th = 2 * math.pi * (k + 0.5 * ring) / n + rng.uniform(-0.12, 0.12)
            shingle(m, dome[0], dome[1], phi + rng.uniform(-0.08, 0.08), th, size, size * 1.15, A.uv("tea_leaves"),
                    col(rng, LEAF if ring < 2 else TOP, state),
                    uv2=A.duv("tea_flush") if (ripe and ring == 2) else None, inset=0.35, sway=(0.2 + 0.3 * ring, 0.8))
    table(m, rng, state, H, R * 0.6, A.uv("tea_top"), A.duv("tea_flush_top") if ripe else None, col(rng, TOP, state))
    ambient(m, H, floor=0.5, power=0.8)
    auto_sway(m, 0.6, seed=1)


def seedling(m, state):
    rng = np.random.default_rng(8)
    stem(m, C, C + np.array([0, 0.18, 0]), 0.012, 0.008, A.uv("culm_thin"), [0.5, 0.42, 0.32], sides=4, segments=1)
    for k in range(6):
        th = 2 * math.pi * k / 6 + rng.uniform(-0.2, 0.2)
        shingle(m, C + np.array([0, 0.04, 0]), (0.2, 0.24, 0.2), rng.uniform(0.5, 1.1), th, 0.26, 0.26,
                A.uv("tea_leaves"), col(rng, LEAF, state), inset=0.4)
    if state != "dead":
        crossed(m, C, rng.uniform(0, 3), 0.28, 0.2, A.uv("seedling_sprig"), col(rng, TOP, state))
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
