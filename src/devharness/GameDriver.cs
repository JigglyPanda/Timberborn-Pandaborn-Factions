using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Bindito.Core;
using Newtonsoft.Json.Linq;
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
using Timberborn.Debugging;
using Timberborn.EntitySystem;
using Timberborn.GameDistricts;
using Timberborn.GameFactionSystem;
using Timberborn.SingletonSystem;
using Timberborn.TemplateSystem;
using Timberborn.TerrainSystem;
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
        private enum Phase { WaitingForStart, Settling, StartShots, Running, EndShots, Finishing, Done }

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
        private readonly DistrictCenterRegistry _districtCenterRegistry;
        private readonly ITerrainService _terrainService;
        private readonly PreviewPlacerFactory _previewPlacerFactory;
        private readonly BlockObjectPlacerService _blockObjectPlacerService;
        private readonly ConstructionFactory _constructionFactory;

        private Phase _phase = Phase.WaitingForStart;
        private bool _primaryUiShown;
        private float _loadedAt, _phaseStartedAt, _runStartedAt, _runStartHours;
        private readonly Queue<ShotRequest> _shotQueue = new Queue<ShotRequest>();
        private readonly List<ShotRequest> _timedShots = new List<ShotRequest>();
        private readonly List<string> _pendingScreenFiles = new List<string>();
        private float _waitUntil;

        public GameDriver(EventBus eventBus, SpeedManager speedManager, IDayNightCycle dayNightCycle, DevModeManager devModeManager,
                          FactionService factionService, CharacterPopulation characterPopulation, BeaverPopulation beaverPopulation,
                          BotPopulation botPopulation, TemplateService templateService, CameraService cameraService,
                          DistrictCenterRegistry districtCenterRegistry, ITerrainService terrainService,
                          PreviewPlacerFactory previewPlacerFactory, BlockObjectPlacerService blockObjectPlacerService,
                          ConstructionFactory constructionFactory)
        {
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
                    _speedManager.ChangeSpeed(request.Speed);
                    Harness.Info("running at speed " + request.Speed + " for " + DescribeRun(request));
                    Harness.Result["run"] = new JObject { ["startDay"] = Math.Round(_dayNightCycle.PartialDayNumber, 3) };
                    Enter(Phase.Running);
                    return;

                case Phase.Running:
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

        private void Enter(Phase phase)
        {
            _phase = phase;
            _phaseStartedAt = Time.unscaledTime;
            Harness.Info("phase " + phase);
        }

        private bool RunIsOver(Request request, float now)
        {
            float real = now - _runStartedAt;
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
            var specs = _templateService.GetAll<PlaceableBlockObjectSpec>().ToList();
            var used = new List<Vector3Int>();
            foreach (var r in requests)
            {
                var entry = new JObject { ["template"] = r.Template, ["finished"] = r.Finished, ["placed"] = false };
                results.Add(entry);
                try
                {
                    var spec = specs.FirstOrDefault(s => TemplateName(s.Blueprint) == r.Template)
                               ?? specs.FirstOrDefault(s => s.GetSpec<TemplateSpec>()?.IsNamed(r.Template) == true);
                    if (spec == null) { entry["error"] = "template not available to this faction"; continue; }
                    var placement = FindPlacement(spec, anchor, r, used);
                    if (!placement.HasValue) { entry["error"] = "no valid spot found near the district center"; continue; }
                    var builder = new EntitySetup.Builder(spec.Blueprint);
                    if (spec.HasSpec<BuildingSpec>())
                    {
                        if (r.Finished) _constructionFactory.CreateAsFinished(builder, placement.Value);
                        else _constructionFactory.CreateAsUnfinished(builder, placement.Value);
                    }
                    else
                    {
                        _blockObjectPlacerService.GetMatchingPlacer(spec.GetSpec<BlockObjectSpec>()).Place(builder, placement.Value);
                    }
                    var c = placement.Value.Coordinates;
                    used.Add(c);
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
            if (body) o["body"] = DescribeRenderer(body);
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
