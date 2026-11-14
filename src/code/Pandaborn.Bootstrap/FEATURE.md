# Pandaborn.Bootstrap - the mod starter

The only assembly the game loads by itself. Its references are limited to `IModStarter`/`IModEnvironment` and `Debug`, so
it can never fail to load. See src/code/README.md for what it does at start. Its list below is for diffing only; nothing
checks it at runtime.

<!-- api:begin -->
<!-- Generated from the compiled module by Pandaborn.ApiScan on every build. Do not edit by hand. -->

### Game API this module references

**Timberborn.ModManagerScene**

* type `Timberborn.ModManagerScene.IModEnvironment`
  * method `get_ModPath()`
* type `Timberborn.ModManagerScene.IModStarter`

**UnityEngine.CoreModule**

* type `UnityEngine.Debug`
  * method `Log(System.Object)`
  * method `LogError(System.Object)`
  * method `LogWarning(System.Object)`

<!-- api:end -->
