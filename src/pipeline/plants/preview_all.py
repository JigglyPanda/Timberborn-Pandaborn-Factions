"""Builds every art/plants/<Id>/build.py, renders each plant's field beside its vanilla neighbours and a lineup of every
model (seedling, mature, ripe, dry, dead, stump) for all seven plants, and writes contact sheets.

    python -I src/pipeline/plants/preview_all.py [--no-build] [--night]

Output in E:\\PandabornDev\\build\\plants\\preview: <Id>_field.png, sheet_fields.png, lineup_mature.png,
lineup_seedling.png (rows: alive, dry, dead; the mature row also shows the ripe yield and the stumps).
"""
import argparse
import glob
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import preview_plant as pp  # noqa: E402
from preview import Field, label  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
ORDER = ["PandabornTimberBamboo", "PandabornPersimmonTree", "PandabornTeaBush", "PandabornShootBamboo",
         "PandabornCabbage", "PandabornRice", "PandabornSichuanPepper"]
GATHER = ORDER[:3]


def lineup(stage, out):
    f = Field(seed=4)
    rows = [("", "alive"), ("Dry", "dry"), ("Dead", "dead")]
    for i, pid in enumerate(ORDER):
        for j, (suffix, _) in enumerate(rows):
            f.one(pp.model(pid, stage + suffix), i * 2.4, j * 2.6, rot=20)
        if stage == "Mature" and os.path.exists(pp.model(pid, "MatureStump")):
            f.one(pp.model(pid, "MatureStump"), i * 2.4, 3 * 2.6, rot=20)
    water = [{"rect": [5 * 2.4 - 0.9, -1.2, 5 * 2.4 + 1.9, 3 * 2.6 + 1], "level": 0.3}]
    f.render(out, target=(7.2, 0.8 if stage == "Mature" else 0.2, 3.4), yaw=0, pitch=42, distance=24 if stage == "Mature" else 19,
             size=(2000, 1100), detail=GATHER, water=water, ground=[-2, -2, 18, 11])
    caps = [(int(2000 * (0.09 + 0.82 * i / 6)) - 70, 10, pid.replace("Pandaborn", "")) for i, pid in enumerate(ORDER)]
    label(out, caps)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-build", action="store_true")
    ap.add_argument("--night", action="store_true")
    a = ap.parse_args()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    if not a.no_build:
        for s in sorted(glob.glob(os.path.join(REPO, "art", "plants", "*", "build.py"))):
            subprocess.run([sys.executable, "-I", s], check=True, env=env, capture_output=True)
    fields = []
    for pid in ORDER:
        fields.append(pp.field(pid))
        if a.night:
            pp.field(pid, night=True)
    from PIL import Image
    ims = [Image.open(p).convert("RGB").crop((0, 150, 1800, 750)).resize((1200, 400)) for p in fields]
    sheet = Image.new("RGB", (1200, 400 * len(ims)))
    for i, im in enumerate(ims):
        sheet.paste(im, (0, 400 * i))
    sheet.save(os.path.join(pp.OUT, "sheet_fields.png"))
    print(lineup("Mature", os.path.join(pp.OUT, "lineup_mature.png")))
    print(lineup("Seedling", os.path.join(pp.OUT, "lineup_seedling.png")))
    print(os.path.join(pp.OUT, "sheet_fields.png"))


if __name__ == "__main__":
    main()
