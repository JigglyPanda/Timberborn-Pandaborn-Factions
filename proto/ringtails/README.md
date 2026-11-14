# Ringtails prototype (dev only, never shipped)

Go/no-go prototype of a second colonist kind for the Inkpaws faction: **Ringtails** (red pandas). Results and the
verdict are in [docs/tech/two-peoples.md](../../docs/tech/two-peoples.md), section "Prototype results".

Manifest Id `JigglyPanda.PandabornProtoRingtails`; requires `JigglyPanda.PandabornFactions`. Built to
`E:\PandabornDev\build\proto\ringtails`; it is only ever installed for a test run (`run_game_test.ps1 -ExtraMods`).

## What is in it

| Piece | Where | Kind |
|---|---|---|
| Ringtail adult and kit templates (hidden: in no template collection) | `mod/Characters/Pandaborn/Ringtail*.Inkpaws` (generated) | Data |
| Worker type `PandabornRingtail` (ignores working hours) | `mod/WorkerTypes/Pandaborn` | Data |
| Ringtail-only Courier Loft (hauling post) and Forager's Nest (gatherer flag), Loft (home) | `mod/Buildings/Pandaborn/Ringtails` (generated), collection `Buildings.PandabornRingtails` appended to the Inkpaws faction | Data |
| Save fallback alias: the Inkpaw templates answer to the Ringtail names | `mod/Characters/Pandaborn/Inkpaw*.Inkpaws` (merge) | Data |
| Outfits for the Ringtail worker type | `mod/WorkerOutfits/Pandaborn` (generated) | Data |
| Feature switch, factory, save/load registration | `src/RingtailService.cs` | Code, 1 private field |
| Day rest (sleep through the morning) | `src/RingtailRestRootBehavior.cs` | Code, 1 private field |
| Coat | `src/RingtailCoat.cs` | Code |
| Kit grows into a Ringtail adult | `src/RingtailGrowth.cs` | Code |
| Housing rule (Ringtails end up in lofts) | `src/LoftHousingRule.cs` | Code |
| Test probe (spawn, hourly log, panels, screenshots) | `src/Dev/*` (inert without a harness request) | Dev code |

## Build and test

```powershell
python proto\ringtails\tools\derive.py                    # regenerate the blueprint copies (after a game update)
powershell -ExecutionPolicy Bypass -File proto\ringtails\build.ps1
powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -InGameDays 3 -Speed 3 `
    -ExtraMods E:\PandabornDev\build\proto\ringtails -RequestJson proto\ringtails\test\gate.request.json `
    -SaveAndReload -ReloadSeconds 150 -TimeoutSeconds 1500
python proto\ringtails\test\analyze.py E:\PandabornDev\build\test\<run id>
```

The probe writes `ringtails.json` (hourly samples) and `rt_*.png` (panels and night shots) next to `result.json`.
