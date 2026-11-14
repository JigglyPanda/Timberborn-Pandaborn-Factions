"""Checks a built Ringtail .timbermesh against its beaver source.

usage: python -I qa_ringtail.py ADULT|CHILD RINGTAIL.timbermesh [--json out.json] [--compare PANDA.timbermesh]

Format (fails the run): zlib header 78 9C; node names, parents and node-animation names/frame counts identical to the
beaver; vertex animations with the same names, frame counts and frame rates; every frame has finite offsets and unit
quaternions for every vertex; indices in range; material name kept.
Motion (reported, compared with the beaver): per animation the 99.9th-percentile edge stretch, collapsed triangles,
the largest frame-to-frame jump of a tail vertex (popping), how much of the tail lies inside the body's reach
(self-intersection proxy: tail vertices nearer than 1.2 cm to a body vertex), and the lowest point of the tail
against the beaver paddle's (ground clipping). Load time and file size are measured as tmesh_inspect.py does.
"""
import argparse
import json
import os
import sys
import time
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402

import rp_configs  # noqa: E402
import tmesh  # noqa: E402
import model_pb2 as pb  # noqa: E402


def load_timed(path):
    raw = open(path, 'rb').read()
    t0 = time.perf_counter()
    m = pb.Model()
    m.ParseFromString(zlib.decompress(raw))
    return m, raw, time.perf_counter() - t0


