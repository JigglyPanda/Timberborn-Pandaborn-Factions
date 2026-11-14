# Pandaborn.Festival - the Lantern Festival

DESIGN.md Pillar 5; full design, player timeline and test results in `docs/tech/events.md`. **Status: built and tested
through the events dev mod (`proto/events`); not yet in `Pandaborn.Code.sln` or `modules.txt`.** It does nothing until the
catalogue carries its data (requests in `docs/tech/events.md`); wire it in together with that data.

**What it does.** A Festival Square's panel shows what its district has in its ordinary stores towards a festival
(paper lanterns, the cooked dishes with 20 or more each, fireworks), a Call button, an auto-call toggle, the cycle of the
next allowed festival and the village's Tradition. Calling takes the goods out of the district's stores at once
(`Inventory.TakeConsumed`, unreserved stock only, the most plentiful dishes first) and the festival runs from the next
dawn to the dawn after:

* `FestivalGoer`, a root behaviour on every colonist template with `PandabornFestivalGoerSpec`, sits just above
  `WorkerRootBehavior` (above `NeederRootBehavior` for the young). On the festival day nobody works except crews of the
  spec's `KeepWorkingTemplates` (pumps and lifts); by day the game's own need loop runs first, then colonists celebrate
  at a random spot near the district's square (the game's `GetRandomDestinationInDistrict` around the square); from
  `ShowStartHours` to `ShowEndHours` everyone goes to the square first. Carrying, critical needs, death and stranding
  stay above it. A Ringtail's day rest (inserted in `InitializeEntity`) stays above it too, because the festival inserts
  in `PostInitializeEntity`: Ringtails sleep through the morning, then join.
* The show: rising lanterns at dusk and, for a Grand Festival (20 fireworks in store as well), bursts in the evening,
  drawn with the game's own firework entities (`FestivalFireworks`), from each finished square. Computed from the clock,
  so a reload never replays them. The square's model may carry `#FestivalLights` (shown from the call to the end),
  `#LanternRise` (a particle system played instead of a comet) and `#FireworkMount` (launch point).
* Rewards: the festive need (`FestiveNeedId`) is set to its maximum for a colonist when it first reaches the square and
  for everyone else when the festival ends; `GrandNeedId` too after a Grand Festival. Tradition rises by one.
