# Engineering rules

Adopted 2026-11-14 from the maintainer review (`docs/reviews/2026-11-14-maintainer-and-scope.md`). These rules
exist because the commonest way a faction mod dies is a game update, and because several kinds of mistake in
this mod's data would crash *every* game, Folktails included.

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

## Ids are frozen forever

| Thing | Rule |
|---|---|
| Manifest Id | `JigglyPanda.PandabornFactions` |
| Faction Id | `Inkpaws` (it is written into every save) |
| Templates | end in `.Inkpaws` |
| Goods, needs, recipes, worker types, collections, loc keys | begin with `Pandaborn` |
| Spec classes | `Pandaborn…Spec` |
| Save keys | begin with `Pandaborn.` |
| Asset bundles | `pandabornfactions…_win` / `_mac` |
| Asset paths | under a `Pandaborn` folder; exact case; forward slashes |

`catalogue/ids.lock.json` is append-only. An id is never deleted or reused. A replacement carries the old id as
a backward-compatible alias, and a retired building keeps an alias so saved instances do not vanish.

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

## Tooling

| Tool | Does |
|---|---|
| Schema dumper | Writes every game spec class with its serialised fields (public and private) and types to `schema/<game version>.json` |
| Validator | Checks every blueprint key and field against the schema; asset references; ids against the lock file; prefixes; "no custom spec in global data"; material coverage; bundle pairs; need and collection usage |
| Generator | Catalogue to blueprints, localisation and collections |
| Game diff | Between two game versions: changed vanilla blueprints and which of ours they feed, schema, loc keys, assets, each module's touch list, Unity version |
| One command | Pin check, generate, validate, build code, build bundles, assemble, package, test, report |

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

## Distribution

* One supported game version. `version-X.Y` folders only for an emergency, always with a floor folder.
* Large binaries stay byte-identical between releases so updates stay small.
* Windows and Mac bundles are both built on every build; Mac is labelled community-tested until someone tests
  it on real hardware.
* Removing the mod breaks Inkpaws saves. The store page says so plainly.
