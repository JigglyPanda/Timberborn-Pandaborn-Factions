using System;
using System.Collections;
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
using Timberborn.BlockSystem;
using Timberborn.BlueprintSystem;
using Timberborn.BonusSystem;
using Timberborn.Buildings;
using Timberborn.Carrying;
using Timberborn.Characters;
using Timberborn.ConstructionSites;
using Timberborn.Cutting;
using Timberborn.EntitySystem;
using Timberborn.FactionSystem;
using Timberborn.GameFactionSystem;
using Timberborn.GameSaveRepositorySystem;
using Timberborn.GameSaveRuntimeSystem;
using Timberborn.Goods;
using Timberborn.Growing;
using Timberborn.InventorySystem;
using Timberborn.Localization;
using Timberborn.NaturalResources;
using Timberborn.NeedSpecs;
using Timberborn.NeedSystem;
using Timberborn.PlatformUtilities;
using Timberborn.SelectionSystem;
using Timberborn.SingletonSystem;
using Timberborn.TemplateSystem;
using Timberborn.TerrainSystem;
using Timberborn.TimeSystem;
using Timberborn.TutorialSettingsSystem;
using Timberborn.TutorialSystem;
using Timberborn.UILayoutSystem;
using Timberborn.WalkingSystem;
using Timberborn.WorkSystem;
using Timberborn.Workshops;
using Timberborn.BlueprintSystem;
using Timberborn.Forestry;
using UnityEngine;

namespace Pandaborn.Stage0
{
    /// <summary>Dev only: bound when the PandabornDevHarness has an active test request.</summary>
    [Context("Game")]
    public class Stage0Configurator : Configurator
    {
        protected override void Configure()
        {
            if (!HarnessBridge.Active) return;
            Bind<BlueprintTracer>().AsSingleton();
            MultiBind<IBlueprintModifierProvider>().ToExisting<BlueprintTracer>();
            Bind<Stage0Probe>().AsSingleton();
        }
    }

    /// <summary>
    /// Dev only. Measures the stage-0 checks inside a harness run and writes stage0.json next to result.json. Talks to
    /// the Pandaborn code modules only by reflection, so it loads (and reports) whether they are on or off.
    /// Request section "stage0" (all optional; a "reload" sub-object overrides keys in the save-and-reload launch):
    ///   devSwitchNext: text written to the mod's pandaborn.dev.txt for the NEXT launch ("" deletes it)
    ///   bamboo: n timber-bamboo trees spawned grown and marked for cutting next to the first lumberjack flag
    ///   pileGood: good id selected on every placed small pile
    ///   bell: [ { atRunHour, hours, relock, emulate } ]   set the working-hours slider; relock = apply now, not at dawn
    ///   wellbeingTable: atRunHour at which multipliers are tabulated for emulated wellbeing 20 and 80 at 16/14/12 h
    ///   tutorialNextAtRunHour: call ITutorialService.StartNextStage on the running Pandaborn tutorial
    ///   shots: [ { name, atRunHour, select } ]   select = inkpaw | bamboo | lumberjack | teahouse | lumbermill | none
    ///   resaveAtRunHour: save the game again (as PB_AutoTest_resave) and copy the file into the run folder
    /// </summary>
    public class Stage0Probe : ILoadableSingleton, IUpdatableSingleton
    {
        private const string Bamboo = "PandabornStage0Bamboo.Inkpaws";
        private readonly EventBus _eventBus;
        private readonly IDayNightCycle _dayNightCycle;
        private readonly CharacterPopulation _characterPopulation;
        private readonly EntityRegistry _entityRegistry;
        private readonly EntitySelectionService _entitySelectionService;
        private readonly WorkingHoursManager _workingHoursManager;
        private readonly IGoodService _goodService;
        private readonly ISpecService _specService;
        private readonly TemplateService _templateService;
        private readonly BonusTypeSpecService _bonusTypeSpecService;
        private readonly BlueprintSourceService _blueprintSourceService;
        private readonly FactionService _factionService;
        private readonly FactionNeedService _factionNeedService;
        private readonly NaturalResourceFactory _naturalResourceFactory;
        private readonly TreeCuttingArea _treeCuttingArea;
        private readonly ITerrainService _terrainService;
        private readonly ITutorialService _tutorialService;
        private readonly TutorialSettings _tutorialSettings;
        private readonly GameSaver _gameSaver;
        private readonly ILoc _loc;

        private readonly JObject _config;
        private readonly JObject _out = new JObject();
        private readonly JArray _events = new JArray();
        private readonly JArray _samples = new JArray();
        private readonly List<JObject> _pending = new List<JObject>();
        private readonly List<Cuttable> _bamboo = new List<Cuttable>();
        private readonly Dictionary<Character, Vector3> _lastPos = new Dictionary<Character, Vector3>();
        private readonly Dictionary<string, double[]> _walk = new Dictionary<string, double[]>();   // label -> moving distance, moving hours, nominal*hours
        private bool _primaryUi;
        private bool _started;
        private float _startHours;
        private float _lastHours;
        private float _lastSample = -1f;
        private float _lastWrite;
        private int _cuts;
        private JObject _shot;
        private int _shotStep;
        private float _shotWait;
        private readonly Queue<JObject> _shotQueue = new Queue<JObject>();
        private string _emulation = "none";
        private string _resaveFile;
        private float _resaveCopyAt;
        private int _resaveTries;
        private bool? _tutorialSettingBefore;

