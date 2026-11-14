using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using Timberborn.ModManagerScene;
using Debug = UnityEngine.Debug;

namespace Pandaborn.Bootstrap
{
    /// <summary>
    /// The mod starter: the only type the game finds by itself. The game loads every *.dll of every enabled mod, then runs
    /// each mod's IModStarter once, then builds the MainMenu context (Bindito scans the configurators of every assembly in
    /// the AppDomain) and only then creates the SpecTypeCache, so assemblies loaded here behave like normal mod DLLs.
    /// It never throws: anything that goes wrong turns a feature off and is reported (see FeatureReport).
    /// </summary>
    public class PandabornStarter : IModStarter
    {
        public void StartMod(IModEnvironment modEnvironment)
        {
            try { Boot.Run(modEnvironment.ModPath); }
            catch (Exception e) { Debug.LogError("[Pandaborn] bootstrap failed; every Pandaborn code feature is off: " + e); }
        }
    }

    /// <summary>
    /// Loads Pandaborn.Specs and Pandaborn.Core (always), then each feature module listed in Modules/modules.txt whose
    /// required-API list resolves against the running game. Each assembly is loaded at most once per AppDomain, so a
    /// second enabled copy of the mod (local folder plus Workshop) does nothing but report itself.
    /// The outcome is published in AppDomain data for Pandaborn.Core (no compile-time link between the two):
    ///   Pandaborn.Boot.Owner       mod path of the copy that loaded the code
    ///   Pandaborn.Boot.Duplicates  mod paths of other copies, one per line
    ///   Pandaborn.Boot.Report      one line per unit: id TAB state TAB reason (state: on, off, forced-off)
    /// </summary>
    internal static class Boot
    {
        public const string OwnerKey = "Pandaborn.Boot.Owner";
        public const string DuplicatesKey = "Pandaborn.Boot.Duplicates";
        public const string ReportKey = "Pandaborn.Boot.Report";
        private const string LoadedKeyPrefix = "Pandaborn.Boot.Loaded.";

        private static readonly Dictionary<string, Assembly> Loaded = new Dictionary<string, Assembly>(StringComparer.OrdinalIgnoreCase);

        public static void Run(string modPath)
        {
            var domain = AppDomain.CurrentDomain;
            if (domain.GetData(OwnerKey) is string owner)
            {
                string previous = domain.GetData(DuplicatesKey) as string;
                domain.SetData(DuplicatesKey, string.IsNullOrEmpty(previous) ? modPath : previous + "\n" + modPath);
                Debug.LogWarning("[Pandaborn] a second copy of Pandaborn - Factions is enabled (" + modPath + "); its code is not loaded. "
                                 + "Using the copy in " + owner + ". Disable one of them in the mod manager.");
                Bundles.Park(modPath);
                return;
            }
            domain.SetData(OwnerKey, modPath);
            Bundles.Unpark(modPath);
            var started = DateTime.UtcNow;
            var dev = DevSwitch.Read(modPath);
            domain.SetData("Pandaborn.Boot.Dev", string.Join("\n", dev.Lines));
            var report = new List<string[]>();
            domain.AssemblyResolve += ResolveOurs;

            bool specsOn = LoadCore("Specs", Path.Combine(modPath, "Scripts", "Pandaborn.Specs.bin"), dev, report, checkSpecNames: true);
            bool coreOn = specsOn && LoadCore("Core", Path.Combine(modPath, "Scripts", "Pandaborn.Core.bin"), dev, report, checkSpecNames: false);
            if (specsOn && !coreOn && report.Count == 1) report.Add(new[] { "Core", "off", "Specs did not load" });

            foreach (var module in ModuleList.Read(Path.Combine(modPath, "Modules", "modules.txt"), report))
            {
                if (dev.ForcedOff(module.Id)) { report.Add(new[] { module.Id, "forced-off", "dev switch (pandaborn.dev.txt or PANDABORN_DEV)" }); continue; }
                if (!coreOn) { report.Add(new[] { module.Id, "off", "Pandaborn.Core is not loaded" }); continue; }
                string file = Path.Combine(modPath, "Modules", module.File);
                string reason = TryLoad(module.Id, file, dev, checkSpecNames: true);
                report.Add(new[] { module.Id, reason == null ? "on" : "off", reason ?? "" });
            }

            var text = new StringBuilder();
            foreach (var r in report) text.Append(r[0]).Append('\t').Append(r[1]).Append('\t').Append(r[2].Replace('\t', ' ').Replace('\n', ' ')).Append('\n');
            domain.SetData(ReportKey, text.ToString());
            Debug.Log("[Pandaborn] bootstrap from " + modPath + " in " + (int)(DateTime.UtcNow - started).TotalMilliseconds + " ms:\n"
                      + string.Join("\n", report.Select(r => "  " + r[0] + ": " + r[1] + (r[2].Length > 0 ? " (" + r[2] + ")" : ""))));
        }

