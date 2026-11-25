# Balance model (second pass)

Small Python that answers the balance questions in [`docs/tech/balance.md`](../../docs/tech/balance.md) from the
numbers the game really reads. It needs no game and runs in a few seconds.

```powershell
E:\PandabornDev\tools\venv\Scripts\python.exe -I tools\balance\run.py all      # every question
E:\PandabornDev\tools\venv\Scripts\python.exe -I tools\balance\run.py q2 q4    # chosen ones
```

Each question prints Markdown and writes it to `tools/balance/out/<name>.md`.

## Where the numbers come from

| Source | Read by | What |
|---|---|---|
| `E:\PandabornDev\reference\Blueprints` | `data.py` | Vanilla: every recipe, good, need, plant, building, wellbeing tier, game mode |
| `E:\PandabornDev\build\gen\PandabornFactions` | `data.py` | The Inkpaws as the last `tools/pandaborn.ps1 generate` wrote them, merged over vanilla as the game merges them (same-path files, then the faction's blueprint modifiers) |
| `E:\PandabornDev\build\test\pt-*` | `playtest.py` | The scripted colony playtests: calibration and the careless and Hard outcomes |

So after a catalogue change: `tools\pandaborn.ps1 generate`, then `run.py all`, and every table moves. Nothing is typed
in twice. `PANDABORN_VANILLA`, `PANDABORN_GEN` and `PANDABORN_TEST` override the three folders.

Three constants are calibrated against the playtests and marked `CALIBRATED` in `mech.py` (time at the post, the
pump's efficiency, food and water per colonist). The assumptions that are not measured are marked `ASSUMED` in
`day.py` (walking per attraction visit, time spent on meals, how well seats are used).

## Files

| File | What it is |
|---|---|
| `data.py` | `Game("Folktails" \| "IronTeeth" \| "Inkpaws")`: the blueprints, indexed |
| `mech.py` | A worker: speeds from wellbeing and the bell, loads, trips; one shift of each job; a workshop run action by action in the game's order |
| `day.py` | Hours off duty: sleep, meals, which rituals fit, how many colonists a building serves |
| `weather.py` | Drought and badtide lengths by occurrence; which plants live through them |
| `economy.py` | Chains: land, labour and science behind a good; the cheapest way to switch each need on |
| `playtest.py` | Reads the scripted playtests' telemetry |
| `questions.py` | One function per question (`calibrate`, `q1` ... `q11`) |
| `run.py` | Command line |

`whatif(game, needs=..., shelves=...)` in `questions.py` copies a game with changed numbers, to try a proposal before
it goes into the catalogue.

The first-pass model is `tools/sim` (it reads its own stat sheet, which the catalogue has since moved away from).
Its opening and population simulations are still the only ones we have; this folder does not replace them.

## Limits

* Workers are pooled per job; there is no map and no pathfinding. Distances are parameters (12 to 20 tiles).
* `day.py` is a time budget, not an agent simulation: it says whether the rituals fit, not who sits where.
* `economy.wellbeing_at` buys needs in order of science per wellbeing point. A player buys what they like.
* Material labour (`questions.material_days`) uses rough figures for scrap metal, resin and extract.
