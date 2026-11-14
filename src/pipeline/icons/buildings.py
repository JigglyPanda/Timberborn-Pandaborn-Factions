"""Building icons (LabeledEntitySpec.Icon) for every new Inkpaws building in docs/CONTENT.md.

Vanilla building icons are pen sketches of what the building *does* (a bell, a grill, a lodge), 112 px, drawn
small for small buildings and large for big ones, usually standing on a short ground line. Ours follow the same
rules in the BUILDING style, with the Sichuan farmstead look: timber frame and plaster, grey tile roofs with a
gentle curve (no sharply upturned palace eaves), bamboo and woven panels, lanterns as accents. No writing,
nothing Japanese-coded, no religious imagery.

Ringtail buildings carry a small solid crescent moon in the top-right corner (`moon()`).
"""
import math

import numpy as np

from ink import BUILDING, Path, arc, circle, ellipse, hatch, icon, line, rrect, spline

G = "Buildings"


def b(id, extent=None, note=""):
    """Register a building icon: file Pandaborn<Name>Icon.png under Sprites/Pandaborn/Buildings."""
    # `extent` is the building's relative size (small buildings are drawn small, as in vanilla); 0.92 brings the
    # set's median ink extent to vanilla's (~79 px of 112)
    return icon(id, group=G, style=BUILDING, extent=extent * 0.92 if extent else None, note=note)


# ------------------------------------------------------------------------------------------------ motifs

def ground(c, x0=6, x1=94, y=97):
    c.stroke(line((x0, y), (x1, y)))


def water(c, y=90, x0=6, x1=94, rows=2):
    for r in range(rows):
        xs = np.linspace(x0 + r * 8, x1 - r * 8, 50)
        c.stroke(Path(np.stack([xs, y + r * 8 + np.sin(xs / 6 + r) * 1.8], 1)))


def moon(c, x=90, y=10, r=11):
    """The Ringtail mark: a solid crescent."""
    c.fill(circle(x, y, r))
    c.erase(circle(x + r * 0.5, y - r * 0.32, r * 0.82))


def steam(c, x, y, h=16, w=0.9):
    c.stroke(spline((x, y), (x + 3, y - h * 0.33), (x - 3, y - h * 0.66), (x + 1, y - h)), w)


def roof(c, cx, y, w, h, tiles=3):
    """A grey tile roof seen at the gable end: gently sagging slopes from a short ridge cap, eaves reaching a
    little past the walls and lifting only slightly; an inner line along the slopes for the tile course."""
    hw = w / 2
    sag = h * 0.12
    left = spline((cx - hw - 1, y + h - 2.5), (cx - hw * 0.5, y + h * 0.5 + sag), (cx - 3, y))
    right = spline((cx + 3, y), (cx + hw * 0.5, y + h * 0.5 + sag), (cx + hw + 1, y + h - 2.5))
    c.shape((left + line((cx - 3, y), (cx + 3, y)) + right + line((cx + hw + 1, y + h - 2.5), (cx + hw - 2, y + h))
             + line((cx + hw - 2, y + h), (cx - hw + 2, y + h)) + line((cx - hw + 2, y + h), (cx - hw - 1, y + h - 2.5))
             ).close())
    if tiles:
        c.stroke(spline((cx - hw + 7, y + h - 4), (cx - hw * 0.45, y + h * 0.5 + sag + 3), (cx, y + 7),
                        (cx + hw * 0.45, y + h * 0.5 + sag + 3), (cx + hw - 7, y + h - 4)), 0.55)


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


def lantern(c, x, y, s=1.0, string=6):
    """A small round hanging lantern, top of the string at (x, y)."""
    with c.at(x, y, s):
        c.stroke(line((0, 0), (0, string)), 0.6)
        c.shape(ellipse(0, string + 7, 6, 7), 0.8)
        c.stroke(line((0, string + 14), (0, string + 19)), 0.6)


def house(c, cx, base, w, wall_h, roof_h, door_w=None, windows=0, tiles=3):
    """Timber-frame house with a tile roof, front view, standing on `base`."""
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


def trestle(c, x, y_top, y_bot, spread=8):
    """An X-legged bamboo trestle under a flume."""
    c.stroke(line((x - spread, y_bot), (x + spread * 0.4, y_top)), 0.85)
    c.stroke(line((x + spread, y_bot), (x - spread * 0.4, y_top)), 0.85)


def flume_run(c, x0, x1, y, depth=8):
    """An open split-bamboo channel seen from the side and a little above: rim ellipse ends, water line."""
    c.shape((line((x0, y), (x1, y)) + arc(x1, y + depth / 2, 3, 90, -90, ry=depth / 2)
             + line((x1, y + depth), (x0, y + depth)) + arc(x0, y + depth / 2, 3, 270, 90, ry=depth / 2)).close())
    c.stroke(line((x0 + 3, y + 3), (x1 - 3, y + 3)), 0.55)
    for x in np.arange(x0 + 18, x1 - 6, 24):
        c.stroke(line((x, y + 1), (x, y + depth - 1)), 0.55)


