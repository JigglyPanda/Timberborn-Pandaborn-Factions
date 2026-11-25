using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using Pandaborn.Bell;
using Pandaborn.Bootstrap;
using Pandaborn.Core;
using Pandaborn.Words;

namespace Pandaborn.Foundation.Tests
{
    internal static class Program
    {
        private static int _run, _failed;
        private static readonly string Asm = typeof(Program).Assembly.GetName().Name;

        private static int Main(string[] args)
        {
            string mod = null, managed = @"C:\Program Files (x86)\Steam\steamapps\common\Timberborn\Timberborn_Data\Managed";
            for (int i = 0; i < args.Length - 1; i++)
            {
                if (args[i] == "--mod") mod = args[++i];
                else if (args[i] == "--managed") managed = args[++i];
            }
            string tmp = Path.Combine(AppContext.BaseDirectory, "tmp-" + Guid.NewGuid().ToString("N").Substring(0, 8));
            Directory.CreateDirectory(tmp);
            try
            {
                Section("API check against fake game types", ApiCheckFake);
                Section("bundle parking", () => BundleTests(tmp));
                Section("manifest, dev switch, player switch, module list, game version", () => SwitchTests(tmp));
                Section("store entries and payloads", StoreTests);
                Section("notices", NoticeTests);
                Section("bell curve", CurveTests);
                Section("rested share against a BonusManager model", ShareTests);
                Section("words table", () => WordsTests(tmp));
                Section("dead bush ledger", LedgerTests);
                if (mod != null) Section("required-API lists of " + mod + " against the game in " + managed, () => RealGame(mod, managed));
                else Console.WriteLine("(no --mod <built mod folder>: the real-game check of the API lists was skipped)");
            }
            finally
            {
                try { Directory.Delete(tmp, true); } catch (Exception) { }
            }
            Console.WriteLine();
            Console.WriteLine(_failed == 0 ? "PASS: " + _run + " checks" : "FAIL: " + _failed + " of " + _run + " checks");
            return _failed == 0 ? 0 : 1;
        }

        private static void Section(string name, Action body)
        {
            Console.WriteLine("== " + name);
            try { body(); }
            catch (Exception e) { Check("no exception in " + name, false, e.ToString()); }
        }

        private static void Check(string what, bool ok, string detail = null)
        {
            _run++;
            if (ok) return;
            _failed++;
            Console.WriteLine("  FAILED: " + what + (detail != null ? "\n    " + detail : ""));
        }

        private static void Same<T>(string what, T expected, T actual) =>
            Check(what, EqualityComparer<T>.Default.Equals(expected, actual), "expected <" + expected + ">, got <" + actual + ">");

        private static void Near(string what, double expected, double actual, double tolerance) =>
            Check(what, Math.Abs(expected - actual) <= tolerance, "expected " + expected + " +- " + tolerance + ", got " + actual);

        // ------------------------------------------------------------------ API check

        private static List<string> Missing(params string[] lines) => ApiCheck.Missing(lines.Select(l => l.Replace("ASM", Asm)), name => name == "Pandaborn.Core");

        private static void None(string what, params string[] lines)
        {
            var m = Missing(lines);
            Check(what, m.Count == 0, string.Join("; ", m));
        }

        private static void One(string what, string expectedPart, params string[] lines)
        {
            var m = Missing(lines);
            Check(what, m.Count == 1 && m[0].Contains(expectedPart), "expected one line with '" + expectedPart + "', got: " + string.Join("; ", m));
        }

