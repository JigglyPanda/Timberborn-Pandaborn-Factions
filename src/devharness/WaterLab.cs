using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using Bindito.Core;
using Newtonsoft.Json.Linq;
using Timberborn.BlockObjectTools;
using Timberborn.BlockSystem;
using Timberborn.Buildings;
using Timberborn.CameraSystem;
using Timberborn.ConstructionSites;
using Timberborn.Coordinates;
using Timberborn.Cutting;
using Timberborn.Demolishing;
using Timberborn.EntitySystem;
using Timberborn.GameCycleSystem;
using Timberborn.GameDistricts;
using Timberborn.Gathering;
using Timberborn.Growing;
using Timberborn.HazardousWeatherSystem;
using Timberborn.MapIndexSystem;
using Timberborn.MechanicalSystem;
using Timberborn.NaturalResources;
using Timberborn.NaturalResourcesLifecycle;
using Timberborn.NaturalResourcesReproduction;
using Timberborn.Planting;
using Timberborn.Forestry;
using Timberborn.PowerGeneration;
using Timberborn.SingletonSystem;
using Timberborn.SoilMoistureSystem;
using Timberborn.TemplateSystem;
using Timberborn.TerrainSystem;
using Timberborn.TickSystem;
using Timberborn.TimeSystem;
using Timberborn.WaterBuildings;
using Timberborn.WaterSystem;
using Timberborn.WeatherSystem;
using Timberborn.Workshops;
using Timberborn.StatusSystem;
using Timberborn.Goods;
using Timberborn.WorkSystem;
using Timberborn.EnterableSystem;
using Timberborn.ResourceCountingSystem;
using UnityEngine;

namespace PandabornDevHarness
{
    [Context("Game")]
    public class WaterLabConfigurator : Configurator
    {
        protected override void Configure()
        {
            if (!Harness.Active || !(Harness.Request?.Raw?["water"] is JObject)) return;
            Bind<WaterLab>().AsSingleton();
        }
    }

    /// <summary>
    /// Scripted water/plant scenarios for the water-toolkit prototype. Active only when request.json has a "water" object:
    /// <code>
    /// "water": { "name": "flume", "speed": 7, "area": [24, 16], "origin": "auto" | [x, y, z] | { "nearDistrict": [dx, dy] },
    ///            "flattenMargin": 2, "steps": [ { "op": ... }, ... ] }
    /// </code>
    /// All step coordinates are relative to the origin: x, y in tiles, z relative to the flattened ground surface (z = 0 is
    /// the first air cell, where a building on the ground stands). Ops (see <see cref="Execute"/>): flatten, place,
    /// placeLine, demolish, water, waterOff, addWater, wait, probe, series, seriesStop, plant, plants, grow, expect, shot,
    /// drought, set, markCut, markPlant, note. The game is paused between steps; "wait" runs it at the lab speed.
    /// Results go to result.json under "water": origin, step log, probes, series, checks. A failed "expect" is logged as a
    /// harness error, so the run fails.
    /// </summary>
    public class WaterLab : ILoadableSingleton, IUpdatableSingleton, ITickableSingleton
    {
        private readonly IWaterService _waterService;
        private readonly IThreadSafeWaterMap _waterMap;
        private readonly ITerrainService _terrainService;
        private readonly IThreadSafeColumnTerrainMap _columnTerrainMap;
        private readonly MapIndexService _mapIndexService;
        private readonly ISoilMoistureService _soilMoistureService;
        private readonly IBlockService _blockService;
        private readonly EntityService _entityService;
        private readonly TemplateService _templateService;
        private readonly PreviewPlacerFactory _previewPlacerFactory;
        private readonly ConstructionFactory _constructionFactory;
        private readonly BlockObjectFactory _blockObjectFactory;
        private readonly NaturalResourceFactory _naturalResourceFactory;
        private readonly SpeedManager _speedManager;
        private readonly IDayNightCycle _dayNightCycle;
        private readonly ITickService _tickService;
        private readonly CameraService _cameraService;
        private readonly DistrictCenterRegistry _districtCenterRegistry;
        private readonly WeatherService _weatherService;
        private readonly HazardousWeatherService _hazardousWeatherService;
        private readonly WeatherFastForwarder _weatherFastForwarder;
        private readonly GameCycleService _gameCycleService;
        private readonly TreeCuttingArea _treeCuttingArea;
        private readonly PlantingService _plantingService;
        private readonly ResourceCountingService _resourceCountingService;

        private JObject _spec;
        private JArray _steps;
        private JObject _out;
        private JArray _log, _checks;
        private JObject _probes, _series;
        private int _stepIndex;
        private bool _started, _done;
        private Vector3Int _origin;
        private float _speed = 3f;
        private int _shotDelay;
        private bool _changedSinceShot;

        private long _ticks;
        private long _waitUntilTick = -1;
        private float _waitUntilHours = -1f;
        private float _waitStartedReal;
        private float _waitCapReal;

        private readonly Dictionary<string, BlockObject> _objects = new Dictionary<string, BlockObject>();
        private readonly Dictionary<string, Source> _sources = new Dictionary<string, Source>();
        private readonly Dictionary<string, Series> _seriesById = new Dictionary<string, Series>();

        private class Source
        {
            public Vector3Int Cell;
            public float Rate;          // per second; negative drains
            public bool Contaminated;
            public float MaxDepth;      // > 0: only add while the cell is shallower (a constant-head reservoir)
            public double Total;
        }

        private class Series
        {
            public string Id;
            public int Every;
            public List<Vector3Int> Cells = new List<Vector3Int>();
            public List<Vector3Int> ContaminationCells = new List<Vector3Int>();
            public List<int[]> VolumeRects = new List<int[]>();
            public List<string> Objects = new List<string>();
            public JArray Rows = new JArray();
        }

