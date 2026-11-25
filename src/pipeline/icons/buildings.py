"""Building icons (LabeledEntitySpec.Icon) for every new Inkpaws building in the catalogue.

Vanilla building icons are pen sketches of what the building *does* (a bell, a grill, a lodge), 112 px, drawn
small for small buildings and large for big ones, usually standing on a short ground line. Ours follow the same
rules in the BUILDING style. Where a building has a model (E:\\PandabornDev\\build\\models\\preview), the icon shows
the model's most recognisable feature, because the player learns the icon and then looks for that shape on the
map: the Village Hall's bell tower, the cisterns' glazed vats, the Dew Collector's funnel, the Kite Windmill's
upright sails. Roofs are this mod's low tiled gables (`roof_side`, `roof`, `roof_hip`), never stacked or upturned.
No writing, nothing Japanese-coded, no religious imagery.

Two families share a mark so they are learnt once:
* Ringtail (night folk) buildings carry the moon mark: a solid crescent at a fixed pixel size and place in the
  top-right corner (`ink.MARKS["moon"]`, `@b(..., moon=True)`). Keep that corner of the drawing empty.
* Water pieces (flume set, gate, spout, scoop wheel, cistern tap, treadwheel lift) are all built around the same
  split-bamboo half-pipe (`half_pipe`): its U-shaped open end faces the viewer, with water inside. The cisterns,
  the tap and the dew collector share the glazed vat (`vat`).
"""
import math

import numpy as np

from ink import BUILDING, Path, arc, circle, ellipse, hatch, icon, line, poly, rrect, spline

G = "Buildings"


def b(id, extent=None, note="", moon=False):
    """Register a building icon: file Pandaborn<Name>Icon.png under Sprites/Pandaborn/Buildings."""
    # `extent` is the building's relative size (small buildings are drawn small, as in vanilla); 0.92 brings the
    # set's median ink extent to vanilla's (~79 px of 112)
    return icon(id, group=G, style=BUILDING, extent=extent * 0.92 if extent else None, note=note,
                marks=("moon",) if moon else ())


# ------------------------------------------------------------------------------------------------ motifs

def ground(c, x0=6, x1=94, y=97):
    c.stroke(line((x0, y), (x1, y)))


def water(c, y=90, x0=6, x1=94, rows=2):
    for r in range(rows):
        xs = np.linspace(x0 + r * 8, x1 - r * 8, 50)
        c.stroke(Path(np.stack([xs, y + r * 8 + np.sin(xs / 6 + r) * 1.8], 1)))


def steam(c, x, y, h=16, w=0.9):
    c.stroke(spline((x, y), (x + 3, y - h * 0.33), (x - 3, y - h * 0.66), (x + 1, y - h)), w)


def sparkle(c, x, y, r):
    """A four-point star, solid: the vanilla Observatory's stars (and the goods' 'treated' sparkle)."""
    k = r * 0.27
    c.fill(poly((x, y - r), (x + k, y - k), (x + r, y), (x + k, y + k), (x, y + r), (x - k, y + k), (x - r, y),
                (x - k, y - k)))


def roof(c, cx, y, w, h, tiles=3):
    """A grey tile roof seen at the gable end: straight, very slightly sagging slopes from a short ridge cap, eaves
    reaching a little past the walls; an inner line along the slopes for the tile course."""
    hw = w / 2
    sag = h * 0.05
    left = spline((cx - hw - 1, y + h - 2), (cx - hw * 0.5, y + h * 0.5 + sag), (cx - 3, y))
    right = spline((cx + 3, y), (cx + hw * 0.5, y + h * 0.5 + sag), (cx + hw + 1, y + h - 2))
    c.shape((left + line((cx - 3, y), (cx + 3, y)) + right + line((cx + hw + 1, y + h - 2), (cx + hw - 2, y + h))
             + line((cx + hw - 2, y + h), (cx - hw + 2, y + h)) + line((cx - hw + 2, y + h), (cx - hw - 1, y + h - 2))
             ).close())
    if tiles:
        c.stroke(spline((cx - hw + 7, y + h - 4), (cx - hw * 0.45, y + h * 0.5 + sag + 3), (cx, y + 7),
                        (cx + hw * 0.45, y + h * 0.5 + sag + 3), (cx + hw - 7, y + h - 4)), 0.55)


def roof_side(c, x0, x1, y_ridge, y_eave, ribs=11.0, inset=None, over=3.0):
    """The long side of a tiled gable roof, the view the game camera gives: a wide sloping plane with cover-tile
    ribs running down it, a ridge roll on top, the eave line sagging very slightly. This is the mod's roof."""
    h = y_eave - y_ridge
    ins = h * 0.22 if inset is None else inset
    xl, xr = x0 - over, x1 + over
    outline = (line((x0 + ins, y_ridge), (x1 - ins, y_ridge))
               + spline((x1 - ins, y_ridge), (x1 - ins * 0.4 + 0.6, y_ridge + h * 0.55), (xr, y_eave - 1.5))
               + spline((xr, y_eave - 1.5), ((x0 + x1) / 2, y_eave + 0.6), (xl, y_eave - 1.5))
               + spline((xl, y_eave - 1.5), (x0 + ins * 0.4 - 0.6, y_ridge + h * 0.55), (x0 + ins, y_ridge)))
    c.shape(outline.close())
    if ribs:
        n = max(1, int((x1 - x0 - 2 * ins) / ribs))
        for k in range(1, n):
            t = k / n
            xa = x0 + ins + (x1 - x0 - 2 * ins) * t
            xb = xl + (xr - xl) * t
            c.stroke(line((xa, y_ridge + 2.5), (xb, y_eave - 3.5)), 0.42, taper=0.3)
    c.stroke(line((x0 + ins - 2.5, y_ridge - 0.5), (x1 - ins + 2.5, y_ridge - 0.5)), 1.35, taper=0.2)


def roof34(c, x0, x1, y_ridge, y_eave, gw, ribs=10.0, over=3.0, chimney=None):
    """A tiled gable roof in three-quarter view, as the game camera sees the models: the gable end (width `gw`) at
    the left, the long slope running right to x1, cover-tile ribs down the slope, a ridge roll. Returns the
    gable's apex x. `chimney` = x of a chimney standing on the slope."""
    ax = x0 + gw / 2
    g1, g2 = (x0 - over, y_eave), (x0 + gw + over * 0.4, y_eave)
    dx = x1 - (x0 + gw)
    r2, e2 = (ax + dx, y_ridge), (g2[0] + dx + over * 0.6, y_eave)
    if chimney is not None:
        t = 0.45
        cy = y_ridge + (y_eave - y_ridge) * t
        c.shape(rrect(chimney - 4, y_ridge - 12, 8, cy - y_ridge + 12, 1), 0.85)
    sag = 0.8
    c.shape((line(g1, (ax, y_ridge), r2, e2) + spline(e2, ((g2[0] + e2[0]) / 2, y_eave + sag), g2)
             + line(g2, g1)).close())
    c.stroke(line((ax, y_ridge), g2), 0.8)                               # the barge edge between gable and slope
    n = max(1, int(dx / ribs))
    for k in range(1, n + 1):
        t = k / (n + 1)
        c.stroke(line((ax + dx * t + 1.5, y_ridge + 2.5), (g2[0] + (e2[0] - g2[0]) * t, y_eave - 2.5)), 0.42,
                 taper=0.3)
    c.stroke(line((ax - 1, y_ridge - 0.5), (r2[0] + 2.5, y_ridge - 0.5)), 1.35, taper=0.2)
    return ax


def walls34(c, x0, x1, y_top, y_bot, gw, posts=2):
    """The walls under roof34: the gable-end wall (left, width gw) and the long side, timber frame."""
    c.shape(rrect(x0, y_top, gw, y_bot - y_top, 1))
    c.shape(rrect(x0 + gw, y_top, x1 - x0 - gw, y_bot - y_top, 1))
    for k in range(1, posts + 1):
        x = x0 + gw + (x1 - x0 - gw) * k / (posts + 1)
        c.stroke(line((x, y_top + 1), (x, y_bot - 1)), 0.65)


def roof_hip(c, cx, y_top, w_top, w_bot, h, ribs=9.0):
    """A hipped (pavilion) roof: short ridge, four slopes, ribs fanning out to the eave."""
    xl, xr = cx - w_bot / 2, cx + w_bot / 2
    tl, tr = cx - w_top / 2, cx + w_top / 2
    yb = y_top + h
    outline = (line((tl, y_top), (tr, y_top)) + spline((tr, y_top), (cx + w_bot * 0.3, y_top + h * 0.6), (xr, yb - 2))
               + spline((xr, yb - 2), (cx, yb + 0.6), (xl, yb - 2))
               + spline((xl, yb - 2), (cx - w_bot * 0.3, y_top + h * 0.6), (tl, y_top)))
    c.shape(outline.close())
    n = max(2, int(w_bot / ribs))
    for k in range(1, n):
        t = k / n
        xa = tl + (tr - tl) * t
        xb = xl + (xr - xl) * t
        c.stroke(line((xa, y_top + 2.5), (xb, yb - 3.5)), 0.42, taper=0.3)
    c.stroke(line((tl - 2, y_top - 0.5), (tr + 2, y_top - 0.5)), 1.3, taper=0.2)


def frame_wall(c, x, y, w, h, posts=2, beam=True):
    """Timber frame with plaster infill: outline, a few posts and a tie beam."""
    c.shape(rrect(x, y, w, h, 1))
    for k in range(1, posts + 1):
        xx = x + w * k / (posts + 1)
        c.stroke(line((xx, y + 1), (xx, y + h - 1)), 0.7)
    if beam:
        c.stroke(line((x + 1, y + h * 0.3), (x + w - 1, y + h * 0.3)), 0.7)


def door(c, x, y, w, h):
    c.shape(rrect(x, y, w, h, 1.5), 0.9)


def round_window(c, x, y, r):
    c.shape(circle(x, y, r), 0.85)
    c.stroke(line((x, y - r + 1), (x, y + r - 1)), 0.55)


def stones(c, x0, x1, y, h=7):
    """A footing of dressed stones."""
    c.shape(rrect(x0, y, x1 - x0, h, 1.5), 0.85)
    n = max(2, int((x1 - x0) / 14))
    for k in range(1, n):
        x = x0 + (x1 - x0) * k / n + (2 if k % 2 else -2)
        c.stroke(line((x, y + 1.5), (x, y + h - 1.5)), 0.5)


