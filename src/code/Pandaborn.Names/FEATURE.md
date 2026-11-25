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
* **What it does not do.** The game's option replaces dead *trees* only: `Forester.Validate` accepts a blocked planting
  spot when the blocker has a `TreeComponent` that is dead (and the tile is not in a cutting area). Timber bamboo and
  persimmon (basis `ChestnutTree`) are trees. Tea and Sichuan pepper are bushes (basis `BlueberryBush`: `BushSpec`, no
  `TreeComponentSpec`), so a dead one still blocks its planting mark until the player demolishes it, exactly like a dead
  blueberry bush in the plain game. Clearing them needs one of: a small component on the Inkpaws bushes that deletes a
  dead bush standing on a planting mark (new spec, new code), or `TreeComponentSpec` on the two bushes, which must
  first be checked against `TreeCuttingArea` (it tracks every `TreeComponent` and may expect a `Cuttable`).

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
* type `Timberborn.BaseComponentSystem.IAwakableComponent`

**Timberborn.Beavers**

* type `Timberborn.Beavers.AdultSpec`

**Timberborn.BlueprintSystem**

* type `Timberborn.BlueprintSystem.Blueprint`
  * method `GetSpec<1>()`: `!!0`
* type `Timberborn.BlueprintSystem.ComponentSpec`
  * method `get_Blueprint()`: `Timberborn.BlueprintSystem.Blueprint`

**Timberborn.Common**

* type `Timberborn.Common.IRandomNumberGenerator`
  * method `Range(System.Int32, System.Int32)`: `System.Int32`

**Timberborn.EntityNaming**

* type `Timberborn.EntityNaming.IEntityNamer`

**Timberborn.FactionSystem**

* type `Timberborn.FactionSystem.FactionSpec`
  * method `get_Id()`: `System.String`

**Timberborn.Forestry**

* type `Timberborn.Forestry.Forester`
  * method `SetReplantDeadTrees(System.Boolean)`
  * method `get_ReplantDeadTrees()`: `System.Boolean`

**Timberborn.GameFactionSystem**

* type `Timberborn.GameFactionSystem.FactionService`
  * method `get_Current()`: `Timberborn.FactionSystem.FactionSpec`

**Timberborn.Localization**

* type `Timberborn.Localization.ILoc`
  * method `T(System.String)`: `System.String`

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

**UnityEngine.CoreModule**

* type `UnityEngine.Debug`
  * method `LogError(System.Object)`
  * method `LogWarning(System.Object)`

**Game classes derived from and interfaces implemented** (with the abstract members each had at build time; a new one keeps the module from loading)

* class `Bindito.Core.Configurator`: `Configure`
* class `Timberborn.BaseComponentSystem.BaseComponent`
* interface `Timberborn.BaseComponentSystem.IAwakableComponent`: `Awake`
* interface `Timberborn.EntityNaming.IEntityNamer`: `GenerateEntityName`, `get_EntityNamerPriority`
* interface `Timberborn.SingletonSystem.ILoadableSingleton`: `Load`

<!-- api:end -->
