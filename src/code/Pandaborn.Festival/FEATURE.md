# Pandaborn.Festival - the Lantern Festival

DESIGN.md Pillar 5; full design, player timeline and test results in `docs/tech/events.md`. **Status: in
`Pandaborn.Code.sln` and `modules.txt`; ships with `catalogue/rules.toml [modules] Festival` (on since 2026-11-14).** Dev
copies with test timings: `proto/events/build.ps1`.

**What it does.** A Festival Square's panel shows what its district has in its ordinary stores towards a festival
(paper lanterns, the cooked dishes with 20 or more each, fireworks), a Call button, an auto-call toggle, the cycle of the
next allowed festival and the village's Tradition. Calling takes the goods out of the district's stores at once
(`Inventory.TakeConsumed`, unreserved stock only, the most plentiful dishes first) and the festival runs from the next
dawn to the dawn after.

**One district.** A festival belongs to the district of the square that called it (saved by the district centre's and
the square's entity ids). Its colonists take the day off and end festive; its squares host the show and light up. Every
other district works as usual and is not festive. The village holds at most one festival per cycle and Tradition is
one village counter, so a second district cannot double it. With one district nothing differs from "the whole
village", and the texts say "the whole village"; with several, the district variants of the texts name the district
(`enUS_PandabornFestivalDistricts.csv`). A save written before this rule has no district on record: that festival is
village-wide, as it was. If the festival's district centre is demolished meanwhile, nobody is on holiday and no square
hosts; the festival still ends at its dawn with Tradition. The auto-call asks the squares of the district that held
the last festival last, so the turn passes on.

* `FestivalGoer`, a root behaviour on every colonist template with `PandabornFestivalGoerSpec`, sits just above
  `WorkerRootBehavior` (above `NeederRootBehavior` for the young). On its district's festival day a colonist does not
  work, except the crews of the spec's `KeepWorkingTemplates` (pumps, lifts, taps) during their working hours (after
  them they join); by day the game's own need loop runs first, then colonists celebrate at the district's square: on
  its own dance slots first (the Dance Hall basis' 20 `Dancing` slots, entered with the game's `WalkInsideExecutor` as
  an attraction is, staying with `ApplyEffectExecutor` and the square's attraction effects), and when the slots are full
  just outside its edge (a ring 3.2–3.8 m from its centre, else the nearest of a few `GetRandomDestinationInDistrict`
  spots); from `ShowStartHours` to `ShowEndHours` everyone goes to the square first. Carrying, critical needs, death and
  stranding stay above it. A Ringtail's day rest (inserted in `InitializeEntity`) stays above it too, because the
  festival inserts in `PostInitializeEntity`: Ringtails sleep through the morning, then join. During the hours of the
  show the rest steps aside for the festival: `FestivalGatheringClock` is the module's Core `IGatheringClock` (true for a
  colonist of the festival's district that has the festival behaviour and is not on a crew in its hours; never outside
  the show), so a Ringtail whose rest would run past 15.5 h does not miss the lanterns.
* **The rising lanterns** (`FestivalSquare.UpdateSky` / `Release`, `FestivalService.UpdateSky` / `RunShow`): a square
  whose blueprint has the `LanternRise` attachment (prefab `Effects/Pandaborn/LanternRise` in `pandabornattachments`,
  one `ParticleSystem`; a particle system under a `#LanternRise` node works too) gets a lantern sky for the whole show:
  the module sets the system's emission rate (`SkyLanternsPerSecond` 0.65, about 21 aloft at once with the prefab's
  25–40 s life, a new one every 1.5 s), `Emit`s the dense release (`LanternRises` 24 over 0.3 game hours from
  `ShowStartHours` + 0.25 = 15.75 h, with `Environment.Pandaborn.LanternRise` three times across it and never
  otherwise), adds the game's wind to the drift, and stops emitting at `ShowEndHours` so the last lanterns rise on and
  fade. A sky switched on late (a load in the middle of the show) is fast-forwarded so it starts filled. **Time:**
  the particles run on scaled game time times the game's `NonlinearAnimationManager.SpeedMultiplier`, i.e. at the
  square root of the game speed, exactly as the game runs its own particles (`NonLinearParticlesSpeedMultiplier`):
  they stand still in a pause, rise 1.7× / 2.6× as fast at speed 2 / 3, and the number aloft is the same at every
  speed. Unscaled time was rejected (lanterns rising through a pause; at speed 3 the show lasts 18 real seconds, less
  than one lantern's life).
* **Comets and bursts** are the game's own firework entities (`FestivalFireworks`), from `#FireworkMount`: the
  trail-only comets (`LanternFireworkIds`, `LanternRises` of them over 1.75 h from 15.75 h) fly only in a Grand
  Festival, or as the lanterns' stand-in at a square without the lantern art; the bursts (`BurstFireworkIds`, `Bursts`
  over 2.5 h from `FireworksStartHours`) only in a Grand Festival (20 fireworks in store as well). Everything is
  computed from the clock (`FestivalRules.Due`), so nothing is launched twice and a reload launches only what is still
  due. The square's `#FestivalLights` node is shown from the call to the end at a hosting square.
