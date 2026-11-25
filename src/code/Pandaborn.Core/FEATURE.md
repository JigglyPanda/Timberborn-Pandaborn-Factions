# Pandaborn.Core - always-loaded services

* `FeatureRegistry`: which units the bootstrap loaded and why the others are off (read from AppDomain data); what
  features report about themselves: `ReportNoData` (this game), `ReportDegradedInGame` (this game: forgotten when the
  next game starts) and `ReportDegraded` (until the game is closed, for something a feature reports once per session).
* `PandabornStore` (per game) and `PandabornEntityState` (per entity): the save carriers, versioned text entries
  `feature|version|payload`. An entry read from a save is written back exactly as it was until its feature sets a new
  value, and so are lines this version cannot read (`StoreEntries`): the data of a feature that is off, or written by a
  newer version of the mod, survives a save made by this one byte for byte. A game where no feature writes anything
  (every Folktails game) saves no store. `Payload` values of any length round-trip.
* `FeatureNotices`, `Messenger`, `NoticePlan`: what the player is told. **Nothing while everything works.** Otherwise
  one message (warning toast plus notification-log entry) in games of our faction, naming each feature in player words
  and saying what will not work (`Pandaborn.Feature.<Id>` and `Pandaborn.Feature.<Id>.Off`,
  `Localizations/enUS_PandabornCoreNotices.csv`): for a feature that is switched off (failed its check against this game
  version, or its file is missing) at every load; for everything else (reduced mode, no data, a developer or player
  switch, the mod enabled twice) once per save and again when the set of problems changes; also during play when a
  feature reports a new state. The save remembers what it was told in store entry `Core.Notices` v2 (a signature;
  removed when all is well). The full state of every unit, with technical reasons, is logged at every load
  (`FeatureNotices.LastReport`).
* `SafeUi`: guard for interface code; a failed piece is off until the game is left (the next game tries again).
* `PandabornSounds`, `IWorkdayClock`, `INightShiftClock` (the Ringtails lane's seam for the night shift's length).

