using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using Bindito.Core;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Timberborn.BaseComponentSystem;
using Timberborn.BatchControl;
using Timberborn.Beavers;
using Timberborn.Characters;
using Timberborn.CoreUI;
using Timberborn.EntitySystem;
using Timberborn.GameDistricts;
using Timberborn.GameFactionSystem;
using Timberborn.Localization;
using Timberborn.SelectionSystem;
using Timberborn.SingletonSystem;
using Timberborn.TimeSystem;
using Timberborn.TutorialSettingsSystem;
using Timberborn.TutorialSystem;
using Timberborn.UILayoutSystem;
using UnityEngine;
using UnityEngine.UIElements;

namespace Pandaborn.Foundation
{
    [Context("Game")]
    public class FoundationProbeConfigurator : Configurator
    {
        protected override void Configure()
        {
            if (!HarnessBridge.Active) return;
            Bind<FoundationProbe>().AsSingleton();
        }
    }

    /// <summary>
    /// Dev only. Measures the foundation features in a harness run and writes foundation.json next to result.json. It reads
    /// the Pandaborn assemblies by reflection only, so it loads whatever is on. Request section "foundation" (a "reload"
    /// sub-object overrides keys in the save-and-reload launch; a chained "then" game may carry its own section):
    ///   devSwitchNext: text for the owner mod's pandaborn.dev.txt for the NEXT launch ("" deletes it)
    ///   carrierWriteAtRunHour: write entry "DevCarrier" into every entity's Core carrier (as if an earlier session had)
    ///   dataAtRunHour: record features, report, messages, words and carriers
    ///   shots: [ { name, atRunHour, what } ]  what = populationTab | migrationTab | populationTooltip | districtCenter | inkpaw | none
    /// </summary>
    public class FoundationProbe : ILoadableSingleton, IUpdatableSingleton
    {
        private static readonly string[] WordKeys =
        {
            "Beaver.Adult.TemplateName", "Beaver.Child.TemplateName", "Beaver.PluralDisplayName", "Beaver.Population.Children",
            "Beaver.Population.Adults", "BatchControl.PopulationStatistics.BeaverEmployment", "Dwelling.NoUnemployedCanReach",
            "Dwelling.NoBeaverCanReach", "Work.BeaverOnly", "Status.Need.Injury.Short", "Building.Campfire.Description",
            "Building.BeaverStatue.DisplayName", "Population.AllPerished"
        };

        private readonly EventBus _eventBus;
        private readonly IDayNightCycle _dayNightCycle;
        private readonly CharacterPopulation _characterPopulation;
        private readonly EntityRegistry _entityRegistry;
        private readonly EntitySelectionService _entitySelectionService;
        private readonly DistrictCenterRegistry _districtCenterRegistry;
        private readonly IBatchControlBox _batchControlBox;
        private readonly UILayout _uiLayout;
        private readonly FactionService _factionService;
        private readonly ILoc _loc;
        private readonly ITutorialService _tutorialService;
        private readonly TutorialSettings _tutorialSettings;
        private bool? _tutorialSettingBefore;
        private readonly JObject _config;
        private readonly JObject _out = new JObject();
        private readonly JArray _events = new JArray();
        private readonly List<JObject> _pending = new List<JObject>();
        private readonly Queue<JObject> _shots = new Queue<JObject>();
        private bool _primaryUi;
        private bool _started;
        private float _startHours;
        private float _lastWrite;
        private JObject _shot;
        private int _shotStep;
        private float _shotWait;
        private VisualElement _tooltipTarget;

        public FoundationProbe(EventBus eventBus, IDayNightCycle dayNightCycle, CharacterPopulation characterPopulation, EntityRegistry entityRegistry,
                               EntitySelectionService entitySelectionService, DistrictCenterRegistry districtCenterRegistry, IBatchControlBox batchControlBox,
                               UILayout uiLayout, FactionService factionService, ILoc loc, ITutorialService tutorialService, TutorialSettings tutorialSettings)
        {
            _eventBus = eventBus;
            _dayNightCycle = dayNightCycle;
            _characterPopulation = characterPopulation;
            _entityRegistry = entityRegistry;
            _entitySelectionService = entitySelectionService;
            _districtCenterRegistry = districtCenterRegistry;
            _batchControlBox = batchControlBox;
            _uiLayout = uiLayout;
            _factionService = factionService;
            _loc = loc;
            _tutorialService = tutorialService;
            _tutorialSettings = tutorialSettings;
            _config = HarnessBridge.Config;
        }