def cistern(c, cx, base, w, h, hoops=2):
    """An open hooped wooden water tub: water surface showing at the top, bamboo hoops, a bamboo tap."""
    rx, ry = w / 2, w * 0.14
    with c.at(cx + rx * 0.9, base - h * 0.25, 1, -10):            # tap pipe, behind the tub wall
        c.shape(rrect(-4, -3.5, 20, 7, 3.5), 0.75)
    c.shape((arc(cx, base - h, rx, 180, 360, ry=ry) + line((cx + rx, base - h), (cx + rx * 0.94, base))
             + arc(cx, base, rx * 0.94, 0, -180, ry=ry) + line((cx - rx * 0.94, base), (cx - rx, base - h))).close())
    c.shape(ellipse(cx, base - h, rx, ry))
    c.stroke(spline((cx - rx * 0.55, base - h + 1), (cx - rx * 0.2, base - h - 1.5), (cx + rx * 0.15, base - h + 1.5),
                    (cx + rx * 0.5, base - h)), 0.55)                 # water ripple
    for k in range(hoops):
        y = base - h * (k + 1) / (hoops + 1)
        c.stroke(arc(cx, y, rx * 0.97, 190, 350, ry=ry), 0.75)


# ------------------------------------------------------------------------------------------- village

@b("PandabornVillageHall", 96, "District centre: a two-tier hall with lanterns either side of the door")
def village_hall(c):
    ground(c, 2, 98)
    frame_wall(c, 14, 58, 72, 38, posts=4)
    door(c, 42, 72, 16, 24)
    roof(c, 50, 42, 92, 20, tiles=5)
    frame_wall(c, 30, 30, 40, 13, posts=2, beam=False)
    roof(c, 50, 10, 56, 22, tiles=3)
    lantern(c, 30, 60, 0.9)
    lantern(c, 70, 60, 0.9)


@b("PandabornFestivalSquare", 90, "Festival square: lanterns strung between two poles over a paved square")
def festival_square(c):
    ground(c, 2, 98)
    c.stroke(line((10, 92), (90, 92)), 0.6)
    bamboo_post(c, 8, 18, 97, 1.1)
    bamboo_post(c, 92, 18, 97, 1.1)
    string = spline((8, 22), (30, 38), (50, 42), (70, 38), (92, 22))
    c.stroke(string, 0.7)
    for x in (24, 40, 58, 76):
        y = float(np.interp(x, string.pts[:, 0], string.pts[:, 1]))
        lantern(c, x, y, 1.0, string=4)
    for x in (34, 50, 66):                                      # stacked festival goods
        c.shape(rrect(x - 7, 80, 14, 12, 2), 0.8)


# ------------------------------------------------------------------------------------------------ homes

@b("PandabornDen", 66, "Den: a small low bamboo hut with woven walls and a round door")
def den(c):
    ground(c, 8, 92)
    wall = rrect(20, 60, 60, 36, 2)
    c.shape(wall)
    for seg in hatch(wall, 9, 90, margin=3):
        c.stroke(seg, 0.5)
    c.shape(arc(50, 96, 11, 0, 180, ry=16).close(), 0.9)
    roof(c, 50, 34, 76, 30, tiles=3)


@b("PandabornCourtyardHouse", 94, "Courtyard house: a main hall behind a walled yard with a gate, two side wings")
def courtyard_house(c):
    ground(c, 2, 98)
    house(c, 50, 70, 46, 24, 18, windows=2)
    for cx in (14, 86):
        frame_wall(c, cx - 12, 64, 24, 33, posts=1)
        roof(c, cx, 50, 26, 16, tiles=2)
    c.shape(rrect(24, 78, 52, 19, 1))                             # courtyard wall
    c.shape(rrect(43, 82, 14, 15, 1), 0.9)                        # gate
    roof(c, 50, 72, 22, 9, tiles=1)


@b("PandabornTerraceHouse", 92, "Terrace house: two homes stepped up a hillside on stone terrace walls")
def terrace_house(c):
    c.stroke(line((2, 97), (98, 97)))
    c.shape(rrect(52, 58, 44, 39, 1), 0.9)                        # upper terrace wall
    for y in (68, 80):
        c.stroke(line((54, y), (94, y)), 0.5)
    house(c, 74, 58, 34, 22, 16)
    c.shape(rrect(4, 80, 52, 17, 1), 0.9)                         # lower terrace wall
    house(c, 30, 80, 38, 24, 16, windows=1)
    for k in range(3):                                            # steps
        c.stroke(line((56 + k * 0, 92 - k * 6), (62 - k * 2 + 6, 92 - k * 6)), 0.7)