        public Stage0Probe(EventBus eventBus, IDayNightCycle dayNightCycle, CharacterPopulation characterPopulation, EntityRegistry entityRegistry,
                           EntitySelectionService entitySelectionService, WorkingHoursManager workingHoursManager, IGoodService goodService,
                           ISpecService specService, TemplateService templateService, BonusTypeSpecService bonusTypeSpecService,
                           BlueprintSourceService blueprintSourceService, FactionService factionService, FactionNeedService factionNeedService,
                           NaturalResourceFactory naturalResourceFactory, TreeCuttingArea treeCuttingArea, ITerrainService terrainService,
                           ITutorialService tutorialService, TutorialSettings tutorialSettings, GameSaver gameSaver, ILoc loc)
        {
            _eventBus = eventBus;
            _dayNightCycle = dayNightCycle;
            _characterPopulation = characterPopulation;
            _entityRegistry = entityRegistry;
            _entitySelectionService = entitySelectionService;
            _workingHoursManager = workingHoursManager;
            _goodService = goodService;
            _specService = specService;
            _templateService = templateService;
            _bonusTypeSpecService = bonusTypeSpecService;
            _blueprintSourceService = blueprintSourceService;
            _factionService = factionService;
            _factionNeedService = factionNeedService;
            _naturalResourceFactory = naturalResourceFactory;
            _treeCuttingArea = treeCuttingArea;
            _terrainService = terrainService;
            _tutorialService = tutorialService;
            _tutorialSettings = tutorialSettings;
            _gameSaver = gameSaver;
            _loc = loc;
            _config = HarnessBridge.Config;
        }

        // ------------------------------------------------------------------ lifecycle

        public void Load()
        {
            _eventBus.Register(this);
            _out["config"] = _config.DeepClone();
            _out["loadSave"] = HarnessBridge.LoadSave;
            _out["features"] = Features();
            _out["events"] = _events;
            _out["samples"] = _samples;
            foreach (var key in new[] { "bell", "shots" })
                if (_config[key] is JArray a) foreach (var s in a.OfType<JObject>()) _pending.Add(new JObject { ["kind"] = key, ["step"] = s.DeepClone() });
            foreach (var key in new[] { "wellbeingTable", "tutorialNextAtRunHour", "resaveAtRunHour", "dataAtRunHour" })
                if (_config[key] != null && _config[key].Type != JTokenType.Null) _pending.Add(new JObject { ["kind"] = key, ["step"] = new JObject { ["atRunHour"] = _config[key] } });
            WriteDevSwitch();
            HarnessBridge.Info("probe loaded; features " + string.Join(", ", ((JArray)_out["features"]["units"]).Select(u => u["id"] + ":" + u["state"])));
        }

        [OnEvent]
        public void OnShowPrimaryUI(ShowPrimaryUIEvent e) => _primaryUi = true;

        [OnEvent]
        public void OnDaytimeStart(DaytimeStartEvent e) => Event("dawn", Bell());

        [OnEvent]
        public void OnTutorialStageStarted(TutorialStageStartedEvent e) =>
            Event("tutorialStage", new JObject { ["tutorial"] = e.TutorialId, ["stage"] = e.TutorialStage?.Id, ["intro"] = e.TutorialStage?.Intro, ["steps"] = e.TutorialStage?.TutorialSteps.Length ?? 0 });

        [OnEvent]
        public void OnTutorialFinished(TutorialFinishedEvent e) => Event("tutorialFinished", e.TutorialId);

        [OnEvent]
        public void OnWorkingHoursChanged(WorkingHoursChangedEvent e) => Event("workingHoursChanged", Bell());

        public void UpdateSingleton()
        {
            if (!_primaryUi) return;
            try
            {
                float hours = _dayNightCycle.PartialDayNumber * 24f;
                if (!_started)
                {
                    if (!(HarnessBridge.Result?["run"] is JObject)) return;   // the harness has placed buildings and started running
                    _started = true;
                    _startHours = hours;
                    _lastHours = hours;
                    OnStart();
                }
                float runHour = hours - _startHours;
                TrackWalking(hours);
                if (runHour - _lastSample >= 0.5f) { _lastSample = runHour; Sample(runHour); }
                for (int i = _pending.Count - 1; i >= 0; i--)
                {
                    var p = _pending[i];
                    if (runHour < (float)p["step"]["atRunHour"]) continue;
                    _pending.RemoveAt(i);
                    Do(p, runHour);
                }
                StepShots();
                CopyResave();
                if (_tutorialSettingBefore.HasValue && runHour >= (_config["showTutorialPanelUntilRunHour"]?.Value<float>() ?? 0f)) RestoreTutorialSetting();
                if (Time.unscaledTime - _lastWrite > 10f) Write();
            }
            catch (Exception e)
            {
                Debug.LogError("[Pandaborn.Stage0] probe failed: " + e);
                Event("probeError", e.ToString());
                RestoreTutorialSetting();
                _primaryUi = false;
                Write();
            }
        }