        public void Load()
        {
            _eventBus.Register(this);
            _out["config"] = _config.DeepClone();
            _out["loadSave"] = HarnessBridge.LoadSave;
            _out["events"] = _events;
            if (_config["shots"] is JArray a) foreach (var s in a.OfType<JObject>()) _pending.Add(new JObject { ["kind"] = "shot", ["step"] = s.DeepClone() });
            foreach (var key in new[] { "carrierWriteAtRunHour", "dataAtRunHour", "tutorialNextAtRunHour" })
                if (_config[key] != null && _config[key].Type != JTokenType.Null) _pending.Add(new JObject { ["kind"] = key, ["step"] = new JObject { ["atRunHour"] = _config[key] } });
            WriteDevSwitch();
            _out["atLoad"] = Data("load");
            HarnessBridge.Info("foundation probe loaded; faction " + _factionService.Current?.Id + "; words " + Static("Pandaborn.Words.WordsService, Pandaborn.Words", "State"));
        }

        [OnEvent]
        public void OnShowPrimaryUI(ShowPrimaryUIEvent e) => _primaryUi = true;

        public void UpdateSingleton()
        {
            if (!_primaryUi) return;
            try
            {
                float hours = _dayNightCycle.PartialDayNumber * 24f;
                if (!_started)
                {
                    if (!(HarnessBridge.Result?["run"] is JObject)) return;
                    _started = true;
                    _startHours = hours;
                }
                float runHour = hours - _startHours;
                for (int i = _pending.Count - 1; i >= 0; i--)
                {
                    var p = _pending[i];
                    if (runHour < (float)p["step"]["atRunHour"]) continue;
                    _pending.RemoveAt(i);
                    switch ((string)p["kind"])
                    {
                        case "shot": _shots.Enqueue((JObject)p["step"]); break;
                        case "carrierWriteAtRunHour": WriteCarriers(); break;
                        case "dataAtRunHour": _out["data"] = Data("run hour " + Math.Round(runHour, 2)); break;
                        case "tutorialNextAtRunHour":
                            try { _tutorialService.StartNextStage((string)_config["tutorialId"] ?? "PandabornDevGoods"); _events.Add(new JObject { ["kind"] = "tutorialNext", ["data"] = "called" }); }
                            catch (Exception e) { _events.Add(new JObject { ["kind"] = "tutorialNextError", ["data"] = e.Message }); }
                            break;
                    }
                }
                StepShots();
                if (_started && _tutorialSettingBefore == null && _config["showTutorialPanelUntilRunHour"] != null && !_tutorialShown) ShowTutorialPanel();
                if (_tutorialSettingBefore != null && runHour >= (_config["showTutorialPanelUntilRunHour"]?.Value<float>() ?? 0f)) RestoreTutorialSetting();
                if (Time.unscaledTime - _lastWrite > 5f) Write();
            }
            catch (Exception e)
            {
                Debug.LogError("[Pandaborn.Foundation] probe failed: " + e);
                _events.Add(new JObject { ["kind"] = "probeError", ["data"] = e.ToString() });
                RestoreTutorialSetting();
                _primaryUi = false;
                Write();
            }
        }

        // ------------------------------------------------------------------ data

