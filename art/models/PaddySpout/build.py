"""Paddy Spout: keeps the field in front of it flooded to a shallow set depth. The vanilla Fill Valve's footprint:
cell (0, 0) is a one-way channel cell, cell (0, 1) hangs over the lower field ('Middle' only) and is where the water
pours out.

A short bamboo channel on a stone-faced earth block, a bamboo plug on a lever (the valve) under a low tiled hood,
and a low, wide fan of five water-worn culms spreading over the field.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, block  # noqa: E402
import parts as K  # noqa: E402
import waterworks as W  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("PaddySpout", size=(1, 2, 2), seed=67, stand_in="FillValve.Folktails", overhang=0.4)
g = m.geo
# earth block under the channel's sides, faced with stones on the field side
K.box(g, (0.04, -0.3, 0.04), (0.96, 0.18, 0.98), EARTH, (0.02, 0.02, 0.98, 0.98), skip=(2, 3), tags={"base"})
K.stones(g, 0.06, 0.06, 0.94, 0.96, y=-0.05, size=0.22, h=0.2, tags={"base"})
W.straight(g, 0.0, 0.92, 0.0, material=BAMBOO_GOLD)
# the spout (its silhouette at game zoom): a low, wide fan of five water-worn culms spreading out over the field
# from a short split-culm throat, lashed to a cross bar on two props, weathered dark and mossy where the water runs
K.channel(g, 0.86, 1.1, -0.02, 0.5, r_in=0.12, wall=0.03, material=BAMBOO_GREEN, around=5, sleeve=True, tilt=0.03)
n0 = len(g.parts)
for k in range(5):
    a = math.radians(-60 + 30 * k)
    end = (0.5 + math.sin(a) * 0.82, 0.02, 1.0 + math.cos(a) * 0.95)
    K.pole(g, (0.5, 0.14, 1.0), end, r=0.05, material=BAMBOO_GREEN, sides=5, bend=0.0, taper=0.85)
for p in g.parts[n0:]:
    t = np.clip((p.P[:, 1] + 0.1) / 0.15, 0, 1)[:, None]
    p.C = np.concatenate([np.array([0.34, 0.38, 0.26]) + (np.array([0.62, 0.64, 0.48]) - [0.34, 0.38, 0.26]) * t,
                          np.ones((len(t), 1))], 1)
K.beam(g, (0.02, 0.04, 1.42), (0.98, 0.04, 1.42), w=0.05)
for x in (0.12, 0.88):
    K.pole(g, (x, -0.6, 1.42), (x, -0.02, 1.42), r=0.022, material=BAMBOO_GOLD, sides=4, bend=0.0)
    K.lashing(g, (x, -0.02, 1.42), (1, 0, 0), r=0.05)
# the valve: a post with a lever and a plug on a rope over the channel's mouth
K.beam(g, (0.9, -0.02, 0.86), (0.9, 0.72, 0.86), w=0.06, caps="end")
K.beam(g, (0.94, 0.66, 0.86), (0.35, 0.78, 0.86), w=0.035)
K.beam(g, (0.45, 0.76, 0.86), (0.45, 0.42, 0.86), w=0.01, material=DETAILS, caps=False)
K.tube(g, [(0.45, 0.42, 0.86), (0.45, 0.26, 0.86)], [0.06, 0.05], BAMBOO_GREEN, sides=6)
K.stones(g, 0.88, 0.8, 1.0, 0.92, y=0.66, size=0.1, h=0.08, ring=False)
# the cap block (0, 0, 1): a little tiled hood over the valve on three posts (the valve post runs up as the fourth)
for (x, z) in ((0.08, 0.08), (0.92, 0.08), (0.08, 0.86)):
    K.beam(g, (x, -0.02, z), (x, 1.12, z), w=0.055, caps=False)
K.beam(g, (0.9, 0.7, 0.86), (0.9, 1.12, 0.86), w=0.055, caps=False)
K.roof(g, 0.08, 0.08, 0.92, 0.86, 1.12, 1.3, kind="gable", axis="z", overhang=0.1, sag=0.03, lift=0.03, thick=0.05,
       tile=0.2, course=0.2, ridge_ends=0.04)   # low: the spout's outline stays low and wide
m.blocks = [block("GroundOrStackable", "Bottom, Top, Corners, Path, Middle", "BlockObject"),
            block("Any", "Middle", "None"),
            block("Any", "Bottom, Top, Corners, Path, Middle", "None"),
            block("Any", "None", "None")]
m.extra["capCells"] = [{"X": 0, "Y": 0, "Z": 1}]
m.stage_height = 1.0
m.extra["outputCell"] = {"X": 0, "Y": 1, "Z": 0}
m.extra["waterCells"] = [{"X": 0, "Y": 0, "Z": 0}]
m.collider((0.5, 0.15, 0.5), (1.0, 0.4, 1.0))
m.collider((0.5, 0.1, 1.25), (0.3, 0.2, 0.5))
m.notes += ["Blocks as the vanilla Fill Valve (1x2x1, second cell 'Middle' only over the field) plus a cap layer: (0,0,1) occupied (the hood), (0,1,1) free.",
            "The spout tip is at about y = 0.0 over the far cell: water seems to pour from it into the field."]
m.build()
