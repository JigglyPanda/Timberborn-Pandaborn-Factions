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

1. Pick the file: goods in `src/pipeline/icons/goods.py`, plants in `plants.py`, logo in `logo.py`.
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
   drying persimmons sit on round bamboo trays, not on strings).

## The goods set (2026-11-14)

25 icons in `mod/PandabornFactions/Sprites/Pandaborn/Goods/`, referenced as
`Sprites/Pandaborn/Goods/<Id>Icon` (ids assumed `Pandaborn<Name>`; rename the function's id if the blueprint
uses another).

| Id | Shows | Verdict |
|---|---|---|
| PandabornBambooShoots | two plump curved shoots wrapped in pointed sheaths, root band | good |
| PandabornBambooPoles | three hollow poles, bulging nodes, a leafy twig | good |
| PandabornRice | drooping ear of packed grains on its stalk, a leaf | good |
| PandabornRiceFlour | tied sack + rice ear (vanilla flour convention) | good |
| PandabornSteamedRice | bowl heaped with rice, three steam wisps | good |
| PandabornCabbage | napa cabbage: tall head, frilly top, white ribs | good |
| PandabornSichuanPepper | thorny twig, pinnate leaf, four husks split open on their seeds | weak |
| PandabornPickles | pao cai jar: round belly, water-seal collar, bowl lid, fermentation bubbles | good |
| PandabornHotPot | yuanyang pot with S divider, ear handles, chilies, steam | good |
| PandabornTeaLeaves | one bud and two leaves | good |
| PandabornTea | gaiwan: saucer, bowl, tilted lid, steam | good |
| PandabornPersimmons | two squat fruits with broad four-lobed caps, a leaf | fair |
| PandabornBambooMushrooms | zhusun: conical cap, netted veil (hatched lattice), stem, volva | good |
| PandabornBambooCharcoal | stack of solid tube ends with hollow centres and cracks | fair |
| PandabornPaperLanterns | round ribbed lantern, caps, tassel | good |
| PandabornRiceBalls (tangyuan) | three glossy balls in a bowl, porcelain spoon | good |
| PandabornBambooSeed | pile of grain outlines on a round woven tray | fair |
| PandabornBambooSeedCakes | two scalloped pressed cakes with a four-petal pattern | fair |
| PandabornCuredPoles | two solid (dark) poles with smoke wisps | weak |
| PandabornTofu | two soft cubes, two soybeans | good (likely cut) |
| PandabornLacquer | pot of solid dark sap, brush, drip | fair (likely cut) |
| PandabornLacqueredPoles | two poles with gloss lines + sparkles (vanilla 'treated') | good (likely cut) |
| PandabornPersimmonCakes | two flattened dried persimmons, cap, sugar-bloom dots | weak (likely cut) |
| PandabornLotusRoot | two linked segments + a slice with its ring of holes | weak (likely cut) |
| PandabornOxParts | carved horned ox head with peg eyes, a pegged dowel | weak (likely cut) |

## Open quality issues

* **Denser than vanilla.** Our median ink coverage is 21 % against vanilla's 15 %: more interior lines per icon.
  At 80 px the set sits well beside vanilla; at 28 px the busiest ones (charcoal, seed cakes, mushroom, persimmon
  cakes, ox parts) turn into texture. Next pass: drop one interior detail from each of those.
* **Sichuan pepper** reads as "berries/seed pods on a twig"; the split-husk detail is too small to carry at 40 px.
  The pinnate leaf is the strongest cue. Alternative to try: three large split husks, no twig.
* **Cured poles** depend on the smoke wisps, which read as generic steam; solid poles read as logs. Needs a better
  "smoked" cue, or accept it as "poles + heat".
* **Persimmon cakes vs bamboo seed cakes**: both are round flat cakes; if both survive the cut, persimmon cakes
  should move to the round bamboo drying tray (as the review rule suggests) to separate them.
* **Bowl family**: steamed rice, rice balls, hot pot and lacquer are all round vessels; they separate by what sits
  on top (steam / balls + spoon / divider + handles / brush). Fine at 40 px, close at 28 px (hot pot vs lacquer).
* **Persimmons** can read as tomatoes; the broad cap and the leaf carry it. Colour would settle it but the style
  has none.
* **Bamboo charcoal**: no vanilla precedent for a black material; solid ink + cracks is our convention.
* Not checked in game yet: the goods do not exist as blueprints. The loader path is verified in the decompiled
  code (`ModSpriteConverter`, `ModTextureSettingLoader`); `tools/validate.py` passes.

## Extending the pipeline

**Plant icons (implemented as proposals).** `plants.py` draws all nine planned plants (river and cloud bamboo,
persimmon and lacquer trees, rice, lotus, cabbage, tea bush, Sichuan pepper) in the `PLANT` style, calibrated
against the 22 vanilla plant icons (`plants_sheet.png`). They render to `E:\PandabornDev\build\icons\rendered\Plants`
only (`ship=False`). To ship: decide the paths the plant blueprints use (vanilla keeps the icon next to the plant,
e.g. `NaturalResources/Pandaborn/Crops/Rice/...`), set `ship=True` and give the group that folder.

**Building icons (style defined, not drawn).** Confirmed: vanilla building icons are pen sketches, not renders of
the building model. So ours should be drawn with the same engine in the `BUILDING` style (calibrated numbers in
`ink.py`), one function per building, showing the building's function as a silhouette (a steamer basket for the
steamer, a teapot for the teahouse, a lantern for the lantern workshop), with shared motifs for roofs, posts and
ground lines. Re-themed vanilla buildings keep their vanilla icon. Blender can help as a reference underlay:
render our `.blend` building model with Freestyle (silhouette and crease lines only, orthographic 3/4 camera) to
`E:\PandabornDev\build\icons\ref\`, then trace the important lines as `spline` calls. Do not ship the Freestyle
output itself: it is uniform and mechanical next to the hand-sketched vanilla set.

**Need icons: none needed.** `NeedSpec` has no icon field; the needs panel is text and bars. Only critical needs
(hunger, thirst, ...) show a status badge, and the Inkpaws reuse the vanilla ones. If a new critical need is ever
added, its badge is a 512 px coloured disc in `Sprites/StatusIcons`, a different style that would need its own
`Style` preset.

**Faction logo (proposal drawn).** `logo.py` draws an Inkpaws logo in the vanilla form: rounded diamond frame and a
solid bamboo emblem in bamboo green (132, 214, 160), 98 px (`avatars_sheet.png`, `rendered/Avatars/InkpawsLogo.png`).
The logo currently in the mod (`Sprites/Pandaborn/Avatars/InkpawsLogo.png`, a 256 px cartoon panda face in a green
disc) does not match the vanilla logos; replacing it is a one-line change (`ship=True`) once the owner agrees.

**New-game art and avatars.** `NewGameFullAvatar` (420 x 560) and the 512 px avatars are painted 3D character
renders in vanilla, not line art. They belong to the character pipeline (render the panda `.timbermesh` in Blender
with the game's lighting), not to this one.
