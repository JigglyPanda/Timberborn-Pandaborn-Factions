"""Goods icons for the Inkpaws. One short function per good; see ink.py for the drawing calls.

Conventions (taken from the vanilla goods set):
* draw in a ~100 x 100 box, y down; the renderer fits and centres the result
* back to front: later shapes hide what is behind them
* a processed good = the product, plus a hint of its ingredient or process when that helps
  (vanilla: flour = sack + plant, grilled = steam lines, fermented = bubbles, treated = sparkles)
* few lines: at 80 px the pen is ~6 units wide, so keep parallel lines 9+ units apart
* no writing or characters anywhere; plain patterns only; nothing Japanese-coded
"""
import math

import numpy as np

from ink import Path, arc, circle, ellipse, hatch, icon, line, rrect, spline

# --------------------------------------------------------------------------------------------- shared motifs


def steam(c, x, y, h=22, w=1.0):
    """One rising wisp starting at (x, y), going up h units."""
    c.stroke(spline((x, y), (x + 4, y - h * 0.33), (x - 4, y - h * 0.66), (x + 1, y - h)), w)


def pole(c, length, r, nodes=(0.45,), face="ring", solid=False):
    """A bamboo pole along +x from its cut face at x=0 to x=length, radius r. Use inside c.at(...).

    Nodes bulge the outline slightly and get a ring line; face is "ring" (hollow), "fill" (solid with a hole)."""
    fx = r * 0.42                                       # half-width of the cut face ellipse (perspective)
    top, bot = [(0, -r)], [(0, r)]
    for t in sorted(nodes):
        x = length * t
        top += [(x - 4, -r), (x - 1.2, -r - 1.6), (x + 1.2, -r - 1.6), (x + 4, -r)]
        bot += [(x - 4, r), (x - 1.2, r + 1.6), (x + 1.2, r + 1.6), (x + 4, r)]
    top.append((length, -r))
    bot.append((length, r))
    body = Path(np.asarray(top)) + arc(length, 0, fx, 90, -90, ry=r) + Path(np.asarray(bot[::-1])) \
        + arc(0, 0, fx, 270, 90, ry=r)
    c.shape(body.close(), filled=solid)
    for t in nodes:
        if solid:
            c.erase(arc(length * t, 0, fx, 80, 280, ry=r * 0.92), 0.55)
        else:
            c.stroke(arc(length * t, 0, fx, 80, 280, ry=r * 0.92), 0.8)
    if solid:
        c.erase(ellipse(0, 0, fx + 1.5, r + 1.5), 0.55)
        c.fill(ellipse(0, 0, fx - 1.2, r - 1.2))
        c.erase(ellipse(0, 0, fx * 0.42, r * 0.5))
    else:
        c.shape(ellipse(0, 0, fx, r), filled=(face == "fill"))
        if face == "fill":
            c.erase(ellipse(0, 0, fx * 0.45, r * 0.52))
        else:
            c.stroke(ellipse(0, 0, fx * 0.42, r * 0.5), 0.7)


def leaf(c, x, y, length, width, ang, w=0.8, vein=True):
    """A narrow pointed leaf from its base at (x, y) along `ang` degrees."""
    with c.at(x, y, 1, ang):
        c.shape(spline((0, 0), (length * 0.35, -width / 2), (length, 0), (length * 0.35, width / 2), closed=True), w)
        if vein:
            c.stroke(line((2, 0), (length * 0.7, 0)), 0.55)


def grain(c, x, y, ang=0.0, s=1.0, filled=True, halo=0.0):
    """A single rice-like grain (a pointed oval) at (x, y), long axis at `ang` degrees.
    `halo` (px) clears a thin gap around a filled grain so neighbours stay separate."""
    with c.at(x, y, s, ang):
        g = spline((-7, 0), (-3, -3.4), (4, -2.8), (7.5, 0), (4, 2.8), (-3, 3.4), closed=True)
        if filled and halo:
            c.shape(g, 0.3, filled=True, halo=halo)
        elif filled:
            c.fill(g)
        else:
            c.shape(g, 0.8)


