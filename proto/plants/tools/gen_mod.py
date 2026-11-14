"""Assembles the plants prototype mod (dev only) into E:\\PandabornDev\\build\\proto\\plants.

    python -I proto/plants/tools/gen_mod.py [--out DIR]

* proto/plants/mod (manifest, the PandabornPlants.Inkpaws material collection, the faction merge that lists it)
* for every art/plants/<Id>/model.json: the built .timbermesh stages from E:\\PandabornDev\\build\\plants\\<Id> into
  NaturalResources/Pandaborn/<Kind>/<Id>/, and a same-path optional merge onto the generated plant blueprint
  (<Id>.Inkpaws.optional.blueprint.json: model paths, preview model, randomizer, colliders) - exactly what the catalogue
  lane has to emit to adopt the models (docs/tech/plants.md)
* AssetBundles/pandabornplants_win (built by tools/build_plants.ps1; copied with its own name, never renamed)
The DLL (Scripts/PandabornProtoPlants.dll) is built by proto/plants/build.ps1. Never touches the Mods folder.

Once the faction itself ships the plants (its build has AssetBundles/pandabornplants_win, the collection and the
models: the catalogue lane adopted them on 2026-11-14), a second copy of the bundle crashes every game load ("another
AssetBundle with the same files is already loaded", run plants-pass2-1). Then (detected from the installed faction
build, or forced with --adopted) only the manifest, the plant lab DLL and the blueprint merges are written: the merges
point at the faction's own model files and add what the adopter does not read yet (per-state colliders).
"""
import argparse
import glob
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
BUNDLE = r"E:\PandabornDev\build\plants\AssetBundles\pandabornplants_win"
FACTION = r"E:\PandabornDev\build\PandabornFactions"


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
        if key in col:               # a state of its own ("Mature/#Dead": narrower, as vanilla's dead trees)
            node["CollidersSpec"] = colliders(col[key])
        elif stage in col:
            node["CollidersSpec"] = colliders(col[stage])
        models.setdefault(stage, {"Children": {}})["Children"][state] = node
    bp = {"PlantablePreviewModelSpec": {"Model": info["PlantablePreviewModelSpec.Model"]},
          "Children": {"#Models": {"Children": models}}}
    if info.get("randomizer"):
        bp["NaturalResourceModelRandomizerSpec"] = {k: v for k, v in info["randomizer"].items() if k != "note"}
    if info.get("treeCuttingRadius"):
        bp["TreeCuttingRadiusSpec"] = {"Radius": info["treeCuttingRadius"]}
    return bp


DEV_BUNDLE = r"E:\PandabornDev\build\plants\dev-bundle\pandabornplantsdev_win"
DEV_COLLECTION = "PandabornPlantsDev.Inkpaws"


