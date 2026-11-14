# Pandaborn.Ringtails - the second people

DESIGN.md Pillar 1, "The gate". Ported from the go/no-go prototype `proto/ringtails` (results:
`docs/tech/two-peoples.md` section 17). **Status: not wired yet** — not in `Pandaborn.Code.sln` or `modules.txt` until
the spec records in `proposed/RingtailSpecs.cs` are added to `Pandaborn.Specs` by its owner. Compile check meanwhile:
`dotnet build -c Release -p:RingtailsProposedSpecs=true -p:ModOut=<scratch>`.

**What it does.** Ringtails are a hidden second adult/kit template pair (in no template collection, so the vanilla
`BeaverFactory` still sees exactly one adult) with their own worker type `PandabornRingtail` (ignores working hours).
They staff only buildings typed for them (`WorkplaceSpec.DefaultWorkerType: PandabornRingtail`,
`DisallowOtherWorkerTypes: true`). Each day they rest from dawn until the bell — the end of the Inkpaw working hours
(the working-hours slider, read live), clamped to 4–16 h after dawn — sleeping at home first, then eating, drinking and
taking leisure; then they work until the next dawn.

| Class | Job |
|---|---|
| `RingtailService` | Switch (a game is a Ringtails game when the faction adult template carries `PandabornRingtailsSpec`), load-time compatibility check, factory (adult, kit, grown kit), save registration |
| `RingtailRestRootBehavior` | The rest window: a root behaviour inserted just above `WorkerRootBehavior`; runs the game's `SleepNeedBehavior`, `NeederRootBehavior`, `WanderRootBehavior` |
| `RingtailCoat` | Red panda coat from `PandabornRingtailSpec.Textures` in `PostInitializeEntity` |
| `RingtailGrowth` | A kit becomes a Ringtail adult at growth 0.995 (vanilla would make an Inkpaw at 1.0) |
| `LoftHousingRule` | Lofts belong to Ringtails: swap an Inkpaw out of a loft for a Ringtail; a homeless Ringtail takes a loft bed |

**Data it needs** (main mod / catalogue): `PandabornRingtailsSpec` on the Inkpaw adult template;
`RingtailAdult|RingtailChild.Inkpaws` templates with `PandabornRingtailSpec` (generator: `proto/ringtails/tools/derive.py`;
walking speed equal to Inkpaws, `BaseSlowedSpeed = BaseWalkingSpeed` so loads never slow them, lifting 14); the
worker type blueprint; Ringtail workplaces with `PandabornRingtailWorkplaceSpec`; lofts with `PandabornLoftSpec`; the
alias `BackwardCompatibleTemplateNames: [RingtailAdult.Inkpaws]` (and the kit) on the Inkpaw templates, permanently;
worker outfits for the Ringtail worker type.

**Saved**: nothing of its own. Ringtails are ordinary entities saved under their template name; the game reloads them
because `RingtailService` registers the hidden templates in `TemplateNameMapper`.

**Fails safely** (each checked once at load, before any Ringtail exists):

| Private member | If missing |
|---|---|
| `TemplateNameMapper._templates` | Feature off. Saved Ringtails load as Inkpaws (alias) with name, age, needs, home; their Ringtail jobs drop. One notice. Verified in game (`rt-fallback1`) |
| `BehaviorManager._rootBehaviors` | No new Ringtails; existing Ringtails work round the clock (vanilla critical sleep keeps them alive). One notice |

Implicit (public) dependencies: the behaviour order (Worker root before Needer root); vanilla growth at 1.0;
`BeaverTextureSetter` in `InitializeEntity`. If the module itself is off (API check), nothing registers the hidden
templates, so saved Ringtails load as Inkpaws through the alias, exactly as in the first row: the save stays loadable
and keeps every colonist.

**Open item for the owner of Bell**: `Pandaborn.Bell` locks the day length at dawn; the rest window here reads the
slider live. Ideally both read the same value (`BellService.Current` locked hours when Bell is on).

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
