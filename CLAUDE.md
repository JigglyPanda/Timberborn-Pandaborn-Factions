# Pandaborn - Factions

A Timberborn faction mod: a new playable panda faction (the **Inkpaws**) that stands alone next to Folktails and
Iron Teeth. It grows out of the visual-only mod *Pandaborn - Panda Reskin*
(`..\Timberborn-Pandaborn-Reskin`, Workshop item 3838695858), whose panda bodies, coats, portraits and fur it reuses.

Game design lives in [docs/DESIGN.md](docs/DESIGN.md). Read it before adding content.

## Identity

| | |
|---|---|
| Workshop / manifest name | `Pandaborn - Factions` |
| Manifest Id | `JigglyPanda.PandabornFactions` (never change it) |
| Installed folder | `Documents\Timberborn\Mods\PandabornFactions` |
| Faction Id | `Inkpaws` |
| Target game | Timberborn 1.1.x (installed: 1.1.2.8, Unity 6000.5.11f1) |

## Where things are

| Path | Contents |
|---|---|
| `catalogue/` | **The source of truth for all content**: faction, characters, buildings, goods, needs, recipes, plants, text, the id lock. Author content only here ([catalogue/README.md](catalogue/README.md)) |
| `mod/PandabornFactions/` | Hand-written files only: manifest, sprites, coat textures, hand-authored loc. Never put generated or copied blueprints here |
| `src/gen/` | The generator (catalogue -> mod data, deterministic, with provenance) and the stat-sheet importer |
| `schema/` | Every game spec class, field, type and enum per game version, from `tools/schema` (the validator's reference) |
| `src/code/` | Runtime C#: `Pandaborn.Bootstrap` (the only DLL), `Specs`, `Core`, one module per feature (`Bell`, `Names`). Read its README before adding code |
| `src/scripts/` | Water prototype code (flume, dew), to move into `src/code/Pandaborn.Water` |
| `proto/stage0/` | Stage-0 prototype: faction modifiers, plank tree, tutorial, the code modules, an in-game probe. Results in `docs/tech/stage0.md` |
| `src/devharness/` | Dev-only automated test mod. Never shipped |
| `src/unity/` | Sources for Unity asset bundles (materials, shaders, sounds) |
| `src/pipeline/` | Code that generates models, textures and icons |
| `tools/` | Build, validate and test scripts |
| `E:\PandabornDev\reference\Blueprints` | All 1,067 vanilla blueprints, unzipped |
| `E:\PandabornDev\reference\decompiled` | Decompiled game C# (ilspycmd). Reference only |
| `E:\PandabornDev\reference\{Localizations,Shaders,UI,EditorDll,EditorUI}` | Other official modding files |
| `E:\PandabornDev\assets\Pandaborn-Reskin-release` | Released Reskin mod incl. the two panda `.timbermesh` files |
| `E:\PandabornDev\tools` | Blender, Python venv and other heavy tools |
| `E:\PandabornDev\build` | Build and test output |
| `C:\Program Files (x86)\Steam\steamapps\common\Timberborn` | The game (Steam) |
| `...\Timberborn_Data\StreamingAssets\Modding\ModTemplates` | Official example mods (BerryJam is the best one) |
| `C:\Users\Israel Gonzalez\Documents\Timberborn\Mods` | Installed mods; useful working examples |
| `C:\Users\Israel Gonzalez\AppData\LocalLow\Mechanistry\Timberborn\Player.log` | Game log |
| `..\Timberborn-Pandaborn-Reskin` | Reskin source: fur shader, C#, Python mesh pipeline, docs |
| `..\Timberborn Character Skin Mod` | Custom Characters framework: debug/hot-reload tooling worth copying |
| `..\Timberborn Migration Control` | Working `dotnet build` csproj against game DLLs |

## Rules

* **Disk:** heavy files go on `E:\PandabornDev`, not C:. The repo holds source only.
* **No game files in git.** Decompiled code, vanilla blueprints, vanilla textures and meshes stay in
  `E:\PandabornDev\reference`. Learn from them; don't commit them.
* **No other mod's assets.** Other faction mods may be read to learn structure and scope. Never copy their files.
* **Never override a vanilla asset path.** This mod must leave Folktails and Iron Teeth untouched. Everything new
  goes under a `Pandaborn` path segment, e.g. `Characters/Pandaborn/...`, `Sprites/Pandaborn/...`,
  `Buildings/Pandaborn/...`. Merging into a vanilla blueprint is allowed only through a faction-scoped mechanism.
* **Collision-proof ids.** Template names end in `.Inkpaws`. Global ids (goods, needs, recipes, need groups,
  collections) start with `Pandaborn` or are `Inkpaws`-scoped. Other faction mods have crashed over shared ids
  such as `Grapes`.
* **Content is generated, never hand-written.** Buildings, goods, needs, recipes, plants, collections, the faction
  file, characters, decals, outfits and their loc are entries in `catalogue/` turned into game data by `src/gen`
  (`tools/pandaborn.ps1 all`). New ids must be locked (`generate -Lock`) and are then frozen forever
  (`catalogue/ids.lock.json`, append-only). Never edit files in the build folders; they are overwritten.
* **No required mods** unless a mechanic cannot be built without one. Mod Settings stays optional. A DLL that
  references an absent mod crashes the game, so optional integrations load late (see the Reskin's `.bin` trick).
* **The user's machine:** never delete or edit the user's saves, other mods, or mod enable states. Test saves use
  the settlement name prefix `PB_AutoTest`. Never leave the game running after a test.
* **Commits, pushes, Workshop uploads:** only when the user says so.
* **AI disclosure:** art and code are AI-generated; the README and Workshop text say so, as the Reskin does.

## Verified facts about faction modding (game 1.1.2.8)

Taken from the decompiled game and installed mods. Items marked *untested* still need an in-game check.

**Loading**
* Every file in the mod is an asset. Its path is relative to the mod root, lowercased, extension stripped.
* Loose types: `.png`/`.jpg` (any PNG asked for as a Sprite becomes one, `ModSpriteConverter`; the `<file>.meta.json`
  sets the texture preset: `{"isSprite": true}` for UI sprites, mipmap settings for goods icons as BerryJam does;
  house rule: every icon has one), `.timbermesh`,
  `*.blueprint.json`, text files. Materials, shaders and audio only load from `AssetBundles/<name>_win|_mac`.
* Blueprints are indexed by spec type; folders are convention. Files at the same path merge: objects deep-merge,
  arrays replace unless the key ends `#append` / `#remove`; `#delete` removes a key. `X.optional.blueprint.json`
  merges only when `X` exists.
* Collections join by `CollectionId`, not by path. A new file with an existing `CollectionId` adds to it.
* Collection entries omit `.json`: `"Buildings/Food/JamStove/JamStove.Folktails.blueprint"`.
* Localization: any text asset under `Localizations/`, language = filename before the first `_`
  (`enUS_pandaborn.csv`). Format `ID,Text,Comment`. All `enUS` files (mods' too) go through the game's
  `LocalizationCsvValidator`: an empty line, a 4th column or `, "` / `" ,` throws and breaks loading. A mod key
  equal to a vanilla key replaces the vanilla text for every faction.
* Every built-in asset path (sprites, materials, models, prefabs, sounds, blueprints; lowercase, no extension) is
  listed in the Unity ResourceManager table inside `Timberborn_Data\globalgamemanagers`. `tools/validate.py`
  reads it to check vanilla references. Sounds are `sounds/.../<id lowercased>` with `_01`… variants.
* A `.png` without a meta file loads sRGB, mipmapped, trilinear, RGBA32 (right for coats). Texture name = file name.
* DLLs anywhere in the mod load via `Assembly.Load(bytes)` (`Assembly.Location` is empty; get the folder from
  `IModStarter.StartMod(IModEnvironment)`). Bindito picks up `[Context("Game"|"MainMenu"|"MapEditor")]`
  configurators. Harmony is a separate mod, not built in.
* **Late-loaded code works like a normal DLL** (verified in game 2026-11-14): `ModCodeStarter` loads every mod's DLLs,
  then runs each `IModStarter` once per process, all before the main menu. Bindito scans `AppDomain.GetAssemblies()`
  every time it builds a context, and `SpecTypeCache` is created with each context's `BlueprintDeserializer`, so
  assemblies loaded with `Assembly.Load(bytes)` inside a mod starter get their configurators bound and their spec
  records registered with no extra step. `src/code`'s bootstrap does exactly this, after resolving each module's
  required-API list. A second enabled copy of a mod runs its starter too (`MarkDuplicatedIds` only works within one
  source), so the bootstrap loads each assembly once per AppDomain and reports the duplicate. Two enabled copies also
  crash every game on their asset bundles (Unity refuses a bundle with the same files twice; `ModAssetBundleLoader`
  throws; verified): the duplicate copy's starter moves its own `AssetBundles` to `AssetBundles.parked` (mod starters
  run before the bundle loader) and the owner moves its own back.
* **Texts can be swapped per game without Harmony** (verified): `ILoc.Initialize(Dictionary)` is public and clears the
  cache; the live dictionary is `Loc._localization` (private). `Pandaborn.Words` swaps a reviewed table in Inkpaws games
  before the first blueprint is read and restores the original on unload. `Phrase` objects cache their text for the
  whole session, so keys read through `Phrase.New` must not be swapped; `LocalizedText` in specs resolves when the spec is
  deserialised (per game).
* Testing code changes now that the installed mod ships a bootstrap: `proto/foundation/build.ps1 -Name <copy>` and
  `-DisableMods JigglyPanda.PandabornFactions -ExtraMods E:\PandabornDev\build\proto\<copy>` (a layered dev mod with its
  own bootstrap would only be the duplicate).
* **Faction blueprint modifiers** (`FactionSpec.BlueprintModifiers`, `[{Original, Modifier}]`, both blueprint asset
  paths without `.json`) work for every blueprint except the faction files themselves: in a new Inkpaws game only the 3
  faction blueprints are read before `FactionService.Load` initialises them; goods, needs, templates, recipes, bonus
  types, wellbeing tiers and tutorials are all read later and get the merge (same JSON merge rules as same-path files).
  Applied again on every load. Verified: `Plank` renamed, re-iconed (mod sprite) and reweighted, a need's `DailyDelta`,
  a building's cost, a recipe list, `BonusType.MovementSpeed` max, and the tutorials, all for Inkpaws only.
  **Modifier files must be `<name>.optional.blueprint.json` at a path with no base blueprint**: `SpecService.Load`
  indexes every blueprint file by its spec keys, so a normally named modifier becomes a broken standalone blueprint in
  every game; optional-only groups are skipped by the index but still load through the modifier's asset path.
* Blueprint top-level keys are all read as spec names: no comment or provenance keys (an unknown key throws on read).

**A faction needs**
* `Factions/Faction.<Id>.blueprint.json` with `FactionSpec` and `FactionWonderSpec` (required in practice: the UI
  sound controller reads it with no null check). `StartingFactionSpec` (empty) switches the tutorial system on for
  a faction (read only by `TutorialService`, `TutorialTriggers`, `TutorialToggleController`); with it, every vanilla
  `TutorialSpec` is built for that faction, so switch them off with faction modifiers and add your own (verified in
  game, see docs/tech/stage0.md). Two load crashes verified in a tutorial faction: `StairsUnlockedTrigger` throws
  unless a template answers to `Stairs.Folktails` (alias it on `Stairs.Inkpaws`), and every tutorial step that names a
  template the faction lacks throws in `TutorialService.Load` (stages are built eagerly). Omit `UnlockableFactionSpec` to be unlocked from the start.
* `FactionSpec` fields: `Id`, `Order`, `Avatar`, `ChildAvatar`, `BotAvatar`, `ContaminatedAdultAvatar`,
  `ContaminatedChildAvatar`, `Logo`, `NewGameFullAvatar`, `Textures`, `ChildTextures`, `MaterialCollectionIds`,
  `TemplateCollectionIds`, `NeedCollectionIds`, `GoodCollectionIds`, `PathMaterial`, `BaseWoodMaterial`,
  `BlueprintModifiers`, `StartingBuildingId`, `SoundId`, and the display/description/game-over loc keys.
* Across the faction's template collections plus `Common` there must be exactly one each of `AdultSpec`,
  `ChildSpec`, `BotSpec`, `ModularShaftPartsSpec` (and `PlaneSpec` only for the Iron Teeth wonder).
* Template names must be unique game-wide.
* `DecalSpec`s with the faction's `FactionId` for both categories `Banners` and `Tails` (the decal service
  indexes them without a check).
  A decal's id is its texture's asset name; duplicates in a category are dropped silently. A `DecalSpec` with an
  empty `FactionId` applies to every faction.
* `WorkerOutfitSpec`s are keyed by `FactionId`; without them workers have no outfit. Two specs with the same
  (`Id`, `WorkerType`) for one faction throw (`ToDictionary`).
* Every `NeedSpec` must sit in a collection, and every need collection must be used by an installed faction.
* A timbermesh can only use materials from the faction's `MaterialCollectionIds` plus `Common`. A faction may
  list `Folktails` and `IronTeeth` material collections to reuse their models.
* `MaterialRepository` keys materials by the Unity asset's **name**, from the active faction's collections
  only, and throws on a duplicate name. So a faction-only collection may hold bundle materials *named* like
  vanilla ones (e.g. `BaseWood_Brown.Folktails`), provided the faction does not also list the `Folktails`
  collection. Every vanilla Folktails model then renders with our materials in an Inkpaws game only.
  **Proven in game, but the data-only form is unsafe with other mods:** ChooChoo loads its own copy of the
  Folktails materials into any faction that does not list `Folktails` ("already loaded" crash), and building
  mods such as KnatteAnka Staircase need materials that live in the `Folktails` collection ("not found"
  crash). **Use the swap form instead:** the faction keeps listing `Folktails`, and a small class copies our
  bundle materials' properties into the same-named vanilla materials when an Inkpaws game loads and restores
  them on unload (`src/code/Pandaborn.Look`; passed with all 35 of the owner's mods, including an Inkpaws game
  followed by a Folktails game in one session). If the bundle is missing the faction simply looks like Folktails.
  The bundle file must keep the name it was built with (`tools\build_look.ps1 -BundleName pandabornlook`): a
  hand-renamed copy crashes on return to the main menu. Details in `docs/tech/look.md`; sheet regions for
  modellers in `docs/tech/look-regions.md`.
* Global, not per faction: game modes, starting goods (hardcoded Berries and Water), wellbeing tiers, bottom-bar tool
  groups, achievements. The name pool (`Beaver.NamePool`) is global, but an `IEntityNamer` with priority above 20
  decorated on a faction-only spec names that faction's colonists (`Pandaborn.Names`, verified; glosses like
  "Le Le (Joy)" show verbatim). Many global specs (needs, goods, bonus types, tiers) can be retuned per faction with
  blueprint modifiers.

