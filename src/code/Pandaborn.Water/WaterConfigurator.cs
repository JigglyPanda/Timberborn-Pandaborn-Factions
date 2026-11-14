using Bindito.Core;
using Pandaborn.Specs;
using Timberborn.EntityPanelSystem;
using Timberborn.TemplateInstantiation;

namespace Pandaborn.Water
{
    [Context("Game")]
    public class WaterConfigurator : Configurator
    {
        protected override void Configure()
        {
            Bind<FlumeService>().AsSingleton();
            Bind<WaterSounds>().AsSingleton();
            Bind<CisternTapHint>().AsSingleton();
            Bind<FlumeGateFragment>().AsSingleton();
            Bind<WaterInfoFragment>().AsSingleton();
            Bind<FlumeSegment>().AsTransient();
            Bind<SolidCells>().AsTransient();
            Bind<FlumeGate>().AsTransient();
            Bind<FlumeMonitor>().AsTransient();
            Bind<DewLimiter>().AsTransient();
            Bind<CurrentDriven>().AsTransient();
            MultiBind<TemplateModule>().ToProvider(ProvideTemplateModule).AsSingleton();
            MultiBind<EntityPanelModule>().ToProvider<PanelModuleProvider>().AsSingleton();
        }

        private static TemplateModule ProvideTemplateModule()
        {
            var builder = new TemplateModule.Builder();
            builder.AddDecorator<PandabornFlumeSegmentSpec, FlumeSegment>();
            builder.AddDecorator<FlumeSegment, FlumeMonitor>();
            builder.AddDecorator<PandabornFlumeGateSpec, FlumeGate>();
            builder.AddDecorator<PandabornSolidCellsSpec, SolidCells>();
            builder.AddDecorator<PandabornDewLimiterSpec, DewLimiter>();
            builder.AddDecorator<PandabornCurrentDrivenSpec, CurrentDriven>();
            return builder.Build();
        }

        private class PanelModuleProvider : IProvider<EntityPanelModule>
        {
            private readonly FlumeGateFragment _gate;
            private readonly WaterInfoFragment _info;

            public PanelModuleProvider(FlumeGateFragment gate, WaterInfoFragment info)
            {
                _gate = gate;
                _info = info;
            }

            public EntityPanelModule Get()
            {
                var builder = new EntityPanelModule.Builder();
                builder.AddMiddleFragment(_gate, 40);
                builder.AddMiddleFragment(_info, 41);
                return builder.Build();
            }
        }
    }
}
