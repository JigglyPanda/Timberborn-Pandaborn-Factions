"""Generates the water dev mod's blueprints (proto/water/mod) from vanilla blueprints and the art kit's models.

Dev only (built by proto/water/build.ps1 on top of a copy of the generated faction build). Templates end in
.PandabornProto and join the Inkpaws collections (Buildings.Inkpaws, NaturalResources.Inkpaws) by CollectionId, next to
the catalogue's own stand-ins. Water pieces use the art kit's models (art/models/<Id>/model.json; meshes from
E:\\PandabornDev\\build\\models, copied by the build script) and the Pandaborn.Water specs, with the module-off data
contract described in docs/tech/water.md ("For the catalogue lane"). Rerun after a game update:

    E:\\PandabornDev\\tools\\venv\\Scripts\\python.exe -I proto/water/tools/gen_blueprints.py
"""
import copy
import json
import os
import sys

BP = r"E:\PandabornDev\reference\Blueprints"
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
MODELS = os.path.join(REPO, "art", "models")
MOD = os.path.normpath(os.path.join(HERE, "..", "mod"))
SUFFIX = ".PandabornProto"
BUILD_DIR = "Buildings/Pandaborn/ProtoWater"
PLANT_DIR = "NaturalResources/Pandaborn/ProtoWater"

loc = []          # (key, text)
buildings = []    # collection entries
plants = []
kit_models = []   # art-kit model ids whose meshes the build script copies


def load(rel):
    with open(os.path.join(BP, rel), encoding="utf-8-sig") as f:
        return json.load(f)