        private void OnStart()
        {
            _out["data"] = Data("start");
            ShowTutorialPanelBriefly();
            int n = _config["bamboo"]?.Value<int>() ?? 0;
            if (n > 0 && !HarnessBridge.LoadSave) SpawnBamboo(n);
            else foreach (var c in Entities<Cuttable>().Where(c => Template(c) == Bamboo)) Watch(c);
            string pileGood = _config["pileGood"]?.Value<string>();
            if (!string.IsNullOrEmpty(pileGood))
                foreach (var a in Entities<SingleGoodAllower>().Where(a => Template(a).StartsWith("SmallPile")))
                {
                    try { a.Allow(pileGood); Event("pileGood", Template(a) + " -> " + pileGood); }
                    catch (Exception e) { Event("pileGoodError", e.Message); }
                }
            Write();
        }

        private void Do(JObject p, float runHour)
        {
            var step = (JObject)p["step"];
            switch ((string)p["kind"])
            {
                case "bell":
                {
                    int h = step["hours"].Value<int>();
                    _workingHoursManager.WorkedPartOfDay = h / 24f;
                    if (step["relock"]?.Value<bool>() == true) BellCall("Lock", h, "stage-0 probe");
                    Event("bellStep", new JObject { ["runHour"] = Math.Round(runHour, 2), ["set"] = h, ["relock"] = step["relock"], ["bell"] = Bell() });
                    break;
                }
                case "wellbeingTable":
                    _out["wellbeingTable"] = WellbeingTable();
                    break;
                case "tutorialNextAtRunHour":
                    try
                    {
                        _tutorialService.StartNextStage("PandabornStage0");
                        Event("tutorialNext", "StartNextStage(PandabornStage0) called");
                    }
                    catch (Exception e) { Event("tutorialNextError", e.Message); }
                    break;
                case "resaveAtRunHour":
                    Resave();
                    break;
                case "dataAtRunHour":
                    _out["dataLater"] = Data("later");
                    break;
                case "shots":
                    _shotQueue.Enqueue(step);
                    break;
            }
        }

        // ------------------------------------------------------------------ check 1 (modifiers), 3 (features), 4, 5

        private JObject Data(string when)
        {
            var d = new JObject { ["when"] = when, ["day"] = Math.Round(_dayNightCycle.PartialDayNumber, 3) };
            d["faction"] = _factionService.Current.Id;
            d["startingFactionSpec"] = _factionService.Current.GetSpec<StartingFactionSpec>() != null;
            d["features"] = Features();
            try
            {
                var plank = _goodService.GetGood("Plank");
                d["plank"] = new JObject
                {
                    ["displayName"] = plank.DisplayName.Value, ["plural"] = plank.PluralDisplayName.Value,
                    ["icon"] = plank.Icon?.Path, ["iconSprite"] = plank.Icon?.Asset ? plank.Icon.Asset.name : null, ["weight"] = plank.Weight,
                    ["sources"] = Sources(plank)
                };
            }
            catch (Exception e) { d["plankError"] = e.Message; }
            try
            {
                var need = _factionNeedService.Needs.FirstOrDefault(n => n.Id == "Campfire");
                d["campfireNeed"] = need == null ? null : new JObject { ["dailyDelta"] = need.DailyDelta, ["sources"] = Sources(need) };
                var adult = _characterPopulation.Characters.FirstOrDefault(c => c && c.GetComponent<AdultSpec>() != null);
                var manager = adult?.GetComponent<NeedManager>();
                var ns = manager?.NeedSpecs.FirstOrDefault(n => n.Id == "Campfire");
                if (ns != null) d["campfireNeedOnColonist"] = ns.DailyDelta;
            }
            catch (Exception e) { d["needError"] = e.Message; }
            d["buildings"] = new JObject();
            foreach (var name in new[] { "LumberMill.Folktails", "Campfire.Folktails", "Grill.Folktails", "PandabornStage0Teahouse.Inkpaws", "Stairs.Folktails" })
            {
                var spec = _templateService.GetAll<TemplateSpec>().FirstOrDefault(t => t.TemplateName == name);
                if (spec == null) { d["buildings"][name] = "not in this faction"; continue; }
                var b = new JObject();
                var building = spec.GetSpec<BuildingSpec>();
                if (building != null) b["cost"] = new JArray(building.BuildingCost.Select(c => c.Id + " x" + c.Amount));
                var manufactory = spec.GetSpec<ManufactorySpec>();
                if (manufactory != null) b["recipes"] = new JArray(manufactory.ProductionRecipeIds);
                b["specs"] = new JArray(spec.Blueprint.Specs.Select(s => s.GetType().Name).Where(n => n.StartsWith("Pandaborn")));
                b["sources"] = Sources(spec);
                d["buildings"][name] = b;
            }
            try
            {
                var move = _bonusTypeSpecService.GetSpec("MovementSpeed");
                d["movementSpeedType"] = new JObject { ["min"] = move.MinimumValue, ["max"] = move.MaximumValue, ["sources"] = Sources(move) };
            }
            catch (Exception e) { d["bonusTypeError"] = e.Message; }
            d["tutorial"] = Tutorial();
            d["colonists"] = new JArray(_characterPopulation.Characters.Where(c => c).Select(c => new JObject
            {
                ["name"] = c.FirstName,
                ["template"] = Template(c),
                ["components"] = new JArray(Ours(c))
            }));
            d["oursByTemplate"] = OursByTemplate();
            d["bell"] = Bell();
            d["store"] = Store();
            d["messages"] = Messages();
            d["blueprintReads"] = ReadSummary();
            return d;
        }

