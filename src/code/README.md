# Runtime code

All C# that ships in the mod. The rules are in [docs/ENGINEERING.md](../../docs/ENGINEERING.md) ("Code rules"); this
page is how they are built and how to add a feature.

## Layout

| Project | Ships as | Loaded | Contents |
|---|---|---|---|
| `Pandaborn.Bootstrap` | `Scripts/Pandaborn.Bootstrap.dll` | by the game | Only the mod starter. References nothing but `IModStarter` and `Debug.Log`, so it can always load |
| `Pandaborn.Specs` | `Scripts/Pandaborn.Specs.bin` | always, first | Every spec record (`Pandaborn…Spec`). Only references the blueprint system |
| `Pandaborn.Core` | `Scripts/Pandaborn.Core.bin` | always, second | Feature registry, save carrier (`PandabornStore`), notices (`FeatureNotices`, `Messenger`), interface guard (`SafeUi`) |
| `Pandaborn.<Feature>` | `Modules/Pandaborn.<Feature>.bin` | only if its game-API check passes | One feature each: `Bell` (the afternoon bell), `Names` (faction colonist names), `Look` (the Inkpaws building look) |
| `tools/Pandaborn.ApiScan` | not shipped | build only | Extracts a module's required-API list from the compiled assembly |

Every `.bin` ships with `<name>.api.txt`, the list of game types, methods and fields it references (generated on every
build), and `Modules/modules.txt` lists the feature modules in load order.

## Build

```powershell
dotnet build src\code\Pandaborn.Code.sln -c Release                          # into E:\PandabornDev\build\PandabornFactions
dotnet build src\code\Pandaborn.Code.sln -c Release -p:ModOut=<mod folder>   # into any mod folder (e.g. a prototype)
```

