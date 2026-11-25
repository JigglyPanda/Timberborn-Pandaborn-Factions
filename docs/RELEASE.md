# Release checklist

What must be true, in order, before Pandaborn - Factions is published on the Steam Workshop and mod.io. Derived
from [ENGINEERING.md](ENGINEERING.md) ("Tests required before a release", "Distribution"), the `package` rules in
`CLAUDE.md` and `tools/pandaborn.ps1`, and the technical notes.

Status is as of **2026-11-25**, taken from the documents, not from new runs: no game could be started that day.
The in-game runs each step owes are listed once, in order, with commands, in
[tech/needs-game-run.md](tech/needs-game-run.md). This page names its items (G1, C2, N6 and so on) and does not
repeat them.

**Where it stands in one paragraph.** Nothing is published. The manifest says `0.0.1`. The catalogue has every
feature switched on. The build that was last installed (2026-11-14) is older: it has no
water toolkit, festival or flowering. No staged build with everything on has passed the install gate, and none of
the release tests has been run on such a build. The balance numbers changed on 2026-11-25 with no run behind
them. So the next step is step 2 below, and everything after it is open.

Legend: **done**, **partly**, **open**, **owner** (waits for a decision or for the owner's eyes and ears).

## 1. Freeze what ships

| # | Item | Status | Notes |
|---|---|---|---|
| 1.1 | Module switches final in `catalogue/rules.toml [modules]` | **done** in the catalogue | Bell, Names, Look, Words, Water, Ringtails, RingtailsFallback, Tutorial, Festival, Flowering on. The Star Tower ships with the Ringtails since 2026-11-25 |
| 1.2 | Decisions of 2026-11-25 in the catalogue and the code | **partly** | In: shelves, water science, well-being trims, pickles, the ox, the bell's taper, the Ringtails' rested bonus, the Star Tower as a night post, steamed seed cakes, the players' switch file. Not yet: the returning Ringtail family. None of it has a game run behind it. `docs/DESIGN.md` change log is the list |
| 1.3 | Player-facing text final, and every description true of the data | **open** | A text pass is in progress in `catalogue/text/` (uncommitted on 2026-11-25). When it lands, read each description against the catalogue; `docs/tech/audit-2.md` lists the contradictions the second audit found |
| 1.4 | Colonist names checked by a native speaker of Mandarin | **owner** | `catalogue/text/names.json` says so itself. Until then the store pages say the names are unchecked |
| 1.5 | Documents regenerated: `tools/docs/guide_tables.py`, `tools/docs/content_tables.py`, `tools/docs/store_pages.py`, each with `--check` | **done** for today's catalogue | Rerun after any catalogue change |

## 2. Build and gate

One command per stage: `powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 <stage>`.

| # | Stage | Must pass | Status |
|---|---|---|---|
| 2.1 | `pin` | The vanilla dump equals `catalogue/vanilla.pin.json`. The Words table check passes (a failure for `package`) | **done** for game 1.1.2.8; rerun on the day |
| 2.2 | `models` (with `-Plants`) | Every `art/models/<Id>/build.py` and plant builds | **partly**: built on 2026-11-14. Needs Blender; no art job could run on 2026-11-25 |
| 2.3 | `generate` | Deterministic output; new ids locked with `-Lock` | **done** on each catalogue change |
| 2.4 | `code` | `src/code` builds; `tools/check_api_lists.py` clean (a failure for `package`); every shipped module's data switch agrees | **partly**: builds; the Ringtails' rested bonus is new code with no run |
| 2.5 | `bundles` | Every `pandaborn*` bundle present as `_win` **and** `_mac`, never renamed: look, plants, sounds, attachments | **partly**: all four exist in both forms. `pandabornattachments` must be rebuilt for the rising lanterns (needs Unity) |
| 2.6 | `assemble` | Paired changes hold: the look bundle is newer than `src/pipeline/sheet_regions.json`; the plants bundle and adopted plant meshes are newer than `art/plants`. No `AssetBundles.parked` | **open** for the build that will ship |
| 2.7 | `validate` with `--release` | No errors: schema, asset references, ids and lock, no custom spec in global data, need and collection use, bundle pairs with equal contents, and the economy rules (no need nothing meets, no good nothing makes or uses, no two buildings on one toolbar slot, modules and data agree) | **open** for the build that will ship |
| 2.8 | `gate` (backlog **G1**) | A dev copy of the staged build places and finishes every placeable building in a real game, runs recipes, a speed ladder and three in-game hours with zero errors from our mods; the water line with a reload; the scoop wheels. Writes `<stage>.gate.json` | **open**. The last recorded pass was for a build without water, festival or flowering. On the catalogue's own templates the flume line with a reload passed once (`gate-20261114-173036-water_w4_inkpaws`); the scoop-wheel scenario has not |
| 2.9 | `install` (backlog **G2**) | Only a gated folder. No Timberborn process running; the test mutex held | **open** |

Never use `-GateOverride` for a release.

## 3. The release tests

From ENGINEERING.md. The status column there is the detailed one; this is the summary. None has been run on the
build that will ship.

| # | Test | Status | Backlog |
|---|---|---|---|
| 3.1 | Load to the main menu and into a game: alone, with the Reskin, with popular mods | **partly**, on older builds | C1, C2, C3 |
| 3.2 | A new Inkpaws game on each difficulty, three days, no errors | **open** as a set | R1 |
| 3.3 | A soak of twenty days or more per difficulty, through a drought: nobody starves, no exceptions | **partly**: Normal ran 41 days clean in a scripted playtest; the Hard runs failed | R2, B1, B2 |
| 3.4 | Save and reload with counts compared | **partly**, on dev copies. There is no previous release, so this release's save becomes the one later versions must load: **keep a copy** | C4, R3 |
| 3.5 | Grid session: every building placed and finished, every panel opened, every recipe run, every plant grown and killed in each soil state | **partly**: placing, finishing and recipes are the gate; plants in each state were shown; panels are not opened by the grid run | G1 |
| 3.6 | Water probes: flume one-way and sealed, spout depth, lift with and without current, badwater gate | **partly**: all proven on the prototype's templates; the badwater gate and the dew limiter not re-run in the shipped module | N6, N7, N8, N9 |
| 3.7 | Folktails and Iron Teeth with the mod on and off: templates, goods, needs, toolbar, character meshes | **partly**; not since ten modules ship. Iron Teeth once, on the first day | C1, C3 |
| 3.8 | Each code module forced off: the game loads, saves load, the notice appears | **partly**: Look, Water, Ringtails, Festival, Flowering one at a time, through the test switch. Not Bell, Names, Words, Tutorial. The players' file `PandabornFactions.txt` has never been run | C5 |
| 3.9 | New behaviour of 2026-11-25 | **open** | N1 to N5 |
| 3.10 | Festival and Flowering on the build's own numbers: a real pump crew, Ringtails, the buds, timber bamboo | **open** | N10, N11, N12 |
| 3.11 | The tutorial played through; the Wooden Ox at work; sounds from their natural triggers | **open** | N15, N16, N17 |

## 4. Other mods

From the compatibility audit ([reviews/2026-11-25-mod-compatibility.md](reviews/2026-11-25-mod-compatibility.md)),
which read code and ran no game.

| # | Item | Status |
|---|---|---|
| 4.1 | All of the owner's mods enabled, with every feature on: an Inkpaws game, then a Folktails game | **open**. The clean run with 35 mods predates four features. Until it is repeated, no page says "tested with" (backlog C2) |
| 4.2 | T3MP and Performance Plus together: load, save, reload, a festival day, a Flowering through to the rest, a flume line across a reload, a night shift, speed 7 | **open**. The audit's first priority. Until then the pages say "not tested yet" |
| 4.3 | Moddable Tool Groups with MoreGroups: the Inkpaws toolbar and the tutorial | **open** |
| 4.4 | A second faction mod installed, including one that ships a tutorial | **open**. Until then: "other faction mods: not tested yet" |
| 4.5 | A building pack given the `Buildings.Inkpaws` collection file from the README | **open**. The README says it has not been run |
| 4.6 | The store pages' "Works with" list equals the audit's section 8, with "tested" only where a run exists | **done** as a draft (`catalogue/text/store/`) |

## 5. The Reskin's compatibility update

It should go out the same day. Without it, the most likely pairing of mods shows the wrong portraits for the
Inkpaws and giant-panda fur on Ringtails (`docs/tech/ringtail-body.md` 8.1).

| # | Item | Status |
|---|---|---|
| 5.1 | The change exists: branch `factions-compat` in the Reskin repository, one file, one local commit | **done**, not pushed |
| 5.2 | Tested with this mod: Inkpaws keep their coats, Ringtails use their own fur mask, a Folktails game is unchanged (run `rb-p3b`) | **done** on 2026-11-14; repeat on the build that ships |
| 5.3 | Portraits looked at with the compat build. The probe did not photograph them | **open** |
| 5.4 | Reskin version bumped, its README and Workshop text mention the Inkpaws, the new DLL in its `Scripts` folder | **open** |
| 5.5 | Reskin update published to the Workshop, and its release zip refreshed | **owner** |
| 5.6 | If the Reskin update is late: swap the Reskin sentence on the store pages for the "until its next update" one in `known_issues.md` | ready |

## 6. Mac

| # | Item | Status |
|---|---|---|
| 6.1 | Every bundle has a `_mac` twin built for macOS with the same contents as its `_win` twin (`validate --release` compares them) | **partly**: look, plants, sounds and attachments are built and checked on Windows (`docs/tech/mac.md`). Rebuild with the final art |
| 6.2 | A person with a Mac runs the seven checks in `docs/tech/mac.md` ("What only a real Mac can verify"), ideally one Apple Silicon and one Intel machine | **owner**: needs a community tester. Nobody has run the mod on a Mac |
| 6.3 | Until 6.2: the store pages say Mac is built and untested, and the mod.io platform tag is Windows only | **done** in the drafts |

The plants have no fallback on a Mac: if their bundle fails to load, an Inkpaws game does not start. That is the
first thing to ask a tester.

## 7. Only the owner can settle these

| # | Item | Notes |
|---|---|---|
| 7.1 | **Listen to the sounds.** Every clip plays from `index.html` in the sound build folder on the build drive | Nothing has been listened to. The bell, the clapper and the water carry the least risk, the panda voices the most |
| 7.2 | Panda voices on or off | They are made. `sound_id` stays `Common` (the game's beaver calls) until they are approved |
| 7.3 | Look at the art by day and by night, and at the first hour: does it feel cozy | Engineering's "needs the owner's eyes" |
| 7.4 | Read the text in game for tone | |
| 7.5 | The version number | Proposed: `0.1.0`, early access. Reasons in `CHANGELOG.md` |
| 7.6 | A licence | There is no `LICENSE`. The Reskin has none either, so there was nothing to mirror. A draft, `LICENSE.draft.md` at the repository root, is left uncommitted for the owner to accept or change: MIT for the code, and the art, sound and text free to reuse with credit |
| 7.7 | Screenshots | `catalogue/text/store/screenshots.md`: three usable, seven to retake, seven missing. They need a real village and someone to frame them |
| 7.8 | The store text, tags and thumbnail | Drafts in `catalogue/text/store/`. The thumbnail does not exist |
| 7.9 | Whether the GitHub repository is public, since the store pages link to it | |

## 8. Package

| # | Item | Status |
|---|---|---|
| 8.1 | `manifest.json`: `Version` set to the chosen number; `Description` true of the build; `Id` unchanged (`JigglyPanda.PandabornFactions`, never changes); `MinimumGameVersion` right | **partly**: the description was rewritten on 2026-11-25 to match the switches. The version stays `0.0.1` until the owner decides |
| 8.2 | `tools\pandaborn.ps1 package`: runs `validate --release`, `check_api_lists.py` and the Words check, and refuses on any failure; writes the folder and `PandabornFactions.zip` | **open** |
| 8.3 | The package holds no `pandaborn.dev.txt`, no `AssetBundles.parked`, no dev harness, no prototype | Checked by `package` and by hand |
| 8.4 | Unzip the package into an empty `Mods` folder on a clean profile and start an Inkpaws game | **open** |
| 8.5 | Large binaries byte-identical to the last release where unchanged, so updates stay small | First release: nothing to compare. Keep this package |
| 8.6 | `CHANGELOG.md`: move "Unreleased" under the version with the date | **open** |

## 9. Publish

In this order, on one day:

1. Tag the commit and create the GitHub Release with `PandabornFactions.zip`. The repository itself holds no
   meshes or bundles.
2. Publish the Reskin's compatibility update (step 5).
3. Upload to the Steam Workshop. Paste `steam_workshop.bbcode.txt` below its line of dashes, after deleting the
   line of any feature that did not ship. Answer the AI-content question: yes.
4. Upload the zip to mod.io. Paste `modio.html` or `modio.md`, and `summary.txt` line 2.
5. Put both links into `README.md` ("Install") and into each store page.
6. Add the change note from `catalogue/text/store/changelog_first_release.md`.
7. Subscribe from a second account or machine and start an Inkpaws game from the Workshop copy alone. Then
   remove the local copy for good: two copies stop the game when TimberUi is installed.

Commits, pushes of release tags and uploads happen only on the owner's word.

## 10. After release

* Watch reports for the three things no run has cleared: performance mods, other faction mods, Mac.
* On a Timberborn update: do not load the Inkpaws save first. Run `tools/game_diff.py` against the new game,
  review, then `pin -Accept`, rebuild, gate, and publish the update. The store pages already tell players to
  wait for it.
* Every later version must load this release's kept save (3.4).
