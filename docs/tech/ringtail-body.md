# The Ringtail body (red panda)

Status: built and tested in game (runs rb-1 to rb-5, pass 3: rb-p3a, rb-p3b), 2026-11-14 (game 1.1.2.8). Art lane. Replaces the prototype's stand-in (the Inkpaw
body scaled to 0.82 with a recoloured coat, `proto/ringtails`, two-peoples.md §17).

## 1. What was built

| Deliverable | Where |
|---|---|
| Adult and kit meshes, every vanilla animation | `E:\PandabornDev\build\characters\out\RingtailAdult.Model.timbermesh`, `RingtailChild.Model.timbermesh` (not in git, like the Inkpaw meshes) |
| 5 adult and 3 kit coats (beaver UV layout) | `mod/PandabornFactions/Materials/Pandaborn/Ringtails/Adult/RingtailAdultCoat1..5.png`, `.../Child/RingtailChildCoat1..3.png` |
| Avatars (adult, kit, contaminated adult, contaminated kit) | `mod/PandabornFactions/Sprites/Pandaborn/Avatars/RingtailAdult.png`, `RingtailChild.png`, `RingtailContaminatedAdult.png`, `RingtailContaminatedChild.png` (+ `.meta.json`) |
| Pipeline (deterministic, rerunnable) | `src/pipeline/characters/` (`make_ringtails.py` runs everything) |
| Sources and rebuild notes | `art/characters/Ringtail/README.md` |
| In-game test mod (dev only) | `proto/ringtail-body/` |

## 2. Method

