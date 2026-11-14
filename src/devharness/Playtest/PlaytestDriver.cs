using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using Bindito.Core;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Timberborn.BehaviorSystem;
using Timberborn.BlockObjectTools;
using Timberborn.BlockSystem;
using Timberborn.BuilderPrioritySystem;
using Timberborn.Buildings;
using Timberborn.CameraSystem;
using Timberborn.Characters;
using Timberborn.ConstructionSites;
using Timberborn.EntitySystem;
using Timberborn.Forestry;
using Timberborn.GameCycleSystem;
using Timberborn.GameDistricts;
using Timberborn.Goods;
using Timberborn.GoodsSampling;
using Timberborn.HazardousWeatherSystem;
using Timberborn.InventorySystem;
using Timberborn.Planting;
using Timberborn.PrioritySystem;
using Timberborn.ResourceCountingSystem;
using Timberborn.ScienceSystem;
using Timberborn.SingletonSystem;
using Timberborn.SoilMoistureSystem;
using Timberborn.Stockpiles;
using Timberborn.TemplateSystem;
using Timberborn.TerrainSystem;
using Timberborn.TimeSystem;
using Timberborn.WaterSystem;
using Timberborn.WeatherSystem;
using Timberborn.Wellbeing;
using Timberborn.WorkSystem;
using Timberborn.Workshops;
using UnityEngine;

namespace PandabornDevHarness
{
    [Context("Game")]
    public class PlaytestConfigurator : Configurator
    {
        protected override void Configure()
        {
            if (!Harness.Active || !(Harness.Request?.Raw?["playtest"] is JObject)) return;
            Bind<PlaytestDriver>().AsSingleton();
        }
    }

    /// <summary>
    /// Scripted colony: plays a faction from a build order the way a player would, and writes daily telemetry.
    /// Active only when request.json has a "playtest" object. Format (every key optional unless marked):
    /// <code>
    /// "playtest": {
    ///   "name": "folktails-baseline",
    ///   "names": { "farm": "EfficientFarmHouse.Folktails", ... },  // "@farm" anywhere a template/good/recipe/plant is expected
    ///   "speed": 7,                                     // game speed once the run starts (else request "speed")
    ///   "shotsEveryDays": 3, "shotSize": [1280, 720],   // overview at dawn (hour 1) and night (hour 21) every N days; 0 = none
    ///   "sampleEveryHours": 0.5,                        // workplace/builder activity sampling period (in-game hours)
    ///   "steps": [ {
    ///       "id": "pump1", "op": "build" | "plant" | "cut" | "recipe" | "workers" | "priority" | "good" | "hours"
    ///                            | "science" | "give" | "speed" | "unmarkPlant" | "note",
    ///       "when": { "day": 2, "hour": 6, "after": ["id"], "finished": ["id"], "stock": { "Log": 40 }, "stockBelow": {},
    ///                 "population": 15, "adults": 10, "science": 100, "freeBedsBelow": 2, "homelessAtLeast": 1,
    ///                 "unemployedAtLeast": 1, "weather": "drought|temperate|badtide|hazard", "hazardWithinDays": 3,
    ///                 "cycle": 2, "notDone": ["id"] },
    ///       "repeat": 4, "everyHours": 12,              // run up to 4 times, at least 12 in-game hours apart
    ///       // build:
    ///       "template": "@farm", "near": "dc" | "&lt;step id&gt;", "rule": "any|nearWater|moist|dry|trees|bushes",
    ///       "offset": [dx, dy], "orientation": "Cw90", "minDistance": 3, "maxDistance": 30, "radius": 6, "min": 12,
    ///       "minDepth": 0.4, "unlock": "science|grant", "priority": "VeryHigh" (builder priority of the site, then the
    ///       workplace's), "workers": 2, "recipe": "@bread", "good": "Log" (stockpile good),
    ///       // plant: "target": "&lt;planter step id&gt;", "plant": "@carrot", "count": 30, "radius": 9, "soil": "moist|dry|any"
    ///       // cut:   "target": "&lt;lumberjack step id&gt;", "count": 40, "radius": 12, "trees": ["Pine", ...] | "field": "&lt;plant step id&gt;"
    ///       // recipe/workers/priority/good: "target": "&lt;build step id&gt;" (every instance), "recipe"/"count"/"priority"/"good"
    ///       // hours: "hours": 16;  science: "add": 100;  give: "target", "good", "amount";  speed: "speed": 7
    ///   } ]
    /// }
    /// </code>
    /// Buildings are placed as construction sites (the colony's builders build them with real costs; paths, which the game
    /// places finished, are laid finished from the building's entrance to the existing path network). Science is spent as
    /// the unlock button does (or granted with "unlock": "grant"). Output: &lt;run&gt;\playtest\ (daily.jsonl, events.jsonl,
    /// state.json, shots) and result.json "playtest".
    /// </summary>
    public partial class PlaytestDriver : ILoadableSingleton, IUpdatableSingleton
    {
        private readonly EventBus _eventBus;
        private readonly SpeedManager _speedManager;
        private readonly IDayNightCycle _dayNightCycle;
        private readonly TemplateService _templateService;
        private readonly DistrictCenterRegistry _districtCenterRegistry;
        private readonly ITerrainService _terrainService;
        private readonly PreviewPlacerFactory _previewPlacerFactory;
        private readonly BlockObjectPlacerService _blockObjectPlacerService;
        private readonly ConstructionFactory _constructionFactory;
        private readonly IBlockService _blockService;
        private readonly IThreadSafeWaterMap _waterMap;
        private readonly ISoilMoistureService _soilMoistureService;
        private readonly PlantingService _plantingService;
        private readonly PlantingAreaValidator _plantingAreaValidator;
        private readonly TreeCuttingArea _treeCuttingArea;
        private readonly RecipeSpecService _recipeSpecService;
        private readonly ScienceService _scienceService;
        private readonly BuildingUnlockingService _buildingUnlockingService;
        private readonly WorkingHoursManager _workingHoursManager;
        private readonly EntityRegistry _entityRegistry;
        private readonly EntityService _entityService;
        private readonly CharacterPopulation _characterPopulation;
        private readonly ResourceCountingService _resourceCountingService;
        private readonly GlobalGoodSamplingRegistry _globalGoodSamplingRegistry;
        private readonly IGoodService _goodService;
        private readonly WeatherService _weatherService;
        private readonly HazardousWeatherService _hazardousWeatherService;
        private readonly GameCycleService _gameCycleService;
        private readonly WellbeingService _wellbeingService;
        private readonly CameraService _cameraService;