def lantern(c, x, y, s=1.0, string=6):
    """A small round hanging lantern, top of the string at (x, y)."""
    with c.at(x, y, s):
        c.stroke(line((0, 0), (0, string)), 0.6)
        c.shape(ellipse(0, string + 7, 6, 7), 0.8)
        c.stroke(line((0, string + 14), (0, string + 19)), 0.6)


def box_lantern(c, x, y, s=1.0, string=5):
    """A hexagonal paper lantern under a small hat (the decorations' lantern), top of the string at (x, y)."""
    with c.at(x, y, s):
        c.stroke(line((0, 0), (0, string)), 0.6)
        c.shape(spline((-9, string + 6), (0, string), (9, string + 6), closed=True), 0.8)       # hat
        c.shape(poly((-7, string + 6), (7, string + 6), (8, string + 20), (5, string + 24), (-5, string + 24),
                     (-8, string + 20)), 0.85)
        c.stroke(line((0, string + 8), (0, string + 22)), 0.5)
        c.stroke(line((0, string + 24), (0, string + 29)), 0.6)


def house(c, cx, base, w, wall_h, roof_h, door_w=None, windows=0, tiles=3):
    """Timber-frame house with a tile roof, gable-end view, standing on `base`."""
    top = base - wall_h
    frame_wall(c, cx - w / 2, top, w, wall_h, posts=2)
    dw = door_w or w * 0.24
    door(c, cx - dw / 2, base - wall_h * 0.62, dw, wall_h * 0.62)
    for k in range(windows):
        side = -1 if k % 2 == 0 else 1
        round_window(c, cx + side * w * 0.3, top + wall_h * 0.52, min(6, wall_h * 0.2))
    roof(c, cx, top - roof_h + 4, w + 12, roof_h, tiles)


def bamboo_post(c, x, y0, y1, w=1.0, nodes=2):
    c.stroke(line((x, y0), (x, y1)), w, taper=0)
    for k in range(1, nodes + 1):
        y = y0 + (y1 - y0) * k / (nodes + 1)
        c.stroke(line((x - 3, y), (x + 3, y)), 0.6, taper=0)


def wheel(c, cx, cy, r, spokes=8, kind="paddle"):
    """Water wheel: rim, hub, spokes; paddles or tube buckets on the rim."""
    c.shape(circle(cx, cy, r), occlude=False)
    c.shape(circle(cx, cy, r * 0.16), 0.8)
    for k in range(spokes):
        a = math.radians(k * 360 / spokes + 10)
        c.stroke(line((cx + math.cos(a) * r * 0.16, cy - math.sin(a) * r * 0.16),
                      (cx + math.cos(a) * r, cy - math.sin(a) * r)), 0.7)
        p = (cx + math.cos(a) * r, cy - math.sin(a) * r)
        if kind == "paddle":
            t = (math.cos(a + 1.5708), -math.sin(a + 1.5708))
            o = (math.cos(a), -math.sin(a))
            c.stroke(line(p, (p[0] + o[0] * 8 + t[0] * 3, p[1] + o[1] * 8 + t[1] * 3)), 1.0)
        else:  # tube buckets tied to the rim, angled
            with c.at(p[0], p[1], 1, math.degrees(a) + 60):
                c.shape(rrect(-3, -9, 7, 16, 3), 0.75)


def pao_jar(c, x, y, s=1.0):
    """A pickle jar with its water-seal collar and bowl lid; base centre at (x, y)."""
    with c.at(x, y, s):
        c.shape(spline((-12, -30), (-22, -22), (-24, -10), (-16, 0), (16, 0), (24, -10), (22, -22), (12, -30),
                       closed=True))
        c.shape(spline((-20, -30), (-12, -26), (12, -26), (20, -30), (0, -34), closed=True), 0.85)
        c.shape(spline((-12, -31), (-8, -39), (8, -39), (12, -31), closed=True), 0.85)


def vat(c, cx, base, w, h, lid=True, plinth=True, band=True):
    """A glazed stoneware water vat (the cisterns): a full belly, rounded shoulder, rolled lip, a planked lid over
    the back of the mouth, a glaze band at the shoulder, on a stone plinth. Base centre (cx, base); returns the
    y of the mouth."""
    if plinth:
        stones(c, cx - w * 0.5, cx + w * 0.5, base - 7, 7)
        base -= 7
    top = base - h
    mx, my = w * 0.27, w * 0.07
    c.shape(spline((cx - mx, top), (cx - w * 0.42, top + h * 0.16), (cx - w * 0.5, top + h * 0.48),
                   (cx - w * 0.42, top + h * 0.82), (cx - w * 0.3, base), (cx + w * 0.3, base),
                   (cx + w * 0.42, top + h * 0.82), (cx + w * 0.5, top + h * 0.48),
                   (cx + w * 0.42, top + h * 0.16), (cx + mx, top), closed=True))
    c.shape(ellipse(cx, top, mx + 2, my + 1.5))                    # rolled lip
    c.stroke(arc(cx, top, mx - 2, 180, 360, ry=my * 0.6), 0.5)     # inner lip edge (water side)
    if lid:                                                        # planks over the back half of the mouth
        c.shape((arc(cx, top - 1, mx + 3, 0, 180, ry=my + 3) + line((cx - mx - 3, top - 1), (cx + mx + 3, top - 1))
                 ).close(), 0.8)
        for k in (-1, 0, 1):
            c.stroke(line((cx + k * mx * 0.48, top - 2), (cx + k * mx * 0.5, top - my - 1.5)), 0.45)
    if band:
        c.stroke(arc(cx, top + h * 0.2, w * 0.45, 200, 340, ry=my * 1.3), 0.6)
    return top


def half_pipe(c, x, y, d, L, ang, water_line=True, end=True):
    """The split-bamboo flume: a half-pipe seen from a little above, its U-shaped cut end towards the viewer at
    (x, y) (the middle of the rim chord), radius d, running back `L` units in screen direction `ang` degrees
    (0 = right, 90 = up). You look into it: the far end shows as a shallow arc, a culm node rib crosses the inside,
    water runs along the bottom."""
    a = math.radians(ang)
    v = np.array([math.cos(a) * L, -math.sin(a) * L])
    A, B = np.array([x - d, y], float), np.array([x + d, y], float)
    A2, B2 = A + v, B + v
    sag_far = d * 0.55

    def inner_arc(p, q, sag):
        m = (p + q) / 2 + np.array([0, sag])
        return spline(tuple(p), tuple((p + m) / 2 + np.array([0, sag * 0.35])), tuple(m),
                      tuple((q + m) / 2 + np.array([0, sag * 0.35])), tuple(q))

    outline = line(tuple(A), tuple(A2)) + inner_arc(A2, B2, sag_far) + line(tuple(B2), tuple(B)) \
        + arc(x, y, d, 360, 180)
    c.shape(outline.close())
    t = 0.5                                                          # a culm node rib across the inside
    c.stroke(inner_arc(A + v * t, B + v * t, d * (1 - 0.45 * t)), 0.5)
    if water_line:
        wy = d * 0.62
        c.stroke(spline((x - d * 0.3, y + wy), (x + v[0] * 0.5, y + v[1] * 0.5 + d * 0.78),
                        (x + v[0] * 0.92, y + v[1] * 0.92 + sag_far * 0.8)), 0.5)
    if end:
        c.shape((arc(x, y, d, 180, 360) + arc(x, y, d * 0.72, 360, 180)).close(), 0.75)   # the cut culm wall


def trestle(c, x, y_top, y_bot, spread=8):
    """An X-legged bamboo trestle."""
    c.stroke(line((x - spread, y_bot), (x + spread * 0.4, y_top)), 0.85)
    c.stroke(line((x + spread, y_bot), (x - spread * 0.4, y_top)), 0.85)
    c.dot(x, y_top + (y_bot - y_top) * 0.29, 0.85)


def napper(c, x, y, s=1.0, flip=False):
    """A panda lying asleep on its side: a long body, the head at one end with ears and a dark eye patch."""
    k = -1 if flip else 1
    with c.at(x, y, s, sx=k * s):
        c.shape(spline((-14, 0), (-12, -7), (4, -9), (14, -6), (16, 0), closed=True), 0.8)       # body
        c.shape(circle(19, -6, 7), 0.85)                                                         # head
        c.shape(circle(16, -13, 2.6), 0.7, filled=True)                                          # ears
        c.shape(circle(23, -12.5, 2.6), 0.7, filled=True)
        c.stroke(arc(21, -6, 2.2, 200, 340, ry=1.2), 0.55)                                       # closed eye


def mushroom(c, x, base, h, s=1.0):
    """A bamboo mushroom (zhusun) as in the goods icon: conical cap, a netted veil skirt, a stem."""
    with c.at(x, base, s):
        c.shape(spline((-9, 0), (-6, -h * 0.5), (6, -h * 0.5), (9, 0), closed=True), 0.7)          # veil
        for seg in hatch(poly((-9, 0), (-6, -h * 0.5), (6, -h * 0.5), (9, 0)), 4.5, 60, margin=1.2):
            c.stroke(seg, 0.4)
        c.shape(spline((-7, -h * 0.5), (-5, -h * 0.8), (0, -h), (5, -h * 0.8), (7, -h * 0.5), closed=True), 0.8)


# ------------------------------------------------------------------------------------------- village

@b("PandabornVillageHall", 98, "District centre: a long tiled hall with a lower eave, and its open bell tower at "
                               "the front-left with the bell hanging inside")
def village_hall(c):

    ground(c, 2, 98)
    c.stroke(line((90, 26), (90, 4)), 0.7)                          # signal mast at the back
    c.shape(rrect(86, 1, 8, 4, 1.5), 0.6)
    walls34(c, 38, 96, 62, 97, 26, posts=2)
    door(c, 70, 74, 14, 23)
    roof34(c, 38, 96, 20, 62, 26, ribs=9)
    # the bell tower: open timber legs, braces, a small pyramid roof, the bell inside
    for x in (6, 30):
        c.stroke(line((x, 97), (x, 26)), 1.0)
    c.stroke(line((6, 60), (30, 60)), 0.7)
    c.stroke(line((6, 62), (30, 84)), 0.55)
    c.stroke(line((30, 62), (6, 84)), 0.55)
    c.stroke(line((6, 48), (30, 48)), 0.8)
    c.shape(spline((11, 32), (12, 42), (10, 46), (26, 46), (24, 42), (25, 32), (18, 28), closed=True), 0.85)
    c.stroke(line((18, 26), (18, 28)), 0.6)
    roof_hip(c, 18, 6, 2, 38, 20, ribs=8)


