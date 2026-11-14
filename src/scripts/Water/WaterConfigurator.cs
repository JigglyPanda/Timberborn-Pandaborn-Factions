using Bindito.Core;
using Timberborn.TemplateInstantiation;

namespace Pandaborn.Water
{
    [Context("Game")]
    public class WaterConfigurator : Configurator
    {
        protected override void Configure()
        {
            Bind<FlumeSegment>().AsTransient();
            Bind<DewLimiter>().AsTransient();
            MultiBind<TemplateModule>().ToProvider(ProvideTemplateModule).AsSingleton();
        }

        private static TemplateModule ProvideTemplateModule()
        {
            var builder = new TemplateModule.Builder();
            builder.AddDecorator<PandabornFlumeSegmentSpec, FlumeSegment>();
            builder.AddDecorator<PandabornDewLimiterSpec, DewLimiter>();
            return builder.Build();
        }
    }
}

namespace System.Runtime.CompilerServices
{
    /// <summary>Lets C# 9 init-only setters compile against netstandard2.1.</summary>
    internal static class IsExternalInit { }
}
