# Ship-and-maintain review of the Pandaborn - Factions plan (design rev 3 + catalogue draft 1)

I only read files. I edited nothing, ran no builds and did not launch the game. The one thing I executed was `src/pipeline/tmesh_inspect.py` on the Reskin's adult mesh, to measure its size.

## Headline findings

1. **The biggest danger is the game failing to start, not Inkpaws breaking.** Several things in the plan's data load in every game, Folktails included, and they fail hard:
   - **Unknown spec keys throw.** `SpecService.Deserialize` always calls `DeserializeUnsafe`, and an unknown spec key throws `ArgumentException("No type found for key")` (`Timberborn.BlueprintSystem/BlueprintDeserializer.cs`, `SpecService.cs`). At index time it is only a warning.
   - **The need check runs for all games.** `NeedVerifier` (`Timberborn.GameFactionSystem/NeedVerifier.cs`) throws whenever a need or need collection is unused.
   - **Duplicate recipe ids throw** (`RecipeSpecService.ToFrozenDictionary`).
   - **Duplicate spec class names throw.** `SpecTypeCache` keys spec classes by their simple name, across every loaded assembly, so another mod's spec with the same name crashes the game.
   - **A bad asset bundle throws.** If one fails to load, `ModAssetBundleLoader` throws `InvalidOperationException`.
   - **Assembly loading is unguarded.** `ModCodeStarter` and `SpecTypeCache.Create` both call `assembly.GetTypes()` with no guard. One DLL whose types can't load (a renamed game type, or an absent optional mod) takes down every mod.

   Goods, needs, recipes, worker types, decals, outfits, collections and the faction file are all indexed for every game. So one stale field there can crash a Folktails player's game.
2. **Field renames fail silently.** `BasicDeserializer` ignores unknown JSON fields and leaves missing ones at their defaults. A renamed field after an update therefore gives no error at all: a free building, zero yield, a plant that never dies. Two notes understate this:
   - water.md says "a rename breaks loading, not saves". That is true only for spec types.
   - water.md also says "validate.py checks spec keys against the DLLs". That check does not exist yet.
3. **Removing the mod cannot fail cleanly.** The game shows its incompatibility dialog (`SaveModsValidator`). If the player continues, `FactionSpecService.GetFaction("Inkpaws")` throws. Every mod version change also shows that dialog on older saves, because the version string must match exactly. Missing templates, goods and recipes are handled gracefully (entities dropped with a loading issue; goods and recipes silently dropped). The missing faction is not.
4. **Nothing in the plan needs Harmony.** Rev 3's own-buildings-per-people design removed the shift-flipping risks. What remains is two private-field reflection points, both in Ringtails.
5. **Two cheap mechanisms can remove a lot of risk; both need an in-game check now:**
   - **Bamboo poles as a faction-scoped re-skin of vanilla `Planks`** (and possibly `TreatedPlanks`/`PineResin`), done through `FactionSpec.BlueprintModifiers`. This removes most cost edits and fixes third-party building mods. Reason: `GoodService.GetGood` throws for goods outside the faction's collections, so any Folktails-style building that costs Planks would crash an Inkpaws game if Planks is not an Inkpaws good.
   - **Choosing the re-theme in code.** `IMaterialCollectionIdsProvider` is public, so code can pick "our re-themed collection if it is complete, otherwise `Folktails`". That gives the re-theme a self-disabling fallback.
6. **Scope is about three releases' worth.** The long poles are the Ringtail body, ~45 kit models, plants with growth stages, and Festival and Flowering code. The cut line below keeps 1.0 mostly data, with three small public-API modules.

## 1. Risk register (highest priority first)