def chili(c, x, y, ang=0.0, s=1.0):
    """A curved chili pepper with its cap and stalk; base at (x, y), pointing along `ang`."""
    with c.at(x, y, s, ang):
        c.shape(spline((0, -6), (16, -6), (30, -2), (40, 8), (28, 5), (14, 6), (0, 6), closed=True))
        c.shape(spline((-7, -7), (1, -7), (3, 0), (1, 7), (-7, 7), (-5, 0), closed=True))
        c.stroke(spline((-6, 0), (-12, -2), (-15, -7)), 0.8)


def rice_ear(c, x=0, y=0, s=1.0, grains=11, gs=1.25):
    """A drooping rice ear on its stalk, base at (x, y): solid grains packed along the bent tip."""
    with c.at(x, y, s):
        stalk = spline((0, 0), (2, -40), (12, -66), (30, -78), (46, -72), (54, -50))
        c.stroke(stalk, 0.8)
        pts = stalk.pts
        n = len(pts)
        for i in range(grains):
            k = min(n - 2, int(n * (0.48 + 0.52 * i / (grains - 1))))
            px, py = pts[k]
            dx, dy = pts[k + 1] - pts[k - 1]
            side = 1 if i % 2 else -1
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            ang = -math.degrees(math.atan2(dy, dx)) - 18 * side
            grain(c, px + nx * 5 * side, py + ny * 5 * side, ang, gs, halo=0.7)


def bowl_body(c, cx, rim_y, rx, ry, depth, foot=0.36):
    """Front of a round bowl in 3/4 view: lower half of the rim plus the belly down to a foot ring."""
    fr = rx * foot
    by = rim_y + depth
    body = (arc(cx, rim_y, rx, 180, 360, ry=ry)
            + spline((cx + rx, rim_y), (cx + rx * 0.86, rim_y + depth * 0.6), (cx + fr * 1.3, by - 2), (cx + fr, by))
            + line((cx - fr, by))
            + spline((cx - fr, by), (cx - fr * 1.3, by - 2), (cx - rx * 0.86, rim_y + depth * 0.6), (cx - rx, rim_y)))
    c.shape(body.close())
    c.shape(rrect(cx - fr, by - 1, fr * 2, 8, 2))


# ----------------------------------------------------------------------------------------------- raw food

@icon("PandabornBambooShoots", note="Two bamboo shoots: plump curved cones wrapped in sheaths, root band at the base")
def bamboo_shoots(c):
    def shoot():
        # the whole shoot (the innermost sheath), tip bent to the right
        left = [(24, 88), (21, 68), (26, 46), (37, 24), (50, 8), (60, 0)]
        right = [(60, 0), (65, 10), (71, 28), (78, 50), (80, 70), (77, 88)]
        c.shape(spline(*left, *right[1:], closed=True))
        # outer sheaths, top to bottom: each covers the shoot below a sagging edge that ends in a small point
        c.shape(spline((35, 28), (46, 34), (58, 30), (70, 16), (72, 30), (78, 50), (80, 70), (77, 88), (24, 88),
                       (21, 68), (26, 46), closed=True))
        c.shape(spline((77, 46), (64, 54), (44, 54), (28, 40), (24, 56), (21, 68), (24, 88), (77, 88), (80, 70),
                       closed=True))
        c.shape(spline((21, 70), (36, 78), (58, 76), (82, 58), (80, 72), (77, 88), (24, 88), closed=True))
        # root band with root nubs
        c.shape(spline((26, 86), (50, 88), (75, 86), (73, 97), (50, 99), (28, 97), closed=True))
    with c.at(-28, 26, 0.7):
        shoot()
    shoot()


def calyx(c, x, y, r):
    """The persimmon's cap seen from the side: a wide flat collar of four sepals (left, right, a front one
    lying on the fruit, the back one behind the stem), as wide as the fruit's shoulders, with a stem stub."""
    with c.at(x, y, r / 30):
        c.shape(spline((-31, 1), (-22, -6), (-10, -8), (-4, -13), (4, -13), (10, -8), (22, -6), (31, 1), (18, 2),
                       (8, 4), (0, 13), (-8, 4), (-18, 2), closed=True), 0.9)
        c.stroke(line((-24, -1), (-10, -3)), 0.5)
        c.stroke(line((24, -1), (10, -3)), 0.5)
        c.stroke(line((0, 9), (0, 0)), 0.5)
        c.shape(rrect(-4, -20, 8, 10, 3), 0.9)


