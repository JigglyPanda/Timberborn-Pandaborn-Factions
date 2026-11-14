# Icons

How the game draws its UI icons, the rules we copy, how our icons are made, and what is still weak.
Pipeline code: [src/pipeline/icons/](../../src/pipeline/icons/README.md). Measured 2026-11-14 on game 1.1.2.8;
pass 3 (icons matched to the models, the two families, banners, the Wooden Ox avatar) 2026-11-14.

## Finding: vanilla icons are drawings, not renders

Every goods, building and plant icon in Timberborn 1.1 is a **flat line drawing in one gold ink with a black drop
shadow** on a transparent background. None is a render of a 3D model (checked by extracting all 60 goods, 213
building and 22 plant icons and looking at each). So our icons are line drawings too, generated in code by a small
2D vector engine (`ink.py`), not lit Blender renders: a shaded 3D render would be the one icon in the storage panel
that looks different. Blender stays useful as a reference (see "Buildings" below) but does not draw icons.

## How icons are referenced and loaded

| Icon | Field | Vanilla path pattern | Size | Texture settings |
|---|---|---|---|---|
| Good | `GoodSpec.Icon` | `Sprites/Goods/<Id>Icon` | 80 x 80 | RGBA32, sRGB, mipmaps (7), trilinear, repeat |
| Recipe | `RecipeSpec.Icon` | usually the product's good icon | | |
| Building | `LabeledEntitySpec.Icon` | `Buildings/<Group>/<Name>/<Name>Icon` (next to the blueprint) | 112 x 112 | no mipmaps, clamp |
| Plant (planting tool, plant panel) | `LabeledEntitySpec.Icon` on the plant | `NaturalResources/<Crops,Trees,Bushes>/<Name>/<Name>Icon` | 112 x 112 | no mipmaps, clamp |
| Tool group, building group | `ToolGroupSpec.Icon` | `Sprites/BottomBar/...` | ~80-128 | coloured painted icons, a different style |
| Faction logo | `FactionSpec.Logo` | `Sprites/Avatars/<Faction>Logo` | 98 x 98 | flat colour emblem |
| New-game art, avatars | `FactionSpec.NewGameFullAvatar`, `Avatar`... | `Sprites/Avatars/...` | 420 x 560, 512 x 512 | painted character art |
| Needs | none | `NeedSpec` has no icon. Only `CriticalNeedSpec.SpriteName` (Hunger, Thirst, Injury...) picks a status badge from `Sprites/StatusIcons` | 512 | |

