"""Read .timbermesh files into flat numpy data (for previews, checks and comparisons).

`load(path)` returns a list of node dicts in Unity space with world matrices resolved, and `to_npz(path, out)` writes
the same data, converted to Blender space (x, y, z)_unity -> (-x, -z, y)_blender with triangle order reversed, for
`blender_preview.py` (Blender's Python has numpy but no protobuf).
"""
import json
import os
import sys
import zlib

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import model_pb2 as pb  # noqa: E402

_DT = {1: np.uint8, 2: np.uint32, 3: np.int32, 4: np.float32, 5: np.float64}


def _prop(node, name):
    for p in node.vertexProperties:
        if p.name == name and p.data:
            a = np.frombuffer(p.data, dtype=_DT[p.scalarType])
            return a.reshape(-1, p.scalarTypeDimension) if p.scalarTypeDimension > 1 else a
    return None


def quat_to_mat(q):
    x, y, z, w = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def trs(pos, rot, scale):
    m = np.eye(4)
    m[:3, :3] = quat_to_mat(rot) * np.asarray(scale)[None, :]
    m[:3, 3] = pos
    return m


def read_model(path):
    raw = open(path, "rb").read()
    m = pb.Model()
    m.ParseFromString(zlib.decompress(raw))
    return m


def load(path, frame=None):
    """Nodes with world matrices. frame: (animation name or None, normalized time) to pose animated nodes."""
    m = read_model(path)
    out = []
    for i, nd in enumerate(m.nodes):
        pos = (nd.position.x, nd.position.y, nd.position.z)
        rot = (nd.rotation.x, nd.rotation.y, nd.rotation.z, nd.rotation.w)
        scl = (nd.scale.x, nd.scale.y, nd.scale.z)
        if frame is not None and nd.nodeAnimations:
            an = nd.nodeAnimations[0]
            f = an.frames[int(frame * len(an.frames)) % len(an.frames)]
            pos = (f.position.x, f.position.y, f.position.z)
            rot = (f.rotation.x, f.rotation.y, f.rotation.z, f.rotation.w)
            scl = (f.scale.x, f.scale.y, f.scale.z)
        local = trs(pos, rot, scl)
        world = local if nd.parent < 0 else out[nd.parent]["world"] @ local
        d = {"name": nd.name, "parent": nd.parent, "world": world, "local": local, "count": nd.vertexCount,
             "P": _prop(nd, "position"), "N": _prop(nd, "normal"), "UV": _prop(nd, "uv0"), "C": _prop(nd, "color"),
             "meshes": [(me.material, np.asarray(me.indices, np.int64).reshape(-1, 3)) for me in nd.meshes],
             "nodeAnims": [(a.name, len(a.frames), a.framerate) for a in nd.nodeAnimations]}
        out.append(d)
    return out


def stats(path):
    nodes = load(path)
    tris = {}
    for n in nodes:
        for mat, idx in n["meshes"]:
            tris[mat] = tris.get(mat, 0) + len(idx)
    return {"triangles": sum(tris.values()), "perMaterial": tris,
            "vertices": sum(n["count"] for n in nodes), "nodes": [n["name"] for n in nodes]}


def to_npz(path, out, offset=(0.0, 0.0, 0.0), frame=None):
    """offset is in Unity space (x right, y up, z forward), applied before conversion."""
    nodes = load(path, frame)
    arrays, meta = {}, []
    k = 0
    for n in nodes:
        if n["P"] is None or not len(n["P"]):
            if n["name"].startswith("#Slot#"):
                p = n["world"][:3, 3] + np.asarray(offset)
                meta.append({"slot": n["name"], "pos": [float(-p[0]), float(-p[2]), float(p[1])]})
            continue
        W = n["world"]
        P = n["P"].astype(np.float64) @ W[:3, :3].T + W[:3, 3] + np.asarray(offset)
        N = n["N"].astype(np.float64) @ np.linalg.inv(W[:3, :3]) if n["N"] is not None else np.zeros_like(P)
        N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
        Pb = np.stack([-P[:, 0], -P[:, 2], P[:, 1]], 1)
        Nb = np.stack([-N[:, 0], -N[:, 2], N[:, 1]], 1)
        UV = n["UV"] if n["UV"] is not None else np.zeros((len(P), 2))
        C = n["C"] if n["C"] is not None else np.ones((len(P), 4))
        mats = []
        for j, (mat, idx) in enumerate(n["meshes"]):
            arrays[f"i{k}_{j}"] = idx[:, ::-1].astype(np.int32)
            mats.append(mat)
        arrays[f"P{k}"] = Pb.astype(np.float32)
        arrays[f"N{k}"] = Nb.astype(np.float32)
        arrays[f"UV{k}"] = np.asarray(UV, np.float32)
        arrays[f"C{k}"] = np.asarray(C, np.float32)
        meta.append({"node": n["name"], "k": k, "mats": mats})
        k += 1
    arrays["meta"] = np.frombuffer(json.dumps(meta).encode(), np.uint8)
    np.savez_compressed(out, **arrays)
    return out
