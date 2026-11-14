using System.Text.Json;

namespace SchemaDump;

/// <summary>
/// Sanity check of the schema against a folder of blueprints: every spec key (top level and inside Children,
/// recursively) must be known, and every key one level inside a spec object should be one of its fields.
/// </summary>
static class BlueprintCheck
{
    static readonly string[] Suffixes = { "#append", "#remove", "#delete" };

    sealed class Hits
    {
        public int Count;
        public string Example = "";
    }

    /// <returns>Number of distinct unknown spec keys.</returns>
    public static int Run(string dir, JObj specs, JObj types)
    {
        var unknownSpecs = new SortedDictionary<string, Hits>(StringComparer.Ordinal);
        var unknownFields = new SortedDictionary<string, Hits>(StringComparer.Ordinal);
        var files = Directory.GetFiles(dir, "*.blueprint.json", SearchOption.AllDirectories)
            .OrderBy(p => p, StringComparer.OrdinalIgnoreCase).ToList();
        int specObjects = 0;

        void Note(SortedDictionary<string, Hits> map, string key, string file)
        {
            if (!map.TryGetValue(key, out var h)) map[key] = h = new Hits { Example = Path.GetRelativePath(dir, file) };
            h.Count++;
        }

        void WalkBlueprint(JsonElement obj, string file)
        {
            foreach (var prop in obj.EnumerateObject())
            {
                var key = Strip(prop.Name);
                if (key == "Children")
                {
                    if (prop.Value.ValueKind != JsonValueKind.Object) continue;
                    foreach (var child in prop.Value.EnumerateObject())
                    {
                        if (child.Name.Contains("#nested", StringComparison.Ordinal)) continue;
                        if (child.Value.ValueKind == JsonValueKind.Object) WalkBlueprint(child.Value, file);
                    }
                    continue;
                }
                if (!specs.TryGetValue(key, out var specObj))
                {
                    Note(unknownSpecs, key, file);
                    continue;
                }
                var spec = (JObj)specObj!;
                if (spec.TryGetValue("aliasOf", out var target)) spec = (JObj)specs[(string)target!]!;
                var fields = (JObj)spec["fields"]!;
                specObjects++;
                if (prop.Value.ValueKind != JsonValueKind.Object) continue;
                foreach (var f in prop.Value.EnumerateObject())
                {
                    var fk = Strip(f.Name);
                    if (!fields.ContainsKey(fk)) Note(unknownFields, key + "." + fk, file);
                }
            }
        }

        foreach (var file in files)
        {
            var bytes = File.ReadAllBytes(file);
            var span = bytes.AsSpan();
            if (span.Length >= 3 && span[0] == 0xEF && span[1] == 0xBB && span[2] == 0xBF) span = span[3..];
            JsonDocument doc;
            try
            {
                doc = JsonDocument.Parse(span.ToArray(), new JsonDocumentOptions
                {
                    AllowTrailingCommas = true,
                    CommentHandling = JsonCommentHandling.Skip,
                });
            }
            catch (JsonException e)
            {
                Console.WriteLine($"  unparsable: {Path.GetRelativePath(dir, file)}: {e.Message}");
                continue;
            }
            using (doc)
            {
                if (doc.RootElement.ValueKind == JsonValueKind.Object) WalkBlueprint(doc.RootElement, file);
            }
        }

        Console.WriteLine($"Checked {files.Count} blueprints ({specObjects} spec objects) in {dir}");
        Console.WriteLine($"  unknown spec keys: {unknownSpecs.Count}");
        foreach (var kv in unknownSpecs)
            Console.WriteLine($"    {kv.Key}  x{kv.Value.Count}  e.g. {kv.Value.Example}");
        Console.WriteLine($"  unknown field keys: {unknownFields.Count}");
        foreach (var kv in unknownFields)
            Console.WriteLine($"    {kv.Key}  x{kv.Value.Count}  e.g. {kv.Value.Example}");
        return unknownSpecs.Count;
    }

    static string Strip(string key)
    {
        foreach (var s in Suffixes)
            if (key.EndsWith(s, StringComparison.Ordinal)) return key[..^s.Length];
        return key;
    }
}
