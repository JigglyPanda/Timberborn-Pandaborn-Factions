# Pandaborn.Flowering - the Great Flowering

DESIGN.md Pillar 5; full design, player timeline, the fairness arithmetic and test results in `docs/tech/events.md`.
**Status: in `Pandaborn.Code.sln` and `modules.txt`; ships with `catalogue/rules.toml [modules] Flowering` (on since
2026-11-14).** Dev copies with test timings: `proto/events/build.ps1`.

**What it does.** One bamboo species flowers per Flowering, in the order of `PandabornFloweringSpec.Species`, alternating.

* **Schedule** (`FloweringSchedule`, no game types; tests in `src/code/tests/Events`): never before `FirstCycle` (6;
  "rare" adds `RareDelayCycles`), then every `NormalMinCycles`..`NormalMaxCycles` cycles (rare:
  `RareMinCycles`..`RareMaxCycles`); the chosen cycle is saved. A Flowering happens at the start of a cycle, which is
  always temperate weather, so never in a drought or badtide.
* **Announced a full cycle ahead**, at the start of the cycle before (if announced later, by a load or a setting change, it
  moves one cycle further): a notice, a line under the top bar with the advice in its tooltip, a line on every bamboo's
  panel, and buds on the plants where the plant's spec says they are painted in its detail map (`BudsUseDetail`).
