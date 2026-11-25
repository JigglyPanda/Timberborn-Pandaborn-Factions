# Runtime code

All C# that ships in the mod. The rules are in [docs/ENGINEERING.md](../../docs/ENGINEERING.md) ("Code rules"); this
page is how they are built and how to add a feature.

## Layout

| Project | Ships as | Loaded | Contents |
|---|---|---|---|
| `Pandaborn.Bootstrap` | `Scripts/Pandaborn.Bootstrap.dll` | by the game | Only the mod starter. References nothing but `IModStarter` and `Debug.Log`, so it can always load |
| `Pandaborn.Specs` | `Scripts/Pandaborn.Specs.bin` | always, first | Every spec record (`Pandaborn…Spec`). Only references the blueprint system |
| `Pandaborn.Core` | `Scripts/Pandaborn.Core.bin` | always, second | Feature registry, save carriers (`PandabornStore` per game, `PandabornEntityState` per entity), notices and the feature report (`FeatureNotices`, `Messenger`), interface guard (`SafeUi`) |
| `Pandaborn.<Feature>` | `Modules/Pandaborn.<Feature>.bin` | only if its game-API check passes | One feature each: `Bell` (the afternoon bell), `Names` (faction colonist names), `Look` (the Inkpaws building look), `Words` (Inkpaw words in the interface), `Tutorial` (tutorial step types) |
| `tools/Pandaborn.ApiScan` | not shipped | build only | Extracts a module's required-API list from the compiled assembly |

Every `.bin` ships with `<name>.api.txt`, the list of game types, methods and fields it references (generated on every
build), and `Modules/modules.txt` lists the feature modules in load order.

## Build

```powershell
powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 code            # the shipping build (below)
dotnet build src\code\Pandaborn.Code.sln -c Release                          # a scratch build, into E:\PandabornDev\build\code\dev
dotnet build src\code\Pandaborn.Code.sln -c Release -p:ModOut=<mod folder>   # into any mod folder (e.g. a prototype)
dotnet run --project src\code\tests\Foundation -c Release -- --mod <built mod folder>   # the foundation's tests, no game
```

**The code ships in the mod** (since 2026-11-14): the `code` stage of `tools/pandaborn.ps1` builds this solution into
`E:\PandabornDev\build\code\PandabornFactions`, `assemble` puts it into the staging folder with the data, and it reaches
the installed mod only through `gate` and `install`. A module ships only while its switch in `catalogue/rules.toml
[modules]` is on. A bare `dotnet build` never writes into the installed mod (the default output is a scratch folder).

`src/code/tests/Foundation` (a console program, not in the solution, never shipped) compiles the production source
files of the bootstrap and the pure parts of Core, Bell and Words against stand-ins and checks them without the game:
the API check against fake types, bundle parking on real folders, the switches, store entries, the notice rule, the
bell's curve and multiplying share against a model of `BonusManager`, the words table. With `--mod` it also resolves
every module's required-API list of that build against the real game assemblies. Run it after any change to these parts.

Intermediates go to `E:\PandabornDev\build\obj\code\<project>`. Each build also rewrites the generated half of every
project's `FEATURE.md`, so a game update that changes what a module touches shows up as a diff in git, and stamps the
game version it was built against (`Scripts/Pandaborn.built-for.txt`, from `catalogue/vanilla.pin.json`).

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
4. For each module in `Modules/modules.txt`: unless a switch turns it off (the player's `PandabornFactions.txt`, or the
   dev switch), every line of its `.api.txt` is resolved by reflection against the running game: types by name; methods
   by name, generic arity, parameter types and return type, searched through base types and interfaces; fields by name
   and type; all of them still public; game base classes still open and game interfaces without a member the module
   does not know; other Pandaborn assemblies it names loaded (`Pandaborn.Bootstrap/FEATURE.md`). If anything is missing
   the module is not loaded and the reason is recorded. Otherwise it is loaded once per AppDomain.
