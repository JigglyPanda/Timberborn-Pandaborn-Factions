"""The proposed first-pass Inkpaws stat sheet (design revision 4), as data.

The model reads these numbers; `run.py sheet` writes them as Markdown tables (docs/tech/balance.md) and as
`tools/sim/out/statsheet.json`, one entry per catalogue item, for the catalogue generator.

Basis per field:  M = derived from the model (scenario in brackets)   V = copied from the vanilla analogue named in
`basis_template`   G = a guess, to be tuned in play.
Field names follow vanilla spec fields where one exists.
"""
from . import vanilla as V
from .mech import Species, rested_bonus_linear

# =====================================================================================================================
# Colonists
# =====================================================================================================================
REST_BONUS = dict(full_at_hours=12, zero_at_hours=16, bonus=1 / 3, applies_to=["WorkingSpeed", "MovementSpeed"],
                  form="multiplies the colonist's whole multiplier (code: delta = bonus x current multiplier)")


def inkpaw_bonus(hours):
    return rested_bonus_linear(hours, REST_BONUS["full_at_hours"], REST_BONUS["zero_at_hours"], REST_BONUS["bonus"])


INKPAW_LIFT = 18
INKPAW = Species("Inkpaw", lift=INKPAW_LIFT, rested=inkpaw_bonus)
RINGTAIL_LIFT = 14
RINGTAIL = Species("Ringtail", lift=RINGTAIL_LIFT, rested=inkpaw_bonus, slow=V.tiles_per_hour(V.WALK_TILES_PER_S))
OX = Species("Wooden Ox", walk=V.tiles_per_hour(1.8), slow=V.tiles_per_hour(0.9), lift=40, ignores_hours=True,
             fixed_ws=1.65, fixed_mv=1.3, lifespan=90)

COLONISTS = [
    dict(stat="BaseWalkingSpeed (tiles/s)", spec="WalkerSpeedManagerSpec", Inkpaw=2.7, Ringtail=2.7, Folktail=2.7,
         basis="V"),
    dict(stat="BaseSlowedSpeed (tiles/s)", spec="WalkerSpeedManagerSpec", Inkpaw=1.35, Ringtail=2.7,
         Folktail=1.35, basis="V (Inkpaw) · design (Ringtail: no slowing when loaded)"),
    dict(stat="BaseLiftingCapacity", spec="GoodCarrierSpec", Inkpaw=18, Ringtail=14, Folktail=14,
         basis="M (q1: 3 logs and 6 poles a trip; q5: a Ringtail at 14 equals an Inkpaw builder at 12/12)"),
    dict(stat="Rested bonus, WorkingSpeed and MovementSpeed", spec="code (decorator)",
         Inkpaw="+33% at <=12 h, linear to 0 at 16 h, by the bell", Ringtail="same curve, by the Ringtail shift (24 - bell)",
         Folktail="-", basis="M (q2)"),
    dict(stat="Working hours", spec="new-game slider", Inkpaw="dawn to the bell; starts at 16", Ringtail="bell to dawn",
         Folktail="16", basis="design · M (q2, q5)"),
    dict(stat="Life (days at wellbeing < 7)", spec="LifeService (global)", Inkpaw=50, Ringtail=50, Folktail=50,
         basis="V · M (q6: no change needed)"),
    dict(stat="Childhood (days at wellbeing < 5)", spec="LifeService (global)", Inkpaw=6, Ringtail=6, Folktail=6,
         basis="V"),
    dict(stat="Hunger, Thirst, Sleep", spec="Need.Beaver.*", Inkpaw="vanilla", Ringtail="vanilla", Folktail="vanilla",
         basis="V"),
    dict(stat="Births", spec="ProcreationHouseSpec / nursery", Inkpaw="0.1875 per den entry (vanilla)",
         Ringtail="Moon Loft: 0.1875 per entry while Ringtail jobs > Ringtail adults + kits", Folktail="0.1875",
         basis="V · M (q6)"),
]

