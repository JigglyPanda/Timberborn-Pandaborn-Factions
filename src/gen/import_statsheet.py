#!/usr/bin/env python3
"""The balance model's stat sheet (tools/sim/out/statsheet.json) and the catalogue.

    python src/gen/import_statsheet.py --check           # report every number where the catalogue and the sheet differ
    python src/gen/import_statsheet.py --write [--force] # one-time import: writes catalogue/{goods,needs,recipes,plants}.toml

The catalogue is the single source of truth. The import runs once, to enter the sheet's numbers with their provenance
(M model / V vanilla / G guess, kept as `src` on every item); from then on a balance change is an edit to one catalogue
file followed by `tools/pandaborn.ps1 all`. --check (also run by `pandaborn.ps1 validate`) lists the drift between the
model's latest sheet and the catalogue so the balance lane can see what it has not carried over yet, or what the
catalogue settled differently on purpose (SETTLED below records the owner's settled numbers, which win over the sheet).

Mapping decisions the sheet leaves open are made here, in one place: the vanilla basis of every item (look, carrying,
goods group), recipe ids for the sheet's unnamed rows, and which sheet rows are not data yet (the cistern tap and the
dew collector need code; the star tower is a Ringtail building for 1.1). Poles and cured poles are written as the
vanilla Plank and TreatedPlank: catalogue/rules.toml [poles] decides whether they are renamed or replaced.
"""
import argparse
import json
import os
import re
import sys
import tomllib

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SHEET = os.path.join(REPO, "tools", "sim", "out", "statsheet.json")
CAT = os.path.join(REPO, "catalogue")

# settled numbers (coordinator, 2026-11-14) that win over the sheet
SETTLED = {
    ("plant", "PandabornShootBamboo", "dry_days"): 5,
    ("plant", "PandabornCabbage", "dry_days"): 7,
    ("plant", "PandabornTimberBamboo", "dry_days"): 7,
    ("good", "PandabornTea", "consumption.Thirst"): 0.2,
}
POLE_IDS = {"PandabornPole": "Plank", "PandabornCuredPole": "TreatedPlank"}

GOOD_BASIS = {
    "PandabornBambooShoots": "Carrot", "PandabornCabbage": "Carrot", "PandabornPersimmons": "Carrot",
    "PandabornBambooMushrooms": "Carrot", "PandabornSteamedShoots": "GrilledPotato", "PandabornPickles": "GrilledPotato",
    "PandabornSteamedRice": "Bread", "PandabornSweetRiceBalls": "CattailCracker", "PandabornHotPot": "MaplePastry",
    "PandabornBambooSeedCakes": "MaplePastry", "PandabornTea": "MapleSyrup", "PandabornRice": "Wheat",
    "PandabornRiceFlour": "WheatFlour", "PandabornSichuanPepper": "Wheat", "PandabornTeaLeaves": "Wheat",
    "PandabornBambooSeed": "SunflowerSeeds", "PandabornPole": "Plank", "PandabornCuredPole": "TreatedPlank",
    "PandabornPaperLantern": "Book",
}
FOOD_GROUP = {"PandabornTea"}  # a drink that sits with the foods, not the ingredients
RECIPES = {  # sheet id -> (catalogue id, vanilla basis recipe) ; None = not data yet
    "PandabornSteamedShoots": ("PandabornSteamedShoots", "GrilledPotato"),
    "PandabornSteamedRice": ("PandabornSteamedRice", "Bread"),
    "PandabornPickles": ("PandabornPickles", "Paper"),
    "PandabornRiceFlour": ("PandabornRiceFlour", "WheatFlour"),
    "PandabornSweetRiceBalls": ("PandabornSweetRiceBalls", "MaplePastry"),
    "PandabornBambooSeedCakes": ("PandabornBambooSeedCakes", "MaplePastry"),
    "PandabornHotPot": ("PandabornHotPot", "MaplePastry"),
    "PandabornTea": ("PandabornTea", "Paper"),
    "Paper (from poles)": ("PandabornPaper", "Paper"),
    "PandabornPaperLantern": ("PandabornPaperLantern", "Paper"),
    "PandabornCuredPole": ("PandabornCuredPole", "TreatedPlank"),
    "PandabornWoodenOx": ("PandabornWoodenOx", "Bot.Folktails"),
    "Gear": None, "Water": None,   # the vanilla recipes, unchanged
    "PandabornDewWater": ("PandabornDewWater", "Paper"),   # data alone: a steady trickle; the drought limiter is code
    "PandabornCisternTap": None,   # needs code (water module)
    "SciencePointsStarTower": None,   # Ringtail building, 1.1
}
NEEDS_BASIS = {
    "PandabornNap": ("RooftopTerrace", "own"), "PandabornTea": ("Bread", "good:PandabornTea"),
    "PandabornTeahouse": ("DomedGarden", "building:PandabornTeahouse"), "PandabornPlay": ("Lido", "own"),
    "PandabornCubWatching": ("Agora", "own"), "PandabornSoak": ("MudPit", "own"),
    "PandabornContemplation": ("ContemplationSpot", "own"), "PandabornPerformance": ("DanceHall", "own"),
    "PandabornFestive": ("Bread", "own"),
}
AWE = {"PandabornMemorialArch": ("BrazierOfBonding", 6), "PandabornGreatSittingPanda": ("HallOfAbundance", 12),
       "PandabornSkyLantern": ("EarthRecultivator", 10)}
