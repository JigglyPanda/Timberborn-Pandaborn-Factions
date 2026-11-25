# Pandaborn.Water - flumes, gates, current-driven machines, dew

What it does, per spec (all specs in `Pandaborn.Specs/WaterSpecs.cs`, only on `.Inkpaws` templates):

* `PandabornFlumeSegmentSpec { FlowCells }` -> `FlumeSegment` (+ `FlumeMonitor`). One tick after the piece is finished
  (`FlumeService` queue) it adds `IWaterService` direction limiters on its flow cells (water moves only along the piece's
  arrow) and lifts the piece's vanilla inert obstacle with the public `WaterObstacle.RemoveFromWaterService()`. On demolish
  it removes the limiters; the vanilla obstacle's own exit is then a no-op. Limiters are not saved by the game and are
  re-added on every load. `FlumeMonitor` (every 30 ticks) shows at most one status per piece, and one cause gives one
  status on the whole run (rules in `FlumeRules.cs`, tested without the game): a bend without a corner and a walled-off
  outlet on the piece itself; a dry intake on the first piece; a starved run on the last piece, after about four game
  hours dry, and only when no piece upstream already shows why (a dry intake, a gate shut by badwater, a missing corner,
  a wall). A run goes on through a Flume Corner's open cell (the piece that pours into the cell feeds the piece that
  leaves it), and the last flume before a Paddy Spout is the end of its run. A gate the player set to zero is not a
  cause: the end then says "let more through at the Flume Gate", which is the right advice.
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
  obstacle) and shows a status; it reopens after six clean checks in a row below half that (`BadwaterLatch`). Settings
  live in the per-entity carrier (`PandabornEntityStateSpec`, entry `Water|1|flow=0.30;guard=1;bad=1`; `bad`, optional,
  keeps a gate that was shut by badwater shut across a load; an older build ignores it).
* `PandabornCurrentDrivenSpec` -> `CurrentDriven`: reads the vanilla water wheel's rotation and its mechanical node's
  efficiency, shows "needs a current" when finished, not paused and idle. The wheel is its own power source (one
  mechanical node that is generator and consumer: the lift and the mill need the consumer half), so vanilla's
  `NoPowerStatus` raises "Building needs power" on a becalmed wheel too. Our status is a **priority** status, the game's
  own way to let one status stand for a building (as "Paused" does): while it shows, the vanilla line, its floating
  icon and its alert are hidden, with no patch. Any other ordinary status of the building is hidden with it for as long
  as the wheel is becalmed.
* `PandabornDewLimiterSpec { TemperateEfficiency, DroughtEfficiency }` -> `DewLimiter`, an `IManufactoryLimiter`.
* `PandabornPaddySpoutSpec`, `PandabornTreadwheelSpec`, `PandabornCisternTapSpec`: markers for the info panel lines.
* Panels (`WaterPanels.cs`, inside `SafeUi`): the Flume Gate panel reuses the vanilla floodgate fragment (flow slider in
  m3/s, badwater toggle, state line); one info line for Scoop Wheel, Trip-Hammer, Paddy Spout, Treadwheel, Cistern Tap.
  Text: `mod/Localizations/enUS_PandabornWater.csv`. A zero that is a healthy state is named, not shown as a number: a
  wheel whose basin is full says so and that it resumes by itself; a wheel whose scoops miss the water, a dry spout and
  an off-shift treadwheel say what is going on.
* `CisternTapHint`: when a Scoop Wheel that turned before (or any, in a drought) stops, or a Flume Gate that had water
  runs dry, the status carries one more sentence naming the faction's Cistern Tap ("A Cistern Tap can pour stored Water
  into the line."), only if the faction has a building with `PandabornCisternTapSpec` and it is unlocked.
* `WaterSounds` (docs/tech/sound.md §8): one area sound (`Environment.Pandaborn.FlumeWater`, building mixer, 10-tile
  cutoff) whose emitter tiles are the flume cells where water is flowing (each `FlumeMonitor` reports its own every 30
  ticks; a dry or standing line is quiet), and the bamboo tok (`Environment.Pandaborn.BambooTok`) from a child object
  of a run's last piece when water first reaches it, at most once every 20 real seconds game-wide. Both check
  `PandabornSounds.Has` first: silent without the clips.
* The Cistern Tap's panel line also gives the drought numbers in one sentence (how many tiles of farmland a small,
  medium or large cistern keeps moist through 3, 6 or 9 dry days).

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

