# Playtests: a scripted colony living for weeks

**Status: closed on 2026-11-25 by the docs lane, unfinished.** The playtest lane was stopped at the pause on
2026-11-14 and never reported: the sections per scenario that this page promised were never written. What follows
is the lane's own description of its driver (unchanged), and then "What the playtests established" and "What
stopped them", written from the run folders and from `docs/tech/balance.md`, whose second pass is the only analysis
these runs ever got. The runs still owed are in `docs/tech/needs-game-run.md` (ids B1 to B13, N2, N15, R1, R2).

Original status line: in progress, 2026-11-14. Lane: playtest. Every number on this page was measured in a running game by the dev
harness's scripted colony (`src/devharness/Playtest`), unless it is marked as the model's (`docs/tech/balance.md`).

## How the colony is played

The driver plays a build order the way a player would, with the game's own services:

| A player... | The driver |
|---|---|
| picks a spot with the building tool | scores cells around an anchor (the district center or an earlier building) by a rule (`any`, `nearWater`, `moist`, `dry`, `trees`, `bushes`), then asks the game's own placement check (`PreviewPlacer`, as the tool does) |
| places a construction site | `ConstructionFactory.CreateAsUnfinished`: the colony's builders fetch the real materials and build it |
| unlocks with science | waits until the points are there, then `BuildingUnlockingService.Unlock` (spends them), as the unlock button does |
| draws a path | lays finished `Path` tiles (the game places paths finished too) from the entrance to the connected network, over level ground, around fields; through trees only when the step allows it, and then the trees are marked for cutting and the tiles are laid once the lumberjacks have cleared them |
| marks a field / a grove / trees to cut | `PlantingService.SetPlantingCoordinates` after `PlantingAreaValidator.CanPlant` and the soil check (moist or dry); `TreeCuttingArea.AddCoordinates` on the trees nearest the flag, or on a planted grove |
| sets a recipe, workers, priority, stockpile good, working hours | `Manufactory.SetRecipe`, `Workplace.Increase/DecreaseDesiredWorkers`, `WorkplacePriority` / `BuilderPrioritizable`, `SingleGoodAllower.Allow`, `WorkingHoursManager.WorkedPartOfDay` |
| reacts to the colony | every step can wait on a day, an hour, other steps, finished buildings, stock above/below a level, population, science, free beds, homeless, unemployed, the weather or a coming hazard; a step can repeat (e.g. "another home whenever fewer than two beds are free") |

It needs no mouse, keyboard or window focus (it runs on the hidden test desktop).

What it cannot do like a human: rebuild or move something that went wrong, demolish, use stairs or build across
levels (routes stay on the district center's level), lay power shafts (so no powered chains: gristmill, bakery, gear
workshop with power, paper mill), notice a problem it was not told to watch for, or read the map's intent (a human
sees "the river is over there"). Where that matters it is said below.

Telemetry, per dawn, in `<run>/playtest/daily.jsonl`: population by age, births, grown-ups, deaths with the game's own
death message and the needs at their minimum, every good's available stock, total stock, capacity and the previous
day's production and consumption (the game's own goods sampler), every need's average and the number of colonists
critical and below warning, wellbeing average / median / histogram, employed, unemployed, vacancies, beds, homeless,
each workplace's worker time by running behaviour and its status texts ("No available workers", "isn't connected",
"Lack of resources"...), unfinished construction sites and their material/build progress, every plant kind alive /
grown / dying / dead, the weather and cycle, science, working hours, game speed and real seconds per day, and which plan
steps are blocked and on what. Events (placements, unlocks, finishes, deaths) in `events.jsonl`; overview renders at
dawn and night every few days. `tools/playtest_report.py` turns runs into `verdict.md` and charts.

Scenarios: `tests/scenarios/playtest/` (README there).

## Game speed and real-time cost

Measured on this machine (RTX 5070 Ti; 13 colonists, small colony):

| Speed | Real seconds per game day |
|---|---|
| 7 | 66 |
| 30 | 17–30 (more while the driver searches for a hard spot) |
| 60 | 18 (CPU-bound: no faster than 30) |

The game ran stably at 30 and 60 (no errors, plans executed). 30 is the playtest speed. Workplace sampling every half
game hour still lands several samples per worker per day at that speed.

## What the playtests established

Thirty-one runs named `pt-*` are in `E:\PandabornDev\build\test` (2026-11-14, 06:51 to 19:12). Most are driver
development. The ones that count were played on the map **Meander**, at speed 30, with only this mod enabled, on
the build installed that day (no Water, Festival or Flowering; a 16-hour day throughout).

| Runs | Plan | Days | Use |
|---|---|---|---|
| `pt-ft-base-m2`, `-m3`, `-m4`; `pt-ink-std-m1`, `-m3` | standard, Normal | 41 | Trustworthy for the first six days hour by hour, consumption, pump, inventor and lumberjack rates, first-crop days, stores before a drought, the wellbeing of a small village |
| `pt-ft-care-m1`, `-m2`, `-m3`; `pt-ink-care-m1`, `-m3` | careless (no water storage, one crop, three homes), Normal | 31 | Trustworthy for one question: does a careless start survive the first drought |
| `pt-ft-hard-m1`; `pt-ink-hard-m1`, `-m2` | Hard | 31 | Worst cases: where an unprepared Hard start dies and of what. Their FAIL verdicts are the colony dying, not a fault |
| `pt-ft-base-m1` | | | Discard: three colonists died homeless, the mill step never ran |
| `pt-ft-base-1`, `-2`, `pt-ftb-dev1` to `-dev5`, `pt-smoke-*`, `pt-survey-*` | on Plains | | Discard: driver development; no adults left by day 8 to 11 |
| `pt-ft-base-m5`, `pt-ink-std-1`, `-m2`, `-m4`, `pt-ink-care-m2` | | | Discard: no telemetry (the last two were cut off by the pause) |

