#!/usr/bin/env python3
"""Tests tools/game_diff.py against a synthetic "next game version" made from the real dump and schema.

    python tools/tests/test_game_diff.py [--blueprints E:\\PandabornDev\\reference\\Blueprints]

The fake update (in a temp folder under E:\\PandabornDev\\build\\scratch): LumberMill's cost changes, Bench is removed,
Hedge moves to another folder, Good.Plank gets a new id, a brand-new blueprint appears; in the schema
BuildingSpec.ScienceCost is renamed ScienceCosts, DecalSpec is removed, an enum value goes and the Unity version
changes. Each must be reported, and the ones that feed our generated files must be in "affects us".
"""
import argparse
import io
import json
import os
import shutil
import sys
import contextlib

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO, "tools"))
import game_diff  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blueprints", default=r"E:\PandabornDev\reference\Blueprints")
    ap.add_argument("--scratch", default=r"E:\PandabornDev\build\scratch\game_diff_test")
    a = ap.parse_args()
    schema_old = os.path.join(REPO, "schema", "1.1.2.8.json")
    new_bp = os.path.join(a.scratch, "Blueprints")
    if os.path.isdir(a.scratch):
        shutil.rmtree(a.scratch)
    shutil.copytree(a.blueprints, new_bp)

    def edit(rel, fn):
        p = os.path.join(new_bp, *rel.split("/"))
        with open(p, "rb") as f:
            d = json.loads(f.read().decode("utf-8-sig"))
        fn(d)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2)

    edit("Buildings/Wood/LumberMill/LumberMill.Folktails.blueprint.json",
         lambda d: d["BuildingSpec"]["BuildingCost"][0].__setitem__("Amount", 20))
    os.remove(os.path.join(new_bp, "Buildings/Decoration/Bench/Bench.Folktails.blueprint.json"))
    os.makedirs(os.path.join(new_bp, "Buildings/Garden/Hedge"))
    shutil.move(os.path.join(new_bp, "Buildings/Decoration/Hedge/Hedge.Folktails.blueprint.json"),
                os.path.join(new_bp, "Buildings/Garden/Hedge/Hedge.Folktails.blueprint.json"))
    edit("Goods/Good.Plank.blueprint.json", lambda d: d["GoodSpec"].__setitem__("Id", "WoodPlank"))
    with open(os.path.join(new_bp, "Goods/Good.Brand.New.blueprint.json"), "w") as f:
        json.dump({"GoodSpec": {"Id": "BrandNew"}}, f)

    with open(schema_old, encoding="utf-8") as f:
        s = json.load(f)
    s["gameVersion"] = "1.2.0.0"
    s["unityVersion"] = "6000.9.1f1"
    bf = s["specs"]["BuildingSpec"]["fields"]
    bf["ScienceCosts"] = bf.pop("ScienceCost")
    del s["specs"]["DecalSpec"]
    occ = s["enums"]["Timberborn.BlockSystem.BlockStackable"]["values"]
    occ[:] = [v for v in occ if v["name"] != "UnfinishedPath"] if any(
        v["name"] == "UnfinishedPath" for v in occ) else occ[:-1]
    schema_new = os.path.join(a.scratch, "1.2.0.0.json")
    with open(schema_new, "w", encoding="utf-8") as f:
        json.dump(s, f)

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = game_diff.main(["--old-blueprints", a.blueprints, "--new-blueprints", new_bp,
                               "--old-schema", schema_old, "--new-schema", schema_new,
                               "--json", os.path.join(a.scratch, "report.json")])
    text = out.getvalue()
    rep = json.load(open(os.path.join(a.scratch, "report.json"), encoding="utf-8"))
    checks = [
        ("exit code 3 (affects us)", code == 3),
        ("LumberMill changed with the cost diff", any(e["path"].endswith("LumberMill.Folktails.blueprint") and
                                                      any("BuildingCost[0].Amount" in d for d in e["diff"])
                                                      for e in rep["blueprints"]["changed"])),
        ("Bench removed and feeds us", any(e["path"].endswith("Bench.Folktails.blueprint") and e["uses"]
                                           for e in rep["blueprints"]["removed"])),
        ("Hedge renamed (moved)", any(e["from"].endswith("Hedge.Folktails.blueprint") and
                                      e["to"].startswith("Buildings/Garden") for e in rep["blueprints"]["renamed"])),
        ("Plank id gone", "GoodSpec:Plank" in rep["ids_removed"]),
        ("Plank referenced by our files", any("GoodSpec Plank is gone" in x for x in rep["affects_us"])),
        ("new blueprint added", "Goods/Good.Brand.New.blueprint" in rep["blueprints"]["added"]),
        ("ScienceCost removed and used by us", any(f["field"] == "ScienceCost" and f["change"] == "removed" and
                                                   f["usedBy"] for f in rep["schema"]["fields"])),
        ("DecalSpec removed and used by us", any("spec DecalSpec was removed" in x for x in rep["affects_us"])),
        ("enum value removed", bool(rep["schema"]["enums"])),
        ("Unity change flagged", any(x.startswith("Unity ") for x in rep["affects_us"])),
    ]
    bad = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(("ok   " if ok else "FAIL ") + n)
    if bad:
        print(text[-3000:])
    print("\ngame_diff test: %d checks, %d failed" % (len(checks), len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