**Fails safely.** The game treats an exception in a finished-state listener as a failed load and one in a tick as a
crash, so every callback of the module is contained (`WaterGuard`): the piece keeps the state it had (a flume that could
not be opened stays the solid block its data makes it; a gate keeps its flow and loses only its guard; a monitor stops
reporting), the first failure marks the feature "on, reduced" in the feature report, and the log gets the first eight
stack traces. Full obstacles are not counted by the game (a second removal of the same cell merges or deletes the water
column there), so each is added and removed exactly once, through vanilla's own `WaterObstacle` book-keeping or the
`SolidCells` list. In an Inkpaws game without any water building the report says "off (no data in this game)". Panel
pieces that fail while on screen are hidden, not left with stale text.

**Known limits** (docs/tech/water.md, "Review 2026-11-25"): the game restores saved water by column index, so a piece
whose flow cell stands on its own inert leg (Flume Bridge, Bridge span) and a capped piece (Gate) come back from a load
with the water of the wrong column for a moment; the per-cell safety net above puts back what is missing but does not
take away a surplus (a Bridge standing in a pond lifts up to one block of pond water into the line at each load).

**Private members**: none. Everything above is public game API (see the list below).


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
  * method `EnableComponent()`
  * method `GetComponent<1>()`: `!!0`
  * method `get_Transform()`: `UnityEngine.Transform`
  * method `op_Implicit(Timberborn.BaseComponentSystem.BaseComponent)`: `System.Boolean`
* type `Timberborn.BaseComponentSystem.IAwakableComponent`

**Timberborn.BlockSystem**

* type `Timberborn.BlockSystem.BlockObject`
  * method `TransformCoordinates(UnityEngine.Vector3Int)`: `UnityEngine.Vector3Int`
  * method `get_Coordinates()`: `UnityEngine.Vector3Int`
  * method `get_IsFinished()`: `System.Boolean`
  * method `get_Orientation()`: `Timberborn.Coordinates.Orientation`
* type `Timberborn.BlockSystem.IBlockService`
  * method `Contains(UnityEngine.Vector3Int)`: `System.Boolean`
  * method `GetObjectsAt(UnityEngine.Vector3Int)`: `Timberborn.Common.ReadOnlyList`1<Timberborn.BlockSystem.BlockObject>`
* type `Timberborn.BlockSystem.IFinishedStateListener`

**Timberborn.BlueprintSystem**

* type `Timberborn.BlueprintSystem.Blueprint`
  * method `GetSpec<1>()`: `!!0`
  * method `HasSpec<1>()`: `System.Boolean`
* type `Timberborn.BlueprintSystem.ComponentSpec`
  * method `get_Blueprint()`: `Timberborn.BlueprintSystem.Blueprint`

**Timberborn.Buildings**

* type `Timberborn.Buildings.BuildingService`
  * method `get_Buildings()`: `Timberborn.Common.ReadOnlyList`1<Timberborn.Buildings.BuildingSpec>`
* type `Timberborn.Buildings.BuildingSpec`
  * method `op_Inequality(Timberborn.Buildings.BuildingSpec, Timberborn.Buildings.BuildingSpec)`: `System.Boolean`
* type `Timberborn.Buildings.PausableBuilding`
  * method `get_Paused()`: `System.Boolean`

**Timberborn.Common**

