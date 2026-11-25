using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;

namespace Pandaborn.Core
{
    /// <summary>
    /// One saved entry of a carrier (PandabornStore, PandabornEntityState): "feature|version|payload". The payload may
    /// hold anything, '|' included. An entry read from a save keeps its saved text and is written back exactly as it
    /// was until its feature sets a new value, so the data of a feature that is off, or that a newer version of the mod
    /// wrote in a form this version does not know, survives a save made by this version byte for byte.
    /// No game types here: tests/Foundation reads this file directly.
    /// </summary>
    internal sealed class StoreEntry
    {
        public readonly string Feature;
        public readonly int Version;
        public readonly string Payload;
        private readonly string _saved;

        public StoreEntry(string feature, int version, string payload) : this(feature, version, payload, null) { }

        private StoreEntry(string feature, int version, string payload, string saved)
        {
            Feature = feature;
            Version = version;
            Payload = payload ?? "";
            _saved = saved;
        }

        public override string ToString() => _saved ?? Feature + "|" + Version.ToString(CultureInfo.InvariantCulture) + "|" + Payload;

        /// <summary>Null when the text is not "feature|integer|...".</summary>
        public static StoreEntry Parse(string raw)
        {
            if (string.IsNullOrEmpty(raw)) return null;
            int a = raw.IndexOf('|');
            if (a <= 0) return null;
            int b = raw.IndexOf('|', a + 1);
            if (b < 0) return null;
            return int.TryParse(raw.Substring(a + 1, b - a - 1), NumberStyles.Integer, CultureInfo.InvariantCulture, out int version)
                ? new StoreEntry(raw.Substring(0, a), version, raw.Substring(b + 1), raw)
                : null;
        }

        public static void CheckFeature(string feature)
        {
            if (string.IsNullOrEmpty(feature) || feature.IndexOf('|') >= 0) throw new ArgumentException("bad feature id " + feature);
        }
    }

    /// <summary>
    /// The entries of one carrier. Lines that cannot be read as an entry are kept and written back unchanged (after the
    /// entries), never dropped: this version cannot know what a later version meant by them.
    /// </summary>
    internal sealed class StoreEntries
    {
        /// <summary>Unreadable lines kept per carrier; more than this is damage, not data.</summary>
        private const int MaxUnreadable = 32;
        private readonly Dictionary<string, StoreEntry> _entries = new Dictionary<string, StoreEntry>(StringComparer.Ordinal);
        private readonly List<string> _unreadable = new List<string>();

        public bool IsEmpty => _entries.Count == 0 && _unreadable.Count == 0;

        public IEnumerable<string> Features => _entries.Keys;

        /// <summary>Returns the lines that were not entries.</summary>
        public List<string> Read(IEnumerable<string> lines)
        {
            var bad = new List<string>();
            if (lines == null) return bad;
            foreach (var raw in lines)
            {
                var entry = StoreEntry.Parse(raw);
                if (entry != null) _entries[entry.Feature] = entry;
                else if (!string.IsNullOrEmpty(raw))
                {
                    bad.Add(raw);
                    if (_unreadable.Count < MaxUnreadable) _unreadable.Add(raw);
                }
            }
            return bad;
        }

        public List<string> Write() =>
            _entries.Values.OrderBy(e => e.Feature, StringComparer.Ordinal).Select(e => e.ToString()).Concat(_unreadable).ToList();

        public bool TryGet(string feature, out int version, out string payload)
        {
            if (feature != null && _entries.TryGetValue(feature, out var entry))
            {
                version = entry.Version;
                payload = entry.Payload;
                return true;
            }
            version = 0;
            payload = null;
            return false;
        }

        public void Set(string feature, int version, string payload)
        {
            StoreEntry.CheckFeature(feature);
            // an unchanged value keeps the saved text (and so the exact bytes) of the entry
            if (_entries.TryGetValue(feature, out var old) && old.Version == version && old.Payload == (payload ?? "")) return;
            _entries[feature] = new StoreEntry(feature, version, payload);
        }

        public bool Remove(string feature) => feature != null && _entries.Remove(feature);
    }

    /// <summary>Tiny "key=value;key=value" payload helper for store entries.</summary>
    public static class Payload
    {
        public static Dictionary<string, string> Parse(string payload)
        {
            var result = new Dictionary<string, string>(StringComparer.Ordinal);
            if (string.IsNullOrEmpty(payload)) return result;
            foreach (var part in payload.Split(';'))
            {
                int eq = part.IndexOf('=');
                if (eq <= 0) continue;
                string value = part.Substring(eq + 1);
                try { value = Uri.UnescapeDataString(value); }
                catch (Exception) { }      // a value this version cannot decode is passed on as it is
                result[part.Substring(0, eq)] = value;
            }
            return result;
        }

        public static string Write(IEnumerable<KeyValuePair<string, string>> values) =>
            string.Join(";", values.Select(kv => kv.Key + "=" + Escape(kv.Value ?? "")));

        /// <summary>Percent-escapes like Uri.EscapeDataString (what Parse undoes), in pieces: the framework refuses
        /// strings longer than about 65,000 characters in one call, and a save must never fail on a long value.</summary>
        private static string Escape(string value)
        {
            const int Piece = 16000;
            if (value.Length <= Piece) return Uri.EscapeDataString(value);
            var sb = new System.Text.StringBuilder(value.Length + value.Length / 4);
            for (int i = 0; i < value.Length;)
            {
                int n = Math.Min(Piece, value.Length - i);
                if (i + n < value.Length && char.IsHighSurrogate(value[i + n - 1])) n--;     // never split a surrogate pair
                sb.Append(Uri.EscapeDataString(value.Substring(i, n)));
                i += n;
            }
            return sb.ToString();
        }
    }
}
