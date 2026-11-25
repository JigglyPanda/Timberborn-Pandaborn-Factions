# Pandaborn.Tutorial - tutorial step types for the faction tutorial

The tutorial itself is data (`catalogue/tutorial.toml`, docs/tech/tutorial.md). This module adds the step types vanilla
lacks; today one:

* `PandabornGoodAmountStepSpec { GoodId, Amount }`: "Have 20 Poles (7/20)", achieved while the settlement's available
  stock of the good reaches the amount (`ResourceCountingService.GetGlobalResourceCount(..).AvailableStock`, all finished
  districts). Text `Pandaborn.Tutorial.HaveGoods` (`mod/Localizations/enUS_PandabornTutorialSteps.csv`).

Bound with `MultiBind<IStepDeserializer>`; no saved state (the game saves only finished tutorial ids and re-checks steps
on load).

**Fails safely**: with the module off the game drops steps no reader accepts, so a stage keeps its other steps. A good the
faction lacks reads as its id and is never achieved; nothing throws.

A step is built while `TutorialService` loads every stage, so its constructor contains its own failures: a good that
cannot be read is an unknown good, never a failed load.

<!-- api:begin -->
<!-- Generated from the compiled module by Pandaborn.ApiScan on every build. Do not edit by hand. -->

### Game API this module references

**Bindito.Core**

* type `Bindito.Core.Configurator`
  * method `.ctor()`
  * method `MultiBind<1>()`: `Bindito.Core.IMultiBindingBuilder`1<!!0>`
* type `Bindito.Core.ContextAttribute`
  * method `.ctor(System.String)`
* type `Bindito.Core.IBindingBuilder`1`
  * method `To<1>()`: `Bindito.Core.IScopeAssignee`
* type `Bindito.Core.IExportAssignee`
* type `Bindito.Core.IMultiBindingBuilder`1`
* type `Bindito.Core.IScopeAssignee`
  * method `AsSingleton()`: `Bindito.Core.IExportAssignee`

**Timberborn.BlueprintSystem**

* type `Timberborn.BlueprintSystem.Blueprint`
  * method `get_Specs()`: `System.Collections.Immutable.ImmutableArray`1<Timberborn.BlueprintSystem.ComponentSpec>`
* type `Timberborn.BlueprintSystem.ComponentSpec`

**Timberborn.Goods**

* type `Timberborn.Goods.GoodSpec`
  * method `get_PluralDisplayName()`: `Timberborn.LocalizationSerialization.LocalizedText`
  * method `op_Inequality(Timberborn.Goods.GoodSpec, Timberborn.Goods.GoodSpec)`: `System.Boolean`
* type `Timberborn.Goods.IGoodService`
  * method `GetGoodOrNull(System.String)`: `Timberborn.Goods.GoodSpec`

**Timberborn.Localization**

* type `Timberborn.Localization.ILoc`
  * method `T<3>(System.String, !!0, !!1, !!2)`: `System.String`

**Timberborn.LocalizationSerialization**

* type `Timberborn.LocalizationSerialization.LocalizedText`
  * method `get_Value()`: `System.String`

**Timberborn.ResourceCountingSystem**

* type `Timberborn.ResourceCountingSystem.ResourceCount`
  * method `get_AvailableStock()`: `System.Int32`
* type `Timberborn.ResourceCountingSystem.ResourceCountingService`
  * method `GetGlobalResourceCount(System.String)`: `Timberborn.ResourceCountingSystem.ResourceCount`

**Timberborn.TutorialSystem**

* type `Timberborn.TutorialSystem.IStepDeserializer`
* type `Timberborn.TutorialSystem.ITutorialStep`
* type `Timberborn.TutorialSystem.TutorialStep`
  * method `Create(Timberborn.TutorialSystem.ITutorialStep, System.Action`1<System.Boolean>, System.String, System.String)`: `Timberborn.TutorialSystem.TutorialStep`

**UnityEngine.CoreModule**

* type `UnityEngine.Debug`
  * method `LogWarning(System.Object)`

**Game classes derived from and interfaces implemented** (with the abstract members each had at build time; a new one keeps the module from loading)

* class `Bindito.Core.Configurator`: `Configure`
* interface `Timberborn.TutorialSystem.IStepDeserializer`: `TryDeserialize`
* interface `Timberborn.TutorialSystem.ITutorialStep`: `Achieved`, `Description`

<!-- api:end -->
