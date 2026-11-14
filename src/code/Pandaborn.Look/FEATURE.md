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
(in `E:\PandabornDevuild\look\AssetBundles`, never in git); the code build copies it into `<mod>\AssetBundles` when it
is there. No material collection, no spec, no id to lock.

**Fails safely.** Module off (forced, or the game API changed): nothing is copied and the Inkpaws have the vanilla
Folktails look; `Pandaborn.Core` posts its notice. Bundle missing: nothing is found under the folder, nothing is copied, one log line says so. Any exception during the swap restores what was already changed, is logged once, and switches the look off
for the rest of the session. Nothing is saved: the look is rebuilt at every load.

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
* type `Bindito.Core.IExportAssignee`
* type `Bindito.Core.IMultiBindingBuilder`1`
* type `Bindito.Core.IScopeAssignee`
  * method `AsSingleton()`
* type `Bindito.Core.ISingleBindingBuilder`1`

**Timberborn.AssetSystem**

* type `Timberborn.AssetSystem.IAssetLoader`
  * method `LoadAll<1>(System.String, System.Collections.Generic.IEnumerable`1<System.String>)`
* type `Timberborn.AssetSystem.LoadedAsset`1`
  * method `get_Asset()`
  * method `get_IsBuiltIn()`

**Timberborn.BlueprintSystem**

* type `Timberborn.BlueprintSystem.AssetRef`1`
  * method `get_Asset()`
* type `Timberborn.BlueprintSystem.ISpecService`
  * method `GetSpecs<1>()`

**Timberborn.FactionSystem**

* type `Timberborn.FactionSystem.FactionSpec`
  * method `get_Id()`
  * method `get_MaterialCollectionIds()`
  * method `op_Equality(Timberborn.FactionSystem.FactionSpec, Timberborn.FactionSystem.FactionSpec)`

**Timberborn.GameFactionSystem**

* type `Timberborn.GameFactionSystem.FactionService`
  * method `get_Current()`

**Timberborn.SingletonSystem**

* type `Timberborn.SingletonSystem.ILoadableSingleton`
* type `Timberborn.SingletonSystem.IUnloadableSingleton`

**Timberborn.TimbermeshMaterials**

* type `Timberborn.TimbermeshMaterials.IMaterialCollectionIdsProvider`
* type `Timberborn.TimbermeshMaterials.MaterialCollectionSpec`
  * method `get_CollectionId()`
  * method `get_Materials()`

**UnityEngine.CoreModule**

* type `UnityEngine.Debug`
  * method `Log(System.Object)`
  * method `LogError(System.Object)`
* type `UnityEngine.Material`
  * method `.ctor(UnityEngine.Material)`
  * method `CopyPropertiesFromMaterial(UnityEngine.Material)`
* type `UnityEngine.Object`
  * method `Destroy(UnityEngine.Object)`
  * method `get_name()`
  * method `op_Inequality(UnityEngine.Object, UnityEngine.Object)`
  * method `set_name(System.String)`

<!-- api:end -->
