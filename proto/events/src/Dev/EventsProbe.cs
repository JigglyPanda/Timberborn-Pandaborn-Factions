using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using Bindito.Core;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Pandaborn.Core;
using Timberborn.BaseComponentSystem;
using Timberborn.BehaviorSystem;
using Timberborn.BlockSystem;
using Timberborn.Characters;
using Timberborn.EntitySystem;
using Timberborn.Forestry;
using Timberborn.GameDistricts;
using Timberborn.Goods;
using Timberborn.Growing;
using Timberborn.InventorySystem;
using Timberborn.NaturalResources;
using Timberborn.NaturalResourcesLifecycle;
using Timberborn.Planting;
using Timberborn.SelectionSystem;
using Timberborn.SingletonSystem;
using Timberborn.SoilMoistureSystem;
using Timberborn.TemplateSystem;
using Timberborn.TerrainSystem;
using Timberborn.TimeSystem;
using Timberborn.UILayoutSystem;
using Timberborn.WeatherSystem;
using Timberborn.WorkSystem;
using UnityEngine;

namespace Pandaborn.Events.Dev
{
    [Context("Game")]
    public class EventsDevConfigurator : Configurator
    {
        protected override void Configure()
        {
            if (HarnessBridge.Active && HarnessBridge.RawRequest?["events"] is JObject) Bind<EventsProbe>().AsSingleton();
        }
    }

    /// <summary>
    /// Dev only (never shipped). Drives and records the two events in a harness run, from the request's "events" section
    /// ("reload" overrides it after a save is loaded):
    /// <code>
    /// { "stock": { good: amount },  "fields": [ { "template", "count", "near", "grown", "mark", "cuttingArea", "radius" } ],
    ///   "actions": [ { "atRunHour" | "day"+"hour", "do": "...", ... } ],  "shots": [ { "name", time, "select" } ] }
    /// </code>
    /// Actions: announce, flowerNow, setSetting, callFestival, autoCall, resetCycleRule, setTradition, stock, seedlings,
    /// jumpToHour, startDrought, writeDevSwitch (pandaborn.dev.txt of the running copy, for the next launch), fakeMidEvent.
    /// Several districts: "district": n on stock, spawnAdults and callFestival (and "square:n" as a shot target) picks the
    /// n-th finished district centre, 0 the first. The probe does not build a district: the harness places the second
    /// district centre and its buildings (docs/tech/events.md 14, "What a two-district scenario needs").
    /// Everything that touches the Festival or Flowering module lives in FestivalProbe / FloweringProbe and is only called
    /// when that module's assembly was loaded by the bootstrap, so the probe also runs with a module forced off.
    /// Output: events.json (events_reload.json after a reload) in the run folder, every in-game hour.
    /// </summary>
    public class EventsProbe : ILoadableSingleton, IUpdatableSingleton
    {
        private readonly EventBus _eventBus;
        private readonly IDayNightCycle _dayNightCycle;
        private readonly DistrictCenterRegistry _districtCenterRegistry;
        private readonly EntityRegistry _entityRegistry;
        private readonly EntitySelectionService _entitySelectionService;
        private readonly NaturalResourceFactory _naturalResourceFactory;
        private readonly PlantingService _plantingService;
        private readonly TreeCuttingArea _treeCuttingArea;
        private readonly ISoilMoistureService _soilMoistureService;
        private readonly ITerrainService _terrainService;
        private readonly PandabornStore _store;
        private readonly WeatherService _weatherService;
        private readonly WeatherFastForwarder _weatherFastForwarder;
        private readonly EntityService _entityService;
        private readonly Timberborn.Beavers.BeaverFactory _beaverFactory;
        private readonly Timberborn.Navigation.IDistrictService _districtService;
        private readonly Timberborn.CameraSystem.CameraService _cameraService;

        private readonly JObject _config;
        private readonly JObject _out = new JObject();
        private readonly JArray _samples = new JArray();
        private readonly JArray _events = new JArray();
        private readonly JArray _shotsTaken = new JArray();
        private readonly List<JObject> _actions = new List<JObject>();
        private readonly List<JObject> _shots = new List<JObject>();
        private readonly Queue<JObject> _shotQueue = new Queue<JObject>();

