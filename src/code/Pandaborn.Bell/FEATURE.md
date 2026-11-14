# Pandaborn.Bell - the afternoon bell

DESIGN.md Pillar 3. The working-hours slider is vanilla and a new game starts where vanilla does. Inkpaws that work a
short day are rested: they work **and walk** faster. The bonus depends on the length of the working day, read from the
slider **at dawn** (moving the slider during the day changes nothing until the next morning), through
`PandabornBellSpec` on the faction's adult character template:

* `WorkingSpeedCurve`, `MovementSpeedCurve`: points `{Hours, Bonus}`, piecewise linear, flat beyond the ends. Default
  +0.33 at 12 h or fewer, 0 at 16 h, 0 above.
* `SuggestionDay` (4) and `SuggestionLocKey`: the one-time message, posted at that dawn or when the first building with
  `PandabornBellSettledMarkerSpec` (hammock, teahouse) is finished, whichever comes first.

**The bonus multiplies.** Game bonuses add (one sum per bonus id in `BonusManager`), so a flat +0.33 would be worth less
and less as wellbeing bonuses grow. `BellRestedBonus` adds `d = m x b`, where `m` is the colonist's multiplier without the
bell, and recomputes `d` whenever any other bonus of that id changes (`BonusValueChanged`): it removes its own share,
reads the multiplier, and puts the new share back. The result is `m x (1 + b)` exactly, unless `m` is clamped by the
bonus type's limits. The vanilla `MovementSpeed` cap is 2.0 (`BonusTypes/BonusType.MovementSpeed`), so above about
wellbeing 50 the walking half would be cut; Inkpaws games raise the cap with a faction blueprint modifier (verified in
stage 0, see docs/tech/stage0.md).

**Shown** as a line under the working-hours panel ("Rested +33%", or "Rested +33%; tomorrow +0%" after the slider has
moved), with a tooltip; as a line on an Inkpaw's panel; and inside the vanilla wellbeing bonus totals.

**Saved**: `PandabornStore` entry `Bell` v1, `locked=<hours>;suggested=<0|1>`. Bonuses are not saved (the game rebuilds
them), so with the module off colonists have vanilla speeds and the entry is carried through saves unchanged.

**Fails safely**: module off means vanilla speeds and no panel line, and `Pandaborn.Core` posts a notice. The teahouse
marker is inert. Interface pieces sit behind `SafeUi`.

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
  * method `ToExisting<1>()`
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
* type `Timberborn.BaseComponentSystem.IAwakableComponent`

**Timberborn.Beavers**

* type `Timberborn.Beavers.AdultSpec`

**Timberborn.BlockSystem**

* type `Timberborn.BlockSystem.IFinishedStateListener`

**Timberborn.BlueprintSystem**

* type `Timberborn.BlueprintSystem.Blueprint`
  * method `GetSpec<1>()`
* type `Timberborn.BlueprintSystem.ComponentSpec`
  * method `get_Blueprint()`

**Timberborn.BonusSystem**

* type `Timberborn.BonusSystem.BonusManager`
  * method `AddBonus(System.String, System.Single)`
  * method `Multiplier(System.String)`
  * method `RemoveBonus(System.String, System.Single)`
  * method `add_BonusValueChanged(System.EventHandler`1<Timberborn.BonusSystem.BonusValueChangedEventArgs>)`
  * method `remove_BonusValueChanged(System.EventHandler`1<Timberborn.BonusSystem.BonusValueChangedEventArgs>)`
* type `Timberborn.BonusSystem.BonusValueChangedEventArgs`
  * method `get_BonusId()`

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

* type `Timberborn.EntitySystem.IDeletableEntity`
* type `Timberborn.EntitySystem.IPostInitializableEntity`
* type `Timberborn.EntitySystem.LabeledEntity`
  * method `get_DisplayName()`

**Timberborn.Localization**

* type `Timberborn.Localization.ILoc`
  * method `T(System.String)`
  * method `T<1>(System.String, !!0)`
  * method `T<2>(System.String, !!0, !!1)`
  * method `T<3>(System.String, !!0, !!1, !!2)`

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

* type `Timberborn.TemplateSystem.TemplateService`
  * method `GetAll<1>()`

**Timberborn.TimeSystem**

* type `Timberborn.TimeSystem.DaytimeStartEvent`
* type `Timberborn.TimeSystem.IDayNightCycle`
  * method `get_DayNumber()`

**Timberborn.TooltipSystem**

* type `Timberborn.TooltipSystem.ITooltipRegistrar`
  * method `RegisterUpdatable(UnityEngine.UIElements.VisualElement, System.Func`1<System.String>)`

**Timberborn.UILayoutSystem**

* type `Timberborn.UILayoutSystem.ShowPrimaryUIEvent`
* type `Timberborn.UILayoutSystem.UILayout`
  * method `AddTopRight(UnityEngine.UIElements.VisualElement, System.Int32)`

**Timberborn.WorkSystem**

* type `Timberborn.WorkSystem.WorkingHoursChangedEvent`
* type `Timberborn.WorkSystem.WorkingHoursManager`
  * method `get_WorkedPartOfDay()`

**UnityEngine.CoreModule**

* type `UnityEngine.Debug`
  * method `Log(System.Object)`
  * method `LogError(System.Object)`
* type `UnityEngine.Mathf`
  * method `Abs(System.Single)`
  * method `CeilToInt(System.Single)`
  * method `Clamp(System.Int32, System.Int32, System.Int32)`
  * method `RoundToInt(System.Single)`

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
