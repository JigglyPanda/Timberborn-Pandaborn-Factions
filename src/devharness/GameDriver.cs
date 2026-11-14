using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Bindito.Core;
using Newtonsoft.Json.Linq;
using Timberborn.AssetSystem;
using Timberborn.BatchControl;
using Timberborn.BehaviorSystem;
using Timberborn.Beavers;
using Timberborn.BlockObjectTools;
using Timberborn.BlockSystem;
using Timberborn.Bots;
using Timberborn.Buildings;
using Timberborn.CameraSystem;
using Timberborn.CharacterModelSystem;
using Timberborn.Characters;
using Timberborn.ConstructionSites;
using Timberborn.Coordinates;
using Timberborn.CoreUI;
using Timberborn.Debugging;
using Timberborn.EntitySystem;
using Timberborn.GameDistricts;
using Timberborn.GameFactionSystem;
using Timberborn.GameSaveRepositorySystem;
using Timberborn.GameSaveRuntimeSystem;
using Timberborn.NeedSystem;
using Timberborn.PlatformUtilities;
using Timberborn.SingletonSystem;
using Timberborn.TemplateSystem;
using Timberborn.TerrainSystem;
using Timberborn.Timbermesh;
using Timberborn.TimeSystem;
using Timberborn.UILayoutSystem;
using UnityEngine;

namespace PandabornDevHarness
{
    [Context("Game")]
    public class GameHarnessConfigurator : Configurator
    {
        protected override void Configure()
        {
            if (!Harness.Active) return;   // no request: bind nothing at all
            Bind<GameDriver>().AsSingleton();
        }
    }

    /// <summary>Runs the requested scenario once the new game is playable, then reports and quits.</summary>
    public class GameDriver : ILoadableSingleton, IUpdatableSingleton
    {
        private enum Phase { WaitingForStart, Settling, StartShots, Running, EndShots, BatchControl, Saving, Finishing, Done }

        private readonly EventBus _eventBus;
        private readonly SpeedManager _speedManager;
        private readonly IDayNightCycle _dayNightCycle;
        private readonly DevModeManager _devModeManager;
        private readonly FactionService _factionService;
        private readonly CharacterPopulation _characterPopulation;
        private readonly BeaverPopulation _beaverPopulation;
        private readonly BotPopulation _botPopulation;
        private readonly TemplateService _templateService;
        private readonly CameraService _cameraService;
        private readonly Timberborn.Rendering.MaterialColorer _materialColorer;
        private readonly DistrictCenterRegistry _districtCenterRegistry;
        private readonly ITerrainService _terrainService;
        private readonly PreviewPlacerFactory _previewPlacerFactory;
        private readonly BlockObjectPlacerService _blockObjectPlacerService;
        private readonly ConstructionFactory _constructionFactory;
        private readonly IBlockService _blockService;
        private readonly IBatchControlBox _batchControlBox;
        private readonly List<BatchControlModule> _batchControlModules;
        private readonly GameSaver _gameSaver;
        private readonly List<IAssetProvider> _assetProviders;

        private Phase _phase = Phase.WaitingForStart;
        private bool _primaryUiShown;
        private float _loadedAt, _phaseStartedAt, _runStartedAt, _runStartHours;
        private readonly Queue<ShotRequest> _shotQueue = new Queue<ShotRequest>();
        private readonly List<ShotRequest> _timedShots = new List<ShotRequest>();
        private readonly List<string> _pendingScreenFiles = new List<string>();
        // first placed building of each template, for "building" close-up shots
        private readonly Dictionary<string, BlockObject> _placedByTemplate = new Dictionary<string, BlockObject>();
        private readonly List<AnimationRequest> _pendingAnimations = new List<AnimationRequest>();
        private float _waitUntil;
        private int _batchStep;
        private List<BatchControlTab> _batchTabs;
        private JArray _batchResults;
        private bool _saveCompleted;
        private Dictionary<Texture, string> _coatPaths;
        private readonly Dictionary<string, int> _activity = new Dictionary<string, int>();
        private readonly Dictionary<string, int> _executors = new Dictionary<string, int>();
        private float _nextActivitySample;
        private int _activitySamples;

        public GameDriver(EventBus eventBus, SpeedManager speedManager, IDayNightCycle dayNightCycle, DevModeManager devModeManager,
                          FactionService factionService, CharacterPopulation characterPopulation, BeaverPopulation beaverPopulation,
                          Timberborn.Rendering.MaterialColorer materialColorer,
                          BotPopulation botPopulation, TemplateService templateService, CameraService cameraService,
                          DistrictCenterRegistry districtCenterRegistry, ITerrainService terrainService,
                          PreviewPlacerFactory previewPlacerFactory, BlockObjectPlacerService blockObjectPlacerService,
                          ConstructionFactory constructionFactory, IBatchControlBox batchControlBox,
                          IEnumerable<BatchControlModule> batchControlModules, GameSaver gameSaver,
                          IAssetLoader assetLoader, IBlockService blockService)
        {
            _blockService = blockService;
            _batchControlBox = batchControlBox;
            _batchControlModules = batchControlModules.ToList();
            _gameSaver = gameSaver;
            // the providers the game's AssetLoader really uses (an injected IEnumerable<IAssetProvider> comes back empty here)
            _assetProviders = new List<IAssetProvider>();
            var field = assetLoader.GetType().GetField("_assetProviders", System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic);
            if (field?.GetValue(assetLoader) is IEnumerable<IAssetProvider> providers) _assetProviders.AddRange(providers);
            else Harness.Warn("could not read AssetLoader._assetProviders; asset provenance will be empty");
            _eventBus = eventBus;
            _speedManager = speedManager;
            _dayNightCycle = dayNightCycle;
            _devModeManager = devModeManager;
            _factionService = factionService;
            _characterPopulation = characterPopulation;
            _beaverPopulation = beaverPopulation;
            _botPopulation = botPopulation;
            _templateService = templateService;
            _cameraService = cameraService;
            _materialColorer = materialColorer;
            _districtCenterRegistry = districtCenterRegistry;
            _terrainService = terrainService;
            _previewPlacerFactory = previewPlacerFactory;
            _blockObjectPlacerService = blockObjectPlacerService;
            _constructionFactory = constructionFactory;
        }

