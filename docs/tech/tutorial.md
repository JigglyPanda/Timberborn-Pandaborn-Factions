# The Inkpaws tutorial: a proposal the content lane can generate

Status: proposal (not built). Mechanism verified in game in stage 0 (`docs/tech/stage0.md`, check 4): a faction gets the
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
| `PandabornTutorial.Poles` | Food | Bamboo is cut straight into poles | `BuildingTutorialStepSpec` (`LumberjackFlag.Inkpaws`, 1), `MarkTreesTutorialStepSpec`, `BuildingTutorialStepSpec` (`Forester.Inkpaws`, 1) + `MarkPlantablesTutorialStepSpec` (`PandabornTimberBamboo.Inkpaws`, 4) | flag, trees marked, grove planted |
| `PandabornTutorial.Homes` | Poles | Dens for the village | `BuildingTutorialStepSpec` (`PandabornDen.Inkpaws`, 2, finished) | two finished |
| `PandabornTutorial.Rituals` | Homes | Afternoons are for tea and naps | `BuildingTutorialStepSpec` (`PandabornHammock.Inkpaws`, 1), `BuildingTutorialStepSpec` (`PandabornTeahouse.Inkpaws`, 1) | placed |
| `PandabornTutorial.Bell` | Rituals | The afternoon bell | `SetWorkingHoursStepSpec` (12) | hours at 12 (the bell's own suggestion message appears too) |
| `PandabornTutorial.Flume` | Bell | Lead the water | `BuildingTutorialStepSpec` (`PandabornScoopWheel.Inkpaws`, 1), `BuildingTutorialStepSpec` (`PandabornFlume.Inkpaws`, 3) | placed |
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
5. `PowerBuildingsTutorialStepSpec` is unusable (it hard-codes the Folktails shaft buttons). `BeaverBirthStepSpec` is not
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