* **The Flowering**: every grown plant of the species, planted or wild, is replaced by its `InFlowerTemplate` twin (whose
  harvest, its cut yield in data, is bamboo seed) at the same tile, the planting mark put back under it; young plants
  die. **The change is spread over game ticks** (about 5 ms of work in each, never fewer than 8 plants; in a wave
  across the map): replacing a plant deletes an entity and creates one, and thousands in one tick would stall the game (an estimate from the game's code, never measured). A
  farm of a few dozen flowers within a few ticks; the notice with the number of plants and seed comes when the last
  one has turned. No entity is touched in Load, PostLoad or an event handler (by the game's code a twin placed before its
  event bus is ready has its planting mark cleared again later; not seen in game). Farmers and lumberjacks
  take the seed with their ordinary harvest, because the seed is a yield of their resource group.
* **The twins' end**, over the last day of `SeedDays` (3), each at an hour fixed for its tile (`FloweringSchedule.EndOf`):
  * on a tile **with a planting mark** the twin dies where it stands, as before: a dead crop loses its seed (the game's
    rule) and the farm plants over it; a dead twin tree keeps its seed until cut and the forester replants the stump;
  * a **wild** twin (no planting mark) that is **still standing** reseeds its own tile: it is replaced by a seedling of
    its species, which rests like every young plant until the rest ends (ruling of 2026-11-25; before, a wild grove
    flowered once and was gone for good). Its uncut seed is lost with it, trees included;
  * a twin that was **cut for its seed** is dead from the cut and is not touched: gone, like any wild tree that is cut.
  The twins that are alive and due queue up every in-game hour and meet their end in the following ticks, on the same
  budget as the change into flower; nothing pending is saved, because a due twin is either still alive (and found
  again next hour, also after a load) or already dead or replaced. The seed time closes when none is left alive.
* **The rest**: until `DormantDays` (9) after the Flowering, young plants of the species do not grow. The planting marks
  stay, so farms and foresters replant on their own; the seedlings start growing when the rest ends.
* **Setting** per save: normal, rare or off, in a game dialog opened from the top-bar line or any bamboo's panel. No other
  mod needed.

**Data it needs** (catalogue): `PandabornFloweringSpec` on the Inkpaw adult template; `PandabornFloweringPlantSpec` on the
two bamboos; the two twins (`PandabornShootBambooInFlower.Inkpaws`, `PandabornTimberBambooInFlower.Inkpaws`) with
`PandabornInFlowerSpec`, in `NaturalResources.Inkpaws`. No growth time or yield is in code.

**Saved**: `PandabornStore` entry `Flowering` v1: `setting`, `phase` (Idle/Announced/Flowering/Resting), `next` (cycle),
`nextSpecies`, `species`, `day` (when it flowered), `last` (cycle), `borne`, `lost` (seed), and since 2026-11-25 `twins`,
`killed` and `converting` (0 done, 1 grown plants still turning, 2 not begun; an older module ignores them, a save
without them is read as done) and `reseeded` (wild twins that reseeded, for the log). The twins are ordinary saved
plants. A save made while the bamboo is still coming into
flower goes on after the load with the grown plants that are left. The growth holds are not saved: the game saves
growth progress as always, and the service holds the plants again after a load.

**Growth holds and other mods.** A hold is the plant's own growth timer paused (`Growable._timeTrigger`, private). It
is never set once and trusted: the timer is read from the plant at every call, and every resting plant is held again
after a load, every in-game hour, when the Flowering begins and when a plant is planted. So when the game resumes a
plant by itself (one that stops dying), or **another mod replaces the timer object** (TimberCommons'
`GrowthRateModifier` does when one of its growth modifiers registers, and resumes the new one: compatibility audit
2026-11-25, m6), the plant grows for at most one in-game hour before it is held again: a slightly milder Flowering,
never a harsher one. The first time an hourly check finds resting plants growing, one line goes to the log
(`HeldAgain` counts them). Not seen in game with TimberCommons (docs/tech/events.md, "Needs a game run").

**Fails safely.**
* Module off: no announcements and no Flowering. Twins already in a save stay ordinary plants whose harvest is seed and
  never die by themselves; young bamboo grows at once; grown bamboo that had not turned yet stays ordinary bamboo. The
  store entry is carried unchanged; when the module is back it picks up where the save left off (an announced
  Flowering whose date passed moves to the next cycle start).
* `Growable._timeTrigger` (private) gone, or `simulate-missing-member: Flowering.GrowthHold`, or the timer throwing:
  young bamboo regrows at once after a Flowering (milder, never harsher).
* A plant that cannot be replaced is skipped; after five failures the rest of the bamboo is left as it is (ordinary
  plants). A wild twin that cannot be replaced is tried again next hour; after five failures wild twins die where
  they stand for the rest of that game (the behaviour before the reseeding rule).
* Every fault is reported with `FeatureRegistry.ReportDegradedInGame("Flowering", ...)`: all of the running game's
  faults in one line, forgotten when the next game starts (where Load checks again).
* A game of our faction without the data gets `FeatureRegistry.ReportNoData`.
* Nothing thrown by the module reaches the game (ticks, event handlers, entity callbacks, the cut event).
  Interface pieces sit behind `SafeUi`.

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
  * method `GetComponent<1>()`: `!!0`
  * method `get_GameObject()`: `UnityEngine.GameObject`
  * method `op_Implicit(Timberborn.BaseComponentSystem.BaseComponent)`: `System.Boolean`
* type `Timberborn.BaseComponentSystem.IAwakableComponent`

**Timberborn.Beavers**

* type `Timberborn.Beavers.AdultSpec`

**Timberborn.BlockSystem**

* type `Timberborn.BlockSystem.BlockObject`
  * method `get_Coordinates()`: `UnityEngine.Vector3Int`

**Timberborn.BlueprintSystem**

* type `Timberborn.BlueprintSystem.Blueprint`
  * method `GetSpec<1>()`: `!!0`
* type `Timberborn.BlueprintSystem.ComponentSpec`
  * method `GetSpec<1>()`: `!!0`
  * method `get_Blueprint()`: `Timberborn.BlueprintSystem.Blueprint`

**Timberborn.CoreUI**

* type `Timberborn.CoreUI.DialogBox`
* type `Timberborn.CoreUI.DialogBoxShower`
  * method `Create()`: `Timberborn.CoreUI.DialogBoxShower+Builder`
* type `Timberborn.CoreUI.DialogBoxShower+Builder`
  * method `AddContent(UnityEngine.UIElements.VisualElement)`: `Timberborn.CoreUI.DialogBoxShower+Builder`
  * method `SetConfirmButton(System.Action)`: `Timberborn.CoreUI.DialogBoxShower+Builder`
  * method `Show()`: `Timberborn.CoreUI.DialogBox`
* type `Timberborn.CoreUI.VisualElementExtensions`
  * method `ToggleDisplayStyle(UnityEngine.UIElements.VisualElement, System.Boolean)`
* type `Timberborn.CoreUI.VisualElementLoader`
  * method `LoadVisualElement(System.String)`: `UnityEngine.UIElements.VisualElement`

**Timberborn.Cutting**

* type `Timberborn.Cutting.Cuttable`
  * method `add_WasCut(System.EventHandler)`
  * method `get_RemoveOnCut()`: `System.Boolean`
  * method `get_Yielder()`: `Timberborn.Yielding.Yielder`
  * method `get_YielderSpec()`: `Timberborn.Yielding.YielderSpec`
  * method `remove_WasCut(System.EventHandler)`

**Timberborn.EntityPanelSystem**

* type `Timberborn.EntityPanelSystem.EntityPanelModule`
* type `Timberborn.EntityPanelSystem.EntityPanelModule+Builder`
  * method `.ctor()`
  * method `AddMiddleFragment(Timberborn.EntityPanelSystem.IEntityPanelFragment, System.Int32)`
  * method `Build()`: `Timberborn.EntityPanelSystem.EntityPanelModule`
* type `Timberborn.EntityPanelSystem.IEntityPanelFragment`

**Timberborn.EntitySystem**

* type `Timberborn.EntitySystem.EntityService`
  * method `Delete(Timberborn.BaseComponentSystem.BaseComponent)`
* type `Timberborn.EntitySystem.IDeletableEntity`
* type `Timberborn.EntitySystem.IPostInitializableEntity`
* type `Timberborn.EntitySystem.LabeledEntitySpec`
  * method `get_DisplayNameLocKey()`: `System.String`
  * method `op_Inequality(Timberborn.EntitySystem.LabeledEntitySpec, Timberborn.EntitySystem.LabeledEntitySpec)`: `System.Boolean`

**Timberborn.FactionSystem**

* type `Timberborn.FactionSystem.FactionSpec`
  * method `get_Id()`: `System.String`

**Timberborn.Forestry**

* type `Timberborn.Forestry.TreeComponentSpec`
  * method `op_Inequality(Timberborn.Forestry.TreeComponentSpec, Timberborn.Forestry.TreeComponentSpec)`: `System.Boolean`

**Timberborn.GameCycleSystem**

* type `Timberborn.GameCycleSystem.CycleStartedEvent`
  * method `get_Cycle()`: `System.Int32`
* type `Timberborn.GameCycleSystem.GameCycleService`
  * method `get_Cycle()`: `System.Int32`
  * method `get_CycleDay()`: `System.Int32`

**Timberborn.GameFactionSystem**

* type `Timberborn.GameFactionSystem.FactionService`
  * method `get_Current()`: `Timberborn.FactionSystem.FactionSpec`

**Timberborn.Goods**

* type `Timberborn.Goods.GoodAmount`
  * method `get_Amount()`: `System.Int32`
* type `Timberborn.Goods.GoodAmountSpec`
  * method `get_Amount()`: `System.Int32`

**Timberborn.Growing**

* type `Timberborn.Growing.Growable`
  * method `IncreaseGrowthProgress(System.Single)`
  * method `get_IsGrown()`: `System.Boolean`

**Timberborn.Localization**

* type `Timberborn.Localization.ILoc`
  * method `T(System.String)`: `System.String`
  * method `T<1>(System.String, !!0)`: `System.String`
  * method `T<2>(System.String, !!0, !!1)`: `System.String`
  * method `T<3>(System.String, !!0, !!1, !!2)`: `System.String`

**Timberborn.NaturalResources**

* type `Timberborn.NaturalResources.NaturalResource`
* type `Timberborn.NaturalResources.NaturalResourceFactory`
  * method `SpawnIgnoringConstraints(System.String, UnityEngine.Vector3Int)`: `Timberborn.NaturalResources.NaturalResource`

**Timberborn.NaturalResourcesLifecycle**

* type `Timberborn.NaturalResourcesLifecycle.DyingNaturalResource`
  * method `get_IsDying()`: `System.Boolean`
* type `Timberborn.NaturalResourcesLifecycle.LivingNaturalResource`
  * method `Die()`
  * method `get_IsDead()`: `System.Boolean`

**Timberborn.Planting**

* type `Timberborn.Planting.PlantingService`
  * method `GetResourceAt(UnityEngine.Vector3Int)`: `System.String`
  * method `SetPlantingCoordinates(UnityEngine.Vector3Int, System.String)`

**Timberborn.SingletonSystem**

* type `Timberborn.SingletonSystem.EventBus`
  * method `Register(System.Object)`
* type `Timberborn.SingletonSystem.ILoadableSingleton`
* type `Timberborn.SingletonSystem.IPostLoadableSingleton`
* type `Timberborn.SingletonSystem.IUpdatableSingleton`
* type `Timberborn.SingletonSystem.OnEventAttribute`
  * method `.ctor()`

**Timberborn.TemplateInstantiation**

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
* type `Timberborn.TemplateSystem.TemplateSpec`
  * method `get_TemplateName()`: `System.String`

**Timberborn.TickSystem**

* type `Timberborn.TickSystem.ITickableSingleton`

**Timberborn.TimeSystem**

* type `Timberborn.TimeSystem.IDayNightCycle`
  * method `get_HoursPassedToday()`: `System.Single`
  * method `get_PartialDayNumber()`: `System.Single`
* type `Timberborn.TimeSystem.ITimeTrigger`
  * method `Pause()`
  * method `Resume()`
  * method `get_InProgress()`: `System.Boolean`

**Timberborn.TooltipSystem**

* type `Timberborn.TooltipSystem.ITooltipRegistrar`
  * method `RegisterUpdatable(UnityEngine.UIElements.VisualElement, System.Func`1<System.String>)`

**Timberborn.UILayoutSystem**

* type `Timberborn.UILayoutSystem.ShowPrimaryUIEvent`
* type `Timberborn.UILayoutSystem.UILayout`
  * method `AddTopRight(UnityEngine.UIElements.VisualElement, System.Int32)`

**Timberborn.Yielding**

* type `Timberborn.Yielding.Yielder`
  * method `get_IsYieldRemoved()`: `System.Boolean`
  * method `get_Yield()`: `Timberborn.Goods.GoodAmount`
* type `Timberborn.Yielding.YielderSpec`
  * method `get_Yield()`: `Timberborn.Goods.GoodAmountSpec`

**UnityEngine.CoreModule**

* type `UnityEngine.Component`
  * method `GetComponentsInChildren<1>(System.Boolean)`: `!!0[]`
* type `UnityEngine.Debug`
  * method `Log(System.Object)`
  * method `LogError(System.Object)`
  * method `LogWarning(System.Object)`
* type `UnityEngine.GameObject`
  * method `GetComponentsInChildren<1>(System.Boolean)`: `!!0[]`
* type `UnityEngine.Material`
  * method `SetFloat(System.String, System.Single)`
* type `UnityEngine.Mathf`
  * method `CeilToInt(System.Single)`: `System.Int32`
  * method `Max(System.Single, System.Single)`: `System.Single`
* type `UnityEngine.Object`
  * method `get_name()`: `System.String`
* type `UnityEngine.Renderer`
  * method `get_material()`: `UnityEngine.Material`
* type `UnityEngine.Time`
  * method `get_unscaledTime()`: `System.Single`
* type `UnityEngine.Transform`
* type `UnityEngine.Vector3Int`
  * method `get_x()`: `System.Int32`
  * method `get_y()`: `System.Int32`
  * method `get_z()`: `System.Int32`
  * method `get_zero()`: `UnityEngine.Vector3Int`

**UnityEngine.UIElementsModule**

* type `UnityEngine.UIElements.Button`
  * method `.ctor()`
  * method `add_clicked(System.Action)`
* type `UnityEngine.UIElements.CallbackEventHandler`
  * method `RegisterCallback<1>(UnityEngine.UIElements.EventCallback`1<!!0>, UnityEngine.UIElements.TrickleDown)`
* type `UnityEngine.UIElements.ClickEvent`
* type `UnityEngine.UIElements.DisplayStyle`
* type `UnityEngine.UIElements.EventCallback`1`
  * method `.ctor(System.Object, System.IntPtr)`
* type `UnityEngine.UIElements.IStyle`
  * method `set_display(UnityEngine.UIElements.StyleEnum`1<UnityEngine.UIElements.DisplayStyle>)`
  * method `set_whiteSpace(UnityEngine.UIElements.StyleEnum`1<UnityEngine.UIElements.WhiteSpace>)`
* type `UnityEngine.UIElements.Label`
  * method `.ctor()`
* type `UnityEngine.UIElements.StyleEnum`1`
  * method `op_Implicit(!0)`: `UnityEngine.UIElements.StyleEnum`1<!0>`
* type `UnityEngine.UIElements.TextElement`
  * method `set_text(System.String)`
* type `UnityEngine.UIElements.TrickleDown`
* type `UnityEngine.UIElements.UQueryExtensions`
  * method `Q<1>(UnityEngine.UIElements.VisualElement, System.String, System.String)`: `!!0`
* type `UnityEngine.UIElements.VisualElement`
  * method `.ctor()`
  * method `Add(UnityEngine.UIElements.VisualElement)`
  * method `AddToClassList(System.String)`
  * method `get_style()`: `UnityEngine.UIElements.IStyle`
  * method `set_name(System.String)`
* type `UnityEngine.UIElements.WhiteSpace`

**Game classes derived from and interfaces implemented** (with the abstract members each had at build time; a new one keeps the module from loading)

* class `Bindito.Core.Configurator`: `Configure`
* interface `Bindito.Core.IProvider`1`: `Get`
* class `Timberborn.BaseComponentSystem.BaseComponent`
* interface `Timberborn.BaseComponentSystem.IAwakableComponent`: `Awake`
* interface `Timberborn.EntityPanelSystem.IEntityPanelFragment`: `ClearFragment`, `InitializeFragment`, `ShowFragment`, `UpdateFragment`
* interface `Timberborn.EntitySystem.IDeletableEntity`: `DeleteEntity`
* interface `Timberborn.EntitySystem.IPostInitializableEntity`: `PostInitializeEntity`
* interface `Timberborn.SingletonSystem.ILoadableSingleton`: `Load`
* interface `Timberborn.SingletonSystem.IPostLoadableSingleton`: `PostLoad`
* interface `Timberborn.SingletonSystem.IUpdatableSingleton`: `UpdateSingleton`
* interface `Timberborn.TickSystem.ITickableSingleton`: `Tick`

<!-- api:end -->