@b("PandabornMoonLoft", 86, "Moon Loft (Ringtails): a small house on stilts over a path, a lantern lit in its window")
def moon_loft(c):
    moon(c, 92, 8)
    c.stroke(line((2, 97), (98, 97)))
    c.stroke(line((32, 92), (68, 92)), 0.5)
    for x in (24, 76):
        bamboo_post(c, x, 56, 97, 1.0, nodes=1)
    c.stroke(line((24, 72), (76, 86)), 0.6)                       # cross brace
    c.stroke(line((76, 72), (24, 86)), 0.6)
    c.shape(rrect(16, 54, 68, 5, 1), 0.8)                         # floor
    frame_wall(c, 22, 30, 56, 25, posts=1, beam=False)
    c.shape(rrect(40, 36, 18, 14, 1), 0.85)                       # window
    lantern(c, 49, 36, 0.7, string=2)
    roof(c, 50, 12, 72, 20, tiles=3)


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


@b("PandabornPickleYard", 84, "Pickle yard: a row of water-sealed pickle jars under a small lean-to")
def pickle_yard(c):
    ground(c, 2, 98)
    c.stroke(line((10, 38), (10, 97)), 0.9)
    c.stroke(line((90, 30), (90, 97)), 0.9)
    c.shape(spline((2, 40), (50, 30), (98, 22), (98, 28), (50, 37), (2, 46), closed=True))   # lean-to roof
    pao_jar(c, 28, 97, 0.9)
    pao_jar(c, 72, 97, 0.9)
    pao_jar(c, 50, 97, 1.05)


@b("PandabornPaddyHouse", 86, "Paddy house: a farmhouse beside a flooded terrace of rice")
def paddy_house(c):
    house(c, 30, 70, 40, 26, 18)
    c.stroke(line((4, 70), (56, 70)))
    water(c, 84, 4, 96)
    for x in (66, 80, 94):
        for a in (100, 75, 125):
            c.stroke(line((x, 84), (x + math.cos(math.radians(a)) * 14, 84 - math.sin(math.radians(a)) * 20)), 0.7)
        c.stroke(spline((x, 84), (x + 2, 62), (x + 8, 58), (x + 10, 66)), 0.7)


@b("PandabornTeaRoastery", 80, "Tea roastery: tea leaves turning in a big wok on a brick stove, a hand in the leaves, heat")
def tea_roastery(c):
    c.shape(rrect(12, 66, 76, 31, 2))
    for y in (76, 86):
        c.stroke(line((14, y), (86, y)), 0.5)
    for x, y in ((30, 71), (60, 71), (45, 81), (75, 81), (30, 91), (60, 91)):
        c.stroke(line((x, y - 4), (x, y + 4)), 0.5)
    c.shape(spline((6, 50), (50, 70), (94, 50), (50, 46), closed=True))          # wide wok
    for x, y, a in ((34, 52, 20), (50, 54, -15), (64, 51, 35), (44, 47, -40), (58, 46, 10)):
        with c.at(x, y, 1, a):
            c.shape(spline((-7, 0), (0, -3.5), (7, 0), (0, 3.5), closed=True), 0.7)
    c.stroke(spline((70, 44), (78, 30), (84, 16)), 1.0)                          # wooden paddle
    c.shape(ellipse(68, 46, 7, 3, rot=-30), 0.8)
    steam(c, 30, 38)
    steam(c, 46, 34)


@b("PandabornTripHammerMill", 94, "Trip-hammer mill: a water wheel turns a shaft whose cam tips a hammer beam over a mortar")
def trip_hammer_mill(c):
    water(c, 90, 2, 46)
    wheel(c, 24, 64, 22, 8)
    c.stroke(line((24, 64), (60, 64)), 1.0)                      # shaft
    c.shape(rrect(58, 58, 8, 12, 2), 0.8)                         # cam
    c.stroke(line((50, 97), (64, 76)), 0.9)                       # pivot post
    c.stroke(line((78, 97), (64, 76)), 0.9)
    c.stroke(line((60, 60), (96, 84)), 1.2)                       # hammer beam, raised end over the cam
    c.shape(rrect(86, 78, 9, 14, 2), 0.9)                         # hammer head
    c.shape(spline((80, 97), (82, 90), (98, 90), (100, 97), closed=True), 0.9)     # mortar
    ground(c, 46, 100)


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


