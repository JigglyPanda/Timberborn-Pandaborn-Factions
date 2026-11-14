"""Generates the water-toolkit prototype mod's blueprints from vanilla blueprints.

Dev prototype only (proto/water/mod, manifest Id JigglyPanda.PandabornProtoWater). Vanilla models and materials are
stand-ins: this is about mechanics, not art. Every template ends in .PandabornProto; every global id starts with
Pandaborn. Rerun after a game update:

    E:\\PandabornDev\\tools\\venv\\Scripts\\python.exe -I proto/water/tools/gen_blueprints.py
"""
import copy
import json
import os
import sys

BP = r"E:\PandabornDev\reference\Blueprints"
HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, "..", "mod"))
SUFFIX = ".PandabornProto"
BUILD_DIR = "Buildings/Pandaborn/ProtoWater"
PLANT_DIR = "NaturalResources/Pandaborn/ProtoWater"

loc = []          # (key, text)
buildings = []    # collection entries
plants = []


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
    key = "Building.Pandaborn" + short
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


def one_by_one(bp, matter="GroundOrStackable", occ="Bottom, Top, Corners, Path, Middle", stackable="BlockObject"):
    bp["BlockObjectSpec"] = blocks_spec((1, 1, 1), {(0, 0, 0): block(matter, occ, stackable)})


def finished_model(bp, model):
    bp["Children"]["#Finished"]["TimbermeshSpec"]["Model"] = model


# ------------------------------------------------------------------ 1. bamboo spout (data only)
def spout():
    bp = load("Buildings/Landscaping/FillValve/FillValve.Folktails.blueprint.json")
    bp["FillValveSpec"]["DefaultTargetHeightOffset"] = 0.3
    bp["FillValveSpec"]["DefaultTargetHeightEnabled"] = True
    bp["PandabornSolidCellsSpec"] = {"Cells": [v3(0, 0, 1)]}   # cap: backed-up water cannot run over the top
    name_building(bp, "PaddySpout", "Paddy Spout",
                  "Holds the pool in front of it at a set shallow depth (default 0.3). Water comes in from behind.",
                  "Landscaping", 36)


# ------------------------------------------------------------------ 2a. flume, zero-code route (restyled 1x1 throttling valves)
def flume_valves():
    base = load("Buildings/Landscaping/ThrottlingValve/ThrottlingValve.Folktails.blueprint.json")
    for short, display, enabled, limit, lid in [
        ("FlumeValve", "Flume segment (valve route, lidded)", False, 1.0, True),
        ("FlumeValveOpen", "Flume segment (valve route, open top)", False, 1.0, False),
        ("FlumeValveGate", "Flume gate (valve route)", True, 0.3, True),
    ]:
        bp = copy.deepcopy(base)
        one_by_one(bp)
        bp["ThrottlingValveSpec"]["DefaultOutflowLimitEnabled"] = enabled
        bp["ThrottlingValveSpec"]["DefaultOutflowLimit"] = limit
        bp["FinishableHorizontalWaterObstacleSpec"]["Obstacles"] = [v3(0, 0, 0)] + ([v3(0, 0, 1)] if lid else [])
        name_building(bp, short, display,
                      "Zero-code flume prototype: a 1x1 throttling valve. Water runs one way along the arrow and never "
                      "leaks out of the sides.", "Landscaping", 37)


# ------------------------------------------------------------------ 2b. flume, small-component route
FLOOR_MODEL = "Buildings/Landscaping/ImpermeableFloor/ImpermeableFloor.Folktails.Model"


def flume_base():
    bp = load("Buildings/Landscaping/ThrottlingValve/ThrottlingValve.Folktails.blueprint.json")
    del bp["ThrottlingValveSpec"]
    finished_model(bp, FLOOR_MODEL)
    return bp