* Sounds (the sound lane's `pandabornsounds`, docs/tech/sound.md 8): `Environment.Pandaborn.Firecrackers` once when the
  festival begins and at each hosting square as the gathering starts, `Environment.Pandaborn.FestivalDrum` looped there
  through the gathering, `Environment.Pandaborn.LanternRise` on the dense release. A clip that is not loaded is silent
  (`FestivalSounds`).
* Rewards: the festive need (`FestiveNeedId`) is set to its maximum for a colonist when it first reaches the square and
  for everyone else of the district when the festival ends; `GrandNeedId` too after a Grand Festival. Tradition rises
  by one. No number of the need (its decay, its well-being) is in code.
* `TraditionToolLocker` (an `IToolLocker`, the game's own toolbar lock) keeps decorations with
  `PandabornTraditionSpec { Level }` locked until Tradition reaches their level; clicking one explains it. It only locks
  tools science does not lock (the game allows one locker per tool), so such decorations need `ScienceCost` 0.

**Rules.** At most one festival per cycle in the village (the cycle of its day, read when the game posts
`CycleDayStartedEvent`, i.e. after it has moved the cycle on). Manual calls are allowed in any weather; the auto-call
never fires during a drought or badtide or on the day before one. Called at any hour, it begins at the next dawn.
`FestivalRules` holds the arithmetic without game types (tests: `src/code/tests/Events`).

**Data it needs** (catalogue): `PandabornFestivalSpec` (all numbers and lists) and `PandabornFestivalGoerSpec` on the Inkpaw
adult template; `PandabornFestivalGoerSpec` on the Inkpaw child and the Ringtail adult and child templates;
`PandabornFestivalSquareSpec` on the Festival Square, and for the lantern sky its `TemplateAttachmentsSpec` entry
`LanternRise` (docs/tech/events.md 8); `PandabornTraditionSpec` on the Tradition decorations.

**Saved**: `PandabornStore` entry `Festival` v1: `phase` (None/Called/Running), `day`, `grand`, `last` (cycle),
`tradition`, `auto`, `count`, and since 2026-11-25 `district` and `square` (entity ids, empty when none; an older module
ignores them, a save without them is read as village-wide). Nothing per entity: need points are the game's own (the
festive need decays by itself); lanterns in the air are not saved (the sky refills after a load).

**Fails safely.**
* Module off (or its game API changed): no panel, no festival, the square is its vanilla basis (a village square
  attraction), decorations are simply buildable, the store entry is carried unchanged. A save made mid-festival loads
  with everyone working as usual (a colonist saved in the middle of its festival walk simply decides again: the game
  drops a saved behaviour it cannot find); when the module is back, a festival whose day has passed ends at once on load
  with its rewards (the goods were spent), one called for today starts.
* `BehaviorManager._rootBehaviors` (private) gone, or `simulate-missing-member: Festival.RootBehaviors`: no day off;
  the evening show, festive spirit and Tradition remain, and the panel says so. Found only with the first colonist
  (after Load), it is reported then. One entity that is not built like a colonist only loses its own day off.
* `Timberborn.FireworkSystem.Firework.Launch` (public method of an internal type, reached by reflection) gone, or
  `simulate-missing-member: Festival.Fireworks`: no comets or bursts; the lantern sky and everything else run.
* Every fault is reported through `FeatureRegistry.ReportDegradedInGame("Festival", ...)` (`FestivalService.Fault`:
  all of the running game's faults in one line; forgotten when the next game starts, where Load checks again; fireworks
  that fail in the middle of a game are reported then). A game of our faction without the data gets `ReportNoData`.
* The festival's notices are posted with a subject (`Messenger.Post(text, subject)`): the square it is held at, else
  its district's centre, so the notification log entry leads to the festival's own district, not to the first
  district centre.
* Missing art degrades to nothing: no `LanternRise` attachment (or no particle system in it, or a failure while driving
  it) means the comets instead; no `#FestivalLights` or `#FireworkMount` node means no toggle and the square's centre as
  the launch point. A missing sound clip is silent.
* Nothing thrown by the module reaches the game: `FestivalGoer.Decide` (the game does not catch a behaviour's
  exception) releases the colonist to its ordinary day and logs once; ticks, event handlers, entity callbacks and the
  tool lock's click are wrapped; a lock that cannot explain itself opens. Interface pieces sit behind `SafeUi`.
* Per-session statics are reset at each game's Load (`FestivalGoer.ResetForGame`), so one game's failure does not
  switch the day off in the next.

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
  * method `To<1>()`: `Bindito.Core.IScopeAssignee`
  * method `ToProvider(System.Func`1<!0>)`: `Bindito.Core.IScopeAssignee`
  * method `ToProvider<1>()`: `Bindito.Core.IScopeAssignee`
* type `Bindito.Core.IContainer`
  * method `GetInstance<1>()`: `!!0`
* type `Bindito.Core.IExportAssignee`
* type `Bindito.Core.IMultiBindingBuilder`1`
* type `Bindito.Core.IProvider`1`
* type `Bindito.Core.IScopeAssignee`
  * method `AsSingleton()`: `Bindito.Core.IExportAssignee`
  * method `AsTransient()`: `Bindito.Core.IExportAssignee`
* type `Bindito.Core.ISingleBindingBuilder`1`