Statics hold only what must outlive a game (the boot report, session-level degraded states) or is cleared when a game
starts (`FeatureRegistry.StartGame`, `SafeUi.StartGame`, called from `FeatureNotices`' constructor); test lists are capped.

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
* type `Bindito.Core.IExportAssignee`
* type `Bindito.Core.IMultiBindingBuilder`1`
* type `Bindito.Core.IScopeAssignee`
  * method `AsSingleton()`: `Bindito.Core.IExportAssignee`
  * method `AsTransient()`: `Bindito.Core.IExportAssignee`
* type `Bindito.Core.ISingleBindingBuilder`1`

**Timberborn.BaseComponentSystem**

* type `Timberborn.BaseComponentSystem.BaseComponent`
  * method `.ctor()`
  * method `op_Implicit(Timberborn.BaseComponentSystem.BaseComponent)`: `System.Boolean`

**Timberborn.Common**

* type `Timberborn.Common.ReadOnlyList`1`

**Timberborn.FactionSystem**

* type `Timberborn.FactionSystem.FactionSpec`
  * method `get_Id()`: `System.String`

**Timberborn.GameDistricts**

* type `Timberborn.GameDistricts.DistrictCenter`
* type `Timberborn.GameDistricts.DistrictCenterRegistry`
  * method `get_AllDistrictCenters()`: `Timberborn.Common.ReadOnlyList`1<Timberborn.GameDistricts.DistrictCenter>`
  * method `get_FinishedDistrictCenters()`: `Timberborn.Common.ReadOnlyList`1<Timberborn.GameDistricts.DistrictCenter>`

**Timberborn.GameFactionSystem**

* type `Timberborn.GameFactionSystem.FactionService`
  * method `get_Current()`: `Timberborn.FactionSystem.FactionSpec`

**Timberborn.Localization**

* type `Timberborn.Localization.ILoc`
  * method `T(System.String)`: `System.String`
  * method `T<1>(System.String, !!0)`: `System.String`
  * method `T<2>(System.String, !!0, !!1)`: `System.String`

**Timberborn.NotificationSystem**

* type `Timberborn.NotificationSystem.NotificationBus`
  * method `Post(System.String, Timberborn.BaseComponentSystem.BaseComponent)`

**Timberborn.Persistence**

* type `Timberborn.Persistence.IObjectLoader`
  * method `Get(Timberborn.Persistence.ListKey`1<System.String>)`: `System.Collections.Generic.List`1<System.String>`
  * method `Has<1>(Timberborn.Persistence.ListKey`1<!!0>)`: `System.Boolean`
* type `Timberborn.Persistence.IObjectSaver`
  * method `Set(Timberborn.Persistence.ListKey`1<System.String>, System.Collections.Generic.IReadOnlyCollection`1<System.String>)`
* type `Timberborn.Persistence.ListKey`1`
  * method `.ctor(System.String)`

**Timberborn.QuickNotificationSystem**

* type `Timberborn.QuickNotificationSystem.QuickNotificationService`
  * method `SendNotification(System.String)`
  * method `SendWarningNotification(System.String)`

**Timberborn.RootProviders**

* type `Timberborn.RootProviders.RootObjectProvider`
  * method `CreateRootObject(System.String)`: `UnityEngine.GameObject`

**Timberborn.SingletonSystem**

* type `Timberborn.SingletonSystem.EventBus`
  * method `Register(System.Object)`
* type `Timberborn.SingletonSystem.ILoadableSingleton`
* type `Timberborn.SingletonSystem.OnEventAttribute`
  * method `.ctor()`

**Timberborn.SoundSystem**

* type `Timberborn.SoundSystem.AudioClipService`
  * method `GetAudioClipNames(System.String)`: `System.Collections.Generic.IEnumerable`1<System.String>`
* type `Timberborn.SoundSystem.ISoundSystem`
  * method `PlaySound2D(UnityEngine.GameObject, System.String, System.Int32)`
  * method `PlaySound3D(UnityEngine.GameObject, System.String, System.Int32)`

**Timberborn.TemplateInstantiation**

* type `Timberborn.TemplateInstantiation.TemplateModule`
* type `Timberborn.TemplateInstantiation.TemplateModule+Builder`
  * method `.ctor()`
  * method `AddDecorator<2>()`
  * method `Build()`: `Timberborn.TemplateInstantiation.TemplateModule`

**Timberborn.UILayoutSystem**

* type `Timberborn.UILayoutSystem.ShowPrimaryUIEvent`

**Timberborn.WorldPersistence**

* type `Timberborn.WorldPersistence.ComponentKey`
  * method `.ctor(System.String)`
* type `Timberborn.WorldPersistence.IEntityLoader`
  * method `GetComponent(Timberborn.WorldPersistence.ComponentKey)`: `Timberborn.Persistence.IObjectLoader`
  * method `HasComponent(Timberborn.WorldPersistence.ComponentKey)`: `System.Boolean`
* type `Timberborn.WorldPersistence.IEntitySaver`
  * method `GetComponent(Timberborn.WorldPersistence.ComponentKey)`: `Timberborn.Persistence.IObjectSaver`
* type `Timberborn.WorldPersistence.IPersistentEntity`
* type `Timberborn.WorldPersistence.ISaveableSingleton`
* type `Timberborn.WorldPersistence.ISingletonLoader`
  * method `TryGetSingleton(Timberborn.WorldPersistence.SingletonKey, Timberborn.Persistence.IObjectLoader&)`: `System.Boolean`
* type `Timberborn.WorldPersistence.ISingletonSaver`
  * method `GetSingleton(Timberborn.WorldPersistence.SingletonKey)`: `Timberborn.Persistence.IObjectSaver`
* type `Timberborn.WorldPersistence.SingletonKey`
  * method `.ctor(System.String)`

**UnityEngine.CoreModule**

* type `UnityEngine.Debug`
  * method `Log(System.Object)`
  * method `LogError(System.Object)`
  * method `LogWarning(System.Object)`
* type `UnityEngine.GameObject`
* type `UnityEngine.Object`
  * method `op_Implicit(UnityEngine.Object)`: `System.Boolean`

**Game classes derived from and interfaces implemented** (with the abstract members each had at build time; a new one keeps the module from loading)

* class `Bindito.Core.Configurator`: `Configure`
* class `Timberborn.BaseComponentSystem.BaseComponent`
* interface `Timberborn.SingletonSystem.ILoadableSingleton`: `Load`
* interface `Timberborn.WorldPersistence.IPersistentEntity`: `Load`, `Save`
* interface `Timberborn.WorldPersistence.ISaveableSingleton`: `Save`

<!-- api:end -->