        public void Load()
        {
            _loadedAt = Time.unscaledTime;
            _eventBus.Register(this);
            Harness.CollectOnCrash = () => CollectGameData(false);
            Harness.Info("game scene loaded");
        }

        [OnEvent]
        public void OnShowPrimaryUI(ShowPrimaryUIEvent showPrimaryUIEvent)
        {
            _primaryUiShown = true;
        }

        public void UpdateSingleton()
        {
            if (Harness.Finished || _phase == Phase.Done) return;
            Harness.ApplyRuntimeSettings();
            try { Step(); }
            catch (Exception e)
            {
                Harness.Error("harness step failed in phase " + _phase, e);
                SafeCollect();
                _phase = Phase.Done;
                Harness.Finish("error");
            }
        }

        private void Step()
        {
            float now = Time.unscaledTime;
            if (now < _waitUntil) return;
            var request = Harness.Request;
            switch (_phase)
            {
                case Phase.WaitingForStart:
                    if (!_primaryUiShown)
                    {
                        if (now - _loadedAt > request.StartTimeoutSeconds)
                        {
                            Harness.Error("the game did not become playable within " + request.StartTimeoutSeconds + " s");
                            SafeCollect();
                            _phase = Phase.Done;
                            Harness.Finish("error");
                        }
                        return;
                    }
                    OnGameStarted();
                    Enter(Phase.Settling);
                    return;

                case Phase.Settling:
                    if (now - _phaseStartedAt < request.SettleSeconds) return;
                    PlaceBuildings();
                    foreach (var shot in request.Screenshots)
                    {
                        if (shot.At == "start") _shotQueue.Enqueue(shot);
                        else if (shot.IsTimed(out _)) _timedShots.Add(shot);
                    }
                    _speedManager.ChangeSpeed(0f);   // freeze for steady pictures
                    Enter(Phase.StartShots);
                    _waitUntil = now + 1f;            // let placed buildings and the pause settle for a moment
                    return;

                case Phase.StartShots:
                    if (TakeNextShot()) return;
                    _runStartedAt = now;
                    _runStartHours = _dayNightCycle.PartialDayNumber * 24f;
                    _pendingAnimations.AddRange(request.Animations);
                    _speedManager.ChangeSpeed(request.Speed);
                    Harness.Info("running at speed " + request.Speed + " for " + DescribeRun(request));
                    Harness.Result["run"] = new JObject { ["startDay"] = Math.Round(_dayNightCycle.PartialDayNumber, 3) };
                    Enter(Phase.Running);
                    return;

                case Phase.Running:
                    if (now >= _nextActivitySample) { SampleActivity(); _nextActivitySample = now + 2f; }
                    for (int i = _pendingAnimations.Count - 1; i >= 0; i--)
                        if (now - _runStartedAt >= _pendingAnimations[i].At)
                        {
                            StartAnimation(_pendingAnimations[i]);
                            _pendingAnimations.RemoveAt(i);
                        }
                    for (int i = _timedShots.Count - 1; i >= 0; i--)
                        if (_timedShots[i].IsTimed(out float at) && now - _runStartedAt >= at)
                        {
                            _shotQueue.Enqueue(_timedShots[i]);
                            _timedShots.RemoveAt(i);
                        }
                    if (TakeNextShot()) return;
                    if (!RunIsOver(request, now)) return;
                    _speedManager.ChangeSpeed(0f);
                    foreach (var shot in _timedShots) _shotQueue.Enqueue(shot);
                    foreach (var shot in request.Screenshots) if (shot.At == "end") _shotQueue.Enqueue(shot);
                    Enter(Phase.EndShots);
                    _waitUntil = now + 0.5f;
                    return;

                case Phase.EndShots:
                    if (TakeNextShot()) return;
                    if (request.BatchControl) { _batchStep = 0; Enter(Phase.BatchControl); }
                    else EnterSavingOrFinishing(request);
                    return;

                case Phase.BatchControl:
                    if (StepBatchControl(now)) EnterSavingOrFinishing(request);
                    return;

                case Phase.Saving:
                    if (!_saveCompleted && now - _phaseStartedAt < 60f) return;
                    if (Harness.Result["save"] is JObject save)
                    {
                        save["saved"] = _saveCompleted;
                        save["seconds"] = Math.Round(now - _phaseStartedAt, 1);
                        save["exists"] = File.Exists((string)save["file"]);
                        if (!_saveCompleted) Harness.Error("saving the game did not complete within 60 s");
                        else Harness.Info("saved the game to " + save["file"]);
                    }
                    Enter(Phase.Finishing);
                    return;

                case Phase.Finishing:
                    // ScreenCapture writes its file at the end of a frame: wait for those
                    if (_pendingScreenFiles.Any(f => !File.Exists(f)) && now - _phaseStartedAt < 10f) return;
                    CollectGameData(true);
                    _phase = Phase.Done;
                    Harness.Finish("completed");
                    return;
            }
        }