        private JArray Sources(ComponentSpec spec)
        {
            try { return new JArray(_blueprintSourceService.Get(spec.Blueprint).Sources); }
            catch (Exception e) { return new JArray("error: " + e.Message); }
        }

        private JObject Features()
        {
            var units = new JArray();
            string report = AppDomain.CurrentDomain.GetData("Pandaborn.Boot.Report") as string ?? "";
            foreach (var line in report.Split(new[] { '\n' }, StringSplitOptions.RemoveEmptyEntries))
            {
                var p = line.Split('\t');
                units.Add(new JObject { ["id"] = p[0], ["state"] = p.Length > 1 ? p[1] : "", ["reason"] = p.Length > 2 ? p[2] : "" });
            }
            return new JObject
            {
                ["owner"] = AppDomain.CurrentDomain.GetData("Pandaborn.Boot.Owner") as string,
                ["duplicates"] = AppDomain.CurrentDomain.GetData("Pandaborn.Boot.Duplicates") as string,
                ["units"] = units,
                ["assemblies"] = new JArray(AppDomain.CurrentDomain.GetAssemblies().Select(a => a.GetName().Name).Where(n => n.StartsWith("Pandaborn")).OrderBy(n => n))
            };
        }

        private JObject Tutorial()
        {
            var t = new JObject();
            try
            {
                t["disableTutorialSetting"] = _tutorialSettings.DisableTutorial;
                var service = _tutorialService;
                var type = service.GetType();
                var configs = type.GetField("_tutorialConfigurations", BindingFlags.Instance | BindingFlags.NonPublic)?.GetValue(service) as IEnumerable;
                if (configs != null)
                    t["configurations"] = new JArray(configs.Cast<TutorialConfiguration>().Select(c =>
                        c.TutorialId + " stages=" + c.TutorialStages.Length + " requires=[" + string.Join(",", c.RequiredTutorialIds) + "]"));
                var active = type.GetField("_activeTutorialStages", BindingFlags.Instance | BindingFlags.NonPublic)?.GetValue(service) as IDictionary;
                if (active != null)
                {
                    var a = new JObject();
                    foreach (DictionaryEntry kv in active)
                    {
                        var stage = kv.Value as TutorialStage;
                        a[(string)kv.Key] = stage == null ? null : new JObject
                        {
                            ["stage"] = stage.Id, ["intro"] = stage.Intro, ["achieved"] = stage.AllStepsAchieved,
                            ["steps"] = new JArray(stage.TutorialSteps.Select(s => SafeDescription(s)))
                        };
                    }
                    t["active"] = a;
                }
                var finished = type.GetField("_finishedTutorials", BindingFlags.Instance | BindingFlags.NonPublic)?.GetValue(service) as IEnumerable<string>;
                if (finished != null) t["finished"] = new JArray(finished);
            }
            catch (Exception e) { t["error"] = e.Message; }
            return t;
        }

        private static string SafeDescription(TutorialStep step)
        {
            try { return step.Step.Description() + (step.Step.Achieved() ? " [achieved]" : ""); }
            catch (Exception e) { return "error: " + e.Message; }
        }

        // ------------------------------------------------------------------ check 2: a tree that yields planks

        private void SpawnBamboo(int n)
        {
            var flag = Entities<BlockObject>().FirstOrDefault(b => Template(b).StartsWith("LumberjackFlag"));
            var report = new JObject();
            _out["bambooSpawn"] = report;
            if (flag == null) { report["error"] = "no lumberjack flag"; return; }
            var origin = flag.Coordinates;
            report["flag"] = new JArray(origin.x, origin.y, origin.z);
            var marked = new List<Vector3Int>();
            for (int r = 2; r <= 6 && marked.Count < n; r++)
                for (int dx = -r; dx <= r && marked.Count < n; dx++)
                    for (int dy = -r; dy <= r && marked.Count < n; dy++)
                    {
                        if (Math.Max(Math.Abs(dx), Math.Abs(dy)) != r) continue;
                        var xy = new Vector2Int(origin.x + dx, origin.y + dy);
                        if (!_terrainService.Contains(xy)) continue;
                        int z = _terrainService.GetTerrainHeightBelow(new Vector3Int(xy.x, xy.y, origin.z + 4));
                        if (Math.Abs(z - origin.z) > 1) continue;
                        var c = new Vector3Int(xy.x, xy.y, z);
                        try
                        {
                            var resource = _naturalResourceFactory.SpawnIgnoringConstraints(Bamboo, c);
                            if (!resource) continue;
                            resource.GetComponent<Growable>()?.IncreaseGrowthProgress(1f);
                            var cuttable = resource.GetComponent<Cuttable>();
                            if (cuttable != null) Watch(cuttable);
                            marked.Add(c);
                        }
                        catch (Exception e) { report["lastError"] = e.Message; }
                    }
            _treeCuttingArea.AddCoordinates(marked);
            report["spawned"] = marked.Count;
            report["cells"] = new JArray(marked.Select(c => c.x + "," + c.y + "," + c.z));
            var first = _bamboo.FirstOrDefault();
            if (first != null) report["yield"] = first.YielderSpec.Yield.Id + " x" + first.YielderSpec.Yield.Amount;
            HarnessBridge.Info("spawned " + marked.Count + " timber bamboo next to the lumberjack flag and marked them for cutting");
        }

