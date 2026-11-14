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
more, with `ConstructionSiteProgressVisualizerSpec.ProgressThresholds`). **Exactly one ConstructionBase child is
required:** the game counts the children minus one base against the thresholds, and a blueprint without a base throws
on every game load (seen in game: the whole new game failed to start). Sizes with no vanilla base (1x3) use
`ConstructionBase1x1`. The stage model is the building's timber
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

**Two district centres joined by a path crash the game** (`District ... conflicts with district`, seen in game when
the test harness laid a path from the starting centre to a placed Village Hall): test a district centre model away
from the road network.

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
| `parts.py` | `tube`, `pole` (bamboo or round timber: taper, bend, strip-mapped segments, disc caps), `beam` (squared timber, sag), `lashing`, `box`, `panel`, `boards`, `frame_ring`, `window` (lattice / panes / round, glowing), `door` (dark glowing doorway, posts, lintel, step, plank leaf ajar), `wall` (timber frame + lime plaster with openings), `gable_end` (chuan-dou frame on plaster or weave), `roof` (gable, hip, pyramid, lean-to: pan-and-cover tile columns with real cover-tile ribs aligned to the texture, courses, sagging Sichuan curve, gently lifted corners, underside, fascia, verge boards, hip rolls, `ridge_course` with softly raised ends), `lathe` (jars, barrels, pots, finials), `jar`, `barrel`, `basket`, `lantern` (glowing, red caps), `lantern_string`, `chilli_string`, `cloth` (sagging awnings and banners, both faces), `stones` (river stones as painted plaster), `plinth` (rammed earth with a stone edge), `stairs`, `ladder`, `wheel` (bamboo rims, spokes, cross-bars, woven paddles, tube buckets), `channel` (split giant-bamboo half-pipe with rims, cut ends and an upstream rope sleeve), `cradle`, `gear` (cog wheel), `standing_lantern`, `screen` (woven panel in a bamboo frame), `round_roof` (many-sided tiled cone), `chilli_string` |
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
E:\PandabornDev\tools\venv\Scripts\python.exe -I src\pipeline\kit\game_zoom.py [Id ...]       # fixed-scale game-camera sheet (sheet_gamezoom.png)
powershell -File tools\run_game_test.ps1 -NoBuild -Faction Inkpaws -ExtraMods "E:\PandabornDev\build\proto\models" -RequestJson proto\models\tests\pass3.request.json -WaitForGameSeconds 10800
```

## Results

All runs: `tools/run_game_test.ps1 -NoBuild -Faction Inkpaws -ExtraMods E:\PandabornDev\build\proto\models` (the
installed faction ships the Look code and the `pandabornlook` bundle itself: never add `proto/look-swap` or
`PandabornCodeDev`, which apply the swap twice or crash on the duplicate bundle; passes 1 and 2 used them before the
faction shipped the look), screenshots in `E:\PandabornDev\build\test\<run>\`. Previews (Blender, faction textures,
beside the vanilla stand-in, day / night / construction stage) in
`E:\PandabornDev\build\models\preview\<Id>_{day,night,stage}.png`
and contact sheets `sheet_day.png`, `sheet_night.png`, `sheet_stage.png`.

| Run | What | Result |
|---|---|---|
| `models-den-1` | first load | **crash on every game load**: the Scoop Wheel blueprint had no `ConstructionBase` child (fixed; rule above) |
| `models-all-2` | 21 buildings | **crash**: Village Hall placed as a second district centre and joined by a path to the first (rule above) |
| `models-all-3` | 18 models + 4 unfinished + 3 vanilla, Diorama, 13.5 h to night | **pass**, 25/25 placed, 0 errors; day and night close-ups of every model |
| `models-water-1` | flume line, drop, spout, Scoop Wheel and Bamboo Water Wheel in rivers, Moon Loft with paths under it, Village Hall (WaterLab, Plains) | all 19 placements valid; **Path tiles placed in the cells under the Moon Loft: walk-under works by the block rules**; Scoop Wheel turning (generator rotation 0.26, animator enabled); flume water only a thin film (pond too low); the scoop's lift moved no water (`canMove` false: the outlet, a mechanics question for the water lane) |
| `models-stages-1`, `models-water-2` | | nothing placed: the faction had switched to `Buildings.Inkpaws` (fixed: both collections) |
| `models-stages-2` | unfinished buildings filmed during construction, Kite Windmill filmed 2 s apart | pass; Kite Windmill rotor visibly turned between frames; every unfinished building was built by the builders within 45 s (cost removed for tests) |
| `models-water-3` | | **crash**: the Steamer's stand-in Grill recipes name Folktails goods the Inkpaws no longer have (fixed: recipes stripped in the prototype) |
| `models-water-4` | the water scene again in daylight, pond lower | flume line, bridge over a dip, drop, spout, both wheels and the Moon Loft placed; **the Bamboo Water Wheel turns in the current** (frames 3 ticks apart differ: `wheel_a.png` / `wheel_b.png`, generator multiplier 0.25); flume water still only a 1 cm film (the pond barely tops the gate's bed) and water drips out under the bridge pieces (zero-code route: the direction limiter sits at the block origin, not the raised cell; the water lane's `PandabornFlumeSegmentSpec` with `FlowCells` is the fix). The only error is the water lab's own lift expectation for the Scoop Wheel |
| `models-stages-3` | six unfinished buildings filmed every 4-7 s at speed 1 | pass; **construction proven**: the dirt base until builders start, then our stage model (timber skeleton on the plinth inside a lashed bamboo scaffold), then the finished model (`stage_Den_{start,4,8,12,17,23}.png`, `stage_MoonLoft_8.png`) |

Lessons that bind the catalogue lane (who turns `model.json` into blueprints):

* `#Unfinished` children: exactly one `ConstructionBase...` **first**, then `ConstructionStage0...` in order. The progress
  visualiser shows child 0 until construction starts and the stages after; reversed children show the stage before
  work starts and the bare pad during construction.
