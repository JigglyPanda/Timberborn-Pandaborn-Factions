"""Sky Lantern: the Inkpaws' wonder, a great paper lantern that carries seeds over the wasteland. 7x7x8 on the
vanilla Earth Recultivator (its blocks, entrance, wonder specs and the 'Lanterns' particle attachment, which already
releases small lanterns).

A launch terrace of three stone-faced earth steps; on it a tall lashed bamboo launch tower (four leaning legs, ring
platforms, ladders) holding the great lantern: a paper body glowing warm at night (lit WindowsAtlas paper, tinted
red-gold), a woven bamboo hoop and a fire tray hanging under it, held down by four ropes to stakes. Strings of small
lanterns run from the tower to poles at the terrace corners; banners and baskets of seed. When the wonder fires, the
great lantern ('#SkyLanternAnimated', WonderAnimationController plays it once) turns slowly and rises up and away.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("SkyLantern", size=(7, 7, 8), seed=191, stand_in="EarthRecultivator.Folktails", overhang=0.4)
g = m.geo
C = np.array([3.5, 0.0, 3.5])
# the stepped launch terrace
for k, (inset, top) in enumerate(((0.05, 0.3), (0.9, 0.6), (1.7, 0.9))):
    K.box(g, (inset, 0.0, inset), (7 - inset, top, 7 - inset), EARTH, (0.02, 0.02, 0.98, 0.98), skip=(3,),
          tags={"base"})
    K.stones(g, inset + 0.04, inset + 0.04, 7 - inset - 0.04, 7 - inset - 0.04, y=top - 0.3 if k else -0.01,
             size=0.42, h=0.32, skip=0.12, tags={"base"})
for k in range(3):   # front stair through the terraces
    K.box(g, (3.0, 0.0, -0.05 + 0.85 * k), (4.0, 0.3 * (k + 1), 0.6 + 0.85 * k), PLASTER, (0.1, 0.1, 0.9, 0.9), skip=(3,))
    g.parts[-1].C = np.tile([0.62, 0.62, 0.6, 1.0], (len(g.parts[-1].P), 1))
TOPY = 0.9
# the launch tower: four leaning bamboo legs (lashed bundles of two), two ring platforms, ladders
LEG = [(1.95, 1.95), (5.05, 1.95), (5.05, 5.05), (1.95, 5.05)]
HT = 4.1
with g.tagged("frame"):
    for (x, z) in LEG:
        top = C + (np.array([x, 0, z]) - C) * 0.45 + [0, HT, 0]
        for dx in (-0.06, 0.06):
            K.pole(g, (x + dx, TOPY, z), top + [dx * 0.5, 0, 0], r=0.07, material=BAMBOO_GOLD, sides=6, bend=0.008)
        for y in (2.0, 3.6):
            K.lashing(g, np.array([x, TOPY, z]) + (top - np.array([x, TOPY, z])) * ((y - TOPY) / (HT - TOPY)), (0, 1, 0),
                      r=0.14)
    for (yy, f) in ((2.4, 0.82), (HT - 0.05, 0.45)):
        pts = [C + (np.array([x, 0, z]) - C) * f + [0, yy, 0] for (x, z) in LEG]
        for i in range(4):
            K.beam(g, pts[i], pts[(i + 1) % 4], w=0.1, caps=False)
        K.box(g, pts[0] + [0.05, -0.05, 0.05], pts[2] + [-0.05, 0.0, -0.05], TIMBER, WOOD_BLOCK, skip=(3,))
K.ladder(g, (3.5, TOPY, 1.7), (3.5, 2.4, 2.25), width=0.36, rungs=7)
K.ladder(g, (2.9, 2.4, 2.6), (2.9, HT - 0.05, 2.85), width=0.32, rungs=8)
# the great lantern on its own node, tethered over the top platform
LC = C + np.array([0.0, HT + 0.15, 0.0])
with g.node("#SkyLanternAnimated"):
    body = [(0.85, 0.0), (1.5, 0.55), (1.85, 1.6), (1.8, 2.6), (1.45, 3.3), (0.65, 3.7), (0.0, 3.78)]
    n0 = len(g.parts)
    K.lathe(g, body, LC + [0, 0.35, 0], 12, WINDOWS, uv_region=(0.80, 0.03, 0.95, 0.20), cap_top=False, tags={"glow"})
    for p in g.parts[n0:]:
        p.C = np.tile([1.0, 0.62, 0.36, 1.0], (len(p.P), 1))      # red-gold paper
    # bamboo ribs over the paper, a hoop at the mouth, the fire tray hanging inside
    for k in range(8):
        a = 2 * math.pi * k / 8
        rib = [LC + [math.cos(a) * r * 1.02, 0.35 + y, math.sin(a) * r * 1.02] for r, y in body[:-1]]
        K.tube(g, rib, [0.035] * len(rib), BAMBOO_GOLD, sides=4, caps=False)
    ring = [LC + [math.cos(a) * 0.88, 0.35, math.sin(a) * 0.88] for a in np.linspace(0, 2 * math.pi, 13)]
    K.tube(g, ring, [0.06] * len(ring), BAMBOO_GOLD, sides=4, caps=False)
    K.lathe(g, [(0.0, 0.0), (0.22, 0.02), (0.25, 0.08)], LC + [0, 0.12, 0], 8, IRON, cap_top=False)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        K.beam(g, LC + [math.cos(a) * 0.24, 0.18, math.sin(a) * 0.24], LC + [math.cos(a) * 0.86, 0.36, math.sin(a) * 0.86],
               w=0.015, material=DETAILS, caps=False)
# tethers from the hoop down to the platform corners, small lanterns strung to the terrace corners
for (x, z) in LEG:
    corner = C + (np.array([x, 0, z]) - C) * 0.45 + [0, HT, 0]
    K.beam(g, LC + (corner - LC) * np.array([0.25, 0, 0.25]) + [0, 0.45, 0], corner, w=0.018, material=DETAILS,
           caps=False)
for (x, z) in ((0.35, 0.35), (6.65, 0.35), (6.65, 6.65), (0.35, 6.65)):
    K.pole(g, (x, 0.3, z), (x, 2.3, z), r=0.045, material=BAMBOO_GOLD, sides=5, bend=0.01)
    a = C + (np.array([x, 0, z]) - C) * 0.82 + [0, 2.4, 0]
    K.lantern_string(g, (x, 2.25, z), a, n=4, sag=0.35)
    K.lantern(g, (x, 2.3, z), r=0.13, h=0.3)
# banners on the front legs, baskets of seed on the terrace
for (x, z) in LEG[:2]:
    K.cloth(g, [(x - 0.2, 1.4, z - 0.12), (x + 0.2, 1.4, z - 0.12), (x + 0.2, 2.2, z - 0.12), (x - 0.2, 2.2, z - 0.12)],
            DETAILS, DET_BANNER, sag=0.0, nu=2, nv=3, wave=0.02)
for (x, z) in ((1.4, 2.6), (1.5, 4.6), (5.6, 3.0), (5.5, 4.8)):
    K.basket(g, (x, 0.6, z), h=0.18, r=0.16, material=WEAVE_GOLD)
m.animate("#SkyLanternAnimated", LC, (0, 1, 0), kind="rise", height=30.0, frames=240, fps=24.0,
          driver="WonderAnimationControllerSpec (plays once when the wonder fires)")
m.slot("Entrance", (3.5, 0.0, 0.0), yaw=180)
# builder slots on the construction stage, as the vanilla wonder's stages carry them
for i, (x, z) in enumerate(((2.6, 5.0), (4.9, 3.2), (3.0, 0.6), (2.9, 3.3), (2.0, 6.1), (6.2, 5.0), (4.0, 4.2),
                            (4.5, 0.4), (3.5, 4.4), (3.1, 2.9), (2.6, 3.8))):
    m.stage_slots.append((f"Working{i}", (x, 0.02, z), 0.0))
for i, (x, z) in enumerate(((1.0, 1.0), (6.0, 1.0), (6.0, 6.0), (1.0, 6.0), (3.5, 1.2), (5.8, 3.5))):
    m.stage_slots.append((f"Building{i}", (x, 0.02, z), 0.0))
for i, (x, z) in enumerate(((0.6, 3.5), (6.4, 3.5))):
    m.stage_slots.append((f"Cutting{i}", (x, 0.02, z), 0.0))
for i, (x, z) in enumerate(((2.0, 0.5), (5.0, 0.5), (3.5, 6.5))):
    m.stage_slots.append((f"Digging{i}", (x, 0.02, z), 0.0))
m.entrance(3, -1, 0)
m.extra["access"] = {"X": 3.5, "Y": 0.0, "Z": 0.6}
m.attach("Lanterns", (3.5, HT + 4.2, 3.5), "the vanilla rising-lantern particles, now from the top platform")
m.stage_height = 3.0
m.collider((3.5, 0.45, 3.5), (7.0, 0.9, 7.0))
m.collider((3.5, 3.0, 3.5), (3.2, 4.4, 3.2))
m.collider((3.5, 6.3, 3.5), (3.6, 3.8, 3.6))
m.notes += ["Blocks, entrance and wonder specs as the vanilla Earth Recultivator. The vanilla wonder uses four stages "
            "(thresholds 0.25/0.5/0.75); this model ships one stage carrying the builder slots (Working, Building, "
            "Cutting, Digging): set ConstructionSiteProgressVisualizerSpec.ProgressThresholds to [0.0].",
            "WonderAnimationController plays '#SkyLanternAnimated' once (rise, 10 s) and it snaps home on the last frame."]
m.build()
