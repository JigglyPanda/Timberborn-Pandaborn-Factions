using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using Bindito.Core;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Timberborn.BaseComponentSystem;
using Timberborn.Beavers;
using Timberborn.BehaviorSystem;
using Timberborn.Bots;
using Timberborn.Carrying;
using Timberborn.Characters;
using Timberborn.DwellingSystem;
using Timberborn.EnterableSystem;
using Timberborn.EntitySystem;
using Timberborn.GameDistricts;
using Timberborn.NeedSystem;
using Timberborn.Population;
using Timberborn.SelectionSystem;
using Timberborn.SingletonSystem;
using Timberborn.TemplateSystem;
using Timberborn.TimeSystem;
using Timberborn.UILayoutSystem;
using Timberborn.WalkingSystem;
using Timberborn.WorkSystem;
using UnityEngine;

namespace Pandaborn.Ringtails.Dev
{
    /// <summary>
    /// Dev only: bound when the PandabornDevHarness has an active test request. Applies the request's dev switches before the
    /// game's singletons load.
    /// </summary>
    [Context("Game")]
    public class RingtailDevConfigurator : Configurator
    {
        protected override void Configure()
        {
            if (!HarnessBridge.Active) return;
            var config = HarnessBridge.Config;
            RingtailService.SimulateRegistrationFailure = config["disableTemplateRegistration"]?.Value<bool>() ?? false;
            LoftHousingRule.DisabledByDev = !(config["housingRule"]?.Value<bool>() ?? true);
            Bind<PathConnector>().AsSingleton();
            Bind<RingtailProbe>().AsSingleton();
        }
    }

    /// <summary>
    /// Dev only. Drives and measures the Ringtail gate test inside a harness run, writing ringtails.json next to result.json:
    ///  * spawns Ringtail adults (and kits) on request (never when the run loaded a save);
    ///  * every in-game hour: every colonist's kind, activity, workplace, location, home and needs; every workplace's staffing;
    ///    the population numbers the player sees (the vanilla collector, district 1);
    ///  * every frame: goods picked up by each colonist (hauling and gathering throughput by hour, kind and workplace);
    ///  * at requested run hours: selects a colonist or building (opens its panel), centres the camera and captures the screen.
    /// Request section (all optional):
    /// <code>"ringtails": { "spawn": 4, "spawnKits": 1, "kitGrowth": 0.97, "housingRule": true, "disableTemplateRegistration": false,
    ///   "shots": [ { "name": "night1", "atRunHour": 14.5, "select": "ringtail|ringtailWorkplace|inkpaw|inkpawWorkplace|loft|districtCenter|none" } ] }</code>
    /// </summary>
    public class RingtailProbe : ILoadableSingleton, IUpdatableSingleton
    {
        private readonly RingtailService _ringtailService;
        private readonly LoftHousingRule _housingRule;
        private readonly EventBus _eventBus;
        private readonly IDayNightCycle _dayNightCycle;
        private readonly CharacterPopulation _characterPopulation;
        private readonly DistrictCenterRegistry _districtCenterRegistry;
        private readonly EntityRegistry _entityRegistry;
        private readonly EntitySelectionService _entitySelectionService;
        private readonly WorkingHoursManager _workingHoursManager;
        private readonly PathConnector _pathConnector;

        private readonly JObject _config;
        private readonly JObject _out = new JObject();
        private readonly JArray _samples = new JArray();
        private readonly JArray _events = new JArray();
        private readonly JArray _shotsTaken = new JArray();
        private readonly Dictionary<Character, bool> _wasCarrying = new Dictionary<Character, bool>();
        private readonly Dictionary<string, JObject> _pickups = new Dictionary<string, JObject>();
        private readonly Queue<JObject> _shotQueue = new Queue<JObject>();
        private readonly List<JObject> _pendingShots = new List<JObject>();

        private bool _primaryUi;
        private float _primaryUiAt;
        private bool _spawned;
        private int _lastHour = int.MinValue;
        private float _firstSampleHours = -1f;
        private float _firstSampleSinceDawn;
        private float _lastWrite;
        private JObject _activeShot;
        private int _shotStep;
        private float _shotWait;

