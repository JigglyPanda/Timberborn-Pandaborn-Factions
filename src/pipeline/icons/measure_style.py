"""Measure icon style numbers, to calibrate ink.Style against vanilla and to check our output.

For every *icon.png in a folder (full-rect sprites, e.g. from extract_vanilla_icons.py or build_icons.py):
  width     stroke width estimate, px (2 * ink area / ink perimeter)
  extent    longest side of the ink (no shadow), px
  cover     share of the canvas covered by ink
  cx, cy    ink centroid offset from the canvas centre, px
  shadow    best-fitting shadow model (dilation, dx, dy), px - only with --shadow (slow)
Prints per icon and the medians.

Usage: python -I measure_style.py <dir> [<dir> ...] [--shadow]
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi


def ink_mask(a):
    lum = a[..., :3].mean(2)
    return (a[..., 3] / 255.0) * np.clip((lum - 40) / 110, 0, 1)


def measure(path, shadow=False):
    a = np.asarray(Image.open(path).convert("RGBA")).astype(float)
    g = ink_mask(a)
    U = 4
    gu = ndi.zoom(g, U, order=1) > 0.5
    area = gu.sum() / U / U
    per = (gu ^ ndi.binary_erosion(gu)).sum() / U
    m = g > 0.5
    ys, xs = np.nonzero(m)
    H, W = m.shape
    r = {
        "width": 2 * area / max(per, 1e-6),
        "extent": max(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1),
        "cover": m.mean(),
        "cx": xs.mean() - W / 2 + 0.5,
        "cy": ys.mean() - H / 2 + 0.5,
    }
    if shadow:
        A = a[..., 3] / 255.0
        Gu, Au = np.kron(g, np.ones((U, U))), np.kron(A, np.ones((U, U)))
        best = None
        for grow in (0, 2, 4):
            D = ndi.grey_dilation(Gu, size=(2 * grow + 1, 2 * grow + 1)) if grow else Gu
            for dy in range(0, 17):
                S = np.zeros_like(D)
                S[dy:] = D[: D.shape[0] - dy]
                err = np.abs(np.maximum(Gu, S) - Au).sum()
                if best is None or err < best[0]:
                    best = (err, grow / U, 0.0, dy / U)
        r["shadow"] = best[1:]
    return r


def main():
    dirs = [d for d in sys.argv[1:] if not d.startswith("--")]
    shadow = "--shadow" in sys.argv
    for d in dirs:
        rows = []
        for f in sorted(os.listdir(d)):
            if f.lower().endswith("icon.png"):
                r = measure(os.path.join(d, f), shadow)
                rows.append(r)
                extra = f" shadow={r['shadow']}" if shadow else ""
                print(f"  {f:40s} width={r['width']:.2f} extent={r['extent']:3d} cover={r['cover']:.3f} "
                      f"c=({r['cx']:+.1f},{r['cy']:+.1f}){extra}")
        keys = ("width", "extent", "cover", "cx", "cy")
        med = {k: float(np.median([r[k] for r in rows])) for k in keys}
        print(d, len(rows), "icons; median", {k: round(v, 3) for k, v in med.items()})


if __name__ == "__main__":
    main()
