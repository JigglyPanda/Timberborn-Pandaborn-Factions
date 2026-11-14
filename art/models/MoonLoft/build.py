"""Moon Loft: a snug home raised on stilts above a path, a lantern in its round window. Its first one invites the
Ringtails. 2x2x3: the ground layer is stilts at the cell corners only (Occupations 'Corners', as the vanilla
Double Platform's lower block), so a path can run underneath and colonists can walk under it; the house is the
second block, the roof the third. A bamboo ladder at the front reaches the entrance cell.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
from building import Model, block  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("MoonLoft", size=(2, 2, 3), seed=83, stand_in="Lodge.Folktails")
g = m.geo
FL = 1.02          # loft floor
TOP = 1.86
RIDGE = 2.5
X0, X1, Z0, Z1 = 0.22, 1.78, 0.36, 1.72

# stilts: four bamboo/timber legs at the outer corners, X braces on the two sides only, so the middle stays open
with g.tagged("frame"):
    for x in (0.1, 1.9):
        for z in (0.12, 1.88):
            K.pole(g, (x, 0.0, z), (x * 0.96 + 0.04, FL, z * 0.97 + 0.03), r=0.06, material=TIMBER, sides=6,
                   bend=0.01, taper=0.9)
    for x in (0.1, 1.9):
        K.pole(g, (x, 0.1, 0.16), (x, FL - 0.1, 1.84), r=0.025, material=BAMBOO_GOLD, sides=4, bend=0.0, caps=False)
        K.pole(g, (x, FL - 0.1, 0.16), (x, 0.1, 1.84), r=0.025, material=BAMBOO_GOLD, sides=4, bend=0.0, caps=False)
    for z in (0.12, 1.88):
        K.beam(g, (0.0, FL - 0.05, z), (2.0, FL - 0.05, z), w=0.08)
# loft floor: boards on joists, a little balcony at the front
K.boards(g, (0.0, FL, 0.08), (1, 0, 0), (0, 0, 1), 2.0, 1.84, 5, TIMBER, thick=0.04)
for x in (0.05, 1.95):
    K.beam(g, (x, FL + 0.04, 0.1), (x, FL + 0.3, 0.1), w=0.04, caps="end")
K.beam(g, (0.03, FL + 0.28, 0.1), (0.85, FL + 0.28, 0.1), w=0.035)
K.beam(g, (1.15, FL + 0.28, 0.1), (1.97, FL + 0.28, 0.1), w=0.035)
# the house: timber frame and plaster; round moon window at the front with a red lantern in it; door to the balcony
with g.tagged("walls"):
    K.wall(g, (X0, Z0), (X1, Z0), FL + 0.03, TOP, openings=[("door", 0.72, 0.34, 0.0, 0.58)], rail=False)
    K.wall(g, (X1, Z0), (X1, Z1), FL + 0.03, TOP, openings=[("window", 0.5, 0.32, 0.3, 0.58)])
    K.wall(g, (X1, Z1), (X0, Z1), FL + 0.03, TOP, openings=[("window", 0.5, 0.32, 0.3, 0.58)])
    K.wall(g, (X0, Z1), (X0, Z0), FL + 0.03, TOP, openings=[("window", 0.5, 0.32, 0.3, 0.58)])
    K.gable_end(g, X0, Z0, Z1, TOP, RIDGE, outward=-1)
    K.gable_end(g, X1, Z0, Z1, TOP, RIDGE, outward=1)
# moon window: the round cracked-ice window, set in a white plaster disc with a dark ring
MW = (0.72, FL + 0.48, Z0 - 0.03)
K.lathe(g, [(0.0, 0.0), (0.3, 0.0)], (0, 0, 0), 12, PLASTER, uv_region=(0.1, 0.1, 0.9, 0.9), cap_top=False)
disc = g.parts[-1]
R = rot_axis((1, 0, 0), math.pi / 2)
disc.P = disc.P @ R.T + np.array(MW) + np.array([0, 0, -0.005])
disc.N = disc.N @ R.T
K.window(g, MW, (0, 0, -1), 0.36, 0.36, frame=0.035, region=WIN_ROUND, sill=False)
K.lantern(g, (MW[0], MW[1] + 0.12, MW[2] - 0.08), r=0.06, h=0.13)
K.roof(g, X0, Z0, X1, Z1, TOP, RIDGE, kind="gable", overhang=0.24, sag=0.08, lift=0.06, ridge_ends=0.08)
# ladder from the path up to the balcony gap
K.ladder(g, (1.0, 0.0, -0.22), (1.0, FL + 0.05, 0.08), width=0.3, rungs=6)
# a little crescent of red lanterns on a string under the side eave, a potted plant on the balcony
K.lantern_string(g, (X1 + 0.25, TOP - 0.05, 0.2), (X1 + 0.25, TOP - 0.05, 1.6), n=3, sag=0.12)
K.jar(g, (0.25, FL + 0.04, 0.22), h=0.16, r=0.08, lid=False)
for k in range(4):
    K.pole(g, (0.25, FL + 0.18, 0.22), (0.25 + 0.06 * np.cos(k * 1.6), FL + 0.45, 0.22 + 0.06 * np.sin(k * 1.6)),
           r=0.012, material=BAMBOO_GREEN, sides=3, bend=0.03, caps=False)

cells = []
for z in range(3):
    for y in range(2):
        for x in range(2):
            if z == 0:
                cells.append(block("GroundOrStackable", "Corners", "None"))
            else:
                cells.append(block("Any", "Bottom, Top, Corners, Path, Middle", "None"))
m.blocks = cells
m.entrance(1, -1, 0)
m.extra["access"] = {"X": 1.0, "Y": 0.0, "Z": -0.1}
m.extra["walkUnder"] = "ground layer Occupations 'Corners' only (vanilla DoublePlatform lower block); paths fit under"
m.stage_height = 1.9
m.collider((1.0, 1.45, 1.0), (1.9, 0.9, 1.6))
m.collider((1.0, 2.2, 1.0), (2.0, 0.6, 1.6))
m.notes += ["Colonists enter at the foot of the ladder (the access point), as vanilla buildings swallow them at the door.",
            "Windows (and the moon window) glow at night when someone is home (EnterableIlluminatorSpec)."]
m.build()
