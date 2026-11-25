# The two signature events: Lantern Festival and Great Flowering

Status: 2026-11-25, game 1.1.2.8. Design of record for DESIGN.md Pillar 5, built as two code modules
(`src/code/Pandaborn.Festival`, `src/code/Pandaborn.Flowering`, spec records in `src/code/Pandaborn.Specs/EventSpecs.cs`)
and tested in game on dev copies of the faction built by `proto/events/build.ps1` (README there). Every mechanism below was
read from the decompiled game first; the [Results](#results) section says what was then seen in game. Both modules are in
`Pandaborn.Code.sln` and `modules.txt`, load through the bootstrap's API check, and **ship**: the catalogue switched
`rules.toml [modules] Festival` and `Flowering` on on 2026-11-14. The design changes of section 7 were accepted
(DESIGN.md, 2decaec).

**What is proven and what is not, in one place.** Everything in [Results](#results) ran in game on or before 2026-11-14.
The code changed on 2026-11-25 (the lantern sky finished, the one-district rule, the Flowering spread over ticks, wild
bamboo that reseeds, failure containment: [section 13](#13-review-of-2026-11-25)) **compiles and passes its tests without the game, and has not been
run in game**; the lantern prefab's new numbers and sprite are in the builder script and **the bundle has not been
rebuilt**. [Section 14](#14-needs-a-game-run) is the ordered list of builds and runs that this owes.

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
13. [Review of 2026-11-25](#13-review-of-2026-11-25)
14. [Needs a game run](#14-needs-a-game-run)

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
| Dusk (15.5 h) | Everyone gathers at the square, and paper lanterns begin to rise from among the dancers: one every second or two all evening, about twenty aloft at a time at every height, drifting with the wind. At 15.75 h a dense release of 24 goes up within a few seconds, with the sound of lanterns lifting. (A square without the lantern art sends up the game's red and white trail rockets instead, 24 over 1.75 h) |
| Evening, Grand only | From 15.75 h the trail rockets fly as well; from 19 h twenty fireworks burst over the square over 2.5 h, with the game's own firework sounds |
| 22 h | The gathering ends and no more lanterns leave; the last ones rise on and fade. Colonists go about their night and sleep |
| Next dawn | "The Lantern Festival is over. Everyone is festive. Tradition: 1". Everyone who did not reach the square gets festive spirit now. Tradition-locked decorations of level 1 unlock in the toolbar. Work resumes |
| Aftermath | Festive spirit (+4 well-being, +5 after a Grand Festival) fades over about 25 days (the needs' `daily_delta` -0.04 since the balance pass of 2026-11-25; data only, no number of it is in code). The panel: "The next festival can be called in cycle 3." |

Pressure points a player hits, and what happens:

* **Called in a hurry at 23:00.** It begins an hour later at dawn. Nothing is lost.
* **Called at 01:00.** It begins at the next dawn, 23 hours later: the eve is a normal working day. The panel shows the
  countdown. (Starting at once was rejected: a festival that starts mid-shift would cost two half-days and its day/night
  would not line up with the bell.)
* **A drought starts tomorrow.** Manual calls are allowed in any weather (the pumps keep their crews, so drinking water
  keeps coming; one day without food work cannot starve a fed colony, whose Hunger takes 1.25 days to reach zero and 5 to
  kill). The auto-call never fires during a drought or badtide, nor the day before one.
* **Two districts.** A festival belongs to the district of the square that called it (ruling of 2026-11-25): that
  district's colonists take the day off, gather at that square and end festive; its stores paid for it. The other
  districts work as usual and are not festive. The village still holds one festival a cycle and has one Tradition, so
  a second district cannot double it; the turn can pass from district to district, cycle by cycle (the auto-call asks
  the last host last). A colony with one district sees "the whole village", as before. Details in section 2.
* **Game speed 2 or 3.** Everything is on the game clock (behaviour decisions, launch times computed from the hour), so
  speed changes nothing but how fast it passes. The lanterns in the air follow the game's own rule for particles:
  they move at the square root of the speed (section 2, The show).

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

1. a worker at a `KeepWorkingTemplates` workplace releases to the Worker root during its working hours and works;
   after them it joins the festival like everyone else (2026-11-25; before, it spent its evening on community
   service);
2. by day, the game's `NeederRootBehavior` decides first (eat, drink, attractions, decorations, sleep near dawn);
3. otherwise, and first of all during the show (`ShowStartHours`..`ShowEndHours`), go to the district's square: onto
   one of its own 20 dance slots (the Dance Hall basis' `Dancing` slots in rings round the pole; entered with the game's
   `WalkInsideExecutor` exactly as an attraction is entered, then a 0.5–1 h stay with `ApplyEffectExecutor` and the
   square's attraction effects, so dancers also get its Campfire points); when every slot is taken, to a spot just outside
   its edge (a ring 3.2–3.8 m from its centre, else the nearest of five `GetRandomDestinationInDistrict` picks) for
   0.3–0.8 h. Overflow colonists try the slots again each time they choose. Both peoples' bodies carry the `Dancing`
   animation;
4. with no square in the district: needs, then the game's wander behaviour.

In the hours of the show the festival also goes before routines that sit above it: `FestivalGatheringClock` is the
module's Core `IGatheringClock`, and the Ringtails' day rest steps aside while it says a colonist gathers now (a
colonist of the festival's district that has the festival behaviour and is not on a crew in its hours). So a Ringtail
whose rest would run past 15.5 h (a long working day) is at the square for the lanterns; in the morning the clock
claims nobody and Ringtails sleep as on any day. Notices of a festival are posted with the square (else the district
centre) as their subject, so the notification log leads to the festival's own district (2026-11-25, round two).

**What keeps running** (so a festival never strands a colony): critical needs (above us), all eating and drinking from
stock (off-duty colonists do nothing else), the crews of the `KeepWorkingTemplates` workplaces, every bot and Wooden Ox
(no goer spec; they ignore working hours), and every building that runs without workers (water wheels, wind and kite
mills, the Scoop Wheel, the Dew Collector, mechanical pumps, flumes, decorations, growth). What stops for one day in
the festival's district: building, hauling, farming, cutting, cooking and worker-turned power wheels (so a powered pump
on a power wheel stalls; one fed by water or wind does not).

**Which workplaces are in the list** (checked against the generated build on 2026-11-25: the water buildings that have
a `WorkplaceSpec`). Staffed, and in the list: `WaterPump.Inkpaws`, `LargeWaterPump.Inkpaws`,
`PandabornTreadwheelLift.Inkpaws`. Staffed and **missing from the list: `PandabornCisternTap.Inkpaws`** (it keeps its
worker, because the vanilla flow limiter needs the workshop: without it the tap closes for the festival day, in a
drought too) and `BadwaterPump.Inkpaws` (industry, not drinking water: may stay out). In the list but unstaffed, so the
entry does nothing: `MechanicalPump`, `CompactMechanicalPump`, `AquiferDrill`, `PandabornScoopWheel`,
`PandabornDewCollector`. The corrected list is in section 8 (a request to the catalogue lane; the module reads
whatever the data says).

**Ringtails.** Both the Ringtails' day rest and the festival insert above `WorkerRootBehavior`. The rest inserts in
`InitializeEntity`, the festival in `PostInitializeEntity` (which the game runs after every component's
`InitializeEntity`), so the order is always rest, then festival: a Ringtail sleeps and eats through its morning as on any
day; outside its rest window, where it would work, the festival takes it to the square. Their templates only need
`PandabornFestivalGoerSpec`. With the Ringtails module off, saved Ringtails load as Inkpaws (their alias) and celebrate as
Inkpaws; with the festival module off, Ringtails work as usual.

The insertion uses one private field, `BehaviorManager._rootBehaviors` (the Ringtails use the same one). Fallback: if it
is gone, nobody takes the day off; the festival keeps its show, festive spirit and Tradition, and the panel's rule line
says so. Nothing of the behaviour is saved (a reload restarts the current walk).

### One district

Decided and built on 2026-11-25 (`FestivalService.FestivalDistrict`, `IsHolidayFor`, `Hosts`); **not run in game**.

* **Whose festival.** The square that calls it names the district (`DistrictBuilding.District`). The store entry keeps
  the district centre's and the square's entity ids. On the festival day `FestivalGoer` asks
  `IsHolidayFor(Citizen.AssignedDistrict)`: a colonist of another district is released at once and works as usual.
  A colonist that migrates during the day follows its new district at its next decision.
* **Where.** The district's colonists go to the calling square, or to the district's first finished square if that one
  is gone. Only the district's squares light up, drum and send up lanterns and fireworks.
* **Rewards.** Festive spirit at the square on arrival and, at the end, for every colonist of the district. Tradition
  is the village's: one counter, +1 per festival.
* **One a cycle, in the whole village.** Not one per district: with a counter per district, Tradition would rise once
  per district per cycle, and two festivals could run at once (two sets of state, two shows). A village with several
  districts chooses each cycle where the festival is held. The auto-call asks the squares of the district that held
  the last festival last, so with stock in both the turn passes on.
* **Old saves.** A save written before this rule has no district on record: its called or running festival is
  village-wide, exactly as it was. A festival whose district centre is demolished meanwhile has nobody on holiday and
  no host; it still ends at its dawn and Tradition rises (the goods were spent).
* **Texts.** With one finished district centre the module uses the existing keys, which say "the whole village" and
  "everyone" and are true. With several it uses district variants that name the district. They are new keys in a new
  file, `src/code/Pandaborn.Festival/mod/Localizations/enUS_PandabornFestivalDistricts.csv`, first-draft text **for the
  text lane to review** (fold them into `enUS_PandabornEvents.csv` when convenient; the module only needs the keys):

  | Key | Used | Arguments | Replaces, with several districts |
  |---|---|---|---|
  | `Pandaborn.Festival.RuleDistrict` | the rule line on the square's panel | - | `Pandaborn.Festival.Rule` |
  | `Pandaborn.Festival.RuleNoDayOffDistrict` | the same when the day off is unavailable | - | `...RuleNoDayOff` |
  | `Pandaborn.Festival.Status.CalledElsewhere` | status on a square of another district while a festival is called | {0} district name, {1} hours | `...Status.Called` |
  | `Pandaborn.Festival.Status.RunningElsewhere` | status on a square of another district on the festival day | {0} district name | `...Status.Running` |
  | `Pandaborn.Festival.Message.StartedDistrict` | notification at dawn | {0} district name | `...Message.Started` |
  | `Pandaborn.Festival.Message.StartedGrandDistrict` | notification at dawn, Grand | {0} district name | `...Message.StartedGrand` |
  | `Pandaborn.Festival.Message.EndedDistrict` | notification at the next dawn | {0} district name, {1} Tradition | `...Message.Ended` |

  Unchanged in both cases: `Message.Called`, `Message.CalledGrand` (they claim nothing about who celebrates),
  `Status.NextCycle`, the stock lines ("the district's stores" was already right). The Core `Messenger` files every
  notification under the first district centre in the notification log; for a festival in another district that is
  the wrong heading (a note for the Core lane, section 13).

### The show

**The lantern sky** (2026-11-25; the first version is what run `events-sky-1` saw). A Festival Square whose blueprint has
the `LanternRise` attachment (`{AttachmentId "LanternRise", Prefab "Effects/Pandaborn/LanternRise", Parent
"#LanternRise", CreateInstantly false}`; prefab in `pandabornattachments`, one `ParticleSystem` that emits nothing by
itself) gets, from `ShowStartHours` to `ShowEndHours`:

| What | How | Number, and why |
|---|---|---|
| Lanterns leaving the square all evening | the module sets the looping system's emission rate | 0.65 a second (`FestivalService.SkyLanternsPerSecond`): with the prefab's 25–40 s life that is about 21 aloft at once (15–30 was asked; `events-sky-1` at 0.85 held 20–24 and peaked at 45 with the release) and a new one every 1.5 s |
| The dense release | `ParticleSystem.Emit(1)` per lantern, from the clock | `LanternRises` (24) over 0.3 game hours from 15.75 h: 5.8 s at speed 1. `Play()` was the bug of run `lanterns-1`: it does nothing while earlier lanterns are aloft |
| The sound | `Environment.Pandaborn.LanternRise` (2.2 s, three variants) at the square | at lanterns 0, 8 and 16 of the release only; the steady sky is silent |
| Drift | velocity over lifetime x/z, written when the wind changes | the game's wind direction × (0.10 + 0.20 × strength) m/s, each lantern ±0.16 m/s of its own (±0.08 in `events-sky-1` gave one thin stream downwind) |
| The end | rate 0 and `Stop(StopEmitting)` | the lanterns aloft rise on and fade (the prefab's last 12 % of life) |
| A sky that starts late | `Simulate` fast-forward by the time since the show began, at most 40 s | after a load in the middle of the show the sky starts filled instead of refilling for half a minute; lanterns themselves are not saved |

**Time: the game's nonlinear particle clock, deliberately.** The system runs on scaled game time and its
`simulationSpeed` is `NonlinearAnimationManager.SpeedMultiplier` (√scale / scale), which is exactly what the game does
for its own smoke and sparks (`NonLinearParticlesSpeedMultiplier`). So lantern time passes at the square root of the
game speed: ×1 at speed 1, ×1.7 at speed 2 (scale 3), ×2.6 at speed 3 (scale 7); a pause freezes the sky; rate and life
are both in lantern time, so **the number aloft is the same at every speed**. The show lasts 125 real seconds at speed
1, 42 at speed 2, 18 at speed 3 (72 and 47 lantern-seconds: more than one lantern life, so the sky still fills).
Rejected: unscaled real time (lanterns rising through a pause, and an 18-second show with 30-second lanterns that
outlive it by far), and plain scaled time (lanterns at seven times their speed read as rockets).

**Comets and bursts** are the game's 1.1 firework entities (`Fireworks/*` blueprints, Common collection), spawned as the
Firework Launcher does: `EntityService.Instantiate(FireworkSpec.Blueprint)` then the component's
`Launch(position, rotation, distance)`. The component class `Timberborn.FireworkSystem.Firework` is internal, so `Launch`
(public) is called by reflection; fallback: no comets or bursts, everything else runs. The trail-only rockets
`Firework.CometRed`/`CometWhite` (gentle pitch, short flight; `LanternRises` of them over 1.75 h from 15.75 h) fly
**only in a Grand Festival, or as the lanterns' stand-in at a square without the lantern art**. The bursts
(`KamuroOrange`, `PalmGold`, `KamuroRed`, `Willow`, `PeonyYellowGreen`; `Bursts` over 2.5 h from `FireworksStartHours`)
fly only in a Grand Festival. All launch times come from the clock each tick (`FestivalRules.Due`, tested without the
game), so a reload launches only what is still due and nothing twice; the flying fireworks themselves are saved by the
game.

Hooks on the square's model (section 9): `#FestivalLights` is shown from the call to the end of the festival at a
hosting square and hidden otherwise; `#FireworkMount` is the launch point of comets and bursts; `#LanternRise` is the
attachment's parent. No attachment (`KeyNotFoundException`, caught) means a `ParticleSystem` under a `#LanternRise`
node, and neither means the comets. Every missing node, particle system or clip degrades to nothing, silently; a
failure while driving the particle system switches that square to the comets and is logged once.

Sounds: `pandabornsounds` clips `Environment.Pandaborn.FestivalDrum` (looped on a child emitter of each hosting square
during the show; the square's own emitter already loops the visitors' sound, and one emitter loops one sound),
`Environment.Pandaborn.Firecrackers` (2D at the start of the festival day, 3D at the square when the show starts) and
`Environment.Pandaborn.LanternRise` (above). A clip the game does not know (`AudioClipService.GetAudioClipNames`) is
skipped silently.

### Festive spirit and Tradition

* Festive spirit is the catalogue need `PandabornFestive` (+4, decays 0.04 a day since 2026-11-25: about 25 days). The
  module raises it to its maximum through the need system (`NeedManager.ApplyEffect(InstantEffect)`), as an attraction
  would, when a colonist first reaches the square and, at the end, for every colonist of the festival's district that
  has not. It is the game's own need state: with the module off it simply fades, and the code holds none of its
  numbers. A Grand Festival also fills `GrandNeedId` (`PandabornFestiveGrand`, +1).
* Tradition is a counter in the store (+1 per festival). It gates decorations through the game's own toolbar lock: an
  `IToolLocker`, as science and plant groups use (`ToolUnlockingService`). A decoration with `PandabornTraditionSpec`
  `{ Level }` is locked until Tradition reaches it; clicking it explains ("String Lanterns is earned with Tradition 1. Each
  Lantern Festival raises Tradition by one."). The game asks lockers with `SingleOrDefault`, so two lockers claiming one
  tool would throw: the Tradition locker only claims tools science does not lock, and **Tradition decorations need
  `ScienceCost` 0**. Unlocks are not saved by the game (the lock is recomputed from Tradition at every load). With the
  module off there is no locker: the decorations are simply buildable.

### Saved state

Store entry `Festival` v1: `phase`, `day`, `grand`, `last` (cycle of the last festival), `tradition`, `auto`, `count`,
and since 2026-11-25 `district` and `square` (entity ids; empty or absent: village-wide). Additive: the version stays 1,
an older module ignores the two keys, a newer one reads their absence as the old rule.

The festival's day is booked to its cycle when the game posts `CycleDayStartedEvent`, not on `DaytimeStartEvent`:
`GameCycleService` moves the cycle on in its own handler of `DaytimeStartEvent`, and whether that ran before ours was
only load order. Had ours run first, a festival held on the first day of a cycle was booked to the cycle before and a
second one could be called in the same cycle.

## 3. Great Flowering: what the player experiences

| When | What the player sees |
|---|---|
| Before cycle 6 | Nothing, except a line on any bamboo's panel: "Bamboo flowers once in a long while: about every 5 to 7 cycles, never before cycle 6." and a **Flowering: Normal** button (the setting) |
| Start of cycle 5 (a full cycle ahead) | "The Shoot Bamboo is budding. It will flower at the start of cycle 6, bear seed for a few days and die." A line under the top bar: "Shoot Bamboo flowers at the start of cycle 6", whose tooltip gives one instruction: "Store about 11 food for each panda before it starts" (timber bamboo: about 5 poles for each panda; a Pole Mill can split logs into poles meanwhile). Every shoot bamboo's panel: "Budding: it will flower at the start of cycle 6, bear seed for 3 days, then die." Buds on the plants once the plant lane paints them |
| Start of cycle 6 | "The Shoot Bamboo is in flower. 56 plants bear 168 bamboo seed: harvest it within 3 days." Every grown shoot bamboo on the map, planted or wild, becomes Flowering Shoot Bamboo, whose harvest is bamboo seed; young plants die. Top-bar line: "Shoot Bamboo in flower: harvest the seed, 3 days left" |
| Days 1–3 | Farmers harvest the flowering plants for seed exactly as they harvest shoots (it is their crop's harvest), carry it to the farmhouse and on to storage. Freed tiles are replanted at once from the planting marks |
| Day 3 | Over the last day the flowering plants' time ends ("The flowered Shoot Bamboo has died. Bamboo seed harvested: 151. Its young plants grow again in 6 days."). On a farm's or forester's marked tiles the unharvested ones die where they stand and are planted over. **A wild one, on a tile nobody marked, that is still standing reseeds its own tile**: a seedling takes its place. One that was cut for its seed is gone, like any wild tree that is cut |
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
* **The Flowering** (`FloweringService.Flower`, `ConvertSome`): for every plant of the species: grown and alive → deleted
  and its twin (`InFlowerTemplate`) spawned on the same tile (`NaturalResourceFactory.SpawnIgnoringConstraints`, then
  grown with `Growable.IncreaseGrowthProgress(1)`); young → `LivingNaturalResource.Die()`; a harvested crop whose pile
  still lies there is left alone. **Since 2026-11-25 this is spread over game ticks**: `Flower` only sets the state; in
  the first tick after it the young plants die and the grown ones queue up, sorted across the map; each tick then turns
  plants until about 5 ms have gone (never fewer than 8), so a farm of a few dozen flowers within a few ticks and a map
  of thousands comes into flower as a wave over the first hours of day 1 (768 ticks a day). The "in flower" notice with
  the counts comes when the last plant has turned. Why: each replacement deletes one entity and creates another, and
  `EntityRegistry.RemoveEntity` alone is a linear search of every entity in the game per deletion; thousands in one
  tick, inside the cycle-start event, would stall the game (estimated from the code, never measured: no test had more
  than 56 plants). The progress is saved (`converting`: 2 not begun, 1 grown plants still turning, 0 done), so a save
  made in the middle goes on after the load. And no entity is touched in PostLoad or an event handler any more: by the
  game's code a twin placed before the event bus is ready (a Flowering that fell due at a load) had its planting mark
  cleared again afterwards, when the queued `BlockObjectSetEvent` reached `PlantingCoordinatesUnsetter`. The twin's harvest is its cut yield, `PandabornBambooSeed` × 3, in the same resource group as the bamboo
  (Farmhouse / Cuttable), so the farmhouse's and lumberjack's inventories accept seed (`YieldRemovingBuilding` allows the
  yields of every template of its group) and their workers harvest and carry it with the vanilla behaviours.
* **The twins' end**, over the last day of `SeedDays`, each at a time hashed from its tile (`FloweringSchedule.EndOf`,
  tested without the game):
  * **on a tile with a planting mark** the twin dies where it stands, as before. Dead crops lose their seed (the game's
    rule) and become overridable, so farmers plant over them; dead twin trees keep their seed until a lumberjack cuts
    them, then leave a stump to replant.
  * **wild, on a tile without a planting mark, and still standing: it reseeds its own tile** (the coordinator's ruling
    of 2026-11-25; before it, twins did not reproduce and only marked tiles were replanted, so every wild grove
    flowered once and was gone). The twin is deleted and a new plant of its species is placed on the tile
    (`NaturalResourceFactory.SpawnIgnoringConstraints`: a new plant is a seedling), which registers like any bamboo and
    is held until the rest ends. Its uncut seed goes with it (trees too: the three seed days are the time to cut a
    wild grove).
  * **cut for its seed**: a cut plant is dead from the cut (`Cuttable.Cut` calls `Die`), so it has no end left to
    meet: a crop is carried off and removed, a tree leaves its stump. Gone, like any wild tree that is cut.
  Every in-game hour the twins that are alive and due queue up; they meet their end in the following ticks on the same
  budget as the change into flower (a wild grove of thousands is 1/24 of it an hour, a few plants a tick). Nothing
  pending is saved: a due twin is either still alive, and queues again at the next hourly pass, also after a load,
  or it is dead or replaced. The seed time closes when no twin is left alive. The count of reseeded plants is saved
  (`reseeded`, additive) for the log line at the end of the seed time. If replacing fails five times in a game, wild
  twins die where they stand for the rest of it (the old behaviour) and the feature reports it.
* **Replanting and the rest**: planting marks are a separate map (`PlantingService`) and are never touched, so farms and
  foresters replant on their own. Until `DormantDays` (9) after the Flowering, young plants of the species do not grow:
  the module pauses each one's growth timer every in-game hour and whenever one is planted. The game has no public pause
  for growth, so this uses the private field `Growable._timeTrigger` (an `ITimeTrigger`, a public interface with
  `Pause`/`Resume`). Fallback: no rest (young bamboo regrows at once: the event is shorter, never harsher). The holds are
  not saved; the game saves growth progress and the module holds the plants again after a load.
* **A hold is re-read, never trusted.** The timer is taken from the plant at every call, and every resting plant is held
  again after a load, every in-game hour, when the Flowering begins and when a plant is planted. The game itself
  resumes a plant that stops dying; and another mod may replace the timer object: TimberCommons' `GrowthRateModifier`
  does when one of its growth modifiers registers, and resumes the new one (compatibility audit of 2026-11-25, m6).
  Either way the plant grows for at most one in-game hour before it is held again (a 3-day crop gains about 1.4 %).
  The first hourly check that finds resting plants growing writes one log line; `FloweringService.HeldAgain` counts
  them. This was already how the module worked; on 2026-11-25 the counter, the log line and the handling of a timer
  that throws were added. Not seen in game with TimberCommons (section 14).
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

**Choice: `DormantDays` 9** (a 12-day gap for shoot bamboo; 16 days for timber bamboo, which grows in 7 since the
ruling of 2026-11-25, was 5 and 14). A colony that
follows the forecast is never at risk at either length; at 15 days, one that keeps a thin two-day pantry and ignores the
forecast loses a third to two-thirds of its colonists when the cycle's drought follows, at 12 days it loses none. The
event still costs real food: 0.35 × 2.67 × 12 ≈ **11 food per panda** without the stock (what the tooltip asks for), and
about 6 poles per panda for timber (0.35 a day × 16; it was "about 5" at 14 days: the tooltip no longer gives a number). The seed windfall (3 a plant; a 40-colonist colony grows about 56
shoot tiles, so about 168 seed, 670 seed cakes) refills the pantry once a Kitchen and rice flour exist.

**Warning for the coordinator:** the balance sheet's "until the next temperate season" and "reserve 14 food a colonist"
should become "9 days of rest" and "about 11 food a colonist". On Hard (temperate 5–8 days) the rest always runs into the
cycle's drought; there shoot bamboo is not the staple (balance claim 8: cabbage is), and the drought decides more than
the Flowering. A future Hard tuning could shorten `DormantDays` per game mode; not done.

## 6. Edge cases, defined

| Case | Festival | Flowering |
|---|---|---|
| Save and reload mid-event | Phase, day, grand, district and square are in the store; colonists re-enter the festival at their next decision; the show resumes from the clock without repeats; the lantern sky starts filled | Phase, species and day are in the store; twins are ordinary saved plants; young plants are held again at load; a change into flower that was under way goes on with the grown plants that are left |
| Called at hour 23 | Begins at dawn, an hour later | — |
| Two districts | The calling square's district only: its colonists off and festive, its stores, its square; the others work. One festival a cycle in the village, one Tradition | Flowers on the whole map, every district |
| Drought or badtide | Manual call allowed (pump crews keep working); auto-call never, nor the day before | Impossible by construction: day 1 of a cycle is temperate; the seed days end before any hazard |
| Game speed 2 / 3 | Clock-driven; nothing depends on frames. Lanterns in the air on the game's nonlinear particle clock: same number aloft at every speed | Hourly ticks on the game clock; the change into flower takes the same number of ticks at every speed |
| Module forced off in a save mid-event | Everyone works as usual; goods already spent; store entry kept. Back on: a festival whose day passed ends at load with its rewards; one called for today starts | No new Flowering; twins stay plants that bear seed and never die by themselves; young bamboo grows; store entry kept. Back on: picks up (an overdue announced Flowering moves to the next cycle start) |
| Game update removes a private member | No day off (show, festive, Tradition kept); or no fireworks | No rest after a Flowering (milder) |
| The square is demolished while called | The festival still runs; the district's colonists go to another square of the district, or have a day off without one | — |
| The district centre is demolished while called | Nobody is on holiday and no square hosts; the festival ends at its dawn and Tradition rises | — |
| A colonist moves to another district on the day | It follows its new district at its next decision | — |
| Another mod swaps a plant's growth timer | — | Held again within an in-game hour |
| A wild grove (no planting marks) | — | The plants still standing at the end of the seed days reseed their tiles and rest with the others; those cut for seed are gone |
| A wild tile the player marks during the seed days | — | It is a marked tile when its twin's time comes: the twin dies standing and the farm or forester replants |
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
| 2026-11-25: a festival is the calling square's district's, not the whole village's (it was: everyone off and festive, each district at its own square) | The coordinator's ruling. One festival a cycle and one Tradition stay village-wide, so districts take turns |
| 2026-11-25: pump crews join the festival after their working hours | They were released to the game's worker behaviour all day and night, so they hauled in the evening while everyone else danced |
| 2026-11-25: the bamboo comes into flower over the first hours of the cycle's first day on a large map, not in one instant | Spread over ticks so that thousands of plants do not stall the game. Still always day 1 of a cycle; the seed days count from the start |
| 2026-11-25: wild bamboo reseeds after a Flowering (a standing flowered plant on an unmarked tile leaves a seedling; cut ones are gone; marked tiles unchanged) | The coordinator's ruling on the review's finding: without it every wild grove flowered once and was gone for good |
| 2026-11-25: comet rockets only in a Grand Festival (or without the lantern art) | With real lanterns the rockets are a firework, and fireworks are what makes a festival Grand |

## 8. Requests to the catalogue lane

**Status (2026-11-25):** the catalogue has applied all of the numbered requests below, and both module switches are on
(square on `DanceHall.Folktails`, the three module specs on the characters, `PandabornFestiveGrand`, Tradition levels, the
twins on the plant lane's flowering models, `BudsUseDetail = true` on shoot bamboo and `false` on timber bamboo). The dev
copies generate exactly this data from a scratch copy of the catalogue. **Still open, two requests:**

**A. The square's `LanternRise` attachment: ADOPT AFTER THE BUNDLE IS REBUILT** (section 14, steps 1 to 3; until then
the installed bundle carries the old prefab, 0.5 m lanterns that live 10 to 16 s and nine built-in bursts; the module
would drive it without error, but the sky would be thin and fast). On `PandabornFestivalSquare` in `buildings.toml`,
appended to the basis' `TemplateAttachmentsSpec.Attachments` (the Dance Hall basis already has the spec; the entry is
the one `proto/events/variants/sky` merges in, proven to load and play in `events-sky-1`):

```json
"TemplateAttachmentsSpec": { "Attachments#append": [ {
    "AttachmentId": "LanternRise", "Prefab": "Effects/Pandaborn/LanternRise", "Parent": "#LanternRise",
    "Position": { "X": 0.0, "Y": 0.0, "Z": 0.0 }, "Rotation": { "X": 0.0, "Y": 0.0, "Z": 0.0 },
    "Scale": { "X": 1.0, "Y": 1.0, "Z": 1.0 }, "CreateInstantly": false } ] }
```

It must sit behind the Festival switch like the square itself, and it makes `pandabornattachments_win|_mac` a bundle
the square needs: `Prefab` is an asset reference, and a blueprint that names a prefab no bundle carries stops every
game at load (`events-final-1` was exactly that crash, with a character attachment). The adopted model already has
the `#LanternRise` node (`art/models/FestivalSquare/build.py`).

**B. `KeepWorkingTemplates`: adopted** (2026-11-25, in the coordinator's form: the existing list kept,
`PandabornCisternTap.Inkpaws` added; `catalogue/faction.toml` carries it). Every entry is harmless: a name is only
compared with the template of a colonist's own workplace, so an unstaffed building (`MechanicalPump`,
`CompactMechanicalPump`, `AquiferDrill`, `PandabornScoopWheel`, `PandabornDewCollector`: no `WorkplaceSpec` in the
generated build) or a name no template has simply never matches. `BadwaterPump.Inkpaws` is staffed and not in the
list: its crew takes the day off.

Done by other lanes meanwhile, nothing to do: the festive needs' `daily_delta` is -0.04 (no code reads it); the
Lantern Workshop costs 100 science and the Festival Square 200 (only Tradition decorations must cost 0); the six plant
text keys of the twins left `enUS_PandabornEvents.csv` and live in `catalogue/text/plants.json`.

The original requests, as they were made:

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
5. **The two bamboos** (`plants.toml`): `PandabornFloweringPlantSpec = { InFlowerTemplate = "PandabornShootBambooInFlower.Inkpaws", BudsUseDetail = true }`
   on `PandabornShootBamboo` (the plant lane painted its buds in the detail map), and `InFlowerTemplate =
   "PandabornTimberBambooInFlower.Inkpaws", BudsUseDetail = false` on `PandabornTimberBamboo` (its detail map is the
   bamboo fungus: section 10). This is what the catalogue carries.
6. **The two twins** (`plants.toml`, new items in `NaturalResources.Inkpaws`): copies of each bamboo with the same model
   (until the plant lane's flowering models exist), `cut_yield = { PandabornBambooSeed = 3 }` in the same resource group,
   **no** `PlantableSpec`/`PlantablePreviewModelSpec` (no planting tool), no `ReproducibleSpec`, no `GatherableSpec`
   (timber), and `add = { PandabornInFlowerSpec = { Species = "PandabornShootBamboo.Inkpaws" } }` (resp. timber).
   `proto/events/tools/derive.py` was the reference implementation. Names "Flowering Shoot Bamboo" / "Flowering Timber
   Bamboo": in `catalogue/text/plants.json` (the copies in `enUS_PandabornEvents.csv` were removed on 2026-11-25).
7. **Balance note** (`docs/tech/balance.md` Q7 is the balance lane's): "blocked until the next temperate season" →
   "9 days of rest after the Flowering"; reserve 14 → 11 food a colonist (section 5).

## 9. Requests to the model lane (Festival Square)

A 5 × 5 open village square on the dance-hall slots (visitors dance in the open, visible in the slots), timber frame and
plaster, a tall central lantern pole or small stage, red only on the lanterns. Named child nodes the module drives:

| Node | Kind | Driven by the module |
|---|---|---|
| `#FestivalLights` | static lantern strings and lit stall lanterns (emissive or `WindowsAtlas` lit regions) | shown from the call to the end of the festival, hidden otherwise (with the module off they always show) |
| `#LanternRise` | an empty on the dais near the centre: the parent of the `LanternRise` attachment (the lantern particle prefab, section 2) | the module sets the particle system's rate, releases, drift and speed; lanterns leave from a 3.8 m box round this node at hand height |
| `#FireworkMount` | an empty transform at the launch point (pole top) | launch origin of comets and bursts |

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
| `events-crowd-1` | copy `pbevents4` (variant `crews`, no LanternRise attachment, so comets): 13 starting colonists plus 14 spawned adults (27), festival called; festival-goers onto the square's dance slots | **PASS, 0 own errors.** The square's 20 dance slots were full (20/20) for most of the festival day and from the show's start to its end at h22; the overflow (3–4) stood at the square's edges, the farmhouse crew (3) worked. 24 of 27 attended. From the normal camera the square is a full ring of dancing pandas round the lantern pole: dusk with the comets rising (`ev_cr_d1_h16_dusk_b.png`), night (`ev_cr_d1_h20_night.png`, `ev_cr_d1_h21_night_b.png`), day (`ev_cr_d1_h11_day.png`), the panel (`ev_cr_d1_h17_dusk_panel.png`). Both peoples' bodies carry the `Dancing` animation (adult and young, Inkpaw and Ringtail meshes) |
| `lanterns-1` (2026-11-14, ended 18:20) | copy `pblanterns` (built 17:14–17:18 by `proto/events/build.ps1 -Variant proto\ringtail-body\variants\lanterns -NoProbe`), queued by the characters lane. **Code: the committed module of that hour** (5f2a933: `FestivalSquare.Launch` called `ParticleSystem.Play()` once per lantern). **Bundle: the first lantern prefab** (bc43759, built 17:25: 0.44–0.58 m quads, 1.0–1.5 m/s, 10–16 s life, a non-looping 9 s schedule of nine single bursts) | **PASS, 0 own errors; the prefab renders and glows the right colour, the show does not work.** The probe counted 24 launches by 18 h, but a `Play()` on a system that still has lanterns aloft does nothing and one on an idle system starts a flight of nine: the shot at 16.8 h shows one flight of about nine small lanterns (`ev_l_d1_h1610.png`), others show two far from the square or none (`ev_l_d1_h1590_first.png` … `ev_l_d1_h1710.png`). 13 of 20 slots danced on. This run is why the lanterns were reworked |
| `events-sky-1` (2026-11-14, 19:05–19:09) | copy `pbsky` (`-Variant proto\events\variants\crews,proto\events\variants\sky`), scenario `events-sky`, game speed 1, 27 colonists. **Code: the rework as it stood that evening, uncommitted** (kept as `wip/pause-2026-11-14`, ca45aaf): the module sets the rate (0.85 a second then), emits the release of 24 over 0.3 h, wind drift, the nonlinear clock. **Bundle: a Windows-only `pandabornattachments_win` built that evening from the then uncommitted builder** (0.7–0.9 m quads, 0.5–0.9 m/s, 25–40 s life, 160 particles, no bursts; the old sprite); the copy's `_mac` bundle was the old one | **PASS, 0 own errors.** Lanterns aloft (`skyLanterns`, the particle count): 2 at 15.62 h, 24 at 15.91, 33 at 16.12, 38 at 16.5, 45 at 17.0, 36 at 17.5, then 20–24 from 18 h to 22 h, 17 at 22.31 h (emission stopped, fading), 10 at 23 h. 24 lanterns released, 6 sounds, the square's 20 slots full from 15 h to 22 h. From the normal camera at dusk the near lanterns read as glowing paper lanterns (`ev_s_h1700_dusk.png`); the wide shot at 18 h shows about seventeen in one stream rising downwind of the square (`ev_s_h1800_wide.png`); night `ev_s_h1950_night.png`, after the end `ev_s_h2230_after.png`. **Not what is committed now:** since then the rate is 0.65, each lantern's own drift is doubled (to break up the single stream), the sprite is repainted, the fades changed, comets fly only in a Grand Festival, and the district rule and the load fast-forward were added; none of that has run (section 14). `events-sky-2` (speed 3) was queued at 19:11 and never ran: the project was paused |

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

The square looks like a festival: at dusk and at night its lantern strings glow red-orange over the pale paving and
twenty pandas dance in rings round the lantern pole, with the overflow close in at its edges
(`events-crowd-1\ev_cr_d1_h20_night.png`; before the dance slots, `events-final-2\ev_f_d1_h16_dusk_b.png` showed three
pandas on it and the rest scattered).

The sky was the weak part and is now most of the way there. The vanilla comets read as rockets, gone in seconds; the
`Sparks_Trail` stand-in was a small pink sparkle at the pole; the first lantern prefab driven by `Play()` gave a
flight of nine now and then (`lanterns-1`). With the module feeding the particle system (`events-sky-1`) the evening has
twenty-odd paper lanterns in the air from dusk to 22 h and a visible release at 15.75 h, and from the normal camera
the near ones are plainly lanterns. What that run still showed, and what was changed for it without a new run: the
lanterns left in one narrow stream downwind (each lantern's own drift doubled, the wind's share lowered a little); the
old sprite was soft, mostly halo (repainted: the paper fills 74 % of the quad's height with a dark crisp silhouette,
preview `E:\PandabornDev\build\toolcheck\skylantern\sky_lantern_preview.png`); the count overshot to 45 after the
release (rate 0.85 → 0.65). Whether the sky now reads as "above and around the square" is for the proof run to show
(section 14). Burst fireworks (Grand only) are the game's own and look right.

## Unproven

* **Everything changed on 2026-11-25** (section 13): compiled, unit-tested where it is arithmetic, read against the
  game's code, not run. Section 14 lists the runs.
* **Visible buds**: the switch is proven (`events-buds-1`), but the buds need stronger art before anyone can see them.
* **A real pump crew**: keep-working is proven with the Efficient Farmhouse and the lumberjack as stand-ins (the same
  template check); no pump, lift or tap stood in a test district.
* **The festival with Ringtails on, through their morning rest**: in `events-main-3` the 3 Ringtails did not work on the
  festival day and all 16 were at the square at h19, but no sample caught a Ringtail asleep in its rest window on that
  day (the order rest-then-festival is read from code: section 13, Ringtails).
* **Sounds by ear**: the probe counts plays (drum loop start, firecrackers 2D and 3D, the lantern-rise sound) and the
  clips exist in `pandabornsounds`; nobody listened.
* **Two districts**: built on 2026-11-25, never run; no scenario can build a second district yet.
* **A large map**: no run had more than 56 bamboo plants or 27 colonists; the cost of one plant's change into flower
  was never measured (the 5 ms budget per tick is a guess that bounds the hitch whatever the cost).
* Game speed 3 with the lantern sky; many cycles in one game.

## 13. Review of 2026-11-25

Both modules were read end to end against the decompiled game (event order, load and post-load, entity deletion,
districts, the behaviour system) with no game available. Findings by severity; "fixed" names the commit.

### Fixed

| | Finding | Where | Fix |
|---|---|---|---|
| Major | **A behaviour's exception ends the session.** `BehaviorManager.Tick` does not catch what a root behaviour's `Decide` throws, and `FestivalGoer.Decide` ran unguarded through walking, entering, effects and district lookups for every colonist on the festival day | `FestivalGoer.Decide` | wrapped: logged once, the colonist is released to its ordinary day (8038a53) |
| Major | **The lantern show did not work**: `Play()` per lantern (run `lanterns-1`) | `FestivalSquare.Launch` | the lantern sky (section 2): rate from code, `Emit` for the release, stop and fade (8038a53, ef00de2) |
| Major | **The once-a-cycle rule depended on handler order.** Dawn was taken from `DaytimeStartEvent`, the same event on which `GameCycleService` moves the cycle on; had our handler run first, a festival on day 1 of a cycle was booked to the cycle before and a second could be called in that cycle | `FestivalService.OnDaytimeStart` | dawn from `CycleDayStartedEvent`, which the game posts after the cycle is current (8038a53) |
| Major | **The Flowering replaced every plant in one tick**, inside the cycle-start event: one entity deleted and one created per plant, each deletion a linear search of all entities, plus a linear `List.Remove` of our own per plant | `FloweringService.Flower` | spread over ticks with a time budget, saved progress, sets instead of lists (b628c63) |
| Major | **A Flowering that fell due at a load lost its planting marks** (by the code: twins were placed in `PostLoad`, before the event bus delivers the queued `BlockObjectSetEvent`; `PlantingCoordinatesUnsetter` then cleared the mark we had just put back). Reached when the module was off at the cycle start and on again that day | `FloweringService.PostLoad` → `Flower` | no entity is touched outside a tick (b628c63) |
| Major | **Districts**: everyone took the day off, but the goods came from one district and the show ran at every square; the rule had to be decided | `FestivalService`, `FestivalGoer` | the one-district rule (section 2) (8038a53) |
| Minor | One odd entity (no worker and no needer behaviour) set the static "day off unavailable" for every colonist created after it, for the rest of the session, including the next game, and never reached the feature report | `FestivalGoer.Insert`, `Fail` | only a missing private member is global; it is reported with `ReportDegraded` whenever found; statics reset at each game's Load (8038a53) |
| Minor | A click on a Tradition-locked decoration could throw (label spec missing, dialog changed) inside the game's tool-unlock call | `TraditionToolLocker.TryToUnlock` | contained; a lock that cannot explain itself opens (8038a53) |
| Minor | Entity callbacks (`PostInitializeEntity`, finished-state, delete), the `Changed` listeners, the cut event and `GrowthHold.Hold/Release` could let an exception into the game's entity loop | both modules | wrapped (8038a53, b628c63) |
| Minor | The drum was started per show, not per square: a square finished or reconnected during the show stayed silent, and one removed kept the flag | `FestivalService.UpdateShowSounds` | kept per square (8038a53) |
| Minor | Pump crews never joined the festival | `FestivalGoer.KeepsWorking` | after their working hours they do (8038a53) |
| Minor | `Persist` once per dying twin, per hour | `FloweringService.Advance` | once per pass (b628c63) |
| Minor | A seed time under a day put the twins' deaths before the Flowering | `Advance` | `FloweringSchedule.DieAt` spreads over the time there is (b628c63) |
| Minor | The dishes taken were chosen after an unstable sort (ties could differ from the panel) | `FestivalStock.Take` | `FestivalRules.PickDishes`, stable and tested (a602675) |
| Minor | An unknown enum number in a hand-edited save became a phase | both `ReadState` | `Enum.IsDefined` (8038a53, b628c63) |
| Minor | The square's panel kept reading a square demolished while it was open | `FestivalSquareFragment.Refresh` | checked (8038a53) |
| Minor, round two | **Wild bamboo never came back after a Flowering** (twins do not reproduce; only marked tiles were replanted) | `FloweringService.Advance` | the reseeding rule, ruled by the coordinator (37e7a70) |
| Minor, round two | A Ringtail whose rest ran past 15.5 h missed the release (the rest sits above the festival) | `RingtailRestRootBehavior`, Core `IGatheringClock` | the Core and Ringtails lanes added the contract; the festival registers `FestivalGatheringClock` (ae3111f) |
| Minor, round two | Faults were reported for the session (`ReportDegraded`) though every check is made per game, and a second fault replaced the first in the report | both modules | `ReportDegradedInGame` through one `Fault` method per module that keeps the game's list (ae3111f, 37e7a70) |
| Minor, round two | A festival's notices were filed under the first district centre | `FestivalService.Call/Start/End` | posted with the square, else the district centre, as subject (`Messenger.Post(text, subject)`, Core 1b3eb58) (ae3111f) |
| Minor, round two | Fireworks that failed in the middle of a game were logged but never reported | `FestivalFireworks.Fail` | reported (ae3111f) |

### Left, and why

| | Finding | Why left |
|---|---|---|
| Major (data) | `KeepWorkingTemplates` lacks the staffed `PandabornCisternTap.Inkpaws` | catalogue lane's file: request B in section 8 |
| Major (art) | The lantern prefab and sprite are changed in source only | no Unity today: section 14 |
| Minor | The festive need is filled again for a colonist that re-enters the square after a load (the attended set is not saved) | harmless: it is already at its maximum |
| Minor | Buds use `renderer.material` (one material instance per renderer of every announced plant for a cycle) | it is exactly what the game's `GatherableModel` does for every berry bush; revisit only if a large map shows it |
| Minor | During the show nobody runs the need loop (critical needs only), 6.5 h | by design: Hunger and Thirst take far longer to matter and the square pays Campfire points; the critical behaviour is above us |
| Minor | The stock counted and taken includes input stores of workshops and consumers (every public inventory of the district), e.g. fireworks waiting in a Firework Launcher | it is "what the district has in store"; changing it needs a rule for which stores count |
| Minor | The overflow crowd asks for five random district spots and up to two paths per decision | 0.3–0.8 h between decisions; of the order of what working colonists cost. To measure at 300 colonists (section 14) |
| Minor | `FestivalFireworks` warns in the log in every game, also Folktails', when the game's firework class changes | one line; the module is otherwise inert outside Inkpaws games |

### For other lanes

* **Catalogue**: requests A (after the bundle) and B in section 8.
* **Text**: the seven district keys (table in section 2), first drafts in `enUS_PandabornFestivalDistricts.csv`.
  `Message.Started*` says "Only the pump crews work today": with the tap in the list it is pumps, lifts and taps.
* **Core**: nothing open. `ReportDegradedInGame` and `Messenger.Post(text, subject)` (1b3eb58) and `IGatheringClock`
  are used by both modules since round two.
* **Scenarios** (`src/devharness`, `tests/scenarios`): the two-district scenario needs the harness to place a second
  district (section 14, "What a two-district scenario needs"); the probe's half is written. The two wild-grove
  requests are in `proto/events/requests/` (runnable today; move them to `tests/scenarios/events/` if you keep them).
* **Ringtails**: the static `RingtailRestRootBehavior.InsertionError` is set for the session by one failing entity,
  as ours was (the lane's working tree already guards `Decide`).
* **Docs**: `docs/tech/ringtail-body.md` 8.7 describes the first lantern prefab (nine bursts, 10–16 s, `Play()` per
  lantern) and a `lanterns-1` "queued"; this page now holds the prefab's contract and both runs.
* **Bundles / release**: once request A is adopted the Festival Square needs `pandabornattachments_win|_mac` at
  load; `assemble` should refuse a build whose square names the prefab without the bundle (as it does for models).

### Checked and found right (by code)

* **Load order**: singletons `Load`, then every entity is loaded, initialised and post-initialised, then singletons
  `PostLoad`, then entities' `PostLoadEntity`. So at our `PostLoad` the colonists, squares and plants are registered
  (a festival that ended while the code was off is settled there, as `events-backon-2` saw), and nothing in `PostLoad`
  needs an `Enterer`'s restored state.
* **Saved behaviours**: the game saves the running behaviour by component name and drops one it cannot find, so a
  save made in the middle of a festival walk loads cleanly with the module off; walking to and standing on the
  square's slots is reserved and released by the game's own `Enterer` and `WalkInsideExecutor`, also on death.
* **Non-Inkpaws games**: no spec, so neither service registers for events or ticks beyond one null check; the
  decorators exist only on Inkpaws templates; the tool locker answers "no" for every tool. **Map editor**: the
  configurators are `Game` context only; the spec records deserialise from the always-loaded Specs assembly.
* **Module off then on, older and newer saves**: all new store keys are additive under version 1 and read tolerantly.
* **Design fidelity** (`FloweringSchedule`, tested over 400 cycles per setting and seed): never before cycle 6 (9 when
  rare), always day 1 of a cycle, announced exactly one cycle ahead in an unbroken game and never less after a load
  or a setting change, intervals within the data's range, species alternating; the seed is the twin's harvest; the
  rest keeps the planting marks. Festival: once per cycle, the auto-call only in fair weather (`IsHazardousWeather`
  and `NextDayIsHazardousWeather`), everyone of the district ends festive, Tradition unlocks through the game's lock.
* **Ringtails** (read from `Pandaborn.Ringtails`, not edited): the rest inserts at the index of `WorkerRootBehavior`
  (`NeederRootBehavior` for kits) in `InitializeEntity`; the festival inserts at the same index in
  `PostInitializeEntity`, which the game runs after every `InitializeEntity`, so the list reads ..., rest, festival,
  worker. Inside the rest window the rest decides (sleep, needs, wander) and the festival is not asked; outside it
  the festival takes the Ringtail to the square instead of its night post, all night. Their worker type ignores
  working hours, so a Ringtail at a keep-working workplace would work on. With the Ringtails module off the saved
  Ringtails are Inkpaws and nothing differs.
* **Balance of 2026-11-25**: no code reads the festive needs' decay or well-being, the science costs, or a growth
  time; the texts no longer give the 20 days.

Tests without the game: `dotnet run -c Release --project src\code\tests\Events` (28,427 checks: the calendar, the
deaths, the once-a-cycle rule, the dishes, the launch times across ticks, jumps and loads, the sky's steady count).

## 14. Needs a game run

Nothing of 2026-11-25 has run. In order; each step needs the one before. Runs go through `tools\run_game_test.ps1`
(hidden desktop, the test mutex), map Plains, `-OnlyMods JigglyPanda.PandabornFactionsDev`, with
`-ExtraMods <copy>,E:\PandabornDev\build\proto\events-probe`.

**Builds**

1. `powershell -ExecutionPolicy Bypass -File src\unity\PandabornAttachments\build.ps1` (Unity batch mode: paints the new
   sprite, builds the prefab and `pandabornattachments_win` into `E:\PandabornDev\build\characters\attachments`), then
   the same with `-Mac`. Check with UnityPy, as before: the prefab has `_EMISSION`, rate 0, no bursts, max 160.
2. `proto\events\build.ps1 -Name pbsky -Variant proto\events\variants\crews,proto\events\variants\sky -AttachmentBundles E:\PandabornDev\build\characters\attachments`
   (also builds the probe against the new modules).

**Runs**

| # | Run | Command (after the common part) | What must be seen |
|---|---|---|---|
| 3 | the lantern sky, speed 1 | `-RequestJson tests\scenarios\events\events-sky.request.json -ExtraMods ...\pbsky,...` | 0 own errors. `skyLanterns` 15–30 from about 16 h to 22 h (a short peak after the release is fine), falling to 0 within an hour after 22 h; `lanterns` 24, `comets` 0, `bursts` 0. Shots: lanterns above and around the square at every height, not one stream; the near ones lantern-shaped (`s_h1750_dusk_close`); the wide shots show the square as the source. Listen once: the rise sound only at 15.75 h |
| 4 | the same at speed 3 | `events-sky-speed3.request.json` | the same counts; the lanterns do not read as rockets |
| 5 | adopt request A in the catalogue, full build | `tools\pandaborn.ps1 all` (the gate runs the grid) | the gate passes with the attachment on the installed square |
| 6 | the old proofs again on the new code | `events-main` with `-SaveAndReload` on a fresh `pbevents` (`-Variant proto\events\variants\test,proto\events\variants\sky` until the catalogue carries the attachment) | as `events-main-3`: auto-call, Grand day (now `comets` 24 and `bursts` 20 beside the sky), nobody working but the crew, 16/16 festive, Tradition, the drought call; **after the mid-show reload `skyLanterns` is above 10 at the first sample** (the fast-forward) and only the launches still due happen; the Flowering: `converting` true then false within the hour, the "in flower" notice with the right counts, seed harvested, tiles replanted (marks kept), the rest held |
| 7 | fallbacks | `events-fallback` (`pbevents-fb`, its dev switch) and `events-backon` (`pbevents-on`) | as before; with `Festival.Fireworks` simulated missing the lantern sky still runs |
| 8 | crews | `events-crews` (`pbevents2 -Variant proto\events\variants\crews`) | the crew works its hours and **is at the square in the evening** (new); replanting after the rest |
| 9 | a real water crew | a new request: a Water Pump, a Treadwheel Lift and a Cistern Tap staffed in the district (after request B) | all three crews at work on the festival day in their hours |
| 10 | two districts | **blocked on the harness** (see "What a two-district scenario needs" below); the probe's side is ready: `"district": n` on `stock`, `spawnAdults`, `callFestival`, shot target `square:n`, and the sample block `festivalDistricts` | per district in `festivalDistricts`: A (the caller): `dayOff` = its colonists minus the crew, `working` only the crew, its square `hosts` true with lanterns aloft, `festiveAvg` 1 at the end; B: `dayOff` 0, colonists `working`, its square `hosts` false, 0 lanterns, `status` "A festival begins at dawn in A ..." then "The Lantern Festival is today in A ...", `festiveAvg` unchanged. The notices name A, and clicking them in the notification log goes to A's square. Next cycle, both stocked and auto-call on: B is called |
| 11 | a large colony | a late save or a probe run with 300+ colonists and a festival; 2,000+ shoot bamboo and `flowerNow` | no frame stall at dawn, at 15.5 h or at the Flowering; how many ticks the change into flower takes (`convertQueue` per sample), FPS during it; the overflow crowd's cost |
| 12 | TimberCommons (audit m6, run 6 of the compatibility list) | ours + TimberCommons, a building with its growth range effect beside resting shoot bamboo (no Inkpaws building has one today, so this needs a TimberCommons-using mod or a test fragment), a Flowering, a few days | `held` stays the number of young plants, `heldAgain` rises when the modifier registers, young bamboo's growth stays within about 1.4 % per swap; the log line "were growing again and are held again" appears; no error |
| 13 | Ringtails through the festival | `events-ringtails-off` first launch, sampled hourly; and once with the working hours set to 16 or more, so the rest window reaches past 15.5 h | a Ringtail asleep in its rest window on the festival morning, at the square after it, no night post staffed that night; **with the long day: Ringtails at the square from 15.5 h** (the gathering clock), not in bed until 16 h |
| 14 | a wild grove, nobody harvesting | `-RequestJson proto\events\requests\events-wild.request.json` on a `pbevents2`-style copy (`-Variant proto\events\variants\crews`: seed 2 days, rest 1.5 days). 8 shoot bamboo on marked tiles, 16 wild, no farm | `raw.plants`, hour by hour. Before: `PandabornShootBamboo.Inkpaws` grown 8, `... (wild)` grown 16. In flower (from the first sample after 1.2 h): `PandabornShootBambooInFlower.Inkpaws` grown 8, `... (wild)` grown 16. Over the last seed day (25 h to 49 h after the Flowering): the wild twins go one by one and `PandabornShootBamboo.Inkpaws (wild)` young rises to 16, `reseeded` 16, no dead wild twin left; the 8 marked twins end as `dead` 8 (no farm to plant over them). `held` 16 until the rest ends, then the seedlings' growth moves (`young` list). Log: "16 wild plants reseeded their tiles". 0 own errors. Shots `ev_w_*`: the grove before, in flower, as seedlings, growing |
| 15 | a wild grove in reach of a farm | `proto\events\requests\events-wild-farm.request.json`, same copy. 8 marked and 24 wild shoot bamboo round a staffed Efficient Farmhouse | seed in store rises; at the end `reseeded` + (wild twins cut by the farmers) = 24, `PandabornShootBamboo.Inkpaws (wild)` young = `reseeded`, no seedling where a twin was cut; the marked field is replanted from its marks as in `events-crews-3` |
| 16 | a fault is this game's | `events-fallback` (`simulate-missing-member`), then in the same launch a second game (the harness's `then`) | the feature report of the first game lists all three reasons in one line ("no day off ...; no fireworks ..." for Festival); the reload with the modules forced off, and a later clean launch, do not carry them |

After 3 and 4, write the counts and the shots into Results and close "The look of the festival".

### What a two-district scenario needs

Two halves, by owner.

**The harness** (`src/devharness`, the scenarios lane): today `GameDriver.PlaceBuildings` takes
`AllDistrictCenters.FirstOrDefault()` as the anchor of every building and `ConnectWithPaths` lays paths from that one
centre's doorstep. It needs:

1. **A second district centre.** A `buildings` entry such as `{ "template": "PandabornVillageHall.Inkpaws", "district": 1,
   "offset": [40, 0, 0], "connect": false }`: placed finished, far enough from the first that no path of one reaches the
   other (the Village Hall is the Inkpaws' only template with `DistrictCenterSpec`; whether a second one can be placed
   from data alone is the first thing to find out), and **not** joined to the first centre by `connectPaths`.
2. **Buildings that belong to it.** `"district": 1` on later entries: their offsets are taken from that centre's
   entrance (`relativeTo: districtEntrance` of district 1) and their paths are laid to that centre's doorstep only.
3. **The report**: `placedBuildings[].district`, `paths` per district, and "could not test" when the second centre
   found no level ground or its buildings are not in its district (`DistrictBuilding.District` of each).

**The probe** (`proto/events`, this lane; written on 2026-11-25, compiled, not run): `"district": n` (the n-th finished
district centre, 0 the first) on `stock` (into that centre's store), `spawnAdults` (on that district's roads; the game
assigns them by where they stand) and `callFestival` (at that district's first finished square); `square:n` as a shot
target; and in every sample `festivalDistricts`: per district name its colonists, how many have the day off, how many
are working, who attended, the festive average, and for each of its squares whether it hosts, its slots, its lanterns
aloft and the status line its panel would show.

The request the run needs once the harness can do 1 to 3 (the `events` part works today):

```json
"buildings": [ "PandabornFestivalSquare.Inkpaws", "SmallWarehouse.Inkpaws",
               { "template": "PandabornVillageHall.Inkpaws", "district": 1, "offset": [40, 0, 0], "connect": false },
               { "template": "PandabornFestivalSquare.Inkpaws", "district": 1 },
               { "template": "SmallWarehouse.Inkpaws", "district": 1 } ],
"events": {
  "stock": { "Water": 400, "PandabornPaperLantern": 40, "PandabornSteamedShoots": 70, "PandabornPickles": 70, "PandabornSteamedRice": 70 },
  "actions": [
    { "atRunHour": 0.1, "do": "spawnAdults", "count": 8, "district": 1 },
    { "atRunHour": 0.2, "do": "stock", "district": 1, "goods": { "Water": 300, "PandabornSteamedRice": 60 } },
    { "atRunHour": 0.3, "do": "callFestival", "district": 0 },
    { "id": "j1", "atRunHour": 0.6, "do": "jumpToHour", "hour": 23.4 },
    { "after": "j1", "delayHours": 1.6, "do": "jumpToHour", "hour": 15.0 } ],
  "shots": [ { "name": "d_a_dusk", "day": 1, "hour": 16.5, "select": "none", "focus": "square:0", "zoom": 0 },
             { "name": "d_b_dusk", "day": 1, "hour": 16.7, "select": "square:1" } ] }
```
