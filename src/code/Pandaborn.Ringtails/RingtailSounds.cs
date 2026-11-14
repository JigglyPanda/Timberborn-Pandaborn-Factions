using System;
using System.Linq;
using Timberborn.GameDistricts;
using Timberborn.RootProviders;
using Timberborn.SingletonSystem;
using Timberborn.SoundSystem;
using UnityEngine;

namespace Pandaborn.Ringtails
{
    /// <summary>
    /// The Ringtails' sounds (docs/tech/sound.md section 8). The night clapper plays once when the Ringtail shift starts, only
    /// in a village that has Ringtails; when the shift starts at the bell it answers the bell about 2.5 s after the strike.
    /// The red panda twitter plays at a Moon Loft when the family arrives. Silent, never throwing, when the clip is missing
    /// (the game throws "No sound files for: id" for an id without a clip, so every call checks first).
    /// </summary>
    public class RingtailSounds : ILoadableSingleton, IUpdatableSingleton
    {
        public const string NightClapper = "Environment.Pandaborn.NightClapper";
        public const string RingtailTwitter = "Environment.Pandaborn.RingtailTwitter";
        private const float AnswerDelaySeconds = 2.5f;

        private readonly ISoundSystem _soundSystem;
        private readonly AudioClipService _audioClipService;
        private readonly RootObjectProvider _rootObjectProvider;
        private readonly RingtailService _ringtailService;
        private readonly RingtailWorkday _workday;
        private readonly DistrictCenterRegistry _districtCenterRegistry;
        private GameObject _root;
        private float _lastHour = -1f;
        private float _playAt = -1f;

        public RingtailSounds(ISoundSystem soundSystem, AudioClipService audioClipService, RootObjectProvider rootObjectProvider,
                              RingtailService ringtailService, RingtailWorkday workday, DistrictCenterRegistry districtCenterRegistry)
        {
            _soundSystem = soundSystem;
            _audioClipService = audioClipService;
            _rootObjectProvider = rootObjectProvider;
            _ringtailService = ringtailService;
            _workday = workday;
            _districtCenterRegistry = districtCenterRegistry;
        }

        /// <summary>What happened to the last clapper (tests): "played", "no clip", "no Ringtails".</summary>
        public static string LastClapper { get; private set; }

        public static int ClappersPlayed { get; private set; }

        public void Load()
        {
            if (!_ringtailService.Enabled) return;
            _ringtailService.FamilyArrived += loft => PlayAt(loft.GameObject, RingtailTwitter);
            try { _root = _rootObjectProvider.CreateRootObject("PandabornRingtailSounds"); }
            catch (Exception e) { Debug.LogWarning("[Pandaborn.Ringtails] no sound root: " + e.Message); }
        }

        public bool Has(string id)
        {
            try { return _audioClipService.GetAudioClipNames(id).Any(); }
            catch (Exception) { return false; }
        }

        public void PlayAt(GameObject emitter, string id)
        {
            try { if (emitter && Has(id)) _soundSystem.PlaySound3D(emitter, id, 30); }
            catch (Exception e) { Debug.LogWarning("[Pandaborn.Ringtails] sound " + id + " failed: " + e.Message); }
        }

        public void UpdateSingleton()
        {
            if (!_ringtailService.Enabled || !_root) return;
            float hour = _workday.HoursSinceDawn;
            float start = _workday.ShiftStartHours;
            if (_lastHour >= 0f && _lastHour < start && hour >= start && hour - _lastHour < 2f)
            {
                bool atBell = Mathf.Abs(start - _workday.WorkdayHours) < 0.01f;
                _playAt = Time.unscaledTime + (atBell ? AnswerDelaySeconds : 0f);
            }
            _lastHour = hour;
            if (_playAt < 0f || Time.unscaledTime < _playAt) return;
            _playAt = -1f;
            if (RingtailsPopulationRow.Count(_districtCenterRegistry.FinishedDistrictCenters).Total == 0) { LastClapper = "no Ringtails"; return; }
            if (!Has(NightClapper)) { LastClapper = "no clip"; return; }
            try
            {
                _soundSystem.PlaySound2D(_root, NightClapper, 10);
                ClappersPlayed++;
                LastClapper = "played";
            }
            catch (Exception e)
            {
                LastClapper = "failed: " + e.Message;
                Debug.LogWarning("[Pandaborn.Ringtails] clapper failed: " + e.Message);
            }
        }
    }
}
