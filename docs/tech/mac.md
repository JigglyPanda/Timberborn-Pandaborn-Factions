# Mac asset bundles

The game on macOS loads only `AssetBundles/<name>_mac`; on Windows only `<name>_win` (and unsuffixed files on both).
`ModAssetBundleLoader.CanBeLoadedOnCurrentPlatform` decides **per file** (decompiled `Timberborn.ModdingAssets`), so
`_mac` files sitting next to the `_win` ones are never opened on Windows. Without `pandabornplants_mac` a Mac player
of the Inkpaws crashes (plant models whose materials are missing); without `pandabornlook_mac` they get the plain
Folktails look (docs/tech/look.md, *Mac bundles*). Since 2026-11-14 both `_mac` bundles build on this machine.

## What was installed where (no admin, nothing written to C:)

| What | Where | Size |
|---|---|---|
| Private copy of Unity 6000.5.11f1 (revision `5c3a1087d8e4`), robocopy of the Hub install on C: (read only) | `E:\PandabornDev\tools\unity-6000.5.11f1` | 8.40 GB |
| + Mac Build Support (Mono), 271 files | `...\unity-6000.5.11f1\Editor\Data\PlaybackEngines\MacStandaloneSupport` | 2.05 GB |
| The official installer, kept for re-extraction | `E:\PandabornDev\tools\downloads\unity-mac-mono-6000.5.11f1\` | 0.49 GB |
| Portable 7-Zip 26.06 (from 7-zip.org; in the end not needed, see below) | `E:\PandabornDev\tools\7zip`, downloads in `E:\PandabornDev\tools\downloads\7zip*` | 0.01 GB |
| Mac Unity projects (made like the Windows ones, own `Library`) | `E:\PandabornDev\unity\PandabornLook-mac`, `E:\PandabornDev\unity\PandabornPlants-mac` | 1.91 + 1.76 GB |
| Mac staging output + logs | `E:\PandabornDev\build\{look,plants}\mac-stage`, `unity_build_mac.log`, `unity_import_mac.log` | 0.05 GB |

Total about **14.7 GB on E:**. The C: install, the registry, PATH and Unity Hub were not changed; Hub does not know the
E: copy. Like the C: editor, the copy still writes its usual small logs and the Bee cache under `%LOCALAPPDATA%\Unity`.

**Licence:** the copy runs in batch mode with the machine's existing licence through the Hub's licensing client; no
prompt, no activation. Its log has the same licensing lines as the C: editor (including the harmless
`Code 10 while verifying Licensing Client signature ... ignoring`, which the C: editor logs too).

### The module, and how it was unpacked

* Source: Unity's public release API
  `https://services.api.unity.com/unity/editor/release/v1/releases?version=6000.5.11f1&platform=WINDOWS&architecture=X86_64`,
  module `mac-mono` "Mac Build Support (Mono)": url
  `https://download.unity3d.com/download_unity/5c3a1087d8e4/TargetSupportInstaller/UnitySetup-Mac-Mono-Support-for-Editor-6000.5.11f1.exe`,
  `downloadSize` 523,284,776, `installedSize` 2,203,513,396, `integrity` `md5-Jg9+vqe2DhC1ywkEAfFA+w==`,
  `destination` `{UNITY_PATH}`.
* Checks on the download: size and MD5 equal the metadata; Authenticode signature **Valid**, signer
  "Unity Technologies SF".
* The installer is NSIS with `requestedExecutionLevel highestAvailable` (a UAC prompt for an admin account), so it was
  **not run**. 7-Zip (23.01 and 26.06) cannot open it: Unity builds it with its own NSIS ("v15-May-2025.cvs",
  first-header flags `0x70`) whose data is a chain of separate LZMA chunks with 8-byte block lengths and 36-byte
  script entries. `tools/unity_nsis_extract.py` reads that format (layout documented at its top) and writes exactly
  the files the install section would put in `$INSTDIR\Editor\Data\PlaybackEngines\MacStandaloneSupport`. It runs
  no installer code.
* Checks on the extraction: 271 files, **2,203,513,396 bytes = the metadata's `installedSize` to the byte**; the
  signed Windows binaries inside (`MacStandalonePlayerBuildProgram.exe`, `Newtonsoft.Json.dll`) have Valid
  Authenticode signatures; a second extraction with the committed script is identical (`diff -r`) to the installed tree.
* What the installer does besides copying (read from its script, not done): deletes an older `MacStandaloneSupport`,
  checks `Unity.exe` exists, runs `DocCombiner.exe` to index documentation (no documentation files are in this module).
