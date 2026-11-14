"""Beaver -> red panda (Ringtail) geometry: rest-pose sculpt, ringed bushy tail, all-animation transfer.

Built on the Pandaborn Reskin's giant-panda builder (panda.py, same owner): the same refinement, SDF head and
body sculpt, mouth cap and Kabsch neighbourhood transfer. What is new here:
  * pointed, flat, rounded-tip ears instead of half-ellipsoid bumps;
  * a slim body (the SDF may pull the beaver's belly in, not only push it out);
  * a long round tail built from the beaver's flat paddle, driven in every frame by a chain of "slice bones"
    fitted to the paddle (weighted Kabsch per slice, linear blend between neighbouring slices), so it bends
    with the beaver's tail in every animation without shearing;
  * per-vertex tail coordinates (t along the tail, phi around it) for the ring paint and the tail-decal uv1.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
from scipy.sparse.csgraph import dijkstra  # noqa: E402

import geom  # noqa: E402
import panda  # noqa: E402
from panda import smoothstep  # noqa: E402

V3 = lambda *a: np.array(a, dtype=np.float64)  # noqa: E731


def ear_profile(rho, tr):
    """1 at the centre, 0 at the rim; a cone whose tip is rounded with radius ~tr (in rho units)."""
    a = np.sqrt(1 + tr * tr)
    return np.clip((a - np.sqrt(rho * rho + tr * tr)) / (a - tr), 0, 1)


class RedPandaBuilder(panda.PandaBuilder):

    # ------------------------------------------------------------ tail geometry helpers
    def tail_radius(self, t):
        """Bushy profile: slim where it leaves the body, fullest in the last third, a soft round tip (0 at t=1)."""
        tc = self.cfg['tail']
        r = tc['r_root'] + (tc['r_max'] - tc['r_root']) * smoothstep(0.0, tc['t_max'], t) ** tc.get('swell', 1.0)
        q = np.clip((t - tc['t_cap']) / (1 - tc['t_cap']), 0, 1)
        return r * np.sqrt(np.clip(1 - q * q, 0.0, 1))

    def tail_centre(self, t):
        """Rest centreline (x=0): from the hip down to rest just above the ground, then a small upward curl."""
        tc = self.cfg['tail']
        tr = self.cfg['tail_root']
        ground = tc['r_max'] * 0.92 + tc['rest_clear']
        y = tc['root_y'] + (ground - tc['root_y']) * smoothstep(0.0, tc['settle_t'], t)
        y = y + tc['curl'] * smoothstep(tc['curl_t'], 1.0, t)
        z = tr[2] - tc['length'] * t
        return np.stack([np.zeros_like(t), y, z], -1)

    def tail_frame(self, t):
        h = 1e-3
        c0 = self.tail_centre(np.clip(t - h, 0, 1))
        c1 = self.tail_centre(np.clip(t + h, 0, 1))
        T = c1 - c0
        T /= np.linalg.norm(T, axis=-1, keepdims=True).clip(1e-9)
        X = np.broadcast_to(V3(1, 0, 0), T.shape)
        U = np.cross(T, X)            # up, perpendicular to the tangent
        U *= np.sign(U[..., 1:2] + 1e-9)
        return X, U, T

    # ------------------------------------------------------------ rest sculpt
    def build_rest(self):
        s, cfg = self.s, self.cfg
        self.source_regions()
        head_y = cfg['neck_y'][0]
        cent = s.P[s.tri].mean(1)
        # refine the face and the front of the head (the back of the head stays at the beaver's resolution: vertex budget)
        is_head_tri = (cent[:, 1] > head_y) & (cent[:, 2] > cfg.get('refine_zmin', cfg['head_zmin'])) & ~self.teeth_src[s.tri].any(1)
        is_tail_tri = self.tail_src[s.tri].all(1)
        attrs = dict(uv0=s.uv0, uv1=s.uv1, T=s.T, C=s.C.astype(np.float64), N=s.N)
        P, tri, at, winv, parents = geom.refine(s.P, s.tri, attrs, s.winv, is_head_tri | is_tail_tri, iterations=1)
        ears = np.array(cfg['ear']['c'])
        cent = P[tri].mean(1)
        near_ear = np.zeros(len(tri), bool)
        for e in (ears, ears * [-1, 1, 1]):
            near_ear |= np.linalg.norm(cent - e, axis=1) < cfg['ear']['r'] * cfg.get('ear_refine', 1.35)
        P2, tri2, at2, winv2, parents2 = geom.refine(P, tri, at, winv, near_ear, iterations=1)
        comp_par = []
        for d in parents2:
            dd = {}
            for k, w in d.items():
                for k2, w2 in parents[k].items():
                    dd[k2] = dd.get(k2, 0) + w * w2
            comp_par.append(dd)
        P, tri, at, winv, parents = P2, tri2, at2, winv2, comp_par
        self.parents = parents
        V = len(P)
        self.log(f"refined: {len(s.P)} -> {V} verts, {len(s.tri)} -> {len(tri)} tris")

        def inherit(flag):
            return np.array([any(flag[k] for k in d) for d in parents])

        def inherit_all(flag):
            return np.array([all(flag[k] for k in d) for d in parents])
        teeth = inherit_all(self.teeth_src)
        tail = inherit_all(self.tail_src)
        arm = inherit_all(self.arm_src)
        sole = inherit(self.sole_src)
        N0 = at['N'] / np.linalg.norm(at['N'], axis=1, keepdims=True)
        Pw = np.zeros((winv.max() + 1, 3)); Pw[winv] = P
        A, _ = geom.edge_graph(winv[tri], len(Pw), Pw)
        dsole = dijkstra(A, directed=False, indices=np.unique(winv[sole]), min_only=True)[winv]
        darm = dijkstra(A, directed=False, indices=np.unique(winv[arm]), min_only=True)[winv]
        self.geo = dict(dsole=dsole, darm=darm)
        X = P.copy()
        y = P[:, 1]

        # ---- head: cranium + cheeks + short muzzle + jaw
        cr = cfg['cranium']; ch = cfg['cheek']; mz = cfg['muzzle']; jw = cfg['jaw']

        def f_head(x):
            d = geom.sd_ellipsoid(x, V3(*cr['c']), V3(*cr['r']))
            for sx in (1, -1):
                d = geom.smin(d, geom.sd_ellipsoid(x, V3(ch['c'][0] * sx, *ch['c'][1:]), V3(*ch['r'])), ch['k'])
            d = geom.smin(d, geom.sd_ellipsoid(x, V3(*mz['c']), V3(*mz['r'])), mz['k'])
            d = geom.smin(d, geom.sd_ellipsoid(x, V3(*jw['c']), V3(*jw['r'])), jw['k'])
            return d
        self.f_head = f_head
        w_head = smoothstep(cfg['neck_y'][0], cfg['neck_y'][1], y) * smoothstep(cfg['head_zmin'] - 0.03, cfg['head_zmin'] + 0.02, P[:, 2])
        w_head *= ~teeth
        X = geom.project_to_sdf(f_head, X, w_head * cfg['head_strength'])

        # ---- body: slim (inward motion mostly kept)
        bd = cfg['body']

        def f_body(x):
            d = geom.sd_ellipsoid(x, V3(*bd['belly_c']), V3(*bd['belly_r']))
            return geom.smin(d, geom.sd_ellipsoid(x, V3(*bd['chest_c']), V3(*bd['chest_r'])), bd['k'])
        w_body = (1 - smoothstep(cfg['neck_y'][0] - 0.04, cfg['neck_y'][0] + 0.01, y))
        w_body *= smoothstep(0.02, bd['limb_fade'], darm) * smoothstep(bd['leg_fade'][0], bd['leg_fade'][1], dsole)
        w_body *= ~tail & ~teeth
        Xb = geom.project_to_sdf(f_body, X, w_body * bd['strength'])
        inward = np.sum((Xb - X) * N0, 1) < 0
        Xb[inward] = X[inward] + (Xb[inward] - X[inward]) * bd['inward_keep']
        X = Xb

        lm = cfg['limbs']
        w_arm_infl = (1 - smoothstep(0.0, lm['arm_fade'], darm)) * (1 - smoothstep(0.30, 0.42, y / cfg['height']))
        w_leg_infl = (1 - smoothstep(lm['leg_len'] * 0.6, lm['leg_len'], dsole))
        infl = (lm['arm'] * w_arm_infl + lm['leg'] * w_leg_infl) * (~tail & ~teeth & ~sole)
        X = X + N0 * infl[:, None]
        if cfg.get('tubes'):
            X = self.tube_sculpt(X, P, tri, winv, arm, sole, darm, dsole, teeth, tail, cfg['tubes'])

        # ---- ears: flat pointed cones with a rounded tip, leaning out and slightly back
        er = cfg['ear']
        ear_rho = np.ones(V)
        ear_front = np.zeros(V)
        ear_cos = np.zeros(V)
        ear_mask = np.zeros(V, bool)
        for sx in (1, -1):
            c0 = V3(er['c'][0] * sx, *er['c'][1:])
            k = np.argmin(np.linalg.norm(X - c0, axis=1) + 10 * teeth)
            c = X[k]
            n = N0[k]
            dirv = n * er['normal_mix'] + V3(0, 1, 0) * (1 - er['normal_mix']) + V3(sx * er['splay'], 0, -er.get('lean_back', 0))
            dirv /= np.linalg.norm(dirv)
            fwd = V3(0, 0, 1) - dirv * dirv[2]; fwd /= np.linalg.norm(fwd)
            side = np.cross(dirv, fwd)
            rel = X - c
            a = rel @ side; b = rel @ fwd; h0 = rel @ dirv
            ea, eb = er.get('base_ellipse', (1.0, 1.0))
            rho = np.sqrt((a / (er['r'] * ea)) ** 2 + (b / (er['r'] * eb)) ** 2)
            m = (rho < 1) & (np.abs(h0) < er['r']) & (w_head > 0.5) & ~teeth
            prof = ear_profile(rho, er.get('tip_round', 0.2)) ** er.get('sharp', 1.0)
            lift = er['h'] * prof
            newb = b * (er['thick'] + (1 - er['thick']) * (1 - prof))
            # the base widens into the head a little so the ear does not look glued on
            newa = a * (1 + 0.10 * (1 - prof))
            X[m] = c + side * newa[m, None] + fwd * newb[m, None] + dirv * (h0[m, None] + lift[m, None])
            ear_mask |= m
            ear_rho[m] = np.minimum(ear_rho[m], rho[m])
            ear_front[m] = np.sign(b[m])
            # 1 on the ear's side edges (its outline seen from the front), 0 on the middle of the front/back face
            ear_cos[m] = np.abs(a[m] / (er['r'] * ea)) / np.maximum(rho[m], 1e-6)
            setattr(self, f'ear_centre_{sx}', c + dirv * er['h'] * 0.5)
            setattr(self, f'ear_dir_{sx}', dirv)
        self.ear_mask = ear_mask

        # ---- tail: a round, bushy tube built from the paddle's vertices
        tr = V3(*cfg['tail_root'])
        tc = cfg['tail']
        tail_t = np.zeros(V); tail_phi = np.zeros(V)
        if tail.any():
            idx = np.nonzero(tail)[0]
            Pt = P[idx]
            L = np.clip(tr[2] - Pt[:, 2], 0, None)
            t01 = np.clip(L / L.max(), 0, 1)
            nb = 14
            bins = np.clip((t01 * nb).astype(int), 0, nb - 1)
            wmax = np.array([np.abs(Pt[bins == k, 0]).max() if np.any(bins == k) else 1e-3 for k in range(nb)])
            wmax = np.maximum(wmax, 1e-3)
            u = np.clip(Pt[:, 0] / wmax[bins], -1, 1)
            mid = np.array([Pt[bins == k, 1].mean() if np.any(bins == k) else 0 for k in range(nb)])
            sidev = np.where(Pt[:, 1] >= mid[bins], 1.0, -1.0)
            sidev = np.where(np.abs(N0[idx, 1]) > 0.3, np.sign(N0[idx, 1]), sidev)
            # left/right from the vertex's own side of the paddle (the centre seam is split per UV island)
            sgn = np.where(np.abs(Pt[:, 0]) > 1e-4, np.sign(Pt[:, 0]), np.sign(N0[idx, 0] + 1e-9))
            phi = np.where(sidev > 0, 0.5 * np.pi * u, sgn * (np.pi - 0.5 * np.pi * np.abs(u)))
            X_, U_, T_ = self.tail_frame(t01)
            R = self.tail_radius(t01)
            newp = self.tail_centre(t01) + R[:, None] * (np.sin(phi)[:, None] * X_ + np.cos(phi)[:, None] * U_)
            # keep the vertices welded to the body (the root ring) where they are; blend out from them
            shared_w = np.zeros(winv.max() + 1, bool)
            shared_w[np.intersect1d(winv[tail], winv[~tail])] = True
            shared = shared_w[winv[idx]]
            t_ring = t01[shared].max() if shared.any() else 0.0
            blend = smoothstep(t_ring * 0.5, t_ring + tc['root_blend'], t01) * ~shared
            X[idx] = Pt * (1 - blend[:, None]) + newp * blend[:, None]
            tail_t[idx] = t01
            tail_phi[idx] = phi
            self.tail_blend = np.zeros(V); self.tail_blend[idx] = blend
            self.log(f"tail: {len(idx)} verts, ring t<= {t_ring:.3f}, length {tc['length']}, r_max {tc['r_max']}")
        self.stub_centre = self.tail_centre(np.array([0.5]))[0]

        if teeth.any():
            tcn = V3(*cfg['teeth_hide'])
            X[teeth] = tcn + (P[teeth] - tcn) * 0.04
        X = self.laplacian_smooth(X, tri, winv, (w_head > 0.5) & ~teeth, cfg.get('smooth_iters', 4), 0.35)
        # weld consistency: every copy of a welded vertex takes the body-side copy's position
        X = self.weld_fix(X, winv, tail)

        if tc.get('sides'):
            A = dict(P=P, X=X, teeth=teeth, tail=tail, arm=arm, sole=sole, w_head=w_head, darm=self.geo['darm'],
                     dsole=self.geo['dsole'], ear_rho=ear_rho, ear_front=ear_front, ear_cos=ear_cos,
                     ear_mask=self.ear_mask, tail_t=tail_t, tail_phi=tail_phi, tail_blend=self.tail_blend)
            for k in at:
                A['at_' + k] = at[k]
            A, tri, winv, parents = self.rebuild_tail(A, tri, winv, parents)
            P, X, teeth, tail, arm, sole, w_head = A['P'], A['X'], A['teeth'], A['tail'], A['arm'], A['sole'], A['w_head']
            self.geo = dict(darm=A['darm'], dsole=A['dsole'])
            ear_rho, ear_front, ear_cos, self.ear_mask = A['ear_rho'], A['ear_front'], A['ear_cos'], A['ear_mask']
            tail_t, tail_phi, self.tail_blend = A['tail_t'], A['tail_phi'], A['tail_blend']
            at = {k: A['at_' + k] for k in at}
            self.parents = parents
            V = len(P)

        self.P0, self.P1, self.tri, self.winv, self.at = P, X, tri, winv, at
        self.flags = dict(teeth=teeth, tail=tail, arm=arm, sole=sole, head=w_head > 0.5,
                          tail_t=tail_t, tail_phi=tail_phi, ear_rho=ear_rho, ear_front=ear_front, ear_cos=ear_cos,
                          tail_blend=getattr(self, 'tail_blend', np.zeros(V)))
        self.w_head = w_head
        self.sg = self.smoothing_ids(P, at['N'], winv)
        return X

    def rebuild_tail(self, A, tri, winv, parents):
        """Replace the paddle-derived tail with a clean tube: `sides` around (16), rings dense toward a round pole tip.

        The beaver's tail UV islands are kept (top/bottom, and left/right on the adult): every new vertex takes its uv0,
        tangent sign, colour and parentage by barycentric lookup in its island's (t, angle) parameter space, built
        from the old paddle-tube vertices, so the coat painter, the fixed AO/normal maps and the bind all still work.
        The vertices welded to the body (the root hole) are kept and zipped to the first ring per island.
        """
        tc = self.cfg['tail']
        nside = tc['sides']
        step = 360.0 / nside
        V = len(A['X'])
        tail = A['tail'].astype(bool)
        tt, tp = A['tail_t'], A['tail_phi']
        isl = panda.uv_islands(tri, V)
        shared_w = np.zeros(winv.max() + 1, bool)
        shared_w[np.intersect1d(winv[tail], winv[~tail])] = True
        hole = tail & shared_w[winv]
        t_ring = tt[hole].max()
        tail_tri = tail[tri].all(1)
        phd = np.degrees(tp)
        islands = {}
        for I in np.unique(isl[tail]):
            m = (isl == I) & tail & (tt > t_ring + 0.12)      # the root region's angles are unreliable
            top = np.mean(np.cos(tp[m])) > 0
            ph = phd[m] if top else np.mod(phd[m], 360.0)
            ph = np.where(top, ph, np.where(ph < 89.0, ph + 360.0, ph))
            ph = np.clip(ph, -90, 90) if top else np.clip(ph, 90, 270)
            lo, hi = step * np.round(np.percentile(ph, 4) / step), step * np.round(np.percentile(ph, 96) / step)
            islands[I] = dict(top=top, lo=lo, hi=hi)
            self.log(f"  tail island {I}: {'top' if top else 'bottom'} {lo:.1f}..{hi:.1f} ({m.sum()} verts)")

        def phid_of(i, I):   # vertex angle in its island's continuous range ([-90,90] top, [90,270] bottom)
            p = phd[i]
            inf = islands[I]
            if not inf['top']:
                p = np.mod(p, 360.0)
                p = p + 360.0 if p < 89.0 else p
            return float(np.clip(p, inf['lo'], inf['hi']))

        # parameter-space triangles per island: (t, angle/180)
        ptri = {}
        for I in islands:
            ts = tri[tail_tri & (isl[tri[:, 0]] == I)]
            q = np.array([[[tt[v], phid_of(v, I) / 180.0] for v in t3] for t3 in ts])
            ptri[I] = (ts, q)

        def lookup(I, t, ph):
            ts, q = ptri[I]
            p = np.array([t, ph / 180.0])
            a, b, c = q[:, 0], q[:, 1], q[:, 2]
            v0, v1, v2 = b - a, c - a, p - a
            den = v0[:, 0] * v1[:, 1] - v1[:, 0] * v0[:, 1]
            den = np.where(np.abs(den) < 1e-12, 1e-12, den)
            w1 = (v2[:, 0] * v1[:, 1] - v1[:, 0] * v2[:, 1]) / den
            w2 = (v0[:, 0] * v2[:, 1] - v2[:, 0] * v0[:, 1]) / den
            w = np.stack([1 - w1 - w2, w1, w2], 1)
            k = np.argmax(w.min(1))
            ww = np.clip(w[k], 0, None); ww /= ww.sum()
            return ts[k], ww

        # smooth uv0 per island: least-squares bicubic in (t, angle) over the old paddle-tube vertices; unlike a
        # barycentric lookup in the irregular paddle triangulation it cannot fold (pass 3: no slanted ring patches)
        def feats(t, q):
            t = np.asarray(t, float); q = np.asarray(q, float)
            return np.stack([np.ones_like(t), t, t * t, t ** 3, q, q * t, q * t * t, q * q, q * q * t, q ** 3, q * t ** 3,
                             q * q * t * t], -1)
        uvfit = {}
        for I in islands:
            vi = np.nonzero((isl == I) & tail & ~hole)[0]
            F = feats(tt[vi], [phid_of(v, I) / 180.0 for v in vi])
            uvfit[I] = np.linalg.lstsq(F, A['at_uv0'][vi], rcond=None)[0]

        K = tc.get('rings', 14)
        t0 = t_ring + tc.get('first_ring', 0.05)
        s = np.linspace(0, 1, K)
        ring_t = t0 + (0.975 - t0) * (1 - (1 - s) ** tc.get('ring_bias', 1.35))
        new = {k: [] for k in A}
        new_par, new_w = [], []
        wkey = {}
        next_w = winv.max() + 1

        def add(I, t, ph, pole=False):
            nonlocal next_w
            tri3, ww = lookup(I, min(t, 0.999), ph)
            r = self.tail_radius(np.array([t]))[0]
            X_, U_, T_ = self.tail_frame(np.array([t]))
            rad = np.radians(ph)
            nrm = np.sin(rad) * X_[0] + np.cos(rad) * U_[0]
            pos = self.tail_centre(np.array([t]))[0] + r * nrm
            if pole:
                nrm = T_[0]
            for k in A:
                if k in ('X', 'P'):
                    new[k].append(pos)
                elif k == 'at_N':
                    new[k].append(nrm)
                elif k == 'at_uv0':
                    new[k].append(feats(min(t, 1.0), ph / 180.0) @ uvfit[I])
                elif k in ('teeth', 'arm', 'sole', 'ear_mask'):
                    new[k].append(False)
                elif k == 'tail':
                    new[k].append(True)
                elif k == 'w_head':
                    new[k].append(0.0)
                elif k == 'ear_rho':
                    new[k].append(1.0)
                elif k in ('ear_front', 'ear_cos'):
                    new[k].append(0.0)
                elif k == 'tail_t':
                    new[k].append(t)
                elif k == 'tail_phi':
                    new[k].append(np.radians(((ph + 180.0) % 360.0) - 180.0))
                elif k == 'tail_blend':
                    new[k].append(float(smoothstep(t_ring * 0.5, t_ring + tc['root_blend'], np.array(t))))
                else:
                    new[k].append(np.einsum('k,k...->...', ww, A[k][tri3]))
            d = {}
            for wgt, v in zip(ww, tri3):
                for kk, vv in parents[v].items():
                    d[kk] = d.get(kk, 0) + wgt * vv
            new_par.append(d)
            key = ('pole',) if pole else (round(t, 6), round(ph % 360.0, 3))
            if key not in wkey:
                wkey[key] = next_w; next_w += 1
            new_w.append(wkey[key])
            return V + len(new_par) - 1

        faces = []
        for I, inf in islands.items():
            phs = np.arange(inf['lo'], inf['hi'] + 1e-6, step)
            rings = [[add(I, t, ph) for ph in phs] for t in ring_t]
            pole = add(I, 1.0, 0.5 * (inf['lo'] + inf['hi']), pole=True)
            for a, b in zip(rings[:-1], rings[1:]):
                for j in range(len(phs) - 1):
                    faces += [[a[j], a[j + 1], b[j + 1]], [a[j], b[j + 1], b[j]]]
            for j in range(len(phs) - 1):
                faces.append([rings[-1][j], rings[-1][j + 1], pole])
            # zipper: the island's part of the root hole to the first ring
            hv = np.unique(tri[tail_tri & (isl[tri[:, 0]] == I)].ravel())
            hv = hv[hole[hv]]
            if len(hv) >= 1:
                fa = np.array([(phid_of(v, I) - inf['lo']) / max(inf['hi'] - inf['lo'], 1e-6) for v in hv])
                Al = list(hv[np.argsort(fa)]); fa = np.sort(fa)
                Bl = rings[0]; fb = (phs - inf['lo']) / max(inf['hi'] - inf['lo'], 1e-6)
                i = j = 0
                while i < len(Al) - 1 or j < len(Bl) - 1:
                    if j == len(Bl) - 1 or (i < len(Al) - 1 and fa[i + 1] <= fb[j + 1]):
                        faces.append([Al[i], Bl[j], Al[i + 1]]); i += 1
                    else:
                        faces.append([Al[i], Bl[j], Bl[j + 1]]); j += 1
        # assemble, drop the old paddle vertices (all tail vertices but the hole)
        for k in A:
            A[k] = np.concatenate([A[k], np.array(new[k]).reshape((len(new[k]),) + A[k].shape[1:]).astype(A[k].dtype)])
        parents = list(parents) + new_par
        winv = np.r_[winv, new_w]
        keep = np.ones(len(A['X']), bool)
        keep[np.nonzero(tail & ~hole)[0]] = False
        faces = np.array(faces)
        tri2 = np.vstack([tri[keep[tri].all(1)], faces])
        # outward winding (cross(p1-p0, p2-p0) points away from the tail axis)
        Xa = A['X']
        fc = Xa[faces].mean(1)
        tf = np.clip((self.cfg['tail_root'][2] - fc[:, 2]) / tc['length'], 0, 1)
        out = fc - self.tail_centre(tf)
        nrm = np.cross(Xa[faces[:, 1]] - Xa[faces[:, 0]], Xa[faces[:, 2]] - Xa[faces[:, 0]])
        flip = np.sum(nrm * out, 1) < 0
        faces[flip] = faces[flip][:, [0, 2, 1]]
        tri2 = np.vstack([tri[keep[tri].all(1)], faces])
        used = np.zeros(len(Xa), bool); used[tri2.ravel()] = True
        sel = np.nonzero(used)[0]
        remap = -np.ones(len(Xa), int); remap[sel] = np.arange(len(sel))
        for k in A:
            A[k] = A[k][sel]
        parents = [parents[i] for i in sel]
        winv = np.unique(winv[sel], return_inverse=True)[1]
        self.log(f"tail rebuilt: {nside} sides x {K} rings + pole, {int(A['tail'].sum())} tail verts "
                 f"(hole {int(hole.sum())}), {flip.sum()} faces flipped; verts {V} -> {len(sel)}")
        return A, remap[tri2], winv, parents

    def weld_fix(self, X, winv, tail):
        order = np.argsort(winv, kind='stable')
        ws = winv[order]
        starts = np.r_[0, np.nonzero(np.diff(ws))[0] + 1, len(ws)]
        worst = 0.0
        for a, b in zip(starts[:-1], starts[1:]):
            if b - a < 2:
                continue
            ids = order[a:b]
            spread = np.linalg.norm(X[ids] - X[ids].mean(0), axis=1).max()
            worst = max(worst, spread)
            body = ids[~tail[ids]]
            X[ids] = X[body].mean(0) if len(body) else X[ids].mean(0)
        self.log(f"weld fix: largest spread {worst:.5f}")
        return X

    # ------------------------------------------------------------ tail bones (slices of the beaver paddle)
    def bind_tail(self):
        s, cfg = self.s, self.cfg
        tc = cfg['tail']
        tr = cfg['tail_root']
        src = np.nonzero(self.tail_src)[0]
        L = np.clip(tr[2] - s.P[src, 2], 0, None)
        ts = L / L.max()
        K = tc['slices']
        tk = np.linspace(0, 1, K)
        sig = 1.0 / (K - 1)
        W = np.exp(-((ts[:, None] - tk[None, :]) / sig) ** 2)          # (Ns, K)
        # the first bone also holds the hips around the tail root, so the base follows the body
        hip = np.nonzero(~self.tail_src & ~self.teeth_src & (np.linalg.norm(s.P - np.array(tr), axis=1) < 0.06 * cfg['height'] / 0.53 * 1.6))[0]
        self.tb_src = np.r_[src, hip]
        Wh = np.zeros((len(hip), K)); Wh[:, 0] = 1.0
        self.tb_w = np.vstack([W, Wh]).T                                 # (K, Ns+Nh)
        self.tb_tk = tk
        self.log(f"tail bones: {K} slices over {len(src)} paddle + {len(hip)} hip verts")

    def tail_skin(self, Fsrc, t, Prest):
        """Fsrc (F,Vs,3) -> positions (F,n,3) of points with rest positions Prest at tail coordinate t."""
        X = self.s.P[self.tb_src]                     # (Ns,3)
        Y = Fsrc[:, self.tb_src]                      # (F,Ns,3)
        K = len(self.tb_tk)
        F = len(Fsrc)
        Xk = np.broadcast_to(X, (F, K) + X.shape)
        Yk = np.broadcast_to(Y[:, None], (F, K) + Y.shape[1:])
        w = np.broadcast_to(self.tb_w, (F, K, X.shape[0]))
        R, cx, cy = geom.kabsch_batch(Xk, Yk, w)      # (F,K,3,3), (F,K,3)
        # Curve deformer. Knots = where the paddle's slices put the red panda's own rest centreline (the paddle's path,
        # which the animators kept on or above the ground, lifted by the tube's rest offset). The tube follows a
        # Catmull-Rom curve through the knots with frames from the curve tangent and the slices' rotated "up"; the part
        # of the tail longer than the paddle rides rigidly on the last knot's frame. At rest this is the identity.
        tc = self.cfg['tail']
        tr = self.cfg['tail_root']
        cx0 = cx[0]
        tk = np.clip((tr[2] - cx0[:, 2]) / tc['length'], 0, 1)
        keep = np.r_[True, np.diff(tk) > 1e-3]
        # the paddle's last slices flap fast (a beaver's tail slap); a long bushy tail rides on a calmer frame
        drop = tc.get('drop_tip_knots', 1)
        if drop:
            keep[np.nonzero(keep)[0][-drop:]] = False
        tk, R, cx0, cy = tk[keep], R[:, keep], cx0[keep], cy[:, keep]
        K = len(tk)
        Qr = self.tail_centre(tk)                                     # (K,3) rest knots on our centreline
        Qf = cy + np.einsum('fkij,kj->fki', R, Qr - cx0)              # (F,K,3)
        _, Ur, _ = self.tail_frame(tk)
        Uf = np.einsum('fkij,kj->fki', R, Ur)                         # (F,K,3)

        def cr(Q, u):
            """Uniform Catmull-Rom through Q (...,K,3) at knot parameter u (n,) -> point and tangent (...,n,3)."""
            i = np.clip(np.floor(u).astype(int), 0, K - 2)
            s = np.clip(u - i, 0, 1)[..., :, None]
            P0 = Q[..., np.clip(i - 1, 0, K - 1), :]; P1 = Q[..., i, :]; P2 = Q[..., i + 1, :]; P3 = Q[..., np.clip(i + 2, 0, K - 1), :]
            m1 = 0.5 * (P2 - P0); m2 = 0.5 * (P3 - P1)
            s2, s3 = s * s, s * s * s
            pos = (2 * s3 - 3 * s2 + 1) * P1 + (s3 - 2 * s2 + s) * m1 + (-2 * s3 + 3 * s2) * P2 + (s3 - s2) * m2
            tan = (6 * s2 - 6 * s) * P1 + (3 * s2 - 4 * s + 1) * m1 + (-6 * s2 + 6 * s) * P2 + (3 * s2 - 2 * s) * m2
            return pos, tan

        def frames(Q, U, u):
            pos, tan = cr(Q, u)
            T = tan / np.linalg.norm(tan, axis=-1, keepdims=True).clip(1e-9)
            i = np.clip(np.floor(u).astype(int), 0, K - 2)
            s = np.clip(u - i, 0, 1)[:, None]
            Ui = U[..., i, :] * (1 - s) + U[..., i + 1, :] * s
            Ui = Ui - T * np.sum(Ui * T, -1, keepdims=True)
            Ui /= np.linalg.norm(Ui, axis=-1, keepdims=True).clip(1e-9)
            return pos, np.stack([T, Ui, np.cross(T, Ui)], -1)        # (...,n,3), (...,n,3,3) columns

        tt = np.clip(t, 0, 1)
        u = np.interp(tt, tk, np.arange(K))                           # knot parameter (clamped at both ends)
        pr, Fr = frames(Qr, Ur, u)
        pf, Ff = frames(Qf, Uf, u)
        A = np.einsum('fnij,nkj->fnik', Ff, Fr)                        # rotation rest frame -> current frame
        return pf + np.einsum('fnij,nj->fni', A, Prest - pr)

    def bind(self, **kw):
        super().bind(**kw)
        self.bind_tail()

    def transfer(self, Fsrc):
        out = super().transfer(Fsrc)
        tm = self.flags['tail']
        if tm.any():
            idx = np.nonzero(tm)[0]
            t = self.flags['tail_t'][idx]
            sk = self.tail_skin(Fsrc, t, self.P1[idx])
            wr = self.flags['tail_blend'][idx][None, :, None]
            out[:, idx] = out[:, idx] * (1 - wr) + sk * wr
            if getattr(self, 'ground', False):
                # in animations on the ground (feet at the origin) the thick tail rests on it instead of sinking in:
                # heights below h0 are squeezed smoothly into (0, h0] (C1 at h0), so the fur flattens on the ground
                h0 = self.cfg['tail'].get('ground_soft', 0.012) * self.cfg['scale']
                y = out[:, idx, 1]
                low = y < h0
                y[low] = h0 * np.exp((y[low] - h0) / h0)
                out[:, idx, 1] = y
        return out

    def set_animation(self, Fs):
        """Called once per animation with all its source frames: decides whether the ground is at the origin
        (the soles never go more than 4 cm below it), which switches the tail's ground contact on."""
        sole_y = Fs[:, self.sole_src, 1].min()
        self.ground = bool(sole_y > -0.04 * self.cfg['height'] / 0.53)
        return self.ground


