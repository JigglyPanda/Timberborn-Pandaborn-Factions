using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using Bindito.Core;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Timberborn.BlockObjectTools;
using Timberborn.BlockSystem;
using Timberborn.Buildings;
using Timberborn.ConstructionSites;
using Timberborn.Coordinates;
using Timberborn.EntitySystem;
using Timberborn.GameDistricts;
using Timberborn.MapIndexSystem;
using Timberborn.NaturalResources;
using Timberborn.SelectionSystem;
using Timberborn.SingletonSystem;
using Timberborn.TemplateSystem;
using Timberborn.TerrainSystem;
using Timberborn.UILayoutSystem;
using Timberborn.WaterSystem;
using UnityEngine;

namespace PandabornDevHarness
{
    [Context("Game")]
    public class GridLabConfigurator : Configurator
    {
        protected override void Configure()
        {
            if (!Harness.Active || !(Harness.Request?.Raw?["grid"] is JObject)) return;
            Bind<GridLab>().AsSingleton();
        }
    }

    /// <summary>
    /// Places every requested building template once, finishes it through the game's own construction code and opens its
    /// entity panel, reporting per template what worked. Used to prove that faction copies of buildings (e.g. the
    /// ".Inkpaws" copies of the Folktails buildings) behave exactly like their originals: run the same scenario for both
    /// factions on the same map and compare grid.json by "base" name. Active only when request.json has a "grid" object:
    /// <code>
    /// "grid": {
    ///   "templates": [ "LumberMill.Inkpaws", ... ],   // explicit list; or
    ///   "suffix": ".Folktails",                       // every PlaceableBlockObjectSpec of the current faction whose
    ///                                                 // template name ends with this ("" = all placeable templates)
    ///   "exclude": [ "Path", ... ],                   // template names (or names without the faction suffix) to skip
    ///   "area": [64, 64],                             // test area (shrunk to fit the map): dry, free of buildings, flat
    ///   "flatten": true,                              // and near the district center; flattened (plants removed);
    ///   "spacing": 1,                                 // buildings laid out in rows, "spacing" free tiles apart
    ///   "mode": "unfinishedThenFinish" | "finished",  // default: place as a construction site, then complete it with
    ///                                                 // ConstructionSite.FinishNow() (what dev mode's "Finish now" button
    ///                                                 // calls); "finished" = ConstructionFactory.CreateAsFinished.
    ///                                                 // Templates whose BuildingSpec.PlaceFinished is set are always placed
    ///                                                 // finished, as the game's BuildingPlacer does.
    ///   "select": true,                               // select each finished building once (its entity panel opens)
    ///   "perFrame": 1,                                // templates placed/finished per frame
    ///   "failOnError": true,                          // errors attributed to a template become harness errors (run fails)
    ///   "retry": true,                                // templates with no spot get a second map-wide search at the end,
    ///                                                 // also on top of placed objects (roof terraces, detonators, ...)
    ///   "startDelaySeconds": 2,                       // after the primary UI is shown
    ///   "finishWaitSeconds": 10,                      // real seconds a blocked site may take to report finished
    ///   "searchSeconds": 4,                           // per template and pass: real-time budget of the map-wide search
    ///   "areaTries": 400,                             // per template: game validity checks tried inside the area
    ///   "exercise": {                                 // after every template is done: run the finished-state and
    ///     "recipes": true,                            // working-state code (animation controllers, sound emitters,
    ///     "bots": 2,                                  // (bots spawned at the district centre: the faction's bot body)
    ///     "speeds": [1, 3, 0, 2, 3],                  // particles, progress visualisers): give every manufactory with
    ///     "everySeconds": 4,                          // no recipe its first one, then change the game speed through
    ///     "holdHours": 3                              // the list, one step every N real seconds, then let N in-game
    ///   }                                             // hours pass at the last speed (result "grid.exercise"); the run
    ///                                                 // does not end before (GameDriver waits for "exercise.done")
    /// }
    /// </code>
    /// Placement: candidates come from the test area first (rows, deterministic: largest footprint first, then name without
    /// the faction suffix, so a faction copy lands where its original did), then from the whole map (columns near water first,
    /// then by distance from the district center). Candidate z follows the building tool (BlockObjectPreviewPicker): ground
    /// minus BlockObjectSpec.BaseZ, one lower for all-underground objects, cliff sides for CanBeAttachedToTerrainSide; "Half"
    /// layouts (linked pairs such as the district crossing) are placed as the tool's two mirrored halves. Validity is the
    /// game's own (PreviewPlacer.GetBuildableCoordinates, as the building tool uses).
    /// Every Unity error/exception/assert logged while a template is placed, finished or selected (including the frames
    /// after each step) is attributed to it. Report: result.json "grid" (kept current every frame) and grid.json in the
    /// output folder; "complete" stays false if the harness ended first.
    /// </summary>
    public class GridLab : ILoadableSingleton, IUpdatableSingleton
    {
        private enum Phase { Waiting, Preparing, Settle, Processing, Done }

        private readonly EventBus _eventBus;
        private readonly TemplateService _templateService;
        private readonly PreviewPlacerFactory _previewPlacerFactory;
        private readonly ConstructionFactory _constructionFactory;
        private readonly BlockObjectPlacerService _blockObjectPlacerService;
        private readonly IBlockService _blockService;
        private readonly ITerrainService _terrainService;
        private readonly IThreadSafeWaterMap _waterMap;
        private readonly MapIndexService _mapIndexService;
        private readonly EntityService _entityService;
        private readonly DistrictCenterRegistry _districtCenterRegistry;
        private readonly EntitySelectionService _entitySelectionService;
        private readonly IBlockOccupancyService _blockOccupancyService;
        private readonly Timberborn.TimeSystem.SpeedManager _speedManager;
        private readonly EntityRegistry _entityRegistry;
        private readonly Timberborn.Bots.BotFactory _botFactory;

        private JObject _spec, _out, _summary;
        private JObject _exercise;
        private int _exerciseStep = -1;
        private float _exerciseAt, _holdFromHours = -1f;
        private readonly Timberborn.TimeSystem.IDayNightCycle _dayNightCycle;
        private JArray _items;
        private Phase _phase = Phase.Waiting;
        private float _primaryUiAt = -1f, _lastWrite;
        private int _settleFrames;
        private string _mode;
        private bool _select, _failOnError, _flatten, _retry, _retryStarted;
        private int _perFrame, _spacing, _areaTries;
        private float _finishWait, _searchSeconds;

        private readonly List<Item> _all = new List<Item>();
        private readonly Queue<Item> _pending = new Queue<Item>();
        private readonly List<Item> _deferred = new List<Item>();
        private List<Item> _batch;
        private int _batchStage, _selectIndex, _selectFrames;
        private float _batchStageAt;

