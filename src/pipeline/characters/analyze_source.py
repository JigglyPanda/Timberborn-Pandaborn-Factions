"""Per-animation facts about a character .timbermesh (beaver or panda): body extents, contact height,
attachment-node positions and how far the tail moves. Used to choose the pivot of the baked size change.

usage: python -I analyze_source.py MODEL.timbermesh [--tail-z -0.21]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import tmesh  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('model')
    ap.add_argument('--tail-z', type=float, default=-0.21)
    a = ap.parse_args()
    m = tmesh.load(a.model)
    n = m.nodes[1]
    P = tmesh.prop_array(n.vertexProperties, 'position').astype(float)
    tail = P[:, 2] < a.tail_z
    print(f"verts {len(P)}  rest y {P[:,1].min():.3f}..{P[:,1].max():.3f}  z {P[:,2].min():.3f}..{P[:,2].max():.3f}  tail verts {tail.sum()}")
    nodes = {nd.name: nd for nd in m.nodes}
    print(f"{'anim':44s} {'fr':>4s} {'ymin':>6s} {'ymax':>6s} {'hip_y':>6s} {'tailmin_y':>9s} {'tail_dz':>7s} zipH(y) head(y) hands(y)")
    for ai, va in enumerate(n.vertexAnimations):
        ys, yM, tmin, tdz, hip = [], [], [], [], []
        for fr in va.frames:
            off = tmesh.prop_array(fr.vertexProperties, 'offset')
            p = P.copy(); p[:len(off)] += off
            ys.append(p[:, 1].min()); yM.append(p[:, 1].max())
            tmin.append(p[tail, 1].min()); tdz.append(np.abs(p[tail] - P[tail]).max())
            hip.append(p[(P[:, 1] > 0.08) & (P[:, 1] < 0.14) & ~tail, 1].mean())
        def node_y(name):
            nd = nodes.get(name)
            if nd is None or ai >= len(nd.nodeAnimations):
                return float('nan')
            return np.mean([f.position.y for f in nd.nodeAnimations[ai].frames])
        print(f"{va.name:44s} {len(va.frames):4d} {min(ys):6.3f} {max(yM):6.3f} {np.mean(hip):6.3f} {min(tmin):9.3f} {max(tdz):7.3f} "
              f"{node_y('#ZiplineHarness'):6.3f} {node_y('#Head'):6.3f} {node_y('#CarriedInHands'):6.3f}")


if __name__ == '__main__':
    main()