@icon("PandabornPersimmons", note="Two squat persimmons, each with its wide flat four-sepal cap")
def persimmons(c):
    def fruit(x, y, s):
        with c.at(x, y, s):
            c.shape(spline((-34, -8), (-28, -19), (-12, -22), (12, -22), (28, -19), (34, -8), (30, 12), (0, 22),
                           (-30, 12), closed=True))
            calyx(c, 0, -20, 30)
    fruit(30, 36, 0.8)
    fruit(58, 66, 1.08)


@icon("PandabornBambooMushrooms", note="Bamboo mushroom (zhusun): thimble cap, white stem, lacy net veil")
def bamboo_mushrooms(c):
    c.shape(spline((36, 102), (34, 95), (42, 90), (58, 90), (66, 95), (64, 102), closed=True))
    c.shape(rrect(43, 66, 14, 28, 3))
    hem = []
    for k in range(9):
        x = 10 + k * 10
        hem.append((x, 84 + (5 if k % 2 else 0)))
    skirt = spline((36, 34), (28, 48), (18, 68), (10, 84)) + spline(*hem) + spline((90, 84), (82, 68), (72, 48),
                                                                                   (64, 34))
    skirt = skirt.close()
    c.shape(skirt, 0.9)
    for seg in hatch(skirt, 13, 60, margin=4) + hatch(skirt, 13, -60, margin=4):
        c.stroke(seg, 0.55)
    # conical cap, wider than the top of the veil
    c.shape(spline((28, 40), (34, 22), (44, 8), (50, 5), (56, 8), (66, 22), (72, 40), (50, 45), closed=True))
    c.stroke(spline((38, 30), (50, 33), (62, 30)), 0.55)
    c.stroke(spline((44, 18), (50, 20), (56, 18)), 0.55)


@icon("PandabornCabbage", note="Napa cabbage: a tall barrel head, frilly leaf tops, broad white ribs")
def cabbage(c):
    with c.at(50, 52, 1, -16):
        with c.at(-50, -52):
            frill = [(26, 30), (24, 18), (32, 8), (40, 12), (46, 4), (54, 9), (62, 3), (70, 10), (76, 18), (76, 30)]
            c.shape(spline((50, 102), (30, 92), (22, 64), (24, 40), *frill, (80, 54), (74, 88), closed=True))
            front = [(34, 32), (40, 24), (46, 28), (52, 22), (58, 28), (64, 26), (66, 36)]
            c.shape(spline((50, 102), (36, 94), (30, 70), *front, (68, 64), (64, 92), closed=True))
            c.stroke(spline((44, 98), (40, 70), (40, 44)), 0.8)
            c.stroke(spline((56, 98), (58, 70), (58, 44)), 0.8)


def split_husk(c, x, y, r=13, ang=0.0, open_deg=34):
    """A Sichuan pepper husk split open like a tiny clam: two half-shells hinged at the bottom, seed between."""
    with c.at(x, y, 1, ang):
        half = arc(0, -r, r, 90, 270) + line((0, 0), (0, -2 * r))
        with c.at(0, 0, 1, open_deg):
            c.shape(half.close())
        with c.at(0, 0, 1, -open_deg, sx=-1, sy=1):
            c.shape(half.close())
        c.shape(circle(0, -r * 1.1, r * 0.48), 0.4, filled=True, halo=0.9)


def open_husk(c, x, y, r=12):
    """A Sichuan pepper husk split open at the top, its round black seed sitting in the opening."""
    c.shape(circle(x, y, r))
    c.erase(arc(x, y, r, 55, 125), 1.4)
    c.shape(circle(x, y - r * 0.55, r * 0.52), 0.4, filled=True, halo=0.9)