        public WaterLab(IWaterService waterService, IThreadSafeWaterMap waterMap, ITerrainService terrainService,
                        IThreadSafeColumnTerrainMap columnTerrainMap, MapIndexService mapIndexService,
                        ISoilMoistureService soilMoistureService, IBlockService blockService, EntityService entityService,
                        TemplateService templateService, PreviewPlacerFactory previewPlacerFactory,
                        ConstructionFactory constructionFactory, BlockObjectFactory blockObjectFactory,
                        NaturalResourceFactory naturalResourceFactory, SpeedManager speedManager, IDayNightCycle dayNightCycle,
                        ITickService tickService, CameraService cameraService, DistrictCenterRegistry districtCenterRegistry,
                        WeatherService weatherService, HazardousWeatherService hazardousWeatherService,
                        WeatherFastForwarder weatherFastForwarder, GameCycleService gameCycleService,
                        TreeCuttingArea treeCuttingArea, PlantingService plantingService,
                        ResourceCountingService resourceCountingService)
        {
            _waterService = waterService;
            _waterMap = waterMap;
            _terrainService = terrainService;
            _columnTerrainMap = columnTerrainMap;
            _mapIndexService = mapIndexService;
            _soilMoistureService = soilMoistureService;
            _blockService = blockService;
            _entityService = entityService;
            _templateService = templateService;
            _previewPlacerFactory = previewPlacerFactory;
            _constructionFactory = constructionFactory;
            _blockObjectFactory = blockObjectFactory;
            _naturalResourceFactory = naturalResourceFactory;
            _speedManager = speedManager;
            _dayNightCycle = dayNightCycle;
            _tickService = tickService;
            _cameraService = cameraService;
            _districtCenterRegistry = districtCenterRegistry;
            _weatherService = weatherService;
            _hazardousWeatherService = hazardousWeatherService;
            _weatherFastForwarder = weatherFastForwarder;
            _gameCycleService = gameCycleService;
            _treeCuttingArea = treeCuttingArea;
            _plantingService = plantingService;
            _resourceCountingService = resourceCountingService;
        }

        public void Load()
        {
            _spec = (JObject)Harness.Request.Raw["water"];
            _steps = _spec["steps"] as JArray ?? new JArray();
            _speed = Request.Num(_spec, "speed", 3f);
            _out = new JObject { ["name"] = Request.Str(_spec, "name", "water"), ["status"] = "waiting" };
            _log = new JArray();
            _checks = new JArray();
            _probes = new JObject();
            _series = new JObject();
            _out["log"] = _log;
            _out["probes"] = _probes;
            _out["series"] = _series;
            _out["checks"] = _checks;
            Harness.Result["water"] = _out;
            Harness.Info("water lab loaded: " + _out["name"] + ", " + _steps.Count + " steps");
        }

        // ------------------------------------------------------------------ ticking

        public void Tick()
        {
            if (!_started || _done) return;
            _ticks++;
            float dt = _tickService.TickIntervalInSeconds;
            foreach (var s in _sources.Values)
            {
                float amount = Mathf.Abs(s.Rate) * dt;
                if (amount <= 0f) continue;
                if (s.Rate > 0f)
                {
                    if (s.MaxDepth > 0f)
                    {
                        float room = s.MaxDepth - _waterMap.WaterDepth(s.Cell);
                        if (room <= 0f) continue;
                        amount = Mathf.Min(amount, room);
                    }
                    if (s.Contaminated) _waterService.AddContaminatedWater(s.Cell, amount);
                    else _waterService.AddCleanWater(s.Cell, amount);
                    s.Total += amount;
                }
                else
                {
                    // drain: every third tick only, so each request sees a snapshot that already includes the last one
                    // (removals are queued and applied a tick later); never ask for more than is there
                    if (_ticks % 3 != 0) continue;
                    amount *= 3f;
                    float available = _waterMap.WaterDepth(s.Cell) - Mathf.Max(0f, s.MaxDepth);   // maxDepth on a drain = level kept
                    float take = Mathf.Min(amount, available);
                    if (take > 0f)
                    {
                        // remove clean and contaminated parts in proportion, so draining does not concentrate badwater
                        float c = Mathf.Clamp01(_waterMap.ColumnContamination(s.Cell));
                        if (c < 1f) _waterService.RemoveCleanWater(s.Cell, take * (1f - c));
                        if (c > 0f) _waterService.RemoveContaminatedWater(s.Cell, take * c);
                        s.Total -= take;
                    }
                }
            }
            foreach (var series in _seriesById.Values)
                if (series.Every > 0 && _ticks % series.Every == 0) series.Rows.Add(SampleRow(series));
        }

        public void UpdateSingleton()
        {
            if (_done || Harness.Finished) return;
            try { Step(); }
            catch (Exception e)
            {
                Harness.Error("water lab failed at step " + _stepIndex, e);
                Finish("error");
            }
        }

        private void Step()
        {
            if (!_started)
            {
                if (Harness.Result["run"] == null) return;   // the game driver has not started its run phase yet
                _started = true;
                _speedManager.ChangeSpeed(0f);
                ChooseOrigin();
                _out["status"] = "running";
                return;
            }
            if (_waitUntilTick >= 0 || _waitUntilHours >= 0f)
            {
                bool reached = _waitUntilTick >= 0 ? _ticks >= _waitUntilTick : Hours() >= _waitUntilHours;
                bool capped = Time.unscaledTime - _waitStartedReal > _waitCapReal;
                if (!reached && !capped) return;
                if (capped && !reached) Note("wait capped after " + _waitCapReal + " real s at tick " + _ticks);
                _waitUntilTick = -1;
                _waitUntilHours = -1f;
                _speedManager.ChangeSpeed(0f);
                return;   // give the pause one frame
            }
            // run instant steps until a wait or the end; at most 40 per frame
            if (_shotDelay > 0) { _shotDelay--; return; }
            for (int n = 0; n < 40; n++)
            {
                if (_stepIndex >= _steps.Count) { Finish("completed"); return; }
                var step = (JObject)_steps[_stepIndex];
                // pictures wait a few frames after other changes so terrain and models are rebuilt
                if (Request.Str(step, "op", "") == "shot" && _shotDelay == 0 && _changedSinceShot) { _shotDelay = 3; _changedSinceShot = false; return; }
                _stepIndex++;
                if (Request.Str(step, "op", "") != "shot") _changedSinceShot = true;
                Execute(step);
                if (_waitUntilTick >= 0 || _waitUntilHours >= 0f) return;
                if (Request.Str(step, "op", "") == "shot") return;   // one render per frame
            }
        }

        private void Finish(string status)
        {
            _done = true;
            _out["status"] = status;
            _out["ticks"] = _ticks;
            _out["day"] = Math.Round(_dayNightCycle.PartialDayNumber, 3);
            foreach (var s in _seriesById.Values) _series[s.Id] = s.Rows;
            var sources = new JObject();
            foreach (var kv in _sources) sources[kv.Key] = Math.Round(kv.Value.Total, 4);
            _out["sourceTotals"] = sources;
            _speedManager.ChangeSpeed(0f);
            Harness.Info("water lab " + status + " after " + _ticks + " ticks; " + _checks.Count(c => !(bool)c["pass"]) + " failed check(s)");
            // end the game driver's run phase now
            Harness.Request.RunInGameHours = 0f;
            Harness.Request.RunRealSeconds = 0f;
        }

        private float Hours()
        {
            return _dayNightCycle.PartialDayNumber * 24f;
        }

        // ------------------------------------------------------------------ origin and terrain