# =====================================================================================================================
# Plants. Field names: GrowableSpec.GrowthTimeInDays, PlantableSpec.PlantTimeInHours, Yielder.Yield,
# Yielder.RemovalTimeInHours, GatherableSpec.YieldGrowthTimeInDays, WateredNaturalResourceSpec.DaysToDieDry,
# FloodableNaturalResourceSpec (Min/MaxWaterHeight, DaysToDie), ReproducibleSpec.ReproductionChance.
# =====================================================================================================================
PLANTS = [
    dict(id="PandabornShootBamboo", template="PandabornShootBamboo.Inkpaws", kind="crop", basis_template="Carrot",
         planter="Farmstead (Farmhouse group)", zone="moist", PlantTimeInHours=0.2, GrowthTimeInDays=3,
         harvest="PandabornBambooShoots x2", RemovalTimeInHours=1.0, DaysToDieDry=5, Water="0/0, DaysToDie 2",
         ReproductionChance=0,
         basis=dict(GrowthTimeInDays="M q1", Yield="M q1", DaysToDieDry="M q1/q4", PlantTimeInHours="V",
                    RemovalTimeInHours="G", Water="V"),
         model=dict(plant_h=0.2, grow_d=3, yield_n=2, harvest_h=1.0, dry_d=5)),
    dict(id="PandabornCabbage", template="PandabornCabbage.Inkpaws", kind="crop", basis_template="Carrot",
         planter="Farmstead", zone="moist", PlantTimeInHours=0.2, GrowthTimeInDays=5, harvest="PandabornCabbage x3",
         RemovalTimeInHours=1.2, DaysToDieDry=7, Water="0/0, DaysToDie 2", ReproductionChance=0,
         basis=dict(GrowthTimeInDays="M q3", Yield="M q3", DaysToDieDry="M q1", PlantTimeInHours="V",
                    RemovalTimeInHours="V"),
         model=dict(plant_h=0.2, grow_d=5, yield_n=3, harvest_h=1.2, dry_d=7)),
    dict(id="PandabornTimberBamboo", template="PandabornTimberBamboo.Inkpaws", kind="tree", basis_template="Birch",
         planter="Forester", zone="moist", PlantTimeInHours=0.5, GrowthTimeInDays=5,
         harvest="cut: PandabornPole x2 (CuttableSpec, RemoveOnCut false like trees); gather: "
                 "PandabornBambooMushrooms x2 every 3 d (pick 0.5 h)",
         RemovalTimeInHours=1.5, DaysToDieDry=7, Water="0/0, DaysToDie 8", ReproductionChance=0.03,
         basis=dict(GrowthTimeInDays="M q1", Yield="M q1/q8", DaysToDieDry="M q1", PlantTimeInHours="V",
                    RemovalTimeInHours="M q8", Mushrooms="G", ReproductionChance="V"),
         model=dict(plant_h=0.5, grow_d=5, poles=2, cut_h=1.5, dry_d=7, mushrooms=2, mushroom_d=3, pick_h=0.5)),
    dict(id="PandabornRice", template="PandabornRice.Inkpaws", kind="crop", basis_template="Cattail",
         planter="Paddy House (aquatic group)", zone="flooded", PlantTimeInHours=0.2, GrowthTimeInDays=8,
         harvest="PandabornRice x3", RemovalTimeInHours=1.2, DaysToDieDry=1, Water="1/1, DaysToDie 1.5",
         ReproductionChance=0, basis=dict(GrowthTimeInDays="V (Cattail)", Yield="V", Water="M q4"),
         model=dict(plant_h=0.2, grow_d=8, yield_n=3, harvest_h=1.2, dry_d=1)),
    dict(id="PandabornTeaBush", template="PandabornTeaBush.Inkpaws", kind="bush (arid)", basis_template="Blueberry",
         planter="Farmstead (dry ground)", zone="dry", PlantTimeInHours=0.4, GrowthTimeInDays=6,
         harvest="gather: PandabornTeaLeaves x3 every 3 d", RemovalTimeInHours=0.6, DaysToDieDry="-",
         Water="arid: dies 2 d after its soil turns moist", ReproductionChance=0,
         basis=dict(Yield="M q4", GrowthTimeInDays="G", PlantTimeInHours="V", Water="design"),
         model=dict(plant_h=0.4, grow_d=6, fruit=3, regrow_d=3, pick_h=0.6)),
    dict(id="PandabornSichuanPepper", template="PandabornSichuanPepper.Inkpaws", kind="crop (arid)",
         basis_template="Sunflower", planter="Farmstead (dry ground)", zone="dry", PlantTimeInHours=0.2,
         GrowthTimeInDays=5, harvest="PandabornSichuanPepper x2", RemovalTimeInHours=1.2, DaysToDieDry="-",
         Water="arid: dies 2 d after its soil turns moist", ReproductionChance=0,
         basis=dict(Yield="M q3", GrowthTimeInDays="V (Sunflower)"),
         model=dict(plant_h=0.2, grow_d=5, yield_n=2, harvest_h=1.2)),
    dict(id="PandabornPersimmonTree", template="PandabornPersimmonTree.Inkpaws", kind="tree",
         basis_template="ChestnutTree", planter="Forester", zone="moist", PlantTimeInHours=0.75, GrowthTimeInDays=14,
         harvest="gather: PandabornPersimmons x3 every 6 d (pick 1.0 h); cut: Log x3", RemovalTimeInHours=1.2,
         DaysToDieDry=10, Water="0/0, DaysToDie 10", ReproductionChance=0.01,
         basis=dict(all="V (Chestnut) with growth M q3"),
         model=dict(plant_h=0.75, grow_d=14, fruit=3, regrow_d=6, pick_h=1.0, logs=3, cut_h=1.2, dry_d=10)),
]


