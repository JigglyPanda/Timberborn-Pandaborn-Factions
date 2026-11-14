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
# Art direction (docs/tech/look.md): rural Sichuan farmsteads of the Chengdu plain. Dark timber frames, white lime
# plaster, grey clay tile, bamboo (green fresh, straw-gold cured, grey weathered), woven bamboo, rammed earth and river
# stone. Red is an accent only (lanterns, small trim, festival cloth). No text on any texture. Nothing Japanese-coded.
INK = np.array([34, 31, 30])
INK_GREY = np.array([66, 63, 60])
TIMBER = np.array([72, 54, 40])               # dark, oiled and smoke-darkened fir
LIME = np.array([236, 234, 226])              # white lime plaster
PAPER = np.array([232, 222, 198])             # window paper (unbleached)
PAPER_WARM = np.array([240, 220, 180])
LACQUER = np.array([150, 44, 36])             # accents only
INDIGO = np.array([52, 66, 96])               # indigo-dyed cloth
BAMBOO_PALE = np.array([226, 220, 176])       # pale culm; tints below make it straw-gold, green or weathered grey
TEA = np.array([150, 170, 112])
TILE = np.array([104, 108, 114])
TILE_DARK = np.array([58, 60, 66])
IRON = np.array([60, 58, 56])
RUST = np.array([120, 82, 56])
EARTH = np.array([168, 140, 104])             # rammed earth
STONE = np.array([150, 148, 140])             # river stone

# _Color tints per material (linear multipliers applied by the game, baked into vertex colours)
TINT = {
    "BaseWood_Brown": (1.0, 1.0, 1.0, 1.0),          # dark timber frame (own texture; most used wood: 320 models)
    "BaseWood_White": (0.86, 0.85, 0.80, 1.0),       # weathered grey bamboo
    "BaseWood_LightBrown": (0.88, 0.80, 0.62, 1.0),  # cured straw-gold bamboo
    "BaseWood_Yellow": (0.66, 0.80, 0.50, 1.0),      # fresh green bamboo
    "IrregularPlanks_White": (1.0, 1.0, 1.0, 1.0),     # woven panels: tones are baked in (straw, grey-green)
    "IrregularPlanks_Brown": (1.0, 1.0, 1.0, 1.0),     # coarse, smoke-darkened weave (own texture)
    "IrregularPlanks_LightBrown": (0.96, 0.92, 0.84, 1.0),
    "IrregularPlanks_Yellow": (0.86, 0.95, 0.78, 1.0),
    "IrregularPlanks_Mossy": (1.0, 1.0, 1.0, 1.0),
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
        self.n_baked = None      # RGBA uint8, already in the game's swizzled layout (Blender bake)
        self.ao_baked = None     # float 0..1 (Blender bake)

    def write(self, outdir):
        p = os.path.join(outdir, "PBLook_" + self.name)
        save_rgb(p + "_D.png", self.d)
        n = self.n_baked if self.n_baked is not None else normal_from_height(self.h, self.nstrength)
        Image.fromarray(n, "RGBA").save(p + "_N.png")
        ao = self.ao_baked if self.ao_baked is not None else ao_from_height(self.h, self.ao_radius, self.ao_strength,
                                                                             self.ao_extra)
        save_gray(p + "_AO.png", ao)
        save_m(p + "_M.png", self.metal, self.smooth)
        maps = {"_MainTex": p + "_D.png", "_BumpMap": p + "_N.png", "_AmbientOcclusion": p + "_AO.png",
                "_MetallicGlossMap": p + "_M.png"}
        if self.e is not None:
            save_rgb(p + "_E.png", self.e)
            maps["_LightingMap"] = p + "_E.png"
        return maps


# ------------------------------------------------------------------------------------------------ Blender bakes
BAKE = "E:/PandabornDev/build/look/bake"
LIGHT = np.array([-0.45, 0.55, 0.70]) / np.linalg.norm([-0.45, 0.55, 0.70])   # painted light: upper left


def from_bake(name, smooth, metal=0.02, paint=0.55, ao_paint=0.5, crisp=0.8, light=None):
    """A set baked by src/pipeline/bake_sheets.py (Cycles passes of modelled geometry). The albedo gets a painted
    light (soft top-left key + AO), the way the vanilla sheets are hand-painted, so models do not look flatter than
    Folktails ones under the game's own lighting."""
    d = os.path.join(BAKE, name)
    diff = np.load(os.path.join(d, "diffcol.npy"))
    nrm = np.load(os.path.join(d, "normal.npy"))
    ao = np.clip(np.load(os.path.join(d, "ao.npy")).mean(2), 0, 1)
    ln = np.linalg.norm(nrm, axis=2, keepdims=True)
    nrm = nrm / np.maximum(ln, 1e-6)
    lt = LIGHT if light is None else np.asarray(light) / np.linalg.norm(light)
    lam = np.clip((nrm * lt).sum(2), 0, 1)
    flat = lt[2]
    shade = (1 - paint + paint * lam / flat) * (1 - ao_paint + ao_paint * ao ** 1.3)
    lin = np.clip(diff * shade[..., None], 0, 1)
    st = Set(name)
    d8 = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1 / 2.4) - 0.055).astype(np.float32)
    # painterly crispness: local contrast boost (unsharp mask), as the hand-painted vanilla sheets have
    soft = ndi.gaussian_filter(d8, (3, 3, 0), mode="wrap")
    st.d = np.clip(d8 + crisp * (d8 - soft), 0, 1).astype(np.float32)
    n8 = np.zeros((S, S, 4), np.uint8)
    n8[..., 0] = 255
    n8[..., 1] = np.clip((nrm[..., 1] * 0.5 + 0.5) * 255, 0, 255)
    n8[..., 2] = n8[..., 1]
    n8[..., 3] = np.clip((nrm[..., 0] * 0.5 + 0.5) * 255, 0, 255)
    st.n_baked = n8
    st.ao_baked = ao
    st.smooth = smooth
    st.metal = metal
    return st