* Never let a recipe, need or good id in a stand-in blueprint point at something the faction does not have: the
  building throws when it is created (here, in the placement preview).
* Workshop smoke (`TemplateAttachmentsSpec` particles) makes the harness's framed close-up see the whole map; use the
  overview or a fixed camera for those buildings.

### Verdicts (harsh, against the re-themed vanilla buildings in the same frames)

| Model | Tris (vanilla stand-in) | In game | Verdict |
|---|---|---|---|
| Den | 1654 (Lodge 662) | built, finished, beside vanilla lodges | **Good**: the tile roof with real cover-tile ribs, ridge roll and chimney holds up at close range; reads as a house, not a dome. Front hides under the porch eave from the high camera |
| Village Hall | 3008 (District Center 1788) | placed (water lab), district fire burns on the mast | **Good/fair**: distinct hip-and-gable hall, banners, fire mast; smaller-looking than the vanilla centre |
| Moon Loft | 1910 (Lodge) | built on stilts, paths placed under it | **Good**: the clearest silhouette of the set |
| Teahouse | 2616 (Campfire 1028) | built | **Good/fair**: the hip roof and indigo awning read; the roof hides the tables from above |
| Steamer | 1250 (Grill 1191) | built | **Fair**: the steamer stack reads once out from under the roof; framed close-ups fail (smoke particles) |
| Kite Windmill | 1280 (Wind Turbine 1650) | built, **rotor turns** | **Good**: unique vertical sail windmill |
| Kindergarten | 1742 (Campfire) | built | **Good/fair**: playhouse, slide, swing, fence read; busy |
| Pickle Yard | 2164 (Bakery 1703) | built | **Good/fair**: rows of glazed jars are an instant read |
| Flume / Gate / Bridge / Drop | 192 / 254 / 372 / 502 (Throttling Valve 256) | all placed in a working line | **Fair**: clean and joined, but a plain half-pipe; water inside not yet seen deep enough to judge |
| Flume Corner | ~800 | placed | **Weak/fair**: the solid cells still read as boxes |
| Paddy Spout | 382 (Fill Valve 176) | placed at the line's end | **Fair** |
| Scoop Wheel | ~1500 (Water Wheel 1212) | placed in a river, generator turning | **Fair**: spindly bamboo next to vanilla's chunky wheel (frame made chunkier after the run) |
| Bamboo Water Wheel | 1288 (Water Wheel 1212) | placed in a river | **Fair**: reads as a cage from above |
| Cistern | 502 (Small Tank 390) | built | **Fair**: a plain glazed jar |
| Dew Collector | 677 | built | **Good**: the mesh funnel is unmistakable |
| Hammock | 303 (Hammock 248) | built | **Fair**: small; the swing animation not yet seen with a sleeper |

## Requests from the catalogue lane

The catalogue adopts a model with one line, `PandabornDen = { model = "Den" }` in `catalogue/buildings.toml`; the
generator (`src/gen/pbgen/models.py`) takes footprint, blocks, entrance, access, colliders, both meshes, the
construction base (first) and stage, attachment positions, `connectionAnchor`, `windRotationAnimator`, `removeSpecs`
and `addSpecs` from `model.json`, and the basis defaults to `standIn`. `tools/validate.py` checks the result against
`model.json` and the mesh (slot keywords against `#Slot#` nodes, animated nodes against the mesh and their driver
spec against the blueprint). Adopted on 2026-11-14: Village Hall, Den, Moon Loft, Steamer, Pickle Yard, Teahouse,
Kindergarten, Hammock (as the Nap attraction), Kite Windmill, Bamboo Water Wheel, Cistern (small only). Water pieces
(Flume set, Flume Gate, Paddy Spout, Scoop Wheel, Dew Collector) wait for the water module. Requests, in priority
order:

1. **`drivenBy` as data.** Please add `"driver": "<SpecName>"` (e.g. `"EnterableAnimationControllerSpec"`,
   `"WindRotationAnimatorSpec"`) to each `animatedNodes` entry. The validator now parses the first `...Spec` word out
   of the free text; a field cannot be misread.
