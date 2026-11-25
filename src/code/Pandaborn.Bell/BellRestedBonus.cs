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
    /// m (wellbeing tiers, need penalties, overburdening, workplace bonuses, other mods' bonuses), the result is
    /// m x (1 + b), not m + b. The game's bonuses only add (BonusManager keeps one sum per bonus id), so this component
    /// adds d = m x b and recomputes d whenever any other bonus of that id changes (BonusManager.BonusValueChanged), by
    /// taking its own share out, reading the multiplier, and putting d back (RestedShare). The result is exact unless m
    /// itself is clamped by the bonus type's limits, in which case the clamp decides either way. The order in which
    /// other bonuses arrive does not matter: d is recomputed from the sum as it stands after each change.
    ///
    /// Nothing is saved: bonuses are rebuilt on load by whoever adds them, so with the module off the colonist simply has
    /// vanilla speeds (ENGINEERING.md, code rule 5).
    /// </summary>
    public class BellRestedBonus : BaseComponent, IAwakableComponent, IPostInitializableEntity, IDeletableEntity
    {
        public const string WorkingSpeedId = "WorkingSpeed";
        public const string MovementSpeedId = "MovementSpeed";
        private const int MaxLoggedFailures = 3;
        private static int _loggedFailures;

        private readonly BellService _bellService;
        private readonly RestedShare _working = new RestedShare();
        private readonly RestedShare _movement = new RestedShare();
        private BonusManager _bonusManager;
        private Sum _workingSum;
        private Sum _movementSum;
        private bool _registered;
        private bool _updating;

        public BellRestedBonus(BellService bellService)
        {
            _bellService = bellService;
        }

        /// <summary>The additive share currently in the colonist's WorkingSpeed sum.</summary>
        public float WorkingDelta => _working.Delta;

        /// <summary>The additive share currently in the colonist's MovementSpeed sum.</summary>
        public float MovementDelta => _movement.Delta;

        /// <summary>WorkingSpeed multiplier without the bell, as last measured.</summary>
        public float WorkingBase => _working.Base;

        /// <summary>MovementSpeed multiplier without the bell, as last measured.</summary>
        public float MovementBase => _movement.Base;

        public float WorkingFactor => _bellService.WorkingBonus;

        public float MovementFactor => _bellService.MovementBonus;

        public bool IsActive => _registered;

        public void Awake()
        {
            _bonusManager = GetComponent<BonusManager>();
            if (_bonusManager == null) return;
            _workingSum = new Sum(_bonusManager, WorkingSpeedId);
            _movementSum = new Sum(_bonusManager, MovementSpeedId);
        }

        public void PostInitializeEntity()
        {
            if (_registered || !_bellService.Active || _bonusManager == null) return;
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
            Apply(_working, _workingSum, 0f);
            Apply(_movement, _movementSum, 0f);
        }

        /// <summary>Recomputes both shares (after a change of day length).</summary>
        public void Refresh()
        {
            if (!_registered) return;
            Apply(_working, _workingSum, _bellService.WorkingBonus);
            Apply(_movement, _movementSum, _bellService.MovementBonus);
        }

        private void OnBonusValueChanged(object sender, BonusValueChangedEventArgs e)
        {
            if (_updating || !_registered) return;
            if (e.BonusId == WorkingSpeedId) Apply(_working, _workingSum, _bellService.WorkingBonus);
            else if (e.BonusId == MovementSpeedId) Apply(_movement, _movementSum, _bellService.MovementBonus);
        }

        private void Apply(RestedShare share, Sum sum, float factor)
        {
            if (_updating) return;
            _updating = true;
            try
            {
                share.Apply(sum, factor);
            }
            catch (Exception e)
            {
                // our own change of the sum tells every listener of the colonist's bonuses; one of them threw
                if (_loggedFailures < MaxLoggedFailures)
                {
                    _loggedFailures++;
                    Debug.LogError("[Pandaborn.Bell] updating the rested bonus failed: " + e);
                }
            }
            finally
            {
                _updating = false;
            }
        }

        /// <summary>One bonus id of this colonist's BonusManager.</summary>
        private sealed class Sum : IBonusSum
        {
            private readonly BonusManager _bonusManager;
            private readonly string _bonusId;

            public Sum(BonusManager bonusManager, string bonusId)
            {
                _bonusManager = bonusManager;
                _bonusId = bonusId;
            }

            public float Multiplier() => _bonusManager.Multiplier(_bonusId);

            public void Add(float delta) => _bonusManager.AddBonus(_bonusId, delta);

            public void Remove(float delta) => _bonusManager.RemoveBonus(_bonusId, delta);
        }
    }
}