        // area and map
        private Vector3Int _mapSize;
        private int _ax, _ay, _aw, _ah, _az;
        private bool[,] _reserved;
        private int _scanRow;
        private List<Vector2Int> _fallbackCells, _retryCells;   // retry = area columns first, then the map
        private int _areaCellCount;

        // log attribution
        private List<Item> _context = new List<Item>();
        private string _contextStep;
        private bool _suppressLog;
        private int _unattributed;
        private readonly JArray _unattributedSamples = new JArray();

        private class Item
        {
            public string Template, BaseName;
            public PlaceableBlockObjectSpec Spec;
            public BlockObjectSpec Blocks;
            public JObject Entry;
            public readonly List<BlockObject> Objects = new List<BlockObject>();
            public bool Placed, Unfinished, Failed, Deferred, DeleteOnFinish, Ended;
            public bool Half, AllUnderground, AttachToSide;
            public int Pass, BaseZ, FootprintArea;
            public List<Vector2Int>[] Footprints;   // per orientation, relative x/y offsets of every placement of the layout
            public int SearchIndex, FirstPassIndex;
            public float SearchSpent;
            public float FinishedAt = -1f;
            public PreviewPlacer Placer;            // one per template (each creates preview entities)
            public readonly JArray Errors = new JArray();
            public BlockObject Main => Objects.Count > 0 ? Objects[0] : null;
        }

        private static readonly Orientation[] Orientations = { Orientation.Cw0, Orientation.Cw90, Orientation.Cw180, Orientation.Cw270 };

        public GridLab(EventBus eventBus, TemplateService templateService, PreviewPlacerFactory previewPlacerFactory,
                       ConstructionFactory constructionFactory, BlockObjectPlacerService blockObjectPlacerService, IBlockService blockService,
                       ITerrainService terrainService, IThreadSafeWaterMap waterMap, MapIndexService mapIndexService, EntityService entityService,
                       DistrictCenterRegistry districtCenterRegistry, EntitySelectionService entitySelectionService,
                       IBlockOccupancyService blockOccupancyService, Timberborn.TimeSystem.SpeedManager speedManager,
                       EntityRegistry entityRegistry, Timberborn.TimeSystem.IDayNightCycle dayNightCycle,
                       Timberborn.Bots.BotFactory botFactory)
        {
            _botFactory = botFactory;
            _dayNightCycle = dayNightCycle;
            _speedManager = speedManager;
            _entityRegistry = entityRegistry;
            _eventBus = eventBus;
            _templateService = templateService;
            _previewPlacerFactory = previewPlacerFactory;
            _constructionFactory = constructionFactory;
            _blockObjectPlacerService = blockObjectPlacerService;
            _blockService = blockService;
            _terrainService = terrainService;
            _waterMap = waterMap;
            _mapIndexService = mapIndexService;
            _entityService = entityService;
            _districtCenterRegistry = districtCenterRegistry;
            _entitySelectionService = entitySelectionService;
            _blockOccupancyService = blockOccupancyService;
        }

        public void Load()
        {
            _spec = (JObject)Harness.Request.Raw["grid"];
            _mode = Request.Str(_spec, "mode", "unfinishedThenFinish");
            _select = Request.Bool(_spec, "select", true);
            _failOnError = Request.Bool(_spec, "failOnError", true);
            _flatten = Request.Bool(_spec, "flatten", true);
            _retry = Request.Bool(_spec, "retry", true);
            _perFrame = Math.Max(1, (int)Request.Num(_spec, "perFrame", 1f));
            _spacing = Math.Max(0, (int)Request.Num(_spec, "spacing", 1f));
            _areaTries = Math.Max(1, (int)Request.Num(_spec, "areaTries", 400f));
            _finishWait = Request.Num(_spec, "finishWaitSeconds", 10f);
            _searchSeconds = Request.Num(_spec, "searchSeconds", 4f);
            _items = new JArray();
            _summary = new JObject();
            _out = new JObject
            {
                ["status"] = "waiting", ["complete"] = false, ["mode"] = _mode, ["select"] = _select,
                ["spec"] = _spec.DeepClone(), ["summary"] = _summary, ["items"] = _items
            };
            Harness.Result["grid"] = _out;
            _eventBus.Register(this);
            Harness.Info("grid lab loaded: mode " + _mode);
        }

        [OnEvent]
        public void OnShowPrimaryUI(ShowPrimaryUIEvent showPrimaryUIEvent)
        {
            if (_primaryUiAt < 0f) _primaryUiAt = Time.unscaledTime;
        }

        public void UpdateSingleton()
        {
            if (Harness.Finished)
            {
                if (_phase != Phase.Done)
                {
                    _out["status"] = "incomplete: the harness finished first (phase " + _phase + ", " + _pending.Count + " template(s) not started)";
                    _phase = Phase.Done;
                    Detach();
                    RefreshSummary();
                    WriteGridJson();
                }
                return;
            }
            if (_phase == Phase.Done)
            {
                try { Exercise(); }
                catch (Exception e) { Harness.Error("grid exercise failed", e); _exerciseStep = int.MaxValue; }
                RefreshSummary();   // keeps "alive" current until the harness ends
                if (Time.unscaledTime - _lastWrite > 2f) WriteGridJson();
                return;
            }
            try { Step(); }
            catch (Exception e)
            {
                ClearContext();
                Harness.Error("grid lab failed in phase " + _phase, e);
                _out["status"] = "error: " + e.GetType().Name + ": " + e.Message;
                _phase = Phase.Done;
                Detach();
                RefreshSummary();
                WriteGridJson();
            }
        }

        private void Step()
        {
            float now = Time.unscaledTime;
            switch (_phase)
            {
                case Phase.Waiting:
                    if (_primaryUiAt < 0f || now - _primaryUiAt < Request.Num(_spec, "startDelaySeconds", 2f)) return;
                    _phase = Phase.Preparing;
                    return;

                case Phase.Preparing:
                    Application.logMessageReceived += OnLog;
                    _out["status"] = "running";
                    _out["startedRealSeconds"] = Math.Round(now, 1);
                    CollectTemplates();
                    PrepareArea();
                    _phase = Phase.Settle;
                    _settleFrames = 3;
                    RefreshSummary();
                    WriteGridJson();
                    return;

                case Phase.Settle:
                    if (--_settleFrames > 0) return;
                    _phase = Phase.Processing;
                    return;

                case Phase.Processing:
                    Process(now);
                    if (_phase != Phase.Processing) return;
                    RefreshSummary();   // cheap; keeps result.json current whenever the harness finishes
                    if (now - _lastWrite > 3f) WriteGridJson();
                    return;
            }
        }

        // ------------------------------------------------------------------ templates