@b("PandabornHotPotHall", 92, "Hot pot hall: a divided hot pot steaming on a round table under a tile eave")
def hot_pot_hall(c):
    roof(c, 50, 2, 100, 18, tiles=5)
    for x in (10, 90):
        c.stroke(line((x, 18), (x, 97)), 0.9)
    lantern(c, 26, 18, 0.8)
    lantern(c, 74, 18, 0.8)
    c.shape(ellipse(50, 76, 36, 8))                               # table
    c.stroke(line((50, 84), (50, 97)), 1.2)
    c.stroke(line((40, 97), (60, 97)), 0.9)
    c.shape((arc(50, 62, 18, 180, 360, ry=6) + spline((68, 62), (66, 72), (50, 75), (34, 72), (32, 62))).close())
    c.shape(ellipse(50, 62, 18, 6))
    c.stroke(spline((34, 60), (46, 60), (54, 64), (66, 64)), 0.7)
    steam(c, 42, 50)
    steam(c, 58, 50)


# --------------------------------------------------------------------------------------- wood, materials

@b("PandabornLanternWorkshop", 84, "Lantern workshop: a bare lantern frame on the bench, a finished lantern hanging")
def lantern_workshop(c):
    c.shape(rrect(4, 70, 92, 7, 2))
    for x in (10, 90):
        c.stroke(line((x, 77), (x, 97)), 1.0)
    # bare frame: ribs only
    c.stroke(ellipse(34, 46, 20, 22), 0.8)
    for k in (0.45, 0.85):
        c.stroke(arc(34, 46, 20 * k, 90, 270, ry=22), 0.6)
        c.stroke(arc(34, 46, 20 * k, 90, -90, ry=22), 0.6)
    c.stroke(line((24, 70), (24, 66)), 0.7)
    c.stroke(line((44, 70), (44, 66)), 0.7)
    # finished lantern hanging from a bracket
    c.stroke(line((72, 4), (88, 4)), 0.8)
    c.stroke(line((80, 4), (80, 12)), 0.6)
    c.shape(rrect(74, 11, 12, 5, 1.5), 0.7)
    c.shape(ellipse(80, 32, 14, 16))
    c.stroke(arc(80, 32, 6, 90, 270, ry=16), 0.55)
    c.stroke(arc(80, 32, 6, 90, -90, ry=16), 0.55)
    c.shape(rrect(74, 48, 12, 5, 1.5), 0.7)
    c.stroke(line((80, 53), (80, 62)), 0.6)


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


# ------------------------------------------------------------------------------------------------- water

@b("PandabornCisternSmall", 56, "Small cistern: one hooped tub")
def cistern_small(c):
    cistern(c, 50, 92, 46, 40, hoops=2)
    ground(c, 20, 80)


@b("PandabornCisternMedium", 74, "Medium cistern: a tall hooped tub")
def cistern_medium(c):
    cistern(c, 50, 92, 52, 62, hoops=3)
    ground(c, 16, 84)


@b("PandabornCisternLarge", 92, "Large cistern: a wide hooped vat on a stone base with a ladder")
def cistern_large(c):
    c.shape(rrect(8, 86, 84, 11, 1), 0.9)
    cistern(c, 50, 86, 76, 56, hoops=3)
    c.stroke(line((86, 86), (94, 30)), 0.7)
    c.stroke(line((96, 86), (100, 32)), 0.7)
    for y in (76, 62, 48):
        c.stroke(line((88 + (86 - y) * 0.08, y), (97 + (86 - y) * 0.05, y)), 0.6)


@b("PandabornFlume", 90, "Flume: an open bamboo channel on X trestles, water running in it")
def flume(c):
    ground(c, 2, 98)
    flume_run(c, 4, 96, 40, 10)
    for x in (22, 78):
        trestle(c, x, 52, 97, 12)


@b("PandabornFlumeCorner", 86, "Flume corner: two channels meeting at a right angle on a trestle")
def flume_corner(c):
    ground(c, 2, 98)
    flume_run(c, 4, 60, 50, 10)
    with c.at(60, 55, 1, 60):
        flume_run(c, 0, 50, -5, 10)
    c.shape(rrect(52, 44, 14, 16, 3), 0.9)                        # joint box
    trestle(c, 30, 62, 97, 10)
    trestle(c, 62, 62, 97, 10)


@b("PandabornFlumeDrop", 86, "Flume drop: a channel stepping down, water falling to the lower channel")
def flume_drop(c):
    ground(c, 2, 98)
    flume_run(c, 4, 52, 24, 9)
    flume_run(c, 48, 96, 58, 9)
    for x in (44, 49):
        c.stroke(spline((x + 6, 34), (x + 10, 44), (x + 10, 56)), 0.7)
    trestle(c, 22, 35, 97, 10)
    trestle(c, 80, 69, 97, 8)


