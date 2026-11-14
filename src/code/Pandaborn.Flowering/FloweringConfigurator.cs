using Bindito.Core;
using Pandaborn.Specs;
using Timberborn.EntityPanelSystem;
using Timberborn.TemplateInstantiation;

namespace Pandaborn.Flowering
{
    [Context("Game")]
    public class FloweringConfigurator : Configurator
    {
        protected override void Configure()
        {
            if (DevFlags.ForcedOff("Flowering")) return;   // only for test builds; the bootstrap never loads a forced-off module
            Bind<FloweringService>().AsSingleton();
            Bind<FloweringSettingDialog>().AsSingleton();
            Bind<FloweringIndicator>().AsSingleton();
            Bind<FloweringPlantFragment>().AsSingleton();
            Bind<FloweringPlant>().AsTransient();
            Bind<InFlowerPlant>().AsTransient();
            MultiBind<TemplateModule>().ToProvider(ProvideTemplateModule).AsSingleton();
            MultiBind<EntityPanelModule>().ToProvider<PanelModuleProvider>().AsSingleton();
        }

        private static TemplateModule ProvideTemplateModule()
        {
            var builder = new TemplateModule.Builder();
            builder.AddDecorator<PandabornFloweringPlantSpec, FloweringPlant>();
            builder.AddDecorator<PandabornInFlowerSpec, InFlowerPlant>();
            return builder.Build();
        }

        private class PanelModuleProvider : IProvider<EntityPanelModule>
        {
            private readonly FloweringPlantFragment _fragment;

            public PanelModuleProvider(FloweringPlantFragment fragment)
            {
                _fragment = fragment;
            }

            public EntityPanelModule Get()
            {
                var builder = new EntityPanelModule.Builder();
                builder.AddMiddleFragment(_fragment, 60);
                return builder.Build();
            }
        }
    }
}
