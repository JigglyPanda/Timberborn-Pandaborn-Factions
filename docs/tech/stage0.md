# Stage 0: the mechanisms the plan rests on, checked in game

Game 1.1.2.8. Prototype: `proto/stage0` (manifest Id `JigglyPanda.PandabornProtoStage0`), layered on the installed
main mod with `-ExtraMods`; it carries the whole runtime code (`src/code`, built into it with `-p:ModOut`) and a
dev-only probe (`proto/stage0/src`) that writes `stage0.json` next to the harness's `result.json`.

## How each check was measured

* **When blueprints are first read.** The probe registers a blueprint-modifier provider that adds nothing.
  `SpecService` asks every provider exactly once per blueprint, when that blueprint is first deserialised (lazily), so
  the provider logs every first read, the game class that caused it (first frame outside the blueprint system), and
  whether `FactionBlueprintModifierProvider` was already initialised (that happens in `FactionService.Load`).
  `BlueprintSourceService` then shows, for each spec, whether "Faction modifier" is among its sources.
* **Faction modifiers** (in `proto/stage0/mod/Factions/Pandaborn/Faction.Inkpaws.blueprint.json`, `BlueprintModifiers#append`):
  `Good.Plank` renamed "Pole/Poles", icon `Sprites/Pandaborn/Stage0/PolesIcon` (a mod sprite), `Weight` 3 -> 2;
  `Need.Beaver.Campfire` `DailyDelta` -0.1 -> -0.05; `LumberMill.Folktails` cost Log 15 -> Plank 4; `Grill.Folktails`
  recipes without spadderdock; `BonusType.MovementSpeed` `MaximumValue` 2.0 -> 2.66; every vanilla `Tutorials.*`
  switched off; the stage-0 tutorial switched on. All modifier files are `*.optional.blueprint.json` at paths with no
  base blueprint (see "Modifier files must not be indexed").
* **Plank tree**: `PandabornStage0Bamboo.Inkpaws`, Birch with `CuttableSpec.Yielder.Yield = Plank x2`, in an
  Inkpaws-only collection. The probe spawns eight grown next to a lumberjack flag and marks them; a small pile is set to
  planks; the Lumber Mill is placed unfinished (its Inkpaws cost is planks).
* **Bootstrap and custom spec**: `PandabornBellSpec` and `PandabornNamePoolSpec` merged into the Inkpaws adult/child
  templates; `PandabornBellSettledMarkerSpec` on `PandabornStage0Teahouse.Inkpaws` (a Campfire copy).
* **Bell**: the probe sets the slider to 16, 14 and 12 and relocks the bell at once (dev hook), logging every adult's
  `WorkingSpeed`/`MovementSpeed` multipliers, `Worker.WorkingSpeedMultiplier`, `WalkerSpeedManager.GetWalkerBaseSpeed()`
  and the distance actually walked per in-game hour while moving; then sets 16 without relocking to check the dawn lock;
  then tabulates multipliers with wellbeing 20 and 80 emulated (the same bonus sums the wellbeing tiers add).

## Results