@b("PandabornFestivalSquare", 92, "Festival square: a tall lantern pole with lantern strings to the corner poles, "
                                  "a tiled gateway in front, paving")
def festival_square(c):
    c.shape(poly((2, 97), (98, 97), (84, 78), (16, 78)), 0.9)        # the paved square
    for x0, x1 in ((34, 30), (66, 70)):
        c.stroke(line((x0, 79), (x1, 96)), 0.45)
    c.stroke(line((10, 87), (90, 87)), 0.45)
    for x, y0 in ((12, 30), (88, 30)):
        bamboo_post(c, x, y0, 86, 0.9, nodes=1)
    c.stroke(line((50, 12), (50, 86)), 1.1)                          # centre pole and its lantern
    lantern(c, 50, 4, 0.8, string=2)
    for sgn in (-1, 1):
        sp = spline((50, 20), (50 + sgn * 20, 30), (50 + sgn * 38, 32))
        c.stroke(sp, 0.55)
        for t in (0.35, 0.75):
            px, py = sp.pts[int(t * (len(sp.pts) - 1))]
            c.shape(ellipse(px, py + 4.5, 3.6, 4.2), 0.6)
    for x, w in ((26, 14), (40, 10)):                                 # festival goods on the square
        c.shape(rrect(x - w / 2, 74 - w * 0.8, w, w * 0.8, 1), 0.7)
    c.shape(rrect(64, 62, 16, 12, 5), 0.8)                            # the drum on its stand
    c.shape(ellipse(64, 68, 3, 6), 0.6)


# ------------------------------------------------------------------------------------------------ homes

@b("PandabornDen", 70, "Den: a small house under a big steep tiled roof, chimney at the ridge, open porch posts")
def den(c):

    ground(c, 6, 94)
    stones(c, 10, 90, 89, 8)
    walls34(c, 16, 84, 60, 89, 28, posts=1)
    door(c, 58, 68, 12, 21)
    c.stroke(line((48, 60), (48, 89)), 0.9)                          # porch posts
    c.stroke(line((82, 60), (82, 89)), 0.9)
    roof34(c, 14, 86, 12, 60, 30, ribs=10, chimney=72)


@b("PandabornCourtyardHouse", 94, "Courtyard house: two tiled wings at a right angle round a walled yard, the "
                                  "front wing showing its gable")
def courtyard_house(c):

    ground(c, 2, 98)
    walls34(c, 34, 96, 50, 90, 22, posts=2)                         # back wing, three-quarter view
    roof34(c, 34, 96, 18, 50, 22, ribs=10)
    frame_wall(c, 4, 60, 36, 37, posts=1)                           # front wing, its gable towards you
    door(c, 16, 76, 12, 21)
    roof(c, 22, 34, 46, 28, tiles=2)
    c.shape(rrect(44, 80, 52, 17, 1), 0.85)                         # yard wall with its gate
    c.shape(rrect(64, 84, 14, 13, 1), 0.8)


@b("PandabornTerraceHouse", 94, "Terrace house: a two-storey house seen from the corner, a tiled skirt roof and a "
                                "railed gallery between the floors, and the flat roof deck with its two drying trays")
def terrace_house(c):
    ground(c, 2, 98)
    dx, dy = 22, -17                                                 # the depth of the block, up and to the right
    x0, x1, yt, ym, yb = 6, 70, 40, 64, 90
    stones(c, x0 - 2, x1 + 2, yb, 7)
    c.shape(poly((x1, yt), (x1 + dx, yt + dy), (x1 + dx, yb + dy + 9), (x1, yb + 7)), 0.9)    # side wall
    c.stroke(line((x1 + 2, ym + 2), (x1 + dx, ym + dy + 4)), 0.6)
    c.shape(rrect(x0, yt, x1 - x0, yb - yt, 1))                      # front wall
    door(c, 32, ym + 12, 12, yb - ym - 12)
    for x in range(x0 + 8, x1 - 2, 9):                               # gallery balusters and rail
        c.stroke(line((x, ym - 10), (x, ym)), 0.42)
    c.stroke(line((x0, ym - 10), (x1, ym - 10)), 0.7)
    c.shape(poly((x0 - 4, ym + 8), (x0, ym), (x1, ym), (x1 + 4, ym + 8)), 0.9)   # the tiled skirt roof
    for x in range(x0 + 6, x1, 9):
        c.stroke(line((x, ym + 1.5), (x + (x - 38) * 0.06, ym + 6.5)), 0.42)
    c.shape(poly((x0, yt), (x1, yt), (x1 + dx, yt + dy), (x0 + dx, yt + dy)))    # the flat roof deck
    for x, r in ((32, 11), (59, 11)):                                # drying trays on the deck
        y = yt + dy / 2
        c.shape(ellipse(x, y, r, 5.2), 0.8)
        c.stroke(ellipse(x, y, r - 4.5, 2.0), 0.45)


@b("PandabornMoonLoft", 88, "Moon Loft (Ringtails): a tiled house high on bamboo stilts with a ladder up to it",
   moon=True)
def moon_loft(c):

    ground(c, 2, 92)
    for x in (16, 70):
        bamboo_post(c, x, 50, 97, 1.0, nodes=1)
    c.shape(rrect(8, 48, 72, 5, 1), 0.85)                            # floor
    walls34(c, 12, 74, 30, 48, 22, posts=1)
    round_window(c, 23, 39, 5)
    door(c, 52, 34, 10, 14)
    roof34(c, 12, 74, 4, 30, 22, ribs=10)
    c.stroke(line((38, 97), (46, 53)), 0.75)                         # ladder
    c.stroke(line((48, 97), (56, 53)), 0.75)
    for k in range(1, 5):
        y = 97 - k * 9
        t = (97 - y) / 44
        c.stroke(line((38 + 8 * t, y), (48 + 8 * t, y)), 0.55)


# ------------------------------------------------------------------------------------------------- food

@b("PandabornSteamer", 80, "Steamer: three stacked bamboo steamer baskets on a wok over a stove, steam")
def steamer(c):
    c.shape(rrect(14, 78, 72, 19, 2))                             # stove
    c.shape(arc(50, 97, 9, 0, 180, ry=9).close(), 0.8)            # fire mouth
    c.shape(spline((12, 74), (50, 84), (88, 74), (50, 70), closed=True), 0.9)   # wok rim
    for k, y in enumerate((60, 44, 28)):
        c.shape((arc(50, y, 30, 180, 360, ry=7) + line((80, y), (80, y + 13)) + arc(50, y + 13, 30, 0, -180, ry=7)
                 + line((20, y + 13), (20, y))).close())
    c.shape(ellipse(50, 28, 30, 7))
    c.shape(rrect(45, 17, 10, 7, 3), 0.8)
    steam(c, 30, 18)
    steam(c, 70, 18)


def cloth_jar(c, x, y, s=1.0):
    """A pickle jar as the model shows it: a tall glazed pot, its mouth under a tied cloth (solid: the red cloth is
    what you see from above); base centre at (x, y)."""
    with c.at(x, y, s):
        c.shape(spline((-7, -33), (-18, -27), (-20, -13), (-13, 0), (13, 0), (20, -13), (18, -27), (7, -33),
                       closed=True))
        c.stroke(arc(0, -20, 17, 200, 340, ry=4), 0.45)                                   # a glaze line
        c.shape(spline((-9, -33), (-8, -40), (0, -43), (8, -40), (9, -33), (0, -31), closed=True), 0.7, filled=True)
        c.stroke(line((-9, -32), (-14, -27)), 0.6)                   # the cloth's tied corners
        c.stroke(line((9, -32), (14, -27)), 0.6)


@b("PandabornPickleYard", 86, "Pickle yard: rows of big glazed pickle jars under their tied cloth tops, behind the "
                              "yard's rail")
def pickle_yard(c):
    # pass 4: the jars alone, large (with the shed behind them the yard and the Tea Roastery were both 'a house with
    # round things in front' at 40 px); the cloth tops are the model's mark from above
    ground(c, 2, 98)
    for x in (33, 67):                                               # back row
        cloth_jar(c, x, 70, 0.72)
    for x in (17, 50, 83):                                           # front row
        cloth_jar(c, x, 97, 0.8)


def roof_thatch(c, x0, x1, y_ridge, y_eave, gw, over=4.0):
    """A thatched roof in the same three-quarter view as roof34: a thick rounded ridge, a shaggy eave, two bamboo
    battens tied along the slope and short straw ticks between them."""
    ax = x0 + gw / 2
    h = y_eave - y_ridge
    g1, g2 = (x0 - over, y_eave), (x0 + gw + over * 0.4, y_eave)
    dx = x1 - (x0 + gw)
    r2, e2 = (ax + dx, y_ridge), (g2[0] + dx + over * 0.6, y_eave)
    eave = [e2]
    n = max(4, int((e2[0] - g2[0]) / 6))
    for k in range(1, n):
        x = e2[0] + (g2[0] - e2[0]) * k / n
        eave.append((x, y_eave + (2.6 if k % 2 else 0.2)))
    eave.append(g2)
    c.shape((spline(g1, (ax - gw * 0.34, y_ridge + h * 0.42), (ax - 2, y_ridge + 1), (ax + 3, y_ridge - 1.5))
             + line((ax + 3, y_ridge - 1.5), (r2[0] - 2, y_ridge - 1.5))
             + spline((r2[0] - 2, y_ridge - 1.5), (r2[0] + 3, y_ridge + 2), (e2[0] - 1, y_eave - h * 0.4), e2)
             + line(*eave) + line(g2, g1)).close())
    c.stroke(spline((ax + 2, y_ridge), (ax + (g2[0] - ax) * 0.55, y_ridge + h * 0.5), g2), 0.8)   # the gable edge
    sl = (g2[0] - ax) / h
    for t in (0.5,):                                                 # a bamboo batten holding the thatch down
        c.stroke(line((ax + sl * h * t + 2.5, y_ridge + h * t), (r2[0] + (e2[0] - r2[0]) * t - 1.5,
                                                                 y_ridge + h * t)), 0.55, taper=0.2)
    m = int(dx / 9)
    for row, (ta, tb) in enumerate(((0.12, 0.38), (0.62, 0.88))):   # straw
        for k in range(1, m + 1):
            x = ax + 4 + (dx - 6) * (k - (0.5 if row % 2 else 0.0)) / (m + 0.5)
            c.stroke(line((x + sl * h * ta, y_ridge + h * ta), (x + sl * h * tb, y_ridge + h * tb)), 0.38, taper=0.4)


