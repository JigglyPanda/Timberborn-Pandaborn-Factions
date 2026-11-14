# Pandaborn.Specs - every spec record

Always loaded, so blueprint data that names our specs always deserialises, whatever features are on. Spec class names are
global across all mods: `Pandaborn...Spec`, frozen once shipped. Before loading, the bootstrap checks that no other assembly
already defines one of these names.

<!-- api:begin -->
<!-- Generated from the compiled module by Pandaborn.ApiScan on every build. Do not edit by hand. -->

### Game API this module references

Spec classes defined: `PandabornBellSettledMarkerSpec`, `PandabornBellSpec`, `PandabornNamePoolSpec`

**Timberborn.BlueprintSystem**

* type `Timberborn.BlueprintSystem.ComponentSpec`
  * method `.ctor()`
  * method `.ctor(Timberborn.BlueprintSystem.ComponentSpec)`
  * method `Equals(Timberborn.BlueprintSystem.ComponentSpec)`
  * method `GetHashCode()`
  * method `PrintMembers(System.Text.StringBuilder)`
* type `Timberborn.BlueprintSystem.SerializeAttribute`
  * method `.ctor()`

<!-- api:end -->
