using System;
using System.Collections.Generic;
using Bindito.Core;
using Pandaborn.Core;
using Pandaborn.Specs;
using Timberborn.BaseComponentSystem;
using Timberborn.Characters;
using Timberborn.EntitySystem;
using Timberborn.TemplateInstantiation;

namespace Pandaborn.DevCarrier
{
    [Context("Game")]
    public class DevCarrierConfigurator : Configurator
    {
        protected override void Configure()
        {
            Bind<DevCarrierComponent>().AsTransient();
            MultiBind<TemplateModule>().ToProvider(() =>
            {
                var b = new TemplateModule.Builder();
                b.AddDecorator<PandabornEntityStateSpec, DevCarrierComponent>();
                return b.Build();
            }).AsSingleton();
        }
    }

    /// <summary>
    /// Dev only. On every entity with the carrier: reads entry "DevCarrier" after the entity has loaded (what an earlier
    /// session, or the test probe while this feature was off, left there), records it, then keeps its own entry up to date
    /// through a save-time writer that also carries the previous payload forward.
    /// </summary>
    public class DevCarrierComponent : BaseComponent, IPostInitializableEntity
    {
        public const string Feature = "DevCarrier";

        /// <summary>One line per entity: "name|found|version|payload". Read by the foundation probe.</summary>
        public static readonly List<string> Reports = new List<string>();

        public void PostInitializeEntity()
        {
            var state = GetComponent<PandabornEntityState>();
            if (state == null) return;
            var character = GetComponent<Character>();
            string name = character != null ? character.FirstName : "?";
            bool found = state.TryGet(Feature, out int version, out string payload);
            Reports.Add(name + "|" + found + "|" + version + "|" + payload);
            string carried = found ? payload : "";
            state.SetWriter(Feature, 1, () => "seenOn=1;prev=" + Uri.EscapeDataString(carried));
        }
    }
}
