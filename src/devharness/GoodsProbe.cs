using System;
using System.Linq;
using Bindito.Core;
using Newtonsoft.Json.Linq;
using Timberborn.BlueprintSystem;
using Timberborn.Buildings;
using Timberborn.Goods;
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
    public class GoodsProbe : ILoadableSingleton
    {
        private readonly EventBus _eventBus;
        private readonly IGoodService _goodService;
        private readonly TemplateService _templateService;

        public GoodsProbe(EventBus eventBus, IGoodService goodService, TemplateService templateService)
        {
            _eventBus = eventBus;
            _goodService = goodService;
            _templateService = templateService;
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
