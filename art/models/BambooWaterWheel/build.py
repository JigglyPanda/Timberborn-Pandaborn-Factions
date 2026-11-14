"""Bamboo Water Wheel: water power. 3x2 with the vanilla Water Wheel's blocks, generator cells and shaft ends.

A broad bamboo undershot wheel with woven paddles between twin rims, on an axle through two timber A-frames standing
on stone footings; the axle ends at both faces (the vanilla transputs at (1, 0, 1) and (1, 1, 1)) in iron-banded
hubs. The wheel is '#WheelAnimated', turned by the vanilla WaterPoweredGeneratorAnimator with the current.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("BambooWaterWheel", size=(3, 2, 3), seed=89, stand_in="WaterWheel.Folktails")
g = m.geo
C = np.array([1.5, 1.5, 1.0])
with g.node("#WheelAnimated"):
    K.wheel(g, C, (0, 0, 1), 1.38, width=1.25, spokes=8, rim_r=0.05, material=BAMBOO_GOLD, buckets=0,
            paddles=16, paddle_depth=0.5, paddle_material=WEAVE_GOLD)
    # a middle rim so the wide wheel does not read as two
    ring = [C + np.array([np.cos(a), np.sin(a), 0.0]) * 1.38 for a in np.linspace(0, 2 * np.pi, 15)]
    K.tube(g, ring, [0.04] * len(ring), BAMBOO_GREEN, sides=5, caps=False)
with g.tagged("frame"):
    for z in (0.08, 1.92):
        for sx in (-1, 1):
            K.beam(g, (1.5 + sx * 0.8, 0.0, z), (1.5 + sx * 0.06, C[1] + 0.1, z), w=0.1, caps="end")
        K.beam(g, (0.6, 0.55, z), (2.4, 0.55, z), w=0.08)
        K.box(g, (1.25, 0.0, z - 0.12), (1.75, 0.18, z + 0.12), PLASTER, (0.1, 0.1, 0.9, 0.9), tags={"stone"})
        g.parts[-1].C = np.tile([0.6, 0.6, 0.58, 1.0], (len(g.parts[-1].P), 1))
    K.tube(g, [(1.5, C[1], -0.02), (1.5, C[1], 2.02)], [0.07, 0.07], TIMBER, sides=8)
for z, dz in ((0.0, 0.08), (2.0, -0.08)):
    K.lathe(g, [(0.0, 0.0), (0.13, 0.0), (0.13, 0.1), (0.0, 0.1)], (1.5, C[1], z + (0.0 if dz > 0 else -0.1)), 8,
            BANDED, axis=(0, 0, 1), uv_region=(0.03, 0.05, 0.08, 0.95))
K.lantern(g, (2.32, 0.52, 0.0), r=0.06, h=0.13)
m.animate("#WheelAnimated", C, (0, 0, 1), driver="WaterPoweredGeneratorAnimator (WaterPoweredGeneratorSpec)")
m.stage_height = 1.6
m.collider((1.5, 1.2, 1.0), (2.2, 2.4, 1.4))
m.notes += ["Blocks, generator cells, transputs and the water object as the vanilla Water Wheel (3x2x3)."]
m.build()