**Characters**
* The body is whatever single adult/child template the faction's `Characters.*` collection lists. The mesh is
  set in the blueprint (`Children.Model_Preserved.TimbermeshSpec.Model`). `BeaverFactory`, `BotFactory` and the
  shaft factories take `TemplateService.GetSingle<AdultSpec|ChildSpec|BotSpec|ModularShaftPartsSpec>()` over the
  active collections only. No game code loads `Characters/Beaver/...` by string or compares a template name to
  `BeaverAdult`/`BeaverChild` (only the Folktails-only tutorial stage `Wellbeing.SelectBeaver` lists them).
  The mesh is imported per path (no cache by node or animation name). Verified in game 2026-11-14 (Reskin off):
  Inkpaws colonists use `Characters/Pandaborn/InkpawAdult|InkpawChild.Model` with coats
  `Materials/Pandaborn/Inkpaws/...` (adult body 1,716 vertices, kit 1,608), while with this mod on, Folktails and
  Iron Teeth keep `BeaverAdult`/`BeaverChild` on `Characters/Beaver/...` (877 / 874 vertices) served only by the game's
  own `ResourceAssetProvider`, with their vanilla coats. A coat is picked at random on every load
  (`BeaverTextureSetter`), so it changes after save/load for every faction.
* Character templates must keep the vanilla label keys in `SimpleLabeledEntitySpec.EntityNameLocKey`
  (`Beaver.Adult.TemplateName`, `Beaver.Child.TemplateName`, `Bot.TemplateName`): the Population tab of the
  batch-control window (`CharacterBatchControlTab.GetSortingKey`) throws `ArgumentOutOfRangeException` on any other
  key. So the tab's group headers read "Beaver adult"/"Beaver child" in an Inkpaws game; changing that needs code
  (a faction-aware label at runtime), never a vanilla loc override. `tools/validate.py` enforces the keys and the
  test harness opens every batch-control tab.
