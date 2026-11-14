using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Bindito.Core;
using Newtonsoft.Json.Linq;
using Timberborn.BlockSystem;
using Timberborn.Cutting;
using Timberborn.Gathering;
using Timberborn.Goods;
using Timberborn.Growing;
using Timberborn.NaturalResources;
using Timberborn.NaturalResourcesLifecycle;
using Timberborn.NaturalResourcesModelSystem;
using Timberborn.SingletonSystem;
using Timberborn.TemplateSystem;
using UnityEngine;

namespace Pandaborn.PlantsProto
{
    [Context("Game")]
    public class PlantLabConfigurator : Configurator
    {
        protected override void Configure()
        {
            if (!HarnessBridge.Active || !(HarnessBridge.RawRequest?["plantLab"] is JObject)) return;
            Bind<PlantLab>().AsSingleton();
        }
    }

    /// <summary>
    /// Dev only: forces the visual state of plants the harness's water lab spawned, so every model a plant has (seedling,
    /// mature, ripe, dry, dead, stump) can be filmed in one run. Request key "plantLab":
    /// <code>
    /// "plantLab": { "rules": [ { "template": "PandabornTeaBush.Inkpaws", "rect": [x0, y0, x1, y1], "state": "ripe" } ] }
    /// </code>
    /// rect is relative to the water lab's origin (result.json water.origin), like the water lab's own steps. States:
    /// alive (keeps the healthy model even on soil that would make it die), dying (the #Dying model), dead (dies),
    /// ripe (a grown gatherable gets its yield: the detail shows), cut (a grown cuttable is cut: trees show the stump),
    /// buds (the detail map switched on for the grown model, as the Flowering module does a cycle before a flowering).
    /// Applied every half second, so it also catches plants the water lab spawns or grows later. It reports, for the
    /// first plant of every rule, which model nodes are active, their material, mesh size and _EnableDetail.
    /// </summary>
    public class PlantLab : ILoadableSingleton, IUpdatableSingleton
    {
        private static readonly int EnableDetailId = Shader.PropertyToID("_EnableDetail");
        private readonly IBlockService _blockService;
        private JArray _rules;
        private JObject _out;
        private float _next;
        private int _passes;
        private readonly HashSet<int> _done = new HashSet<int>();

        public PlantLab(IBlockService blockService)
        {
            _blockService = blockService;
        }

        public void Load()
        {
            _rules = HarnessBridge.RawRequest["plantLab"]["rules"] as JArray ?? new JArray();
            _out = new JObject { ["rules"] = _rules.Count, ["status"] = "waiting" };
            var result = HarnessBridge.Result;
            if (result != null) result["plantLab"] = _out;
            HarnessBridge.Info("[plants] plant lab loaded: " + _rules.Count + " rules");
        }

        public void UpdateSingleton()
        {
            if (Time.unscaledTime < _next) return;
            _next = Time.unscaledTime + 0.5f;
            var origin = Origin();
            if (origin == null) return;
            _passes++;
            _out["status"] = "running";
            _out["passes"] = _passes;
            var report = new JArray();
            foreach (JObject rule in _rules)
            {
                try { report.Add(Apply(rule, origin.Value)); }
                catch (Exception e) { report.Add(new JObject { ["rule"] = rule.DeepClone(), ["error"] = e.GetType().Name + ": " + e.Message }); }
            }
            _out["report"] = report;
        }

        private static Vector3Int? Origin()
        {
            var o = HarnessBridge.Result?["water"]?["origin"] as JArray;
            if (o == null || o.Count < 3) return null;
            return new Vector3Int((int)o[0], (int)o[1], (int)o[2]);
        }

        private IEnumerable<NaturalResource> PlantsIn(JArray r, Vector3Int origin, string template)
        {
            var seen = new HashSet<NaturalResource>();
            for (int x = Math.Min((int)r[0], (int)r[2]); x <= Math.Max((int)r[0], (int)r[2]); x++)
                for (int y = Math.Min((int)r[1], (int)r[3]); y <= Math.Max((int)r[1], (int)r[3]); y++)
                    for (int dz = -3; dz <= 3; dz++)
                    {
                        var c = origin + new Vector3Int(x, y, dz);
                        if (!_blockService.Contains(c)) continue;
                        foreach (var nr in _blockService.GetObjectsWithComponentAt<NaturalResource>(c))
                        {
                            if (nr == null || !seen.Add(nr)) continue;
                            if (template != null && nr.GetComponent<TemplateSpec>()?.TemplateName != template) continue;
                            yield return nr;
                        }
                    }
        }

