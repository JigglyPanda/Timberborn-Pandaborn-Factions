"""Ringtail UI portraits (avatars): clean studio renders of the Ringtail meshes with real hair, on the same painted
teal plate as the Inkpaw avatars (the Pandaborn Reskin's portrait2.py method, same owner), split so that Blender
only needs numpy: this script prepares the posed mesh, texture and fur weights, bl_portrait.py renders, and this
script composites the plate.

usage: python -I make_portraits.py OUT_DIR [--samples 96] [--only RingtailAdult,...]
Writes RingtailAdult.png, RingtailChild.png, RingtailContaminatedAdult.png, RingtailContaminatedChild.png (512x512).
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
from PIL import Image, ImageFilter  # noqa: E402
from scipy import ndimage  # noqa: E402

import pose_export  # noqa: E402
import rp_configs  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
BLENDER = os.environ.get('BLENDER', r'E:\PandabornDev\tools\blender-4.5-lts\blender-4.5.16-windows-x64\blender.exe')
BENV = dict(os.environ, BLENDER_USER_RESOURCES=r'E:\PandabornDev\tools\blender-userdata',
            TEMP=r'E:\PandabornDev\tools\tmp', TMP=r'E:\PandabornDev\tools\tmp')
OUT = r'E:\PandabornDev\build\characters\out'
WORK = r'E:\PandabornDev\build\characters\portraits'
COATS = os.path.join(REPO, 'mod', 'PandabornFactions', 'Materials', 'Pandaborn', 'Ringtails')

PORTRAITS = [
    # name, kind, coat, contaminated, pose, azimuth, seed
    ('RingtailAdult', 'adult', 'Adult/RingtailAdultCoat1.png', False, 'idle:10', -18, 3),
    ('RingtailChild', 'child', 'Child/RingtailChildCoat1.png', False, 'idle:10', -18, 4),
    ('RingtailContaminatedAdult', 'adult', 'Adult/RingtailAdultCoat1.png', True, 'idle:10', -18, 5),
    ('RingtailContaminatedChild', 'child', 'Child/RingtailChildCoat1.png', True, 'idle:10', -18, 6),
]


def fur_weights(paint, kind):
    """Per-vertex fur length 0..1: none on the eyes, nose and pads, short on the face, longest on the tail."""
    from paint_ringtail import LANDMARK_UV
    P = paint['P']
    uv = paint['uv0']
    w = np.full(len(P), 0.75)
    head = paint['head'] > 0.5
    w[head & (P[:, 2] > np.percentile(P[head, 2], 55))] = 0.40
    w[paint['ear'] > 0.5] = 0.55
    w[paint['tail'] > 0.5] = 1.0
    w[paint['sole'] > 0.5] = 0.0
    w[paint['teeth'] > 0.5] = 0.0
    s = 1.0 if kind == 'adult' else 0.6
    for name, rad in (('eye', 0.024), ('nose', 0.020)):
        p = P[np.argmin(np.linalg.norm(uv - np.array(LANDMARK_UV[kind][name]), axis=1))]
        for q in (p, p * np.array([-1, 1, 1])):
            d = np.linalg.norm(P - q, axis=1) / (rad * s)
            w = np.minimum(w, np.clip(d - 0.6, 0, 1) * 0.4)
    return w


def prep(name, kind, coat, contam, pose, az, samples):
    cfg = rp_configs.get('ADULT' if kind == 'adult' else 'CHILD')
    model = os.path.join(OUT, f"Ringtail{'Adult' if kind == 'adult' else 'Child'}.Model.timbermesh")
    paint = np.load(model.replace('.timbermesh', '') + '.paint.npz')
    anim, fr = pose.split(':')
    p, _ = pose_export.posed(model, anim, int(fr))
    _, _, uv, uv1, tri = pose_export.load(model)
    base = np.array(Image.open(os.path.join(COATS, coat)).convert('RGB').resize((2048, 2048), Image.BICUBIC)).astype(float) / 255
    ao = np.load(model.replace('.timbermesh', '') + '.ao.npy')
    ao = np.array(Image.fromarray((ao * 255).clip(0, 255).astype(np.uint8)).resize((2048, 2048), Image.BILINEAR)) / 255.0
    base = base * (0.55 + 0.45 * ao[..., None])
    if contam:
        c = np.array(Image.open(os.path.join(rp_configs.TEX, 'Contamination_D.png')).convert('RGBA').resize((2048, 2048))).astype(float) / 255
        al = c[..., 3:] * 0.6
        base = base * (1 - al) + c[..., :3] * al
    os.makedirs(WORK, exist_ok=True)
    tex = os.path.join(WORK, name + '_tex.png')
    Image.fromarray((base.clip(0, 1) * 255).astype(np.uint8)).save(tex)
    top, bot = p[:, 1].max(), p[:, 1].min()
    h = top - bot
    scene = dict(tex=tex, out=os.path.join(WORK, name + '_raw.png'), samples=samples, child=kind == 'child',
                 tz=float(top - 0.33 * h), dist=float(h * (1.95 if kind == 'child' else 1.85)), az=az, el=6, lens=70,
                 width=1024, height=1024, hair_len=(0.011 if kind == 'child' else 0.013) * 1.6 * rp_configs.SIZE,
                 root_radius=(0.0011 if kind == 'child' else 0.0013) * rp_configs.SIZE)
    npz = os.path.join(WORK, name + '.npz')
    np.savez(npz, P=p.astype(np.float32), T=tri.astype(np.int32), UV=uv.astype(np.float32),
             W=fur_weights(paint, kind).astype(np.float32), meta=np.array(json.dumps(scene)))
    return npz, scene


def plate(raw_png, out_png, seed, W=512, H=512):
    rng = np.random.default_rng(seed)
    fg = Image.open(raw_png).convert('RGBA').resize((W, H), Image.LANCZOS)
    fg = fg.filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2))
    yy, xx = np.mgrid[0:H, 0:W] / max(W, H)

    def noise(scale, octaves=4):
        out = np.zeros((H, W))
        for o in range(octaves):
            s = scale * 2 ** o
            n = rng.random((int(H / s) + 2, int(W / s) + 2))
            out += ndimage.zoom(n, (H / n.shape[0], W / n.shape[1]), order=3)[:H, :W] / 2 ** o
        return out / 2
    cx, cy = 0.5 * W / max(W, H), 0.42 * H / max(W, H)
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    teal_hi, teal_lo = np.array([0.20, 0.33, 0.33]), np.array([0.06, 0.12, 0.13])
    g = np.clip(1 - r * 1.5, 0, 1)[..., None]
    bg = teal_lo + (teal_hi - teal_lo) * g
    bg *= 0.88 + 0.24 * noise(24, 4)[..., None]
    edge = np.minimum.reduce([xx, (W / max(W, H)) - xx, yy, (H / max(W, H)) - yy])
    rough = edge + (noise(10, 3) - 0.5) * 0.035
    alpha = np.clip((rough - 0.012) / 0.012, 0, 1)
    out = Image.fromarray(np.dstack([(bg * 255).clip(0, 255), alpha * 255]).astype(np.uint8), 'RGBA')
    out.alpha_composite(fg)
    out.save(out_png, optimize=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('outdir')
    ap.add_argument('--samples', type=int, default=96)
    ap.add_argument('--only', default='')
    a = ap.parse_args()
    only = [x for x in a.only.split(',') if x]
    os.makedirs(a.outdir, exist_ok=True)
    for name, kind, coat, contam, pose, az, seed in PORTRAITS:
        if only and name not in only:
            continue
        npz, scene = prep(name, kind, coat, contam, pose, az, a.samples)
        r = subprocess.run([BLENDER, '-b', '--factory-startup', '--python', os.path.join(HERE, 'bl_portrait.py'), '--', npz],
                           env=BENV, capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(scene['out']):
            print(r.stdout[-3000:], r.stderr[-3000:])
            raise SystemExit('portrait render failed: ' + name)
        plate(scene['out'], os.path.join(a.outdir, name + '.png'), seed)
        print('portrait', name)


if __name__ == '__main__':
    main()
