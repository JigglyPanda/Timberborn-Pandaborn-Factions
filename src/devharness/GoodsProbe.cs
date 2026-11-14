using System;
using System.Linq;
using Bindito.Core;
using Newtonsoft.Json.Linq;
using Timberborn.BlueprintSystem;
using Timberborn.Buildings;
using Timberborn.BlockSystem;
using Timberborn.EntitySystem;
using Timberborn.Goods;
using Timberborn.ResourceCountingSystem;
using Timberborn.TimeSystem;
using UnityEngine;
using Timberborn.Cutting;
using Timberborn.Gathering;
using Timberborn.SingletonSystem;
using Timberborn.TemplateSystem;
using Timberborn.UILayoutSystem;
using Timberborn.Yielding;

namespace PandabornDevHarness
{
    [Context("Game")]
    public class GoodsProbeConfigurator : Configurator
    {
        protected override void Configure()
        {
            if (!Harness.Active || !(Harness.Request?.Raw?["goodsProbe"] is JObject)) return;
            Bind<GoodsProbe>().AsSingleton();
        }
    }

    /// <summary>
    /// Reports goods as the running game sees them (after faction blueprint modifiers), and the goods that templates cost
    /// and yield. Active only when request.json has a "goodsProbe" object:
    /// <code>
    /// "goodsProbe": { "goods": [ "Plank", "TreatedPlank" ], "templates": [ "BuildersHut.Inkpaws", "PandabornTimberBamboo.Inkpaws" ] }
    /// </code>
    /// Result under "goodsProbe": per good { inFaction, name, plural, icon, weight }; per template { found, costs: [{ id, amount,
    /// name }], cutYield, gatherYield }. Written once the game is playable.
    /// </summary>
    public class GoodsProbe : ILoadableSingleton, IUpdatableSingleton
    {
        private readonly EventBus _eventBus;
        private readonly IGoodService _goodService;
        private readonly TemplateService _templateService;
        private readonly ResourceCountingService _resourceCountingService;
        private readonly EntityRegistry _entityRegistry;
        private readonly IDayNightCycle _dayNightCycle;
        private readonly Timberborn.WorkSystem.WorkingHoursManager _workingHoursManager;
        private JArray _watch;
        private float _nextWatch = -1f;

        public GoodsProbe(EventBus eventBus, IGoodService goodService, TemplateService templateService,
                          ResourceCountingService resourceCountingService, EntityRegistry entityRegistry,
                          IDayNightCycle dayNightCycle, Timberborn.WorkSystem.WorkingHoursManager workingHoursManager)
        {
            _workingHoursManager = workingHoursManager;
            _eventBus = eventBus;
            _goodService = goodService;
            _templateService = templateService;
            _resourceCountingService = resourceCountingService;
            _entityRegistry = entityRegistry;
            _dayNightCycle = dayNightCycle;
        }

        /// <summary>
        /// "watch": { "everySeconds": 20, "goods": [ ids ], "templates": [ names ] }: a sample every N real seconds of each
        /// good's global stock (stockpiled + buffered output + on its way to storage) and how many of each template exist
        /// finished and unfinished; under "goodsProbe.watch".
        /// </summary>
        public void UpdateSingleton()
        {
            if (_nextWatch < 0f || Harness.Finished || Time.unscaledTime < _nextWatch) return;
            var spec = (JObject)((JObject)Harness.Request.Raw["goodsProbe"])["watch"];
            _nextWatch = Time.unscaledTime + Request.Num(spec, "everySeconds", 20f);
            try
            {
                var sample = new JObject { ["realSeconds"] = Math.Round(Time.unscaledTime, 1),
                                           ["day"] = Math.Round(_dayNightCycle.PartialDayNumber, 3) };
                var goods = new JObject();
                foreach (var token in (spec["goods"] as JArray) ?? new JArray())
                {
                    var c = _resourceCountingService.GetGlobalResourceCount((string)token);
                    goods[(string)token] = c.StockpiledStock + c.BufferedOutputStock + c.CarriedToStockpilesStock;
                }
                sample["goods"] = goods;
                var templates = new JObject();
                foreach (var token in (spec["templates"] as JArray) ?? new JArray())
                {
                    int finished = 0, unfinished = 0;
                    foreach (var entity in _entityRegistry.Entities)
                    {
                        if (!entity) continue;
                        var ts = entity.GetComponent<TemplateSpec>();
                        if (ts == null || ts.TemplateName != (string)token) continue;
                        var bo = entity.GetComponent<BlockObject>();
                        if (bo != null && bo.IsFinished) finished++; else unfinished++;
                    }
                    templates[(string)token] = new JObject { ["finished"] = finished, ["unfinished"] = unfinished };
                }
                sample["templates"] = templates;
                // "bonuses": [ "WorkingSpeed", "MovementSpeed" ]: mean multiplier per character template (the bell)
                if (spec["bonuses"] is JArray bonusIds && bonusIds.Count > 0)
                {
                    var sums = new System.Collections.Generic.Dictionary<string, double[]>();
                    var counts = new System.Collections.Generic.Dictionary<string, int>();
                    foreach (var entity in _entityRegistry.Entities)
                    {
                        if (!entity) continue;
                        var bm = entity.GetComponent<Timberborn.BonusSystem.BonusManager>();
                        var ts = entity.GetComponent<TemplateSpec>();
                        if (bm == null || ts == null) continue;
                        if (!sums.TryGetValue(ts.TemplateName, out var acc))
                        {
                            acc = new double[bonusIds.Count];
                            sums[ts.TemplateName] = acc;
                            counts[ts.TemplateName] = 0;
                        }
                        for (int i = 0; i < bonusIds.Count; i++) acc[i] += bm.Multiplier((string)bonusIds[i]);
                        counts[ts.TemplateName]++;
                    }
                    var bonuses = new JObject();
                    foreach (var kv in sums)
                    {
                        var o = new JObject { ["count"] = counts[kv.Key] };
                        for (int i = 0; i < bonusIds.Count; i++) o[(string)bonusIds[i]] = Math.Round(kv.Value[i] / counts[kv.Key], 4);
                        bonuses[kv.Key] = o;
                    }
                    sample["bonuses"] = bonuses;
                    sample["workingHours"] = Math.Round(_workingHoursManager.WorkedPartOfDay * 24f, 2);
                }
                _watch.Add(sample);
            }
            catch (Exception ex) { Harness.Warn("goods probe watch: " + ex.GetType().Name + ": " + ex.Message); }
        }