def flumes():
    # straight segment on the ground, open top
    bp = flume_base()
    one_by_one(bp)
    bp["PandabornFlumeSegmentSpec"] = {"FlowCells": [v3(0, 0, 0)], "InflowLimit": -1.0, "ContaminationShutoff": 0.0}
    bp["FinishableHorizontalWaterObstacleSpec"]["Obstacles"] = [v3(0, 0, 0)]
    name_building(bp, "Flume", "Flume",
                  "Carries water one way along the arrow, level or downhill. Water never leaks out of the sides.",
                  "Landscaping", 38)

    # lidded: depth capped at one block, a path or platform can sit on top
    bp = flume_base()
    one_by_one(bp)
    bp["PandabornFlumeSegmentSpec"] = {"FlowCells": [v3(0, 0, 0)], "InflowLimit": -1.0, "ContaminationShutoff": 0.0}
    bp["FinishableHorizontalWaterObstacleSpec"]["Obstacles"] = [v3(0, 0, 0), v3(0, 0, 1)]
    bp["PandabornSolidCellsSpec"] = {"Cells": [v3(0, 0, 1)]}   # cap: backed-up water cannot run over the top
    name_building(bp, "FlumeLidded", "Flume (covered)",
                  "A covered flume segment. Holds at most one block of water; a path can be built on top.",
                  "Landscaping", 39)

    # raised on a one-block trestle; water under the trestle flows freely
    bp = flume_base()
    bp["BlockObjectSpec"] = blocks_spec((1, 1, 2), {
        (0, 0, 0): block("GroundOrStackable", "Corners"),
        (0, 0, 1): block("Any", "Bottom, Top, Corners, Path, Middle", "BlockObject"),
    })
    bp["PandabornFlumeSegmentSpec"] = {"FlowCells": [v3(0, 0, 1)], "InflowLimit": -1.0, "ContaminationShutoff": 0.0}
    bp["FinishableHorizontalWaterObstacleSpec"]["Obstacles"] = [v3(0, 0, 1)]
    name_building(bp, "FlumeBridge", "Flume Bridge",
                  "A flume segment one block above the ground on a trestle.", "Landscaping", 40)

    # step-down: upper cell at z+1, lower cell at z, one tile further along the flow
    bp = flume_base()
    bp["BlockObjectSpec"] = blocks_spec((1, 2, 2), {
        (0, 0, 0): block("GroundOrStackable", "Corners"),
        (0, 0, 1): block("Any", "Bottom, Top, Corners, Path, Middle", "BlockObject"),
        (0, 1, 0): block("GroundOrStackable", "Bottom, Top, Corners, Path, Middle", "BlockObject"),
    })
    bp["PandabornFlumeSegmentSpec"] = {"FlowCells": [v3(0, 0, 1), v3(0, 1, 0)], "InflowLimit": -1.0, "ContaminationShutoff": 0.0}
    bp["FinishableHorizontalWaterObstacleSpec"]["Obstacles"] = [v3(0, 0, 1), v3(0, 1, 0)]
    open_step = copy.deepcopy(bp)
    # sealed: the cell under the upper half is solid, so floodwater under it cannot enter the lower flume from behind
    bp["WaterObstacleSpec"] = {"Coordinates": [{"X": 0, "Y": 0}]}
    bp["FinishableWaterObstacleSpec"] = {"Height": 1.0}
    name_building(bp, "FlumeDrop", "Flume Drop",
                  "Drops a flume one level: water enters at the top and leaves one block lower.", "Landscaping", 41)
    name_building(open_step, "FlumeDropOpen", "Flume Drop (open leg, test)",
                  "Test variant whose leg cell is open to water.", "Landscaping", 41)

    # gate: our segment plus a fixed inflow limit (code route); adjustable gate is the valve route above
    bp = flume_base()
    one_by_one(bp)
    bp["PandabornFlumeSegmentSpec"] = {"FlowCells": [v3(0, 0, 0)], "InflowLimit": 0.3, "ContaminationShutoff": 0.05}
    bp["FinishableHorizontalWaterObstacleSpec"]["Obstacles"] = [v3(0, 0, 0), v3(0, 0, 1)]
    bp["PandabornSolidCellsSpec"] = {"Cells": [v3(0, 0, 1)]}   # cap: backed-up water cannot run over the top
    name_building(bp, "FlumeGate", "Flume Gate",
                  "The intake of a flume. Lets at most 0.3 cubic metres per second through, and shuts by itself while "
                  "the water at the intake is contaminated.", "Landscaping", 42)


