#!/usr/bin/env python3
"""Writes the validator's fixture mods: one folder per case, each a tiny mod with one deliberate mistake, plus
expect.json naming the error the validator must report. Run `python tools/validate.py --self-test` to check them.

    python tools/tests/validate/make_fixtures.py [--blueprints E:\\PandabornDev\\reference\\Blueprints]

Fixtures are built from small vanilla blueprints (Bench, Good.Plank) so they track the game; the files are committed so
the suite runs without regenerating. Standard library only.
"""
import argparse
import copy
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SUFFIX = ".PandabornFixture"
MANIFEST = {"Name": "Validator fixture", "Version": "0.0.1", "Id": "Test.PandabornFixture",
            "MinimumGameVersion": "1.1.0.0", "Description": "validator fixture", "RequiredMods": [],
            "OptionalMods": []}
PNG_1x1 = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d4944415478da63f8"
                        "cfc0f01f0005000201a5f1d2d80000000049454e44ae426082")


def load(bp_dir, rel):
    with open(os.path.join(bp_dir, rel), "rb") as f:
        return json.loads(f.read().decode("utf-8-sig"))


def write(root, rel, data):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if isinstance(data, bytes):
        with open(p, "wb") as f:
            f.write(data)
    elif isinstance(data, str):
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(data)
    else:
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(data, indent=2) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blueprints", default=r"E:\PandabornDev\reference\Blueprints")
    a = ap.parse_args()
    bench = load(a.blueprints, "Buildings/Decoration/Bench/Bench.Folktails.blueprint.json")
    bench["TemplateSpec"]["TemplateName"] = "Bench" + SUFFIX
    bench["TemplateSpec"]["BackwardCompatibleTemplateNames"] = []
    plank = load(a.blueprints, "Goods/Good.Plank.blueprint.json")
    plank["GoodSpec"]["Id"] = "PandabornFixtureGood"
    bench_rel = "Buildings/Pandaborn/Fixture/Bench" + SUFFIX + ".blueprint.json"
    good_rel = "Goods/Pandaborn/Good.PandabornFixtureGood.blueprint.json"
    gen = ["--template-suffix", SUFFIX]

    cases = {}

    def case(name, errors, files, args=None, clean=False):
        cases[name] = (errors, files, (args or []) + gen, clean)

    base = {bench_rel: bench, good_rel: plank}
    case("valid_minimal", [], base, clean=True)

    def with_bench(mutate, extra=None):
        b = copy.deepcopy(bench)
        mutate(b)
        files = {bench_rel: b}
        files.update(extra or {})
        return files

    case("unknown_spec_key", ["unknown spec key BuildingSpecc"],
         with_bench(lambda b: b.__setitem__("BuildingSpecc", b.pop("BuildingSpec"))))
    case("unknown_field", ["unknown field BuildingCosts", "did you mean BuildingCost"],
         with_bench(lambda b: b["BuildingSpec"].__setitem__("BuildingCosts", b["BuildingSpec"].pop("BuildingCost"))))
    case("wrong_type_int", ["ScienceCost: expected an integer"],
         with_bench(lambda b: b["BuildingSpec"].__setitem__("ScienceCost", 2.5)))
    case("wrong_type_bool", ["PlaceFinished: expected true or false"],
         with_bench(lambda b: b["BuildingSpec"].__setitem__("PlaceFinished", "no")))
    case("bad_enum", ["'Groundd' is not a value of BlockStackable"],
         with_bench(lambda b: b["BlockObjectSpec"]["Blocks"][0].__setitem__("Stackable", "Groundd")))
    case("bad_flags_enum", ["'Topp' is not a value of BlockOccupations"],
         with_bench(lambda b: b["BlockObjectSpec"]["Blocks"][0].__setitem__("Occupations", "Bottom, Topp")))
    case("vector_missing_key", ["vector3 needs exactly the keys X, Y, Z"],
         with_bench(lambda b: b["BuildingAccessibleSpec"]["LocalAccess"].pop("Z")))
    case("nested_unknown_field", ["unknown field Amout"],
         with_bench(lambda b: b["BuildingSpec"]["BuildingCost"][0].__setitem__("Amout", 3)))
    sprite = {"Sprites/Pandaborn/Fixture/BenchIcon.png": PNG_1x1,
              "Sprites/Pandaborn/Fixture/BenchIcon.png.meta.json": {"isSprite": True}}
    case("asset_case", ["differs in case from the file"],
         with_bench(lambda b: b["LabeledEntitySpec"].__setitem__("Icon", "Sprites/Pandaborn/Fixture/benchicon"), sprite))
    case("asset_backslash", ["uses a backslash"],
         with_bench(lambda b: b["LabeledEntitySpec"].__setitem__("Icon", "Sprites\\Pandaborn\\Fixture\\BenchIcon"),
                    sprite))
    case("asset_missing", ["Sprites/Pandaborn/Fixture/NoSuchIcon does not resolve"],
         with_bench(lambda b: b["LabeledEntitySpec"].__setitem__("Icon", "Sprites/Pandaborn/Fixture/NoSuchIcon")))
    case("sprite_without_meta", ["has no {\"isSprite\": true} meta file"],
         with_bench(lambda b: b["LabeledEntitySpec"].__setitem__("Icon", "Sprites/Pandaborn/Fixture/BenchIcon"),
                    {"Sprites/Pandaborn/Fixture/BenchIcon.png": PNG_1x1}))
    case("nested_blueprint_missing", ["Construction/NoSuch.blueprint does not resolve"],
         with_bench(lambda b: b["Children"].__setitem__("Base#nested", {"BlueprintPath": "Construction/NoSuch.blueprint"})))

    g = copy.deepcopy(plank)
    g["PandabornFixtureSpec"] = {"Strength": 1}
    schema = {"specs": {"PandabornFixtureSpec": {"fullName": "Pandaborn.Fixture.PandabornFixtureSpec", "origin": "mod",
                                                 "fields": {"Strength": {"type": {"kind": "int"}}}}},
              "types": {}, "enums": {}}
    case("custom_spec_in_global_data", ["custom spec PandabornFixtureSpec in a blueprint that is indexed and read in "
                                        "every game"],
         {good_rel: g, "../fixture.schema.json": schema}, args=["--mod-schema", "{case}/fixture.schema.json"])
    case("custom_spec_unknown", ["unknown spec key PandabornFixtureSpec", "pass --mod-schema"], {good_rel: g})
    case("global_id_prefix", ["global id Grapes must start with Pandaborn"],
         {good_rel: dict(plank, GoodSpec=dict(plank["GoodSpec"], Id="Grapes"))})
    case("duplicate_vanilla_good", ["GoodSpec id Plank is also a vanilla id"],
         {good_rel: dict(plank, GoodSpec=dict(plank["GoodSpec"], Id="Plank"))}, args=["--id-prefix", ""])
    recipe = load(a.blueprints, "Recipes/Recipe.Plank.blueprint.json")
    case("duplicate_vanilla_recipe", ["RecipeSpec id Plank is also a vanilla id"],
         {"Recipes/Pandaborn/Recipe.PandabornX.blueprint.json": recipe}, args=["--id-prefix", ""])
    b2 = copy.deepcopy(bench)
    case("duplicate_template", ["template name Bench.PandabornFixture is also used by"],
         {bench_rel: bench, "Buildings/Pandaborn/Fixture/Bench2.PandabornFixture.blueprint.json": b2})
    b3 = copy.deepcopy(bench)
    b3["TemplateSpec"]["TemplateName"] = "Bench.Folktails2"
    case("template_suffix", ["template name Bench.Folktails2 must end in .PandabornFixture"], {bench_rel: b3})
    b4 = copy.deepcopy(bench)
    b4["TemplateSpec"]["TemplateName"] = "Bench.Folktails"
    case("template_clashes_vanilla", ["clashes with a vanilla template"], {bench_rel: b4},
         args=["--template-suffix", ".Folktails"])

    need = load(a.blueprints, "Needs/Need.Beaver.Campfire.blueprint.json")
    n1 = copy.deepcopy(need)
    n1["NeedSpec"]["Id"] = "PandabornFixtureNeed"
    case("need_in_no_collection", ["NeedSpec PandabornFixtureNeed is in no need collection"],
         {"Needs/Pandaborn/Need.PandabornFixtureNeed.blueprint.json": n1})
    n2 = copy.deepcopy(n1)
    n2["NeedSpec"]["NeedGroupId"] = "PandabornNoSuchGroup"
    nc = {"NeedCollectionSpec": {"CollectionId": "Common", "Needs": ["PandabornFixtureNeed"]}}
    case("need_bad_group", ["has NeedGroupId PandabornNoSuchGroup, which does not exist"],
         {"Needs/Pandaborn/Need.PandabornFixtureNeed.blueprint.json": n2,
          "NeedCollections/Pandaborn/NeedCollection.PandabornFixture.blueprint.json": nc})
    nc2 = {"NeedCollectionSpec": {"CollectionId": "PandabornFixtureNeeds", "Needs": ["PandabornFixtureNeed"]}}
    case("need_collection_unused", ["need collection PandabornFixtureNeeds is used by no faction"],
         {"Needs/Pandaborn/Need.PandabornFixtureNeed.blueprint.json": n1,
          "NeedCollections/Pandaborn/NeedCollection.PandabornFixture.blueprint.json": nc2})
    nc3 = {"NeedCollectionSpec": {"CollectionId": "Common", "Needs": ["PandabornGhostNeed"]}}
    case("need_collection_lists_missing_need", ["lists need PandabornGhostNeed, which does not exist"],
         {"NeedCollections/Pandaborn/NeedCollection.PandabornFixture.blueprint.json": nc3})

    case("bundle_without_pair", ["asset bundle pandabornfactionsfixture has no _mac build"],
         {"AssetBundles/pandabornfactionsfixture_win": b"not a real bundle"})
    case("vanilla_loc_override", ["loc key Good.Plank.DisplayName overrides vanilla text"],
         {"Localizations/enUS_PandabornFixture.csv": 'ID,Text,Comment\n"Good.Plank.DisplayName","Pole",""\n'})
    case("loc_comma_quote", ["space between comma and quote"],
         {"Localizations/enUS_PandabornFixture.csv": 'ID,Text,Comment\n"PandabornFixture.Key", "Text",""\n'})
    case("vanilla_path_override", ["file sits on a vanilla asset path"],
         {"Buildings/Decoration/Bench/Bench.Folktails.blueprint.json": bench})
    case("vanilla_collection_join", ["adds to vanilla template collection Buildings.Folktails"],
         {bench_rel: bench, "TemplateCollections/Pandaborn/TemplateCollection.Fixture.blueprint.json":
          {"TemplateCollectionSpec": {"CollectionId": "Buildings.Folktails",
                                      "Blueprints": [bench_rel[:-len(".json")]]}}})
    modifier = {"GoodSpec": {"Weigth": 2}}
    case("modifier_unknown_field", ["unknown field Weigth", "did you mean Weight"],
         {"Modifiers/Pandaborn/Good.Plank.optional.blueprint.json": modifier})

    # lock: a pandaborn-profile fixture with its own lock file
    lock = {"ids": {"template": {"Bench.PandabornFixture": {"since": "2026-11-14"},
                                 "Gone.PandabornFixture": {"since": "2026-11-14"}}, "good": {}}}
    case("lock_ids", ["good id PandabornFixtureGood is not in catalogue/ids.lock.json",
                      "locked template id Gone.PandabornFixture is no longer produced"],
         dict(base, **{"../fixture.lock.json": lock}),
         args=["--profile", "pandaborn", "--lock", "{case}/fixture.lock.json"])

    # faction-level: goods outside the faction's collections, material coverage, need not in faction collection
    faction = load(a.blueprints, "Factions/Faction.Folktails.blueprint.json")
    fs = faction["FactionSpec"]
    fs.update(Id="PandabornFixture", TemplateCollectionIds=["PandabornFixture.Buildings"],
              GoodCollectionIds=["PandabornFixture.Goods"], NeedCollectionIds=["PandabornFixture.Needs"],
              MaterialCollectionIds=["PandabornFixture.Materials"], StartingBuildingId="Bench" + SUFFIX)
    faction.pop("StartingFactionSpec", None)
    bcost = copy.deepcopy(bench)
    bcost["BuildingSpec"]["BuildingCost"] = [{"Id": "TreatedPlank", "Amount": 2}]
    fx = {"Factions/Pandaborn/Faction.PandabornFixture.blueprint.json": faction,
          bench_rel: bcost,
          "TemplateCollections/Pandaborn/TemplateCollection.PandabornFixture.Buildings.blueprint.json":
              {"TemplateCollectionSpec": {"CollectionId": "PandabornFixture.Buildings",
                                          "Blueprints": [bench_rel[:-len(".json")]]}},
          "GoodCollections/Pandaborn/GoodCollection.PandabornFixture.blueprint.json":
              {"GoodCollectionSpec": {"CollectionId": "PandabornFixture.Goods", "Goods": ["Log"]}},
          "NeedCollections/Pandaborn/NeedCollection.PandabornFixture.blueprint.json":
              {"NeedCollectionSpec": {"CollectionId": "PandabornFixture.Needs", "Needs": []}},
          "MaterialCollections/Pandaborn/MaterialCollection.PandabornFixture.blueprint.json":
              {"MaterialCollectionSpec": {"CollectionId": "PandabornFixture.Materials", "Materials": []}},
          "Needs/Pandaborn/Need.PandabornFixtureNeed.blueprint.json": n1,
          "NeedCollections/Pandaborn/NeedCollection.PandabornFixtureCommon.blueprint.json":
              {"NeedCollectionSpec": {"CollectionId": "Common", "Needs": []}},
          "NeedCollections/Pandaborn/NeedCollection.PandabornFixtureOther.blueprint.json":
              {"NeedCollectionSpec": {"CollectionId": "Folktails", "Needs": ["PandabornFixtureNeed"]}}}
    case("faction_rules", ["costs TreatedPlank, which is not in the faction's good collections",
                           "drops the Folktails material collection but uses Folktails models",
                           "need PandabornFixtureNeed is not in a need collection this mod's faction always lists",
                           "adds to vanilla need collection Folktails"],
         fx, args=["--template-suffix", SUFFIX])

    for name in os.listdir(HERE):
        p = os.path.join(HERE, name)
        if os.path.isdir(p):
            shutil.rmtree(p)
    for name, (errors, files, args, clean) in sorted(cases.items()):
        root = os.path.join(HERE, name)
        mod = os.path.join(root, "mod")
        write(mod, "manifest.json", MANIFEST)
        for rel, data in files.items():
            if rel.startswith("../"):
                write(root, rel[3:], data)
            else:
                write(mod, rel, data)
        args = [x.replace("{case}", root.replace("\\", "/")) for x in args]
        args = [x.replace(HERE.replace("\\", "/"), "{fixtures}") for x in args]
        write(root, "expect.json", {"errors": errors, "args": args, "clean": clean})
    print("wrote %d fixtures in %s" % (len(cases), HERE))


if __name__ == "__main__":
    main()
