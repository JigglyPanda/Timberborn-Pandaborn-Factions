"""The Inkpaws wonder-completion picture: night, the Sky Lantern's great lantern risen above the village, homes with
lit windows, strings of lanterns, small lanterns drifting up, warm light against a deep blue sky. Rendered in Blender
from the faction's own models (art/models; run their build.py first), no characters.

    python -I src/pipeline/kit/wonder_image.py [--out PNG] [--samples 160] [--preview]

The vanilla pictures (FactionSpec.WonderCompletionImage, UI/Images/WonderCompletion/wonder-completion-folktails) are
1514 x 348 RGB sprites without mipmaps; this one matches. Default output:
mod/PandabornFactions/Sprites/Pandaborn/WonderCompletion/wonder-completion-inkpaws.png (+ .meta.json, isSprite).
"""
import argparse
import json
import math
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
import preview  # noqa: E402
import tmio  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
MODELS = r"E:\PandabornDev\build\models"
DEFAULT_OUT = os.path.join(ROOT, "mod", "PandabornFactions", "Sprites", "Pandaborn", "WonderCompletion",
                           "wonder-completion-inkpaws.png")
SIZE = (1514, 348)


def drifting_lantern():
    """A small paper sky lantern (no string, open at the bottom), built with the kit into the build folder."""
    from building import Model
    import parts as K
    m = Model("WonderDriftLantern", size=(1, 1, 1), seed=5, stand_in="Lantern.Folktails")
    K.lantern(m.geo, (0.5, 0.0, 0.5), r=0.22, h=0.5, hanging=False)
    m.build(write_json=False)
    return os.path.join(MODELS, "WonderDriftLantern", "WonderDriftLantern.Model.timbermesh")


def hills():
    """Far hills behind the village (soft dark cones, a Sichuan skyline), built with the kit into the build folder."""
    from building import Model
    import parts as K
    m = Model("WonderHills", size=(1, 1, 1), seed=7, stand_in="Lantern.Folktails")
    rng = np.random.default_rng(3)
    for k in range(22):
        x, z = -330 + k * 30 + rng.uniform(-10, 10), 200 + rng.uniform(0, 90)
        h, r = rng.uniform(16, 34), rng.uniform(36, 60)
        K.lathe(m.geo, [(r, 0.0), (r * 0.55, h * 0.55), (r * 0.18, h * 0.95), (0.0, h)], (x, -0.5, z), 10, "Moss.Folktails",
                cap_top=False)
        m.geo.parts[-1].C = np.tile([0.075, 0.095, 0.17, 1.0], (len(m.geo.parts[-1].P), 1))
        m.geo.parts[-1].tags.add("noshade")
    m.build(write_json=False, ao=False)
    return os.path.join(MODELS, "WonderHills", "WonderHills.Model.timbermesh")