        private readonly Dictionary<string, float> _actionDone = new Dictionary<string, float>(StringComparer.Ordinal);
        private bool _primaryUi;
        private float _primaryUiAt;
        private bool _started;
        private float _startHours;
        private int _startDay;
        private int _lastHour = int.MinValue;
        private JObject _activeShot;
        private int _shotStep;
        private float _shotWait;

        public EventsProbe(EventBus eventBus, IDayNightCycle dayNightCycle, DistrictCenterRegistry districtCenterRegistry, EntityRegistry entityRegistry,
                           EntitySelectionService entitySelectionService, NaturalResourceFactory naturalResourceFactory, PlantingService plantingService,
                           TreeCuttingArea treeCuttingArea, ISoilMoistureService soilMoistureService, ITerrainService terrainService, PandabornStore store,
                           WeatherService weatherService, WeatherFastForwarder weatherFastForwarder, EntityService entityService,
                           Timberborn.Beavers.BeaverFactory beaverFactory, Timberborn.Navigation.IDistrictService districtService,
                           Timberborn.CameraSystem.CameraService cameraService)
        {
            _cameraService = cameraService;
            _beaverFactory = beaverFactory;
            _districtService = districtService;
            _eventBus = eventBus;
            _dayNightCycle = dayNightCycle;
            _districtCenterRegistry = districtCenterRegistry;
            _entityRegistry = entityRegistry;
            _entitySelectionService = entitySelectionService;
            _naturalResourceFactory = naturalResourceFactory;
            _plantingService = plantingService;
            _treeCuttingArea = treeCuttingArea;
            _soilMoistureService = soilMoistureService;
            _terrainService = terrainService;
            _store = store;
            _weatherService = weatherService;
            _weatherFastForwarder = weatherFastForwarder;
            _entityService = entityService;
            _config = HarnessBridge.Config;
        }

        public static bool FestivalLoaded => Loaded("Pandaborn.Festival");

        public static bool FloweringLoaded => Loaded("Pandaborn.Flowering");

        private static bool Loaded(string name) => AppDomain.CurrentDomain.GetAssemblies().Any(a => a.GetName().Name == name);

        public void Load()
        {
            _eventBus.Register(this);
            _out["config"] = _config.DeepClone();
            _out["loadSave"] = HarnessBridge.LoadSave;
            if (_config["actions"] is JArray actions) _actions.AddRange(actions.OfType<JObject>());
            if (_config["shots"] is JArray shots) _shots.AddRange(shots.OfType<JObject>());
        }

        [OnEvent]
        public void OnShowPrimaryUI(ShowPrimaryUIEvent e)
        {
            _primaryUi = true;
            _primaryUiAt = Time.unscaledTime;
        }

        public void UpdateSingleton()
        {
            try
            {
                if (!_primaryUi || Time.unscaledTime - _primaryUiAt < 3f) return;
                if (!_started) Begin();
                RunActions();
                QueueShots();
                StepShots();
                int hour = Mathf.FloorToInt(_dayNightCycle.PartialDayNumber * 24f);
                if (hour != _lastHour)
                {
                    _lastHour = hour;
                    Sample();
                    Write();
                }
            }
            catch (Exception e)
            {
                Debug.LogError("[Pandaborn.Events.Dev] probe step failed: " + e);
                Event("probeError", e.GetType().Name + ": " + e.Message);
            }
        }

        private float RunHour => _dayNightCycle.PartialDayNumber * 24f - _startHours;

        private void Begin()
        {
            _started = true;
            _startHours = _dayNightCycle.PartialDayNumber * 24f;
            _startDay = _dayNightCycle.DayNumber;
            if (HarnessBridge.LoadSave && _store.TryGet("EventsProbe", out _, out string payload))
            {
                var v = Payload.Parse(payload);
                if (v.TryGetValue("startDay", out var d) && int.TryParse(d, out int day)) _startDay = day;
            }
            else _store.Set("EventsProbe", 1, "startDay=" + _startDay.ToString(CultureInfo.InvariantCulture));
            _out["start"] = new JObject { ["day"] = _dayNightCycle.DayNumber, ["hour"] = Math.Round(_dayNightCycle.HoursPassedToday, 2), ["runStartDay"] = _startDay };
            var features = new JObject
            {
                ["festivalAssembly"] = FestivalLoaded,
                ["floweringAssembly"] = FloweringLoaded,
                ["features"] = string.Join("; ", FeatureRegistry.All.Select(s => s.ToString())),
                ["degraded"] = string.Join("; ", FeatureRegistry.Degraded.Select(kv => kv.Key + ": " + kv.Value)),
                ["noData"] = string.Join("; ", FeatureRegistry.NoData.Select(kv => kv.Key + ": " + kv.Value)),
                ["owner"] = FeatureRegistry.Owner
            };
            if (FestivalLoaded) FestivalProbe.Features(features);
            if (FloweringLoaded) FloweringProbe.Features(features);
            _out["features"] = features;
            if (!HarnessBridge.LoadSave)
            {
                Stock(_config["stock"] as JObject);
                Fields();
            }
            HarnessBridge.Info("events probe started on day " + _dayNightCycle.DayNumber + " hour " + _dayNightCycle.HoursPassedToday.ToString("0.0"));
        }