def dev_materials(out, keep, ids):
    """Copies the listed plants' models to NaturalResources/Pandaborn/Dev/<Id>/ with every material renamed <name>Dev,
    points the plants' blueprints at them, and ships the dev bundle with its collection, listed by the faction."""
    import sys
    import zlib
    sys.path.insert(0, os.path.join(REPO, "src", "pipeline"))
    import model_pb2 as pb
    mats = set()
    for pid in ids:
        info = json.load(open(os.path.join(REPO, "art", "plants", pid, "model.json")))
        dev = dict(info, models={})
        d = os.path.join(out, "NaturalResources", "Pandaborn", "Dev", pid)
        os.makedirs(d, exist_ok=True)
        for key, path in info["models"].items():
            name = path.split("/")[-1]
            m = pb.Model()
            m.ParseFromString(zlib.decompress(open(os.path.join(info["builtTo"], name + ".timbermesh"), "rb").read()))
            for nd in m.nodes:
                for me in nd.meshes:
                    if me.material.startswith("Pandaborn"):
                        me.material += "Dev"
                        mats.add(me.material)
            with open(os.path.join(d, name + ".timbermesh"), "wb") as fh:
                fh.write(zlib.compress(m.SerializeToString(), 6))
            keep.add(os.path.relpath(os.path.join(d, name + ".timbermesh"), out).lower())
            dev["models"][key] = "NaturalResources/Pandaborn/Dev/%s/%s" % (pid, name)
        dev["PlantablePreviewModelSpec.Model"] = dev["models"].get("Mature/#Alive", info["PlantablePreviewModelSpec.Model"])
        bd = os.path.join(out, *info["modelDir"].split("/"))
        os.makedirs(bd, exist_ok=True)
        bp_path = os.path.join(bd, info["template"] + ".optional.blueprint.json")
        bp = blueprint(dev)
        if pid.endswith("InFlower"):
            bp.pop("PlantablePreviewModelSpec", None)    # twins are never planted (no such spec on their blueprint)
        json.dump(bp, open(bp_path, "w", encoding="utf-8"), indent=2)
        keep.add(os.path.relpath(bp_path, out).lower())
        print("dev materials:", pid, "->", "NaturalResources/Pandaborn/Dev/" + pid)
    os.makedirs(os.path.join(out, "AssetBundles"), exist_ok=True)
    shutil.copyfile(DEV_BUNDLE, os.path.join(out, "AssetBundles", os.path.basename(DEV_BUNDLE)))
    keep.add(os.path.join("assetbundles", os.path.basename(DEV_BUNDLE)).lower())
    names = ["PandabornTimberBamboo", "PandabornShootBamboo", "PandabornCabbage", "PandabornRice", "PandabornTeaBush",
             "PandabornSichuanPepper", "PandabornPersimmonTree", "PandabornShootBambooBuds"]
    coll = {"MaterialCollectionSpec": {"CollectionId": DEV_COLLECTION,
                                       "Materials": ["Materials/Pandaborn/Plants/%sDev" % n for n in names]}}
    cp = os.path.join(out, "MaterialCollections", "Pandaborn", "MaterialCollection.%s.blueprint.json" % DEV_COLLECTION)
    os.makedirs(os.path.dirname(cp), exist_ok=True)
    json.dump(coll, open(cp, "w"), indent=2)
    keep.add(os.path.relpath(cp, out).lower())
    fp = os.path.join(out, "Factions", "Pandaborn", "Faction.Inkpaws.optional.blueprint.json")
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    json.dump({"FactionSpec": {"MaterialCollectionIds#append": [DEV_COLLECTION]}}, open(fp, "w"), indent=2)
    keep.add(os.path.relpath(fp, out).lower())


