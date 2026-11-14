# Two peoples: technical design

Status: feasibility study, 2026-11-14. Research only: nothing here has run in game yet.
Game: Timberborn 1.1.2.8. All code paths are relative to `E:\PandabornDev\reference\decompiled` and were read
for this note. Blueprint paths are relative to `E:\PandabornDev\reference\Blueprints`. Bindito internals were
decompiled into a scratch folder (`Bindito.Core.dll`, not kept).

The design target is Pillar 1 as rewritten on 2026-11-14: **Inkpaws work the day, Ringtails work the night**,
with automatic day and night crews on every workplace, Ringtails arriving with the first loft, and an optional
"Long Nap" bet. The earlier three-way toggle model is covered too, as fallback rung 2.

---

## 1. Verdict

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

## 2. Facts checked (the brief's "already found" list)

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

## 3. Architecture for two living kinds

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

## 4. Day and night crews on one workplace

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

## 5. Night workers: sleep, beds, leisure, day stage

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

## 6. Per-kind stats and appetite

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

## 7. Housing, births, arrival, Long Nap

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

## 8. Appearance

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

## 9. UI

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

## 10. Tutorial and messages

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

## 11. Bots ("Wooden Oxen")

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

## 12. Data, code, reflection, Harmony

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

## 13. Risks, ranked

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

## 14. Staged plan

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

## 15. Fallback ladder

| Rung | What the player gets | Code | Reflection | Harmony | Robustness across updates |
|---|---|---|---|---|---|
| 1. Shared workplaces, automatic crews (W3) | The design | Largest: factory, scheduler, crews, rest behaviour, nursery, UI (rough order: 2,000–3,000 lines C#) | `TemplateNameMapper`, `BehaviorManager` root list, optional `Need` fields | None required; optional `PopulationDataCollector` postfix | Medium. Depends on public work-system API, two private fields, and the vanilla behaviour order |
| 2. One people per workplace, simple toggle | Toggle Inkpaws/Ringtails (or day/night) per workplace, district default | Same factory and nursery; the scheduler shrinks to "open Ringtail workplaces at night, close by day" (otherwise Ringtails would work 24 h, since a per-kind clock needs Harmony). Saves crew memory and some UI (rough order: 1,200–2,000 lines) | Same as rung 1 | None | Medium. Night work still needs the rest behaviour; with **same hours for both peoples**, the rest behaviour and scheduler go away and only `TemplateNameMapper` remains |
| 3. One people, Ringtail coats as variety | Inkpaws with red coats in the pool | None (`FactionSpec.Textures`) | None | None | High |

Realistic and robust: **rung 1 is realistic** and needs no Harmony; its fragile parts are few and testable.
**Rung 2 without night work** (same hours for both peoples) is the most robust version that still has two peoples.
Rung 3 is the safe floor.

---

## 16. Design changes suggested by the code

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
