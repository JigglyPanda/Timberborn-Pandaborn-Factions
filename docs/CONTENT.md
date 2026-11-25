# Inkpaws content catalogue

The human overview of what the faction contains. Two parts:

1. **Design intent** (hand-written): what exists and why, who works it and when a player meets it. It follows
   `docs/DESIGN.md` revision 4 and its change log, the balance decisions of 2026-11-25 included; where the two
   disagree, DESIGN.md wins.
2. **Catalogue tables** (generated): every building, good, need, recipe, plant and character exactly as
   `catalogue/*.toml` defines them today: basis, model, the code module an item waits for, icon, cost.

The machine-readable source of truth is `catalogue/` ([catalogue/README.md](../catalogue/README.md)). Numbers come
from `docs/tech/balance.md` and are now owned by the catalogue. To refresh part 2 after any catalogue change:

```powershell
E:\PandabornDev\tools\venv\Scripts\python.exe -I tools\docs\content_tables.py          # rewrite the tables
E:\PandabornDev\tools\venv\Scripts\python.exe -I tools\docs\content_tables.py --check  # exit 1 if they are stale
```

Last reconciled by hand: 2026-11-25 (draft 3; draft 2 was written 2026-11-14 before the catalogue existed).

# Part 1: design intent

## How to read it

* **Who:** `I` Inkpaws (dawn to the bell), `R` Ringtails (the bell to dawn), `—` no workers.
* **When:** roughly when a player meets it. `0` at the start, `1` first cycle, `2` second and third cycles,
  `3` mid game, `4` late game.
* Whether a building is a re-themed vanilla model, one of our own models or a stand-in, and whether it is in the
  game today or hidden until its code module ships, are facts of the catalogue: see the *Model* and *Waits for*
  columns in part 2. Part 1 says what is intended.

## Rules for the whole catalogue

1. **Vanilla functions keep vanilla names and behaviour.** Levee, Dam, Floodgate, Water Pump, Warehouse,
   Platform, Stairs and all automation are re-themed and otherwise untouched.
2. **Identity lives in food, water, homes, leisure and power.** New models go there.
3. **Poles are the Inkpaws' planks.** A pole *is* the vanilla plank and a cured pole *is* the treated plank,
   renamed and re-iconed for Inkpaws only by a faction blueprint modifier (decided 2026-11-14, proven in game:
   `docs/tech/stage0.md`). Nothing is recosted, and other mods' buildings work unchanged.
4. **Vanilla goods are reused wherever the thing is the same.** New goods are only for new things.
5. **A colony with no Ringtails is complete.** Nothing it needs is made only by Ringtails. Only the Star Tower
   depends on them, and it adds science the inventors would also make, more slowly.
6. **One real place.** Sichuan. No writing on textures, nothing Japanese-coded, no red-and-gold palace style,
   no religious imagery.
7. **Nothing in the toolbar lies** (DESIGN.md, quality bar). A building, good, need or recipe that waits for a code
   module is left out of the game until that module ships; part 2 marks each one.

## Goods

| Good | Kind | From | Used for |
|---|---|---|---|
| Bamboo shoots | Raw food | Shoot bamboo, a field crop | Starter staple; steamed shoots |
| Poles | Material (the vanilla plank) | Timber bamboo, cut; or logs split at the Pole Mill | Construction in place of planks; paper |
| Cured poles | Material (the vanilla treated plank) | Smoke Kiln | Late construction in place of treated planks |
| Cabbage | Raw food | Farmhouse | Second staple; pickles, hot pot |
| Rice | Crop | Paddy House | Steamed rice, rice flour |
| Rice flour | Ingredient | Trip-Hammer Mill | Sweet rice balls, seed cakes |
| Steamed shoots | Food | Steamer | The first cooked dish |
| Steamed rice | Food | Steamer | Staple meal |
| Pickles | Food | Pickle Yard | Stretches a cabbage field, about as well as bread does wheat (2026-11-25); not a pantry food |
| Sweet rice balls | Food | Kitchen | The festival sweet |
| Sichuan pepper | Crop | A bush on dry ground: planted by the Forester, picked by gatherers | Hot pot |
| Hot pot | Food | Hot Pot Hall | Best everyday meal |
| Tea leaves | Crop | Tea bushes on dry ground: planted by the Forester, picked by gatherers | Tea |
| Tea | Dry good | Tea Roastery | Used up at the Teahouse, with water, to meet the one Tea need. Never drunk from storage |
| Persimmons | Raw food | Persimmon trees | Snack; sweet rice balls |
| Bamboo mushrooms | Raw food | Foraged in standing timber groves | Delicacy; hot pot |
| Bamboo seed | Rare crop | The harvest of a bamboo in a Great Flowering | Seed cakes |
| Bamboo seed cakes | Food | Kitchen (seed and rice flour: the better recipe); or the Steamer, two per seed, with no mill (2026-11-25) | The best food in the mod |
| Paper lanterns | Festival good | Lantern Workshop | Festival; lantern decorations; the wonder |

Logs, gears, paper, scrap metal, metal blocks, water, berries, badwater, explosives, fireworks, dirt and
antidote are the vanilla goods.

Twelve things to eat and drink, in the order a player reaches them: berries, shoots, cabbage, steamed shoots,
persimmons, pickles, steamed rice, tea, sweet rice balls, mushrooms, hot pot, seed cakes.

### Cut from draft 1

Tofu and soybeans, dumplings (now sweet rice balls), lacquer and lacquered poles (now cured poles), bamboo
charcoal, persimmon cakes, lotus root, ox parts and ox upkeep goods, scrolls.

## Plants

| Plant | Zone | Planted by | Harvest | Notes |
|---|---|---|---|---|
| Shoot bamboo | Moist | Farmhouse | Shoots | Field crop, like carrots; edible raw; about three days; survives a short drought (5 dry days) |
| Timber bamboo | Moist | Forester | Poles; mushrooms foraged while standing | Fast tree: seven days (2026-11-25; it was five); lasts ten dry days |
| Cabbage | Moist | Farmhouse | Cabbage | Edible raw; the hardier staple (7 dry days) |
| Rice | Flooded, shallow | Paddy House | Rice | Staple of the second cycle onward |
| Tea bush | Dry (brown ground) | Forester; picked by gatherers | Tea leaves, repeatedly | Wet roots stop its growth; it dies after about three wet days |
| Sichuan pepper | Dry (brown ground) | Forester; picked by gatherers | Pepper | As the tea bush |
| Persimmon tree | Moist | Forester | Persimmons; logs when felled | Orchard tree |

Birch, pine, oak and blueberries remain. In a Great Flowering each grown bamboo becomes its flowering twin
(two more plants in the catalogue, never planted by hand), whose harvest is bamboo seed.

## Buildings

### Village and logistics

| Building | Who | When | Role |
|---|---|---|---|
| Village Hall | I | 0 | District center |
| Builders' Hut | I | 1 | Builders |
| Hauling Post | I | 1 | Hauling |
| District Crossing | I | 3 | Districts |
| Festival Square | — | 2 | Calls and hosts the Lantern Festival. It stores nothing: festival goods stay in ordinary storage and are taken at the call |

### Homes

| Building | When | Role |
|---|---|---|
| Den | 0 | Starter home |
| Courtyard House | 2 | Larger home in the Sichuan farmstead style |
| Terrace House | 3 | Stackable hillside home |
| Moon Loft | 1–2 | A snug home on stilts above a path. The first one invites the Ringtails; lofts raise their kits. If a district with a loft loses its last Ringtail, a new family comes after a few days (2026-11-25) |

Any home takes anyone, with one rule: Moon Lofts belong to Ringtails (an Inkpaw lodger gives way when a Ringtail or
a kit needs the bed).

### Food

| Building | Who | When | Role |
|---|---|---|---|
| Gatherer Flag | I | 0 | Berries, persimmons, mushrooms; picks tea and pepper |
| Farmhouse | I | 0 | Shoot bamboo, cabbage |
| Steamer | I | 1 | Steamed shoots, then steamed rice; after a Flowering, seed cakes |
| Pickle Yard | I | 1 | Pickles |
| Paddy House | I | 2 | Rice |
| Tea Roastery | I | 2 | Tea |
| Trip-Hammer Mill | I | 2 | Rice flour, driven by flowing water, no shafts |
| Kitchen | I | 2 | Sweet rice balls, seed cakes |
| Hot Pot Hall | I | 3 | Hot pot |

