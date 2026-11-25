# Needs a game run: the one backlog

Written 2026-11-25 by the docs lane, on a day when no game could be started. It collects every in-game check that
any document, `FEATURE.md` or `CLAUDE.md` still owes, drops the ones a later run already settled (checked against
the 233 run folders in `E:\PandabornDev\build\test`, each with a `summary.json`), and adds the checks owed by the
balance decisions of 2026-11-25 (`docs/DESIGN.md` change log, `docs/tech/balance.md` "Proposed changes").

It also holds the game-run lists of the three reviews finished that day: the tooling review
(`docs/tech/tooling-review.md`), the second independent audit (`docs/tech/audit-2.md`) and the mod-compatibility
audit (`docs/reviews/2026-11-25-mod-compatibility.md`).

**Size:** 87 game runs and one screenshot session in 74 items, about 10 hours 45 minutes of game time (about 13
hours of wall clock with loading and builds). The first three blocks, which decide whether the test tooling can be trusted, whether the
build may be installed and whether it can crash, are 21 runs and about 1 hour 15 minutes of game time. Totals per
tier are at the end.

**Order:** the test tooling itself; the install gate; what crashes if wrong; proofs of new behaviour; other mods
alongside; balance runs; the release soak; cosmetic proofs last. Inside a tier the runs are in the order to run
them.

**Where things stand today (read this first).**

* The catalogue has all ten code modules switched on (`catalogue/rules.toml [modules]`: Bell, Names, Look, Words,
  Water, Ringtails, RingtailsFallback, Tutorial, Festival, Flowering). The build *installed* on 2026-11-14 does not
  have Water, Festival or Flowering. No staging folder with all ten has a gate file: the last gate that passed and
  was recorded is `gate-20261114-143547`, for a build without them. The second audit found the shared
  `E:\PandabornDev\build\gen` and `stage` folders stale as well: P3 rebuilds both, so never run G1 without P3.
* The test runner, the hold scripts and the gate were edited on 2026-11-25 after a reading review (467b7f5 and a
  second round), with no game to try them on. Tier 0 proves them before anything else is trusted.
* The gate does not yet test the code that gets installed: it builds its dev copy with a *fresh* build of
  `src/code` and the unfiltered `modules.txt`, not with the staged DLLs (tooling review, G1 there; a fix was in
  progress on 2026-11-25). Until `tools\pandaborn.ps1` is changed, run P3 and G1 back to back with no code commit
  in between, and compare the module list by hand (see G1).
* The owner's `Mods` folder was cleaned at the pause: the junctions `PandabornFactions`, `PandabornDevHarness` and
  `pbgate-*` are gone (their targets on E: are intact). `install` (G2) re-creates the faction's junction; every test
  run re-creates and removes the harness junction itself.
* Every dev copy in `E:\PandabornDev\build\proto` (`pbevents*`, `pbsky`, `rtdev`, `water*`, `pbgate-*`) was built
  from the build of 2026-11-14 and is stale. Rebuild a copy before using it; the commands below do.
* Changes made on 2026-11-25 with no game behind them: pump shelves, flume / gate / scoop-wheel science, the bell
  curve at 13, 14 and 15 hours, the Ringtails' rested bonus (new code), the Star Tower as a Ringtail night post,
  the Opera Stage as an ordinary attraction, wellbeing trims, the Wooden Ox recipe, pickles, festival numbers, and
  the rising-lantern rework (code ready, `pandabornattachments` bundle not rebuilt).

## Run order for a two-hour window

Everything in "Before any run" must already be done. Times are wall clock. Stop after any FAIL in steps 1 to 6 and
hand the run folder to the lane named in that item.

| Step | Item | What | Minutes |
|---|---|---|---|
| 1 | T1, T2 | The test runner after its edits: a plain run; then flags, an extra mod and a reload | 8 |
| 2 | G1 (with T7) | The install gate on the staged build: grid, water line with reload, scoop wheels | 25 |
| 3 | G2 | Install (no game) | 2 |
| 4 | C1 | Installed build alone: an Inkpaws game, then a Folktails game in the same launch | 7 |
| 5 | C2 | The same with all of the owner's mods, the Reskin included | 9 |
| 6 | C4 | A colony lived in for a day, saved and reloaded, counts compared | 15 |
| 7 | C5a | A save made with every module on, loaded with every module off | 10 |
| 8 | N1 | Ringtails' rested bonus: day builders against night builders | 9 |
| 9 | N2 + N5 | Bell curve at 12 to 16 hours; pump shelf size (one launch) | 8 |
| 10 | N3 + N4 + N13 | Star Tower by night, Opera Stage with visitors, a den finished overnight (one launch) | 12 |
| 11 | N10 | Rising lanterns at speed 1 and speed 3 (needs the rebuilt bundle, P1) | 12 |
| | | **Total** | **117** |

If there is time left: N6, C3, C5b, N7, N11, then B1. If P1 (the Unity rebuild) was not possible, skip step 11 and
run N6 instead. T3 and T6 need a person at the console and T4 and T5 need the owner: they are not in this list.

## Before any run (no game needed)

| Id | What | Command | Lane |
|---|---|---|---|
| P1 | Rebuild the attachments bundle with the reworked rising-lantern prefab, Windows and Mac. Needs Unity, so it could not be done on 2026-11-25 | `powershell -ExecutionPolicy Bypass -File src\unity\PandabornAttachments\build.ps1`, then the same with `-Mac` | Characters (bundle), events (prefab settings) |
| P2 | Add the `LanternRise` attachment to `PandabornFestivalSquare` in the catalogue (text of the entry: `docs/tech/ringtail-body.md` 8.7; the dev variant `proto\events\variants\sky` carries it meanwhile). The rework itself was committed on 2026-11-25 (code 8038a53, prefab and sprite c3b6a33, dev tools ef00de2); only the bundle (P1) and this catalogue line are missing | (one catalogue edit, after P1) | Catalogue |
| P3 | Build and validate the staged build | `powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 pin,generate,code,bundles,assemble,validate` (add `models` in front of `generate` only if anything under `art/models` or `src/pipeline/kit` changed) | Catalogue |
| P5 | Every build a player can end up with generates, assembles and passes the release rules: all modules on, the data-only build, and each module or family switched off (nine combinations; a tutorial stage that names a template one of them lacks would throw at the start of every game). Added to the build on 2026-11-25 (7822e6b) | `powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 code,combos` (one of them: `-Combo no-code`); the last combination built stays in `E:\PandabornDev\build\combos\stage\PandabornFactions` | Catalogue |
| P4 | Check nobody is playing and nothing holds the queue | `Get-Process Timberborn -ErrorAction SilentlyContinue` prints nothing; the files `E:\PandabornDev\build\test\HOLD` and `E:\PandabornDev\build\test\modstate.pending.json` do not exist | Whoever runs |

`assemble` (inside P3) refuses a `pandabornlook` bundle older than the last change of
`src/pipeline/sheet_regions.json` and plant meshes or a `pandabornplants` bundle older than the last change under
`art/plants`. If it refuses, take the newest bundles from `E:\PandabornDev\build\look\AssetBundles` and
`E:\PandabornDev\build\plants\AssetBundles`; if those are older too, a rebuild is owed (Blender and Unity).

## How to run and read a run

* Run every command from the repository root, in PowerShell. One game at a time: each run takes the mutex
  `Global\PandabornGameTest` and waits its turn, so commands can be started one after another without watching.
* The game runs on a hidden desktop. Never add `-Visible`, and never start Timberborn another way, while the owner
  is at the machine.
