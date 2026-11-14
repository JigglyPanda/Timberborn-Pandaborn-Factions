# Pandaborn.Water - flumes, gates, current-driven machines, dew

What it does, per spec (all specs in `Pandaborn.Specs/WaterSpecs.cs`, only on `.Inkpaws` templates):

* `PandabornFlumeSegmentSpec { FlowCells }` -> `FlumeSegment` (+ `FlumeMonitor`). One tick after the piece is finished
  (`FlumeService` queue) it adds `IWaterService` direction limiters on its flow cells (water moves only along the piece's
  arrow) and lifts the piece's vanilla inert obstacle with the public `WaterObstacle.RemoveFromWaterService()`. On demolish
  it removes the limiters; the vanilla obstacle's own exit is then a no-op. Limiters are not saved by the game and are
  re-added on every load. `FlumeMonitor` (every 30 ticks) shows one status: blocked, misaligned, intake dry, end dry.
  Loading re-adds the inert obstacle (vanilla's finished-state listener). The segment lifts it again in
  `PostLoadEntity`, so the add and the lift reach the water simulation in the same batch before its first tick and the
  water standing in the line is kept (run `water-w4d`; lifting a tick later cut up to one block of water out of each cell
  and let the rest spill sideways, runs `water-w4-1155`, `water-w4c`). As a safety net, with a
  `PandabornEntityStateSpec` on the piece the depth and contamination of each flow cell are saved (entry
  `Water.Flume|1|t=<day>;<depth>,<contamination>;...`); three ticks after loading, whatever is missing (at most one
  block per cell) is put back, only when the entry's game time matches the loaded game.
* `PandabornSolidCellsSpec { Cells }` -> `SolidCells`: full obstacles at extra cells (sealed Flume Drop body, caps).
* `PandabornFlumeGateSpec { DefaultFlow, MaxFlow, FlowStep, ContaminationShutoff }` -> `FlumeGate`: an inflow limit on
  the gate cell (m3/s), and the badwater guard: above `ContaminationShutoff` behind the gate it closes (re-adds the inert
  obstacle) and shows a status; it reopens after six clean checks below half that. Settings live in the per-entity
  carrier (`PandabornEntityStateSpec`, entry `Water|1|flow=0.30;guard=1`).
* `PandabornCurrentDrivenSpec` -> `CurrentDriven`: reads the vanilla water wheel's rotation and its mechanical node's
  efficiency, shows "needs a current" when finished and idle.
* `PandabornDewLimiterSpec { TemperateEfficiency, DroughtEfficiency }` -> `DewLimiter`, an `IManufactoryLimiter`.
* `PandabornPaddySpoutSpec`, `PandabornTreadwheelSpec`, `PandabornCisternTapSpec`: markers for the info panel lines.
* Panels (`WaterPanels.cs`, inside `SafeUi`): the Flume Gate panel reuses the vanilla floodgate fragment (flow slider in
  m3/s, badwater toggle, state line); one info line for Scoop Wheel, Trip-Hammer, Paddy Spout, Treadwheel, Cistern Tap.
  Text: `mod/Localizations/enUS_PandabornWater.csv`.

**Data alone behaves like vanilla** (module off, forced off, or its API check failed):

| Piece | With the module off |
|---|---|
| Flume, covered Flume, Flume Gate, Flume Drop, Flume Bridge | a solid block over its flow cells (vanilla `WaterObstacleSpec` + `FinishableWaterObstacleSpec`): holds no water, floods nothing |
| Flume Bridge span (over another flume) | an empty trestle; its neighbours are solid, so no water reaches it |
| Flume Corner | posts and one open cell between solid neighbours |
| Paddy Spout | the vanilla fill valve it is built on |
| Scoop Wheel, Treadwheel, Water Trip-Hammer | the vanilla water wheel / power wheel + pump / manufactory, without the info line and status |
| Dew Collector | makes water at full rate in every weather |
| Cistern Tap | the vanilla discharge building with its worker |

A save made with the module on loads with it off (the specs assembly is always loaded; components that are not created
just have nothing to save) and nothing floods; the gate's settings stay in the carrier and come back with the module.

**Private members**: none. Everything above is public game API (see the list below).

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
  * method `EnableComponent()`
  * method `GetComponent<1>()`
  * method `op_Implicit(Timberborn.BaseComponentSystem.BaseComponent)`
* type `Timberborn.BaseComponentSystem.IAwakableComponent`

**Timberborn.BlockSystem**

* type `Timberborn.BlockSystem.BlockObject`
  * method `TransformCoordinates(UnityEngine.Vector3Int)`
  * method `get_Coordinates()`
  * method `get_IsFinished()`
  * method `get_Orientation()`
* type `Timberborn.BlockSystem.IBlockService`
  * method `Contains(UnityEngine.Vector3Int)`
  * method `GetObjectsAt(UnityEngine.Vector3Int)`
* type `Timberborn.BlockSystem.IFinishedStateListener`

**Timberborn.Common**

* type `Timberborn.Common.ReadOnlyList`1`
  * method `GetEnumerator()`

**Timberborn.Coordinates**

* type `Timberborn.Coordinates.Orientation`

**Timberborn.CoreUI**

* type `Timberborn.CoreUI.VisualElementExtensions`
  * method `ToggleDisplayStyle(UnityEngine.UIElements.VisualElement, System.Boolean)`
* type `Timberborn.CoreUI.VisualElementLoader`
  * method `LoadVisualElement(System.String)`

**Timberborn.EntityPanelSystem**

* type `Timberborn.EntityPanelSystem.EntityPanelModule`
* type `Timberborn.EntityPanelSystem.EntityPanelModule+Builder`
  * method `.ctor()`
  * method `AddMiddleFragment(Timberborn.EntityPanelSystem.IEntityPanelFragment, System.Int32)`
  * method `Build()`
* type `Timberborn.EntityPanelSystem.IEntityPanelFragment`

**Timberborn.EntitySystem**

* type `Timberborn.EntitySystem.IInitializableEntity`
* type `Timberborn.EntitySystem.IPostLoadableEntity`

**Timberborn.Goods**

* type `Timberborn.Goods.GoodAmountSpec`
  * method `get_Amount()`

**Timberborn.HazardousWeatherSystem**

* type `Timberborn.HazardousWeatherSystem.DroughtWeather`
* type `Timberborn.HazardousWeatherSystem.HazardousWeatherService`
  * method `get_CurrentCycleHazardousWeather()`
* type `Timberborn.HazardousWeatherSystem.IHazardousWeather`

**Timberborn.Localization**

* type `Timberborn.Localization.ILoc`
  * method `T(System.String)`
  * method `T<1>(System.String, !!0)`
  * method `T<2>(System.String, !!0, !!1)`
  * method `T<3>(System.String, !!0, !!1, !!2)`

**Timberborn.MechanicalSystem**

* type `Timberborn.MechanicalSystem.MechanicalGraph`
* type `Timberborn.MechanicalSystem.MechanicalNode`
  * method `get_Graph()`
  * method `get_PowerEfficiency()`
* type `Timberborn.MechanicalSystem.MechanicalNodeSpec`
  * method `get_PowerInput()`
  * method `get_PowerOutput()`
  * method `op_Inequality(Timberborn.MechanicalSystem.MechanicalNodeSpec, Timberborn.MechanicalSystem.MechanicalNodeSpec)`

**Timberborn.PowerGeneration**

* type `Timberborn.PowerGeneration.WaterPoweredGenerator`
  * method `get_GeneratorRotation()`

**Timberborn.StatusSystem**

* type `Timberborn.StatusSystem.StatusSubject`
  * method `RegisterStatus(Timberborn.StatusSystem.StatusToggle)`
* type `Timberborn.StatusSystem.StatusToggle`
  * method `CreateNormalStatusWithAlertAndFloatingIcon(System.String, System.String, System.String, System.Single)`
  * method `CreateNormalStatusWithFloatingIcon(System.String, System.String, System.Single)`
  * method `Deactivate()`
  * method `Toggle(System.Boolean)`
  * method `get_IsActive()`

**Timberborn.TemplateInstantiation**

* type `Timberborn.TemplateInstantiation.TemplateModule`
* type `Timberborn.TemplateInstantiation.TemplateModule+Builder`
  * method `.ctor()`
  * method `AddDecorator<2>()`
  * method `Build()`

**Timberborn.TickSystem**

* type `Timberborn.TickSystem.ITickableSingleton`
* type `Timberborn.TickSystem.TickableComponent`
  * method `.ctor()`

**Timberborn.TimeSystem**

* type `Timberborn.TimeSystem.IDayNightCycle`
  * method `get_PartialDayNumber()`

**Timberborn.WaterBuildings**

* type `Timberborn.WaterBuildings.FillValve`
  * method `get_ActualHeight()`
  * method `get_MinTargetHeight()`
  * method `get_TargetDepth()`
* type `Timberborn.WaterBuildings.ThrottlingValve`
* type `Timberborn.WaterBuildings.WaterMover`
  * method `get_CanMoveWater()`
  * method `get_EffectiveFlowRate()`

**Timberborn.WaterObjects**

* type `Timberborn.WaterObjects.WaterObstacle`
  * method `AddToWaterService(System.Single)`
  * method `RemoveFromWaterService()`

**Timberborn.WaterSystem**

* type `Timberborn.WaterSystem.FlowDirection`
* type `Timberborn.WaterSystem.FlowDirectionExtensions`
  * method `ToFlowDirection(Timberborn.Coordinates.Orientation)`
* type `Timberborn.WaterSystem.IThreadSafeWaterMap`
  * method `ColumnContamination(UnityEngine.Vector3Int)`
  * method `TryGetColumnFloor(UnityEngine.Vector3Int, System.Int32&)`
  * method `WaterDepth(UnityEngine.Vector3Int)`
  * method `WaterHeightOrFloor(UnityEngine.Vector3Int)`
* type `Timberborn.WaterSystem.IWaterService`
  * method `AddCleanWater(UnityEngine.Vector3Int, System.Single)`
  * method `AddContaminatedWater(UnityEngine.Vector3Int, System.Single)`
  * method `AddDirectionLimiter(UnityEngine.Vector3Int, Timberborn.WaterSystem.FlowDirection)`
  * method `AddFullObstacle(UnityEngine.Vector3Int)`
  * method `RemoveDirectionLimiter(UnityEngine.Vector3Int)`
  * method `RemoveFullObstacle(UnityEngine.Vector3Int)`
  * method `RemoveInflowLimit(UnityEngine.Vector3Int)`
  * method `SetInflowLimit(UnityEngine.Vector3Int, System.Single)`

**Timberborn.WeatherSystem**

* type `Timberborn.WeatherSystem.WeatherService`
  * method `get_IsHazardousWeather()`

**Timberborn.WorkSystem**

* type `Timberborn.WorkSystem.Workplace`
  * method `get_NumberOfAssignedWorkers()`

**Timberborn.Workshops**

* type `Timberborn.Workshops.IManufactoryLimiter`
* type `Timberborn.Workshops.Manufactory`
  * method `get_CurrentRecipe()`
* type `Timberborn.Workshops.RecipeSpec`
  * method `get_CycleDurationInHours()`
  * method `get_Ingredients()`
  * method `op_Equality(Timberborn.Workshops.RecipeSpec, Timberborn.Workshops.RecipeSpec)`

**UnityEngine.CoreModule**

* type `UnityEngine.Debug`
  * method `LogWarning(System.Object)`
* type `UnityEngine.Mathf`
  * method `Abs(System.Int32)`
  * method `Abs(System.Single)`
  * method `Clamp(System.Single, System.Single, System.Single)`
  * method `Clamp01(System.Single)`
  * method `Max(System.Single, System.Single)`
  * method `Round(System.Single)`
  * method `RoundToInt(System.Single)`
* type `UnityEngine.Vector3Int`
  * method `.ctor(System.Int32, System.Int32, System.Int32)`
  * method `get_z()`
  * method `get_zero()`
  * method `op_Addition(UnityEngine.Vector3Int, UnityEngine.Vector3Int)`
  * method `op_Equality(UnityEngine.Vector3Int, UnityEngine.Vector3Int)`
  * method `op_Inequality(UnityEngine.Vector3Int, UnityEngine.Vector3Int)`
  * method `op_Subtraction(UnityEngine.Vector3Int, UnityEngine.Vector3Int)`

**UnityEngine.UIElementsModule**

* type `UnityEngine.UIElements.BaseBoolField`
  * method `set_text(System.String)`
* type `UnityEngine.UIElements.BaseField`1`
  * method `SetValueWithoutNotify(!0)`
* type `UnityEngine.UIElements.BaseSlider`1`
  * method `set_highValue(!0)`
  * method `set_lowValue(!0)`
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
* type `UnityEngine.UIElements.Slider`
* type `UnityEngine.UIElements.StyleEnum`1`
  * method `op_Implicit(!0)`
* type `UnityEngine.UIElements.TextElement`
  * method `get_text()`
  * method `set_text(System.String)`
* type `UnityEngine.UIElements.Toggle`
* type `UnityEngine.UIElements.UQueryExtensions`
  * method `Q<1>(UnityEngine.UIElements.VisualElement, System.String, System.String)`
* type `UnityEngine.UIElements.VisualElement`
  * method `.ctor()`
  * method `get_style()`
* type `UnityEngine.UIElements.WhiteSpace`

<!-- api:end -->