        public RingtailProbe(RingtailService ringtailService, LoftHousingRule housingRule, EventBus eventBus, IDayNightCycle dayNightCycle,
                             CharacterPopulation characterPopulation, DistrictCenterRegistry districtCenterRegistry, EntityRegistry entityRegistry,
                             EntitySelectionService entitySelectionService, WorkingHoursManager workingHoursManager,
                             PathConnector pathConnector)
        {
            _ringtailService = ringtailService;
            _housingRule = housingRule;
            _eventBus = eventBus;
            _dayNightCycle = dayNightCycle;
            _characterPopulation = characterPopulation;
            _districtCenterRegistry = districtCenterRegistry;
            _entityRegistry = entityRegistry;
            _entitySelectionService = entitySelectionService;
            _workingHoursManager = workingHoursManager;
            _pathConnector = pathConnector;
            _config = HarnessBridge.Config;
        }

        public void Load()
        {
            _eventBus.Register(this);
            _out["config"] = _config.DeepClone();
            _out["loadSave"] = HarnessBridge.LoadSave;
            _out["feature"] = new JObject
            {
                ["inkpawsGame"] = _ringtailService.IsInkpawsGame,
                ["enabled"] = _ringtailService.Enabled,
                ["disabledReason"] = _ringtailService.DisabledReason,
                ["housingRule"] = _housingRule.Active
            };
            if (_config["shots"] is JArray shots)
                foreach (var s in shots.OfType<JObject>()) _pendingShots.Add(s);
            HarnessBridge.Info("probe loaded; feature " + (_ringtailService.Enabled ? "enabled" : "off (" + (_ringtailService.DisabledReason ?? "not Inkpaws") + ")"));
        }

        [OnEvent]
        public void OnShowPrimaryUI(ShowPrimaryUIEvent e)
        {
            _primaryUi = true;
            _primaryUiAt = Time.unscaledTime;
        }

        public void UpdateSingleton()
        {
            if (!_primaryUi) return;
            try
            {
                if (!_spawned) TrySpawn();
                TrackCarrying();
                int hour = (int)Math.Floor(_dayNightCycle.PartialDayNumber * 24f);
                if (hour != _lastHour && _spawned)
                {
                    _lastHour = hour;
                    Sample();
                    QueueDueShots();
                }
                StepShots();
                if (Time.unscaledTime - _lastWrite > 15f) Write();
            }
            catch (Exception e)
            {
                Debug.LogError("[Pandaborn.Ringtails] probe failed: " + e);
                _primaryUi = false;   // stop; the harness reports the error
            }
        }

        // ------------------------------------------------------------------ spawning

