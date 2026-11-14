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
WARM_MODELS = r"E:\PandabornDev\build\models_warm"
WARM_IDS = ("SkyLantern", "StringLanterns", "StandingLantern", "HangingLantern")


def drifting_lanterns():
    """Small paper sky lanterns in three sizes (no string), built with the kit into the build folder."""
    from building import Model
    import parts as K
    out = []
    for i, r in enumerate((0.16, 0.24, 0.34)):
        mid = f"WonderDriftLantern{i}"
        m = Model(mid, size=(1, 1, 1), seed=5 + i, stand_in="Lantern.Folktails")
        K.lantern(m.geo, (0.5, 0.0, 0.5), r=r, h=r * 2.3, hanging=False)
        m.build(write_json=False)
        out.append(os.path.join(os.environ.get("PB_MODELS_OUT", MODELS), mid, mid + ".Model.timbermesh"))
    return out


def hills():
    """Far hills behind the village: three soft layers of rounded Sichuan hills, each farther layer paler and bluer
    (aerial perspective), every hill fading into a band of mist at its foot. Unlit vertex colour (preview-only
    'Unlit' material), so the layers read as painted depth, not black cut-outs."""
    from building import Model
    import parts as K
    m = Model("WonderHills", size=(1, 1, 1), seed=7, stand_in="Lantern.Folktails")
    rng = np.random.default_rng(3)
    mist = np.array([0.075, 0.08, 0.15])
    layers = [  # (count, z range, height range, radius range, top colour)
        (16, (330, 420), (22, 38), (70, 110), np.array([0.085, 0.09, 0.19])),
        (18, (220, 300), (14, 25), (50, 80), np.array([0.05, 0.058, 0.13])),
        (20, (130, 190), (7, 14), (34, 56), np.array([0.028, 0.035, 0.08])),
    ]
    for count, zr, hr, rr, top in layers:
        span = 900 if zr[0] > 300 else 650
        for k in range(count):
            x = -span / 2 + k * span / count + rng.uniform(-14, 14)
            z, h, r = rng.uniform(*zr), rng.uniform(*hr), rng.uniform(*rr)
            prof = [(r, 0.0), (r * 0.78, h * 0.3), (r * 0.5, h * 0.62), (r * 0.25, h * 0.88), (0.0, h)]
            K.lathe(m.geo, prof, (x, -2.0, z), 14, "Unlit.Hills", cap_top=False)
            part = m.geo.parts[-1]
            t = np.clip((part.P[:, 1] + 2.0) / (h * 0.45), 0, 1)[:, None] ** 0.8   # 0 at the foot (mist), 1 up high
            part.C = np.concatenate([mist + (top - mist) * t, np.ones((len(t), 1))], 1)
            part.tags.add("noshade")
    m.build(write_json=False, ao=False)
    return os.path.join(os.environ.get("PB_MODELS_OUT", MODELS), "WonderHills", "WonderHills.Model.timbermesh")


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
    ap.add_argument("--warm-look", default=r"E:\PandabornDev\build\models\study\look_after",
                    help="texture set with the warm lantern patches (models.md, 'Lantern glow colour'); '' = the look "
                         "lane's current textures")
    a = ap.parse_args()
    out = os.path.join(MODELS, "preview", "wonder-completion-inkpaws.png") if a.preview else a.out
    os.makedirs(preview.TMP, exist_ok=True)
    work = tempfile.mkdtemp(dir=preview.TMP)
    warm = bool(a.warm_look) and os.path.isdir(a.warm_look)
    if warm:
        # the lanterns in their warm patches (a picture need not wait for the sheet): trial builds of the lantern-heavy
        # models into models_warm, and the drifting lanterns built warm as well
        os.environ["PB_LANTERN_WARM"] = "1"
        os.environ["PB_MODELS_OUT"] = WARM_MODELS
        for mid in WARM_IDS:
            subprocess.run([sys.executable, "-I", os.path.join(ROOT, "art", "models", mid, "build.py")], check=True,
                           capture_output=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    items = []
    for i, (mid, x, z, t) in enumerate(LAYOUT):
        base = WARM_MODELS if warm and mid in WARM_IDS else MODELS
        path = os.path.join(base, mid, f"{mid}.Model.timbermesh")
        items.append({"npz": tmio.to_npz(path, os.path.join(work, f"m{i}.npz"), offset=(x, 0.0, z), frame=t)})
    # the great lantern's position at that moment (for the warm light it throws on the village)
    lantern = [n for n in tmio.load(os.path.join(WARM_MODELS if warm else MODELS, "SkyLantern", "SkyLantern.Model.timbermesh"), 0.2)
               if n["name"] == "#SkyLanternAnimated"][0]["world"][:3, 3] + np.array([-3.6, 1.8, 6.0])
    items.append({"npz": tmio.to_npz(hills(), os.path.join(work, "hills.npz"))})
    small = drifting_lanterns()
    rng = np.random.default_rng(11)
    k = 0
    while k < 46:   # lanterns of varied size and depth, a few low over the roofs, most drifting up and away
        x, z = rng.uniform(-30, 28), rng.uniform(-2, 70)
        y = rng.uniform(3.5, 9.0) + z * rng.uniform(0.05, 0.16)
        if abs(x - lantern[0]) < 4.0 and abs(y - lantern[1]) < 4.0 and z < 14:
            continue
        size = 2 if z < 10 else (1 if z < 35 else 0)
        items.append({"npz": tmio.to_npz(small[size], os.path.join(work, f"s{k}.npz"), offset=(x, y, z))})
        k += 1
    L = [-float(lantern[0]), -float(lantern[2]), float(lantern[1])]   # Blender coordinates
    look = a.warm_look if warm else preview.LOOK
    job = {"items": items, "textures": os.path.join(look, "Textures"),
           "spec": os.path.join(look, "look_spec.json"), "out": {"night": out}, "size": list(SIZE),
           "samples": a.samples, "grid": [-600, -600, 600, 600], "groundColor": (0.065, 0.075, 0.08),
           "skyRamp": [[0.0, (0.3, 0.17, 0.12)], [0.05, (0.16, 0.1, 0.14)], [0.16, (0.05, 0.06, 0.16)],
                       [0.45, (0.012, 0.018, 0.07)], [1.0, (0.004, 0.006, 0.03)]],
           "skyStrength": 1.0, "stars": [140.0, 0.07, 3.0], "sunEnergy": 0.7, "emission": 2.2,
           "emissionByVertexColor": True,
           "camera": {"loc": (0.0, 31.0, 4.4), "target": (0.0, -4.0, 5.6), "lens": 26},
           "lights": [{"type": "POINT", "loc": L, "energy": 14000, "color": (1.0, 0.5, 0.2), "radius": 2.0},
                      {"type": "POINT", "loc": (2.0, 6.0, 1.6), "energy": 500, "color": (1.0, 0.6, 0.3), "radius": 1.0},
                      {"type": "POINT", "loc": (-14.0, 2.0, 2.5), "energy": 600, "color": (1.0, 0.6, 0.3), "radius": 1.5},
                      {"type": "POINT", "loc": (14.0, 2.0, 2.5), "energy": 600, "color": (1.0, 0.6, 0.3), "radius": 1.5},
                      {"type": "POINT", "loc": (-24.0, 4.0, 3.0), "energy": 400, "color": (1.0, 0.6, 0.3), "radius": 1.5},
                      {"type": "POINT", "loc": (22.0, 4.0, 3.0), "energy": 400, "color": (1.0, 0.6, 0.3), "radius": 1.5},
                      {"type": "AREA", "loc": (0.0, 18.0, 16.0), "energy": 6000, "color": (0.55, 0.62, 1.0), "radius": 40.0}]}
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