        private static void ApiCheckFake()
        {
            None("type", "T\tASM\tFake.Service");
            None("nested type", "T\tASM\tFake.Service+Nested");
            One("type gone", "type Fake.Gone", "T\tASM\tFake.Gone");
            One("assembly gone", "type X.Y", "T\tTimberborn.NoSuchAssembly\tX.Y");
            One("type made internal", "no longer public", "T\tASM\tFake.Secret");

            None("field with its type", "F\tASM\tFake.Service\tCount\tSystem.Int32");
            None("field, old list without a type", "F\tASM\tFake.Service\tCount");
            One("field gone", "field Fake.Service.Nope", "F\tASM\tFake.Service\tNope\tSystem.Int32");
            One("field retyped", "now System.Int32", "F\tASM\tFake.Service\tCount\tSystem.Single");
            One("field made internal", "no longer public", "F\tASM\tFake.Service\tHidden\tSystem.Int32");

            None("constructor", "M\tASM\tFake.Service\t.ctor\t0\t\tSystem.Void");
            None("property getter with its type", "M\tASM\tFake.Service\tget_Name\t0\t\tSystem.String");
            None("method, old list without a return type", "M\tASM\tFake.Service\tget_Name\t0\t");
            One("getter retyped", "now returns System.String", "M\tASM\tFake.Service\tget_Name\t0\t\tSystem.Int32");
            None("generic return type", "M\tASM\tFake.Service\tItems\t0\tSystem.Int32\tSystem.Collections.Generic.List`1<System.String>");
            One("generic return type changed", "now returns", "M\tASM\tFake.Service\tItems\t0\tSystem.Int32\tSystem.Collections.Generic.IList`1<System.String>");
            None("generic method", "M\tASM\tFake.Service\tPick\t1\tSystem.Collections.Generic.IEnumerable`1<!!0>\t!!0");
            One("parameters changed", "method Fake.Service.Items", "M\tASM\tFake.Service\tItems\t0\tSystem.Int64\tSystem.Collections.Generic.List`1<System.String>");
            One("method made internal", "no longer public", "M\tASM\tFake.Service\tInternal\t0\t\tSystem.Void");
            None("protected method (a derived class may call it)", "M\tASM\tFake.Service\tHook\t0\t\tSystem.Void");
            None("method of an inherited interface", "M\tASM\tFake.IDerived\tA\t0\t\tSystem.Void");
            None("method inherited from System.Object", "M\tASM\tFake.Service\tToString\t0\t\tSystem.String");
            None("method of a generic interface", "M\tASM\tFake.IProvider`1\tGet\t0\t\t!0");

            None("interface with all its members", "V\tASM\tFake.IDerived\tI\tA~0~~System.Void|B~0~System.String~System.Int32|get_Title~0~~System.String");
            One("interface that gained a member", "now requires B", "V\tASM\tFake.IDerived\tI\tA~0~~System.Void|get_Title~0~~System.String");
            One("inherited interface that gained a member", "now requires A", "V\tASM\tFake.IDerived\tI\tB~0~System.String~System.Int32|get_Title~0~~System.String");
            One("interface member retyped", "now requires B", "V\tASM\tFake.IDerived\tI\tA~0~~System.Void|B~0~System.String~System.Int64|get_Title~0~~System.String");
            None("generic interface", "V\tASM\tFake.IProvider`1\tI\tGet~0~~!0");
            One("interface that became a class", "no longer an interface", "V\tASM\tFake.Service\tI\t");
            None("base class with its abstract members", "V\tASM\tFake.Abstract\tC\tX~0~~System.Void|get_Y~0~~System.Int32");
            One("base class that gained an abstract member", "now requires", "V\tASM\tFake.Abstract\tC\tX~0~~System.Void");
            None("base class without abstract members", "V\tASM\tFake.Service\tC\t");
            None("base class whose own base's abstract members are implemented", "V\tASM\tFake.Done\tC\t");
            None("abstract member inherited from a generic base, in the base's own terms", "V\tASM\tFake.Middle\tC\tMake~0~!0~!0");
            One("base class sealed", "can no longer be derived from", "V\tASM\tFake.Closed\tC\t");
            One("base class that became an interface", "now an interface", "V\tASM\tFake.IBase\tC\t");

            None("Pandaborn assembly that is loaded", "R\tPandaborn.Core");
            One("Pandaborn assembly that is not loaded", "needs Pandaborn.Festival", "R\tPandaborn.Festival");
            Check("R lines are skipped without a loader", ApiCheck.Missing(new[] { "R\tPandaborn.Festival" }).Count == 0);
            None("spec name lines are not API", "D\tPandabornBellSpec");
            One("a damaged line is missing, not a crash", "M ", "M\tASM\tFake.Service\tItems");
        }

        // ------------------------------------------------------------------ bundles

        private static string Mod(string tmp, string name, params string[] bundles)
        {
            string dir = Path.Combine(tmp, name);
            Directory.CreateDirectory(Path.Combine(dir, "AssetBundles"));
            foreach (var b in bundles) File.WriteAllText(Path.Combine(dir, "AssetBundles", b), name + ":" + b);
            return dir;
        }

        private static string[] Files(string dir, string folder) =>
            Directory.Exists(Path.Combine(dir, folder)) ? Directory.GetFiles(Path.Combine(dir, folder)).Select(Path.GetFileName).OrderBy(f => f).ToArray() : new string[0];