@icon("PandabornSichuanPepper", note="Sichuan pepper: three husks split open on their black seeds, a pinnate leaf sprig")
def sichuan_pepper(c):
    c.stroke(spline((96, 2), (74, 18), (50, 34)), 0.8)
    for t, side in ((0.3, 1), (0.3, -1), (0.62, 1), (0.62, -1)):
        x, y = 96 - 46 * t, 2 + 32 * t
        leaf(c, x, y, 17, 9, 215 + 50 * side, 0.75, vein=False)
    leaf(c, 50, 34, 18, 9, 215, 0.75, vein=False)
    open_husk(c, 26, 66, 14)
    open_husk(c, 58, 72, 14)
    open_husk(c, 40, 92, 13)
    c.shape(circle(78, 94, 5.5), 0.5, filled=True)


# ------------------------------------------------------------------------------------------- crops, plants

@icon("PandabornRice", note="A drooping rice ear on its stalk, with a leaf")
def rice(c):
    c.stroke(spline((30, 100), (20, 80), (4, 64)), 1.0)
    rice_ear(c, 32, 100, 1.0)


@icon("PandabornTeaLeaves", note="Tea: one bud and two leaves on a sprig")
def tea_leaves(c):
    c.stroke(spline((52, 98), (50, 70), (48, 40)), 1.0)
    c.shape(spline((50, 70), (34, 66), (14, 52), (6, 38), (22, 40), (40, 52), closed=True))
    c.stroke(spline((48, 68), (30, 56), (12, 42)), 0.7)
    c.shape(spline((50, 56), (64, 48), (84, 42), (96, 28), (80, 26), (60, 36), closed=True))
    c.stroke(spline((52, 54), (70, 42), (90, 30)), 0.7)
    c.shape(spline((48, 44), (40, 30), (44, 12), (50, 2), (56, 14), (56, 32), closed=True))
    c.stroke(spline((49, 40), (49, 22), (50, 8)), 0.6)


@icon("PandabornBambooSeed", note="Bamboo seed: a pile of pale grains in a round woven tray")
def bamboo_seed(c):
    c.shape(ellipse(50, 62, 46, 15))
    pile = [(30, 60, 20), (50, 62, -10), (70, 60, 25), (40, 47, -30), (60, 47, 15), (50, 34, 0)]
    for x, y, a in pile:
        grain(c, x, y, a, 1.75, filled=False)
    front = arc(50, 62, 46, 180, 360, ry=15) + arc(50, 72, 44, 0, -180, ry=15)
    front = front.close()
    c.shape(front)
    for seg in hatch(front, 14, 70, margin=3):
        c.stroke(seg, 0.55)


# ------------------------------------------------------------------------------------------------- dishes

@icon("PandabornSteamedRice", note="A bowl heaped with rice, rising steam")
def steamed_rice(c):
    rim_y, rx, ry = 56, 40, 10
    c.shape(spline((10, rim_y), (16, 40), (34, 30), (50, 28), (66, 30), (84, 40), (90, rim_y), closed=True))
    for x, y, a in ((36, 44, 20), (54, 38, -10), (66, 48, 30)):
        grain(c, x, y, a, 0.75)
    bowl_body(c, 50, rim_y, rx, ry, 34)
    steam(c, 36, 22, 18)
    steam(c, 52, 18, 18)
    steam(c, 68, 22, 18)


@icon("PandabornSteamedShoots", note="Steamed shoots: a round bamboo steamer with a woven lid, steam, a halved shoot")
def steamed_shoots(c):
    # a round bamboo steamer: one woven tier and a lid with a cross-woven top; steam from the top
    rx, ry = 38, 10
    lid_top = ellipse(50, 30, rx - 3, ry - 1)
    for y in (52,):
        c.shape((arc(50, y, rx, 180, 360, ry=ry) + line((88, y), (88, y + 24))
                 + arc(50, y + 24, rx, 0, -180, ry=ry) + line((12, y + 24), (12, y))).close())
    c.shape((arc(50, 34, rx, 180, 360, ry=ry) + line((88, 34), (87, 30)) + arc(50, 30, rx - 1, 0, 180, ry=ry)
             + line((13, 30), (12, 34))).close())
    c.shape(lid_top)
    for seg in hatch(lid_top, 11, 45, margin=3) + hatch(lid_top, 11, -45, margin=3):
        c.stroke(seg, 0.5)
    steam(c, 40, 16, 16, 0.9)
    steam(c, 60, 16, 16, 0.9)
    # a halved shoot lying in front
    with c.at(70, 90, 0.8, 8):
        c.shape(spline((-30, 6), (-30, -6), (-10, -10), (14, -6), (34, 0), (14, 6), (-10, 10), closed=True))
        c.stroke(spline((-20, -8), (-12, 0), (-20, 8)), 0.6)


