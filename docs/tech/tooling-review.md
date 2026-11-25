# Tooling review: the test runner, the hold scripts, the build and the install gate

2026-11-25, two rounds. A reading review of `tools/run_game_test.ps1`, `tools/play_timberborn.ps1`,
`tools/game_test_hold.ps1`, `tools/pandaborn.ps1`, `tools/build.ps1` and `proto/foundation/build.ps1`, then fixes.

**Nothing here has been through the game.** No game, test run, hold script, play script, install or gate was started
in either round; the Mods folder, the registry and `E:\PandabornDev\build\test` were not touched. What was run:
the PowerShell parser on every edited script, and `tools/tests/game_lock.trial.ps1` (120 checks, all passing) in a
scratch folder with a scratch mutex. That trial exercises the shared helpers directly, the functions of
`run_game_test.ps1` and `pandaborn.ps1` pulled out of the files by the parser, and `proto/foundation/build.ps1
-Staged` for real with `-ProtoRoot` in the scratch folder. The parts that write the registry (flag restore, window
prefs) and everything that needs a game are in the last section, in the order to run them.

Commits: `467b7f5` (round 1), `77c22e6` (round 2), and the commit that carries this text (the code lanes' asks,
below). Both game-free test commands were run once to check them: Events passes (28,518 checks); Foundation runs
and failed only its last check, because `E:\PandabornDev\build\code\PandabornFactions` held no build at that moment.

## How it works now

Shared helpers live in `tools/game_lock.ps1` (dot-sourced by the four scripts; functions only, every folder and
name a parameter). Files in `E:\PandabornDev\build\test`:

