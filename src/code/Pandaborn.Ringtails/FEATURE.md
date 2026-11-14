# Pandaborn.Ringtails - the second people

DESIGN.md Pillar 4. Results and the catalogue hand-over: `docs/tech/two-peoples.md` sections 17 and 18.

**What it does.** Ringtails are a hidden adult/kit template pair (in no template collection, so the vanilla
`BeaverFactory` still finds one adult) with the worker type `PandabornRingtail` (ignores working hours).

| Class | Job |
|---|---|
| `RingtailService` | The switch (a Ringtails game: the faction adult template carries `PandabornRingtailsSpec`), the load-time check of the two private members, the factory, save registration, the arrival (first finished Moon Loft: 2 adults and 1 kit move in, the night posts unlock for free, one message). Saved: `PandabornStore` "Ringtails" v1 `arrived=0|1` |
| `RingtailWorkday` | The bell in hours after dawn: Bell's day locked at dawn when Bell is on (read by name, no reference), else the live slider |
| `RingtailRestRootBehavior` | Rest from dawn to the bell (clamped 4–16 h): to bed first thing unless nearly rested, then needs and leisure; a root behaviour inserted above `WorkerRootBehavior` |
| `NightPost` | On `PandabornNightPostSpec`: switches the post to the Ringtail worker type when finished or loaded, keeps it there, shows "Closed for the day" by day |
| `MoonLoft`, `LoftNursery` | On `PandabornMoonLoftSpec`: triggers the arrival; at each dawn raises at most one kit per loft while the district has open night jobs (desired workers of Ringtail-typed posts minus Ringtail adults and kits) and nobody is critically hungry or thirsty |
| `LoftHousingRule` | Lofts are Ringtail homes: swaps an Inkpaw out for a Ringtail; a homeless Ringtail takes a loft bed |
| `RingtailCoat`, `RingtailGrowth`, `RingtailBadge` | Coat; kit grows into a Ringtail; portrait and "Ringtail, age N" |
| `RingtailsPopulationRow`, `RingtailsBuildingFragment` | The second population row (Ringtails, working, idle) and the moon line on night posts and lofts, behind `SafeUi` |

**Data it needs**: see two-peoples.md §18.1 (templates, worker type, outfits, specs on the posts, loft and Inkpaw adult,
the permanent alias).

**Saved**: the arrival flag in `PandabornStore`. Ringtails are ordinary entities saved under their template name.

**Fails safely**: module off (API check, forced off) or degraded (private member gone, or the dev switch
`simulate-missing-member: Ringtails`): saved Ringtails load as Inkpaws through the alias, no new Ringtails, and
`Pandaborn.RingtailsFallback` turns night posts back into Inkpaw workplaces. Moon Lofts are plain homes.

**Wanted from Core** (proposal): `public interface IWorkdayClock { bool HasLockedDay { get; } int LockedWorkdayHours { get; } }`
in `Pandaborn.Core`, bound by Bell (`MultiBind<IWorkdayClock>().To<BellService>()`); Ringtails would take
`IEnumerable<IWorkdayClock>` and drop the by-name bridge in `RingtailWorkday`.

<!-- api:begin -->
<!-- Generated from the compiled module by Pandaborn.ApiScan on every build. Do not edit by hand. -->

### Game API this module references

**Bindito.Core**

* type `Bindito.Core.Configurator`
  * method `.ctor()`
  * method `Bind<1>()`
  * method `MultiBind<1>()`
* type `Bindito.Core.ContextAttribute`
  * method `.ctor(System.String)`
