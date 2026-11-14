"""Stage-0 prototype: derive the two test templates from the vanilla blueprint dump into the build folder.

    python -I proto/stage0/tools/derive.py <vanilla Blueprints dir> <build dir>

* NaturalResources/Pandaborn/Stage0/PandabornStage0Bamboo.Inkpaws  <- Birch: a fast tree whose cut yield is the vanilla
  Plank good (shown as "Poles" to Inkpaws by the faction modifier), so no mill is needed.
* Buildings/Pandaborn/Stage0/PandabornStage0Teahouse.Inkpaws       <- Campfire.Folktails plus PandabornBellSettledMarkerSpec:
  the bell's "village is settled" trigger. With the Bell module off it is a plain campfire.
Vanilla files are read from E: and the copies are written to the build folder only (no game files in git).
"""
import json
import sys
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, data: dict, source: str) -> None:
    # No provenance key inside the blueprint: every top-level key is read as a spec name, and an unknown one throws.
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    vanilla, build = Path(sys.argv[1]), Path(sys.argv[2])

    tree = load(vanilla / "NaturalResources/Trees/Birch/Birch.blueprint.json")
    tree["TemplateSpec"]["TemplateName"] = "PandabornStage0Bamboo.Inkpaws"
    tree["TemplateSpec"]["BackwardCompatibleTemplateNames"] = []
    tree["GrowableSpec"]["GrowthTimeInDays"] = 3.0
    tree["CuttableSpec"]["Yielder"]["Yield"] = {"Id": "Plank", "Amount": 2}
    tree["LabeledEntitySpec"]["DisplayNameLocKey"] = "Pandaborn.Stage0.TimberBamboo.DisplayName"
    tree["LabeledEntitySpec"]["FlavorDescriptionLocKey"] = "Pandaborn.Stage0.TimberBamboo.FlavorDescription"
    tree.pop("ReproducibleSpec", None)
    save(build / "NaturalResources/Pandaborn/Stage0/PandabornStage0Bamboo.Inkpaws.blueprint.json", tree, "Birch")

    hut = load(vanilla / "Buildings/Wellbeing/Campfire/Campfire.Folktails.blueprint.json")
    hut["TemplateSpec"]["TemplateName"] = "PandabornStage0Teahouse.Inkpaws"
    hut["TemplateSpec"]["BackwardCompatibleTemplateNames"] = []
    hut["LabeledEntitySpec"]["DisplayNameLocKey"] = "Pandaborn.Stage0.Teahouse.DisplayName"
    hut["PandabornBellSettledMarkerSpec"] = {}
    save(build / "Buildings/Pandaborn/Stage0/PandabornStage0Teahouse.Inkpaws.blueprint.json", hut, "Campfire.Folktails")
    print("derived 2 templates into", build)
    return 0


if __name__ == "__main__":
    sys.exit(main())