* The Reskin's panda meshes keep the beaver layout: adult nodes `Beaver_mesh_default`, `#BeaverAdult.001`
  (1,716 vertices, material `BeaverAdult`), `#Backpack`, `#CarriedInHands`, `#Head`, `#Teeth`, `#ZiplineHarness`,
  `#PlantingParticles`, `#BuildingParticles`, `#Collider`; 61 animations. Kit: `#BeaverChild` (1,608 vertices,
  material `BeaverChild`), `#ZiplineHarness`, `#Collider`; 39 animations.
* With the Reskin enabled, its `PandabornFactionSkins` rewrites every non-vanilla faction's textures and avatars
  to the Folktails ones (giant panda by default), and it overrides the vanilla beaver meshes, so Folktails look
  like pandas too. Test "beavers untouched" with the Reskin disabled, or by mesh path rather than by eye.
* Animation is baked per vertex inside the `.timbermesh` (zlib level 6 around protobuf). Coats come from
  `FactionSpec.Textures`, applied as `_BaseMap` on the fixed `BeaverURP` material. A body must keep the beaver UV
  layout or outfits, injuries and the fixed normal map misalign. See the Reskin's
  `docs/CHARACTER_MOD_CONTEXT.md`.

**Bonuses, working hours, trees** (verified in game 2026-11-14, `proto/stage0`)
* `BonusManager` keeps one additive sum per bonus id (start 1.0), clamped by `BonusTypeSpec` min/max
  (`MovementSpeed` 0.25..2.0, `WorkingSpeed` 0.05..1000); bonuses are not saved. `Worker.WorkingSpeedMultiplier` and
  `WalkerSpeedManager` read the multiplier every tick. A multiplicative bonus is possible by re-adding
  `share = multiplier without it x factor` on `BonusValueChanged` (`Pandaborn.Bell`: wellbeing-80 work 3.8 -> 5.054,
  walk 1.7 -> 2.261 with the Inkpaws-only cap raised to 2.66 by a modifier).
