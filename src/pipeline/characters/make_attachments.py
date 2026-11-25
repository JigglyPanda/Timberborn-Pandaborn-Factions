"""Model and paint the Inkpaws' character attachments: the conical paddy hat and the woven back-basket.

usage: python -I make_attachments.py <unity project dir> [--preview <dir>]

Writes, into <project>/Assets/PandabornAttachments/Source/:
  ConicalHat.mesh.json, BackBasket.mesh.json   vertices / normals / uv / one triangle list per material
  <Material>_D.png, <Material>_N.png            colour (alpha = cut-out) and tangent-space normal maps (OpenGL, y up)
  materials.json                                name, textures, cut-out, smoothness per material
which PandabornAttachmentsBuilder.cs turns into prefabs and the `pandabornattachments_win|_mac` bundles.
With --preview also static .timbermesh copies (one per material) for the offline renderer.

Frames (as the vanilla attachments): the hat in the #Head node's frame, y up; the basket in the #Backpack node's
frame, +y away from the back, -z up the spine. Sizes are for the Inkpaw adult (#Head scaled x1.12 by the Reskin
body); the Ringtail's nodes are 0.82 of that, so the same prefab fits both.
Deterministic (fixed seeds).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from PIL import Image
from scipy import ndimage


# ------------------------------------------------------------------ noise
def vnoise1(x, seed):
    """Periodic-free smooth 1D value noise in [-1, 1]."""
    rng = np.random.default_rng(seed)
    tab = rng.uniform(-1, 1, 4096)
    i = np.floor(x).astype(int); f = x - i
    f = f * f * (3 - 2 * f)
    return tab[i % 4096] * (1 - f) + tab[(i + 1) % 4096] * f


def tile_noise(shape, cells, seed):
    """Tileable 2D value noise in [0,1] (cells per axis)."""
    rng = np.random.default_rng(seed)
    g = rng.uniform(0, 1, (cells[0], cells[1]))
    H, W = shape
    y = np.arange(H) / H * cells[0]; x = np.arange(W) / W * cells[1]
    yi = np.floor(y).astype(int); xi = np.floor(x).astype(int)
    fy = y - yi; fx = x - xi
    fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
    a = g[yi % cells[0]][:, xi % cells[1]]; b = g[yi % cells[0]][:, (xi + 1) % cells[1]]
    c = g[(yi + 1) % cells[0]][:, xi % cells[1]]; d = g[(yi + 1) % cells[0]][:, (xi + 1) % cells[1]]
    top = a * (1 - fx) + b * fx; bot = c * (1 - fx) + d * fx
    return top * (1 - fy[:, None]) + bot * fy[:, None]


def tile_fbm(shape, base, seed, octaves=4):
    out = np.zeros(shape); amp = 0.5; tot = 0
    for o in range(octaves):
        out += amp * tile_noise(shape, (base[0] * 2 ** o, base[1] * 2 ** o), seed + 13 * o)
        tot += amp; amp *= 0.5
    return out / tot


def normal_from_height(h, strength, wrap=True):
    mode = 'wrap' if wrap else 'nearest'
    gx = ndimage.sobel(h, 1, mode=mode) / 8.0
    gy = ndimage.sobel(h, 0, mode=mode) / 8.0
    # image rows grow downwards; v (and tangent-space y) grows upwards
    n = np.dstack([-gx * strength, gy * strength, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return ((n * 0.5 + 0.5) * 255).round().astype(np.uint8)


def save_rgba(path, rgb, a=None):
    rgb = (np.clip(rgb, 0, 1) * 255).round().astype(np.uint8)
    if a is None:
        Image.fromarray(rgb, 'RGB').save(path)
    else:
        Image.fromarray(np.dstack([rgb, (np.clip(a, 0, 1) * 255).round().astype(np.uint8)]), 'RGBA').save(path)


# ------------------------------------------------------------------ textures
def paint_hat_leaf(S=1024):
    """Palm-leaf strips of a nón lá. u (columns): around the hat, tiled (the cone maps 8 repeats). v (rows up): apex
    (v=0) to brim (v=0.86); v 0.88..1.0 is the ragged fibre fringe (alpha cut-out)."""
    H = W = S
    v = 1 - (np.arange(H) + 0.5) / H              # per row
    u = (np.arange(W) + 0.5) / W
    U, Vv = np.meshgrid(u, v)
    strips = 7                                     # leaf strips per tile
    su = U * strips
    sid = np.floor(su).astype(int)
    fu = su - sid
    rng = np.random.default_rng(7)
    tone = rng.uniform(-1, 1, strips)[sid % strips]
    # pale straw with per-strip tone, darker overlaps at strip edges, fine fibres along the strip (radial)
    fib = tile_fbm((H, W), (2, 96), 11, 3)
    edge = np.exp(-((fu - 0.0) / 0.06) ** 2) + np.exp(-((fu - 1.0) / 0.06) ** 2)
    base = np.array([0.86, 0.78, 0.56])
    col = base[None, None] * (1 + 0.06 * tone[..., None]) * (0.90 + 0.14 * fib[..., None])
    col *= (1 - 0.22 * edge[..., None])
    # weathering: warmer/darker towards the brim, a few water stains
    stain = tile_fbm((H, W), (3, 4), 23, 4)
    col *= (1 - 0.10 * np.clip(Vv / 0.86, 0, 1) ** 2)[..., None]
    col = col * (1 - 0.12 * np.clip((stain - 0.55) * 4, 0, 1))[..., None] + np.array([0.05, 0.02, -0.02]) * np.clip((stain - 0.55) * 4, 0, 1)[..., None]
    # concentric binding threads (the hoops under the leaves show as stitched rings)
    height = 0.5 * fib - 0.6 * edge
    for vr in (0.20, 0.34, 0.47, 0.59, 0.70, 0.79, 0.855):
        d = np.abs(Vv - vr)
        ring = np.exp(-(d / 0.0045) ** 2)
        stitch = 0.5 + 0.5 * np.cos(2 * np.pi * U * strips * 3)   # stitches over each strip
        col = col * (1 - 0.30 * ring[..., None]) + np.array([0.55, 0.47, 0.33]) * 0.30 * ring[..., None]
        col = col * (1 - 0.25 * (ring * stitch)[..., None])
        height = height + 1.2 * ring * (0.6 + 0.4 * stitch)
    # rim band: the leaf folded over the outer hoop
    rim = np.clip(1 - np.abs(Vv - 0.85) / 0.012, 0, 1)
    col = col * (1 - 0.15 * rim[..., None])
    height = height + 0.8 * rim
    # fringe: frayed leaf ends with varying length, alpha cut-out
    fr = Vv > 0.865
    ln = 0.88 + 0.10 * tile_fbm((1, W), (1, 48), 31, 3)[0]       # fibre end per column
    ln = ln + 0.03 * np.sin(2 * np.pi * u * strips * 5) * tile_fbm((1, W), (1, 20), 37, 2)[0]
    fine = tile_fbm((H, W), (1, 256), 41, 2)
    alpha = np.ones((H, W))
    alpha[fr] = (Vv[fr] < (ln[None, :].repeat(H, 0)[fr] - 0.02 * fine[fr])).astype(float)
    col[fr] *= (0.92 + 0.08 * fine[fr])[..., None]
    nrm = normal_from_height(ndimage.gaussian_filter(height, 0.8, mode='wrap'), 2.5)
    return col, alpha, nrm


def paint_weave(S=1024, base=(0.62, 0.47, 0.27), seed=3):
    """Over-under basket weave (tileable): vertical stakes, horizontal split-bamboo weavers. u around, v up."""
    H = W = S
    y = (np.arange(H) + 0.5) / H; x = (np.arange(W) + 0.5) / W
    X, Y = np.meshgrid(x, y)
    ns, nw = 8, 10                                   # stakes across, weavers up, per tile
    sx = X * ns; wy = Y * nw
    si = np.floor(sx).astype(int); wi = np.floor(wy).astype(int)
    fx = sx - si; fy = wy - wi
    over = ((si + wi) % 2 == 0)                       # weaver over the stake here
    # weaver profile across its width, stake profile across its width
    wprof = np.sin(np.pi * np.clip((fy - 0.06) / 0.88, 0, 1))
    sprof = np.sin(np.pi * np.clip((fx - 0.30) / 0.40, 0, 1))
    # the weaver dips where it passes under a stake, rises over it
    bend = np.where(over, 1.0, 0.35) * (0.6 + 0.4 * np.cos(np.pi * (fx - 0.5)))
    hw = wprof * bend
    hs = sprof * np.where(over, 0.25, 1.0)
    h = np.maximum(hw, hs)
    is_stake = hs > hw
    fib = tile_fbm((H, W), (64, 4), seed + 1, 3)
    fib2 = tile_fbm((H, W), (4, 64), seed + 2, 3)
    rng = np.random.default_rng(seed)
    wt = rng.uniform(-1, 1, nw)[wi % nw]
    stt = rng.uniform(-1, 1, ns)[si % ns]
    b = np.array(base)
    col = np.where(is_stake[..., None], b * 0.82 * (1 + 0.08 * stt[..., None]) * (0.9 + 0.2 * fib2[..., None]),
                   b * (1 + 0.10 * wt[..., None]) * (0.88 + 0.22 * fib[..., None]))
    gap = h < 0.12
    col = col * (0.35 + 0.65 * np.clip(h / 0.25, 0, 1))[..., None]
    col[gap] = np.array([0.10, 0.07, 0.04])
    ao = ndimage.gaussian_filter(h, 3, mode='wrap')
    col *= (0.75 + 0.25 * np.clip(ao * 1.6, 0, 1))[..., None]
    grime = tile_fbm((H, W), (3, 3), seed + 9, 4)
    col *= (1 - 0.12 * np.clip((grime - 0.5) * 3, 0, 1))[..., None]
    nrm = normal_from_height(ndimage.gaussian_filter(h + 0.15 * (fib - 0.5), 1.0, mode='wrap'), 6.0)
    return col, None, nrm


def paint_strap(S=512):
    """Plaited hemp cord / cloth strap (tileable along v): u across the strap, v along it."""
    H = W = S
    y = (np.arange(H) + 0.5) / H; x = (np.arange(W) + 0.5) / W
    X, Y = np.meshgrid(x, y)
    n = 12
    ph = (Y * n + np.where(X < 0.5, 0, 0.5)) % 1.0
    lean = np.where(X < 0.5, X * 2, (X - 0.5) * 2)
    h = np.sin(np.pi * np.clip(ph + 0.25 * lean, 0, 1) % 1.0)
    edge = np.minimum(X, 1 - X)
    h *= np.clip(edge / 0.08, 0, 1)
    fib = tile_fbm((H, W), (8, 64), 51, 3)
    col = np.array([0.55, 0.42, 0.26]) * (0.7 + 0.3 * h[..., None]) * (0.9 + 0.2 * fib[..., None])
    nrm = normal_from_height(ndimage.gaussian_filter(h, 1.0, mode='wrap'), 4.0)
    return col, None, nrm


def paint_sky_lantern(S=256):
    """The rising paper sky lantern (kongming lantern) for the Festival's LanternRise particle: a red-orange paper bag,
    wider at the top and tapering to its open mouth, lit from the flame in the mouth (brightest yellow-orange low in the
    middle, the look sheet's LanternPaperRed glow (240,70,22) at the shoulders, deep red at the silhouette), four faint
    bamboo struts, a dark hoop at the mouth, and a thin warm halo. No writing. Returns (rgb, alpha, emission rgb), y up.

    Drawn to read as a lantern from the normal game camera on a 0.7 to 0.9 m quad (MakeLanternRise): the paper fills
    74 % of the quad's height and up to 54 % of its width (it was 60 % and 43 %, mostly halo), the silhouette is crisp
    and darker than the lit middle, and the halo is thin so that a far lantern is a small lantern, not a soft dot."""
    H = W = S
    y = 1 - (np.arange(H) + 0.5) / H
    x = (np.arange(W) + 0.5) / W
    X, Y = np.meshgrid(x, y)
    cx = 0.5
    yb, yt = 0.13, 0.87                                   # mouth, crown
    t = np.clip((Y - yb) / (yt - yb), 0, 1)
    half = 0.185 + 0.085 * np.sin(np.pi * 0.5 * t) ** 0.8  # tapers to the mouth, widest below the crown
    # rounded crown: the half-width closes over the top 22 %
    crown = np.clip((t - 0.78) / 0.22, 0, 1)
    half = half * np.sqrt(np.clip(1 - crown ** 2, 0, 1))
    u = (X - cx) / np.maximum(half, 1e-4)                  # -1..1 across the body
    inside = (np.abs(u) <= 1) & (Y >= yb) & (Y <= yt)
    edge_d = np.minimum((1 - np.abs(u)) * half / 0.20, np.minimum((Y - yb) / 0.02, 1.0))
    body_a = np.clip(edge_d / 0.05, 0, 1) * inside         # a crisp edge (about 2.5 px at 256)
    body_a = ndimage.gaussian_filter(body_a, 0.7)
    # glow: from the flame at the mouth up through the paper
    fx, fy = cx, yb + 0.09
    d_flame = np.sqrt(((X - fx) / 0.21) ** 2 + ((Y - fy) / 0.34) ** 2)
    glow = 0.85 * np.exp(-d_flame ** 2 * 1.7)
    across = np.sqrt(np.clip(1 - u ** 2, 0, 1))            # rounder in the middle, darker at the silhouette
    red = np.array([240, 70, 22]) / 255
    deep = np.array([128, 22, 8]) / 255
    core = np.array([255, 200, 108]) / 255
    col = deep[None, None] * (1 - across[..., None]) + red[None, None] * across[..., None]
    col = col * (1 - glow[..., None]) + core[None, None] * glow[..., None]
    # the crown is the farthest from the flame: a shade darker, so the bag reads as a volume
    col = col * (1 - 0.22 * np.clip((t - 0.62) / 0.38, 0, 1) ** 1.5)[..., None]
    # paper texture and four bamboo struts (cylinder projection), the hoop at the mouth
    fib = tile_fbm((H, W), (6, 6), 71, 3)
    col = col * (0.92 + 0.12 * fib[..., None])
    for deg in (-60.0, -20.0, 20.0, 60.0):              # four struts on the visible half of the round bag
        pos = np.sin(np.radians(deg))
        strut = np.exp(-((u - pos) / 0.04) ** 2)
        col = col * (1 - 0.20 * strut[..., None])
    hoop = np.exp(-((Y - yb - 0.014) / 0.012) ** 2) * (np.abs(u) <= 1.05)
    col = col * (1 - 0.60 * hoop[..., None])
    # the flame itself, seen through the mouth: a small bright yellow-white bead just inside
    flame = np.exp(-(((X - cx) / 0.042) ** 2 + ((Y - yb - 0.05) / 0.06) ** 2))
    col = col * (1 - flame[..., None]) + np.array([1.0, 0.92, 0.70]) * flame[..., None]
    # halo: a thin warm glow around the paper, low alpha
    dist_body = ndimage.distance_transform_edt(body_a < 0.5) / S
    halo = np.exp(-(dist_body / 0.045) ** 2) * (body_a < 0.5)
    alpha = np.clip(np.maximum(body_a * 0.97, halo * 0.24), 0, 1)
    hal_col = np.array([255, 120, 40]) / 255
    rgb = col * body_a[..., None] + hal_col[None, None] * (1 - body_a[..., None])
    emis = rgb * np.maximum(body_a, halo * 0.8)[..., None] * (0.75 + 0.45 * glow[..., None])
    # keep the bottom row and borders fully transparent (clamped sampling)
    alpha[:2] = alpha[-2:] = alpha[:, :2] = alpha[:, -2:] = 0
    return np.clip(rgb, 0, 1), alpha, np.clip(emis, 0, 1)


# ------------------------------------------------------------------ geometry
class Mesh:
    def __init__(self):
        self.P, self.N, self.UV = [], [], []
        self.subs = {}

    def add(self, mat, P, N, UV, tri):
        base = sum(len(p) for p in self.P)
        P = np.asarray(P, float); N = np.asarray(N, float)
        N = N / np.linalg.norm(N, axis=1, keepdims=True).clip(1e-9)
        tri = np.asarray(tri, int)
        # wind every triangle so its face normal agrees with the vertex normals (outward)
        fn = np.cross(P[tri[:, 1]] - P[tri[:, 0]], P[tri[:, 2]] - P[tri[:, 0]])
        flip = np.sum(fn * (N[tri[:, 0]] + N[tri[:, 1]] + N[tri[:, 2]]), 1) < 0
        tri[flip] = tri[flip][:, [0, 2, 1]]
        self.P.append(P); self.N.append(N); self.UV.append(np.asarray(UV, float))
        self.subs.setdefault(mat, []).append(tri + base)

    def grid(self, mat, F, NF, nu, nv, uvf, both=False, offset=0.0):
        """Surface from F(u,v) on an (nu+1)x(nv+1) grid; NF gives the normal; uvf the texture coordinates."""
        us = np.linspace(0, 1, nu + 1); vs = np.linspace(0, 1, nv + 1)
        Ug, Vg = np.meshgrid(us, vs)
        P = F(Ug, Vg).reshape(-1, 3); N = NF(Ug, Vg).reshape(-1, 3)
        UV = uvf(Ug, Vg).reshape(-1, 2)
        tri = []
        for j in range(nv):
            for i in range(nu):
                a = j * (nu + 1) + i; b = a + 1; c = a + nu + 1; d = c + 1
                tri += [[a, b, d], [a, d, c]]
        self.add(mat, P + offset * N, N, UV, tri)
        if both:
            self.add(mat, P - 0.0025 * N, -N, UV, tri)

    def json(self, name):
        mats = list(self.subs)
        return dict(name=name, vertices=np.vstack(self.P).round(5).ravel().tolist(),
                    normals=np.vstack(self.N).round(4).ravel().tolist(), uv=np.vstack(self.UV).round(5).ravel().tolist(),
                    materials=mats, submeshes=[np.vstack(self.subs[m]).ravel().tolist() for m in mats])


def normals_numeric(F, eps=1e-4):
    def NF(U, V):
        du = (F(U + eps, V) - F(U - eps, V)); dv = (F(U, V + eps) - F(U, V - eps))
        n = np.cross(dv, du)
        return n / np.linalg.norm(n, axis=-1, keepdims=True).clip(1e-12)
    return NF


def conical_hat():
    """Nón lá: a shallow cone (apex 7.5 cm over a 15.5 cm brim radius), slightly convex, the brim ragged and gently
    wavy, a bamboo hoop under the rim, a head ring inside, and a fringe of frayed leaf ends."""
    m = Mesh()
    R, Hh, y0 = 0.150, 0.080, -0.046
    rough = lambda th: 1 + 0.022 * vnoise1(th / (2 * np.pi) * 19, 5)
    droop = lambda th: 0.004 * vnoise1(th / (2 * np.pi) * 7, 8)

    def F(U, V):
        V = np.clip(V, 0, 1)
        th = 2 * np.pi * U
        r = R * V * np.where(V > 0.9, rough(th) ** ((V - 0.9) / 0.1), 1.0)
        prof = 1 - V ** 0.92 + 0.05 * np.sin(np.pi * V)          # slightly convex shell
        y = y0 + Hh * prof - droop(th) * V ** 4
        return np.stack([r * np.cos(th), y, r * np.sin(th)], -1)
    uv = lambda U, V: np.stack([U * 8, V * 0.855], -1)
    m.grid('PandabornHatLeaf', F, normals_numeric(F), 56, 9, uv, both=True)

    # fringe: frayed ends just past the brim, drooping slightly (cut-out texture rows 0.865..1.0)
    def Ff(U, V):
        th = 2 * np.pi * U
        r = R * rough(th) * (1 + 0.06 * V)
        y = y0 + Hh * (-0.0) - droop(th) - 0.006 * V
        return np.stack([r * np.cos(th), y, r * np.sin(th)], -1)
    m.grid('PandabornHatLeaf', Ff, lambda U, V: np.stack([np.cos(2 * np.pi * U) * 0.25, np.ones_like(U), np.sin(2 * np.pi * U) * 0.25], -1),
           56, 1, lambda U, V: np.stack([U * 8, 0.862 + 0.135 * V], -1), both=True)

    # hoop under the rim and a head ring (bamboo/cord)
    def torus(Rr, r, yc, nu=40, nv=5, rep=10):
        def Ft(U, V):
            th = 2 * np.pi * U; ph = 2 * np.pi * V
            return np.stack([(Rr + r * np.cos(ph)) * np.cos(th), yc + r * np.sin(ph), (Rr + r * np.cos(ph)) * np.sin(th)], -1)

        def Nt(U, V):
            th = 2 * np.pi * U; ph = 2 * np.pi * V
            return np.stack([np.cos(ph) * np.cos(th), np.sin(ph), np.cos(ph) * np.sin(th)], -1)
        m.grid('PandabornCord', Ft, Nt, nu, nv, lambda U, V: np.stack([V, U * rep], -1))
    torus(R * 0.965, 0.0045, y0 + 0.0012 - 0.004, rep=24)
    torus(0.058, 0.0055, y0 + Hh * (1 - (0.058 / R) ** 0.92 + 0.05 * np.sin(np.pi * 0.058 / R)) - 0.012, rep=8)
    # a small knot at the apex
    def Fk(U, V):
        th = 2 * np.pi * U; ph = np.pi * V * 0.5
        return np.stack([0.008 * np.cos(ph) * np.cos(th), y0 + Hh + 0.04 * 0.0 + 0.008 * np.sin(ph) - 0.002, 0.008 * np.cos(ph) * np.sin(th)], -1)
    m.grid('PandabornCord', Fk, lambda U, V: np.stack([np.cos(np.pi * V * 0.5) * np.cos(2 * np.pi * U), np.sin(np.pi * V * 0.5),
                                                      np.cos(np.pi * V * 0.5) * np.sin(2 * np.pi * U)], -1),
           12, 3, lambda U, V: np.stack([V, U * 2], -1))
    return m


def back_basket():
    """Bei lou: a tapered, rounded-square woven basket open at the top, a rolled rim, a woven base, two shoulder
    straps and a waist strap leading into the body. #Backpack frame: +y away from the back, -z up the spine."""
    m = Mesh()
    zb, zt, dist = 0.105, -0.118, 0.094            # bottom, top (up = -z), centre distance from the back
    rb, rt = (0.056, 0.046), (0.080, 0.064)          # half sizes (x across the back, y away) at bottom and top
    n = 3.2                                          # superellipse exponent (rounded square)

    def ring_xy(th, ax, ay):
        c, s = np.cos(th), np.sin(th)
        return ax * np.sign(c) * np.abs(c) ** (2 / n), ay * np.sign(s) * np.abs(s) ** (2 / n)

    def Fw(U, V, inset=0.0):
        th = 2 * np.pi * U
        ax = rb[0] + (rt[0] - rb[0]) * V - inset; ay = rb[1] + (rt[1] - rb[1]) * V - inset
        bulge = 1 + 0.06 * np.sin(np.pi * V)
        x, y = ring_xy(th, ax * bulge, ay * bulge)
        z = zb + (zt - zb) * V
        return np.stack([x, dist + y, z], -1)
    per = 2 * (rt[0] + rt[1]) * 2.2                  # approx. perimeter (m) for an even weave scale
    m.grid('PandabornWeave', Fw, normals_numeric(Fw), 36, 6, lambda U, V: np.stack([U * per / 0.08, V * (zb - zt) / 0.08], -1))
    Fi = lambda U, V: Fw(U, V, inset=0.004)
    m.grid('PandabornWeave', Fi, lambda U, V: -normals_numeric(Fi)(U, V), 36, 6,
           lambda U, V: np.stack([U * per / 0.08, V * (zb - zt) / 0.08], -1))
    # base: a woven disc closing the bottom (both faces)
    def Fb(U, V):
        th = 2 * np.pi * U
        x, y = ring_xy(th, rb[0] * V, rb[1] * V)
        return np.stack([x, dist + y, np.full_like(U, zb)], -1)
    m.grid('PandabornWeave', Fb, lambda U, V: np.stack([np.zeros_like(U), np.zeros_like(U), np.ones_like(U)], -1), 18, 2,
           lambda U, V: np.stack([0.5 + 1.2 * V * np.cos(2 * np.pi * U), 0.5 + 1.2 * V * np.sin(2 * np.pi * U)], -1))
    m.grid('PandabornWeave', lambda U, V: Fb(U, V) - np.array([0, 0, 0.004]),
           lambda U, V: np.stack([np.zeros_like(U), np.zeros_like(U), -np.ones_like(U)], -1), 18, 2,
           lambda U, V: np.stack([0.5 + 1.2 * V * np.cos(2 * np.pi * U), 0.5 + 1.2 * V * np.sin(2 * np.pi * U)], -1))
    # rolled rim (a tube following the top edge)
    def Fr(U, V):
        th = 2 * np.pi * U; ph = 2 * np.pi * V
        b = 1 + 0.06 * np.sin(np.pi * 1.0)
        x, y = ring_xy(th, rt[0] * b, rt[1] * b)
        c = np.stack([x, dist + y, np.full_like(U, zt)], -1)
        out = np.stack([np.cos(th), np.sin(th), np.zeros_like(U)], -1)
        up = np.array([0, 0, -1.0])
        return c + 0.0075 * (np.cos(ph)[..., None] * out + np.sin(ph)[..., None] * up)

    def Nr(U, V):
        th = 2 * np.pi * U; ph = 2 * np.pi * V
        out = np.stack([np.cos(th), np.sin(th), np.zeros_like(U)], -1)
        return np.cos(ph)[..., None] * out + np.sin(ph)[..., None] * np.array([0, 0, -1.0])
    m.grid('PandabornCord', Fr, Nr, 36, 5, lambda U, V: np.stack([V, U * 30], -1))
    # four corner ribs (thicker stakes) for structure
    for k in range(4):
        th0 = (k + 0.5) * np.pi / 2

        def Fs(U, V, th0=th0):
            ph = 2 * np.pi * U
            p = Fw(np.full_like(V, th0 / (2 * np.pi)), V)
            c, s = np.cos(th0), np.sin(th0)
            out = np.stack([np.full_like(U, c), np.full_like(U, s), np.zeros_like(U)], -1)
            tan = np.stack([np.full_like(U, -s), np.full_like(U, c), np.zeros_like(U)], -1)
            return p + 0.0045 * (np.cos(ph)[..., None] * out + np.sin(ph)[..., None] * tan) + 0.002 * out

        def Ns(U, V, th0=th0):
            ph = 2 * np.pi * U
            c, s = np.cos(th0), np.sin(th0)
            return np.stack([np.cos(ph) * c - np.sin(ph) * s, np.cos(ph) * s + np.sin(ph) * c, np.zeros_like(U)], -1)
        m.grid('PandabornCord', Fs, Ns, 5, 4, lambda U, V: np.stack([U, V * 6], -1))
    # straps: flat bands from the basket's back over the shoulders and under the arms, into the body
    def strap(path, width, rep):
        path = np.asarray(path, float)
        t = np.linspace(0, 1, 12)
        # Catmull-Rom through the path points
        k = len(path) - 1
        seg = np.minimum((t * k).astype(int), k - 1); f = t * k - seg
        P0 = path[np.maximum(seg - 1, 0)]; P1 = path[seg]; P2 = path[seg + 1]; P3 = path[np.minimum(seg + 2, k)]
        f = f[:, None]
        C = 0.5 * ((2 * P1) + (-P0 + P2) * f + (2 * P0 - 5 * P1 + 4 * P2 - P3) * f ** 2 + (-P0 + 3 * P1 - 3 * P2 + P3) * f ** 3)
        T = np.gradient(C, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True)
        side = np.array([1.0, 0, 0])
        Nn = np.cross(T, side); Nn /= np.linalg.norm(Nn, axis=1, keepdims=True)
        Nn *= np.sign(Nn[:, 1:2] + 1e-9)                           # face away from the body (+y)
        Sd = np.cross(Nn, T)
        P, N, UV, tri = [], [], [], []
        L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]
        for j in range(len(C)):
            for s in (-1, 1):
                P.append(C[j] + s * width * 0.5 * Sd[j]); N.append(Nn[j]); UV.append(((s + 1) / 2, L[j] / 0.05 * rep))
        for j in range(len(C) - 1):
            a = 2 * j
            tri += [[a, a + 1, a + 3], [a, a + 3, a + 2]]
        P = np.array(P); N = np.array(N)
        m.add('PandabornStrap', P, N, UV, tri)
        m.add('PandabornStrap', P - 0.002 * N, -N, UV, tri)
    for sx in (-1, 1):
        # top: from the back of the rim, up over the shoulder and down the front into the chest
        strap([(sx * 0.045, dist - rt[1] + 0.002, zt + 0.02), (sx * 0.050, 0.006, -0.175), (sx * 0.055, -0.040, -0.205),
               (sx * 0.060, -0.110, -0.195), (sx * 0.062, -0.150, -0.155)], 0.016, 1)
        # bottom: from the lower back of the basket forward under the arm into the side
        strap([(sx * 0.040, dist - rb[1] + 0.002, zb - 0.025), (sx * 0.075, -0.010, zb - 0.030), (sx * 0.095, -0.060, zb - 0.040),
               (sx * 0.090, -0.120, zb - 0.050)], 0.014, 1)
    return m


