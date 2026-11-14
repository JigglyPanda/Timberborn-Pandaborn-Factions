# Pandaborn.Core - always-loaded services

* `FeatureRegistry`: which units the bootstrap loaded and why the others are off (read from AppDomain data).
* `PandabornStore`: the save carrier, one saved singleton `Pandaborn.Store` with a versioned text entry per feature;
  entries of features that are off are carried through saves unchanged.
* `FeatureNotices`, `Messenger`: the player is told once per save when a feature is off or the mod is enabled twice
  (toast plus notification log).
* `SafeUi`: guard for interface code.

<!-- api:begin -->
<!-- Generated from the compiled module by Pandaborn.ApiScan on every build. Do not edit by hand. -->

### Game API this module references

**Bindito.Core**

* type `Bindito.Core.Configurator`
  * method `.ctor()`
  * method `Bind<1>()`
* type `Bindito.Core.ContextAttribute`
  * method `.ctor(System.String)`
* type `Bindito.Core.IExportAssignee`
* type `Bindito.Core.IScopeAssignee`
  * method `AsSingleton()`
* type `Bindito.Core.ISingleBindingBuilder`1`

**Timberborn.BaseComponentSystem**

* type `Timberborn.BaseComponentSystem.BaseComponent`

**Timberborn.Common**

* type `Timberborn.Common.ReadOnlyList`1`

**Timberborn.GameDistricts**

* type `Timberborn.GameDistricts.DistrictCenter`
* type `Timberborn.GameDistricts.DistrictCenterRegistry`
  * method `get_AllDistrictCenters()`
  * method `get_FinishedDistrictCenters()`

**Timberborn.Localization**

* type `Timberborn.Localization.ILoc`
  * method `T(System.String)`
  * method `T<1>(System.String, !!0)`
  * method `T<2>(System.String, !!0, !!1)`

**Timberborn.NotificationSystem**

* type `Timberborn.NotificationSystem.NotificationBus`
  * method `Post(System.String, Timberborn.BaseComponentSystem.BaseComponent)`

**Timberborn.Persistence**

* type `Timberborn.Persistence.IObjectLoader`
  * method `Get(Timberborn.Persistence.ListKey`1<System.String>)`
  * method `Has<1>(Timberborn.Persistence.ListKey`1<!!0>)`
* type `Timberborn.Persistence.IObjectSaver`
  * method `Set(Timberborn.Persistence.ListKey`1<System.String>, System.Collections.Generic.IReadOnlyCollection`1<System.String>)`
* type `Timberborn.Persistence.ListKey`1`
  * method `.ctor(System.String)`

**Timberborn.QuickNotificationSystem**

* type `Timberborn.QuickNotificationSystem.QuickNotificationService`
  * method `SendNotification(System.String)`
  * method `SendWarningNotification(System.String)`

**Timberborn.SingletonSystem**

* type `Timberborn.SingletonSystem.EventBus`
  * method `Register(System.Object)`
* type `Timberborn.SingletonSystem.ILoadableSingleton`
* type `Timberborn.SingletonSystem.OnEventAttribute`
  * method `.ctor()`

**Timberborn.UILayoutSystem**

* type `Timberborn.UILayoutSystem.ShowPrimaryUIEvent`

**Timberborn.WorldPersistence**

* type `Timberborn.WorldPersistence.ISaveableSingleton`
* type `Timberborn.WorldPersistence.ISingletonLoader`
  * method `TryGetSingleton(Timberborn.WorldPersistence.SingletonKey, Timberborn.Persistence.IObjectLoader&)`
* type `Timberborn.WorldPersistence.ISingletonSaver`
  * method `GetSingleton(Timberborn.WorldPersistence.SingletonKey)`
* type `Timberborn.WorldPersistence.SingletonKey`
  * method `.ctor(System.String)`

**UnityEngine.CoreModule**

* type `UnityEngine.Debug`
  * method `Log(System.Object)`
  * method `LogError(System.Object)`
  * method `LogWarning(System.Object)`

<!-- api:end -->