        private void TrySpawn()
        {
            var result = HarnessBridge.Result;
            bool buildingsPlaced = result?["placedBuildings"] != null || (HarnessBridge.RawRequest?["buildings"] as JArray)?.Count == 0;
            if (!buildingsPlaced && Time.unscaledTime - _primaryUiAt < 20f) return;
            if (Time.unscaledTime - _primaryUiAt < 6f) return;
            _spawned = true;
            var center = _districtCenterRegistry.FinishedDistrictCenters.FirstOrDefault();
            if (!HarnessBridge.LoadSave && center != null && _config["place"] is JArray place)
            {
                // our own placement on the district's terrace (the harness's ring search also uses other terraces)
                var list = place.Select(t => t.Type == JTokenType.String
                    ? new KeyValuePair<string, bool>((string)t, true)
                    : new KeyValuePair<string, bool>((string)t["template"], t["finished"]?.Value<bool>() ?? true)).ToList();
                try { Event("place", _pathConnector.PlaceOnDistrictLevel(center, list)); }
                catch (Exception e) { Debug.LogError("[Pandaborn.Ringtails] placing buildings failed: " + e); }
            }
            if (!HarnessBridge.LoadSave && (_config["connectPaths"]?.Value<bool>() ?? true) && center != null)
            {
                try { Event("paths", _pathConnector.Connect(center)); }
                catch (Exception e) { Debug.LogError("[Pandaborn.Ringtails] laying paths failed: " + e); }
            }
            if (!HarnessBridge.LoadSave && center != null && _config["stock"] is JObject stock)
            {
                // the test map's start has no water in stock: give the district center what a 3-day test needs
                var given = new List<string>();
                foreach (var p in stock.Properties())
                {
                    var inventory = center.GetComponent<Timberborn.InventorySystem.Inventories>()?.EnabledInventories
                        .FirstOrDefault(i => i.Takes(p.Name) || i.Gives(p.Name));
                    if (inventory == null) { given.Add(p.Name + ": no inventory"); continue; }
                    inventory.GiveExistingIgnoringCapacity(new Timberborn.Goods.GoodAmount(p.Name, p.Value.Value<int>()));
                    given.Add(p.Name + " " + p.Value + " -> " + inventory.AmountInStock(p.Name));
                }
                Event("stock", string.Join(", ", given));
            }
            int adults = _config["spawn"]?.Value<int>() ?? 0;
            int kits = _config["spawnKits"]?.Value<int>() ?? 0;
            if (HarnessBridge.LoadSave) { adults = 0; kits = 0; }
            var anchor = _characterPopulation.Characters.FirstOrDefault(c => c && c.GetComponent<Bot>() == null && !RingtailService.IsRingtail(c));
            var spawned = new JArray();
            if ((adults > 0 || kits > 0) && anchor == null) { Event("spawn", "no colonist to spawn next to"); }
            else
            {
                var basePos = anchor ? anchor.Transform.position : Vector3.zero;
                for (int i = 0; i < adults; i++)
                {
                    var c = _ringtailService.CreateAdult(basePos, 0.2f + 0.1f * i);
                    spawned.Add(c ? Id(c) : "null");
                }
                for (int i = 0; i < kits; i++)
                {
                    var c = _ringtailService.CreateChild(basePos);
                    if (c)
                    {
                        // dev only: push the kit close to growing up, to see the Ringtail growth hook within the run
                        float growth = _config["kitGrowth"]?.Value<float>() ?? 0.97f;
                        var child = c.GetComponent<Child>();
                        typeof(Child).GetProperty("GrowthProgress")?.GetSetMethod(true)?.Invoke(child, new object[] { growth });
                    }
                    spawned.Add(c ? "kit:" + Id(c) : "null");
                }
            }
            _out["spawned"] = spawned;
            _out["runStartDay"] = Math.Round(_dayNightCycle.PartialDayNumber, 3);
            Event("spawn", adults + " adult(s), " + kits + " kit(s) requested; created " + spawned.Count(t => (string)t != "null"));
        }

        // ------------------------------------------------------------------ measuring

        private static string Id(BaseComponent c)
        {
            var e = c.GetComponent<EntityComponent>();
            return e ? e.EntityId.ToString().Substring(0, 8) : "?";
        }

        private static string TemplateName(BaseComponent c)
        {
            return c ? c.GetComponent<TemplateSpec>()?.TemplateName : null;
        }

        private static string Kind(Character c)
        {
            if (c.GetComponent<Bot>() != null) return "bot";
            bool child = c.GetComponent<Child>() != null;
            if (RingtailService.IsRingtail(c)) return child ? "ringtailKit" : "ringtail";
            return child ? "inkpawCub" : "inkpaw";
        }

        private void TrackCarrying()
        {
            foreach (var c in _characterPopulation.Characters)
            {
                if (!c) continue;
                var carrier = c.GetComponent<GoodCarrier>();
                if (carrier == null) continue;
                bool carrying = carrier.IsCarrying;
                _wasCarrying.TryGetValue(c, out bool was);
                _wasCarrying[c] = carrying;
                if (!carrying || was) continue;
                var worker = c.GetComponent<Worker>();
                string place = worker != null && worker.Workplace ? TemplateName(worker.Workplace) : "none";
                string key = Kind(c) + "|" + place;
                if (!_pickups.TryGetValue(key, out var bucket))
                    _pickups[key] = bucket = new JObject { ["kind"] = Kind(c), ["workplace"] = place, ["pickups"] = 0, ["goods"] = 0 };
                bucket["pickups"] = (int)bucket["pickups"] + 1;
                bucket["goods"] = (int)bucket["goods"] + carrier.CarriedGood.GoodAmount.Amount;
            }
        }

