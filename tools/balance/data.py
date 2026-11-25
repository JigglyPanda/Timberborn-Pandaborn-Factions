"""The numbers the game actually reads: vanilla blueprints and the generated Inkpaws build.

Nothing is typed in by hand here. `Game("Folktails")` is the vanilla reference dump; `Game("Inkpaws")` is the same dump
with the generated mod laid over it the way the game does it: files at the same path deep-merge, then the faction's
BlueprintModifiers are merged into their originals (CLAUDE.md, "Loading"). So a shelf size or a science cost printed
by this folder is the one a player gets from the last `tools/pandaborn.ps1 generate`.

Paths can be overridden with PANDABORN_VANILLA and PANDABORN_GEN.
"""
import json
import os

VANILLA = os.environ.get("PANDABORN_VANILLA", r"E:\PandabornDev\reference\Blueprints")
GEN = os.environ.get("PANDABORN_GEN", r"E:\PandabornDev\build\gen\PandabornFactions")
SUFFIX = ".blueprint.json"


def _read(path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def _merge(base, over):
    """The game's JSON merge: objects deep-merge, arrays replace, '#append' appends, '#delete' removes."""
    out = dict(base)
    for key, value in over.items():
        if key.endswith("#delete"):
            out.pop(key[:-7], None)
        elif key.endswith("#append"):
            out[key[:-7]] = list(out.get(key[:-7], [])) + list(value)
        elif isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def _scan(root):
    found = {}
    for folder, _, files in os.walk(root):
        for name in files:
            if name.endswith(SUFFIX):
                rel = os.path.relpath(os.path.join(folder, name), root).replace("\\", "/")
                found[rel[:-len(".json")].lower()] = os.path.join(folder, name)
    return found


class Game:
    """Every blueprint of one faction's game, indexed by the ids a balance question asks for."""

    def __init__(self, faction):
        self.faction = faction
        files = {key: _read(path) for key, path in _scan(VANILLA).items()}
        if faction == "Inkpaws":
            optional = {}
            for key, path in _scan(GEN).items():
                data = _read(path)
                if key.endswith(".optional.blueprint"):
                    optional[key] = data
                else:
                    files[key] = _merge(files[key], data) if key in files else data
            spec = next(d["FactionSpec"] for d in files.values() if d.get("FactionSpec", {}).get("Id") == "Inkpaws")
            for pair in spec["BlueprintModifiers"]:
                original, modifier = pair["Original"].lower(), pair["Modifier"].lower()
                if original in files and modifier in optional:
                    files[original] = _merge(files[original], optional[modifier])
        self.files = files
        self.recipes, self.goods, self.needs, self.templates, self.bonus_types = {}, {}, {}, {}, {}
        for data in files.values():
            if "RecipeSpec" in data:
                self.recipes[data["RecipeSpec"]["Id"]] = data["RecipeSpec"]
            if "GoodSpec" in data:
                self.goods[data["GoodSpec"]["Id"]] = data["GoodSpec"]
            if "NeedSpec" in data:
                self.needs[data["NeedSpec"]["Id"]] = data["NeedSpec"]
            if "BonusTypeSpec" in data:
                self.bonus_types[data["BonusTypeSpec"]["Id"]] = data["BonusTypeSpec"]
            name = data.get("TemplateSpec", {}).get("TemplateName")
            if name:
                self.templates[name] = data
        self.suffix = "." + faction

    # --- buildings ---------------------------------------------------------------------------------------------------

    def template(self, name):
        """A template by full name, or by base name with this faction's suffix."""
        return self.templates.get(name) or self.templates[name + self.suffix]

    def has(self, name):
        return name in self.templates or name + self.suffix in self.templates

    def cost(self, name):
        return {c["Id"]: c["Amount"] for c in self.template(name).get("BuildingSpec", {}).get("BuildingCost", [])}

    def science(self, name):
        return self.template(name).get("BuildingSpec", {}).get("ScienceCost", 0)

    def workers(self, name):
        return self.template(name).get("WorkplaceSpec", {}).get("MaxWorkers", 0)

    def seats(self, name):
        return self.template(name).get("EnterableSpec", {}).get("CapacityFinished", 0)

    def recipes_of(self, name):
        return list(self.template(name).get("ManufactorySpec", {}).get("ProductionRecipeIds", []))

    def buildings(self):
        """Names of every template this faction can place (its Buildings collection)."""
        want = "Buildings." + self.faction
        names = []
        for data in self.files.values():
            col = data.get("TemplateCollectionSpec")
            if col and col.get("CollectionId") == want:
                names += [path.rsplit("/", 1)[-1].replace(".blueprint", "") for path in col.get("Blueprints", [])]
        return [n for n in names if n in self.templates]

    # --- recipes -----------------------------------------------------------------------------------------------------

    def recipe(self, rid):
        r = self.recipes[rid]
        return {
            "id": rid,
            "hours": r["CycleDurationInHours"],
            "in": {i["Id"]: i["Amount"] for i in r.get("Ingredients", [])},
            "out": {p["Id"]: p["Amount"] for p in r.get("Products", [])},
            "science": r.get("ProducedSciencePoints", 0),
            "fuel": r.get("Fuel") or None,
            "cycles_per_fuel": r.get("CyclesFuelLasts", 0),
            "fuel_cap": r.get("FuelCapacity", 0),
            "shelf": r.get("CyclesCapacity", 0),
        }

    def weight(self, good):
        return self.goods[good].get("Weight", 1) if good in self.goods else 1

    # --- needs -------------------------------------------------------------------------------------------------------

    def need(self, nid):
        n = self.needs[nid]
        return {"id": nid, "group": n.get("NeedGroupId"), "daily": n.get("DailyDelta", 0.0),
                "wellbeing": n.get("FavorableWellbeing", 0), "wastable": n.get("Wastable", True),
                "importance": n.get("ImportanceMultiplier", 1.0)}

    def faction_needs(self):
        """Need ids in this faction's need collections plus Common."""
        ids = []
        wanted = {"Needs." + self.faction, "Common", "Needs.Common", self.faction}
        for data in self.files.values():
            col = data.get("NeedCollectionSpec")
            if col and col.get("CollectionId") in wanted:
                ids += col.get("Needs", [])
        return [i for i in dict.fromkeys(ids) if i in self.needs]

    # --- plants ------------------------------------------------------------------------------------------------------

    def plant(self, name):
        t = self.templates.get(name) or self.templates[name + self.suffix]
        cut = t.get("CuttableSpec", {}).get("Yielder", {})
        gather = t.get("GatherableSpec", {}).get("Yielder", {})
        return {
            "name": name,
            "group": t.get("PlantableSpec", {}).get("ResourceGroup"),
            "plant_h": t.get("PlantableSpec", {}).get("PlantTimeInHours", 0.0),
            "grow_d": t.get("GrowableSpec", {}).get("GrowthTimeInDays", 0.0),
            "cut": (cut.get("Yield", {}).get("Id"), cut.get("Yield", {}).get("Amount", 0)) if cut else None,
            "cut_h": cut.get("RemovalTimeInHours", 0.0) if cut else 0.0,
            "gather": (gather.get("Yield", {}).get("Id"), gather.get("Yield", {}).get("Amount", 0)) if gather else None,
            "gather_h": gather.get("RemovalTimeInHours", 0.0) if gather else 0.0,
            "regrow_d": t.get("GatherableSpec", {}).get("YieldGrowthTimeInDays", 0.0),
            "dry_d": t.get("WateredNaturalResourceSpec", {}).get("DaysToDieDry"),
            "wet_d": t.get("AridNaturalResourceSpec", {}).get("DaysToDieWet"),
            "flood_d": t.get("FloodableNaturalResourceSpec", {}).get("DaysToDie"),
        }