@b("PandabornPaddyHouse", 86, "Paddy house: the farmhouse under its thick thatched roof, beside a flooded terrace of "
                              "rice")
def paddy_house(c):
    c.stroke(line((2, 74), (70, 74)))
    for x in (8, 26, 44, 62):                                        # open posts under the thatch
        c.stroke(line((x, 44), (x, 74)), 0.85, taper=0)
    c.stroke(line((8, 60), (62, 60)), 0.55)
    roof_thatch(c, 4, 66, 16, 46, 20)
    water(c, 86, 4, 96)
    for x in (74, 90):
        for a in (100, 75, 125):
            c.stroke(line((x, 86), (x + math.cos(math.radians(a)) * 12, 86 - math.sin(math.radians(a)) * 20)), 0.7)
        c.stroke(spline((x, 86), (x + 2, 64), (x + 7, 58), (x + 10, 66)), 0.7)


def tea_tray(c, x, y, rx, ry, sprig=False):
    """A round woven tray of tea leaves on the drying rack, tilted towards the game camera."""
    c.shape(ellipse(x, y, rx, ry), 0.9)
    if sprig:                                                        # one bud and two leaves, as on the goods icon
        c.stroke(line((x, y + ry * 0.62), (x, y - ry * 0.1)), 0.55)
        for ang, L in ((90, 0.78), (150, 0.7), (30, 0.7)):
            with c.at(x, y + ry * 0.12, 1, ang):
                c.shape(spline((0, 0), (rx * L * 0.4, -rx * 0.17), (rx * L, 0), (rx * L * 0.4, rx * 0.17),
                               closed=True), 0.5, filled=True)
    else:
        for dx, dy in ((-0.35, -0.1), (0.3, -0.25), (0.05, 0.3)):
            c.dot(x + dx * rx, y + dy * ry, 0.6)


@b("PandabornTeaRoastery", 84, "Tea roastery: round woven trays of tea leaves on the rack in front of the tiled "
                               "roasting shed, the tea sprig on the nearest")
def tea_roastery(c):
    ground(c, 2, 98)
    walls34(c, 34, 96, 24, 97, 20, posts=1)
    roof34(c, 34, 96, 2, 24, 20, ribs=10, chimney=80)
    c.erase(rrect(-2, 44, 104, 52, 0))
    tea_tray(c, 52, 56, 19, 11)                                      # (never one big and two small: a face)
    tea_tray(c, 25, 78, 23, 17, sprig=True)
    tea_tray(c, 75, 78, 23, 17, sprig=True)


@b("PandabornTripHammerMill", 94, "Trip-hammer mill: a water wheel in the stream, a long hammer beam rocking on a "
                                  "post, its head over a stone mortar")
def trip_hammer_mill(c):
    wheel(c, 24, 60, 22, 8)
    c.erase(rrect(-4, 82, 52, 20, 0))
    water(c, 86, 0, 46, rows=2)
    c.stroke(line((24, 60), (54, 60)), 1.0)                          # axle, its cam lifting the beam's tail
    c.shape(rrect(50, 52, 9, 13, 2), 0.8)
    c.stroke(line((60, 97), (68, 64)), 1.0)                          # pivot post
    c.stroke(line((76, 97), (68, 64)), 1.0)
    c.stroke(line((54, 50), (98, 74)), 1.4)                          # the beam
    c.shape(rrect(86, 70, 12, 16, 2))                                # hammer head
    c.shape(spline((78, 97), (80, 89), (102, 89), (104, 97), closed=True), 0.9)   # mortar
    ground(c, 50, 104)


@b("PandabornKitchen", 82, "Kitchen: a work table with a bowl of rice balls, a round seed cake and a rolling pin")
def kitchen(c):
    c.shape(rrect(6, 64, 88, 7, 2))                               # table top
    for x in (12, 88):
        c.stroke(line((x, 71), (x, 97)), 1.0)
    c.stroke(line((12, 88), (88, 88)), 0.6)
    c.shape(ellipse(32, 46, 20, 6))                               # bowl
    for x, y in ((24, 42), (34, 39), (42, 44)):
        c.shape(circle(x, y, 6), 0.8)
    c.shape((arc(32, 46, 20, 180, 360, ry=6) + spline((52, 46), (46, 60), (32, 63), (18, 60), (12, 46))).close())
    c.shape(spline((58, 60), (60, 54), (82, 54), (84, 60), (71, 63), closed=True), 0.9)   # cake
    c.shape(ellipse(71, 55, 13, 4), 0.8)
    with c.at(64, 40, 1, -14):                                    # rolling pin
        c.shape(rrect(-14, -4, 28, 8, 4), 0.9)
        c.stroke(line((-20, 0), (-14, 0)), 1.0)
        c.stroke(line((14, 0), (20, 0)), 1.0)


@b("PandabornHotPotHall", 92, "Hot pot hall: a divided hot pot steaming on a round table under a raised tiled roof")
def hot_pot_hall(c):
    roof_side(c, 26, 74, 0, 12, ribs=8, inset=3, over=2)             # the raised vent roof
    c.stroke(line((30, 12), (30, 18)), 0.6)
    c.stroke(line((70, 12), (70, 18)), 0.6)
    roof_side(c, 6, 94, 16, 34, ribs=10, inset=6)
    for x in (10, 90):
        c.stroke(line((x, 34), (x, 97)), 0.9)
    c.shape(ellipse(50, 78, 36, 8))                               # table
    c.stroke(line((50, 86), (50, 97)), 1.2)
    c.stroke(line((40, 97), (60, 97)), 0.9)
    c.shape((arc(50, 64, 18, 180, 360, ry=6) + spline((68, 64), (66, 74), (50, 77), (34, 74), (32, 64))).close())
    c.shape(ellipse(50, 64, 18, 6))
    c.stroke(spline((34, 62), (46, 62), (54, 66), (66, 66)), 0.7)
    steam(c, 42, 54, 14)
    steam(c, 58, 54, 14)


# --------------------------------------------------------------------------------------- wood, materials

@b("PandabornLanternWorkshop", 88, "Lantern workshop: finished paper lanterns hung out on a cord between bamboo poles "
                                   "in front of the tiled workshop")
def lantern_workshop(c):
    ground(c, 2, 98)
    walls34(c, 30, 96, 28, 97, 20, posts=1)
    roof34(c, 30, 96, 4, 28, 20, ribs=10)
    bamboo_post(c, 8, 30, 97, 1.0, nodes=2)
    bamboo_post(c, 92, 50, 97, 1.0, nodes=1)
    cord = spline((8, 36), (30, 54), (60, 60), (92, 54))
    c.stroke(cord, 0.6)
    pts = cord.pts
    for t in (0.2, 0.42, 0.64, 0.86):
        x, y = pts[int(t * (len(pts) - 1))]
        with c.at(x, y, 1.0):                                        # a ribbed round lantern with cap and tassel
            c.stroke(line((0, 0), (0, 3)), 0.6)
            c.shape(ellipse(0, 12, 8.5, 9), 0.85)
            c.stroke(arc(0, 12, 3.4, 90, 270, ry=9), 0.4)
            c.stroke(arc(0, 12, 3.4, 90, -90, ry=9), 0.4)
            c.stroke(line((0, 21), (0, 26)), 0.6)


@b("PandabornSmokeKiln", 86, "Smoke kiln: a low arched brick kiln with a chimney, poles laid along its top, smoke")
def smoke_kiln(c):
    ground(c, 2, 98)
    kiln = spline((8, 97), (8, 64), (24, 44), (50, 38), (76, 44), (92, 64), (92, 97), closed=False)
    c.shape((kiln + line((92, 97), (8, 97))).close())
    c.shape(arc(36, 97, 12, 0, 180, ry=16).close(), 0.9)          # firing mouth
    for y in (62, 78):
        c.stroke(line((14 if y < 70 else 10, y), (90, y)), 0.5)
    c.shape(rrect(70, 14, 12, 34, 1))                             # chimney
    for k in range(3):                                            # poles curing on the kiln
        y = 52 - k * 6
        c.shape(rrect(14 + k * 6, y, 52 - k * 10, 5, 2.5), 0.7)
    c.stroke(spline((76, 12), (72, 6), (80, 0), (74, -6)), 0.8)


@b("PandabornOxWorkshop", 88, "Ox workshop: the Wooden Ox, an upright horned wooden automaton with a block head, bolt "
                              "eyes, a nose ring and plank limbs, and a cog beside it")
def ox_workshop(c):
    ground(c, 2, 98)
    for x in (30, 52):                                               # plank legs
        c.shape(rrect(x - 6, 82, 13, 15, 2), 0.9)
    c.shape(rrect(12, 54, 11, 26, 3), 0.9)                           # arms hanging at the sides
    c.shape(rrect(60, 54, 11, 26, 3), 0.9)
    c.shape(rrect(22, 50, 39, 36, 5))                                # the barrel body
    c.stroke(line((26, 62), (57, 62)), 0.5)
    c.stroke(line((41, 64), (41, 84)), 0.45)
    c.stroke(spline((24, 22), (11, 17), (8, 2)), 1.5, taper=0.55)    # the horns
    c.stroke(spline((60, 22), (73, 17), (76, 2)), 1.5, taper=0.55)
    c.shape(rrect(20, 18, 44, 31, 5))                                # the block head
    c.shape(rrect(30, 32, 24, 19, 3), 0.9)                           # snout
    c.shape(circle(42, 45, 3.4), 0.7)                                # nose ring
    for x in (28, 56):                                               # bolt eyes
        c.shape(circle(x, 27, 3.6), 0.75, filled=True)
    gx, gy, gr = 88, 82, 9                                           # a cog: it is built, not born
    c.shape(circle(gx, gy, gr), 0.9)
    c.shape(circle(gx, gy, 3), 0.6)
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        c.stroke(line((gx + math.cos(a) * gr, gy - math.sin(a) * gr), (gx + math.cos(a) * (gr + 4.5),
                                                                       gy - math.sin(a) * (gr + 4.5))), 1.1, taper=0)


# ------------------------------------------------------------------------------------------------- water

@b("PandabornCisternSmall", 58, "Small cistern: a squat glazed stoneware vat on its stone plinth, planked lid")
def cistern_small(c):
    vat(c, 50, 97, 56, 34)