* Output: `E:\PandabornDev\build\test\<RunId>\`. Read `summary.json` first: `verdict` is `PASS`, `FAIL` or
  `ERROR`; `problems` says why; `logErrorsOurs` lists exceptions from our mods. Exit code 0 pass, 1 fail, 2 could
  not test (run it again). With `-SaveAndReload` the second launch writes into `<RunId>\reload\`.
* "Must see" names the file and the field. Look at the PNGs that are named.
* Two ways to load the faction. **Installed** (after G2): `-OnlyMods JigglyPanda.PandabornFactions`. **Dev copy**
  (code or data not installed, or a dev switch): build the copy, then
  `-DisableMods JigglyPanda.PandabornFactions -ExtraMods E:\PandabornDev\build\proto\<copy>`. Never enable a dev
  copy and the installed faction together: the same asset bundle twice crashes every game.
* Never rebuild a dev copy or a probe while a run that uses it is in the game.
* Items marked **SCENARIO TO WRITE** have no request file yet. The lane named there writes it (the nearest
  existing file to copy is given); the command is otherwise complete.

---

## Tier 0: the test tooling itself

From `docs/tech/tooling-review.md` ("Needs a game run"; reread that section first: a second round of fixes was in
progress when this was written). The runner, the hold scripts and the gate were changed without a game to try them
on. Until T1 and T2 pass, a FAIL anywhere below may be the tooling's. All take the real lock. Run them when the
owner is away, in the background, not from a shell call with a timeout.

| Id | Proves | Command | Must see | Game min | Needs |
|---|---|---|---|---|---|
| T1 | The fixes did not break a plain run (pid tracking, the new checks, the desktop handle) | `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Folktails -RunSeconds 30 -RunId t1-plain` | exit 0, `summary.json` PASS, no Timberborn process left | 1.5 | |
| T2 | Mod flags, an extra mod and two launches are all put back | `powershell -ExecutionPolicy Bypass -File proto\foundation\build.ps1` (after G2 this copies the new install; before it, add `-Source E:\PandabornDev\build\stage\PandabornFactions`), then `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -DisableMods JigglyPanda.PandabornFactions -ExtraMods E:\PandabornDev\build\proto\pbfoundation -SaveAndReload -RunSeconds 30 -RunId t2-flags-reload` | PASS for both launches; `modstate.restore.json` shows every value matching; afterwards no `E:\PandabornDev\build\test\modstate.pending.json`, no `Mods\pbfoundation`, no `Saves\PB_AutoTest_*` | 4 | |
| T3 | `-DuringHold` runs under a real hold and is refused under a stray `HOLD` file | Window 1: `powershell -ExecutionPolicy Bypass -File tools\game_test_hold.ps1`. Window 2, once it says "Holding": `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Folktails -RunSeconds 30 -DuringHold -RunId t3-during-hold` (must run); then `Remove-Item E:\PandabornDev\build\test\HOLD`. Then create a `HOLD` file by hand with no hold script running and repeat the second command: it must refuse; delete the file | first run PASS; second attempt refuses and starts no game | 1.5 | A person at two consoles |
| T4 | **Needs the owner at the PC.** The owner starts the game during a run: the run stops its own game only, restores the flags and waits | `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -OnlyMods JigglyPanda.PandabornFactions -RunSeconds 300 -RunId t4-owner-starts`; about 10 s after the console prints "hidden desktop ... pid", the owner starts Timberborn from Steam, looks at the mod manager (are the owner's mods shown on?) and closes the game | exit 2; two restores in the log; no `request.json` left; no test starting in the owner's window | 1 | **The owner**; after G2 |
| T5 | **Needs the owner at the PC.** The owner's launcher pauses the queue end to end | With a test queued: `powershell -ExecutionPolicy Bypass -File tools\play_timberborn.ps1 -NoLaunch`; the owner starts and closes the game | the queued test starts only after the owner's game has closed | 1.5 | **The owner** |
| T6 | Ctrl-C in the console during a run like T2 | T2's command again with `-RunId t6-ctrl-c`; press Ctrl-C once the game is up | the game dies, the flags come back (`modstate.restore.json`), the junctions go. A second Ctrl-C during the clean-up is expected to cut it short; then `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -RestoreModState E:\PandabornDev\build\test\t6-ctrl-c\modstate.json` | 1 | A person at the console |
| T7 | The gate leaves no registry litter (one `ModEnabled...pbgate-*` value per gate copy) | `reg query HKCU\Software\Mechanistry\Timberborn /f pbgate` before and after G1 | the same list before and after | 0 (it is G1) | With G1 |
| T8 | Install refuses while a game is open and works with the queue held by the caller | After G1: `powershell -ExecutionPolicy Bypass -File tools\game_test_hold.ps1` in a second window, then G2's command, then delete `E:\PandabornDev\build\test\HOLD` | install completes under the hold; with a game open it refuses | 0 (it is G2) | With G2 |

**If one fails:** the tooling lane (the author of `docs/tech/tooling-review.md`). If T2 or T6 leaves a mod flag
changed, undo it at once with `-RestoreModState <run>\modstate.json` and tell the coordinator: that is the owner's
machine left changed.

---

## Tier 1: the install gate

### G1. The install gate on the staged build

* **Proves:** the staged build loads an Inkpaws game with all ten modules; every placeable template can be placed
  *and finished* (two adopted-model crashes only showed at that moment); recipes run; three in-game hours on a
  speed ladder with no error from our mods. With Water shipped the gate also runs a flume line that crosses another
  on a Bridge Span into a spout and a paddy, saved and reloaded, and scoop wheels in a current with a cistern-tap
  loop and a dew collector, all on the catalogue's `.Inkpaws` templates. It also covers, for crashes only, every
  data change of 2026-11-25 (Star Tower as a night post, Opera Stage, Ox recipe, pickles, shelves, science costs,
  the bell's new curve points) and every Inkpaws tutorial stage (the game builds all stages when it loads).
* **Command:** `powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 gate`
  (it builds the dev copy `pbgate-<hash>` itself and starts three runs: `gate-<time>`,
  `gate-<time>-water_w4_inkpaws`, `gate-<time>-water_scoop_inkpaws`).
* **Must see:** the last line `gate: passed (run ...)`, and the file
  `E:\PandabornDev\build\stage\PandabornFactions.gate.json`. In the first run's `result.json`: `grid.complete`
  true and `grid.requested` about 170; in `foundation.json` `atLoad.units` lists all ten modules as `on`. Look at
  `night_PandabornSkyLantern.png` (the great lantern glows amber) and `screen_end.png`.
* **Time:** about 16 minutes of game (grid 4, water line with reload 5, scoop 7), 25 with builds.
* **Check by hand until the gate is fixed** (tooling review G1): the gate's dev copy carries a fresh build of
  `src/code`, not the staged DLLs. Compare `E:\PandabornDev\build\proto\pbgate-<hash>\Modules\modules.txt` with
  `E:\PandabornDev\build\stage\PandabornFactions\Modules\modules.txt` (same modules), and make sure `git log -1 -- src/code`
  is older than the `code` stage of P3. If either differs, rerun P3 and the gate. Do T7's registry query before
  and after.
* **Known:** the scoop scenario has never passed on the catalogue's templates. Its first run was started as a
  Folktails game by mistake (`gate-20261114-172537-...`, fixed in 9cd509a) and the rerun was cut off by the pause.
  The grid and the water line passed twice on older stagings (`gate-20261114-155403`, `-171322`, `-173036-...`).
* **Data of 2026-11-25 that needs nothing beyond this run:** the Goldfish Bowl and Moon Gate prices, the Flume
  Bridge Span's cost, science costs, the wellbeing trims (numbers the game reads without code of ours).
* **If it fails:** the catalogue lane reads the run; a template that throws on place or finish goes to the models
  lane, a water check to the water lane, a module that is not `on` to that module's code lane. Do not install.
  `-GateOverride` only on the coordinator's word.

### G2. Install

* **Command:** `powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 install` (no game; it refuses without
  a gate file that matches the staging folder, and while a Timberborn process is open). The stage does not take the
  test mutex itself: hold the queue around it as in T8, so that no queued test starts its game during the copy.
* **Must see:** `Documents\Timberborn\Mods\PandabornFactions` is a junction to `E:\PandabornDev\build\PandabornFactions`,
  and `E:\PandabornDev\build\PandabornFactions\Modules\modules.txt` lists ten modules.
* **Paired installs that ride on this one** (old half plus new half fails silently, see `CLAUDE.md`): look bundle
  with lantern meshes; plants bundle with the shoot-bamboo model; attachments bundle with hats, baskets, the Wooden
  Ox and the lantern prefab. N18 looks at all three in game.

---

## Tier 2: crashes if wrong

These run on the installed build. A failure here is a bug every player would hit.

### C1. Installed build alone: Inkpaws, then Folktails in one launch

* **Proves:** the shipped mod with no other mod; our materials, texts and sounds are put back when an Inkpaws game
  is left; a Folktails game after it is vanilla.
* **Command:**
  `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Plains -OnlyMods JigglyPanda.PandabornFactions -RequestJson tests\scenarios\catalogue\shipped_inkpaws_then_folktails.json -TimeoutSeconds 1200 -WaitForGameSeconds 10800 -RunId c1-alone-then-ft`
* **Must see:** `summary.json` PASS for both games (`overall.json` lists two). Inkpaws `result.json`:
  `activeFaction` Inkpaws, adult model `Characters/Pandaborn/InkpawAdult.Model`. Folktails `result.json`:
  `BeaverAdult` on `Characters/Beaver/...`, no template ending `.Inkpaws` among the available ones, and the
  feature report line shows no feature active.
* **Time:** 5 minutes (as `p5-fullmods-3`: 303 s). **If it fails:** Bootstrap/Core lane; Look, Words or sound
  leftovers go to that module's lane.

### C2. The same with all of the owner's mods

* **Proves:** the shipped mod beside 35 others, the Reskin, ChooChoo and the staircase mod among them (the two
  that crashed the data-only look).
* **Command:** as C1 without `-OnlyMods JigglyPanda.PandabornFactions`, and `-RunId c2-fullmods-then-ft`.
* **Must see:** PASS, `logErrorsOurs` empty; `modsLoaded` has about 34 entries. Other mods' noise is listed and
  does not fail the run (31 `Assertion failed` lines after "Too many atlases loaded" are known).
* **Time:** 7 minutes (`p4-fullmods-then-ft-1`: 421 s). **If it fails:** the compatibility audit lane.

### C3. Folktails and Iron Teeth with the mod off and on

* **Proves:** the other two factions are untouched: same templates, goods, needs, toolbar and character meshes.
* **Commands** (four short runs):
  * `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Folktails -Map Plains -RunSeconds 60 -OnlyMods JigglyPanda.PandabornDevHarness -WaitForGameSeconds 10800 -RunId c3-ft-off`
  * the same with `-OnlyMods JigglyPanda.PandabornFactions -RunId c3-ft-on`
  * both again with `-Faction IronTeeth` and `-RunId c3-it-off`, `c3-it-on`
* **Must see:** in each pair the two `result.json` files agree on the `templates` counts (Folktails was 332
  placeable of 368), on `characterTemplatesActive` (beaver meshes, 877 and 874 vertices) and on the population;
  all batch-control tabs open.
* **Time:** 6 minutes for the four (`catalogue-ft-off` 88 s, `-on` 90 s, `...-ironteeth` 71 s).
  **If it fails:** catalogue lane (global data leaked into another faction).

### C4. A lived-in colony, saved and reloaded

* **Proves:** a save of the shipped build loads: faction, colonists, buildings, module state.
* **Command:**
  `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Plains -InGameDays 2 -Speed 3 -OnlyMods JigglyPanda.PandabornFactions -Buildings 'PandabornDen.Inkpaws,EfficientFarmHouse.Inkpaws,PandabornSteamer.Inkpaws,PandabornHammock.Inkpaws,PandabornMoonLoft.Inkpaws,PandabornNightBuildersPost.Inkpaws,LumberjackFlag.Inkpaws,WaterPump.Inkpaws' -SaveAndReload -ReloadSeconds 120 -TimeoutSeconds 1800 -WaitForGameSeconds 10800 -RunId c4-save-reload`
* **Must see:** PASS for both launches; the population in `reload\result.json` equals the first launch's (adults,
  children, and three Ringtails if the Moon Loft was finished); `reload\foundation.json` has `loadSave` true and
  all modules on; no "loading issue" dialog text in `reload\harness.log`.
* **Time:** 13 minutes (`p4-fullmods-days-1`: 588 s and 199 s). **If it fails:** the lane of the module named in
  the error; Bootstrap/Core for the store.

### C5. Modules switched off

* **Proves:** "data alone behaves like vanilla" on the build that ships: with every module off the game loads, a
  save made with them on loads, the notice appears, flumes are solid blocks, Ringtails load as Inkpaws.
* **C5a, all off at once. SCENARIO TO WRITE** (Bootstrap/Core lane; copy `proto\ringtails\test\forcedoff.request.json`
  and set `devSwitchNextLaunch` to
  `force-off: Bell, Names, Look, Words, Water, Ringtails, Tutorial, Festival, Flowering`; place a Moon Loft, a
  short flume line and a Festival Square before the save). Suggested path `tests\scenarios\code\all_off.request.json`.
  * Build: `powershell -ExecutionPolicy Bypass -File proto\foundation\build.ps1 -Name pballoff` and
    `powershell -ExecutionPolicy Bypass -File proto\ringtails\build.ps1`
  * Run: `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Plains -InGameDays 1.2 -Speed 3 -DisableMods JigglyPanda.PandabornFactions -ExtraMods E:\PandabornDev\build\proto\pballoff,E:\PandabornDev\build\proto\ringtails -RequestJson tests\scenarios\code\all_off.request.json -SaveAndReload -ReloadSeconds 120 -TimeoutSeconds 1800 -WaitForGameSeconds 10800 -RunId c5a-all-off`
  * Must see: `reload\foundation.json` shows every module `forced-off` and RingtailsFallback on; the same number
    of colonists as before the save, the Ringtails now `InkpawAdult.Inkpaws`; nothing wet beside the flume; zero
    errors from our mods. The run-time "feature off" notice (new code of 2026-11-25): one message in the game's
    notification log per switched-off feature that the save used, in plain words, once per load and not once per
    building (`reload\harness.log` lists the messages; take one `screen` shot with the log open).
* **C5b, one at a time, for the four never tried:** four short new games on the installed build with the dev
  switch in the environment (it reaches the game the same way `tests\scenarios\look\run_look_tests.ps1` does it):
  `$env:PANDABORN_DEV = 'force-off: Bell'`, then
  `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Plains -RunSeconds 60 -OnlyMods JigglyPanda.PandabornFactions -WaitForGameSeconds 10800 -RunId c5b-off-bell`;
  repeat with `Names`, `Words`, `Tutorial`; then `Remove-Item Env:PANDABORN_DEV`.
  * Must see: PASS; `foundation.json` shows that one module `forced-off`; with Words off the population panel says
    "Beavers"; with Names off colonists have vanilla names; with Tutorial off the game still loads (the tutorial
    stages that use our step type must be left out, not thrown on).
* **Time:** C5a 8 minutes, C5b 8 minutes for the four. **If it fails:** Bootstrap/Core lane first.
* **A3, the switch as a player would set it** (release documents lane; `README.md` tells players to use `setx` and
  says it "has not been tried here"). C5b sets the variable for the test's own process only. This one writes the
  owner's user environment (`HKCU\Environment`), so **it needs the owner's go-ahead**, and the Steam half needs the
  owner at the PC.
  * In a console: `setx PANDABORN_DEV "force-off: Water"`. Open a **new** PowerShell window (an open one does not
    see the change) and run
    `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Plains -RunSeconds 60 -OnlyMods JigglyPanda.PandabornFactions -WaitForGameSeconds 10800 -RunId a3-setx`.
  * Must see: `foundation.json` shows Water `forced-off` and the other nine on; the feature notice names the Water
    toolkit; no flume piece carries water.
  * Undo at once: `reg delete HKCU\Environment /v PANDABORN_DEV /f` (the README's `setx PANDABORN_DEV ""` leaves an
    empty variable behind; check that an empty value really switches nothing off, and correct the README if the
    variable must be deleted instead). Then confirm with a new window: `$env:PANDABORN_DEV` prints nothing.
  * The owner's half, once: with the variable set, close Steam completely, start it, start the game from Steam,
    load an Inkpaws game, read the notice. This is the only way to prove the README's "restart Steam" sentence.
  * Time: 1 minute of game. If it fails: Bootstrap/Core lane; release documents for the README.
* **Proven before, one at a time, on dev copies:** Look (`look-module-forceoff-2`), Water (`water-w2-0809`),
  Ringtails (`rt2-forcedoff`), Festival and Flowering (`events-fallback-4`, `events-backon-2`).

---

## Tier 3: proofs of new behaviour

Code or data that has never run, or has run only on the prototype's own templates. Most of these can change design
or data. Ringtail runs need the probe: build it once with
`powershell -ExecutionPolicy Bypass -File proto\ringtails\build.ps1` (after G2, and again after any code change).

### N1. The Ringtails' rested bonus (new code, 2026-11-25)

* **Proves:** a Ringtail is rested by the length of its own night shift, so at twelve and twelve a night builder
  does the work of a day builder (the build before this change gave 0.75).
* **SCENARIO TO WRITE** (Ringtails code lane): `proto\ringtails\test\throughput2.request.json`, from
  `throughput.request.json`: day builders (Builders' Hut) and night builders (Night Builders' Post) on the same
  queue of dens, `workingHours` 12, and the probe sampling each colonist's `WorkingSpeed` and `MovementSpeed`
  multiplier and the goods each carried per shift. This is the `rt-throughput2` that balance.md says "never ran".
* **Command:**
  `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Plains -InGameDays 3 -Speed 3 -OnlyMods JigglyPanda.PandabornFactions -ExtraMods E:\PandabornDev\build\proto\ringtails -RequestJson proto\ringtails\test\throughput2.request.json -TimeoutSeconds 1500 -WaitForGameSeconds 10800 -RunId n1-rt-throughput2`
  then `python proto\ringtails\test\analyze.py E:\PandabornDev\build\test\n1-rt-throughput2`
* **Must see:** in `ringtails.json`, from day 2 (the bell locks the day at dawn), a Ringtail's two multipliers
  equal an Inkpaw's of the same wellbeing (1.33 times the multiplier without the bonus; at 16 hours no bonus for
  either); goods carried per worker per shift within about 10% of each other; the bonus is gone after a reload
  until the next dawn locks it again, with no error. Ringtails never exceed the walking cap (2.66).
* **Time:** 7 minutes (`rt-throughput1`: 400 s). **If it fails:** Ringtails code lane; if parity is still off,
  balance (options B and C in balance.md M2).

### N2. The bell curve from twelve to sixteen hours (data, 2026-11-25)

* **Proves:** the rested bonus tapers by the hour (12 h +33%, 13 h +22.8%, 14 h +14%, 15 h +6.4%, 16 h none), the
  slider line says so, and the module does not report the walking cap as too low.
* **SCENARIO TO WRITE** (Bell lane): a five-day variant of `tests\scenarios\catalogue\phase5_played_inkpaws.json`
  with one `hours` step a day (12, 13, 14, 15, 16) and the bonus watch it already has
  (`tests\scenarios\catalogue\make_phase5.py`, `bell_step`). Suggested name `bell_curve_inkpaws.json`.
* **Command:**
  `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Meander -GameMode Normal -InGameDays 6 -RunSeconds 900 -TimeoutSeconds 1500 -WaitForGameSeconds 10800 -NoBatchControl -OnlyMods JigglyPanda.PandabornFactions -RequestJson tests\scenarios\catalogue\bell_curve_inkpaws.json -RunId n2-bell-curve`
* **Must see:** `result.json` `goodsProbe.watch`: for `InkpawAdult.Inkpaws` the `WorkingSpeed` and `MovementSpeed`
  multipliers on each day equal the multiplier without the bell times 1.33, 1.228, 1.14, 1.064 and 1.0; the
  feature report in `harness.log` reads "The afternoon bell: on", not "on, reduced".
* **Time:** 6 minutes. **If it fails:** Bell lane (code), catalogue (curve points, cap in `modifiers.toml`).
* **Note:** use the map Meander for every scripted colony. On Plains the scripted player cannot place its pump
  ("no level path to the network"), which is why `p5-played-3` and `p5-folktails-3` failed.

### N3. The Star Tower as a Ringtail night post (decided 2026-11-25)

* **Proves:** the tower is staffed by Ringtails from the bell to dawn, makes science overnight, shows "Closed for
  the day" by day, and is an ordinary workplace when the Ringtails module is off.
* **SCENARIO TO WRITE** (Ringtails code lane, after the catalogue lane un-hides the tower): add
  `PandabornStarTower.Inkpaws` and `PandabornOperaStage.Inkpaws` to the `place` list of
  `proto\ringtails\test\module.request.json`, and queue two dens one hour after the bell (`laterPlace`, unfinished)
  for N13. Suggested name `proto\ringtails\test\posts2.request.json`.
* **Command (N3, N4 and N13 share it):**
  `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Plains -InGameDays 2.4 -Speed 3 -OnlyMods JigglyPanda.PandabornFactions -ExtraMods E:\PandabornDev\build\proto\ringtails -RequestJson proto\ringtails\test\posts2.request.json -TimeoutSeconds 1500 -WaitForGameSeconds 10800 -RunId n3-posts2`
* **Must see:** `ringtails.json`: the Star Tower's workers are `RingtailAdult.Inkpaws` only, working between the
  shift start and dawn; the science count is higher at dawn than at the bell; a daytime shot of its panel with the
  moon mark and "Closed for the day". **The tower keeps its science cost:** after the family arrives the three
  posts are unlocked and the Star Tower is still locked (`UnlockOnArrival = false`; the probe lists the locked
  tools, and the request must place the tower through the unlock, not past it).
* **Time:** 6 minutes game, shared (`rt3_ui3`: 433 s). **If it fails:** Ringtails code lane; catalogue for the
  template.

### N4. The Opera Stage as an ordinary attraction (same launch as N3)

* **Must see:** in the same run, off-duty colonists enter the stage (`result.json` `activity` shows the
  attraction behaviour; the Opera need `PandabornPerformance` rises above zero in a need sample); the loop
  `Environment.Buildings.Loop.Pandaborn.OperaStage` starts with real visitors; nothing in its panel says who runs
  it.
* **If it fails:** catalogue lane. **Open decision:** it still sits in the Night Watch toolbar group, and it is on
  the vanilla Dance Hall model although `art/models/OperaStage` exists (coordinator, catalogue).

### N5. Pump and tap shelves back to vanilla size (data, 2026-11-25; same launch as N2)

* **Must see:** in N2's `result.json` goods probe, the first Water Pump's store holds about 49 water, not 146
  (large pump 240, not 720); workshops with ingredients still hold three working days.
* **If it fails:** catalogue lane (generator rule in `rules.toml [shelves]`). Its effect on a careless colony is B1.

### N6. Trip-Hammer Mill and Treadwheel Lift at work, on the catalogue's templates

* **Proves:** the mill as the catalogue builds it (the 3x2x3 Gristmill shell with its worker, wheel cell (0,1))
  grinds rice flour in a current with no shafts and says "needs a current" when becalmed; the staffed Treadwheel
  Lift raises water. Neither has ever worked in a game: the gate's scoop scenario leaves the mill out on purpose.
* **SCENARIO TO WRITE** (water lane): `tests\scenarios\catalogue\water_mill_inkpaws.json`, from
  `proto\water\tests\scoop.json`: a channel with a current, `PandabornTripHammerMill.Inkpaws` with rice in a
  warehouse and a worker, the current stopped after one day; `PandabornTreadwheelLift.Inkpaws` at a still pond
  with a worker and a basin above; the camera on each building for one shot with its panel open.
* **Command:**
  `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Plains -OnlyMods JigglyPanda.PandabornFactions -RequestJson tests\scenarios\catalogue\water_mill_inkpaws.json -TimeoutSeconds 2400 -WaitForGameSeconds 10800 -RunId n6-water-mill`
* **Must see:** the water checks in `result.json` pass (flour made while the current runs, none after; lift above
  zero while staffed, zero off shift); the shots show the panel lines and the status icon text on screen (the
  earlier runs read the texts from the files, never from the screen); the mill's wheel and hammers move.
* **Time:** 8 minutes (`gate-...-water_scoop`: 425 s). **If it fails:** water lane; models lane for the mill's
  animation and the lift's model (the kit's `TreadwheelLift` was made for a Water Pump basis and is not adopted).

### N7. Badwater shut-off and dew in a drought, under the module

* **Proves:** a Flume Gate shuts itself when the water turns bad and reopens when it clears (the design's answer
  to "a flume would poison every terrace"); the Dew Collector slows to 35% in a drought. Both were proven only in
  the phase-1 prototype (`water-parts-0308`, `water-dew-0404`).
* **SCENARIO TO WRITE** (water lane): `tests\scenarios\catalogue\water_badwater_inkpaws.json`, from
  `proto\water\tests\parts.json` and `dew.json`, with the same change of template names that
  `tests\scenarios\catalogue\make_water.py` makes (add both to that script).
* **Command:** as N6 with that file and `-RunId n7-water-badwater`.
* **Must see:** contamination below 0.05 in the flume cells after the gate; the gate's status "shut: bad water";
  the soil beside the flume uncontaminated; dew output in the drought about a third of the temperate rate, and the
  temperate rate equal to the catalogue's new recipe (retuned on 2026-11-25; B13 asks whether four collectors
  carry an outpost).
* **Time:** 6 minutes. **If it fails:** water lane.

### N8. Flume shapes never built

* **Proves:** a raised Bridge stepping straight down onto ground, a Corner after a Bridge, and a line that
  splits. Only the Drop from ground level and the span crossing have run.
* **SCENARIO TO WRITE** (water lane): `tests\scenarios\catalogue\water_shapes_inkpaws.json`.
* **Command:** as N6 with that file and `-RunId n8-water-shapes`.
* **Must see:** water reaches the end of each line; side cells stay at 0.000; a missing piece shows its status.
* **Time:** 6 minutes. **If it fails:** water lane; if a shape cannot work, the Flume's description (text lane)
  and the models lane's cap request.

### N9. The first drought with haulers, a tap and a colony drinking

* **Proves:** with a Hauling Post, haulers do not carry the cisterns' water into the Cistern Tap's store where
  nobody can drink it (balance W1); the "Tip: a Cistern Tap ..." line appears on the stopped wheel; the area sound
  of the flume plays only where water runs.
* **Command** (the water lane's W3 scenario on a fresh dev copy with the prototype pieces; or its `.Inkpaws`
  conversion once `make_water.py` writes it):
  `powershell -ExecutionPolicy Bypass -File proto\water\build.ps1`, then
  `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Plains -RequestJson proto\water\tests\w3.json -DisableMods JigglyPanda.PandabornFactions -ExtraMods E:\PandabornDev\build\proto\water -TimeoutSeconds 2400 -WaitForGameSeconds 10800 -RunId n9-water-drought`
  (add a `HaulingPost.Inkpaws` to the scenario first: water lane).
* **Must see:** drinkable water left in the cisterns on drought day 3; the tap's store near 15, not 144; the grove
  beside the flume alive (the plant-state probe must cover the grove this time: a slip in `water-w3-0815`).
* **Time:** 14 minutes (`water-w3-0815`: 832 s). **If it fails:** catalogue (shelf exception), water lane.

### N10. The rising lanterns fill the festival sky (needs P1 and P2)

* **Proves:** the reworked lanterns (continuous `Emit`, bigger and slower prefab, drift with the wind, speed
  follows game speed) read as a sky full of lanterns from the normal camera, at speed 1 and at speed 3. This is
  the owner-facing "postcard".
* **Build:** `powershell -ExecutionPolicy Bypass -File proto\events\build.ps1 -Name pbsky -Variant proto\events\variants\sky`
* **Commands:**
  `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Plains -RequestJson tests\scenarios\events\events-sky.request.json -ExtraMods E:\PandabornDev\build\proto\pbsky,E:\PandabornDev\build\proto\events-probe -OnlyMods JigglyPanda.PandabornFactionsDev -TimeoutSeconds 1500 -WaitForGameSeconds 10800 -RunId n10-sky`
  and the same with `events-sky-speed3.request.json` and `-RunId n10-sky-speed3`.
* **Must see:** `ev_s_h1650_dusk.png`, `ev_s_h1800_wide.png`, `ev_s_h2050_night_wide.png`: lanterns in the air
  over the whole show (16:00 to 22:00), not a single flight; no comet rockets; `events.json` festival block
  `skyLanterns` above zero in every sample of the show. The speed-3 shots look the same.
* **Time:** 4 minutes each (`events-sky-1`: 252 s). **If it fails:** events lane; the prefab and bundle go to the
  characters lane.
* **Seen so far:** `events-sky-1` (2026-11-14, the unfinished rework with the old bundle) shows about seventeen
  lanterns rising over the square at 18:00 (`ev_s_h1800_wide.png`). It was never written up.

### N11. The festival on the build's own numbers, with a real pump crew and Ringtails

* **Proves:** the festival still runs end to end after the number changes (festive decay, science costs, the rules
  file `FestivalRules.cs`): auto-call in fair weather, Grand Festival, a mid-show save, Tradition; a real
  `WaterPump.Inkpaws` crew works through the festival day (only stand-in crews have); a Ringtail sleeps through its
  morning rest and then joins.
* **Build:** `powershell -ExecutionPolicy Bypass -File proto\events\build.ps1` (copy `pbevents` and the probe).
* **Command:**
  `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Plains -RequestJson tests\scenarios\events\events-main.request.json -ExtraMods E:\PandabornDev\build\proto\pbevents,E:\PandabornDev\build\proto\events-probe -OnlyMods JigglyPanda.PandabornFactionsDev -SaveAndReload -ReloadSeconds 130 -TimeoutSeconds 1500 -WaitForGameSeconds 10800 -RunId n11-events-main`
  (events lane first adds a staffed Water Pump and a Moon Loft with a night post to that request).
* **Also look at worker-turned power** (second audit: a festival halts it): add a staffed Power Wheel driving a
  Pole Mill and a staffed Treadwheel Lift. The lift's crew is on the keep-working list and must work; the Power
  Wheel's crew takes the day off and the mill stops. That is the design ("the cost is a day's work"), but the
  Festival Square's panel and the call message must say it, and nothing may break when power returns at dawn.
* **Must see:** `events.json`: `phase` Called then Running; on the festival day `working` holds only the pump
  and lift crews; a Ringtail sample with the rest behaviour in the morning and at the square by 19:00; Tradition 1 at dawn;
  the reload launches only the bursts still due; `#FestivalLights` hidden before the call and shown after it
  (compare `ev_d1_h15_gathering.png` with a shot taken before the call).
