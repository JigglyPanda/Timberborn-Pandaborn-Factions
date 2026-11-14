using System.Collections;
using System.Text;
using System.Text.Encodings.Web;
using System.Text.Json;

namespace SchemaDump;

/// <summary>An ordinally sorted JSON object.</summary>
sealed class JObj : SortedDictionary<string, object?>
{
    public JObj() : base(StringComparer.Ordinal) { }
}

/// <summary>Deterministic JSON writer: 2-space indent, LF, sorted keys (via JObj), UTF-8 without BOM.</summary>
static class JsonOut
{
    public static byte[] Serialize(object? root)
    {
        using var ms = new MemoryStream();
        var options = new JsonWriterOptions
        {
            Indented = true,
            IndentSize = 2,
            NewLine = "\n",
            Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
        };
        using (var w = new Utf8JsonWriter(ms, options))
        {
            Write(w, root);
        }
        ms.WriteByte((byte)'\n');
        return ms.ToArray();
    }

    static void Write(Utf8JsonWriter w, object? v)
    {
        switch (v)
        {
            case null: w.WriteNullValue(); break;
            case string s: w.WriteStringValue(s); break;
            case bool b: w.WriteBooleanValue(b); break;
            case int i: w.WriteNumberValue(i); break;
            case long l: w.WriteNumberValue(l); break;
            case ulong ul: w.WriteNumberValue(ul); break;
            case float f: w.WriteNumberValue(f); break;
            case double d: w.WriteNumberValue(d); break;
            case JObj o:
                w.WriteStartObject();
                foreach (var kv in o)
                {
                    w.WritePropertyName(kv.Key);
                    Write(w, kv.Value);
                }
                w.WriteEndObject();
                break;
            case IEnumerable e:
                w.WriteStartArray();
                foreach (var item in e) Write(w, item);
                w.WriteEndArray();
                break;
            default:
                throw new InvalidOperationException("Cannot write " + v.GetType());
        }
    }
}