* type `Timberborn.Common.ReadOnlyList`1`
  * method `get_Count()`: `System.Int32`
  * method `get_Item(System.Int32)`: `!0`

**Timberborn.Coordinates**

* type `Timberborn.Coordinates.Orientation`

**Timberborn.CoreSound**

* type `Timberborn.CoreSound.MixerNames`
  * field `BuildingMixerNameKey`: `System.String`

**Timberborn.CoreUI**

* type `Timberborn.CoreUI.VisualElementExtensions`
  * method `ToggleDisplayStyle(UnityEngine.UIElements.VisualElement, System.Boolean)`
* type `Timberborn.CoreUI.VisualElementLoader`
  * method `LoadVisualElement(System.String)`: `UnityEngine.UIElements.VisualElement`

**Timberborn.EntityPanelSystem**

* type `Timberborn.EntityPanelSystem.EntityPanelModule`
* type `Timberborn.EntityPanelSystem.EntityPanelModule+Builder`
  * method `.ctor()`
  * method `AddMiddleFragment(Timberborn.EntityPanelSystem.IEntityPanelFragment, System.Int32)`
  * method `Build()`: `Timberborn.EntityPanelSystem.EntityPanelModule`
* type `Timberborn.EntityPanelSystem.IEntityPanelFragment`

**Timberborn.EntitySystem**

* type `Timberborn.EntitySystem.IInitializableEntity`
* type `Timberborn.EntitySystem.IPostLoadableEntity`
* type `Timberborn.EntitySystem.LabeledEntitySpec`
  * method `get_DisplayNameLocKey()`: `System.String`
  * method `op_Inequality(Timberborn.EntitySystem.LabeledEntitySpec, Timberborn.EntitySystem.LabeledEntitySpec)`: `System.Boolean`

**Timberborn.FactionSystem**

* type `Timberborn.FactionSystem.FactionSpec`
  * method `get_Id()`: `System.String`

**Timberborn.GameFactionSystem**

* type `Timberborn.GameFactionSystem.FactionService`
  * method `get_Current()`: `Timberborn.FactionSystem.FactionSpec`

**Timberborn.Goods**

* type `Timberborn.Goods.GoodAmountSpec`
  * method `get_Amount()`: `System.Int32`

**Timberborn.HazardousWeatherSystem**

* type `Timberborn.HazardousWeatherSystem.DroughtWeather`
* type `Timberborn.HazardousWeatherSystem.HazardousWeatherService`
  * method `get_CurrentCycleHazardousWeather()`: `Timberborn.HazardousWeatherSystem.IHazardousWeather`
* type `Timberborn.HazardousWeatherSystem.IHazardousWeather`

**Timberborn.Localization**

* type `Timberborn.Localization.ILoc`
  * method `T(System.String)`: `System.String`
  * method `T<1>(System.String, !!0)`: `System.String`
  * method `T<2>(System.String, !!0, !!1)`: `System.String`
  * method `T<3>(System.String, !!0, !!1, !!2)`: `System.String`

**Timberborn.MechanicalSystem**

* type `Timberborn.MechanicalSystem.MechanicalGraph`
* type `Timberborn.MechanicalSystem.MechanicalNode`
  * method `get_Graph()`: `Timberborn.MechanicalSystem.MechanicalGraph`
  * method `get_PowerEfficiency()`: `System.Single`
* type `Timberborn.MechanicalSystem.MechanicalNodeSpec`
  * method `get_PowerInput()`: `System.Int32`
  * method `get_PowerOutput()`: `System.Int32`
  * method `op_Inequality(Timberborn.MechanicalSystem.MechanicalNodeSpec, Timberborn.MechanicalSystem.MechanicalNodeSpec)`: `System.Boolean`

**Timberborn.PowerGeneration**

* type `Timberborn.PowerGeneration.WaterPoweredGenerator`
  * method `get_GeneratorRotation()`: `System.Single`

**Timberborn.RootProviders**

* type `Timberborn.RootProviders.RootObjectProvider`
  * method `CreateRootObject(System.String)`: `UnityEngine.GameObject`

**Timberborn.ScienceSystem**

* type `Timberborn.ScienceSystem.BuildingUnlockingService`
  * method `Unlocked(Timberborn.Buildings.BuildingSpec)`: `System.Boolean`

**Timberborn.SingletonSystem**

* type `Timberborn.SingletonSystem.ILoadableSingleton`

**Timberborn.SoundSystem**

* type `Timberborn.SoundSystem.IEmitterMap`
* type `Timberborn.SoundSystem.ISoundSystem`
  * method `AddLargeAreaSound(UnityEngine.Transform, Timberborn.SoundSystem.IEmitterMap, System.String, System.Int32, System.Int32, System.String)`

**Timberborn.StatusSystem**

* type `Timberborn.StatusSystem.StatusSubject`
  * method `RegisterStatus(Timberborn.StatusSystem.StatusToggle)`
* type `Timberborn.StatusSystem.StatusToggle`
  * method `CreateNormalStatusWithAlertAndFloatingIcon(System.String, System.String, System.String, System.Single)`: `Timberborn.StatusSystem.StatusToggle`
  * method `CreateNormalStatusWithFloatingIcon(System.String, System.String, System.Single)`: `Timberborn.StatusSystem.StatusToggle`
  * method `CreatePriorityStatusWithFloatingIcon(System.String, System.String, System.Single)`: `Timberborn.StatusSystem.StatusToggle`
  * method `Deactivate()`
  * method `Toggle(System.Boolean)`
  * method `get_IsActive()`: `System.Boolean`

**Timberborn.TemplateInstantiation**

* type `Timberborn.TemplateInstantiation.TemplateModule`
* type `Timberborn.TemplateInstantiation.TemplateModule+Builder`
  * method `.ctor()`
  * method `AddDecorator<2>()`
  * method `Build()`: `Timberborn.TemplateInstantiation.TemplateModule`

**Timberborn.TemplateSystem**

* type `Timberborn.TemplateSystem.TemplateService`
  * method `GetAll<1>()`: `System.Collections.Generic.IEnumerable`1<!!0>`