DECORATION_NEEDS = {"PandabornPandaStatue": "BeaverStatue", "PandabornBambooPinwheel": "Weathervane"}
PLANT_BASIS = {
    "PandabornShootBamboo": "Carrot", "PandabornCabbage": "Carrot", "PandabornTimberBamboo": "ChestnutTree",
    "PandabornRice": "Cattail", "PandabornTeaBush": "BlueberryBush", "PandabornSichuanPepper": "Sunflower",
    "PandabornPersimmonTree": "ChestnutTree",
}


def load_sheet(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def num(x):
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def parse_amounts(s):
    """'PandabornPole x2' -> {'PandabornPole': 2}"""
    m = re.match(r"\s*([A-Za-z]+)\s*x(\d+)", s)
    return {POLE_IDS.get(m.group(1), m.group(1)): int(m.group(2))} if m else None


def parse_fuel(s):
    m = re.match(r"\s*([A-Za-z]+),\s*1 per (\d+) cycles", s or "")
    return (m.group(1), int(m.group(2))) if m else (None, None)


def sub(table):
    return {POLE_IDS.get(k, k): v for k, v in (table or {}).items()}


# ------------------------------------------------------------------------------------------------ sheet -> items
def sheet_items(sheet):
    """kind -> {id: {field: value}} as the catalogue would hold them, plus 'src' notes."""
    out = {"good": {}, "need": {}, "recipe": {}, "plant": {}}
    for g in sheet["goods"]:
        gid = g["id"]
        cons = dict(g.get("ConsumptionEffects") or {})
        e = {"basis": GOOD_BASIS[gid], "good_type": g["GoodType"], "weight": g["Weight"], "consumption": cons,
             "src": g.get("basis", "")}
        if gid in POLE_IDS:
            e["when_poles"] = "good"
        out["good"][gid] = e
    for n in sheet["needs"]:
        nid = n["id"]
        if nid in NEEDS_BASIS:
            basis, name = NEEDS_BASIS[nid]
            out["need"][nid] = {"basis": basis, "name_from": name, "group": n["group"],
                                "daily_delta": n["DailyDelta"], "favorable_wellbeing": n["FavorableWellbeing"],
                                "importance": n["ImportanceMultiplier"], "wastable": n["Wastable"],
                                "src": n.get("basis", "")}
        elif nid.startswith("Pandaborn<Dish>"):
            for g in sheet["goods"]:
                if g.get("dish") and g["id"] not in out["need"]:
                    out["need"][g["id"]] = {"basis": "Bread", "name_from": "good:" + g["id"], "group": n["group"],
                                            "daily_delta": n["DailyDelta"], "favorable_wellbeing": g["dish"],
                                            "importance": n["ImportanceMultiplier"], "wastable": n["Wastable"],
                                            "src": "%s; wellbeing from the dish tier" % n.get("basis", "")}
        elif "MemorialArch" in nid:
            for aid, (basis, fw) in AWE.items():
                out["need"][aid] = {"basis": basis, "name_from": "building:" + aid, "group": n["group"],
                                    "daily_delta": n["DailyDelta"], "favorable_wellbeing": fw,
                                    "importance": n["ImportanceMultiplier"], "wastable": n["Wastable"],
                                    "src": n.get("basis", "")}
    # decoration needs the sheet does not list (one per decoration kind, as vanilla): vanilla numbers
    for did, basis in DECORATION_NEEDS.items():
        out["need"][did] = {"basis": basis, "name_from": "building:" + did, "not_in_sheet": True,
                            "src": "V (%s): not in the stat sheet" % basis}
    for r in sheet["recipes"]:
        m = RECIPES.get(r["id"], "missing")
        if m == "missing":
            raise SystemExit("import: the sheet has a recipe %r this importer does not map; add it to RECIPES" % r["id"])
        if m is None:
            continue
        rid, basis = m
        fuel, lasts = parse_fuel(r.get("Fuel"))
        e = {"basis": basis, "cycle_hours": r["CycleDurationInHours"], "ingredients": sub(r["Ingredients"]),
             "products": {k: v for k, v in sub(r["Products"]).items() if k != "Wooden Ox"},
             "capacity": r["CyclesCapacity"], "src": "%s (building: %s)" % (r.get("basis", ""), r["building"])}
        if fuel:
            e["fuel"], e["cycles_fuel_lasts"] = fuel, lasts
        else:
            e["fuel"], e["cycles_fuel_lasts"], e["fuel_capacity"] = "", 0, 0
        out["recipe"][rid] = e
    for p in sheet["plants"]:
        pid = p["id"]
        e = {"basis": PLANT_BASIS[pid], "plant_hours": p["PlantTimeInHours"], "growth_days": p["GrowthTimeInDays"],
             "src": p.get("basis", {})}
        harvest = p["harvest"]
        if pid in ("PandabornTimberBamboo",):
            e["cut_yield"] = {"Plank": 2}
            e["cut_hours"] = p["RemovalTimeInHours"]
            e["gather_yield"], e["gather_days"], e["gather_hours"] = {"PandabornBambooMushrooms": 2}, 3.0, 0.5
        elif pid == "PandabornPersimmonTree":
            e["gather_yield"], e["gather_days"], e["gather_hours"] = {"PandabornPersimmons": 3}, 6.0, 1.0
            e["cut_yield"], e["cut_hours"] = {"Log": 3}, p["RemovalTimeInHours"]
        elif pid == "PandabornTeaBush":
            e["gather_yield"], e["gather_days"], e["gather_hours"] = {"PandabornTeaLeaves": 3}, 3.0, p["RemovalTimeInHours"]
            e["planter"] = "Farmhouse"
        else:
            e["cut_yield"], e["cut_hours"] = parse_amounts(harvest), p["RemovalTimeInHours"]
        if num(p.get("DaysToDieDry")) is not None:
            e["dry_days"] = p["DaysToDieDry"]
        w = p.get("Water", "")
        m = re.match(r"(\d+)/(\d+), DaysToDie ([\d.]+)", w)
        if m:
            e["flood_min"], e["flood_max"], e["flood_days"] = int(m.group(1)), int(m.group(2)), float(m.group(3))
        if w.startswith("arid"):
            m2 = re.search(r"dies ([\d.]+) d", w)
            e["wet_days"] = float(m2.group(1)) if m2 else 2.0
        if num(p.get("ReproductionChance")) is not None and (p["ReproductionChance"] or
                                                              PLANT_BASIS[pid] in ("ChestnutTree", "BlueberryBush")):
            e["reproduction"] = p["ReproductionChance"]   # crops have no ReproducibleSpec: 0 is their default
        out["plant"][pid] = e
    for k, v in SETTLED.items():
        kind, i, field = k
        if i in out[kind]:
            if "." in field:
                a, b = field.split(".")
                out[kind][i].setdefault(a, {})[b] = v
            else:
                out[kind][i][field] = v
    return out


# ------------------------------------------------------------------------------------------------------ check
COMPARE = {"good": ("good_type", "weight", "consumption"),
           "need": ("group", "daily_delta", "favorable_wellbeing", "importance", "wastable"),
           "recipe": ("cycle_hours", "ingredients", "products", "capacity", "fuel", "cycles_fuel_lasts"),
           "plant": ("plant_hours", "growth_days", "cut_yield", "cut_hours", "gather_yield", "gather_days",
                     "gather_hours", "dry_days", "flood_min", "flood_max", "flood_days", "wet_days", "reproduction")}
FILES = {"good": ("goods", "goods"), "need": ("needs", "needs"), "recipe": ("recipes", "recipes"),
         "plant": ("plants", "plants")}


def check(sheet):
    want = sheet_items(sheet)
    drift = []
    for kind, (fname, table) in FILES.items():
        p = os.path.join(CAT, fname + ".toml")
        have = {}
        if os.path.isfile(p):
            with open(p, "rb") as f:
                have = tomllib.load(f).get(table, {})
        for i, w in want[kind].items():
            h = have.get(i)
            if h is None:
                drift.append("%s %s: in the stat sheet, not in catalogue/%s.toml" % (kind, i, fname))
                continue
            if w.get("not_in_sheet"):
                continue
            for field in COMPARE[kind]:
                if w.get(field) != h.get(field) and not (w.get(field) is None and field not in h):
                    note = " (settled)" if any(k[1] == i and k[2].split(".")[0] == field for k in SETTLED) else ""
                    drift.append("%s %s.%s: sheet %s, catalogue %s%s" % (kind, i, field, json.dumps(w.get(field)),
                                                                         json.dumps(h.get(field)), note))
        for i in have:
            if i not in want[kind] and not have[i].get("not_in_sheet"):
                drift.append("%s %s: in catalogue/%s.toml, not in the stat sheet" % (kind, i, fname))
    return drift


# ------------------------------------------------------------------------------------------------------ write
def toml_value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, dict):
        return "{ " + ", ".join("%s = %s" % (k if re.match(r"^[A-Za-z0-9_]+$", k) else json.dumps(k), toml_value(x))
                                for k, x in v.items()) + " }"
    if isinstance(v, list):
        return "[" + ", ".join(toml_value(x) for x in v) + "]"
    raise TypeError(v)


