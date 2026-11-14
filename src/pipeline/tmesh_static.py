"""Static (non-animated) .timbermesh writer, no Blender needed.

Format facts (verified against the shipped BerryJam JamStove files and the decompiled game):
  * file = zlib.compress(Model.SerializeToString(), 6); game demands header bytes 78 9C.
  * Model.version=0, Model.name=''. Node 0 is the model root (parent -1, identity transform);
    '#Slot#<Name>' empties are child nodes (parent 0) with no vertices, only position/rotation.
  * Each node with vertices carries FLOAT vertexProperties: position(3) normal(3) tangent(4) color(4) uv0(2).
    The game only reads properties by name; any may be missing (the 590-vertex construction stage in JamStove
    has position/color/uv0 only). Vertex count is node.vertexCount; indices are int32 (UInt16 if <=65535 verts).
  * One Mesh (submesh) per material; Mesh.material is the Unity material name, e.g. 'BaseWood_Brown.Folktails'.
    A name not in the faction's material collections (+Common) throws in-game; '' maps to Materials/Common/Empty.
  * Coordinates are in Unity space (X right, Y up, Z forward, left-handed, 1 unit = 1 tile edge).
    Blender -> Unity is (x, y, z) -> (-x, z, -y) and triangle order reversed.
  * Winding (verified on JamStove, 100% of triangles): np.cross(b - a, c - a) points the SAME way as the
    outward vertex normal.
  * tangent.xyz = dP/du; tangent.w = sign(dot(cross(normal, tangent), dP/dv)) (verified, 100% match; JamStove
    values are mostly -1).
  * color = baked AO / tint in [0, 1], alpha 1 (white = unshaded).

Usage:  from tmesh_static import StaticNode, write_model, box_faces, build_crate
        python -I tmesh_static.py OUT.timbermesh      (writes the demo 1x1 crate)
"""
import os
import sys
import zlib
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import model_pb2 as pb


@dataclass
class StaticNode:
    name: str
    parent: int = -1
    position: tuple = (0.0, 0.0, 0.0)
    rotation: tuple = (0.0, 0.0, 0.0, 1.0)      # quaternion x, y, z, w (Unity space)
    scale: tuple = (1.0, 1.0, 1.0)
    positions: np.ndarray = None                # (N,3) float32
    normals: np.ndarray = None                  # (N,3)
    tangents: np.ndarray = None                 # (N,4) or None -> computed from uv0 when uv0 given
    colors: np.ndarray = None                   # (N,4) or None -> omitted
    uv0: np.ndarray = None                      # (N,2)
    uv1: np.ndarray = None
    uv2: np.ndarray = None
    meshes: list = field(default_factory=list)  # [(material_name, (M,3) int triangle indices)]


def compute_tangents(P, N, UV, tris):
    """Per-vertex tangent (xyz = dP/du, w = handedness) accumulated over triangles, Gram-Schmidt vs normal."""
    P, N, UV = (np.asarray(a, dtype=np.float64) for a in (P, N, UV))
    tan = np.zeros_like(P)
    bit = np.zeros_like(P)
    for t in tris:
        a, b, c = t
        e1, e2 = P[b] - P[a], P[c] - P[a]
        d1, d2 = UV[b] - UV[a], UV[c] - UV[a]
        det = d1[0] * d2[1] - d2[0] * d1[1]
        if abs(det) < 1e-12:
            continue
        tu = (e1 * d2[1] - e2 * d1[1]) / det
        bv = (e2 * d1[0] - e1 * d2[0]) / det
        for v in t:
            tan[v] += tu
            bit[v] += bv
    tan -= N * np.sum(N * tan, axis=1, keepdims=True)
    ln = np.linalg.norm(tan, axis=1, keepdims=True)
    fallback = np.where(np.abs(N[:, :1]) < 0.9, [[1.0, 0, 0]], [[0, 1.0, 0]])
    fallback = fallback - N * np.sum(N * fallback, axis=1, keepdims=True)
    tan = np.where(ln > 1e-9, tan / np.maximum(ln, 1e-12), fallback / np.linalg.norm(fallback, axis=1, keepdims=True))
    w = np.where(np.sum(np.cross(N, tan) * bit, axis=1) < 0, -1.0, 1.0)
    return np.concatenate([tan, w[:, None]], axis=1).astype(np.float32)


def check_winding(P, N, tris):
    """Return fraction of triangles whose cross(b-a, c-a) agrees with the mean vertex normal."""
    P, N = np.asarray(P, dtype=np.float64), np.asarray(N, dtype=np.float64)
    ok = total = 0
    for a, b, c in tris:
        g = np.cross(P[b] - P[a], P[c] - P[a])
        if np.linalg.norm(g) < 1e-12:
            continue
        total += 1
        ok += np.dot(g, N[a] + N[b] + N[c]) > 0
    return ok / max(total, 1)


def _prop(name, arr, dim):
    arr = np.ascontiguousarray(arr, dtype='<f4').reshape(-1, dim)
    p = pb.VertexProperty()
    p.name = name
    p.scalarType = pb.SCALAR_TYPE_FLOAT
    p.scalarTypeDimension = dim
    p.data = arr.tobytes()
    return p


