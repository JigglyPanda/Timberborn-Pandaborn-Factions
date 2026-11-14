"""Banner decals (DecalSpec category "Banners") for the Inkpaws: the cloth pictures on the Pole and Square Banner.

Vanilla banner decals (Materials/Banners/<Faction>/BannerN.<Faction>, 512 x 512, opaque) are a worn cloth in one
faction colour with one solid emblem in a second colour, ringed by a dark rough halo: Folktails yellow on teal (leaf
diamond, tree, windmill, wheat), Iron Teeth pink on navy (gear diamond, boar, flame, tools). Ours follow that form in
the Inkpaws colours: a cream emblem on lacquer red, ten emblems from the faction's own things. No writing or
characters of any script, no religious signs.

The emblem is drawn with the icon engine (solid fills, `ink.Icon`) as a mask; the cloth, halo and wear are painted
here with numpy. Every texture is named Pandaborn<Name>: a decal's id is its texture's asset name, and a duplicate
name in a category is dropped silently.

usage (venv python): python -I src/pipeline/icons/banners.py [--out DIR] [--sheet DIR]
  default --out  mod/PandabornFactions/Materials/Pandaborn/Decals/Banners
  default --sheet E:\\PandabornDev\\build\\icons  (banners_sheet.png beside the vanilla ones, if extracted to
                  E:\\PandabornDev\\reference\\vanilla-banners by extract_vanilla_icons.py ... materials/banners/)
"""
import argparse
import glob
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
from PIL import Image, ImageFilter  # noqa: E402
from scipy import ndimage  # noqa: E402

import ink  # noqa: E402
from ink import Icon, Path, arc, circle, ellipse, line, poly, rrect, spline  # noqa: E402

S = 512
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CLOTH_HI, CLOTH_LO = np.array([0.60, 0.17, 0.13]), np.array([0.40, 0.09, 0.08])    # lacquer red
EMBLEM = np.array([0.93, 0.86, 0.69])                                              # cream
HALO = np.array([0.24, 0.05, 0.05])
# the emblem mask: pen in px at 512, no shadow; drawn in a 100-unit box like the icons
MASK = ink.Style("banner", canvas=S, extent=372, extent_tall=400, pen=26.0, ink=(255, 255, 255),
                 shadow_dy=0, shadow_grow=0, shadow_alpha=0.0, wobble=0.0, center_dy=0.0)

BANNERS = {}


def banner(name, extent=None):
    def deco(fn):
        BANNERS[name] = (fn, extent)
        return fn
    return deco


def star(c, x, y, r):
    c.fill(poly((x, y - r), (x + r * 0.28, y - r * 0.28), (x + r, y), (x + r * 0.28, y + r * 0.28), (x, y + r),
                (x - r * 0.28, y + r * 0.28), (x - r, y), (x - r * 0.28, y - r * 0.28)))


def leaf_shape(c, x, y, length, width, ang, vein=True):
    with c.at(x, y, 1, ang):
        c.fill(spline((0, 0), (length * 0.3, -width / 2), (length * 0.75, -width * 0.35), (length, 0),
                      (length * 0.75, width * 0.35), (length * 0.3, width / 2), closed=True))
        if vein:
            c.erase(line((length * 0.12, 0), (length * 0.8, 0)), 0.28)


# ------------------------------------------------------------------------------------------------ emblems

@banner("PandabornBannerPaw")
def paw(c):
    """The faction logo: a paw print in a rounded diamond."""
    with c.at(50, 50, 1, 45):
        c.stroke(rrect(-36, -36, 72, 72, 9).close(), 0.55)
    c.fill(spline((32, 62), (36, 50), (50, 46), (64, 50), (68, 62), (62, 74), (50, 76), (38, 74), closed=True))
    for k, a in enumerate((150, 118, 90, 62, 30)):
        r = 24 if k in (0, 4) else 26
        x, y = 50 + math.cos(math.radians(a)) * r, 58 - math.sin(math.radians(a)) * r
        c.fill(circle(x, y, 5.6 if k in (0, 4) else 6.4))


@banner("PandabornBannerBamboo")
def bamboo(c):
    """A jointed bamboo culm with a spray of leaves."""
    with c.at(44, 96, 1, 80):
        for k, (a, b) in enumerate(((0, 30), (33, 60), (63, 88))):
            c.fill(rrect(a, -6, b - a, 12, 3))
        c.fill(rrect(30, -8, 4, 16, 2))
        c.fill(rrect(60, -8, 4, 16, 2))
    leaf_shape(c, 50, 40, 38, 15, 20)
    leaf_shape(c, 50, 44, 34, 14, 62)
    leaf_shape(c, 47, 60, 36, 14, 160)
    leaf_shape(c, 48, 30, 28, 12, 118)


