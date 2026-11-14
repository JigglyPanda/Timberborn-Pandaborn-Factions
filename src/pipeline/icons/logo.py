"""Faction logo (FactionSpec.Logo), in the vanilla form: a rounded diamond frame around a solid emblem, one flat
colour (Folktails pale yellow with a leaf, Iron Teeth pink with a gear-tree). Inkpaws: bamboo green.

Three candidates render to the build dir (avatars_sheet.png); the chosen one is registered again as
"InkpawsLogo" and shipped to Sprites/Pandaborn/Avatars/InkpawsLogo.png (the path FactionSpec.Logo uses).
Everything inside the frame keeps |x-50| + |y-50| < ~38.
"""
import math

import numpy as np

from ink import LOGO, Path, circle, icon, rrect, spline


def frame(c):
    with c.at(50, 50, 1, 45):
        c.shape(rrect(-36, -36, 72, 72, 9), occlude=False)


def bamboo_emblem(c, top=41, bottom=80, leaves=True):
    c.fill(Path(np.array([[42, bottom], [58, bottom], [57.5, 63], [42.5, 63]]), True))
    c.fill(Path(np.array([[42.5, 59], [57.5, 59], [57, top + 3], [43, top + 3]]), True))
    c.fill(rrect(40, 58.5, 20, 5, 2.5))
    c.fill(rrect(40.5, top, 19, 5, 2.5))
    if leaves:
        c.fill(spline((46, top + 3), (36, top - 4), (26, top - 3), (18, top + 3), (28, top + 7), (40, top + 7),
                      closed=True))
        c.fill(spline((54, top + 1), (62, top - 8), (71, top - 11), (79, top - 8), (71, top), (60, top + 3),
                      closed=True))
        c.fill(spline((48, top), (44, top - 11), (47, top - 21), (53, top - 28), (56, top - 17), (53, top - 5),
                      closed=True))


@icon("InkpawsLogoBamboo", group="Avatars", style=LOGO, ship=False, suffix="",
      note="Logo candidate A: a jointed bamboo stalk with three leaves")
def logo_bamboo(c):
    frame(c)
    bamboo_emblem(c)


@icon("InkpawsLogoPaw", group="Avatars", style=LOGO, ship=False, suffix="",
      note="Logo candidate B: a panda paw print (big pad, five toes)")
def logo_paw(c):
    frame(c)
    c.fill(spline((32, 62), (36, 50), (50, 46), (64, 50), (68, 62), (62, 74), (50, 76), (38, 74), closed=True))
    for k, a in enumerate((150, 118, 90, 62, 30)):
        r = 24 if k in (0, 4) else 26
        x, y = 50 + math.cos(math.radians(a)) * r, 58 - math.sin(math.radians(a)) * r
        c.fill(circle(x, y, 5.6 if k in (0, 4) else 6.4))


@icon("InkpawsLogoSunMoon", group="Avatars", style=LOGO, ship=False, suffix="",
      note="Logo candidate C: sun and moon over a bamboo stalk (the two peoples, day and night)")
def logo_sun_moon(c):
    frame(c)
    bamboo_emblem(c, top=50, bottom=82, leaves=False)
    c.fill(spline((48, 53), (38, 48), (28, 50), (24, 56), (34, 57), (44, 57), closed=True))
    c.fill(spline((52, 51), (62, 46), (72, 46), (76, 52), (66, 55), (56, 55), closed=True))
    c.fill(circle(38, 34, 7.5))                                   # sun
    c.fill(circle(62, 34, 7.5))                                   # moon: a crescent
    c.erase(circle(66, 31, 6.4))


# The pick (see docs/tech/icons.md): the paw print reads at 40 px and is unlike both vanilla emblems.
icon("InkpawsLogo", group="Avatars", style=LOGO, suffix="", note="Inkpaws logo (shipped)")(logo_paw)