        public void Load()
        {
            _eventBus.Register(this);
        }

        [OnEvent]
        public void OnShowPrimaryUI(ShowPrimaryUIEvent e)
        {
            var spec = (JObject)Harness.Request.Raw["goodsProbe"];
            var output = new JObject();
            try
            {
                var goods = new JObject();
                foreach (var token in (spec["goods"] as JArray) ?? new JArray())
                {
                    var id = (string)token;
                    goods[id] = Describe(id);
                }
                output["goods"] = goods;
                var templates = new JObject();
                foreach (var token in (spec["templates"] as JArray) ?? new JArray())
                {
                    var name = (string)token;
                    var entry = new JObject { ["found"] = false };
                    templates[name] = entry;
                    var ts = _templateService.GetAll<TemplateSpec>().FirstOrDefault(t => t.TemplateName == name);
                    if (ts == null) continue;
                    entry["found"] = true;
                    var bp = ts.Blueprint;
                    if (bp.HasSpec<BuildingSpec>())
                        entry["costs"] = new JArray(bp.GetSpec<BuildingSpec>().BuildingCost.Select(c =>
                            new JObject { ["id"] = c.Id, ["amount"] = c.Amount, ["name"] = Name(c.Id) }));
                    if (bp.HasSpec<CuttableSpec>())
                    {
                        var y = bp.GetSpec<CuttableSpec>().Yielder.Yield;
                        entry["cutYield"] = new JObject { ["id"] = y.Id, ["amount"] = y.Amount, ["name"] = Name(y.Id) };
                    }
                    if (bp.HasSpec<GatherableSpec>())
                    {
                        var y = bp.GetSpec<GatherableSpec>().Yielder.Yield;
                        entry["gatherYield"] = new JObject { ["id"] = y.Id, ["amount"] = y.Amount, ["name"] = Name(y.Id) };
                    }
                }
                output["templates"] = templates;
                Harness.Info("goods probe: " + output.ToString(Newtonsoft.Json.Formatting.None));
            }
            catch (Exception ex)
            {
                output["error"] = ex.GetType().Name + ": " + ex.Message;
                Harness.Error("goods probe failed", ex);
            }
            Harness.Result["goodsProbe"] = output;
            if (spec["watch"] is JObject)
            {
                _watch = new JArray();
                output["watch"] = _watch;
                _nextWatch = Time.unscaledTime + 1f;
            }
        }

        private JObject Describe(string id)
        {
            var o = new JObject { ["inFaction"] = _goodService.HasGood(id) };
            var g = _goodService.GetGoodOrNull(id);
            if (g == null) return o;
            o["name"] = g.DisplayName?.Value;
            o["plural"] = g.PluralDisplayName?.Value;
            o["icon"] = g.Icon?.Path;
            o["weight"] = g.Weight;
            return o;
        }

        private string Name(string id)
        {
            return _goodService.GetGoodOrNull(id)?.PluralDisplayName?.Value;
        }
    }
}
