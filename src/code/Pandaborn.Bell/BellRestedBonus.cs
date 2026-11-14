using System;
using Timberborn.BaseComponentSystem;
using Timberborn.BonusSystem;
using Timberborn.EntitySystem;
using UnityEngine;

namespace Pandaborn.Bell
{
    /// <summary>
    /// The rested bonus on one Inkpaw (decorates PandabornBellSpec, which only the faction's adult template carries).
    ///
    /// The bonus multiplies the colonist's whole multiplier: with the bell's bonus b and every other bonus summed into
    /// m (wellbeing tiers, need penalties, overburdening, workplace bonuses), the result is m x (1 + b), not m + b. The game's
    /// bonuses only add (BonusManager keeps one sum per bonus id), so this component adds d = m x b and recomputes d
    /// whenever any other bonus of that id changes (BonusManager.BonusValueChanged), by taking its own share out,
    /// reading the multiplier, and putting d back. The result is exact unless m itself is clamped by the bonus type's
    /// limits, in which case the clamp decides either way.
    ///
    /// Nothing is saved: bonuses are rebuilt on load by whoever adds them, so with the module off the colonist simply has
    /// vanilla speeds (ENGINEERING.md, code rule 5).
    /// </summary>
    public class BellRestedBonus : BaseComponent, IAwakableComponent, IPostInitializableEntity, IDeletableEntity
    {
        public const string WorkingSpeedId = "WorkingSpeed";
        public const string MovementSpeedId = "MovementSpeed";

        private readonly BellService _bellService;
        private BonusManager _bonusManager;
        private bool _registered;
        private bool _updating;

        public BellRestedBonus(BellService bellService)
        {
            _bellService = bellService;
        }

        /// <summary>The additive share currently in the colonist's WorkingSpeed sum.</summary>
        public float WorkingDelta { get; private set; }

        /// <summary>The additive share currently in the colonist's MovementSpeed sum.</summary>
        public float MovementDelta { get; private set; }

        /// <summary>WorkingSpeed multiplier without the bell, as last measured.</summary>
        public float WorkingBase { get; private set; } = 1f;

        /// <summary>MovementSpeed multiplier without the bell, as last measured.</summary>
        public float MovementBase { get; private set; } = 1f;

        public float WorkingFactor => _bellService.WorkingBonus;

        public float MovementFactor => _bellService.MovementBonus;

        public bool IsActive => _registered;

        public void Awake()
        {
            _bonusManager = GetComponent<BonusManager>();
        }

        public void PostInitializeEntity()
        {
            if (!_bellService.Active || _bonusManager == null) return;
            _registered = true;
            _bellService.Changed += Refresh;
            _bonusManager.BonusValueChanged += OnBonusValueChanged;
            Refresh();
        }

        public void DeleteEntity()
        {
            if (!_registered) return;
            _registered = false;
            _bellService.Changed -= Refresh;
            _bonusManager.BonusValueChanged -= OnBonusValueChanged;
            Apply(WorkingSpeedId, 0f);
            Apply(MovementSpeedId, 0f);
        }

        /// <summary>Recomputes both shares (after a change of day length).</summary>
        public void Refresh()
        {
            if (!_registered) return;
            Apply(WorkingSpeedId, _bellService.WorkingBonus);
            Apply(MovementSpeedId, _bellService.MovementBonus);
        }

        private void OnBonusValueChanged(object sender, BonusValueChangedEventArgs e)
        {
            if (_updating || !_registered) return;
            if (e.BonusId == WorkingSpeedId) Apply(WorkingSpeedId, _bellService.WorkingBonus);
            else if (e.BonusId == MovementSpeedId) Apply(MovementSpeedId, _bellService.MovementBonus);
        }

        private void Apply(string bonusId, float factor)
        {
            if (_updating) return;
            _updating = true;
            try
            {
                bool working = bonusId == WorkingSpeedId;
                float old = working ? WorkingDelta : MovementDelta;
                if (old != 0f) _bonusManager.RemoveBonus(bonusId, old);
                float baseMultiplier = _bonusManager.Multiplier(bonusId);
                float delta = baseMultiplier * factor;
                if (Mathf.Abs(delta) < 1e-5f) delta = 0f;
                if (delta != 0f) _bonusManager.AddBonus(bonusId, delta);
                if (working) { WorkingDelta = delta; WorkingBase = baseMultiplier; }
                else { MovementDelta = delta; MovementBase = baseMultiplier; }
            }
            catch (Exception e)
            {
                Debug.LogError("[Pandaborn.Bell] updating the rested bonus failed: " + e);
            }
            finally
            {
                _updating = false;
            }
        }
    }
}