Runs (all in `E:\PandabornDev\build\test\`): `s0-inkpaws-1` (Inkpaws, everything on; reload with Bell and Names
forced off), `s0-inkpaws-2` (same, plus a plank-cost building site and the tutorial panel shown), `s0-folktails-1`
(Folktails with the prototype installed), `s0-inkpaws-5` (Inkpaws with Bell failing its API check and Names forced off;
reload with everything on; by then the main mod had its own catalogue, `-3` and `-4` crashed on tutorial pitfalls). Evidence: each run's `stage0.json`, `s0_*.png`, `Player.log`.

### 1. `FactionSpec.BlueprintModifiers`: works, early enough for everything but the faction file itself

**When modifiers apply.** Of 1,203 blueprints read in a new Inkpaws game, exactly **3 are read before** the faction's
modifiers are initialised: the faction blueprints themselves (`FactionSpecService.Load`). The very next read
(`Configurations/TickTime`, by `TickService.Load`) already has them. So every other kind of blueprint takes faction
modifiers: goods (first read by `GameGoodFilter.Load`), needs (`FactionNeedService.Load`), templates and buildings
(`TemplateCollectionService.Load`), bonus types (`BonusTypeSpecService.Load`), wellbeing tiers, recipes, tutorials
(`TutorialService.GetConfigurations`). The order follows from singleton creation order (dependencies first): everything
that reads specs per faction depends, directly or not, on `FactionService`. On load from a save the same order holds
(`FactionService.Load` reads the faction id from the save first).

| Modifier (Inkpaws only) | Inkpaws game | Folktails game (same mods) |
|---|---|---|
| `Good.Plank`: name, plural, icon (a mod sprite), `Weight` 3 -> 2 | "Pole"/"Poles", our icon in the top bar, yield panel and stock; weight 2; sources `[Game, Faction modifier]` | "Plank"/"Planks", vanilla icon, weight 3, sources `[Game]` |
| `Need.Beaver.Campfire` `DailyDelta` -0.1 -> -0.05 | -0.05 in `FactionNeedService` and on every colonist's `NeedManager` | -0.1 |
| `LumberMill.Folktails` cost Log 15 -> Plank 4 | Plank x4 | Log x15 |
| `Grill.Folktails` recipes minus spadderdock | GrilledPotato, GrilledChestnut | all three |
| `BonusType.MovementSpeed` `MaximumValue` 2.0 -> 2.66 | 2.66 (and a colonist reached 2.261, above the vanilla cap) | 2.0 |
| 18 vanilla `Tutorials.*` switched off, ours switched on | see check 4 | vanilla tutorials intact (stages built), ours inert (0 stages) |

**Save/load.** The save stores good, need and template ids, never the merged spec. After reload (`s0-inkpaws-1/reload`)
every modifier was in force again (Pole, -0.05, Plank x4, cap 2.66), with no loading issue. Goods keep their vanilla id
`Plank`, so stock, costs and recipes in saves are untouched.

**Modifier files must not be indexed.** `SpecService.Load` indexes every `*.blueprint.json` of every mod by its
top-level spec keys before any modifier is applied. A modifier file named like a normal blueprint and holding a partial
`GoodSpec` would therefore also become a second, broken good in **every** game. The prototype names every modifier file
`<name>.optional.blueprint.json` at a path with no base blueprint: `BlueprintFileBundleLoader.GetBundles` drops groups
made only of optional files (never indexed), while the faction's `AssetRef` still loads it by its exact path
(`Modifiers/Pandaborn/Stage0/Good.Plank.optional.blueprint`). Verified: no ghost good, need or tutorial in either faction.

**Decision this enables: poles can be the vanilla `Plank` under a new name, for Inkpaws only.** Name, plural, icon and
weight all change; every vanilla and third-party building that costs `Plank` keeps working in an Inkpaws game; the
Folktails game is untouched. Limits: the good's id, `GoodType`/stockpile class and goods-group stay vanilla unless
modified too (they can be); the model shown on a carried or piled good follows `VisibleContainer`/
`StockpileVisualization` (a modifier can point them at other vanilla containers, not at new models); the loc keys are
ours. The same mechanism retunes needs, costs, recipe lists, bonus types and tutorials per faction.

### 2. A tree that yields planks: works with lumberjacks, piles, the yield panel and haulers

`PandabornStage0Bamboo.Inkpaws` (Birch with `Yield: Plank x2`): the vanilla lumberjack cut all eight trees in under a
day, carrying `Plank` ("Poles") to its flag; the planks went on to a small pile set to planks (16 in the pile at the end
of `s0-inkpaws-1`); the tree's panel shows the yield with the poles icon and amount 2 (`s0_bamboo_yield.png`). No code
assumes the yield is `Log`, with two side effects: the lumberjack's chipped-teeth effect (`YieldRemoverWorkplaceEffectsSpec`,
`YieldGoodId: Log`) and the cutting-success chance bonus (`GoodId: Log`) do not apply to a plank yield (harmless or
pleasant). A good stack of planks left on the ground shows no model (`GoodStackModel` has models for Log, Barrel, Box,
Bag only). **Builders** (`s0-inkpaws-2`): the vanilla Campfire, costed at Plank x4 for Inkpaws by a modifier and placed as a site, got its 4 planks from the lumberjack flag and was finished within four in-game hours. Folktails games cannot see the tree (it is in an Inkpaws-only collection).

### 3. Custom spec through the bootstrap; module forced off; save carried

* `PandabornBellSpec` + `PandabornNamePoolSpec` on `InkpawAdult.Inkpaws`, `PandabornBellSettledMarkerSpec` on
  `PandabornStage0Teahouse.Inkpaws`. With the modules on, every Inkpaw adult had `BellRestedBonus` and `FactionNamer`, the
  teahouse had `BellSettledMarker` (it posted the bell's suggestion when finished). Specs, Core, Bell and Names were all
  loaded from `.bin` files by the bootstrap in 1.3 s, Bindito found their configurators and `SpecTypeCache` registered
  their specs: **late loading from the mod starter needs no special arrangement**, because the game builds each
  context's container and `SpecTypeCache` only after every mod starter has run, and both scan `AppDomain.GetAssemblies()`.
* Reload with `force-off: Bell, Names`: the game loaded the save without issues; the templates still carried the specs
  (Specs is always loaded) but no Pandaborn component was attached; colonists had vanilla speed (1.0/1.0) and kept
  their saved names; the teahouse was a plain campfire; the player got one notice per feature off (toast and log), and
  `Core.Notices` recorded it so it is not repeated in that save. The `Pandaborn.Store` singleton loaded from the save
  with the Bell (`locked=16;suggested=1`) and Names entries and kept them while off. A save made in that state
  (`s0-inkpaws-2/reload/resave.timber`, `world.json`) still holds `"Pandaborn.Store":{"Entries":["Bell|1|locked=16;suggested=1", "Core.Notices|1|...", "Names|1|..."]}`, so turning the module back on finds its state. Turning features on for a save
  that never had them, and the "game changed" path: `s0-inkpaws-5` (`s0-inkpaws-3`/`-4` crashed on the two tutorial
  pitfalls in check 4, not on the code). First launch with `simulate-missing-api: Bell` and `force-off: Names`: the
  bootstrap kept Bell off ("game API changed: 1 missing, e.g. type Timberborn.PandabornSimulated.MissingType") without
  loading it, the game started normally, colonists had vanilla speeds and vanilla names, and the player got one notice
  per feature ("...is switched off because this game version changed something it relies on..."). Reload of that save
  with everything on: no loading issue; the Bell locked the current 16 h, every Inkpaw got its rested component, the
  teahouse its marker (the suggestion is posted once, also when a marker building is already standing on load); colonists
  kept their saved vanilla names (new ones would get Inkpaw names); the off-state notices were not repeated.

### 4. Faction tutorial route: works with data alone

Giving Inkpaws `StartingFactionSpec` turns the tutorial system on for them; 18 faction modifiers set every vanilla
`TutorialSpec` to `Stages: []`, `RequiredTutorialIds: [PandabornNever]` (never starts, builds no steps), and one
modifier switches on our dormant `Tutorials.PandabornStage0` (its base file has no stages and an unmeetable requirement,
so it is inert in Folktails and Iron Teeth games). In game the Inkpaws tutorial started at once with stage
"PandabornStage0.Grove" (our intro text; step "place a lumberjack flag", achieved), `StartNextStage` moved it to
"PandabornStage0.Afternoon" (step "Set working hours to 12", achieved when the probe set 12 h), and on reload the game
fast-forwarded it and marked it finished. Note: the player's own "disable tutorial" setting hides the panel (it was on
on this machine). In `s0-inkpaws-2` the probe switched that setting off for two in-game hours and back: the tutorial panel showed our title "First days in the grove 1/1" (`s0_tutorial_stage1.png`), and the setting was restored to its prior value.

Constraints: vanilla step types only (place/finish/connect buildings, mark trees or plantables, select an entity, set
working hours, unlock or accumulate science, camera and speed); no "have N of a good" step without code (a small
`IStepDeserializer`). `BuildingTutorialStepSpec` needs each template to have exactly one toolbar button in the faction, and **a step that names a template the faction does not have crashes the game at load** (`BuildingService.GetBuildingTemplate` throws inside `TutorialService.Load`; run `s0-inkpaws-3`, after the main mod stopped listing `Buildings.Folktails`). Every stage blueprint of the Inkpaws tutorial must therefore be validated against the faction's templates, by the generator or the validator; the prototype's first stage now uses `MarkTreesTutorialStepSpec`, which names no template.
`StairsUnlockedTrigger` throws `TemplateMappingException: No template found with name 'Stairs.Folktails'` at load in a starting faction that has no such template (verified, run `s0-inkpaws-4`, once the main mod stopped listing `Buildings.Folktails`); the fix is `"BackwardCompatibleTemplateNames": ["Stairs.Folktails"]` on `Stairs.Inkpaws` (the prototype merges it in).

A concrete proposal for the Inkpaws tutorial, with these rules as validator requirements: `docs/tech/tutorial.md`.

### 5. Per-faction names: an `IEntityNamer` decorator, no Harmony

`NamedEntity` asks the namer with the highest `EntityNamerPriority` once, when a colonist first gets a name, and saves
the name per colonist. `Pandaborn.Names` decorates `PandabornNamePoolSpec` (on the Inkpaws adult and kit templates) with
a namer of priority 30 (vanilla 20) that draws from its own loc entry without repeats. All 13 starting Inkpaws were
named from it, glosses included: "Yu Yu (Rain)", "Le Le (Joy)", "Qing Qing (Clear Water)"; names showed verbatim in the
colonist panel. With the module off, existing names stay (saved by the game) and new colonists get vanilla names.
Avoid `#` plus six hex digits (tints the colonist) and `<...>` (rich text) in names.

### The afternoon bell (`Pandaborn.Bell`), measured

Run `s0-inkpaws-1`, nine Inkpaw adults (fresh colony, wellbeing about 0, so no other bonus). Multipliers are the
colonists' own `BonusManager` values; `Worker.WorkingSpeedMultiplier` (what build, cut, plant and production executors
use) and `WalkerSpeedManager.GetWalkerBaseSpeed()` (tiles per second) matched them every sample.