* The working-hours slider is `WorkingHoursManager.WorkedPartOfDay` (saved); `DaytimeStartEvent` fires at dawn.
* A tree may yield any good: a Birch copy with `CuttableSpec.Yielder.Yield = Plank` was cut by the vanilla lumberjack,
  carried to its flag and piled; the yield panel shows the good's icon. The chipped-teeth effect and the cutting
  success chance are keyed to `Log` and do not apply to other yields.

**Known constraints from other faction mods**
* Breeding is a property of the housing building (`ProcreationHouseSpec`), not the faction.
* A need with a "cure" good makes colonists drop work to fetch it.
* Storage for a good colonists consume needs `EnterableSpec`, or the game crashes.
* Each plant belongs to one planter group (`PlantableSpec.ResourceGroup`), which decides who plants it.

## Building and testing

* Scripts compile with `dotnet build` (SDK 9) against `Timberborn_Data\Managed\*.dll`, netstandard2.1.
* Unity 6000.5.11f1 is installed and batch-mode bundle builds work
  (`Unity.exe -batchmode -quit -projectPath <proj> -executeMethod <Builder.Build>`). The Unity project goes in
  `E:\PandabornDev\unity`.
* Dev mode in game is Shift+Alt+Z; `-skipModManager` skips the launch dialog.
* **One command:** `powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 <stage>`; `all` = `pin`, `models`,
  `generate` (`-DryRun`, `-Lock`), `code`, `bundles`, `assemble`, `validate`, `gate`, `install`; also `test` (grid scenario)
  and `package` (release rules). `tools/build.ps1` runs models, generate, code, bundles, assemble, validate, install.
  The build refuses to run if the vanilla dump differs from `catalogue/vanilla.pin.json` until you review
  `tools/game_diff.py` and `pin -Accept`; `pin` also runs the Words table check
  (`src/code/Pandaborn.Words/tools/candidates.py --check`, a warning there, a failure for `package`).
  * `models`: runs every `art/models/<Id>/build.py` (the building kit; `-Plants` also `art/plants/<Id>/build.py`)
    into `E:\PandabornDev\build\models\<Id>`; plant meshes live in `E:\PandabornDev\build\plants\<Id>`. Meshes never
    enter git; `assemble` copies the ones the catalogue adopts (`model = "<Id>"`) from `<gen>.models.json`, and the
    Ringtail bodies from `E:\PandabornDev\build\characters\out` when the data has the Ringtail templates.
  * `code`: **the code ships in the mod since 2026-11-14.** `src/code` builds into
    `E:\PandabornDev\build\code\PandabornFactions`; the Look module brings the `pandabornlook` bundle; the stage also
    dumps the mod's own spec classes (`code-schema.json`) for the validator and runs `tools/check_api_lists.py`
    (game-API lists, a warning here, a failure for `package`). **A module ships only when its data is switched on**
    in `catalogue/rules.toml [modules]` (today Bell, Names, Look, Words, Ringtails, RingtailsFallback; Water, Festival,
    Flowering are left out of `Modules/modules.txt`). `-NoCode` builds the data-only fallback (no custom specs,
    vanilla names, Folktails look). Do not also load `E:\PandabornDev\build\PandabornCodeDev` (`-ExtraMods`) with the
    installed faction: the code would be there twice.
  * `bundles`: copies built `pandaborn*_win|_mac` bundles, never renamed, from `-BundleDirs` (today
    `E:\PandabornDev\build\plants\AssetBundles` and `E:\PandabornDev\build\sound\AssetBundles`; planned:
    `E:\PandabornDev\build\characters\attachments` once real hats and baskets exist) into `AssetBundles/`; fails if
    an adopted model needs a bundle that is not built. A missing `_mac` twin is a warning in dev stages and an error
    for `package` (`validate.py --release`); Mac builds: docs/tech/mac.md. Never enable `proto/sound` with the
    faction (the same bundle twice crashes). A folder `AssetBundles.parked` (left by a second enabled copy) is never
    content: assemble skips it, install's mirror removes it, `package` refuses it.
  * **Install discipline:** run `install` only when no Timberborn process runs (other lanes queue game tests all
    day); take the test mutex `Global\PandabornGameTest` for it, and never leave the tree in a state where `all`
    fails.
  * **THE INSTALL GATE** (2026-11-14, after two adopted-model crashes that only showed once a building existed or was
    finished): the shared install only receives a staging folder whose dev copy has passed the GRID run. `gate`
    builds the copy (`proto/foundation/build.ps1 -Name pbgate -Source <StageDir>`), runs `<gen>.grid.json` on it with
    the installed faction switched off (every placeable template placed AND finished, then recipes on, a speed
    ladder 1-3-0-2-3 and three in-game hours, zero errors from our mods), and writes `<StageDir>.gate.json` with
    the folder's content hash. `install` refuses a folder without a matching gate; `-GateOverride "<reason>"` (only
    on the coordinator's word) is logged in `<StageDir>.gate-overrides.log`. Loading a new game is not enough.
