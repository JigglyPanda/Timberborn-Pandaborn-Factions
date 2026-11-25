"""One function per balance question. Each returns Markdown; run.py prints it and writes tools/balance/out/<name>.md.

Read docs/tech/balance.md for what the numbers mean and how far each can be trusted.
"""
import copy
import math

from . import data, day, economy as eco, mech, playtest, weather

FT = data.Game("Folktails")
IT = data.Game("IronTeeth")
INK = data.Game("Inkpaws")
BEAVER = mech.kind(FT, "BeaverAdult", "Folktail")
INKPAW = mech.kind(INK, "InkpawAdult.Inkpaws", "Inkpaw")
RINGTAIL = mech.kind(INK, "RingtailAdult.Inkpaws", "Ringtail")
OX = mech.kind(INK, "Bot.Inkpaws", "Wooden Ox")
BOT = mech.kind(FT, "Bot.Folktails", "Folktails bot")
NOT_YET = ("PandabornBambooSeedCakes",)          # only after a Great Flowering


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for row in rows:
        out.append("| " + " | ".join(fmt(c) for c in row) + " |")
    return out + [""]


def fmt(x):
    if isinstance(x, float):
        return ("%.2f" % x) if abs(x) < 10 else ("%.1f" % x) if abs(x) < 100 else ("%.0f" % x)
    return str(x)


def whatif(game, needs=None, shelves=None):
    g = copy.copy(game)
    g.needs = copy.deepcopy(game.needs)
    g.recipes = copy.deepcopy(game.recipes)
    for need, wb in (needs or {}).items():
        g.needs[need]["FavorableWellbeing"] = wb
    for rid, n in (shelves or {}).items():
        g.recipes[rid]["CyclesCapacity"] = n
    return g


def worker(kind, hours, wb, **kw):
    return mech.Worker(INK if kind is not BEAVER and kind is not BOT else FT, kind, hours, wb, **kw)


# --- calibration -----------------------------------------------------------------------------------------------------

def calibrate():
    runs = [s for label in ("Folktails standard", "Inkpaws standard") for r in playtest.TRUSTED[label]
            if (s := playtest.summary(r))]
    mean = lambda key: sum(s[key] for s in runs) / len(runs) if runs else float("nan")
    b = worker(BEAVER, 16, 2)
    rows = [
        ["Logs a lumberjack a day (pine, flag 7 tiles from the trees, wellbeing under 5)", mean("logs_per_cutter"),
         mech.cutting(b, FT.plant("Pine"), tiles=7)],
        ["Water a pump worker makes a day (Inkpaws runs: the store never filled)",
         sum(s["pump"] for s in runs if "ink" in s["run"]) / max(1, sum(1 for s in runs if "ink" in s["run"])),
         mech.workshop(b, FT.recipe("Water"), supplied=True) * mech.PUMP_EFFICIENCY],
        ["Science an inventor makes a day", mean("science"), mech.workshop(b, FT.recipe("SciencePoints"), supplied=True)],
        ["Food a colonist eats a day", mean("food_each"), mech.FOOD_PER_DAY],
        ["Water a colonist drinks a day", mean("water_each"), mech.WATER_PER_DAY],
    ]
    shoots = playtest.shoot_survival()
    if shoots:
        alive = sum(a for _, _, _, a in shoots) / sum(b0 for _, _, b0, _ in shoots)
        rows.append(["Shoot bamboo (5 dry days) alive after a 5-day drought, share", alive, weather.survives(5.0, 5)])
    farm = mech.farming(b, INK.plant("PandabornShootBamboo"))
    rows.append(["Shoot-bamboo tiles one farmer keeps harvested (3 farmers were saturated on 105 crop tiles: 35 each)",
                 35.0, farm[1]])
    out = ["## Calibration: the model against the scripted playtests", ""]
    out += table(["Quantity", "Measured in game", "Model"], rows)
    out += ["Measured = mean over the trusted standard runs on Meander, Normal (three Folktails, two Inkpaws).",
            "The first crop came one day earlier for Inkpaws in every pair of runs (shoots day 5 to 6, carrots day 6",
            "to 7, farmhouses finished on day 2.5 to 3.0): the growth times, 3 days against 4.", ""]
    return out


# --- Q1 the first three cycles ---------------------------------------------------------------------------------------