        private void Sample()
        {
            float hours = _dayNightCycle.PartialDayNumber * 24f;
            float dawn = _dayNightCycle.BoundsInHours(TimeOfDay.Daytime).start;
            float sinceDawn = _dayNightCycle.HoursPassedToday - dawn;
            if (sinceDawn < 0f) sinceDawn += 24f;
            if (_firstSampleHours < 0f) { _firstSampleHours = hours; _firstSampleSinceDawn = sinceDawn; }
            var sample = new JObject
            {
                ["day"] = _dayNightCycle.DayNumber,
                ["partialDay"] = Math.Round(_dayNightCycle.PartialDayNumber, 3),
                ["hour"] = Math.Round(sinceDawn, 2),
                ["runHour"] = Math.Round(hours - _firstSampleHours, 2),
                ["daytime"] = _dayNightCycle.IsDaytime,
                ["inkpawWorkingHours"] = _workingHoursManager.AreWorkingHours
            };
            var colonists = new JArray();
            foreach (var c in _characterPopulation.Characters.ToList())
                if (c) colonists.Add(DescribeColonist(c));
            sample["colonists"] = colonists;

            var workplaces = new JArray();
            foreach (var entity in _entityRegistry.Entities)
            {
                var wp = entity.GetComponent<Workplace>();
                if (wp == null || !wp.Enabled) continue;
                var assigned = wp.AssignedWorkers.Select(w => w.GetComponent<Character>()).Where(x => x).ToList();
                workplaces.Add(new JObject
                {
                    ["id"] = Id(wp),
                    ["template"] = TemplateName(wp),
                    ["workerType"] = wp.GetComponent<WorkplaceWorkerType>()?.WorkerType,
                    ["ringtailOnly"] = wp.GetComponent<PandabornRingtailWorkplaceSpec>() != null,
                    ["desired"] = wp.DesiredWorkers,
                    ["assigned"] = assigned.Count,
                    ["assignedKinds"] = new JArray(assigned.Select(x => (object)Kind(x)).ToArray()),
                    ["jobRunning"] = wp.AssignedWorkers.Count(w => w.JobRunning)
                });
            }
            sample["workplaces"] = workplaces;

            var pickups = new JArray();
            foreach (var b in _pickups.Values) pickups.Add(b);
            sample["pickupsSinceLastSample"] = pickups;
            _pickups.Clear();

            sample["playerNumbers"] = PlayerNumbers();
            sample["housing"] = new JObject { ["swaps"] = _housingRule.Swaps, ["movesIntoLofts"] = _housingRule.MovesIntoLofts, ["evictions"] = _housingRule.Evictions };
            _samples.Add(sample);
            Write();
        }

