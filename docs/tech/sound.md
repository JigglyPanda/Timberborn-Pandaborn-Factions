# Sound

The Inkpaws' own sounds: what the game lets a mod attach a sound to, the sounds made for the faction, how they are made
and checked, how they reach the game (one asset bundle, `pandabornsounds`), what was proven in game, and what the
catalogue and code lanes adopt. All audio is synthesized by our own code (`src/pipeline/sound`, numpy/scipy): no
samples from the game, other mods or the internet. Disclosure: art, code and audio are AI-generated.

Game 1.1.2.8. Sources: decompiled `Timberborn.SoundSystem`, `CoreSound`, `GameSound`, `UISound`, `Buildings`,
`WorkSystem`, `WorkshopsEffects`, `PowerGeneration`, `EnterableSystem`, `BeaversUI`, `MainMenuPanels`, `WondersUI`,
`FireworkSystem`, `AutomationBuildings`, `ModdingAssets`, `AssetSystem` (in `E:\PandabornDev\reference\decompiled`); the
vanilla blueprints; the game's own clips, extracted for measurement only to `E:\PandabornDev\reference\vanilla-sounds`.

## 1. How the game plays sounds

### Clips, ids and variants

* `AudioClipService.LoadAudioClips()` runs in every context (main menu, game, map editor) when `SoundSystem` loads: it
  takes **every** `AudioClip` whose asset path starts with `sounds` from every asset provider (the game's `Resources`
  and every enabled mod's asset bundles: `IAssetLoader.LoadAll<AudioClip>("Sounds")`) and keys it by the clip's
  **asset name** (the file name without extension). A later clip with the same name replaces an earlier one, for every
  faction: so a mod must never ship a clip named like a vanilla one.
* A **sound id** plays one of its variants: every clip whose name equals the id or starts with `id + "_"`
  (`Environment.Pandaborn.ShiftBell.End` plays `..._01`, `..._02` or `..._03`; never the same one twice in a row).
* An id with no clip throws `ArgumentException("No sound files for: <id>")` the first time it is played on an emitter
  (`Sounds.AddSounds`). Inside a tick or a selection handler that is an unhandled exception. **So a blueprint that names
  one of our ids needs our bundle on that platform** (the `_mac` bundle is not optional once data points at it), and code
  must check `AudioClipService.GetAudioClipNames(id).Any()` before playing.
* Mod bundles are loaded for every game, whatever the faction: our clips are in the dictionary in a Folktails game too,
  but nothing plays them there (proven in game, section 6, run `sound-4`).

### Mixer groups

* The mixer group comes from the id's first dot-segment (`AudioMixerGroupRetriever.GetAudioMixerGroupFromSoundName`), unless
  the caller passes a custom one. The game's own ids use `Environment`, `UI`, `Music_Game`, `Music_MainMenu`; custom
  groups set by callers: `Building` (building loops, fire, shafts), `Ambient` (day/night/water ambience, sleeping beavers),
  `Wind`. `FindMatchingGroups(name).Single(...)` throws for an unknown name, so **every id must start with an existing
  group**: ours are `Environment.…Pandaborn…` and `UI.…Pandaborn…`. (The house rule "global ids start with `Pandaborn`"
  cannot hold for sounds; the `Pandaborn` segment sits after the mixer prefix, and no vanilla id is a prefix of ours.)
* Volume parameters: `GameMaster_Volume`, `Music_Volume`, `UI_Volume`, `Environment_Volume` (the settings sliders);
  `Building_Volume` follows the listener-to-camera distance (1 to 60 units), `Ambient_Volume` and `Wind_Volume` follow
  the zoom (`CameraHeightVolumeUpdater`, `CoreSoundSpec`).

### Emitters

| | 3D (`spatialBlend` 1) | 2D (`spatialBlend` 0) |
|---|---|---|
| Distance | linear roll-off, full volume to 2 units, silent at 10 (`AudioSourceFactory`: `minDistance` 2, `maxDistance` 10; area sounds take their own cut-off), no doppler | everywhere at full volume |
| Listener | a point above the terrain at the screen centre (`SoundListener`: up to 3 units above ground, scaled by zoom); lerped 10 % per frame | |
| Used for | building loops, fire, bell toll, firework trails, speakers set to "spatial" | UI, selection sounds, wonder launch, firework bursts, music, ambience |

* **Loops** (`LoopSingle2DSound`/`LoopSingle3DSound`): random pitch 0.9 to 1.1, a random 0 to 0.5 s start delay, a 3 s
  fade-in. Stopping fades out over 3 s and leaves the source playing at volume 0 (it is restarted, not recreated, next
  time). One looping sound per emitter `GameObject` (a second throws `InvalidOperationException`).
* **One-shots** (`PlaySound2D`/`PlaySound3D`): pitch 1, volume 1, no fade.
* **A custom mixer sticks to the emitter.** `SetCustomMixer(emitter, ...)` also sets the mixer for every sound created
  on that `GameObject` afterwards (`Sounds._customMixerName`). Selecting a building calls it with `UI`, so a sound that
  code later plays from the building's own `GameObject` goes through the `UI` group (seen in run `sound-2`: 3D clips
  played on the Village Hall after it was selected came out of `UI`). Code should play from its own child object, or
  call `SetCustomMixer` itself before playing.
* Sounds are 3D only within 10 units of the listener: a building loop is heard only when the camera looks at it.

### Every slot a mod can fill

