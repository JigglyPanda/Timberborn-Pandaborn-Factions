# Tooling review: the test runner, the hold scripts, the build and the install gate

2026-11-25. A reading review of `tools/run_game_test.ps1`, `tools/play_timberborn.ps1`, `tools/game_test_hold.ps1`,
`tools/pandaborn.ps1`, `tools/build.ps1` and `proto/foundation/build.ps1`. Nothing was launched: no game, no test run,
no hold script, no install, no gate. The Mods folder, the registry and `E:\PandabornDev\build\test` were not touched.
What was run: the PowerShell parser on the edited scripts, and four helper functions pulled out of
`run_game_test.ps1` and exercised in a scratch folder (queue tickets, the UTF-8 read, the process filters, the
`-DuringHold` lock probe on a scratch mutex).

Line numbers are those after the fixes (commit `467b7f5`). "Sure" means sure from reading; anything that needs the
game is in the last section.

## Fixed in 467b7f5

| # | File, line | What went wrong | Sure? |
|---|---|---|---|
| F1 | `run_game_test.ps1` 162-175 | On the hidden desktop, until the first launch had returned a pid, "the test's processes" meant every Timberborn started since the run began (minus 3 s). The clean-up after an early failure (bad `-RequestJson`, registry error, `CreateProcess` failure) and the junction clean-up at the very end would then wait for and kill a game the owner started in those seconds. Now the start-time rule is `-Visible` only; hidden runs go by their own pids and nothing else. | Sure. Tested on the extracted functions. |
| F2 | `run_game_test.ps1` 172-175, 348-349, 878-881 | The "no Timberborn open" check happened once, when the lock was taken. Then came the harness build (10-60 s), the junctions and the flag changes. If the owner started the game in that gap (Steam also restarts the game once at launch, leaving a few seconds with no process), the run changed the mod flags under the owner's starting game and launched a second game; the owner was noticed only 2 s after launch. Same gap between the two launches of `-SaveAndReload`. Now: a check just before any flag changes (exit 2, nothing changed), and a check before every launch. Before a launch, any Timberborn that is not ours counts as the owner's, so the wait-and-restore-again path also runs when our own game never started. | Sure. |
| F3 | `run_game_test.ps1` 931 | The request file sits at the harness's default path (`E:\PandabornDev\build\test\request.json`, `src/devharness/Harness.cs` line 36 and 101), which the harness reads when a game has no `-pbTestRequest` argument. On the owner-abort path the run killed its game, then waited (for as long as the owner played, when flags had been changed) and only then deleted the request. If the test game had not consumed the request yet (the first seconds after launch), the owner's game, with the harness junction still in Mods, would pick it up and run the test in the owner's window. Now the request is deleted first. | Sure of the order; the window is a few seconds. |
| F4 | `run_game_test.ps1` 724, 729, 934 (and 338) | `modstate.json` is written as UTF-8 without a BOM and was read back with Windows PowerShell's default (ANSI). `ConvertTo-Json` does not escape non-ASCII. A mod whose folder name or manifest Id has a non-ASCII character would get a mangled value name on restore: the real flag stays off, a junk value is created, and the check compares the junk with itself and reports "restored and verified", deleting the pending file. Now read as UTF-8. | Sure (shown in scratch). Only bites with a non-ASCII Local mod folder or Id; Workshop folders are numbers. |
| F5 | `run_game_test.ps1` 696-714 | `-DuringHold` skips the lock on the strength of the `HOLD` file alone. That file stays behind when a hold script's window is closed or the process is killed (see L3), and it is written before the hold script has the lock. So with a stale file, or while the hold still waited behind a test that was between two launches, a `-DuringHold` run started with no lock next to a real run: two games, two sets of flag changes, one pending file. Now it also needs the lock to be taken and the holder file to name a live `HOLD` process. `play_timberborn.ps1`'s own call (restore under its hold) still passes. | Sure. Probe tested on a scratch mutex (free, held by another process, abandoned). |
| F6 | `run_game_test.ps1` 598-600 | A waiter deleted any queue ticket it could not parse, including one another waiter was writing at that instant. The loser then never finds its own ticket and counts every other waiter as ahead of it. Unreadable tickets younger than 30 s are now left alone. | Sure; rare. Tested. |
| F7 | `run_game_test.ps1` 999-1000 | `HiddenDesktop.Close()` was never called. With `-File` the process exit closes the handle; called with `&` from a session (as CLAUDE.md says for `-Checks`) the handle on the empty desktop stayed until that session closed. | Sure; harmless but a leak. |
| F8 | `pandaborn.ps1` 424-430 | CLAUDE.md: "run `install` only when no Timberborn process runs". The stage did not look. A running game holds the mod's bundles open, so the mirror stops half way with part of the tree new and part old; a test game loading the folder during the mirror reads a mix. Now install refuses while any Timberborn process is open. This does not replace taking the lock (see G3). | Sure. |
| F9 | `pandaborn.ps1` 446 | The override log had the time and the reason only. It now also has the stage hash and the user, so a line can be matched to what was installed. | Sure. |
| F10 | `play_timberborn.ps1` 63-67 | When a test had left mod flags changed and the restore could not be confirmed, the script printed the red warning, then "your mod settings are as you left them" in green, and started the game through Steam with the test's mod settings. Now it stops there. | Sure. |
| F11 | `pandaborn.ps1` 38 | Help said `all` has no gate; it has. | Sure. |

