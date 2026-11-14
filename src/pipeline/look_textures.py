"""Generate the Inkpaws building textures and the material spec for the Unity bundle builder.

Every texture is painted here, in code, from noise and simple shapes. Where a vanilla material is a trim sheet (its
models' UVs point at fixed regions: plank strips, log ends, window frames, crate panels, metal plates), the *layout*
of that sheet is read from the vanilla texture in E:\\PandabornDev\\reference\\vanilla-assets as a binary mask (which
pixels belong to which plank / window / frame line) and new content is painted into it. No vanilla pixels are copied.

Outputs (all 1024 x 1024, PNG):
  <unity project>/Assets/PandabornLook/Textures/PBLook_<Set>_<D|N|AO|M|E>.png
  <unity project>/Assets/PandabornLook/look_spec.json      materials for PandabornLookBuilder.cs
  E:\\PandabornDev\\build\\look\\preview\\look_sheet.png       contact sheet (albedo x tint) for eyeballing

Map conventions (match the vanilla EnvironmentURP materials, see docs/tech/look.md):
  D  albedo, sRGB, alpha 255
  N  normal, linear, swizzled like the vanilla maps: R = 255, G = B = y, A = x  (works with UnpackNormal RG or AG)
  AO grey, sRGB
  M  R = G = B = metallic, A = smoothness, sRGB
  E  _LightingMap: colour of the night glow, sRGB, black = no glow

Usage: python -I src/pipeline/look_textures.py [--unity E:\\PandabornDev\\unity\\PandabornLook] [--only Set,...]
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

REF = r"E:\PandabornDev\reference\vanilla-assets"
VT = os.path.join(REF, "textures")
S = 1024

# ------------------------------------------------------------------------------------------------ palette (sRGB 0-255)
INK = np.array([34, 31, 30])
INK_GREY = np.array([66, 63, 60])
PAPER = np.array([238, 228, 204])
PAPER_WARM = np.array([244, 226, 186])
LACQUER = np.array([164, 42, 34])
LACQUER_DARK = np.array([112, 28, 24])
BAMBOO_PALE = np.array([226, 220, 176])       # bleached culm; tints below turn it gold, green or black
TEA = np.array([150, 170, 112])
TILE = np.array([104, 108, 114])
TILE_DARK = np.array([58, 60, 66])
BRONZE = np.array([74, 70, 62])
VERDIGRIS = np.array([96, 132, 112])

# _Color tints per material (linear multipliers applied by the game, baked into vertex colours)
TINT = {
    "BaseWood_White": (1.0, 1.0, 1.0, 1.0),          # pale bamboo
    "BaseWood_Brown": (0.82, 0.80, 0.50, 1.0),       # golden bamboo (most used wood: 320 models)
    "BaseWood_LightBrown": (0.33, 0.31, 0.30, 1.0),  # black "ink" bamboo
    "BaseWood_Yellow": (0.62, 0.78, 0.48, 1.0),      # green bamboo
    "IrregularPlanks_White": (1.0, 1.0, 1.0, 1.0),
    "IrregularPlanks_Brown": (0.80, 0.74, 0.52, 1.0),
    "IrregularPlanks_LightBrown": (0.62, 0.58, 0.48, 1.0),
    "IrregularPlanks_Yellow": (0.70, 0.80, 0.52, 1.0),
    "IrregularPlanks_Mossy": (0.66, 0.76, 0.56, 1.0),
}


# ------------------------------------------------------------------------------------------------ helpers
def rng(seed):
    return np.random.default_rng(seed)


def noise(seed, scale=64.0, beta=2.0, aniso=(1.0, 1.0), shape=(S, S)):
    """Periodic (tileable) power-law noise in [0, 1]. scale: feature size in px; aniso stretches (x, y)."""
    h, w = shape
    white = rng(seed).standard_normal((h, w))
    fy = np.fft.fftfreq(h)[:, None] * aniso[1]
    fx = np.fft.fftfreq(w)[None, :] * aniso[0]
    f = np.sqrt(fx * fx + fy * fy)
    f0 = 1.0 / scale
    filt = 1.0 / np.power(np.maximum(f, f0 * 0.25) / f0, beta / 2.0 + 0.5)
    filt[f < f0 * 0.25] = 0
    out = np.real(np.fft.ifft2(np.fft.fft2(white) * filt))
    out -= out.min()
    return (out / max(out.max(), 1e-9)).astype(np.float32)


def blur(a, r):
    return ndi.gaussian_filter(a, r, mode="wrap")


def lerp(a, b, t):
    t = np.asarray(t)[..., None] if np.ndim(t) == 2 else t
    return a + (b - a) * t


def color_field(base, var=0.08, seed=0, scale=96):
    n = noise(seed, scale) - 0.5
    return np.clip(base[None, None, :] / 255.0 * (1 + var * 2 * n[..., None]), 0, 1)


def normal_from_height(h, strength=4.0):
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * strength
    dr = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * strength
    nx, ny, nz = -dx, dr, np.ones_like(h)   # rows run down the image, v runs up
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny = nx / ln, ny / ln
    out = np.zeros((h.shape[0], h.shape[1], 4), np.uint8)
    out[..., 0] = 255
    out[..., 1] = np.clip((ny * 0.5 + 0.5) * 255, 0, 255)
    out[..., 2] = out[..., 1]
    out[..., 3] = np.clip((nx * 0.5 + 0.5) * 255, 0, 255)
    return out


def ao_from_height(h, radius=6, strength=2.5, extra=None):
    cav = np.clip(blur(h, radius) - h, 0, None)
    ao = np.clip(1.0 - cav * strength, 0.25, 1.0)
    if extra is not None:
        ao = ao * extra
    return ao


def vanilla(name, mode="RGBA"):
    return np.asarray(Image.open(os.path.join(VT, name + ".png")).convert(mode)).astype(np.float32) / 255.0


def save_rgb(path, a):
    Image.fromarray(np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8), "RGB").save(path)


def save_gray(path, a):
    Image.fromarray(np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8), "L").convert("RGB").save(path)


def save_m(path, metal, smooth):
    m = np.zeros((S, S, 4), np.uint8)
    mv = np.clip(np.broadcast_to(metal, (S, S)) * 255 + 0.5, 0, 255).astype(np.uint8)
    m[..., 0] = m[..., 1] = m[..., 2] = mv
    m[..., 3] = np.clip(np.broadcast_to(smooth, (S, S)) * 255 + 0.5, 0, 255).astype(np.uint8)
    Image.fromarray(m, "RGBA").save(path)


class Set:
    """One texture set: albedo, height (for N and AO), metal/smooth, optional emission."""

    def __init__(self, name):
        self.name = name
        self.d = np.ones((S, S, 3), np.float32) * 0.5
        self.h = np.zeros((S, S), np.float32)
        self.ao_extra = None
        self.metal = 0.0
        self.smooth = 0.25
        self.e = None
        self.nstrength = 4.0
        self.ao_radius = 6
        self.ao_strength = 2.5

    def write(self, outdir):
        p = os.path.join(outdir, "PBLook_" + self.name)
        save_rgb(p + "_D.png", self.d)
        Image.fromarray(normal_from_height(self.h, self.nstrength), "RGBA").save(p + "_N.png")
        save_gray(p + "_AO.png", ao_from_height(self.h, self.ao_radius, self.ao_strength, self.ao_extra))
        save_m(p + "_M.png", self.metal, self.smooth)
        maps = {"_MainTex": p + "_D.png", "_BumpMap": p + "_N.png", "_AmbientOcclusion": p + "_AO.png",
                "_MetallicGlossMap": p + "_M.png"}
        if self.e is not None:
            save_rgb(p + "_E.png", self.e)
            maps["_LightingMap"] = p + "_E.png"
        return maps


# ------------------------------------------------------------------------------------------------ painters
def paint_culm(st, mask, x0, y0, x1, y1, seed, horizontal=False, node_gap=(110, 190)):
    """A bamboo culm / split slat filling the bbox, clipped to mask (bool array, full size)."""
    r = rng(seed)
    w, h = x1 - x0, y1 - y0
    if horizontal:
        w, h = h, w
    t = (np.arange(w) + 0.5) / max(w, 1)
    across = np.sin(np.pi * t)                                # rounded profile
    prof_h = np.broadcast_to(across[None, :], (h, w)).copy()
    shade = 0.80 + 0.20 * np.sqrt(np.clip(across, 0, 1))
    hue = r.uniform(-0.04, 0.04, 3)
    col = np.broadcast_to(BAMBOO_PALE / 255.0 * (1 + hue), (h, w, 3)).copy() * shade[None, :, None]
    # nodes
    yy = np.arange(h)[:, None].astype(np.float32)
    pos = r.uniform(0, node_gap[0])
    nodes = []
    while pos < h:
        nodes.append(pos)
        pos += r.uniform(*node_gap)
    ridge = np.zeros((h, 1), np.float32)
    band = np.zeros((h, 1), np.float32)
    for p in nodes:
        ridge += np.exp(-((yy - p) ** 2) / (2 * 2.2 ** 2))
        band += np.exp(-((yy - p) ** 2) / (2 * 9.0 ** 2))
    line = np.exp(-((yy - np.array(nodes)[None, :] - 3.5) ** 2) / (2 * 1.1 ** 2)).sum(1, keepdims=True) if nodes else 0 * yy
    col = col * (1 - 0.18 * band[..., None]) + np.array([0.02, 0.03, -0.02]) * band[..., None]
    col = col * (1 - 0.45 * np.clip(line, 0, 1)[..., None])
    fib = noise(seed + 1, 6, 1.6, aniso=(1.0, 0.06), shape=(max(h, 8), max(w, 8)))[:h, :w]
    col = col * (0.93 + 0.12 * fib[..., None])
    hh = 0.55 * prof_h + 0.35 * ridge - 0.25 * np.clip(line, 0, 1) + 0.05 * fib
    if horizontal:
        col = col.transpose(1, 0, 2)
        hh = hh.T
    m = mask[y0:y1, x0:x1]
    st.d[y0:y1, x0:x1][m] = col[m]
    st.h[y0:y1, x0:x1][m] = hh[m] + 0.3


def paint_cross_section(st, cx, cy, rad, seed, broken=False):
    r = rng(seed)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    ang = np.arctan2(yy - cy, xx - cx)
    rout = rad * (1 + (0.12 * np.sin(ang * 7 + r.uniform(0, 6)) if broken else 0.02 * np.sin(ang * 3)))
    rin = rad * 0.62
    wall = (d < rout) & (d >= rin)
    hollow = d < rin
    ring_t = np.clip((d - rin) / np.maximum(rout - rin, 1), 0, 1)
    wc = BAMBOO_PALE / 255.0 * (0.95 - 0.25 * ring_t[..., None]) * (0.92 + 0.08 * np.cos(d * 1.3)[..., None])
    st.d[wall] = wc[wall]
    st.d[hollow] = (INK / 255.0 * 1.6)[None, :] * (0.7 + 0.3 * (d[hollow] / rin))[:, None]
    st.h[wall] = 0.6 + 0.05 * np.cos(d[wall] * 1.3)
    st.h[hollow] = 0.05 + 0.2 * (d[hollow] / rin)


def components(mask, min_px=400):
    lab, n = ndi.label(mask)
    out = []
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        if sl is None:
            continue
        m = lab == i
        if m.sum() < min_px:
            continue
        out.append((sl[1].start, sl[0].start, sl[1].stop, sl[0].stop, m))
    return out


# ------------------------------------------------------------------------------------------------ sets
def make_bamboo():
    """Replaces the BaseWood trim sheet: plank strips become split bamboo slats, the long-grain block becomes a row
    of thin culms, log ends become hollow cross-sections, the plain corner a pale lime wash."""
    st = Set("Bamboo")
    v = vanilla("BaseWood_1K_D_White", "RGB")
    whiteish = v.min(2) > 0.80
    wood = ndi.binary_opening(~whiteish, iterations=2)
    wood = ndi.binary_fill_holes(wood)
    # background: pale wash
    st.d[:] = color_field(np.array([236, 232, 218]), 0.05, 11, 48)
    st.h[:] = 0.1 + 0.05 * noise(12, 24)
    k = 0
    for x0, y0, x1, y1, m in components(wood):
        w, h = x1 - x0, y1 - y0
        k += 1
        if w > 300 and h > 300:                       # long-grain block: packed thin culms
            x = x0
            j = 0
            while x < x1:
                cw = int(rng(500 + j).integers(22, 40))
                sub = np.zeros_like(m)
                sub[:, x:min(x + cw, x1)] = True
                paint_culm(st, m & sub, x, y0, min(x + cw, x1), y1, 600 + j, node_gap=(70, 150))
                x += cw
                j += 1
        elif h > 1.8 * w or w > 1.8 * h:               # plank strip -> slat
            paint_culm(st, m, x0, y0, x1, y1, 100 + k, horizontal=w > h)
        else:                                          # disc -> bamboo end
            paint_cross_section(st, (x0 + x1) / 2, (y0 + y1) / 2, min(w, h) / 2 * 0.95, 300 + k,
                                broken=(k % 3 == 0))
    st.smooth = 0.32 + 0.12 * (st.h > 0.3)
    st.metal = 0.03
    return st


def make_weave():
    """Replaces IrregularPlanks: woven bamboo matting (twill), seamless."""
    st = Set("Weave")
    yy, xx = np.mgrid[0:S, 0:S]
    strip = 32
    u = (xx + yy) // strip          # diagonal strands one way
    vv = (xx - yy) % S // strip     # and the other
    over = ((u + (vv // 2)) % 2 == 0)
    tu = ((xx + yy) % strip) / strip
    tv = (((xx - yy) % S) % strip) / strip
    prof_u = np.sin(np.pi * tu)
    prof_v = np.sin(np.pi * tv)
    hh = np.where(over, 0.6 + 0.3 * prof_u, 0.4 + 0.3 * prof_v).astype(np.float32)
    fib_a = noise(21, 5, 1.5, aniso=(0.08, 1.0))
    fib = np.where(over, noise(22, 5, 1.5, aniso=(1.0, 0.08)), fib_a)
    base = np.where(over[..., None], BAMBOO_PALE / 255.0, BAMBOO_PALE / 255.0 * 0.86)
    per = noise(23, 40)
    d = base * (0.88 + 0.12 * np.where(over, prof_u, prof_v)[..., None]) * (0.92 + 0.1 * fib[..., None])
    d *= (0.94 + 0.1 * per[..., None])
    edge = np.minimum(np.where(over, prof_u, prof_v), 1)
    d *= (0.6 + 0.4 * np.clip(edge * 3, 0, 1))[..., None]
    st.d = d.astype(np.float32)
    st.h = hh + 0.04 * fib
    st.smooth = 0.28
    st.metal = 0.02
    st.ao_radius, st.ao_strength = 4, 3.0
    return st


def make_tiles():
    """Replaces ThatchedRoof: grey clay pan-and-cover tiles in four courses (same course height and lower-edge rows
    as the vanilla thatch: edges at y = 200 + 256k, strands hang down the image)."""
    st = Set("RoofTiles")
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    course = 256.0
    edge0 = 200.0
    yc = (yy - edge0) % course            # 0 at the lower edge of the course above, grows downwards
    t_in = (course - yc) / course         # 1 just above an edge, 0 at the top of a course
    col_w = 64.0
    cx = (xx % col_w) / col_w             # within a pan+cover pair
    cover = np.abs(cx - 0.5) < 0.22
    tc = np.clip((cx - 0.28) / 0.44, 0, 1)
    cover_h = np.sqrt(np.clip(np.sin(np.pi * tc), 0, 1)) * 0.55
    pan_t = np.where(cx < 0.5, cx / 0.28, (1 - cx) / 0.28)
    pan_h = 0.15 * (1 - np.clip(pan_t, 0, 1)) ** 2
    hh = np.where(cover, 0.35 + cover_h, 0.1 + pan_h)
    # individual tile lengths inside a course: two overlapping tiles per course
    seg = (yc % (course / 2)) / (course / 2)
    hh = hh + 0.10 * seg                  # each tile rises toward its lower end
    # overlap shadow just below each course edge (yc small means just below the edge)
    under = np.exp(-yc / 18.0)
    hh = hh - 0.35 * under
    hh = hh + 0.04 * noise(31, 10)
    pair = (xx // col_w).astype(int)
    crs = ((yy - edge0) // course).astype(int)
    var = (np.sin(pair * 12.9898 + crs * 78.233) * 43758.5453) % 1.0
    base = TILE / 255.0 * (0.88 + 0.22 * var[..., None])
    base = np.where(cover[..., None], base * (0.85 + 0.25 * cover_h[..., None] / 0.55), base * 0.82)
    base = base * (1 - 0.55 * under[..., None])
    grime = noise(32, 60)
    base = base * (0.9 + 0.15 * grime[..., None])
    lichen = (noise(33, 30) > 0.78) & ~cover
    base[lichen] = base[lichen] * 0.6 + TEA / 255.0 * 0.4
    # round end caps of the cover tiles at each course edge (seen as a darker rim)
    cap = cover & (yc < 10)
    base[cap] = TILE_DARK / 255.0
    st.d = base.astype(np.float32)
    st.h = hh.astype(np.float32)
    st.smooth = 0.22
    st.metal = 0.0
    st.nstrength = 5.0
    return st


def make_plaster(name="Plaster", base=PAPER, seed=40):
    st = Set(name)
    n1, n2, n3 = noise(seed, 120), noise(seed + 1, 24), noise(seed + 2, 6)
    st.d = color_field(base, 0.05, seed + 3, 140) * (0.94 + 0.06 * n2[..., None]) * (0.97 + 0.04 * n3[..., None])
    pits = noise(seed + 4, 3, 1.0) > 0.86
    st.d[pits] *= 0.9
    st.h = 0.3 * n1 + 0.15 * n2 + 0.05 * n3 - 0.1 * pits
    st.smooth = 0.2
    st.nstrength = 3.0
    return st


def make_plastered_wood():
    """Replaces PlasteredWood: lime plaster with thin dark bamboo laths showing through in horizontal strokes."""
    st = make_plaster("PlasterLath", PAPER, 50)
    r = rng(51)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    lath = np.zeros((S, S), np.float32)
    for _ in range(140):
        cy, cx = r.uniform(0, S), r.uniform(0, S)
        ln, th = r.uniform(40, 140), r.uniform(2.0, 4.5)
        dx = (xx - cx + S / 2) % S - S / 2
        dy = (yy - cy + S / 2) % S - S / 2
        taper = np.clip(1 - (2 * dx / ln) ** 2, 0, 1)
        lath = np.maximum(lath, np.exp(-(dy ** 2) / (2 * (th * taper + 0.01) ** 2)) * (np.abs(dx) < ln / 2))
    st.d = st.d * (1 - lath[..., None]) + (INK_GREY / 255.0) * lath[..., None]
    st.h = st.h + 0.25 * lath
    return st


def make_shoji():
    """Replaces Paper: cream rice paper with a dark lacquered lattice where the vanilla sheet has frame lines."""
    st = Set("Shoji")
    v = vanilla("Paper_D.Folktails", "RGB")
    lum = v.mean(2)
    lines = (blur(lum, 6) - lum) > 0.05
    lines = ndi.binary_closing(ndi.binary_opening(lines, iterations=1), iterations=2)
    lines = ndi.binary_dilation(lines, iterations=2)
    fib = noise(61, 3, 1.2)
    st.d = color_field(PAPER, 0.03, 62, 200) * (0.95 + 0.07 * fib[..., None])
    soft = blur(lines.astype(np.float32), 1.2)
    st.d = st.d * (1 - soft[..., None]) + (INK / 255.0 * 1.3) * soft[..., None]
    st.h = 0.2 + 0.03 * fib + 0.4 * soft
    st.smooth = np.where(lines, 0.55, 0.12)
    return st


def make_iron():
    """Replaces BaseMetal: blackened bronze with verdigris in the seams; plate seams and rivets follow the vanilla
    sheet's layout (read from its normal map)."""
    st = Set("Bronze")
    vn = vanilla("BaseMetal_N")
    dev = np.sqrt((vn[..., 3] - 0.5) ** 2 + (vn[..., 1] - 0.5) ** 2)
    seams = blur(dev, 1.0) > 0.12
    seams = ndi.binary_opening(seams, iterations=1)
    sf = blur(seams.astype(np.float32), 1.5)
    n1, n2 = noise(71, 80), noise(72, 8)
    st.d = color_field(BRONZE, 0.10, 73, 90) * (0.9 + 0.15 * n2[..., None])
    patina = np.clip((blur(sf, 6) * 1.5 + 0.6 * n1 - 0.55) * 2, 0, 1)
    st.d = st.d * (1 - 0.6 * patina[..., None]) + VERDIGRIS / 255.0 * 0.6 * patina[..., None]
    st.d = st.d * (1 - 0.5 * sf[..., None])
    st.h = 0.5 - 0.35 * sf + 0.05 * n2
    st.metal = 0.55 - 0.4 * patina
    st.smooth = 0.42 - 0.25 * patina
    return st


