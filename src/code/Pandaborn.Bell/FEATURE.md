# Pandaborn.Bell

(What this module does, its data, and how it fails safely. Hand-written; the section below is generated.)

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
