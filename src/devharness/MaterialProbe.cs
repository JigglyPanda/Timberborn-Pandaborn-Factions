using System;
using System.Collections.Generic;
using Bindito.Core;
using Newtonsoft.Json.Linq;
using Timberborn.AssetSystem;
using Timberborn.SingletonSystem;
using Timberborn.Timbermesh;
using UnityEngine;

namespace PandabornDevHarness
{
    [Context("Game")]
    public class MaterialProbeConfigurator : Configurator
    {
        protected override void Configure()
        {
            if (!Harness.Active) return;   // no request: bind nothing at all
            Bind<MaterialProbe>().AsSingleton();
        }
    }

    /// <summary>
    /// Records which texture is on a few loaded materials, once the game has loaded ("atLoad") and when the run finishes
    /// ("atEnd"), in result.json "materialProbe". Proves whether a material re-theme (Pandaborn.Look) is in effect: vanilla
    /// albedo names look like "BaseWood_1K_D_Brown", ours start with "PBLook_". Also copies the Pandaborn bootstrap report
    /// (which code features loaded) into "pandabornBoot".
    /// Request: "materialProbe": [ asset paths ] (default: three Folktails materials); checks:
    ///   "materialMainTexPrefix": "PBLook_"      every probed _MainTex name starts with it (atLoad and atEnd)
    ///   "materialMainTexNotPrefix": "PBLook_"   none does
    /// </summary>
    public class MaterialProbe : IPostLoadableSingleton
    {
        private static readonly string[] DefaultPaths =
        {
            "Materials/UberAtlas/Materials/Folktails/BaseWood_Brown.Folktails",
            "Materials/UberAtlas/Materials/Folktails/ThatchedRoof.Folktails",
            "Materials/UberAtlas/Materials/Folktails/WindowsAtlas.Folktails"
        };

        private static Func<JArray> _takeAgain;
        private readonly IMaterialRepository _materialRepository;
        private readonly IAssetLoader _assetLoader;

        public MaterialProbe(IMaterialRepository materialRepository, IAssetLoader assetLoader)
        {
            _materialRepository = materialRepository;
            _assetLoader = assetLoader;
        }

        public void PostLoad()
        {
            try
            {
                var paths = new List<string>();
                if (Harness.Request.Raw["materialProbe"] is JArray wanted) foreach (var p in wanted) paths.Add((string)p);
                else paths.AddRange(DefaultPaths);
                var probe = new JObject { ["atLoad"] = Take(paths) };
                Harness.Result["materialProbe"] = probe;
                _takeAgain = () => Take(paths);
                Harness.Result["pandabornBoot"] = BootReport();
                Harness.Info("material probe: " + Describe((JArray)probe["atLoad"]));
                Harness.WriteResult("running");
            }
            catch (Exception e) { Harness.Warn("material probe failed: " + e.Message); }
        }

        /// <summary>Called when the run finishes: probes the same materials again ("atEnd").</summary>
        public static void ProbeAtEnd()
        {
            var take = _takeAgain;
            _takeAgain = null;
            if (take == null || !(Harness.Result["materialProbe"] is JObject probe)) return;
            try { probe["atEnd"] = take(); }
            catch (Exception e) { probe["atEndError"] = e.Message; }
        }

        private JArray Take(List<string> paths)
        {
            var list = new JArray();
            foreach (var path in paths)
            {
                string name = path.Substring(path.LastIndexOf('/') + 1);
                var entry = new JObject { ["path"] = path, ["name"] = name };
                try { entry["repository"] = Describe(_materialRepository.GetMaterial(name)); }
                catch (Exception e) { entry["repositoryError"] = e.GetType().Name + ": " + e.Message; }
                try { entry["asset"] = Describe(_assetLoader.Load<Material>(path)); }
                catch (Exception e) { entry["assetError"] = e.GetType().Name + ": " + e.Message; }
                entry["mainTex"] = entry["repository"]?["mainTex"] ?? entry["asset"]?["mainTex"];
                list.Add(entry);
            }
            return list;
        }

        private static JObject Describe(Material material)
        {
            if (!material) return new JObject { ["missing"] = true };
            var o = new JObject { ["material"] = material.name, ["entityId"] = material.GetEntityId().ToString(),["shader"] = material.shader ? material.shader.name : null };
            o["mainTex"] = material.HasProperty("_MainTex") && material.GetTexture("_MainTex") ? material.GetTexture("_MainTex").name : null;
            return o;
        }

        private static string Describe(JArray entries)
        {
            var parts = new List<string>();
            foreach (var e in entries) parts.Add((string)e["name"] + " = " + ((string)e["mainTex"] ?? "?"));
            return string.Join(", ", parts.ToArray());
        }

        private static JArray BootReport()
        {
            var list = new JArray();
            if (!(AppDomain.CurrentDomain.GetData("Pandaborn.Boot.Report") is string text)) return list;
            foreach (var line in text.Split('\n'))
            {
                var parts = line.Split('\t');
                if (parts.Length >= 2) list.Add(new JObject { ["id"] = parts[0], ["status"] = parts[1], ["reason"] = parts.Length > 2 ? parts[2] : "" });
            }
            return list;
        }

        /// <summary>Adds the material checks named in request.checks (see the class comment).</summary>
        public static void AddChecks(JObject result, JObject options, Action<string, bool, string> add)
        {
            // "pandabornFeatures": { "Look": "on" | "off" | "forced-off" }: the bootstrap's status of each named feature
            if (options["pandabornFeatures"] is JObject features)
                foreach (var f in features.Properties())
                {
                    string want = (string)f.Value, got = null, reason = "";
                    if (result["pandabornBoot"] is JArray boot)
                        foreach (var b in boot)
                            if (string.Equals((string)b["id"], f.Name, StringComparison.OrdinalIgnoreCase)) { got = (string)b["status"]; reason = (string)b["reason"]; }
                    add("pandabornFeature", got == want, f.Name + ": " + (got ?? "not reported") + (string.IsNullOrEmpty(reason) ? "" : " (" + reason + ")") + ", want " + want);
                }

            string prefix = options["materialMainTexPrefix"]?.Type == JTokenType.String ? (string)options["materialMainTexPrefix"] : null;
            string notPrefix = options["materialMainTexNotPrefix"]?.Type == JTokenType.String ? (string)options["materialMainTexNotPrefix"] : null;
            if (prefix == null && notPrefix == null) return;
            var probe = result["materialProbe"] as JObject;
            var seen = new List<string>();
            bool pass = probe != null, any = false;
            foreach (var when in new[] { "atLoad", "atEnd" })
            {
                if (!(probe?[when] is JArray entries)) continue;
                foreach (var e in entries)
                {
                    any = true;
                    string tex = (string)e["mainTex"] ?? "";
                    if (prefix != null && !tex.StartsWith(prefix, StringComparison.Ordinal)) pass = false;
                    if (notPrefix != null && (tex.Length == 0 || tex.StartsWith(notPrefix, StringComparison.Ordinal))) pass = false;
                    seen.Add(when + " " + (string)e["name"] + "=" + (tex.Length > 0 ? tex : "none"));
                }
            }
            add(prefix != null ? "materialMainTexPrefix" : "materialMainTexNotPrefix", pass && any,
                (prefix != null ? "want _MainTex starting " + prefix : "want _MainTex not starting " + notPrefix) + ": "
                + (any ? string.Join(", ", seen.ToArray()) : "no probe"));
        }
    }
}