        private void Watch(Cuttable c)
        {
            _bamboo.Add(c);
            c.WasCut += (s, e) =>
            {
                _cuts++;
                Event("bambooCut", new JObject { ["cuts"] = _cuts, ["yield"] = c.YielderSpec.Yield.Id });
            };
        }

        private JObject Goods()
        {
            var byTemplate = new JObject();
            var inventories = new List<Inventory>();
            foreach (var entity in _entityRegistry.Entities)
            {
                inventories.Clear();
                entity.GetComponents(inventories);
                int planks = inventories.Sum(i => i.AmountInStock("Plank"));
                int logs = inventories.Sum(i => i.AmountInStock("Log"));
                if (planks == 0 && logs == 0) continue;
                string t = Template(entity);
                var o = byTemplate[t] as JObject ?? new JObject { ["Plank"] = 0, ["Log"] = 0 };
                o["Plank"] = (int)o["Plank"] + planks;
                o["Log"] = (int)o["Log"] + logs;
                byTemplate[t] = o;
            }
            var carrying = new JObject();
            foreach (var c in _characterPopulation.Characters.Where(c => c))
            {
                var carrier = c.GetComponent<GoodCarrier>();
                if (carrier == null || !carrier.IsCarrying) continue;
                var worker = c.GetComponent<Worker>();
                string key = carrier.CarriedGoodId + "@" + (worker?.Workplace ? Template(worker.Workplace) : "none");
                carrying[key] = (carrying[key]?.Value<int>() ?? 0) + carrier.CarriedGood.GoodAmount.Amount;
            }
            var sites = new JObject();
            foreach (var site in Entities<ConstructionSite>())
                sites[Template(site)] = new JObject { ["materials"] = Math.Round(site.MaterialProgress, 3), ["build"] = Math.Round(site.BuildTimeProgress, 3) };
            return new JObject { ["stock"] = byTemplate, ["carrying"] = carrying, ["sites"] = sites, ["bambooCuts"] = _cuts, ["bambooLeft"] = _bamboo.Count(b => b && b.Yielder != null && b.Yielder.Yield.Amount > 0) };
        }

        // ------------------------------------------------------------------ the bell

        private static object BellService() => Type.GetType("Pandaborn.Bell.BellService, Pandaborn.Bell")?.GetProperty("Current")?.GetValue(null);

        private static object BellCall(string method, params object[] args)
        {
            var s = BellService();
            return s?.GetType().GetMethod(method)?.Invoke(s, args);
        }

        private static object Prop(object o, string name) => o?.GetType().GetProperty(name)?.GetValue(o);

        private JObject Bell()
        {
            var s = BellService();
            var j = new JObject
            {
                ["module"] = s != null,
                ["slider"] = Mathf.CeilToInt(_workingHoursManager.WorkedPartOfDay * 24f - 0.001f),
                ["day"] = Math.Round(_dayNightCycle.PartialDayNumber, 3)
            };
            if (s == null) return j;
            j["active"] = (bool)Prop(s, "Active");
            j["lockedHours"] = (int)Prop(s, "LockedHours");
            j["workingBonus"] = Math.Round((float)Prop(s, "WorkingBonus"), 4);
            j["movementBonus"] = Math.Round((float)Prop(s, "MovementBonus"), 4);
            j["suggested"] = (bool)Prop(s, "Suggested");
            j["hint"] = Type.GetType("Pandaborn.Bell.BellHoursHint, Pandaborn.Bell")?.GetProperty("ShownText")?.GetValue(null) as string;
            j["colonistLine"] = Type.GetType("Pandaborn.Bell.BellColonistFragment, Pandaborn.Bell")?.GetProperty("ShownText")?.GetValue(null) as string;
            return j;
        }

        private IEnumerable<Character> Adults() => _characterPopulation.Characters.Where(c => c && c.GetComponent<AdultSpec>() != null);

        private JObject Colonist(Character c)
        {
            var bonus = c.GetComponent<BonusManager>();
            var worker = c.GetComponent<Worker>();
            var walker = c.GetComponent<WalkerSpeedManager>();
            var bell = c.AllComponents.FirstOrDefault(x => x.GetType().Name == "BellRestedBonus");
            var o = new JObject
            {
                ["name"] = c.FirstName,
                ["work"] = Math.Round(bonus.Multiplier("WorkingSpeed"), 4),
                ["move"] = Math.Round(bonus.Multiplier("MovementSpeed"), 4),
                ["workerMultiplier"] = worker != null ? Math.Round(worker.WorkingSpeedMultiplier, 4) : (JToken)JValue.CreateNull(),
                ["walkerBaseSpeed"] = walker != null ? Math.Round(walker.GetWalkerBaseSpeed(), 4) : (JToken)JValue.CreateNull(),
                ["workplace"] = worker?.Workplace ? Template(worker.Workplace) : null
            };
            if (bell != null)
            {
                o["bellWorkDelta"] = Math.Round((float)Prop(bell, "WorkingDelta"), 4);
                o["bellMoveDelta"] = Math.Round((float)Prop(bell, "MovementDelta"), 4);
                o["workWithoutBell"] = Math.Round((float)Prop(bell, "WorkingBase"), 4);
                o["moveWithoutBell"] = Math.Round((float)Prop(bell, "MovementBase"), 4);
            }
            return o;
        }

