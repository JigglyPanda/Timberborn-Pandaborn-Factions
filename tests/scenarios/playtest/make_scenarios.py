"""Writes the Inkpaws and careless scenario files from one shared plan shape (run: python make_scenarios.py).
folktails-baseline.json is the hand-written reference; the others are derived here so the quality of play stays equal."""
import copy, json

def load(p): return json.load(open(p, encoding="utf-8"))
def save(p, d): json.dump(d, open(p, "w", encoding="utf-8"), indent=2); print("wrote", p)

ft = load("folktails-baseline.json")

INK_NAMES = {
    "lumber": "LumberjackFlag.Inkpaws", "pump": "WaterPump.Inkpaws", "gatherer": "GathererFlag.Inkpaws",
    "farm": "EfficientFarmHouse.Inkpaws", "home": "PandabornDen.Inkpaws", "home2": "PandabornCourtyardHouse.Inkpaws",
    "tank": "PandabornCisternSmall.Inkpaws", "tankM": "PandabornCisternMedium.Inkpaws", "pile": "SmallPile.Inkpaws",
    "pileL": "LargePile.Inkpaws", "wh": "SmallWarehouse.Inkpaws", "whM": "MediumWarehouse.Inkpaws",
    "inventor": "Inventor.Inkpaws", "forester": "Forester.Inkpaws", "campfire": "Campfire.Inkpaws",
    "gears": "GearWorkshop.Inkpaws", "hauling": "HaulingPost.Inkpaws", "contemplation": "PandabornInkStudio.Inkpaws",
    "shrub": "Shrub.Inkpaws", "staple": "PandabornShootBamboo.Inkpaws", "staple2": "PandabornCabbage.Inkpaws",
    "shoots": "PandabornBambooShoots", "cabbage": "PandabornCabbage", "tree1": "PandabornTimberBamboo.Inkpaws",
    "cook": "PandabornSteamer.Inkpaws", "cookRecipe": "PandabornSteamedShoots", "cooked": "PandabornSteamedShoots",
    "pickler": "PandabornPickleYard.Inkpaws", "logTree": "Birch", "pickles": "PandabornPickles", "hammock": "PandabornHammock.Inkpaws", "teahouse": "PandabornTeahouse.Inkpaws",
}

def step(**kw): return kw