def baked_or(name, fallback, smooth, keep_emission=False, crisp=None):
    def make():
        if os.path.exists(os.path.join(BAKE, name, "diffcol.npy")):
            print("  (from Blender bake)", flush=True)
            st = from_bake(name, smooth, crisp=crisp if crisp is not None else (1.0 if name == "Timber" else 0.8),
                           paint=0.85 if name == "RoofTiles" else 0.55,
                           light=(-0.75, 0.25, 0.6) if name == "RoofTiles" else None)   # grazing: rounds the covers
            if keep_emission:
                st.e = fallback().e
            return st
        return fallback()
    return make


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


def paint_board(st, mask, x0, y0, x1, y1, seed, horizontal=False):
    """A dark timber board: wavy grain along its length, darker edges, the odd knot."""
    r = rng(seed)
    w, h = x1 - x0, y1 - y0
    if horizontal:
        w, h = h, w
    ww, hh_ = max(w, 8), max(h, 8)
    warp = (noise(seed + 2, 40, 2.0, shape=(hh_, ww)) - 0.5) * 18
    xx = np.arange(ww)[None, :] + warp
    grain = 0.5 + 0.5 * np.sin(xx * r.uniform(0.35, 0.6) + 3 * noise(seed + 3, 12, aniso=(1, 0.1), shape=(hh_, ww)))
    grain = grain[:h, :w]
    fib = noise(seed + 1, 4, 1.4, aniso=(1.0, 0.05), shape=(hh_, ww))[:h, :w]
    t = (np.arange(w) + 0.5) / max(w, 1)
    edge = np.clip(np.minimum(t, 1 - t) * 8, 0, 1)
    tone = r.uniform(0.85, 1.12)
    col = (TIMBER / 255.0)[None, None, :] * tone * (0.82 + 0.25 * grain[..., None]) * (0.92 + 0.12 * fib[..., None])
    col = col * (0.7 + 0.3 * edge[None, :, None])
    hgt = 0.45 + 0.08 * grain + 0.04 * fib + 0.15 * edge[None, :]
    # a knot or two
    for _ in range(r.integers(0, 3)):
        ky, kx = r.uniform(0, h), r.uniform(0.2, 0.8) * w
        yy, xs = np.mgrid[0:h, 0:w]
        d = np.sqrt(((yy - ky) / 2.2) ** 2 + (xs - kx) ** 2)
        k = np.exp(-(d / 5.0) ** 2)
        col = col * (1 - 0.5 * k[..., None])
        hgt = hgt - 0.1 * k
    if horizontal:
        col = col.transpose(1, 0, 2)
        hgt = hgt.T
    m = mask[y0:y1, x0:x1]
    st.d[y0:y1, x0:x1][m] = col[m]
    st.h[y0:y1, x0:x1][m] = hgt[m] + 0.2