        private void Sample(float runHour)
        {
            var adults = Adults().ToList();
            var s = new JObject
            {
                ["runHour"] = Math.Round(runHour, 2),
                ["day"] = Math.Round(_dayNightCycle.PartialDayNumber, 3),
                ["workingHours"] = _workingHoursManager.AreWorkingHours,
                ["bell"] = Bell(),
                ["emulation"] = _emulation,
                ["meanWork"] = adults.Count == 0 ? 0 : Math.Round(adults.Average(a => a.GetComponent<BonusManager>().Multiplier("WorkingSpeed")), 4),
                ["meanMove"] = adults.Count == 0 ? 0 : Math.Round(adults.Average(a => a.GetComponent<BonusManager>().Multiplier("MovementSpeed")), 4),
                ["colonists"] = new JArray(adults.Take(6).Select(Colonist)),
                ["goods"] = Goods()
            };
            _samples.Add(s);
        }

        /// <summary>Distance actually travelled per in-game hour while moving, by locked bell hours.</summary>
        private void TrackWalking(float hours)
        {
            float dt = hours - _lastHours;
            _lastHours = hours;
            var s = BellService();
            string label = "lock" + (s != null ? Prop(s, "LockedHours") : "none") + (_emulation != "none" ? "_" + _emulation : "");
            if (!_walk.TryGetValue(label, out var acc)) _walk[label] = acc = new double[3];
            foreach (var c in Adults())
            {
                var p = c.Transform.position;
                if (_lastPos.TryGetValue(c, out var last) && dt > 0f && dt < 0.5f)
                {
                    float d = Vector3.Distance(p, last);
                    var walker = c.GetComponent<WalkerSpeedManager>();
                    if (d / dt > 0.5f && d < 2f && walker != null)
                    {
                        acc[0] += d;
                        acc[1] += dt;
                        acc[2] += walker.GetWalkerBaseSpeed() * dt;
                    }
                }
                _lastPos[c] = p;
            }
        }

        /// <summary>Multipliers for sample colonists with wellbeing emulated through the same bonus sums the wellbeing tiers
        /// add (adult tiers: wellbeing 20 = working +0.8, walking +0.15; wellbeing 80 = working +2.8, walking +0.7), at 16, 14
        /// and 12 locked hours.</summary>
        private JObject WellbeingTable()
        {
            var table = new JObject();
            var s = BellService();
            if (s == null) { table["error"] = "bell module not loaded"; return table; }
            int before = (int)Prop(s, "LockedHours");
            var levels = new[] { ("wellbeing20", 0.8f, 0.15f), ("wellbeing80", 2.8f, 0.7f) };
            var sample = Adults().Take(4).ToList();
            foreach (var (name, work, move) in levels)
            {
                var rows = new JObject();
                foreach (var c in sample)
                {
                    var b = c.GetComponent<BonusManager>();
                    b.AddBonus("WorkingSpeed", work);
                    b.AddBonus("MovementSpeed", move);
                }
                foreach (int h in new[] { 16, 14, 12 })
                {
                    BellCall("Lock", h, "wellbeing table");
                    rows[h + "h"] = new JArray(sample.Select(Colonist));
                }
                foreach (var c in sample)
                {
                    var b = c.GetComponent<BonusManager>();
                    b.RemoveBonus("WorkingSpeed", work);
                    b.RemoveBonus("MovementSpeed", move);
                }
                table[name] = rows;
            }
            BellCall("Lock", before, "wellbeing table done");
            table["movementCap"] = _bonusTypeSpecService.GetSpec("MovementSpeed").MaximumValue;
            return table;
        }

        // ------------------------------------------------------------------ check 3: save carried while off

        private JObject Store()
        {
            var j = new JObject();
            try
            {
                var type = Type.GetType("Pandaborn.Core.PandabornStore, Pandaborn.Core");
                var store = type?.GetProperty("Current")?.GetValue(null);
                if (store == null) { j["error"] = "no store"; return j; }
                j["loadedFromSave"] = (bool)type.GetProperty("LoadedFromSave").GetValue(store);
                foreach (string f in (IEnumerable<string>)type.GetProperty("Features").GetValue(store))
                {
                    var args = new object[] { f, 0, null };
                    type.GetMethod("TryGet").Invoke(store, args);
                    j[f] = "v" + args[1] + " " + args[2];
                }
            }
            catch (Exception e) { j["error"] = e.Message; }
            return j;
        }

        private static JArray Messages()
        {
            var log = Type.GetType("Pandaborn.Core.Messenger, Pandaborn.Core")?.GetField("Log")?.GetValue(null) as IEnumerable<string>;
            return log == null ? new JArray("Pandaborn.Core not loaded") : new JArray(log);
        }

        private void Resave()
        {
            try
            {
                var raw = HarnessBridge.RawRequest;
                string settlement = (string)raw?["settlementName"];
                string dir = Path.Combine(UserDataFolder.Folder, "Saves");
                var reference = new SaveReference("PB_AutoTest_resave", new SettlementReference(settlement, dir));
                string file = Path.Combine(dir, settlement, "PB_AutoTest_resave.timber");
                _gameSaver.QueueSaveSkippingNameValidation(reference, () => { _resaveFile = file; _resaveCopyAt = Time.unscaledTime + 2f; });
            }
            catch (Exception e) { Event("resaveError", e.Message); }
        }

