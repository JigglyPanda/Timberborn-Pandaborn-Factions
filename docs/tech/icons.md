# Icons

How the game draws its UI icons, the rules we copy, how our icons are made, and what is still weak.
Pipeline code: [src/pipeline/icons/](../../src/pipeline/icons/README.md). Measured 2026-11-14 on game 1.1.2.8.

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
   drying persimmons sit on round bamboo trays, not on strings); no religious imagery; roofs are farmhouse roofs
   with a gentle sag (the `roof()` motif), never upturned palace eaves.
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

## Building icons (46, `buildings_sheet.png`)

Every building marked *new* in CONTENT.md draft 2: Village Hall, Festival Square; Den, Courtyard House, Terrace
House, Moon Loft; Steamer, Pickle Yard, Paddy House, Tea Roastery, Trip-Hammer Mill, Kitchen, Hot Pot Hall;
Lantern Workshop, Smoke Kiln; Cistern Small/Medium/Large; Flume, Flume Corner, Flume Drop, Flume Bridge, Flume
Gate, Scoop Wheel, Paddy Spout, Dew Collector, Treadwheel Lift, Dry-Stone Wall; Bamboo Water Wheel, Kite Windmill
Small/Large; Star Tower; Hammock, Nap Platform, Teahouse, Slide and Swing, Panda Kindergarten, Ink Studio, Hot
Spring Bath, Opera Stage; Night Builders' Post, Night Courier Post, Night Forager's Post; Memorial Arch, Great
Sitting Panda, Sky Lantern. Decorations (lanterns, fence, pinwheel...) are not drawn yet. The catalogue speaks of
"the four night posts" but lists three; three are drawn.

Drawn from the descriptions, not from models (none exist yet). Each shows what the building does, standing on a
ground line, in the `BUILDING` pen style; small buildings are drawn small (the `size` argument of `@b`), as vanilla
does for tanks and lodges. Measured against 213 vanilla building icons: median ink extent 78 px (vanilla 79),
coverage 11 % (vanilla 8 %), pen width 3.3 px (vanilla 3.2).

Shared motifs in `buildings.py`: `roof` (gable end of a grey tile roof, gently sagging slopes, a short ridge cap,
eaves lifting only slightly), `frame_wall` (timber frame, plaster panels), `house`, `door`, `round_window`,
`lantern`, `bamboo_post`, `wheel` (paddles or tube buckets), `flume_run`, `trestle`, `cistern`, `pao_jar`,
`water`, `ground`, `moon`.

**The Ringtail moon.** Moon Loft, the three night posts, Star Tower and Opera Stage carry a solid crescent in the
top-right corner (radius 11 units, ~9 px at 112). At 56 px (toolbar button size) it reads clearly as a moon on
every one of them. At ~39 px it is still a visible crescent but small, and on the busiest icons (Opera Stage) it
competes with the roof line. It works as the "Ringtail building" rule; if the toolbar shows these smaller than
56 px, enlarge it to radius 13 and keep that corner clear of other lines.

Verdicts:
* good: Village Hall, Den, Moon Loft, Steamer, Tea Roastery, Teahouse, Hot Pot Hall, Kitchen, Lantern Workshop,
  Smoke Kiln, the three cisterns, Flume, Flume Bridge, Flume Drop, Flume Gate, Dew Collector, Dry-Stone Wall,
  Bamboo Water Wheel, Star Tower, Hammock, Nap Platform, Slide and Swing, Panda Kindergarten, Ink Studio, Hot Spring
  Bath, Opera Stage, Memorial Arch, Paddy House.
* fair: Festival Square, Terrace House, Paddy Spout, Great Sitting Panda (reads as a seated panda in a rock niche;
  can look like a teddy bear), Night Courier Post, Night Builders' Post, Kite Windmill Small/Large (the kite sails
  read as pinwheel petals).
* weak, redo: **Sky Lantern** (reads as a bell jar or balloon; needs a taller paper-bag shape and a lighter
  cradle), **Courtyard House** (too many small parts at 56 px), **Pickle Yard** (jars under the lean-to merge),
  **Flume Corner** (the turn is hard to read in a side view; try a top-down L), **Treadwheel Lift** and
  **Trip-Hammer Mill** (both mechanisms read only enlarged), **Scoop Wheel** (busy rim), **Night Forager's Post**
  (mushrooms look like lollipops).

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

## Open quality issues

* **Goods are still denser than vanilla**: median coverage 19 % against 15 % (was 21 %). The rest of the gap is
  the subjects: bowls, jars and steamers are closed shapes with rims. Further cuts would cost recognisability.
* **Sichuan pepper** is better (open husks with seeds plus the pinnate leaf) but still reads as "seed pods on a
  sprig" rather than unmistakably Sichuan pepper; colour (reddish husks) would settle it, and the style has none.
* **Persimmons** now have the wide flat cap, which separates them from tomatoes at 40 px; at 28 px the cap
  shrinks to a lid line.
* **Bowl family**: steamed rice, sweet rice balls, hot pot, tea and the steamer are all round vessels. They
  separate by what sits on top (steam, balls and spoon, divider and handles, lid and saucer, woven lid). Fine at
  40 px, close at 28 px.
* The building icons marked weak above.
* Not checked in game: no blueprint references these sprites yet. The loader path is verified in the decompiled
  code (`ModSpriteConverter`, `ModTextureSettingLoader`); `tools/validate.py` passes.

## Still to do

**Need icons: none needed.** `NeedSpec` has no icon field; the needs panel is text and bars. Only critical needs
(hunger, thirst, ...) show a status badge, and the Inkpaws reuse the vanilla ones. A new critical need would need a
512 px coloured badge in `Sprites/StatusIcons`, a different style with its own `Style` preset.

**Decoration icons** (lanterns, fence, hedge, pinwheel, scarecrow, bench, banners, goldfish bowl, moon gate, tile
roofs): same `BUILDING` style, small sizes.

**From models later.** When the building models exist, Blender can render each `.blend` with Freestyle
(silhouette and crease lines, orthographic 3/4 camera) to `E:\PandabornDev\build\icons\ref\` as a reference to
check the icon against the model. Do not ship that output: it is uniform and mechanical next to the hand-sketched
vanilla set.

**New-game art and avatars.** `NewGameFullAvatar` (420 x 560) and the 512 px avatars are painted 3D character
renders in vanilla, not line art. They belong to the character pipeline (render the panda `.timbermesh` in Blender
with the game's lighting), not to this one.