        private static void BundleTests(string tmp)
        {
            string owner = Mod(tmp, "b1-owner", "look_win", "look_mac"), dup = Mod(tmp, "b1-dup", "look_win", "look_mac");
            Bundles.Park(dup, owner);
            Same("duplicate parked", "look_mac,look_win", string.Join(",", Files(dup, "AssetBundles.parked")));
            Same("duplicate's live folder empty", 0, Files(dup, "AssetBundles").Length);
            Same("owner untouched", 2, Files(owner, "AssetBundles").Length);
            Bundles.Park(dup, owner);
            Same("parking twice is harmless", 2, Files(dup, "AssetBundles.parked").Length);

            Bundles.Unpark(dup);
            Same("taken back", 2, Files(dup, "AssetBundles").Length);
            Check("parked folder removed when empty", !Directory.Exists(Path.Combine(dup, "AssetBundles.parked")));
            Bundles.Unpark(dup);
            Same("taking back with nothing parked is harmless", 2, Files(dup, "AssetBundles").Length);

            // the store re-downloaded a bundle while an older copy sat parked: the live file wins
            string re = Mod(tmp, "b2", "look_win");
            Directory.CreateDirectory(Path.Combine(re, "AssetBundles.parked"));
            File.WriteAllText(Path.Combine(re, "AssetBundles.parked", "look_win"), "old");
            File.WriteAllText(Path.Combine(re, "AssetBundles.parked", "sounds_win"), "old sounds");
            Bundles.Unpark(re);
            Same("live bundle kept over the parked one", "b2:look_win", File.ReadAllText(Path.Combine(re, "AssetBundles", "look_win")));
            Same("a bundle only in the parked folder comes back", "old sounds", File.ReadAllText(Path.Combine(re, "AssetBundles", "sounds_win")));

            // parking over an older parked copy keeps the newer one
            string again = Mod(tmp, "b3", "look_win");
            Directory.CreateDirectory(Path.Combine(again, "AssetBundles.parked"));
            File.WriteAllText(Path.Combine(again, "AssetBundles.parked", "look_win"), "old");
            Bundles.Park(again, owner);
            Same("parking replaces an older parked file", "b3:look_win", File.ReadAllText(Path.Combine(again, "AssetBundles.parked", "look_win")));

            // the duplicate cannot move one file (held open): the owner gives way for exactly that file
            string owner4 = Mod(tmp, "b4-owner", "look_win", "sounds_win"), dup4 = Mod(tmp, "b4-dup", "look_win", "sounds_win");
            if (OperatingSystem.IsWindows())
            {
                using (new FileStream(Path.Combine(dup4, "AssetBundles", "look_win"), FileMode.Open, FileAccess.Read, FileShare.None))
                    Bundles.Park(dup4, owner4);
                Same("the held file stayed in the duplicate", "look_win", string.Join(",", Files(dup4, "AssetBundles")));
                Same("the duplicate's other file was parked", "sounds_win", string.Join(",", Files(dup4, "AssetBundles.parked")));
                Same("the owner parked its copy of the held file", "look_win", string.Join(",", Files(owner4, "AssetBundles.parked")));
                Same("the owner kept the other file", "sounds_win", string.Join(",", Files(owner4, "AssetBundles")));
                Bundles.Unpark(owner4);
                Same("the owner takes its file back at its next start", 2, Files(owner4, "AssetBundles").Length);
            }

            string none = Path.Combine(tmp, "b5-nothing");
            Directory.CreateDirectory(none);
            Bundles.Park(none, owner);
            Bundles.Unpark(none);
            Check("a mod without bundles is left alone", !Directory.Exists(Path.Combine(none, "AssetBundles")) && !Directory.Exists(Path.Combine(none, "AssetBundles.parked")));
            Bundles.Unpark(Path.Combine(tmp, "does-not-exist"));
        }

        // ------------------------------------------------------------------ switches