@b("PandabornCisternMedium", 76, "Medium cistern: a tall glazed vat with a ladder against it")
def cistern_medium(c):
    vat(c, 54, 97, 60, 62)
    c.stroke(line((14, 97), (22, 28)), 0.75)                         # ladder
    c.stroke(line((24, 97), (31, 30)), 0.75)
    for k in range(1, 7):
        y = 97 - k * 10
        t = (97 - y) / 69
        c.stroke(line((14 + 8 * t, y), (24 + 7.5 * t, y)), 0.5)


@b("PandabornCisternLarge", 94, "Large cistern: a wide glazed vat with a stair up to a small tiled windlass shelter")
def cistern_large(c):
    vat(c, 46, 97, 84, 54)
    for k in range(5):                                               # stair up the side
        y = 88 - k * 10
        c.shape(rrect(86 - k * 2, y, 14, 4, 1), 0.65)
    c.stroke(line((98, 90), (90, 46)), 0.6)


@b("PandabornDewCollector", 84, "Dew collector: a wide woven funnel on four bamboo posts, drops falling into a vat")
def dew_collector(c):
    for x in (14, 86):
        bamboo_post(c, x, 18, 92, 0.9, nodes=1)
    cone = (arc(50, 16, 40, 180, 360, ry=8) + line((90, 16), (54, 50)) + line((54, 50), (46, 50))
            + line((46, 50), (10, 16))).close()
    c.shape(cone)
    for seg in hatch(cone, 8, 62, margin=2) + hatch(cone, 8, -62, margin=2):
        c.stroke(seg, 0.42)
    c.shape(ellipse(50, 16, 40, 8))
    c.stroke(arc(50, 16, 34, 200, 340, ry=5.5), 0.45)
    for y in (56, 62):
        c.fill(spline((50, y - 3), (52, y + 1), (50, y + 2.5), (48, y + 1), closed=True))
    vat(c, 50, 97, 34, 22, lid=False, band=False)


@b("PandabornFlume", 90, "Flume: the split-bamboo half-pipe, open U end towards you, water inside, on lashed stakes")
def flume(c):
    ground(c, 2, 98)
    trestle(c, 32, 80, 97, 12)
    trestle(c, 78, 77, 97, 12)
    half_pipe(c, 18, 68, 14, 70, 5)


@b("PandabornFlumeCorner", 90, "Flume corner: two half-pipes meeting at a stone basin, both open ends towards you")
def flume_corner(c):
    ground(c, 2, 98)
    c.shape(poly((66, 30), (96, 30), (96, 50), (66, 50)), 0.9)        # stone basin at the corner
    c.stroke(line((70, 40), (92, 40)), 0.5)
    half_pipe(c, 18, 40, 13, 50, 4)                                  # the run coming in from the left
    half_pipe(c, 80, 78, 15, 30, 92)                                 # the run turning towards you


@b("PandabornFlumeDrop", 90, "Flume drop: the upper half-pipe on a dry-stone pier pours off its end into the lower "
                             "one")
def flume_drop(c):
    ground(c, 2, 98)
    for x, y, w, h in ((4, 54, 24, 21), (30, 54, 22, 21), (2, 77, 20, 20), (24, 77, 30, 20)):
        c.shape(rrect(x, y, w, h, 5), 0.8)                           # the dry-stone pier
    half_pipe(c, 17, 38, 14, 36, 3)                                  # upper run
    for x, y0 in ((52, 46), (58, 44), (64, 46)):                     # the fall
        c.stroke(spline((x, y0), (x + 3, y0 + 14), (x + 2, 74)), 0.7)
    half_pipe(c, 62, 76, 14, 32, 3)                                  # lower run, receiving
    trestle(c, 88, 90, 97, 7)


@b("PandabornFlumeBridge", 96, "Flume bridge: the half-pipe carried high on two lashed bamboo X-trestles over a gap")
def flume_bridge(c):
    c.stroke(line((2, 97), (22, 97)))
    c.stroke(line((78, 97), (98, 97)))
    water(c, 92, 26, 74, rows=1)
    for x in (24, 74):
        trestle(c, x, 40, 97, 14)
    c.stroke(line((14, 40), (84, 40)), 0.8)                          # head beam
    half_pipe(c, 22, 30, 13, 66, 12)


@b("PandabornFlumeBridgeSpan", 92, "Flume bridge span: a half-pipe on two posts crossing over another flume that "
                                   "runs towards you underneath")
def flume_bridge_span(c):
    ground(c, 2, 98)
    half_pipe(c, 50, 82, 14, 44, 90)                                 # the lower run, coming towards you
    for x in (16, 86):                                               # the span's trestles, as on the bridge
        trestle(c, x, 44, 97, 10)
    c.stroke(line((6, 45), (96, 41)), 0.9, taper=0.2)                # head beam
    half_pipe(c, 16, 32, 13, 72, 3)                                  # the span, crossing over


@b("PandabornFlumeGate", 92, "Flume gate: the half-pipe runs towards you through a small roofed sluice frame; the "
                             "slatted gate board hangs on a rope from a tall bamboo lever with a stone counterweight")
def flume_gate(c):
    ground(c, 2, 98)
    c.stroke(line((16, 97), (16, 8)), 1.1, taper=0)                  # the lever post
    half_pipe(c, 50, 80, 17, 22, 90)                                 # the flume, its cut end towards you
    for x in (30, 70):                                               # the sluice frame
        c.stroke(line((x, 42), (x, 84)), 1.1, taper=0)
    c.shape(rrect(35, 46, 30, 24, 1), 0.9)                           # the gate board
    for x in (43, 50, 57):
        c.stroke(line((x, 48), (x, 68)), 0.42)
    roof_side(c, 26, 74, 28, 42, ribs=9, inset=5, over=3)
    c.stroke(line((50, 12), (50, 28)), 0.55)                         # rope from the lever down to the board
    c.stroke(line((4, 26), (84, 4)), 1.05, taper=0.15)               # the lever
    c.dot(16, 22.5, 0.8)
    c.stroke(line((82, 5), (82, 13)), 0.55)
    c.shape(poly((75, 13), (89, 13), (93, 29), (71, 29)), 0.9)       # the stone counterweight


@b("PandabornScoopWheel", 96, "Scoop wheel: a tall bamboo wheel with tube buckets on an A-frame, lifting water from "
                              "the current into a half-pipe chute")
def scoop_wheel(c):
    c.stroke(line((22, 97), (42, 46)), 0.9)
    c.stroke(line((62, 97), (42, 46)), 0.9)
    wheel(c, 42, 46, 34, 8, kind="tube")
    c.erase(rrect(-2, 86, 100, 20, 0))
    water(c, 90, 0, 84, rows=2)
    half_pipe(c, 66, 22, 9, 30, 28)                                  # the chute the buckets tip into


@b("PandabornPaddySpout", 86, "Paddy spout: a small roofed stone basin with a low wide fan of three bamboo culms "
                              "pouring into a shallow rice field")
def paddy_spout(c):
    stones(c, 2, 38, 64, 11)
    c.shape(rrect(7, 46, 26, 18, 1), 0.9)                            # the basin under its little roof
    roof(c, 20, 26, 42, 20)
    for ang, L in ((16, 40), (-4, 46), (-24, 42)):                   # the fan of culms
        a = math.radians(ang)
        with c.at(33, 56, 1, ang):
            c.shape(rrect(0, -4.2, L, 8.4, 3.5), 0.85)
            c.stroke(line((L * 0.5, -3.5), (L * 0.5, 3.5)), 0.45, taper=0)
        ex, ey = 33 + math.cos(a) * L, 56 - math.sin(a) * L
        c.stroke(spline((ex + 1, ey + 3), (ex + 4, ey + 9), (ex + 4, min(86, ey + 20))), 0.6)
    water(c, 90, 30, 98, rows=2)
    for a in (100, 78, 122):
        c.stroke(line((92, 88), (92 + math.cos(math.radians(a)) * 9, 88 - math.sin(math.radians(a)) * 17)), 0.7)


@b("PandabornCisternTap", 80, "Cistern tap: a glazed vat with a bamboo tap low on its side, pouring into a half-pipe")
def cistern_tap(c):
    vat(c, 34, 97, 52, 48)
    c.shape(rrect(52, 64, 22, 6, 3), 0.8)                            # tap pipe
    c.stroke(line((62, 64), (62, 56)), 0.8)                          # valve handle
    c.stroke(line((57, 56), (67, 56)), 0.9)
    for x in (72, 75):
        c.stroke(spline((x, 70), (x + 2, 76), (x + 2, 80)), 0.6)
    half_pipe(c, 70, 86, 10, 26, 4)


@b("PandabornTreadwheelLift", 94, "Treadwheel lift: under a tiled shed roof a pedal wheel on its axle, with a hand "
                                  "rail to lean on, drags a chain of pallets up a sloping half-pipe from the water")
def treadwheel_lift(c):
    water(c, 92, 0, 40, rows=1)
    ground(c, 44, 100)
    for x in (48, 94):                                               # the shed's posts
        c.stroke(line((x, 16), (x, 97)), 0.95, taper=0)
    c.stroke(line((48, 32), (94, 32)), 0.7)                          # the hand rail
    roof_side(c, 42, 100, 2, 17, ribs=9, inset=5, over=2)
    half_pipe(c, 15, 82, 11, 52, 30, water_line=False)
    for t in np.linspace(0.22, 0.8, 4):                              # pallets on the chain
        x, y = 15 + math.cos(math.radians(30)) * 52 * t, 82 - math.sin(math.radians(30)) * 52 * t
        c.stroke(line((x - 6, y + 4), (x + 4, y - 5)), 0.7)
    c.stroke(line((48, 58), (94, 58)), 0.8, taper=0)                 # the axle
    c.shape(circle(71, 58, 6.5), 0.85)                               # the pedal wheel
    for k in range(6):
        a = math.radians(k * 60 + 30)
        c.stroke(line((71 + math.cos(a) * 6.5, 58 - math.sin(a) * 6.5), (71 + math.cos(a) * 17,
                                                                        58 - math.sin(a) * 17)), 0.85)
        with c.at(71 + math.cos(a) * 17, 58 - math.sin(a) * 17, 1, math.degrees(a) + 90):
            c.shape(rrect(-5, -2.6, 10, 5.2, 2.2), 0.7)


