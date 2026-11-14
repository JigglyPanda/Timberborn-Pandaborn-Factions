"""Generates the model prototype mod (dev only) from art/models/*/model.json and the vanilla stand-in blueprints.

Each building is the vanilla building closest in function with our model swapped in: footprint, entrance, slots,
colliders and attachments come from the model.json written by the model's build script. Templates end in
.PandabornProto and are added to Buildings.Folktails (which the Inkpaws faction also lists), so they are available
to both. Costs are cut to one log so builders finish them quickly in tests.

    E:\\PandabornDev\\tools\\venv\\Scripts\\python.exe -I proto/models/tools/gen_mod.py [--out E:\\PandabornDev\\build\\proto\\models]

Writes the blueprints, collection and localisation into proto/models/mod and mirrors mod + the built .timbermesh
files (from E:\\PandabornDev\\build\\models\\<Id>) into the build folder.
"""
import argparse
import copy
import glob
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
MOD = os.path.normpath(os.path.join(HERE, "..", "mod"))
ART = os.path.join(ROOT, "art", "models")
BP = r"E:\PandabornDev\reference\Blueprints"
MODELS = r"E:\PandabornDev\build\models"
SUFFIX = ".PandabornProto"
DIR = "Buildings/Pandaborn/ProtoModels"

STAND_IN = {   # stand-in vanilla template -> blueprint path under BP
    "Lodge.Folktails": "Buildings/Housing/Lodge/Lodge.Folktails.blueprint.json",
    "MiniLodge.Folktails": "Buildings/Housing/MiniLodge/MiniLodge.Folktails.blueprint.json",
    "DistrictCenter.Folktails": "Buildings/DistrictManagement/DistrictCenter/DistrictCenter.Folktails.blueprint.json",
    "ThrottlingValve.Folktails": "Buildings/Landscaping/ThrottlingValve/ThrottlingValve.Folktails.blueprint.json",
    "FillValve.Folktails": "Buildings/Landscaping/FillValve/FillValve.Folktails.blueprint.json",
    "WaterWheel.Folktails": "Buildings/Power/WaterWheel/WaterWheel.Folktails.blueprint.json",
    "SmallTank.Folktails": "Buildings/Storage/SmallTank/SmallTank.Folktails.blueprint.json",
    "MediumTank.Folktails": "Buildings/Storage/MediumTank/MediumTank.Folktails.blueprint.json",
    "LargeTank.Folktails": "Buildings/Storage/LargeTank/LargeTank.Folktails.blueprint.json",
    "DoubleLodge.Folktails": "Buildings/Housing/DoubleLodge/DoubleLodge.Folktails.blueprint.json",
    "TripleLodge.Folktails": "Buildings/Housing/TripleLodge/TripleLodge.Folktails.blueprint.json",
    "Observatory.Folktails": "Buildings/Science/Observatory/Observatory.Folktails.blueprint.json",
    "BuildersHut.Folktails": "Buildings/DistrictManagement/BuildersHut/BuildersHut.Folktails.blueprint.json",
    "Lantern.Folktails": "Buildings/Decoration/Lantern/Lantern.Folktails.blueprint.json",
    "HaulingPost.Folktails": "Buildings/DistrictManagement/HaulingPost/HaulingPost.Folktails.blueprint.json",
    "GathererFlag.Folktails": "Buildings/Food/GathererFlag/GathererFlag.Folktails.blueprint.json",
    "RooftopTerrace.Folktails": "Buildings/Wellbeing/RooftopTerrace/RooftopTerrace.Folktails.blueprint.json",
    "Hammock.Folktails": "Buildings/Decoration/Hammock/Hammock.Folktails.blueprint.json",
    "Campfire.Folktails": "Buildings/Wellbeing/Campfire/Campfire.Folktails.blueprint.json",
    "Grill.Folktails": "Buildings/Food/Grill/Grill.Folktails.blueprint.json",
    "Bakery.Folktails": "Buildings/Food/Bakery/Bakery.Folktails.blueprint.json",
    "WindTurbine.Folktails": "Buildings/Power/WindTurbine/WindTurbine.Folktails.blueprint.json",
    "WaterPump.Folktails": "Buildings/Water/WaterPump/WaterPump.Folktails.blueprint.json",
}