* `TraditionToolLocker` (an `IToolLocker`, the game's own toolbar lock) keeps decorations with
  `PandabornTraditionSpec { Level }` locked until Tradition reaches their level; clicking one explains it. It only locks
  tools science does not lock (the game allows one locker per tool), so such decorations need `ScienceCost` 0.

**Rules.** At most one festival per cycle (the cycle of its day). Manual calls are allowed in any weather; the auto-call
never fires during a drought or badtide or on the day before one. Called at any hour, it begins at the next dawn.

**Data it needs** (catalogue): `PandabornFestivalSpec` (all numbers and lists) and `PandabornFestivalGoerSpec` on the Inkpaw
adult template; `PandabornFestivalGoerSpec` on the Inkpaw child and the Ringtail adult and child templates;
`PandabornFestivalSquareSpec` on the Festival Square; `PandabornTraditionSpec` on the Tradition decorations.

**Saved**: `PandabornStore` entry `Festival` v1: `phase` (None/Called/Running), `day`, `grand`, `last` (cycle),
`tradition`, `auto`, `count`. Nothing per entity: need points are the game's own (the festive need decays by itself).

**Fails safely.**
* Module off (or its game API changed): no panel, no festival, the square is its vanilla basis (a village square
  attraction), decorations are simply buildable, the store entry is carried unchanged. A save made mid-festival loads
  with everyone working as usual; when the module is back, a festival whose day has passed ends at once on load with its
  rewards (the goods were spent), one called for today starts.
* `BehaviorManager._rootBehaviors` (private) gone, or `simulate-missing-member: Festival.RootBehaviors`: no day off;
  the evening show, festive spirit and Tradition remain, and the panel says so.
* `Timberborn.FireworkSystem.Firework.Launch` (public method of an internal type, reached by reflection) gone, or
  `simulate-missing-member: Festival.Fireworks`: no lanterns or fireworks in the sky; everything else runs.
* Interface pieces sit behind `SafeUi`.

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
  * method `To<1>()`
  * method `ToProvider(System.Func`1<!0>)`
  * method `ToProvider<1>()`
* type `Bindito.Core.IContainer`
  * method `GetInstance<1>()`
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
  * method `GetComponent<1>()`
  * method `get_AllComponents()`
  * method `get_GameObject()`
  * method `get_Transform()`
  * method `op_Implicit(Timberborn.BaseComponentSystem.BaseComponent)`
* type `Timberborn.BaseComponentSystem.IAwakableComponent`

**Timberborn.Beavers**

* type `Timberborn.Beavers.AdultSpec`

**Timberborn.BehaviorSystem**

* type `Timberborn.BehaviorSystem.Behavior`
  * method `Decide(Timberborn.BehaviorSystem.BehaviorAgent)`
* type `Timberborn.BehaviorSystem.BehaviorAgent`
* type `Timberborn.BehaviorSystem.BehaviorManager`
* type `Timberborn.BehaviorSystem.Decision`
  * method `ReleaseNextTick()`
  * method `ReleaseNow()`
  * method `ReleaseWhenFinished(Timberborn.BehaviorSystem.IExecutor)`
  * method `ReturnWhenFinished(Timberborn.BehaviorSystem.IExecutor)`
  * method `TransferNow(Timberborn.BehaviorSystem.Behavior, Timberborn.BehaviorSystem.Decision&)`
  * method `get_ShouldReleaseNow()`
* type `Timberborn.BehaviorSystem.ExecutorStatus`
* type `Timberborn.BehaviorSystem.IExecutor`
* type `Timberborn.BehaviorSystem.RootBehavior`
  * method `.ctor()`
* type `Timberborn.BehaviorSystem.WaitExecutor`
  * method `LaunchForSpecifiedTime(System.Single)`

**Timberborn.BlockObjectTools**

* type `Timberborn.BlockObjectTools.BlockObjectTool`
  * method `get_Template()`

**Timberborn.BlockSystem**

* type `Timberborn.BlockSystem.BlockObjectCenter`
  * method `get_WorldCenterGrounded()`
* type `Timberborn.BlockSystem.IFinishedStateListener`
* type `Timberborn.BlockSystem.PlaceableBlockObjectSpec`
  * method `op_Equality(Timberborn.BlockSystem.PlaceableBlockObjectSpec, Timberborn.BlockSystem.PlaceableBlockObjectSpec)`

**Timberborn.BlueprintSystem**

* type `Timberborn.BlueprintSystem.Blueprint`
  * method `GetSpec<1>()`
* type `Timberborn.BlueprintSystem.ComponentSpec`
  * method `GetSpec<1>()`
  * method `get_Blueprint()`

**Timberborn.Buildings**

* type `Timberborn.Buildings.BuildingSpec`
  * method `op_Equality(Timberborn.Buildings.BuildingSpec, Timberborn.Buildings.BuildingSpec)`

**Timberborn.Common**

* type `Timberborn.Common.IRandomNumberGenerator`
  * method `Range(System.Single, System.Single)`
* type `Timberborn.Common.ReadOnlyHashSet`1`
  * method `GetEnumerator()`
