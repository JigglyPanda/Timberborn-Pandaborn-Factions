# Building models: vanilla craft, rules, and the building kit

Status: 2026-11-14, game 1.1.2.8. Read from the vanilla models (dumped by `src/pipeline/dump_vanilla_models.py` into
`E:\PandabornDev\reference\vanilla-models`, never committed), the vanilla blueprints, the decompiled game, and renders
of both in the faction's materials. **These rules are the acceptance criteria for every Inkpaws model.** In-game results
are in [Results](#results).

## What the vanilla models do

### Budgets (Folktails building models, triangles)

| Footprint | Typical | Examples |
|---|---|---|
| 1x1 | 150–500 | Bench 152, Hammock 248, Lantern 246, Small Tank 390, Medical Bed 342 |
| 1x2 / 1x3 | 180–660 | Throttling Valve 256, Fill Valve 176, Mini Lodge 470, Detailer 659 |
| 2x2 | 600–1200 | Lodge 662, Double Lodge 852, Inventor 922, Medium Tank 914, Grill 1191 |
| 3x2 / 2x3 | 800–1700 | Triple Lodge 1082, Water Wheel 1212, Bakery 1703, Efficient Farmhouse 1500, Gristmill 1484 |
| 3x3 | 1000–2200 | District Center 1788, Wind Turbine 1650, Large Tank 1210, Campfire 1028 |
| 5x5 | 2000–6500 | Agora 6388, Domed Garden 6483, Carousel 2494 |

Construction stages are 150–1000 triangles (median about 350), roughly a third of the finished model. Every model is
one root mesh merged by material (the game merges by material again at load); animated parts and slots are child
nodes. These are small numbers: vanilla's look comes from chunky shapes and the textures, not from geometry.

### Silhouette and proportions

* Chunky, slightly irregular, hand-made: posts are 6- or 8-sided prisms 0.08–0.12 thick with log-end discs on top,
  roofs are thick slabs with wavy edges, walls lean and bulge a little. Nothing is perfectly straight.
* Exaggerated parts: doors are big (0.45 wide, 0.6–0.7 tall on a 1-high building), roofs and chimneys oversized.
* The game camera looks down at 45–60°: **the roof is most of what a player sees.** A building is recognised by its
  roof shape, its top-mounted parts (chimney, tower, wheel, sails) and one or two strong colours, not by its walls.
* Models fill their footprint and overhang it by up to about 0.05–0.15 (eaves, wheels in water overhang more).

### Trim sheets and texel density

* **Every UV is inside 0..1.** The sheets are fixed-region trim sheets, not tiling textures, and the runtime atlaser
  packs 15 Folktails materials 4x4 into one atlas by remapping `uv * 1/4 + offset`: a UV outside 0..1 bleeds into
  a neighbour.
* Texel density is about **500 px of the 1024 sheet per tile edge** (median 523 for timber, 516 for roofs, 443 for
  windows). Long pieces compress, small ones use the same density.
* The BaseWood sheet (timber; and the three bamboos, which share its layout) has: a long-grain block (u 0–0.56),
  five long strips (u 0.56–1, v 0.5–1), seven short strips, and log-end / culm cross-section discs (lower right).
  A pole maps its length along a strip and its circumference across it; its ends map to a disc.
* `ThatchedRoof` (our grey tile): four courses, lower edges at v = 0.055 + 0.25k, sixteen tile columns across.
* `WindowsAtlas`: glowing panes in fixed regions (cracked-ice square lower right, round window, four-pane strip, tall
  pane), dark doorways in the lower-left quarter (vanilla doors use u 0.11–0.40, v 0.05–0.39), plain lime wall.
* `Details`: banner (indigo with the ink bamboo), hemp sack, rope (along v), three labels (red, green, blue), crates.
* Uniform sheets (plaster, weave, rammed earth, moss) are planar-mapped at the same density.

### Vertex colour

About half the wood models and almost all metal models carry vertex colours, multiplied onto the albedo (and the
material's `_Color` tint is multiplied into them at load): ambient occlusion at the base and in corners, darker
undersides, and per-part tinting. Means are 0.8–1.0, minimums 0–0.5. White means unshaded.

### Construction stages

`#Unfinished` holds a nested `ConstructionBase<X>x<Y>` (the dirt pad, shared) and `ConstructionStage0` (sometimes
more, with `ConstructionSiteProgressVisualizerSpec.ProgressThresholds`). The stage model is the building's timber
skeleton in `BaseWood_Brown` only: posts, beams and arches outlining the finished shape, at 60–100 % of its height,
with no walls, roof or glass. The finished model replaces it when construction ends.

### Entrances, slots and access

* `BlockObjectSpec.Entrance.Coordinates` is the cell *in front of* the door (outside the footprint, usually y = -1).
  The door belongs on that side of the model, centred on that cell's x.
* Colonists walk to `BuildingAccessibleSpec.LocalAccess` (inside the doorway) and disappear; the model's door must
  be at that line.
* `#Slot#<Keyword>…` empty nodes place colonists: `TransformSlotInitializerSpec` matches nodes whose name *starts
  with* `#Slot#` + keyword (`Seat1`…`Seat5` for keyword `Seat`), with an animation (Sitting, Swinging, …). A slot
  can be a child of an animated node (the hammock's sleeper swings with it). Workshops use one `#Slot#Entrance`
  with `WorkshopWorkerHiderSpec`.

### Animated parts

* Animation is **node animation inside the timbermesh**: a child node with one `NodeAnimation` (vanilla: named
  `Default`, 100 frames at 24 fps, per-frame position/rotation/scale). The game adds a `TimbermeshAnimator` to the
  model root that plays the **first** animation, looped, and interpolates between frames.
* The blueprint drives *whether and how fast* it plays, through a component on the building, not through names:
  `WaterPoweredGeneratorAnimator` (decorates `WaterPoweredGenerator`: speed from the measured current),
  `WindPoweredGeneratorAnimator`, `MechanicalNodeAnimator` (`MechanicalNodeAnimatorSpec`: powered workshops),
  `EnterableAnimationController` (`EnterableAnimationControllerSpec`: plays while occupied: the hammock),
  `WorkshopAnimationController`.
* Wheels: the node's pivot is the axle; frames are one full turn (frame 99 = identity, frame 0 = 1/100 turn).
  The hammock's node sits under a rotated `Pivot` node and swings ±15° about its local z.
* Vertex animation exists (characters) but no building uses it.

### Night lights

* Glow comes only from `WindowsAtlas`'s `_LightingMap`: lit texels of windows and doorways glow when the building's
  illuminator is on (`EnterableIlluminatorSpec`: someone inside; `WorkplaceIlluminatorSpec`: someone working;
  `StockpileIlluminatorSpec`). There are no light sources in the mesh; fires and lamps are prefab attachments.
* So anything meant to glow at night (windows, lanterns, the stove's mouth) must be mapped to a lit region of
  `WindowsAtlas`.

### What the blueprint needs from the model

Footprint and per-cell `Blocks` (occupations decide what can stand on, under and beside it: `Corners` only = legs, a
path can pass beneath, as the Double Platform), entrance cell, `LocalAccess`, slot node names, animated node and its
driver, box colliders for picking, `TemplateAttachmentsSpec` positions (district fire, workshop smoke) in model
space, construction-base size, and for water parts the water cells (horizontal obstacles), solid cells (water
obstacles), input/output cells. Every building script records these in its `model.json`.

### Materials and culling

Models name the vanilla Folktails materials; the faction's look swaps their textures (docs/tech/look.md), so new
models share one material set and atlas with the re-themed vanilla ones. `_Cull` is 2 (back faces culled): thin
things seen from both sides (cloth, banners, mats) need both faces. The winding rule and tangent convention are in
`src/pipeline/tmesh_static.py`.

## Rules for every Inkpaws model (acceptance criteria)

1. **Budget:** within 1.25x the vanilla p90 for its footprint (2x2: 1500, 3x3: 2750); the kit's report flags it.
   Construction stage under about 1000.
2. **UVs inside 0..1, in the matching trim region, at about 500 px per tile;** no stretched or mismatched regions.
3. **Vanilla material names only** (listed in `src/pipeline/kit/core.py`); new names only for genuinely new surfaces,
   in an Inkpaws-only collection.
4. **Footprint:** fills its cells, overhangs at most 0.35 (eaves), more only where the thing stands in water (wheels).
   Height inside the blocks it occupies, roofs may rise into an occupied top block.
5. **Readable from the game camera:** a distinct roof shape or top feature per building; red only as small accents
   (lanterns, chillies), never on structure; no writing; nothing Japanese-coded; no religious imagery; grey tile
   with gentle curves only; no stacked roof tiers.
6. **Hand-made:** deliberate small offsets, leans, sags and tint variation from a fixed seed; nothing perfectly
   straight or repeated.
7. **Door where the entrance is, access point inside it; slots where colonists sit or work.**
8. **Night:** windows, lanterns and the door mapped to lit regions of `WindowsAtlas`, so the building glows when
   its illuminator is on.
9. **Construction stage** from the same parts (frame, base) plus bamboo scaffold, lashings and a pile of poles.
10. **Animated parts** as child nodes with a looping `Default` node animation, pivot on the axle, driven by the
    vanilla component the blueprint already has.
11. **`model.json`** beside the script records everything the blueprint needs (see above).

## The building kit (`src/pipeline/kit/`)

| Module | Does |
|---|---|
| `core.py` | Materials, trim regions, `Part`/`Geo` (geometry bag with seeded rng, tag and node contexts), vertex-colour shading (base occlusion, undersides, per-part tint jitter), the `.timbermesh` writer with animated child nodes (turn or swing, optional rotated pivot) and slot nodes |
| `parts.py` | `tube`, `pole` (bamboo or round timber: taper, bend, strip-mapped segments, disc caps), `beam` (squared timber, sag), `lashing`, `box`, `panel`, `boards`, `frame_ring`, `window` (lattice / panes / round, glowing), `door` (dark glowing doorway, posts, lintel, step, plank leaf ajar), `wall` (timber frame + lime plaster with openings), `gable_end` (chuan-dou frame on plaster or weave), `roof` (gable, hip, pyramid, lean-to: pan-and-cover tile columns with real cover-tile ribs aligned to the texture, courses, sagging Sichuan curve, gently lifted corners, underside, fascia, verge boards, hip rolls, `ridge_course` with softly raised ends), `lathe` (jars, barrels, pots, finials), `jar`, `barrel`, `basket`, `lantern` (glowing, red caps), `lantern_string`, `chilli_string`, `cloth` (sagging awnings and banners, both faces), `stones` (river stones as painted plaster), `plinth` (rammed earth with a stone edge), `stairs`, `ladder`, `wheel` (bamboo rims, spokes, cross-bars, woven paddles, tube buckets), `channel` (split giant-bamboo half-pipe with rims, cut ends and an upstream rope sleeve), `cradle` |
| `waterworks.py` | Flume pieces: `straight` channel on a water cell's floor, `stakes`, `x_trestle`, `leg_frame` (corner legs so the middle stays walkable) |
| `building.py` | `Model`: grid helpers, entrance, slots, animation, colliders, attachments, blocks; automatic construction stage (frame/base parts + bamboo scaffold scaled to the footprint + a pole pile); report (triangles per material and per tag, budget against vanilla, footprint and overhang, UV range); writes `<Id>.Model` and `<Id>.ConstructionStage0.Model` to `E:\PandabornDev\build\models\<Id>\` and `model.json` beside the script |
| `tmio.py` | Reads any `.timbermesh` (vanilla or ours) with node transforms and animation poses |
| `preview.py`, `blender_preview.py` | Renders a model in the faction's actual textures (albedo x tint x vertex colour x AO, swizzled normal maps, smoothness, window glow at night) from the game's angle, by day and night, beside a vanilla model, on a tile grid; contact sheets |
| `preview_all.py` | Builds every `art/models/<Id>/build.py`, previews each beside its vanilla stand-in (day, night, construction stage) and writes contact sheets |

A building is a short script, `art/models/<Id>/build.py`, that composes parts and calls `m.build()`.

```
E:\PandabornDev\tools\venv\Scripts\python.exe art\models\Den\build.py
E:\PandabornDev\tools\venv\Scripts\python.exe -I src\pipeline\kit\preview_all.py [Id ...]     # sheets in E:\PandabornDev\build\models\preview
E:\PandabornDev\tools\venv\Scripts\python.exe -I proto\models\tools\gen_mod.py                 # prototype mod -> E:\PandabornDev\build\proto\models
powershell -File tools\run_game_test.ps1 -NoBuild -Faction Inkpaws -ExtraMods "E:\PandabornDev\build\proto\look-swap,E:\PandabornDev\build\proto\models" -RequestJson proto\models\tests\all.request.json -WaitForGameSeconds 10800
```

## Results

See the end of this file (filled in from the in-game runs).
