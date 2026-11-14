# Ringtails test probe (dev only, never shipped)

The Ringtails (red pandas, the Inkpaws' second people) ship in the faction mod: code in `src/code/Pandaborn.Ringtails`
and `src/code/Pandaborn.RingtailsFallback`, data generated from the catalogue (templates, worker type, outfits, night
posts, Moon Loft, name pool). Design, results and history: [docs/tech/two-peoples.md](../../docs/tech/two-peoples.md).

This folder used to be the go/no-go prototype and carried its own copy of the data; since the content lane adopted
§18.1 into the catalogue (phase 3) it is only the **test probe**: a dev mod (`JigglyPanda.PandabornProtoRingtails`,
built to `E:\PandabornDev\build\proto\ringtails`) whose `Scripts\` DLL is inert without a harness request. It reaches
the module by reflection (`src/Dev/ModuleBridge.cs`), so it has no compile-time reference to it.

## Build and test

```powershell
powershell -ExecutionPolicy Bypass -File proto\ringtails\build.ps1
# against the installed faction build:
powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -InGameDays 2.4 -Speed 3 `
    -ExtraMods E:\PandabornDev\build\proto\ringtails -RequestJson proto\ringtails\test\ui.request.json -TimeoutSeconds 1500
# against a dev copy carrying code under test (proto/foundation/build.ps1 -Name rtdev):
    ... -DisableMods JigglyPanda.PandabornFactions -ExtraMods E:\PandabornDev\build\proto\rtdev,E:\PandabornDev\build\proto\ringtails
python proto\ringtails\test\analyze.py E:\PandabornDev\build\test\<run id>
python proto\ringtails\test\births.py E:\PandabornDev\build\test\<run id>
```

The probe writes `ringtails.json` (hourly samples: colonists, workplaces, lofts and their nursery state, player numbers,
UI and sound state) and `rt_*.png` (panels and night shots) next to `result.json`.

## Request section `"ringtails"`

| Key | Meaning |
|---|---|
| `place` | templates (or `{template, finished}`) placed on the district's terrace, then joined with paths (`connectPaths`, default on) |
| `stock`, `storage`, `recipes`, `workingHours` | district-center goods; stockpile goods; workshop recipes; the slider |
| `spawn`, `spawnKits`, `kitGrowth` | Ringtail adults/kits created at once (dev only; the game itself gets them from the Moon Loft) |
| `laterPlace`, `laterDelete`, `laterGoods` | timed placement, demolition, goods (`"set": {"Water": 0}` empties every inventory of it; a positive number gives the district center that much) |
| `shots` | `{name, day, hour, select}`: select `ringtail`, `ringtailWorkplace`, `inkpaw`, `inkpawWorkplace`, `loft`, `districtCenter` or `none`, centre and capture |
| `afterReload` | on any timed item or shot: only in the reload launch of a `-SaveAndReload` run (day 0 = its first day); timed items without it run only in the first launch |
| `devSwitchNextLaunch` | dev switch lines for the reload launch (e.g. `force-off: Ringtails`) |

Requests in `test/`: `ui` (clock arc, sun and moon marks, clapper, "no room"), `breeding` (ten lofts on Plains, the
population valve, save and reload, the thirst drain), `module`, `soak`, `forcedoff`, `folktails`, `workshops*`,
`throughput` (phase 2; see two-peoples.md §18).
