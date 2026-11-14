using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using Bindito.Core;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Pandaborn.Core;
using Pandaborn.Festival;
using Pandaborn.Flowering;
using Timberborn.BaseComponentSystem;
using Timberborn.BehaviorSystem;
using Timberborn.BlockSystem;
using Timberborn.Characters;
using Timberborn.Common;
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
    /// Dev only (never shipped). Drives and records the two events in a harness run, from the request's "events" section:
    /// <code>
    /// { "stock": { "PandabornPaperLantern": 40, ... },                       // given to the district center (first launch)
    ///   "fields": [ { "template", "count", "near": "&lt;placed building template&gt;", "grown": true, "mark": true,
    ///                 "cuttingArea": false, "radius": 5 } ],
    ///   "actions": [ { "atRunHour": 0.5, "do": "flowerNow|announce|callFestival|resetCycleRule|jumpToHour|seedlings|setTradition|setSetting|autoCall",
    ///                  "hour": 23.5, "template", "count", "near", "value" } ],
    ///   "shots": [ { "name", "day": 1, "hour": 16.7, "select": "square|inflower|plant:&lt;template&gt;|colonist|none" } ],
    ///   "reload": { ... same keys, used when the run loaded the save ... } }
    /// </code>
    /// Times: "atRunHour" counts in-game hours from the probe's start; "day"/"hour" is the day index from the run's first day
    /// (0 = the day the run started) and the hour of that day. Output: events.json (events_reload.json after a reload) in the
    /// run folder, written every in-game hour, plus a summary in result.json under "events".
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

        private readonly JObject _config;
        private readonly JObject _out = new JObject();
        private readonly JArray _samples = new JArray();
        private readonly JArray _events = new JArray();
        private readonly JArray _shotsTaken = new JArray();
        private readonly List<JObject> _actions = new List<JObject>();
        private readonly List<JObject> _shots = new List<JObject>();
        private readonly Queue<JObject> _shotQueue = new Queue<JObject>();
        private readonly List<Growable> _seedlings = new List<Growable>();

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
                           TreeCuttingArea treeCuttingArea, ISoilMoistureService soilMoistureService, ITerrainService terrainService, PandabornStore store)
        {
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
            _config = HarnessBridge.Config;
        }

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

        // the modules may be forced off in a test launch: then their services do not exist
        private static FestivalService Fest => FestivalService.Current != null && FestivalService.Current.Active ? FestivalService.Current : null;

        private static FloweringService Flow => FloweringService.Current != null && FloweringService.Current.Active ? FloweringService.Current : null;

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
            _out["features"] = new JObject
            {
                ["festivalActive"] = Fest != null,
                ["floweringActive"] = Flow != null,
                ["fireworks"] = Fest?.FireworksStatus,
                ["dayOff"] = FestivalGoer.InsertionError ?? "ok",
                ["growthHold"] = GrowthHold.Available ? "ok" : GrowthHold.Unavailable,
                ["features"] = string.Join("; ", FeatureRegistry.All.Select(s => s.ToString()))
            };
            if (!HarnessBridge.LoadSave)
            {
                Stock();
                Fields();
            }
            HarnessBridge.Info("events probe started on day " + _dayNightCycle.DayNumber + " hour " + _dayNightCycle.HoursPassedToday.ToString("0.0"));
        }

        // ------------------------------------------------------------------ setup

        private void Stock() => Stock(_config["stock"] as JObject);

        private void Stock(JObject stock)
        {
            if (stock == null) return;
            var center = _districtCenterRegistry.FinishedDistrictCenters.FirstOrDefault();
            if (center == null) { Event("stock", "no district center"); return; }
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
                string template = (string)f["template"];
                int count = f["count"]?.Value<int>() ?? 6;
                bool grown = f["grown"]?.Value<bool>() ?? true;
                bool mark = f["mark"]?.Value<bool>() ?? true;
                bool cutting = f["cuttingArea"]?.Value<bool>() ?? false;
                int radius = f["radius"]?.Value<int>() ?? 6;
                var made = SpawnPlants(template, count, (string)f["near"], radius, grown, mark, cutting);
                Event("field", template + ": " + made.Count + " planted near " + f["near"] + (grown ? " (grown)" : "") + "; moist "
                               + made.Count(c => _soilMoistureService.SoilIsMoist(c)));
            }
        }

        private List<Vector3Int> SpawnPlants(string template, int count, string near, int radius, bool grown, bool mark, bool cutting)
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
                else { var g = plant.GetComponent<Growable>(); if (g != null) _seedlings.Add(g); }
                if (mark) _plantingService.SetPlantingCoordinates(c, template);
                made.Add(c);
            }
            if (cutting && made.Count > 0) _treeCuttingArea.AddCoordinates(made);
            return made;
        }

        private BaseComponent FindBuilding(string template)
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
            }
        }

        private bool Due(JObject a)
        {
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
            if (what == "writeDevSwitch")
            {
                string dir = EventsDevStarter.ModPath;
                if (dir == null) return "mod path unknown";
                File.WriteAllText(Path.Combine(dir, EventsDevStarter.FileName), ((string)a["value"] ?? "").Replace(';', '\n'));
                return "written for the next launch: " + a["value"];
            }
            if (what == "stock") { Stock(a["goods"] as JObject); return "ok"; }
            if (what == "jumpToHour")
            {
                float target = a["hour"]?.Value<float>() ?? 23.5f;
                float delta = target - _dayNightCycle.HoursPassedToday;
                if (delta <= 0f) return "already past " + target;
                _dayNightCycle.JumpTimeInHours(delta);
                return "jumped " + delta.ToString("0.00") + " h to day " + _dayNightCycle.DayNumber + " hour " + _dayNightCycle.HoursPassedToday.ToString("0.00");
            }
            if (what == "seedlings")
            {
                var made = SpawnPlants((string)a["template"], a["count"]?.Value<int>() ?? 4, (string)a["near"], a["radius"]?.Value<int>() ?? 8, false,
                                       a["mark"]?.Value<bool>() ?? false, false);
                return made.Count + " young " + a["template"];
            }
            if (Fest == null && Flow == null) return "modules off";
            switch (what)
            {
                case "announce": Flow.DevAnnounce(); return Flow.Phase + " " + Flow.Species;
                case "flowerNow": Flow.DevFlowerNow(); return Flow.Phase + " " + Flow.Species + "; twins " + Flow.TwinsMade + ", young died " + Flow.YoungKilled;
                case "setSetting": Flow.SetSetting((string)a["value"]); return Flow.Setting + ", next " + Flow.NextCycle;
                case "resetCycleRule": Fest.DevResetCycleRule(); return "ok";
                case "setTradition": Fest.DevSetTradition(a["value"]?.Value<int>() ?? 0); return "Tradition " + Fest.Tradition;
                case "autoCall": Fest.SetAutoCall(a["value"]?.Value<bool>() ?? true); return "auto " + Fest.AutoCall + ", phase " + Fest.Phase;
                case "callFestival":
                {
                    var square = Fest.Squares.FirstOrDefault(s => s && s.IsFinished);
                    if (square == null) return "no finished square";
                    var stock = FestivalStock.Count(square.District, Fest.Spec);
                    string why = Fest.WhyNot(square, stock);
                    bool ok = Fest.Call(square, auto: false);
                    return (ok ? "called for day " + Fest.FestivalDay + (Fest.Grand ? " (grand)" : "") : "refused: " + why)
                           + "; stock lanterns " + stock.Lanterns + ", dishes " + string.Join(" ", stock.Dishes.Select(d => d.Key + "=" + d.Value))
                           + ", fireworks " + stock.Fireworks;
                }
                default: return "unknown action";
            }
        }

        // ------------------------------------------------------------------ samples

        private void Sample()
        {
            var s = new JObject
            {
                ["runHour"] = Math.Round(RunHour, 2),
                ["day"] = _dayNightCycle.DayNumber - _startDay,
                ["hour"] = Math.Round(_dayNightCycle.HoursPassedToday, 2)
            };
            s["raw"] = Raw();
            if (Fest != null)
            {
                var goers = Fest.Goers.Where(g => g).ToList();
                var doing = new JObject();
                var behaviors = new JObject();
                foreach (var g in goers)
                {
                    string d = string.IsNullOrEmpty(g.Doing) ? "-" : g.Doing;
                    if (!Fest.IsHoliday) d = "-";
                    doing[d] = (doing[d]?.Value<int>() ?? 0) + 1;
                    string b = Behavior(g);
                    behaviors[b] = (behaviors[b]?.Value<int>() ?? 0) + 1;
                }
                string need = Fest.Spec.FestiveNeedId;
                var festive = goers.Select(g => g.NeedPoints(need)).Where(p => p >= 0f).ToList();
                s["festival"] = new JObject
                {
                    ["phase"] = Fest.Phase.ToString(),
                    ["holiday"] = Fest.IsHoliday,
                    ["show"] = Fest.IsShowTime,
                    ["grand"] = Fest.Grand,
                    ["tradition"] = Fest.Tradition,
                    ["lanterns"] = Fest.LanternsLaunched,
                    ["bursts"] = Fest.BurstsLaunched,
                    ["goers"] = goers.Count,
                    ["attended"] = goers.Count(g => Fest.HasAttended(g)),
                    ["festiveAvg"] = festive.Count > 0 ? Math.Round(festive.Average(), 3) : -1,
                    ["festiveMin"] = festive.Count > 0 ? Math.Round(festive.Min(), 3) : -1,
                    ["doing"] = doing,
                    ["behaviors"] = behaviors,
                    ["working"] = goers.Count(g => IsWorking(g)),
                    ["keepWorking"] = goers.Count(g => g.KeepsWorking),
                    ["ringtails"] = goers.Count(g => Template(g).StartsWith("Ringtail", StringComparison.Ordinal)),
                    ["ringtailsWorking"] = goers.Count(g => Template(g).StartsWith("Ringtail", StringComparison.Ordinal) && IsWorking(g)),
                    ["lockedByTradition"] = TraditionToolLocker.LockedCount,
                    ["panel"] = FestivalSquareFragment.ShownText
                };
            }
            if (Flow != null)
            {
                var plants = Flow.Plants.Where(p => p).ToList();
                var twins = Flow.InFlower.Where(t => t).ToList();
                var byTemplate = new JObject();
                foreach (var grp in plants.GroupBy(p => p.Species ?? "?"))
                    byTemplate[grp.Key] = new JObject
                    {
                        ["alive"] = grp.Count(p => !p.IsDead), ["dead"] = grp.Count(p => p.IsDead), ["grown"] = grp.Count(p => p.IsGrown && !p.IsDead)
                    };
                s["flowering"] = new JObject
                {
                    ["setting"] = Flow.Setting,
                    ["phase"] = Flow.Phase.ToString(),
                    ["species"] = Flow.Species,
                    ["nextCycle"] = Flow.NextCycle,
                    ["twinsAlive"] = twins.Count(t => !t.IsDead),
                    ["twinsDead"] = twins.Count(t => t.IsDead),
                    ["seedOnPlants"] = twins.Sum(t => t.SeedLeft),
                    ["seedCut"] = Flow.SeedCut,
                    ["held"] = Flow.HeldNow,
                    ["seedInStore"] = StoreAmount("PandabornBambooSeed"),
                    ["plants"] = byTemplate,
                    ["seedlings"] = new JArray(_seedlings.Where(g => g).Select(g => (object)(Template(g) + " " + g.GrowthProgress.ToString("0.000")
                                                                                              + (g.GetComponent<LivingNaturalResource>().IsDead ? " dead" : ""))).ToArray()),
                    ["young"] = new JArray(plants.Where(p => !p.IsGrown && !p.IsDead).Take(8)
                                                  .Select(p => (object)(p.Species + " " + p.Growable.GrowthProgress.ToString("0.000"))).ToArray()),
                    ["indicator"] = FloweringIndicator.ShownText,
                    ["plantPanel"] = FloweringPlantFragment.ShownText
                };
            }
            s["store"] = new JArray(_store.Features.Where(f => f == "Festival" || f == "Flowering")
                                          .Select(f => { _store.TryGet(f, out int v, out string p); return (object)(f + "|" + v + "|" + p); }).ToArray());
            _samples.Add(s);
        }

        /// <summary>State read without the modules: characters' behaviours, bamboo and twins by template, alive or dead.</summary>
        private JObject Raw()
        {
            var behaviors = new JObject();
            int characters = 0, working = 0;
            var plants = new JObject();
            foreach (var e in _entityRegistry.Entities)
            {
                if (e.GetComponent<Character>() != null)
                {
                    characters++;
                    string b = Behavior(e);
                    behaviors[b] = (behaviors[b]?.Value<int>() ?? 0) + 1;
                    if (IsWorkingBehavior(b)) working++;
                    continue;
                }
                string t = Template(e);
                if (!t.Contains("Bamboo")) continue;
                var living = e.GetComponent<LivingNaturalResource>();
                if (living == null) continue;
                var o = plants[t] as JObject ?? new JObject { ["alive"] = 0, ["dead"] = 0 };
                o[living.IsDead ? "dead" : "alive"] = o[living.IsDead ? "dead" : "alive"].Value<int>() + 1;
                plants[t] = o;
            }
            return new JObject { ["characters"] = characters, ["working"] = working, ["behaviors"] = behaviors, ["plants"] = plants,
                                 ["seedInStore"] = StoreAmount("PandabornBambooSeed") };
        }

        private static bool IsWorking(FestivalGoer g) => IsWorkingBehavior(Behavior(g));

        private static bool IsWorkingBehavior(string b)
        {
            return b.Contains("Workplace") || b.Contains("Build") || b.Contains("Haul") || b.Contains("Plant") || b.Contains("Cut")
                   || b.Contains("Gather") || b.Contains("Produce") || b.Contains("Labor") || b.Contains("Harvest") || b.Contains("Worker")
                   || b.Contains("Empty") || b.Contains("Fill") || b.Contains("Deliver") || b.Contains("Construct");
        }

        private static string Behavior(BaseComponent c)
        {
            try { return c.GetComponent<BehaviorManager>()?.RunningBehavior.Name ?? "-"; }
            catch (Exception) { return "?"; }
        }

        private static string Template(BaseComponent c) => c.GetComponent<TemplateSpec>()?.TemplateName ?? "?";

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
                    _shotsTaken.Add(new JObject { ["name"] = name, ["runHour"] = Math.Round(RunHour, 2), ["hour"] = Math.Round(_dayNightCycle.HoursPassedToday, 2),
                                                  ["target"] = target ? Template(target) : null });
                    if (target) _entitySelectionService.SelectAndFocusOn(target);
                    else _entitySelectionService.Unselect();
                    _shotWait = Time.unscaledTime + 1.5f;
                    return;
                case 1:
                    string dir = HarnessBridge.OutputDir;
                    if (dir != null)
                    {
                        string file = Path.Combine(dir, "ev_" + name + ".png");
                        ScreenCapture.CaptureScreenshot(file);
                        ((JObject)_shotsTaken.Last)["file"] = Path.GetFileName(file);
                        ((JObject)_shotsTaken.Last)["festivalPanel"] = FestivalSquareFragment.ShownText;
                        ((JObject)_shotsTaken.Last)["plantPanel"] = FloweringPlantFragment.ShownText;
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
            if (Fest == null && Flow == null) return null;
            if (what == "square") return Fest?.Squares.FirstOrDefault(s => s);
            if (what == "inflower") return Flow?.InFlower.FirstOrDefault(t => t && !t.IsDead);
            if (what == "colonist") return Fest == null ? null : Fest.Goers.FirstOrDefault(g => g && g.Doing.StartsWith("at the square", StringComparison.Ordinal)) ?? Fest.Goers.FirstOrDefault(g => g);
            if (what.StartsWith("plant:", StringComparison.Ordinal))
            {
                string t = what.Substring(6);
                return Flow?.Plants.Where(p => p && p.Species == t).OrderBy(p => p.IsGrown ? 1 : 0).FirstOrDefault();
            }
            if (what.StartsWith("building:", StringComparison.Ordinal)) return FindBuilding(what.Substring(9));
            return null;
        }

        // ------------------------------------------------------------------ output

        private void Event(string kind, string text)
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