**Measured, and used to calibrate the balance model** (`docs/tech/balance.md`, "Calibration"):

| Quantity | Measured in game |
|---|---|
| Logs a lumberjack cuts a day (pine, wellbeing under 5) | 16.9 |
| Water a pump worker makes a day | 40.2 (the recipe says 46: pumps run at 85%) |
| Science an inventor makes a day | 16.3 |
| Food a colonist eats a day | 2.57 |
| Water a colonist drinks a day | 2.10 |
| Shoot bamboo alive after a five-day drought | 45% (52 of 116 plants, two runs) |
| Crop tiles one farmer keeps harvested | 35 |
| First crop | shoots on day 5 to 6, carrots on day 6 to 7 |

**The two comparisons the lane charted** (`tools/playtest_report.py`; the charts are kept beside this page. Which
runs each was drawn from is not recorded; by their time, 19:12, most likely the `-m3` careless pair, and
`pt-ft-hard-m1` with `pt-ink-hard-m2`):

* [playtest/careless.png](playtest/careless.png), careless Folktails against careless Inkpaws, 31 days. In the first
  drought (days 15 to 17) up to eleven Folktails were critically hungry or thirsty and the average wellbeing fell
  below zero; no Inkpaw was critical at any time. The Inkpaws had about 120 water in stock before the drought and
  the Folktails none. Balance.md reads this as a fault, not a success: the shelf rule had made the Inkpaws' first
  water pump a 146-water tank ("a careless Inkpaws colony lost nobody in the first drought where the same script
  lost ten of thirty-nine Folktails"). The pump shelf was cut back to vanilla size on 2026-11-25; run B1 repeats
  the pair. Both colonies shrink after day 15 (13 to 7 or 8 Folktails, 13 to 9 Inkpaws); the chart does not say
  of what, and each run's `playtest\daily.jsonl` has the game's death messages.
* [playtest/hard.png](playtest/hard.png), Hard, 31 days. Both colonies ran out of water in the first drought (days
  7 to 12, with 27 and 56 water in stock when it began) and then out of food; the chart's count of colonists
  critical in hunger or thirst peaks at 26 for each. The
  Folktails colony was dead by day 18. The Inkpaws colony fell to 9, recovered its food once (to 88 on day 20), ran
  out again and was down to 2 on day 31. The scripted plan does not stock up for a Hard drought, so this shows
  where an unprepared start dies, not whether a prepared one lives. Run B2 repeats it; R2 needs a plan that
  prepares.

Other things the runs showed, as balance.md records them: the Inkpaws' first shoots come about a day before the
Folktails' first carrots; Inkpaws poles from bamboo piled up unused (244 by day 35, with logs at zero), because logs,
not poles, limit building in these runs; hammocks were shared by three to four colonists each on a 16-hour day.

## What stopped them

1. **The driver stops marking trees.** It marks the trees nearest the lumberjack flag once; when those are cut,
   logs fall from about 33 a day to between 0 and 8, homes stall and nobody is born. No run got past 20 colonists or
   told us anything about the game after the first week of building: "13 to 18 colonists in 41 days" is the driver,
   not the faction. Nobody owns the fix (`src/devharness/Playtest`). Until it is made, every mid-game and late-game
   number in balance.md is the model's alone (run B5, and through it B7 and B10).
2. **It cannot lay power shafts**, so the Folktails colonies never made a plank and built nothing that needs one,
   while the Inkpaws cut poles from bamboo with no mill. The faction comparison is fair for water, food and the
   first drought, and unfair for anything built after the first week.
3. **It cannot place a pump on Plains.** There the scripted player fails with "no spot: no level path to the
   network" and the colony dies of thirst. That is why every Plains run is discarded above, and why the catalogue
   lane's "played" proof of phase 5 failed and was never reported: `p5-played-3` (the Inkpaws on a 12-hour day with
   a bonus watch: 0 adults at the end) and `p5-folktails-3` (the same check that the bell leaves Folktails alone).
   Their request files are sound (`tests/scenarios/catalogue/phase5_played_*.json`); run them on Meander (N2, B4).
4. **Every colony stayed on a 16-hour day**, so the afternoon bell was never exercised by a living economy (B4).
5. **None had a Teahouse with tea, a festival, an ox, flumes or Ringtails at work**: the build of that day could
   not, or the plan did not ask (B3, B7, B8).
6. **The pause.** The last two runs (`pt-ft-base-m5`, `pt-ink-std-m4`) were in the queue when all agents were
   stopped, and the lane's findings were never written.

## Where each open question went

| Question | Run in `docs/tech/needs-game-run.md` |
|---|---|
| A careless start after the pump shelf was cut back | B1 |
| Hard, and a plan that prepares for it | B2, R2 |
| The first flume, the first poles from bamboo, the first festival, by day | B3 |
| A 12-hour day with a real economy; Folktails untouched by the bell | B4, N2 |
| Anything past day 20 and 20 colonists | B5 (needs the driver fix) |
| How much of a day is off duty | B6 |
| Tea in a living village | B7 |
| The tutorial followed by the scripted player | N15a, N15b |
| Three days and forty-one days on every difficulty, for the release | R1, R2 |
