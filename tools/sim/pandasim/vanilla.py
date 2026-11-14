"""Vanilla Timberborn 1.1.2.8 numbers.

Every number here is copied from docs/tech/game-mechanics.md (section in the comment) or from a vanilla blueprint
in E:/PandabornDev/reference/Blueprints. Nothing in this file is a proposal.
"""
from dataclasses import dataclass, field

# --- time and movement (2.4) -------------------------------------------------------------------------------------
REAL_SECONDS_PER_GAME_HOUR = 19.2
WALK_TILES_PER_S = 2.7              # adult beaver and bot
SLOWED_TILES_PER_S = 1.35           # anyone carrying anything
CHILD_TILES_PER_S = 1.35
DEFAULT_WORK_HOURS = 16             # 1.2
NEW_GAME_HOUR = 4                   # 1.1: a new game starts at hour 4 of day 1

def tiles_per_hour(tiles_per_s):
    return tiles_per_s * REAL_SECONDS_PER_GAME_HOUR

# --- lifting (2.5) -------------------------------------------------------------------------------------------------
BEAVER_LIFT = 14
BOT_LIFT = 20
HAULER_CARRY_BONUS = 1.0            # Hauling Post / District Crossing: CarryingCapacity +1.0 -> x2

WEIGHT = {  # GoodSpec.Weight [data]
    "Berries": 1, "Carrot": 1, "Bread": 1, "Wheat": 1, "Potato": 1, "GrilledPotato": 1, "SunflowerSeeds": 1,
    "Water": 2, "WheatFlour": 2, "Badwater": 2, "PineResin": 2,
    "Plank": 3, "Gear": 3, "MetalPart": 3, "TreatedPlank": 4, "MetalBlock": 5, "Log": 6, "Dirt": 7,
    "ScrapMetal": 11, "Paper": 1, "Extract": 1, "Explosives": 1, "Book": 1,
    "CattailRoot": 1, "CattailFlour": 2, "CattailCracker": 1, "Spadderdock": 1, "GrilledSpadderdock": 1,
    "Chestnut": 1, "GrilledChestnut": 1, "MapleSyrup": 1, "MaplePastry": 1, "Soybean": 1, "Biofuel": 1,
}

# --- needs (3.2, 3.3, 3.5) -----------------------------------------------------------------------------------------
HUNGER_PER_DAY = 0.8
THIRST_PER_DAY = 0.7
FOOD_POINTS = 0.3
WATER_POINTS = 0.33
FOOD_PER_DAY = HUNGER_PER_DAY / FOOD_POINTS      # 2.67 on Normal
WATER_PER_DAY = THIRST_PER_DAY / WATER_POINTS    # 2.12 on Normal
HUNGER_MIN = -3.0                                # death
THIRST_MIN = -3.0
SLEEP_PER_DAY = 0.6
HOME_SLEEP_PER_HOUR = 0.2
DISH_DECAY_PER_DAY = 0.05
DISH_POINTS = 0.2
ATTRACTION_FILL_PER_HOUR = 0.6
WATER_GOOD_M3 = 0.2                              # 8: one Water good = 0.2 m3 of map water

# Wellbeing tier tables [data: BP/WellbeingTiers], (threshold, delta); beyond the last entry +increment per 10.
TIERS = {
    "WorkingSpeed": ([(5, .2), (10, .4), (15, .6), (20, .8), (25, 1.0), (30, 1.2), (35, 1.4), (40, 1.6), (45, 1.8),
                      (50, 2.0), (55, 2.2), (60, 2.4), (70, 2.6), (80, 2.8), (90, 2.9), (100, 3.0)], 10, .1),
    "MovementSpeed": ([(2, .05), (12, .15), (22, .3), (32, .4), (42, .5), (52, .6), (62, .65), (72, .7), (82, .75),
                       (92, .8)], 10, .05),
    "LifeExpectancy": ([(7, .2), (17, .4), (27, .6), (37, .8), (47, 1.0), (57, 1.1), (67, 1.2), (77, 1.3), (87, 1.4),
                        (97, 1.5)], 10, .1),
    "GrowthSpeed": ([(5, .05), (10, .1), (14, .15), (18, .2), (22, .25), (26, .3), (30, .35), (34, .4), (38, .45),
                     (42, .5), (46, .55), (50, .6), (54, .65), (60, .7), (70, .75), (80, .8), (90, .85), (100, .9)],
                    10, .1),
}

