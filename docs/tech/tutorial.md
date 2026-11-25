# The Inkpaws tutorial: a proposal the content lane can generate

**Status, corrected 2026-11-25: built.** This page was written as a proposal and its first line still said
"not built". Since then: `catalogue/tutorial.toml` and `catalogue/text/tutorial.json` generate the Inkpaws'
tutorials (`StartingFactionSpec`, every vanilla tutorial switched off by a faction modifier, the `Stairs.Folktails`
alias on `Stairs.Inkpaws`); the module `Pandaborn.Tutorial` ships the "have N of a good" step and is switched on in
`catalogue/rules.toml`. Proven in game: the step type, a stage achieved, the tutorial resumed after a save and a
reload (`p3-bell-tutorial-2`); every Pandaborn tutorial dormant with no stages in a Folktails game, and the vanilla
chain intact there (`p3-nodata-2`); the generated stages build in an Inkpaws game (every gate run since, last
`gate-20261114-171322`). The order of the stages was changed on 2026-11-25 (DESIGN.md change log: the woodcutter
first, then water and food, poles, dens, a cistern, the inventor, the Steamer, the bell, flumes, tea last), so where
"Shape" below and `catalogue/tutorial.toml` differ, the catalogue is right. Not yet done: the chain played from a
new game to its end, on the full build and on the data-only build (runs N15a and N15b of
`docs/tech/needs-game-run.md`).