        private JObject _spec;
        private string _dir;
        private bool _started, _ended;
        private float _startHours, _startReal, _nextEval, _nextPathTry;
        private readonly List<Step> _steps = new List<Step>();
        private readonly Dictionary<string, Placed> _placed = new Dictionary<string, Placed>();   // instance id -> placed building
        private readonly JObject _names = new JObject();
        private readonly JObject _state = new JObject();

        private class Step
        {
            public string Id, Op;
            public JObject Raw, When;
            public int Max = 1, Done, Attempts;
            public float EveryHours, LastAt = -1e9f, NextTry;
            public bool Failed;
            public string Waiting, Error;
            public readonly List<string> Instances = new List<string>();
            public readonly List<Vector3Int> Cells = new List<Vector3Int>();   // plant / cut steps: the cells marked
        }

        private class Placed
        {
            public string Id, StepId, Template;
            public BlockObject Bo;
            public float PlacedAt, FinishedAt = -1f;
            public bool Configured;
        }

        public PlaytestDriver(EventBus eventBus, SpeedManager speedManager, IDayNightCycle dayNightCycle, TemplateService templateService,
                              DistrictCenterRegistry districtCenterRegistry, ITerrainService terrainService,
                              PreviewPlacerFactory previewPlacerFactory, BlockObjectPlacerService blockObjectPlacerService,
                              ConstructionFactory constructionFactory, IBlockService blockService, IThreadSafeWaterMap waterMap,
                              ISoilMoistureService soilMoistureService, PlantingService plantingService,
                              PlantingAreaValidator plantingAreaValidator, TreeCuttingArea treeCuttingArea, RecipeSpecService recipeSpecService,
                              ScienceService scienceService, BuildingUnlockingService buildingUnlockingService,
                              WorkingHoursManager workingHoursManager, EntityRegistry entityRegistry, EntityService entityService,
                              CharacterPopulation characterPopulation, ResourceCountingService resourceCountingService,
                              GlobalGoodSamplingRegistry globalGoodSamplingRegistry, IGoodService goodService, WeatherService weatherService,
                              HazardousWeatherService hazardousWeatherService, GameCycleService gameCycleService,
                              WellbeingService wellbeingService, CameraService cameraService)
        {
            _eventBus = eventBus;
            _speedManager = speedManager;
            _dayNightCycle = dayNightCycle;
            _templateService = templateService;
            _districtCenterRegistry = districtCenterRegistry;
            _terrainService = terrainService;
            _previewPlacerFactory = previewPlacerFactory;
            _blockObjectPlacerService = blockObjectPlacerService;
            _constructionFactory = constructionFactory;
            _blockService = blockService;
            _waterMap = waterMap;
            _soilMoistureService = soilMoistureService;
            _plantingService = plantingService;
            _plantingAreaValidator = plantingAreaValidator;
            _treeCuttingArea = treeCuttingArea;
            _recipeSpecService = recipeSpecService;
            _scienceService = scienceService;
            _buildingUnlockingService = buildingUnlockingService;
            _workingHoursManager = workingHoursManager;
            _entityRegistry = entityRegistry;
            _entityService = entityService;
            _characterPopulation = characterPopulation;
            _resourceCountingService = resourceCountingService;
            _globalGoodSamplingRegistry = globalGoodSamplingRegistry;
            _goodService = goodService;
            _weatherService = weatherService;
            _hazardousWeatherService = hazardousWeatherService;
            _gameCycleService = gameCycleService;
            _wellbeingService = wellbeingService;
            _cameraService = cameraService;
        }

