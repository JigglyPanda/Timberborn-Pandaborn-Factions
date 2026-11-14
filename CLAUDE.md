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
| `mod/PandabornFactions/` | The mod as shipped, minus large binaries (meshes over ~10 MB) |
| `src/scripts/` | C# runtime code for the mod's DLL |
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
* Loose types: `.png`/`.jpg` (sprite needs `<file>.meta.json` with `{"isSprite": true}`), `.timbermesh`,
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

**A faction needs**
* `Factions/Faction.<Id>.blueprint.json` with `FactionSpec` and `FactionWonderSpec` (required in practice: the UI
  sound controller reads it with no null check). Omit `StartingFactionSpec` (tutorial-only, hardcoded to
  Folktails). Omit `UnlockableFactionSpec` to be unlocked from the start.
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
  *Untested in game.*
* Global, not per faction: game modes, starting goods (hardcoded Berries and Water), the name pool
  (`Beaver.NamePool`), wellbeing tiers, bottom-bar tool groups, achievements.

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
* `tools/build.ps1` mirrors `mod/PandabornFactions` plus the two panda meshes (from
  `E:\PandabornDev\assets\Pandaborn-Reskin-release`) into `E:\PandabornDev\build\PandabornFactions`, runs
  `tools/validate.py`, then junctions `Documents\Timberborn\Mods\PandabornFactions` to it. It never touches any
  other `Mods` entry and refuses to replace a real folder. *Untested:* that the game loads a mod through a junction.
* `src/pipeline/derive_vanilla_copies.py` regenerates the Inkpaws copies of vanilla blueprints (characters, bot,
  shaft parts, decals, worker outfits) from the dump; rerun it after a game update.

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
