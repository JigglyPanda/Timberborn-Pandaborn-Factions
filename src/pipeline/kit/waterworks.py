"""Shared pieces of the flume set: every flume part is a split giant-bamboo channel one tile wide whose inner floor
sits on the water cell's floor, so the water the game simulates in that cell shows inside it.

Flow runs along +z (the grid's +Y, 'Top' for an unrotated building: ThrottlingValve/FillValve orientation Cw0), so
z = 0 is upstream. Rims at the channel's centre height (about 0.37 above the floor).
"""
import math

import numpy as np

import parts as K
from core import BAMBOO_GREEN, BAMBOO_GOLD, TIMBER, DETAILS

R_IN = 0.34
CX = 0.5


def straight(geo, z0, z1, y_floor, material=BAMBOO_GREEN, sleeve=True, tilt=0.0, tags=(), tint=(0.8, 0.84, 0.78)):
    n0 = len(geo.parts)
    K.channel(geo, z0, z1, y_floor + 0.012, CX, r_in=R_IN, wall=0.045, material=material, around=6, sleeve=sleeve,
              tilt=tilt, tags=tags)
    # a culm node: a slightly proud ring round the outside near the downstream end
    L = z1 - z0
    zn = z0 + L * 0.62
    K.channel(geo, zn, zn + 0.035 * (1 if L > 0 else -1), y_floor + 0.012 - 0.045 - 0.012 + tilt * 0.38,
              CX, r_in=R_IN + 0.045, wall=0.018, material=material, around=6, sleeve=False, tags=tags)
    # the fresh green reads as a toy in the game's bright light: weather it a little
    for p in geo.parts[n0:]:
        if p.material == material:
            p.C = np.tile(list(tint) + [1.0], (len(p.P), 1))


def stakes(geo, z, y_base=-0.02, y_top=0.46, tie=True, material=BAMBOO_GOLD, tags=()):
    """A pair of bamboo stakes either side of the channel at z, lashed to it, with a tie across above the rims."""
    for x in (CX - R_IN - 0.09, CX + R_IN + 0.09):
        K.pole(geo, (x, y_base, z), (x + geo.jitter(0.02), y_top, z), r=0.026, material=material, sides=5,
               bend=0.0, tags=set(tags) | {"frame"})
        K.lashing(geo, (x, 0.3, z), (0, 1, 0), r=0.036, tags=tags)
    if tie:
        K.pole(geo, (CX - R_IN - 0.13, y_top - 0.05, z), (CX + R_IN + 0.13, y_top - 0.04, z), r=0.017,
               material=material, sides=4, bend=0.0, tags=tags)


def x_trestle(geo, z, y_base, y_top, spread=0.42, material=BAMBOO_GOLD, tags=()):
    """Two bamboo poles crossed in an X under the channel, lashed where they cross; the channel rests in the V."""
    h = y_top - y_base
    a0, a1 = np.array([CX - spread, y_base, z]), np.array([CX + spread * 0.75, y_top, z])
    b0, b1 = np.array([CX + spread, y_base, z]), np.array([CX - spread * 0.75, y_top, z])
    K.pole(geo, a0, a1, r=0.028, material=material, sides=5, bend=0.01, tags=tags)
    K.pole(geo, b0, b1, r=0.028, material=material, sides=5, bend=0.01, tags=tags)
    t = spread / (spread + spread * 0.75)
    K.lashing(geo, a0 + (a1 - a0) * t, (0, 0, 1), r=0.04, tags=tags)


def leg_frame(geo, y_top, z_pairs=((0.08, 0.92),), x_pair=(0.07, 0.93), material=BAMBOO_GOLD, braces=True,
              tags=(), y_base=0.0):
    """Four bamboo legs at the cell's corners (so the middle stays free to walk under), a cross-tie at the top on
    each end, and X braces on the two long sides only."""
    for z0, z1 in z_pairs:
        for z in (z0, z1):
            for x in x_pair:
                K.pole(geo, (x, y_base, z), (x, y_top, z), r=0.032, material=material, sides=5, bend=0.012, tags=tags)
            K.pole(geo, (x_pair[0] - 0.04, y_top - 0.05, z), (x_pair[1] + 0.04, y_top - 0.05, z), r=0.026,
                   material=material, sides=4, bend=0.0, tags=tags)
            for x in x_pair:
                K.lashing(geo, (x, y_top - 0.05, z), (0, 1, 0), r=0.045, tags=tags)
        if braces:
            for x in x_pair:
                K.pole(geo, (x, y_base + 0.08, z0), (x, y_top - 0.12, z1), r=0.02, material=material, sides=4,
                       bend=0.0, tags=tags, caps=False)
                K.pole(geo, (x, y_top - 0.12, z0), (x, y_base + 0.08, z1), r=0.02, material=material, sides=4,
                       bend=0.0, tags=tags, caps=False)


def cistern_vessel(geo, cx, cz, r, h, floor, sides=12, tags=()):
    """A round open cistern for the vanilla tanks' liquid plane (which rises from `floor` to about `h`): a river-stone
    foot, a rammed-earth lower wall, a lime-plastered upper wall with cane hoops and a timber rim, and the inside
    (dark, down to `floor`) so the stored water's surface shows in the open top."""
    c = np.array([cx, 0.0, cz])
    K.stones(geo, cx - r - 0.02, cz - r - 0.02, cx + r + 0.02, cz + r + 0.02, y=-0.01, size=0.32, h=0.2, skip=0.1,
             tags=set(tags) | {"base"})
    split = min(0.9, h * 0.4)
    K.lathe(geo, [(r * 1.02, 0.0), (r * 1.03, split)], c, sides, "Sand.Folktails", uv_region=(0.03, 0.03, 0.97, 0.97),
            tags=set(tags) | {"base"}, cap_top=False)
    K.lathe(geo, [(r * 1.01, split), (r, h * 0.7), (r * 1.01, h)], c, sides, "PlasteredWood_White.Folktails",
            uv_region=(0.03, 0.03, 0.97, 0.97), tags=tags, cap_top=False)
    K.lathe(geo, [(r - 0.07, h), (r - 0.07, h * 0.6), (r - 0.09, floor + 0.05), (0.0, floor)], c, sides,
            "BaseMetal.Folktails", uv_region=(0.03, 0.03, 0.45, 0.45), tags=tags, cap_top=False)
    K.lathe(geo, [(r + 0.04, h - 0.02), (r + 0.05, h + 0.04), (r - 0.09, h + 0.04), (r - 0.09, h - 0.02)], c, sides,
            TIMBER, tags=tags, cap_top=False, strips=None)
    for y in (split + 0.12, h * 0.75):
        K.lathe(geo, [(r + 0.012, y - 0.03), (r + 0.025, y), (r + 0.012, y + 0.03)], c, sides, BAMBOO_GOLD, tags=tags,
                cap_top=False)