| File | What |
|---|---|
| `gametest.lock.json` | who owns the test lock: pid, start time, what |
| `HOLD.<pid>.json` | one per holder (`game_test_hold.ps1`: kind `hold`; `play_timberborn.ps1`: kind `play`), with pid and start time. A hold is in force while any of these names a live process. A file whose process is gone is stale: ignored and removed by whoever sees it. A file plainly named `HOLD` is the old format and is ignored |
| `run.pending.json` | what the run in progress has changed on the machine; written before the first change, removed on a clean exit |
| `modstate.pending.json` | unchanged: the prior mod flags, until their restore is verified |
| `<run>\request.in.json` | the test request of a hidden run (was `request.json` in the test root, the harness's default path) |

**A pid never decides anything alone.** `Test-SameProcess` (pid, start time, and the process name where it matters)
is behind every kill and every takeover: the run's own games, the record's games, queue tickets, hold files, the
holder file.

**The pending-run record** (`run.pending.json`): runner pid and start time; each test game's pid and start time as
it is launched; each junction the run makes in Mods, with its target, written before the junction exists; the save
folder; the request files; the window prefs before the first launch and the test's window size; the path of the
flag state. Not recorded, so never cleaned: what is meant to stay (`-KeepSave`'s save, `-KeepInstalled`'s harness
junction). On exit the runner removes the record unless a test game is still alive, the flags are not verified, a
junction could not be removed or the clean-up itself threw; then it stays.

**Cleaning from it.** Whoever gets the lock next (a run, `-Recover`, or `play_timberborn.ps1` through `-Recover
-DuringHold`) finds a record whose runner is dead and, in this order: stops the recorded game only if pid, start
time and name still match (this step also runs while waiting for "no Timberborn open", so an orphan game no longer
blocks the queue); refuses to go on if any other Timberborn is open (flags cannot be restored under a running
game); restores the flags through `Restore-ModState` from the pending file of that run id; removes the recorded
junctions (a link directly in Mods that is a junction and still points at the recorded target; the link only);
deletes the recorded save (a real folder directly in Saves named `PB_AutoTest_*`) and requests (inside the test
root, named `request.json` or `request.in.json`); puts the window prefs back, only if the registry still holds the
test's own window size. The record goes when all of that succeeded. A record whose runner is alive means a run in
progress (possible only under `-DuringHold`): a second run refuses to start next to it.

## Findings and their state

| # | Finding | State |
|---|---|---|
| F1 | Hidden runs counted any Timberborn started since the run began as their own until a pid was known: the owner's game could be killed | Fixed (467b7f5); now pid and start time (77c22e6) |
| F2 | "No Timberborn open" was checked once, long before the flags changed and the game launched | Fixed (467b7f5): checked again before any flag changes and before every launch |
| F3 | An unconsumed request at the harness's default path could run the test in the owner's game | Fixed twice: deleted first on abort (467b7f5); hidden runs no longer use the default path at all (77c22e6). The harness needed no change: `FindRequestPath` already takes `-pbTestRequest` and `PANDABORN_TEST_REQUEST`. Only `-Visible` still writes the default path (a Steam bounce loses both) |
| F4 | `modstate.json` read back as ANSI: a non-ASCII mod folder or Id restored the wrong value and "verified" it | Fixed (467b7f5) |
| F5 | `-DuringHold` trusted the `HOLD` file | Fixed (467b7f5), now `Test-HoldOwnsLock`: a live hold (pid and start time) must own the lock, by the mutex and by the holder file (77c22e6) |
| F6 | A waiter deleted a half-written queue ticket | Fixed (467b7f5) |
| F7 | Hidden-desktop handle never closed in a session that used `&` | Fixed (467b7f5) |
| F8, G3 | Install did not follow the install discipline | Fixed: refuses while Timberborn runs (467b7f5); takes the test lock for validation, mirror and link, without waiting, and names the holder when it is taken; `-CallerHoldsLock` takes nothing and checks that a live hold owns the lock (77c22e6) |
| F9, G4 | Override log | Hash and user (467b7f5); written only after validation has passed, with the game version and the reason the gate did not count; the help says an override never applies in a run that has the gate stage (77c22e6) |
| F10 | `play_timberborn.ps1` started the game after a restore it could not confirm | Fixed (467b7f5); now also for an unfinished clean-up of a dead run (77c22e6) |
| L1 | A killed runner left game, flags, junctions, save, request and prefs behind, with no record of the junctions | Fixed (77c22e6): the record and the clean-up above |
| L3, R2 | Stale `HOLD`; two holders shared one file and ended each other | Fixed (77c22e6): one file per holder, stale ones ignored and removed. `game_test_hold.ps1` removes its own file however it ends, and has `-Release` (ends every hold of kind `hold`, never the owner's play session). The play script's header now says what closing its window does |
| R1 | A queued run could beat a hold to the lock | Fixed (77c22e6): while a live hold exists, a queued run does not try for the lock |
| R4 | `play_timberborn.ps1` killed every Timberborn without a window | Fixed (77c22e6): `Get-HiddenGames` is gone. S stops the game in the record (pid, start time, name) and nothing else; leftovers go through the dead-run clean-up. A trial on a scratch lock with the real test root acts on nothing |
| R5 | Hold time drifted against the deadline | Fixed (77c22e6): the real time since the last look is added |
| L4 | `-KeepInstalled` kept `-ExtraMods` junctions | Fixed (77c22e6): harness only. Flags of an extra mod were already always restored |
| L6 | Pids compared without start times | Fixed (77c22e6), see above |
| L7 | Mirror and clear targets unguarded | Fixed (77c22e6): `Sync-Tree` refuses a target that is not inside `E:\PandabornDev\build`; the foundation build refuses an empty, rooted or path-like `-Name`, a target not directly in the proto root, and a source that is the target |
| G1 | The gate tested a fresh build of `src/code` with every module, DevCarrier, fragments and a probe, not the staged code | Fixed (77c22e6), below |
| G2 | Gate file had hash, run and time only | Fixed (77c22e6), below |
| L5 | Gate copies pile up | `gate -Prune` added (77c22e6); nothing deleted. Listing below |

### The gate now (G1, G2)

`pandaborn.ps1 gate` calls `proto/foundation/build.ps1 -Name pbgate-<hash8> -Source <StageDir> -Staged`. In that
mode nothing is built and nothing is added: every staged file is copied as it is, `Scripts`, `Modules` (with the
staged, filtered `modules.txt`) and `AssetBundles` included. **One file is replaced: `manifest.json`** (Id
`JigglyPanda.PandabornFactionsDev` and a dev-copy name), because a second copy cannot carry the installed mod's Id.
The grid request and the two water scenarios need neither DevCarrier nor the foundation probe (the "probe" they
mention is a step of the harness's own water lab), so neither is in the copy. One side effect, named in the gate
file: with an Id that is not the released one the bootstrap would read `pandaborn.dev.txt`; a staged build has none.
The build writes `E:\PandabornDev\build\proto\<name>.devcopy.json` next to the copy: the substitutions, the code
files, their hash, and it fails if the copy differs from the source in anything but the substituted files.

The gate then checks for itself that the copy's code files hash like the staged ones and that the rest (all but
`manifest.json`) hashes like the stage, hashes the grid request, reads the game version, runs, and afterwards
refuses to pass if the stage, the copy, the grid request or the game changed meanwhile. The gate file:

```
hash, run, passedUtc, stage            as before
gameVersion, steamBuild                Timberborn_Data\StreamingAssets\VersionNumbers.json, Steam's appmanifest
gameVersionReported                    what the game itself said in the grid run's result.json
codeHash, codeFiles                    Scripts\, Modules\, AssetBundles\ as run
devCopy { name, mode, manifestId, substitutions[] }
grid { path, sha256 }
modsLoaded                             ids of every mod the grid run loaded
```

Install refuses a gate whose `gameVersion` is missing or is not the installed game's (so every gate file written
before 77c22e6 is refused: one gate run is needed before the next install). A different Steam build with the same
version is a warning.

### Gate copies on disk (L5)

`E:\PandabornDev\build\proto`, measured in round 1:

| Folder | Size |
|---|---|
| `pbgate-3DA8DAA3` | 503 MB |
| `pbgate-BFE176F4` | 502 MB |
| `pbgate-C1D0B56C` | 459 MB |
| `pbgate-C27F882E` | 502 MB |
| `pbgate-CC92404E` | 501 MB |
| `pbgate-F3718EAD` | 502 MB |

About 3 GB; there is also an older `pbgate` (not a hash name, never pruned). `pandaborn.ps1 gate -Prune -DryRun`
lists what would go; `gate -Prune` removes every `pbgate-<8 hex>` folder that is not the current stage's, is not
junctioned into Mods and is older than 12 hours, with its `.devcopy.json`. With `-Prune` the gate itself does not
run.

## Asked by the code lanes (third commit)

* **`package` refuses a dev switch file.** Any `pandaborn.dev.txt` anywhere in the staging folder stops the stage,
  before validation.
* **`gate` fails when a shipped module is not on.** The harness already records the bootstrap's boot report:
  `result.json` `pandabornBoot`, a list of `{ id, status, reason }` taken from the AppDomain value
  `Pandaborn.Boot.Report` (`src/devharness/MaterialProbe.cs`, `PostLoad`). For every run of the gate (the grid run
  and the water runs) each id in the staged `Modules\modules.txt` must be there with status `on`, and `Core` must
  not be `off`; a result without a boot report fails too. The gate file lists the modules as `modulesOn`.
  **One thing for the scenarios lane:** the report is written inside the material probe's `try`, after the probe has
  read its materials. If that read throws, the result has no `pandabornBoot` and the gate now fails with "no boot
  report", which is safe but misleading. The harness should record `pandabornBoot` on its own, before any probe (for
  example where it writes `gameVersion`, or first thing in the game scene), and in the reload launch as well.
