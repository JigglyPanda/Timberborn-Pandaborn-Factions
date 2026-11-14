"""Paint the Ringtail (red panda) coats in the beaver UV layout.

usage: python -I paint_ringtail.py ADULT|CHILD MODEL.paint.npz OUT_DIR [--only 1,3] [--size 2048]

Patterns are evaluated on the red panda's rest surface (rasterised into UV space), as in the Pandaborn Reskin's
painter (paint.py, same owner): face markings in head-surface angle space, eyes seated in the game's fixed eye
sockets (normal-map relief), fur strokes from a vanilla beaver texture's high-pass (never on the tail, whose
beaver texture is scales), procedural micro fur, AO baked on the red panda. New here: the ringed tail painted in
the tail's own coordinates (t along, phi around), pointed ears with white rims (front and back faces), a dark
front and underside, and coat variants that differ the way real red pandas do (Himalayan-type pale faces,
Chinese-type deep red with bold rings, ring count, mask shape), not by hue shifts.
No writing or symbols anywhere.
"""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
from scipy import ndimage  # noqa: E402

import paint  # noqa: E402
import raster  # noqa: E402
import rp_configs  # noqa: E402
from paint import fbm, smoothstep  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER = os.environ.get('BLENDER', r'E:\PandabornDev\tools\blender-4.5-lts\blender-4.5.16-windows-x64\blender.exe')
BENV = dict(os.environ, BLENDER_USER_RESOURCES=r'E:\PandabornDev\tools\blender-userdata',
            TEMP=r'E:\PandabornDev\tools\tmp', TMP=r'E:\PandabornDev\tools\tmp')

# Eye sockets and nose in the beaver UV layout (from the Reskin's verified red-panda landmarks on the panda meshes).
LANDMARK_UV = {
    'adult': dict(eye=(0.5265, 0.5085), nose=(0.4999, 0.5686)),
    'child': dict(eye=(0.5287, 0.5039), nose=(0.5423, 0.5876)),
}