        /// <summary>Counts what every character is doing (running root behavior and executor), every 2 real seconds of the run.</summary>
        private void SampleActivity()
        {
            _activitySamples++;
            foreach (var character in _characterPopulation.Characters)
            {
                if (!character) continue;
                var behaviors = character.GetComponent<BehaviorManager>();
                if (behaviors == null) continue;
                string kind = Kind(character);
                string behavior = kind + ":" + (behaviors.RunningBehavior.Name ?? "none");
                _activity.TryGetValue(behavior, out int n);
                _activity[behavior] = n + 1;
                string executor = kind + ":" + (behaviors.RunningExecutor.Name ?? "none");
                _executors.TryGetValue(executor, out int m);
                _executors[executor] = m + 1;
            }
        }

        private void EnterSavingOrFinishing(Request request)
        {
            if (request.SaveName == null) { Enter(Phase.Finishing); return; }
            Enter(Phase.Saving);
            try
            {
                string dir = Path.Combine(UserDataFolder.Folder, "Saves");
                var reference = new SaveReference(request.SaveName, new SettlementReference(request.SettlementName, dir));
                Harness.Result["save"] = new JObject
                {
                    ["settlementName"] = request.SettlementName,
                    ["saveName"] = request.SaveName,
                    ["file"] = Path.Combine(dir, request.SettlementName, request.SaveName + ".timber"),
                    ["day"] = Math.Round(_dayNightCycle.PartialDayNumber, 3)
                };
                _gameSaver.QueueSaveSkippingNameValidation(reference, () => _saveCompleted = true);
                Harness.Info("saving as " + reference);
            }
            catch (Exception e)
            {
                Harness.Error("queueing the save failed", e);
                Enter(Phase.Finishing);
            }
        }

        /// <summary>
        /// Opens every batch-control tab once, the Population (characters) tab last, captures the screen with it open, then
        /// closes the window. A tab that throws is recorded and fails the batchControlTabs check. Returns true when done.
        /// </summary>
        private bool StepBatchControl(float now)
        {
            if (_batchTabs == null)
            {
                _batchTabs = _batchControlModules.SelectMany(m => m.Tabs).OrderBy(kv => kv.Key).Select(kv => kv.Value).ToList();
                _batchResults = new JArray();
                Harness.Result["batchControl"] = new JObject { ["tabs"] = _batchResults };
            }
            int count = _batchTabs.Count;
            int population = _batchTabs.FindIndex(t => t.GetType().Name == "CharacterBatchControlTab");
            // order: every other tab, then Population, then capture, then close
            var order = Enumerable.Range(0, count).Where(i => i != population).ToList();
            if (population >= 0) order.Add(population);
            if (_batchStep < order.Count)
            {
                int index = order[_batchStep++];
                var tab = _batchTabs[index];
                var entry = new JObject { ["index"] = index, ["type"] = tab.GetType().Name, ["nameLocKey"] = tab.TabNameLocKey, ["opened"] = false };
                _batchResults.Add(entry);
                try
                {
                    _batchControlBox.OpenTab(index);
                    entry["opened"] = true;
                }
                catch (Exception e)
                {
                    entry["error"] = e.GetType().Name + ": " + e.Message;
                    Harness.Error("batch-control tab " + index + " (" + tab.GetType().Name + ") threw", e);
                }
                _waitUntil = now + (index == population ? 1.2f : 0.3f);
                return false;
            }
            if (_batchStep == order.Count)
            {
                _batchStep++;
                string file = Path.Combine(Harness.OutputDir, "batch_population.png");
                ScreenCapture.CaptureScreenshot(file);
                _pendingScreenFiles.Add(file);
                Harness.RecordScreenshot("batch_population", "screen", Path.GetFileName(file), new JObject { ["tabIndex"] = population }, null);
                _waitUntil = now + 0.6f;
                return false;
            }
            try
            {
                if (_batchControlBox is IPanelController panel) panel.OnUICancelled();
                else Harness.Warn("batch-control box is not an IPanelController; left open");
            }
            catch (Exception e) { Harness.Error("closing the batch-control window failed", e); }
            _waitUntil = now + 0.5f;
            return true;
        }

        private void Enter(Phase phase)
        {
            _phase = phase;
            _phaseStartedAt = Time.unscaledTime;
            Harness.Info("phase " + phase);
        }

        private bool RunIsOver(Request request, float now)
        {
            float real = now - _runStartedAt;
            // a grid request with "exercise" keeps the run going until GridLab has finished it (within the real cap)
            if (Harness.Request.Raw?["grid"]?["exercise"] != null && real < request.RunRealSeconds
                && !((bool?)Harness.Result["grid"]?["exercise"]?["done"] ?? false)
                && !(((string)Harness.Result["grid"]?["status"])?.StartsWith("incomplete") ?? false)
                && !(((string)Harness.Result["grid"]?["status"])?.StartsWith("error") ?? false))
                return false;
            if (request.RunInGameHours > 0f)
                return _dayNightCycle.PartialDayNumber * 24f - _runStartHours >= request.RunInGameHours || real >= request.RunRealSeconds;
            return real >= request.RunRealSeconds;
        }

        private static string DescribeRun(Request request)
        {
            return request.RunInGameHours > 0f
                ? request.RunInGameHours + " in-game hours (cap " + request.RunRealSeconds + " real s)"
                : request.RunRealSeconds + " real seconds";
        }

        private void OnGameStarted()
        {
            var request = Harness.Request;
            Harness.ApplyWindow();
            if (request.DevMode) _devModeManager.Enable();
            Harness.Result["game"] = new JObject
            {
                ["started"] = true,
                ["secondsToPlayable"] = Math.Round(Time.unscaledTime - _loadedAt, 1),
                ["devMode"] = _devModeManager.Enabled
            };
            CollectGameData(false);
            Harness.WriteResult("running");
            Harness.Info("game is playable; faction " + _factionService.Current.Id + ", " + _beaverPopulation.NumberOfAdults + " adults, "
                         + _beaverPopulation.NumberOfChildren + " children");
        }