def v3(x, y, z):
    return {"X": x, "Y": y, "Z": z}


def load(rel):
    with open(os.path.join(BP, rel), encoding="utf-8-sig") as f:
        return json.load(f)


def model_path(mid, name):
    return f"{DIR}/{mid}/{name}"


def apply_model(bp, mj):
    mid = mj["id"]
    template = "PandabornModel" + mid + SUFFIX
    bp["TemplateSpec"] = {"TemplateName": template, "BackwardCompatibleTemplateNames": [], "RequiredFeatureToggle": "",
                          "DisablingFeatureToggle": ""}
    key = "Building.PandabornModel" + mid
    lab = bp.setdefault("LabeledEntitySpec", {})
    lab["DisplayNameLocKey"] = key + ".DisplayName"
    lab["DescriptionLocKey"] = key + ".Description"
    lab["FlavorDescriptionLocKey"] = ""
    if "BuildingSpec" in bp:
        bp["BuildingSpec"]["BuildingCost"] = []          # builders only: finishes in tests without logs
        bp["BuildingSpec"]["ScienceCost"] = 0
        # a site that "finishes" with colonists standing on it waits for them to leave (FinishIfRequirementsMet):
        # test placements next to the district centre then show the construction stage in "finished" shots
        bp["BuildingSpec"]["FinishableWithBeaversOnSite"] = True
    bos = bp["BlockObjectSpec"]
    s = mj["size"]
    if mj.get("blocks"):
        bos["Size"] = v3(s["X"], s["Y"], s["Z"])
        bos["Blocks"] = mj["blocks"]
    if mj.get("entrance"):
        e = mj["entrance"]
        bos["Entrance"] = {"HasEntrance": True, "Coordinates": v3(e["X"], e["Y"], e["Z"])}
    if mj.get("access") and "BuildingAccessibleSpec" in bp:
        bp["BuildingAccessibleSpec"]["LocalAccess"] = mj["access"]
    ch = bp["Children"]
    fin = ch["#Finished"]
    fin["TimbermeshSpec"] = {"Model": model_path(mid, mj["models"]["finished"])}
    if mj.get("colliders"):
        fin["CollidersSpec"] = {"BoxColliders": mj["colliders"], "SphereColliders": [], "CapsuleColliders": []}
    unf = ch.get("#Unfinished", {}).get("Children", {})
    for k in [k for k in unf if k.startswith("ConstructionStage") and k != "ConstructionStage0"]:
        del unf[k]
    base = f"ConstructionBase{s['X']}x{s['Y']}"
    for k in [k for k in unf if "ConstructionBase" in k]:
        del unf[k]
    # the game counts #Unfinished's children minus one base against the progress thresholds: a base is required
    # (without it every game load throws). No vanilla base for this size: the 1x1 pad under the origin cell.
    if not os.path.isdir(os.path.join(BP, "ConstructionBases", base)):
        base = "ConstructionBase1x1"
    unf[base + "#nested"] = {"BlueprintPath": f"ConstructionBases/{base}/{base}.blueprint"}
    if mj.get("connectionAnchor") and "ConnectionAnchorPointSpec" in bp:
        bp["ConnectionAnchorPointSpec"]["Position"] = mj["connectionAnchor"]
    stage_entry = {
        "TimbermeshSpec": {"Model": model_path(mid, mj["models"]["constructionStage0"])},
        "CollidersSpec": {"BoxColliders": [{"Center": v3(s["X"] / 2, 0.05, s["Y"] / 2), "Size": v3(s["X"], 0.1, s["Y"])}],
                          "SphereColliders": [], "CapsuleColliders": []}}
    # child order matters: the progress visualizer shows child 0 (the base) until construction starts, then the
    # stages in order, so the base must come first
    unf.pop("ConstructionStage0", None)
    bases = {k: v for k, v in unf.items() if "ConstructionBase" in k}
    others = {k: v for k, v in unf.items() if "ConstructionBase" not in k}
    unf.clear()
    unf.update(bases)
    unf["ConstructionStage0"] = stage_entry
    unf.update(others)
    if "ConstructionSiteProgressVisualizerSpec" in bp:
        bp["ConstructionSiteProgressVisualizerSpec"]["ProgressThresholds"] = [0.0]
    for a in mj.get("attachments", []):
        for at in bp.get("TemplateAttachmentsSpec", {}).get("Attachments", []):
            if at["AttachmentId"] == a["AttachmentId"]:
                at["Position"] = a["Position"]
    return template


