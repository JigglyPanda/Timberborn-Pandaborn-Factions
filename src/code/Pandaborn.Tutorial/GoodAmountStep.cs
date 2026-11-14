using System;
using Bindito.Core;
using Pandaborn.Specs;
using Timberborn.BlueprintSystem;
using Timberborn.Goods;
using Timberborn.Localization;
using Timberborn.ResourceCountingSystem;
using Timberborn.TutorialSystem;
using UnityEngine;

namespace Pandaborn.Tutorial
{
    [Context("Game")]
    public class TutorialStepsConfigurator : Configurator
    {
        protected override void Configure()
        {
            MultiBind<IStepDeserializer>().To<GoodAmountStepDeserializer>().AsSingleton();
        }
    }

    /// <summary>
    /// Turns a PandabornGoodAmountStepSpec step blueprint into a tutorial step. The game offers every step blueprint to
    /// every IStepDeserializer and drops a step none accepts, so with this module off such a step simply disappears.
    /// </summary>
    public class GoodAmountStepDeserializer : IStepDeserializer
    {
        private readonly ResourceCountingService _resourceCountingService;
        private readonly IGoodService _goodService;
        private readonly ILoc _loc;

        public GoodAmountStepDeserializer(ResourceCountingService resourceCountingService, IGoodService goodService, ILoc loc)
        {
            _resourceCountingService = resourceCountingService;
            _goodService = goodService;
            _loc = loc;
        }

        public bool TryDeserialize(Blueprint step, out TutorialStep tutorialStep)
        {
            tutorialStep = null;
            if (step.Specs.IsDefaultOrEmpty || !(step.Specs[0] is PandabornGoodAmountStepSpec spec)) return false;
            tutorialStep = TutorialStep.Create(new GoodAmountStep(_resourceCountingService, _goodService, _loc, spec.GoodId, Math.Max(1, spec.Amount)));
            return true;
        }
    }

    /// <summary>"Have 20 Poles (7/20)": achieved while the settlement's available stock of the good reaches the amount.
    /// A good the faction does not have reads its id and is never achieved (it never throws).</summary>
    public class GoodAmountStep : ITutorialStep
    {
        private readonly ResourceCountingService _resourceCountingService;
        private readonly ILoc _loc;
        private readonly string _goodId;
        private readonly int _amount;
        private readonly string _goodName;
        private readonly bool _known;

        public GoodAmountStep(ResourceCountingService resourceCountingService, IGoodService goodService, ILoc loc, string goodId, int amount)
        {
            _resourceCountingService = resourceCountingService;
            _loc = loc;
            _goodId = goodId ?? "";
            _amount = amount;
            var good = goodService.GetGoodOrNull(_goodId);
            _known = good != null;
            _goodName = good?.PluralDisplayName?.Value ?? _goodId;
            if (!_known) Debug.LogWarning("[Pandaborn.Tutorial] tutorial step names a good this faction does not have: " + _goodId);
        }

        public int InStock
        {
            get
            {
                if (!_known) return 0;
                try { return _resourceCountingService.GetGlobalResourceCount(_goodId).AvailableStock; }
                catch (Exception) { return 0; }
            }
        }

        public string Description() => _loc.T("Pandaborn.Tutorial.HaveGoods", _amount, _goodName, Math.Min(InStock, _amount));

        public bool Achieved() => _known && InStock >= _amount;
    }
}
