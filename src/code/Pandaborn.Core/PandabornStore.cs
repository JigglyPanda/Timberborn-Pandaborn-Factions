using System;
using System.Collections.Generic;
using System.Linq;
using Timberborn.Persistence;
using Timberborn.SingletonSystem;
using Timberborn.WorldPersistence;
using UnityEngine;

namespace Pandaborn.Core
{
    /// <summary>
    /// The save carrier: one saved singleton ("Pandaborn.Store") holding a versioned text entry per feature. It lives in the
    /// always-loaded core, so a feature that is off (forced off, or its game API changed) keeps its saved state: the entry
    /// is read and written back unchanged, and the feature finds it again when it is back on.
    /// Rules for features (ENGINEERING.md, code rule 6): store small text, carry a version, read tolerantly (an unknown
    /// version or a malformed payload means "start fresh", never an exception).
    /// </summary>
    public class PandabornStore : ISaveableSingleton, ILoadableSingleton
    {
        private static readonly SingletonKey StoreKey = new SingletonKey("Pandaborn.Store");
        private static readonly ListKey<string> EntriesKey = new ListKey<string>("Entries");

        private readonly ISingletonLoader _singletonLoader;
        private readonly Dictionary<string, Entry> _entries = new Dictionary<string, Entry>(StringComparer.Ordinal);

        public PandabornStore(ISingletonLoader singletonLoader)
        {
            _singletonLoader = singletonLoader;
            Current = this;
        }

        /// <summary>The store of the running game (for tests; features get it injected).</summary>
        public static PandabornStore Current { get; private set; }

        /// <summary>True when this game was loaded from a save that already had a Pandaborn store.</summary>
        public bool LoadedFromSave { get; private set; }

        public void Load()
        {
            try
            {
                if (!_singletonLoader.TryGetSingleton(StoreKey, out var loader) || !loader.Has(EntriesKey)) return;
                LoadedFromSave = true;
                foreach (var raw in loader.Get(EntriesKey))
                {
                    var entry = Entry.Parse(raw);
                    if (entry != null) _entries[entry.Feature] = entry;
                    else Debug.LogWarning("[Pandaborn] ignored a malformed saved entry: " + raw);
                }
            }
            catch (Exception e)
            {
                Debug.LogError("[Pandaborn] reading the Pandaborn store failed; features start fresh: " + e);
            }
        }

        public void Save(ISingletonSaver singletonSaver)
        {
            try
            {
                if (_entries.Count == 0) return;
                var lines = _entries.Values.OrderBy(e => e.Feature, StringComparer.Ordinal).Select(e => e.ToString()).ToList();
                singletonSaver.GetSingleton(StoreKey).Set(EntriesKey, lines);
            }
            catch (Exception e)
            {
                Debug.LogError("[Pandaborn] saving the Pandaborn store failed: " + e);
            }
        }

        /// <summary>The saved payload of a feature, if any, with the version it was written with.</summary>
        public bool TryGet(string feature, out int version, out string payload)
        {
            if (_entries.TryGetValue(feature, out var entry))
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
            if (string.IsNullOrEmpty(feature) || feature.Contains("|")) throw new ArgumentException("bad feature id " + feature);
            _entries[feature] = new Entry(feature, version, payload ?? "");
        }

        public IEnumerable<string> Features => _entries.Keys;

        private sealed class Entry
        {
            public readonly string Feature;
            public readonly int Version;
            public readonly string Payload;

            public Entry(string feature, int version, string payload)
            {
                Feature = feature;
                Version = version;
                Payload = payload;
            }

            /// <summary>"feature|version|payload"; the payload may contain anything.</summary>
            public override string ToString() => Feature + "|" + Version + "|" + Payload;

            public static Entry Parse(string raw)
            {
                if (string.IsNullOrEmpty(raw)) return null;
                int a = raw.IndexOf('|');
                if (a <= 0) return null;
                int b = raw.IndexOf('|', a + 1);
                if (b < 0) return null;
                return int.TryParse(raw.Substring(a + 1, b - a - 1), out int version)
                    ? new Entry(raw.Substring(0, a), version, raw.Substring(b + 1))
                    : null;
            }
        }
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
                if (eq > 0) result[part.Substring(0, eq)] = Uri.UnescapeDataString(part.Substring(eq + 1));
            }
            return result;
        }

        public static string Write(IEnumerable<KeyValuePair<string, string>> values) =>
            string.Join(";", values.Select(kv => kv.Key + "=" + Uri.EscapeDataString(kv.Value ?? "")));
    }
}