# --- life (3.8, 9) ---------------------------------------------------------------------------------------------------
AVERAGE_LIFESPAN = 50
DAYS_OF_CHILDHOOD = 6
LONGEVITY_RANGE = (0.9, 1.1)
FT_BIRTH_CHANCE_PER_ENTRY = 0.1875
START_ADULTS, START_CHILDREN = 9, 4
START_ADULT_LIFE_PROGRESS = (0.21, 0.74)
START_CHILD_PROGRESS = (0.1, 0.8)

# --- construction (6) ------------------------------------------------------------------------------------------------
UNITS_PER_BUILD_HOUR = 20           # build time = ceil(units / 20) h
DC_BUILDERS_DEFAULT, DC_BUILDERS_MAX = 2, 4
BUILDERS_HUT_WORKERS = 4

# --- game modes (12) -------------------------------------------------------------------------------------------------
@dataclass
class GameMode:
    name: str
    consumption: float          # food and water multiplier
    start_berries: int
    start_water: int
    temperate: tuple            # days, rerolled each cycle
    drought: tuple              # base days
    drought_handicap: float     # first-drought multiplier
    drought_handicap_n: int     # droughts to reach full length
    badtide_from_cycle: int
    badtide: tuple
    badtide_handicap: float
    badtide_handicap_n: int

MODES = {
    "Easy": GameMode("Easy", 0.4, 300, 250, (16, 19), (2, 4), 0.25, 8, 6, (1, 3), 0.3, 6),
    "Normal": GameMode("Normal", 1.0, 130, 0, (13, 17), (5, 9), 0.38, 5, 5, (4, 8), 0.15, 5),
    "Hard": GameMode("Hard", 1.0, 90, 0, (5, 8), (15, 30), 0.2, 12, 4, (15, 30), 0.4, 9),
}
BADTIDE_CHANCE = 0.4
FORECAST_DAYS = 3

# --- plants (7.3) [data] ---------------------------------------------------------------------------------------------
@dataclass
class Plant:
    name: str
    kind: str                   # crop | bush | tree
    plant_h: float
    grow_d: float
    good: str = ""              # harvested good (crop yield or fruit)
    yield_n: float = 0          # per harvest (crop) or per fruit regrowth (bush/tree fruit)
    harvest_h: float = 0        # crop harvest / fruit pick / tap time
    regrow_d: float = 0         # fruit regrowth (bush, fruit tree)
    logs: float = 0             # tree logs when cut
    cut_h: float = 0
    dry_d: float = 0            # DaysToDieDry
    band: tuple = (0, 0)        # water band in whole blocks
    flood_d: float = 0
    spread: float = 0
    zone: str = "moist"

PLANTS = {p.name: p for p in [
    Plant("Carrot", "crop", 0.2, 4, "Carrot", 3, 1.2, dry_d=2, flood_d=2),
    Plant("Potato", "crop", 0.2, 6, "Potato", 1, 1.2, dry_d=1, flood_d=1),
    Plant("Wheat", "crop", 0.2, 10, "Wheat", 3, 1.2, dry_d=0.5, flood_d=0.5),
    Plant("Sunflower", "crop", 0.2, 5, "SunflowerSeeds", 2, 1.8, dry_d=3.5, flood_d=0.66),
    Plant("Cattail", "crop", 0.2, 8, "CattailRoot", 3, 1.2, dry_d=1, band=(1, 1), flood_d=1, zone="flooded"),
    Plant("Spadderdock", "crop", 0.4, 12, "Spadderdock", 3, 1.2, dry_d=0.3, band=(1, 1), flood_d=1, zone="flooded"),
    Plant("Kohlrabi", "crop", 0.2, 3, "Kohlrabi", 2, 1.2, dry_d=2, flood_d=1),
    Plant("Soybean", "crop", 0.2, 8, "Soybean", 2, 1.2, dry_d=0.25, flood_d=0.25),
    Plant("Blueberry", "bush", 0.37, 12, "Berries", 3, 0.8, regrow_d=12, dry_d=9, flood_d=7, spread=0.02),
    Plant("Birch", "tree", 0.5, 7, logs=1, cut_h=1.0, dry_d=11, flood_d=14, spread=0.03),
    Plant("Pine", "tree", 0.75, 12, "PineResin", 2, 1.2, regrow_d=7, logs=2, cut_h=1.5, dry_d=13, flood_d=12),
    Plant("Oak", "tree", 1.0, 30, logs=8, cut_h=2.0, dry_d=15, flood_d=10, spread=0.01),
    Plant("Chestnut", "tree", 0.74, 23, "Chestnut", 3, 1.2, regrow_d=8, logs=4, cut_h=1.2, dry_d=8, flood_d=10),
    Plant("Maple", "tree", 1.1, 28, "MapleSyrup", 3, 1.2, regrow_d=12, logs=6, cut_h=2.0, dry_d=12, flood_d=10),
]}