@b("PandabornDryStoneWall", 80, "Dry-stone wall: fitted stones holding up a tea terrace, a tea bush on top")
def dry_stone_wall(c):
    stns = [(4, 66, 26, 14), (32, 64, 30, 16), (64, 66, 32, 14), (4, 82, 34, 15), (40, 82, 22, 15),
            (64, 82, 32, 15)]
    for x, y, w, h in stns:
        c.shape(rrect(x, y, w, h, 5), 0.9)
    c.stroke(line((2, 62), (98, 62)), 0.8)
    bumps = []
    for k in range(9):
        t = math.pi * k / 8
        rr = 1.0 if k % 2 else 0.88
        bumps.append((50 - math.cos(t) * 30 * rr, 60 - math.sin(t) * 24 * rr))
    c.shape(spline(*bumps, closed=True))


# ------------------------------------------------------------------------------------------------- power

@b("PandabornBambooWaterWheel", 92, "Bamboo water wheel: woven paddles on bamboo spokes, half in the stream, its shaft")
def bamboo_water_wheel(c):
    wheel(c, 44, 52, 38, 10)
    c.shape(rrect(78, 48, 22, 8, 2), 0.9)                         # shaft to the power network
    c.stroke(line((44, 52), (80, 52)), 1.0)
    c.erase(rrect(0, 74, 100, 30, 0))
    water(c, 80, 2, 98, rows=2)


def sail_rotor(c, cx, y_top, y_bot, rx, ry, angles, W, mast_top, deck_w, battens=3, rise=12):
    """The model's vertical-axis sail windmill in three-quarter view: batten sails hang on spokes round an upright
    mast, on a deck. The spoke tips lie on an ellipse (rx, ry) seen from above; a sail at screen angle `a` (0 = right,
    90 = towards you) is a parallelogram as wide as it is turned to the viewer, so the sails differ and the rotor
    does not close into a barrel. Back sails are drawn first, then the mast, then the front ones."""
    yb = y_bot + ry + 3
    c.shape(rrect(cx - deck_w / 2, yb, deck_w, 7, 1), 0.9)                                 # the deck

    def geom(a):
        r = math.radians(a)
        return (cx + rx * math.cos(r), ry * math.sin(r), -math.sin(r) * W / 2, math.cos(r) * W / 2 * ry / rx)

    def sail(a):
        x, dy, hx, hy = geom(a)
        c.shape(poly((x - hx, y_top + dy - hy), (x + hx, y_top + dy + hy), (x + hx, y_bot + dy + hy),
                     (x - hx, y_bot + dy - hy)), 0.9)
        for k in range(1, battens + 1):
            y = y_top + (y_bot - y_top) * k / (battens + 1) + dy
            c.stroke(line((x - hx * 0.82, y - hy * 0.82), (x + hx * 0.82, y + hy * 0.82)), 0.42, taper=0.2)

    def spokes(a):
        x, dy, _, _ = geom(a)
        c.stroke(line((cx, y_top - rise), (x, y_top + dy)), 0.6)
        c.stroke(line((cx, y_bot - 4), (x, y_bot + dy)), 0.6)

    order = sorted(angles, key=lambda a: math.sin(math.radians(a)))
    back = [a for a in order if math.sin(math.radians(a)) < 0]
    front = [a for a in order if a not in back]
    for a in back:
        sail(a)
    for a in back:
        spokes(a)
    c.stroke(line((cx, yb), (cx, mast_top + 3)), 1.35, halo=1.2, taper=0)                 # the mast
    for a in front:
        spokes(a)
    for a in front:
        sail(a)
    c.shape(poly((cx, mast_top - 3), (cx + 13, mast_top + 1.5), (cx, mast_top + 6)), 0.7, filled=True)   # pennant


@b("PandabornKiteWindmillSmall", 78, "Kite windmill: three tall batten sails turning round an upright mast on a deck, "
                                     "seen three-quarter on: one face-on behind the mast, two swung round in front")
def kite_windmill_small(c):
    ground(c, 6, 94)
    sail_rotor(c, 50, 26, 70, 34, 13, (270, 35, 145), 26, 0, 76)


@b("PandabornKiteWindmillLarge", 100, "Large kite windmill: the same rotor, taller, on a wider deck, with five sails")
def kite_windmill_large(c):
    ground(c, 0, 100)
    sail_rotor(c, 50, 24, 76, 42, 15, (270, 200, 340, 52, 128), 22, -8, 100, battens=4, rise=14)


# ---------------------------------------------------------------------------------------------- science

@b("PandabornStarTower", 96, "Star Tower (Ringtails): a lattice tower rising out of a tiled pavilion, a telescope "
                             "on its railed top", moon=True)
def star_tower(c):
    ground(c, 2, 92)
    frame_wall(c, 14, 72, 64, 25, posts=2, beam=False)               # the pavilion
    roof_hip(c, 46, 54, 16, 84, 20)
    c.erase(rrect(30, 20, 32, 30, 0))
    for x0, x1 in ((34, 38), (58, 54)):                              # lattice tower through the roof
        c.stroke(line((x0, 56), (x1, 22)), 0.9)
    for y in (48, 36):
        k = (56 - y) / 34
        c.stroke(line((34 + 4 * k, y), (58 - 4 * k, y)), 0.6)
        c.stroke(line((34 + 4 * k, y), (58 - 4 * (k + 0.35), y - 12)), 0.45)
    c.shape(rrect(30, 18, 32, 5, 1), 0.85)                           # railed top
    for x in (32, 46, 60):
        c.stroke(line((x, 18), (x, 12)), 0.5)
    c.stroke(line((30, 12), (62, 12)), 0.6)
    with c.at(46, 12, 1, 35):                                        # telescope, aimed up at the sky
        c.shape(rrect(-6, -4, 34, 8, 3), 0.85)
        c.shape(rrect(26, -5, 6, 10, 2), 0.7)
    sparkle(c, 14, 14, 8)                                            # the stars it watches: the vanilla
    sparkle(c, 30, -4, 5.5)                                          # Observatory's own sign for night science
    sparkle(c, 84, 40, 6.5)


# ---------------------------------------------------------------------------------------------- leisure

@b("PandabornHammock", 76, "Hammock: a striped sling between a tall bamboo mast and a short post, a panda's round "
                           "back and head showing above the cloth as it sleeps")
def hammock(c):
    ground(c, 4, 96)
    bamboo_post(c, 12, 4, 97, 1.15, nodes=3)                         # the tall mast
    c.stroke(line((88, 48), (88, 97)), 1.15, taper=0)                # the short post
    c.shape(circle(48, 62, 16), 0.9)                                 # the sleeper's round back
    c.shape(circle(69, 60, 9), 0.9)                                  # its head, an ear, a closed eye
    c.shape(circle(66, 51, 3.0), 0.7, filled=True)
    c.shape(circle(75, 53, 3.0), 0.7, filled=True)
    c.stroke(arc(71, 61, 2.6, 200, 340, ry=1.4), 0.55)
    top = spline((12, 20), (28, 50), (50, 65), (72, 65), (88, 52))
    bot = spline((88, 52), (76, 76), (50, 84), (27, 68), (12, 20))
    c.shape((top + bot).close())                                     # the sling
    for xa, ya, xb, yb in ((33, 56, 30, 71), (48, 65, 47, 82), (63, 66, 65, 81), (77, 62, 81, 68)):
        c.stroke(line((xa, ya + 1.5), (xb, yb - 1.5)), 0.5)          # its stripes


@b("PandabornNapPlatform", 86, "Nap platform: a slatted deck under a flat sloping canopy, round cushions to doze on")
def nap_platform(c):
    ground(c, 2, 98)
    c.shape(poly((4, 24), (96, 14), (98, 20), (6, 31)), 0.9)         # the flat canopy
    for x, y in ((10, 30), (90, 21)):
        c.stroke(line((x, y), (x, 88)), 0.9)
    c.shape(rrect(2, 86, 96, 9, 1))                                  # slatted deck on the ground
    for x in range(10, 94, 8):
        c.stroke(line((x, 87.5), (x, 93.5)), 0.42)
    napper(c, 18, 86, 1.25)
    napper(c, 62, 86, 1.25)


@b("PandabornTeahouse", 90, "Teahouse: a pavilion under a broad hipped roof with an awning, a big teapot and a cup "
                            "on the counter")
def teahouse(c):
    ground(c, 2, 98)
    roof_hip(c, 50, 4, 24, 100, 22)
    for x in (8, 92):
        c.stroke(line((x, 26), (x, 97)), 0.9)
    c.stroke(spline((8, 28), (20, 34), (32, 28), (44, 34), (56, 28), (68, 34), (80, 28), (92, 34)), 0.6)   # awning
    c.shape(rrect(18, 76, 64, 6, 2))                              # counter
    c.stroke(line((24, 82), (24, 97)), 0.7)
    c.stroke(line((76, 82), (76, 97)), 0.7)
    c.shape(spline((34, 74), (32, 58), (40, 50), (56, 50), (64, 58), (62, 74), closed=True))   # teapot
    c.shape(rrect(44, 44, 8, 6, 2), 0.8)
    c.stroke(spline((34, 62), (24, 58), (20, 50)), 1.0)           # spout
    c.stroke(spline((62, 56), (72, 56), (70, 68), (62, 70)), 0.9)  # handle
    c.shape(spline((70, 76), (70, 68), (80, 68), (80, 76), closed=True), 0.7)


@b("PandabornSlideAndSwing", 86, "Slide and swing: a curved bamboo slide beside a rope swing")
def slide_and_swing(c):
    ground(c, 2, 98)
    c.stroke(line((8, 97), (8, 40)), 0.9)                          # ladder
    c.stroke(line((18, 97), (18, 40)), 0.9)
    for y in (88, 76, 64, 52):
        c.stroke(line((8, y), (18, y)), 0.6)
    c.shape(rrect(6, 36, 20, 5, 1), 0.8)
    c.stroke(spline((24, 38), (34, 46), (42, 70), (54, 92), (62, 95)), 1.0)
    c.stroke(spline((26, 44), (34, 52), (40, 74), (52, 96)), 0.7)
    c.stroke(line((62, 97), (70, 20)), 0.9)                        # swing frame
    c.stroke(line((98, 97), (90, 20)), 0.9)
    c.stroke(line((66, 20), (94, 20)), 1.0)
    c.stroke(line((74, 21), (74, 72)), 0.6)
    c.stroke(line((86, 21), (86, 72)), 0.6)
    c.shape(rrect(70, 72, 20, 5, 2), 0.85)


