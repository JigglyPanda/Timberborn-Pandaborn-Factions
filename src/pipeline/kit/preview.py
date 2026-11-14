"""Preview any .timbermesh in the faction's materials, by day and by night, beside a vanilla model for scale.

    python -I src/pipeline/kit/preview.py MODEL.timbermesh [--ref Lodge.Folktails.Model] [--out DIR] [--name N]
                                          [--yaw 25] [--pitch 50] [--size 1200x800] [--frame-anim 0.3] [--slots]
    python -I src/pipeline/kit/preview.py --sheet OUT.png IMG [IMG ...]      # contact sheet of finished previews

The reference model is read from E:\\PandabornDev\\reference\\vanilla-models (dumped by
src/pipeline/dump_vanilla_models.py; never committed) and stands one tile to the right of the model. The camera
looks at the model's front (the grid's -Y side, where entrances are) from above, like the game's default camera.
Output: <out>/<name>_day.png and <name>_night.png. Textures are the look prototype's
(E:\\PandabornDev\\unity\\PandabornLook\\Assets\\PandabornLook\\Textures, the same files the game bundle is built from).
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import tmio  # noqa: E402

BLENDER = r"E:\PandabornDev\tools\blender-4.5-lts\blender-4.5.16-windows-x64\blender.exe"
LOOK = r"E:\PandabornDev\unity\PandabornLook\Assets\PandabornLook"
VANILLA = r"E:\PandabornDev\reference\vanilla-models"
OUT = r"E:\PandabornDev\build\models\preview"
TMP = r"E:\PandabornDev\tools\tmp"


def bounds_unity(path):
    lo, hi = np.full(3, 1e9), np.full(3, -1e9)
    for n in tmio.load(path):
        if n["P"] is None or not len(n["P"]):
            continue
        W = n["world"]
        P = n["P"] @ W[:3, :3].T + W[:3, 3]
        lo, hi = np.minimum(lo, P.min(0)), np.maximum(hi, P.max(0))
    return lo, hi


def render(model, ref=None, out=OUT, name=None, yaw=25.0, pitch=55.0, size=(1200, 800), frame_anim=None,
           slots=False, samples=48, night=True, extra=()):
    os.makedirs(out, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)
    name = name or os.path.basename(model).split(".")[0]
    work = tempfile.mkdtemp(dir=TMP)
    items = [{"npz": tmio.to_npz(model, os.path.join(work, "a.npz"), frame=frame_anim)}]
    lo, hi = bounds_unity(model)
    x1 = max(np.ceil(hi[0]), 1)
    gx0, gz0, gx1, gz1 = min(np.floor(lo[0]), 0), min(np.floor(lo[2]), 0), x1, max(np.ceil(hi[2]), 1)
    if ref:
        rp = ref if os.path.isabs(ref) else os.path.join(VANILLA, ref + ".timbermesh")
        rlo, rhi = bounds_unity(rp)
        off = x1 + 0.6 - rlo[0]
        items.append({"npz": tmio.to_npz(rp, os.path.join(work, "b.npz"), offset=(off, 0, 0))})
        gx1 = max(gx1, off + np.ceil(rhi[0]))
        gz1 = max(gz1, np.ceil(rhi[2]))
    for i, (path, offset) in enumerate(extra):
        items.append({"npz": tmio.to_npz(path, os.path.join(work, f"x{i}.npz"), offset=offset)})
    # grid in Blender XY: unity x -> -x, unity z -> -y
    grid = [-(gx1 + 1), -(gz1 + 1), -(gx0 - 1), -(gz0 - 1)]
    res = {"day": os.path.join(out, name + "_day.png")}
    if night:
        res["night"] = os.path.join(out, name + "_night.png")
    job = {"items": items, "textures": os.path.join(LOOK, "Textures"), "spec": os.path.join(LOOK, "look_spec.json"),
           "out": res, "size": list(size), "yaw": yaw, "pitch": pitch, "focal": 110, "samples": samples,
           "grid": grid, "showSlots": slots}
    jp = os.path.join(work, "job.json")
    json.dump(job, open(jp, "w"))
    env = dict(os.environ, BLENDER_USER_RESOURCES=r"E:\PandabornDev\tools\blender-userdata", TEMP=TMP, TMP=TMP)
    r = subprocess.run([BLENDER, "-b", "--factory-startup", "--python",
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), "blender_preview.py"), "--", jp],
                       env=env, capture_output=True, text=True)
    if r.returncode != 0 or "WROTE" not in r.stdout:
        print(r.stdout[-3000:], r.stderr[-3000:])
        raise RuntimeError("blender failed")
    return res


def sheet(out, images, cols=4, cell=(600, 400), labels=None):
    from PIL import Image, ImageDraw
    rows = (len(images) + cols - 1) // cols
    W, H = cell
    canvas = Image.new("RGB", (cols * W, rows * (H + 22)), (24, 24, 24))
    d = ImageDraw.Draw(canvas)
    for i, p in enumerate(images):
        im = Image.open(p).convert("RGB")
        im.thumbnail((W, H))
        x, y = (i % cols) * W, (i // cols) * (H + 22)
        canvas.paste(im, (x + (W - im.width) // 2, y + 22))
        d.text((x + 6, y + 4), labels[i] if labels else os.path.basename(p), fill=(235, 235, 235))
    canvas.save(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model", nargs="?")
    ap.add_argument("--ref")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--name")
    ap.add_argument("--yaw", type=float, default=25)
    ap.add_argument("--pitch", type=float, default=55)
    ap.add_argument("--size", default="1200x800")
    ap.add_argument("--frame-anim", type=float)
    ap.add_argument("--slots", action="store_true")
    ap.add_argument("--day-only", action="store_true")
    ap.add_argument("--sheet")
    ap.add_argument("images", nargs="*")
    a = ap.parse_args()
    if a.sheet:
        print(sheet(a.sheet, ([a.model] if a.model else []) + a.images))
        return
    w, h = (int(v) for v in a.size.split("x"))
    print(render(a.model, a.ref, a.out, a.name, a.yaw, a.pitch, (w, h), a.frame_anim, a.slots,
                 night=not a.day_only))


if __name__ == "__main__":
    main()
