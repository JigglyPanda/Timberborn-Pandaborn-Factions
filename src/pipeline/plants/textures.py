"""Paints the plant atlases (no vanilla pixels: everything is drawn here) and writes the Unity material spec.

    python -I src/pipeline/plants/textures.py [--unity E:\\PandabornDev\\unity\\PandabornPlants] [--out DIR]

Writes PandabornPlants_D.png (2048, RGBA, alpha = cut-out), PandabornPlants_N.png (2048, linear, swizzled like the
vanilla maps: R = 1, G = B = y, A = x), PandabornPlants_Detail.png (1024, RGBA; the yield overlay), into
<out> (default E:\\PandabornDev\\build\\plants\\textures) with a preview contact sheet and plants_preview.json for
preview.py, and, with --unity, into <project>/Assets/PandabornPlants/Textures plus plants_spec.json for
PandabornPlantsBuilder.cs. Deterministic: fixed seeds.

Layout: atlas.py. Style: leaves near-grey with painted light (value) and a soft drop shadow under each leaf, so the
vertex colour of a model sets the hue (fresh, dry, dead) exactly as the vanilla plant sheets work; bark, sheaths, rice
heads, pepper berries and the detail sheet (persimmons, tea flush, bamboo fungus) in colour.
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import atlas  # noqa: E402

OUT = r"E:\PandabornDev\build\plants\textures"


# ============================================================================================ canvas
class Canvas:
    def __init__(self, size):
        self.s = size
        self.col = np.zeros((size, size, 3), np.float32)
        self.a = np.zeros((size, size), np.float32)
        self.h = np.zeros((size, size), np.float32)
        self.layer = 0.0
        self.clip = (0, 0, size, size)     # sprites never paint outside their own region (set by region_origin)

    # --- compositing a soft mask with colour and height inside a bbox
    def put(self, x0, y0, a, col, h, shadow=0.0, shadow_off=(3, 4), shadow_blur=3.0):
        H, W = a.shape
        x1, y1 = x0 + W, y0 + H
        k0, k1, k2, k3 = self.clip
        cx0, cy0, cx1, cy1 = max(x0, k0), max(y0, k1), min(x1, k2), min(y1, k3)
        if cx1 <= cx0 or cy1 <= cy0:
            return
        sl = (slice(cy0, cy1), slice(cx0, cx1))
        ls = (slice(cy0 - y0, cy1 - y0), slice(cx0 - x0, cx1 - x0))
        a = a[ls]
        col = col[ls] if col.ndim == 3 else col
        h = h[ls] if np.ndim(h) == 2 else h
        if shadow > 0:
            sm = ndimage.shift(a, (shadow_off[1], shadow_off[0]), order=1, mode="constant")
            sm = ndimage.gaussian_filter(sm, shadow_blur)
            self.col[sl] *= (1 - shadow * sm * (self.a[sl] > 0.01))[..., None]
            self.h[sl] -= 0.15 * sm * (self.a[sl] > 0.01)
        self.layer += 0.002
        self.col[sl] = self.col[sl] * (1 - a[..., None]) + col * a[..., None]
        self.h[sl] = self.h[sl] * (1 - a) + (h + self.layer) * a
        self.a[sl] = self.a[sl] + a * (1 - self.a[sl])


def grid(x0, y0, x1, y1):
    ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    return xs + 0.5, ys + 0.5


def smooth(x):
    return np.clip(x, 0, 1) ** 2 * (3 - 2 * np.clip(x, 0, 1))


def value_noise(shape, scale, seed, octaves=3):
    rng = np.random.default_rng(seed)
    out = np.zeros(shape, np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        s = max(2, int(max(shape) / scale * (2 ** o)))
        g = rng.random((s + 3, s + 3)).astype(np.float32)
        z = ndimage.zoom(g, (shape[0] / s, shape[1] / s), order=3)[:shape[0], :shape[1]]
        out += amp * z
        tot += amp
        amp *= 0.5
    return out / tot


# ============================================================================================ primitives
LIGHT = np.array([-0.55, -0.6])   # painted key light from the upper left (image space, y down)


def leaf(cv, base, angle, length, width, value=0.8, profile="lance", bend=0.0, rng=None, veins=True, serrate=0.0,
         midrib=0.12, midrib_w=0.06, shadow=0.35, color=None, crinkle=0.0, tip_dark=0.0, edge_dark=0.22, curl=0.0):
    """A leaf from `base` (px) pointing at `angle` (radians, 0 = right, y down), midrib bent sideways by `bend` (fraction
    of length at the tip). profile: lance (bamboo, rice), ellipse (tea, persimmon), obovate (cabbage), ovate."""
    rng = rng or np.random.default_rng(0)
    d = np.array([math.cos(angle), math.sin(angle)])
    n = np.array([-d[1], d[0]])
    L, Wd = float(length), float(width)
    pts = [np.array(base) + d * L * s + n * bend * L * s * s for s in np.linspace(0, 1, 9)]
    pts = np.array(pts)
    pad = Wd + 3
    x0, y0 = int(math.floor(pts[:, 0].min() - pad)), int(math.floor(pts[:, 1].min() - pad))
    x1, y1 = int(math.ceil(pts[:, 0].max() + pad)), int(math.ceil(pts[:, 1].max() + pad))
    X, Y = grid(x0, y0, x1, y1)
    qx, qy = X - base[0], Y - base[1]
    s = (qx * d[0] + qy * d[1]) / L
    toff = (qx * n[0] + qy * n[1]) - bend * L * np.clip(s, 0, 1) ** 2
    sc = np.clip(s, 0, 1)
    if profile == "lance":
        prof = np.clip(np.sin(np.pi * np.clip(sc, 0, 1) ** 0.75), 0, 1) ** 0.8
    elif profile == "ellipse":
        prof = np.sqrt(np.clip(1 - (2 * sc - 1) ** 2, 0, 1))
    elif profile == "obovate":   # widest at about 3/4 of the length, a round tip
        prof = (sc ** 0.7) * np.sqrt(np.clip(1 - sc ** 4, 0, 1)) / 0.86
    elif profile == "ovate":
        prof = np.sqrt(np.clip(1 - (2 * sc - 0.8) ** 2 / 1.2 ** 2, 0, 1)) * np.clip((1 - sc) * 3, 0, 1) ** 0.6
    else:
        prof = np.ones_like(sc)
    hw = Wd / 2 * prof
    if serrate > 0:
        hw = hw * (1 - serrate * (0.5 + 0.5 * np.sin(sc * L / 4.5 * 2 * np.pi)))
    if crinkle > 0:
        wob = value_noise(X.shape, 14, int(rng.integers(1e6)), 2) - 0.5
        hw = hw * (1 + crinkle * wob * 1.6)
    side = hw - np.abs(toff)
    ends = np.minimum(s * L, (1 - s) * L * 1.0)
    dist = np.minimum(side, ends + 0.5)
    a = np.clip(dist + 0.5, 0, 1) * (hw > 0.3)
    t = np.clip(toff / np.maximum(hw, 1e-3), -1, 1)
    # painted light: the half of the blade facing the key light is brighter (a folded leaf), edges darker
    lit = 0.5 + 0.5 * np.sign(t) * np.sign(n @ LIGHT + 1e-6) * -1
    v = value * (0.86 + 0.16 * lit) * (1 - edge_dark * np.abs(t) ** 2.2) * (0.86 + 0.14 * np.clip(sc * 2.5, 0, 1))
    v = v * (1 - tip_dark * np.clip((sc - 0.75) * 4, 0, 1))
    h = (1 - t * t) * 0.6 + curl * t
    if midrib > 0:
        mr = np.clip(1 - np.abs(toff) / max(Wd * midrib_w * (1.2 - 0.7 * sc).mean(), 0.6), 0, 1)
        v = v + midrib * mr
        h = h - 0.25 * mr
    if veins:
        sp = max(L / 9.0, 4.0)
        ph = (sc * L - np.abs(toff) * 0.9) / sp
        vein = np.clip(1 - np.abs(ph - np.round(ph)) * 7, 0, 1) * (np.abs(t) > 0.12) * (np.abs(t) < 0.92)
        v = v - 0.07 * vein
        h = h - 0.12 * vein
    if crinkle > 0:
        nz = value_noise(X.shape, 7, int(rng.integers(1e6)), 2)
        v = v * (0.9 + 0.2 * nz)
        h = h + crinkle * 0.9 * nz
    v = np.clip(v, 0, 1)
    if color is None:
        col = np.repeat(v[..., None], 3, 2)
    else:
        col = np.clip(np.asarray(color)[None, None, :] * v[..., None] / max(value, 1e-3), 0, 1)
    cv.put(x0, y0, a.astype(np.float32), col.astype(np.float32), h.astype(np.float32), shadow=shadow)


def stroke(cv, pts, w0, w1, value=0.5, color=None, shadow=0.25, round_tip=True):
    """A tapered stem/twig along polyline pts (px), width w0 at the start to w1 at the end."""
    pts = np.asarray(pts, float)
    seg = np.diff(pts, axis=0)
    lens = np.linalg.norm(seg, axis=1)
    cum = np.concatenate([[0], np.cumsum(lens)])
    tot = max(cum[-1], 1e-6)
    pad = max(w0, w1) + 3
    x0, y0 = int(pts[:, 0].min() - pad), int(pts[:, 1].min() - pad)
    x1, y1 = int(pts[:, 0].max() + pad), int(pts[:, 1].max() + pad)
    X, Y = grid(x0, y0, x1, y1)
    best = np.full(X.shape, 1e9, np.float32)
    rad = np.zeros(X.shape, np.float32)
    for i in range(len(seg)):
        p, dv, ln = pts[i], seg[i], max(lens[i], 1e-6)
        t = np.clip(((X - p[0]) * dv[0] + (Y - p[1]) * dv[1]) / (ln * ln), 0, 1)
        dx, dy = X - (p[0] + t * dv[0]), Y - (p[1] + t * dv[1])
        dist = np.sqrt(dx * dx + dy * dy)
        r = (w0 + (w1 - w0) * (cum[i] + t * ln) / tot) / 2
        rel = dist - r
        m = rel < best
        best = np.where(m, rel, best)
        rad = np.where(m, r, rad)
    a = np.clip(0.5 - best, 0, 1)
    rr = np.clip(1 - (best + rad) / np.maximum(rad, 1e-3), 0, 1)   # 1 at the centre line
    v = value * (0.7 + 0.35 * np.sqrt(rr))
    col = np.repeat(v[..., None], 3, 2) if color is None else np.clip(np.asarray(color)[None, None] * (v / value)[..., None], 0, 1)
    cv.put(x0, y0, a.astype(np.float32), col.astype(np.float32), (rr * 0.8).astype(np.float32), shadow=shadow)


def blob(cv, c, rx, ry, color, shade=0.35, spec=0.25, shadow=0.3, h=1.0, angle=0.0):
    """A shaded ellipse (berry, fruit) with a highlight."""
    x0, y0 = int(c[0] - rx - 3), int(c[1] - ry - 3)
    X, Y = grid(x0, y0, int(c[0] + rx + 4), int(c[1] + ry + 4))
    ca, sa = math.cos(angle), math.sin(angle)
    u = ((X - c[0]) * ca + (Y - c[1]) * sa) / rx
    w = (-(X - c[0]) * sa + (Y - c[1]) * ca) / ry
    r2 = u * u + w * w
    a = np.clip((1 - np.sqrt(r2)) * min(rx, ry) + 0.5, 0, 1)
    z = np.sqrt(np.clip(1 - r2, 0, 1))
    lam = np.clip(-0.45 * u - 0.5 * w + 0.75 * z, 0, 1)
    col = np.asarray(color)[None, None] * ((1 - shade) + shade * lam)[..., None]
    hl = np.clip(1 - np.sqrt((u + 0.38) ** 2 + (w + 0.42) ** 2) / 0.32, 0, 1) ** 1.5
    col = np.clip(col + spec * hl[..., None], 0, 1)
    cv.put(x0, y0, a.astype(np.float32), col.astype(np.float32), (z * h).astype(np.float32), shadow=shadow)


# ============================================================================================ sprites
CURRENT = []


def region_origin(name, regions=atlas.REGIONS):
    x0, y0, x1, y1 = regions[name]
    if CURRENT:
        CURRENT[0].clip = (x0 + 1, y0 + 1, x1 - 1, y1 - 1)
    return x0, y0, x1 - x0, y1 - y0


def bamboo_spray(cv, name, seed, leaves=(5, 9), scale=1.0, droop=0.25, value=0.82):
    """Fan sprays: a twig from the bottom centre rising and branching, with palmate groups of 3-6 narrow leaves at the
    twig nodes, fanned outward and drooping. Seen from above on a tilted card, base toward the culm."""
    rng = np.random.default_rng(seed)
    x0, y0, W, H = region_origin(name)
    bx, by = x0 + W * 0.5, y0 + H * 0.97
    twigs = []
    n_tw = 3 if W >= 400 else 2
    for k in range(n_tw):
        ang = -math.pi / 2 + (k - (n_tw - 1) / 2) * 0.62 + rng.uniform(-0.12, 0.12)
        ln = H * rng.uniform(0.62, 0.8)
        pts = [(bx + rng.uniform(-4, 4), by)]
        a = ang
        for i in range(5):
            a += rng.uniform(-0.12, 0.12)
            p = pts[-1]
            pts.append((p[0] + math.cos(a) * ln / 5, p[1] + math.sin(a) * ln / 5))
        twigs.append(pts)
        stroke(cv, pts, 5.5 * scale, 2.0 * scale, value=0.55, shadow=0.15)
    groups = []
    for pts in twigs:
        for i in (2, 3, 4, 5):
            if i >= len(pts):
                continue
            groups.append((pts[i], math.atan2(pts[i][1] - pts[i - 1][1], pts[i][0] - pts[i - 1][0])))
    rng.shuffle(groups)
    for (px, py), ta in groups:
        nl = int(rng.integers(leaves[0], leaves[1] + 1)) // 2 + 2
        spread = rng.uniform(1.1, 1.7)
        for j in range(nl):
            a = ta + (j - (nl - 1) / 2) * spread / max(nl - 1, 1) + rng.uniform(-0.1, 0.1)
            L = H * scale * rng.uniform(0.26, 0.36)
            Wd = L * rng.uniform(0.15, 0.19)
            bend = droop * (1 if math.cos(a) > 0 else -1) * rng.uniform(0.4, 1.0)
            leaf(cv, (px, py), a, L, Wd, value=value * rng.uniform(0.88, 1.08), profile="lance", bend=bend, rng=rng,
                 veins=False, midrib=0.10, midrib_w=0.08, shadow=0.38, tip_dark=0.05)


def bamboo_dead(cv, name, seed):
    rng = np.random.default_rng(seed)
    x0, y0, W, H = region_origin(name)
    bx, by = x0 + W * 0.5, y0 + H * 0.96
    for k in range(3):
        a = -math.pi / 2 + (k - 1) * 0.6
        pts = [(bx, by)]
        for i in range(4):
            a += rng.uniform(-0.25, 0.25)
            pts.append((pts[-1][0] + math.cos(a) * H * 0.18, pts[-1][1] + math.sin(a) * H * 0.18))
        stroke(cv, pts, 4, 1.5, value=0.6)
        for p in pts[2:]:
            for j in range(int(rng.integers(1, 4))):
                aa = a + rng.uniform(-1.2, 1.2)
                L = H * rng.uniform(0.18, 0.28)
                leaf(cv, p, aa, L, L * 0.09, value=0.78, bend=rng.uniform(-0.5, 0.5), rng=rng, veins=False,
                     midrib=0.05, curl=0.3, shadow=0.3)


def culm_strip(cv, name, node_every, base=0.84, seed=1, ridge=0.5):
    x0, y0, W, H = region_origin(name)
    rng = np.random.default_rng(seed)
    X, Y = grid(x0, y0, x0 + W, y0 + H)
    fib = value_noise((H, W * 8), 3, seed, 2)
    fib = ndimage.zoom(fib, (1, 1 / 8), order=1)[:H, :W]
    streak = value_noise((H // 6 + 2, W), 2, seed + 1, 1)
    streak = ndimage.zoom(streak, (H / streak.shape[0], 1), order=1)[:H, :W]
    v = base * (0.94 + 0.06 * fib) * (0.95 + 0.07 * streak)
    h = 0.05 * fib
    yy = (Y - y0)
    ph = (yy % node_every) / node_every    # 0 at a node line (top of a segment in image space)
    node = np.exp(-((yy % node_every) / 2.2) ** 2) + np.exp(-(((yy % node_every) - node_every) / 2.2) ** 2)
    below = np.clip(1 - ((yy % node_every) - 3) / (node_every * 0.12), 0, 1) * ((yy % node_every) > 3)
    v = v * (1 - ridge * 0.6 * node) + 0.12 * below * (1 - node)
    v = v * (1 - 0.08 * np.clip(ph * 3 - 2.2, 0, 1))          # slightly darker just above the next node
    h = h + 0.8 * node
    for k in range(int(H / node_every) + 1):                   # occasional sheath scars and blemishes
        if rng.random() < 0.5:
            cy = y0 + k * node_every + rng.uniform(10, node_every * 0.6)
            cx = x0 + rng.uniform(0, W)
            m = np.exp(-(((X - cx) / (W * 0.18)) ** 2 + ((Y - cy) / 5) ** 2))
            v = v * (1 - 0.1 * m)
    a = np.ones_like(v)
    cv.put(x0, y0, a, np.repeat(np.clip(v, 0, 1)[..., None], 3, 2).astype(np.float32), h.astype(np.float32))


def bark_strip(cv, name, seed=3):
    x0, y0, W, H = region_origin(name)
    rng = np.random.default_rng(seed)
    X, Y = grid(x0, y0, x0 + W, y0 + H)
    pts = np.stack([rng.uniform(x0, x0 + W, 220), rng.uniform(y0, y0 + H, 220)], 1)
    # plates elongated vertically: scale y distances
    pts_w = np.concatenate([pts, pts + [W, 0], pts - [W, 0]])     # wrap across u so the trunk has no seam
    d1 = np.full(X.shape, 1e9, np.float32)
    d2 = np.full(X.shape, 1e9, np.float32)
    for p in pts_w:
        d = np.sqrt((X - p[0]) ** 2 + ((Y - p[1]) * 0.45) ** 2)
        d2 = np.where(d < d1, d1, np.minimum(d2, d))
        d1 = np.minimum(d1, d)
    crack = np.clip(1 - (d2 - d1) / 3.0, 0, 1)
    nz = value_noise((H, W), 6, seed, 3)
    plate = np.array([0.33, 0.28, 0.24]) * (0.85 + 0.3 * nz)[..., None]
    col = plate * (1 - 0.65 * crack)[..., None]
    h = (1 - crack) * 0.8 + 0.2 * nz
    cv.put(x0, y0, np.ones(X.shape, np.float32), np.clip(col, 0, 1).astype(np.float32), h.astype(np.float32))


def thorny_strip(cv, name, seed=4):
    x0, y0, W, H = region_origin(name)
    rng = np.random.default_rng(seed)
    X, Y = grid(x0, y0, x0 + W, y0 + H)
    nz = value_noise((H, W), 5, seed, 3)
    col = np.array([0.42, 0.37, 0.31]) * (0.85 + 0.25 * nz)[..., None]
    h = 0.3 * nz
    for k in range(40):
        cx, cy = x0 + rng.uniform(0, W), y0 + rng.uniform(0, H)
        r = rng.uniform(3, 5)
        m = np.clip(1 - np.sqrt((X - cx) ** 2 + (Y - cy) ** 2) / r, 0, 1)
        col = col * (1 - 0.3 * m[..., None]) + np.array([0.55, 0.5, 0.4]) * 0.3 * m[..., None]
        h = h + m
    cv.put(x0, y0, np.ones(X.shape, np.float32), np.clip(col, 0, 1).astype(np.float32), h.astype(np.float32))


def sheath_strip(cv, name, seed=5):
    """Bamboo shoot: overlapping sheaths, tan-brown with dark mottling, a fine hair texture, yellow-green at the tip."""
    x0, y0, W, H = region_origin(name)
    X, Y = grid(x0, y0, x0 + W, y0 + H)
    u = (X - x0) / W
    v = 1 - (Y - y0) / H          # 0 = base, 1 = tip
    mott = value_noise((H, W), 5, seed, 3)
    hair = value_noise((H, W * 4), 1.5, seed + 1, 1)
    hair = ndimage.zoom(hair, (1, 0.25), order=1)[:H, :W]
    rows = 7
    ph = v * rows + 0.5 * np.abs(np.sin(u * np.pi * 2))       # chevron sheath edges
    edge = np.clip(1 - np.abs(ph - np.round(ph)) * 9, 0, 1)
    tan = np.array([0.66, 0.54, 0.36])
    dark = np.array([0.33, 0.24, 0.15])
    green = np.array([0.74, 0.74, 0.40])
    spots = np.clip((mott - 0.55) * 4, 0, 1)
    col = tan[None, None] * (0.9 + 0.2 * hair)[..., None]
    col = col * (1 - spots[..., None]) + dark[None, None] * spots[..., None]
    tipm = smooth((v - 0.72) / 0.22)
    col = col * (1 - tipm[..., None]) + green[None, None] * (0.85 + 0.2 * hair)[..., None] * tipm[..., None]
    col = col * (1 - 0.35 * edge)[..., None]
    h = 0.6 * (ph - np.floor(ph)) + 0.15 * hair
    cv.put(x0, y0, np.ones(X.shape, np.float32), np.clip(col, 0, 1).astype(np.float32), h.astype(np.float32))


def discs_culm(cv, name):
    x0, y0, W, H = region_origin(name)
    r = W / 2 * 0.44
    for i in range(2):
        cx, cy = x0 + W / 4 * (2 * i + 1), y0 + W / 4
        X, Y = grid(int(cx - r - 3), int(cy - r - 3), int(cx + r + 4), int(cy + r + 4))
        d = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2) / r
        a = np.clip((1 - d) * r + 0.5, 0, 1)
        rings = 0.5 + 0.5 * np.sin(d * 40)
        if i == 0:      # hollow cut culm: rind, pale wall, dark hollow
            v = np.where(d > 0.86, 0.62, np.where(d > 0.62, 0.9 - 0.06 * rings, 0.2 + 0.1 * d))
        else:           # closed node face
            v = np.where(d > 0.86, 0.62, 0.86 - 0.05 * rings)
        cv.put(int(cx - r - 3), int(cy - r - 3), a.astype(np.float32), np.repeat(v[..., None], 3, 2).astype(np.float32),
               (1 - d).astype(np.float32))


def discs_wood(cv, name):
    x0, y0, W, H = region_origin(name)
    for i in range(2):
        r = W / 2 * 0.44
        cx, cy = x0 + W / 4 * (2 * i + 1), y0 + W / 4
        X, Y = grid(int(cx - r - 3), int(cy - r - 3), int(cx + r + 4), int(cy + r + 4))
        ang = np.arctan2(Y - cy, X - cx)
        d = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2) / r * (1 + 0.05 * np.sin(ang * 5))
        a = np.clip((1 - d) * r + 0.5, 0, 1)
        rings = 0.5 + 0.5 * np.sin(d * 46 + 0.4 * np.sin(ang * 3))
        wood = np.array([0.78, 0.62, 0.43]) * (0.9 + 0.1 * rings)[..., None]
        bark = np.array([0.26, 0.21, 0.18])
        m = smooth((d - 0.82) / 0.08)
        col = wood * (1 - m[..., None]) + bark * m[..., None]
        cv.put(int(cx - r - 3), int(cy - r - 3), a.astype(np.float32), np.clip(col, 0, 1).astype(np.float32),
               (1 - d + 0.1 * rings).astype(np.float32))


def leaf_cluster(cv, name, seed, n, length, width, profile, value=0.82, round_=0.92, serrate=0.0, veins=True,
                 midrib=0.1, bend=0.25, center=(0.5, 0.5), shadow=0.4, crinkle=0.0, radial=True, ring=(0.0, 1.0)):
    """A round puff of leaves radiating from the centre, back leaves first (darker), front ones last."""
    rng = np.random.default_rng(seed)
    x0, y0, W, H = region_origin(name)
    R = min(W, H) / 2 * round_
    cx, cy = x0 + W * center[0], y0 + H * center[1]
    order = sorted(range(n), key=lambda i: rng.random())
    for k, i in enumerate(order):
        frac = k / max(n - 1, 1)
        rr = R * rng.uniform(*ring) * (1 - 0.55 * frac)
        a = rng.uniform(0, 2 * math.pi)
        L = length * rng.uniform(0.8, 1.15)
        bx, by = cx + math.cos(a) * max(rr - L * 0.85, 0), cy + math.sin(a) * max(rr - L * 0.85, 0)
        if not radial:
            a = rng.uniform(0, 2 * math.pi)
        dd = a + rng.uniform(-0.45, 0.45)
        # keep the leaf inside the sprite
        tipx, tipy = bx + math.cos(dd) * L, by + math.sin(dd) * L
        if not (x0 + 4 < tipx < x0 + W - 4 and y0 + 4 < tipy < y0 + H - 4):
            L *= 0.6
        val = value * (0.78 + 0.3 * frac) * rng.uniform(0.92, 1.06)
        leaf(cv, (bx, by), dd, L, width * rng.uniform(0.85, 1.15), value=val, profile=profile,
             bend=rng.uniform(-bend, bend), rng=rng, veins=veins, serrate=serrate, midrib=midrib, shadow=shadow,
             crinkle=crinkle)


def tea_mass(cv, name, seed, n, L, Wd, flat=False):
    rng = np.random.default_rng(seed)
    x0, y0, W, H = region_origin(name)
    cx, cy = x0 + W / 2, y0 + H / 2
    for k in range(n):
        frac = k / max(n - 1, 1)
        if flat:
            px, py = x0 + rng.uniform(0.06, 0.94) * W, y0 + rng.uniform(0.06, 0.94) * H
        else:
            r = math.sqrt(rng.random()) * W * 0.44 * (1 - 0.25 * frac)
            a = rng.uniform(0, 2 * math.pi)
            px, py = cx + math.cos(a) * r, cy + math.sin(a) * r * 0.95
        a = rng.uniform(0, 2 * math.pi) if flat else math.atan2(py - cy, px - cx) + rng.uniform(-0.9, 0.9)
        ln = L * rng.uniform(0.75, 1.2)
        leaf(cv, (px - math.cos(a) * ln * 0.3, py - math.sin(a) * ln * 0.3), a, ln, Wd * rng.uniform(0.85, 1.1),
             value=0.68 * (0.8 + 0.35 * frac) * rng.uniform(0.9, 1.1), profile="ellipse", bend=rng.uniform(-0.2, 0.2),
             rng=rng, veins=True, serrate=0.12, midrib=0.08, shadow=0.45, edge_dark=0.3)


def cabbage_leaf(cv, name, seed, big=True):
    rng = np.random.default_rng(seed)
    x0, y0, W, H = region_origin(name)
    base = (x0 + W / 2, y0 + H * 0.985)
    leaf(cv, base, -math.pi / 2, H * 0.96, W * (0.86 if big else 0.7), value=0.74, profile="obovate", bend=0.0,
         rng=rng, veins=True, midrib=0.0, shadow=0.0, crinkle=0.14 if big else 0.06, edge_dark=0.2)
    # the broad white midrib, widest at the base
    pts = [(base[0], base[1] - 2)] + [(base[0] + rng.uniform(-1.5, 1.5), base[1] - H * f) for f in (0.25, 0.5, 0.75, 0.9)]
    stroke(cv, pts, W * (0.2 if big else 0.1), W * 0.025, value=0.97, shadow=0.12)
    if big:     # pale side veins fanning from the midrib
        for f in np.linspace(0.18, 0.8, 7):
            for sgn in (-1, 1):
                p0 = (base[0], base[1] - H * f)
                a = -math.pi / 2 + sgn * rng.uniform(0.9, 1.15)
                p1 = (p0[0] + math.cos(a) * W * 0.38, p0[1] + math.sin(a) * W * 0.38 - H * 0.04)
                stroke(cv, [p0, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 - 6), p1], 4, 1.2, value=0.86, shadow=0.0)


def withered(cv, name, seed):
    rng = np.random.default_rng(seed)
    x0, y0, W, H = region_origin(name)
    for k in range(7):
        a = rng.uniform(0, 2 * math.pi)
        c = (x0 + W / 2 + rng.uniform(-30, 30), y0 + H / 2 + rng.uniform(-30, 30))
        L = rng.uniform(70, 110)
        leaf(cv, c, a, L, L * rng.uniform(0.25, 0.4), value=0.7 * rng.uniform(0.8, 1.1), profile="ellipse",
             bend=rng.uniform(-0.6, 0.6), rng=rng, veins=True, midrib=0.05, crinkle=0.5, curl=0.5, shadow=0.35,
             edge_dark=0.45)


def rice_tuft(cv, name, seed, n, spread, droop, value=0.8, width=7.0, heights=(0.75, 1.0)):
    rng = np.random.default_rng(seed)
    x0, y0, W, H = region_origin(name)
    bx, by = x0 + W / 2, y0 + H * 0.995
    blades = sorted(range(n), key=lambda i: rng.random())
    for k in blades:
        a0 = -math.pi / 2 + (k / max(n - 1, 1) - 0.5) * spread + rng.uniform(-0.08, 0.08)
        L = H * rng.uniform(*heights)
        pts = []
        a = a0
        p = np.array([bx + rng.uniform(-6, 6), by])
        steps = 10
        for i in range(steps + 1):
            pts.append(p.copy())
            a += (droop * (1 if math.cos(a0) >= 0 else -1) * (i / steps) ** 2) * 0.18
            p = p + np.array([math.cos(a), math.sin(a)]) * L / steps
        pts = np.array(pts)
        pts[:, 0] = np.clip(pts[:, 0], x0 + 4, x0 + W - 4)
        pts[:, 1] = np.clip(pts[:, 1], y0 + 4, y0 + H)
        ws = np.linspace(width, 1.0, len(pts))
        for i in range(len(pts) - 1):
            stroke(cv, [pts[i], pts[i + 1]], ws[i], ws[i + 1], value=value * rng.uniform(0.85, 1.1) * (0.85 + 0.2 * i / steps),
                   shadow=0.18 if i == 0 else 0.0)


def rice_panicle(cv, name, seed, n=3):
    """Ripe rice heads: a stem arches over and the panicle hangs from it as a dense, drooping golden cluster (a
    tapering tassel of short branchlets packed with grains), several heads bunched together."""
    rng = np.random.default_rng(seed)
    x0, y0, W, H = region_origin(name)
    golds = [np.array([0.90, 0.78, 0.42]), np.array([0.84, 0.70, 0.36]), np.array([0.94, 0.84, 0.52])]
    husk = np.array([0.66, 0.54, 0.28])
    for k in range(n):
        # stem from the bottom-left rising to an apex, then the head hanging down and to the right
        base = np.array([x0 + W * rng.uniform(0.12, 0.3), y0 + H * 0.97])
        apex = np.array([x0 + W * rng.uniform(0.38, 0.55), y0 + H * rng.uniform(0.12, 0.22)])
        mid = (base + apex) / 2 + np.array([-W * 0.08, 0])
        stroke(cv, [base, mid, apex], 4.5, 2.5, value=0.6, color=np.array([0.62, 0.6, 0.32]), shadow=0.1)
        # the head's axis: from the apex curving down to the lower right
        L = H * rng.uniform(0.62, 0.78)
        axis = [apex]
        ang = rng.uniform(0.05, 0.35)                     # just right of straight down... measured from +x
        ang = math.pi / 2 - ang
        for i in range(12):
            ang -= 0.035
            axis.append(axis[-1] + np.array([math.cos(ang), math.sin(ang)]) * L / 12)
        axis = np.array(axis)
        stroke(cv, axis, 2.6, 1.2, value=0.6, color=np.array([0.66, 0.6, 0.3]), shadow=0.0)
        gold = golds[k % len(golds)]
        for i in range(1, len(axis)):
            f = i / (len(axis) - 1)
            width = W * 0.11 * (1 - 0.65 * f) + 3      # tassel tapers toward the tip
            tdir = axis[i] - axis[i - 1]
            tdir /= np.linalg.norm(tdir)
            nrm = np.array([-tdir[1], tdir[0]])
            for side in (-1, 1):
                for g in range(int(rng.integers(2, 4))):
                    off = rng.uniform(0.15, 1.0) * width
                    gp = axis[i] + nrm * side * off + tdir * (off * 0.55) + rng.uniform(-2, 2, 2)
                    col = gold * rng.uniform(0.9, 1.08) if rng.random() > 0.15 else husk
                    blob(cv, gp, 6.0, 3.4, col, angle=math.atan2(tdir[1], tdir[0]) + side * 0.35, spec=0.18,
                         shadow=0.3, h=0.8)
            if rng.random() < 0.8:
                blob(cv, axis[i] + rng.uniform(-2, 2, 2), 6.0, 3.4, gold, angle=math.atan2(tdir[1], tdir[0]), spec=0.18,
                     shadow=0.3, h=0.8)


def pepper_cluster(cv, name, seed, n):
    """Compound leaves: a rachis with paired small leaflets, radiating from the centre."""
    rng = np.random.default_rng(seed)
    x0, y0, W, H = region_origin(name)
    cx, cy = x0 + W / 2, y0 + H / 2
    for k in range(n):
        frac = k / max(n - 1, 1)
        a = rng.uniform(0, 2 * math.pi)
        L = W * rng.uniform(0.28, 0.42)
        st = (cx + math.cos(a) * rng.uniform(0, W * 0.08), cy + math.sin(a) * rng.uniform(0, W * 0.08))
        en = (st[0] + math.cos(a) * L, st[1] + math.sin(a) * L)
        stroke(cv, [st, en], 3.5, 1.5, value=0.5, shadow=0.1)
        pairs = int(rng.integers(4, 6))
        val = 0.74 * (0.8 + 0.3 * frac)
        for j in range(pairs):
            f = 0.28 + 0.7 * j / pairs
            p = (st[0] + (en[0] - st[0]) * f, st[1] + (en[1] - st[1]) * f)
            for sgn in (-1, 1):
                aa = a + sgn * rng.uniform(0.75, 1.05)
                ll = W * rng.uniform(0.075, 0.095)
                leaf(cv, p, aa, ll, ll * 0.48, value=val * rng.uniform(0.9, 1.08), profile="ellipse", bend=0.1 * sgn,
                     rng=rng, veins=False, serrate=0.08, midrib=0.08, shadow=0.35)
        leaf(cv, en, a, W * 0.09, W * 0.045, value=val, profile="ellipse", rng=rng, veins=False, midrib=0.08, shadow=0.3)


def pepper_berries(cv, name, seed, clusters):
    rng = np.random.default_rng(seed)
    x0, y0, W, H = region_origin(name)
    red = np.array([0.74, 0.14, 0.08])
    deep = np.array([0.50, 0.09, 0.06])
    for c in range(clusters):
        cx, cy = x0 + W * rng.uniform(0.25, 0.75), y0 + H * rng.uniform(0.25, 0.75)
        nb = int(rng.integers(14, 24))
        for b in range(nb):
            r = math.sqrt(rng.random()) * W * 0.16
            a = rng.uniform(0, 2 * math.pi)
            p = (cx + math.cos(a) * r, cy + math.sin(a) * r)
            stroke(cv, [(cx, cy), p], 1.6, 1.2, value=0.4, color=np.array([0.38, 0.32, 0.22]), shadow=0.0)
        for b in range(nb):
            r = math.sqrt(rng.random()) * W * 0.16
            a = rng.uniform(0, 2 * math.pi)
            p = (cx + math.cos(a) * r, cy + math.sin(a) * r)
            col = red if rng.random() > 0.3 else deep
            rad = rng.uniform(6.0, 8.0)
            blob(cv, p, rad, rad, col * rng.uniform(0.9, 1.1), spec=0.3, shadow=0.35)
            if rng.random() < 0.18:      # split husk showing the black seed
                blob(cv, (p[0] + 1.5, p[1] + 1), rad * 0.42, rad * 0.42, np.array([0.06, 0.05, 0.05]), spec=0.2, shadow=0.0)


def branches(cv, name, seed, color, n=3, thick=10, value=0.45, thorns=False):
    rng = np.random.default_rng(seed)
    x0, y0, W, H = region_origin(name)

    def grow(p, a, ln, w, depth):
        pts = [p]
        for i in range(4):
            a += rng.uniform(-0.25, 0.25)
            q = pts[-1]
            pts.append((q[0] + math.cos(a) * ln / 4, q[1] + math.sin(a) * ln / 4))
        pts = [(min(max(x, x0 + 3), x0 + W - 3), min(max(y, y0 + 3), y0 + H - 3)) for x, y in pts]
        stroke(cv, pts, w, w * 0.45, value=value, color=color, shadow=0.25)
        if thorns:
            for q in pts[1:]:
                for sgn in (-1, 1):
                    ta = a + sgn * 1.3
                    stroke(cv, [q, (q[0] + math.cos(ta) * 7, q[1] + math.sin(ta) * 7)], 3, 0.8, value=value,
                           color=color * 1.2, shadow=0.0)
        if depth > 0:
            for q in pts[1:-1]:
                if rng.random() < 0.7:
                    grow(q, a + rng.choice([-1, 1]) * rng.uniform(0.5, 0.9), ln * 0.55, w * 0.55, depth - 1)
    for k in range(n):
        grow((x0 + W * (0.1 + 0.8 * (k + 0.5) / n), y0 + H * 0.97), -math.pi / 2 + rng.uniform(-0.5, 0.5),
             H * rng.uniform(0.7, 0.9), thick, 2)


def soil_mound(cv, name, seed, dry=False):
    x0, y0, W, H = region_origin(name)
    X, Y = grid(x0, y0, x0 + W, y0 + H)
    cx, cy = x0 + W / 2, y0 + H / 2
    ang = np.arctan2(Y - cy, X - cx)
    nz = value_noise((H, W), 9, seed, 3)
    rough = value_noise((H, W), 3, seed + 1, 2)
    d = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2) / (W * 0.46) * (1 + 0.08 * np.sin(ang * 7 + 1.0) + 0.1 * (nz - 0.5))
    a = np.clip((1 - d) * 18, 0, 1)
    if dry:
        base = np.array([0.52, 0.42, 0.30])
        cracks = np.clip(1 - np.abs(np.sin(ang * 9 + rough * 6)) * 12, 0, 1) * (d < 0.85)
        col = base[None, None] * (0.85 + 0.3 * rough)[..., None] * (1 - 0.4 * cracks)[..., None]
    else:
        base = np.array([0.38, 0.29, 0.20])
        col = base[None, None] * (0.75 + 0.5 * rough)[..., None]
    col = col * (0.75 + 0.3 * (1 - d))[..., None]
    cv.put(x0, y0, a.astype(np.float32), np.clip(col, 0, 1).astype(np.float32), ((1 - d) + 0.3 * rough).astype(np.float32))


def sprig(cv, name, seed):
    rng = np.random.default_rng(seed)
    x0, y0, W, H = region_origin(name)
    b = (x0 + W / 2, y0 + H * 0.98)
    top = (x0 + W / 2 + rng.uniform(-8, 8), y0 + H * 0.35)
    stroke(cv, [b, top], 6, 3, value=0.55)
    for f, sgn in ((0.45, -1), (0.6, 1), (0.8, -1), (0.95, 1)):
        p = (b[0] + (top[0] - b[0]) * f, b[1] + (top[1] - b[1]) * f)
        a = -math.pi / 2 + sgn * rng.uniform(0.6, 1.1)
        leaf(cv, p, a, W * 0.36, W * 0.16, value=0.8, profile="ellipse", bend=0.15 * sgn, rng=rng, midrib=0.1, shadow=0.3)
    leaf(cv, top, -math.pi / 2, W * 0.3, W * 0.13, value=0.86, profile="ellipse", rng=rng, midrib=0.1, shadow=0.3)


# ============================================================================================ detail sprites
def persimmon_fruit(cv, name, seed, n):
    rng = np.random.default_rng(seed)
    x0, y0, W, H = region_origin(name, atlas.DETAIL_REGIONS)
    orange = np.array([0.96, 0.50, 0.10])
    for k in range(n):
        cx = x0 + W * rng.uniform(0.25, 0.75) if n > 1 else x0 + W / 2
        cy = y0 + H * rng.uniform(0.3, 0.7) if n > 1 else y0 + H / 2
        r = W * (0.17 if n > 1 else 0.3) * rng.uniform(0.9, 1.1)
        stroke(cv, [(cx, cy - r * 1.25), (cx + rng.uniform(-3, 3), cy - r * 0.6)], 3.5, 2.5, value=0.3,
               color=np.array([0.28, 0.22, 0.14]), shadow=0.0)
        blob(cv, (cx, cy), r, r * 0.86, orange * rng.uniform(0.92, 1.05), shade=0.4, spec=0.3, shadow=0.35)
        for j in range(4):      # the four-lobed green-brown calyx on top
            a = j * math.pi / 2 + rng.uniform(-0.2, 0.2) + math.pi / 4
            leaf(cv, (cx, cy - r * 0.62), a, r * 0.55, r * 0.42, value=0.42, profile="ovate", rng=rng, veins=False,
                 midrib=0.05, shadow=0.2, color=np.array([0.36, 0.38, 0.18]))


def tea_flush(cv, name, seed, n):
    rng = np.random.default_rng(seed)
    x0, y0, W, H = region_origin(name, atlas.DETAIL_REGIONS)
    fresh = np.array([0.66, 0.86, 0.30])
    for k in range(n):
        p = (x0 + W * rng.uniform(0.12, 0.88), y0 + H * rng.uniform(0.12, 0.88))
        if np.hypot(p[0] - (x0 + W / 2), p[1] - (y0 + H / 2)) > W * 0.42:
            continue
        a = rng.uniform(0, 2 * math.pi)
        for j, sgn in enumerate((-1, 1)):
            leaf(cv, p, a + sgn * 0.5, W * 0.055, W * 0.026, value=0.9, profile="ellipse", rng=rng, veins=False,
                 midrib=0.05, shadow=0.3, color=fresh * rng.uniform(0.9, 1.08))
        leaf(cv, p, a, W * 0.05, W * 0.016, value=0.95, profile="lance", rng=rng, veins=False, midrib=0.0, shadow=0.2,
             color=np.array([0.80, 0.90, 0.48]))


def mushrooms(cv, name, seed, n):
    """Bamboo fungus: a white lace veil hanging from a dark olive cap on a white stem."""
    rng = np.random.default_rng(seed)
    x0, y0, W, H = region_origin(name, atlas.DETAIL_REGIONS)
    for k in range(n):
        cx = x0 + W * (0.22 + 0.56 * k / max(n - 1, 1)) + rng.uniform(-8, 8)
        by = y0 + H * rng.uniform(0.9, 0.97)
        h = H * rng.uniform(0.72, 0.86)
        top = by - h
        X, Y = grid(int(cx - W * 0.2), int(top), int(cx + W * 0.2), int(by))
        # veil: a bell of lace from below the cap down to near the ground
        t = (Y - (top + h * 0.22)) / (h * 0.7)
        half = W * (0.06 + 0.16 * np.clip(t, 0, 1) ** 0.7)
        inside = (np.abs(X - cx) < half) & (t > 0) & (t < 1)
        lace = (np.sin((X - cx) * 0.75) * np.sin(Y * 0.75) > -0.45)
        a = (inside & lace).astype(np.float32)
        a = ndimage.gaussian_filter(a, 0.6)
        col = np.ones(X.shape + (3,), np.float32) * np.array([0.97, 0.96, 0.9])
        col *= (0.8 + 0.2 * (1 - np.abs(X - cx) / np.maximum(half, 1)))[..., None]
        cv.put(int(cx - W * 0.2), int(top), a, col, a * 0.5, shadow=0.2)
        stroke(cv, [(cx, by), (cx, top + h * 0.15)], W * 0.07, W * 0.05, value=0.95, shadow=0.0)
        blob(cv, (cx, top + h * 0.13), W * 0.07, h * 0.15, np.array([0.40, 0.38, 0.22]), spec=0.15, shadow=0.2)


# ============================================================================================ assemble
def paint_main(size=atlas.MAIN):
    cv = Canvas(size)
    CURRENT[:] = [cv]
    culm_strip(cv, "culm", 160, base=0.86, seed=11)
    culm_strip(cv, "culm_thin", 96, base=0.82, seed=12, ridge=0.6)
    bark_strip(cv, "bark", 13)
    thorny_strip(cv, "pepper_stem", 14)
    sheath_strip(cv, "sheath", 15)
    bamboo_spray(cv, "bamboo_spray_a", 21, leaves=(6, 9))
    bamboo_spray(cv, "bamboo_spray_b", 22, leaves=(5, 8), droop=0.35)
    bamboo_spray(cv, "bamboo_spray_c", 23, leaves=(4, 7), scale=1.0)
    bamboo_spray(cv, "bamboo_spray_d", 24, leaves=(4, 6), droop=0.4)
    bamboo_spray(cv, "bamboo_spray_e", 25, leaves=(5, 7), droop=0.15)
    bamboo_dead(cv, "bamboo_dry", 26)
    discs_culm(cv, "culm_discs")
    branches(cv, "twigs_dead", 27, np.array([0.55, 0.5, 0.42]), n=2, thick=7, value=0.55)
    leaf_cluster(cv, "persimmon_leaves_a", 31, 72, 115, 68, "ovate", value=0.82, bend=0.2, midrib=0.1, crinkle=0.0, round_=0.97)
    leaf_cluster(cv, "persimmon_leaves_b", 32, 28, 64, 38, "ovate", value=0.82, bend=0.2, round_=0.97)
    leaf_cluster(cv, "persimmon_leaves_c", 33, 26, 60, 36, "ovate", value=0.8, bend=0.25, round_=0.97)
    branches(cv, "persimmon_branch", 34, np.array([0.24, 0.20, 0.17]), n=3, thick=14, value=0.3)
    discs_wood(cv, "persimmon_discs")
    tea_mass(cv, "tea_leaves", 41, 420, 46, 22)
    tea_mass(cv, "tea_top", 42, 260, 34, 16, flat=True)
    cabbage_leaf(cv, "cabbage_leaf", 51, big=True)
    cabbage_leaf(cv, "cabbage_young", 52, big=False)
    withered(cv, "withered", 53)
    rice_panicle(cv, "rice_panicle_a", 61, 4)
    rice_panicle(cv, "rice_panicle_b", 62, 3)
    rice_tuft(cv, "rice_tuft_a", 63, 26, 1.5, 0.7, width=13.0)
    rice_tuft(cv, "rice_tuft_b", 64, 22, 0.9, 0.25, value=0.84, width=12.0)
    rice_tuft(cv, "rice_tuft_dry", 65, 16, 1.7, 1.4, value=0.8, width=11.0)
    pepper_cluster(cv, "pepper_leaves", 71, 18)
    pepper_berries(cv, "pepper_berries_a", 72, 3)
    pepper_berries(cv, "pepper_berries_b", 73, 2)
    branches(cv, "pepper_branch", 74, np.array([0.42, 0.37, 0.31]), n=3, thick=9, value=0.42, thorns=True)
    soil_mound(cv, "soil_mound", 81)
    soil_mound(cv, "soil_mound_dry", 82, dry=True)
    bamboo_spray_small_low(cv, "shoot_leaves", 83)
    sprig(cv, "seedling_sprig", 84)
    return cv


def bamboo_spray_small_low(cv, name, seed):
    """Low fan of short bamboo leaves for the shoot crop: leaves spread from the bottom centre."""
    rng = np.random.default_rng(seed)
    x0, y0, W, H = region_origin(name)
    b = (x0 + W / 2, y0 + H * 0.96)
    for k in range(9):
        a = -math.pi / 2 + (k / 8 - 0.5) * 2.2 + rng.uniform(-0.1, 0.1)
        L = H * rng.uniform(0.5, 0.8)
        leaf(cv, b, a, L, L * 0.17, value=0.84 * rng.uniform(0.9, 1.08), profile="lance",
             bend=0.25 * (1 if math.cos(a) > 0 else -1), rng=rng, veins=False, midrib=0.1, midrib_w=0.08, shadow=0.35)


def paint_detail(size=atlas.DETAIL):
    cv = Canvas(size)
    CURRENT[:] = [cv]
    persimmon_fruit(cv, "persimmon_fruit_a", 91, 3)
    persimmon_fruit(cv, "persimmon_fruit_b", 92, 2)
    persimmon_fruit(cv, "persimmon_fruit_c", 93, 1)
    tea_flush(cv, "tea_flush", 94, 70)
    tea_flush(cv, "tea_flush_top", 95, 30)
    mushrooms(cv, "mushrooms", 96, 3)
    mushrooms(cv, "mushrooms_b", 97, 2)
    return cv


def normal_from_height(h, strength=3.0):
    h = ndimage.gaussian_filter(h, 0.8)
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * strength
    dr = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * strength
    nx, ny, nz = -dx, dr, np.ones_like(h)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny = nx / ln, ny / ln
    out = np.zeros((h.shape[0], h.shape[1], 4), np.uint8)
    out[..., 0] = 255
    out[..., 1] = np.clip((ny * 0.5 + 0.5) * 255, 0, 255)
    out[..., 2] = out[..., 1]
    out[..., 3] = np.clip((nx * 0.5 + 0.5) * 255, 0, 255)
    return out


def dilate_color(col, a, iters=6):
    """Bleed colour into transparent texels so mips and bilinear filtering do not pull in black fringes."""
    col = col.copy()
    known = a > 0.02
    for _ in range(iters):
        if known.all():
            break
        acc = np.zeros_like(col)
        cnt = np.zeros(a.shape, np.float32)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            sh = np.roll(np.roll(known, dy, 0), dx, 1)
            acc += np.roll(np.roll(col, dy, 0), dx, 1) * sh[..., None]
            cnt += sh
        grow = (~known) & (cnt > 0)
        col[grow] = acc[grow] / cnt[grow][:, None]
        known = known | grow
    col[~known] = np.array([0.5, 0.5, 0.45])
    return col


def save_rgba(path, col, a):
    col = dilate_color(col, a, 12)
    img = np.concatenate([np.clip(col, 0, 1), np.clip(a, 0, 1)[..., None]], 2)
    Image.fromarray((img * 255 + 0.5).astype(np.uint8), "RGBA").save(path)


# ============================================================================================ materials
# VegetationURP floats (graph properties). Sway moves a vertex by uv1.y ** exponent (0 = rooted); flutter shakes the
# parts above the threshold. Vanilla references: Carrot 0.027/0.5/3, Cattail 0.07/1/2 thr 0.6, Birch 0.035/1/2,
# ChestnutTree 0.125/0.5/2, Blueberry 0.018/1/2, Wheat 0.055/0.45/3, CoffeeBush 0.075/0.5/2.
MATERIALS = {
    "PandabornTimberBamboo": dict(sway=(0.11, 0.55, 2.0), flutter=(0.05, 6.0, 4.0, 0.55), wind=0.6, detail="mushrooms"),
    "PandabornShootBamboo": dict(sway=(0.045, 0.8, 2.0), flutter=(0.06, 6.0, 4.0, 0.3), wind=0.55),
    "PandabornCabbage": dict(sway=(0.02, 0.5, 3.0), flutter=(0.025, 4.0, 5.0, 0.5), wind=0.5),
    "PandabornRice": dict(sway=(0.07, 0.9, 2.0), flutter=(0.04, 4.0, 5.0, 0.6), wind=0.55),
    "PandabornTeaBush": dict(sway=(0.015, 1.0, 2.0), flutter=(0.035, 6.0, 5.0, 0.0), wind=0.6, detail="tea"),
    "PandabornSichuanPepper": dict(sway=(0.04, 0.8, 2.0), flutter=(0.05, 6.0, 4.0, 0.3), wind=0.55),
    "PandabornPersimmonTree": dict(sway=(0.10, 0.5, 2.0), flutter=(0.035, 5.0, 3.0, 0.0), wind=0.5, detail="fruit"),
}


def material_floats(m):
    s, f = m["sway"], m["flutter"]
    return {"_SwayStrength": s[0], "_SwaySpeed": s[1], "_SwayExponent": s[2], "_FlutterStrength": f[0],
            "_FlutterSpeed": f[1], "_FlutterExponent": f[2], "_FlutterThreshold": f[3], "_WindModifier": m["wind"],
            "_DetailUseColor": 0.0, "_DetailColorBoost": 0.0, "_EnableDetail": 0.0}


def contact(out, d_png, detail_png):
    D = Image.open(d_png).convert("RGBA")
    bg = Image.new("RGBA", D.size, (255, 0, 255, 255))
    bg.alpha_composite(D)
    De = Image.open(detail_png).convert("RGBA")
    bg2 = Image.new("RGBA", De.size, (255, 0, 255, 255))
    bg2.alpha_composite(De)
    sheet = Image.new("RGB", (1024 + 512, 1024), (30, 30, 30))
    sheet.paste(bg.convert("RGB").resize((1024, 1024)), (0, 0))
    sheet.paste(bg2.convert("RGB").resize((512, 512)), (1024, 0))
    sheet.save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unity")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    main_cv = paint_main()
    det = paint_detail()
    d_png = os.path.join(a.out, "PandabornPlants_D.png")
    n_png = os.path.join(a.out, "PandabornPlants_N.png")
    x_png = os.path.join(a.out, "PandabornPlants_Detail.png")
    save_rgba(d_png, main_cv.col, main_cv.a)
    Image.fromarray(normal_from_height(main_cv.h * 6.0), "RGBA").save(n_png)
    save_rgba(x_png, det.col, det.a)
    contact(os.path.join(a.out, "atlas_preview.png"), d_png, x_png)
    prev = {}
    for name in MATERIALS:
        prev[name] = {"D": d_png, "N": n_png, "Detail": x_png, "detailUseColor": 0}
    json.dump(prev, open(os.path.join(a.out, "plants_preview.json"), "w"), indent=1)
    print("painted ->", a.out)
    if a.unity:
        tdir = os.path.join(a.unity, "Assets", "PandabornPlants", "Textures")
        os.makedirs(tdir, exist_ok=True)
        rel = {}
        for key, src in (("_MainTex", d_png), ("_BumpMap", n_png), ("_DetailMap", x_png)):
            dst = os.path.join(tdir, os.path.basename(src))
            with open(src, "rb") as fi, open(dst, "wb") as fo:
                fo.write(fi.read())
            rel[key] = "Assets/PandabornPlants/Textures/" + os.path.basename(src)
        spec = {"textures": [{"path": rel["_MainTex"], "linear": False, "readable": False, "maxSize": atlas.MAIN},
                             {"path": rel["_BumpMap"], "linear": True, "readable": False, "maxSize": atlas.MAIN},
                             {"path": rel["_DetailMap"], "linear": False, "readable": False, "maxSize": atlas.DETAIL}],
                "materials": []}
        for name, m in MATERIALS.items():
            spec["materials"].append({
                "name": name, "shader": "Assets/TimberbornShaders/VegetationURP.shadergraph",
                "textures": [{"key": k, "value": v} for k, v in rel.items()],
                "floats": [{"key": k, "value": v} for k, v in material_floats(m).items()],
                "colors": [{"key": "_Color", "value": [1.0, 1.0, 1.0, 1.0]},
                           {"key": "_EmissionColor", "value": [0.0, 0.0, 0.0, 1.0]}]})
        with open(os.path.join(a.unity, "Assets", "PandabornPlants", "plants_spec.json"), "w", encoding="utf-8") as fh:
            json.dump(spec, fh, indent=1)
        print("spec ->", a.unity)


if __name__ == "__main__":
    main()