        private void ChooseOrigin()
        {
            var size = _terrainService.Size;
            var area = _spec["area"] as JArray;
            int w = area != null ? (int)area[0] : 24, h = area != null ? (int)area[1] : 16;
            int margin = (int)Request.Num(_spec, "flattenMargin", 2f);
            var originToken = _spec["origin"];
            Vector2Int corner;
            int z0;
            if (originToken is JArray fixedOrigin)
            {
                corner = new Vector2Int((int)fixedOrigin[0], (int)fixedOrigin[1]);
                z0 = fixedOrigin.Count > 2 ? (int)fixedOrigin[2] : MedianHeight(corner, w, h);
            }
            else
            {
                Vector2Int? near = null;
                bool preferNear = false;
                var center = _districtCenterRegistry.AllDistrictCenters.FirstOrDefault();
                if (originToken is JObject o && center != null)
                {
                    if (o["nearDistrict"] is JArray d) near = new Vector2Int(center.CenterCoordinates.x + (int)d[0], center.CenterCoordinates.y + (int)d[1]);
                    else if (Request.Bool(o, "nearDistrict", false)) preferNear = true;
                }
                corner = near ?? FindDryArea(size, w, h, margin, preferNear);
                // next to the district the ground is levelled to the doorstep so a straight path can reach it
                z0 = (near.HasValue || preferNear) && center != null ? center.CenterCoordinates.z : MedianHeight(corner, w, h);
            }
            _origin = new Vector3Int(corner.x, corner.y, z0);
            _out["origin"] = Arr(_origin);
            _out["area"] = new JArray(w, h);
            _out["mapSize"] = Arr(size);
            var dc = _districtCenterRegistry.AllDistrictCenters.FirstOrDefault();
            if (dc != null) _out["districtCenter"] = Arr(dc.CenterCoordinates);
            Note("origin " + _origin + " (area " + w + "x" + h + ", map " + size + ")");
            if (Request.Bool(_spec, "flatten", true))
                Flatten(-margin, -margin, w - 1 + margin, h - 1 + margin, 0);
        }

        private int Surface(int x, int y)
        {
            return _terrainService.GetTerrainHeightBelow(new Vector3Int(x, y, _terrainService.Size.z - 1));
        }

        private int MedianHeight(Vector2Int corner, int w, int h)
        {
            var heights = new List<int>();
            for (int x = 0; x < w; x++)
                for (int y = 0; y < h; y++)
                    if (_terrainService.Contains(new Vector2Int(corner.x + x, corner.y + y))) heights.Add(Surface(corner.x + x, corner.y + y));
            heights.Sort();
            return heights.Count > 0 ? heights[heights.Count / 2] : 0;
        }

        /// <summary>A dry, building-free, single-level area far from the district center, as flat as possible.</summary>
        private Vector2Int FindDryArea(Vector3Int size, int w, int h, int margin, bool preferNear)
        {
            var dc = _districtCenterRegistry.AllDistrictCenters.FirstOrDefault();
            Vector2Int best = new Vector2Int(margin + 4, margin + 4);
            float bestScore = float.MaxValue;
            int pad = margin + (int)Request.Num(_spec, "dryPad", 10f);
            int candidates = 0;
            for (int cx = pad; cx + w + pad < size.x; cx += 3)
                for (int cy = pad; cy + h + pad < size.y; cy += 3)
                {
                    int min = int.MaxValue, max = int.MinValue;
                    bool ok = true;
                    for (int x = -pad; x < w + pad && ok; x++)
                        for (int y = -pad; y < h + pad && ok; y++)
                        {
                            var c = new Vector2Int(cx + x, cy + y);
                            if (_waterMap.IsWaterOnAnyHeight(c)) { ok = false; break; }
                            if (_terrainService.GetColumnCount(_mapIndexService.CellToIndex(c)) > 1) { ok = false; break; }
                            int s = Surface(c.x, c.y);
                            if (x >= -margin && x < w + margin && y >= -margin && y < h + margin)
                            {
                                min = Math.Min(min, s); max = Math.Max(max, s);
                                foreach (var bo in _blockService.GetObjectsAt(new Vector3Int(c.x, c.y, s)))
                                    if (bo.GetComponent<NaturalResource>() == null) { ok = false; break; }
                            }
                        }
                    if (!ok) continue;
                    candidates++;
                    float score = (max - min) * 10f;
                    if (dc != null)
                    {
                        float dist = Vector2.Distance(new Vector2(cx + w / 2f, cy + h / 2f), new Vector2(dc.CenterCoordinates.x, dc.CenterCoordinates.y));
                        if (preferNear) score = (max - min) * 2f + dist;
                        else
                        {
                            if (dist < 20f) score += 100f;
                            score += dist * 0.05f;
                        }
                    }
                    if (score < bestScore) { bestScore = score; best = new Vector2Int(cx, cy); }
                }
            _out["areaSearchScore"] = bestScore;
            _out["areaCandidates"] = candidates;
            if (candidates == 0) Harness.Error("water lab: no dry, free " + w + "x" + h + " area (pad " + pad + ") on this map; using " + best);
            return best;
        }

        /// <summary>Sets the ground surface of a rectangle (relative, inclusive) to origin z + z, removing plants first.</summary>
        private void Flatten(int x0, int y0, int x1, int y1, int z)
        {
            int target = _origin.z + z;
            int changed = 0, removed = 0;
            for (int x = Math.Min(x0, x1); x <= Math.Max(x0, x1); x++)
                for (int y = Math.Min(y0, y1); y <= Math.Max(y0, y1); y++)
                {
                    int ax = _origin.x + x, ay = _origin.y + y;
                    if (!_terrainService.Contains(new Vector2Int(ax, ay))) continue;
                    int s = Surface(ax, ay);
                    for (int zz = Math.Min(s, target) - 1; zz <= Math.Max(s, target) + 3; zz++)
                    {
                        var cell = new Vector3Int(ax, ay, zz);
                        if (!_blockService.Contains(cell)) continue;
                        foreach (var bo in _blockService.GetObjectsAt(cell).ToList())
                            if (bo && bo.GetComponent<NaturalResource>() != null) { _entityService.Delete(bo); removed++; }
                    }
                    if (s < target) { _terrainService.SetTerrain(new Vector3Int(ax, ay, s), target - s); changed++; }
                    else if (s > target) { _terrainService.UnsetTerrain(new Vector3Int(ax, ay, s - 1), s - target); changed++; }
                }
            Note("flatten [" + x0 + "," + y0 + "]..[" + x1 + "," + y1 + "] to z" + z + ": " + changed + " columns changed, " + removed + " plants removed");
        }

        // ------------------------------------------------------------------ steps