| Day locked at | Working speed | Walking speed (base 2.7 tiles/s) | Walked distance per in-game hour while moving, relative to 16 h |
|---|---|---|---|
| 16 h | x1.00 | 2.70 | 1.00 (31.7, 0.34 h of movement sampled) |
| 14 h | x1.165 | 3.15 | too few samples (0.06 h) |
| 12 h | x1.33 | 3.59 | 1.38 (43.8, 0.47 h sampled; expected 1.33, the difference is route noise) |

* **Dawn lock works.** Slider moved 12 -> 16 at 13:00: the bonus stayed +33% for the rest of the day, the panel read
  "Rested +33%; tomorrow +0%", and at dawn of day 2 it dropped to +0%. Slider moved 16 -> 12 after dawn: "Rested +0%;
  tomorrow +33%" (`s0_slider16_before_dawn.png`, `s0_hint_tomorrow.png`).
* **Shown** under the working-hours panel and on the colonist's panel ("Rested (12 h day): working +33%, walking
  +33%"), and the vanilla wellbeing bonus totals include it (+33% / +33%, `s0_hint_12h_colonist.png`).
* **Suggestion** posted once, as a toast and in the notification log, when the test teahouse (settled marker) was
  finished; recorded in the store so it never repeats.
* **Folktails**: bell inactive, no rested component on any beaver, multipliers vanilla (`s0-folktails-1`).
* **Module off**: vanilla multipliers 1.0/1.0 after reload with `force-off: Bell`.