## Left as they are

Ranked. None is small, local and certain at once; each says why.

### 1. The owner's machine left changed

**L1. A killed runner leaves everything behind, and nothing records the junctions.** `run_game_test.ps1`, whole main
block. All clean-up is in `finally`. Ctrl-C runs it; closing the console window, `Stop-Process`, a tool timeout that
kills the process, a reboot or a power cut do not. An agent's foreground shell call is killed after at most ten
minutes, while a run can wait 30 minutes and a gate run 3 hours plus 70 minutes of game: any runner not started in the
background ends this way. What stays:
* the test game, alive on the hidden desktop, with no window anywhere (not after a reboot). It usually quits by
  itself when the harness finishes. If it hangs, every later run takes over the abandoned lock, sees a Timberborn
  process and waits its full `-WaitForGameSeconds`, then exits 2; the owner cannot see the game and has to end it in
  Task Manager. `play_timberborn.ps1` does kill it (line 57-58);
* the mod flags, changed. `modstate.pending.json` blocks later runs and `play_timberborn.ps1` restores it, but a game
  the owner starts from Steam directly runs with the test's mod set (with `-OnlyMods`: every other mod off; in a gate
  run: the installed faction off and a dev copy on);
* the junctions: `PandabornDevHarness` and every `-ExtraMods` junction. `play_timberborn.ps1` removes the harness one
  only. An extra junction is then permanent: the next run that uses the same folder finds it "existing" and never
  adds it to its removal list (line 781), and no other run looks at it. When no flag had to change, there is not even
  a pending file to say that a run died. A proto copy left enabled next to the installed faction is the
  "second enabled copy" case of CLAUDE.md;
* `request.json` if the game had not consumed it (valid for `-TimeoutSeconds` + 120 s; over an hour for gate runs),
  the `PB_AutoTest_<run>` save, the holder file, the queue ticket (the last two are harmless and are cleaned by the
  next run), and the window size prefs if the orphan game exits normally (the owner's next game opens 1280x720
  windowed).
Sure from reading. Proposal: write one `run.pending.json` at the start with the game pid and start time, the junctions
created and the settlement name, next to the flag state; let the next lock holder and `play_timberborn.ps1` clean from
it (kill that pid if it is still the same process, remove those junctions, delete that save). Put the request in the
run folder instead of the default path (the path is passed on the command line anyway). This is a restructure, so it
was not done.