@banner("PandabornBannerMoon")
def moon(c):
    """The Ringtails: a crescent moon and two stars."""
    c.fill(circle(46, 52, 34))
    c.erase(circle(62, 42, 29))
    star(c, 74, 66, 9)
    star(c, 82, 34, 6)


@banner("PandabornBannerLantern")
def lantern(c):
    """A round paper lantern with its ribs, cap, base and tassel."""
    c.fill(rrect(38, 8, 24, 9, 2))
    c.fill(rrect(38, 79, 24, 9, 2))
    c.fill(ellipse(50, 48, 34, 32))
    for k in (0.38, 0.76):
        c.erase(arc(50, 48, 34 * k, 90, 270, ry=31), 0.3)
        c.erase(arc(50, 48, 34 * k, 90, -90, ry=31), 0.3)
    c.fill(rrect(46, 2, 8, 8, 2))
    c.fill(poly((46, 88), (54, 88), (58, 100), (42, 100)))


@banner("PandabornBannerTeaLeaf")
def tea_leaf(c):
    """One bud and two leaves (the tea flush)."""
    c.stroke(spline((50, 98), (52, 70), (50, 46)), 0.5)
    leaf_shape(c, 50, 62, 40, 18, 150)
    leaf_shape(c, 51, 70, 38, 17, 30)
    leaf_shape(c, 50, 48, 46, 13, 88)


@banner("PandabornBannerRice")
def rice(c):
    """A drooping ear of rice on its stalk, with a leaf."""
    stalk = spline((40, 100), (42, 60), (50, 30), (64, 16), (78, 20), (84, 34))
    c.stroke(stalk, 0.4)
    pts = stalk.pts
    n = len(pts)
    for t in np.linspace(0.48, 0.98, 9):
        i = int(t * (n - 1))
        x, y = pts[i]
        d = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
        a = math.degrees(math.atan2(-d[1], d[0]))
        for side in (-1, 1):
            with c.at(x, y, 1, a + side * 55):
                c.fill(ellipse(6.5, 0, 7.5, 4.4))
    leaf_shape(c, 41, 72, 40, 9, 135, vein=False)


@banner("PandabornBannerFlume")
def flume(c):
    """Water: the split-bamboo flume end-on, three waves running in it."""
    c.fill((arc(50, 34, 40, 180, 360, ry=40) + arc(50, 34, 30, 360, 180, ry=30)).close())
    for k, y in enumerate((44, 54, 63)):
        xs = np.linspace(28 + k * 5, 72 - k * 5, 40)
        c.stroke(Path(np.stack([xs, y + np.sin((xs - 20) / 4.5) * 2.4], 1)), 0.32)
    for x in (24, 76):                                   # the lashed X-stakes under it
        c.stroke(line((x - 12, 100), (x + 8, 62)), 0.38)
        c.stroke(line((x + 12, 100), (x - 8, 62)), 0.38)


@banner("PandabornBannerBell")
def bell(c):
    """The village bell: a flared bronze bell on its loop, a band of bosses."""
    c.fill(rrect(43, 4, 14, 14, 6))
    c.erase(rrect(47, 8, 6, 6, 3))
    c.fill(spline((32, 22), (68, 22), (70, 50), (78, 82), (50, 86), (22, 82), (30, 50), closed=True))
    c.erase(line((27, 66), (73, 66)), 0.28)
    for x in (36, 50, 64):
        c.erase(circle(x, 38, 3.4))
    c.fill(ellipse(50, 92, 7, 5))


@banner("PandabornBannerPanda")
def panda(c):
    """A panda face: the ears and eye patches cut from the cream head, as the cloth shows through."""
    c.fill(circle(22, 22, 13))
    c.fill(circle(78, 22, 13))
    c.fill(ellipse(50, 56, 40, 36))
    for sx in (-1, 1):
        c.erase(ellipse(50 + sx * 16, 52, 9, 12, rot=sx * -30))
        c.fill(circle(50 + sx * 15, 50, 3.2))
    c.erase(ellipse(50, 70, 6, 4.2))
    c.erase(spline((42, 80), (50, 84), (58, 80)), 0.2)


@banner("PandabornBannerRingTail")
def ring_tail(c):
    """The red panda's tail: long and bushy, rising on a gentle curve, ringed along its length."""
    tail = spline((14, 90), (26, 70), (36, 54), (50, 40), (66, 28), (86, 18))
    pts = tail.pts
    n = len(pts)
    for i in range(0, n, 2):                               # bushy: overlapping discs, thinning to the tip
        t = i / (n - 1)
        r = 13 + 3 * math.sin(t * math.pi) - 2 * t
        c.fill(circle(pts[i][0], pts[i][1], r))
    for t in (0.16, 0.32, 0.48, 0.64, 0.80):
        i = int(t * (n - 1))
        p = pts[i]
        d = pts[min(i + 2, n - 1)] - pts[max(i - 2, 0)]
        d = d / (np.linalg.norm(d) + 1e-9)
        nrm = np.array([-d[1], d[0]])
        w = 20
        c.erase(Path(np.array([p - nrm * w - d * 3, p + nrm * w - d * 3, p + nrm * w + d * 3, p - nrm * w + d * 3]),
                     True))


