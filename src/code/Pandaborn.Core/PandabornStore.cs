using System;
using System.Collections.Generic;
using Timberborn.Persistence;
using Timberborn.SingletonSystem;
using Timberborn.WorldPersistence;
using UnityEngine;

namespace Pandaborn.Core
{
    /// <summary>
    /// The save carrier: one saved singleton ("Pandaborn.Store") holding a versioned text entry per feature. It lives in the
    /// always-loaded core, so a feature that is off (forced off, or its game API changed) keeps its saved state: the entry
    /// is read and written back unchanged, and the feature finds it again when it is back on. The same holds for an entry
    /// of a feature this version of the mod does not have, and for lines it cannot read at all (StoreEntries).
    /// Rules for features (ENGINEERING.md, code rule 6): store small text, carry a version, read tolerantly (an unknown
    /// version or a malformed payload means "start fresh", never an exception). A game of another faction, where no
    /// feature writes anything, saves no store at all.
    /// </summary>
    public class PandabornStore : ISaveableSingleton, ILoadableSingleton
    {
        private static readonly SingletonKey StoreKey = new SingletonKey("Pandaborn.Store");
        private static readonly ListKey<string> EntriesKey = new ListKey<string>("Entries");

        private readonly ISingletonLoader _singletonLoader;
        private readonly StoreEntries _entries = new StoreEntries();

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
                foreach (var raw in _entries.Read(loader.Get(EntriesKey)))
                    Debug.LogWarning("[Pandaborn] a saved entry is not readable by this version of the mod; it is kept as it is: " + Short(raw));
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
                if (_entries.IsEmpty) return;
                singletonSaver.GetSingleton(StoreKey).Set(EntriesKey, _entries.Write());
            }
            catch (Exception e)
            {
                Debug.LogError("[Pandaborn] saving the Pandaborn store failed: " + e);
            }
        }

        /// <summary>The saved payload of a feature, if any, with the version it was written with.</summary>
        public bool TryGet(string feature, out int version, out string payload) => _entries.TryGet(feature, out version, out payload);

        public void Set(string feature, int version, string payload) => _entries.Set(feature, version, payload);

        /// <summary>Drops a feature's entry (its own, when it has nothing left to remember). False if there was none.</summary>
        public bool Remove(string feature) => _entries.Remove(feature);

        public IEnumerable<string> Features => _entries.Features;

        internal static string Short(string raw) => raw == null ? "" : raw.Length <= 80 ? raw : raw.Substring(0, 80) + "...";
    }
}