def buds_test(out, keep):
    """A test-only template, PandabornShootBambooBudsTest.Inkpaws: the installed shoot bamboo's blueprint with its models
    copied onto the dev material whose detail map is baked on (build_dev_bundle.py), joined to NaturalResources.Inkpaws,
    so a test can plant a budding field beside a normal one (the Flowering module's switch is proven separately)."""
    import sys
    import zlib
    sys.path.insert(0, os.path.join(REPO, "src", "pipeline"))
    import model_pb2 as pb
    info = json.load(open(os.path.join(REPO, "art", "plants", "PandabornShootBamboo", "model.json")))
    tid = "PandabornShootBambooBudsTest"
    d = os.path.join(out, "NaturalResources", "Pandaborn", "Dev", tid)
    os.makedirs(d, exist_ok=True)
    src_bp = os.path.join(FACTION, *info["modelDir"].split("/"), info["template"] + ".blueprint.json")
    bp = json.load(open(src_bp, encoding="utf-8"))
    bp["TemplateSpec"]["TemplateName"] = tid + ".Inkpaws"
    bp["TemplateSpec"]["BackwardCompatibleTemplateNames"] = []
    for k in [k for k in bp if k.startswith("Pandaborn")]:   # no module behaviour on a test plant
        del bp[k]
    models = bp["Children"]["#Models"]["Children"]
    for key, path in info["models"].items():
        name = path.split("/")[-1]
        m = pb.Model()
        m.ParseFromString(zlib.decompress(open(os.path.join(info["builtTo"], name + ".timbermesh"), "rb").read()))
        for nd in m.nodes:
            for me in nd.meshes:
                me.material = "PandabornShootBambooBudsDev"
        open(os.path.join(d, name + ".timbermesh"), "wb").write(zlib.compress(m.SerializeToString(), 6))
        keep.add(os.path.relpath(os.path.join(d, name + ".timbermesh"), out).lower())
        stage, state = key.split("/")
        models[stage]["Children"][state]["TimbermeshSpec"]["Model"] = "NaturalResources/Pandaborn/Dev/%s/%s" % (tid, name)
    if "PlantablePreviewModelSpec" in bp:
        bp["PlantablePreviewModelSpec"]["Model"] = "NaturalResources/Pandaborn/Dev/%s/%sMature" % (tid, info["id"])
    bpp = os.path.join(d, tid + ".Inkpaws.blueprint.json")
    json.dump(bp, open(bpp, "w", encoding="utf-8"), indent=2)
    keep.add(os.path.relpath(bpp, out).lower())
    cp = os.path.join(out, "TemplateCollections", "Pandaborn", "TemplateCollection.PandabornPlantsDev.blueprint.json")
    os.makedirs(os.path.dirname(cp), exist_ok=True)
    json.dump({"TemplateCollectionSpec": {"CollectionId": "NaturalResources.Inkpaws", "Blueprints": [
        "NaturalResources/Pandaborn/Dev/%s/%s.Inkpaws.blueprint" % (tid, tid)]}}, open(cp, "w"), indent=2)
    keep.add(os.path.relpath(cp, out).lower())
    print("buds test template:", tid + ".Inkpaws")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=r"E:\PandabornDev\build\proto\plants")
    ap.add_argument("--adopted", action="store_true", help="the faction ships the plants: lab and merges only")
    ap.add_argument("--standalone", action="store_true", help="ship bundle, collection and models even if adopted")
    ap.add_argument("--dev-materials", default="",
                    help="comma list of plant ids whose models switch to the dev bundle's <name>Dev materials "
                         "(build_dev_bundle.py), for new art the installed faction's bundle does not have yet")
    ap.add_argument("--buds-test", action="store_true", help="with --dev-materials: add the budding test template")
    a = ap.parse_args()
    out = a.out
    adopted = a.adopted or (not a.standalone and
                            os.path.exists(os.path.join(FACTION, "AssetBundles", os.path.basename(BUNDLE))))
    print("mode:", "adopted by the faction (lab + merges only)" if adopted else "standalone (bundle, collection, models)")
    keep = {os.path.join("scripts", "pandabornprotoplants.dll")}
    src = os.path.join(REPO, "proto", "plants", "mod")
    for root, _, files in os.walk(src):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), src)
            if adopted and rel != "manifest.json":
                continue
            os.makedirs(os.path.dirname(os.path.join(out, rel)), exist_ok=True)
            shutil.copyfile(os.path.join(root, f), os.path.join(out, rel))
            keep.add(rel.lower())
    for mj in sorted(glob.glob(os.path.join(REPO, "art", "plants", "*", "model.json"))):
        info = json.load(open(mj))
        d = os.path.join(out, *info["modelDir"].split("/"))
        os.makedirs(d, exist_ok=True)
        paths = set(info["models"].values())
        if adopted:   # only the meshes the faction does not ship yet (e.g. the flowering twins before adoption)
            paths = {pth for pth in paths if not os.path.exists(os.path.join(FACTION, *pth.split("/")) + ".timbermesh")}
        for path in paths:
            name = path.split("/")[-1] + ".timbermesh"
            shutil.copyfile(os.path.join(info["builtTo"], name), os.path.join(d, name))
            keep.add(os.path.relpath(os.path.join(d, name), out).lower())
        bp_path = os.path.join(d, info["template"] + ".optional.blueprint.json")
        with open(bp_path, "w", encoding="utf-8") as fh:
            json.dump(blueprint(info), fh, indent=2)
        keep.add(os.path.relpath(bp_path, out).lower())
        print("plant", info["id"], "->", info["modelDir"], "(%d models)" % len(set(info["models"].values())))
    if not adopted:
        os.makedirs(os.path.join(out, "AssetBundles"), exist_ok=True)
        shutil.copyfile(BUNDLE, os.path.join(out, "AssetBundles", os.path.basename(BUNDLE)))
        keep.add(os.path.join("assetbundles", os.path.basename(BUNDLE)).lower())
    if a.dev_materials:
        dev_materials(out, keep, [x.strip() for x in a.dev_materials.split(",") if x.strip()])
        if a.buds_test:
            buds_test(out, keep)
    for root, _, files in os.walk(out):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), out)
            if rel.lower() not in keep:
                os.remove(os.path.join(root, f))
                print("removed stale", rel)
    print("mod ->", out)


if __name__ == "__main__":
    main()
