"""Dry-Stone Wall: a full block of stacked stones that keeps soil moisture out (a tea-slope terrace wall). 1x1x1 on
the vanilla Levee (its blocks: full, stackable on itself; water obstacle and soil barrier).

Courses of grey-blue field stones laid dry over an earth core, each course a little inset, with a mossy turf cap and
a few ferns, so stacked walls read as a terrace face and a row of them as one wall.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
from building import Model, block  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("DryStoneWall", size=(1, 1, 1), seed=311, stand_in="Levee.Folktails")
g = m.geo
K.box(g, (0.06, 0.0, 0.06), (0.94, 0.9, 0.94), EARTH, (0.05, 0.05, 0.95, 0.95), skip=(3,), tags={"base"})
for k, (y, inset, size) in enumerate(((0.0, 0.0, 0.3), (0.24, 0.02, 0.26), (0.47, 0.035, 0.27), (0.69, 0.05, 0.22))):
    K.stones(g, inset, inset, 1.0 - inset, 1.0 - inset, y=y - 0.01, size=size, h=0.25, gap=0.01, ring=True,
             tone=(0.6, 0.62, 0.6) if k % 2 else (0.54, 0.57, 0.56))
K.box(g, (0.08, 0.9, 0.08), (0.92, 0.97, 0.92), MOSS, (0.05, 0.05, 0.95, 0.95), skip=(3,))
for (x, z) in ((0.25, 0.3), (0.7, 0.62), (0.4, 0.78)):
    for k in range(3):
        K.pole(g, (x, 0.96, z), (x + 0.08 * (k - 1), 1.08, z + 0.05 * (k - 1)), r=0.01, material=BAMBOO_GREEN,
               sides=3, bend=0.0, caps=False)
m.blocks = [block("GroundOrStackable", "Bottom, Top, Corners, Path, Middle", "BlockObject")]
m.stage_height = 0.5
m.collider((0.5, 0.5, 0.5), (1.0, 1.0, 1.0))
m.notes += ["Blocks as the vanilla Levee (stackable on itself); keep the Levee's water obstacle and soil barrier specs."]
m.build()