**L2. The owner starts Timberborn during a run that changed flags.** `run_game_test.ps1` 402-406, 932-943. The run
kills its game within 2 s, restores the flags, waits for the owner's game to close and restores again. Whether the
owner's game already read the test's flags depends on when Unity loads PlayerPrefs; if it did, the owner sees the
test's mod set in that session (the mod manager shows it), and anything the owner changes in the mod manager for a
recorded mod is overwritten by the second restore. Cannot be decided by reading. Using `play_timberborn.ps1` avoids
it; starting from Steam does not.

**L3. The `HOLD` file is left behind.** `play_timberborn.ps1` line 11 says closing the window early is safe; the
`finally` that deletes `HOLD` does not run when a console window is closed. `game_test_hold.ps1` never deletes `HOLD`
itself, so Ctrl-C or a kill leaves it. Effects of a stale file: waiters behind a running test no longer time out
(line 648 keeps pushing the deadline), and before F5 `-DuringHold` was open to anyone. Tests still start (the lock is
free), which is why F5 could not simply make waiters obey the file. Proposal: put the holder's pid and start time in
`HOLD` and treat a file whose holder is gone as absent. Sure.

**L4. `-KeepInstalled` also keeps the `-ExtraMods` junctions** (line 781), enabled, in the owner's Mods. CLAUDE.md
describes it for the harness only ("inert without a request"); an extra mod is not inert. Sure.

**L5. Gate copies pile up.** `pandaborn.ps1` 376: one full copy per staging hash in `E:\PandabornDev\build\proto`.
Today six `pbgate-<hash>` folders, about 500 MB each, plus the older `pbgate`. Nothing deletes them. Whether the game
also leaves one `ModEnabled.Local.pbgate-<hash>...` registry value per copy needs a look after a gate run. Sure of
the folders.

**L6. Pid reuse.** `run_game_test.ps1` 165, 174: pids are compared without start times. If the test game exits and a
game the owner starts in the same run gets the same pid, it is taken for the test game and killed at the end. Very
unlikely. Sure of the logic.

**L7. Mirror targets are not guarded.** `pandaborn.ps1` `Sync-Tree` (132-146) makes the target an exact mirror and
deletes everything else in it; `-InstallDir`, `-StageDir`, `-PackageDir` and `build.ps1 -BuildDir` take any path.
`proto/foundation/build.ps1` 33-40 deletes `E:\PandabornDev\build\proto\<Name>`; `-Name ''` or `-Name ..\x` clears the
whole proto folder or a folder outside it. Operator error only, but one typo. Proposal: refuse a target outside
`E:\PandabornDev\build`, and a `-Name` that is not `[A-Za-z0-9._-]+`. (The second file is outside what this review
could edit.) Sure.

### 2. Races

**R1. A queued run can beat a hold to the lock.** `run_game_test.ps1` 621-623 tries for the mutex whatever `HOLD`
says; the file only stops the clock. The hold scripts sit in a blocking wait almost all the time, so they nearly
always win when the run in progress ends; a poller wins only if it polls in the instant between two of their waits.
Then a second test starts while the owner waits "for the test in progress". Rare. See L3 for why the simple fix is
wrong today.

**R2. Two holders share one file.** `play_timberborn.ps1` and `game_test_hold.ps1` both write and both end on the
same `HOLD`. Agent holds, owner runs the play script: the owner waits (pressing S does nothing) until the agent
deletes `HOLD`. Owner plays, agent starts a hold meanwhile: when the owner's game closes the play script deletes
`HOLD`, and the agent's hold ends with "Hold released before it started" (line 25); the agent believes the queue is
held. Sure.

**R3. Two gates on the same staging content share a copy.** `pandaborn.ps1` 376-377 with
`proto/foundation/build.ps1` 36-40: the name comes from the hash, and the build starts by deleting the folder. A
second `gate` on unchanged content while the first is in the game deletes the first's files under the running game
(until it hits a locked bundle and stops). Both gates then fail or the first crashes. It cannot produce a wrong pass.
Sure.

