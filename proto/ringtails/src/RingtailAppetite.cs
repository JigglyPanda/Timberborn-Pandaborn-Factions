using System.Collections.Generic;
using Timberborn.BaseComponentSystem;
using Timberborn.Effects;
using Timberborn.NeedSystem;
using Timberborn.TickSystem;
using Timberborn.TimeSystem;

namespace Pandaborn.Ringtails
{
    /// <summary>
    /// Light eaters and drinkers, with public API only. Vanilla <c>Need.Update</c> skips a tick's decay whenever any effect
    /// was applied to the need since the last update (that is how eating and sleeping pause it). So applying a negligible
    /// effect on (1 - AppetiteFactor) of the ticks removes exactly that share of the Hunger and Thirst decay: net rate =
    /// AppetiteFactor x vanilla, game-mode consumption multipliers included. No private field.
    /// Implicit dependency: the "an effect suppresses this tick's decay" rule in Need.Update. If it changed, Ringtails would
    /// simply eat like Inkpaws (safe).
    /// (A first version gave back points every tick; because of the same rule that stopped the decay entirely.)
    /// </summary>
    public class RingtailAppetite : TickableComponent, IAwakableComponent
    {
        private static readonly string[] NeedIds = { "Hunger", "Thirst" };
        private const float Nudge = 0.0001f;   // points per hour; about 3e-6 points per tick
        private readonly IDayNightCycle _dayNightCycle;
        private NeedManager _needManager;
        private float _skipShare;
        private float _accumulator;

        public RingtailAppetite(IDayNightCycle dayNightCycle)
        {
            _dayNightCycle = dayNightCycle;
        }

        public void Awake()
        {
            _needManager = GetComponent<NeedManager>();
            var spec = GetComponent<PandabornRingtailSpec>();
            float factor = spec != null ? spec.AppetiteFactor : 1f;
            _skipShare = 1f - factor;
            if (_needManager == null || _skipShare <= 0f) DisableComponent();
        }

        public override void Tick()
        {
            _accumulator += _skipShare;
            if (_accumulator < 1f) return;
            _accumulator -= 1f;
            float hours = _dayNightCycle.FixedDeltaTimeInHours;
            foreach (var id in NeedIds)
                if (_needManager.HasNeed(id) && _needManager.NeedIsEnabled(id))
                    _needManager.ApplyEffect(new ContinuousEffect(id, Nudge), hours);
        }
    }
}