Intermediates go to `E:\PandabornDev\build\obj\code\<project>`. Each build also rewrites the generated half of every
project's `FEATURE.md`, so a game update that changes what a module touches shows up as a diff in git. Note: `tools/build.ps1`
mirrors `mod/PandabornFactions` and deletes anything else in the build folder, so run the code build after it (or wire it in
there; it is not yet wired, to keep other agents' test runs unaffected until the owner switches the code on).

`Pandaborn.Look` also copies its asset bundle (`pandabornlook_win`/`_mac`, made by `tools/build_look.ps1 -BundleName
pandabornlook` into `E:\PandabornDev\build\look\AssetBundles`, never in git) into `<ModOut>\AssetBundles` when it is there.
Until the code ships in the faction mod, feature tests use `tools/build_code_devmod.ps1 [-DevSwitch '...']`: the whole code
build plus a manifest in `E:\PandabornDev\build\PandabornCodeDev` (Id `JigglyPanda.PandabornCodeDev`, requires the faction
mod), passed to `tools/run_game_test.ps1 -ExtraMods`. Never enable it together with another mod that carries the code
(`proto/stage0`).

## What happens at start

1. The game loads every `*.dll` of every enabled mod (`ModCodeStarter`), then runs each mod's `IModStarter` once, before
   the main menu. Our starter (`PandabornStarter`) runs `Boot.Run(modPath)`:
2. If a copy of the mod has already booted in this process (local folder plus Workshop), it records itself as a duplicate
   and stops: no assembly is loaded twice, so `SpecTypeCache` never sees a duplicate spec name. The running copy posts a
   notice in game.
3. `Pandaborn.Specs.bin` and `Pandaborn.Core.bin` are checked and loaded with `Assembly.Load(bytes)`. Before loading
   Specs, every spec class name it defines is looked up in the AppDomain; if another assembly already defines one, Specs
   (and so every feature) stays off instead of crashing every game.
4. For each module in `Modules/modules.txt`: unless the dev switch forces it off, every line of its `.api.txt` is resolved
   by reflection against the running game (type by name in its assembly; method by name, generic arity and parameter
   types, searched through base types and interfaces; field by name). If anything is missing the module is not loaded and
   the reason is recorded. Otherwise it is loaded once per AppDomain.
5. The outcome goes into AppDomain data (`Pandaborn.Boot.Report`, `.Owner`, `.Duplicates`) and the log. `Pandaborn.Core`
   reads it (`FeatureRegistry`) and, when a game's interface first appears, `FeatureNotices` tells the player once per save
   about every feature that is off, as a toast and an entry in the notification log.

Verified in game (stage 0, see `docs/tech/stage0.md`): Bindito finds configurators in assemblies loaded this way, and the
game's `SpecTypeCache` registers their spec records, because both scan `AppDomain.GetAssemblies()` after the mod starters
have run (the configurator scan happens whenever a context is built, `SpecTypeCache` is created with each context's
`BlueprintDeserializer`).

## Dev switch (tests only)

`pandaborn.dev.txt` in the mod folder, or the environment variable `PANDABORN_DEV` (lines separated by `;`):

```
force-off: Bell, Names          # the module is not loaded, as for a player whose game changed under it
simulate-missing-api: Bell      # the API check fails (adds a missing type), exercising the "needs update" path
```

`proto/stage0/build.ps1 -DevSwitch 'force-off: Bell'` (or `tools/build_code_devmod.ps1 -DevSwitch ...`) writes it; the stage-0 probe can write it for the next launch.

## Adding a feature module

1. **Specs first.** Add the spec records to `Pandaborn.Specs` (`public record Pandaborn<Thing>Spec : ComponentSpec`, `[Serialize]`
   properties with sensible defaults). Spec class names are global across every mod: always the `Pandaborn` prefix, never
   renamed or removed once shipped. Our specs go only in templates listed solely in Inkpaws collections (data rule 1) -
   for example the Inkpaws adult character template, or an Inkpaws-only building.
2. **Create `src/code/Pandaborn.<Feature>/Pandaborn.<Feature>.csproj`**: copy `Pandaborn.Names.csproj`, change the names,
   keep `<PandabornKind>Feature</PandabornKind>` and the project references to Specs and Core (`Private="false"`).
   `dotnet sln src\code\Pandaborn.Code.sln add <csproj>`.
3. **Configurator**: `[Context("Game")] public class <Feature>Configurator : Configurator`. Attach behaviour to entities with
   `MultiBind<TemplateModule>()` and `AddDecorator<Pandaborn<Thing>Spec, <Component>>()`, so it exists only where the
   data names the spec. Singletons that should do nothing outside Inkpaws games should check for their spec (see
   `BellService.Active`: the faction's adult template carries `PandabornBellSpec`) rather than a faction id.
4. **List it** in `src/code/modules.txt` (`Id  File  Description`) and give it a display name in
   `Pandaborn.Core/mod/Localizations/enUS_PandabornCore.csv` (`Pandaborn.Feature.<Id>`).
5. **Data that ships with the module** (localisation, blueprint fragments) goes in the project's `mod/` folder; it is copied
   into the mod. Use loc keys `Pandaborn.<Feature>.*` and a file `Localizations/enUS_Pandaborn<Feature>.csv`.
6. **Saved state** goes through `PandabornStore` (inject it): `Set("<Feature>", version, payload)` / `TryGet(...)`; payload
   helpers in `Payload`. The store lives in Core, so the entry survives saves made while the feature is off. Read
   tolerantly: unknown version or malformed text means start fresh.
7. **Degradation rule**: with the module off, every building and character must still be a sensible vanilla thing. Never
   write saved vanilla state for a temporary effect; use bonuses (not saved: `BonusManager` rebuilds from whoever adds
   them), behaviours or effects.
8. **Interface code** runs inside `SafeUi.Run/Get("<Feature>.<Piece>", ...)`: an exception switches that piece off for
   the session and is logged once.
9. **Reflection on private members** only with a written fallback, and a test that simulates the member being gone.
10. **Write `FEATURE.md`'s first half** (what it does, its data, how it fails). The second half is generated.
11. **Test** with the harness: a request under `tests/scenarios/<feature>/`, one run with the feature on, one with
    `force-off`, one with `simulate-missing-api`; Folktails unchanged.

## Migrating the water code (`src/scripts/Water`) into `Pandaborn.Water`

The flume and dew code is still being prototyped by another agent in `src/scripts/` (built into `proto/water`). When it
settles:

1. Move the spec records (`PandabornFlume…Spec`, `PandabornDew…Spec` and so on, currently next to their components) into
   `Pandaborn.Specs/WaterSpecs.cs`, unchanged in name and fields.
2. Move the components, services and `WaterConfigurator` into `src/code/Pandaborn.Water/`, with a csproj made as above, and
   add `Water  Pandaborn.Water.bin  ...` to `modules.txt`.
3. Persisted state (if any) moves to `PandabornStore` entries `Water.*`; limiters are not saved by the game, which suits
   rule 5 already.
4. Any panel or status text goes behind `SafeUi`.
5. Check the generated `FEATURE.md`: the touch list should be `IWaterService` direction limiters and inflow limits,
   `BlockObject`, `IFinishedStateListener`, `FlowDirection`, the manufactory limiter and weather services, and nothing
   private. If it shows a private member, write its fallback first.
6. Retire `src/scripts/Pandaborn.Water.csproj`; `proto/water` then builds `src/code` with `-p:ModOut` like `proto/stage0` does.
