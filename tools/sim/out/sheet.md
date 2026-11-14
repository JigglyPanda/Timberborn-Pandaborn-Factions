## Proposed stat sheet (first pass)

Basis: **M** derived from the model (question in brackets), **V** copied from the vanilla analogue in `basis_template`, **G** a guess to tune in play. Re-themed buildings not listed keep their Folktails analogue with Plank -> PandabornPole and TreatedPlank -> PandabornCuredPole.

### Colonists

| stat | spec | Inkpaw | Ringtail | Folktail | basis |
|---|---|---|---|---|---|
| BaseWalkingSpeed (tiles/s) | WalkerSpeedManagerSpec | 2.7 | 2.7 | 2.7 | V |
| BaseSlowedSpeed (tiles/s) | WalkerSpeedManagerSpec | 1.35 | 2.7 | 1.35 | V (Inkpaw) · design (Ringtail: no slowing when loaded) |
| BaseLiftingCapacity | GoodCarrierSpec | 18 | 14 | 14 | M (q1: 3 logs and 6 poles a trip; q5: a Ringtail at 14 equals an Inkpaw builder at 12/12) |
| Rested bonus, WorkingSpeed and MovementSpeed | code (decorator) | +33% at <=12 h, linear to 0 at 16 h, by the bell | same curve, by the Ringtail shift (24 - bell) | - | M (q2) |
| Working hours | new-game slider | dawn to the bell; starts at 16 | bell to dawn | 16 | design · M (q2, q5) |
| Life (days at wellbeing < 7) | LifeService (global) | 50 | 50 | 50 | V · M (q6: no change needed) |
| Childhood (days at wellbeing < 5) | LifeService (global) | 6 | 6 | 6 | V |
| Hunger, Thirst, Sleep | Need.Beaver.* | vanilla | vanilla | vanilla | V |
| Births | ProcreationHouseSpec / nursery | 0.1875 per den entry (vanilla) | Moon Loft: 0.1875 per entry while Ringtail jobs > Ringtail adults + kits | 0.1875 | V · M (q6) |

Rested bonus: +33% at 12 working hours or fewer, falling linearly to 0 at 16; applies to WorkingSpeed, MovementSpeed; multiplies the colonist's whole multiplier (code: delta = bonus x current multiplier).

### Plants

| id | kind | basis | planter | zone | plant h | grow d | harvest | harvest h | dry d | water | spread | basis of numbers |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PandabornShootBamboo | crop | Carrot | Farmstead (Farmhouse group) | moist | 0.2 | 3 | PandabornBambooShoots x2 | 1.0 | 5 | 0/0, DaysToDie 2 | 0 | GrowthTimeInDays: M q1; Yield: M q1; DaysToDieDry: M q1/q4; PlantTimeInHours: V; RemovalTimeInHours: G; Water: V |
| PandabornCabbage | crop | Carrot | Farmstead | moist | 0.2 | 5 | PandabornCabbage x3 | 1.2 | 7 | 0/0, DaysToDie 2 | 0 | GrowthTimeInDays: M q3; Yield: M q3; DaysToDieDry: M q1; PlantTimeInHours: V; RemovalTimeInHours: V |
| PandabornTimberBamboo | tree | Birch | Forester | moist | 0.5 | 5 | cut: PandabornPole x2 (CuttableSpec, RemoveOnCut false like trees); gather: PandabornBambooMushrooms x2 every 3 d (pick 0.5 h) | 1.5 | 7 | 0/0, DaysToDie 8 | 0.03 | GrowthTimeInDays: M q1; Yield: M q1/q8; DaysToDieDry: M q1; PlantTimeInHours: V; RemovalTimeInHours: M q8; Mushrooms: G; ReproductionChance: V |
| PandabornRice | crop | Cattail | Paddy House (aquatic group) | flooded | 0.2 | 8 | PandabornRice x3 | 1.2 | 1 | 1/1, DaysToDie 1.5 | 0 | GrowthTimeInDays: V (Cattail); Yield: V; Water: M q4 |
| PandabornTeaBush | bush (arid) | Blueberry | Farmstead (dry ground) | dry | 0.4 | 6 | gather: PandabornTeaLeaves x3 every 3 d | 0.6 | - | arid: dies 2 d after its soil turns moist | 0 | Yield: M q4; GrowthTimeInDays: G; PlantTimeInHours: V; Water: design |
| PandabornSichuanPepper | crop (arid) | Sunflower | Farmstead (dry ground) | dry | 0.2 | 5 | PandabornSichuanPepper x2 | 1.2 | - | arid: dies 2 d after its soil turns moist | 0 | Yield: M q3; GrowthTimeInDays: V (Sunflower) |
| PandabornPersimmonTree | tree | ChestnutTree | Forester | moist | 0.75 | 14 | gather: PandabornPersimmons x3 every 6 d (pick 1.0 h); cut: Log x3 | 1.2 | 10 | 0/0, DaysToDie 10 | 0.01 | all: V (Chestnut) with growth M q3 |