def q1():
    out = ["## Q1. Cycles 1 to 3", "", "### Food: land, labour, science and drought", ""]
    rows = []
    for game, kind in ((FT, BEAVER), (INK, INKPAW)):
        for good, dish in sorted(eco.foods(game).items()):
            c = eco.chain(game, good)
            if not c["tile_days"] or good == "PandabornBambooSeedCakes":
                continue
            rows.append([game.faction, good.replace("Pandaborn", ""), game.need(dish)["wellbeing"] if dish else 0,
                         1 / c["tile_days"], c["hours"], eco.science_of(game, c["science"]),
                         ", ".join(sorted(c["extras"])) or "-", c["dry"] if c["dry"] is not None else "-"])
    out += table(["Faction", "Food", "Dish wellbeing", "Food per tile-day", "Work hours per food (speed 1)",
                  "Science", "Needs", "Dry days of its crop"], rows)

    out += ["### Share of unwatered plants alive after the n-th drought", ""]
    rows = []
    plants = [("Folktails carrot", 2.0), ("Folktails potato", 1.0), ("Shoot bamboo", 5.0), ("Cabbage", 7.0),
              ("Timber bamboo", 10.0), ("Shoot bamboo at 4", 4.0), ("Cabbage at 6", 6.0)]
    for mode_name, ns in (("Normal", (1, 2, 3, 4, 5, 6)), ("Hard", (1, 2, 3, 4))):
        m = weather.mode(FT, mode_name)
        for n in ns:
            dist = weather.lengths(m, n)
            rows.append([mode_name, n, "%d-%d" % (min(dist), max(dist))] +
                        ["%d%%" % round(100 * weather.survival(m, n, d)) for _, d in plants])
    out += table(["Mode", "Drought", "Days"] + [p for p, _ in plants], rows)

    out += ["### Stores a colony gets without building storage", ""]
    rows = []
    for label, vanilla, ours, per_day in (
            ("Water in one pump (recipe shelf)", FT.recipe("Water")["shelf"], INK.recipe("Water")["shelf"],
             mech.WATER_PER_DAY),
            ("Food in one farmhouse", FT.template("EfficientFarmHouse")["SimpleOutputInventorySpec"]["Capacity"],
             INK.template("EfficientFarmHouse")["SimpleOutputInventorySpec"]["Capacity"], mech.FOOD_PER_DAY),
            ("Food in one gatherer flag", FT.template("GathererFlag")["SimpleOutputInventorySpec"]["Capacity"],
             INK.template("GathererFlag")["SimpleOutputInventorySpec"]["Capacity"], mech.FOOD_PER_DAY)):
        rows.append([label, vanilla, ours, vanilla / per_day / 13, ours / per_day / 13])
    out += table(["Store", "Folktails", "Inkpaws", "Days for 13, Folktails", "Days for 13, Inkpaws"], rows)

    out += ["### Measured: the same scripted colony, both factions (Meander)", ""]
    rows = []
    for label, runs in playtest.TRUSTED.items():
        for r in runs:
            s = playtest.summary(r)
            if s:
                rows.append([label, r, s["days"], "%d to %d" % (s["start"], s["end"]), s["water_before_drought"],
                             s["food_before_drought"], s["critical_days"]["Thirst"], s["critical_days"]["Hunger"],
                             s["deaths"].get("thirst", 0) + s["deaths"].get("hunger", 0),
                             s["wellbeing30"] if s["wellbeing30"] is not None else "-"])
    out += table(["Scenario", "Run", "Days", "Colonists", "Water at the first drought", "Food at the first drought",
                  "Thirsty colonist-days", "Hungry colonist-days", "Died of thirst or hunger", "Wellbeing day 30"], rows)

    out += ["### Wellbeing a colony can hold at a given science spent (monuments and boosts aside)", ""]
    trims = {"PandabornPlay": 2, "PandabornContemplation": 2, "PandabornCubWatching": 3, "PandabornTea": 4}
    trimmed = whatif(INK, needs=trims)
    rows = []
    for s in (0, 200, 400, 700, 1000, 1500, 2500, 4000, 6000, 10000):
        rows.append([s, eco.wellbeing_at(FT, s)[0], eco.wellbeing_at(IT, s)[0], eco.wellbeing_at(INK, s, NOT_YET)[0],
                     eco.wellbeing_at(INK, s, NOT_YET, 3)[0], eco.wellbeing_at(trimmed, s, NOT_YET)[0]])
    out += table(["Science", "Folktails", "Iron Teeth", "Inkpaws", "Inkpaws with Tradition 3",
                  "Inkpaws, proposed trims"], rows)
    return out


# --- Q2 the bell -----------------------------------------------------------------------------------------------------

FLAT = tuple((("Hours", h), ("Bonus", 16.0 / h - 1)) for h in (12, 13, 14, 15, 16))


def q2():
    out = ["## Q2. The afternoon bell", "",
           "### Work done per Inkpaw-day against the same Inkpaw on a 16-hour day (no bonus), same wellbeing", ""]
    flat = mech.kind(INK, "InkpawAdult.Inkpaws", bell_override=(FLAT, FLAT))
    jobs = {"workshop": lambda w: w.on_post() * w.work_speed(),
            "builder": lambda w: mech.building(w, {"Log": 20, "Plank": 20}),
            "carrier": lambda w: mech.hauling(w, "Berries")}
    rows = []
    for wb in (0, 20, 50, 80):
        base = worker(INKPAW, 16, wb)
        for hours in (8, 10, 12, 13, 14, 15, 16, 18):
            w, f = worker(INKPAW, hours, wb), mech.Worker(INK, flat, hours, wb)
            rows.append([wb, hours, "+%d%%" % round(100 * w._bonus(0))] +
                        [job(w) / job(base) for job in jobs.values()] + [jobs["workshop"](f) / jobs["workshop"](base),
                         jobs["builder"](w) / jobs["builder"](worker(BEAVER, 16, wb))])
    out += table(["Wellbeing", "Day (h)", "Rested", "Workshop", "Builder", "Carrier", "Workshop with a flat curve",
                  "Builder against a Folktails builder on 16 h"], rows)
    out += ["The walking cap (%.2f) is never reached: the fastest Inkpaw walks at %.2f." %
            (INK.bonus_types["MovementSpeed"]["MaximumValue"], worker(INKPAW, 12, 100).move()), ""]

    out += ["### Do the rituals fit?", ""]
    rows = []
    for hours in (10, 12, 13, 14, 15, 16, 17, 18):
        have, need, kept, lost = day.fits(INK, hours)
        fh, fneed, fkept, flost = day.fits(FT, hours)
        rows.append([hours, have, need, kept, ", ".join(n.replace("Pandaborn", "") for n in lost) or "-",
                     fneed, fkept])
    out += table(["Day (h)", "Leisure hours", "Inkpaw rituals need", "Leisure wellbeing kept (of 23)", "Lapses",
                  "Folktails attractions need", "Folktails kept (of 22)"], rows)

    out += ["### Colony work per colonist-day with every ritual built, against Folktails on 16 hours", ""]
    hours_list = (10, 12, 13, 14, 15, 16, 17, 18)
    rows = []
    for base in (10, 30, 50):
        ref = day.output(FT, BEAVER, 16, base)[0]
        rows.append(["Inkpaws", base] + [day.output(INK, INKPAW, h, base)[0] / ref for h in hours_list])
        rows.append(["Folktails", base] + [day.output(FT, BEAVER, h, base)[0] / ref for h in hours_list])
    out += table(["Faction", "Wellbeing without leisure"] + ["%d h" % h for h in hours_list], rows)
    out += ["Both factions have all their attractions; a colonist short of time keeps the ones worth most per hour.", ""]

    out += ["### With Ringtails (no rested bonus; their night is 24 minus the bell, at most 20 h)", ""]
    rows = []
    for share in (0.0, 0.15, 0.3):
        row = ["%d%%" % round(100 * share)]
        ref = None
        for hours in (10, 12, 13, 14, 15, 16):
            ink = day.output(INK, INKPAW, hours, 30)[0]
            night = min(20.0, 24.0 - hours)
            ring = worker(RINGTAIL, night, 30 + 23)
            value = (1 - share) * ink + share * ring.on_post() * ring.work_speed()
            ref = ref or value
            row.append(value)
        rows.append(row)
    out += table(["Ringtails"] + ["%d h" % h for h in (10, 12, 13, 14, 15, 16)], rows)
    return out


