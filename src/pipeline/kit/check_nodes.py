"""Check every model against the node names its stand-in blueprint looks up by name.

    python -I src/pipeline/kit/check_nodes.py [Id ...]

Specs such as ManufactoryProgressVisualizerSpec, BotManufactoryAnimationControllerSpec, WindRotationAnimatorSpec or
ObservatoryAnimatorSpec find transforms by name at run time; a missing one throws ("Child ... not found") and crashes
the game when the building is created. Workshop, enterable and wonder animation controllers also need the model
to carry at least one animated node (they take its IAnimator and throw without one). This lists every '#Name' string in the stand-in's specs (outside Children and
attachment parents) that the model lacks, unless model.json supplies a replacement spec block that names its own
nodes (windRotationAnimator, observatoryAnimator, botManufactoryAnimation, surfaceName). Exit code 1 when a model
misses a node.
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tmio  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
ART = os.path.join(ROOT, "art", "models")
MODELS = r"E:\PandabornDev\build\models"
BP = r"E:\PandabornDev\reference\Blueprints"
OVERRIDES = {"windRotationAnimator": "WindRotationAnimatorSpec", "observatoryAnimator": "ObservatoryAnimatorSpec",
             "botManufactoryAnimation": None, "surfaceName": "GoodConsumingAttractionSurfaceControllerSpec"}
ANIMATOR_SPECS = ("WorkshopAnimationControllerSpec", "EnterableAnimationControllerSpec", "WonderAnimationControllerSpec")
SKIP_SPECS = {"Children", "TemplateAttachmentsSpec", "WaterInputPipeSpec",
              "BuildingModelSpec"}   # its node names are #Finished/#Unfinished children or optional (FindChildIfNameNotEmpty)


def names(o, out):
    if isinstance(o, dict):
        for v in o.values():
            names(v, out)
    elif isinstance(o, list):
        for v in o:
            names(v, out)
    elif isinstance(o, str) and o.startswith("#"):
        out.add(o)


def find_bp(template):
    hits = glob.glob(os.path.join(BP, "**", template + ".blueprint.json"), recursive=True)
    return hits[0] if hits else None


def main():
    ids = sys.argv[1:] or sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(ART, "*", "model.json")))
    bad = 0
    for mid in ids:
        mj = json.load(open(os.path.join(ART, mid, "model.json")))
        bpp = find_bp(mj["standIn"])
        if not bpp:
            print(f"{mid}: stand-in {mj['standIn']} not found")
            continue
        bp = json.load(open(bpp, encoding="utf-8-sig"))
        replaced = {OVERRIDES[k] for k in OVERRIDES if k in mj and OVERRIDES[k]}
        wanted = set()
        removed = set(mj.get("removeSpecs", []))
        where = {}
        for spec, body in bp.items():
            if spec in SKIP_SPECS or spec in replaced or spec in removed:
                continue
            before = set(wanted)
            if spec == "BotManufactoryAnimationControllerSpec" and "botManufactoryAnimation" in mj:
                body = dict(body, **mj["botManufactoryAnimation"])
            names(body, wanted)
            for n in wanted - before:
                where[n] = spec
        wanted -= {"#Finished", "#Unfinished"}     # blueprint children, not model nodes
        for k in ("windRotationAnimator", "observatoryAnimator"):
            if k in mj:
                names(mj[k], wanted)
        model_files = [os.path.join(MODELS, mid, f"{mj['models']['finished']}.timbermesh")] if mj["models"].get("finished") else []
        if mj.get("mergeableObjectModel"):
            model_files = [os.path.join(MODELS, mid, f"{m}.timbermesh") for m in mj["mergeableObjectModel"]["children"].values()]
        have = set()
        for f in model_files:
            if os.path.exists(f):
                have |= {n["name"] for n in tmio.load(f)}
        missing = sorted(n for n in wanted if n not in have)
        # controllers that take the model's IAnimator (GetComponentInChildren<IAnimator>) and throw without one
        needs_animator = [k for k in ANIMATOR_SPECS if k in bp and k not in removed]
        if needs_animator and model_files and os.path.exists(model_files[0]):
            if not any(n["nodeAnims"] for n in tmio.load(model_files[0])):
                missing.append("an animated node (for " + ", ".join(needs_animator) + ")")
        if missing:
            bad += 1
            print(f"{mid} ({mj['standIn']}): MISSING " + ", ".join(n if n.startswith("an animated") else f"{n} (by {where.get(n, 'model.json')})" for n in missing))
    print(f"{len(ids)} model(s) checked, {bad} missing named nodes")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