* **`code` runs the game-free tests** after the build and the module trim, and fails on a failure:
  `dotnet run --project src\code\tests\Foundation -c Release -- --mod <codeOut>` and
  `dotnet run -c Release --project src\code\tests\Events`.
* **`assemble`, the lantern sky pairing.** When any generated blueprint names `Effects/Pandaborn/LanternRise`,
  `pandabornattachments_win` and `_mac` must both be among the bundles and not older than the last git change of
  `src/unity/PandabornAttachments/Editor/PandabornAttachmentsBuilder.cs` (an hour of slack, as for the plants). No
  blueprint names it today, so the rule is silent until the catalogue adds the attachment.
* **Header and help of `pandaborn.ps1`**: the stage list, `all` with the gate, the three bundle folders.

## Still open

1. **L2, the owner starts Timberborn from Steam during a run that changed flags.** The run stops its game within
   2 s and restores, but whether the owner's game had already read the test's flags depends on when Unity loads
   PlayerPrefs. Game run 6 below answers it. `play_timberborn.ps1` avoids it.
2. **R3, two gates on the same staging content** still share `pbgate-<hash>`; the second build clears the folder
   under the first's game. It cannot give a wrong pass (the gate now re-hashes the copy after the run and fails).
3. **Between gate and install** the lock is free for a moment. If a queued test takes it, install refuses and has to
   be run again; nothing is installed half way. Install does not compare the installed folder with the gated hash
   after the mirror.