        private void CollectTemplates()
        {
            var specs = _templateService.GetAll<PlaceableBlockObjectSpec>().ToList();
            var exclude = new HashSet<string>((_spec["exclude"] as JArray)?.Select(t => (string)t) ?? Enumerable.Empty<string>());
            var wanted = new List<string>();
            string suffix = null;
            if (_spec["templates"] is JArray list) wanted.AddRange(list.Select(t => (string)t));
            else
            {
                suffix = Request.Str(_spec, "suffix", "");
                wanted.AddRange(specs.Select(TemplateName).Where(n => n != null && n.EndsWith(suffix, StringComparison.Ordinal)).Distinct());
            }
            var items = new List<Item>();
            foreach (var name in wanted.Distinct())
            {
                string baseName = StripSuffix(name);
                if (exclude.Contains(name) || exclude.Contains(baseName)) continue;
                var item = new Item { Template = name, BaseName = baseName };
                item.Entry = new JObject { ["template"] = name, ["base"] = baseName, ["placed"] = false, ["finished"] = false };
                item.Spec = specs.FirstOrDefault(s => TemplateName(s) == name)
                            ?? specs.FirstOrDefault(s => s.GetSpec<TemplateSpec>()?.IsNamed(name) == true);
                if (item.Spec == null) { item.Entry["reason"] = "template not available to this faction"; item.Failed = true; }
                else
                {
                    item.Blocks = item.Spec.GetSpec<BlockObjectSpec>();
                    item.Half = item.Spec.Layout == BlockObjectLayout.Half;
                    item.BaseZ = item.Blocks?.BaseZ ?? 0;
                    item.AllUnderground = item.Blocks != null && item.Blocks.Blocks.Length > 0 && item.Blocks.Blocks.All(b => b.Underground);
                    item.AttachToSide = item.Spec.CanBeAttachedToTerrainSide;
                    item.Entry["building"] = item.Spec.HasSpec<BuildingSpec>();
                    item.Entry["devOnly"] = item.Spec.DevModeTool;
                    item.Entry["toolGroup"] = item.Spec.ToolGroupId;
                    if (item.Spec.Layout != BlockObjectLayout.Single) item.Entry["layout"] = item.Spec.Layout.ToString();
                    if (item.BaseZ != 0) item.Entry["baseZ"] = item.BaseZ;
                    if (item.Blocks != null) item.Entry["size"] = new JArray(item.Blocks.Size.x, item.Blocks.Size.y, item.Blocks.Size.z);
                    item.Footprints = Orientations.Select(o => Footprint(item, o)).ToArray();
                    item.FootprintArea = item.Footprints[0].Count;
                    if (item.Spec.GetSpec<TemplateSpec>()?.UsableWithCurrentFeatureToggles == false)
                    {
                        item.Entry["reason"] = "disabled by the current feature toggles";
                        item.Failed = true;
                    }
                }
                items.Add(item);
            }
            // deterministic layout: largest footprint first, then by name without the faction suffix
            foreach (var item in items.OrderByDescending(i => i.FootprintArea).ThenBy(i => i.BaseName, StringComparer.Ordinal).ThenBy(i => i.Template, StringComparer.Ordinal))
            {
                _all.Add(item);
                _items.Add(item.Entry);
                if (!item.Failed) _pending.Enqueue(item);
            }
            _out["suffix"] = suffix;
            _out["requested"] = _all.Count;
            Harness.Info("grid: " + _all.Count + " template(s), " + _pending.Count + " to place");
        }

        private static string TemplateName(PlaceableBlockObjectSpec spec)
        {
            return spec.GetSpec<TemplateSpec>()?.TemplateName ?? spec.Blueprint?.Name;
        }

        private static string StripSuffix(string name)
        {
            int dot = name.LastIndexOf('.');
            return dot > 0 ? name.Substring(0, dot) : name;
        }

        /// <summary>The placements the building tool makes for one click: one, or two mirrored halves (AreaPicker.HalvesCoordinates).</summary>
        private static List<Placement> Placements(Item item, Vector3Int at, Orientation orientation)
        {
            var list = new List<Placement> { new Placement(at, orientation, FlipMode.Unflipped) };
            if (item.Half && item.Blocks != null)
            {
                var size = item.Blocks.Size;
                list.Add(new Placement(at + orientation.Transform(new Vector3Int(size.x - 1, size.y * 2 - 1, 0)), orientation.Flip(), FlipMode.Unflipped));
            }
            return list;
        }

        private static List<Vector2Int> Footprint(Item item, Orientation orientation)
        {
            var set = new HashSet<Vector2Int>();
            if (item.Blocks != null)
                foreach (var placement in Placements(item, Vector3Int.zero, orientation))
                    foreach (var block in item.Blocks.GetBlocks(placement))
                        set.Add(new Vector2Int(block.Coordinates.x, block.Coordinates.y));
            if (set.Count == 0) set.Add(Vector2Int.zero);
            return set.ToList();
        }

        // ------------------------------------------------------------------ area

        private int Surface(int x, int y) => _terrainService.GetTerrainHeightBelow(new Vector3Int(x, y, _mapSize.z - 1));

        private bool HasBuilding(Vector3Int cell)
        {
            if (!_blockService.Contains(cell)) return false;
            foreach (var bo in _blockService.GetObjectsAt(cell))
                if (bo && bo.GetComponent<NaturalResource>() == null) return true;
            return false;
        }

