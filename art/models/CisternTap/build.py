"""Cistern Tap: pours stored water into a flume or a channel. 1x2 on the vanilla Discharge (cell (0, 0) on the ground,
cell (0, 1) over the water or drop, where the water leaves; its 'Water' drops attachment falls from the spout).

A celadon-glazed stoneware vat on a stone plinth with a wooden lid, a bamboo pipe from its foot with a wooden plug
tap, running out on a plank catwalk over the second cell to a split-bamboo spout tipping down; a ladle hung on the
tap post.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
from building import Model, block  # noqa: E402
import parts as K  # noqa: E402
import waterworks as W  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("CisternTap", size=(1, 2, 1), seed=313, stand_in="Discharge.Folktails")
g = m.geo
W.vat(g, 0.5, 0.42, 0.36, 1.05, floor=0.4, glaze=W.GLAZE_CELADON, sides=10, lid=0.6, plinth=0.1)
# the pipe from the vat's foot: a bamboo culm with a plug tap, out over the second cell on a plank catwalk
K.tube(g, [(0.5, 0.3, 0.72), (0.5, 0.3, 1.1)], [0.05, 0.05], BAMBOO_GOLD, sides=6)
K.tube(g, [(0.5, 0.36, 0.86), (0.5, 0.48, 0.86)], [0.035, 0.03], TIMBER, sides=5)
K.beam(g, (0.82, -0.02, 0.9), (0.82, 0.62, 0.9), w=0.05, caps="end")
K.beam(g, (0.82, 0.55, 0.9), (0.6, 0.55, 0.9), w=0.02, material=DETAILS, caps=False)
K.lathe(g, [(0.0, 0.0), (0.05, 0.01), (0.055, 0.05)], (0.6, 0.38, 0.9), 6, BAMBOO_GOLD, cap_top=False)
K.boards(g, (0.2, 0.0, 1.0), (0, 0, 1), (1, 0, 0), 0.9, 0.6, 4, TIMBER, thick=0.04)
for x in (0.2, 0.8):
    K.beam(g, (x, -0.35, 1.05), (x, 0.0, 1.05), w=0.05, caps=False)
    K.beam(g, (x, -0.35, 1.85), (x, 0.0, 1.85), w=0.05, caps=False)
K.channel(g, 1.05, 1.62, 0.22, 0.5, r_in=0.09, wall=0.025, material=BAMBOO_GREEN, around=5, sleeve=True, tilt=0.1)
K.lantern(g, (0.82, 0.62, 0.9), r=0.05, h=0.11)
m.blocks = [block("GroundOrStackable", "Bottom, Top, Path, Middle", "None"),
            block("Air", "Floor, Bottom, Path, Middle", "None")]
m.entrance(0, -1, 0)
m.slot("Entrance", (0.5, 0.0, 0.0), yaw=180)
m.extra["access"] = {"X": 0.5, "Y": 0.0, "Z": -0.1}
m.attach("Water", (0.5, 0.25, 1.62), "the vanilla Discharge's water drops, falling from the spout tip")
m.collider((0.5, 0.55, 0.42), (0.8, 1.1, 0.8))
m.collider((0.5, 0.05, 1.4), (0.7, 0.1, 0.9))
m.notes += ["Blocks, entrance and WaterOutput (0, 1, 0) as the vanilla Discharge (1x2x1)."]
m.build()
