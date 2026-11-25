# Pandaborn.Ringtails - the second people

DESIGN.md Pillar 4. Results and the catalogue hand-over: `docs/tech/two-peoples.md` sections 17 and 18.

**What it does.** Ringtails are a hidden adult/kit template pair (in no template collection, so the vanilla
`BeaverFactory` still finds one adult) with the worker type `PandabornRingtail` (ignores working hours).

| Class | Job |
|---|---|
| `RingtailService` | The switch (a Ringtails game: the faction adult template carries `PandabornRingtailsSpec`), the load-time check of the two private members, the factory, save registration, the arrival (first finished Moon Loft: 2 adults and 1 kit move in, the night posts unlock for free except those with `UnlockOnArrival = false`, one message whose log entry leads to the loft) and the return (below). A finished loft only queues the arrival; the next tick carries it out, so no colonist is ever created inside a building's load step. Saved: `PandabornStore` "Ringtails" v1 `arrived=0|1;waits=<district id>:<empty dawns>,...` |
| `RingtailWorkday` | The bell in hours after dawn: the first Core `IWorkdayClock` with a locked day (Bell binds one), else the live slider; `ShiftStartHours` = the bell clamped to the Ringtail adult's limits (4 h, 16 h) and to nightfall as the game has it (`ShiftMath.ShiftStart`, one number for the rest, the post status, the clock arc and the clapper). Also Core's `INightShiftClock`: the length of the night shift, 24 h minus the shift start |
| `RingtailRestRootBehavior` | Rest from dawn to the shift start: to bed first thing unless nearly rested, then needs and leisure; a root behaviour inserted above `WorkerRootBehavior`. If it ever throws, that Ringtail goes back to the plain worker behaviour. It steps aside while a Core `IGatheringClock` says the Ringtail gathers now (meant for the Lantern Festival's evening: with a 16-hour day the rest runs to 16 h and the lantern release at 15.75 h was missed). **The Festival module does not register a clock yet**, so today nothing changes: see "Known, not fixed" |
| `NightPost` | On `PandabornNightPostSpec`: switches the post to the Ringtail worker type when finished or loaded, keeps it there, shows "Closed for the day" by day. A change made elsewhere (the beaver/bot toggle, copied settings) is switched back on the **next tick**, never inside the game's `WorkerTypeChanged` event (see "Found in review") |
| `MoonLoft`, `LoftNursery` | On `PandabornMoonLoftSpec`: triggers the arrival; at each dawn raises at most one kit per loft while the district has open night jobs (desired workers of Ringtail-typed posts minus living Ringtail adults and kits) and nobody is critically hungry or thirsty (`KitValve`, tested without the game). The loft's line is recounted while the loft is selected, so it is right after a load and for a loft built since dawn |
| The return | A district with a finished Moon Loft and no living Ringtail (old age took the last of them; a second district that never had any; a session with the module off, which turns Ringtails into Inkpaws while the arrival flag stays set) counts its empty dawns. After `PandabornRingtailsSpec.ReturnAfterDays` of them in a row (3), and while nobody starves, a new family moves into a loft of that district, with the message `Pandaborn.Ringtails.Returned`. Any Ringtail in the district ends the count |
| `LoftHousingRule` | Lofts are Ringtail homes: swaps an Inkpaw out for a Ringtail; a homeless Ringtail takes a loft bed. With `MoonLoft.MakeRoomForKit`, an Inkpaw lodger (cub first) moves out when the nursery has a kit to raise in a full loft |
| `RingtailCoat`, `RingtailGrowth`, `RingtailBadge` | Coat; kit grows into a Ringtail (if the adult cannot be created the kit is shown again and grows up as an Inkpaw); portrait and "Ringtail, age N" |
| `RingtailsPopulationRow` | The second population row (Ringtails, working, idle, free night jobs), behind `SafeUi`. The vanilla top bar counts employed, vacancies and unemployed for the `Beaver` and `Bot` worker types only (`PopulationDataCollector`), so Ringtails and their posts are missing from it by design of the game; the head count and the beds do include them. This row is where the night jobs are |
| `RingtailsBuildingFragment` | Once the Ringtails have arrived: a drawn sun and "Day shift: ..." on every Inkpaw workplace, a crescent and "Night shift: ..." on night posts, the nursery state on Moon Lofts; behind `SafeUi` |
| `RingtailClockArc` | A pale moon arc inside the rim of the vanilla day clock, from the shift start to dawn (an extra child of the clock's `Clock` element, vector-drawn; the clock itself is unchanged); behind `SafeUi` |
| `RingtailSounds`, `RingtailVoice` | Through Core's `PandabornSounds`: `Environment.Pandaborn.NightClapper` once when the shift starts (2.5 s after the bell when they coincide), only if the village has Ringtails; `RingtailTwitter` at the loft when a family arrives and when a living Ringtail is selected (over the faction's colonist call, which is vanilla's and chosen by faction), from the module's own object moved to the spot; silent when a clip is missing (docs/tech/sound.md section 8) |

**Data it needs**: generated from the catalogue (two-peoples.md §18.1: templates, worker type, outfits, specs on the
posts, loft and Inkpaw adult, the permanent alias). The sounds come from the `pandabornsounds` bundle.

**Saved**: the arrival flag and the districts' empty-dawn counts in `PandabornStore`. Nothing per colonist or per
building: Ringtails are ordinary entities saved under their template name, a night post's worker type is the vanilla
`WorkplaceWorkerType` save (re-applied on load), and a loft's nursery state is display only (recounted at each dawn and
while the loft is selected). So no `PandabornEntityState` is needed.

**The rested bonus (2026-11-25)** is not in this module. Ringtails get the Bell's bonus by the length of their night
shift; the Bell applies it (`Pandaborn.Bell/BellNightShift.cs`, a component on `PandabornRingtailSpec`) and reads the
shift length through Core's `INightShiftClock`, which `RingtailWorkday` implements. This module does not know the Bell
exists: with the Bell off Ringtails work at plain speed, as Inkpaws do. Why there and not here: the Bell owns the
curve, the multiplying share, the walking-speed cap and the colonist line; the only thing it lacked was one number.

**Found in review (2026-11-25), fixed.** (1) One click on the vanilla beaver/bot toggle of a night post (shown once a
bot exists), or copying settings onto one, crashed the game: the post switched itself back inside the game's
`WorkerTypeChanged` event, the game's `DistrictWorkplaceAssigner` then got the two events in the wrong order and added
the post to its Ringtail list twice (`SortedList.Add`, `ArgumentException`). The switch back now waits for the next tick.
(2) The arrival created colonists inside the loft's finished-state step, which on a load runs while the world is still
being put together (a save whose first loft was finished while the module was off or degraded). It is queued now.
(3) A homeless Ringtail could be given a den bed taken from an Inkpaw who had just been swapped out of a loft.
(4) Dawn handler, housing rule, rest behaviour, growth, post and fallback callbacks are contained: an exception
switches that piece off and is logged, instead of crashing the tick or failing the load.
(5) The people could die out for good (the arrival happened once per save, kits need an adult): see "The return".

**Known, not fixed.** On a festival day with a working day of more than 15.5 hours, Ringtails are still in their rest
when the show starts and miss its first half hour, the lantern release included (the rest sits above the festival's
behaviour). The Ringtails' half of the fix is in (`IGatheringClock` in Core, the rest steps aside); the Festival's half
is to register one: `MultiBind<Pandaborn.Core.IGatheringClock>().ToExisting<FestivalService>()` and
`bool GathersNow(BaseComponent colonist)` = it is show time and the colonist's district holds the festival. A night post still shows
 the vanilla beaver/bot toggle once a bot exists; clicking it does nothing
(the post takes itself back within a tick), and a player can spend science unlocking bots for a post that will not keep
them (the catalogue could drop the posts' bot unlock cost; hiding the toggle needs interface code). The vanilla top-bar
job numbers leave Ringtails out (above). Ringtails appear at the loft's door; walking in from the map edge is not built.


**Fails safely**: module off (API check, forced off) or degraded (private member gone, or the dev switch
`simulate-missing-member: Ringtails`): saved Ringtails load as Inkpaws through the alias, no new Ringtails, and
`Pandaborn.RingtailsFallback` turns night posts back into Inkpaw workplaces. Moon Lofts are plain homes.

**Uses from Core**: `FeatureRegistry`, `PandabornStore`, `Messenger`, `SafeUi`, `IWorkdayClock` (all clocks injected as
`IEnumerable<IWorkdayClock>`; no by-name access to any other module).

<!-- api:begin -->
<!-- Generated from the compiled module by Pandaborn.ApiScan on every build. Do not edit by hand. -->

### Game API this module references

**Bindito.Core**

* type `Bindito.Core.Configurator`
  * method `.ctor()`
  * method `Bind<1>()`: `Bindito.Core.ISingleBindingBuilder`1<!!0>`
  * method `MultiBind<1>()`: `Bindito.Core.IMultiBindingBuilder`1<!!0>`
* type `Bindito.Core.ContextAttribute`
  * method `.ctor(System.String)`
* type `Bindito.Core.IBindingBuilder`1`
  * method `ToExisting<1>()`: `Bindito.Core.IExportAssignee`
  * method `ToProvider(System.Func`1<!0>)`: `Bindito.Core.IScopeAssignee`
  * method `ToProvider<1>()`: `Bindito.Core.IScopeAssignee`
* type `Bindito.Core.IExportAssignee`
* type `Bindito.Core.IMultiBindingBuilder`1`
* type `Bindito.Core.IProvider`1`
* type `Bindito.Core.IScopeAssignee`
  * method `AsSingleton()`: `Bindito.Core.IExportAssignee`
  * method `AsTransient()`: `Bindito.Core.IExportAssignee`
* type `Bindito.Core.ISingleBindingBuilder`1`

**Timberborn.BaseComponentSystem**

* type `Timberborn.BaseComponentSystem.BaseComponent`
  * method `.ctor()`
  * method `DisableComponent()`
  * method `GetComponent<1>()`: `!!0`
  * method `get_GameObject()`: `UnityEngine.GameObject`
  * method `get_Name()`: `System.String`
  * method `get_Transform()`: `UnityEngine.Transform`
  * method `op_Implicit(Timberborn.BaseComponentSystem.BaseComponent)`: `System.Boolean`
* type `Timberborn.BaseComponentSystem.IAwakableComponent`

**Timberborn.BeaverContaminationSystem**

* type `Timberborn.BeaverContaminationSystem.Contaminable`
  * method `get_IsContaminated()`: `System.Boolean`

**Timberborn.Beavers**

* type `Timberborn.Beavers.AdultSpec`
* type `Timberborn.Beavers.Beaver`
* type `Timberborn.Beavers.Child`
  * method `get_GrowthProgress()`: `System.Single`

**Timberborn.BehaviorSystem**

* type `Timberborn.BehaviorSystem.Behavior`
  * method `Decide(Timberborn.BehaviorSystem.BehaviorAgent)`: `Timberborn.BehaviorSystem.Decision`
* type `Timberborn.BehaviorSystem.BehaviorAgent`
* type `Timberborn.BehaviorSystem.BehaviorManager`
* type `Timberborn.BehaviorSystem.Decision`
  * method `ReleaseNextTick()`: `Timberborn.BehaviorSystem.Decision`
  * method `ReleaseNow()`: `Timberborn.BehaviorSystem.Decision`
  * method `TransferNow(Timberborn.BehaviorSystem.Behavior, Timberborn.BehaviorSystem.Decision&)`: `Timberborn.BehaviorSystem.Decision`
  * method `get_ShouldReleaseNow()`: `System.Boolean`
* type `Timberborn.BehaviorSystem.RootBehavior`
  * method `.ctor()`

**Timberborn.BlockSystem**

* type `Timberborn.BlockSystem.BlockObject`
  * method `get_HasEntrance()`: `System.Boolean`
  * method `get_IsFinished()`: `System.Boolean`
  * method `get_PositionedEntrance()`: `Timberborn.BlockSystem.PositionedEntrance`
* type `Timberborn.BlockSystem.IFinishedStateListener`
* type `Timberborn.BlockSystem.PositionedEntrance`
  * method `get_Coordinates()`: `UnityEngine.Vector3Int`

**Timberborn.BlueprintSystem**

* type `Timberborn.BlueprintSystem.AssetRef`1`
  * method `get_Asset()`: `!0`
* type `Timberborn.BlueprintSystem.Blueprint`
  * method `GetSpec<1>()`: `!!0`
* type `Timberborn.BlueprintSystem.ComponentSpec`
  * method `GetSpec<1>()`: `!!0`
  * method `get_Blueprint()`: `Timberborn.BlueprintSystem.Blueprint`
* type `Timberborn.BlueprintSystem.ISpecService`
  * method `GetBlueprint(System.String)`: `Timberborn.BlueprintSystem.Blueprint`

**Timberborn.Buildings**

* type `Timberborn.Buildings.BuildingSpec`
  * method `op_Inequality(Timberborn.Buildings.BuildingSpec, Timberborn.Buildings.BuildingSpec)`: `System.Boolean`

**Timberborn.Characters**

* type `Timberborn.Characters.Character`
  * method `get_Age()`: `System.Int32`
  * method `get_Alive()`: `System.Boolean`
  * method `get_FirstName()`: `System.String`
* type `Timberborn.Characters.CharacterInit`
  * method `.ctor(System.Int32, System.Single, Timberborn.Characters.Character, UnityEngine.Vector3, UnityEngine.Quaternion)`
* type `Timberborn.Characters.CharacterMaterialModifier`
  * method `SetTexture(System.Int32, UnityEngine.Texture)`

**Timberborn.Common**

* type `Timberborn.Common.IRandomNumberGenerator`
  * method `Range(System.Int32, System.Int32)`: `System.Int32`
* type `Timberborn.Common.ReadOnlyList`1`
  * method `GetEnumerator()`: `System.Collections.Generic.List`1+Enumerator<!0>`
  * method `get_Count()`: `System.Int32`
  * method `get_Item(System.Int32)`: `!0`

**Timberborn.Coordinates**

* type `Timberborn.Coordinates.CoordinateSystem`
  * method `GridToWorldCentered(UnityEngine.Vector3Int)`: `UnityEngine.Vector3`

**Timberborn.CoreUI**

* type `Timberborn.CoreUI.VisualElementExtensions`
  * method `ToggleDisplayStyle(UnityEngine.UIElements.VisualElement, System.Boolean)`
* type `Timberborn.CoreUI.VisualElementLoader`
  * method `LoadVisualElement(System.String)`: `UnityEngine.UIElements.VisualElement`

**Timberborn.DwellingSystem**

* type `Timberborn.DwellingSystem.Dweller`
  * method `get_HasHome()`: `System.Boolean`
  * method `get_Home()`: `Timberborn.DwellingSystem.Dwelling`
* type `Timberborn.DwellingSystem.Dwelling`
  * method `AssignDweller(Timberborn.DwellingSystem.Dweller)`
  * method `UnassignDweller(Timberborn.DwellingSystem.Dweller)`
  * method `get_AdultDwellers()`: `System.Collections.Generic.IEnumerable`1<Timberborn.DwellingSystem.Dweller>`
  * method `get_ChildDwellers()`: `System.Collections.Generic.IEnumerable`1<Timberborn.DwellingSystem.Dweller>`
  * method `get_ChildSlots()`: `System.Int32`
  * method `get_HasFreeChildSlots()`: `System.Boolean`
  * method `get_HasFreeSlots()`: `System.Boolean`
  * method `get_NumberOfChildDwellers()`: `System.Int32`
  * method `get_UnderpopulatedByChildren()`: `System.Boolean`

**Timberborn.EntityPanelSystem**

* type `Timberborn.EntityPanelSystem.ClickableSubtitle`
  * method `Create(System.Action, System.String)`: `Timberborn.EntityPanelSystem.ClickableSubtitle`
  * method `CreateEmpty()`: `Timberborn.EntityPanelSystem.ClickableSubtitle`
* type `Timberborn.EntityPanelSystem.EntityPanelModule`
* type `Timberborn.EntityPanelSystem.EntityPanelModule+Builder`
  * method `.ctor()`
  * method `AddMiddleFragment(Timberborn.EntityPanelSystem.IEntityPanelFragment, System.Int32)`
  * method `Build()`: `Timberborn.EntityPanelSystem.EntityPanelModule`
* type `Timberborn.EntityPanelSystem.IEntityBadge`
* type `Timberborn.EntityPanelSystem.IEntityPanelFragment`

**Timberborn.EntitySystem**

* type `Timberborn.EntitySystem.EntityComponent`
  * method `get_EntityId()`: `System.Guid`
* type `Timberborn.EntitySystem.EntityService`
  * method `Instantiate(Timberborn.EntitySystem.EntitySetup+Builder)`: `Timberborn.EntitySystem.EntityComponent`
* type `Timberborn.EntitySystem.EntitySetup`
* type `Timberborn.EntitySystem.EntitySetup+Builder`
  * method `.ctor(Timberborn.BlueprintSystem.Blueprint)`
  * method `AddInitComponent(System.Object)`: `Timberborn.EntitySystem.EntitySetup+Builder`
* type `Timberborn.EntitySystem.IInitializableEntity`
* type `Timberborn.EntitySystem.IPostInitializableEntity`

**Timberborn.FactionSystem**

* type `Timberborn.FactionSystem.FactionSpec`
  * method `get_Id()`: `System.String`

**Timberborn.GameDistricts**

* type `Timberborn.GameDistricts.Citizen`
  * method `get_AssignedDistrict()`: `Timberborn.GameDistricts.DistrictCenter`
  * method `get_HasAssignedDistrict()`: `System.Boolean`
* type `Timberborn.GameDistricts.DistrictBuilding`
  * method `get_InstantDistrict()`: `Timberborn.GameDistricts.DistrictCenter`
* type `Timberborn.GameDistricts.DistrictBuildingRegistry`
  * method `GetEnabledBuildingsInstant<1>()`: `System.Collections.Generic.IEnumerable`1<!!0>`
* type `Timberborn.GameDistricts.DistrictCenter`
  * method `get_DistrictName()`: `System.String`
  * method `get_DistrictPopulation()`: `Timberborn.GameDistricts.DistrictPopulation`
* type `Timberborn.GameDistricts.DistrictCenterRegistry`
  * method `get_FinishedDistrictCenters()`: `Timberborn.Common.ReadOnlyList`1<Timberborn.GameDistricts.DistrictCenter>`
* type `Timberborn.GameDistricts.DistrictContextService`
  * method `get_SelectedDistrict()`: `Timberborn.GameDistricts.DistrictCenter`
* type `Timberborn.GameDistricts.DistrictPopulation`
  * method `get_Adults()`: `Timberborn.Common.ReadOnlyList`1<Timberborn.Beavers.Beaver>`
  * method `get_Beavers()`: `Timberborn.Common.ReadOnlyList`1<Timberborn.Beavers.Beaver>`
  * method `get_Children()`: `Timberborn.Common.ReadOnlyList`1<Timberborn.Beavers.Beaver>`

**Timberborn.GameFactionSystem**

* type `Timberborn.GameFactionSystem.FactionService`
  * method `get_Current()`: `Timberborn.FactionSystem.FactionSpec`

**Timberborn.LifeSystem**

* type `Timberborn.LifeSystem.LifeProgressor`
  * method `get_LifeProgress()`: `System.Single`
* type `Timberborn.LifeSystem.LifeService`
  * method `AdulthoodProgressToLifeProgress(System.Single)`: `System.Single`
  * method `CalculateDayOfBirth(System.Single)`: `System.Int32`
  * method `ChildhoodProgressToLifeProgress(System.Single)`: `System.Single`

**Timberborn.Localization**

* type `Timberborn.Localization.ILoc`
  * method `T(System.String)`: `System.String`
  * method `T<1>(System.String, !!0)`: `System.String`
  * method `T<3>(System.String, !!0, !!1, !!2)`: `System.String`

**Timberborn.MortalSystem**

* type `Timberborn.MortalSystem.Mortal`
  * method `get_Dead()`: `System.Boolean`

**Timberborn.NeedBehaviorSystem**

* type `Timberborn.NeedBehaviorSystem.NeederRootBehavior`

**Timberborn.NeedSystem**

* type `Timberborn.NeedSystem.NeedManager`
  * method `GetNeedPoints(System.String)`: `System.Single`
  * method `HasNeed(System.String)`: `System.Boolean`
  * method `NeedIsInCriticalState(System.String)`: `System.Boolean`

**Timberborn.RootProviders**

* type `Timberborn.RootProviders.RootObjectProvider`
  * method `CreateRootObject(System.String)`: `UnityEngine.GameObject`

**Timberborn.ScienceSystem**

* type `Timberborn.ScienceSystem.BuildingUnlockingService`
  * method `UnlockIgnoringCost(Timberborn.Buildings.BuildingSpec)`
  * method `Unlocked(Timberborn.Buildings.BuildingSpec)`: `System.Boolean`

**Timberborn.SelectionSystem**

* type `Timberborn.SelectionSystem.EntitySelectionService`
  * method `SelectAndFocusOn(Timberborn.BaseComponentSystem.BaseComponent)`
* type `Timberborn.SelectionSystem.ISelectionListener`

**Timberborn.SingletonSystem**

* type `Timberborn.SingletonSystem.EventBus`
  * method `Register(System.Object)`
* type `Timberborn.SingletonSystem.ILoadableSingleton`
* type `Timberborn.SingletonSystem.IPostLoadableSingleton`
* type `Timberborn.SingletonSystem.IUpdatableSingleton`
* type `Timberborn.SingletonSystem.OnEventAttribute`
  * method `.ctor()`

**Timberborn.SleepSystem**

* type `Timberborn.SleepSystem.SleepNeedBehavior`

**Timberborn.StatusSystem**

* type `Timberborn.StatusSystem.StatusSubject`
  * method `RegisterStatus(Timberborn.StatusSystem.StatusToggle)`
* type `Timberborn.StatusSystem.StatusToggle`
  * method `CreateNormalStatus(System.String, System.String)`: `Timberborn.StatusSystem.StatusToggle`
  * method `Deactivate()`
  * method `Toggle(System.Boolean)`

**Timberborn.TemplateInstantiation**

* type `Timberborn.TemplateInstantiation.TemplateInstantiator`
  * method `CacheInstance(Timberborn.BlueprintSystem.Blueprint)`
* type `Timberborn.TemplateInstantiation.TemplateModule`
* type `Timberborn.TemplateInstantiation.TemplateModule+Builder`
  * method `.ctor()`
  * method `AddDecorator<2>()`
  * method `Build()`: `Timberborn.TemplateInstantiation.TemplateModule`

**Timberborn.TemplateSystem**

* type `Timberborn.TemplateSystem.TemplateNameMapper`
  * method `TryGetTemplate(System.String, Timberborn.TemplateSystem.TemplateSpec&)`: `System.Boolean`
* type `Timberborn.TemplateSystem.TemplateService`
  * method `GetAll<1>()`: `System.Collections.Generic.IEnumerable`1<!!0>`
  * method `GetSingle<1>()`: `!!0`
* type `Timberborn.TemplateSystem.TemplateSpec`
  * method `get_TemplateName()`: `System.String`

**Timberborn.TickSystem**

* type `Timberborn.TickSystem.ITickableSingleton`
* type `Timberborn.TickSystem.TickableComponent`
  * method `.ctor()`

**Timberborn.TimeSystem**

* type `Timberborn.TimeSystem.DaytimeStartEvent`
* type `Timberborn.TimeSystem.IDayNightCycle`
  * method `BoundsInHours(Timberborn.TimeSystem.TimeOfDay)`: `System.ValueTuple`2<System.Single,System.Single>`
  * method `get_DayNumber()`: `System.Int32`
  * method `get_DaytimeLengthInHours()`: `System.Single`
  * method `get_HoursPassedToday()`: `System.Single`
  * method `get_NighttimeLengthInHours()`: `System.Single`
* type `Timberborn.TimeSystem.TimeOfDay`

**Timberborn.UILayoutSystem**

* type `Timberborn.UILayoutSystem.ShowPrimaryUIEvent`
* type `Timberborn.UILayoutSystem.UILayout`
  * method `AddAbsoluteItem(UnityEngine.UIElements.VisualElement)`
  * method `AddTopLeft(UnityEngine.UIElements.VisualElement, System.Int32)`

**Timberborn.Wandering**

* type `Timberborn.Wandering.WanderRootBehavior`

**Timberborn.WorkSystem**

* type `Timberborn.WorkSystem.Worker`
  * method `get_Employed()`: `System.Boolean`
* type `Timberborn.WorkSystem.WorkerRootBehavior`
* type `Timberborn.WorkSystem.WorkerTypeChangedEventArgs`
* type `Timberborn.WorkSystem.WorkingHoursManager`
  * method `get_EndHours()`: `System.Single`
* type `Timberborn.WorkSystem.Workplace`
  * method `get_DesiredWorkers()`: `System.Int32`
  * method `get_NumberOfAssignedWorkers()`: `System.Int32`
* type `Timberborn.WorkSystem.WorkplaceWorkerType`
  * method `SetWorkerType(System.String)`
  * method `add_WorkerTypeChanged(System.EventHandler`1<Timberborn.WorkSystem.WorkerTypeChangedEventArgs>)`
  * method `get_WorkerType()`: `System.String`

**UnityEngine.CoreModule**

* type `UnityEngine.Color`
  * method `.ctor(System.Single, System.Single, System.Single, System.Single)`
* type `UnityEngine.Debug`
  * method `Log(System.Object)`
  * method `LogError(System.Object)`
  * method `LogWarning(System.Object)`
* type `UnityEngine.GameObject`
  * method `SetActive(System.Boolean)`
  * method `get_transform()`: `UnityEngine.Transform`
* type `UnityEngine.Mathf`
  * method `Abs(System.Single)`: `System.Single`
  * method `Clamp(System.Int32, System.Int32, System.Int32)`: `System.Int32`
  * method `Cos(System.Single)`: `System.Single`
  * method `Min(System.Single, System.Single)`: `System.Single`
  * method `RoundToInt(System.Single)`: `System.Int32`
  * method `Sin(System.Single)`: `System.Single`
* type `UnityEngine.Object`
  * method `get_name()`: `System.String`
  * method `op_Implicit(UnityEngine.Object)`: `System.Boolean`
* type `UnityEngine.Quaternion`
  * method `get_identity()`: `UnityEngine.Quaternion`
* type `UnityEngine.Rect`
  * method `get_height()`: `System.Single`
  * method `get_width()`: `System.Single`
  * method `get_x()`: `System.Single`
  * method `get_y()`: `System.Single`
* type `UnityEngine.Shader`
  * method `PropertyToID(System.String)`: `System.Int32`
* type `UnityEngine.Sprite`
* type `UnityEngine.Texture`
* type `UnityEngine.Texture2D`
* type `UnityEngine.Time`
  * method `get_unscaledTime()`: `System.Single`
* type `UnityEngine.Transform`
  * method `get_position()`: `UnityEngine.Vector3`
  * method `set_position(UnityEngine.Vector3)`
* type `UnityEngine.Vector2`
  * method `.ctor(System.Single, System.Single)`
  * method `op_Addition(UnityEngine.Vector2, UnityEngine.Vector2)`: `UnityEngine.Vector2`
  * method `op_Multiply(UnityEngine.Vector2, System.Single)`: `UnityEngine.Vector2`
* type `UnityEngine.Vector3`
  * method `.ctor(System.Single, System.Single, System.Single)`
  * method `op_Addition(UnityEngine.Vector3, UnityEngine.Vector3)`: `UnityEngine.Vector3`
* type `UnityEngine.Vector3Int`

**UnityEngine.UIElementsModule**

* type `UnityEngine.UIElements.Angle`
  * method `Degrees(System.Single)`: `UnityEngine.UIElements.Angle`
* type `UnityEngine.UIElements.ArcDirection`
* type `UnityEngine.UIElements.Button`
* type `UnityEngine.UIElements.DisplayStyle`
* type `UnityEngine.UIElements.FillRule`
* type `UnityEngine.UIElements.IPanel`
  * method `get_visualTree()`: `UnityEngine.UIElements.VisualElement`
* type `UnityEngine.UIElements.IStyle`
  * method `set_bottom(UnityEngine.UIElements.StyleLength)`
  * method `set_display(UnityEngine.UIElements.StyleEnum`1<UnityEngine.UIElements.DisplayStyle>)`
  * method `set_height(UnityEngine.UIElements.StyleLength)`
  * method `set_left(UnityEngine.UIElements.StyleLength)`
  * method `set_marginTop(UnityEngine.UIElements.StyleLength)`
  * method `set_paddingLeft(UnityEngine.UIElements.StyleLength)`
  * method `set_position(UnityEngine.UIElements.StyleEnum`1<UnityEngine.UIElements.Position>)`
  * method `set_right(UnityEngine.UIElements.StyleLength)`
  * method `set_top(UnityEngine.UIElements.StyleLength)`
  * method `set_width(UnityEngine.UIElements.StyleLength)`
* type `UnityEngine.UIElements.Label`
* type `UnityEngine.UIElements.Length`
  * method `Percent(System.Single)`: `UnityEngine.UIElements.Length`
* type `UnityEngine.UIElements.LineCap`
* type `UnityEngine.UIElements.MeshGenerationContext`
  * method `get_painter2D()`: `UnityEngine.UIElements.Painter2D`
* type `UnityEngine.UIElements.Painter2D`
  * method `Arc(UnityEngine.Vector2, System.Single, UnityEngine.UIElements.Angle, UnityEngine.UIElements.Angle, UnityEngine.UIElements.ArcDirection)`
  * method `BeginPath()`
  * method `ClosePath()`
  * method `Fill(UnityEngine.UIElements.FillRule)`
  * method `LineTo(UnityEngine.Vector2)`
  * method `MoveTo(UnityEngine.Vector2)`
  * method `Stroke()`
  * method `set_fillColor(UnityEngine.Color)`
  * method `set_lineCap(UnityEngine.UIElements.LineCap)`
  * method `set_lineWidth(System.Single)`
  * method `set_strokeColor(UnityEngine.Color)`
* type `UnityEngine.UIElements.PickingMode`
* type `UnityEngine.UIElements.Position`
* type `UnityEngine.UIElements.StyleEnum`1`
  * method `op_Implicit(!0)`: `UnityEngine.UIElements.StyleEnum`1<!0>`
* type `UnityEngine.UIElements.StyleLength`
  * method `op_Implicit(System.Single)`: `UnityEngine.UIElements.StyleLength`
  * method `op_Implicit(UnityEngine.UIElements.Length)`: `UnityEngine.UIElements.StyleLength`
* type `UnityEngine.UIElements.TextElement`
  * method `get_text()`: `System.String`
  * method `set_text(System.String)`
* type `UnityEngine.UIElements.UQueryExtensions`
  * method `Q<1>(UnityEngine.UIElements.VisualElement, System.String, System.String)`: `!!0`
* type `UnityEngine.UIElements.VisualElement`
  * method `.ctor()`
  * method `Add(UnityEngine.UIElements.VisualElement)`
  * method `MarkDirtyRepaint()`
  * method `get_contentRect()`: `UnityEngine.Rect`
  * method `get_generateVisualContent()`: `System.Action`1<UnityEngine.UIElements.MeshGenerationContext>`
  * method `get_panel()`: `UnityEngine.UIElements.IPanel`
  * method `get_style()`: `UnityEngine.UIElements.IStyle`
  * method `get_worldBound()`: `UnityEngine.Rect`
  * method `set_generateVisualContent(System.Action`1<UnityEngine.UIElements.MeshGenerationContext>)`
  * method `set_name(System.String)`
  * method `set_pickingMode(UnityEngine.UIElements.PickingMode)`

**Game classes derived from and interfaces implemented** (with the abstract members each had at build time; a new one keeps the module from loading)

* class `Bindito.Core.Configurator`: `Configure`
* interface `Bindito.Core.IProvider`1`: `Get`
* class `Timberborn.BaseComponentSystem.BaseComponent`
* interface `Timberborn.BaseComponentSystem.IAwakableComponent`: `Awake`
* class `Timberborn.BehaviorSystem.RootBehavior`: `Decide`
* interface `Timberborn.BlockSystem.IFinishedStateListener`: `OnEnterFinishedState`, `OnExitFinishedState`
* interface `Timberborn.EntityPanelSystem.IEntityBadge`: `GetEntityAvatar`, `GetEntityClickableSubtitle`, `GetEntitySubtitle`, `get_EntityBadgePriority`
* interface `Timberborn.EntityPanelSystem.IEntityPanelFragment`: `ClearFragment`, `InitializeFragment`, `ShowFragment`, `UpdateFragment`
* interface `Timberborn.EntitySystem.IInitializableEntity`: `InitializeEntity`
* interface `Timberborn.EntitySystem.IPostInitializableEntity`: `PostInitializeEntity`
* interface `Timberborn.SelectionSystem.ISelectionListener`: `OnSelect`, `OnUnselect`
* interface `Timberborn.SingletonSystem.ILoadableSingleton`: `Load`
* interface `Timberborn.SingletonSystem.IPostLoadableSingleton`: `PostLoad`
* interface `Timberborn.SingletonSystem.IUpdatableSingleton`: `UpdateSingleton`
* interface `Timberborn.TickSystem.ITickableSingleton`: `Tick`
* class `Timberborn.TickSystem.TickableComponent`: `Tick`

<!-- api:end -->