HEADERS = {
    "good": """# Inkpaws goods. Numbers imported from the balance model's stat sheet (tools/sim/out/statsheet.json) on %s;
# this file is now the source of truth (src/gen/import_statsheet.py --check reports drift from the latest sheet).
# src = where each number comes from: M model (tools/sim, question), V vanilla analogue, G guess.
# basis = the vanilla good copied for look, carrying and stockpile; fields: catalogue/README.md.
# Poles and cured poles exist as goods only with rules.toml [poles] mode = "good" (when_poles).

[collection]
id = "Goods.Inkpaws"
# vanilla goods the Inkpaws keep beyond the Common collection (logs, planks, gears, water, berries, metal...)
vanilla = ["Paper", "Antidote", "Dandelion", "TreatedPlank"]
""",
    "need": """# Inkpaws needs (imported from the stat sheet, see goods.toml). basis = the vanilla need copied;
# name_from = own (text/needs.json) | good:<id> (the good's plural name) | building:<id> (the building's name).

[collection]
id = "Needs.Inkpaws"
# vanilla needs kept beyond the Common collection (hunger, thirst, sleep, shelter, wet fur, injury, contamination,
# teeth, campfire, lantern, roof, rooftop terrace, shrub)
vanilla = ["Antidote", "Scarecrow"]
""",
    "recipe": """# Inkpaws recipes (imported from the stat sheet, see goods.toml). basis = the vanilla recipe copied.
# Name and icon follow the first product. Plank and TreatedPlank are the poles and cured poles (rules.toml [poles]).
""",
    "plant": """# Inkpaws plants (imported from the stat sheet, see goods.toml). basis = the vanilla plant copied: its model
# is the stand-in until the growth-stage models exist. planter = PlantableSpec.ResourceGroup (Farmhouse, Forester,
# AquaticFarmhouse). wet_days adds the arid rule (dies on moist soil) and drops WateredNaturalResourceSpec.

[collection]
id = "NaturalResources.Inkpaws"
# vanilla plants kept beyond the Common collection (birch, oak, pine, blueberry, succulent): dandelion feeds the antidote
vanilla = ["Dandelion"]
""",
}


