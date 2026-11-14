# Look: materials pipeline and the vanilla re-theme

Status: prototype, 2026-11-14. Game 1.1.2.8, Unity 6000.5.11f1. Everything marked **in game** was run with
`tools/run_game_test.ps1`; the rest is read from the decompiled game (`E:\PandabornDev\reference\decompiled`, **DC**)
and the vanilla assets extracted for reference into `E:\PandabornDev\reference\vanilla-assets` (never committed).

## Summary

* **The re-theme works in game.** An Inkpaws game renders every vanilla Folktails building model (finished and
  construction stages, district center, power shafts, decorations, storage, paths' tunnel roofs) with our own
  materials; a Folktails game with the same mod enabled is unchanged. No new models, no errors in the log.
* **But the pure-data form of the trick ("names" variant) is not mod-safe.** It drops the `Folktails` material
  collection from the faction, which crashes the game as soon as any other mod (a) injects vanilla Folktails
  materials into non-Folktails factions (ChooChoo does, *Material BaseWood_Brown.Folktails is already loaded*) or
  (b) adds buildings to `Buildings.Folktails` whose materials live in the `Folktails` collection (KnatteAnka's
  Staircase and others: *Material 1KA_DarkMetal.Folktails not found*). Both mods are installed on this machine.
* **The fix is ~100 lines of C# with no Harmony ("swap" variant).** The faction keeps `Folktails`; in an Inkpaws
  game a tiny `IMaterialCollectionIdsProvider` copies our bundle materials into the vanilla materials of the same
  name (`Material.CopyPropertiesFromMaterial`) during `MaterialRepository.Load`, and restores them when the game
  unloads. The game's own shader stays on every material. **In game it passed with all 35 of the owner's mods
  enabled (ChooChoo and KnatteAnka included), and a Folktails game with it enabled is unchanged.** The vanilla
  runtime atlas even picks up our textures, so draw calls stay as in vanilla. This is the recommended form.
* **Cost:** one 39 MB asset bundle (61 BC7 1024² textures incl. mips), ~15 s to repaint the textures, ~1 min for the
  Unity batch build after the first import (~5 min once). Runtime memory ~+80 MB in Inkpaws games only. Draw calls:
  see *Costs*.
* **Character material:** possible the same way, but it needs a re-exported panda mesh whose material is renamed
  (e.g. `PandabornInkpawAdult`), a bundle material on a copy of `BeaverURP.shadergraph`, and that material listed in
  an Inkpaws-only collection. No other faction is affected. Details below.
* **Mac bundles:** not buildable now. Mac Build Support (Mono) is not installed for 6000.5.11f1; it is a 523 MB
  download (≈1.5 GB installed) into the editor folder on C:.

## Art direction

From the design review (2026-11-14), binding for every material and model:

* **Rural Sichuan, the bamboo-grove farmsteads of the Chengdu plain.** Dark timber frames with white lime-plaster
  infill panels, grey clay roof tile (pan and cover), natural and weathered bamboo (green when fresh, straw-gold
  when cured, silver-grey when old), woven bamboo panels, rammed earth and river stone for bases.
* **Red is an accent only:** paper lanterns, small trim, festival items. No red columns, no yellow glazed or sharply
  upturned imperial roofs. Not "Chinatown".
* **Paper windows use Chinese lattice patterns** (cracked-ice *bing lie wen*, lantern-frame *deng long kuang*,
  step-brocade), never a shoji grid. Nothing Japanese-coded.
* **No writing on any texture.** Generated characters come out as gibberish. Where a sign, scroll or label would
  carry text, use ink-painted bamboo, paw prints or plain patterns.
* **Both panda peoples share one architectural vocabulary**; only scale and height differ.

## How the game resolves building materials

* A `.timbermesh` stores, per mesh, a material **name** (e.g. `BaseWood_Brown.Folktails`). `MaterialRepository`
  (DC `Timberborn.TimbermeshMaterials`) builds a name → `Material` dictionary at game load from the material
  collections returned by every `IMaterialCollectionIdsProvider`: `Common` (always), the faction's
  `MaterialCollectionIds` (`FactionMaterialCollectionIdsProvider`), and any a mod binds. A duplicate name throws
  (`Material X is already loaded`), a missing one throws when a model asks for it (`Material X not found in
  repository`). The providers are enumerated lazily *inside* `Load`, so a provider runs before any model is built.
* Collections are joined by `CollectionId`, so mods add to `Folktails` freely. Mod materials can only come from
  asset bundles (`AssetBundles/<name>_win|_mac`); a bundle asset's path is everything after `/Resources/`, so ours
  load as `Materials/Pandaborn/Look/<name>` while their **name** is the vanilla one.
* After import, each building prefab goes through `PrefabOptimizationChain` (DC `Timberborn.PrefabOptimization`):
  1. `AutoAtlasingPrefabOptimizer`: for submeshes on `Shader Graphs/EnvironmentURP` whose texture set matches a
     fragment of `Configurations/AutoAtlaser.blueprint.json` (the 15 `FactionAtlas.Folktails` materials), it builds
     one 4×4 atlas per map at runtime (`GetPixels32`, so fragment textures must be **readable** and the same size)
     and remaps UVs (`uv * 1/4 + offset`). The key is the *texture objects*, so two fragments with the same textures
     throw. Only one "unique" atlas is expected per game (the "Too many atlases loaded" warning).
  2. `VertexColorPrefabOptimizer`: multiplies each material's `_Color` into the vertex colours and swaps the
     material for an "Uncolored" copy made with `Shader.Find(<shader name>)`. So `_Color` tints behave exactly like
     vanilla.
  3. `MergeMeshesByMaterialPrefabOptimizer`: one submesh per material.
* Highlighting, grey-out, night lighting and construction use shader properties of the same `EnvironmentURP`
  material: `_EmissionColor` (selection), `_Grayscale`, `_LightingColor` + the renderer's shader user value
  (`MaterialLightingEnabler`, night lights on finished buildings), `_LightingMap` (which texels glow), and
  `_HeightCutoff` (layer cut-away). Keeping the game's shader means all of these work unchanged.
* `FactionSpec.PathMaterial` and `BaseWoodMaterial` are asset references (paths), not names: the path ground uses
  `PathMaterial` (DirtURP, world-space UVs), tunnel/path roofs use `BaseWoodMaterial`.

## Vanilla building materials (Folktails collection)

Extracted by `src/pipeline/extract_vanilla_materials.py`; usage counted over the 1,189 built-in timbermesh models by
`src/pipeline/vanilla_material_usage.py` (models / triangles in models whose name contains `Folktails`).

All `EnvironmentURP` building materials share these facts: maps 1024², BC7, 11 mips, trilinear, aniso 16, repeat,
**readable**; albedo/AO/metallic/emission sRGB, normal linear and swizzled DXT5nm-style (R = 1, G = y, A = x); `_M`
map R = metallic (wood ≈ 0.09, metal ≈ 0.5), A = smoothness (0.1–0.6); no keywords; render queue default;
`_HeightCutoff` −100000; detail maps unused (`_DetailAlbedoUV2Color` 0.745 grey, `_DetailAlbedoUV3Gradient`
0.025); `_MainUVFromCoordinates` off. **Every model UV is inside 0..1** (min −0.01, max 1.001; windows −0.17..0.98):
these are trim sheets, not tiling textures, which is also what makes runtime atlasing possible. 128 of 131
`BaseMetal` models and about half of the wood models carry non-white vertex colours (tints/AO baked by the
artists), multiplied onto whatever albedo we supply.

| Material | Shader | Models / tris | Atlas | Maps (vanilla texture) and tint |
|---|---|---|---|---|
| `BaseWood_Brown.Folktails` | EnvironmentURP | 315 / 100,535 | yes | D `BaseWood_1K_D_Brown`, N, AO, M (`BaseWood_1K_*`) |
| `BaseMetal.Folktails` | EnvironmentURP | 131 / 46,101 | yes | `BaseMetal_D1`, N, AO, M |
| `BaseWood_LightBrown.Folktails` | EnvironmentURP | 111 / 24,782 | (shares White's key) | `BaseWood_1K_D_White`, `_Color` 0.66,0.56,0.41 |
| `BaseWood_White.Folktails` | EnvironmentURP | 98 / 15,330 | yes | `BaseWood_1K_D_White`, `_Color` 0.89,0.86,0.83 |
| `Details.Folktails` | EnvironmentURP | 49 / 10,007 | yes | banner, sack, rope, good labels, crates |
| `WindowsAtlas.Folktails` | EnvironmentURP | 85 / 6,615 | yes | D, N, AO, M, **E (`_LightingMap`: night glow)** |
| `BaseWood_Yellow.Folktails` | EnvironmentURP | 5 / 6,491 | (White's key) | White texture, `_Color` 0.70,0.57,0.35 |
| `PaintedMetal.Folktails` | EnvironmentURP | 32 / 4,930 | yes | yellow/black hazard stripes |
| `Moss.Folktails` | EnvironmentURP | 3 / 4,332 | yes | `Moss_D` + plaster N/AO/M |
| `Plaster_White.Folktails` | EnvironmentURP | 17 / 3,019 | yes | `Plaster_D_White` |
| `Paper.Folktails` | EnvironmentURP | 34 / 2,278 | yes | paper panels in frames (no M) |
| `ThatchedRoof.Folktails` | EnvironmentURP | 19 / 2,233 | yes | 4 courses of 256 px, lower edges at y = 200 + 256k, `_Color` 0.92 |
| `IrregularPlanks_LightBrown.Folktails` | EnvironmentURP | 16 / 2,102 | (White's key) | White planks, `_Color` 0.66,0.56,0.41 |
| `PlasteredWood_White.Folktails` | EnvironmentURP | 10 / 1,960 | yes | plaster with lath streaks (no M) |
| `IrregularPlanks_White.Folktails` | EnvironmentURP | 14 / 1,894 | yes | 8 vertical planks of 128 px |
| `IrregularPlanks_Brown.Folktails` | EnvironmentURP | 37 / 1,572 | yes | own D |
| `IrregularPlanks_Mossy.Folktails` | EnvironmentURP | 10 / 86 | yes | own D/N/AO/M |
| `Sand.Folktails` | EnvironmentURP | 2 / 4 | yes | D + plaster N only |
| `IrregularPlanks_Yellow.Folktails` | EnvironmentURP | 0 / 0 | – | unused |
| `Dam.Folktails` | EnvironmentURP | 4 / 284 | – | 2048² own set |
| `Path.Folktails` | DirtURP (transparent, q 2998) | 1 / 62 | – | world-space UV (`_MainUVFromCoordinates` 1, scale 0.7), `_Color` 0.76,0.65,0.49 |
| `Hedge.Folktails`, `Shrub.Folktails` | VegetationURP | 8 / 5,650; 1 / 246 | – | cut-out, wind noise |
| `Bot.Folktails` | BotURP | 1 / 1,082 | – | 2048² D/E/N/M/AO |
| `FountainWater`, `Water` | FountainWaterURP / WaterURP | | – | |
| crops, trees (`Carrot`, `Maple`, …) | VegetationURP | | – | |

`Common` materials used by Folktails models and **not replaceable per faction** (Common is always loaded, so a
same-named material would be a duplicate): `Dirt` (153 models, construction ground), `BeaverCarryingModels`,
`DirtUnderground`, `BaseWoodCommon(_Amber)`, `PaperCommon`.

## The trick, two variants

| | "names" (data only) | "swap" (≈100 lines C#, no Harmony) |
|---|---|---|
| Files | `proto/look/mod` | `proto/look/mod-swap` + `proto/look/src/MaterialSwap.cs` |
| Faction | merge onto `Factions/Pandaborn/Faction.Inkpaws.blueprint.json`: `MaterialCollectionIds` = `["PandabornLook.Inkpaws"]`, `BaseWoodMaterial` = ours | unchanged (keeps `Folktails`) |
| Collection `PandabornLook.Inkpaws` | our 19 bundle materials + the 16 non-replaced vanilla Folktails entries | our 19 bundle materials only (not listed by the faction) |
| How | the repository finds our materials under the vanilla names | during `MaterialRepository.Load` our provider copies each bundle material's properties into the loaded vanilla material of the same name; restores on unload and on the main menu |
| Shader at render time | bundle copy of `EnvironmentURP` until the vertex-colour optimizer re-creates the material with `Shader.Find` | always the game's own |
| Other mods adding to `Folktails` / ChooChoo | **crash** | work (and their models are re-themed too, when they use vanilla names) |
| Folktails / Iron Teeth games | untouched (collection not listed) | untouched (provider does nothing unless the faction has a `PandabornLook.<FactionId>` collection) |

Both variants share one bundle: `pandabornprotolook_win`, 19 materials named exactly like the vanilla ones, all on
`Assets/TimberbornShaders/EnvironmentURP.shadergraph` (from the game's `Shaders.zip`), vanilla floats and colours
copied, `_Color` set per material.

## Results (in game)

All runs: Diorama map, 20 vanilla Folktails buildings placed by the harness around the district center (Lodge,
DoubleLodge, LumberMill, Inventor, WaterWheel, PowerShaft, SmallWarehouse, MediumTank, Campfire, Lantern,
PoleBanner, WindTurbine, GearWorkshop, Bakery, SmallPile, Shrub, WoodWorkshop, BeaverStatue, plus TripleLodge and
Gristmill placed **unfinished**, so their construction-stage models show at the start and get built during the
run), day shot at the start (hour ~4), night shot after 13.5 in-game hours (hour ~17.7), 2560×1440 off-screen
renders. Screenshots: `E:\PandabornDev\build\test\<run>\{day,night}_overview.png` (+ `_crop.png` around the town)
and `{day,night}_screen.png` (real screen with UI).

| Run | Variant, mods | Result |
|---|---|---|
| `look-inkpaws-1` | names, all 35 mods | **crash** at load: `Material BaseWood_Brown.Folktails is already loaded` (ChooChoo) |
| `look-inkpaws-2` | names, ChooChoo off | **crash**: `Material 1KA_DarkMetal.Folktails not found in repository` (KnatteAnka Staircase) |
| `look-inkpaws-3` | names, only Factions + Reskin, first (red-leaning) palette | PASS, 20/20 placed, 0 errors: the trick works |
| `look-inkpaws-4` | names, only Factions + Reskin, Sichuan palette | PASS, 0 errors |
| `look-swap-inkpaws-2` | **swap, all 35 mods** | **PASS**, 20/20 placed, 0 errors from us or the mods (only the known 31 `Assertion failed`); log: `re-themed 19 materials for faction Inkpaws`, `restored 19 materials on game unload` |
| `look-swap-folktails-2` | swap, all 35 mods, **Folktails** | **PASS**, 20/20, 0 errors; no swap log line (the provider did nothing); `day_overview_crop.png` shows vanilla thatch, brown wood and teal banners, i.e. unchanged (the colonists are pandas only because the Reskin is enabled) |

What the screenshots show (`look-swap-inkpaws-2/day_overview_crop.png`, same as `look-inkpaws-4`):

* Every vanilla building is re-themed: dark timber frames and posts, woven-bamboo wall panels (straw-gold), grey
  clay-tile roofs on the district center, lodges and workshops, white lime plaster walls on the warehouse, lattice
  windows, bamboo vats for the tank, cane bands on the wind turbine. It reads as a different, coherent faction at
  normal zoom. The pandas and the vanilla terrain, trees and path are unchanged.
* Construction stages (the open timber frames of the unfinished TripleLodge and Gristmill) use the same materials
  and look right. Power shaft, banner, lantern, statue, campfire: re-themed, no missing materials. No bot was
  present (bots use `Bot.Folktails`, kept vanilla in both variants).
* In the swap game the vanilla `FactionAtlas.Folktails` atlas was built (its usage list in `Player.log` names ~290
  models) and the buildings look identical to the un-atlased names run, so the atlaser ran *after* our swap and
  atlased our textures: the swap variant keeps vanilla's draw-call count.
* Night (`night_overview_crop.png`): the district center's lantern and the campfire glow; lodge and workshop
  windows give a faint warm glow; at this zoom the lattice pattern in the glow cannot be judged. A close-up camera
  in the harness would be needed to review windows properly.
* Not yet tested: an Inkpaws game followed by a Folktails game *in the same session* (main menu in between). The
  restore ran on unload (`restored 19 materials on game unload`) and the main menu has a second safety restore,
  but a two-game session needs a harness option to prove it.
* Honest assessment: convincing as a first pass and far better than expected for zero modelling. Weak spots: the
  woven panels are too yellow and too uniform on big walls; roof tiles read as grey stripes from above (the arched
  lips only show close up); the beaver-dome lodges and round domes stay beaver-shaped; the Beaver Statue is still
  a beaver; textures are flatter than the hand-painted vanilla ones.

## The replacement textures

Two generators, one output. **Region map:** every trim sheet's rectangles (which part is plank strip, log end,
window, banner, roof course...) and the texel density vanilla models use are in
[look-regions.md](look-regions.md) (generated by `src/pipeline/sheet_regions.py` into `src/pipeline/sheet_regions.json`).
Those rectangles are the vanilla layout, measured; they are what our sheets fill and what new Inkpaws models UV
against. If a region ever changes, `sheet_regions.json` changes in the same commit and the modelling side is told.

1. **Blender bake** (`src/pipeline/bake_sheets.py`, headless Cycles on the GPU, ~2 min for all six sets): small dioramas
   of real geometry laid into the regions, rendered straight down by an orthographic camera (1 unit = 1024 px) as
   diffuse-colour, normal and AO passes. Geometry is extended past the sheet edges and coloured by index modulo the
   period, so the sheets tile seamlessly, AO included. Fine detail (wood grain, bamboo fibres, clay mottling) is
   material noise with bump, which the normal pass picks up.
2. **Code painter** (`src/pipeline/look_textures.py`, numpy + Pillow, ~15 s): everything not baked, and the fallback
   for any baked set whose bake output is missing. It also finishes the baked sets: the albedo gets a painted light
   (soft upper-left key from the baked normals, times AO), as the hand-painted vanilla sheets have, so models do not
   look flatter than Folktails ones; normals are written in the game's swizzled layout; metallic/smoothness per set.

**No vanilla pixels are copied.** The vanilla textures are read only to measure the layout (rectangles, glass masks,
frame lines, plate seams).

| Set (→ materials) | Made by | What it looks like |
|---|---|---|
| `Timber` → BaseWood_Brown | Blender: bevelled sawn boards in every strip and across the long-grain block, log ends with rings on the discs, dark gaps | dark oiled fir, grain along the boards, darker board edges |
| `Bamboo` → BaseWood_White / LightBrown / Yellow (tints: weathered grey, cured straw-gold, fresh green) | Blender: split culms in the strips, whole thin culms in the long block, cut tube ends on the discs, lime wash between | culms with raised nodes and node grooves, fibre streaks |
| `Weave` → IrregularPlanks_White / LightBrown / Yellow; `WeaveCoarse` → _Brown; `WeaveMossy` → _Mossy | Blender: one plain-weave panel per vanilla plank column (16 px strands, 24 px for coarse), over-under strands, bamboo battens on the seams and a binding batten across the middle, repaired patches in fresher strands; panels alternate straw / grey-green / grey tones; mossy adds moss clumps | woven wall panels with visible framing, varied from panel to panel |
| `RoofTiles` → ThatchedRoof | Blender: clay pan-and-cover tiles, 16 pairs across, courses 256 px with the lip at y = 200 + 256k (vanilla rhythm), three overlapping tiles per course, cover end caps, moss in the channels near the lips, the odd replaced tile | rounded cover tiles catching light over darker channels |
| `Plaster` → Plaster_White | painter | white lime plaster |
| `PlasterLath` → PlasteredWood_White | painter | lime plaster with spalls showing rammed earth and bamboo laths |
| `LatticePaper` → Paper | painter, frame lines from the vanilla sheet | paper panels in dark timber frames, lantern-frame lattice |
| `Iron` → BaseMetal | painter, plate seams and rivets from the vanilla normal map | soot-dark forged iron, rust in the seams |
| `Banded` → PaintedMetal | painter, stripes from the vanilla sheet | straw-gold cane binding over black iron (no red) |
| `Windows` → WindowsAtlas | painter: glass = vanilla `_LightingMap` mask, frames = non-wall non-glass | dark timber frames, paper on a cracked-ice lattice, lime wall; `_LightingMap` = flat, strong warm lamplight across each pane, cut by the lattice |
| `Details` → Details | painter, regions by position | indigo banner with ink-painted bamboo; hemp sack; straw rope; plain colour labels with pictures; bamboo crates with cane lashing |
| `RammedEarth` → Sand, `Moss` → Moss | painter | layered rammed earth with pebbles; tea-green moss |

Previews: `E:\PandabornDevuild\look\preview\look_sheet.png` (albedo × tint of every material),
`baked_D.png` (the baked sets), `regions_<Sheet>.png` (each region map drawn over our sheet).

Still to raise, in order of value: bake the remaining sheets too (windows with modelled frames and lattice,
details' crates, plaster with timber framing); stronger painted contrast on Timber (grain still reads soft at game
zoom); the path (`Path.Folktails`, DirtURP, world-space UV) is still vanilla and needs a `PathMaterial` of ours;
roof **ridges** are model geometry, not part of the sheet, so a clear ridge needs new models (the sheet only has
courses).

## Build and test commands

```powershell
# 1. region map (+ docs/tech/look-regions.md); --density re-measures texel density from the game's models
E:\PandabornDev\tools\venv\Scripts\python.exe -I src\pipeline\sheet_regions.py [--density "<Timberborn_Data>"]
# 2. Blender bakes into E:\PandabornDev\build\look\bake\<Set>\ (bash, env vars from CLAUDE.md "Art toolchain")
$BL -b --factory-startup --python src/pipeline/bake_sheets.py -- src/pipeline/sheet_regions.json E:/PandabornDev/build/look/bake [Timber,Bamboo,Weave,WeaveCoarse,WeaveMossy,RoofTiles]
# 3. textures + Unity batch build
powershell -ExecutionPolicy Bypass -File tools\build_look.ps1
#   -BundleName pandabornlook   the shipping bundle for the Pandaborn.Look module, into E:\PandabornDev\build\look\AssetBundles
#   -SkipTextures      reuse the PNGs already in the Unity project
#   -Only Windows,RoofTiles   repaint only these sets
#   -Mac               also build <name>_mac (fails with a clear message until Mac Build Support is installed)
#   -Setup             recreate E:\PandabornDev\unity\PandabornLook from the official template + Shaders.zip
# default output: E:\PandabornDev\build\proto\look (data-only prototype mod + pandabornprotolook_win)

# the pieces, by hand
E:\PandabornDev\tools\venv\Scripts\python.exe -I src\pipeline\look_textures.py --unity E:\PandabornDev\unity\PandabornLook
"C:\Program Files\Unity\Hub\Editor\6000.5.11f1\Editor\Unity.exe" -batchmode -quit -nographics `
    -projectPath E:\PandabornDev\unity\PandabornLook -logFile E:\PandabornDev\build\look\unity_build.log `
    -executeMethod PandabornLookBuilder.Build -lookOut E:\PandabornDev\build\proto\look\AssetBundles
dotnet build proto\look\src -c Release -p:ModOut=E:\PandabornDev\build\proto\look-swap

# reference dumps (once per game update; output stays on E:)
E:\PandabornDev\tools\venv\Scripts\python.exe -I src\pipeline\extract_vanilla_materials.py `
    "C:\Program Files (x86)\Steam\steamapps\common\Timberborn\Timberborn_Data" E:\PandabornDev\reference\Blueprints E:\PandabornDev\reference\vanilla-assets
E:\PandabornDev\tools\venv\Scripts\python.exe -I src\pipeline\vanilla_material_usage.py `
    "C:\Program Files (x86)\Steam\steamapps\common\Timberborn\Timberborn_Data" E:\PandabornDev\reference\vanilla-assets

# in-game checks (20 vanilla buildings, 2 of them unfinished; day shot at start, night shot 13.5 h later)
powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -ExtraMods E:\PandabornDev\build\proto\look-swap `
    -RequestJson proto\look\tests\retheme.request.json
powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Folktails -ExtraMods E:\PandabornDev\build\proto\look-swap `
    -RequestJson proto\look\tests\retheme.request.json
```

The Unity project (`E:\PandabornDev\unity\PandabornLook`, 1.9 GB with Library) is a fresh project made from the
official `mechanistry/timberborn-modding` template (its `ProjectSettings`, `Packages` and URP `Assets/Rendering`, so
shader variants are compiled with the same URP settings the game uses) plus `Assets/TimberbornShaders` = the game's
`Shaders.zip`. The template's own editor tools are not copied (they need the game DLLs imported; we do not need
them). The owner's `PandaFurProject` on C: was not touched. UPM caches go to `E:\PandabornDev\unity\cache`; Unity
still keeps a small Bee cache in `%LOCALAPPDATA%\Unity\Caches` (43 MB in total, pre-existing).

## Costs

* **Disk / download:** `pandabornprotolook_win` 38.7 MB (LZ4 chunk compression). A `_mac` copy would roughly
  double the mod's size.
* **Memory:** 61 textures × 1024² BC7 with mips ≈ 1.33 MB each ≈ 81 MB of GPU memory, plus the same again in RAM
  because they are imported **readable** (needed only if they are to be atlased, as the vanilla ones are). Loaded
  only when the materials are loaded, i.e. in Inkpaws games. Turning `readable` off in `look_spec.json` halves it if
  atlasing is given up. Fewer, shared sets (the three bamboo materials already share one) bring it down further.
* **Draw calls:** (swap variant: measured indirectly, the vanilla atlas was built from our textures in `look-swap-inkpaws-2`, so as vanilla.) Vanilla Folktails buildings are atlased into one material per building at load. Our materials
  are not atlas fragments in the "names" variant, so a building renders one submesh per distinct material (about
  3–6 instead of 1–2). In the "swap" variant the vanilla `FactionAtlas.Folktails` entry points at the very material
  objects we overwrite; whether the atlas is then built from our textures or skipped depends on whether
  `AutoAtlaser.Load` runs before or after `MaterialRepository.Load` (both safe: the three weave variants exist so
  that no two fragments share a texture set, which would throw). Not measured yet; the frame rate in the test runs
  was not noticeably different, but these are small towns.
* **Build time:** textures ~15 s (`look_textures.py`, all 15 sets); Unity first import of the project ≈ 5 min
  (packages + shader graph import), afterwards 1–4 min per bundle build (BC7 compression and texture re-import dominate; 244 s measured with `-SkipTextures`); DLL 8 s.
* **Code to maintain (swap variant):** one class, public game APIs only (`IMaterialCollectionIdsProvider`,
  `ISpecService`, `FactionService`, `MaterialCollectionSpec`) plus Unity's `Material.CopyPropertiesFromMaterial`.
  It depends on one implementation detail: that `MaterialRepository.Load` enumerates the providers before any model
  is built. If that ever changes, models built earlier would show vanilla textures (no crash).

## Problems found

1. **Names variant vs other mods (blocking for that variant).** With all 35 of the owner's mods:
   `InvalidOperationException: Material BaseWood_Brown.Folktails is already loaded` (ChooChoo's
   `BaseFactionMaterialsProvider` adds `ChooChoo.FolktailsMaterials`, the vanilla Folktails materials, to every
   faction that does not list `Folktails`). With ChooChoo off: `Material 1KA_DarkMetal.Folktails not found in
   repository` (KnatteAnka's Staircase adds a Folktails building whose material sits in the `Folktails` collection).
   Any faction mod that drops `Folktails` but keeps `Buildings.Folktails` has this problem. The swap variant fixes
   both by keeping `Folktails`.
2. **`Common` materials cannot be re-themed per faction** by either variant without also changing them for every
   faction's models in that game (`Dirt` under construction sites, `BeaverCarryingModels` for carried goods). In an
   Inkpaws-only game that would be acceptable for the swap variant (the change is per game session), but it is not
   done yet.
3. **The path stays vanilla brown dirt** (`PathMaterial` is DirtURP with world-space UVs, a different shader). It
   needs its own material (`FactionSpec.PathMaterial`, data only) and a 2048² tiling texture.
4. **Domed thatch roofs** on several vanilla workshops become tiled domes, which is not Sichuan; and the vanilla
   lodges are beaver-dome shaped whatever the material. See the recommendation.
5. **Vertex colours baked into vanilla models** darken some areas (they were tuned for brown wood). On pale bamboo
   and white plaster this reads as dirt patches in places. Mostly fine at game zoom.
6. **Woven bamboo reads strongly yellow** at a distance on the large flat walls (district center, warehouses); tints
   were muted once, could go further toward grey-gold.
7. **The bundle ships a second copy of the `Shader Graphs/EnvironmentURP` shader** (as every mod with building
   materials does). In the names variant it renders until the vertex-colour optimizer swaps in `Shader.Find`'s
   copy; in the swap variant it is never used. No visual difference was seen in either the Inkpaws or the Folktails
   runs.
8. **Test queue:** several agents share one game instance; a run waits up to `-WaitForGameSeconds` (default 1800 s)
   for the lock and then gives up with exit code 2. Long water tests hold the lock for up to an hour, so look runs
   used `-WaitForGameSeconds 10800`.
9. **Unity batch builds must not be killed:** wrapping `build_look.ps1` in `timeout` crashed the editor on shutdown
   (the bundle was not replaced). Run it in the background instead.

10. **A bundle file must keep the name it was built with.** A copy of `pandabornprotolook_win` renamed to
    `pandabornlook_win` loads at start, but when the game returns to the main menu `ModAssetBundleLoader` matches
    already-loaded bundles by file name, does not recognise it, loads it again and Unity refuses ("another
    AssetBundle with the same files is already loaded"): crash (`look-module-then-1`). Always build the shipping
    bundle as `tools/build_look.ps1 -BundleName pandabornlook`.
11. **Night windows only glow on lit buildings.** Window glow (`_LightingMap`) shows only while the building's
    illumination is on (an occupied house, a working workplace, a district center); in a fresh test town most
    buildings are dark at night in Folktails and Inkpaws alike. The close-up shots therefore switch lighting on for
    the framed building (`"lit": true`, harness `MaterialColorer.EnableLighting`). Our glow map is flatter and
    brighter than vanilla (mean luminance over the glass ≈ 0.93 vs 0.71).

## Character material for the Inkpaws

* The body mesh asks the repository for the material named in the timbermesh (`BeaverAdult` / `BeaverChild`, both
  in `Common`). `Common` is always loaded, so a faction cannot ship its own material under those names (duplicate),
  and copying into the Common material (the swap trick) would also hit every other faction's beavers in that game
  only, which is acceptable *within* an Inkpaws game but means Folktails-model characters in the same game (none
  today) would change too.
* The clean way: the Inkpaws already have their own meshes (`Characters/Pandaborn/InkpawAdult|InkpawChild.Model`).
  Re-export them with the material renamed (`PandabornInkpawAdult`, `PandabornInkpawChild`), put bundle materials of
  those names in an Inkpaws-only collection, and list that collection in `FactionSpec.MaterialCollectionIds` (adding
  a new name never conflicts; this part is data-only and mod-safe).
* The material must be on a shader derived from `BeaverURP.shadergraph` (shipped in `Shaders.zip`): it carries the
  vertex-animation code (`AnimateVAT.hlsl`: `_AnimationTime`, `_AnimatedVertexCount`, `_FrameCount`, `_Offsets`,
  `_Rotations`, `_AnimationEnabled`, `_Looped`) and the properties the game sets per character through
  `CharacterMaterialModifier` (`renderer.material.Set*`): `_BaseMap` (coat, `BeaverTextureSetter`),
  `_WorkerOutfitDiffuse` / `_WorkerOutfitNormal`, `_TailDecalDiffuse` / `_TailDecalGradient`, `_BumpMap`,
  `_EmissionMap`, `_BeeStingMap` / `_BeeSting`, contamination (`_ContaminationDiffuse`, `_BadwaterContamination`),
  injuries, `_WetFur`, `_MudPit`, `_TintColor` / `_TintEnabled`. A copy of the graph with new normal/AO/fur maps
  (or the Reskin's shell-fur passes added) keeps all of that working; renaming the graph path avoids a name clash
  with the game's shader.
* Not affected: other factions (they keep `BeaverAdult`), outfits and coats (still set by name on the instance).
  The Reskin's `PandabornFactionSkins` only rewrites textures, so it still works on top.

## Mac bundles

* `C:\Program Files\Unity\Hub\Editor\6000.5.11f1\Editor\Data\PlaybackEngines` holds only
  `windowsstandalonesupport` (1.1 GB). `BuildTarget.StandaloneOSX` therefore cannot be built; `build_look.ps1 -Mac`
  checks `BuildPipeline.IsBuildTargetSupported` and warns instead.
* Installing it: "Mac Build Support (Mono)" for 6000.5.11f1 (changeset `5c3a1087d8e4`), either from Unity Hub
  (*Installs → 6000.5.11f1 → Add modules*) or the stand-alone installer
  `https://download.unity3d.com/download_unity/5c3a1087d8e4/TargetSupportInstaller/UnitySetup-Mac-Mono-Support-for-Editor-6000.5.11f1.exe`
  (523,284,776 bytes; needs admin because the editor lives in Program Files; installs into the editor folder on C:,
  roughly 1.5 GB). Not installed, as instructed.
* **What a Mac player sees today** (read from the code path, not run on a Mac): `ModAssetBundleLoader` skips files
  ending `_win` on macOS, so our bundle never loads. The `PandabornLook.Inkpaws` collection's `AssetRef<Material>`s
  are lazy; resolving one calls `IAssetLoader.Load`, which throws for a missing asset. `Pandaborn.Look` resolves each
  replacement inside its own try/catch, counts it as unavailable, copies nothing, and logs one line ("not available
  (asset bundle missing?)"). The faction still lists the vanilla `Folktails` collection, so every model finds its
  materials: **a Mac player gets the plain Folktails look, no error**. (The old data-only "names" variant would have
  crashed on Mac: its faction lists only our collection, whose materials would be missing.)
* `tools/build_look.ps1 -Mac` is ready: it passes `-mac` to the Unity builder, which builds `<name>_mac` for
  `StandaloneOSX` after the Windows bundle, and fails with a clear message while the module is missing.

## Recommendation: how to produce the whole look

1. **Adopt the swap variant as the faction's base layer** (move `MaterialSwap.cs` into the faction DLL, collection
   `PandabornLook.Inkpaws` into `mod/PandabornFactions`, bundle into the shipped mod with `_win` and `_mac`). It
   re-themes all ~315 vanilla Folktails building models plus every mod building that uses vanilla Folktails
   material names, for ~40 MB and no modelling, and it is compatible with the mods that broke the data-only form.
   Keep the data-only "names" variant only as a fallback if a game update ever changes `MaterialRepository`'s
   provider timing (the swap code fails safe: it logs and restores).
2. **Author every new Inkpaws model against the same trim sheets and the same vanilla material names**
   (`BaseWood_Brown.Folktails` = dark timber, `ThatchedRoof.Folktails` = clay tile, `WindowsAtlas.Folktails` =
   lattice windows, …). New models then share one material set and one runtime atlas with the re-themed vanilla
   ones, need no new materials, and get every future texture improvement for free. Only genuinely new surfaces
   (lantern paper with glow, flume water, tea bushes) need new material names, in an Inkpaws-only collection.
3. **Improve the sheets before modelling much**: rebake the 13 sets in Blender at the extracted layouts (real
   bamboo/board/tile geometry baked to D/N/AO), keep the code painter for masks and fallbacks.
4. **Which buildings can ride on re-themed vanilla models** (shape is generic: boxes, frames, sheds, machinery):
   storage (piles, warehouses, tanks read as vats), most workshops (lumber mill, wood/gear workshop, bakery, grill,
   gristmill, smelter, paper mill, printing press), power shafts, clutches, gravity battery, water wheel (reads as a
   noria), pumps and water infrastructure (levees, dams, floodgates, valves, sluices), paths, platforms, stairs,
   ziplines, tunnels, district crossing, hauling post, builders' hut, scavenger/gatherer/lumberjack flags, fences,
   benches, banners, lanterns, the bot factories. Nobody looks at these for faction identity once the materials
   match.
5. **Which need new models to feel like their own faction** (silhouette and the buildings a player looks at most):
   * **Housing**: the vanilla lodges are domed beaver lodges; with tile and plaster they read as odd yurts. Inkpaws
     need courtyard houses with hipped tile roofs, stilt houses, and the Ringtail lofts (one vocabulary, smaller
     scale).
   * **District center** and the **wonder**: the faction's signature buildings.
   * **Anything beaver-shaped or beaver-coded**: Beaver Statue, the Scratcher-like wellbeing buildings, Teeth
     Grindstone, Mud Pit, Lido, Sauna and the Folktails monuments; replace with panda equivalents (tea house,
     bamboo grove shrine, hot pot, kite field).
   * **Design-specific buildings** from DESIGN.md: bamboo flume, noria, treadwheel, terraces, granary, pickle cellar,
     scroll library, lantern and firework workshops, kite windmill, and the Lantern Festival dressing (red paper
     lanterns are the main legitimate use of red).
   * **Domed roofs in general**: several Folktails workshops have round thatched domes; tiled domes are not
     Sichuan. If those buildings stay, a later pass could swap only their roof node for a hipped one.
