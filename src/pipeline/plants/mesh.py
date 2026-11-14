"""Plant geometry: a small mesh bag with the four vertex streams vegetation needs, primitives and the .timbermesh writer.

Space is Unity's (x right, y up, z forward; 1 unit = 1 tile edge). A plant fills the cell x, z in [0, 1] standing on
y = 0 (the game centres it on (0.5, 0, 0.5) for its random rotation, NaturalResourceModel). Every vertex carries:

* uv0  - the albedo atlas (src/pipeline/plants/atlas.py), cut-out by alpha;
* uv1  - wind: VegetationURP's ComputeWindOffset sways a vertex by uv1.y (0 = rooted, 1 = free tip), x is unused
         (vanilla fills it with a planar coordinate; we store a per-part random so it stays meaningful);
* uv2  - the detail atlas: where the yield shows when the gatherable has one (`_EnableDetail` = 1). Vertices of a part
         that is never yield get UV2_NONE, a transparent texel;
* colour - multiplies the albedo: the leaf hue (the atlas leaves are near-grey like vanilla's), dry and dead tints,
           ground occlusion and per-part variation.

The writer reuses src/pipeline/tmesh_static.py (format facts there). Never edit src/pipeline/kit (another lane's).
"""
import json
import math
import os
import sys
import zlib

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
import tmesh_static as ts  # noqa: E402