        // ------------------------------------------------------------------ setup

        /// <summary>The n-th finished district centre (0 the first), or null.</summary>
        public Timberborn.GameDistricts.DistrictCenter DistrictAt(int index)
        {
            var centers = _districtCenterRegistry.FinishedDistrictCenters;
            return index >= 0 && index < centers.Count ? centers[index] : null;
        }

        private static int DistrictIndex(JObject a) => a?["district"]?.Value<int>() ?? 0;

        private void Stock(JObject stock, int district = 0)
        {
            if (stock == null) return;
            var center = DistrictAt(district);
            if (center == null) { Event("stock", "no district center " + district); return; }
            var given = new List<string>();
            foreach (var p in stock.Properties())
            {
                var inventory = center.GetComponent<Inventories>()?.EnabledInventories.FirstOrDefault(i => i.Takes(p.Name) || i.Gives(p.Name));
                if (inventory == null) { given.Add(p.Name + ": no inventory"); continue; }
                inventory.GiveExistingIgnoringCapacity(new GoodAmount(p.Name, p.Value.Value<int>()));
                given.Add(p.Name + " " + inventory.AmountInStock(p.Name));
            }
            Event("stock", string.Join(", ", given));
        }

        private void Fields()
        {
            if (!(_config["fields"] is JArray fields)) return;
            foreach (var f in fields.OfType<JObject>())
            {
                var made = SpawnPlants((string)f["template"], f["count"]?.Value<int>() ?? 6, (string)f["near"], f["radius"]?.Value<int>() ?? 6,
                                       f["grown"]?.Value<bool>() ?? true, f["mark"]?.Value<bool>() ?? true, f["cuttingArea"]?.Value<bool>() ?? false);
                Event("field", f["template"] + ": " + made.Count + " near " + f["near"] + "; moist " + made.Count(c => _soilMoistureService.SoilIsMoist(c)));
            }
        }

        public List<Vector3Int> SpawnPlants(string template, int count, string near, int radius, bool grown, bool mark, bool cutting)
        {
            var made = new List<Vector3Int>();
            var anchor = FindBuilding(near);
            Vector3Int origin = anchor ? anchor.GetComponent<BlockObject>().Coordinates
                                       : _districtCenterRegistry.FinishedDistrictCenters.First().GetComponent<BlockObject>().Coordinates;
            var candidates = new List<Vector3Int>();
            for (int r = 2; r <= radius; r++)
                for (int dx = -r; dx <= r; dx++)
                    for (int dy = -r; dy <= r; dy++)
                    {
                        if (Math.Max(Math.Abs(dx), Math.Abs(dy)) != r) continue;
                        for (int dz = -1; dz <= 1; dz++)
                        {
                            var c = new Vector3Int(origin.x + dx, origin.y + dy, origin.z + dz);
                            if (_terrainService.Contains(c) && _terrainService.OnGround(c)) candidates.Add(c);
                        }
                    }
            foreach (var c in candidates.OrderByDescending(c => _soilMoistureService.SoilIsMoist(c)))
            {
                if (made.Count >= count) break;
                if (_plantingService.IsResourceAt(c)) continue;
                var plant = _naturalResourceFactory.SpawnIgnoringConstraints(template, c);
                if (plant == null) continue;
                if (grown) plant.GetComponent<Growable>()?.IncreaseGrowthProgress(1f);
                if (mark) _plantingService.SetPlantingCoordinates(c, template);
                made.Add(c);
            }
            if (cutting && made.Count > 0) _treeCuttingArea.AddCoordinates(made);
            return made;
        }

