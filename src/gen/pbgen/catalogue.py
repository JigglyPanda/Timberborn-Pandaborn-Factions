"""Loads catalogue/*.toml and catalogue/text/*.json and checks their shape. Unknown fields are errors: a typo must not
silently become "use the vanilla value"."""
import os
import tomllib

from .util import GenError, load_json

# allowed fields per item kind; anything else is an error
BUILDING_FIELDS = {
    "basis", "archetype", "vanilla", "text", "template", "cost", "science", "workers", "default_workers", "worker_type",
    "disallow_other_workers", "recipes", "capacity", "tool_group", "tool_order", "models", "icon", "retire", "aliases",
    "set", "delete", "standin", "needs_code", "note", "retire_when", "path", "needs_map", "add", "src", "effects", "model", "waits_for", "module_specs",
}
CHARACTER_FIELDS = {"basis", "template", "path", "models", "set", "note", "name_pool", "module_specs", "aliases", "add"}
GOOD_FIELDS = {"basis", "vanilla", "text", "icon", "weight", "good_type", "group", "order", "consumption", "set",
               "delete", "aliases", "note", "provenance", "container", "path"}
NEED_FIELDS = {"basis", "vanilla", "text", "group", "daily_delta", "favorable_wellbeing", "unfavorable_wellbeing",
               "importance", "starting_value", "set", "delete", "aliases", "note", "provenance", "collection", "path"}
RECIPE_FIELDS = {"basis", "text", "cycle_hours", "ingredients", "products", "fuel", "cycles_fuel_lasts", "capacity",
                 "set", "delete", "aliases", "note", "provenance", "path"}
PLANT_FIELDS = {"basis", "archetype", "text", "template", "planter", "growth_days", "yield", "gatherable",
                "dry_days", "flood", "models", "icon", "set", "delete", "aliases", "note", "provenance", "path"}

FILES = ("rules", "faction", "buildings", "building_stats", "goods", "needs", "recipes", "plants", "archetypes", "modifiers",
         "tutorial")
TEXT_FILES = ("buildings", "goods", "needs", "plants", "faction", "messages", "names", "tutorial")


def _load_toml(path):
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise GenError("%s: %s" % (path, e)) from None


class Catalogue:
    def __init__(self, root):
        self.root = root
        self.data = {}
        for name in FILES:
            p = os.path.join(root, name + ".toml")
            self.data[name] = _load_toml(p) if os.path.isfile(p) else {}
        self.text = {}
        tdir = os.path.join(root, "text")
        for name in TEXT_FILES:
            p = os.path.join(tdir, name + ".json")
            self.text[name] = load_json(p) if os.path.isfile(p) else {}
        self._check()

    def __getitem__(self, name):
        return self.data[name]

    def where(self, file, key):
        return "catalogue/%s.toml [%s]" % (file, key)

    def _check(self):
        for bid, b in (self.data["buildings"].get("buildings") or {}).items():
            _fields(b, BUILDING_FIELDS, self.where("buildings", "buildings." + bid))
        for cid, c in (self.data["faction"].get("characters") or {}).items():
            _fields(c, CHARACTER_FIELDS, self.where("faction", "characters." + cid))
        # goods, needs, recipes and plants are checked field by field in pbgen/content.py

    # ---------------------------------------------------------------------------------------------- text lookup
    def text_items(self, kind):
        return (self.text.get(kind) or {}).get("items") or {}

    def text_by_id(self, kind):
        out = {}
        for english, entry in self.text_items(kind).items():
            if isinstance(entry, dict) and entry.get("id"):
                if entry["id"] in out:
                    raise GenError("text/%s.json: id %s is used by two entries (%s, %s)"
                                   % (kind, entry["id"], out[entry["id"]]["_english"], english))
                e = dict(entry)
                e["_english"] = english
                out[entry["id"]] = e
        return out


def _fields(item, allowed, where):
    if not isinstance(item, dict):
        raise GenError("%s: expected a table, got %r" % (where, item))
    unknown = sorted(set(item) - allowed)
    if unknown:
        raise GenError("%s: unknown field(s) %s. Allowed: %s" % (where, ", ".join(unknown), ", ".join(sorted(allowed))))
