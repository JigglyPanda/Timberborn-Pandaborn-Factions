"""Faction logo (FactionSpec.Logo), in the vanilla form: a rounded diamond frame around a solid emblem, one flat
colour (Folktails pale yellow with a leaf, Iron Teeth pink with a gear-tree). Inkpaws: bamboo green, a bamboo
stalk with two leaves. Proposal only (ship=False); the current Sprites/Pandaborn/Avatars/InkpawsLogo.png belongs to
another work stream.
"""
from ink import LOGO, Path, icon, rrect, spline
import numpy as np


@icon("InkpawsLogo", group="Avatars", style=LOGO, ship=False, suffix="",
      note="Inkpaws logo proposal: diamond frame, solid bamboo stalk with two leaves")
def inkpaws_logo(c):
    with c.at(50, 50, 1, 45):
        c.shape(rrect(-36, -36, 72, 72, 9), occlude=False)
    # everything inside the frame keeps |x-50| + |y-50| < ~38
    # stalk: two solid segments with node rings between them
    c.fill(Path(np.array([[42, 80], [58, 80], [57.5, 63], [42.5, 63]]), True))
    c.fill(Path(np.array([[42.5, 59], [57.5, 59], [57, 44], [43, 44]]), True))
    c.fill(rrect(40, 58.5, 20, 5, 2.5))
    c.fill(rrect(40.5, 41, 19, 5, 2.5))
    # three leaves from the top node
    c.fill(spline((46, 44), (36, 37), (26, 38), (18, 44), (28, 48), (40, 48), closed=True))
    c.fill(spline((54, 42), (62, 33), (71, 30), (79, 33), (71, 41), (60, 44), closed=True))
    c.fill(spline((48, 41), (44, 30), (47, 20), (53, 13), (56, 24), (53, 36), closed=True))
