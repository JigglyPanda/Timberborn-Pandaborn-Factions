# Vanilla mechanics bible (Timberborn 1.1.2.8)

Status: research note, 2026-11-14. Read from the decompiled game and vanilla data; nothing here was observed in a
running game. This is the reference every design idea is checked against. It describes what colonists actually do
minute to minute, not only what the specs say.

**Companion notes (not repeated here):** [water.md](water.md) (water simulation, valves, flumes, moisture zones for
crops), [two-peoples.md](two-peoples.md) (worker types, shift flipping, hidden templates, sleep insertion).

**Paths.** `Asm/Class` = `E:\PandabornDev\reference\decompiled\Timberborn.<Asm>.dll\Timberborn.<Asm>\<Class>.cs`
(namespace folder can differ slightly; search by class name). `BP/...` = `E:\PandabornDev\reference\Blueprints\...`.
`loc` = `E:\PandabornDev\reference\Localizations\enUS.csv`.

**Basis tags.** **[code]** read in decompiled C#. **[data]** read in a blueprint. **[loc]** read in a tooltip or
string. **[inferred]** arithmetic or interpretation from the above, not traced end to end. Untagged numbers in a
table take the tag in the table caption.

**Units.** 1 tick = 0.6 s real at 1×. 1 day = 768 ticks = 24 game hours. 1 game hour = 32 ticks = 19.2 s real at
1×. "Tiles" = grid cells. Need points run roughly 0 to 1.

## Contents