### Wood and materials

| Building | Who | When | Role |
|---|---|---|---|
| Lumberjack Flag | I | 0 | Cuts trees and timber bamboo |
| Forester | I | 0 | Plants timber bamboo, trees, tea and pepper; replants dead trees by default |
| Pole Mill | I | 0 | The vanilla lumber mill: splits logs into poles. Supplies the first days and is the fallback when a drought kills the groves |
| Gear Workshop | I | 1 | Gears |
| Paper Mill | I | 2 | Paper from poles |
| Lantern Workshop | I | 2 | Paper lanterns |
| Smoke Kiln | I | 3 | Cured poles |
| Explosives Factory | I | 3 | Explosives, fireworks |

### Metal

Scavenger Flag, Smelter, Mine: re-themed, `I`.

### Water

| Building | Who | When | Role |
|---|---|---|---|
| Water Pump | I | 0 | Drinking water |
| Cistern (small, medium, large) | — | 0–3 | Water storage |
| Flume, Flume Corner, Flume Drop, Flume Bridge, Flume Bridge Span | — | 1 | Lead water one way, level or downhill; a span lets one line cross another |
| Flume Gate | — | 1 | Intake; sets flow; shuts itself on badwater |
| Scoop Wheel | — | 1 | Lifts water using the current. Logs and poles, no gears; cheap in science, like the flumes (free) and the gate, so the first flume is reachable in days 6 to 10 |
| Paddy Spout | — | 2 | Holds a field at a shallow depth |
| Cistern Tap | I | 2 | A worker pours stored water into a flume or basin |
| Dew Collector | — | 2 | A little water, less in drought: four keep a landlocked outpost of about six in water (2026-11-25) |
| Treadwheel Lift | I | 2 | Lifts water where there is no current |
| Large Water Pump, Mechanical Pumps, Aquifer Drill | I / — | 3–4 | Deep and powered pumping |
| Badwater Pump, Discharge, Centrifuge, Dome, Rig | I | 3–4 | Badwater |

### Landscaping

Levee, Dam, Floodgates, Fill Valve, Throttling Valve, Impermeable Floor, Contamination Barrier, Dynamite,
Tunnel, Dirt Excavator, Terrain Block: re-themed. One addition: **Dry-Stone Wall**, which stops moisture creeping
sideways through the soil, so tea can stand closer to the irrigated land. It costs logs and poles only.

### Power

| Building | Who | When | Role |
|---|---|---|---|
| Bamboo Water Wheel | — | 1 | Water power |
| Power Wheel | I | 1 | Worker power |
| Kite Windmill (small, large) | — | 2–3 | Wind power |
| Shafts, Clutch, Gravity Battery | — | 1–3 | Network |

No fuel engines.

### Science and Wooden Oxen

| Building | Who | When | Role |
|---|---|---|---|
| Inventor | I | 0 | Science |
| Star Tower | R | 3 | A Ringtail night post that makes science from the night sky (decided 2026-11-25). It keeps its own science cost: the Moon Loft does not unlock it |
| Ox Workshop | I | 4 | Builds Wooden Oxen: tireless, strong (lift 30), lasting ninety days, able to do what vanilla bots do; priced above a vanilla bot (2026-11-25) |

### Storage

Warehouses, piles and the underground pile: re-themed. Cisterns are listed under Water.

### Paths and getting around

Paths, stairs, platforms, overhangs, bridges, gate, airlock and ziplines: re-themed as bamboo scaffolding and
rope.

### Leisure and care

| Building | Need | How often | When |
|---|---|---|---|
| Campfire | Company | Every few days | 0 |
| Hammock | Nap | Daily | 0 |
| Nap Platform | Nap, for several at once; on the ground or on a roof (it keeps the rooftop effect) | Daily | 2 |
| Teahouse | Tea: the one place the Tea need is met; it uses up roasted tea and water, brought by haulers or night couriers | Daily | 2 |
| Slide and Swing | Play | Every few days | 2 |
| Kindergarten | Watching the young | Every few days | 2 |
| Ink Studio | Ink painting | Weekly | 2 |
| Hot Spring Bath | Soak; uses water | Every few days | 3 |
| Opera Stage | Opera. An ordinary attraction, with no claim about who runs it (decided 2026-11-25) | Weekly | 3 |
| Teeth Grindstone, Medical Bed, Herbalist, Shower | As vanilla | As vanilla | 0–2 |

### Ringtail workplaces

All in one toolbar group, the Night Watch. The three posts are locked behind a science cost until the first Moon
Loft brings the Ringtails, which unlocks them free; the Star Tower keeps its cost.

| Building | When | Role |
|---|---|---|
| Night Builders' Post | With the first Moon Loft | Builders through the evening and night |
| Night Courier Post | 2 | Restocks workshops and clears flags overnight |
| Night Gatherers' Post | 2 | Mushrooms and wild food |
| Star Tower | 3 | Science, by night |

### Decoration

Standing, hanging and string lanterns; bamboo fence; hedge; shrub; potted pine; panda statue; bamboo pinwheel;
scarecrow; bench; banners; goldfish bowl; garden moon gate; grey tile roofs in the vanilla sizes. Each kind is
its own small need, as in vanilla. Lantern decorations are built from paper lanterns. Tradition (one step per
Lantern Festival) unlocks String Lanterns and the Goldfish Bowl (1), the Hanging Lantern (2) and the Garden Moon
Gate (3) at no science cost.

### Monuments and the wonder

| Building | When | Note |
|---|---|---|
| Memorial Arch | 3 | First monument |
| Great Sitting Panda | 4 | A freestanding cliff carving with water at its feet, showing both peoples |
| Sky Lantern | 4 | The wonder, launched with the village's own paper lanterns |

### Automation

All nineteen vanilla automation buildings, re-themed.

## Needs

Shared with vanilla: hunger, thirst, sleep, shelter, wet fur, injury, contamination, teeth, company.

| New need | Satisfied by |
|---|---|
| One per dish (nine; raw bamboo shoots carry none) | Eating it |
| Tea | The Teahouse; daily |
| Nap | Hammock, nap platform; daily |
| Play | Slide and swing |
| Watching the young | Kindergarten |
| Soak | Hot spring bath |
| Ink painting | Ink studio |
| Opera | Opera stage |
| One per decoration kind of our own (statue, pinwheel, goldfish bowl, moon gate, string lanterns) | Standing near it |
| One per monument (three) | Monuments |
| Festive spirit, and Grand festival | A Lantern Festival; fades over about twenty days |

## Models