        // ------------------------------------------------------------------ buildings

        private void PlaceBuildings()
        {
            var requests = Harness.Request.Buildings;
            if (requests.Count == 0) return;
            var results = new JArray();
            Harness.Result["placedBuildings"] = results;
            var center = _districtCenterRegistry.AllDistrictCenters.FirstOrDefault();
            if (center == null)
            {
                foreach (var r in requests) results.Add(new JObject { ["template"] = r.Template, ["placed"] = false, ["error"] = "no district center" });
                return;
            }
            var anchor = center.CenterCoordinates;
            var centerBlockObject = center.GetComponent<BlockObject>();
            var entranceAnchor = centerBlockObject != null && centerBlockObject.HasEntrance
                ? centerBlockObject.PositionedEntrance.Coordinates : anchor;
            Vector3Int? previousOrigin = null;
            var specs = _templateService.GetAll<PlaceableBlockObjectSpec>().ToList();
            var used = new List<Vector3Int>();
            var created = new List<BlockObject>();
            foreach (var r in requests)
            {
                var entry = new JObject { ["template"] = r.Template, ["finished"] = r.Finished, ["placed"] = false };
                results.Add(entry);
                try
                {
                    var spec = specs.FirstOrDefault(s => TemplateName(s.Blueprint) == r.Template)
                               ?? specs.FirstOrDefault(s => s.GetSpec<TemplateSpec>()?.IsNamed(r.Template) == true);
                    if (spec == null) { entry["error"] = "template not available to this faction"; continue; }
                    var relative = anchor;
                    if (r.RelativeTo == "districtEntrance") relative = entranceAnchor;
                    else if (r.RelativeTo == "previous" && previousOrigin.HasValue) relative = previousOrigin.Value;
                    var placement = FindPlacement(spec, relative, r, used);
                    if (!placement.HasValue) { entry["error"] = "no valid spot found near the district center"; continue; }
                    var builder = new EntitySetup.Builder(spec.Blueprint);
                    if (spec.HasSpec<BuildingSpec>())
                    {
                        var blockObject = r.Finished ? _constructionFactory.CreateAsFinished(builder, placement.Value)
                                                     : _constructionFactory.CreateAsUnfinished(builder, placement.Value);
                        if (blockObject)
                        {
                            created.Add(blockObject);
                            if (!_placedByTemplate.ContainsKey(r.Template)) _placedByTemplate[r.Template] = blockObject;
                        }
                    }
                    else
                    {
                        _blockObjectPlacerService.GetMatchingPlacer(spec.GetSpec<BlockObjectSpec>()).Place(builder, placement.Value);
                    }
                    var c = placement.Value.Coordinates;
                    used.Add(c);
                    previousOrigin = c;
                    entry["placed"] = true;
                    entry["coordinates"] = new JArray(c.x, c.y, c.z);
                    entry["orientation"] = placement.Value.Orientation.ToString();
                }
                catch (Exception e)
                {
                    entry["error"] = e.GetType().Name + ": " + e.Message;
                    Harness.Error("placing " + r.Template + " failed", e);
                }
            }
            Harness.Info("placed " + results.Count(t => (bool)t["placed"]) + " of " + requests.Count + " building(s)");
            if (Harness.Request.ConnectPaths)
            {
                // PositionedEntrance.Coordinates is the cell in front of the door (where the path goes);
                // DoorstepCoordinates, despite its name, is the building's own block behind it
                var centerBlock = center.GetComponent<BlockObject>();
                var start = centerBlock != null && centerBlock.HasEntrance ? centerBlock.PositionedEntrance.Coordinates : anchor;
                ConnectWithPaths(start, created, specs);
            }
        }

        /// <summary>
        /// Explicit offsets are tried as given. Otherwise rings around the district center doorstep are searched, from 4 tiles
        /// out, keeping 2 tiles from earlier placements; the game's own placement validation decides what is valid.
        /// </summary>
        private Placement? FindPlacement(PlaceableBlockObjectSpec spec, Vector3Int anchor, BuildingRequest request, List<Vector3Int> used)
        {
            var placer = _previewPlacerFactory.Create(spec);
            try
            {
                var orientations = new List<Orientation>();
                if (request.Orientation != null && Enum.TryParse(request.Orientation, true, out Orientation wanted)) orientations.Add(wanted);
                else orientations.AddRange(new[] { Orientation.Cw0, Orientation.Cw90, Orientation.Cw180, Orientation.Cw270 });

                if (request.Offset != null)
                {
                    var target = new Vector3Int(anchor.x + request.Offset[0], anchor.y + request.Offset[1], anchor.z + request.Offset[2]);
                    foreach (var o in orientations)
                    {
                        var p = Valid(placer, Ground(target), o);
                        if (p.HasValue) return p;
                    }
                    return null;
                }
                for (int radius = 4; radius <= 24; radius++)
                    for (int dx = -radius; dx <= radius; dx++)
                        for (int dy = -radius; dy <= radius; dy++)
                        {
                            if (Math.Max(Math.Abs(dx), Math.Abs(dy)) != radius) continue;
                            var cell = Ground(new Vector3Int(anchor.x + dx, anchor.y + dy, anchor.z));
                            if (used.Any(u => Math.Abs(u.x - cell.x) < 3 && Math.Abs(u.y - cell.y) < 3)) continue;
                            foreach (var o in orientations)
                            {
                                var p = Valid(placer, cell, o);
                                if (p.HasValue) return p;
                            }
                        }
                return null;
            }
            finally
            {
                placer.HideAllPreviews();
            }
        }

