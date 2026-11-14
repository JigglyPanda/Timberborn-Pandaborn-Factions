using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Globalization;
using System.Linq;
using Pandaborn.Core;
using Pandaborn.Specs;
using Timberborn.Beavers;
using Timberborn.BlueprintSystem;
using Timberborn.Localization;
using Timberborn.SingletonSystem;
using Timberborn.TemplateSystem;
using Timberborn.TimeSystem;
using Timberborn.WorkSystem;
using UnityEngine;

namespace Pandaborn.Bell
{
    /// <summary>
    /// The afternoon bell. The working-hours slider is vanilla; this service reads it at every dawn and "locks" that day's
    /// length, so moving the slider during the day changes nothing until the next morning (no toggling exploits). The
    /// locked length gives the rested bonus through PandabornBellSpec's curves. The game is a bell game when the
    /// faction's adult template carries PandabornBellSpec (only Inkpaws templates do), so no faction id is hard-coded.
    /// Saved state (Pandaborn store, feature "Bell", version 1): the locked hours and whether the suggestion was shown.
    /// </summary>
    public class BellService : ILoadableSingleton, IPostLoadableSingleton, IWorkdayClock
    {
        public const string StoreFeature = "Bell";
        private const int StoreVersion = 1;

        private readonly TemplateService _templateService;
        private readonly WorkingHoursManager _workingHoursManager;
        private readonly EventBus _eventBus;
        private readonly IDayNightCycle _dayNightCycle;
        private readonly PandabornStore _store;
        private readonly Messenger _messenger;
        private readonly ILoc _loc;

        private int _lockedHours = -1;
        private bool _suggested;

        public BellService(TemplateService templateService, WorkingHoursManager workingHoursManager, EventBus eventBus,
                           IDayNightCycle dayNightCycle, PandabornStore store, Messenger messenger, ILoc loc)
        {
            _templateService = templateService;
            _workingHoursManager = workingHoursManager;
            _eventBus = eventBus;
            _dayNightCycle = dayNightCycle;
            _store = store;
            _messenger = messenger;
            _loc = loc;
        }

        /// <summary>Raised when the locked day length (and so the bonus) changes.</summary>
        public event Action Changed;

        /// <summary>The service of the running game, for tests and other modules' optional integrations.</summary>
        public static BellService Current { get; private set; }

        public bool Active => Spec != null;

        public PandabornBellSpec Spec { get; private set; }

        /// <summary>The working day the bonus is based on: the slider as it stood at the last dawn.</summary>
        public int LockedHours => _lockedHours;

        // IWorkdayClock (Core): what other modules (Ringtails) read instead of finding this class by name.
        public bool HasLockedDay => Active && _lockedHours >= 0;

        public int LockedWorkdayHours => _lockedHours;

        /// <summary>The slider right now (whole hours, as the vanilla panel shows it).</summary>
        public int SliderHours => Mathf.CeilToInt(_workingHoursManager.WorkedPartOfDay * 24f - 0.001f);

        public float WorkingBonus => Active && _lockedHours >= 0 ? Curve(Spec.WorkingSpeedCurve, _lockedHours) : 0f;

        public float MovementBonus => Active && _lockedHours >= 0 ? Curve(Spec.MovementSpeedCurve, _lockedHours) : 0f;

        public float WorkingBonusAt(int hours) => Active ? Curve(Spec.WorkingSpeedCurve, hours) : 0f;

        public float MovementBonusAt(int hours) => Active ? Curve(Spec.MovementSpeedCurve, hours) : 0f;

        public bool Suggested => _suggested;