| # | Risk | Likelihood | Impact | Mitigation | Owner action |
|---|---|---|---|---|---|
| 1 | A game update renames or removes a spec, field or type, so globally loaded data or code crashes all games, or malfunctions silently | High over the mod's life | Critical | Spec schema dumped from the DLLs, plus a validator. Custom specs only in Inkpaws-only template blueprints, never in goods/needs/recipes/faction/decals/outfits. Bootstrap loader that checks each feature's game references before loading it (§5). Shipped self-check that shows a "needs update" notice. Day-one update runbook | Approve the bootstrap architecture |
| 2 | Silent data drift: ~110 re-themed copies go stale against vanilla (rebalances, new specs, renamed assets) | High | High | Generate copies by rule from the vanilla dump. Record source hashes per derived file. Vanilla diff report on every update | None |
| 3 | Player removes or loses the mod, and the save won't load | Certain for some players | High (reads as "mod broke my save") | Not fixable in code. Say it plainly in README and Workshop text. Never drop the mod from a version-folder layout (see #10) | Approve the wording |
| 4 | Ringtails' private fields (`TemplateNameMapper._templates`, `BehaviorManager._rootBehaviors`) or behaviour churn | Medium per update | High (Ringtails vanish or never sleep) | The prototype already falls back to "load as Inkpaws" through a `BackwardCompatibleTemplateNames` alias. Add a defined fallback for the root-behaviour insert. Run every reflection point under a simulated-breakage harness test. Ship in 1.1 unless the gate and a multi-day soak both pass | Decide Ringtails' release |
| 5 | Re-theme by material-name shadowing: a vanilla update adds a Folktails material, so `"Material X not found in repository"` when a building is placed in an Inkpaws game | Medium | High | Generate the collection from `MaterialCollection.Folktails` plus a coverage check. Runtime provider falls back to `Folktails` if coverage is incomplete | Run the stage-0 in-game test |
| 6 | Planks replaced by a new Poles good: hundreds of cost edits, and third-party Folktails buildings crash Inkpaws games | High if the current plan stands | High | Poles = faction-scoped re-skin of `Planks` through `BlueprintModifiers`, if the timing test passes | Decision #3 |
| 7 | A feature whose data needs its code: e.g. the nursery replacing `ProcreationHouseSpec` means no births at all if the module is off, so the colony slowly dies | Medium | High (silent) | Rule: data alone must behave like vanilla, and code only adds. Keep vanilla `ProcreationHouseSpec`. The cubs switch moves to 1.1 with a vanilla fallback | Adopt the rule |
| 8 | Temporary effects written into saved vanilla state (e.g. the Festival setting working hours to 0) leave the colony stuck if the mod is disabled mid-effect | Medium | High | Rule: temporary effects only through unsaved means (bonuses, root behaviours, effects). Never write saved vanilla state except the one-off new-game default | Adopt the rule |
| 9 | Size and memory: the panda adult mesh is 96 MB on disk (171 MB unpacked: 61 animations, 3,535 frames × 1,716 vertices), the kit 57 MB, a Ringtail body maybe another ~150 MB. mod.io re-downloads it all on every update | High | Medium (memory on low-end Macs, download churn) | Measure and cut the frame budget (frame rate, per-frame tangents). Keep binaries byte-identical between releases. No duplication through version folders | Accept the size budget |
| 10 | `version-X.Y` folders: when any exist the root folder is ignored, the highest version ≤ the game is picked, and if none matches the mod does not load (so faction saves crash). Every folder repeats the full meshes | Medium | High | Support one game version. Use a version folder only for an experimental-branch emergency, and always include a floor folder | Policy |
| 11 | Mac: the Reskin ships only `pandacolonistsv6_win`. No Mac bundles are proven, no Mac to test on, and the shaders are custom | High | Medium–High (pink or crashing for Mac players) | Build `_mac` on every build, with Unity Mac build support. Validator requires the win/mac pair. Find Mac testers or label Mac as community-tested | Decide Mac support level |
| 12 | The game moves to a new Unity version, so bundles break (pink materials, or a load throw that stops every mod) | Medium | Critical | Builder refuses to run unless the editor matches the game's Unity version. Rebuild bundles on every game update | Install the new editor when needed |
| 13 | Two installs (Workshop + local) are both enabled: duplicates are only marked within the same source (`ModRepository.MarkDuplicatedIds`), so both DLLs load, spec names duplicate, and `SpecTypeCache` crashes | Medium (dev machine with junction + subscription; players doing manual installs) | Critical | Spec records ship as a `.bin` that the bootstrap loads once per AppDomain. Harness refuses to run if both copies are enabled | None |
| 14 | Scope: the art volume never converges and 1.0 slips indefinitely | High | High | Cut line and lanes in §8. Each model replaces a stand-in, so every build stays releasable | Approve the cut |
| 15 | The Reskin's `PandabornFactionSkins` rewrites non-vanilla factions to Folktails coats, which includes the Inkpaws | Certain until fixed | Medium | Release a Reskin update that excludes `Inkpaws` before the Factions mod ships. Test both orders | Owner (same author) |
| 16 | Opening balance (no mill, 12 h day, Normal start has no water) produces "brutal start" reviews | Medium | Medium | Colony model driven by the catalogue, plus scripted soaks per difficulty | None |
| 17 | UI fragments (entity panels, UXML element names) change often | Medium | Medium | Keep them in feature modules wrapped in try/catch. No core feature needs a panel in 1.0 | None |
| 18 | Third-party building mods are invisible to Inkpaws once the faction stops listing `Buildings.Folktails` | Certain | Low–Medium (reviews) | Publish a `Buildings.Inkpaws` convention and a one-file compat recipe (§7) | None |
| 19 | The harness is serial (one game per machine, global mutex), so agent tests queue | High | Medium (throughput) | One "grid" session per run that places every building and runs every recipe. Under 15 min per change, full suite nightly | Lead schedules the game slot |
| 20 | Stale docs steer agents wrong: two-peoples.md still recommends W3 shift flipping and an Oxen crew setting; the Ringtails README points to a "Prototype results" section that doesn't exist | Medium | Medium | Mark the superseded sections | Lead |

