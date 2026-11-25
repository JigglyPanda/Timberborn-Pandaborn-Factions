# Icons

How the game draws its UI icons, the rules we copy, how our icons are made, and what is still weak.
Pipeline code: [src/pipeline/icons/](../../src/pipeline/icons/README.md). Measured 2026-11-14 on game 1.1.2.8;
pass 3 (icons matched to the models, the two families, banners, the Wooden Ox avatar) 2026-11-14; pass 4 (the weak
icons redrawn, the workplaces' marks, the tool group icon, store art; the coordinator's task sheet calls it "pass 3")
2026-11-25.

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
| Tool group, building group | `ToolGroupSpec.Icon`, `BlockObjectToolGroupSpec.Icon` | `Sprites/BottomBar/BuildingGroups/<Group>` | 112 x 112 | small painted signs: a gold outline round flat colour, each area hatched in a second tone, no shadow. Ours: `Sprites/Pandaborn/BottomBar/PandabornNightWatchIcon` (below) |
| Faction logo | `FactionSpec.Logo` | `Sprites/Avatars/<Faction>Logo` | 98 x 98 | flat colour emblem |
| New-game art, avatars | `FactionSpec.NewGameFullAvatar`, `Avatar`... | `Sprites/Avatars/...` | 420 x 560, 512 x 512 | painted character art |
| Needs, need groups | none | `NeedSpec` and `NeedGroupSpec` have no sprite field. Only `CriticalNeedSpec.SpriteName` (Hunger, Thirst, Injury...) picks a status badge from `Sprites/StatusIcons` (see "Need and wellbeing icons") | 512 | |
| Bonuses (wellbeing panel) | `BonusTypeSpec.Icon` | `Sprites/Bonuses/<Id>` | | global vanilla specs; the faction adds none |
| Good groups (top bar) | `GoodGroupSpec.Icon` | `Sprites/TopBar/<Group>` | | global; our goods sit in the vanilla Food, Ingredients and Materials groups |
| Workshop preview | file `thumbnail.png` in the mod's root | | 960 x 540 (official examples), ours 1280 x 720 | read only by the Steam Workshop uploader (see "Store art") |

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

**Pass 4 (2026-11-25):** 20 icons. `PandabornTea` redrawn: tea is a dry good now (roasted leaves, served with water
at the Teahouse; nobody takes it from storage), so the gaiwan with steam became a **lidded tea caddy marked with a
tea leaf and a heap of rolled dry leaves**; no cup, no steam. Verdict: good (at 28 px a jar and a heap; the Pickles
jar keeps its round belly, collar and bubbles). New: `PandabornWoodenOx`, the automaton's block head with horns, bolt
eyes and nose ring, for the Ox Workshop's recipe (vanilla bot recipes carry no icon; ours need not either, see "For
the catalogue lane"). Bamboo seed and seed cakes are unchanged.