@icon("PandabornSweetRiceBalls", note="Tangyuan: three glossy rice balls in a bowl, porcelain spoon")
def rice_balls(c):
    rim_y, rx, ry = 52, 44, 13
    c.shape(ellipse(50, rim_y, rx, ry))
    c.shape(spline((62, 48), (76, 28), (90, 12), (96, 11), (94, 17), (80, 32), (68, 52), closed=True), 0.9)
    for x, y in ((30, 46), (52, 42), (42, 56)):
        c.shape(circle(x, y, 13))
    bowl_body(c, 50, rim_y, rx, ry, 30, foot=0.34)


@icon("PandabornPickles", note="Pickles: a bellied pao cai jar with water-seal collar and bowl lid, a chili")
def pickles(c):
    c.shape(spline((34, 30), (16, 44), (10, 64), (18, 86), (34, 96), (66, 96), (82, 86), (90, 64), (84, 44),
                   (66, 30), closed=True))
    c.stroke(arc(50, 62, 38, 190, 350, ry=9), 0.7)
    c.stroke(arc(50, 71, 37, 192, 348, ry=9), 0.7)
    c.shape(spline((18, 30), (28, 38), (50, 40), (72, 38), (82, 30), (50, 24), closed=True))
    c.shape(spline((28, 30), (32, 18), (44, 12), (56, 12), (68, 18), (72, 30), (50, 33), closed=True))
    c.shape(rrect(44, 4, 12, 9, 3))
    # fermentation bubbles, the vanilla convention for fermented goods
    c.shape(circle(88, 24, 4.5), 0.75)
    c.shape(circle(96, 12, 3.2), 0.75)
    c.shape(circle(86, 4, 2.4), 0.75)


@icon("PandabornHotPot", note="Two-flavour (yuanyang) hot pot with ear handles, chilies on the spicy side, steam")
def hot_pot(c):
    rim_y, rx, ry = 48, 42, 19
    c.shape(rrect(0, rim_y - 6, 14, 12, 5))
    c.shape(rrect(86, rim_y - 6, 14, 12, 5))
    body = (arc(50, rim_y, rx, 180, 360, ry=ry) + spline((92, rim_y), (90, 72), (78, 84), (50, 87), (22, 84),
                                                          (10, 72), (8, rim_y)))
    c.shape(body.close())
    c.shape(ellipse(50, rim_y, rx, ry))
    c.stroke(spline((14, rim_y - 9), (40, rim_y - 9), (60, rim_y + 9), (86, rim_y + 9)), 1.0)
    chili(c, 54, rim_y - 6, 15, 0.42)
    steam(c, 32, rim_y - 22, 20)
    steam(c, 50, rim_y - 25, 20)
    steam(c, 68, rim_y - 22, 20)


@icon("PandabornTea", note="Tea in a gaiwan: saucer, lidded bowl, steam from the gap")
def tea(c):
    c.shape(ellipse(50, 84, 46, 11))
    c.shape(spline((16, 46), (20, 66), (34, 80), (50, 82), (66, 80), (80, 66), (84, 46), (50, 52), closed=True))
    c.shape(ellipse(50, 46, 34, 8))
    with c.at(46, 39, 1, -9):
        c.shape(spline((-32, 4), (-24, -6), (-10, -12), (10, -12), (24, -6), (32, 4), (0, 8), closed=True))
        c.shape(rrect(-6, -20, 12, 9, 3))
    steam(c, 80, 36, 18, 0.9)
    steam(c, 90, 30, 14, 0.9)


