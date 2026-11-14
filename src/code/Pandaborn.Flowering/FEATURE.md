# Pandaborn.Flowering - the Great Flowering

DESIGN.md Pillar 5; full design, player timeline, the fairness arithmetic and test results in `docs/tech/events.md`.
**Status: in `Pandaborn.Code.sln` and `modules.txt`; ships when `catalogue/rules.toml [modules] Flowering` is on** (the
catalogue already carries its data behind that switch). Dev copies: `proto/events/build.ps1`.

**What it does.** One bamboo species flowers per Flowering, in the order of `PandabornFloweringSpec.Species`, alternating.

* **Schedule**: never before `FirstCycle` (6; "rare" adds `RareDelayCycles`), then every `NormalMinCycles`..`NormalMaxCycles`
  cycles (rare: `RareMinCycles`..`RareMaxCycles`); the chosen cycle is saved. A Flowering happens at the start of a cycle,
  which is always temperate weather, so never in a drought or badtide.
* **Announced a full cycle ahead**, at the start of the cycle before (if announced later, by a load or a setting change, it
  moves one cycle further): a notice, a line under the top bar with the advice in its tooltip, a line on every bamboo's
  panel, and buds on the plants where the plant's spec says they are painted in its detail map (`BudsUseDetail`).
* **The Flowering**: every grown plant of the species, planted or wild, is replaced by its `InFlowerTemplate` twin (whose
  harvest, its cut yield in data, is bamboo seed) at the same tile; young plants die. The twins die over the last day of
  `SeedDays` (3). Farmers and lumberjacks take the seed with their ordinary harvest, because the seed is a yield of their
  resource group; crops that die unharvested lose it (the game's rule), dead twin trees keep it until cut.
* **The rest**: until `DormantDays` (9) after the Flowering, young plants of the species do not grow. The planting marks
  stay, so farms and foresters replant on their own; the seedlings start growing when the rest ends.
* **Setting** per save: normal, rare or off, in a game dialog opened from the top-bar line or any bamboo's panel. No other
  mod needed.

**Data it needs** (catalogue): `PandabornFloweringSpec` on the Inkpaw adult template; `PandabornFloweringPlantSpec` on the
two bamboos; the two twins (`PandabornShootBambooInFlower.Inkpaws`, `PandabornTimberBambooInFlower.Inkpaws`) with
`PandabornInFlowerSpec`, in `NaturalResources.Inkpaws`.

**Saved**: `PandabornStore` entry `Flowering` v1: `setting`, `phase` (Idle/Announced/Flowering/Resting), `next` (cycle),
`nextSpecies`, `species`, `day` (when it flowered), `last` (cycle). The twins are ordinary saved plants. The growth holds
are not saved: the game saves growth progress as always, and the service holds the plants again after a load.

**Fails safely.**
* Module off: no announcements and no Flowering. Twins already in a save stay ordinary plants whose harvest is seed and
  never die by themselves; young bamboo grows at once. The store entry is carried unchanged; when the module is back it
  picks up where the save left off (an announced Flowering whose date passed moves to the next cycle start).
* `Growable._timeTrigger` (private) gone, or `simulate-missing-member: Flowering.GrowthHold`: young bamboo regrows at once
  after a Flowering (milder, never harsher); reported through `FeatureRegistry.ReportDegraded("Flowering", ...)`.
* A game of our faction without the data gets `FeatureRegistry.ReportNoData`.
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
  * method `GetComponent<1>()`
  * method `get_GameObject()`
  * method `op_Implicit(Timberborn.BaseComponentSystem.BaseComponent)`
* type `Timberborn.BaseComponentSystem.IAwakableComponent`

**Timberborn.Beavers**

* type `Timberborn.Beavers.AdultSpec`

**Timberborn.BlockSystem**

* type `Timberborn.BlockSystem.BlockObject`
  * method `get_Coordinates()`

**Timberborn.BlueprintSystem**

* type `Timberborn.BlueprintSystem.Blueprint`
  * method `GetSpec<1>()`
* type `Timberborn.BlueprintSystem.ComponentSpec`
  * method `GetSpec<1>()`
  * method `get_Blueprint()`

**Timberborn.CoreUI**

* type `Timberborn.CoreUI.DialogBox`
* type `Timberborn.CoreUI.DialogBoxShower`
  * method `Create()`
* type `Timberborn.CoreUI.DialogBoxShower+Builder`
  * method `AddContent(UnityEngine.UIElements.VisualElement)`
  * method `SetConfirmButton(System.Action)`
  * method `Show()`
* type `Timberborn.CoreUI.VisualElementExtensions`
  * method `ToggleDisplayStyle(UnityEngine.UIElements.VisualElement, System.Boolean)`
* type `Timberborn.CoreUI.VisualElementLoader`
  * method `LoadVisualElement(System.String)`

**Timberborn.Cutting**

* type `Timberborn.Cutting.Cuttable`
  * method `add_WasCut(System.EventHandler)`
  * method `get_RemoveOnCut()`
  * method `get_Yielder()`
  * method `get_YielderSpec()`
  * method `remove_WasCut(System.EventHandler)`

**Timberborn.EntityPanelSystem**

* type `Timberborn.EntityPanelSystem.EntityPanelModule`
* type `Timberborn.EntityPanelSystem.EntityPanelModule+Builder`
  * method `.ctor()`
  * method `AddMiddleFragment(Timberborn.EntityPanelSystem.IEntityPanelFragment, System.Int32)`
  * method `Build()`
* type `Timberborn.EntityPanelSystem.IEntityPanelFragment`

**Timberborn.EntitySystem**

* type `Timberborn.EntitySystem.EntityService`
  * method `Delete(Timberborn.BaseComponentSystem.BaseComponent)`
* type `Timberborn.EntitySystem.IDeletableEntity`
* type `Timberborn.EntitySystem.IPostInitializableEntity`
* type `Timberborn.EntitySystem.LabeledEntitySpec`
  * method `get_DisplayNameLocKey()`
  * method `op_Inequality(Timberborn.EntitySystem.LabeledEntitySpec, Timberborn.EntitySystem.LabeledEntitySpec)`

**Timberborn.FactionSystem**

* type `Timberborn.FactionSystem.FactionSpec`
  * method `get_Id()`

**Timberborn.Forestry**

* type `Timberborn.Forestry.TreeComponentSpec`
  * method `op_Inequality(Timberborn.Forestry.TreeComponentSpec, Timberborn.Forestry.TreeComponentSpec)`

**Timberborn.GameCycleSystem**

* type `Timberborn.GameCycleSystem.CycleStartedEvent`
  * method `get_Cycle()`
* type `Timberborn.GameCycleSystem.GameCycleService`
  * method `get_Cycle()`
  * method `get_CycleDay()`

**Timberborn.GameFactionSystem**

* type `Timberborn.GameFactionSystem.FactionService`
  * method `get_Current()`

**Timberborn.Goods**

* type `Timberborn.Goods.GoodAmount`
  * method `get_Amount()`
* type `Timberborn.Goods.GoodAmountSpec`
  * method `get_Amount()`

**Timberborn.Growing**

* type `Timberborn.Growing.Growable`
  * method `IncreaseGrowthProgress(System.Single)`
  * method `get_IsGrown()`

**Timberborn.Localization**

* type `Timberborn.Localization.ILoc`
  * method `T(System.String)`
  * method `T<1>(System.String, !!0)`
  * method `T<2>(System.String, !!0, !!1)`
  * method `T<3>(System.String, !!0, !!1, !!2)`

**Timberborn.NaturalResources**

* type `Timberborn.NaturalResources.NaturalResource`
* type `Timberborn.NaturalResources.NaturalResourceFactory`
  * method `SpawnIgnoringConstraints(System.String, UnityEngine.Vector3Int)`

**Timberborn.NaturalResourcesLifecycle**

* type `Timberborn.NaturalResourcesLifecycle.DyingNaturalResource`
  * method `get_IsDying()`
* type `Timberborn.NaturalResourcesLifecycle.LivingNaturalResource`
  * method `Die()`
  * method `get_IsDead()`

**Timberborn.Planting**

* type `Timberborn.Planting.PlantingService`
  * method `GetResourceAt(UnityEngine.Vector3Int)`
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
  * method `Build()`

**Timberborn.TemplateSystem**

* type `Timberborn.TemplateSystem.TemplateNameMapper`
  * method `TryGetTemplate(System.String, Timberborn.TemplateSystem.TemplateSpec&)`
* type `Timberborn.TemplateSystem.TemplateService`
  * method `GetAll<1>()`
* type `Timberborn.TemplateSystem.TemplateSpec`
  * method `get_TemplateName()`

**Timberborn.TickSystem**

* type `Timberborn.TickSystem.ITickableSingleton`

**Timberborn.TimeSystem**

* type `Timberborn.TimeSystem.IDayNightCycle`
  * method `get_HoursPassedToday()`
  * method `get_PartialDayNumber()`
* type `Timberborn.TimeSystem.ITimeTrigger`
  * method `Pause()`
  * method `Resume()`

**Timberborn.TooltipSystem**

* type `Timberborn.TooltipSystem.ITooltipRegistrar`
  * method `RegisterUpdatable(UnityEngine.UIElements.VisualElement, System.Func`1<System.String>)`

**Timberborn.UILayoutSystem**

* type `Timberborn.UILayoutSystem.ShowPrimaryUIEvent`
* type `Timberborn.UILayoutSystem.UILayout`
  * method `AddTopRight(UnityEngine.UIElements.VisualElement, System.Int32)`

**Timberborn.Yielding**

* type `Timberborn.Yielding.Yielder`
  * method `get_IsYieldRemoved()`
  * method `get_Yield()`
* type `Timberborn.Yielding.YielderSpec`
  * method `get_Yield()`

**UnityEngine.CoreModule**

* type `UnityEngine.Component`
  * method `GetComponentsInChildren<1>(System.Boolean)`
* type `UnityEngine.Debug`
  * method `Log(System.Object)`
  * method `LogError(System.Object)`
  * method `LogWarning(System.Object)`
* type `UnityEngine.GameObject`
  * method `GetComponentsInChildren<1>(System.Boolean)`
* type `UnityEngine.Material`
  * method `SetFloat(System.String, System.Single)`
* type `UnityEngine.Mathf`
  * method `CeilToInt(System.Single)`
  * method `Max(System.Single, System.Single)`
* type `UnityEngine.Object`
  * method `get_name()`
* type `UnityEngine.Renderer`
  * method `get_material()`
* type `UnityEngine.Time`
  * method `get_unscaledTime()`
* type `UnityEngine.Transform`
* type `UnityEngine.Vector3Int`
  * method `get_x()`
  * method `get_y()`
  * method `get_z()`

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
* type `UnityEngine.UIElements.FlexDirection`
* type `UnityEngine.UIElements.IStyle`
  * method `set_display(UnityEngine.UIElements.StyleEnum`1<UnityEngine.UIElements.DisplayStyle>)`
  * method `set_flexDirection(UnityEngine.UIElements.StyleEnum`1<UnityEngine.UIElements.FlexDirection>)`
  * method `set_marginTop(UnityEngine.UIElements.StyleLength)`
  * method `set_whiteSpace(UnityEngine.UIElements.StyleEnum`1<UnityEngine.UIElements.WhiteSpace>)`
* type `UnityEngine.UIElements.Label`
  * method `.ctor()`
* type `UnityEngine.UIElements.StyleEnum`1`
  * method `op_Implicit(!0)`
* type `UnityEngine.UIElements.StyleLength`
  * method `op_Implicit(System.Single)`
* type `UnityEngine.UIElements.TextElement`
  * method `set_text(System.String)`
* type `UnityEngine.UIElements.TrickleDown`
* type `UnityEngine.UIElements.UQueryExtensions`
  * method `Q<1>(UnityEngine.UIElements.VisualElement, System.String, System.String)`
* type `UnityEngine.UIElements.VisualElement`
  * method `.ctor()`
  * method `Add(UnityEngine.UIElements.VisualElement)`
  * method `AddToClassList(System.String)`
  * method `get_style()`
  * method `set_name(System.String)`
* type `UnityEngine.UIElements.WhiteSpace`

<!-- api:end -->
