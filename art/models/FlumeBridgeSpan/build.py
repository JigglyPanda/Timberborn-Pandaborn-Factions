"""Flume Bridge Span: the Flume Bridge's deck with nothing standing in its own cell, so it can cross over a ground
flume (or a path) below. Water cell (0, 0, 1) as the Flume Bridge (floor at y = 1); the lower cell is not occupied at
all (Occupations 'None'): the span is carried by its neighbours. Two long timber stringers under the culm run out a
little past both cell edges to rest on the next pieces, trussed from below by a bamboo king-post and two rope ties;
nothing reaches down into the cell under it.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
from building import Model, block  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403
import waterworks as W  # noqa: E402

m = Model("FlumeBridgeSpan", size=(1, 1, 2), seed=47, stand_in="ThrottlingValve.Folktails", overhang=0.12)
g = m.geo
with g.tagged("frame"):
    for x in (0.12, 0.88):
        K.beam(g, (x, 0.95, -0.1), (x, 0.95, 1.1), w=0.08, h=0.1)
        # a shallow truss under each stringer: a short king post and two rope ties (stays above y = 0.7)
        K.beam(g, (x, 0.9, 0.5), (x, 0.72, 0.5), w=0.04, caps=False)
        K.beam(g, (x, 0.92, 0.02), (x, 0.72, 0.5), w=0.012, material=DETAILS, caps=False)
        K.beam(g, (x, 0.72, 0.5), (x, 0.92, 0.98), w=0.012, material=DETAILS, caps=False)
    for z in (0.08, 0.5, 0.92):
        K.beam(g, (0.04, 0.99, z), (0.96, 0.99, z), w=0.06, h=0.05)
        for x in (0.12, 0.88):
            K.lashing(g, (x, 0.98, z), (1, 0, 0), r=0.045)
W.straight(g, 0.0, 1.0, 1.0)
m.blocks = [block("Any", "None", "None"),
            block("Any", "Bottom, Top, Corners, Path, Middle", "None")]
m.extra["waterCells"] = [{"X": 0, "Y": 0, "Z": 1}]
m.extra["flow"] = "along +Y (grid) for orientation Cw0"
m.extra["spanOver"] = "the lower cell (0, 0, 0) is unoccupied: a ground flume or a path may run under the span"
m.stage_height = 1.0
m.collider((0.5, 1.2, 0.5), (0.9, 0.45, 1.0))
m.notes += ["The water lane's FlumeBridgeSpan: same water cell as the Flume Bridge; no inert obstacle and no legs in "
            "the cell below. Stringers overhang the cell's front and back edges by 0.1 to rest on the neighbours."]
m.build()