# ------------------------------------------------------------------ 2c. turning box (pure data, both routes)
def turning_box():
    bp = load("Buildings/Landscaping/ThrottlingValve/ThrottlingValve.Folktails.blueprint.json")
    del bp["ThrottlingValveSpec"]
    finished_model(bp, "Buildings/Landscaping/Levee/Levee.Folktails.Model")
    full = block("GroundOrStackable", "Bottom, Top, Corners, Path, Middle", "BlockObject")
    bp["BlockObjectSpec"] = blocks_spec((2, 2, 1), {(0, 0, 0): full, (1, 0, 0): full, (0, 1, 0): full, (1, 1, 0): full})
    # water cell (0,0); solid posts on its two inner faces plus the far corner
    bp["WaterObstacleSpec"] = {"Coordinates": [{"X": 1, "Y": 0}, {"X": 0, "Y": 1}, {"X": 1, "Y": 1}]}
    bp["FinishableWaterObstacleSpec"] = {"Height": 2.0}
    bp["FinishableHorizontalWaterObstacleSpec"]["Obstacles"] = [v3(0, 0, 0), v3(0, 0, 1)]
    bp["PandabornSolidCellsSpec"] = {"Cells": [v3(0, 0, 1)]}   # cap: backed-up water cannot run over the top
    bp["PlaceableBlockObjectSpec"]["CustomPivot"] = {"HasCustomPivot": False, "Coordinates": {"X": 0.0, "Y": 0.0, "Z": 0.0}}
    name_building(bp, "FlumeCorner", "Flume Corner",
                  "A corner for flumes: one open water cell with posts on two sides. Flumes enter and leave through "
                  "the two open faces.", "Landscaping", 43)


# ------------------------------------------------------------------ 3. noria and treadwheel lift
LIFT = 2   # levels lifted


def lift_common(bp, rate):
    bp["MechanicalBuildingSpec"] = {}
    bp["TransputProviderSpec"] = {"Transputs": [], "IgnoreRotation": False}
    bp["WaterMoverSpec"] = {"WaterPerSecond": rate}
    bp["WaterInputFixedSpec"] = {}


def noria():
    bp = load("Buildings/Power/WaterWheel/WaterWheel.Folktails.blueprint.json")
    for k in ("FloodableBuildingSpec", "BlockableFloodableObjectSpec", "WaterObjectSpec", "WaterWheelSpec",
              "PowerGeneratorSoundsSpec", "MechanicalNodeDescriptionSpec"):
        bp.pop(k, None)
    # y=0: the wheel column standing in the river (z0..LIFT); y=1: a lip of bank one block higher than the outlet
    # (unoccupied, so terrain may fill it) that keeps the lifted water from running straight back into the river;
    # y=2: the outlet cell at z=LIFT, over the basin floor
    cells = {}
    for z in range(LIFT + 1):
        cells[(0, 0, z)] = block("Any" if z else "GroundOrStackable", "Corners, Middle")
    cells[(0, 2, LIFT)] = block("Any", "Corners, Middle")
    bp["BlockObjectSpec"] = blocks_spec((1, 3, LIFT + 1), cells)
    bp["MechanicalNodeSpec"] = {"PowerOutput": 100, "PowerInput": 100, "IsShaft": False}
    bp["WaterPoweredGeneratorSpec"] = {"Blocks": [{"X": 0, "Y": 0}], "ExpectedWaterDirection": {"X": 1.0, "Y": 0.0},
                                       "MinRequiredOutflow": 0.15}
    lift_common(bp, 0.1)
    bp["WaterInputSpec"] = {"WaterInputCoordinates": v3(0, 0, 0)}
    # like vanilla pumps, the outlet cell hangs one block above the basin floor (offset 0: the basin fills to 0.9;
    # an outlet cell *on* the floor has no space, and TimberCommons' output patch ignores DistanceToGroundOffset)
    bp["WaterOutputSpec"] = {"WaterCoordinates": v3(0, 2, LIFT), "DistanceToGroundOffset": 0.0, "OverflowAllowed": False}
    bp["Children"]["#Unfinished"]["Children"].pop("ConstructionBase3x2WaterWheel#nested", None)
    name_building(bp, "ScoopWheel", "Scoop Wheel",
                  f"Stands in a current and lifts water {LIFT} levels onto the bank behind it, with no workers. "
                  "Lifts more in faster water (needs at least 0.15).", "Water", 60,
                  [{"Id": "Log", "Amount": 10}])


def treadwheel():
    bp = load("Buildings/Power/PowerWheel/PowerWheel.Folktails.blueprint.json")
    # PowerWheel footprint 3x1x2, entrance at (1,-1,0). Intake in a pit right behind the left end (cell z-1),
    # outlet one row further back over a ledge whose floor is z+1 (walled off from the wheel row).
    bp["MechanicalNodeSpec"] = {"PowerOutput": 100, "PowerInput": 100, "IsShaft": False}
    lift_common(bp, 0.1)
    bp["WaterInputSpec"] = {"WaterInputCoordinates": v3(0, 1, -1)}
    bp["WaterOutputSpec"] = {"WaterCoordinates": v3(2, 2, 1), "DistanceToGroundOffset": 0.0, "OverflowAllowed": False}
    name_building(bp, "Treadwheel", "Treadwheel lift",
                  "A worker walks the wheel and lifts water from the pit behind its left end to a ledge two rows "
                  "behind its right end, about two levels up.", "Water", 61, [{"Id": "Log", "Amount": 10}])