@icon("PandabornBambooSeedCakes", note="Bamboo seed cakes: a stack of round pressed cakes with ribbed sides")
def bamboo_seed_cakes(c):
    def face(r, k):
        """Scalloped cake top with a pressed four-petal flower; k squashes it into perspective."""
        scal = []
        for j in range(28):
            a = j / 28 * 2 * math.pi
            rr = r + (2.6 if j % 2 else -0.6)
            scal.append((math.cos(a) * rr, -math.sin(a) * rr * k))
        c.shape(spline(*scal, closed=True))
        for j in range(4):
            a = j / 4 * 2 * math.pi + math.pi / 4
            c.dot(math.cos(a) * r * 0.3, -math.sin(a) * r * 0.3 * k, 0.5)
    # one cake standing up behind, facing us
    with c.at(36, 38, 1, 12):
        c.shape(ellipse(4, 0, 32, 32), 0.9)          # its thickness
        face(31, 1.0)
    # one cake lying in front
    with c.at(58, 76):
        r, h, k = 36, 9, 0.42
        c.shape(line((-r, 0), (-r, h)) + arc(0, h, r, 180, 360, ry=r * k) + line((r, h), (r, 0)) +
                arc(0, 0, r, 0, -180, ry=r * k))
        face(r, k)


# --------------------------------------------------------------------------------------------- materials

@icon("PandabornPoles", note="A bundle of three hollow bamboo poles with a leafy twig")
def bamboo_poles(c):
    ang = 26
    with c.at(26, 50, 1, ang):
        pole(c, 82, 11, nodes=(0.42,))
        c.stroke(spline((34, -12), (40, -24), (50, -30)), 0.7)
        leaf(c, 50, -30, 24, 8, 30, 0.75)
        leaf(c, 44, -26, 22, 7, 100, 0.75)
    for dx, dy in ((0, 0), (25, 6)):
        with c.at(12 + dx, 72 + dy, 1, ang):
            pole(c, 84, 11, nodes=(0.32, 0.74))


@icon("PandabornCuredPoles", note="Cured poles: a lashed bundle of jointed poles with dark ends and the vanilla 'treated' sparkles")
def cured_poles(c):
    ang = 26
    for dx, dy in ((14, -20), (0, 0), (25, 6)):
        with c.at(12 + dx, 72 + dy, 1, ang):
            pole(c, 84, 11, nodes=(0.28, 0.82), face="fill")
    # lashing: two wraps of cord around the middle of the bundle, and the loose end
    with c.at(12, 72, 1, ang):
        c.stroke(spline((48, -36), (52, -12), (52, 12), (48, 22)), 1.3, halo=0.8)
        c.stroke(spline((50, 22), (58, 30), (54, 38)), 0.7)
    sparkle(c, 14, 34, 10)
    sparkle(c, 30, 18, 6)
    sparkle(c, 90, 94, 7)


@icon("PandabornBambooCharcoal", ship=False, note="Bamboo charcoal: a pile of short black hollow pieces")
def bamboo_charcoal(c):
    # a stack of charred tube ends seen end-on: solid discs, a hollow centre, radial cracks
    r = 15
    cracks = [(35, 0.95), (160, 0.7), (250, 0.85)]
    for i, (x, y) in enumerate(((50, 24), (32, 52), (68, 52), (14, 80), (50, 80), (86, 80))):
        c.shape(circle(x, y, r), 0.8, filled=True, halo=0.7)
        c.erase(ellipse(x, y, r * 0.34, r * 0.38, rot=20 * i))
        for k, (a0, ln) in enumerate(cracks):
            a = math.radians(a0 + i * 47)
            b = a + math.radians(14 if k % 2 else -14)
            p0 = (x + math.cos(a) * r * 0.3, y - math.sin(a) * r * 0.3)
            p1 = (x + math.cos(b) * r * 0.6 * ln, y - math.sin(b) * r * 0.6 * ln)
            p2 = (x + math.cos(a) * r * ln, y - math.sin(a) * r * ln)
            c.erase(line(p0, p1, p2), 0.36)


