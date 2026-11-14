using Bindito.Core;
using Timberborn.TemplateInstantiation;

namespace Pandaborn.Ringtails
{
    [Context("Game")]
    public class RingtailsConfigurator : Configurator
    {
        protected override void Configure()
        {
            Bind<RingtailService>().AsSingleton();
            Bind<LoftHousingRule>().AsSingleton();
            Bind<RingtailRestRootBehavior>().AsTransient();
            Bind<RingtailCoat>().AsTransient();
            Bind<RingtailGrowth>().AsTransient();
            MultiBind<TemplateModule>().ToProvider(ProvideTemplateModule).AsSingleton();
        }

        private static TemplateModule ProvideTemplateModule()
        {
            var builder = new TemplateModule.Builder();
            builder.AddDecorator<PandabornRingtailSpec, RingtailRestRootBehavior>();
            builder.AddDecorator<PandabornRingtailSpec, RingtailCoat>();
            builder.AddDecorator<PandabornRingtailSpec, RingtailGrowth>();
            return builder.Build();
        }
    }
}
