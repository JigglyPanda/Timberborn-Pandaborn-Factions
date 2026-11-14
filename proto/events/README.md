# Events dev mod (dev only, never shipped)

Proves the Lantern Festival and the Great Flowering (`src/code/Pandaborn.Festival`, `src/code/Pandaborn.Flowering`; design
in `docs/tech/events.md`) in game before the catalogue carries their data. Manifest Id `JigglyPanda.PandabornProtoEvents`,
requires the faction mod. Built to `E:\PandabornDev\build\proto\events`; the test script junctions it for a run only.

## What it is

* `Scripts\PandabornProtoEvents.dll`: the two modules' **sources from `src/code`** (linked, not copied), the test probe
  (`src/Dev/EventsProbe.cs`, inert unless the harness request has an `events` section) and a dev starter
  (`src/Dev/EventsDevStarter.cs`). The game loads it as a normal mod DLL after the faction mod's bootstrap (this mod
  requires the faction mod, so it starts later), so the modules run on the installed `Pandaborn.Core` and, since the
  shared build carries `EventSpecs.cs`, on the installed `Pandaborn.Specs` too (`build.ps1` checks the installed
  `Pandaborn.Specs.bin` and compiles the spec records in only if they are missing; two copies would be a duplicate spec
  name). This bypasses the bootstrap's API check: dev only.
* `mod/`: the data the catalogue is asked for (docs/tech/events.md, section 8), merged onto the generated templates by
  same-path files: the festival and Flowering rules and the goer spec on `InkpawAdult.Inkpaws`, the goer spec on the child,
  the Festival Square turned from a warehouse into an attraction (Campfire need) with `PandabornFestivalSquareSpec`,
  Tradition on three decorations, the flowering spec on the two bamboos, and the twins' collection entry.
  **Test fixture:** `KeepWorkingTemplates` also lists `LumberjackFlag.Inkpaws`, so the test map (which has no reliable
  pump water) shows a crew that keeps working through the festival.
* `tools/derive.py`: writes the two "in flower" twins from the installed faction mod's bamboo blueprints (build artefacts).
* `tools/flowering_fair.py`: the colony-model runs behind the 9-day rest (docs/tech/events.md, section 5).

## Build and test

```powershell
powershell -ExecutionPolicy Bypass -File proto\events\build.ps1
powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Diorama `
    -RequestJson tests\scenarios\events\events-main.request.json -ExtraMods E:\PandabornDev\build\proto\events `
    -OnlyMods JigglyPanda.PandabornFactions -SaveAndReload -ReloadSeconds 160 -TimeoutSeconds 1500 -WaitForGameSeconds 10800
# fallbacks, then the modules forced off in a save made mid-festival:
$env:PANDABORN_DEV = 'simulate-missing-member: Festival.RootBehaviors, Festival.Fireworks, Flowering.GrowthHold'
powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 ... -RequestJson tests\scenarios\events\events-fallback.request.json -SaveAndReload -ReloadSeconds 60
# Folktails unchanged with the mod on:
powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Folktails ... -RequestJson tests\scenarios\events\events-folktails.request.json -RunSeconds 45
```

Never rebuild while one of these runs is in the game: the build folder is the mod the game is reading.

The probe writes `events.json` (`events_reload.json` after the reload) into the run folder every in-game hour: events
(stock, fields, actions with their results), hourly samples (festival phase, show, Tradition, lanterns and bursts launched,
what every colonist is doing, festive need, working count; Flowering phase, twins alive and dead, seed on plants, cut and in
store, held seedlings and their growth; a module-free `raw` block of every character's behaviour and every bamboo), the
player messages, and the screenshots `ev_*.png` (the probe selects the square, a bamboo or a colonist so its panel shows).

Request keys (`events`, and `events.reload` for the reload launch): `stock`, `fields` (spawn grown or young plants near a
placed building, mark them, add a cutting area), `actions` (`announce`, `flowerNow`, `callFestival`, `resetCycleRule`,
`setTradition`, `setSetting`, `autoCall`, `stock`, `seedlings`, `jumpToHour`, `writeDevSwitch` for the next launch), `shots`.
Times: `atRunHour` (in-game hours since the probe started) or `day` + `hour` (day index from the run's first day).
