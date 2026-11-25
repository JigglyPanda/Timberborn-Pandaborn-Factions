# Pandaborn.Specs - every spec record

Always loaded, so blueprint data that names our specs always deserialises, whatever features are on. Spec class names are
global across all mods: `Pandaborn...Spec`, frozen once shipped. Before loading, the bootstrap checks that no other assembly
already defines one of these names.

<!-- api:begin -->
<!-- Generated from the compiled module by Pandaborn.ApiScan on every build. Do not edit by hand. -->

### Game API this module references

Spec classes defined: `PandabornBellSettledMarkerSpec`, `PandabornBellSpec`, `PandabornCisternTapSpec`, `PandabornCurrentDrivenSpec`, `PandabornDewLimiterSpec`, `PandabornEntityStateSpec`, `PandabornFestivalGoerSpec`, `PandabornFestivalSpec`, `PandabornFestivalSquareSpec`, `PandabornFloweringPlantSpec`, `PandabornFloweringSpec`, `PandabornFlumeGateSpec`, `PandabornFlumeSegmentSpec`, `PandabornGoodAmountStepSpec`, `PandabornInFlowerSpec`, `PandabornMoonLoftSpec`, `PandabornNamePoolSpec`, `PandabornNightPostSpec`, `PandabornPaddySpoutSpec`, `PandabornRingtailSpec`, `PandabornRingtailsSpec`, `PandabornSolidCellsSpec`, `PandabornTraditionSpec`, `PandabornTreadwheelSpec`

**Timberborn.BlueprintSystem**

* type `Timberborn.BlueprintSystem.AssetRef`1`
* type `Timberborn.BlueprintSystem.ComponentSpec`
  * method `.ctor()`
  * method `.ctor(Timberborn.BlueprintSystem.ComponentSpec)`
  * method `Equals(Timberborn.BlueprintSystem.ComponentSpec)`: `System.Boolean`
  * method `GetHashCode()`: `System.Int32`
  * method `PrintMembers(System.Text.StringBuilder)`: `System.Boolean`
* type `Timberborn.BlueprintSystem.SerializeAttribute`
  * method `.ctor()`

**UnityEngine.CoreModule**

* type `UnityEngine.Sprite`
* type `UnityEngine.Texture2D`
* type `UnityEngine.Vector3Int`

**Game classes derived from and interfaces implemented** (with the abstract members each had at build time; a new one keeps the module from loading)

* class `Timberborn.BlueprintSystem.ComponentSpec`: `<Clone>$`

<!-- api:end -->