        public void Load()
        {
            _spec = (JObject)Harness.Request.Raw["playtest"];
            _dir = Path.Combine(Harness.OutputDir, "playtest");
            Directory.CreateDirectory(_dir);
            if (_spec["names"] is JObject names) foreach (var p in names.Properties()) _names[p.Name] = p.Value;
            int auto = 0;
            if (_spec["steps"] is JArray steps)
                foreach (var token in steps)
                {
                    if (!(token is JObject o)) continue;
                    var step = new Step
                    {
                        Raw = o,
                        Op = Request.Str(o, "op", "build"),
                        When = o["when"] as JObject ?? new JObject(),
                        Max = Math.Max(1, (int)Request.Num(o, "repeat", 1f)),
                        EveryHours = Request.Num(o, "everyHours", 0f)
                    };
                    step.Id = Request.Str(o, "id", step.Op + "_" + (++auto).ToString(CultureInfo.InvariantCulture));
                    if (_steps.Any(s => s.Id == step.Id)) step.Id += "_" + (++auto).ToString(CultureInfo.InvariantCulture);
                    _steps.Add(step);
                }
            _state["name"] = Request.Str(_spec, "name", "playtest");
            _state["steps"] = _steps.Count;
            Harness.Result["playtest"] = _state;
            _eventBus.Register(this);
            LoadTelemetry();
            Harness.Info("playtest: " + _steps.Count + " step(s) loaded (" + _state["name"] + ")");
        }

        public void UpdateSingleton()
        {
            if (_ended) return;
            if (Harness.Finished) { End("harness finished"); return; }
            if (!_started)
            {
                // the game driver starts the run (and the clock) after its settle phase and start shots
                if (Harness.Result["run"] == null) return;
                Begin();
            }
            try
            {
                float now = Hours();
                UpdateTelemetry(now);
                ConfigureFinished(now);
                if (now >= _nextPathTry) { _nextPathTry = now + 1f; LayPendingPaths(); }
                if (now >= _nextEval)
                {
                    _nextEval = now + 0.25f;
                    EvaluateSteps(now);
                }
            }
            catch (Exception e)
            {
                Harness.Error("playtest: update failed", e);
                _nextEval = Hours() + 1f;
            }
        }