def plant_model(pid):
    return next(p["model"] for p in PLANTS if p["id"] == pid)


# =====================================================================================================================
# Goods. Weight, type and ConsumptionEffects as GoodSpec. dish = FavorableWellbeing of the dish's own need.
# =====================================================================================================================
GOODS = [
    dict(id="PandabornBambooShoots", GoodType="Box", Weight=1, ConsumptionEffects={"Hunger": 0.3}, dish=0,
         basis="V (Berries): the raw staple carries no dish need"),
    dict(id="PandabornCabbage", GoodType="Box", Weight=1, ConsumptionEffects={"Hunger": 0.3, "PandabornCabbage": 0.2},
         dish=1, basis="V (Carrot)"),
    dict(id="PandabornPersimmons", GoodType="Box", Weight=1,
         ConsumptionEffects={"Hunger": 0.3, "PandabornPersimmons": 0.2}, dish=1, basis="V (Carrot)"),
    dict(id="PandabornBambooMushrooms", GoodType="Box", Weight=1,
         ConsumptionEffects={"Hunger": 0.3, "PandabornBambooMushrooms": 0.2}, dish=1, basis="V"),
    dict(id="PandabornSteamedShoots", GoodType="Box", Weight=1,
         ConsumptionEffects={"Hunger": 0.3, "PandabornSteamedShoots": 0.2}, dish=1, basis="M q3"),
    dict(id="PandabornPickles", GoodType="Box", Weight=1, ConsumptionEffects={"Hunger": 0.3, "PandabornPickles": 0.2},
         dish=2, basis="V (Grilled Potato)"),
    dict(id="PandabornSteamedRice", GoodType="Box", Weight=1,
         ConsumptionEffects={"Hunger": 0.3, "PandabornSteamedRice": 0.2}, dish=2, basis="V (Bread)"),
    dict(id="PandabornSweetRiceBalls", GoodType="Box", Weight=1,
         ConsumptionEffects={"Hunger": 0.3, "PandabornSweetRiceBalls": 0.2}, dish=2, basis="V (Cattail Cracker)"),
    dict(id="PandabornHotPot", GoodType="Box", Weight=1, ConsumptionEffects={"Hunger": 0.3, "PandabornHotPot": 0.2},
         dish=3, basis="V (Maple Pastry)"),
    dict(id="PandabornBambooSeedCakes", GoodType="Box", Weight=1,
         ConsumptionEffects={"Hunger": 0.3, "PandabornBambooSeedCakes": 0.2}, dish=3, basis="M q7"),
    dict(id="PandabornTea", GoodType="Liquid", Weight=2, ConsumptionEffects={"Thirst": 0.2, "PandabornTea": 0.3},
         dish=2, basis="M q4 (Tea need non-wastable: about 2 cups a day)"),
    dict(id="PandabornRice", GoodType="Box", Weight=1, ConsumptionEffects={}, dish=0, basis="V (Wheat)"),
    dict(id="PandabornRiceFlour", GoodType="Box", Weight=2, ConsumptionEffects={}, dish=0, basis="V (Wheat Flour)"),
    dict(id="PandabornSichuanPepper", GoodType="Box", Weight=1, ConsumptionEffects={}, dish=0,
         basis="M q3: never edible"),
    dict(id="PandabornTeaLeaves", GoodType="Box", Weight=1, ConsumptionEffects={}, dish=0, basis="V"),
    dict(id="PandabornBambooSeed", GoodType="Box", Weight=1, ConsumptionEffects={}, dish=0, basis="M q7"),
    dict(id="PandabornPole", GoodType="Pileable", Weight=3, ConsumptionEffects={}, dish=0,
         basis="V (Plank): keeps the rename option open; lift 18 makes it light"),
    dict(id="PandabornCuredPole", GoodType="Pileable", Weight=4, ConsumptionEffects={}, dish=0,
         basis="V (Treated Plank)"),
    dict(id="PandabornPaperLantern", GoodType="Box", Weight=1, ConsumptionEffects={}, dish=0, basis="G"),
]

