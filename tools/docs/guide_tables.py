#!/usr/bin/env python3
"""Writes the generated blocks of docs/PLAYER_GUIDE.md from the catalogue.

    python -I tools/docs/guide_tables.py            # rewrite every block between its markers
    python -I tools/docs/guide_tables.py --check    # exit 1 if the guide is out of date (writes nothing)
    python -I tools/docs/guide_tables.py --stdout   # print the blocks, touch nothing

The guide's prose states rules; every cost, rate and count a balance pass may change sits in a block
`<!-- gen:NAME -->` ... `<!-- /gen:NAME -->` that this script fills. An item whose code module is off (or not in
src/code/modules.txt) is left out, as the build leaves it out.

Reads only catalogue/*.toml, catalogue/text/*.json and src/code/modules.txt. Writes only docs/PLAYER_GUIDE.md, and
only between markers. Output is deterministic: no dates, no absolute paths. Run it after any catalogue change.

Works on Python 3.11+ (tomllib) and on 3.10 with the tomli that pip vendors.
"""
import argparse
import io
import json
import os
import re
import sys

try:
    import tomllib as _toml
except ImportError:
    from pip._vendor import tomli as _toml

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
GUIDE = os.path.join(REPO, "docs", "PLAYER_GUIDE.md")
VANILLA_LIFT = 14          # a beaver's lifting capacity in the game, for comparison only
FULL_DAY = 16.0            # the game's default working day, the yardstick of the bell table

# Names of vanilla things the catalogue's text files leave to the game.
BUILDING_NAMES = {
    "WaterPump": "Water Pump", "GathererFlag": "Gatherer Flag", "LumberjackFlag": "Lumberjack Flag",
    "EfficientFarmHouse": "Farmhouse", "Inventor": "Inventor", "PowerWheel": "Power Wheel", "Forester": "Forester",
    "LumberMill": "Pole Mill", "PaperMill": "Paper Mill", "Campfire": "Campfire",
}
GOOD_NAMES = {   # plural, singular
    "Log": ("logs", "log"), "Plank": ("poles", "pole"), "TreatedPlank": ("cured poles", "cured pole"),
    "Gear": ("gears", "gear"), "MetalBlock": ("metal blocks", "metal block"), "ScrapMetal": ("scrap metal", "scrap metal"),
    "Paper": ("paper", "paper"), "Water": ("water", "water"), "Extract": ("extract", "extract"),
    "Fireworks": ("fireworks", "firework"), "Berries": ("berries", "berry"),
}
# What each water piece is for: structure, not numbers.
WATER_PIECES = [
    ("PandabornFlumeGate", "The intake of a line. Sets how much water enters and shuts itself when the water turns bad"),
    ("PandabornFlume", "One tile of aqueduct on the ground"),
    ("PandabornFlumeCorner", "A turn. Flumes do not bend on their own"),
    ("PandabornFlumeDrop", "Steps the line down one level"),
    ("PandabornFlumeBridge", "Carries the line above the ground on a trestle"),
    ("PandabornFlumeBridgeSpan", "A bridge piece that stands over another flume, so two lines can cross"),
    ("PandabornPaddySpout", "Keeps the field in front of it flooded to a shallow set depth"),
    ("PandabornScoopWheel", "Lifts water out of a current. No workers"),
    ("PandabornTreadwheelLift", "Lifts water where there is no current. Turned by a worker, so only during the working day"),
    ("PandabornCisternTap", "A worker pours stored water into a flume or a basin"),
    ("PandabornDewCollector", "A little drinking water with no workers, less in a drought"),
    ("PandabornTripHammerMill", "Pounds rice into rice flour. Its wheel stands in a flume or a stream; no power shafts"),
    ("PandabornDryStoneWall", "Stops moisture spreading sideways through the soil, to keep a tea slope dry"),
]
FIRST_DAYS = ["WaterPump", "GathererFlag", "LumberjackFlag", "EfficientFarmHouse", "Inventor", "PandabornDen",
              "PandabornHammock", "PowerWheel", "LumberMill", "Forester", "PandabornSteamer", "PandabornCisternSmall",
              "PandabornCisternMedium", "PandabornScoopWheel", "PandabornFlumeGate", "PandabornFlume",
              "PandabornMoonLoft", "PandabornNightBuildersPost"]
