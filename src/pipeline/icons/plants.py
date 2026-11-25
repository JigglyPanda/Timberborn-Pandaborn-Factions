"""Plant icons (planting tools and the plant's own panel; LabeledEntitySpec.Icon of the plant blueprint).

Vanilla conventions (naturalresources/*): 112 px, thin pen lines; crops stand on two or three rows of short
horizontal ground lines, water plants on wavy water lines; trees are shown as one characteristic leaf or twig.
Shipped to Sprites/Pandaborn/Plants/Pandaborn<Plant>Icon.png; lotus (a later update) renders to the build dir only.
"""
import math

import numpy as np

from ink import PLANT, Path, arc, circle, ellipse, icon, line, spline
from goods import calyx, grain

G = "Plants"


def ground(c, gaps=(), y0=82, rows=3, x0=4, x1=96):
    """Rows of short ground strokes, interrupted where a stem enters the soil (gaps: list of (x0, x1))."""
    for r in range(rows):
        y = y0 + r * 8
        xs = [x0 + r * 3] + [v for g in sorted(gaps) for v in g] + [x1 - r * 4]
        for a, b in zip(xs[0::2], xs[1::2]):
            if b - a > 4:
                c.stroke(line((a, y), (b, y + (0.6 if r % 2 else -0.6))))


def water(c, y0=84, rows=2, x0=4, x1=96, gaps=()):
    """Wavy water lines."""
    for r in range(rows):
        y = y0 + r * 9
        xs = np.linspace(x0 + r * 6, x1 - r * 6, 60)
        pts = np.stack([xs, y + np.sin(xs / 6.5 + r) * 1.8], 1)
        keep = np.ones(len(xs), bool)
        for g0, g1 in gaps:
            keep &= ~((xs > g0) & (xs < g1))
        run = []
        for p, k in zip(pts, keep):
            if k:
                run.append(p)
            elif run:
                if len(run) > 2:
                    c.stroke(Path(np.asarray(run)))
                run = []
        if len(run) > 2:
            c.stroke(Path(np.asarray(run)))


def blade(c, x, y, length, ang, width=5, w=1.0):
    """A long grass/bamboo leaf from (x, y) along `ang` degrees, with its midrib."""
    with c.at(x, y, 1, ang):
        c.shape(spline((0, 0), (length * 0.3, -width / 2), (length * 0.75, -width * 0.3), (length, 0),
                       (length * 0.75, width * 0.3), (length * 0.3, width / 2), closed=True), w)
        c.stroke(line((3, 0), (length * 0.8, 0)), 0.6, taper=0.8)


def broad_leaf(c, x, y, length, width, ang, veins=4):
    """A broad pointed leaf with a midrib and side veins, base at (x, y)."""
    with c.at(x, y, 1, ang):
        c.shape(spline((0, 0), (length * 0.25, -width * 0.45), (length * 0.6, -width * 0.42), (length, 0),
                       (length * 0.6, width * 0.42), (length * 0.25, width * 0.45), closed=True))
        c.stroke(line((-6, 0), (length * 0.9, 0)))
        for k in range(veins):
            t = 0.2 + 0.6 * k / max(1, veins - 1)
            for s in (-1, 1):
                c.stroke(line((length * t, 0), (length * (t + 0.12), s * width * 0.32)), 0.7)


# ------------------------------------------------------------------------------------------------- trees

@icon("PandabornTimberBamboo", group=G, style=PLANT,
      note="Timber bamboo: a tall jointed culm with sprays of long leaves")
def timber_bamboo(c):
    for x0 in (44, 54):
        c.stroke(line((x0, 100), (x0 + 6, 6)), 1.0, taper=0)
    for y in (78, 54, 30):
        c.stroke(arc(49 + (100 - y) * 0.064 + 0.5, y, 5.5, 200, 340, ry=2), 0.8)
    for x, y, ln, a in ((56, 50, 36, 20), (56, 50, 30, -12), (52, 70, 34, 160), (52, 70, 28, 195),
                        (59, 26, 30, 35), (57, 26, 28, 150), (60, 8, 24, 70)):
        blade(c, x, y, ln, a, 8)


@icon("PandabornShootBamboo", group=G, style=PLANT,
      note="Shoot bamboo: plump shoots breaking through the field, a young leaf spray behind")