@b("PandabornFlumeBridge", 94, "Flume bridge: a channel carried high on tall trestles over a gap")
def flume_bridge(c):
    c.stroke(line((2, 97), (24, 97)))
    c.stroke(line((76, 97), (98, 97)))
    water(c, 90, 28, 72, rows=1)
    flume_run(c, 2, 98, 20, 10)
    for x in (16, 84):
        trestle(c, x, 32, 97, 12)
    c.stroke(line((16, 60), (84, 60)), 0.6)
    c.stroke(line((24, 32), (50, 58)), 0.5)
    c.stroke(line((76, 32), (50, 58)), 0.5)


@b("PandabornFlumeGate", 84, "Flume gate: a sliding board in a frame across the channel, with a handle")
def flume_gate(c):
    ground(c, 2, 98)
    flume_run(c, 4, 96, 56, 10)
    for x in (36, 64):
        c.stroke(line((x, 18), (x, 97)), 1.0)
    c.stroke(line((32, 18), (68, 18)), 1.0)
    c.shape(rrect(40, 34, 20, 30, 1), 0.9)                        # gate board, raised a little
    c.stroke(line((44, 44), (56, 44)), 0.55)
    c.stroke(line((50, 34), (50, 10)), 0.9)                       # rod and handle
    c.stroke(line((42, 8), (58, 8)), 1.1)
    trestle(c, 16, 68, 97, 8)
    trestle(c, 84, 68, 97, 8)


@b("PandabornScoopWheel", 96, "Scoop wheel: a tall bamboo wheel with tube buckets, lifting water from the current into a trough")
def scoop_wheel(c):
    water(c, 88, 2, 98)
    c.stroke(line((36, 97), (50, 52)), 0.8)
    c.stroke(line((64, 97), (50, 52)), 0.8)
    wheel(c, 50, 48, 40, 12, kind="tube")
    c.shape(rrect(74, 4, 26, 8, 2), 0.9)                          # trough at the top
    c.stroke(spline((80, 12), (82, 18)), 0.6)


@b("PandabornPaddySpout", 76, "Paddy spout: a bamboo spout pouring into a shallow field with a rice tuft")
def paddy_spout(c):
    c.shape(rrect(4, 40, 22, 57, 1))                              # earth bank with the pipe through it
    with c.at(20, 48, 1, -12):
        c.shape(rrect(0, -5, 40, 10, 5))
        c.shape(ellipse(40, 0, 3, 5), 0.8)
    c.stroke(spline((60, 58), (62, 68), (62, 80)), 0.7)
    c.stroke(spline((56, 58), (56, 70), (58, 80)), 0.7)
    water(c, 84, 28, 98)
    for a in (100, 78, 122):
        c.stroke(line((86, 84), (86 + math.cos(math.radians(a)) * 12, 84 - math.sin(math.radians(a)) * 22)), 0.7)


@b("PandabornDewCollector", 82, "Dew collector: a fine net between two bamboo poles, drops running into a jar")
def dew_collector(c):
    ground(c, 2, 98)
    bamboo_post(c, 12, 6, 97, 1.0)
    bamboo_post(c, 88, 6, 97, 1.0)
    net = rrect(14, 10, 72, 46, 1)
    c.shape(net, 0.7)
    for seg in hatch(net, 10, 45, margin=1.5) + hatch(net, 10, -45, margin=1.5):
        c.stroke(seg, 0.45)
    c.stroke(spline((14, 58), (50, 66), (86, 58)), 0.7)           # gutter
    for y in (70, 76):
        c.fill(spline((50, y - 3), (52, y + 1), (50, y + 2.5), (48, y + 1), closed=True))
    pao_jar(c, 50, 97, 0.6)


@b("PandabornTreadwheelLift", 94, "Treadwheel lift: a square-pallet chain pump in a sloping trough, worked by a treadle wheel")
def treadwheel_lift(c):
    water(c, 90, 2, 40, rows=1)
    with c.at(14, 92, 1, 32):                                     # the sloping trough with its chain
        c.shape(rrect(0, -10, 92, 10, 1))
        for x in range(8, 88, 12):
            c.stroke(line((x, -9), (x, -1)), 0.6)
    c.shape(circle(86, 40, 15))                                   # treadle wheel at the top
    for k in range(6):
        a = math.radians(k * 60)
        c.stroke(line((86, 40), (86 + math.cos(a) * 22, 40 - math.sin(a) * 22)), 0.8)
        c.shape(rrect(86 + math.cos(a) * 22 - 3, 40 - math.sin(a) * 22 - 2, 6, 4, 1.5), 0.6)
    c.stroke(line((70, 97), (86, 40)), 0.8)
    c.stroke(line((100, 97), (86, 40)), 0.8)
    c.stroke(line((60, 97), (100, 97)))


