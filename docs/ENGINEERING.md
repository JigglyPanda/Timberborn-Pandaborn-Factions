# Engineering rules

Adopted 2026-11-14 from the maintainer review (`docs/reviews/2026-11-14-maintainer-and-scope.md`). These rules
exist because the commonest way a faction mod dies is a game update, and because several kinds of mistake in
this mod's data would crash *every* game, Folktails included.

**Status marks, added 2026-11-25.** The rules are unchanged in intent. Each section now ends with where reality
stands: **done** (exists and proven in a game run, run named), **built** (exists, not proven in game or only on a
dev copy), **partly**, **not done**. The runs still owed are in
[docs/tech/needs-game-run.md](tech/needs-game-run.md), under the ids given here (G1, C2, ...). Run folders are in
`E:\PandabornDev\build\test`.

## How the game punishes mistakes

| Mistake | What happens | Where |
|---|---|---|
| A blueprint names a spec the game does not know | Exception when that blueprint is first read. Goods, needs, recipes, worker types, decals, outfits, collections and the faction file are read in every game | All games |
| A field name is wrong or was renamed | Nothing. The field silently keeps its default: a free building, a zero yield, a plant that never dies | Silent |
| A need or need collection is not used by an installed faction | Exception | All games |
| Two recipes, templates or spec classes share a name, across all mods | Exception | All games |
| An asset bundle fails to load | Exception | All games |
| A DLL has a type that cannot load (renamed game type, absent optional mod) | Every mod's loading stops | All games |
| The mod is removed and a faction save is opened | The game warns, then fails on the missing faction | That save |

Learned since (all verified in game on 2026-11-14, details in `CLAUDE.md`):

| Mistake | What happens | Where |
|---|---|---|
| A model lacks a node its basis's code looks up (a progress stage, an animated part) | Exception when the building is placed or finished, not when the game loads | Inkpaws games; this is why the install gate places and finishes every template |
| The same asset bundle in two enabled mods (a dev copy beside the installed mod) | Exception at load | All games |
| A bundle built before the meshes that use it, or the reverse (look sheet regions, plant detail regions) | No error: lanterns that never glow, wrong masks on leaves | Silent; `assemble` compares build times with git |
| A faction modifier file named like a normal blueprint | It is indexed as a blueprint of its own | All games |

## Ids are frozen forever

| Thing | Rule |
|---|---|
| Manifest Id | `JigglyPanda.PandabornFactions` |
| Faction Id | `Inkpaws` (it is written into every save) |
| Templates | end in `.Inkpaws` |
| Goods, needs, recipes, worker types, collections, loc keys | begin with `Pandaborn` |
| Spec classes | `Pandaborn…Spec` |
| Save keys | begin with `Pandaborn.` |
| Asset bundles | `pandaborn<part>_win` / `_mac`, never renamed after the build |
| Asset paths | under a `Pandaborn` folder; exact case; forward slashes |

`catalogue/ids.lock.json` is append-only. An id is never deleted or reused. A replacement carries the old id as
a backward-compatible alias, and a retired building keeps an alias so saved instances do not vanish.

Status 2026-11-25:

* **done** for the mechanics: the generator stops on an id that is not in the lock, and `tools/validate.py` checks
  the build against the lock, the lock against its last commit, and the prefixes.
* The bundles are `pandabornlook`, `pandabornplants`, `pandabornsounds` and `pandabornattachments`. (This table said
  `pandabornfactions…` until 2026-11-25; no bundle of that name was ever built.)
* The save keys in use are `Pandaborn.Store` and `Pandaborn.EntityState` (both in Core).
* Permanent aliases that ship: `RingtailAdult.Inkpaws` and `RingtailChild.Inkpaws` on the Inkpaw templates (a save
  keeps its Ringtails as Inkpaws when the module is off), `Stairs.Folktails` on `Stairs.Inkpaws` (the tutorial
  system asks for it by name). The worker type `PandabornRingtail` ships in every build for the same reason.
