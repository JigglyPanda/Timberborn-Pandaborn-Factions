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
                Bundles.Park(modPath, owner);
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
            if (!specsOn) report.Add(new[] { "Core", "off", "Pandaborn.Specs is not loaded" });

            var modules = ModuleList.Read(Path.Combine(modPath, "Modules", "modules.txt"), report);
            var player = PlayerSwitch.Read();
            player.Announce(modules.Select(m => m.Id).ToList());
            foreach (var module in modules)
            {
                if (dev.ForcedOff(module.Id)) { report.Add(new[] { module.Id, "forced-off", "dev switch (pandaborn.dev.txt or PANDABORN_DEV)" }); continue; }
                if (player.Off(module.Id)) { report.Add(new[] { module.Id, "forced-off", PlayerSwitch.Reason }); continue; }
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
            GameVersion.Log(modPath);
            if (!specsOn)
                // nothing in game can say this (the notices live in Core), and the faction's templates name our spec classes
                Debug.LogError("[Pandaborn] Pandaborn - Factions could not load its data definitions (see the lines above). Inkpaws games will "
                               + "fail to load until the mod is updated or reinstalled; games of other factions are not affected.");
        }

        private static bool LoadCore(string id, string file, DevSwitch dev, List<string[]> report, bool checkSpecNames)
        {
            string reason = TryLoad(id, file, dev, checkSpecNames);
            report.Add(new[] { id, reason == null ? "on" : "off", reason ?? "" });
            return reason == null;
        }

        private static bool IsLoaded(string assemblyName) => AppDomain.CurrentDomain.GetData(LoadedKeyPrefix + assemblyName) != null;

        /// <summary>Returns null when the assembly is loaded (now or earlier in this AppDomain), else why not.</summary>
        private static string TryLoad(string id, string file, DevSwitch dev, bool checkSpecNames)
        {
            try
            {
                string name = Path.GetFileNameWithoutExtension(file);
                if (IsLoaded(name)) return null;
                if (!File.Exists(file)) return "file missing: " + Path.GetFileName(file);
                string apiFile = Path.Combine(Path.GetDirectoryName(file), name + ".api.txt");
                if (!File.Exists(apiFile)) return "required-API list missing: " + Path.GetFileName(apiFile);
                var lines = File.ReadAllLines(apiFile).Where(l => l.Length > 0 && l[0] != '#').ToList();
                if (dev.SimulatesMissingApi(id)) lines.Add("T\tTimberborn.PandabornSimulated\tTimberborn.PandabornSimulated.MissingType");
                var missing = ApiCheck.Missing(lines, IsLoaded);
                if (missing.Count > 0)
                {
                    if (missing.Count > 3) Debug.LogWarning("[Pandaborn] " + name + " is not loaded; everything it misses in this game version:\n  " + string.Join("\n  ", missing));
                    return "game API changed: " + missing.Count + " missing, e.g. " + string.Join("; ", missing.Take(3));
                }
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
                    // The game's SpecTypeCache calls GetTypes() on every assembly, so say plainly what will follow.
                    Debug.LogError("[Pandaborn] " + name + " loaded but some of its types do not, although its game-API check passed. The game "
                                   + "will most likely fail to start any game until Pandaborn - Factions is updated or disabled. Please report this: "
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
    /// that runs the code moves its own back if an earlier session parked them. Only ever touches folders of this mod.
    ///
    /// Failure paths:
    /// * The duplicate's folder cannot be changed (read-only, a file held by another program): for exactly the files that
    ///   stayed, the running copy's same-named files are parked instead, so each bundle is still there once. The running
    ///   copy takes them back at its next start, and the same thing happens again while both copies stay enabled.
    /// * A file is in both folders when the running copy takes its bundles back (the store re-downloaded the bundles of
    ///   a parked copy, perhaps a newer version): the file in AssetBundles is the live one and stays; the parked one goes.
    /// * The process dies half way: every step is a single file move, and both directions finish the job at the next start.
    /// </summary>
    internal static class Bundles
    {
        private const string Folder = "AssetBundles";
        private const string Parked = "AssetBundles.parked";

        /// <summary>Called by a duplicate copy: moves its bundles aside; where it cannot, parks the owner's instead.</summary>
        public static void Park(string modPath, string ownerPath)
        {
            var stuck = Move(Path.Combine(modPath, Folder), Path.Combine(modPath, Parked), true, null, "parked");
            if (stuck.Count == 0 || string.IsNullOrEmpty(ownerPath) || SamePath(modPath, ownerPath)) return;
            var ownerStuck = Move(Path.Combine(ownerPath, Folder), Path.Combine(ownerPath, Parked), true, stuck, "parked (the other copy's could not be moved)");
            if (ownerStuck.Count > 0)
                Debug.LogError("[Pandaborn] two copies of Pandaborn - Factions are enabled and neither copy's asset bundles could be moved aside ("
                               + string.Join(", ", ownerStuck) + "). The game will fail to start until one copy is disabled in the mod manager.");
        }

        /// <summary>Called by the copy that runs the code: takes back bundles an earlier session parked.</summary>
        public static void Unpark(string modPath)
        {
            string parked = Path.Combine(modPath, Parked);
            var stuck = Move(parked, Path.Combine(modPath, Folder), false, null, "restored");
            if (stuck.Count > 0)
                Debug.LogError("[Pandaborn] asset bundles parked by an earlier session could not be moved back (" + string.Join(", ", stuck)
                               + "): move the files in " + parked + " back into " + Path.Combine(modPath, Folder) + " by hand, or reinstall the mod.");
            try
            {
                if (Directory.Exists(parked) && Directory.GetFileSystemEntries(parked).Length == 0) Directory.Delete(parked);
            }
            catch (Exception) { }
        }

        /// <summary>Moves the files of one folder into another, one by one, and returns the names that could not be moved.
        /// When a file is already at the target: replace it (parking), or keep it and drop the source (taking back).</summary>
        private static List<string> Move(string from, string to, bool replace, List<string> only, string what)
        {
            var stuck = new List<string>();
            string[] files;
            try
            {
                if (!Directory.Exists(from)) return stuck;
                files = Directory.GetFiles(from);
                if (only != null) files = files.Where(f => only.Contains(Path.GetFileName(f), StringComparer.OrdinalIgnoreCase)).ToArray();
                if (files.Length == 0) return stuck;
            }
            catch (Exception e)
            {
                Debug.LogError("[Pandaborn] could not list asset bundles in " + from + ": " + e.Message);
                return stuck;
            }
            int moved = 0;
            string firstError = null;
            foreach (var file in files)
            {
                try
                {
                    Directory.CreateDirectory(to);
                    string target = Path.Combine(to, Path.GetFileName(file));
                    if (File.Exists(target))
                    {
                        if (!replace) { File.Delete(file); moved++; continue; }
                        File.Delete(target);
                    }
                    File.Move(file, target);
                    moved++;
                }
                catch (Exception e)
                {
                    stuck.Add(Path.GetFileName(file));
                    if (firstError == null) firstError = e.Message;
                }
            }
            if (moved > 0) Debug.LogWarning("[Pandaborn] " + what + " " + moved + " asset bundle file(s): " + from + " -> " + to);
            if (stuck.Count > 0) Debug.LogWarning("[Pandaborn] could not move " + stuck.Count + " asset bundle file(s) (" + from + " -> " + to + "): " + firstError);
            return stuck;
        }

        private static bool SamePath(string a, string b)
        {
            try { return string.Equals(Path.GetFullPath(a).TrimEnd('\\', '/'), Path.GetFullPath(b).TrimEnd('\\', '/'), StringComparison.OrdinalIgnoreCase); }
            catch (Exception) { return false; }
        }
    }

    /// <summary>
    /// Says in the log which game version the mod was built against (Scripts/Pandaborn.built-for.txt, stamped by the code
    /// build from catalogue/vanilla.pin.json) and which one is running. Three things can fail in Inkpaws games only after
    /// a game update (a faction modifier that names a vanilla blueprint, a frozen .Inkpaws copy of a changed building,
    /// our spec classes not loading), so a bug report should show the two versions at a glance. Log only.
    /// </summary>
    internal static class GameVersion
    {
        public const string FileName = "Pandaborn.built-for.txt";

        public static void Log(string modPath)
        {
            try
            {
                string file = Path.Combine(modPath, "Scripts", FileName);
                string built = File.Exists(file) ? File.ReadAllText(file).Trim() : null;
                string running = Running();
                Debug.Log("[Pandaborn] built for game version " + (string.IsNullOrEmpty(built) ? "unknown" : built) + ", running "
                          + (string.IsNullOrEmpty(running) ? "unknown" : running));
                if (Differs(built, running))
                    Debug.LogWarning("[Pandaborn] built for " + built + ", running " + running + ": Inkpaws games may fail to load until the mod is updated");
            }
            catch (Exception) { }
        }

        /// <summary>Compares the numbers only: the running version carries a build suffix ("1.1.2.8-ffc2de0-sw").</summary>
        public static bool Differs(string built, string running) =>
            !string.IsNullOrEmpty(built) && !string.IsNullOrEmpty(running) && Numeric(built) != Numeric(running);

        private static string Numeric(string version)
        {
            int dash = version.IndexOf('-');
            return (dash < 0 ? version : version.Substring(0, dash)).Trim();
        }

        /// <summary>UnityEngine.Application.version (what the game's own GameVersions reads), by name: the bootstrap keeps
        /// its compiled references to the mod-starter interface and Debug.</summary>
        private static string Running()
        {
            try { return typeof(Debug).Assembly.GetType("UnityEngine.Application")?.GetProperty("version")?.GetValue(null, null) as string; }
            catch (Exception) { return null; }
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
                var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
                foreach (var raw in File.ReadAllLines(path))
                {
                    string line = raw.Trim();
                    if (line.Length == 0 || line[0] == '#') continue;
                    var parts = line.Split(new[] { ' ', '\t' }, 3, StringSplitOptions.RemoveEmptyEntries);
                    if (parts.Length < 2) { report.Add(new[] { line, "off", "bad line in modules.txt" }); continue; }
                    // a module file is a plain file name in Modules: never a path out of the folder
                    if (parts[1].IndexOfAny(new[] { '/', '\\', ':' }) >= 0) { report.Add(new[] { parts[0], "off", "bad file name in modules.txt" }); continue; }
                    if (!seen.Add(parts[0])) continue;
                    result.Add(new ModuleEntry { Id = parts[0], File = parts[1] });
                }
            }
            catch (Exception e) { report.Add(new[] { "modules.txt", "off", e.Message }); }
            return result;
        }
    }

    /// <summary>Reads the one thing the bootstrap needs from manifest.json, without a JSON library: the mod's own Id.</summary>
    internal static class Manifest
    {
        /// <summary>The Id of the released mod (Workshop, mod.io, the installed build). Dev copies carry other Ids.</summary>
        public const string ReleaseId = "JigglyPanda.PandabornFactions";

        /// <summary>True unless the folder's manifest clearly names another Id: when in doubt, behave as the release.</summary>
        public static bool IsRelease(string modPath)
        {
            try
            {
                string file = Path.Combine(modPath, "manifest.json");
                if (!File.Exists(file)) return true;
                string id = TopLevelString(File.ReadAllText(file), "Id");
                return id == null || id == ReleaseId;
            }
            catch (Exception) { return true; }
        }

        /// <summary>The string value of a key of the outermost object (RequiredMods entries have an "Id" too), or null.</summary>
        public static string TopLevelString(string json, string key)
        {
            int depth = 0;
            bool valueNext = false;
            for (int i = 0; i < json.Length; i++)
            {
                char c = json[i];
                if (c == '"')
                {
                    var sb = new StringBuilder();
                    for (i++; i < json.Length && json[i] != '"'; i++)
                    {
                        if (json[i] == '\\' && i + 1 < json.Length) i++;
                        sb.Append(json[i]);
                    }
                    if (valueNext) return sb.ToString();
                    int j = i + 1;
                    while (j < json.Length && char.IsWhiteSpace(json[j])) j++;
                    valueNext = depth == 1 && j < json.Length && json[j] == ':' && sb.ToString() == key;
                }
                else if (c == '{' || c == '[') { depth++; valueNext = false; }
                else if (c == '}' || c == ']') { depth--; valueNext = false; }
                else if (c == ',') valueNext = false;
                else if (valueNext && c != ':' && !char.IsWhiteSpace(c)) valueNext = false;   // a number, true, false or null
            }
            return null;
        }
    }

    /// <summary>
    /// The player's switch: a plain text file PandabornFactions.txt in the game's user data folder (the folder that holds
    /// Saves and Mods: Documents\Timberborn on Windows; found through the game's own UserDataFolder, never a path written
    /// here). For a player whose other mods clash with one feature, with no settings mod and no environment variable:
    ///   # lines starting with # are notes
    ///   off: Flowering
    ///   off: Water, Festival
    /// Names are the feature ids of Modules/modules.txt, in any letter case. A feature named here is not loaded (state
    /// forced-off: the same as the dev switch, and the same in-game notice as any feature that is off). Read once at
    /// start. A name that is not a feature is logged and ignored; no file is the normal case.
    /// </summary>
    internal sealed class PlayerSwitch
    {
        public const string FileName = "PandabornFactions.txt";
        /// <summary>The reason in the boot report; Pandaborn.Core recognises the file name in it.</summary>
        public const string Reason = "switched off in " + FileName;
        private readonly HashSet<string> _off = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        private string _file;

        public bool Off(string id) => _off.Contains(id);

        public static PlayerSwitch Read() => Read(UserDataFolder());

        public static PlayerSwitch Read(string folder)
        {
            var result = new PlayerSwitch();
            try
            {
                if (string.IsNullOrEmpty(folder)) return result;
                string file = Path.Combine(folder, FileName);
                if (!File.Exists(file)) return result;
                result._file = file;
                foreach (var raw in File.ReadAllLines(file))
                {
                    string line = raw.Trim().TrimStart('\uFEFF');
                    if (line.Length == 0 || line[0] == '#') continue;
                    int colon = line.IndexOf(':');
                    if (colon < 0 || !string.Equals(line.Substring(0, colon).Trim(), "off", StringComparison.OrdinalIgnoreCase))
                    {
                        Debug.LogWarning("[Pandaborn] " + FileName + ": line not understood and ignored (write \"off: Feature\"): " + line);
                        continue;
                    }
                    foreach (var name in line.Substring(colon + 1).Split(',', ';', ' ', '\t'))
                        if (name.Trim().Length > 0) result._off.Add(name.Trim());
                }
            }
            catch (Exception e) { Debug.LogWarning("[Pandaborn] " + FileName + " could not be read and is ignored: " + e.Message); }
            return result;
        }

        /// <summary>Logs what the file switches off, and the names in it that are not features of this version.</summary>
        public void Announce(List<string> features)
        {
            if (_file == null) return;
            var known = _off.Where(n => features.Contains(n, StringComparer.OrdinalIgnoreCase)).ToList();
            var unknown = _off.Where(n => !features.Contains(n, StringComparer.OrdinalIgnoreCase)).ToList();
            Debug.Log("[Pandaborn] " + _file + " switches off: " + (known.Count > 0 ? string.Join(", ", known) : "nothing"));
            if (unknown.Count > 0)
                Debug.LogWarning("[Pandaborn] " + FileName + " names " + string.Join(", ", unknown) + ", which this version does not have; ignored. Features: "
                                 + string.Join(", ", features));
        }

        /// <summary>Timberborn.PlatformUtilities.UserDataFolder.Folder, by name: the bootstrap keeps its compiled references
        /// to the mod-starter interface and Debug. If the game renames it, the file is not read and the log says so.</summary>
        private static string UserDataFolder()
        {
            try
            {
                var type = Type.GetType("Timberborn.PlatformUtilities.UserDataFolder, Timberborn.PlatformUtilities");
                var folder = type?.GetField("Folder", BindingFlags.Public | BindingFlags.Static)?.GetValue(null) as string;
                if (string.IsNullOrEmpty(folder)) Debug.LogWarning("[Pandaborn] the game's user data folder was not found; " + FileName + " is not read");
                return folder;
            }
            catch (Exception e)
            {
                Debug.LogWarning("[Pandaborn] the game's user data folder was not found; " + FileName + " is not read: " + e.Message);
                return null;
            }
        }
    }

    /// <summary>
    /// Dev switch, for tests only: the environment variable PANDABORN_DEV (lines separated by ';'), or a file
    /// pandaborn.dev.txt in the mod folder of a dev copy, with lines such as
    ///   force-off: Bell, Names           (the module is not loaded, as if a player had an old game)
    ///   simulate-missing-api: Bell       (the required-API check fails, exercising the "needs update" path)
    /// The file is ignored in a copy whose manifest Id is the released mod's: test probes write that file, and one left
    /// behind in a packaged build must not switch features off for players. The environment variable works everywhere
    /// (nobody has it set by accident), so the release copy itself can still be tested.
    /// </summary>
    internal sealed class DevSwitch
    {
        public const string FileName = "pandaborn.dev.txt";
        public const string Variable = "PANDABORN_DEV";
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
                string file = Path.Combine(modPath, FileName);
                if (File.Exists(file))
                {
                    if (Manifest.IsRelease(modPath))
                        Debug.LogWarning("[Pandaborn] " + FileName + " is ignored: this is the released mod (manifest Id " + Manifest.ReleaseId
                                         + "). Delete the file; to test this copy use the environment variable " + Variable + ".");
                    else lines.AddRange(File.ReadAllLines(file));
                }
                string env = Environment.GetEnvironmentVariable(Variable);
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
                if (dev.Lines.Count > 0) Debug.LogWarning("[Pandaborn] dev switch active: " + string.Join("; ", dev.Lines));
            }
            catch (Exception e) { Debug.LogWarning("[Pandaborn] dev switch unreadable: " + e.Message); }
            return dev;
        }
    }
}