        private void Begin()
        {
            _started = true;
            _startHours = Hours();
            _startReal = Time.unscaledTime;
            float speed = Request.Num(_spec, "speed", -1f);
            if (speed >= 0f) _speedManager.ChangeSpeed(speed);
            // the district center is the instance "dc", so steps can set its builders ("workers", target "dc")
            var center = _districtCenterRegistry.AllDistrictCenters.FirstOrDefault();
            var centerBlock = center ? center.GetComponent<BlockObject>() : null;
            if (centerBlock)
                _placed["dc"] = new Placed
                {
                    Id = "dc", StepId = "dc", Template = centerBlock.GetComponent<TemplateSpec>()?.TemplateName, Bo = centerBlock,
                    PlacedAt = Hours(), FinishedAt = Hours(), Configured = true
                };
            _state["startDay"] = Math.Round(_dayNightCycle.PartialDayNumber, 3);
            _state["startSpeed"] = speed >= 0f ? speed : Harness.Request.Speed;
            Event("start", null, new JObject { ["speed"] = _state["startSpeed"], ["workingHours"] = WorkingHours() });
            try { DumpMap((int)Request.Num(_spec, "mapDumpRadius", 45f)); }
            catch (Exception e) { Harness.Warn("playtest: map dump failed: " + e.Message); }
            BeginTelemetry();
        }

        private void End(string why)
        {
            if (_ended) return;
            _ended = true;
            try
            {
                EndTelemetry();
                WriteState();
                Event("end", null, new JObject { ["why"] = why });
            }
            catch (Exception e) { Harness.Error("playtest: ending failed", e); }
        }

        private float Hours() => _dayNightCycle.PartialDayNumber * 24f;
        /// <summary>The hour the game driver started its run clock (result "run.startDay").</summary>
        private float _gameDriverStartHours()
        {
            var run = Harness.Result["run"] as JObject;
            return run != null && run["startDay"] != null ? (float)run["startDay"] * 24f : _startHours;
        }
        private float Day() => _dayNightCycle.PartialDayNumber;
        private float WorkingHours() => (float)Math.Round(_workingHoursManager.WorkedPartOfDay * 24f, 2);

        // ------------------------------------------------------------------ steps

        private void EvaluateSteps(float now)
        {
            foreach (var step in _steps)
            {
                if (step.Failed || step.Done >= step.Max) continue;
                if (now < step.NextTry) continue;
                if (step.Done > 0 && now - step.LastAt < step.EveryHours) continue;
                if (!Ready(step.When, out string waiting))
                {
                    step.Waiting = waiting;
                    continue;
                }
                step.Waiting = null;
                bool ok;
                try { ok = Execute(step, now); }
                catch (Exception e)
                {
                    Harness.Error("playtest: step " + step.Id + " threw", e);
                    step.Error = e.GetType().Name + ": " + e.Message;
                    ok = false;
                    step.Attempts = 99;
                }
                if (ok)
                {
                    step.Done++;
                    step.LastAt = now;
                    step.Attempts = 0;
                    step.Error = null;
                }
                else if (step.Waiting == null)
                {
                    step.Attempts++;
                    int maxAttempts = (int)Request.Num(step.Raw, "attempts", 8f);
                    if (step.Attempts >= maxAttempts)
                    {
                        step.Failed = true;
                        Event("stepFailed", step.Id, new JObject { ["error"] = step.Error, ["attempts"] = step.Attempts });
                        Harness.Warn("playtest: step " + step.Id + " gave up: " + step.Error);
                    }
                    else step.NextTry = now + Request.Num(step.Raw, "retryHours", 3f);
                }
            }
        }

