"""Bottom-bar tool group icons (BlockObjectToolGroupSpec.Icon) in the vanilla bottom-bar style.

Vanilla group icons (Sprites/BottomBar/BuildingGroups/<Group>, 112 x 112) are not the gold line drawings of the
building icons: they are small painted signs, a gold outline about 3.5 px wide round flat colour, each colour area
hatched with a few strokes of a second tone, no shadow (the water drop, the two masks, the atom, the open door).

The Inkpaws add one group, Night Watch (every Ringtail building). Its sign is the night folk's two things: the
crescent moon of the moon mark, in the pale yellow of the vanilla Housing door, and a red paper lantern hung from
its upper horn.

An icon here is a list of layers drawn on one shared frame (`Icon.bounds`): colour areas first (a solid mask drawn
with the ink engine, painted in one colour, hatched in a second), the gold outline last.

usage (venv python): python -I src/pipeline/icons/toolgroup.py [--mod DIR] [--out DIR] [--no-mod]
  writes <mod>/Sprites/Pandaborn/BottomBar/Pandaborn<Group>Icon.png (+ .meta.json {"isSprite": true}) and
  <out>/toolgroups_sheet.png (beside the vanilla group icons, at 112, 56 and 40 px)
"""
import argparse
import glob
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import ink  # noqa: E402
from ink import Icon, arc, circle, clip, ellipse, line, rrect  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
GOLD = (190, 160, 108)
# no shadow, a round pen with a little wobble; extent as the vanilla group icons (their ink is 52..88 px of 112)
SIGN = ink.Style("toolgroup", canvas=112, extent=84, extent_tall=84, pen=3.6, ink=GOLD, shadow_dy=0, shadow_grow=0,
                 shadow_alpha=0.0, wobble=0.35, width_jitter=0.10, taper=0.0, center_dy=0.0)
BOX = ((0, 0), (100, 100))

GROUPS = {}


def group(name):
    def deco(fn):
        GROUPS[name] = fn
        return fn
    return deco


def _mask(draw, name):
    c = Icon(name=name, bounds=BOX, extent=SIGN.extent)
    draw(c)
    return np.asarray(ink.render(c, SIGN, seed_name=name))[..., 3].astype(float) / 255


def _hatch(c, x0, y0, x1, y1, spacing, ang, w):
    """Loose parallel strokes across a box (the mask of the colour area clips them)."""
    a = math.radians(ang)
    d = np.array([math.cos(a), -math.sin(a)])
    n = np.array([-d[1], d[0]])
    mid = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
    half = math.hypot(x1 - x0, y1 - y0) / 2
    k = -half
    i = 0
    while k <= half:
        p = mid + n * k
        ln = half * (0.55 + 0.4 * ((i * 37) % 10) / 10)               # uneven lengths, like brush strokes
        off = ((i * 53) % 7 - 3) * 1.5
        c.stroke(line(tuple(p - d * ln + d * off), tuple(p + d * ln + d * off)), w)
        k += spacing
        i += 1


def paint(name):
    """Compose one group icon: [(area mask fn, colour, hatch fn or None, hatch colour)], then the outline."""
    areas, outline = GROUPS[name]()
    S = SIGN.canvas
    rgb = np.zeros((S, S, 3))
    alpha = np.zeros((S, S))
    for k, (area, colour, hatch, hatch_colour) in enumerate(areas):
        m = _mask(area, "%s.area%d" % (name, k))
        col = np.broadcast_to(np.asarray(colour, float), (S, S, 3)).copy()
        if hatch is not None:
            h = _mask(hatch, "%s.hatch%d" % (name, k))[..., None]
            col = col * (1 - h) + np.asarray(hatch_colour, float) * h
        rgb = rgb * (1 - m[..., None]) + col * m[..., None]
        alpha = np.maximum(alpha, m)
    o = _mask(outline, name + ".outline")
    rgb = rgb * (1 - o[..., None]) + np.asarray(GOLD, float) * o[..., None]
    alpha = np.maximum(alpha, o)
    return Image.fromarray(np.dstack([rgb, alpha * 255]).round().clip(0, 255).astype(np.uint8), "RGBA")


# ---------------------------------------------------------------------------------------------- Night Watch

MOON_OUT = (44, 50, 37)        # centre x, y, radius
MOON_CUT = (59, 41, 31)
LANTERN = (71, 58, 12.5, 14.5)  # centre x, y, rx, ry


