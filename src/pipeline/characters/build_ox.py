"""Build the Inkpaws' Wooden Ox bot (.timbermesh) from the vanilla Folktails bot.

usage: python -I build_ox.py <Bot.Folktails.Model.timbermesh> <OUT.timbermesh> [--only idle,walk]

The vanilla bot is 38 rigid wooden parts (head, eyes, ears, teeth, torso, limbs, five tail segments) whose vertex
animation moves each part as a rigid body (blinking eyelids aside). The ox keeps every node, every animation, the
material (`Bot.Folktails`, so it keeps the vanilla wood texture) and every UV island:
  * existing parts are moved or reshaped in rest space by a displacement d per vertex; in each frame the vertex goes to
    (its vanilla animated position) + R_part(frame) d, so the part keeps its exact motion (and the lids still blink);
  * new parts (horns, muzzle, nostrils, nose ring) are rigidly attached to a vanilla part (the head) and follow its
    per-frame rigid transform (Kabsch over the part's vertices, exact for rigid parts); their UVs are planar or
    cylindrical maps into existing wood / pale-metal islands of the vanilla texture;
  * normals and tangents of every frame are the rest ones turned by the part's rotation.
Deterministic: same inputs -> same bytes. The biped rig stays: an upright ox-headed automaton, not a quadruped.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402

import geom  # noqa: E402
import tmesh  # noqa: E402
import model_pb2 as pb  # noqa: E402
from ox_analyze import parts as split_parts  # noqa: E402


def half(a):
    return np.asarray(a, np.float32).astype(np.float16).astype(np.float32)


# UV rectangles (u0, v0, u1, v1) of islands in the vanilla bot texture (BotFolktails_2K_D), each with its painted rim
UV = dict(
    plank=(0.378, 0.283, 0.533, 0.536),      # long dark plank (tan rim)
    wood=(0.700, 0.640, 0.860, 0.810),       # mid-brown wood with grain
    pale=(0.095, 0.290, 0.150, 0.500),       # pale weathered metal / stone of the limbs
    dark=(0.386, 0.566, 0.418, 0.598),       # the dark socket
)


def rot(axis, deg):
    a = np.radians(deg)
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


# ------------------------------------------------------------------ new geometry (rest space, game axes)
class Geo:
    def __init__(self):
        self.P, self.N, self.uv, self.tri, self.smooth, self.owner = [], [], [], [], [], []
        self.role = None

    def add(self, P, N, uv, tri, smooth):
        base = sum(len(p) for p in self.P)
        self.P.append(np.asarray(P, float)); self.N.append(np.asarray(N, float)); self.uv.append(np.asarray(uv, float))
        self.tri.append(np.asarray(tri, int) + base); self.smooth.append(smooth)
        self.owner.append(np.full(len(P), self.role))

    def box(self, centre, half_size, R=np.eye(3), rect=UV['plank'], taper=None):
        """Box with one quad per face (hard edges); each face maps onto `rect`. taper=(sx, sy) shrinks the +z face."""
        c = np.asarray(centre, float); h = np.asarray(half_size, float)
        faces = [((0, 0, 1), (1, 0, 0), (0, 1, 0)), ((0, 0, -1), (-1, 0, 0), (0, 1, 0)),
                 ((1, 0, 0), (0, 0, -1), (0, 1, 0)), ((-1, 0, 0), (0, 0, 1), (0, 1, 0)),
                 ((0, 1, 0), (1, 0, 0), (0, 0, -1)), ((0, -1, 0), (1, 0, 0), (0, 0, 1))]
        u0, v0, u1, v1 = rect
        for n, a, b in faces:
            n, a, b = map(np.array, (n, a, b))
            q = []
            for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                p = n * h + a * su * h + b * sv * h
                if taper is not None and p[2] > 0:
                    p = p * np.array([taper[0], taper[1], 1.0])
                q.append(p)
            q = np.array(q) @ R.T + c
            fn = np.cross(q[1] - q[0], q[2] - q[0]); fn /= np.linalg.norm(fn)
            uv = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
            self.add(q, np.repeat(fn[None], 4, 0), uv, [[0, 1, 2], [0, 2, 3]], False)

    def tube(self, pts, radii, sides, rects, cap=True):
        """Smooth tube along a polyline; ring j gets the UV rect rects[j] (u around, v along)."""
        pts = np.asarray(pts, float)
        n = len(pts)
        T = np.gradient(pts, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True)
        ref = np.array([0, 0, 1.0]) if abs(T[0, 2]) < 0.9 else np.array([1.0, 0, 0])
        U = np.cross(T[0], ref); U /= np.linalg.norm(U)
        P, N, uv = [], [], []
        for j in range(n):
            U = U - T[j] * (U @ T[j]); U /= np.linalg.norm(U)
            W = np.cross(T[j], U)
            u0, v0, u1, v1 = rects[j]
            vv = v0 + (v1 - v0) * j / max(n - 1, 1)
            for k in range(sides + 1):
                a = 2 * np.pi * k / sides
                d = np.cos(a) * U + np.sin(a) * W
                P.append(pts[j] + radii[j] * d); N.append(d); uv.append((u0 + (u1 - u0) * k / sides, vv))
        tri = []
        for j in range(n - 1):
            for k in range(sides):
                a = j * (sides + 1) + k; b = a + sides + 1
                tri += [[a, a + 1, b], [a + 1, b + 1, b]]
        P = np.array(P); N = np.array(N)
        # winding outward
        t0 = tri[0]
        fn = np.cross(P[t0[1]] - P[t0[0]], P[t0[2]] - P[t0[0]])
        if fn @ N[t0[0]] < 0:
            tri = [[a, c, b] for a, b, c in tri]
        self.add(P, N, uv, tri, True)
        if cap and radii[-1] > 1e-4:
            c = pts[-1]; nrm = T[-1]
            ring = P[-(sides + 1):-1]
            cu = np.mean(rects[-1][0::2]), np.mean(rects[-1][1::2])
            Pc = np.vstack([ring, c[None]]); Nc = np.repeat(nrm[None], sides + 1, 0)
            uvc = [cu] * (sides + 1)
            tc = [[k, (k + 1) % sides, sides] for k in range(sides)]
            fn = np.cross(Pc[tc[0][1]] - Pc[tc[0][0]], Pc[tc[0][2]] - Pc[tc[0][0]])
            if fn @ nrm < 0:
                tc = [[a, c_, b] for a, b, c_ in tc]
            self.add(Pc, Nc, uvc, tc, False)

    def torus(self, centre, R, r, normal_axis, seg, sides, rect):
        c = np.asarray(centre, float)
        ax = np.asarray(normal_axis, float); ax /= np.linalg.norm(ax)
        e1 = np.cross(ax, [0, 1, 0] if abs(ax[1]) < 0.9 else [1, 0, 0]); e1 /= np.linalg.norm(e1)
        e2 = np.cross(ax, e1)
        P, N, uv = [], [], []
        u0, v0, u1, v1 = rect
        for i in range(seg + 1):
            a = 2 * np.pi * i / seg
            d = np.cos(a) * e1 + np.sin(a) * e2
            for k in range(sides + 1):
                b = 2 * np.pi * k / sides
                n = np.cos(b) * d + np.sin(b) * ax
                P.append(c + R * d + r * n); N.append(n); uv.append((u0 + (u1 - u0) * i / seg, v0 + (v1 - v0) * k / sides))
        tri = []
        for i in range(seg):
            for k in range(sides):
                a = i * (sides + 1) + k; b = a + sides + 1
                tri += [[a, b, a + 1], [a + 1, b, b + 1]]
        P = np.array(P); N = np.array(N)
        t0 = tri[0]
        fn = np.cross(P[t0[1]] - P[t0[0]], P[t0[2]] - P[t0[0]])
        if fn @ N[t0[0]] < 0:
            tri = [[a, c_, b] for a, b, c_ in tri]
        self.add(P, N, uv, tri, True)

    def arrays(self):
        return (np.vstack(self.P), np.vstack(self.N), np.vstack(self.uv), np.vstack(self.tri))


def tangents(P, N, uv, tri):
    t = geom.tangents_batch(P[None], N[None], uv, tri)[0]
    # handedness from the UV orientation of the triangles at each vertex
    e1 = P[tri[:, 1]] - P[tri[:, 0]]; e2 = P[tri[:, 2]] - P[tri[:, 0]]
    d1 = uv[tri[:, 1]] - uv[tri[:, 0]]; d2 = uv[tri[:, 2]] - uv[tri[:, 0]]
    det = d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1]
    det = np.where(np.abs(det) < 1e-12, 1e-12, det)
    bs = (e2 * d1[:, :1] - e1 * d2[:, :1]) / det[:, None]
    acc = np.zeros_like(P)
    for k in range(3):
        np.add.at(acc, tri[:, k], bs)
    w = np.sign(np.sum(np.cross(N, t) * acc, 1)); w[w == 0] = 1
    return np.c_[t, w]


# ------------------------------------------------------------------ the design
def find(P, lab, centre, tol=0.012):
    """The part whose bounding-box centre is nearest `centre` (asserting it is within tol)."""
    best, bd = None, 1e9
    for c in np.unique(lab):
        idx = lab == c
        bc = 0.5 * (P[idx].min(0) + P[idx].max(0))
        d = np.linalg.norm(bc - centre)
        if d < bd:
            best, bd = c, d
    assert bd < tol, (centre, bd)
    return best


def design(P, lab):
    """Returns (D: rest displacement per vanilla vertex, geo: new geometry, owner role per new block, roles)."""
    D = np.zeros_like(P)
    roles = {}
    roles['head'] = find(P, lab, (0, 0.4905, 0.1825))
    for s, sx in (('L', -1), ('R', 1)):
        roles['ear' + s] = find(P, lab, (sx * 0.0475, 0.5395, 0.125))
        roles['rim' + s] = find(P, lab, (sx * 0.0465, 0.522, 0.2455))
        roles['lid' + s] = find(P, lab, (sx * 0.046, 0.5225, 0.2505))
        roles['toe' + s] = find(P, lab, (sx * 0.144, 0.015, 0.12))
    roles['teeth'] = find(P, lab, (0, 0.447, 0.2585))
    tails = [find(P, lab, c) for c in ((0, 0.186, -0.116), (0, 0.159, -0.1645), (0, 0.1225, -0.241),
                                       (0, 0.086, -0.3185), (0, 0.049, -0.416))]
    roles['tail'] = tails

    def part(c):
        return np.nonzero(lab == c)[0]

    def move(idx, f):
        D[idx] = f(P[idx]) - P[idx]

    # head: a little broader and deeper, as a block
    hp = np.array([0, 0.43, 0.15])
    move(part(roles['head']), lambda X: hp + (X - hp) * np.array([1.12, 1.02, 1.06]))
    # eyes (rim + lid): out to the sides of the face, turned 30 degrees outward
    for s, sx in (('L', -1), ('R', 1)):
        idx = np.r_[part(roles['rim' + s]), part(roles['lid' + s])]
        c = 0.5 * (P[idx].min(0) + P[idx].max(0))
        Rz = rot((0, 1, 0), sx * 30)
        new_c = np.array([sx * 0.068, 0.533, 0.258])
        move(idx, lambda X, c=c, Rz=Rz, new_c=new_c: (X - c) @ Rz.T * 0.92 + new_c)
        # ears: flaps sticking out sideways under the horns, longer
        idx = part(roles['ear' + s])
        c = 0.5 * (P[idx].min(0) + P[idx].max(0))
        Rr = rot((0, 0, 1), -sx * 75) @ rot((1, 0, 0), -10)
        move(idx, lambda X, c=c, Rr=Rr, sx=sx: ((X - c) * np.array([1.0, 1.35, 1.0])) @ Rr.T + np.array([sx * 0.102, 0.512, 0.168]))
        # hooves: the toes shorter and taller (a blunt hoof)
        idx = part(roles['toe' + s])
        z0 = P[idx][:, 2].min()
        move(idx, lambda X, z0=z0: np.c_[X[:, 0], X[:, 1] * 1.35, z0 + (X[:, 2] - z0) * 0.72])
    # teeth -> a pale smile under the muzzle
    idx = part(roles['teeth'])
    c = 0.5 * (P[idx].min(0) + P[idx].max(0))
    move(idx, lambda X: (X - c) * np.array([1.35, 0.30, 0.55]) + np.array([0, 0.414, 0.300]))
    # tail: a thin rod of the same segments, ending in a tuft
    for j, t in enumerate(tails):
        idx = part(t)
        c = 0.5 * (P[idx].min(0) + P[idx].max(0))
        sx, sy, sz = (0.30, 0.55, 1.25) if j < len(tails) - 1 else (0.55, 0.95, 1.0)
        move(idx, lambda X, c=c, sx=sx, sy=sy, sz=sz: c + (X - c) * np.array([sx, sy, sz]))

    g = Geo()
    g.role = roles['head']
    # muzzle: a broad block in front of the face, tapering to the nose
    g.box((0, 0.448, 0.282), (0.070, 0.042, 0.036), rect=UV['plank'], taper=(0.90, 0.85))
    # nostrils
    for sx in (-1, 1):
        g.box((sx * 0.029, 0.456, 0.3175), (0.012, 0.009, 0.0035), rect=UV['dark'])
    # horns: out from the top of the head, then up and a little forward; wood, pale tips
    for sx in (-1, 1):
        t = np.linspace(0, 1, 9)
        pts = np.c_[sx * (0.078 + 0.095 * np.sin(t * np.pi * 0.55)), 0.552 + 0.115 * t ** 1.6, 0.165 + 0.035 * t ** 2]
        radii = 0.021 * (1 - 0.78 * t) + 0.002
        rects = [UV['wood'] if tj < 0.72 else UV['pale'] for tj in t]
        g.tube(pts, radii, 8, rects)
    # nose ring
    g.torus((0, 0.428, 0.323), 0.019, 0.0040, (0, 0, 1), 14, 6, UV['pale'])
    return D, g, roles


# ------------------------------------------------------------------ build
def build(src_path, out_path, only=None, log=print):
    t0 = time.time()
    model = tmesh.load(src_path)
    node = model.nodes[1]
    g_ = lambda k: tmesh.prop_array(node.vertexProperties, k).astype(np.float64)
    P, N, T, C, uv0, uv1 = g_('position'), g_('normal'), g_('tangent'), g_('color'), g_('uv0'), g_('uv1')
    tri = np.array(node.meshes[0].indices).reshape(-1, 3)
    material = node.meshes[0].material
    k, lab = split_parts(P, tri)
    D, geo, roles = design(P, lab)
    GP, GN, Guv, Gtri = geo.arrays()
    owner = np.concatenate(geo.owner).astype(int)
    V0 = len(P)
    P1 = np.vstack([P + D, GP])
    lab1 = np.r_[lab, owner].astype(int)
    tri1 = np.vstack([tri, Gtri + V0])
    uv0_1 = np.vstack([uv0, Guv])
    # uv1 of new vertices: the owner part's mean
    uv1_new = np.array([uv1[lab == o].mean(0) for o in owner])
    uv1_1 = np.vstack([uv1, uv1_new])
    C1 = np.vstack([C, np.ones((len(GP), 4))])
    # rest normals: vanilla ones turned by the part's rest edit (Kabsch of the moved part), new ones from the generator
    N1 = N.copy(); T1 = T.copy()
    for c in np.unique(lab):
        idx = lab == c
        if not np.any(D[idx]):
            continue
        R, _, _ = geom.kabsch_batch(P[idx], P[idx] + D[idx], np.ones(idx.sum()))
        N1[idx] = N[idx] @ R.T
        T1[idx, :3] = T[idx, :3] @ R.T
    GT = tangents(GP, GN, Guv, Gtri)
    N1 = np.vstack([N1, GN]); T1 = np.vstack([T1, GT])
    V = len(P1)

    node2 = model.nodes[1]
    del node2.vertexProperties[:]
    for name, arr in [('position', P1), ('normal', N1), ('tangent', T1), ('color', C1), ('uv0', uv0_1), ('uv1', uv1_1)]:
        node2.vertexProperties.append(tmesh.make_prop(name, arr))
    node2.vertexCount = V
    del node2.meshes[:]
    m = node2.meshes.add()
    m.indices.extend(tri1.ravel().tolist())
    m.material = material
    src_anims = list(tmesh.load(src_path).nodes[1].vertexAnimations)
    del node2.vertexAnimations[:]
    parts = np.unique(lab)
    keep = []
    nframes = 0
    for ai, a in enumerate(src_anims):
        if only and not any(a.name.endswith(o) for o in only):
            continue
        keep.append(ai)
        va = node2.vertexAnimations.add()
        va.name = a.name; va.framerate = a.framerate; va.animatedVertexCount = V
        for fr in a.frames:
            off = tmesh.prop_array(fr.vertexProperties, 'offset').astype(np.float64)
            Q = P.copy(); Q[:len(off)] += off
            out = np.empty((V, 3)); Nf = np.empty((V, 3)); Tf = np.empty((V, 3))
            for c in parts:
                idx0 = np.nonzero(lab == c)[0]
                R, cx, cy = geom.kabsch_batch(P[idx0], Q[idx0], np.ones(len(idx0)))
                out[idx0] = Q[idx0] + D[idx0] @ R.T
                idx1 = np.nonzero(lab1 == c)[0]
                new = idx1[idx1 >= V0]
                if len(new):
                    out[new] = (P1[new] - cx) @ R.T + cy
                Nf[idx1] = N1[idx1] @ R.T
                Tf[idx1] = T1[idx1, :3] @ R.T
            q = tmesh.frame_to_quat(Nf, Tf)
            f2 = va.frames.add()
            f2.vertexProperties.append(tmesh.make_prop('offset', half(out - P1)))
            f2.vertexProperties.append(tmesh.make_prop('rotation', half(q)))
            nframes += 1
    for n in model.nodes:
        if n is node2 or not len(n.nodeAnimations):
            continue
        kept = [pb.NodeAnimation() for _ in keep]
        for t_, i in zip(kept, keep):
            t_.CopyFrom(n.nodeAnimations[i])
        del n.nodeAnimations[:]
        for t_ in kept:
            n.nodeAnimations.add().CopyFrom(t_)
    sz = tmesh.save(model, out_path)
    log(f"wrote {out_path}: {V} verts ({V0} vanilla + {V - V0} new), {len(tri1)} tris, {len(keep)} anims, "
        f"{nframes} frames, {sz / 1e6:.1f} MB in {time.time() - t0:.0f}s")
    return model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('out')
    ap.add_argument('--only', default='')
    a = ap.parse_args()
    build(a.src, a.out, [o for o in a.only.split(',') if o] or None)


if __name__ == '__main__':
    main()
