# Pandaborn.RingtailsFallback - night posts without the Ringtails

The data-alone rule for night posts (docs/tech/two-peoples.md, "For the catalogue lane"). Night posts keep the vanilla
`Beaver` worker type in data; the Ringtails module switches them to `PandabornRingtail`. A save keeps that type. If the
Ringtails module is then off (its API check failed, or forced off) or degraded (its private-member check failed), this
module switches every such post back to `Beaver` with the public `WorkplaceWorkerType.SetWorkerType`, so it is an ordinary
Inkpaw-staffed workplace. Saved Ringtails load as Inkpaws through the template alias. With the Ringtails module on, it
does nothing.

Kept separate from `Pandaborn.Ringtails` on purpose: its required API is a handful of public members, so it still loads
when the larger module does not. It keeps no state.

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
* type `Bindito.Core.IExportAssignee`
* type `Bindito.Core.IMultiBindingBuilder`1`
* type `Bindito.Core.IScopeAssignee`
  * method `AsSingleton()`: `Bindito.Core.IExportAssignee`
  * method `AsTransient()`: `Bindito.Core.IExportAssignee`
* type `Bindito.Core.ISingleBindingBuilder`1`

**Timberborn.BaseComponentSystem**

* type `Timberborn.BaseComponentSystem.BaseComponent`
  * method `.ctor()`
  * method `GetComponent<1>()`: `!!0`
  * method `get_Name()`: `System.String`
* type `Timberborn.BaseComponentSystem.IAwakableComponent`

**Timberborn.BlockSystem**

* type `Timberborn.BlockSystem.BlockObject`
  * method `get_IsFinished()`: `System.Boolean`
* type `Timberborn.BlockSystem.IFinishedStateListener`

**Timberborn.EntitySystem**

* type `Timberborn.EntitySystem.IPostInitializableEntity`

**Timberborn.TemplateInstantiation**

* type `Timberborn.TemplateInstantiation.TemplateModule`
* type `Timberborn.TemplateInstantiation.TemplateModule+Builder`
  * method `.ctor()`
  * method `AddDecorator<2>()`
  * method `Build()`: `Timberborn.TemplateInstantiation.TemplateModule`

**Timberborn.WorkSystem**

* type `Timberborn.WorkSystem.WorkplaceWorkerType`
  * method `SetWorkerType(System.String)`
  * method `get_WorkerType()`: `System.String`

**UnityEngine.CoreModule**

* type `UnityEngine.Debug`
  * method `Log(System.Object)`
  * method `LogError(System.Object)`

**Game classes derived from and interfaces implemented** (with the abstract members each had at build time; a new one keeps the module from loading)

* class `Bindito.Core.Configurator`: `Configure`
* class `Timberborn.BaseComponentSystem.BaseComponent`
* interface `Timberborn.BaseComponentSystem.IAwakableComponent`: `Awake`
* interface `Timberborn.BlockSystem.IFinishedStateListener`: `OnEnterFinishedState`, `OnExitFinishedState`
* interface `Timberborn.EntitySystem.IPostInitializableEntity`: `PostInitializeEntity`

<!-- api:end -->