**R4. `play_timberborn.ps1` line 57-58 kills every Timberborn without a window** once it has the lock. A game of the
owner's that is still starting has no window yet. Only if the owner started the game and the script within seconds
of each other. With `-MutexName` set for testing the kill is skipped, but the script still writes the real `HOLD`,
restores the real pending file and removes the real harness junction (line 68-72), which breaks a test that is
between "junction made" and "game launched". Sure.

**R5. The deadline drifts during a hold.** Line 648 adds 5 s per loop; a loop takes 5 s plus the queue scan, so
"held time does not count" loses some tenths of a second per loop: minutes over a three-hour hold. Sure; minor.

### 3. Not what CLAUDE.md says

* **`-DryRun` "prints the plan without changing anything."** It launches nothing, but before printing it queues for
  the lock (up to 30 minutes), rebuilds the harness, makes a run folder, and creates and removes the harness and
  extra-mod junctions in Mods (line 868, after 769-783). It was not run in this review for that reason.
* **"`gate` builds the copy (`-Name pbgate -Source <StageDir>`)."** The name is `pbgate-<hash8>`, and the copy is not
  the staging folder (G1).
* **"Take the test mutex for install."** The stage does not; F8 only refuses while a game is open (G3).
* **"`-KeepInstalled` keeps it"**: also the extra mods (L4). **"Removes the junctions it created on every exit
  path"**: not when killed, and never one it found already there (L1).
* **`bundles`, "planned: `E:\PandabornDev\build\characters\attachments`."** It is already in the default
  `-BundleDirs` (`pandaborn.ps1` 67-68).
* **Paired change, look.** `assemble` refuses a look bundle older than the last *commit* of `sheet_regions.json`
  (303-314). It does not see an uncommitted edit of that file, has no slack (a bundle built just before the commit
  that it belongs to is refused; plants get an hour), and does not check the other half: old meshes with a new bundle
  ("pale lanterns") pass, unless the `models` stage ran. Plants check both halves.
* **`tools/build.ps1`** header lists five stages; it runs seven (code and bundles too). It has no gate stage, so its
  install passes only when a gate file for exactly this content already exists.

### 4. The install gate