# ------------------------------------------------------------------ 4. dew collector
def dew_collector():
    bp = load("Buildings/Water/WaterPump/WaterPump.Folktails.blueprint.json")
    for k in ("WorkplaceSpec", "WorkshopSpec", "EnterableSpec", "WorkplaceSlotManagerSpec", "TransformSlotInitializerSpec",
              "WorkshopAnimationControllerSpec", "WorkplaceIlluminatorSpec", "WorkshopWorkerHiderSpec",
              "ManufactoryWaterConsumerSpec", "WaterInputSpec", "WaterInputPipeSpec"):
        bp.pop(k, None)
    bp["BuildingSpec"]["LoopingSoundName"] = ""
    # the pump's own footprint hangs a level below the ground (BaseZ 1); a collector stands on flat ground
    ground = block("GroundOrStackable", "Bottom, Top, Corners, Path, Middle")
    cells = {(x, y, 0): ground for x in range(2) for y in range(3)}
    cells.update({(x, y, 1): block("Any", "Bottom, Top, Corners, Path, Middle") for x in range(2) for y in range(3)})
    bp["BlockObjectSpec"] = blocks_spec((2, 3, 2), cells, {"HasEntrance": True, "Coordinates": v3(1, -1, 0)})
    bp["BuildingAccessibleSpec"]["LocalAccess"] = {"X": 1.1, "Y": 0.0, "Z": -0.01}
    bp["ManufactorySpec"] = {"ProductionRecipeIds": ["PandabornDewWater"]}
    bp["ProductionIncreaserSpec"] = {}
    bp["PandabornDewLimiterSpec"] = {"DroughtEfficiency": 0.35, "TemperateEfficiency": 1.0}
    name_building(bp, "DewCollector", "Dew collector",
                  "Collects a trickle of Water from the air with no workers: 1 every 4 hours in good weather, about a "
                  "third of that in drought.", "Water", 62)
    write("Recipes/Pandaborn/Recipe.PandabornDewWater.blueprint.json", {"RecipeSpec": {
        "Id": "PandabornDewWater", "BackwardCompatibleIds": [], "DisplayLocKey": "Good.Water.PluralDisplayName",
        "CycleDurationInHours": 4.0, "Ingredients": [], "Products": [{"Id": "Water", "Amount": 1}],
        "ProducedSciencePoints": 0, "Fuel": "", "CyclesFuelLasts": 0, "FuelCapacity": 0, "CyclesCapacity": 30,
        "Icon": "Sprites/Goods/WaterIcon"}})


# ------------------------------------------------------------------ 4b. cistern tap and trip-hammer
def cistern_tap():
    base = load("Buildings/Water/Discharge/Discharge.Folktails.blueprint.json")
    for k in ("ManufactoryWaterContaminationProducerSpec", "ManufactoryTogglableRecipesSpec"):
        base.pop(k, None)
    base["ManufactorySpec"] = {"ProductionRecipeIds": ["FlowingWater"]}
    bp = copy.deepcopy(base)
    name_building(bp, "CisternTap", "Cistern Tap",
                  "A worker pours stored Water into the basin or flume in front: 3 Water per hour becomes 0.6 cubic "
                  "metres of clean water.", "Water", 63)
    # test variant without a worker (the harness puts Water goods into it)
    for k in ("WorkplaceSpec", "EnterableSpec", "TransformSlotInitializerSpec", "WorkplaceSlotManagerSpec",
              "WorkshopSpec", "WorkplaceIlluminatorSpec", "WorkshopWorkerHiderSpec", "WorkshopParticleControllerSpec"):
        base.pop(k, None)
    base["ProductionIncreaserSpec"] = {}
    name_building(base, "CisternTapAuto", "Cistern Tap (no worker, test)", "Test variant of the Cistern Tap.", "Water", 64)