@icon("PandabornPaperLanterns", note="A round paper lantern with ribs, caps and a tassel")
def paper_lanterns(c):
    c.stroke(line((50, 0), (50, 10)), 0.8)
    c.shape(rrect(38, 8, 24, 9, 2))
    c.shape(ellipse(50, 48, 38, 33))
    for k in (0.42, 0.78):
        c.stroke(arc(50, 48, 38 * k, 90, 270, ry=33), 0.7)
        c.stroke(arc(50, 48, 38 * k, 90, -90, ry=33), 0.7)
    c.shape(rrect(38, 79, 24, 9, 2))
    c.stroke(line((50, 88), (50, 92)), 0.8)
    c.stroke(spline((50, 92), (46, 100)), 0.7)
    c.stroke(line((50, 92), (50, 102)), 0.7)
    c.stroke(spline((50, 92), (54, 100)), 0.7)


@icon("PandabornRiceFlour", note="A tied sack of rice flour with a rice ear leaning on it")
def rice_flour(c):
    rice_ear(c, 70, 100, 1.0)
    c.shape(spline((20, 34), (8, 58), (6, 84), (16, 98), (44, 100), (68, 98), (76, 84), (74, 58), (62, 34), closed=True))
    c.shape(spline((24, 36), (14, 22), (24, 14), (34, 22), (42, 12), (52, 22), (62, 14), (68, 24), (58, 36),
                   closed=True))
    c.stroke(spline((22, 36), (41, 40), (60, 36)), 1.0)
    c.stroke(spline((60, 62), (64, 76), (62, 90)), 0.7)


# ------------------------------------------- cut from the catalogue (draft 2); kept in case they return, not shipped

def sparkle(c, x, y, r):
    """A four-pointed glint (the vanilla 'treated' convention)."""
    k = r * 0.28
    c.fill(spline((x, y - r), (x + k, y - k), (x + r, y), (x + k, y + k), (x, y + r), (x - k, y + k), (x - r, y),
                  (x - k, y - k), closed=True))


def cube(c, x, y, s, r=3.0):
    """A soft-edged cube in 3/4 view, top-centre corner at (x, y), edge length s."""
    dx, dy = s * 0.87, s * 0.5
    top, right, left = (x, y), (x + dx, y + dy), (x - dx, y + dy)
    mid = (x, y + 2 * dy)
    c.shape(spline(top, (x + dx * 0.5, y + dy * 0.5 - 0.6), right, (x + dx + 0.6, y + dy + s * 0.5), (x + dx, y + dy + s),
                   (x + dx * 0.5, y + dy * 1.5 + s), (x, mid[1] + s), (x - dx * 0.5, y + dy * 1.5 + s),
                   (x - dx, y + dy + s), (x - dx - 0.6, y + dy + s * 0.5), left, (x - dx * 0.5, y + dy * 0.5 - 0.6),
                   closed=True))
    c.stroke(spline(left, (x, mid[1] + 0.8), right), 0.75)
    c.stroke(line(mid, (x, mid[1] + s - 2)), 0.75)


@icon("PandabornTofu", ship=False, note="Tofu: a soft white block and a small cube, two soybeans")
def tofu(c):
    cube(c, 40, 6, 40)
    cube(c, 78, 52, 22)
    for x, y, a in ((14, 84, 20), (30, 90, -15)):
        with c.at(x, y, 1, a):
            c.shape(ellipse(0, 0, 9, 7), 0.8)
            c.stroke(arc(0, 0, 4, 200, 340, ry=2.5), 0.5)


@icon("PandabornLacquer", ship=False, note="Raw lacquer: a pot of dark glossy sap with a flat brush and a drip")
def lacquer(c):
    c.shape(rrect(70, 2, 10, 46, 4), 0.85)                         # brush handle, leaning in the pot
    c.shape(spline((12, 40), (10, 66), (20, 88), (50, 94), (80, 88), (90, 66), (88, 40), closed=True))
    c.shape(ellipse(50, 40, 40, 11))
    c.fill(ellipse(50, 41, 32, 7))                                    # the dark lacquer surface
    c.erase(arc(40, 41, 18, 150, 175, ry=4), 0.5)                     # gloss on the surface
    c.shape(spline((20, 44), (24, 56), (22, 66), (18, 62), (16, 50), closed=True), 0.6, filled=True)  # drip
    c.stroke(arc(50, 68, 39, 195, 345, ry=9), 0.6)