# =====================================================================================================================
# Recipes (RecipeSpec). CycleDurationInHours at working speed 1; CyclesCapacity sets buffers (4.3).
# =====================================================================================================================
RECIPES = [
    dict(id="PandabornSteamedShoots", building="Steamer", CycleDurationInHours=0.5,
         Ingredients={"PandabornBambooShoots": 1}, Products={"PandabornSteamedShoots": 2}, CyclesCapacity=30,
         Fuel="Log, 1 per 10 cycles", power=0, ratio=2, cycle_h=0.5,
         basis="M q1/q3 (ratio) · V (Grill: fuel, buffer)"),
    dict(id="PandabornSteamedRice", building="Steamer", CycleDurationInHours=1.0,
         Ingredients={"PandabornRice": 1}, Products={"PandabornSteamedRice": 4}, CyclesCapacity=30,
         Fuel="Log, 1 per 10 cycles", power=0, ratio=4, cycle_h=1.0, basis="M q3 · V (Bread)"),
    dict(id="PandabornPickles", building="Pickle Yard", CycleDurationInHours=1.0,
         Ingredients={"PandabornCabbage": 1}, Products={"PandabornPickles": 3}, CyclesCapacity=20, Fuel="",
         power=0, ratio=3, cycle_h=1.0, basis="M q3 (one cabbage makes several)"),
    dict(id="PandabornRiceFlour", building="Trip-Hammer Mill", CycleDurationInHours=0.5,
         Ingredients={"PandabornRice": 1}, Products={"PandabornRiceFlour": 1}, CyclesCapacity=20,
         Fuel="", power="flowing water (own wheel)", ratio=1, cycle_h=0.5, basis="V (Gristmill)"),
    dict(id="PandabornSweetRiceBalls", building="Kitchen", CycleDurationInHours=1.0,
         Ingredients={"PandabornRiceFlour": 1, "PandabornPersimmons": 1}, Products={"PandabornSweetRiceBalls": 5},
         CyclesCapacity=20, Fuel="Log, 1 per 10 cycles", power=0, ratio=5, cycle_h=1.0,
         basis="V (Maple Pastry shape) · M q3"),
    dict(id="PandabornBambooSeedCakes", building="Kitchen", CycleDurationInHours=1.5,
         Ingredients={"PandabornBambooSeed": 1, "PandabornRiceFlour": 1}, Products={"PandabornBambooSeedCakes": 4},
         CyclesCapacity=20, Fuel="Log, 1 per 10 cycles", power=0, ratio=4, cycle_h=1.5, basis="M q7"),
    dict(id="PandabornHotPot", building="Hot Pot Hall", CycleDurationInHours=1.5,
         Ingredients={"PandabornCabbage": 1, "PandabornSichuanPepper": 1, "PandabornBambooMushrooms": 1},
         Products={"PandabornHotPot": 8}, CyclesCapacity=15, Fuel="Log, 1 per 10 cycles", power=0, ratio=8,
         cycle_h=1.5, basis="M q3"),
    dict(id="PandabornTea", building="Tea Roastery", CycleDurationInHours=0.75,
         Ingredients={"PandabornTeaLeaves": 1, "Water": 1}, Products={"PandabornTea": 3}, CyclesCapacity=20,
         Fuel="", power=0, ratio=3, cycle_h=0.75, basis="design (3 cups per water) · M q4"),
    dict(id="Paper (from poles)", building="Paper Mill", CycleDurationInHours=1.56,
         Ingredients={"PandabornPole": 1}, Products={"Paper": 2}, CyclesCapacity=10, Fuel="", power=80, ratio=2,
         cycle_h=1.56, basis="V (Paper, pole for log)"),
    dict(id="PandabornPaperLantern", building="Lantern Workshop", CycleDurationInHours=1.5,
         Ingredients={"Paper": 2, "PandabornPole": 1}, Products={"PandabornPaperLantern": 2}, CyclesCapacity=10,
         Fuel="", power=0, ratio=1, cycle_h=1.5, basis="M q7 (Small Festival in cycle 2)"),
    dict(id="PandabornCuredPole", building="Smoke Kiln", CycleDurationInHours=3.0,
         Ingredients={"PandabornPole": 1}, Products={"PandabornCuredPole": 1}, CyclesCapacity=10,
         Fuel="Log, 1 per 4 cycles", power=0, ratio=1, cycle_h=3.0,
         basis="V (Treated Plank: 3 h) · M q8 (log smoke instead of resin and 250 hp)"),
    dict(id="Gear", building="Gear Workshop", CycleDurationInHours=3.0, Ingredients={"PandabornPole": 1},
         Products={"Gear": 1}, CyclesCapacity=10, Fuel="", power=120, ratio=1, cycle_h=3.0, basis="V"),
    dict(id="Water", building="Water Pump", CycleDurationInHours=0.33, Ingredients={}, Products={"Water": 1},
         CyclesCapacity=15, Fuel="", power=0, ratio=1, cycle_h=0.33, basis="V"),
    dict(id="PandabornDewWater", building="Dew Collector", CycleDurationInHours=12.0, Ingredients={},
         Products={"Water": 1}, CyclesCapacity=4, Fuel="", power=0, ratio=1, cycle_h=12.0,
         basis="M q4: 2 a day; DewLimiter DroughtEfficiency 0.33, and efficiency / (collectors within 6 tiles)"),
    dict(id="PandabornCisternTap", building="Cistern Tap", CycleDurationInHours=1.0, Ingredients={"Water": 1},
         Products={"0.2 m3 into the flume": 1}, CyclesCapacity=5, Fuel="", power=0, ratio=1, cycle_h=1.0,
         basis="V (Discharge: 3 Water/h) · M q4 (1 Water/h keeps a 10-tile strip)"),
    dict(id="PandabornWoodenOx", building="Ox Workshop", CycleDurationInHours=72.0,
         Ingredients={"PandabornCuredPole": 10, "Gear": 15, "MetalBlock": 2}, Products={"Wooden Ox": 1},
         CyclesCapacity=1, Fuel="", power=250, ratio=1, cycle_h=72, basis="M q8 (vanilla bot parts, one building)"),
    dict(id="SciencePointsStarTower", building="Star Tower", CycleDurationInHours=4.0, Ingredients={},
         Products={"Science": 12}, CyclesCapacity=1, Fuel="", power=0, ratio=12, cycle_h=4.0,
         basis="V (Observatory, 4 workers, no power) · M q5"),
]