def tail_uv1(t, phi):
    """Tail-decal UVs (the game samples _TailDecalDiffuse with uv1): the decal runs root->tip along the top of the
    tail and is mirrored underneath, as on the beaver's paddle (both faces share uv1). No seam."""
    a = np.abs(phi)
    fold = np.where(a <= 0.5 * np.pi, phi, np.sign(phi) * (np.pi - a))
    u = 0.5 + 0.30 * fold / (0.5 * np.pi)
    v = 0.04 + 0.92 * np.clip(t, 0, 1)
    return np.stack([u, v], 1)


def export_paint_data(b, path, extra=None):
    P1, tri = b.P1, b.tri
    N1 = geom.vertex_normals(P1, tri, b.sg)
    ear = b.ear_mask.astype(float)
    cav = getattr(b, 'cavity_tri', np.zeros(len(tri), bool)).astype(float)
    np.savez(path, P=P1, N=N1, tri=tri, uv0=b.at['uv0'], ear=ear, cavity=cav,
             darm=b.geo['darm'], dsole=b.geo['dsole'], head=b.w_head,
             tail=b.flags['tail'].astype(float), teeth=b.flags['teeth'].astype(float),
             sole=b.flags['sole'].astype(float), arm=b.flags['arm'].astype(float),
             tail_t=b.flags['tail_t'], tail_phi=b.flags['tail_phi'], ear_rho=b.flags['ear_rho'],
             ear_front=b.flags['ear_front'], ear_cos=b.flags['ear_cos'],
             ear_c1=b.ear_centre_1, ear_c2=getattr(b, 'ear_centre_-1'), stub=b.stub_centre, **(extra or {}))