# ------------------------------------------------------------------ preview (.timbermesh, one node per material)
def write_preview(mesh, path_base, textures):
    from tmesh_static import StaticNode, write_model
    out = {}
    for mat, tris in mesh.subs.items():
        P = np.vstack(mesh.P); N = np.vstack(mesh.N); UV = np.vstack(mesh.UV)
        T = np.vstack(tris)
        used = np.unique(T)
        remap = -np.ones(len(P), int); remap[used] = np.arange(len(used))
        node = StaticNode(name=mat, parent=0, positions=P[used].astype(np.float32), normals=N[used].astype(np.float32),
                          uv0=UV[used].astype(np.float32), meshes=[(mat, remap[T])])
        root = StaticNode(name='root')
        p = f'{path_base}.{mat}.timbermesh'
        write_model(p, [root, node])
        out[mat] = (p, textures.get(mat))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('project')
    ap.add_argument('--preview', default='')
    a = ap.parse_args()
    src = os.path.join(a.project, 'Assets', 'PandabornAttachments', 'Source')
    os.makedirs(src, exist_ok=True)
    mats = []
    tex = {}

    def put(name, col, alpha, nrm, smooth, cutout):
        d = os.path.join(src, name + '_D.png'); nn = os.path.join(src, name + '_N.png')
        save_rgba(d, col, alpha)
        Image.fromarray(nrm, 'RGB').save(nn)
        mats.append(dict(name=name, diffuse=name + '_D.png', normal=name + '_N.png', cutout=cutout, smoothness=smooth))
        tex[name] = d
    c, al, nr = paint_hat_leaf(); put('PandabornHatLeaf', c, al, nr, 0.18, True)
    c, al, nr = paint_weave(); put('PandabornWeave', c, al, nr, 0.12, False)
    c, al, nr = paint_strap(); put('PandabornStrap', c, al, nr, 0.10, False)
    c, al, nr = paint_weave(512, base=(0.56, 0.44, 0.28), seed=17); put('PandabornCord', c, al, nr, 0.10, False)
    with open(os.path.join(src, 'materials.json'), 'w') as f:
        json.dump(mats, f, indent=1)
    # the Festival's rising sky lantern (particle sprite + emission map; PandabornAttachmentsBuilder.MakeLanternRise)
    rgb, al, em = paint_sky_lantern()
    save_rgba(os.path.join(src, 'PandabornSkyLantern_D.png'), rgb, al)
    save_rgba(os.path.join(src, 'PandabornSkyLantern_E.png'), em)
    tex['PandabornSkyLantern'] = os.path.join(src, 'PandabornSkyLantern_D.png')
    meshes = dict(ConicalHat=conical_hat(), BackBasket=back_basket())
    for name, m in meshes.items():
        with open(os.path.join(src, name + '.mesh.json'), 'w') as f:
            json.dump(m.json(name), f)
        nv = sum(len(p) for p in m.P); nt = sum(len(t) for ts in m.subs.values() for t in ts)
        print(f'{name}: {nv} vertices, {nt} triangles, materials {list(m.subs)}')
    if a.preview:
        os.makedirs(a.preview, exist_ok=True)
        idx = {}
        for name, m in meshes.items():
            idx[name] = write_preview(m, os.path.join(a.preview, name), tex)
        with open(os.path.join(a.preview, 'preview_index.json'), 'w') as f:
            json.dump(idx, f, indent=1)
        print('preview meshes in', a.preview)


if __name__ == '__main__':
    main()