class RingtailPainter(paint.Painter):
    def __init__(self, paint_npz, ao_npy, size, kind, beaver_ao_png, scale):
        d = np.load(paint_npz)
        self.scale = scale
        self.d = d
        self.S = size
        tri = d['tri']
        attrs = dict(P=d['P'], N=d['N'], ear=d['ear'], darm=np.minimum(d['darm'], 1.0),
                     dsole=np.minimum(d['dsole'], 1.0), head=d['head'], tail=d['tail'], teeth=d['teeth'],
                     sole=d['sole'], tail_t=d['tail_t'], ear_rho=d['ear_rho'], ear_front=d['ear_front'], ear_cos=d['ear_cos'],
                     tphi_c=np.cos(d['tail_phi']), tphi_s=np.sin(d['tail_phi']))
        r = raster.rasterize(d['uv0'], tri, attrs, size)
        self.mask = r['mask']
        self.r = {k: raster.pad(v, self.mask) for k, v in r.items() if k not in ('mask', 'tri')}
        N = self.r['N']
        self.r['N'] = N / np.linalg.norm(N, axis=2, keepdims=True).clip(1e-9)
        self.r['P'] = self.r['P'] / scale
        self.r['darm'] = self.r['darm'] / scale
        self.r['dsole'] = self.r['dsole'] / scale
        lm = {}
        for k, (u, v) in LANDMARK_UV[kind].items():
            iy = int(np.clip((1 - v) * size, 0, size - 1)); ix = int(np.clip(u * size, 0, size - 1))
            lm[k] = tuple(self.r['P'][iy, ix])
        self.lm = lm
        ao = np.load(ao_npy)
        ao = np.array(Image.fromarray((ao * 255).clip(0, 255).astype(np.uint8)).resize((size, size), Image.BILINEAR)) / 255.0
        self.ao = raster.pad(ao[..., None], self.mask & (ao > 0.02))[..., 0]
        bao = np.array(Image.open(beaver_ao_png).convert('L').resize((size, size), Image.BILINEAR)) / 255.0
        self.beaver_ao = bao

    # ------------------------------------------------------------ markings
    def ringtail_masks(self, var, m):
        r, lm = self.r, self.lm
        P, N = r['P'], r['N']
        x, y, z = P[..., 0], P[..., 1], P[..., 2]
        head = r['head'][..., 0]
        tail = r['tail'][..., 0]
        front = m['front']
        jag = m['jag']
        ex, ey, ez = lm['eye']
        nx, ny, nzc = lm['nose']
        fz = smoothstep(ez - 0.07, ez - 0.035, z) * (head > 0.5)
        hm = head > 0.5
        Hp = P[hm]
        C = np.array([0.0, 0.5 * (Hp[:, 1].min() + Hp[:, 1].max()), 0.5 * (Hp[:, 2].min() + Hp[:, 2].max())])

        def angles(px, py, pz):
            vx, vy, vz = px - C[0], py - C[1], pz - C[2]
            rr = np.sqrt(vx * vx + vy * vy + vz * vz) + 1e-9
            return np.degrees(np.arctan2(np.abs(vx), vz)), np.degrees(np.arcsin(np.clip(vy / rr, -1, 1)))
        th, ph = angles(x, y, z)
        the, phe = angles(np.array(ex), np.array(ey), np.array(ez))
        _, phn = angles(np.array(nx), np.array(ny), np.array(nzc))
        u = th / max(float(the), 1.0)                      # 0 = centre line, 1 = eye
        v = (ph - phn) / max(float(phe - phn), 1.0)        # 0 = nose, 1 = eye
        wob = jag * 10

        def blob(cu, cv, ru, rv, soft=0.18):
            dd = np.sqrt(((u - cu) / ru) ** 2 + ((v - cv) / rv) ** 2) + wob
            return 1 - smoothstep(1 - soft, 1 + soft, dd)
        onface = (head > 0.5) * smoothstep(-0.4, 0.1, N[..., 2] + 0.6)
        # white: muzzle, cheeks sweeping back, eyebrow ovals
        mz = var.get('muzzle', (0.0, -0.18, 0.92, 0.70))
        white = blob(*mz)
        white = white * (1 - smoothstep(var.get('bridge', 0.30), var.get('bridge', 0.30) + 0.25, v))
        ck = var.get('cheek', (1.55, -0.02, 0.80, 0.62))
        white = np.maximum(white, blob(*ck))
        bw = var.get('brow', (0.90, 1.58, 0.36, 0.17))
        white = np.maximum(white, blob(*bw, soft=0.25))
        white *= onface * var.get('white_amount', 1.0)
        # tear tracks: inner eye corner down to the corner of the mouth
        a = np.array(var.get('tear_a', (0.74, 0.70))); b = np.array(var.get('tear_b', (0.56, -0.46)))
        ab = b - a; t = np.clip(((u - a[0]) * ab[0] + (v - a[1]) * ab[1]) / (ab @ ab), 0, 1)
        dd = np.sqrt((u - a[0] - t * ab[0]) ** 2 + (v - a[1] - t * ab[1]) ** 2)
        w = var.get('tear_w', 0.20) * (1 - t) + var.get('tear_w', 0.20) * 0.5 * t
        band = (1 - smoothstep(w * 0.35, w * 1.25, dd + wob * 0.15)) * onface * (1.0 - 0.2 * t)
        ring = np.zeros_like(x)
        s = 1.0
        for sx in (1, -1):
            dd2 = np.sqrt(((x - sx * ex) / (var.get('ring_rx', 0.0140) * s)) ** 2 + ((y - ey + 0.0015) / (var.get('ring_ry', 0.0125) * s)) ** 2) + jag * 14
            ring = np.maximum(ring, 1 - smoothstep(0.65, 1.35, dd2))
        ring *= fz * front * var.get('tear_strength', 0.85)
        white = white * (1 - np.maximum(ring, band))
        # dark: limbs, belly and the whole front of the torso, throat
        darm = r['darm'][..., 0]
        # the dark of the forelegs stops lower on the back than on the chest: the back stays red
        reach = var.get('arm_reach', 0.075) - var.get('arm_back_trim', 0.035) * smoothstep(0.0, -0.6, N[..., 2])
        arms = 1 - smoothstep(reach - 0.015, reach + 0.015, darm + jag * 1.5)
        dsole = r['dsole'][..., 0]
        lr = var.get('leg_reach', 0.20)
        legs = 1 - smoothstep(lr - 0.02, lr + 0.02, dsole + jag * 1.6)
        legs = np.maximum(legs, r['sole'][..., 0])
        under = smoothstep(-0.05, -0.45, N[..., 1] + jag * 6) * (head < 0.45)
        neck_y = var.get('neck_y', 0.345)
        torso_front = smoothstep(var.get('front_edge', 0.30), var.get('front_edge', 0.30) + 0.30, N[..., 2] + jag * 6)
        torso_front *= (head < 0.45) * (1 - smoothstep(neck_y - 0.03, neck_y + 0.01, y + jag * 3))
        throat = (head > 0.3) * smoothstep(ny - 0.035, ny - 0.07, y + jag * 2) * front * 0.9
        dark = np.maximum.reduce([arms, legs, under, torso_front, throat]) * (1 - tail)
        dark = dark * (1 - white)
        # ears: white along the outline (side edges and tip) of the front face, dark inner with pale tufts at the
        # base; the back is dark russet with only a thin white edge; everything fades into the head at the base
        er = r['ear_rho'][..., 0]
        ef = r['ear_front'][..., 0]
        ec = r['ear_cos'][..., 0]
        on_ear = (er < 0.995) * (head > 0.3) * (1 - smoothstep(0.82, 0.97, er))
        ee = var.get('ear_edge', 0.78)
        edge = smoothstep(ee - 0.08, ee + 0.04, ec + jag * 3)
        tipz = 1 - smoothstep(0.10, 0.24, er + jag * 2)
        frontf = (ef > 0).astype(float)
        rim_front = np.maximum(edge, tipz) * frontf
        rim_back = smoothstep(0.90, 0.97, ec + jag * 2) * (1 - frontf)
        rim = np.maximum(rim_front, rim_back) * on_ear
        inner = (1 - edge) * (1 - tipz) * frontf * on_ear
        tuft = inner * smoothstep(0.40, 0.75, er + fbm(P * 400, 2, 3) * 0.15) * var.get('ear_tuft', 0.5)
        back = (1 - frontf) * on_ear * (1 - rim_back)
        # tail rings along t, slightly wavy; the first ring starts where the tail leaves the body
        tt = r['tail_t'][..., 0]
        tc = r['tphi_c'][..., 0]
        nr = var.get('rings', 6)
        t0 = var.get('ring_start', 0.14)
        q = np.clip((tt - t0) / (1 - t0), 0, 1)
        phase = q * nr + jag * var.get('ring_wobble', 9) + var.get('ring_tilt', 0.0) * tc
        stripe = 0.5 + 0.5 * np.cos(2 * np.pi * phase)
        rings = smoothstep(1 - var.get('ring_width', 0.45) - 0.12, 1 - var.get('ring_width', 0.45) + 0.12, stripe)
        rings *= smoothstep(t0 - 0.02, t0 + 0.04, tt) * tail
        rings *= 1 - smoothstep(var.get('tip_start', 0.90), var.get('tip_start', 0.90) + 0.05, tt)
        tip = smoothstep(var.get('tip_start', 0.90), var.get('tip_start', 0.90) + 0.06, tt) * tail * var.get('tip_dark', 0.6)
        under_tail = smoothstep(0.2, -0.8, tc) * tail
        return dict(white=white, tear=ring, band=band, dark=dark, ear_rim=rim, ear_in=inner, ear_tuft=tuft,
                    ear_back=back, rings=rings, tip=tip, under_tail=under_tail)

    def paint_ringtail(self, var, beaver_tex_png, out_png, out_size=None):
        S = self.S
        m = self.masks(var)
        rm = self.ringtail_masks(var, m)
        r = self.r
        P, N = r['P'], r['N']
        head = r['head'][..., :1]
        tail = r['tail'][..., 0]
        tone = fbm(P * 18.0, 3, var.get('seed', 0) + 31)[..., None]
        red = np.array(var['red']); dark = np.array(var['dark']); white = np.array(var['white'])
        backside = smoothstep(-0.2, -0.8, N[..., 2])[..., None] * (head < 0.5)
        top = smoothstep(0.2, 0.9, N[..., 1])[..., None]
        coat = red * (1 + 0.08 * tone) * (1 - var.get('back_deep', 0.16) * backside) + np.array(var.get('ginger', (0.06, 0.04, 0.0))) * top
        # head a touch brighter and more orange than the back (as in real red pandas)
        coat = coat + np.array(var.get('head_glow', (0.05, 0.03, 0.0))) * head
        col = coat

        def over(c, a, k=0.6):
            a = ndimage.gaussian_filter(a, k)[..., None]
            return col * (1 - a) + c * a
        # tail: base, rings, darker tip, a little darker underneath
        tail_base = np.array(var.get('tail_red', var['red']))
        col = over(tail_base * (1 + 0.06 * tone), tail, 1.0)
        col = over(np.array(var.get('ring_col', (0.80, 0.52, 0.26))) * (1 + 0.05 * tone), rm['rings'] * var.get('ring_contrast', 0.9), 1.2)
        col = over(np.array(var.get('tip_col', (0.30, 0.10, 0.04))), rm['tip'], 2.0)
        col = col * (1 - 0.18 * rm['under_tail'][..., None])
        col = over(dark * (1 + 0.1 * tone), rm['dark'], 2.5)
        col = over(np.array(var.get('track_col', (0.47, 0.17, 0.065))), rm['band'], 2.5)
        col = over(np.array(var.get('tear_col', (0.30, 0.095, 0.045))), rm['tear'], 2.5)
        col = over(white * (1 + 0.03 * tone), rm['white'])
        col = over(np.array(var.get('ear_back_col', tuple(np.array(var['red']) * 0.45 + np.array(var['dark']) * 0.4))), rm['ear_back'], 1.5)
        col = over(dark * 1.2 + 0.02, rm['ear_in'], 1.5)
        col = over(white * 0.92, rm['ear_tuft'], 1.5)
        col = over(white * 0.96, rm['ear_rim'], 1.2)
        nose_c = np.array(var.get('nose_col', (0.045, 0.040, 0.042)))
        col = col * (1 - m['nose'][..., None]) + nose_c * m['nose'][..., None]
        col = col + 0.10 * m['nosehi'][..., None]
        col = col * (1 - 0.75 * m['mouth'][..., None]) + 0.06 * m['mouth'][..., None] * nose_c
        rim_c = np.array(var.get('eye_rim', (0.13, 0.08, 0.06)))
        col = col * (1 - m['eyerim'][..., None]) + rim_c * m['eyerim'][..., None]
        col = col * (1 - m['eye'][..., None]) + np.array(var.get('iris', (0.10, 0.065, 0.04))) * m['eye'][..., None]
        col = col + np.array(var.get('iris_low', (0.0, 0.0, 0.0))) * m['eyelow'][..., None]
        col = col * (1 - m['eyehi'][..., None]) + np.array((0.97, 0.97, 0.95)) * m['eyehi'][..., None]
        col = col * (1 - m['eyehi2'][..., None]) + np.array((0.92, 0.92, 0.95)) * m['eyehi2'][..., None]
        bl = ndimage.gaussian_filter(m['blush'], 2.0)[..., None]
        col = col * (1 - bl) + np.array(var.get('blush_col', (0.93, 0.62, 0.62))) * bl
        sole = r['sole'][..., 0]
        col = col * (1 - 0.35 * sole[..., None])
        # fur strokes: the beaver artwork's high-pass on the body; procedural strands along the tail
        bt = np.array(Image.open(beaver_tex_png).convert('RGB').resize((S, S), Image.BICUBIC)) / 255.0
        lum = bt.mean(2)
        hp = lum - ndimage.gaussian_filter(lum, 5.0)
        hp = hp / (ndimage.gaussian_filter(lum, 5.0) + 0.05)
        hp = np.tanh(hp * 1.5) / 1.5
        k = var.get('fur_detail', 0.22) * (1 - m['eye'] - m['eyerim']).clip(0, 1) * (1 - m['nose']) * (1 - tail)
        col = col * (1 + (hp * k)[..., None])
        tt = r['tail_t'][..., 0]
        tphi = np.arctan2(r['tphi_s'][..., 0], r['tphi_c'][..., 0])
        strands = fbm(np.stack([tt * 40, np.cos(tphi) * 30, np.sin(tphi) * 30], -1), 3, var.get('seed', 0) + 13)
        col = col * (1 + var.get('tail_fluff', 0.16) * (strands * tail)[..., None])
        fine = fbm(P * np.array([900, 300, 900]) + N * 40, 2, var.get('seed', 0) + 77)[..., None]
        col = col * (1 + var.get('fluff', 0.035) * fine)
        if var.get('frost', 0) > 0:     # an older individual: grizzled muzzle and brow, frosted crown and shoulders
            where = np.maximum((head[..., 0] > 0.5) * smoothstep(0.0, 0.6, N[..., 2]), 0.5 * smoothstep(0.3, 0.9, N[..., 1]))
            where *= (1 - tail) * (1 - rm['dark'])
            g = smoothstep(0.2, 0.7, fbm(P * 260, 2, var.get('seed', 0) + 5) + 0.25) * where
            col = col + var['frost'] * ndimage.gaussian_filter(g, 1.0)[..., None] * (white - col)
        pa = ndimage.gaussian_filter(self.ao, 6)
        ba = ndimage.gaussian_filter(self.beaver_ao, 6)
        comp = np.clip((pa + 0.15) / (ba + 0.15), 0.8, 1.25) ** var.get('ao_comp', 0.35)
        col = col * comp[..., None]
        col = col * (0.82 + 0.18 * self.ao[..., None]) ** 0.7
        col = np.clip(col, 0, 1)
        img = raster.pad(col, self.mask)
        im = Image.fromarray((img * 255 + 0.5).astype(np.uint8))
        if out_size and out_size != S:
            im = im.resize((out_size, out_size), Image.LANCZOS)
        im.save(out_png, optimize=True)
        return img


