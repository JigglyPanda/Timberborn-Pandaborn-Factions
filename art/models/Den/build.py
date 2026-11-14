"""Den: the Inkpaws' starter home (replaces the beaver dome lodge). 2x2 footprint, two blocks high, not stackable.

A small Sichuan farmhouse: rammed-earth plinth edged with river stones, dark timber frame with lime-plaster infill,
a grey tile gable roof with a gently sagging ridge, a lattice window either side, a plank door left ajar under a
red lantern, a bench and a pickle jar on the porch, bamboo poles leaning on the gable.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
from building import Model, solid_blocks  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("Den", size=(2, 2, 2), seed=11, stand_in="Lodge.Folktails")
g = m.geo

BASE = 0.12            # plinth top
WX0, WX1 = 0.18, 1.82  # walls
WZ0, WZ1 = 0.42, 1.78
TOP = 0.98             # wall plate
RIDGE = 1.68

K.plinth(g, 0.05, 0.08, 1.95, 1.92, h=BASE)

with g.tagged("walls"):
    # front: lattice window left, door right of centre (entrance cell x = 1)
    K.wall(g, (WX0, WZ0), (WX1, WZ0), BASE, TOP,
           openings=[("window", 0.26, 0.44, 0.2, 0.74), ("door", 0.71, 0.38, 0.0, 0.66)])   # big lattice: glows at night
    K.wall(g, (WX1, WZ0), (WX1, WZ1), BASE, TOP, openings=[("window", 0.5, 0.4, 0.26, 0.64)])
    K.wall(g, (WX1, WZ1), (WX0, WZ1), BASE, TOP, openings=[("panes", 0.35, 0.42, 0.42, 0.62)])
    K.wall(g, (WX0, WZ1), (WX0, WZ0), BASE, TOP, openings=[("window", 0.5, 0.34, 0.3, 0.6)], braces=True)
    K.gable_end(g, WX0, WZ0, WZ1, TOP, RIDGE, outward=-1)
    K.gable_end(g, WX1, WZ0, WZ1, TOP, RIDGE, outward=1)

# roof: ridge along x, generous front eave over the porch
K.roof(g, WX0, WZ0, WX1, WZ1, TOP, RIDGE, kind="gable", overhang=0.24, sag=0.08, lift=0.05, ridge_ends=0.08)
# porch posts carrying the front eave
for x in (0.24, 1.76):
    K.pole(g, (x, BASE, 0.2), (x, TOP - 0.17, 0.2), r=0.045, material=TIMBER, sides=6, bend=0.015, taper=0.92)
    K.beam(g, (x, TOP - 0.15, 0.2), (x, TOP - 0.04, WZ0), w=0.05)
K.beam(g, (0.1, TOP - 0.15, 0.2), (1.9, TOP - 0.15, 0.2), w=0.07, sag=0.015, segs=2)

# porch life: bench, pickle jar, basket, lantern by the door, bamboo leaning on the left gable
K.boards(g, (0.33, 0.33, 0.24), (1, 0, 0), (0, 0, 1), 0.5, 0.14, 2, TIMBER, thick=0.03)
for x in (0.37, 0.78):
    K.beam(g, (x, BASE, 0.31), (x, 0.32, 0.31), w=0.04)
K.jar(g, (1.86, BASE, 0.3), h=0.24, r=0.09)
K.basket(g, (0.62, BASE, 0.22), h=0.1, r=0.09)
K.lantern(g, (1.36, TOP - 0.1, 0.12), r=0.07, h=0.16)
K.chilli_string(g, (0.5, TOP - 0.1, 0.13), length=0.4)
K.chilli_string(g, (0.62, TOP - 0.1, 0.12), length=0.32, n=5)
for k, (z, lean) in enumerate(((0.62, 0.12), (0.8, 0.16), (1.05, 0.1))):
    K.pole(g, (0.03 - 0.02 * k, BASE, z), (WX0 - 0.05, 0.9 + 0.08 * k, z + lean), r=0.028,
           material=BAMBOO_GREEN if k != 1 else BAMBOO_GOLD, sides=5, bend=0.01)
# a woven screen against the right side, patched
K.panel(g, [(1.9, BASE, 1.15), (1.9, BASE, 0.62), (1.95, 0.55, 0.64), (1.95, 0.55, 1.17)], WEAVE_GOLD, both=True)
# little smoke flue at the back, lime-plastered
K.box(g, (1.32, 1.05, 1.62), (1.5, 1.86, 1.8), PLASTER, (0.1, 0.1, 0.9, 0.9))
K.box(g, (1.29, 1.86, 1.59), (1.53, 1.92, 1.83), TILE, (0.0, TILE_COURSES[0][0], 0.2, TILE_COURSES[0][1]))

m.blocks = solid_blocks(2, 2, 2)
m.entrance(1, -1, 0)
m.extra["access"] = {"X": 1.5, "Y": BASE, "Z": 0.7}
m.collider((1.0, 0.55, 1.1), (1.7, 1.1, 1.5))
m.collider((1.0, 1.35, 1.1), (1.9, 0.6, 1.4))
m.notes += ["Dwelling, 3 beds as the Lodge. Not stackable: the second block holds the roof.",
            "Windows glow at night when someone is inside (EnterableIlluminatorSpec)."]
m.build()