**Pass 3 (2026-11-14):** `PandabornPoles` redrawn: two long slim jointed poles laid on the vanilla plank's diagonal,
hollow ends towards you (pass 2's three short fat poles read as sausages or logs at the 28 px inventory size).
`PandabornCuredPoles` follows it: the same two poles with solid ends, a lashing and the vanilla sparkles. At 28 px
Poles reads as a jointed slanted bar beside the vanilla plank's plain board; the sparkles separate the cured ones.

## Coverage (pass 4, 2026-11-25)

Every sprite reference on what this mod adds, read from a fresh generation of the catalogue (`src/gen/generate.py
--out E:\PandabornDev\build\icons\gen-scratch\PandabornFactions`, so the shared build folder is not touched) and
`mod/PandabornFactions`. "Own" = drawn by this pipeline (or the characters lane for portraits).

| What | Count | Own | Still vanilla | Missing | Notes |
|---|---|---|---|---|---|
| New buildings `Pandaborn*.Inkpaws` | 58 | 58 | 0 | 0 | 57 in today's generated data + the Star Tower (hidden until a night post can keep its science cost; its icon is ready). New this pass: `PandabornFlumeBridgeSpan` (it showed the vanilla Throttling Valve) |
| Pole Mill (`LumberMill.Inkpaws`) | 1 | 1 | | | `PandabornPoleMillIcon`, set in the catalogue |
| Re-themed vanilla buildings `<Name>.Inkpaws` | 110 | | 110 | | Same name, same model under the material swap: the vanilla icon is the right one |
| Goods `Pandaborn*` | 17 + 2 renamed | 19 | | | Poles and Cured poles are the vanilla Plank and TreatedPlank renamed and re-iconed by faction modifiers. Tea redrawn as a dry good |
| Vanilla goods kept | 4 | | Paper, Antidote, Dandelion, Water | | Same goods, right icons |
| Recipes | 13 | 10 + 2 by modifier | 2 | 0 | A recipe takes its first product's icon; the generator now gives Poles and Cured poles theirs (Plank and TreatedPlank recipes by modifier, `PandabornCuredPole`). Paper and Dew water show the vanilla good, which is right. `PandabornWoodenOx` has an empty icon exactly like the vanilla `Bot.Folktails` recipe (no product); an icon is drawn if wanted |
| Plants | 9 | 9 | 0 | | New this pass: the flowering twins (they showed the Carrot and the Chestnut tree) |
| Tool group | 1 | 1 | | | `PandabornNightWatch`: its own bottom-bar sign is drawn; the catalogue still names the Moon Loft icon |
| Faction logo, new-game art, adult/child/contaminated avatars, Ringtail avatars | 10 | 10 | | | |
| Bot avatar | 1 | 1 | | | `InkpawsBot.png`: the characters lane's render of the real Wooden Ox (not this pipeline's any more) |
| Wonder picture | 1 | 1 | | | models lane |
| Banner decals | 10 | 10 | | | In use since the catalogue lane wired them; the ringed tail redrawn this pass |
| Tail decals | 4 | 4 (characters lane) | | | In use |
| Needs, need groups | 26 | | | | No icon field anywhere (below) |
| Bonuses, good groups, status badges | | | all | | Global vanilla specs; the faction adds none |
| Workshop preview | 1 | 1 | | | `mod/PandabornFactions/thumbnail.png` (below) |

Every PNG under `Sprites/Pandaborn/{Buildings,Goods,Plants,BottomBar,Avatars}` has its `.png.meta.json` (checked by
script: 59 + 20 + 9 + 1 + 11 files). Sprites nothing refers to yet: `PandabornStarTowerIcon` (hidden building),
`PandabornWoodenOxIcon` (optional recipe icon), `BottomBar/PandabornNightWatchIcon` (until the catalogue names it).

Review sheets: `E:\PandabornDev\build\icons\buildings_sheet.png` (beside vanilla, three sizes),
`toolbar_sheet.png` (the whole Inkpaws toolbar, below), `goods_sheet.png`, `plants_sheet.png`, `banners_sheet.png`,
`toolgroups_sheet.png` (our group sign in the row of vanilla ones), model-against-icon sheets in
`E:\PandabornDev\build\icons\models_*.png` (`model_compare.py`: each model at the game's zoom, then its icon at 224,
56 and 39 px), `store_try\review.png` (the store pictures at listing sizes).

## Building icons (59, `buildings_sheet.png`)

### Pass 4 (2026-11-25): the weak ones redrawn, each workplace's mark

The models lane's game-zoom previews (`E:\PandabornDev\build\models\preview\sheet_gamezoom.png`, `gamezoom\<Id>_day.png`)
show each workplace's one mark from above; the icon now shows the same mark. Measured against 213 vanilla building
icons: median ink extent 80 px (vanilla 79), pen 3.3 px (vanilla 3.2), coverage 12.3 % (vanilla ~8-11 %).