        /// <summary>
        /// Lays finished Path tiles from the district center's entrance cell to each placed building's entrance cell along the shortest
        /// route (breadth-first search over level ground where a path is valid or already exists), so placed buildings are
        /// connected and get workers. Routes never change level, so buildings on another level stay unconnected.
        /// </summary>
        private void ConnectWithPaths(Vector3Int anchor, List<BlockObject> buildings, List<PlaceableBlockObjectSpec> specs)
        {
            var pathSpec = specs.FirstOrDefault(sp => TemplateName(sp.Blueprint) == "Path");
            var report = new JObject();
            Harness.Result["paths"] = report;
            if (pathSpec == null) { report["error"] = "no Path template"; return; }
            var placer = _previewPlacerFactory.Create(pathSpec);
            var passable = new Dictionary<Vector2Int, Placement?>();   // null value = already a path (or a doorstep)
            int placedTiles = 0;
            var connections = new JArray();
            try
            {
                foreach (var building in buildings)
                {
                    if (!building || !building.HasEntrance) continue;
                    var door = building.PositionedEntrance.Coordinates;
                    var route = FindRoute(anchor, door, placer, passable);
                    int laid = 0;
                    if (route != null)
                        foreach (var cell in route)
                        {
                            if (IsPath(cell)) continue;
                            var placement = Valid(placer, cell, Orientation.Cw0);
                            if (!placement.HasValue) continue;
                            var builder = new EntitySetup.Builder(pathSpec.Blueprint);
                            if (pathSpec.HasSpec<BuildingSpec>()) _constructionFactory.CreateAsFinished(builder, placement.Value);
                            else _blockObjectPlacerService.GetMatchingPlacer(pathSpec.GetSpec<BlockObjectSpec>()).Place(builder, placement.Value);
                            laid++;
                        }
                    placedTiles += laid;
                    connections.Add(new JObject
                    {
                        ["building"] = building.GetComponent<TemplateSpec>()?.TemplateName ?? "?",
                        ["entrance"] = new JArray(door.x, door.y, door.z),
                        ["routeFound"] = route != null,
                        ["routeLength"] = route?.Count ?? 0,
                        ["tilesLaid"] = laid
                    });
                }
            }
            catch (Exception e) { Harness.Error("laying paths failed", e); report["error"] = e.GetType().Name + ": " + e.Message; }
            finally { placer.HideAllPreviews(); }
            report["anchor"] = new JArray(anchor.x, anchor.y, anchor.z);
            report["tiles"] = placedTiles;
            report["connections"] = connections;
            Harness.Info("laid " + placedTiles + " path tile(s)");
        }

        private List<Vector3Int> FindRoute(Vector3Int from, Vector3Int to, PreviewPlacer placer, Dictionary<Vector2Int, Placement?> cache)
        {
            const int margin = 12;
            int minX = Math.Min(from.x, to.x) - margin, maxX = Math.Max(from.x, to.x) + margin;
            int minY = Math.Min(from.y, to.y) - margin, maxY = Math.Max(from.y, to.y) + margin;
            var start = new Vector2Int(from.x, from.y);
            var goal = new Vector2Int(to.x, to.y);
            bool Open(Vector2Int c)
            {
                if (c == start || c == goal) return true;
                if (c.x < minX || c.x > maxX || c.y < minY || c.y > maxY) return false;
                if (!_terrainService.Contains(c)) return false;
                var cell = new Vector3Int(c.x, c.y, from.z);
                if (Ground(cell).z != from.z) return false;
                if (cache.TryGetValue(c, out var known)) return known.HasValue || IsPath(cell);
                if (IsPath(cell)) { cache[c] = null; return true; }
                var p = Valid(placer, cell, Orientation.Cw0);
                cache[c] = p;
                return p.HasValue;
            }
            if (to.z != from.z) return null;
            var previous = new Dictionary<Vector2Int, Vector2Int> { [start] = start };
            var queue = new Queue<Vector2Int>();
            queue.Enqueue(start);
            var steps = new[] { new Vector2Int(1, 0), new Vector2Int(-1, 0), new Vector2Int(0, 1), new Vector2Int(0, -1) };
            while (queue.Count > 0)
            {
                var c = queue.Dequeue();
                if (c == goal)
                {
                    var route = new List<Vector3Int>();
                    for (var at = goal; ; at = previous[at])
                    {
                        route.Add(new Vector3Int(at.x, at.y, from.z));
                        if (at == start) break;
                    }
                    route.Reverse();
                    return route;
                }
                foreach (var step in steps)
                {
                    var n = c + step;
                    if (previous.ContainsKey(n) || !Open(n)) continue;
                    previous[n] = c;
                    queue.Enqueue(n);
                }
            }
            return null;
        }

        private bool IsPath(Vector3Int cell)
        {
            foreach (var o in _blockService.GetObjectsAt(cell))
                if (o && o.GetComponent<TemplateSpec>()?.TemplateName == "Path") return true;
            return false;
        }

        private Vector3Int Ground(Vector3Int c)
        {
            if (!_terrainService.Contains(new Vector2Int(c.x, c.y))) return c;
            int z = _terrainService.GetTerrainHeightBelow(new Vector3Int(c.x, c.y, c.z + 4));
            return new Vector3Int(c.x, c.y, z);
        }

        private static Placement? Valid(PreviewPlacer placer, Vector3Int cell, Orientation orientation)
        {
            var buildable = placer.GetBuildableCoordinates(new[] { new Placement(cell, orientation, FlipMode.Unflipped) }).ToList();
            return buildable.Count > 0 ? buildable[0] : (Placement?)null;
        }

