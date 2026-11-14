using Bindito.Core;
using Pandaborn.Specs;
using Timberborn.EntityPanelSystem;
using Timberborn.TemplateInstantiation;

namespace Pandaborn.Ringtails
{
    [Context("Game")]
    public class RingtailsConfigurator : Configurator
    {
        protected override void Configure()
        {
            Bind<RingtailService>().AsSingleton();
            Bind<RingtailWorkday>().AsSingleton();
            Bind<LoftHousingRule>().AsSingleton();
            Bind<LoftNursery>().AsSingleton();
            Bind<RingtailsPopulationRow>().AsSingleton();
            Bind<RingtailsBuildingFragment>().AsSingleton();
            Bind<RingtailRestRootBehavior>().AsTransient();
            Bind<RingtailCoat>().AsTransient();
            Bind<RingtailGrowth>().AsTransient();
            Bind<RingtailBadge>().AsTransient();
            Bind<NightPost>().AsTransient();
            Bind<MoonLoft>().AsTransient();
            MultiBind<TemplateModule>().ToProvider(ProvideTemplateModule).AsSingleton();
            MultiBind<EntityPanelModule>().ToProvider<PanelModuleProvider>().AsSingleton();
        }

        private static TemplateModule ProvideTemplateModule()
        {
            var builder = new TemplateModule.Builder();
            builder.AddDecorator<PandabornRingtailSpec, RingtailRestRootBehavior>();
            builder.AddDecorator<PandabornRingtailSpec, RingtailCoat>();
            builder.AddDecorator<PandabornRingtailSpec, RingtailGrowth>();
            builder.AddDecorator<PandabornRingtailSpec, RingtailBadge>();
            builder.AddDecorator<PandabornNightPostSpec, NightPost>();
            builder.AddDecorator<PandabornMoonLoftSpec, MoonLoft>();
            return builder.Build();
        }

        private class PanelModuleProvider : IProvider<EntityPanelModule>
        {
            private readonly RingtailsBuildingFragment _fragment;

            public PanelModuleProvider(RingtailsBuildingFragment fragment)
            {
                _fragment = fragment;
            }

            public EntityPanelModule Get()
            {
                var builder = new EntityPanelModule.Builder();
                builder.AddMiddleFragment(_fragment, 40);
                return builder.Build();
            }
        }
    }
}