# (food good, where it comes from)
FOODS = [
    ("PandabornBambooShoots", "Farmhouse"), ("PandabornCabbage", "Farmhouse"),
    ("PandabornPersimmons", "Gatherer Flag"), ("PandabornBambooMushrooms", "Gatherer Flag"),
    ("PandabornSteamedShoots", "PandabornSteamer"), ("PandabornPickles", "PandabornPickleYard"),
    ("PandabornSteamedRice", "PandabornSteamer"), ("PandabornHotPot", "PandabornHotPotHall"),
    ("PandabornSweetRiceBalls", "PandabornKitchen"), ("PandabornBambooSeedCakes", "PandabornKitchen"),
]
# (building, need it meets, note)
AFTERNOON = [
    ("PandabornHammock", "PandabornNap", "One napper"),
    ("PandabornNapPlatform", "PandabornNap", "Several nappers; on the ground or on a roof"),
    ("PandabornTeahouse", "PandabornTea", "Needs roasted tea and water in stock"),
    ("PandabornSlideAndSwing", "PandabornPlay", ""),
    ("PandabornKindergarten", "PandabornCubWatching", ""),
    ("PandabornInkStudio", "PandabornContemplation", ""),
    ("PandabornHotSpringBath", "PandabornSoak", "Uses water; wets the fur"),
    ("PandabornOperaStage", "PandabornPerformance", ""),
]
NIGHT_POSTS = [
    ("PandabornNightBuildersPost", "Ringtail builders stock and raise construction sites through the night"),
    ("PandabornNightCourierPost", "Ringtail couriers refill workshops and clear their outputs and the flags overnight"),
    ("PandabornNightForagersPost", "Ringtail gatherers forage at night: whatever a Gatherer Flag would pick in its range"),
    ("PandabornStarTower", "Ringtail stargazers make science from the night sky"),
]
MONUMENTS = [("PandabornMemorialArch", "PandabornMemorialArch"), ("PandabornGreatSittingPanda", "PandabornGreatSittingPanda"),
             ("PandabornSkyLantern", "PandabornSkyLantern")]


def load_toml(name):
    with open(os.path.join(REPO, "catalogue", name + ".toml"), "rb") as f:
        return _toml.loads(f.read().decode("utf-8"))


def load_text(name):
    p = os.path.join(REPO, "catalogue", "text", name + ".json")
    if not os.path.isfile(p):
        return {}
    with io.open(p, encoding="utf-8") as f:
        items = json.load(f).get("items", {})
    by_id = {}
    for v in (items.values() if isinstance(items, dict) else items):
        if isinstance(v, dict) and v.get("id"):
            by_id[v["id"]] = v
    return by_id


def num(x):
    """12.0 -> 12, 0.75 -> 0.75, 1200 -> 1,200."""
    if isinstance(x, float) and abs(x - round(x)) < 1e-9:
        x = int(round(x))
    if isinstance(x, int):
        return "{:,}".format(x)
    return ("%.2f" % x).rstrip("0").rstrip(".")


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "|".join(["---"] * len(head)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c).replace("|", "\\|") for c in r) + " |")
    return out