# --- Q3 rituals ------------------------------------------------------------------------------------------------------

def q3():
    out = ["## Q3. Nap and tea", "", "### Colonists one building serves", ""]
    rows = []
    r = day.rituals(INK)
    for need, label in (("PandabornNap", None), ("PandabornTea", None), ("PandabornPlay", None),
                        ("PandabornCubWatching", None), ("PandabornContemplation", None), ("PandabornSoak", None)):
        seat, visits, wb, building, seats = r[need]
        rows.append([building.replace("Pandaborn", "").replace(".Inkpaws", ""), seats, wb, seat * 60] +
                    [day.served(INK, need, h) for h in (12, 14, 16)])
    hammock = INK.seats("PandabornHammock")
    rows.insert(0, ["Hammock", hammock, 3, 60.0] + [hammock * day.window_hours(h) * day.PACKING for h in (12, 14, 16)])
    out += table(["Building", "Seats", "Wellbeing", "Minutes a colonist-day", "Served at 12 h", "14 h", "16 h"], rows)

    tea = INK.template("PandabornTeahouse")["GoodConsumingBuildingSpec"]
    rate = {c["GoodId"]: c["GoodPerHour"] for c in tea["ConsumedGoods"]}
    bush = INK.plant("PandabornTeaBush")
    roast = INK.recipe("PandabornTea")
    out += ["### The tea chain for 100 colonists (12-hour day, wellbeing 30)", ""]
    w = worker(INKPAW, 12, 30)
    rows = []
    for label, occupied in (("Teahouses open only in the Inkpaws' afternoon", day.window_hours(12) * 0.9),
                            ("Ringtails fill them in the morning too", day.window_hours(12) * 0.9 + 4.0)):
        houses = math.ceil(100 / day.served(INK, "PandabornTea", 12))
        tea_day = houses * occupied * rate["PandabornTea"]
        water_day = houses * occupied * rate["Water"]
        leaves = tea_day / roast["out"]["PandabornTea"]
        bushes = leaves / (bush["gather"][1] / bush["regrow_d"])
        gather = leaves / mech.gathering(w, bush)
        roasting = leaves / mech.workshop(w, roast, supplied=True)
        hauling = (tea_day + water_day) / mech.hauling(worker(INKPAW, 12, 30, carry_bonus=1.0), "Water", 15)
        rows.append([label, houses, tea_day, water_day, bushes, gather + roasting + hauling,
                     "%.0f%%" % (100 * water_day / (100 * mech.WATER_PER_DAY))])
    out += table(["Case", "Teahouses", "Tea a day", "Water a day", "Tea bushes", "Workers (pick, roast, carry)",
                  "Water against drinking"], rows)
    gain = lambda wb, plus: (1 + mech.tier(INK, "WorkingSpeed", wb + plus)) / (1 + mech.tier(INK, "WorkingSpeed", wb)) - 1
    mean_gain = lambda wb, plus: sum(gain(wb + k, plus) for k in range(10)) / 10
    out += ["A Teahouse uses %.1f tea and %.1f water for every hour it has anyone inside, whatever the number of guests," %
            (rate["PandabornTea"], rate["Water"]),
            "and only haulers or night couriers stock it (a good-consuming building, game-mechanics.md 5.2).",
            "Its wellbeing 5 is worth %+.0f%% work at wellbeing 20, %+.0f%% at 40, %+.0f%% at 60, %+.0f%% at 80:" %
            tuple(100 * mean_gain(wb, 5) for wb in (20, 40, 60, 80)),
            "about 1 to 11 workers' worth per 100 colonists against under one worker of upkeep.",
            "Nap (3): %+.0f%%, %+.0f%%, %+.0f%%, %+.0f%% at the same wellbeing levels." %
            tuple(100 * mean_gain(wb, 3) for wb in (20, 40, 60, 80)), ""]
    return out


# --- Q4 Ringtails ----------------------------------------------------------------------------------------------------