@b("PandabornDryStoneWall", 80, "Dry-stone wall: fitted stones holding up a tea terrace, a tea bush on top")
def dry_stone_wall(c):
    stones = [(4, 66, 26, 14), (32, 64, 30, 16), (64, 66, 32, 14), (4, 82, 34, 15), (40, 82, 22, 15),
              (64, 82, 32, 15)]
    for x, y, w, h in stones:
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


def kite_rotor(c, cx, cy, r, n):
    for k in range(n):
        a = math.radians(k * 360 / n + 15)
        with c.at(cx, cy, 1, math.degrees(a)):
            c.shape(spline((4, 0), (r * 0.45, -r * 0.2), (r, 0), (r * 0.45, r * 0.2), closed=True), 0.85)
            c.stroke(line((6, 0), (r * 0.95, 0)), 0.45)
            c.stroke(spline((r, 0), (r + 5, 4), (r + 9, 0), (r + 13, 4)), 0.55)       # kite tail
    c.shape(circle(cx, cy, 4), 0.8)


@b("PandabornKiteWindmillSmall", 72, "Small kite windmill: four kite-shaped sails with tails on a bamboo mast")
def kite_windmill_small(c):
    ground(c, 20, 80)
    c.stroke(line((44, 97), (50, 44)), 1.0)
    c.stroke(line((56, 97), (50, 44)), 1.0)
    kite_rotor(c, 50, 38, 32, 4)


@b("PandabornKiteWindmillLarge", 98, "Large kite windmill: six kite sails on a tall braced bamboo tower")
def kite_windmill_large(c):
    ground(c, 14, 86)
    c.stroke(line((36, 97), (50, 40)), 1.1)
    c.stroke(line((64, 97), (50, 40)), 1.1)
    c.stroke(line((40, 82), (60, 82)), 0.7)
    c.stroke(line((44, 64), (56, 64)), 0.7)
    kite_rotor(c, 50, 36, 40, 6)


# ---------------------------------------------------------------------------------------------- science

@b("PandabornStarTower", 96, "Star Tower (Ringtails): a slim wooden tower with an armillary sphere on top")
def star_tower(c):
    moon(c, 92, 8)
    ground(c, 18, 82)
    c.stroke(line((34, 97), (44, 44)), 1.0)
    c.stroke(line((66, 97), (56, 44)), 1.0)
    for y in (84, 70, 56):
        k = (97 - y) / 53
        c.stroke(line((34 + 10 * k, y), (66 - 10 * k, y)), 0.7)
    c.shape(rrect(38, 40, 24, 5, 1), 0.85)                        # platform
    c.stroke(circle(50, 22, 16), 0.85)                            # armillary sphere: rings
    c.stroke(ellipse(50, 22, 16, 5, rot=20), 0.7)
    c.stroke(ellipse(50, 22, 5, 16, rot=20), 0.7)
    c.stroke(line((50, 40), (50, 4)), 0.6)


# ---------------------------------------------------------------------------------------------- leisure

@b("PandabornHammock", 72, "Hammock: a woven hammock slung between two bamboo posts, a leaf canopy")
def hammock(c):
    ground(c, 4, 96)
    bamboo_post(c, 10, 30, 97, 1.0, nodes=1)
    bamboo_post(c, 90, 30, 97, 1.0, nodes=1)
    sling = spline((12, 44), (30, 66), (50, 72), (70, 66), (88, 44))
    c.stroke(sling, 1.1)
    c.stroke(spline((20, 56), (36, 72), (50, 76), (64, 72), (80, 56)), 0.7)
    for x in (30, 50, 70):
        y = float(np.interp(x, sling.pts[:, 0], sling.pts[:, 1]))
        c.stroke(line((x, y), (x, y + 6)), 0.5)
    for x, a in ((10, 140), (10, 100), (90, 40), (90, 80)):
        with c.at(x, 30, 1, a):
            c.shape(spline((0, 0), (8, -4), (20, 0), (8, 4), closed=True), 0.7)


@b("PandabornNapPlatform", 84, "Nap platform: a raised shaded deck with round cushions")
def nap_platform(c):
    ground(c, 2, 98)
    roof(c, 50, 12, 92, 18, tiles=4)
    for x in (12, 88):
        c.stroke(line((x, 28), (x, 97)), 0.9)
    c.shape(rrect(6, 70, 88, 7, 2))                               # deck
    for x in (26, 50, 74):
        c.shape(ellipse(x, 64, 11, 6), 0.85)
    c.stroke(line((20, 77), (20, 97)), 0.7)
    c.stroke(line((80, 77), (80, 97)), 0.7)