        private void PrepareArea()
        {
            _mapSize = _terrainService.Size;
            int sx = _mapSize.x, sy = _mapSize.y;
            var dc = _districtCenterRegistry.AllDistrictCenters.FirstOrDefault();
            var anchor = dc != null ? new Vector2Int(dc.CenterCoordinates.x, dc.CenterCoordinates.y) : new Vector2Int(sx / 2, sy / 2);
            int anchorZ = dc != null ? dc.CenterCoordinates.z : Surface(anchor.x, anchor.y);
            var sw = Stopwatch.StartNew();

            // per-column facts, then prefix sums so every candidate rectangle is O(1)
            int W = sx + 1;
            var blocked = new long[W * (sy + 1)];
            var sumH = new long[W * (sy + 1)];
            var sumH2 = new long[W * (sy + 1)];
            var water = new bool[sx, sy];
            var nearWater = new bool[sx, sy];
            for (int x = 0; x < sx; x++)
                for (int y = 0; y < sy; y++)
                    water[x, y] = _waterMap.IsWaterOnAnyHeight(new Vector2Int(x, y));
            for (int y = 0; y < sy; y++)
                for (int x = 0; x < sx; x++)
                {
                    int s = Surface(x, y);
                    bool b = water[x, y] || _terrainService.GetColumnCount(_mapIndexService.CellToIndex(new Vector2Int(x, y))) > 1;
                    for (int z = s - 1; z <= s + 1 && !b; z++) b = HasBuilding(new Vector3Int(x, y, z));
                    for (int dx = -2; dx <= 2 && !nearWater[x, y]; dx++)
                        for (int dy = -2; dy <= 2; dy++)
                            if (x + dx >= 0 && y + dy >= 0 && x + dx < sx && y + dy < sy && water[x + dx, y + dy]) { nearWater[x, y] = true; break; }
                    int i = (x + 1) + (y + 1) * W;
                    blocked[i] = (b ? 1 : 0) + blocked[i - 1] + blocked[i - W] - blocked[i - 1 - W];
                    sumH[i] = s + sumH[i - 1] + sumH[i - W] - sumH[i - 1 - W];
                    sumH2[i] = (long)s * s + sumH2[i - 1] + sumH2[i - W] - sumH2[i - 1 - W];
                }
            long Rect(long[] p, int x0, int y0, int x1, int y1)   // inclusive
                => p[(x1 + 1) + (y1 + 1) * W] - p[x0 + (y1 + 1) * W] - p[(x1 + 1) + y0 * W] + p[x0 + y0 * W];

            var areaSpec = _spec["area"] as JArray;
            int wantW = areaSpec != null ? (int)areaSpec[0] : 64, wantH = areaSpec != null && areaSpec.Count > 1 ? (int)areaSpec[1] : wantW;
            const int margin = 3;
            bool found = false;
            int w = Math.Min(wantW, sx - 2 * margin - 2), h = Math.Min(wantH, sy - 2 * margin - 2);
            for (; !found && w >= 8 && h >= 8; w -= 4, h -= 4)
            {
                double bestScore = double.MaxValue;
                long n = (long)w * h;
                for (int cx = margin + 1; cx + w + margin < sx; cx++)
                    for (int cy = margin + 1; cy + h + margin < sy; cy++)
                    {
                        if (Rect(blocked, cx - margin, cy - margin, cx + w - 1 + margin, cy + h - 1 + margin) > 0) continue;
                        double sum = Rect(sumH, cx, cy, cx + w - 1, cy + h - 1);
                        double mean = sum / n;
                        int target = Math.Abs(mean - anchorZ) <= 2.0 ? anchorZ : (int)Math.Round(mean);
                        double sq = Rect(sumH2, cx, cy, cx + w - 1, cy + h - 1) - 2.0 * target * sum + (double)n * target * target;
                        double dist = Vector2.Distance(new Vector2(cx + w / 2f, cy + h / 2f), anchor);
                        double score = (_flatten ? sq / n * 20.0 : sq * 1000.0) + dist;
                        if (score < bestScore) { bestScore = score; _ax = cx; _ay = cy; _az = target; found = true; }
                    }
                if (found) { _aw = w; _ah = h; _out["areaScore"] = Math.Round(bestScore, 2); }
            }
            _out["mapSize"] = new JArray(sx, sy, _mapSize.z);
            if (dc != null) _out["districtCenter"] = new JArray(dc.CenterCoordinates.x, dc.CenterCoordinates.y, dc.CenterCoordinates.z);
            if (!found)
            {
                _aw = _ah = 0;
                _out["area"] = null;
                Harness.Warn("grid: no dry, building-free area of at least 8x8 on this map; every template uses the map-wide search");
            }
            else
            {
                _out["area"] = new JObject { ["corner"] = new JArray(_ax, _ay, _az), ["size"] = new JArray(_aw, _ah) };
                if (_aw < wantW || _ah < wantH) Harness.Warn("grid: area shrunk to " + _aw + "x" + _ah + " to fit the map");
                if (_flatten) Flatten();
            }
            _reserved = new bool[Math.Max(1, _aw), Math.Max(1, _ah)];

            // map-wide candidates: columns near water first, then by distance from the district center
            _fallbackCells = new List<Vector2Int>();
            for (int x = 0; x < sx; x++)
                for (int y = 0; y < sy; y++)
                {
                    if (found && x >= _ax - 1 && x <= _ax + _aw && y >= _ay - 1 && y <= _ay + _ah) continue;
                    _fallbackCells.Add(new Vector2Int(x, y));
                }
            _fallbackCells = _fallbackCells.OrderBy(c => nearWater[c.x, c.y] ? 0 : 1).ThenBy(c => (c - anchor).sqrMagnitude).ThenBy(c => c.x).ThenBy(c => c.y).ToList();
            var areaCells = new List<Vector2Int>();
            for (int y = _ay; y < _ay + _ah; y++)
                for (int x = _ax; x < _ax + _aw; x++)
                    areaCells.Add(new Vector2Int(x, y));
            _areaCellCount = areaCells.Count;
            _retryCells = areaCells.Concat(_fallbackCells).ToList();
            _out["prepareMs"] = sw.ElapsedMilliseconds;
            Harness.Info("grid: area " + (found ? "[" + _ax + "," + _ay + "] " + _aw + "x" + _ah + " at z" + _az : "none") + " on map " + sx + "x" + sy
                         + ", prepared in " + sw.ElapsedMilliseconds + " ms");
        }

        private void Flatten()
        {
            int changed = 0, removed = 0;
            for (int x = _ax; x < _ax + _aw; x++)
                for (int y = _ay; y < _ay + _ah; y++)
                {
                    int s = Surface(x, y);
                    for (int z = Math.Min(s, _az) - 1; z <= Math.Max(s, _az) + 3; z++)
                    {
                        var cell = new Vector3Int(x, y, z);
                        if (!_blockService.Contains(cell)) continue;
                        foreach (var bo in _blockService.GetObjectsAt(cell).ToList())
                            if (bo && bo.GetComponent<NaturalResource>() != null) { _entityService.Delete(bo); removed++; }
                    }
                    if (s < _az) { _terrainService.SetTerrain(new Vector3Int(x, y, s), _az - s); changed++; }
                    else if (s > _az) { _terrainService.UnsetTerrain(new Vector3Int(x, y, s - 1), s - _az); changed++; }
                }
            _out["flattened"] = new JObject { ["columnsChanged"] = changed, ["plantsRemoved"] = removed };
            Harness.Info("grid: flattened area to z" + _az + ": " + changed + " columns changed, " + removed + " plants removed");
        }

        // ------------------------------------------------------------------ processing

