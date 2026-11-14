# Plant models: vanilla craft, rules, the plant kit, results

Status: 2026-11-14, game 1.1.2.8. Read from the vanilla plant models (dumped by `src/pipeline/dump_vanilla_models.py`
into `E:\PandabornDev\reference\vanilla-plants`, never committed), the vanilla blueprints and materials
(`E:\PandabornDev\reference\{Blueprints,vanilla-assets}`), the decompiled game and `VegetationURP.shadergraph`
(`E:\PandabornDev\reference\Shaders`). **The rules below are the acceptance criteria for every Inkpaws plant.** In-game
results are in [Results](#results).

## How the game shows a plant (decompiled)

| What the player sees | Where it comes from |
|---|---|
| Planting a field (ghost) | `PlantablePreviewModelSpec.Model`: vanilla uses the **Mature** model |
| Planted, growing | `#Models/Seedling/#Alive` until `Growable` finishes. **There are exactly two growth stages**: no scaling, no intermediate model; growth progress is only a timer for the UI |
| Grown | `#Models/Mature/#Alive` |
| Dry (any dying cause: dry soil for watered plants, wet roots for arid ones, flooding, contamination) | `<stage>/#Dying` while any `IDyingProgressProvider` reports dying (`NaturalResourceLifecycleModel`) |
| Dead | `<stage>/#Dead` |
| Ripe (gatherables: bushes, fruit trees) | **the same Mature model with its material's detail map switched on**: `GatherableModel` sets `_EnableDetail` 1 on every renderer under `Mature` (instancing the material) while the yielder has yield and the plant is not dead; 0 after gathering. Blueberries and chestnuts are drawn this way |
| Harvested crop | nothing: crops have `CuttableSpec.RemoveOnCut`; the entity is deleted once its good stack is carried away (the pile is the generic good stack) |
| Tree being cut | `TreeShaker` rocks the whole entity and sets `_IsShaking` (wind sway off); no falling animation |
| Cut tree | `#Models/#Leftover` (the stump, `CuttableSpec.LeftoverModelName`) plus the log pile (good stack) until the stump is overridden |
| Variation | `NaturalResourceModelRandomizerSpec`: per instance random rotation (free, by 90 degrees or a range) and height/width scale |

The model root is placed at the cell corner and the plant is rotated about the cell centre (`NaturalResourceModel`
moves its children by (0.5, 0, 0.5)), so a plant model is authored in cell space: x, z in 0..1, y up from the ground.

## What vanilla plants are made of

### Models and budgets (triangles; heights in tiles)

| Plant | Seedling | Mature | Dry | Dead | Stump | Heights (seedling / mature) |
|---|---|---|---|---|---|---|
| Carrot | 120 | 192 | 162 | 126 | | 0.16 / 0.26 |
| Potato | 32 | 57 | 57 | 57 | | 0.20 / 0.20 |
| Wheat | 120 | 120 | 120 | 120 | | 0.36 / 0.64 |
| Cattail (aquatic) | 36 | 135 | 135 | 165 | | 1.05 / 1.25 |
| Sunflower | 129 | 192 | 198 | 192 | | 0.52 / 1.24 |
| Kohlrabi (IT) | 128 | 230 | 222 | 166 | | 0.36 / 0.51 |
| Corn (IT) | 101 | 232 | 232 | 232 | | 0.70 / 1.37 |
| Blueberry | 37 | 61 | 61 | 61 | | 0.25 / 0.42 |
| Coffee (IT) | 102 | 138 | 138 | 110 | | 0.38 / 0.73 |
| Birch | 84 | 129 | 129 | 73 | 18 | 0.90 / 1.92 |
| Pine | 40 | 135 | 135 | 110 | 35 | 1.26 / 3.01 |
| Oak | 64 | 172 | 169 | 176 | 45 | 0.86 / 2.26 |
| Chestnut | 114 | 162 | 162 | 50 | 42 | 0.76 / 2.22 |
| Mangrove (IT) | 153 | 285 | 285 | 142 | 36 | 1.08 / 1.52 |

* **One node, one submesh, one material per model** (`Carrot`, `Birch`, ...). The dry model is usually the alive geometry
  with other vertex colours (and sometimes other atlas regions); the dead one is often new geometry (flopped leaves,
  bare branches). Crops overhang their cell by up to 0.25, tree crowns by up to 0.3.
* **Canopies are 30-60 big leaf-cluster cards laid like shingles** (normals mostly 35-65 degrees from vertical, leaning
  out), on a 5-7 sided tapered trunk. Vertex normals are the face normals bent upward a little. Leaf vertex colours are
  dark (about 0.2, 0.3, 0.12 on a near-white texture); trunks white or light.

### Materials (all `Shader Graphs/VegetationURP`)

* Collections: Folktails lists Carrot, Cattail, Potato, Spadderdock, Sunflower, Wheat, ChestnutTree, Maple, Dandelion;
  Common lists Birch, Oak, Pine, Blueberry, Succulent; Iron Teeth the rest. An Inkpaws game reaches Folktails + Common.
* Textures 1024 px (some 512), BC7, readable, repeat: `_MainTex` RGBA (alpha = cut-out), `_BumpMap` swizzled like the
  building maps (R = 1, G = B = y, A = x), optional `_DetailMap` (yield sprites) and `_MetallicGlossMap`. **Leaf sprites
  are near-grey and take their hue from the vertex colour**; bark and fruit are painted in colour.
* From the graph: albedo x saturate(vertex colour); alpha clip at 0.5; **front faces only** (`RenderFace` Front: a card
  seen from behind is invisible); wind = `ComputeWindOffset` driven by **uv1.y** (0 = rooted, 1 = free; `_SwayStrength`,
  `_SwaySpeed`, `_SwayExponent`, flutter above `_FlutterThreshold`, `_WindModifier`), switched off by `_IsShaking`;
  **detail sampled with uv2**: where its alpha is set and `_EnableDetail` is 1, the colour is the detail colour (times
  the vertex colour with `_DetailUseColor`) and the alpha is max(albedo, detail), so a yield sprite can sit on a part
  whose albedo is transparent.
* Not atlased (the runtime atlaser only takes EnvironmentURP); `VertexColorPrefabOptimizer` re-creates the material with
  the game's own shader at load and keeps the properties listed in `VegetationMaterialProperties` (textures, sway,
  flutter, detail): a bundle's copy of the shader is never drawn.