@b("PandabornTeahouse", 88, "Teahouse: an open pavilion with a big teapot and cups on the counter")
def teahouse(c):
    ground(c, 2, 98)
    roof(c, 50, 4, 100, 20, tiles=5)
    for x in (8, 92):
        c.stroke(line((x, 22), (x, 97)), 0.9)
    lantern(c, 20, 22, 0.75)
    c.shape(rrect(18, 74, 64, 6, 2))                              # counter
    c.stroke(line((24, 80), (24, 97)), 0.7)
    c.stroke(line((76, 80), (76, 97)), 0.7)
    c.shape(spline((34, 72), (32, 56), (40, 48), (56, 48), (64, 56), (62, 72), closed=True))   # teapot
    c.shape(rrect(44, 42, 8, 6, 2), 0.8)
    c.stroke(spline((34, 60), (24, 56), (20, 48)), 1.0)           # spout
    c.stroke(spline((62, 54), (72, 54), (70, 66), (62, 68)), 0.9)  # handle
    c.shape(spline((70, 74), (70, 66), (80, 66), (80, 74), closed=True), 0.7)
    steam(c, 20, 44, 12, 0.7)


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


@b("PandabornPandaKindergarten", 86, "Panda kindergarten: a little house with panda ears on its roof, a ball in the fenced yard")
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


@b("PandabornOperaStage", 96, "Opera stage (Ringtails): a raised pavilion stage, curtains drawn back, an opera mask")
def opera_stage(c):
    moon(c, 92, 8)
    roof(c, 50, 8, 92, 20, tiles=4)
    for x in (12, 88):
        c.stroke(line((x, 26), (x, 72)), 1.0)
    c.stroke(spline((14, 28), (22, 44), (16, 60)), 0.8)            # curtains
    c.stroke(spline((86, 28), (78, 44), (84, 60)), 0.8)
    c.stroke(line((12, 30), (88, 30)), 0.7)
    # mask: an opera face with bold brows and eye patches (plain pattern)
    c.shape(spline((36, 36), (50, 32), (64, 36), (64, 50), (58, 62), (50, 66), (42, 62), (36, 50), closed=True))
    c.fill(spline((40, 44), (44, 40), (48, 46), (44, 48), closed=True))
    c.fill(spline((60, 44), (56, 40), (52, 46), (56, 48), closed=True))
    c.stroke(spline((40, 38), (50, 42), (60, 38)), 0.6)
    c.stroke(spline((46, 56), (50, 58), (54, 56)), 0.6)
    c.shape(rrect(4, 72, 92, 8, 1))                               # stage floor
    c.shape(rrect(8, 80, 84, 17, 1), 0.9)
    for x in (30, 50, 70):
        c.stroke(line((x, 82), (x, 95)), 0.5)


# ------------------------------------------------------------------------------------- Ringtail posts

@b("PandabornNightBuildersPost", 80, "Night builders' post (Ringtails): a lantern on a post, a mallet and a pole crossed")
def night_builders_post(c):
    moon(c, 92, 8)
    ground(c, 6, 94)
    bamboo_post(c, 30, 14, 97, 1.0)
    c.stroke(line((30, 16), (44, 16)), 0.8)
    lantern(c, 42, 16, 0.9)
    with c.at(66, 70, 1, 40):                                      # mallet
        c.stroke(line((-24, 0), (14, 0)), 1.0)
        c.shape(rrect(14, -8, 12, 16, 3), 0.9)
    with c.at(66, 70, 1, -40):                                     # bamboo pole
        c.stroke(line((-26, 0), (26, 0)), 1.1, taper=0)
        c.stroke(line((0, -3), (0, 3)), 0.6, taper=0)


@b("PandabornNightCourierPost", 80, "Night courier post (Ringtails): a woven back-basket with a lantern hung on it")
def night_courier_post(c):
    moon(c, 92, 8)
    ground(c, 6, 94)
    basket = spline((24, 40), (20, 70), (30, 94), (70, 94), (80, 70), (76, 40), closed=False)
    region = (basket + line((76, 40), (24, 40))).close()
    c.shape(region)
    for seg in hatch(region, 10, 90, margin=3) + hatch(region, 12, 0, margin=3):
        c.stroke(seg, 0.45)
    c.shape(ellipse(50, 40, 26, 6))
    c.stroke(spline((28, 40), (24, 20), (34, 12)), 0.8)            # straps
    c.stroke(spline((72, 40), (76, 20), (66, 12)), 0.8)
    c.stroke(line((76, 44), (90, 40)), 0.7)
    lantern(c, 88, 40, 0.75)


