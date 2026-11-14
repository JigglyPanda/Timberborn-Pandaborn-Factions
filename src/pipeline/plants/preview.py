"""Field previews of plant models (ours beside vanilla), rendered in Blender Cycles from the game's angle.

Library use (art/plants/*/build.py, preview_all.py):
    from preview import Field
    f = Field()
    f.block("NaturalResources/.../X.timbermesh", origin=(0, 0), size=(5, 4), rand=(0.9, 1.1, 0.9, 1.1))
    f.render(out_png, target=(5, 0, 3), yaw=0, pitch=50, distance=18)

Materials: ours from E:\\PandabornDev\\build\\plants\\textures\\plants_preview.json (written by textures.py: albedo,
normal, detail per material), vanilla ones from the reference dump (E:\\PandabornDev\\reference\\vanilla-assets,
materials.json + textures, never committed). Vanilla models from E:\\PandabornDev\\reference\\vanilla-plants.
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import mesh as pm  # noqa: E402

BLENDER = r"E:\PandabornDev\tools\blender-4.5-lts\blender-4.5.16-windows-x64\blender.exe"
TMP = r"E:\PandabornDev\tools\tmp"
VANILLA_MODELS = r"E:\PandabornDev\reference\vanilla-plants"
VANILLA_ASSETS = r"E:\PandabornDev\reference\vanilla-assets"
OURS = r"E:\PandabornDev\build\plants\textures\plants_preview.json"


def vanilla_materials():
    out = {}
    path = os.path.join(VANILLA_ASSETS, "materials.json")
    if not os.path.exists(path):
        return out
    for m in json.load(open(path))["materials"].values():
        if m["shader"] != "Shader Graphs/VegetationURP":
            continue
        t = m["textures"]

        def tex(key):
            n = t.get(key, {}).get("name")
            p = os.path.join(VANILLA_ASSETS, "textures", n + ".png") if n else None
            return p if p and os.path.exists(p) else None
        out[m["name"]] = {"D": tex("_MainTex"), "N": tex("_BumpMap"), "Detail": tex("_DetailMap"),
                          "detailUseColor": m["floats"].get("_DetailUseColor", 0)}
    return out


def our_materials():
    return json.load(open(OURS)) if os.path.exists(OURS) else {}


def vanilla(name):
    return os.path.join(VANILLA_MODELS, name + ".timbermesh")


class Field:
    def __init__(self, seed=3):
        self.rng = np.random.default_rng(seed)
        self.instances = []
        self.models = {}
        self.detail = set()
        self.water = []
        self.wet = []
        self.grounds = []

    def _key(self, path):
        if path not in self.models:
            self.models[path] = "m%d" % len(self.models)
        return self.models[path]

    def one(self, path, x, z, y=0.0, rot=None, w=1.0, h=1.0):
        self.instances.append({"model": self._key(path), "pos": [x, y, z],
                               "rot": float(self.rng.uniform(0, 360)) if rot is None else rot, "w": w, "h": h})

    def block(self, path, origin, size, rand=(1, 1, 1, 1), rot="free", y=0.0, fill=1.0, pick=None):
        """size (nx, nz) cells from origin (x, z). rand = (min h, max h, min w, max w) as NaturalResourceModelRandomizerSpec.
        rot: 'free' (0..360), 'by90', or a fixed number. pick: list of paths to choose from per cell instead of `path`."""
        x0, z0 = origin
        for i in range(size[0]):
            for j in range(size[1]):
                if fill < 1.0 and self.rng.random() > fill:
                    continue
                h = float(self.rng.uniform(rand[0], rand[1]))
                w = float(self.rng.uniform(rand[2], rand[3]))
                if rot == "free":
                    r = float(self.rng.uniform(0, 360))
                elif rot == "by90":
                    r = 90.0 * int(self.rng.integers(0, 4))
                else:
                    r = float(rot)
                p = pick[int(self.rng.integers(0, len(pick)))] if pick else path
                self.one(p, x0 + i, z0 + j, y, r, w, h)

    def render(self, out, target, yaw=0.0, pitch=50.0, distance=20.0, focal=50, size=(1600, 1000), samples=40,
               night=False, ground=None, ground_color=None, detail=(), water=None, wet=None, grounds=None):
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        os.makedirs(TMP, exist_ok=True)
        work = tempfile.mkdtemp(dir=TMP)
        mats = vanilla_materials()
        mats.update(our_materials())
        for name in detail:
            if name in mats:
                mats[name] = dict(mats[name], detail=True)
        models = {}
        for path, key in self.models.items():
            models[key] = pm.to_blender_npz(path, os.path.join(work, key + ".npz"))
        xs = [i["pos"][0] for i in self.instances]
        zs = [i["pos"][2] for i in self.instances]
        if ground is None and not grounds:
            ground = [min(xs) - 3, min(zs) - 3, max(xs) + 4, max(zs) + 4]
        job = {"materials": mats, "models": models, "instances": self.instances, "ground": ground,
               "grounds": grounds or [], "groundColor": ground_color or [0.30, 0.31, 0.17], "water": water or [],
               "wet": wet or [], "camera": {"target": list(target), "yaw": yaw, "pitch": pitch, "distance": distance,
                                           "focal": focal},
               "size": list(size), "samples": samples, "night": night, "out": os.path.abspath(out)}
        jp = os.path.join(work, "job.json")
        json.dump(job, open(jp, "w"))
        env = dict(os.environ, BLENDER_USER_RESOURCES=r"E:\PandabornDev\tools\blender-userdata", TEMP=TMP, TMP=TMP)
        r = subprocess.run([BLENDER, "-b", "--factory-startup", "--python", os.path.join(_HERE, "blender_field.py"),
                            "--", jp], env=env, capture_output=True, text=True)
        if r.returncode != 0 or "WROTE" not in r.stdout:
            print(r.stdout[-4000:], r.stderr[-3000:])
            raise RuntimeError("blender failed")
        return out


def label(png, texts, size=22):
    """Writes captions [(x, y, text)] onto a rendered PNG (top-left pixel coordinates)."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.open(png).convert("RGB")
    d = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("arial.ttf", size)
    except OSError:
        font = None
    for x, y, t in texts:
        d.text((x + 1, y + 1), t, fill=(0, 0, 0), font=font)
        d.text((x, y), t, fill=(255, 255, 255), font=font)
    im.save(png)
    return png