**Timberborn.TickSystem**

* type `Timberborn.TickSystem.ITickableSingleton`
* type `Timberborn.TickSystem.TickableComponent`
  * method `.ctor()`

**Timberborn.TimeSystem**

* type `Timberborn.TimeSystem.IDayNightCycle`
  * method `get_PartialDayNumber()`: `System.Single`

**Timberborn.WaterBuildings**

* type `Timberborn.WaterBuildings.FillValve`
  * method `get_ActualHeight()`: `System.Single`
  * method `get_MinTargetHeight()`: `System.Int32`
  * method `get_TargetDepth()`: `System.Single`
* type `Timberborn.WaterBuildings.ThrottlingValve`
* type `Timberborn.WaterBuildings.WaterInput`
  * method `get_IsUnderwater()`: `System.Boolean`
* type `Timberborn.WaterBuildings.WaterMover`
  * method `get_CanMoveWater()`: `System.Boolean`
  * method `get_EffectiveFlowRate()`: `System.Single`
* type `Timberborn.WaterBuildings.WaterOutput`
  * method `get_HasSpaceForWater()`: `System.Boolean`

**Timberborn.WaterObjects**

* type `Timberborn.WaterObjects.WaterObstacle`
  * method `AddToWaterService(System.Single)`
  * method `RemoveFromWaterService()`

**Timberborn.WaterSystem**

* type `Timberborn.WaterSystem.FlowDirection`
* type `Timberborn.WaterSystem.FlowDirectionExtensions`
  * method `ToFlowDirection(Timberborn.Coordinates.Orientation)`: `Timberborn.WaterSystem.FlowDirection`
* type `Timberborn.WaterSystem.IThreadSafeWaterMap`
  * method `ColumnContamination(UnityEngine.Vector3Int)`: `System.Single`
  * method `TryGetColumnFloor(UnityEngine.Vector3Int, System.Int32&)`: `System.Boolean`
  * method `WaterDepth(UnityEngine.Vector3Int)`: `System.Single`
  * method `WaterFlowDirection(UnityEngine.Vector3Int)`: `UnityEngine.Vector2`
  * method `WaterHeightOrFloor(UnityEngine.Vector3Int)`: `System.Single`
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
  * method `get_IsHazardousWeather()`: `System.Boolean`

**Timberborn.WorkSystem**

* type `Timberborn.WorkSystem.Workplace`
  * method `get_NumberOfAssignedWorkers()`: `System.Int32`

**Timberborn.Workshops**

* type `Timberborn.Workshops.IManufactoryLimiter`
* type `Timberborn.Workshops.Manufactory`
  * method `get_CurrentRecipe()`: `Timberborn.Workshops.RecipeSpec`
* type `Timberborn.Workshops.RecipeSpec`
  * method `get_CycleDurationInHours()`: `System.Single`
  * method `get_Ingredients()`: `System.Collections.Immutable.ImmutableArray`1<Timberborn.Goods.GoodAmountSpec>`
  * method `op_Equality(Timberborn.Workshops.RecipeSpec, Timberborn.Workshops.RecipeSpec)`: `System.Boolean`

**UnityEngine.CoreModule**

* type `UnityEngine.Debug`
  * method `LogError(System.Object)`
  * method `LogWarning(System.Object)`
* type `UnityEngine.GameObject`
  * method `.ctor(System.String)`
  * method `get_transform()`: `UnityEngine.Transform`
* type `UnityEngine.Mathf`
  * method `Abs(System.Single)`: `System.Single`
  * method `Clamp01(System.Single)`: `System.Single`
  * method `Max(System.Single, System.Single)`: `System.Single`
  * method `RoundToInt(System.Single)`: `System.Int32`
* type `UnityEngine.Object`
  * method `op_Implicit(UnityEngine.Object)`: `System.Boolean`
* type `UnityEngine.Time`
  * method `get_unscaledTime()`: `System.Single`
* type `UnityEngine.Transform`
  * method `SetParent(UnityEngine.Transform, System.Boolean)`
  * method `set_localPosition(UnityEngine.Vector3)`
* type `UnityEngine.Vector2`
  * method `get_magnitude()`: `System.Single`
* type `UnityEngine.Vector2Int`
  * method `.ctor(System.Int32, System.Int32)`
* type `UnityEngine.Vector3`
  * method `.ctor(System.Single, System.Single, System.Single)`
* type `UnityEngine.Vector3Int`
  * method `.ctor(System.Int32, System.Int32, System.Int32)`
  * method `get_x()`: `System.Int32`
  * method `get_y()`: `System.Int32`
  * method `get_z()`: `System.Int32`
  * method `get_zero()`: `UnityEngine.Vector3Int`
  * method `op_Addition(UnityEngine.Vector3Int, UnityEngine.Vector3Int)`: `UnityEngine.Vector3Int`
  * method `op_Equality(UnityEngine.Vector3Int, UnityEngine.Vector3Int)`: `System.Boolean`
  * method `op_Inequality(UnityEngine.Vector3Int, UnityEngine.Vector3Int)`: `System.Boolean`
  * method `op_Subtraction(UnityEngine.Vector3Int, UnityEngine.Vector3Int)`: `UnityEngine.Vector3Int`

**UnityEngine.UIElementsModule**

* type `UnityEngine.UIElements.BaseBoolField`
  * method `set_text(System.String)`
* type `UnityEngine.UIElements.BaseField`1`
  * method `SetValueWithoutNotify(!0)`