@icon("PandabornLacqueredPoles", ship=False, note="Lacquered poles: glossy poles with sparkles (the vanilla 'treated' convention)")
def lacquered_poles(c):
    for dx, dy in ((0, 0), (24, 6)):
        with c.at(12 + dx, 70 + dy, 1, 26):
            pole(c, 84, 12, nodes=(0.36, 0.72), face="fill")
            c.stroke(line((10, -6), (26, -6)), 0.5)
            c.stroke(line((40, -6), (56, -6)), 0.5)
    sparkle(c, 16, 32, 10)
    sparkle(c, 30, 14, 6)
    sparkle(c, 92, 96, 7)


@icon("PandabornPersimmonCakes", ship=False, note="Persimmon cakes: flattened dried persimmons with caps and a sugar bloom")
def persimmon_cakes(c):
    def cake(x, y, s):
        with c.at(x, y, s):
            r, h, k = 34, 8, 0.48
            c.shape(line((-r, 0), (-r + 2, h)) + arc(0, h, r - 2, 180, 360, ry=(r - 2) * k) + line((r - 2, h), (r, 0))
                    + arc(0, 0, r, 0, -180, ry=r * k))
            c.shape(ellipse(0, 0, r, r * k))
            pts = []
            for j in range(48):
                t = j / 48 * 2 * math.pi
                rr = 13 * (0.35 + 0.65 * abs(math.cos(2 * t)) ** 0.55)
                pts.append((math.cos(t) * rr, -math.sin(t) * rr * k))
            c.shape(Path(np.asarray(pts), True), 0.8)
            for px, py in ((-22, -4), (-14, 9), (18, 8), (24, -5), (6, -12), (-6, 12)):
                c.dot(px, py, 0.35)
    cake(40, 40, 0.85)
    cake(56, 70, 1.05)


@icon("PandabornLotusRoot", ship=False, note="Lotus root: two linked segments and a slice showing the ring of holes")
def lotus_root(c):
    with c.at(54, 36, 1, 25):
        c.shape(rrect(0, -16, 52, 32, 15))
        c.shape(rrect(-50, -17, 54, 34, 16))
    with c.at(24, 80):
        c.shape(ellipse(0, 0, 24, 20))
        c.shape(circle(0, 0, 3.4), 0.6)
        for k in range(7):
            a = k / 7 * 2 * math.pi + 0.3
            c.shape(circle(math.cos(a) * 13, math.sin(a) * 11, 3.6 if k % 2 else 4.2), 0.6)


@icon("PandabornOxParts", ship=False, note="Wooden ox parts: a carved horned ox head and a pegged dowel")
def ox_parts(c):
    c.shape(rrect(52, 58, 46, 12, 6), 0.9)                            # dowel behind
    c.dot(62, 64, 0.5)
    c.dot(88, 64, 0.5)
    c.shape(spline((14, 26), (4, 14), (2, 2), (14, 8), (24, 20), closed=True))    # horns
    c.shape(spline((70, 26), (80, 14), (82, 2), (70, 8), (60, 20), closed=True))
    c.shape(spline((24, 22), (42, 18), (60, 22), (62, 46), (56, 72), (42, 82), (28, 72), (22, 46), closed=True))
    c.shape(spline((8, 30), (20, 26), (24, 36), (14, 38), closed=True), 0.8)       # ears
    c.shape(spline((76, 30), (64, 26), (60, 36), (70, 38), closed=True), 0.8)
    c.shape(ellipse(42, 66, 13, 9), 0.8)                                            # muzzle
    c.dot(37, 66, 0.45)
    c.dot(47, 66, 0.45)
    c.shape(circle(32, 42, 4), 0.7, filled=True)                                    # peg eyes
    c.shape(circle(52, 42, 4), 0.7, filled=True)
    c.stroke(spline((36, 28), (42, 32), (48, 28)), 0.55)                            # grain