def paint_log_end(st, cx, cy, rad, seed):
    r = rng(seed)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    ang = np.arctan2(yy - cy, xx - cx)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) * (1 + 0.05 * np.sin(ang * 5 + r.uniform(0, 6)))
    disc = d < rad
    rings = 0.5 + 0.5 * np.cos(d * 0.9)
    bark = d > rad * 0.9
    col = (np.array([150, 112, 78]) / 255.0) * (0.8 + 0.2 * rings[..., None])
    col = np.where(bark[..., None], TIMBER / 255.0 * 0.7, col)
    crack = (np.abs(((ang + 3.2) % 0.9) - 0.45) < 0.015) & (d < rad * 0.7)
    col[crack] = INK / 255.0
    st.d[disc] = col[disc]
    st.h[disc] = (0.55 + 0.03 * rings - 0.1 * crack)[disc]


def wood_components():
    """The plank strips, the long-grain block and the log-end discs of the vanilla BaseWood trim sheet."""
    v = vanilla("BaseWood_1K_D_White", "RGB")
    whiteish = v.min(2) > 0.80
    wood = ndi.binary_opening(~whiteish, iterations=2)
    wood = ndi.binary_fill_holes(wood)
    return components(wood)


# ------------------------------------------------------------------------------------------------ sets
def make_timber():
    """Replaces BaseWood_Brown (the main structural wood): dark oiled timber boards in the same strips, end grain on
    the log-end discs, dark gaps between boards."""
    st = Set("Timber")
    st.d[:] = color_field(np.array([52, 40, 32]), 0.08, 13, 48)
    st.h[:] = 0.1 + 0.05 * noise(14, 24)
    for k, (x0, y0, x1, y1, m) in enumerate(wood_components()):
        w, h = x1 - x0, y1 - y0
        if w > 300 and h > 300:
            x, j = x0, 0
            while x < x1:
                bw = int(rng(800 + j).integers(48, 90))
                sub = np.zeros_like(m)
                sub[:, x:min(x + bw, x1)] = True
                paint_board(st, m & sub, x, y0, min(x + bw, x1), y1, 900 + j)
                x += bw
                j += 1
        elif h > 1.8 * w or w > 1.8 * h:
            paint_board(st, m, x0, y0, x1, y1, 1000 + k, horizontal=w > h)
        else:
            paint_log_end(st, (x0 + x1) / 2, (y0 + y1) / 2, min(w, h) / 2 * 0.95, 1100 + k)
    st.smooth = 0.30
    st.metal = 0.02
    return st


def make_bamboo():
    """Replaces the BaseWood trim sheet: plank strips become split bamboo slats, the long-grain block becomes a row
    of thin culms, log ends become hollow cross-sections, the plain corner a pale lime wash."""
    st = Set("Bamboo")
    # background (gaps, plain corner): lime wash
    st.d[:] = color_field(LIME, 0.05, 11, 48)
    st.h[:] = 0.1 + 0.05 * noise(12, 24)
    k = 0
    for x0, y0, x1, y1, m in wood_components():
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