        private static void SwitchTests(string tmp)
        {
            Same("top-level id", "A.B", Manifest.TopLevelString("{ \"Name\": \"x\", \"Id\": \"A.B\", \"RequiredMods\": [ { \"Id\": \"C.D\" } ] }", "Id"));
            Same("top-level id after a nested one", "A.B", Manifest.TopLevelString("{\"RequiredMods\":[{\"Id\":\"C.D\"}],\"Id\":\"A.B\"}", "Id"));
            Same("no top-level id", null, Manifest.TopLevelString("{\"RequiredMods\":[{\"Id\":\"C.D\"}]}", "Id"));
            Same("an id that is not a string", null, Manifest.TopLevelString("{\"Id\": 5, \"Name\": \"n\"}", "Id"));
            Same("a value equal to the key name", "A.B", Manifest.TopLevelString("{\"Name\": \"Id\", \"Id\": \"A.B\"}", "Id"));
            Same("escaped quotes", "A.B", Manifest.TopLevelString("{\"Description\": \"say \\\"Id\\\": no\", \"Id\": \"A.B\"}", "Id"));

            string release = Path.Combine(tmp, "s-release"), dev = Path.Combine(tmp, "s-dev"), bare = Path.Combine(tmp, "s-bare");
            foreach (var d in new[] { release, dev, bare }) Directory.CreateDirectory(d);
            File.WriteAllText(Path.Combine(release, "manifest.json"), "{ \"Name\": \"Pandaborn - Factions\", \"Id\": \"JigglyPanda.PandabornFactions\", \"RequiredMods\": [] }");
            File.WriteAllText(Path.Combine(dev, "manifest.json"), "{ \"Id\": \"JigglyPanda.PandabornFactionsDev\", \"RequiredMods\": [ { \"Id\": \"JigglyPanda.PandabornFactions\" } ] }");
            Check("release copy", Manifest.IsRelease(release));
            Check("dev copy (even one that requires the release)", !Manifest.IsRelease(dev));
            Check("no manifest counts as release", Manifest.IsRelease(bare));

            Environment.SetEnvironmentVariable(DevSwitch.Variable, null);
            foreach (var d in new[] { release, dev, bare }) File.WriteAllText(Path.Combine(d, DevSwitch.FileName), "# test\nforce-off: Bell, Names\nsimulate-missing-api: Look\n");
            Check("a dev file in the release copy does nothing", !DevSwitch.Read(release).ForcedOff("Bell") && DevSwitch.Read(release).Lines.Count == 0);
            Check("a dev file in a folder without a manifest does nothing", !DevSwitch.Read(bare).ForcedOff("Bell"));
            var devSwitch = DevSwitch.Read(dev);
            Check("a dev file in a dev copy works", devSwitch.ForcedOff("bell") && devSwitch.ForcedOff("Names") && devSwitch.SimulatesMissingApi("Look") && !devSwitch.ForcedOff("Look"));
            Environment.SetEnvironmentVariable(DevSwitch.Variable, "force-off: Words; simulate-missing-member: Words");
            var env = DevSwitch.Read(release);
            Check("the environment variable works in the release copy", env.ForcedOff("Words") && !env.ForcedOff("Bell") && env.Lines.Count == 2);
            Environment.SetEnvironmentVariable(DevSwitch.Variable, null);

            string user = Path.Combine(tmp, "s-user");
            Directory.CreateDirectory(user);
            Check("no player file: nothing off", !PlayerSwitch.Read(user).Off("Flowering"));
            Check("no user folder: nothing off", !PlayerSwitch.Read(null).Off("Flowering"));
            File.WriteAllText(Path.Combine(user, PlayerSwitch.FileName), "\uFEFF# my switches\r\noff: Flowering\r\n\r\nOFF: water, Festival\r\non: Bell\r\nnonsense\r\noff: Typo\r\n");
            var player = PlayerSwitch.Read(user);
            Check("player file switches off what it names", player.Off("Flowering") && player.Off("Water") && player.Off("festival"));
            Check("player file leaves the rest on", !player.Off("Bell") && !player.Off("Names"));
            UnityEngine.Debug.Lines.Clear();
            player.Announce(new List<string> { "Bell", "Names", "Water", "Festival", "Flowering" });
            Check("what is off is logged", UnityEngine.Debug.Lines.Any(l => l.StartsWith("LOG") && l.Contains("switches off") && l.Contains("Flowering")));
            Check("an unknown name is logged", UnityEngine.Debug.Lines.Any(l => l.StartsWith("WARN") && l.Contains("Typo")));

            string list = Path.Combine(tmp, "modules.txt");
            File.WriteAllText(list, "# comment\nBell   Pandaborn.Bell.bin    The bell\n\nNames\tPandaborn.Names.bin\nBell Pandaborn.Other.bin again\nEvil ..\\..\\x.bin\nbroken\n");
            var report = new List<string[]>();
            var modules = ModuleList.Read(list, report);
            Same("modules read", "Bell:Pandaborn.Bell.bin,Names:Pandaborn.Names.bin", string.Join(",", modules.Select(m => m.Id + ":" + m.File)));
            Same("bad lines reported", 2, report.Count);
            Same("missing modules.txt", 0, ModuleList.Read(Path.Combine(tmp, "none.txt"), report).Count);

            Check("same version", !GameVersion.Differs("1.1.2.8", "1.1.2.8-ffc2de0-sw"));
            Check("other version", GameVersion.Differs("1.1.2.8", "1.1.3.0-abc-sw"));
            Check("unknown version says nothing", !GameVersion.Differs(null, "1.1.3.0") && !GameVersion.Differs("1.1.2.8", null));
        }

        // ------------------------------------------------------------------ store