        private JObject DescribeColonist(Character c)
        {
            var o = new JObject { ["id"] = Id(c), ["name"] = c.FirstName, ["kind"] = Kind(c), ["template"] = TemplateName(c), ["alive"] = c.Alive };
            var worker = c.GetComponent<Worker>();
            if (worker != null)
            {
                o["workerType"] = worker.WorkerType;
                o["employed"] = worker.Employed;
                if (worker.Workplace)
                {
                    o["workplace"] = TemplateName(worker.Workplace);
                    o["workplaceId"] = Id(worker.Workplace);
                }
                o["jobRunning"] = worker.JobRunning;
            }
            var bm = c.GetComponent<BehaviorManager>();
            if (bm != null)
            {
                o["behavior"] = bm.RunningBehavior.Name;
                o["executor"] = bm.RunningExecutor.Name;
            }
            var dweller = c.GetComponent<Dweller>();
            Dwelling home = dweller != null ? dweller.Home : null;
            if (home)
            {
                o["home"] = TemplateName(home);
                o["homeId"] = Id(home);
                o["homeIsLoft"] = home.GetComponent<PandabornLoftSpec>() != null;
            }
            var enterer = c.GetComponent<Enterer>();
            string location = "outdoors";
            if (enterer != null && enterer.IsInside)
            {
                var building = enterer.CurrentBuilding;
                if (home && building == home.GetComponent<Enterable>()) location = "home";
                else if (worker != null && worker.Workplace && building == worker.Workplace.GetComponent<Enterable>()) location = "workplace";
                else location = "in:" + TemplateName(building);
            }
            o["location"] = location;
            var needs = c.GetComponent<NeedManager>();
            if (needs != null)
            {
                foreach (var id in new[] { "Sleep", "Hunger", "Thirst" })
                    if (needs.HasNeed(id)) o[id.ToLowerInvariant()] = Math.Round(needs.GetNeedPoints(id), 3);
                var critical = new JArray();
                foreach (var id in new[] { "Sleep", "Hunger", "Thirst" })
                    if (needs.HasNeed(id) && needs.NeedIsInCriticalState(id)) critical.Add(id);
                if (critical.Count > 0) o["critical"] = critical;
            }
            var rest = c.GetComponent<RingtailRestRootBehavior>();
            if (rest != null)
            {
                o["restInserted"] = rest.Inserted;
                o["inRestWindow"] = rest.InRestWindow;
                o["restEnd"] = Math.Round(rest.RestEndHours, 2);
            }
            var coat = c.GetComponent<RingtailCoat>();
            if (coat != null) o["coat"] = coat.CoatName;
            var walker = c.GetComponent<WalkerSpeedManager>();
            if (walker != null) o["baseSpeed"] = Math.Round(walker.GetWalkerBaseSpeed(), 3);
            return o;
        }

        private JObject PlayerNumbers()
        {
            var district = _districtCenterRegistry.FinishedDistrictCenters.FirstOrDefault();
            if (district == null) return null;
            var data = new PopulationData();
            new PopulationDataCollector().CollectData(district, data);
            return new JObject
            {
                ["adults"] = data.NumberOfAdults,
                ["children"] = data.NumberOfChildren,
                ["bots"] = data.NumberOfBots,
                ["beaverEmployable"] = data.BeaverWorkforceData.Employable,
                ["beaverUnemployable"] = data.BeaverWorkforceData.Unemployable,
                ["beaverEmployed"] = data.BeaverWorkplaceData.OccupiedWorkslots,
                ["beaverVacancies"] = data.BeaverWorkplaceData.FreeWorkslots,
                ["beaverUnemployed"] = data.BeaverWorkplaceData.Unemployed,
                ["bedsOccupied"] = data.BedData.OccupiedBeds,
                ["bedsFree"] = data.BedData.FreeBeds,
                ["homeless"] = data.BedData.Homeless
            };
        }

        // ------------------------------------------------------------------ panels and screenshots

        private void QueueDueShots()
        {
            float runHour = _dayNightCycle.PartialDayNumber * 24f - _firstSampleHours;
            for (int i = _pendingShots.Count - 1; i >= 0; i--)
            {
                var s = _pendingShots[i];
                // "atRunHour": hours since the first sample; or "day" (0 = the first day of the run) + "hour" (hours after dawn)
                float due = s["day"] != null
                    ? s["day"].Value<float>() * 24f + (s["hour"]?.Value<float>() ?? 0f) - (float)Math.Floor(_firstSampleSinceDawn)
                    : s["atRunHour"]?.Value<float>() ?? 0f;
                if (runHour >= due)
                {
                    _shotQueue.Enqueue(s);
                    _pendingShots.RemoveAt(i);
                }
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
                    var entry = new JObject { ["name"] = name, ["select"] = _activeShot["select"], ["runHour"] = Math.Round(_dayNightCycle.PartialDayNumber * 24f - _firstSampleHours, 2),
                                              ["hour"] = _samples.Count > 0 ? _samples.Last["hour"] : null, ["target"] = target ? TemplateName(target) + " " + Id(target) : null };
                    _shotsTaken.Add(entry);
                    try
                    {
                        if (target) _entitySelectionService.SelectAndFocusOn(target);
                        else _entitySelectionService.Unselect();
                        entry["selected"] = target != null;
                    }
                    catch (Exception e)
                    {
                        entry["error"] = e.GetType().Name + ": " + e.Message;
                        Debug.LogError("[Pandaborn.Ringtails] selecting " + name + " threw: " + e);
                    }
                    _shotWait = Time.unscaledTime + 1.5f;
                    return;
                case 1:
                    string dir = HarnessBridge.OutputDir;
                    if (dir != null)
                    {
                        string file = Path.Combine(dir, "rt_" + name + ".png");
                        ScreenCapture.CaptureScreenshot(file);
                        ((JObject)_shotsTaken.Last)["file"] = Path.GetFileName(file);
                    }
                    _shotWait = Time.unscaledTime + 0.7f;
                    return;
                default:
                    try { _entitySelectionService.Unselect(); }
                    catch (Exception e) { Debug.LogError("[Pandaborn.Ringtails] unselect threw: " + e); }
                    _activeShot = null;
                    _shotWait = Time.unscaledTime + 0.3f;
                    Write();
                    return;
            }
        }