* **Time:** 6 minutes (`events-main-3`: 171 s and 188 s). **If it fails:** events lane.
* **Still not staged anywhere:** two districts; sixty colonists (27 is the most: `events-crowd-1`); a long run at
  speed 7. Events lane, when a scenario exists.

### N12. The Great Flowering: buds seen at the announcement, and timber bamboo

* **Proves:** with the pass-4 plants bundle and shoot-bamboo model installed, the announcement itself turns a field
  pale and speckled (so far the switch is proven on the old art, `events-buds-1`, and the new art through a
  test material, `plants-buds-2`, never both together); a timber-bamboo Flowering is harvested by lumberjacks.
* **Command:**
  `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Plains -RequestJson tests\scenarios\events\events-buds.request.json -ExtraMods E:\PandabornDev\build\proto\pbevents,E:\PandabornDev\build\proto\events-probe -OnlyMods JigglyPanda.PandabornFactionsDev -TimeoutSeconds 900 -WaitForGameSeconds 10800 -RunId n12-buds`
  and `tests\scenarios\events\events-crews.request.json` with the Flowering species set to timber bamboo and a
  staffed Lumberjack Flag (events lane edits the request), `-RunId n12-timber`.
* **Must see:** `ev_b_before.png` against `ev_b_after_field.png`: the field visibly paler; in `n12-timber`,
  "Bamboo seed harvested" above zero and the grove regrowing after the nine-day rest. **Steamed seed cakes** (data
  of 2026-11-25): with no Kitchen and no mill in the colony, a Steamer set to the seed-cake recipe turns the seed
  into cakes, two per seed, and colonists eat them (events lane adds a Steamer and the `setRecipe` action).