* Nothing has been released, so no id has yet had to survive a real version change.

## Data rules

1. **Global data stays plain.** Goods, needs, recipes, collections, decals, outfits, worker types and the
   faction file use only vanilla spec types. Our own spec types appear only in templates that are listed
   solely in Inkpaws collections. Inkpaws-only changes to vanilla blueprints (a good's name, a need's rate, a
   building's cost, tutorials) go through `FactionSpec.BlueprintModifiers`, and every modifier file is named
   `<name>.optional.blueprint.json` at a path with no base blueprint: a modifier file named like a normal
   blueprint is also indexed as a blueprint of its own, in every game (verified, docs/tech/stage0.md).
2. **Data alone behaves like vanilla; code only adds.** With every code module switched off, every building is
   still a sensible vanilla building. A feature never replaces a vanilla spec the colony depends on.
3. **Faction blueprints are generated, never hand-edited.** The catalogue names each item's vanilla basis and a
   few transforms (rename, recost, retheme, worker kind, planter group). The generator writes into the build
   folder, deterministically, and stamps each output with its source path and hash.
4. **Every need sits in a collection the faction always lists**, whether or not the feature that uses it is on.
5. **Vanilla functions keep vanilla loc keys** where the game's interface requires them (character labels in
   the batch-control window are one such place).

| Rule | Status 2026-11-25 |
|---|---|
| 1. Global data stays plain | **done**: the validator refuses a custom spec in global data; modifiers are generated as `<name>.optional.blueprint.json` (`catalogue/modifiers.toml`, the poles rename, the tutorial switch-offs). Folktails games with the mod enabled: `catalogue-ft-on`, `p4-fullmods-then-ft-1`, `p5-fullmods-3` |
| 2. Data alone behaves like vanilla | **partly**: proven one module at a time on dev copies (Look `look-module-forceoff-2`, Water `water-w2-0809`, Ringtails `rt2-forcedoff`, Festival and Flowering `events-fallback-4`) and for the data-only `-NoCode` build (`p3-nodata-2`). Not proven: every module off at once on the build that will ship; Bell, Names, Words and Tutorial forced off (run C5) |
| 3. Generated, never hand-edited | **done**: `src/gen`, deterministic, one provenance line per output; `assemble` fails when a generated file lands on a hand-written one |
| 4. Every need in a collection the faction always lists | **done**, with one refinement: there is one collection, `Needs.Inkpaws`, always listed, and the validator applies the game's NeedVerifier rule. A need whose only source is a hidden building is left out of the build with it ("nothing in the toolbar lies"), so "whether or not the feature is on" now means the module's *runtime* state, not its catalogue switch |
| 5. Vanilla loc keys where required | **done**: the validator enforces the three character label keys; every run opens all batch-control tabs |

## Code rules

1. **No Harmony. No required mods.**
2. **Layout:**
   * `Pandaborn.Bootstrap.dll` — only the mod starter. It checks each feature's game references before loading
     it, loads each module once, and records which features are on.
   * `Pandaborn.Specs` and `Pandaborn.Core` — spec records, save carriers, the self-check and notices. Always
     loaded, so a disabled feature's data still reads and is written back unchanged.
   * One module per feature, loaded only if its check passes. A failed check means "feature off, player told",
     never a crash.
   * Built and verified in game: `src/code` (see its README for how to add a module). The bootstrap itself may
     reference only `IModStarter`/`IModEnvironment` and `Debug`; `Pandaborn.Specs` only the blueprint system. A
     dev switch (`pandaborn.dev.txt`: `force-off:`, `simulate-missing-api:`) exercises the off paths.
3. **Each module lists the game types, methods and fields it touches** in a `FEATURE.md`, and the build
   produces that list from the compiled module so it can be diffed against a new game version.
4. **Reflection on private members is allowed only with a written fallback**, and is exercised by a test that
   simulates the member being gone.
