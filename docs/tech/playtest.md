# Playtests: a scripted colony living for weeks

Status: in progress, 2026-11-14. Lane: playtest. Every number on this page was measured in a running game by the dev
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

(Sections per scenario, problems and proposals follow below as the soaks finish.)