        /// <summary>Plays a placed building's animation the way WonderAnimationController starts it on activation (every
        /// IAnimator under the building; result "animations").</summary>
        private void StartAnimation(AnimationRequest a)
        {
            var log = Harness.Result["animations"] as JArray;
            if (log == null) { log = new JArray(); Harness.Result["animations"] = log; }
            var entry = new JObject { ["target"] = a.Target, ["name"] = a.Name, ["at"] = a.At };
            log.Add(entry);
            try
            {
                if (!_placedByTemplate.TryGetValue(a.Target, out var building) || !building)
                {
                    entry["error"] = "target not placed";
                    return;
                }
                var animators = building.GameObject.GetComponentsInChildren<Timberborn.TimbermeshAnimations.IAnimator>(true);
                entry["animators"] = animators.Length;
                var started = new JArray();
                foreach (var animator in animators)
                {
                    animator.Enabled = true;
                    animator.PlayBackwards = a.Backwards;
                    animator.Speed = a.Speed;
                    animator.Play(a.Name, a.Looped);
                    started.Add(new JObject { ["animation"] = animator.AnimationName, ["length"] = Math.Round(animator.AnimationLength, 3) });
                }
                entry["started"] = started;
                Harness.Info("animation " + a.Name + " started on " + a.Target + " (" + animators.Length + " animator(s))");
            }
            catch (Exception e)
            {
                entry["error"] = e.GetType().Name + ": " + e.Message;
                Harness.Error("starting animation on " + a.Target + " failed", e);
            }
        }

        // ------------------------------------------------------------------ screenshots

        /// <summary>Takes at most one queued shot per frame. Returns true while shots remain.</summary>
        private bool TakeNextShot()
        {
            if (_shotQueue.Count == 0) return false;
            var shot = _shotQueue.Dequeue();
            string file = Path.Combine(Harness.OutputDir, Sanitize(shot.Name) + ".png");
            JObject subject = null;
            try
            {
                var request = Harness.Request;
                var source = _cameraService.Transform ? _cameraService.Transform.GetComponent<Camera>() : Camera.main;
                switch (shot.Kind)
                {
                    case "screen":
                        ScreenCapture.CaptureScreenshot(file);
                        _pendingScreenFiles.Add(file);
                        break;
                    case "overview":
                        Capture.RenderView(source, request.ShotWidth, request.ShotHeight, file);
                        break;
                    case "building":
                        GameObject framed = null;
                        Timberborn.BaseComponentSystem.BaseComponent framedEntity = null;
                        if (shot.Target != null && _placedByTemplate.TryGetValue(shot.Target, out var placed) && placed) framedEntity = placed;
                        else if (shot.Target != null && shot.Target.StartsWith("DistrictCenter", StringComparison.Ordinal))
                            framedEntity = _districtCenterRegistry.AllDistrictCenters.FirstOrDefault();
                        if (framedEntity) framed = framedEntity.GameObject;
                        // "lit": switch the building's night lighting on (as an occupied house or a working workplace is)
                        if (framed && shot.Lit)
                        {
                            try { _materialColorer.EnableLighting(framedEntity, 1f); }
                            catch (Exception) { Harness.Warn("shot " + shot.Name + ": " + shot.Target + " has no night lighting to switch on"); }
                        }
                        if (!framed)
                        {
                            Harness.RecordScreenshot(shot.Name, shot.Kind, null, null, "no placed building " + (shot.Target ?? "(no target)"));
                            return _shotQueue.Count > 0;
                        }
                        subject = new JObject { ["template"] = shot.Target, ["yaw"] = shot.Yaw, ["pitch"] = shot.Pitch, ["zoom"] = shot.Zoom };
                        if (shot.Front) subject["front"] = true;
                        Capture.RenderFramed(source, framed, shot.Yaw, shot.Pitch, shot.Zoom,
                                             request.ShotWidth, request.ShotHeight, file,
                                             shot.Front ? framed.transform.eulerAngles.y : (float?)null, shot.MinDistance);
                        break;
                    case "adult":
                    case "child":
                    case "bot":
                        var character = PickVisible(shot.Kind);
                        if (character == null)
                        {
                            Harness.RecordScreenshot(shot.Name, shot.Kind, null, null, "no visible " + shot.Kind + " right now");
                            return _shotQueue.Count > 0;
                        }
                        subject = Describe(character);
                        Capture.RenderStudio(source, character.GetComponent<CharacterModel>().Model, BodyRenderer(character), request.CloseupSize, file);
                        break;
                    default:
                        Harness.RecordScreenshot(shot.Name, shot.Kind, null, null, "unknown kind " + shot.Kind);
                        return _shotQueue.Count > 0;
                }
                if (subject == null) subject = new JObject();
                subject["inGameDay"] = Math.Round(_dayNightCycle.PartialDayNumber, 3);
                subject["daytime"] = _dayNightCycle.IsDaytime;
                Harness.RecordScreenshot(shot.Name, shot.Kind, Path.GetFileName(file), subject, null);
                Harness.Info("screenshot " + shot.Name + " -> " + file);
            }
            catch (Exception e)
            {
                Harness.RecordScreenshot(shot.Name, shot.Kind, null, subject, e.GetType().Name + ": " + e.Message);
                Harness.Error("screenshot " + shot.Name + " failed", e);
            }
            return true;
        }

        private Character PickVisible(string kind)
        {
            foreach (var character in _characterPopulation.Characters)
            {
                if (!character || Kind(character) != kind) continue;
                var body = BodyRenderer(character);
                var model = character.GetComponent<CharacterModel>();
                if (body && body.enabled && body.gameObject.activeInHierarchy && model != null && model.Model
                    && body.transform.IsChildOf(model.Model))
                    return character;
            }
            return null;
        }

        private static string Sanitize(string name)
        {
            foreach (var c in Path.GetInvalidFileNameChars()) name = name.Replace(c, '_');
            return name;
        }

        // ------------------------------------------------------------------ reporting

        private void SafeCollect()
        {
            try { CollectGameData(false); }
            catch (Exception e) { Harness.Error("collecting game data failed", e); }
        }

