"""Derive the Ringtail prototype's blueprint copies from the vanilla blueprint dump.

Prototype only (proto/ringtails). Writes into proto/ringtails/mod:
  * Characters/Pandaborn/RingtailAdult|RingtailChild.Inkpaws  - hidden second colonist kind (in no template collection)
  * Buildings/Pandaborn/Ringtails/RingtailHaulingPost|RingtailGathererFlag.Inkpaws - Ringtail-only workplaces
  * Buildings/Pandaborn/Ringtails/RingtailLoft.Inkpaws        - a Lodge copy marked as a Ringtail home (no procreation)
  * WorkerOutfits/Pandaborn/WorkerOutfit.<Id>.PandabornRingtail.Inkpaws - outfits for the Ringtail worker type
Hand-written files (manifest, worker type, collections, faction merge, localization) are not touched.

Usage: python proto/ringtails/tools/derive.py [--blueprints E:\\PandabornDev\\reference\\Blueprints]
Standard library only. Rerun after a game update.
"""
import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(HERE, "..", "mod"))
WORKER_TYPE = "PandabornRingtail"

# Ringtail stats relative to the vanilla beaver (Inkpaws use the vanilla values today)
WALK_FACTOR = 1.3          # faster walkers
ANIMATION_FACTOR = 1.25    # keep the legs roughly in step with the faster walk on a smaller body
BODY_SCALE = 0.82
APPETITE_FACTOR = 0.75     # light eaters and drinkers: net Hunger/Thirst decay x0.75          # smaller body, applied to the Model_Preserved child (TransformSpec)

COATS_ADULT = ["Materials/Pandaborn/Ringtails/Adult/RingtailAdult%d" % i for i in range(1, 6)]
COATS_CHILD = ["Materials/Pandaborn/Ringtails/Child/RingtailChild%d" % i for i in range(1, 4)]