        public void Load()
        {
            Current = this;
            try
            {
                var adult = _templateService.GetAll<AdultSpec>().FirstOrDefault();
                Spec = adult?.Blueprint?.GetSpec<PandabornBellSpec>();
            }
            catch (Exception e)
            {
                Debug.LogError("[Pandaborn.Bell] reading the adult template failed; the bell is off: " + e);
                Spec = null;
            }
            if (!Active) return;
            if (_store.TryGet(StoreFeature, out int version, out string payload) && version == StoreVersion)
            {
                var values = Payload.Parse(payload);
                if (values.TryGetValue("locked", out var locked) && int.TryParse(locked, NumberStyles.Integer, CultureInfo.InvariantCulture, out int h)
                    && h >= 0 && h <= 24) _lockedHours = h;
                _suggested = values.TryGetValue("suggested", out var s) && s == "1";
            }
            // WorkingHoursManager (a dependency) has loaded, so the slider is known: lock now, before any colonist
            // applies its bonus (a new game, or a save made before the bell existed or with the module off).
            if (_lockedHours < 0) Lock(SliderHours, "start");
            _eventBus.Register(this);
        }

        public void PostLoad()
        {
            if (!Active) return;
            Debug.Log("[Pandaborn.Bell] active; working day locked at " + _lockedHours + " h: working +" + Pct(WorkingBonus) + ", walking +" + Pct(MovementBonus));
        }

        [OnEvent]
        public void OnDaytimeStart(DaytimeStartEvent e)
        {
            try
            {
                Lock(SliderHours, "dawn of day " + _dayNightCycle.DayNumber);
                if (!_suggested && Spec.SuggestionDay > 0 && _dayNightCycle.DayNumber >= Spec.SuggestionDay) Suggest("day " + _dayNightCycle.DayNumber);
            }
            catch (Exception ex) { Debug.LogError("[Pandaborn.Bell] dawn update failed: " + ex); }
        }

        /// <summary>Called by BellSettledMarker when a leisure building that marks a settled village is finished.</summary>
        public void OnSettledBuildingFinished(string what)
        {
            if (Active && !_suggested) Suggest(what);
        }

        /// <summary>Locks the bonus to a day length now. The game calls it at dawn; tests may call it to skip the wait.</summary>
        public void Lock(int hours, string why)
        {
            hours = Mathf.Clamp(hours, 0, 24);
            bool changed = hours != _lockedHours;
            _lockedHours = hours;
            Persist();
            if (!changed) return;
            Debug.Log("[Pandaborn.Bell] working day locked at " + hours + " h (" + why + "): working +" + Pct(WorkingBonus) + ", walking +" + Pct(MovementBonus));
            try { Changed?.Invoke(); }
            catch (Exception e) { Debug.LogError("[Pandaborn.Bell] applying the new bonus failed: " + e); }
        }

        private void Suggest(string why)
        {
            _suggested = true;
            Persist();
            string key = string.IsNullOrEmpty(Spec.SuggestionLocKey) ? "Pandaborn.Bell.Suggestion" : Spec.SuggestionLocKey;
            Debug.Log("[Pandaborn.Bell] suggestion posted (" + why + ")");
            _messenger.Post(_loc.T(key));
        }

        private void Persist()
        {
            _store.Set(StoreFeature, StoreVersion, Payload.Write(new[]
            {
                new KeyValuePair<string, string>("locked", _lockedHours.ToString(CultureInfo.InvariantCulture)),
                new KeyValuePair<string, string>("suggested", _suggested ? "1" : "0")
            }));
        }

        /// <summary>Piecewise-linear curve over hours, flat beyond its ends; an empty curve is 0.</summary>
        public static float Curve(ImmutableArray<PandabornBellPointSpec> points, float hours)
        {
            if (points.IsDefaultOrEmpty) return 0f;
            var sorted = points.OrderBy(p => p.Hours).ToList();
            if (hours <= sorted[0].Hours) return sorted[0].Bonus;
            for (int i = 1; i < sorted.Count; i++)
            {
                if (hours > sorted[i].Hours) continue;
                var a = sorted[i - 1];
                var b = sorted[i];
                float t = b.Hours > a.Hours ? (hours - a.Hours) / (b.Hours - a.Hours) : 1f;
                return a.Bonus + (b.Bonus - a.Bonus) * t;
            }
            return sorted[sorted.Count - 1].Bonus;
        }

        public static string Pct(float bonus) => Mathf.RoundToInt(bonus * 100f).ToString(CultureInfo.InvariantCulture) + "%";
    }
}