        private void CollectGameData(bool full)
        {
            var result = Harness.Result;
            var faction = _factionService.Current;
            if (faction != null)
                result["activeFaction"] = new JObject
                {
                    ["id"] = faction.Id,
                    ["startingBuildingId"] = faction.StartingBuildingId,
                    ["templateCollectionIds"] = new JArray(faction.TemplateCollectionIds.ToArray()),
                    ["materialCollectionIds"] = new JArray(faction.MaterialCollectionIds.ToArray()),
                    ["needCollectionIds"] = new JArray(faction.NeedCollectionIds.ToArray()),
                    ["goodCollectionIds"] = new JArray(faction.GoodCollectionIds.ToArray()),
                    ["textures"] = new JArray(faction.Textures.Select(t => (object)t.Path).ToArray()),
                    ["childTextures"] = new JArray(faction.ChildTextures.Select(t => (object)t.Path).ToArray())
                };
            result["population"] = new JObject
            {
                ["adults"] = _beaverPopulation.NumberOfAdults,
                ["children"] = _beaverPopulation.NumberOfChildren,
                ["bots"] = _botPopulation.NumberOfBots,
                ["characters"] = _characterPopulation.NumberOfCharacters
            };
            result["time"] = new JObject
            {
                ["day"] = Math.Round(_dayNightCycle.PartialDayNumber, 3),
                ["daytime"] = _dayNightCycle.IsDaytime,
                ["speed"] = _speedManager.CurrentSpeed,
                ["inGameHoursRun"] = _runStartedAt > 0f ? Math.Round(_dayNightCycle.PartialDayNumber * 24f - _runStartHours, 2) : 0,
                ["realSecondsRun"] = _runStartedAt > 0f ? Math.Round(Time.unscaledTime - _runStartedAt, 1) : 0
            };
            result["window"] = new JObject { ["width"] = Screen.width, ["height"] = Screen.height, ["mode"] = Screen.fullScreenMode.ToString() };
            if (result["game"] is JObject game) game["devMode"] = _devModeManager.Enabled;

            var samples = new JArray();
            var perKind = new Dictionary<string, int>();
            foreach (var character in _characterPopulation.Characters)
            {
                if (!character) continue;
                string kind = Kind(character);
                perKind.TryGetValue(kind, out int n);
                if (n >= Harness.Request.SamplePerKind) continue;
                perKind[kind] = n + 1;
                samples.Add(Describe(character));
            }
            result["characterSamples"] = samples;
            if (_activitySamples > 0)
                result["activity"] = new JObject
                {
                    ["samples"] = _activitySamples,
                    ["behaviors"] = JObject.FromObject(_activity.OrderByDescending(kv => kv.Value).ToDictionary(kv => kv.Key, kv => kv.Value)),
                    ["executors"] = JObject.FromObject(_executors.OrderByDescending(kv => kv.Value).Take(40).ToDictionary(kv => kv.Key, kv => kv.Value))
                };
            var templateCounts = new JObject();
            foreach (var character in _characterPopulation.Characters)
            {
                if (!character) continue;
                string name = TemplateName(character) ?? "?";
                templateCounts[name] = ((int?)templateCounts[name] ?? 0) + 1;
            }
            result["characterTemplates"] = templateCounts;

            if (!full) return;
            var placeable = new JArray();
            foreach (var spec in _templateService.GetAll<PlaceableBlockObjectSpec>()
                         .OrderBy(s => s.ToolGroupId).ThenBy(s => s.ToolOrder))
                placeable.Add(new JObject
                {
                    ["template"] = TemplateName(spec.Blueprint),
                    ["toolGroup"] = spec.ToolGroupId,
                    ["building"] = spec.HasSpec<BuildingSpec>(),
                    ["devOnly"] = spec.DevModeTool
                });
            var characterTemplates = new JObject();
            foreach (var kind in new[] { "AdultSpec", "ChildSpec", "BotSpec" })
            {
                var list = new JArray();
                foreach (var t in _templateService.GetAll<TemplateSpec>())
                {
                    var blueprint = t.Blueprint;
                    if (blueprint == null || !blueprint.Specs.Any(sp => sp.GetType().Name == kind)) continue;
                    string model = FindModelPath(blueprint);
                    list.Add(new JObject
                    {
                        ["template"] = t.TemplateName,
                        ["model"] = model,
                        ["modelProviders"] = model != null ? AssetProviders<BinaryData>(model) : null,
                        ["label"] = blueprint.GetSpec<SimpleLabeledEntitySpec>()?.EntityNameLocKey
                    });
                }
                characterTemplates[kind] = list;
            }
            result["characterTemplatesActive"] = characterTemplates;
            var coats = new JArray();
            if (faction != null)
                foreach (var t in faction.Textures.Concat(faction.ChildTextures))
                    coats.Add(new JObject { ["path"] = t.Path, ["name"] = t.Asset ? t.Asset.name : null, ["providers"] = AssetProviders<Texture2D>(t.Path) });
            result["factionCoats"] = coats;
            var all = _templateService.GetAll<TemplateSpec>().Select(t => t.TemplateName).Where(n => n != null).Distinct().OrderBy(n => n).ToList();
            result["templates"] = new JObject
            {
                ["placeableCount"] = placeable.Count,
                ["placeable"] = placeable,
                ["allCount"] = all.Count,
                ["all"] = new JArray(all.Cast<object>().ToArray())
            };
        }

        private static string Kind(Character character)
        {
            if (character.GetComponent<Bot>() != null) return "bot";
            if (character.GetComponent<Child>() != null) return "child";
            return "adult";
        }

        private static string TemplateName(Character character)
        {
            return character.GetComponent<TemplateSpec>()?.TemplateName;
        }