        private void CopyResave()
        {
            if (_resaveFile == null || Time.unscaledTime < _resaveCopyAt) return;
            try
            {
                File.Copy(_resaveFile, Path.Combine(HarnessBridge.OutputDir, "resave.timber"), true);
                Event("resaved", _resaveFile);
                _resaveFile = null;
            }
            catch (Exception e)
            {
                _resaveCopyAt = Time.unscaledTime + 2f;
                if (++_resaveTries >= 10) { Event("resaveCopyError", e.Message); _resaveFile = null; }
            }
        }

        /// <summary>The player's "disable tutorial" setting hides the tutorial panel. For screenshots only, it is switched
        /// off briefly and put back (showTutorialPanelUntilRunHour); the restore also runs when the probe stops.</summary>
        private void ShowTutorialPanelBriefly()
        {
            if (_config["showTutorialPanelUntilRunHour"] == null || HarnessBridge.LoadSave) return;
            _tutorialSettingBefore = _tutorialSettings.DisableTutorial;
            // the owner's setting: record it in the run folder BEFORE changing it (like mod states), verify after restore
            File.WriteAllText(Path.Combine(HarnessBridge.OutputDir, "settings.before.json"),
                new JObject { ["setting"] = "TutorialSettings.DisableTutorial", ["value"] = _tutorialSettingBefore.Value }.ToString());
            if (_tutorialSettingBefore.Value) _tutorialSettings.DisableTutorial = false;
            Event("tutorialSetting", "DisableTutorial was " + _tutorialSettingBefore.Value + "; panel shown for screenshots");
        }

        private void RestoreTutorialSetting()
        {
            if (!_tutorialSettingBefore.HasValue) return;
            try
            {
                if (_tutorialSettings.DisableTutorial != _tutorialSettingBefore.Value) _tutorialSettings.DisableTutorial = _tutorialSettingBefore.Value;
                bool ok = _tutorialSettings.DisableTutorial == _tutorialSettingBefore.Value;
                File.WriteAllText(Path.Combine(HarnessBridge.OutputDir, "settings.restore.json"),
                    new JObject { ["setting"] = "TutorialSettings.DisableTutorial", ["expected"] = _tutorialSettingBefore.Value,
                                  ["actual"] = _tutorialSettings.DisableTutorial, ["verified"] = ok }.ToString());
                if (!ok) Debug.LogError("[Pandaborn.Stage0] could not restore the owner's DisableTutorial setting; restore it by hand");
                Event("tutorialSetting", "DisableTutorial restored to " + _tutorialSettings.DisableTutorial + (ok ? " (verified)" : " (NOT VERIFIED)"));
            }
            catch (Exception e) { Event("tutorialSettingError", e.Message); }
            _tutorialSettingBefore = null;
        }

        private void WriteDevSwitch()
        {
            if (!(_config["devSwitchNext"] is JValue v)) return;
            try
            {
                string owner = AppDomain.CurrentDomain.GetData("Pandaborn.Boot.Owner") as string;
                if (string.IsNullOrEmpty(owner)) { Event("devSwitch", "no bootstrap owner"); return; }
                string file = Path.Combine(owner, "pandaborn.dev.txt");
                string text = (string)v ?? "";
                if (text.Length == 0) { if (File.Exists(file)) File.Delete(file); Event("devSwitch", "deleted " + file); }
                else { File.WriteAllText(file, text.Replace(";", "\n")); Event("devSwitch", "wrote " + file + ": " + text); }
            }
            catch (Exception e) { Event("devSwitchError", e.Message); }
        }

        // ------------------------------------------------------------------ helpers

        private JObject ReadSummary()
        {
            var reads = BlueprintTracer.Reads.OfType<JObject>().ToList();
            var early = reads.Where(r => r["factionModifiersReady"]?.Type == JTokenType.Boolean && !(bool)r["factionModifiersReady"]).ToList();
            JObject Find(string fragment)
            {
                var r = reads.FirstOrDefault(x => ((string)x["path"]).IndexOf(fragment, StringComparison.OrdinalIgnoreCase) >= 0);
                return r == null ? null : (JObject)r.DeepClone();
            }
            return new JObject
            {
                ["total"] = reads.Count,
                ["beforeFactionModifiers"] = early.Count,
                ["beforeByFolder"] = new JObject(early.GroupBy(r => Folder((string)r["path"])).OrderBy(g => g.Key)
                    .Select(g => new JProperty(g.Key, g.Count()))),
                ["beforeReaders"] = new JObject(early.GroupBy(r => (string)r["reader"]).OrderByDescending(g => g.Count()).Take(25)
                    .Select(g => new JProperty(g.Key ?? "?", g.Count()))),
                ["firstAfter"] = reads.FirstOrDefault(r => r["factionModifiersReady"]?.Type == JTokenType.Boolean && (bool)r["factionModifiersReady"])?.DeepClone(),
                ["plank"] = Find("good.plank"),
                ["campfireNeed"] = Find("need.beaver.campfire"),
                ["lumberMill"] = Find("lumbermill.folktails"),
                ["grill"] = Find("grill.folktails"),
                ["movementSpeedType"] = Find("bonustype.movementspeed"),
                ["tutorialWood"] = Find("tutorials.wood"),
                ["tutorialStageStart"] = Find("pandabornstage0"),
                ["inkpawAdult"] = Find("inkpawadult.inkpaws"),
                ["wellbeingTier"] = Find("wellbeingtier.adult.movementspeed")
            };
        }