        private static bool LoadCore(string id, string file, DevSwitch dev, List<string[]> report, bool checkSpecNames)
        {
            string reason = TryLoad(id, file, dev, checkSpecNames);
            report.Add(new[] { id, reason == null ? "on" : "off", reason ?? "" });
            return reason == null;
        }

        /// <summary>Returns null when the assembly is loaded (now or earlier in this AppDomain), else why not.</summary>
        private static string TryLoad(string id, string file, DevSwitch dev, bool checkSpecNames)
        {
            try
            {
                string name = Path.GetFileNameWithoutExtension(file);
                if (AppDomain.CurrentDomain.GetData(LoadedKeyPrefix + name) != null) return null;
                if (!File.Exists(file)) return "file missing: " + Path.GetFileName(file);
                string apiFile = Path.Combine(Path.GetDirectoryName(file), name + ".api.txt");
                if (!File.Exists(apiFile)) return "required-API list missing: " + Path.GetFileName(apiFile);
                var lines = File.ReadAllLines(apiFile).Where(l => l.Length > 0 && l[0] != '#').ToList();
                if (dev.SimulatesMissingApi(id)) lines.Add("T\tTimberborn.PandabornSimulated\tTimberborn.PandabornSimulated.MissingType");
                var missing = ApiCheck.Missing(lines);
                if (missing.Count > 0)
                    return "game API changed: " + missing.Count + " missing, e.g. " + string.Join("; ", missing.Take(3));
                if (checkSpecNames)
                {
                    var clash = ApiCheck.SpecNameClashes(lines);
                    if (clash.Count > 0) return "spec class name already defined by another assembly: " + string.Join(", ", clash.Take(5));
                }
                var assembly = Assembly.Load(File.ReadAllBytes(file));
                Loaded[assembly.GetName().Name] = assembly;
                AppDomain.CurrentDomain.SetData(LoadedKeyPrefix + name, file);
                try { assembly.GetTypes(); }
                catch (ReflectionTypeLoadException e)
                {
                    // Too late to undo (an assembly cannot be unloaded); the API check exists to make this unreachable.
                    Debug.LogError("[Pandaborn] " + name + " loaded but some of its types do not: "
                                   + string.Join("; ", e.LoaderExceptions.Where(x => x != null).Select(x => x.Message).Distinct().Take(5)));
                    return "types failed to load after the check passed";
                }
                return null;
            }
            catch (Exception e)
            {
                return "load failed: " + e.GetType().Name + ": " + e.Message;
            }
        }

        private static Assembly ResolveOurs(object sender, ResolveEventArgs args)
        {
            try
            {
                string name = new AssemblyName(args.Name).Name;
                return Loaded.TryGetValue(name, out var assembly) ? assembly : null;
            }
            catch (Exception) { return null; }
        }
    }

    /// <summary>
    /// Two enabled copies of the mod (a local folder and the Workshop, or two local folders) both carry the same asset
    /// bundles, and Unity refuses to load a bundle twice: the game's ModAssetBundleLoader then throws and every game fails to
    /// start, before our code could do anything else (verified, run fd-dup-1). Mod starters run before the bundle loader, so
    /// the copy that is not running the code moves its own bundles aside (AssetBundles -> AssetBundles.parked), and the copy
    /// that runs the code moves its own back if an earlier session parked them. Only ever touches this mod's own folder.
    /// </summary>
    internal static class Bundles
    {
        private const string Folder = "AssetBundles";
        private const string Parked = "AssetBundles.parked";

        public static void Park(string modPath) => Move(Path.Combine(modPath, Folder), Path.Combine(modPath, Parked), "parked");

        public static void Unpark(string modPath) => Move(Path.Combine(modPath, Parked), Path.Combine(modPath, Folder), "restored");