4. **Scripts already running keep the old rules** until they are restarted: a waiter queued before 77c22e6 does not
   wait behind `HOLD.<pid>.json`, writes no record and still uses the default request path; an old hold script
   writes `HOLD`, which new runs ignore (its mutex still holds). Stop and requeue them.
5. **A junction left by a run that died before 77c22e6** has no record. A later run that uses the same folder finds
   it "existing" and leaves it. Look once at `Documents\Timberborn\Mods` for `pbgate-*` and other proto links.
6. **Two `-DuringHold` runs started in the same instant** can both pass the "no record" check. One hold session
   should start one at a time.
7. **`-Visible`** still goes by start time and cannot tell the owner's game from the test's; unchanged, and still
   never to be used while the owner is at the PC.
8. **`-DryRun`** still queues for the lock, rebuilds the harness and makes and removes the junctions (and now the
   record). It launches nothing.
9. **The look pairing check** (commit time, no slack, old meshes with a new bundle pass) and the `build.ps1`
   header are as in round 1; not part of this round.
10. **A hung clean-up.** If the recorded game cannot be stopped, or another Timberborn is open, the clean-up stops
    before the flags and the record stays; runs refuse to start until it succeeds. That is intended, and it means a
    dead run plus an owner who plays for hours holds the queue (with a message naming the pid).

## CLAUDE.md lines these changes make untrue

* Install discipline: install now takes the test lock itself (no wait; refuses and names the holder) and refuses
  while Timberborn runs; with the queue held by the caller, pass `-CallerHoldsLock`.
* The gate: the copy is `proto/foundation/build.ps1 -Name pbgate-<hash8> -Source <StageDir> -Staged` (the staged
  files as they are, only `manifest.json` replaced); the gate file also has the code hash, the game version, the grid
  hash and the loaded mods; install refuses a gate from another game version; an override is logged after
  validation; `gate -Prune`.
* Holding the queue: the file is `E:\PandabornDev\build\test\HOLD.<pid>.json`, one per holder; release with
  `tools\game_test_hold.ps1 -Release` (or delete that file); while a hold is in force queued runs do not try for
  the lock.
* The request: a hidden run writes `<run>\request.in.json`; `E:\PandabornDev\build\test\request.json` is used by
  `-Visible` only.
* `-KeepInstalled` keeps the harness junction only.
* New: `run.pending.json`, `-Recover`, `tools/game_lock.ps1`, `tools/tests/game_lock.trial.ps1`.

## Needs a game run

In this order; each step assumes the ones before it passed. Background processes, owner away, never from a shell
call with a timeout. Step 0 needs no game.

0. No game needed. The trials, again, on the machine as it is; then the code stage with its tests (it rebuilds
   `E:\PandabornDev\build\code\PandabornFactions`, so not while another lane is assembling):
   `powershell -ExecutionPolicy Bypass -File tools\tests\game_lock.trial.ps1 -Scratch $env:TEMP\pbtrial`
   `powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 code`
