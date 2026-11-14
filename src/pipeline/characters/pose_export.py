"""Export posed frames of character .timbermesh files to one .npz for the Blender preview renderer.

Runs in the venv (numpy + protobuf); Blender only needs numpy to read the result.

usage: python -I pose_export.py scene.json
scene.json: {"out_npz": "...", "items": [{"model": "...timbermesh", "anim": "walk", "frame": 6,
             "texture": "...png", "offset": [x, z], "yaw": 0, "scale": 1.0, "label": "..."}, ...], ...}
`anim` matches the end of the animation name (e.g. "walk" -> "BeaverAdult_walk"); "rest" is the bind pose.
`frame` may be an int or a fraction "0.5" of the clip. Node positions (#Head, #CarriedInHands, #Backpack ...)
are exported too, so attachments can be drawn as markers.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import tmesh  # noqa: E402

_cache = {}


def load(path):
    if path not in _cache:
        m = tmesh.load(path)
        n = m.nodes[1]
        P = tmesh.prop_array(n.vertexProperties, 'position').astype(np.float64)
        uv = tmesh.prop_array(n.vertexProperties, 'uv0').astype(np.float64)
        uv1 = tmesh.prop_array(n.vertexProperties, 'uv1').astype(np.float64)
        tri = np.array(n.meshes[0].indices).reshape(-1, 3)
        _cache[path] = (m, P, uv, uv1, tri)
    return _cache[path]


def find_anim(node, name):
    for i, a in enumerate(node.vertexAnimations):
        if a.name == name or a.name.endswith('_' + name) or a.name.lower().endswith(name.lower()):
            return i, a
    raise KeyError(f'animation {name} not in {[a.name for a in node.vertexAnimations]}')


def posed(path, anim, frame):
    m, P, uv, uv1, tri = load(path)
    nodes = {}
    if anim == 'rest':
        for nd in m.nodes[2:]:
            nodes[nd.name] = (np.array([nd.position.x, nd.position.y, nd.position.z]),
                              np.array([nd.rotation.x, nd.rotation.y, nd.rotation.z, nd.rotation.w]),
                              np.array([nd.scale.x, nd.scale.y, nd.scale.z]))
        return P.copy(), nodes
    ai, a = find_anim(m.nodes[1], anim)
    nf = len(a.frames)
    if isinstance(frame, str):
        fi = int(round(float(frame) * (nf - 1)))
    else:
        fi = min(int(frame), nf - 1)
    off = tmesh.prop_array(a.frames[fi].vertexProperties, 'offset')
    p = P.copy()
    p[:len(off)] += off
    for nd in m.nodes[2:]:
        if ai < len(nd.nodeAnimations) and len(nd.nodeAnimations[ai].frames) > fi:
            f = nd.nodeAnimations[ai].frames[fi]
            nodes[nd.name] = (np.array([f.position.x, f.position.y, f.position.z]),
                              np.array([f.rotation.x, f.rotation.y, f.rotation.z, f.rotation.w]),
                              np.array([f.scale.x, f.scale.y, f.scale.z]))
    return p, nodes


def main():
    sc = json.load(open(sys.argv[1], encoding='utf-8'))
    out = {}
    meta = []
    world_nodes = {}
    for k, it in enumerate(sc['items']):
        if it.get('parent') is not None:
            # an attachment (hat, tool, pack): every mesh node of `model`, placed on node `node` of item `parent`
            pk = it['parent']
            m = tmesh.load(it['model'])
            verts, tris, uvs = [], [], []
            for nd in m.nodes:
                pp = tmesh.prop_array(nd.vertexProperties, 'position')
                if pp is None or not len(pp) or not len(nd.meshes):
                    continue
                q = np.array([nd.rotation.x, nd.rotation.y, nd.rotation.z, nd.rotation.w])
                v = tmesh.quat_rotate(np.broadcast_to(q, (len(pp), 4)), pp * np.array([nd.scale.x, nd.scale.y, nd.scale.z])) \
                    + np.array([nd.position.x, nd.position.y, nd.position.z])
                uvv = tmesh.prop_array(nd.vertexProperties, 'uv0')
                for me in nd.meshes:
                    tris.append(np.array(me.indices).reshape(-1, 3) + sum(len(x) for x in verts))
                verts.append(v); uvs.append(uvv if uvv is not None else np.zeros((len(v), 2)))
            V_ = np.vstack(verts)
            pos, rot, scl, Rm, s, off = world_nodes[pk][it['node']]
            V_ = tmesh.quat_rotate(np.broadcast_to(rot, (len(V_), 4)), V_ * scl) + pos
            p = (V_ * s) @ Rm.T + off
            out[f'P{k}'] = p.astype(np.float32); out[f'T{k}'] = np.vstack(tris).astype(np.int32)
            out[f'UV{k}'] = np.vstack(uvs).astype(np.float32); out[f'UVB{k}'] = np.zeros((len(p), 2), np.float32)
            out[f'N{k}'] = np.zeros((0, 3), np.float32)
            meta.append(dict(texture=it.get('texture', ''), decal='', label=it.get('label', ''), nodes=[], markers=False))
            continue
        p, nodes = posed(it['model'], it.get('anim', 'rest'), it.get('frame', 0))
        _, _, uv, uv1, tri = load(it['model'])
        s = it.get('scale', 1.0)
        yaw = np.radians(it.get('yaw', 0.0))
        c, si = np.cos(yaw), np.sin(yaw)
        Rm = np.array([[c, 0, si], [0, 1, 0], [-si, 0, c]])
        off = np.array([it.get('offset', [0, 0])[0], it.get('lift', 0.0), it.get('offset', [0, 0])[1]])
        world_nodes[k] = {name: (pos, rot, scl, Rm, s, off) for name, (pos, rot, scl) in nodes.items()}
        p = (p * s) @ Rm.T + off
        out[f'P{k}'] = p.astype(np.float32)
        out[f'T{k}'] = tri.astype(np.int32)
        out[f'UV{k}'] = uv.astype(np.float32)
        out[f'UVB{k}'] = uv1.astype(np.float32)
        npos = []
        for name, (pos, rot, scl) in nodes.items():
            npos.append([(pos * s) @ Rm.T + off])
        out[f'N{k}'] = np.array([x[0] for x in npos], np.float32).reshape(-1, 3)
        meta.append(dict(texture=it.get('texture', ''), decal=it.get('decal', ''), label=it.get('label', ''),
                         nodes=list(nodes.keys()), markers=it.get('markers', False)))
    out['meta'] = np.array(json.dumps(dict(items=meta, cameras=sc.get('cameras', []), size=sc.get('size', [900, 700]),
                                           samples=sc.get('samples', 32), ground=sc.get('ground', True),
                                           out=sc.get('out', ''), night=sc.get('night', False),
                                           background=sc.get('background', None))))
    np.savez(sc['out_npz'], **out)
    print('wrote', sc['out_npz'], len(meta), 'items')


if __name__ == '__main__':
    main()