**It multiplies** (balance model requirement). Wellbeing emulated on four colonists by adding the same sums the adult
wellbeing tiers add (wellbeing 20: working +0.8, walking +0.15; wellbeing 80: working +2.8, walking +0.7):

| | 16 h | 14 h | 12 h | 12 h / 16 h |
|---|---|---|---|---|
| Wellbeing 20, working | 1.800 | 2.097 | 2.394 | 1.33 |
| Wellbeing 20, walking | 1.150 | 1.340 | 1.530 | 1.33 |
| Wellbeing 80, working | 3.800 | 4.427 | 5.054 | 1.33 |
| Wellbeing 80, walking | 1.700 | 1.981 | 2.261 | 1.33 (above the vanilla cap, see below) |

**The walking cap.** `BonusTypes/BonusType.MovementSpeed` has `MaximumValue` 2.0 and `BonusManager.Multiplier` clamps to
it. Without a remedy, a wellbeing-80 Inkpaw on 12 h would walk at 2.0 instead of 2.261 (+17.6% instead of +33%); the
cap starts to bite above a walking multiplier of 1.50 (adult walking tier +0.6 from wellbeing 52 up). For a builder whose day is about 89%
walking and 11% building (balance model, bakery), output per day relative to a 16-hour day:

| | 12 h, vanilla cap | 12 h, cap raised |
|---|---|---|
| Wellbeing 20 | 0.997 | 0.997 |
| Wellbeing 80 | 0.888 | 0.998 |

(computed from the measured multipliers: output per day = hours / (0.89 / walk + 0.11 / work); not a measured builder
output.) **Remedy, verified:** an Inkpaws-only faction modifier on `BonusTypes/BonusType.MovementSpeed` raises
`MaximumValue` to 2.66 (= 2.0 x 1.33). Bonus types are read after faction modifiers apply, so the cap really is 2.66 in
Inkpaws games (and 2.0 in Folktails games), and the wellbeing-80 colonist reached 2.261. This needs no code and leaves
other factions alone; it also lets very happy Inkpaws on long days walk past 2.0 only if other bonuses push them there
(rare: walking tiers top out at +0.8, so 1.8 plus hauling bonuses).

## What this decides

