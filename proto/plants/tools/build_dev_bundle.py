"""Builds a dev-only copy of the plants bundle whose materials are renamed `<name>Dev`, for testing new plant art while
the installed faction still ships an older `pandabornplants` bundle (dev only, never shipped).

    python -I proto/plants/tools/build_dev_bundle.py

Two bundles may not hold the same files (docs/tech/plants.md, one bundle per mod), and two materials may not share a
name (MaterialRepository), so the dev bundle is `pandabornplantsdev_win` with materials `PandabornTimberBambooDev`, ...
at `Materials/Pandaborn/Plants/<name>Dev`. gen_mod.py --dev-materials ships it with models whose material names are rewritten.
Uses the Windows plants Unity project (paints its textures first), then restores the normal spec there.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
PROJECT = r"E:\PandabornDev\unity\PandabornPlants"
OUT = r"E:\PandabornDev\build\plants\dev-bundle"
UNITY = r"C:\Program Files\Unity\Hub\Editor\6000.5.11f1\Editor\Unity.exe"
PY = sys.executable


def main():
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", TEMP=r"E:\PandabornDev\tools\tmp", TMP=r"E:\PandabornDev\tools\tmp",
               UPM_CACHE_ROOT=r"E:\PandabornDev\unity\cache\upm")
    tex = os.path.join(REPO, "src", "pipeline", "plants", "textures.py")
    subprocess.run([PY, "-I", tex, "--unity", PROJECT], check=True, env=env)
    spec_path = os.path.join(PROJECT, "Assets", "PandabornPlants", "plants_spec.json")
    spec = json.load(open(spec_path))
    for m in spec["materials"]:
        m["name"] += "Dev"
    json.dump(spec, open(spec_path, "w"), indent=1)
    os.makedirs(OUT, exist_ok=True)
    log = os.path.join(os.path.dirname(OUT), "unity_build_dev.log")
    try:
        r = subprocess.run([UNITY, "-batchmode", "-quit", "-nographics", "-projectPath", PROJECT, "-logFile", log,
                            "-executeMethod", "PandabornPlantsBuilder.Build", "-plantsOut", OUT,
                            "-bundleName", "pandabornplantsdev"], env=env)
        ok = r.returncode == 0 and "[PandabornPlants] OK" in open(log, encoding="utf-8", errors="replace").read()
    finally:
        subprocess.run([PY, "-I", tex, "--unity", PROJECT], check=True, env=env)   # the normal spec again
    print("dev bundle", "OK" if ok else "FAILED", "->", OUT, "log", log)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