        private void Execute(JObject step)
        {
            string op = Request.Str(step, "op", "");
            switch (op)
            {
                case "note":
                    Note(Request.Str(step, "text", ""));
                    break;
                case "flatten":
                {
                    var r = (JArray)step["rect"];
                    Flatten((int)r[0], (int)r[1], (int)r[2], (int)r[3], (int)Request.Num(step, "z", 0f));
                    break;
                }
                case "place":
                    Place(step, Rel(step["at"]), Request.Str(step, "id", null));
                    break;
                case "placeLine":
                {
                    var from = Rel(step["from"]);
                    var d = step["step"] as JArray ?? new JArray(0, 1, 0);
                    int count = (int)Request.Num(step, "count", 1f);
                    string prefix = Request.Str(step, "idPrefix", null);
                    for (int i = 0; i < count; i++)
                        Place(step, from + new Vector3Int((int)d[0] * i, (int)d[1] * i, (int)d[2] * i), prefix != null ? prefix + i : null);
                    break;
                }
                case "demolish":
                {
                    string id = Request.Str(step, "id", null);
                    if (id != null && _objects.TryGetValue(id, out var bo) && bo) { _entityService.Delete(bo); _objects.Remove(id); Note("demolished " + id); }
                    else Note("demolish: no object " + id);
                    break;
                }
                case "water":
                {
                    string id = Request.Str(step, "id", "src" + _sources.Count);
                    _sources[id] = new Source { Cell = Rel(step["at"]), Rate = Request.Num(step, "rate", 0.5f), Contaminated = Request.Bool(step, "contaminated", false),
                                              MaxDepth = Request.Num(step, "maxDepth", 0f) };
                    Note("water source " + id + " at " + _sources[id].Cell + " rate " + _sources[id].Rate);
                    break;
                }
                case "waterOff":
                {
                    string id = Request.Str(step, "id", null);
                    if (id != null && _sources.TryGetValue(id, out var s)) { s.Rate = 0f; Note("water source " + id + " off; total " + Math.Round(s.Total, 3)); }
                    break;
                }
                case "addWater":
                {
                    var cell = Rel(step["at"]);
                    float amount = Request.Num(step, "amount", 1f);
                    if (amount >= 0f) _waterService.AddCleanWater(cell, amount); else _waterService.RemoveCleanWater(cell, -amount);
                    Note("addWater " + amount + " at " + cell);
                    break;
                }
                case "wait":
                    BeginWait(step);
                    break;
                case "probe":
                    Probe(step);
                    WriteProgress();
                    break;
                case "series":
                {
                    var s = new Series { Id = Request.Str(step, "id", "s" + _seriesById.Count), Every = (int)Request.Num(step, "every", 20f) };
                    if (step["cells"] is JArray cells) foreach (var c in cells) s.Cells.Add(Rel(c));
                    if (step["contamination"] is JArray ccells) foreach (var c in ccells) s.ContaminationCells.Add(Rel(c));
                    if (step["volumes"] is JArray vols) foreach (JArray r in vols) s.VolumeRects.Add(new[] { (int)r[0], (int)r[1], (int)r[2], (int)r[3], r.Count > 4 ? (int)r[4] : 0 });
                    if (step["objects"] is JArray objs) foreach (var o in objs) s.Objects.Add((string)o);
                    _seriesById[s.Id] = s;
                    var header = new JArray("tick", "hours");
                    foreach (var c in s.Cells) header.Add("d" + Arr(c - _origin).ToString(Newtonsoft.Json.Formatting.None));
                    foreach (var c in s.ContaminationCells) header.Add("c" + Arr(c - _origin).ToString(Newtonsoft.Json.Formatting.None));
                    foreach (var r in s.VolumeRects) header.Add("vol" + string.Join(",", r));
                    foreach (var o in s.Objects) header.Add("obj:" + o);
                    s.Rows.Add(header);
                    s.Rows.Add(SampleRow(s));
                    break;
                }
                case "seriesStop":
                {
                    string id = Request.Str(step, "id", null);
                    if (id != null && _seriesById.TryGetValue(id, out var s)) { s.Rows.Add(SampleRow(s)); s.Every = 0; }
                    break;
                }
                case "plant":
                {
                    string template = Request.Str(step, "template", null);
                    int ok = 0, failed = 0;
                    foreach (var c in Cells(step))
                    {
                        var resource = _naturalResourceFactory.SpawnIgnoringConstraints(template, c);
                        if (resource) ok++; else failed++;
                    }
                    Note("plant " + template + ": " + ok + " spawned, " + failed + " refused");
                    break;
                }
                case "grow":
                {
                    string template = Request.Str(step, "template", null);
                    float progress = Request.Num(step, "progress", 1f);
                    int n = 0;
                    foreach (var r in PlantsIn(step, template)) { var g = r.GetComponent<Growable>(); if (g != null && !g.IsGrown) { g.IncreaseGrowthProgress(progress); n++; } }
                    Note("grow " + template + " by " + progress + ": " + n + " plants");
                    break;
                }
                case "plants":
                    ProbePlants(step);
                    WriteProgress();
                    break;
                case "expect":
                    Expect(step);
                    break;
                case "shot":
                    Shot(step);
                    break;
                case "drought":
                {
                    int guard = 0;
                    while (!(_weatherService.IsHazardousWeather && _hazardousWeatherService.CurrentCycleHazardousWeather is DroughtWeather) && guard++ < 4)
                        _weatherFastForwarder.JumpToNextSeason();
                    Note("drought: hazardous=" + _weatherService.IsHazardousWeather + " kind=" + _hazardousWeatherService.CurrentCycleHazardousWeather?.GetType().Name
                         + " cycleDay=" + _gameCycleService.CycleDay + " after " + guard + " jump(s)");
                    break;
                }
                case "nextSeason":
                    _weatherFastForwarder.JumpToNextSeason();
                    Note("next season: hazardous=" + _weatherService.IsHazardousWeather + " cycleDay=" + _gameCycleService.CycleDay);
                    break;
                case "set":
                    Set(step);
                    break;
                case "markCut":
                    _treeCuttingArea.AddCoordinates(Cells(step).ToList());
                    Note("marked for cutting: " + Cells(step).Count() + " cells");
                    break;
                case "unmarkCut":
                    _treeCuttingArea.RemoveCoordinates(Cells(step).ToList());
                    break;
                case "markPlant":
                {
                    string template = Request.Str(step, "template", null);
                    int n = 0;
                    foreach (var c in Cells(step)) { _plantingService.SetPlantingCoordinates(c, template); n++; }
                    Note("marked for planting " + template + ": " + n + " cells");
                    break;
                }
                case "giveGoods":
                {
                    string id = Request.Str(step, "id", null);
                    var manufactory = id != null && _objects.TryGetValue(id, out var gbo) && gbo ? gbo.GetComponent<Manufactory>() : null;
                    if (manufactory?.Inventory == null) { Note("giveGoods: no manufactory " + id); break; }
                    int amount = (int)Request.Num(step, "amount", 1f);
                    manufactory.Inventory.GiveExistingIgnoringCapacity(new GoodAmount(Request.Str(step, "good", "Water"), amount));
                    Note("gave " + amount + " " + Request.Str(step, "good", "Water") + " to " + id + "; stock " + manufactory.Inventory.TotalAmountInStock);
                    break;
                }
                case "pathFromDistrict":
                    PathFromDistrict(Rel(step["to"]));
                    break;
                default:
                    Harness.Warn("water lab: unknown op '" + op + "'");
                    break;
            }
        }