# ------------------------------------------------------------------------------------------------ painting

def _noise(rng, scale, octaves=4):
    out = np.zeros((S, S))
    for o in range(octaves):
        s = scale / 2 ** o
        n = rng.random((int(S / s) + 3, int(S / s) + 3))
        out += ndimage.zoom(n, (S / (n.shape[0] - 2), S / (n.shape[1] - 2)), order=3)[:S, :S] / 2 ** o
    return out / (2 - 2 ** (1 - octaves))


def paint(name, fn, extent, seed):
    rng = np.random.default_rng(seed)
    ic = Icon(name=name, extent=extent)
    fn(ic)
    m = np.asarray(ink.render(ic, MASK, seed_name=name))[..., 3].astype(float) / 255
    yy, xx = np.mgrid[0:S, 0:S] / S
    # the cloth: a soft vignette, a fabric weave, blotches
    r = np.sqrt((xx - 0.5) ** 2 + (yy - 0.45) ** 2)
    g = np.clip(1 - r * 1.3, 0, 1)[..., None]
    cloth = CLOTH_LO + (CLOTH_HI - CLOTH_LO) * g
    cloth = cloth * (0.86 + 0.24 * _noise(rng, 90)[..., None])
    weave = (np.sin(xx * S * 1.6) * np.sin(yy * S * 1.6)) * 0.025
    cloth = cloth * (1 + weave[..., None])
    # the halo: the emblem grown by a rough margin, darker cloth
    grow = ndimage.distance_transform_edt(m < 0.5)
    rough = 26 + (_noise(rng, 40, 3) - 0.5) * 14
    halo = np.clip((rough - grow) / 4.0, 0, 1)
    out = cloth * (1 - halo[..., None] * 0.85) + HALO * halo[..., None] * 0.85
    # the emblem: cream, worn in patches and speckles
    wear = np.clip((_noise(rng, 60) - 0.25) * 2.4, 0.78, 1)
    speck = (rng.random((S, S)) > 0.985).astype(float)
    speck = ndimage.gaussian_filter(speck, 0.8) * 3
    em = np.clip(m * wear - speck * m * 0.5, 0, 1)
    out = out * (1 - em[..., None]) + EMBLEM[None, None] * (0.92 + 0.08 * _noise(rng, 30)[..., None]) * em[..., None]
    img = Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB").convert("RGBA")
    return img.filter(ImageFilter.UnsharpMask(radius=1.0, percent=40, threshold=2))


def sheet(images, out_png, vanilla_dir=r"E:\PandabornDev\reference\vanilla-banners"):
    vs = sorted(glob.glob(os.path.join(vanilla_dir, "**", "*.png"), recursive=True))
    rows = [[Image.open(v).convert("RGBA") for v in vs]] if vs else []
    rows.append(list(images))
    cell = 200
    cols = max(len(r) for r in rows)
    W = cols * (cell + 8) + 8
    H = len(rows) * (cell + 8) + 8 + 2 * 80
    sh = Image.new("RGB", (W, H), (30, 36, 32))
    y = 8
    for r in rows:
        for k, im in enumerate(r):
            sh.paste(im.convert("RGB").resize((cell, cell), Image.LANCZOS), (8 + k * (cell + 8), y))
        y += cell + 8
    for k, im in enumerate(images):                          # at the size a banner shows from the game camera
        for j, px in enumerate((64, 32)):
            sh.paste(im.convert("RGB").resize((px, px), Image.LANCZOS), (8 + k * (cell + 8) + j * 80, y + 8))
    sh.save(out_png)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(REPO, "mod", "PandabornFactions", "Materials", "Pandaborn",
                                                  "Decals", "Banners"))
    ap.add_argument("--sheet", default=r"E:\PandabornDev\build\icons")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    imgs = []
    for k, (name, (fn, extent)) in enumerate(BANNERS.items()):
        img = paint(name, fn, extent, 11 + k)
        img.save(os.path.join(a.out, name + ".png"), optimize=True)
        imgs.append(img)
        print(name)
    if a.sheet:
        os.makedirs(a.sheet, exist_ok=True)
        sheet(imgs, os.path.join(a.sheet, "banners_sheet.png"))


if __name__ == "__main__":
    main()
