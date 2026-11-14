# Pandaborn.Ringtails - the second people

DESIGN.md Pillar 1, "The gate". Ported from the go/no-go prototype `proto/ringtails` (results:
`docs/tech/two-peoples.md` section 17). **Status: not wired yet** — not in `Pandaborn.Code.sln` or `modules.txt` until
the spec records in `proposed/RingtailSpecs.cs` are added to `Pandaborn.Specs` by its owner. Compile check meanwhile:
`dotnet build -c Release -p:RingtailsProposedSpecs=true -p:ModOut=<scratch>`.

**What it does.** Ringtails are a hidden second adult/kit template pair (in no template collection, so the vanilla
`BeaverFactory` still sees exactly one adult) with their own worker type `PandabornRingtail` (ignores working hours).
They staff only buildings typed for them (`WorkplaceSpec.DefaultWorkerType: PandabornRingtail`,
`DisallowOtherWorkerTypes: true`). Each day they rest from dawn until the bell — the end of the Inkpaw working hours
(the working-hours slider, read live), clamped to 4–16 h after dawn — sleeping at home first, then eating, drinking and
taking leisure; then they work until the next dawn.

| Class | Job |
|---|---|
| `RingtailService` | Switch (a game is a Ringtails game when the faction adult template carries `PandabornRingtailsSpec`), load-time compatibility check, factory (adult, kit, grown kit), save registration |
| `RingtailRestRootBehavior` | The rest window: a root behaviour inserted just above `WorkerRootBehavior`; runs the game's `SleepNeedBehavior`, `NeederRootBehavior`, `WanderRootBehavior` |
| `RingtailCoat` | Red panda coat from `PandabornRingtailSpec.Textures` in `PostInitializeEntity` |
| `RingtailGrowth` | A kit becomes a Ringtail adult at growth 0.995 (vanilla would make an Inkpaw at 1.0) |
| `LoftHousingRule` | Lofts belong to Ringtails: swap an Inkpaw out of a loft for a Ringtail; a homeless Ringtail takes a loft bed |

**Data it needs** (main mod / catalogue): `PandabornRingtailsSpec` on the Inkpaw adult template;
`RingtailAdult|RingtailChild.Inkpaws` templates with `PandabornRingtailSpec` (generator: `proto/ringtails/tools/derive.py`;
walking speed equal to Inkpaws, `BaseSlowedSpeed = BaseWalkingSpeed` so loads never slow them, lifting 14); the
worker type blueprint; Ringtail workplaces with `PandabornRingtailWorkplaceSpec`; lofts with `PandabornLoftSpec`; the
alias `BackwardCompatibleTemplateNames: [RingtailAdult.Inkpaws]` (and the kit) on the Inkpaw templates, permanently;
worker outfits for the Ringtail worker type.

**Saved**: nothing of its own. Ringtails are ordinary entities saved under their template name; the game reloads them
because `RingtailService` registers the hidden templates in `TemplateNameMapper`.

**Fails safely** (each checked once at load, before any Ringtail exists):

| Private member | If missing |
|---|---|
| `TemplateNameMapper._templates` | Feature off. Saved Ringtails load as Inkpaws (alias) with name, age, needs, home; their Ringtail jobs drop. One notice. Verified in game (`rt-fallback1`) |
| `BehaviorManager._rootBehaviors` | No new Ringtails; existing Ringtails work round the clock (vanilla critical sleep keeps them alive). One notice |

Implicit (public) dependencies: the behaviour order (Worker root before Needer root); vanilla growth at 1.0;
`BeaverTextureSetter` in `InitializeEntity`. If the module itself is off (API check), nothing registers the hidden
templates, so saved Ringtails load as Inkpaws through the alias, exactly as in the first row: the save stays loadable
and keeps every colonist.

**Open item for the owner of Bell**: `Pandaborn.Bell` locks the day length at dawn; the rest window here reads the
slider live. Ideally both read the same value (`BellService.Current` locked hours when Bell is on).

<!-- api:begin -->
<!-- api:end -->