5. **Temporary effects never write saved vanilla state.** Use bonuses, behaviours and effects that disappear
   when the code is absent. Bonuses only add (one sum per bonus id); an effect meant to multiply must re-add
   `share = multiplier without it x factor` whenever another bonus of that id changes (`BonusValueChanged`), as
   `Pandaborn.Bell` does. Bonus types clamp (`MovementSpeed` at 2.0 in vanilla).
6. **Our saved data carries a version and is read tolerantly.** Singleton state goes in `PandabornStore` (in
   Core, so it survives saves made while its feature is off). Per-entity state of a feature that can be off
   needs the same treatment: a Core-owned component carrier, not yet built; until then a feature module keeps
   per-entity state out of the save or accepts losing it while off.
7. **Interface fragments are wrapped** so an exception in a panel never breaks the game.

| Rule | Status 2026-11-25 |
|---|---|
| 1. No Harmony, no required mods | **done**: no module references Harmony; the manifest requires nothing |
| 2. Layout | **done**. Ten modules are in `src/code/modules.txt` and switched on in `catalogue/rules.toml`: Bell, Names, Look, Words, Water, Ringtails, RingtailsFallback, Tutorial, Festival, Flowering. The build *installed* on 2026-11-14 has only the first four, the two Ringtail modules and Tutorial: the staged build with all ten has not passed the install gate (run G1). The dev switch also has `simulate-missing-member:` and can be given through the environment variable `PANDABORN_DEV` |
| 3. Each module lists what it touches | **done**: `Pandaborn.ApiScan` rewrites the generated half of every `FEATURE.md` on each build; `tools/check_api_lists.py` compares the lists with the game (a warning in dev stages, a failure for `package`) |
| 4. Reflection only with a fallback and a test | **done** on dev copies: Festival and Flowering (`events-fallback-4`), Ringtails (`simulate-missing-member: Ringtails`, the degraded path), Words (`fd-carrier-1`). To be repeated on the build that ships (run C5). An API check that fails for real can only come from a game update |
| 5. Temporary effects never write saved vanilla state | **done** for what has run: Bell re-adds its share on `BonusValueChanged` (`s0-inkpaws-5`: work 3.8 to 5.054, walk 1.7 to 2.261); Look restores the vanilla materials on unload (`look-module-then-4`); Words restores the vanilla texts (`fd-words-1`). New on 2026-11-25 and never run: the Ringtails' rested bonus (run N1) and the hour-by-hour bell curve (run N2) |
| 6. Saved data versioned and tolerant | **done**. The per-entity carrier that the rule calls "not yet built" was built the same day: `PandabornEntityState` in Core, declared on a template with `PandabornEntityStateSpec { Features [...] }` (`fd-carrier-1`). The Water module keeps gate settings and flume depths in it (`water-w4e-1448`; on the catalogue's own templates `gate-20261114-173036-water_w4_inkpaws`). Bell, Festival, Flowering and Ringtails keep only singleton state, in `PandabornStore` |
| 7. Interface fragments wrapped | **done**: `SafeUi` in Core, used by every module's panels. No test injects an exception into a panel |

## Tooling

| Tool | Does |
|---|---|
| Schema dumper | Writes every game spec class with its serialised fields (public and private) and types to `schema/<game version>.json` |
| Validator | Checks every blueprint key and field against the schema; asset references; ids against the lock file; prefixes; "no custom spec in global data"; material coverage; bundle pairs; need and collection usage |
| Generator | Catalogue to blueprints, localisation and collections |
| Game diff | Between two game versions: changed vanilla blueprints and which of ours they feed, schema, loc keys, assets, each module's touch list, Unity version |
| One command | Pin check, generate, validate, build code, build bundles, assemble, package, test, report |

| Tool | Status 2026-11-25 |
|---|---|
| Schema dumper | **done**: `tools/schema`, output `schema/1.1.2.8.json`; it also dumps our own spec classes for the validator |
| Validator | **done**: `tools/validate.py`, with `--self-test` fixtures and a `--release` mode. Beyond the list above it checks sound names against our bundles, bundle-only assets against the staged bundles, model nodes the basis looks up, and the economy (needs nothing meets, goods nothing makes or uses, shipped modules without data) |
| Generator | **done**: `src/gen`, with the lock, provenance, the report and the grid request |
| Game diff | **built**: `tools/game_diff.py`, with a unit test; never used on a real game update (there has been none since the pin) |
| One command | **done**: `tools/pandaborn.ps1`, stages `pin`, `models`, `generate`, `code`, `bundles`, `assemble`, `validate`, `gate`, `install`, `test`, `package`. The install gate was added after this table was written. `package` has never been run to the end |
| Not in the original list | `tools/balance` (the balance model on the generated build), `tools/playtest_report.py`, `tools/docs/content_tables.py` (the tables of `docs/CONTENT.md`), the dev harness `src/devharness` with `tools/run_game_test.ps1` |

## Repository layout

| Path | Contents | Owner |
|---|---|---|
| `catalogue/` | The source of truth for content, one file per category; `ids.lock.json`; the pinned game version | One file per lane |
| `src/gen/` | Generator and transforms | Tooling |
| `src/code/<Module>/` | One folder per code module, with its `FEATURE.md` | One module per lane |
| `src/pipeline/` | Art generation | Art lanes |
| `art/models/<Id>/` | One folder per model: its script and outputs | One model per lane |
| `mod/PandabornFactions/` | Hand-written data only: manifest, sprites, hand-authored loc | Single owner |
| `tests/scenarios/<feature>/` | In-game test requests | With the feature |
| `tools/` | Build, validate, test, release | Tooling |
| `proto/` | Throwaway prototypes | Their author |

Contributions that many lanes need go in as fragments, never as edits to a shared file: localisation as
`Localizations/enUS_Pandaborn<Feature>.csv`; collection entries as a file per feature (collections join by id);
test scenarios as files.

Status 2026-11-25: **partly**. The layout exists as written, with these differences.

* Test scenarios are split. `tests/scenarios/` holds catalogue, events, grid, look and playtest. The water,
  Ringtail, sound, foundation, model, plant and character scenarios still live in the prototypes that grew them
  (`proto/water/tests`, `proto/ringtails/test`, `proto/sound/tests`, `proto/foundation/tests`,
  `proto/models/tests`, `proto/plants/tests`, `proto/ringtail-body/test`). Those prototypes were meant to be
  thrown away and are now the only home of those scenarios and of the test probes.
* In practice the catalogue has one owner (the catalogue lane), not one file per lane; other lanes hand it
  requests in their own documents.
* Collections are generated whole from the catalogue, not as a file per feature.
* Not in the table: `art/plants/<Id>/`, `src/devharness/` (the test mod), `src/unity/` (bundle projects),
  `schema/`, `tools/docs/`.

## Tests required before a release

* Load to the main menu: alone, with the Reskin, and with a set of popular mods.
* New Inkpaws game on each difficulty, three days, no errors.
* Scripted soak of twenty or more days per difficulty, through a drought: nobody starves, no exceptions.
* Save and reload with counts compared; saves from the previous release still load.
* Grid session: place and finish every Inkpaws building, open every panel, run every recipe, grow and kill
  every plant in each soil state.
* Water probes: flume one-way and sealed, spout depth, lift with and without current, badwater gate.
* Folktails and Iron Teeth compared with the mod on and off: templates, goods, needs, toolbar, character
  meshes.
* Each code module forced off: the game loads, saves load, the notice appears.

Needs the owner's eyes: art quality by day and night, whether the first hour feels cozy, text tone, Mac on
real hardware, store pages.

Status 2026-11-25. **None of these has been run on the build that will ship.** Every proof below was made on
2026-11-14, on that morning's installed build or on a dev copy, before Water, Festival and Flowering were switched
on together and before the balance changes of 2026-11-25. The last column names the backlog run that repeats it.

| Test | Where it stands | Owed |
|---|---|---|
| Load: alone, with the Reskin, with popular mods | **partly**: alone (`20261114-onlymods-inkpaws`, `p5-fullmods-3`), with the owner's 35 mods (`p4-fullmods-days-1`, `p4-fullmods-then-ft-1`), with the Reskin (`rb-p3a`, `rb-p3b`) | C1, C2, C3 |
| New Inkpaws game on each difficulty, three days | **not done** as a set. Normal only, inside the scripted playtests (`pt-ink-std-m3`: 41 days, no errors) | R1 |
| Soak of twenty or more days per difficulty, through a drought | **partly**: Normal 41 days and the careless plan 31 days ran without exceptions (`pt-ink-std-m1`, `-m3`, `pt-ink-care-m1`, `-m3`). The Hard runs failed (`pt-ink-hard-m1`, `-m2`: the scripted plan does not stock up). No run got past 20 colonists | R2, B1, B2 |
| Save and reload with counts compared; saves from the previous release | **partly**: reloads with counts compared on dev copies (`rt2-soak` 16 of 16, `rt3_breed3`, `water-w4e-1448`, `events-main-3`, `rb-p3a` 25 of 25). There is no previous release; the first one sets the save to keep for this test | C4, R3 |
| Grid session | **partly**: every placeable template placed and finished, recipes on, a speed ladder (`gate-20261114-171322`: 167 templates on a dev copy of that hour's staged build, all ten modules loaded); plants in each soil state (`plants-states-1`). "Open every panel" is not part of the grid run. Today's staged build has no gate | G1, R4 |
| Water probes | **partly**: all four proven on the prototype's templates (`water-parts-0308`, `water-w1b-0934`, `water-w3-0815`, `water-w4e-1448`). On the catalogue's own templates: the line with a crossing, a spout and a reload (`gate-20261114-173036-water_w4_inkpaws`). The scoop-wheel scenario has never passed on them; badwater shut-off and dew in drought were not rerun under the module | G1, N6 to N9 |
| Folktails and Iron Teeth, mod on and off | **partly**: Folktails on and off (`catalogue-ft-off`, `catalogue-ft-on`), Folktails after an Inkpaws game in one session (`p4-fullmods-then-ft-1`, `sound-4`), Iron Teeth once, on the first day (`20261114-010054-ironteeth`). Not since ten modules ship | C1, C3 |
| Each code module forced off | **partly**: Look, Water, Ringtails, Festival and Flowering, one at a time, on dev copies. Not Bell, Names, Words, Tutorial; not all at once | C5 |
| The owner's eyes | **not done**: nothing has been looked at or listened to by the owner. The sounds wait at `E:\PandabornDev\build\sound\index.html`, and `sound_id` stays `"Common"` (beaver calls) until the panda calls are approved | O1 to O6 |

## Distribution

* One supported game version. `version-X.Y` folders only for an emergency, always with a floor folder.
* Large binaries stay byte-identical between releases so updates stay small.
* Windows and Mac bundles are both built on every build; Mac is labelled community-tested until someone tests
  it on real hardware.
* Removing the mod breaks Inkpaws saves. The store page says so plainly.

| Item | Status 2026-11-25 |
|---|---|
| One supported game version | **done**: pinned to 1.1.2.8 (`catalogue/vanilla.pin.json`); the build refuses a game that differs from the pin. No `version-X.Y` folder exists or is needed |
| Large binaries byte-identical between releases | **not done**: nothing checks it and there is no release to compare with. Bundles change only when a lane rebuilds one by hand |
| Windows and Mac bundles on every build | **partly**: every bundle has a `_mac` twin, built on this machine from a private editor copy (`docs/tech/mac.md`) by a separate `-Mac` run of each bundle script, not by the one command. `validate --release` refuses a missing twin. `pandabornattachments` needs rebuilding (both twins) for the rising-lantern rework. Nothing has been loaded on a real Mac |
| The store page says removing the mod breaks saves | **built**: `README.md` (being written on 2026-11-25) says so; no store page is published |
| AI disclosure (a project rule, not in this list) | **built**: in `README.md`; to be repeated on the Workshop and mod.io pages |