UV2_NONE = (0.004, 0.004)   # a transparent corner texel of the detail atlas


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def rot_axis(axis, ang):
    a = np.asarray(axis, float)
    a = a / np.linalg.norm(a)
    x, y, z = a
    c, s = math.cos(ang), math.sin(ang)
    C = 1 - c
    return np.array([[c + x * x * C, x * y * C - z * s, x * z * C + y * s],
                     [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
                     [z * x * C - y * s, z * y * C + x * s, c + z * z * C]])


def basis_from(direction, up=(0, 1, 0)):
    """Columns (side, normal-ish, direction) with direction as the local +y axis of a part."""
    d = np.asarray(direction, float)
    d = d / np.linalg.norm(d)
    u = np.asarray(up, float)
    if abs(np.dot(u, d)) > 0.97:
        u = np.array([1.0, 0, 0]) if abs(d[0]) < 0.9 else np.array([0, 0, 1.0])
    s = np.cross(d, u)
    s /= np.linalg.norm(s)
    n = np.cross(s, d)
    return np.stack([s, d, n], 1)


class Mesh:
    """Vertices with P, N, uv0, uv1, uv2, colour; triangles. One material per Mesh (a plant uses one material)."""

    def __init__(self, material):
        self.material = material
        self.P, self.N, self.U0, self.U1, self.U2, self.C, self.T = [], [], [], [], [], [], []
        self.n = 0

    # ------------------------------------------------------------------ raw
    def add(self, P, N, U0, T, U1=None, U2=None, C=None):
        P = np.asarray(P, float)
        k = len(P)
        N = np.asarray(N, float)
        if N.ndim == 1:
            N = np.tile(N, (k, 1))
        N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
        U0 = np.asarray(U0, float)
        U1 = np.zeros((k, 2)) if U1 is None else np.asarray(U1, float)
        if U2 is None:
            U2 = np.tile(UV2_NONE, (k, 1))
        U2 = np.asarray(U2, float)
        if U2.ndim == 1:
            U2 = np.tile(U2, (k, 1))
        C = np.ones((k, 4)) if C is None else np.asarray(C, float)
        if C.ndim == 1:
            C = np.tile(np.concatenate([C[:3], [1.0]]) if len(C) >= 3 else C, (k, 1))
        if C.shape[1] == 3:
            C = np.concatenate([C, np.ones((k, 1))], 1)
        T = np.asarray(T, int) + self.n
        self.P.append(P), self.N.append(N), self.U0.append(U0), self.U1.append(U1), self.U2.append(U2)
        self.C.append(C), self.T.append(T)
        self.n += k
        return slice(self.n - k, self.n)

    def extend(self, other, R=None, t=(0, 0, 0)):
        if other.n == 0:
            return
        P, N, U0, U1, U2, C, T = other.arrays()
        R = np.eye(3) if R is None else np.asarray(R, float)
        self.add(P @ R.T + np.asarray(t, float), N @ R.T, U0, T if np.linalg.det(R) > 0 else T[:, ::-1], U1, U2, C)

    def arrays(self):
        if not self.n:
            z = np.zeros((0, 3))
            return z, z, np.zeros((0, 2)), np.zeros((0, 2)), np.zeros((0, 2)), np.zeros((0, 4)), np.zeros((0, 3), int)
        return (np.concatenate(self.P), np.concatenate(self.N), np.concatenate(self.U0), np.concatenate(self.U1),
                np.concatenate(self.U2), np.concatenate(self.C), np.concatenate(self.T))

    @property
    def triangles(self):
        return sum(len(t) for t in self.T)

    def tint(self, rgb, where=None):
        """Multiply colours (all, or the vertices of slice `where`)."""
        P, N, U0, U1, U2, C, T = self.arrays()
        sl = slice(None) if where is None else where
        C[sl, :3] *= np.asarray(rgb, float)[None, :]
        self._set(P, N, U0, U1, U2, C, T)

    def _set(self, P, N, U0, U1, U2, C, T):
        self.P, self.N, self.U0, self.U1, self.U2, self.C, self.T = [P], [N], [U0], [U1], [U2], [C], [T]
        self.n = len(P)

    def map_colors(self, fn):
        P, N, U0, U1, U2, C, T = self.arrays()
        C = fn(P, N, U0, U1, C)
        self._set(P, N, U0, U1, U2, C, T)

    def bounds(self):
        P = self.arrays()[0]
        return P.min(0), P.max(0)

    # ------------------------------------------------------------------ primitives
    def quad(self, corners, uv_rect, normal=None, sway=(0, 0, 1, 1), uv2=None, color=None, two_sided=False, bend=None):
        """corners: bottom-left, bottom-right, top-right, top-left (front view). uv_rect (u0, v0, u1, v1) maps bottom
        to v0 and top to v1. sway (b0, b1, t0, t1): uv1.y at bottom-left/right, top-right/left... given as
        (bottom, bottom, top, top) weights. uv2: (u0, v0, u1, v1) detail rect or None."""
        P = np.asarray(corners, float)
        n = np.cross(P[1] - P[0], P[3] - P[0]) if normal is None else np.asarray(normal, float)
        n = n / max(np.linalg.norm(n), 1e-12)
        u0, v0, u1, v1 = uv_rect
        UV = np.array([[u0, v0], [u1, v0], [u1, v1], [u0, v1]])
        sb0, sb1, st0, st1 = sway
        U1 = np.array([[0, sb0], [0, sb1], [0, st0], [0, st1]], float)
        U2 = None
        if uv2 is not None:
            a0, b0, a1, b1 = uv2
            U2 = np.array([[a0, b0], [a1, b0], [a1, b1], [a0, b1]])
        N = np.tile(n, (4, 1))
        if bend is not None:            # vertex normals tilted outward from the card centre: softer, rounder light
            c = P.mean(0)
            N = N + bend * (P - c) / max(np.linalg.norm(P - c, axis=1).max(), 1e-9)
        T = np.array([[0, 1, 2], [0, 2, 3]])
        if np.dot(np.cross(P[1] - P[0], P[2] - P[0]), n) < 0:
            T = T[:, ::-1]
        self.add(P, N, UV, T, U1, U2, color)
        if two_sided:
            self.add(P, -N, UV, T[:, ::-1], U1, U2, color)

    def strip(self, spine, widths, normals, uv_rect, sway, color=None, two_sided=True, uv2=None, sides=None):
        """A ribbon along `spine` (k points), width per point, facing `normals` (k vectors). uv maps across = u, along = v.
        sway: k weights. sides: k unit vectors across the ribbon (default: cross(tangent, normal))."""
        S = np.asarray(spine, float)
        k = len(S)
        W = np.asarray(widths, float)
        Nn = np.asarray(normals, float)
        if Nn.ndim == 1:
            Nn = np.tile(Nn, (k, 1))
        tan = np.gradient(S, axis=0)
        tan /= np.maximum(np.linalg.norm(tan, axis=1, keepdims=True), 1e-9)
        if sides is None:
            side = np.cross(tan, Nn)
            side /= np.maximum(np.linalg.norm(side, axis=1, keepdims=True), 1e-9)
        else:
            side = np.asarray(sides, float)
        Nf = np.cross(side, tan)
        Nf /= np.maximum(np.linalg.norm(Nf, axis=1, keepdims=True), 1e-9)
        L = S - side * W[:, None] / 2
        Rr = S + side * W[:, None] / 2
        P = np.concatenate([L, Rr])
        u0, v0, u1, v1 = uv_rect
        t = np.linspace(0, 1, k)
        UV = np.concatenate([np.stack([np.full(k, u0), v0 + (v1 - v0) * t], 1),
                             np.stack([np.full(k, u1), v0 + (v1 - v0) * t], 1)])
        sw = np.asarray(sway, float)
        U1 = np.stack([np.zeros(2 * k), np.concatenate([sw, sw])], 1)
        U2 = None
        if uv2 is not None:
            a0, b0, a1, b1 = uv2
            U2 = np.concatenate([np.stack([np.full(k, a0), b0 + (b1 - b0) * t], 1),
                                 np.stack([np.full(k, a1), b0 + (b1 - b0) * t], 1)])
        N = np.concatenate([Nf, Nf])
        T = []
        for i in range(k - 1):
            a, b, c, d = i, i + 1, k + i + 1, k + i
            T += [[a, c, b], [a, d, c]]
        T = np.array(T)
        # orient so the geometric normal agrees with N
        g = np.cross(P[T[0, 1]] - P[T[0, 0]], P[T[0, 2]] - P[T[0, 0]])
        if np.dot(g, N[T[0, 0]]) < 0:
            T = T[:, ::-1]
        self.add(P, N, UV, T, U1, U2, color)
        if two_sided:
            self.add(P, -N, UV, T[:, ::-1], U1, U2, color)

    def tube(self, path, radii, sides, uv_rect, sway, color=None, cap_top=None, cap_bottom=False, twist=0.0,
             v_repeat=None, open_ends=False):
        """A tapered n-gon prism along `path` (k points). uv: circumference across u (u0..u1), length along v. v_repeat:
        world length per full v range (None = stretch once). cap_top: (cx, cy, r) disc in the atlas for a flat end."""
        S = np.asarray(path, float)
        k = len(S)
        R = np.asarray(radii, float)
        tan = np.gradient(S, axis=0)
        tan /= np.maximum(np.linalg.norm(tan, axis=1, keepdims=True), 1e-9)
        ref = np.array([1.0, 0, 0]) if abs(tan[0][0]) < 0.9 else np.array([0, 0, 1.0])
        P, N, UV, U1 = [], [], [], []
        u0, v0, u1, v1 = uv_rect
        acc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(S, axis=0), axis=1))])
        vv = acc / (v_repeat if v_repeat else max(acc[-1], 1e-9))
        sw = np.asarray(sway, float)
        x = ref - tan[0] * np.dot(ref, tan[0])
        x /= np.linalg.norm(x)
        for i in range(k):
            t = tan[i]
            x = x - t * np.dot(x, t)
            x /= np.linalg.norm(x)
            y = np.cross(t, x)
            for j in range(sides + 1):
                a = 2 * math.pi * j / sides + twist * i
                d = math.cos(a) * x + math.sin(a) * y
                P.append(S[i] + d * R[i])
                N.append(d)
                UV.append((u0 + (u1 - u0) * j / sides, v0 + (v1 - v0) * (vv[i] % 1.0000001 if v_repeat else vv[i])))
                U1.append((0, sw[i]))
        T = []
        m = sides + 1
        for i in range(k - 1):
            for j in range(sides):
                a, b, c, d = i * m + j, i * m + j + 1, (i + 1) * m + j + 1, (i + 1) * m + j
                T += [[a, b, c], [a, c, d]]
        T = np.array(T)
        P, N = np.array(P), np.array(N)
        g = np.cross(P[T[0, 1]] - P[T[0, 0]], P[T[0, 2]] - P[T[0, 0]])
        if np.dot(g, N[T[0, 0]]) < 0:
            T = T[:, ::-1]
        self.add(P, N, np.array(UV), T, np.array(U1), None, color)
        if cap_top is not None:
            self.disc(S[-1], tan[-1], R[-1], sides, cap_top, sw[-1], color)
        if cap_bottom and cap_top is not None:
            self.disc(S[0], -tan[0], R[0], sides, cap_top, sw[0], color)

    def disc(self, centre, normal, radius, sides, uv_disc, sway=0.0, color=None):
        cx, cy, r = uv_disc
        n = np.asarray(normal, float)
        n /= np.linalg.norm(n)
        ref = np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 0, 1.0])
        x = ref - n * np.dot(ref, n)
        x /= np.linalg.norm(x)
        y = np.cross(n, x)
        P = [np.asarray(centre, float)]
        UV = [(cx, cy)]
        for j in range(sides):
            a = 2 * math.pi * j / sides
            P.append(centre + radius * (math.cos(a) * x + math.sin(a) * y))
            UV.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        T = np.array([[0, 1 + j, 1 + (j + 1) % sides] for j in range(sides)])
        P = np.array(P)
        g = np.cross(P[T[0, 1]] - P[T[0, 0]], P[T[0, 2]] - P[T[0, 0]])
        if np.dot(g, n) < 0:
            T = T[:, ::-1]
        self.add(P, n, np.array(UV), T, np.tile((0, sway), (len(P), 1)), None, color)