        private JObject Data(string when)
        {
            var d = new JObject { ["when"] = when, ["faction"] = _factionService.Current?.Id };
            var units = new JArray();
            string report = AppDomain.CurrentDomain.GetData("Pandaborn.Boot.Report") as string ?? "";
            foreach (var line in report.Split(new[] { '\n' }, StringSplitOptions.RemoveEmptyEntries)) units.Add(line.Replace('\t', ' '));
            d["units"] = units;
            d["owner"] = AppDomain.CurrentDomain.GetData("Pandaborn.Boot.Owner") as string;
            d["duplicates"] = AppDomain.CurrentDomain.GetData("Pandaborn.Boot.Duplicates") as string;
            d["dev"] = AppDomain.CurrentDomain.GetData("Pandaborn.Boot.Dev") as string;
            d["assemblies"] = new JArray(AppDomain.CurrentDomain.GetAssemblies().Select(x => x.GetName().Name).Where(n => n.StartsWith("Pandaborn")).OrderBy(n => n));
            d["report"] = Static("Pandaborn.Core.FeatureNotices, Pandaborn.Core", "LastReport") as string;
            d["messages"] = new JArray(((Static("Pandaborn.Core.Messenger, Pandaborn.Core", "Log") as IEnumerable<string>) ?? new string[0]).ToArray());
            d["degraded"] = JToken.FromObject(Static("Pandaborn.Core.FeatureRegistry, Pandaborn.Core", "Degraded") ?? new Dictionary<string, string>());
            d["words"] = new JObject
            {
                ["state"] = Static("Pandaborn.Words.WordsService, Pandaborn.Words", "State") as string,
                ["applied"] = JToken.FromObject(Static("Pandaborn.Words.WordsService, Pandaborn.Words", "AppliedCount") ?? -1),
                ["skipped"] = new JArray(((Static("Pandaborn.Words.WordsService, Pandaborn.Words", "Skipped") as IEnumerable<string>) ?? new string[0]).ToArray()),
                ["texts"] = new JObject(WordKeys.Select(k => new JProperty(k, _loc.T(k))))
            };
            d["carrierReports"] = new JArray(((Static("Pandaborn.DevCarrier.DevCarrierComponent, Pandaborn.DevCarrier", "Reports") as IEnumerable<string>) ?? new string[0]).ToArray());
            d["carriers"] = Carriers();
            d["noData"] = JToken.FromObject(Static("Pandaborn.Core.FeatureRegistry, Pandaborn.Core", "NoData") ?? new Dictionary<string, string>());
            d["tutorial"] = Tutorial();
            d["bell"] = Bell();
            d["colonists"] = new JArray(_characterPopulation.Characters.Where(c => c).Take(6).Select(c => c.FirstName));
            return d;
        }

        private bool _tutorialShown;

        /// <summary>The owner's "disable tutorial" setting hides the panel: switched off for the shots only, recorded in the run
        /// folder before the change and verified after the restore (like mod states).</summary>
        private void ShowTutorialPanel()
        {
            _tutorialShown = true;
            try
            {
                _tutorialSettingBefore = _tutorialSettings.DisableTutorial;
                File.WriteAllText(Path.Combine(HarnessBridge.OutputDir, "settings.before.json"),
                    new JObject { ["setting"] = "TutorialSettings.DisableTutorial", ["value"] = _tutorialSettingBefore.Value }.ToString());
                if (_tutorialSettingBefore.Value) _tutorialSettings.DisableTutorial = false;
                _events.Add(new JObject { ["kind"] = "tutorialSetting", ["data"] = "was " + _tutorialSettingBefore.Value + "; panel shown" });
            }
            catch (Exception e) { _events.Add(new JObject { ["kind"] = "tutorialSettingError", ["data"] = e.Message }); }
        }

        private void RestoreTutorialSetting()
        {
            if (_tutorialSettingBefore == null) return;
            try
            {
                if (_tutorialSettings.DisableTutorial != _tutorialSettingBefore.Value) _tutorialSettings.DisableTutorial = _tutorialSettingBefore.Value;
                bool ok = _tutorialSettings.DisableTutorial == _tutorialSettingBefore.Value;
                File.WriteAllText(Path.Combine(HarnessBridge.OutputDir, "settings.restore.json"),
                    new JObject { ["setting"] = "TutorialSettings.DisableTutorial", ["expected"] = _tutorialSettingBefore.Value,
                                  ["actual"] = _tutorialSettings.DisableTutorial, ["verified"] = ok }.ToString());
                if (!ok) Debug.LogError("[Pandaborn.Foundation] could not restore the owner's DisableTutorial setting; restore it by hand");
                _events.Add(new JObject { ["kind"] = "tutorialSetting", ["data"] = "restored to " + _tutorialSettings.DisableTutorial + (ok ? " (verified)" : " (NOT VERIFIED)") });
            }
            catch (Exception e) { _events.Add(new JObject { ["kind"] = "tutorialSettingError", ["data"] = e.Message }); }
            _tutorialSettingBefore = null;
        }