        private void Process(float now)
        {
            if (_batch == null)
            {
                if (_pending.Count == 0 && _deferred.Count > 0 && !_retryStarted)
                {
                    _retryStarted = true;
                    Harness.Info("grid: second pass for " + _deferred.Count + " template(s) without a spot");
                    foreach (var item in _deferred) { item.Deferred = false; item.Pass = 1; item.SearchIndex = 0; item.SearchSpent = 0f; _pending.Enqueue(item); }
                    _deferred.Clear();
                }
                if (_pending.Count == 0) { Complete(); return; }
                _batch = new List<Item>();
                while (_batch.Count < _perFrame && _pending.Count > 0) _batch.Add(_pending.Dequeue());
                _batchStage = 0;
                _batchStageAt = now;
            }
            switch (_batchStage)
            {
                case 0:   // place: inside the area, or (incrementally, time-boxed) anywhere on the map
                {
                    bool searching = false;
                    foreach (var item in _batch)
                    {
                        if (item.Placed || item.Failed || item.Deferred) continue;
                        SetContext(item, "place");
                        try
                        {
                            List<Placement> placements = null;
                            if (item.Pass == 0 && item.SearchIndex == 0 && item.SearchSpent == 0f) placements = FindInArea(item);
                            if (placements == null) placements = SearchMap(item, out searching);
                            if (placements != null) Place(item, placements);
                            else if (!searching)
                            {
                                if (item.Pass == 0 && _retry)
                                {
                                    item.Deferred = true;
                                    item.FirstPassIndex = item.SearchIndex;
                                    item.Entry["firstPass"] = "no valid spot (" + item.Entry["searched"] + ")";
                                    _deferred.Add(item);
                                }
                                else NotPlaced(item, "no valid spot found (" + item.Entry["searched"] + ")");
                            }
                        }
                        catch (Exception e)
                        {
                            RecordException(item, "place", e);
                            item.Failed = true;
                            item.Entry["reason"] = "exception while placing: " + e.GetType().Name + ": " + e.Message;
                        }
                        finally { ClearContext(); }
                        if (searching) break;   // one map search at a time
                    }
                    if (searching) return;
                    _batchStage = 1;
                    _batchStageAt = now;
                    SetContext(_batch.Where(i => i.Placed).ToList(), "place");   // errors from the frame after placing
                    return;
                }
                case 1:   // finish construction sites through the game's own completion path
                    ClearContext();
                    foreach (var item in _batch.Where(i => i.Placed && i.Unfinished))
                    {
                        SetContext(item, "finish");
                        try
                        {
                            foreach (var bo in item.Objects)
                            {
                                var site = bo ? bo.GetComponent<ConstructionSite>() : null;
                                if (site == null) item.Entry["finishNote"] = "no ConstructionSite component";
                                else if (bo.IsUnfinished) site.FinishNow();
                            }
                        }
                        catch (Exception e) { RecordException(item, "finish", e); }
                        finally { ClearContext(); }
                    }
                    _batchStage = 2;
                    _batchStageAt = now;
                    SetContext(_batch.Where(i => i.Placed).ToList(), "finish");
                    return;
                case 2:   // verify with the game's own state; blocked sites get a few real seconds of ticks
                {
                    bool waiting = false;
                    foreach (var item in _batch.Where(i => i.Placed && i.FinishedAt < 0f))
                    {
                        if (item.Objects.All(bo => !bo || bo.IsFinished))
                        {
                            item.FinishedAt = now;
                            item.Entry["finishSeconds"] = Math.Round(now - _batchStageAt, 2);
                        }
                        else waiting = true;
                    }
                    if (waiting && now - _batchStageAt < _finishWait) return;
                    ClearContext();
                    foreach (var item in _batch.Where(i => i.Placed))
                    {
                        bool gone = item.Objects.Any(bo => !bo);
                        bool finished = item.Objects.All(bo => !bo || bo.IsFinished);
                        if (gone)
                        {
                            // tunnels and ground raisers delete themselves on finishing (DeleteOnFinishConstructionSite)
                            item.Entry["finishNote"] = item.DeleteOnFinish ? "deleted itself on finishing (DeleteOnFinishConstructionSite)" : "entity gone after finishing";
                            finished = finished && item.DeleteOnFinish;
                        }
                        item.Entry["finished"] = finished;
                        if (!finished) DescribeUnfinished(item);
                    }
                    _batchStage = 3;
                    _selectIndex = 0;
                    _selectFrames = 0;
                    return;
                }
                case 3:   // open each finished building's entity panel once
                    if (_select && StepSelect()) return;
                    ClearContext();
                    foreach (var item in _batch) EndItem(item);
                    _batch = null;
                    return;
            }
        }

        /// <summary>Selects one finished item per call, keeps it selected for two more frames, then unselects. True while busy.</summary>
        private bool StepSelect()
        {
            var finished = _batch.Where(i => i.Placed && i.Main && i.Main.IsFinished).ToList();
            if (_selectIndex >= finished.Count) return false;
            var item = finished[_selectIndex];
            if (_selectFrames == 0)
            {
                SetContext(item, "select");
                try
                {
                    _entitySelectionService.Select(item.Main);
                    var selected = _entitySelectionService.SelectedObject;
                    item.Entry["selected"] = _entitySelectionService.IsAnythingSelected && selected && selected.GameObject == item.Main.GameObject;
                }
                catch (Exception e) { RecordException(item, "select", e); item.Entry["selected"] = false; }
                _selectFrames = 1;
                return true;
            }
            if (_selectFrames < 3) { _selectFrames++; return true; }   // the panel updates its fragments in later frames
            try { _entitySelectionService.Unselect(); }
            catch (Exception e) { RecordException(item, "unselect", e); }
            ClearContext();
            _selectFrames = 0;
            _selectIndex++;
            return true;
        }

        private PreviewPlacer PlacerFor(Item item) => item.Placer ?? (item.Placer = _previewPlacerFactory.Create(item.Spec));

        /// <summary>The game's own validity check for the tool's placements at this spot; null when not all are buildable.</summary>
        private List<Placement> Valid(Item item, Vector3Int at, Orientation orientation)
        {
            var wanted = Placements(item, at, orientation);
            var buildable = PlacerFor(item).GetBuildableCoordinates(wanted).ToList();
            return buildable.Count == wanted.Count ? buildable : null;
        }

        private List<Placement> FindInArea(Item item)
        {
            if (_aw == 0) return null;
            int tries = 0;
            int z = _az - item.BaseZ - (item.AllUnderground ? 1 : 0);
            try
            {
                for (int y = _scanRow; y < _ah; y++)
                    for (int x = 0; x < _aw; x++)
                        for (int o = 0; o < 4; o++)
                        {
                            if (!FitsReserved(item.Footprints[o], x, y)) continue;
                            if (++tries > _areaTries) { item.Entry["areaTries"] = tries - 1; return null; }
                            var at = new Vector3Int(_ax + x, _ay + y, z);
                            var p = Valid(item, at, Orientations[o]);
                            if (p != null) { item.Entry["where"] = "area"; item.Entry["areaTries"] = tries; return p; }
                            if (tries <= 2) Diagnose(item, at, Orientations[o]);
                        }
                item.Entry["areaTries"] = tries;
                return null;
            }
            finally { PlacerFor(item).HideAllPreviews(); }
        }

