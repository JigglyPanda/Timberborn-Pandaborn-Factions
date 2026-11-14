"""Build and preview every model under art/models, each beside its vanilla stand-in, by day and night, plus its
construction stage; then contact sheets.

    python -I src/pipeline/kit/preview_all.py [Id ...] [--no-build] [--jobs 4]

Output: E:\\PandabornDev\\build\\models\\preview\\<Id>_{day,night,stage}.png and contact sheets sheet_day.png,
sheet_night.png, sheet_stage.png.
"""
import argparse
import concurrent.futures as cf
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import preview  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
ART = os.path.join(ROOT, "art", "models")
MODELS = r"E:\PandabornDev\build\models"
PY = sys.executable


def one(mid, build):
    if build:
        r = subprocess.run([PY, os.path.join(ART, mid, "build.py")], capture_output=True, text=True,
                           env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        if r.returncode:
            return mid, "build failed: " + r.stderr[-800:]
    mj = json.load(open(os.path.join(ART, mid, "model.json")))
    ref = mj["standIn"] + ".Model"
    fin = os.path.join(MODELS, mid, f"{mid}.Model.timbermesh")
    st = os.path.join(MODELS, mid, f"{mid}.ConstructionStage0.Model.timbermesh")
    out = os.path.join(MODELS, "preview")
    refp = os.path.join(preview.VANILLA, ref + ".timbermesh")
    preview.render(fin, ref if os.path.exists(refp) else None, out, mid, samples=40)
    preview.render(st, None, out, mid + "_stage_tmp", night=False, extra=[(fin, (mj["size"]["X"] + 0.8, 0, 0))],
                   samples=24, size=(1000, 700))
    os.replace(os.path.join(out, mid + "_stage_tmp_day.png"), os.path.join(out, mid + "_stage.png"))
    return mid, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--no-build", action="store_true")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    ids = a.ids or sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(ART, "*", "build.py")))
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        for mid, res in ex.map(lambda i: one(i, not a.no_build), ids):
            print(mid, res)
    out = os.path.join(MODELS, "preview")
    every = sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(ART, "*", "model.json")))
    for kind in ("day", "night", "stage"):
        imgs = [os.path.join(out, f"{i}_{kind}.png") for i in every if os.path.exists(os.path.join(out, f"{i}_{kind}.png"))]
        labels = []
        for p in imgs:
            i = os.path.basename(p).rsplit("_", 1)[0]
            mj = json.load(open(os.path.join(ART, i, "model.json")))
            labels.append(f"{i}  ({mj['triangles']['finished']} tris; vanilla median {mj['triangles']['vanillaMedianForFootprint']})"
                          f"  beside {mj['standIn']}" if kind != "stage" else f"{i} construction stage ({mj['triangles']['constructionStage0']} tris) and finished")
        print(preview.sheet(os.path.join(out, f"sheet_{kind}.png"), imgs, cols=4, cell=(600, 400), labels=labels))


if __name__ == "__main__":
    main()