### Goods

| id | type | weight | consumption effects | dish wellbeing | basis |
|---|---|---|---|---|---|
| PandabornBambooShoots | Box | 1 | Hunger 0.3 | 0 | V (Berries): the raw staple carries no dish need |
| PandabornCabbage | Box | 1 | Hunger 0.3, PandabornCabbage 0.2 | 1 | V (Carrot) |
| PandabornPersimmons | Box | 1 | Hunger 0.3, PandabornPersimmons 0.2 | 1 | V (Carrot) |
| PandabornBambooMushrooms | Box | 1 | Hunger 0.3, PandabornBambooMushrooms 0.2 | 1 | V |
| PandabornSteamedShoots | Box | 1 | Hunger 0.3, PandabornSteamedShoots 0.2 | 1 | M q3 |
| PandabornPickles | Box | 1 | Hunger 0.3, PandabornPickles 0.2 | 2 | V (Grilled Potato) |
| PandabornSteamedRice | Box | 1 | Hunger 0.3, PandabornSteamedRice 0.2 | 2 | V (Bread) |
| PandabornSweetRiceBalls | Box | 1 | Hunger 0.3, PandabornSweetRiceBalls 0.2 | 2 | V (Cattail Cracker) |
| PandabornHotPot | Box | 1 | Hunger 0.3, PandabornHotPot 0.2 | 3 | V (Maple Pastry) |
| PandabornBambooSeedCakes | Box | 1 | Hunger 0.3, PandabornBambooSeedCakes 0.2 | 3 | M q7 |
| PandabornTea | Liquid | 2 | Thirst 0.2, PandabornTea 0.3 | 2 | M q4 (Tea need non-wastable: about 2 cups a day) |
| PandabornRice | Box | 1 | - | 0 | V (Wheat) |
| PandabornRiceFlour | Box | 2 | - | 0 | V (Wheat Flour) |
| PandabornSichuanPepper | Box | 1 | - | 0 | M q3: never edible |
| PandabornTeaLeaves | Box | 1 | - | 0 | V |
| PandabornBambooSeed | Box | 1 | - | 0 | M q7 |
| PandabornPole | Pileable | 3 | - | 0 | V (Plank): keeps the rename option open; lift 18 makes it light |
| PandabornCuredPole | Pileable | 4 | - | 0 | V (Treated Plank) |
| PandabornPaperLantern | Box | 1 | - | 0 | G |

### Recipes

