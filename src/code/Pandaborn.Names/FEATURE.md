# Pandaborn.Names - faction colonist names

`PandabornNamePoolSpec { NamePoolLocKey }` on the faction's adult and child templates gives their colonists names from that
localisation entry (one name per line, like the vanilla `Beaver.NamePool`; a gloss such as "Le Le (Joy)" is shown
verbatim). `FactionNamer` is an `IEntityNamer` with priority 30, above the vanilla `BeaverEntityNamer` (20); the game's
`NamedEntity` asks the highest-priority namer once, when a colonist first gets a name, and saves the name per colonist.
A kit keeps its name when it grows up. Names are drawn without repeats until the pool is used up; what is left is kept in
`PandabornStore` entry `Names` v1.

**Fails safely**: module off means vanilla names for new colonists; existing names are saved by the game and stay.

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
* type `Bindito.Core.IExportAssignee`
* type `Bindito.Core.IMultiBindingBuilder`1`
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

**Timberborn.BlueprintSystem**

* type `Timberborn.BlueprintSystem.Blueprint`
  * method `GetSpec<1>()`
* type `Timberborn.BlueprintSystem.ComponentSpec`
  * method `get_Blueprint()`

**Timberborn.Common**

* type `Timberborn.Common.IRandomNumberGenerator`
  * method `Range(System.Int32, System.Int32)`

**Timberborn.EntityNaming**

* type `Timberborn.EntityNaming.IEntityNamer`

**Timberborn.FactionSystem**

* type `Timberborn.FactionSystem.FactionSpec`
  * method `get_Id()`

**Timberborn.GameFactionSystem**

* type `Timberborn.GameFactionSystem.FactionService`
  * method `get_Current()`

**Timberborn.Localization**

* type `Timberborn.Localization.ILoc`
  * method `T(System.String)`

**Timberborn.SingletonSystem**

* type `Timberborn.SingletonSystem.ILoadableSingleton`

**Timberborn.TemplateInstantiation**

* type `Timberborn.TemplateInstantiation.TemplateModule`
* type `Timberborn.TemplateInstantiation.TemplateModule+Builder`
  * method `.ctor()`
  * method `AddDecorator<2>()`
  * method `Build()`

**Timberborn.TemplateSystem**

* type `Timberborn.TemplateSystem.TemplateService`
  * method `GetAll<1>()`

**UnityEngine.CoreModule**

* type `UnityEngine.Debug`
  * method `LogError(System.Object)`
  * method `LogWarning(System.Object)`

<!-- api:end -->