5. The outcome goes into AppDomain data (`Pandaborn.Boot.Report`, `.Owner`, `.Duplicates`) and the log, with the game
   version the mod was built for and the one running. `Pandaborn.Core` reads it (`FeatureRegistry`). While everything
   works the player is told nothing. Otherwise, when the interface of an Inkpaws game appears, `FeatureNotices` posts
   one message that names each feature in player words and says what will not work: at every load for a feature that
   is switched off, once per save for the rest (`Pandaborn.Core/FEATURE.md`). The state of every unit with its
   technical reason (the **feature report**) goes to the log at every load.

Verified in game (stage 0, see `docs/tech/stage0.md`): Bindito finds configurators in assemblies loaded this way, and the
game's `SpecTypeCache` registers their spec records, because both scan `AppDomain.GetAssemblies()` after the mod starters
have run (the configurator scan happens whenever a context is built, `SpecTypeCache` is created with each context's
`BlueprintDeserializer`).

## The player's switch

`PandabornFactions.txt` in the game's user data folder (the folder that holds `Saves` and `Mods`; `Documents\Timberborn`
on Windows), for a player whose other mods clash with one feature:

```
# lines starting with # are notes
off: Flowering
off: Water, Festival
```

Names are the ids in `modules.txt`, in any letter case. The feature is not loaded (the same forced-off state as the dev
switch, read once at start), the log says what the file switched off, and the in-game notice names the file. A name
that is not a feature is logged and ignored. No file is the normal case.

## Dev switch (tests only)

The environment variable `PANDABORN_DEV` (lines separated by `;`) works in every copy. The file `pandaborn.dev.txt` in
the mod folder works only in a dev copy: a copy whose manifest Id is the released `JigglyPanda.PandabornFactions`
ignores it and says so in the log (probes write that file, and one left in a packaged build must not switch features
off for players). Test the installed or packaged mod with the variable.

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
4. **List it** in `src/code/modules.txt` (`Id  File  Description`), give it a display name (`Pandaborn.Feature.<Id>`, in
   the module's own loc file) and a line that says in player words what does not work while it is off
   (`Pandaborn.Feature.<Id>.Off` in `Pandaborn.Core/mod/Localizations/enUS_PandabornCoreNotices.csv`), and add its id to
   `FeatureNotices.Modules`. A module never references another feature module (the bootstrap would keep it off whenever
   that one is off): shared seams are interfaces in Core.
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
7a. **Say when there is no data.** A module that ships but finds none of its data in a game of our faction (its spec is not
   on any template, its table file is missing) calls `FeatureRegistry.ReportNoData("<Id>", "<what is missing>")` in its
   Load; the feature report then lists it as "off (no data in this game: ...)" instead of the module silently doing
   nothing. A module that runs but with part of its data missing calls `FeatureRegistry.ReportDegradedInGame` ("on,
   reduced (...)", plus one notice; forgotten when the next game starts), or `ReportDegraded` for something that holds
   for the whole session and is reported once. Bell, Names and Words do this; `FeatureNotices.FactionId` is the faction to check.
7b. **Sounds** go through `Pandaborn.Core.PandabornSounds` (inject it): `Has(id)`, `Play2D(id)`,
   `Play3D(gameObject, id)`. It never throws and returns false when the clip is not loaded (no bundle, old copy). Ids
   and where each belongs: docs/tech/sound.md section 8 (the night clapper is the Ringtails module's: `Play2D` when the
   Ringtail shift starts, about 2.5 s after the shift bell when they coincide).
8. **Interface code** runs inside `SafeUi.Run/Get("<Feature>.<Piece>", ...)`: an exception switches that piece off until
   the game is left and is logged once. **Callbacks the game calls** (event handlers, finished-state listeners,
   `PostInitializeEntity`, ticks, tutorial step constructors) catch their own exceptions: the game treats one as a
   failed load or a crash, and it calls every singleton's `Unload` in a row with no guard, so state swapped into
   session-wide objects (texts, shared materials) needs a second restore point (the next game, the main menu).
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