* The editor log then shows `Register platform support module: .../MacStandaloneSupport/UnityEditor.OSXStandalone.Extensions.dll`
  and, as on every Windows host, `Native extension for OSXStandalone target not found` (that native extension exists
  only in the macOS editor; bundle builds do not need it).

Redo from scratch (e.g. on another machine, or after a Unity upgrade: change the version and revision):

```powershell
robocopy "C:\Program Files\Unity\Hub\Editor\6000.5.11f1" E:\PandabornDev\tools\unity-6000.5.11f1 /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /MT:8
# download the module URL above into a new empty folder, check size + MD5 + signature, then:
E:\PandabornDev\tools\venv\Scripts\python.exe -I tools\unity_nsis_extract.py `
    E:\PandabornDev\tools\downloads\unity-mac-mono-6000.5.11f1\UnitySetup-Mac-Mono-Support-for-Editor-6000.5.11f1.exe `
    E:\PandabornDev\tools\unity-6000.5.11f1\Editor\Data\PlaybackEngines\MacStandaloneSupport `
    --temp E:\PandabornDev\tools\tmp\macnsis --expect-bytes 2203513396
```

(The script needs ~2.2 GB of scratch space for a few minutes and deletes it.)

## How to build

```powershell
powershell -ExecutionPolicy Bypass -File tools\build_plants.ps1 -Mac                          # pandabornplants_mac
powershell -ExecutionPolicy Bypass -File tools\build_look.ps1 -Mac -BundleName pandabornlook  # pandabornlook_mac
#   -SkipTextures   reuse the textures already painted into the Mac project
#   -UnityPath <editor folder or Unity.exe>   override the auto-detected editor
#   -MacProject <folder>                      override the Mac project (default <Project>-mac)
```

* `-Mac` builds **only** `<name>_mac`; the same command without `-Mac` builds `<name>_win` as before. Run both for a
  release; they can run at the same time.
* Editor choice (`tools/unity_editor.ps1`): an explicit `-UnityPath` wins (with `-Mac` it must have
  `MacStandaloneSupport`); otherwise Windows builds use the C: install first (unchanged), `-Mac` builds the first
  editor that has Mac support (the E: copy). The old `-UnityExe` name still works (alias).
* `-Mac` uses its own project, `E:\PandabornDev\unity\PandabornLook-mac` / `PandabornPlants-mac`, created on first use
  exactly like the Windows ones (official template + `Shaders.zip`; plants: one import pass, ~12 min the first time)
  and opened with `-buildTarget OSXUniversal`, so the macOS target is always active there and the Windows projects
  are never switched, reimported or locked. Textures are painted into it from the same sources
  (`src/pipeline/look_textures.py`, `src/pipeline/plants/textures.py`) and the builders come from the same
  `src/unity/*/Editor/*.cs` (new `-macOnly` switch skips the `_win` build).
* Unity writes into `E:\PandabornDev\build\{look,plants}\mac-stage` (own folder manifest, own log
  `unity_build_mac.log`); the script then copies `<name>_mac` and its `.manifest` next to the `_win` files in
  `E:\PandabornDev\build\look\AssetBundles` / `E:\PandabornDev\build\plants\AssetBundles`. From there the existing
  steps ship them unrenamed: `Pandaborn.Look.csproj` copies `pandabornlook_win` and `_mac`, `tools/pandaborn.ps1
  bundles` copies every `pandaborn*_win|_mac` from `-BundleDirs`.
* Times: first look build 679 s (import + build), plants 699 s import + 110 s build; later builds take minutes.

## What was verified on Windows

| Check | How | Result |
|---|---|---|
| Valid UnityFS for macOS | header; `WebExtract.exe` + `binary2text.exe` from the editor's `Data\Tools`; serialized-file header read | both `UnityFS`, engine `6000.5.11f1`, serialized format 23, **target platform 2 (StandaloneOSX)**; the `_win` twins say 19 (StandaloneWindows64) |
| Same assets as the `_win` twin | the bundle's `m_Container` paths and every object name, `_mac` vs `_win` | identical (look: 19 materials, 61 textures; plants: 7 materials) except the AssetBundle object's own name and the shaders' constant-buffer names (`FGlobals`/`VGlobals` on Metal, `$Globals` on D3D) |
| Metal shaders | GPU program types in the dumped shaders; build log | `_mac`: 19 × type 23 (Metal VS) + 43 × type 24 (Metal FS); `_win`: 19 × 15 + 43 × 17 (D3D11 SM5.0): the same variant set. Log: `Target graphics API: metal`, no shader errors; two `pow(f, e)` warnings from the game's own `ComputeWindOffset.hlsl` |
| Texture format | `m_TextureFormat` | BC7 (25) on both targets, from the importers' `Standalone` override |
| Sizes | file sizes | `pandabornlook_mac` 43,945,017 B vs `_win` 43,923,326 B; `pandabornplants_mac` 5,765,047 B vs `_win` 5,747,171 B |
| Windows game unaffected | `tools/run_game_test.ps1` run `mac-bundles-1` (see below) | see Results |

## Results

`mac-bundles-1` (2026-11-14), Inkpaws on Plains, `-OnlyMods JigglyPanda.PandabornFactions`, 60 s, plus a dev-only mod
`E:\PandabornDev\build\mac\PandabornMacBundleCheck` (`-ExtraMods`) whose `AssetBundles/` holds `pandabornlook_mac`
and `pandabornplants_mac`. The installed faction itself already ships `pandabornlook_win` and
`pandabornplants_win` and the code, so the older dev mods (code dev mod, plants prototype) could not be used: they would load
the `_win` bundles a second time, which crashes (look.md problem 10). Because the loader decides per file, `_mac`
files in a second mod's `AssetBundles` behave as they would beside the `_win` ones.
**PASS**: verdict pass, 0 errors, 0 exceptions, no log issues from any mod. `result.json` lists all three mods loaded;
`Pandaborn.Look` re-themed 19 materials and restored them on unload (the `_win` bundle in use); Inkpaw adults/children with their
own meshes and coats; all 10 batch-control tabs opened. No log line mentions the `_mac` files. The faction's next
regular build carries the `_mac` files itself (`Pandaborn.Look.csproj`, `tools/pandaborn.ps1 bundles`), which
`tools/validate.py --release` already requires.

## What only a real Mac can verify

Ask a community tester with a Mac (ideally one Apple Silicon and one Intel) to check, with the mod's `AssetBundles`
holding all four `_mac` bundles: `pandabornlook_mac`, `pandabornplants_mac`, `pandabornsounds_mac` and
`pandabornattachments_mac`. (Corrected 2026-11-25: this list named only the first two, the ones that existed when it
was written. The sound and attachment twins are built the same way, sit in the staged build beside their `_win`
twins, and `tools/validate.py --release` compares each pair; neither has been loaded on a Mac. Checks 8 and 9 are
theirs.)

1. **The game starts and the Inkpaws load** (new game, any map): no error dialog, `Player.log`
   (`~/Library/Logs/Mechanistry/Timberborn/Player.log`) has no `AssetBundle`, `Material ... not found` or shader
   errors mentioning `pandaborn`.
2. **Plants render**: the seven Inkpaws plants (tea, timber bamboo, shoot bamboo, rice, cabbage, persimmon, Sichuan
   pepper) show their own leaves, not pink/magenta and not invisible; alpha-cut leaves look like the Windows
   screenshots in docs/tech/plants.md; they sway in the wind.
3. **The look applies**: buildings show the dark timber / clay tile / lattice window look, not plain Folktails; the
   log line of `Pandaborn.Look` reports the materials as copied, not "not available (asset bundle missing?)".
4. **Night windows glow** on lit buildings (emission through Metal).
5. **Return to main menu and start or load a game again** (the second load re-matches bundles by file name;
   docs/tech/look.md problem 10): no "another AssetBundle with the same files is already loaded" error.
6. Folktails and Iron Teeth games still look vanilla with the mod enabled.
7. Memory/performance: no obvious drop compared with a Folktails game (BC7 textures need a GPU that supports BC
   formats; all Apple Silicon and Intel Macs that run the game do, but this is unconfirmed).
8. **Sounds play** (`pandabornsounds_mac`): a bell is heard when the working day ends, a Steamer at work sizzles,
   clicking the Village Hall gives its own sound. A missing clip is silent for the sounds our code plays, but a
   building that names one of our loops throws when it starts, so a Steamer that works without an error is the
   real check.
9. **Hats, baskets, the Wooden Ox and the festival's lanterns** (`pandabornattachments_mac`): a farmer wears the
   conical hat, a gatherer the back-basket; an Inkpaws game loads at all (a character template that names a prefab
   no bundle holds fails at load: seen on Windows in `events-final-1`).

## Notes

* Only Mac Build Support (Mono) was added; IL2CPP and the Mac dedicated-server module are not needed for asset bundles.
* After a Unity upgrade the E: copy and the module must be redone for the new version (the bundle builds use 6000.5.11f1
  because the game does).
* Nothing here goes into git except `tools/unity_nsis_extract.py`, `tools/unity_editor.ps1`, the two build scripts
  and the builders' `-macOnly` switch.
