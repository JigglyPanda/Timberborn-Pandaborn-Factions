"""Derive the Inkpaws copies of vanilla Folktails blueprints from the vanilla blueprint dump.

Milestone 0 reuses vanilla Folktails content. Some specs cannot be shared and need a faction-owned copy:
the adult/child character templates (they carry the body mesh), the bot template, the modular shaft parts,
decals and worker outfits (both keyed by FactionId). This script writes those copies into
mod/PandabornFactions so they can be regenerated after a game update. Hand-written files (faction,
collections, localization) are not touched.

Usage: python src/pipeline/derive_vanilla_copies.py [--blueprints E:\\PandabornDev\\reference\\Blueprints]
Standard library only.
"""
import argparse
import json
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MOD = os.path.join(REPO, "mod", "PandabornFactions")
FACTION = "Inkpaws"
SOURCE_FACTION = "Folktails"

# vanilla blueprint (relative to the dump) -> (mod path, template name, body model).
# SimpleLabeledEntitySpec.EntityNameLocKey is deliberately left at the vanilla value
# (Beaver.Adult.TemplateName / Beaver.Child.TemplateName / Bot.TemplateName): the Population tab of the
# batch-control window (CharacterBatchControlTab.GetSortingKey) throws ArgumentOutOfRangeException for any
# other key. tools/validate.py enforces this.
CHARACTERS = {
    "Characters/Beaver/BeaverAdult.blueprint.json": (
        "Characters/Pandaborn/InkpawAdult.Inkpaws.blueprint.json",
        "InkpawAdult.Inkpaws", "Characters/Pandaborn/InkpawAdult.Model"),
    "Characters/Beaver/BeaverChild.blueprint.json": (
        "Characters/Pandaborn/InkpawChild.Inkpaws.blueprint.json",
        "InkpawChild.Inkpaws", "Characters/Pandaborn/InkpawChild.Model"),
}


def load(path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def save(rel, data):
    path = os.path.join(MOD, *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("wrote", rel)


def derive_characters(bp):
    for src, (dst, template_name, model) in CHARACTERS.items():
        data = load(os.path.join(bp, src))
        data["TemplateSpec"]["TemplateName"] = template_name
        data["TemplateSpec"]["BackwardCompatibleTemplateNames"] = []
        data["Children"]["Model_Preserved"]["TimbermeshSpec"]["Model"] = model
        save(dst, data)


def derive_bot(bp):
    data = load(os.path.join(bp, "Characters/Bot/Bot.Folktails.blueprint.json"))
    data["TemplateSpec"]["TemplateName"] = "Bot.Inkpaws"
    data["TemplateSpec"]["BackwardCompatibleTemplateNames"] = []
    data["NumberedEntityNamerSpec"]["FormatLocKey"] = "Bot.DisplayName.Inkpaws"
    # Body, material and hats stay the Folktails bot's (Folktails material collection is active).
    save("Characters/Pandaborn/Bot.Inkpaws.blueprint.json", data)


def derive_shaft_parts(bp):
    data = load(os.path.join(bp, "Buildings/Power/PowerShaft/Models/ModularShaftParts.Folktails.blueprint.json"))
    save("Buildings/Pandaborn/PowerShaft/ModularShaftParts.Inkpaws.blueprint.json", data)


def derive_faction_keyed(bp, folder, spec_name):
    src_dir = os.path.join(bp, folder)
    for name in sorted(os.listdir(src_dir)):
        if not name.endswith("." + SOURCE_FACTION + ".blueprint.json"):
            continue
        data = load(os.path.join(src_dir, name))
        assert data[spec_name]["FactionId"] == SOURCE_FACTION, name
        data[spec_name]["FactionId"] = FACTION
        new_name = name.replace("." + SOURCE_FACTION + ".blueprint.json", "." + FACTION + ".blueprint.json")
        save(folder + "/Pandaborn/" + new_name, data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blueprints", default=r"E:\PandabornDev\reference\Blueprints")
    args = ap.parse_args()
    if not os.path.isdir(args.blueprints):
        sys.exit("vanilla blueprint dump not found: " + args.blueprints)
    derive_characters(args.blueprints)
    derive_bot(args.blueprints)
    derive_shaft_parts(args.blueprints)
    derive_faction_keyed(args.blueprints, "Decals", "DecalSpec")
    derive_faction_keyed(args.blueprints, "WorkerOutfits", "WorkerOutfitSpec")


if __name__ == "__main__":
    main()
