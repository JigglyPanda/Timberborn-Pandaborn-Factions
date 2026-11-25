"""Chains: what a good costs in land, labour and science, and what each need costs to switch on.

Everything is walked from the blueprints: a good comes from a recipe in some building, or from a plant that some
planter building tends; a need is met by a good's consumption effect, an attraction or a decoration.
"""
from . import mech


def producers(game):
    """{good: [(building, recipe id)]} over the faction's own buildings."""
    found = {}
    for b in game.buildings():
        for rid in game.recipes_of(b):
            for good in game.recipe(rid)["out"]:
                found.setdefault(good, []).append((b, rid))
    return found


def plants(game):
    """{good: (plant template, 'cut' | 'gather')} over the faction's plants (the Common ones included)."""
    wanted = {"NaturalResources." + game.faction, "NaturalResources.Common", "Common"}
    names = []
    for data in game.files.values():
        col = data.get("TemplateCollectionSpec")
        if col and col.get("CollectionId") in wanted:
            names += [p.rsplit("/", 1)[-1].replace(".blueprint", "") for p in col.get("Blueprints", [])]
    found = {}
    for name in names:
        if name not in game.templates or "PlantableSpec" not in game.templates[name]:
            continue
        p = game.plant(name)
        for how in ("cut", "gather"):
            if p[how] and p[how][0] and p[how][0] not in found:
                found[p[how][0]] = (name, how)
    return found


def planter(game, group):
    for b in game.buildings():
        if game.templates[b].get("PlanterBuildingSpec", {}).get("PlantableResourceGroup") == group:
            return b
    return None


def chain(game, good, _seen=()):
    """How one unit of `good` is made: {'tile_days', 'hours' (work at speed 1), 'science' (set of buildings),
    'needs' (fuel, power)} per unit. Raw wild goods (logs, berries, water) cost nothing here."""
    made, grown = producers(game), plants(game)
    if good in grown and good not in ("Log",):
        name, how = grown[good]
        p = game.plant(name)
        amount = p[how][1]
        if how == "cut":
            tile_days = p["grow_d"] / amount
            hours = (p["plant_h"] + p["cut_h"] + 0.35) / amount            # 0.35 h: the walk out and back, 6 tiles
        else:
            tile_days = p["regrow_d"] / amount
            hours = (p["gather_h"] + 0.45) / amount
        house = planter(game, p["group"])
        return {"tile_days": tile_days, "hours": hours, "science": {house} if house else set(), "extras": set(),
                "dry": p["dry_d"], "plant": name}
    if good in made and good not in _seen:
        building, rid = made[good][0]
        r = game.recipe(rid)
        out = r["out"][good]
        total = {"tile_days": 0.0, "hours": r["hours"] / out, "science": {building}, "extras": set(), "dry": None,
                 "plant": None}
        if r["fuel"]:
            total["extras"].add("fuel")
        if game.templates[building].get("MechanicalNodeSpec", {}).get("PowerInput", 0) > 0 and \
                "WaterPoweredGeneratorSpec" not in game.templates[building]:
            total["extras"].add("power")
        for ingredient, amount in r["in"].items():
            part = chain(game, ingredient, _seen + (good,))
            total["tile_days"] += part["tile_days"] * amount / out
            total["hours"] += part["hours"] * amount / out
            total["science"] |= part["science"]
            total["extras"] |= part["extras"]
            if part["dry"] is not None:
                total["dry"] = part["dry"] if total["dry"] is None else min(total["dry"], part["dry"])
            total["plant"] = total["plant"] or part["plant"]
        return total
    return {"tile_days": 0.0, "hours": 0.0, "science": set(), "extras": set(), "dry": None, "plant": None}


def science_of(game, buildings):
    return sum(game.science(b) for b in buildings)


def foods(game):
    """Goods that feed Hunger, with the dish need each also fills."""
    out = {}
    for gid, g in game.goods.items():
        effects = {e["NeedId"]: e["Points"] for e in g.get("ConsumptionEffects", [])}
        if effects.get("Hunger"):
            dish = next((n for n in effects if n != "Hunger" and n in game.needs), None)
            out[gid] = dish
    return out


def unlock_set(game, building, _seen=frozenset()):
    """Every building whose science must be paid before `building` can be built and supplied: itself, and the
    makers of each good in its cost (gears, paper, cured poles...), and theirs."""
    if building in _seen:
        return set()
    seen = _seen | {building}
    need = {building}
    t = game.templates[building]
    goods = set(game.cost(building))
    goods |= {c["GoodId"] for c in t.get("GoodConsumingBuildingSpec", {}).get("ConsumedGoods", [])}
    for good in goods:
        for maker in chain(game, good)["science"]:
            need |= unlock_set(game, maker, seen)
    return need


def need_offers(game):
    """{need: (buildings to unlock, what gives it, Tradition level or 0)}: the cheapest way to switch each need on."""
    best = {}

    def offer(need, buildings, what, tradition=0):
        if need not in game.needs:
            return
        cost = science_of(game, buildings)
        if need not in best or (tradition, cost) < (best[need][2], science_of(game, best[need][0])):
            best[need] = (buildings, what, tradition)

    made, grown = producers(game), plants(game)
    for good, dish in foods(game).items():
        if dish and (good in made or good in grown):
            buildings = set()
            for b in chain(game, good)["science"]:
                buildings |= unlock_set(game, b)
            offer(dish, buildings, good)
    for b in game.buildings():
        t = game.templates[b]
        tradition = t.get("PandabornTraditionSpec", {}).get("Level", 0)
        effects = t.get("AttractionSpec", {}).get("Effects", []) +             t.get("ContinuousEffectBuildingSpec", {}).get("Effects", []) + t.get("DwellingSpec", {}).get("SleepEffects", [])
        for effect in effects:
            offer(effect["NeedId"], unlock_set(game, b), b, tradition)
    return best


def wellbeing_at(game, science, skip=(), tradition=0):
    """Wellbeing a colony can hold once it has earned `science`, buying the cheapest point first and paying each
    building's science once. Monuments, wonders, boosts and anything in `skip` are left out; basic needs count as
    met. Needs locked behind a Tradition level above `tradition` are left out too."""
    mine = set(game.faction_needs())
    total = sum(game.need(n)["wellbeing"] for n in mine if game.need(n)["group"] == "BasicNeeds")
    offers = {n: o for n, o in need_offers(game).items()
              if n in mine and n not in skip and o[2] <= tradition and game.need(n)["wellbeing"] > 0
              and game.need(n)["group"] not in ("BasicNeeds", "Awe", "Boosts")}
    owned, left, bought = set(), science, []
    while offers:
        price = {n: science_of(game, o[0] - owned) for n, o in offers.items()}
        need = min(offers, key=lambda n: (price[n] / game.need(n)["wellbeing"], price[n]))
        if price[need] > left:
            affordable = [n for n in offers if price[n] <= left]
            if not affordable:
                break
            need = min(affordable, key=lambda n: (price[n] / game.need(n)["wellbeing"], price[n]))
        left -= price[need]
        owned |= offers.pop(need)[0]
        total += game.need(need)["wellbeing"]
        bought.append(need)
    return total, bought


def labour_per_unit(game, kind, good, hours=16.0, wellbeing=20.0):
    """Worker-days (of this kind, on this working day) behind one unit of a material, mill and carrying included."""
    w = mech.Worker(game, kind, hours, wellbeing)
    c = chain(game, good)
    return c["hours"] / (w.on_post() * w.work_speed())