# ------------------------------------------------------------------------------------------- per-building edits
def edit_flume(bp, mj, lid=False, limit=None):
    bp["ThrottlingValveSpec"]["DefaultOutflowLimitEnabled"] = limit is not None
    bp["ThrottlingValveSpec"]["DefaultOutflowLimit"] = 1.0 if limit is None else limit
    cells = mj.get("waterCells") or [{"X": 0, "Y": 0, "Z": 0}]
    obst = [dict(c) for c in cells]
    if lid:
        obst += [{"X": c["X"], "Y": c["Y"], "Z": c["Z"] + 1} for c in cells]
    bp["FinishableHorizontalWaterObstacleSpec"]["Obstacles"] = obst
    if mj.get("solidCells"):
        bp["WaterObstacleSpec"] = {"Coordinates": [{"X": c["X"], "Y": c["Y"]} for c in mj["solidCells"]]}
        bp["FinishableWaterObstacleSpec"] = {"Height": 1.0}


def edit_scoop(bp, mj):
    for k in ("FloodableBuildingSpec", "BlockableFloodableObjectSpec", "WaterObjectSpec", "WaterWheelSpec",
              "PowerGeneratorSoundsSpec", "MechanicalNodeDescriptionSpec"):
        bp.pop(k, None)
    bp["MechanicalNodeSpec"] = {"PowerOutput": 100, "PowerInput": 100, "IsShaft": False}
    bp["WaterPoweredGeneratorSpec"] = {"Blocks": [{"X": 0, "Y": 0}], "ExpectedWaterDirection": {"X": 1.0, "Y": 0.0},
                                       "MinRequiredOutflow": 0.15}
    bp["MechanicalBuildingSpec"] = {}
    bp["TransputProviderSpec"] = {"Transputs": [], "IgnoreRotation": False}
    bp["WaterMoverSpec"] = {"WaterPerSecond": 0.1}
    bp["WaterInputFixedSpec"] = {}
    bp["WaterInputSpec"] = {"WaterInputCoordinates": v3(0, 0, 0)}
    o = mj["waterOutput"]
    bp["WaterOutputSpec"] = {"WaterCoordinates": v3(o["X"], o["Y"], o["Z"]), "DistanceToGroundOffset": 0.0,
                             "OverflowAllowed": False}


def edit_spout(bp, mj):
    bp["FillValveSpec"]["DefaultTargetHeightOffset"] = 0.3
    bp["FillValveSpec"]["DefaultTargetHeightEnabled"] = True


