# Ringtail body test (dev only, never shipped)

Puts the real red panda body on the Ringtails of the prototype (`proto/ringtails`) and takes pictures of it in game.
Results and method: [docs/tech/ringtail-body.md](../../docs/tech/ringtail-body.md).

Manifest Id `JigglyPanda.PandabornProtoRingtailBody`; requires `JigglyPanda.PandabornProtoRingtails` (so it loads after
it and its same-path blueprints merge on top). Built to `E:\PandabornDev\build\proto\ringtail-body`; only ever
installed for a test run (`run_game_test.ps1 -ExtraMods`).

| Piece | Where |
|---|---|
| Template merges: model `Characters/Pandaborn/RingtailAdult|RingtailChild.Model`, `TransformSpec` scale back to 1 (the size is baked into the mesh), coat lists | `mod/Characters/Pandaborn/Ringtail*.Inkpaws.blueprint.json` |
| The two meshes (copied by `build.ps1` from `E:\PandabornDev\build\characters\out`) and the coats (from `mod/PandabornFactions/Materials/Pandaborn/Ringtails`) | build output only |
| Picture probe (request key `ringtailBody`): line-up of Inkpaw adult, Ringtail adult, Ringtail kit, Inkpaw cub lifted above the map (front, back, side, top), and game-camera shots of a Ringtail carrying goods by day and by night, alone and with an Inkpaw set down beside it | `src/RingtailBodyProbe.cs` |

## Build and test

```powershell
powershell -ExecutionPolicy Bypass -File proto\ringtail-body\build.ps1
powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -NoBuild -Faction Inkpaws -InGameDays 1.1 -Speed 3 `
    -ExtraMods E:\PandabornDev\build\proto\ringtails,E:\PandabornDev\build\proto\ringtail-body `
    -OnlyMods JigglyPanda.PandabornFactions -RequestJson proto\ringtail-body\test\body.request.json `
    -TimeoutSeconds 1500 -WaitForGameSeconds 10800 -RunId rb-<n>
```

Output in `E:\PandabornDev\build\test\<run id>\`: `rb_*.png` and `ringtailBody.json` (per shot: the subjects' template,
model asset, mesh vertex count, coat, carried good), plus the prototype probe's `rt_*.png` panel shots.
