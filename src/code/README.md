# Runtime code

All C# that ships in the mod. The rules are in [docs/ENGINEERING.md](../../docs/ENGINEERING.md) ("Code rules"); this
page is how they are built and how to add a feature.

## Layout

| Project | Ships as | Loaded | Contents |
|---|---|---|---|
| `Pandaborn.Bootstrap` | `Scripts/Pandaborn.Bootstrap.dll` | by the game | Only the mod starter. References nothing but `IModStarter` and `Debug.Log`, so it can always load |
| `Pandaborn.Specs` | `Scripts/Pandaborn.Specs.bin` | always, first | Every spec record (`Pandaborn…Spec`). Only references the blueprint system |
| `Pandaborn.Core` | `Scripts/Pandaborn.Core.bin` | always, second | Feature registry, save carriers (`PandabornStore` per game, `PandabornEntityState` per entity), notices and the feature report (`FeatureNotices`, `Messenger`), interface guard (`SafeUi`) |
| `Pandaborn.<Feature>` | `Modules/Pandaborn.<Feature>.bin` | only if its game-API check passes | One feature each: `Bell` (the afternoon bell), `Names` (faction colonist names), `Look` (the Inkpaws building look), `Words` (Inkpaw words in the interface) |
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
**Testing code now that the faction mod ships its own bootstrap:** a layered dev mod with a second bootstrap is only reported as a duplicate (the faction mod loads first and owns the code). Use `proto/foundation/build.ps1 -Name <folder> [-DevSwitch '...']`: a full copy of the installed mod (big files hard-linked) with the code under test, Id `JigglyPanda.PandabornFactionsDev`, run with `-DisableMods JigglyPanda.PandabornFactions -ExtraMods E:\PandabornDev\build\proto\<folder>`. Before that, feature tests used `tools/build_code_devmod.ps1 [-DevSwitch '...']`: the whole code
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
   about every feature that is off, as a toast and an entry in the notification log. In Inkpaws games it also adds one\n   notification-log entry per save, the **feature report** (`Pandaborn - Factions features: The afternoon bell: on; ...`),\n   posted again only when the states change.

Verified in game (stage 0, see `docs/tech/stage0.md`): Bindito finds configurators in assemblies loaded this way, and the
game's `SpecTypeCache` registers their spec records, because both scan `AppDomain.GetAssemblies()` after the mod starters
have run (the configurator scan happens whenever a context is built, `SpecTypeCache` is created with each context's
`BlueprintDeserializer`).

## Dev switch (tests only)

`pandaborn.dev.txt` in the mod folder, or the environment variable `PANDABORN_DEV` (lines separated by `;`):

```
force-off: Bell, Names          # the module is not loaded, as for a player whose game changed under it
simulate-missing-api: Bell      # the API check fails (adds a missing type), exercising the "needs update" path
simulate-missing-member: Words  # a module's private-member reflection takes its written fallback (FeatureRegistry.DevFlag)
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
6. **Saved state** never goes in your own `IPersistentEntity`/`ISaveableSingleton` (a component of a module that is
   off is not there to load and re-save its data, so the next save drops it). Use the Core carriers, which are always
   loaded and write back every feature's entry unchanged while that feature is off:
   * **Per game**: `PandabornStore` (inject it): `Set("<Feature>", version, payload)` / `TryGet(...)`; payload helpers
     in `Payload` (`key=value;...`).
   * **Per entity** (a colonist, a building, a plant): `PandabornEntityState`. Add `"PandabornEntityStateSpec": {}` to
     each Inkpaws-only template that needs it (catalogue; `Features` is informational), then from your component on the
     same entity:
     ```csharp
     var state = GetComponent<PandabornEntityState>();          // null when the template lacks the spec: run stateless
     // read in InitializeEntity or PostInitializeEntity (the game has loaded the entity by then)
     if (state != null && state.TryGet("Ringtails", out int v, out string payload) && v == 1) { /* parse tolerantly */ }
     // write: whenever it changes ...
     state.Set("Ringtails", 1, payload);
     // ... or once, and the carrier asks at every save
     state.SetWriter("Ringtails", 1, () => Payload.Write(...));
     ```
     Saved as component `Pandaborn.EntityState`, entries `feature|version|payload`. A feature removes its entry with
     `Remove("<Feature>")`; the carrier never drops entries itself.
   * Use your feature id as the key (`Ringtails`, `Water`, `Festival`, `Flowering`), carry a version, read
     tolerantly: unknown version or malformed text means start fresh.
   * Verified in game (`docs/tech/stage0.md`, run `fd-carrier-1`): entries written while their feature was off were
     saved, and the feature found them after reloading with it on.
7. **Degradation rule**: with the module off, every building and character must still be a sensible vanilla thing. Never
   write saved vanilla state for a temporary effect; use bonuses (not saved: `BonusManager` rebuilds from whoever adds
   them), behaviours or effects.
8. **Interface code** runs inside `SafeUi.Run/Get("<Feature>.<Piece>", ...)`: an exception switches that piece off for
   the session and is logged once.
9. **Reflection on private members** only with a written fallback, and a test that simulates the member being gone.
10. **Write `FEATURE.md`'s first half** (what it does, its data, how it fails). The second half is generated. The game-update
    alarm `tools/check_api_lists.py` fails when a generated half differs from the committed one: review the diff and
    commit `FEATURE.md` to acknowledge (`--warn-only` for dev builds).
11. **Test** with the harness: a request under `tests/scenarios/<feature>/`, one run with the feature on, one with
    `force-off`, one with `simulate-missing-api`; Folktails unchanged.

## The water module (`Pandaborn.Water`)

Migrated from the old `src/scripts/` prototype (retired): specs in `Pandaborn.Specs/WaterSpecs.cs`, components, panels and
statuses in `Pandaborn.Water/`, gate settings in the per-entity carrier (entry `Water`), no private members. What each
piece is with the module off is in `Pandaborn.Water/FEATURE.md`; the catalogue hand-over (basis, specs, cells per piece)
is in `docs/tech/water.md`, "For the catalogue lane". `proto/water/build.ps1` builds a dev copy of the faction with it.