def q4():
    out = ["## Q4. Ringtails", "", "### One Ringtail against one Inkpaw, per shift (wellbeing 30)", ""]
    flat = (tuple(INKPAW.bell[0]), tuple(INKPAW.bell[1]))
    variants = [("as shipped: lift 14, no rested bonus", RINGTAIL, None),
                ("lift 16", mech.kind(INK, "RingtailAdult.Inkpaws", lift=16), None),
                ("lift 18", mech.kind(INK, "RingtailAdult.Inkpaws", lift=18), None),
                ("lift 14 and the rested bonus by their own night", mech.kind(INK, "RingtailAdult.Inkpaws",
                                                                         bell_override=flat), "own")]
    rows = []
    for bell in (12, 14, 16):
        ink = worker(INKPAW, bell, 30)
        ink_h = worker(INKPAW, bell, 30, carry_bonus=1.0)
        beaver = worker(BEAVER, 16, 30)
        for label, kind, own in variants:
            night = 24 - bell
            r = mech.Worker(INK, kind, night, 30)
            rh = mech.Worker(INK, kind, night, 30, carry_bonus=1.0)
            rows.append([bell, label,
                         mech.building(r, {"Log": 1}) / mech.building(ink, {"Log": 1}),
                         mech.building(r, {"Plank": 1}) / mech.building(ink, {"Plank": 1}),
                         mech.hauling(rh, "Log") / mech.hauling(ink_h, "Log"),
                         mech.hauling(rh, "Water") / mech.hauling(ink_h, "Water"),
                         mech.hauling(rh, "Berries") / mech.hauling(ink_h, "Berries"),
                         mech.building(r, {"Log": 1, "Plank": 1}) / mech.building(beaver, {"Log": 1, "Plank": 1})])
    out += table(["Bell", "Ringtail", "Builder, logs", "Builder, poles", "Courier, logs", "Courier, water",
                  "Courier, food", "Builder against a Folktails builder"], rows)

    out += ["### What a night courier is worth: one workshop worker's cycles a day, alone and supplied (12-hour day)", ""]
    w = worker(INKPAW, 12, 30)
    rows = []
    for building in ("LumberMill", "PandabornSteamer", "PandabornPickleYard", "PandabornTeaRoastery",
                     "PandabornHotPotHall", "GearWorkshop", "PaperMill", "PandabornLanternWorkshop", "Smelter"):
        rid = INK.recipes_of(building)[0]
        r = INK.recipe(rid)
        alone, full = mech.workshop(w, r), mech.workshop(w, r, supplied=True)
        loads = sum(full * a / worker(RINGTAIL, 12, 30, carry_bonus=1.0).load(g)
                    for g, a in list(r["in"].items()) + list(r["out"].items()))
        trips_h = loads * worker(RINGTAIL, 12, 30).trip(12)
        rows.append([building.replace("Pandaborn", ""), rid.replace("Pandaborn", ""), alone, full,
                     "%d%%" % round(100 * alone / full), trips_h,
                     (full - alone) / full * 12 / trips_h if trips_h else 0.0])
    out += table(["Workshop", "Recipe", "Cycles alone", "Cycles supplied", "Uptime alone", "Courier hours a night",
                  "Inkpaw hours freed per courier hour"], rows)

    posts = [(b, INK.workers(b)) for b in ("PandabornNightBuildersPost", "PandabornNightCourierPost",
                                           "PandabornNightForagersPost")]
    out += ["Night posts: " + ", ".join("%s %d workers, %d science, %s" % (
        b.replace("Pandaborn", ""), n, INK.science(b), INK.cost(b)) for b, n in posts) +
        "; Moon Loft %d science, %s." % (INK.science("PandabornMoonLoft"), INK.cost("PandabornMoonLoft")), ""]
    return out


# --- Q5 shelves ------------------------------------------------------------------------------------------------------

def q5():
    out = ["## Q5. Shelves", "", "### What each workshop can hold back, once haulers or couriers fill it", ""]
    rows = []
    scarce = ("Log", "Plank", "TreatedPlank", "Gear", "Paper", "Water")
    totals = {"now": {}, "day": {}, "vanilla": {}}
    for b in INK.buildings():
        for rid in INK.recipes_of(b):
            r = INK.recipe(rid)
            workers = max(1, INK.workers(b))
            vanilla = FT.recipes.get(rid, {}).get("CyclesCapacity") or \
                {"PandabornSteamedShoots": 30, "PandabornSteamedRice": 30, "PandabornPickles": 20, "PandabornTea": 20,
                 "PandabornPaper": 10, "PandabornPaperLantern": 10, "PandabornCuredPole": 10, "PandabornHotPot": 15,
                 "PandabornSweetRiceBalls": 20, "PandabornBambooSeedCakes": 20, "PandabornRiceFlour": 20}.get(rid, 0)
            one_day = max(vanilla, math.ceil(16 * workers / r["hours"]))
            held = {g: a * r["shelf"] for g, a in r["in"].items() if g in scarce}
            if r["fuel"] in scarce:
                held[r["fuel"]] = held.get(r["fuel"], 0) + r["fuel_cap"]
            if not held and rid not in ("Water", "Water.Efficient"):
                continue
            ratio = one_day / r["shelf"] if r["shelf"] else 0
            for g, n in held.items():
                totals["now"][g] = totals["now"].get(g, 0) + n
                totals["day"][g] = totals["day"].get(g, 0) + n * ratio
                totals["vanilla"][g] = totals["vanilla"].get(g, 0) + n * (vanilla / r["shelf"] if r["shelf"] else 0)
            rows.append([b.replace("Pandaborn", "").replace(".Inkpaws", ""), rid.replace("Pandaborn", ""),
                         r["shelf"], one_day, vanilla, ", ".join("%s %d" % kv for kv in held.items()) or "-",
                         ", ".join("%s %d" % (g, a * r["shelf"]) for g, a in r["out"].items()) or "-"])
    out += table(["Building", "Recipe", "Cycles held (48 h)", "At 16 h", "Vanilla", "Scarce inputs held at 48 h",
                  "Output shelf at 48 h"], rows)
    out += ["Held in input shelves if one of each were built and haulers kept them full: logs %d (16-hour rule %d, vanilla %d),"
            % (totals["now"].get("Log", 0), totals["day"].get("Log", 0), totals["vanilla"].get("Log", 0)),
            "poles %d (%d, %d). Two lumberjacks bring in about 33 logs a day (measured)." %
            (totals["now"].get("Plank", 0), totals["day"].get("Plank", 0), totals["vanilla"].get("Plank", 0)), ""]
    return out