* type `Timberborn.Common.ReadOnlyList`1`

**Timberborn.CoreUI**

* type `Timberborn.CoreUI.DialogBox`
* type `Timberborn.CoreUI.DialogBoxShower`
  * method `Create()`
* type `Timberborn.CoreUI.DialogBoxShower+Builder`
  * method `SetConfirmButton(System.Action)`
  * method `SetMessage(System.String)`
  * method `Show()`
* type `Timberborn.CoreUI.VisualElementExtensions`
  * method `ToggleDisplayStyle(UnityEngine.UIElements.VisualElement, System.Boolean)`
* type `Timberborn.CoreUI.VisualElementLoader`
  * method `LoadVisualElement(System.String)`

**Timberborn.Effects**

* type `Timberborn.Effects.InstantEffect`
  * method `.ctor(System.String, System.Single, System.Int32)`

**Timberborn.EntityPanelSystem**

* type `Timberborn.EntityPanelSystem.EntityPanelModule`
* type `Timberborn.EntityPanelSystem.EntityPanelModule+Builder`
  * method `.ctor()`
  * method `AddBottomFragment(Timberborn.EntityPanelSystem.IEntityPanelFragment, System.Int32)`
  * method `Build()`
* type `Timberborn.EntityPanelSystem.IEntityPanelFragment`

**Timberborn.EntitySystem**

* type `Timberborn.EntitySystem.EntityComponent`
* type `Timberborn.EntitySystem.EntityService`
  * method `Delete(Timberborn.BaseComponentSystem.BaseComponent)`
  * method `Instantiate(Timberborn.BlueprintSystem.Blueprint)`
* type `Timberborn.EntitySystem.IDeletableEntity`
* type `Timberborn.EntitySystem.IPostInitializableEntity`
* type `Timberborn.EntitySystem.LabeledEntitySpec`
  * method `get_DisplayNameLocKey()`

**Timberborn.FireworkSystem**

* type `Timberborn.FireworkSystem.FireworkLimits`
  * field `MaxFlightDistance`
  * field `MinFlightDistance`
* type `Timberborn.FireworkSystem.FireworkSpec`
* type `Timberborn.FireworkSystem.FireworkSpecService`
  * method `GetFireworkSpec(System.String)`
  * method `HasSpec(System.String)`

**Timberborn.GameCycleSystem**

* type `Timberborn.GameCycleSystem.GameCycleService`
  * method `get_Cycle()`

**Timberborn.GameDistricts**

* type `Timberborn.GameDistricts.Citizen`
  * method `get_AssignedDistrict()`
* type `Timberborn.GameDistricts.DistrictBuilding`
  * method `get_District()`
* type `Timberborn.GameDistricts.DistrictCenter`
  * method `get_District()`

**Timberborn.Goods**

* type `Timberborn.Goods.GoodAmount`
  * method `.ctor(System.String, System.Int32)`
  * method `get_Amount()`
  * method `get_GoodId()`
* type `Timberborn.Goods.GoodSpec`
  * method `get_PluralDisplayName()`
  * method `op_Inequality(Timberborn.Goods.GoodSpec, Timberborn.Goods.GoodSpec)`
* type `Timberborn.Goods.IGoodService`
  * method `GetGoodOrNull(System.String)`

**Timberborn.InputSystem**

* type `Timberborn.InputSystem.InputService`
  * method `IsKeyHeld(System.String)`

**Timberborn.InventorySystem**

* type `Timberborn.InventorySystem.DistrictInventoryRegistry`
  * method `ActiveInventoriesWithStock(System.String)`
* type `Timberborn.InventorySystem.Inventory`
  * method `TakeConsumed(Timberborn.Goods.GoodAmount)`
  * method `UnreservedAmountInStock(System.String)`

**Timberborn.Localization**

* type `Timberborn.Localization.ILoc`
  * method `T(System.String)`
  * method `T<1>(System.String, !!0)`
  * method `T<2>(System.String, !!0, !!1)`
  * method `T<3>(System.String, !!0, !!1, !!2)`

**Timberborn.LocalizationSerialization**

* type `Timberborn.LocalizationSerialization.LocalizedText`
  * method `get_Value()`

**Timberborn.Navigation**

* type `Timberborn.Navigation.District`
* type `Timberborn.Navigation.IDistrictService`
  * method `GetRandomDestinationInDistrict(Timberborn.Navigation.District, UnityEngine.Vector3)`

**Timberborn.NeedBehaviorSystem**

* type `Timberborn.NeedBehaviorSystem.NeederRootBehavior`

**Timberborn.NeedSystem**

* type `Timberborn.NeedSystem.NeedManager`
  * method `ApplyEffect(Timberborn.Effects.InstantEffect&)`
  * method `GetNeedPoints(System.String)`
  * method `HasNeed(System.String)`
  * method `NeedPointsToMax(System.String)`

**Timberborn.ScienceSystem**

* type `Timberborn.ScienceSystem.BuildingUnlockingService`
  * method `Unlocked(Timberborn.Buildings.BuildingSpec)`

**Timberborn.SingletonSystem**

* type `Timberborn.SingletonSystem.EventBus`
  * method `Register(System.Object)`
* type `Timberborn.SingletonSystem.ILoadableSingleton`
* type `Timberborn.SingletonSystem.IPostLoadableSingleton`
* type `Timberborn.SingletonSystem.OnEventAttribute`
  * method `.ctor()`

**Timberborn.TemplateInstantiation**

* type `Timberborn.TemplateInstantiation.TemplateModule`
* type `Timberborn.TemplateInstantiation.TemplateModule+Builder`
  * method `.ctor()`
  * method `AddDecorator<2>()`
  * method `Build()`

**Timberborn.TemplateSystem**

* type `Timberborn.TemplateSystem.TemplateService`
  * method `GetAll<1>()`
* type `Timberborn.TemplateSystem.TemplateSpec`
  * method `get_TemplateName()`
  * method `op_Inequality(Timberborn.TemplateSystem.TemplateSpec, Timberborn.TemplateSystem.TemplateSpec)`

**Timberborn.TickSystem**

* type `Timberborn.TickSystem.ITickableSingleton`

**Timberborn.TimeSystem**

* type `Timberborn.TimeSystem.DaytimeStartEvent`
* type `Timberborn.TimeSystem.IDayNightCycle`
  * method `get_DayNumber()`
  * method `get_HoursPassedToday()`
  * method `get_PartialDayNumber()`

**Timberborn.ToolSystem**

* type `Timberborn.ToolSystem.ITool`
* type `Timberborn.ToolSystem.IToolLocker`
* type `Timberborn.ToolSystem.ToolUnlockingService`
  * method `IsLocked(Timberborn.ToolSystem.ITool)`
  * method `Unlock(Timberborn.ToolSystem.ITool)`

**Timberborn.WalkingSystem**

* type `Timberborn.WalkingSystem.WalkToPositionExecutor`
  * method `Launch(UnityEngine.Vector3)`

**Timberborn.Wandering**

* type `Timberborn.Wandering.WanderRootBehavior`

**Timberborn.WeatherSystem**

* type `Timberborn.WeatherSystem.WeatherService`
  * method `NextDayIsHazardousWeather()`
  * method `get_IsHazardousWeather()`

**Timberborn.WorkSystem**

* type `Timberborn.WorkSystem.Worker`
  * method `get_Employed()`
  * method `get_Workplace()`
* type `Timberborn.WorkSystem.WorkerRootBehavior`
* type `Timberborn.WorkSystem.Workplace`

**UnityEngine.CoreModule**

* type `UnityEngine.Component`
  * method `GetComponentInChildren<1>(System.Boolean)`
  * method `get_gameObject()`
* type `UnityEngine.Debug`
  * method `Log(System.Object)`
  * method `LogError(System.Object)`
  * method `LogWarning(System.Object)`
* type `UnityEngine.GameObject`
  * method `GetComponentsInChildren<1>(System.Boolean)`
  * method `SetActive(System.Boolean)`
* type `UnityEngine.Mathf`
  * method `CeilToInt(System.Single)`
  * method `Clamp(System.Single, System.Single, System.Single)`
  * method `Max(System.Single, System.Single)`
* type `UnityEngine.Object`
  * method `get_name()`
  * method `op_Implicit(UnityEngine.Object)`
* type `UnityEngine.Quaternion`
  * method `Euler(System.Single, System.Single, System.Single)`
* type `UnityEngine.Time`
  * method `get_unscaledTime()`
* type `UnityEngine.Transform`
  * method `get_position()`
* type `UnityEngine.Vector3`
  * method `.ctor(System.Single, System.Single, System.Single)`
  * method `get_up()`
  * method `op_Addition(UnityEngine.Vector3, UnityEngine.Vector3)`
  * method `op_Multiply(UnityEngine.Vector3, System.Single)`

**UnityEngine.ParticleSystemModule**

* type `UnityEngine.ParticleSystem`
  * method `Play()`

**UnityEngine.UIElementsModule**

* type `UnityEngine.UIElements.BaseField`1`
  * method `SetValueWithoutNotify(!0)`