* **Hidden until wired** (DESIGN.md 2026-11-14): a catalogue item with `waits_for = "<Module>"` is left out of the
  build (templates, goods, needs, recipes, plants, tutorial stages, tool groups) unless that module ships and its
  switch in `rules.toml [modules]` is on; its ids stay in the lock marked `gatedBy`. `module_specs = { <Module> = {
  <Spec> = {...} } }` adds our own spec classes only when the module is on. `<gen>.report.json` `leftOut` lists what
  is hidden. The validator's economy block (`--release`: errors) refuses needs nothing meets, goods nothing makes or
  uses, two buildings on one toolbar slot, shipped modules without their data and data without its module.
* **Catalogue extras:** `catalogue/modifiers.toml` (Inkpaws-only blueprint modifiers, e.g. the bell's walking cap),
  `catalogue/tutorial.toml` + `text/tutorial.json` (StartingFactionSpec, every vanilla tutorial off, our dormant
  tutorials switched on by modifier, `Stairs.Folktails` alias on `Stairs.Inkpaws`), `rules.toml [shelves]` (workshop
  recipes hold `workshop_hours` of work at full staffing, flags and farms `harvest_hours` of harvest), `faction.toml`
  `[tool_groups]` (the Night Watch group), `[worker_types]` (PandabornRingtail: ships forever), own decals and
  `[outfits] extra` (Ringtail outfits), characters with `in_collection = false` (the Ringtails).
* **Validator:** `python tools/validate.py --mod <any mod folder>` checks every blueprint key and field against
  `schema/<game version>.json` (unknown spec keys throw in game; unknown fields are silently ignored), asset
  references (exact case), ids and the lock, custom specs in global data, NeedVerifier, goods outside the faction's
  collections, bundle pairs. Prototypes that add fragments to the faction build: `--base-mod
  E:\PandabornDev\build\stage\PandabornFactions`; their own spec classes: `--mod-schema` (from `tools/schema
  --include <dll>`). `--self-test` writes the broken fixtures from the vanilla dump
  (`tools/tests/validate/make_fixtures.py`, into `E:\PandabornDev\build\validate-fixtures`: they copy game files, so
  they stay out of git) and runs them. Our own sound names are checked against the mod's bundles (UnityPy from the
  art venv).