        /// <summary>Why the game rejected an area spot: its warning text (if any) and what occupies the footprint.</summary>
        private void Diagnose(Item item, Vector3Int at, Orientation orientation)
        {
            var d = new JObject { ["at"] = new JArray(at.x - _ax, at.y - _ay, at.z - _az), ["orientation"] = orientation.ToString() };
            try
            {
                var placer = PlacerFor(item);
                placer.ShowPreviews(Placements(item, at, orientation));
                d["warning"] = placer.WarningText;
                placer.HideAllPreviews();
                var objects = new HashSet<string>();
                int minS = int.MaxValue, maxS = int.MinValue;
                foreach (var p in Placements(item, at, orientation))
                    foreach (var block in item.Blocks.GetBlocks(p))
                    {
                        var c = block.Coordinates;
                        int s = Surface(c.x, c.y);
                        minS = Math.Min(minS, s); maxS = Math.Max(maxS, s);
                        if (_waterMap.IsWaterOnAnyHeight(new Vector2Int(c.x, c.y))) objects.Add("water");
                        for (int z = c.z - 1; z <= c.z; z++)
                        {
                            var cell = new Vector3Int(c.x, c.y, z);
                            if (!_blockService.Contains(cell)) continue;
                            foreach (var bo in _blockService.GetObjectsAt(cell))
                                if (bo) objects.Add((bo.GetComponent<TemplateSpec>()?.TemplateName ?? bo.Name) + (bo.IsPreview ? " (preview)" : bo.IsUnfinished ? " (unfinished)" : ""));
                        }
                    }
                d["surface"] = new JArray(minS - _az, maxS - _az);
                d["objects"] = new JArray(objects.Cast<object>().ToArray());
            }
            catch (Exception e) { d["error"] = e.GetType().Name + ": " + e.Message; }
            if (!(item.Entry["areaRejects"] is JArray list)) item.Entry["areaRejects"] = list = new JArray();
            list.Add(d);
        }

        private bool FitsReserved(List<Vector2Int> footprint, int x, int y)
        {
            foreach (var f in footprint)
            {
                int fx = x + f.x, fy = y + f.y;
                if (fx < 0 || fy < 0 || fx >= _aw || fy >= _ah || _reserved[fx, fy]) return false;
            }
            return true;
        }

        private void Reserve(BlockObject bo)
        {
            if (_aw == 0 || !bo || !bo.Positioned) return;
            foreach (var c in bo.PositionedBlocks.GetAllCoordinates())
                for (int dx = -_spacing; dx <= _spacing; dx++)
                    for (int dy = -_spacing; dy <= _spacing; dy++)
                        Mark(c.x - _ax + dx, c.y - _ay + dy);
            if (bo.HasEntrance)
            {
                var d = bo.PositionedEntrance.DoorstepCoordinates;
                Mark(d.x - _ax, d.y - _ay);
            }
            while (_scanRow < _ah && Enumerable.Range(0, _aw).All(x => _reserved[x, _scanRow])) _scanRow++;
        }

        private void Mark(int x, int y)
        {
            if (x >= 0 && y >= 0 && x < _aw && y < _ah) _reserved[x, y] = true;
        }

        /// <summary>
        /// Candidate z levels in one column, as the building tool would pick them: ground minus BaseZ; one lower for
        /// all-underground objects; cliff sides for objects attachable to terrain sides; in the second pass also the top of
        /// whatever stands there (roofs, platforms, dynamite).
        /// </summary>
        private IEnumerable<int> CandidateZ(Item item, int x, int y, bool onlyNew)
        {
            int s = Surface(x, y);
            var zs = new List<int>();
            if (onlyNew)
            {
                // this column's ground levels were tried in the first pass; retry only where something was built since
                // (on top of it, and the ground again for objects that sit on underground ones, e.g. a detonator on dynamite)
                int topOnly = -1;
                for (int z = Math.Max(0, s - 2); z < s + 16 && z < _mapSize.z; z++) if (HasBuilding(new Vector3Int(x, y, z))) topOnly = z;
                if (topOnly < 0) return Array.Empty<int>();
                return new[] { s, topOnly + 1 }.Distinct().Select(z => z - item.BaseZ);
            }
            zs.Add(s);
            if (item.AllUnderground) zs.Add(s - 1);
            if (item.AttachToSide)
            {
                int max = s;
                foreach (var d in new[] { new Vector2Int(1, 0), new Vector2Int(-1, 0), new Vector2Int(0, 1), new Vector2Int(0, -1) })
                    if (_terrainService.Contains(new Vector2Int(x + d.x, y + d.y))) max = Math.Max(max, Surface(x + d.x, y + d.y));
                for (int z = s + 1; z < max && z < s + 8; z++) zs.Add(z);
            }
            if (item.Pass > 0)
            {
                int top = -1;
                for (int z = Math.Max(0, s - 2); z < s + 16 && z < _mapSize.z; z++) if (HasBuilding(new Vector3Int(x, y, z))) top = z;
                if (top >= 0) zs.Add(top + 1);
            }
            return zs.Distinct().Select(z => z - item.BaseZ);
        }

        /// <summary>Map-wide search, time-boxed per frame (12 ms) and per template and pass (searchSeconds).</summary>
        private List<Placement> SearchMap(Item item, out bool searching)
        {
            searching = false;
            var sw = Stopwatch.StartNew();
            try
            {
                var cells = item.Pass == 0 ? _fallbackCells : _retryCells;
                // second pass: columns already tried on the ground (the area, and the map up to where the first pass got)
                // only get the new candidate on top of whatever stands there
                int triedUpTo = item.Pass == 0 ? 0 : _areaCellCount + item.FirstPassIndex;
                while (item.SearchIndex < cells.Count)
                {
                    var c = cells[item.SearchIndex++];
                    foreach (int z in CandidateZ(item, c.x, c.y, item.SearchIndex <= triedUpTo))
                        foreach (var o in Orientations)
                        {
                            var p = Valid(item, new Vector3Int(c.x, c.y, z), o);
                            if (p != null)
                            {
                                item.SearchSpent += sw.ElapsedMilliseconds / 1000f;
                                bool inArea = _aw > 0 && c.x >= _ax && c.x < _ax + _aw && c.y >= _ay && c.y < _ay + _ah;
                                item.Entry["where"] = (inArea ? "area" : "map") + (item.Pass == 0 ? "" : ", second pass");
                                item.Entry["searched"] = item.SearchIndex + " of " + cells.Count + " columns";
                                return p;
                            }
                        }
                    if (sw.ElapsedMilliseconds > 12)
                    {
                        item.SearchSpent += sw.ElapsedMilliseconds / 1000f;
                        if (item.SearchSpent < _searchSeconds) { searching = true; return null; }
                        item.Entry["searched"] = item.SearchIndex + " of " + cells.Count + " columns in " + Math.Round(item.SearchSpent, 1) + " s, time budget used up";
                        return null;
                    }
                }
                item.SearchSpent += sw.ElapsedMilliseconds / 1000f;
                item.Entry["searched"] = "all " + cells.Count + " columns in " + Math.Round(item.SearchSpent, 1) + " s";
                return null;
            }
            finally { PlacerFor(item).HideAllPreviews(); }
        }