EDITS = {
    "Flume": lambda bp, mj: edit_flume(bp, mj),
    "FlumeBridge": lambda bp, mj: edit_flume(bp, mj),
    "FlumeDrop": lambda bp, mj: edit_flume(bp, mj),
    "FlumeCorner": lambda bp, mj: (edit_flume(bp, mj, lid=True), bp.pop("ThrottlingValveSpec")),  # unlimited cell: water turns
    "FlumeGate": lambda bp, mj: edit_flume(bp, mj, lid=True, limit=0.3),
    "ScoopWheel": edit_scoop,
    "StarTower": lambda bp, mj: bp.__setitem__("ObservatoryAnimatorSpec", mj["observatoryAnimator"]),
    "KiteWindmill": lambda bp, mj: bp.__setitem__("WindRotationAnimatorSpec", mj["windRotationAnimator"]),
    "PaddySpout": edit_spout,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=r"E:\PandabornDev\build\proto\models")
    ap.add_argument("--only")
    a = ap.parse_args()
    for sub in ("Buildings", "TemplateCollections", "Localizations"):
        p = os.path.join(MOD, sub)
        if os.path.isdir(p):
            shutil.rmtree(p)
    entries, loc = [], []
    for mjp in sorted(glob.glob(os.path.join(ART, "*", "model.json"))):
        mj = json.load(open(mjp))
        mid = mj["id"]
        if a.only and mid not in a.only.split(","):
            continue
        bp = load(STAND_IN[mj["standIn"]])
        bp = copy.deepcopy(bp)
        if mid in EDITS:
            EDITS[mid](bp, mj)
        if "ManufactorySpec" in bp:
            # the stand-in's recipes name Folktails goods, which the Inkpaws faction does not have (a missing good
            # throws when the building is created); the model check needs no production
            bp["ManufactorySpec"]["ProductionRecipeIds"] = []
        for k in mj.get("removeSpecs", []):
            bp.pop(k, None)
        for k, v in mj.get("addSpecs", {}).items():
            bp[k] = v
        template = apply_model(bp, mj)
        rel = f"{DIR}/{mid}/PandabornModel{mid}{SUFFIX}.blueprint.json"
        path = os.path.join(MOD, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(bp, f, indent=2)
            f.write("\n")
        entries.append(rel[: -len(".json")])
        loc.append((f"Building.PandabornModel{mid}.DisplayName", f"[Model] {mj.get('displayName', mid)}"))
        loc.append((f"Building.PandabornModel{mid}.Description",
                    f"Model prototype of the {mj.get('displayName', mid)}, on the {mj['standIn']} blueprint."))
        print(f"{template:45s} <- {mj['standIn']}  ({mj['triangles']['finished']} tris)")
    # Folktails, and the Inkpaws (whose faction lists Buildings.Inkpaws since the catalogue generator landed)
    for cid in ("Buildings.Folktails", "Buildings.Inkpaws"):
        coll = os.path.join(MOD, "TemplateCollections", "Pandaborn",
                            f"TemplateCollection.{cid}.ProtoModels.blueprint.json")
        os.makedirs(os.path.dirname(coll), exist_ok=True)
        json.dump({"TemplateCollectionSpec": {"CollectionId": cid, "Blueprints": entries}},
                  open(coll, "w", newline="\n"), indent=2)
    lp = os.path.join(MOD, "Localizations", "enUS_PandabornProtoModels.csv")
    os.makedirs(os.path.dirname(lp), exist_ok=True)
    with open(lp, "w", encoding="utf-8", newline="\n") as f:
        f.write("ID,Text,Comment\n")
        for k, t in loc:
            f.write(f'{k},"{t}",\n')
    # mirror into the build folder with the model files (never while a game test has it junctioned into Mods)
    live = os.path.join(os.path.expanduser("~"), "Documents", "Timberborn", "Mods", os.path.basename(a.out))
    if os.path.exists(live):
        raise SystemExit(f"{live} exists: a game test is using the build folder; blueprints written to {MOD} only")
    if os.path.isdir(a.out):
        shutil.rmtree(a.out)
    shutil.copytree(MOD, a.out)
    n = 0
    for e in entries:
        mid = e.split("/")[3]
        for f in glob.glob(os.path.join(MODELS, mid, "*.timbermesh")):
            dst = os.path.join(a.out, DIR.replace("/", os.sep), mid, os.path.basename(f))
            shutil.copy2(f, dst)
            n += 1
    print(f"{len(entries)} buildings, {n} model files -> {a.out}")


if __name__ == "__main__":
    main()