| Slot | Spec and field (data) or API (code) | Plays | 2D/3D, mixer | When | Faction-scoped? |
|---|---|---|---|---|---|
| Building loop | `BuildingSpec.LoopingSoundName` = `X` | `Environment.Buildings.Loop.X` | 3D, `Building`, priority 128, offset to the footprint centre | `WorkshopSounds` (any `Workshop`): while `CurrentlyWorking`; `PowerGeneratorSounds` (needs `PowerGeneratorSoundsSpec`): while active, powered and output > 0; `EnterableSounds` (attractions, dwellings): while someone is inside; `UndergroundWaterSourceDrillSounds`; `RangedEffectBuilding` | yes (our templates) |
| Building selected | `BuildingSpec.SelectionSoundName` = `X` (default `Default`) | `UI.Buildings.Selected.X` (unfinished: `.Default`) | 2D, `UI` | click on the building | yes |
| Colonist selected | `FactionSpec.SoundId` = `S` (vanilla `Common`) | `UI.Beavers.S.Selected.{Adult,Child}_{Content,Discontent,Sleepy,Sleeping}` (all eight needed) | 2D | click on a colonist | yes |
| New-game faction panel | `FactionSpec.SoundId` | `UI.Beavers.S.Selected.Adult_Content` | 2D | picking the faction (`MainMenuSoundController`) | yes |
| Bot selected | `BotSelectionSoundSpec.SoundNameKey` = `K` | `UI.Bots.Selected.K_{Content,Discontent}` | 2D | click on a bot | yes |
| Wonder launch | `FactionWonderSpec.WonderLaunchSound` | the id as written | 2D, `UI` | the wonder is activated (`WonderFragment`) | yes |
| Natural resource selected | `BasicSelectionSoundSpec.SoundName` / `AlternativeSoundName` | `UI.BasicSelection.X` (10 %: `Y.AltSound`) | 2D | click on a plant, tree, ruin | yes (our plants) |
| Firework | `FireworkSpec.TrailSound`, `BurstSound` | as written | trail 3D, burst 2D | a firework flies / bursts | **no**: firework specs are global (`FireworkSpecService` = every `FireworkSpec`); a new firework appears in every faction's launcher. An Inkpaws-only blueprint modifier on an existing firework is possible |
| Speaker sound | `SpeakerSoundSpec` (`SoundId`, `DisplayNameLocKey`) | as written | speaker's choice | automation | **no**: global list, shows in every faction |
| Working-hours bell | `WorkingHoursBellSpec` (Iron Teeth Bell) | hard-coded `Environment.Buildings.BellToll` | 3D, priority 30 | `WorkingHoursTransitionedEvent` | the id cannot be changed by data |
| Fire, dynamite, shafts, sleeping, UI clicks, weather, music, ambience | hard-coded ids or global configuration specs (`AmbientSpec`, `MusicSpec`, `GameUISoundSpec`, `CoreSoundSpec`) | | | | **no**: global; changing them changes every faction |
| Anything | `ISoundSystem` (`Timberborn.SoundSystem`, public) from code | any id | either | whenever code says | yes (code decides) |

Also possible from code (not used): `AudioClipService.AddAudioClip(id, clip)` / `RemoveAudioClip` are public, so code can
register clips at run time (the speaker building loads user WAV/MP3 files this way with `UnityWebRequestMultimedia`).
That would be the route to loose audio files without a bundle; it is not needed.

### Import settings of the game's clips

254 clips: 204 `CompressedInMemory` Vorbis preloaded mono (131 at 48 kHz, 73 at 44.1 kHz), 16 stereo music `Streaming`,
the rest `DecompressOnLoad` (fireworks, fire, shafts, sleeping) or stereo `CompressedInMemory` (ambience, wonder).
Ours: `CompressedInMemory`, Vorbis quality 0.6, 48 kHz preserved, preload on, forced mono except the stereo wonder launch.

## 2. Vanilla loudness (measured)

BS.1770 integrated loudness (LUFS-I), momentary maximum, sample peak, spectral centroid; `src/pipeline/sound/vanilla_report.py`.

| Kind | Clip | s | LUFS-I | M max | peak dBFS | centroid Hz |
|---|---|---|---|---|---|---|
| building loop | Loop.WaterWheel | 16.5 | -15.9 | -12.9 | 0.0 | 418 |
| | Loop.Gristmill | 6.5 | -21.3 | -18.7 | 0.0 | 852 |
| | Loop.Grill | 5.6 | -14.5 | -12.2 | 0.0 | 123 |
| | Loop.Bakery | 5.6 | -16.1 | -15.1 | 0.0 | 138 |
| | Loop.PaperMill | 7.5 | -18.4 | -17.1 | 0.0 | 1385 |
| | Loop.WaterPump | 8.0 | -15.1 | -12.2 | 0.0 | 904 |
| | Loop.LumberMill | 17.4 | -19.7 | -14.7 | 0.0 | 2062 |
| | Loop.GearWorkshop | 19.4 | -22.2 | -17.4 | 0.0 | 2350 |
| | Loop.WateringPlace | 7.9 | -30.9 | -26.1 | -0.1 | 1969 |
| | Buildings.Fire | 12.1 | -25.3 | -22.7 | 0.0 | 947 |
| attraction loop | Loop.DanceHall | 30.8 | -26.0 | -20.8 | -0.3 | 694 |
| | Loop.Agora | 29.6 | -14.7 | -11.8 | 0.0 | 628 |
| ambience (2D) | Ambient.Water / Day / Night / Wind | 19-48 | -40.2 / -37.4 / -34.1 / -40.1 | | | |
| one-shot | Buildings.BellToll | 4.0 | -14.2 | -11.4 | 0.0 | 1105 |
| | Fireworks.Trail_01 / Burst_01 / BigBurst_01 | 2-3 | -29.1 / -36.8 / -21.0 | | | |
| | Speaker.Chime_01 | 3.8 | -27.5 | -25.2 | -11.2 | 725 |
| UI | Wonder.EarthRecultivator / EarthRepopulator | 1.8 / 0.9 | -24.4 / -21.8 | -21.1 / -19.6 | -9.2 / -7.9 | 248 / 369 |
| | Wonder.Congratulations | 5.6 | -15.9 | -12.2 | -2.7 | 444 |
| | Selected.Bell / DistrictCenter / Bakery | 1-1.7 | -24.0 / -24.1 / -30.8 | | -7 to -10 | |
| | Beavers.Common.Selected.Adult_Content_01 | 1.4 | -24.3 | -22.2 | -10.0 | 1185 |
| | UI.Click | 0.15 | -20.2 | | -0.7 | 6819 |