# ---------------------------------------------------------------- coat variants
REAL = dict(eye_r=0.0080, eye_rim_w=0.0014, hi_r=0.0026, sparkle2=True, eye_squash=1.0,
            iris=(0.07, 0.045, 0.035), iris_low=(0.10, 0.06, 0.04), eye_rim=(0.12, 0.08, 0.06),
            ring_rx=0.0140, ring_ry=0.0125, nose_w=0.022, nose_h=0.0135, fluff=0.06, wobble=0.008,
            fine_jag=0.004, fur_detail=0.24)
CUTE = dict(eye_r=0.0165, eye_rim_w=0.0014, eye_squash=1.0, eye_dy=0.0, iris=(0.05, 0.035, 0.03),
            iris_low=(0.13, 0.09, 0.06), eye_rim=(0.16, 0.12, 0.09), hi_r=0.0050, sparkle2=True,
            blush=0.75, blush_dx=0.010, blush_dy=0.042, blush_rx=0.024, blush_ry=0.014,
            ring_rx=0.0215, ring_ry=0.0200, nose_w=0.016, nose_h=0.0105, fluff=0.05, fur_detail=0.15, wobble=0.005)

ADULT_COATS = [
    # classic: bright rufous, clean white mask, seven rings
    dict(name=1, seed=41, red=(0.64, 0.25, 0.075), dark=(0.075, 0.042, 0.032), white=(0.93, 0.90, 0.84),
         ring_col=(0.84, 0.58, 0.30), rings=6),
    # Chinese type: deep chestnut, smaller cheek patches, bold rings, dark tip
    dict(name=2, seed=42, red=(0.50, 0.17, 0.060), dark=(0.055, 0.032, 0.028), white=(0.90, 0.87, 0.80),
         ring_col=(0.80, 0.50, 0.24), ring_contrast=1.0, rings=7, ring_width=0.42, tip_dark=0.9,
         cheek=(1.50, -0.04, 0.70, 0.52), brow=(0.90, 1.55, 0.30, 0.14), muzzle=(0.0, -0.20, 0.86, 0.64),
         tear_col=(0.26, 0.08, 0.04), tear_w=0.24),
    # Himalayan type: paler golden coat, big white face, soft rings
    dict(name=3, seed=43, red=(0.72, 0.36, 0.12), dark=(0.12, 0.07, 0.045), white=(0.95, 0.93, 0.87),
         ginger=(0.08, 0.05, 0.0), ring_col=(0.88, 0.66, 0.38), ring_contrast=0.75, rings=5, ring_width=0.50,
         cheek=(1.58, 0.00, 0.88, 0.70), brow=(0.88, 1.58, 0.42, 0.20), muzzle=(0.0, -0.14, 0.98, 0.76),
         tear_col=(0.42, 0.16, 0.06), tear_w=0.17, tip_dark=0.45, ear_tuft=0.8),
    # an older individual: frosted muzzle, dusky back, nine fine rings
    dict(name=4, seed=44, red=(0.55, 0.22, 0.085), dark=(0.07, 0.05, 0.045), white=(0.86, 0.84, 0.79),
         ring_col=(0.76, 0.52, 0.30), rings=8, ring_width=0.40, ring_contrast=0.85, back_deep=0.26, frost=0.10,
         cheek=(1.52, -0.02, 0.76, 0.60), tear_w=0.22),
    # rare cinnamon: light, sandy-red with brown (not black) legs
    dict(name=5, seed=45, red=(0.76, 0.46, 0.24), dark=(0.30, 0.17, 0.10), white=(0.95, 0.93, 0.88),
         ring_col=(0.90, 0.72, 0.48), ring_contrast=0.8, rings=7, tear_col=(0.55, 0.28, 0.12),
         track_col=(0.62, 0.34, 0.16), tip_col=(0.45, 0.22, 0.10), iris=(0.24, 0.15, 0.08)),
]
CHILD_COATS = [
    dict(name=1, seed=51, red=(0.68, 0.32, 0.11), dark=(0.13, 0.08, 0.06), white=(0.95, 0.93, 0.88),
         ring_col=(0.86, 0.60, 0.32), rings=6, ring_contrast=0.75, fur_detail=0.16),
    dict(name=2, seed=52, red=(0.58, 0.24, 0.085), dark=(0.10, 0.06, 0.05), white=(0.93, 0.90, 0.84),
         ring_col=(0.82, 0.52, 0.26), rings=7, ring_contrast=0.85, fur_detail=0.16,
         cheek=(1.50, -0.04, 0.74, 0.56), tear_w=0.24),
    dict(name=3, seed=53, red=(0.76, 0.42, 0.18), dark=(0.18, 0.11, 0.07), white=(0.96, 0.94, 0.90),
         ring_col=(0.92, 0.70, 0.44), rings=6, ring_contrast=0.65, fur_detail=0.16,
         cheek=(1.60, 0.0, 0.90, 0.72), muzzle=(0.0, -0.14, 0.98, 0.76), tear_w=0.16, ear_tuft=0.8),
]


