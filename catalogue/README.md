# The catalogue

The source of truth for everything the Inkpaws add to the game. Nothing under `mod/PandabornFactions/` or the build
folder is written by hand except the manifest, sprites, coat textures and hand-authored loc: **author content here
and run the generator.**

```powershell
powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 all              # pin, models, generate, code, bundles, assemble, validate, gate, install
powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 generate,assemble,validate   # the loop while editing here (no game)
powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 combos           # every module combination, release rules (no game)
powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 generate -DryRun  # what would change, with diffs
powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 generate -Lock    # after adding a new id (see "Ids")
powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 test              # grid scenario: place and finish everything
```

## Files

| File | Holds | Generated into |
|---|---|---|
| `faction.toml` | the faction file, characters, bot, shaft parts, decal and outfit copies | `Factions/`, `Characters/`, `Decals/`, `WorkerOutfits/`, `TemplateCollections/` (all under `Pandaborn/`) |
| `buildings.toml` | every building, one line each; the template collection `Buildings.Inkpaws` in this order | `Buildings/Pandaborn/<group>/<Id>/<Id>.Inkpaws.blueprint.json` |
| `building_stats.toml` | the balance numbers of buildings (cost, science, workers, storage capacity), imported from the stat sheet; merged into `buildings.toml` items (a field set in both is an error) | (used by buildings) |
| `archetypes.toml` | named defaults for wholly new buildings (workshop, dwelling, attraction...) | (used by buildings) |
| `goods.toml` | new goods + the good collection `Goods.Inkpaws` | `Goods/Pandaborn/`, `GoodCollections/Pandaborn/` |
| `needs.toml` | new needs + the need collection `Needs.Inkpaws` | `Needs/Pandaborn/`, `NeedCollections/Pandaborn/` |
| `recipes.toml` | recipes | `Recipes/Pandaborn/` |
| `plants.toml` | crops, trees, bushes + the collection `NaturalResources.Inkpaws` | `NaturalResources/Pandaborn/` |
| `rules.toml` | rules applied to everything: template suffix, the pole decision, cost substitutions | |
| `text/*.json` | all player-facing English (writers' lane); the generator writes `Localizations/enUS_Pandaborn<Kind>.csv` from it | `Localizations/` |
| `ids.lock.json` | every id ever generated; append-only | |
| `vanilla.pin.json` | the game version, Unity version and vanilla dump hash the catalogue was derived against | |

Each output also gets a line in `E:\PandabornDev\build\gen\PandabornFactions.provenance.json` (vanilla source path and
its sha256, catalogue item, output sha256); `.report.json` lists stand-ins, missing icons and code needs; `.grid.json`
is the grid test request.

## Why TOML

* **Comments.** Provenance of a number ("M q3", "V (Carrot)", "settled by the owner") and the reason for a choice sit
  next to it. JSON has no comments, and blueprint JSON may not carry extra keys (every top-level key is read as a spec).
* **One item per line or block**, so a diff shows exactly what changed and two lanes rarely touch the same lines.
* **No indentation rules and no implicit types.** YAML's `no` = false, `1.10` = 1.1 and tab/space traps are exactly
  the silent mistakes this project exists to avoid. TOML values are explicit.
* **Standard library** (`tomllib`, Python 3.11+): no package to install on any machine.

The writers' text stays JSON (`text/`), as it was delivered; it is long prose, keyed by English name, edited in its own
lane.

## How an item becomes game data

Every item is **a vanilla basis plus named transforms**. The generator copies the basis blueprint from the vanilla dump
(`E:\PandabornDev\reference\Blueprints`, pinned in `vanilla.pin.json`), applies the fields below, stamps provenance and
writes it. Anything ambiguous stops the run with a message saying what to change: an unknown field, a basis that
does not exist, a building whose basis references a template the Inkpaws lack, a loc key that would overwrite
vanilla text, a duplicate id, a new id not yet in the lock. Output is deterministic (same input, same bytes).

Fields shared by every kind: `basis`, `text` (which entry of `text/<kind>.json`, default: the item id), `icon`, `set`
(`{ "Spec.Field.Sub" = value }` for anything without a shorthand), `add` (`{ Spec = { ... } }` for a spec the basis
lacks), `delete` (`["Spec"]` or `["Spec.Field"]`), `aliases` (old ids that load as this one), `note`, `src`
(provenance of the numbers). The validator then checks every key and field of the result against the game's own
schema, so a typo in `set` is caught too.

## Buildings

```toml
[buildings]
Levee = {}                                         # re-themed: a copy of Levee.Folktails as Levee.Inkpaws
PandabornDen = { basis = "Lodge.Folktails", standin = "art/models/Den" }
PandabornPickleYard = { archetype = "workshop", recipes = ["PandabornPickles"], standin = "art/models/PickleYard" }
```

| Field | Effect |
|---|---|
| (key) | the building id; template name = id + `.Inkpaws` (frozen once locked) |
| `basis` | vanilla template name; default `<Id>.Folktails` (a plain re-theme) |
| `archetype` | defaults from `archetypes.toml` (basis + required specs); the building's own fields win |
| `model` | adopt an art-lane model: `model = "Den"` reads `art/models/Den/model.json` (footprint, blocks, entrance, access, colliders, both meshes, construction base and stage, attachments, anchor, the model's spec additions/removals); the basis defaults to the model's `standIn`. Meshes come from the `models` stage. Water pieces wait for the water module |
| `waits_for`, `needs_code` | the code module(s) this building waits for (`Water`, `Ringtails`, `Festival`...) and what the code does; the building is left out until they ship (see "Modules") |
| `vanilla` | list a vanilla blueprint unchanged in the collection (dev buildings) |
| `text` | entry in `text/buildings.json`; `null` texts there keep the vanilla loc key (already translated) |
| `cost` | `{ Log = 10, Plank = 5 }` replaces `BuildingSpec.BuildingCost` (after `rules.toml` substitutions) |
| `science` | `BuildingSpec.ScienceCost` |
| `workers`, `default_workers`, `worker_type`, `disallow_other_workers` | `WorkplaceSpec` |
| `recipes` | `ManufactorySpec.ProductionRecipeIds` |
| `capacity` | beds, storage units or seats (`DwellingSpec`, `StockpileSpec`, `AttractionSpec`...) |
| `effects` | `{ PandabornNap = 0.6 }`: the need points per hour of an attraction or decoration |
| `needs_map` | `{ DomedGarden = "PandabornTeahouse" }`: retarget the basis's need effects to ours |
| `tool_group`, `tool_order` | toolbar group and position |
| `models` | `{ "#Finished" = "Buildings/Pandaborn/Den/Den.Model" }` per child node |
| `icon` | default for `Pandaborn*` buildings: `Sprites/Pandaborn/Buildings/<Id>Icon` if it exists with a sprite meta |
| `retire` | still loads (saved instances survive) but hidden from the toolbar |
| `standin`, `needs_code`, `retire_when` | notes for the art and code lanes, collected in the report |

Template-name references inside a basis (a tunnel's support platform, a detonator's dynamite) are rewritten to our
copies automatically; a reference to a Folktails template the Inkpaws do not have is an error.

**Worked example: adopting a model.** When the kit writes `art/models/Steamer/model.json`, the Steamer's line becomes
`PandabornSteamer = { model = "Steamer", recipes = [...] }`; `pandaborn.ps1 all` builds the mesh, generates the
blueprint from the model, copies the meshes to `Buildings/Pandaborn/Models/Steamer/`, and the validator checks the
blueprint against `model.json` and the mesh (slot keywords, animated nodes and their drivers). `.models.request.json`
next to the generated folder is a ready test request: every adopted model placed and finished, one copy per model
started so its construction stage shows, and close-ups of both (`tools/run_game_test.ps1 -RequestJson ...`).

**Worked example: a new building.** The Kitchen bakes sweet rice balls and seed cakes on the vanilla bakery until its
own model exists:

```toml
PandabornKitchen = { basis = "Bakery.Folktails", standin = "new model", recipes = ["PandabornSweetRiceBalls", "PandabornBambooSeedCakes"] }
```
Add its English to `text/buildings.json` (`"Kitchen": { "id": "PandabornKitchen", "name": ..., "description": ...,
"flavor": ... }`), drop `Sprites/Pandaborn/Buildings/PandabornKitchenIcon.png` (+ `.png.meta.json` with
`{"isSprite": true}`) into `mod/PandabornFactions`, then `pandaborn.ps1 generate -Lock` and `pandaborn.ps1 all`.

## Goods

```toml
[collection]
id = "Goods.Inkpaws"
vanilla = ["Paper", "Antidote", "Dandelion", "TreatedPlank"]   # kept vanilla goods beyond Common

[goods.PandabornCabbage]
basis = "Carrot"                 # look, container, carrying animation, goods group
good_type = "Box"
weight = 1
consumption = { Hunger = 0.3, PandabornCabbage = 0.2 }
src = "V (Carrot)"
```
Shorthands: `good_type`, `weight`, `group`, `order`, `consumption` (`{ Need = points }`). Names come from
`text/goods.json` (`singular`, `plural`) as `Pandaborn.Good.<Id>.DisplayName/PluralDisplayName`; the icon from
`Sprites/Pandaborn/Goods/<Id>Icon` (or `<Id>sIcon`). `when_poles = "good"` emits the good only in that pole mode.

## Needs

```toml
[needs.PandabornNap]
basis = "RooftopTerrace"         # a vanilla need of the same shape
name_from = "own"                # own (text/needs.json) | good:<id> | building:<id> | key:<loc key>
group = "Fun"
daily_delta = -0.6
favorable_wellbeing = 2
importance = 1.2
wastable = false
```
Shorthands: `group`, `daily_delta`, `favorable_wellbeing`, `unfavorable_wellbeing`, `importance`, `starting_value`,
`maximum`, `wastable`, `order`. Every need lands in `Needs.Inkpaws`, which the faction always lists (NeedVerifier
throws for a need in no collection, in every game).

## Recipes

```toml
[recipes.PandabornSteamedShoots]
basis = "GrilledPotato"
cycle_hours = 0.5
ingredients = { PandabornBambooShoots = 1 }
products = { PandabornSteamedShoots = 2 }
capacity = 30
fuel = "Log"
cycles_fuel_lasts = 10
```
Name and icon follow the first product. Write poles as `Plank` and cured poles as `TreatedPlank`: `rules.toml`
decides what that means.

## Plants

```toml
[plants.PandabornTeaBush]
basis = "BlueberryBush"          # model = stand-in until the growth-stage models exist
planter = "Forester"             # PlantableSpec.ResourceGroup: Farmhouse | Forester | AquaticFarmhouse
growth_days = 6
gather_yield = { PandabornTeaLeaves = 3 }
gather_days = 3.0
wet_days = 3.0                   # the arid rule: dies on moist soil (adds AridNaturalResourceSpec, drops the dry rule)
```
Shorthands: `growth_days`, `plant_hours`, `planter`, `cut_yield`, `cut_hours`, `gather_yield`, `gather_hours`,
`gather_days`, `dry_days`, `wet_days`, `flood_min`, `flood_max`, `flood_days`, `reproduction`, `demolish_hours`,
`models`. Template name = id + `.Inkpaws`. Text from `text/plants.json` (name, description, flavor).

## Faction, characters, decals, outfits

`faction.toml` holds the `FactionSpec` fields by name (`template_collections`, `need_collections`,
`good_collections`, `starting_building` = a building id, ...), the characters as `basis` + `template` + `path` +
`models`, and `[decals]` / `[outfits]` `copy_faction = "Folktails"` (every vanilla decal and outfit of that faction,
re-keyed to Inkpaws).

## Modules: hidden until wired

`rules.toml [modules]` has one switch per code module. A module is on when it ships (`src/code/modules.txt`) and its
switch is on. Any item may carry `waits_for = "<Module>"` (or a list: all must be on): buildings, goods, needs, recipes,
plants, characters, tool groups, modifiers, tutorials, tutorial stages and single tutorial steps. With that module off
the item is left out of the build entirely (nothing in the toolbar lies); its ids stay locked and are marked `gatedBy`.

| Field | Effect |
|---|---|
| `waits_for` | the module(s) the item needs; buildings also say in `needs_code` what the code does |
| `module_specs = { Bell = { PandabornBellSpec = {...} } }` | our own spec classes, added only while that module is on. A list in such a spec never names a good, need or template the build leaves out (the festival's dishes) |
| `module_set = { Festival = { "BuildingSpec.ScienceCost" = 0 } }` | `set` values that apply only while a module is on |

`<gen>.report.json` lists what a build leaves out (`leftOut`) and why. Before committing a change here, run
`tools\pandaborn.ps1 combos`: it generates, assembles and validates (release rules) the full build, the data-only build
and every build with a module or family switched off, in a scratch folder, with no game.

## Shelves, modifiers, tutorial

* `rules.toml [shelves]`: every staffed Inkpaw workshop recipe holds `workshop_hours` of work (never less than vanilla),
  flags and farms `harvest_hours` of harvest. Recipes with no ingredients (pumps) hold `no_ingredient_hours`;
  `recipe_hours = { Plank = 24, FlowingWater = 0 }` sets single recipes (0 = the vanilla shelf). Vanilla recipes are
  changed by Inkpaws-only modifiers, ours in place.
* `modifiers.toml`: vanilla blueprints changed for Inkpaws games only (`original`, `set` or `data`, `waits_for`).
* `tutorial.toml`: `[tutorials.<Id>]` (`order`, `after`, `stages`, `waits_for`) and `[stages."PandabornTutorial.<X>"]`
  (`steps`, each one step spec, optionally with its own `waits_for`). Names and intros come from `text/tutorial.json`
  by id. A stage that names a template the build does not ship is left out, a tutorial with no stage left is left
  out, and `after` skips over tutorials that are left out. Tutorials whose `after` are all finished run side by side.

## Translations

A language is one overlay file, `text/<lang>.json` (`text/zhCN.json`), flat, keyed by the generated loc key:

```json
{
  "_meta": { "language": "zhCN" },
  "Pandaborn.Building.Den.DisplayName": { "text": "<the translation>", "en": "Den" }
}
```

`en` is the English the translation was made from. The generator writes `Localizations/<lang>_Pandaborn<Fragment>.csv`
beside each English fragment, holding only translated keys (the game falls back to English for the rest), with the
same determinism and provenance. A translation is **left out and reported** (console and `<gen>.report.json`
`translations`) when its `en` is no longer today's English (stale), or when it does not keep the English text's `{0}`
placeholders and tags; keys the build does not have are listed as unused. Name pools are not translated here: a
language may take another column of `text/names.json` (zhCN: `characters`), and the pool is an ordinary loc key
(`Pandaborn.NamePool.<Pool>`), so the Names module needs nothing more. Texts that ship with a code module are
translated beside their English file (`src/code/<Module>/mod/Localizations/<lang>_*.csv`; the code build copies the
whole `mod` folder). `tools/validate.py` checks every non-English file: keys a subset of the mod's enUS keys, never a
vanilla key, the same placeholders and tags (warnings in a dev build, errors for `package`).

## Poles: one line

`rules.toml [poles] mode`:

* `"plank"`: planks stay planks.
* `"rename"` (chosen 2026-11-14, the mode today): poles are the vanilla `Plank` (and cured poles `TreatedPlank`) under another name and icon, for Inkpaws
  only, through `FactionSpec.BlueprintModifiers` (`Modifiers/Pandaborn/Good.Plank.optional.blueprint.json`). Proven
  in game (docs/tech/stage0.md). Nothing is recosted and other mods' plank buildings keep working.
* `"good"`: `PandabornPole` / `PandabornCuredPole` from `goods.toml` replace them in every generated cost, recipe and
  yield (`[costs].substitute`). New ids get locked; vanilla and third-party buildings that cost planks still cost
  `Plank`.

## Balance numbers

`goods/needs/recipes/plants.toml` and `building_stats.toml` were imported once from the balance model's sheet (`tools/sim/out/statsheet.json`)
by `src/gen/import_statsheet.py`; each item keeps its `src`. The catalogue is now the source: a balance change is one
edit here plus `pandaborn.ps1 all`. `python src/gen/import_statsheet.py --check` (also printed by the validate stage)
lists every number where the latest sheet and the catalogue differ.

## Ids

Ids are frozen forever (docs/ENGINEERING.md). `ids.lock.json` lists every template, alias, collection, good, need,
recipe and faction id the generator has produced. A new id makes `generate` stop until you rerun with `-Lock` (check the
spelling first: it is permanent). An id is never deleted: a replaced item carries the old id in `aliases`; an item
taken out before release is marked `"retired": "<date>: <why>"` in the lock. The validator checks the build against the
lock and the lock against its last commit (append-only).

## After a game update

1. `python tools/game_diff.py --old-blueprints <old dump> --new-blueprints E:\PandabornDev\reference\Blueprints
   --old-schema schema/<old>.json --new-schema schema/<new>.json` lists changed, removed and renamed vanilla
   blueprints, specs and fields, and which of our generated files they feed.
2. `dotnet run --project tools/schema -c Release` writes the new schema.
3. Fix the catalogue, then `pandaborn.ps1 pin -Accept` and `pandaborn.ps1 all`.
