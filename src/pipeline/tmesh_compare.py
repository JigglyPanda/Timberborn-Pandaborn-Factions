"""Field-by-field structural comparison of two .timbermesh files.
Usage: python -I tmesh_compare.py A.timbermesh B.timbermesh
Compares model/node fields, vertex property names/types/dims/counts, per-material triangle counts and the
(sorted) set of triangle position-triples per material. Exits 1 if anything differs structurally."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import tmesh_inspect as ti


def tri_set(n, me):
    P = ti.prop(n.vertexProperties, 'position')
    idx = np.array(me.indices).reshape(-1, 3)
    t = np.round(P[idx], 4)
    # canonical per-triangle form: rotate so lexicographically smallest vertex is first (keeps winding)
    out = []
    for tri in t:
        k = min(range(3), key=lambda i: tuple(tri[i]))
        out.append(tuple(map(tuple, np.roll(tri, -k, axis=0))))
    return sorted(out)


def main(a, b):
    ma, *_ = ti.load(a); mb, *_ = ti.load(b)
    bad = 0
    def chk(label, x, y):
        nonlocal bad
        ok = x == y
        if not ok: bad += 1
        print(f"{'OK  ' if ok else 'DIFF'} {label}: {x!r} | {y!r}")
    chk('version', ma.version, mb.version); chk('model.name', ma.name, mb.name); chk('node count', len(ma.nodes), len(mb.nodes))
    for i, (na, nb) in enumerate(zip(ma.nodes, mb.nodes)):
        p = f"node[{i}]"
        chk(p + '.name', na.name, nb.name); chk(p + '.parent', na.parent, nb.parent)
        for f in ('position', 'rotation', 'scale'):
            va, vb = getattr(na, f), getattr(nb, f)
            ta = tuple(round(getattr(va, c), 4) for c in ('x', 'y', 'z', 'w') if hasattr(va, c))
            tb = tuple(round(getattr(vb, c), 4) for c in ('x', 'y', 'z', 'w') if hasattr(vb, c))
            chk(p + '.' + f, ta, tb)
        chk(p + '.vertexCount', na.vertexCount, nb.vertexCount)
        chk(p + '.props', [(q.name, q.scalarType, q.scalarTypeDimension) for q in na.vertexProperties],
            [(q.name, q.scalarType, q.scalarTypeDimension) for q in nb.vertexProperties])
        chk(p + '.prop bytes', [len(q.data) for q in na.vertexProperties], [len(q.data) for q in nb.vertexProperties])
        chk(p + '.materials(order)', [m.material for m in na.meshes], [m.material for m in nb.meshes])
        chk(p + '.tris/material', [len(m.indices) // 3 for m in na.meshes], [len(m.indices) // 3 for m in nb.meshes])
        chk(p + '.anims', (len(na.vertexAnimations), len(na.nodeAnimations)), (len(nb.vertexAnimations), len(nb.nodeAnimations)))
        if len(na.meshes) == len(nb.meshes) and na.vertexCount and nb.vertexCount:
            for k, (x, y) in enumerate(zip(na.meshes, nb.meshes)):
                if x.material == y.material:
                    chk(f"{p}.mesh[{k}] triangle geometry identical", tri_set(na, x) == tri_set(nb, y), True)
    print('RESULT:', 'IDENTICAL STRUCTURE' if not bad else f'{bad} difference(s)')
    return bad


if __name__ == '__main__':
    sys.exit(1 if main(sys.argv[1], sys.argv[2]) else 0)
