# Pandaborn.Names - faction colonist names

`PandabornNamePoolSpec { NamePoolLocKey }` on the faction's adult and child templates gives their colonists names from that
localisation entry (one name per line, like the vanilla `Beaver.NamePool`; a gloss such as "Le Le (Joy)" is shown
verbatim). `FactionNamer` is an `IEntityNamer` with priority 30, above the vanilla `BeaverEntityNamer` (20); the game's
`NamedEntity` asks the highest-priority namer once, when a colonist first gets a name, and saves the name per colonist.
A kit keeps its name when it grows up. Names are drawn without repeats until the pool is used up; what is left is kept in
`PandabornStore` entry `Names` v1.

**Fails safely**: module off means vanilla names for new colonists; existing names are saved by the game and stay.

## Small Inkpaw customs hosted here (`ForesterCustom.cs`, namespace `Pandaborn.Customs`)

Defaults of vanilla buildings that differ for the Inkpaws and need no data live in this assembly: of the modules that
always ship it is the one whose loss costs least (a game update that changes `Forester` switches off the names, not the
bell), and a module of its own for one checkbox would be all ceremony. They share nothing with the names.

* **Foresters replant dead trees by default** (DESIGN.md). `ForesterReplantDefault` decorates the game's `Forester`
  and, in a game of our faction only, sets `Forester.ReplantDeadTrees` in `Awake`, the first thing that happens to a new
  building. Everything later wins: a building loaded from a save gets its saved value (`Forester.Load` runs after
  `Awake`), a building made with the copy tool gets its source's value (settings are copied in `PreInitialize`), and
  the player's checkbox is the game's own setter, saved by the game. Nothing of ours is saved. Module off: new
  foresters start with the option off, as in the plain game.