| Icon | Was (pass 3) | Now |
|---|---|---|
| Kite Windmill | two bellied sails between top and bottom arms: a barrel or a cage at 39 px | the rotor in **three-quarter view** (`sail_rotor`): the spoke tips lie on an ellipse, each sail is a parallelogram as wide as it is turned to you, so the three differ (one face-on behind the mast, two swung round in front), the spokes meet in a raised hub like an umbrella frame, a clear mast with a pennant, a deck |
| Large Kite Windmill | the same with four sails | the same rotor, taller, on a wider deck, **five sails** |
| Hammock | a sling from one mast down to a front bar: a deck chair | the vanilla hammock form: a **striped sling between a tall bamboo mast and a short post, a panda's round back and head above the cloth** |
| Terrace House | a flat front with three bars | the block **seen from the corner**: the tiled skirt roof and railed gallery between the floors, and the flat roof deck with its **two drying trays** large on top |
| Flume Drop | a nine-stone step | four big stones for the pier, the upper half-pipe, the fall, the lower one |
| Flume Gate | lever over a bare frame, the pipe sideways | as the model: the half-pipe **runs towards you** through a small **roofed sluice frame**, the slatted board in it, a **tall lever with its hanging stone counterweight** |
| Paddy Spout | a half-pipe pouring off a stone lip | the model's small roofed stone basin and its **low wide fan of three culms** pouring into the paddy |
| Treadwheel Lift | a big pedal wheel in the open | the pedal wheel on its axle with the hand rail **under the tiled shed roof** of the model, the chain of pallets coming up the sloping half-pipe |
| Ox Workshop | a four-legged plank ox on a wheel | the Wooden Ox as it is now: an **upright horned automaton** (block head, bolt eyes, nose ring, plank limbs) and a cog |
| Pickle Yard | lidded jars in front of the shed | five big jars **under their tied cloth tops** (solid: the red cloth is the mark from above), no shed (with it the yard and the Tea Roastery were both "a house with round things in front") |
| Tea Roastery | a wok on a brick stove | the roasting shed with its chimney and the **round trays of tea** on the rack, the tea sprig on the two nearest |
| Lantern Workshop | a bench with a frame and a lantern | the tiled workshop with its **cord of finished lanterns** between bamboo poles |
| Paddy House | a tiled farmhouse | the farmhouse under its **thatch** (`roof_thatch`: rounded ridge, shaggy eave, a batten, straw), posts, the paddy |
| Night Builders' Post | a lantern post, a mallet and a pole | the model's **shear legs** (two lashed spars and a guy rope) with the lantern hung from the top, and the mallet |
| Star Tower | telescope on the tower | the same with the **vanilla Observatory's four-point stars** round the telescope: night science at a glance, beside the moon mark |
| Opera Stage | with the moon mark | the same drawing **without the moon**: it ships as an ordinary attraction since 2026-11-25 (DESIGN.md), in Wellbeing |

**New:** Flume Bridge Span (`PandabornFlumeBridgeSpanIcon`): the bridge's half-pipe on its two X-trestles crossing
over another flume that runs towards you underneath (the flume family's motif twice).

Kept after checking against the game-zoom previews: Steamer (the basket tower), Hot Pot Hall (the pot under its
raised roof), Smoke Kiln, Kitchen (its table of dishes; the model's mark is a millstone under an awning, which would
read as the Trip-Hammer Mill), Trip-Hammer Mill, Nap Platform (ground deck, canopy, sleepers), the cisterns, Dew
Collector, Village Hall, homes, monuments, decorations, the night couriers' and gatherers' posts.

Verdicts (pass 4): good: Hammock, Terrace House, Flume Gate, Ox Workshop, Pickle Yard, Lantern Workshop, Star Tower,
Opera Stage. Fair: Kite Windmill and Large Kite Windmill (sails round a mast with a pennant at 56 px; at 39 px a
cluster of upright panels, no longer a barrel), Flume Drop, Flume Bridge Span (close to the Flume Bridge on purpose),
Paddy Spout, Treadwheel Lift, Tea Roastery (trays read as baskets), Paddy House (the thatch reads as a patterned roof
at 39 px), Night Builders' Post (shear legs can read as a tent). Weak: none left on the sheet.

### Pass 3 (2026-11-14)

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
Gatherers' Post, Star Tower: the catalogue's Night Watch group; the Opera Stage left the family on 2026-11-25, when it
became an ordinary attraction) carries one solid crescent,
**drawn by the renderer at a fixed pixel size and place**, not by the drawing: `ink.MARKS["moon"]`, centre 17 px from
the top-right corner of the 112 px icon, radius 11 px, a 3 px clear ring erased round it (`@b(..., moon=True)`). It is
therefore identical on all five whatever each drawing's scale (pass 2 drew it in drawing units, so it changed size
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
  barrel or a cage; the wind lines help a little), **Hammock** (the sling-on-a-mast reads as a deck chair). Both
  redrawn in pass 4 (above).

