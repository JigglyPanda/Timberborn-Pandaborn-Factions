"""Dump vanilla built-in .timbermesh models (reference only; output stays on E:, never committed).

Usage: python -I src/pipeline/dump_vanilla_models.py <Timberborn_Data> <out dir> [name substring ...]
Writes <out>/<GameObject name>.timbermesh (the raw zlib bytes) for every model whose name contains any substring
(default: 'Folktails'), and <out>/index.json with per-model node names, vertex/triangle counts and materials.
"""
import json
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import UnityPy  # noqa: E402
import model_pb2 as pb  # noqa: E402


def main():
    data_dir, out = sys.argv[1:3]
    subs = sys.argv[3:] or ["Folktails"]
    os.makedirs(out, exist_ok=True)
    env = UnityPy.load(os.path.join(data_dir, "resources.assets"))
    by_id = {o.path_id: o for o in env.objects}
    index = {}
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
        if blob[:1] != b"\x78":
            continue
        try:
            m = pb.Model()
            m.ParseFromString(zlib.decompress(blob))
        except Exception:  # noqa: BLE001
            continue
        go = by_id.get(struct.unpack_from("<q", raw, 4)[0])
        name = go.peek_name() if go is not None else m.name
        if not any(s in name for s in subs):
            continue
        with open(os.path.join(out, name + ".timbermesh"), "wb") as f:
            f.write(blob)
        nodes = []
        tris = 0
        for nd in m.nodes:
            t = sum(len(me.indices) // 3 for me in nd.meshes)
            tris += t
            nodes.append({"name": nd.name, "parent": nd.parent, "verts": nd.vertexCount, "tris": t,
                          "pos": [round(nd.position.x, 3), round(nd.position.y, 3), round(nd.position.z, 3)],
                          "mats": [me.material for me in nd.meshes],
                          "nodeAnims": [(a.name, len(a.frames), a.framerate) for a in nd.nodeAnimations],
                          "vertAnims": [(a.name, len(a.frames)) for a in nd.vertexAnimations],
                          "props": [p.name for p in nd.vertexProperties]})
        index[name] = {"tris": tris, "nodes": nodes}
    with open(os.path.join(out, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, indent=1)
    print(len(index), "models ->", out)


if __name__ == "__main__":
    main()