## 2. Feature by feature

**Data only.** Each can break on a spec or field rename. A spec rename throws at deserialisation (globally, for global specs). A field rename does nothing visible. Safety for all of them comes from the schema validator, generated copies and functional tests.
- Faction, characters, coats, decals, outfits.
- Goods, needs, recipes, collections. These are global, so they carry the crash-all-games risk. Prefix every id. Keep every need in a collection that the faction always uses: `NeedVerifier` throws otherwise, even if the owning feature is disabled.
- Re-themed copies of vanilla buildings: specs, costs and workplaces.
- Plants:
  - Bamboo is a tree with both `GatherableSpec` and `CuttableSpec`, like the chestnut.
  - Rice and lotus use `FloodableNaturalResourceSpec` with integer bands.
  - Cabbage and soybean are ordinary land crops.
  - Tea and pepper use `AridNaturalResourceSpec`.
  - Persimmon and lacquer are trees.
- Planter groups (paddy house, hill farm, grove keeper).
- Spout (`FillValveSpec` is an `internal record`; fields verified: `DefaultTargetHeightOffset`, `OverflowLimit`, `OutputCoordinates`).
- Cisterns, water wheel, kite windmill, gravity battery, drying rack (`ProductionIncreaserSpec`).
- Attractions (hammock, nap platform, teahouse, kindergarten, swing and slide, hot spring, ink studio), decorations, monuments, wonder.
- Wooden Oxen as bots.
- Rest need: penalties come from `PunitiveNeedSpec`, which applies only while the need is unfavourable. "Tired pandas work slower" is data.
- Ringtail-only workplaces (`DefaultWorkerType` + `DisallowOtherWorkerTypes`).
- Planks re-skin and per-faction tweaks through `BlueprintModifiers`. The mechanism is untested: modifiers apply only to blueprints first deserialised after `FactionService.Load`, because `SpecService` is lazy and per context.
- Noria and treadwheel lift are "probably data" until the water prototype proves it.
- Tutorial through `StartingFactionSpec` (only `TutorialService`, `TutorialTriggers` and `TutorialToggleController` read it; verified). It needs a small trigger in code.

