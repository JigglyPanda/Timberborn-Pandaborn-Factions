# Mod compatibility audit (2026-11-25)

Read-only study: every mod installed on the owner's machine (local `Documents\Timberborn\Mods` and the Workshop
folder), the decompiled game (1.1.2.8), our generated mod (`E:\PandabornDev\build\gen\PandabornFactions`, all
modules on: Bell, Names, Look, Words, Tutorial, Ringtails, RingtailsFallback, Water, Festival, Flowering) and
`src/code`. **No game was run for this audit.** Other mods' DLLs were decompiled into
`E:\PandabornDev\build\scratch\compat` only; nothing of theirs is copied here.

**How sure:** every finding carries one of
*certain* (follows from game code and data, no judgement involved),
*likely* (read in their code and ours, one step of inference),
*unverified* (large Harmony surface or behaviour that only a run can show).

## Bottom line

* **No crash was found by reading**, and no id, loc key, template, tool group, worker type or bundle name of ours
  collides with any installed mod or with vanilla (checked by script, 438 loc keys, 181 templates, 17 goods,
  25 needs, 13 recipes).
* We use no Harmony, so nobody's patch can collide with a patch of ours. What can still go wrong is other mods'
  patches changing game classes our modules call. Two mods do that on a scale reading cannot clear:
  **T3MP** and **Performance Plus**. They are the first thing to test.
* The one thing every player with building mods will notice: **building packs do not appear in an Inkpaws game**
  (ten of the installed mods). That is how the game's collections work, not a fault, but it needs a sentence on the
  store page and, if wanted, a bridge (see Recommendations).
* The earlier clean run "Inkpaws then Folktails with all 35 mods" (docs/tech/look.md) predates the Ringtails, Water,
  Festival and Flowering modules. It has to be repeated with everything on before the store page may say "tested
  with".

## 1. Inventory

Active folder = the `version-*` folder the game picks for 1.1.2.8 (`ModRepository.GetDirectoryForCurrentVersion`).
"On" = enable flag in the registry (absent = on). H = ships Harmony patches.