        private void BeginWait(JObject step)
        {
            _waitStartedReal = Time.unscaledTime;
            _waitCapReal = Request.Num(step, "capSeconds", 600f);
            if (step["ticks"] != null) _waitUntilTick = _ticks + (long)Request.Num(step, "ticks", 0f);
            else _waitUntilHours = Hours() + Request.Num(step, "hours", 0f) + 24f * Request.Num(step, "days", 0f);
            float speed = Request.Num(step, "speed", _speed);
            _speedManager.ChangeSpeed(speed);
        }

        private Vector3Int Rel(JToken token)
        {
            var a = (JArray)token;
            return _origin + new Vector3Int((int)a[0], (int)a[1], a.Count > 2 ? (int)a[2] : 0);
        }

        private IEnumerable<Vector3Int> Cells(JObject step)
        {
            if (step["cells"] is JArray cells) foreach (var c in cells) yield return Rel(c);
            if (step["rect"] is JArray r)
            {
                int z = r.Count > 4 ? (int)r[4] : (int)Request.Num(step, "z", 0f);
                for (int x = Math.Min((int)r[0], (int)r[2]); x <= Math.Max((int)r[0], (int)r[2]); x++)
                    for (int y = Math.Min((int)r[1], (int)r[3]); y <= Math.Max((int)r[1], (int)r[3]); y++)
                        yield return _origin + new Vector3Int(x, y, z);
            }
            if (step["at"] is JArray) yield return Rel(step["at"]);
        }

        /// <summary>Snapshot to progress.json so long runs can be inspected while they go.</summary>
        private void WriteProgress()
        {
            foreach (var s in _seriesById.Values) _series[s.Id] = s.Rows;
            try { Harness.WriteResult("running"); }
            catch (Exception e) { Harness.Warn("water lab: progress write failed: " + e.Message); }
        }

        private void Note(string text)
        {
            _log.Add(new JObject { ["tick"] = _ticks, ["hours"] = Math.Round(Hours(), 2), ["text"] = text });
            Harness.Info("water: " + text);
        }

        // ------------------------------------------------------------------ placing

        private void Place(JObject step, Vector3Int at, string id)
        {
            string template = Request.Str(step, "template", null);
            var entry = new JObject { ["op"] = "place", ["template"] = template, ["at"] = Arr(at - _origin), ["id"] = id };
            var spec = _templateService.GetAll<PlaceableBlockObjectSpec>()
                .FirstOrDefault(s => s.GetSpec<TemplateSpec>()?.TemplateName == template);
            if (spec == null)
            {
                entry["error"] = "template not available";
                Harness.Error("water lab: template " + template + " not available to this faction");
                _log.Add(entry);
                return;
            }
            var orientation = Orientation.Cw0;
            string o = Request.Str(step, "orientation", "Cw0");
            if (!Enum.TryParse(o, true, out orientation)) orientation = Orientation.Cw0;
            var placement = new Placement(at, orientation, FlipMode.Unflipped);
            bool valid;
            var placer = _previewPlacerFactory.Create(spec);
            try
            {
                var buildable = placer.GetBuildableCoordinates(new[] { placement }).ToList();
                valid = buildable.Count > 0;
                if (valid && buildable[0].Coordinates != at) entry["adjustedTo"] = Arr(buildable[0].Coordinates - _origin);
            }
            finally { placer.HideAllPreviews(); }
            entry["valid"] = valid;
            if (!valid && !Request.Bool(step, "force", false))
            {
                entry["error"] = "placement invalid";
                Harness.Warn("water lab: " + template + " at " + (at - _origin) + " " + orientation + " is not a valid placement");
                _log.Add(entry);
                return;
            }
            var builder = new EntitySetup.Builder(spec.Blueprint);
            BlockObject placed;
            if (spec.HasSpec<BuildingSpec>())
                placed = Request.Bool(step, "finished", true) ? _constructionFactory.CreateAsFinished(builder, placement) : _constructionFactory.CreateAsUnfinished(builder, placement);
            else placed = _blockObjectFactory.CreateFinished(builder, placement);
            if (id != null && placed) _objects[id] = placed;
            entry["placed"] = (bool)placed;
            entry["orientation"] = orientation.ToString();
            _log.Add(entry);
        }

        /// <summary>
        /// Levels a 1-wide L-shaped corridor from the district center's doorstep to the target at the doorstep height and
        /// lays "Path" on it. Of the two L orders, the one crossing no buildings is used.
        /// </summary>
        private void PathFromDistrict(Vector3Int target)
        {
            var center = _districtCenterRegistry.AllDistrictCenters.FirstOrDefault();
            if (center == null) { Note("pathFromDistrict: no district center"); return; }
            var start = center.CenterCoordinates;
            List<Vector3Int> best = null;
            foreach (bool xFirst in new[] { true, false })
            {
                var cells = new List<Vector3Int>();
                var c = new Vector3Int(start.x, start.y, start.z);
                cells.Add(c);
                for (int leg = 0; leg < 2; leg++)
                {
                    bool alongX = (leg == 0) == xFirst;
                    while (alongX ? c.x != target.x : c.y != target.y)
                    {
                        if (alongX) c.x += Math.Sign(target.x - c.x); else c.y += Math.Sign(target.y - c.y);
                        cells.Add(new Vector3Int(c.x, c.y, start.z));
                    }
                }
                bool blocked = cells.Skip(1).Any(cell =>
                {
                    int s = Surface(cell.x, cell.y);
                    for (int z = Math.Min(s, start.z); z <= Math.Max(s, start.z) + 2; z++)
                        foreach (var bo in _blockService.GetObjectsAt(new Vector3Int(cell.x, cell.y, z)))
                            if (bo.GetComponent<NaturalResource>() == null && bo.GetComponent<TemplateSpec>()?.TemplateName != "Path") return true;
                    return false;
                });
                if (!blocked) { best = cells; break; }
                if (best == null) best = cells;
            }
            var spec = _templateService.GetAll<PlaceableBlockObjectSpec>().FirstOrDefault(sp => sp.GetSpec<TemplateSpec>()?.TemplateName == "Path");
            int placed = 0, failed = 0;
            foreach (var cell in best)
            {
                int s = Surface(cell.x, cell.y);
                for (int z = Math.Min(s, start.z) - 1; z <= Math.Max(s, start.z) + 3; z++)
                {
                    var at = new Vector3Int(cell.x, cell.y, z);
                    if (!_blockService.Contains(at)) continue;
                    foreach (var bo in _blockService.GetObjectsAt(at).ToList())
                        if (bo && bo.GetComponent<NaturalResource>() != null) _entityService.Delete(bo);
                }
                if (s < start.z) _terrainService.SetTerrain(new Vector3Int(cell.x, cell.y, s), start.z - s);
                else if (s > start.z) _terrainService.UnsetTerrain(new Vector3Int(cell.x, cell.y, s - 1), s - start.z);
                if (spec == null || _blockService.GetObjectsAt(cell).Any(bo => bo.GetComponent<TemplateSpec>()?.TemplateName == "Path")) continue;
                var placer = _previewPlacerFactory.Create(spec);
                bool ok;
                try { ok = placer.GetBuildableCoordinates(new[] { new Placement(cell) }).Any(); }
                finally { placer.HideAllPreviews(); }
                if (!ok) { failed++; continue; }
                _constructionFactory.CreateAsFinished(new EntitySetup.Builder(spec.Blueprint), new Placement(cell));
                placed++;
            }
            Note("path from district " + start + " to " + target + ": " + best.Count + " cells, " + placed + " paths placed, " + failed + " invalid");
        }