def make_lacquer():
    """Replaces PaintedMetal: the vanilla yellow/black hazard stripes become lacquer red / ink black, worn at edges."""
    st = Set("Lacquer")
    v = vanilla("PaintedMetal_D.Folktails", "RGB")
    yellow = (v[..., 0] > 0.55) & (v[..., 1] > 0.45) & (v[..., 2] < 0.35)
    yellow = ndi.binary_closing(ndi.binary_opening(yellow, iterations=2), iterations=3)
    ys = blur(yellow.astype(np.float32), 1.5)
    wear = noise(81, 18) * noise(82, 90)
    chips = (wear > 0.55) & yellow
    base = (LACQUER / 255.0) * ys[..., None] + (INK / 255.0) * (1 - ys[..., None])
    base = base * (0.92 + 0.12 * noise(83, 50)[..., None])
    base[chips] = BRONZE / 255.0
    st.d = base.astype(np.float32)
    st.h = 0.5 + 0.08 * ys - 0.15 * chips + 0.02 * noise(84, 4)
    st.smooth = np.where(chips, 0.3, 0.62)
    st.metal = np.where(chips, 0.5, 0.0)
    return st


def make_windows():
    """Replaces WindowsAtlas: same window shapes; frames become lacquered red / ink wood, glass becomes paper with
    a shoji lattice, and the night glow (_LightingMap) is a warm paper light broken by the lattice."""
    st = Set("Windows")
    vd = vanilla("WindowsAtlas_D.Folktails", "RGB")
    ve = vanilla("WindowsAtlas_E.Folktails", "RGB").mean(2)
    glass = ve > 0.25
    glow_soft = np.clip(ve, 0, 1)
    # the sheet's wall colour is one flat tan; everything else that is not glass is frame, except the big dark
    # square (a doorway interior), which stays dark
    wall_col = np.array([140, 116, 84]) / 255.0
    wall = np.sqrt(((vd - wall_col) ** 2).sum(2)) < 0.09
    rest = ~wall & ~glass
    lab, n = ndi.label(rest)
    sizes = ndi.sum(rest, lab, range(1, n + 1))
    interior = np.isin(lab, 1 + np.nonzero(sizes > 120000)[0])
    frame = ndi.binary_opening(rest & ~interior, iterations=1)
    yy, xx = np.mgrid[0:S, 0:S]
    lattice = ((xx % 22) < 3) | ((yy % 22) < 3)
    st.d = color_field(PAPER, 0.04, 91, 120) * 0.92
    edge = blur(frame.astype(np.float32), 2.0)       # frames darken toward their edges
    st.d[frame] = (LACQUER / 255.0)[None, :] * (0.55 + 0.45 * edge[frame] * (0.85 + 0.3 * noise(94, 30)[frame]))[:, None]
    st.d[interior] = (INK / 255.0)[None, :] * (0.8 + 0.4 * noise(92, 120)[interior])[:, None]
    gl = glass & ~lattice
    st.d[gl] = PAPER_WARM / 255.0
    st.d[glass & lattice] = INK / 255.0 * 1.4
    st.h = 0.3 + 0.3 * edge * frame - 0.1 * gl + 0.1 * (glass & lattice) - 0.2 * interior + 0.03 * noise(93, 6)
    st.smooth = np.where(frame, 0.55, 0.15)
    e = np.zeros((S, S, 3), np.float32)
    e[:] = (np.array([255, 206, 140]) / 255.0)[None, None, :]
    e *= (glow_soft * (~lattice | ~glass))[..., None]
    st.e = e
    return st


