# Water toolkit: feasibility and technical design

Status: research note, 2026-11-14, game 1.1.2.8, followed by an in-game prototype the same day. The sections below
the summary are the original study (read from the decompiled source); **"Prototype results" at the end records what
the game actually did** and overrides the study where they differ.

Paths: **DC** = `E:\PandabornDev\reference\decompiled\<Assembly>.dll\<Namespace>\`, **BP** =
`E:\PandabornDev\reference\Blueprints\`. Third-party mods decompiled (read only, technique only) into
`E:\PandabornDev\reference\mods-decompiled\{barkimedes-screw,timber-commons,automation,simplefloodgatetriggers}`.

## Summary

| # | Feature | Verdict | Value for risk |
|---|---|---|---|
| 1 | Bamboo spout | **Data only** (restyled `FillValveSpec`) | Highest: free, robust |
| 2 | Bamboo pipeline as an open **flume** | **Small code** (one ~40-line component, no Harmony). Zero-code prototype possible | Very high: the headline, real water, low risk |
| 3 | Crop moisture zones | Mostly **data**; grove spreading from planted parents and fractional depth bands need code | High |
| 4 | Mist catcher | **Data** for the Water *good*; **small code** for weather scaling or for water poured into the world | Medium |
| 5 | Noria | **Probably data** (self-powered pump); small code fallback | Medium, needs a prototype |
| 6 | Treadwheel lift | **Probably data**, but power follows *walking* speed, which pandas lack | Medium |
| 7 | Charcoal filter | Data-only "badwater skimmer" exists; a true filter that passes cleaned water is **small code** | Lower |
| – | Virtual pipe network | **Code**, sizeable | Keep only for a later culvert or siphon piece |

No feature needs Harmony. No feature needs another mod.

## How the water simulation works (what everything below relies on)

* **Grid of stacked columns.** Each map cell holds one or more water columns with `Floor`, `Ceiling`, `WaterDepth`,
  `Overflow` and `Contamination` (DC `Timberborn.WaterSystem\WaterColumn.cs`, `WaterSimulator.cs`). Terrain and full
  obstacles split columns. A horizontal obstacle (`AddHorizontalObstacle`) puts a watertight floor under a cell, so
  water can sit above air. That is how raised aqueducts and the vanilla Impermeable Floor work.
* **Obstacle kinds** (`IWaterService`, all public):
  * `AddFullObstacle` / `RemoveFullObstacle`: a solid cell.
  * `AddHorizontalObstacle`: a floor.
  * `SetPartialObstacle(cell, height)`: a fractional dam. This is how Dam 0.65 and floodgates work, through
    `WaterObstacle` (DC `Timberborn.WaterObjects\WaterObstacle.cs`).
  * `SetInflowLimit(cell, cms)`: caps the flow into a cell. Throttling and fill valves use it.
  * **`AddDirectionLimiter(cell, FlowDirection)`**: a per-cell axis lock. This is the key finding (next section).
* **No per-edge walls.** There is no wall thinner than a tile and no per-edge blocking, except what the direction
  limiter gives.
* **Ticking.**
  * One tick is 0.6 s (`BP Configurations\TickTime`).
  * `TickableSingletonService.TickAll` runs in this order: `FinishParallelTick`, then the singleton `Tick`s, then
    `StartParallelTick`.
  * The simulation (`WaterSimulator.StartParallelTick` → `WaterSimulationTaskStarter.Simulate`) runs on worker threads
    in 2 substeps per tick, at the same time as the next round of entity ticks.
  * Entity components must read only `IThreadSafeWaterMap`, a snapshot copied in its singleton `Tick`.
  * Water added or removed through `IWaterService` is queued (`WaterChangeService.EnqueueWaterChange`). It is applied
    by `UpdateWaterChangesTask` at the end of the next parallel tick.
  * The amount actually removed is read one tick later (`IWaterRemovalService.GetWaterChangeUnsafe`), and only from a
    singleton `Tick`. Vanilla `WaterInputService` does exactly this.
  * So any code that moves water runs on the main thread and sees a 1–2 tick lag. That is safe. Nothing of ours needs
    to touch the worker threads.
* **Contamination.**
  * Each column holds clean and contaminated parts.
  * `AddContaminatedWater` / `RemoveContaminatedWater` change only the contaminated part. `AddCleanWater` dilutes.
  * The fraction is capped by `MaxWaterContamination` 1.0.
  * Contamination diffuses between columns (`SimulateContaminationTask`, `DiffusionRate` 0.45) and respects direction
    limiters.
* **Evaporation.**
  * The rate is `NormalEvaporationSpeed` 0.0001, or `FastEvaporationSpeed` 0.001 when depth < 0.02, per second, times
    a saturation factor.
  * The factor is `0.0595 n² + 0.101 n + 0.72` with `n = 10 - clusterSaturation`
    (`SoilMoistureSimulationTaskStarter.InitializeEvaporationModifiers`).
  * A 1-wide channel has saturation about 1, so its factor is **about 6.5×**. A lake's is about 1.2×.
* **The flow-limiter arrays are not saved.** Valves re-apply them in `OnEnterFinishedState` on load
  (`FlowLimiterService` has no save). Our parts can do the same.

## 1. Bamboo pipeline

### Option (a): a true open channel. **Feasible, recommended, as a 1-wide "flume".**

The simulation already has the thin watertight part the design needs: the **direction limiter**. Vanilla
`FillValve.OnEnterFinishedState` and `ThrottlingValve.OnEnterFinishedState` call
`_waterService.AddDirectionLimiter(coords, orientation.ToFlowDirection())`, as does `DirectionalWaterSource`.

Semantics (DC `Timberborn.WaterSystem\FlowLimitCalculator.cs`, used in `OutflowsUpdateTask.GetOutflow` and in
`SimulateContaminationTask`):

* `CanInflowInDirection(target)`: a limited cell accepts water **only from the cell behind it**
  (`limit == direction`).
* `CanOutflowInDirection(origin)`: a limited cell sends water only **forward or backward** along its axis
  (`limit == ±direction`).
* So **both side faces are watertight in both directions**, even with no wall tile beside them.
* In a chain of same-direction cells, backward flow is refused by the previous cell. The chain is **strictly
  one-way**.
* Its last cell refuses inflow from the front, so a flume never drains back out of the paddy it feeds.
* The limiter is stored at the **column floor** (`Index2DTo3D(index, waterBase)`). The flume cell must therefore be
  a column floor: either terrain, or a horizontal obstacle at its own z (`FinishableHorizontalWaterObstacleSpec`,
  data).
* It holds at any water depth, because the check uses the floor.
* A second horizontal obstacle at z+1 (a lid) caps the depth at one block. Vanilla valves do this: obstacles at z0
  and z1.

**Flow.**

* Flow is pressure-driven by surface height. Water enters if the source surface is above the flume floor, runs
  level or downhill, and steps down any number of levels (flow into a neighbour column with a lower floor is
  ordinary).
* It can never run uphill.
* On a dry, level step it needs 0.1 of head before it spills forward (`WaterSpillThreshold`).
* **Fixed flow:** put an inflow limit on the intake cell. This is exactly `ThrottlingValve`: `SetInflowLimit`, plus a
  full obstacle when the limit is 0.

**Corners.**

* A single limited cell cannot turn: a cell locked to "Right" refuses water arriving from below.
* A turn needs an **unlimited** cell whose two outer faces are sealed by solid cells (full obstacles).
* So corners and splits are **2x2 "turning box" parts**: one water cell and three solid posts. A splitter is the
  same idea with one solid side.

**Implementation.**

* *Production version:* our own spec and component, `PandabornFlumeSegmentSpec` → `FlumeSegment : BaseComponent,
  IAwakableComponent, IFinishedStateListener`.
  * `OnEnterFinishedState`: `AddDirectionLimiter(_blockObject.Coordinates, _blockObject.Orientation.ToFlowDirection())`.
  * `OnExitFinishedState`: `RemoveDirectionLimiter`.
  * It uses only public types (`IWaterService`, `FlowDirection`, `FlowDirectionExtensions`, `BlockObject`).
  * Not tickable, so it costs nothing per tick. It needs no save.
* *Gate:* a `PandabornFlumeGate` that sets a fixed inflow limit. Or reuse `ThrottlingValveSpec` in data, which also
  gives automation for free.
* *Zero-code prototype:* every segment is a restyled `ThrottlingValveSpec` blueprint.
  * Use `DefaultOutflowLimitEnabled: false` for plain segments, and `true` with a preset limit for the gate.
  * Size 1x1x1, with horizontal obstacles at (0,0,0) and (0,0,1).
  * Water-extention ships `ThrottlingValveSpec` in a pure-data 1.1 mod, so internal spec records do load from mod
    blueprints.
  * The drawback is that each segment shows a valve panel and ticks.
* *Trestles:* flume parts with leg variants whose lower blocks use `Occupations: None` (the Water-extention "U" pipe
  trick). Or stack flumes on platform-like trestle parts. The flume floor is a horizontal obstacle, so water under the
  trestle flows freely.

**Player-facing rules this implies.**

* Water runs one way, along the arrows. It never leaks out of the sides, never comes in from the sides, and never
  runs backwards. A flume can cross a flooded field without mixing with it.
* The intake end must sit in water whose surface is above the flume bed.
* Keep the flume level or falling. It can drop any number of steps but can never climb (use a noria or lift).
* The gate sets the maximum flow. Less arrives if the source is low or the run is long and flat.
* Turns and branches use a turning box.
* At the end, the water pours into whatever is in front. Put a spout there to hold a set depth.
* Vanilla fill valves and throttling valves are themselves one-cell direction-limited channels, so they drop into a
  flume line unchanged. Vanilla stream gauges and automation work on the pools at either end.
* A lidded segment can carry a path or platform on top, so it can be crossed.
* A ground-level flume moistens about 1–2 tiles on each side, because a thin cluster has low saturation (crop report,
  `ClusterSaturationCalculationTask`). That gives a natural "moist strip" along every flume.

**Risks.**

* The limiter is undocumented behaviour. It is used by three vanilla systems, so it should be reasonably stable.
* The flume floor must be a column floor (handled by the part's horizontal obstacle).
* The last writer wins per cell: another mod's valve on the same cell would clear our limit (only one building per
  cell, so unlikely).
* Thin water evaporates about 6.5× faster. Very thin films (< 0.02 deep) on a steep run lose about 0.0065/s per tile.
  Gate rates must keep runs wetter than that; measure in the prototype.
* Deep water in a lid-less segment stacks into a 1-wide "wall of water". Always lid segments.
* Beavers cannot walk through a water cell, so give flumes path-on-top variants.

**Smallest prototype.**

* Flat test map. A `DevWaterSource` (dev-mode building, `BP Buildings\Water\DevWaterSource`) fills a 3x3 pond.
* Ten restyled `ThrottlingValve` 1x1 segments run out of the pond on the ground; then two drop one level; then a 2x2
  turning box built from Levee-style solid blocks around an empty cell.
* Next to the flume, an unlimited dry strip of ground.

*Automated check (devharness):*

* After 600 ticks, read `IThreadSafeWaterMap.WaterDepth` at the flume cells (> 0.02), at the outlet basin (> 0), and
  at the side strip cells (== 0, proves sealing).
* Then raise the outlet basin above the flume end, run 300 ticks, and check that the last flume cell's depth did not
  rise (proves one-way).

### Option (b): a "virtual" pipe. **Feasible in code; not recommended as the main pipe.**

How vanilla moves water (DC `Timberborn.WaterBuildings\`):

* **`WaterMover`** (Mechanical Pump, Compact Mechanical Pump, Barkimedes Screw):
  * It is a `TickableComponent`.
  * Each tick it moves `TickIntervalInSeconds × PowerEfficiency × FlowRate`, only if `ActiveAndPowered`,
    `WaterOutput.HasSpaceForWater` and `WaterInput.IsUnderwater`.
  * It splits the amount by the input's contamination: `GetCleanMovementScaler`, then `DemandClean/Contaminated`, then
    `WaterOutput.AddWater(clean, contaminated)`.
* **`WaterInput`** (public) keeps a buffer.
  * When the buffer is under 3× the need, `DemandCleanWaterAmount` queues a `RemoveCleanWater`.
  * `WaterInputService` (an `ITickableSingleton`) credits the amount really removed one tick later.
  * The buffer is saved.
* **`WaterOutput.AvailableSpace`** = `out.z + DistanceToGroundOffset − 0.1 − WaterHeightOrFloor(out)`. That is the
  depth cap.
* **Intake coordinates** come from `WaterInputFixedCoordinates` or `WaterInputPipeCoordinates`. The latter scans down
  to `MaxDepth` and recomputes on block or terrain events.

How other vanilla water buildings work:

* **Water Dump / Discharge:** `ManufactoryWaterProducer` adds clean water per production progress.
  * It works **only for a recipe with Id `FlowingWater`** (hardcoded).
  * The amount is Water ingredient × 0.2 (`WaterGoodToWaterAmountConverter`).
* **Fill Valve:** see feature 3.
* **Throttling Valve:** described above.
* **Floodgates:** partial obstacles.
* **Badwater Pressurizer and Badwater Dome:** these act on the map's water source under them
  (`UnderstructureConstraint` → `UnderlyingWaterSource`).
  * `WaterSourceDischarger` disables that source's `DroughtWaterStrengthModifier`.
  * `WaterSourceRegulator` opens and closes it.
* **Water sources** are `WaterSource : IWaterSource`, registered with `IWaterService.RegisterWaterSource`.
  * Strength is the product of `IWaterStrengthModifier`s; drought sets it to 0.
  * The water is added in the parallel `UpdateWaterSourcesTask`.

**Connected networks.**

* Tubeways keep an `Array3D<Tube>` map singleton (`TubeMap`), filled in `OnEnterFinishedState` and emptied in
  `OnExitFinishedState`. Connectivity is queried live and nothing is saved.
* Mechanical graphs (`MechanicalGraphManager`, `MechanicalGraphFactory`) are rebuilt from finished nodes on load.
  The graph itself is not saved either.
* Saved references between entities, where needed, use `ReferenceSerializer.Of<T>()` (seen in
  SimpleFloodgateTriggers' `StreamGaugeFloodgateLinkSerializer`).

**Design if ever built.**

* A `PipeNetworkMap` singleton (`Array3D` of segments), with a BFS rebuild on finished-state enter and exit.
* An intake carrying vanilla `WaterInputSpec` plus `WaterInputPipeSpec`, and an outlet carrying vanilla
  `WaterOutputSpec`.
* A `PipeNetworkService : ITickableSingleton` that, per network, moves
  `min(rate × 0.6, demand, outlet.AvailableSpace)`, but only while
  `WaterHeightOrFloor(intake) > outlet level + ε`. This gravity guard prevents loops and perpetual motion.
* The contamination split is preserved exactly as `WaterMover` does it.
* Nothing to save beyond the vanilla `WaterInput` buffer and per-network settings.
* Roughly 400–600 lines plus a UI panel and particles.

**Why not as the headline.**

* The water is invisible between its ends, so "a contraption the player watches fill" is lost.
* It duplicates physics the game already does.
* It needs its own network UI.
* It adds exploit surface.

**Where it is worth it later:** a short **culvert or siphon** piece that hops a flume under a road or over a ridge.
That is the one thing a flume cannot do.

### Option (c): wide aqueduct troughs. **Data only; good fallback for big canals.**

* A 3-wide trough: `WaterObstacleSpec` walls at x=0 and x=2 (`FinishableWaterObstacleSpec` Height 1), a
  `FinishableHorizontalWaterObstacleSpec` floor at the middle cell, plus `ImpermeableFloorSpec` and `SoilBarrierSpec`.
* This is exactly Water-extention's `Aqueduct_P_1X` and works on 1.1.
* Downsides: chunky (3 tiles wide), turns need wide pieces, and water can still flow both ways.

### Recommendation

Build the **flume** (option a):

* 1-wide parts: straight, step-down, leg variants, lidded or walkable, a 2x2 turning box, a 2x2 splitter, and a gate.
* Prototype it first with restyled `ThrottlingValve` blueprints (zero code). Then replace them with the 40-line
  `FlumeSegment` component.
* Add a culvert (option b, short fixed length) only if playtests ask for crossings.
* This matches the design's "fixed flow per pipe, clear arrows, no pressure or mixing puzzles, connects to vanilla
  valves and sensors" almost literally.

## 2. Noria and treadwheel lift

**How water wheels read current.** `WaterPoweredGenerator.Tick` (DC `Timberborn.PowerGeneration\`):

* For each `WaterPoweredGeneratorSpec.Blocks` cell that `CellIsUnderwater`, it takes
  `IThreadSafeWaterMap.WaterFlowDirection(cell)` (the flow vector at the column top) projected on
  `ExpectedWaterDirection`.
* It ignores values under `MinRequiredOutflow` (0.15 in vanilla) and averages the rest.
* It sets `MechanicalNode.SetOutputMultiplier(|rotation|)`, which is **unclamped**. Power is nominal × flow, hence the
  "HP per m³/s" label.

**How pumps lift:** `WaterMover`, as above. Lift height is simply where `WaterOutputSpec.WaterCoordinates` sits in the
building, and how deep `WaterInputPipeSpec.MaxDepth` reaches. The Barkimedes Screw is only this: a 1x4x3 vanilla
pump blueprint with output at (0,3,2), 0.2 m³/s, 30 power, and no Harmony.

**One building doing both: probably data only.**

* Give the building one `MechanicalNodeSpec` with both `PowerOutput` P and `PowerInput` D.
* Add `TransputProviderSpec` with an empty `Transputs` list, so it joins no shafts. `MechanicalNode.InitializeTransputs`
  dereferences the spec, so the spec must exist, but the list may be empty.
* Add `WaterPoweredGeneratorSpec`, `MechanicalBuildingSpec`, `WaterInputSpec` + `WaterInputFixedSpec`,
  `WaterMoverSpec` and `WaterOutputSpec`.
* `MechanicalGraphManager.AddNode` gives an unconnected node its own graph. `MechanicalGraph` sums supply and demand
  from the node's actuals. So the lift rate becomes `min(P × current / D, 1) × WaterPerSecond`: no current, no lift;
  a strong current gives full rate.
* Nothing in the code forbids a node from being both generator and consumer (only UI branches on `IsGenerator`).
* **Prototype required.** The UI will show power numbers, which may need hiding.
* Fallback: a ~60-line `NoriaLift` component that reads `WaterFlowDirection` like `WaterPoweredGenerator` and calls
  the public `WaterInput` / `WaterOutput` like `WaterMover`.

**Treadwheel.**

* Vanilla `WalkerPoweredGenerator` (Folktails power wheel) sets strength = Σ workers' **`MovementSpeed`** bonus
  multiplier / `MaxWorkers`.
* A self-powered treadwheel lift is the same isolated-node trick with `WalkerPoweredGeneratorSpec` plus a
  `WorkplaceSpec`.
* **Design catch:** Inkpaws are slow walkers, so an Inkpaw on the wheel lifts *less*. Either make it a Ringtail job,
  which fits "nimble" and is still data, or write a small generator that uses `WorkingSpeed`.

**What limits lift height.**

* The building's height: output z is fixed in the footprint.
* `WaterOutput` stops when the outlet pool reaches `out.z + offset − 0.1`, so a lift never floods.
* The output cell must stay clear. Water-extention warns that a levee on a pipe output crashes the game; keep the
  output cell inside the building's own occupied blocks, as vanilla pumps do.

**Player rules.**

* The noria turns only in a current of at least 0.15 and lifts more in faster water, up to its rated flow.
* It lifts N levels (the model height) and stops when the top basin is full.
* A flume is a fast current, so a noria at a flume drop is a natural combo.

**Prototype.**

* A noria data blueprint in a dev river, plus one with no current.
* Check: the outlet basin depth is > 0 after 600 ticks with current, and == 0 without current.
* Check that `MechanicalNode.Graph.Nodes.Count == 1`.

## 3. Bamboo spout. **Data only.**

`FillValve` (DC `Timberborn.WaterBuildings\FillValve.cs`; BP `Buildings\Landscaping\FillValve\FillValve.Folktails`):

* A 1x2 building. Block 0 is a direction-limited channel cell. Block 1 (`Occupations: Middle`, `MatterBelow: Any`)
  marks `OutputCoordinates` (0,1,0).
* Each tick it compares `WaterHeightOrFloor(Output)` with the target height.
  * It opens the inflow limit in steps of 0.005 while the pool is low (hysteresis `OverflowLimit` 0.02).
  * It closes along `ClosingCurve` when the pool is high.
  * It becomes a full obstacle when shut.
* The target range is from `MinTargetHeight` (the floor of the output column, via `TryGetColumnFloor`) to
  `MaxTargetHeight` (valve z + 1).
* The default is floor + `DefaultTargetHeightOffset` 0.5.
* Placed on a terrace edge, the output block hangs over the lower field. The output column's floor is the field, so
  it **holds the pool below at the set depth**.
* It is automatable for free (`AutoAutomatableNeeder` is decorated).

**The spout itself:**

* A new blueprint with `FillValveSpec { DefaultTargetHeightOffset: 0.3, DefaultTargetHeightEnabled: true, OverflowLimit: 0.02, OutputCoordinates: (0,1,0) }`.
* Cheap cost, a bamboo model, and horizontal obstacles at z0 and z1.
* The vanilla panel still lets the player change the depth, which is good.

Rules:

* Water feeds in from behind (a flume or pond at spout level).
* The field in front, or below, is kept topped up to the set depth, never higher.
* Up to one block above the spout's own base.

Risk: `FillValveSpec` is an internal record and could be renamed by an update. Have `tools/validate.py` check spec type
names against the game DLLs.

Prototype and test:

* Pond at z, spout at the edge, a 4x4 paddy at z−1.
* After 900 ticks, the paddy depth is 0.3 ± 0.05.
* Open a drain, run 600 more ticks, and the depth is again 0.3 ± 0.05.

## 4. Mist catcher

* **Water good from nothing: data only, valid.**
  * Vanilla `Recipe.Water` has `"Ingredients": []`.
  * `Manufactory.IsReadyToProduce` needs no ingredients.
  * `ProductionIncreaserSpec` (Numbercruncher) advances production every tick with **no workers**
    (`Manufactory.IncreaseProductionProgress(FixedDeltaTimeInHours)`).
  * So: `ManufactorySpec { ProductionRecipeIds: ["PandabornMistWater"] }` + `ProductionIncreaserSpec`, a recipe with
    no ingredients and `Products: [Water × 1]`, plus storage.
  * Haulers carry it off.
* **Tied to weather: small code, no Harmony.**
  * Add a component implementing the public `IManufactoryLimiter`. `Manufactory.Awake` collects them with
    `GetComponents`.
  * Its `ProductionEfficiency()` returns, for example:
    * 1.0 in temperate weather;
    * 0.35 in drought (`HazardousWeatherService.CurrentCycleHazardousWeather is DroughtWeather` and
      `WeatherService.IsHazardousWeather`);
    * optionally more around dawn (`IDayNightCycle.DayProgress`).
  * All of these are public. There is no "rain" weather in the game; "wet" can only mean temperate, or time of day.
* **Water poured into the world** (fills a basin you can pipe from): **small code.**
  * `ManufactoryWaterProducer` only fires for recipe Id `FlowingWater`, which costs 3 Water goods. So it cannot be
    reused for water from nothing.
  * Write a component that listens to the public `Manufactory.ProductionProgressed` and calls the public
    `WaterOutput.AddCleanWater`.
  * Do **not** use `WaterSourceSpec` on a building. `WaterSource` always gets `DroughtWaterStrengthModifier`, so it
    stops in drought. It also registers with the simulation in `InitializeEntity`, which very likely means before
    construction finishes.

Rules: a small steady amount, always some even in drought, more in good weather. Choose either stored Water (feeds
pandas) or a basin (feeds flumes).

Test: after 1 game day in drought, the stock is > 0 and smaller than after 1 temperate day.

## 5. Charcoal filter

**How contamination works:** per column, as above. The vanilla "Contamination Barrier" is only
`SoilBarrierSpec.BlockContamination` (soil contamination, `Timberborn.SoilContaminationSystem`). It never touches
water.

* **Data-only "badwater skimmer".**
  * `ManufactoryWaterContaminationConsumer` removes contaminated water only, 0.2 per unit, from the intake column.
  * It fires for **any recipe whose Products contain the good `Badwater`**
    (`WaterContaminationGoodToWaterContaminationAmountConverter`).
  * Its limiter runs only when the input is contaminated.
  * So: a workplace with `WaterInputSpec` + `WaterInputPipeSpec` + `ManufactoryWaterContaminationConsumerSpec`, and a
    recipe with `Fuel: PandabornCharcoal` and `Products: [Badwater × 1]`.
  * It strips badwater and burns charcoal. But it **removes volume**, outputs Badwater goods that need storage, and
    needs a worker.
  * Fuel hauling to a workerless (`ProductionIncreaser`) manufactory is unverified.
* **True filter, inline in a flume: small code, recommended if the feature stays.**
  * A flume cell part whose component, each tick, calls `RemoveContaminatedWater(cell, x)` and `AddCleanWater(cell, k·x)`.
  * `x` is limited by `ColumnContamination(cell) × depth` and by a fuel budget from charcoal progress
    (`Manufactory.ProductionProgressed`, or a `GoodConsumingBuilding` like TimberCommons' good-consuming irrigation
    tower).
  * Volume is preserved, and water comes out cleaner downstream. All APIs used are public.

Rules: put the filter box in a flume. While it has charcoal, water leaving it is less contaminated, by a fixed amount
per hour. It does not remove water.

Test: dev badwater source → flume → filter → basin. After 900 ticks, the basin contamination is lower than the
source's by the expected margin, and the basin volume is within 5% of an unfiltered control.

## 6. Crop moisture zones

Full findings: DC `Timberborn.NaturalResourcesMoisture`, `NaturalResourcesReproduction`, `Planting`,
`SoilMoistureSystem`.

**Every plantable needs a `FloodableNaturalResourceSpec`.** `PlantingSpotFinder.CanPlantAt` →
`FloodableNaturalResourceService.ConditionsAreMet` does a dictionary lookup. Land crops use 0/0.

### (i) Paddy crop (rice, lotus): data only, with integer bands

* Use `FloodableNaturalResourceSpec { MinWaterHeight: 1, MaxWaterHeight: 1, DaysToDie }` and
  `WateredNaturalResourceSpec { DaysToDieDry }`.
* Use `PlantableSpec.ResourceGroup` of an aquatic planter group, our own string, matched by our farmhouse's
  `PlanterBuildingSpec.PlantableResourceGroup`.
* **How depth is measured:** `WaterObject.CurrentWaterAboveBase` = `CeiledWaterHeight − base.z`. So the band is in
  **whole blocks**: Min 1 / Max 1 means "any standing water above 0, up to 1.0 deep".
* **Out of band:** the plant is dying, on a timer of `DaysToDie × 0.9–1.1`. Growth pauses, and the timer resets fully
  when the water returns to band (`LivingWaterNaturalResource`).
* **A band such as 0.1–0.6 needs code.** It means replacing `LivingWaterObject.Dry/Flooded` and
  `FloodableNaturalResourceService.WaterDepth`, which is Harmony territory. Clean alternative: accept the integer band.
  A spout preset at 0.3 depth sits inside it anyway.

### (ii) Moist-soil crop (bamboo, cabbage, soybean)

* **Moist** = soil moisture > 0 (`DryObject`, `SoilMoistureService.SoilIsMoist`).
* **Survives drought and regrows: data.** Use `WateredNaturalResourceSpec.DaysToDieDry` large, e.g. 30+.
  * While dry it is browned (`#Dying` model) and paused: growth, yield regrowth and spreading all stop.
  * It resumes when moisture returns.
  * True death is permanent: `LivingNaturalResource.ReverseDeath` is map-editor only. Re-sprouting after real death
    would be code.