def trip_hammer():
    """A workshop driven straight by the current under it: one mechanical node that is both the water-wheel generator
    and the consumer, no shafts. Test recipe without ingredients so production speed can be read on its own."""
    bp = load("Buildings/Power/WaterWheel/WaterWheel.Folktails.blueprint.json")
    for k in ("FloodableBuildingSpec", "BlockableFloodableObjectSpec", "WaterObjectSpec", "WaterWheelSpec",
              "PowerGeneratorSoundsSpec", "MechanicalNodeDescriptionSpec"):
        bp.pop(k, None)
    cells = {(0, 0, z): block("Any" if z else "GroundOrStackable", "Corners, Middle") for z in range(2)}
    bp["BlockObjectSpec"] = blocks_spec((1, 1, 2), cells)
    bp["MechanicalNodeSpec"] = {"PowerOutput": 100, "PowerInput": 100, "IsShaft": False}
    bp["WaterPoweredGeneratorSpec"] = {"Blocks": [{"X": 0, "Y": 0}], "ExpectedWaterDirection": {"X": 1.0, "Y": 0.0},
                                       "MinRequiredOutflow": 0.15}
    bp["MechanicalBuildingSpec"] = {}
    bp["TransputProviderSpec"] = {"Transputs": [], "IgnoreRotation": False}
    bp["ManufactorySpec"] = {"ProductionRecipeIds": ["PandabornTripHammerTest"]}
    bp["ProductionIncreaserSpec"] = {}
    bp["Children"]["#Unfinished"]["Children"].pop("ConstructionBase3x2WaterWheel#nested", None)
    name_building(bp, "TripHammer", "Water Trip-Hammer",
                  "A mill driven by the current it stands in, with no shafts. Works faster in faster water.", "Water", 65)
    write("Recipes/Pandaborn/Recipe.PandabornTripHammerTest.blueprint.json", {"RecipeSpec": {
        "Id": "PandabornTripHammerTest", "BackwardCompatibleIds": [], "DisplayLocKey": "Good.Plank.PluralDisplayName",
        "CycleDurationInHours": 2.0, "Ingredients": [], "Products": [{"Id": "Plank", "Amount": 1}],
        "ProducedSciencePoints": 0, "Fuel": "", "CyclesFuelLasts": 0, "FuelCapacity": 0, "CyclesCapacity": 30,
        "Icon": "Sprites/Goods/PlankIcon"}})


# ------------------------------------------------------------------ 5. crop-zone test plants
def plant(src, short, display, edit):
    bp = load(src)
    template = "Pandaborn" + short + SUFFIX
    bp["TemplateSpec"] = {"TemplateName": template, "BackwardCompatibleTemplateNames": [],
                          "RequiredFeatureToggle": "", "DisablingFeatureToggle": ""}
    key = "NaturalResource.Pandaborn" + short
    bp["LabeledEntitySpec"]["DisplayNameLocKey"] = key + ".DisplayName"
    bp["LabeledEntitySpec"]["FlavorDescriptionLocKey"] = ""
    loc.append((key + ".DisplayName", "[Proto] " + display))
    edit(bp)
    rel = f"{PLANT_DIR}/{short}/Pandaborn{short}{SUFFIX}.blueprint.json"
    write(rel, bp)
    plants.append(rel[: -len(".json")])


def paddy(bp):
    # rice stand-in on the wheat model: lives only in standing water, 0 < depth <= 1 block
    bp["BlockObjectSpec"] = load("NaturalResources/Crops/Cattail/Cattail.blueprint.json")["BlockObjectSpec"]
    bp["FloodableNaturalResourceSpec"] = {"MinWaterHeight": 1, "MaxWaterHeight": 1, "DaysToDie": 2.0}
    bp["WateredNaturalResourceSpec"] = {"DaysToDieDry": 1.0}
    bp["PlantableSpec"]["ResourceGroup"] = "AquaticFarmhouse"
    bp["CuttableSpec"]["Yielder"]["ResourceGroup"] = "AquaticFarmhouse"
    bp["GrowableSpec"]["GrowthTimeInDays"] = 3.0


def moist(bp):
    # cabbage stand-in on the potato model (Kohlrabi is Iron Teeth: its materials are missing in a Folktails game): moist soil, survives a long time dry (paused, browned)
    bp["WateredNaturalResourceSpec"] = {"DaysToDieDry": 30.0}
    bp["FloodableNaturalResourceSpec"] = {"MinWaterHeight": 0, "MaxWaterHeight": 0, "DaysToDie": 1.0}
    bp["GrowableSpec"]["GrowthTimeInDays"] = 3.0


def dry(bp):
    # tea stand-in on the sunflower model: dry ground only, dies when irrigated
    bp.pop("WateredNaturalResourceSpec", None)
    bp["AridNaturalResourceSpec"] = {"DaysToDieWet": 1.0}
    bp["FloodableNaturalResourceSpec"] = {"MinWaterHeight": 0, "MaxWaterHeight": 0, "DaysToDie": 0.5}
    bp["GrowableSpec"]["GrowthTimeInDays"] = 3.0


