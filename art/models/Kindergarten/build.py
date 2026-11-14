"""Kindergarten: cubs play, adults watch. 3x3, on the vanilla Campfire's attraction blueprint (five seats).

A bamboo-fenced play yard: a little plastered playhouse with a tile roof and a round window, a bamboo slide off its
side, a swing on a bamboo frame, a sandpit of rammed earth with buckets, a giant panda-sized ball, and benches along
the fence for the grown-ups who watch.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, block  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("Kindergarten", size=(3, 3, 2), seed=107, stand_in="Campfire.Folktails")
g = m.geo
# ground: woven mats and a sandpit
K.panel(g, [(0.15, 0.01, 0.15), (2.85, 0.01, 0.15), (2.85, 0.01, 2.85), (0.15, 0.01, 2.85)], WEAVE_GOLD)
K.box(g, (1.75, 0.0, 0.35), (2.7, 0.12, 1.25), TIMBER, WOOD_STRIPS[0], skip=(2, 3))
K.box(g, (1.8, 0.0, 0.4), (2.65, 0.08, 1.2), EARTH, (0.05, 0.05, 0.95, 0.95), skip=(3,))
K.lathe(g, [(0.0, 0.0), (0.05, 0.0), (0.06, 0.08)], (2.1, 0.08, 0.7), 6, BAMBOO_GREEN, cap_top=False)
K.lathe(g, [(0.0, 0.0), (0.04, 0.0), (0.05, 0.07)], (2.4, 0.08, 0.95), 6, DETAILS, uv_region=DET_RED, cap_top=False)
# fence: bamboo posts and two rails, open at the front middle
pts = [(0.08, 0.08), (2.92, 0.08), (2.92, 2.92), (0.08, 2.92)]
for i in range(4):
    (ax, az), (bx, bz) = pts[i], pts[(i + 1) % 4]
    n = 6
    for k in range(n + 1):
        t = k / n
        x, z = ax + (bx - ax) * t, az + (bz - az) * t
        if i == 0 and 0.38 < t < 0.62:
            continue
        K.pole(g, (x, 0.0, z), (x, 0.42 + g.jitter(0.04), z), r=0.022, material=BAMBOO_GOLD, sides=4, bend=0.0)
    for y in (0.18, 0.36):
        if i == 0:
            for (s0, s1) in ((0.0, 0.4), (0.6, 1.0)):
                K.pole(g, (ax + (bx - ax) * s0, y, az), (ax + (bx - ax) * s1, y, az), r=0.014, material=BAMBOO_GREEN,
                       sides=3, bend=0.0, caps=False)
        else:
            K.pole(g, (ax, y, az), (bx, y, bz), r=0.014, material=BAMBOO_GREEN, sides=3, bend=0.0, caps=False)
# playhouse at the back left
HX0, HX1, HZ0, HZ1 = 0.3, 1.3, 1.85, 2.75
with g.tagged("walls"):
    K.wall(g, (HX0, HZ0), (HX1, HZ0), 0.0, 0.7, openings=[("door", 0.35, 0.26, 0.0, 0.46)], rail=False)
    K.wall(g, (HX1, HZ0), (HX1, HZ1), 0.0, 0.7, rail=False)
    K.wall(g, (HX1, HZ1), (HX0, HZ1), 0.0, 0.7, rail=False)
    K.wall(g, (HX0, HZ1), (HX0, HZ0), 0.0, 0.7, rail=False)
    K.gable_end(g, HX0, HZ0, HZ1, 0.7, 1.1, outward=-1)
    K.gable_end(g, HX1, HZ0, HZ1, 0.7, 1.1, outward=1)
K.window(g, (1.05, 0.42, HZ0 - 0.02), (0, 0, -1), 0.2, 0.2, frame=0.03, region=WIN_ROUND, sill=False)
K.roof(g, HX0, HZ0, HX1, HZ1, 0.7, 1.1, kind="gable", overhang=0.14, sag=0.05, lift=0.05, ridge_ends=0.06, tile=0.24,
       course=0.26)
# slide from the playhouse's side: a split-bamboo chute and a ladder
K.ladder(g, (1.55, 0.0, 2.55), (1.42, 0.72, 2.45), width=0.22, rungs=4)
K.box(g, (1.32, 0.68, 2.1), (1.6, 0.72, 2.6), TIMBER, WOOD_BLOCK)
K.channel(g, 2.1, 0.9, 0.06, 1.48, r_in=0.13, wall=0.025, material=BAMBOO_GREEN, around=5, sleeve=False, tilt=0.62)
# swing on a bamboo frame (left front)
for x in (0.3, 1.1):
    for dz in (-0.18, 0.18):
        K.pole(g, (x, 0.0, 0.9 + dz), (x, 1.05, 0.9), r=0.025, material=BAMBOO_GOLD, sides=4, bend=0.0)
K.pole(g, (0.24, 1.05, 0.9), (1.16, 1.05, 0.9), r=0.024, material=BAMBOO_GOLD, sides=5, bend=0.0)
for x in (0.55, 0.85):
    K.beam(g, (x, 1.04, 0.9), (x, 0.32, 0.9), w=0.01, material=DETAILS, caps=False)
K.box(g, (0.5, 0.29, 0.82), (0.9, 0.33, 0.98), TIMBER, WOOD_STRIPS[1])
# a big woven ball, and benches for the watchers
K.lathe(g, [(0.0, 0.0), (0.12, 0.03), (0.16, 0.16), (0.12, 0.29), (0.0, 0.32)], (1.55, 0.0, 1.45), 7, WEAVE_GOLD)
seats = []
for (x0, z0, x1, z1, yaw) in ((2.3, 2.7, 2.8, 2.7, 180), (2.72, 1.55, 2.72, 2.35, -90), (0.28, 0.3, 0.28, 0.6, 90)):
    p0, p1 = np.array([x0, 0.25, z0]), np.array([x1, 0.25, z1])
    K.beam(g, p0, p1, w=0.14, h=0.03)
    for p in (p0, p1):
        K.beam(g, p - [0, 0.25, 0], p, w=0.04, caps=False)
    L = int(round(np.linalg.norm(p1 - p0) / 0.32))
    for k in range(max(1, L)):
        t = (k + 0.5) / max(1, L)
        seats.append((tuple(p0 + (p1 - p0) * t + [0, 0.02, 0]), yaw))
for i, (p, yaw) in enumerate(seats[:5]):
    m.slot(f"Seat{i + 1}", p, yaw)
K.lantern(g, (2.92, 0.62, 0.08), r=0.05, h=0.11, hanging=False)
m.blocks = [block("Ground", "Floor, Bottom, Corners, Path, Middle", "None") for _ in range(9)] + \
           [block("Any", "None", "None") for _ in range(9)]
m.entrance(1, -1, 0)
m.extra["access"] = {"X": 1.5, "Y": 0.0, "Z": 0.6}
m.extra["removeSpecs"] = ["AttractionFireSpec", "FireSpec", "IlluminatorLightObjectsSpec", "TemplateAttachmentsSpec"]
m.extra["addSpecs"] = {"EnterableIlluminatorSpec": {}}
m.collider((1.5, 0.3, 1.5), (3.0, 0.6, 3.0))
m.collider((0.8, 0.6, 2.3), (1.1, 1.1, 1.0))
m.build()
