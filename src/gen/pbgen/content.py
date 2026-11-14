"""Goods, needs, recipes and plants: each "a vanilla basis + named fields", plus their collections.

Shorthand fields map to spec paths (tables below); `set` reaches any other field; `add` adds whole specs the basis lacks;
`delete` removes keys. Loc comes from catalogue/text/<kind>.json by id. Icons follow the naming rule
Sprites/Pandaborn/<Goods|Plants|Buildings>/<Id>Icon(.png) in mod/PandabornFactions, else the basis icon is kept and the
report says so.
"""
import os

from . import models as model_adopter
from .util import GenError, load_json

# shorthand -> (dotted path, transform). Transforms: None (as is), "amounts" ({Good: n} -> [{Id, Amount}]),
# "effects" ({Need: points} -> [{NeedId, Points}]), "yield" ({Good: n} -> {Id, Amount}).
GOOD_FIELDS = {
    "good_type": ("GoodSpec.GoodType", None), "weight": ("GoodSpec.Weight", "int"),
    "group": ("GoodSpec.GoodGroupId", None), "order": ("GoodSpec.GoodOrder", "int"),
    "consumption": ("GoodSpec.ConsumptionEffects", "effects"),
}
NEED_FIELDS = {
    "group": ("NeedSpec.NeedGroupId", None), "daily_delta": ("NeedSpec.DailyDelta", "float"),
    "favorable_wellbeing": ("NeedSpec.FavorableWellbeing", "int"),
    "unfavorable_wellbeing": ("NeedSpec.UnfavorableWellbeing", "int"),
    "importance": ("NeedSpec.ImportanceMultiplier", "float"), "starting_value": ("NeedSpec.StartingValue", "float"),
    "maximum": ("NeedSpec.MaximumValue", "float"), "wastable": ("NeedSpec.Wastable", "bool"),
    "order": ("NeedSpec.Order", "int"),
}
RECIPE_FIELDS = {
    "cycle_hours": ("RecipeSpec.CycleDurationInHours", "float"), "ingredients": ("RecipeSpec.Ingredients", "amounts"),
    "products": ("RecipeSpec.Products", "amounts"), "fuel": ("RecipeSpec.Fuel", None),
    "cycles_fuel_lasts": ("RecipeSpec.CyclesFuelLasts", "int"), "fuel_capacity": ("RecipeSpec.FuelCapacity", "int"),
    "capacity": ("RecipeSpec.CyclesCapacity", "int"), "science": ("RecipeSpec.ProducedSciencePoints", "int"),
}
PLANT_FIELDS = {
    "growth_days": ("GrowableSpec.GrowthTimeInDays", "float"), "plant_hours": ("PlantableSpec.PlantTimeInHours", "float"),
    "planter": ("PlantableSpec.ResourceGroup", None),
    "cut_yield": ("CuttableSpec.Yielder.Yield", "yield"), "cut_hours": ("CuttableSpec.Yielder.RemovalTimeInHours", "float"),
    "gather_yield": ("GatherableSpec.Yielder.Yield", "yield"),
    "gather_hours": ("GatherableSpec.Yielder.RemovalTimeInHours", "float"),
    "gather_days": ("GatherableSpec.YieldGrowthTimeInDays", "float"),
    "dry_days": ("WateredNaturalResourceSpec.DaysToDieDry", "float"),
    "wet_days": ("AridNaturalResourceSpec.DaysToDieWet", "float"),
    "flood_min": ("FloodableNaturalResourceSpec.MinWaterHeight", "int"),
    "flood_max": ("FloodableNaturalResourceSpec.MaxWaterHeight", "int"),
    "flood_days": ("FloodableNaturalResourceSpec.DaysToDie", "float"),
    "reproduction": ("ReproducibleSpec.ReproductionChance", "float"),
    "demolish_hours": ("DemolishableSpec.DemolishTimeInHours", "float"),
}
COMMON_FIELDS = {"basis", "text", "icon", "set", "add", "delete", "aliases", "note", "src", "when_poles", "path", "not_in_sheet",
                 "waits_for",
                 "name", "template", "standin", "models"}
ICON_DIRS = {"good": "Goods", "plant": "Plants", "building": "Buildings"}


def stem(i):
    return i[len("Pandaborn"):] if i.startswith("Pandaborn") else i


