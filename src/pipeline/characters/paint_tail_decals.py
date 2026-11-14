"""Tail decals (DecalSpec category "Tails") for the Inkpaws faction: plain ribbons and bands, no symbols.

usage: python -I paint_tail_decals.py OUT_DIR

The game samples `_TailDecalDiffuse` with uv1. On the beaver paddle (and the Inkpaw's stub, which keeps the paddle's
uv1) the decal spans u 0.18..0.82 root (v~0.04) to tip (v~0.96). On the Ringtail's round tail uv1 runs root->tip along
the top and is mirrored underneath (redpanda.tail_uv1), so a band across the full width becomes a ribbon tied around the
tail. Decals are per faction, chosen at the tail-painting building, so one set must suit both peoples: bands do.
Image row 0 is v = 1 (the tip).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from paint import fbm, smoothstep  # noqa: E402

S = 1024


def canvas():
    v, u = np.mgrid[0:S, 0:S] / (S - 1.0)
    v = 1.0 - v
    return u, v, np.zeros((S, S, 3)), np.zeros((S, S))


def band(v, c, w, soft=0.006):
    return 1 - smoothstep(w / 2 - soft, w / 2 + soft, np.abs(v - c))


def width_mask(u):
    return smoothstep(0.13, 0.17, u) * (1 - smoothstep(0.83, 0.87, u))


def put(rgb, a, m, col, u, v, seed, cloth=True):
    tone = fbm(np.dstack([u * 60, v * 60, np.zeros_like(u)]), 3, seed) * (0.10 if cloth else 0.04)
    shade = 0.85 + 0.15 * np.cos((u - 0.5) * np.pi)          # a little rounder in the middle
    c = np.array(col)[None, None] * (shade * (1 + tone))[..., None]
    rgb = rgb * (1 - m[..., None]) + c * m[..., None]
    return rgb, np.maximum(a, m)


def save(rgb, a, path):
    Image.fromarray((np.dstack([np.clip(rgb, 0, 1), np.clip(a, 0, 1)]) * 255 + 0.5).astype(np.uint8), 'RGBA').save(path, optimize=True)


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    # 1. a crimson silk ribbon with gold edges
    u, v, rgb, a = canvas(); w = width_mask(u)
    rgb, a = put(rgb, a, band(v, 0.40, 0.13) * w, (0.66, 0.08, 0.10), u, v, 1)
    for e in (0.40 - 0.068, 0.40 + 0.068):
        rgb, a = put(rgb, a, band(v, e, 0.012) * w, (0.86, 0.66, 0.22), u, v, 2, cloth=False)
    save(rgb, a, os.path.join(out, 'PandabornTailRibbon.png'))
    # 2. two indigo bands
    u, v, rgb, a = canvas(); w = width_mask(u)
    for c in (0.36, 0.62):
        rgb, a = put(rgb, a, band(v, c, 0.08) * w, (0.17, 0.22, 0.44), u, v, 3)
    save(rgb, a, os.path.join(out, 'PandabornTailTwinBands.png'))
    # 3. a cream "dipped" tip with a thin dark line
    u, v, rgb, a = canvas(); w = width_mask(u)
    tip = smoothstep(0.80, 0.83, v + 0.01 * np.sin(u * 40)) * (1 - smoothstep(0.955, 0.97, v)) * w
    rgb, a = put(rgb, a, tip, (0.93, 0.88, 0.76), u, v, 4)
    rgb, a = put(rgb, a, band(v + 0.01 * np.sin(u * 40), 0.80, 0.010) * w, (0.20, 0.12, 0.08), u, v, 5, cloth=False)
    save(rgb, a, os.path.join(out, 'PandabornTailTipCream.png'))
    # 4. a braided cord with three wooden beads on top
    u, v, rgb, a = canvas(); w = width_mask(u)
    braid = band(v + 0.006 * np.sin(u * 160), 0.50, 0.04) * w
    rgb, a = put(rgb, a, braid, (0.62, 0.50, 0.30), u, v, 6)
    for cu in (0.40, 0.50, 0.60):
        bead = 1 - smoothstep(0.036, 0.044, np.sqrt((u - cu) ** 2 + ((v - 0.50) * 1.0) ** 2))
        rgb, a = put(rgb, a, bead, (0.42, 0.24, 0.12), u, v, 7, cloth=False)
    save(rgb, a, os.path.join(out, 'PandabornTailBeadCord.png'))
    print('wrote 4 tail decals to', out)


if __name__ == '__main__':
    main()