| Mod (manifest id, version) | Kind | On | Code | What it touches |
|---|---|---|---|---|
| Harmony 2.4.1 (Workshop) | library | yes | lib | - |
| Mod Settings `eMka.ModSettings` 1.1.1.0 (Workshop on, local copy off) | framework | yes | yes | own UI only |
| TimberUi 11.0.3 (Workshop) | UI library | yes | yes | `ModUpdateService` builds a dictionary of enabled mods by id (throws on any duplicated id); `EntityFragmentOrderService` reorders fragments that opt in |
| TimberApi 0.8 stub, TimberApi UIBuilder 1.0.2.3 | library | yes | yes | UI builder only |
| Mod Manager 3.0.13 | mod.io client | yes | yes | main menu |
| Moddable Tool Groups 11.1.0 | framework | yes | H | rebuilds the bottom bar (`BottomBarPanel.Initialize*Section`, `BlockObjectToolButtonFactory.CreateTool`, `ToolGroupButton`, `ToolButtonService.Add`), redirects the tutorial's tool-button lookups (`BuildingTutorialStepDeserializer.GetToolButtons` and four more) |
| MoreGroups `KnatteAnka.MoreGroups` 1.1.0.2 | toolbar data | yes | no | merges `ToolGroupChildrenSpec` into vanilla `BlockObjectToolGroup.Landscaping` / `Paths`; 16 sub-groups that list tools **by template name** (`Floodgate.Folktails`, `...IronTeeth`, `...Emberpelts`) |
| CustomTools `Timberborn.IgorZ.CustomTools` 1.4.2 | tools | yes | H | `BlockObjectToolWarningPanel.UpdateSingleton`, `KeyBinding.UpdatePressedState`; its Levee+/Platform+/Path+ tools carry `AllowedFactions: Folktails, IronTeeth` |
| Advanced Automation 4.11.0 | QoL | yes | H | `BaseInstantiator.InstantiateComponents`, `Automator.*`, `BreedingPod.*`, `Floodgate` height, `NoUnemployedStatus.UpdateStatus`, `StatusAlertFragmentRow.GetAlertText`, `ConstructionSite.FinishIfRequirementsMet`; 7 tool groups; reads `WorkingHoursManager.AreWorkingHours` |
| SmartPower 1.19.0 | QoL | yes | H | `BaseInstantiator.InstantiateComponents`, `GoodPoweredGenerator.UpdateState`; decorates `GoodPoweredGenerator`, `WalkerPoweredGenerator` |
| TimberCommons 1.23.0 | library + tweaks | yes | H | `DecoratorDefinition.CreateSingleton` (swaps `WaterOutput` for its subclass), `SoilMoistureService`, `MoistureCalculationTask`, `GrowableFragment`, `GrowableToolPanelItemFactory`, manufactory describers and fragments, `ThrottlingValveFragment`; decorates every `Growable` with `GrowthRateModifier` (replaces the private `Growable._timeTrigger` when a growth modifier registers); hardcodes `Discharge.Folktails|IronTeeth`, `FluidDump.*` |
| SimpleFloodgateTriggers 10.0.4 | QoL | yes | H (`PatchAll`) | decorates `Floodgate`, `StreamGauge`, `WaterSourceRegulator`, `WaterInput`, `WaterOutput` |
| TImprove 10.2.2 | QoL / UI | yes | H | `DayStageCycle.GetCurrentTransition` (optional all-day light), `BlockObject.MakeOverridable`, `BuilderPrioritizable`, `CameraService`, `RecoveredGoodStack`; adds a clock label inside the working-hours panel; `UILayout.AddTopRight(.., 7)` |
| Goods Statistics 1.1.2.0 | UI | yes | yes | own panels |
| Pipette Tool 1.0.0.2, Unstuckify 1.0.0.0 | tools | yes | yes | no patches |
| Configurable Game Speed 7.0.0 (built for game 0.7) | QoL | **off** | H | `SpeedControlPanel.SetSpeed` |
| T3MP 1.2.5 (Workshop) | performance | yes | H, transpilers | load pipeline (`SingletonLifecycleService.LoadAll`, `WorldEntitiesLoader`, `TemplateInstantiator.Instantiate`, `AutoAtlaser`, `EntityMaterials`, `MaterialColorer`), `TickableEntityBucket`, `WalkerMover.Move`, speed buttons x1/x3/x7 |
| Performance Plus 1.0.1 (Workshop, needs T3MP) | performance | yes | H, ~90 features | `BonusManager.Awake`, `NeedManager.*`, `Need.*`, `DayNightCycleSpec.ConfiguredDayLengthInTicks`, `WaterSimulationTaskStarter`, `ThreadSafeWaterMap`, `WaterObjectService`, `Yielder.Enable/ResetYield`, `InRangeYielders`, planting spots, `DwellerHomeAssigner.AssignDweller`, `RangedEffect*`, `LumberjackFlagWorkplaceBehavior`, pathfinding caches |
| Choo!Choo! 2.2.1 (Workshop) | buildings + trains | yes | H | own template collections chosen in code (`ChooChoo.<Faction>` for Folktails, IronTeeth, Emberpelts; **`ChooChoo.Default` for everyone else**); material collections `ChooChoo.FolktailsMaterials` / `IronTeethMaterials` added to factions that do not list the vanilla one; patches `MaterialRepository.Load` (postfix, clones `Details.Folktails`), `BehaviorManager.AddRootBehavior` (postfix), `CharacterBatchControlTab.GetSortingKey` (prefix, its own two keys), `UnemployedWorkers`, `DistrictEmploymentStatisticsProvider`, migration, block validation; decorates `BeaverSpec` with `Traveller`; an `IToolLocker` for its tracks |
| Staircase, Path Extention, Water Extention, Extended Floodgates (KnatteAnka) | building packs | yes | no | append to `Buildings.Folktails`, `.IronTeeth`, `.Emberpelts` (+ `GreedyBuilders`); sub-groups under vanilla tool groups; Water Extention adds recipe `BigWater` |
| KnatteMaterials 1.0.1.0 | materials | yes | no | appends to material collections `Common`, `Folktails`, `IronTeeth` |
| Ladder 1.0.0.2, More Platforms 3.1.2 (Tobbert) | building packs | yes | yes (More Platforms H) | `Buildings.Folktails` / `.IronTeeth`; More Platforms patches `BlockObject.IsAlmostValid`, `WorldSerializer.DeserializeEntity` (renames one of its own templates), `TerrainPhysicsPostLoader.ValidateBlockObjects` |
| Flywheels 4.1.1.15 | building pack | yes | yes | `Buildings.Folktails` / `.IronTeeth` / `.Emberpelts` |
| Ferris Wheel 3.0.0 | building | yes | no | `Buildings.*` of five factions; **need `FerrisWheel` in the `Common` need collection**; adds Iron Teeth wood to the `Folktails` material collection and the reverse |
| Food Stall 1.0.4.0 (Workshop) | building | yes | yes | `Buildings.Folktails` / `.IronTeeth`; need `Snacking` in `Common` (hidden while inactive) |
| The Barkimedes Screw 2.1.0 (Workshop) | building | yes | yes | `Buildings.Folktails` / `.IronTeeth` / `.Emberpelts` / `.LeafCoats` |
| 4-way District Center 3.0.3 | building | yes | no | **overrides `StartingBuildingId` in the vanilla `Faction.Folktails` / `Faction.IronTeeth` files**; optional files for Emberpelts, GreedyBuilders |
| MoreZiplineConnections 1.1.0.1 (Workshop) | tweak | yes | no | merges `ZiplineTowerSpec.MaxConnections = 6` into vanilla `ZiplineStation|Pylon|Beam.Folktails` |
| Population Control `Panda.PopulationControl` 1.0.0 (owner's) | QoL | yes | H | `AdultsDistributorTemplate.MigrateTo`, `ChildrenDistributorTemplate.MigrateTo`, `BotsDistributorTemplate.MigrateTo`, `MigrationCoordinator.Migrate` |
| Pandaborn - Panda Reskin `JigglyPanda.Pandaborn` 7.0.0 (owner's) | visual | yes | yes | overrides `Characters/Beaver/...` meshes; `PandabornFactionSkins` rewrites every non-vanilla faction's coats and portraits; `PandaFurAttacher` on every `BeaverSpec` |
| Custom Characters 0.1.0, Panda Colonists 1.0.0, Panda Colonists Fur 4.9.0 (owner's, older) | visual | **off** | yes | Custom Characters picks packs by `FactionService.Current.Id` |

## 2. Findings

### Blocker
None found by reading. Not the same as "none": see Major 2 and the test matrix.

### Major

**M1. Building packs do not appear in an Inkpaws game.** *Certain.*
`TemplateCollectionService.Load` reads only the collections the current faction lists plus `Common`. Ours are
`Buildings.Inkpaws`, `Characters.Inkpaws`, `ModularShaftParts.Inkpaws`, `NaturalResources.Inkpaws`
(`Factions/Pandaborn/Faction.Inkpaws.blueprint.json`). Staircase, Path Extention, Water Extention, Extended
Floodgates, Ladder, More Platforms, Flywheels, Ferris Wheel, Food Stall, Barkimedes Screw and the 4-way District
Center all append to `Buildings.Folktails` / `.IronTeeth` (and to named third factions such as `Buildings.Emberpelts`),
so an Inkpaws player gets none of them, silently. Nothing crashes; their materials still load because we list the
`Folktails` material collection. The same convention means **authors can opt in with one file**, as they already do
for Emberpelts. Choo!Choo! is the exception: it picks its collection in code and gives unknown factions
`ChooChoo.Default`, so trains are available to the Inkpaws.
*A run must show:* the Inkpaws toolbar without those packs and no error; ChooChoo's group present and buildable.

**M2. T3MP and Performance Plus rewrite loops our modules run inside.** *Unverified.*
Between them: the tick loop (`TickableEntityBucket.TickAll`, an own tick loop, coarser ticks through
`DayNightCycleSpec.ConfiguredDayLengthInTicks`), the load pipeline (cached component construction per blueprint,
`TemplateInstantiator.Instantiate`, atlas pixels), needs (`Need.SetPoints/AddPoints/Update`, `NeedManager.UpdateNeeds`,
`ApplyEffects`), bonuses (`BonusManager.Awake`), water (`WaterSimulationTaskStarter.Simulate`, `ThreadSafeWaterMap.Update`),
plants (`Yielder.Enable/ResetYield`, planting-spot mirrors keyed to `LivingNaturalResource`), housing
(`DwellerHomeAssigner.AssignDweller`) and walking (`WalkerMover.Move`). Spot checks found no direct clash:

| Their piece | Ours | Read as |
|---|---|---|
| `BonusLookups`: replaces `BonusManager._bonuses` with a dictionary using its own comparer (falls back to `string.Equals`) | Bell adds bonuses and listens to `BonusValueChanged` | same semantics |
| T3MP walking rewrite still asks the speed provider on every call | Bell's walking bonus | fine |
| T3MP atlas cache keyed by `Texture2D`, scoped to one load | Look swaps textures on the shared vanilla materials per game | fine |
| `ColouredMaterials` cache cleared on `ColoredMaterialCache.Unload` | Look restores on unload | probably fine |
| `DwellerLookups` caches Beaver -> Dweller component only | `LoftHousingRule` uses public `Dwelling.AssignDweller/UnassignDweller` | fine |
| `RipeCrops`, `PlantingSpots`, `YielderTemplates` caches | Flowering deletes grown bamboo and spawns the in-flower twin on the same tile, kills young plants, pauses growth | **not read through** |
| Coarse ticks, water task patches | Water: `IWaterService` direction and inflow limiters, re-adding the obstacle in `PostLoadEntity`, checks every 30 ticks, "three ticks after loading" | **not read through** |
| Need caches | Festival sets a need to its maximum, applies attraction effects through `ApplyEffectExecutor` | **not read through** |

Both mods carry their own "verify" switches and compatibility gates (T3MP inspects who patched what; we patch
nothing, so its gates stay open). Rank stays Major until a run clears it: a perf mod is exactly what a player with a
big Inkpaws town installs.
*A run must show (both mods on, all our modules on):* load, save, reload; a festival day (everyone off work, need at
maximum after); an announced Flowering through to the rest (no ghost harvest jobs on vanished bamboo, farms replant,
young bamboo held); a flume line holding water across a reload; a Ringtail night shift; speed x7; zero errors from
either side and no "different from a plain search" lines in their log.

**M3. The Reskin replaces Inkpaw portraits and gives Ringtails giant-panda fur.** *Certain; verified in game earlier
(run `rb-p3a`, docs/tech/ringtail-body.md 8.1).* Nothing breaks. The fix is one local commit on the Reskin's
`factions-compat` branch (`fc8e25d`, not pushed, not released). Until the Reskin ships it, this is the most visible
flaw of the most likely mod pairing.

**M4. Two enabled copies of any mod crash TimberUi, and TimberUi is required by TImprove and ChooChoo.** *Certain;
seen in game (`fd-dup-2`, docs/tech/stage0.md).* `ModUpdateService.QueueMessages` calls `ToDictionary` on manifest ids.
Our own duplicate guard (parked bundles, one copy runs code) cannot help once TimberUi is installed. A player who
subscribes on the Workshop while a zip copy sits in `Mods` hits this. Store-page sentence, nothing to code.

**M5. Game updates: three dependencies have no runtime fallback** (details in section 6). *Certain.* A vanilla
blueprint path named as a modifier `Original` that disappears, a spec class a copied vanilla building still names,
or a failure to load `Pandaborn.Specs`, each stop Inkpaws games (Folktails and Iron Teeth stay fine).

**M6. Another mod's tutorial could stop Inkpaws games from loading.** *Likely from our own verified facts; no such
mod is installed, so unverified.* The Inkpaws carry `StartingFactionSpec`, so the game builds **every** `TutorialSpec`
for them, and a step that names a template the faction lacks throws in `TutorialService.Load` (CLAUDE.md, stage 0).
We switch the vanilla tutorials off by modifier, one by one, by path. A tutorial added by any other mod (a second
faction with its own tutorial, a tutorial mod naming `.Folktails` buildings) is not on that list, and a modifier
cannot name a file that may be absent (section 6). Our own tutorials are dormant in everyone else's game, so the
risk runs one way only.
*A run must show:* an Inkpaws game loading with a mod that ships a `TutorialSpec`. Until then the store page says
"other faction mods: not tested".

### Minor

| # | Finding | Evidence | Sure | A run must show |
|---|---|---|---|---|
| m1 | **Ferris Wheel's need is in `Common`**, so Inkpaws carry a "Ferris Wheel" fun need (+4) no Inkpaws building can meet: the wellbeing ceiling reads 4 too high. Any mod that adds a need to `Common` does this. Food Stall's `Snacking` is inert (hidden, sits at its maximum) | their `NeedCollections/NeedCollection.FerrisWheel.Common`; game `CommonNeedCollectionIdsProvider` | certain | the row in an Inkpaw's wellbeing panel; no error |
| m2 | **Tweaks that merge into a vanilla blueprint by path do not reach our `.Inkpaws` copies.** Here: MoreZiplineConnections (Inkpaws ziplines keep the vanilla connection count). Same for any "bigger storage", "cheaper X" mod | their three `Zipline*.Folktails` files; our `ZiplineStation|Pylon|Beam.Inkpaws` | certain | - |
| m3 | **MoreGroups does not sort Inkpaws buildings into its sub-menus** (it lists template names). They stay in the main groups. Moddable Tool Groups hides groups with no visible content (`HasVisibleContent`), so there are no empty buttons, and our Night Watch group does not show in other factions' games (vanilla: `CreateRegularBlockObjectToolGroup` returns null for an empty group) | MTG `AssignToolParents`, `CreateToolGroup` | likely | Inkpaws toolbar with MTG + MoreGroups: every building reachable, no empty group; Folktails toolbar unchanged |
| m4 | **Moddable Tool Groups redirects the tutorial's tool-button lookups.** Our tutorial uses vanilla step types with `.Inkpaws` template names, so it goes through its redirect | MTG `TutorialPatches.RedirectGTB` | unverified | the Inkpaws tutorial highlights the right buttons with MTG on; no exception on load |
| m5 | **CustomTools' Levee+/Platform+/Path+ tools are hidden for Inkpaws** by its own faction list | `CustomToolFeatureLimiterSpec.AllowedFactions` | certain | - |
| m6 | **TimberCommons swaps the growth timer.** `GrowthRateModifier.UpdateRate` builds a new trigger, puts it in `Growable._timeTrigger` and resumes it. A growth hold of ours on that plant would be released early (milder Flowering, never harsher). Needs a building with its growth range effect next to bamboo; no Inkpaws building has one today | their `GrowthRateModifier`; our `Pandaborn.Flowering/GrowthHold.cs` | likely, latent | - |
| m7 | **TimberCommons' discharge settings skip our Discharge and Cistern Tap** (hardcoded vanilla template names); they behave as vanilla. Its `WaterOutput` subclass is transparent to our Water module | `DischargeTemplateMatcher`, `DecoratorDefinitionPatch` | certain / likely | Scoop Wheel, Paddy Spout, Cistern Tap move water with it on (README: flumes already compared) |
| m8 | **Choo!Choo! in an Inkpaws game** uses vanilla Folktails material names, so trains and stations are re-themed by the Look swap; its `MaterialRepository.Load` postfix clones `Details.Folktails` after our swap, so its logo materials carry our maps under its own picture. Its `AddRootBehavior` postfix puts `TravellerRootBehavior` after `StrandedRootBehavior`; ours insert by type (`FindIndex(r => r is WorkerRootBehavior)`), so order holds. Its `GetSortingKey` prefix passes all other keys through | ChooChoo `BaseFactionMaterialsProvider`, `ChooChooCustomMaterialsPatch`, `TravellerRootBehaviorPatch`; our `FestivalGoer.Insert`, `RingtailRestRootBehavior.Insert` | likely | a station built and staffed by Inkpaws; logos and wagons look right day and night; a traveller on a festival day; Population tab opens |
| m9 | **SimpleFloodgateTriggers and Automation attach by component**, so they work on `Floodgate.Inkpaws` and the pumps, and SFT also lands on Scoop Wheel, Treadwheel Lift and Cistern Tap (`WaterInput`/`WaterOutput`). The Flume Gate is not a `Floodgate` (no `FloodgateSpec`), so neither mod can drive it | SFT decorators; our Flume Gate's spec list | certain | a Scoop Wheel paused by an SFT trigger shows a sensible status line |
| m10 | **Population Control filters migration**; Ringtails count as adults and kits in `DistrictPopulation`, so its age and job filters apply to them. Vanilla migration can already move a Ringtail to a district without a Moon Loft | their four patches | likely | migrate with a filter in a town with Ringtails: no error |
| m11 | **TImprove's all-day light** removes night visuals (lantern glow, the moon arc still draws). Its clock label and our "Rested" line use different slots | `DayStageCyclePatches`; our `UILayout.AddTopRight(root, 3)` | certain | top bar with both: no overlap |
| m12 | **4-way District Center** changes the starting building of Folktails and Iron Teeth only; Inkpaws keep the Village Hall | their faction files | certain | - |
| m13 | **Materials added to `Folktails`** (KnatteMaterials, Ferris Wheel) load in Inkpaws games, unused. No duplicate: `MaterialRepository.Load` throws only for two different materials with one name, and our look materials are never in a collection | game `MaterialRepository` | certain | - |
| m14 | **Mod Settings**: not used, nothing needed for 1.0 | - | certain | - |

### The checks asked for, in one place

| Check | Answer |
|---|---|
| (a) merges onto vanilla templates our copies came from | Only MoreZiplineConnections on this machine (m2). The class is real and silent |
| (b) buildings added to `Buildings.Folktails` / `Common` | `Buildings.Folktails`: not offered to Inkpaws (M1). `Common` template collection: none of the installed mods use it; such buildings would show, with correct materials as long as they use `Common` or `Folktails` materials |
| (c) Harmony on what our modules call or read | `BonusManager` (P+, same semantics), `BehaviorManager.AddRootBehavior` (ChooChoo, compatible), `Growable._timeTrigger` (TimberCommons writes it, m6), `CharacterBatchControlTab.GetSortingKey` (ChooChoo, passes through), `MaterialRepository.Load` (ChooChoo postfix, m8). Nobody patches `WorkingHoursManager`, `Loc`, `Firework`, `WaterObstacle`, `TemplateNameMapper`, the decal or outfit services |
| (d) UI mods rebuilding panels we add to | None rebuilds the entity panel, top bar or clock. We use the public `UILayout.AddTopRight/AddTopLeft/AddAbsoluteItem` and `EntityPanelModule`; one lookup by name (`"Clock"`), behind `SafeUi` |
| (e) working hours, bonuses, needs, wellbeing, names, sounds, materials | Nobody sets working hours (Automation and TImprove only read them). Needs: m1. Bonuses: P+. Names: nobody binds an `IEntityNamer`. Materials: m8, m13 |
| (f) id collisions | None (script over all active mod folders; our aliases `RingtailAdult.Inkpaws`, `RingtailChild.Inkpaws`, and `Stairs.Folktails`, which no mod loads in an Inkpaws game). The only `pandaborn*` file elsewhere is the Reskin's `PandabornSettings.bin`; its bundles are `pandacolonistsv5/v6` |
| (g) the Reskin, character frameworks | M3. Custom Characters (off) selects packs by faction id; a pack would have to name `Inkpaws` to do anything |
| (h) Mod Settings | Nothing needed. A player-facing "turn a feature off" file would be the only candidate (section 7) |

## 3. The wider ecosystem: five conflict classes

From the game's code, the mods installed here, and what a short web search turned up (the Workshop pages themselves
answered HTTP 429, so the web notes are second-hand and marked).

| Class | How it bites | Where we stand |
|---|---|---|
| 1. Duplicate global names: goods, needs, recipes, templates, worker types, spec classes, materials | Exception in every game | Every id prefixed `Pandaborn` or suffixed `.Inkpaws`, locked; spec class names checked against the AppDomain before `Pandaborn.Specs` loads; look materials never enter a collection. A reported modded-Emberpelts log shows the "material already loaded" form of this class (web, unverified) |
| 2. Data keyed to faction ids or template names | Silent absence: packs listed per faction (M1), toolbar sorters (m3), tools with faction lists (m5), code with hardcoded names (m7) | Nothing breaks; the Inkpaws just do not get the extra. Solved only by opt-in files, ours or theirs |
| 3. Harmony patches on shared game classes | Changed order or cached state under our feet | We patch nothing. Root behaviours are inserted by type, bonuses through the public API, each private member has a written fallback. Open risk: performance mods (M2) |
| 4. Global data another mod changes for everyone: needs in `Common`, wellbeing tiers, bonus-type caps, vanilla goods and recipes overridden at vanilla paths | Balance drift, unmeetable needs (m1) | Our Inkpaws-only tuning is applied last, as faction modifiers, so ours wins in our game and leaks nowhere. Bell reports "reduced" if the walking cap ends up too low. Words replaces a text only while it still equals the vanilla text |
| 5. Game updates and duplicated installs | Old `version-*` folders, a second copy, a renamed game type | Per-module API lists, module off + notice; duplicate guard. Gaps: section 6, and TimberUi's duplicate crash (M4) |

Web notes (unverified, second-hand): an Emberpelts page mirror lists AquaCadre and More Paths as crashing with it
and Automation as working; one user thread reports an `ISpecService is no longer SpecService` error with Automation
or TImprove plus a weather mod on an Emberpelts save; a "Configurable Faction (Faction Mixer)" mod exists that moves
buildings between factions, which is the kind of mod that could hand Inkpaws a second copy of a material or a
building whose goods they lack. Sources:
[Steam discussion 1](https://steamcommunity.com/workshop/filedetails/discussion/3493039008/819206164467162647),
[Steam discussion 2](https://steamcommunity.com/workshop/filedetails/discussion/3455892854/599653731153245602),
[Emberpelts changelog](https://steamcommunity.com/sharedfiles/filedetails/changelog/3346318229),
[page mirror](https://catalogue.smods.ru/?p=428744),
[Timberborn mods guide](https://timberborn.pages.dev/mods).

## 4. Another new faction in the same install

Reasoned from the game's code; no other faction mod is installed here, so **none of this was run**.

| Thing | Shared? | Result |
|---|---|---|
| Faction list | sorted by `FactionSpec.Order` (ours 2), stable sort | both appear; a tie only fixes the order by load order |
| Template, good, need, material collections | per faction id + `Common` | separate. `NeedVerifier` wants every need collection listed by an installed faction: ours always is |
| Goods, needs, recipes, worker types | global dictionaries | safe while ids differ (ours are prefixed). A faction mod that reuses a plain id such as another mod's `Tea` is the known crash of this class; ours cannot be the second party |
| Faction blueprint modifiers | only the current faction's are applied | our Plank-as-Poles, bell cap, tutorial switches and shelf sizes exist only in Inkpaws games; theirs only in theirs |
| Wellbeing tiers, bonus types, need groups, good groups | global | if their mod overrides one at the vanilla path, our game changes too (class 4). We override none |
| Tool groups | global specs, empty groups hidden | our Night Watch group shows only where its buildings exist |
| Decals, outfits | by `FactionId`; an empty id applies to all | ours all carry `Inkpaws` (14 decals, 15 outfits). A decal of theirs with an empty id would show in our banner picker |
| Name pool | global vanilla pool; ours is an `IEntityNamer` on our own templates | their colonists never get Inkpaw names; if they also bind a namer above priority 30 it would outrank ours on their templates only |
| Tutorial | global `TutorialSpec`s, built for factions with `StartingFactionSpec` | **the one real question (M6):** our tutorials are dormant until our modifiers switch them on, and we switch every vanilla tutorial off for Inkpaws. A second faction that also carries `StartingFactionSpec` would have all of ours built for it, dormant (no stages, as in the Folktails check `p3-nodata-2`). Their tutorials, if not dormant by default, would be built in our game, and a step naming a template we lack throws in `TutorialService.Load` |
| Building packs | per faction | each pack serves the factions it names; Inkpaws get none (M1) |

What a player with an Emberpelts-like mod plus ours would see: in a **Folktails** game, nothing of ours (no goods,
needs, tool group, tutorial, look or words; the Reskin aside). In **our** game, nothing of theirs unless they changed
global data, plus the tutorial question above. In **their** game, nothing of ours: every module of ours asks for its
spec on the faction's own templates or for the faction id `Inkpaws` before acting.
*A run must show:* main menu with both; a new game of each of the three kinds in one session; our feature report
only in ours.

## 5. What a game run would have to show, by mod

Covered above per finding; the matrix in section 9 orders the runs.

## 6. Game updates: what is fragile, and whether the fallback is real

| Dependency | If the game changes it | Fallback | Real? |
|---|---|---|---|
| Game API each module references (`<Module>.api.txt`, resolved before load) | module not loaded, feature off, notice | yes | yes, tested per module (`simulate-missing-api`) |
| `BehaviorManager._rootBehaviors` (Festival, Ringtails) | Festival: no day off, show and Tradition stay. Ringtails: degraded, RingtailsFallback returns night posts to Inkpaws | yes | yes, dev switch |
| `Growable._timeTrigger` (Flowering) | young bamboo regrows at once | yes | yes |
| `TemplateNameMapper._templates` (Ringtails) | Ringtails off, saved ones load as Inkpaws through the alias | yes | yes |
| `Loc._localization` (Words) | vanilla words, notice | yes | yes |
| `Firework.Launch` (internal type, Festival) | no lanterns or bursts in the sky | yes | yes |
| **33 of the faction's 42 modifiers name a vanilla blueprint path as `Original`** (2 goods, 12 recipes, `BonusType.MovementSpeed`, 18 tutorials; today's build) | `FactionBlueprintModifierProvider.GetModifiers` reads `Original.Asset` for every blueprint; a missing asset throws on the first blueprint read: **every Inkpaws game stops loading** | none at runtime | **no**. The pin (`catalogue/vanilla.pin.json`) catches it at build time only |
| **113 `.Inkpaws` copies of vanilla buildings** (of 170 buildings), frozen at the pinned dump | a renamed or removed spec class: unknown key throws when the template is read (Inkpaws games). A renamed field: silent default (a free building, a zero yield). A removed model, sound or sprite path: throws on use | none at runtime | **no**; `tools/game_diff.py` + regenerate + release is the only cure |
| `Pandaborn.Specs` (references only `ComponentSpec`, `[Serialize]`) | if it cannot load, every template naming a `Pandaborn...Spec` throws on read: Inkpaws games stop | the `-NoCode` build exists, but only as a build variant | partly |
| Facts the tutorial faction rests on: `Stairs.Folktails` alias, vanilla character label keys, `StartingFactionSpec` | load crash or Population tab crash in Inkpaws games | validator rules | build time only |
| Asset bundles (Unity version change) | a bundle that fails to load throws in **every** game | none | no; rebuild on each Unity bump. This is the only item that can hurt Folktails players |

So: code is well defended; **data is the fragile half**, and the two "no" rows fail closed for Inkpaws saves only.
The honest store-page line is "after a game update, wait for the mod's update before loading an Inkpaws save".

## 7. Recommendations

Cheapest first.

1. **Say M1 on the store page and publish the opt-in for authors**: "add
   `TemplateCollectionSpec { CollectionId: "Buildings.Inkpaws", "Blueprints#append": [...] }`; your `.Folktails`
   templates work as they are (we list the `Folktails` material collection; Log, Plank, Gear, Metal Block, Scrap
   Metal, Treated Plank, Explosives exist for Inkpaws)". Checked: the installed Knatte and Tobbert packs cost only
   those goods.
2. **Decide on a bridge for the popular packs.** Three routes, none run yet:
   * a separate small mod per pack (or one for several) with the collection file and `RequiredMods`. Safe, more
     items to maintain. A plain collection file in the main mod is **not** an option: `TemplateCollectionService`
     calls `GetBlueprint` on every listed path and throws when the pack is absent.
   * a faction modifier that rewrites a pack's collection id is **not** an option either: a modifier whose `Original`
     is missing throws (section 6).
   * an `.optional` file at the pack's own building path that adds a `TemplateCollectionSpec` listing that same
     file under `Buildings.Inkpaws`. It is skipped when the pack is absent or renames the file, and it is the
     pattern MoreGroups and the 4-way District Center already use on other mods' files. It puts an inert spec on
     someone else's template in every game, so it needs a ten-minute probe (Folktails and Inkpaws game, pack on and
     off) and the owner's yes before it is used.
3. **Release the Reskin's `factions-compat` commit** with or before the faction mod (M3).
4. **Give the modifier `Original`s a runtime guard** (section 6, first "no" row). The bootstrap runs before any
   blueprint is read and may only use file IO: keep the vanilla-path modifiers in
   `Faction.Inkpaws.optional.blueprint.json` next to the faction file (`BlueprintModifiers#append`; an optional file
   merges into its base), and have the starter rename that file away when the game's version is not the one the mod
   was built for, the way it parks bundles. Inkpaws games then load with "Planks", vanilla shelf sizes and the vanilla
   tutorials no longer switched off, which brings M6's crash back for the vanilla tutorials unless
   `StartingFactionSpec` moves into the same optional file. It also fires on harmless patches. Untested, and worth
   doing only if the owner wants saves to survive the days between a game patch and our update; otherwise the
   store-page line is enough.
5. **Flowering: hold again when the timer object changes.** `FloweringService` could re-apply `GrowthHold.Hold` for
   resting plants at each dawn; it costs one loop and closes m6 and the vanilla case of a plant that dried and
   recovered.
6. **Turn the dev switch into a documented player switch** (`force-off: <Feature>` in a text file next to the
   manifest). It already exists; players with a perf mod get a way to isolate a feature, and it answers the Mod
   Settings question without a dependency.
7. **Add three scenarios to the release list in ENGINEERING.md**: "T3MP + Performance Plus", "Moddable Tool Groups +
   MoreGroups toolbar and tutorial", "second faction mod".
8. Nothing to change for ids, bundles, loc keys, tool groups, worker types, decals or outfits.

## 8. For the store page

**Works with / known issues** (plain sentences; move a line to "tested" only after its run):

* Pandaborn - Factions uses no Harmony and needs no other mod.
* It does not change Folktails or Iron Teeth. Adding it to an existing game is safe.
* Removing it breaks Inkpaws saves. After a Timberborn update, wait for this mod's update before loading one.
* Use one copy only. A Workshop copy plus a manual copy makes TimberUi (needed by TImprove and Choo!Choo!) stop the
  game at start.
* Building mods such as Staircase, Ladder, More Platforms, Path Extention, Water Extention, Extended Floodgates,
  Flywheels, Ferris Wheel, Food Stall, The Barkimedes Screw and the 4-way District Center keep working for Folktails
  and Iron Teeth, but their buildings are not offered to the Inkpaws: those mods list their buildings per faction.
  Authors can add the Inkpaws with one small file (see the mod page for the collection name).
* Choo!Choo! is available to the Inkpaws. Its stations and wagons take on the Inkpaws' building look.
* Mods that change a vanilla building (more zipline connections, bigger storage) do not change the Inkpaws' own
  version of that building.
* With Ferris Wheel installed, Inkpaws show a "Ferris Wheel" need they cannot meet. It costs nothing but the last 4
  points of wellbeing.
* MoreGroups keeps Inkpaws buildings in the main toolbar groups, not in its sub-menus. CustomTools' Levee+, Platform+
  and Path+ tools are for Folktails and Iron Teeth only.
* Automation and Simple Floodgate Triggers work on Inkpaws floodgates and pumps. They cannot control the Flume Gate.
* Pandaborn - Panda Reskin: works. Until its next update it shows its own portraits for the Inkpaws and gives
  Ringtails giant-panda fur.
* Performance mods (T3MP, Performance Plus): not tested yet. If something looks wrong in an Inkpaws game, try
  without them first and tell us.
* Other faction mods: expected to live side by side; not tested yet.
* Mod Settings is not needed. The Great Flowering is set per save, in the game.

## 9. Test matrix, in priority order

Each run: hidden desktop, `tools\run_game_test.ps1`, the installed faction with all modules on, zero errors from
either side. "Inkpaws then Folktails" = one launch, both games (harness `"then"`).

| # | Mods on | Scenario | Look for |
|---|---|---|---|
| 1 | all of the owner's mods | Inkpaws then Folktails, grid request, save and reload | the old 35-mod result again, now with Ringtails, Water, Festival, Flowering; feature report all "on"; Folktails templates, goods, needs, toolbar equal to a run without us |
| 2 | ours + Harmony + T3MP + Performance Plus | events and water scenarios (`tests/scenarios/events`, `water`), speed ladder up to x7, save and reload | M2's list; their logs free of verify mismatches; no stuck harvest or planting jobs after a Flowering; flume water kept across reload |
| 3 | ours + Reskin 7.0.0, then ours + the `factions-compat` build | `adult@start,child@start`, a Ringtail close-up, Folktails after | M3 before and after; Folktails pandas unchanged |
| 4 | ours + Moddable Tool Groups + MoreGroups + CustomTools + Automation | new Inkpaws game with the tutorial on, `-FactionPanelShots`, screenshot of every toolbar group | every Inkpaws building reachable; no empty group; tutorial steps highlight a button; Night Watch absent in a Folktails game |
| 5 | ours + Choo!Choo! + TimberUi + KnatteMaterials | build a station and track as Inkpaws, festival day, Population tab | m8; no "already loaded" or "not found in repository" |
| 6 | ours + TimberCommons + Simple Floodgate Triggers + SmartPower | water scenarios; SFT trigger on a Scoop Wheel | m7, m9; flume numbers equal to the run without them |
| 7 | ours + Ferris Wheel + Food Stall + MoreZiplineConnections + 4-way DC | new Inkpaws game, an Inkpaw's wellbeing panel | m1 as described, no crash; Village Hall is the start building |
| 8 | ours + one other faction mod (Emberpelts or the most subscribed one at the time) | main menu, then a game of each faction in one launch | section 4, the tutorial question first |
| 9 | two copies of ours, with and without TimberUi | start | our notice without TimberUi; TimberUi's crash text with it, for the store page |
| 10 | ours alone on the next game patch, before regenerating | load a saved Inkpaws game | which of section 6's "no" rows fires first; the text a player would see |

## 10. Not verified

* Everything marked *unverified* or *likely*: no game was run.
* T3MP (335 KB decompiled) and Performance Plus (620 KB) were sampled, not read in full.
* Which mods are the most subscribed, and other faction mods' files: the Workshop refused automated reads; the web
  notes in section 3 are second-hand.
* Mac: not looked at.
* The installed faction junction was absent from `Mods` during the audit (project paused), so "installed" means the
  generated folder, not a build that passed the gate.