Mod sprites: any `.png` in the mod loads as a `Sprite` covering the whole texture, pivot centre
(`ModSpriteConverter`). `<file>.png.meta.json` sets texture options (`ModTextureSettingLoader`): `isSprite`
(= no mipmaps + clamp), `generateMipmap`, `mipmapCount`, `ignoreMipmapLimits`, `filterMode`, `wrapMode`,
`textureFormat` (a `UnityEngine.TextureFormat` name; BerryJam's `"RGB32"` is not one and is silently ignored),
`linear`, `anisoLevel`, `width`/`height`. Our goods meta copies the vanilla goods settings:
`{"generateMipmap": true, "mipmapCount": -1, "ignoreMipmapLimits": true, "textureFormat": "RGBA32"}`.
Building, plant and logo icons use `{"isSprite": true}` like BerryJam's `JamStoveIcon`.

Vanilla sprites are packed tight in the game files, but their sprite **rect is the full 80 x 80 (or 112 x 112)
texture**; `extract_vanilla_icons.py` puts them back on the full rect so framing can be measured. Our PNGs are full
size too, so the UI scales both the same way.

## Style rules (measured with `measure_style.py`)

**Goods (80 x 80)**
* Ink: one flat colour, RGB (202, 172, 107). No gradients, no second colour, no fill colour.
* Line: round pen, about **3.7-4.0 px** wide at 80 px (median 4.0 by area/perimeter), round caps and joins.
  Slightly hand-drawn: tiny wobble and width variation, never ruler-straight.
* Shadow: the ink grown by 0.5 px, moved **2.5 px straight down**, opaque black, under the ink. No blur, no
  sideways offset (so light comes from straight above).
* Framing: the ink's longer side is **51-74 px, median 65**, centred (ink centroid median +0.7 px below centre);
  about 8 px clear on each side. Coverage median 15 % of the canvas.
* View: a 3/4 front view for objects (bowls, jars, blocks show their top ellipse/face), side view for plants.
  No perspective distortion beyond simple ellipses.
* Detail: one object or a small group of 2-3, a few interior lines (veins, grain, a band), small solid dots for
  texture. Overlaps hide what is behind (no see-through lines).
* Shorthand the set uses consistently: flour = tied sack + the plant; fermented = 3 rising bubbles; grilled or hot
  = 3 short steam squiggles; treated = 4-point sparkles; rations = a pot showing the food inside.
* No outline around the whole icon, no background, no text.

**Plants (112 x 112)**: same ink family but paler (187, 161, 108), thinner pen (~2.6-2.8 px), slightly tapered and
wobblier; ink extent ~93 px, sitting low (centroid ~9 px below centre). Crops stand on 2-3 rows of short horizontal
ground strokes, water plants on wavy lines; trees are one characteristic leaf or twig. Faint soft shadow.

**Buildings (112 x 112)**: the same pen-sketch look as plants, more loosely drawn (brush-like, tapered strokes), ink
extent median ~79 px, often a ground line or base. Subjects are a recognisable silhouette of the building's
function (a tent, a clock, a bell), not a picture of its model.

**Faction logo (98 x 98)**: a rounded diamond frame (~6 px line) around a solid emblem, one flat faction colour
(Folktails (254, 245, 136), Iron Teeth (228, 73, 133)), ink inside 16..82, faint shadow.

## Adding an icon

1. Pick the file: goods in `src/pipeline/icons/goods.py`, buildings in `buildings.py` (decorator `@b(id, size)`),
   plants in `plants.py`, logo in `logo.py`.
2. Write a function, decorated with its id (the good id; the file becomes `<Id>Icon.png`):
   ```python
   @icon("PandabornTofu", note="Tofu: a soft white block and a small cube, two soybeans")
   def tofu(c):
       cube(c, 40, 6, 40)          # shared motifs live at the top of goods.py
       cube(c, 78, 52, 22)
   ```
   Draw in a ~100 x 100 box, y down, back to front. Calls: `c.shape(path)` (closed outline that hides what is
   behind), `c.stroke(path, w)` (line, `w` = pen multiplier), `c.fill(path)`, `c.erase(path[, w])`,
   `c.dot(x, y)`, `with c.at(x, y, s, rot):` for a moved/scaled/rotated block. Paths: `line`, `spline` (smooth
   curve through points), `ellipse`/`circle`/`arc`, `rrect`, `bez`; `hatch(region, spacing, angle)` for nets and
   weaves. Pen widths are pixels and stay constant; geometry is scaled to fit, so only proportions matter.
3. Run `E:\PandabornDev\tools\venv\Scripts\python.exe -I src/pipeline/icons/build_icons.py <Id>` and open
   `E:\PandabornDev\build\icons\preview\<Id>Icon.png` (4x) and `goods_sheet.png` (beside vanilla, three sizes).
4. Judge at 40 px and 28 px, not only enlarged. Keep parallel lines 9+ units apart (the pen is ~6 units wide).
5. Rules from the design review: no writing or characters on anything; nothing Japanese-coded (no shoji grids;
   drying persimmons sit on round bamboo trays, not on strings); no religious imagery; roofs are the mod's low tiled
   gables (`roof34`, `roof_side`, `roof_hip`, `roof` in buildings.py), never stacked in tiers or upturned like palace
   eaves. Ringtail buildings take `@b(..., moon=True)` and keep the top-right corner empty.
6. An icon that is not (or no longer) in the catalogue gets `ship=False`: it still renders to
   `rendered/<Group>/unshipped/` but is not written to the mod and not shown on the review sheets. Remove its old
   PNG and meta from the mod by hand (`git rm`).

## File names

`mod/PandabornFactions/Sprites/Pandaborn/<Group>/Pandaborn<Name>Icon.png` (+ `.png.meta.json`), where `<Name>` is
the catalogue name in CamelCase (docs/CONTENT.md draft 2): goods under `Goods/`, buildings under `Buildings/`,
plants under `Plants/`. Blueprints reference them without the extension, e.g.
`Sprites/Pandaborn/Buildings/PandabornSteamerIcon`. The logo keeps its existing path
`Sprites/Pandaborn/Avatars/InkpawsLogo.png`.

## The goods set (pass 2, 2026-11-14)

19 icons, the draft 2 goods list. Pass 2 renamed Bamboo poles to `PandabornPoles` and rice balls to
`PandabornSweetRiceBalls`, added `PandabornSteamedShoots`, redrew Sichuan pepper, cured poles and persimmons, and
thinned the line work (pen 3.7 to 3.5 px, fewer interior details). Removed from the mod (drawings kept, unshipped):
tofu, lacquer, lacquered poles, persimmon cakes, lotus root, ox parts, bamboo charcoal.

| Id | Shows | Verdict |
|---|---|---|
| PandabornBambooShoots | two plump curved shoots wrapped in pointed sheaths, root band | good |
| PandabornPoles | three hollow poles, bulging nodes, a leafy twig | good |
| PandabornCuredPoles | three jointed poles with dark ends, a cord lashing, the vanilla 'treated' sparkles | good |
| PandabornCabbage | napa cabbage: tall head, frilly top, white ribs | good |
| PandabornRice | drooping ear of packed grains on its stalk, a leaf | good |
| PandabornRiceFlour | tied sack + rice ear (vanilla flour convention) | good |
| PandabornSteamedShoots | round bamboo steamer with a cross-woven lid, steam, a halved shoot in front | fair |
| PandabornSteamedRice | bowl heaped with rice, steam | good |
| PandabornPickles | pao cai jar: round belly, water-seal collar, bowl lid, fermentation bubbles | good |
| PandabornSweetRiceBalls | three balls in a bowl, porcelain spoon | good |
| PandabornSichuanPepper | three husks split open at the top on their black seeds, a loose seed, a pinnate leaf sprig | fair |
| PandabornHotPot | yuanyang pot with S divider, ear handles, a chili, steam | good |
| PandabornTeaLeaves | one bud and two leaves | good |
| PandabornTea | gaiwan: saucer, bowl, tilted lid, steam | good |
| PandabornPersimmons | two squat fruits, each with a wide flat four-sepal cap and stem stub | fair |
| PandabornBambooMushrooms | zhusun: conical cap, netted veil, stem, volva | good |
| PandabornBambooSeed | grains piled on a round woven tray | fair |
| PandabornBambooSeedCakes | two scalloped pressed cakes, one standing, one lying, dotted flower pattern | fair |
| PandabornPaperLanterns | round ribbed lantern, caps, tassel | good |

**Pass 3 (2026-11-14):** `PandabornPoles` redrawn: two long slim jointed poles laid on the vanilla plank's diagonal,
hollow ends towards you (pass 2's three short fat poles read as sausages or logs at the 28 px inventory size).
`PandabornCuredPoles` follows it: the same two poles with solid ends, a lashing and the vanilla sparkles. At 28 px
Poles reads as a jointed slanted bar beside the vanilla plank's plain board; the sparkles separate the cured ones.

## Coverage (pass 3, 2026-11-14)

Every sprite reference on what this mod adds, from the generated mod (`E:\PandabornDev\build\gen\PandabornFactions`)
and `mod/PandabornFactions`. "Own" = drawn by this pipeline (or the characters lane for portraits).

| What | Count | Own | Still vanilla | Missing | Notes |
|---|---|---|---|---|---|
| New buildings `Pandaborn*.Inkpaws` | 57 | 57 | 0 | 0 | 46 before this pass + 11 new (Cistern Tap, Ox Workshop, Standing/Hanging/String lanterns, Bamboo Fence, Potted Pine, Panda Statue, Bamboo Pinwheel, Goldfish Bowl, Garden Moon Gate). The generated data still names the stand-in's icon for the 11 until `generate` runs again; the file names match `find_icon`'s convention |
| Pole Mill (`LumberMill.Inkpaws`, coming) | 1 | 1 | | | `PandabornPoleMillIcon`: the vanilla lumber mill shows a plank; ours is the vanilla Wood-workshop house outline with a lashed pole bundle. Needs the catalogue's `icon` field (below) |
| Re-themed vanilla buildings `<Name>.Inkpaws` | 110 | | 110 | | All fine as they are: same name, same model under the material swap. None shows a beaver except the Beaver Statue, which the faction replaces with the Panda Statue |
| Goods `Pandaborn*` | 17 + 2 renamed | 19 | | | Poles and Cured poles are the vanilla Plank and TreatedPlank renamed and re-iconed by faction modifiers |
| Vanilla goods kept | 4 | | Paper, Antidote, Dandelion, Water | | Same goods, right icons |
| Recipes | 13 | 11 | 2 | | Recipe icons come from the product. `PandabornCuredPole` still shows `Sprites/Goods/TreatedPlankIcon` (generator: the renamed good's icon is not used for recipes); Paper and Dew water show the vanilla good, which is right |
| Plants | 7 | 7 | | | |
| Faction logo, new-game art, adult/child/contaminated avatars | 6 | 6 | | | |
| Bot avatar | 1 | 1 | | | New `Sprites/Pandaborn/Avatars/InkpawsBot.png` (Wooden Ox); the faction still names `Sprites/Avatars/FolktailsBot` until the catalogue changes |
| Banner decals | 4 | 10 drawn | 4 in use | | New set under `Materials/Pandaborn/Decals/Banners/`; the generated faction still uses the four Folktails banners |
| Tail decals | 4 | 4 exist (characters lane) | 4 in use | | `Materials/Pandaborn/Decals/Tails/PandabornTail*.png` exist; the generated DecalSpecs still point at the Folktails tails |
| Needs, need groups | | | | | No icon field (`NeedSpec` has none) |
| Tool groups, bottom bar, bonuses, wellbeing | | | | | The faction adds none |

Review sheets: `E:\PandabornDev\build\icons\buildings_sheet.png` (beside vanilla, three sizes),
`toolbar_sheet.png` (the whole Inkpaws toolbar, below), `goods_sheet.png`, `banners_sheet.png`,
`E:\PandabornDev\build\icons\ox\` (avatar work files), model-against-icon sheets in
`E:\PandabornDev\build\icons\models_*.png` (`model_compare.py`: each model preview, then its icon at 224, 56 and
39 px).

## Building icons (58, `buildings_sheet.png`)

Pass 3 matched the icons to the models (`E:\PandabornDev\build\models\preview\<Id>_day.png`; pass-2 and pass-3
model work). Measured against 213 vanilla building icons: median ink extent 79 px (vanilla 79), pen 3.3 px
(vanilla 3.2), coverage 11.6 % (vanilla ~8-11 %).

**Roofs.** The pass-2 `roof()` (gable end with a sag and lifted eaves) read as a pagoda when stacked. Pass 3 adds the
mod's own roof as the game camera sees it: `roof34` (three-quarter view: the gable end on the left, the long slope
with cover-tile ribs, a ridge roll), `roof_side` (the long side only, for gateways and stages) and `roof_hip`
(pavilions: Teahouse, Star Tower, the Village Hall's bell tower). `roof()` lost most of its sag. Nothing is stacked
in tiers any more.

**Redrawn to match the model** (pass 3):
| Icon | Was | Now (the model's recognisable feature) |
|---|---|---|
| Village Hall | two-tier hall, pagoda-like | the long tiled hall and its open **bell tower** at the front-left, bell inside, signal mast |
| Den | low woven hut, round door | a small house under a **big steep tiled roof**, chimney, porch posts, stone footing |
| Courtyard House | five small parts | two tiled wings at a right angle (one in three-quarter view, one gable-on), yard wall and gate |
| Terrace House | two houses stepped up a slope | a two-storey house on a stone base, railed **gallery**, flat roof deck with **drying trays** |
| Moon Loft | house on stilts, cross brace | tiled house high on bamboo stilts with its **ladder** |
| Pickle Yard | three jars merging under a lean-to | rows of glazed jars in front of the tiled shed |
| Hot Pot Hall | hot pot under a curly eave | the same pot under the model's raised vent roof |
| Cisterns (3) | straight hooped tubs (read as the steamer's baskets) | **glazed stoneware vats**: full belly, rolled lip, planked lid, stone plinth; medium with a ladder, large wide with a stair |
| Dew Collector | flat net between poles | the **woven funnel** on four bamboo posts over a vat |
| Flume set, Gate, Spout, Scoop Wheel | flat bars on X legs | the split-bamboo **half-pipe** with its U end (below) |
| Treadwheel Lift | small hub on a long box | a big treadle wheel with pedals at the top of a sloping half-pipe with pallets |
| Kite Windmill small / large | kite-tailed rotor (read as a pinwheel) | the model's **upright sails round a mast** on a square deck, wind lines; large has four sails |
| Star Tower | armillary sphere on a tower | lattice tower rising from a **hipped pavilion**, a **telescope** on the railed top |
| Hammock | hammock between two posts | the model's striped **sling hung from one tall mast** down to a front bar, a panda dozing in it |
| Nap Platform | roofed deck with cushions (read like the Teahouse) | a slatted **ground deck** under a flat canopy with two **sleeping pandas** |
| Teahouse | gable pavilion | **hipped** pavilion roof with the awning, the big teapot and a cup |
| Memorial Arch | three-bay gate (read as a temple front) | one **timber gateway** on drum-stone feet under a broad tiled roof, blank panel, **lantern cage with its flame** |
| Great Sitting Panda | panda in a rock niche (could be a teddy bear) | the same, **holding bamboo** with a leaf |
| Sky Lantern | bell jar in a cradle | the **great round lantern** on its lashed launch tower over a stepped terrace, tethers |
| Festival Square | lanterns between two poles over crates | a paved square, the tall centre pole with lantern strings to the corner poles, goods and the drum |
| Trip-Hammer Mill | busy cam and shaft | wheel in the stream, one big beam rocking on a post, head over the mortar |
| Night Gatherers' Post | mushrooms like lollipops | bamboo mushrooms with netted veils, as on the goods icon |

**New** (pass 3): Cistern Tap (vat, bamboo tap, pouring into a half-pipe), Ox Workshop (the Wooden Ox: box body, block
head, horns, one wheel under the belly, carrying handles, a mallet), Standing Lantern (post, arm, hatted paper
lantern), Hanging Lantern (big lantern under a bar on two splayed bamboo posts), String Lanterns (four small lanterns on
a sagging cord), Bamboo Fence (jointed posts, rails, lashed lattice), Potted Pine (three cloud pads in a hexagonal
pot), Panda Statue (seated panda with bamboo on a plinth), Bamboo Pinwheel (four curled blades and a tail vane),
Goldfish Bowl (basin on a stand, lily pads, a goldfish leaping), Garden Moon Gate (white wall, round opening, tiled
coping, potted bamboo), Pole Mill (above).

Kept as they were (they match their model or have none): Steamer, Paddy House, Tea Roastery, Kitchen, Lantern
Workshop, Smoke Kiln, Dry-Stone Wall, Bamboo Water Wheel, Slide and Swing, Kindergarten, Ink Studio, Hot Spring Bath
(water and steam), Opera Stage, Night Builders' and Night Couriers' posts.

### The two families

**Night folk: the moon mark.** Every Ringtail building (Moon Loft, Night Builders' Post, Night Couriers' Post, Night
Gatherers' Post, Star Tower, Opera Stage: the catalogue's `waits_for = "Ringtails"`) carries one solid crescent,
**drawn by the renderer at a fixed pixel size and place**, not by the drawing: `ink.MARKS["moon"]`, centre 17 px from
the top-right corner of the 112 px icon, radius 11 px, a 3 px clear ring erased round it (`@b(..., moon=True)`). It is
therefore identical on all six whatever each drawing's scale (pass 2 drew it in drawing units, so it changed size
with the drawing). Vanilla puts its corner signs in the same place (Discharge's arrow, the Observatory's own moon). At
56 px it is a 5.5 px crescent; at 39 px a 4 px crescent that still shows its notch. Each night post is also its day
counterpart's job (builders: mallet and pole; couriers: back-basket; gatherers: mushroom basket) plus a lantern.
Drawings must leave that corner empty.

**Water: the half-pipe.** The flume, its corner, drop and bridge, the flume gate, the paddy spout, the scoop wheel's
chute, the cistern tap and the treadwheel lift are all drawn round one motif, `half_pipe()`: the split-bamboo trough
seen a little from above, its **U-shaped cut end towards the viewer** at the left, a culm-node rib across the inside,
water along the bottom. The flume stands low on short X stakes, the bridge high on tall X trestles, the corner turns
the run towards you at a stone basin, the drop pours from one run into a lower one off a dry-stone step, the gate
puts a sluice frame and lever over it, the spout pours onto a rice field. The glazed vat (`vat()`) is the second
water motif: the three cisterns, the cistern tap and the dew collector's catch jar.

### Distinguishability (the whole toolbar, `toolbar_sheet.png`)

`src/pipeline/icons/toolbar_sheet.py` lays out every Inkpaws building (ours and the 110 vanilla icons kept by
re-themed buildings) by the bottom bar's tool group and order, at 56 and 40 px. Pairs found and fixed:
* Cisterns against the Steamer (pass 2: all stacked hooped cylinders): cisterns are now bellied vats.
* Teahouse against Nap Platform (both "roof on posts with things on a counter"): hipped roof and teapot against a flat
  canopy and sleeping pandas on a ground deck.
* Memorial Arch against Village Hall (both columns under tiered roofs): one gateway against a hall with a bell tower.
* Kite Windmill against the Bamboo Pinwheel (pass 2 kites read as pinwheel blades): upright sails on a deck.
* Hanging Lantern against Garden Moon Gate (both a rectangle at 39 px): the lantern now hangs from a bar running past
  two splayed posts, no closed frame.
* String Lanterns against Festival Square (both lanterns on a string): the square has its paving, centre pole,
  goods and drum.
Remaining near pairs, accepted: Den / Courtyard House at 39 px (one roof against two); Cistern Small (Storage) and
Cistern Tap (Water) share the vat but sit in different groups; the flume pieces share their trough on purpose.

### Verdicts (pass 3)

* good: Village Hall, Den, Courtyard House, Moon Loft, Pickle Yard, the three cisterns, Cistern Tap, Dew Collector,
  Flume, Flume Corner, Flume Bridge, Scoop Wheel, Memorial Arch, Great Sitting Panda, Sky Lantern, Star Tower,
  Teahouse, Garden Moon Gate, Goldfish Bowl, Potted Pine, Panda Statue, Bamboo Fence, Bamboo Pinwheel, Hanging and
  Standing Lantern, Pole Mill, and the pass-2 icons kept.
* fair: Terrace House (reads as a building with balconies; the trays are small), Festival Square, Flume Drop, Flume
  Gate, Paddy Spout, Nap Platform, Ox Workshop (an ox, but toy-like), Treadwheel Lift, Trip-Hammer Mill, Night
  Gatherers' Post.
* weak: **Kite Windmill small/large** (an upright-axis sail windmill is hard to draw flat: at 39 px it reads as a
  barrel or a cage; the wind lines help a little), **Hammock** (the sling-on-a-mast reads as a deck chair).

## Banner decals (10, `banners_sheet.png`)

`src/pipeline/icons/banners.py`. Vanilla banners (`Materials/Banners/<Faction>/BannerN.<Faction>`, 512 x 512, opaque,
extracted to `E:\PandabornDev\reference\vanilla-banners` for reference) are worn cloth in one faction colour with
one solid emblem in a second colour and a dark rough halo. Ours: a cream emblem on lacquer red (Folktails are yellow
on teal, Iron Teeth pink on navy), drawn with the icon engine as a fill mask, cloth, halo and wear painted in numpy.
Files `mod/PandabornFactions/Materials/Pandaborn/Decals/Banners/PandabornBanner<Name>.png`, no meta (sRGB, mipmapped,
like the coats and tail decals): Paw (the logo: paw print in the rounded diamond), Bamboo (jointed culm, leaf spray),
Moon (crescent and two stars: the Ringtails), Lantern, TeaLeaf (bud and two leaves), Rice (drooping ear), Flume (the
half-pipe end-on with water, on X stakes), Bell, Panda (face; patches cut so the cloth shows through), RingTail (the
red panda's ringed tail). No script, no religious signs. Verdicts: good except RingTail (fair: reads as a ringed tail,
could be a raccoon's) and Rice (fair at 32 px).

## Wooden Ox avatar (`InkpawsBot.png`)

`src/pipeline/icons/ox_avatar.py` (driver) and `bl_ox_avatar.py` (Blender): a generic wooden ox built from planks in
code (plank body with pegs, block head and snout, horns, ears, a rope collar, halter and rein, plank legs, one iron-shod
wheel under the chest, a red paper lantern glowing on a string from the right horn), Cycles, three-quarter bust, on
the same painted teal plate with the torn edge as the Inkpaw and Ringtail avatars (`characters/make_portraits.plate`).
512 x 512, `{"isSprite": true}`. Generic on purpose: the ox's game body is not built; when it is, render that instead.
Verdict: fair (clearly a wooden ox with a lantern, toy-like; the halter reads a little like a smile).

## Plant icons (7, `plants_sheet.png`)

Shoot bamboo (shoots breaking the field, a leaf spray), timber bamboo (jointed culm with leaf sprays), cabbage,
rice (tufts and bowing ears over paddy water), tea bush (clipped mound with a bud and two leaves on top), Sichuan
pepper (thorny shrub with husk clusters), persimmon tree (leaf and a fruit with the same cap as the goods icon).
Shipped under `Sprites/Pandaborn/Plants/`. Medians: extent 93 px, coverage 12 %, sitting 10 px below centre
(vanilla 93 px, 11.5 %, 9 px). Weakest: tea bush (the mound can read as a rock). Lotus stays drawn but unshipped
(a later update); cloud bamboo and lacquer tree were dropped.

## Faction logo

Three candidates in the vanilla form (rounded diamond, one flat colour, solid emblem), bamboo green
(132, 214, 160), 98 px, on `avatars_sheet.png` beside the Folktails and Iron Teeth logos:
* A, bamboo: a jointed stalk with three leaves. Clear, but its silhouette is close to the Folktails leaf-and-stem.
* B, paw print: a pad and five toes. Reads at 34 px, is unlike both vanilla emblems, and says "pandas" at once.
* C, sun and moon over bamboo: the idea is right (two peoples), but at 49 px it reads as a little figure with arms
  out.

**Picked: B, the paw print.** It replaces `Sprites/Pandaborn/Avatars/InkpawsLogo.png` (was a 256 px cartoon panda
face in a green disc); the meta stays `{"isSprite": true}`.

## For the catalogue lane

1. **Banners:** replace the four Folktails banner DecalSpecs (`Decals/Pandaborn/Decal.Banner1..4.Inkpaws`, texture
   `Materials/Banners/Folktails/BannerN.Folktails`) with ten, category `Banners`, `FactionId` Inkpaws, textures
   `Materials/Pandaborn/Decals/Banners/PandabornBanner{Paw,Bamboo,Moon,Lantern,TeaLeaf,Rice,Flume,Bell,Panda,RingTail}`.
2. **Tails** (characters lane's files, noticed here): the four tail DecalSpecs still use the Folktails tails although
   `Materials/Pandaborn/Decals/Tails/PandabornTail{BeadCord,Ribbon,TipCream,TwinBands}.png` exist.
3. **Bot avatar:** `catalogue/faction.toml` `bot_avatar = "Sprites/Pandaborn/Avatars/InkpawsBot"` (now
   `Sprites/Avatars/FolktailsBot`).
4. **Pole Mill:** when `LumberMill` joins `buildings.toml`, give it
   `icon = "Sprites/Pandaborn/Buildings/PandabornPoleMillIcon"` (a re-themed building does not take the naming rule).
5. **Recipe icon of a renamed good:** `Recipe.PandabornCuredPole` shows `Sprites/Goods/TreatedPlankIcon`. In poles mode
   "rename" the generator should give recipes producing Plank / TreatedPlank the renamed icon
   (`Sprites/Pandaborn/Goods/PandabornPolesIcon`, `PandabornCuredPolesIcon`).
6. **Tool groups:** the flume set (Flume, Corner, Drop, Bridge) sits in **Decoration** (its PoleBanner basis) between
   the stream gauge and the banners, while the Flume Gate and Paddy Spout are in Landscaping and the Scoop Wheel,
   Cistern Tap and Treadwheel Lift in Water. Suggest `tool_group = "Water"` (or Landscaping, beside the gate) for the
   four flume pieces so the water family sits together. The **Lantern Workshop** is in **Food** (archetype workshop);
   it makes paper lanterns from paper, so Wood (beside the Smoke Kiln and Paper Mill) fits better.
7. Run `generate` again: the 11 new building icons follow the naming rule (`Pandaborn<Name>Icon`, checked against
   the report's "no icon" notes and `find_icon`) and are picked up without a catalogue change.

## Open quality issues

* **Kite Windmill** and **Hammock** icons (see verdicts). A Kite Windmill with its model in game may make a
  different drawing obvious; the Hammock may be better as the sleeper alone.
* **Goods are still denser than vanilla**: median coverage 19 % against 15 %. The gap is the subjects: bowls, jars
  and steamers are closed shapes with rims.
* **Sichuan pepper** reads as "seed pods on a sprig"; colour would settle it and the style has none.
* **Persimmons** at 28 px: the cap shrinks to a lid line.
* **Bowl family**: steamed rice, sweet rice balls, hot pot, tea and the steamer are all round vessels; fine at 40 px,
  close at 28 px.
* Not checked in game: no game run in pass 3 (the queue was deep). The loader path is verified in the decompiled code.

## Still to do

**Need icons: none needed.** `NeedSpec` has no icon field; only critical needs show a status badge, and the
Inkpaws reuse the vanilla ones.

**When new models land:** Trip-Hammer Mill, Kitchen, Ox Workshop, Treadwheel Lift, Cistern Tap, Dry-Stone Wall and
the Large Kite Windmill have no model yet; their icons are drawn from the design and should be checked against the
model when it exists (`model_compare.py` puts each model preview beside its icon).