### Fields of 100+

Cheapness comes from tiny meshes (60-290 triangles), one material and one submesh per plant, alpha-tested cards instead
of geometry, and no per-frame code (wind is in the vertex shader). Variety comes from the randomizer (rotation, scale)
and the per-vertex colour jitter painted into the model. Only gatherables pay for a material instance each (the detail
toggle).

## Rules for every Inkpaws plant (acceptance criteria)

1. **Stages:** Seedling and Mature, each Alive, Dry and Dead; trees also a stump. Gatherables show their yield only
   through uv2 detail, nothing else changes. Crops need no harvested model.
2. **Budget:** within 1.25 x the vanilla maximum for the stage and kind (crops: seedling 176, mature 290; bushes: 146,
   247; trees: 191, 356, stump 60). The kit's report flags anything over.
3. **One root node named like the file, one material, one submesh.** Model paths `NaturalResources/Pandaborn/<Kind>/<Id>/<Id><Stage>`.
4. **Cell space**, standing on y = 0, overhang at most about 0.3; height inside the blueprint's block height.
5. **Cards face up and out.** Back faces are culled and the camera looks down at 40-70 degrees, so a card rising
   outward steeper than ~45 degrees vanishes on the near side. Rising cards stay under ~40 degrees; steep sides are
   built from drooping, shingled cards whose up face is their outer face (`plant.shingle`). Vertical cards (rice tufts,
   pepper twigs, mushrooms) are two-sided.
6. **uv1.y = sway weight** rising from 0 at the ground to 1 at the tips (`plant.auto_sway`), uv2 on every vertex (a
   transparent texel where there is no yield).
7. **Vertex colours carry hue and state** on near-grey leaves: fresh / dry (straw) / dead (grey-brown), per-part jitter,
   ground occlusion; leaf values in vanilla's range so plants sit beside birch, pine and chestnut.
8. **Readable en masse from the game camera** and distinct from every vanilla plant; red only as small accents; no
   writing; nothing Japanese-coded.
