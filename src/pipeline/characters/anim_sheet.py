"""Render an animation contact sheet: rows = animations, columns = frames spread over each clip.

usage: python -I anim_sheet.py MODEL.timbermesh TEXTURE.png OUT_PREFIX anim1,anim2,... [--cols 5] [--az 60] [--el 20]
       [--spacing 0.7] [--decal DECAL.png] [--compare OTHER.timbermesh OTHER_TEX.png]
Writes OUT_PREFIX_<view>.png. With --compare, each row shows the other model's frame 0 at the left.
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('model'); ap.add_argument('tex'); ap.add_argument('out'); ap.add_argument('anims')
    ap.add_argument('--cols', type=int, default=5)
    ap.add_argument('--views', default='side:80:14,back:165:38,front:15:12')
    ap.add_argument('--spacing', type=float, default=0.75)
    ap.add_argument('--decal', default='')
    ap.add_argument('--samples', type=int, default=16)
    ap.add_argument('--width', type=int, default=1600)
    a = ap.parse_args()
    anims = a.anims.split(',')
    items = []
    for r, an in enumerate(anims):
        for c in range(a.cols):
            fr = f'{c / max(a.cols - 1, 1):.3f}' if an != 'rest' else 0
            items.append(dict(model=a.model, anim=an, frame=fr, texture=a.tex, decal=a.decal,
                              offset=[(c - (a.cols - 1) / 2) * a.spacing, -r * a.spacing * 1.3]))
    rows = len(anims)
    cz = -(rows - 1) * a.spacing * 1.3 / 2
    cams = []
    for v in a.views.split(','):
        name, az, el = v.split(':')
        dist = max(a.cols * a.spacing, rows * a.spacing * 1.3) * 1.9
        cams.append(dict(out=f'{a.out}_{name}.png', target=[0, 0.2, cz], az=float(az), el=float(el), dist=dist, lens=55))
    h = int(a.width * min(1.0, (rows * 1.3 + 0.6) / (a.cols + 0.4)) * 0.9) + 200
    sc = dict(out_npz=a.out + '.npz', samples=a.samples, size=[a.width, h], items=items, cameras=cams)
    sp = a.out + '.scene.json'
    json.dump(sc, open(sp, 'w'), indent=1)
    subprocess.run([sys.executable, '-I', os.path.join(HERE, 'preview.py'), sp], check=True)


if __name__ == '__main__':
    main()
