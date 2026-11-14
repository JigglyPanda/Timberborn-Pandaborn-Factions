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


def straight(geo, z0, z1, y_floor, material=BAMBOO_GREEN, sleeve=True, tilt=0.0, tags=(), tint=(0.8, 0.84, 0.78),
             nodes=(0.3, 0.78), rims=True):
    """One run of split giant culm from z0 to z1: the half-pipe, weathered dark and mossy below the waterline and
    fresher above, proud culm nodes round the outside, a lighter split-culm rim along both edges, and a rope-lashed
    sleeve at the upstream joint."""
    n0 = len(geo.parts)
    yf = y_floor + 0.012
    K.channel(geo, z0, z1, yf, CX, r_in=R_IN, wall=0.045, material=material, around=6, sleeve=False, tilt=tilt,
              tags=tags)
    L = z1 - z0
    sg = 1 if L > 0 else -1
    for f in nodes:
        zn = z0 + L * f
        K.channel(geo, zn, zn + 0.04 * sg, yf - 0.06 + tilt * (1 - f), CX, r_in=R_IN + 0.045, wall=0.02,
                  material=material, around=6, sleeve=False, tags=tags)
    # weathering by height: dark and green-brown at the bottom where water stands, cleaner toward the rims
    lo, hi = np.array([0.46, 0.52, 0.38]), np.array(tint)
    for p in geo.parts[n0:]:
        if p.material == material:
            t = np.clip((p.P[:, 1] - yf) / 0.3, 0, 1)[:, None] ** 0.8
            p.C = np.concatenate([lo + (hi - lo) * t, np.ones((len(t), 1))], 1)
    if rims:
        for x in (CX - R_IN - 0.022, CX + R_IN + 0.022):
            K.tube(geo, [(x, yf + R_IN + tilt, z0), (x, yf + R_IN, z1)], [0.024, 0.024], BAMBOO_GOLD, sides=4,
                   caps=False, tags=tags)
    if sleeve:
        # the joint: a short wider sleeve of culm over the upstream end, bound with two rope rings
        K.channel(geo, z0 - 0.02 * sg, z0 + 0.13 * sg, yf - 0.07 + tilt, CX, r_in=R_IN + 0.05, wall=0.02,
                  material=BAMBOO_GOLD, around=6, sleeve=False, tags=tags)
        for dz in (0.02, 0.1):
            n1 = len(geo.parts)
            K.channel(geo, z0 + dz * sg, z0 + (dz + 0.025) * sg, yf - 0.095 + tilt, CX, r_in=R_IN + 0.072,
                      wall=0.012, material=DETAILS, around=6, sleeve=False, tags=tags)
            for q in geo.parts[n1:]:
                q.UV = np.tile([0.775, 0.6], (len(q.P), 1)) + np.stack([np.zeros(len(q.P)),
                                                                           0.3 * (q.P[:, 0] - q.P[:, 0].min())], 1)


def x_stakes(geo, z, y_base=-0.02, y_top=0.62, material=BAMBOO_GOLD, tags=()):
    """Two stakes driven in either side of the channel at z, leaning out a little, lashed to the rims, with a tie
    across the top: the rhythm of a hand-built bamboo aqueduct."""
    for sx in (-1, 1):
        x = CX + sx * (R_IN + 0.085)
        K.pole(geo, (x - sx * 0.02, y_base, z), (x + sx * 0.06, y_top, z + geo.jitter(0.02)), r=0.028, material=material,
               sides=5, bend=0.01, tags=set(tags) | {"frame"})
        K.lashing(geo, (x + sx * 0.012, R_IN + 0.02, z), (0, 1, 0), r=0.04, tags=tags)
    K.pole(geo, (CX - R_IN - 0.18, y_top - 0.07, z), (CX + R_IN + 0.18, y_top - 0.06, z), r=0.018, material=material,
           sides=4, bend=0.0, tags=tags)


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


GLAZE_BROWN = (0.2, 0.13, 0.08)
GLAZE_CELADON = (0.48, 0.56, 0.5)


