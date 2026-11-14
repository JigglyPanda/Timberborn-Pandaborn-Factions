"""Dump the structure of a .timbermesh (zlib/gzip-wrapped protobuf, Mechanistry model.proto).

Usage:  E:\PandabornDev\tools\venv\Scripts\python.exe -I src/pipeline/tmesh_inspect.py FILE [--anim-detail]
(-I is fine: this script adds its own folder to sys.path for model_pb2.)
"""
import sys, os, time, zlib, gzip, ctypes, ctypes.wintypes as wt, tracemalloc
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import model_pb2 as pb

DT = {1: np.uint8, 2: np.uint32, 3: np.int32, 4: np.float32, 5: np.float64}


def load(path):
    raw = open(path, 'rb').read()
    head = raw[:2]
    if head == b'\x1f\x8b':
        data = gzip.decompress(raw)
    else:
        data = zlib.decompress(raw)
    m = pb.Model()
    m.ParseFromString(data)
    return m, head, len(raw), len(data)


def prop(props, name):
    for p in props:
        if p.name == name:
            a = np.frombuffer(p.data, dtype=DT[p.scalarType])
            return a.reshape(-1, p.scalarTypeDimension) if p.scalarTypeDimension > 1 else a
    return None


def peak_ws_mb():
    class PMC(ctypes.Structure):
        _fields_ = [('cb', wt.DWORD), ('PageFaultCount', wt.DWORD), ('PeakWorkingSetSize', ctypes.c_size_t),
                    ('WorkingSetSize', ctypes.c_size_t), ('a', ctypes.c_size_t), ('b', ctypes.c_size_t),
                    ('c', ctypes.c_size_t), ('d', ctypes.c_size_t), ('PagefileUsage', ctypes.c_size_t),
                    ('PeakPagefileUsage', ctypes.c_size_t)]
    k = ctypes.windll.kernel32
    k.GetCurrentProcess.restype = wt.HANDLE
    k.K32GetProcessMemoryInfo.argtypes = [wt.HANDLE, ctypes.POINTER(PMC), wt.DWORD]
    c = PMC(); c.cb = ctypes.sizeof(c)
    k.K32GetProcessMemoryInfo(k.GetCurrentProcess(), ctypes.byref(c), c.cb)
    return c.PeakWorkingSetSize / 1048576


def describe(m, anim_detail=False):
    out = [f"Model name={m.name!r} version={m.version} nodes={len(m.nodes)}"]
    for i, n in enumerate(m.nodes):
        out.append(f"[{i}] node {n.name!r} parent={n.parent} vertexCount={n.vertexCount}")
        out.append(f"     pos=({n.position.x:.4f},{n.position.y:.4f},{n.position.z:.4f}) "
                   f"rot=({n.rotation.x:.4f},{n.rotation.y:.4f},{n.rotation.z:.4f},{n.rotation.w:.4f}) "
                   f"scale=({n.scale.x:.4f},{n.scale.y:.4f},{n.scale.z:.4f})")
        for p in n.vertexProperties:
            a = prop(n.vertexProperties, p.name)
            rng = f" min={np.round(a.min(0),4).tolist()} max={np.round(a.max(0),4).tolist()}" if len(a) else ''
            out.append(f"     prop {p.name!r} type={pb.ScalarType.Name(p.scalarType)} dim={p.scalarTypeDimension} "
                       f"bytes={len(p.data)}{rng}")
        for k, me in enumerate(n.meshes):
            idx = np.array(me.indices)
            out.append(f"     mesh[{k}] material={me.material!r} indices={len(idx)} triangles={len(idx)//3} "
                       f"idx_range=({idx.min() if len(idx) else '-'},{idx.max() if len(idx) else '-'})")
        if anim_detail:
            for a in n.vertexAnimations:
                fr = a.frames[0].vertexProperties if len(a.frames) else []
                out.append(f"     vertexAnim {a.name!r} frames={len(a.frames)} fps={a.framerate:g} "
                           f"animatedVertexCount={a.animatedVertexCount} frameProps={[(p.name, p.scalarTypeDimension) for p in fr]}")
            for a in n.nodeAnimations:
                out.append(f"     nodeAnim {a.name!r} frames={len(a.frames)} fps={a.framerate:g}")
        else:
            for label, anims in (('vertexAnim', n.vertexAnimations), ('nodeAnim', n.nodeAnimations)):
                if anims:
                    tot = sum(len(a.frames) for a in anims)
                    out.append(f"     {label}: {len(anims)} animations, {tot} frames total (use --anim-detail for the list)")
    return '\n'.join(out)


if __name__ == '__main__':
    path = sys.argv[1]
    tracemalloc.start()
    t0 = time.perf_counter()
    m, head, csize, usize = load(path)
    dt = time.perf_counter() - t0
    cur, peak = tracemalloc.get_traced_memory()
    print(f"file={path}\nheader bytes={head.hex()} compressed={csize} decompressed={usize}")
    print(f"load time={dt*1000:.1f} ms  python-heap peak={peak/1048576:.1f} MB  process peak working set={peak_ws_mb():.0f} MB")
    print(describe(m, '--anim-detail' in sys.argv))
