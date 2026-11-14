using System.Diagnostics;
using System.Reflection;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace SchemaDump;

static class Program
{
    const string DefaultGame = @"C:\Program Files (x86)\Steam\steamapps\common\Timberborn";

    static int Main(string[] args)
    {
        try
        {
            return Run(args);
        }
        catch (Exception e)
        {
            Console.Error.WriteLine("ERROR: " + e);
            return 1;
        }
    }

    static int Run(string[] args)
    {
        string game = DefaultGame;
        string? managed = null;
        string? output = null;
        string? checkDir = null;
        var includes = new List<string>();
        for (int i = 0; i < args.Length; i++)
        {
            string Next() => i + 1 < args.Length ? args[++i] : throw new ArgumentException("Missing value for " + args[i]);
            switch (args[i])
            {
                case "--managed": managed = Next(); break;
                case "--game": game = Next(); break;
                case "--out": output = Next(); break;
                case "--include": includes.Add(Next()); break;
                case "--check-blueprints": checkDir = Next(); break;
                case "-h": case "--help":
                    Console.WriteLine("usage: dotnet run --project tools/schema -c Release -- [--managed <dir>] [--game <game root>] " +
                                      "[--out <file or dir>] [--include <dll or dir>]... [--check-blueprints <dir>]");
                    return 0;
                default: throw new ArgumentException("Unknown argument " + args[i]);
            }
        }
        managed ??= Path.Combine(game, "Timberborn_Data", "Managed");

        string gameVersion = ReadGameVersion(game);
        var (unityVersion, unitySource) = ReadUnityVersion(game);
        Console.WriteLine($"Game {gameVersion}, Unity {unityVersion} (from {unitySource})");

        // ---- load (metadata only, nothing executes) ----
        var gameDlls = Directory.GetFiles(managed, "*.dll").OrderBy(p => p, StringComparer.OrdinalIgnoreCase).ToList();
        var modDlls = includes.SelectMany(p => Directory.Exists(p)
                ? Directory.GetFiles(p, "*.dll", SearchOption.AllDirectories)
                : new[] { Path.GetFullPath(p) })
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .OrderBy(p => p, StringComparer.OrdinalIgnoreCase).ToList();
        var resolverPaths = gameDlls.Concat(modDlls).ToList();
        using var mlc = new MetadataLoadContext(new PathAssemblyResolver(resolverPaths), "mscorlib");
        using var il = new IlDefaults();

        int loadFailures = 0;
        var gameAssemblies = new List<Assembly>();
        var modAssemblies = new List<Assembly>();
        foreach (var path in gameDlls.Concat(modDlls))
        {
            try
            {
                var asm = mlc.LoadFromAssemblyPath(path);
                (modDlls.Contains(path) ? modAssemblies : gameAssemblies).Add(asm);
            }
            catch (BadImageFormatException)
            {
                // native plugin dll in Managed: not a .NET assembly, the game never loads it as one
                if (modDlls.Contains(path)) { Console.Error.WriteLine("ERROR: not a .NET assembly: " + path); loadFailures++; }
            }
            catch (Exception e)
            {
                Console.Error.WriteLine($"ERROR: cannot load {path}: {e.Message}");
                loadFailures++;
            }
        }

        var blueprintSystem = gameAssemblies.Concat(modAssemblies).FirstOrDefault(a => a.GetName().Name == "Timberborn.BlueprintSystem")
                              ?? throw new InvalidOperationException("Timberborn.BlueprintSystem.dll not found in " + managed);
        var componentSpec = blueprintSystem.GetType("Timberborn.BlueprintSystem.ComponentSpec", throwOnError: true)!;

        var builder = new SchemaBuilder(componentSpec, il, modAssemblies);
        foreach (var asm in gameAssemblies.Concat(modAssemblies))
        {
            // only assemblies that can see ComponentSpec can define specs
            bool relevant = asm == blueprintSystem ||
                            asm.GetReferencedAssemblies().Any(r => r.Name == "Timberborn.BlueprintSystem");
            if (!relevant) continue;
            builder.AddAssembly(asm);
        }
        builder.DrainTypes();

        var assemblies = new JObj();
        foreach (var asm in builder.UsedAssemblies)
            assemblies[asm.GetName().Name!] = SchemaBuilder.AssemblyInfo(asm);

        var root = new JObj
        {
            ["formatVersion"] = 1,
            ["gameVersion"] = gameVersion,
            ["unityVersion"] = unityVersion,
            ["assemblies"] = assemblies,
            ["specs"] = builder.Specs,
            ["types"] = builder.Types,
            ["enums"] = builder.Enums,
        };

        output ??= Path.Combine(RepoRoot(), "schema");
        string outFile = Directory.Exists(output) || output.EndsWith('/') || output.EndsWith('\\') || !output.EndsWith(".json", StringComparison.OrdinalIgnoreCase)
            ? Path.Combine(output, gameVersion + ".json")
            : output;
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(outFile))!);
        File.WriteAllBytes(outFile, JsonOut.Serialize(root));

        int aliasCount = builder.Specs.Values.Count(v => ((JObj)v!).ContainsKey("aliasOf"));
        Console.WriteLine($"Wrote {outFile}");
        Console.WriteLine($"  spec classes: {builder.SpecClassCount}, spec keys: {builder.Specs.Count} ({aliasCount} aliases), " +
                          $"nested types: {builder.Types.Count}, enums: {builder.Enums.Count}, assemblies: {assemblies.Count}");
        foreach (var w in builder.Warnings) Console.Error.WriteLine("WARNING: " + w);
        foreach (var e in builder.Errors) Console.Error.WriteLine("ERROR: " + e);

        int exit = builder.Errors.Count > 0 || loadFailures > 0 ? 1 : 0;
        if (checkDir != null && BlueprintCheck.Run(checkDir, builder.Specs, builder.Types) > 0 && exit == 0)
            exit = 3;
        return exit;
    }

    static string RepoRoot()
    {
        var meta = typeof(Program).Assembly.GetCustomAttributes<AssemblyMetadataAttribute>()
            .FirstOrDefault(a => a.Key == "RepoRoot")?.Value;
        return meta ?? Directory.GetCurrentDirectory();
    }

    static string ReadGameVersion(string game)
    {
        var path = Path.Combine(game, "Timberborn_Data", "StreamingAssets", "VersionNumbers.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(path));
        return doc.RootElement.GetProperty("CurrentVersion").GetString()!;
    }

    /// <summary>
    /// The Unity version string ("6000.5.11f1") from the serialized-file header of globalgamemanagers;
    /// falls back to UnityPlayer.dll's FileVersion.
    /// </summary>
    static (string version, string source) ReadUnityVersion(string game)
    {
        var ggm = Path.Combine(game, "Timberborn_Data", "globalgamemanagers");
        if (File.Exists(ggm))
        {
            var head = new byte[256];
            using (var fs = File.OpenRead(ggm)) fs.ReadExactly(head, 0, (int)Math.Min(head.Length, fs.Length));
            var m = Regex.Match(Encoding.ASCII.GetString(head), @"\d{4}\.\d+\.\d+[abfpx]\d+");
            if (m.Success) return (m.Value, "Timberborn_Data/globalgamemanagers header");
        }
        var player = Path.Combine(game, "UnityPlayer.dll");
        if (File.Exists(player))
        {
            var v = FileVersionInfo.GetVersionInfo(player).FileVersion;
            if (!string.IsNullOrEmpty(v)) return (v, "UnityPlayer.dll FileVersion");
        }
        return ("unknown", "not found");
    }
}