**G1. The gate does not test the code that gets installed.** `pandaborn.ps1` 375-377 hashes the staging folder,
then `proto/foundation/build.ps1` builds the copy: it leaves out everything the code build contributes
(`Scripts\`, `Modules\`, the look bundle, line 58) and puts in a fresh build of `src/code` from the working tree at
that moment (45-51, 66), with the unfiltered `modules.txt` (Water, Festival, Flowering load in the gate although the
staged mod leaves them out), the DevCarrier module, the fragments of `proto/foundation/mod` merged into the faction
and character blueprints, a dev tutorial, a probe DLL, and the sound bundle taken again from the sound lane's folder
(79-80). The gate file then vouches for the staging hash. So:
* the staged DLLs are never loaded by the gate. The `code` stage and the gate build are minutes apart in `all`, and
  other lanes edit `src/code` all day: staged code and gated code differ whenever a commit or an unsaved edit lands
  in between;
* a crash that only the filtered module list has (a shipped module that needs a left-out one) cannot show;
* blueprints, models, plants and their bundles are the same files, so the gate does what it was made for (adopted
  models that crash once built).
Sure. Proposal: an option on the foundation build that takes the staged `Scripts`, `Modules` and bundles as they are
and changes only the manifest Id; or at least compare the fresh build's files with the staged ones and fail the gate
on a difference.

**G2. What the hash covers.** Every file of the staging folder (relative path lowercased, SHA-256), except
`AssetBundles.parked`. Checked before the run and again after it (417), and again by install (434-438): a stale
gate file cannot let changed content in. Not covered: the game version (a pass from before a game update still
counts; `pin` catches it only when it is among the stages), the grid request (read from `<gen>.grid.json`, which a
later `generate` may have changed or emptied), and the other mods that were on during the run.

**G3. Between the gate and the mirror.** The gate's run releases the lock; install starts without it. The next queued
test needs 5 s to notice and then builds its harness, so install usually finishes its hash first, but the mirror can
overlap that test's game loading the installed folder. F8 catches a game already open, not one that opens during the
mirror. Install also hashes, then builds its file list, then copies: a second lane assembling in those seconds gets
partly installed under the old gate. Proposal: install takes `Global\PandabornGameTest` for the mirror (and accepts
a hold that the caller owns, by the holder file), and compares the hash of the installed folder with the gated one
afterwards. Not done: the present way to "take the mutex for install" is a hold from another process, and a plain
wait on the mutex inside install would deadlock with it.

**G4. Override.** Logged before validation, so a line can stand for an install that validation then refused. With
`all` an override never applies (a failed gate stops the run before install); it only works when `gate` is not among
the stages. No override without a reason is possible. Sure.

## Checked and found sound

* Flag changes: prior values on disk (run folder and pending file) before the first write; only recorded values are
  written; restore deletes values that did not exist; restore runs after our game is gone; the pending file goes only
  after a verified restore; a non-DWORD value is refused before anything changes.
* Junction removal checks type and target and removes the link only (`Directory.Delete`, non-recursive).
* Save deletion: only the folder named exactly `PB_AutoTest_<run id>`. No scenario file in the repo overrides
  `settlementName`.
* Abandoned lock: taken over in all three scripts; `exit` inside `try` runs the `finally` blocks; the mutex is used
  from one thread (Windows PowerShell runs STA).
* `Sync-Tree` for install never follows the Mods junction; the junction code refuses a real folder.
* `break` and `continue` inside the stage `switch` end the stage as intended; a failed stage stops the run (501).

## Needs a game run

None of these was run. All take the real lock; run them when the owner is away, in the background, not from a shell
call with a timeout.

1. The fixes did not break a plain run (pid tracking, the new checks, the desktop handle):
   `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Folktails -RunSeconds 30`
2. Flags, an extra mod and two launches; afterwards `modstate.restore.json` must show every value matching, no
   `modstate.pending.json`, no `Mods\pbfoundation`, no `Saves\PB_AutoTest_*`:
   `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -DisableMods JigglyPanda.PandabornFactions -ExtraMods E:\PandabornDev\build\proto\pbfoundation -SaveAndReload -RunSeconds 30`
3. `-DuringHold` with a real hold. Window 1: `powershell -ExecutionPolicy Bypass -File tools\game_test_hold.ps1`;
   window 2, once it says "Holding":
   `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Folktails -RunSeconds 30 -DuringHold`
   (must run); then `Remove-Item E:\PandabornDev\build\test\HOLD`. Then create a `HOLD` file by hand with no hold
   script running and repeat the second command: it must refuse; delete the file.
4. The owner starts the game during a run (needs the owner; L2, F2, F3). Start
   `powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -OnlyMods JigglyPanda.PandabornFactions -RunSeconds 300`,
   start Timberborn from Steam about 10 s after "hidden desktop ... pid", look at the mod manager (are the owner's
   mods shown on?), close the game. Expect exit 2, two restores in the log, no `request.json`, and no test starting
   in the owner's window.
5. The owner's launcher end to end (needs the owner): `powershell -ExecutionPolicy Bypass -File tools\play_timberborn.ps1 -NoLaunch`
   while a test is queued; start and close the game; the queued test must start only afterwards.
6. Ctrl-C in a console during run 2: the game must die, the flags come back, the junctions go. A second Ctrl-C
   during the clean-up is expected to cut it short (then: `-RestoreModState`).
7. Registry litter (L5): `reg query HKCU\Software\Mechanistry\Timberborn /f pbgate` before and after
   `powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 gate`.
8. Gate then install with the new refusal, queue held by the caller:
   `powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 gate`, then
   `powershell -ExecutionPolicy Bypass -File tools\game_test_hold.ps1` in a second window, then
   `powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 install`, then delete `HOLD`.
