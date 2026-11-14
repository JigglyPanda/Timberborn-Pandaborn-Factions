# Playtest scenarios

Scripted colonies played by the dev harness (`src/devharness/Playtest`, request key `playtest`). Each file is a
`-RequestJson` for `tools/run_game_test.ps1`; the build order format is documented at the top of
`src/devharness/Playtest/PlaytestDriver.cs`. Findings: `docs/tech/playtest.md`.

| File | What it plays |
|---|---|
| `folktails-baseline.json` | The reference: a standard Folktails opening and mid game (hand-written) |
| `inkpaws-standard.json` | The same plan for the Inkpaws, following DESIGN.md's first two hours |
| `inkpaws-hard.json` | The same on Hard, water storage and the second staple brought forward |
| `inkpaws-careless.json` / `folktails-careless.json` | New-player mistakes: no water storage, one crop, three homes |
| `inkpaws-pure.json` | The Inkpaws plan without the seven-pole workaround (does a colony ever get its first pole?) |
| `dev-smoke.json` | Driver development: a few buildings and a speed ladder |

The Inkpaws and careless files are generated from `folktails-baseline.json` by `make_scenarios.py` so the quality of
play stays equal; edit the baseline or the script, not the generated files.

Run one (Normal, Plains, only this mod enabled; the scenario's `speed` overrides `-Speed`):

```powershell
powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Folktails -Map Plains -GameMode Normal `
  -InGameDays 40 -RunSeconds 7200 -TimeoutSeconds 8000 -WaitForGameSeconds 10800 -NoBatchControl `
  -OnlyMods JigglyPanda.PandabornFactions -RequestJson tests\scenarios\playtest\folktails-baseline.json -RunId pt-ft-base
E:\PandabornDev\tools\venv\Scripts\python.exe -I tools\playtest_report.py E:\PandabornDev\build\test\pt-ft-base
```

Several runs side by side: `playtest_report.py <run> <run> ... --labels a,b,...`.
