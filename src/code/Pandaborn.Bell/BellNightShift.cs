using System;
using System.Collections.Generic;
using System.Linq;
using Pandaborn.Core;
using Pandaborn.Specs;
using Timberborn.BaseComponentSystem;
using Timberborn.Beavers;
using Timberborn.BonusSystem;
using Timberborn.EntitySystem;
using UnityEngine;

namespace Pandaborn.Bell
{
    /// <summary>
    /// The rested bonus of the night people (DESIGN.md 2026-11-25: "Ringtails get the rested bonus from the length of their
    /// own night shift, exactly as Inkpaws are by the length of their day"). One rule for both peoples: a twelve-hour shift
    /// is a rested shift. The bonus is the bell's own curves (PandabornBellSpec.WorkingSpeedCurve / MovementSpeedCurve,
    /// read from the data, never a constant here) looked up at the length of the night shift instead of the length of the
    /// working day, and it multiplies the colonist's whole multiplier the way BellRestedBonus does for Inkpaws.
    ///
    /// Where it lives, and why: here, in the Bell. The Bell owns the curve, the multiplying share, the walking-speed cap
    /// and the colonist line; all it needs from the other people is one number, the length of their shift, which it reads
    /// through Core's INightShiftClock (Pandaborn.Ringtails registers its clock there). Neither module names the other:
    ///  * Bell off: this component does not exist, Ringtails work at plain speed (the same as Inkpaws without the Bell).
    ///  * Ringtails off or degraded: no Ringtail exists (saved ones load as Inkpaws and get the Inkpaw bonus), and Core's
    ///    NoNightShiftClock says "no night shift", so nothing is added.
    /// It decorates PandabornRingtailSpec, a spec record of the always-loaded Pandaborn.Specs, which only the Ringtail
    /// templates of the Inkpaws faction carry: no other faction is touched. Kits get nothing, as Inkpaw cubs get nothing.
    ///
    /// The night clocks are held by a small singleton of their own (BellNightClocks) and not by BellService: the Ringtails'
    /// clock reads the Bell's locked day (IWorkdayClock), so BellService taking it in its constructor would close a circle.
    /// The shift length changes only when the Bell locks a new day (dawn), so the factors are worked out then and not at
    /// every change of the colonist's other bonuses.
    ///
    /// Nothing is saved, and nothing is left behind on unload: bonuses live in the colonist's BonusManager, which the
    /// game rebuilds on every load; the share is taken out when the colonist is deleted.
    /// </summary>
    public class BellNightRestedBonus : BaseComponent, IAwakableComponent, IPostInitializableEntity, IDeletableEntity
    {
        private const int MaxLoggedFailures = 3;
        private static int _loggedFailures;

        private readonly BellService _bellService;
        private readonly BellNightClocks _clocks;
        private readonly Share _working = new Share(BellRestedBonus.WorkingSpeedId);
        private readonly Share _movement = new Share(BellRestedBonus.MovementSpeedId);
        private BonusManager _bonusManager;
        private bool _kit;
        private bool _registered;
        private bool _updating;

        public BellNightRestedBonus(BellService bellService, BellNightClocks clocks)
        {
            _bellService = bellService;
            _clocks = clocks;
        }

        /// <summary>The night shift the bonus is based on, in hours (0 when there is none).</summary>
        public float ShiftHours { get; private set; }

        /// <summary>The bonus factors in force (0.33 = +33%).</summary>
        public float WorkingFactor { get; private set; }

        public float MovementFactor { get; private set; }

        /// <summary>The additive shares currently in the colonist's sums, and the multipliers without them.</summary>
        public float WorkingDelta => _working.Delta;

        public float MovementDelta => _movement.Delta;

        public float WorkingBase => _working.Base;

        public float MovementBase => _movement.Base;

        public bool IsActive => _registered;

        public void Awake()
        {
            _bonusManager = GetComponent<BonusManager>();
            _kit = GetComponent<Child>() != null;
        }

        public void PostInitializeEntity()
        {
            // an exception here would fail the creation (or the load) of the colonist: contain it
            try
            {
                if (_registered || _kit || !_bellService.Active || _bonusManager == null) return;
                _registered = true;
                _bellService.Changed += Refresh;
                _bonusManager.BonusValueChanged += OnBonusValueChanged;
                Refresh();
            }
            catch (Exception e) { Log(e); }
        }