def build_model(nodes):
    m = pb.Model()
    m.version = 0
    m.name = ''
    for n in nodes:
        x = m.nodes.add()
        x.parent = n.parent
        x.name = n.name
        x.position.x, x.position.y, x.position.z = n.position
        x.rotation.x, x.rotation.y, x.rotation.z, x.rotation.w = n.rotation
        x.scale.x, x.scale.y, x.scale.z = n.scale
        count = 0 if n.positions is None else len(n.positions)
        x.vertexCount = count
        tangents = n.tangents
        if tangents is None and count and n.uv0 is not None:
            tris = np.concatenate([np.asarray(t).reshape(-1, 3) for _, t in n.meshes]) if n.meshes else []
            tangents = compute_tangents(n.positions, n.normals, n.uv0, tris)
        # Property order matches the official exporter: position, normal, tangent, color, uv0, uv1, uv2.
        # Nodes without vertices (slots) still get the three empty geometry properties, as the exporter does.
        x.vertexProperties.append(_prop('position', n.positions if count else np.zeros((0, 3)), 3))
        x.vertexProperties.append(_prop('normal', n.normals if count else np.zeros((0, 3)), 3))
        x.vertexProperties.append(_prop('tangent', tangents if count else np.zeros((0, 4)), 4))
        if count:
            for name, arr, dim in (('color', n.colors, 4), ('uv0', n.uv0, 2), ('uv1', n.uv1, 2), ('uv2', n.uv2, 2)):
                if arr is not None:
                    assert len(arr) == count, name
                    x.vertexProperties.append(_prop(name, arr, dim))
        for material, tris in n.meshes:
            me = x.meshes.add()
            me.material = material
            me.indices.extend(int(i) for i in np.asarray(tris).reshape(-1))
    return m


def write_model(path, nodes):
    data = zlib.compress(build_model(nodes).SerializeToString(), 6)
    assert data[:2] == b'\x78\x9c'
    with open(path, 'wb') as f:
        f.write(data)
    return len(data)


# ------------------------------------------------------------------ geometry helpers
_BOX = [  # (outward normal, u axis, v axis) per face; u x v = normal direction depends on handedness, fixed below
    ((1, 0, 0), (0, 0, 1), (0, 1, 0)), ((-1, 0, 0), (0, 0, -1), (0, 1, 0)),
    ((0, 1, 0), (1, 0, 0), (0, 0, 1)), ((0, -1, 0), (1, 0, 0), (0, 0, -1)),
    ((0, 0, 1), (-1, 0, 0), (0, 1, 0)), ((0, 0, -1), (1, 0, 0), (0, 1, 0)),
]


def box_faces(lo, hi, uv_rect=(0, 0, 1, 1), color=1.0):
    """Axis-aligned box lo..hi (Unity space). Returns positions, normals, uv0, colors, triangles.
    24 vertices (hard edges), 12 triangles, every face maps to uv_rect = (u0, v0, u1, v1)."""
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    c, h = (lo + hi) / 2, (hi - lo) / 2
    u0, v0, u1, v1 = uv_rect
    P, N, UV, T = [], [], [], []
    for nrm, ua, va in _BOX:
        nrm, ua, va = (np.array(a, float) for a in (nrm, ua, va))
        for su, sv, uu, vv in ((-1, -1, u0, v0), (1, -1, u1, v0), (1, 1, u1, v1), (-1, 1, u0, v1)):
            P.append(c + h * (nrm + su * ua + sv * va))
            N.append(nrm)
            UV.append((uu, vv))
        base = len(P) - 4
        tri = [(base, base + 1, base + 2), (base, base + 2, base + 3)]
        # enforce the game's winding: cross(b-a, c-a) along the outward normal
        for t in tri:
            g = np.cross(P[t[1]] - P[t[0]], P[t[2]] - P[t[0]])
            T.append(t if np.dot(g, nrm) > 0 else (t[0], t[2], t[1]))
    col = np.full((len(P), 4), color, np.float32)
    col[:, 3] = 1.0
    return (np.array(P, np.float32), np.array(N, np.float32), np.array(UV, np.float32), col,
            np.array(T, np.int32))


def build_crate(material='BaseWood_Brown.Folktails', with_slot=True):
    """1x1x1 crate on a single tile: footprint x,z in [0,1], height y in [0,1]; one material."""
    P, N, UV, C, T = box_faces((0, 0, 0), (1, 1, 1))
    nodes = [StaticNode(' Crate.Model', -1, positions=P, normals=N, colors=C, uv0=UV, meshes=[(material, T)])]
    if with_slot:   # entrance slot on the -Z side, facing outwards like JamStove's (rotation y = 180 deg)
        nodes.append(StaticNode('#Slot#Entrance', 0, position=(0.5, 0.0, 0.0), rotation=(0.0, -1.0, 0.0, 0.0),
                                positions=None, meshes=[]))
    return nodes


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'Crate.Model.timbermesh'
    print('wrote', out, write_model(out, build_crate()), 'bytes')