| id | building | cycle h | ingredients | products | cycles capacity | fuel | power | basis |
|---|---|---|---|---|---|---|---|---|
| PandabornSteamedShoots | Steamer | 0.5 | PandabornBambooShoots 1 | PandabornSteamedShoots 2 | 30 | Log, 1 per 10 cycles | 0 | M q1/q3 (ratio) · V (Grill: fuel, buffer) |
| PandabornSteamedRice | Steamer | 1.0 | PandabornRice 1 | PandabornSteamedRice 4 | 30 | Log, 1 per 10 cycles | 0 | M q3 · V (Bread) |
| PandabornPickles | Pickle Yard | 1.0 | PandabornCabbage 1 | PandabornPickles 3 | 20 |  | 0 | M q3 (one cabbage makes several) |
| PandabornRiceFlour | Trip-Hammer Mill | 0.5 | PandabornRice 1 | PandabornRiceFlour 1 | 20 |  | flowing water (own wheel) | V (Gristmill) |
| PandabornSweetRiceBalls | Kitchen | 1.0 | PandabornRiceFlour 1, PandabornPersimmons 1 | PandabornSweetRiceBalls 5 | 20 | Log, 1 per 10 cycles | 0 | V (Maple Pastry shape) · M q3 |
| PandabornBambooSeedCakes | Kitchen | 1.5 | PandabornBambooSeed 1, PandabornRiceFlour 1 | PandabornBambooSeedCakes 4 | 20 | Log, 1 per 10 cycles | 0 | M q7 |
| PandabornHotPot | Hot Pot Hall | 1.5 | PandabornCabbage 1, PandabornSichuanPepper 1, PandabornBambooMushrooms 1 | PandabornHotPot 8 | 15 | Log, 1 per 10 cycles | 0 | M q3 |
| PandabornTea | Tea Roastery | 0.75 | PandabornTeaLeaves 1, Water 1 | PandabornTea 3 | 20 |  | 0 | design (3 cups per water) · M q4 |
| Paper (from poles) | Paper Mill | 1.56 | PandabornPole 1 | Paper 2 | 10 |  | 80 | V (Paper, pole for log) |
| PandabornPaperLantern | Lantern Workshop | 1.5 | Paper 2, PandabornPole 1 | PandabornPaperLantern 2 | 10 |  | 0 | M q7 (Small Festival in cycle 2) |
| PandabornCuredPole | Smoke Kiln | 3.0 | PandabornPole 1 | PandabornCuredPole 1 | 10 | Log, 1 per 4 cycles | 0 | V (Treated Plank: 3 h) · M q8 (log smoke instead of resin and 250 hp) |
| Gear | Gear Workshop | 3.0 | PandabornPole 1 | Gear 1 | 10 |  | 120 | V |
| Water | Water Pump | 0.33 | free | Water 1 | 15 |  | 0 | V |
| PandabornDewWater | Dew Collector | 12.0 | free | Water 1 | 4 |  | 0 | M q4: 2 a day; DewLimiter DroughtEfficiency 0.33, and efficiency / (collectors within 6 tiles) |
| PandabornCisternTap | Cistern Tap | 1.0 | Water 1 | 0.2 m3 into the flume 1 | 5 |  | 0 | V (Discharge: 3 Water/h) · M q4 (1 Water/h keeps a 10-tile strip) |
| PandabornWoodenOx | Ox Workshop | 72.0 | PandabornCuredPole 10, Gear 15, MetalBlock 2 | Wooden Ox 1 | 1 |  | 250 | M q8 (vanilla bot parts, one building) |
| SciencePointsStarTower | Star Tower | 4.0 | free | Science 12 | 1 |  | 0 | V (Observatory, 4 workers, no power) · M q5 |

### Needs (new)

| id | group | daily | wellbeing | importance | wastable | satisfied by | rhythm | basis |
|---|---|---|---|---|---|---|---|---|
| PandabornNap | Fun | -0.6 | 2 | 1.2 | False | Hammock (1 seat), Nap Platform (6 seats): +0.6/h | daily: one 1-hour visit | M q2 |
| PandabornTea | Nutrition | -0.6 | 2 | 1.0 | False | PandabornTea +0.3 a cup (about 2 a day) | daily, on ordinary drinking trips | M q4 |
| PandabornTeahouse | SocialLife | -0.15 | 2 | 1.0 | False | Teahouse +0.6/h, 12 seats | every 3-4 days | V (Domed Garden) · M q2 capacity |
| PandabornPlay | Fun | -0.2 | 2 | 1.0 | False | Slide and Swing +0.6/h, 8 seats | every 3 days | V (Lido) · M |
| PandabornCubWatching | SocialLife | -0.2 | 3 | 1.0 | False | Panda Kindergarten +0.6/h, 12 seats | every 3 days | V (Agora) · M |
| PandabornSoak | Fun | -0.2 | 3 | 1.0 | False | Hot Spring Bath +0.6/h, 8 seats (+WetFur) | every 3 days | V (Mud Pit) · M |
| PandabornContemplation | Fun | -0.12 | 2 | 1.0 | False | Ink Studio +0.6/h, 4 seats | weekly | V (Contemplation Spot) |
| PandabornPerformance | Fun | -0.12 | 5 | 1.0 | False | Opera Stage +0.6/h, 20 seats, while performers work | weekly | V (Dance Hall) |
| Pandaborn<Dish> (nine) | Nutrition | -0.05 | see goods | 1.0 | True | +0.2 a unit | a bite every 4 days | V (Need.Beaver.Bread) |
| PandabornFestive | Boosts | -0.05 | 4 | 1.0 | True | A Lantern Festival sets it to 1 (Grand: and +1 wb) | 20 days, most of a cycle | M q7 |
| PandabornMemorialArch / GreatSittingPanda / SkyLantern | Awe | -0.3 | 6 / 12 / 10 | 1.0 | True | ranged 0.1/h (wonder 10/h) | 3 h a day in range | V (Awe) · M q8 |