@b("PandabornPandaKindergarten", 86, "Kindergarten: a little house with panda ears on its roof, a ball in the "
                                     "fenced yard")
def panda_kindergarten(c):
    ground(c, 2, 98)
    for x in (54, 64, 74, 84, 94):                                 # yard fence
        c.stroke(line((x, 74), (x, 97)), 0.7)
    c.stroke(line((52, 80), (98, 80)), 0.6)
    c.stroke(line((52, 90), (98, 90)), 0.6)
    c.shape(circle(28, 30, 9), 0.9)                                # panda ears on the roof
    c.shape(circle(72, 30, 9), 0.9)
    house(c, 50, 97, 56, 34, 26, windows=0)
    round_window(c, 32, 76, 6)
    c.shape(circle(84, 90, 8), 0.85)                               # ball, in front of the fence
    c.stroke(arc(84, 90, 8, 60, 240, ry=3), 0.5)


@b("PandabornInkStudio", 84, "Ink studio: a hanging painting of misty mountains, a brush on its rest, an inkstone")
def ink_studio(c):
    c.stroke(line((22, 4), (78, 4)), 1.0)                          # hanging rod
    c.stroke(spline((40, 4), (50, -4), (60, 4)), 0.6)
    c.shape(rrect(26, 6, 48, 62, 1), 0.9)                         # the painting
    c.stroke(spline((30, 52), (40, 30), (48, 44), (56, 22), (70, 52)), 0.8)   # mountains
    c.stroke(spline((34, 58), (50, 54), (66, 58)), 0.55)          # mist
    c.fill(circle(62, 16, 3))                                     # sun
    c.stroke(line((22, 68), (78, 68)), 1.0)                        # weighted bottom rod
    c.shape(rrect(14, 84, 34, 10, 3), 0.9)                        # inkstone
    c.shape(ellipse(24, 89, 6, 2.5), 0.6, filled=True)
    c.shape(spline((54, 92), (58, 84), (66, 84), (70, 92), closed=True), 0.8)    # brush rest
    with c.at(62, 80, 1, -8):
        c.stroke(line((-22, 0), (14, 0)), 1.0)
        c.shape(spline((14, -3), (26, 0), (14, 3), closed=True), 0.8)
    ground(c, 6, 94)


@b("PandabornHotSpringBath", 86, "Hot spring bath: a rock-ringed pool with steam and a bamboo spout pouring in")
def hot_spring_bath(c):
    c.shape(ellipse(50, 78, 46, 17))
    c.shape(ellipse(50, 76, 34, 10))
    c.stroke(spline((26, 76), (36, 74), (44, 77)), 0.55)
    for x, y, r in ((8, 76, 7), (18, 88, 8), (36, 94, 7), (64, 94, 8), (82, 88, 7), (92, 76, 6)):
        c.shape(ellipse(x, y, r * 1.3, r), 0.85)
    c.stroke(line((96, 40), (96, 70)), 1.0)                        # spout post
    with c.at(98, 40, 1, 168):
        c.shape(rrect(0, -4, 30, 8, 4), 0.85)
    c.stroke(spline((70, 50), (68, 60), (68, 70)), 0.6)
    steam(c, 36, 62, 20)
    steam(c, 50, 58, 22)
    steam(c, 64, 62, 18)


@b("PandabornOperaStage", 96, "Opera stage: a raised roofed stage, curtains drawn back, an opera mask. An ordinary "
                              "attraction since 2026-11-25 (DESIGN.md), so it carries no moon mark")
def opera_stage(c):
    roof_side(c, 8, 80, 10, 28, ribs=10)
    for x in (10, 82):
        c.stroke(line((x, 28), (x, 72)), 1.0)
    c.stroke(spline((12, 30), (20, 44), (14, 60)), 0.8)            # curtains
    c.stroke(spline((80, 30), (72, 44), (78, 60)), 0.8)
    # mask: an opera face with bold brows and eye patches (plain pattern)
    c.shape(spline((32, 36), (46, 32), (60, 36), (60, 50), (54, 62), (46, 66), (38, 62), (32, 50), closed=True))
    c.fill(spline((36, 44), (40, 40), (44, 46), (40, 48), closed=True))
    c.fill(spline((56, 44), (52, 40), (48, 46), (52, 48), closed=True))
    c.stroke(spline((36, 38), (46, 42), (56, 38)), 0.6)
    c.stroke(spline((42, 56), (46, 58), (50, 56)), 0.6)
    c.shape(rrect(2, 72, 96, 8, 1))                               # stage floor
    c.shape(rrect(6, 80, 88, 17, 1), 0.9)
    for x in (28, 50, 72):
        c.stroke(line((x, 82), (x, 95)), 0.5)


# ------------------------------------------------------------------------------------- Ringtail posts
# Each night post is its daytime counterpart's job plus the moon: builders (mallet and pole), couriers (the
# back-basket), gatherers (bamboo mushrooms in a basket). A lantern on each: they work after dark.

@b("PandabornNightBuildersPost", 86, "Night builders' post (Ringtails): the model's shear legs, two lashed bamboo "
                                     "spars and a guy rope, a lantern hung from the top, and a mallet", moon=True)
def night_builders_post(c):
    ground(c, 4, 92)
    c.stroke(line((33, 12), (70, 97)), 0.55)                         # the guy rope
    c.stroke(line((6, 97), (36, 4)), 1.15, taper=0)                  # the shear legs, crossed and lashed at the top
    c.stroke(line((50, 97), (26, 4)), 1.15, taper=0)
    c.stroke(line((25, 17), (37, 17)), 1.0, taper=0)
    box_lantern(c, 31, 18, 1.05, string=14)
    with c.at(72, 72, 1, 40):                                        # the builders' mallet
        c.stroke(line((-24, 0), (10, 0)), 1.0)
        c.shape(rrect(10, -9, 12, 18, 3), 0.9)


@b("PandabornNightCourierPost", 82, "Night courier post (Ringtails): a woven back-basket with a lantern hung on it",
   moon=True)
def night_courier_post(c):
    ground(c, 6, 94)
    basket = spline((20, 40), (16, 70), (26, 94), (66, 94), (76, 70), (72, 40), closed=False)
    region = (basket + line((72, 40), (20, 40))).close()
    c.shape(region)
    for seg in hatch(region, 10, 90, margin=3) + hatch(region, 12, 0, margin=3):
        c.stroke(seg, 0.45)
    c.shape(ellipse(46, 40, 26, 6))
    c.stroke(spline((24, 40), (20, 20), (30, 12)), 0.8)            # straps
    c.stroke(spline((68, 40), (72, 20), (62, 12)), 0.8)
    c.stroke(line((72, 46), (86, 46)), 0.7)
    lantern(c, 86, 46, 0.75)


@b("PandabornNightForagersPost", 82, "Night gatherers' post (Ringtails): a basket of bamboo mushrooms and a lantern "
                                     "on a bamboo pole", moon=True)
def night_foragers_post(c):
    ground(c, 6, 94)
    bamboo_post(c, 80, 28, 97, 0.9, nodes=1)
    c.stroke(line((80, 30), (68, 30)), 0.7)
    lantern(c, 68, 30, 0.75)
    mushroom(c, 30, 70, 34, 1.15)
    mushroom(c, 48, 72, 40, 1.15)
    basket = (spline((12, 66), (16, 90), (36, 96), (56, 90), (60, 66))).close()
    c.shape(basket)
    for seg in hatch(basket, 9, 90, margin=3):
        c.stroke(seg, 0.45)


# -------------------------------------------------------------------------------------- monuments

@b("PandabornMemorialArch", 92, "Memorial arch: a timber gateway on drum-stone feet under one broad tiled roof, a "
                                "blank panel, a lantern cage with its flame hanging in the opening")
def memorial_arch(c):
    ground(c, 2, 98)
    for x in (20, 80):
        c.stroke(line((x, 30), (x, 88)), 1.4)
        c.shape(ellipse(x, 90, 9, 7), 0.85)                          # drum stones
        c.shape(ellipse(x, 84, 6, 3), 0.6)
    c.stroke(line((12, 36), (88, 36)), 1.1)                          # lintel
    c.shape(rrect(28, 38, 44, 14, 1), 0.85)                          # blank panel, no writing
    roof_side(c, 6, 94, 8, 30, ribs=10)
    c.stroke(line((50, 52), (50, 58)), 0.6)                          # lantern cage and flame
    c.shape(rrect(42, 58, 16, 18, 2), 0.8)
    c.fill(spline((50, 61), (54, 68), (50, 73), (46, 68), closed=True))


@b("PandabornGreatSittingPanda", 98, "Great sitting panda: a big seated panda holding bamboo, carved into a rock "
                                     "outcrop, water at its feet")
def great_sitting_panda(c):
    c.shape(spline((2, 86), (6, 50), (14, 24), (30, 8), (50, 2), (72, 8), (88, 26), (96, 52), (98, 86),
                   closed=True), 0.9)                              # rock outcrop
    c.stroke(spline((8, 60), (14, 48)), 0.5)
    c.stroke(spline((92, 62), (88, 48)), 0.5)
    c.shape(spline((24, 84), (22, 60), (32, 44), (50, 40), (68, 44), (78, 60), (76, 84), closed=True))
    c.shape(circle(37, 18, 6), 0.9)
    c.shape(circle(63, 18, 6), 0.9)
    c.shape(circle(50, 30, 15))
    c.fill(ellipse(44, 29, 3.5, 4.5, rot=-30))
    c.fill(ellipse(56, 29, 3.5, 4.5, rot=30))
    c.fill(ellipse(50, 36, 2.5, 1.8))
    with c.at(58, 58, 1, 62):                                       # the bamboo it holds
        c.stroke(line((-24, 0), (30, 0)), 1.1, taper=0, halo=0.8)
        c.stroke(line((6, -3), (6, 3)), 0.6, taper=0)
    c.shape(spline((60, 22), (72, 14), (80, 18), (70, 24), closed=True), 0.7)   # its leaf
    c.stroke(spline((30, 52), (40, 62), (54, 62)), 0.8)            # paws round it
    c.shape(ellipse(34, 84, 10, 6), 0.9)                           # feet
    c.shape(ellipse(66, 84, 10, 6), 0.9)
    c.erase(rrect(0, 89, 100, 14, 0))                              # water at its feet, in front
    water(c, 92, 0, 100)


@b("PandabornSkyLantern", 100, "Sky Lantern (wonder): a great round paper lantern on a lashed bamboo launch tower "
                               "over a stepped stone terrace")
