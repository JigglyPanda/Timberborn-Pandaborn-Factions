"""Split the vanilla bot mesh into its rigid parts and report them (bounds, UV box, rigidity over all animations).

usage: python -I ox_analyze.py <Bot.Folktails.Model.timbermesh> <out.json>
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

import tmesh


def parts(P, tri, weld=1e-5):
    # weld by position so split UV seams do not split a part
    key = np.round(P / weld).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.ravel()
    e = np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
    n = inv.max() + 1
    g = coo_matrix((np.ones(len(e)), (inv[e[:, 0]], inv[e[:, 1]])), shape=(n, n))
    k, lab = connected_components(g, directed=False)
    return k, lab[inv]


def kabsch(A, B):
    ca, cb = A.mean(0), B.mean(0)
    H = (A - ca).T @ (B - cb)
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    D = np.diag([1, 1, d])
    R = Vt.T @ D @ U.T
    return R, cb - R @ ca


def main():
    m = tmesh.load(sys.argv[1])
    n = m.nodes[1]
    P = tmesh.prop_array(n.vertexProperties, 'position').astype(np.float64)
    uv = tmesh.prop_array(n.vertexProperties, 'uv0').astype(np.float64)
    tri = np.array(n.meshes[0].indices).reshape(-1, 3)
    k, lab = parts(P, tri)
    out = dict(parts=[], anims=[a.name for a in n.vertexAnimations])
    worst = np.zeros(k)
    for a in n.vertexAnimations:
        for f in a.frames[::4]:
            off = tmesh.prop_array(f.vertexProperties, 'offset')
            Q = P + off
            for c in range(k):
                idx = lab == c
                if idx.sum() < 3:
                    continue
                R, t = kabsch(P[idx], Q[idx])
                r = np.abs(P[idx] @ R.T + t - Q[idx]).max()
                worst[c] = max(worst[c], r)
    for c in range(k):
        idx = np.nonzero(lab == c)[0]
        out['parts'].append(dict(id=int(c), verts=int(len(idx)), tris=int(np.isin(tri, idx).all(1).sum()),
                                 lo=P[idx].min(0).round(4).tolist(), hi=P[idx].max(0).round(4).tolist(),
                                 uvlo=uv[idx].min(0).round(4).tolist(), uvhi=uv[idx].max(0).round(4).tolist(),
                                 nonrigid=round(float(worst[c]), 5)))
    out['parts'].sort(key=lambda p: -p['hi'][1])
    json.dump(out, open(sys.argv[2], 'w'), indent=1)
    for p in out['parts']:
        print(p['id'], p['verts'], 'y %.3f..%.3f x %.3f..%.3f z %.3f..%.3f' % (p['lo'][1], p['hi'][1], p['lo'][0], p['hi'][0], p['lo'][2], p['hi'][2]),
              'uv', p['uvlo'], p['uvhi'], 'nonrigid', p['nonrigid'])
    np.save(os.path.splitext(sys.argv[2])[0] + '.labels.npy', lab)
    print(k, 'parts;', len(out['anims']), 'anims:', ', '.join(out['anims']))


if __name__ == '__main__':
    main()