* **Dead bushes are cleared for the forester** (`DeadBushClearing.cs`). The game's option replaces dead *trees*
  only: `Forester.Validate` accepts a blocked planting spot when the blocker has a `TreeComponent` that is dead. Timber
  bamboo and persimmon (basis `ChestnutTree`) are trees. Tea and Sichuan pepper are bushes (basis `BlueberryBush`:
  `BushSpec`, no `TreeComponentSpec`), so a dead one blocked its planting mark until the player demolished it. In a
  game of our faction a dead plant is now removed a day (`DelayDays`) after it was first seen waiting, and the forester
  plants the empty mark like any other. It is removed only while all of this holds at every hourly look of that day:
  it is the blocker of a planting mark (`PlantingService.TryGetPlantingBlocker`, what the game's own planters ask) and
  the mark is for its own species; it is dead, has a `Gatherable`, has no `TreeComponent` and is not marked for
  demolition; a finished forester building whose range covers the tile plants that species and has "replant dead
  trees" on. So the one checkbox governs trees and bushes, a wild bush off a mark is never touched, and kinds are found
  by data, not by name. Entities are removed only in the singleton's tick; a failure switches the piece off until the
  game is left. Nothing is saved: after a load the day starts over. Not `TreeComponentSpec` on the bushes:
  `TreeCuttingArea` tracks every `TreeComponent`, which nobody can test today. After the removal nothing else in the
  planting job refuses the tile (the blocker was the only obstacle; dry soil delays planting as it does for trees).

**Names fall back** to a random name from the game's own list when a template's pool key is missing or its pool is
empty (before: the same name for every colonist).

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
  * method `op_Implicit(Timberborn.BaseComponentSystem.BaseComponent)`: `System.Boolean`
* type `Timberborn.BaseComponentSystem.IAwakableComponent`

**Timberborn.Beavers**

* type `Timberborn.Beavers.AdultSpec`

**Timberborn.BlockSystem**

* type `Timberborn.BlockSystem.BlockObject`
* type `Timberborn.BlockSystem.IFinishedStateListener`

**Timberborn.BlueprintSystem**

* type `Timberborn.BlueprintSystem.Blueprint`
  * method `GetSpec<1>()`: `!!0`
* type `Timberborn.BlueprintSystem.ComponentSpec`
  * method `get_Blueprint()`: `Timberborn.BlueprintSystem.Blueprint`

**Timberborn.BuildingsNavigation**

* type `Timberborn.BuildingsNavigation.BuildingTerrainRange`
  * method `GetRange()`: `Timberborn.Common.ReadOnlyHashSet`1<UnityEngine.Vector3Int>`

**Timberborn.Common**

* type `Timberborn.Common.IRandomNumberGenerator`
  * method `Range(System.Int32, System.Int32)`: `System.Int32`
* type `Timberborn.Common.ReadOnlyHashSet`1`
  * method `Contains(!0)`: `System.Boolean`

**Timberborn.Demolishing**

* type `Timberborn.Demolishing.Demolishable`
  * method `get_IsMarked()`: `System.Boolean`

**Timberborn.EntityNaming**

* type `Timberborn.EntityNaming.IEntityNamer`

**Timberborn.EntitySystem**

* type `Timberborn.EntitySystem.EntityComponent`
  * method `get_Deleted()`: `System.Boolean`
  * method `get_EntityId()`: `System.Guid`
* type `Timberborn.EntitySystem.EntityService`
  * method `Delete(Timberborn.BaseComponentSystem.BaseComponent)`
* type `Timberborn.EntitySystem.IDeletableEntity`

**Timberborn.FactionSystem**

* type `Timberborn.FactionSystem.FactionSpec`
  * method `get_Id()`: `System.String`

**Timberborn.Forestry**

* type `Timberborn.Forestry.Forester`
  * method `SetReplantDeadTrees(System.Boolean)`
  * method `get_ReplantDeadTrees()`: `System.Boolean`
* type `Timberborn.Forestry.TreeComponent`

**Timberborn.GameFactionSystem**

* type `Timberborn.GameFactionSystem.FactionService`
  * method `get_Current()`: `Timberborn.FactionSystem.FactionSpec`

**Timberborn.Gathering**

* type `Timberborn.Gathering.Gatherable`

**Timberborn.Localization**

* type `Timberborn.Localization.ILoc`
  * method `T(System.String)`: `System.String`

**Timberborn.NaturalResourcesLifecycle**

* type `Timberborn.NaturalResourcesLifecycle.LivingNaturalResource`
  * method `get_IsDead()`: `System.Boolean`

**Timberborn.Planting**

* type `Timberborn.Planting.PlantableSpec`
  * method `get_TemplateName()`: `System.String`
  * method `op_Equality(Timberborn.Planting.PlantableSpec, Timberborn.Planting.PlantableSpec)`: `System.Boolean`
* type `Timberborn.Planting.PlanterBuilding`
  * method `CanPlant(System.String)`: `System.Boolean`
* type `Timberborn.Planting.PlantingService`
  * method `GetResourceAt(UnityEngine.Vector3Int)`: `System.String`
  * method `TryGetPlantingBlocker(UnityEngine.Vector3Int, Timberborn.BlockSystem.BlockObject&)`: `System.Boolean`
  * method `get_PlantingCoordinates()`: `System.Collections.Generic.IEnumerable`1<UnityEngine.Vector3Int>`

**Timberborn.SingletonSystem**

* type `Timberborn.SingletonSystem.ILoadableSingleton`

**Timberborn.TemplateInstantiation**

* type `Timberborn.TemplateInstantiation.TemplateModule`
* type `Timberborn.TemplateInstantiation.TemplateModule+Builder`
  * method `.ctor()`
  * method `AddDecorator<2>()`
  * method `Build()`: `Timberborn.TemplateInstantiation.TemplateModule`

**Timberborn.TemplateSystem**

* type `Timberborn.TemplateSystem.TemplateService`
  * method `GetAll<1>()`: `System.Collections.Generic.IEnumerable`1<!!0>`

**Timberborn.TickSystem**

* type `Timberborn.TickSystem.ITickableSingleton`

**Timberborn.TimeSystem**

* type `Timberborn.TimeSystem.IDayNightCycle`
  * method `get_PartialDayNumber()`: `System.Single`

**UnityEngine.CoreModule**

* type `UnityEngine.Debug`
  * method `LogError(System.Object)`
  * method `LogWarning(System.Object)`
* type `UnityEngine.Vector3Int`

**Game classes derived from and interfaces implemented** (with the abstract members each had at build time; a new one keeps the module from loading)

* class `Bindito.Core.Configurator`: `Configure`
* class `Timberborn.BaseComponentSystem.BaseComponent`
* interface `Timberborn.BaseComponentSystem.IAwakableComponent`: `Awake`
* interface `Timberborn.BlockSystem.IFinishedStateListener`: `OnEnterFinishedState`, `OnExitFinishedState`
* interface `Timberborn.EntityNaming.IEntityNamer`: `GenerateEntityName`, `get_EntityNamerPriority`
* interface `Timberborn.EntitySystem.IDeletableEntity`: `DeleteEntity`
* interface `Timberborn.SingletonSystem.ILoadableSingleton`: `Load`
* interface `Timberborn.TickSystem.ITickableSingleton`: `Tick`

<!-- api:end -->