        private static void Move(string from, string to, string what)
        {
            try
            {
                if (!Directory.Exists(from)) return;
                var files = Directory.GetFiles(from);
                if (files.Length == 0) return;
                Directory.CreateDirectory(to);
                foreach (var file in files)
                {
                    string target = Path.Combine(to, Path.GetFileName(file));
                    if (File.Exists(target)) File.Delete(target);
                    File.Move(file, target);
                }
                Debug.LogWarning("[Pandaborn] " + what + " " + files.Length + " asset bundle file(s): " + from + " -> " + to);
            }
            catch (Exception e)
            {
                Debug.LogError("[Pandaborn] could not move asset bundles (" + from + " -> " + to + "): " + e.Message);
            }
        }
    }

    internal sealed class ModuleEntry
    {
        public string Id;
        public string File;
    }

    /// <summary>Modules/modules.txt: one module per line, "Id File [description]", whitespace-separated; '#' starts a comment.</summary>
    internal static class ModuleList
    {
        public static List<ModuleEntry> Read(string path, List<string[]> report)
        {
            var result = new List<ModuleEntry>();
            try
            {
                if (!File.Exists(path)) return result;
                foreach (var raw in File.ReadAllLines(path))
                {
                    string line = raw.Trim();
                    if (line.Length == 0 || line[0] == '#') continue;
                    var parts = line.Split(new[] { ' ', '\t' }, 3, StringSplitOptions.RemoveEmptyEntries);
                    if (parts.Length < 2) { report.Add(new[] { line, "off", "bad line in modules.txt" }); continue; }
                    result.Add(new ModuleEntry { Id = parts[0], File = parts[1] });
                }
            }
            catch (Exception e) { report.Add(new[] { "modules.txt", "off", e.Message }); }
            return result;
        }
    }

    /// <summary>
    /// Dev switch, for tests only. A file pandaborn.dev.txt in the mod folder, or the environment variable PANDABORN_DEV
    /// (lines separated by ';'), with lines such as
    ///   force-off: Bell, Names           (the module is not loaded, as if a player had an old game)
    ///   simulate-missing-api: Bell       (the required-API check fails, exercising the "needs update" path)
    /// </summary>
    internal sealed class DevSwitch
    {
        private readonly HashSet<string> _forcedOff = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        private readonly HashSet<string> _missingApi = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        /// <summary>Every dev-switch line, published for Pandaborn.Core (FeatureRegistry.DevFlag) as AppDomain data Pandaborn.Boot.Dev.</summary>
        public readonly List<string> Lines = new List<string>();

        public bool ForcedOff(string id) => _forcedOff.Contains(id) || _forcedOff.Contains("*");
        public bool SimulatesMissingApi(string id) => _missingApi.Contains(id) || _missingApi.Contains("*");

        public static DevSwitch Read(string modPath)
        {
            var dev = new DevSwitch();
            try
            {
                var lines = new List<string>();
                string file = Path.Combine(modPath, "pandaborn.dev.txt");
                if (File.Exists(file)) lines.AddRange(File.ReadAllLines(file));
                string env = Environment.GetEnvironmentVariable("PANDABORN_DEV");
                if (!string.IsNullOrEmpty(env)) lines.AddRange(env.Split(';'));
                foreach (var raw in lines)
                {
                    int colon = raw.IndexOf(':');
                    if (colon < 0 || raw.TrimStart().StartsWith("#")) continue;
                    dev.Lines.Add(raw.Trim());
                    string key = raw.Substring(0, colon).Trim().ToLowerInvariant();
                    var ids = raw.Substring(colon + 1).Split(',').Select(s => s.Trim()).Where(s => s.Length > 0);
                    if (key == "force-off") foreach (var id in ids) dev._forcedOff.Add(id);
                    else if (key == "simulate-missing-api") foreach (var id in ids) dev._missingApi.Add(id);
                }
                if (lines.Count > 0) Debug.LogWarning("[Pandaborn] dev switch active: force-off [" + string.Join(", ", dev._forcedOff)
                                                      + "], simulate-missing-api [" + string.Join(", ", dev._missingApi) + "]");
            }
            catch (Exception e) { Debug.LogWarning("[Pandaborn] dev switch unreadable: " + e.Message); }
            return dev;
        }
    }
}