        private JObject Tutorial()
        {
            var t = new JObject();
            try
            {
                var type = _tutorialService.GetType();
                const BindingFlags flags = BindingFlags.Instance | BindingFlags.NonPublic;
                if (type.GetField("_tutorialConfigurations", flags)?.GetValue(_tutorialService) is IEnumerable configs)
                    t["configurations"] = new JArray(configs.Cast<TutorialConfiguration>().Select(c =>
                        c.TutorialId + " stages=" + c.TutorialStages.Length + " steps=" + c.TutorialStages.Sum(s => s.TutorialSteps.Length)
                        + " requires=[" + string.Join(",", c.RequiredTutorialIds) + "]"));
                if (type.GetField("_activeTutorialStages", flags)?.GetValue(_tutorialService) is IDictionary active)
                {
                    var a = new JObject();
                    foreach (DictionaryEntry kv in active)
                    {
                        var stage = kv.Value as TutorialStage;
                        a[(string)kv.Key] = stage == null ? null : new JObject
                        {
                            ["stage"] = stage.Id, ["achieved"] = stage.AllStepsAchieved,
                            ["steps"] = new JArray(stage.TutorialSteps.Select(s => { try { return s.Step.Description() + (s.Step.Achieved() ? " [achieved]" : ""); } catch (Exception e) { return "error " + e.Message; } }))
                        };
                    }
                    t["active"] = a;
                }
                if (type.GetField("_finishedTutorials", flags)?.GetValue(_tutorialService) is IEnumerable<string> finished) t["finished"] = new JArray(finished);
            }
            catch (Exception e) { t["error"] = e.Message; }
            return t;
        }

        private static JObject Bell()
        {
            var j = new JObject();
            var type = Type.GetType("Pandaborn.Bell.BellService, Pandaborn.Bell");
            var s = type?.GetProperty("Current")?.GetValue(null);
            j["module"] = type != null;
            if (s != null)
                foreach (var p in new[] { "Active", "LockedHours", "Suggested", "Settled", "HasLockedDay" })
                    j[p] = JToken.FromObject(type.GetProperty(p)?.GetValue(s) ?? "n/a");
            j["rings"] = new JArray(((type?.GetField("Rings")?.GetValue(null) as IEnumerable<string>) ?? new string[0]).ToArray());
            return j;
        }

        private JArray Carriers()
        {
            var list = new JArray();
            var type = Type.GetType("Pandaborn.Core.PandabornEntityState, Pandaborn.Core");
            if (type == null) return list;
            foreach (var entity in _entityRegistry.Entities)
            {
                var c = entity.AllComponents.FirstOrDefault(x => x.GetType() == type);
                if (c == null) continue;
                var o = new JObject { ["entity"] = Name(entity), ["loadedFromSave"] = (bool)type.GetProperty("LoadedFromSave").GetValue(c) };
                foreach (string f in (IEnumerable<string>)type.GetProperty("Features").GetValue(c))
                {
                    var args = new object[] { f, 0, null };
                    if ((bool)type.GetMethod("TryGet").Invoke(c, args)) o[f] = "v" + args[1] + " " + args[2];
                    else o[f] = "(writer only)";
                }
                list.Add(o);
            }
            return list;
        }

        private void WriteCarriers()
        {
            var type = Type.GetType("Pandaborn.Core.PandabornEntityState, Pandaborn.Core");
            int n = 0;
            if (type != null)
                foreach (var entity in _entityRegistry.Entities)
                {
                    var c = entity.AllComponents.FirstOrDefault(x => x.GetType() == type);
                    if (c == null) continue;
                    type.GetMethod("Set").Invoke(c, new object[] { "DevCarrier", 1, "writtenWhileOff=1;name=" + Uri.EscapeDataString(Name(entity)) });
                    n++;
                }
            _events.Add(new JObject { ["kind"] = "carrierWrite", ["data"] = n + " carrier(s) given a DevCarrier entry" });
        }

        private static string Name(BaseComponent entity)
        {
            var ch = entity.GetComponent<Character>();
            return ch != null ? ch.FirstName : entity.GameObject.name;
        }

        private static object Static(string typeName, string member)
        {
            try
            {
                var t = Type.GetType(typeName);
                if (t == null) return null;
                var p = t.GetProperty(member, BindingFlags.Public | BindingFlags.Static);
                if (p != null) return p.GetValue(null);
                return t.GetField(member, BindingFlags.Public | BindingFlags.Static)?.GetValue(null);
            }
            catch (Exception) { return null; }
        }

