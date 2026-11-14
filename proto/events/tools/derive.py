"""Writes the "in flower" twins of the two bamboos into the events dev mod's build folder.

Dev only. Each twin is a copy of the installed faction mod's plant blueprint (so model paths match what is installed)
whose harvest is bamboo seed, with no planting tool, no spreading and no mushrooms, marked PandabornInFlowerSpec. The
catalogue lane makes the real ones (docs/tech/events.md, "Requests to the catalogue lane"); these are build artefacts
and never enter git.

    python -I proto/events/tools/derive.py <installed faction mod folder> <events build folder>
"""
import copy
import json
import pathlib
import sys

SEED = "PandabornBambooSeed"
TWINS = [
    # (source blueprint, twin id, species, loc stem, seed per plant)
    ("NaturalResources/Pandaborn/Crops/PandabornShootBamboo/PandabornShootBamboo.Inkpaws.blueprint.json",
     "PandabornShootBambooInFlower", "PandabornShootBamboo.Inkpaws", "ShootBambooInFlower", 3),
    ("NaturalResources/Pandaborn/Trees/PandabornTimberBamboo/PandabornTimberBamboo.Inkpaws.blueprint.json",
     "PandabornTimberBambooInFlower", "PandabornTimberBamboo.Inkpaws", "TimberBambooInFlower", 3),
]
DROP = ["PlantableSpec", "PlantablePreviewModelSpec", "ReproducibleSpec", "GatherableSpec", "PandabornFloweringPlantSpec"]


SQUARE_BASIS = pathlib.Path("E:/PandabornDev/reference/Blueprints/Buildings/Wellbeing/DanceHall/DanceHall.Folktails.blueprint.json")
SQUARE = "Buildings/Pandaborn/Wellbeing/PandabornFestivalSquare/PandabornFestivalSquare.Inkpaws.blueprint.json"


def square(out: pathlib.Path) -> None:
    """The Festival Square as requested of the catalogue (docs/tech/events.md 8.1): the vanilla Dance Hall meeting the
    Campfire need, with PandabornFestivalSquareSpec. The catalogue hides its own square while the Festival module is off,
    so the dev mod carries a whole one. Cheap and science-free so a test can place it finished."""
    data = json.loads(SQUARE_BASIS.read_text(encoding="utf-8"))
    data["TemplateSpec"]["TemplateName"] = "PandabornFestivalSquare.Inkpaws"
    data["TemplateSpec"]["BackwardCompatibleTemplateNames"] = []
    data["BuildingSpec"]["BuildingCost"] = [{"Id": "Log", "Amount": 30}, {"Id": "Plank", "Amount": 30}, {"Id": "Paper", "Amount": 10}]
    data["BuildingSpec"]["ScienceCost"] = 0
    for effect in data["AttractionSpec"]["Effects"]:
        if effect["NeedId"] == "DanceHall":
            effect["NeedId"] = "Campfire"
    label = data["LabeledEntitySpec"]
    label["DisplayNameLocKey"] = "Pandaborn.ProtoEvents.FestivalSquare.DisplayName"
    label["DescriptionLocKey"] = "Pandaborn.ProtoEvents.FestivalSquare.Description"
    label["FlavorDescriptionLocKey"] = ""
    data["PandabornFestivalSquareSpec"] = {}
    dest = out / SQUARE
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("square PandabornFestivalSquare.Inkpaws <- DanceHall.Folktails")


SEED_BASIS = pathlib.Path("E:/PandabornDev/reference/Blueprints/Goods/Good.SunflowerSeeds.blueprint.json")


def seed_good(installed: pathlib.Path, out: pathlib.Path) -> None:
    """PandabornBambooSeed is gated with the Flowering in the catalogue (hidden while the module is off): when the
    installed faction lacks it, the dev mod carries a plain copy (vanilla GoodSpec only) and adds it to Goods.Inkpaws."""
    if (installed / "Goods" / "Pandaborn" / "Good.PandabornBambooSeed.blueprint.json").exists():
        return
    data = json.loads(SEED_BASIS.read_text(encoding="utf-8"))
    good = data["GoodSpec"]
    good["Id"] = SEED
    good["BackwardCompatibleIds"] = []
    good["ConsumptionEffects"] = []
    good["DisplayNameLocKey"] = "Pandaborn.ProtoEvents.BambooSeed.DisplayName"
    good["PluralDisplayNameLocKey"] = "Pandaborn.ProtoEvents.BambooSeed.PluralDisplayName"
    dest = out / "Goods" / "Pandaborn" / "Good.PandabornBambooSeed.blueprint.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    coll = {"GoodCollectionSpec": {"CollectionId": "Goods.Inkpaws", "Goods": [SEED]}}
    dest = out / "GoodCollections" / "Pandaborn" / "GoodCollection.PandabornProtoEvents.blueprint.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(coll, indent=2) + "\n", encoding="utf-8")
    print("good PandabornBambooSeed <- SunflowerSeeds (the installed faction gates it)")


def main(installed: pathlib.Path, out: pathlib.Path) -> None:
    square(out)
    seed_good(installed, out)
    for source, twin_id, species, stem, seed in TWINS:
        src = installed / source
        data = json.loads(src.read_text(encoding="utf-8"))
        twin = copy.deepcopy(data)
        for key in DROP:
            twin.pop(key, None)
        twin["TemplateSpec"]["TemplateName"] = twin_id + ".Inkpaws"
        twin["TemplateSpec"]["BackwardCompatibleTemplateNames"] = []
        twin["CuttableSpec"]["Yielder"]["Yield"] = {"Id": SEED, "Amount": seed}
        label = twin["LabeledEntitySpec"]
        label["DisplayNameLocKey"] = f"Pandaborn.NaturalResource.{stem}.DisplayName"
        label["DescriptionLocKey"] = f"Pandaborn.NaturalResource.{stem}.Description"
        label["FlavorDescriptionLocKey"] = f"Pandaborn.NaturalResource.{stem}.FlavorDescription"
        twin["PandabornInFlowerSpec"] = {"Species": species}
        kind = pathlib.PurePosixPath(source).parts[2]
        dest = out / "NaturalResources" / "Pandaborn" / kind / twin_id / f"{twin_id}.Inkpaws.blueprint.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(twin, indent=2) + "\n", encoding="utf-8")
        print(f"twin {twin_id}.Inkpaws <- {source} (seed {seed})")


if __name__ == "__main__":
    main(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]))