        public BaseComponent FindBuilding(string template)
        {
            if (string.IsNullOrEmpty(template)) return null;
            return _entityRegistry.Entities.FirstOrDefault(e => e.GetComponent<TemplateSpec>()?.TemplateName == template);
        }

        // ------------------------------------------------------------------ actions

        private void RunActions()
        {
            for (int i = _actions.Count - 1; i >= 0; i--)
            {
                var a = _actions[i];
                if (!Due(a)) continue;
                _actions.RemoveAt(i);
                string what = (string)a["do"];
                string result;
                try { result = Do(what, a); }
                catch (Exception e) { result = "threw " + e.GetType().Name + ": " + e.Message; Debug.LogError("[Pandaborn.Events.Dev] action " + what + ": " + e); }
                Event("action:" + what, result);
                if (a["id"] != null) _actionDone[(string)a["id"]] = _dayNightCycle.PartialDayNumber * 24f;
            }
        }

        private bool Due(JObject a)
        {
            // "after": "<id of an earlier action>", "delayHours": h  (in-game hours after that action ran; survives time jumps)
            if (a["after"] != null)
                return _actionDone.TryGetValue((string)a["after"], out float at) && _dayNightCycle.PartialDayNumber * 24f >= at + (a["delayHours"]?.Value<float>() ?? 0f);
            if (a["atRunHour"] != null) return RunHour >= a["atRunHour"].Value<float>();
            if (a["day"] != null)
            {
                int day = _dayNightCycle.DayNumber - _startDay;
                return day > a["day"].Value<int>() || (day == a["day"].Value<int>() && _dayNightCycle.HoursPassedToday >= (a["hour"]?.Value<float>() ?? 0f));
            }
            return true;
        }

        private string Do(string what, JObject a)
        {
            switch (what)
            {
                case "writeDevSwitch":
                {
                    string file = Path.Combine(FeatureRegistry.Owner, "pandaborn.dev.txt");
                    File.WriteAllText(file, ((string)a["value"] ?? "").Replace(';', '\n'));
                    return "written for the next launch: " + file + ": " + a["value"];
                }
                case "stock": Stock(a["goods"] as JObject, DistrictIndex(a)); return "ok";
                case "setRecipe":
                {
                    var m = FindBuilding((string)a["building"])?.GetComponent<Timberborn.Workshops.Manufactory>();
                    if (m == null) return "no such workshop";
                    var r = m.ProductionRecipes.FirstOrDefault(x => x.Id == (string)a["recipe"]);
                    if (r == null) return "no recipe " + a["recipe"] + " (has " + string.Join(", ", m.ProductionRecipes.Select(x => x.Id)) + ")";
                    m.SetRecipe(r);
                    return "recipe " + r.Id;
                }
                case "jumpToHour":
                {
                    float target = a["hour"]?.Value<float>() ?? 23.5f;
                    float delta = target - _dayNightCycle.HoursPassedToday;
                    if (delta <= 0f) return "already past " + target;
                    _dayNightCycle.JumpTimeInHours(delta);
                    return "jumped to day " + _dayNightCycle.DayNumber + " hour " + _dayNightCycle.HoursPassedToday.ToString("0.00");
                }
                case "startDrought":
                {
                    if (!_weatherService.IsHazardousWeather) _weatherFastForwarder.JumpToNextSeason();
                    return "hazardous " + _weatherService.IsHazardousWeather + ", day " + _dayNightCycle.DayNumber + " hour " + _dayNightCycle.HoursPassedToday.ToString("0.0");
                }
                case "spawnAdults":
                {
                    // grown colonists at the district centre (a crowd for the square; never on a loaded save's run)
                    var dc = DistrictAt(DistrictIndex(a));
                    if (dc == null) return "no district centre " + DistrictIndex(a);
                    int n = a["count"]?.Value<int>() ?? 10;
                    var at = dc.GetComponent<BlockObjectCenter>().WorldCenterGrounded;
                    // on the district's own roads: the game assigns an unassigned colonist to the district it stands in (the
                    // festival block's per-district counts show where they ended up)
                    for (int i = 0; i < n; i++) _beaverFactory.CreateAdult(_districtService.GetRandomDestinationInDistrict(dc.District, at), 0.3f);
                    return n + " adults in district " + DistrictIndex(a) + " (" + dc.DistrictName + ")";
                }
                case "seedlings":
                {
                    var made = SpawnPlants((string)a["template"], a["count"]?.Value<int>() ?? 4, (string)a["near"], a["radius"]?.Value<int>() ?? 8, false,
                                           a["mark"]?.Value<bool>() ?? false, false);
                    return made.Count + " young " + a["template"];
                }
            }
            string result = null;
            if (FestivalLoaded) result = FestivalProbe.Do(what, a, _dayNightCycle, DistrictAt(DistrictIndex(a)), a?["district"] != null);
            if (result == null && FloweringLoaded) result = FloweringProbe.Do(what, a, this);
            if (result == null && what == "fakeMidEvent") result = FakeMidEvent(a);
            return result ?? (FestivalLoaded || FloweringLoaded ? "unknown action" : "modules off");
        }