# (model id, unity x, unity z, animation time or None): the village spread left and right of the wonder, homes
# nearer the camera, the Sky Lantern behind them with its great lantern partway up its launch
LAYOUT = [
    ("SkyLantern", -3.6, 6.0, 0.2),
    ("VillageHall", -15.5, 2.5, None), ("StarTower", -21.0, 6.0, None), ("MoonLoft", -11.0, 0.5, None),
    ("Den", -8.0, -2.5, None), ("CourtyardHouse", -18.5, -1.5, None), ("Den", -24.0, 1.5, None),
    ("Teahouse", 7.5, 2.0, None), ("Den", 4.5, -2.5, None), ("CourtyardHouse", 11.5, -0.5, None),
    ("TerraceHouse", 15.0, 3.5, None), ("Den", 18.5, 0.0, None), ("MoonLoft", 22.0, 3.0, None),
    ("Kindergarten", 25.0, 6.5, None), ("Den", -28.5, 5.5, None),
    ("StringLanterns", -2.5, -4.5, None), ("StringLanterns", -1.5, -4.5, None), ("StringLanterns", 0.5, -4.5, None),
    ("StandingLantern", -5.0, -4.0, None), ("StandingLantern", 3.0, -4.0, None), ("HangingLantern", 9.5, -2.0, None),
    ("HangingLantern", -13.0, -1.0, None), ("StandingLantern", -20.0, -3.0, None), ("StandingLantern", 15.0, -2.5, None),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--samples", type=int, default=160)
    ap.add_argument("--preview", action="store_true", help="write to the build folder instead of the mod")
    a = ap.parse_args()
    out = os.path.join(MODELS, "preview", "wonder-completion-inkpaws.png") if a.preview else a.out
    os.makedirs(preview.TMP, exist_ok=True)
    work = tempfile.mkdtemp(dir=preview.TMP)
    items = []
    for i, (mid, x, z, t) in enumerate(LAYOUT):
        path = os.path.join(MODELS, mid, f"{mid}.Model.timbermesh")
        items.append({"npz": tmio.to_npz(path, os.path.join(work, f"m{i}.npz"), offset=(x, 0.0, z), frame=t)})
    # the great lantern's position at that moment (for the warm light it throws on the village)
    lantern = [n for n in tmio.load(os.path.join(MODELS, "SkyLantern", "SkyLantern.Model.timbermesh"), 0.2)
               if n["name"] == "#SkyLanternAnimated"][0]["world"][:3, 3] + np.array([-3.6, 1.8, 6.0])
    items.append({"npz": tmio.to_npz(hills(), os.path.join(work, "hills.npz"))})
    small = drifting_lantern()
    rng = np.random.default_rng(11)
    for k in range(16):
        x, y, z = rng.uniform(-24, 22), rng.uniform(5.5, 11.0), rng.uniform(4, 22)
        if abs(x - lantern[0]) < 3.5 and abs(y - lantern[1]) < 3.5:
            continue
        items.append({"npz": tmio.to_npz(small, os.path.join(work, f"s{k}.npz"), offset=(x, y, z))})
    L = [-float(lantern[0]), -float(lantern[2]), float(lantern[1])]   # Blender coordinates
    job = {"items": items, "textures": os.path.join(preview.LOOK, "Textures"),
           "spec": os.path.join(preview.LOOK, "look_spec.json"), "out": {"night": out}, "size": list(SIZE),
           "samples": a.samples, "grid": [-300, -300, 300, 300], "groundColor": (0.035, 0.05, 0.035),
           "sky": [(0.045, 0.06, 0.17), (0.004, 0.007, 0.03), 1.0], "sunEnergy": 0.3, "emission": 9.0,
           "emissionByVertexColor": True,
           "camera": {"loc": (0.0, 31.0, 4.4), "target": (0.0, -4.0, 5.6), "lens": 26},
           "lights": [{"type": "POINT", "loc": L, "energy": 9000, "color": (1.0, 0.55, 0.25), "radius": 2.0},
                      {"type": "POINT", "loc": (2.0, 6.0, 1.6), "energy": 300, "color": (1.0, 0.6, 0.3), "radius": 1.0},
                      {"type": "POINT", "loc": (-14.0, 2.0, 2.0), "energy": 250, "color": (1.0, 0.6, 0.3), "radius": 1.0},
                      {"type": "POINT", "loc": (14.0, 2.0, 2.0), "energy": 250, "color": (1.0, 0.6, 0.3), "radius": 1.0}]}
    jp = os.path.join(work, "job.json")
    json.dump(job, open(jp, "w"))
    env = dict(os.environ, BLENDER_USER_RESOURCES=r"E:\PandabornDev\tools\blender-userdata", TEMP=preview.TMP,
               TMP=preview.TMP)
    r = subprocess.run([preview.BLENDER, "-b", "--factory-startup", "--python", os.path.join(HERE, "blender_preview.py"),
                        "--", jp], env=env, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(out):
        print(r.stdout[-3000:], r.stderr[-3000:])
        raise SystemExit("blender failed")
    from PIL import Image
    Image.open(out).convert("RGB").save(out)       # RGB like the vanilla sprite
    if not a.preview:
        with open(out + ".meta.json", "w") as f:
            f.write('{"isSprite": true}')
    print(out)


if __name__ == "__main__":
    main()
