# Pandaborn - Factions: the Inkpaws

A new playable faction for [Timberborn](https://store.steampowered.com/app/1062090/Timberborn/).

The Inkpaws are giant pandas. They grow bamboo, rice and tea, and they lead water downhill in open bamboo flumes
where beavers would dam it. They work a short day and work it well. When the afternoon bell rings they put down
their tools, and the Ringtails, the red pandas of the Night Watch, take over the village until dawn.

Unlocked from the start. Needs no other mods. Folktails and Iron Teeth are left exactly as they are.

> **State of this repository, 2026-11-25.** Nothing is published yet. The manifest still says `0.0.1`, a
> development build. Every feature below carries its real state: what runs in the installed build, what is proven
> only on test copies, and what is still being tested. The path to a release is in [docs/RELEASE.md](docs/RELEASE.md).

## How the Inkpaws play

**The first hour is the game you know.** Water pump, gatherer, lumberjack, a Farmhouse. The first crop on the list
is shoot bamboo, which is edible raw and the fastest food there is. Levees, dams and floodgates keep their names and
do what they always did.

**Poles instead of planks.** Timber bamboo is a fast tree, and cut bamboo is already a pole, so it needs no mill.
A Pole Mill splits logs into poles for the first days and for long droughts.

**The afternoon bell.** The bell is the game's own working-hours control. Rested pandas are quick pandas: the
shorter the day, the faster Inkpaws work and walk, and from twelve hours to sixteen the work done comes out the
same. So the choice is yours: a long day, or a free afternoon for a nap in a hammock and a cup at the Teahouse.
Longer days still are allowed. They only remove the bonus.

**Every kind of land has a use.** Rice in flooded fields. Bamboo, cabbage and persimmons on green, moist ground.
Tea and Sichuan pepper on the brown, dry ground every other faction leaves empty.

**Lead the water.** A flume is an open bamboo aqueduct one tile wide. Water runs one way along it, level or
downhill, and the ground beside it stays moist six tiles to each side. A Scoop Wheel lifts water out of a current
with no workers. A Paddy Spout holds a rice field at a shallow depth.

**Two peoples, one village.** Build a Moon Loft and a Ringtail family moves in: two adults and a kit. Ringtails work
from the bell to dawn in their own night posts. They build, carry and gather while the Inkpaws sleep. A village that
never builds a Moon Loft is still complete.

**A festival and a flowering.** Once a cycle the village can take a day and a night off for the Lantern Festival.
And once in several cycles one of the two bamboos flowers, bears seed for three days and dies back. The game tells
you a full cycle ahead.

The guide for after the first hour is [docs/PLAYER_GUIDE.md](docs/PLAYER_GUIDE.md).

## What is in the build

About 170 buildings: the Folktails' staples in the Inkpaws' own look, plus nearly sixty of the faction's own,
almost all on new models. Seven new plants. New goods for the kitchen, the tea table and the lanterns, and poles
and cured poles, which are the Inkpaws' names for planks and treated planks. All of it is generated from the files
in `catalogue/`; the full lists are in [docs/CONTENT.md](docs/CONTENT.md).

"Proven" means a run of the real game showed it, and the run is named in `docs/tech/`.

### In the installed build, proven in game

| Feature | Notes |
|---|---|
| The Inkpaws as a faction | Own panda bodies for adults and cubs, five adult and three cub coats, portraits, banners and tail marks. Folktails and Iron Teeth keep their meshes, coats, buildings and text with the mod enabled |
| The Inkpaws' look | Dark timber, pale plaster, grey clay tile, bamboo, lattice windows that glow at night. Applied in code to Inkpaws games only; tested with the author's 35 mods enabled |
| The afternoon bell | Rested Inkpaws work and walk faster on a shorter day. The bonus multiplies with well-being, is fixed each dawn, and shows on the working-hours panel. A bell rings at the end of the day and at dawn |
| Bamboo twice, and poles | Shoot bamboo as a crop, timber bamboo as a tree that yields poles, the Pole Mill |
| Seven plants on three kinds of land | Shoot bamboo, timber bamboo, cabbage, rice, tea, Sichuan pepper, persimmon. A test terrace of 346 plants stayed healthy with each on its own kind of ground |
| The kitchen | Steamed shoots, pickles, steamed rice, hot pot. Roasted tea, served at the Teahouse |
| Afternoon places | Hammock, Nap Platform, Teahouse, Slide and Swing, Kindergarten, Ink Studio, Hot Spring Bath |
| The Ringtails | The first Moon Loft brings a family. Night Builders' Post, Night Courier Post, Night Gatherers' Post. Kits are raised while night jobs are open. A red panda body, five coats, their own names. Survived a 13-day run with a save and reload |
| Names | "Le Le (Joy)", "Xing He (River of stars)". Ringtails get star, fruit and spice names |
| Panda words | In an Inkpaws game the interface says Inkpaw, cub and panda where the game says beaver and kit. Other factions keep the game's text |
| Hats and baskets | Paddy farmers wear a conical hat, gatherers a back-basket |
| Wooden Oxen | The faction's bots, on their own ox body. Stronger than a panda, and they wear out |
| Sounds | 32 sounds made for the faction: the bell, the watchman's clapper, flume water, workshop loops. They load and play in tests. Nobody has listened to them yet |
| Safe to break | Every code feature checks the game before it loads. If a game update breaks one, that feature switches off, the game says so once, and the building behaves like its vanilla cousin |

### Switched on, proven on test copies, not yet through the install gate

These work in game on private copies of the build. The shared build takes them only after the gate run described in
[docs/RELEASE.md](docs/RELEASE.md).

| Feature | Proven | Still open |
|---|---|---|
| Flume, Flume Corner, Drop, Bridge, Bridge Span, Flume Gate | One-way flow, sealed sides, a crossing, the badwater shut-off, save and reload | The badwater shut-off was proven in the prototype and not re-run in the shipped module |
| Paddy Spout, Scoop Wheel, Cistern Tap, Dew Collector | Spout depth and cascade, the wheel in a current, the tap with a worker, dew in fair weather and drought | The Scoop Wheel on the catalogue's own template (its gate run did not finish) |
| Lantern Festival | Call, day off, gathering and dancing on the square, fireworks, festive spirit, Tradition, save and reload mid-show | A real pump crew, two districts, a large village. The rising lanterns are the game's firework comets until their own art is finished |
| Great Flowering | Forecast, flowering, seed harvest, the nine-day rest, replanting, the setting | Timber bamboo's flowering harvested by lumberjacks; the buds with the shipped bundle and the module together |

### In testing

Built, placed and finished in test runs, but not yet shown working the way a player would use them:

* The Trip-Hammer Mill, and with it rice flour, sweet rice balls and bamboo seed cakes.
* The Treadwheel Lift (it still stands on a stand-in model).
* The Opera Stage. For now it is an ordinary attraction on a stand-in model.
* The Dry-Stone Wall keeping a tea slope dry.
* The Inkpaws tutorial from start to finish.
* The Ox Workshop, the Memorial Arch, the Great Sitting Panda and the Sky Lantern in a played game. Their models are in
  and the Sky Lantern's rise plays; no test has reached them by playing.
* A village living twenty days or more on each difficulty. Balance numbers are a first pass.
* Mac. The Mac files are built and checked on Windows. Nobody has run them on a Mac.

### Not in this version

* The Star Tower. It is decided and modelled: a Ringtail night post that makes science from the night sky. It stays
  out of the toolbar until its data is ready.
* Panda voices when you select a colonist. They are made, and stay off until the owner has heard them.
* Translations. The faction's own text is English only.

## Install

**Steam Workshop or mod.io:** not published yet. The links will be here.

**From Releases:**

1. Download `PandabornFactions.zip` from [Releases](../../releases).
2. Unzip it into `Documents\Timberborn\Mods\`. You should end up with `Mods\PandabornFactions\manifest.json`.
3. Enable **Pandaborn - Factions** in the game's mod manager.
4. Start a new game and choose the Inkpaws.

Use one copy only. If the Workshop copy and a local copy are both enabled, the mod runs the first, parks the second
copy's asset bundles and tells you. Other mods may not cope with the duplicate (see below).

Game version: Timberborn 1.1. Built and tested on 1.1.2.8.

## Works with

| Mod | State |
|---|---|
| No other mods | Tested. This is the main test setup |
| [Pandaborn - Panda Reskin](https://steamcommunity.com/sharedfiles/filedetails/?id=3838695858) 7.0.0 | Works, nothing breaks. The Reskin treats the Inkpaws as an unknown faction: it swaps their portraits for its Folktails ones and gives Ringtails fur in the giant panda's pattern. A small Reskin update that leaves the Inkpaws their own coats and portraits is written and tested, and goes out with this mod |
| ChooChoo, KnatteAnka's Staircase and the other 33 mods on the author's machine | An Inkpaws game followed by a Folktails game ran clean with all 35 enabled |
| TimberCommons | The flumes ran the same with it and without it |
| TimberUi | Crashes if any mod is enabled twice (a local and a Workshop copy). That is true with or without this mod. Keep one copy |
| Mod Settings | Not needed. This mod has no settings page |
| Harmony | Not needed and not used |

A wider compatibility audit is in progress. Its results will be added here and to the store pages.

## Settings

* **The afternoon bell** is the game's working-hours slider.
* **The Great Flowering** can be set to normal, rare or off, per save, from the line under the top bar or from any
  bamboo's panel.
* **The festival** can call itself when the village is stocked. The switch is on the Festival Square's panel.

There is nothing to configure outside the game.

## Saves

* Adding the mod to an existing game is safe. Nothing changes for Folktails or Iron Teeth.
* **Removing the mod breaks Inkpaws saves.** A game played as the Inkpaws needs the mod to load.
* If one feature is switched off, by a game update or on purpose, the save still loads. Ringtails load as Inkpaws
  and keep their names, homes and needs. Flumes become solid blocks and flood nothing. Festival and Flowering state
  waits in the save and picks up when the feature is back.
* Ids are frozen (`catalogue/ids.lock.json`). A later version does not rename what a save refers to.

## For modders

### Layout

| Path | Contents |
|---|---|
| `catalogue/` | The source of truth for all content: faction, characters, buildings, goods, needs, recipes, plants, text, the id lock |
| `src/gen/` | The generator: catalogue to blueprints, collections and localization, deterministic, with provenance |
| `src/code/` | Runtime C#. One small bootstrap DLL, shared specs and core, then one module per feature, each with a `FEATURE.md` listing the game API it touches |
| `src/pipeline/`, `art/` | Code that makes the models, textures, icons and sounds. One folder per model and plant |
| `src/unity/` | Sources for the asset bundles (materials, shaders, attachments, sounds) |
| `src/devharness/` | A dev-only mod that drives the game for automated tests. Never shipped |
| `mod/PandabornFactions/` | Hand-made files only: manifest, sprites, coat textures |
| `schema/` | Every game spec class and field per game version, dumped from the game for the validator |
| `tools/` | Build, validate and test scripts |
| `tests/scenarios/` | In-game test requests |
| `proto/` | Prototypes and their test probes |
| `docs/` | Design, content, engineering rules, and one technical note per subject in `docs/tech/` |

### From catalogue to mod

```
catalogue/*.toml + catalogue/text/*.json
        |  generate   (src/gen: blueprints, collections, loc, stamped with source and hash)
        v
generated data  +  mod/PandabornFactions  +  models  +  code modules  +  asset bundles
        |  assemble
        v
staging folder
        |  validate   (every key and field against the game's own schema, asset paths, ids, economy rules)
        |  gate       (a dev copy places and finishes every building in a real game, runs recipes, zero errors)
        v
install  ->  Documents\Timberborn\Mods\PandabornFactions
```

Nobody writes a blueprint by hand. A building is one line in `catalogue/buildings.toml`, and its numbers are in
`catalogue/building_stats.toml`. An item that waits for a code module stays out of the build until that module
ships, so nothing in the toolbar promises what it cannot do.

### Build

One command, from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 all
```

`all` runs `pin`, `models`, `generate`, `code`, `bundles`, `assemble`, `validate`, `gate` and `install`. Each stage
also runs by name. `package` applies the release rules and writes the zip. `-NoCode` builds the data-only fallback.

You need Timberborn 1.1.2.8, the .NET SDK 9, Python 3.10, and for art and bundles Blender 4.5 LTS and Unity
6000.5.11f1. The scripts expect a build drive at `E:\PandabornDev`; paths are parameters where the scripts take them.

### What lives on the build drive, not in git

Heavy and derived files stay out of the repository: built models (`.timbermesh`), asset bundles, Unity projects,
the generated mod, test output, and the reference copies of the game's blueprints and decompiled code. The two panda
bodies come from the Reskin's release. The build pulls each of them in at `assemble`.

### In-game tests

`tools\run_game_test.ps1` builds the dev harness, starts the game on a hidden Windows desktop, plays a scripted
request, and writes `result.json`, logs and screenshots. No window appears and the mouse and keyboard are left
alone. One test runs at a time. A run switches other mods off for itself and restores every flag afterwards. It
never touches saves that are not its own.

```powershell
powershell -ExecutionPolicy Bypass -File tools\run_game_test.ps1 -Faction Inkpaws -Map Plains -RunSeconds 60
```

### No game files

This repository holds no file from Timberborn: no decompiled code, no vanilla blueprint, texture, mesh or sound.
The generator reads your own copy of the game. It also holds no other mod's assets.

### Read next

| Read | For |
|---|---|
| [docs/DESIGN.md](docs/DESIGN.md) | The design and the reason for each decision |
| [docs/CONTENT.md](docs/CONTENT.md) | Every good, plant, building and need |
| [docs/ENGINEERING.md](docs/ENGINEERING.md) | Id rules, data rules, code rules, the tests a release needs |
| [docs/PLAYER_GUIDE.md](docs/PLAYER_GUIDE.md) | How to play the faction. Its tables are written from the catalogue by `tools/docs/guide_tables.py` |
| [docs/RELEASE.md](docs/RELEASE.md) | The release checklist and where each item stands |
| [catalogue/README.md](catalogue/README.md) | How to add or change content |
| [src/code/README.md](src/code/README.md) | How the code loads and how to add a module |
| [catalogue/text/STYLE.md](catalogue/text/STYLE.md) | How the in-game text is written |
| [CHANGELOG.md](CHANGELOG.md) | What changed |

## Credits and AI disclosure

Made by JigglyPanda.

This mod is AI-generated. Generative AI (Claude, by Anthropic) wrote the code, the build tools and the art
pipeline. The models, textures, icons and sounds are produced by that code: meshes are built by scripts, textures
are painted procedurally, sounds are synthesized. None of them is an AI image or audio model's output, and none is
taken from the game or from another mod. Portraits are 3D renders of the mod's own models. The in-game text and
the colonist names were also written by Claude. The names have not yet been checked by a native speaker of
Mandarin.

The panda bodies come from the author's earlier mod,
[Pandaborn - Panda Reskin](https://steamcommunity.com/sharedfiles/filedetails/?id=3838695858), which was made the
same way.

Timberborn is © Mechanistry. This is an unofficial fan mod.

## Licence

No licence file yet. The Reskin repository has none either, so there was nothing to match, and one will not be
invented here. Until the author chooses, the usual default applies: you may read the code and play the mod; ask
before you reuse the code or the art elsewhere.