* type `UnityEngine.UIElements.BaseSlider`1`
  * method `set_highValue(!0)`
  * method `set_lowValue(!0)`
* type `UnityEngine.UIElements.ChangeEvent`1`
  * method `get_newValue()`: `!0`
* type `UnityEngine.UIElements.DisplayStyle`
* type `UnityEngine.UIElements.EventCallback`1`
  * method `.ctor(System.Object, System.IntPtr)`
* type `UnityEngine.UIElements.INotifyValueChangedExtensions`
  * method `RegisterValueChangedCallback<1>(UnityEngine.UIElements.INotifyValueChanged`1<!!0>, UnityEngine.UIElements.EventCallback`1<UnityEngine.UIElements.ChangeEvent`1<!!0>>)`: `System.Boolean`
* type `UnityEngine.UIElements.INotifyValueChanged`1`
* type `UnityEngine.UIElements.IStyle`
  * method `set_display(UnityEngine.UIElements.StyleEnum`1<UnityEngine.UIElements.DisplayStyle>)`
  * method `set_whiteSpace(UnityEngine.UIElements.StyleEnum`1<UnityEngine.UIElements.WhiteSpace>)`
* type `UnityEngine.UIElements.Label`
* type `UnityEngine.UIElements.Slider`
* type `UnityEngine.UIElements.StyleEnum`1`
  * method `op_Implicit(!0)`: `UnityEngine.UIElements.StyleEnum`1<!0>`
* type `UnityEngine.UIElements.TextElement`
  * method `get_text()`: `System.String`
  * method `set_text(System.String)`
* type `UnityEngine.UIElements.Toggle`
* type `UnityEngine.UIElements.UQueryExtensions`
  * method `Q<1>(UnityEngine.UIElements.VisualElement, System.String, System.String)`: `!!0`
* type `UnityEngine.UIElements.VisualElement`
  * method `.ctor()`
  * method `get_style()`: `UnityEngine.UIElements.IStyle`
* type `UnityEngine.UIElements.WhiteSpace`

**Game classes derived from and interfaces implemented** (with the abstract members each had at build time; a new one keeps the module from loading)

* class `Bindito.Core.Configurator`: `Configure`
* interface `Bindito.Core.IProvider`1`: `Get`
* class `Timberborn.BaseComponentSystem.BaseComponent`
* interface `Timberborn.BaseComponentSystem.IAwakableComponent`: `Awake`
* interface `Timberborn.BlockSystem.IFinishedStateListener`: `OnEnterFinishedState`, `OnExitFinishedState`
* interface `Timberborn.EntityPanelSystem.IEntityPanelFragment`: `ClearFragment`, `InitializeFragment`, `ShowFragment`, `UpdateFragment`
* interface `Timberborn.EntitySystem.IInitializableEntity`: `InitializeEntity`
* interface `Timberborn.EntitySystem.IPostLoadableEntity`: `PostLoadEntity`
* interface `Timberborn.SingletonSystem.ILoadableSingleton`: `Load`
* interface `Timberborn.SoundSystem.IEmitterMap`: `IsEmitterAt`
* interface `Timberborn.TickSystem.ITickableSingleton`: `Tick`
* class `Timberborn.TickSystem.TickableComponent`: `Tick`
* interface `Timberborn.Workshops.IManufactoryLimiter`: `MaxProductionProgressChange`, `ProductionEfficiency`

<!-- api:end -->