        private void Set(JObject step)
        {
            string id = Request.Str(step, "id", null);
            if (id == null || !_objects.TryGetValue(id, out var bo) || !bo) { Note("set: no object " + id); return; }
            var valve = bo.GetComponent<ThrottlingValve>();
            if (valve != null)
            {
                if (step["limitEnabled"] != null) valve.SetOutflowLimitEnabled((bool)step["limitEnabled"]);
                if (step["limit"] != null) valve.SetOutflowLimit((float)step["limit"]);
            }
            var forester = bo.GetComponent<Forester>();
            if (forester != null && step["replantDeadTrees"] != null) forester.SetReplantDeadTrees((bool)step["replantDeadTrees"]);
            var fill = bo.GetComponent<FillValve>();
            if (fill != null)
            {
                if (step["targetEnabled"] != null) fill.SetTargetHeightEnabled((bool)step["targetEnabled"]);
                if (step["targetDepth"] != null) fill.SetTargetHeight(fill.MinTargetHeight + (float)step["targetDepth"]);
            }
            Note("set " + id + ": " + step.ToString(Newtonsoft.Json.Formatting.None));
        }

        // ------------------------------------------------------------------ measuring

        private JObject CellInfo(Vector3Int c)
        {
            var o = new JObject { ["cell"] = Arr(c - _origin) };
            if (!_terrainService.Contains(c)) { o["outside"] = true; return o; }
            o["depth"] = R(_waterMap.WaterDepth(c));
            o["height"] = R(_waterMap.WaterHeightOrFloor(c) - _origin.z);
            if (_waterMap.TryGetColumnFloor(c, out int floor)) o["floor"] = floor - _origin.z;
            o["contamination"] = R(_waterMap.ColumnContamination(c));
            var flow = _waterMap.WaterFlowDirection(c);
            o["flow"] = new JArray(R(flow.x), R(flow.y));
            o["moisture"] = R(Moisture(c));
            o["moist"] = _soilMoistureService.SoilIsMoist(c);
            return o;
        }

        private float Moisture(Vector3Int c)
        {
            int index2D = _mapIndexService.CellToIndex(new Vector2Int(c.x, c.y));
            return _columnTerrainMap.TryGetIndexAtCeiling(index2D, c.z, out int index3D) ? _soilMoistureService.SoilMoisture(index3D) : -1f;
        }

        private float Volume(int[] r)
        {
            float v = 0f;
            for (int x = Math.Min(r[0], r[2]); x <= Math.Max(r[0], r[2]); x++)
                for (int y = Math.Min(r[1], r[3]); y <= Math.Max(r[1], r[3]); y++)
                    v += _waterMap.WaterDepth(_origin + new Vector3Int(x, y, r[4]));
            return v;
        }

        private JArray SampleRow(Series s)
        {
            var row = new JArray(_ticks, Math.Round(Hours(), 3));
            foreach (var c in s.Cells) row.Add(R(_waterMap.WaterDepth(c)));
            foreach (var c in s.ContaminationCells) row.Add(R(_waterMap.ColumnContamination(c)));
            foreach (var r in s.VolumeRects) row.Add(R(Volume(r)));
            foreach (var id in s.Objects) row.Add(ObjectValue(id));
            return row;
        }

        /// <summary>One number per object for time series: lift rate for movers, stock for manufactories.</summary>
        private JToken ObjectValue(string id)
        {
            if (!_objects.TryGetValue(id, out var bo) || !bo) return null;
            var mover = bo.GetComponent<WaterMover>();
            if (mover != null) return R(mover.CanMoveWater ? mover.EffectiveFlowRate : 0f);
            var manufactory = bo.GetComponent<Manufactory>();
            if (manufactory != null) return R((manufactory.Inventory?.TotalAmountInStock ?? 0) + manufactory.ProductionProgress);
            return null;
        }

        private JObject ObjectInfo(string id)
        {
            var o = new JObject { ["id"] = id };
            if (!_objects.TryGetValue(id, out var bo) || !bo) { o["missing"] = true; return o; }
            o["template"] = bo.GetComponent<TemplateSpec>()?.TemplateName;
            o["at"] = Arr(bo.Coordinates - _origin);
            o["finished"] = bo.IsFinished;
            var node = bo.GetComponent<MechanicalNode>();
            if (node != null)
            {
                o["powerEfficiency"] = R(node.PowerEfficiency);
                o["outputMultiplier"] = R(node.OutputMultiplier);
                o["activeAndPowered"] = node.ActiveAndPowered;
                o["graphNodes"] = node.Graph?.Nodes.Count() ?? 0;
                o["supply"] = node.Graph?.PowerSupply ?? 0;
                o["demand"] = node.Graph?.PowerDemand ?? 0;
            }
            var gen = bo.GetComponent<WaterPoweredGenerator>();
            if (gen != null) o["generatorRotation"] = R(gen.GeneratorRotation);
            var mover = bo.GetComponent<WaterMover>();
            if (mover != null) { o["canMove"] = mover.CanMoveWater; o["effectiveFlowRate"] = R(mover.EffectiveFlowRate); }
            var manufactory = bo.GetComponent<Manufactory>();
            if (manufactory != null)
            {
                o["stock"] = manufactory.Inventory?.TotalAmountInStock ?? -1;
                o["productionProgress"] = R(manufactory.ProductionProgress);
                o["readyToProduce"] = manufactory.IsReadyToProduce;
            }
            var workplace = bo.GetComponent<Workplace>();
            if (workplace != null) { o["workers"] = workplace.NumberOfAssignedWorkers; o["maxWorkers"] = workplace.MaxWorkers; }
            var enterable = bo.GetComponent<Enterable>();
            if (enterable != null) o["inside"] = enterable.NumberOfEnterersInside;
            var statusSubject = bo.GetComponent<StatusSubject>();
            if (statusSubject != null && statusSubject.ActiveStatuses.Count > 0)
            {
                var st = new JArray();
                foreach (var status in statusSubject.ActiveStatuses) st.Add(status.StatusDescription);
                o["statuses"] = st;
            }
            var valve = bo.GetComponent<ThrottlingValve>();
            if (valve != null) o["valveCurrentLimit"] = valve.CurrentOutflowLimit.HasValue ? (JToken)R(valve.CurrentOutflowLimit.Value) : null;
            var fill = bo.GetComponent<FillValve>();
            if (fill != null) { o["fillTargetDepth"] = R(fill.TargetDepth); o["fillActualHeight"] = R(fill.ActualHeight - _origin.z); }
            return o;
        }

