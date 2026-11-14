using System.Collections.Generic;
using Timberborn.BaseComponentSystem;
using Timberborn.Effects;
using Timberborn.NeedSystem;
using Timberborn.TickSystem;
using Timberborn.TimeSystem;

namespace Pandaborn.Ringtails
{
    /// <summary>
    /// Light eaters and drinkers, with public API only: every tick a small continuous effect gives back part of the Hunger
    /// and Thirst decay (NeedSpec.DailyDelta), so the net rate is AppetiteFactor x vanilla. No private field; the per-entity
    /// rate inside Need is left alone. Approximation: the game mode's food/water consumption multiplier is not applied
    /// to the give-back, so on non-default modes the factor is slightly off.
    /// </summary>
    public class RingtailAppetite : TickableComponent, IAwakableComponent
    {
        private static readonly string[] Needs = { "Hunger", "Thirst" };
        private readonly IDayNightCycle _dayNightCycle;
        private readonly List<ContinuousEffect> _effects = new List<ContinuousEffect>();
        private NeedManager _needManager;

        public RingtailAppetite(IDayNightCycle dayNightCycle)
        {
            _dayNightCycle = dayNightCycle;
        }

        private float _factor = 1f;
        private bool _initialized;

        public void Awake()
        {
            _needManager = GetComponent<NeedManager>();
            var spec = GetComponent<PandabornRingtailSpec>();
            _factor = spec != null ? spec.AppetiteFactor : 1f;
            if (_needManager == null || _factor >= 1f) DisableComponent();
        }

        /// <summary>NeedManager fills NeedSpecs in its own Awake, whose order relative to ours is not defined: read them lazily.</summary>
        private void Initialize()
        {
            _initialized = true;
            foreach (var need in _needManager.NeedSpecs)
                if (System.Array.IndexOf(Needs, need.Id) >= 0 && need.DailyDelta < 0f)
                    _effects.Add(new ContinuousEffect(need.Id, -need.DailyDelta / 24f * (1f - _factor)));
        }

        public override void Tick()
        {
            if (!_initialized) Initialize();
            float hours = _dayNightCycle.FixedDeltaTimeInHours;
            for (int i = 0; i < _effects.Count; i++)
                if (_needManager.NeedIsEnabled(_effects[i].NeedId)) _needManager.ApplyEffect(_effects[i], hours);
        }
    }
}
