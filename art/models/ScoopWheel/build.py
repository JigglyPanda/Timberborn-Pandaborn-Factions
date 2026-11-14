"""Scoop Wheel: a tall bamboo wheel standing in a current, lifting water two levels with tube buckets, no workers.

Footprint as the water prototype's noria (1x3x3): the wheel column (0, 0, 0..2) stands in the river with the
current along +x; (0, 1) is the bank lip (left free for terrain); the outlet cell is (0, 2, 2), where the trough
pours into the basin. The wheel turns with the current: node '#WheelAnimated', one turn per 100 frames, its speed set
by the vanilla WaterPoweredGeneratorAnimator from the measured flow (stops when the current does).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, block  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("ScoopWheel", size=(1, 3, 3), seed=61, stand_in="WaterWheel.Folktails", overhang=0.8)
g = m.geo
C = np.array([0.5, 1.42, 0.5])
RAD = 1.22
WID = 0.34

with g.node("#WheelAnimated"):
    K.wheel(g, C, (0, 0, 1), RAD, width=WID, spokes=8, rim_r=0.045, material=BAMBOO_GOLD, buckets=8,
            bucket_material=BAMBOO_GREEN, paddles=8, paddle_depth=0.34)

# static A-frames either side of the wheel carrying the axle, feet in the riverbed
with g.tagged("frame"):
    for z in (0.06, 0.94):
        for sx in (-1, 1):
            K.beam(g, (0.5 + sx * 0.66, -0.05, z), (0.5 + sx * 0.06, C[1] + 0.12, z), w=0.09, caps="end")
        K.beam(g, (0.5 - 0.55, 0.45, z), (0.5 + 0.55, 0.45, z), w=0.07)
        K.beam(g, (0.5 - 0.35, 0.95, z), (0.5 + 0.35, 0.95, z), w=0.06)
        K.lashing(g, (0.5, C[1] + 0.02, z), (0, 0, 1), r=0.07)
    K.tube(g, [(0.5, C[1], -0.06), (0.5, C[1], 1.06)], [0.045, 0.045], TIMBER, sides=6)
    # the near frame rises to carry the catch basin beside the top of the wheel
    for x in (0.2, 0.8):
        K.pole(g, (x, -0.05, 0.98), (x, 2.42, 0.98), r=0.035, material=BAMBOO_GOLD, sides=5, bend=0.008)
    K.lashing(g, (0.2, 1.9, 0.98), (0, 1, 0), r=0.05)
    K.lashing(g, (0.8, 1.9, 0.98), (0, 1, 0), r=0.05)

# catch basin beside the wheel's crown, and the trough down to the outlet over the basin at (0, 2, 2)
K.box(g, (0.18, 2.3, 0.72), (0.82, 2.44, 1.02), TIMBER, WOOD_STRIPS[2], skip=(2,))
K.channel(g, 0.98, 2.62, 2.18, 0.5, r_in=0.13, wall=0.03, material=BAMBOO_GREEN, around=5, sleeve=False, tilt=0.16)
K.tube(g, [(0.5, 2.26, 2.62), (0.5, 2.22, 2.72)], [0.06, 0.05], BAMBOO_GREEN, sides=6, caps=False)
for x in (0.38, 0.62):
    K.pole(g, (x, 1.98, 2.55), (x, 2.24, 2.55), r=0.022, material=BAMBOO_GOLD, sides=4, bend=0.0)
K.pole(g, (0.3, 2.22, 2.55), (0.7, 2.22, 2.55), r=0.018, material=BAMBOO_GOLD, sides=4, bend=0.0)
# a rope stay from the top of the frame back to a stake on the bank
K.beam(g, (0.5, 2.38, 0.98), (0.5, 1.02, 1.85), w=0.012, material=DETAILS, caps=False)
K.pole(g, (0.5, 0.92, 1.85), (0.5, 1.12, 1.88), r=0.02, material=TIMBER, sides=4, bend=0.0)

m.animate("#WheelAnimated", C, (0, 0, 1), driver="WaterPoweredGeneratorAnimator (WaterPoweredGeneratorSpec)")
cells = {(0, 0, z): block("Any" if z else "GroundOrStackable", "Corners, Middle") for z in range(3)}
cells[(0, 2, 2)] = block("Any", "Corners, Middle")
m.blocks = [cells.get((x, y, z), block("Any", "None")) for z in range(3) for y in range(3) for x in range(1)]
m.extra["waterOutput"] = {"X": 0, "Y": 2, "Z": 2}
m.extra["waterInput"] = {"X": 0, "Y": 0, "Z": 0}
m.extra["expectedWaterDirection"] = {"X": 1.0, "Y": 0.0}
m.stage_height = 1.5
m.collider((0.5, 1.42, 0.5), (2.4, 2.6, 0.5))
m.collider((0.5, 2.35, 1.7), (0.6, 0.3, 2.0))
m.notes += ["The wheel overhangs the footprint by about 0.75 tile up- and downstream (it stands in the river).",
            "Animation: '#WheelAnimated' turns about +z through the axle; bottom moves with the current (+x)."]
m.build()