def make_details():
    """Replaces Details: the banner becomes lacquer red with an ink disc and a pale bamboo-leaf mark; the sack,
    rope and good labels are repainted; crate and plank regions keep their seams (read from the vanilla sheet)
    and are filled with bamboo."""
    st = Set("Details")
    v = vanilla("Details_D.Folktails", "RGB")
    lum = v.mean(2)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    # crates and planks (lower half): seams -> slats
    seams = (blur(lum, 4) - lum) > 0.06
    seams = ndi.binary_dilation(ndi.binary_opening(seams), iterations=1)
    st.d[:] = BAMBOO_PALE / 255.0 * 0.85
    st.h[:] = 0.4
    lower = np.zeros((S, S), bool)
    lower[512:, :] = True
    slat = lower & ~seams
    for k, (x0, y0, x1, y1, m) in enumerate(components(slat, 200)):
        paint_culm(st, m, x0, y0, x1, y1, 700 + k, horizontal=(x1 - x0) > (y1 - y0), node_gap=(60, 120))
    st.d[lower & seams] = INK_GREY / 255.0
    st.h[lower & seams] = 0.1
    # metal bands on the plank panel -> rope lashing
    band = lower & (v[..., 2] > 0.55) & (np.abs(v[..., 0] - v[..., 2]) < 0.12)
    band = ndi.binary_opening(band, iterations=2)
    rope = 0.75 + 0.25 * np.sin((xx + yy) * 0.6)
    st.d[band] = (np.array([196, 170, 120]) / 255.0)[None, :] * rope[band][:, None]
    st.h[band] = 0.6 + 0.2 * rope[band]
    # banner (0..512, 0..512)
    by, bx = slice(0, 512), slice(0, 512)
    cloth = 0.9 + 0.1 * noise(94, 20, aniso=(1, 0.3))[by, bx]
    st.d[by, bx] = (LACQUER / 255.0)[None, None, :] * cloth[..., None]
    st.h[by, bx] = 0.3 + 0.1 * cloth
    cxb, cyb = 256, 250
    dd = np.sqrt((xx[by, bx] - cxb) ** 2 + (yy[by, bx] - cyb) ** 2)
    disc = dd < 150
    st.d[by, bx][disc] = INK / 255.0
    # leaf: two curved blades
    lx, ly = xx[by, bx] - cxb, yy[by, bx] - cyb
    for ang, sc in ((0.6, 1.0), (-0.5, 0.85), (1.6, 0.7)):
        ca, sa = np.cos(ang), np.sin(ang)
        u = (lx * ca + ly * sa) / (110 * sc)
        w = (-lx * sa + ly * ca) / (110 * sc)
        leaf = (u > -0.9) & (u < 0.9) & (np.abs(w - 0.15 * u * u) < 0.22 * (1 - u * u))
        st.d[by, bx][leaf & disc] = PAPER / 255.0
    # sack (512..768, 0..512)
    sy, sx = slice(0, 512), slice(512, 768)
    weave = 0.85 + 0.15 * (np.sin(xx[sy, sx] * 1.4) * np.sin(yy[sy, sx] * 1.4))
    st.d[sy, sx] = color_field(np.array([214, 196, 160]), 0.08, 95, 40)[sy, sx] * weave[..., None]
    st.h[sy, sx] = 0.4 + 0.25 * noise(96, 40)[sy, sx] + 0.05 * weave
    # rope column (768..832)
    ry, rx = slice(0, 512), slice(768, 832)
    twist = 0.7 + 0.3 * np.sin((xx[ry, rx] * 0.4 + yy[ry, rx]) * 0.35)
    st.d[ry, rx] = (np.array([190, 160, 110]) / 255.0)[None, None, :] * twist[..., None]
    st.h[ry, rx] = 0.4 + 0.3 * twist
    # labels (832..1024): three colour bands with simple marks
    for (y0, y1), colr, mark in (((0, 170), LACQUER, "logs"), ((170, 340), TEA, "leaf"), ((340, 512), INK_GREY, "dots")):
        ly0, ly1 = y0, y1
        st.d[ly0:ly1, 832:1024] = colr / 255.0
        st.h[ly0:ly1, 832:1024] = 0.45
        cx0, cy0 = 928, (ly0 + ly1) / 2
        X, Y = xx[ly0:ly1, 832:1024] - cx0, yy[ly0:ly1, 832:1024] - cy0
        if mark == "logs":
            m = (np.abs(Y) < 40) & (np.abs(X) < 55) & ((np.abs(Y) % 28) < 22)
        elif mark == "leaf":
            m = (np.abs(X) < 55) & (np.abs(Y + 0.004 * X * X) < 18 * np.clip(1 - (X / 55) ** 2, 0, 1) + 1)
        else:
            m = np.zeros_like(X, bool)
            for ox, oy in ((-25, -15), (20, -20), (0, 18), (-30, 25), (30, 20)):
                m |= (X - ox) ** 2 + (Y - oy) ** 2 < 15 ** 2
        st.d[ly0:ly1, 832:1024][m] = PAPER / 255.0
        st.h[ly0:ly1, 832:1024][m] = 0.55
    st.smooth = 0.25
    return st