* See `tools/` for the build, validate and automated in-game test scripts.

### Automated in-game test

```powershell
powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Diorama -RunSeconds 60
# more: -InGameDays 1 -Speed 3 -Buildings 'Lodge.Folktails,EfficientFarmHouse.Folktails'
#       -Screenshots 'overview@start,adult@start,child@start,overview@30,screen@end' -RequestJson <file>
#       -DisableMods JigglyPanda.Pandaborn | -OnlyMods JigglyPanda.PandabornFactions   (this run only, restored after)
#       -ExtraMods E:\PandabornDev\build\proto\<name>   (junction + enable a dev mod for this run only)
#       -FactionPanelShots -SaveAndReload -WaitForGameSeconds 1800 -DryRun -NoBatchControl
# -Checks needs a hashtable, so call it from PowerShell (& tools\run_game_test.ps1 ...) rather than -File:
#       -Checks @{ adultTemplate = 'InkpawAdult.Inkpaws'; adultModel = 'Characters/Pandaborn/InkpawAdult.Model';
#                  adultTextureAsset = 'Materials/Pandaborn/Inkpaws/'; botTemplateActive = 'Bot.Inkpaws'; minChildren = 1 }
powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -RestoreModState <run>\modstate.json   # manual undo
```

* One test at a time per machine: the script holds the named mutex `Global\PandabornGameTest` for the whole run
  (holder in `E:\PandabornDev\build\test\gametest.lock.json`) and waits while another run holds it or any Timberborn
  process is open, printing who it waits on. Exit code 2 only after `-WaitForGameSeconds` (default 1800). The mutex is
  released on every exit path; a holder that died is taken over.
* **The game runs on a hidden Windows desktop by default** (since bee3cb4): no window on the owner's screen, no focus,
  no real keyboard or mouse; rendering, UI and screenshots work (run `quiet-trial-1`). `-Visible` shows the game on
  the real desktop: never pass it, and never start Timberborn any other way, while the owner is at the PC.
* **Holding the queue:** `tools\game_test_hold.ps1` takes the test mutex after the run in progress and holds it (file
  `E:\PandabornDev\build\test\HOLD`); delete that file to release. Queued runs keep waiting and nothing is cancelled;
  held time does not count against `-WaitForGameSeconds`. A waiter started before a change to `run_game_test.ps1`
  keeps the old script in memory: stop and requeue it.
* A run tracks its own game pid and never counts or kills any other Timberborn process. If the owner starts Timberborn
  during a run, the run stops its own game, restores mod flags, exits "could not test" (2) and the queue waits for the
  owner's game to close; `tools\play_timberborn.ps1` is the owner's way to pause the queue and play.
* Builds `src/devharness` (dev-only mod) to `E:\PandabornDev\build\PandabornDevHarness`, junctions it into `Mods`,
  writes `E:\PandabornDev\build\test\request.json`, launches the game, waits, kills it on timeout, then removes the
  junction (`-KeepInstalled` keeps it; it is inert without a request), deletes the `PB_AutoTest_<run>` save and
  restores the `Screenmanager*` window prefs Unity saves on exit. List parameters accept `a,b` (also through `-File`).
