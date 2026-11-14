# Pandaborn.Look - the Inkpaws building look

Every vanilla Folktails building the Inkpaws use is re-themed (dark timber, bamboo, clay-tile roofs, lime plaster, paper
lattice windows) without a single new model. The faction keeps listing the vanilla `Folktails` material collection, so
other mods that add materials or buildings to it, or inject its materials into other factions (ChooChoo), keep working.
Background and results: `docs/tech/look.md`.

**How.** `PandabornLookSpec { MaterialCollectionIds }` sits on the faction blueprint (this module's
`mod/Factions/Pandaborn/Faction.Inkpaws.optional.blueprint.json` merges it onto `Faction.Inkpaws`). `MaterialSwap` is an
`IMaterialCollectionIdsProvider`, so `MaterialRepository.Load` enumerates it while it fills its dictionary, before any
model is built. On that first enumeration, in a game whose faction carries the spec, every material of the named
collections (here `PandabornLook.Inkpaws`: 19 asset-bundle materials named exactly like vanilla ones, e.g.
`Materials/Pandaborn/Look/BaseWood_Brown.Folktails`) is copied with `Material.CopyPropertiesFromMaterial` into the loaded
material of the same name from the faction's own collections; a backup of each is kept. The game's shader stays; only
textures, colours and floats change. It yields no ids. The originals are restored on `IUnloadableSingleton.Unload`,
before the next game's swap, and from a main-menu `ILoadableSingleton` as a safety net. Folktails and Iron Teeth games
(no spec on their faction) are untouched.

**Data.** `mod/MaterialCollections/Pandaborn/MaterialCollection.PandabornLook.Inkpaws.blueprint.json` (the collection, not
listed by any faction) and the faction fragment above. The materials live in the asset bundle `pandabornlook_win`, a build
artefact of `tools/build_look.ps1 -BundleName pandabornlook` (in `E:\PandabornDev\build\look\AssetBundles`, never in git);
the code build copies it into `<mod>\AssetBundles` when it is there.

**Fails safely.** Module off (forced, or the game API changed): nothing is copied and the Inkpaws have the vanilla
Folktails look; `Pandaborn.Core` posts its notice. Bundle missing: the replacements do not load, nothing is copied, one log
line says so. Any exception during the swap restores what was already changed, is logged once, and switches the look off
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

**Timberborn.BlueprintSystem**

* type `Timberborn.BlueprintSystem.AssetRef`1`
  * method `get_Asset()`
  * method `op_Equality(Timberborn.BlueprintSystem.AssetRef`1<!0>, Timberborn.BlueprintSystem.AssetRef`1<!0>)`
* type `Timberborn.BlueprintSystem.Blueprint`
  * method `GetSpec<1>()`
* type `Timberborn.BlueprintSystem.ComponentSpec`
  * method `get_Blueprint()`
* type `Timberborn.BlueprintSystem.ISpecService`
  * method `GetSpecs<1>()`

**Timberborn.FactionSystem**

* type `Timberborn.FactionSystem.FactionSpec`
  * method `get_Id()`
  * method `get_MaterialCollectionIds()`

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
  * method `op_Equality(UnityEngine.Object, UnityEngine.Object)`
  * method `op_Inequality(UnityEngine.Object, UnityEngine.Object)`
  * method `set_name(System.String)`

<!-- api:end -->