def vat(geo, cx, cz, r, h, floor, glaze=GLAZE_BROWN, sides=12, lid=0.45, plinth=0.14, tags=()):
    """A great glazed stoneware vat in the Sichuan pickle-jar tradition, for the tanks' liquid plane (which rises
    from `floor` to about `h`): a stone plinth, a full-bellied body (lime-white sheet painted with the glaze colour by
    vertex colour, darker at the foot, a lighter glaze-pool band at the shoulder), a rolled lip, the dark inside down to
    `floor`, and a planked wooden lid covering `lid` of the mouth."""
    c = np.array([cx, 0.0, cz])
    K.stones(geo, cx - r - 0.06, cz - r - 0.06, cx + r + 0.06, cz + r + 0.06, y=-0.01, size=0.3, h=plinth + 0.04,
             skip=0.0, tags=set(tags) | {"base"})
    K.lathe(geo, [(r * 0.8, 0.0), (r * 0.82, plinth)], c, sides, "Sand.Folktails", uv_region=(0.05, 0.05, 0.95, 0.95),
            tags=set(tags) | {"base"}, cap_top=True)
    y0 = plinth
    body = [(r * 0.68, y0), (r * 0.9, y0 + (h - y0) * 0.18), (r, y0 + (h - y0) * 0.5), (r * 0.97, y0 + (h - y0) * 0.72),
            (r * 0.86, y0 + (h - y0) * 0.9), (r * 0.84, h - 0.03), (r * 0.88, h), (r * 0.9, h + 0.03)]
    n0 = len(geo.parts)
    K.lathe(geo, body, c, sides, "Plaster_White.Folktails", uv_region=(0.05, 0.05, 0.95, 0.95), tags=tags,
            cap_top=False)
    K.lathe(geo, [(r * 0.9, h + 0.03), (r * 0.8, h + 0.03), (r * 0.8, h - 0.06)], c, sides, "Plaster_White.Folktails",
            uv_region=(0.05, 0.05, 0.95, 0.95), tags=tags, cap_top=False)
    g0 = np.array(glaze)
    for p in geo.parts[n0:]:
        t = np.clip((p.P[:, 1] - y0) / max(h - y0, 1e-6), 0, 1)[:, None]
        band = np.exp(-((t - 0.8) / 0.08) ** 2)       # glaze pooling at the shoulder: a lighter ring
        col = g0 * (0.75 + 0.35 * t) + band * 0.12
        p.C = np.concatenate([np.clip(col, 0, 1), np.ones((len(t), 1))], 1)
    K.lathe(geo, [(r * 0.8, h - 0.06), (r * 0.82, h * 0.6), (r * 0.7, floor + 0.08), (0.0, floor)], c, sides,
            "BaseMetal.Folktails", uv_region=(0.03, 0.03, 0.45, 0.45), tags=tags, cap_top=False)
    if lid > 0:
        # planked lid over the back part of the mouth, a handle bar across it
        rr = r * 0.86
        zc = cz + rr * (1 - lid)
        half = rr * lid
        n = 4
        for k in range(n):
            x0 = cx - rr + 2 * rr * k / n
            x1 = cx - rr + 2 * rr * (k + 1) / n
            xm = (x0 + x1) / 2
            span = math.sqrt(max(rr * rr - (xm - cx) ** 2, 0.01))
            zf, zb = max(cz + rr * (1 - 2 * lid), cz - span * 0.95), cz + span * 0.95
            if zb - zf < 0.05:
                continue
            K.box(geo, (x0 + 0.005, h + 0.03, zf), (x1 - 0.005, h + 0.06, zb), TIMBER, (0.02, 0.52, 0.48, 0.98),
                  skip=(3,), tags=tags)
        zh = cz + rr * (1 - lid)
        K.beam(geo, (cx - rr * 0.6, h + 0.09, zh), (cx + rr * 0.6, h + 0.09, zh), w=0.04, tags=tags)
