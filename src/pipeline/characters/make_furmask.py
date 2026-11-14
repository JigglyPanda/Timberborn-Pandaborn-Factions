"""Ringtail fur masks for the Pandaborn Reskin's shell fur (R = fur length, G = ambient occlusion, B = 0).

The Reskin draws shell fur on every colonist with a fur mask in the panda UV layout. A Ringtail keeps the beaver UV
islands but has a long ringed tail, pointed ears and a slimmer face, so the panda mask puts fur where a Ringtail has
none (and too little on the tail). The Reskin's `factions-compat` branch looks up `<model asset>.FurMask` next to
the mesh; these files are that mask:

  Characters/Pandaborn/RingtailAdult.Model.FurMask.png   (1024, linear)
  Characters/Pandaborn/RingtailChild.Model.FurMask.png

Usage: python -I make_furmask.py <adult|child> <paint.npz> <out.png>
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from scipy import ndimage

import raster
import rp_configs
from paint_ringtail import RingtailPainter, REAL, CUTE, ADULT_COATS, CHILD_COATS, smoothstep


def build(which, npz, out, S=1024):
    cfg = rp_configs.get(which)
    kind = cfg['kind']
    ao_npy = npz.replace('.paint.npz', '.ao.npy')
    pt = RingtailPainter(npz, ao_npy, S, kind, cfg['beaver_ao'], scale=cfg['scale'])
    var = dict(REAL if kind == 'adult' else CUTE, **(ADULT_COATS if kind == 'adult' else CHILD_COATS)[0])
    m = pt.masks(var)
    rm = pt.ringtail_masks(var, m)
    r = pt.r
    N = r['N']
    head = r['head'][..., 0]
    tail = r['tail'][..., 0]
    ear = r['ear'][..., 0]
    tt = r['tail_t'][..., 0]
    face = (head > 0.5) * smoothstep(-0.1, 0.5, N[..., 2])
    L = np.full((S, S), 0.80)
    L = L * (1 - 0.30 * (head > 0.5)) * (1 - 0.40 * face)          # shorter on the head, shortest on the face
    # ears: short velvet on the back, a little longer at the pale rim; never a pompom
    L = L * (1 - ear) + ear * (0.28 + 0.20 * rm['ear_rim'])
    # the tail is the bushiest part: long from the root, thinning to a soft point at the dark tip
    tl = smoothstep(0.0, 0.18, tt) * (1 - 0.35 * smoothstep(0.88, 1.0, tt))
    L = L * (1 - tail) + tail * (0.75 + 0.25 * tl)
    eye_zone = ndimage.grey_dilation(np.maximum(m['eye'], m['eyerim']), size=(int(S * 0.012) | 1,) * 2)
    L *= 1 - np.clip(eye_zone, 0, 1)
    L *= 1 - np.clip(ndimage.grey_dilation(m['nose'], size=(5, 5)), 0, 1)
    L *= 1 - 0.9 * np.clip(m['mouth'] * 3, 0, 1)
    L *= 1 - r['sole'][..., 0]
    L *= 1 - r['teeth'][..., 0]
    L = ndimage.gaussian_filter(L, 1.5)
    L = raster.pad(L[..., None], pt.mask)[..., 0]
    G = raster.pad(pt.ao[..., None], pt.mask)[..., 0]
    img = np.zeros((S, S, 3), np.uint8)
    img[..., 0] = (np.clip(L, 0, 1) * 255).round()
    img[..., 1] = (np.clip(G, 0, 1) * 255).round()
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    Image.fromarray(img).save(out)
    with open(out + '.meta.json', 'w') as f:
        f.write('{"linear": true}\n')
    on = pt.mask
    print('fur mask', out, 'R mean %.3f tail %.3f face %.3f ear %.3f' % (
        L[on].mean(), L[on & (tail > 0.5)].mean(), L[on & (face > 0.5)].mean(), L[on & (ear > 0.5)].mean()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('which'); ap.add_argument('npz'); ap.add_argument('out')
    ap.add_argument('--size', type=int, default=1024)
    a = ap.parse_args()
    build(a.which, a.npz, a.out, a.size)


if __name__ == '__main__':
    main()