        private void Place(Item item, List<Placement> placements)
        {
            var building = item.Spec.GetSpec<BuildingSpec>();
            bool finished = building == null || _mode == "finished" || building.PlaceFinished;
            if (building != null && building.PlaceFinished) item.Entry["placeFinishedBySpec"] = true;
            item.Unfinished = !finished;
            foreach (var placement in placements)
            {
                var builder = new EntitySetup.Builder(item.Spec.Blueprint);
                BlockObject bo;
                if (building != null)
                    bo = finished ? _constructionFactory.CreateAsFinished(builder, placement) : _constructionFactory.CreateAsUnfinished(builder, placement);
                else
                {
                    _blockObjectPlacerService.GetMatchingPlacer(item.Blocks).Place(builder, placement);
                    bo = _blockService.GetObjectsAt(placement.Coordinates).FirstOrDefault(o => o && o.GetComponent<TemplateSpec>()?.TemplateName == item.Template);
                }
                item.Objects.Add(bo);
            }
            item.Placed = item.Objects.Count > 0 && item.Objects.All(bo => bo);
            item.Entry["placed"] = item.Placed;
            var c = placements[0].Coordinates;
            item.Entry["coordinates"] = new JArray(c.x, c.y, c.z);
            if (_aw > 0) item.Entry["areaOffset"] = new JArray(c.x - _ax, c.y - _ay, c.z - _az);
            item.Entry["orientation"] = placements[0].Orientation.ToString();
            if (placements.Count > 1)
                item.Entry["linked"] = new JArray(placements.Skip(1).Select(p => (object)new JArray(p.Coordinates.x, p.Coordinates.y, p.Coordinates.z, p.Orientation.ToString())).ToArray());
            if (!item.Placed) { item.Entry["reason"] = "the game created no entity"; return; }
            item.Entry["unfinishedAfterPlacing"] = item.Main.IsUnfinished;
            item.DeleteOnFinish = item.Main.GetComponent<DeleteOnFinishConstructionSite>() != null;
            if (item.DeleteOnFinish) item.Entry["deleteOnFinish"] = true;
            foreach (var bo in item.Objects) Reserve(bo);
        }

        private void NotPlaced(Item item, string reason)
        {
            item.Failed = true;
            item.Entry["reason"] = reason;
            // the game's own explanation for a typical rejected spot (what the building tool shows), when it has one
            try
            {
                var placer = PlacerFor(item);
                try
                {
                    // the first map spots (by the shore, near the district center) until one gives a message
                    foreach (var c in _fallbackCells.Take(300))
                    {
                        placer.ShowPreviews(Placements(item, new Vector3Int(c.x, c.y, Surface(c.x, c.y) - item.BaseZ), Orientation.Cw0));
                        if (string.IsNullOrEmpty(placer.WarningText)) continue;
                        item.Entry["gameWarning"] = placer.WarningText;
                        break;
                    }
                }
                finally { placer.HideAllPreviews(); }
            }
            catch (Exception) { }
        }

        private void DescribeUnfinished(Item item)
        {
            var sites = new JArray();
            foreach (var bo in item.Objects)
            {
                if (!bo) { sites.Add(null); continue; }
                var site = bo.GetComponent<ConstructionSite>();
                if (site == null) { sites.Add(new JObject { ["isFinished"] = bo.IsFinished, ["constructionSite"] = false }); continue; }
                sites.Add(new JObject
                {
                    ["isFinished"] = bo.IsFinished, ["isOn"] = site.IsOn, ["inventoryFull"] = site.Inventory?.IsFull,
                    ["buildTimeProgress"] = Math.Round(site.BuildTimeProgress, 3), ["readyToFinish"] = site.IsReadyToFinish,
                    ["occupantOnSite"] = _blockOccupancyService.OccupantPresentOnArea(bo, 0f),
                    ["finishBlocked"] = bo.GetComponent<IConstructionFinishBlocker>()?.IsFinishBlocked
                });
            }
            item.Entry["sites"] = sites;
        }

        private void EndItem(Item item)
        {
            if (item.Deferred) return;   // comes back in the second pass
            item.Ended = true;
            if (item.Errors.Count > 0) item.Entry["errors"] = item.Errors;
            if (item.Placed && (bool?)item.Entry["finished"] != true && item.Entry["reason"] == null)
            {
                item.Entry["reason"] = "placed but not finished";
                Harness.Warn("grid: " + item.Template + " placed but not finished: " + item.Entry["sites"]?.ToString(Formatting.None));
            }
            if (_failOnError && item.Errors.Count > 0)
            {
                var first = (JObject)item.Errors[0];
                _suppressLog = true;
                try { Harness.Error("grid: " + item.Template + ": " + item.Errors.Count + " error(s), first during " + first["step"] + ": " + first["message"]); }
                finally { _suppressLog = false; }
            }
            Harness.Info("grid: " + item.Template + " placed=" + item.Entry["placed"] + " finished=" + item.Entry["finished"]
                         + (item.Entry["where"] != null ? " (" + item.Entry["where"] + ")" : "")
                         + (item.Entry["reason"] != null ? " reason: " + item.Entry["reason"] : "") + (item.Errors.Count > 0 ? " errors=" + item.Errors.Count : ""));
        }

        private void Complete()
        {
            Detach();
            _phase = Phase.Done;
            _out["status"] = "completed";
            _out["completedRealSeconds"] = Math.Round(Time.unscaledTime, 1);
            _out["realSeconds"] = Math.Round(Time.unscaledTime - (float)_out["startedRealSeconds"], 1);
            RefreshSummary();
            WriteGridJson();
            Harness.Info("grid complete: " + _summary.ToString(Formatting.None));
        }

