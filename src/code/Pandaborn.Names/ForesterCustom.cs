using System;
using Bindito.Core;
using Pandaborn.Core;
using Timberborn.BaseComponentSystem;
using Timberborn.Forestry;
using Timberborn.GameFactionSystem;
using Timberborn.TemplateInstantiation;
using UnityEngine;

namespace Pandaborn.Customs
{
    /// <summary>
    /// Small Inkpaw customs: defaults of vanilla buildings that differ for this faction and need no data. They live in
    /// the Names assembly (see its FEATURE.md for why here) but share nothing with the names.
    /// </summary>
    [Context("Game")]
    public class CustomsConfigurator : Configurator
    {
        protected override void Configure()
        {
            Bind<ForesterReplantDefault>().AsTransient();
            MultiBind<TemplateModule>().ToProvider(ProvideTemplateModule).AsSingleton();
        }

        private static TemplateModule ProvideTemplateModule()
        {
            var builder = new TemplateModule.Builder();
            builder.AddDecorator<Forester, ForesterReplantDefault>();
            return builder.Build();
        }
    }

    /// <summary>
    /// DESIGN.md: Inkpaw foresters replant dead trees unless told otherwise (vanilla foresters start with the option off,
    /// so trees a drought killed stand dead on their planting marks until someone finds the checkbox).
    ///
    /// In a game of our faction every forester building starts with Forester.ReplantDeadTrees on. It is set in Awake, the
    /// first thing that happens to a new building, so everything that comes later wins:
    /// * a building loaded from a save gets its saved value (Forester.Load runs after Awake), on or off, also in saves
    ///   made before this existed;
    /// * a building made with the copy tool gets its source's value (the game copies settings in PreInitialize);
    /// * the player's checkbox (building panel or batch control) is the game's own Forester.SetReplantDeadTrees and is
    ///   saved by the game. Nothing of ours is saved.
    /// With the module off, new foresters start with the option off as in the plain game; existing ones keep theirs.
    /// The option replaces dead TREES only (Forester.Validate asks the blocker for a TreeComponent): timber bamboo and
    /// persimmon. Tea and Sichuan pepper are bushes and are not replaced by it (see FEATURE.md).
    /// </summary>
    public class ForesterReplantDefault : BaseComponent, IAwakableComponent
    {
        private static bool _failed;
        private readonly FactionService _factionService;

        public ForesterReplantDefault(FactionService factionService)
        {
            _factionService = factionService;
        }

        /// <summary>Foresters given the default in this session (for tests).</summary>
        public static int Defaulted { get; private set; }

        public void Awake()
        {
            if (_failed) return;
            try
            {
                if (_factionService.Current?.Id != FeatureNotices.FactionId) return;
                var forester = GetComponent<Forester>();
                if (forester == null || forester.ReplantDeadTrees) return;
                forester.SetReplantDeadTrees(true);
                Defaulted++;
            }
            catch (Exception e)
            {
                _failed = true;
                Debug.LogError("[Pandaborn.Customs] the replant-dead-trees default failed and is off for this session: " + e);
            }
        }
    }
}