def frames(node, a, P):
    for fr in a.frames:
        off = tmesh.prop_array(fr.vertexProperties, 'offset')
        rot = tmesh.prop_array(fr.vertexProperties, 'rotation')
        p = P.copy()
        p[:len(off)] += off
        yield p, off, rot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('which'); ap.add_argument('model')
    ap.add_argument('--json', default='')
    ap.add_argument('--compare', default='')
    a = ap.parse_args()
    cfg = rp_configs.get(a.which)
    size = rp_configs.SIZE
    fails = []

    def chk(c, msg):
        if not c:
            fails.append(msg)
            print('FAIL:', msg)

    m, raw, tload = load_timed(a.model)
    o, _, _ = load_timed(cfg['path'])
    chk(raw[:2] == b'\x78\x9c', 'zlib header')
    chk([x.name for x in m.nodes] == [x.name for x in o.nodes], 'node names')
    chk([x.parent for x in m.nodes] == [x.parent for x in o.nodes], 'node parents')
    for x, y in zip(m.nodes, o.nodes):
        chk([(q.name, len(q.frames)) for q in x.nodeAnimations] == [(q.name, len(q.frames)) for q in y.nodeAnimations],
            f'{x.name} node animations')
    nd, od = m.nodes[1], o.nodes[1]
    V = nd.vertexCount
    for k in ['position', 'normal', 'tangent', 'color', 'uv0', 'uv1']:
        arr = tmesh.prop_array(nd.vertexProperties, k)
        chk(arr is not None and len(arr) == V and np.isfinite(arr).all(), f'prop {k}')
    idx = np.array(nd.meshes[0].indices)
    chk(idx.min() >= 0 and idx.max() < V and len(idx) % 3 == 0, 'indices')
    chk(nd.meshes[0].material == od.meshes[0].material, 'material name')
    chk([(q.name, len(q.frames), q.framerate) for q in nd.vertexAnimations] ==
        [(q.name, len(q.frames), q.framerate) for q in od.vertexAnimations], 'vertex animation names/frames/fps')

    P = tmesh.prop_array(nd.vertexProperties, 'position').astype(np.float64)
    tri = idx.reshape(-1, 3)
    Po = tmesh.prop_array(od.vertexProperties, 'position').astype(np.float64)
    trio = np.array(od.meshes[0].indices).reshape(-1, 3)
    paint = np.load(a.model.replace('.timbermesh', '') + '.paint.npz')
    tail = paint['tail'] > 0.5
    tt = paint['tail_t']
    far_tail = tail & (tt > 0.3)
    body = ~tail & (paint['teeth'] < 0.5)
    tz = cfg['tail_root'][2]
    paddle = Po[:, 2] < tz - 0.005

    def edges(t):
        e = np.unique(np.sort(np.concatenate([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), 1), axis=0)
        return e
    e_m, e_o = edges(tri), edges(trio)
    L_m = np.linalg.norm(P[e_m[:, 0]] - P[e_m[:, 1]], axis=1) + 1e-9
    L_o = np.linalg.norm(Po[e_o[:, 0]] - Po[e_o[:, 1]], axis=1) + 1e-9
    A_m = np.linalg.norm(np.cross(P[tri[:, 1]] - P[tri[:, 0]], P[tri[:, 2]] - P[tri[:, 0]]), axis=1)
    A_o = np.linalg.norm(np.cross(Po[trio[:, 1]] - Po[trio[:, 0]], Po[trio[:, 2]] - Po[trio[:, 0]]), axis=1)
    rows = []
    worst_q = 0.0
    for am, ao in zip(nd.vertexAnimations, od.vertexAnimations):
        st_m = st_o = 0.0
        col_m = col_o = 0
        jump_m = jump_o = 0.0
        near = 0.0
        tmin_m = tmin_o = 9.0
        prev_m = prev_o = None
        for (pm, off, rot), (po, _, _) in zip(frames(nd, am, P), frames(od, ao, Po)):
            if off is None or rot is None or len(off) != V or len(rot) != V or not np.isfinite(off).all() or not np.isfinite(rot).all():
                chk(False, f'{am.name} frame data')
                break
            worst_q = max(worst_q, float(np.abs(np.linalg.norm(rot, axis=1) - 1).max()))
            st_m = max(st_m, np.percentile(np.linalg.norm(pm[e_m[:, 0]] - pm[e_m[:, 1]], axis=1) / L_m, 99.9))
            st_o = max(st_o, np.percentile(np.linalg.norm(po[e_o[:, 0]] - po[e_o[:, 1]], axis=1) / L_o, 99.9))
            am_ = np.linalg.norm(np.cross(pm[tri[:, 1]] - pm[tri[:, 0]], pm[tri[:, 2]] - pm[tri[:, 0]]), axis=1)
            ao_ = np.linalg.norm(np.cross(po[trio[:, 1]] - po[trio[:, 0]], po[trio[:, 2]] - po[trio[:, 0]]), axis=1)
            col_m = max(col_m, int((am_ < 0.05 * A_m).sum()))
            col_o = max(col_o, int((ao_ < 0.05 * A_o).sum()))
            if prev_m is not None:
                jump_m = max(jump_m, float(np.linalg.norm(pm[tail] - prev_m[tail], axis=1).max()) / size)
                jump_o = max(jump_o, float(np.linalg.norm(po[paddle] - prev_o[paddle], axis=1).max()))
            prev_m, prev_o = pm, po
            d, _ = cKDTree(pm[body]).query(pm[far_tail])
            near = max(near, float((d < 0.012 * size / 0.82 * (0.6 if cfg['kind'] == 'child' else 1.0)).mean()))
            tmin_m = min(tmin_m, float(pm[tail, 1].min()) / size)
            tmin_o = min(tmin_o, float(po[paddle, 1].min()))
        rows.append(dict(anim=am.name, frames=len(am.frames), stretch=round(st_m, 2), stretch_beaver=round(st_o, 2),
                         collapsed=col_m, collapsed_beaver=col_o, tail_jump=round(jump_m, 4), paddle_jump=round(jump_o, 4),
                         tail_near_body=round(near, 3), tail_min_y=round(tmin_m, 3), paddle_min_y=round(tmin_o, 3)))
    chk(worst_q < 0.01, f'quaternion norms {worst_q}')
    print(f"{'anim':44s} {'fr':>4s} {'str':>5s} {'str_b':>5s} {'col':>4s} {'col_b':>5s} {'tjump':>6s} {'pjump':>6s} {'tnear':>5s} {'tminy':>6s} {'pminy':>6s}")
    for r in rows:
        flag = ''
        if r['stretch'] > max(1.6, r['stretch_beaver'] * 1.35): flag += ' STRETCH'
        if r['tail_jump'] > max(0.05, r['paddle_jump'] * 1.8): flag += ' POP'
        if r['tail_near_body'] > 0.25: flag += ' TAIL-IN-BODY?'
        if r['tail_min_y'] < r['paddle_min_y'] - 0.03: flag += ' GROUND'
        print(f"{r['anim']:44s} {r['frames']:4d} {r['stretch']:5.2f} {r['stretch_beaver']:5.2f} {r['collapsed']:4d} {r['collapsed_beaver']:5d} "
              f"{r['tail_jump']:6.3f} {r['paddle_jump']:6.3f} {r['tail_near_body']:5.2f} {r['tail_min_y']:6.3f} {r['paddle_min_y']:6.3f}{flag}")
    summary = dict(model=a.model, bytes=len(raw), megabytes=round(len(raw) / 1e6, 1), parse_seconds=round(tload, 2),
                   vertices=V, triangles=len(tri), animations=len(rows), frames=sum(r['frames'] for r in rows),
                   failures=fails, rows=rows)
    if a.compare:
        pm_, praw, pt = load_timed(a.compare)
        summary['compare'] = dict(model=a.compare, bytes=len(praw), megabytes=round(len(praw) / 1e6, 1),
                                  parse_seconds=round(pt, 2), vertices=pm_.nodes[1].vertexCount)
    print(json.dumps({k: v for k, v in summary.items() if k != 'rows'}, indent=1))
    if a.json:
        json.dump(summary, open(a.json, 'w'), indent=1)
    print('ALL FORMAT CHECKS PASSED' if not fails else f'{len(fails)} FORMAT CHECK(S) FAILED')
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