        /// <summary>
        /// The state a save made mid-festival and mid-flowering carries, written while both modules are off (the Core store
        /// keeps any feature's entry): a festival whose day ended yesterday (or runs today), shoot bamboo in flower since
        /// half a day. For the "back on" load test.
        /// </summary>
        private string FakeMidEvent(JObject a)
        {
            int day = _dayNightCycle.DayNumber + (a["festivalDayOffset"]?.Value<int>() ?? -1);
            _store.Set("Festival", 1, "phase=Running;day=" + day + ";grand=1;last=1;tradition=0;auto=0;count=0");
            float flowered = _dayNightCycle.PartialDayNumber - 0.5f;
            _store.Set("Flowering", 1, "setting=normal;phase=Flowering;next=8;nextSpecies=1;species=PandabornShootBamboo.Inkpaws;day="
                                        + flowered.ToString("0.###", CultureInfo.InvariantCulture) + ";last=1");
            int twins = 0;
            foreach (var e in _entityRegistry.Entities.ToList())
            {
                if (Template(e) != "PandabornShootBamboo.Inkpaws") continue;
                var g = e.GetComponent<Growable>();
                if (g == null || !g.IsGrown) continue;
                var c = e.GetComponent<BlockObject>().Coordinates;
                _entityService.Delete(e);
                var twin = _naturalResourceFactory.SpawnIgnoringConstraints("PandabornShootBambooInFlower.Inkpaws", c);
                if (twin != null) { twin.GetComponent<Growable>()?.IncreaseGrowthProgress(1f); twins++; }
            }
            return "store set (festival day " + day + ", flowering since " + flowered.ToString("0.00") + "), twins " + twins;
        }

        // ------------------------------------------------------------------ samples

        private void Sample()
        {
            var s = new JObject
            {
                ["runHour"] = Math.Round(RunHour, 2),
                ["day"] = _dayNightCycle.DayNumber - _startDay,
                ["hour"] = Math.Round(_dayNightCycle.HoursPassedToday, 2),
                ["hazard"] = _weatherService.IsHazardousWeather,
                ["raw"] = Raw()
            };
            if (FestivalLoaded) FestivalProbe.Sample(s);
            if (FloweringLoaded) FloweringProbe.Sample(s);
            s["store"] = new JArray(_store.Features.Where(f => f == "Festival" || f == "Flowering")
                                          .Select(f => { _store.TryGet(f, out int v, out string p); return (object)(f + "|" + v + "|" + p); }).ToArray());
            _samples.Add(s);
        }