def recipe(rid):
    return next(r for r in RECIPES if r["id"] == rid)


# =====================================================================================================================
# Needs (NeedSpec). Shared vanilla needs keep vanilla values.
# =====================================================================================================================
NEEDS = [
    dict(id="PandabornNap", group="Fun", DailyDelta=-0.6, MaximumValue=1, FavorableWellbeing=2,
         ImportanceMultiplier=1.2, Wastable=False, satisfied_by="Hammock (1 seat), Nap Platform (6 seats): +0.6/h",
         rhythm="daily: one 1-hour visit", basis="M q2"),
    dict(id="PandabornTea", group="Nutrition", DailyDelta=-0.6, MaximumValue=1, FavorableWellbeing=2,
         ImportanceMultiplier=1.0, Wastable=False, satisfied_by="PandabornTea +0.3 a cup (about 2 a day)",
         rhythm="daily, on ordinary drinking trips", basis="M q4"),
    dict(id="PandabornTeahouse", group="SocialLife", DailyDelta=-0.15, MaximumValue=1, FavorableWellbeing=2,
         ImportanceMultiplier=1.0, Wastable=False, satisfied_by="Teahouse +0.6/h, 12 seats", rhythm="every 3-4 days",
         basis="V (Domed Garden) · M q2 capacity"),
    dict(id="PandabornPlay", group="Fun", DailyDelta=-0.2, MaximumValue=1, FavorableWellbeing=2,
         ImportanceMultiplier=1.0, Wastable=False, satisfied_by="Slide and Swing +0.6/h, 8 seats",
         rhythm="every 3 days", basis="V (Lido) · M"),
    dict(id="PandabornCubWatching", group="SocialLife", DailyDelta=-0.2, MaximumValue=1, FavorableWellbeing=3,
         ImportanceMultiplier=1.0, Wastable=False, satisfied_by="Panda Kindergarten +0.6/h, 12 seats",
         rhythm="every 3 days", basis="V (Agora) · M"),
    dict(id="PandabornSoak", group="Fun", DailyDelta=-0.2, MaximumValue=1, FavorableWellbeing=3,
         ImportanceMultiplier=1.0, Wastable=False, satisfied_by="Hot Spring Bath +0.6/h, 8 seats (+WetFur)",
         rhythm="every 3 days", basis="V (Mud Pit) · M"),
    dict(id="PandabornContemplation", group="Fun", DailyDelta=-0.12, MaximumValue=1, FavorableWellbeing=2,
         ImportanceMultiplier=1.0, Wastable=False, satisfied_by="Ink Studio +0.6/h, 4 seats", rhythm="weekly",
         basis="V (Contemplation Spot)"),
    dict(id="PandabornPerformance", group="Fun", DailyDelta=-0.12, MaximumValue=1, FavorableWellbeing=5,
         ImportanceMultiplier=1.0, Wastable=False, satisfied_by="Opera Stage +0.6/h, 20 seats, while performers work",
         rhythm="weekly", basis="V (Dance Hall)"),
    dict(id="Pandaborn<Dish> (nine)", group="Nutrition", DailyDelta=-0.05, MaximumValue=1,
         FavorableWellbeing="see goods", ImportanceMultiplier=1.0, Wastable=True, satisfied_by="+0.2 a unit",
         rhythm="a bite every 4 days", basis="V (Need.Beaver.Bread)"),
    dict(id="PandabornFestive", group="Boosts", DailyDelta=-0.05, MaximumValue=1, FavorableWellbeing=4,
         ImportanceMultiplier=1.0, Wastable=True, satisfied_by="A Lantern Festival sets it to 1 (Grand: and +1 wb)",
         rhythm="20 days, most of a cycle", basis="M q7"),
    dict(id="PandabornMemorialArch / GreatSittingPanda / SkyLantern", group="Awe", DailyDelta=-0.3,
         MaximumValue=1, FavorableWellbeing="6 / 12 / 10", ImportanceMultiplier=1.0, Wastable=True,
         satisfied_by="ranged 0.1/h (wonder 10/h)", rhythm="3 h a day in range", basis="V (Awe) · M q8"),
]