**Small code on public APIs.** In every case the code is skipped (by the bootstrap's pre-load check) or turns itself off, and the data stays inert.

| Feature | Game dependencies | Change likelihood | What the player sees if it breaks | Safe failure |
|---|---|---|---|---|
| Flume segment | `IWaterService.Add/RemoveDirectionLimiter`, `SetInflowLimit`, `BlockObject`, `IFinishedStateListener`, `FlowDirection` | Low (3 vanilla systems use it) | Type-load crash, otherwise water leaks or flows backwards | Pre-load check; inert flume. Limiters are not saved, so nothing to clean up |
| Dew limiter | `IManufactoryLimiter`, `WeatherService`, `HazardousWeatherService`, `DroughtWeather` | Low–Medium | Full rate during drought | Pre-load check |
| Golden afternoon (12 h at new game + working-speed bonus) | `WorkingHoursManager.WorkedPartOfDay` setter (the default comes from global daytime, so this is code, not data), `BonusManager.AddBonus("WorkingSpeed")` | Low | A 12 h day without the speed bonus: a silent nerf | Notice telling the player to set 16 h if the module is off |
| Long life / slow growth | `LifeExpectancy` bonus | Low | Vanilla lifespan | None needed |
| Notifications | `NotificationBus` | Low | No message | None needed |
| Nursery and "welcome cubs" | `NewbornSpawner` / `BeaverFactory` (public), `Enterable.EntererAdded`; vanilla `ProcreationHouse` and `Procreator` are internal, 0.1875 roll hardcoded | Medium | **No births** if the nursery replaced the vanilla spec | Keep the vanilla spec; v1.1 |
| Bamboo spreading from planted groves | `Reproducible.UnblockReproduction` | Medium | No spreading | None needed |
| Entity panels (sun/moon, festival, settings) | `EntityPanelModule`, UI Toolkit | Medium–High | Exception when selecting a building | try/catch; optional |
| Lantern Festival | EventBus, effects, bonuses, births, UI, saved state | Medium–High | Stuck or broken festival | Rule from risk #8; v1.1 |
| Great Flowering | Weather and cycle events, plant death, template replacement, custom forecast UI, settings | Medium–High | Wrong or missing events | v1.2 |

**Reflection on private fields (Ringtails only).**
- `TemplateNameMapper._templates`: needed so saves can reload Ringtails. Verified: aliases are added after names with `throwIfDuplicated: false`, so the prototype's alias fallback is sound.
- `BehaviorManager._rootBehaviors`: a private `List<RootBehavior>`; `AddRootBehavior` only appends. Verified.
- If either breaks: Ringtails load as Inkpaws, or work around the clock until exhaustion. The second needs a defined fallback, for example pausing Ringtail workplaces during the rest window.
- The prototype rightly avoided `Need._deltaPointsPerUpdate`, a private readonly field.

**Would need Harmony, and is designed out or dropped:** per-kind working hours, housing filtered by kind, steady vanilla population numbers overnight, faction-aware batch-control labels, fractional water bands, the Long Nap.

## 3. Technical claims checked

**Wrong or misleading**
- **Treadwheel speed** (water.md "Inkpaws are slow walkers so lift less", DESIGN "a wheel turns faster under a quick walker"): `WalkerPoweredGenerator.GetBonusMultiplier` sums the `MovementSpeed` **bonus** multiplier per worker and divides by `MaxWorkers`. Base walking speed (`WalkerSpeedManagerSpec`, the data route in two-peoples §6) has no effect. A faster wheel under Ringtails needs a code `MovementSpeed` bonus.
- **water.md "a rename breaks loading, not saves"**: only spec types throw. Field renames are silent, and a spec rename in a global blueprint breaks every game.
- **water.md "validate.py checks every spec key against the DLLs"**: not implemented. `tools/validate.py` has no DLL schema check.
- **CONTENT vs DESIGN contradictions:**
  - Bamboo: "browns in drought and regrows" vs "first to die, replanted".
  - Pepper "can follow rice in a drained paddy": crop rotation was dropped, and arid plants need moisture 0, which a drained paddy next to water will not have.
  - Tea "dies if flooded": arid plants die on any moist soil, i.e. anywhere within moisture reach of water.
  - Paper lanterns are Ringtail-made (R) but are a decoration cost and the festival good. That breaks "a player who never builds a loft has a complete colony".
  - Soybeans are listed as a new good but are an Iron Teeth good. Including them is fine; just note it.
- **DESIGN "breed slowly", "12-hour start", "work faster", "live long"** read as data, but each needs code or an untested modifier. The procreation chance is a hardcoded constant.

**Verified**
- `GetSortingKey` throws `ArgumentOutOfRangeException` for any other label key.
- `MaterialRepository` throws on a duplicate material name and on a missing one; `IMaterialCollectionIdsProvider` is public.
- `TemplateService.GetSingle` (exactly one; uses active collections only).
- `ITemplateCollectionIdProvider`, `INeedCollectionIdsProvider` and `IGoodCollectionIdsProvider` are public.
- Working hours start at the daytime start.
- `ResourceBuildings = 20` in code.
- Starting goods hardcoded as Berries and Water.
- Direction-limiter semantics (`FlowLimitCalculator`).
- `Workplace.AssignWorker` throws on a worker-type mismatch.
- `WorkerOutfitService` uses `ToDictionary`.
- `NeedVerifier` rules (and they apply to every game).
- `GoodSpec`, `NeedSpec`, `TemplateSpec`, `WorkerTypeSpec` and recipes all support backward-compatible ids. Missing goods and recipes in a save are dropped gracefully.
- `NeedSpec.FavorableWellbeing` is a **private** `[Serialize]` property, so the schema dumper must include non-public properties.
- Mod load order sorts by `RequiredMods` and `OptionalMods`, then by display name and user priority.
- `MinimumGameVersion` only produces a warning.
- Bundles without `_win`/`_mac` load on both platforms.

**Still unverified:** `BlueprintModifiers` timing; material shadowing in game; whether Bindito finds configurators in assemblies loaded late (the Reskin's `.bin` pattern suggests yes); whether foresters replant marked spots after a tree is cut or dies; the noria working as one isolated node; unknown singleton/component save data being dropped when saved again (likely — so persistence must live in the always-loaded core); `UnlockableFactionSpec` omission.

## 4. Data fragility: tooling to build

1. **Spec schema dumper** (C#, `MetadataLoadContext` over `Timberborn_Data/Managed`): writes every `ComponentSpec` subclass with its `[Serialize]` properties (public and private), types and `SpecAlias` to `schema/<gameversion>.json`.
2. **Validator v2** (extends `tools/validate.py`). Every blueprint key and field must exist in the schema, and value types must match. It also checks:
   - Asset references (existing resource index plus mod files), with case matched exactly and forward slashes only.
   - Ids against `ids.lock.json`.
   - Global-uniqueness prefixes, including spec class names, save keys and bundle names.
   - "No custom spec in a globally indexed blueprint".
   - Material coverage of `MaterialCollection.Folktails`.
   - A `_win`/`_mac` pair for every bundle.
   - Need and collection usage, mirroring `NeedVerifier`.
3. **Catalogue + generator.** One source of truth (YAML or JSON per category), giving each item's `basis` (vanilla path or kit model) plus small, pure transforms (rename, recost, retheme, worker type, planter group). The generator:
   - writes into the build folder, not into `mod/`, so generated files are never hand-edited;
   - is deterministic (sorted keys, fixed float formatting) so binaries and blueprints stay byte-identical for Workshop deltas;
   - stamps each output with its source path and hash.

   It replaces the three generators that already exist: `src/pipeline/derive_vanilla_copies.py`, `proto/ringtails/tools/derive.py`, `proto/water/tools/gen_blueprints.py`.
4. **Required-API manifest per code module.** Built from the compiled feature assembly with Cecil or `MetadataLoadContext`: every external game type, method and field it references. At update time it is diffed against the new DLLs. At runtime the bootstrap resolves the whole list before loading the module, which turns `MissingMethodException`/`ReflectionTypeLoadException` into "feature off + notice".
5. **Game diff report** (`tools/game_diff.py old new`), covering:
   - the blueprint dump (changed, removed or renamed vanilla templates → which Inkpaws outputs are affected, via provenance);
   - the spec schema;
   - loc keys;
   - the resource index (materials, sounds, sprites);
   - the required-API manifests;
   - the Unity version.
6. **One command**: `tools/pandaborn.ps1 release` = pin check (game version vs dump) → generate → validate → `dotnet build` → bundles (win + mac, with the Unity version check) → assemble → package (Workshop folder + mod.io zip) → test suite → `report.html`. Subcommands for each stage.

## 5. Save safety: rules to fix now

- **Ids frozen forever:**
  - Manifest Id and Faction Id `Inkpaws`; the faction id is saved in every game.
  - Templates `*.Inkpaws`.
  - Goods, needs, recipes, worker types, collections and loc keys `Pandaborn*` / `Pandaborn.*`.
  - Spec classes `Pandaborn*Spec`; save keys (components and singletons) `Pandaborn.*`.
  - Bundles `pandabornfactions*_win|_mac`, distinct from the Reskin's.
- `ids.lock.json` is append-only. Never delete or reuse an id. A replacement carries `BackwardCompatibleTemplateNames`/`BackwardCompatibleIds`, and a building retired from collections keeps an alias, otherwise saved instances vanish.
- **Code architecture:**
  - `Pandaborn.Bootstrap.dll` holds only `IModStarter`. It runs the pre-load checks, loads each `.bin` once per AppDomain, and logs which features are on.
  - `Pandaborn.Specs.bin` (all spec records, always loaded) and `Pandaborn.Core.bin` (persistence carriers, self-check, notices) load first.
  - Feature `.bin`s load only if their required-API check passes.
  - Spec records and persistence must stay loaded even when the behaviour is off, so a disabled feature's data still deserialises and is saved back unchanged.
- **Degradation rule:** a building with its code module off must still be a sensible vanilla building.
- **Temporary effects:** nothing temporary goes into saved vanilla state.
- **Versioned save data:** our persisted data carries a version number and is read tolerantly (`Has()` checks). Optional features (Ringtails, events) leave saves loadable when off: Ringtails fall back to Inkpaws through the alias.
- **Release gate: upgrade test.** Archive each release build and a golden save (Normal, day 20 or later). Before each release, load every archived golden save in the new build and assert no loading issues and identical counts per template, plus good totals.

## 6. Compatibility

- **Harmony:** not used. Test with the popular Harmony mods installed. Another mod already patches `GetSortingKey` on this machine.
- **Mod Settings:** optional, through the `.bin` pattern. For 1.0, settings can be per-save toggles on the Village Hall panel, or none.
- **TimberApi, Moddable Tool Groups, Ladder, Choo Choo:** test that they load together, that the Folktails toolbar is unchanged, and that the Inkpaws toolbar has no empty or duplicated groups.
- **TimberCommons:** swaps `WaterOutput` through Harmony; test the noria and the lift with it installed.
- **Other faction mods:** check ids, spec class names, recipe ids and bundle names; run a combined load plus a new game for each faction.
- **Owner's Reskin:** both enable orders; Inkpaws coats must survive; "beavers untouched" checked by mesh path.
- **Mods adding goods or needs with common names:** prefixes make clashes impossible on our side. Add a test with a dummy mod that defines common ids like `Tea` or `Rice`.
- **Third-party support:** publish a modder's guide.
  - Add buildings to collection id `Buildings.Inkpaws` from a file in your own mod. It is inert if Inkpaws is absent.
  - Existing `.Folktails` blueprint paths can be listed directly. That works only if (a) material shadowing covers every Folktails material name and (b) Planks stays a usable good (decision #3).
  - Use the vanilla tool groups.
  - Use `OptionalMods: [JigglyPanda.PandabornFactions]` for load order.

## 7. Scope, order and repository

**1.0 cut line.** One people, complete without Ringtails.
- Water identity: spout, flume set, noria, dew collector, cisterns.
- Bamboo, poles and the food ladder: shoots, rice, steamed rice, cabbage, soybean/tofu, dumplings, pickles, tea, persimmon cakes. Hot pot if it fits.
- Golden afternoon (12 h + speed bonus) and the Rest need with hammocks.
- Kindergarten and play, re-themed infrastructure, Wooden Oxen as re-skinned bots, one monument (Paifang), and the wonder.
- **About 20 new models:**
  - Homes and centre: Den, Courtyard House, Village Hall.
  - Food: Steamer, Paddy House, Hill Farm, Dumpling Kitchen, Pickle Cellar, Tea Drier, Drying Rack.
  - Water and power: cistern set, spout, flume kit, noria, dew collector, water wheel, kite windmill.
  - Leisure and monuments: hammock, teahouse, kindergarten, swing, Paifang, Sky Lantern.
- **7 plants:** river bamboo, rice, cabbage, tea, pepper, persimmon, lacquer tree. Soybean uses the vanilla model.
- Icons for all new goods and buildings. Re-themed buildings may keep vanilla icons, or batch-rendered ones.
- Final portraits and 2 outfits.
- **Code:** bootstrap/core plus three small public-API modules (flume, dew, golden afternoon). No reflection, no Harmony.

**1.1:** Ringtails, if the gate and soak pass, with lofts, courier and forager, a scaled Inkpaw body with a red coat or the real body. Lantern workshop and the Lantern Festival. Nursery and the "welcome cubs" switch with a vanilla fallback. Lotus. Opera stage, star tower, hot spring, ink studio.

**1.2:** Great Flowering, cloud bamboo and bamboo rice. Tradition. Drum Tower, Great Sitting Panda, Hall of Harvests. Faction tutorial.

**Drop:** Long Nap, charcoal filter, lantern colours tied to Tradition (use science unlocks), Great Kite Array (a larger kite windmill variant instead), faction-aware batch labels.

**Work order. Every step ends in a releasable build.**
- **A. Foundation** (one tooling agent plus one code agent):
  - id freeze and lock file, schema dumper, validator v2, catalogue generator, bootstrap/specs/core, one command, self-check notice;
  - in-game stage-0 checks: Planks re-skin, material shadowing with provider fallback, custom spec through `.bin`, `BlueprintModifiers` on a need;
  - Reskin update.
- **B. Playable core in data on stand-in models:** all goods, needs, recipes, plants and copies; water modules; golden afternoon; first hour tuned with the colony model.
- **C. Look:** material re-theme, then the building kit of parts, then identity models in priority order (homes → kitchens → water → leisure), then plants and icons. Each one replaces a stand-in.
- **D. Release:** balance per difficulty, soaks, compatibility matrix, Mac, store pages.

The Ringtail gate prototype continues on its own branch in `proto/`.

**Long poles:** the building kit (blocks every model), plant growth stages, the Ringtail body (beaver UV layout, 61 animations, maybe 150 MB), material-shadowing validation, and serial game-test time.

**Lanes that can run in parallel without collisions:** tooling; one lane per code module (each in its own assembly folder); catalogue per category file; art per model folder (`art/models/<Id>/` with its own script and outputs); plants; icon renderer; balance model; harness core (single owner).

**Single-owner hot spots:** the faction blueprint, manifest, harness core, validator and build scripts.

**Contributions through fragments only:**
- loc as `Localizations/enUS_Pandaborn<Feature>.csv` (multiple files load);
- collection files per feature (collections join by `CollectionId`);
- scenarios as `tests/scenarios/<feature>/*.json`.

**Suggested layout:**
- `catalogue/` (data, `ids.lock.json`, `vanilla.pin.json`)
- `src/gen/` (generator and transforms)
- `src/code/<Module>/` (with a `FEATURE.md` listing its game touch points)
- `art/`
- `mod/PandabornFactions/` (hand-written data only)
- `tests/scenarios/`
- `tools/`

## 8. Testing

**Automated, required before 1.0:**
- Load to the main menu with only this mod, with the Reskin, and with a curated set of popular mods.
- New Inkpaws game on Easy, Normal and Hard: 3 days, no errors.
- Scripted colony soak of 20+ days per difficulty, including a drought: population above 0, no starvation, no exceptions.
- Save and reload with counts compared.
- Golden-save upgrade from the previous release (§5).
- Grid session: place and dev-finish every template in the Inkpaws collections; open every entity panel and batch-control tab; produce every recipe with dev-supplied inputs (output > 0); growth and death for every plant (moist, dry, wet, flooded).
- Water probes: flume one-way and sealed sides, spout depth, noria with and without current, dew output during drought.
- Folktails and Iron Teeth unchanged, compared semantically: template, good and need lists, toolbar, and character mesh paths — with this mod on vs off.
- Disabled-feature runs: each module forced off through a dev switch. The game must load, saves must load, and the notice must appear.
- Validator and game diff on every build.
- Performance sample with 200 characters.

**Needs the owner's eyes:**
- Art quality and readability by day and night (glow), and the "Folktails with a paint job" judgement.
- Whether the first hour feels cozy rather than brutal.
- Text tone and UI overflow (screenshots help).
- Mac on real hardware.
- Store pages and AI disclosure.

## 9. Mac and distribution

- Build `_win` and `_mac` for every bundle with the game's exact Unity version. Unity needs Mac build support installed. The Reskin pipeline has never produced a Mac bundle.
- Use only lowercase-safe, exact-case, forward-slash paths. C# gets the folder from `IModEnvironment`.
- Keep the root folder to manifest, thumbnail and data. Workshop and mod.io get the same tree. Use the same `Version` on both; bump it rarely, since every bump warns on old saves.
- Use `version-X.Y` only for experimental-branch emergencies, with a floor folder, and accept that it doubles the download.
- Investigate cutting the mesh frame budget before adding a second body.

## 10. Five decisions for the lead, now

1. **Freeze ids and adopt catalogue-plus-generator.** Faction `Inkpaws`, `.Inkpaws` templates, `Pandaborn*` globals, specs and save keys, append-only `ids.lock`. Generated blueprints are never hand-edited.
2. **Adopt the code architecture and the degradation rules.** Bootstrap + always-loaded Specs/Core + per-feature `.bin` loaded only after its game references check out. Data alone must behave like vanilla. No saved vanilla state for temporary effects. No Harmony.
3. **Poles = faction-scoped re-skin of vanilla `Planks`** (and possibly TreatedPlanks/PineResin), if the stage-0 modifier test passes. Otherwise new goods with generated recost.
4. **Ringtails ship in 1.1, not 1.0**, unless the gate and soak pass by a fixed date. Decide the body now (scaled panda body with a red coat for 1.1; true red-panda body later) and move lanterns off the Ringtail-only list.
5. **Commit to the look strategy before modelling:** material shadowing with a code fallback to `Folktails`, generated coverage, and the building kit of parts built before any identity model. Fix the Mac support level and mesh size budget at the same time.