2. **Cistern sizes.** The catalogue has three cisterns (small 1x1, medium and large on the vanilla Medium/Large Tank
   footprints). One `model.json` per size (`CisternMedium`, `CisternLarge`, with their own `size`/`blocks`) lets all
   three adopt; today only the small one does.
3. **Dew Collector.** Until the water module ships it stands in as a staffed workshop (data alone needs a worker):
   it needs an `entrance` and a `#Slot#Entrance` (or say it should stay un-adopted until then).
4. **`standIn` that matches the catalogue.** Teahouse and Kindergarten were made for the Campfire; the catalogue now
   uses that basis and retargets the need, so nothing is needed. Pickle Yard's Bakery and Moon Loft's Lodge also
   became the catalogue's basis. If a model is made for a different basis than CONTENT's, say why in `notes`.
5. **Models still missing** (each building stands on a vanilla model until then; the generator's report lists them):
   Courtyard House, Terrace House, Paddy House, Tea Roastery, Trip-Hammer Mill, Kitchen, Hot Pot Hall, Lantern
   Workshop, Smoke Kiln, Ox Workshop, Star Tower, Festival Square, Nap Platform, Slide and Swing, Ink Studio, Hot
   Spring Bath, Opera Stage, the three night posts, Dry-Stone Wall, Treadwheel Lift, Cistern Tap, the decorations
   (lanterns, fence, potted pine, statue, pinwheel, goldfish bowl, moon gate), Memorial Arch, Great Sitting Panda,
   Sky Lantern.

### Answers from the model lane (2026-11-14)

1. **`driver` as data:** every `animatedNodes` entry now has `"driver": "<SpecName>"` (Hammock
   `EnterableAnimationControllerSpec`, Kite Windmill tower and rotor `WindRotationAnimatorSpec`, Scoop Wheel and
   Bamboo Water Wheel `WaterPoweredGeneratorSpec`); `drivenBy` keeps the human sentence.
2. **Cistern sizes:** `art/models/CisternMedium` (2x2x3 on `MediumTank.Folktails`, mouth radius 0.85 over the 2x2
   liquid plane, 0.546 to 2.3) and `art/models/CisternLarge` (3x3x3 on `LargeTank.Folktails`, mouth radius 1.33, plane
   0.566 to 2.45, windlass shelter and stair). Entrances and access points as the vanilla tanks.
3. **Dew Collector:** now has an `entrance` (front cell) and a `#Slot#Entrance` for the staffed stand-in; with the dew
   module (no workers) both go unused.
4. **Why a stage is "never seen":** the stage child shows from the moment the site `WasStarted` (a builder hour logged
   or any material delivered) until it finishes, and a site's work is `ceil(total cost / 20)` builder-hours (1 h minimum,
   `ConstructionSiteBuildTimeCalculator`). Cheap buildings with several builders on hand finish within seconds of real
   time at speed 3, and once materials are stocked the delivery is quick too. In `models-stages-3` (speed 1, shots every
   4-7 s) the Den and Moon Loft stages were caught (`stage_Den_4.png`...`_17.png`); for the Teahouse and Kindergarten
   the camera was 4 s late. It is not the model or the threshold: film at speed 1 within the first seconds, or give the
   test site a bigger cost. Base-first order is required (see above).
5. **Basis:** Teahouse and Kindergarten were made for the Campfire's five seats; Pickle Yard for the Bakery (2x3,
   smoke); Moon Loft for the Lodge (a dwelling); the cisterns for the tanks; Courtyard and Terrace House (below) for
   the Double and Triple Lodge footprints but with a **ground-floor entrance** and no stacking on the tiled roof (the
   vanilla Double/Triple Lodge enter at z = 1 and take lodges on top).
6. **New since the requests:** `CourtyardHouse` (Double Lodge, six beds, L of two tiled wings round a gated
   courtyard), `TerraceHouse` (Triple Lodge, nine beds, flat roof at y = 2 and top blocks Stackable `BlockObject` so it
   stacks; drying mats on the roof), `CisternMedium`, `CisternLarge`, `StandingLantern`, `HangingLantern`,
   `StringLanterns` (all three on the vanilla Lantern, whose `NightTimeLightControllerSpec` lights them at dusk; the
   paper is the window glow region tinted red by vertex colour), `StarTower` (Observatory; `observatoryAnimator`
   names `#StarDome` and `#StarTelescope` for its `ObservatoryAnimatorSpec`). Previews only; not yet in a game run.