class Catalogue:
    def __init__(self):
        self.buildings = load_toml("buildings").get("buildings", {})
        self.stats = load_toml("building_stats").get("stats", {})
        self.goods = load_toml("goods").get("goods", {})
        self.needs = load_toml("needs").get("needs", {})
        self.plants = load_toml("plants").get("plants", {})
        self.recipes = load_toml("recipes").get("recipes", {})
        self.faction = load_toml("faction")
        self.rules = load_toml("rules")
        self.text_buildings = load_text("buildings")
        self.text_goods = load_text("goods")
        self.text_needs = load_text("needs")
        self.text_plants = load_text("plants")
        self.shipped = set()
        with io.open(os.path.join(REPO, "src", "code", "modules.txt"), encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    self.shipped.add(line.split()[0])

    # ---- switches
    def module_on(self, m):
        return bool(self.rules.get("modules", {}).get(m)) and m in self.shipped

    def visible(self, item):
        w = (item or {}).get("waits_for")
        if not w:
            return True
        return all(self.module_on(m) for m in ([w] if isinstance(w, str) else w))

    def has_building(self, bid):
        return bid in self.buildings and self.visible(self.buildings[bid])

    def has_good(self, gid):
        return gid not in self.goods or self.visible(self.goods[gid])

    def has_recipe(self, rid):
        r = self.recipes.get(rid)
        return bool(r) and self.visible(r) and all(self.has_good(g) for g in list(r.get("ingredients", {})) + list(r.get("products", {})))

    def module_spec(self, item, module, spec):
        """A spec the item carries only while its module is on."""
        if not self.module_on(module):
            return None
        return (item or {}).get("module_specs", {}).get(module, {}).get(spec)

    # ---- names
    def bname(self, bid):
        t = self.text_buildings.get(bid) or self.text_buildings.get(self.buildings.get(bid, {}).get("text", ""))
        if t and t.get("name"):
            return t["name"]
        if bid in BUILDING_NAMES:
            return BUILDING_NAMES[bid]
        s = bid[len("Pandaborn"):] if bid.startswith("Pandaborn") else bid
        return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", s)

    def gname(self, gid, n=2):
        """The good's name in running text: plural, or singular when n is 1."""
        if gid in GOOD_NAMES:
            return GOOD_NAMES[gid][0 if n != 1 else 1]
        t = self.text_goods.get(gid)
        if t and t.get("plural"):
            w = t["plural"] if n != 1 or not t.get("singular") else t["singular"]
            return w if w.startswith("Sichuan") else w[0].lower() + w[1:]
        s = gid[len("Pandaborn"):] if gid.startswith("Pandaborn") else gid
        return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", s).lower()

    def nname(self, nid):
        t = self.text_needs.get(nid)
        return (t or {}).get("name") or self.gname(nid)

    def pname(self, pid):
        t = self.text_plants.get(pid)
        return (t or {}).get("name") or self.gname(pid)

    def goods_list(self, d):
        return ", ".join("%s %s" % (num(n), self.gname(g, n)) for g, n in d.items()) if d else "free"

    def cost(self, bid):
        st = self.stats.get(bid)
        if st is None or "cost" not in st:
            return "as in the game"
        return self.goods_list(st["cost"])

    def price(self, bid):
        """Cost and science in one phrase."""
        sc = self.science(bid)
        if sc == "as in the game":
            return self.cost(bid)
        return "%s; %s" % (self.cost(bid), "no science" if sc == "none" else "%s science" % sc)

    def science(self, bid, free_word="none"):
        st = self.stats.get(bid)
        if st is None or "science" not in st:
            return "as in the game"
        return num(st["science"]) if st["science"] else free_word

    def wellbeing(self, nid):
        n = self.needs.get(nid)
        if not n or not self.visible(n) or "favorable_wellbeing" not in n:
            return None
        return n["favorable_wellbeing"]

    def fade_days(self, nid):
        n = self.needs.get(nid, {})
        d = abs(n.get("daily_delta", 0))
        return (1.0 / d) if d else None

    def recipe_line(self, rid):
        r = self.recipes[rid]
        ins = self.goods_list(r.get("ingredients", {})) if r.get("ingredients") else "nothing"
        outs = self.goods_list(r.get("products", {}))
        s = "%s \u2192 %s, %s h" % (ins, outs, num(r.get("cycle_hours", 0)))
        if r.get("fuel"):
            s += ", %s fuel" % self.gname(r["fuel"], 1)
        return s


def curve(points, hours):
    pts = sorted((p["Hours"], p["Bonus"]) for p in points)
    if not pts:
        return 0.0
    if hours <= pts[0][0]:
        return pts[0][1]
    if hours >= pts[-1][0]:
        return pts[-1][1]
    for (h0, b0), (h1, b1) in zip(pts, pts[1:]):
        if h0 <= hours <= h1:
            return b0 + (b1 - b0) * (hours - h0) / (h1 - h0)
    return 0.0


def fade_words(days):
    if days is None:
        return ""
    if days < 1.3:
        return "in about a day"
    return "in about %s days" % num(int(days + 0.5))


def build():
    c = Catalogue()
    adult = c.faction.get("characters", {}).get("adult", {})
    ring = c.faction.get("characters", {}).get("ringtail_adult", {})
    bot = c.faction.get("characters", {}).get("bot", {})
    B = {}

    # ------------------------------------------------------------------ switches
    marks = [("Bell", "The afternoon bell and the rested bonus"),
             ("Ringtails", "The Moon Loft, the Ringtails and the night posts"),
             ("Water", "Flumes, spouts, the scoop wheel, the cistern tap, dew, the trip-hammer mill"),
             ("Festival", "The Lantern Festival and Tradition"),
             ("Flowering", "The Great Flowering")]
    rows = [("**[%s]**" % m, what, "on" if c.module_on(m) else "**off**: its buildings and goods are left out of the build")
            for m, what in marks]
    B["switches"] = table(["Mark", "Feature", "In the catalogue as this page was generated"], rows)

    # ------------------------------------------------------------------ peoples
    lift_i = adult.get("set", {}).get("GoodCarrierSpec.BaseLiftingCapacity", VANILLA_LIFT)
    lift_r = ring.get("set", {}).get("GoodCarrierSpec.BaseLiftingCapacity", VANILLA_LIFT)
    lift_o = bot.get("set", {}).get("GoodCarrierSpec.BaseLiftingCapacity")
    ox_days = bot.get("set", {}).get("DeteriorableSpec.DeteriorationInDays")
    B["lifts"] = ["A beaver lifts %s. An Inkpaw lifts %s." % (num(VANILLA_LIFT), num(lift_i))]
    ring_rested = "Bell" in ring.get("module_specs", {}) and c.module_on("Bell")
    rows = [("Hours", "Dawn to the bell", "The bell to dawn"),
            ("Lifts", num(lift_i), num(lift_r)),
            ("Walking with a load", "Slower, as in the game", "Full speed"),
            ("Rested bonus", "From the length of the day", "From the length of the night shift"),
            ("Young", "Cubs, born in homes", "Kits, raised in Moon Lofts"),
            ("Food, water, well-being, lifespan", "The same", "The same")]
    B["peoples"] = table(["", "Inkpaw", "Ringtail"], rows)
    if not ring_rested:
        B["peoples"] += ["", "*The Ringtails' rested bonus was decided on 2026-11-25. The catalogue did not carry it yet "
                             "when this page was generated: until it does, only Inkpaws are rested.*"]

    # ------------------------------------------------------------------ bell
    spec = c.module_spec(adult, "Bell", "PandabornBellSpec") or {}
    work, walk = spec.get("WorkingSpeedCurve", []), spec.get("MovementSpeedCurve", [])
    if work:
        rows, worst = [], 0.0
        for h in (10, 11, 12, 13, 14, 15, 16, 18):
            b = curve(work, h)
            rel = h * (1 + b) / FULL_DAY
            if 12 <= h <= 16:
                worst = max(worst, abs(rel - 1))
            rows.append(("%d hours" % h, "+%s%%" % num(round(b * 100, 1)) if b else "none", "%d%%" % round(rel * 100)))
        B["bell"] = table(["Working day", "Rested bonus", "Work done in the day, against a plain 16-hour day"], rows)
        if [(p["Hours"], p["Bonus"]) for p in work] != [(p["Hours"], p["Bonus"]) for p in walk]:
            B["bell"] += ["", "Walking speed follows its own curve in the catalogue; the table shows working speed."]
        if worst > 0.012:
            B["bell"] += ["", "*The decided curve gives the same work at every length from 12 to 16 hours. The "
                              "catalogue's curve was still a little off that when this page was generated.*"]
    else:
        B["bell"] = ["*The bell is switched off in this build: working hours behave as in the plain game.*"]

    # ------------------------------------------------------------------ first days
    rows = []
    for bid in FIRST_DAYS:
        if not c.has_building(bid):
            continue
        st = c.stats.get(bid, {})
        extra = "%s water" % num(st["capacity"]) if "capacity" in st else ""
        rows.append((c.bname(bid), c.cost(bid), c.science(bid), extra))
    B["first_days"] = table(["Building", "Cost", "Science to unlock", "Holds"], rows)

    # ------------------------------------------------------------------ shelves
    sh = c.rules.get("shelves", {})
    if sh.get("workshop_hours"):
        line = "A workshop that turns ingredients into goods holds inputs and outputs for %s hours of work at full staffing." % num(sh["workshop_hours"])
        if sh.get("no_ingredient_hours"):
            line += " A pump holds what it would in the plain game."
        B["shelves"] = [line]
    else:
        B["shelves"] = ["Workshops hold what they would in the plain game."]

    # ------------------------------------------------------------------ the first drought
    out = []
    hold = sh.get("no_ingredient_hours")
    if hold:
        out.append("* A Water Pump holds about %s hours of its own pumping and then stops. It is not a store." % num(hold))
    cis = [(b, c.stats.get(b, {}).get("capacity")) for b in ("PandabornCisternSmall", "PandabornCisternMedium", "PandabornCisternLarge")]
    cis = [(b, n) for b, n in cis if n and c.has_building(b)]
    if cis:
        out.append("* Cisterns are the store: " + "; ".join("%s %s water (%s)" % (c.bname(b), num(n), c.price(b)) for b, n in cis) + ".")
    dry = [(c.pname(pid), p["dry_days"]) for pid, p in c.plants.items()
           if c.visible(p) and "PlantableSpec" not in p.get("delete", []) and "wet_days" not in p and not p.get("flood_min")]
    if dry:
        out.append("* Dry days a plant survives: " + ", ".join("%s %s" % (n.lower(), num(d)) for n, d in dry) + ". Tea and pepper need no water at all.")
    B["drought"] = out

    # ------------------------------------------------------------------ the rice chain
    rice = c.plants.get("PandabornRice", {})
    rows = []
    if rice and c.has_building("PandabornPaddyHouse"):
        rows.append(("Grow", "%s (%s), in a flooded field" % (c.bname("PandabornPaddyHouse"), c.price("PandabornPaddyHouse")),
                     "%s days to grow, %s a plant" % (num(rice.get("growth_days", 0)), c.goods_list(rice.get("cut_yield", {})))))
    if c.has_recipe("PandabornSteamedRice") and c.has_building("PandabornSteamer"):
        rows.append(("Steam", c.bname("PandabornSteamer"), c.recipe_line("PandabornSteamedRice")))
    if c.has_recipe("PandabornRiceFlour") and c.has_building("PandabornTripHammerMill"):
        rows.append(("Mill", "%s (%s), in a flume or a stream" % (c.bname("PandabornTripHammerMill"), c.price("PandabornTripHammerMill")),
                     c.recipe_line("PandabornRiceFlour")))
    if c.has_building("PandabornKitchen"):
        for rid in ("PandabornSweetRiceBalls", "PandabornBambooSeedCakes"):
            if c.has_recipe(rid):
                rows.append(("Cook", "%s (%s)" % (c.bname("PandabornKitchen"), c.price("PandabornKitchen")), c.recipe_line(rid)))
    B["rice"] = table(["Step", "Where", "Numbers"], rows) if rows else ["*Rice is not in this build.*"]

    # ------------------------------------------------------------------ plants
    def planter(p):
        if p.get("planter"):
            return p["planter"]
        return {"Carrot": "Farmhouse", "Cattail": "Paddy House"}.get(p.get("basis"), "Forester")
    rows = []
    for pid, p in c.plants.items():
        if not c.visible(p) or "PlantableSpec" in p.get("delete", []):
            continue
        land = "Dry" if "wet_days" in p else ("Flooded, shallow" if p.get("flood_min") else "Moist")
        ys = []
        if p.get("cut_yield"):
            ys.append("%s when %s" % (c.goods_list(p["cut_yield"]), "harvested" if p.get("basis") in ("Carrot", "Cattail") else "cut"))
        if p.get("gather_yield"):
            ys.append("%s every %s days while it stands" % (c.goods_list(p["gather_yield"]), num(p.get("gather_days", 0))))
        if "wet_days" in p:
            lasts = "about %s days with wet roots" % num(p["wet_days"])
        else:
            lasts = "%s dry day%s" % (num(p.get("dry_days", 0)), "" if p.get("dry_days") == 1 else "s")
        rows.append((c.pname(pid), land, planter(p), "%s days" % num(p.get("growth_days", 0)), "; ".join(ys), lasts))
    B["plants"] = table(["Plant", "Land", "Planted by", "Grows in", "Yield", "Survives"], rows)

    # ------------------------------------------------------------------ water
    if c.module_on("Water"):
        rows = [(c.bname(b), what, c.cost(b), c.science(b)) for b, what in WATER_PIECES if c.has_building(b)]
        out = table(["Piece", "What it does", "Cost", "Science to unlock"], rows)
        facts = []
        gate = c.module_spec(c.buildings.get("PandabornFlumeGate"), "Water", "PandabornFlumeGateSpec")
        if gate and c.has_building("PandabornFlumeGate"):
            facts.append("* **Flume Gate:** lets through %s m³/s to start, adjustable up to %s. It shuts itself when the water "
                         "behind it is %s%% badwater or more, and reopens when it is clean."
                         % (num(gate["DefaultFlow"]), num(gate["MaxFlow"]), num(gate["ContaminationShutoff"] * 100)))
        sp = c.buildings.get("PandabornPaddySpout", {}).get("set", {}).get("FillValveSpec.DefaultTargetHeightOffset")
        if sp and c.has_building("PandabornPaddySpout"):
            facts.append("* **Paddy Spout:** holds its field %s deep unless you change it." % num(sp))
        wh = c.buildings.get("PandabornScoopWheel", {}).get("set", {}).get("WaterPoweredGeneratorSpec", {})
        if wh and c.has_building("PandabornScoopWheel"):
            facts.append("* **Scoop Wheel:** starts turning in a current of %s. Its panel shows the current it has and the "
                         "current it wants." % num(wh.get("MinRequiredOutflow", 0)))
        dew = c.module_spec(c.buildings.get("PandabornDewCollector"), "Water", "PandabornDewLimiterSpec")
        if dew and c.has_building("PandabornDewCollector") and c.has_recipe("PandabornDewWater"):
            r = c.recipes["PandabornDewWater"]
            per_day = sum(r["products"].values()) * 24.0 / r["cycle_hours"]
            facts.append("* **Dew Collector:** %s water a day in fair weather, %s in a drought."
                         % (num(per_day), num(round(per_day * dew["DroughtEfficiency"], 1))))
        cis = [(b, c.stats.get(b, {}).get("capacity")) for b in ("PandabornCisternSmall", "PandabornCisternMedium", "PandabornCisternLarge")]
        cis = [(b, n) for b, n in cis if n and c.has_building(b)]
        if cis:
            facts.append("* **Cisterns:** " + "; ".join("%s holds %s water (%s)" % (c.bname(b), num(n), c.price(b)) for b, n in cis) + ".")
        B["water"] = out + [""] + facts
    else:
        B["water"] = ["*The water toolkit is switched off in this build. None of its pieces is in the toolbar.*"]

    # ------------------------------------------------------------------ tea
    out = []
    tea = c.plants.get("PandabornTeaBush", {})
    if tea and c.has_recipe("PandabornTea") and c.has_building("PandabornTeaRoastery") and c.has_building("PandabornTeahouse"):
        th = c.buildings["PandabornTeahouse"].get("add", {}).get("GoodConsumingBuildingSpec", {}).get("ConsumedGoods", [])
        used = " and ".join("%s %s" % (num(g["GoodPerHour"]), c.gname(g["GoodId"])) for g in th)
        rows = [("Grow", "Forester, on dry ground", "%s days to grow, then %s every %s days"
                 % (num(tea.get("growth_days", 0)), c.goods_list(tea.get("gather_yield", {})), num(tea.get("gather_days", 0)))),
                ("Pick", "Gatherer Flag", ""),
                ("Roast", "%s (%s)" % (c.bname("PandabornTeaRoastery"), c.price("PandabornTeaRoastery")),
                 c.recipe_line("PandabornTea")),
                ("Serve", "%s (%s)" % (c.bname("PandabornTeahouse"), c.price("PandabornTeahouse")),
                 ("Uses %s for each hour it is serving. Closed when it has none" % used) if used else "")]
        out = table(["Step", "Where", "Numbers"], rows)
    B["tea"] = out or ["*Tea is not in this build.*"]

    # ------------------------------------------------------------------ dishes
    rows = []
    for gid, where in FOODS:
        if gid not in c.goods or not c.has_good(gid):
            continue
        rid = gid if gid in c.recipes else None
        if rid and not c.has_recipe(rid):
            continue
        if where.startswith("Pandaborn"):
            if not c.has_building(where):
                continue
            where = c.bname(where)
        wb = c.wellbeing(gid)
        name = c.gname(gid)
        rows.append((name[0].upper() + name[1:], where, c.recipe_line(rid) if rid else "raw", "+%s" % num(wb) if wb else "none"))
    B["dishes"] = table(["Food", "From", "Recipe", "Well-being while the need is met"], rows)
    kitchens = [(b, c.buildings[b].get("recipes", [])) for b in ("PandabornSteamer", "PandabornPickleYard", "PandabornHotPotHall",
                                                               "PandabornKitchen", "PandabornTripHammerMill") if c.has_building(b)]
    B["dishes"] += ["", "Where they are cooked:", ""] + table(
        ["Building", "Cost", "Science to unlock"], [(c.bname(b), c.cost(b), c.science(b)) for b, _ in kitchens])
    if c.has_recipe("PandabornRiceFlour") and c.has_building("PandabornTripHammerMill"):
        B["dishes"] += ["", "Rice flour: " + c.recipe_line("PandabornRiceFlour") + ", at the Trip-Hammer Mill."]

    # ------------------------------------------------------------------ afternoon
    rows = []
    for bid, nid, note in AFTERNOON:
        if not c.has_building(bid) or c.wellbeing(nid) is None:
            continue
        rows.append((c.bname(bid), c.nname(nid), "+%s" % num(c.wellbeing(nid)), fade_words(c.fade_days(nid)),
                     c.price(bid), note))
    B["afternoon"] = table(["Place", "Need", "Well-being", "Fades from full", "Cost", "Notes"], rows)

    # ------------------------------------------------------------------ night posts
    if c.module_on("Ringtails"):
        out = []
        if c.has_building("PandabornMoonLoft"):
            out += ["Moon Loft: %s." % c.price("PandabornMoonLoft"), ""]
        rows = []
        for bid, what in NIGHT_POSTS:
            if not c.has_building(bid):
                continue
            st = c.stats.get(bid, {})
            rows.append((c.bname(bid), what, c.cost(bid), "up to %s" % num(st["workers"]) if st.get("workers") else ""))
        out += table(["Post", "What it does", "Cost", "Workers"], rows)
        if not c.has_building("PandabornStarTower"):
            out += ["", "*The Star Tower, a night post where Ringtail stargazers make science, is decided and modelled. "
                        "It keeps a science cost of its own. It was not in the build when this page was generated.*"]
        B["night_posts"] = out
    else:
        B["night_posts"] = ["*The Ringtails are switched off in this build. A Moon Loft is a plain home.*"]

    # ------------------------------------------------------------------ festival
    fs = c.module_spec(adult, "Festival", "PandabornFestivalSpec")
    if fs and c.has_building("PandabornFestivalSquare"):
        lan = c.gname(fs["LanternGoodId"])
        dishes = [c.gname(d) for d in fs.get("Dishes", []) if d in c.goods and c.has_good(d) and (d not in c.recipes or c.has_recipe(d))]
        out = ["Festival Square: %s." % c.price("PandabornFestivalSquare"), ""]
        out += table(["For", "In the district's storage"], [
            ("A Small Festival", "%s %s, and %s or more of each of %s different cooked dishes"
             % (num(fs["Lanterns"]), lan, num(fs["DishAmount"]), num(fs["DishKinds"]))),
            ("A Grand Festival", "The same, and %s %s" % (num(fs["Fireworks"]), c.gname(fs["FireworksGoodId"])))])
        out += ["", "Cooked dishes that count: %s. Raw food does not." % ", ".join(dishes)]
        if c.has_recipe("PandabornPaperLantern") and c.has_building("PandabornLanternWorkshop"):
            out += ["", "Paper lanterns: %s, at the %s (%s)." % (
                c.recipe_line("PandabornPaperLantern"), c.bname("PandabornLanternWorkshop"), c.price("PandabornLanternWorkshop"))]
            if c.has_recipe("PandabornPaper"):
                out += ["", "Paper: %s, at the Paper Mill." % c.recipe_line("PandabornPaper")]
        show = [("0", "It begins. Nobody works except the crews of pumps and lifts, so the village keeps its water"),
                ("Through the day", "Villagers eat, drink, nap and drift to the square to dance. Ringtails sleep through the morning as usual, then come"),
                (num(fs["ShowStartHours"]), "Everyone gathers at the square. Lanterns rise, %s of them" % num(fs["LanternRises"])),
                (num(fs["FireworksStartHours"]), "Fireworks, at a Grand Festival"),
                (num(fs["ShowEndHours"]), "The gathering ends"),
                ("Next dawn", "Work starts again. Tradition rises by one")]
        out += ["", "The day:", ""] + table(["Hours after dawn", "What happens"], show)
        wb, days = c.wellbeing(fs["FestiveNeedId"]), c.fade_days(fs["FestiveNeedId"])
        gwb = c.wellbeing(fs.get("GrandNeedId", ""))
        reward = "Festive spirit: +%s well-being for everyone, fading over about %s days." % (num(wb), num(round(days)))
        if gwb:
            reward += " A Grand Festival adds +%s." % num(gwb)
        out += ["", reward]
        trad = {}
        for bid, b in c.buildings.items():
            t = c.module_spec(b, "Festival", "PandabornTraditionSpec")
            if t and c.has_building(bid):
                trad.setdefault(t["Level"], []).append(c.bname(bid))
        if trad:
            out += ["", "What Tradition unlocks, at no science cost:", ""] + table(
                ["Tradition", "Decorations"], [(num(l), ", ".join(sorted(trad[l]))) for l in sorted(trad)])
        B["festival"] = out
    else:
        B["festival"] = ["*The Lantern Festival is switched off in this build. The Festival Square is not in the toolbar.*"]

    # ------------------------------------------------------------------ flowering
    fl = c.module_spec(adult, "Flowering", "PandabornFloweringSpec")
    if fl:
        species = [s.split(".")[0] for s in fl.get("Species", [])]
        rows = [("Never before cycle %s" % num(fl["FirstCycle"]), "Nothing"),
                ("Start of the cycle before", "The forecast: a notice, a line under the top bar, a line on every bamboo's panel"),
                ("Start of the flowering cycle", "Every grown plant of that bamboo, planted or wild, flowers. Young plants die"),
                ("The first %s days" % num(fl["SeedDays"]), "Flowering plants bear bamboo seed. Farmers or lumberjacks take it as their ordinary harvest"),
                ("Until day %s" % num(fl["DormantDays"]), "That bamboo rests. Planting marks stay and fields are replanted, but seedlings do not grow"),
                ("%s to %s cycles later" % (num(fl["NormalMinCycles"]), num(fl["NormalMaxCycles"])), "The next Flowering, of the other bamboo")]
        out = table(["When", "What happens"], rows)
        gaps = []
        for pid in species:
            p = c.plants.get(pid, {})
            twin = c.plants.get(pid + "InFlower", {})
            seed = sum(twin.get("cut_yield", {}).values())
            gaps.append((c.pname(pid), "%s bamboo seed from each grown plant" % num(seed) if seed else "",
                         "about %s days: %s of rest and %s to grow" % (num(fl["DormantDays"] + p.get("growth_days", 0)), num(fl["DormantDays"]), num(p.get("growth_days", 0)))))
        out += ["", "The first Flowering is the %s's. The two take turns." % c.pname(species[0]).lower() if species else "", ""]
        out += table(["Bamboo", "Seed", "Time without its ordinary harvest"], gaps)
        out += ["", "The setting, per save: normal, rare or off. Rare means the first one comes %s cycles later and they are %s to %s cycles apart."
                % (num(fl["RareDelayCycles"]), num(fl["RareMinCycles"]), num(fl["RareMaxCycles"]))]
        if c.has_recipe("PandabornBambooSeedCakes") and c.has_building("PandabornKitchen"):
            out += ["", "Bamboo seed cakes: %s, at the Kitchen." % c.recipe_line("PandabornBambooSeedCakes")]
        else:
            out += ["", "*Nothing cooks bamboo seed in this build: the Kitchen or its rice flour is switched off.*"]
        B["flowering"] = out
    else:
        B["flowering"] = ["*The Great Flowering is switched off in this build. Bamboo never flowers.*"]

    # ------------------------------------------------------------------ what cooks bamboo seed
    out = []
    for rid, r in c.recipes.items():
        if "PandabornBambooSeed" in r.get("ingredients", {}) and c.has_recipe(rid):
            where = [c.bname(b) for b, d in c.buildings.items() if rid in d.get("recipes", []) and c.has_building(b)]
            if where:
                out.append("* %s, at the %s." % (c.recipe_line(rid), " or the ".join(where)))
    B["seed"] = out or ["*Nothing cooks bamboo seed in this build.*"]

    # ------------------------------------------------------------------ late game
    out = []
    if c.has_building("PandabornOxWorkshop") and "PandabornWoodenOx" in c.recipes:
        r = c.recipes["PandabornWoodenOx"]
        out += ["**Wooden Oxen.** The %s (%s) builds one from %s in %s hours of work. An ox lifts %s against an Inkpaw's %s%s."
                % (c.bname("PandabornOxWorkshop"), c.price("PandabornOxWorkshop"),
                   c.goods_list(r.get("ingredients", {})), num(r["cycle_hours"]), num(lift_o), num(lift_i),
                   " and wears out after %s days" % num(ox_days) if ox_days else ""), ""]
    if c.has_building("PandabornSmokeKiln") and c.has_recipe("PandabornCuredPole"):
        out += ["**Cured poles.** %s, at the %s (%s). No power."
                % (c.recipe_line("PandabornCuredPole"), c.bname("PandabornSmokeKiln"), c.price("PandabornSmokeKiln")), ""]
    rows = []
    for bid, nid in MONUMENTS:
        if c.has_building(bid):
            wb = c.wellbeing(nid)
            rows.append((c.bname(bid), c.cost(bid), c.science(bid), "+%s" % num(wb) if wb else ""))
    out += table(["Monument", "Cost", "Science to unlock", "Well-being"], rows)
    sky = c.buildings.get("PandabornSkyLantern", {}).get("set", {}).get("WonderInventorySpec.RequiredGoods")
    if sky and c.has_building("PandabornSkyLantern"):
        out += ["", "The Sky Lantern is released with %s." % " and ".join("%s %s" % (num(g["Amount"]), c.gname(g["Id"], g["Amount"])) for g in sky)]
    lant = [(b, c.stats.get(b, {}).get("cost", {}).get("PandabornPaperLantern")) for b in
            ("PandabornStandingLantern", "PandabornHangingLantern", "PandabornStringLanterns")]
    lant = [(b, n) for b, n in lant if n and c.has_building(b)]
    if lant:
        out += ["", "Lantern decorations are built from paper lanterns: " + ", ".join("%s %s" % (c.bname(b), num(n)) for b, n in lant) + "."]
    B["late"] = out
    return B


MARK = re.compile(r"<!-- gen:([a-z_]+) -->\n(.*?)<!-- /gen:\1 -->", re.S)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if docs/PLAYER_GUIDE.md is out of date")
    ap.add_argument("--stdout", action="store_true", help="print the blocks, write nothing")
    ap.add_argument("--doc", default=GUIDE)
    a = ap.parse_args()
    blocks = build()
    if a.stdout:
        for k, v in blocks.items():
            sys.stdout.buffer.write(("## %s\n\n%s\n\n" % (k, "\n".join(v))).encode("utf-8"))
        return 0
    with io.open(a.doc, encoding="utf-8", newline="") as f:
        old = f.read().replace("\r\n", "\n")
    seen = set()

    def fill(m):
        name = m.group(1)
        seen.add(name)
        if name not in blocks:
            sys.stderr.write("unknown block gen:%s\n" % name)
            return m.group(0)
        return "<!-- gen:%s -->\n%s\n<!-- /gen:%s -->" % (name, "\n".join(blocks[name]), name)

    new = MARK.sub(fill, old)
    unused = sorted(set(blocks) - seen)
    if unused:
        sys.stderr.write("blocks with no marker in the guide: %s\n" % ", ".join(unused))
    if a.check:
        if new != old:
            sys.stderr.write("docs/PLAYER_GUIDE.md is out of date: run tools/docs/guide_tables.py\n")
            return 1
        return 0
    if new != old:
        with io.open(a.doc, "w", encoding="utf-8", newline="\n") as f:
            f.write(new)
    return 0


if __name__ == "__main__":
    sys.exit(main())