def bamboo(bp):
    # fast, self-spreading tree: cut for logs, gathered for berries (stand-ins for poles and shoots)
    bp["GrowableSpec"]["GrowthTimeInDays"] = 2.0
    bp["ReproducibleSpec"] = {"ReproductionChance": 0.25}
    bp["WateredNaturalResourceSpec"] = {"DaysToDieDry": 6.0}
    bp["CuttableSpec"]["Yielder"]["Yield"] = {"Id": "Log", "Amount": 1}
    bp["GatherableSpec"] = {"YieldGrowthTimeInDays": 2.0, "Yielder": {
        "YielderComponentName": "Gatherable", "Yield": {"Id": "Berries", "Amount": 1},
        "RemovalTimeInHours": 0.5, "ResourceGroup": "Gatherable"}}


def shoot_bamboo(bp):
    # field crop planted and harvested by the farmhouse (carrot model stand-in); moist soil; fast
    bp["WateredNaturalResourceSpec"] = {"DaysToDieDry": 2.0}
    bp["FloodableNaturalResourceSpec"] = {"MinWaterHeight": 0, "MaxWaterHeight": 0, "DaysToDie": 1.0}
    bp["GrowableSpec"]["GrowthTimeInDays"] = 2.0


def timber_bamboo(bp):
    # plain fast tree planted by the forester, cut for logs (poles stand-in), spreads when unmarked
    bp["GrowableSpec"]["GrowthTimeInDays"] = 3.0
    bp["ReproducibleSpec"] = {"ReproductionChance": 0.1}
    bp["WateredNaturalResourceSpec"] = {"DaysToDieDry": 2.0}
    bp["CuttableSpec"]["Yielder"]["Yield"] = {"Id": "Log", "Amount": 1}


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
    spout()
    flume_valves()
    flumes()
    turning_box()
    noria()
    treadwheel()
    dew_collector()
    cistern_tap()
    trip_hammer()
    plant("NaturalResources/Crops/Wheat/Wheat.blueprint.json", "PaddyCrop", "Paddy crop", paddy)
    plant("NaturalResources/Crops/Potato/Potato.blueprint.json", "MoistCrop", "Moist crop", moist)
    plant("NaturalResources/Crops/Sunflower/Sunflower.blueprint.json", "DryCrop", "Dry-ground crop", dry)
    plant("NaturalResources/Trees/Birch/Birch.blueprint.json", "Bamboo", "Bamboo (tree stand-in)", bamboo)
    plant("NaturalResources/Crops/Carrot/Carrot.blueprint.json", "ShootBamboo", "Shoot Bamboo", shoot_bamboo)
    plant("NaturalResources/Trees/Birch/Birch.blueprint.json", "TimberBamboo", "Timber Bamboo", timber_bamboo)
    # appended by CollectionId: Folktails and (for now) Inkpaws both use these collections
    write("TemplateCollections/Pandaborn/TemplateCollection.Buildings.ProtoWater.blueprint.json",
          {"TemplateCollectionSpec": {"CollectionId": "Buildings.Folktails", "Blueprints": buildings}})
    write("TemplateCollections/Pandaborn/TemplateCollection.NaturalResources.ProtoWater.blueprint.json",
          {"TemplateCollectionSpec": {"CollectionId": "NaturalResources.Folktails", "Blueprints": plants}})
    loc.extend([
        ("Status.Pandaborn.Flume.Blocked", "Blocked: the tile ahead is solid. Water cannot leave this flume."),
        ("Status.Pandaborn.Flume.Misaligned", "Misaligned: the flume next to this one runs another way. A bend needs a Flume Corner."),
        ("Status.Pandaborn.Flume.IntakeDry", "No water can enter: the water behind the intake is below the flume bed."),
        ("Status.Pandaborn.Flume.EndDry", "No water is reaching the end of this flume."),
        ("Status.Pandaborn.Flume.BadwaterClosed", "Closed: the water at the intake is contaminated."),
    ])
    path = os.path.join(MOD, "Localizations", "enUS_PandabornProtoWater.csv")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("ID,Text,Comment\n")
        for k, t in loc:
            f.write(f'{k},"{t}",\n')
    print(f"{len(buildings)} buildings, {len(plants)} plants, {len(loc)} loc keys -> {MOD}")


if __name__ == "__main__":
    main()