7. **Still missing** (in the coordinator's priority order): Paddy House, Festival Square, the three night posts,
   Opera Stage, Hot Spring Bath, Ink Studio, Nap Platform, Slide and Swing, Large Kite Windmill, Tea Roastery,
   Trip-Hammer Mill, Kitchen, Hot Pot Hall, Lantern Workshop, Smoke Kiln, Ox Workshop, Treadwheel Lift, Cistern Tap,
   Dry-Stone Wall, Bamboo Fence (vanilla fences are modular: needs a look at `WoodFence`'s segment models first), Potted
   Pine, Panda Statue, Pinwheel, Goldfish Bowl, Garden Moon Gate, Memorial Arch, Great Sitting Panda, Sky Lantern.

## Pass 2 (2026-11-14)

Test setup: the re-theme now comes from the `Pandaborn.Look` code module: `-ExtraMods
E:\PandabornDev\build\PandabornCodeDev,E:\PandabornDev\build\proto\models` (never together with `proto/look-swap`).

| Model | Change | Triangles |
|---|---|---|
| Village Hall | hall widened to the full 3x3 and raised (walls 1.62, ridge 2.7); **open bell tower** at the front-left corner, four braced timber legs, one small pyramid roof, a bronze bell (lime sheet painted bronze) on a yoke with its rope down to the veranda (`bell` in model.json marks it for a future sound or swing); signal mast with the district fire kept at the back right | 3842 |
| Flume | split culm **weathered by height** (dark green-brown at the waterline, fresh toward the rims), two proud culm nodes, lighter split-culm rims, a rope-bound **sleeve at the upstream joint**, a pair of leaning stakes lashed to the rims with a tie across | 404 |
| Flume Bridge | two lashed bamboo **X-trestles** at the cell's front and back edges with head beams | 528 |
| Flume Drop | dry-stone step, upper culm narrowing into a lipped **spout** over a flat-stone splash basin, lower run on stakes | 718 |
| Flume Corner | an **open junction**: stone-floored basin, stone kerbs, bamboo lips and posts; the three solid cells a heap of rubble stones with a bamboo clump and a lantern post (no box) | 976 |
| Flume Gate | iron-banded **sluice board** in a timber frame, raised by a rope from a long bamboo **lever** with a stone counterweight | 498 |
| Paddy Spout | inherits the new culm | 594 |
| Cistern small / medium / large | **glazed stoneware vats**: full-bellied body on a stone plinth, dark-brown (small, large) or celadon (medium) glaze by vertex colour with a lighter glaze-pool band at the shoulder, rolled lip, planked wooden lid over the back of the mouth, ladder or stair | 520 / 798 / 1414 |
| Night Builders' Post (new) | Builders' Hut: open lean-to shed of building stores; **moon window** in the back wall and a glowing moon plaque on a pole above the roof | ~1300 |
| Night Courier Post (new) | Hauling Post: plaster wall pierced by a **moon gate**, back-baskets on a rack behind; moon plaque above | ~1400 |
| Night Gatherers' Post (new) | Gatherer Flag: moon plaque and crescent on a bamboo pole, mushroom basket, back-basket | ~520 |

The moon mark (kit `moon_window`: the round cracked-ice window region in a lime disc with a timber ring) is shared
by all Ringtail buildings, glows at night, and sits high enough to read from the game camera.

### What the catalogue lane must change to adopt pass 2 and the new models

* Village Hall: nothing new in the blueprint; colliders changed (four boxes now), `bell` is informational.
* Flume set, Paddy Spout: the water pieces still wait for the water module; when adopted, take `waterCells` and
  `solidCells` from model.json (unchanged from pass 1).
* Cistern, CisternMedium, CisternLarge: re-run the generator (meshes and colliders changed; footprints unchanged).
* New models, each with its stand-in as basis: `CourtyardHouse` (DoubleLodge; **entrance at z = 0**, not the
  vanilla Double Lodge's z = 1), `TerraceHouse` (TripleLodge; entrance z = 0, top blocks Stackable `BlockObject`),
  `StarTower` (Observatory; set `ObservatoryAnimatorSpec` from `observatoryAnimator`), `NapPlatform`
  (RooftopTerrace; eight `#Slot#Seat` nodes), `StandingLantern`, `HangingLantern`, `StringLanterns` (Lantern),
  `NightBuildersPost` (BuildersHut), `NightCourierPost` (HaulingPost), `NightForagersPost` (GathererFlag; keeps the
  `Seat` slot keyword), `DewCollector` (entrance and `#Slot#Entrance` added).

### Pass 2 in game (`models-pass2-1`, Diorama, code-module re-theme, 17 h into the night)

23 of 25 placed, **0 errors from our mods**. Not placed: Nap Platform (needs a stackable top: the Rooftop Terrace
basis has `MatterBelow: Stackable`, so it must go on a roof; expected) and `Lodge.Inkpaws` (no such template; the
request's mistake). Screenshots `E:\PandabornDev\build\test\models-pass2-1\*_{day,night}.png`, sheet
`E:\PandabornDev\build\models\ingame_pass2_day.png`. The starting district centre is already the catalogue-adopted
Village Hall (pass-1 mesh), fire burning on its mast.

Harsh findings: the night overview shows almost no window glow on any home, ours or the re-themed vanilla ones, and
the lanterns glow only faintly; with the look module's latest window map the glow is too weak to read at this zoom
(look lane). The celadon vat reads pale grey-white under the new palette (glaze tint should be darker). The Terrace
House reads from above as a flat tan box (the clear roof needed for stacking is a weakness; it needs a parapet coping
and a stronger roof colour). The flume green still reads bright in daylight next to the brown-grey terrain.
Still unverified: lit windows with occupants at close range, hammock swinging with a sleeper (the swing shots caught
nobody in it), colonists walking under the Moon Loft.

## Requests from the water lane (2026-11-14)

The water module (`src/code/Pandaborn.Water`) and its dev mod (`proto/water`) now place the kit models directly
(meshes from `E:\PandabornDev\build\models\<Id>`, blocks and colliders from `model.json`). Every `waterCells`,
`solidCells`, `waterInput` and `waterOutput` in the kit matches what the module needs; nothing there is wrong. What the
water pieces need beyond the current models, in priority order:

1. **A cap block on the Flume Gate, Flume Corner and Paddy Spout (and a covered Flume, if there is one).** The module
   puts a solid water obstacle one block above each of these (cell `(0,0,1)`), so a line that backs up to its pond level
   cannot run over the top (measured: without it a backed-up line overtopped 1-block pieces and flooded the field).
   Today that cell is not part of the building, so another object could be built into it, and two obstacles in one
   cell corrupt the water column. Please make these pieces **two blocks tall**: the second block occupied
   (`Bottom, Top, Corners, Path, Middle`, `MatterBelow Any`) with a visible hood, lid or post top, so the cap is inside
   the building. Corner posts: two blocks tall as well (the module makes them solid to that height).
2. **Flume Bridge span.** A Bridge piece cannot stand over a ground flume: the leg's `Corners` occupation collides with
   the flume tile below. The dev mod now gives the Flume `Occupations "Bottom, Middle, Path"` (corners free), the span
   variant a leg on `Corners` only and no inert obstacle, and the regular Bridge leg `Corners, Bottom` (so it cannot go
   over a flume). Proven in game (`water-w1b-0934`): the span stands over a running flume, both lines run, and it
   survives save and load (a leg that occupied nothing was deleted on load as "not supported by terrain physics"). A
   model for it: the same deck, with the four trestle posts at the very corners of the cell so they stand beside the
   channel below, not in it. Save it as `FlumeBridgeSpan` with `waterCells` `(0,0,1)`, and keep the Flume's channel
   clear of the cell corners.
3. **Flume Drop: the open cell above the lower half.** The lower flow cell `(0,1,0)` has open air above it; that is
   right. Keep the upper half's leg `(0,0,0)` solid as it is (`solidCells` `(0,0)`): it is what stops the drop leaking
   backwards.
4. **Scoop Wheel**: the outlet at `(0,2,2)` hanging one block above the basin floor is right (vanilla `WaterOutput` needs
   the gap). No change.
5. **Models still missing for the water set:** Treadwheel Lift (the dev mod uses the vanilla Power Wheel: input
   `(0,1,-1)`, output `(2,2,1)`), Cistern Tap (vanilla Discharge, 1x2, second cell over water), Water Trip-Hammer Mill
   (one cell must stand in the current: `WaterPoweredGeneratorSpec.Blocks`; say which).

## Pass 3 (2026-11-14)

**Test setup changed again:** the installed faction now ships `pandabornlook_win` itself, so `-ExtraMods
PandabornCodeDev` on top crashes the load ("another AssetBundle with the same files is already loaded",
`models-pass3-1`). Pass `-ExtraMods E:\PandabornDev\build\proto\models` only.

**Evidence fixes:**
* Harness (additive, `src/devharness`): framed `building` shots take `"front": true` (camera heading from the
  building's own orientation, so it looks at the entrance side; `yaw` adds to it) and `"minDistance"` (tiles; the
  camera never comes closer than this or than 1.2x the model's radius). Together with the look lane's
  MeshRenderer-only bounds this keeps small objects and smoking workshops in frame.
* Prototype blueprints set `FinishableWithBeaversOnSite: true`: a site "finished" by the harness next to the district
  centre otherwise waits for colonists to step off it (`ConstructionSite.FinishIfRequirementsMet`), which is why the
  pass-2 Den, Moon Loft, Teahouse and large Cistern showed their construction stage in "finished" shots.
* `proto/models/tools/gen_pass3_request.py`: every model placed finished, a front view and a three-quarter view each,
  three evening hammock frames, and at night each lit-capable building twice: as occupied (unforced) and with the
  look lane's `"lit": true`.

**Kit fix:** `beam()` and therefore `boards()` made square sections the size of the diagonal; they now make true
w x h sections (floors, door leaves, shutters and planks all became thinner and flatter; every model rebuilt).

**Changes from the coordinator's pass-2 review:** Terrace House roof is now a plank deck inside a low lime parapet
with tile coping and drying trays (stackable still); Night Courier Post has a tiled lean-to over its yard;
Night Builders' Post has a plastered end wall with the moon window facing out, clear of the eave; celadon glaze darker;
flume culms weathered olive.

**New models (preview proven):** Sky Lantern (wonder, 4966 tris: stepped stone terrace, lashed bamboo launch tower,
a 3.7-unit red-gold paper lantern that glows at night, lantern strings; `#SkyLanternAnimated` with a one-shot `rise`
animation for WonderAnimationController, builder slots on the stage), Great Sitting Panda (3576: rock outcrop, a
painted carved panda holding bamboo, a red panda on its knee, a still pool and lanterns), Festival Square (3x3:
paved square, roofed timber gateway, central lantern pole with strings to corner poles, drum stand, festival goods),
Hot Spring Bath (Mud Pit: stone pool whose `#SpringWater` surface node is the vanilla surface controller's, steam from
the bubbles), Ink Studio (Contemplation Spot), Opera Stage (Dance Hall: roofed stage, backdrop, benches, moon plaque),
Slide and Swing (Lido: deck, slide tower, swing over the pool, Lido slots and `#MiscStart/#MiscEnd` patrol markers),
Paddy House (Aquatic Farmhouse), Bamboo Fence (six modular variants), Panda Statue, Potted Pine, Goldfish Bowl,
Garden Moon Gate, Bamboo Pinwheel (Weathervane; wind-turned rotor), Hot Pot Hall and Lantern Workshop (Bakery).

### Catalogue adoption list for pass 3
* Re-run every adopted model (beam fix changes all meshes; footprints unchanged).
* Sky Lantern: basis EarthRecultivator; **one** construction stage carrying the `Working/Building/Cutting/Digging`
  slots, so `ProgressThresholds` = `[0.0]`; keep the `Lanterns` attachment at `attachments`.
* Great Sitting Panda: basis HallOfAbundance, one stage, thresholds `[0.0]`, no entrance.
* Festival Square: the Small Warehouse stand-in is 1x1; take size 3x3, blocks, entrance and access from model.json.
* Hot Spring Bath: set `GoodConsumingAttractionSurfaceControllerSpec.SurfaceName` to `surfaceName` (`#SpringWater`).
* Slide and Swing: Lido blocks and BaseZ 1 from model.json; slot nodes keep the vanilla names.
* Bamboo Fence: replace the six `#Finished` children with `mergeableObjectModel.children` and set
  `ModelNamePrefix` = `BambooFence`; the stage is `BambooFence.ConstructionStage0.Model`.
* Bamboo Pinwheel: `WindRotationAnimatorSpec` from `windRotationAnimator`.
* Lantern Workshop: `removeSpecs` drops the Bakery's smoke.
* Opera Stage: its 20 slots all use the Dance Hall's `Spot` keyword (Dancing).
* Memorial Arch: basis BrazierOfBonding, one stage, thresholds `[0.0]`; keep the `Fire` attachment at `attachments`
  (it burns in the lantern cage under the roof).
* Smoke Kiln: basis WoodWorkshop (2x4x4); `Smoke` attachment at the chimney if the blueprint gives it one.
* Tea Roastery: basis Bakery (2x3x4); the Bakery smoke comes out of the stove flue (`Smoke` attachment).
* Hot Pot Hall: basis Bakery; smoke from the pot's flue.
* Paddy House: the generator must **not** carry a second `PlanterBuildingSpec` for `AquaticFarmhouse` into a game
  that also has the vanilla or re-themed Aquatic Farmhouse (fields tool `.Single` crash, `models-pass3-2`); the
  prototype strips every Planter spec.

### Pass 3 verdicts (from previews; the in-game proof run did not happen)

| Verdict | Models |
|---|---|
| Good | Sky Lantern (the great lantern on its tower reads at once and glows), Great Sitting Panda (charming, readable), Opera Stage |
| Good / fair | Festival Square (reads as a square only with its gateway; empty in the middle by design), Terrace House pass 3 (deck and parapet fixed the flat box) |
| Fair | Paddy House, Hot Spring Bath, Ink Studio, Slide and Swing, Bamboo Fence, the five decorations, Lantern Workshop, Smoke Kiln (the vault reads; the firing shed is plain), Memorial Arch (no longer torii-like, but a little boxy) |
| Weak / fair | Tea Roastery (the drying trays read as drums from the game camera), Hot Pot Hall (the roof hides the pot and most chillies) |

**Not proven in game, still:** lit windows with occupants at close range, the hammock swinging with a sleeper,
colonists walking under the Moon Loft. The proof request is ready (`proto/models/tests/pass3.request.json`; run with
`tools/run_game_test.ps1 -NoBuild -Faction Inkpaws -ExtraMods E:\PandabornDev\build\proto\models -RequestJson
proto/models/tests/pass3.request.json -WaitForGameSeconds 10800 -TimeoutSeconds 1500`) but the run (`models-pass3-3`) was cancelled unstarted: the
shared game queue was twelve runs deep. Pass-3 game runs that did happen: `models-pass3-1` (bundle loaded twice,
setup error) and `models-pass3-2` (Paddy House planter crash, fixed).

**Not built yet:** Trip-Hammer Mill, Kitchen, Ox Workshop, Treadwheel Lift, Cistern Tap, Dry-Stone Wall, Large Kite
Windmill, Flume Bridge Span, and the water lane's two-block caps on the Flume Gate, Flume Corner and Paddy Spout.

## Pass 4 (2026-11-14)

### Readability from the game camera

`src/pipeline/kit/game_zoom.py` renders every model at one fixed scale (orthographic, 110 px per tile, pitch 55,
day) grouped so look-alikes sit side by side: `E:\PandabornDev\build\models\preview\sheet_gamezoom.png` (per model
in `preview\gamezoom\`). Before this pass five workplaces were the same charcoal gable on posts. Each workplace now
has one mark that reads from above:

| Workplace | Its mark at game zoom |
|---|---|
| Steamer | a tower of five big bamboo steamer baskets and a cone lid, through and above the lean-to |
| Pickle Yard | six fat brown jars with red cloth tied over their mouths |
| Tea Roastery | two stepped tiers of wide, shallow pale trays of green and roasted leaf, tilted to the street, outside the roofline |
| Lantern Workshop | a bamboo mast with four strings of big red lanterns running down to the eaves and yard |
| Hot Pot Hall | open front; the red pot under its own tiered "lantern roof" with a vent, chillies on every eave |
| Kitchen (new) | end-on gable, tall white chimney, a round grey hand mill and trays of white rice balls |
| Trip-Hammer Mill (new) | paddle wheel in a stone race, two long hammer beams over stone mortars |
| Ox Workshop (new) | a great round turntable with a red-lacquered rim in a timber yard |
| Paddy House | the only rice-straw thatch roof (gold where all the others are charcoal) |
| Smoke Kiln | the earthen vault (unchanged) |
| Night Builders' Post | tall bamboo shear legs with a hoisted bundle of poles; moon plaque |
| Night Courier Post | white wall with the moon gate (unchanged) |
| Large Kite Windmill (new) | all-indigo sails, taller, a gear house; the small one keeps alternating hemp and indigo |

Still close at game zoom: Flume Gate and Paddy Spout (both one cell with a little hood; they stand in different
places, gate on a line, spout at a field edge).

### Weak models fixed

* Tea Roastery: the drum-like trays replaced by wide shallow trays (kit `tray`) on a rack outside the roofline.
* Hot Pot Hall: rebuilt open on the entrance side; the big red-lacquered pot (red and pale broth) under a raised
  lantern roof whose vent carries the Bakery smoke as steam; chilli strings on the pavilion and hall eaves.
* Memorial Arch: posts slimmed (0.16 to 0.11), plaster panels removed, a light two-tier roof (thin hipped eave and a
  small raised gable), a blank lacquered name board in a red frame (no writing) under the front beam; `Fire` kept.

### New models

| Model | Basis | Notes | Tris |
|---|---|---|---|
| TripHammerMill | Gristmill (3x2x3) | `#MillWheel` turns, `#Hammer1/2` trip (new kit kind `trip`: slow lift, quick fall, half a lift apart); all played by the Gristmill's WorkshopAnimationController. The wheel turns in a stone race over cells (0,0) and (0,1): `wheelCells` in model.json for the water module's WaterPoweredGeneratorSpec | 2013 |
| Kitchen | Bakery (2x3x4) | smoke at the chimney | 2482 |
| OxWorkshop | BotAssembler (3x3x1) | `#OxTurntable` (RingName, turns about up) and `#OxAuger` (DrillName, turns about forward): set `BotManufactoryAnimationControllerSpec` from `botManufactoryAnimation`; front centre clear for the driveway | 2204 |
| TreadwheelLift | WaterPump (2x3x3, BaseZ 1) | the square-pallet chain pump: trough from the intake column (0,2) at y = -1 up to a sprocket; `#TreadAxle` turns while working. Drop the WaterPump's `WaterInputPipeSpec` when adopting (the trough is the intake) | 2306 |
| CisternTap | Discharge (1x2x1) | celadon vat, plug tap, plank catwalk over the second cell, spout; `Water` drops at the spout tip | 682 |
| DryStoneWall | Levee (1x1x1) | stacked stone courses over an earth core, mossy cap; stackable on itself (`BlockObject`) as the Levee | 554 |
| LargeKiteWindmill | LargeWindTurbine (3x3x5) | ten indigo sails; `windRotationAnimator` names `#KiteRotor`/`#KiteTower` | 2206 |
| FlumeBridgeSpan | ThrottlingValve (1x1x2) | the water lane's span: lower block `Occupations None`, water cell (0,0,1), stringers resting on the neighbours, nothing in the cell below | 508 |

**Water caps** (the water lane's request 1): Flume Gate (1x1x2), Flume Corner (2x2x2) and Paddy Spout (1x2x2) are
two blocks tall; the cap block over the water cell is occupied (`Bottom, Top, Corners, Path, Middle`, MatterBelow Any)
and holds a little tiled hood (gate, spout) or pavilion roof (corner); `capCells` in model.json. The Flume Corner's
solid L is two blocks tall too (bamboo clump and lantern post). The Paddy Spout's cap layer leaves (0,1,1) free.

**Nap Platform:** stands on the ground or a roof (blocks MatterBelow `GroundOrStackable`), deck on short legs over
stone pads (0.26 high), five mats with cushions and five `#Slot#Seat` nodes; capacity 5.

**Night windows** (look lane: glow needs the building lit and big glass): the Den's front lattice window enlarged
(0.42 x 0.40 to 0.44 x 0.54), the Courtyard House's front window enlarged. Lantern paper now uses an even strip of
the glass panel (`LANTERN_GLOW`, no dark gap: the old region put a black streak across every lantern and the Sky
Lantern's great lantern).

### Wonder-completion picture

`src/pipeline/kit/wonder_image.py` renders the faction's picture in Blender from our own models: night, the Sky
Lantern's great lantern risen above the village (Village Hall, Star Tower, homes with lit windows, string and standing
lanterns), sixteen small sky lanterns drifting up, far hills, a deep blue sky, no characters. Same format as the
vanilla `wonder-completion-folktails` (1514 x 348, RGB, no mipmaps; read from the game's resources.assets header,
not copied): `mod/PandabornFactions/Sprites/Pandaborn/WonderCompletion/wonder-completion-inkpaws.png` + `.meta.json`
(`isSprite`).

### Harness (additive, `src/devharness`)

* Buildings may be placed `"relativeTo": "districtEntrance"` (the offset counts from the cell in front of the
  district centre's door, where every connecting path starts) or `"previous"` (from the last placed building: rows of
  fences).
* `"animations": [{"target", "at", "name", "speed", "looped", "backwards"}]` plays a placed building's animation as
  WonderAnimationController does on activation, without activating the wonder (no wonder events, no achievements).

### Named nodes the stand-in looks up (crash found in pass 4)

Several stand-in specs find model nodes by name at run time and throw when one is missing: the Bot Assembler's
`ManufactoryProgressVisualizerSpec` (`#BotAssembler.Folktails.Progress0`, `...Progress1Of3`, `...2Of3`, `...3Of3`),
`BotManufactoryAnimationControllerSpec` (ring, drill), the Earth Recultivator's `BuildingModelGroundCutoffSpec`
(`#Screw_Animated`, `FindChild(...).GetComponent<MeshRenderer>()`), wind rotators, observatory parts. The adopted Ox
Workshop lacked the progress nodes and **every new Inkpaws game crashed** ("Child #BotAssembler.Folktails.Progress0
not found", `models-pass3-3`, 11:29). Fixed: the Ox Workshop carries the four progress nodes (empty cradle, frame,
half planked, closed body) and the vanilla ring/drill names; the Sky Lantern removes the ground-cutoff spec
(`removeSpecs`). Rule: run `python src/pipeline/kit/check_nodes.py` before handing models over; it lists every
`#Name` a stand-in's specs reference that the model lacks (only the optional `#Underground` of the Campfire basis
remains, looked up with `FindChildIfNameNotEmpty`).

### Catalogue adoption list for pass 4

* Regenerate every adopted model: meshes changed (lantern paper region) and these model.json files changed:
  Steamer (Smoke attachment now at the cone's vent, y 1.96), Pickle Yard, Tea Roastery, Lantern Workshop, Hot Pot
  Hall (Smoke at the vent (1.0, 2.5, 0.92), access z 0.2, colliders), Memorial Arch (colliders), Paddy House (thatch),
  Night Builders' Post, Teahouse (a brazier with a big kettle and a tea stand with teapot and cups out front, in
  view of the game camera), Den, Courtyard House, Nap Platform (blocks GroundOrStackable, access y 0.26, five seats:
  `EnterableSpec.CapacityFinished` 5), Flume Gate, Flume Corner, Paddy Spout (two blocks; `capCells`).
  The faction's own validator flags Steamer and Nap Platform until regenerated.
* New: TripHammerMill (Gristmill), Kitchen (Bakery), OxWorkshop (BotAssembler; RingName/DrillName), TreadwheelLift
  (WaterPump; drop WaterInputPipeSpec), CisternTap (Discharge), DryStoneWall (Levee), LargeKiteWindmill
  (LargeWindTurbine; WindRotationAnimatorSpec), FlumeBridgeSpan (water module).
* OxWorkshop and SkyLantern again after `aad784b` (progress nodes; ground-cutoff spec removed): the build installed
  at 11:28 crashes every Inkpaws game until regenerated.
* Faction: `FactionSpec.WonderCompletionImage` = `Sprites/Pandaborn/WonderCompletion/wonder-completion-inkpaws`.