        /// <summary>State read without the modules: characters' behaviours and workplaces, bamboo by template, goods.</summary>
        private JObject Raw()
        {
            var behaviors = new JObject();
            var working = new JObject();
            int characters = 0, ringtails = 0;
            var plants = new JObject();
            foreach (var e in _entityRegistry.Entities)
            {
                if (e.GetComponent<Character>() != null)
                {
                    characters++;
                    string t = Template(e);
                    if (t.StartsWith("Ringtail", StringComparison.Ordinal)) ringtails++;
                    string b = Behavior(e);
                    behaviors[b] = (behaviors[b]?.Value<int>() ?? 0) + 1;
                    var worker = e.GetComponent<Worker>();
                    if (worker != null && worker.Employed && worker.Workplace && IsWorkingBehavior(b))
                    {
                        string w = Template(worker.Workplace) + (t.StartsWith("Ringtail", StringComparison.Ordinal) ? " (Ringtail)" : "");
                        working[w] = (working[w]?.Value<int>() ?? 0) + 1;
                    }
                    continue;
                }
                string tp = Template(e);
                if (!tp.Contains("Bamboo")) continue;
                var living = e.GetComponent<LivingNaturalResource>();
                if (living == null) continue;
                var g = e.GetComponent<Growable>();
                string key = living.IsDead ? "dead" : g != null && !g.IsGrown ? "young" : "grown";
                // plants on tiles without a planting mark are counted apart ("... (wild)"): the reseeding rule is about them
                var block = e.GetComponent<BlockObject>();
                if (block != null && !_plantingService.IsResourceAt(block.Coordinates)) tp += " (wild)";
                var o = plants[tp] as JObject ?? new JObject { ["grown"] = 0, ["young"] = 0, ["dead"] = 0 };
                o[key] = o[key].Value<int>() + 1;
                plants[tp] = o;
            }
            return new JObject
            {
                ["characters"] = characters, ["ringtails"] = ringtails, ["behaviors"] = behaviors, ["working"] = working, ["plants"] = plants,
                ["stock"] = new JObject
                {
                    ["seed"] = StoreAmount("PandabornBambooSeed"), ["seedCakes"] = StoreAmount("PandabornBambooSeedCakes"),
                    ["riceFlour"] = StoreAmount("PandabornRiceFlour"), ["lanterns"] = StoreAmount("PandabornPaperLantern"),
                    ["fireworks"] = StoreAmount("Fireworks"), ["water"] = StoreAmount("Water")
                }
            };
        }

        public static bool IsWorkingBehavior(string b) =>
            b.Contains("Workplace") || b.Contains("Build") || b.Contains("Haul") || b.Contains("Plant") || b.Contains("Cut")
            || b.Contains("Gather") || b.Contains("Produce") || b.Contains("Labor") || b.Contains("Harvest") || b.Contains("Worker")
            || b.Contains("Empty") || b.Contains("Fill") || b.Contains("Deliver") || b.Contains("Construct") || b.Contains("Retriev")
            || b.Contains("Manufactory") || b.Contains("Yield");

        public static string Behavior(BaseComponent c)
        {
            try { return c.GetComponent<BehaviorManager>()?.RunningBehavior.Name ?? "-"; }
            catch (Exception) { return "?"; }
        }

        public static string Template(BaseComponent c) => c ? c.GetComponent<TemplateSpec>()?.TemplateName ?? "?" : "?";

        private int StoreAmount(string goodId)
        {
            int sum = 0;
            foreach (var center in _districtCenterRegistry.FinishedDistrictCenters)
            {
                var registry = center.GetComponent<DistrictInventoryRegistry>();
                try { foreach (var inv in registry.ActiveInventoriesWithStock(goodId)) sum += inv.AmountInStock(goodId); }
                catch (Exception) { }
            }
            return sum;
        }

        // ------------------------------------------------------------------ shots

        private void QueueShots()
        {
            for (int i = _shots.Count - 1; i >= 0; i--)
            {
                if (!Due(_shots[i])) continue;
                _shotQueue.Enqueue(_shots[i]);
                _shots.RemoveAt(i);
            }
        }