Building loops are mastered hot (peaks at 0 dBFS, -15 to -22 LUFS) because the 3D roll-off and the `Building` mixer
take them down; selection and colonist sounds sit at about -24 LUFS with peaks near -10 dBFS.

## 3. The sounds

`src/pipeline/sound/sounds.py`, one function per sound; `report.md` and `report.json` in `E:\PandabornDev\build\sound`
have every number. Clip file = id, or id`_01`.. for variants. Loudness targets follow the vanilla clip of the same kind,
a little softer (the faction should sit inside the game's soundscape, not on top of it).

| Id | Variants | Kind | LUFS-I | What it is | Slot |
|---|---|---|---|---|---|
| `Environment.Pandaborn.ShiftBell.End` | 3 | one-shot 7.5 s | -18 | one soft strike of a small bronze bell (prime G4, hum an octave below, minor-third tierce; wooden striker; slow beating doublets); variants differ in strike strength and a hair of tuning | code |
| `Environment.Pandaborn.ShiftBell.Dawn` | 2 | one-shot 8.5 s | -20 | the same bell, two lighter strikes | code |
| `Environment.Pandaborn.NightClapper` | 2 | one-shot 1.9 s | -24 | two hardwood blocks: "tok ... tok-tok" / "tok-tok ... tok", dry | code |
| `Environment.Pandaborn.RingtailTwitter` | 3 | one-shot 1.2 s | -26 | a red panda's twitter: a quick falling run of soft chirps (fundamental 700-900 Hz, rolled off above: never a whistle) | code |
| `UI.Buildings.Selected.Pandaborn.VillageHall` | 1 | one-shot 2.4 s | -25 | the bell touched lightly | data |
| `Environment.Pandaborn.FlumeWater` | 1 | loop 16 s | -24 | a thin stream in a bamboo trough: small bubbles, a soft rush, the hollow body | code (area sound) |
| `Environment.Pandaborn.BambooTok` | 3 | one-shot 1.2 s | -26 | the hollow knock of a bamboo pipe on stone, a little spill | code, sparingly |
| `Environment.Buildings.Loop.Pandaborn.ScoopWheel` | 1 | loop 18 s (3 turns) | -19 | slow axle creak once a turn, eight buckets tipping, drips | data (stand-in) / code |
| `Environment.Buildings.Loop.Pandaborn.BambooWaterWheel` | 1 | loop 18 s (4 turns) | -18 | paddles churning the current, deeper axle creak | data |
| `Environment.Buildings.Loop.Pandaborn.KiteWindmill` | 1 | loop 16 s (5 turns) | -20 | four cloth sails sweeping past, flutter with the gusts, rope creak, hub tick | data |
| `UI.Buildings.Wonder.PandabornSkyLantern` | 1 | one-shot 7.6 s, stereo | -19 | the Sky Lantern lifts: a deep drum, a rising airy swell carrying a warm chord up a fourth, a second drum and the bell's shimmer at the top | data |
| `Environment.Buildings.Loop.Pandaborn.Steamer` | 1 | loop 14 s | -20 | pot simmering under bamboo baskets, steam breathing through the lid, lid taps | data |
| `Environment.Buildings.Loop.Pandaborn.TeaRoastery` | 1 | loop 12.8 s | -21 | dry leaves tossed in a wok every 1.6 s, faint wok scrape | data |
| `Environment.Buildings.Loop.Pandaborn.PickleYard` | 1 | loop 16 s | -22 | stoneware lids set down, brine sloshing | data |
| `Environment.Buildings.Loop.Pandaborn.LanternWorkshop` | 1 | loop 16 s | -22 | paper smoothed on frames, bamboo strips flexed and tapped, a paste brush | data |
| `Environment.Buildings.Loop.Pandaborn.SmokeKiln` | 1 | loop 15 s | -21 | a low wood fire: soft roar, crackles, the odd pop | data |
| `Environment.Buildings.Loop.Pandaborn.TripHammer` | 1 | loop 12 s (4 strokes) | -19 | water fills the lever's spoon, it tips with a splash, the wooden head thumps into the mortar | data |
| `Environment.Buildings.Loop.Pandaborn.Simmer` | 1 | loop 15 s | -21 | a broth pot on a low fire, a ladle now and then (Kitchen and Hot Pot Hall) | data |
| `Environment.Pandaborn.FestivalDrum` | 1 | loop 9.6 s (4 bars at 100 bpm) | -20 | a soft barrel drum and a rim click | code |
| `Environment.Pandaborn.Firecrackers` | 2 | one-shot 3.6 s | -25 | a short string of small firecrackers a little way off | code |
| `Environment.Pandaborn.LanternRise` | 3 | one-shot 2.2 s | -29 | one paper lantern lifting: an airy rise, a faint shimmer | code (or an Inkpaws-only firework modifier) |
| `Environment.Buildings.Loop.Pandaborn.OperaStage` | 1 | loop 24 s | -27 | very quiet plucked-string phrase (pentatonic, tremolo on long notes) and a wooden clapper | data |
| `Environment.Buildings.Loop.Pandaborn.Teahouse` | 1 | loop 18 s | -24 | tea poured into cups, porcelain lids, cups set on wood | data |
| `Environment.Buildings.Loop.Pandaborn.HotSpring` | 1 | loop 17 s | -24 | slow lapping, a spout trickle, a breath of steam | data |
| `UI.Beavers.Pandaborn.Selected.Adult_Content` | 4 | 0.9-1.1 s | -24 | an adult's soft quavering bleat ("mmeh-eh") | data (`SoundId`) |
| `...Adult_Discontent` | 2 | 1.3 s | -24 | a huff through the nose and a short low moan | data |
| `...Adult_Sleepy` | 2 | 1.5 s | -24 | a yawn | data |
| `...Adult_Sleeping` | 2 | 2.3 s | -24 | two slow breaths, the softest snore | data |
| `...Child_Content` | 4 | 1.0 s | -24 | two or three cub chirps | data |
| `...Child_Discontent` | 2 | 0.75 s | -24 | a short whiny falling squeal | data |
| `...Child_Sleepy` / `Child_Sleeping` | 2 / 2 | 1.7 s | -24 | a small yawn / quick light breaths | data |

55 clips, 32 ids. The bundle: see section 5.

### How they are made

Building blocks (`synth.py`): modal synthesis (decaying sines and resonator banks: the bell's partials, wood blocks,
bamboo, stoneware, porcelain), van den Doel bubbles (water), stick-slip impulse trains through wooden resonances (creaks),
noise shaped in the frequency domain (beds), hide-drum membranes with a pitch drop, Karplus-Strong plucks, noise grains
(leaves, paper, crackles), a noise-tail reverb. The panda calls (`voices.py`) are additive source-filter synthesis: a
band-limited glottal source with jitter, shimmer and a bleat quaver, shaped by gliding formants, plus breath.

Loops are seamless **by construction**: noise beds are shaped by FFT (circular), IIR filters run over two copies of the
loop and keep the second, events that ring past the end wrap to the start, modulations use whole cycles per loop, and
reverb on a loop is circular convolution. Loudness is set to the target with a lookahead limiter for one-shots and a
memoryless soft knee for loops (a limiter's gain state would not wrap).

### How they are checked (no listening)

`build_sounds.py` measures every written WAV and fails the build on any of: integrated loudness more than 0.8 LU off
target; true peak over the ceiling; clipped samples; DC over 0.002; presence + air (2 kHz and up) above 45 % of the
energy ("shrill"); for loops, the seam step larger than the clip's own 99.9th-percentile sample step, the 10 ms RMS at
the seam outside 0.25 to 4 times the median, or the envelope repeating faster than every 2 s with an autocorrelation
prominence over 0.35 (unless it is the mechanism's declared rhythm: a wheel's turn, a toss, a drum bar). Each clip also
gets a spectrogram PNG (waveform, RMS envelope, spectrogram; loops drawn with the first second again after the seam),
and the report lists the vanilla reference clip's numbers next to ours. All 55 pass.

## 4. Building

```powershell
# sounds + Windows bundle (first run creates the Unity project E:\PandabornDev\unity\PandabornSounds)
powershell -ExecutionPolicy Bypass -File tools\build_sound.ps1
# Mac bundle (E: editor copy with Mac Build Support, project E:\PandabornDev\unity\PandabornSounds-mac)
powershell -ExecutionPolicy Bypass -File tools\build_sound.ps1 -SkipSynth -Mac
#   -Only Bell,Clapper  re-synthesize only ids containing these   -SkipSynth  reuse the WAVs in the project
# sounds only (WAVs, PNGs, report), no Unity
E:\PandabornDev\tools\venv\Scripts\python.exe -I src\pipeline\sound\build_sounds.py
# the vanilla reference (once per game update; stays on E:)
E:\PandabornDev\tools\venv\Scripts\python.exe -I src\pipeline\sound\vanilla_extract.py
E:\PandabornDev\tools\venv\Scripts\python.exe -I src\pipeline\sound\vanilla_report.py
# the prototype mod (layered on the installed faction), and its test
powershell -ExecutionPolicy Bypass -File proto\sound\build.ps1
```

* Output: `E:\PandabornDev\build\sound\{wav,png,report.json,report.md,AssetBundles}`. Nothing heavy in git.
* The Unity project is minimal: only the built-in `audio`, `assetbundle` and `jsonserialize` modules (no render
  pipeline, no shaders, nothing downloaded). The script writes `ProjectSettings\ProjectVersion.txt` before Unity first
  opens the folder: without it Unity treats the folder as a new project and replaces the manifest with its default
  template (two dozen registry packages; the first build did exactly that and spent 6 minutes compiling them).
* The builder (`src/unity/PandabornSounds/Editor/PandabornSoundsBuilder.cs`) sets the import settings, removes clips that
  are no longer in the spec, builds `pandabornsounds_win` (StandaloneWindows64) or `_mac` (StandaloneOSX), chunk-based
  compression, strict mode, and deletes Unity's folder-manifest bundle (any non-`.manifest` file in a mod's
  `AssetBundles` folder is loaded as a bundle).
* **Bundle rules** (as for look and plants): keep the built name; exactly one enabled mod may ship `pandabornsounds`
  (two copies crash every game on load). `proto/sound/build.ps1` refuses to build if the installed faction already ships
  it. Ship the `.manifest` text file next to each bundle: the game skips `*.manifest`, and it lists the clips (for the
  validator, below).

## 5. The bundle

| | `pandabornsounds_win` | `pandabornsounds_mac` |
|---|---|---|
| Target | StandaloneWindows64 | StandaloneOSX (E: editor copy with Mac Build Support) |
| Size | 8,067,249 bytes | 8,062,281 bytes |
| Clips | 55, all `CompressedInMemory`, ADPCM, 48 kHz, preloaded; 54 mono, 1 stereo | same |
| Asset paths | `assets/pandabornsounds/resources/sounds/pandaborn/<clip>.wav` (the game indexes `sounds/pandaborn/<clip>`) | same |

`src/pipeline/sound/bundle_check.py` decodes each built bundle the way the game will (UnityPy + fmod) and compares it
with the WAVs: import settings, length, loudness and loop seams after encoding (`build_sound.ps1` runs it after every
build). It found one real thing: Unity's ADPCM pads every clip to a whole block of 64 samples. All loop lengths are whole
blocks (16 s, 18 s, 12.8 s... at 48 kHz), so their seams are untouched; one-shots are now padded with silence to a whole
block before encoding, so the decoded clip equals the source sample for sample. Result: 55 clips, 0 problems on both
bundles (`E:\PandabornDev\build\sound\bundle_check_pandabornsounds_win.json`, `..._mac.json`).

Vorbis was tried first (2.6 MB instead of 8 MB). ADPCM was kept: the game itself uses it for all of its sound effects
(Vorbis only for streamed music), it costs almost nothing to decode with many building loops running, and after encoding
every clip's loudness is within 0.1 LU of the source. Switch the builder to Vorbis only if size ever matters more than CPU.

## 6. In game

Runs with `tools/run_game_test.ps1 -RequestJson proto/sound/tests/sound.request.json -OnlyMods JigglyPanda.PandabornFactions
-ExtraMods E:\PandabornDev\build\proto\sound`: an Inkpaws game on Plains (75 s), then in the same launch a Folktails game
(the request's `then`). The harness probe `src/devharness/SoundProbe.cs` (request key `soundProbe`) looks every id up in
the game's `AudioClipService`, checks each clip is the very object in the loaded bundle, makes the game's own calls
(`PlaySound2D`, `PlaySound3D`, `BuildingSounds.ToggleSound`, `BuildingSelectionSound`/`BeaverSelectionSound.OnSelect`,
`GameUISoundController.PlayWonderLaunchSound`) and samples every `AudioSource` twice a second. The run is muted
(`AudioListener.volume = 0`), which makes Unity treat every voice as inaudible: `GetOutputData` reads zeros, so the proof of
playback is the clip's playback position moving between samples (`advanced`), plus mixer group, loop flag, pitch and
emitter.

| Run | What happened |
|---|---|
| `sound-1` | crashed while loading: "The AssetBundle ... pandabornsounds_win can't be loaded because another AssetBundle with the same files is already loaded". The catalogue lane had adopted the bundle into the faction 5 minutes earlier (`b24e571`), and the prototype shipped it too. Since then the prototype ships fragments only when the faction ships the bundle |
| `sound-2` | the game ran; the probe's clock started at `PostLoad`, so after a 67 s scene load every action fired at once, before the harness had placed the buildings; placing `PandabornSmokeKiln.Inkpaws` threw `NullReferenceException` in `WorkshopAnimationController.UpdateAnimatorState` (**a faction bug, reported to the orchestrator**; not a sound issue). Still: 18 of our clips seen playing, and the **Kite Windmill's loop started on its own** (`PowerGeneratorSounds`, wind): clip `Environment.Buildings.Loop.Pandaborn.KiteWindmill`, loop on, `Building` mixer, random pitch 0.946, emitter the windmill |
| `sound-3` | Inkpaws: completed, 0 errors from our mods, all 8 buildings placed, all batch-control tabs open; 32 of 32 ids known, every clip `CompressedInMemory`, `Loaded`, the same object as in `pandabornsounds_win` (55 sound assets). **Seen playing:** bell end and dawn, clapper, twitter, firecrackers, lantern rise (2D, `Environment`); bamboo tok, flume water, scoop wheel, water wheel, trip hammer, opera, smoke kiln, festival drum (3D from the Village Hall, `Environment`); the **Kite Windmill loop again on its own** (`Building`, looping); the **Village Hall click** (`UI.Buildings.Selected.Pandaborn.VillageHall`, from `BuildingSpec.SelectionSoundName` in the faction's own data); **colonist clicks** `Adult_Content_01` and `Child_Content_01` (`FactionSpec.SoundId = "Pandaborn"` merged by the prototype); the **wonder launch** `UI.Buildings.Wonder.PandabornSkyLantern` (`FactionWonderSpec`, faction data). Not seen: the seven workshop/attraction loops forced through `ToggleSound` (the probe fired before the buildings were placed; fixed for `sound-4`). Folktails (same launch, after the Inkpaws game): completed, 0 errors, **`soundsNotPlayed: Pandaborn` passed** (no clip with Pandaborn in its name played); its own sounds played as vanilla: `UI.Buildings.Wonder.EarthRecultivator` for the launch, `UI.Beavers.Common.Selected.*` for colonists, `UI.Buildings.Selected.DistrictCenter`, ambience, music, the district center fire and a Dance Hall loop with visitors; our bundle is loaded there too (55 assets) and unused |
| `sound-4` | **PASS, both games** (Inkpaws 67 checks, Folktails 15, 0 errors of any kind in either). Inkpaws: everything `sound-3` saw, plus **all eight building loops started through the game's own `BuildingSounds.ToggleSound` on the real placed buildings** (Steamer, Tea Roastery, Pickle Yard, Lantern Workshop, Hot Pot Hall: `Simmer`, Kite Windmill, Teahouse, Hot Spring Bath): each read its `LoopingSoundName` from the faction's data, played `Environment.Buildings.Loop.Pandaborn.<name>` looping, through `Building`, 3D, with the game's random loop pitch (0.909 to 1.088), from 52 s to the end of the run. 34 of our clips were seen playing in all; every one of the 32 ids is known and loaded from `pandabornsounds_win`. After the scripted stop at 58 s the loops' sources kept running at volume 0, as section 1 says the game does. Folktails, same launch: `soundsNotPlayed: Pandaborn` passed; its Grill and Dance Hall loops, colonist and building clicks and wonder launch played their vanilla clips |

## 7. For the catalogue lane

Everything below is data in `catalogue/` (yours) plus shipping the bundle. **Status:** items 1, 2, 4 and the launch
sound of item 3 were adopted in commit `b24e571` (the faction ships `pandabornsounds_win`/`_mac`, the validator reads
our bundles, every building below carries its sound); `sound_id` stays `"Common"` until the owner has listened to the
panda calls. Since then `proto/sound` carries blueprint fragments only (`*.optional.blueprint.json`: SoundId, and the
same values again for older faction builds) and ships no bundle while the faction does; its first run (`sound-1`)
crashed on load exactly because both shipped the bundle.

1. **Ship the bundle.** Add `E:\PandabornDev\build\sound\AssetBundles` to the `bundles` stage's `-BundleDirs`
   (`tools/pandaborn.ps1`); it copies `pandabornsounds_win` and `_mac` unrenamed. **The `_mac` twin is required, not
   optional**, as soon as any blueprint names one of our ids: a missing clip throws when it is played (section 1). Never
   enable a second mod that ships it (`proto/sound/build.ps1` leaves the bundle out while the faction ships it).
2. **The validator** (`tools/validate.py check_sound`) knows only built-in sounds and reports `SoundId` and
   `WonderLaunchSound` as errors. It should also accept clip names found in the mod's own `AssetBundles/*_win` bundles
   (UnityPy, already in the E: venv: every container path under `.../resources/sounds/`, clip = file name without
   `.wav`), and should check every `BuildingSpec.LoopingSoundName` (`Environment.Buildings.Loop.<name>`),
   `SelectionSoundName` (`UI.Buildings.Selected.<name>`) the same way. Do not ship the bundles' `.manifest` text files to
   help it: the game skips them, but the validator reads the bundle and its `.manifest` as one duplicated asset path.
3. **Faction** (`faction.toml`):
   ```toml
   sound_id = "Pandaborn"                                     # all eight UI.Beavers.Pandaborn.Selected.* sets exist
   [faction.wonder]
   launch_sound = "UI.Buildings.Wonder.PandabornSkyLantern"
   ```
   `sound_id` changes every colonist's click and the new-game panel: adopt it only after the owner has listened to the
   panda calls (the one kind of sound that cannot be judged from numbers); `"Common"` keeps the beaver chitter.
4. **Buildings** (`buildings.toml`, `set = { ... }`):

   | Building | `set` | Plays while |
   |---|---|---|
   | `PandabornSteamer` | `"BuildingSpec.LoopingSoundName" = "Pandaborn.Steamer"` | working |
   | `PandabornTeaRoastery` | `"BuildingSpec.LoopingSoundName" = "Pandaborn.TeaRoastery"` | working |
   | `PandabornPickleYard` | `"BuildingSpec.LoopingSoundName" = "Pandaborn.PickleYard"` | working |
   | `PandabornLanternWorkshop` | `"BuildingSpec.LoopingSoundName" = "Pandaborn.LanternWorkshop"` | working |
   | `PandabornSmokeKiln` | `"BuildingSpec.LoopingSoundName" = "Pandaborn.SmokeKiln"` | working |
   | `PandabornTripHammerMill` | `"BuildingSpec.LoopingSoundName" = "Pandaborn.TripHammer"` | working |
   | `PandabornKitchen`, `PandabornHotPotHall` | `"BuildingSpec.LoopingSoundName" = "Pandaborn.Simmer"` | working |
   | `PandabornBambooWaterWheel` | `"BuildingSpec.LoopingSoundName" = "Pandaborn.BambooWaterWheel"` | making power (it has `PowerGeneratorSoundsSpec`) |
   | `PandabornKiteWindmill`, `PandabornLargeKiteWindmill` | `"BuildingSpec.LoopingSoundName" = "Pandaborn.KiteWindmill"` | making power |
   | `PandabornScoopWheel` | `"BuildingSpec.LoopingSoundName" = "Pandaborn.ScoopWheel"` and `add = { PowerGeneratorSoundsSpec = {} }` | its node is powered (the stand-in pump has no other trigger; when the Water module drives the wheel from the current, it should start and stop the loop itself and the added spec goes) |
   | `PandabornTeahouse` | `"BuildingSpec.LoopingSoundName" = "Pandaborn.Teahouse"` | visitors inside |
   | `PandabornHotSpringBath` | `"BuildingSpec.LoopingSoundName" = "Pandaborn.HotSpring"` | visitors inside |
   | `PandabornOperaStage` | `"BuildingSpec.LoopingSoundName" = "Pandaborn.OperaStage"` | visitors inside |
   | `PandabornVillageHall` | `"BuildingSpec.SelectionSoundName" = "Pandaborn.VillageHall"` | clicked |

   Buildings not listed keep their basis's sound, which is the right sound for them (pumps, the treadwheel lift, the dew
   collector's grill stand-in should get `""` once it has its own model: a dripping collector should not sizzle).
5. Do **not** add `FireworkSpec` or `SpeakerSoundSpec` blueprints: both are global lists and would show in Folktails and
   Iron Teeth games. If the festival's lanterns should sound like lanterns instead of rockets, use an Inkpaws-only
   blueprint modifier on `Fireworks/Firework.CometRed` and `Firework.CometWhite` (the festival's `LanternFireworkIds`):
   `{ "FireworkSpec": { "TrailSound": "Environment.Pandaborn.LanternRise" } }` (not tested in game; it also changes those
   two fireworks in an Inkpaws player's own launcher, which fits the faction).

## 8. For the code lane

All of `ISoundSystem`, `AudioClipService`, `RootObjectProvider`, `MixerNames`, `IEmitterMap`, `WorkingHoursManager` and
`WorkingHoursTransitionedEvent` are public. The harness probe (`src/devharness/SoundProbe.cs`) made the same calls in
game: `PlaySound2D`, `PlaySound3D`, `AudioClipService.GetAudioClipNames`, `BuildingSounds.ToggleSound`,
`GameUISoundController.PlayWonderLaunchSound`, the selection components' `OnSelect` (section 6). The snippet below is
compile-checked against the 1.1.2.8 DLLs (netstandard2.1, a scratch project on E:):

```csharp
using System.Linq;
using Timberborn.CoreSound;        // MixerNames
using Timberborn.RootProviders;    // RootObjectProvider
using Timberborn.SingletonSystem;  // ILoadableSingleton, EventBus, OnEvent
using Timberborn.SoundSystem;      // ISoundSystem, AudioClipService, IEmitterMap
using Timberborn.WorkSystem;       // WorkingHoursManager, WorkingHoursTransitionedEvent
using UnityEngine;

public static class SoundIds
{
    public const string ShiftBellEnd = "Environment.Pandaborn.ShiftBell.End";    // 3 variants, 7.5 s
    public const string ShiftBellDawn = "Environment.Pandaborn.ShiftBell.Dawn";  // 2 variants, 8.5 s
    public const string NightClapper = "Environment.Pandaborn.NightClapper";     // 2 variants, 1.9 s
    public const string BambooTok = "Environment.Pandaborn.BambooTok";           // 3 variants, 1.2 s
    public const string FlumeWater = "Environment.Pandaborn.FlumeWater";         // loop 16 s
    public const string FestivalDrum = "Environment.Pandaborn.FestivalDrum";     // loop 9.6 s
    public const string Firecrackers = "Environment.Pandaborn.Firecrackers";     // 2 variants, 3.6 s
    public const string LanternRise = "Environment.Pandaborn.LanternRise";       // 3 variants, 2.2 s
    public const string RingtailTwitter = "Environment.Pandaborn.RingtailTwitter"; // 3 variants, 1.2 s
}

/// Plays Pandaborn sounds and never throws for a missing clip (the game throws "No sound files for: id"
/// when an id has no clip: a platform without its bundle, an old copy). Bind<PandabornSoundPlayer>().AsSingleton().
public class PandabornSoundPlayer : ILoadableSingleton
{
    private readonly ISoundSystem _soundSystem;
    private readonly AudioClipService _audioClipService;
    private readonly RootObjectProvider _rootObjectProvider;
    private GameObject _root;

    public PandabornSoundPlayer(ISoundSystem soundSystem, AudioClipService audioClipService, RootObjectProvider rootObjectProvider)
    {
        _soundSystem = soundSystem;
        _audioClipService = audioClipService;
        _rootObjectProvider = rootObjectProvider;
    }

    public void Load() => _root = _rootObjectProvider.CreateRootObject("PandabornSounds");

    public bool Has(string id) => _audioClipService.GetAudioClipNames(id).Any();

    /// Everywhere at full level; mixer from the id (Environment = the environment volume slider).
    public bool Play2D(string id, int priority = 10)
    {
        if (!Has(id)) return false;
        _soundSystem.PlaySound2D(_root, id, priority);
        return true;
    }

    /// From a building: full level within 2 units of the listener, silent beyond 10. Pass a child object of the
    /// building (not its root, where a click sets the UI mixer for every later sound), or let this set the mixer.
    public bool Play3D(GameObject emitter, string id, int priority = 30)
    {
        if (!emitter || !Has(id)) return false;
        _soundSystem.SetCustomMixer(emitter, id, MixerNames.EnvironmentMixerNameKey);
        _soundSystem.PlaySound3D(emitter, id, priority);
        return true;
    }

    /// One loop per GameObject (a second throws): use a child object on a building that already loops.
    public bool StartLoop(GameObject emitter, string id, string mixer = null)
    {
        if (!emitter || !Has(id)) return false;
        _soundSystem.LoopSingle3DSound(emitter, id, 128);
        _soundSystem.SetCustomMixer(emitter, id, mixer ?? MixerNames.BuildingMixerNameKey);
        return true;
    }

    /// Fades out over 3 s; the game keeps the source and restarts it on the next StartLoop.
    public void StopLoop(GameObject emitter, string id)
    {
        if (emitter && Has(id)) _soundSystem.StopSound(emitter, id);
    }

    /// One sound for many tiles (flumes): played at the nearest tile where map.IsEmitterAt(xy) is true, fading
    /// linearly to silence at `cutoff` tiles, like the vanilla water ambience. Create it once per game.
    public bool AddAreaSound(Transform parent, IEmitterMap map, string id, int cutoff = 10, string mixer = null)
    {
        if (!parent || !Has(id)) return false;
        _soundSystem.AddLargeAreaSound(parent, map, id, 50, cutoff, mixer ?? MixerNames.AmbientMixerNameKey);
        return true;
    }
}

/// The shift bell: once per transition per game (not once per Village Hall).
public class ShiftBellSounds : ILoadableSingleton
{
    private readonly EventBus _eventBus;
    private readonly WorkingHoursManager _workingHoursManager;
    private readonly PandabornSoundPlayer _sounds;

    public ShiftBellSounds(EventBus eventBus, WorkingHoursManager workingHoursManager, PandabornSoundPlayer sounds)
    {
        _eventBus = eventBus;
        _workingHoursManager = workingHoursManager;
        _sounds = sounds;
    }

    public void Load() => _eventBus.Register(this);

    [OnEvent]
    public void OnWorkingHoursTransitioned(WorkingHoursTransitionedEvent e)
    {
        // posted from WorkingHoursManager.Tick after the change, so AreWorkingHours is already the new state
        _sounds.Play2D(_workingHoursManager.AreWorkingHours ? SoundIds.ShiftBellDawn : SoundIds.ShiftBellEnd);
    }
}
```

Where each one goes:

| Sound | Module | Call | Notes |
|---|---|---|---|
| `ShiftBell.End` / `.Dawn` | Bell | `Play2D` on `WorkingHoursTransitionedEvent` (above) | only in Inkpaws games (`BellService.Active`); 2D because it is the day's signal, not a building's noise; the 3 and 2 variants never repeat back to back |
| `RingtailTwitter` | Ringtails | `Play3D(moonLoft)` when a Ringtail family arrives at a new Moon Loft; or `Play2D` as a Ringtail-only selection sound if the module ever replaces the faction-wide colonist call | the design's "red panda's twitter"; 3 variants |
| `NightClapper` | Ringtails | `Play2D` when the Ringtail shift actually starts (the bell, or the clamped start four hours after dawn / at nightfall), only if the village has Ringtails | when it coincides with the bell, play it about 2.5 s after the strike: the bell asks, the clapper answers |
| `FlumeWater` | Water | `AddAreaSound(root, flumeMap, FlumeWater, 10, MixerNames.BuildingMixerNameKey)` once per game; `flumeMap.IsEmitterAt` = a flume tile with flowing water | one voice for every flume (dozens of per-piece loops would phase and cost voices); a dry flume is silent, which is itself the "dry" cue |
| `BambooTok` | Water | `Play3D(pieceGameObject, BambooTok)` when water first reaches the end of a run, or a gate opens | rate-limit: at most one per run per fill and about one every 20 s game-wide, or it turns from charming to a ticking clock |
| `ScoopWheel` | Water (later) | `StartLoop` while the current turns the wheel, `StopLoop` when becalmed | replaces the stand-in's `PowerGeneratorSoundsSpec` trigger; then the catalogue drops that spec |
| `FestivalDrum` | Festival | `StartLoop(square child object, FestivalDrum)` from the gathering (15.5 h) to the end of the show, `StopLoop` after | 3D: heard when the player looks at the square |
| `Firecrackers` | Festival | `Play2D` once when the festival begins at dawn, and `Play3D(square)` as the gathering starts | |
| `LanternRise` | Festival | `Play3D(square)` with each rising lantern if the module draws its own lanterns; with comet fireworks, use the catalogue's firework modifier instead (section 7) | |
| Wonder launch | none | data (`launch_sound`) | |

## 9. What is not proven, and risks

* **How it sounds.** Nothing here was listened to. Every number (loudness against the vanilla clip of the same kind,
  spectrum, envelope, seam) is checked and the spectrograms were looked at, but character ("warm", "charming", "not
  tiring on the hundredth repeat") is a judgement for ears. Listen before adopting: `E:\PandabornDev\build\sound\index.html`
  plays every clip (loops on repeat) next to its spectrogram. The panda calls carry the most risk (a synthesized voice
  can sound like a toy); the bell, clapper, water and wheels the least.
* **Natural triggers.** In game the loops were started through the game's own `BuildingSounds.ToggleSound` (the exact
  call a working workshop, a visited attraction or a turning generator makes); a workshop actually producing, an
  attraction with real visitors were not reached in a 75 s test; the Kite Windmill in real wind was (runs `sound-2` and
  `sound-3`: its loop started on its own through `PowerGeneratorSounds`), and the vanilla Dance Hall's loop started with
  real visitors in the Folktails game, so both kinds of natural trigger work as read from the code.
* **Audible output.** The tests are muted, so Unity reports every voice as inaudible and `GetOutputData` reads zeros;
  playback is proven by the clip position advancing, not by measured output. Loudness and spectrum are proven offline
  on the decoded bundle (`bundle_check.py`).
* **Mac.** `pandabornsounds_mac` is built for StandaloneOSX and decodes correctly (`bundle_check.py`), but has not been
  loaded on a Mac.
* **Many buildings at once.** 3D loops are only audible within 10 units of the listener, so a town of Steamers does not
  stack; the priority (128) and Unity's voice limit decide what drops first, as for vanilla. Not measured with a large
  town.
* **Area sound for flumes** and the code-played sounds are only proven as clips that load and play; the modules that
  will call them are not written yet.

## 10. Notes for the design, from the sound side

* **One bell, heard everywhere, twice a day.** Play it 2D once per transition, not from every Village Hall (several
  districts would ring a chord). At -18 LUFS with a 7 s bloom it sits under the game's weather alerts (-17) and well
  under the music, so it marks the day without startling.
* **Call and response.** When Ringtails exist, the clapper answering the bell a breath later makes the shift change
  audible as *two peoples*, which no tooltip does. Without Ringtails there is only the bell.
* **The flume's sound is its status.** One area sound that exists only where water flows: a player hears a run go dry.
  The bamboo tok as a run fills is the "it works" moment of the first hour; keep it rare.
* **Ringtails share the faction's colonist calls.** `SoundId` is per faction, so Ringtails bleat like giant pandas. A
  red panda's twitter exists (`RingtailTwitter`) but only code can play it: as the arrival of a Ringtail family, or as a
  Ringtail-only selection sound replacing the faction-wide call.
* **Not Japanese-coded.** The bamboo knock is described and used as a flume sound, not as a garden deer-scarer; the opera
  phrase is pentatonic plucked string with a wooden clapper (Sichuan opera's own instruments are percussion-led; a gong
  was left out to keep it quiet).