9. **`model.json`** beside the script records the model paths per blueprint child, preview model, recommended
   randomizer, colliders, cutting radius and the material.

## Materials: why a bundle, and how it is built

No reachable vanilla vegetation texture can carry bamboo culms and sprays, napa cabbage, rice panicles, tea or Sichuan
pepper, and the persimmon's orange fruit cannot be drawn with the chestnut's detail map. So the plants have their own
materials, from **their own bundle**, separate from the look lane's:

* `tools/build_plants.ps1` (Unity project `E:\PandabornDev\unity\PandabornPlants`, builder
  `src/unity/PandabornPlants/Editor/PandabornPlantsBuilder.cs`, `-Setup` creates the project from the official template
  and `Shaders.zip`, `-Mac` builds `_mac` when Mac Build Support is installed) paints the textures
  (`src/pipeline/plants/textures.py`) and builds `E:\PandabornDev\build\plants\AssetBundles\pandabornplants_win`.
* Seven materials on `VegetationURP`, one per plant (each tunes its own wind), all sharing **one painted atlas**:
  `PandabornPlants_D` (2048, alpha cut-out), `PandabornPlants_N` (2048), `PandabornPlants_Detail` (1024). Asset paths
  `Materials/Pandaborn/Plants/<name>`, names `PandabornTimberBamboo`, `PandabornShootBamboo`, `PandabornCabbage`,
  `PandabornRice`, `PandabornTeaBush`, `PandabornSichuanPepper`, `PandabornPersimmonTree`.
* Collection `PandabornPlants.Inkpaws` (Inkpaws only), which the faction lists. Bundle about 5.6 MB.
* No vanilla pixels are used: every sprite is painted by code (leaves with painted light and drop shadows, culms with
  nodes and waxy bands, bark plates, sheaths, berries, fruit, bamboo fungus).

## The plant kit (`src/pipeline/plants/`)

| Module | Does |
|---|---|
| `mesh.py` | `Mesh` with the vegetation streams (P, N, uv0, uv1 wind, uv2 detail, colour), quads, ribbons (`strip`), tubes, discs; the `.timbermesh` writer (via `src/pipeline/tmesh_static.py`); a reader/exporter of any model for the previews |
| `atlas.py` | the atlas layout (pixel rectangles) shared by the painter and the models; `uv()`, `duv()`, `sub()`, `disc()`, the blank texel |
| `textures.py` | the painter (leaf, stroke, blob primitives; culm, bark, sheath strips; sprays, clusters, tea mass, cabbage leaf, rice tufts and panicles, pepper leaves and berries, soil; detail sprites), normal map, Unity spec |
| `plant.py` | `Plant` (stages x states -> files, report against vanilla budgets, `model.json`), parts: `card`, `shingle`, `upright`, `crossed`, `stem`, `mound`; colour helpers (`state_tint`, `jitter`, `ambient`) and `auto_sway` |
| `preview.py`, `blender_field.py` | Blender Cycles field previews of any models, ours and vanilla, with the shader's cut-out, back-face culling and detail emulated, water planes |
| `preview_plant.py` | standard field (20+ plants beside the vanilla neighbours) and state-row previews per plant |

```
E:\PandabornDev\tools\venv\Scripts\python.exe -I art\plants\PandabornTeaBush\build.py        # one plant
E:\PandabornDev\tools\venv\Scripts\python.exe -I src\pipeline\plants\preview_plant.py PandabornTeaBush
powershell -ExecutionPolicy Bypass -File tools\build_plants.ps1                               # textures + bundle
powershell -ExecutionPolicy Bypass -File proto\plants\build.ps1 [-Models] [-Bundle]           # dev mod
E:\PandabornDev\tools\venv\Scripts\python.exe -I proto\plants\tools\gen_requests.py           # test requests
powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -NoBuild -Faction Inkpaws -Map Plains `
    -OnlyMods JigglyPanda.PandabornFactions -ExtraMods E:\PandabornDev\build\proto\plants `
    -RequestJson proto\plants\tests\states.request.json -TimeoutSeconds 2700 -WaitForGameSeconds 10800 -NoBatchControl
```

(Results, per-plant notes and the catalogue hand-over follow below.)