# ------------------------------------------------------------------------------------------------ writer
def write(path, mesh, root_name):
    """Writes one node (the model root) with one submesh. Returns stats."""
    P, N, U0, U1, U2, C, T = mesh.arrays()
    U0 = np.clip(U0, 0.0, 1.0)
    node = ts.StaticNode(root_name, -1, positions=P.astype(np.float32), normals=N.astype(np.float32),
                         colors=np.clip(C, 0, 1).astype(np.float32), uv0=U0.astype(np.float32),
                         uv1=U1.astype(np.float32), uv2=U2.astype(np.float32), meshes=[(mesh.material, T)])
    model = ts.build_model([node])
    data = zlib.compress(model.SerializeToString(), 6)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    lo, hi = (P.min(0), P.max(0)) if len(P) else (np.zeros(3), np.zeros(3))
    return {"triangles": int(len(T)), "vertices": int(len(P)), "bboxMin": np.round(lo, 3).tolist(),
            "bboxMax": np.round(hi, 3).tolist(), "uv0": [float(U0.min()), float(U0.max())] if len(U0) else None}


# ------------------------------------------------------------------------------------------------ preview export
def read_streams(path):
    """Any .timbermesh (ours or vanilla) -> list of (material, P, N, uv0, uv2, colour, tris) per mesh, model space."""
    sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "kit"))
    import tmio  # noqa: E402  (read-only use of the kit's reader)
    m = tmio.read_model(path)
    out = []
    worlds = []
    for i, nd in enumerate(m.nodes):
        local = tmio.trs((nd.position.x, nd.position.y, nd.position.z),
                         (nd.rotation.x, nd.rotation.y, nd.rotation.z, nd.rotation.w), (nd.scale.x, nd.scale.y, nd.scale.z))
        W = local if nd.parent < 0 else worlds[nd.parent] @ local
        worlds.append(W)
        P = tmio._prop(nd, "position")
        if P is None or not len(P):
            continue
        P = P.astype(float) @ W[:3, :3].T + W[:3, 3]
        N = tmio._prop(nd, "normal")
        N = np.zeros_like(P) if N is None else N.astype(float) @ W[:3, :3].T
        U0 = tmio._prop(nd, "uv0")
        U2 = tmio._prop(nd, "uv2")
        C = tmio._prop(nd, "color")
        k = len(P)
        U0 = np.zeros((k, 2)) if U0 is None else U0
        U2 = np.tile(UV2_NONE, (k, 1)) if U2 is None else U2
        C = np.ones((k, 4)) if C is None else C
        for me in nd.meshes:
            out.append((me.material, P, N, U0, U2, C, np.asarray(me.indices, np.int64).reshape(-1, 3)))
    return out


def to_blender_npz(path, out):
    """Blender space (x, y, z)_unity -> (-x, -z, y), triangle order reversed. Several meshes -> k0, k1..."""
    arrays, meta = {}, []
    for k, (mat, P, N, U0, U2, C, T) in enumerate(read_streams(path)):
        arrays[f"P{k}"] = np.stack([-P[:, 0], -P[:, 2], P[:, 1]], 1).astype(np.float32)
        arrays[f"N{k}"] = np.stack([-N[:, 0], -N[:, 2], N[:, 1]], 1).astype(np.float32)
        arrays[f"UV{k}"] = np.asarray(U0, np.float32)
        arrays[f"UVD{k}"] = np.asarray(U2, np.float32)
        arrays[f"C{k}"] = np.asarray(C, np.float32)
        arrays[f"T{k}"] = T[:, ::-1].astype(np.int32)
        meta.append({"k": k, "mat": mat})
    arrays["meta"] = np.frombuffer(json.dumps(meta).encode(), np.uint8)
    np.savez_compressed(out, **arrays)
    return out