# --- recipes (4.4) [data: BP/Recipes] --------------------------------------------------------------------------------
@dataclass
class Recipe:
    name: str
    cycle_h: float
    inputs: dict
    outputs: dict
    cycles_capacity: int
    fuel: tuple = None          # (good, cycles per unit)
    workers: int = 1
    power: int = 0

RECIPES = {r.name: r for r in [
    Recipe("Bread", 1.0, {"WheatFlour": 1}, {"Bread": 5}, 38, ("Log", 10)),
    Recipe("WheatFlour", 0.5, {"Wheat": 1}, {"WheatFlour": 1}, 20, power=60),
    Recipe("Plank", 1.25, {"Log": 1}, {"Plank": 1}, 13, power=50),
    Recipe("Gear", 3.0, {"Plank": 1}, {"Gear": 1}, 10, power=120),
    Recipe("MetalBlock", 2.0, {"ScrapMetal": 2}, {"MetalBlock": 1}, 13, ("Log", 5), power=200),
    Recipe("Paper", 1.56, {"Log": 1}, {"Paper": 2}, 10, power=80),
    Recipe("GrilledPotato", 0.52, {"Potato": 1}, {"GrilledPotato": 4}, 30, ("Log", 10)),
    Recipe("GrilledSpadderdock", 0.4, {"Spadderdock": 1}, {"GrilledSpadderdock": 3}, 30, ("Log", 10)),
    Recipe("GrilledChestnut", 0.33, {"Chestnut": 1}, {"GrilledChestnut": 2}, 30, ("Log", 10)),
    Recipe("CattailFlour", 0.25, {"CattailRoot": 1}, {"CattailFlour": 1}, 20, power=60),
    Recipe("CattailCracker", 0.5, {"CattailFlour": 1}, {"CattailCracker": 4}, 20, ("Log", 10)),
    Recipe("MaplePastry", 1.5, {"WheatFlour": 1, "MapleSyrup": 1}, {"MaplePastry": 3}, 20, ("Log", 10)),
    Recipe("TreatedPlank", 3.0, {"Plank": 1, "PineResin": 1}, {"TreatedPlank": 1}, 10, power=250),
    Recipe("Water", 0.33, {}, {"Water": 1}, 15),
    Recipe("Water.Efficient", 1.0, {}, {"Water": 5}, 12, workers=3),
    Recipe("SciencePoints", 1.0, {}, {}, 1),
    Recipe("ScrapMetal", 18.0, {"TreatedPlank": 1}, {"ScrapMetal": 5}, 30, workers=10),
]}

# --- Folktails dish wellbeing (3.3) ----------------------------------------------------------------------------------
FT_DISHES = {"Carrot": 1, "SunflowerSeeds": 1, "GrilledPotato": 2, "GrilledChestnut": 2, "GrilledSpadderdock": 2,
             "Bread": 2, "CattailCracker": 2, "MaplePastry": 3}