**Timberborn.Attractions**

* type `Timberborn.Attractions.Attraction`
  * method `GetEfficiencyAdjustedEffects(System.Collections.Generic.List`1<Timberborn.Effects.ContinuousEffect>)`

**Timberborn.BaseComponentSystem**

* type `Timberborn.BaseComponentSystem.BaseComponent`
  * method `.ctor()`
  * method `GetComponent<1>()`: `!!0`
  * method `get_AllComponents()`: `Timberborn.Common.ReadOnlyList`1<System.Object>`
  * method `get_GameObject()`: `UnityEngine.GameObject`
  * method `get_Name()`: `System.String`
  * method `get_Transform()`: `UnityEngine.Transform`
  * method `op_Implicit(Timberborn.BaseComponentSystem.BaseComponent)`: `System.Boolean`
* type `Timberborn.BaseComponentSystem.IAwakableComponent`

**Timberborn.Beavers**

* type `Timberborn.Beavers.AdultSpec`

**Timberborn.BehaviorSystem**

* type `Timberborn.BehaviorSystem.Behavior`
  * method `Decide(Timberborn.BehaviorSystem.BehaviorAgent)`: `Timberborn.BehaviorSystem.Decision`
* type `Timberborn.BehaviorSystem.BehaviorAgent`
* type `Timberborn.BehaviorSystem.BehaviorManager`
* type `Timberborn.BehaviorSystem.Decision`
  * method `ReleaseNextTick()`: `Timberborn.BehaviorSystem.Decision`
  * method `ReleaseNow()`: `Timberborn.BehaviorSystem.Decision`
  * method `ReleaseWhenFinished(Timberborn.BehaviorSystem.IExecutor)`: `Timberborn.BehaviorSystem.Decision`
  * method `ReturnWhenFinished(Timberborn.BehaviorSystem.IExecutor)`: `Timberborn.BehaviorSystem.Decision`
  * method `TransferNow(Timberborn.BehaviorSystem.Behavior, Timberborn.BehaviorSystem.Decision&)`: `Timberborn.BehaviorSystem.Decision`
  * method `get_ShouldReleaseNow()`: `System.Boolean`
* type `Timberborn.BehaviorSystem.ExecutorStatus`
* type `Timberborn.BehaviorSystem.IExecutor`
* type `Timberborn.BehaviorSystem.RootBehavior`
  * method `.ctor()`
* type `Timberborn.BehaviorSystem.WaitExecutor`
  * method `LaunchForSpecifiedTime(System.Single)`

**Timberborn.BlockObjectTools**

* type `Timberborn.BlockObjectTools.BlockObjectTool`
  * method `get_Template()`: `Timberborn.BlockSystem.PlaceableBlockObjectSpec`

**Timberborn.BlockSystem**

* type `Timberborn.BlockSystem.BlockObjectCenter`
  * method `get_WorldCenterGrounded()`: `UnityEngine.Vector3`
