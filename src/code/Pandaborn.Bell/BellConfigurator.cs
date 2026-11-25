using Bindito.Core;
using Pandaborn.Specs;
using Timberborn.EntityPanelSystem;
using Timberborn.TemplateInstantiation;

namespace Pandaborn.Bell
{
    [Context("Game")]
    public class BellConfigurator : Configurator
    {
        protected override void Configure()
        {
            Bind<BellService>().AsSingleton();
            MultiBind<Pandaborn.Core.IWorkdayClock>().ToExisting<BellService>();
            Bind<BellHoursHint>().AsSingleton();
            Bind<BellColonistFragment>().AsSingleton();
            Bind<BellRestedBonus>().AsTransient();
            Bind<BellNightRestedBonus>().AsTransient();
            Bind<BellNightClocks>().AsSingleton();

            Bind<BellSettledMarker>().AsTransient();
            MultiBind<TemplateModule>().ToProvider(ProvideTemplateModule).AsSingleton();
            MultiBind<EntityPanelModule>().ToProvider<PanelModuleProvider>().AsSingleton();
        }

        private static TemplateModule ProvideTemplateModule()
        {
            var builder = new TemplateModule.Builder();
            builder.AddDecorator<PandabornBellSpec, BellRestedBonus>();
            // the night people (a spec of Pandaborn.Specs on the Inkpaws faction's Ringtail templates; see BellNightShift.cs)
            builder.AddDecorator<PandabornRingtailSpec, BellNightRestedBonus>();

            builder.AddDecorator<PandabornBellSettledMarkerSpec, BellSettledMarker>();
            return builder.Build();
        }

        private class PanelModuleProvider : IProvider<EntityPanelModule>
        {
            private readonly BellColonistFragment _fragment;

            public PanelModuleProvider(BellColonistFragment fragment)
            {
                _fragment = fragment;
            }

            public EntityPanelModule Get()
            {
                var builder = new EntityPanelModule.Builder();
                builder.AddMiddleFragment(_fragment, 50);
                return builder.Build();
            }
        }
    }
}