Same family as the Reskin's giant panda (`..\Timberborn-Pandaborn-Reskin\docs\PIPELINE.md`; its `panda.py`, `geom.py`,
`paint.py` are copied unchanged into `src/pipeline/characters/`). The source is the **vanilla beaver** (dumped from the
owner's install to `E:\PandabornDev\reference\vanilla-characters`), not the panda mesh, because only the beaver has
the tail motion: the giant panda's tail was collapsed into a stub bound to the hips.

1. **Refine** (red-green subdivision): the face and front of the head once, the ears twice, the tail paddle once. The
   back of the head stays at the beaver's resolution (vertex budget, §4).
2. **Sculpt the rest pose** (`redpanda.py`, numbers in `rp_configs.py`): SDF head (round cranium, puffy cheeks, short
   muzzle, jaw); slim body (the body SDF may also pull the beaver's belly *in*, `inward_keep` 0.95, where the giant
   panda only grows outward); modest limb thickening; **ears** as flattened cones with a rounded tip, leaning out and
   slightly back, base widened into the head (`ear_profile`); the mouth cavity capped as in the Reskin.
3. **Tail**: the beaver's flat paddle vertices are remapped onto a round tube: across the paddle → around the tube
   (top face → upper half, bottom face → lower half), along the paddle → along the tube, on a rest curve that leaves the
   hip at 0.10, settles on the ground by mid-length and curls up slightly at the tip. Radius 0.047 → 0.060 → rounded
   cap; length 0.46 (paddle 0.35). The 6 vertices welded to the body stay put; the tube blends out from them.
4. **Transfer every frame**: body vertices by the Reskin's Kabsch neighbourhood transfer. Tail vertices by a **curve
   deformer**: 10 weighted-Kabsch "slices" of the paddle (the first also holds the hips) give knots = where the paddle
   puts our rest centreline; the tube follows a Catmull-Rom curve through the knots, framed by the curve tangent and
   each slice's rotated "up"; the length beyond the paddle rides rigidly on the last knot's frame; the paddle's
   flapping tip slice is ignored (a bushy tail moves more calmly). At rest the deformer is exactly the identity
   (checked: A-pose deviation 0). In the 37 adult / 28 kit animations whose feet stay on the origin, tail heights
   under 1.2 cm are squeezed smoothly onto the ground (the fur flattens instead of sinking in). Two earlier variants were
   rejected after measurement: per-slice linear blend (tail tip moved 2.2× the paddle's tip, i.e. whipped) and a
   damped FK chain (calm, but drove the tail 27 cm into the ground in `scratching`).
5. **Bake the size**: every rest position, every frame offset and every attachment node (position *and* scale) × 0.82
   about the origin. The origin is the contact point in every vanilla animation (ground, seat, bed, water surface,
   zipline cable: checked per animation with `analyze_source.py`), so contacts are kept; attachments (goods, backpack,
   tools, hats, zipline harness, collider) shrink with the body exactly as the prototype's `TransformSpec` did.
   `#Head` keeps the Reskin's adjustment (+1 cm up, ×1.12) for hats.
6. **Normals, tangents and VAT rotations** rebuilt per frame (Reskin code), offsets and quaternions pre-rounded to
   half floats, zlib level 6.
7. **uv1 (tail decal)**: the game samples `_TailDecalDiffuse` with **uv1** (BeaverURP shadergraph: the sample node's UV
   channel is 1, plus an `EdgeUVMask` on uv1), not uv0. Body vertices have uv1 = (0,0) (transparent corner). The tube's
   uv1 maps the decal root→tip along the top of the tail, mirrored underneath like the paddle's two faces (no seam).

### Coats (`paint_ringtail.py`)

Painted on the red panda's rest surface rasterised into the beaver UV layout (Reskin painter): face markings in
head-surface angle space (white muzzle, cheeks and brow ovals, rufous tear tracks, dark eye ring over the game's fixed
eye-socket relief), eyes seated at the socket UV found on the Reskin's red-panda landmarks, dark legs, arms, belly and the
whole front of the torso, russet back, a brighter head; ears white along the outline of the front face with a dark inner
and pale tufts at the base, dark-russet backs with a thin white edge; the tail ringed in its own (t, φ) coordinates
with a darker tip and slightly darker underside, procedural fur strands along it (the beaver texture's high-pass, used
for fur elsewhere, is scales on the paddle and is kept off the tail). AO baked on the red panda in Blender. No writing or
symbols.

| Coat | Variation (as in real red pandas) |
|---|---|
| Adult 1 | Classic: bright rufous, clean white mask, 6 pale rings |
| Adult 2 | Chinese type: deep chestnut, smaller cheek patches, bold tracks, 7 rings, near-black tip |
| Adult 3 | Himalayan type: paler golden coat, big white face, 5 soft rings |
| Adult 4 | Older individual: frosted muzzle, brow and crown, dusky back, 8 fine rings |
| Adult 5 | Rare cinnamon: sandy red with brown (not black) legs |
| Kit 1–3 | Big eyes and blush (the Reskin's cub style), paler and softer; ring count 6–7, mask size and shade vary |

### Avatars (`make_portraits.py` + `bl_portrait.py`)

The Reskin's `portrait2.py` method (the Inkpaw avatars are from it): posed mesh, subdivided, ~60k Cycles hair strands
coloured from the coat, same lights, camera and painted teal plate; split so Blender only needs numpy. No hair on the
eyes and nose. Contaminated = the game's `Contamination_D` overlay at 60 %, same pose (as the Inkpaw ones).

## 3. Measurements

| | Ringtail adult | Inkpaw adult | Ringtail kit | Inkpaw cub |
|---|---|---|---|---|
| Vertices / triangles | 1,931 / 3,192 | 1,716 | 1,790 / 2,966 | 1,608 |
| File size | 108.1 MB | 95.8 MB (+13 %) | 63.5 MB | 56.8 MB (+12 %) |
| Parse time (zlib + protobuf, Python) | 1.0–1.4 s | 1.0–1.2 s | 0.6 s | 0.6 s |
| Height in `idle` (ears included) | 0.478 | 0.570 (×0.84) | 0.328 | 0.390 (×0.84) |
| Width / belly width | 0.307 / 0.271 | 0.380 / 0.338 (×0.80) | 0.182 / 0.162 | 0.229 / 0.199 |
| Length incl. tail | 0.608 | 0.439 | 0.361 | 0.265 |
| Animations / frames | 61 / 3,535 | same | 39 / 2,228 | same |

`qa_ringtail.py` (`E:\PandabornDev\build\characters\out\qa_adult.json`, `qa_child.json`): all format checks pass (node
names, parents, node animations, vertex animation names/frames/fps, finite data, unit quaternions, material names,
zlib header). Motion vs the beaver, per animation: edge stretch at the 99.9th percentile is at most 1.7× (adult) and
1.9× (kit) the beaver's. The adult outliers are all the eyelid blink on the refined 4 mm eyelid edges. The kit's are
the armpits in the arms-over-the-head clips (`exercising`, `swinging`: 6.2 against the giant-panda kit's 3.6–4.4); the
worst frame was rendered (`prev/ex_front.png`, `ex_side.png`) and shows no tear or spike, but it is the weakest joint
of the kit. The far half of the tail is within 1.2 cm of a body vertex for at most 6 % of its vertices (adult,
`teeth_sharpening`) and 17 % (kit, `sleeping`: the tail lies under the lying body). In animations on the ground the tail
never goes below the origin. Remaining flags are expected: in the zipline clips the tail tip moves ~1.8× the paddle tip per frame (longer
tail, same swing; looks like a flowing tail in renders, `prev/zip_side.png`), and in swimming/underwater/zipline clips the
tail is below the origin like the paddle (no ground there).

Vertex budget: the first full build had 2,082 adult vertices (+21 % over the Inkpaw); refining only the front of the
head and a tighter ear region brought it to 1,931 (+13 %). The tail costs ~190 vertices over the paddle and is still an
octagon in cross-section (visible only in close-ups; the game's own models are as faceted).

## 4. In game

Dev mod `proto/ringtail-body` (README there) on top of the Ringtail prototype, new Inkpaws game on Diorama with only
this faction mod (`-OnlyMods JigglyPanda.PandabornFactions`, Reskin off), 4 Ringtail adults and 2 kits spawned by the
prototype's probe. Output in `E:\PandabornDev\build\test\<run>\` (`rb_*.png`, `ringtailBody.json`).

**rb-1** (exit 0; 0 errors from any of our mods; all 10 batch-control tabs opened; population 13 adults, 6 children):
every Ringtail is drawn with `Characters/Pandaborn/RingtailAdult.Model` (1,931 vertices) or `RingtailChild.Model`
(1,790) and a `RingtailAdultCoat*`/`RingtailChildCoat*` coat; Inkpaws keep `InkpawAdult.Model` (1,716). Bounds height:
Ringtail adult 0.464, Inkpaw adult 0.558 (×0.83). The gatherer outfit straps and backpack sit on the body as on an
Inkpaw. Pictures: `rb_lineup1_front/back/side/top.png` and `rb_lineup2_*.png` (studio line-up, Inkpaw adult, Ringtail
adult, Ringtail kit, Inkpaw cub, lifted above the map), `rb_carry_day_d3/d6/d12.png`, `rb_group_day_d3/d6.png`,
`rb_carry_day_steep_d4/d9.png` (game-camera settings, 55° and 70°), plus the prototype's panel shots
`rt_d0_h10_ringtail.png` and `rt_d0_h20_night_ringtail.png` (the real game camera at its default zoom, with the UI).
Two probe faults, fixed for rb-2: the line-up was framed with the vertical field of view (subjects tiny), and shots were
scheduled in run-hours, so the "day" shots fell at dawn (Ringtails resting, none carrying) and the night ones after the
run ended.

**rb-2** (exit 0, 0 errors; final coats except the coat-4 frost tweak): all 8 shots taken. `rb_lineup1_*` and
`rb_lineup2_*` frame the four side by side: the Ringtail adult (cinnamon coat 5 in both) is clearly a red panda next to
the Inkpaw (pointed white-rimmed ears, white cheeks and brows, tear tracks, dark legs and chest, ringed tail), and the kit
next to the Inkpaw cub. `rb_carry_day_d6.png` is the cleanest game-camera view: a Ringtail walking on a path by day, an
Inkpaw on the porch behind. Faults: no Ringtail carried goods in any window (the prototype's courier loft is not
connected on this layout, two-peoples.md §17.3), `rb_group_day_*` caught the Ringtail still tinted by the prototype probe's
selection, and both night views put the Ringtail behind a building.

**rb-3** (exit 0, 0 errors; final coats). Because no Ringtail carries anything on this test layout, the probe now
(dev only) hands a walking, unoccluded Ringtail one good for the picture and takes it back ~1 s later, and clears the
selection first. Results: `rb_carry_day_d3.png` (two Ringtails at the farm fence, one with a log on its gatherer's
back-frame, ringed tails clear), `rb_carry_day_steep_d4.png` (70° from above: a Ringtail carrying poles on its back,
the ringed tail the clearest cue), `rb_group_day_d3.png` (Ringtail with back-frame, a Ringtail kit, an Inkpaw adult and an
Inkpaw cub on one path: the size and colour difference reads at once), `rb_carry_day_d12.png` (a normal play zoom:
Ringtails are the orange ones with striped tails among white Inkpaws), `rb_lineup1_back.png` / `rb_lineup2_front.png`
(studio). The night views still showed the building in front of the Ringtail (fixed for rb-4: the probe now tries
eight camera headings and picks a Ringtail that can be seen).

**rb-4** (exit 0, 0 errors; dusk and night, request `proto/ringtail-body/test/night.request.json`): at night the
Ringtails were working and carrying for real (Berries ×3 at the Forager's Nest; nothing forced). `rb_carry_night_d3.png`
and `_d6.png`: a Ringtail with a berry crate in its arms by a bush, ringed tail behind it, in the game's night light;
`rb_group_night_d3.png`: the carrying Ringtail beside an Inkpaw adult (hammer outfit), a Ringtail kit and an Inkpaw cub;
`rb_carry_dusk_d3.png`: a Ringtail at dusk with a log on its back-frame (forced, dev only).

Verdict from the pictures: at the game's camera a Ringtail reads as a red panda without being told: orange head with
white cheeks and pointed white-rimmed ears, dark legs and chest, and above all the long striped tail, which is visible
from every heading in the walking and carrying poses. It is clearly smaller and slimmer than an Inkpaw. Nothing looked
broken in any in-game picture (no detached tail, no spikes, outfits and carried goods in place).

Offline renders used for the motion review (Blender, `E:\PandabornDev\build\characters\prev\`): `zip_side.png`
(zipline frames, Ringtail vs beaver), `kitclap.png` (kit clapping and flying frames), `kitA_side/back.png`,
`sheetA_*.png` (idle, walk, sitting, sleeping at 5 frames each), `ex_front/side.png` (kit armpit worst frame),
`all8_front/back.png` (all coats), `outfit_front/back.png` (hauler and builder overlays, Folktails tail decal on the tail),
`gamecam55.png` (a mixed group at ~40 px per character), and the avatars sheet
`E:\PandabornDev\build\characters\portraits\sheet.png`.

## 5. Adopting it (what the catalogue and code lanes must change)

Nothing here is wired into the faction yet; the art lane did not edit `catalogue/`, `src/code/` or `tools/`.

1. **Build** (`tools/pandaborn.ps1`, the `$meshes` table next to the Inkpaw meshes): add
   `'Characters\Pandaborn\RingtailAdult.Model.timbermesh' = 'E:\PandabornDev\build\characters\out\RingtailAdult.Model.timbermesh'`
   and the same for `RingtailChild`. The files stay out of git (`*.timbermesh` is ignored outside `Buildings/`), like
   the Inkpaw meshes. Rebuild them with `src/pipeline/characters/make_ringtails.py --steps meshes,qa`.
2. **Ringtail templates** (today `proto/ringtails/tools/derive.py`): `Children.Model_Preserved.TimbermeshSpec.Model` =
   `Characters/Pandaborn/RingtailAdult.Model` / `Characters/Pandaborn/RingtailChild.Model`; **drop the `TransformSpec`
   scale** (0.82 is baked in; leaving it would make Ringtails 0.67 of an Inkpaw). Keep everything else: node names,
   the attachment list, the collider prefab and the animator states are unchanged.
3. **Coats** (the Ringtail coat list, `PandabornRingtailSpec.Textures` in the prototype):
   `Materials/Pandaborn/Ringtails/Adult/RingtailAdultCoat1` … `RingtailAdultCoat5` and
   `Materials/Pandaborn/Ringtails/Child/RingtailChildCoat1` … `RingtailChildCoat3`. They replace the prototype's
   `RingtailAdult1..5`/`RingtailChild1..3`, which were the Reskin's Iron Teeth coats painted for the giant-panda body
   (different names, so no clash while both exist).
4. **Avatars** for the Ringtail badge (two-peoples.md §17.5, own `IEntityBadge`):
   `Sprites/Pandaborn/Avatars/RingtailAdult`, `RingtailChild`, `RingtailContaminatedAdult`, `RingtailContaminatedChild`.
5. **Outfits** keep working (`WorkerOutfitSpec` for `PandabornRingtail`; seen in game, §4). The **tail decal** (uv1) now
   lands along the top of the round tail; if the Inkpaws keep copying the Folktails decals, consider a ringtail-specific
   decal set or none for Ringtails (the gold emblems sit on top of the rings).
6. `MovementAnimatorSpec.AnimationSpeedScale` ×1.25 (prototype) suits the shorter legs; keep it.

## 6. Known weak spots (honest)

* **Tail cross-section is an octagon** (the paddle's topology, refined once). Invisible at game distance, visible in
  close-ups and the studio line-up. A rebuilt tube with 16 sides would cost ~+300 vertices.
* **Sitting/sleeping/scratching**: the beaver puts its paddle forward between its feet or under its back. The tail
  follows: when sitting, a red panda's tail curls up in front of its feet (reads fine, even cute); when lying on its
  back the tail is under the body and mostly hidden. Not a red panda's natural curl-up sleep; that would need new
  animations.
* **Reach**: everything is 0.82 of the beaver, including arm reach, so in animations that touch the world (cutting,
  building, pushing) the hands stop ~5 cm short, exactly as with the prototype's `TransformSpec` scale.
* **Zipline**: the longer tail swings ~1.8× as far as the beaver's paddle per frame. It looks like a flowing tail in
  renders; worth a look in game.
* **Kit armpits** stretch more than the giant-panda kit's in `exercising`/`swinging` (§3). No visible tear.
* **Eyes** are painted on the beaver's fixed eye-socket relief (unavoidable with the fixed normal map), so the
  eye position is the beaver's; the shorter red panda muzzle makes the face slightly flatter than a real red panda's.
* **Back of the head** stays at the beaver's resolution (budget), so the crown silhouette is a little angular up close.
* **Size**: +13 % (adult) and +12 % (kit) over the Inkpaw meshes, i.e. about +19 MB in the download.

## 7. Pass 2 (coordinator review): tail, warmer coat, outfits, attachments, tail decals

### 7.1 Tail: 16 sides, bushier, round tip

`RedPandaBuilder.rebuild_tail` replaces the paddle-derived tube with a clean one: 16 sides x 14 rings (kit 12) and a
pole at the tip, rings denser toward the tip. The beaver's tail UV islands are kept (top/bottom, plus left/right on
the adult): each new vertex takes uv0, tangent sign, colour and parentage by barycentric lookup in its island's
(t, angle) parameter space, so the coat painter, the fixed AO/normal maps and the bind all still work; the vertices
welded to the body (the root hole) are kept and zipped to the first ring per island. Profile: radius 0.046 at the
root swelling to 0.070 in the last third (kit 0.026 to 0.050), then a hemispherical tip (`tail_radius`, `swell`,
`t_max`, `t_cap` in `rp_configs.py`). The path-following deformer is unchanged. Cost: adult 1,951 vertices (was
1,931; 109.2 MB), kit 1,778 (was 1,790; 63.0 MB); the clean tube needs fewer vertices than the refined paddle did.

### 7.2 Warmer adult coat

Adults: the dark parts are blackish only on the legs and belly and warm to deep chestnut on the chest and forelegs
(`dark_warm` per coat, blended by height), and the dark of the forelegs stops lower (`arm_reach` 0.055, was 0.075), so
the russet wraps the shoulders and upper arms. Kits unchanged.

### 7.3 Outfits

How they work (game 1.1.2.8): a workplace names an outfit (`WorkplaceWorkerOutfitSpec.WorkerOutfit`); the worker gets
the `WorkerOutfitSpec` with that `Id`, its own `WorkerType` and the faction's `FactionId` (a duplicate (Id, WorkerType)
per faction throws). `DiffuseTexture` is alpha-blended over the coat in the beaver UV layout; `NormalTexture` is
sampled as a normal map (vanilla packing R=255, G=B=y, A=x; a loose PNG needs `{"isNormalMap": true}` to load linear).
`Attachments` lists `TemplateAttachmentsSpec` ids on the character template to show (hats, hammer, gatherer pack).

**(a) Ringtail outfits** (`src/pipeline/characters/paint_outfits.py`, painted on the Ringtail's own surface; textures
committed under `mod/PandabornFactions/Materials/Pandaborn/Outfits/Ringtail/`, each `_N` with its `.meta.json`):

| Outfit Id (suggested; `WorkerType` `PandabornRingtail`, `FactionId` `Inkpaws`) | Workplace | Diffuse / Normal texture | Attachments | Look |
|---|---|---|---|---|
| `PandabornNightBuilder` | Night Builders' Post | `Materials/Pandaborn/Outfits/Ringtail/RingtailNightBuilder_D` / `_N` | `HammerBack.Beaver` (vanilla) | indigo head-wrap tied at the back, leather tool belt |
| `PandabornNightCourier` | Night Courier Post | `.../RingtailNightCourier_D` / `_N` | none (goods ride on the vanilla `Backpack`) | woven back-basket straps, chest strap, rope belt |
| `PandabornNightForager` | Night Forager's Post | `.../RingtailNightForager_D` / `_N` | `GathererBackpack` (vanilla) | green head-wrap, leather satchel strap, cloth waist band |
| `PandabornStargazer` | Star Tower | `.../RingtailStargazer_D` / `_N` | none | night-blue shawl over shoulders and back, pale trim |
| `PandabornOpera` | Opera Stage | `.../RingtailOpera_D` / `_N` | none | crimson sash, gold collar, black silk belt |

Offline: `E:\PandabornDev\build\characters\prev\outf_front.png`, `outf_back.png`. In game the prototype's Ringtail
`Hauler` and `Gatherer` outfits were pointed at the courier and forager textures by a merge in the test mod (§7.6).
The other three need their workplaces (Ringtails lane). Weak spots: the normal maps are a mild emboss in UV axes
(straps read raised, not modelled); head-wraps are painted, so they sit below the ears.

**(b) The 12 Inkpaw outfits on the panda body** (7 `Beaver` outfits copied from Folktails plus 5 `Bot` ones; bots are
not on the panda body), rendered on the Inkpaw body with every overlay and attachment hung on its node
(`prev/ink_front.png`, `ink_back.png`, `hats_front.png`). The three strap overlays (`WorkerHammerStrings`,
`HaulerBackpackStrings`, `LumberjackStrings`) follow the panda's chest and back because the UV layout is the beaver's;
the farmer, forester and scavenger hats sit on the head (the Reskin's `#Head` +1 cm and x1.15 suit the giant panda);
hammer and gatherer pack sit on the back. **No landing is bad enough to need a replacement overlay.** Two design
notes instead: the Folktails farmer hat is a wide-brimmed straw hat, not the conical paddy hat the art direction asks
for (new geometry, below); and on the **Ringtail** the vanilla hats collide with the tall ears (the scavenger hat
sits low over the brow), so Ringtails get head-wraps (overlays), not hats.

**(c) Hats and baskets as real geometry.** Per-outfit attachments are already data: `WorkerOutfitSpec.Attachments`
names ids in the character's `TemplateAttachmentsSpec.Attachments` (`AttachmentId`, `Prefab`, `Parent` node such as
`#Head`/`#Backpack`, `Position`/`Rotation`/`Scale`, `CreateInstantly`), shown and hidden by
`WorkerOutfitAttachmentVisualizer`, per animation by `WorkerOutfitAnimationAttachmentVisibilitySpec`. The blocker is
the asset: `Prefab` is an `AssetRef<GameObject>`, and a loose `.timbermesh` in a mod loads as `BinaryData`
(`ModTimbermeshConverter`), not a GameObject. A mod **AssetBundle** can supply a GameObject
(`ModAssetBundleProvider.TryLoad<T>` serves any asset type; the look lane already builds bundles,
`tools/build_look.ps1`). So:
* **Data-only route (recommended): a small attachments bundle.** Unity prefabs
  `Characters/Pandaborn/Attachments/ConicalHat` and `.../BackBasket` (mesh + one material on a copy of the game's
  shader, as the look bundle's materials are), shipped as `AssetBundles/pandabornattachments_win` / `_mac`; then pure
  blueprint entries: `TemplateAttachmentsSpec.Attachments#append` on `InkpawAdult.Inkpaws` / `RingtailAdult.Inkpaws`
  with `{"AttachmentId": "PandabornConicalHat", "Prefab": "Characters/Pandaborn/Attachments/ConicalHat", "Parent": "#Head"}`
  and `{"AttachmentId": "PandabornBackBasket", "Prefab": "Characters/Pandaborn/Attachments/BackBasket", "Parent": "#Backpack"}`,
  and the outfit's `"Attachments": ["PandabornConicalHat"]`. The basket must hide while goods ride on `#Backpack` (or
  become the courier's backpack); `WorkerOutfitAnimationAttachmentVisibilitySpec` hides per animation.
  **Proven in game (rb-5, §7.6):** `src/unity/PandabornAttachments/Editor/PandabornAttachmentsBuilder.cs` builds a
  procedural conical straw hat and an open back-basket as prefabs (URP Lit material, two-sided) into
  `pandabornattachments_win` (58 KB; project `E:\PandabornDev\unity\PandabornAttachments`, made like the look
  project; bundle in `E:\PandabornDev\build\characters\attachments`). With only blueprint merges in the test mod
  (`TemplateAttachmentsSpec.Attachments#append` on both adult templates, `"Attachments": ["GathererBackpack",
  "PandabornConicalHat"]` on the Inkpaw `Gatherer` outfit), an Inkpaw gatherer wore the hat in game
  (`E:\PandabornDev\build\test\rb-5\reload\rb_reload_lineup_front.png`). The geometry is placeholder (a plain cone and
  a plain cylinder, flat straw colour); a modelled hat and basket and a Mac bundle are still to do. The back-basket on
  the Ringtail forager was loaded but no forager was in frame in any picture, so it is unverified.
* **Code route (only if bundles are unwanted):** a small component that, on an outfit change, instantiates a mesh
  decoded from a loose `.timbermesh` under `#Head`/`#Backpack`. More code and risk than a bundle; not recommended.

### 7.4 Tail decals

Decals are per character but chosen from the **faction's** `Tails` set at a tail-painting building
(`TailDecalApplier`, need `Detailer`), so Ringtails cannot have their own set by data. Decision: **one faction set of
plain ribbons and bands** that suits both peoples (the faction needs a `Tails` set anyway). On the Ringtail's round
tail uv1 runs root to tip along the top and is mirrored underneath, so a band across the decal becomes a ribbon tied
around the tail; on the Inkpaw stub it is a stripe. Textures (`src/pipeline/characters/paint_tail_decals.py`,
committed, 1024x1024 RGBA, no meta file needed):

| Requested `DecalSpec` (`FactionId` `Inkpaws`, `Category` `Tails`) | `Texture` |
|---|---|
| crimson ribbon with gold edges | `Materials/Pandaborn/Decals/Tails/PandabornTailRibbon` |
| two indigo bands | `Materials/Pandaborn/Decals/Tails/PandabornTailTwinBands` |
| cream "dipped" tip | `Materials/Pandaborn/Decals/Tails/PandabornTailTipCream` |
| braided cord with three wooden beads | `Materials/Pandaborn/Decals/Tails/PandabornTailBeadCord` |

They would replace the copied Folktails emblems (a gold emblem on top of the rings reads as a sticker). Offline:
`prev/decals.png`. Not seen in game (needs a tail-painting building and a visit).

### 7.5 With the Reskin enabled (what it does to both peoples)

Read from the Reskin source (`..\Timberborn-Pandaborn-Reskin\src\scripts\PandaColonistsFur.cs`) and confirmed in
rb-5 (mods loaded: Pandaborn (Reskin) 7.0.0, Pandaborn - Factions, the Ringtail prototype, this test mod, the harness):
* **Inkpaws lose their own coats and avatars.** `PandabornFactionSkins` rewrites every non-vanilla `FactionSpec`'s
  `Textures`, `ChildTextures` and avatars to the Folktails ones (giant panda by default), so Inkpaws wear the Reskin's
  `BeaverAdultN.Folktails` / `BeaverChildN.Folktails` coats (rb-5: `BeaverAdult4.Folktails`, `BeaverChild2.Folktails`)
  instead of `InkpawAdultN`. They still look like giant pandas, but the Inkpaws' own coat variants and avatars are gone.
* **Ringtails keep their coats** (`RingtailAdultCoatN`, `RingtailChildCoatN` in every sample), because the Ringtail coat
  is set later, from `PandabornRingtailSpec`, not from the faction. Their avatar is not touched either (badge code).
* **Fur shells on everyone.** `PandaFurAttacher` decorates every `BeaverSpec` character, Ringtails included, and builds
  shells from that character's own mesh with the giant panda's UV fur mask. Up close the Ringtail looks furry and the
  tail (the paddle's UV region, "longest fur" in the mask) bushier. One artefact: from above, a pale patch with a blue
  rim shows on the Ringtail's crown in the game-camera shots with the Reskin on (`rb-5\reload\rb_reload_game_d3.png`,
  `rb-5\rb_carry_night_d3.png`). **Traced in pass 3 (§8.1): it is not on the crown but the front face of the far ear**,
  seen from above: the pass-2 coat painted it pale (white rim and tufts), the Reskin's shells (the giant-panda mask gives the
  ear region longer fur than the rest of the head: 0.49 against 0.37 of full length, sampled on the Ringtail's UVs) thickened it into a fuzzy pale disc, and at night the moonlight turns it blue.
* **Meshes untouched.** The Reskin overrides only `Characters/Beaver/...`; Ringtails and Inkpaws use
  `Characters/Pandaborn/...` (1,951 and 1,716 vertices in every sample).
* Suggested Reskin update (for the coordinator): skip `PandabornFactionSkins` for the `Inkpaws` faction (it already has
  panda coats and avatars), and either skip fur on characters whose mesh is not one of the Reskin's or ship a Ringtail
  fur mask.

### 7.6 The combined game run (rb-5)

`tools/run_game_test.ps1 -NoBuild -Faction Inkpaws -InGameDays 1.0 -Speed 3 -ExtraMods <ringtails>,<ringtail-body>
-OnlyMods JigglyPanda.PandabornFactions,JigglyPanda.Pandaborn -RequestJson proto\ringtail-body\test\combined.request.json
-SaveAndReload -ReloadSeconds 200` (output `E:\PandabornDev\build\test\rb-5\`, reload in `rb-5\reload\`). Exit 0,
both launches PASS, 0 errors and 0 log issues from any mod, all batch-control tabs opened, mod flags restored.
* **Save and reload with the new body:** all 4 Ringtail adults and 2 kits came back as `RingtailAdult/RingtailChild`
  on `RingtailAdult.Model` (1,951 v) / `RingtailChild.Model` (1,778 v) with Ringtail coats (re-rolled on load, as every
  coat is). `rb-5\reload\rb_reload_lineup_front.png`, `rb_reload_group_d3.png`, `rb_reload_game_d3.png` (carrying a log).
* **Reskin alongside:** §7.5.
* **New outfits:** the Ringtail builder, courier and gatherer outfits were pointed at the NightBuilder, NightCourier
  and NightForager overlays; no texture or normal-map error was logged, and the head-wrap reads as a ring from the side
  (`rb-5\rb_lineup1_front.png`). The per-outfit hat from the attachments bundle: §7.3(c).
* **Zipline:** not exercised in game (no zipline in the test colony); offline the bushy tail swings cleanly
  (`E:\PandabornDev\build\characters\prev\zip_side_pass2.png`).
* Other pictures: `rb-5\rb_lineup1_front/back.png` (Reskin fur on both peoples), `rb_group_day_d3.png` (Ringtail with
  poles on its back-frame, a kit, two Inkpaws, two cubs), `rb_carry_night_d3.png` (night, with the crown artefact).

## 8. Pass 3: the Reskin alongside, hats and baskets, tail UVs, the Wooden Ox

### 8.1 Playing with the Reskin enabled

> **For the owner: the Reskin decision in short.**
> * **Today, with both mods** (released Reskin 7.0.0 + Pandaborn - Factions, run `rb-p3a`): every colonist looks
>   right and nothing breaks, but the Reskin treats the Inkpaws as an unknown modded faction. Inkpaw adults and cubs
>   wear the Reskin's **Folktails** panda coats (`BeaverAdultN.Folktails`; they happen to be byte-identical to ours) and
>   the faction's **portraits are replaced** by the Reskin's Folktails ones. Ringtails keep their own red-panda coats and
>   portraits, and everyone gets the Reskin's shell fur, but the Ringtails' fur follows the **giant panda's** fur
>   pattern (longer on the ears than the head, panda eye/nose holes). The old pale "crown patch" on Ringtails is gone
>   after our coat change.
> * **What the `factions-compat` branch changes** (one file, `src/scripts/PandaColonistsFur.cs`, +30/-1 lines, one
>   local commit `fc8e25d`, not pushed): (1) the Inkpaws keep their own coats and portraits (a player can still force
>   a look with `faction.inkpaws = giant` in `PandaFurSettings.txt`); (2) any body may ship its own fur mask next to its
>   mesh (`<model>.FurMask`) or opt out of fur (`<model>.NoFur`); the Ringtails ship one. Vanilla factions are untouched.
> * **Proven** in run `rb-p3b` (compat dev copy, released Reskin off): Inkpaws wear `InkpawAdultN`/`InkpawChildN` with fur,
>   Ringtails use `RingtailAdult.Model.FurMask`, and a Folktails game in the same launch loads the Reskin's panda bodies,
>   coats, fur masks and the vanilla bot exactly as the released Reskin does (0 errors).
> * **Build and test it:** check out `factions-compat` in `..\Timberborn-Pandaborn-Reskin`; compile with the response
>   file `E:\PandabornDev\build\reskin-compat-dll\build.rsp` (`dotnet "C:/Program Files/dotnet/sdk/9.0.203/Roslyn/bincore/csc.dll" @build.rsp`)
>   or the Reskin's own `tools/build_dlls.sh`; the dev copy for tests is `E:\PandabornDev\build\reskin-compat\PandabornReskinCompat`
>   (`tools\run_game_test.ps1 ... -OnlyMods JigglyPanda.PandabornFactions -ExtraMods <that folder>`). Releasing it is
>   only: put the new `PandaColonistsFurV6.dll` in the Reskin's `Scripts` folder and publish a Reskin update.

**What the Reskin does** (`..\Timberborn-Pandaborn-Reskin\src\scripts\PandaColonistsFur.cs`, namespace
`PandaColonistsV6`; the V5 DLL and `PandaReskin.dll` are 3 KB stubs):
* `PandabornFactionSkins` (on `FactionService` load) rewrites every non-vanilla `FactionSpec`'s `Textures`,
  `ChildTextures`, `Avatar`, `ChildAvatar`, `ContaminatedAdultAvatar`, `ContaminatedChildAvatar` and
  `NewGameFullAvatar` to the look `FactionLooks.For(id)` picks: `faction.<id>` in `PandaFurSettings.txt`, else
  `otherfactions` (default `giant`). The Inkpaw coats are byte-identical to the Reskin's Folktails coats (same md5), so
  in practice only the **avatars** visibly change; the Inkpaws' own coat list is still replaced.
* `PandaFurAttacher` decorates **every** `BeaverSpec` character (Ringtails included) with `PandaFurRenderer`: shells and
  silhouette fins built from that character's own mesh, coloured every frame from the character's own `_BaseMap`
  (so Ringtails get red-panda-coloured fur), with fur **length** from the bundle material's `_FurMask` (R = length,
  G = AO) painted for the **giant panda's** UV layout. A Ringtail keeps the beaver UV islands, so the mask lands, but
  its distribution is the panda's: ear region longer than the head (0.49 vs 0.37), eye/nose holes at the panda's
  landmarks. That is the "giant-panda fur on Ringtails".
* The crown patch: §7.5 (the far ear's front face; pale in the pass-2 coat, thickened by the shells, blue at night).

**(b) Fix from our side, no Reskin change.** There is no data-only way to keep the Reskin from rewriting a faction it
does not know (it reads `FactionSpec` after load and owns the decision), and we must not reference its DLL. What we
did and can do:
1. The Ringtail ear front is no longer pale (coat change in `paint_ringtail.py`: the white rim narrower, `ear_edge`
   0.78 -> 0.84; the pale tufts weaker, `ear_tuft` 0.5 -> 0.28, 0.8 -> 0.45 on adult coat 3 and kit coat 3), so the
   shells thicken a brown-grey ear, not a white disc (`E:\PandabornDev\build\characters\prev\pass3_top.png`).
2. We ship `Characters/Pandaborn/RingtailAdult.Model.FurMask.png` / `RingtailChild.Model.FurMask.png`
   (`src/pipeline/characters/make_furmask.py`, linear, R = Ringtail fur length: none on eyes, nose, pads and teeth,
   short face, short velvet ears, the longest fur on the tail; G = the Ringtail AO). Inert today; the compat Reskin uses
   them (c).
3. Proposal for the code lane (no Reskin reference, works whatever the Reskin does): an Inkpaw coat component like
   `RingtailCoat` (pick the coat from an Inkpaw-only spec after `BeaverTextureSetter`) and the Inkpaw avatar through
   the same `IEntityBadge` the Ringtails use. Then the Reskin's faction rewrite has nothing left to change.

**(c) The proper fix in the Reskin** (branch `factions-compat` in `..\Timberborn-Pandaborn-Reskin`, local only, one
commit `fc8e25d` on top of `main` `b6cc714`; not pushed; `main`, the installed Reskin and the Workshop item untouched).
`src/scripts/PandaColonistsFur.cs`, +30/-1:
* `FactionLooks.OwnPandaFactions = { "Inkpaws" }`: `For(id)` returns `Own` for them (after a player's explicit
  `faction.<id>` setting, before `otherfactions`), so `PandabornFactionSkins` writes the faction's original specs back:
  Inkpaws keep their coats and avatars. Fur still applies and takes its colour from the Inkpaw coat.
* `PandaFurAttacher.PostInitializeEntity`: reads the character's model asset (`TimbermeshDescription.ModelName`); if an
  asset `<model>.NoFur` exists the character gets no fur; if `<model>.FurMask` (a Texture2D) exists, the fur material is
  a cached copy of the adult/child template with that `_FurMask` (`MaskedTemplate`, one per template and mask). The
  Reskin's own and vanilla bodies have neither file, so they are unchanged (two `LoadSafe` misses per character spawn).
* Build: `csc` (Roslyn from SDK 9.0.203) against `Timberborn_Data\Managed`, response file
  `E:\PandabornDev\build\reskin-compat-dll\build.rsp` -> `E:\PandabornDev\build\reskin-compat-dll\PandaColonistsFurV6.dll`
  (24,576 bytes; the released one is 23,552).
* Dev copy for tests: `E:\PandabornDev\build\reskin-compat\PandabornReskinCompat` = the installed Reskin's
  `AssetBundles`, `Characters`, `Materials`, `Scripts`, `Sprites`, `PandaFurSettings.txt` with the new V6 DLL, manifest
  Id `JigglyPanda.PandabornReskinCompatDev`, and **without** `Scripts\PandabornSettings.bin` (its Mod Settings page is
  keyed to `JigglyPanda.Pandaborn`). Run with `-OnlyMods JigglyPanda.PandabornFactions` (the released Reskin off) and
  `-ExtraMods` this folder: the bundles `pandacolonistsv5_win`/`v6_win` then load once, from the copy only (two enabled
  copies would crash on the bundles, CLAUDE.md), and the assembly name `PandaColonistsFurV6` loads once.

### 8.2 The conical hat and the back-basket (real geometry)

`src/pipeline/characters/make_attachments.py` models and paints both (deterministic, numpy); the Unity builder
`src/unity/PandabornAttachments/Editor/PandabornAttachmentsBuilder.cs` turns them into prefabs; one command builds a
bundle: `powershell -File src\unity\PandabornAttachments\build.ps1` (`_win`, project
`E:\PandabornDev\unity\PandabornAttachments`) and `... build.ps1 -Mac` (`_mac`, its own project
`E:\PandabornDev\unity\PandabornAttachments-mac`, editor from `tools\unity_editor.ps1` with Mac Build Support, as
`tools\build_look.ps1 -Mac` does). Output `E:\PandabornDev\build\characters\attachments\pandabornattachments_win`
(2.15 MB) and `pandabornattachments_mac` (2.22 MB, built for StandaloneOSX); both hold
`Characters/Pandaborn/Attachments/ConicalHat` and `.../BackBasket` (checked with UnityPy).

| Prefab | Geometry | Materials (URP Lit, 1024 px colour + normal map) |
|---|---|---|
| `ConicalHat` (#Head frame, y up) | nón lá: slightly convex cone, 15 cm brim radius, 8 cm high, sitting 4.6 cm below the node; the brim wavy and ragged (noise in radius and droop) with a cut-out fringe of frayed leaf ends; a bamboo hoop under the rim, a head ring inside, a knot at the apex; both faces of the shell modelled (no two-sided shader). 1,912 vertices | `PandabornHatLeaf` (palm-leaf strips, stitched concentric binding rings, weathering; alpha cut-out for the fringe), `PandabornCord` |
| `BackBasket` (#Backpack frame, +y away from the back, -z up the spine) | bei lou: rounded-square, tapered (wider at the top), 22 cm tall, open top with a rolled rim, four corner ribs, a woven base, two shoulder straps and two waist straps leading into the body. 1,166 vertices | `PandabornWeave` (over-under split-bamboo weave), `PandabornCord`, `PandabornStrap` (plaited hemp) |

Offline on both peoples: `E:\PandabornDev\build\characters\prev\attach\attach_front.png`, `attach_back.png`,
`attach_side.png` (Inkpaw with the hat, Ringtail and Inkpaw with the basket, in idle, walk, carrying and cutting).
The Ringtail keeps its painted head-wraps (no hat: the tall ears).


### 8.3 In game: runs rb-p3a and rb-p3b (2026-11-14, hidden desktop)

Both PASS, 0 errors from any mod, all batch-control tabs opened, mod flags restored. Per character the probe wrote
template, model asset, vertex count, coat, shown attachments and fur components with the fur mask in use
(`ringtailBody.json` in each folder). T = `E:\PandabornDev\build\test`.

* **rb-p3a**: mods `JigglyPanda.Pandaborn` (released Reskin 7.0.0), `PandabornFactions`, `PandabornProtoRingtails`,
  `PandabornProtoRingtailBody`, harness. Inkpaws, Diorama, 1 in-game day, 3 bots spawned, then save and reload. 25
  characters (9 Inkpaw adults, 4 cubs, 6 Ringtail adults, 3 kits, 3 Wooden Oxen) before and after the reload.
* **rb-p3b**: the compat dev copy `JigglyPanda.PandabornReskinCompatDev` instead of the released Reskin, Inkpaws 1 day
  with 2 bots, then (same launch) a Folktails game with 2 bots (`rb-p3b\folktails\`).

**With the released Reskin** (rb-p3a):
* **Crown patch: gone.** Top-down day and night line-ups and game-camera night shots show the Ringtail's ears as
  brown-grey with a thin pale rim, no pale or blue disc (`T\rb-p3a\rb_people_day_top.png`, `rb_people_night_top.png`,
  `rb_ringtail_night_d3.png`).
* **Coats:** Inkpaw adults and cubs wear the Reskin's `BeaverAdult1/3/4/5.Folktails` and `BeaverChild2.Folktails`
  (the faction coat list is rewritten); they look like our giant pandas because the files are identical. Ringtails
  wear `RingtailAdultCoat1/2/3` and `RingtailChildCoat2/3`.
* **Portraits:** not photographed by the probe. From the code, the Inkpaw portraits are replaced by the Reskin's
  Folktails ones and the Ringtail portraits (badge code) are untouched.
* **Fur:** every Inkpaw and Ringtail has `PandaFurRenderer` with the Reskin's masks (`PandaFurAdult [mask
  FurMaskAdult]`, `PandaFurChild [mask FurMaskChild]`), i.e. the giant-panda pattern on Ringtails; bots have none.
  It reads as soft fur on both peoples (`rb_people_day_front.png`, `rb_gear_day_front.png`).

**With the compat build** (rb-p3b):
* **Inkpaws keep their own coats, with fur:** `InkpawAdult2`/`InkpawAdult4`, `InkpawChild1` in every sample, each with
  `PandaFurRenderer` (`T\rb-p3b\rb_people_day_front.png`, `rb_inkpaw_day_d2.5.png`, `rb_people_night_front.png`).
  Portraits: the code path now writes back the faction's own avatars (`Own`); not photographed.
* **Ringtails take the Ringtail mask:** `PandaFurAdult+RingtailAdult.Model.FurMask [mask RingtailAdult.Model.FurMask]`
  and `PandaFurChild+RingtailChild.Model.FurMask` on every Ringtail adult and kit (`rb_people_day_top.png`,
  `rb_ringtail_day_d2.5.png`, `rb_ringtail_night_d2.5.png`, `rb_family_night_d3.png`).
* **Folktails game as with the released Reskin:** `BeaverAdult` / `BeaverChild` on the Reskin's `Characters/Beaver/...`
  meshes (1,716 / 1,608 vertices), Reskin coats (`BeaverAdult1/5.Folktails`, `BeaverChild3.Folktails`, a brown
  Qinling panda among them), the Reskin's own masks (`FurMaskAdult`/`FurMaskChild`), vanilla `Bot.Folktails` (1,655
  vertices, no fur) (`T\rb-p3b\folktails\rb_ft_people_front.png`, `rb_ft_beaver_d2.5.png`, `rb_ft_bot_d2.5.png`). That
  is what the released Reskin does (same code path: the Folktails meshes have no `.FurMask`/`.NoFur`); no
  released-Reskin Folktails game was run side by side in this pass.

**Hats and baskets** (rb-p3a, both peoples in frame):
* An Inkpaw farmer wears `ConicalHat(Clone)`; an Inkpaw gatherer and the Ringtail foragers wear `BackBasket(Clone)`
  (`T\rb-p3a\rb_gear_day_front.png`, `_back.png`, `_side.png`, `_top.png`; groups with the ox and a cub:
  `rb_gear_group_day_d3.png`, `rb_gear_group_night_d3.png`). Ringtails keep their head-wraps. The hat sits on the
  panda's crown with the ears under the brim; the basket sits between the shoulders.
* **Survives save and reload:** `T\rb-p3a\reload\rb_reload_gear_front.png` (hat, both baskets, kit, ox).
* **Clash with goods on the back: not seen.** Gatherers and foragers carry their yield as a crate in their hands
  (`Berries x3`; `rb_gear_day_front.png`, `rb_ringtail_night_d3.png`, `rb-p3b\rb_ringtail_night_d2.5.png`): the
  basket stays on the back, the crate in front, no overlap. No basket wearer carried goods on its back in either run
  (the Ringtail with logs on its back in `rb_ringtail_day_d3.png` had no basket outfit at that moment). If a gatherer
  ever carries logs on its back, the log frame and the basket share `#Backpack` and would overlap; the fix is a
  `WorkerOutfitAnimationAttachmentVisibilitySpec` entry hiding `PandabornBackBasket` in the `walk_log` animations.

### 8.4 Tail UV folds

Fixed: tail UVs are a least-squares fit per UV island with clamped island ranges (`redpanda.py`); 0 folded tail
triangles for adult and kit; QA passes. Clean rings offline (`E:\PandabornDev\build\characters\prev\pass3_tail_side.png`,
`pass3_tail_back.png`) and in game (`T\rb-p3a\rb_gear_day_back.png`, `rb-p3b\rb_people_day_front.png`). The faction
build already ships these meshes (same positions, UVs and frames as this rebuild).

### 8.5 The Wooden Ox

`src/pipeline/characters/build_ox.py` (parts split by `ox_analyze.py`) reshapes the vanilla Folktails bot into an
upright ox-headed automaton: broader head with a muzzle block, nostrils and a nose ring, pale-tipped horns, ear flaps,
goggle eyes on the sides, the beaver teeth flattened into a smile plate, the tail a thin rod with a tuft, blunt hooves.
Every node, all 48 animations (1,921 frames), the material `Bot.Folktails` and every UV island are kept; each vanilla
part keeps its exact motion (blinking lids too) and the new parts ride on the head. Mesh
`E:\PandabornDev\build\characters\out\WoodenOx.Model.timbermesh` (2,012 vertices, vanilla 1,655; 39.6 MB). The biped
rig stays: an ox-headed automaton, not the four-legged ox of the icon (accepted).

In game (rb-p3a):
* **Looks right** at studio and game distance, day and night (`T\rb-p3a\rb_gear_day_front.png`, `rb_people_day_top.png`,
  `rb_ox_day_d2.5.png`, `rb_ox_day_d5.png`, `rb_ox_night_d2.5.png`). Weak spot: in idle the bot's tail stands up
  behind the back, so the tuft shows as a small pale hump behind the head from above.
* **Works:** 3 bots made by the game's `BotFactory`, all `Bot.Inkpaws` on `Characters/Pandaborn/WoodenOx.Model`; the
  Lumberjack Flag was switched to bots (`LumberjackFlag.Inkpaws -> Bot`) and they took the jobs
  (`bot:WaitInsideIdlyWorkplaceBehavior` 64 samples, `bot:WalkToPositionExecutor` 33), but no trees were marked for
  cutting, so **no cutting was seen**.
* **Carries:** a log in its hands at night and after the reload (forced by the dev probe for the picture:
  `rb_ox_night_d2.5.png`, `reload\rb_reload_ox_d2.5.png`). No hauling job was seen.
* **Save and reload:** all 3 oxen came back on the ox mesh (`reload\rb_reload_gear_front.png`, `rb_reload_ox_d5.png`).
* **Folktails bots unchanged:** `Bot.Folktails` on `Characters/Bot/Bot.Folktails.Model`, 1,655 vertices (rb-p3b
  Folktails game, `T\rb-p3b\folktails\rb_ft_bot_d2.5.png`, `rb_ft_people_front.png`).
* **Horns and vanilla bot hats: not seen in game** (the lumberjack bot outfit has no hat). Offline the farmer bot hat
  sits between the horns and the horns pass through its brim (`E:\PandabornDev\build\characters\ox\ox_final_34.png`):
  acceptable; if not, give the Inkpaw bot outfits no hat.
* **Zipline:** offline only (`ox_final_side.png`); no zipline in the test colony.

**Bot avatar:** `mod/PandabornFactions/Sprites/Pandaborn/Avatars/InkpawsBot.png` is now a render of the real ox mesh
in the avatar style (`src/pipeline/characters/make_ox_portrait.py`: the same studio lights and teal plate as the
Ringtail and Inkpaw avatars, 512 px; meta kept). It replaces the icon lane's four-legged plank ox
(`src/pipeline/icons/ox_avatar.py`, which would overwrite it if rerun; the earlier picture is kept at
`E:\PandabornDev\build\characters\portraits\InkpawsBot_icon_lane_old.png`).

### 8.6 For the catalogue lane

All shapes below were proven in rb-p3a/rb-p3b as merges in the dev mod `proto/ringtail-body/mod`.

1. **Wooden Ox model.** `catalogue/faction.toml` `[characters.bot]`:
   `models = { "Model_Preserved" = "Characters/Pandaborn/WoodenOx.Model" }` (the material stays `Bot.Folktails`; nothing
   else changes). `tools/pandaborn.ps1`, next to `$ringtailMeshes` (source `$RingtailMeshSource` =
   `E:\PandabornDev\build\characters\out`), shipped always, not only with Ringtails:
   `'Characters\Pandaborn\WoodenOx.Model.timbermesh' = Join-Path $RingtailMeshSource 'WoodenOx.Model.timbermesh'`.
   Rebuild: `python -I src/pipeline/characters/build_ox.py E:\PandabornDev\reference\vanilla-bot\Bot.Folktails.Model.timbermesh E:\PandabornDev\build\characters\out\WoodenOx.Model.timbermesh`.
2. **Attachments on both adults** (`InkpawAdult.Inkpaws` and `RingtailAdult.Inkpaws`), appended to the copied
   `TemplateAttachmentsSpec.Attachments` (the generator's `set` replaces lists, so this needs an append):
   ```json
   {"AttachmentId": "PandabornConicalHat", "Prefab": "Characters/Pandaborn/Attachments/ConicalHat", "Parent": "#Head",
    "Position": {"X": 0.0, "Y": 0.0, "Z": 0.0}, "Rotation": {"X": 0.0, "Y": 0.0, "Z": 0.0},
    "Scale": {"X": 1.0, "Y": 1.0, "Z": 1.0}, "CreateInstantly": false},
   {"AttachmentId": "PandabornBackBasket", "Prefab": "Characters/Pandaborn/Attachments/BackBasket", "Parent": "#Backpack",
    "Position": {"X": 0.0, "Y": 0.0, "Z": 0.0}, "Rotation": {"X": 0.0, "Y": 0.0, "Z": 0.0},
    "Scale": {"X": 1.0, "Y": 1.0, "Z": 1.0}, "CreateInstantly": false}
   ```
3. **Three outfit overrides** (`WorkerOutfitSpec.Attachments`, replacing the copied list):
   * `WorkerOutfit.Farmer.Beaver.Inkpaws`: `["PandabornConicalHat"]` (was `FarmerHat.Beaver.Folktails`; the Paddy House
     and the Efficient Farm House both use the `Farmer` outfit).
   * `WorkerOutfit.Gatherer.Beaver.Inkpaws`: `["PandabornBackBasket"]` (was `GathererBackpack`).
   * `WorkerOutfit.Gatherer.PandabornRingtail.Inkpaws`: `["PandabornBackBasket"]`: in `[outfits] extra` the Gatherer
     entry's `set` gains `Attachments = ["PandabornBackBasket"]`. The first two are copies of Folktails outfits, which
     `[outfits]` cannot override yet.
4. **Bundles stage:** add `E:\PandabornDev\build\characters\attachments` to `-BundleDirs` in `tools/pandaborn.ps1`, so
   `pandabornattachments_win` and `pandabornattachments_mac` are copied unrenamed into `AssetBundles/`. Rebuild with
   `src\unity\PandabornAttachments\build.ps1` and `... build.ps1 -Mac`.
5. **Fur masks:** nothing to do; `mod/PandabornFactions/Characters/Pandaborn/RingtailAdult|RingtailChild.Model.FurMask.png`
   (+ meta) are hand-written mod files and already assembled. They only matter with a Reskin that has the compat change.

### 8.7 The Festival's rising sky lanterns

`Effects/Pandaborn/LanternRise` (in `pandabornattachments_win|_mac`, built by `src/unity/PandabornAttachments/build.ps1`):
one `ParticleSystem`, no Play on Awake, emission rate 0, non-looping 9 s with 9 single-lantern bursts (a `Play()` that
finds it idle sends up a flight of 9; `Emit(1)` sends one), box release 2.6 x 2.6 m at hand height, world-space rise
1.0-1.5 m/s easing in, sideways drift +-0.16 m/s, noise sway, slight rock, life 10-16 s, fade in 0.5 s and out over the
last ~3 s, size 0.44-0.58 m quad (the paper ~0.3 m plus a halo), max 64. Sprite painted by `make_attachments.py`
(`paint_sky_lantern`: red-orange paper, LanternPaperRed (240,70,22) shoulders, yellow-orange core, flame bead, four
struts, hoop, soft halo; no writing). Material: `Universal Render Pipeline/Particles/Unlit`, transparent alpha blend,
`_EMISSION`, queue 3035: the shader and settings of the game's own firework trails (`CometRed_Trail`, `Sparks`, read
from `resources.assets`); keywords checked in both bundles with UnityPy.

**Catalogue entry** (Festival Square `PandabornFestivalSquare.Inkpaws`, `TemplateAttachmentsSpec.Attachments`, append):
`{"AttachmentId": "LanternRise", "Prefab": "Effects/Pandaborn/LanternRise", "Parent": "#LanternRise", "Position": {0,0,0},
"Rotation": {0,0,0}, "Scale": {1,1,1}, "CreateInstantly": false}` (the adopted square model has `#LanternRise`).
For the events lane: `FestivalSquare.Launch` calls `Play()`, which does nothing while lanterns are still aloft, so
today each idle call sends a flight of 9; for exactly one lantern per call use `_lanternRise.Emit(1)`.

**In game** (written 2026-11-25 by the docs lane: this lane stopped at the pause with the run still queued, and
the line here read "not yet proven"). Run `lanterns-1` ran and passed on 2026-11-14 at 18:20 (hidden desktop, 0
errors): dev copy `E:\PandabornDev\build\proto\pblanterns`
(`proto/events/build.ps1 -Name pblanterns -Variant proto\ringtail-body\variants\lanterns -NoProbe`, with the new bundles),
request `proto/ringtail-body/test/lanterns.request.json` (festival called at once, dusk shots every 0.2 h from 15.9 h,
one at 19 h), output `E:\PandabornDev\build\test\lanterns-1\ev_l_*.png`.

* The prefab loads from the bundle and plays from the square without error.
* It does not read as a sky of lanterns: in the dusk shots (for example `ev_l_d1_h1650.png`) the only lanterns to
  be seen from the game camera are small red points at the square itself, hard to tell from its string lanterns.
* The events lane then changed how the lanterns are released. Its run `events-sky-1` (19:09, PASS, never written
  up) shows about seventeen lanterns climbing away over the square at 18:00 (`ev_s_h1800_wide.png`).
* On 2026-11-25 that rework was finished without a game: a continuous release for the whole show (8038a53) and a
  bigger, slower prefab and sprite (c3b6a33: 0.7 to 0.9 m quads, 0.5 to 0.9 m/s). **`pandabornattachments` has not
  been rebuilt with it** (Unity was not available that day), so the numbers in the paragraph above describe the
  bundle as built on 2026-11-14, not the prefab in git.
* Owed: rebuild both twins of the bundle, then run N10 of `docs/tech/needs-game-run.md` (speed 1 and speed 3).
