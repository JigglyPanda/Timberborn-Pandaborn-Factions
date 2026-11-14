using System;
using System.Collections.Generic;
using System.Linq;
using Timberborn.BaseComponentSystem;
using Timberborn.Persistence;
using Timberborn.WorldPersistence;
using UnityEngine;

namespace Pandaborn.Core
{
    /// <summary>
    /// The per-entity save carrier (Core, always loaded), attached to every entity whose template carries
    /// Pandaborn.Specs.PandabornEntityStateSpec. It holds one versioned text entry per feature and saves all of them,
    /// including the entries of features that are off in this session, so turning a feature off never loses its
    /// per-entity data. Saved as component "Pandaborn.EntityState", list "Entries", each "feature|version|payload".
    ///
    /// Use from a feature component on the same entity:
    ///   var state = GetComponent&lt;PandabornEntityState&gt;();            // null if the template lacks the spec
    ///   in InitializeEntity/PostInitializeEntity (after the game has loaded the entity):
    ///       if (state.TryGet("Feature", out int v, out string payload) &amp;&amp; v == 1) ... read tolerantly ...
    ///   to save, either state.Set("Feature", 1, payload) whenever it changes, or once:
    ///       state.SetWriter("Feature", 1, () =&gt; payload)               // called on every save
    /// Entries are never removed by the carrier; a feature removes its own with Remove("Feature").
    /// </summary>
    public class PandabornEntityState : BaseComponent, IPersistentEntity
    {
        private static readonly ComponentKey Key = new ComponentKey("Pandaborn.EntityState");
        private static readonly ListKey<string> EntriesKey = new ListKey<string>("Entries");

        private readonly Dictionary<string, (int Version, string Payload)> _entries = new Dictionary<string, (int, string)>(StringComparer.Ordinal);
        private readonly Dictionary<string, (int Version, Func<string> Writer)> _writers = new Dictionary<string, (int, Func<string>)>(StringComparer.Ordinal);

        /// <summary>True when this entity was loaded from a save that had a carrier entry list.</summary>
        public bool LoadedFromSave { get; private set; }

        public IEnumerable<string> Features => _entries.Keys.Concat(_writers.Keys).Distinct();

        public bool TryGet(string feature, out int version, out string payload)
        {
            if (_entries.TryGetValue(feature, out var e))
            {
                version = e.Version;
                payload = e.Payload;
                return true;
            }
            version = 0;
            payload = null;
            return false;
        }

        public void Set(string feature, int version, string payload)
        {
            Check(feature);
            _entries[feature] = (version, payload ?? "");
        }

        /// <summary>Registers a function that produces the feature's payload at save time (replaces Set for that feature).</summary>
        public void SetWriter(string feature, int version, Func<string> writer)
        {
            Check(feature);
            _writers[feature] = (version, writer);
        }

        public void Remove(string feature)
        {
            _entries.Remove(feature);
            _writers.Remove(feature);
        }

        public void Save(IEntitySaver entitySaver)
        {
            try
            {
                foreach (var w in _writers)
                {
                    try { _entries[w.Key] = (w.Value.Version, w.Value.Writer() ?? ""); }
                    catch (Exception e) { Debug.LogError("[Pandaborn] entity state writer of " + w.Key + " failed; its last entry is kept: " + e); }
                }
                if (_entries.Count == 0) return;
                var lines = _entries.OrderBy(e => e.Key, StringComparer.Ordinal).Select(e => e.Key + "|" + e.Value.Version + "|" + e.Value.Payload).ToList();
                entitySaver.GetComponent(Key).Set(EntriesKey, lines);
            }
            catch (Exception e)
            {
                Debug.LogError("[Pandaborn] saving entity state failed: " + e);
            }
        }

        public void Load(IEntityLoader entityLoader)
        {
            try
            {
                if (!entityLoader.HasComponent(Key)) return;
                var loader = entityLoader.GetComponent(Key);
                if (!loader.Has(EntriesKey)) return;
                LoadedFromSave = true;
                foreach (var raw in loader.Get(EntriesKey))
                {
                    int a = raw?.IndexOf('|') ?? -1;
                    int b = a > 0 ? raw.IndexOf('|', a + 1) : -1;
                    if (b < 0 || !int.TryParse(raw.Substring(a + 1, b - a - 1), out int version))
                    {
                        Debug.LogWarning("[Pandaborn] ignored a malformed entity state entry: " + raw);
                        continue;
                    }
                    _entries[raw.Substring(0, a)] = (version, raw.Substring(b + 1));
                }
            }
            catch (Exception e)
            {
                Debug.LogError("[Pandaborn] reading entity state failed; the entity starts fresh: " + e);
            }
        }

        private static void Check(string feature)
        {
            if (string.IsNullOrEmpty(feature) || feature.Contains("|")) throw new ArgumentException("bad feature id " + feature);
        }
    }
}
