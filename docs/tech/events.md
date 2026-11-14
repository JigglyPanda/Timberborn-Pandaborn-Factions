# The two signature events: Lantern Festival and Great Flowering

Status: 2026-11-14, game 1.1.2.8. Design of record for DESIGN.md Pillar 5, built as two code modules
(`src/code/Pandaborn.Festival`, `src/code/Pandaborn.Flowering`, spec records in `src/code/Pandaborn.Specs/EventSpecs.cs`)
and tested in game on dev copies of the faction built by `proto/events/build.ps1` (README there). Every mechanism below was
read from the decompiled game first; the [Results](#results) section says what was then seen in game. Both modules are in
`Pandaborn.Code.sln` and `modules.txt` and load through the bootstrap's API check; they ship when the content lane switches
`catalogue/rules.toml [modules] Festival` / `Flowering` on (the catalogue already carries the data of section 8 behind
those switches). The design changes of section 7 were accepted (DESIGN.md, 2decaec).

## Contents

1. [Lantern Festival: what the player experiences](#1-lantern-festival-what-the-player-experiences)
2. [Lantern Festival: how it works](#2-lantern-festival-how-it-works)
3. [Great Flowering: what the player experiences](#3-great-flowering-what-the-player-experiences)
4. [Great Flowering: how it works](#4-great-flowering-how-it-works)
5. [Is the first Flowering fair?](#5-is-the-first-flowering-fair)
6. [Edge cases, defined](#6-edge-cases-defined)
7. [Design changes made here, and why](#7-design-changes-made-here-and-why)
8. [Requests to the catalogue lane](#8-requests-to-the-catalogue-lane)
9. [Requests to the model lane (Festival Square)](#9-requests-to-the-model-lane-festival-square)
10. [Requests to the plant lane](#10-requests-to-the-plant-lane)
11. [Results](#results)
12. [Unproven](#unproven)

---

## 1. Lantern Festival: what the player experiences

Every mechanic fits one sentence on the square's panel: *"Once a cycle, the whole village takes a day and a night off.
Afterwards everyone is festive for about 20 days and Tradition rises by one."*

| When | What the player sees |
|---|---|
| Cycle 2 | The Festival Square is unlocked (science) and built. Its panel: "Not ready: this district needs more in store." / "Paper lanterns in store: 12/40" / "Dishes with 20 or more in store: 2 of 3 kinds" / "Steamed rice 45, Pickles 23, Steamed shoots 12" / "Fireworks for a Grand Festival: 0/20" / "Tradition: 0", the one-sentence rule, a red **Call the festival** button (greyed while not ready) and a **Call it by itself when ready** toggle |
| Stocking | Nothing new to learn: lanterns from the Lantern Workshop and dishes from the cooks go to ordinary warehouses as always; the panel counts what the square's district has in store |
| The call (any hour) | Toast and log entry: "The Lantern Festival is called. It begins at dawn." The goods leave the stores at once. The panel: "The festival begins at dawn (in 7 h)." The square's festival lights come on (art hook) |
| Dawn | "The Lantern Festival has begun. Only the pump crews work today." Workers leave their jobs at their next decision (a delivery in hands is finished first). Pump and lift crews keep working |
| The day | Off-duty life all day: colonists eat, drink, nap, take tea, visit attractions, and in between drift to the square and mill about there. Each one gets festive spirit (+4) the first time it reaches the square |
| Ringtails | They sleep through the morning as on any day, then come to the square at the bell instead of going to their night posts |
| Dusk (15.5 h) | Everyone gathers at the square. From 15.75 h, 24 lanterns rise from it over 1.75 h (drawn as the game's red and white trail rockets until the art lane's lantern particles exist) |
| Evening, Grand only (19 h) | Twenty fireworks burst over the square over 2.5 h, with the game's own firework sounds |
| 22 h | The gathering ends; colonists go about their night and sleep |
| Next dawn | "The Lantern Festival is over. Everyone is festive. Tradition: 1". Everyone who did not reach the square gets festive spirit now. Tradition-locked decorations of level 1 unlock in the toolbar. Work resumes |
| Aftermath | Festive spirit (+4 well-being, +5 after a Grand Festival if the catalogue adds the Grand need) fades over about 20 days. The panel: "The next festival can be called in cycle 3." |

Pressure points a player hits, and what happens:

* **Called in a hurry at 23:00.** It begins an hour later at dawn. Nothing is lost.
* **Called at 01:00.** It begins at the next dawn, 23 hours later: the eve is a normal working day. The panel shows the
  countdown. (Starting at once was rejected: a festival that starts mid-shift would cost two half-days and its day/night
  would not line up with the bell.)
* **A drought starts tomorrow.** Manual calls are allowed in any weather (the pumps keep their crews, so drinking water
  keeps coming; one day without food work cannot starve a fed colony, whose Hunger takes 1.25 days to reach zero and 5 to
  kill). The auto-call never fires during a drought or badtide, nor the day before one.
* **Two districts.** The festival is the whole village's: everyone takes the day off and everyone ends festive. Colonists
  go to the square of their own district; a district without a square simply has a day off. The goods come from the
  district of the square that was used to call it.
* **Game speed 3 or 7.** Everything is on the game clock (behaviour decisions, launch times computed from the hour), so
  speed changes nothing but how fast it passes.

## 2. Lantern Festival: how it works

### The Festival Square in data

Data alone behaves like vanilla (ENGINEERING.md data rule 2): with the module off the square is **a village square that
meets the Campfire need**, i.e. a vanilla attraction on a dance-hall basis (20 visitors, visible dance slots). With the
module on, `PandabornFestivalSquareSpec` attaches `FestivalSquare` (registration, the show, the art hooks) and the panel
fragment. The square needs no inventory of its own (see the next point).

### Stocking: the district's ordinary stores, taken at the call

Options examined in the decompiled game:

| Option | Why not |
|---|---|
| A stockpile on the square | One good per stockpile; and any enterable storage of a consumable good is a place colonists **eat from** (`InventoryNeedBehavior`), so dishes put aside would be eaten |
| `GoodConsumingBuildingSpec` with every eligible dish | Its `CanUse` needs every listed good at once (not "any three"), haulers would pull every dish kind into the square, and with the module off it would burn them |
| A workshop recipe | A recipe has fixed ingredients, so "any three dishes" is impossible |
| An inventory added by the module | Its contents would be lost whenever the module is off (per-entity state; ENGINEERING.md code rule 6) |
| **The district's own stores, counted live and taken at the call (chosen)** | Lanterns and dishes live in warehouses as every good does; haulers and producers need nothing new; nothing is lost when the module is off; the panel shows exactly what is there |

`FestivalStock` sums the unreserved stock of each good over `DistrictInventoryRegistry.ActiveInventoriesWithStock`
(warehouses, piles, workshop outputs, the district center: the public inventories of the square's district). "Any three
cooked dishes" is the list `PandabornFestivalSpec.Dishes`; a festival needs `DishKinds` (3) of them with `DishAmount` (20)
each. At the call the lanterns, 20 of each of the **three most plentiful** qualifying dishes, and (Grand) the fireworks are
taken with `Inventory.TakeConsumed`, unreserved stock only. Bamboo-seed cakes are simply one of the dishes.

### The day off

Working hours are one colony-wide value (`WorkingHoursManager.WorkedPartOfDay`), saved by the game; zeroing it for a day
would write saved vanilla state (a save made mid-festival and loaded without the module would keep a colony that never
works) and would not stop Ringtails (`IgnoresWorkingHours`). Pausing workplaces is saved too and releases workers.

So the day off is a **root behaviour**, `FestivalGoer`, decorated on every colonist template with
`PandabornFestivalGoerSpec` and inserted just above `WorkerRootBehavior` (`NeederRootBehavior` for cubs and kits). The
behaviour list (`BeaverBehaviorInitializer`): CharacterControl, Dead, Carry, Die, Contaminate, **CriticalNeeder**,
Stranded, *[Ringtail rest]*, *[FestivalGoer]*, Worker, Needer, Wander. So a colonist always finishes a delivery in hands,
answers critical needs (Hunger or Thirst at 0, Sleep at its minimum, injury) and leaves an unreachable district before
the festival can claim it. On the festival day:

1. a worker at a `KeepWorkingTemplates` workplace releases to the Worker root and works its normal hours;
2. by day, the game's `NeederRootBehavior` decides first (eat, drink, attractions, decorations, sleep near dawn);
3. otherwise, and first of all during the show (`ShowStartHours`..`ShowEndHours`), walk to a spot near the district's
   square (the nearest of five `IDistrictService.GetRandomDestinationInDistrict` picks around the square's centre, so the
   crowd stands on and beside it rather than scattered), then wait there 0.3–0.8 h;
4. with no square in the district: needs, then the game's wander behaviour.

**What keeps running** (so a festival never strands a colony): critical needs (above us), all eating and drinking from
stock (off-duty colonists do nothing else), pump and lift crews (`KeepWorkingTemplates`: Water Pump, Large Water Pump,
Mechanical and Compact Mechanical Pump, Aquifer Drill, Treadwheel Lift, Scoop Wheel, Dew Collector), every bot and
Wooden Ox (no goer spec; they ignore working hours), and every building that runs without workers (water wheels, wind
and kite mills, flumes, decorations, growth). What stops for one day: building, hauling, farming, cutting, cooking and
worker-turned power wheels (so a powered pump on a power wheel stalls; one fed by water or wind does not).

**Ringtails.** Both the Ringtails' day rest and the festival insert above `WorkerRootBehavior`. The rest inserts in
`InitializeEntity`, the festival in `PostInitializeEntity` (which the game runs after every component's
`InitializeEntity`), so the order is always rest, then festival: a Ringtail sleeps and eats through its morning as on any
day; outside its rest window, where it would work, the festival takes it to the square. Their templates only need
`PandabornFestivalGoerSpec`. With the Ringtails module off, saved Ringtails load as Inkpaws (their alias) and celebrate as
Inkpaws; with the festival module off, Ringtails work as usual.

The insertion uses one private field, `BehaviorManager._rootBehaviors` (the Ringtails use the same one). Fallback: if it
is gone, nobody takes the day off; the festival keeps its show, festive spirit and Tradition, and the panel's rule line
says so. Nothing of the behaviour is saved (a reload restarts the current walk).

### The show

The game 1.1 has real fireworks: firework entities (`Fireworks/*` blueprints, Common collection) with trail and burst
particles and sounds, spawned by the Firework Launcher. `FestivalFireworks` spawns the same entities from any point:
`EntityService.Instantiate(FireworkSpec.Blueprint)` then the component's `Launch(position, rotation, distance)`. The
component class `Timberborn.FireworkSystem.Firework` is internal, so `Launch` (public) is called by reflection; fallback:
no fireworks, everything else runs. Lanterns use the trail-only rockets `Firework.CometRed`/`CometWhite` (gentle pitch,
short flight) until the art lane provides lantern particles; bursts use `KamuroOrange`, `PalmGold`, `KamuroRed`, `Willow`,
`PeonyYellowGreen`. Launch times are computed from the clock each tick (`ShowStartHours + 0.25 + i × 1.75 / LanternRises`,
`FireworksStartHours + i × 2.5 / Bursts`), so a reload mid-show launches only what is still due and nothing twice; the
flying fireworks themselves are saved by the game.

Hooks for the art lane on the square's model (section 9): `#FestivalLights` is shown from the call to the end of the
festival and hidden otherwise; `#FireworkMount` is the launch point. Each lantern first asks the square's
`TemplateAttachments.GetOrCreateAttachment("LanternRise")` (a blueprint attachment `{AttachmentId "LanternRise", Prefab,
Parent "#LanternRise", CreateInstantly false}`) and plays its `ParticleSystem`; no attachment (`KeyNotFoundException`,
caught) means a `ParticleSystem` under a `#LanternRise` node, and neither means the comet. Every missing node or particle
system degrades to nothing.

Sounds: `pandabornsounds` clips `Environment.Pandaborn.FestivalDrum` (looped on a child emitter of the square during
the show; the square's own emitter already loops the visitors' sound, and one emitter loops one sound) and
`Environment.Pandaborn.Firecrackers` (2D at the start of the festival day, 3D at the square when the show starts). A clip
the game does not know (`AudioClipService.GetAudioClipNames`) is skipped silently.

### Festive spirit and Tradition

* Festive spirit is the catalogue need `PandabornFestive` (+4, decays 0.05 a day: about 20 days; balance Q7). The module
  raises it to its maximum through the need system (`NeedManager.ApplyEffect(InstantEffect)`), as an attraction would,
  when a colonist first reaches the square and, at the end, for every colonist that has not. It is the game's own need
  state: with the module off it simply fades. A Grand Festival also fills `GrandNeedId` if the catalogue adds that need.
* Tradition is a counter in the store (+1 per festival). It gates decorations through the game's own toolbar lock: an
  `IToolLocker`, as science and plant groups use (`ToolUnlockingService`). A decoration with `PandabornTraditionSpec`
  `{ Level }` is locked until Tradition reaches it; clicking it explains ("String Lanterns is earned with Tradition 1. Each
  Lantern Festival raises Tradition by one."). The game asks lockers with `SingleOrDefault`, so two lockers claiming one
  tool would throw: the Tradition locker only claims tools science does not lock, and **Tradition decorations need
  `ScienceCost` 0**. Unlocks are not saved by the game (the lock is recomputed from Tradition at every load). With the
  module off there is no locker: the decorations are simply buildable.

### Saved state

Store entry `Festival` v1: `phase`, `day`, `grand`, `last` (cycle of the last festival), `tradition`, `auto`, `count`.

## 3. Great Flowering: what the player experiences

| When | What the player sees |
|---|---|
| Before cycle 6 | Nothing, except a line on any bamboo's panel: "Bamboo flowers once in a long while: about every 5 to 7 cycles, never before cycle 6." and a **Flowering: Normal** button (the setting) |
| Start of cycle 5 (a full cycle ahead) | "The Shoot Bamboo is budding. It will flower at the start of cycle 6, bear seed for a few days and die." A line under the top bar: "Shoot Bamboo flowers at the start of cycle 6", whose tooltip says what to do: store about 11 food for each panda or grow other food, set the farmhouses to harvest first, keep storage free for bamboo seed. Every shoot bamboo's panel: "Budding: it will flower at the start of cycle 6, bear seed for 3 days, then die." Buds on the plants once the plant lane paints them |
| Start of cycle 6 | "The Shoot Bamboo is in flower. 56 plants bear 168 bamboo seed: harvest it within 3 days." Every grown shoot bamboo on the map, planted or wild, becomes Flowering Shoot Bamboo, whose harvest is bamboo seed; young plants die. Top-bar line: "Shoot Bamboo in flower: harvest the seed, 3 days left" |
| Days 1–3 | Farmers harvest the flowering plants for seed exactly as they harvest shoots (it is their crop's harvest), carry it to the farmhouse and on to storage. Freed tiles are replanted at once from the planting marks |
| Day 3 | Unharvested flowering plants die over the last day ("The flowered Shoot Bamboo has died. Bamboo seed harvested: 151. Its young plants grow again in 6 days.") |
| Days 1–9 | Young shoot bamboo sits as seedlings: "Resting after the Flowering: it grows again in 6 days." Top-bar line: "Shoot Bamboo grows again in 6 days" |
| Day 9 | "The Shoot Bamboo grows again." Seedlings grow (3 days); the first shoots come in on day 12 |
| Afterwards | Bamboo seed is cooked with rice flour into seed cakes (4 per seed), the best dish in the mod. Next Flowering (timber bamboo) 5–7 cycles later |

Timber bamboo goes the same way, with lumberjacks: flowering groves in the cutting area are cut for seed (dead flowering
trees keep their seed until cut, as dead trees keep their logs); the tooltip says to store about 5 poles for each panda and
to mark the groves for cutting.

"Prepared" means, in the player's words: food (or poles) to last two weeks without that bamboo, farmers free to harvest,
and room for seed. The forecast says exactly that, a full cycle ahead.

## 4. Great Flowering: how it works

* **Schedule** (store entry `Flowering` v1). `PandabornFloweringSpec` on the adult template: `Species` (order), `FirstCycle`
  6, intervals 5–7 (normal) or 9–11 (rare, first at cycle 9). The next cycle is drawn once and saved. `CycleStartedEvent`
  drives it: at the start of cycle N−1 the Flowering of cycle N is announced; at the start of cycle N it happens. Day 1 of
  a cycle is always temperate (the hazard starts on day `TemperateWeatherDuration + 1`), so a Flowering is never in a
  drought or badtide, and the seed days (3) end long before the earliest hazard (temperate is at least 5 days even on
  Hard). The countdown says "at the start of cycle N", never a number of days: the cycle's length includes the hazard's
  duration, which the game deliberately hides until it starts.
* **Buds**: while announced, plants whose spec says `BudsUseDetail` get the material's detail map switched on for their
  grown model (`_EnableDetail`, as vanilla shows ripe fruit). Off until the plant lane paints buds there.
* **The Flowering** (`FloweringService.Flower`): for every plant of the species: grown and alive → deleted and its twin
  (`InFlowerTemplate`) spawned on the same tile (`NaturalResourceFactory.SpawnIgnoringConstraints`, then grown with
  `Growable.IncreaseGrowthProgress(1)`); young → `LivingNaturalResource.Die()`; a harvested crop whose pile still lies there
  is left alone. The twin's harvest is its cut yield, `PandabornBambooSeed` × 3, in the same resource group as the bamboo
  (Farmhouse / Cuttable), so the farmhouse's and lumberjack's inventories accept seed (`YieldRemovingBuilding` allows the
  yields of every template of its group) and their workers harvest and carry it with the vanilla behaviours.
* **Dying**: twins die over the last day of `SeedDays` (each at a time hashed from its tile). Dead crops lose their seed (the
  game's rule) and become overridable, so farmers plant over them; dead twin trees keep their seed until a lumberjack cuts
  them, then leave a stump to replant.
* **Replanting and the rest**: planting marks are a separate map (`PlantingService`) and are never touched, so farms and
  foresters replant on their own. Until `DormantDays` (9) after the Flowering, young plants of the species do not grow:
  the module pauses each one's growth timer every in-game hour and whenever one is planted. The game has no public pause
  for growth, so this uses the private field `Growable._timeTrigger` (an `ITimeTrigger`, a public interface with
  `Pause`/`Resume`). Fallback: no rest (young bamboo regrows at once: the event is shorter, never harsher). The holds are
  not saved; the game saves growth progress and the module holds the plants again after a load.
* **Setting** without any other mod: per save, normal / rare / off, in a game dialog opened from the top-bar line or from
  any bamboo's panel. Switching off cancels an announced Flowering (with a notice). A Mod Settings integration would be a
  separate optional module that loads late (the Reskin's `.bin` pattern) and calls `FloweringService.SetSetting`; not
  built, because the per-save dialog already covers it.
* **An unprepared colony is told**, not surprised: the announcement a cycle ahead, the top-bar line through the whole
  event, the count of plants and seed when it flowers, and the seed harvested when the seed days end.

## 5. Is the first Flowering fair?

The design's numbers (balance Q7) blocked replanting "until the next temperate season" (about 15 days in the model). Day 1
of a cycle is the Flowering, so that rest would have ended near the cycle's own drought, which on Normal starts on day
14–18 of the cycle. The colony model (`tools/sim` `popsim.run`, 60 colonists, shoots 35% of food, crops pause in a
drought, a 7-day drought starting on cycle day 13 or 17, 10 random seeds each; `proto/events/tools/flowering_fair.py`):

| Days without a shoot harvest | Drought starts on cycle day | Pantry kept by the player | Lowest population (of 60) | Starved |
|---|---|---|---|---|
| none (no Flowering) | 13 | 2 days | 60 | 0 |
| 12 (rest 9 + growth 3) | 13 | 2 days | 60 | 0 |
| 12 | 17 | 2 days | 60 | 0 |
| 12 | 13 | 6 days | 60 | 0 |
| 15 (rest 12 + growth 3) | 13 | 2 days | 41 | 19 |
| 15 | 17 | 2 days | 21.5 | 40.5 |
| 15 | 13 | 6 days (the forecast followed) | 60 | 0 |
| 15 | 17 | 11 days | 60 | 0 |

**Choice: `DormantDays` 9** (a 12-day gap for shoot bamboo, 14 days for timber bamboo, which grows in 5). A colony that
follows the forecast is never at risk at either length; at 15 days, one that keeps a thin two-day pantry and ignores the
forecast loses a third to two-thirds of its colonists when the cycle's drought follows, at 12 days it loses none. The
event still costs real food: 0.35 × 2.67 × 12 ≈ **11 food per panda** without the stock (what the tooltip asks for), and
about 5 poles per panda for timber (0.35 a day × 14). The seed windfall (3 a plant; a 40-colonist colony grows about 56
shoot tiles, so about 168 seed, 670 seed cakes) refills the pantry once a Kitchen and rice flour exist.

**Warning for the coordinator:** the balance sheet's "until the next temperate season" and "reserve 14 food a colonist"
should become "9 days of rest" and "about 11 food a colonist". On Hard (temperate 5–8 days) the rest always runs into the
cycle's drought; there shoot bamboo is not the staple (balance claim 8: cabbage is), and the drought decides more than
the Flowering. A future Hard tuning could shorten `DormantDays` per game mode; not done.

## 6. Edge cases, defined

| Case | Festival | Flowering |
|---|---|---|
| Save and reload mid-event | Phase, day and grand are in the store; colonists re-enter the festival at their next decision; the show resumes from the clock without repeats | Phase, species and day are in the store; twins are ordinary saved plants; young plants are held again at load |
| Called at hour 23 | Begins at dawn, an hour later | — |
| Two districts | Everyone off; each district's square hosts its own; goods from the calling square's district; festive for all | Flowers on the whole map, every district |
| Drought or badtide | Manual call allowed (pump crews keep working); auto-call never, nor the day before | Impossible by construction: day 1 of a cycle is temperate; the seed days end before any hazard |
| Game speed 3 / 7 | Clock-driven; nothing depends on frames | Hourly ticks on the game clock |
| Module forced off in a save mid-event | Everyone works as usual; goods already spent; store entry kept. Back on: a festival whose day passed ends at load with its rewards; one called for today starts | No new Flowering; twins stay plants that bear seed and never die by themselves; young bamboo grows; store entry kept. Back on: picks up (an overdue announced Flowering moves to the next cycle start) |
| Game update removes a private member | No day off (show, festive, Tradition kept); or no fireworks | No rest after a Flowering (milder) |
| The square is demolished while called | The festival still runs; colonists of that district have a day off without a square | — |
| A colonist is starving on festival day | Critical needs come before the festival | — |
| Setting changed to off while announced | — | Cancelled with a notice |

## 7. Design changes made here, and why

| Change | Why |
|---|---|
| Festival goods stay in the district's ordinary stores and are taken at the call; the square holds nothing (balance sheet: "holds 40 lanterns, 60 dishes, 20 fireworks") | Any storage colonists can enter is a place they eat from, a consuming building needs every listed dish, a recipe cannot say "any three", and a module-made inventory loses its goods when the module is off. Ordinary stores need no new rule |
| The festival begins at the next dawn after the call, whatever the hour | One clean day and night aligned with the bell; a call at 01:00 costs nothing extra; the eve gives a beat of anticipation |
| Manual calls allowed in any weather; auto-call only in fair weather | Pump crews keep working, so no colony can be stranded by one day; a player in a long drought may want the boost; the automatic call should never surprise anyone in bad weather |
| Pump and lift crews keep working on the festival day | "Everyone takes the day off" must never mean "nobody pumps water in a drought" |
| Everyone ends festive, not only those who reached the square | One sentence for the player; nobody is punished for living in a district without a square |
| The Grand Festival's extra reward is a second need (+1) only if the catalogue adds it (`GrandNeedId`) | Balance Q7 asked for +1 well-being; the module supports it; without the need, Grand is the fireworks show alone |
| Tradition decorations need ScienceCost 0 | The game allows one tool locker per tool; science and Tradition cannot both lock one decoration |
| The Flowering's rest is 9 days, not "until the next temperate season" | Section 5: at 15 days a thin-pantry colony that ignores the forecast is wiped out by the cycle's drought; at 12 nobody starves; the forecast's ask drops from 14 to 11 food a panda |
| The seed is the flowering plant's harvest (a twin plant whose yield is seed), not goods dropped on the ground | The game's recovered-goods spawner is internal; a dropped pile is only fetched by builders, slowly, and rots in 15 days; a harvest is taken by the farmers and lumberjacks who already work those plants, and farmhouses accept the good only if it is a yield of their group |
| The countdown names the cycle, not a number of days | The cycle's length includes the coming hazard's duration, which the game hides until the hazard starts |

## 8. Requests to the catalogue lane

**Status (phase 2):** the catalogue has applied all of these behind `rules.toml [modules] Festival` / `Flowering`
(square on `DanceHall.Folktails`, the three module specs on the characters, `PandabornFestiveGrand`, Tradition levels, the
twins on the plant lane's flowering models, `BudsUseDetail = true` on shoot bamboo and `false` on timber bamboo). Still
open: the square's `LanternRise` attachment and its own lantern particle (section 9). The dev
copies generate exactly this data, with the switches flipped in a scratch copy of the catalogue.

All ids below are new and must be locked (`generate -Lock`). Custom specs go only on Inkpaws-only templates.

1. **Festival Square** (`buildings.toml`, replacing the storage stand-in):
   ```toml
   PandabornFestivalSquare = { basis = "DanceHall.Folktails", needs_map = { DanceHall = "Campfire" }, standin = "new model", add = { PandabornFestivalSquareSpec = {} }, waits_for = "Festival", needs_code = "calls and hosts the Lantern Festival (Festival module); until then a village square that meets the Campfire need" }
   ```
   Keep `building_stats.toml`'s cost and science; drop "holds 40 lanterns, 60 dishes, 20 fireworks" from the balance note.
   Text: description "Calls the Lantern Festival and hosts it. Pandas gather here in the evening." (the panel explains the rest).
2. **The festival's rules** on `InkpawAdult.Inkpaws` (`faction.toml`, adult character `add`):
   ```toml
   PandabornFestivalSpec = { LanternGoodId = "PandabornPaperLantern", Lanterns = 40, Dishes = ["PandabornSteamedShoots", "PandabornPickles", "PandabornSteamedRice", "PandabornSweetRiceBalls", "PandabornHotPot", "PandabornBambooSeedCakes"], DishKinds = 3, DishAmount = 20, FireworksGoodId = "Fireworks", Fireworks = 20, FestiveNeedId = "PandabornFestive", GrandNeedId = "PandabornFestiveGrand", KeepWorkingTemplates = ["WaterPump.Inkpaws", "LargeWaterPump.Inkpaws", "MechanicalPump.Inkpaws", "CompactMechanicalPump.Inkpaws", "AquiferDrill.Inkpaws", "PandabornTreadwheelLift.Inkpaws", "PandabornScoopWheel.Inkpaws", "PandabornDewCollector.Inkpaws"], ShowStartHours = 15.5, ShowEndHours = 22.0, FireworksStartHours = 19.0, LanternRises = 24, LanternFireworkIds = ["Firework.CometRed", "Firework.CometWhite"], BurstFireworkIds = ["Firework.KamuroOrange", "Firework.PalmGold", "Firework.KamuroRed", "Firework.Willow", "Firework.PeonyYellowGreen"], Bursts = 20 }
   PandabornFestivalGoerSpec = {}
   PandabornFloweringSpec = { Species = ["PandabornShootBamboo.Inkpaws", "PandabornTimberBamboo.Inkpaws"], FirstCycle = 6, NormalMinCycles = 5, NormalMaxCycles = 7, RareMinCycles = 9, RareMaxCycles = 11, RareDelayCycles = 3, SeedDays = 3.0, DormantDays = 9.0, DefaultSetting = "normal" }
   ```
   and `PandabornFestivalGoerSpec = {}` on `InkpawChild.Inkpaws`, `RingtailAdult.Inkpaws` and `RingtailChild.Inkpaws`.
   Keep `Fireworks` in the Inkpaws' goods (it is in the Common collection) and the Explosives Factory's Fireworks recipe.
3. **Grand need** (`needs.toml`), optional (without it Grand is the show alone):
   ```toml
   [needs.PandabornFestiveGrand]
   basis = "Bread"
   name_from = "own"            # text: "Grand festival"
   group = "Boosts"
   daily_delta = -0.05
   favorable_wellbeing = 1
   importance = 1.0
   wastable = true
   src = "M q7 (Grand adds 1 well-being while festive)"
   ```
4. **Tradition** on decorations (`buildings.toml`; each needs `science = 0`), proposed:
   `PandabornStringLanterns` and `PandabornGoldfishBowl` level 1, `PandabornHangingLantern` level 2,
   `PandabornGardenMoonGate` level 3: `add = { PandabornTraditionSpec = { Level = 1 } }`, `science = 0`. Their
   descriptions should end "Earned with Tradition N (Lantern Festivals)."
5. **The two bamboos** (`plants.toml`): `add = { PandabornFloweringPlantSpec = { InFlowerTemplate = "PandabornShootBambooInFlower.Inkpaws", BudsUseDetail = false } }`
   on `PandabornShootBamboo`, and `InFlowerTemplate = "PandabornTimberBambooInFlower.Inkpaws"` on `PandabornTimberBamboo`
   (`BudsUseDetail = true` once the plant lane paints buds).
6. **The two twins** (`plants.toml`, new items in `NaturalResources.Inkpaws`): copies of each bamboo with the same model
   (until the plant lane's flowering models exist), `cut_yield = { PandabornBambooSeed = 3 }` in the same resource group,
   **no** `PlantableSpec`/`PlantablePreviewModelSpec` (no planting tool), no `ReproducibleSpec`, no `GatherableSpec`
   (timber), and `add = { PandabornInFlowerSpec = { Species = "PandabornShootBamboo.Inkpaws" } }` (resp. timber).
   `proto/events/tools/derive.py` is the reference implementation. Names "Flowering Shoot Bamboo" / "Flowering Timber
   Bamboo"; the loc keys used by the prototype are in `enUS_PandabornEvents.csv` and can move to `text/plants.json`.
7. **Balance note** (`docs/tech/balance.md` Q7 is the balance lane's): "blocked until the next temperate season" →
   "9 days of rest after the Flowering"; reserve 14 → 11 food a colonist (section 5).

## 9. Requests to the model lane (Festival Square)

A 5 × 5 open village square on the dance-hall slots (visitors dance in the open, visible in the slots), timber frame and
plaster, a tall central lantern pole or small stage, red only on the lanterns. Named child nodes the module drives:

| Node | Kind | Driven by the module |
|---|---|---|
| `#FestivalLights` | static lantern strings and lit stall lanterns (emissive or `WindowsAtlas` lit regions) | shown from the call to the end of the festival, hidden otherwise (with the module off they always show) |
| `#LanternRise` | a `ParticleSystem` attachment: one paper lantern rising slowly and drifting, warm glow, 8–12 s life | played once per lantern at dusk, in place of the comet rocket |
| `#FireworkMount` | an empty transform at the launch point (pole top) | launch origin of lanterns and fireworks |

Keep the dance-hall slot nodes so the 20 visible dance slots work. Lantern particles need the art lane's own bundle (the
module never ships materials).

## 10. Requests to the plant lane

1. **Flowering models** for the twins (`Mature/#Alive|#Dying|#Dead` like the bamboos; no seedling needed: twins are always
   grown): shoot bamboo with drooping seed panicles over yellowing culms; timber bamboo with straw-coloured culms and
   seed heads in the sprays. Model paths `NaturalResources/Pandaborn/<Kind>/<Id>InFlower/<Id>InFlower<Stage>`.
2. **Buds** on the ordinary bamboos, painted in the detail map on the grown model's uv2 (small pale bud clusters at the
   spray tips), so `BudsUseDetail = true` shows them a cycle ahead. Timber bamboo already uses its detail map for the
   bamboo fungus, and the game's `GatherableModel` switches the detail map with the mushroom yield: put the buds on the
   shoot bamboo only, or give timber bamboo its buds in the flowering model only (no visible buds before it flowers).

## Results

All runs on the hidden desktop, map Plains (paths connect there) unless noted, with only the dev copy, the events probe
and the harness enabled (`-OnlyMods JigglyPanda.PandabornFactionsDev`). Both modules load through the bootstrap's API
check like any shipped module (`features`: `Festival: On; Flowering: On`). Folders `E:\PandabornDev\build\test\<run>`; the
probe writes `events.json` (and `reload\events_reload.json`), shots `ev_*.png`.

### Phase 2 (real module path)

| Run | What | Result |
|---|---|---|
| `events-main-3` | copy `pbevents` (catalogue data, test timings); auto-call, Grand Festival, festival day, mid-show save and reload, drought, Flowering with seed cakes | **PASS, 0 own errors**, both launches. **Auto-call** fired in fair weather at h5.2 ("The Grand Lantern Festival is called"). **Festival day:** nobody worked (`working` empty, Ringtails included), 16/16 attended, festive average 0.97; 11 at the square at h10, 16 at h19. **Show:** 24 lanterns from h15.75, bursts from h19 (the reflected `Firework.Launch`), 3 sounds. **Mid-show reload:** the reload launched only the 7 bursts still due and 0 lanterns (no replay). **End at dawn:** Tradition 1, Tradition-locked decorations 4 → 2 (level 1 unlocked), festive 1.0 and grand 1.0 on everyone. **Drought:** auto-call (on, stocked) did not fire in the drought; a manual call at hour 23.0 held the festival next day in the drought, nobody working; Tradition 2. **Flowering:** farmers harvested the seed (store 3 → 24), the Kitchen cooked seed cakes (4, 8, 12 ...), young bamboo held at 0.000, growth resumed on time. Gaps fixed later: replanting failed (below), the lumberjack had no worker. Shots `ev_d1_h15_gathering.png`, `ev_d1_h16b_lanterns.png`, `ev_d1_h20_fireworks.png`, `reload\ev_r_*.png` |
| `events-fallback-4` | copy `pbevents-fb`: `simulate-missing-member` for `Festival.DayOff`, `Festival.Fireworks`, `Flowering.GrowthHold`; then a reload with `force-off: Festival, Flowering` written by the probe | **PASS.** `Degraded` reported with all three reasons and the notice "runs in a reduced mode"; colonists worked on the festival day, no fireworks, young bamboo grew; replanting worked (11 young). Reload forced off: `ForcedOff` notices, colonists worked normally, store entries kept, 0 errors |
| `events-backon-2` | copy `pbevents-on`: a mid-festival and mid-flowering state saved with both modules forced off, reloaded with them on | **PASS.** The overdue festival ended at load (Tradition 1, festive and grand 1.0, locks 4 → 2); the Flowering resumed ("in flower, 2 days left"). With the module off, farmers still harvested the twins (plain data plants) |
| `events-crews-3` | copy `pbevents2` (keep-working Efficient Farmhouse as a stand-in pump crew, the plant lane's flowering bundle) | **PASS.** The farmhouse crew (3) worked through the festival day; 48 seed harvested ("Bamboo seed harvested: 48"); all 16 tiles replanted, held, and grew after the rest; twins render with the flowering models (`ev_c_d0_h10_twins.png`). Buds not seen at camera distance (`ev_c_d0_buds_plant.png`). Dusk: `ev_c_d1_h16_dusk_a.png` (comet sparks, read as rockets), `ev_c_d1_h16_dusk_b.png` |
| `events-rtoff-3` | copy `pbevents-rt`: a Ringtail family moves in, festival called, then a reload with `force-off: Ringtails` mid-call | **PASS**, both launches. First launch: 3 Ringtails on the night post. Reload: 0 Ringtails, 16 Inkpaws (the saved Ringtails loaded as Inkpaws), the festival ran: 15/16 attended, festive 0.9; the lumberjack (a keep-working template in this variant) stayed at its flag all day; 24 lanterns. Shots `reload\ev_rt_off_gathering.png`, `reload\ev_rt_off_lumberjack.png`, `reload\ev_rt_off_square.png` |
| `events-final-1` | copy `pbevents3` | **could not test**: crashed at load on another lane's new character attachment (`Characters/Pandaborn/Attachments/ConicalHat`, bundle `pandabornattachments`, which the copy lacked). `build.ps1` now copies every `pandaborn*` bundle the copy lacks from the last full build |
| `events-final-2` | copy `pbevents3`: the square's `LanternRise` attachment (`Fireworks/Content/Sparks_Trail` on `#Finished`, until the model lane's node exists), crowd nearer, the panel layout fix, `BudsUseDetail` | **PASS, 0 own errors.** The farmhouse crew of 3 kept working; the 10 others all attended and spent the day at or walking to the square. **LanternRise:** the attachment played for each of the 24 lanterns (no comets in the sky); it shows as small pink sparks halfway up the pole (`ev_f_d1_h16_dusk_c.png`, `ev_f_d1_h17_dusk_d.png`). **Panel:** the bamboo line and its setting button no longer overlap (`ev_f_d0_inflower_panel.png`, `ev_f_d0_buds_plant.png`). **Buds:** not visible (`ev_f_d0_buds_plant.png`); see `events-buds-1` |
| `events-buds-1` | copy `pbevents3`, short: a grown shoot-bamboo field, announcement, close-ups before and after; the probe lists each renderer under `Mature` with its material, `_EnableDetail` and detail textures | **PASS, 0 own errors. The switch works, the buds do not read.** Before the announcement the grown model's material (`PandabornShootBamboo - Uncolored21 (Instance)`, VegetationURP, re-created by the game's optimizer) has `_DetailMap PandabornPlants_Detail` and `_EnableDetail 0`; from the announcement on, `_EnableDetail 1` on every renderer under `Mature` (as the game's `GatherableModel` does). On screen the field looks the same before and after (`ev_b_before.png`, `ev_b_after.png`, `ev_b_after_field.png`): the bud clusters are too small and too close to the leaf green to see from the game camera. Art request to the plant lane: larger, paler (cream to white) clusters at the spray tips, or a pale tint over the upper sprays in the detail map. No code change is needed (why the plant lab's `buds` rule changed nothing is not known; the switch itself works) |

### Phase 1

| Run | What | Result |
|---|---|---|
| `events-main-1` | Diorama, the phase-1 dev mod | **PASS.** The Flowering proven end to end (twins, seed, deaths, rest held across a reload); the festival refused correctly ("The square must be connected to a district by a path"): no path routes on Diorama |
| `events-folktails-1` | Folktails + the events dev mod | **PASS.** Both modules inactive; Folktails untouched |

### Bugs found in game and fixed

* Replanting marks were lost under the twins: the game's `PlantingCoordinatesUnsetter` clears a planting mark when a
  block of another template is placed on it. The Flowering now puts the mark back after placing a twin (proven in
  `events-fallback-4` and `events-crews-3`).
* "Seed harvested: 0": the count is now seed borne minus seed lost, both saved.
* Crash when visitors entered the square during the show (`SoundEmitter is currently playing another sound in a loop`):
  the drum loops on its own child emitter.
* Startup crash with Festival forced off (`TypeLoadException` from a compiler-generated lambda class in the probe):
  the probe's module code has no lambdas. A rule worth keeping for any DLL that names an optional module's types.
* The bamboo panel's text and its setting button overlapped: the fragment uses the vanilla wonder fragment's layout.

### The look of the festival (honest)

Functional, not yet beautiful. At night the square itself looks good: its lantern strings glow red-orange over the
pale paving, with a few pandas on it and the rest of the crowd around its edges (`ev_f_d1_h16_dusk_b.png`). The sky is the weak part. The vanilla comets read as
rockets, gone in seconds; the `Sparks_Trail` stand-in on the attachment is a small pink sparkle at the pole, invisible
from the normal camera. **Rising lanterns need their own art**: a small bundle prefab with one `ParticleSystem`
(a warm, softly glowing paper-lantern quad, emission rate 0, played once per lantern; rises 1–1.5 m/s with a slow
sideways drift and a gentle sway; 10–16 s life; fades in over 0.5 s and out over the last 3 s; additive or emissive
warm orange, about 0.3 m), referenced by the square blueprint's `LanternRise` attachment on `#LanternRise`. Burst
fireworks (Grand only) are the game's own and look right.

## Unproven

* **Visible buds**: the switch is proven (`events-buds-1`), but the buds need stronger art before anyone can see them.
* **A real pump crew**: keep-working is proven with the Efficient Farmhouse and the lumberjack as stand-ins (the same
  template check); no pump or lift stood in a test district.
* **The festival with Ringtails on, through their morning rest**: in `events-main-3` the 3 Ringtails did not work on the
  festival day and all 16 were at the square at h19, but no sample caught a Ringtail asleep in its rest window on that
  day (the order rest-then-festival is read from code).
* **Sounds by ear**: the probe counts 3 plays (drum loop start, firecrackers 2D and 3D) and the clips exist in
  `pandabornsounds`; nobody listened.
* Two districts, game speed 7 with many colonists over many cycles: defined above, not run.