        private BaseComponent FindTarget(string what)
        {
            switch (what)
            {
                case "ringtail":
                    return _characterPopulation.Characters.Where(c => c && Kind(c) == "ringtail")
                        .OrderByDescending(c => c.GetComponent<Worker>()?.JobRunning == true).FirstOrDefault();
                case "inkpaw":
                    return _characterPopulation.Characters.Where(c => c && Kind(c) == "inkpaw")
                        .OrderByDescending(c => c.GetComponent<Worker>()?.JobRunning == true).FirstOrDefault();
                case "ringtailWorkplace":
                    return Workplaces().Where(w => w.GetComponent<PandabornRingtailWorkplaceSpec>() != null)
                        .OrderByDescending(w => w.NumberOfAssignedWorkers).FirstOrDefault();
                case "ringtailGatherer":
                    return Workplaces().FirstOrDefault(w => TemplateName(w) == "RingtailGathererFlag.Inkpaws");
                case "inkpawWorkplace":
                    return Workplaces().Where(w => w.GetComponent<PandabornRingtailWorkplaceSpec>() == null && w.GetComponent<DistrictCenter>() == null)
                        .OrderByDescending(w => w.NumberOfAssignedWorkers).FirstOrDefault();
                case "loft":
                    return _entityRegistry.Entities.Select(e => e.GetComponent<Dwelling>()).FirstOrDefault(d => d && d.GetComponent<PandabornLoftSpec>() != null);
                case "districtCenter":
                    return _districtCenterRegistry.FinishedDistrictCenters.FirstOrDefault();
                default:
                    return null;
            }
        }

        private IEnumerable<Workplace> Workplaces()
        {
            return _entityRegistry.Entities.Select(e => e.GetComponent<Workplace>()).Where(w => w && w.Enabled);
        }

        // ------------------------------------------------------------------ output

        private void Event(string what, string detail)
        {
            _events.Add(new JObject { ["what"] = what, ["detail"] = detail, ["day"] = Math.Round(_dayNightCycle.PartialDayNumber, 3) });
            HarnessBridge.Info(what + ": " + detail);
        }

        private void Write()
        {
            _lastWrite = Time.unscaledTime;
            string dir = HarnessBridge.OutputDir;
            if (dir == null) return;
            _out["updatedUtc"] = DateTime.UtcNow.ToString("o", CultureInfo.InvariantCulture);
            _out["restInsertionError"] = RingtailRestRootBehavior.InsertionError;
            _out["events"] = _events;
            _out["shots"] = _shotsTaken;
            _out["samples"] = _samples;
            string target = Path.Combine(dir, "ringtails.json");
            string tmp = target + ".tmp";
            File.WriteAllText(tmp, _out.ToString(Formatting.None));
            if (File.Exists(target)) File.Delete(target);
            File.Move(tmp, target);
            var result = HarnessBridge.Result;
            if (result != null)
                result["ringtailsProbe"] = new JObject { ["file"] = "ringtails.json", ["samples"] = _samples.Count, ["feature"] = _out["feature"].DeepClone() };
        }
    }
}