* **Harvest without replanting:** a bush pattern (`GatherableSpec.YieldGrowthTimeInDays`, gathered by a gatherer-type
  building) or `CuttableSpec.RemoveOnCut: false`. A `Crop` with `RemoveOnCut: true` is deleted and replanted.
* **Self-spreading: data.**
  * Use `ReproducibleSpec { ReproductionChance }`. The chance applies per eligible adjacent tile per day, with no cap.
  * Spawn rules in `SpawnValidationService.CanSpawn`, all of which must hold:
    * 4-neighbour, same z;
    * moist and uncontaminated soil;
    * `!CellIsField` (never onto planting-marked tiles: **"never takes over fields" is free**);
    * unobstructed (never onto paths or buildings).
  * Self-spawned plants are unmarked, and farmhouses and gatherers in range harvest them. That is the "bonus harvest
    outside the grove" in the design.
* **Catch:** `PlantableReproductionBlocker` stops **planted** (marked) parents from spreading, so a planted grove does
  not spread by itself. Fixing this needs code. Clean options, no Harmony:
  * call the public `Reproducible.UnblockReproduction(blocker)` from our own component, re-applied after planting
    events; or
  * write our own spreader using the public `NaturalResourceReproducer`.
* Spreading only inside a marked grove, or a density cap, needs a custom `ISpawnValidator` (multibound; filter by
  template name).