def sky_lantern(c):
    c.shape(rrect(2, 90, 96, 8, 1), 0.85)                            # stepped terrace
    c.shape(rrect(14, 82, 72, 8, 1), 0.85)
    for x in (6, 94):                                                # tethers to the terrace corners
        c.stroke(line((50 + (x - 50) * 0.42, 34), (x, 90)), 0.5)
    for x in (26, 74):                                               # the launch tower
        c.stroke(line((x, 82), (x + (50 - x) * 0.4, 50)), 1.0)
    c.stroke(line((30, 72), (70, 72)), 0.7)
    c.stroke(line((30, 72), (68, 60)), 0.5)
    c.shape(rrect(32, 48, 36, 5, 1), 0.85)                           # tower head
    c.shape(spline((50, 2), (70, 8), (76, 24), (70, 40), (58, 46), (42, 46), (30, 40), (24, 24), (30, 8),
                   closed=True))                                     # the great paper lantern
    for k in (0.38, 0.75):
        c.stroke(spline((50 - 26 * k, 5), (50 - 30 * k, 24), (50 - 22 * k, 45)), 0.55)
        c.stroke(spline((50 + 26 * k, 5), (50 + 30 * k, 24), (50 + 22 * k, 45)), 0.55)
    c.shape(rrect(42, 0, 16, 4, 1.5), 0.7)                            # top ring
    c.fill(spline((50, 36), (53, 42), (50, 46), (47, 42), closed=True))   # the flame showing below


# ------------------------------------------------------------------------------------------- decoration
# Small things, drawn small as vanilla draws its lantern, shrub and fence.

@b("PandabornStandingLantern", 64, "Standing lantern: a wooden post on a stone foot, a hatted paper lantern on its arm")
def standing_lantern(c):
    c.shape(rrect(20, 88, 24, 9, 2), 0.85)
    c.stroke(line((30, 88), (30, 8)), 1.2)
    c.stroke(line((30, 12), (64, 12)), 1.0)
    c.stroke(line((34, 12), (30, 22)), 0.6)
    box_lantern(c, 60, 12, 1.0, 5)


@b("PandabornHangingLantern", 64, "Hanging lantern: a paper lantern hung from a bar between two bamboo posts")
def hanging_lantern(c):
    for x0, x1 in ((24, 14), (76, 86)):                              # two splayed bamboo posts
        c.stroke(line((x0, 12), (x1, 97)), 0.85, taper=0)
        c.stroke(line((x0 + (x1 - x0) * 0.5 - 3, 54), (x0 + (x1 - x0) * 0.5 + 3, 54)), 0.55, taper=0)
    c.stroke(spline((2, 8), (50, 12), (98, 8)), 1.0)                 # the bar, reaching past them
    box_lantern(c, 50, 11, 2.2, 2)


@b("PandabornStringLanterns", 70, "String of lanterns: small round lanterns along a sagging cord between two poles")
def string_lanterns(c):
    ground(c, 2, 98)
    bamboo_post(c, 6, 14, 97, 0.9, nodes=2)
    bamboo_post(c, 94, 14, 97, 0.9, nodes=2)
    cord = spline((6, 18), (30, 30), (50, 33), (70, 30), (94, 18))
    c.stroke(cord, 0.6)
    for x in (22, 40, 58, 76):
        y = float(np.interp(x, cord.pts[:, 0], cord.pts[:, 1]))
        c.shape(ellipse(x, y + 7, 5.5, 6.5), 0.75)
        c.stroke(line((x, y + 13.5), (x, y + 17)), 0.5)


@b("PandabornBambooFence", 66, "Bamboo fence: jointed posts, two rails and a lashed lattice")
def bamboo_fence(c):
    ground(c, 2, 98)
    for x in (8, 50, 92):
        bamboo_post(c, x, 26, 97, 1.1, nodes=1)
        c.shape(ellipse(x, 26, 3.5, 1.5), 0.6)
    for y in (40, 78):
        c.stroke(line((4, y), (96, y)), 0.9, taper=0)
    for x0 in (8, 50):
        c.stroke(line((x0 + 4, 76), (x0 + 38, 42)), 0.6)
        c.stroke(line((x0 + 38, 76), (x0 + 4, 42)), 0.6)


@b("PandabornPottedPine", 62, "Potted pine: a crooked pine with three cloud-shaped pads in a hexagonal pot")
def potted_pine(c):
    c.shape(poly((20, 70), (80, 70), (74, 97), (26, 97)), 0.9)        # pot
    c.shape(rrect(16, 66, 68, 6, 1.5), 0.85)
    c.stroke(line((40, 72), (40, 96)), 0.5)
    c.stroke(line((60, 72), (60, 96)), 0.5)
    c.stroke(spline((48, 66), (54, 54), (42, 42), (52, 28), (46, 16)), 1.4)   # trunk
    c.stroke(spline((44, 42), (30, 40)), 0.8)
    c.stroke(spline((50, 32), (64, 30)), 0.8)

    def pad(x, y, w):
        c.shape(spline((x - w, y + 2), (x - w * 0.6, y - 5), (x - w * 0.15, y - 3), (x + w * 0.2, y - 7),
                       (x + w * 0.65, y - 4), (x + w, y + 2), closed=True), 0.85)
    pad(28, 40, 18)
    pad(66, 30, 18)
    pad(46, 14, 16)


@b("PandabornPandaStatue", 66, "Panda statue: a seated panda munching bamboo on a square stone plinth")
def panda_statue(c):
    c.shape(rrect(16, 72, 68, 25, 2))                                 # plinth
    c.stroke(line((18, 78), (82, 78)), 0.5)
    c.shape(spline((26, 72), (24, 50), (36, 36), (64, 36), (76, 50), (74, 72), closed=True))   # body
    c.shape(circle(37, 12, 5.5), 0.9)
    c.shape(circle(63, 12, 5.5), 0.9)
    c.shape(circle(50, 24, 14))
    c.fill(ellipse(44, 23, 3.2, 4.2, rot=-30))
    c.fill(ellipse(56, 23, 3.2, 4.2, rot=30))
    c.fill(ellipse(50, 30, 2.3, 1.6))
    with c.at(60, 50, 1, 70):                                        # bamboo in its paws
        c.stroke(line((-16, 0), (26, 0)), 1.0, taper=0, halo=0.8)
    c.stroke(spline((32, 48), (42, 56), (56, 54)), 0.8)


@b("PandabornBambooPinwheel", 66, "Bamboo pinwheel: a four-bladed paper pinwheel and a tail vane on a bamboo pole")
def bamboo_pinwheel(c):
    c.shape(rrect(36, 90, 28, 7, 2), 0.85)
    bamboo_post(c, 50, 36, 90, 1.1, nodes=2)
    c.stroke(line((50, 36), (90, 36)), 0.8)                          # tail arm and vane
    c.shape(poly((80, 28), (94, 30), (94, 42), (80, 44)), 0.8)
    for k in range(4):                                               # the blades, curled
        with c.at(42, 30, 1, k * 90 + 20):
            c.shape(spline((0, 0), (20, -2), (16, 10), (4, 4), closed=True), 0.8)
    c.shape(circle(42, 30, 3), 0.8, filled=True)


@b("PandabornGoldfishBowl", 66, "Goldfish bowl: a wide glazed basin on a wooden stand, lily pads, a goldfish leaping")
def goldfish_bowl(c):
    for x0, x1 in ((24, 18), (76, 82), (50, 50)):                    # stand legs
        c.stroke(line((x0, 72), (x1, 97)), 1.0)
    c.stroke(line((22, 88), (78, 88)), 0.6)
    c.shape(spline((8, 40), (12, 62), (30, 76), (70, 76), (88, 62), (92, 40), closed=True))     # basin
    c.shape(ellipse(50, 40, 42, 9))
    c.shape(ellipse(50, 40, 36, 6.5), 0.6)
    for x, y in ((36, 41), (60, 39)):                                # lily pads
        c.shape((arc(x, y, 7, 30, 330, ry=2.6) + line((x + 6, y - 1.3), (x, y))).close(), 0.55)
    with c.at(62, 22, 1, -25):                                       # the goldfish
        c.shape(spline((-10, 0), (0, -5), (10, 0), (0, 5), closed=True), 0.8)
        c.shape(poly((-9, 0), (-17, -6), (-15, 0), (-17, 6)), 0.7)
        c.dot(5, -1, 0.5)


@b("PandabornGardenMoonGate", 72, "Garden moon gate: a white wall with a round opening, a tiled coping, a potted "
                                  "bamboo at its foot")
def garden_moon_gate(c):
    ground(c, 2, 98)
    wall = rrect(10, 22, 80, 75, 1)
    c.shape(wall)
    c.shape(circle(50, 58, 25), 0.95)
    c.erase(circle(50, 58, 23))
    c.shape(circle(50, 58, 21), 0.6, occlude=False)
    c.stroke(line((10, 97), (90, 97)))
    roof_side(c, 8, 92, 10, 24, ribs=8, inset=3, over=3)
    c.shape(poly((70, 84), (88, 84), (85, 97), (73, 97)), 0.8)        # pot of bamboo
    for x, top in ((76, 52), (81, 60)):
        c.stroke(line((x, 84), (x, top)), 0.7, taper=0)
    c.shape(spline((76, 56), (66, 50), (72, 58), closed=True), 0.55)


@b("PandabornPoleMill", 90, "Pole mill (the Inkpaws' lumber mill): a saw bench splitting a log, a lashed bundle of "
                            "hollow bamboo-like poles beside it")
def pole_mill(c):
    # the vanilla Wood workshops are a plain house outline with their product inside (gear, paper, plank); the
    # Inkpaws' mill shows a lashed bundle of poles instead of the plank
    c.stroke(line((10, 96), (90, 96)), 1.0)
    c.stroke(line((16, 92), (16, 50)), 1.0)
    c.stroke(line((84, 92), (84, 50)), 1.0)
    c.stroke(line((6, 56), (50, 14), (94, 56)), 1.0)
    for k in range(3):                                               # the bundle of poles, ends towards you
        with c.at(30 + k * 5, 84 - k * 9, 1, 32):
            c.shape(rrect(0, -4.5, 46, 9, 4.5), 0.85)
            c.stroke(line((24, -4.5), (24, 4.5)), 0.55)
            c.shape(ellipse(0, 0, 3, 4.5), 0.7)
    c.stroke(spline((52, 76), (56, 66), (58, 58)), 1.1, halo=0.6)    # the lashing