        private static void StoreTests()
        {
            var e = StoreEntry.Parse("Bell|1|locked=12;x=a|b|c");
            Check("entry parsed", e != null && e.Feature == "Bell" && e.Version == 1 && e.Payload == "locked=12;x=a|b|c");
            Check("not entries", StoreEntry.Parse("") == null && StoreEntry.Parse("Bell") == null && StoreEntry.Parse("Bell|x|p") == null
                                 && StoreEntry.Parse("|1|p") == null && StoreEntry.Parse("Bell|1") == null);
            Same("empty payload", "", StoreEntry.Parse("Bell|3|").Payload);

            var saved = new[] { "Zeta|+07| odd  spacing ", "Future|2|newer=format", "garbage without bars", "Bell|1|locked=12", "Half|v2|x" };
            var store = new StoreEntries();
            var bad = store.Read(saved);
            Same("unreadable lines", 2, bad.Count);
            store.Set("Bell", 1, "locked=12");                     // unchanged
            store.Set("Names", 1, "pool=a");                       // new
            var written = store.Write();
            foreach (var line in saved) Check("written back byte for byte: " + line, written.Contains(line));
            Check("new entry written", written.Contains("Names|1|pool=a"));
            Same("line count", 6, written.Count);
            store.Set("Zeta", 8, "new");
            Check("a set entry is rewritten", store.Write().Contains("Zeta|8|new") && !store.Write().Contains(saved[0]));
            Check("version and payload read", store.TryGet("Future", out int v, out string p) && v == 2 && p == "newer=format");
            Check("unknown feature", !store.TryGet("Nope", out _, out _) && !store.TryGet(null, out _, out _));
            Check("remove", store.Remove("Names") && !store.Remove("Names") && !store.Write().Any(l => l.StartsWith("Names|")));
            Check("empty store", new StoreEntries().IsEmpty && !store.IsEmpty);
            bool threw = false;
            try { store.Set("a|b", 1, ""); } catch (ArgumentException) { threw = true; }
            Check("a feature id with a bar is refused", threw);
            var twice = new StoreEntries();
            twice.Read(new[] { "A|1|first", "A|2|second" });
            Check("the later of two entries of one feature holds", twice.TryGet("A", out v, out p) && v == 2 && p == "second" && twice.Write().Count == 1);

            var values = new Dictionary<string, string> { ["a"] = "x;y=z|w", ["b"] = "", ["c"] = "Le Le (Joy)\nYu Yu (Rain)\n乐乐", ["d"] = "100%" };
            var back = Payload.Parse(Payload.Write(values));
            Check("payload round trip", values.All(kv => back.TryGetValue(kv.Key, out var got) && got == kv.Value) && back.Count == values.Count);
            string big = string.Concat(Enumerable.Repeat("Le Le (Joy)\n乐", 20000)) + "\uD83D\uDC3C";
            var bigBack = Payload.Parse(Payload.Write(new[] { new KeyValuePair<string, string>("pool", big) }));
            Check("a value longer than the framework's limit round-trips", bigBack["pool"] == big);
            Check("payload read tolerantly", Payload.Parse(null).Count == 0 && Payload.Parse(";;=x;novalue;k=%ZZ;ok=1")["ok"] == "1");
        }

        // ------------------------------------------------------------------ notices

        private static void NoticeTests()
        {
            var none = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            var allOn = new[] { new FeatureState("Specs", FeatureStatus.On, ""), new FeatureState("Core", FeatureStatus.On, ""), new FeatureState("Bell", FeatureStatus.On, ""), new FeatureState("Water", FeatureStatus.On, "") };
            var p = NoticePlan.Problems(allOn, none, none, 0);
            Check("all on: nothing to say", p.Count == 0 && NoticePlan.Signature(p) == "" && !NoticePlan.Due("", false, "", null) && !NoticePlan.Due("", true, "Bell=Off", null));

            var waterOff = new[] { allOn[0], allOn[1], allOn[2], new FeatureState("Water", FeatureStatus.Off, "game API changed: 1 missing") };
            p = NoticePlan.Problems(waterOff, none, none, 0);
            string sig = NoticePlan.Signature(p);
            Check("a failed check is one problem", p.Count == 1 && p[0].Kind == ProblemKind.Off && p[0].Id == "Water" && sig == "Water=Off");
            Check("a switched-off feature is announced at every load", NoticePlan.EveryLoad(p) && NoticePlan.Due(sig, true, sig, null));
            Check("but once per load", !NoticePlan.Due(sig, true, sig, sig));

            var degraded = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase) { ["Bell"] = "walking cap", ["Water"] = "x failed" };
            var noData = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase) { ["Bell"] = "no spec" };
            p = NoticePlan.Problems(waterOff, degraded, noData, 1);
            sig = NoticePlan.Signature(p);
            Same("off wins over reduced, no data wins over reduced", "Bell=NoData;Duplicate;Water=Off", sig);

            var forced = new[] { allOn[0], allOn[1], new FeatureState("Bell", FeatureStatus.ForcedOff, "switched off in PandabornFactions.txt"), allOn[3] };
            p = NoticePlan.Problems(forced, degraded, none, 0);
            sig = NoticePlan.Signature(p);
            Same("forced off and reduced", "Bell=ForcedOff;Water=Degraded", sig);
            Check("announced once per save", !NoticePlan.EveryLoad(p) && NoticePlan.Due(sig, false, "", null) && !NoticePlan.Due(sig, false, sig, null));
            Check("announced again when the problems change", NoticePlan.Due(sig, false, "Bell=ForcedOff", null));
            Check("a reason that changes its wording is not news", NoticePlan.Signature(NoticePlan.Problems(forced, new Dictionary<string, string> { ["Water"] = "y failed" }, none, 0)) == sig);