1. [Time](#1-time)
2. [A colonist's day](#2-a-colonists-day)
3. [Needs and wellbeing](#3-needs-and-wellbeing)
4. [Work and production](#4-work-and-production)
5. [Hauling and logistics](#5-hauling-and-logistics)
6. [Construction, science, demolition](#6-construction-science-demolition)
7. [Farming and forestry](#7-farming-and-forestry)
8. [Water, soil and power](#8-water-soil-and-power)
9. [Population](#9-population)
10. [Bots](#10-bots)
11. [Districts, paths, vertical building](#11-districts-paths-vertical-building)
12. [Difficulty and game modes](#12-difficulty-and-game-modes)
13. [Attractions, decorations, area effects](#13-attractions-decorations-area-effects)
14. [Automation and other 1.0/1.1 systems](#14-automation-and-other-1011-systems)
15. [Rules of thumb](#15-rules-of-thumb)
16. [Things that surprise designers](#16-things-that-surprise-designers)

---

## 1. Time

### 1.1 Day length and game speed

| Item | Value | Source |
|---|---|---|
| Tick | 0.6 s real at 1× | `BP/Configurations/TickTime` [data] |
| Day | 768 ticks = 460.8 s real at 1× | `BP/Configurations/DayNightCycle`, `TimeSystem/DayNightCycle` [data, code] |
| Game hour | 32 ticks = 19.2 s real at 1×; `FixedDeltaTimeInHours` = 0.03125 | `DayNightCycle.InitializeConfigurationValues` [code] |
| Daytime | hours 0–16 (`ConfiguredDaytimeLengthInHours` 16) | [data] |
| Night | hours 16–24 (8 h) | `DayNightCycle.BoundsInHours` [code] |
| Sunrise/sunset visuals | 2 h, transition 1 h (cosmetic) | `BP/Configurations/DayStageCycle` [data] |
| New game starts at | hour 4 of day 1 | `HoursPassedOnNewGame` 4 [data] |
| "Dawn" for all logic | hour 0 (`HoursToNextStartOf(Daytime)`) | [code] |

Speed buttons in game: **pause, 1×, 3×, 7×** (`UI/Views/Game/SpeedControlPanel.uxml`: `Speed0/1/3/7`) [data]. Dev
speeds 0.25×, 30×, 99× (`TimeSystemUI/SpeedControlPanel`) [code].

**Large colonies run slower.** `Characters/GameSpeedThrottler` scales any speed above 1×: effective =
lerp(1, speed, scale), scale falls linearly from 1.0 at ≤30 characters to 0.4 at ≥200 (`BP/Configurations/
GameSpeedThrottler`) [code, data]. At 200+ characters, 3× is really 1.8× and 7× is 3.4×.

| Real seconds per game day | ≤30 characters | 200+ characters |
|---|---|---|
| 1× | 460.8 | 460.8 |
| 3× | 153.6 | 256 |
| 7× | 65.8 | 135.5 |

[inferred]

### 1.2 Working hours

`WorkSystem/WorkingHoursManager` [code]:

* **One colony-wide schedule.** There is no per-district, per-building or per-worker schedule.
* **Work always starts at hour 0 (dawn).** `_startHours` is the daytime start and is never changed. The player only
  sets the length: `EndHours = WorkedPartOfDay × 24`.
* The top-bar panel (`WorkSystemUI/WorkingHoursPanel`) steps in **whole hours from 0 to 24**. Default = daytime =
  **16 h** (hours 0–16).
* `AreWorkingHours` = `WorkedPartOfDay > 0 && 0 ≤ hour < EndHours`. At 24 every hour is a working hour; at 0 no
  beaver works.
* Per worker: `WorkerWorkingHours.AreWorkingHours` = true always if the worker type has `IgnoresWorkingHours`
  (bots), else the global value. `WorkplaceWorkingHours` does the same for a building, keyed by its current worker
  type (used by productivity counters).
* A bell sound (`WorkingHoursBell`) and `WorkingHoursTransitionedEvent` mark the transitions.

So "dusk" can be off-duty only if the player shortens the day below 16 h; "dawn" is never off-duty unless hours are 0.

### 1.3 What colonists do outside working hours

`WorkSystem/WorkerRootBehavior.Decide` [code]: an employed beaver in working hours works; otherwise it runs
`CommunityServiceBehavior`, whose only vanilla implementation is Iron Teeth breeding-pod nutrient delivery
(`BringNutrientBehavior`; loc: "Nutrients are brought by haulers, the unemployed, and workers after work"). Then
the need loop (§2) takes over: eat, drink, attractions, decorations, then sleep near dawn, else wander.

**Nobody hauls, builds, farms or produces outside working hours except bots**, deliveries already in hands (§2.1),
and buildings that run with no workers (§4.6) [code].

### 1.4 Sleep

`SleepSystem/Sleeper`, `SleepNeedBehavior`, `BeaverBehavior/BeaverNeedBehaviorPicker` [code]; numbers [data]:

* Sleep need: max 0.8, min −0.2, decays −0.6/day. Home sleep effect +0.2/h (every dwelling); sleeping outside
  +0.15/h; ×0.66 when sleeping "critically" (Sleep at its minimum).
* **When a beaver goes to bed.** Sleep is the one "essential" need behaviour. It is picked when there is **no
  other useful need action** left that fits in (hours to dawn − sleep duration), **and** hours to dawn < 1.2 × the
  time to walk home and fill Sleep to max. It is also picked if Sleep sits at its minimum and outranks the best
  other action.
* **When it wakes.** At dawn (+0–0.25 h random, `MaxOffsetInHours`) if the time to fill Sleep is within 1 h of the
  time to dawn; otherwise when Sleep is full. Newborns sleep at least 24 h.
* **How long.** A day costs 0.6 Sleep, home refills 0.2/h, so a beaver needs about **3 h of sleep a night** and
  goes to bed roughly 3–4 h before dawn (≈ hour 20–21) [inferred].
* Critically tired beavers sleep at home only if home is within 13 tiles (heuristic distance); else on the spot.
* Homeless beavers sleep outside wherever they are, and get no Shelter (−3 wellbeing).

So of an 8 h night, about 3–4 h is sleep and 4–5 h is eating, drinking, attractions and wandering [inferred].

### 1.5 If working hours are 24 (or 0)

[inferred from the code paths above]

* **24 h:** `WorkerRootBehavior` always wins over `NeederRootBehavior`. Employed beavers attend only needs that are
  **critical**: Hunger ≤ 0, Thirst ≤ 0, Sleep ≤ 0, Injury, contamination. They eat one item when Hunger hits 0
  (−10 wellbeing and −50% working speed while it is ≤ 0), return to work, repeat. They sleep only when Sleep is at
  its minimum (−0.2) or near dawn, at 66% rate, possibly outdoors. Shelter, fun, decorations and dishes lapse.
  Wellbeing collapses and with it all tier bonuses. Net output is usually lower than with 16 h.
* **0 h:** no beaver works. Bots still do.

### 1.6 Cycles, seasons and forecasts

[code: `WeatherSystem/WeatherService`, `TemperateWeatherDurationService`, `HazardousWeatherSystem/*`; data:
`BP/NewGameModes`]

* A **cycle** = a temperate season then one hazard season (drought or badtide). The hazard starts on cycle day
  `temperate + 1`. Cycle length = temperate + hazard days.
* The hazard type and its duration are chosen when the cycle is set up (`HazardousWeatherService.SetForCycle`).
* **Forecast:** the weather panel shows "Drought approaching" or "Badtide approaching" with a countdown
  **3 days** before it starts (`HazardousWeatherUISpec.ApproachingNotificationDays` 3). The **duration is not
  shown** until the hazard is running; then the panel counts down the days left (`WeatherSystemUI/WeatherPanel`).
  The Weather Station "does not make forecasts" [loc] but can fire up to 72 h early.
* **Drought:** every map water source's strength goes to 0 (`DroughtWaterStrengthModifier`, see water.md). Water
  then only evaporates and drains.
* **Badtide:** sources emit badwater ("all rivers turn into badwater" [loc `Weather.Badtide`]).

Durations by mode, handicap growth and badtide chances: §12.

---

## 2. A colonist's day

### 2.1 Decision loop

`BehaviorSystem/BehaviorManager` ticks every character. While an **executor** (walk, work chunk, wait, sleep) is
running, nothing is re-decided; when it ends, root behaviours are tried top to bottom and the first that returns
a decision wins [code]. Interruption therefore happens only at executor boundaries (work is done in 0.25 h production
chunks or 0.5 h build chunks; a walk always finishes).

| # | Adult beaver (`BeaverBehavior/BeaverBehaviorInitializer`) | Child | Bot (`BotBehavior/BotBehaviorInitializer`) |
|---|---|---|---|
| 1 | CharacterControl (cutscenes, player) | same | same |
| 2 | Dead | same | same |
| 3 | **Carry**: finish delivering goods in hands | ChildRoot: newborn wait, grow up | Carry |
| 4 | Die | Die | Die |
| 5 | Contaminate (incubation done → sick) | same | — |
| 6 | **CriticalNeeder**: needs in critical state | same | CriticalNeeder |
| 7 | Stranded (outside district) | same | Stranded |
| 8 | **Worker** (in hours) / community service | — | **Needer** |
| 9 | **Needer** (all needs; sleep is chosen here) | Needer | **Worker** |
| 10 | Wander (20% chance to visit a rest place) | Wander | Wander |

[code]

Consequences:

* **An employed beaver in working hours never eats, drinks, sleeps or visits an attraction unless that need is
  critical** (Hunger/Thirst ≤ 0, Sleep ≤ 0, Injury, Contamination). Leisure happens after hours.
* An unemployed adult runs the need loop all day, then wanders.
* **Bots check needs before work**, but only needs below their warning threshold (`BotNeedBehaviorPicker`).
* A beaver holding goods always finishes that delivery first, even past the end of the shift.

### 2.2 How a need action is chosen, and how far they walk

`NeedBehaviorSystem/DistrictNeedBehaviorService.PickBestAction`, `ActionDurationCalculator` [code]:

1. Every need-satisfying building **in the beaver's own district** registers behaviour groups keyed by effect set
   (e.g. "Hunger +0.3, Bread +0.2").
2. Groups are scored by `Appraiser`: per effect, min(points, room to max) × ImportanceMultiplier ×
   (1 + 0.1 × room to max). A group scores **0 if any one effect would be wasted on a non-wastable need**.
3. Best group first; within it, the building with the **shortest walk there + walk to the sleep spot + 0.3 h**.
4. That duration must fit in the hours left before the beaver must head to bed; **critical needs skip this
   check**, so a starving beaver walks any distance in the district.
5. There is no other distance cap. Homes are assigned with no regard to where a beaver works
   (`DwellingSystem/DwellerHomeAssigner` picks from the district's homeless list) [code].

### 2.3 Eating and drinking

[code: `InventoryNeedSystem/InventoryNeedBehavior`; data: goods]

* **One unit per visit.** The beaver reserves 1 unit of the best good, walks **inside** the building, takes it,
  applies its effects, and re-decides (usually eating again on the spot if still hungry).
* Hunger and Thirst are non-wastable: a food (Hunger +0.3) is accepted only when Hunger ≤ 0.7; water (+0.33) when
  Thirst ≤ 0.67. A beaver cannot eat a dish "for variety" while its Hunger is above 0.7.
* **Where from:** any finished building with a takeable consumable good and an enterable slot: warehouses, tanks,
  piles, the District Center, **workshop outputs** (bakery, grill, water pump), gatherer flags and farmhouses,
  district crossings. **Dwellings hold no food.** Only buildings in the beaver's district count.
* Per beaver per day (Normal): **2.67 food items, 2.12 water**, in about 2–4 trips after work [inferred].

### 2.4 Movement

[code: `WalkingSystem/WalkerSpeedManager`, `Walker`, `Carrying/GoodCarrier`, `Overburdenable`; data:
`BP/Characters/*`, path and transit blueprints]

| Item | Value |
|---|---|
| Adult beaver, bot | 2.7 tiles/s = **51.8 tiles per game hour** |
| Child | 1.35 tiles/s |
| Carrying **anything** | slowed speed 1.35 tiles/s = **25.9 tiles/h**. `IsMovementSlowed => IsCarrying`: one berry or two logs, same penalty |
| Movement bonus | × MovementSpeed multiplier (1 + Σ deltas, clamped 0.25–2.0); wellbeing gives +0.05…+0.8 |
| Swimming (any water in the cell) | multiplier − 0.3 (floor 0.25); no depth limit found [inferred] |
| Path vs bare terrain | **no difference**: both cost 1 per tile (terrain also allows diagonals at √2) |
| Stairs vertical hop | edge cost 0.4 (≈ 2.5× on that step) |
| Zipline (Folktails) | cable cost 0.4 × length → 2.5× ("+150%"); max span 30, 2 links per tower |
| Tubeway (Iron Teeth) | cost 0.25 → 4× ("+300%"); no swim penalty, no contamination or soaking inside |
| Overburdened | −0.5 MovementSpeed, only when **one unit weighs more than lifting capacity**; never happens in vanilla (heaviest good 11, lowest capacity 14) |
| Night | no speed penalty at night (no time check in movement code) |

Penalties from needs: Thirst critical −0.25, exhausted −0.1, contaminated −0.7, bot out of fuel/energy −0.75
(MovementSpeed) [data].

### 2.5 Lifting capacity

`Carrying/GoodCarrier`, `CarryAmountCalculator` [code]; capacities and weights [data]:

* Lifting = ⌊base × CarryingCapacity multiplier⌋. Base: adult **14**, bot **20**, child cannot carry.
* Units per trip = min(max(⌊lifting ÷ weight⌋, 1), stock available, free space at destination).
* Hauling Post and District Crossing workers get **CarryingCapacity +1.0** (`WorkplaceBonusesSpec`) → 28 / 40.

| Good (weight) | Beaver 14 | Hauler 28 | Bot 20 | Bot hauler 40 |
|---|---|---|---|---|
| Foods, most crops, berries (1) | 14 | 28 | 20 | 40 |
| Water, flour, badwater, resin (2) | 7 | 14 | 10 | 20 |
| Plank, gear, metal part (3) | 4 | 9 | 6 | 13 |
| Treated plank (4) | 3 | 7 | 5 | 10 |
| Metal block (5) | 2 | 5 | 4 | 8 |
| Log (6) | 2 | 4 | 3 | 6 |
| Dirt (7) | 2 | 4 | 2 | 5 |
| Scrap metal (11) | 1 | 2 | 1 | 3 |

Pick-up and drop-off are instant; a trip is pure walking [code, per agent read of `CarryRootBehavior`].

### 2.6 A worker's day, typical (default 16 h)

[inferred from §1–2 and §4–5]

| Hours | Employed adult |
|---|---|
| 0–16 | At work. The walk from wherever it woke to the workplace is on work time. Leaves only for a critical need |
| 16 | Finishes any delivery in hands, then runs needs |
| 16–~20.5 | 2–4 trips to eat and drink (one unit per bite, from the nearest qualifying building), attractions for fun/social needs, decorations in passing, wandering |
| ~20.5–24 | Walks home, sleeps ~3 h |

Walking share of the work block depends on the job: haulers and builders walk nearly all the time; a workshop
worker with haulers produces ~90%+ of the time; a workshop worker without haulers 40–60% (§5.6).

---

## 3. Needs and wellbeing

### 3.1 How a need works

[code: `NeedSystem/Need`, `NeedManager`, `NeedBehaviorSystem/NeedPenaltyManager`, `Wellbeing/WellbeingTracker`]

* Each tick, points += DailyDelta × tickHours/24, clamped to [min, max]. **If any effect touched that need since the
  last tick, its decay is skipped that tick** (effects replace decay, per need). Sleeping stops Sleep decay only;
  Hunger keeps falling while asleep.
* **Favourable** = points > 0 (for "never-positive" needs with max ≤ 0, such as Injury: points == 0).
* **Wellbeing** = Σ over enabled needs of FavorableWellbeing if favourable, else UnfavorableWellbeing. Integer,
  **all or nothing**: Carrots at 0.001 still gives its full +1.
* **Critical** = the need has a CriticalNeedSpec and is not favourable.
* **Penalties** (`PunitiveNeedSpec`) are binary: added when the need turns unfavourable, removed when it recovers.
* **Lethal** needs (Hunger, Thirst only) kill when they reach their minimum.
* **Work refusal** (`WorkSystem/WorkRefuser`): any critical need with `NeedPreventingWorkSpec` unemploys the
  character: Injury, BadwaterContamination, bot Energy/Biofuel. Hunger and thirst do **not**.
* Game-mode consumption scales Hunger, Thirst and the whole Nutrition group only (§12).

### 3.2 Basic needs (beaver; adults and children alike)

[data: `BP/Needs/Need.Beaver.*`]

| Need | Start | Min | Max | Daily | Fav / Unfav | Effect when unfavourable | Time to effect |
|---|---|---|---|---|---|---|---|
| Hunger | 1.0 | −3 | 1.0 | −0.8 | +1 / **−10** | WorkingSpeed −0.5, GrowthSpeed −0.4; critical; **dies at −3** | full → 0 in 1.25 d; 0 → death 3.75 d; **5 d total** |
| Thirst | 1.0 | −3 | 1.0 | −0.7 | +1 / **−10** | MovementSpeed −0.25; critical; **dies at −3** | 1.43 d; 4.29 d; **5.7 d total** |
| Sleep | 0.8 | −0.2 | 0.8 | −0.6 | +1 / −1 | MovementSpeed −0.1; critical (action) | 0.8 → 0 in 1.33 d |
| Shelter | 0 | −0.2 | 0.8 | −0.3 | +1 / **−3** | none; refilled +0.3/h while sleeping at home | 0.8 lasts 2.67 d |
| WetFur | 0 | 0 | 1 | −0.3 | +1 / 0 | +0.5/h while soaked (swimming, showers) | — |
| Injury | 0 | −1 | 0 | +0.1 | 0 / −2 | refuses work | heals in 10 d (medical bed 2.8 d) |
| BeeSting | 0 | −1 | 0 | +0.75 | 0 / −1 | none | heals in 1.33 d |
| ChippedTeeth | 0 | −1 | 0 | 0 | 0 / −1 | CuttingSuccessChance −0.75 (cuts fail 75%) | never heals; Teeth Grindstone ≈ 2 h |
| BadwaterContamination | 0 | −1 | 0 | 0 | 0 / **−10** | MovementSpeed −0.7, refuses work, disables most other needs (§3.7) | never heals by itself |

### 3.3 Nutrition, fun, social, aesthetics, awe

[data] All start 0, min 0, max 1, unfavourable 0 (absent = no penalty, only a missing bonus).

**Nutrition** (decay −0.05/day × FoodConsumption; +0.2 per matching dish; non-wastable unless noted):

| Faction | Need: wellbeing |
|---|---|
| Folktails | Carrots +1, SunflowerSeeds +1 (+0.5 per seed), GrilledPotatoes +2, GrilledChestnuts +2, GrilledSpadderdock +2, Bread +2, CattailCracker +2, MaplePastry +3 |
| Iron Teeth | Kohlrabi +1, MangroveFruit +1, AlgaeRation +2, CornRation +2, EggplantRation +2, FermentedCassava +2, FermentedMushroom +2, FermentedSoybean +2, Coffee +3 (importance 1.25, decays 0.05/d, +0.4 per coffee) |

One dish of a kind every 4 days keeps its bonus (Easy: every 10 days) [inferred].

**Social and fun** (attraction needs; decay −0.1 to −0.15/day; non-wastable):

| Need | Group | Fav | Faction |
|---|---|---|---|
| Campfire | Social | +1 | both |
| RooftopTerrace | Social | +1 | both |
| ContemplationSpot | Social | +1 | FT |
| DomedGarden | Social | +2 | FT |
| Agora | Social | +3 | FT |
| DanceHall | Social | +5 | FT |
| DancePit | Social | +2 | IT |
| Books (+0.4 per book) | Fun | +3 | FT |
| Carousel, MudPit | Fun | +3 | FT |
| Lido, Sauna | Fun | +1 | FT |
| Detailer | Fun | +1 | both |
| ExercisePlaza, MudBath, WindTunnel | Fun | +3 | IT |
| Motivatorium | Fun | +5 | IT |
| Massager, Scratcher, SwimmingPool | Fun | +1 | IT |

**Aesthetics** (decorations; decay −0.3 to −0.4/day; wastable): Lantern, Roof, Shrub +1 (both); Scarecrow,
Weathervane +1, BulletinPole +2 (FT); Bell, Brazier, BeaverBust +1, DecorativeClock +2 (IT); BeaverStatue +2 (both).

**Awe** (monuments; decay −0.3/day; wastable): Farmer/Laborer Monument +2, Brazier of Bonding/Flame of Unity +4,
Fountain of Joy/Tribute to Ingenuity +6, Hall of Abundance/Arch of Progress +8, wonder +10 (decays −0.01/day).

**Ceilings** (sum of favourable points): Folktails +84 (Awe 30, Nutrition 15, Social 13, Fun 12, Aesthetics 9,
Basic 5); Iron Teeth +84 (Awe 30, Fun 18, Nutrition 17, Aesthetics 10, Basic 5, Social 4). Floor about −38.
Average wellbeing = mean over beavers only, bots excluded (`WellbeingTrackerRegistrar` on `Beaver`). Iron Teeth unlock
at average 15 as Folktails [data].

Need groups (BasicNeeds 10, Nutrition 20, SocialLife 30, Fun 40, Aesthetics 50, Awe 60, Boosts 90) are UI
groupings; the only mechanical use is the Nutrition × FoodConsumption scaling [code].

### 3.4 Wellbeing tiers

[code: `Wellbeing/WellbeingTier*`, `BonusSystem/BonusManager`; data: `BP/WellbeingTiers`, `BP/BonusTypes`]

* Every bonus starts at 1.0; sources add deltas; result clamped. Tier between listed thresholds = last threshold
  reached. **Negative wellbeing gives no tier bonus at all.** Tables are global per character kind (adult, child,
  bot), not per faction.

| Bonus | Clamp | Adult table (wellbeing → delta) |
|---|---|---|
| WorkingSpeed | 0.05–1000 | 5→+0.2, 10→+0.4, 15→+0.6, 20→+0.8, 25→+1.0, 30→+1.2 … +0.2 per 5 up to 60→+2.4; 70→+2.6, 80→+2.8, 90→+2.9, 100→+3.0; +0.1 per 10 beyond |
| MovementSpeed | 0.25–2.0 | 2→+0.05, 12→+0.15, 22→+0.3, 32→+0.4, 42→+0.5, 52→+0.6, 62→+0.65, 72→+0.7, 82→+0.75, 92→+0.8 |
| LifeExpectancy | 0.1–1000 | 7→+0.2, 17→+0.4, 27→+0.6, 37→+0.8, 47→+1.0, 57→+1.1 … 97→+1.5 |
| GrowthSpeed (child) | 0.1–2.0 | 5→+0.05 … +0.05 per ~4 … 50→+0.6, 100→+0.9 |
| Bot WorkingSpeed / MovementSpeed | — | 0 → +0.65/+0.3; 1 → +1.1/+0.6; 2 → +1.7/+0.8 |

Children get GrowthSpeed, MovementSpeed, LifeExpectancy (no working speed). Bots get WorkingSpeed and MovementSpeed.

**Wellbeing is the biggest production lever in the game**: an adult at wellbeing 20 works 1.8× as fast, at 50
3.0×, at 80 3.8× [inferred from the table]. The adult working-speed table reaching ×4 was not cross-checked against
a hidden reduction elsewhere; none was found.

### 3.5 Food and drink goods

[data: `BP/Goods`, `GoodSpec.ConsumptionEffects`]

| Good | Effects per unit |
|---|---|
| Every food (Berries, Carrot, Bread, rations …) | **Hunger +0.3**, plus +0.2 to its own dish need (SunflowerSeeds +0.5; Berries none) |
| Water | Thirst +0.33 (weight 2) |
| Coffee (IT) | Coffee +0.4, no Hunger |
| Book (FT) | Books +0.4 |
| Antidote (FT) | Contamination +0.125, Antidote +0.5 |
| Biofuel / Catalyst / PunchCard / Grease | bot needs +0.3 each |

Raw goods with no consumption effect (must be processed): Wheat, Potato, Corn, Eggplant, Soybean, Cassava, Canola,
CattailRoot, Spadderdock, Chestnut, MapleSyrup, Dandelion, CoffeeBean.

| Per beaver per day | Normal / Hard | Easy (×0.4) |
|---|---|---|
| Food items | 0.8 ÷ 0.3 = **2.67** | 1.07 |
| Water | 0.7 ÷ 0.33 = **2.12** (= 0.42 m³ of map water at a pump) | 0.85 |

### 3.6 Injuries, stings, teeth

[code: `NeedApplication/*`, `EffectProbabilityService`; data: `BP/Configurations/ProbabilityGroups`, building
blueprints]

| Roll group | Low | Medium | High | When rolled |
|---|---|---|---|---|
| Workshop | 0.003125 | 0.01 | 0.02 | every hour per worker inside a working workshop |
| Area | 0.025 | 0.1 | 0.3 | every hour per character in range |
| Yield remover | 0.05 | 0.1 | 0.3 | per completed harvest |
| Demolisher | 0.025 | 0.05 | 0.1 | every hour while demolishing |

Injurable effects × game-mode InjuryChance (Easy 0.3, Normal/Hard 1.0). Bots have no Injury need and are immune.

| Source | Effect, probability |
|---|---|
| Dirt Excavator, Explosives Factory, Bot Assembler, Bot Part Factory | Injury −1.0, High |
| Mine, Efficient Mine, Badwater Rig, Centrifuge | Injury −0.8, High |
| Smelter, Refinery, Paper Mill, Printing Press, Wood Workshop, Grease Factory | Injury −0.6, Medium |
| Gear Workshop, Metalsmith | Injury −0.4, Medium |
| Lumber Mill, Industrial Lumber Mill | Injury −0.1, Low |
| Thorns (demolishing) | Injury −1.0, High |
| Succulent harvest | Injury −1.0, 0.1 per harvest |
| Beehive area, radius 3 | BeeSting −1.0, 0.1/h |
| Lumberjack Flag | ChippedTeeth −1.0, 0.1 roll only after 75+ logs since the last chip |

An injured beaver (−2 wellbeing) **refuses work** for 10 days unless it gets a Medical Bed (Injury +0.015/h,
≈ 2.8 days; bed suspends Sleep and Shelter while inside).

### 3.7 Badwater contamination

[code: `BeaverContaminationSystem/*`]

* Exposure: each tick a beaver stands in water with contamination ≥ 0.05 (not in a tube), probability
  contamination × 0.01 to start **incubation**, which lasts **3 days** and continues after leaving the water.
* Then Contamination = −1: −10 wellbeing, MovementSpeed −0.7, refuses work, no natural recovery, **not lethal**.
* While contaminated, every need without a CriticalNeedSpec except Shelter is **reset and disabled** (nutrition,
  fun, aesthetics, awe). Wellbeing ends up ≤ about −6, so no tier bonuses.
* Cures: Folktails Antidote (8 needed, gated by the Antidote need so ~2/day, ≈ 3–3.5 days) [inferred];
  Iron Teeth Decontamination Pod (+0.068/h, ≈ 14.7 h, uses Extract and 50 power).
* Soil contamination does nothing to beavers (only to plants) [code].

### 3.8 Life and ageing

[code: `LifeSystem/LifeProgressor`, `Beavers/BeaverLongevity`, `MortalSystem/Temporal`, `Beavers/Child`; data:
`BP/Configurations/LifeService`]

* AverageLifespan **50 days**, DaysOfChildhood **6**. Childhood counts toward the 50 days.
* Each beaver rolls ExpectedLongevity U(0.9, 1.1). Progress per day = 1/50 ÷ LifeExpectancy multiplier.
  Old-age death is checked at each dawn.
* Lifespan at constant wellbeing: < 7 → 50 d; 7–16 → 60; 17–26 → 70; 27–36 → 80; 37–46 → 90; 47–56 → 100;
  … 97+ → 125 d [inferred].
* Childhood: progress += hours/(6 × 24) × GrowthSpeed. 6 days at wellbeing < 5, 3.16 days at 100. A hungry
  child grows 40% slower.
* Deaths: old age, Hunger −3, Thirst −3, dynamite/explosions, (drowning/crushing not checked). Corpses vanish after
  23–25 h. Not lethal: contamination, injury, sleep, teeth.

---

## 4. Work and production

### 4.1 Assigning workers

[code: `WorkSystem/WorkplaceAssigner`, `DistrictWorkplaceAssigner`, `PriorityOrderedWorkplaces`,
`UnemployedWorkers`]

* One assigner per **district** per **worker type** (Beaver, Bot), run every tick.
* Workplaces sorted by **priority** (VeryLow … VeryHigh), then **oldest building first**. **Distance is never
  considered**, for the workplace or the worker (`HashSet.First()` of the unemployed).
* The top understaffed workplace takes unemployed workers up to its desired count. With nobody unemployed, a
  strictly higher-priority understaffed workplace **steals** from the lowest-priority staffed one; equal priority
  never steals.
* Lowering desired workers unassigns one idle worker at once, the rest at their next decision.
* Workers live and work anywhere in their district; long commutes are paid out of working hours.

| Building state | Workers |
|---|---|
| Paused, flooded, out of science, contaminated, no water for a water-needer | Building is **blocked** → all workers **unassigned** and reassigned elsewhere; building marked for emptying (`AutoEmptiable`) |
| Unpowered or partly powered | **Stay assigned.** Zero power: cannot produce, so they empty output, fetch input, help with district labor, idle. Partial power: production slows proportionally |
| No inputs anywhere in the district | Stay; "lack of resources" status after 3 h; idle in 0.15 h waits |
| Output full | Production stops; the worker carries output to storage itself |

### 4.2 What a workshop worker does

`Workshops/WorkshopsTemplateModuleProvider` order, re-evaluated after every action [code]:

1. **Produce** if a recipe, one cycle of ingredients, fuel, output space, power and efficiency > 0 are all present.
   Walks inside, works in 0.25 h chunks.
2. **Empty output**: one load of product to the closest stockpile that accepts it.
3. **Fill input**: one load of the input (or fuel) with the lowest stock, from the closest public source in the
   district by path (another workshop's output counts, e.g. the bakery pulls flour straight from the mill).
4. Empty inventories (if marked), 5. remove unwanted stock, 6. district labor (empty any building marked for
   emptying), 7. wait inside 0.15 h.

**Produce always wins**, so output piles up until the buffer is full or inputs run out; then the worker carries
**all** output out, fetches **one** load of input, produces again [inferred from order]. Haulers break this cycle
by keeping inputs topped and outputs drained so the worker stays in step 1.

### 4.3 Recipe maths

[code: `Workshops/Manufactory`, `ProduceExecutor`, `RecipeSpec`]

* Progress per tick = tickHours × worker WorkingSpeedMultiplier ÷ CycleDurationInHours × ProductionEfficiency.
* **Workers add linearly** on one shared cycle: two workers at 1.0 finish a 1 h cycle in 0.5 h.
* ProductionEfficiency = min(power efficiency, each `IManufactoryLimiter`). Water pumps: 1 − contamination, 0 if
  the intake is dry.
* Ingredients are taken at the first progress tick of a cycle; products appear at progress 1.
* Fuel: one unit is burned when the fuel meter is empty; each cycle uses 1/CyclesFuelLasts of it.
* **Buffers:** each good's cap = Amount × **CyclesCapacity** (ingredients and products); fuel cap = FuelCapacity.
  Only the active recipe's goods are allowed. Input is private (own workers and haulers fill it); **output is
  public** (anyone can take from it, and colonists eat/drink from it).
* Power is drawn only while an assigned worker is running a workplace behaviour (`WorkplacePowerConsumptionSwitch`),
  so workshop demand follows working hours.

### 4.4 Worked examples

1 worker, speed 1.0, full power, 16 h day. Buffer hours = CyclesCapacity × cycle time. [data: `BP/Recipes`,
buildings; arithmetic inferred]

| Building (recipe) | Cycle | In → out | Power | Per 16 h day | Input buffer | Output buffer | Buffer = hours of work | Loads per beaver trip |
|---|---|---|---|---|---|---|---|---|
| Bakery FT (Bread) | 1.0 h | 1 flour → 5 bread; 1 log per 10 cycles | — | 80 bread | 38 flour | 190 bread | **38 h** | flour 7, log 2 |
| Gristmill FT (WheatFlour) | 0.5 h | 1 wheat → 1 flour | 60 | 32 flour | 20 wheat | 20 flour | **10 h** | wheat 14, flour 7 |
| Lumber Mill FT (Plank) | 1.25 h | 1 log → 1 plank | 50 | 12.8 | 13 logs | 13 planks | 16 h | log **2**, plank 4 |
| Industrial Lumber Mill IT | 1.25 h, 2 workers | same | 75 | 25.6 | 13 | 13 | 8 h | same |
| Gear Workshop | 3 h | plank → gear | 120 | 5.3 | 10 | 10 | 30 h | 4 |
| Smelter (MetalBlock) | 2 h | 2 scrap → 1 block; 1 log per 5 cycles | 200 | 8 | 26 scrap | 13 | 26 h | scrap **1** |
| Paper Mill FT | 1.56 h | log → 2 paper | 80 | 20.5 | 10 logs | 20 | 15.6 h | log 2 |
| Grill FT (GrilledPotato) | 0.52 h | potato → 4 | — | 123 | 30 | 120 | 15.6 h | 14 |
| Water Pump FT | 0.33 h | → 1 water | — | 48.5 | — | **15** | **5 h** | water 7 |
| Large Water Pump FT | 1 h, 3 workers | → 5 water | — | 240 | — | 60 | 4 h | 7 |
| Inventor | 1 h | → 1 science | — | 16 SP | — | — | — | — |
| Observatory FT | 4 h, 4 workers | → 12 SP | 200 | 192 SP | — | — | — | — |
| Numbercruncher IT | 1 h, **no workers** | → 10 SP | 500 always | 240 SP (24 h) | — | — | — | — |

Bakery total inventory is 413 because capacity is summed over all its recipes, but only the active recipe's goods
are accepted [code].

Harvest buildings [data, code: `Gathering`, `Forestry`, `Fields` configurators]:

| Building | Workers | Inventory | Loop |
|---|---|---|---|
| Gatherer Flag | 1 | 20 | pick up spilled stacks → gather (nearest bush by path, one bush per trip) → carry own output to storage when needed → labor → idle |
| Lumberjack Flag | 1 | 20 | pick up stacks → cut marked tree (2 logs per trip; rest stays as a stack on the stump) → empty output → … |
| Forester | 1 | none | plant marked spots → labor → idle |
| Farmhouse IT / Efficient Farmhouse FT / Aquatic FT | 2 / 3 / 2 | 50 | pick up stacks → **plant first (default)**, else harvest; with "prioritize harvesting": harvest, else empty output, else plant |

### 4.5 When things run out

* **Inputs gone**: workers fetch from anywhere in the district; if nothing exists, they idle (status after 3 h).
* **Output full, no storage set for that good**: production stops; workers can only wait for someone to consume
  or pull the output. A producer needs a stockpile **set to its good** to unload into [code: `DistrictInventoryPicker`].
* **No power**: production stops, workers stay (and keep "occupying" jobs).
* **Paused**: workers released; goods marked to be emptied.

### 4.6 What runs with nobody working

[code] Bots (24 h). `ProductionIncreaserSpec` workshops (Numbercruncher). `GoodConsumingBuilding`s consume
continuously while supplied and unblocked (Steam Engine log + water; attractions with goods pause when empty of
visitors per `GoodConsumingAttraction`). Water wheels and wind turbines. Plant growth. Decorations and monuments.
Iron Teeth breeding pods (timer). Water-moving buildings with their own logic (valves).

---

## 5. Hauling and logistics

### 5.1 Who moves goods

| Carrier | What they move | When |
|---|---|---|
| Workshop workers | Their own inputs and fuel (from the closest source) and their own outputs (to the closest accepting stockpile) | Working hours |
| Flag, farmhouse, lumberjack workers | Harvest into their own building (one plant per trip); carry their own output to storage when it blocks them | Working hours |
| **Builders** (District Center 2–4, Builder's Hut 4) | **All construction materials**; recovered goods after demolition | Working hours |
| **Haulers** (Hauling Post 5–10, carry ×2) | Everything with a haul candidate in the district, by weight (§5.2) | Working hours |
| District Crossing workers (4–10, carry ×2) | Goods between two districts | Working hours |
| Idle workers of any workplace | Empty buildings marked for emptying, remove unwanted stock | Working hours, when their own job has nothing to do |
| Unemployed, off-duty beavers | Nothing (except IT breeding-pod nutrients) | — |
| Bots in any of the above jobs | Same jobs | 24 h |

[code; haul provider list: `EmptiableHaulBehaviorProvider`, `UnwantedStockHaulBehaviorProvider`,
`BringNutrientHaulBehaviorProvider`, `SimpleOutputInventoryHaulBehaviorProvider`, `ObtainGoodHaulBehaviorProvider`,
`SupplyGoodHaulBehaviorProvider`, `FillInputHaulBehaviorProvider`, `ManufactoryHaulBehaviorProvider`. **There is no
provider for construction sites**: haulers never supply construction.]

### 5.2 The Hauling Post

[code: `Hauling/*`; data: `BP/Buildings/DistrictManagement/HaulingPost`]

* Cost Log 20 + Plank 10, no science, 5 workers default, 10 max; bots for 250 science.
* **District-wide, no range.** One finished post switches hauling on for every building in its district.
* A hauler gathers every haul candidate in the district, asks each for weighted jobs, sorts by **weight only
  (distance ignored)**, and takes the first it can start. Nothing to do → wait inside 0.15 h.

| Job | Weight |
|---|---|
| Workshop input | 1 − fill fraction of its emptiest input (recipe set, not paused) |
| Workshop output | average output fill |
| Good-consuming building input (steam engine, mud bath …) | 1 − fill |
| Flag / farmhouse / builder hub output | output fill |
| Building marked for emptying | 0.51 |
| Unwanted stock | 0.50 |
| Stockpile in Obtain mode | 1 − fill |
| Stockpile in Supply mode | fill |
| "Prioritize haulers" toggle | +0.5, only when the base weight ≥ 0.5 |

* Haulers carry 28 (×2) and run the same carry behaviours as workshop workers.
* Some things work **only** with haulers ("Requires haulers" [loc]): good-consuming buildings (Steam Engine, Mud
  Bath, Agora's extract, Decontamination Pod) and stockpile Obtain/Supply modes.

### 5.3 Stockpiles

[code: `Stockpiles/*`, `StockpilePrioritySystem/*`; data]

* One good per stockpile, of its type: Box (warehouses), Liquid (tanks), Pileable (piles).
* Capacities: Small/Medium/Large Warehouse 30/200/1200; Small/Large pile 20/180, Underground 1000;
  Small/Medium/Large Tank 30/300/1200.
* Modes: **Accept** (default; passive destination), **Empty** (gives goods away), **Obtain** (haulers pull the good
  in from anywhere), **Supply** (haulers push it out to consumers).
* Outputs go only to public-input stockpiles that accept the good, have room, and are not blocked or emptying.
  Sources for fetching are every public output (stockpiles, workshop outputs, flags, crossings), closest by path.

### 5.4 District crossings

[code: `DistributionSystem/*`; data]

* The only way goods cross districts. Log 30 + Plank 15, 600 science, 4–10 workers, carry ×2.
* Each crossing balances fill rates: export if my fill > the other side's and > the export threshold;
  amount ⌊min(c₁c₂(f₁−f₂)/(c₁+c₂), (f₁−threshold)c₁)⌋, capped at 30 per good in the crossing. Import modes
  Disabled / Auto / Forced (default Forced for foods, water, logs, planks, biofuel…).
* Workers fetch into the crossing; the transfer to its twin is **instant**; far-side workers unload.
* Colonists can eat and drink straight from a crossing.

### 5.5 How colonists get food and water

See §2.3. In short: colonists walk to the nearest qualifying building in their district, one unit per bite, after
work or when critical. There is no delivery to homes. A water pump's own output (15 units) is drinkable at once.

### 5.6 Trips and loads, quantified

[inferred from 51.8 / 25.9 tiles/h]

* **Fetch trip** of D path tiles: D empty + D loaded = **0.058 × D hours**. D = 10 → 0.58 h; D = 20 → 1.16 h;
  D = 40 → 2.3 h. A **delivery** trip (loaded out, empty back) costs the same.
* **Hauler throughput** (16 h, D = 20 average each way): ~13.8 round trips/day → 386 food units, 193 water, 124
  planks, 55 logs per hauler per day if every trip is full.
* **Lumber mill without haulers**, storage 20 tiles away: per 2 logs (one fetch, 1.16 h) the mill produces 2.5 h and
  sends half an output trip (0.58 h). Uptime ≈ 2.5 / (2.5 + 1.74) ≈ **59%**, ~7.5 planks/day instead of 12.8.
* **Smelter without haulers**: 1 scrap per trip, 2 per 2 h cycle: ≈ 2.3 h walking per 2 h producing, **< 45%**.
* **Bakery without haulers**: one flour trip (7 flour, 1.16 h) feeds 7 h and makes 35 bread, which takes 2.5
  delivery trips (1.45 h) to clear: uptime ≈ 7 / (7 + 2.6) ≈ **73%**.
* **With haulers**, the same workshops stay ≥ 90% busy as long as haulers keep up; each hauler carries one load
  at a time, so hauler count is the limit.
* A builder delivering a Bakery (8 + 4 + 3 = 15 trips at D = 20) walks ~17 h for 2 h of building (§6).

**Colony without haulers:** heavy-input workshops run at half speed; good-consuming buildings (steam engine, mud
bath, agora) never get supplied; Obtain/Supply stockpiles do nothing; paused buildings are emptied only by idle
workers. **With haulers:** inputs and outputs are kept balanced district-wide by fill fraction, workshop workers
stay producing, and loads double.

### 5.7 Night and logistics

Workshop input buffers hold 5–38 h of work (table §4.4), output buffers similar. A water pump fills its 15-unit
output in 5 h, a gristmill its 20 flour in 10 h. With beavers, all moving of goods happens in working hours; the
only vanilla night movers are bots.

---

## 6. Construction, science, demolition

[code: `ConstructionSites/*`, `BuilderHubSystem/*`, `BuilderPrioritySystem/*`]

* **Build time** = ⌈total material units ÷ 20⌉ hours (1 h if free) unless `ConstructionSiteBuildTimeSpec` sets it.
  Bakery 40 units → 2 h; Hauling Post 30 → 2 h; Mine 800 → 40 h; wonders 15000 h.
* Progress per tick = tickHours × builder working speed; worked in 0.5 h chunks.
* **Building trails delivery**: it advances only while delivered materials are ≥ 10% ahead of build progress.
* **Builders per site** (`ConstructionSiteBuildersLimiter`): `MaxAllowedBuilders` defaults to **1** (wonders 40);
  the allowed number scales with the material lead (0 below 10%, max at 30% or a full inventory). In vanilla one
  builder builds a site at a time; several may deliver [delivery limit inferred].
* **Who:** District Center (2 default / 4 max builders, bots free) and Builder's Hut (4; Log 20 + Plank 10; 100
  science). Job order per priority VeryHigh → VeryLow: build or deliver, demolish, collect recovered goods.
  Within a priority, sites go in **placement order**, not distance.
* **Materials come only from builders** (§5.1). A builder fetches the first still-needed good from the closest
  public source, at normal lifting (logs 2, planks 4 per trip).
* **Reach:** construction and demolition only within 10 terrain tiles of the district's paths (`NavigationDistance.
  DistrictTerrain` 10).

**Science** [code: `ScienceSystem/*`; data]: one global pool. Unlocking a building costs its `ScienceCost` once.
Bot crews cost extra per building type (`WorkerTypeUnlockCosts`, 250–10,000). Sources: Inventor 1 SP/h/worker
(16/day), Observatory 192/day, Numbercruncher 240/day, relics 200/800/3000 when demolished. The Control Tower
spends 3 SP/h.

**Deleting and recovery** [code: `DeconstructionSystem`, `RecoverableGoodSystem`, `RecoveredGoodSystem`]:
deletion is instant. Goods drop as stacks around the footprint and **rot after 15 days**. Finished buildings
return materials × DemolishableRecoveryRate (Easy 0.9, Normal/Hard 0.75, rounded up); unfinished sites 100%;
stored goods 100%. Builders carry stacks back. Map objects (ruins, blockages, thorns) take 2–10 h of builder work.

---

## 7. Farming and forestry

### 7.1 Who plants and harvests

[code: `Planting/*`, `Fields/*`, `Forestry/*`, `Gathering/*`, `Navigation/NavigationDistance`]

| Building | Plants (group) | Harvests (group) | Range |
|---|---|---|---|
| Farmhouse IT (2) / Efficient Farmhouse FT (3) | Farmhouse | Farmhouse | **20 tiles of walking from its access** (all of these) |
| Aquatic Farmhouse FT (2) | AquaticFarmhouse | AquaticFarmhouse | 20 |
| Forester (1) | Forester (trees, bushes) | — | 20 |
| Lumberjack Flag (1) | — | Cuttable, **only trees in the global cutting area** | 20 |
| Gatherer Flag (1) | — | Gatherable (bushes, chestnut, mangrove), marked or wild | 20 |
| Tapper's Shack (1) | — | Tappable (pine resin, maple syrup), tree unharmed | 20 |

* Range is a walking distance on the terrain nav mesh (`ResourceBuildings` = 20, drawn as 22), hardcoded, not data.
* Planters only plant **marked spots** in range whose plant they accept; the Forester too. Valid spot: moist soil
  (dry for arid plants), uncontaminated, right water depth, unobstructed.
* Tile choice: first the 8 tiles around the planter, else all spots; closest to the **building centre**.
  Planting time = PlantTimeInHours ÷ working speed.
* Harvest: per good, the nearest yielder by path from the building; carry = min(lifting ÷ weight, yield, free
  room at the building). **One plant per trip.** A partial take spills the rest as a stack on the tile (oak: 8 logs
  = 4 trips) and the plant dies; the tile cannot be replanted until the stack is gone.
* A full harvester inventory means **no harvesting** (farmers keep planting). Ripe crops and fruit never rot.

### 7.2 Growth and dying

[code: `Growing/Growable`, `NaturalResourcesMoisture/*`, `NaturalResourcesContamination/*`,
`NaturalResourcesLifecycle/*`]

* Growth is a plain day timer. **Nothing changes its speed** except the Folktails Beehive (crops only).
* Each threat runs its own dying timer; the plant is "dying" while any runs:

| Cause | Timer |
|---|---|
| Dry soil (moisture 0) | DaysToDieDry × U(0.9, 1.1) |
| Wet soil (arid plants only) | DaysToDieWet × U(0.9, 1.1) |
| Water depth outside band (too dry for aquatic, or flooded) | Floodable DaysToDie × U(0.9, 1.1) |
| Contaminated soil (any level > 0) | **0.2–0.3 days, hardcoded, same for every plant** |

* While dying: growth, fruit regrowth and spreading pause; growth progress is **kept**. When the cause clears, that
  timer **resets fully**.
* Death is **permanent** (`ReverseDeath` is map-editor only). A crop that dies loses its harvest. A dead tree
  keeps its logs (Succulent excepted). A dead bush loses its fruit.
* Moisture vanishes fast: a fully moist tile dries to 0 about **0.7 game hours** after water stops reaching it, so
  in a drought the plant's DaysToDieDry is the real clock [inferred from `SoilMoistureSimulator` constants].
* Badtide kills through soil contamination; contaminated water also gives **no irrigation** (moisture reach falls
  to 0 at contamination ≥ 0.53; water on a tile counts only if ≤ 0.01).

### 7.3 Every vanilla plant

[data: `BP/NaturalResources/*`; derived columns inferred: harvest/day = yield ÷ growth days (fruit: yield ÷
regrowth days after maturity); food = 0.3 Hunger per food item; 1 beaver eats 0.8 Hunger/day]

**Crops** (deleted on harvest, replanted; never spread):

| Crop | Fac. | Group | Plant h | Grow d | Yield | Harvest h | Dry d | Water band | Flood d | Goods/tile/day | Food chain | Beavers fed per tile |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Carrot | FT | Farmhouse | 0.2 | 4 | 3 | 1.2 | 2 | 0/0 | 2 | 0.75 | raw | 0.28 |
| Potato | FT | Farmhouse | 0.2 | 6 | 1 | 1.2 | 1 | 0/0 | 1 | 0.167 | Grill 1 → 4 | 0.25 |
| Wheat | FT | Farmhouse | 0.2 | 10 | 3 | 1.2 | 0.5 | 0/0 | 0.5 | 0.30 | Mill 1 → 1 flour; Bakery 1 → 5 bread | **0.56** |
| Sunflower | FT | Farmhouse | 0.2 | 5 | 2 | 1.8 | 3.5 | 0/0 | 0.66 | 0.40 | raw | 0.15 |
| Cattail | FT | Aquatic | 0.2 | 8 | 3 | 1.2 | 1 | **1/1** | 1 | 0.375 | flour 1→1; cracker 1→4 | 0.56 |
| Spadderdock | FT | Aquatic | 0.4 | 12 | 3 | 1.2 | 0.3 | **1/1** | 1 | 0.25 | Grill 1 → 3 | 0.28 |
| Kohlrabi | IT | Farmhouse | 0.2 | 3 | 2 | 1.2 | 2 | 0/0 | 1 | 0.667 | raw | 0.25 |
| Cassava | IT | Farmhouse | 0.2 | 5 | 1 | 1.2 | 3 | 0/0 | 2 | 0.20 | Fermenter 4 → 10 | 0.19 |
| Corn | IT | Farmhouse | 0.2 | 10 | 2 | 1.2 | 2 | 0/0 | 2 | 0.20 | 1 → 5 rations | 0.375 |
| Eggplant | IT | Farmhouse | 0.2 | 12 | 3 | 1.2 | 1 | 0/0 | 1 | 0.25 | 1 + 1 canola oil → 6 | 0.56 (0.32 incl. canola land) |
| Soybean | IT | Farmhouse | 0.2 | 8 | 2 | 1.2 | 0.25 | 0/0 | 0.25 | 0.25 | 6 + 1 oil → 20 | 0.31 (0.28) |
| Canola | IT | Farmhouse | 0.2 | 9 | 3 | 1.2 | 0.5 | 0/0 | 0.5 | 0.333 | oil press 1 → 1 (ingredient only) | — |

**Bushes** (Forester plants; Gatherer picks; bush survives):

| Bush | Fac. | Plant h | Grow d | Fruit / regrow d | Pick h | Spread | Dry d | Flood d | Goods/day | Fed per bush |
|---|---|---|---|---|---|---|---|---|---|---|
| Blueberry | both | 0.37 | 12 | 3 berries / 12 | 0.8 | 0.02 | 9 | 7 | 0.25 | 0.094 |
| Dandelion | FT | 0.25 | 3 | 1 / 3 | 0.5 | 0.01 | 8 | 4 | 0.33 | (antidote input) |
| Coffee bush | IT | 0.2 | 9 | 1 bean / 3 | 0.8 | 0.02 | 8 | 4 | 0.33 | (coffee) |

**Trees** (Forester plants; Lumberjack cuts marked trees, leaves a stump; fruit by Gatherer or Tapper):

| Tree | Fac. | Plant h | Grow d | Logs | Cut h | Fruit (n / regrow d) | Spread | Dry d | Band | Flood d | Logs/tile/day |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Birch | both | 0.5 | 7 | 1 | 1.0 | — | 0.03 | 11 | 0/0 | 14 | 0.143 |
| Pine | both | 0.75 | 12 | 2 | 1.5 | resin 2 / 7 (tap) | 0.03 | 13 | 0/0 | 12 | 0.167 |
| Oak | both | 1.0 | 30 | 8 | 2.0 | — | 0.01 | 15 | 0/0 | 10 | 0.267 |
| Succulent | both | 0.5 | 65 | Water ×2 (harvest injures 10%) | 1.0 | — | — | **arid**: dies after 8 wet days | 0/0 | 4 | — |
| Chestnut | FT | 0.74 | 23 | 4 | 1.2 | 3 / 8 (gather) | 0.03 | 8 | 0/0 | 10 | 0.174 |
| Maple | FT | 1.1 | 28 | 6 | 2.0 | syrup 3 / 12 (tap) | 0.01 | 12 | 0/0 | 10 | 0.214 |
| Mangrove | IT | 0.6 | 10 | 2 | 1.2 | 4 / 10 (gather) | 0.03 | 6 | **1/1** | 16 | 0.20 |

* Fruit first appears after growth **plus** one regrowth period (blueberry: day 24) and never stacks up unpicked.
* Cutting has a success roll only for logs: 100% normally, 25% with chipped teeth (a failed cut wastes the time).
* Water band is in whole blocks (see water.md): 1/1 = "standing water, up to 1 deep".

### 7.4 Spreading

[code: `NaturalResourcesReproduction/NaturalResourceReproducer`, `Planting/PlantableReproductionBlocker`; data]

Per species per tick, P = tickHours/24 × chance × |free 4-neighbour tiles of all grown, healthy, **unmarked**
parents|, at most one spawn per species per tick, on moist, uncontaminated, unmarked, unobstructed ground. A lone
blueberry bush spawns about once per 12.5 days. **Planted (marked) plants never spread**; crops never spread.
Spawns next to a parent marked for demolition are marked too.

### 7.5 Beehive (Folktails)

[code: `Pollination/Hive`, `Pollinatee`; data] Every 2 h, up to 3 growing **crops** within a 7×7 square get their
timer pushed 0.43 days forward, each crop at most once a day. About 1.4× growth for crops in range; trees and bushes
never. Stings beavers in range (10%/h × InjuryChance).

---

## 8. Water, soil and power

Water simulation, evaporation, valves, pumps' water mechanics and moisture reach are in [water.md](water.md).
Additions:

* **Pump yield.** One Water good = 0.2 m³ of map water (`WaterGoodToWaterAmountConverter`) [code]. A beaver drinks
  2.12 Water/day = **0.42 m³/day** [inferred].
* **Pump throughput**: Water Pump FT 48.5/day per worker (16 h) → ~23 beavers; Large Water Pump 240/day → ~113
  beavers; IT Deep Water Pump same recipe as Water Pump [data, inferred]. Pumps stop when their intake is dry
  and slow with contamination (efficiency 1 − contamination).
* **Moisture**: decays 24 units per game hour once the source is gone; max reach 16 tiles (2 × max cluster
  saturation 8); climbing one block costs 6 [data, code: `SoilMoistureSystem`].
* **Soil contamination**: from water with contamination ≥ 0.5, up to 7 tiles; clears in about 5 h after the source
  goes [data, inferred].
* **Drought survival**: stored water needed = population × 2.12 × drought days (Normal), plus pump losses; e.g.
  40 beavers × 9 days = 763 Water ≈ two-thirds of a Large Tank (1200). Fields survive only if a reservoir keeps
  their soil moist; wheat dies within half a day of drying [inferred].

**Power** [code: `MechanicalSystem/MechanicalGraph`; data]:

* Connected shafts and buildings form one graph; efficiency = min((supply + battery discharge) ÷ demand, 1).
  Partial power slows every consumer proportionally.
* Workshop demand is on only while a worker is on the job (so mostly in working hours); the Numbercruncher always
  draws.
* Generators: Power Wheel FT 50 (1 worker), Large Power Wheel IT 300 (4 workers) — output × workers' MovementSpeed
  multipliers ÷ max workers, so **0 outside working hours**; Water Wheel FT 270, Compact IT 120, Large IT 540
  (× flow, cells under 0.15 ignored); Wind Turbine 150 (wind ≥ 0.3), Large 300 (≥ 0.2); Geothermal 400; Steam
  Engine IT 400 (log 0.1/h + water 0.3/h, hauler-fed).
* Consumers (hp): Lumber Mill 50, Industrial LM 75, Gristmill 60, Paper Mill 80, Gear Workshop 120, Food Factory
  120, Printing Press 150, Bot Part Factory 150, Smelter / Centrifuge / Observatory / Coffee Brewery / Dirt
  Excavator 200, Wood Workshop / Bot Assembler 250, Carousel / Wind Tunnel / Aquifer Drill 400, Mechanical and
  Deep Pump 500, Numbercruncher 500, Compact Pump 700.
* Gravity Battery: 2000 hp·h per tile of weight travel. Clutch disconnects a branch.

---

## 9. Population

### 9.1 Starting population

[data: `BP/NewGameModes`; code: `GameStartup/StartingBeaversInitializer`, `StartingGoodsProvider`]

All modes: **9 adults + 4 children**. Adults at adulthood progress 0.1…0.7 (life progress 0.21–0.74: the oldest
can die of age around day 8–13); children at 0.1…0.8 (grow up after 5.4 / 4.0 / 2.6 / 1.2 days). Starting goods
go into the District Center ignoring capacity: Berries Easy 300 / Normal 130 / Hard 90; Water 250 / **0** / **0**.
Starting goods are hardcoded as Berries and Water for every faction.

| Mode | Food/day for 13 | Starting food lasts | Starting water lasts |
|---|---|---|---|
| Easy | 13.9 | 21.6 d | 22.6 d |
| Normal | 34.7 | **3.7 d** | **0** — first critical thirst at 1.43 d |
| Hard | 34.7 | **2.6 d** | 0 |

[inferred]

### 9.2 Housing and births

[data: housing blueprints; code: `DwellingSystem/Dwelling`, `Reproduction/ProcreationHouse`, `BreedingPod`]

| Dwelling | Fac. | Capacity | Adult slots | Child slots (⌊cap/3⌋) | Births | Cost |
|---|---|---|---|---|---|---|
| Mini Lodge | FT | 1 | 1 | 0 | no | Log 5 |
| Lodge | FT | 3 | 2 | 1 | yes | Log 12 |
| Double Lodge | FT | 6 | 4 | 2 | yes | Log 20 |
| Triple Lodge | FT | 9 | 6 | 3 | yes | Log 35 |
| Rowhouse | IT | 5 | 4 | 1 | no | Log 20 |
| Large Rowhouse | IT | 8 | 6 | 2 | no | Log 35 |
| Barrack / Large Barrack | IT | 10 / 16 | 7 / 11 | 3 / 5 | no | — |

Every dwelling: Sleep +0.2/h, Shelter +0.3/h. Many have stackable roofs (§11).

**Folktails births** (`ProcreationHouse`), rolled **each time any beaver enters the lodge**: free child slot,
children < ⌊adult dwellers ÷ 2⌋, the entering adult and another adult dweller have no critical need, then a
**0.1875** roll. No wellbeing check, no food cost. The baby belongs to that lodge.

**Iron Teeth births** (`BreedingPod`): a 1-day cycle needing 1 Water + 1 Berries (Advanced: Berries + Extract),
5 cycles per beaver; Breeding Pod makes a child, Advanced Breeding Pod makes a **fresh adult**. No housing or
wellbeing check; nutrients come from haulers, the unemployed and off-duty workers.

### 9.3 Death, replacement, migration

* No automatic replacement or immigration from outside. Population grows only by births.
* **Migration between districts** (`GameDistrictsMigration/*`): each district has a minimum per kind (adults,
  children, bots, contaminated), default 0. A district below its minimum pulls from the connected district with
  the most spare; with all minimums at 0 **nothing moves**. Who goes first: work-refusers, unemployed, homeless,
  youngest. Up to 100 moves per pass.

---

## 10. Bots

[data: bot blueprints and recipes; code: `BotsUpkeep/*`, `BotBehavior/*`, `DeteriorationSystem/*`]

* **Making one:** Bot Part Factory (150 power, 1 worker) makes chassis (18 h; 5 plank, 1 metal block, +1 biofuel
  for FT), head (18 h; plank, 3 gear, metal block), limbs (4.5 h; plank, 3 gear) ×4; Bot Assembler (250 power,
  2 workers) assembles in **72 h**. Raw cost ≈ 10 planks, 15 gears, 2 metal blocks (+1 biofuel). ~126 worker-hours.
  The bot spawns at the assembler, in its district.
* **Body:** speed 2.7 (same as a beaver), lifting **20**, no home, no sleep, no hunger, thirst, injury or
  contamination; immune to every beaver attraction and decoration.
* **Hours:** ignore working hours (24 h); check needs **before** work.
* **Needs:** FT Biofuel (−0.58/day, ≈ 1.9 units/day; +0.3 each), Catalyst and PunchCard boosts (≈ 0.67/day each);
  IT Energy (Charging Station 0.6/h, 1.7 h per charge, lasts 1.7 days), Grease boost, Control Tower boost (in
  range only). Out of fuel/energy: refuses work, −0.75 movement, wellbeing −3 → no tier bonus. **Never lethal.**
* **Bot tiers:** wellbeing 0/1/2 → working speed ×1.65 / ×2.1 / ×2.7, movement ×1.3 / ×1.6 / ×1.8.
* **Life:** fixed **70 days** (`DeteriorableSpec`), counted unconditionally; nothing repairs it.
* **Where they can work:** banned from Power Wheel, Large Power Wheel, Inventor (`DisallowOtherWorkerTypes`);
  free at District Center, flags, Efficient Farmhouse, Water Pump, Deep Water Pump, Industrial Lumber Mill;
  250–10,000 science per building type elsewhere. They can build, haul, farm, cut, produce.
* Bot wellbeing is not in the colony average.

---

## 11. Districts, paths, vertical building

[code: `Navigation/NavigationDistance`, `BlockSystem/*`, `MapStateSystem/MapSize`; data]

| Rule | Value |
|---|---|
| District road spill (membership, builder reach) | 10 terrain tiles off the district's paths |
| Resource building range | 20 walking tiles |
| District size | **no cap**; a warning above 70 tiles from the District Center |
| Idle wander | 10 road steps or 5 terrain steps |
| Connectivity | buildings must reach the road graph through their entrance; paths, stairs, bridges, ziplines, tubes count as road; characters may also walk bare terrain |
| District Center | free, pre-built, 2–4 builders, 20 storage (starting goods here) |
| Map | 4–256 tiles a side (default 128); 33 levels (z 0–32); terrain up to 22; buildings up to 10 above terrain |

**Stacking** (`MatterBelow`, `Occupations`): Ground / GroundOrStackable / Stackable / Air / Any. Objects share a voxel
when their occupation flags do not overlap (a path can run under a platform). Stackable tops: every dwelling,
warehouses and industrial piles, Hydroponic Garden, Bot Part Factory, Dam, Levee, valves (partly), Airlock,
Compact Pump, platforms (1–3, metal 3×3/5×5), overhangs, vertical tubeways and shafts, Roof3x2, terrain blocks.
Rooftop Terrace **requires** a stackable surface; Agora, Campfire, Motivatorium, mines, Geothermal, Badwater Rig
and Dome, Dynamite require real ground. Overhangs cantilever up to 5 tiles from one anchor; suspension bridges
span air.

**Tunnels** remove one terrain voxel and auto-place a platform; **Dirt Excavator** removes terrain inside a 5×4
area one voxel per 6 h cycle (4 Dirt); **Terrain Block** (4 Dirt) raises ground by one.

---

## 12. Difficulty and game modes

[data: `BP/NewGameModes/GameMode.{Easy,Normal,Hard}`; code as noted]

| Parameter | Easy | Normal | Hard | Code |
|---|---|---|---|---|
| Starting adults / children | 9 / 4 | 9 / 4 | 9 / 4 | `StartingBeaversInitializer` |
| Food consumption (Hunger + Nutrition) | **0.4** | 1.0 | 1.0 | `NeedModificationService` |
| Water consumption (Thirst) | **0.4** | 1.0 | 1.0 | same |
| Starting Berries / Water | 300 / 250 | 130 / 0 | 90 / 0 | `StartingGoodsProvider` |
| Temperate days (rerolled each cycle) | 16–19 | 13–17 | 5–8 | `TemperateWeatherDurationService` |
| Drought days (base) | 2–4 | 5–9 | 15–30 | `DroughtWeather` |
| Drought handicap start × / over N droughts | 0.25 / 8 | 0.38 / 5 | 0.2 / 12 | `HazardousWeatherHelper` |
| Badtide possible from cycle | 6 | 5 | 4 | `CyclesBeforeRandomizingBadtide` 5/4/3 |
| Badtide chance | 0.4 | 0.4 | 0.4 | `HazardousWeatherRandomizer` |
| Badtide days (base) | 1–3 | 4–8 | 15–30 | `BadtideWeather` |
| Badtide handicap start × / over N | 0.3 / 6 | 0.15 / 5 | 0.4 / 9 | |
| Injury chance | **0.3** | 1.0 | 1.0 | `EffectProbabilityService` |
| Demolition refund | 0.9 | 0.75 | 0.75 | `GoodRecoveryRateService` |

Players can also build a custom mode in the new-game panel (same parameters; droughts and badtides can be turned
off) [loc].

**Duration growth.** For the n-th occurrence of a hazard type: multiplier = lerp(handicap, 1, (n−1)/N); duration =
round(Uniform(mult × min, mult × max)), at least 1. n counts that hazard type only, so the first badtide is always
short. Approximate rounded ranges [inferred]:

| Occurrence | 1 | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 13+ |
|---|---|---|---|---|---|---|---|---|---|
| Easy drought | 1 | 1 | 1–2 | 1–2 | 1–3 | 1–3 | 2–4 | 2–4 | 2–4 |
| Normal drought | 2–3 | 3–5 | 3–6 | 4–7 | 4–8 | 5–9 | 5–9 | 5–9 | 5–9 |
| Hard drought | 3–6 | 4–8 | 5–10 | 6–12 | 7–14 | 8–16 | 10–20 | 12–24 | 15–30 |
| Normal badtide | 1 | 1–3 | 2–4 | 3–5 | 3–7 | 4–8 | 4–8 | 4–8 | 4–8 |
| Hard badtide | 6–12 | 7–14 | 8–16 | 9–18 | 10–20 | 11–22 | 13–26 | 15–30 | 15–30 |

**Badtide odds** after it becomes possible: 0.4, adjusted by streaks — after 3 badtides in a row 0.2, after 4
none; after 5–6 droughts in a row 0.7, after 7 a forced badtide.

Cycle length therefore runs about 15–26 days on Normal, 8–38 on Hard [inferred].

---

## 13. Attractions, decorations, area effects

### 13.1 Attractions

[code: `Attractions/Attraction`, `AttractionNeedBehavior`; data]

* **No vanilla attraction has workers.** Visitors come through the need loop, so **only off-duty, unemployed or
  critical** colonists visit. Effects are filtered to the faction's needs and scaled by power where powered.
* First visit lasts at least 0.5 h, then 0.05 h chunks; `SatisfyToMaxValue` effects keep the visitor until full.
* A visit of ~1.7 h fills a fun/social need (0.6/h), which then lasts 7–10 days.
* Some consume goods while occupied (Agora Extract 0.2/h, Sauna log 0.2/h, Domed Garden/Dance Pit water 0.2/h,
  Mud Pit/Bath dirt 0.5/h, Detailer Extract 0.25/h) — these need haulers.

| Attraction | Need, points/h | Capacity | Wellbeing |
|---|---|---|---|
| Campfire | Campfire 0.6 | 5 | +1 |
| Rooftop Terrace FT / IT | 0.6 | 8 / 10 | +1 |
| Contemplation Spot FT | 0.6 | 1 | +1 |
| Agora FT | 0.6 | 15 | +3 |
| Dance Hall FT | 0.6 | 20 | +5 |
| Domed Garden FT / Dance Pit IT | 0.6 + WetFur 0.4 | 16 / 15 | +2 |
| Carousel FT | 0.6 (400 power) | 12 | +3 |
| Lido FT / Swimming Pool IT | 0.6 + WetFur 0.5 | 7 / 8 | +1 |
| Sauna FT | 0.6 | 6 | +1 |
| Mud Pit FT / Mud Bath IT | 0.6 | 8 | +3 |
| Exercise Plaza IT | 0.6 | 13 | +3 |
| Motivatorium IT | 0.6 (200 power) | 18 | +5 |
| Wind Tunnel IT | 0.6 (400 power) | 12 | +3 |
| Massager / Scratcher IT | 0.6 | 1 | +1 |
| Detailer | 0.6 | 1 | +1 |
| Shower FT / Double Shower IT | WetFur 1.0 | 1 / 2 | +1 |
| Teeth Grindstone | ChippedTeeth 0.5 to max | 1 | clears −1 |
| Medical Bed | Injury 0.015 | 1 | clears −2 |
| Decontamination Pod IT | Contamination 0.068 | 1 | clears −10 |
| Charging Station IT (bots) | Energy 0.6 to max | 1 | — |

### 13.2 Ranged effects (decorations, monuments)

[code: `RangedEffectSystem/*`]

* Area = footprint + radius on every side, a **square, all heights**.
* **Anyone standing in it** (walking, working, idle) or inside a building with any block in it receives the effect
  every tick. No visit, no capacity, no time-of-day check, so it works at night and during work.
* Identical effects from several buildings **do not stack**; the best efficiency counts. Powered ones scale with
  power.

| Building | Need, points/h | Radius | Decay/day | Wellbeing | Hours in range per day to keep it |
|---|---|---|---|---|---|
| Shrub, Lantern | 0.64 | 1 | −0.4 | +1 | 0.63 |
| Roofs | 0.2 | 1 | −0.4 | +1 | 2 |
| Scarecrow, Weathervane FT | 0.32 | 2 / 3 | −0.4 | +1 | 1.25 |
| Beaver Statue | 0.64 | 3 | −0.4 | +2 | 0.63 |
| Bulletin Pole FT / Decorative Clock IT | 0.64 | 3 | −0.3 | +2 | 0.47 |
| Beaver Bust, Brazier IT | 0.64 | 2 | −0.4 | +1 | 0.63 |
| Bell IT | 0.32 | 3 | −0.4 | +1 | 1.25 |
| Farmer / Laborer Monument | 0.1 | 7 | −0.3 | +2 | 3 |
| Brazier of Bonding / Flame of Unity | 0.1 | 10 | −0.3 | +4 | 3 |
| Fountain of Joy / Tribute to Ingenuity | 0.1 | 20 | −0.3 | +6 | 3 |
| Hall of Abundance / Arch of Progress | 0.1 | 30 | −0.3 | +8 | 3 |
| Wonder (while active) | 10 | 40 | −0.01 | +10 | lasts ~100 days |
| Control Tower IT (bots) | 3.0 | 10 | −72 | +1 (bot) | must stay in range |

### 13.3 Wonders

[code: `Wonders/*`, `GameWonderCompletion/*`; data] Folktails Earth Recultivator and Iron Teeth Earth Repopulator:
huge cost (≈ 5500 materials, 15000 build hours, 40 builders), then a fill of 500 + 500 goods, crew of 8–10.
Launch turns on the +10 Awe field (radius 40), then records the map as "mastered" for the faction and shows the end
screen. No other gameplay unlock.

---

## 14. Automation and other 1.0/1.1 systems

[code: `Automation/*`, `AutomationBuildings/*`, `Explosions/*`, `FireworkSystem/*`, `HttpApiSystem/*`; data]

* **Every pausable building is automatable**: a signal pauses it ("Paused by automation"), which, like any pause,
  releases its workers. Also floodgates, valves, gates, clutch, water-source regulator, detonator, speaker,
  indicator, firework launcher, HTTP adapter. No wiring distance limit found.
* **Logic**: Lever, Relay (Not/And/Or/Xor/Passthrough), Memory (SetReset/Toggle/Latch/FlipFlop), Timer
  (Delay/Pulse/Oscillator/Accumulator/Random), **Chronometer** (TimeRange, WorkingHours, NonWorkingHours).
* **Sensors**: Weather Station (current weather, up to 72 h early), Depth, Flow, Contamination, Population Counter
  (beavers, adults, children, bots, beds, homeless, jobs, employed, unemployed, contaminated…), Resource Counter
  (fill or stock of one good), Science Counter, Power Meter.
* A Chronometer + automation can **pause buildings at chosen hours** — the only vanilla per-building time control,
  and it works by releasing workers, not by giving them a schedule [inferred].
* **Valves**: Fill Valve, Throttling Valve, Floodgate, Airlock (beavers pass, water does not). See water.md.
* **Dynamite** (1/2/3 deep) lowers one terrain column, kills characters on the tile, chains to neighbours;
  Detonator fires it on a signal. **Tunnels** and **overhangs**: §11.
* **Fireworks**: purely cosmetic; 1 good per launch; made from badwater (1 → 10 in 3 h).
* **HTTP API**: local server on port 8080 (levers, adapters, webhooks).
* **Night-only gameplay**: none. Lights, campfire flames and ambient sound are cosmetic; no gameplay reads
  illumination.

---

## 15. Rules of thumb

All [inferred], Normal difficulty, speed 1.0 (no wellbeing bonus) unless noted. Wellbeing 20 multiplies every
"work" figure by 1.8; Easy multiplies food and water needs by 0.4.

| Rule | Arithmetic |
|---|---|
| **A beaver eats 2.7 food and drinks 2.1 water a day** | 0.8 ÷ 0.3; 0.7 ÷ 0.33 |
| **2–4 food-and-water trips an evening** | ~5 items/day, one per bite, usually 2–3 per visit |
| **Land per beaver**: ~3.6 carrot tiles, ~1.8 wheat tiles (as bread), ~11 blueberry bushes, ~4 kohlrabi tiles | 1 ÷ 0.28; 1 ÷ 0.56; 1 ÷ 0.094; 1 ÷ 0.25 |
| **One water pump worker serves ~20 beavers** | 48.5 ÷ 2.12 = 23, minus walking |
| **Drought stock** = population × 2.1 × drought days (+ 50% margin on Hard) | 40 beavers, 9 days → 763 water |
| **One bakery feeds ~30 beavers on bread alone; one gristmill ~60** | 80 bread ÷ 2.67; 160 bread-equivalent ÷ 2.67 |
| **One farmer works ~90 wheat tiles** | per tile per 10 days: plant 0.2 + harvest 1.2 + ~0.3 walking ≈ 1.7 h; 16 h/day ÷ 0.17 h/tile/day |
| **Bread chain for 30 beavers**: 54 wheat tiles, 1 farmer, 1 miller (half-time), 1 baker, 1 log per 10 bread cycles | 30 × 2.67 = 80 bread = 16 flour = 16 wheat/day; 16 ÷ 0.3 |
| **Walking**: 52 tiles/h empty, 26 loaded; a fetch or delivery round trip ≈ 0.06 h per tile of distance | 1/51.8 + 1/25.9 |
| **Hauler round trip at 20 tiles ≈ 1.2 h, ~14 trips a shift** | 0.058 × 20; 16 ÷ 1.16 |
| **One hauler moves ~390 food, ~190 water, ~55 logs a day at 20 tiles** | 14 trips × 28 / 14 / 4 |
| **Workshops without haulers lose 40–60% to walking for heavy inputs** | lumber mill 59% uptime, smelter < 45% (§5.6) |
| **Keep producers within ~10 tiles of their storage** | each 10 tiles costs 0.58 h per load |
| **Construction is delivery-bound**: delivery hours ≈ (units ÷ load) × 0.058 × D; build hours = units ÷ 20 | Bakery: 15 trips ≈ 17 h at 20 tiles vs 2 h of building |
| **Off-duty time**: ~3 h sleep, ~1–2 h eating and drinking, the rest leisure or idle, out of 8 h | §1.4 |
| **A decoration covers whoever passes for 40 min a day; a monument needs 3 h a day in range** | 0.4 ÷ 0.64; 0.3 ÷ 0.1 |
| **Fun/social visit of ~1.7 h lasts a week or more** | 1 ÷ 0.6; 1 ÷ 0.1–0.15 per day |
| **A lodge of 2 adults makes about one child in a few entries** | 0.1875 per entry with a free slot |
| **Wellbeing 20 ≈ +80% work, +30% walking, +40% life** | tier table §3.4 |
| **Each dish type needs one bite every 4 days to keep its bonus** | 0.2 ÷ 0.05 |
| **Starting food lasts ~4 days on Normal, water 0 days** | §9.1 |

---

## 16. Things that surprise designers

**Time and schedule**

1. **Working hours always start at dawn (hour 0)** and are one global block, 0–24 whole hours. There is no
   per-worker, per-kind or per-building schedule. Dusk is off-duty only if the player shortens the day; dawn is
   always on-duty. [code]
2. **Employed colonists ignore every non-critical need during working hours.** No mid-shift meals, naps, tea or
   attractions. Leisure happens after work, and only off-duty or unemployed colonists fill attractions. [code]
3. **Beavers sleep ~3 hours, late.** Sleep refills fast (0.2/h) and the picker fills the evening with other needs
   first. The night is mostly awake time. [code, inferred duration]
4. **Sleep does not slow hunger or thirst.** Effects replace decay only for the need they touch. [code]
5. **At 24 working hours** colonists only answer critical needs; wellbeing and output collapse. [inferred]
6. Forecasts give the **type 3 days ahead, never the duration** until it starts. [code]

**Logistics**

7. **Carrying anything halves walking speed**, whatever the load. Load size (lifting ÷ weight) is the real lever,
   not speed. A small carrier is crippled by heavy goods: lifting 10 moves **one** log per trip. [code, data]
8. **Haulers never deliver construction materials.** Builders do, at normal (not doubled) loads, one site at a time
   in placement order, and one builder builds per site. Construction time is mostly walking. [code]
9. **Workshop workers supply themselves.** Haulers are a district-wide efficiency layer that picks jobs by fill
   fraction, not distance. A colony works without haulers, just slower. [code]
10. **Produce beats unloading**: a lone worker lets output pile up to the buffer cap, then unloads all of it before
    fetching one input load. [code]
11. **A producer with no stockpile set to its good stalls when its small buffer fills** (water pump: 15 units, 5 h).
    [code, data]
12. Colonists **eat from workshop outputs and flags** directly, one unit per bite, never from homes. [code]
13. Workers are assigned by **priority, then building age — never distance**. Homes are assigned with no regard to
    the workplace. Commutes are paid from working hours. [code]
14. Pausing a building (by hand or automation) **releases its workers**; unpowering it does not. [code]

**Needs and wellbeing**

15. **Every food is Hunger +0.3**; dishes differ only by their +1…+3 variety need. A need gives its full wellbeing
    as soon as it is above 0. [data, code]
16. A good is refused entirely if **any** of its effects would be wasted on a non-wastable need (you cannot eat
    bread for its Bread bonus when not hungry). [code]
17. **Negative wellbeing gives zero tier bonuses**; wellbeing tables are global, not per faction (faction changes
    need `BlueprintModifiers` or code). [code]
18. Hunger costs −10 wellbeing and −50% work speed the moment it reaches 0, long before death (5 days). [data]
19. Contamination **disables most needs** and does not kill; injury makes a beaver refuse work for 10 days. [code]

**Population and life**

20. Folktails births are a **0.1875 roll per lodge entry**, no wellbeing gate, child slots ⌊capacity/3⌋, children
    ≤ ⌊adults/2⌋. [code]
21. Lifespan is 50 days × a wellbeing multiplier up to 2.5; childhood 6 days (3.2 at top wellbeing). [data]
22. With district minimums at 0, **nobody migrates** between districts. [code]
23. Normal and Hard start with **no water** and under 4 days of food. [data]

**Plants**

24. Growth speed is fixed; dryness, flooding and contamination only start a **dying countdown**, which resets fully
    if conditions return in time. Death is permanent. [code]
25. **Any** soil contamination kills **every** vanilla plant in 0.2–0.3 days; tolerance is not data, only "has the
    spec or not". [code]
26. Soil dries in under an hour once water is gone; drought survival is the plant's DaysToDieDry (wheat 0.5 d,
    blueberry 9 d, oak 15 d). [data, inferred]
27. **Marked (planted) plants never spread**; only wild ones do. Crops never spread. [code]
28. All resource buildings have a **hardcoded 20-tile walking range**. [code]
29. Water depth bands for plants are **whole blocks**. [code, see water.md]

**Bots, effects, misc**

30. Bots live a fixed 70 days, never sleep, ignore hours, check needs before work, and are immune to every beaver
    effect. [code, data]
31. Area effects reach **everyone standing in the square**, at all heights, day and night, during work; they do not
    stack. [code]
32. **Nothing in vanilla gameplay depends on night** except sleep timing and working hours. Lights, fires and
    lanterns are cosmetic; there is no night speed penalty. [code]
33. Power Wheels make power **only while staffed**, so only in working hours. [code]
34. Above 30 characters the fast speeds are throttled; at 200+, 7× is really 3.4×. [code, data]
35. Starting goods (Berries, Water), the name pool, wellbeing tiers and game modes are **global**, not per faction
    (see CLAUDE.md). [code]