        private void Probe(JObject step)
        {
            string label = Request.Str(step, "label", "probe" + _probes.Count);
            var p = new JObject { ["tick"] = _ticks, ["hours"] = Math.Round(Hours(), 3), ["day"] = Math.Round(_dayNightCycle.PartialDayNumber, 3),
                                  ["drought"] = _weatherService.IsHazardousWeather };
            if (_sources.Count > 0)
            {
                var totals = new JObject();
                foreach (var kv in _sources) totals[kv.Key] = Math.Round(kv.Value.Total, 4);
                p["sourceTotals"] = totals;
            }
            var cells = new JArray();
            foreach (var c in Cells(step)) cells.Add(CellInfo(c));
            if (cells.Count > 0) p["cells"] = cells;
            if (step["volumes"] is JArray vols)
            {
                var v = new JArray();
                foreach (JArray r in vols) v.Add(new JObject { ["rect"] = r, ["volume"] = R(Volume(new[] { (int)r[0], (int)r[1], (int)r[2], (int)r[3], r.Count > 4 ? (int)r[4] : 0 })) });
                p["volumes"] = v;
            }
            if (step["objects"] is JArray objs) { var a = new JArray(); foreach (var o in objs) a.Add(ObjectInfo((string)o)); p["objects"] = a; }
            if (step["goods"] is JArray goods)
            {
                var g = new JObject();
                foreach (var t in goods)
                {
                    var count = _resourceCountingService.GetGlobalResourceCount((string)t);
                    g[(string)t] = new JObject { ["stockpiled"] = count.StockpiledStock, ["bufferedOutput"] = count.BufferedOutputStock,
                                                 ["carriedToStockpiles"] = count.CarriedToStockpilesStock };
                }
                p["goods"] = g;
            }
            if (step["rows"] is JArray rows)
            {
                // compact depth grid: one string per row, depths in hundredths
                var grid = new JArray();
                foreach (JArray r in rows)
                {
                    int y = (int)r[0], x0 = (int)r[1], x1 = (int)r[2], z = r.Count > 3 ? (int)r[3] : 0;
                    var parts = new List<string>();
                    for (int x = x0; x <= x1; x++) parts.Add(((int)Math.Round(_waterMap.WaterDepth(_origin + new Vector3Int(x, y, z)) * 100)).ToString(CultureInfo.InvariantCulture));
                    grid.Add("y" + y + " z" + z + ": " + string.Join(" ", parts));
                }
                p["grid"] = grid;
            }
            if (step["moistRows"] is JArray mrows)
            {
                var grid = new JArray();
                foreach (JArray r in mrows)
                {
                    int y = (int)r[0], x0 = (int)r[1], x1 = (int)r[2], z = r.Count > 3 ? (int)r[3] : 0;
                    var parts = new List<string>();
                    for (int x = x0; x <= x1; x++) parts.Add(((int)Math.Round(Moisture(_origin + new Vector3Int(x, y, z)) * 10)).ToString(CultureInfo.InvariantCulture));
                    grid.Add("y" + y + " z" + z + ": " + string.Join(" ", parts));
                }
                p["moistGrid"] = grid;
            }
            _probes[label] = p;
        }

        private IEnumerable<NaturalResource> PlantsIn(JObject step, string template)
        {
            var seen = new HashSet<NaturalResource>();
            foreach (var c in Cells(step))
                for (int dz = -1; dz <= 1; dz++)
                {
                    var cell = c + new Vector3Int(0, 0, dz);
                    if (!_blockService.Contains(cell)) continue;
                    var r = _blockService.GetBottomObjectComponentAt<NaturalResource>(cell);
                    if (r == null || !seen.Add(r)) continue;
                    if (template != null && r.GetComponent<TemplateSpec>()?.TemplateName != template) continue;
                    yield return r;
                }
        }

        private JObject PlantInfo(NaturalResource r)
        {
            var bo = r.GetComponent<BlockObject>();
            var o = new JObject { ["t"] = r.GetComponent<TemplateSpec>()?.TemplateName, ["at"] = Arr(bo.Coordinates - _origin) };
            var g = r.GetComponent<Growable>();
            if (g != null) { o["growth"] = R(g.GrowthProgress); o["grown"] = g.IsGrown; }
            var living = r.GetComponent<LivingNaturalResource>();
            if (living != null) o["dead"] = living.IsDead;
            var dying = r.GetComponent<DyingNaturalResource>();
            if (dying != null)
            {
                o["dying"] = dying.IsDying;
                var p = dying.GetClosestDyingProgress();
                if (p.IsDying) o["daysLeft"] = R(p.DaysLeft);
            }
            var rep = r.GetComponent<Reproducible>();
            if (rep != null && rep.Enabled) o["reproBlocked"] = rep.ReproductionDisabled;
            var cut = r.GetComponent<Cuttable>();
            if (cut != null) o["cutYield"] = cut.Yielder.Yield.Amount;
            var gather = r.GetComponent<Gatherable>();
            if (gather != null) o["gatherYield"] = gather.Yielder.Yield.Amount;
            var demolish = r.GetComponent<Demolishable>();
            if (demolish != null && demolish.IsMarked) o["markedDemolish"] = true;
            if (_treeCuttingArea.IsInCuttingArea(bo.Coordinates)) o["inCuttingArea"] = true;
            if (_plantingService.IsResourceAt(bo.Coordinates)) o["plantingMarked"] = _plantingService.GetResourceAt(bo.Coordinates);
            o["water"] = R(_waterMap.WaterDepth(bo.Coordinates));
            o["moist"] = _soilMoistureService.SoilIsMoist(bo.Coordinates);
            return o;
        }