        private void StepShots()
        {
            if (Time.unscaledTime < _shotWait) return;
            if (_activeShot == null)
            {
                if (_shotQueue.Count == 0) return;
                _activeShot = _shotQueue.Dequeue();
                _shotStep = 0;
            }
            string name = (string)_activeShot["name"] ?? "shot";
            switch (_shotStep++)
            {
                case 0:
                    var target = FindTarget((string)_activeShot["select"] ?? "none");
                    _shotsTaken.Add(new JObject { ["name"] = name, ["runHour"] = Math.Round(RunHour, 2), ["day"] = _dayNightCycle.DayNumber - _startDay,
                                                  ["hour"] = Math.Round(_dayNightCycle.HoursPassedToday, 2), ["target"] = target ? Template(target) : null });
                    if (target) _entitySelectionService.SelectAndFocusOn(target);
                    else _entitySelectionService.Unselect();
                    // optional camera: "focus" (a target to centre on without selecting it), "zoom" (ZoomLevel),
                    // "vAngle" / "hAngle" (degrees); the camera stays there for later shots
                    var entryCam = (JObject)_shotsTaken.Last;
                    if (_activeShot["focus"] != null)
                    {
                        var f = FindTarget((string)_activeShot["focus"]);
                        if (f) _cameraService.MoveTargetTo(f.Transform.position);
                    }
                    if (_activeShot["zoom"] != null) _cameraService.ZoomLevel = _activeShot["zoom"].Value<float>();
                    if (_activeShot["vAngle"] != null) _cameraService.VerticalAngle = _activeShot["vAngle"].Value<float>();
                    if (_activeShot["hAngle"] != null) _cameraService.HorizontalAngle = _activeShot["hAngle"].Value<float>();
                    entryCam["camera"] = "zoom " + _cameraService.ZoomLevel.ToString("0.00") + ", v " + _cameraService.VerticalAngle.ToString("0.0")
                                         + ", h " + _cameraService.HorizontalAngle.ToString("0.0") + ", speed " + Time.timeScale.ToString("0.00");
                    _shotWait = Time.unscaledTime + 1.5f;
                    return;
                case 1:
                    string dir = HarnessBridge.OutputDir;
                    if (dir != null)
                    {
                        string file = Path.Combine(dir, "ev_" + name + ".png");
                        ScreenCapture.CaptureScreenshot(file);
                        var entry = (JObject)_shotsTaken.Last;
                        entry["file"] = Path.GetFileName(file);
                        if (FestivalLoaded) FestivalProbe.Panels(entry);
                        if (FloweringLoaded) FloweringProbe.Panels(entry);
                    }
                    _shotWait = Time.unscaledTime + 0.7f;
                    return;
                default:
                    _entitySelectionService.Unselect();
                    _activeShot = null;
                    _shotWait = Time.unscaledTime + 0.3f;
                    Write();
                    return;
            }
        }

        private BaseComponent FindTarget(string what)
        {
            if (what.StartsWith("building:", StringComparison.Ordinal)) return FindBuilding(what.Substring(9));
            if (what == "ringtail") return _entityRegistry.Entities.FirstOrDefault(e => Template(e).StartsWith("RingtailAdult", StringComparison.Ordinal));
            BaseComponent target = null;
            if (FestivalLoaded && what.StartsWith("square:", StringComparison.Ordinal) && int.TryParse(what.Substring(7), out int di))
                return FestivalProbe.SquareOf(DistrictAt(di));
            if (FestivalLoaded) target = FestivalProbe.FindTarget(what);
            if (!target && FloweringLoaded) target = FloweringProbe.FindTarget(what);
            if (!target && what == "square") target = FindBuilding("PandabornFestivalSquare.Inkpaws");
            if (!target && what.StartsWith("plant:", StringComparison.Ordinal)) target = FindBuilding(what.Substring(6));
            return target;
        }

        // ------------------------------------------------------------------ output

        public void Event(string kind, string text)
        {
            _events.Add(new JObject { ["runHour"] = _started ? Math.Round(RunHour, 2) : 0, ["day"] = _dayNightCycle.DayNumber - _startDay,
                                      ["hour"] = Math.Round(_dayNightCycle.HoursPassedToday, 2), ["kind"] = kind, ["text"] = text });
            Debug.Log("[Pandaborn.Events.Dev] " + kind + ": " + text);
        }

        private void Write()
        {
            string dir = HarnessBridge.OutputDir;
            if (dir == null) return;
            _out["events"] = _events;
            _out["samples"] = _samples;
            _out["shots"] = _shotsTaken;
            _out["messages"] = new JArray(Messenger.Log.Cast<object>().ToArray());
            try
            {
                File.WriteAllText(Path.Combine(dir, HarnessBridge.LoadSave ? "events_reload.json" : "events.json"), _out.ToString(Formatting.Indented));
                var result = HarnessBridge.Result;
                if (result != null)
                    result["events"] = new JObject { ["samples"] = _samples.Count, ["events"] = _events.Count, ["last"] = _samples.Count > 0 ? _samples.Last.DeepClone() : null };
            }
            catch (Exception e) { Debug.LogError("[Pandaborn.Events.Dev] writing output failed: " + e.Message); }
        }
    }
}