            // registry: session states stay, game states go with the game
            FeatureRegistry.StartGame();
            int told = 0;
            FeatureRegistry.Reported = () => told++;
            FeatureRegistry.ReportDegraded("TestSession", "s");
            FeatureRegistry.ReportDegraded("TestSession", "s again");
            FeatureRegistry.ReportDegradedInGame("TestGame", "g");
            FeatureRegistry.ReportNoData("TestData", "d");
            Same("the listener hears each new state once", 3, told);
            Check("all reported", FeatureRegistry.Degraded.ContainsKey("testsession") && FeatureRegistry.Degraded.ContainsKey("TestGame") && FeatureRegistry.NoData.ContainsKey("TestData"));
            FeatureRegistry.Reported = () => throw new InvalidOperationException("listener of a dead game");
            FeatureRegistry.ReportDegradedInGame("TestGame2", "g");
            FeatureRegistry.StartGame();
            Check("a new game forgets the last game's states, not the session's",
                  FeatureRegistry.Degraded.ContainsKey("TestSession") && !FeatureRegistry.Degraded.ContainsKey("TestGame") && FeatureRegistry.NoData.Count == 0);
            FeatureRegistry.Reported = null;
        }

        // ------------------------------------------------------------------ bell

        private static void CurveTests()
        {
            float[] h = { 12, 16 }, b = { 0.33f, 0f };
            Near("12 h", 0.33, BellCurve.At(h, b, 12), 1e-6);
            Near("8 h (flat below)", 0.33, BellCurve.At(h, b, 8), 1e-6);
            Near("14 h (between)", 0.165, BellCurve.At(h, b, 14), 1e-6);
            Near("16 h", 0, BellCurve.At(h, b, 16), 1e-6);
            Near("24 h (flat above)", 0, BellCurve.At(h, b, 24), 1e-6);
            Same("ceiling of the two-point curve", 12, BellCurve.CeilingHours(h, b));

            // the flat-output taper of 2026-11-25: hours x (1 + bonus) = 16 from 12 to 16 h, a point for every hour, any order
            float[] h2 = { 16, 13, 12, 15, 14 }, b2 = { 0f, 16f / 13 - 1, 0.33f, 16f / 15 - 1, 16f / 14 - 1 };
            for (int hours = 12; hours <= 16; hours++)
                Near("a point at " + hours + " h gives its own bonus", hours == 12 ? 0.33 : 16.0 / hours - 1, BellCurve.At(h2, b2, hours), 1e-6);
            for (int hours = 13; hours <= 16; hours++)
                Near("output at " + hours + " h", 16, hours * (1 + BellCurve.At(h2, b2, hours)), 1e-4);
            Near("half hours interpolate", (0.33 + (16.0 / 13 - 1)) / 2, BellCurve.At(h2, b2, 12.5f), 1e-6);
            Near("0 h", 0.33, BellCurve.At(h2, b2, 0), 1e-6);
            Same("ceiling of the tapered curve", 12, BellCurve.CeilingHours(h2, b2));

            Near("no points", 0, BellCurve.At(new float[0], new float[0], 12), 0);
            Near("null curve", 0, BellCurve.At(null, null, 12), 0);
            Near("one point", 0.2, BellCurve.At(new[] { 10f }, new[] { 0.2f }, 3), 1e-6);
            Near("two points at one hour: the later holds from there", 0.1, BellCurve.At(new[] { 12f, 12f, 16f }, new[] { 0.33f, 0.1f, 0f }, 12.0001f), 1e-3);
            Near("a NaN bonus is no bonus", 0, BellCurve.At(new[] { 12f }, new[] { float.NaN }, 12), 0);
            Same("a curve without a bonus has no ceiling", -1, BellCurve.CeilingHours(new[] { 12f, 16f }, new[] { 0f, 0f }));
            Same("a flat curve's ceiling is the whole day", 24, BellCurve.CeilingHours(new[] { 12f }, new[] { 0.2f }));
        }

        /// <summary>BonusManager as the game has it: one sum from 1, clamped when read, listeners told after every change.</summary>
        private sealed class Sum : IBonusSum
        {
            public double Raw = 1;
            public float Min = 0.05f, Max = 1000f;
            public Action Changed;
            public int Events;

            public float Multiplier() => Math.Min(Max, Math.Max(Min, (float)Raw));

            public void Add(float delta) { Raw += delta; Events++; Changed?.Invoke(); }

            public void Remove(float delta) { Raw -= delta; Events++; Changed?.Invoke(); }
        }

        private static void ShareTests()
        {
            // other bonuses come and go; the share follows through the change event, as BellRestedBonus wires it
            var sum = new Sum();
            var share = new RestedShare();
            float factor = 0.33f;
            sum.Changed = () => share.Apply(sum, factor);     // the share guards itself against its own changes
            share.Apply(sum, factor);
            Near("alone: 1.33", 1.33, sum.Multiplier(), 1e-5);
            sum.Add(2.8f);                                   // wellbeing 80
            Near("wellbeing 80 working: 3.8 x 1.33 = 5.054 (measured in game)", 5.054, sum.Multiplier(), 1e-4);
            Near("the share is base x factor", 3.8 * 0.33, share.Delta, 1e-4);
            sum.Remove(2.8f);
            Near("back to 1.33", 1.33, sum.Multiplier(), 1e-5);

            // order does not matter, and nothing drifts over a long game
            var random = new Random(7);
            double others = 0;
            for (int i = 0; i < 200000; i++)
            {
                float d = (float)(random.NextDouble() * 0.6 - 0.25);
                if (others + d < -0.9 || others + d > 6) d = -d;
                if (random.Next(2) == 0) sum.Add(d); else sum.Remove(-d);
                others += d;
                if (i % 50000 == 0) factor = i % 100000 == 0 ? 0.33f : 0.1429f;      // a new day length
                if (i % 50000 == 0) share.Apply(sum, factor);
            }
            double expected = Math.Max(0.05, (1 + others)) * (1 + factor);
            Near("after 200,000 changes of other bonuses the result is still m x (1 + b)", expected, sum.Multiplier(), expected * 2e-3);

            // day length changes; 16 h takes the share out entirely
            factor = 0f;
            share.Apply(sum, factor);
            Same("no bonus: no share", 0f, share.Delta);
            Near("no bonus: the plain multiplier", Math.Max(0.05, 1 + others), sum.Multiplier(), 2e-3 * (1 + Math.Abs(others)));

            // the walking cap: vanilla 2.0 clips, the Inkpaws' 2.66 does not (wellbeing 80 walking 1.7 -> 2.261)
            foreach (var cap in new[] { 2.0f, 2.66f })
            {
                var walk = new Sum { Min = 0.25f, Max = cap };
                var walkShare = new RestedShare();
                walk.Raw = 1.7;
                walkShare.Apply(walk, 0.33f);
                Near("walking at wellbeing 80 with cap " + cap, Math.Min(cap, 2.261), walk.Multiplier(), 1e-4);
                walk.Raw += 1.0;                               // another mod's +100%: over the cap either way
                walkShare.Apply(walk, 0.33f);
                Near("over the cap the cap decides", cap, walk.Multiplier(), 1e-6);
                walk.Raw -= 1.0;
                walkShare.Apply(walk, 0.33f);
                Near("and back under it the share is right again", Math.Min(cap, 2.261), walk.Multiplier(), 1e-4);
                walkShare.Apply(walk, 0f);
                Near("share removed: the raw sum is what the others added", 1.7, walk.Raw, 1e-5);
            }

            // below the floor
            var low = new Sum { Min = 0.25f, Max = 2f, Raw = -0.5 };
            var lowShare = new RestedShare();
            lowShare.Apply(low, 0.33f);
            Near("under the floor the floor decides", 0.25, low.Multiplier(), 1e-6);
            lowShare.Apply(low, 0f);
            Near("and the raw sum is restored", -0.5, low.Raw, 1e-6);

            // another mod's listener throws while the game tells it about our change: the books stay right
            var hostile = new Sum { Raw = 2.0 };
            var hostileShare = new RestedShare();
            hostileShare.Apply(hostile, 0.33f);
            bool angry = true;
            hostile.Changed = () => { if (angry) throw new InvalidOperationException("another mod's listener"); };
            int thrown = 0;
            for (int i = 0; i < 5; i++)
            {
                try { hostileShare.Apply(hostile, 0.33f); }
                catch (InvalidOperationException) { thrown++; }
                Near("with a throwing listener the sum holds exactly what the share says (try " + i + ")", 2.0 + hostileShare.Delta, hostile.Raw, 1e-5);
            }
            Check("the listener did throw", thrown == 5);
            angry = false;
            hostileShare.Apply(hostile, 0.33f);
            Near("and the result is right once it stops", 2.0 * 1.33, hostile.Multiplier(), 1e-4);
            hostileShare.Apply(hostile, 0f);
            Near("nothing of ours is left behind", 2.0, hostile.Raw, 1e-5);

            // no events when nothing is to be added
            var quiet = new Sum();
            new RestedShare().Apply(quiet, 0f);
            Same("no share, no change events", 0, quiet.Events);
        }

        // ------------------------------------------------------------------ words

        private static void WordsTests(string tmp)
        {
            string dir = Path.Combine(tmp, "w", "Pandaborn", "Words");
            Directory.CreateDirectory(dir);
            File.WriteAllText(Path.Combine(dir, "words.enUS.txt"),
                "# comment\nfaction: Inkpaws\nA.Key\tpanda\tbeaver\n\nB.Key\tline one\\nline two\\ttab \\\\ slash\tv\n@Ringtails\tA.Key\tpanda or ringtail\tbeaver\n"
                + "@@Ringtails\tC.Key\told double at\tv\n@Water\tD.Key\tonly with water\tv\nshort\tline\n");
            var table = WordsTable.Load(Path.Combine(tmp, "w"), "enUS");
            Check("table read", table != null && table.Faction == "Inkpaws" && table.Entries.Count == 5);
            Check("no table for another language", WordsTable.Load(Path.Combine(tmp, "w"), "zhCN") == null && WordsTable.Load("", "enUS") == null);
            var plain = table.Effective(f => false).ToDictionary(e => e.Key, e => e.Text);
            Check("plain lines without features", plain.Count == 2 && plain["A.Key"] == "panda" && plain["B.Key"] == "line one\nline two\ttab \\ slash");
            var withRingtails = table.Effective(f => f == "Ringtails").ToDictionary(e => e.Key, e => e.Text);
            Check("feature lines apply while the feature is on, and win over the plain line",
                  withRingtails.Count == 3 && withRingtails["A.Key"] == "panda or ringtail" && withRingtails["C.Key"] == "old double at" && !withRingtails.ContainsKey("D.Key"));
        }

        // ------------------------------------------------------------------ dead bushes

        private static void LedgerTests()
        {
            var ledger = new Pandaborn.Customs.DeadBushLedger();
            Guid tea = Guid.NewGuid(), pepper = Guid.NewGuid();
            const float hour = 1f / 24f;
            bool due = false;
            for (int h = 0; h < 24; h++)
            {
                ledger.Begin();
                due |= ledger.Observe(tea, 10f + h * hour, 1f);
                ledger.End();
            }
            Check("a dead bush is not due within its day", !due && ledger.Waiting == 1);
            ledger.Begin();
            Check("and is due after a full day", ledger.Observe(tea, 11f + hour / 2, 1f));
            ledger.End();

            // the option was switched off for a look (the bush did not qualify): the day starts over
            ledger.Begin();
            ledger.Observe(pepper, 11.1f, 1f);
            ledger.End();
            Check("a bush that stops qualifying is forgotten", ledger.Waiting == 1);
            ledger.Begin();
            Check("and starts its day again", !ledger.Observe(tea, 11.2f, 1f) && !ledger.Observe(pepper, 11.2f, 1f));
            ledger.End();
            ledger.Begin();
            Check("each waits from its own start", !ledger.Observe(tea, 12.15f, 1f) && ledger.Observe(pepper, 12.15f, 1f));
            ledger.End();
            Same("both are still in the ledger", 2, ledger.Waiting);
            ledger.Forget(pepper);
            Same("a removed bush leaves the ledger", 1, ledger.Waiting);

            ledger.Begin();
            ledger.Observe(tea, 20f, 1f);
            ledger.End();
            ledger.Begin();
            Check("a clock that went back starts the wait again", !ledger.Observe(tea, 5f, 1f));
            Check("no delay means due at once", ledger.Observe(pepper, 5f, 0f));
            ledger.End();
            ledger.Clear();
            Same("cleared", 0, ledger.Waiting);
        }

        // ------------------------------------------------------------------ the real game

        private static void RealGame(string mod, string managed)
        {
            if (!Directory.Exists(managed)) { Check("game folder " + managed, false, "not found"); return; }
            AppDomain.CurrentDomain.AssemblyResolve += (sender, e) =>
            {
                string file = Path.Combine(managed, new AssemblyName(e.Name).Name + ".dll");
                return File.Exists(file) ? Assembly.LoadFrom(file) : null;
            };
            var lists = new List<string>();
            foreach (var folder in new[] { "Scripts", "Modules" })
                if (Directory.Exists(Path.Combine(mod, folder))) lists.AddRange(Directory.GetFiles(Path.Combine(mod, folder), "*.api.txt"));
            Check("API lists found", lists.Count >= 2, lists.Count + " in " + mod);
            foreach (var list in lists.OrderBy(l => l))
            {
                var lines = File.ReadAllLines(list).Where(l => l.Length > 0 && l[0] != '#').ToList();
                var missing = ApiCheck.Missing(lines, name => true);
                Check(Path.GetFileName(list) + ": every one of " + lines.Count + " lines resolves", missing.Count == 0, string.Join("\n    ", missing.Take(12)));
                Check(Path.GetFileName(list) + " carries return types and base types", lines.Any(l => l.StartsWith("M\t") && l.Split('\t').Length > 6)
                                                                                         && (lines.Any(l => l.StartsWith("V\t")) || list.Contains("Specs")));
                Console.WriteLine("  " + Path.GetFileName(list) + ": " + lines.Count + " lines, " + lines.Count(l => l.StartsWith("V\t")) + " base types and interfaces");
            }
            // what a game update does, shown on the real assemblies
            Check("a getter whose type changed is caught",
                  ApiCheck.Missing(new[] { "M\tTimberborn.GameDistricts\tTimberborn.GameDistricts.DistrictCenterRegistry\tget_FinishedDistrictCenters\t0\t\tSystem.Int32" }).Any(m => m.Contains("now returns")));
            Check("a type that is internal is caught", ApiCheck.Missing(new[] { "T\tTimberborn.Localization\tTimberborn.Localization.Loc" }).Any(m => m.Contains("no longer public")));
            Check("an interface with a member the module does not know is caught",
                  ApiCheck.Missing(new[] { "V\tTimberborn.WorldPersistence\tTimberborn.WorldPersistence.IPersistentEntity\tI\tLoad~0~Timberborn.WorldPersistence.IEntityLoader~System.Void" }).Any(m => m.Contains("now requires Save")));
        }
    }
}