# --- Q6 water --------------------------------------------------------------------------------------------------------

def q6():
    out = ["## Q6. Water", "", "### Drinking water to store for a drought", ""]
    tanks = [(b, INK.template(b)["StockpileSpec"]["MaxCapacity"], INK.cost(b), INK.science(b))
             for b in ("PandabornCisternSmall", "PandabornCisternMedium", "PandabornCisternLarge")]
    rows = []
    for pop in (20, 50, 100):
        for days_ in (3, 6, 9):
            need = pop * mech.WATER_PER_DAY * days_
            rows.append([pop, days_, need] + [need / cap for _, cap, _, _ in tanks] +
                        [need / INK.recipe("Water")["shelf"]])
    out += table(["Colonists", "Dry days", "Water"] + ["%s (%d)" % (b.replace("PandabornCistern", ""), cap)
                                                       for b, cap, _, _ in tanks] + ["Pump shelves (146)"], rows)
    out += ["Cisterns: " + "; ".join("%s %d water, %s, %d science" % (b.replace("Pandaborn", ""), cap, cost, sci)
                                      for b, cap, cost, sci in tanks) + ".",
            "Folktails: Small Tank 30 (%s), Medium 300 (%s, %d science), Large 1200 (%s, %d science)." % (
                FT.cost("SmallTank"), FT.cost("MediumTank"), FT.science("MediumTank"), FT.cost("LargeTank"),
                FT.science("LargeTank")), ""]

    strip, good_m3 = 0.21, 0.2                   # measured, docs/tech/water.md: m3 a strip tile a day; m3 per Water
    band = 13                                    # moist tiles across a one-wide flume (6 each side), measured
    tap = INK.recipe("FlowingWater")
    out += ["### Irrigation (measured rates from docs/tech/water.md)", ""]
    day_seconds = 768 * 0.6
    rows = [["Scoop Wheel at a current of 0.30", "0.10 m3/s", 0.10 * day_seconds, 0.10 * day_seconds / strip,
             0.10 * day_seconds / strip * band],
            ["Flume Gate at its default 0.30", "0.36 m3/s", 0.36 * day_seconds, 0.36 * day_seconds / strip,
             0.36 * day_seconds / strip * band],
            ["Cistern Tap, one worker, 12-hour day at speed 1.33",
             "%d Water an hour of work" % sum(tap["in"].values()),
             sum(tap["in"].values()) * 16 * good_m3, sum(tap["in"].values()) * 16 * good_m3 / strip,
             sum(tap["in"].values()) * 16 * good_m3 / strip * band]]
    out += table(["Source", "Rate", "m3 a day", "Strip tiles kept wet", "Farm tiles kept moist"], rows)
    out += ["The tap's rule of thumb, 100 Water for six days: %.0f tiles (text: about 200)." %
            (100 * good_m3 / 6 / strip * band), ""]
    rows = []
    for b, cap, _, _ in tanks:
        rows.append([b.replace("PandabornCistern", ""), cap] +
                    [cap * good_m3 / d / strip * band for d in (3, 6, 9, 20, 30)])
    out += table(["Cistern poured through a tap", "Water"] + ["Farm tiles, %d dry days" % d for d in (3, 6, 9, 20, 30)],
                 rows)
    dew = INK.recipe("PandabornDewWater")
    per_day = 24 / dew["hours"]
    dry = INK.template("PandabornDewCollector")["PandabornDewLimiterSpec"]["DroughtEfficiency"]
    out += ["Dew Collector: %.1f Water a day, %.1f in a drought, %s, %d science: %.1f collectors per colonist in fair"
            % (per_day, per_day * dry, INK.cost("PandabornDewCollector"), INK.science("PandabornDewCollector"),
               mech.WATER_PER_DAY / per_day),
            "weather and %.1f in a drought. The crowding rule its text promises is not in the code." %
            (mech.WATER_PER_DAY / (per_day * dry)), ""]
    return out


# --- Q7 Flowering, Q8 Festival ---------------------------------------------------------------------------------------

def q7():
    spec = INK.template("InkpawAdult.Inkpaws")["PandabornFloweringSpec"]
    shoot, timber = INK.plant("PandabornShootBamboo"), INK.plant("PandabornTimberBamboo")
    out = ["## Q7. The Great Flowering", ""]
    rows = []
    for share in (0.2, 0.35, 0.5, 0.75, 1.0):
        gap = spec["DormantDays"] + shoot["grow_d"]
        rows.append(["%d%%" % round(100 * share), gap, share * mech.FOOD_PER_DAY * gap,
                     share * mech.FOOD_PER_DAY * (INK.plant("PandabornCabbage")["grow_d"] + 0.5)])
    out += table(["Shoots' share of the food", "Days without shoots", "Food to store per panda",
                  "...if the fields are re-marked with cabbage"], rows)
    cakes = INK.recipe("PandabornBambooSeedCakes")
    seeds = INK.plant("PandabornShootBambooInFlower")["cut"][1]
    rows = []
    for pop in (40, 80, 150):
        tiles = pop * 0.35 * mech.FOOD_PER_DAY / 2 / (shoot["cut"][1] / shoot["grow_d"])    # steamed: 2 per shoot
        seed = tiles * seeds
        cake = seed * cakes["out"]["PandabornBambooSeedCakes"]
        rows.append([pop, tiles, seed, cake, cake / (pop * mech.FOOD_PER_DAY), cake / (pop * 0.25),
                     seed * cakes["hours"] / 12])
    out += table(["Colonists", "Shoot tiles (35% of food, steamed)", "Seed", "Seed cakes", "Days of all food",
                  "Days the +3 dish lasts at a bite every four days", "Kitchen worker-days at speed 1"], rows)
    out += ["Timber year: %d days without poles from bamboo; one Pole Mill worker makes %.0f poles a day from logs." %
            (spec["DormantDays"] + timber["grow_d"],
             mech.workshop(worker(INKPAW, 12, 30), INK.recipe("Plank"), supplied=True)), ""]
    m = weather.mode(FT, "Hard")
    out += ["Hard: the temperate season is %d to %d days, so the nine-day rest always ends inside the cycle's drought;"
            % m["temperate"], "the sixth Hard drought lasts %d to %d days." %
            (min(weather.lengths(m, 6)), max(weather.lengths(m, 6))), ""]
    return out