def inkpaws(name, mode_note, bootstrap=True):
    d = copy.deepcopy(ft)
    p = d["playtest"]
    p["name"] = name
    p["names"] = INK_NAMES
    p["note"] = ("Inkpaws, the same quality of play, following DESIGN.md's first two hours: shoot bamboo and cabbage first, "
                 "timber bamboo (forester) for poles, cisterns before the first drought, steamer then pickles, dens as beds run "
                 "out, campfire, hammocks, ink studio. Working day left at 16 h: the rested bonus is not in the installed build. "
                 + mode_note)
    steps = []
    for s in p["steps"]:
        s = copy.deepcopy(s)
        i = s["id"]
        if i == "whCarrot": s["good"] = "@shoots"
        if i == "whBerry2": s["good"] = "@shoots"
        if i == "mill1" or i == "pilePlank": continue          # no lumber mill: poles come from timber bamboo
        if i == "forester1":                                     # DESIGN: forester with timber bamboo on day 1-2
            s["when"] = {"day": 1.5}
            s["near"] = "lumber1"
        if i == "field2":                                        # second farm: cabbage (second staple), not potatoes
            s["plant"] = "@staple2"
        if i == "field1b": s["plant"] = "@staple"
        if i == "tankM1": s["when"] = {"day": 7, "science": 100, "stock": {"Plank": 30}}   # Inkpaws cistern: no gears
        if i == "field3": s["plant"] = "@staple2"
        if i == "cook1": s["when"] = {"day": 3, "science": 40, "stock": {"Plank": 5}}   # steamer cooks shoots, days 3-5
        steps.append(s)
        if i == "field1":
            steps.append(step(id="field1c", op="plant", target="farm1", plant="@staple2", count=15, when={"after": ["field1"]}))
        if i == "forester1" and bootstrap:
            # WORKAROUND, not play: the installed Forester.Inkpaws costs 7 poles and poles only come from timber bamboo the
            # forester plants, so a pure colony never gets its first pole (see inkpaws-pure). Seven poles are put in a pole
            # pile once, the cost difference to the balance sheet's log-only forester.
            steps.insert(0, step(id="pilePoles", op="build", template="@pile", good="Plank", maxDistance=12, when={"day": 0.3}))
            steps.insert(1, step(id="bootstrapPoles", op="give", target="pilePoles", good="Plank", amount=7, when={"finished": ["pilePoles"]}))
        if i == "forester1":
            steps.append(step(id="pilePoles2", op="build", template="@pileL", good="Plank", near="forester1", maxDistance=10, when={"after": ["forester1"], "day": 4}))
        if i == "cook1":
            steps.append(step(id="pickler1", op="build", template="@pickler", maxDistance=15, recipe="@pickles", when={"day": 5, "science": 120, "stock": {"Plank": 15}}))
            steps.append(step(id="whPickles", op="build", template="@wh", good="@pickles", near="pickler1", maxDistance=8, when={"after": ["pickler1"]}))
            steps.append(step(id="whCabbage", op="build", template="@wh", good="@cabbage", near="farm1", maxDistance=10, when={"day": 4}))
        if i == "campfire1":
            steps.append(step(id="hammock", op="build", template="@hammock", repeat=4, everyHours=2, maxDistance=12, when={"day": 5}))
            steps.append(step(id="teahouse1", op="build", template="@teahouse", maxDistance=16, when={"day": 10, "science": 150, "stock": {"Plank": 20}}))
    p["steps"] = steps
    return d

std = inkpaws("inkpaws-standard", "Normal difficulty.", bootstrap=False)
save("inkpaws-standard.json", std)

# inkpaws-pure.json (the plan without any pole workaround) is now the same as inkpaws-standard: since the stat-sheet
# import the Forester costs Log 12, so the first pole no longer depends on a pole. Kept as a file for the history.

hard = inkpaws("inkpaws-hard", "Hard difficulty: the same plan with water storage and the second staple brought forward, as a Hard player would.", bootstrap=False)
for s in hard["playtest"]["steps"]:
    w = s.get("when", {})
    if s["id"] in ("tank2", "tank3"): w["day"] = {"tank2": 2.5, "tank3": 3.5}[s["id"]]
    if s["id"] == "farm2": w["day"] = 3
save("inkpaws-hard.json", hard)

fthard = copy.deepcopy(ft)
fthard["playtest"]["name"] = "folktails-hard"
fthard["playtest"]["note"] = "Folktails on Hard, the comparison for inkpaws-hard: the baseline plan with water storage and the second farm brought forward."
for s in fthard["playtest"]["steps"]:
    w = s.get("when", {})
    if s["id"] in ("tank2", "tank3"): w["day"] = {"tank2": 2.5, "tank3": 3.5}[s["id"]]
    if s["id"] == "farm2": w["day"] = 3
save("folktails-hard.json", fthard)

def careless(d, name, faction_note):
    d = copy.deepcopy(d)
    p = d["playtest"]
    p["name"] = name
    p["note"] = ("Typical new-player mistakes: no water storage at all, one crop only, too few homes (three), no second farm. "
                 + faction_note)
    drop = {"tank1", "tank2", "tank3", "tankM1", "tankM2", "field1c", "field1b", "farm2", "field2", "farm3", "field3", "home2", "whCabbage", "pickler1", "whPickles"}
    keep = []
    for s in p["steps"]:
        if s["id"] in drop: continue
        if s["id"] == "home": s["repeat"] = 3
        keep.append(s)
    p["steps"] = keep
    return d

save("inkpaws-careless.json", careless(std, "inkpaws-careless", "Inkpaws: shoot bamboo only."))
save("folktails-careless.json", careless(ft, "folktails-careless", "Folktails: carrots only."))