def write(rel, data):
    path = os.path.join(MOD, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def v3(x, y, z):
    return {"X": x, "Y": y, "Z": z}


def v2(x, y):
    return {"X": x, "Y": y}


def block(matter="GroundOrStackable", occ="Bottom, Top, Corners, Path, Middle", stackable="None"):
    return {"MatterBelow": matter, "Occupations": occ, "Stackable": stackable, "OccupyAllBelow": False, "Underground": False}


def blocks_spec(size, blocks, entrance=None, base_z=0, flippable=False):
    """blocks: dict {(x,y,z): block}; missing cells get Occupations None."""
    sx, sy, sz = size
    out = []
    for z in range(sz):
        for y in range(sy):
            for x in range(sx):
                out.append(blocks.get((x, y, z), block("Any", "None")))
    return {
        "Size": v3(sx, sy, sz), "Blocks": out,
        "Entrance": entrance or {"HasEntrance": False, "Coordinates": v3(0, 0, 0)},
        "BaseZ": base_z, "Overridable": False, "Flippable": flippable,
    }


def name_building(bp, short, display, description, tool_group=None, tool_order=None, cost=None):
    template = "Pandaborn" + short + SUFFIX
    bp["TemplateSpec"] = {"TemplateName": template, "BackwardCompatibleTemplateNames": [],
                          "RequiredFeatureToggle": "", "DisablingFeatureToggle": ""}
    key = "Building.PandabornProto" + short          # distinct from the catalogue's Building.Pandaborn<Id> keys
    label = bp.setdefault("LabeledEntitySpec", {})
    label["DisplayNameLocKey"] = key + ".DisplayName"
    label["DescriptionLocKey"] = key + ".Description"
    label["FlavorDescriptionLocKey"] = ""
    loc.append((key + ".DisplayName", "[Proto] " + display))
    loc.append((key + ".Description", description))
    if "BuildingSpec" in bp:
        bp["BuildingSpec"]["BuildingCost"] = cost or [{"Id": "Log", "Amount": 2}]
        bp["BuildingSpec"]["ScienceCost"] = 0
    if tool_group:
        bp["PlaceableBlockObjectSpec"]["ToolGroupId"] = tool_group
    if tool_order is not None:
        bp["PlaceableBlockObjectSpec"]["ToolOrder"] = tool_order
    rel = f"{BUILD_DIR}/{short}/Pandaborn{short}{SUFFIX}.blueprint.json"
    write(rel, bp)
    buildings.append(rel[: -len(".json")])
    return template


def kit(bp, model_id):
    """Takes the art kit's footprint, blocks, colliders and meshes (copied by the build script beside the blueprint)."""
    m = json.load(open(os.path.join(MODELS, model_id, "model.json"), encoding="utf-8"))
    kit_models.append(model_id)
    if m.get("blocks"):
        s = m["size"]
        bp["BlockObjectSpec"]["Size"] = s
        bp["BlockObjectSpec"]["Blocks"] = m["blocks"]
    if m.get("entrance"):
        bp["BlockObjectSpec"]["Entrance"] = {"HasEntrance": True, "Coordinates": m["entrance"]}
    path = f"{BUILD_DIR}/Models/{model_id}/{model_id}"
    fin = bp["Children"]["#Finished"]
    fin["TimbermeshSpec"] = {"Model": path + ".Model"}
    fin["CollidersSpec"] = {"BoxColliders": m["colliders"], "SphereColliders": [], "CapsuleColliders": []}
    un = bp["Children"].get("#Unfinished", {}).get("Children", {})
    for k, v in un.items():
        if "TimbermeshSpec" in v:
            v["TimbermeshSpec"]["Model"] = path + ".ConstructionStage0.Model"
    return m


def flume_piece(model_id, flow_cells, floors, inert_height, solid_cells=()):
    """A flume piece on the throttling valve's building shell, with the module-off contract: a vanilla full obstacle
    over the flow cells (inert block) that the water module lifts."""
    bp = load("Buildings/Landscaping/ThrottlingValve/ThrottlingValve.Folktails.blueprint.json")
    del bp["ThrottlingValveSpec"]
    kit(bp, model_id)
    bp["PandabornFlumeSegmentSpec"] = {"FlowCells": [v3(*c) for c in flow_cells]}
    bp["FinishableHorizontalWaterObstacleSpec"]["Obstacles"] = [v3(*c) for c in floors]
    bp["WaterObstacleSpec"] = {"Coordinates": [v2(0, 0)]}
    bp["FinishableWaterObstacleSpec"] = {"Height": inert_height}
    if solid_cells:
        bp["PandabornSolidCellsSpec"] = {"Cells": [v3(*c) for c in solid_cells]}
    return bp


# Occupations that let exactly one thing stand over a ground flume: the Bridge span. The flume leaves its cell's corners
# free; the span's leg takes only the corners (and is supported by the ground, unlike a leg that occupies nothing, which
# the game deletes on load as "not supported by terrain physics"); a regular Bridge leg also takes Bottom, so it cannot
# be built over a flume (its inert obstacle would share the flume's cell).
FLUME_OCCUPATIONS = "Bottom, Middle, Path"
BRIDGE_LEG = "Corners, Bottom"
SPAN_LEG = "Corners"


def flumes():
    bp = flume_piece("Flume", [(0, 0, 0)], [(0, 0, 0)], 1.0)
    bp["BlockObjectSpec"]["Blocks"][0]["Occupations"] = FLUME_OCCUPATIONS
    name_building(bp, "Flume", "Flume", "Carries water one way along the arrow, level or downhill.", "Landscaping", 38)

    bp = flume_piece("Flume", [(0, 0, 0)], [(0, 0, 0), (0, 0, 1)], 1.0, [(0, 0, 1)])
    bp["BlockObjectSpec"]["Blocks"][0]["Stackable"] = "BlockObject"   # a path can stand on it
    name_building(bp, "FlumeCovered", "Flume (covered)", "A covered flume. A path can be built on top.", "Landscaping", 39)

    # Bridge span: the piece that crosses over a ground flume. Its leg takes only the cell's corners (the flume leaves them
    # free) and it carries no inert obstacle (that would cover the flume cell below a second time; full obstacles are not
    # reference counted). With the module off its neighbours are inert, so no water reaches it.
    # See docs/tech/models.md, "Requests from the water lane".
    bp = flume_piece("FlumeBridge", [(0, 0, 1)], [(0, 0, 1)], 2.0)
    bp["BlockObjectSpec"]["Blocks"][0]["Occupations"] = SPAN_LEG
    del bp["WaterObstacleSpec"], bp["FinishableWaterObstacleSpec"]
    name_building(bp, "FlumeBridgeSpan", "Flume Bridge (span over a flume)",
                  "A Flume Bridge piece that stands over another flume.", "Landscaping", 40)

    bp = flume_piece("FlumeBridge", [(0, 0, 1)], [(0, 0, 1)], 2.0)
    bp["BlockObjectSpec"]["Blocks"][0]["Occupations"] = BRIDGE_LEG
    name_building(bp, "FlumeBridge", "Flume Bridge", "A flume one block up on a trestle. Water and walkers pass under it.",
                  "Landscaping", 40)

    bp = flume_piece("FlumeDrop", [(0, 0, 1), (0, 1, 0)], [(0, 0, 1), (0, 1, 0)], 2.0, [(0, 0, 0)])
    name_building(bp, "FlumeDrop", "Flume Drop", "Drops a flume one level.", "Landscaping", 41)

    bp = flume_piece("FlumeGate", [(0, 0, 0)], [(0, 0, 0), (0, 0, 1)], 1.0, [(0, 0, 1)])
    bp["PandabornFlumeGateSpec"] = {"DefaultFlow": 0.3, "MaxFlow": 1.0, "FlowStep": 0.05, "ContaminationShutoff": 0.05}
    bp["PandabornEntityStateSpec"] = {"Features": ["Water"]}
    name_building(bp, "FlumeGate", "Flume Gate", "The start of a flume. Sets how much water goes in, and closes against badwater.",
                  "Landscaping", 42)

    # corner: one open water cell, posts on its two inner faces and the far corner; no flow cells, no inert obstacle
    bp = load("Buildings/Landscaping/ThrottlingValve/ThrottlingValve.Folktails.blueprint.json")
    del bp["ThrottlingValveSpec"]
    kit(bp, "FlumeCorner")
    bp["WaterObstacleSpec"] = {"Coordinates": [v2(1, 0), v2(0, 1), v2(1, 1)]}
    bp["FinishableWaterObstacleSpec"] = {"Height": 2.0}
    bp["FinishableHorizontalWaterObstacleSpec"]["Obstacles"] = [v3(0, 0, 0), v3(0, 0, 1)]
    bp["PandabornSolidCellsSpec"] = {"Cells": [v3(0, 0, 1)]}
    bp["PlaceableBlockObjectSpec"]["CustomPivot"] = {"HasCustomPivot": False, "Coordinates": {"X": 0.0, "Y": 0.0, "Z": 0.0}}
    name_building(bp, "FlumeCorner", "Flume Corner", "Turns a flume. Flumes enter and leave through its two open sides.",
                  "Landscaping", 43)


def spout():
    bp = load("Buildings/Landscaping/FillValve/FillValve.Folktails.blueprint.json")
    kit(bp, "PaddySpout")
    bp["FillValveSpec"]["DefaultTargetHeightOffset"] = 0.3
    bp["FillValveSpec"]["DefaultTargetHeightEnabled"] = True
    bp["PandabornPaddySpoutSpec"] = {}
    bp["PandabornSolidCellsSpec"] = {"Cells": [v3(0, 0, 1)]}
    name_building(bp, "PaddySpout", "Paddy Spout", "Holds the field in front at a set shallow depth.", "Landscaping", 36)


def scoop_wheel():
    bp = load("Buildings/Power/WaterWheel/WaterWheel.Folktails.blueprint.json")
    for k in ("FloodableBuildingSpec", "BlockableFloodableObjectSpec", "WaterObjectSpec", "WaterWheelSpec",
              "PowerGeneratorSoundsSpec", "MechanicalNodeDescriptionSpec"):
        bp.pop(k, None)
    bp["Children"]["#Unfinished"]["Children"].pop("ConstructionBase3x2WaterWheel#nested", None)
    kit(bp, "ScoopWheel")
    # one node, generator 100 x current, consumer 30: full speed from a current of 0.3
    bp["MechanicalNodeSpec"] = {"PowerOutput": 100, "PowerInput": 30, "IsShaft": False}
    bp["WaterPoweredGeneratorSpec"] = {"Blocks": [v2(0, 0)], "ExpectedWaterDirection": {"X": 1.0, "Y": 0.0},
                                       "MinRequiredOutflow": 0.15}
    bp["MechanicalBuildingSpec"] = {}
    bp["TransputProviderSpec"] = {"Transputs": [], "IgnoreRotation": False}
    bp["WaterMoverSpec"] = {"WaterPerSecond": 0.1}
    bp["WaterInputSpec"] = {"WaterInputCoordinates": v3(0, 0, 0)}
    bp["WaterInputFixedSpec"] = {}
    # the outlet cell hangs one block above the basin floor (vanilla pumps do the same; TimberCommons-safe)
    bp["WaterOutputSpec"] = {"WaterCoordinates": v3(0, 2, 2), "DistanceToGroundOffset": 0.0, "OverflowAllowed": False}
    bp["PandabornCurrentDrivenSpec"] = {}
    name_building(bp, "ScoopWheel", "Scoop Wheel", "Stands in a current and lifts water two levels onto the bank behind it.",
                  "Water", 60, [{"Id": "Log", "Amount": 10}])


def treadwheel():
    bp = load("Buildings/Power/PowerWheel/PowerWheel.Folktails.blueprint.json")
    bp["MechanicalNodeSpec"] = {"PowerOutput": 100, "PowerInput": 100, "IsShaft": False}
    bp["MechanicalBuildingSpec"] = {}
    bp["TransputProviderSpec"] = {"Transputs": [], "IgnoreRotation": False}
    bp["WaterMoverSpec"] = {"WaterPerSecond": 0.1}
    bp["WaterInputSpec"] = {"WaterInputCoordinates": v3(0, 1, -1)}
    bp["WaterInputFixedSpec"] = {}
    bp["WaterOutputSpec"] = {"WaterCoordinates": v3(2, 2, 1), "DistanceToGroundOffset": 0.0, "OverflowAllowed": False}
    bp["PandabornTreadwheelSpec"] = {}
    name_building(bp, "Treadwheel", "Treadwheel Lift", "A worker walks the wheel and lifts water from the pit behind it to a ledge.",
                  "Water", 61, [{"Id": "Log", "Amount": 10}])


def trip_hammer():
    bp = load("Buildings/Power/WaterWheel/WaterWheel.Folktails.blueprint.json")
    for k in ("FloodableBuildingSpec", "BlockableFloodableObjectSpec", "WaterObjectSpec", "WaterWheelSpec",
              "PowerGeneratorSoundsSpec", "MechanicalNodeDescriptionSpec"):
        bp.pop(k, None)
    cells = {(0, 0, z): block("Any" if z else "GroundOrStackable", "Corners, Middle") for z in range(2)}
    bp["BlockObjectSpec"] = blocks_spec((1, 1, 2), cells)
    bp["MechanicalNodeSpec"] = {"PowerOutput": 100, "PowerInput": 30, "IsShaft": False}
    bp["WaterPoweredGeneratorSpec"] = {"Blocks": [v2(0, 0)], "ExpectedWaterDirection": {"X": 1.0, "Y": 0.0},
                                       "MinRequiredOutflow": 0.15}
    bp["MechanicalBuildingSpec"] = {}
    bp["TransputProviderSpec"] = {"Transputs": [], "IgnoreRotation": False}
    bp["ManufactorySpec"] = {"ProductionRecipeIds": ["PandabornTripHammerTest"]}
    bp["ProductionIncreaserSpec"] = {}
    bp["PandabornCurrentDrivenSpec"] = {}
    bp["Children"]["#Unfinished"]["Children"].pop("ConstructionBase3x2WaterWheel#nested", None)
    name_building(bp, "TripHammer", "Water Trip-Hammer", "A mill driven by the current it stands in, with no shafts.", "Water", 65)
    write("Recipes/Pandaborn/Recipe.PandabornTripHammerTest.blueprint.json", {"RecipeSpec": {
        "Id": "PandabornTripHammerTest", "BackwardCompatibleIds": [], "DisplayLocKey": "Good.Plank.PluralDisplayName",
        "CycleDurationInHours": 2.0, "Ingredients": [], "Products": [{"Id": "Plank", "Amount": 1}],
        "ProducedSciencePoints": 0, "Fuel": "", "CyclesFuelLasts": 0, "FuelCapacity": 0, "CyclesCapacity": 30,
        "Icon": "Sprites/Goods/PlankIcon"}})


def cistern_tap():
    bp = load("Buildings/Water/Discharge/Discharge.Folktails.blueprint.json")
    for k in ("ManufactoryWaterContaminationProducerSpec", "ManufactoryTogglableRecipesSpec"):
        bp.pop(k, None)
    bp["ManufactorySpec"] = {"ProductionRecipeIds": ["FlowingWater"]}
    bp["PandabornCisternTapSpec"] = {}
    # vanilla WaterOutputManufactoryLimiter needs the Workshop component: keep the worker
    name_building(bp, "CisternTap", "Cistern Tap", "A worker pours stored Water into the water in front.", "Water", 63)


def dew_collector():
    bp = load("Buildings/Water/WaterPump/WaterPump.Folktails.blueprint.json")
    for k in ("WorkplaceSpec", "WorkshopSpec", "EnterableSpec", "WorkplaceSlotManagerSpec", "TransformSlotInitializerSpec",
              "WorkshopAnimationControllerSpec", "WorkplaceIlluminatorSpec", "WorkshopWorkerHiderSpec",
              "ManufactoryWaterConsumerSpec", "WaterInputSpec", "WaterInputPipeSpec"):
        bp.pop(k, None)
    bp["BuildingSpec"]["LoopingSoundName"] = ""
    ground = block("GroundOrStackable", "Bottom, Top, Corners, Path, Middle")
    cells = {(x, y, 0): ground for x in range(2) for y in range(3)}
    cells.update({(x, y, 1): block("Any", "Bottom, Top, Corners, Path, Middle") for x in range(2) for y in range(3)})
    bp["BlockObjectSpec"] = blocks_spec((2, 3, 2), cells, {"HasEntrance": True, "Coordinates": v3(1, -1, 0)})
    bp["BuildingAccessibleSpec"]["LocalAccess"] = {"X": 1.1, "Y": 0.0, "Z": -0.01}
    bp["ManufactorySpec"] = {"ProductionRecipeIds": ["PandabornDewWater"]}
    bp["ProductionIncreaserSpec"] = {}
    bp["PandabornDewLimiterSpec"] = {"DroughtEfficiency": 0.35, "TemperateEfficiency": 1.0}
    name_building(bp, "DewCollector", "Dew Collector", "Collects a trickle of Water from the air, with no workers.", "Water", 62)
    write("Recipes/Pandaborn/Recipe.PandabornDewWater.blueprint.json", {"RecipeSpec": {
        "Id": "PandabornDewWater", "BackwardCompatibleIds": [], "DisplayLocKey": "Good.Water.PluralDisplayName",
        "CycleDurationInHours": 4.0, "Ingredients": [], "Products": [{"Id": "Water", "Amount": 1}],
        "ProducedSciencePoints": 0, "Fuel": "", "CyclesFuelLasts": 0, "FuelCapacity": 0, "CyclesCapacity": 30,
        "Icon": "Sprites/Goods/WaterIcon"}})


# ------------------------------------------------------------------ test plants (vanilla Folktails models, Inkpaws goods)
def plant(src, short, display, edit):
    bp = load(src)
    template = "Pandaborn" + short + SUFFIX
    bp["TemplateSpec"] = {"TemplateName": template, "BackwardCompatibleTemplateNames": [],
                          "RequiredFeatureToggle": "", "DisablingFeatureToggle": ""}
    key = "NaturalResource.PandabornProto" + short
    bp["LabeledEntitySpec"]["DisplayNameLocKey"] = key + ".DisplayName"
    bp["LabeledEntitySpec"]["FlavorDescriptionLocKey"] = ""
    loc.append((key + ".DisplayName", "[Proto] " + display))
    edit(bp)
    rel = f"{PLANT_DIR}/{short}/Pandaborn{short}{SUFFIX}.blueprint.json"
    write(rel, bp)
    plants.append(rel[: -len(".json")])


def dry(bp):
    # tea/pepper stand-in: dry ground only; wet roots for 3 days (growth paused) before it dies; resets when dry again
    bp.pop("WateredNaturalResourceSpec", None)
    bp["AridNaturalResourceSpec"] = {"DaysToDieWet": 3.0}
    bp["FloodableNaturalResourceSpec"] = {"MinWaterHeight": 0, "MaxWaterHeight": 0, "DaysToDie": 3.0}
    bp["GrowableSpec"]["GrowthTimeInDays"] = 3.0
    bp["CuttableSpec"]["Yielder"]["Yield"] = {"Id": "PandabornTeaLeaves", "Amount": 1}


def main():
    if not os.path.isdir(BP):
        sys.exit("vanilla blueprint dump not found: " + BP)
    for sub in ("Buildings", "NaturalResources", "Recipes", "TemplateCollections", "Localizations"):
        p = os.path.join(MOD, sub)
        if os.path.isdir(p):
            for root, _, files in os.walk(p):
                for f in files:
                    if f.endswith(".blueprint.json") or f.endswith(".csv"):
                        os.remove(os.path.join(root, f))
    flumes()
    spout()
    scoop_wheel()
    treadwheel()
    trip_hammer()
    cistern_tap()
    dew_collector()
    plant("NaturalResources/Crops/Sunflower/Sunflower.blueprint.json", "DryCrop", "Dry-ground crop (3-day wet roots)", dry)
    write("TemplateCollections/Pandaborn/TemplateCollection.Buildings.ProtoWater.blueprint.json",
          {"TemplateCollectionSpec": {"CollectionId": "Buildings.Inkpaws", "Blueprints": buildings}})
    write("TemplateCollections/Pandaborn/TemplateCollection.NaturalResources.ProtoWater.blueprint.json",
          {"TemplateCollectionSpec": {"CollectionId": "NaturalResources.Inkpaws", "Blueprints": plants}})
    path = os.path.join(MOD, "Localizations", "enUS_PandabornProtoWater.csv")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("ID,Text,Comment\n")
        for k, t in loc:
            f.write(f'{k},"{t}",\n')
    with open(os.path.join(HERE, "kit_models.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(sorted(set(kit_models))) + "\n")
    print(f"{len(buildings)} buildings, {len(plants)} plants, {len(loc)} loc keys, kit models {sorted(set(kit_models))} -> {MOD}")


if __name__ == "__main__":
    main()