        /// <summary>Runs one step. False with step.Waiting set = not yet (no attempt counted); false otherwise = a failed attempt.</summary>
        private bool Execute(Step step, float now)
        {
            var o = step.Raw;
            switch (step.Op)
            {
                case "build": return Build(step, now);
                case "plant": return Plant(step);
                case "cut": return Cut(step);
                case "unmarkPlant":
                {
                    var source = _steps.FirstOrDefault(s => s.Id == Request.Str(o, "field", null));
                    if (source == null) { step.Error = "no field " + Request.Str(o, "field", null); return false; }
                    foreach (var c in source.Cells) _plantingService.UnsetPlantingCoordinates(c);
                    Event("unmarkPlant", step.Id, new JObject { ["field"] = source.Id, ["cells"] = source.Cells.Count });
                    return true;
                }
                case "recipe":
                case "workers":
                case "priority":
                case "good":
                {
                    var targets = Instances(Request.Str(o, "target", null)).ToList();
                    if (targets.Count == 0) { step.Waiting = "target " + Request.Str(o, "target", null) + " not placed"; return false; }
                    if (targets.Any(p => !p.Bo || !p.Bo.IsFinished)) { step.Waiting = "target not finished"; return false; }
                    foreach (var p in targets) Apply(p, o, step.Op);
                    Event(step.Op, step.Id, new JObject { ["target"] = Request.Str(o, "target", null), ["instances"] = targets.Count });
                    return true;
                }
                case "hours":
                {
                    float hours = Request.Num(o, "hours", 16f);
                    _workingHoursManager.WorkedPartOfDay = Mathf.Clamp(hours, 0f, 24f) / 24f;
                    Event("hours", step.Id, new JObject { ["hours"] = hours });
                    return true;
                }
                case "science":
                {
                    int add = (int)Request.Num(o, "add", 0f);
                    _scienceService.AddPoints(add);
                    Event("science", step.Id, new JObject { ["add"] = add, ["total"] = _scienceService.SciencePoints });
                    return true;
                }
                case "give":
                {
                    var target = Instances(Request.Str(o, "target", null)).FirstOrDefault(p => p.Bo && p.Bo.IsFinished);
                    if (target == null) { step.Waiting = "target not finished"; return false; }
                    string good = Resolve(Request.Str(o, "good", null));
                    int amount = (int)Request.Num(o, "amount", 1f);
                    var inventory = target.Bo.GetComponent<Stockpile>()?.Inventory ?? target.Bo.GetComponent<Manufactory>()?.Inventory;
                    if (inventory == null) { step.Error = "target has no inventory"; return false; }
                    inventory.GiveExistingIgnoringCapacity(new GoodAmount(good, amount));
                    Event("give", step.Id, new JObject { ["target"] = target.Id, ["good"] = good, ["amount"] = amount });
                    return true;
                }
                case "speed":
                {
                    float speed = Request.Num(o, "speed", 3f);
                    _speedManager.ChangeSpeed(speed);
                    Event("speed", step.Id, new JObject { ["speed"] = speed });
                    return true;
                }
                case "note":
                    Event("note", step.Id, new JObject { ["text"] = Request.Str(o, "text", "") });
                    return true;
                default:
                    step.Error = "unknown op " + step.Op;
                    step.Failed = true;
                    return false;
            }
        }

        private IEnumerable<Placed> Instances(string stepOrInstanceId)
        {
            if (stepOrInstanceId == null) yield break;
            if (_placed.TryGetValue(stepOrInstanceId, out var single)) { yield return single; yield break; }
            foreach (var p in _placed.Values) if (p.StepId == stepOrInstanceId && p.Bo) yield return p;
        }

        /// <summary>Applies a build step's settings (workers, recipe, priority, stockpile good) once the building is finished.</summary>
        private void ConfigureFinished(float now)
        {
            foreach (var p in _placed.Values)
            {
                if (p.Configured || !p.Bo) continue;
                if (!p.Bo.IsFinished) continue;
                p.Configured = true;
                p.FinishedAt = now;
                var step = _steps.FirstOrDefault(s => s.Id == p.StepId);
                var settings = new JObject();
                if (step != null)
                    foreach (var key in new[] { "workers", "recipe", "priority", "good" })
                        if (step.Raw[key] != null) settings[key] = step.Raw[key];
                foreach (var prop in settings.Properties()) Apply(p, settings, prop.Name);
                Event("finished", p.Id, new JObject
                {
                    ["template"] = p.Template, ["hoursToBuild"] = Math.Round(now - p.PlacedAt, 1)
                });
            }
        }

