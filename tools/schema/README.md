# Blueprint schema dumper

Reads the game's assemblies as metadata only (`System.Reflection.MetadataLoadContext`; no game code runs) and
writes `schema/<game version>.json`: every blueprint spec key, its JSON fields with types and defaults, the nested
object types and the enums they use. `tools/validate.py` uses it to check blueprint keys and fields.

It mirrors `Timberborn.BlueprintSystem` exactly (`SpecTypeCache`, `BasicDeserializer`, `AdvancedDeserializer`,
`SerializableTypeExtensions`, `PrimitiveTypeSerialization`):

* A spec is a non-abstract class assignable to `ComponentSpec`. Keys: `type.Name` plus `[SpecAlias]` aliases
  (the most derived `[SpecAlias]` wins, as with `inherit: true`). Duplicate keys are errors (the game's
  `ToFrozenDictionary` throws).
* Fields: `GetProperties(Instance|Public|NonPublic)` with `[Serialize]` and no source name. So private
  properties of the class itself count (e.g. `NeedSpec.FavorableWellbeing`); private ones of base classes don't.
* `[Serialize("Source")]` properties are listed under `derived`; they are filled from `Source`, not from JSON.
* A property type is an `object` if it is a `ComponentSpec` or has any `[Serialize]` property; such types are
  collected recursively under `types`.

## Run

```
dotnet run --project tools/schema -c Release -- [--managed <dir>] [--game <game root>] [--out <file or dir>]
                                                [--include <dll or dir>]... [--check-blueprints <dir>]
```

* Defaults: game = Steam install, managed = `<game>/Timberborn_Data/Managed`, out = `<repo>/schema/`
  (a directory gets `<gameVersion>.json`; a path ending `.json` is used as is).
* `--include` adds our own DLLs; their specs get `"origin": "mod"` (vanilla: `"game"`).
* `--check-blueprints E:\PandabornDev\reference\Blueprints` walks every `*.blueprint.json` (top level and
  `Children`, recursively, skipping `#nested` children), strips `#append`/`#remove`/`#delete`, and prints
  unknown spec keys and unknown field keys (one level inside each spec).
* Exit codes: 0 ok; 1 load failure or duplicate spec key; 3 unknown spec keys in `--check-blueprints`.
* Build output goes to `E:\PandabornDev\build\obj\schema\` (`Directory.Build.props`).

## Format (`formatVersion` 1)

UTF-8 without BOM, LF, 2-space indent, keys sorted ordinally, deterministic.

```
{
  "formatVersion": 1, "gameVersion": "1.1.2.8", "unityVersion": "6000.5.11f1",
  "assemblies": { "<name>": { "version", "mvid", "sha256" } },          // only assemblies that define something listed
  "specs": {
    "<key>": { "fullName", "assembly", "visibility": "public|internal", "isRecord", "base", "aliases": [],
               "origin": "game|mod", "fields": { "<json key>": <field> },
               "derived": { "<property>": { "source", "type" } } },
    "<alias key>": { "aliasOf": "<type name>" }
  },
  "types": { "<full name>": { "assembly", "visibility", "isRecord", "fields", "derived" } },
  "enums": { "<full name>": { "assembly", "flags", "values": [ { "name", "value" } ] } }
}
<field>    = { "type": <typedesc>, "declaredOn", "access": "public|internal|protected|private",
               "default", "defaultSource": "typeDefault|initializer|unknown", "attributes": [ ... ] (omitted if none) }
<typedesc> = { "kind": "int|float|bool|string|char|guid|vector2|vector2int|vector3|vector3int|quaternion|color|serializedobject" }
           | { "kind": "enum", "enum": "<full name>" }      | { "kind": "object", "type": "<full name>" }
           | { "kind": "assetref", "asset": "<T>" }          | { "kind": "array", "element": <typedesc> }
           | { "kind": "nullable", "inner": <typedesc> }     | { "kind": "unsupported", "clr": "<name>" }
```

* Vectors/quaternions are JSON objects with `X`,`Y`(,`Z`,`W`); `color` uses `r`,`g`,`b`,`a`. Enums are names
  (flags: `"A, B"`). `serializedobject` is any JSON object (`SerializedObject` passes through; unused in 1.1.2.8).
* Arrays: an `AssetRef` or object element is handled like a single value, other elements go through
  `PrimitiveTypeSerialization` without `Nullable` unwrapping (so `ImmutableArray<int?>` is `unsupported`).
* Type names: CLR full names; nested types use `+`; generics are written `Name<Arg,...>`.

## Defaults

`typeDefault` is the CLR default in JSON form (0, false, null, `[]` for arrays, zero vectors, the enum member
with value 0). `initializer` comes from reading the IL of the declaring type's parameterless constructors:
`ldarg.0; <ldc.*|ldstr|ldnull|string.Empty|ImmutableArray<T>.Empty>; [newobj Nullable<T>]; stfld <P>k__BackingField`
(or `call set_P`). Any other assignment to the backing field (e.g. `= Vector3.one`) gives `unknown` with
`default: null`, as does a `[Serialize]` property that is not an auto-property. On 1.1.2.8 this finds all 18
initializers the decompiled source shows (16 constants, 2 `Vector3.one` reported as unknown).

## Known limits

* The game registers open generic spec classes too: `MinMaxSpec`1` is a spec key whose `Min`/`Max` are
  `unsupported` (`T`). Its closed forms used as fields (`MinMaxSpec<System.Single>`, `MinMaxSpec<System.Int32>`)
  are listed under `types` with real field types.
* Custom `IDeserializer`s are not modelled beyond naming the source property of each `derived` entry.
* Only assemblies that reference `Timberborn.BlueprintSystem` are scanned (no other can define a spec).
* `access` folds `protected internal` into `protected` and `private protected` into `private`.