def shoot_bamboo(c):
    ground(c, gaps=((22, 44), (54, 80)))
    blade(c, 60, 40, 30, 60, 7)
    blade(c, 60, 40, 26, 110, 7)
    c.stroke(line((60, 40), (62, 86)), 0.9, taper=0)
    for cx, s in ((33, 0.8), (67, 1.0)):
        with c.at(cx, 88, s):
            c.shape(spline((-14, 0), (-12, -20), (-4, -42), (4, -50), (6, -36), (13, -16), (14, 0), closed=True))
            c.stroke(spline((-12, -12), (0, -16), (12, -24)), 0.7)
            c.stroke(spline((-8, -30), (2, -30), (8, -40)), 0.7)


def plume(c, x, y, side, L=30, n=5):
    """A bamboo seed plume (the Great Flowering): a wiry branchlet arching out from (x, y) to `side` (+1 right,
    -1 left) and hanging, solid spikelets dangling along it."""
    st = spline((x, y), (x + side * L * 0.45, y - L * 0.3), (x + side * L * 0.85, y - L * 0.14),
                (x + side * L, y + L * 0.3))
    c.stroke(st, 0.7)
    for k in range(n):
        px, py = st.pts[min(len(st.pts) - 1, int(len(st.pts) * (0.3 + 0.7 * k / (n - 1))))]
        c.shape(ellipse(px + side * 0.6, py + 4.6, 2.1, 4.2, rot=-side * 12), 0.45, filled=True)


@icon("PandabornTimberBambooInFlower", group=G, style=PLANT,
      note="Timber bamboo in flower: the same jointed culm, its leaves gone thin, seed plumes hanging from every joint")
def timber_bamboo_in_flower(c):
    for x0 in (44, 54):
        c.stroke(line((x0, 100), (x0 + 6, 6)), 1.0, taper=0)
    for y in (78, 54, 30):
        c.stroke(arc(49 + (100 - y) * 0.064 + 0.5, y, 5.5, 200, 340, ry=2), 0.8)
    plume(c, 57, 52, 1, 36)
    plume(c, 51, 74, -1, 36)
    plume(c, 59, 28, 1, 30)
    plume(c, 55, 32, -1, 32)
    plume(c, 58, 8, -1, 22, n=4)
    blade(c, 60, 8, 22, 55, 5)                                        # one last thin leaf
    for x, y in ((20, 92), (84, 84), (30, 60)):                       # seed falling
        c.dot(x, y, 0.55)


@icon("PandabornShootBambooInFlower", group=G, style=PLANT,
      note="Shoot bamboo in flower: no shoots, thin culms with seed plumes arching out and hanging over the field")
def shoot_bamboo_in_flower(c):
    ground(c, gaps=((24, 32), (46, 54), (68, 76)))
    for x, top, lean in ((28, 44, -3), (50, 28, 1), (72, 40, 4)):
        c.stroke(line((x, 88), (x + lean, top)), 0.9, taper=0)
        c.stroke(line((x + lean * 0.5 - 2.5, (88 + top) / 2), (x + lean * 0.5 + 2.5, (88 + top) / 2)), 0.6, taper=0)
        plume(c, x + lean, top, 1, 22 if x != 50 else 26, n=4)
        plume(c, x + lean, top + 2, -1, 22 if x != 50 else 26, n=4)


@icon("PandabornPersimmonTree", group=G, style=PLANT,
      note="Persimmon tree: a broad persimmon leaf with a fruit hanging below it")
def persimmon_tree(c):
    broad_leaf(c, 20, 86, 84, 46, 55, veins=4)
    c.stroke(spline((24, 82), (16, 92), (10, 96)))
    with c.at(70, 76, 0.7):
        c.shape(spline((-34, -8), (-28, -19), (-12, -22), (12, -22), (28, -19), (34, -8), (30, 12), (0, 22),
                       (-30, 12), closed=True), 1.3)
        calyx(c, 0, -20, 30)


# ------------------------------------------------------------------------------------------------- crops

@icon("PandabornRice", group=G, style=PLANT,
      note="Rice: three tufts in the paddy, ears bowing over the water")
def rice(c):
    water(c, 84, 2, gaps=((18, 34), (42, 58), (68, 84)))
    for x, s in ((26, 0.8), (50, 1.0), (76, 0.8)):
        with c.at(x, 88, s):
            for a in (100, 80, 120, 62):
                c.stroke(spline((0, 0), (math.cos(math.radians(a)) * 20, -math.sin(math.radians(a)) * 30),
                                (math.cos(math.radians(a)) * 34, -math.sin(math.radians(a)) * 46)), 0.9)
            stalk = spline((0, 0), (2, -40), (10, -60), (22, -66), (30, -58))
            c.stroke(stalk, 0.9)
            for k in range(5):
                p = stalk.pts[int(len(stalk.pts) * (0.62 + 0.08 * k))]
                grain(c, p[0] + (2 if k % 2 else -2), p[1] + 3, -60 - 10 * k, 0.9, filled=False)