def q8():
    f = INK.template("InkpawAdult.Inkpaws")["PandabornFestivalSpec"]
    lantern, paper = INK.recipe("PandabornPaperLantern"), INK.recipe("PandabornPaper")
    lanterns = f["Lanterns"]
    cycles = lanterns / lantern["out"]["PandabornPaperLantern"]
    paper_n = cycles * lantern["in"]["Paper"]
    poles = cycles * lantern["in"].get("Plank", 0) + paper_n / paper["out"]["Paper"] * paper["in"]["Plank"]
    hours = cycles * lantern["hours"] + paper_n / paper["out"]["Paper"] * paper["hours"]
    dishes = f["DishKinds"] * f["DishAmount"]
    festive = INK.need("PandabornFestive")
    lasts = 1.0 / -festive["daily"]
    out = ["## Q8. The Lantern Festival", "",
           "A Small Festival burns %d lanterns (%d paper, %.0f poles, %.0f work hours at speed 1) and %d dishes, and"
           % (lanterns, paper_n, poles, hours, dishes),
           "costs one working day. Festive +%d lasts %.0f days; a Normal cycle is %d to %d days." %
           (festive["wellbeing"], lasts, weather.mode(FT, "Normal")["temperate"][0] + 2,
            weather.mode(FT, "Normal")["temperate"][1] + 9), ""]
    rows = []
    for wb in (10, 20, 30, 40, 50, 60, 70, 80):
        gain = sum((1 + mech.tier(INK, "WorkingSpeed", wb + k + festive["wellbeing"])) /
                   (1 + mech.tier(INK, "WorkingSpeed", wb + k)) - 1 for k in range(10)) / 10
        for pop in (40,):
            goods = (hours / (12 * 0.97 * (1 + mech.tier(INK, "WorkingSpeed", wb)) * 1.33) + dishes / 60.0) / pop
            rows.append([wb, "%+.1f%%" % (100 * gain), gain * lasts, 1.0 + goods, gain * lasts - 1.0 - goods,
                         (gain * lasts) / (1.0 + goods)])
    out += table(["Colony wellbeing", "Work speed from +%d" % festive["wellbeing"], "Days of work gained",
                  "Days of work spent (40 colonists)", "Net", "Return"], rows)
    out += ["Tradition unlocks, by level: " + "; ".join(
        "%d: %s (+%d)" % (lvl, b.replace("Pandaborn", "").replace(".Inkpaws", ""), wb) for lvl, b, wb in sorted(
            (INK.templates[b]["PandabornTraditionSpec"]["Level"], b,
             sum(INK.need(e["NeedId"])["wellbeing"] for e in
                 INK.templates[b].get("ContinuousEffectBuildingSpec", {}).get("Effects", [])
                 if e["NeedId"].startswith("Pandaborn")))
            for b in INK.buildings() if "PandabornTraditionSpec" in INK.templates[b])) + ".", ""]
    return out


# --- Q9 late game ----------------------------------------------------------------------------------------------------

def material_days(game, kind, hours, wb=30):
    """Worker-days per unit of each building material, made and carried 12 tiles."""
    w = mech.Worker(game, kind, hours, wb)
    log = 1 / mech.cutting(w, game.plant("Pine"))
    if game is INK:
        bamboo = game.plant("PandabornTimberBamboo")
        plank = 1 / mech.cutting(w, bamboo) + bamboo["plant_h"] / bamboo["cut"][1] / (w.on_post() * w.work_speed())
    else:
        plank = log + 1 / mech.workshop(w, game.recipe("Plank"))
    gear = plank + 1 / mech.workshop(w, game.recipe("Gear"))
    paper_r = game.recipe("PandabornPaper" if game is INK else "Paper")
    paper = ((plank if game is INK else log) + 1 / mech.workshop(w, paper_r)) / 2
    if game is INK:
        cured_r = game.recipe("PandabornCuredPole")
        cured = plank + 1 / mech.workshop(w, cured_r) + log / cured_r["cycles_per_fuel"]
    else:
        resin = 7.0 / 2 * 0.1 / (w.on_post())            # a tapper's hour per two resin every seven days: small
        cured = plank + 1 / mech.workshop(w, game.recipe("TreatedPlank")) + resin
    metal_r = game.recipe("MetalBlock")
    scrap = 1 / (w.on_post() / (1.0 / w.work_speed() + w.trip(15)))       # scavenger: one scrap a trip
    metal = 2 * scrap + 1 / mech.workshop(w, metal_r) + log / metal_r["cycles_per_fuel"]
    return {"Log": log, "Plank": plank, "Gear": gear, "Paper": paper, "TreatedPlank": cured, "MetalBlock": metal,
            "ScrapMetal": scrap}


