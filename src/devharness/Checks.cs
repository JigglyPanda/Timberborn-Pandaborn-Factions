using System;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;

namespace PandabornDevHarness
{
    /// <summary>Turns the collected result into pass/fail checks. Options come from request.checks.</summary>
    public static class Checks
    {
        public static void Evaluate(JObject result, Request request, string status, int ownProblems, int allProblems)
        {
            var checks = new JArray();
            var options = request.Checks ?? new JObject();

            void Add(string name, bool pass, string detail)
            {
                checks.Add(new JObject { ["name"] = name, ["pass"] = pass, ["detail"] = detail });
            }

            Add("completed", status == "completed", "status " + status);
            bool started = result["game"] is JObject game && (bool?)game["started"] == true;
            Add("gameStarted", started, started ? "new game reached the playing state" : "the game never reached the playing state");

            string active = (string)result["activeFaction"]?["id"];
            Add("faction", string.Equals(active, request.Faction, StringComparison.OrdinalIgnoreCase),
                "requested " + request.Faction + ", active " + (active ?? "none"));

            var population = result["population"] as JObject;
            int adults = (int?)population?["adults"] ?? 0, children = (int?)population?["children"] ?? 0, bots = (int?)population?["bots"] ?? 0;
            int minAdults = Int(options, "minAdults", 1), minChildren = Int(options, "minChildren", 0), minBots = Int(options, "minBots", 0);
            Add("minAdults", adults >= minAdults, adults + " adults (need " + minAdults + ")");
            if (minChildren > 0) Add("minChildren", children >= minChildren, children + " children (need " + minChildren + ")");
            if (minBots > 0) Add("minBots", bots >= minBots, bots + " bots (need " + minBots + ")");

            if (Bool(options, "noOwnErrors", true))
                Add("noOwnErrors", ownProblems == 0, ownProblems + " errors/exceptions matching " + string.Join(", ", request.OwnPatterns));
            if (options["maxErrors"] != null)
            {
                int max = (int)options["maxErrors"];
                Add("maxErrors", allProblems <= max, allProblems + " errors/exceptions in total (max " + max + ")");
            }

            if (request.Buildings.Count > 0)
            {
                int placed = 0;
                if (result["placedBuildings"] is JArray list)
                    foreach (var b in list) if ((bool?)b["placed"] == true) placed++;
                Add("buildingsPlaced", placed == request.Buildings.Count, placed + " of " + request.Buildings.Count + " placed");
            }

            if (request.Screenshots.Count > 0)
            {
                int ok = 0;
                var missing = new List<string>();
                if (result["screenshots"] is JArray shots)
                    foreach (var s in shots)
                    {
                        if (s["error"] == null && s["file"] != null) ok++;
                        else missing.Add((string)s["name"] + ": " + (string)s["error"]);
                    }
                Add("screenshots", ok >= request.Screenshots.Count,
                    ok + " of " + request.Screenshots.Count + " written" + (missing.Count > 0 ? " (" + string.Join("; ", missing.ToArray()) + ")" : ""));
            }

            foreach (var kind in new[] { "adult", "child", "bot" })
            {
                string template = Str(options, kind + "Template");
                string mesh = Str(options, kind + "MeshContains");
                string texture = Str(options, kind + "TextureContains");
                string model = Str(options, kind + "Model");
                string textureAsset = Str(options, kind + "TextureAsset");
                if (template == null && mesh == null && texture == null && model == null && textureAsset == null) continue;
                var samples = new List<JObject>();
                if (result["characterSamples"] is JArray sampled)
                    foreach (var c in sampled) if ((string)c["kind"] == kind) samples.Add((JObject)c);
                if (samples.Count == 0) { Add(kind + "Look", false, "no " + kind + " sampled"); continue; }
                foreach (var s in samples)
                {
                    string t = (string)s["template"] ?? "", m = (string)s["body"]?["mesh"] ?? "", x = (string)s["body"]?["baseMap"] ?? "";
                    string ma = (string)s["body"]?["modelAsset"] ?? "", xa = (string)s["body"]?["baseMapAsset"] ?? "";
                    string v = (string)s["body"]?["vertices"] ?? "?";
                    bool pass = (template == null || t == template)
                                && (mesh == null || m.IndexOf(mesh, StringComparison.OrdinalIgnoreCase) >= 0)
                                && (texture == null || x.IndexOf(texture, StringComparison.OrdinalIgnoreCase) >= 0)
                                && (model == null || string.Equals(ma, model, StringComparison.OrdinalIgnoreCase))
                                && (textureAsset == null || xa.IndexOf(textureAsset, StringComparison.OrdinalIgnoreCase) >= 0);
                    Add(kind + "Look", pass, (string)s["name"] + ": template " + t + ", model " + ma + " (" + m + ", " + v
                                             + " vertices), baseMap " + x + (xa.Length > 0 ? " = " + xa : " (not a faction coat)"));
                }
            }

            string botActive = Str(options, "botTemplateActive");
            if (botActive != null)
            {
                var botNames = new List<string>();
                if (result["characterTemplatesActive"]?["BotSpec"] is JArray botList)
                    foreach (var b in botList) botNames.Add((string)b["template"]);
                Add("botTemplateActive", botNames.Count == 1 && botNames[0] == botActive,
                    "active bot templates: " + (botNames.Count > 0 ? string.Join(", ", botNames.ToArray()) : "none") + " (want " + botActive + ")");
            }

            if (request.BatchControl && status == "completed")
            {
                var failed = new List<string>();
                int opened = 0;
                if (result["batchControl"]?["tabs"] is JArray tabs)
                    foreach (var tab in tabs)
                    {
                        if ((bool?)tab["opened"] == true) opened++;
                        else failed.Add((string)tab["type"] + ": " + (string)tab["error"]);
                    }
                Add("batchControlTabs", opened > 0 && failed.Count == 0,
                    opened + " tab(s) opened" + (failed.Count > 0 ? "; failed: " + string.Join("; ", failed.ToArray()) : ""));
            }

            if (request.SaveName != null)
            {
                var save = result["save"] as JObject;
                bool saved = save != null && (bool?)save["saved"] == true && (bool?)save["exists"] == true;
                Add("saved", saved, save != null ? (string)save["file"] + (saved ? "" : " not written") : "no save attempted");
            }

            var templates = new HashSet<string>();
            if (result["templates"]?["all"] is JArray names) foreach (var n in names) templates.Add((string)n);
            if (options["templatesAvailable"] is JArray wanted)
                foreach (var w in wanted) Add("templateAvailable", templates.Contains((string)w), (string)w);
            if (options["templatesUnavailable"] is JArray unwanted)
                foreach (var w in unwanted) Add("templateUnavailable", !templates.Contains((string)w), (string)w);

            bool allPass = true;
            foreach (var c in checks) allPass &= (bool)c["pass"];
            result["checks"] = checks;
            result["verdict"] = allPass ? "pass" : "fail";
        }

        private static int Int(JObject o, string key, int fallback) { return o[key] == null ? fallback : (int)o[key]; }
        private static bool Bool(JObject o, string key, bool fallback) { return o[key] == null ? fallback : (bool)o[key]; }
        private static string Str(JObject o, string key) { return o[key] == null || o[key].Type == JTokenType.Null ? null : (string)o[key]; }
    }
}