def make_weave(name="Weave", strip=32, seed=21, moss=False):
    """Replaces IrregularPlanks: woven bamboo matting (twill), seamless. Three variants (plain, coarse, mossy) so the
    atlas fragments IrregularPlanks_White/Brown/Mossy keep distinct texture sets (AutoAtlaser keys on textures)."""
    st = Set(name)
    yy, xx = np.mgrid[0:S, 0:S]
    u = (xx + yy) // strip          # diagonal strands one way
    vv = (xx - yy) % S // strip     # and the other
    over = ((u + (vv // 2)) % 2 == 0)
    tu = ((xx + yy) % strip) / strip
    tv = (((xx - yy) % S) % strip) / strip
    prof_u = np.sin(np.pi * tu)
    prof_v = np.sin(np.pi * tv)
    hh = np.where(over, 0.6 + 0.3 * prof_u, 0.4 + 0.3 * prof_v).astype(np.float32)
    fib_a = noise(seed, 5, 1.5, aniso=(0.08, 1.0))
    fib = np.where(over, noise(seed + 1, 5, 1.5, aniso=(1.0, 0.08)), fib_a)
    base = np.where(over[..., None], BAMBOO_PALE / 255.0, BAMBOO_PALE / 255.0 * 0.86)
    per = noise(seed + 2, 40)
    d = base * (0.88 + 0.12 * np.where(over, prof_u, prof_v)[..., None]) * (0.92 + 0.1 * fib[..., None])
    d *= (0.94 + 0.1 * per[..., None])
    edge = np.minimum(np.where(over, prof_u, prof_v), 1)
    d *= (0.6 + 0.4 * np.clip(edge * 3, 0, 1))[..., None]
    st.h = hh + 0.04 * fib
    if moss:
        m = np.clip((noise(seed + 3, 50) * 0.7 + noise(seed + 4, 8) * 0.3 - 0.5) * 4, 0, 1) * (1 - 0.5 * edge)
        d = d * (1 - m[..., None]) + (TEA / 255.0 * 0.75)[None, None, :] * (0.8 + 0.3 * noise(seed + 5, 3))[..., None] * m[..., None]
        st.h = st.h + 0.1 * m
    st.d = d.astype(np.float32)
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
    # three overlapping tiles per course, each with a lip at its lower end
    tile_len = course / 3
    curve = np.where(cover, 9 * np.sin(np.pi * tc), -4 * np.clip(1 - np.abs(cx - 0.5) * 2, 0, 1))
    ycl = (yc + curve) % tile_len         # tile lips are arcs, not straight lines
    seg = ycl / tile_len                  # 0 at a tile's lower lip, 1 at its upper end (rows grow downwards)
    lip = np.exp(-ycl / 4.0)
    hh = hh + 0.12 * (1 - seg) - 0.18 * lip
    # overlap shadow just below each course edge (yc small means just below the edge)
    under = np.exp(-yc / 18.0)
    hh = hh - 0.35 * under
    hh = hh + 0.04 * noise(31, 10)
    pair = (xx // col_w).astype(int)
    tile_i = ((yy - edge0) // tile_len).astype(int)
    var = (np.sin(pair * 12.9898 + tile_i * 78.233) * 43758.5453) % 1.0
    base = TILE / 255.0 * (0.90 + 0.15 * var[..., None])
    pan_shade = 0.62 + 0.18 * np.clip(pan_t, 0, 1)            # pans are concave: darker down the middle
    base = np.where(cover[..., None], base * (0.70 + 0.45 * np.sin(np.pi * tc))[..., None], base * pan_shade[..., None])
    base = base * (1 - 0.35 * lip[..., None]) * (1 - 0.55 * under[..., None])
    grime = noise(32, 60)
    base = base * (0.88 + 0.18 * grime[..., None])
    lichen = (noise(33, 30) > 0.80) & ~cover
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


def make_plaster(name="Plaster", base=LIME, seed=40):
    """White lime plaster: soft mottling and trowel marks."""
    st = Set(name)
    n1, n2, n3 = noise(seed, 120), noise(seed + 1, 24), noise(seed + 2, 6)
    st.d = color_field(base, 0.04, seed + 3, 140) * (0.95 + 0.05 * n2[..., None]) * (0.97 + 0.04 * n3[..., None])
    pits = noise(seed + 4, 3, 1.0) > 0.86
    st.d[pits] *= 0.92
    st.h = 0.3 * n1 + 0.15 * n2 + 0.05 * n3 - 0.1 * pits
    st.smooth = 0.18
    st.nstrength = 3.0
    return st


def make_plastered_wood():
    """Replaces PlasteredWood: lime plaster over wattle; where it has spalled, bamboo laths and rammed earth show."""
    st = make_plaster("PlasterLath", LIME, 50)
    r = rng(51)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    lath = np.zeros((S, S), np.float32)
    for _ in range(110):
        cy, cx = r.uniform(0, S), r.uniform(0, S)
        ln, th = r.uniform(40, 130), r.uniform(2.0, 4.0)
        dx = (xx - cx + S / 2) % S - S / 2
        dy = (yy - cy + S / 2) % S - S / 2
        taper = np.clip(1 - (2 * dx / ln) ** 2, 0, 1)
        lath = np.maximum(lath, np.exp(-(dy ** 2) / (2 * (th * taper + 0.01) ** 2)) * (np.abs(dx) < ln / 2))
    spall = np.clip((noise(52, 70) - 0.66) * 6, 0, 1)
    earth = EARTH / 255.0 * (0.85 + 0.2 * noise(53, 8)[..., None])
    st.d = st.d * (1 - spall[..., None]) + earth * spall[..., None]
    st.d = st.d * (1 - lath[..., None]) + (BAMBOO_PALE / 255.0 * 0.62) * lath[..., None]
    st.h = st.h - 0.25 * spall + 0.2 * lath
    return st


def lattice_lantern(period=64, bar=4):
    """Chinese "lantern frame" lattice (deng long kuang): square cells with an inner panel tied to the frame by
    short bars at the middle of each side."""
    yy, xx = np.mgrid[0:S, 0:S]
    u, v = xx % period, yy % period
    half, inset = period / 2, period * 0.28
    border = (u < bar) | (v < bar)
    inner = (np.abs(u - half) < half - inset) & (np.abs(v - half) < half - inset)
    inner_core = (np.abs(u - half) < half - inset - bar) & (np.abs(v - half) < half - inset - bar)
    inner_edge = inner & ~inner_core
    ties = ((np.abs(u - half) < bar / 2 + 0.5) & ~inner) | ((np.abs(v - half) < bar / 2 + 0.5) & ~inner)
    return border | inner_edge | ties


def lattice_ice(seed=7, cell=46, bar=2.6):
    """Chinese cracked-ice lattice (bing lie wen): straight bars along the edges of an irregular tiling."""
    from scipy.spatial import cKDTree
    r = rng(seed)
    n = int((S / cell) ** 2)
    pts = r.uniform(0, S, (n, 2))
    tiled = np.concatenate([pts + [dx, dy] for dx in (-S, 0, S) for dy in (-S, 0, S)])
    yy, xx = np.mgrid[0:S, 0:S]
    q = np.stack([xx.ravel(), yy.ravel()], 1).astype(np.float32)
    d, _ = cKDTree(tiled).query(q, k=2)
    return ((d[:, 1] - d[:, 0]) < bar).reshape(S, S)


def make_lattice_paper():
    """Replaces Paper: paper panels in dark timber frames (frame lines where the vanilla sheet has them), each panel
    backed by a lantern-frame lattice."""
    st = Set("LatticePaper")
    v = vanilla("Paper_D.Folktails", "RGB")
    lum = v.mean(2)
    lines = (blur(lum, 6) - lum) > 0.05
    lines = ndi.binary_closing(ndi.binary_opening(lines, iterations=1), iterations=2)
    lines = ndi.binary_dilation(lines, iterations=3)
    lat = lattice_lantern(85, 4) & ~lines
    fib = noise(61, 3, 1.2)
    st.d = color_field(PAPER, 0.03, 62, 200) * (0.95 + 0.07 * fib[..., None])
    soft = blur(lines.astype(np.float32), 1.2)
    lats = blur(lat.astype(np.float32), 0.8)
    timber = TIMBER / 255.0 * (0.85 + 0.25 * noise(63, 20, aniso=(1, 0.2))[..., None])
    st.d = st.d * (1 - lats[..., None]) + timber * 0.9 * lats[..., None]
    st.d = st.d * (1 - soft[..., None]) + timber * soft[..., None]
    st.h = 0.2 + 0.03 * fib + 0.3 * lats + 0.45 * soft
    st.smooth = np.where(lines | lat, 0.4, 0.12)
    return st


def make_iron():
    """Replaces BaseMetal: hand-forged iron, soot-dark with rust in the seams; plate seams and rivets follow the
    vanilla sheet's layout (read from its normal map)."""
    st = Set("Iron")
    vn = vanilla("BaseMetal_N")
    dev = np.sqrt((vn[..., 3] - 0.5) ** 2 + (vn[..., 1] - 0.5) ** 2)
    seams = blur(dev, 1.0) > 0.12
    seams = ndi.binary_opening(seams, iterations=1)
    sf = blur(seams.astype(np.float32), 1.5)
    n1, n2 = noise(71, 80), noise(72, 8)
    st.d = color_field(IRON, 0.10, 73, 90) * (0.9 + 0.15 * n2[..., None])
    rust = np.clip((blur(sf, 6) * 1.5 + 0.6 * n1 - 0.6) * 2, 0, 1)
    st.d = st.d * (1 - 0.7 * rust[..., None]) + RUST / 255.0 * 0.7 * rust[..., None]
    st.d = st.d * (1 - 0.5 * sf[..., None])
    st.h = 0.5 - 0.35 * sf + 0.05 * n2
    st.metal = 0.6 - 0.45 * rust
    st.smooth = 0.4 - 0.25 * rust
    return st


def make_painted():
    """Replaces PaintedMetal (vanilla yellow/black hazard stripes on machinery): the stripes become straw-gold cane
    binding over soot-black iron. No red here: red is kept for accents."""
    st = Set("Banded")
    v = vanilla("PaintedMetal_D.Folktails", "RGB")
    yellow = (v[..., 0] > 0.55) & (v[..., 1] > 0.45) & (v[..., 2] < 0.35)
    yellow = ndi.binary_closing(ndi.binary_opening(yellow, iterations=2), iterations=3)
    ys = blur(yellow.astype(np.float32), 1.5)
    yy = np.mgrid[0:S, 0:S][0]
    wrap = 0.75 + 0.25 * np.abs(np.sin(yy * 0.45))          # cane wraps across the band
    wear = noise(81, 18) * noise(82, 90)
    chips = (wear > 0.55) & yellow
    cane = (BAMBOO_PALE / 255.0 * np.array([0.95, 0.80, 0.52]))[None, None, :] * wrap[..., None]
    base = cane * ys[..., None] + (IRON / 255.0 * 0.8) * (1 - ys[..., None])
    base = base * (0.92 + 0.12 * noise(83, 50)[..., None])
    base[chips] = IRON / 255.0
    st.d = base.astype(np.float32)
    st.h = 0.5 + 0.1 * ys * wrap - 0.15 * chips + 0.02 * noise(84, 4)
    st.smooth = np.where(yellow, 0.35, 0.45)
    st.metal = np.where(yellow & ~chips, 0.0, 0.55)
    return st


def make_windows():
    """Replaces WindowsAtlas: same window shapes; frames become dark timber, the glass becomes paper on a
    cracked-ice lattice, the wall around them lime plaster, and the night glow (_LightingMap) is warm lamplight
    through paper, broken by the lattice."""
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
    lattice = lattice_ice(7, 40, 2.4)
    st.d = color_field(LIME, 0.04, 91, 120) * 0.95
    edge = blur(frame.astype(np.float32), 2.0)       # frames darken toward their edges
    timber = TIMBER / 255.0 * (0.85 + 0.3 * noise(94, 20, aniso=(1, 0.3)))[..., None]
    st.d[frame] = timber[frame] * (0.6 + 0.4 * edge[frame])[:, None]
    st.d[interior] = (INK / 255.0)[None, :] * (0.8 + 0.4 * noise(92, 120)[interior])[:, None]
    gl = glass & ~lattice
    st.d[gl] = PAPER_WARM / 255.0
    st.d[glass & lattice] = TIMBER / 255.0 * 0.9
    st.h = 0.3 + 0.3 * edge * frame - 0.1 * gl + 0.12 * (glass & lattice) - 0.2 * interior + 0.03 * noise(93, 6)
    st.smooth = np.where(frame, 0.4, 0.15)
    e = np.zeros((S, S, 3), np.float32)
    # warm lamplight through paper: flat and strong across the panes (the vanilla map falls off toward the frame),
    # cut by the lattice; the doorway keeps the vanilla soft gradient
    e[:] = (np.array([255, 234, 188]) / 255.0)[None, None, :]
    pane = np.where(glass, np.clip(0.92 + 0.1 * glow_soft, 0, 1), glow_soft)
    e *= (pane * (~(lattice & glass)))[..., None]
    st.e = e
    return st


def make_details():
    """Replaces Details: the banner becomes indigo-dyed cloth with ink-painted bamboo; the sack is hemp, the rope
    rice straw, the three good labels are plain colour fields with simple pictures (no writing); crate and plank
    regions keep their seams (read from the vanilla sheet) and are filled with bamboo, the metal bands become cane
    lashing."""
    st = Set("Details")
    v = vanilla("Details_D.Folktails", "RGB")
    lum = v.mean(2)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    seams = (blur(lum, 4) - lum) > 0.06
    seams = ndi.binary_dilation(ndi.binary_opening(seams), iterations=1)
    st.d[:] = BAMBOO_PALE / 255.0 * 0.85
    st.h[:] = 0.4
    lower = np.zeros((S, S), bool)
    lower[512:, :] = True
    slat = lower & ~seams
    for k, (x0, y0, x1, y1, m) in enumerate(components(slat, 200)):
        paint_culm(st, m, x0, y0, x1, y1, 700 + k, horizontal=(x1 - x0) > (y1 - y0), node_gap=(60, 120))
    st.d[lower & seams] = TIMBER / 255.0 * 0.8
    st.h[lower & seams] = 0.1
    band = lower & (v[..., 2] > 0.55) & (np.abs(v[..., 0] - v[..., 2]) < 0.12)
    band = ndi.binary_opening(band, iterations=2)
    rope = 0.75 + 0.25 * np.sin((xx + yy) * 0.6)
    st.d[band] = (np.array([196, 170, 120]) / 255.0)[None, :] * rope[band][:, None]
    st.h[band] = 0.6 + 0.2 * rope[band]
    # banner (0..512, 0..512): indigo cloth, a pale disc, ink-painted bamboo stalk and leaves
    by, bx = slice(0, 512), slice(0, 512)
    cloth = 0.88 + 0.12 * noise(94, 20, aniso=(1, 0.3))[by, bx]
    st.d[by, bx] = (INDIGO / 255.0)[None, None, :] * cloth[..., None]
    st.h[by, bx] = 0.3 + 0.1 * cloth
    X, Y = xx[by, bx], yy[by, bx]
    disc = (X - 256) ** 2 + (Y - 250) ** 2 < 165 ** 2
    st.d[by, bx][disc] = PAPER / 255.0 * 0.95
    ink = np.zeros((512, 512), bool)
    stalk_x = 230 + 0.06 * (Y - 250)
    ink |= (np.abs(X - stalk_x) < 9) & (np.abs(Y - 250) < 150)
    for ny in (150, 230, 310):                                         # nodes
        ink |= (np.abs(Y - ny) < 3) & (np.abs(X - (230 + 0.06 * (ny - 250))) < 13)
    for (lx, ly, ang, ln) in ((240, 160, -0.5, 95), (240, 165, -0.9, 80), (238, 235, 0.35, 100),
                              (238, 240, 0.75, 85), (222, 300, 3.5, 90), (222, 305, 2.9, 75)):
        ca, sa = np.cos(ang), np.sin(ang)
        u = ((X - lx) * ca + (Y - ly) * sa) / ln
        w = (-(X - lx) * sa + (Y - ly) * ca) / ln
        ink |= (u > 0) & (u < 1) & (np.abs(w) < 0.14 * np.sin(np.pi * np.clip(u, 0, 1)) ** 0.8)
    ink &= disc
    st.d[by, bx][ink] = INK / 255.0
    st.h[by, bx][ink] = 0.42
    # sack (512..768, 0..512): hemp
    sy, sx = slice(0, 512), slice(512, 768)
    weave = 0.85 + 0.15 * (np.sin(xx[sy, sx] * 1.4) * np.sin(yy[sy, sx] * 1.4))
    st.d[sy, sx] = color_field(np.array([200, 182, 146]), 0.08, 95, 40)[sy, sx] * weave[..., None]
    st.h[sy, sx] = 0.4 + 0.25 * noise(96, 40)[sy, sx] + 0.05 * weave
    # rope column (768..832): twisted rice straw
    ry, rx = slice(0, 512), slice(768, 832)
    twist = 0.7 + 0.3 * np.sin((xx[ry, rx] * 0.4 + yy[ry, rx]) * 0.35)
    st.d[ry, rx] = (np.array([196, 170, 110]) / 255.0)[None, None, :] * twist[..., None]
    st.h[ry, rx] = 0.4 + 0.3 * twist
    # labels (832..1024): three colour fields with simple pictures; one small red accent
    for (y0, y1), colr, mark in (((0, 170), LACQUER, "logs"), ((170, 340), TEA, "leaf"),
                                 ((340, 512), INDIGO, "dots")):
        st.d[y0:y1, 832:1024] = colr / 255.0
        st.h[y0:y1, 832:1024] = 0.45
        X, Y = xx[y0:y1, 832:1024] - 928, yy[y0:y1, 832:1024] - (y0 + y1) / 2
        if mark == "logs":
            m = (np.abs(Y) < 40) & (np.abs(X) < 55) & ((np.abs(Y) % 28) < 22)
        elif mark == "leaf":
            m = (np.abs(X) < 55) & (np.abs(Y + 0.004 * X * X) < 18 * np.clip(1 - (X / 55) ** 2, 0, 1) + 1)
        else:
            m = np.zeros_like(X, bool)
            for ox, oy in ((-25, -15), (20, -20), (0, 18), (-30, 25), (30, 20)):
                m |= (X - ox) ** 2 + (Y - oy) ** 2 < 15 ** 2
        st.d[y0:y1, 832:1024][m] = PAPER / 255.0
        st.h[y0:y1, 832:1024][m] = 0.55
    st.smooth = 0.25
    return st


def make_earth():
    """Replaces Sand: rammed earth, in horizontal pour layers with small river pebbles."""
    st = make_plaster("RammedEarth", EARTH, 100)
    yy = np.mgrid[0:S, 0:S][0].astype(np.float32)
    layers = 0.5 + 0.5 * np.sin(yy / S * 2 * np.pi * 12 + 2 * noise(101, 80))
    st.d *= (0.9 + 0.12 * layers[..., None])
    pebbles = noise(102, 5, 1.0) > 0.74
    st.d[pebbles] = st.d[pebbles] * 0.4 + STONE / 255.0 * 0.6
    st.h += 0.08 * layers + 0.2 * pebbles
    return st


def make_moss():
    st = make_plaster("Moss", TEA, 110)
    st.d *= (0.8 + 0.3 * noise(111, 4)[..., None])
    st.smooth = 0.1
    return st


SETS = {
    "Timber": baked_or("Timber", make_timber, 0.30), "Bamboo": baked_or("Bamboo", make_bamboo, 0.40),
    "Weave": baked_or("Weave", make_weave, 0.25),
    "WeaveCoarse": baked_or("WeaveCoarse", lambda: make_weave("WeaveCoarse", 48, 121), 0.22),
    "WeaveMossy": baked_or("WeaveMossy", lambda: make_weave("WeaveMossy", 32, 221, True), 0.20),
    "RoofTiles": baked_or("RoofTiles", make_tiles, 0.30, crisp=1.0),
    "Plaster": make_plaster,
    "PlasterLath": baked_or("PlasterLath", make_plastered_wood, 0.18, crisp=0.4),
    "LatticePaper": baked_or("LatticePaper", make_lattice_paper, 0.3, crisp=0.5),
    "Iron": baked_or("Iron", make_iron, 0.35, crisp=0.6), "Banded": baked_or("Banded", make_painted, 0.4, crisp=0.6),
    "Windows": baked_or("Windows", make_windows, 0.3, keep_emission=True, crisp=0.5),
    "Details": baked_or("Details", make_details, 0.25, crisp=0.6),
    "RammedEarth": make_earth, "Moss": make_moss,
}

# painter sets that can go through the Blender heightfield bake (--export-hf), and their plain painters
HF_PAINTERS = {"PlasterLath": make_plastered_wood, "LatticePaper": make_lattice_paper, "Iron": make_iron,
               "Banded": make_painted, "Windows": make_windows, "Details": make_details}

# vanilla material -> (texture set, tint key or None)
MATERIALS = {
    "BaseWood_Brown.Folktails": ("Timber", "BaseWood_Brown"),
    "BaseWood_White.Folktails": ("Bamboo", "BaseWood_White"),
    "BaseWood_LightBrown.Folktails": ("Bamboo", "BaseWood_LightBrown"),
    "BaseWood_Yellow.Folktails": ("Bamboo", "BaseWood_Yellow"),
    "IrregularPlanks_White.Folktails": ("Weave", "IrregularPlanks_White"),
    "IrregularPlanks_Brown.Folktails": ("WeaveCoarse", "IrregularPlanks_Brown"),
    "IrregularPlanks_LightBrown.Folktails": ("Weave", "IrregularPlanks_LightBrown"),
    "IrregularPlanks_Yellow.Folktails": ("Weave", "IrregularPlanks_Yellow"),
    "IrregularPlanks_Mossy.Folktails": ("WeaveMossy", "IrregularPlanks_Mossy"),
    "ThatchedRoof.Folktails": ("RoofTiles", None),
    "Plaster_White.Folktails": ("Plaster", None),
    "PlasteredWood_White.Folktails": ("PlasterLath", None),
    "Paper.Folktails": ("LatticePaper", None),
    "BaseMetal.Folktails": ("Iron", None),
    "PaintedMetal.Folktails": ("Banded", None),
    "WindowsAtlas.Folktails": ("Windows", None),
    "Details.Folktails": ("Details", None),
    "Sand.Folktails": ("RammedEarth", None),
    "Moss.Folktails": ("Moss", None),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unity", default=r"E:\PandabornDev\unity\PandabornLook")
    ap.add_argument("--only", default="")
    ap.add_argument("--preview", default=r"E:\PandabornDev\build\look\preview")
    ap.add_argument("--export-hf", default="", help="painter sets whose height + albedo go to the Blender heightfield bake")
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
        if name in set(filter(None, a.export_hf.split(","))):
            st = HF_PAINTERS[name]()
            os.makedirs(BAKE, exist_ok=True)
            np.savez_compressed(os.path.join(BAKE, name + "_hf.npz"), h=st.h.astype(np.float32), d=st.d.astype(np.float32))
            print("  exported heightfield for the Blender bake", flush=True)
            maps[name] = st.write(texdir)
            continue
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