@b("PandabornNightForagersPost", 80, "Night forager's post (Ringtails): a basket of bamboo mushrooms and a lantern")
def night_foragers_post(c):
    moon(c, 92, 8)
    ground(c, 6, 94)
    bamboo_post(c, 84, 24, 97, 0.9, nodes=1)
    c.stroke(line((84, 26), (72, 26)), 0.7)
    lantern(c, 72, 26, 0.75)
    for x, h in ((34, 34), (50, 40)):                              # netted mushrooms in the basket
        c.shape(spline((x - 4, 74), (x - 4, 74 - h * 0.5), (x + 4, 74 - h * 0.5), (x + 4, 74), closed=True), 0.7)
        c.shape(spline((x - 9, 74 - h * 0.5), (x - 6, 74 - h), (x, 74 - h - 4), (x + 6, 74 - h),
                       (x + 9, 74 - h * 0.5), closed=True), 0.8)
        c.stroke(line((x - 6, 74 - h * 0.6), (x + 6, 74 - h * 0.6)), 0.5)
    basket = (spline((18, 70), (22, 92), (40, 96), (58, 92), (62, 70))).close()
    c.shape(basket)
    for seg in hatch(basket, 9, 90, margin=3):
        c.stroke(seg, 0.45)


# -------------------------------------------------------------------------------------- monuments

@b("PandabornMemorialArch", 92, "Memorial arch: a three-bay stone and timber arch with gentle tile roofs and a blank panel")
def memorial_arch(c):
    ground(c, 2, 98)
    for x in (12, 36, 64, 88):
        c.shape(rrect(x - 4, 36, 8, 61, 1), 0.9)
        c.shape(rrect(x - 7, 90, 14, 7, 1), 0.8)
    c.shape(rrect(8, 36, 84, 8, 1), 0.9)
    c.shape(rrect(40, 22, 20, 12, 1), 0.85)                       # blank panel, no writing
    roof(c, 50, 6, 46, 16, tiles=3)
    roof(c, 16, 24, 26, 12, tiles=1)
    roof(c, 84, 24, 26, 12, tiles=1)


@b("PandabornGreatSittingPanda", 98, "Great sitting panda: a big seated panda carved into a rock outcrop, water at its feet")
def great_sitting_panda(c):
    c.shape(spline((2, 86), (6, 50), (14, 24), (30, 8), (50, 2), (72, 8), (88, 26), (96, 52), (98, 86),
                   closed=True), 0.9)                              # rock outcrop
    c.stroke(spline((8, 60), (14, 48)), 0.5)
    c.stroke(spline((92, 62), (88, 48)), 0.5)
    # the seated panda, relaxed: round head, ears, body, arms resting, feet forward
    c.shape(spline((24, 84), (22, 60), (32, 44), (50, 40), (68, 44), (78, 60), (76, 84), closed=True))
    c.shape(circle(37, 18, 6), 0.9)
    c.shape(circle(63, 18, 6), 0.9)
    c.shape(circle(50, 30, 15))
    c.fill(ellipse(44, 29, 3.5, 4.5, rot=-30))
    c.fill(ellipse(56, 29, 3.5, 4.5, rot=30))
    c.fill(ellipse(50, 36, 2.5, 1.8))
    c.stroke(spline((30, 52), (36, 66), (46, 68)), 0.8)            # arms resting on the belly
    c.stroke(spline((70, 52), (64, 66), (54, 68)), 0.8)
    c.shape(ellipse(34, 84, 10, 6), 0.9)                           # feet
    c.shape(ellipse(66, 84, 10, 6), 0.9)
    c.erase(rrect(0, 89, 100, 14, 0))                              # water at its feet, in front
    water(c, 92, 0, 100)


@b("PandabornSkyLantern", 98, "Sky Lantern (wonder): a huge paper lantern in its launch cradle, a flame glowing inside")
def sky_lantern(c):
    ground(c, 2, 98)
    c.shape(spline((24, 70), (18, 40), (24, 14), (50, 4), (76, 14), (82, 40), (76, 70), closed=True))
    for k in (0.4, 0.8):
        c.stroke(spline((50 - 30 * k, 68), (50 - 34 * k, 40), (50 - 26 * k, 12)), 0.6)
        c.stroke(spline((50 + 30 * k, 68), (50 + 34 * k, 40), (50 + 26 * k, 12)), 0.6)
    c.shape(ellipse(50, 70, 26, 5), 0.9)                           # open bottom ring
    c.fill(spline((50, 62), (54, 70), (50, 74), (46, 70), closed=True))     # the flame
    for x0, x1 in ((6, 26), (94, 74)):                             # launch cradle and ropes
        c.stroke(line((x0, 97), (x1, 72)), 1.0)
    c.stroke(line((14, 86), (86, 86)), 0.9)
    c.stroke(line((26, 72), (74, 72)), 0.9)
    c.stroke(line((10, 92), (22, 40)), 0.5)
    c.stroke(line((90, 92), (78, 40)), 0.5)