        private void Apply(Placed p, JObject o, string what)
        {
            var bo = p.Bo;
            switch (what)
            {
                case "workers":
                {
                    var workplace = bo.GetComponent<Workplace>();
                    if (workplace == null) { Harness.Warn("playtest: " + p.Id + " has no workplace"); return; }
                    int wanted = Mathf.Clamp((int)Request.Num(o, o["count"] != null ? "count" : "workers", workplace.DesiredWorkers), 0, workplace.MaxWorkers);
                    int guard = 0;
                    while (workplace.DesiredWorkers < wanted && guard++ < 20) workplace.IncreaseDesiredWorkers();
                    while (workplace.DesiredWorkers > wanted && guard++ < 40) workplace.DecreaseDesiredWorkers();
                    return;
                }
                case "recipe":
                {
                    var manufactory = bo.GetComponent<Manufactory>();
                    string id = Resolve(Request.Str(o, "recipe", null));
                    var recipe = manufactory?.ProductionRecipes.FirstOrDefault(r => r.Id == id);
                    if (recipe == null)
                    {
                        Harness.Warn("playtest: " + p.Id + " cannot make recipe " + id + " (has: "
                                     + (manufactory == null ? "no manufactory" : string.Join(",", manufactory.ProductionRecipes.Select(r => r.Id))) + ")");
                        Event("recipeMissing", p.Id, new JObject { ["recipe"] = id });
                        return;
                    }
                    manufactory.SetRecipe(recipe);
                    return;
                }
                case "priority":
                {
                    if (!Enum.TryParse(Request.Str(o, "priority", "Normal"), true, out Priority priority)) return;
                    bo.GetComponent<WorkplacePriority>()?.SetPriority(priority);
                    if (!bo.IsFinished) bo.GetComponent<BuilderPrioritizable>()?.SetPriority(priority);
                    return;
                }
                case "good":
                {
                    string good = Resolve(Request.Str(o, "good", null));
                    var allower = bo.GetComponent<SingleGoodAllower>();
                    if (allower == null) { Harness.Warn("playtest: " + p.Id + " has no single-good allower"); return; }
                    allower.Allow(good);
                    return;
                }
            }
        }

        // ------------------------------------------------------------------ conditions

        private bool Ready(JObject when, out string waiting)
        {
            waiting = null;
            foreach (var prop in when.Properties())
            {
                var v = prop.Value;
                switch (prop.Name)
                {
                    case "day":
                        if (Day() < (float)v) { waiting = "day " + v; return false; }
                        break;
                    case "dayBelow":
                        if (Day() >= (float)v) { waiting = "past day " + v; return false; }
                        break;
                    case "hour":
                        if (_dayNightCycle.HoursPassedToday < (float)v) { waiting = "hour " + v; return false; }
                        break;
                    case "after":
                        foreach (var id in Ids(v))
                            if (!_steps.Any(s => s.Id == id && s.Done > 0)) { waiting = "after " + id; return false; }
                        break;
                    case "notDone":
                        foreach (var id in Ids(v))
                            if (_steps.Any(s => s.Id == id && s.Done > 0)) { waiting = "already done " + id; return false; }
                        break;
                    case "finished":
                        foreach (var id in Ids(v))
                        {
                            var list = Instances(id).ToList();
                            if (list.Count == 0 || list.Any(p => !p.Bo.IsFinished)) { waiting = "finished " + id; return false; }
                        }
                        break;
                    case "stock":
                        foreach (var g in ((JObject)v).Properties())
                            if (Stock(Resolve(g.Name)) < (int)g.Value) { waiting = "stock " + g.Name + " " + g.Value; return false; }
                        break;
                    case "stockBelow":
                        foreach (var g in ((JObject)v).Properties())
                            if (Stock(Resolve(g.Name)) >= (int)g.Value) { waiting = "stock below " + g.Name + " " + g.Value; return false; }
                        break;
                    case "population":
                        if (CountCharacters(false) < (int)v) { waiting = "population " + v; return false; }
                        break;
                    case "adults":
                        if (CountCharacters(true) < (int)v) { waiting = "adults " + v; return false; }
                        break;
                    case "science":
                        if (_scienceService.SciencePoints < (int)v) { waiting = "science " + v; return false; }
                        break;
                    case "freeBedsBelow":
                        if (Housing().free >= (int)v) { waiting = "free beds below " + v; return false; }
                        break;
                    case "homelessAtLeast":
                        if (Housing().homeless < (int)v) { waiting = "homeless " + v; return false; }
                        break;
                    case "unemployedAtLeast":
                        if (Employment().unemployed < (int)v) { waiting = "unemployed " + v; return false; }
                        break;
                    case "weather":
                        if (WeatherName() != (string)v && !((string)v == "hazard" && _weatherService.IsHazardousWeather)) { waiting = "weather " + v; return false; }
                        break;
                    case "hazardWithinDays":
                        if (_weatherService.IsHazardousWeather || _weatherService.HazardousWeatherStartCycleDay - _gameCycleService.PartialCycleDay > (float)v)
                        { waiting = "hazard within " + v + " days"; return false; }
                        break;
                    case "pathsClear":
                        // pending tiles whose tree can no longer be cut (it died empty, or a sapling took its place) do not count
                        if (_pendingPath.Any(c => TreeAt(c).HasValue)) { waiting = "path tiles waiting for trees: " + _pendingPath.Count; return false; }
                        break;
                    case "cycle":
                        if (_gameCycleService.Cycle < (int)v) { waiting = "cycle " + v; return false; }
                        break;
                    default:
                        Harness.Warn("playtest: unknown condition " + prop.Name);
                        break;
                }
            }
            return true;
        }

