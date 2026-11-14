"""Per-vertex ambient occlusion for a model's parts, baked with Cycles in headless Blender (blender_ao.py).

    ao.bake(parts, samples=64, distance=0.5) -> list of (N_i,) arrays in 0..1, one per part, in part order

Used by building.Model.build(ao=True): the baked occlusion replaces the height-based guess in core.shade, so walls
under deep eaves, the insides of porches, the feet of posts and the gaps between jars darken the way vanilla's
hand-tuned vertex colours do. About 10-20 s per model on the RTX 5070 Ti.
"""
import os
import subprocess
import tempfile

import numpy as np

BLENDER = r"E:\PandabornDev\tools\blender-4.5-lts\blender-4.5.16-windows-x64\blender.exe"
TMP = r"E:\PandabornDev\tools\tmp"


def bake(parts, samples=64, distance=0.5):
    Ps, Ts, sizes = [], [], []
    base = 0
    for p in parts:
        P = np.asarray(p.P, float)
        Ps.append(np.stack([-P[:, 0], -P[:, 2], P[:, 1]], 1))      # Unity -> Blender
        Ts.append(np.asarray(p.T)[:, ::-1] + base)
        sizes.append(len(P))
        base += len(P)
    os.makedirs(TMP, exist_ok=True)
    work = tempfile.mkdtemp(dir=TMP)
    src, dst = os.path.join(work, "in.npz"), os.path.join(work, "out.npz")
    np.savez(src, P=np.concatenate(Ps).astype(np.float32), T=np.concatenate(Ts).astype(np.int32))
    env = dict(os.environ, BLENDER_USER_RESOURCES=r"E:\PandabornDev\tools\blender-userdata", TEMP=TMP, TMP=TMP)
    r = subprocess.run([BLENDER, "-b", "--factory-startup", "--python",
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), "blender_ao.py"), "--", src, dst,
                        str(samples), str(distance)], env=env, capture_output=True, text=True)
    if "AO DONE" not in r.stdout:
        raise RuntimeError("AO bake failed: " + r.stdout[-1500:] + r.stderr[-1500:])
    ao = np.load(dst)["ao"]
    out, k = [], 0
    for n in sizes:
        out.append(ao[k:k + n])
        k += n
    return out
