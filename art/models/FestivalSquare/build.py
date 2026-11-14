"""Festival Square: where the Lantern Festival is called and danced. 5x5x2 on the vanilla Dance Hall (its attraction,
the twenty 'Spot' dance slots and its 'Light' attachment), laid on the ground as an open village square.

The postcard of the faction at dusk. A square of flagstones inside a stone kerb, framed by low plastered walls with
grey-tile coping and bamboo in planters; at the front a roofed timber gateway with two red lanterns; in the middle a
round stone dais with a tall lantern pole (tiled cap, a crown of lanterns); twenty dancers circle it in two rings.
At the back left a raised drum stand with a big barrel drum; at the back right a festival stall under an indigo awning
with lantern boxes, paper and baskets; a long bench for onlookers between them. Red only on the lanterns.

Nodes for the events module (docs/tech/events.md, section 9):
* `#FestivalLights` (static): the lantern strings from the pole top to the four corner masts and round the square, and
  the stall's lanterns. The module shows it from the festival's call to its end and hides it otherwise.
* `#FireworkMount`: an empty at the pole top, the launch point for lanterns and fireworks.
* `#LanternRise`: an empty on the dais in front of the pole: the Parent for a TemplateAttachmentsSpec entry
  ('LanternRise') whose prefab carries the rising-lantern particle system (see models.md, "Lantern rise").
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "pipeline", "kit"))
import numpy as np  # noqa: E402
from building import Model, block  # noqa: E402
import parts as K  # noqa: E402
from core import *  # noqa: E402,F401,F403

m = Model("FestivalSquare", size=(5, 5, 2), seed=223, stand_in="DanceHall.Folktails", overhang=0.3)
g = m.geo
C = np.array([2.5, 0.0, 2.5])
F = 0.06       # paving top
# paving: an earth bed, flagstones, a kerb of bigger stones all round
K.box(g, (0.03, 0.0, 0.03), (4.97, F, 4.97), EARTH, (0.02, 0.02, 0.98, 0.98), skip=(3,), tags={"base"})
# flagstones laid in courses (running bond), each slab a little different in tone and height
rows = 10
for j in range(rows):
    z0 = 0.2 + j * 4.6 / rows
    off = 0.25 if j % 2 else 0.0
    xs = [0.2] + [0.2 + off + 0.5 * k for k in range(1, 10) if 0.2 + off + 0.5 * k < 4.75] + [4.8]
    for x0, x1 in zip(xs[:-1], xs[1:]):
        if (x1 + x0) / 2 > 2.0 and (x1 + x0) / 2 < 3.0 and z0 > 2.0 and z0 < 2.9:
            continue    # under the dais
        h = 0.02 + 0.012 * g.rng.uniform()
        K.box(g, (x0 + 0.015, F - 0.01, z0 + 0.015), (x1 - 0.015, F + h, z0 + 4.6 / rows - 0.015), PLASTER,
              (0.1, 0.1, 0.9, 0.9), tags={"stone"})
        t = 0.6 + 0.08 * g.rng.uniform()
        g.parts[-1].C = np.tile([t, t * 0.99, t * 0.94, 1.0], (len(g.parts[-1].P), 1))
K.stones(g, 0.04, 0.04, 4.96, 4.96, y=-0.01, size=0.46, h=0.13, skip=0.0, tone=(0.58, 0.59, 0.57))
# a ring of darker stones round the dance floor
for k in range(20):
    a = 2 * math.pi * k / 20
    K.box(g, (-0.08, 0.0, -0.05), (0.08, 0.025, 0.05), PLASTER, (0.1, 0.1, 0.9, 0.9),
          R=rot_axis((0, 1, 0), -a), t=C + [math.cos(a) * 2.1, F, math.sin(a) * 2.1])
    g.parts[-1].C = np.tile([0.42, 0.44, 0.45, 1.0], (len(g.parts[-1].P), 1))
# --- the dais and the lantern pole
K.lathe(g, [(0.0, F), (0.5, F), (0.52, F + 0.1), (0.42, F + 0.18), (0.0, F + 0.18)], C, 12, PLASTER,
        uv_region=(0.1, 0.1, 0.9, 0.9))
g.parts[-1].C = np.tile([0.6, 0.6, 0.57, 1.0], (len(g.parts[-1].P), 1))
PT = 4.25
K.tube(g, [C + [0, F + 0.18, 0], C + [0, PT, 0]], [0.09, 0.07], TIMBER, sides=8)
for y in (0.6, 1.4, 2.4, 3.4):
    K.lathe(g, [(0.095, -0.04), (0.105, 0.0), (0.095, 0.04)], C + [0, y, 0], 8, BANDED, cap_top=False,
            uv_region=(0.03, 0.05, 0.08, 0.95))
K.round_roof(g, C + [0, 0.0, 0], 0.32, PT, PT + 0.3, sides=8, sag=0.03, thick=0.04)
for k in range(4):   # a crown of four lanterns under the cap (always there)
    a = math.pi / 4 + k * math.pi / 2
    K.beam(g, C + [0, PT - 0.05, 0], C + [math.cos(a) * 0.3, PT - 0.05, math.sin(a) * 0.3], w=0.03, caps=False)
    K.lantern(g, C + [math.cos(a) * 0.3, PT - 0.08, math.sin(a) * 0.3], r=0.1, h=0.24)
# --- the front: a roofed gateway between two low plastered walls with tile coping
GX0, GX1, GZ = 1.6, 3.4, 0.18
for x in (GX0, GX1):
    K.lathe(g, [(0.0, 0.0), (0.14, 0.0), (0.15, 0.16), (0.0, 0.18)], (x, F, GZ), 8, PLASTER, uv_region=(0.1, 0.1, 0.9, 0.9))
    g.parts[-1].C = np.tile([0.58, 0.58, 0.56, 1.0], (len(g.parts[-1].P), 1))
    K.beam(g, (x, F + 0.18, GZ), (x, 2.02, GZ), w=0.12, caps="end", tags={"frame"})
    for sx in (-1, 1):
        K.beam(g, (x, 1.75, GZ), (x + sx * 0.2, 1.98, GZ), w=0.05, caps=False)
K.beam(g, (GX0, 1.95, GZ), (GX1, 1.95, GZ), w=0.1, h=0.13, caps=False, tags={"frame"})
K.beam(g, (GX0, 1.6, GZ), (GX1, 1.6, GZ), w=0.07, h=0.08, caps=False, tags={"frame"})
K.roof(g, GX0 - 0.1, GZ - 0.18, GX1 + 0.1, GZ + 0.18, 2.02, 2.32, kind="gable", overhang=0.2, sag=0.05, lift=0.05,
       ridge_ends=0.05, tile=0.24, course=0.22)
for x in (GX0 + 0.35, GX1 - 0.35):
    K.lantern(g, (x, 1.56, GZ), r=0.1, h=0.24)
for (x0, x1) in ((0.12, GX0 - 0.1), (GX1 + 0.1, 4.88)):
    with g.tagged("walls"):
        K.box(g, (x0, F, 0.08), (x1, 0.62, 0.22), PLASTER_LATH, (0.05, 0.05, 0.95, 0.95), skip=(3,))
    K.box(g, (x0 - 0.03, 0.62, 0.05), (x1 + 0.03, 0.68, 0.25), TILE, (0.0, TILE_COURSES[0][0], 0.3, TILE_COURSES[0][1]),
          skip=(3,))
# side walls (left and right) along the front half, planters of bamboo on them
for x in (0.15, 4.85):
    with g.tagged("walls"):
        K.box(g, (x - 0.07, F, 0.22), (x + 0.07, 0.55, 2.6), PLASTER_LATH, (0.05, 0.05, 0.95, 0.95), skip=(3,))
    K.box(g, (x - 0.1, 0.55, 0.19), (x + 0.1, 0.6, 2.63), TILE, (0.0, TILE_COURSES[0][0], 0.3, TILE_COURSES[0][1]),
          skip=(3,))
    for z in (0.9, 2.0):
        K.lathe(g, [(0.0, 0.0), (0.12, 0.0), (0.14, 0.16)], (x, 0.6, z), 7, EARTH)
        for k in range(5):
            K.pole(g, (x, 0.74, z), (x + 0.08 * math.cos(k * 1.3), 1.45 + 0.15 * (k % 3), z + 0.08 * math.sin(k * 1.3)),
                   r=0.014, material=BAMBOO_GREEN, sides=3, bend=0.03, caps=False)
# --- the four corner masts for the lantern strings
MASTS = [(0.3, 0.42), (4.7, 0.42), (0.3, 4.65), (4.7, 4.65)]
MH = 2.75
for (x, z) in MASTS:
    K.pole(g, (x, F, z), (x, MH, z), r=0.04, material=BAMBOO_GOLD, sides=6, bend=0.008, taper=0.85)
    K.lathe(g, [(0.0, 0.0), (0.05, 0.02), (0.0, 0.12)], (x, MH, z), 6, BAMBOO_GOLD)
# --- back left: the drum stand
K.box(g, (0.3, F, 3.75), (1.55, 0.42, 4.85), TIMBER, WOOD_BLOCK, skip=(3,))
K.stairs(g, (0.93, F, 3.75), (0.93, 0.42, 3.45), width=0.5, steps=3)
DC = np.array([0.93, 0.95, 4.35])
for sx in (-1, 1):   # the drum frame: two splayed legs each side, a cross bar
    K.beam(g, DC + [sx * 0.5, -0.53, -0.18], DC + [sx * 0.42, 0.2, 0.0], w=0.06)
    K.beam(g, DC + [sx * 0.5, -0.53, 0.18], DC + [sx * 0.42, 0.2, 0.0], w=0.06)
K.lathe(g, [(0.3, -0.36), (0.38, -0.2), (0.4, 0.0), (0.38, 0.2), (0.3, 0.36)], DC, 12, TIMBER, axis=(1, 0, 0),
        cap_top=False, uv_region=WOOD_STRIPS[0])
for sx in (-1, 1):   # the drumheads (pale hide) and a ring of studs
    K.lathe(g, [(0.0, 0.0), (0.31, 0.0)], DC + [sx * 0.36, 0, 0], 12, PAPER, axis=(sx, 0, 0), cap_top=False,
            uv_region=(0.4, 0.1, 0.55, 0.3))
    K.lathe(g, [(0.33, -0.01), (0.34, 0.0), (0.33, 0.01)], DC + [sx * 0.345, 0, 0], 12, IRON, axis=(1, 0, 0),
            cap_top=False)
for k in range(2):   # drumsticks resting on the stand
    K.pole(g, (0.5 + 0.12 * k, 0.43, 3.9), (0.75 + 0.12 * k, 0.45, 3.95), r=0.02, material=TIMBER, sides=4, bend=0.0)
# --- back right: the festival stall under an indigo awning
SX0, SX1, SZ0, SZ1 = 3.35, 4.75, 3.8, 4.8
for (x, z) in ((SX0, SZ0), (SX1, SZ0), (SX0, SZ1), (SX1, SZ1)):
    K.pole(g, (x, F, z), (x, 1.55 if z > 4 else 1.35, z), r=0.035, material=BAMBOO_GOLD, sides=5, bend=0.01)
K.cloth(g, [(SX0 - 0.05, 1.33, SZ0 - 0.15), (SX1 + 0.05, 1.33, SZ0 - 0.15), (SX1 + 0.05, 1.55, SZ1),
            (SX0 - 0.05, 1.55, SZ1)], DETAILS, (0.03, 0.54, 0.09, 0.98), sag=0.05, nu=3, nv=2, wave=0.012)
K.box(g, (SX0 + 0.1, 0.48, SZ0 + 0.1), (SX1 - 0.1, 0.53, SZ0 + 0.55), TIMBER, WOOD_BLOCK, skip=(3,))
for x in (SX0 + 0.15, SX1 - 0.15):
    for z in (SZ0 + 0.15, SZ0 + 0.5):
        K.beam(g, (x, F, z), (x, 0.48, z), w=0.04, caps=False)
for k in range(3):   # folded lanterns, paper rolls, lantern boxes
    K.lathe(g, [(0.06, 0.0), (0.12, 0.02), (0.12, 0.06), (0.06, 0.08)], (SX0 + 0.35 + 0.3 * k, 0.53, SZ0 + 0.3), 6,
            PAPER, uv_region=(0.4, 0.1, 0.55, 0.3))
for k in range(2):
    K.tube(g, [(SX0 + 0.3, 0.56 + 0.06 * k, SZ0 + 0.5), (SX0 + 0.9, 0.56 + 0.06 * k, SZ0 + 0.5)], [0.03, 0.03], PAPER,
           sides=6, strips=[(0.36, 0.05, 0.6, 0.6)])
for k, (x, z) in enumerate(((SX1 - 0.3, SZ1 - 0.25), (SX1 - 0.65, SZ1 - 0.2), (SX1 - 0.35, SZ1 - 0.6))):
    K.box(g, (x - 0.16, F, z - 0.13), (x + 0.16, F + 0.24 + 0.04 * k, z + 0.13), DETAILS, DET_CRATE)
K.basket(g, (SX0 + 0.3, F, SZ1 - 0.25), h=0.2, r=0.15)
# --- onlookers' bench between the drum and the stall, potted bamboo
K.beam(g, (1.75, 0.32, 4.7), (3.2, 0.32, 4.7), w=0.2, h=0.05)
for x in (1.8, 3.15):
    K.beam(g, (x, F, 4.7), (x, 0.3, 4.7), w=0.05, caps=False)
# --- the festival lights: strings from the pole top to the masts and round the square, the stall's lanterns
with g.node("#FestivalLights"):
    top = C + [0, PT - 0.25, 0]
    for (x, z) in MASTS:
        K.lantern_string(g, tuple(top), (x, MH - 0.1, z), n=5, sag=0.35, r=0.08)
    for (a, b) in ((MASTS[0], MASTS[2]), (MASTS[2], MASTS[3]), (MASTS[3], MASTS[1])):
        K.lantern_string(g, (a[0], MH - 0.25, a[1]), (b[0], MH - 0.25, b[1]), n=5, sag=0.4, r=0.075)
    for (a, b) in ((MASTS[0], (GX0, 1.95, GZ)), ((GX1, 1.95, GZ), MASTS[1])):
        a3 = a if len(a) == 3 else (a[0], MH - 0.25, a[1])
        b3 = b if len(b) == 3 else (b[0], MH - 0.25, b[1])
        K.lantern_string(g, a3, b3, n=2, sag=0.2, r=0.07)
    for x in (SX0 + 0.2, (SX0 + SX1) / 2, SX1 - 0.2):
        K.lantern(g, (x, 1.3, SZ0 - 0.12), r=0.085, h=0.2)
m.animate("#FestivalLights", (0.0, 0.0, 0.0), (0, 1, 0), kind="static",
          driver="Pandaborn.Festival (shown from the festival's call to its end)")
# --- empties for the events module
m.slots.append({"name": "#FireworkMount", "raw": True, "local_pos": (2.5, PT + 0.32, 2.5)})
m.slots.append({"name": "#LanternRise", "raw": True, "local_pos": (2.5, F + 0.2, 2.05)})
# --- twenty dancers in two rings round the pole (inner 8, outer 12), facing along the ring
spots = []
for n, r in ((8, 1.0), (12, 1.65)):
    for k in range(n):
        a = 2 * math.pi * (k + 0.5) / n
        spots.append(((2.5 + math.cos(a) * r, F + 0.02, 2.5 + math.sin(a) * r), -math.degrees(a)))
for i, (p, yaw) in enumerate(spots):
    m.slot(f"Spot{i + 1}", p, yaw=yaw)
m.blocks = [block("GroundOrStackable", "Floor, Bottom, Corners, Path, Middle", "None") for _ in range(25)] + \
           [block("Any", "None", "None") for _ in range(25)]
m.entrance(2, -1, 0)
m.extra["access"] = {"X": 2.5, "Y": F, "Z": 0.3}
m.extra["festivalNodes"] = {"lights": "#FestivalLights", "fireworkMount": "#FireworkMount",
                            "lanternRise": "#LanternRise (attachment parent, see models.md 'Lantern rise')"}
m.attach("Light", (2.5, 1.375, 2.5), "the vanilla dance-hall light, high on the lantern pole")
m.collider((2.5, 0.05, 2.5), (5.0, 0.1, 5.0))
m.collider((2.5, 1.8, 2.5), (0.3, 3.6, 0.3))
m.collider((0.93, 0.4, 4.3), (1.3, 0.8, 1.1))
m.collider((4.05, 0.6, 4.3), (1.4, 1.2, 1.0))
m.stage_height = 1.2
m.notes += ["Blocks: an open square (ground layer Floor/Bottom/Corners/Path/Middle, upper layer free), entrance at the "
            "gateway (2, -1). Twenty 'Spot' slots in two rings round the pole (the Dance Hall's 'Dancing').",
            "Events-module nodes: #FestivalLights (static, shown/hidden by code), #FireworkMount, #LanternRise."]
m.build()