def transform(value, how, item, field):
    if how is None:
        return value
    if how == "int":
        if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value:
            raise GenError("%s: %s must be a whole number, got %r" % (item, field, value))
        return int(value)
    if how == "float":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise GenError("%s: %s must be a number, got %r" % (item, field, value))
        return float(value)
    if how == "bool":
        if not isinstance(value, bool):
            raise GenError("%s: %s must be true or false" % (item, field))
        return value
    if how == "amounts":
        return [{"Id": g, "Amount": transform(a, "int", item, field)} for g, a in value.items()]
    if how == "effects":
        return [{"NeedId": n, "Points": transform(p, "float", item, field)} for n, p in value.items()]
    if how == "yield":
        if len(value) != 1:
            raise GenError("%s: %s takes exactly one good, e.g. { Log = 2 }" % (item, field))
        (g, a), = value.items()
        return {"Id": g, "Amount": transform(a, "int", item, field)}
    raise GenError("internal: unknown transform " + how)


def put(data, path, value, item, field, create=False):
    parts = path.split(".")
    node = data
    for p in parts[:-1]:
        if p not in node:
            if not create:
                raise GenError("%s: %s needs %s on the basis, which has none (add it with `add`)"
                               % (item, field, ".".join(parts[:parts.index(p) + 1])))
            node[p] = {}
        node = node[p]
    node[parts[-1]] = value


def apply_fields(gen, data, entry, table, item, allowed_extra=()):
    unknown = set(entry) - set(table) - COMMON_FIELDS - set(allowed_extra)
    if unknown:
        raise GenError("%s: unknown field(s) %s. Known: %s" % (item, ", ".join(sorted(unknown)),
                                                              ", ".join(sorted(set(table) | COMMON_FIELDS))))
    for spec, body in (entry.get("add") or {}).items():
        if spec in data:
            raise GenError("%s: add %s: the basis already has it; use set or the shorthand fields" % (item, spec))
        data[spec] = body
    for path in entry.get("delete") or []:
        gen.apply_delete(data, [path], item)
    for field, (path, how) in table.items():
        if field in entry:
            value = transform(entry[field], how, item, field)
            if how in ("amounts", "yield") or (how is None and path.endswith(("Fuel",))):
                value = gen.sub_goods(value)
            put(data, path, value, item, field)
    gen.apply_set(data, entry.get("set"), item)


def find_icon(gen, kind, ident, explicit):
    if explicit:
        return explicit
    folder = ICON_DIRS[kind]
    for name in (ident, ident + "s"):
        rel = "Sprites/Pandaborn/%s/%sIcon" % (folder, name)
        png = os.path.join(gen.mod_src, *rel.split("/")) + ".png"
        if os.path.isfile(png):
            # The game makes a Sprite of any PNG asked for as one (ModSpriteConverter); "isSprite" is only a texture
            # preset. Goods icons carry mipmap settings instead (drawn small in the world; BerryJam does the same).
            # Either kind of meta is accepted; a bare PNG is not (same rule as tools/validate.py).
            try:
                meta = load_json(png + ".meta.json")
            except (OSError, ValueError):
                meta = {}
            if meta.get("isSprite") is True or meta.get("generateMipmap") is True:
                return rel
            gen.note("icons", "%s.png exists but has no usable .meta.json ({\"isSprite\": true}, or mipmap settings "
                              "for goods icons); using the basis icon until the icon pipeline writes it" % rel)
            return None
    return None