### (iii) Dry-ground crop (tea, Sichuan pepper): data

* Use `AridNaturalResourceSpec { DaysToDieWet }` (vanilla Succulent, BP `NaturalResources\Trees\Succulent`) plus
  `FloodableNaturalResourceSpec` 0/0.
* It can only be planted where moisture == 0 (`PlantingSoilValidator`: `SoilIsMoist == IsAridResource` rejects).
* It stalls and starts dying when the soil gets wet, and recovers if it dries before `DaysToDieWet`.
* It cannot self-spread: spawning requires moist soil.
* Never combine it with `WateredNaturalResourceSpec`.

### Moisture geography

* Only water creates moisture. There is no building that adds moisture without water (TimberCommons fakes it with
  Harmony on worker threads; we don't need that).
* Reach is about 2 × cluster saturation tiles: a big lake about 16, a 1-wide flume about 2.
* `SoilBarrierSpec.BlockFullMoisture` (Iron Teeth irrigation barrier) carves dry pockets, as data.
* Growth and yield are binary moist/dry. Scaling by moisture level would be code.

### Prototype

* One paddy crop, one moist crop with `ReproducibleSpec` and large `DaysToDieDry`, one arid crop.
* Place them by a flume on the test map.
* Checks:
  * the paddy plant is alive after 3 days with the spout on;
  * it is dying after the spout is closed for 1 day;
  * the moist crop has more than 1 instance after N days, and none on marked tiles;
  * the arid crop is dying after the soil is wetted.

## Tests in general

The devharness can already place buildings. Add a "water probe" check:

* a list of cells;
* a tick count;
* expected ranges for `IThreadSafeWaterMap.WaterDepth`, `ColumnContamination` and `WaterFlowDirection`;
* optionally `ISoilMoistureService` moisture.

Use `DevWaterSource` (dev-mode tool) as a deterministic supply. Run at max speed, read on the main thread after the
singleton tick, and log JSON for `tools/run_game_test.ps1`.

## Robustness across game updates

* **Public API used:** `IWaterService` (all methods), `IThreadSafeWaterMap`, `FlowDirection` and its extensions,
  `WaterInput`, `WaterOutput`, `Manufactory` events, `IManufactoryLimiter`, `IWaterStrengthModifier`, `WeatherService`,
  `HazardousWeatherService`, `IDayNightCycle`, `Reproducible`, `NaturalResourceReproducer`. All are plain interfaces or
  public classes used by many vanilla systems.
* **Internal spec records used from data:** `FillValveSpec`, `ThrottlingValveSpec`, `WaterInputSpec`,
  `WaterMoverSpec`, `WaterOutputSpec`, `WaterPoweredGeneratorSpec`, `WalkerPoweredGeneratorSpec`, the obstacle specs,
  `ReproducibleSpec`, `AridNaturalResourceSpec`, `ManufactoryWaterContaminationConsumerSpec`.
  * A rename breaks loading, not saves.
  * Mitigation: `validate.py` checks every spec key in our blueprints against types in the game DLLs, so the failure
    shows up at build time.
* **Hardcoded strings to watch:** recipe Id `FlowingWater`, goods `Water` and `Badwater` (the conversion factor 0.2),
  the bonus id `MovementSpeed`.
* **Interaction risks:**
  * TimberCommons swaps every vanilla `WaterOutput` for its `AdjustableWaterOutput` via Harmony, with a default level
    of `MaxHeight − 0.1`. Test noria and lift outputs with it installed.
  * Advanced Automation postfixes `Floodgate.Height` and `Automator.SetState`. That is harmless to us.

## Prototype results (in game, 2026-11-14)

Everything below was run in Timberborn 1.1.2.8 by the dev harness, not read from code. Numbers are per game second
unless stated (1 tick = 0.6 s, 768 ticks = 1 day).

**How it was tested.**

* Prototype mod `proto/water/mod` (manifest Id `JigglyPanda.PandabornProtoWater`), generated from vanilla blueprints by
  `proto/water/tools/gen_blueprints.py`, built with `dotnet build src/scripts -c Release` to
  `E:\PandabornDev\build\proto\water` (data plus `Scripts\Pandaborn.Water.dll`). Its buildings join
  `Buildings.Folktails` and its plants `NaturalResources.Folktails` by `CollectionId`, so they exist in Folktails games
  and in Inkpaws games (which list those collections today). Verified: the `parts` scenario ran as **Inkpaws** and
  placed every piece.
* Harness: `src/devharness/WaterLab.cs`, active when `request.json` has a `water` section. It picks a dry, free area,
  flattens it, sculpts pits and terraces, places buildings at exact cells and orientations, adds or drains water at
  cells (optionally a constant-head source that tops a cell up to a depth, or a drain that keeps a level), and records
  probes (depth, height, column floor, contamination, flow vector, soil moisture), time series, plant states, building
  states (power, lift rate, stock, status icons) and screenshots. The game is paused between steps and runs at speed 7
  (about 11.5 ticks per real second) during waits.
* Scenarios: `proto/water/tests/*.json`, generated by `proto/water/tools/gen_tests.py`, read with
  `proto/water/tools/analyze.py <run dir>`. Run:
  `tools\run_game_test.ps1 -RequestJson proto\water\tests\flume.json -ExtraMods E:\PandabornDev\build\proto\water`.
* Map: **Plains** (256 x 256). Diorama (50 x 50) has no dry 30 x 20 area; the first run there was flooded by its river.
  Area origins used are recorded in each `result.json` (`water.origin`), e.g. flume (27,150,5), longrun (6,6,5).

### Flume: works (runs `water-flume-0130`, `water-longrun-0211`, `water-parts-*`)

Three identical 16-tile lines (10 tiles level on the ground, a one-level drop, 6 tiles level below) from ponds whose
surface stays 1.0 above the flume bed, gate set to 0.3:

| Measured | Component route (`FlumeSegment`) | Valve route (1x1 throttling valves) |
|---|---|---|
| Intake flow at steady state | 0.359 m³/s | 0.359 m³/s |
| Water depth along the level run | 0.09–0.16 (mean ≈ 0.12) | identical to 3 decimals |
| Side strip beside the flume | 0.000 (dry) | 0.000 |
| Flume after the source is shut | empty within 150 ticks (90 s) | same |
| Lower run with the terrace flooded 0.6 deep around it | 0.000 (dry) | 0.000 |
| Upstream pond while the outlet basin floods | did not rise | did not rise |

* **One-way and side-sealed, proven.** Flooding the terrace 0.6 deep all around the lower run left the flume cells at
  exactly 0 (screenshot `flume_flooded.png` shows the dry flume floor inside the flood).
* **"Gate 0.3" really passes about 0.36 m³/s.** `SetInflowLimit(0.3)` and the vanilla valve at 0.3 both measured
  0.358–0.359. Treat the number as a setting, not litres.
* **Long level runs are fine.** Level flumes of 10, 20, 40 and 60 tiles from the same 0.358 m³/s intake delivered
  0.351, 0.346, 0.338 and 0.329 m³/s: a loss of about **0.0005 m³/s per tile (≈ 1.4 % of a 0.36 gate per 10 tiles)**,
  which is the evaporation of a 0.12-deep, one-tile-wide film. Depth stays 0.09–0.16 over all 60 tiles. No slope is
  needed; "level or downhill" is honest.
* **Corners (2x2 Flume Corner) work**: water turned twice and came out at 0.12 deep; the post cells stayed dry.
* **Covered segment** carried 0.11–0.12 under a path built on top. **Flume Bridge** (flow cell one block up on a
  trestle) carried 0.10–0.12 over a contaminated puddle 0.11 deep at contamination 0.99, and the water on the bridge
  stayed at contamination 0.000: the two do not mix.
* **Drop (step-down) needs a solid leg.** With the cell under the upper half open (`FlumeDropOpen`), water leaked
  *backwards* out of the lower flume into that pocket during normal running (lower run 0.04–0.06 deep instead of
  0.09–0.13, side strip wet 0.008), and in the flood test the lower flume filled to the flood level through it. The
  sealed `FlumeDrop` (full obstacle in the leg cell) has neither problem. Same rule for any raised piece followed by a
  ground piece.
* **Backed-up water must stay under the piece tops.** A flume only seals up to the top of its pieces. When a Paddy
  Spout at the end closed, the line backed up to the pond level (≈1.0–1.2 above the bed), ran over the one-block-tall
  spout/lid/corner tops and flooded the field and the ground around (run `water-parts-0255`). Fixed in the prototype by
  a solid cap one block above every lidded piece, gate, corner and spout (`PandabornSolidCellsSpec`) and two-block
  corner posts; see the rerun for the result.
* **Route decision: the component route.** Both routes move water identically (same physics: the vanilla valve is
  the same direction limiter plus an inflow limit). The component route wins because it is (1) not tickable (the valve
  ticks every 0.6 s per segment), (2) has no valve panel on every segment, (3) is the only route that can make the
  Drop, Bridge and cap pieces (a valve's limiter is always on its origin cell), and (4) gave the status icons a place to
  live. The valve route stays useful only as the zero-code fallback and for automatable gates.

### Flume failure is visible: works (`FlumeMonitor`, run `water-parts-0200`)

Every flume piece carries a small tickable monitor (checks every 30 ticks, reads only the water snapshot) that raises
the game's own building status icons (`StatusToggle` on the vanilla `StatusSubject`, floating icon over the piece):

| Status (icon) | Condition | Seen in game |
|---|---|---|
| Blocked (`UnreachableObject`) | the cell after the last flow cell is solid (terrain, levee, corner post) | yes, on a flume facing raised ground |
| Misaligned (`GenericError`) | the flume or vanilla valve ahead or behind runs another way (a bend without a Flume Corner) | yes, on the first of two perpendicular pieces |
| No water can enter (`BuildingNeedsWater`) | first piece of a run, dry, and the water behind is not above its bed | yes, on gates whose pond was empty, and on any run start with nothing behind |
| No water reaching the end (`NotEnoughWater`) | last piece of a run dry for 4 checks (≈ 70 s) and the intake is not the reason | yes, on a run end with no supply |
| Closed: contaminated intake (`BuildingBlockedByContamination`) | Flume Gate shut-off is active | yes |

Needs: our component only (no Harmony), loc keys for the texts, vanilla sprite names. Cost: one cheap check per piece
every 30 ticks. Not done: a run-level summary ("this run delivers 0.2 m³/s") would need a run graph; the per-piece
icons are enough to stop silent failure.

### Badwater shut-off on the Flume Gate: works (`FlumeGateGuard`, run `water-parts-0308`)

* The gate reads the contamination of the water right behind it every 5 ticks. Above **0.05** (the same threshold at
  which vanilla starts contaminating beavers who stand in water) it puts a full obstacle in its own cell and shows
  "Closed: the water at the intake is contaminated"; it reopens after 6 checks below 0.025. On by default
  (`GuardEnabled`; the prototype has no panel toggle yet: a one-checkbox entity panel fragment is the remaining work).
* Test: the feeding pond switched to badwater. The gate closed when the water at the intake reached 0.050 (tick 1135);
  the flume behind it emptied; the paddy fed by it stayed at contamination **0.000** for the rest of the run and its
  6 paddy crops stayed healthy and finished growing (growth 1.0). After the pond was emptied and refilled clean, the
  gate reopened by itself and the line refilled (depth 1.15 at the far end 400 ticks later).
* Residual: the water already in the flume when the gate shut carried contamination 0.008 (seepage before closing).
* Control line without a guard: it was backed up (its spout full), so badwater crept along it only by diffusion and had
  not reached its paddy in 500 ticks. In a flowing line it arrives at flow speed: in the earlier run
  (`water-parts-0212`, flowing control line) the bridge water reached contamination 0.93 within 150 ticks and the
  paddy 0.97; every paddy crop there died (contaminated soil) within about half a day.
* **Farmers in a contaminated paddy** (from code, `BeaverContaminationSystem.ContaminationApplier`, not run): a beaver
  standing in water of contamination c ≥ 0.05 starts incubating contamination with probability c × 1 % per tick, e.g.
  c = 0.5 → 0.5 % per tick → on average after about 200 ticks (≈ 0.26 day) of work in the water. So badwater in a paddy
  costs both the crop and the farmers.

### Paddy Spout: works, with one rule (runs `water-parts-0308`, `water-crops-*`)

* Restyled vanilla Fill Valve. Held a 16-tile paddy at **0.32–0.33** (target 0.30, the vanilla 0.02 overflow band and
  a tick of lag) for 2,000 ticks, fed from a flume that was backed up 1.0 deep behind it.
* **The default depth counts from the floor of the field below**, but only if the field exists when the spout is
  built. Our harness carved the field and placed the spout in the same frame, so the spout read the old floor and
  aimed for 1.3; in play the field always exists first. Still: show the depth on the panel, and re-read it when the
  terrain under the output changes.
* Rule (with the solid cap): water behind a spout may stand up to 2 blocks above the spout's base; without the cap the
  limit is 1 block, beyond which it runs over the spout and floods the field and the ground around it.

### Water Trip-Hammer (water as the power line): works (run `water-scoop-0247`)

* One building, one mechanical node that is both generator (`WaterPoweredGeneratorSpec`, 100 nominal) and consumer
  (100), `TransputProviderSpec` with no transputs (joins no shafts), a manufactory with `ProductionIncreaserSpec` and a
  test recipe without ingredients (1 Plank per 2 h). Pure data, no code.
* The node forms its own one-node graph (`graphNodes` 1). Supply = 100 × the current at the wheel cell; production
  speed = supply / demand. Measured in a 1-wide channel: current 0.44 → supply 45 / demand 100 → 45 % speed; 0.36 → 36 %;
  0.51 → 52 %; when the current at its cell fell below 0.15 (0.08) the supply dropped to 0 and it showed the vanilla
  "Building needs power to operate" status. It made 4 planks in about 1,000 ticks of mixed current.
* What the panel shows: the vanilla power numbers of its private graph ("45 / 100 hp", 45 %). Readable, but it should
  be relabelled as "current" rather than power, and the "connect it to a generator" status text is misleading for a
  mill that is its own generator (replace it with our own status, small code).
* Design rule: a trip-hammer runs at (current at its wheel ÷ 1.0) of full speed, nothing below a current of 0.15. A
  1-wide channel with a strong through-flow only reached currents of 0.26–0.51, so the building should be rated so that
  ~0.4 is a good site (e.g. demand 40 instead of 100).

### Dew Collector: works (run `water-dew-0404`)

* Workerless manufactory (`ManufactorySpec` + `ProductionIncreaserSpec`), recipe `PandabornDewWater` (no ingredients,
  1 Water per 4 h, 30 cycles of storage), plus our `DewLimiter : IManufactoryLimiter` (efficiency 1.0 temperate, 0.35
  in drought; badtide counts as temperate air).
* Measured: **6.0 Water in a temperate day, 2.1 Water in a drought day**, linear (0.25 per game hour, then 0.0875).
  Drought was started with the vanilla `WeatherFastForwarder.JumpToNextSeason` (it skipped 15 days instantly).
* Haulers empty it like any workshop output (not tested: the test area had no path to the district, and the building
  correctly showed the vanilla "not connected" status).
* Rule: one collector keeps about 2 pandas in water in good weather (vanilla beavers drink ≈ 2–3 per day; to be
  balanced) and a third of that in drought. The weather scaling costs one ~40-line component.

### Plants: what the game did (run `water-district-0608`, with beavers; settings below)

Test plants (stand-ins on vanilla models): **Shoot Bamboo** = field crop on the carrot model (moist soil,
`DaysToDieDry` 2, growth 2 days); **Timber Bamboo** = tree on the birch model (`DaysToDieDry` 2, growth 3 days,
`ReproductionChance` 0.1, cut for 1 Log); combined **Bamboo** = birch tree that is both cuttable (1 Log) and gatherable
(1 Berries every 2 days), `ReproductionChance` 0.25, `DaysToDieDry` 6. Soil kept moist by a water strip for 2 days,
then dry for 3 days, then wet again.

* **Growth pauses while a plant is dying and resumes where it stopped.** E.g. a bamboo sapling at growth 0.344 stayed
  at 0.344 for the whole dry spell and went on to 0.585 12 h after the soil was wet again.
* **The dying countdown resets fully when water returns** (code: `LivingWaterNaturalResource.StopDying` →
  `Reset`). The 6-day bamboo survived a 3-day dry spell and was healthy 12 h after rewetting; the 2-day crop and tree
  died between 44 h and 68 h after the water was cut (the soil itself stays moist for a while after the water goes).
* **Dead trees and the forester.** Dead Timber Bamboo on planting-marked tiles outside any cutting area was cleared and
  replanted by the forester within 12 h of the soil turning moist again, **but only because "Replant dead trees" was
  switched on** (`Forester.ReplantDeadTrees`; it is off by default and only applies outside cutting areas). The dead
  unmarked (wild) tree stayed dead. With the toggle off a dead tree stands until a lumberjack cuts it (it keeps its log
  yield, so it never becomes overridable). Design: default the Inkpaw forester's toggle to on, or explain it.
* **Dead crops** lose their yield on death and become overridable (code: `EmptyDeadNaturalResourceOverrider`), so a
  farmer can plant over them. Not observed yet: in this run no yield worker did anything ("Nothing to do in range"),
  because the district had no storage for the goods (rerun `district2` with storages).
* **Wild spreading (combined bamboo, chance 0.25, unmarked, inside a cutting area that no lumberjack worked).** Two
  parents became 3 after 12 h, 5 after 48 h, 7 after 60 h, 11 after 168 h (with the 3 dry days in between, during which
  nothing spread: dying parents are reproduction-blocked). Growing saplings do not spread until grown. Spawns only on the
  4 neighbours at the same height, on moist free tiles.
* **Planted (marked) parents never spread** (`reproBlocked` true for every Timber Bamboo on planting-marked tiles,
  confirmed in game); the new trees on the second marked row were planted by the forester, not spawned.
* **Cutting** (code, `Cuttable.Cut`): cutting always kills the plant (`LivingNaturalResource.Die`); `RemoveOnCut:false`
  only leaves the dead stump standing (overridable). There is no "cut and regrow" in vanilla; it would need a small
  component (on `WasCut`: `ReverseDeath`, `Yielder.ResetYield`, own regrow timer). A gatherable on the same plant stops
  yielding once it is cut. This is why splitting shoots (crop) from poles (tree) is right.
* Workers: the treadwheel got its worker and the walker generator gave output multiplier 1.0 (one Folktails worker at
  normal speed), but it lifted nothing: its outlet sat on the ledge floor (no space, see Scoop Wheel). Fixed in
  `district2` (below).

### District, second run (`water-district2-0639`: storages for the goods, fields reachable, outlet fixed)

* **Treadwheel lift works.** One Folktails worker (walker multiplier 1.0) lifted **0.098 m³/s** from a pit (surface
  −0.5) into a ledge basin (floor 0, outlet at +1): the 12-tile basin filled to 0.9 in about 200 ticks, then the wheel
  idled because the outlet had no space. It stops at night when the worker goes home (status "needs power"). Rule: a
  treadwheel lifts ~0.1 m³/s while staffed, i.e. it fills a 12-tile basin in 2 minutes and is idle the rest of the time
  unless the basin drains; worth pairing with a flume gate.
* **Lumberjack vs gatherable on one plant:** with a log store present, the lumberjack cut both combined-bamboo plants
  within the first 4 hours (2 Logs), before their berries had grown; both died and stood as stumps for the rest of the
  run, so the gatherer never had anything to pick. Confirms the split into a shoot crop and a timber tree.
* **Shoot Bamboo as a farm crop works end to end:** farmers harvested the grown crop (Carrot stand-in, 3 per tile),
  replanted all 8 marked tiles, and harvested again 4.5 days later (Carrot stock 20 at h108).
* **Forester replanting confirmed again:** Timber Bamboo that died when its soil dried was replanted by the forester
  (toggle on) within 12 h of rewetting, on all 3 dead marked tiles outside the cutting area; the dead wild tree and its
  dead wild seedling stayed. The wild tree also spread once before dying (chance 0.1).
* Both district runs ran out of food after about 5 days (no food production in the test), which ends worker activity.

### Scoop Wheel (current-driven lift): works with caveats (runs `water-scoop-0247`, `water-combo-0609`)

* Pure data: one mechanical node, generator 100 + consumer 100, no transputs, `WaterPoweredGeneratorSpec` reading the
  current in the wheel cell, vanilla `WaterMoverSpec` 0.1 m³/s, fixed intake in the wheel cell, outlet two rows behind
  over a bank lip. Lift rate = 0.1 × (current × 100 / 100), capped at 0.1.
* Measured in a 1-wide channel with through-flows stepped from 0 to 3.0 m³/s: current at the wheel 0 (still water),
  then 0.25–0.37; **lift 0 in still water, 0.025–0.038 m³/s in a current** (basin gained 3.1, 4.4, 4.3, 4.3 m³ per 150 s
  step); water raised from the channel surface (≈ −0.6) into a basin with floor −1 + outlet at 0, i.e. 1–1.6 levels.
* **Outlet geometry matters.** With the outlet cell on the basin floor the wheel turned but lifted nothing: vanilla
  `WaterOutput` needs space between the water and the outlet cell top, and this machine's TimberCommons replaces every
  water output with one that ignores `DistanceToGroundOffset`. Rule for the model: the outlet hangs one block above the
  basin floor, as on vanilla pumps.
* The power panel shows its private graph ("25 / 100 hp", 25 %); same relabelling need as the trip-hammer.
* **Exploit check: a scoop wheel feeding a flume back into its own channel does not run itself.** After a kick the
  wheel lifted 0.028 m³/s; the moment the external current stopped, the current at the wheel fell to 0.001 (the
  returning 0.028 m³/s is far too little to make a current of 0.15 in the channel) and it stopped; the basin drained back.
  Also in drought: a scoop wheel only turns where something else drives the river.
* Design rules: needs current ≥ 0.15 at the wheel; in a 1-wide channel expect 0.25–0.4, so rate it so that 0.3 is a
  good site (e.g. consumer 30 instead of 100 → full 0.1 m³/s at current 0.3). Lifts 2 levels by model height; a taller
  model lifts more at the same rate.

### Paddy Spout cascade, crop zones, moisture reach, cistern tap (run `water-crops-0648`)

Layout: reservoir → Paddy Spout → paddy 1 (12 x 4, floor −1) → Spout 2 standing *inside* paddy 1 at its lower edge →
paddy 2 (floor −2) → Spout 3 → paddy 3 (floor −3). Test crops: **paddy crop** (wheat model; `FloodableNaturalResourceSpec`
1/1, `DaysToDie` 2, `DaysToDieDry` 1, growth 3 d), **moist crop** (potato model; `WateredNaturalResourceSpec`
`DaysToDieDry` 30, Floodable 0/0, growth 3 d), **dry crop** (sunflower model; `AridNaturalResourceSpec` `DaysToDieWet` 1,
no watered spec, growth 3 d). Each planted in paddy 1, on the ground 1, 3, 5 and 8 tiles beside it, and in a "far" zone.

* **Spouts chain down a staircase: works.** Each spout takes water from the paddy behind it and holds the next one.
  Depths after 3 days: 0.28 / 0.33 / 0.32 (targets 0.30). Rule: a staircase of paddies needs one spout per step, set
  inside the upper paddy at its lower edge; the top one is fed by a flume or pond.
* **Paddy crop:** healthy and fully grown (growth 0.99 in 3 days) in 0.28–0.37 of standing water; on dry or merely
  moist ground it died within about a day (it is "flooded-type": needs 0 < depth ≤ 1 block). When the paddy was drained
  it went dying (0.4–0.5 days left after 2 dry days), and recovered fully when the water came back. Deeper than 1.0 it
  dies too (seen at 1.05–1.09 in `water-parts-0255`).
* **Moist crop:** grew fully on moist ground at 1, 3, 5 and 8 tiles from the paddy; **died in the paddy water** (Floodable
  0/0). In a 2-day drain it stayed healthy where the soil stayed moist and went dying (26.9 days left of 30) at 8 tiles,
  then healthy again on rewetting.
* **Dry crop:** died within a day everywhere in this run, because every test spot was moist (the "far" zone sat 2 tiles
  from a test water strip, a layout mistake). So "dies when irrigated" is proven; "thrives on dry ground" is not yet shown
  in game (vanilla Succulent is the same mechanism and works).
* **Moisture reach (the most important number for the design):** soil moisture falls by 1 per tile from the water's
  edge, starting from a level that depends on the water body's size:

  | Water body | Level at the edge | Moist out to |
  |---|---|---|
  | 1-wide flume or strip (kept 0.12–0.15 deep) | 6 | **6 tiles each side** (a 13-tile band) |
  | Spout-held paddy, 12 x 4, 0.3 deep | 16 | **16 tiles** from its edge |

  Moisture decays about 5–6 levels per day after the water goes: two days after draining the paddy, only 5 tiles beside
  it were still moist. The study's "a flume moistens about 1–2 tiles" was wrong: a flume moistens 6 tiles each side,
  and a paddy turns a whole hillside moist. Dry-ground crops need distance (≥ 7 tiles from a flume, ≥ 17 from a paddy) or
  an Irrigation Barrier.
* **What a moist strip costs:** a 10-tile, 1-wide strip kept 0.15 deep took 2.09 m³ per day (0.21 m³ per tile per day,
  ≈ 1 Water good per tile per day at the vanilla 0.2 m³ per good) and kept a 13 x 10 area moist. Large pools lose much
  less per tile: the three paddies (132 tiles at 0.3 deep) took 6.2 m³ per day together (0.047 m³ per tile per day).
* **Cistern Tap:** data only as a restyled Water Dump (`Discharge`) with only the `FlowingWater` recipe: 3 Water goods
  per hour of work → 0.6 m³ of clean water. It **must keep its worker**: a workerless test variant crashed the game
  (vanilla `WaterOutputManufactoryLimiter` reads the `Workshop` component without a null check). So one worker running
  a tap 4 hours a day (12 Water goods) keeps a 10-tile strip, i.e. about 130 tiles of moist farmland, alive through a
  drought. A workerless tap would need our own small water-producer component. The worked tap was not run in game.

### Verdicts after the prototype

| Tool | Verdict | Key numbers |
|---|---|---|
| Flume (component route) | **Works** | 0.36 m³/s at gate "0.3"; −0.0005 m³/s per level tile; 60 level tiles deliver 92 %; sides and back watertight |
| Flume Corner (2x2) | **Works** | turns twice, posts dry |
| Flume Drop | **Works only with a solid leg** | open leg leaks backwards and floods in |
| Flume Bridge | **Works** | carries 0.1–0.12 deep over a contaminated puddle with zero mixing |
| Covered Flume | **Works** (with cap) | carries water under a path |
| Flume Gate + badwater shut-off | **Works** | closes at contamination 0.05, reopens when clean; paddy stayed at 0.000 |
| Flume status icons | **Works** | blocked / misaligned / intake dry / end dry / closed by badwater |
| Paddy Spout | **Works** (with cap) | holds 0.30–0.33; cascades down a staircase |
| Scoop Wheel | **Works with caveats** | 0 in still water; 0.025–0.038 m³/s in currents of 0.25–0.37; outlet must hang above the basin |
| Treadwheel lift | **Works** | one Folktails worker: 0.098 m³/s up ~1.5 levels; stops when the basin is full and when the worker goes home |
| Water Trip-Hammer | **Works** | speed = current at its wheel (36–52 % in a 1-wide channel) |
| Dew Collector | **Works** | 6.0 Water per temperate day, 2.1 per drought day |
| Cistern Tap | **Data only, with a worker**; workerless crashes | 3 Water/h → 0.6 m³/h |
| Paddy / moist / dry crops | **Works**; dry-ground thriving not yet shown | see crop section |
| Wild spreading, dead-tree replanting | **Works as vanilla** | 2 → 11 bamboo in 7 days at chance 0.25; replant needs the forester toggle |

### Player-facing rules that follow (for the design)

* **Flume.** Water runs one way along the arrows; it never leaks from the sides and never runs back, even through a
  flooded field. It can run level for 60+ tiles (it loses about 1.5 % of its flow per 10 tiles to evaporation) or step
  down any number of levels with Flume Drops; it never climbs. A gate passes up to its setting (about 0.36 m³/s at the
  prototype's "0.3"). Turn with a Flume Corner. A flume on the ground keeps the soil moist **6 tiles to each side**.
* **Heads.** The water feeding a flume may stand at most 2 blocks above the flume bed (1 without the caps), or it runs
  over gates, corners and spouts when the line backs up.
* **Paddies.** One Paddy Spout holds a whole level paddy at its depth (default 0.3) — there is no "spout every N
  tiles" limit on level ground; terraces need one spout per step, set at the lower edge of the paddy above. A paddy
  deeper than 1 block kills rice. A paddy keeps the ground moist 16 tiles around it, so tea and pepper fields must sit
  at least 17 tiles away or behind an irrigation barrier.
* **Drought.** Moist soil stays moist for about 1–2 days after its water goes (longer near big pools), then crops go
  brown; anything with a dying timer longer than the drought recovers fully when the water returns. A 10-tile strip
  needs about 2 m³ (10 Water goods) a day to stay wet.
* **Badwater.** Flume Gates close by themselves at 5 % contamination at the intake and show it; they reopen when the
  intake is clean.
* **Scoop Wheel / Trip-Hammer.** They work only where the current at the wheel is at least 0.15 and work harder in
  faster water; they cannot run on water they lift themselves.
* **Dew Collector.** About 6 Water a day in good weather, 2 in drought, no workers.

### Recommended changes to this study and the design

* Replace the study's moisture estimate (1–2 tiles beside a flume) with the measured 6 tiles per side and 16 tiles
  around a 50-tile paddy. Pillar 3's "dry, near irrigation but not on it" needs explicit dry pockets (irrigation
  barriers) or longer distances than the design assumes.
* Build the flume as our component, not as restyled valves (identical physics, no ticking, no panel per tile, and only
  the component can make Drops, Bridges and caps). Keep restyled valves only for an automatable gate.
* Every lidded piece, gate, corner and spout gets a solid cap one block above its lid (now in the prototype); every
  raised piece followed by a ground piece needs a solid leg (Flume Drop).
* The Scoop Wheel and Trip-Hammer should be rated for ~0.3 current (consumer 30), have their power numbers relabelled
  as current, and get our own "needs a current" status instead of vanilla's "connect it to a generator". Their outlets
  hang one block above the basin floor (also required for compatibility with TimberCommons).
* Default the Inkpaw forester's "replant dead trees" to on (vanilla default is off), or teach it.
* A Paddy Spout's depth is measured from the field below at the moment it is built; show it on the panel.
* Flume Gate shut-off: add the panel toggle (one checkbox); threshold 0.05 matches vanilla's own beaver-contamination
  threshold.
* Test plants must use models whose materials are in the faction's material collections (an Iron Teeth model in a
  Folktails game threw "Material Kohlrabi not found").

### Not proven yet

* Treadwheel with a Ringtail (or any faster/slower) worker: no Ringtail exists yet; the lift scales with the worker's
  `MovementSpeed` bonus multiplier (code).
* Farmers clearing and replanting *dead* crops (in `district2` the shoot field never dried out: a full 12-tile basin
  9 tiles away kept it moist). The code says dead crops become overridable and are replanted over.
* A dry-ground crop thriving on truly dry soil next to a wet zone.
* Cistern Tap run in game with a worker and hauled Water goods.
* Raised/trestle step-down from a Bridge straight onto ground (only Drop from ground level tested), splitters, and a
  flume crossing *under* a Bridge.
* Save and reload of flume limiters and gate state (the components re-apply on load by design; not run).
* Behaviour with TimberCommons disabled (all runs had the owner's mods enabled, TimberCommons included).