* **Poles are the vanilla `Plank`, renamed for Inkpaws** (name, plural, icon, weight by faction modifier). No new good,
  no recost of every building, and third-party buildings that cost planks keep working in Inkpaws games. The same
  route is open for `TreatedPlank` and `PineResin`. Timber bamboo is a fast tree whose cut yield is `Plank`, so the
  Inkpaws need no mill for poles. If a "poles" model is wanted on carried and piled goods, that is the one thing a
  modifier cannot add (it can only pick another vanilla container).
* **Per-faction tuning of global data is data, not code**: need rates, building costs and recipe lists of reused
  vanilla buildings, bonus-type caps, wellbeing tiers. Always through `.optional` modifier files.
* **The tutorial is in reach for 1.0**: a short Inkpaws checklist built from vanilla step types, in data, with the
  vanilla Folktails tutorial switched off for Inkpaws only. A "have N of a good" step would need one small step type
  in code. Players with tutorials disabled in settings will not see it (vanilla behaviour).
* **Names with a gloss are a small, safe module** (`Pandaborn.Names`), off = vanilla names.
* **The bell**: the code is done and multiplies as the balance model requires; raise the walking cap for Inkpaws
  with the `BonusType.MovementSpeed` modifier so long-game short days do not lose on walking jobs.
* **Code architecture**: as ENGINEERING.md describes, verified; other agents can add modules now (src/code/README.md).

## Code phase 2 (2026-11-14): carrier, words, report, duplicates

Runs on `proto/foundation` dev copies of the installed mod (`-DisableMods JigglyPanda.PandabornFactions -ExtraMods
E:\PandabornDev\build\proto\<copy>`), because the installed mod now carries its own bootstrap.

* **Per-entity carrier** (`fd-carrier-1`). First launch with `force-off: DevCarrier` (a dev module that keeps
  per-entity state) and `simulate-missing-member: Words`: the probe wrote a `DevCarrier` entry into the Core carrier of
  all 13 colonists while the feature was off; the game was saved. Reload with everything on: all 13 carriers loaded from
  the save (`loadedFromSave`), and the module read every entry back
  (`Xiao Shan (Little mountain)|True|1|writtenWhileOff=1;name=...`).
* **Words** (`fd-words-1`, Inkpaws game then a Folktails game in the same launch). Inkpaws: 106 texts swapped, none
  skipped; Population tab headers "Inkpaw adult (9)" / "Inkpaw cub (4)" (`f_population_tab.png`), population tooltip
  rows "Adults / Cubs", "No unemployed Inkpaw can reach this dwelling.", "Inkpaw-only: Only Inkpaws are allowed...",
  "Inkpaw is injured", building descriptions with pandas; kept texts unchanged ("Beaver Statue"). Folktails afterwards:
  every one of those texts vanilla again ("Beaver adult/child", `folktails/f_population_tab.png`). The swap happens
  before the first blueprint is read: `WordsService` is constructed as a dependency of SpecService's modifier providers,
  so its Load runs first. The district panel and the migration tab contain no beaver words in either game. The top-bar
  tooltip could not be screenshotted (the game draws tooltips at the real mouse position); its texts are the probe's.
* **Fallback** (`fd-carrier-1` first launch, `simulate-missing-member: Words`): vanilla words, the feature report reads
  "Inkpaw words: on with plain-game fallback (simulated: Loc._localization missing)", plus one warning notice.
* **Feature report**: one notification-log entry per save in Inkpaws games, e.g. "Pandaborn - Factions features: The
  afternoon bell (rested Inkpaws): on; Inkpaw names: on; The Inkpaws building look: on; Inkpaw words: on; DevCarrier:
  off (developer setting)" (visible top left in every screenshot of those runs).
* **Duplicate copies** (two local folders with the same manifest Id; `MarkDuplicatedIds` only renames them in the mod
  list, and a local plus a Workshop copy are not even marked: in both cases both copies load). Without a guard every game
  crashed at startup on the asset bundles (`fd-dup-1`: "another AssetBundle with the same files is already loaded",
  `ModAssetBundleLoader` throws). With the duplicate's starter parking its own bundles (`AssetBundles.parked`) that crash
  is gone (`fd-dup-2`); that run then stopped on another mod (TimberUi's `ModUpdateService` builds a dictionary by mod Id
  and throws on any duplicated Id, with or without our code). With only our mods (`fd-dup-3`, `-OnlyMods`): the game
  starts, plays, saves and reloads; only the first copy runs code; the player gets one notice ("enabled twice ... Only the
  copy in ...\pbdupA runs its code") and the feature report ends "mod enabled 1 more time(s)"; not repeated after reload.