Wellbeing ceiling by group: Inkpaws: Basic 5, Nutrition 18, Social 6, Fun 14, Aesthetics 10, Awe 28, Boosts 4 = 85; Folktails: Basic 5, Nutrition 15, Social 13, Fun 12, Aesthetics 9, Awe 30, Boosts 0 = 84


### Buildings

| id | basis | who | cost | science | workers max (default) | recipes | capacity / notes | basis of numbers |
|---|---|---|---|---|---|---|---|---|
| PandabornVillageHall | DistrictCenter.Folktails | I | free | 0 | 4 (2) | - | builders; 20 storage | V |
| BuildersHut | BuildersHut.Folktails | I | Log 20, PandabornPole 10 | 100 | 4 (4) | - |  | V |
| HaulingPost | HaulingPost.Folktails | I | Log 20, PandabornPole 10 | 0 | 10 (5) | - | CarryingCapacity +1 | V |
| DistrictCrossing | DistrictCrossing.Folktails | I | Log 30, PandabornPole 15 | 600 | 10 (4) | - |  | V |
| PandabornFestivalSquare | new | - | Log 30, PandabornPole 30, Paper 10 | 300 | 0 | - | holds 40 lanterns, 60 dishes, 20 fireworks | M q7 (reachable in cycle 2) |
| PandabornDen | Lodge.Folktails | - | Log 12 | 0 | - | - | 3 (2 adults, 1 child) | V |
| PandabornCourtyardHouse | DoubleLodge.Folktails | - | Log 20 | 150 | - | - | 6 (4, 2) | V |
| PandabornTerraceHouse | TripleLodge.Folktails | - | Log 25, PandabornPole 10 | 250 | - | - | 9 (6, 3), stackable | V · M (poles for the stackable frame) |
| PandabornMoonLoft | new (Lodge) | - | Log 10, PandabornPole 10 | 200 | - | - | 4 (3 adults, 1 kit slot); a kit is born only while open Ringtail jobs > Ringtail adults + kits; the first loft brings 3 adults + 1 kit | M q5/q6 |
| GathererFlag | GathererFlag.Folktails | I | free | 0 | 1 | - | 20; berries, persimmons, mushrooms | V |
| PandabornFarmstead | EfficientFarmHouse.Folktails | I | Log 25 | 0 | 3 | - | 50; shoot bamboo, cabbage; tea and pepper on dry ground | V |
| PandabornSteamer | Grill.Folktails | I | Log 20, PandabornPole 5 | 40 | 1 | PandabornSteamedShoots, PandabornSteamedRice |  | M q1/q3 |
| PandabornPickleYard | new | I | Log 20, PandabornPole 15 | 120 | 1 | PandabornPickles |  | M q3 |
| PandabornPaddyHouse | AquaticFarmhouse.Folktails | I | Log 30, PandabornPole 10 | 150 | 2 | - | 50; rice | V |
| PandabornTeaRoastery | new | I | Log 15, PandabornPole 20 | 250 | 1 | PandabornTea |  | M q4 |
| PandabornTripHammerMill | Gristmill.Folktails | I | Log 30, PandabornPole 20, Gear 10 | 200 | 1 | PandabornRiceFlour | runs on flowing water at its wheel, no shafts | V · G (cheaper: no power plant) |
| PandabornKitchen | Bakery.Folktails | I | Log 15, PandabornPole 15, Gear 10 | 300 | 1 | PandabornSweetRiceBalls, PandabornBambooSeedCakes |  | V |
| PandabornHotPotHall | new | I | Log 40, PandabornPole 40, Gear 20 | 800 | 1 | PandabornHotPot |  | M q3 |
| LumberjackFlag | LumberjackFlag.Folktails | I | free | 0 | 1 | - |  | V |
| Forester | Forester.Folktails | I | Log 12 | 0 | 1 | - |  | M q1 (log-only: built before the first pole) |
| GearWorkshop | GearWorkshop.Folktails | I | Log 15, PandabornPole 25 | 100 | 1 | Gear |  | V |
| PaperMill | PaperMill.Folktails | I | Log 40, PandabornPole 40, Gear 15 | 250 | 1 | Paper (from poles) |  | V |
| PandabornLanternWorkshop | new | I | Log 10, PandabornPole 20 | 200 | 1 | PandabornPaperLantern |  | M q7 |
| PandabornSmokeKiln | WoodWorkshop.Folktails | I | Log 20, PandabornPole 40, Gear 20 | 600 | 1 | PandabornCuredPole |  | M q8 (no power, so cheaper than the Wood Workshop) |
| ExplosivesFactory | ExplosivesFactory.Folktails | I | PandabornPole 30, Gear 30, MetalBlock 30 | 400 | 1 | - |  | V |
| ScavengerFlag | ScavengerFlag.Folktails | I | free | 250 | 1 | - |  | V |
| Smelter | Smelter.Folktails | I | PandabornPole 50, Gear 20, ScrapMetal 30 | 300 | 1 | - |  | V |
| Mine | Mine.Folktails | I | Log 250, Gear 350, PandabornCuredPole 200 | 4000 | 10 | - |  | V |
| WaterPump | WaterPump.Folktails | I | Log 12 | 0 | 1 | Water |  | V |
| PandabornCisternSmall | SmallTank.Folktails | - | Log 15 | 0 | - | - | 40 | M q4 |
| PandabornCisternMedium | MediumTank.Folktails | - | Log 20, PandabornPole 30 | 100 | - | - | 300 | M q4 (no gears: reachable before the first drought) |
| PandabornCisternLarge | LargeTank.Folktails | - | PandabornPole 80, Gear 40, MetalBlock 20 | 500 | - | - | 1200 | V · M |
| PandabornFlume | new (ThrottlingValve cell) | - | PandabornPole 2 | 60 | - | - | per tile | G |
| PandabornFlumeCorner | new | - | PandabornPole 3 | 60 | - | - |  | G |
| PandabornFlumeDrop | new | - | PandabornPole 3 | 60 | - | - |  | G |
| PandabornFlumeBridge | new | - | PandabornPole 4, Log 1 | 120 | - | - | per tile | G |
| PandabornFlumeGate | FillValve.Folktails | - | Log 6, PandabornPole 6 | 80 | - | - | sets flow; shuts at contamination >= 0.05 | G · design |
| PandabornScoopWheel | new | - | Log 20, PandabornPole 30, Gear 5 | 250 | - | - | lifts 1 block; needs flow >= 0.15 | G (prototype measures) |
| PandabornPaddySpout | FillValve.Folktails | - | PandabornPole 6 | 150 | - | - | holds 0.3 deep | G |
| PandabornCisternTap | Discharge.Folktails | - | Log 8, PandabornPole 8 | 250 | - | PandabornCisternTap | 1 Water an hour into a flume; no workers | M q4 |
| PandabornDewCollector | new | - | PandabornPole 15, Paper 4 | 300 | - | PandabornDewWater | buffer 4; footprint 2x2; 2 Water a day, 2/3 in drought, shared with collectors within 6 tiles | M q4 |
| PandabornTreadwheelLift | new | I | PandabornPole 30, Gear 10 | 300 | 1 | - | lifts 1 block | G |
| PandabornDryStoneWall | Levee.Folktails | - | Log 4, Dirt 2 | 120 | - | - | blocks moisture like an impermeable floor, sideways | G |
| PandabornBambooWaterWheel | WaterWheel.Folktails | - | Log 30, PandabornPole 15 | 0 | - | - | 270 hp x flow | V |
| PowerWheel | PowerWheel.Folktails | I | Log 20 | 0 | 1 | - | 50 hp | V |
| PandabornKiteWindmill | WindTurbine.Folktails | - | Log 20, PandabornPole 20 | 120 | - | - | 150 hp | V |
| PandabornLargeKiteWindmill | LargeWindTurbine.Folktails | - | PandabornPole 40, Gear 20, Paper 30 | 1400 | - | - | 300 hp | V |
| Inventor | Inventor.Folktails | I | Log 12 | 0 | 1 | SciencePoints |  | V |
| PandabornStarTower | Observatory.Folktails | R | PandabornPole 60, Gear 30, Paper 10 | 1000 | 4 | SciencePointsStarTower | no power (stars, not machines) | V · M q5 |
| PandabornOxWorkshop | BotAssembler.Folktails | I | PandabornPole 100, Gear 50, MetalBlock 40 | 1000 | 2 | PandabornWoodenOx | 250 hp; all parts in one building | M q8 |
| PandabornNightBuildersPost | BuildersHut.Folktails | R | Log 15, PandabornPole 10 | 0 | 4 (4) | - | unlocked by the first Moon Loft | M q5 |
| PandabornNightCourierPost | HaulingPost.Folktails | R | Log 20, PandabornPole 10 | 150 | 6 (3) | - | CarryingCapacity +1 | M q5 |
| PandabornNightForagersPost | GathererFlag.Folktails | R | PandabornPole 10 | 100 | 2 (2) | - | 30; mushrooms first | M q5 |
| PandabornOperaStage | DanceHall.Folktails | R | Log 100, PandabornCuredPole 40, MetalBlock 20 | 1200 | 2 (2) | - | 20 seats; open while performers work | V · M q5 |
| Campfire | Campfire.Folktails | - | Log 15 | 0 | - | - | 5 seats | V |
| PandabornHammock | Hammock.Folktails | - | Log 4 | 0 | - | - | 1 seat, Nap +0.6/h | M q2 (log-only: buildable on day 1) |
| PandabornNapPlatform | RooftopTerrace.Folktails | - | Log 10, PandabornPole 15 | 100 | - | - | 6 seats, Nap +0.6/h, stackable | M q2 |
| PandabornTeahouse | DomedGarden.Folktails | - | Log 25, PandabornPole 25 | 150 | - | - | 12 seats; stocks 30 Tea | M q2/q4 |
| PandabornSlideAndSwing | Lido.Folktails | - | Log 25, PandabornPole 20 | 250 | - | - | 8 seats | V |
| PandabornKindergarten | Agora.Folktails | - | Log 60, PandabornPole 40 | 400 | - | - | 12 adult seats + cubs' play | V · M |
| PandabornInkStudio | ContemplationSpot.Folktails | - | Log 10, Paper 10 | 200 | - | - | 4 seats | V |
| PandabornHotSpringBath | MudPit.Folktails | - | Log 60, PandabornCuredPole 30, Dirt 20 | 1500 | - | - | 8 seats | V |
| TeethGrindstone / MedicalBed / Herbalist / Shower | vanilla | - | vanilla | vanilla | vanilla | - |  | V |
| PandabornMemorialArch | BrazierOfBonding.Folktails | - | Log 250, PandabornPole 800 | 3000 | - | - | Awe +6, radius 10 | M q8 (labour of Farmer Monument + Brazier) |
| PandabornGreatSittingPanda | HallOfAbundance.Folktails | - | PandabornPole 1400, PandabornCuredPole 700, MetalBlock 650 | 15000 | - | - | Awe +12, radius 30 | M q8 (labour of Fountain + Hall) |
| PandabornSkyLantern | EarthRecultivator.Folktails | - | Gear 2400, PandabornCuredPole 2400, MetalBlock 1800, Paper 500 | 20000 | 10 (crew) | - | build 15000 h, 40 builders; fill 500 Paper Lanterns + 500 Tea | V · M q8 |

### Events and oxen

**Great Flowering.** first_cycle: 6; every_cycles: 5-7 (alternating shoot, timber; first is shoot bamboo); announce: at the start of the cycle before: buds show, about 15-20 days; never_in: drought, badtide; when: the first day of a temperate season; plants die over 2 days; seed: each flowering plant drops 3 PandabornBambooSeed when cleared (gathered or cut); replant: that bamboo cannot be replanted until the next temperate season (code: planting check); reserve: shoot year: ~14 food per colonist (40 colonists: 560); timber year: ~5 poles per colonist; setting: off / rare (every 9-11 cycles) / normal; basis: M q7

**Lantern Festival.** small: 40 Paper Lanterns + 20 each of three cooked dishes; grand: adds 20 Fireworks; cost: everyone off duty from dawn to the next dawn; festive: PandabornFestive (+4) set to 1, decay 0.05: 20 days; Grand adds 1 more wellbeing while it lasts; once_per_cycle: True; basis: M q7

**Wooden Ox.** walk_tiles_s: 1.8; lift: 40; life_days: 90; hours: 24; needs: none (bot tier 0: work x1.65, walk x1.3); cost: 10 Cured Pole + 15 Gear + 2 Metal Block, 72 h at the Ox Workshop; basis: M q8