def _horn():
    """The crescent's upper horn tip: where the two circles meet, top right."""
    (x0, y0, r0), (x1, y1, r1) = MOON_OUT, MOON_CUT
    d = math.hypot(x1 - x0, y1 - y0)
    a = (r0 * r0 - r1 * r1 + d * d) / (2 * d)
    h = math.sqrt(max(0.0, r0 * r0 - a * a))
    ux, uy = (x1 - x0) / d, (y1 - y0) / d
    pts = [(x0 + ux * a - uy * h * s, y0 + uy * a + ux * h * s) for s in (-1, 1)]
    return min(pts, key=lambda p: p[1])


@group("PandabornNightWatch")
def night_watch():
    lx, ly, lrx, lry = LANTERN
    hx, hy = _horn()

    def moon_area(c):
        c.fill(circle(*MOON_OUT))
        c.erase(circle(*MOON_CUT))

    def moon_hatch(c):
        _hatch(c, 6, 12, 60, 90, 8.5, 52, 0.62)

    def lantern_area(c):
        c.fill(ellipse(lx, ly, lrx, lry))

    def lantern_hatch(c):
        for k in (-0.45, 0.45):
            c.stroke(arc(lx, ly, lrx * abs(k), 90, 270 if k < 0 else -90, ry=lry * 0.92), 0.55)

    def outline(c):
        c.stroke(circle(*MOON_OUT))
        c.erase(circle(*MOON_CUT))
        for seg in clip(circle(*MOON_CUT), circle(*MOON_OUT)):
            c.stroke(seg)
        c.stroke(line((hx - 1, hy + 1), (lx, ly - lry - 5)), 0.6)            # the string from the horn
        c.shape(rrect(lx - 5, ly - lry - 5, 10, 5, 1.5), 0.75, filled=True)   # cap
        c.shape(ellipse(lx, ly, lrx, lry), occlude=False)
        c.shape(rrect(lx - 5, ly + lry, 10, 4.5, 1.5), 0.75, filled=True)     # foot
        c.stroke(line((lx, ly + lry + 4), (lx, ly + lry + 12)), 0.7)          # tassel

    return ([(moon_area, (240, 208, 120), moon_hatch, (205, 172, 104)),
             (lantern_area, (158, 60, 48), lantern_hatch, (206, 104, 76))], outline)


# -------------------------------------------------------------------------------------------------- output

def sheet(images, out_png, vanilla_dir=r"E:\PandabornDev\reference\vanilla-icons\sprites\bottombar\buildinggroups"):
    vs = [Image.open(v).convert("RGBA") for v in sorted(glob.glob(os.path.join(vanilla_dir, "*.png")))]
    wb = [k for k, v in enumerate(sorted(glob.glob(os.path.join(vanilla_dir, "*.png")))) if "wellbeing" in v]
    row = vs[: (wb[0] + 1) if wb else len(vs)] + list(images) + (vs[wb[0] + 1:] if wb else [])
    cell = 120
    sh = Image.new("RGBA", (len(row) * cell + 8, 112 + 56 + 40 + 40), (34, 53, 42, 255))
    for k, im in enumerate(row):
        x = 8 + k * cell
        sh.alpha_composite(im.resize((112, 112), Image.LANCZOS), (x, 6))
        sh.alpha_composite(im.resize((56, 56), Image.LANCZOS), (x + 28, 126))
        sh.alpha_composite(im.resize((40, 40), Image.LANCZOS), (x + 36, 190))
    sh.convert("RGB").save(out_png)


def build(mod=None, out=r"E:\PandabornDev\build\icons"):
    """Render every group icon; write it to the mod (unless mod is None) and the sheet to the build dir."""
    imgs = []
    for name in GROUPS:
        img = paint(name)
        imgs.append(img)
        os.makedirs(os.path.join(out, "rendered", "BottomBar"), exist_ok=True)
        img.save(os.path.join(out, "rendered", "BottomBar", name + "Icon.png"))
        where = "build only"
        if mod:
            dest = os.path.join(mod, "Sprites", "Pandaborn", "BottomBar")
            os.makedirs(dest, exist_ok=True)
            img.save(os.path.join(dest, name + "Icon.png"), optimize=True)
            with open(os.path.join(dest, name + "Icon.png.meta.json"), "w", encoding="utf-8", newline="\n") as fh:
                json.dump({"isSprite": True}, fh, indent=2)
                fh.write("\n")
            where = "mod"
        print(f"BottomBar/{name}Icon.png ({where})")
    sheet(imgs, os.path.join(out, "toolgroups_sheet.png"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mod", default=os.path.join(REPO, "mod", "PandabornFactions"))
    ap.add_argument("--out", default=r"E:\PandabornDev\build\icons")
    ap.add_argument("--no-mod", action="store_true")
    a = ap.parse_args()
    build(None if a.no_mod else a.mod, a.out)


if __name__ == "__main__":
    main()
