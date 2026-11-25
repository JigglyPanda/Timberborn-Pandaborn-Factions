# Pandaborn.Look - the Inkpaws building look

Every vanilla Folktails building the Inkpaws use is re-themed (dark timber, bamboo, clay-tile roofs, lime plaster, paper
lattice windows) without a single new model. The faction keeps listing the vanilla `Folktails` material collection, so
other mods that add materials or buildings to it, or inject its materials into other factions (ChooChoo), keep working.
Background and results: `docs/tech/look.md`.

**How.** No blueprint data at all (the faction file is read in every game and stays plain, data rule 1). `MaterialSwap` is
an `IMaterialCollectionIdsProvider`, so `MaterialRepository.Load` enumerates it while it fills its dictionary, before any
model is built. On that first enumeration, if the loaded faction's Id is `Inkpaws`, it loads every material our asset
bundle holds under `Materials/Pandaborn/Look/` (`IAssetLoader.LoadAll`, mod assets only; 19 materials named exactly like
vanilla ones, e.g. `BaseWood_Brown.Folktails`) and copies each with `Material.CopyPropertiesFromMaterial` into the loaded
material of the same name from the faction's own material collections; a backup of each is kept. The game's shader
stays; only textures, colours and floats change. It yields no ids. The originals are restored on
`IUnloadableSingleton.Unload`, before the next game's swap, and from a main-menu `ILoadableSingleton` as a safety net.
Folktails and Iron Teeth games are untouched.

**Data.** Only the asset bundle `pandabornlook_win`, a build artefact of `tools/build_look.ps1 -BundleName pandabornlook`
(in `E:\PandabornDev\build\look\AssetBundles`, never in git); the code build copies it into `<mod>\AssetBundles` when it
is there. No material collection, no spec, no id to lock.

**Fails safely.** Module off (forced, or the game API changed): nothing is copied and the Inkpaws have the vanilla
Folktails look; `Pandaborn.Core` posts its notice. Bundle missing: nothing is found under the folder, nothing is copied, one log line says so. Any exception during the swap restores what was already changed, is logged once, and switches the look off
for the rest of the session. Nothing is saved: the look is rebuilt at every load.

**Exit paths.** The swapped materials are shared Unity assets that live for the whole session, so the vanilla
properties are put back by the game's `Unload` (quit to menu, loading another save), before the next game's swap, and on
the main menu. Only the game that made the swap undoes it on `Unload` (an older game's late `Unload` cannot undo a newer
game's look). The game calls every singleton's `Unload` in a row without a guard, so another mod's exception can skip
ours: the next game and the main menu restore anyway. A crash or Alt+F4 leaves nothing behind (nothing is written to
disk). In an Inkpaws game without the bundle (a platform whose `_win`/`_mac` twin is missing) the feature report and the
notice say "nothing to work with"; after a failed swap they say reduced.

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
  * method `ToExisting<1>()`: `Bindito.Core.IExportAssignee`
* type `Bindito.Core.IExportAssignee`
* type `Bindito.Core.IMultiBindingBuilder`1`
* type `Bindito.Core.IScopeAssignee`
  * method `AsSingleton()`: `Bindito.Core.IExportAssignee`
* type `Bindito.Core.ISingleBindingBuilder`1`

**Timberborn.AssetSystem**

* type `Timberborn.AssetSystem.IAssetLoader`
  * method `LoadAll<1>(System.String, System.Collections.Generic.IEnumerable`1<System.String>)`: `System.Collections.Generic.IEnumerable`1<Timberborn.AssetSystem.LoadedAsset`1<!!0>>`
* type `Timberborn.AssetSystem.LoadedAsset`1`
  * method `get_Asset()`: `!0`
  * method `get_IsBuiltIn()`: `System.Boolean`

**Timberborn.BlueprintSystem**

* type `Timberborn.BlueprintSystem.AssetRef`1`
  * method `get_Asset()`: `!0`
* type `Timberborn.BlueprintSystem.ISpecService`
  * method `GetSpecs<1>()`: `System.Collections.Generic.IEnumerable`1<!!0>`

**Timberborn.FactionSystem**

* type `Timberborn.FactionSystem.FactionSpec`
  * method `get_Id()`: `System.String`
  * method `get_MaterialCollectionIds()`: `System.Collections.Immutable.ImmutableArray`1<System.String>`
  * method `op_Equality(Timberborn.FactionSystem.FactionSpec, Timberborn.FactionSystem.FactionSpec)`: `System.Boolean`

**Timberborn.GameFactionSystem**

* type `Timberborn.GameFactionSystem.FactionService`
  * method `get_Current()`: `Timberborn.FactionSystem.FactionSpec`

**Timberborn.SingletonSystem**

* type `Timberborn.SingletonSystem.ILoadableSingleton`
* type `Timberborn.SingletonSystem.IUnloadableSingleton`

**Timberborn.TimbermeshMaterials**

* type `Timberborn.TimbermeshMaterials.IMaterialCollectionIdsProvider`
* type `Timberborn.TimbermeshMaterials.MaterialCollectionSpec`
  * method `get_CollectionId()`: `System.String`
  * method `get_Materials()`: `System.Collections.Immutable.ImmutableArray`1<Timberborn.BlueprintSystem.AssetRef`1<UnityEngine.Material>>`

**UnityEngine.CoreModule**

* type `UnityEngine.Debug`
  * method `Log(System.Object)`
  * method `LogError(System.Object)`
* type `UnityEngine.Material`
  * method `.ctor(UnityEngine.Material)`
  * method `CopyPropertiesFromMaterial(UnityEngine.Material)`
* type `UnityEngine.Object`
  * method `Destroy(UnityEngine.Object)`
  * method `get_name()`: `System.String`
  * method `op_Inequality(UnityEngine.Object, UnityEngine.Object)`: `System.Boolean`
  * method `set_name(System.String)`

**Game classes derived from and interfaces implemented** (with the abstract members each had at build time; a new one keeps the module from loading)

* class `Bindito.Core.Configurator`: `Configure`
* interface `Timberborn.SingletonSystem.ILoadableSingleton`: `Load`
* interface `Timberborn.SingletonSystem.IUnloadableSingleton`: `Unload`
* interface `Timberborn.TimbermeshMaterials.IMaterialCollectionIdsProvider`: `GetMaterialCollectionIds`

<!-- api:end -->