        public void DeleteEntity()
        {
            if (!_registered) return;
            _registered = false;
            try
            {
                _bellService.Changed -= Refresh;
                _bonusManager.BonusValueChanged -= OnBonusValueChanged;
            }
            catch (Exception e) { Log(e); }
            Apply(_working, 0f);
            Apply(_movement, 0f);
        }

        /// <summary>Reads the shift length and the curve again (the Bell has locked a new day) and recomputes both shares.</summary>
        public void Refresh()
        {
            if (!_registered) return;
            try
            {
                float hours = _clocks.Hours;
                ShiftHours = hours;
                var spec = _bellService.Spec;
                bool on = hours > 0f && spec != null && _bellService.HasLockedDay;
                WorkingFactor = on ? Clean(BellService.Curve(spec.WorkingSpeedCurve, hours)) : 0f;
                MovementFactor = on ? Clean(BellService.Curve(spec.MovementSpeedCurve, hours)) : 0f;
            }
            catch (Exception e)
            {
                WorkingFactor = 0f;
                MovementFactor = 0f;
                Log(e);
            }
            Apply(_working, WorkingFactor);
            Apply(_movement, MovementFactor);
        }

        private static float Clean(float bonus) => float.IsNaN(bonus) || float.IsInfinity(bonus) ? 0f : bonus;

        private void OnBonusValueChanged(object sender, BonusValueChangedEventArgs e)
        {
            if (_updating || !_registered) return;
            if (e.BonusId == BellRestedBonus.WorkingSpeedId) Apply(_working, WorkingFactor);
            else if (e.BonusId == BellRestedBonus.MovementSpeedId) Apply(_movement, MovementFactor);
        }

        /// <summary>The share that makes the bonus multiply: with every other bonus summed into m it is m x factor, so the
        /// colonist ends at m x (1 + factor). The old share is taken out, m is read, the new share goes in. The share is
        /// written down before each call into the BonusManager (which tells its listeners, any of which may throw), so
        /// after an exception it still says what the sum holds.</summary>
        private void Apply(Share share, float factor)
        {
            if (_updating || _bonusManager == null) return;
            _updating = true;
            try
            {
                float old = share.Delta;
                if (old != 0f)
                {
                    share.Delta = 0f;
                    _bonusManager.RemoveBonus(share.BonusId, old);
                }
                float baseMultiplier = _bonusManager.Multiplier(share.BonusId);
                float delta = baseMultiplier * factor;
                if (float.IsNaN(delta) || float.IsInfinity(delta) || Mathf.Abs(delta) < 1e-5f) delta = 0f;
                share.Base = baseMultiplier;
                if (delta != 0f)
                {
                    share.Delta = delta;
                    _bonusManager.AddBonus(share.BonusId, delta);
                }
            }
            catch (Exception e) { Log(e); }
            finally { _updating = false; }
        }

        private static void Log(Exception e)
        {
            if (_loggedFailures >= MaxLoggedFailures) return;
            _loggedFailures++;
            Debug.LogError("[Pandaborn.Bell] updating a Ringtail's rested bonus failed: " + e);
        }

        private sealed class Share
        {
            public readonly string BonusId;
            public float Delta;
            public float Base = 1f;

            public Share(string bonusId)
            {
                BonusId = bonusId;
            }
        }
    }

    /// <summary>
    /// Every night-shift clock registered through Core (Pandaborn.Ringtails registers one; Core always registers the
    /// inactive NoNightShiftClock, so the list is never empty). A singleton, so the list is injected the way every other
    /// multi-bound list of the mod is; nothing of the Bell's own takes it in a constructor except the per-colonist bonus.
    /// </summary>
    public class BellNightClocks
    {
        private readonly INightShiftClock[] _clocks;

        public BellNightClocks(IEnumerable<INightShiftClock> clocks)
        {
            _clocks = clocks != null ? clocks.ToArray() : new INightShiftClock[0];
        }

        /// <summary>The length of the night shift from the first clock that has one; 0 when none does.</summary>
        public float Hours
        {
            get
            {
                for (int i = 0; i < _clocks.Length; i++)
                {
                    try
                    {
                        if (_clocks[i] == null || !_clocks[i].HasNightShift) continue;
                        float hours = _clocks[i].NightShiftHours;
                        return float.IsNaN(hours) || hours <= 0f ? 0f : Math.Min(hours, 24f);
                    }
                    catch (Exception) { }
                }
                return 0f;
            }
        }
    }

}