# Wellbeing ceilings by need group (3.3). Inkpaws: Nutrition 13 dishes + 3 seed cakes + 2 tea.
CEILING = dict(
    Inkpaws=dict(Basic=5, Nutrition=18, Social=6, Fun=14, Aesthetics=10, Awe=28, Boosts=4),
    Folktails=dict(Basic=5, Nutrition=15, Social=13, Fun=12, Aesthetics=9, Awe=30, Boosts=0),
)

# =====================================================================================================================
# Buildings. One entry per catalogue item. cost: BuildingSpec.BuildingCost; science: ScienceCost;
# workers: WorkplaceSpec Max (default); who: I / R / -.
# A re-themed building copies its basis_template with Plank -> PandabornPole and TreatedPlank -> PandabornCuredPole
# unless the row says otherwise.
# =====================================================================================================================
def B(id, basis_template, who, cost, science, workers, recipes=(), capacity="", basis="V", note=""):
    return dict(id=id, basis_template=basis_template, who=who, cost=cost, science=science, workers=workers,
                recipes=list(recipes), capacity=capacity, basis=basis, note=note)


L, P, CP, G, MB, PA = "Log", "PandabornPole", "PandabornCuredPole", "Gear", "MetalBlock", "Paper"

BUILDINGS = [
    # village and logistics
    B("PandabornVillageHall", "DistrictCenter.Folktails", "I", {}, 0, "4 (2)", capacity="builders; 20 storage"),
    B("BuildersHut", "BuildersHut.Folktails", "I", {L: 20, P: 10}, 100, "4 (4)"),
    B("HaulingPost", "HaulingPost.Folktails", "I", {L: 20, P: 10}, 0, "10 (5)", capacity="CarryingCapacity +1"),
    B("DistrictCrossing", "DistrictCrossing.Folktails", "I", {L: 30, P: 15}, 600, "10 (4)"),
    B("PandabornFestivalSquare", "new", "-", {L: 30, P: 30, PA: 10}, 300, 0,
      capacity="holds 40 lanterns, 60 dishes, 20 fireworks", basis="M q7 (reachable in cycle 2)"),
    # homes
    B("PandabornDen", "Lodge.Folktails", "-", {L: 12}, 0, "-", capacity="3 (2 adults, 1 child)"),
    B("PandabornCourtyardHouse", "DoubleLodge.Folktails", "-", {L: 20}, 150, "-", capacity="6 (4, 2)"),
    B("PandabornTerraceHouse", "TripleLodge.Folktails", "-", {L: 25, P: 10}, 250, "-", capacity="9 (6, 3), stackable",
      basis="V · M (poles for the stackable frame)"),
    B("PandabornMoonLoft", "new (Lodge)", "-", {L: 10, P: 10}, 200, "-",
      capacity="4 (3 adults, 1 kit slot); a kit is born only while open Ringtail jobs > Ringtail adults + kits; the first loft brings 3 adults + 1 kit",
      basis="M q5/q6"),
    # food
    B("GathererFlag", "GathererFlag.Folktails", "I", {}, 0, 1, capacity="20; berries, persimmons, mushrooms"),
    B("PandabornFarmstead", "EfficientFarmHouse.Folktails", "I", {L: 25}, 0, 3,
      capacity="50; shoot bamboo, cabbage; tea and pepper on dry ground"),
    B("PandabornSteamer", "Grill.Folktails", "I", {L: 20, P: 5}, 40, 1,
      ["PandabornSteamedShoots", "PandabornSteamedRice"], basis="M q1/q3"),
    B("PandabornPickleYard", "new", "I", {L: 20, P: 15}, 120, 1, ["PandabornPickles"], basis="M q3"),
    B("PandabornPaddyHouse", "AquaticFarmhouse.Folktails", "I", {L: 30, P: 10}, 150, 2, capacity="50; rice"),
    B("PandabornTeaRoastery", "new", "I", {L: 15, P: 20}, 250, 1, ["PandabornTea"], basis="M q4"),
    B("PandabornTripHammerMill", "Gristmill.Folktails", "I", {L: 30, P: 20, G: 10}, 200, 1, ["PandabornRiceFlour"],
      capacity="runs on flowing water at its wheel, no shafts", basis="V · G (cheaper: no power plant)"),
    B("PandabornKitchen", "Bakery.Folktails", "I", {L: 15, P: 15, G: 10}, 300, 1,
      ["PandabornSweetRiceBalls", "PandabornBambooSeedCakes"]),
    B("PandabornHotPotHall", "new", "I", {L: 40, P: 40, G: 20}, 800, 1, ["PandabornHotPot"], basis="M q3"),
    # wood and materials
    B("LumberjackFlag", "LumberjackFlag.Folktails", "I", {}, 0, 1),
    B("Forester", "Forester.Folktails", "I", {L: 12}, 0, 1, basis="M q1 (log-only: built before the first pole)"),
    B("GearWorkshop", "GearWorkshop.Folktails", "I", {L: 15, P: 25}, 100, 1, ["Gear"]),
    B("PaperMill", "PaperMill.Folktails", "I", {L: 40, P: 40, G: 15}, 250, 1, ["Paper (from poles)"]),
    B("PandabornLanternWorkshop", "new", "I", {L: 10, P: 20}, 200, 1, ["PandabornPaperLantern"], basis="M q7"),
    B("PandabornSmokeKiln", "WoodWorkshop.Folktails", "I", {L: 20, P: 40, G: 20}, 600, 1, ["PandabornCuredPole"],
      basis="M q8 (no power, so cheaper than the Wood Workshop)"),
    B("ExplosivesFactory", "ExplosivesFactory.Folktails", "I", {P: 30, G: 30, MB: 30}, 400, 1),
    # metal
    B("ScavengerFlag", "ScavengerFlag.Folktails", "I", {}, 250, 1),
    B("Smelter", "Smelter.Folktails", "I", {P: 50, G: 20, "ScrapMetal": 30}, 300, 1),
    B("Mine", "Mine.Folktails", "I", {L: 250, G: 350, CP: 200}, 4000, 10),
    # water
    B("WaterPump", "WaterPump.Folktails", "I", {L: 12}, 0, 1, ["Water"]),
    B("PandabornCisternSmall", "SmallTank.Folktails", "-", {L: 15}, 0, "-", capacity=40, basis="M q4"),
    B("PandabornCisternMedium", "MediumTank.Folktails", "-", {L: 20, P: 30}, 100, "-", capacity=300,
      basis="M q4 (no gears: reachable before the first drought)"),
    B("PandabornCisternLarge", "LargeTank.Folktails", "-", {P: 80, G: 40, MB: 20}, 500, "-", capacity=1200,
      basis="V · M"),
    B("PandabornFlume", "new (ThrottlingValve cell)", "-", {P: 2}, 60, "-", capacity="per tile", basis="G"),
    B("PandabornFlumeCorner", "new", "-", {P: 3}, 60, "-", basis="G"),
    B("PandabornFlumeDrop", "new", "-", {P: 3}, 60, "-", basis="G"),
    B("PandabornFlumeBridge", "new", "-", {P: 4, L: 1}, 120, "-", capacity="per tile", basis="G"),
    B("PandabornFlumeGate", "FillValve.Folktails", "-", {L: 6, P: 6}, 80, "-",
      capacity="sets flow; shuts at contamination >= 0.05", basis="G · design"),
    B("PandabornScoopWheel", "new", "-", {L: 20, P: 30, G: 5}, 250, "-", capacity="lifts 1 block; needs flow >= 0.15",
      basis="G (prototype measures)"),
    B("PandabornPaddySpout", "FillValve.Folktails", "-", {P: 6}, 150, "-", capacity="holds 0.3 deep", basis="G"),
    B("PandabornCisternTap", "Discharge.Folktails", "-", {L: 8, P: 8}, 250, "-", ["PandabornCisternTap"],
      capacity="1 Water an hour into a flume; no workers", basis="M q4"),
    B("PandabornDewCollector", "new", "-", {P: 15, PA: 4}, 300, "-", ["PandabornDewWater"],
      capacity="buffer 4; footprint 2x2; 2 Water a day, 2/3 in drought, shared with collectors within 6 tiles", basis="M q4"),
    B("PandabornTreadwheelLift", "new", "I", {P: 30, G: 10}, 300, 1, capacity="lifts 1 block", basis="G"),
    B("PandabornDryStoneWall", "Levee.Folktails", "-", {L: 4, "Dirt": 2}, 120, "-",
      capacity="blocks moisture like an impermeable floor, sideways", basis="G"),
    # power
    B("PandabornBambooWaterWheel", "WaterWheel.Folktails", "-", {L: 30, P: 15}, 0, "-", capacity="270 hp x flow"),
    B("PowerWheel", "PowerWheel.Folktails", "I", {L: 20}, 0, 1, capacity="50 hp"),
    B("PandabornKiteWindmill", "WindTurbine.Folktails", "-", {L: 20, P: 20}, 120, "-", capacity="150 hp"),
    B("PandabornLargeKiteWindmill", "LargeWindTurbine.Folktails", "-", {P: 40, G: 20, PA: 30}, 1400, "-",
      capacity="300 hp"),
    # science and oxen
    B("Inventor", "Inventor.Folktails", "I", {L: 12}, 0, 1, ["SciencePoints"]),
    B("PandabornStarTower", "Observatory.Folktails", "R", {P: 60, G: 30, PA: 10}, 1000, 4,
      ["SciencePointsStarTower"], capacity="no power (stars, not machines)", basis="V · M q5"),
    B("PandabornOxWorkshop", "BotAssembler.Folktails", "I", {P: 100, G: 50, MB: 40}, 1000, 2, ["PandabornWoodenOx"],
      capacity="250 hp; all parts in one building", basis="M q8"),
    # Ringtail workplaces
    B("PandabornNightBuildersPost", "BuildersHut.Folktails", "R", {L: 15, P: 10}, 0, "4 (4)",
      capacity="unlocked by the first Moon Loft", basis="M q5"),
    B("PandabornNightCourierPost", "HaulingPost.Folktails", "R", {L: 20, P: 10}, 150, "6 (3)",
      capacity="CarryingCapacity +1", basis="M q5"),
    B("PandabornNightForagersPost", "GathererFlag.Folktails", "R", {P: 10}, 100, "2 (2)",
      capacity="30; mushrooms first", basis="M q5"),
    B("PandabornOperaStage", "DanceHall.Folktails", "R", {L: 100, CP: 40, MB: 20}, 1200, "2 (2)",
      capacity="20 seats; open while performers work", basis="V · M q5"),
    # leisure
    B("Campfire", "Campfire.Folktails", "-", {L: 15}, 0, "-", capacity="5 seats"),
    B("PandabornHammock", "Hammock.Folktails", "-", {L: 4}, 0, "-", capacity="1 seat, Nap +0.6/h",
      basis="M q2 (log-only: buildable on day 1)"),
    B("PandabornNapPlatform", "RooftopTerrace.Folktails", "-", {L: 10, P: 15}, 100, "-",
      capacity="6 seats, Nap +0.6/h, stackable", basis="M q2"),
    B("PandabornTeahouse", "DomedGarden.Folktails", "-", {L: 25, P: 25}, 150, "-",
      capacity="12 seats; stocks 30 Tea", basis="M q2/q4"),
    B("PandabornSlideAndSwing", "Lido.Folktails", "-", {L: 25, P: 20}, 250, "-", capacity="8 seats"),
    B("PandabornKindergarten", "Agora.Folktails", "-", {L: 60, P: 40}, 400, "-",
      capacity="12 adult seats + cubs' play", basis="V · M"),
    B("PandabornInkStudio", "ContemplationSpot.Folktails", "-", {L: 10, PA: 10}, 200, "-", capacity="4 seats"),
    B("PandabornHotSpringBath", "MudPit.Folktails", "-", {L: 60, CP: 30, "Dirt": 20}, 1500, "-", capacity="8 seats"),
    B("TeethGrindstone / MedicalBed / Herbalist / Shower", "vanilla", "-", "vanilla", "vanilla", "vanilla"),
    # monuments and wonder
    B("PandabornMemorialArch", "BrazierOfBonding.Folktails", "-", {L: 250, P: 800}, 3000, "-",
      capacity="Awe +6, radius 10", basis="M q8 (labour of Farmer Monument + Brazier)"),
    B("PandabornGreatSittingPanda", "HallOfAbundance.Folktails", "-", {P: 1400, CP: 700, MB: 650}, 15000, "-",
      capacity="Awe +12, radius 30", basis="M q8 (labour of Fountain + Hall)"),
    B("PandabornSkyLantern", "EarthRecultivator.Folktails", "-", {G: 2400, CP: 2400, MB: 1800, PA: 500}, 20000,
      "10 (crew)", capacity="build 15000 h, 40 builders; fill 500 Paper Lanterns + 500 Tea",
      basis="V · M q8"),
]