* type `Timberborn.BlockSystem.IFinishedStateListener`
* type `Timberborn.BlockSystem.PlaceableBlockObjectSpec`
  * method `op_Equality(Timberborn.BlockSystem.PlaceableBlockObjectSpec, Timberborn.BlockSystem.PlaceableBlockObjectSpec)`: `System.Boolean`

**Timberborn.BlueprintSystem**

* type `Timberborn.BlueprintSystem.Blueprint`
  * method `GetSpec<1>()`: `!!0`
* type `Timberborn.BlueprintSystem.ComponentSpec`
  * method `GetSpec<1>()`: `!!0`
  * method `get_Blueprint()`: `Timberborn.BlueprintSystem.Blueprint`

**Timberborn.Buildings**

* type `Timberborn.Buildings.BuildingSpec`
  * method `op_Equality(Timberborn.Buildings.BuildingSpec, Timberborn.Buildings.BuildingSpec)`: `System.Boolean`

**Timberborn.Common**

* type `Timberborn.Common.IRandomNumberGenerator`
  * method `Range(System.Single, System.Single)`: `System.Single`
* type `Timberborn.Common.ReadOnlyHashSet`1`
  * method `GetEnumerator()`: `System.Collections.Generic.HashSet`1+Enumerator<!0>`
* type `Timberborn.Common.ReadOnlyList`1`
  * method `get_Count()`: `System.Int32`

**Timberborn.CoreUI**

* type `Timberborn.CoreUI.DialogBox`
* type `Timberborn.CoreUI.DialogBoxShower`
  * method `Create()`: `Timberborn.CoreUI.DialogBoxShower+Builder`
* type `Timberborn.CoreUI.DialogBoxShower+Builder`
  * method `SetConfirmButton(System.Action)`: `Timberborn.CoreUI.DialogBoxShower+Builder`
  * method `SetMessage(System.String)`: `Timberborn.CoreUI.DialogBoxShower+Builder`
  * method `Show()`: `Timberborn.CoreUI.DialogBox`
* type `Timberborn.CoreUI.VisualElementExtensions`
  * method `ToggleDisplayStyle(UnityEngine.UIElements.VisualElement, System.Boolean)`
* type `Timberborn.CoreUI.VisualElementLoader`
  * method `LoadVisualElement(System.String)`: `UnityEngine.UIElements.VisualElement`

**Timberborn.Effects**

* type `Timberborn.Effects.ContinuousEffect`
* type `Timberborn.Effects.InstantEffect`
  * method `.ctor(System.String, System.Single, System.Int32)`

**Timberborn.EnterableSystem**

* type `Timberborn.EnterableSystem.Enterable`
  * method `get_CanReserveSlot()`: `System.Boolean`
* type `Timberborn.EnterableSystem.Enterer`
  * method `get_CurrentBuilding()`: `Timberborn.EnterableSystem.Enterable`
  * method `get_IsInside()`: `System.Boolean`

**Timberborn.EntityPanelSystem**

* type `Timberborn.EntityPanelSystem.EntityPanelModule`
* type `Timberborn.EntityPanelSystem.EntityPanelModule+Builder`
  * method `.ctor()`
  * method `AddBottomFragment(Timberborn.EntityPanelSystem.IEntityPanelFragment, System.Int32)`
  * method `Build()`: `Timberborn.EntityPanelSystem.EntityPanelModule`
* type `Timberborn.EntityPanelSystem.IEntityPanelFragment`

**Timberborn.EntitySystem**

* type `Timberborn.EntitySystem.EntityComponent`
  * method `get_EntityId()`: `System.Guid`
* type `Timberborn.EntitySystem.EntityRegistry`
  * method `GetEntity(System.Guid)`: `Timberborn.EntitySystem.EntityComponent`
* type `Timberborn.EntitySystem.EntityService`
  * method `Delete(Timberborn.BaseComponentSystem.BaseComponent)`
  * method `Instantiate(Timberborn.BlueprintSystem.Blueprint)`: `Timberborn.EntitySystem.EntityComponent`
* type `Timberborn.EntitySystem.IDeletableEntity`
* type `Timberborn.EntitySystem.IPostInitializableEntity`
* type `Timberborn.EntitySystem.LabeledEntitySpec`
  * method `get_DisplayNameLocKey()`: `System.String`
  * method `op_Inequality(Timberborn.EntitySystem.LabeledEntitySpec, Timberborn.EntitySystem.LabeledEntitySpec)`: `System.Boolean`

**Timberborn.FactionSystem**

* type `Timberborn.FactionSystem.FactionSpec`
  * method `get_Id()`: `System.String`

**Timberborn.FireworkSystem**

* type `Timberborn.FireworkSystem.FireworkLimits`
  * field `MaxFlightDistance`: `System.Int32`
  * field `MinFlightDistance`: `System.Int32`
* type `Timberborn.FireworkSystem.FireworkSpec`
* type `Timberborn.FireworkSystem.FireworkSpecService`
  * method `GetFireworkSpec(System.String)`: `Timberborn.FireworkSystem.FireworkSpec`
  * method `HasSpec(System.String)`: `System.Boolean`

**Timberborn.GameCycleSystem**

* type `Timberborn.GameCycleSystem.CycleDayStartedEvent`
* type `Timberborn.GameCycleSystem.GameCycleService`
  * method `get_Cycle()`: `System.Int32`

**Timberborn.GameDistricts**

* type `Timberborn.GameDistricts.Citizen`
  * method `get_AssignedDistrict()`: `Timberborn.GameDistricts.DistrictCenter`
* type `Timberborn.GameDistricts.DistrictBuilding`
  * method `get_District()`: `Timberborn.GameDistricts.DistrictCenter`
* type `Timberborn.GameDistricts.DistrictCenter`
  * method `get_District()`: `Timberborn.Navigation.District`
  * method `get_DistrictName()`: `System.String`
* type `Timberborn.GameDistricts.DistrictCenterRegistry`
  * method `get_FinishedDistrictCenters()`: `Timberborn.Common.ReadOnlyList`1<Timberborn.GameDistricts.DistrictCenter>`