* type `Bindito.Core.IBindingBuilder`1`
  * method `ToProvider(System.Func`1<!0>)`
  * method `ToProvider<1>()`
* type `Bindito.Core.IExportAssignee`
* type `Bindito.Core.IMultiBindingBuilder`1`
* type `Bindito.Core.IProvider`1`
* type `Bindito.Core.IScopeAssignee`
  * method `AsSingleton()`
  * method `AsTransient()`
* type `Bindito.Core.ISingleBindingBuilder`1`

**Timberborn.BaseComponentSystem**

* type `Timberborn.BaseComponentSystem.BaseComponent`
  * method `.ctor()`
  * method `DisableComponent()`
  * method `GetComponent<1>()`
  * method `get_GameObject()`
  * method `get_Transform()`
  * method `op_Implicit(Timberborn.BaseComponentSystem.BaseComponent)`
* type `Timberborn.BaseComponentSystem.IAwakableComponent`

**Timberborn.BeaverContaminationSystem**

* type `Timberborn.BeaverContaminationSystem.Contaminable`
  * method `get_IsContaminated()`

**Timberborn.Beavers**

* type `Timberborn.Beavers.AdultSpec`
* type `Timberborn.Beavers.Beaver`
* type `Timberborn.Beavers.Child`
  * method `get_GrowthProgress()`

**Timberborn.BehaviorSystem**

* type `Timberborn.BehaviorSystem.Behavior`
  * method `Decide(Timberborn.BehaviorSystem.BehaviorAgent)`
* type `Timberborn.BehaviorSystem.BehaviorAgent`
* type `Timberborn.BehaviorSystem.BehaviorManager`
* type `Timberborn.BehaviorSystem.Decision`
  * method `ReleaseNextTick()`
  * method `ReleaseNow()`
  * method `TransferNow(Timberborn.BehaviorSystem.Behavior, Timberborn.BehaviorSystem.Decision&)`
  * method `get_ShouldReleaseNow()`
* type `Timberborn.BehaviorSystem.RootBehavior`
  * method `.ctor()`

**Timberborn.BlockSystem**

* type `Timberborn.BlockSystem.BlockObject`
  * method `get_HasEntrance()`
  * method `get_IsFinished()`
  * method `get_PositionedEntrance()`
* type `Timberborn.BlockSystem.IFinishedStateListener`
* type `Timberborn.BlockSystem.PositionedEntrance`
  * method `get_Coordinates()`

**Timberborn.BlueprintSystem**

* type `Timberborn.BlueprintSystem.AssetRef`1`
  * method `get_Asset()`
* type `Timberborn.BlueprintSystem.Blueprint`
  * method `GetSpec<1>()`
* type `Timberborn.BlueprintSystem.ComponentSpec`
  * method `GetSpec<1>()`
  * method `get_Blueprint()`
* type `Timberborn.BlueprintSystem.ISpecService`
  * method `GetBlueprint(System.String)`

**Timberborn.Buildings**

* type `Timberborn.Buildings.BuildingSpec`
  * method `op_Inequality(Timberborn.Buildings.BuildingSpec, Timberborn.Buildings.BuildingSpec)`

**Timberborn.Characters**

* type `Timberborn.Characters.Character`
  * method `get_Age()`
  * method `get_Alive()`
  * method `get_FirstName()`
* type `Timberborn.Characters.CharacterInit`
  * method `.ctor(System.Int32, System.Single, Timberborn.Characters.Character, UnityEngine.Vector3, UnityEngine.Quaternion)`
* type `Timberborn.Characters.CharacterMaterialModifier`
  * method `SetTexture(System.Int32, UnityEngine.Texture)`

**Timberborn.Common**

* type `Timberborn.Common.IRandomNumberGenerator`
  * method `Range(System.Int32, System.Int32)`
* type `Timberborn.Common.ReadOnlyList`1`
  * method `GetEnumerator()`

**Timberborn.Coordinates**

* type `Timberborn.Coordinates.CoordinateSystem`
  * method `GridToWorldCentered(UnityEngine.Vector3Int)`

**Timberborn.CoreUI**

* type `Timberborn.CoreUI.VisualElementExtensions`
  * method `ToggleDisplayStyle(UnityEngine.UIElements.VisualElement, System.Boolean)`
* type `Timberborn.CoreUI.VisualElementLoader`
  * method `LoadVisualElement(System.String)`

**Timberborn.DwellingSystem**

* type `Timberborn.DwellingSystem.Dweller`
  * method `get_HasHome()`
  * method `get_Home()`
* type `Timberborn.DwellingSystem.Dwelling`
  * method `AssignDweller(Timberborn.DwellingSystem.Dweller)`
  * method `UnassignDweller(Timberborn.DwellingSystem.Dweller)`
  * method `get_AdultDwellers()`
  * method `get_HasFreeChildSlots()`
  * method `get_HasFreeSlots()`

**Timberborn.EntityPanelSystem**

* type `Timberborn.EntityPanelSystem.ClickableSubtitle`
  * method `Create(System.Action, System.String)`
  * method `CreateEmpty()`
* type `Timberborn.EntityPanelSystem.EntityPanelModule`
* type `Timberborn.EntityPanelSystem.EntityPanelModule+Builder`
  * method `.ctor()`
  * method `AddMiddleFragment(Timberborn.EntityPanelSystem.IEntityPanelFragment, System.Int32)`
  * method `Build()`
* type `Timberborn.EntityPanelSystem.IEntityBadge`
* type `Timberborn.EntityPanelSystem.IEntityPanelFragment`

**Timberborn.EntitySystem**

* type `Timberborn.EntitySystem.EntityComponent`
* type `Timberborn.EntitySystem.EntityService`
  * method `Instantiate(Timberborn.EntitySystem.EntitySetup+Builder)`
* type `Timberborn.EntitySystem.EntitySetup`
* type `Timberborn.EntitySystem.EntitySetup+Builder`
  * method `.ctor(Timberborn.BlueprintSystem.Blueprint)`
  * method `AddInitComponent(System.Object)`
* type `Timberborn.EntitySystem.IInitializableEntity`
* type `Timberborn.EntitySystem.IPostInitializableEntity`

**Timberborn.GameDistricts**

* type `Timberborn.GameDistricts.Citizen`
  * method `get_AssignedDistrict()`
  * method `get_HasAssignedDistrict()`
* type `Timberborn.GameDistricts.DistrictBuildingRegistry`
  * method `GetEnabledBuildingsInstant<1>()`
* type `Timberborn.GameDistricts.DistrictCenter`
  * method `get_DistrictName()`
  * method `get_DistrictPopulation()`
* type `Timberborn.GameDistricts.DistrictCenterRegistry`
  * method `get_FinishedDistrictCenters()`
* type `Timberborn.GameDistricts.DistrictContextService`
  * method `get_SelectedDistrict()`
* type `Timberborn.GameDistricts.DistrictPopulation`
  * method `get_Adults()`
  * method `get_Beavers()`
  * method `get_Children()`

**Timberborn.LifeSystem**

* type `Timberborn.LifeSystem.LifeProgressor`
  * method `get_LifeProgress()`
* type `Timberborn.LifeSystem.LifeService`
  * method `AdulthoodProgressToLifeProgress(System.Single)`
  * method `CalculateDayOfBirth(System.Single)`
  * method `ChildhoodProgressToLifeProgress(System.Single)`

**Timberborn.Localization**

* type `Timberborn.Localization.ILoc`
  * method `T(System.String)`
  * method `T<1>(System.String, !!0)`
  * method `T<3>(System.String, !!0, !!1, !!2)`

**Timberborn.MortalSystem**

* type `Timberborn.MortalSystem.Mortal`
  * method `get_Dead()`

**Timberborn.NeedBehaviorSystem**

* type `Timberborn.NeedBehaviorSystem.NeederRootBehavior`

**Timberborn.NeedSystem**

* type `Timberborn.NeedSystem.NeedManager`
  * method `GetNeedPoints(System.String)`
  * method `HasNeed(System.String)`
  * method `NeedIsInCriticalState(System.String)`

**Timberborn.ScienceSystem**

* type `Timberborn.ScienceSystem.BuildingUnlockingService`
  * method `UnlockIgnoringCost(Timberborn.Buildings.BuildingSpec)`
  * method `Unlocked(Timberborn.Buildings.BuildingSpec)`

**Timberborn.SelectionSystem**

* type `Timberborn.SelectionSystem.EntitySelectionService`
  * method `SelectAndFocusOn(Timberborn.BaseComponentSystem.BaseComponent)`

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
  * method `CreateNormalStatus(System.String, System.String)`
  * method `Deactivate()`
  * method `Toggle(System.Boolean)`

**Timberborn.TemplateInstantiation**

* type `Timberborn.TemplateInstantiation.TemplateInstantiator`
  * method `CacheInstance(Timberborn.BlueprintSystem.Blueprint)`
* type `Timberborn.TemplateInstantiation.TemplateModule`
* type `Timberborn.TemplateInstantiation.TemplateModule+Builder`
  * method `.ctor()`
  * method `AddDecorator<2>()`
  * method `Build()`

**Timberborn.TemplateSystem**

* type `Timberborn.TemplateSystem.TemplateNameMapper`
  * method `TryGetTemplate(System.String, Timberborn.TemplateSystem.TemplateSpec&)`
* type `Timberborn.TemplateSystem.TemplateService`
  * method `GetAll<1>()`
  * method `GetSingle<1>()`
* type `Timberborn.TemplateSystem.TemplateSpec`
  * method `get_TemplateName()`

**Timberborn.TickSystem**

* type `Timberborn.TickSystem.ITickableSingleton`
* type `Timberborn.TickSystem.TickableComponent`
  * method `.ctor()`

**Timberborn.TimeSystem**

* type `Timberborn.TimeSystem.DaytimeStartEvent`
* type `Timberborn.TimeSystem.IDayNightCycle`
  * method `BoundsInHours(Timberborn.TimeSystem.TimeOfDay)`
  * method `get_DayNumber()`
  * method `get_HoursPassedToday()`
* type `Timberborn.TimeSystem.TimeOfDay`

**Timberborn.UILayoutSystem**

* type `Timberborn.UILayoutSystem.ShowPrimaryUIEvent`
* type `Timberborn.UILayoutSystem.UILayout`
  * method `AddTopLeft(UnityEngine.UIElements.VisualElement, System.Int32)`

**Timberborn.Wandering**

* type `Timberborn.Wandering.WanderRootBehavior`

**Timberborn.WorkSystem**

* type `Timberborn.WorkSystem.Worker`
  * method `get_Employed()`
* type `Timberborn.WorkSystem.WorkerRootBehavior`
* type `Timberborn.WorkSystem.WorkerTypeChangedEventArgs`
* type `Timberborn.WorkSystem.WorkingHoursManager`
  * method `get_EndHours()`
* type `Timberborn.WorkSystem.Workplace`
  * method `get_DesiredWorkers()`
* type `Timberborn.WorkSystem.WorkplaceWorkerType`
  * method `SetWorkerType(System.String)`
  * method `add_WorkerTypeChanged(System.EventHandler`1<Timberborn.WorkSystem.WorkerTypeChangedEventArgs>)`
  * method `get_WorkerType()`

**UnityEngine.CoreModule**

* type `UnityEngine.Debug`
  * method `Log(System.Object)`
  * method `LogError(System.Object)`
  * method `LogWarning(System.Object)`
* type `UnityEngine.GameObject`
  * method `SetActive(System.Boolean)`
* type `UnityEngine.Mathf`
  * method `Max(System.Int32, System.Int32)`
* type `UnityEngine.Object`
  * method `get_name()`
  * method `op_Implicit(UnityEngine.Object)`
* type `UnityEngine.Quaternion`
  * method `get_identity()`
* type `UnityEngine.Shader`
  * method `PropertyToID(System.String)`
* type `UnityEngine.Sprite`
* type `UnityEngine.Texture`
* type `UnityEngine.Texture2D`
* type `UnityEngine.Time`
  * method `get_unscaledTime()`
* type `UnityEngine.Transform`
  * method `get_position()`
* type `UnityEngine.Vector3`
* type `UnityEngine.Vector3Int`

**UnityEngine.UIElementsModule**

* type `UnityEngine.UIElements.Button`
* type `UnityEngine.UIElements.DisplayStyle`
* type `UnityEngine.UIElements.IStyle`
  * method `set_display(UnityEngine.UIElements.StyleEnum`1<UnityEngine.UIElements.DisplayStyle>)`
* type `UnityEngine.UIElements.Label`
* type `UnityEngine.UIElements.StyleEnum`1`
  * method `op_Implicit(!0)`
* type `UnityEngine.UIElements.TextElement`
  * method `set_text(System.String)`
* type `UnityEngine.UIElements.UQueryExtensions`
  * method `Q<1>(UnityEngine.UIElements.VisualElement, System.String, System.String)`
* type `UnityEngine.UIElements.VisualElement`
  * method `.ctor()`
  * method `get_style()`
  * method `set_name(System.String)`

<!-- api:end -->
