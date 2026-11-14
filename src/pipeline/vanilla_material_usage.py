"""Which materials do the vanilla timbermesh models use, and how much? (reference only; never commit the output)

The game's built-in models are GameObjects named like `Lodge.Folktails.Model` carrying a `BinaryData` MonoBehaviour
whose `_bytes` field is the .timbermesh file. Player builds carry no type trees, so the MonoBehaviour is parsed raw:
m_GameObject PPtr (12) + m_Enabled (4) + m_Script PPtr (12) + m_Name (empty string, 4) + byte[] (int32 length + data).

Writes <out>/material_usage.json: per model the triangles (and UV range) per material, plus totals per material over
models whose name contains each faction tag.

Usage: python -I src/pipeline/vanilla_material_usage.py <Timberborn_Data> <out dir>
"""
import collections
import gzip
import json
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import UnityPy  # noqa: E402
import model_pb2 as pb  # noqa: E402

DT = {1: np.uint8, 2: np.uint32, 3: np.int32, 4: np.float32, 5: np.float64}


def prop(props, name):
    for p in props:
        if p.name == name:
            a = np.frombuffer(p.data, dtype=DT[p.scalarType])
            return a.reshape(-1, p.scalarTypeDimension) if p.scalarTypeDimension > 1 else a
    return None


def decode(raw):
    try:
        data = gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else zlib.decompress(raw)
    except Exception:  # noqa: BLE001
        return None
    m = pb.Model()
    try:
        m.ParseFromString(data)
    except Exception:  # noqa: BLE001
        return None
    return m


def main():
    data_dir, out = sys.argv[1:3]
    env = UnityPy.load(os.path.join(data_dir, "resources.assets"))
    by_id = {o.path_id: o for o in env.objects}
    models = {}
    for o in env.objects:
        if o.type.name != "MonoBehaviour":
            continue
        raw = o.get_raw_data()
        if len(raw) < 40 or struct.unpack_from("<i", raw, 28)[0] != 0:
            continue
        n = struct.unpack_from("<i", raw, 32)[0]
        if n < 16 or n > len(raw) - 36:
            continue
        blob = raw[36:36 + n]
        if blob[:1] != b"\x78" and blob[:2] != b"\x1f\x8b":
            continue
        m = decode(blob)
        if m is None:
            continue
        go_id = struct.unpack_from("<q", raw, 4)[0]
        go = by_id.get(go_id)
        name = go.peek_name() if go is not None else m.name
        per_mat = collections.defaultdict(lambda: {"triangles": 0, "uvMin": [9, 9], "uvMax": [-9, -9], "colors": False})
        for node in m.nodes:
            uv = prop(node.vertexProperties, "uv0")
            col = prop(node.vertexProperties, "color")
            for mesh in node.meshes:
                idx = np.frombuffer(mesh.indices, dtype=np.uint32) if isinstance(mesh.indices, bytes) else np.array(mesh.indices)
                e = per_mat[mesh.material]
                e["triangles"] += len(idx) // 3
                if uv is not None and len(idx):
                    sel = uv[np.unique(idx)]
                    e["uvMin"] = np.minimum(e["uvMin"], sel.min(0)).round(3).tolist()
                    e["uvMax"] = np.maximum(e["uvMax"], sel.max(0)).round(3).tolist()
                if col is not None and len(idx):
                    c = col[np.unique(idx)]
                    if not np.allclose(c, 1.0, atol=0.01):
                        e["colors"] = True
                for extra in ("uv1", "uv2"):
                    if prop(node.vertexProperties, extra) is not None:
                        e[extra] = True
        models[name] = dict(per_mat)
    totals = collections.defaultdict(lambda: collections.Counter())
    counts = collections.defaultdict(lambda: collections.Counter())
    for name, mats in models.items():
        tag = "Folktails" if "Folktails" in name else "IronTeeth" if "IronTeeth" in name else "other"
        for mat, e in mats.items():
            totals[tag][mat] += e["triangles"]
            counts[tag][mat] += 1
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "material_usage.json"), "w", encoding="utf-8") as fh:
        json.dump({"models": models,
                   "totals": {t: dict(c.most_common()) for t, c in totals.items()},
                   "modelCounts": {t: dict(c.most_common()) for t, c in counts.items()}}, fh, indent=1)
    print(f"{len(models)} models")
    for tag in ("Folktails", "other"):
        print(f"== {tag}: material, models using it, triangles")
        for mat, tri in totals[tag].most_common(45):
            print(f"  {mat:45s} {counts[tag][mat]:4d} {tri:8d}")


if __name__ == "__main__":
    main()