def q9():
    out = ["## Q9. Late game", "", "### Worker-days per unit of material (wellbeing 30; Folktails 16 h, Inkpaws 12 h)", ""]
    ft, ink = material_days(FT, BEAVER, 16), material_days(INK, INKPAW, 12)
    names = {"Plank": "Plank / pole", "TreatedPlank": "Treated plank / cured pole"}
    out += table(["Material", "Folktails", "Inkpaws", "Inkpaws / Folktails"],
                 [[names.get(g, g), ft[g], ink[g], ink[g] / ft[g]] for g in ("Log", "Plank", "Gear", "Paper",
                                                                           "TreatedPlank", "MetalBlock")])
    price = lambda prices, cost: sum(prices.get(g, 0) * n for g, n in cost.items())
    rows = []
    for game, prices, items in ((FT, ft, ("FarmerMonument", "BrazierOfBonding", "FountainOfJoy", "HallOfAbundance",
                                          "EarthRecultivator")),
                                (INK, ink, ("PandabornMemorialArch", "PandabornGreatSittingPanda",
                                            "PandabornSkyLantern"))):
        for b in items:
            t = game.template(b)
            awe = sum(game.need(e["NeedId"])["wellbeing"] for e in t.get("ContinuousEffectBuildingSpec", {}).get(
                "Effects", []) if e["NeedId"] in game.needs)
            if not awe:
                awe = max((game.need(n)["wellbeing"] for n in game.needs if n in b), default=0)
            fill = {g["Id"]: g["Amount"] for g in t.get("WonderInventorySpec", {}).get("RequiredGoods", [])}
            fill_days = fill.get("Paper", 0) * prices["Paper"] + fill.get("Extract", 0) * 0.12 + \
                fill.get("PandabornPaperLantern", 0) * (prices["Paper"] + prices["Plank"] / 2 + 0.75 / 12 / 2.2)
            rows.append([game.faction, b.replace("Pandaborn", ""), awe, t["RangedEffectBuildingSpec"]["EffectRadius"],
                         game.science(b), ", ".join("%s %d" % kv for kv in game.cost(b).items()),
                         price(prices, game.cost(b)), fill_days or "-"])
    out += table(["Faction", "Monument", "Awe", "Radius", "Science", "Cost", "Worker-days of materials",
                  "Worker-days to fill"], rows)

    out += ["### Wooden Ox against a Folktails bot and a colonist (per day)", ""]
    rows = []
    ox, bot = worker(OX, 24, 0), worker(BOT, 24, 0)
    boosted = mech.Worker(FT, mech.kind(FT, "Bot.Folktails", fixed=(1 + mech.tier(FT, "WorkingSpeed", 2, "Bot"),
                                                                     1 + mech.tier(FT, "MovementSpeed", 2, "Bot"))), 24, 0)
    ink50, beaver50 = worker(INKPAW, 12, 50), worker(BEAVER, 16, 50)
    for label, w in (("Wooden Ox", ox), ("Folktails bot, fuel only", bot), ("Folktails bot, both boosts", boosted),
                     ("Inkpaw, wellbeing 50, 12 h", ink50), ("Folktail, wellbeing 50, 16 h", beaver50)):
        hauler = mech.Worker(w.game, w.kind, w.hours, w.wellbeing, carry_bonus=1.0)
        rows.append([label, w.kind.lift, mech.hauling(hauler, "Plank"), mech.hauling(hauler, "Log"),
                     mech.building(w, {"Log": 1, "Plank": 1}), w.on_post() * w.work_speed()])
    out += table(["Worker", "Lift", "Poles hauled 20 tiles", "Logs hauled", "Units built", "Workshop hours at speed 1"],
                 rows)
    ox_r = INK.recipe("PandabornWoodenOx")
    ox_cost = price(ink, ox_r["in"]) + ox_r["hours"] / (ink50.on_post() * ink50.work_speed())
    bot_cost = (10 * ft["Plank"] + 15 * ft["Gear"] + 2 * ft["MetalBlock"]) + (72 + 54) / (
        beaver50.on_post() * beaver50.work_speed())
    life_ox = INK.template("Bot.Inkpaws")["DeteriorableSpec"]["DeteriorationInDays"]
    life_bot = FT.template("Bot.Folktails")["DeteriorableSpec"]["DeteriorationInDays"]
    out += ["An ox costs about %.1f worker-days and lasts %d days with no upkeep (%.3f a day); a Folktails bot about"
            % (ox_cost, life_ox, ox_cost / life_ox),
            "%.1f worker-days, lasts %d days, and drinks about 1.9 biofuel a day. Workshop and science: Ox Workshop %d"
            % (bot_cost, life_bot, INK.science("PandabornOxWorkshop")),
            "science against %d for the Bot Part Factory and Bot Assembler." %
            (FT.science("BotPartFactory") + FT.science("BotAssembler")), ""]

    out += ["### Wellbeing a colonist can reach", ""]
    rows = []
    for game in (FT, IT, INK):
        groups = {}
        for nid in game.faction_needs():
            n = game.need(nid)
            if n["wellbeing"] > 0 and nid not in ("Catalyst", "PunchCard", "ControlTower", "Grease"):
                groups[n["group"]] = groups.get(n["group"], 0) + n["wellbeing"]
        order = ("BasicNeeds", "Nutrition", "SocialLife", "Fun", "Aesthetics", "Awe", "Boosts")
        rows.append([game.faction] + [groups.get(g, 0) for g in order] + [sum(groups.values())])
    out += table(["Faction", "Basic", "Nutrition", "Social", "Fun", "Aesthetics", "Awe", "Boosts", "Total"], rows)
    return out


# --- Q10 science, Q11 Hard -------------------------------------------------------------------------------------------

