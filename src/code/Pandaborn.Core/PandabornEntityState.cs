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
    /// Entries are never removed by the carrier; a feature removes its own with Remove("Feature"). Entries of features
    /// that are off or unknown to this version of the mod, and lines it cannot read, are written back unchanged.
    /// </summary>
    public class PandabornEntityState : BaseComponent, IPersistentEntity
    {
        private static readonly ComponentKey Key = new ComponentKey("Pandaborn.EntityState");
        private static readonly ListKey<string> EntriesKey = new ListKey<string>("Entries");

        private readonly StoreEntries _entries = new StoreEntries();
        private readonly Dictionary<string, (int Version, Func<string> Writer)> _writers = new Dictionary<string, (int, Func<string>)>(StringComparer.Ordinal);

        /// <summary>True when this entity was loaded from a save that had a carrier entry list.</summary>
        public bool LoadedFromSave { get; private set; }

        public IEnumerable<string> Features => _entries.Features.Concat(_writers.Keys).Distinct();

        public bool TryGet(string feature, out int version, out string payload) => _entries.TryGet(feature, out version, out payload);

        public void Set(string feature, int version, string payload) => _entries.Set(feature, version, payload);

        /// <summary>Registers a function that produces the feature's payload at save time (replaces Set for that feature).</summary>
        public void SetWriter(string feature, int version, Func<string> writer)
        {
            StoreEntry.CheckFeature(feature);
            if (writer == null) throw new ArgumentNullException(nameof(writer));
            _writers[feature] = (version, writer);
        }

        public void Remove(string feature)
        {
            if (feature == null) return;
            _entries.Remove(feature);
            _writers.Remove(feature);
        }

        public void Save(IEntitySaver entitySaver)
        {
            try
            {
                foreach (var w in _writers)
                {
                    try { _entries.Set(w.Key, w.Value.Version, w.Value.Writer() ?? ""); }
                    catch (Exception e)
                    {
                        // one line per feature and session: a writer that fails does so on every entity at every save
                        if (FailedWriters.Add(w.Key)) Debug.LogError("[Pandaborn] entity state writer of " + w.Key + " failed; the last entry is kept: " + e);
                    }
                }
                if (_entries.IsEmpty) return;
                entitySaver.GetComponent(Key).Set(EntriesKey, _entries.Write());
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
                var bad = _entries.Read(loader.Get(EntriesKey));
                if (bad.Count > 0 && !_warnedUnreadable)
                {
                    _warnedUnreadable = true;
                    Debug.LogWarning("[Pandaborn] an entity state entry is not readable by this version of the mod; such entries are kept as they are: "
                                     + PandabornStore.Short(bad[0]));
                }
            }
            catch (Exception e)
            {
                Debug.LogError("[Pandaborn] reading entity state failed; the entity starts fresh: " + e);
            }
        }

        private static readonly HashSet<string> FailedWriters = new HashSet<string>(StringComparer.Ordinal);
        private static bool _warnedUnreadable;
    }
}
