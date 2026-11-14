"""Plant icons (planting tools and the plant's own panel; LabeledEntitySpec.Icon of the plant blueprint).

Vanilla conventions (naturalresources/*): 112 px, thin pen lines; crops stand on two or three rows of short
horizontal ground lines, water plants on wavy water lines; trees are shown as one characteristic leaf or twig.
These are proposals (ship=False): they render to E:\\PandabornDev\\build\\icons until the plant blueprints exist.
"""
import math

import numpy as np

from ink import PLANT, Path, arc, circle, ellipse, icon, line, spline
from goods import grain

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

@icon("PandabornRiverBamboo", group=G, style=PLANT, ship=False,
      note="River bamboo: a jointed stalk with a spray of long leaves, over river water")
def river_bamboo(c):
    water(c, 86, 2, gaps=((40, 58),))
    for x0 in (42, 52):
        c.stroke(line((x0, 92), (x0 + 6, 10)), 1.0, taper=0)
    for y in (70, 46, 22):
        c.stroke(arc(47 + (92 - y) * 0.065 + 0.5, y, 5.5, 200, 340, ry=2), 0.8)
    for x, y, ln, a in ((54, 40, 36, 20), (54, 40, 30, -12), (52, 60, 34, 160), (52, 60, 28, 195),
                        (57, 18, 30, 35), (56, 18, 28, 150)):
        blade(c, x, y, ln, a, 8)


@icon("PandabornCloudBamboo", group=G, style=PLANT, ship=False,
      note="Cloud bamboo: a tall jointed stalk with drooping leaves and a curl of mountain cloud")
def cloud_bamboo(c):
    # cloud behind: a classic curled cloud band
    c.shape(spline((8, 52), (14, 42), (26, 42), (30, 34), (44, 34), (50, 42), (64, 40), (72, 48), (64, 56),
                   (16, 58), closed=True))
    c.stroke(spline((26, 50), (30, 44), (36, 48)), 0.7)
    for x0 in (60, 70):
        c.stroke(line((x0, 100), (x0 - 4, 4)), 1.0, taper=0)
    for y in (78, 52, 26):
        c.shape(Path(np.array([[59 - (100 - y) * 0.04, y - 1.5], [69 - (100 - y) * 0.04, y - 1.5],
                               [69 - (100 - y) * 0.04, y + 1.5], [59 - (100 - y) * 0.04, y + 1.5]]), True), 0.5,
                filled=True)
    for x, y, ln, a in ((66, 24, 30, -30), (64, 24, 26, -70), (60, 50, 30, -150), (60, 50, 26, 210),
                        (68, 6, 26, -10), (62, 6, 22, 200)):
        blade(c, x, y, ln, a, 8)


@icon("PandabornPersimmonTree", group=G, style=PLANT, ship=False,
      note="Persimmon tree: a broad persimmon leaf with a fruit hanging below it")
def persimmon_tree(c):
    broad_leaf(c, 20, 86, 84, 46, 55, veins=4)
    c.stroke(spline((24, 82), (16, 92), (10, 96)))
    with c.at(70, 74, 0.7):
        c.shape(spline((-30, -2), (-27, -15), (-14, -19), (0, -16), (14, -19), (27, -15), (30, -2), (24, 15),
                       (0, 21), (-24, 15), closed=True), 1.3)
        pts = []
        for k in range(48):
            t = k / 48 * 2 * math.pi
            rr = 22 * (0.3 + 0.7 * abs(math.cos(2 * t)) ** 0.55)
            pts.append((math.cos(t) * rr, -16 - math.sin(t) * rr * 0.42))
        c.shape(Path(np.asarray(pts), True), 1.2)


@icon("PandabornLacquerTree", group=G, style=PLANT, ship=False,
      note="Lacquer tree: a compound leaf (paired leaflets) and a drop of sap")
def lacquer_tree(c):
    c.stroke(spline((30, 98), (40, 70), (52, 40), (64, 6)))
    for k, t in enumerate((0.25, 0.48, 0.7)):
        x, y = 30 + 34 * t + 2, 98 - 92 * t
        broad_leaf(c, x, y, 30, 14, 150 - k * 5, veins=2)
        broad_leaf(c, x, y, 30, 14, 20 + k * 5, veins=2)
    broad_leaf(c, 64, 8, 26, 13, 75, veins=2)
    c.shape(spline((84, 66), (90, 78), (88, 86), (80, 86), (78, 78), closed=True))


# ------------------------------------------------------------------------------------------------- crops

@icon("PandabornRice", group=G, style=PLANT, ship=False,
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


@icon("PandabornLotus", group=G, style=PLANT, ship=False,
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


@icon("PandabornCabbage", group=G, style=PLANT, ship=False,
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


@icon("PandabornTeaBush", group=G, style=PLANT, ship=False,
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


@icon("PandabornSichuanPepper", group=G, style=PLANT, ship=False,
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
