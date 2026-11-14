"""Terrace House: the stackable hillside home. 3x2x2 on the Triple Lodge's dwelling (nine beds); another Terrace
House (or a platform) can stand on its flat roof, as the vanilla lodges stack.

A Chongqing-hillside stack: a ground storey of river stone and rammed earth with a plank door, an upper storey of dark
timber frame and lime plaster with a lattice-windowed gallery behind a bamboo railing, and a flat beaten-earth roof
terrace (kept clear for stacking); herbs in pots on the gallery, a lantern, chillies; a lean-to of grey tile over the
gallery.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, block  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("TerraceHouse", size=(3, 2, 2), seed=137, stand_in="TripleLodge.Folktails")
g = m.geo
X0, X1, Z0, Z1 = 0.06, 2.94, 0.3, 1.94
# ground storey: stone and rammed earth
K.box(g, (X0, 0.0, Z0), (X1, 0.92, Z1), EARTH, (0.02, 0.02, 0.98, 0.98), skip=(3,), tags={"base"})
K.stones(g, X0 + 0.04, Z0 + 0.03, X1 - 0.04, Z1 - 0.03, y=-0.01, size=0.3, h=0.32, skip=0.05, tags={"base"})
K.door(g, (1.5, 0.0, Z0 - 0.005), (0, 0, -1), w=0.4, h=0.66)
for x in (0.55, 2.45):
    K.window(g, (x, 0.55, Z0 - 0.005), (0, 0, -1), 0.3, 0.26, region=WIN_PANES)
# upper storey: timber frame and plaster, set back behind a gallery
UZ0 = 0.62
with g.tagged("walls"):
    K.wall(g, (X0 + 0.04, UZ0), (X1 - 0.04, UZ0), 0.95, 1.86,
           openings=[("window", 0.18, 0.4, 0.22, 0.6), ("door", 0.5, 0.36, 0.0, 0.66), ("window", 0.82, 0.4, 0.22, 0.6)])
    K.wall(g, (X1 - 0.04, UZ0), (X1 - 0.04, Z1), 0.95, 1.86, openings=[("window", 0.5, 0.34, 0.25, 0.6)], rail=False)
    K.wall(g, (X1 - 0.04, Z1), (X0 + 0.04, Z1), 0.95, 1.86, rail=False)
    K.wall(g, (X0 + 0.04, Z1), (X0 + 0.04, UZ0), 0.95, 1.86, openings=[("window", 0.5, 0.34, 0.25, 0.6)], rail=False)
# the gallery floor over the front of the ground storey, its railing, and a tile lean-to above it
K.boards(g, (X0, 0.92, Z0 - 0.08), (1, 0, 0), (0, 0, 1), X1 - X0, UZ0 - Z0 + 0.08, 3, TIMBER, thick=0.04)
for k in range(9):
    x = X0 + 0.04 + (X1 - X0 - 0.08) * k / 8
    K.pole(g, (x, 0.95, Z0 - 0.04), (x, 1.28, Z0 - 0.04), r=0.018, material=BAMBOO_GOLD, sides=4, bend=0.0)
K.pole(g, (X0, 1.26, Z0 - 0.04), (X1, 1.26, Z0 - 0.04), r=0.022, material=BAMBOO_GOLD, sides=5, bend=0.0)
K.roof(g, X0 + 0.04, Z0 - 0.04, X1 - 0.04, UZ0, 1.5, 1.72, kind="lean", overhang=0.08, sag=0.02, lift=0.02, ridge=False,
       tile=0.3, course=0.3)
# flat roof terrace: beaten earth inside a low plaster parapet with a tile coping (stackable at y = 2)
K.box(g, (X0, 1.86, UZ0 - 0.02), (X1, 2.0, Z1), EARTH, (0.02, 0.02, 0.98, 0.98), skip=(3,))
# pots of herbs on the gallery corners (the roof stays clear: another house may stand on it)
for x in (X0 + 0.14, X1 - 0.14):
    K.lathe(g, [(0.0, 0.0), (0.1, 0.0), (0.12, 0.12)], (x, 0.96, Z0 + 0.02), 7, EARTH, cap_top=True)
    K.lathe(g, [(0.0, 0.0), (0.1, 0.05), (0.07, 0.14), (0.0, 0.18)], (x, 1.08, Z0 + 0.02), 5, MOSS)
# round drying mats on the roof, chillies and greens spread out to dry (flat: nothing stops a house stacking here)
for (x, z, rr, mat, reg, fill) in ((0.62, 1.2, 0.3, DETAILS, DET_RED, 0.5), (1.5, 1.42, 0.3, MOSS, None, 0.8),
                                   (2.3, 1.1, 0.36, DETAILS, DET_SACK, 0.8)):
    K.lathe(g, [(0.0, 0.0), (rr, 0.0), (rr + 0.02, 0.02)], (x, 2.0, z), 10, WEAVE_GOLD, cap_top=False)
    K.lathe(g, [(rr * fill, 0.012), (0.0, 0.012)], (x, 2.0, z), 8, mat, uv_region=reg or (0.1, 0.1, 0.9, 0.9),
            cap_top=False)
    lid = g.parts[-1]
    lid.N[:] = (0, 1, 0)
    lid.T = fix_winding(lid.P, lid.N, lid.T)
K.lantern(g, (2.86, 1.8, 0.46), r=0.06, h=0.14)
K.chilli_string(g, (0.3, 1.66, 0.36), length=0.3, n=5)
cells = []
for z in range(2):
    for y in range(2):
        for x in range(3):
            cells.append(block("GroundOrStackable" if z == 0 else "Any", "Bottom, Top, Corners, Path, Middle",
                               "BlockObject" if z == 1 else "None"))
m.blocks = cells
m.entrance(1, -1, 0)
m.extra["access"] = {"X": 1.5, "Y": 0.0, "Z": 0.5}
m.collider((1.5, 1.0, 1.12), (2.9, 2.0, 1.66))
m.notes += ["Nine beds as the Triple Lodge, entered at ground level (the vanilla Triple Lodge enters at z = 1). The "
            "roof is flat at y = 2 and the top blocks are Stackable 'BlockObject', so Terrace Houses stack up a slope."]
m.build()