* **Time:** 2 and 5 minutes. **If it fails:** plants lane (art), events lane (switch, harvest).

### N13. Ringtail leftovers (same launch as N3)

* **Must see, in N3's run:** a den queued after the bell is *finished* by dawn by the Night Builders' Post (so far
  only the carrying is recorded: 36 goods in 18 night trips, `rt2-soak`); the probe logs the twitter at the
  arrival (`RingtailTwitter` in the sound samples).
* **Not staged anywhere, low value:** the loft line "no Ringtail adult in the district" (NoParents); ten connected
  lofts on one map (seven were, `rt3_breed3`). Ringtails lane, if a scenario is ever written.

### N14. The bell's suggestion waits through bad weather

* **Proves:** "Inkpaws work a short day and work it well" is not posted during a drought or badtide and is posted
  at the first fair dawn after it (read from code only: `docs/tech/stage0.md`).
* **SCENARIO TO WRITE** (Bell lane): `proto\foundation\tests\phase3_tutorial_bell.request.json` with a drought
  started on day 2 and ended on day 4 (the events probe's `startDrought` shows how).
* **Command:** `powershell -ExecutionPolicy Bypass -File proto\foundation\build.ps1 -Name pbphase3`, then
  `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Plains -InGameDays 5 -Speed 3 -DisableMods JigglyPanda.PandabornFactions -ExtraMods E:\PandabornDev\build\proto\pbphase3 -RequestJson <the new file> -TimeoutSeconds 1500 -WaitForGameSeconds 10800 -RunId n14-bell-drought`
* **Must see:** the probe's log: "waits (hazardous weather)" on days 3 and 4, posted on day 5.
* **Time:** 6 minutes (`p3-bell-tutorial-2`: 357 s). **If it fails:** Bell lane.

### N15. The Inkpaws tutorial played from a new game, in its new order

* **Proves:** the generated tutorials advance in a real colony in the order decided on 2026-11-25 (the woodcutter
  first, then water and food, poles, dens, a cistern, the inventor, the Steamer, the bell, flumes, tea last), with
  no step that points at a locked button or at a building that cannot be built yet. So far: the game builds the
  stages, and the "have N of a good" step works in a hand-made two-stage tutorial (`p3-bell-tutorial-2`).
* **N15a, the full build. SCENARIO TO WRITE** (Tutorial lane): the `tutorial` watch of
  `proto\foundation\tests\phase3_tutorial_bell.request.json` added to
  `tests\scenarios\playtest\inkpaws-standard.json` (the scripted player then follows the same order), run as
  `MAP=Meander tests/scenarios/playtest/run_playtest.sh inkpaws-standard Inkpaws Normal 41 n15a-tutorial`.
* **N15b, every build that changes the chain.** The chain is generated, so it changes with the catalogue's
  switches, not with a run-time switch: Water off leaves the Flumes tutorial out, Ringtails off the Ringtails one,
  Tutorial off the "have N" stages, Bell off the bell stage. Without a game, P5 (`pandaborn.ps1 code,combos`)
  already proves that all nine combinations generate and that no stage names a template its build lacks. With a
  game, the one combination that must be played is the data-only build, because it is what a player gets when the
  code cannot load: `powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 code,combos -Combo no-code`
  leaves it in `E:\PandabornDev\build\combos\stage\PandabornFactions`.
  **Blocked on tooling:** there is no way yet to run that folder in the game without installing it. The dev-copy
  builder (`proto\foundation\build.ps1`) always adds a fresh code build, and the folder cannot be passed to
  `-ExtraMods` as it is (same folder name and manifest id as the installed faction). The option the tooling
  review proposes for the gate (a copy that changes only the manifest id) unblocks this run too. Then: the same
  playtest command with `-DisableMods JigglyPanda.PandabornFactions -ExtraMods <that copy>` in place of
  `-OnlyMods ...` and `-RunId n15b-tutorial-nocode`.
* **Must see:** each tutorial's stages achieved in order, with the day of each; none stuck on a step the scripted
  player demonstrably did (a broken trigger); no stage naming a building the build leaves out; the tutorial-panel
  setting restored afterwards. In N15b the chain skips Flumes, Ringtails and the "have N" stages and still ends.
* **Time:** 11 minutes each. **If it fails:** Tutorial lane, catalogue (`tutorial.toml`), text lane for a stage
  that reads wrong.

### N16. Sounds from their natural triggers

* **Proves:** a workshop that is really producing and an attraction with real visitors start our loops by
  themselves (so far the loops were started through the game's own toggle call, `sound-4`); the flume's area sound
  and the bamboo tok fire from the Water module.
* **Command:** `powershell -ExecutionPolicy Bypass -File proto\sound\build.ps1`, then
  `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Plains -RequestJson proto\sound\tests\sound.request.json -OnlyMods JigglyPanda.PandabornFactions -ExtraMods E:\PandabornDev\build\proto\sound -TimeoutSeconds 1200 -WaitForGameSeconds 10800 -RunId n16-sound`
  (sound lane first lengthens the Inkpaws part to one in-game day with a stocked Steamer and a Teahouse, and adds a
  short flume line).
* **Must see:** `result.json` `soundProbe`: the Steamer and Teahouse loops `advanced` with no `ToggleSound` call
  from the probe; `Environment.Pandaborn.FlumeWater` playing while water runs and silent after; in the Folktails
  half, `soundsNotPlayed: Pandaborn` passes.
* **Time:** 5 minutes (`sound-4`: 283 s). **If it fails:** sound lane; Water lane for the two flume sounds.
* **After the owner has listened (O1)** and the catalogue sets `sound_id = "Pandaborn"`: run it once more and
  check the colonist clicks play `UI.Beavers.Pandaborn.Selected.*`.

### N17. The Wooden Ox at work

* **Proves:** oxen cut trees and haul (in `rb-p3a` they took the jobs but no tree was marked, so no cutting and no
  hauling was seen), and the new recipe (20 cured poles, 20 gears, 4 metal, 96 hours) builds one.
* **SCENARIO TO WRITE** (characters lane): `proto\ringtail-body\test\pass3_reskin.request.json` with trees marked
  for the flag and an Ox Workshop stocked for one ox.
* **Command:** `powershell -ExecutionPolicy Bypass -File proto\ringtail-body\build.ps1`, then the README's command
  with the new request: `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -NoBuild -Faction Inkpaws -InGameDays 5 -Speed 3 -ExtraMods E:\PandabornDev\build\proto\ringtails,E:\PandabornDev\build\proto\ringtail-body -OnlyMods JigglyPanda.PandabornFactions -RequestJson <the new file> -TimeoutSeconds 1500 -WaitForGameSeconds 10800 -RunId n17-ox`
* **Must see:** `activity` shows the bot's cutting and carrying behaviours; one ox comes out of the workshop
  after four days; the ox mesh is `Characters/Pandaborn/WoodenOx.Model`.
* **Time:** 9 minutes. **If it fails:** characters lane; catalogue for the recipe. B8 measures its hauling.

### N18. The paired installs, looked at

* **Proves:** on the *installed* build, lanterns glow red-orange and the Sky Lantern amber (look bundle with the
  rebuilt meshes), the budding and flowering bamboo use the right masks (plants bundle with the model), farmers
  wear the conical hat and gatherers the basket (attachments bundle), every adopted model shows its construction
  stage and its finished state.
* **Command:**
  `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Plains -OnlyMods JigglyPanda.PandabornFactions -RequestJson E:\PandabornDev\build\gen\PandabornFactions.models.request.json -TimeoutSeconds 1500 -WaitForGameSeconds 10800 -RunId n18-models`
* **Must see:** look at the PNGs: the night shots of the Festival Square, Lantern Workshop and the three lantern
  decorations (red-orange, not yellow-white and not dark); one farmer close-up with the hat.
* **Time:** 6 minutes (`models-catalogue-2`: 362 s). **If it fails:** the lane of the stale half: look, models,
  plants or characters; the catalogue lane reinstalls both halves together.

### N19. The wonder launch

* **Proves:** the Sky Lantern filled with its goods (400 paper lanterns among them) and launched through the game's
  own wonder button: the launch sound `UI.Buildings.Wonder.PandabornSkyLantern`, the rise animation, the great
  lantern lit while it flies at night, the awe need on every colonist, the completion picture and its two texts.
  So far the pieces were played one by one by the harness (`models-pass3-6` the rise, `sound-4` the launch sound).
* **SCENARIO TO WRITE** (models lane with the harness's owner): a `wonder` action that fills the finished wonder's
  inventory and calls its activation, with shots at 0, 5 and 15 seconds, by day and at night.
* **Command:** `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Plains -OnlyMods JigglyPanda.PandabornFactions -RequestJson <the new file> -TimeoutSeconds 1200 -WaitForGameSeconds 10800 -RunId n19-wonder`
* **Must see:** the shots; the awe need `PandabornSkyLantern` at its maximum in a need sample; the completion panel
  with our picture (`wonder-completion-inkpaws`), not a blank or the Folktails'.
* **Time:** 5 minutes. **If it fails:** models (animation, light), sound, catalogue (`faction.toml [faction.wonder]`).

### N20. Ringtails come back when a district's last one dies (new code, 2026-11-25)

* **Proves:** when a district with a Moon Loft has no living Ringtail, a new family arrives after a few days; and
  the same after a load of a save that was made, or played, with the module off (where the saved Ringtails had
  become Inkpaws).
* **SCENARIO TO WRITE** (Ringtails code lane): from `proto\ringtails\test\forcedoff.request.json`: a Moon Loft and
  a post, the family arrives, the probe removes all three Ringtails on day 1 (a new probe action), five more days;
  the reload half: save with `force-off: Ringtails` for one launch, then load with the module on.
* **Command:** `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Plains -InGameDays 6 -Speed 3 -OnlyMods JigglyPanda.PandabornFactions -ExtraMods E:\PandabornDev\build\proto\ringtails -RequestJson <the new file> -SaveAndReload -ReloadSeconds 200 -TimeoutSeconds 2400 -WaitForGameSeconds 10800 -RunId n20-rt-return`
* **Must see:** `ringtails.json`: zero Ringtails for a few days, then two adults and a kit again with one message;
  never a second family while one Ringtail lives; after the module-off load, the former Ringtails stay Inkpaws and
  one new family comes, once.
* **Time:** 12 minutes (`rt2-soak`: 594 s and 734 s). **If it fails:** Ringtails code lane.

### N21. Inkpaw foresters replant dead trees by default (new code, 2026-11-25)

* **Proves:** a newly built Inkpaws Forester has "replant dead trees" on; a grove killed by drought is replanted
  without the player touching anything; a Folktails Forester in the next game still starts with it off.
* **SCENARIO TO WRITE** (the lane that wrote the code): a Forester with a timber-bamboo grove on a strip that the
  water lab dries for eleven days, then waters again; `then` a Folktails game with one Forester.
* **Command:** `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Plains -OnlyMods JigglyPanda.PandabornFactions -RequestJson <the new file> -TimeoutSeconds 1800 -WaitForGameSeconds 10800 -RunId n21-replant`
* **Must see:** the Forester's toggle reads on at placement; dead bamboo cleared and young bamboo on the same tiles
  after the water returns; the Folktails Forester's toggle off.
* **Time:** 6 minutes. **If it fails:** the Core code lane (the code is `src/code/Pandaborn.Names/ForesterCustom.cs`,
  in the working tree on 2026-11-25).

---

## Tier 3b: other mods alongside

From `docs/reviews/2026-11-25-mod-compatibility.md`, section 9 ("Test matrix, in priority order"); the finding each
run settles (M2, m7, ...) is in that document. Every run uses the installed faction with all modules on, on the
hidden desktop, and must show zero errors from either side.

**No run may leave a mod flag changed.** Each uses `-OnlyMods` or `-DisableMods`, which change flags for that run
only and restore them afterwards. After every run check that `<run>\modstate.restore.json` shows every value
matching and that `E:\PandabornDev\build\test\modstate.pending.json` does not exist; if it does, run
`powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -RestoreModState <run>\modstate.json` before anything else. `-OnlyMods` takes a manifest id, a
folder name or a display name, and keeps what those mods require (Harmony comes along by itself). The ids below
are the ones seen in `summary.json` `modsLoaded` on 2026-11-14; where only a display name is known it is quoted.
Do not use `-DryRun` to check a list casually: it launches nothing, but it queues for the lock, rebuilds the
harness and creates and removes junctions in `Mods`.

| Id | Mods on (besides ours) | Command | Must see | Game min | If it fails |
|---|---|---|---|---|---|
| X1 | All of the owner's mods | No run of its own: G1 runs the grid with every one of the owner's mods on (the gate only switches the installed faction off), C2 is Inkpaws then Folktails, R5 is three days with a reload | the old 35-mod result again with Ringtails, Water, Festival and Flowering; the feature report all "on"; Folktails as in a run without us (C3) | 0 | Compatibility lane |
| X2 | Harmony, T3MP, Performance Plus | N11's command and the gate's water line, each with `-OnlyMods JigglyPanda.PandabornFactionsDev,T3MP,"Performance Plus"` (events) or `-OnlyMods JigglyPanda.PandabornFactions,T3MP,"Performance Plus" -RequestJson tests\scenarios\catalogue\water_w4_inkpaws.json -SaveAndReload` (water); add a speed ladder up to 7 to both requests | their logs free of verify mismatches; no stuck harvest or planting job after a Flowering; flume water kept across the reload; the rested bonus still multiplies (Performance Plus patches `BonusManager`) | 12 | The module named; compatibility lane for a store-page note |
| X3 | The Reskin 7.0.0; then the `factions-compat` build of it | `powershell -ExecutionPolicy Bypass -File proto\ringtail-body\build.ps1`, then `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -NoBuild -Faction Inkpaws -InGameDays 1.1 -Speed 3 -ExtraMods E:\PandabornDev\build\proto\ringtails,E:\PandabornDev\build\proto\ringtail-body -OnlyMods JigglyPanda.PandabornFactions,JigglyPanda.Pandaborn -RequestJson proto\ringtail-body\test\pass3_reskin.request.json -SaveAndReload -TimeoutSeconds 1500 -WaitForGameSeconds 10800 -RunId x3-reskin`; then the same with `pass3_compat.request.json`, the compat dev copy in `-ExtraMods` (`E:\PandabornDev\build\reskin-compat\PandabornReskinCompat`, id `JigglyPanda.PandabornReskinCompatDev`) in place of `JigglyPanda.Pandaborn`, `-RunId x3-compat` | as `rb-p3a` and `rb-p3b`: Inkpaws and Ringtails with fur, no pale crown patch; with the compat build the Inkpaws keep their own coats; Folktails pandas unchanged in the game after | 16 | Characters lane; the Reskin's `factions-compat` branch ships with our release |
| X4 | Moddable Tool Groups, MoreGroups, CustomTools, Automation | `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Plains -RunSeconds 120 -FactionPanelShots -OnlyMods JigglyPanda.PandabornFactions,ModdableToolGroups,KnatteAnka.MoreGroups,Timberborn.IgorZ.CustomTools,Timberborn.IgorZ.Automation -WaitForGameSeconds 10800 -RunId x4-toolgroups`, with the tutorial panel on and a shot of every toolbar group (the harness option K2 asks for) | every Inkpaws building reachable; no empty group; tutorial steps highlight a button; the Night Watch group absent in a Folktails game | 4 | Catalogue (tool groups), Tutorial lane |
| X5 | Choo!Choo!, TimberUi, KnatteMaterials | **SCENARIO TO WRITE** (compatibility lane): a station and track built as Inkpaws, a festival day, the Population tab. `-OnlyMods JigglyPanda.PandabornFactions,Aoernis.ChooChoo,TimberUi,KnatteAnka.Materials` | no "already loaded" and no "not found in repository" material error; the Population tab opens | 6 | Look lane (materials), compatibility lane |
| X6 | TimberCommons, Simple Floodgate Triggers, SmartPower | the gate's two water scenarios with `-OnlyMods JigglyPanda.PandabornFactions,Timberborn.IgorZ.TimberCommons,Hytone.SimpleFloodgateTriggers,Timberborn.IgorZ.SmartPower`, `-RunId x6-water-w4` and `x6-water-scoop`; a floodgate trigger on a Scoop Wheel by hand in the request | flume numbers equal to the run without them (G1's); the Scoop Wheel still lifts with TimberCommons' `WaterOutput` subclass in place | 12 | Water lane |
| X7 | Ferris Wheel, Food Stall, MoreZiplineConnections, 4-way District Center | `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Plains -RunSeconds 90 -Screenshots 'overview@start,adult@start,screen@end' -OnlyMods JigglyPanda.PandabornFactions,Tobbert.FerrisWheel,Timberborn.ARandomDiamond.FoodStall,"MoreZiplineConnections",Lapantouflemagic.4Wdistrictcenter -WaitForGameSeconds 10800 -RunId x7-buildings` | no crash; the Village Hall is the starting building; an Inkpaw's wellbeing panel shows the two foreign needs as the audit describes (m1) | 3 | Catalogue; a store-page note |
| X8 | One other faction mod (Emberpelts, or the most subscribed one then) | Needs the owner to subscribe to it first. Main menu, then a game of each faction in one launch: `-FactionPanelShots`, a request with `then` | both factions listed and playable; the tutorial question of the audit's section 4 answered first | 6 | Compatibility lane, Tutorial lane |
| X9 | Two copies of ours, with and without TimberUi | `powershell -ExecutionPolicy Bypass -File proto\foundation\build.ps1 -Name pbdupA`, then `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -RunSeconds 40 -ExtraMods E:\PandabornDev\build\proto\pbdupA -OnlyMods JigglyPanda.PandabornFactions -RequestJson proto\foundation\tests\duplicate.request.json -WaitForGameSeconds 10800 -RunId x9-dup`; again with `,TimberUi` added to `-OnlyMods`, `-RunId x9-dup-timberui` | without TimberUi: our duplicate notice, one copy's bundles parked, a game that loads (as `fd-dup-3`); with it: TimberUi's own crash text, copied word for word for the store page | 4 | Bootstrap/Core lane; release documents |
| A2 | A real building pack offered to the Inkpaws the way `README.md` tells mod authors to ("For mod authors": one `TemplateCollection` file with `CollectionId` `Buildings.Inkpaws` that appends the pack's `.Folktails` templates). `docs/RELEASE.md` 4.5 lists it as open; the README says it has not been run | **SCENARIO TO WRITE** (compatibility lane): a dev mod of one file, `E:\PandabornDev\build\proto\packtest\TemplateCollections\TemplateCollection.PackTest.Buildings.Inkpaws.blueprint.json` plus a manifest that requires the pack, appending the blueprint paths of one installed pack (the Staircase mod is the hard case: it needs materials from the `Folktails` collection). Nothing is copied from the pack and the pack is not edited. Then `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Plains -RunSeconds 120 -OnlyMods JigglyPanda.PandabornFactions,KnatteAnka.Staircase -ExtraMods E:\PandabornDev\build\proto\packtest -Buildings '<one of the pack's template names>' -WaitForGameSeconds 10800 -RunId a2-building-pack` | the pack's buildings are in the Inkpaws' toolbar, one is placed and finished with no "material not found", it wears the Inkpaws' look; a Folktails game with the same mods is unchanged. If it fails, the README's promise to mod authors must change before release | 4 | Compatibility lane; release documents for the text |
| X10 | Ours alone on the next game patch, before regenerating | Cannot be run until a patch exists. Then: load a saved Inkpaws game (R3's save) | which fallback fires first and the text a player would see (the audit's section 6) | 0 today | Every code lane |

---

## Tier 4: balance runs

Each settles a number in `docs/tech/balance.md` ("Proposed changes", ids M and W) or one of its "thin" places.
Scripted colonies run at speed 30 on the map **Meander** (about 16 real seconds a game day). The report tool turns
a run into `verdict.md` and charts:
`E:\PandabornDev\tools\venv\Scripts\python.exe -I tools\playtest_report.py E:\PandabornDev\build\test\<run> [<run> ...] --labels a,b`.
The general command is the script the playtest lane used (bash):
`MAP=Meander tests/scenarios/playtest/run_playtest.sh <scenario> <Faction> <Normal|Hard> <days> <run id>`.

| Id | Settles | Command | Must see | Game min | If it fails |
|---|---|---|---|---|---|
| B1 | M1, pump shelves: does a careless Inkpaws village now meet thirst in the first drought, as a careless Folktails one does (which lost ten of thirty-nine) | `MAP=Meander tests/scenarios/playtest/run_playtest.sh inkpaws-careless Inkpaws Normal 31 b1-ink-care` and `... folktails-careless Folktails Normal 31 b1-ft-care` | `playtest/daily.jsonl`: water at the start of the first drought near 50 plus the cisterns; some colonists thirsty, no deaths on Normal; the Folktails twin as in `pt-ft-care-m3` | 17 | Balance, then catalogue (`rules.toml [shelves]`) |
| B2 | Hard: where an unprepared start dies, and whether cabbage carries it | `... inkpaws-hard Inkpaws Hard 31 b2-ink-hard` and `... folktails-hard Folktails Hard 31 b2-ft-hard` | deaths and their causes by day; shoot bamboo alive after the first drought (was 45%); before the shelf change the Hard script lost 8 of 13 to thirst, so this is the run that shows what vanilla-sized pump shelves cost; a FAIL verdict is expected when the colony dies: read the telemetry, not the verdict | 17 | Balance; playtest lane for a plan that stocks up (needed for R2) |
| B3 | M3 to M5 and W8: the day of the first flume and of the first festival with two inventors; first crop day | `... inkpaws-standard Inkpaws Normal 41 b3-ink-std` and `... folktails-baseline Folktails Normal 41 b3-ft-base` (playtest lane first adds a gate, three flumes and a scoop wheel to the Inkpaws plan, now that Water is in the build) | `events.jsonl`: first flume finished between day 6 and day 10; the day of the first poles cut from bamboo now that timber bamboo takes seven days (it was five), and whether the Pole Mill carries the colony until then; first festival in cycle 2; stores before the drought | 22 | Balance, catalogue (`building_stats.toml`) |
| B4 | The 12-hour day with a real economy (never exercised: every colony stayed at 16 hours), and Folktails untouched by the bell | `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Meander -GameMode Normal -InGameDays 20 -RunSeconds 1800 -TimeoutSeconds 2400 -WaitForGameSeconds 10800 -NoBatchControl -OnlyMods JigglyPanda.PandabornFactions -RequestJson tests\scenarios\catalogue\phase5_played_inkpaws.json -RunId b4-ink-12h`; the same with `-Faction Folktails`, `phase5_played_folktails.json`, `-RunId b4-ft-12h` | Inkpaws: output per colonist at 12 hours within a few percent of B3's 16-hour run; rested multipliers in the watch. Folktails: multipliers stay vanilla | 22 | Bell lane, balance |
| B5 | W4, W9 and the pole reserve; everything past day 20 and 20 colonists (no run ever got there) | Needs a driver change first (**playtest lane**: keep marking trees so the colony grows; `src/devharness/Playtest`). Then `... inkpaws-standard Inkpaws Normal 60 b5-ink-60` and `... folktails-baseline Folktails Normal 60 b5-ft-60` | both colonies reach 50; wellbeing and population by day side by side: the Inkpaws' lead no more than a few points at equal science | 120 | Balance, then catalogue (`needs.toml`) |
| B6 | Time off duty (3.9 hours for bed, 1.2 for meals are rules of thumb): how many rituals fit a 12-hour and a 16-hour day | **SCENARIO TO WRITE** (playtest lane): one colonist's behaviour logged every half hour for five days, working hours 12, then 16. Two runs of `run_game_test.ps1 ... -InGameDays 5 -Speed 3` on the installed build | hours by behaviour per day; nap and tea both fit at 12 hours; what is lost at 16 | 20 | Balance |
| B7 | Tea in a living village (no run ever stocked a Teahouse): do haulers or night couriers keep it stocked, do five seats serve about 25 | **SCENARIO TO WRITE** (playtest lane): `inkpaws-standard` with tea bushes on dry ground, a Tea Roastery and a Teahouse from day 12, 30 days | the Teahouse never empty for more than a day; the Tea need average above half; visits per day | 12 | Balance, catalogue |
| B8 | W6: an ox against an Inkpaw hauler on the same pile | **SCENARIO TO WRITE** (characters or balance lane): two piles 20 tiles apart, one ox, one Inkpaw, three days | goods moved per day each; the ox no more than about 1.7 times the Inkpaw | 6 | Balance, catalogue (`recipes.toml`) |
| B9 | W10 and the old question "do three-day shelves make workshops hoard scarce logs and poles early": a Pole Mill with dens queued | `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -InGameDays 2 -Speed 3 -OnlyMods JigglyPanda.PandabornFactions -ExtraMods E:\PandabornDev\build\proto\ringtails -RequestJson proto\ringtails\test\workshops-noringtails.request.json -TimeoutSeconds 1500 -WaitForGameSeconds 10800 -RunId b9-shelves` (Ringtails lane first adds a Pole Mill and four queued dens) | the dens are not starved of logs while the mill's store fills; logs in the mill's input at dawn | 6 | Balance, catalogue |
| B10 | W9: pickles on a land-limited map | **SCENARIO TO WRITE** (playtest lane): `inkpaws-standard` with the farm capped at 30 tiles, 41 days, with and without a Pickle Yard | food per tile-day; pickles no better than bread | 22 | Balance |
| B11 | W12: seed cakes after a Flowering | N12's `n12-timber` run with a stocked Kitchen (events lane) | seed harvested against the food the gap cost; cakes made | 0 (shared) | Balance |
| B12 | The first pass's least certain number: a self-supplied workshop's uptime (model 64%) | **SCENARIO TO WRITE** (balance lane): a Pole Mill, one worker, no haulers, a log pile 20 tiles away, three days | poles made per day against the model's figure | 6 | Balance |
| B13 | The Dew Collector's new yield: four collectors keep a landlocked outpost of about six in water outside droughts | **SCENARIO TO WRITE** (balance or water lane): a second district with no water in reach, six colonists, four collectors, a cistern, ten days with one drought | nobody critically thirsty outside the drought; the cistern carries the drought or it does not (say which) | 8 | Balance, catalogue (`recipes.toml`) |

Also owed from the first pass and not yet a scenario: whether a ripe crop can still be harvested while it is dying
of drought, and whether a dying crop resumes fully (the dry-day numbers 5, 7 and 10 rest on it). Water lane's
drought scenario with one ripe and one growing field; balance lane owns the number.

---

## Tier 5: the release soak

Run on the build that will be packaged, after every change above has landed. `docs/ENGINEERING.md` "Tests required
before a release" is the source; C1 to C5, G1 and N6 to N9 are part of it and must be green on that same build.

| Id | What | Command | Must see | Game min | If it fails |
|---|---|---|---|---|---|
| R1 | A new Inkpaws game on each difficulty, three days | `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Meander -GameMode Easy -InGameDays 3 -Speed 3 -OnlyMods JigglyPanda.PandabornFactions -WaitForGameSeconds 10800 -TimeoutSeconds 1200 -RunId r1-easy`; again with `Normal`, `Hard` | PASS, no errors, nobody critical on day 3 | 15 | The lane of the error |
| R2 | A soak of twenty days or more on each difficulty, through a drought: nobody starves, no exceptions | `MAP=Meander tests/scenarios/playtest/run_playtest.sh inkpaws-standard Inkpaws Easy 41 r2-easy`; again with `Normal` and (with the prepared plan from B2) `inkpaws-hard ... Hard 41 r2-hard` | no death from hunger or thirst; `logErrorsOurs` empty; the first drought and one badtide inside the run | 33 | Balance; the module named in an exception |
| R3 | The save every later release must still load | C4's command with `-KeepSave -RunId r3-baseline-save`; then copy `Documents\Timberborn\Saves\PB_AutoTest_r3-baseline-save` to `E:\PandabornDev\assets\release-saves\<version>\` (the test save folder is deleted by later runs) | the folder exists and loads in a rerun | 5 | Catalogue lane |
| R4 | Grid extras the gate does not do: every panel opened, every plant grown and killed in each soil state | **SCENARIO TO WRITE** (harness: a `select` pass over every placed building with its panel open); and `powershell -ExecutionPolicy Bypass -File proto\plants\build.ps1`, then `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Plains -OnlyMods JigglyPanda.PandabornFactions -ExtraMods E:\PandabornDev\build\proto\plants -RequestJson proto\plants\tests\states.request.json -WaitForGameSeconds 10800 -RunId r4-plant-states` (the plants prototype must ship no bundle while the faction does) | no panel throws; each of the nine plants shows its alive, dying and dead model | 10 | The lane of the panel; plants lane |
| R5 | A soak with all of the owner's mods | `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Plains -InGameDays 3 -Speed 3 -SaveAndReload -ReloadSeconds 120 -TimeoutSeconds 1800 -WaitForGameSeconds 10800 -RunId r5-fullmods-days` | PASS for both launches, `logErrorsOurs` empty | 13 | Compatibility audit lane |
| R6 | Release rules, no game | `powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 package` | exit 0: every bundle has its `_mac` twin, the API lists match the game, the economy block has no errors, no `AssetBundles.parked` folder | 0 | Catalogue lane |

### A1. The screenshot session for the store pages (release documents lane)

Not a test: pictures for the Workshop and mod.io pages. The list is `catalogue/text/store/screenshots.md`: of ten
shortlisted, three can be used as they are, seven must be retaken, and seven that the page needs were never taken.
It needs the installed build (after G2 and after N10, so the lanterns are the reworked ones), a real village and
someone to frame each picture: plan an hour with a person, not a scripted run.

* **Missing (seven):** a flume line in a real village (Scoop Wheel in the river, gate, flumes, a green grove beside
  it, brown ground beyond: the first line of the pitch has no picture); a rice terrace stepping down a hillside with
  Paddy Spouts and the Paddy House; the working-hours panel showing the rested line in today's build; the new-game
  screen with the Inkpaws selected (current logo and text); night work, Ringtails raising a building under lantern
  light while the Inkpaws' windows glow; the festival without developer controls and with the rising lanterns; a
  wide village by day with no warning icons (the picture that goes first).
* **Retakes (seven, numbers 4 to 10 of the shortlist):** both peoples at night with the ox, hat and basket (taken
  with the Reskin on); the village street by the Village Hall (status icons in frame); the small village from above
  (test layout, warning icons); the Festival Square at night with twenty dancers (developer controls and frame
  counter on screen); the Sky Lantern glowing on its tower (edge of the test map in frame); a Night Courier Post
  selected at night (developer controls on screen); the three bamboo fields, green, budding and in flower (bare
  test ground).
* **Rules** (from the same file): the Reskin off unless the caption says otherwise; developer mode off
  (`-NoDevMode`); no status icon in the middle of the frame; one idea per picture.
* **How:** the village comes from B5's or R2's colony kept with `-KeepSave`, or from a village built by hand. The
  new-game screen is free in any run with `-FactionPanelShots -OnlyMods JigglyPanda.PandabornFactions`
  (`factionPanel_Inkpaws.png`). The others need a camera placed by a person: either the owner, or a harness
  request with camera positions (the `modelShots` of `proto\models\tools\gen_proof2_request.py` show the form).
  Never with `-Visible` while the owner is at the PC.
* **Owner:** release documents lane picks and captions; the owner approves (O2, O6).

## Cosmetic proofs (last, or inside a launch that is already running)

| Id | What | Where to see it | Lane |
|---|---|---|---|
| K1 | The hammock swinging as motion (stills show it in use), the trip hammers falling, the Treadwheel Lift's axle | Frame pairs a second apart in N6 and N18: `proto\models\tools\gen_proof2_request.py` shows how to ask for them | Models |
| K2 | The icons of pass 3 in the real toolbar (no game run was made in that pass): every bottom-bar group open, at 1280 and at 4K | Needs a harness option to open each tool group and take `screen` shots; until then `screen_end.png` of G1 shows only the bar | Icons, harness |
| K3 | Portraits with the Reskin enabled (never photographed) and the new-game faction panel | C2 with `-FactionPanelShots`: `factionPanel_Inkpaws.png` | Characters |
| K4 | The ox on a zipline; ox horns against vanilla bot hats | A zipline in N17's colony | Characters |
| K5 | Many lit buildings at night at close range; frame rate with the re-themed materials in a large town (never measured) | `overview` shots and `FPS` in the corner of `screen_end.png` of B5 | Look |
| K6 | The festival with sixty colonists and with two districts | See N11 | Events |

## Only the owner or another person can settle these (not runs)

| Id | What | Where |
|---|---|---|
| O1 | Listen to the sounds; approve or refuse the panda calls. Until then `sound_id = "Common"` (beaver calls) | `E:\PandabornDev\build\sound\index.html` |
| O2 | Art by day and by night; the festival postcard | The PNGs of N10, N18 and G1 |
| O3 | Whether the first hour feels cozy | An hour of play on the installed build |
| O4 | Text tone | `catalogue/text/`, `docs/PLAYER_GUIDE.md` |
| O5 | Mac: seven checks on real hardware, with all four `_mac` bundles (look, plants, sounds, attachments) | `docs/tech/mac.md` "What only a real Mac can verify" |
| O6 | Store pages; a native speaker's check of the colonist names | `README.md`, `catalogue/text/names.json` |

## Already proven: do not run these again for the reason the document gives

Each of these is still called unproven, untested or pending somewhere. A later run settled it.

| Document says | Settled by |
|---|---|
| `docs/tech/look.md` line 178: an Inkpaws game followed by a Folktails game in one session is "not yet tested" | `look-module-then-2`, `look-module-then-4`, `p4-fullmods-then-ft-1` (all PASS); `sound-4` did it again |
| `docs/tech/water.md` "Still not proven": the catalogue's own `.Inkpaws` water templates in a game | `gate-20261114-155403` and `-171322` (grid: all thirteen water templates placed and finished); `gate-20261114-162438-water_w4_inkpaws` and `-173036-...` (line, crossing on a span, spout, paddy, save and reload). What is left is G1's scoop run and N6 |
| `docs/tech/water.md` checklist item 3: the `CisternTap` and `TripHammerMill` kit models "have not been in a game yet" | Placed and finished in the same two grid runs. Not yet seen working: N6 |
| `docs/tech/ringtail-body.md` 8.7: the `LanternRise` prefab is "not yet proven", run `lanterns-1` "is queued" | `lanterns-1` ran and passed (2026-11-14 18:20); `events-sky-1` (19:09) shows the lanterns rising. Neither was written up. The reworked version is N10 |
| `docs/tech/models.md` lines 428 and 591 to 593: lit windows with occupants, the hammock with a sleeper, a colonist under the Moon Loft "not proven" | `models-proof2-1` (the same document, pass 5) |
| `docs/tech/models.md` line 679: warm lantern glow in game "needs the look lane's two patches" | `models-lanterns-1` |
| `docs/tech/models.md` pass 6: the risen Sky Lantern is dark at night | The catalogue gave it a night light; `gate-20261114-171322\night_PandabornSkyLantern.png` shows it glowing amber on its tower. The glow while it flies is in N18's shots |
| `docs/tech/two-peoples.md` 18.6: kits raised in game, births over many days, the clock arc "unproven" | `rt3_breed3`, `rt3_ui3` (section 19 of the same document) |
| `docs/tech/two-peoples.md` 19.3: the Night Builders' Post "raising sites at night" | Carrying is proven: `rt2-soak`, 36 goods in 18 trips, all at night. A den *finished* overnight is N13 |
| `docs/tech/sound.md` section 9: the modules that will play the code-played sounds "are not written yet" | Bell rings (`p3-bell-tutorial-2`), the clapper answers at every shift start (`rt3_breed3`, 12 of 12), the festival drum and firecrackers (`events-main-3`), the flume sound and bamboo tok (`water-w5b-1556`) |
| `docs/tech/events.md` and `docs/tech/plants.md`: buds "not visible" | The new art reads across a field: `plants-buds-2`. Together with the module's own switch: N12 |
| `docs/DESIGN.md` change log: three-day shelves "to be re-checked for workshops hoarding scarce logs and poles early" | Read from code in balance.md's second pass ("no hoarding without haulers"); B9 confirms it in game |
| `docs/tech/tutorial.md` line 3: "Status: proposal (not built)" | Built: `catalogue/tutorial.toml` (nine tutorials), the `Tutorial` module, `p3-bell-tutorial-2`. Played through: N15 |

## Not owed

* **A module whose API check fails for real.** Only a game update can do it; `simulate-missing-api` and
  `force-off` stand in (C5).
* **Ringtails walking in from the map edge; a per-kind appetite; the Long Nap; the toolbar moon mark.** Not built.
* **A Treadwheel Lift with a Ringtail worker** (`docs/tech/water.md`). The design no longer gives Ringtails that
  job.
* **Game speed 7 with many colonists over many cycles.** No scenario and no claim rests on it; B5 at speed 30 is
  the long run.

## Totals

| Tier | Items | Game runs | Game time | Of which need a scenario written first |
|---|---|---|---|---|
| 0. Test tooling | T1 to T8 (T7 and T8 ride on G1 and G2) | 6 | 12 min | none; T3 and T6 need a person at the console, T4 and T5 the owner |
| 1. Install gate | G1, G2 | 3 | 16 min | none |
| 2. Crashes if wrong | C1 to C5, A3 | 13 | 48 min | C5a; A3 needs the owner's go-ahead |
| 3. New behaviour | N1 to N21 (N4, N5 and N13 share launches) | 21 | 2 h 25 min | N1, N2, N3, N6, N7, N8, N14, N15a, N17, N19, N20, N21; N9, N11, N12 and N16 need an edit to an existing request; N15b waits for a tooling option |
| 3b. Other mods | X1 to X10, A2 (X1 rides on G1, C2, R5; X10 waits for a game patch) | 13 | 1 h 9 min | X5, A2; X4 needs the harness option of K2; X8 needs the owner to subscribe to a mod |
| 4. Balance | B1 to B13 (B11 shares N12) | 21 | 4 h 40 min | B5 (driver), B6, B7, B8, B10, B12, B13; B3 and B9 need an edit |
| 5. Release soak | R1 to R6 (R6 has no game), A1 | 10, and one screenshot session | 1 h 16 min, and about an hour with a person | half of R4 |
| Cosmetic | K1 to K6 | 0 of their own | inside other runs | K2 |
| **All** | **74 items** | **87, and one session** | **about 10 h 45 min** | **23 scenarios or harness options, 6 edits** |

Wall clock is about a fifth more (loading, dev-copy builds, the report tool): plan thirteen hours, or three to
four evenings if each window is the two-hour list at the top followed by one tier.

## Test scenarios and probes that still live in `proto/` (work list for the scenarios lane)

`docs/ENGINEERING.md` calls `proto/` throwaway, yet the runs above depend on the files below, which exist nowhere
else. Nothing has been moved: this is the list to move from. "Used by" names the backlog ids. After each move, fix
every path in the right-hand column and in this document's commands (they are written against today's paths).

**Request files** (suggested home: `tests/scenarios/<feature>/`, keeping the file name, with `.request.json` where
it lacks it)

| File today | Used by | Should live in | Paths to fix when it moves |
|---|---|---|---|
| `proto/water/tests/w4.json`, `scoop.json` | G1 (through their `.Inkpaws` conversions `tests/scenarios/catalogue/water_w4_inkpaws.json`, `water_scoop_inkpaws.json`), N6, X2, X6 | `tests/scenarios/water/` | `tests/scenarios/catalogue/make_water.py` (`SRC`); the converted files should move to `tests/scenarios/water/` too, and then the two paths in the `gate` stage of `tools/pandaborn.ps1` |
| `proto/water/tests/parts.json`, `dew.json` | N7 | `tests/scenarios/water/` | `make_water.py` (add both) |
| `proto/water/tests/w3.json` | N9 | `tests/scenarios/water/` | `docs/tech/water.md` |
| `proto/water/tests/w1.json`, `w2.json`, `w5.json`, `flume.json`, `longrun.json`, `combo.json`, `crops.json`, `district.json`, `district2.json` | Not in the backlog (their proofs stand); the source for N8 and for B's drought scenario | `tests/scenarios/water/` | `proto/water/tools/gen_tests.py`, which writes `w1` to `w4` |
| `proto/ringtails/test/throughput.request.json` | N1 | `tests/scenarios/ringtails/` | `proto/ringtails/README.md` |
| `proto/ringtails/test/module.request.json` | N3, N4, N13 | `tests/scenarios/ringtails/` | same |
| `proto/ringtails/test/forcedoff.request.json` | C5a, N20 | `tests/scenarios/ringtails/` (the all-off variant in `tests/scenarios/code/`) | same |
| `proto/ringtails/test/workshops-noringtails.request.json`, `workshops.request.json` | B9 | `tests/scenarios/ringtails/` | `proto/ringtails/test/shelves.py` |
| `proto/ringtails/test/soak.request.json`, `breeding.request.json`, `ui.request.json`, `folktails.request.json`, `fallback.request.json`, `gate.request.json`, `smoke.request.json` | Not in the backlog (their proofs stand); R2 may reuse `soak` | `tests/scenarios/ringtails/` | `docs/tech/two-peoples.md` |
| `proto/foundation/tests/phase3_tutorial_bell.request.json` | N14, N15a | `tests/scenarios/code/` | `docs/tech/stage0.md` |
| `proto/foundation/tests/duplicate.request.json` | X9 | `tests/scenarios/code/` | same |
| `proto/foundation/tests/carrier_off_then_on.request.json`, `phase3_nodata_then_folktails.request.json`, `words_inkpaws_then_folktails.request.json` | Not in the backlog (proofs stand); C5 and N15b may reuse them | `tests/scenarios/code/` | same |
| `proto/sound/tests/sound.request.json` | N16 | `tests/scenarios/sound/` | `docs/tech/sound.md` section 6 |
| `proto/ringtail-body/test/pass3_reskin.request.json`, `pass3_compat.request.json` | N17, X3 | `tests/scenarios/characters/` | `proto/ringtail-body/README.md` |
| `proto/ringtail-body/test/lanterns.request.json`, `body.request.json`, `combined.request.json`, `night.request.json` | Not in the backlog (superseded by `tests/scenarios/events/events-sky*.request.json`, or proofs stand) | `tests/scenarios/characters/` | same |
| `proto/plants/tests/states.request.json` | R4 | `tests/scenarios/plants/` | `proto/plants/tools/gen_requests.py`, which writes it |
| `proto/plants/tests/buds.request.json`, `flowering.request.json`, `pass2.request.json`, `terrace.request.json` | Not in the backlog (proofs stand; `terrace` is the source of a store screenshot) | `tests/scenarios/plants/` | same |
| `proto/models/tests/proof2.request.json`, `lanterns.request.json` | K1; the pattern for A1 and N19 | `tests/scenarios/models/` | `proto/models/tools/gen_proof2_request.py`, `gen_look_request.py` |
| `proto/models/tests/all.request.json`, `night.request.json`, `pass2.request.json`, `pass3.request.json`, `stages.request.json`, `water.request.json` | Not in the backlog: superseded by the generated `E:\PandabornDev\build\gen\PandabornFactions.models.request.json` (N18) | Can stay or go | |
| `proto/look/tests/*.json`, `proto/stage0/tests/*.json` | Not in the backlog (proofs stand; the look module's own scenarios are already in `tests/scenarios/look/`) | Can stay | |

**Probes and builders** (dev-only mods and scripts; suggested home: `tests/probes/<feature>/` for a probe mod, `tools/`
for a builder that several lanes use)

| Thing today | What it is | Used by | Should live in |
|---|---|---|---|
| `proto/foundation/build.ps1` (with `proto/foundation/mod`, `devmodule`, `src`, `tools/merge.py`, `variants/nodata`) | **The dev-copy builder.** Makes `E:\PandabornDev\build\proto\<name>`, a full copy of the installed or staged mod under the id `JigglyPanda.PandabornFactionsDev`. The install gate calls it (the `gate` stage of `tools/pandaborn.ps1`), and so do `proto/events/build.ps1` and every "dev copy" in this document | G1, T2, T6, C5a, N14, N15b, X9, and through the events builder N10 to N12 | `tools/dev_copy.ps1` (the builder) and `tests/probes/foundation/` (the DevCarrier test module, the probe, the fragments). It is the least throwaway thing in `proto/` |
| `proto/ringtails/build.ps1`, `src/`, `test/analyze.py`, `births.py`, `shelves.py` | The Ringtails test probe (`JigglyPanda.PandabornProtoRingtails`, request key `ringtails`) and its analysis scripts | C5a, N1, N3, N4, N13, N17, N20, B9, X3 | `tests/probes/ringtails/` |
| `proto/events/build.ps1`, `src/`, `variants/` (`test`, `crews`, `final`, `sky`), `tools/flowering_fair.py` | The events dev copies and probe (`JigglyPanda.PandabornProtoEvents`, request key `events`). Its request files are already in `tests/scenarios/events/` | N10, N11, N12, X2 | `tests/probes/events/` |
| `proto/ringtail-body/build.ps1`, `src/RingtailBodyProbe.cs`, `mod/` | The character picture probe (request key `ringtailBody`) | N17, X3 | `tests/probes/characters/` |
| `proto/sound/build.ps1`, `mod/` | Blueprint fragments for the sound test (the probe itself is `src/devharness/SoundProbe.cs`) | N16 | `tests/probes/sound/` |
| `proto/plants/build.ps1`, `src/PlantLab.cs`, `tools/gen_mod.py`, `gen_requests.py`, `build_dev_bundle.py` | The plant lab (grows and kills each plant in each soil state) | R4 | `tests/probes/plants/` |
| `proto/water/build.ps1`, `tools/gen_blueprints.py`, `gen_tests.py`, `analyze.py`, `mod/` | The water prototype mod (`.PandabornProto` copies of the pieces) and the generator of its scenarios. The lab itself is `src/devharness/WaterLab.cs` | N9 as written; the source of every water scenario | `tests/probes/water/` for the generators. The `.PandabornProto` templates can be dropped once N6 to N9 run on the catalogue's templates |
| `proto/models/tools/gen_proof2_request.py`, `gen_look_request.py`, `gen_mod.py` | Writers of model close-up requests | K1, the pattern for N19 and A1 | `tests/scenarios/models/` |
| `proto/stage0/`, `proto/look/`, `proto/ringtails-shelves/` | Finished prototypes; nothing in the backlog uses them | | Can stay as history |

Already in the right place: `tests/scenarios/catalogue/`, `events/`, `grid/`, `look/`, `playtest/`, and the labs
inside the harness (`src/devharness`: `WaterLab`, `GridLab`, `SoundProbe`, `GoodsProbe`, `ModelShots`, `Playtest`).

New request files this backlog asks for should be written straight into `tests/scenarios/<feature>/`, not into
`proto/`: C5a (`code/`), N1, N3 and N20 (`ringtails/`), N2 (`catalogue/` beside `make_phase5.py`), N6 to N8
(`water/`), N14 (`code/`), N17 (`characters/`), N19 (`models/`), N21 (`code/`), B6 to B8, B10, B12 and B13
(`playtest/` or `balance/`), X5 and A2 (`compat/`).

---

## Added on resume (2026-11-25)

Each lane working on 2026-11-25 reports its own "needs a game run" list to the coordinator. Append them here, one
block per lane, in the same shape as above (what it proves, the command, what must be seen, how long, who fixes it).
When an entry repeats an item above, write its id instead of a new entry. Renumber nothing: new items take the ids
A1, A2, ... in the order they arrive, and the coordinator places each in a tier.

### Catalogue and build lane

(empty)

### Code review: Water and Ringtails

(empty)

### Code review: Festival, Flowering and the lantern rework

(empty)

### Code review: Bootstrap, Core and the small modules

(empty)

### Text lane

(empty)

### Balance lane

(empty; balance.md's "Run to confirm" column is already in tier 4 and in N1, N2, N5)

### Icons and store art

(empty)

### Compatibility audit (received 2026-11-25)

Its ten runs are tier 3b above (X1 to X10), in the audit's own order.

### Second independent audit (received 2026-11-25; the audit is `docs/tech/audit-2.md`)

Every item of its list is placed above; nothing here is a new run.

| The audit asks for | Where |
|---|---|
| The install gate on the full assembled build with every module on, then install (no gate file exists; the shared gen and stage folders are stale) | P3, G1, G2 |
| The generated tutorial played from a new game in its new order, in every module combination that changes it, the data-only build included | N15a, N15b |
| The catalogue's Trip-Hammer Mill (a 3x2x3 staffed mill, its own scenario) | N6 |
| Night builders at night | N13 (inside N3's launch) |
| Badwater shut-off and dew under the Water module | N7 |
| A first drought with vanilla-sized pump shelves (the Hard script lost 8 of 13 to thirst before the change) | B1, B2; the shelf size itself N5 |
| A festival with a real pump crew (a festival halts worker-turned power) | N11 |
| The wonder launch | N19 |
| A Folktails game after an Inkpaws game on the final build | C1, C2 |
| New code: the Ringtails' rested bonus | N1 |
| New code: Ringtails re-invited when a district's Ringtails die out, and after a load with the module off | N20 |
| New code: the Star Tower keeps its science cost (`UnlockOnArrival = false`) | N3 |
| New code: Inkpaw foresters replant dead trees by default | N21 |
| New code: the run-time "feature off" notice | C5a |
| New data: timber bamboo at seven growth days (the day of the first poles) | B3 |
| New data: Steamer seed cakes | N12 |
| New data: the Dew Collector's yield | N7 (the rate), B13 (the outpost) |
| New data: Goldfish Bowl and Moon Gate prices | G1 (nothing beyond the gate) |

Open, not needing a run: the audit first reached the coordinator as a message only. It is now in the repository
as `docs/tech/audit-2.md` (commit eef6abe), so this is closed.

### Release documents (received 2026-11-25)

| The lane asks for | Id | Where it is placed |
|---|---|---|
| A screenshot session: seven retakes and seven missing pictures (a flume line in a real village, a spout terrace, the rested line, the new-game faction panel, night work, the festival, a clean wide village) | A1 | After tier 5, before the cosmetic proofs |
| A real building pack with a `Buildings.Inkpaws` file | A2 | Tier 3b, after X9 |
| One launch with `PANDABORN_DEV` set through `setx` | A3 | Tier 2, under C5 |

### Tooling review (received 2026-11-25)

Its eight runs are tier 0 above (T1 to T8), in the review's own order. Reread `docs/tech/tooling-review.md`
"Needs a game run" before running them: a second round of fixes was in progress when tier 0 was written.
