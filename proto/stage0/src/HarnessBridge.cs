using System;
using System.Linq;
using System.Reflection;
using Newtonsoft.Json.Linq;

namespace Pandaborn.Stage0
{
    /// <summary>
    /// Dev only. Talks to the PandabornDevHarness mod (when it is loaded and has an active test request) by reflection, so
    /// this prototype has no compile-time or load-time dependency on it. Everything here is inert in a normal game.
    /// </summary>
    public static class HarnessBridge
    {
        private static bool _resolved;
        private static Type _harness;

        private static Type Harness
        {
            get
            {
                if (_resolved) return _harness;
                _resolved = true;
                try
                {
                    var assembly = AppDomain.CurrentDomain.GetAssemblies().FirstOrDefault(a => a.GetName().Name == "PandabornDevHarness");
                    _harness = assembly?.GetType("PandabornDevHarness.Harness");
                }
                catch (Exception) { _harness = null; }
                return _harness;
            }
        }

        private static object Static(string name)
        {
            var t = Harness;
            if (t == null) return null;
            var p = t.GetProperty(name, BindingFlags.Public | BindingFlags.Static);
            if (p != null) return p.GetValue(null);
            return t.GetField(name, BindingFlags.Public | BindingFlags.Static)?.GetValue(null);
        }

        public static bool Active => Static("Active") is bool b && b;

        public static string OutputDir => Static("OutputDir") as string;

        /// <summary>The harness's live result object (result.json); we only ever add our own key to it.</summary>
        public static JObject Result => Static("Result") as JObject;

        public static JObject RawRequest
        {
            get
            {
                var request = Static("Request");
                return request?.GetType().GetField("Raw")?.GetValue(request) as JObject;
            }
        }

        /// <summary>
        /// The "stage0" section of the test request, or an empty object. When the run loaded a save, the keys of its
        /// "reload" sub-object override the others (the save-and-reload launch reuses the first launch's request).
        /// </summary>
        public static JObject Config
        {
            get
            {
                var config = (RawRequest?["stage0"] as JObject)?.DeepClone() as JObject ?? new JObject();
                if (LoadSave && config["reload"] is JObject reload)
                    foreach (var p in reload.Properties()) config[p.Name] = p.Value.DeepClone();
                return config;
            }
        }

        public static bool LoadSave => RawRequest?["loadSave"]?.Type == JTokenType.Boolean && (bool)RawRequest["loadSave"];

        public static void Info(string message)
        {
            try { Harness?.GetMethod("Info", BindingFlags.Public | BindingFlags.Static)?.Invoke(null, new object[] { "[stage0] " + message }); }
            catch (Exception) { }
        }
    }
}
