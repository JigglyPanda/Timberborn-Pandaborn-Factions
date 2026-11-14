"""Build a Ringtail (red panda) .timbermesh from the vanilla beaver .timbermesh.

usage: python -I build_ringtail.py ADULT|CHILD OUT.timbermesh [--only walk,idle] [--size 0.82] [--no-anims]

Deterministic: same inputs and config -> same bytes. Writes OUT and OUT-without-extension.paint.npz (rest-pose
fields for the coat painter, in unscaled beaver units). The size change is baked into every vertex, every frame
offset and every attachment node (position and scale), about the model origin: the origin is the contact point in
every animation (ground, seat, bed, water surface, zipline cable), so contacts are kept.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402

import geom  # noqa: E402
import panda  # noqa: E402
import redpanda  # noqa: E402
import rp_configs  # noqa: E402
import tmesh  # noqa: E402
import model_pb2 as pb  # noqa: E402


def half(a):
    return np.asarray(a, np.float32).astype(np.float16).astype(np.float32)


def build(cfg, out_path, size, log=print, chunk=40, only=None, anims=True):
    t0 = time.time()
    src = panda.Source(cfg['path'])
    b = redpanda.RedPandaBuilder(src, cfg, log)
    b.build_rest()
    if cfg.get('beaver_ao'):
        panda.remap_cavity(b, cfg['beaver_ao'], log=log, **cfg.get('cavity', {}))
    b.bind()
    V = len(b.P1)
    tri = b.tri
    uv0 = b.at['uv0']
    uv1 = b.at['uv1'].copy()
    tm = b.flags['tail'].astype(bool)
    uv1[tm] = redpanda.tail_uv1(b.flags['tail_t'][tm], b.flags['tail_phi'][tm])
    tw = np.sign(b.at['T'][:, 3]); tw[tw == 0] = -1
    sg = b.sg
    P1 = b.P1
    N1 = geom.vertex_normals(P1, tri, sg)
    T1 = geom.tangents_batch(P1[None], N1[None], uv0, tri)[0]

    model = pb.Model()
    model.CopyFrom(src.model)
    node = model.nodes[src.node_index]
    del node.vertexProperties[:]
    for name, arr in [('position', P1 * size), ('normal', N1), ('tangent', np.c_[T1, tw]), ('color', b.at['C']),
                      ('uv0', uv0), ('uv1', uv1)]:
        node.vertexProperties.append(tmesh.make_prop(name, arr))
    node.vertexCount = V
    del node.meshes[:]
    m = node.meshes.add()
    m.indices.extend(tri.ravel().tolist())
    m.material = src.material
    del node.vertexAnimations[:]
    nframes = 0
    keep = []
    grounded = []
    for ai, a in enumerate(src.anims):
        if only and not any(a.name.endswith(o) for o in only):
            continue
        keep.append(ai)
        va = node.vertexAnimations.add()
        va.name = a.name
        va.framerate = a.framerate
        va.animatedVertexCount = V
        if not anims:
            continue
        Fs = src.frames(a)
        grounded.append(a.name) if b.set_animation(Fs) else None
        for c0 in range(0, len(Fs), chunk):
            Fp = b.transfer(Fs[c0:c0 + chunk])
            Nf = geom.vertex_normals_batch(Fp, tri, sg)
            Tf = geom.tangents_batch(Fp, Nf, uv0, tri)
            for k in range(len(Fp)):
                q = tmesh.frame_to_quat(Nf[k], Tf[k])
                fr = va.frames.add()
                fr.vertexProperties.append(tmesh.make_prop('offset', half((Fp[k] - P1) * size)))
                fr.vertexProperties.append(tmesh.make_prop('rotation', half(q)))
        nframes += len(Fs)
    log(f"tail rests on the ground in {len(grounded)} of {len(keep)} animations: {', '.join(g.split('_', 1)[-1] for g in grounded)}")
    # other nodes: keep only the selected animations (for --only test builds), adjust, then scale
    for n in model.nodes:
        if n is node or not len(n.nodeAnimations):
            continue
        kept = [n.nodeAnimations[i] for i in keep]
        tmp = [pb.NodeAnimation() for _ in kept]
        for t_, k_ in zip(tmp, kept):
            t_.CopyFrom(k_)
        del n.nodeAnimations[:]
        for t_ in tmp:
            n.nodeAnimations.add().CopyFrom(t_)
    adjust_nodes(model, cfg, log)
    scale_nodes(model, src.node_index, size)
    redpanda.export_paint_data(b, out_path.replace('.timbermesh', '') + '.paint.npz')
    sz = tmesh.save(model, out_path)
    log(f"wrote {out_path}: {V} verts, {len(tri)} tris, {len(keep)} anims, {nframes} frames, size x{size}, "
        f"{sz / 1e6:.1f} MB in {time.time() - t0:.0f}s")
    return b, model


def adjust_nodes(model, cfg, log):
    adj = cfg.get('node_adjust', {})
    for n in model.nodes:
        if n.name not in adj:
            continue
        a = adj[n.name]
        dp = a.get('dpos', (0, 0, 0))
        sc = a.get('scale', 1.0)
        n.position.x += dp[0]; n.position.y += dp[1]; n.position.z += dp[2]
        for na in n.nodeAnimations:
            for fr in na.frames:
                q = np.array([fr.rotation.x, fr.rotation.y, fr.rotation.z, fr.rotation.w])
                d = tmesh.quat_rotate(q[None], np.array(dp)[None])[0] if np.any(dp) else np.zeros(3)
                fr.position.x += d[0]; fr.position.y += d[1]; fr.position.z += d[2]
                fr.scale.x *= sc; fr.scale.y *= sc; fr.scale.z *= sc
        log(f"adjusted node {n.name}: dpos={dp} scale={sc}")


def scale_nodes(model, mesh_index, size):
    """Bake the size into attachment nodes: positions about the origin, and their scale (attached goods, tools,
    hats, the zipline harness and the collider shrink with the body, as with a TransformSpec scale)."""
    for i, n in enumerate(model.nodes):
        if i == mesh_index or n.parent < 0:
            continue
        n.position.x *= size; n.position.y *= size; n.position.z *= size
        n.scale.x *= size; n.scale.y *= size; n.scale.z *= size
        for na in n.nodeAnimations:
            for fr in na.frames:
                fr.position.x *= size; fr.position.y *= size; fr.position.z *= size
                fr.scale.x *= size; fr.scale.y *= size; fr.scale.z *= size


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('which')
    ap.add_argument('out')
    ap.add_argument('--only', default='')
    ap.add_argument('--size', type=float, default=rp_configs.SIZE)
    ap.add_argument('--no-anims', action='store_true')
    a = ap.parse_args()
    build(rp_configs.get(a.which), a.out, a.size, only=[x for x in a.only.split(',') if x] or None, anims=not a.no_anims)