def make_sand():
    st = make_plaster("Gravel", np.array([170, 168, 160]), 100)
    pebbles = noise(101, 5, 1.0) > 0.7
    st.d[pebbles] *= 1.12
    st.h += 0.2 * pebbles
    return st


def make_moss():
    st = make_plaster("Moss", TEA, 110)
    st.d *= (0.8 + 0.3 * noise(111, 4)[..., None])
    st.smooth = 0.1
    return st


SETS = {
    "Bamboo": make_bamboo, "Weave": make_weave, "RoofTiles": make_tiles, "Plaster": make_plaster,
    "PlasterLath": make_plastered_wood, "Shoji": make_shoji, "Bronze": make_iron, "Lacquer": make_lacquer,
    "Windows": make_windows, "Details": make_details, "Gravel": make_sand, "Moss": make_moss,
}

# vanilla material -> (texture set, tint key or None)
MATERIALS = {
    "BaseWood_White.Folktails": ("Bamboo", "BaseWood_White"),
    "BaseWood_Brown.Folktails": ("Bamboo", "BaseWood_Brown"),
    "BaseWood_LightBrown.Folktails": ("Bamboo", "BaseWood_LightBrown"),
    "BaseWood_Yellow.Folktails": ("Bamboo", "BaseWood_Yellow"),
    "IrregularPlanks_White.Folktails": ("Weave", "IrregularPlanks_White"),
    "IrregularPlanks_Brown.Folktails": ("Weave", "IrregularPlanks_Brown"),
    "IrregularPlanks_LightBrown.Folktails": ("Weave", "IrregularPlanks_LightBrown"),
    "IrregularPlanks_Yellow.Folktails": ("Weave", "IrregularPlanks_Yellow"),
    "IrregularPlanks_Mossy.Folktails": ("Weave", "IrregularPlanks_Mossy"),
    "ThatchedRoof.Folktails": ("RoofTiles", None),
    "Plaster_White.Folktails": ("Plaster", None),
    "PlasteredWood_White.Folktails": ("PlasterLath", None),
    "Paper.Folktails": ("Shoji", None),
    "BaseMetal.Folktails": ("Bronze", None),
    "PaintedMetal.Folktails": ("Lacquer", None),
    "WindowsAtlas.Folktails": ("Windows", None),
    "Details.Folktails": ("Details", None),
    "Sand.Folktails": ("Gravel", None),
    "Moss.Folktails": ("Moss", None),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unity", default=r"E:\PandabornDev\unity\PandabornLook")
    ap.add_argument("--only", default="")
    ap.add_argument("--preview", default=r"E:\PandabornDev\build\look\preview")
    a = ap.parse_args()
    texdir = os.path.join(a.unity, "Assets", "PandabornLook", "Textures")
    os.makedirs(texdir, exist_ok=True)
    os.makedirs(a.preview, exist_ok=True)
    only = set(filter(None, a.only.split(",")))
    vanilla_mats = json.load(open(os.path.join(REF, "materials.json"), encoding="utf-8"))["materials"]
    by_name = {m["name"]: m for m in vanilla_mats.values()}
    maps = {}
    for name, fn in SETS.items():
        if only and name not in only:
            p = os.path.join(texdir, "PBLook_" + name)
            maps[name] = {k: p + suf for k, suf in (("_MainTex", "_D.png"), ("_BumpMap", "_N.png"),
                                                  ("_AmbientOcclusion", "_AO.png"), ("_MetallicGlossMap", "_M.png"))}
            if os.path.exists(p + "_E.png"):
                maps[name]["_LightingMap"] = p + "_E.png"
            continue
        print("painting", name, flush=True)
        maps[name] = fn().write(texdir)
    project = a.unity.replace("\\", "/").rstrip("/") + "/"
    spec = {"materials": [], "textures": []}
    seen = set()
    for mat, (setname, tint) in MATERIALS.items():
        vm = by_name[mat]
        floats = [{"key": k, "value": v} for k, v in vm["floats"].items()]
        colors = {k: v for k, v in vm["colors"].items()}
        colors["_Color"] = list(TINT[tint]) if tint else [1.0, 1.0, 1.0, 1.0]
        tex = []
        for slot, path in maps[setname].items():
            rel = path.replace("\\", "/").replace(project, "")
            tex.append({"key": slot, "value": rel})
            if rel not in seen:
                seen.add(rel)
                spec["textures"].append({"path": rel, "linear": slot == "_BumpMap", "readable": True})
        spec["materials"].append({
            "name": mat, "set": setname, "shader": "Assets/TimberbornShaders/EnvironmentURP.shadergraph",
            "textures": tex, "floats": floats,
            "colors": [{"key": k, "value": v} for k, v in colors.items()]})
    with open(os.path.join(a.unity, "Assets", "PandabornLook", "look_spec.json"), "w", encoding="utf-8") as fh:
        json.dump(spec, fh, indent=1)
    # contact sheet: each material's albedo x tint, plus the windows glow
    tiles = []
    for mat, (setname, tint) in MATERIALS.items():
        im = Image.open(maps[setname]["_MainTex"]).convert("RGB").resize((256, 256))
        if tint:
            arr = np.asarray(im).astype(np.float32) * np.array(TINT[tint][:3])
            im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        tiles.append(im)
    tiles.append(Image.open(maps["Windows"]["_LightingMap"]).convert("RGB").resize((256, 256)))
    cols = 5
    sheet = Image.new("RGB", (cols * 256, ((len(tiles) + cols - 1) // cols) * 256), (40, 40, 40))
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % cols) * 256, (i // cols) * 256))
    sheet.save(os.path.join(a.preview, "look_sheet.png"))
    print("spec:", len(spec["materials"]), "materials,", len(spec["textures"]), "textures")


if __name__ == "__main__":
    sys.exit(main())
