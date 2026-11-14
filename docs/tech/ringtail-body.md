# The Ringtail body (red panda)

Status: built and tested in game (runs rb-1 to rb-4), 2026-11-14 (game 1.1.2.8). Art lane. Replaces the prototype's stand-in (the Inkpaw
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