@icon("PandabornLotus", group=G, style=PLANT, ship=False,  # later update
      note="Lotus: a round leaf with radiating veins and a bud on its stalk, over water")
def lotus(c):
    water(c, 86, 2, gaps=((58, 70),))
    c.stroke(spline((64, 90), (62, 50), (66, 26)))
    c.shape(spline((66, 4), (74, 14), (74, 26), (66, 32), (58, 26), (58, 14), closed=True))
    c.stroke(spline((66, 8), (64, 18), (66, 30)), 0.7)
    with c.at(36, 64):
        c.shape(ellipse(0, 0, 34, 14))
        c.erase(Path(np.array([[0, 0], [-6, 16], [6, 16]]), True))
        for a in (20, 60, 100, 140, 175, 215, 325, 5):
            c.stroke(line((0, 1), (math.cos(math.radians(a)) * 28, -math.sin(math.radians(a)) * 11)), 0.6)
        c.stroke(line((0, 1), (0, 22)), 1.0)


@icon("PandabornCabbage", group=G, style=PLANT,
      note="Napa cabbage standing in the field")
def cabbage(c):
    ground(c, gaps=((30, 70),))
    with c.at(50, 50, 0.8):
        with c.at(-50, -46):
            frill = [(26, 30), (24, 18), (32, 8), (40, 12), (46, 4), (54, 9), (62, 3), (70, 10), (76, 18), (76, 30)]
            c.shape(spline((50, 102), (30, 92), (22, 64), (24, 40), *frill, (80, 54), (74, 88), closed=True))
            front = [(34, 32), (40, 24), (46, 28), (52, 22), (58, 28), (64, 26), (66, 36)]
            c.shape(spline((50, 102), (36, 94), (30, 70), *front, (68, 64), (64, 92), closed=True))
            c.stroke(spline((44, 98), (40, 70), (40, 44)))
            c.stroke(spline((56, 98), (58, 70), (58, 44)))


@icon("PandabornTeaBush", group=G, style=PLANT,
      note="Tea bush: a clipped round bush of small leaves with a fresh bud and two leaves on top, dry ground")
def tea_bush(c):
    ground(c, gaps=((44, 56),))
    c.stroke(line((50, 84), (50, 70)), 1.2)
    bumps = []
    for k in range(11):
        t = math.pi * k / 10
        rr = 1.0 if k % 2 else 0.9
        bumps.append((50 - math.cos(t) * 42 * rr, 68 - math.sin(t) * 34 * rr))
    c.shape(spline(*bumps, (88, 72), (50, 76), (12, 72), closed=True))
    for x, y in ((30, 56), (50, 50), (68, 58)):
        c.stroke(spline((x - 6, y + 2), (x, y - 2), (x + 6, y + 2)), 0.7)
    c.stroke(spline((50, 32), (50, 20), (52, 8)), 0.9)
    c.shape(spline((50, 22), (40, 18), (32, 12), (42, 10), closed=True), 0.8)
    c.shape(spline((51, 16), (60, 10), (68, 2), (58, 4), closed=True), 0.8)
    c.shape(spline((52, 10), (49, 2), (52, -6), (55, 2), closed=True), 0.8)


@icon("PandabornSichuanPepper", group=G, style=PLANT,
      note="Sichuan pepper: a small thorny shrub hung with husk clusters, dry ground")
def sichuan_pepper(c):
    ground(c, gaps=((44, 56),))
    c.stroke(spline((50, 84), (50, 60), (36, 34), (26, 16)))
    c.stroke(spline((50, 62), (64, 40), (78, 22)))
    c.stroke(spline((44, 46), (56, 26), (58, 10)))
    for x, y, a in ((40, 38, 150), (60, 44, 30), (52, 26, 120), (70, 30, 60)):
        c.stroke(line((x, y), (x + math.cos(math.radians(a)) * 6, y - math.sin(math.radians(a)) * 6)), 0.7)
    for cx, cy in ((24, 30), (78, 36), (56, 18)):
        for dx, dy in ((0, 0), (8, 3), (3, 9), (-6, 6)):
            c.shape(circle(cx + dx, cy + dy, 4.6), 0.8)
    for x, y, a in ((28, 14, 150), (80, 20, 40), (60, 8, 80)):
        with c.at(x, y, 1, a):
            c.shape(spline((0, 0), (6, -3), (13, 0), (6, 3), closed=True), 0.8)