# ------------------------------------------------------------------------------------------------------ goods
def gen_goods(gen):
    cat = gen.cat["goods"]
    goods = cat.get("goods") or {}
    text = gen.cat.text_by_id("goods")
    coll = cat.get("collection") or {}
    members = list(coll.get("vanilla") or [])
    for gid, g in goods.items():
        item = gen.cat.where("goods", "goods." + gid)
        if gen.skip_for_module("good", gid, g):
            continue
        if g.get("when_poles") and g["when_poles"] != gen.pole_mode:
            continue
        key = gen.v.ids["GoodSpec"].get(g.get("basis"))
        if key is None:
            raise GenError("%s: basis %r is not a vanilla good id" % (item, g.get("basis")))
        data = gen.v.copy(key)
        gs = data["GoodSpec"]
        gs["Id"] = gid
        gs["BackwardCompatibleIds"] = list(g.get("aliases") or [])
        apply_fields(gen, data, g, GOOD_FIELDS, item)
        t = text.get(g.get("text") or gid)
        if not t:
            raise GenError("%s: no entry with id %s in text/goods.json" % (item, g.get("text") or gid))
        k1, k2 = "Pandaborn.Good.%s.DisplayName" % stem(gid), "Pandaborn.Good.%s.PluralDisplayName" % stem(gid)
        gen.add_loc("Goods", k1, t["singular"], t.get("translator_comment"), item)
        gen.add_loc("Goods", k2, t["plural"], t.get("translator_comment"), item)
        gs["DisplayNameLocKey"], gs["PluralDisplayNameLocKey"] = k1, k2
        gen.good_plural[gid] = k2
        icon = find_icon(gen, "good", gid, g.get("icon"))
        if icon:
            gs["Icon"] = icon
        else:
            gen.note(item, "no icon Sprites/Pandaborn/Goods/%sIcon; keeps the %s icon" % (gid, g["basis"]))
        gen.good_icon[gid] = gs["Icon"]
        gen.add_id("good", gid, item)
        gen.emit("Goods/Pandaborn/Good.%s" % gid, data, item, "good", key)
        members.append(gid)
    if coll.get("id"):
        gen.add_id("collection", coll["id"], "catalogue/goods.toml [collection]")
        gen.emit("GoodCollections/Pandaborn/GoodCollection.%s" % coll["id"],
                 {"GoodCollectionSpec": {"CollectionId": coll["id"], "Goods": members}},
                 "catalogue/goods.toml [collection]", "collection")
        gen.generated_collections["good"].add(coll["id"])


# ------------------------------------------------------------------------------------------------------ needs
def gen_needs(gen):
    cat = gen.cat["needs"]
    needs = cat.get("needs") or {}
    text = gen.cat.text_by_id("needs")
    coll = cat.get("collection") or {}
    members = list(coll.get("vanilla") or [])
    for nid, n in needs.items():
        item = gen.cat.where("needs", "needs." + nid)
        if gen.skip_for_module("need", nid, n):
            continue
        key = gen.v.ids["NeedSpec"].get(n.get("basis"))
        if key is None:
            raise GenError("%s: basis %r is not a vanilla need id" % (item, n.get("basis")))
        data = gen.v.copy(key)
        ns = data["NeedSpec"]
        ns["Id"] = nid
        ns["BackwardCompatibleIds"] = list(n.get("aliases") or [])
        apply_fields(gen, data, n, NEED_FIELDS, item, allowed_extra=("name_from",))
        # the name: own text, a good's plural name, or a building's name
        how = n.get("name_from", "own")
        if how == "own":
            t = text.get(n.get("text") or nid)
            if not t:
                raise GenError("%s: no entry with id %s in text/needs.json" % (item, n.get("text") or nid))
            k = "Pandaborn.Need.%s.DisplayName" % stem(nid)
            gen.add_loc("Needs", k, t["name"], t.get("translator_comment") or t.get("tooltip"), item)
            ns["DisplayNameLocKey"] = k
        elif how.startswith("good:"):
            g = how[5:]
            if g not in gen.good_plural:
                raise GenError("%s: name_from %s: no such generated good" % (item, how))
            ns["DisplayNameLocKey"] = gen.good_plural[g]
        elif how.startswith("building:"):
            b = how[9:]
            k = gen.building_name_key.get(b)
            if not k:
                raise GenError("%s: name_from %s: no such generated building (or it has no name)" % (item, how))
            ns["DisplayNameLocKey"] = k
        elif how.startswith("key:"):
            ns["DisplayNameLocKey"] = how[4:]
        else:
            raise GenError("%s: name_from must be own, good:<id>, building:<id> or key:<loc key>" % item)
        gen.add_id("need", nid, item)
        gen.emit("Needs/Pandaborn/Need.%s" % nid, data, item, "need", key)
        members.append(nid)
    if coll.get("id"):
        gen.add_id("collection", coll["id"], "catalogue/needs.toml [collection]")
        gen.emit("NeedCollections/Pandaborn/NeedCollection.%s" % coll["id"],
                 {"NeedCollectionSpec": {"CollectionId": coll["id"], "Needs": members}},
                 "catalogue/needs.toml [collection]", "collection")
        gen.generated_collections["need"].add(coll["id"])