BEATS = [("First shoots; Steamer", ["PandabornSteamer"], "days 3-5"),
         ("Hammock", ["PandabornHammock"], "days 3-5"),
         ("Teahouse with tea in it", ["PandabornTeaRoastery", "PandabornTeahouse"], "days 3-5"),
         ("Scoop wheel and a short flume", ["PandabornScoopWheel", "PandabornFlumeGate", "PandabornFlume"], "days 5-8"),
         ("Medium Cistern before the first drought", ["PandabornCisternMedium"], "first drought"),
         ("First Moon Loft", ["PandabornMoonLoft"], "end of cycle 1"),
         ("Paddy spout and rice; pickles", ["PandabornPaddySpout", "PandabornPaddyHouse", "PandabornPickleYard"],
          "cycle 2"),
         ("Lanterns and the Small Festival", ["GearWorkshop", "PaperMill", "PandabornLanternWorkshop",
                                              "PandabornFestivalSquare"], "cycle 2"),
         ("Trip-hammer mill; sweet rice balls", ["PandabornTripHammerMill", "PandabornKitchen"], "cycle 3")]


def q10():
    out = ["## Q10. Science", "", "### The design's first two hours, in order, on inventors alone", ""]
    rate = mech.workshop(worker(INKPAW, 16, 2), INK.recipe("SciencePoints"), supplied=True)
    rows, spent = [], 0
    for label, buildings, when in BEATS:
        cost = sum(INK.science(b) for b in buildings)
        spent += cost
        row = [label, when, cost, spent]
        for inventors, speed in ((1, 1.0), (2, 1.0), (2, 1.4), (4, 1.4)):
            row.append(4.5 + spent / (rate * inventors * speed))
        rows.append(row)
    out += table(["Beat", "The design says", "Science", "Running total", "Day, 1 inventor", "2 inventors",
                  "2 at wellbeing 10+", "4 at wellbeing 10+"], rows)
    out += ["An inventor makes %.1f science a day at speed 1 (measured 16 to 17); the first is staffed about day 4.5." % rate, ""]

    tea = INK.plant("PandabornTeaBush")
    out += ["Tea cannot be served before day %.0f whatever the science: the forester stands on day 2 to 3, a bush"
            % (2.5 + tea["grow_d"] + tea["regrow_d"]),
            "takes %d days to grow and %d more to bear its first leaves, and the Teahouse is stocked only by haulers." %
            (tea["grow_d"], tea["regrow_d"]), ""]

    out += ["### The whole tree", ""]
    rows = []
    for game in (FT, IT, INK):
        total = sum(game.science(b) for b in game.buildings())
        top = sorted(((game.science(b), b) for b in game.buildings()), reverse=True)[:3]
        rows.append([game.faction, total, ", ".join("%s %d" % (b.split(".")[0].replace("Pandaborn", ""), s)
                                                    for s, b in top)])
    out += table(["Faction", "Science to unlock everything", "Largest"], rows)
    inv = mech.workshop(worker(INKPAW, 12, 50), INK.recipe("SciencePoints"), supplied=True)
    obs_r = FT.recipe("SciencePoints.Observatory") if "SciencePoints.Observatory" in FT.recipes else None
    obs_id = next((r for r in FT.recipes_of("Observatory")), None)
    obs = FT.recipe(obs_id)
    w = worker(BEAVER, 16, 50)
    per_worker = w.on_post() * w.work_speed() / obs["hours"] * obs["science"] / 1.0
    out += ["At wellbeing 50 an Inkpaw inventor makes %.0f science a day. A Folktails Observatory worker makes %.0f"
            % (inv, per_worker),
            "(%d science per %d-hour cycle, each worker adding its speed). The Star Tower is not in the build"
            % (obs["science"], obs["hours"]),
            "(it waits for the RingtailVenues module), so the last 38,000 science (Memorial Arch, Great Sitting Panda,",
            "Sky Lantern) takes %.0f inventor-days against %.0f Observatory worker-days." %
            (38000 / inv, 38000 / per_worker), ""]
    return out


def q11():
    out = ["## Q11. Hard, long droughts and badtides", ""]
    hard, normal = weather.mode(FT, "Hard"), weather.mode(FT, "Normal")
    rows = []
    for n in (1, 2, 3, 4, 5, 6, 8, 10, 13):
        dist = weather.lengths(hard, n)
        p95 = weather.percentile(dist, 0.95)
        bd = weather.lengths(hard, max(1, n - 3), hazard="badtide")
        rows.append([n, "%d-%d" % (min(dist), max(dist)), p95, p95 * mech.WATER_PER_DAY,
                     "%d%%" % round(100 * weather.survival(hard, n, 5.0)),
                     "%d%%" % round(100 * weather.survival(hard, n, 7.0)),
                     "%d%%" % round(100 * weather.survival(hard, n, 10.0)),
                     "%d%%" % round(100 * weather.survival(hard, n, 15.0))])
    out += table(["Hard drought", "Days", "95th percentile", "Water per colonist to store", "Shoot bamboo alive",
                  "Cabbage", "Timber bamboo", "Oak (vanilla, 15)"], rows)
    out += ["Hard temperate seasons last %d to %d days; the first Hard badtide (cycle 4 at the earliest) lasts %d to %d"
            % (hard["temperate"] + (min(weather.lengths(hard, 1, hazard="badtide")),
                                    max(weather.lengths(hard, 1, hazard="badtide")))),
            "days. Normal droughts never exceed %d days, so timber bamboo (10) never dies of drought on Normal." %
            max(weather.lengths(normal, 13)), ""]
    return out


ALL = {"calibrate": calibrate, "q1": q1, "q2": q2, "q3": q3, "q4": q4, "q5": q5, "q6": q6, "q7": q7, "q8": q8,
       "q9": q9, "q10": q10, "q11": q11}