def write(sheet, force):
    import datetime
    items = sheet_items(sheet)
    today = datetime.date.today().isoformat()
    for kind, (fname, table) in FILES.items():
        p = os.path.join(CAT, fname + ".toml")
        if os.path.isfile(p) and not force:
            print("import: %s exists; the catalogue is the source of truth now (use --check, or --force to "
                  "overwrite it)" % p)
            continue
        lines = [HEADERS[kind] % today if "%s" in HEADERS[kind] else HEADERS[kind]]
        for i, e in items[kind].items():
            lines.append("\n[%s.%s]" % (table, i))
            if kind == "plant" and "gather_yield" in e and e["basis"] in ("Carrot", "Cattail", "Sunflower"):
                raise SystemExit("import: %s gathers but its basis cannot" % i)
            for k, v in e.items():
                if k == "src":
                    continue
                lines.append("%s = %s" % (k, toml_value(v)))
            src = e.get("src")
            if src:
                lines.append("src = %s" % toml_value(src))
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines) + "\n")
        print("import: wrote %s (%d items)" % (p, len(items[kind])))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sheet", default=SHEET)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    sheet = load_sheet(a.sheet)
    if a.write:
        write(sheet, a.force)
    drift = check(sheet)
    print("statsheet drift: %d difference(s) between %s and the catalogue" % (len(drift), os.path.relpath(a.sheet, REPO)))
    for d in drift:
        print("  " + d)
    return 0


if __name__ == "__main__":
    sys.exit(main())