* type `UnityEngine.UIElements.Button`
  * method `add_clicked(System.Action)`
* type `UnityEngine.UIElements.ChangeEvent`1`
  * method `get_newValue()`
* type `UnityEngine.UIElements.EventCallback`1`
  * method `.ctor(System.Object, System.IntPtr)`
* type `UnityEngine.UIElements.INotifyValueChangedExtensions`
  * method `RegisterValueChangedCallback<1>(UnityEngine.UIElements.INotifyValueChanged`1<!!0>, UnityEngine.UIElements.EventCallback`1<UnityEngine.UIElements.ChangeEvent`1<!!0>>)`
* type `UnityEngine.UIElements.INotifyValueChanged`1`
* type `UnityEngine.UIElements.IStyle`
  * method `set_whiteSpace(UnityEngine.UIElements.StyleEnum`1<UnityEngine.UIElements.WhiteSpace>)`
* type `UnityEngine.UIElements.Label`
  * method `.ctor()`
* type `UnityEngine.UIElements.StyleEnum`1`
  * method `op_Implicit(!0)`
* type `UnityEngine.UIElements.TextElement`
  * method `get_text()`
  * method `set_text(System.String)`
* type `UnityEngine.UIElements.Toggle`
  * method `.ctor(System.String)`
* type `UnityEngine.UIElements.UQueryExtensions`
  * method `Q<1>(UnityEngine.UIElements.VisualElement, System.String, System.String)`
* type `UnityEngine.UIElements.VisualElement`
  * method `.ctor()`
  * method `Add(UnityEngine.UIElements.VisualElement)`
  * method `AddToClassList(System.String)`
  * method `SetEnabled(System.Boolean)`
  * method `get_style()`
  * method `set_name(System.String)`
* type `UnityEngine.UIElements.WhiteSpace`

<!-- api:end -->