### Tool group icon (pass 4)

`src/pipeline/icons/toolgroup.py` paints `Sprites/Pandaborn/BottomBar/PandabornNightWatchIcon.png` (112 x 112,
`{"isSprite": true}`) in the bottom bar's own style, which is not the building icons' line art: a gold outline
(190, 160, 108) about 3.5 px wide round flat colour, each colour area hatched in a second tone, no shadow. The sign is
the night folk's two things: the **crescent moon** of the moon mark in the pale yellow of the vanilla Housing door,
and a **red paper lantern** hung from its upper horn. On `toolgroups_sheet.png` it sits between the vanilla Wellbeing
masks and the Wood log at 112, 56 and 40 px and reads as one of the set. Layers of one sign are separate drawings
on a shared frame (`ink.Icon.bounds`).

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

**Pass 4:** RingTail redrawn (the other nine files are byte-identical after a re-run): an S-curved tail, slim where
it joins the body and thick and bushy from there to a blunt end, a long pale tip, and soft rings (narrow gaps with a
tufted edge that bow towards the tip and thin out along the tail) where pass 2 had a thin bar cut by hard stripes.
Two earlier tries are worth knowing: a fat curled tail with zigzag gaps read as a shrimp, a straight thick one as a
loaf. Verdict: fair to good; a tail at 64 px, a ringed comma at 32 px.

## Wooden Ox avatar (`InkpawsBot.png`): superseded