        private static string Folder(string path)
        {
            int slash = path.IndexOf('/');
            return slash > 0 ? path.Substring(0, slash) : path;
        }

        private JObject OursByTemplate()
        {
            var j = new JObject();
            foreach (var entity in _entityRegistry.Entities)
            {
                var ours = Ours(entity).ToList();
                if (ours.Count == 0) continue;
                string key = Template(entity) + ": " + string.Join(",", ours);
                j[key] = (j[key]?.Value<int>() ?? 0) + 1;
            }
            return j;
        }

        private static IEnumerable<string> Ours(BaseComponent entity) =>
            entity.AllComponents.Select(c => c.GetType()).Where(t => (t.Namespace ?? "").StartsWith("Pandaborn")).Select(t => t.Name).Distinct();

        private IEnumerable<T> Entities<T>() where T : BaseComponent =>
            _entityRegistry.Entities.Select(e => e.GetComponent<T>()).Where(c => c != null);

        private static string Template(BaseComponent c)
        {
            try { return c.GetComponent<TemplateSpec>()?.TemplateName ?? c.GameObject.name; }
            catch (Exception) { return "?"; }
        }

        private void Event(string kind, JToken data)
        {
            _events.Add(new JObject { ["t"] = Math.Round(_dayNightCycle.PartialDayNumber, 3), ["kind"] = kind, ["data"] = data });
        }

        private void Write()
        {
            _lastWrite = Time.unscaledTime;
            try
            {
                var walk = new JObject();
                foreach (var kv in _walk)
                    walk[kv.Key] = new JObject
                    {
                        ["movingHours"] = Math.Round(kv.Value[1], 3),
                        ["measuredTilesPerHour"] = kv.Value[1] > 0 ? Math.Round(kv.Value[0] / kv.Value[1], 3) : 0,
                        ["nominalSpeed"] = kv.Value[1] > 0 ? Math.Round(kv.Value[2] / kv.Value[1], 4) : 0
                    };
                _out["walking"] = walk;
                _out["final"] = new JObject { ["bell"] = Bell(), ["goods"] = Goods(), ["messages"] = Messages(), ["store"] = Store(), ["tutorial"] = Tutorial(), ["oursByTemplate"] = OursByTemplate() };
                if (HarnessBridge.OutputDir != null)
                    File.WriteAllText(Path.Combine(HarnessBridge.OutputDir, "stage0.json"), _out.ToString(Formatting.Indented));
                var result = HarnessBridge.Result;
                if (result != null) result["stage0"] = new JObject { ["features"] = _out["features"], ["bell"] = _out["final"]["bell"] };
            }
            catch (Exception e) { Debug.LogError("[Pandaborn.Stage0] writing stage0.json failed: " + e); }
        }

        // ------------------------------------------------------------------ screenshots

        private void StepShots()
        {
            if (_shot == null)
            {
                if (_shotQueue.Count == 0) return;
                _shot = _shotQueue.Dequeue();
                _shotStep = 0;
            }
            if (Time.unscaledTime < _shotWait) return;
            string name = (string)_shot["name"];
            switch (_shotStep)
            {
                case 0:
                {
                    BaseComponent target = null;
                    switch ((string)_shot["select"] ?? "none")
                    {
                        case "inkpaw": target = Adults().FirstOrDefault(c => Ours(c).Contains("BellRestedBonus")) ?? Adults().FirstOrDefault(); break;
                        case "bamboo": target = _bamboo.FirstOrDefault(b => b); break;
                        case "lumberjack": target = Entities<BlockObject>().FirstOrDefault(b => Template(b).StartsWith("LumberjackFlag")); break;
                        case "teahouse": target = Entities<BlockObject>().FirstOrDefault(b => Template(b).StartsWith("PandabornStage0Teahouse")); break;
                        case "campfire": target = Entities<BlockObject>().FirstOrDefault(b => Template(b) == "Campfire.Folktails"); break;
                        case "lumbermill": target = Entities<BlockObject>().FirstOrDefault(b => Template(b).StartsWith("LumberMill")); break;
                    }
                    if (target) _entitySelectionService.SelectAndFocusOn(target);
                    else _entitySelectionService.Unselect();
                    _shotStep = 1;
                    _shotWait = Time.unscaledTime + 1.5f;
                    return;
                }
                case 1:
                {
                    string file = Path.Combine(HarnessBridge.OutputDir, "s0_" + name + ".png");
                    ScreenCapture.CaptureScreenshot(file);
                    Event("shot", new JObject { ["name"] = name, ["file"] = Path.GetFileName(file), ["bell"] = Bell() });
                    _shotStep = 2;
                    _shotWait = Time.unscaledTime + 1f;
                    return;
                }
                default:
                    try { _entitySelectionService.Unselect(); }
                    catch (Exception) { }
                    _shot = null;
                    return;
            }
        }
    }
}
