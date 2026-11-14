"""The Wooden Ox's UI portrait (bot avatar) from the real ox mesh, in the same style, size and backdrop as the Ringtail
and Inkpaw avatars (make_portraits.py: studio lights, painted teal plate, 512x512).

usage: python -I make_ox_portrait.py OUT.png [--samples 64] [--model WoodenOx.Model.timbermesh]
The ox wears the vanilla bot texture (its material is Bot.Folktails), read from the reference dump on E: and only
rendered here, never copied into the mod. Hard surface: flat faces, no subdivision, no hair (bl_portrait.py "hard").
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import pose_export  # noqa: E402
from make_portraits import BENV, BLENDER, HERE, WORK, plate  # noqa: E402

TEX = r'E:\PandabornDev\reference\vanilla-assets\textures'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--samples', type=int, default=64)
    ap.add_argument('--model', default=r'E:\PandabornDev\build\characters\out\WoodenOx.Model.timbermesh')
    ap.add_argument('--pose', default='Bot_idle:10')
    ap.add_argument('--az', type=float, default=-24)
    ap.add_argument('--seed', type=int, default=7)
    a = ap.parse_args()
    anim, fr = a.pose.split(':')
    p, _ = pose_export.posed(a.model, anim, int(fr))
    _, _, uv, _, tri = pose_export.load(a.model)
    base = np.array(Image.open(os.path.join(TEX, 'BotFolktails_2K_D.png')).convert('RGB')).astype(float) / 255
    ao = np.array(Image.open(os.path.join(TEX, 'BotFolktails_2K_AO.png')).convert('L').resize(base.shape[1::-1])).astype(float) / 255
    base = base * (0.6 + 0.4 * ao[..., None]) * 1.15
    os.makedirs(WORK, exist_ok=True)
    tex = os.path.join(WORK, 'InkpawsBot_tex.png')
    Image.fromarray((base.clip(0, 1) * 255).astype(np.uint8)).save(tex)
    # frame the head and chest as the other avatars do (the head and horns fill the upper half)
    head = p[:, 1] > 0.40
    top = p[head, 1].max()
    h = top - p[:, 1].min()
    scene = dict(tex=tex, out=os.path.join(WORK, 'InkpawsBot_raw.png'), samples=a.samples, child=False, hard=True,
                 tz=float(top - 0.30 * h), dist=float(h * 1.75), az=a.az, el=6, lens=70, width=1024, height=1024,
                 hair_len=0.0, root_radius=0.0)
    npz = os.path.join(WORK, 'InkpawsBot.npz')
    np.savez(npz, P=p.astype(np.float32), T=tri.astype(np.int32), UV=uv.astype(np.float32),
             W=np.zeros(len(p), np.float32), meta=np.array(json.dumps(scene)))
    r = subprocess.run([BLENDER, '-b', '--factory-startup', '--python', os.path.join(HERE, 'bl_portrait.py'), '--', npz],
                       env=BENV, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(scene['out']):
        print(r.stdout[-3000:], r.stderr[-3000:])
        raise SystemExit('ox portrait render failed')
    plate(scene['out'], a.out, a.seed)
    print('portrait', a.out)


if __name__ == '__main__':
    main()