`mod/PandabornFactions/Sprites/Pandaborn/Avatars/InkpawsBot.png` is now the characters lane's render of the real
Wooden Ox body. This pipeline's generic plank ox (`ox_avatar.py`, `bl_ox_avatar.py`, pass 3) is **superseded**: the
two files stay for reference, are marked so at the top, were never part of `build_icons.py`'s run, write to
`E:\PandabornDev\build\icons\ox\` by default and refuse any path inside `mod/`. Nothing in this folder writes
`Sprites/Pandaborn/Avatars` except the faction logo.

## Plant icons (9, `plants_sheet.png`)

**Pass 4:** the flowering twins, which showed their basis' vanilla icon (a carrot, a chestnut leaf):
`PandabornTimberBambooInFlowerIcon` (the timber bamboo's jointed culm with seed plumes hanging from every joint where
the leaf sprays were, one last thin leaf, seed falling) and `PandabornShootBambooInFlowerIcon` (no shoots: three thin
culms on the field with plumes arching out and hanging). A plume (`plume()`) is a wiry branchlet with solid spikelets
dangling along it. Nobody plants them, so the icon shows only on the plant's own panel. Verdicts: timber good, shoot
fair (three drooping tufts; the ground rows say "field").

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

## Need and wellbeing icons: none to draw (checked 2026-11-25)

From the decompiled game (1.1.2.8) and the vanilla blueprints:
* `NeedSpec` (Id, Order, NeedGroupId, CharacterType, DisplayName, values...) and `NeedGroupSpec` have **no sprite
  field**. The need rows of the entity panel and the wellbeing window (`Timberborn.WellbeingUI.NeedView`,
  `NeedViewFactory`, `PopulationWellbeingCounter*`) are text and bars; building effect lists
  (`NeedApplicationUI.NeedEffectsSpecDescriber`, attractions, ranged effects) are text.
* The wellbeing window shows three pictures: the **faction logo** (`BasicStatisticsPanelFactory`: ours), the
  **bonus icons** (`WellbeingSummaryBonusFactory`: `BonusTypeSpec.Icon`, the four global vanilla bonus types; the
  faction only raises the MovementSpeed cap by modifier) and, in the goal rows, the avatar of an unlockable faction.
* `CriticalNeedSpec.SpriteName` names a status badge under `Sprites/StatusIcons`. Only the vanilla critical needs
  have one (Hunger, Thirst, Exhaustion, Injury, ChippedTeeth, BadwaterContamination and the bots' two), all in the
  `Common` need collection every faction shares; none of our 26 needs is critical. Those badges are the game's own
  and right for pandas too. (A faction could re-point one with a blueprint modifier on `SpriteName`; not needed.)
* `GoodGroupSpec.Icon` (top bar) is global; our goods use the vanilla Food, Ingredients and Materials groups.
So no need of ours shows a vanilla or blank icon anywhere, and there is nothing to draw. If a critical need is ever
added, its badge goes to `Sprites/StatusIcons/<name>` (a new name, never a vanilla one) in the status badges' style.

## Store art (pass 4)

`src/pipeline/icons/store.py`, Pillow only, from pictures already in the repository; writes `art/store/` and the
mod's `thumbnail.png`.

* **What the game uses.** The Steam Workshop uploader (`SteamWorkshopModUploadingUI.SteamWorkshopModThumbnail`)
  takes `thumbnail.png` (or `.jpg`/`.jpeg`) from the mod's root as the Workshop item's preview picture, else its
  own default. Nothing else reads it (the in-game mod list has no pictures). The official examples (Empty,
  TailsAndBanners) ship 960 x 540; the Reskin ships 1280 x 720. Steam refuses preview files of 1 MB or more and
  crops the preview to a square in listings; mod.io wants a 16:9 logo of at least 512 x 288.
* `art/store/workshop_preview_1280x720.png` = `mod/PandabornFactions/thumbnail.png` (1280 x 720, 656 KB; the script
  fails above 950 KB): the dusk village under the rising Sky Lantern (the wonder picture, a render of the mod's own
  models; its sky continued upwards with painted stars and lanterns), the logo and the title, the avatar plates of
  the Inkpaw, the Ringtail and the Wooden Ox, four banner decals in the margins. Title and plates sit inside the
  middle 720 px, so Steam's square crop keeps them.
* `art/store/thumbnail_square_1024.png` (1024 x 1024, 650 KB): the same pieces stacked for square slots.
* The only writing is the title "Pandaborn - Factions" in Segoe UI Bold; no script on any texture.
* The family resemblance to the Reskin's thumbnail (dark ground, a row of avatar plates) is on purpose.
* **Wants a picture from the game later:** the Workshop gallery needs real screenshots (the store lane's list,
  `catalogue/text/store/screenshots.md`: a wide village by day, a flume line, the festival without developer
  controls). When a clean wide village shot exists it would make a stronger backdrop than the wonder strip; the
  script takes any picture as `village()`. The preview has not been seen in the uploader's own window.

## For the catalogue lane

**All seven requests of pass 3 were adopted** (seen in a fresh generation): the ten banners and the four tails are
wired, `FactionSpec.BotAvatar` names `Sprites/Pandaborn/Avatars/InkpawsBot` (the characters lane's ox portrait), the
Pole Mill has its icon, recipes of the renamed poles show the pole icons, the flume set and the Lantern Workshop
moved to Water and Wood, and the eleven icons of that pass were picked up by the naming rule. New requests:

1. **Night Watch tool group:** `catalogue/faction.toml` `[tool_groups.PandabornNightWatch]`
   `icon = "Sprites/Pandaborn/BottomBar/PandabornNightWatchIcon"` (now the Moon Loft's building icon, "until the
   icons lane draws a bottom-bar moon": it is drawn).
2. **Flume Bridge Span:** the sprite is `Sprites/Pandaborn/Buildings/PandabornFlumeBridgeSpanIcon` (with its
   `.png.meta.json`). It follows the naming rule, so `generate` picks it up with no catalogue change (checked: the
   fresh generation no longer names the Throttling Valve); set `icon` explicitly only if you prefer.
3. **Flowering twins:** `Sprites/Pandaborn/Plants/PandabornShootBambooInFlowerIcon` and
   `PandabornTimberBambooInFlowerIcon`, by the naming rule as well (checked the same way).
4. **Wooden Ox recipe (optional):** `Recipe.PandabornWoodenOx` has `Icon: ""`, as the vanilla bot recipes do. If the
   Ox Workshop's panel shows an empty square, give the recipe
   `icon = "Sprites/Pandaborn/Goods/PandabornWoodenOxIcon"`; if not, say so and the sprite is removed.
5. **Opera Stage:** its icon lost the moon mark (an ordinary attraction). If it ever returns to the Night Watch
   group, tell the icons lane: one argument (`moon=True`) puts it back.
6. **Star Tower:** hidden today; its icon (`PandabornStarTowerIcon`, moon mark and stars) is in the mod, unused.
7. **thumbnail.png** is a new hand-written file in the mod's root (`tools/validate.py` already allows it); `package`
   could check it stays under 1 MB.

## Open quality issues

* **Kite Windmills** are fair, not good: at 39 px three or five upright panels with a pennant. Seeing the mill turn
  in game may suggest a better drawing.
* **Tea Roastery** (trays read as baskets), **Paddy House** (thatch), **Night Builders' Post** (shear legs or a
  tent), **Flume Drop**, **Flume Bridge Span**, **Paddy Spout**, **Treadwheel Lift** (its catalogue model is still a
  stand-in on the vanilla power wheel): fair.
* **Goods are still denser than vanilla**: median coverage 19 % against 15 %. The gap is the subjects: bowls, jars
  and steamers are closed shapes with rims.
* **Sichuan pepper** reads as "seed pods on a sprig"; colour would settle it and the style has none.
* **Persimmons** at 28 px: the cap shrinks to a lid line.
* **Bowl family**: steamed rice, sweet rice balls, hot pot and the steamer are all round vessels; fine at 40 px,
  close at 28 px. Tea left the family in pass 4.
* **Not checked in game** (no game run in pass 3 or pass 4): every icon at the toolbar's real size, the tool group
  sign in the bottom bar (and whether the bar tints or scales a 112 px sign like the vanilla ones), the new plant
  icons on the flowering twins' panel, the thumbnail in the Workshop uploader. The loader paths are verified in the
  decompiled code and by a fresh generation.

## Still to do

**Need icons: none needed** (see "Need and wellbeing icons").

**Wants a game screenshot or render later:** a look at the toolbar and bottom bar in a running Inkpaws game
(`-Screenshots screen@start` with the Night Watch group open), and clean village screenshots for the Workshop
gallery and, if wanted, a new backdrop for the preview.

**Models:** the seven buildings pass 3 listed as having no model (Trip-Hammer Mill, Kitchen, Ox Workshop, Treadwheel
Lift, Cistern Tap, Dry-Stone Wall, Large Kite Windmill) all have kit models now, and pass 4 checked each icon against
its game-zoom preview. One is not adopted yet: the catalogue still builds the Treadwheel Lift on the vanilla power
wheel as a stand-in (its kit model is for a water-pump basis); the icon shows the kit model.