def bake_ao(npz, out_npy, size=1024, dist=0.12):
    r = subprocess.run([BLENDER, '-b', '--factory-startup', '--python', os.path.join(HERE, 'bl_bake_ao.py'), '--',
                        npz, out_npy, str(size), str(dist)], env=BENV, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(out_npy):
        print(r.stdout[-2000:], r.stderr[-2000:])
        raise SystemExit('AO bake failed')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('which'); ap.add_argument('npz'); ap.add_argument('outdir')
    ap.add_argument('--only', default='')
    ap.add_argument('--size', type=int, default=2048)
    ap.add_argument('--rebake', action='store_true')
    a = ap.parse_args()
    cfg = rp_configs.get(a.which)
    kind = cfg['kind']
    ao = a.npz.replace('.paint.npz', '.ao.npy')
    if a.rebake or not os.path.exists(ao):
        bake_ao(a.npz, ao, 1024, 0.12 * cfg['scale'])
    pt = RingtailPainter(a.npz, ao, a.size, kind, cfg['beaver_ao'], scale=cfg['scale'])
    print('landmarks', {k: tuple(round(float(c), 4) for c in v) for k, v in pt.lm.items()})
    beaver_tex = os.path.join(rp_configs.TEX, 'BeaverAdult1.Folktails.png' if kind == 'adult' else 'BeaverChild1.Folktails.png')
    coats = ADULT_COATS if kind == 'adult' else CHILD_COATS
    style = REAL if kind == 'adult' else CUTE
    only = [int(x) for x in a.only.split(',') if x]
    os.makedirs(a.outdir, exist_ok=True)
    out_size = 2048 if kind == 'adult' else 1024
    for v in coats:
        if only and v['name'] not in only:
            continue
        var = dict(style, **v)
        if kind == 'child':
            var.setdefault('arm_reach', 0.075); var.setdefault('leg_reach', 0.20); var.setdefault('neck_y', 0.345)
        nm = f"Ringtail{'Adult' if kind == 'adult' else 'Child'}Coat{v['name']}.png"
        pt.paint_ringtail(var, beaver_tex, os.path.join(a.outdir, nm), out_size)
        print('painted', nm)


if __name__ == '__main__':
    main()
