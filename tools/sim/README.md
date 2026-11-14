# Colony model

A small, readable model of a Timberborn colony, used to balance the Inkpaws against vanilla Folktails. It needs no
game: standard library only (numpy is allowed but not needed). Every rule comes from
[`docs/tech/game-mechanics.md`](../../docs/tech/game-mechanics.md); findings are in
[`docs/tech/balance.md`](../../docs/tech/balance.md).

```powershell
E:\PandabornDev\tools\venv\Scripts\python.exe tools\sim\run.py all          # everything, about a minute
E:\PandabornDev\tools\venv\Scripts\python.exe tools\sim\run.py q2 q5        # chosen scenarios
```

Each scenario prints Markdown and writes it to `tools/sim/out/<name>.md`. `sheet` also writes
`out/statsheet.json`, the proposed numbers as one entry per catalogue item for the catalogue generator.

| Command | Question |
|---|---|
| `calibrate` | Reproduce vanilla Folktails ratios from the mechanics reference |
| `q1` | The opening: shoot bamboo timing and yield, carrier strength, builders vs logs |
| `q1drought` | First droughts on Normal and Hard; plants that pause vs plants that die; dry-day tolerances |
| `q2` | The afternoon bell: rested-bonus curve per job, rituals and leisure time, the 12/12 balance |
| `q3` | Food ladder: land, labour and science per food and per wellbeing point |
| `q4` | Water: drought stores, tea, dew collector, paddies, cistern tap |
| `q5` | Ringtails: what each night post adds, lifting capacity, best mix |
| `q6` | Population: growth to 50 and 100, drought death spiral |
| `q7` | Great Flowering reserves and seed; Small Festival timing and payoff |
| `q8` | Late game: material labour, monuments, the wonder, Wooden Oxen vs bots |
| `sheet` | The proposed stat sheet as tables and JSON |

## How it works

| Module | What it is |
|---|---|
| `pandasim/vanilla.py` | Vanilla numbers only, each copied from the reference or a blueprint |
| `pandasim/mech.py` | Wellbeing tiers, walking empty and loaded, loads per trip, a worker's context, the rested bonus, drought lengths |
| `pandasim/jobs.py` | One worker's shift: workshops simulated action by action in the vanilla order (produce, empty output, fill input), closed forms for farmers, gatherers, woodcutters, builders, haulers |
| `pandasim/needs.py` | A colonist's off-duty hours: food trips, attraction visits picked by the Appraiser score, bedtime rule |
| `pandasim/colony.py` | Hour-by-hour opening: every colonist's Hunger and Thirst, every marked tile, wild bushes, a build queue, builders, droughts |
| `pandasim/openings.py` | The Folktails and Inkpaws opening build orders |
| `pandasim/popsim.py` | Day-by-day population: births by the home rules, childhood, ageing with wellbeing, starvation, hazards |
| `pandasim/stats.py` | The proposed stat sheet; the model reads its numbers |
| `pandasim/scenarios.py` | One function per question |

Change a number in `stats.py`, run `run.py all`, and every table moves with it.

## Limits

* Workers are pooled per job; there is no pathfinding. Distances are parameters (15 tiles to a source, 6 to a field).
* The opening player follows a fixed build order and does not pre-stock for a forecast drought.
* The population model builds homes at a fixed rate (1 + 0.12 beds per adult a day); compare cases with each other,
  not with a particular player.
* Evaporation numbers come from simulation constants in `docs/tech/water.md`, not from a measured game.
