# Pandaborn.Bootstrap - the mod starter

The only assembly the game loads by itself. Its compiled references are limited to `IModStarter`/`IModEnvironment` and
`Debug`, so it can never fail to load (two more game members are read by name, each with a fallback: `Application.version`
and `UserDataFolder.Folder`). See src/code/README.md for what it does at start. Its list below is for diffing only;
nothing checks it at runtime.

**The API check** (`ApiCheck.cs`; list format in `tools/Pandaborn.ApiScan/Program.cs`). A module is loaded only if every
line of its `<name>.api.txt` holds in the running game. A line fails when the type, method or field is gone, is no longer
public, or (methods and fields) has another return or field type than the module was compiled against: the runtime binds
by full signature, so a getter that changed from a list to an array is as missing as a removed one. `V` lines carry
every game class the module derives from and every game interface it implements, with the abstract members each had at
build time: a class that became sealed, or an interface that gained or changed a member, keeps the module out (it could
not implement it, and one type that cannot load makes the game's `SpecTypeCache` throw in every game). `R` lines name the
other Pandaborn assemblies a module needs; a module that names a feature module that is off stays off too.
`src/code/tests/Foundation` runs the check against fake types and, given a built mod folder, against the real game
assemblies (every line of every shipped list must resolve).

**Two copies enabled** (local folder plus Workshop). The second copy loads no code and parks its own asset bundles
(`AssetBundles` -> `AssetBundles.parked`); the running copy takes its own back at its next start. If the second copy's
folder cannot be changed (read-only, a file held by another program), the running copy parks its same-named files
instead, so each bundle is still loaded once. When a file is in both folders on the way back, the one in `AssetBundles`
stays (the store may have re-downloaded a newer one). The empty parked folder is removed.

**Switches.**
* Players: `PandabornFactions.txt` in the game's user data folder (the folder with `Saves` and `Mods`, from the game's
  `UserDataFolder`), lines `off: Flowering` or `off: Water, Festival`, `#` for notes. Names are the ids of
  `Modules/modules.txt`; unknown names are logged and ignored. The feature is not loaded (state forced-off) and the
  in-game notice says which file did it.
* Tests: the environment variable `PANDABORN_DEV` everywhere; the file `pandaborn.dev.txt` only in a copy whose manifest
  Id is not the released `JigglyPanda.PandabornFactions` (test probes write that file, and one left in a packaged build
  must not switch features off for players; the release copy logs that it ignored it).

**Log lines for bug reports.** `built for game version X, running Y` (X from `Scripts/Pandaborn.built-for.txt`, stamped
by the build from `catalogue/vanilla.pin.json`), a warning when they differ, the state of every unit, and, when
`Pandaborn.Specs` could not load, an error saying that Inkpaws games will not load (nothing in game can say it: the
notices live in Core, which needs Specs).

<!-- api:begin -->
<!-- Generated from the compiled module by Pandaborn.ApiScan on every build. Do not edit by hand. -->

### Game API this module references

**Timberborn.ModManagerScene**

* type `Timberborn.ModManagerScene.IModEnvironment`
  * method `get_ModPath()`: `System.String`
* type `Timberborn.ModManagerScene.IModStarter`

**UnityEngine.CoreModule**

* type `UnityEngine.Debug`
  * method `Log(System.Object)`
  * method `LogError(System.Object)`
  * method `LogWarning(System.Object)`

**Game classes derived from and interfaces implemented** (with the abstract members each had at build time; a new one keeps the module from loading)

* interface `Timberborn.ModManagerScene.IModStarter`: `StartMod`

<!-- api:end -->