        private static IEnumerable<string> Ids(JToken v)
        {
            if (v is JArray a) foreach (var t in a) yield return (string)t;
            else if (v != null) yield return (string)v;
        }

        private string Resolve(string name)
        {
            if (name == null || !name.StartsWith("@", StringComparison.Ordinal)) return name;
            var key = name.Substring(1);
            var mapped = _names[key];
            if (mapped == null) { Harness.Warn("playtest: no name for " + name); return key; }
            return (string)mapped;
        }

        private int Stock(string good)
        {
            try { return _resourceCountingService.GetGlobalResourceCount(good).AvailableStock; }
            catch (Exception) { return 0; }
        }

        private int CountCharacters(bool adultsOnly)
        {
            int n = 0;
            foreach (var c in _characterPopulation.Characters)
            {
                if (!c || c.GetComponent<Timberborn.Bots.Bot>() != null) continue;
                if (adultsOnly && c.GetComponent<Timberborn.Beavers.Child>() != null) continue;
                n++;
            }
            return n;
        }

        private string WeatherName()
        {
            if (!_weatherService.IsHazardousWeather) return "temperate";
            var hazard = _hazardousWeatherService.CurrentCycleHazardousWeather;
            if (hazard is DroughtWeather) return "drought";
            if (hazard is BadtideWeather) return "badtide";
            return hazard?.GetType().Name ?? "hazard";
        }

        // ------------------------------------------------------------------ output

        private void Event(string type, string id, JObject data)
        {
            var o = new JObject { ["day"] = Math.Round(Day(), 3), ["type"] = type };
            if (id != null) o["id"] = id;
            if (data != null) foreach (var p in data.Properties()) o[p.Name] = p.Value;
            AppendLine("events.jsonl", o);
            if (type != "finished" && type != "start") Harness.Info("playtest: " + o.ToString(Formatting.None));
        }

        private void AppendLine(string file, JObject o)
        {
            try { File.AppendAllText(Path.Combine(_dir, file), o.ToString(Formatting.None) + "\n"); }
            catch (Exception e) { Harness.Warn("playtest: writing " + file + " failed: " + e.Message); }
        }

        private void WriteState()
        {
            var steps = new JArray();
            foreach (var s in _steps)
                steps.Add(new JObject
                {
                    ["id"] = s.Id, ["op"] = s.Op, ["done"] = s.Done, ["max"] = s.Max, ["failed"] = s.Failed,
                    ["waiting"] = s.Waiting, ["error"] = s.Error, ["attempts"] = s.Attempts,
                    ["instances"] = new JArray(s.Instances.Cast<object>().ToArray()), ["cells"] = s.Cells.Count
                });
            var placed = new JArray();
            foreach (var p in _placed.Values)
                placed.Add(new JObject
                {
                    ["id"] = p.Id, ["template"] = p.Template, ["placedDay"] = Math.Round(p.PlacedAt / 24f, 2),
                    ["finishedDay"] = p.FinishedAt >= 0 ? Math.Round(p.FinishedAt / 24f, 2) : (JToken)null,
                    ["exists"] = (bool)p.Bo,
                    ["coordinates"] = p.Bo ? new JArray(p.Bo.Coordinates.x, p.Bo.Coordinates.y, p.Bo.Coordinates.z) : null
                });
            _state["day"] = Math.Round(Day(), 3);
            _state["stepStates"] = steps;
            _state["placed"] = placed;
            _state["realSeconds"] = Math.Round(Time.unscaledTime - _startReal, 1);
            if (_pumpDiagnostics.Count > 0) _state["waterInputTries"] = _pumpDiagnostics;
            try { File.WriteAllText(Path.Combine(_dir, "state.json"), _state.ToString(Formatting.Indented)); }
            catch (Exception e) { Harness.Warn("playtest: writing state.json failed: " + e.Message); }
        }
    }
}
