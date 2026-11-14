"""Assembles the plants prototype mod (dev only) into E:\\PandabornDev\\build\\proto\\plants.

    python -I proto/plants/tools/gen_mod.py [--out DIR]

* proto/plants/mod (manifest, the PandabornPlants.Inkpaws material collection, the faction merge that lists it)
* for every art/plants/<Id>/model.json: the built .timbermesh stages from E:\\PandabornDev\\build\\plants\\<Id> into
  NaturalResources/Pandaborn/<Kind>/<Id>/, and a same-path optional merge onto the generated plant blueprint
  (<Id>.Inkpaws.optional.blueprint.json: model paths, preview model, randomizer, colliders) - exactly what the catalogue
  lane has to emit to adopt the models (docs/tech/plants.md)
* AssetBundles/pandabornplants_win (built by tools/build_plants.ps1; copied with its own name, never renamed)
The DLL (Scripts/PandabornProtoPlants.dll) is built by proto/plants/build.ps1. Never touches the Mods folder.
"""
import argparse
import glob
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
BUNDLE = r"E:\PandabornDev\build\plants\AssetBundles\pandabornplants_win"


def vec(v):
    return {"X": float(v[0]), "Y": float(v[1]), "Z": float(v[2])}


def colliders(spec):
    out = {"BoxColliders": [], "SphereColliders": [], "CapsuleColliders": []}
    if "box" in spec:
        out["BoxColliders"].append({"Center": vec(spec["box"]["center"]), "Size": vec(spec["box"]["size"])})
    if "capsule" in spec:
        c = spec["capsule"]
        out["CapsuleColliders"].append({"Center": vec(c["center"]), "Radius": c["radius"], "Height": c["height"], "Axis": "Y"})
    return out


def blueprint(info):
    models = {}
    col = info.get("colliders") if isinstance(info.get("colliders"), dict) else {}
    for key, path in info["models"].items():
        if key == "#Leftover":
            node = {"TimbermeshSpec": {"Model": path}}
            if "#Leftover" in col:
                node["CollidersSpec"] = colliders(col["#Leftover"])
            models["#Leftover"] = node
            continue
        stage, state = key.split("/")
        node = {"TimbermeshSpec": {"Model": path}}
        if stage in col:
            node["CollidersSpec"] = colliders(col[stage])
        models.setdefault(stage, {"Children": {}})["Children"][state] = node
    bp = {"PlantablePreviewModelSpec": {"Model": info["PlantablePreviewModelSpec.Model"]},
          "Children": {"#Models": {"Children": models}}}
    if info.get("randomizer"):
        bp["NaturalResourceModelRandomizerSpec"] = {k: v for k, v in info["randomizer"].items() if k != "note"}
    if info.get("treeCuttingRadius"):
        bp["TreeCuttingRadiusSpec"] = {"Radius": info["treeCuttingRadius"]}
    return bp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=r"E:\PandabornDev\build\proto\plants")
    a = ap.parse_args()
    out = a.out
    keep = {os.path.join("scripts", "pandabornprotoplants.dll")}
    src = os.path.join(REPO, "proto", "plants", "mod")
    for root, _, files in os.walk(src):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), src)
            os.makedirs(os.path.dirname(os.path.join(out, rel)), exist_ok=True)
            shutil.copyfile(os.path.join(root, f), os.path.join(out, rel))
            keep.add(rel.lower())
    for mj in sorted(glob.glob(os.path.join(REPO, "art", "plants", "*", "model.json"))):
        info = json.load(open(mj))
        d = os.path.join(out, *info["modelDir"].split("/"))
        os.makedirs(d, exist_ok=True)
        for path in set(info["models"].values()):
            name = path.split("/")[-1] + ".timbermesh"
            shutil.copyfile(os.path.join(info["builtTo"], name), os.path.join(d, name))
            keep.add(os.path.relpath(os.path.join(d, name), out).lower())
        bp_path = os.path.join(d, info["template"] + ".optional.blueprint.json")
        with open(bp_path, "w", encoding="utf-8") as fh:
            json.dump(blueprint(info), fh, indent=2)
        keep.add(os.path.relpath(bp_path, out).lower())
        print("plant", info["id"], "->", info["modelDir"], "(%d models)" % len(set(info["models"].values())))
    os.makedirs(os.path.join(out, "AssetBundles"), exist_ok=True)
    shutil.copyfile(BUNDLE, os.path.join(out, "AssetBundles", os.path.basename(BUNDLE)))
    keep.add(os.path.join("assetbundles", os.path.basename(BUNDLE)).lower())
    for root, _, files in os.walk(out):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), out)
            if rel.lower() not in keep:
                os.remove(os.path.join(root, f))
                print("removed stale", rel)
    print("mod ->", out)


if __name__ == "__main__":
    main()