        private static string TemplateName(Timberborn.BlueprintSystem.Blueprint blueprint)
        {
            return blueprint.GetSpec<TemplateSpec>()?.TemplateName ?? blueprint.Name;
        }

        /// <summary>The renderer the game puts the faction coat on (CharacterMaterialModifier uses the same lookup).</summary>
        private static Renderer BodyRenderer(Character character)
        {
            return character.GameObject.GetComponentInChildren<Renderer>(true);
        }

        private JObject Describe(Character character)
        {
            var body = BodyRenderer(character);
            var o = new JObject
            {
                ["kind"] = Kind(character),
                ["name"] = character.FirstName,
                ["template"] = TemplateName(character),
                ["age"] = character.Age,
                ["object"] = character.GameObject.name
            };
            if (body)
            {
                var b = DescribeRenderer(body);
                var description = body.GetComponentInParent<TimbermeshDescription>(true);
                b["modelAsset"] = description ? description.ModelName : null;
                b["baseMapAsset"] = CoatPath(body);
                o["body"] = b;
            }
            var needManager = character.GetComponent<NeedManager>();
            if (needManager != null)
            {
                var needs = new JObject();
                foreach (var need in needManager.NeedSpecs)
                    if (needManager.NeedIsActive(need.Id)) needs[need.Id] = Math.Round(needManager.GetNeedPoints(need.Id), 2);
                o["needs"] = needs;
            }
            var behaviorManager = character.GetComponent<BehaviorManager>();
            if (behaviorManager != null)
            {
                o["behavior"] = behaviorManager.RunningBehavior.Name;
                o["executor"] = behaviorManager.RunningExecutor.Name;
            }
            var models = new JArray();
            foreach (var d in character.GameObject.GetComponentsInChildren<TimbermeshDescription>(true))
                if (!models.Any(m => (string)m == d.ModelName)) models.Add(d.ModelName);
            o["models"] = models;
            var visible = new JArray();
            var hidden = new JArray();
            foreach (var r in character.GameObject.GetComponentsInChildren<Renderer>(true))
            {
                if (r == body) continue;
                if (r.gameObject.activeInHierarchy && r.enabled) { if (visible.Count < 12) visible.Add(DescribeRenderer(r)); }
                else if (hidden.Count < 40) hidden.Add(r.gameObject.name);
            }
            o["otherVisibleRenderers"] = visible;
            o["hiddenRenderers"] = hidden;
            return o;
        }

        /// <summary>The faction texture asset path of the coat on this renderer, or null if it is not one of the faction's coats.</summary>
        private string CoatPath(Renderer renderer)
        {
            var faction = _factionService.Current;
            if (faction == null) return null;
            if (_coatPaths == null)
            {
                _coatPaths = new Dictionary<Texture, string>();
                foreach (var t in faction.Textures.Concat(faction.ChildTextures))
                    if (t.Asset && !_coatPaths.ContainsKey(t.Asset)) _coatPaths[t.Asset] = t.Path;
            }
            foreach (var material in renderer.sharedMaterials)
            {
                if (!material || !material.HasProperty("_BaseMap")) continue;
                var texture = material.GetTexture("_BaseMap");
                if (texture && _coatPaths.TryGetValue(texture, out string path)) return path;
            }
            return null;
        }

        private static string FindModelPath(Timberborn.BlueprintSystem.Blueprint blueprint)
        {
            var spec = blueprint.GetSpec<TimbermeshSpec>();
            if (spec?.Model != null) return spec.Model.Path;
            foreach (var child in blueprint.Children)
            {
                string path = FindModelPath(child);
                if (path != null) return path;
            }
            return null;
        }

        /// <summary>Which asset providers can supply this path: built-in (game) and/or mods, with load order. The highest order wins.</summary>
        private JArray AssetProviders<T>(string path) where T : UnityEngine.Object
        {
            var list = new JArray();
            string normalized = AssetPathHelper.NormalizePath(path);
            foreach (var provider in _assetProviders)
            {
                try
                {
                    if (provider.TryLoad<T>(normalized, out var asset))
                        list.Add(new JObject { ["provider"] = provider.GetType().Name, ["builtIn"] = provider.IsBuiltIn, ["order"] = asset.Order });
                }
                catch (Exception e)
                {
                    list.Add(new JObject { ["provider"] = provider.GetType().Name, ["error"] = e.GetType().Name });
                }
            }
            return list;
        }

        private static JObject DescribeRenderer(Renderer renderer)
        {
            var o = new JObject { ["object"] = renderer.gameObject.name, ["type"] = renderer.GetType().Name };
            Mesh mesh = null;
            if (renderer is SkinnedMeshRenderer skinned) mesh = skinned.sharedMesh;
            else
            {
                var filter = renderer.GetComponent<MeshFilter>();
                if (filter) mesh = filter.sharedMesh;
            }
            o["mesh"] = mesh ? mesh.name : null;
            if (mesh) o["vertices"] = mesh.vertexCount;
            var materials = new JArray();
            foreach (var material in renderer.sharedMaterials)
            {
                if (!material) continue;
                Texture baseMap = material.HasProperty("_BaseMap") ? material.GetTexture("_BaseMap") : material.HasProperty("_MainTex") ? material.mainTexture : null;
                materials.Add(new JObject
                {
                    ["material"] = material.name,
                    ["shader"] = material.shader ? material.shader.name : null,
                    ["baseMap"] = baseMap ? baseMap.name : null
                });
                if (o["baseMap"] == null && baseMap)
                {
                    o["baseMap"] = baseMap.name;
                    o["baseMapSize"] = baseMap.width + "x" + baseMap.height;
                }
            }
            o["materials"] = materials;
            return o;
        }
    }
}
