using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Globalization;
using System.Linq;
using Pandaborn.Core;
using Pandaborn.Specs;
using Timberborn.Beavers;
using Timberborn.BlueprintSystem;
using Timberborn.BonusSystem;
using Timberborn.GameDistricts;
using Timberborn.GameFactionSystem;
using Timberborn.Localization;
using Timberborn.SingletonSystem;
using Timberborn.TemplateSystem;
using Timberborn.TimeSystem;
using Timberborn.UILayoutSystem;
using Timberborn.WeatherSystem;
using Timberborn.WorkSystem;
using UnityEngine;

namespace Pandaborn.Bell
{
    /// <summary>
    /// The afternoon bell. The working-hours slider is vanilla; this service reads it at every dawn and "locks" that day's
    /// length, so moving the slider during the day changes nothing until the next morning (no toggling exploits). The
    /// locked length gives the rested bonus through PandabornBellSpec's curves. The game is a bell game when the
    /// faction's adult template carries PandabornBellSpec (only Inkpaws templates do), so no faction id is hard-coded.
    /// Saved state (Pandaborn store, feature "Bell", version 1): the locked hours, whether the village counts as settled and
    /// whether the suggestion was shown.
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
        private readonly FactionService _factionService;
        private readonly WeatherService _weatherService;
        private readonly PandabornSounds _sounds;
        private readonly DistrictCenterRegistry _districtCenterRegistry;
        private readonly BonusTypeSpecService _bonusTypeSpecService;

        private const int KeptRings = 64;
        private int _lockedHours = -1;
        private float _workingBonus;
        private float _movementBonus;
        private float[] _workingHours, _workingBonuses, _movementHours, _movementBonuses;
        private int _ceilingHours = -1;
        private bool _suggested;
        private bool _settled;
        private bool _interfaceShown;
        private int _ringDay = -1;
        private int _ringsToday;

        /// <summary>The last bell ring attempts of this session (day, sound id, played), for tests.</summary>
        public static readonly List<string> Rings = new List<string>();