# --- Folktails building costs used by the model [data: building blueprints] -------------------------------------------
FT_BUILDINGS = {
    "DistrictCenter": {}, "WaterPump": {"Log": 12}, "GathererFlag": {}, "LumberjackFlag": {},
    "Lodge": {"Log": 12}, "DoubleLodge": {"Log": 20}, "TripleLodge": {"Log": 35}, "MiniLodge": {"Log": 5},
    "EfficientFarmHouse": {"Log": 25}, "Forester": {"Log": 10, "Plank": 7}, "LumberMill": {"Log": 15},
    "Inventor": {"Log": 12}, "SmallTank": {"Log": 15}, "MediumTank": {"Plank": 30, "Gear": 20},
    "LargeTank": {"Plank": 80, "Gear": 60, "MetalBlock": 30}, "SmallWarehouse": {"Log": 3},
    "MediumWarehouse": {"Log": 15}, "SmallPile": {"Log": 2}, "Campfire": {"Log": 15},
    "Bakery": {"Log": 15, "Plank": 15, "Gear": 10}, "Gristmill": {"Log": 40, "Plank": 20, "Gear": 20},
    "GearWorkshop": {"Log": 15, "Plank": 25}, "HaulingPost": {"Log": 20, "Plank": 10},
    "BuildersHut": {"Log": 20, "Plank": 10}, "Grill": {"Log": 25}, "PowerWheel": {"Log": 20},
    "WaterWheel": {"Log": 50}, "Dam": {"Log": 20}, "Levee": {"Log": 12}, "Floodgate": {"Log": 10, "Plank": 5},
    "RooftopTerrace": {"Log": 15}, "Lantern": {"Log": 2, "Plank": 4}, "Shrub": {"Log": 12},
    "LargeWaterPump": {"Log": 20, "Gear": 5, "TreatedPlank": 10}, "PaperMill": {"Log": 40, "Plank": 40, "Gear": 15},
    "WoodWorkshop": {"Log": 20, "Plank": 40, "Gear": 40}, "Smelter": {"Plank": 50, "Gear": 20, "ScrapMetal": 30},
    "AquaticFarmhouse": {"Log": 30, "Plank": 10}, "Agora": {"Log": 150, "Plank": 60},
    "FarmerMonument": {"Log": 200}, "BrazierOfBonding": {"Plank": 400},
    "FountainOfJoy": {"Plank": 400, "TreatedPlank": 200},
    "HallOfAbundance": {"Plank": 700, "TreatedPlank": 300, "MetalBlock": 500},
    "EarthRecultivator": {"Gear": 2000, "TreatedPlank": 2000, "MetalBlock": 1500},
    "BotPartFactory": {"Plank": 50, "Gear": 25, "MetalBlock": 15},
    "BotAssembler": {"Plank": 100, "Gear": 50, "MetalBlock": 50},
}
FT_SCIENCE = {"Bakery": 160, "Gristmill": 180, "GearWorkshop": 100, "Forester": 30, "DoubleLodge": 150,
              "TripleLodge": 250, "MediumTank": 120, "LargeTank": 600, "BuildersHut": 100, "FarmerMonument": 1000,
              "BrazierOfBonding": 3000, "FountainOfJoy": 9000, "HallOfAbundance": 15000, "EarthRecultivator": 20000,
              "AquaticFarmhouse": 150, "PaperMill": 250, "WoodWorkshop": 800, "Smelter": 300,
              "BotPartFactory": 500, "BotAssembler": 750}
WONDER_BUILD_HOURS = 15000
WONDER_MAX_BUILDERS = 40
WONDER_FILL = 1000   # 500 + 500 goods after construction (13.3)

# Monument awe (3.3, 13.2)
FT_MONUMENT_AWE = {"FarmerMonument": 2, "BrazierOfBonding": 4, "FountainOfJoy": 6, "HallOfAbundance": 8,
                   "EarthRecultivator": 10}

# Bots (10)
BOT_LIFE_DAYS = 70
BOT_WORKER_HOURS_TO_MAKE = 126
BOT_BIOFUEL_PER_DAY = 1.9

# Ceilings (3.3)
FT_WELLBEING_CEILING = {"Awe": 30, "Nutrition": 15, "Social": 13, "Fun": 12, "Aesthetics": 9, "Basic": 5}