        // ------------------------------------------------------------------ exercise
        /// <summary>After the grid: recipes on, then a speed ladder, so code that only runs on finished, working buildings
        /// runs (both crashes of 2026-11-14 were there). Errors land in the harness log and fail the run.</summary>
        private void Exercise()
        {
            if (!(_spec["exercise"] is JObject ex) || (string)_out["status"] != "completed" || _exerciseStep == int.MaxValue) return;
            var speeds = (ex["speeds"] as JArray)?.Select(t => (float)t).ToList() ?? new List<float> { 1f, 3f, 0f, 2f, 3f };
            float every = Request.Num(ex, "everySeconds", 4f);
            if (_exerciseStep < 0)
            {
                _exercise = new JObject { ["recipesSet"] = 0, ["speeds"] = new JArray() };
                _out["exercise"] = _exercise;
                if (Request.Bool(ex, "recipes", true))
                {
                    int n = 0;
                    foreach (var entity in _entityRegistry.Entities)
                    {
                        if (!entity) continue;
                        var m = entity.GetComponent<Timberborn.Workshops.Manufactory>();
                        if (m == null || m.HasCurrentRecipe || m.ProductionRecipes.Length == 0) continue;
                        m.SetRecipe(m.ProductionRecipes[0]);
                        n++;
                    }
                    _exercise["recipesSet"] = n;
                    Harness.Info("grid exercise: recipes set on " + n + " manufactories");
                }
                int bots = (int)Request.Num(ex, "bots", 0f);
                var dc = _districtCenterRegistry.AllDistrictCenters.FirstOrDefault();
                if (bots > 0 && dc != null)
                {
                    var bo = dc.GetComponent<BlockObject>();
                    var at = CoordinateSystem.GridToWorldCentered(bo != null ? bo.PositionedEntrance.Coordinates : dc.CenterCoordinates);
                    for (int i = 0; i < bots; i++) _botFactory.Create(at);
                    _exercise["botsSpawned"] = bots;
                    Harness.Info("grid exercise: " + bots + " bot(s) spawned at the district centre");
                }
                _exerciseStep = 0;
                _exerciseAt = Time.unscaledTime;
                return;
            }
            if (_exerciseStep >= speeds.Count)
            {
                if ((bool?)_exercise["done"] == true) return;
                float hours = _dayNightCycle.PartialDayNumber * 24f;
                if (_holdFromHours < 0f) _holdFromHours = hours;
                float hold = Request.Num(ex, "holdHours", 3f);
                if (speeds.Count == 0 || speeds[speeds.Count - 1] <= 0f) _speedManager.ChangeSpeed(3f);
                if (hours - _holdFromHours >= hold)
                {
                    _exercise["done"] = true;
                    _exercise["heldHours"] = Math.Round(hours - _holdFromHours, 2);
                    Harness.Info("grid exercise done after " + Math.Round(hours - _holdFromHours, 2) + " in-game hours");
                }
                return;
            }
            if (Time.unscaledTime - _exerciseAt < every) return;
            _speedManager.ChangeSpeed(speeds[_exerciseStep]);
            ((JArray)_exercise["speeds"]).Add(speeds[_exerciseStep]);
            Harness.Info("grid exercise: speed " + speeds[_exerciseStep]);
            _exerciseStep++;
            _exerciseAt = Time.unscaledTime;
        }

        // ------------------------------------------------------------------ errors

        private void ClearContext() => SetContext((List<Item>)null, null);

        private void SetContext(Item item, string step) => SetContext(item != null ? new List<Item> { item } : null, step);

        private void SetContext(List<Item> items, string step)
        {
            _context = items ?? new List<Item>();
            _contextStep = step;
        }

        private void OnLog(string condition, string stackTrace, LogType type)
        {
            if (type != LogType.Error && type != LogType.Exception && type != LogType.Assert) return;
            if (_suppressLog || (condition != null && condition.StartsWith("[PandabornDevHarness]", StringComparison.Ordinal))) return;
            if (_context.Count == 0)
            {
                _unattributed++;
                if (_unattributedSamples.Count < 20) _unattributedSamples.Add(type + ": " + Truncate(condition, 300));
                return;
            }
            foreach (var item in _context)
                item.Errors.Add(new JObject
                {
                    ["step"] = _contextStep, ["type"] = type.ToString(), ["message"] = Truncate(condition, 1000),
                    ["stack"] = Truncate(stackTrace, 1500), ["sharedWith"] = _context.Count > 1 ? _context.Count : (JToken)null
                });
        }

        private static void RecordException(Item item, string step, Exception e)
        {
            item.Errors.Add(new JObject { ["step"] = step, ["type"] = "CaughtException", ["message"] = e.GetType().Name + ": " + e.Message, ["stack"] = Truncate(e.StackTrace, 1500) });
        }

        private void Detach()
        {
            Application.logMessageReceived -= OnLog;
            ClearContext();
        }

        private static string Truncate(string s, int max) => s == null ? "" : s.Length <= max ? s : s.Substring(0, max) + "...";

        // ------------------------------------------------------------------ report

        private void RefreshSummary()
        {
            int placed = 0, finished = 0, alive = 0, withErrors = 0, errors = 0, selected = 0, deletedOnFinish = 0;
            var notPlaced = new JObject();
            var notFinished = new JArray();
            var where = new Dictionary<string, int>();
            foreach (var item in _all)
            {
                if (item.Placed)
                {
                    placed++;
                    bool isAlive = item.Objects.All(bo => bo);
                    item.Entry["alive"] = isAlive;
                    if (isAlive) alive++;
                    else if (item.DeleteOnFinish) deletedOnFinish++;
                    if ((bool?)item.Entry["finished"] == true) finished++;
                    else if (item.Ended) notFinished.Add(item.Template);
                    string w = (string)item.Entry["where"] ?? "?";
                    where.TryGetValue(w, out int n);
                    where[w] = n + 1;
                }
                else item.Entry["alive"] = false;
                if ((bool?)item.Entry["selected"] == true) selected++;
                if (item.Errors.Count > 0) { withErrors++; errors += item.Errors.Count; item.Entry["errors"] = item.Errors; }
                if (!item.Placed && item.Entry["reason"] != null) notPlaced[item.Template] = item.Entry["reason"];
            }
            _summary["requested"] = _all.Count;
            _summary["handled"] = _all.Count(i => i.Ended || (i.Failed && !i.Placed));
            _summary["placed"] = placed;
            _summary["placedWhere"] = JObject.FromObject(where);
            _summary["finished"] = finished;
            _summary["selected"] = selected;
            _summary["alive"] = alive;
            _summary["deletedOnFinish"] = deletedOnFinish;
            _summary["notPlaced"] = notPlaced.Count;
            _summary["withErrors"] = withErrors;
            _summary["errors"] = errors;
            _summary["unattributedErrors"] = _unattributed;
            _summary["notPlacedTemplates"] = notPlaced;
            _summary["placedNotFinished"] = notFinished;
            _summary["templatesWithErrors"] = new JArray(_all.Where(i => i.Errors.Count > 0).Select(i => (object)i.Template).ToArray());
            if (_unattributedSamples.Count > 0) _out["unattributedErrorSamples"] = _unattributedSamples;
            _out["complete"] = _phase == Phase.Done && (string)_out["status"] == "completed";
        }

        private void WriteGridJson()
        {
            _lastWrite = Time.unscaledTime;
            if (Harness.OutputDir == null) return;
            try
            {
                string target = Path.Combine(Harness.OutputDir, "grid.json");
                File.WriteAllText(target + ".tmp", _out.ToString(Formatting.Indented));
                if (File.Exists(target)) File.Delete(target);
                File.Move(target + ".tmp", target);
            }
            catch (Exception e) { Harness.Warn("grid: writing grid.json failed: " + e.Message); }
        }
    }
}