Original status line: proposal; revised for DESIGN.md 4bf5c97 (Pole Mill first, forester-planted tea and pepper, tea at the
Teahouse, buildings hidden until their code's data ships). The content lane generates the tutorial from `catalogue/tutorial.toml`. Mechanism verified in game in stage 0 (`docs/tech/stage0.md`, check 4): a faction gets the
tutorial system with `StartingFactionSpec`, every vanilla `TutorialSpec` is switched off for it by faction blueprint
modifiers, and its own tutorial (a dormant `TutorialSpec` switched on by a modifier) runs with vanilla step types.

## Shape

One short tutorial per idea, chained by `RequiredTutorialIds`, each one or two stages, never two new ideas at once
(DESIGN.md, "The first two hours"). The player can close the panel; the vanilla "disable tutorial" setting hides it.

| Tutorial id | Opens after | Stage (intro text says) | Vanilla step type (template) | Done when |
|---|---|---|---|---|
| `PandabornTutorial.Basics` | start | Look around (camera, speed) | `CameraMovementStepSpec`, `GameSpeedStepSpec` | moved, sped up |
| `PandabornTutorial.Water` | Basics | Pump water | `BuildingTutorialStepSpec` (`WaterPump.Inkpaws`, 1) | placed |
| `PandabornTutorial.Food` | Water | Forage and plant shoots | `BuildingTutorialStepSpec` (`GathererFlag.Inkpaws`, 1), `BuildingTutorialStepSpec` (`EfficientFarmHouse.Inkpaws`, 1), `MarkPlantablesTutorialStepSpec` (`PandabornShootBamboo.Inkpaws`, 6) | placed, 6 marked |
| `PandabornTutorial.Poles` | Food | Poles from the Pole Mill (it works like a lumber mill) | `BuildingTutorialStepSpec` (`LumberjackFlag.Inkpaws`, 1), `BuildingTutorialStepSpec` (`LumberMill.Inkpaws` = the Pole Mill, 1), `BuildingTutorialStepSpec` (`PowerWheel.Inkpaws`, 1) | placed |
| `PandabornTutorial.Grove` | Poles | Plant a timber-bamboo grove | `BuildingTutorialStepSpec` (`Forester.Inkpaws`, 1), `MarkPlantablesTutorialStepSpec` (`PandabornTimberBamboo.Inkpaws`, 4) | placed, 4 marked |
| `PandabornTutorial.Homes` | Grove | Dens for the village | `BuildingTutorialStepSpec` (`PandabornDen.Inkpaws`, 2, finished) | two finished |
| `PandabornTutorial.Rituals` | Homes | Afternoons are for tea and naps (tea is drunk at the Teahouse) | `BuildingTutorialStepSpec` (`PandabornHammock.Inkpaws`, 1), `BuildingTutorialStepSpec` (`PandabornTeahouse.Inkpaws`, 1) | placed |
| `PandabornTutorial.Bell` | Rituals | The afternoon bell | `SetWorkingHoursStepSpec` (12) | hours at 12 (the bell's own suggestion message appears too) |
| `PandabornTutorial.Bamboo` | Bell | The first bamboo: poles with no mill | `MarkTreesTutorialStepSpec` | trees marked (days 5 to 8, when the grove is grown) |
| `PandabornTutorial.Flume` | Bamboo | Lead the water to a second grove | `BuildingTutorialStepSpec` (`PandabornScoopWheel.Inkpaws`, 1; logs and poles, no gears), `BuildingTutorialStepSpec` (`PandabornFlume.Inkpaws`, 3) | placed |
| `PandabornTutorial.Drought` | trigger `SurvivedFirstDroughtTrigger`-style, or Flume | Cisterns carry the village | `BuildingTutorialStepSpec` (`PandabornCisternSmall.Inkpaws`, 1) | placed |
| `PandabornTutorial.Ringtails` | Drought | The Moon Loft | `BuildingTutorialStepSpec` (`PandabornMoonLoft.Inkpaws`, 1, finished) | finished (only when the Ringtails module ships) |

Cycle 2 onwards (paddy spout, festival, tea on dry ground) is better taught by the buildings' own descriptions than by
more tutorial stages; add them later only if playtests show players miss them.

Stage text is our loc (`Pandaborn.Tutorial.<Id>.<Stage>`); step text is the game's own per step type (only
`SelectEntityStepSpec` takes custom text), which already reads well ("Place a Water Pump", "Mark trees for cutting").

## Rules that come from the in-game crashes (validator requirements)

1. **Every template a step names must be in the faction's template collections, with exactly one toolbar button.**
   A `BuildingTutorialStepSpec` (also `ConnectBuildings`, `UnlockBuilding`, `AccumulateScienceForBuilding`,
   `SelectStockpileGood`, `ChangePausedState`, `DecreasePriority`, `IncreaseDesiredWorkers`) naming a template the
   faction lacks throws `ArgumentException: Building not found` inside `TutorialService.Load`, at the start of every
   Inkpaws game (verified, run `s0-inkpaws-3`). Stages are built eagerly, so this applies to every stage of every
   tutorial the faction can see, not only the current one. The generator must emit stages only for templates it also
   emits into the faction's collections, and the validator must check every step's template names against them.
2. **A template must answer to `Stairs.Folktails`.** `StairsUnlockedTrigger.Load` calls
   `TemplateNameMapper.GetTemplate("Stairs.Folktails")` in any faction with `StartingFactionSpec` and throws
   `TemplateMappingException` otherwise (verified, run `s0-inkpaws-4`). Requirement: `Stairs.Inkpaws` carries
   `"BackwardCompatibleTemplateNames": ["Stairs.Folktails"]`, and the validator fails a faction with `StartingFactionSpec`
   whose collections lack a template named or aliased `Stairs.Folktails`.
3. **Modifier files are `.optional.blueprint.json` at a path with no base** (the 18 vanilla switch-offs and the switch-on
   of our dormant tutorial), or they become standalone blueprints in every game.
4. **Our `TutorialSpec` base files are dormant** (`RequiredTutorialIds: ["PandabornNever"]`, `Stages: []`), so Folktails
   and Iron Teeth games (which build every `TutorialSpec`) never run or build them; the Inkpaws faction modifier gives
   them their real requirements and stages. Stage files may carry their steps directly: stage blueprints are only built
   when a tutorial lists them.
5. **Only buildings that are visible.** Buildings that wait for code are hidden until the code's data ships (DESIGN.md,
   2026-11-14). A hidden building has no toolbar button, and a building step needs exactly one, so the generator must
   emit a stage only when every template it names is visible in that build, and drop or replace it otherwise (for example
   the flume stage while the water module's data is off).
6. `PowerBuildingsTutorialStepSpec` is unusable (it hard-codes the Folktails shaft buttons). `BeaverBirthStepSpec` is not
   saved (after a reload it waits for a new birth).

## "Have N of a good": worth one small step type

No vanilla step counts goods, and two of the stages above would read better with one ("Have 20 poles", "Store 10
shoots"). It is about 60 lines in a module (say `Pandaborn.Tutorial`), all public API:

* spec `PandabornGoodAmountStepSpec { GoodId, Amount }` in `Pandaborn.Specs`, used only in our stage blueprints;
* `class GoodAmountStepDeserializer : IStepDeserializer` (`step.Specs[0] is PandabornGoodAmountStepSpec`), bound with
  `MultiBind<IStepDeserializer>()`, producing a `TutorialStep` whose `ITutorialStep.Achieved()` reads the district
  stock (`DistrictCenterRegistry` + `DistrictInventoryRegistry`/`GoodService` totals) and `Description()` returns
  "Have {Amount} {good plural}" from our loc;
* fallback: if the module is off, `TutorialStageService` skips a step no deserializer accepts (verified in code:
  unmatched steps are dropped), so the stage simply has one step fewer. That makes it safe to ship.

Recommendation: build it with the tutorial, not before; the table above works without it.

## For the catalogue lane: the "have N of a good" step (built, module `Pandaborn.Tutorial`)

The step type exists in code (`src/code/Pandaborn.Tutorial`, spec in `Pandaborn.Specs`). Use it like any vanilla step
type in `catalogue/tutorial.toml`:

```toml
[stages."PandabornTutorial.FirstPoles"]
waits_for = "Tutorial"          # the module id in modules.txt; leave the stage out of a -NoCode build
steps = [{ PandabornGoodAmountStepSpec = { GoodId = "Plank", Amount = 20 } }]
```

which the generator writes into the stage blueprint exactly as a vanilla step:

```json
{
  "TutorialStageSpec": { "Id": "PandabornTutorial.FirstPoles", "IntroLocKey": "Pandaborn.Tutorial.PandabornTutorial.FirstPoles" },
  "Children": {
    "Step1": { "PandabornGoodAmountStepSpec": { "GoodId": "Plank", "Amount": 20 } }
  }
}
```

* Fields: `GoodId` (string, a good id in the faction's goods collections: `Plank` shows as Poles for Inkpaws) and
  `Amount` (int, at least 1, default 1). Nothing else.
* Achieved while the settlement's **available stock** of the good (all finished districts: stockpiled, in output
  buffers, on the way to storage; `ResourceCountingService.GetGlobalResourceCount(..).AvailableStock`) is at least
  `Amount`. It is re-read every frame, so it can become un-achieved if the stock is spent before the player continues
  (as vanilla building steps do when a building is demolished).
* The step text is ours: `Pandaborn.Tutorial.HaveGoods` = "Have {0} {1} ({2}/{0})" (amount, the good's plural name,
  stock now, capped at the amount), shipped by the module (`Localizations/enUS_PandabornTutorialSteps.csv`).
* **Safe to generate even when the module is off**: the game offers each step to every step reader and silently drops
  one nobody reads (`TutorialStageService.GetSteps`), so the stage keeps its other steps; a stage whose only step is
  this one becomes intro text plus Continue. `waits_for = "Tutorial"` is still cleaner.
* **It never throws**: a `GoodId` the faction lacks reads as its id and is never achieved (logged once). The validator
  should still check `GoodId` against the faction's goods, as it checks building steps' templates.
* Unlike building steps it names no template and has no toolbar button, so the two crash rules above do not apply to it.
* Proven in game: run `p3-bell-tutorial-2` (docs/tech/stage0.md, "Code phase 3").