        private JObject Apply(JObject rule, Vector3Int origin)
        {
            string template = (string)rule["template"];
            string state = (string)rule["state"] ?? "alive";
            var plants = PlantsIn((JArray)rule["rect"], origin, template).ToList();
            int changed = 0;
            foreach (var p in plants)
            {
                int id = p.GetHashCode();
                var growable = p.GetComponent<Growable>();
                var living = p.GetComponent<LivingNaturalResource>();
                var dying = p.GetComponent<DyingNaturalResource>();
                bool grown = growable == null || growable.IsGrown;
                switch (state)
                {
                    case "alive":
                        if (dying != null && dying.IsDying) { SetDying(dying, false); Refresh(p); changed++; }
                        break;
                    case "dying":
                        if (dying != null && !dying.IsDying) { SetDying(dying, true); Refresh(p); changed++; }
                        break;
                    case "dead":
                        if (living != null && !living.IsDead) { living.Die(); changed++; }
                        break;
                    case "ripe":
                    {
                        if (dying != null && dying.IsDying) { SetDying(dying, false); Refresh(p); }
                        var grower = p.GetComponent<GatherableYieldGrower>();
                        var gatherable = p.GetComponent<Gatherable>();
                        if (grown && grower != null && gatherable != null && !gatherable.Yielder.IsYielding)
                        {
                            grower.FastForwardGrowth(1f);
                            changed++;
                        }
                        break;
                    }
                    case "buds":
                    {
                        // what the Flowering module does a cycle ahead (BudsUseDetail): the detail map on the grown model
                        var mature = p.GameObject.transform.Find("#Models/Mature") ?? FindDeep(p.GameObject.transform, "Mature");
                        if (grown && mature != null)
                            foreach (var r in mature.GetComponentsInChildren<MeshRenderer>(true))
                                if (r.material.HasProperty(EnableDetailId) && r.material.GetFloat(EnableDetailId) < 0.5f)
                                {
                                    r.material.SetFloat(EnableDetailId, 1f);
                                    changed++;
                                }
                        break;
                    }
                    case "cut":
                    {
                        var cuttable = p.GetComponent<Cuttable>();
                        if (grown && cuttable != null && cuttable.Yielder.IsYielding && _done.Add(id))
                        {
                            var y = cuttable.Yielder.Yield;
                            cuttable.Yielder.DecreaseYield(new GoodAmount(y.GoodId, y.Amount));
                            changed++;
                        }
                        break;
                    }
                }
            }
            var entry = new JObject { ["template"] = template, ["state"] = state, ["plants"] = plants.Count, ["changedThisPass"] = changed };
            if (plants.Count > 0) entry["sample"] = Describe(plants[0]);
            return entry;
        }

        private static Transform FindDeep(Transform t, string name)
        {
            foreach (Transform c in t)
            {
                if (c.name == name) return c;
                var f = FindDeep(c, name);
                if (f != null) return f;
            }
            return null;
        }

        private static void SetDying(DyingNaturalResource dying, bool value)
        {
            typeof(DyingNaturalResource).GetProperty("IsDying", BindingFlags.Public | BindingFlags.Instance)?.SetValue(dying, value);
        }

        private static void Refresh(NaturalResource plant)
        {
            var model = plant.GetComponent<NaturalResourceModel>();
            typeof(NaturalResourceModel).GetMethod("ShowCurrentModel", BindingFlags.NonPublic | BindingFlags.Instance)?.Invoke(model, null);
        }

        private static JObject Describe(NaturalResource plant)
        {
            var o = new JObject();
            var growable = plant.GetComponent<Growable>();
            o["grown"] = growable == null || growable.IsGrown;
            o["growth"] = growable != null ? Math.Round(growable.GrowthProgress, 3) : 1.0;
            o["dying"] = plant.GetComponent<DyingNaturalResource>()?.IsDying;
            o["dead"] = plant.GetComponent<LivingNaturalResource>()?.IsDead;
            var gatherable = plant.GetComponent<Gatherable>();
            if (gatherable != null) o["yielding"] = gatherable.Yielder.IsYielding;
            var shown = new JArray();
            foreach (var r in plant.GameObject.GetComponentsInChildren<MeshRenderer>(false))
            {
                if (!r.enabled || !r.gameObject.activeInHierarchy) continue;
                var mf = r.GetComponent<MeshFilter>();
                var mat = r.sharedMaterial;
                var path = new List<string>();
                for (var t = r.transform; t != null && t != plant.Transform; t = t.parent) path.Insert(0, t.name);
                shown.Add(new JObject
                {
                    ["node"] = string.Join("/", path),
                    ["material"] = mat ? mat.name : null,
                    ["shader"] = mat && mat.shader ? mat.shader.name : null,
                    ["mainTex"] = mat && mat.HasProperty("_MainTex") && mat.GetTexture("_MainTex") ? mat.GetTexture("_MainTex").name : null,
                    ["enableDetail"] = mat && mat.HasProperty(EnableDetailId) ? Math.Round(mat.GetFloat(EnableDetailId), 2) : (double?)null,
                    ["vertices"] = mf && mf.sharedMesh ? mf.sharedMesh.vertexCount : 0,
                    ["uv2"] = mf && mf.sharedMesh ? mf.sharedMesh.uv3 != null && mf.sharedMesh.uv3.Length > 0 : false
                });
            }
            o["shown"] = shown;
            return o;
        }
    }
}
