"""Paint worker-outfit overlays (WorkerOutfitSpec DiffuseTexture/NormalTexture) for a body in the beaver UV layout.

usage: python -I paint_outfits.py MODEL.paint.npz OUT_DIR [--only NightBuilder,...] [--prefix Ringtail] [--size 2048]

The game draws `_WorkerOutfitDiffuse` over the coat by its alpha and blends `_WorkerOutfitNormal` (sampled as a normal
map) the same way. Shapes are evaluated on the body's rest surface (rasterised into UV space, as the coats are), so
they sit on the red panda's own shoulders, waist and head. Normal maps use the vanilla packing (R=255, G=B=y, A=x) and
need `{"isNormalMap": true}` next to them (linear). No writing or symbols: cloth, rope, leather and plain trims.

Outfits (Ringtail worker type; design: DESIGN.md art direction and Pillar 4):
  NightBuilder   indigo cloth head-wrap, leather tool belt
  NightCourier   woven straps for a back-basket (two shoulder straps, chest strap, belt)
  NightForager   green head-wrap, satchel strap across the body, waist pouch band
  Stargazer      night-blue shawl over shoulders and back with a pale trim
  Opera          crimson sash, gold collar, black silk belt
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
from scipy import ndimage  # noqa: E402

import raster  # noqa: E402
from paint import fbm, smoothstep  # noqa: E402


class Body:
    def __init__(self, npz, size, scale=1.0):
        d = np.load(npz)
        attrs = dict(P=d['P'], N=d['N'], head=d['head'], tail=d['tail'], darm=np.minimum(d['darm'], 1.0),
                     dsole=np.minimum(d['dsole'], 1.0), ear_rho=d['ear_rho'] if 'ear_rho' in d else np.ones(len(d['P'])),
                     teeth=d['teeth'])
        r = raster.rasterize(d['uv0'], d['tri'], attrs, size)
        self.mask = r['mask']
        self.r = {k: raster.pad(v, self.mask)[..., :] for k, v in r.items() if k not in ('mask', 'tri')}
        N = self.r['N']
        self.r['N'] = N / np.linalg.norm(N, axis=2, keepdims=True).clip(1e-9)
        self.r['P'] = self.r['P'] / scale
        self.S = size

    def f(self, k):
        v = self.r[k]
        return v[..., 0] if v.shape[-1] == 1 else v


def soft(d, w, aa=0.002):
    """1 inside |d| < w/2 with a soft edge."""
    return 1 - smoothstep(w / 2 - aa, w / 2 + aa, np.abs(d))


def masks(b, name):
    P, N = b.f('P'), b.f('N')
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    head, tail, darm, er = b.f('head'), b.f('tail'), b.f('darm'), b.f('ear_rho')
    torso = (head < 0.4) * (1 - tail) * smoothstep(0.015, 0.035, darm) * (1 - b.f('teeth'))
    torso_arms = (head < 0.4) * (1 - tail)
    on_head = (head > 0.5) * (er > 0.99)
    out = []   # list of (mask, colour, kind)

    def headwrap(col, yc=0.512, tilt=0.06, w=0.024):
        yy = yc - tilt * smoothstep(0.08, -0.08, z)   # lower at the back, where it is tied
        m = soft(y - yy, w) * on_head
        knot = (1 - smoothstep(0.012, 0.02, np.sqrt(x ** 2 + ((y - yc + tilt) * 1.2) ** 2 + 0 * z))) * (z < -0.03) * on_head
        out.append((np.maximum(m, knot), col, 'cloth'))

    def belt(col, yc=0.175, w=0.03, kind='leather'):
        out.append((soft(y - yc - 0.01 * smoothstep(0.0, 0.1, z), w) * torso, col, kind))

    def strap(col, a, b_, w=0.018, kind='rope', front=None):
        """A strap along the line a->b in the x-y plane, on the front (front=True), back (False) or both (None)."""
        a = np.array(a); b_ = np.array(b_)
        ab = b_ - a
        t = np.clip(((x - a[0]) * ab[0] + (y - a[1]) * ab[1]) / (ab @ ab), 0, 1)
        dd = np.sqrt((x - a[0] - t * ab[0]) ** 2 + (y - a[1] - t * ab[1]) ** 2)
        side = 1.0 if front is None else (smoothstep(-0.2, 0.2, N[..., 2]) if front else smoothstep(0.2, -0.2, N[..., 2]))
        out.append((soft(dd, w) * torso_arms * side * (darm > 0.005), col, kind))

    if name == 'NightBuilder':
        headwrap((0.17, 0.21, 0.40))
        belt((0.32, 0.19, 0.10))
        belt((0.55, 0.42, 0.20), yc=0.175, w=0.008, kind='leather')        # stitched seam
    elif name == 'NightCourier':
        for sx in (1, -1):
            strap((0.66, 0.53, 0.32), (sx * 0.055, 0.345), (sx * 0.06, 0.17), w=0.020, front=None)
        strap((0.66, 0.53, 0.32), (-0.07, 0.27), (0.07, 0.27), w=0.016, front=True)
        belt((0.60, 0.48, 0.28), yc=0.17, w=0.022, kind='rope')
    elif name == 'NightForager':
        headwrap((0.24, 0.38, 0.22), yc=0.51, w=0.022)
        strap((0.36, 0.22, 0.12), (0.075, 0.35), (-0.085, 0.16), w=0.020, kind='leather')
        belt((0.30, 0.42, 0.24), yc=0.165, w=0.036, kind='cloth')
    elif name == 'Stargazer':
        back = smoothstep(0.15, -0.15, N[..., 2]) * smoothstep(0.15, 0.20, y) * (y < 0.345)
        shoulders = smoothstep(0.27, 0.30, y) * (y < 0.348)
        cape = np.maximum(back, shoulders) * (head < 0.4) * (1 - tail)
        cape = ndimage.gaussian_filter(cape, 1.2)
        cape = smoothstep(0.35, 0.65, cape)
        edge = cape * (1 - smoothstep(0.35, 0.65, ndimage.gaussian_filter(cape, 6) * 1.6 - 0.6))
        out.append((cape, (0.11, 0.14, 0.32), 'cloth'))
        out.append((np.clip(edge * 1.4, 0, 1) * cape, (0.74, 0.70, 0.54), 'cloth'))
    elif name == 'Opera':
        out.append((soft(y - 0.338, 0.03) * torso_arms * (darm > 0.005), (0.86, 0.66, 0.20), 'silk'))  # collar
        strap((0.64, 0.07, 0.09), (0.08, 0.34), (-0.09, 0.17), w=0.034, kind='silk')
        belt((0.07, 0.06, 0.07), yc=0.175, w=0.026, kind='silk')
    return out


def paint(b, name, out_dir, prefix, seed=7):
    P = b.f('P')
    S = b.S
    rgb = np.zeros((S, S, 3)); a = np.zeros((S, S)); h = np.zeros((S, S))
    for k, (m, col, kind) in enumerate(masks(b, name)):
        m = np.clip(m, 0, 1)
        weave = fbm(P * np.array([900.0, 900.0, 900.0]), 2, seed + k) * (0.10 if kind in ('cloth', 'rope') else 0.04)
        if kind == 'rope':
            weave += 0.12 * np.sin((P[..., 1] + P[..., 0]) * 900.0)
        if kind == 'silk':
            weave = weave + 0.06 * smoothstep(-0.2, 0.8, b.f('N')[..., 1])
        inner = ndimage.gaussian_filter(m, 2.0)
        shade = 0.78 + 0.22 * smoothstep(0.2, 0.9, inner)          # darker at the edges: reads as a thick band
        c = np.array(col)[None, None] * (shade * (1 + weave))[..., None]
        rgb = rgb * (1 - m[..., None]) + c * m[..., None]
        a = np.maximum(a, m)
        h = np.maximum(h, inner * (0.6 + 0.4 * (1 + weave)))
    img = np.dstack([np.clip(rgb, 0, 1), a])
    img = raster.pad(img, b.mask & (a > 0.02)) * np.dstack([np.ones((S, S, 3)), (b.mask | (a > 0)).astype(float)])
    img[..., 3] = a * b.mask
    Image.fromarray((img * 255 + 0.5).astype(np.uint8), 'RGBA').save(os.path.join(out_dir, f'{prefix}{name}_D.png'), optimize=True)
    # tangent-space normal from the height, in UV axes (beaver tangents follow +u; bitangent sign w = -1 -> flip v)
    hs = ndimage.gaussian_filter(h, 1.0) * 6.0
    gy, gx = np.gradient(hs)
    n = np.dstack([-gx, gy, np.ones_like(hs)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    nx, ny = n[..., 0] * 0.5 + 0.5, n[..., 1] * 0.5 + 0.5
    packed = np.dstack([np.ones_like(nx), ny, ny, nx])                  # vanilla packing: R=1, G=B=y, A=x
    Image.fromarray((packed * 255 + 0.5).astype(np.uint8), 'RGBA').save(os.path.join(out_dir, f'{prefix}{name}_N.png'), optimize=True)
    with open(os.path.join(out_dir, f'{prefix}{name}_N.png.meta.json'), 'w', encoding='utf-8') as f:
        f.write('{"isNormalMap": true}')
    return img


ALL = ['NightBuilder', 'NightCourier', 'NightForager', 'Stargazer', 'Opera']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('npz'); ap.add_argument('outdir')
    ap.add_argument('--only', default='')
    ap.add_argument('--prefix', default='Ringtail')
    ap.add_argument('--size', type=int, default=2048)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    b = Body(a.npz, a.size)
    for name in [n for n in ALL if not a.only or n in a.only.split(',')]:
        paint(b, name, a.outdir, a.prefix)
        print('painted', a.prefix + name)


if __name__ == '__main__':
    main()