        private void ProbePlants(JObject step)
        {
            string label = Request.Str(step, "label", "plants" + _probes.Count);
            string template = Request.Str(step, "template", null);
            var list = new JArray();
            int alive = 0, dying = 0, dead = 0, grown = 0;
            foreach (var r in PlantsIn(step, template))
            {
                var info = PlantInfo(r);
                list.Add(info);
                if ((bool?)info["dead"] == true) dead++;
                else if ((bool?)info["dying"] == true) dying++;
                else alive++;
                if ((bool?)info["grown"] == true) grown++;
            }
            _probes[label] = new JObject
            {
                ["tick"] = _ticks, ["hours"] = Math.Round(Hours(), 3), ["day"] = Math.Round(_dayNightCycle.PartialDayNumber, 3),
                ["count"] = list.Count, ["healthy"] = alive, ["dying"] = dying, ["dead"] = dead, ["grown"] = grown,
                ["plants"] = Request.Bool(step, "detail", true) ? list : null
            };
        }

        private void Expect(JObject step)
        {
            string label = Request.Str(step, "label", "expect" + _checks.Count);
            string what = Request.Str(step, "what", "depth");
            float min = Request.Num(step, "min", float.MinValue), max = Request.Num(step, "max", float.MaxValue);
            double value;
            switch (what)
            {
                case "depth": value = _waterMap.WaterDepth(Rel(step["at"])); break;
                case "height": value = _waterMap.WaterHeightOrFloor(Rel(step["at"])) - _origin.z; break;
                case "moisture": value = Moisture(Rel(step["at"])); break;
                case "contamination": value = _waterMap.ColumnContamination(Rel(step["at"])); break;
                case "volume":
                {
                    var r = (JArray)step["rect"];
                    value = Volume(new[] { (int)r[0], (int)r[1], (int)r[2], (int)r[3], r.Count > 4 ? (int)r[4] : 0 });
                    break;
                }
                case "plants": value = PlantsIn(step, Request.Str(step, "template", null)).Count(); break;
                case "healthy":
                    value = PlantsIn(step, Request.Str(step, "template", null)).Count(r =>
                        r.GetComponent<LivingNaturalResource>()?.IsDead != true && r.GetComponent<DyingNaturalResource>()?.IsDying != true);
                    break;
                case "dying": value = PlantsIn(step, Request.Str(step, "template", null)).Count(r => r.GetComponent<DyingNaturalResource>()?.IsDying == true); break;
                case "dead": value = PlantsIn(step, Request.Str(step, "template", null)).Count(r => r.GetComponent<LivingNaturalResource>()?.IsDead == true); break;
                case "flowRate":
                {
                    string id = Request.Str(step, "id", null);
                    var mover = id != null && _objects.TryGetValue(id, out var bo) && bo ? bo.GetComponent<WaterMover>() : null;
                    value = mover != null && mover.CanMoveWater ? mover.EffectiveFlowRate : 0f;
                    break;
                }
                default: Harness.Warn("water lab: unknown expect '" + what + "'"); return;
            }
            bool pass = value >= min && value <= max;
            _checks.Add(new JObject { ["label"] = label, ["what"] = what, ["value"] = Math.Round(value, 4), ["min"] = min > float.MinValue ? (JToken)min : null,
                                      ["max"] = max < float.MaxValue ? (JToken)max : null, ["pass"] = pass, ["tick"] = _ticks });
            if (pass) Harness.Info("water check ok: " + label + " = " + Math.Round(value, 4));
            else Harness.Error("water check failed: " + label + " = " + Math.Round(value, 4) + " not in [" + min + ", " + max + "]");
        }

        // ------------------------------------------------------------------ pictures

        private void Shot(JObject step)
        {
            string name = Request.Str(step, "name", "water" + _ticks);
            string file = Path.Combine(Harness.OutputDir, name + ".png");
            try
            {
                var focusRel = step["focus"] as JArray ?? new JArray(8, 8, 0);
                var focus = CoordinateSystem.GridToWorld(new Vector3(_origin.x + (float)focusRel[0] + 0.5f, _origin.y + (float)focusRel[1] + 0.5f, _origin.z + (float)focusRel[2]));
                float distance = Request.Num(step, "distance", 22f);
                float pitch = Request.Num(step, "pitch", 50f), yaw = Request.Num(step, "yaw", 30f);
                var rotation = Quaternion.Euler(pitch, yaw, 0f);
                var position = focus - rotation * Vector3.forward * distance;
                var source = _cameraService.Transform ? _cameraService.Transform.GetComponent<Camera>() : Camera.main;
                RenderPose(source, (int)Request.Num(step, "width", 1280f), (int)Request.Num(step, "height", 720f), position, rotation, file);
                Harness.RecordScreenshot(name, "water", Path.GetFileName(file), new JObject { ["tick"] = _ticks, ["hours"] = Math.Round(Hours(), 2) }, null);
                Note("shot " + name);
            }
            catch (Exception e)
            {
                Harness.RecordScreenshot(name, "water", null, null, e.GetType().Name + ": " + e.Message);
                Harness.Warn("water lab: shot " + name + " failed: " + e.Message);
            }
        }

        private static void RenderPose(Camera source, int width, int height, Vector3 position, Quaternion rotation, string path)
        {
            var cameraObject = new GameObject("PandabornWaterLabCamera");
            var camera = cameraObject.AddComponent<Camera>();
            camera.enabled = false;
            if (source) camera.CopyFrom(source);
            camera.transform.SetPositionAndRotation(position, rotation);
            camera.farClipPlane = Mathf.Max(camera.farClipPlane, 400f);
            camera.aspect = width / (float)height;
            var target = RenderTexture.GetTemporary(width, height, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
            var texture = new Texture2D(width, height, TextureFormat.RGBA32, false);
            var previous = RenderTexture.active;
            try
            {
                camera.targetTexture = target;
                camera.Render();
                RenderTexture.active = target;
                texture.ReadPixels(new Rect(0, 0, width, height), 0, 0);
                texture.Apply(false);
                Directory.CreateDirectory(Path.GetDirectoryName(path));
                File.WriteAllBytes(path, ImageConversion.EncodeToPNG(texture));
            }
            finally
            {
                RenderTexture.active = previous;
                camera.targetTexture = null;
                RenderTexture.ReleaseTemporary(target);
                UnityEngine.Object.Destroy(cameraObject);
                UnityEngine.Object.Destroy(texture);
            }
        }

        // ------------------------------------------------------------------ helpers

        private static JArray Arr(Vector3Int v) => new JArray(v.x, v.y, v.z);

        private static double R(float v) => Math.Round(v, 4);
    }
}