        public BellService(TemplateService templateService, WorkingHoursManager workingHoursManager, EventBus eventBus,
                           IDayNightCycle dayNightCycle, PandabornStore store, Messenger messenger, ILoc loc, FactionService factionService,
                           WeatherService weatherService, PandabornSounds sounds, DistrictCenterRegistry districtCenterRegistry,
                           BonusTypeSpecService bonusTypeSpecService)
        {
            _factionService = factionService;
            _weatherService = weatherService;
            _sounds = sounds;
            _districtCenterRegistry = districtCenterRegistry;
            _bonusTypeSpecService = bonusTypeSpecService;
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

        /// <summary>Today's bonuses, worked out once when the day is locked (every colonist reads them at each change of
        /// its own bonuses).</summary>
        public float WorkingBonus => Active && _lockedHours >= 0 ? _workingBonus : 0f;

        public float MovementBonus => Active && _lockedHours >= 0 ? _movementBonus : 0f;

        public float WorkingBonusAt(int hours) => Active ? BellCurve.At(_workingHours, _workingBonuses, hours) : 0f;

        public float MovementBonusAt(int hours) => Active ? BellCurve.At(_movementHours, _movementBonuses, hours) : 0f;

        /// <summary>The longest working day (whole hours) that still gives the largest working bonus: shortening the day
        /// further gains nothing. From the curve, never a constant; -1 when the curve gives no bonus at all.</summary>
        public int CeilingHours => Active ? _ceilingHours : -1;

        /// <summary>CeilingHours for a text; the slider's hours when the curve gives no bonus (the text then names the day
        /// the village already works).</summary>
        public string CeilingHoursText => (CeilingHours >= 0 ? CeilingHours : SliderHours).ToString(CultureInfo.InvariantCulture);

        private const string SuggestionKey = "Pandaborn.Bell.Suggestion.WithHour";
        private const string OldSuggestionKey = "Pandaborn.Bell.Suggestion";

        public bool Suggested => _suggested;

        public bool Settled => _settled;

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
            if (!Active)
            {
                // shipped but not switched on by data: say so in the feature report (only in games of our faction)
                if (_factionService.Current?.Id == FeatureNotices.FactionId)
                    FeatureRegistry.ReportNoData("Bell", "the faction's adult template has no PandabornBellSpec");
                return;
            }
            Points(Spec.WorkingSpeedCurve, out _workingHours, out _workingBonuses);
            Points(Spec.MovementSpeedCurve, out _movementHours, out _movementBonuses);
            _ceilingHours = BellCurve.CeilingHours(_workingHours, _workingBonuses);
            CheckWalkingCap();
            try
            {
                if (_store.TryGet(StoreFeature, out int version, out string payload) && version == StoreVersion)
                {
                    var values = Payload.Parse(payload);
                    if (values.TryGetValue("locked", out var locked) && int.TryParse(locked, NumberStyles.Integer, CultureInfo.InvariantCulture, out int h)
                        && h >= 0 && h <= 24) _lockedHours = h;
                    _suggested = values.TryGetValue("suggested", out var s) && s == "1";
                    _settled = values.TryGetValue("settled", out var st) && st == "1";
                }
            }
            catch (Exception e) { Debug.LogWarning("[Pandaborn.Bell] saved bell state unreadable; starting fresh: " + e.Message); }
            Recompute();
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

        /// <summary>A leisure building found finished while a save loads settles the village before there is an interface
        /// to show a message in; the suggestion is posted once the interface is there.</summary>
        [OnEvent]
        public void OnShowPrimaryUI(ShowPrimaryUIEvent e)
        {
            _interfaceShown = true;
            try { TrySuggest("the interface is shown"); }
            catch (Exception ex) { Debug.LogError("[Pandaborn.Bell] suggestion failed: " + ex); }
        }

        [OnEvent]
        public void OnDaytimeStart(DaytimeStartEvent e)
        {
            try
            {
                Lock(SliderHours, "dawn of day " + _dayNightCycle.DayNumber);
                if (!_settled && Spec.SuggestionDay > 0 && _dayNightCycle.DayNumber >= Spec.SuggestionDay)
                {
                    _settled = true;
                    Persist();
                }
                TrySuggest("dawn of day " + _dayNightCycle.DayNumber);
            }
            catch (Exception ex) { Debug.LogError("[Pandaborn.Bell] dawn update failed: " + ex); }
        }

        /// <summary>Called by BellSettledMarker when a leisure building that marks a settled village is finished (also when
        /// one is loaded already finished). The village counts as settled from then on; the suggestion follows as soon as
        /// the day and the weather allow.</summary>
        public void OnSettledBuildingFinished(string what)
        {
            if (!Active || _settled) return;
            try
            {
                _settled = true;
                Persist();
                Debug.Log("[Pandaborn.Bell] village settled (" + what + ")");
                TrySuggest(what);
            }
            catch (Exception ex) { Debug.LogError("[Pandaborn.Bell] settling the village failed: " + ex); }
        }

        /// <summary>The one-time suggestion, once per settlement: only when the village is settled (a Hammock or Teahouse
        /// finished, or the dawn of SuggestionDay), never before the dawn of SuggestionMinimumDay, never during a drought or
        /// badtide (it waits for the next dawn).</summary>
        private void TrySuggest(string why)
        {
            if (!Active || _suggested || !_settled) return;
            if (!_interfaceShown) return;       // still loading: tried again when the interface appears
            int day = _dayNightCycle.DayNumber;
            if (day < Math.Max(1, Spec.SuggestionMinimumDay)) { Debug.Log("[Pandaborn.Bell] suggestion waits: day " + day + " < " + Spec.SuggestionMinimumDay); return; }
            bool hazard;
            try { hazard = _weatherService.IsHazardousWeather; }
            catch (Exception) { hazard = false; }
            if (hazard) { Debug.Log("[Pandaborn.Bell] suggestion waits: hazardous weather"); return; }
            Suggest(why);
        }

        /// <summary>The shift bell: heard everywhere (2D; a 3D sound is silent ten units from the camera, and this is the day's
        /// signal, not a building's noise), rung only once a Village Hall stands, when the Inkpaw working day
        /// ends and when it starts, at most twice a game day, silent when the clip is not loaded.</summary>
        [OnEvent]
        public void OnWorkingHoursTransitioned(WorkingHoursTransitionedEvent e)
        {
            try
            {
                int day = _dayNightCycle.DayNumber;
                if (day != _ringDay) { _ringDay = day; _ringsToday = 0; }
                if (_ringsToday >= 2) return;
                _ringsToday++;
                string id = _workingHoursManager.AreWorkingHours ? Spec.DawnBellSoundId : Spec.EndBellSoundId;
                if (string.IsNullOrEmpty(id)) return;
                var hall = _districtCenterRegistry.FinishedDistrictCenters.FirstOrDefault();
                bool played = hall != null && _sounds.Play2D(id);
                Rings.Add("day " + day + " " + id + (played ? " played" : hall == null ? " silent (no village hall)" : " silent (no clip)"));
                if (Rings.Count > KeptRings) Rings.RemoveAt(0);
            }
            catch (Exception ex) { Debug.LogWarning("[Pandaborn.Bell] bell sound failed: " + ex.Message); }
        }

        /// <summary>The walking half of the bonus needs the Inkpaws-only MovementSpeed cap modifier (vanilla caps at 2.0).</summary>
        private void CheckWalkingCap()
        {
            try
            {
                float max = _bonusTypeSpecService.GetSpec("MovementSpeed").MaximumValue;
                float best = _movementBonuses.Length == 0 ? 0f : _movementBonuses.Max();
                if (best > 0f && max < 2f * (1f + best) - 0.01f)
                    FeatureRegistry.ReportDegradedInGame("Bell", "walking-speed cap " + max.ToString("0.##", CultureInfo.InvariantCulture)
                        + ": the faction's BonusType.MovementSpeed modifier is missing, so happy Inkpaws lose part of the walking bonus");
            }
            catch (Exception e) { Debug.LogWarning("[Pandaborn.Bell] walking-cap check failed: " + e.Message); }
        }

        /// <summary>Locks the bonus to a day length now. The game calls it at dawn; tests may call it to skip the wait.</summary>
        public void Lock(int hours, string why)
        {
            hours = Mathf.Clamp(hours, 0, 24);
            bool changed = hours != _lockedHours;
            _lockedHours = hours;
            Recompute();
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
            // The text names the hour at which the bonus is full, so the key is the one that takes it. The data's key from
            // before the hour was a parameter ("Pandaborn.Bell.Suggestion") means the same text.
            string key = string.IsNullOrEmpty(Spec.SuggestionLocKey) || Spec.SuggestionLocKey == OldSuggestionKey ? SuggestionKey : Spec.SuggestionLocKey;
            Debug.Log("[Pandaborn.Bell] suggestion posted (" + why + ")");
            // {0} = the longest working day, in whole hours, at which the bonus is full (from the curve)
            _messenger.Post(_loc.T(key, CeilingHoursText));
        }

        private void Persist()
        {
            _store.Set(StoreFeature, StoreVersion, Payload.Write(new[]
            {
                new KeyValuePair<string, string>("locked", _lockedHours.ToString(CultureInfo.InvariantCulture)),
                new KeyValuePair<string, string>("suggested", _suggested ? "1" : "0"),
                new KeyValuePair<string, string>("settled", _settled ? "1" : "0")
            }));
        }

        private void Recompute()
        {
            _workingBonus = _lockedHours >= 0 ? BellCurve.At(_workingHours, _workingBonuses, _lockedHours) : 0f;
            _movementBonus = _lockedHours >= 0 ? BellCurve.At(_movementHours, _movementBonuses, _lockedHours) : 0f;
        }

        /// <summary>Piecewise-linear curve over hours, flat beyond its ends; an empty curve is 0 (BellCurve.At).</summary>
        public static float Curve(ImmutableArray<PandabornBellPointSpec> points, float hours)
        {
            Points(points, out var h, out var b);
            return BellCurve.At(h, b, hours);
        }

        /// <summary>The curve's points as two arrays; a missing curve or a null point gives none.</summary>
        private static void Points(ImmutableArray<PandabornBellPointSpec> points, out float[] hours, out float[] bonuses)
        {
            var valid = points.IsDefaultOrEmpty ? new List<PandabornBellPointSpec>() : points.Where(p => p != null).ToList();
            hours = valid.Select(p => p.Hours).ToArray();
            bonuses = valid.Select(p => p.Bonus).ToArray();
        }

        public static string Pct(float bonus) => Mathf.RoundToInt(bonus * 100f).ToString(CultureInfo.InvariantCulture) + "%";
    }
}
