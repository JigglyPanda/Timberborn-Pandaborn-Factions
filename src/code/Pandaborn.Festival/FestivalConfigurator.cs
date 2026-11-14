using Bindito.Core;
using Pandaborn.Specs;
using Timberborn.EntityPanelSystem;
using Timberborn.TemplateInstantiation;
using Timberborn.ToolSystem;

namespace Pandaborn.Festival
{
    [Context("Game")]
    public class FestivalConfigurator : Configurator
    {
        protected override void Configure()
        {
            if (DevFlags.ForcedOff("Festival")) return;   // only for test builds; the bootstrap never loads a forced-off module
            Bind<FestivalService>().AsSingleton();
            Bind<FestivalFireworks>().AsSingleton();
            Bind<FestivalSquareFragment>().AsSingleton();
            Bind<FestivalSquare>().AsTransient();
            Bind<FestivalGoer>().AsTransient();
            MultiBind<IToolLocker>().To<TraditionToolLocker>().AsSingleton();
            MultiBind<TemplateModule>().ToProvider(ProvideTemplateModule).AsSingleton();
            MultiBind<EntityPanelModule>().ToProvider<PanelModuleProvider>().AsSingleton();
        }

        private static TemplateModule ProvideTemplateModule()
        {
            var builder = new TemplateModule.Builder();
            builder.AddDecorator<PandabornFestivalSquareSpec, FestivalSquare>();
            builder.AddDecorator<PandabornFestivalGoerSpec, FestivalGoer>();
            return builder.Build();
        }

        private class PanelModuleProvider : IProvider<EntityPanelModule>
        {
            private readonly FestivalSquareFragment _fragment;

            public PanelModuleProvider(FestivalSquareFragment fragment)
            {
                _fragment = fragment;
            }

            public EntityPanelModule Get()
            {
                var builder = new EntityPanelModule.Builder();
                builder.AddBottomFragment(_fragment, 40);
                return builder.Build();
            }
        }
    }
}