* Output in `E:\PandabornDev\build\test\<run id>\`: `result.json` (faction, mods loaded, population, per-colonist
  template / model asset path / mesh + vertices / coat texture and its asset path, active adult/child/bot templates
  with model path and which asset provider (game or mod) supplies it, faction coats, available templates, placed
  buildings, batch-control tabs, save, captured errors, checks, verdict), `summary.json`, `overall.json`, `harness.log`,
  `Player.log`, PNGs (`overview` = off-screen render of the game view, `screen` = real screen with UI,
  `adult`/`child`/`bot` = studio close-up, front and back, `batch_population` = Population tab open,
  `factionPanel_<Id>` = new-game faction panel). Look at the PNGs.
* Placed buildings are joined to the district center with finished `Path` tiles (`connectPaths`, default on; shortest
  route over level ground; report in `result.json` `paths`); without paths they stay "Unconnected" and nobody works
  there. The path goes on `BlockObject.PositionedEntrance.Coordinates` (the cell in front of the door);
  `DoorstepCoordinates`, despite its name, is the building's own block behind the door. Starting goods are
  only berries and water, so unfinished buildings need a working `LumberjackFlag` first. `result.json` `activity`
  counts each character's running behavior/executor every 2 real seconds (work, eat, sleep, wander), and each sample
  lists its need points.
* At the end of every run the harness opens each batch-control tab (Population last) and fails `batchControlTabs` if
  one throws. `-SaveAndReload` saves as `PB_AutoTest` in `Saves\PB_AutoTest_<run>\`, relaunches with
  `-saveName/-settlementName`, re-checks faction and characters in `<run>\reload\`, then deletes that settlement only.
* Exit code 0 pass, 1 fail, 2 could not test.
* Errors are "ours" when message or stack contains `PandabornFactions`, `PandabornDevHarness`, `Inkpaws` or an
  `-ExtraMods` mod's id/folder/name (`-OwnPatterns`). Other mods' noise is reported but only fails with `-StrictLog`.
  Known noise: 31x `Assertion failed` right after "Too many atlases loaded (3)!" when the game scene loads.
* **Mod isolation.** The game keeps each mod's enable flag in Unity PlayerPrefs, `HKCU\Software\Mechanistry\Timberborn`,
  value `ModEnabled.<Local|Steam Workshop>.<top folder>.<manifest Id>_h<hash>` (REG_DWORD 1/0; absent = enabled, so a
  new mod loads enabled; hash = djb2-xor of the UTF-8 key, `h = (h*33) ^ byte` from 5381, uint32). Workshop items use
  the same flags (`Steam Workshop.<item id>`). `RequiredMods` are not enforced at load (the mod manager UI only warns),
  so `-OnlyMods` keeps the listed mods, the harness, `-ExtraMods` and, transitively, everything they require.
  `-DisableMods`/`-OnlyMods`/`-ExtraMods` write the exact prior values to `<run>\modstate.json` and
  `test\modstate.pending.json` before changing anything, change only those values, and restore them in a `finally`
  (also on timeout, crash and Ctrl-C) after the game has exited (Unity rewrites prefs on exit), then re-read and
  compare (`modstate.restore.json`). While `modstate.pending.json` exists the script refuses to start; undo with
  `-RestoreModState`. `-DryRun` prints the plan without changing anything. `result.json` `mods` proves what loaded.
* `-ExtraMods <folder>[,<folder>]` junctions each folder (it needs a `manifest.json`) into `Mods\<folder name>` for the
  run, refusing to replace a real folder, and removes the junctions it created on every exit path; if a stale flag
  had the mod switched off it is switched on for the run (same record/restore). Prototypes live in `proto/<name>/`,
  built to `E:\PandabornDev\build\proto\<name>`.
* The Pandaborn **Reskin** (`JigglyPanda.Pandaborn`) turns vanilla beavers into pandas and re-skins other factions;
  test vanilla looks and Inkpaws coats with `-DisableMods JigglyPanda.Pandaborn`. Another mod on this machine
  Harmony-patches `CharacterBatchControlTab.GetSortingKey` (stack shows `GetSortingKey_Patch1`).
* Launch facts: `Timberborn.exe` started directly with env `SteamAppId=1062090` does not bounce through Steam, so
  Unity arguments work: `-skipModManager`, `-logFile <path>`, `-screen-fullscreen 0 -screen-width W -screen-height H`.
  The game's own arguments: `-skipModManager`, `-saveName`/`-settlementName` (auto-load a save), `-uncapped`,
  `-benchmarkLength` (loads no mods).
* The build (`tools/pandaborn.ps1`, or `tools/build.ps1`) generates the catalogue into
  `E:\PandabornDev\build\gen\PandabornFactions`, assembles it with `mod/PandabornFactions`, the two panda meshes
  (from `E:\PandabornDev\assets\Pandaborn-Reskin-release`), the adopted model meshes, the code and the bundles in
  `E:\PandabornDev\build\stage\PandabornFactions`,
  validates that, then mirrors it into `E:\PandabornDev\build\PandabornFactions` and junctions
  `Documents\Timberborn\Mods\PandabornFactions` to it (the game loads mods through the junction; verified). It never
  touches any other `Mods` entry and refuses to replace a real folder; a build that fails validation is not installed.
* Since 2026-11-14 the Inkpaws own their building list (`Buildings.Inkpaws`, 152 visible buildings; 15 more wait
  for the Water, Festival and Ringtail-venue modules), goods
  (`Goods.Inkpaws`), needs (`Needs.Inkpaws`) and plants (`NaturalResources.Inkpaws`); an Inkpaws game no longer
  offers `*.Folktails` templates. Re-themed vanilla buildings are `<Name>.Inkpaws` copies; new buildings are
  `Pandaborn<Name>.Inkpaws`, on the art lanes' models where adopted and on vanilla stand-in models otherwise
  (`E:\PandabornDev\build\gen\PandabornFactions.report.json` lists adopted models, stand-ins and the code module
  each stand-in waits for; `<gen>.models.request.json` is a ready test of every adopted model). Harness: `-RequestJson E:\PandabornDev\build\gen\PandabornFactions.grid.json` places and
  finishes every placeable template (`src/devharness/GridLab.cs`, request key `grid`; use `-Map Plains -OnlyMods
  JigglyPanda.PandabornFactions` for a comparable layout).

## Art toolchain

Everything lives under `E:\PandabornDev\tools` (nothing on C:, no PATH/registry changes). Verified 2026-11-13.

| Tool | Path |
|---|---|
| Blender 4.5.16 LTS (portable) | `E:\PandabornDev\tools\blender-4.5-lts\blender-4.5.16-windows-x64\blender.exe` |
| Python 3.10 venv (numpy 2.2.6, scipy 1.15.3, Pillow 12.3, protobuf 7.36; pip cache on E:) | `E:\PandabornDev\tools\venv\Scripts\python.exe` |
| Mechanistry exporter v1.2.0 source (MIT, read + audited; do not edit) | `E:\PandabornDev\tools\timbermesh-exporter\timbermesh-main\src\timbermesh_blender_plugin` |
| Scratch/check output | `E:\PandabornDev\build\toolcheck` (render_cube.py lives here) |

Invocations (bash; set these first so Blender and Python never write to C:):
```
export BLENDER_USER_RESOURCES='E:\PandabornDev\tools\blender-userdata' TEMP='E:\PandabornDev\tools\tmp' TMP='E:\PandabornDev\tools\tmp' PYTHONDONTWRITEBYTECODE=1
BL=/e/PandabornDev/tools/blender-4.5-lts/blender-4.5.16-windows-x64/blender.exe
PY=/e/PandabornDev/tools/venv/Scripts/python.exe
$BL -b --factory-startup --python SCRIPT.py -- args      # headless Blender; ALWAYS --factory-startup
$BL -b --factory-startup FILE.blend --python src/pipeline/tm_export_headless.py -- <plugin dir> <out dir> [collection names]
$BL -b --factory-startup FILE.blend --python src/pipeline/blend_dump.py   # list collections/objects/materials
$PY -I src/pipeline/tmesh_inspect.py FILE.timbermesh [--anim-detail]   # structure dump + load time/memory
$PY -I src/pipeline/tmesh_compare.py A.timbermesh B.timbermesh         # field-by-field comparison
$PY -I src/pipeline/tmesh_static.py OUT.timbermesh                     # writes the demo 1x1 crate
```
Notes: Cycles uses the RTX 5070 Ti (OPTIX/CUDA work in 4.5.16). EEVEE engine id is `BLENDER_EEVEE_NEXT` and its first
headless render takes ~50 s (shader compile). Blender's own Python has numpy 1.26 only (no scipy/Pillow/protobuf), so
heavy math belongs in the venv and Blender scripts should stay thin. The official exporter is driven by importing
`timbermesh_exporter` and calling `Exporter.export_collection(collection, path, ExportSettings(bpy.context, True, True, False))`;
collections excluded from the view layer must be un-excluded first (the driver does this). Static building format
facts (materials, winding, tangents, node layout) are documented at the top of `src/pipeline/tmesh_static.py`.

## Staffing

The main session (Fable 5.2, high) orchestrates and owns design, balance and final review.

| Work | Model / effort |
|---|---|
| C# mechanics, anything touching game internals | Opus / high |
| Mesh and art pipeline | Opus / high |
| Bulk blueprint, localization and icon authoring | Sonnet / medium |
| Independent review of each milestone | Opus / high |
