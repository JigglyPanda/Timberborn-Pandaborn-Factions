using System;
using System.Collections.Generic;
using System.Linq;
using Bindito.Core;
using Pandaborn.Core;
using Pandaborn.Specs;
using Timberborn.BaseComponentSystem;
using Timberborn.Common;
using Timberborn.EntityNaming;
using Timberborn.Localization;
using Timberborn.SingletonSystem;
using Timberborn.TemplateInstantiation;
using UnityEngine;

namespace Pandaborn.Names
{
    [Context("Game")]
    public class NamesConfigurator : Configurator
    {
        protected override void Configure()
        {
            Bind<NamePoolService>().AsSingleton();
            Bind<NamesDataCheck>().AsSingleton();
            Bind<FactionNamer>().AsTransient();
            MultiBind<TemplateModule>().ToProvider(ProvideTemplateModule).AsSingleton();
        }

        private static TemplateModule ProvideTemplateModule()
        {
            var builder = new TemplateModule.Builder();
            builder.AddDecorator<PandabornNamePoolSpec, FactionNamer>();
            return builder.Build();
        }
    }

    /// <summary>
    /// Names a colonist from its template's own pool (PandabornNamePoolSpec). The vanilla namer (BeaverEntityNamer) has
    /// priority 20 and NamedEntity uses the namer with the highest priority, so this one (30) wins wherever the spec is.
    /// It only runs when a colonist gets its first name: names are saved per colonist by the game, and a kit keeps its
    /// name when it grows up.
    /// </summary>
    public class FactionNamer : BaseComponent, IAwakableComponent, IEntityNamer
    {
        private readonly NamePoolService _pools;
        private PandabornNamePoolSpec _spec;

        public FactionNamer(NamePoolService pools)
        {
            _pools = pools;
        }

        public int EntityNamerPriority => 30;

        public void Awake()
        {
            _spec = GetComponent<PandabornNamePoolSpec>();
        }

        public string GenerateEntityName() => _pools.Next(_spec?.NamePoolLocKey);
    }

    /// <summary>
    /// Draws names without repeats until a pool is used up, like the vanilla BeaverNameService, and remembers what is left
    /// in the Pandaborn store (feature "Names", version 1).
    /// </summary>
    public class NamePoolService : ILoadableSingleton
    {
        private const string StoreFeature = "Names";
        private readonly ILoc _loc;
        private readonly IRandomNumberGenerator _random;
        private readonly PandabornStore _store;
        private readonly Dictionary<string, List<string>> _remaining = new Dictionary<string, List<string>>(StringComparer.Ordinal);
        private Dictionary<string, string> _saved = new Dictionary<string, string>(StringComparer.Ordinal);

        public NamePoolService(ILoc loc, IRandomNumberGenerator random, PandabornStore store)
        {
            _loc = loc;
            _random = random;
            _store = store;
        }

        public void Load()
        {
            if (_store.TryGet(StoreFeature, out int version, out string payload) && version == 1) _saved = Payload.Parse(payload);
        }

        /// <summary>A name from the pool. Never null or empty (NamedEntity does not fall back to the next namer): a missing
        /// pool key gives a vanilla name, an empty pool gives "Panda".</summary>
        public string Next(string poolKey)
        {
            try
            {
                if (string.IsNullOrEmpty(poolKey)) return Vanilla();
                var full = Pool(poolKey);
                if (full.Count == 0) return Vanilla();
                if (!_remaining.TryGetValue(poolKey, out var left))
                {
                    left = _saved.TryGetValue(poolKey, out var s)
                        ? s.Split('\n').Where(n => full.Contains(n)).ToList()
                        : new List<string>();
                    _remaining[poolKey] = left;
                }
                if (left.Count == 0) left.AddRange(full);
                string name = left[_random.Range(0, left.Count)];
                left.Remove(name);
                Persist();
                return name;
            }
            catch (Exception e)
            {
                Debug.LogError("[Pandaborn.Names] drawing a name failed: " + e);
                return "Panda";
            }
        }

        /// <summary>A random name from the game's own list, for a template whose pool is missing or empty: better a beaver
        /// name than a village where everyone is called the same.</summary>
        private string Vanilla()
        {
            var names = _loc.T("Beaver.NamePool").Split('\n').Select(Clean).Where(n => n.Length > 0).ToList();
            return names.Count > 0 ? names[_random.Range(0, names.Count)] : "Panda";
        }

        private List<string> Pool(string key) => _loc.T(key).Split('\n').Select(Clean).Where(n => n.Length > 0 && !n.Contains(key)).Distinct().ToList();

        private static string Clean(string s) => s.Replace("\r", "").Trim();

        private void Persist()
        {
            foreach (var kv in _remaining) _saved[kv.Key] = string.Join("\n", kv.Value);
            _store.Set(StoreFeature, 1, Payload.Write(_saved));
        }
    }

    /// <summary>Shipped but not switched on by data: in a game of our faction whose adult template has no
    /// PandabornNamePoolSpec, the feature report says so (colonists then get vanilla names).</summary>
    public class NamesDataCheck : ILoadableSingleton
    {
        private readonly Timberborn.TemplateSystem.TemplateService _templateService;
        private readonly Timberborn.GameFactionSystem.FactionService _factionService;

        public NamesDataCheck(Timberborn.TemplateSystem.TemplateService templateService, Timberborn.GameFactionSystem.FactionService factionService)
        {
            _templateService = templateService;
            _factionService = factionService;
        }

        public void Load()
        {
            try
            {
                if (_factionService.Current?.Id != FeatureNotices.FactionId) return;
                var adult = _templateService.GetAll<Timberborn.Beavers.AdultSpec>().FirstOrDefault();
                if (adult?.Blueprint?.GetSpec<PandabornNamePoolSpec>() == null)
                    FeatureRegistry.ReportNoData("Names", "the faction's adult template has no PandabornNamePoolSpec");
            }
            catch (Exception e) { Debug.LogWarning("[Pandaborn.Names] data check failed: " + e.Message); }
        }
    }
}