# =====================================================================================================================
# Events
# =====================================================================================================================
FLOWERING = dict(first_cycle=6, every_cycles="5-7 (alternating shoot, timber; first is shoot bamboo)",
                 announce="at the start of the cycle before: buds show, about 15-20 days", never_in="drought, badtide",
                 when="the first day of a temperate season; plants die over 2 days",
                 seed="each flowering plant drops 3 PandabornBambooSeed when cleared (gathered or cut)",
                 replant="that bamboo cannot be replanted until the next temperate season (code: planting check)",
                 reserve="shoot year: ~14 food per colonist (40 colonists: 560); timber year: ~5 poles per colonist",
                 setting="off / rare (every 9-11 cycles) / normal", basis="M q7")
FESTIVAL = dict(small="40 Paper Lanterns + 20 each of three cooked dishes", grand="adds 20 Fireworks",
                cost="everyone off duty from dawn to the next dawn", festive="PandabornFestive (+4) set to 1, decay 0.05: "
                "20 days; Grand adds 1 more wellbeing while it lasts", once_per_cycle=True, basis="M q7")
OX_STATS = dict(walk_tiles_s=1.8, lift=40, life_days=90, hours=24, needs="none (bot tier 0: work x1.65, walk x1.3)",
                cost="10 Cured Pole + 15 Gear + 2 Metal Block, 72 h at the Ox Workshop", basis="M q8")
