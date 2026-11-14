# Two peoples: technical design

Game: Timberborn 1.1.2.8. Code paths in the study (§1–16) are relative to `E:\PandabornDev\reference\decompiled`;
blueprint paths to `E:\PandabornDev\reference\Blueprints`.

**How to read this document.** §0 is the design as built and shipping, in one page: read it first. §17–19 are the
results that prove it (prototype, shipping module, phase 3), newest last. §1–16 are the original feasibility study
(research only, written before any code ran). They are **superseded**: kept because their facts about the game code
are still correct and still cited, but their *plan* (shift flipping on shared workplaces, crews, litters, a per-kind
appetite, Long Nap, a crew panel) is not what was built. Where §1–16 and §0 disagree, §0 is right.

---

## 0. The design as built

**One sentence.** Inkpaws work the day; once the first Moon Loft is finished a Ringtail family moves in, and
Ringtails work the night in their **own** night posts, from the afternoon bell to dawn, and sleep through the morning.

| Topic | As built | Where proven |
|---|---|---|
| Two kinds | Ringtail adult and kit are hidden templates (in no template collection), so the vanilla factory still finds one adult; our factory creates them; one reflection write registers them in `TemplateNameMapper` for saves | §17.3, §18.6 |
| Work | Worker type `PandabornRingtail` (`IgnoresWorkingHours`). Three night posts (Builders', Courier, Foragers') keep `Beaver` in data; the module switches them to Ringtails. **No shift flipping, no shared workplaces, no crews.** Inkpaw workplaces stay Inkpaw | §17.1, §18 |
| Hours | Shift start = the bell (the first Core `IWorkdayClock` with a locked day, i.e. Bell's; else the working-hours slider), clamped to 4 h .. nightfall. Rest from dawn to the shift start: a root behaviour inserted by reflection above the worker behaviour | §17.3, §18.6 |
| Stats | Data only: Inkpaw walking speed, never slowed by a load, lifting 14. Same needs, appetite and wellbeing tables as Inkpaws (the per-kind appetite was dropped) | §17.8 |
| Arrival | Once per save, when the first Moon Loft is finished: 2 adults and 1 kit at its door, the night posts unlock for free, one message, the red panda twitter | §18.6, §19 |
| Births | `LoftNursery`, each dawn, per loft: one kit while the district has a Ringtail adult (any loft), open night jobs (Ringtail-typed posts' desired workers minus Ringtail adults and kits), nobody critically hungry or thirsty, and a free kit slot. Kits grow into Ringtail adults. Population follows **night jobs**, not beds | §19 |
| Housing | Lofts are Ringtail homes (`LoftHousingRule` swaps an Inkpaw out for a Ringtail); Inkpaws may use spare loft beds; an Inkpaw lodger moves out when the nursery has a kit to raise there (cub first) | §17.4, §18, §19 |
| Interface | Ringtail badge; a second population row; sun mark on every Inkpaw workplace, moon mark on night posts, nursery line on lofts; "Closed for the day" status on posts; moon arc on the day clock. All behind `SafeUi` | §18.5, §19 |
| Sound | Night clapper when the shift starts (2.5 s after the bell), only with Ringtails; twitter at arrival; silent if a clip is missing | §19 |
| Saved | The arrival flag in `PandabornStore`. Nothing per colonist or building (no `PandabornEntityState` needed) | §19 |
| Without the module | Data alone: saved Ringtails load as Inkpaws (permanent alias), night posts become Inkpaw workplaces (`Pandaborn.RingtailsFallback`), lofts are plain homes | §18.2, §18.6 |
| Data | Generated from the catalogue (§18.1 adopted); `proto/ringtails` is only the test probe | §19 |
| Not built (bets) | Long Nap, Wooden Oxen as a crew setting, crews per shift, walking in from the map edge, a toolbar moon mark (art) | — |

---

# Part B: feasibility study (superseded, see §0)

Original status line: feasibility study, 2026-11-14 (research only). The design target then was Pillar 1 as first
rewritten: automatic day and night crews on every workplace, Ringtails arriving with the first loft, and an optional
"Long Nap" bet.

---

## 1. Verdict (study, superseded)

* **Two living kinds in one faction is buildable without Harmony.** The way in is a *hidden second template*:
  the Ringtail adult and child blueprints carry the same `BeaverSpec`/`AdultSpec`/`ChildSpec` as any beaver but are
  **not listed in any template collection**, so `TemplateService.GetSingle<AdultSpec>()` still finds exactly one
  (the Inkpaw). Every vanilla decorator and every `HasComponent<AdultSpec>()` check then treats Ringtails as normal
  colonists. Cost: our own factory, our own grow-up and birth hooks, and one reflection write into
  `TemplateNameMapper` so saves can reload them.
* **Two crews inside one workplace at the same moment is not realistic.** `Workplace.AssignWorker` throws on a
  worker-type mismatch, `Understaffed` counts one pool, and `DistrictWorkplaceAssigner` files each workplace under
  exactly one worker type. Widening that is four or more Harmony patches on internal code.
* **Day and night crews by "shift flipping" is realistic and needs no Harmony.** A scheduler of ours switches each
  shared workplace's `WorkplaceWorkerType` to the Ringtail type at dusk and back to `Beaver` at dawn, through public
  API, and re-seats each workplace's remembered crew. Because the two crews never overlap in time, the player sees
  "a day crew and a night crew", which is exactly the design.
* **The weak spots are night sleep and vanilla statistics.** Ringtails need a day-sleep behaviour (one reflection
  insert into `BehaviorManager`'s root behaviour list), and vanilla population numbers wobble at dusk because the
  day crews of flipped workplaces count as unemployed overnight. Both are fixable; the second needs either our own
  panel (planned anyway) or one small Harmony postfix.
* **Fallback ladder, honest rating:** rung 1 (shared workplaces, shift flipping) is realistic and patch-free with
  three reflection touch points; rung 2 (one people per workplace) shares the same machinery and is only a little
  cheaper; rung 3 (one people, coat variety) is data-only. Recommend building toward rung 1, with a stage gate
  after the first prototype (section 13).

---

## 2. Facts checked (the brief's "already found" list) (study, superseded)

| Claim | Result |
|---|---|
| `WorkerTypeSpec` is data, ids `Beaver`/`Bot`, `IgnoresWorkingHours` | **True.** `Timberborn.WorkerTypes.dll/.../WorkerTypeSpec.cs`; blueprints `WorkerTypes/WorkerType.Beaver|Bot.blueprint.json`. Global, not per faction. `WorkerTypeService` is a plain dictionary; nothing enumerates all worker types. |
| `WorkerSpec.WorkerType` declares a template's kind | **True.** `WorkSystem/WorkerSpec.cs` (internal record). `Worker.WorkerType => _workerSpec.WorkerType` (`Worker.cs:43`), fixed per template. |
| `WorkplaceSpec` has `DefaultWorkerType`, `DisallowOtherWorkerTypes`, `WorkerTypeUnlockCosts` | **True.** `WorkplaceSpec.cs`. Note: `DisallowOtherWorkerTypes` allows **only the default type** (`WorkplaceWorkerType.IsWorkerTypeAllowed`), so "two of three" cannot be expressed, and a workplace with it set can never be flipped. |
| UI and stats hardcode two kinds | **True.** `WorkerTypesUI/WorkerTypeHelper.cs`, `WorkSystemUI/WorkerTypeToggle.cs`, `GameDistrictsUI/DistrictCenterFragment.cs`, `Population/PopulationDataCollector.cs`, `AutomationBuildings/PopulationCounter.cs` (Beaver/Bot fields). `DistrictDefaultWorkerType` hardcodes the default `"Beaver"` but accepts any string. |
| `BeaverFactory` uses `GetSingle<AdultSpec>/<ChildSpec>` | **True** (`Beavers/BeaverFactory.cs:36-37`). `GetSingle` counts specs with `is T` over `TemplateCollectionService.AllTemplates` only (`TemplateSystem/TemplateService.cs`), so a subclass of `AdultSpec` still counts. Off-collection blueprints are not counted. |
| `Worker.WorkingSpeedMultiplier` from `BonusManager.Multiplier("WorkingSpeed")` | **True** (`Worker.Tick`). |
| Walking speed and lifting in the blueprint | **True** (`WalkerSpeedManagerSpec.BaseWalkingSpeed`, `GoodCarrierSpec.BaseLiftingCapacity`). |
| Hunger/thirst = `NeedSpec.DailyDelta`, needs filtered by `CharacterType` | **True.** `GameFactionSystem/FactionNeedService.cs`: every non-bot gets all `CharacterType == "Beaver"` needs. The only reader of `DailyDelta` is the `Need` constructor (`NeedSystem/Need.cs:114`), which bakes it into a private per-entity field `_deltaPointsPerUpdate`. Game-mode Food/WaterConsumption scales it globally (`NeedModificationService`). |
| `BreedingPodSpec`, `ProcreationHouseSpec`, `DwellingSpec` exist | **True.** `ProcreationHouseSpec` is internal and fully replaceable by our own spec (section 7). |

New facts that matter:

* **Rebinding is impossible.** Bindito throws "it's already bound" (`Bindito.Core.Internal/Binder.cs`,
  `BindingBuilderRegistry.cs`). We cannot replace `BeaverFactory`, `IWellbeingTierService` or any vanilla service.
  Extension points are: `MultiBind<TemplateModule>` (decorators), `MultiBind<EntityPanelModule>` (panel fragments),
  `EventBus` events, new singletons, and new specs.
* **Decorators match the exact spec type or an interface, not base classes**
  (`TemplateInstantiation/TemplateInstantiator.cs`, `DecorateTypeAndInterfaces`). `HasComponent<T>` matches with `is T`
  (`BaseComponentSystem/TypeIndexMap.cs`).
* **`FactionSpec.BlueprintModifiers` is a faction-scoped JSON merge onto any blueprint path**, applied only when that
  faction is active (`GameFactionSystem/FactionBlueprintModifierProvider.cs`, initialised in `FactionService` line 60).
  This makes "global" data such as `NeedSpec` and `WellbeingTierSpec` adjustable for the Inkpaws only. *Untested:*
  blueprints are deserialised lazily, so a modifier only applies if nothing read that blueprint before
  `FactionService.Load`. Worth a stage-0 check because it removes several code needs.
* **Existing bug in the mod:** `InkpawAdult/InkpawChild.Inkpaws.blueprint.json` use `EntityNameLocKey`
  `Inkpaws.Adult|Child.TemplateName`. `CharactersBatchControl/CharacterBatchControlTab.GetSortingKey` throws
  `ArgumentOutOfRangeException` for any key other than `Beaver.Adult.TemplateName`, `Beaver.Child.TemplateName`,
  `Beaver.Population.Contaminated`, `Bot.TemplateName`. Opening the Characters tab of the batch-control window in an
  Inkpaws game should crash it. Use the vanilla keys (and change the displayed name elsewhere) — Ringtail templates
  must do the same.

---

## 3. Architecture for two living kinds (study, superseded)

### Options compared

| | A1: second pair in the collection | **A2: hidden second pair (recommended)** | B: one template + species component |
|---|---|---|---|
| Idea | Ringtail adult/child listed in `TemplateCollection.Inkpaws` | Ringtail blueprints exist as files but in no collection | One adult/child template; a per-entity component switches species |
| `GetSingle<AdultSpec>` | **Throws** (two found). Harmony on `BeaverFactory.Load` unavoidable | Unaffected | Unaffected |
| Ringtail marked without `AdultSpec` instead | `MigrationTrigger.RegisterDistributorToCheck` **throws** for a citizen that is neither `AdultSpec`, `Child` nor `BotSpec`; `Dweller._isAdult` false breaks housing | n/a — keeps `AdultSpec` | n/a |
| Own mesh, walk speed, lifting, animation table, collider, outfits per kind | Data | **Data** | Code: runtime mesh swap of a vertex-animated timbermesh is impractical; bonuses for speed/lifting |
| Worker type per kind | Data (`WorkerSpec`) | **Data** | Reflection: replace `Worker._workerSpec` before the citizen is registered (fragile ordering) |
| Save/load | Native | **One reflection write** into `TemplateNameMapper._templates` | Own persisted component; must be applied before `Worker`/`Citizen` registration |
| Births / growth | Needs Harmony anyway (factory) | Own factory, own grow-up trigger, own nursery | `CharacterInit.Child` carries species; vanilla growth works |
| Verdict | Harmony-only | **Best: data for everything visual and physical, small code** | Fallback for "same body, different coat and stats" |

### A2 in detail: what the hidden template touches

Ringtail blueprints: `Characters/Pandaborn/RingtailAdult.Inkpaws.blueprint.json`, `RingtailChild.Inkpaws.blueprint.json`
— copies of the Inkpaw ones with `BeaverSpec`, `AdultSpec`/`ChildSpec`, `WorkerSpec.WorkerType = "PandabornRingtail"`,
own model, own walking/lifting values, plus our marker spec `PandabornRingtailSpec` (drives our decorators). They
are not added to `TemplateCollections/...`. Every blueprint file is indexed by `SpecService` regardless of
collections (`BlueprintSystem/SpecService.cs`, `GetBlueprint(path)` is public on `ISpecService`), and every other
faction's adult template is already "an off-collection blueprint with `AdultSpec`" when that faction is not active,
so this is a normal state for the game.

| Place | File / member | What happens with a hidden Ringtail | Action |
|---|---|---|---|
| Factory | `Beavers/BeaverFactory.Load` | Sees only the Inkpaw pair | None. Our `RingtailFactory` (singleton): `ISpecService.GetBlueprint(path)`, `TemplateInstantiator.CacheInstance`, `EntityService.Instantiate(new EntitySetup.Builder(bp).AddInitComponent(new CharacterInit(...)))` — all public; mirrors `BeaverFactory.CreateBeaver` |
| Save/load | `WorldPersistence/WorldEntitiesLoader.TryInstantiateEntity` → `TemplateNameMapper.GetTemplate` | Unknown name → entity dropped with a loading issue | **Reflection:** our `ILoadableSingleton` taking `TemplateNameMapper` in its constructor (so it loads after it; `SingletonSystem/SingletonListener` orders by provision) adds the two `TemplateSpec`s to private `Dictionary<string, TemplateSpec> _templates`. Entities load later (`INonSingletonLoader`). Fail loudly if the field is missing. Only when the Inkpaws faction is active |
| Child grows up | `Beavers/Child.GrowUp` → `BeaverFactory.CreateAdultFromChild` | Would make an **Inkpaw** adult | Our `RingtailGrowth` component on the Ringtail child: when `Child.GrowthProgress >= 0.995` (vanilla fires at 1.0), deactivate the child and create a Ringtail adult with `CharacterInit(child)` exactly as `CreateAdultFromChild` does; set `Child._grownUp` by reflection as a guard (or rely on the earlier threshold). `Adult.InitializeEntity` then replaces selection and destroys the child as in vanilla |
| Births | `Reproduction/NewbornSpawner` (uses `BeaverFactory`) | Vanilla procreation only makes Inkpaws | Lofts get our nursery spec instead of `ProcreationHouseSpec` (section 7) |
| Population lists | `Beavers/BeaverPopulation`, `GameDistricts/DistrictPopulation`, `BeaverCollection` | Counted as beavers/adults/children (has `Beaver`, `ChildSpec`) | None. Per-kind counts come from our own registry |
| Dwellings, beds | `DwellingSystem/Dweller.Awake` (`HasComponent<AdultSpec>`), `AutoAssignableDwelling`, `DwellerHomeAssigner` | Works as for any beaver. **Anyone can live anywhere**; there is no filter hook in `CanAssignDweller` | Data. Kind-specific housing would need Harmony (prefix on `AutoAssignableDwelling.CanAssignDweller`) — see design changes |
| Migration | `GameDistrictsMigration/MigrationTrigger`, `AdultsDistributorTemplate`, `ChildrenDistributorTemplate` | Ringtails migrate as adults/children; the player cannot pick a kind | None |
| Wellbeing tiers | `Wellbeing/WellbeingTierService` (internal, interface-bound): Bot / not-child / child | Ringtails use the adult tables | None (identical tables; section 6) |
| Needs | `NeedSystem/NeedManager.GetNeeds`: `BotSpec` or beaver needs | Same needs as Inkpaws | Appetite via per-entity tweak (section 6) |
| Names | `Beavers/BeaverEntityNamer`, `BeaverNameService` (global `Beaver.NamePool`) | Share the name pool | Optional own namer later |
| Portrait / subtitle | `EntityPanelSystem/EntityBadgeService` picks the highest `EntityBadgePriority`; `BeaversUI/BeaverEntityBadge` has 10 | Would show the faction's Inkpaw avatar | Our `IEntityBadge` component with priority 11+ on both kinds: own avatar, contaminated avatar, "Ringtail, age N" subtitle. Clean extension |
| Empty work slots | `CharactersUI/CharacterButton.ShowAdultEmpty` uses `FactionSpec.Avatar` | Inkpaw silhouette for an empty night slot | Cosmetic; our own crew view replaces it (section 9) |
| Batch control, Characters tab | `CharactersBatchControl/CharacterBatchControlTab.GetSortingKey` | Throws for non-vanilla loc keys | Ringtail templates use `Beaver.Adult|Child.TemplateName` |
| Batch control, other tabs | `WorkSystemUI/WorkplaceWorkerTypeBatchControlRowItemFactory` (two-way toggle once bots exist) | Shows Beaver/Bot only | Accept or reconcile (section 9) |
| Automation Population Counter | `AutomationBuildings/PopulationCounter.GetMeasurement` | Totals include Ringtails; worker modes only Beaver + Bot | Accept for now; a Ringtail-aware counter is our own building later |
| Statistics graphs | `PopulationStatisticsSampling/PopulationSampler` | Ringtails inside adult/child counts | Accept |
| Achievements, tutorials | `Achievements/*` check `BeaverSpec` | Ringtails count as beavers | None |
| Dev "spawn beaver" tool | `BeaversUI/BeaverGeneratorTool` | Spawns Inkpaws only | Dev harness gets its own spawn command |

---

## 4. Day and night crews on one workplace (study, superseded)

### What assumes one kind per workplace

| Code | Assumption |
|---|---|
| `WorkSystem/Workplace.AssignWorker` | Throws `InvalidOperationException` if `worker.WorkerType != WorkplaceWorkerType.WorkerType` |
| `Workplace.Understaffed/Overstaffed/DesiredWorkers` | One pool of slots |
| `WorkSystem/DistrictWorkplaceAssigner` (internal) | One `WorkplaceAssigner` per worker-type string; each workplace sits in exactly one, moved on `WorkerTypeChanged` |
| `WorkSystem/WorkplaceAssigner`, `UnemployedWorkers` (internal) | Fills the highest-priority understaffed workplace with `HashSet.First()` of the unemployed of that type |
| `WorkplaceWorkerType` | Single persisted string |
| `PopulationWorkStatistics/WorkplaceWorkerCounter`, `DistrictEmploymentStatisticsProvider` | One `EmploymentStatistics` per workplace, keyed by its current type |
| `WorkSystemUI/WorkplaceFragment`, `WorkerView` | Lists `AssignedWorkers`; empty slots drawn by the workplace's type |
| `Workplace.ValidateEnterable` | Enterable capacity ≥ `MaxWorkers` |

A second workplace-like component on the same building is impossible: `GetComponent<Workplace>()` throws on two
components of one type (`ComponentCache.GetCachedComponent`), and dozens of systems call it.

### Options

| Option | How | Patches | Verdict |
|---|---|---|---|
| W1 Widen the workplace | Same worker type for both peoples, doubled slots, per-worker hours | Harmony on `WorkerWorkingHours.AreWorkingHours` (per-worker hours) and on internal `WorkplaceAssigner.AssignStalestUnemployed` (pick the right people per half), or slot caps fight the vanilla assigner every tick. Without the cap, four Inkpaws can fill a "2 + 2" mill in daytime: a throughput exploit | No |
| W2 Two simultaneous types | Patch `Workplace.AssignWorker`, `Understaffed`, `DistrictWorkplaceAssigner`, statistics | 4+ patches on internal code | No |
| **W3 Shift flipping (recommended)** | Our scheduler calls public `WorkplaceWorkerType.SetWorkerType` at the shift changes and re-seats remembered crews with public `Workplace.AssignWorker` | None | Yes |

### W3 in detail

* **Worker types.** Inkpaws keep `Beaver` (vanilla hours, vanilla UI, vanilla district default). Ringtails get
  `WorkerType.PandabornRingtail` with `IgnoresWorkingHours: true`. A Ringtail therefore works whenever it is employed
  (`WorkerRootBehavior.Decide`: `Employed && AreWorkingHours`), and it is employed only during the night shift because
  the scheduler only opens Ringtail workplaces then. No per-worker hours patch is needed.
* **Scheduler** (`PandabornShiftScheduler`, a tickable singleton, Inkpaws faction only). Reads
  `WorkingHoursManager.EndHours` and `IDayNightCycle.HoursPassedToday` (day 0–16 h, night 16–24 h by default:
  `TimeSystem/DayNightCycle.BoundsInHours`; Inkpaw working hours default to the whole daytime and follow the
  player's working-hours slider).
  * *Night shift start* (Inkpaw `EndHours` + a short gap, so dusk is shared leisure when the player shortens Inkpaw
    hours): per district, take workplaces whose crew setting is *both* or *night*, finished, unpaused, not on Oxen,
    in `WorkplacePriority.Priority` then `InstantiationOrder`. Flip only as many as the district's available Ringtails
    can staff. Then, for each flipped workplace, first re-assign its remembered night crew (unassign them elsewhere if
    needed), and let the vanilla assigner fill the rest.
  * *Night shift end* (before Inkpaw start hours): flip back to `Beaver`, re-seat the remembered day crew.
  * *night only* workplaces stay on the Ringtail type all day (they sit empty by day); *day only* never flip.
  * Before the first Ringtail exists, nothing flips: the colony behaves exactly like vanilla.
* **Per-workplace component** (`PandabornCrews`, decorator on `Workplace` for Inkpaws buildings): persists crew
  setting, remembered day crew, remembered night crew (entity references via `ReferenceSerializer`). Listens to
  `WorkplaceWorkerType.WorkerTypeChanged`; a change it did not cause is reconciled (a vanilla toggle click on *Bot*
  means "Oxen"; on *Beaver* means "both"). Also handles copy-settings (`DuplicateFrom` copies the type).
* **Why it is safe:** every call is a supported vanilla path. `SetWorkerType` already unassigns everyone (used when
  the player toggles beavers/bots), `Worker.Unemploy` fires `GotUnemployed`, which `Hauler`, `Planter` and other
  listeners already handle; carried goods are finished by `CarryRootBehavior`. After load,
  `Worker.AssignToWorkplaceAfterLoad` keeps a worker only if types match, which stays consistent.
* **Costs and side effects**
  * At night, the day crews of flipped workplaces are unemployed in vanilla's eyes. The top-bar population panel
    (`PopulationDataCollector`, Beaver workforce) and the automation counter show them as unemployed overnight.
    The scheduler flips only what Ringtails can staff, which keeps this small, and our own population panel shows
    crews per shift. A fully clean vanilla panel needs a Harmony postfix on `PopulationDataCollector.CollectData`.
  * Unemployed Inkpaws at night may be grabbed by vanilla for an unflipped workplace; the dawn re-seat moves them
    back. Expect a little churn in "who works where" logs.
  * `NoUnemployedStatus` (alert after 0.1 day with no workers) would fire on flipped-but-empty workplaces; flipping
    only staffable workplaces avoids it, *night only* workplaces will show it by day (acceptable, or document).
  * Workplaces with `DisallowOtherWorkerTypes: true` cannot flip. Faction buildings must keep it false; that also
    means the vanilla toggle offers bots everywhere once a bot exists (reconcile as above).

### Answers to the coordinator's specific questions

* **Can one workplace accept two kinds at once?** No, not without W1/W2 patches. With W3 it holds one kind at a
  time and alternates, which is invisible to the player as long as the UI talks about crews.
* **Per-worker working hours?** `WorkerWorkingHours` (`WorkSystem/WorkerWorkingHours.cs`) caches
  `WorkerTypeSpec.IgnoresWorkingHours` at `Awake` and otherwise reads the single global `WorkingHoursManager`.
  There is no per-kind schedule. A true per-kind schedule is a Harmony patch on the `AreWorkingHours` getter. W3
  side-steps it by controlling *employment* instead of hours.
* **Least invasive way to two crews:** W3. One scheduler singleton, one workplace decorator, no patches.

---

## 5. Night workers: sleep, beds, leisure, day stage (study, superseded)

How beavers decide (verified):

* Behaviour order (`BeaverBehavior/BeaverBehaviorInitializer`): CharacterControl, Dead, Carry, Die, Contaminate,
  CriticalNeeder, Stranded, **Worker**, **Needer**, Wander. While employed and in working hours, work wins; needs are
  served only when critical.
* Sleep is the "essential" need behaviour (`SleepSystem/SleepNeedBehavior`). `BeaverNeedBehaviorPicker.GetBestNeedBehavior`
  (internal) picks it when `HoursToNextStartOf(Daytime) < sleep duration × 1.2`, or when Sleep is at its minimum.
  `Sleeper.CalculateWakeUpTimestamp` wakes at dawn, or when full if that is more than an hour away. Sleep need:
  `Needs/Need.Beaver.Sleep.blueprint.json` (−0.6/day, range −0.2…0.8, critical below 0, "Action" type).
* Day-stage checks elsewhere are cosmetic only: `Attractions/AttractionFire` (fire at night),
  `IlluminationUI/NightTimeLightController`, `GameSound/DayNightAmbientSound`, `WorkSystem/WorkingHoursBell`,
  `Workshops/WorkshopProductivityCounter` (uses `WorkplaceWorkingHours`, which reads the type's
  `IgnoresWorkingHours`). No vanilla night movement penalty exists.

What breaks for Ringtails under W3 and the fix:

| Issue | Cause | Fix |
|---|---|---|
| Ringtails never go to bed at night | They are working (Worker root wins) | Intended |
| Ringtails do not sleep by day | Picker only sleeps near dawn or at minimum points | **Our `RingtailRestRootBehavior`** inserted just above `NeederRootBehavior` (after `WorkerRootBehavior`): during the Ringtail rest window, if Sleep is below a threshold and the Ringtail has a home, `WalkInsideExecutor.Launch(home Enterable)` then `Sleeper.LaunchExecutor(home.SleepEffects)` (both public). Wake-up is "when full" because dawn is far away. Insertion needs **reflection** on `BehaviorManager._rootBehaviors` (private `List<RootBehavior>`; `AddRootBehavior` only appends). Find the index of `NeederRootBehavior` by type and insert before it; fail loudly if not found |
| Exhaustion mid-shift if the above fails | Sleep critical → `CriticalNeederRootBehavior` | Natural safety net; the test watches for the Exhaustion status |
| Beds | Any home works by day; `Dwelling` has no time logic | None. Lofts as homes are just dwellings |
| Leisure | Picker budget = hours to dawn − sleep duration: large by day | Works: Ringtails take leisure by day, Inkpaws by evening |
| "Work ended" handling | Shift end = `SetWorkerType` → unassign | Vanilla path |
| Haulers, builders | Workplaces like any other; bots already work at night | None |
| Visibility at night | Dark scene | Lanterns/emissive art; design already plans it |

Cheaper data-only alternative to the rest behaviour (a bet): nap attractions whose `AttractionSpec.Effects` include
`Sleep` (hammocks, nap platforms — already in the leisure list). The picker would choose them when Sleep is low.
Untested: whether a Sleep-satisfying attraction is picked over the essential behaviour and what animation it plays.

---

## 6. Per-kind stats and appetite (study, superseded)

| Stat | Two templates (A2) | Notes |
|---|---|---|
| Walking speed | **Data**: `WalkerSpeedManagerSpec.BaseWalkingSpeed/BaseSlowedSpeed`, `MovementAnimatorSpec.AnimationSpeedScale` | |
| Lifting capacity | **Data**: `GoodCarrierSpec.BaseLiftingCapacity` | |
| Working speed | **Code (small)**: decorator calling `BonusManager.AddBonus("WorkingSpeed", delta)` at `Awake`. Bonuses are not saved; every source re-adds them, so this is load-safe | No data-only constant bonus exists (`AddBonus` callers: `Overburdenable`, `NeedPenaltyManager`, `WellbeingTierManager`, `WorkplaceBonuses`) |
| Life expectancy | **Code (small)**: constant `LifeExpectancy` bonus (`LifeSystem/LifeProgressor` divides progress by it). A second `ILongevity` would make `GetComponent<ILongevity>` throw | |
| Child growth | **Code (small)**: constant `GrowthSpeed` bonus on Ringtail kits | |
| Hunger/thirst (faction-wide "hearty") | **Data, untested**: `FactionSpec.BlueprintModifiers` on `Needs/Need.Beaver.Hunger|Thirst` | Leaves Folktails untouched |
| Hunger/thirst per kind | **Code + reflection**: after `NeedManager.Awake`, scale `Need._deltaPointsPerUpdate` and `_pointsWarningThreshold` (private readonly instance fields on the public `Need`), reached through `NeedManager._needs` (private; `Needs.TryGetNeed` is public). Re-applied on every instantiation, so load and growth are covered | No reader of `DailyDelta` other than the `Need` constructor, so nothing else drifts. The "food days left" UI does not use it |
| Wellbeing tier tables | Global per character type (`WellbeingTierService`: `BeaverAdult`, `BeaverChild`, `Bot`). Faction-wide changes via `BlueprintModifiers` (untested). **Per kind needs compensating bonuses** and the wellbeing summary UI (`WellbeingUI/WellbeingSummaryFactory`) would show the vanilla values | Recommend identical tables for both peoples |

---

## 7. Housing, births, arrival, Long Nap (study, superseded)

* **Vanilla procreation** (`Reproduction/ProcreationHouse`): on `Enterable.EntererAdded`, if the home has a free
  child slot (`Dwelling.HasFreeChildSlots && UnderpopulatedByChildren`; child slots = ⌊capacity/3⌋, desired
  children = adults/2), the entering adult and another adult dweller have an enabled `Procreator` and no critical
  need, and a 0.1875 roll passes, `NewbornSpawner.SpawnChild` → `BeaverFactory.CreateNewbornChild` with
  `CharacterBirthInit(district, dwelling, BeaverBornEvent)`.
* **Our nursery** (`PandabornNurserySpec { Kind, Chance, LitterMin, LitterMax, MinWellbeing }` + component, used
  instead of `ProcreationHouseSpec` on dens and lofts): same trigger (`Enterable.EntererAdded`, public), same slot
  checks, then:
  * den → one Inkpaw cub via `BeaverFactory.CreateNewbornChild` (public), only if the dwellers' wellbeing
    (`WellbeingTracker`) is at or above the threshold;
  * loft → a litter of Ringtail kits via `RingtailFactory`, capped by free child slots.
  The **house decides the kind**, not the parents, because the game has no way to steer who lives where.
  `Procreator` is internal; check `Enterer` readiness and `NeedManager.AnyNeedIsInCriticalState` (public) instead.
* **Ringtail arrival:** `PandabornRingtailArrivalSpec` on loft blueprints; the component implements
  `IFinishedStateListener`; a saveable singleton keeps the "arrived" flag. On the first finished loft: spawn a
  family at its access point with `CharacterBirthInit(district, loft dwelling, event)`, then post a message
  (section 10).
* **Starting population:** unchanged (game mode `StartingAdults/StartingChildren` → `StartingBeaversInitializer` →
  `BeaverFactory`). A mixed start, if ever wanted, is a `NewGameInitializedEvent` handler that spawns Ringtails
  and deletes some Inkpaws.
* **Long Nap (bet):** district toggle in our own district-center fragment. While on, Inkpaws get a forced-sleep
  root behaviour (same insertion as section 5, placed above `WorkerRootBehavior`) that walks home and runs
  `ApplyEffectExecutor.LaunchToTimestamp(homeSleepEffects, far timestamp, "Sleeping")` (public). Lower appetite:
  `NeedManager.DisableUpdate("Hunger"|"Thirst")` (public) plus a periodic small negative `ApplyEffect` (public) for
  the reduced rate; re-applied after load because `_updateEnabled` is not saved. Day workplaces lose their crews
  for the duration (Ringtails can take them at night). No Harmony. Risks: wellbeing of everything else decays,
  critical needs still interrupt, and behaviour on load mid-nap must be tested.

---

## 8. Appearance (study, superseded)

* **Own mesh:** Ringtail blueprint `Children.Model_Preserved.TimbermeshSpec.Model` → own `.timbermesh`. Must keep the
  node names the blueprint uses (`#Backpack`, `#CarriedInHands`, `#Head`, `#Collider`, `#ZiplineHarness`,
  `#PlantingParticles`, `#BuildingParticles`) and either the same animation names as
  `TimbermeshAnimatorControllerSpec.AnimatorStates` (61 adult / 39 child) or an edited state table in its blueprint.
  Material must come from the faction's material collections (`BeaverAdult`/`BeaverChild`).
* **UV layout:** keep the beaver UV layout for v1. Outfit overlays (`WorkerOutfitSpec` textures), injuries
  (`BeaverInjuryTextureSetterSpec`), need shader properties, the tail decal (`TailDecalSystem/TailDecalApplier`) and the
  fixed normal map all assume it. A new layout means a new material (Unity bundle) and new overlay textures.
* **Coat pool:** `BeaverTextureSetter.InitializeEntity` (decorator on `BeaverSpec`) sets `_BaseMap` from
  `FactionSpec.Textures/ChildTextures`, re-randomised on every load. Our `PandabornCoatSpec { Textures, ChildTextures }`
  plus a component in `IPostInitializableEntity.PostInitializeEntity` (runs after all `InitializeEntity`) calling
  `CharacterMaterialModifier.SetTexture(_BaseMap, ...)`. Code, tiny.
* **Scale:** bake into the mesh (safest), or try `TransformSpec.Scale` on the `Model_Preserved` child (vanilla uses
  `TransformSpec` on nested children; untested on characters). Collider attachment scale in `TemplateAttachmentsSpec`.
* **Portraits:** own `IEntityBadge` (section 3). Empty-slot silhouettes stay Inkpaw unless our crew view draws them.
* **Outfits:** `WorkerOutfitSpec` per `(Id, WorkerType, FactionId)` (`WorkerOutfitSystem/WorkerOutfitService`) — add
  `WorkerType: "PandabornRingtail"` copies. Data. Duplicate (Id, WorkerType) per faction throws.

---

## 9. UI (study, superseded)

| Element | Vanilla | Plan |
|---|---|---|
| Workplace panel | `WorkplaceFragment`: worker list + `WorkerTypeToggle` (visible only after `BotPopulation.BotCreated`) | Our `EntityPanelModule` fragment: sun/moon crew rows (remembered day crew, remembered night crew, idle slots) and the *day only / night only / both* setting. `SliderToggleFactory.Create` takes any number of items, and `SliderToggleItem.Create(Func<string>, Sprite, ...)` takes a sprite icon, so a three-way slider needs no USS |
| Beaver/Bot toggle | Two-way, appears once a bot exists | Keep; reconcile its clicks (section 4). Optional: hide the vanilla `WorkerTypeToggleWrapper` element by name from our fragment (no patch, but fragile) |
| District center | `DistrictCenterFragment` default worker type (two-way, after bots) | Our fragment for Long Nap and Oxen default; district default stays `Beaver` |
| Population panel / top bar | `PopulationDataCollector` Beaver + Bot only | Our panel: crews per shift, idle per shift. Optional Harmony postfix to keep the vanilla numbers steady overnight |
| Character panel | `EntityBadgeService` | Our badge |
| Batch control | Characters tab groups by loc key (throws on unknown); Workplaces tab two-way toggle | Vanilla loc keys; accept the two-way toggle |
| Automation Population Counter | Beaver/Bot only | Accept; own counter building later |

---

## 10. Tutorial and messages (study, superseded)

* `TutorialSystem/TutorialService.GetConfigurations` and `TutorialTriggers.Load` run tutorials **only if the
  current `FactionSpec` has `StartingFactionSpec`**. `TutorialSpec` blueprints are global and the vanilla ones are
  Folktails-specific (e.g. `Tutorials/Stages/Housing.BuildLodges` waits for `Lodge.Folktails`).
* A faction tutorial is possible in data: give Inkpaws `StartingFactionSpec` (only other user:
  `MainMenuPanels/TutorialToggleController`, which shows the tutorial toggle), neutralise every vanilla
  `TutorialSpec` for the Inkpaws only with `FactionSpec.BlueprintModifiers` (e.g. an unreachable
  `RequiredTutorialIds`), and add `TutorialSpec`/`TutorialStageSpec` blueprints using the existing step specs
  (`BuildingTutorialStepSpec` with `TemplateNames`, `SelectEntityStepSpec`, `SetWorkingHoursStepSpec`,
  `IncreaseDesiredWorkersStepSpec`, ...). Our tutorials must require a trigger id only our code fires
  (`ITutorialTriggers.AddTrigger`), so they never start for Folktails. Untested: that `StartingFactionSpec` on a
  second faction has no other effect (grep found none), and the lazy-modifier timing.
* One-off messages (Ringtails arrive, first drought, first Flowering): `NotificationSystem/NotificationBus.Post(text,
  entity)` (as `Adult` does for "grew up") or a modal via `CoreUI/DialogBoxShower`. Both public, no data needed.

---

## 11. Bots ("Wooden Oxen") (study, superseded)

* **Minimum for working bots:** one template with `BotSpec` in the faction collections (`BotFactory.Load` →
  `GetSingle<BotSpec>`; the mod has `Characters/Pandaborn/Bot.Inkpaws.blueprint.json` already), `WorkerSpec.WorkerType
  "Bot"`, a building with `BotManufactorySpec` + a `Manufactory` recipe (`BotsUpkeep/BotManufactory` spawns on
  `ProductionFinished`), `FactionSpec.BotAvatar`, worker outfits for `WorkerType: "Bot"`. Bot needs
  (`CharacterType: "Bot"`, e.g. `Needs/Need.Bot.Energy`) are optional: with none, bots run until old age
  (`BotLongevity`). Bots ignore working hours, so they are the natural night labour as well.
* **Rename/restyle:** template, mesh, `SimpleLabeledEntitySpec` must stay `Bot.TemplateName` (batch-control sort
  key), so the visible name comes from our badge and the faction's display text. `BotColors`
  (`Bots/BotColorsSpec`) drive illumination colour.
* **Hauling only:** `DisallowOtherWorkerTypes` cannot express "Inkpaws or Ringtails but not Oxen". Our `PandabornCrews`
  component treats *Oxen* as a crew setting that is only offered (and only accepted, reverting vanilla toggle clicks)
  on hauling posts and other allowed buildings. Clean, no patch.

---

## 12. Data, code, reflection, Harmony (study, superseded)

| Item | Kind |
|---|---|
| Ringtail templates, meshes, walk speed, lifting, animation tables, outfits, worker type, nursery/arrival specs on buildings, crews spec on workplaces | Data |
| Faction-wide appetite, wellbeing tables, tutorial gating | Data via `BlueprintModifiers` (untested mechanism) |
| `RingtailFactory`, growth hook, nursery, arrival, stat bonuses, coat setter, badge, shift scheduler, crews component, panel fragments, own population panel, rest root behaviour, Long Nap | Code (Bindito bindings, `TemplateModule` decorators, `EntityPanelModule`, `EventBus`) |
| `TemplateNameMapper._templates` (save/load of Ringtails) | Reflection, 1 field |
| `BehaviorManager._rootBehaviors` (day sleep, Long Nap) | Reflection, 1 field |
| `NeedManager._needs` → `Need._deltaPointsPerUpdate`, `_pointsWarningThreshold` (per-kind appetite) | Reflection, 3 fields; optional |
| `PopulationDataCollector.CollectData` postfix (steady vanilla numbers overnight) | Harmony, optional |
| `AutoAssignableDwelling.CanAssignDweller` prefix (kind-specific housing) | Harmony, not recommended |
| `WorkerWorkingHours.AreWorkingHours`, `BeaverNeedBehaviorPicker.GetBestNeedBehavior`, `Sleeper.CalculateWakeUpTimestamp` (true per-kind clock) | Harmony, not needed with W3 |

Reflection on private fields breaks on a rename exactly like a Harmony patch does, but needs no dependency and
fails at a single known line. Every reflection point must check the field exists at load and log one clear error
(and disable the feature) instead of throwing.

**Harmony, if ever needed.** Harmony is not in the game. The local convention is a dependency on the Workshop
"Harmony" mod (`RequiredMods: [{ "Id": "Harmony" }]`, as `Documents\Timberborn\Mods\PopulationControl` does).
Shipping our own `0Harmony.dll` is technically possible (mod DLLs are loaded with `Assembly.Load(bytes)` and
Harmony 2 shares patch state across copies), but two copies of the same assembly identity in one domain is a
known source of type-identity and load-order trouble, Mac support (Apple Silicon) would need its own check, and
it is not what players of Timberborn mods expect. If a patch becomes unavoidable, depending on the Harmony mod is
the honest answer; keep such patches optional and loaded late (the Reskin's `.bin` trick), so the core works
without them.

---

## 13. Risks, ranked (study, superseded)

1. **Day sleep for Ringtails** (reflection insert + custom root behaviour). If wrong, Ringtails collapse from
   exhaustion mid-shift and wellbeing sinks. Highest gameplay risk; prototype first.
2. **Vanilla statistics at night** (Inkpaws "unemployed" overnight on flipped workplaces; automation counters). UX
   confusion rather than breakage. Mitigated by flipping only staffable workplaces and by our panel.
3. **Hidden template save/load** (reflection into `TemplateNameMapper`). If the field changes in an update,
   Ringtails vanish on load. Must be covered by an automated save/reload test.
4. **Shift churn bugs**: reservations, half-finished recipes and carried goods at every flip; copy-settings and
   vanilla toggle interplay; load at night.
5. **Balance**: night shift length follows the working-hours slider; default Inkpaw hours fill the whole daytime,
   leaving 8 h of night (minus gaps).
6. **Art**: a new body that keeps the beaver UV layout, node names and animation set.
7. **Untested mechanisms**: `BlueprintModifiers` timing, `TransformSpec` on character models, custom `ComponentSpec`
   types from a mod DLL being found by `SpecTypeCache` (common in other mods, still verify), `StartingFactionSpec` on a
   second faction.
8. **Existing `EntityNameLocKey` bug** (section 2) until fixed.

---

## 14. Staged plan (study, superseded)

**Stage 0 — fixes and mechanism checks (no new gameplay).** Fix the Inkpaw `EntityNameLocKey`. In the dev harness:
check custom spec types load, a `BlueprintModifiers` entry changes `Need.Beaver.Hunger` for Inkpaws only, and the
Characters batch tab opens.

**Stage 1 — the smallest proof: "a Ringtail that works the night shift and survives a save".**
Contents:
* `RingtailAdult.Inkpaws` hidden template (Inkpaw mesh scaled down or the Inkpaw mesh with a red coat is fine),
  `WorkerType.PandabornRingtail` (`IgnoresWorkingHours: true`), `RingtailFactory`, the `TemplateNameMapper`
  registration, a coat setter.
* `PandabornShiftScheduler` + `PandabornCrews` on one faction workplace (e.g. the lumber mill copy) and the
  district's hauling post; flip at dusk/dawn; remembered crews.
* `RingtailRestRootBehavior` (day sleep at home).
* A dev-harness command that spawns N Ringtails (no loft yet).

Automated in-game test (extends `src/devharness`): start a new Inkpaws game (`PB_AutoTest` prefix), place a
den-type dwelling, a lodge for Ringtails, the mill and a hauling post; spawn 3 Ringtails; run 3 in-game days at
high speed, sampling every in-game hour:
* mill `WorkplaceWorkerType` is `Beaver` during Inkpaw hours and `PandabornRingtail` during the night shift;
* during the night shift, the mill's `AssignedWorkers` are Ringtails and at least one is running a job
  (`Worker.JobRunning`); during the day, Inkpaws;
* the same Ringtail is on the mill's night crew on consecutive nights (crew memory);
* every Ringtail spends ≥ 3 h per day in the `Sleeping` executor at home, and no Ringtail ever shows the
  Exhaustion status (`Sleep` need never ≤ 0);
* then save, reload, and check the Ringtails still exist (count and template name), still Ringtail-typed, and the
  next night shift staffs the mill again;
* no exceptions in `Player.log`; a Folktails game with the mod enabled shows no Ringtail templates instantiated.

Gate: if day sleep or the flip churn is not clean here, drop to rung 2 or 3 before investing in art.

**Stage 2 — arrival and breeding.** Loft building with arrival spec and nursery (litters), den nursery gated on
wellbeing, Ringtail kit template + growth hook, stat bonuses, appetite tweak, arrival message. Test: build a loft,
family arrives once; kits are born only in lofts and grow into Ringtail adults; cubs in dens only above the
wellbeing threshold.

**Stage 3 — interface.** Crew fragment with day/night/both, own population panel, badge and portraits,
Oxen-only-on-haulers rule, optional vanilla-toggle hiding.

**Stage 4 — art.** True Ringtail body (beaver UV layout), kit body, coats, outfits per worker type.

**Stage 5 — bets.** Long Nap; faction tutorial via `StartingFactionSpec` + `BlueprintModifiers`; nap attractions.

---

## 15. Fallback ladder (study, superseded)

| Rung | What the player gets | Code | Reflection | Harmony | Robustness across updates |
|---|---|---|---|---|---|
| 1. Shared workplaces, automatic crews (W3) | The design | Largest: factory, scheduler, crews, rest behaviour, nursery, UI (rough order: 2,000–3,000 lines C#) | `TemplateNameMapper`, `BehaviorManager` root list, optional `Need` fields | None required; optional `PopulationDataCollector` postfix | Medium. Depends on public work-system API, two private fields, and the vanilla behaviour order |
| 2. One people per workplace, simple toggle | Toggle Inkpaws/Ringtails (or day/night) per workplace, district default | Same factory and nursery; the scheduler shrinks to "open Ringtail workplaces at night, close by day" (otherwise Ringtails would work 24 h, since a per-kind clock needs Harmony). Saves crew memory and some UI (rough order: 1,200–2,000 lines) | Same as rung 1 | None | Medium. Night work still needs the rest behaviour; with **same hours for both peoples**, the rest behaviour and scheduler go away and only `TemplateNameMapper` remains |
| 3. One people, Ringtail coats as variety | Inkpaws with red coats in the pool | None (`FactionSpec.Textures`) | None | None | High |

Realistic and robust: **rung 1 is realistic** and needs no Harmony; its fragile parts are few and testable.
**Rung 2 without night work** (same hours for both peoples) is the most robust version that still has two peoples.
Rung 3 is the safe floor.

---

## 16. Design changes suggested by the code (study, superseded)

1. **Housing decides the kind of baby, not who lives there.** The game has no hook to restrict dwellers by kind;
   any adult can sleep in any home. Keep "dens raise Inkpaws, lofts raise Ringtails", drop "Inkpaws live in dens".
2. **Identical wellbeing tier tables for both peoples.** Per-kind tables need compensating code and the wellbeing
   panel would show wrong numbers. Express differences as constant stats.
3. **The night shift is the complement of the working-hours slider.** One lever, already in the game: shorter Inkpaw
   hours mean a longer Ringtail shift and real shared dusk hours. Default hours give Ringtails about 8 h minus gaps.
4. **Night crews staff only as many workplaces as there are Ringtails**, by workplace priority. This is the rule the
   panel should show; "every workplace gains a night crew" is true only with enough Ringtails.
5. **Oxen are an explicit crew setting on hauling posts**, not a third worker kind everywhere.
6. **No mixed start** (already decided) — it keeps the vanilla start path untouched.
7. **Population panel is ours.** Vanilla numbers will look odd overnight unless a Harmony postfix is accepted.
8. **"Lantern-lit paths give Ringtails full speed at night"** has nothing to undo: vanilla has no night speed
   penalty. Make lanterns a wellbeing/decoration effect instead.

---

# Part C: results (current)

## 17. Prototype results

Status: go/no-go prototype built and run in game, 2026-11-14 (game 1.1.2.8). Code and data: `proto/ringtails`
(dev-only mod `JigglyPanda.PandabornProtoRingtails`, see its README). Design target: the "Candidate changes" version
of Pillar 1 — Ringtails staff **their own** buildings and sleep through the morning; no shift flipping.

### 17.1 Verdict: GO, for the simplified design

**Go.** A second living colonist kind with its own worker type, its own buildings, its own hours, faster walk and
lighter appetite works in Timberborn 1.1.2.8 **without Harmony**, with two private-field touches that fail safe, and
survives save and reload. In three in-game days plus a reload:

* Ringtails took only Ringtail jobs and Inkpaws never took them (0 violations in every hourly sample).
* Ringtails were at work in the afternoon and all night, went home at dawn, slept ~2.5–3 h in their loft, ate, drank
  and idled until 8 h after dawn, then went back to work — the same cycle every day, before and after the reload.
* No Ringtail ever had a critical need; no exhaustion.
* Inkpaws kept the vanilla day: work through the day, sleep before dawn.
* Every colonist came back from the save with the same kind, template, job and home.
* No exceptions from our code; every batch-control tab and every panel opened with Ringtails present.
* A Folktails game with the prototype enabled is unchanged (same templates, no Ringtails, no errors).

Conditions that come with the go: the vanilla population numbers do not count Ringtail crews (our own panel is
required, 17.5); kind-specific housing is a correction rule, not a restriction (17.4); and the two private fields
must be checked at load with a safe fallback (17.6).

One design caveat came out of the measurements (17.3): **a night crew of haulers only has work if the day leaves
goods behind** — with the vanilla 16-hour day, Inkpaw builders supply construction themselves before the bell, so the
Courier Loft idled in every run without day-time producers. That is a content question (shelves, flags, a Ringtail
builder hub), not a technical one.

### 17.2 What was built

Everything follows the hook points of sections 3–8; no Harmony anywhere.

| Piece | How | Lines (runtime C#) |
|---|---|---|
| Hidden Ringtail adult and kit templates | `Characters/Pandaborn/RingtailAdult|RingtailChild.Inkpaws`, generated from the vanilla beaver by `proto/ringtails/tools/derive.py`, in **no** template collection. Inkpaw body (`InkpawAdult.Model`), red panda coats, body scaled to 0.82 with `TransformSpec` on `Model_Preserved`, normal lifting (14), vanilla label keys. Gate runs used walking ×1.3 (3.51); after the gate: Inkpaw speed 2.7 with no slowdown when carrying | data |
| Worker type `PandabornRingtail` | `WorkerTypeSpec`, `IgnoresWorkingHours: true` | data |
| Ringtail-only workplaces | Copies of the Folktails Hauling Post (Courier Loft) and Gatherer Flag (Forager's Nest): `DefaultWorkerType: PandabornRingtail`, `DisallowOtherWorkerTypes: true`, no unlock costs. Collection `Buildings.PandabornRingtails` appended to the Inkpaws faction by a `FactionSpec` merge (`TemplateCollectionIds#append`), so Folktails and Iron Teeth never see them | data |
| Loft | A Lodge copy without `ProcreationHouseSpec`, marked `PandabornLoftSpec` | data |
| Outfits | `WorkerOutfitSpec` Hauler/Gatherer for the Ringtail worker type | data |
| Feature switch, factory, save registration | `RingtailService`: active only in an Inkpaws game; creates Ringtails with public API (mirrors `BeaverFactory`); registers both templates in `TemplateNameMapper` (private field, see 17.6) and verifies the read-back | 160 |
| Save fallback alias | The Inkpaw templates list `RingtailAdult|RingtailChild.Inkpaws` in `BackwardCompatibleTemplateNames` (merge file) | data |
| Day rest | `RingtailRestRootBehavior`, inserted just above `WorkerRootBehavior` (private list, see 17.6). In the rest window (gate runs: 0–8 h after dawn; now: dawn to the bell, 4–16 h) it keeps the Ringtail off work and runs the game's own `SleepNeedBehavior` while Sleep < 0.55, then the game's `NeederRootBehavior`, then `WanderRootBehavior` | 130 |
| Coat | `RingtailCoat` replaces the faction coat in `PostInitializeEntity` | 40 |
| Kit growth | `RingtailGrowth`: at growth 0.995 the kit becomes a Ringtail adult through our factory (vanilla would make an Inkpaw at 1.0) | 50 |
| Light appetite (gate runs only; removed after the gate) | `RingtailAppetite`: skipped a quarter of the Hunger/Thirst decay ticks (see 17.6) | — |
| Housing rule | `LoftHousingRule`: see 17.4 | 110 |
| Test probe | `src/Dev/*`: spawns Ringtails, places buildings on the district terrace and lays paths, stocks the district center, logs every colonist and workplace each in-game hour, opens panels and takes screenshots. Talks to the harness by reflection; inert without a test request | dev only |

Total runtime code ≈ 640 lines including comments. Harness changes: none were needed (the probe lives in the prototype
mod, so the shared harness files that two other agents are editing were not touched). `-ExtraMods`, the game queue and
`-SaveAndReload` came from the other agents' script work.

### 17.3 Measured in game

Runs (output in `E:\PandabornDev\build\test\<run>`; analysis `proto/ringtails/test/analyze.py` →
`ringtails_report.json`): new Inkpaws game on Diorama (9 Inkpaw adults, 4 cubs), the probe adds 4 Ringtail adults and
1 kit, places a Courier Loft, a Forager's Nest, an Inkpaw lumberjack and gatherer, 2 lofts, 4 lodges and 3 unfinished
lodges on the district terrace and connects them with paths, stocks 400 water and 40 logs, then 72 in-game hours at
speed 3, hourly samples of every colonist and workplace, panels and screenshots, batch-control tabs, save, relaunch
into the save and 200 more real seconds (≈ 31 in-game hours).

| Run | What it covered | Harness verdict |
|---|---|---|
| `rt-gate3` | 4 Ringtails at the Courier Loft, housed in lofts; no water stocked (Inkpaws went thirsty; test-map artefact, since fixed); first appetite version (wrong, see below) | PASS, both launches; reload did not advance time (a loading-issue dialog from a probe path bug paused it) |
| `rt-gate4` | 1 Ringtail at the Forager's Nest (the Courier Loft could not be connected on that layout), Inkpaw lumberjack + gatherer + builders, water stocked, fixed appetite; reload ran 31 h | PASS, both launches, 0 errors from our code |
| `rt-gate6` | **The decided design**: rest window ends at the bell (default day: 16 h), equal appetite, Inkpaw walking speed with no load slowdown; the main mod's own Inkpaws buildings (dens, village hall, Inkpaw lumberjack and gatherer), 5 Ringtails at the Courier Loft; 72 h + reload 31 h | PASS, both launches; 18/18 colonists back; 0 violations; 0 critical needs; 0 errors from our code |
| `rt-fallback1` | Save with 3 Ringtails reloaded with the save registration switched off (17.7) | Ringtails loaded as Inkpaws; only our deliberate error logged |
| `rt-folktails1` | Folktails game with the prototype enabled and asked to spawn Ringtails | No Ringtail created, template set identical to earlier Folktails runs (332 placeable / 368 templates), 0 errors; the Ringtail building is "not available to this faction" |

**The daily cycle of an employed Ringtail** (identical every day; `rt-gate4`, day 3, Kaduvom at the Forager's Nest;
hours after dawn; `rt-gate3` shows the same pattern for all 4 couriers):

| Hours | Doing | Where | Sleep need |
|---|---|---|---|
| 0–1 | finishes the current job, walks home | workplace → loft | 0.27 (lowest of the day) |
| 1–3 | **sleeps** (vanilla `SleepNeedBehavior`, home sleep effects) | loft | 0.41 → 0.79 |
| 4–5 | eats and drinks at the district center (hunger 0.44 → 0.99, thirst 0.31 → 0.93) | district center | 0.78 |
| 5–8 | leisure / wanders | outdoors | 0.75 → 0.68 |
| 8/9–24 | **at work** (afternoon with the Inkpaws, then the whole night alone) | workplace | 0.65 → 0.30 |

* Per Ringtail per day: **16 h at work, 2.5–3 h asleep at home, ~5 h needs and leisure**; never at work inside the
  rest window except to finish a job already running at dawn.
* Inkpaws, same days: at work through the day, home or wandering in the evening, asleep about 21 h → dawn (vanilla).
  So the three acts happen as designed: morning = Inkpaws working while Ringtails sleep/eat, afternoon = both at work,
  night = Ringtails only.
* **Needs:** no Ringtail ever had a critical need in any run (lowest Sleep 0.27, never below 0; lowest Hunger 0.43,
  Thirst 0.31 in `rt-gate4`). With the appetite fix the Ringtails' Hunger fell 0.025/h against the Inkpaws' 0.033/h:
  0.75× as designed. Inkpaws did run short of food late in `rt-gate4`'s reload (Hunger critical in 11 Inkpaw samples:
  the test colony lives on its starting berries and one gatherer); that is the test economy, not the Ringtails, which
  eat the same stock more slowly. (The first appetite version gave points back every tick, which — because any applied effect
  suppresses that tick's decay — stopped hunger entirely; found in `rt-gate3`, fixed.)
* **Job exclusivity: 0 violations** in 72 + 31 hourly samples of every colonist and workplace, in every run: Ringtail
  workplaces only ever held Ringtails, Inkpaws never took them, Ringtails never took an Inkpaw job (vanilla
  `DistrictWorkplaceAssigner` keys workplaces and workers by worker type).
* **Throughput — the important finding: night couriers only have work if the day leaves work behind.** Ringtails
  hauled and gathered whenever there was something to move: the Forager's Nest Ringtail gathered 6 loads (18 berries)
  in `rt-gate4` (until the bushes in range ran out, "Nothing to do in range"). But the Courier Loft crews made **zero**
  hauls in `rt-gate3`, `rt-gate6` and `rt-throughput1`: in `rt-throughput1`, 6 dens queued at dawn (72 logs) were
  supplied entirely by the Inkpaw builders before the bell (24 trips, 72 logs, all by day), and at night there was
  nothing left. In Timberborn, haulers serve haul candidates (builder hubs, flags, farms, stockpiles, workshops'
  inventories); builders, not haulers, carry materials to construction sites, and the builders are Inkpaws.
  So the Courier Loft's night work comes from what the Inkpaws leave in flags, farms and workshops at the bell, and
  from builder-hub restocking. A run to measure exactly that (`rt-throughput2`: Inkpaw lumberjacks and gatherer
  filling their flags by day, 5 Ringtail couriers emptying them at night, construction queued after the bell) was
  queued but had not got the game by the time of writing (the shared test queue was saturated); analyse it with
  `python proto/ringtails/test/analyze.py E:/PandabornDev/build/test/rt-throughput2` (`pickupsByKindWorkplacePhase`).
  Design consequence: the "Inkpaw workshops get roomier output and input shelves" change is not optional, and the
  Courier Loft should be pitched as "clears the flags and restocks the workshops overnight", not as construction
  delivery (unless a Ringtail builder hub is added, which is data: a Ringtail-typed builders' workplace).
* **With the rest ending at the bell** (`rt-gate6`, default 16-hour Inkpaw day, so the window is 0–16 h): Ringtails
  worked 105 of 120 night samples (the rest: walking to work in the first night hour), were never at work in the
  afternoon, and slept once a day; the first version slept only when Sleep fell below 0.55, which drifted the sleep
  to mid-window on short nights (a Ringtail coming off an 8-hour night still has Sleep ≈ 0.6). Fixed after the run:
  a Ringtail now goes to bed first thing in the window unless nearly rested (≥ 0.75), so the sleep sits at dawn again.
  Lowest Ringtail needs with equal appetite: Sleep 0.40, Hunger 0.38, Thirst 0.43; none critical, before or after the
  reload.
* **Speed (gate runs):** Ringtail base walking speed 3.51 vs Inkpaw 2.70 (×1.30); lifting 14 for both. Since changed
  to equal speed with no load slowdown (17.8).
* **Kits:** the kit grew into a Ringtail adult (`RingtailAdult.Inkpaws`, "… grew up" notification) in every run;
  Inkpaw cubs kept growing into Inkpaws.
* **Save and reload:** all colonists came back with the same kind, template, workplace and home (`rt-gate3`: 18 of
  18; `rt-gate4`: 20 of 20; compared colonist by colonist), and after the reload the Ringtail kept the same cycle
  (asleep at home at dawn, at work afternoon and night) for the 31 hours observed, with no exceptions.
* **Population numbers shown to the player** (vanilla `PopulationDataCollector`, every hour): "adults" = Inkpaws +
  Ringtails (14–16), bed counts correct (18 beds, 0 homeless once the rule ran), but workforce, employed and
  unemployed count only `Beaver`-type workers: with 5 Ringtails at work the panel showed "employed 2–4, unemployed
  5–9" — the Ringtail crews are invisible to the vanilla numbers (see 17.5).
* **Errors:** none from our code in any gate run (only the game's 31 known `Assertion failed` lines at scene load).
  Every batch-control tab, including Population, opened with Ringtails present.
* Night screenshots: `rt-gate3\rt_d0_h21_night_ringtail.png` (Ringtail panel: "Lives in: Loft / Works at: Courier
  Loft"), `rt-gate3\rt_d0_h18_night_courierLoft.png`, `rt-gate4\rt_d1_h19_night_foragersNest.png`,
  `rt-gate3\rt_d1_h2_morning_loft.png` (three Ringtails in a loft at 03:13), plus `*_night_overview.png`.

### 17.4 Housing: what happens when both kinds compete for beds

* **Vanilla, no rule** (run `rt-smoke4`: 12 beds for 13 Inkpaws + 5 Ringtails): `DwellerHomeAssigner` hands each free
  bed to the first adult in `DistrictPopulation.Adults` that is looking for a home, and the list is in registration
  order. Inkpaws were there first, so they took **all** beds including both lofts, and all 5 Ringtails slept outside.
  Kind plays no part. Nothing breaks: a homeless Ringtail sleeps outside (vanilla `SleepOutsideEffects`) at the start of
  its rest window.
* **Bed timing never conflicts.** A dwelling slot belongs to one dweller round the clock; the two kinds sleeping at
  different hours does not create or free beds.
* **The rule we kept** (`LoftHousingRule`, public API only, every 10 ticks): (1) a Ringtail in a non-loft home and an
  Inkpaw in a loft swap homes; (2) a homeless Ringtail takes a free loft bed, or else a loft bed held by an Inkpaw,
  who moves to a free non-loft bed or, if there is none, becomes homeless (loft beds belong to Ringtails). Swaps never
  change how many dwellers a home has, so vanilla's own "move to an emptier home" logic has nothing to undo; no
  oscillation was seen in three days. In `rt-gate3` all 4 Ringtails (and later the grown kit) were moved into the two
  lofts within the first hour and stayed there; Inkpaws filled the lodges; 18 beds, 0 homeless.
* Not possible without Harmony: stopping vanilla from putting an Inkpaw into a loft in the first place
  (`AutoAssignableDwelling.CanAssignDweller` has no hook). The rule only corrects afterwards, which the player sees
  as a short move.

### 17.5 Interface: what was opened and what a release needs

Opened in game with Ringtails present, no exceptions: every batch-control tab including the Population
(`CharacterBatchControlTab`) tab, the Ringtail character panel, the Courier Loft and Forager's Nest workplace panels,
the Loft dwelling panel, an Inkpaw panel and workplace panel, and the district center panel (screenshots `rt_*.png` in
the run folders). The Ringtail panel correctly says "Lives in: Loft / Works at: Courier Loft".

What the player sees today and what a release needs:

| Element | Prototype | Release work |
|---|---|---|
| Character panel portrait and subtitle | Inkpaw (giant panda) avatar for Ringtails | Own `IEntityBadge` with priority above `BeaverEntityBadge` (10): Ringtail avatar, contaminated avatar, "Ringtail, age N" |
| Population tab (batch control) | Ringtails listed among "Beavers" adults; works | Add kind column or icon (our own fragment), or accept |
| Top bar population numbers | "Adults" = Inkpaws + Ringtails; workforce, employed and unemployed count **Inkpaws only** (`PopulationDataCollector` reads the `Beaver` and `Bot` worker types only), so Ringtail jobs are invisible | Our own population panel/tooltip with a second row for Ringtails (crews per kind, idle per kind). A vanilla-number fix would be a Harmony postfix; not needed |
| Workplace panel | Ringtail workplaces show their workers; empty slots drawn with the faction (Inkpaw) silhouette; the beaver/bot toggle stays hidden (only after bots exist, and `DisallowOtherWorkerTypes` disables it) | Own empty-slot art (cosmetic); a "Ringtails only" line comes from `WorkerOnlyTextLocKey` |
| District center default worker type toggle | Beaver/Bot only; Ringtails need no default (their buildings are typed) | None |
| Automation population counter | Totals include Ringtails, worker modes Beaver/Bot only | Accept or own counter |
| Statistics graphs | Ringtails inside adult counts | Accept |
| Loft/Courier Loft/Forager's Nest | Vanilla models and icons | Art |

### 17.6 Private-field and implicit dependencies, and how to fail safely

| # | Dependency | Used for | Kind | Break risk on a game update | What happens if it breaks (prototype) | Proposed safe failure (release) |
|---|---|---|---|---|---|---|
| 1 | `TemplateNameMapper._templates` (private `Dictionary<string, TemplateSpec>`), written once at load | Loading saves that contain Ringtails | Reflection, 1 field | Low–medium. A rename or a switch to an immutable/frozen dictionary (the game already uses `FrozenDictionary` in `SpecTypeCache`) breaks it | Detected at load (field missing, wrong type, or read-back check fails): `RingtailService` logs one error and switches the feature off. Saved Ringtails load **as Inkpaws** through the alias merged into the Inkpaw templates (`BackwardCompatibleTemplateNames`), keeping name, age, needs, job and home; no new Ringtails are made; kits grow into Inkpaws | Same, plus a one-time in-game message. Ship the alias in the main mod permanently |
| 2 | `BehaviorManager._rootBehaviors` (private `List<RootBehavior>`), one insert per Ringtail at initialisation | The day rest | Reflection, 1 field | Low–medium. Same field has existed through 1.0–1.1 | Detected per entity: one error logged, Ringtails then behave as round-the-clock workers whose only rest is critical sleep (vanilla `CriticalNeederRootBehavior`). They survive but are exhausted part of the time | Check the field once at load (on a throwaway list type check, before any Ringtail exists). If it is gone: keep the feature but fall back to a public-API rest — pause the Ringtail workplaces (`PausableBuilding`) during the rest window, so Ringtails are unemployed and the vanilla needer/sleep logic runs — and log one warning. Never crash |
| 3 | Behaviour order from `BeaverBehaviorInitializer` (Worker root before Needer root) | Where the rest root is inserted (just above `WorkerRootBehavior`) | Implicit (public types, internal order) | Low | If `WorkerRootBehavior` disappears the insert falls back to "above `NeederRootBehavior`", else reports error #2 | Same |
| 4 | Vanilla growth at `GrowthProgress >= 1.0` inside `ChildRootBehavior` | Kits grow into Ringtails (we act at 0.995) | Implicit | Low. If vanilla started growing earlier, a kit would become an **Inkpaw** (safe, no crash) | Kit becomes an Inkpaw | Acceptable; or check the produced adult in `CharacterCreatedEvent` |
| 4b (removed) | Vanilla `Need.Update` skips a tick's decay when an effect was applied since the last update | Light appetite (we apply a negligible effect on a quarter of the ticks) | Implicit | Low | Ringtails eat and drink like Inkpaws (safe) | Same; or the per-entity `Need._deltaPointsPerUpdate` (private) if exact control is wanted |
| 5 | `BeaverTextureSetter` sets the coat in `InitializeEntity` | Our coat replaces it in `PostInitializeEntity` | Implicit | Low | Ringtails wear Inkpaw coats (cosmetic) | Same |
| 6 | `WorkplaceSpec.DisallowOtherWorkerTypes` + `DefaultWorkerType` | Ringtail-only workplaces | Public data | Very low | — | — |
| 7 | `WorkerTypeSpec.IgnoresWorkingHours` | Ringtails work afternoon and night regardless of the Inkpaw working-hours slider | Public data | Very low | — | — |
| dev | `Child.GrowthProgress` private setter; the harness's `Harness` class | Test probe only (push a kit near adulthood; find the request) | Reflection, dev only | n/a | n/a | not shipped |

No Harmony patch was needed for anything in the target design.

Every dependency is checked where it is used, fails at one known line, and logs a single `[Pandaborn.Ringtails]` error
instead of throwing. For a release the checks should run once at load in one place (a `RingtailCompatibility`
singleton) that decides which features are on, shows one in-game message when something is off, and is covered by the
automated save/reload test after each game update.

### 17.7 A save with Ringtails when the feature is removed

* **Prototype mod removed** (templates gone): `WorldEntitiesLoader` cannot map `RingtailAdult.Inkpaws`, records the
  loading issue "Object had unknown type and was deleted" (shown to the player in the loading-issues panel) and drops
  the Ringtails; the Ringtail buildings go the same way. References to them from other entities are owned by the
  dropped side (a worker stores its workplace, a dweller its home), so nothing dangles. The colony loses those
  colonists and buildings. Read from code; not run, because the test script can only reload with the same mod set.
* **Templates present but registration broken** (simulated game update, run `rt-fallback1`): the feature switches
  itself off with one logged error; the 3 Ringtails loaded **as Inkpaws** with their names, ages, needs and homes
  (through the `BackwardCompatibleTemplateNames` alias), lost their Ringtail jobs (vanilla drops a worker whose type no
  longer matches the workplace on load), and the game ran on. No crash, no corruption.
* **Recommendation:** ship the alias in the main mod's Inkpaw templates permanently, and keep the Ringtail templates
  in the main mod even if the feature is ever turned off by a setting. Then a save never loses colonists: worst case,
  Ringtails become Inkpaws.
* (That fallback run also lost some Lodges on reload; the cause was the test probe's early path layer placing paths
  over lower ground, which the game deletes on load. Fixed in the probe; unrelated to Ringtails.)

### 17.8 Design recommendations

* **Hours window: the rest is "sleep ~3 h, then leisure", whatever its length.**
  The game's sleep logic does not want an 8-hour sleep: a Ringtail coming off a 16-hour shift has Sleep ≈ 0.3, the
  home restores 0.2/h, and the vanilla `Sleeper` wakes it when full, so it sleeps about 2.5–3 h (dawn to ~3 h) and
  then eats, drinks and takes leisure (or wanders) until 8 h, when it goes back to work. That is the natural shape of
  the game's own logic (vanilla Inkpaws sleep ~3 h before dawn, from ~21 h, for the same reason), and it gives the
  design a nice beat: **Ringtails have the morning to themselves at the teahouse while the Inkpaws work.** Forcing an
  8-hour sleep is possible (launch the sleep executor to the window's end) but costs the Ringtails their only leisure
  time and makes them look idle in bed. The gate runs used a fixed 0–8 h window; its end is now the bell (next point).
* **Decided after the gate (coordinator, 2026-11-14): the window ends at the bell.** The rest window now runs from
  dawn to the end of the Inkpaw working hours (`WorkingHoursManager.EndHours`, read live, so moving the slider takes
  effect at once), clamped to 4–16 h after dawn: never so early that a Ringtail cannot sleep, never later than
  nightfall, so Ringtails always hold the night. The handover at the bell is the faction's pitch; at the default
  16-hour day it means no afternoon overlap (morning and afternoon Inkpaws, night Ringtails), and a shorter day opens
  a shared stretch. This overrules the "do not tie" advice of the first draft of this section. Implemented in the
  prototype (`RestEndsAtBell`, `RestMinEndHours`, `RestMaxEndHours` on `PandabornRingtailSpec`) and in the module.
* **Housing rule: "lofts are for Ringtails, anyone may sleep anywhere else".** Use the swap rule of 17.4. Do not try to
  keep Ringtails out of dens (needs Harmony; also cruel to a homeless Ringtail). In the UI, call a loft a Ringtail home
  and show a small "Inkpaw in a loft" warning only if the rule cannot fix it (no free beds).
* **How the player should see the two crews:** a sun or moon icon on every workplace (from its worker type), a second
  row in the population panel ("Ringtails: 5 · working 5 · idle 0"), the Ringtail badge with a moon, and the Courier
  Loft/Forager's Nest grouped in their own tool group. Because Ringtail workplaces are separate buildings, there is no
  crew switching to explain: "these buildings are staffed by Ringtails, at night" is the whole rule.
* **Stats (decided after the gate):** equal appetite (the light-appetite component was removed: one set of food numbers,
  and it leaned on an unwritten rule of `Need.Update`); unladen walking speed equal to the Inkpaws'; lifting 14; and
  **carrying never slows them**, which is pure data: `WalkerSpeedManager` uses `BaseSlowedSpeed` whenever the colonist
  carries anything (`GoodCarrier.IsMovementSlowed`), so the Ringtail template sets `BaseSlowedSpeed = BaseWalkingSpeed`
  (2.7). Overloading beyond the lifting capacity still slows them through vanilla `Overburdenable` (a bonus), which is
  fine. No Harmony, no code.
* **Kits:** kits grow into Ringtails with our hook; births belong in a loft nursery (stage 2 of section 14), still
  needed for the "born in lofts" part of the design.

### 17.9 Remaining work to production quality (estimate)

| Work | Size |
|---|---|
| Move the code into the main mod's runtime project behind a `RingtailCompatibility` check (17.6) and a mod setting; ship the alias | 1 day |
| Loft nursery (litters), Ringtail arrival with the first loft, arrival message | 2–3 days |
| Badge, avatars, population-panel row, workplace sun/moon icon, Ringtail tool group | 3–4 days |
| Real Ringtail body (beaver UV layout, node names, 61/39 animations), kit body, coats, outfits | art milestone, 1–2 weeks |
| Own buildings beyond the two copies (courier loft, forager's nest, dew nets, star tower, lantern workshop) | per building, data + art |
| Balance pass (rest window, appetite, speed, loft size) and the "Inkpaw workshops get roomier input shelves" change | 2 days |
| Automated regression: the gate test of this section in CI-like form, plus a "feature removed" reload test (needs a script option to reload with a different mod set) | 1 day |

Code: roughly 1,000–1,500 lines on top of the prototype's 640, all without Harmony. Started: `src/code/Pandaborn.Ringtails`
(the prototype's runtime code ported as a feature module with the load-time compatibility check; not wired until its
spec records, proposed in `proposed/RingtailSpecs.cs`, are added to `Pandaborn.Specs`).


---

## 18. Phase 2: the shipping module

Status: 2026-11-14. The Ringtails are a feature module of the faction's runtime code (`src/code/Pandaborn.Ringtails`,
`src/code/Pandaborn.RingtailsFallback`, specs in `src/code/Pandaborn.Specs/RingtailSpecs.cs`), wired into
`Pandaborn.Code.sln` and `modules.txt`. The data below was carried by the dev mod `proto/ringtails` during phase 2;
the catalogue lane has since adopted it (§19), and that copy is retired.

### 18.1 For the catalogue lane

Everything the main mod's data needs. Ids follow the lock rules; the four spec classes are already in `Pandaborn.Specs`.

| What | Path / id | Content |
|---|---|---|
| Ringtail adult template | `Characters/Pandaborn/RingtailAdult.Inkpaws.blueprint.json`, template `RingtailAdult.Inkpaws` | The vanilla beaver adult (as the Inkpaw adult is made), **in no template collection**. `Children.Model_Preserved.TimbermeshSpec.Model = Characters/Pandaborn/RingtailAdult.Model` (ringtail-body lane; add the mesh to the build's `$meshes` table), **no `TransformSpec`** (size is baked in). `WorkerSpec.WorkerType = PandabornRingtail`. `GoodCarrierSpec.BaseLiftingCapacity = 14`. `WalkerSpeedManagerSpec.BaseSlowedSpeed = BaseWalkingSpeed` (no slowing when loaded). `MovementAnimatorSpec.AnimationSpeedScale = 1.25`. Keep `SimpleLabeledEntitySpec.EntityNameLocKey = Beaver.Adult.TemplateName`. No `PandabornBellSpec` (the rested bonus is an Inkpaw thing). `PandabornNamePoolSpec { NamePoolLocKey: Pandaborn.Ringtail.NamePool }` (names.json). `PandabornRingtailSpec { Textures: Materials/Pandaborn/Ringtails/Adult/RingtailAdultCoat1..5, Avatar: Sprites/Pandaborn/Avatars/RingtailAdult, ContaminatedAvatar: Sprites/Pandaborn/Avatars/RingtailContaminatedAdult, RestStartHours: 0, RestEndsAtBell: true, RestMinEndHours: 4, RestMaxEndHours: 16, SleepBelow: 0.55 }` |
| Ringtail kit template | `Characters/Pandaborn/RingtailChild.Inkpaws.blueprint.json`, template `RingtailChild.Inkpaws` | The vanilla beaver child, same rules: model `Characters/Pandaborn/RingtailChild.Model`, no `TransformSpec`, `BaseSlowedSpeed = BaseWalkingSpeed`, label `Beaver.Child.TemplateName`, name pool, `PandabornRingtailSpec` with the `RingtailChildCoat1..3` coats and the `RingtailChild` / `RingtailContaminatedChild` avatars |
| Inkpaw adult (merge) | `InkpawAdult.Inkpaws` | `PandabornRingtailsSpec { AdultBlueprint: Characters/Pandaborn/RingtailAdult.Inkpaws.blueprint, ChildBlueprint: Characters/Pandaborn/RingtailChild.Inkpaws.blueprint, WorkerType: PandabornRingtail, ArrivalAdults: 2, ArrivalKits: 1 }`; `TemplateSpec.BackwardCompatibleTemplateNames += RingtailAdult.Inkpaws` — **permanent**: it is what lets a save keep its Ringtails (as Inkpaws) whenever the module is off |
| Inkpaw child (merge) | `InkpawChild.Inkpaws` | `BackwardCompatibleTemplateNames += RingtailChild.Inkpaws` — permanent |
| Worker type | `WorkerTypes/Pandaborn/WorkerType.PandabornRingtail.blueprint.json`, id `PandabornRingtail` (global) | `IgnoresWorkingHours: true`, `DisplayNameLocKey: Pandaborn.Ringtails.PluralDisplayName`, `WorkerOnlyTextLocKey: Pandaborn.Ringtails.WorkerOnly`. **Must stay in data forever**: saves store a workplace's worker type, and the game throws loading a save that names an unknown one |
| Outfits | `WorkerOutfits/Pandaborn/WorkerOutfit.{Builder,Hauler,Gatherer}.PandabornRingtail.Inkpaws` | Copies of the Inkpaws `Beaver` outfits with `WorkerType: PandabornRingtail` |
| Night posts | `PandabornNightBuildersPost`, `PandabornNightCourierPost`, `PandabornNightForagersPost` (`.Inkpaws`) | Add `PandabornNightPostSpec {}`. **Keep** `WorkplaceSpec.DefaultWorkerType: Beaver` and `DisallowOtherWorkerTypes: false`: the module switches them to Ringtails; without it they are Inkpaw workplaces. Give each a science cost above 0 (the Builders' Post has 0 today): the Ringtails' arrival unlocks them for free, so a player without a Moon Loft does not see them as free buildings. Consider dropping the `Bot` unlock cost (the module switches a post back to Ringtails anyway) |
| Moon Loft | `PandabornMoonLoft.Inkpaws` | Add `PandabornMoonLoftSpec { KitsPerDay: 1 }`; **remove `ProcreationHouseSpec`** (it would make Inkpaw cubs from Ringtail parents; the loft's kits come from the module) |
| Loc (data) | `Pandaborn.Ringtails.PluralDisplayName` ("Ringtails"), `Pandaborn.Ringtails.WorkerOnly` (keyword line) | Used by the worker type even when the module is off; the module's own texts ship with it (`enUS_PandabornRingtails.csv`) |
| Collections | none new | The posts and the loft are already in `Buildings.Inkpaws`; the Ringtail templates must stay out of every collection |

### 18.2 Data alone (module off or failing its checks)

| Thing | Module on | Module off (API check failed or forced off) | Module degraded (private member gone) |
|---|---|---|---|
| Ringtails in a save | Ringtails | Load as Inkpaws (alias), keep name, age, needs, home | Same as off |
| Night posts | Ringtail workplaces, night shift | Ordinary Inkpaw workplaces: `Pandaborn.RingtailsFallback` switches any post a save left on the Ringtail type back to `Beaver` (public `SetWorkerType`) | Same (the fallback also acts when Ringtails reports itself degraded) |
| Moon Loft | Ringtail home, arrival, kits | Ordinary home without births | Same |
| New Ringtails | Arrival and kits | Never | Never |
| Notice | — | Core's "switched off" notice | Core's "falls back to the plain game" notice |


### 18.3 Night couriers and shelf size (measured)

Three 2-day runs of the same village (`proto/ringtails/test/workshops*.request.json`, analysis
`proto/ringtails/test/shelves.py`): 2 Paper Mills and 2 Pickle Yards, each with one Inkpaw worker, a plank pile and a
cabbage warehouse stocked at the start, output warehouses for paper (and pickles where it fitted), and — in A and B — a
Moon Loft (the family arrives at once) and a Night Courier Post. "Shelf" = a recipe's `CyclesCapacity`, which sizes both
the input and the output store of the workshop (`RecipeSpec.GetCapacity = Amount x CyclesCapacity`).

| Run | Shelves | Ringtails | Goods moved by the couriers at night (2 nights) | Inkpaw workshop workers by day: carrying / producing / idle at work |
|---|---|---|---|---|
| `rt2-shelvesA` | as generated (Paper 10 cycles, Pickles 20: about one day) | yes | **24** | 5 % / 47 % / 44 % (producing 38.8 h) |
| `rt2-shelvesB` | three working days (Paper 33, Pickles 48) | yes | **107** | 8.5 % / 48 % / 37 % (producing 56.5 h) |
| `rt2-shelvesC` | three working days | no | — | 12 % / 41 % / 41 % (producing 48.0 h) |

What it shows:

* **Shelf size is what makes night work.** With day-sized shelves the couriers found little to move (24 goods in two
  nights); with three-day shelves they moved 4.5 times as much, and the workshops produced 46 % more hours (56.5 vs
  38.8), because the input stores were full at dawn and the output stores had been cleared.
* **Without Ringtails the bigger shelves are harmless:** the Inkpaws fetch and clear for themselves as in vanilla
  (C: 12 % of their workshop day carrying, still producing 48 h). Compared with B, the couriers took about a third of
  the Inkpaws' carrying off them (12 % → 8.5 %).
* Caveats: one small layout per run (the tight Diorama terrace fitted the pickle warehouse only in C), 2 days, one
  worker per workshop. The direction is clear; the exact percentages are not.

**The capacity rule for the catalogue:** every Inkpaw workshop recipe gets
`CyclesCapacity = ceil(48 h x MaxWorkers / CycleDurationInHours)` (inputs and outputs for three full 16-hour working
days at full staffing), and the same factor on `FuelCapacity`. Measured examples: Paper 10 → 33, Pickles 20 → 48,
Paper Lantern 10 → 33, Steamed Rice 30 → 48 (one worker each). Flags and farms (outputs only) are the same idea:
their output store should hold a day's harvest, so the night couriers clear it.

### 18.4 What a player sees, from the first Moon Loft to a two-people village

1. **Before:** an Inkpaws colony. The night posts are locked behind a science cost like other buildings; nothing
   mentions Ringtails. A player who never builds a Moon Loft never sees one (verified: `rt2-shelvesC` and
   `rt2-folktails`; no Ringtail is ever created without the arrival).
2. **The first Moon Loft is finished:** two Ringtail adults and a kit appear at its door and move in. One message:
   "A Ringtail family has moved into the Moon Loft: Azra, Alzim, Aketa. Ringtails work from the afternoon bell to dawn.
   The night posts are now available." The three night posts unlock for free. A second population row appears under
   the vanilla one (in `rt2-module1`, where posts already stood: "Ringtails: 3   Working: 2   Idle: 0").
3. **The player builds night posts.** Each is a Ringtail workplace at once (the panel lists Ringtail workers with
   red-panda portraits and says "Night post: Ringtails work here from the afternoon bell to dawn."). By day the post
   shows the status "Closed for the day. Ringtails start at the afternoon bell." instead of an alarm; the vanilla
   "unstaffed" alert appears only if no Ringtail works there at all.
4. **The bell rings:** Inkpaws walk home, Ringtails walk to work (shift starts at the bell: 16 h after dawn by
   default; with the Bell on, the day the Bell locked at dawn). They work until dawn, go to bed in their lofts for
   about three hours, eat, drink and take leisure (the teahouse beat), and go back at the bell.
5. **Kits:** each dawn a Moon Loft with a Ringtail living in it and room for a kit raises one kit while the district
   has open night jobs (posts' worker slots minus Ringtails and kits already growing), and nobody is starving. The
   loft's panel says which: "Kits: one is raised each morning while night jobs are open." / "Kits: waiting for open
   night jobs." / "Kits: no room for a kit." / "Kits: none while anyone in the district is hungry or thirsty." A birth
   posts "Name was born in a Moon Loft!". Kits grow into Ringtail adults and take the open jobs.
6. **More lofts do not mean more Ringtails:** the arrival happens once per save, and births follow open night jobs,
   not beds. Ten lofts are ten homes; Inkpaws may live in spare loft beds and are swapped out only when a Ringtail
   needs one (adults) or a kit needs the slot (cubs move to a free cub slot elsewhere, never into homelessness).
7. **A demolished post:** its Ringtails become idle (the row shows them), keep their homes, rest and take leisure;
   no kits are raised until there are open night jobs again; a new post takes them at once.
8. **A mature village:** two rows in the population panel, night posts busy from the bell to dawn, Inkpaw workshops
   stocked and cleared overnight (with day-sized shelves, §18.3).

### 18.5 Interface: done and not done

| Piece | State |
|---|---|
| Ringtail badge (portrait, "Ringtail, age N", district link) | Done (`RingtailBadge`, priority 11 over the vanilla 10); seen in game, also used by the workplace worker list |
| Population panel second row (total, working, idle) | Done (`RingtailsPopulationRow`, a copy of the working-hours panel frame under the population panel), follows the selected district |
| Moon line on night posts and lofts | Done as a panel line (`RingtailsBuildingFragment`); phase 3 adds the drawn sun/moon mark and the day-shift line (§19) |
| "Closed for the day" status | Done (`NightPost`, normal status, reuses the vanilla `NoUnemployed` icon) |
| Moon mark in the toolbar, moon arc on the clock | Toolbar mark: art (the kit's icons are moon-marked). Clock arc: done in phase 3 (§19) |
| Ringtail names | Done: the generated templates carry `PandabornNamePoolSpec` with `Pandaborn.NamePool.Ringtails` |

All interface code runs inside `SafeUi`; a failing piece switches itself off for the session.

### 18.6 Tests and what is still unproven

| Run | What | Result |
|---|---|---|
| `rt2-module1` | The module on the real generated build: Moon Loft → arrival, three night posts, badge, row, panel lines, statuses, 34 h | Passed, 0 errors from our code. Found and fixed: the arriving kit could not move in (the arrival runs before the loft has worked out its kit slots), an Inkpaw cub took the loft's kit slot (now moved to a cub slot elsewhere) |
| `rt2-shelvesA/B/C` | Night couriers vs shelf size (§18.3) | Passed, 0 errors |
| `rt2-forcedoff` | A save with Ringtails reloaded with `force-off: Ringtails` (the probe writes the dev switch for the relaunch only and removes it) | Passed (exit 0, 0 errors from our code). Before the save: 2 Ringtail adults at the Night Builders' Post and a kit,
all living in the Moon Loft, three posts on the Ringtail type. After the relaunch with `force-off: Ringtails` (features
line "Ringtails: ForcedOff; RingtailsFallback: On"): the same three colonists, same names ("Dan Xia (Red clouds)", "Zhu
Guang (Candlelight)", "Hong Xia (Red sunset)") and the same loft home, now `InkpawAdult/InkpawChild.Inkpaws`; the
fallback switched all three posts to `Beaver` and Inkpaws staffed them (4, 3 and 2 workers); 16 colonists before and
after; the dev-switch file was removed by the reload |
| `rt2-soak` | Five days (2.5 + save/reload + 2.5), Bell on with a 12-hour day, three posts, ten Moon Lofts requested, workshops, a post demolished on day 1 | Passed both launches (exit 0, 0 errors from our code). Five in-game days with the Bell on (Bell's test numbers, slider
set to 12 h: day 1 kept the 16-hour day Bell had locked at the start, from day 2 the Ringtails' shift started at the
12-hour bell, as the Bell locked it at dawn). 0 job violations in 127 hourly samples; no critical need for anyone
(lowest Ringtail Sleep 0.26, Hunger 0.25, Thirst 0.23); the Night Builders' Post Ringtails carried 36 goods to the dens
queued after the bell (18 trips, all at night); the Night Gatherers' Post was demolished on day 1 and nothing broke;
16 of 16 colonists came back from the save with the same kind, template, job and home, and kept the cycle for the 2.6
days after it. Only 3 of the 10 Moon Lofts fitted on the Diorama terrace (so "ten lofts" is proven only as "three").
**No kit was raised in five days**, and the loft panel said why: "Kits: no room for a kit." The arriving family (2
adults and a kit) fills its own loft, and the nursery then wanted a Ringtail adult *living in* the raising loft. Fixed
after the soak (any Ringtail adult of the district counts, kits go to any loft with a free kit slot); the fix is
compiled but not yet run in game |
| `rt2-folktails` | Folktails with the module and test data | Passed (exit 0, 0 errors). Module loaded and inactive ("ringtailsGame: false"), no Ringtail created although the probe
asked for 2 adults and a kit, 332 placeable / 368 templates, identical to every earlier Folktails run |

Ringtail names work with the pool from `names.json` (test data: key `Pandaborn.NamePool.Ringtails`; seen in game:
"Dan Xia (Red clouds)", "Ma La (Numbing and hot)").

Unproven at the end of phase 2 (see §19 for what phase 3 proved): kits being raised in game (see the soak: the blocking rule is fixed in code but not yet run); ten Moon Lofts
(three fitted); walking in from the map edge (they appear at the loft); the toolbar moon
mark and the clock arc; the Night Builders' Post actually raising sites at night (it needs sites queued after the bell
in a layout with room; the soak queues dens after the bell); births over many days (one kit per loft per dawn was seen
blocked by the cub, then fixed, but a long breeding run was not done); the module-off case where the API check fails
for real (simulated by `force-off` and by `simulate-missing-member: Ringtails`, which takes the degraded path).

---

## 19. Phase 3: births, interface, clapper, data in the catalogue

Status: 2026-11-14. Tested on a dev copy of the installed faction build carrying the code under test
(`proto/foundation/build.ps1 -Name rtdev`, run with `-DisableMods JigglyPanda.PandabornFactions -ExtraMods
E:\PandabornDev\build\proto\rtdev,E:\PandabornDev\build\proto\ringtails`); the Ringtail data came from the installed
build, generated from the catalogue.

### 19.1 What changed

| Change | Detail |
|---|---|
| Data in the catalogue | The content lane adopted §18.1: templates, worker type, outfits, specs on posts and loft, alias and name pool are generated. `proto/ringtails` lost its data copy and `derive.py`; it is the test probe only (README there) |
| `IWorkdayClock` | `RingtailWorkday` takes `IEnumerable<IWorkdayClock>` (Core) and uses the first with `HasLockedDay`; the by-name Bell bridge is gone |
| Per-entity state | Nothing to move: Ringtails save only the arrival flag (`PandabornStore`). Colonists are ordinary entities, a post's worker type is the vanilla `WorkplaceWorkerType` save, a loft's nursery line is display only and comes back at the next dawn |
| Clock arc | `RingtailClockArc`: a pale arc inside the day clock's rim from the shift start to dawn, an extra child of the vanilla `Clock` element drawn with `Painter2D` |
| Sun and moon marks | `RingtailsBuildingFragment`: a drawn sun and "Day shift: Inkpaws work here from dawn to the afternoon bell." on every Inkpaw workplace, a crescent and "Night shift: Ringtails work here from the afternoon bell to dawn." on night posts, once the Ringtails have arrived. The mark sits beside the vanilla label in our own container (a child added inside the label, a text element, was not drawn: first run) |
| Clapper | `RingtailSounds`: `Environment.Pandaborn.NightClapper` (2D) once when the shift starts, 2.5 s after the bell when they coincide, only if the village has Ringtails and the clip exists; `RingtailTwitter` (3D at the loft) when the family arrives |
| Loft lodgers give way | Found in `rt3_ui3`: homeless Inkpaws moved into a new loft before its first dawn and it said "no room" for ever. Now, when the nursery has a kit to raise in a full loft, an Inkpaw lodger moves out (an Inkpaw cub in the kit slot first, else an Inkpaw adult) and looks for another home like any homeless colonist. Ringtails are never moved |

### 19.2 Runs

| Run | What | Result |
|---|---|---|
| `rt3_ui3` | Diorama, 2.4 days: a Moon Loft, three posts, four dens; a second loft on day 1 | Exit 0, 0 errors from our code. Arrival at once (2 adults, 1 kit); the clock arc from the first sample; the clapper "played" at both shift starts (hour 17 after dawn, the 16-hour bell plus the answer delay); loft 1 "no room" (2 Ringtails and their kit); loft 2 filled by homeless Inkpaws and also said "no room" (fixed, §19.1); the panel lines showed but the mark did not (fixed) |
| `rt3_breed3` | Plains, 7.2 days, save, reload, 6 more days (to day 13.2): ten lofts, three posts, six dens, a second Courier Post on day 4; in the reload, all water taken on day 7 and 600 given back on day 9 | Both launches passed (exit 0, 0 errors from our code), details below |

`rt3_breed3`, day by day (hourly samples, `python proto\ringtails\test\births.py E:\PandabornDev\build\test\rt3_breed3`):

* **The layout:** 21 buildings placed, but the upper terrace had no path to the district: 3 lofts, the Night Builders'
  Post and the first Night Courier Post were "unconnected" all game. So the district had **7 lofts** and 2 night jobs
  (Night Foragers' Post) until day 4, then 5 (the second Courier Post). This also shows the valve is per district:
  unconnected posts and lofts are ignored, as the vanilla job assigner ignores them.
* **Days 2-4:** 3 Ringtails (2 adults and the arrival kit), 2 jobs: every connected loft "Kits: waiting for open night
  jobs." No kit.
* **Day 4, hour 3:** second Courier Post (3 jobs). **Day 5 dawn:** open jobs 5 - 3 = 2, so exactly **2 kits** were raised,
  in two lofts that held Inkpaw lodgers (their cubs moved out); those lofts said "Kits: one is raised each morning..."
  for that day, then everyone went back to "waiting" (open jobs 0).
* **Save and reload at day 7:** all 5 Ringtails came back (2 adults, 3 kits) with names, homes and jobs; the nursery
  lines came back at the next dawn.
* **Growing up:** the arrival kit (Li Zi) grew up on day 7 and the two loft kits (Tao Tao, Luo Gu) by day 11 ("X grew
  up" messages). All three took the second Courier Post's three jobs: **5 Ringtails, 5 working, 0 idle**
  (`reload\rt_br_r5_h21_night_post.png`: the three grown kits on the post at night).
* **Starving:** water taken on day 7.1 (701 units); first colonist critically thirsty at hour 20; at the day 8 dawn
  every connected loft said "Kits: none while anyone in the district is hungry or thirsty." (19 colonists critical at
  worst). Water back on day 9.2; nobody critical by hour 6; at the day 10 dawn the lofts said "waiting" again. No deaths.
* **Valve:** Ringtails never outnumbered the district's night jobs (peak 5 of 5), never ran away with 21 free loft beds,
  and never fell below 2 adults. The clapper played at all 12 shift starts (6 per launch).

Nursery states seen: Raising, WaitingForJobs, Hungry (`rt3_breed3`), NoRoom (`rt3_ui3`); NoParents needs a district
without a Ringtail adult and was not staged.

Screenshots (in `E:\PandabornDev\build\test\`):

| What | File |
|---|---|
| Clock arc by day, at night, at dawn | `rt3_ui3\rt_ui_d0_h4_clock_day.png`, `rt3_ui3\rt_ui_d0_h20_clock_night.png`, `rt3_ui3\rt_ui_d1_h2_clock_dawn.png`; zoomed: `rt3_ui3\zoom_clock_day.png`, `rt3_ui3\zoom_clock_night.png` |
| Sun mark (Village Hall panel) | `rt3_breed3\rt_br_d0_h6_overview.png`, zoomed `rt3_breed3\zoom_sun.png` |
| Moon mark (Night Courier Post at night) | `rt3_breed3\reload\rt_br_r5_h21_night_post.png` |
| Loft "no room" | `rt3_ui3\rt_ui_d1_h1_loft_noroom.png` |
| Day-shift and night-shift lines before the mark fix | `rt3_ui3\rt_ui_d0_h5_inkpaw_workplace_sun.png`, `rt3_ui3\rt_ui_d0_h21_night_post_moon_night.png` |

The probe's loft shots in `rt3_breed3` picked the first loft, which was one of the unconnected ones, so the
"waiting" and "hungry" lines are proven by the samples (`ringtails.json`, `lofts[].kitState`), not by a picture.

### 19.3 Still unproven

Ten connected lofts on one map (seven were); the NoParents line in game; the twitter at the arrival (the call is
made, but no test records it);
walking in from the map edge; the Night Builders' Post raising sites at night (unconnected in `rt3_breed3`); the
module-off case where the API check fails for real.