**Timberborn.GameFactionSystem**

* type `Timberborn.GameFactionSystem.FactionService`
  * method `get_Current()`: `Timberborn.FactionSystem.FactionSpec`

**Timberborn.Goods**

* type `Timberborn.Goods.GoodAmount`
  * method `.ctor(System.String, System.Int32)`
  * method `get_Amount()`: `System.Int32`
  * method `get_GoodId()`: `System.String`
* type `Timberborn.Goods.GoodSpec`
  * method `get_PluralDisplayName()`: `Timberborn.LocalizationSerialization.LocalizedText`
  * method `op_Inequality(Timberborn.Goods.GoodSpec, Timberborn.Goods.GoodSpec)`: `System.Boolean`
* type `Timberborn.Goods.IGoodService`
  * method `GetGoodOrNull(System.String)`: `Timberborn.Goods.GoodSpec`

**Timberborn.InputSystem**

* type `Timberborn.InputSystem.InputService`
  * method `IsKeyHeld(System.String)`: `System.Boolean`

**Timberborn.InventorySystem**

* type `Timberborn.InventorySystem.DistrictInventoryRegistry`
  * method `ActiveInventoriesWithStock(System.String)`: `Timberborn.Common.ReadOnlyHashSet`1<Timberborn.InventorySystem.Inventory>`
* type `Timberborn.InventorySystem.Inventory`
  * method `TakeConsumed(Timberborn.Goods.GoodAmount)`
  * method `UnreservedAmountInStock(System.String)`: `System.Int32`

**Timberborn.Localization**

* type `Timberborn.Localization.ILoc`
  * method `T(System.String)`: `System.String`
  * method `T<1>(System.String, !!0)`: `System.String`
  * method `T<2>(System.String, !!0, !!1)`: `System.String`
  * method `T<3>(System.String, !!0, !!1, !!2)`: `System.String`

**Timberborn.LocalizationSerialization**

* type `Timberborn.LocalizationSerialization.LocalizedText`
  * method `get_Value()`: `System.String`

**Timberborn.Navigation**

* type `Timberborn.Navigation.District`
* type `Timberborn.Navigation.IDistrictService`
  * method `GetRandomDestinationInDistrict(Timberborn.Navigation.District, UnityEngine.Vector3)`: `UnityEngine.Vector3`

**Timberborn.NeedBehaviorSystem**

* type `Timberborn.NeedBehaviorSystem.ApplyEffectExecutor`
  * method `LaunchToTimestamp(System.Collections.Generic.IEnumerable`1<Timberborn.Effects.ContinuousEffect>, System.Single, System.String)`
* type `Timberborn.NeedBehaviorSystem.NeederRootBehavior`

**Timberborn.NeedSystem**

* type `Timberborn.NeedSystem.NeedManager`
  * method `ApplyEffect(Timberborn.Effects.InstantEffect&)`
  * method `GetNeedPoints(System.String)`: `System.Single`
  * method `HasNeed(System.String)`: `System.Boolean`
  * method `NeedPointsToMax(System.String)`: `System.Single`

**Timberborn.ScienceSystem**

* type `Timberborn.ScienceSystem.BuildingUnlockingService`
  * method `Unlocked(Timberborn.Buildings.BuildingSpec)`: `System.Boolean`

**Timberborn.SingletonSystem**

* type `Timberborn.SingletonSystem.EventBus`
  * method `Register(System.Object)`
* type `Timberborn.SingletonSystem.ILoadableSingleton`
* type `Timberborn.SingletonSystem.IPostLoadableSingleton`
* type `Timberborn.SingletonSystem.OnEventAttribute`
  * method `.ctor()`

**Timberborn.SoundSystem**

* type `Timberborn.SoundSystem.AudioClipService`
  * method `GetAudioClipNames(System.String)`: `System.Collections.Generic.IEnumerable`1<System.String>`
* type `Timberborn.SoundSystem.ISoundSystem`
  * method `LoopSingle3DSound(UnityEngine.GameObject, System.String, System.Int32)`
  * method `PlaySound2D(UnityEngine.GameObject, System.String, System.Int32)`
  * method `PlaySound3D(UnityEngine.GameObject, System.String, System.Int32)`
  * method `StopSound(UnityEngine.GameObject, System.String)`

**Timberborn.TemplateAttachmentSystem**

* type `Timberborn.TemplateAttachmentSystem.TemplateAttachment`
  * method `get_GameObject()`: `UnityEngine.GameObject`
* type `Timberborn.TemplateAttachmentSystem.TemplateAttachments`
  * method `GetOrCreateAttachment(System.String)`: `Timberborn.TemplateAttachmentSystem.TemplateAttachment`

**Timberborn.TemplateInstantiation**

* type `Timberborn.TemplateInstantiation.TemplateModule`
* type `Timberborn.TemplateInstantiation.TemplateModule+Builder`
  * method `.ctor()`
  * method `AddDecorator<2>()`
  * method `Build()`: `Timberborn.TemplateInstantiation.TemplateModule`

**Timberborn.TemplateSystem**

* type `Timberborn.TemplateSystem.TemplateService`
  * method `GetAll<1>()`: `System.Collections.Generic.IEnumerable`1<!!0>`
* type `Timberborn.TemplateSystem.TemplateSpec`
  * method `get_TemplateName()`: `System.String`
  * method `op_Inequality(Timberborn.TemplateSystem.TemplateSpec, Timberborn.TemplateSystem.TemplateSpec)`: `System.Boolean`

**Timberborn.TickSystem**

* type `Timberborn.TickSystem.ITickableSingleton`

**Timberborn.TimeSystem**

* type `Timberborn.TimeSystem.IDayNightCycle`
  * method `DayNumberHoursFromNow(System.Single)`: `System.Single`
  * method `get_DayLengthInSeconds()`: `System.Single`
  * method `get_DayNumber()`: `System.Int32`
  * method `get_HoursPassedToday()`: `System.Single`
  * method `get_PartialDayNumber()`: `System.Single`
* type `Timberborn.TimeSystem.NonlinearAnimationManager`
  * method `get_SpeedMultiplier()`: `System.Single`

**Timberborn.ToolSystem**

* type `Timberborn.ToolSystem.ITool`
* type `Timberborn.ToolSystem.IToolLocker`
* type `Timberborn.ToolSystem.ToolUnlockingService`
  * method `IsLocked(Timberborn.ToolSystem.ITool)`: `System.Boolean`
  * method `Unlock(Timberborn.ToolSystem.ITool)`

**Timberborn.WalkingSystem**

* type `Timberborn.WalkingSystem.WalkInsideExecutor`
  * method `Launch(Timberborn.EnterableSystem.Enterable)`: `Timberborn.BehaviorSystem.ExecutorStatus`
* type `Timberborn.WalkingSystem.WalkToPositionExecutor`
  * method `Launch(UnityEngine.Vector3)`: `Timberborn.BehaviorSystem.ExecutorStatus`

**Timberborn.Wandering**

* type `Timberborn.Wandering.WanderRootBehavior`

**Timberborn.WeatherSystem**

* type `Timberborn.WeatherSystem.WeatherService`
  * method `NextDayIsHazardousWeather()`: `System.Boolean`
  * method `get_IsHazardousWeather()`: `System.Boolean`

**Timberborn.WindSystem**

* type `Timberborn.WindSystem.WindService`
  * method `get_WindDirection()`: `UnityEngine.Vector2`
  * method `get_WindStrength()`: `System.Single`

**Timberborn.WorkSystem**

* type `Timberborn.WorkSystem.Worker`
  * method `get_Employed()`: `System.Boolean`
  * method `get_Workplace()`: `Timberborn.WorkSystem.Workplace`
* type `Timberborn.WorkSystem.WorkerRootBehavior`
* type `Timberborn.WorkSystem.WorkerWorkingHours`
  * method `get_AreWorkingHours()`: `System.Boolean`
* type `Timberborn.WorkSystem.Workplace`

**UnityEngine.CoreModule**

* type `UnityEngine.Component`
  * method `GetComponentInChildren<1>(System.Boolean)`: `!!0`
  * method `get_gameObject()`: `UnityEngine.GameObject`
* type `UnityEngine.Debug`
  * method `Log(System.Object)`
  * method `LogError(System.Object)`
  * method `LogWarning(System.Object)`
* type `UnityEngine.GameObject`
  * method `.ctor(System.String)`
  * method `GetComponentInChildren<1>(System.Boolean)`: `!!0`
  * method `GetComponentsInChildren<1>(System.Boolean)`: `!!0[]`
  * method `SetActive(System.Boolean)`
  * method `get_transform()`: `UnityEngine.Transform`
* type `UnityEngine.Mathf`
  * method `Approximately(System.Single, System.Single)`: `System.Boolean`
  * method `CeilToInt(System.Single)`: `System.Int32`
  * method `Clamp(System.Single, System.Single, System.Single)`: `System.Single`
  * method `Clamp01(System.Single)`: `System.Single`
  * method `Cos(System.Single)`: `System.Single`
  * method `Max(System.Single, System.Single)`: `System.Single`
  * method `Sin(System.Single)`: `System.Single`
* type `UnityEngine.Object`
  * method `get_name()`: `System.String`
  * method `op_Implicit(UnityEngine.Object)`: `System.Boolean`
* type `UnityEngine.Quaternion`
  * method `Euler(System.Single, System.Single, System.Single)`: `UnityEngine.Quaternion`
* type `UnityEngine.Time`
  * method `get_unscaledTime()`: `System.Single`
* type `UnityEngine.Transform`
  * method `SetParent(UnityEngine.Transform, System.Boolean)`
  * method `get_position()`: `UnityEngine.Vector3`
  * method `set_position(UnityEngine.Vector3)`
* type `UnityEngine.Vector2`
  * field `x`: `System.Single`
  * field `y`: `System.Single`
* type `UnityEngine.Vector3`
  * field `x`: `System.Single`
  * field `z`: `System.Single`
  * method `.ctor(System.Single, System.Single, System.Single)`
  * method `get_sqrMagnitude()`: `System.Single`
  * method `get_up()`: `UnityEngine.Vector3`
  * method `get_zero()`: `UnityEngine.Vector3`
  * method `op_Addition(UnityEngine.Vector3, UnityEngine.Vector3)`: `UnityEngine.Vector3`
  * method `op_Inequality(UnityEngine.Vector3, UnityEngine.Vector3)`: `System.Boolean`
  * method `op_Multiply(UnityEngine.Vector3, System.Single)`: `UnityEngine.Vector3`
  * method `op_Subtraction(UnityEngine.Vector3, UnityEngine.Vector3)`: `UnityEngine.Vector3`

**UnityEngine.ParticleSystemModule**

* type `UnityEngine.ParticleSystem`
  * method `Emit(System.Int32)`
  * method `Play(System.Boolean)`
  * method `Simulate(System.Single, System.Boolean, System.Boolean, System.Boolean)`
  * method `Stop(System.Boolean, UnityEngine.ParticleSystemStopBehavior)`
  * method `get_emission()`: `UnityEngine.ParticleSystem+EmissionModule`
  * method `get_isPlaying()`: `System.Boolean`
  * method `get_main()`: `UnityEngine.ParticleSystem+MainModule`
  * method `get_particleCount()`: `System.Int32`
  * method `get_velocityOverLifetime()`: `UnityEngine.ParticleSystem+VelocityOverLifetimeModule`
* type `UnityEngine.ParticleSystem+EmissionModule`
  * method `set_enabled(System.Boolean)`
  * method `set_rateOverTime(UnityEngine.ParticleSystem+MinMaxCurve)`
* type `UnityEngine.ParticleSystem+MainModule`
  * method `set_loop(System.Boolean)`
  * method `set_simulationSpeed(System.Single)`
* type `UnityEngine.ParticleSystem+MinMaxCurve`
  * method `.ctor(System.Single, System.Single)`
  * method `op_Implicit(System.Single)`: `UnityEngine.ParticleSystem+MinMaxCurve`
* type `UnityEngine.ParticleSystem+VelocityOverLifetimeModule`
  * method `get_enabled()`: `System.Boolean`
  * method `set_x(UnityEngine.ParticleSystem+MinMaxCurve)`
  * method `set_z(UnityEngine.ParticleSystem+MinMaxCurve)`
* type `UnityEngine.ParticleSystemStopBehavior`

**UnityEngine.UIElementsModule**

* type `UnityEngine.UIElements.BaseField`1`
  * method `SetValueWithoutNotify(!0)`
* type `UnityEngine.UIElements.Button`
  * method `add_clicked(System.Action)`
* type `UnityEngine.UIElements.ChangeEvent`1`
  * method `get_newValue()`: `!0`
* type `UnityEngine.UIElements.EventCallback`1`
  * method `.ctor(System.Object, System.IntPtr)`
* type `UnityEngine.UIElements.INotifyValueChangedExtensions`
  * method `RegisterValueChangedCallback<1>(UnityEngine.UIElements.INotifyValueChanged`1<!!0>, UnityEngine.UIElements.EventCallback`1<UnityEngine.UIElements.ChangeEvent`1<!!0>>)`: `System.Boolean`
* type `UnityEngine.UIElements.INotifyValueChanged`1`
* type `UnityEngine.UIElements.IStyle`
  * method `set_whiteSpace(UnityEngine.UIElements.StyleEnum`1<UnityEngine.UIElements.WhiteSpace>)`
* type `UnityEngine.UIElements.Label`
  * method `.ctor()`
* type `UnityEngine.UIElements.StyleEnum`1`
  * method `op_Implicit(!0)`: `UnityEngine.UIElements.StyleEnum`1<!0>`
* type `UnityEngine.UIElements.TextElement`
  * method `get_text()`: `System.String`
  * method `set_text(System.String)`
* type `UnityEngine.UIElements.Toggle`
  * method `.ctor(System.String)`
* type `UnityEngine.UIElements.UQueryExtensions`
  * method `Q<1>(UnityEngine.UIElements.VisualElement, System.String, System.String)`: `!!0`
* type `UnityEngine.UIElements.VisualElement`
  * method `.ctor()`
  * method `Add(UnityEngine.UIElements.VisualElement)`
  * method `AddToClassList(System.String)`
  * method `SetEnabled(System.Boolean)`
  * method `get_style()`: `UnityEngine.UIElements.IStyle`
  * method `set_name(System.String)`
* type `UnityEngine.UIElements.WhiteSpace`

**Game classes derived from and interfaces implemented** (with the abstract members each had at build time; a new one keeps the module from loading)

* class `Bindito.Core.Configurator`: `Configure`
* interface `Bindito.Core.IProvider`1`: `Get`
* class `Timberborn.BaseComponentSystem.BaseComponent`
* interface `Timberborn.BaseComponentSystem.IAwakableComponent`: `Awake`
* class `Timberborn.BehaviorSystem.RootBehavior`: `Decide`
* interface `Timberborn.BlockSystem.IFinishedStateListener`: `OnEnterFinishedState`, `OnExitFinishedState`
* interface `Timberborn.EntityPanelSystem.IEntityPanelFragment`: `ClearFragment`, `InitializeFragment`, `ShowFragment`, `UpdateFragment`
* interface `Timberborn.EntitySystem.IDeletableEntity`: `DeleteEntity`
* interface `Timberborn.EntitySystem.IPostInitializableEntity`: `PostInitializeEntity`
* interface `Timberborn.SingletonSystem.ILoadableSingleton`: `Load`
* interface `Timberborn.SingletonSystem.IPostLoadableSingleton`: `PostLoad`
* interface `Timberborn.TickSystem.ITickableSingleton`: `Tick`
* interface `Timberborn.ToolSystem.IToolLocker`: `ShouldLock`, `TryToUnlock`

<!-- api:end -->