def load(path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def save(rel, data):
    path = os.path.join(MOD, *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print("wrote", rel)


def scale(v):
    return {"X": v, "Y": v, "Z": v}


def derive_character(bp, src, dst, template, model, adult):
    data = load(os.path.join(bp, src))
    data["TemplateSpec"]["TemplateName"] = template
    data["TemplateSpec"]["BackwardCompatibleTemplateNames"] = []
    model_child = data["Children"]["Model_Preserved"]
    model_child["TimbermeshSpec"]["Model"] = model
    model_child["TransformSpec"] = {"Position": scale(0.0), "Rotation": scale(0.0), "Scale": scale(BODY_SCALE)}
    walker = data["WalkerSpeedManagerSpec"]
    walker["BaseWalkingSpeed"] = round(walker["BaseWalkingSpeed"] * WALK_FACTOR, 3)
    walker["BaseSlowedSpeed"] = round(walker["BaseSlowedSpeed"] * WALK_FACTOR, 3)
    data["MovementAnimatorSpec"]["AnimationSpeedScale"] = round(
        data["MovementAnimatorSpec"].get("AnimationSpeedScale", 1.0) * ANIMATION_FACTOR, 3)
    # keep the vanilla label key: CharacterBatchControlTab.GetSortingKey throws for any other key
    assert data["SimpleLabeledEntitySpec"]["EntityNameLocKey"] in ("Beaver.Adult.TemplateName", "Beaver.Child.TemplateName")
    if adult:
        data["WorkerSpec"]["WorkerType"] = WORKER_TYPE
    # our marker: drives the Ringtail decorators (coat, day rest, registry)
    data["PandabornRingtailSpec"] = {
        "Kind": "Ringtail",
        "Textures": COATS_ADULT if adult else COATS_CHILD,
        "RestStartHours": 0.0,
        "RestEndHours": 8.0,
        "SleepBelow": 0.55,
        "AppetiteFactor": APPETITE_FACTOR,
    }
    save(dst, data)


def derive_workplace(bp, src, dst, template, name_key, desc_key, tool_order):
    data = load(os.path.join(bp, src))
    data["TemplateSpec"]["TemplateName"] = template
    data["TemplateSpec"]["BackwardCompatibleTemplateNames"] = []
    wp = data["WorkplaceSpec"]
    wp["DefaultWorkerType"] = WORKER_TYPE
    wp["DisallowOtherWorkerTypes"] = True
    wp["WorkerTypeUnlockCosts"] = []   # required: Workplace.ValidateWorkplaceSpec throws otherwise
    data["LabeledEntitySpec"]["DisplayNameLocKey"] = name_key
    data["LabeledEntitySpec"]["DescriptionLocKey"] = desc_key
    data["PlaceableBlockObjectSpec"]["ToolOrder"] = tool_order
    data["PandabornRingtailWorkplaceSpec"] = {}
    save(dst, data)


def derive_loft(bp):
    data = load(os.path.join(bp, "Buildings/Housing/Lodge/Lodge.Folktails.blueprint.json"))
    data["TemplateSpec"]["TemplateName"] = "RingtailLoft.Inkpaws"
    data["TemplateSpec"]["BackwardCompatibleTemplateNames"] = []
    data.pop("ProcreationHouseSpec", None)   # Inkpaw cubs are not born in lofts (Ringtail litters are stage 2)
    data["LabeledEntitySpec"]["DisplayNameLocKey"] = "Pandaborn.Ringtails.Loft.DisplayName"
    data["LabeledEntitySpec"]["DescriptionLocKey"] = "Pandaborn.Ringtails.Loft.Description"
    data["PlaceableBlockObjectSpec"]["ToolOrder"] = data["PlaceableBlockObjectSpec"]["ToolOrder"] + 1
    data["PandabornLoftSpec"] = {}
    save("Buildings/Pandaborn/Ringtails/RingtailLoft.Inkpaws.blueprint.json", data)


def derive_outfits(bp):
    for outfit_id in ("Hauler", "Gatherer"):
        src = os.path.join(bp, "WorkerOutfits", "WorkerOutfit.%s.Beaver.Folktails.blueprint.json" % outfit_id)
        if not os.path.exists(src):
            # fall back to any Folktails beaver outfit file with this id
            for root, _, files in os.walk(os.path.join(bp, "WorkerOutfits")):
                for f in files:
                    d = load(os.path.join(root, f)).get("WorkerOutfitSpec", {})
                    if d.get("Id") == outfit_id and d.get("FactionId") == "Folktails" and d.get("WorkerType") == "Beaver":
                        src = os.path.join(root, f)
        data = load(src)
        data["WorkerOutfitSpec"]["FactionId"] = "Inkpaws"
        data["WorkerOutfitSpec"]["WorkerType"] = WORKER_TYPE
        save("WorkerOutfits/Pandaborn/WorkerOutfit.%s.%s.Inkpaws.blueprint.json" % (outfit_id, WORKER_TYPE), data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blueprints", default=r"E:\PandabornDev\reference\Blueprints")
    bp = ap.parse_args().blueprints
    derive_character(bp, "Characters/Beaver/BeaverAdult.blueprint.json",
                     "Characters/Pandaborn/RingtailAdult.Inkpaws.blueprint.json",
                     "RingtailAdult.Inkpaws", "Characters/Pandaborn/InkpawAdult.Model", True)
    derive_character(bp, "Characters/Beaver/BeaverChild.blueprint.json",
                     "Characters/Pandaborn/RingtailChild.Inkpaws.blueprint.json",
                     "RingtailChild.Inkpaws", "Characters/Pandaborn/InkpawChild.Model", False)
    derive_workplace(bp, "Buildings/DistrictManagement/HaulingPost/HaulingPost.Folktails.blueprint.json",
                     "Buildings/Pandaborn/Ringtails/RingtailHaulingPost.Inkpaws.blueprint.json",
                     "RingtailHaulingPost.Inkpaws", "Pandaborn.Ringtails.CourierLoft.DisplayName",
                     "Pandaborn.Ringtails.CourierLoft.Description", 21)
    derive_workplace(bp, "Buildings/Food/GathererFlag/GathererFlag.Folktails.blueprint.json",
                     "Buildings/Pandaborn/Ringtails/RingtailGathererFlag.Inkpaws.blueprint.json",
                     "RingtailGathererFlag.Inkpaws", "Pandaborn.Ringtails.ForagersNest.DisplayName",
                     "Pandaborn.Ringtails.ForagersNest.Description", 11)
    derive_loft(bp)
    derive_outfits(bp)


if __name__ == "__main__":
    main()