        private void WriteDevSwitch()
        {
            if (!(_config["devSwitchNext"] is JValue v)) return;
            try
            {
                string owner = AppDomain.CurrentDomain.GetData("Pandaborn.Boot.Owner") as string;
                if (string.IsNullOrEmpty(owner)) return;
                string file = Path.Combine(owner, "pandaborn.dev.txt");
                string text = (string)v ?? "";
                if (text.Length == 0) { if (File.Exists(file)) File.Delete(file); _events.Add(new JObject { ["kind"] = "devSwitch", ["data"] = "deleted " + file }); }
                else { File.WriteAllText(file, text.Replace(";", "\n")); _events.Add(new JObject { ["kind"] = "devSwitch", ["data"] = "wrote " + file + ": " + text }); }
            }
            catch (Exception e) { _events.Add(new JObject { ["kind"] = "devSwitchError", ["data"] = e.Message }); }
        }

        private void Write()
        {
            _lastWrite = Time.unscaledTime;
            try
            {
                _out["final"] = Data("final");
                if (HarnessBridge.OutputDir != null) File.WriteAllText(Path.Combine(HarnessBridge.OutputDir, "foundation.json"), _out.ToString(Formatting.Indented));
            }
            catch (Exception e) { Debug.LogError("[Pandaborn.Foundation] writing foundation.json failed: " + e); }
        }

        // ------------------------------------------------------------------ screenshots

        private void StepShots()
        {
            if (_shot == null)
            {
                if (_shots.Count == 0) return;
                _shot = _shots.Dequeue();
                _shotStep = 0;
            }
            if (Time.unscaledTime < _shotWait) return;
            string what = (string)_shot["what"] ?? "none";
            switch (_shotStep)
            {
                case 0:
                    try { Prepare(what); }
                    catch (Exception e) { _events.Add(new JObject { ["kind"] = "shotError", ["data"] = what + ": " + e.Message }); }
                    _shotStep = 1;
                    _shotWait = Time.unscaledTime + 2f;
                    return;
                case 1:
                {
                    string file = Path.Combine(HarnessBridge.OutputDir, "f_" + (string)_shot["name"] + ".png");
                    ScreenCapture.CaptureScreenshot(file);
                    _events.Add(new JObject { ["kind"] = "shot", ["data"] = Path.GetFileName(file) });
                    _shotStep = 2;
                    _shotWait = Time.unscaledTime + 1f;
                    return;
                }
                default:
                    try { Cleanup(what); }
                    catch (Exception e) { _events.Add(new JObject { ["kind"] = "shotCleanupError", ["data"] = e.Message }); }
                    _shot = null;
                    return;
            }
        }

        private void Prepare(string what)
        {
            switch (what)
            {
                case "populationTab": _batchControlBox.OpenCharactersTab(); break;
                case "migrationTab": _batchControlBox.OpenMigrationTab(); break;
                case "districtCenter":
                    var dc = _districtCenterRegistry.FinishedDistrictCenters.FirstOrDefault();
                    if (dc) _entitySelectionService.SelectAndFocusOn(dc);
                    break;
                case "inkpaw":
                    var adult = _characterPopulation.Characters.FirstOrDefault(c => c && c.GetComponent<AdultSpec>() != null);
                    if (adult) _entitySelectionService.SelectAndFocusOn(adult);
                    break;
                case "populationTooltip":
                {
                    // find the top-left population button through the panel root and send it the hover event the tooltip
                    // system listens for
                    var probe = new VisualElement();
                    _uiLayout.AddTopLeft(probe, 99);
                    var root = probe.panel?.visualTree;
                    probe.RemoveFromHierarchy();
                    _tooltipTarget = root?.Q<Button>("PopulationData");
                    if (_tooltipTarget == null) { _events.Add(new JObject { ["kind"] = "shotError", ["data"] = "PopulationData button not found" }); break; }
                    using (var evt = MouseEnterEvent.GetPooled()) { evt.target = _tooltipTarget; _tooltipTarget.SendEvent(evt); }
                    break;
                }
            }
        }

        private void Cleanup(string what)
        {
            if (what == "populationTab" || what == "migrationTab")
            {
                if (_batchControlBox is IPanelController panel) panel.OnUICancelled();
            }
            else if (what == "populationTooltip" && _tooltipTarget != null)
            {
                using (var evt = MouseLeaveEvent.GetPooled()) { evt.target = _tooltipTarget; _tooltipTarget.SendEvent(evt); }
                _tooltipTarget = null;
            }
            else _entitySelectionService.Unselect();
        }
    }
}