1. A plain hidden run (the record is written and removed, the request is found in the run folder, pid and start
   time tracking, the desktop handle). Afterwards `E:\PandabornDev\build\test` has no `run.pending.json` and no
   `request.json`, and `<run>\request.json` (the harness's copy) exists:
   `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Folktails -RunSeconds 30`
2. Flags, an extra mod, two launches, window prefs. Afterwards: every value in `<run>\modstate.restore.json`
   matches, no `modstate.pending.json`, no `run.pending.json`, no `Mods\pbfoundation`, no `Saves\PB_AutoTest_*`:
   `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -DisableMods JigglyPanda.PandabornFactions -ExtraMods E:\PandabornDev\build\proto\pbfoundation -SaveAndReload -RunSeconds 30`
3. **The killed runner** (the registry half of the clean-up, which no trial covers). Start step 2's command with
   `-RunSeconds 300` in its own console; when it prints "hidden desktop ... pid", end the runner:
   `Stop-Process -Id <runner pid> -Force`. Check that `run.pending.json` lists the game, both junctions, the save
   and the flag file. Then:
   `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Recover`
   Expect: the test game stopped, flags "restored and verified", both junctions removed, the save deleted, window
   prefs put back, "Nothing of a dead run is left", and neither pending file afterwards.
4. Holds. Window 1: `powershell -ExecutionPolicy Bypass -File tools\game_test_hold.ps1`. Window 2, once window 1
   says "Holding": `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Folktails -RunSeconds 30`
   (must print "The queue is held" and wait). Window 3:
   `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Folktails -RunSeconds 30 -DuringHold`
   (must run). Then `powershell -ExecutionPolicy Bypass -File tools\game_test_hold.ps1 -Release`: window 1 ends,
   window 2 runs. Last, close a holding window with its X instead of releasing: a queued run must start (the stale
   `HOLD.<pid>.json` disappears), and `-DuringHold` must refuse.
5. The owner's launcher (needs the owner): with a test queued,
   `powershell -ExecutionPolicy Bypass -File tools\play_timberborn.ps1 -NoLaunch`; start and close the game; the
   queued test starts only afterwards. Once more while a test is in the game, pressing S: only that test's game
   ends, and the test reports "could not test".
6. The owner starts the game from Steam during a run (needs the owner; open item 1). Start
   `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -OnlyMods JigglyPanda.PandabornFactions -RunSeconds 300`,
   start Timberborn from Steam about 10 s after "hidden desktop ... pid", look at the mod manager (are the owner's
   mods shown on?), close the game. Expect exit 2, two restores in the log, no test in the owner's window.
7. Ctrl-C in the console during step 2's command: the game dies, the flags come back, the junctions and the record
   go. (A second Ctrl-C during the clean-up cuts it short; then step 3's `-Recover`.)
8. **The gate on the staged code** (does a copy with the dev Id and the staged, filtered modules load and pass?).
   Needs a current stage (`pandaborn.ps1 pin,models,generate,code,bundles,assemble,validate`):
   `powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 gate`
   Then read `E:\PandabornDev\build\stage\PandabornFactions.gate.json`: `devCopy.substitutions` has `manifest.json`
   only, `gameVersion` is 1.1.2.8 and equals `gameVersionReported` up to the game's own suffix, `modsLoaded` has the
   dev copy and not `JigglyPanda.PandabornFactions`, `modulesOn` is the staged module list. A gate that fails with
   "<module> is off" is the boot-report rule doing its work: read the reason it prints.
9. Install with the lock, both ways. Free lock: `powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 install`.
   Held by the caller: `powershell -ExecutionPolicy Bypass -File tools\game_test_hold.ps1` in a second window, then
   `powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 install` (must refuse and name the hold), then
   `powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 install -CallerHoldsLock` (must install), then
   `powershell -ExecutionPolicy Bypass -File tools\game_test_hold.ps1 -Release`.
10. Old copies: `powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 gate -Prune -DryRun` (lists; removes
    nothing). Whether each copy also left a registry value:
    `reg query HKCU\Software\Mechanistry\Timberborn /f pbgate`.