# ---------------------------------------------------------------------------------------------------- recipes
def gen_recipes(gen):
    recipes = gen.cat["recipes"].get("recipes") or {}
    for rid, r in recipes.items():
        item = gen.cat.where("recipes", "recipes." + rid)
        if gen.skip_for_module("recipe", rid, r):
            continue
        key = gen.v.ids["RecipeSpec"].get(r.get("basis"))
        if key is None:
            raise GenError("%s: basis %r is not a vanilla recipe id" % (item, r.get("basis")))
        data = gen.v.copy(key)
        rs = data["RecipeSpec"]
        rs["Id"] = rid
        rs["BackwardCompatibleIds"] = list(r.get("aliases") or [])
        apply_fields(gen, data, r, RECIPE_FIELDS, item, allowed_extra=("display",))
        products = [p["Id"] for p in rs.get("Products") or []]
        # name and icon follow the first product, as vanilla does
        if "display" in r:
            rs["DisplayLocKey"] = r["display"]
        elif products and products[0] in gen.good_plural:
            rs["DisplayLocKey"] = gen.good_plural[products[0]]
        elif products:
            vk = gen.v.ids["GoodSpec"].get(products[0])
            if vk:
                rs["DisplayLocKey"] = gen.v.get(vk)["GoodSpec"]["PluralDisplayNameLocKey"]
        if products:
            if products[0] in gen.good_icon:
                rs["Icon"] = gen.good_icon[products[0]]
            elif gen.v.ids["GoodSpec"].get(products[0]):
                rs["Icon"] = gen.v.get(gen.v.ids["GoodSpec"][products[0]])["GoodSpec"]["Icon"]
        gen.add_id("recipe", rid, item)
        gen.emit("Recipes/Pandaborn/Recipe.%s" % rid, data, item, "recipe", key)


# ----------------------------------------------------------------------------------------------------- plants
def gen_plants(gen):
    cat = gen.cat["plants"]
    plants = cat.get("plants") or {}
    text = gen.cat.text_by_id("plants")
    coll = cat.get("collection") or {}
    members = []
    for v in coll.get("vanilla") or []:
        members.append(gen.v.rel(gen.vanilla_template_key(v, "catalogue/plants.toml [collection]")))
    for pid, p in plants.items():
        item = gen.cat.where("plants", "plants." + pid)
        if gen.skip_for_module("template", (p.get("template") or pid + gen.suffix), p):
            continue
        key = gen.vanilla_template_key(p.get("basis", ""), item)
        data = gen.v.copy(key)
        template = p.get("template") or pid + gen.suffix
        gen.set_template(data, template, p.get("aliases"), item)
        if "wet_days" in p:   # the arid rule: dies on moist soil instead of dry soil
            data.pop("WateredNaturalResourceSpec", None)
            data.setdefault("AridNaturalResourceSpec", {})
        apply_fields(gen, data, p, PLANT_FIELDS, item, allowed_extra=("model",))
        gen.apply_models(data, p.get("models"), item)
        if p.get("model"):
            model_adopter.apply_plant_model(gen, data, p["model"], item)
        t = text.get(p.get("text") or pid)
        les = data.get("LabeledEntitySpec")
        if t and les is not None:
            for field, spec_field, suffix in (("name", "DisplayNameLocKey", "DisplayName"),
                                              ("description", "DescriptionLocKey", "Description"),
                                              ("flavor", "FlavorDescriptionLocKey", "FlavorDescription")):
                if t.get(field):
                    k = "Pandaborn.NaturalResource.%s.%s" % (stem(pid), suffix)
                    gen.add_loc("Plants", k, t[field], t.get("translator_comment"), item)
                    les[spec_field] = k
        elif not t:
            raise GenError("%s: no entry with id %s in text/plants.json" % (item, p.get("text") or pid))
        icon = find_icon(gen, "plant", pid, p.get("icon"))
        if icon and les is not None:
            les["Icon"] = icon
        elif not icon:
            gen.note(item, "no icon Sprites/Pandaborn/Plants/%sIcon; keeps the basis icon" % pid)
        if not p.get("model"):
            gen.note(item, "stand-in on %s; growth-stage models to come"
                     % gen.v.get(key)["TemplateSpec"]["TemplateName"])
        kind = gen.v.rel(key).split("/")[1] if gen.v.rel(key).startswith("NaturalResources/") else "Plants"
        members.append(gen.emit("NaturalResources/Pandaborn/%s/%s/%s" % (kind, pid, template), data, item, "plant", key))
    if coll.get("id"):
        gen.collections[coll["id"]] = members
