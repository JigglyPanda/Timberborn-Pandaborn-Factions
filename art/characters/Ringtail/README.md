# Ringtail (red panda) body: sources and rebuild

The Ringtail body is not modelled by hand: it is sculpted procedurally from the game's beaver, as the Pandaborn
Reskin's giant panda was, so that it keeps the beaver's node layout, UV layout, material names and all 61 (adult) /
39 (kit) baked animations. Everything that defines it is code and numbers, in `src/pipeline/characters/`:

| File | What |
|---|---|
| `rp_configs.py` | **The shape**: head, cheeks, muzzle, ears, body, limbs, tail (length, thickness, rest curve), the size (0.82 of an Inkpaw) |
| `redpanda.py` | The sculpt (pointed ears, slim body, round tail built from the beaver's paddle) and the tail deformer |
| `build_ringtail.py` | Builds a `.timbermesh`: refine, sculpt, mouth cap, transfer every frame, bake the size, write |
| `paint_ringtail.py` | **The coats**: markings and the coat variants table (`ADULT_COATS`, `CHILD_COATS`) |
| `make_portraits.py`, `bl_portrait.py` | The four avatars |
| `qa_ringtail.py` | Format checks and motion metrics against the beaver |
| `preview.py`, `pose_export.py`, `bl_render.py`, `anim_sheet.py` | Offline renders of any pose (Blender, headless) |
| `make_ringtails.py` | Runs everything |
| `panda.py`, `geom.py`, `raster.py`, `paint.py`, `tmesh.py` | Copied from the Reskin (same owner) |

## Inputs (from your own game install, never committed)

```powershell
$PY = 'E:\PandabornDev\tools\venv\Scripts\python.exe'
& $PY -I src\pipeline\dump_vanilla_models.py 'C:\Program Files (x86)\Steam\steamapps\common\Timberborn\Timberborn_Data' `
    E:\PandabornDev\reference\vanilla-characters BeaverAdult BeaverChild
```

and these textures, decoded with UnityPy into `E:\PandabornDev\reference\vanilla-characters\textures\` (names as in
the game): `Adult_AO_2K`, `Child_AO_1K`, `BeaverAdult1.Folktails`, `BeaverChild1.Folktails`, `Contamination_D`
(used for: placing the mouth cap, AO compensation, the fur-stroke high-pass, the contaminated portraits), and for
checks only `Tail1..4.Folktails`, `HaulerBackpackStrings_D`, `WorkerHammerStrings_D`, `LumberjackStrings_D`.

## Rebuild

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
& $PY -I src\pipeline\characters\make_ringtails.py                       # meshes, qa, coats, portraits
& $PY -I src\pipeline\characters\make_ringtails.py --steps meshes,qa     # only the meshes
```

Meshes: `E:\PandabornDev\build\characters\out\RingtailAdult.Model.timbermesh` (~108 MB) and
`RingtailChild.Model.timbermesh` (~64 MB), with `.paint.npz` (rest fields) and `.ao.npy` (baked AO) beside them. They
are copied into the mod by the build (see `docs/tech/ringtail-body.md`, "Adopting it"). Coats and avatars are written
straight into `mod/PandabornFactions/` and are committed.

Run time on the dev PC: meshes ~3 min each, coats ~2.5 min each (2048² painting in numpy), portraits ~1 min each
(Cycles with hair on the RTX 5070 Ti).
