# Events dev copies and probe (dev only, never shipped)

Tests the Lantern Festival and the Great Flowering (`src/code/Pandaborn.Festival`, `src/code/Pandaborn.Flowering`; design and
results in `docs/tech/events.md`) **through the real module path**, without depending on the shared install's switches.

## What `build.ps1` makes

1. **The data**: `catalogue/` is copied to `E:\PandabornDev\build\proto\events-catalogue` with `rules.toml [modules]`
   Festival, Flowering and Water switched on (the Kitchen and rice flour, needed for seed cakes, are gated with Water), and
   generated with `src/gen/generate.py --catalogue ... --out E:\PandabornDev\build\proto\events-gen\PandabornFactions`.
   This is exactly what the content lane ships when it flips those switches; nothing here carries data of its own.
2. **The copy**: `proto/foundation/build.ps1 -Name <Name>` (the code lane's dev-copy route) mirrors the installed faction and
   adds the current `src/code` build: bootstrap, Specs, Core and every module in `modules.txt`, so Festival and Flowering
   load through the bootstrap's API check and report through the feature registry. Manifest Id
   `JigglyPanda.PandabornFactionsDev`. `-DevSwitch` writes its `pandaborn.dev.txt`.
3. The generated data is laid over the copy, the meshes of every adopted model are copied in, and the `-Variant` fragments
   (`*.fragment.json` merged, other files copied) are applied: `variants/test` (Flowering seed 2 days, rest 1.5 days; the
   lumberjack as a stand-in pump crew) by default, `variants/crews` (the same timings; the farmhouse as the crew).
4. **The probe** (`src/`) is its own mod, `E:\PandabornDev\build\proto\events-probe` (`JigglyPanda.PandabornProtoEvents`,
   requires the copy), compiled against the copy's own Core, Specs, Festival and Flowering. Everything that touches a
   module sits in `FestivalProbe`/`FloweringProbe` and runs only when that module's assembly is loaded, so the probe also
   runs when a module is forced off. `-NoProbe` keeps the existing probe (build further copies while a run uses it).

Never rebuild a copy or the probe while a run that uses it is in the game.

## Runs (Plains: the harness's paths connect there)

```powershell
powershell -ExecutionPolicy Bypass -File proto\events\build.ps1                         # pbevents + probe
powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Plains `
    -RequestJson tests\scenarios\events\events-main.request.json `
    -ExtraMods E:\PandabornDev\build\proto\pbevents,E:\PandabornDev\build\proto\events-probe `
    -OnlyMods JigglyPanda.PandabornFactionsDev -SaveAndReload -ReloadSeconds 130 -TimeoutSeconds 1500 -WaitForGameSeconds 10800
```

| Scenario | Copy (`build.ps1 -Name ... -DevSwitch ...`) | What it covers |
|---|---|---|
| `events-main` | `pbevents` | auto-call, Grand Festival day, show, festive, Tradition, mid-show save and reload, drought call at 23:00, seed harvest and cakes, the rest |
| `events-crews` | `pbevents2 -Variant proto\events\variants\crews` | a crew working through the festival, replanting after the rest, dusk shots |
| `events-fallback` | `pbevents-fb -DevSwitch 'simulate-missing-member: Festival.RootBehaviors, Festival.Fireworks, Flowering.GrowthHold'` | the three fallbacks; the probe then writes `force-off: Festival, Flowering` so the reload loads the mid-event save with both modules off |
| `events-backon` | `pbevents-on -DevSwitch 'force-off: Festival, Flowering'` | a save carrying mid-festival and mid-flowering state written while both were off, loaded with both on |
| `events-ringtails-off` | `pbevents-rt` | a Ringtail family; the reload has `force-off: Ringtails` on festival day |

The probe writes `events.json` (`events_reload.json` after a reload) every in-game hour: events, actions and their results,
hourly samples (a module-free `raw` block: every character's running behaviour, who is working where, bamboo by template,
goods in store; the festival block: phase, show, lanterns, bursts, sounds, attendance, festive and grand need, Tradition,
locked decorations, what each colonist is doing; the Flowering block: phase, twins, seed, held seedlings), the player
messages, and the screenshots `ev_*.png`.

Request keys (`events`, and `events.reload` after a reload): `stock`, `fields`, `actions`, `shots`. Actions: `announce`,
`flowerNow`, `setSetting`, `callFestival`, `autoCall`, `resetCycleRule`, `setTradition`, `stock`, `seedlings`, `setRecipe`,
`jumpToHour`, `startDrought`, `writeDevSwitch` (the running copy's `pandaborn.dev.txt`, for the next launch), `fakeMidEvent`.
Times: `atRunHour`, `day` + `hour` (day index from the run's first day), or `after` (an earlier action's `id`) +
`delayHours`, which survives time jumps.

`tools/flowering_fair.py`: the colony-model runs behind the 9-day rest (`docs/tech/events.md`, section 5).