58 building models from the kit (`art/models/`), 56 of them adopted by the catalogue; nine plant models with
growth stages (`art/plants/`); the Inkpaw adult and cub (the Reskin's bodies), the Ringtail adult and kit, the Wooden
Ox; the conical hat and the back-basket. Part 2 lists which building uses which.

## Later updates

Lotus and lotus root, tofu, a second kitchen tier, more monuments, rope-way variants, the showcase map.

## Where DESIGN.md and the data still disagree

On 2026-11-25 the docs review listed nine places where DESIGN.md promised what the build did not do. The
coordinator ruled on all nine the same day (DESIGN.md 382e91d: "the design is brought to what the build does"):
the farm is the Farmhouse, every farmer wears the conical hat, the Dew Collector has no dawn, the ox is not slow,
scaffolding and rope bridges cost as vanilla, there is no sun or moon in the toolbar and no lantern wave at the
bell, the Opera Stage is out of the Ringtails' table, and the panda calls are "built, off until the owner has
listened". What is left, checked against the catalogue at 05:10 that day:

| # | DESIGN.md says | The catalogue and code have | Who |
|---|---|---|---|
| 1 | The Star Tower ships as a Ringtail night post that keeps its own science cost | Still hidden: it waits for `Ringtails` and for `RingtailVenues`, and that second switch is off and has no module (part 2, *Waits for*) | Catalogue, Ringtails code lane |
| 2 | "Farmhouse (the vanilla name, already translated)" | The vanilla name of the building the Inkpaws' farm is copied from (`EfficientFarmHouse.Folktails`) is "Efficient Farmhouse"; that is what the game shows, while DESIGN.md, the tutorial and the plant texts say "Farmhouse" | Text |
| 3 | Foresters replant dead trees by default | Code written on 2026-11-25 and not yet committed or run (`src/code/Pandaborn.Names/ForesterCustom.cs`); its proof is run N21 of `docs/tech/needs-game-run.md` | Core code lane |
| 4 | Timber bamboo grows in seven days; bamboo seed can be steamed into seed cakes | Check the Plants and Recipes tables in part 2: they show whatever the catalogue holds when they were last generated | Catalogue |

# Part 2: catalogue tables

<!-- generated:begin (tools/docs/content_tables.py; do not edit by hand) -->

### Code modules and what they hide

A catalogue item with `waits_for = "<Module>"` is generated only when that module ships (`src/code/modules.txt`) and its switch in `catalogue/rules.toml [modules]` is on. Hidden items keep their locked ids.

| Module | In `modules.txt` | Switch | Its items are | Items that wait for it |
|---|---|---|---|---|
| Bell | yes | on | visible | nothing |
| Festival | yes | on | visible | 1 building; 2 needs |
| Flowering | yes | on | visible | 2 goods; 1 need; 2 recipes; 2 plants |
| Look | yes | on | visible | nothing |
| Names | yes | on | visible | nothing |
| RingtailVenues | **no** | **off** | **hidden** | 1 building |
| Ringtails | yes | on | visible | 5 buildings; 2 characters |
| RingtailsFallback | yes | on | visible | nothing |
| Tutorial | yes | on | visible | nothing |
| Water | yes | on | visible | 13 buildings; 2 goods; 1 need; 3 recipes |
| Words | yes | on | visible | nothing |

### Buildings

171 entries in `catalogue/buildings.toml`: 111 re-themed vanilla buildings, 58 of our own (`Pandaborn…`: 57 on their own model, 1 on a vanilla stand-in model) and 2 vanilla dev buildings. 1 are hidden today (their module is off or not shipped); 170 are generated.

*Basis* is the vanilla blueprint the generator copies (template name; `—` for our own id on the same vanilla name). *Toolbar* is the bottom-bar group. *Model*: `own` = adopted from the building kit; `vanilla, re-themed` = the vanilla model in the Inkpaws' materials; **stand-in** = one of our own buildings still on a vanilla model. *Waits for* names the code module; bold = hidden today. *Icon*: `own` = a sprite under `mod/PandabornFactions/Sprites/Pandaborn/Buildings`.

#### Village and logistics

| Building | Id | Basis | Toolbar | Model | Waits for | Icon | Cost | Science | Recipes |
|---|---|---|---|---|---|---|---|---|---|
| Village Hall | `PandabornVillageHall` | `DistrictCenter.Folktails` | DistrictManagement | own: `art/models/VillageHall` |  | own | free | 0 |  |
| Builders' Hut | `BuildersHut` | re-theme | DistrictManagement | vanilla, re-themed |  | vanilla | 20 Log, 10 Poles | 100 |  |
| Hauling Post | `HaulingPost` | re-theme | DistrictManagement | vanilla, re-themed |  | vanilla | 20 Log, 10 Poles | 0 |  |
| District Crossing | `DistrictCrossing` | re-theme | DistrictManagement | vanilla, re-themed |  | vanilla | 30 Log, 15 Poles | 600 |  |
| Festival Square | `PandabornFestivalSquare` | `DanceHall.Folktails` | Wellbeing | own: `art/models/FestivalSquare` | Festival | own | 30 Log, 30 Poles, 10 Paper | 200 |  |

#### Homes

| Building | Id | Basis | Toolbar | Model | Waits for | Icon | Cost | Science | Recipes |
|---|---|---|---|---|---|---|---|---|---|
| Den | `PandabornDen` | `Lodge.Folktails` | Housing | own: `art/models/Den` |  | own | 12 Log | 0 |  |
| Courtyard House | `PandabornCourtyardHouse` | `DoubleLodge.Folktails` | Housing | own: `art/models/CourtyardHouse` |  | own | 20 Log | 150 |  |
| Terrace House | `PandabornTerraceHouse` | `TripleLodge.Folktails` | Housing | own: `art/models/TerraceHouse` |  | own | 25 Log, 10 Poles | 250 |  |
| Moon Loft | `PandabornMoonLoft` | `Lodge.Folktails` | PandabornNightWatch | own: `art/models/MoonLoft` | Ringtails | own | 10 Log, 10 Poles | 200 |  |

#### Food

| Building | Id | Basis | Toolbar | Model | Waits for | Icon | Cost | Science | Recipes |
|---|---|---|---|---|---|---|---|---|---|
| Gatherer Flag | `GathererFlag` | re-theme | Food | vanilla, re-themed |  | vanilla | free | 0 |  |
| Efficient Farmhouse | `EfficientFarmHouse` | re-theme | Food | vanilla, re-themed |  | vanilla | 25 Log | 0 |  |
| Steamer | `PandabornSteamer` | `Grill.Folktails` | Food | own: `art/models/Steamer` |  | own | 20 Log, 5 Poles | 40 | `PandabornSteamedShoots`, `PandabornSteamedRice`, `PandabornBambooSeedCakesSteamed` |
| Pickle Yard | `PandabornPickleYard` | `Grill.Folktails` | Food | own: `art/models/PickleYard` |  | own | 20 Log, 15 Poles | 120 | `PandabornPickles` |
| Paddy House | `PandabornPaddyHouse` | `AquaticFarmhouse.Folktails` | Food | own: `art/models/PaddyHouse` |  | own | 30 Log, 10 Poles | 150 |  |
| Tea Roastery | `PandabornTeaRoastery` | `Bakery.Folktails` | Food | own: `art/models/TeaRoastery` |  | own | 15 Log, 20 Poles | 250 | `PandabornTea` |
| Trip-Hammer Mill | `PandabornTripHammerMill` | `Gristmill.Folktails` | Food | own: `art/models/TripHammerMill` | Water | own | 30 Log, 20 Poles, 10 Gear | 200 | `PandabornRiceFlour` |
| Kitchen | `PandabornKitchen` | `Bakery.Folktails` | Food | own: `art/models/Kitchen` | Water | own | 15 Log, 15 Poles, 10 Gear | 300 | `PandabornSweetRiceBalls`, `PandabornBambooSeedCakes` |
| Hot Pot Hall | `PandabornHotPotHall` | `Bakery.Folktails` | Food | own: `art/models/HotPotHall` |  | own | 40 Log, 40 Poles, 20 Gear | 800 | `PandabornHotPot` |

#### Wood and materials

| Building | Id | Basis | Toolbar | Model | Waits for | Icon | Cost | Science | Recipes |
|---|---|---|---|---|---|---|---|---|---|
| Lumberjack Flag | `LumberjackFlag` | re-theme | Wood | vanilla, re-themed |  | vanilla | free | 0 |  |
| Forester | `Forester` | re-theme | Wood | vanilla, re-themed |  | vanilla | 12 Log | 0 |  |
| Gear Workshop | `GearWorkshop` | re-theme | Wood | vanilla, re-themed |  | vanilla | 15 Log, 25 Poles | 100 |  |
| Paper Mill | `PaperMill` | re-theme | Wood | vanilla, re-themed |  | vanilla | 40 Log, 40 Poles, 15 Gear | 250 | `PandabornPaper` |
| Lantern Workshop | `PandabornLanternWorkshop` | `Bakery.Folktails` | Wood | own: `art/models/LanternWorkshop` |  | own | 10 Log, 20 Poles | 100 | `PandabornPaperLantern` |
| Pole Mill | `LumberMill` | re-theme | Wood | vanilla, re-themed |  | own | 15 Log | 0 |  |
| Smoke Kiln | `PandabornSmokeKiln` | `WoodWorkshop.Folktails` | Wood | own: `art/models/SmokeKiln` |  | own | 20 Log, 40 Poles, 20 Gear | 600 | `PandabornCuredPole` |
| Explosives Factory | `ExplosivesFactory` | re-theme | Landscaping | vanilla, re-themed |  | vanilla | 30 Poles, 30 Gear, 30 Metal Block | 400 |  |

#### Metal

| Building | Id | Basis | Toolbar | Model | Waits for | Icon | Cost | Science | Recipes |
|---|---|---|---|---|---|---|---|---|---|
| Scavenger Flag | `ScavengerFlag` | re-theme | Metal | vanilla, re-themed |  | vanilla | free | 250 |  |
| Smelter | `Smelter` | re-theme | Metal | vanilla, re-themed |  | vanilla | 50 Poles, 20 Gear, 30 Scrap Metal | 300 |  |
| Mine | `Mine` | re-theme | Metal | vanilla, re-themed |  | vanilla | 250 Log, 350 Gear, 200 Cured poles | 4000 |  |

#### Water

| Building | Id | Basis | Toolbar | Model | Waits for | Icon | Cost | Science | Recipes |
|---|---|---|---|---|---|---|---|---|---|
| Water Pump | `WaterPump` | re-theme | Water | vanilla, re-themed |  | vanilla | 12 Log | 0 |  |
| Large Water Pump | `LargeWaterPump` | re-theme | Water | vanilla, re-themed |  | vanilla | 20 Log, 5 Gear, 10 Cured poles | 400 |  |
| Mechanical Pump | `MechanicalPump` | re-theme | Water | vanilla, re-themed |  | vanilla | 50 Gear, 15 Cured poles | 2000 |  |
| Compact Mechanical Pump | `CompactMechanicalPump` | re-theme | Water | vanilla, re-themed |  | vanilla | 50 Gear, 25 Cured poles, 25 Metal Block | 4000 |  |
| Aquifer Drill | `AquiferDrill` | re-theme | Water | vanilla, re-themed |  | vanilla | 40 Poles, 25 Gear, 15 Metal Block | 400 |  |
| Badwater Pump | `BadwaterPump` | re-theme | Water | vanilla, re-themed |  | vanilla | 20 Log, 10 Gear, 5 Metal Block | 250 |  |
| Discharge | `Discharge` | re-theme | Water | vanilla, re-themed |  | vanilla | 10 Log, 10 Poles | 250 |  |
| Centrifuge | `Centrifuge` | re-theme | Water | vanilla, re-themed |  | vanilla | 60 Poles, 40 Gear, 30 Metal Block | 600 |  |
| Badwater Dome | `BadwaterDome` | re-theme | Water | vanilla, re-themed |  | vanilla | 100 Poles, 200 Gear, 100 Metal Block | 2000 |  |
| Badwater Rig | `BadwaterRig` | re-theme | Water | vanilla, re-themed |  | vanilla | 400 Gear, 200 Cured poles, 150 Metal Block | 4000 |  |
| Small Cistern | `PandabornCisternSmall` | `SmallTank.Folktails` | Storage | own: `art/models/Cistern` |  | own | 15 Log | 0 |  |
| Medium Cistern | `PandabornCisternMedium` | `MediumTank.Folktails` | Storage | own: `art/models/CisternMedium` |  | own | 20 Log, 30 Poles | 100 |  |
| Large Cistern | `PandabornCisternLarge` | `LargeTank.Folktails` | Storage | own: `art/models/CisternLarge` |  | own | 80 Poles, 40 Gear, 20 Metal Block | 500 |  |
| Stream Gauge | `StreamGauge` | re-theme | Decoration | vanilla, re-themed |  | vanilla | 2 Log, 4 Poles | 150 |  |
| Flume | `PandabornFlume` | `ThrottlingValve.Folktails` | Water | own: `art/models/Flume` | Water | own | 2 Poles | 0 |  |
| Flume Corner | `PandabornFlumeCorner` | `ThrottlingValve.Folktails` | Water | own: `art/models/FlumeCorner` | Water | own | 3 Poles | 0 |  |
| Flume Drop | `PandabornFlumeDrop` | `ThrottlingValve.Folktails` | Water | own: `art/models/FlumeDrop` | Water | own | 3 Poles | 0 |  |
| Flume Bridge | `PandabornFlumeBridge` | `ThrottlingValve.Folktails` | Water | own: `art/models/FlumeBridge` | Water | own | 4 Poles, 1 Log | 120 |  |
| Flume Bridge Span | `PandabornFlumeBridgeSpan` | `ThrottlingValve.Folktails` | Water | own: `art/models/FlumeBridgeSpan` | Water | own | 4 Poles, 1 Log | 120 |  |
| Flume Gate | `PandabornFlumeGate` | `ThrottlingValve.Folktails` | Water | own: `art/models/FlumeGate` | Water | own | 6 Log, 6 Poles | 40 |  |
| Scoop Wheel | `PandabornScoopWheel` | `WaterWheel.Folktails` | Water | own: `art/models/ScoopWheel` | Water | own | 20 Log, 30 Poles | 60 |  |
| Paddy Spout | `PandabornPaddySpout` | `FillValve.Folktails` | Water | own: `art/models/PaddySpout` | Water | own | 6 Poles | 150 |  |
| Cistern Tap | `PandabornCisternTap` | `Discharge.Folktails` | Water | own: `art/models/CisternTap` | Water | own | 8 Log, 8 Poles | 250 | `FlowingWater` |
| Dew Collector | `PandabornDewCollector` | `Grill.Folktails` | Water | own: `art/models/DewCollector` | Water | own | 15 Poles, 4 Paper | 300 | `PandabornDewWater` |
| Treadwheel Lift | `PandabornTreadwheelLift` | `PowerWheel.Folktails` | Water | **stand-in**: the basis's vanilla model (a kit model `art/models/TreadwheelLift` exists, not adopted) | Water | own | 30 Poles, 10 Gear | 300 |  |

#### Landscaping

| Building | Id | Basis | Toolbar | Model | Waits for | Icon | Cost | Science | Recipes |
|---|---|---|---|---|---|---|---|---|---|
| Levee | `Levee` | re-theme | Landscaping | vanilla, re-themed |  | vanilla | 12 Log | 120 |  |
| Dam | `Dam` | re-theme | Landscaping | vanilla, re-themed |  | vanilla | 20 Log | 0 |  |
| Floodgate | `Floodgate` | re-theme | Landscaping | vanilla, re-themed |  | vanilla | 10 Log, 5 Poles | 150 |  |
| Double Floodgate | `DoubleFloodgate` | re-theme | Landscaping | vanilla, re-themed |  | vanilla | 20 Log, 10 Poles | 250 |  |
| Triple Floodgate | `TripleFloodgate` | re-theme | Landscaping | vanilla, re-themed |  | vanilla | 30 Log, 15 Poles | 500 |  |
| Fill Valve | `FillValve` | re-theme | Landscaping | vanilla, re-themed |  | vanilla | 5 Poles, 5 Metal Block | 300 |  |
| Throttling Valve | `ThrottlingValve` | re-theme | Landscaping | vanilla, re-themed |  | vanilla | 5 Cured poles, 5 Metal Block | 500 |  |
| Impermeable Floor | `ImpermeableFloor` | re-theme | Landscaping | vanilla, re-themed |  | vanilla | 1 Metal Block | 200 |  |
| Contamination Barrier | `ContaminationBarrier` | re-theme | Landscaping | vanilla, re-themed |  | vanilla | 5 Poles, 1 Metal Block | 400 |  |
| Dynamite | `Dynamite` | re-theme | Landscaping | vanilla, re-themed |  | vanilla | 1 Explosives | 600 |  |
| Double Dynamite | `DoubleDynamite` | re-theme | Landscaping | vanilla, re-themed |  | vanilla | 1 Explosives, 1 Extract | 900 |  |
| Triple Dynamite | `TripleDynamite` | re-theme | Landscaping | vanilla, re-themed |  | vanilla | 1 Explosives, 2 Extract | 1200 |  |
| Tunnel | `Tunnel` | re-theme | Landscaping | vanilla, re-themed |  | vanilla | 1 Explosives, 1 Extract, 6 Poles | 2000 |  |
| Dirt Excavator | `DirtExcavator` | re-theme | Landscaping | vanilla, re-themed |  | vanilla | 100 Gear, 100 Cured poles, 50 Metal Block | 2000 |  |
| Terrain Block | `TerrainBlock` | re-theme | Landscaping | vanilla, re-themed |  | vanilla | 4 Dirt | 1000 |  |
| Dry-Stone Wall | `PandabornDryStoneWall` | `ContaminationBarrier.Folktails` | Landscaping | own: `art/models/DryStoneWall` |  | own | 4 Log, 2 Poles | 120 |  |

#### Power

| Building | Id | Basis | Toolbar | Model | Waits for | Icon | Cost | Science | Recipes |
|---|---|---|---|---|---|---|---|---|---|
| Power Wheel | `PowerWheel` | re-theme | Power | vanilla, re-themed |  | vanilla | 20 Log | 0 |  |
| Power Shaft | `PowerShaft` | re-theme | Power | vanilla, re-themed |  | vanilla | 1 Log | 0 |  |
| Impermeable Power Shaft | `ImpermeablePowerShaft` | re-theme | Power | vanilla, re-themed |  | vanilla | 12 Log, 6 Gear, 10 Metal Block | 300 |  |
| Vertical Power Shaft | `VerticalPowerShaft` | re-theme | Power | vanilla, re-themed |  | vanilla | 2 Log, 2 Poles, 1 Gear | 40 |  |
| Clutch | `Clutch` | re-theme | Power | vanilla, re-themed |  | vanilla | 2 Gear, 6 Metal Block | 400 |  |
| Gravity Battery | `GravityBattery` | re-theme | Power | vanilla, re-themed |  | vanilla | 40 Poles, 40 Gear, 10 Metal Block | 400 |  |
| Bamboo Water Wheel | `PandabornBambooWaterWheel` | `WaterWheel.Folktails` | Power | own: `art/models/BambooWaterWheel` |  | own | 30 Log, 15 Poles | 0 |  |
| Kite Windmill | `PandabornKiteWindmill` | `WindTurbine.Folktails` | Power | own: `art/models/KiteWindmill` |  | own | 20 Log, 20 Poles | 120 |  |
| Large Kite Windmill | `PandabornLargeKiteWindmill` | `LargeWindTurbine.Folktails` | Power | own: `art/models/LargeKiteWindmill` |  | own | 40 Poles, 20 Gear, 30 Paper | 1400 |  |
| Dev Power Generator (dev) | `DevPowerGenerator` | — | as basis | vanilla dev building, unchanged |  | vanilla | as basis | as basis |  |

#### Science and Wooden Oxen

| Building | Id | Basis | Toolbar | Model | Waits for | Icon | Cost | Science | Recipes |
|---|---|---|---|---|---|---|---|---|---|
| Inventor | `Inventor` | re-theme | Science | vanilla, re-themed |  | vanilla | 12 Log | 0 |  |
| Ox Workshop | `PandabornOxWorkshop` | `BotAssembler.Folktails` | Science | own: `art/models/OxWorkshop` |  | own | 100 Poles, 50 Gear, 40 Metal Block | 1000 | `PandabornWoodenOx` |
| Star Tower | `PandabornStarTower` | `Observatory.Folktails` | PandabornNightWatch | own: `art/models/StarTower` | **Ringtails, RingtailVenues off (hidden)** | own | 60 Poles, 30 Gear, 10 Paper | 1000 |  |

#### Storage

| Building | Id | Basis | Toolbar | Model | Waits for | Icon | Cost | Science | Recipes |
|---|---|---|---|---|---|---|---|---|---|
| Small Warehouse | `SmallWarehouse` | re-theme | Storage | vanilla, re-themed |  | vanilla | 3 Log | 0 |  |
| Medium Warehouse | `MediumWarehouse` | re-theme | Storage | vanilla, re-themed |  | vanilla | 15 Log | 0 |  |
| Large Warehouse | `LargeWarehouse` | re-theme | Storage | vanilla, re-themed |  | vanilla | 60 Log, 80 Poles | 250 |  |
| Small Pile | `SmallPile` | re-theme | Storage | vanilla, re-themed |  | vanilla | 2 Log | 0 |  |
| Large Pile | `LargePile` | re-theme | Storage | vanilla, re-themed |  | vanilla | 6 Log | 0 |  |
| Underground Pile | `UndergroundPile` | re-theme | Storage | vanilla, re-themed |  | vanilla | 20 Log, 40 Poles, 20 Gear | 1000 |  |

#### Paths and getting around

| Building | Id | Basis | Toolbar | Model | Waits for | Icon | Cost | Science | Recipes |
|---|---|---|---|---|---|---|---|---|---|
| Stairs | `Stairs` | re-theme | Paths | vanilla, re-themed |  | vanilla | 1 Log, 4 Poles | 70 |  |
| Spiral Stairs | `SpiralStairs` | re-theme | Paths | vanilla, re-themed |  | vanilla | 1 Log, 4 Cured poles | 350 |  |
| Platform | `Platform` | re-theme | Paths | vanilla, re-themed |  | vanilla | 6 Poles | 100 |  |
| Double Platform | `DoublePlatform` | re-theme | Paths | vanilla, re-themed |  | vanilla | 8 Poles | 150 |  |
| Triple Platform | `TriplePlatform` | re-theme | Paths | vanilla, re-themed |  | vanilla | 10 Poles | 200 |  |
| Overhang 2x1 | `Overhang2x1` | re-theme | Paths | vanilla, re-themed |  | vanilla | 10 Log, 10 Poles, 4 Metal Block | 350 |  |
| Overhang 3x1 | `Overhang3x1` | re-theme | Paths | vanilla, re-themed |  | vanilla | 15 Log, 15 Poles, 6 Metal Block | 550 |  |
| Overhang 4x1 | `Overhang4x1` | re-theme | Paths | vanilla, re-themed |  | vanilla | 20 Log, 20 Poles, 8 Metal Block | 1000 |  |
| Overhang 5x1 | `Overhang5x1` | re-theme | Paths | vanilla, re-themed |  | vanilla | 30 Log, 30 Poles, 10 Metal Block | 1800 |  |
| Overhang 6x1 | `Overhang6x1` | re-theme | Paths | vanilla, re-themed |  | vanilla | 36 Log, 36 Poles, 12 Metal Block | 3000 |  |
| Suspension Bridge 1x1 | `SuspensionBridge1x1` | re-theme | Paths | vanilla, re-themed |  | vanilla | 4 Log, 4 Poles | 150 |  |
| Suspension Bridge 2x1 | `SuspensionBridge2x1` | re-theme | Paths | vanilla, re-themed |  | vanilla | 8 Log, 8 Poles | 250 |  |
| Suspension Bridge 3x1 | `SuspensionBridge3x1` | re-theme | Paths | vanilla, re-themed |  | vanilla | 12 Log, 12 Poles | 400 |  |
| Suspension Bridge 4x1 | `SuspensionBridge4x1` | re-theme | Paths | vanilla, re-themed |  | vanilla | 16 Log, 16 Poles | 600 |  |
| Suspension Bridge 5x1 | `SuspensionBridge5x1` | re-theme | Paths | vanilla, re-themed |  | vanilla | 20 Log, 20 Poles | 1000 |  |
| Suspension Bridge 6x1 | `SuspensionBridge6x1` | re-theme | Paths | vanilla, re-themed |  | vanilla | 24 Log, 24 Poles | 1800 |  |
| Metal Platform 3x3 | `MetalPlatform3x3` | re-theme | Paths | vanilla, re-themed |  | vanilla | 30 Metal Block | 1000 |  |
| Metal Platform 5x5 | `MetalPlatform5x5` | re-theme | Paths | vanilla, re-themed |  | vanilla | 90 Metal Block | 2000 |  |
| Gate | `Gate` | re-theme | Paths | vanilla, re-themed |  | vanilla | 6 Poles, 4 Gear, 4 Scrap Metal | 200 |  |
| Airlock | `Airlock` | re-theme | Paths | vanilla, re-themed |  | vanilla | 15 Log, 8 Gear, 4 Metal Block | 300 |  |
| Zipline Station | `ZiplineStation` | re-theme | Paths | vanilla, re-themed |  | vanilla | 20 Log, 40 Poles, 20 Metal Block | 700 |  |
| Zipline Pylon | `ZiplinePylon` | re-theme | Paths | vanilla, re-themed |  | vanilla | 20 Poles, 10 Gear, 10 Metal Block | 500 |  |
| Zipline Beam | `ZiplineBeam` | re-theme | Paths | vanilla, re-themed |  | vanilla | 20 Poles, 10 Gear, 10 Metal Block | 600 |  |
| Dev Water Source (dev) | `DevWaterSource` | — | as basis | vanilla dev building, unchanged |  | vanilla | as basis | as basis |  |

#### Leisure and care

| Building | Id | Basis | Toolbar | Model | Waits for | Icon | Cost | Science | Recipes |
|---|---|---|---|---|---|---|---|---|---|
| Campfire | `Campfire` | re-theme | Wellbeing | vanilla, re-themed |  | vanilla | 15 Log | 0 |  |
| Hammock | `PandabornHammock` | `Hammock.Folktails` | Wellbeing | own: `art/models/Hammock` |  | own | 4 Log | 0 |  |
| Nap Platform | `PandabornNapPlatform` | `RooftopTerrace.Folktails` | Wellbeing | own: `art/models/NapPlatform` |  | own | 10 Log, 15 Poles | 100 |  |
| Teahouse | `PandabornTeahouse` | `Campfire.Folktails` | Wellbeing | own: `art/models/Teahouse` |  | own | 25 Log, 25 Poles | 150 |  |
| Slide and Swing | `PandabornSlideAndSwing` | `Lido.Folktails` | Wellbeing | own: `art/models/SlideAndSwing` |  | own | 25 Log, 20 Poles | 250 |  |
| Kindergarten | `PandabornKindergarten` | `Campfire.Folktails` | Wellbeing | own: `art/models/Kindergarten` |  | own | 60 Log, 40 Poles | 400 |  |
| Ink Studio | `PandabornInkStudio` | `ContemplationSpot.Folktails` | Wellbeing | own: `art/models/InkStudio` |  | own | 10 Log, 10 Paper | 200 |  |
| Hot Spring Bath | `PandabornHotSpringBath` | `MudPit.Folktails` | Wellbeing | own: `art/models/HotSpringBath` |  | own | 80 Log, 30 Cured poles | 1500 |  |
| Opera Stage | `PandabornOperaStage` | `DanceHall.Folktails` | Wellbeing | own: `art/models/OperaStage` |  | own | 100 Log, 40 Cured poles, 20 Metal Block | 1200 |  |
| Teeth Grindstone | `TeethGrindstone` | re-theme | Wellbeing | vanilla, re-themed |  | vanilla | 5 Log | 0 |  |
| Medical Bed | `MedicalBed` | re-theme | Wellbeing | vanilla, re-themed |  | vanilla | 5 Log, 1 Poles | 80 |  |
| Herbalist | `Herbalist` | re-theme | Wellbeing | vanilla, re-themed |  | vanilla | 10 Poles, 20 Gear | 300 |  |
| Shower | `Shower` | re-theme | Wellbeing | vanilla, re-themed |  | vanilla | 10 Log, 1 Poles | 50 |  |

#### Ringtail workplaces

| Building | Id | Basis | Toolbar | Model | Waits for | Icon | Cost | Science | Recipes |
|---|---|---|---|---|---|---|---|---|---|
| Night Builders' Post | `PandabornNightBuildersPost` | `BuildersHut.Folktails` | PandabornNightWatch | own: `art/models/NightBuildersPost` | Ringtails | own | 15 Log, 10 Poles | 50 |  |
| Night Courier Post | `PandabornNightCourierPost` | `HaulingPost.Folktails` | PandabornNightWatch | own: `art/models/NightCourierPost` | Ringtails | own | 20 Log, 10 Poles | 150 |  |
| Night Gatherers' Post | `PandabornNightForagersPost` | `GathererFlag.Folktails` | PandabornNightWatch | own: `art/models/NightForagersPost` | Ringtails | own | 10 Poles | 100 |  |

#### Decoration

| Building | Id | Basis | Toolbar | Model | Waits for | Icon | Cost | Science | Recipes |
|---|---|---|---|---|---|---|---|---|---|
| Standing Lantern | `PandabornStandingLantern` | `Lantern.Folktails` | Decoration | own: `art/models/StandingLantern` |  | own | 2 Poles, 1 Paper lanterns | 100 |  |
| Hanging Lantern | `PandabornHangingLantern` | `Lantern.Folktails` | Decoration | own: `art/models/HangingLantern` |  | own | 2 Poles, 1 Paper lanterns | 0 |  |
| String Lanterns | `PandabornStringLanterns` | `Lantern.Folktails` | Decoration | own: `art/models/StringLanterns` |  | own | 2 Poles, 3 Paper lanterns | 0 |  |
| Bamboo Fence | `PandabornBambooFence` | `WoodFence.Folktails` | Decoration | own: `art/models/BambooFence` |  | own | 3 Poles | 150 |  |
| Hedge | `Hedge` | re-theme | Decoration | vanilla, re-themed |  | vanilla | 3 Log | 150 |  |
| Shrub | `Shrub` | re-theme | Decoration | vanilla, re-themed |  | vanilla | 12 Log | 0 |  |
| Potted Pine | `PandabornPottedPine` | `Shrub.Folktails` | Decoration | own: `art/models/PottedPine` |  | own | 6 Poles | 0 |  |
| Panda Statue | `PandabornPandaStatue` | `BeaverStatue.Folktails` | Decoration | own: `art/models/PandaStatue` |  | own | 50 Log, 10 Poles | 500 |  |
| Bamboo Pinwheel | `PandabornBambooPinwheel` | `Weathervane.Folktails` | Decoration | own: `art/models/BambooPinwheel` |  | own | 5 Log, 1 Poles | 250 |  |
| Scarecrow | `Scarecrow` | re-theme | Decoration | vanilla, re-themed |  | vanilla | 5 Log, 10 Paper | 200 |  |
| Bench | `Bench` | re-theme | Decoration | vanilla, re-themed |  | vanilla | 6 Log, 2 Poles | 80 |  |
| Pole Banner | `PoleBanner` | re-theme | Decoration | vanilla, re-themed |  | vanilla | 4 Log, 4 Poles, 1 Extract | 700 |  |
| Square Banner | `SquareBanner` | re-theme | Decoration | vanilla, re-themed |  | vanilla | 2 Log, 4 Poles, 1 Extract | 700 |  |
| Goldfish Bowl | `PandabornGoldfishBowl` | `Shrub.Folktails` | Decoration | own: `art/models/GoldfishBowl` |  | own | 50 Log, 10 Poles | 0 |  |
| Garden Moon Gate | `PandabornGardenMoonGate` | `Shrub.Folktails` | Decoration | own: `art/models/GardenMoonGate` |  | own | 50 Log, 10 Poles | 0 |  |
| Roof 1x1 | `Roof1x1` | re-theme | Decoration | vanilla, re-themed |  | vanilla | 2 Log, 1 Poles | 60 |  |
| Roof 1x2 | `Roof1x2` | re-theme | Decoration | vanilla, re-themed |  | vanilla | 4 Log, 2 Poles | 80 |  |
| Roof 2x2 | `Roof2x2` | re-theme | Decoration | vanilla, re-themed |  | vanilla | 4 Log, 2 Poles | 120 |  |
| Roof 2x3 | `Roof2x3` | re-theme | Decoration | vanilla, re-themed |  | vanilla | 6 Log, 3 Poles | 150 |  |
| Roof 3x2 | `Roof3x2` | re-theme | Decoration | vanilla, re-themed |  | vanilla | 6 Log, 3 Poles | 150 |  |

#### Monuments and the wonder

| Building | Id | Basis | Toolbar | Model | Waits for | Icon | Cost | Science | Recipes |
|---|---|---|---|---|---|---|---|---|---|
| Memorial Arch | `PandabornMemorialArch` | `BrazierOfBonding.Folktails` | Monuments | own: `art/models/MemorialArch` |  | own | 250 Log, 800 Poles | 3000 |  |
| Great Sitting Panda | `PandabornGreatSittingPanda` | `HallOfAbundance.Folktails` | Monuments | own: `art/models/GreatSittingPanda` |  | own | 1400 Poles, 700 Cured poles, 650 Metal Block | 15000 |  |
| Sky Lantern | `PandabornSkyLantern` | `EarthRecultivator.Folktails` | Monuments | own: `art/models/SkyLantern` |  | own | 2400 Gear, 2400 Cured poles, 1800 Metal Block, 500 Paper | 20000 |  |

#### Automation

| Building | Id | Basis | Toolbar | Model | Waits for | Icon | Cost | Science | Recipes |
|---|---|---|---|---|---|---|---|---|---|
| Chronometer | `Chronometer` | re-theme | Automation | vanilla, re-themed |  | vanilla | 8 Poles, 6 Gear | 150 |  |
| Contamination Sensor | `ContaminationSensor` | re-theme | Automation | vanilla, re-themed |  | vanilla | 8 Gear, 8 Metal Block | 400 |  |
| Depth Sensor | `DepthSensor` | re-theme | Automation | vanilla, re-themed |  | vanilla | 4 Gear, 8 Scrap Metal | 200 |  |
| Detonator | `Detonator` | re-theme | Automation | vanilla, re-themed |  | vanilla | 1 Metal Block, 1 Explosives, 1 Extract | 1400 |  |
| Firework Launcher | `FireworkLauncher` | re-theme | Automation | vanilla, re-themed |  | vanilla | 1 Gear, 2 Cured poles | 700 |  |
| Flow Sensor | `FlowSensor` | re-theme | Automation | vanilla, re-themed |  | vanilla | 6 Poles, 4 Gear | 100 |  |
| HTTP Adapter | `HttpAdapter` | re-theme | Automation | vanilla, re-themed |  | vanilla | 2 Gear, 4 Scrap Metal | 7500 |  |
| HTTP Lever | `HttpLever` | re-theme | Automation | vanilla, re-themed |  | vanilla | 2 Gear, 2 Scrap Metal | 5000 |  |
| Indicator | `Indicator` | re-theme | Automation | vanilla, re-themed |  | vanilla | 2 Scrap Metal, 1 Poles | 400 |  |
| Lever | `Lever` | re-theme | Automation | vanilla, re-themed |  | vanilla | 1 Poles, 2 Gear | 50 |  |
| Memory | `Memory` | re-theme | Automation | vanilla, re-themed |  | vanilla | 1 Metal Block, 1 Extract | 1000 |  |
| Population Counter | `PopulationCounter` | re-theme | Automation | vanilla, re-themed |  | vanilla | 2 Poles, 2 Gear, 1 Paper | 200 |  |
| Power Meter | `PowerMeter` | re-theme | Automation | vanilla, re-themed |  | vanilla | 10 Gear, 6 Metal Block | 600 |  |
| Relay | `Relay` | re-theme | Automation | vanilla, re-themed |  | vanilla | 1 Poles, 1 Gear | 80 |  |
| Resource Counter | `ResourceCounter` | re-theme | Automation | vanilla, re-themed |  | vanilla | 4 Poles, 4 Gear, 1 Paper | 250 |  |
| Science Counter | `ScienceCounter` | re-theme | Automation | vanilla, re-themed |  | vanilla | 6 Gear, 4 Scrap Metal, 6 Paper | 300 |  |
| Speaker | `Speaker` | re-theme | Automation | vanilla, re-themed |  | vanilla | 4 Poles, 2 Gear, 4 Metal Block | 500 |  |
| Timer | `Timer` | re-theme | Automation | vanilla, re-themed |  | vanilla | 1 Cured poles, 1 Metal Block | 600 |  |
| Weather Station | `WeatherStation` | re-theme | Automation | vanilla, re-themed |  | vanilla | 10 Gear, 8 Cured poles | 300 |  |

### Goods

19 goods of our own in `catalogue/goods.toml`. Poles mode is `rename` (Poles and Cured poles are the vanilla `Plank` and `TreatedPlank`, renamed and re-iconed for Inkpaws only). Vanilla goods kept beyond the Common collection: `Paper`, `Antidote`, `Dandelion`, `TreatedPlank`.

| Good | Id | Basis | Eating it gives | Made by | Used by | Waits for | Icon |
|---|---|---|---|---|---|---|---|
| Bamboo shoots | `PandabornBambooShoots` | `Carrot` | Hunger 0.3 | plant `PandabornShootBamboo` | recipe `PandabornSteamedShoots` |  | own |
| Cabbages | `PandabornCabbage` | `Carrot` | Hunger 0.3, PandabornCabbage 0.2 | plant `PandabornCabbage` | recipe `PandabornPickles`; recipe `PandabornHotPot` |  | own |
| Persimmons | `PandabornPersimmons` | `Carrot` | Hunger 0.3, PandabornPersimmons 0.2 | plant `PandabornPersimmonTree` | recipe `PandabornSweetRiceBalls` |  | own |
| Bamboo mushrooms | `PandabornBambooMushrooms` | `Carrot` | Hunger 0.3, PandabornBambooMushrooms 0.2 | plant `PandabornTimberBamboo` | recipe `PandabornHotPot` |  | own |
| Steamed shoots | `PandabornSteamedShoots` | `GrilledPotato` | Hunger 0.3, PandabornSteamedShoots 0.2 | recipe `PandabornSteamedShoots` | Lantern Festival |  | own |
| Pickles | `PandabornPickles` | `GrilledPotato` | Hunger 0.3, PandabornPickles 0.2 | recipe `PandabornPickles` | Lantern Festival |  | own |
| Steamed rice | `PandabornSteamedRice` | `Bread` | Hunger 0.3, PandabornSteamedRice 0.2 | recipe `PandabornSteamedRice` | Lantern Festival |  | own |
| Sweet rice balls | `PandabornSweetRiceBalls` | `CattailCracker` | Hunger 0.3, PandabornSweetRiceBalls 0.2 | recipe `PandabornSweetRiceBalls` | Lantern Festival | Water | own |
| Hot pot | `PandabornHotPot` | `MaplePastry` | Hunger 0.3, PandabornHotPot 0.2 | recipe `PandabornHotPot` | Lantern Festival |  | own |
| Bamboo seed cakes | `PandabornBambooSeedCakes` | `MaplePastry` | Hunger 0.3, PandabornBambooSeedCakes 0.2 | recipe `PandabornBambooSeedCakes`; recipe `PandabornBambooSeedCakesSteamed` | Lantern Festival | Flowering | own |
| Tea | `PandabornTea` | `WheatFlour` | not eaten | recipe `PandabornTea` | `PandabornTeahouse` |  | own |
| Rice | `PandabornRice` | `Wheat` | not eaten | plant `PandabornRice` | recipe `PandabornSteamedRice`; recipe `PandabornRiceFlour` |  | own |
| Rice flour | `PandabornRiceFlour` | `WheatFlour` | not eaten | recipe `PandabornRiceFlour` | recipe `PandabornSweetRiceBalls`; recipe `PandabornBambooSeedCakes` | Water | own |
| Sichuan pepper | `PandabornSichuanPepper` | `Wheat` | not eaten | plant `PandabornSichuanPepper` | recipe `PandabornHotPot` |  | own |
| Tea leaves | `PandabornTeaLeaves` | `Wheat` | not eaten | plant `PandabornTeaBush` | recipe `PandabornTea` |  | own |
| Bamboo seed | `PandabornBambooSeed` | `SunflowerSeeds` | not eaten | plant `PandabornShootBambooInFlower`; plant `PandabornTimberBambooInFlower` | recipe `PandabornBambooSeedCakes`; recipe `PandabornBambooSeedCakesSteamed` | Flowering | own |
| Poles | `PandabornPole` | `Plank` | not eaten | — | — | not generated (poles mode is `rename`) | own |
| Cured poles | `PandabornCuredPole` | `TreatedPlank` | not eaten | — | — | not generated (poles mode is `rename`) | own |
| Paper lanterns | `PandabornPaperLantern` | `Book` | not eaten | recipe `PandabornPaperLantern` | building costs; `PandabornSkyLantern`; Lantern Festival |  | own |

### Needs

26 needs of our own in `catalogue/needs.toml`, all in the collection `Needs.Inkpaws`. Vanilla needs kept beyond Common: `Antidote`, `Scarecrow`. *Per day* is the daily change; *Wellbeing* the points when satisfied.

| Need | Id | Group | Per day | Wellbeing | Met by | Waits for |
|---|---|---|---|---|---|---|
| Nap | `PandabornNap` | Fun | -0.6 | 3 | Hammock; Nap Platform |  |
| Tea | `PandabornTea` | SocialLife | -0.4 | 4 | Teahouse |  |
| Play | `PandabornPlay` | Fun | -0.2 | 2 | Slide and Swing |  |
| Watching the young | `PandabornCubWatching` | SocialLife | -0.2 | 3 | Kindergarten |  |
| Soak | `PandabornSoak` | Fun | -0.2 | 3 | Hot Spring Bath |  |
| Ink painting | `PandabornContemplation` | Fun | -0.12 | 2 | Ink Studio |  |
| Opera | `PandabornPerformance` | Fun | -0.12 | 5 | Opera Stage |  |
| Cabbages | `PandabornCabbage` | Nutrition | -0.05 | 1 | eating cabbages |  |
| Persimmons | `PandabornPersimmons` | Nutrition | -0.05 | 1 | eating persimmons |  |
| Bamboo mushrooms | `PandabornBambooMushrooms` | Nutrition | -0.05 | 1 | eating bamboo mushrooms |  |
| Steamed shoots | `PandabornSteamedShoots` | Nutrition | -0.05 | 2 | eating steamed shoots |  |
| Pickles | `PandabornPickles` | Nutrition | -0.05 | 2 | eating pickles |  |
| Steamed rice | `PandabornSteamedRice` | Nutrition | -0.05 | 2 | eating steamed rice |  |
| Sweet rice balls | `PandabornSweetRiceBalls` | Nutrition | -0.05 | 3 | eating sweet rice balls | Water |
| Hot pot | `PandabornHotPot` | Nutrition | -0.05 | 4 | eating hot pot |  |
| Bamboo seed cakes | `PandabornBambooSeedCakes` | Nutrition | -0.05 | 3 | eating bamboo seed cakes | Flowering |
| Festive spirit | `PandabornFestive` | Boosts | -0.04 | 4 | a Lantern Festival | Festival |
| Memorial Arch | `PandabornMemorialArch` | Awe | -0.3 | 6 | Memorial Arch |  |
| Great Sitting Panda | `PandabornGreatSittingPanda` | Awe | -0.3 | 14 | Great Sitting Panda |  |
| Sky Lantern | `PandabornSkyLantern` | Awe | -0.01 | 10 | Sky Lantern |  |
| Panda Statue | `PandabornPandaStatue` | as `BeaverStatue` | as basis | as basis | Panda Statue |  |
| Bamboo Pinwheel | `PandabornBambooPinwheel` | as `Weathervane` | as basis | as basis | Bamboo Pinwheel |  |
| Goldfish Bowl | `PandabornGoldfishBowl` | as `BeaverStatue` | as basis | as basis | Goldfish Bowl |  |
| Garden Moon Gate | `PandabornGardenMoonGate` | as `BeaverStatue` | as basis | as basis | Garden Moon Gate |  |
| String Lanterns | `PandabornStringLanterns` | as `Lantern` | as basis | as basis | String Lanterns |  |
| Grand festive spirit | `PandabornFestiveGrand` | Boosts | -0.04 | 1 | a Grand Festival | Festival |

### Recipes

14 recipes in `catalogue/recipes.toml`. Workshop stores are sized by `rules.toml [shelves]` (`workshop_hours = 48`), not by the recipe's own capacity.

| Recipe | Ingredients | Products | Hours | Fuel | Made at | Waits for |
|---|---|---|---|---|---|---|
| `PandabornSteamedShoots` | 1 Bamboo shoots | 2 Steamed shoots | 0.5 | Log | Steamer |  |
| `PandabornSteamedRice` | 1 Rice | 4 Steamed rice | 1.0 | Log | Steamer |  |
| `PandabornPickles` | 2 Cabbages | 5 Pickles | 1.7 |  | Pickle Yard |  |
| `PandabornRiceFlour` | 1 Rice | 1 Rice flour | 0.5 |  | Trip-Hammer Mill | Water |
| `PandabornSweetRiceBalls` | 1 Rice flour, 1 Persimmons | 5 Sweet rice balls | 1.0 | Log | Kitchen | Water |
| `PandabornBambooSeedCakes` | 1 Bamboo seed, 1 Rice flour | 6 Bamboo seed cakes | 1.5 | Log | Kitchen | Flowering, Water |
| `PandabornBambooSeedCakesSteamed` | 1 Bamboo seed | 2 Bamboo seed cakes | 1.0 | Log | Steamer | Flowering |
| `PandabornHotPot` | 1 Cabbages, 1 Sichuan pepper, 1 Bamboo mushrooms | 8 Hot pot | 1.5 | Log | Hot Pot Hall |  |
| `PandabornTea` | 1 Tea leaves | 2 Tea | 0.75 |  | Tea Roastery |  |
| `PandabornPaper` | 1 Poles | 2 Paper | 1.56 |  | Paper Mill |  |
| `PandabornPaperLantern` | 2 Paper, 1 Poles | 2 Paper lanterns | 1.5 |  | Lantern Workshop |  |
| `PandabornCuredPole` | 1 Poles | 1 Cured poles | 3.0 | Log | Smoke Kiln |  |
| `PandabornWoodenOx` | 20 Cured poles, 20 Gear, 4 Metal Block | nothing | 96.0 |  | Ox Workshop |  |
| `PandabornDewWater` | nothing | 1 Water | 7.5 |  | Dew Collector |  |

### Plants

9 plants in `catalogue/plants.toml`, collection `NaturalResources.Inkpaws`. Vanilla plants kept beyond Common: `Dandelion`.

| Plant | Id | Basis | Planted by | Grows (days) | Yield | Water rule | Model | Waits for |
|---|---|---|---|---|---|---|---|---|
| Shoot Bamboo | `PandabornShootBamboo` | `Carrot` | Farmhouse | 3 | cut: 2 Bamboo shoots | dies after 5 dry days; dies after 2 days under water | own: `art/plants/PandabornShootBamboo` |  |
| Cabbage | `PandabornCabbage` | `Carrot` | Farmhouse | 5 | cut: 3 Cabbages | dies after 7 dry days; dies after 2 days under water | own: `art/plants/PandabornCabbage` |  |
| Timber Bamboo | `PandabornTimberBamboo` | `ChestnutTree` | Forester | 5 | cut: 2 Poles; gathered every 3 days: 2 Bamboo mushrooms | dies after 10 dry days; dies after 8 days under water | own: `art/plants/PandabornTimberBamboo` |  |
| Rice | `PandabornRice` | `Cattail` | AquaticFarmhouse | 8 | cut: 3 Rice | dies after 1 dry days; needs standing water (`flood_min` 1, `flood_max` 1), dies after 1.5 days outside it | own: `art/plants/PandabornRice` |  |
| Tea Bush | `PandabornTeaBush` | `BlueberryBush` | Forester | 6 | gathered every 3 days: 3 Tea leaves | dry ground only: dies after 3 days on moist soil; dies after 3 days under water | own: `art/plants/PandabornTeaBush` |  |
| Sichuan Pepper | `PandabornSichuanPepper` | `BlueberryBush` | Forester | 5 | gathered every 3 days: 2 Sichuan pepper | dry ground only: dies after 3 days on moist soil; dies after 3 days under water | own: `art/plants/PandabornSichuanPepper` |  |
| Persimmon Tree | `PandabornPersimmonTree` | `ChestnutTree` | Forester | 14 | cut: 3 Log; gathered every 6 days: 3 Persimmons | dies after 10 dry days; dies after 10 days under water | own: `art/plants/PandabornPersimmonTree` |  |
| Flowering Shoot Bamboo | `PandabornShootBambooInFlower` | `Carrot` | nobody (appears in a Flowering) | as basis | cut: 3 Bamboo seed | as basis | own: `art/plants/PandabornShootBambooInFlower` | Flowering |
| Flowering Timber Bamboo | `PandabornTimberBambooInFlower` | `ChestnutTree` | nobody (appears in a Flowering) | as basis | cut: 3 Bamboo seed | as basis | own: `art/plants/PandabornTimberBambooInFlower` | Flowering |

### Characters

| Character | Template | Basis | Body mesh | In `Characters.Inkpaws` | Waits for |
|---|---|---|---|---|---|
| adult | `InkpawAdult.Inkpaws` | `Characters/Beaver/BeaverAdult` | `Characters/Pandaborn/InkpawAdult.Model` | yes |  |
| child | `InkpawChild.Inkpaws` | `Characters/Beaver/BeaverChild` | `Characters/Pandaborn/InkpawChild.Model` | yes |  |
| ringtail_adult | `RingtailAdult.Inkpaws` | `Characters/Beaver/BeaverAdult` | `Characters/Pandaborn/RingtailAdult.Model` | no (made by code) | Ringtails |
| ringtail_child | `RingtailChild.Inkpaws` | `Characters/Beaver/BeaverChild` | `Characters/Pandaborn/RingtailChild.Model` | no (made by code) | Ringtails |
| bot | `Bot.Inkpaws` | `Bot.Folktails` | `Characters/Pandaborn/WoodenOx.Model` | yes |  |

<!-- generated:end -->
