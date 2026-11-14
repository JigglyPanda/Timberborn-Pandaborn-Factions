using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Reflection;
using Newtonsoft.Json.Linq;
using Timberborn.BlueprintSystem;
using Timberborn.GameFactionSystem;

namespace Pandaborn.Stage0
{
    /// <summary>
    /// Dev only. A blueprint modifier provider that adds nothing: SpecService asks every provider for modifiers exactly
    /// once per blueprint, at the moment that blueprint is first deserialised (SpecService.Deserialize, lazily). So this
    /// records, for every blueprint, when it was first read, by whom (first game frame on the stack outside the
    /// blueprint system), and whether the faction's BlueprintModifiers were already initialised at that moment
    /// (FactionService.Load). Blueprints first read before that can never receive a faction modifier.
    /// </summary>
    public class BlueprintTracer : IBlueprintModifierProvider
    {
        public static readonly JArray Reads = new JArray();
        private static int _sequence;
        private readonly FactionBlueprintModifierProvider _factionProvider;
        private readonly PropertyInfo _initialized;

        public BlueprintTracer(FactionBlueprintModifierProvider factionProvider)
        {
            _factionProvider = factionProvider;
            _initialized = typeof(FactionBlueprintModifierProvider).GetProperty("Initialized", BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public);
        }

        public string ModifierName => "Pandaborn stage-0 tracer";

        public IEnumerable<string> GetModifiers(string blueprintPath)
        {
            Record(blueprintPath);
            yield break;
        }

        private void Record(string path)
        {
            try
            {
                bool? ready = _initialized != null ? (bool?)(bool)_initialized.GetValue(_factionProvider) : null;
                Reads.Add(new JObject
                {
                    ["seq"] = _sequence++,
                    ["path"] = path,
                    ["factionModifiersReady"] = ready.HasValue ? (JToken)ready.Value : JValue.CreateNull(),
                    ["reader"] = Reader()
                });
            }
            catch (Exception e)
            {
                Reads.Add(new JObject { ["seq"] = _sequence++, ["path"] = path, ["error"] = e.Message });
            }
        }

        private static string Reader()
        {
            var frames = new StackTrace(2, false).GetFrames();
            if (frames == null) return "";
            var chain = new List<string>();
            foreach (var f in frames)
            {
                var m = f.GetMethod();
                var t = m?.DeclaringType;
                if (t == null) continue;
                string ns = t.Namespace ?? "";
                if (ns.StartsWith("System") || ns.StartsWith("Timberborn.BlueprintSystem") || ns.StartsWith("Pandaborn.Stage0")) continue;
                string name = (t.DeclaringType != null && t.Name.StartsWith("<") ? t.DeclaringType.Name : t.Name) + "." + m.Name;
                if (chain.Count == 0 || chain[chain.Count - 1] != name) chain.Add(name);
                if (chain.Count == 3) break;
            }
            return string.Join(" < ", chain);
        }
    }
}
