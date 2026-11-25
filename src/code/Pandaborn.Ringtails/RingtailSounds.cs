using System;
using Pandaborn.Core;
using Timberborn.BaseComponentSystem;
using Timberborn.Characters;
using Timberborn.GameDistricts;
using Timberborn.RootProviders;
using Timberborn.SelectionSystem;
using Timberborn.SingletonSystem;
using UnityEngine;

namespace Pandaborn.Ringtails
{
    /// <summary>
    /// The Ringtails' sounds (docs/tech/sound.md section 8), all through Core's PandabornSounds, which checks that the clip
    /// is loaded and never throws (the game throws "No sound files for: id" for an id without a clip).
    /// The night clapper plays once when the Ringtail shift starts, only in a village that has Ringtails; when the shift
    /// starts at the bell it answers the bell about 2.5 s after the strike. The red panda twitter plays at a Moon Loft when
    /// a family arrives, and (<see cref="RingtailVoice"/>) when a Ringtail is selected.
    /// </summary>
    public class RingtailSounds : ILoadableSingleton, IUpdatableSingleton
    {
        public const string NightClapper = "Environment.Pandaborn.NightClapper";
        public const string RingtailTwitter = "Environment.Pandaborn.RingtailTwitter";
        private const float AnswerDelaySeconds = 2.5f;
        private const float TwitterIntervalSeconds = 1.5f;

        private readonly PandabornSounds _sounds;
        private readonly RingtailService _ringtailService;
        private readonly RingtailWorkday _workday;
        private readonly DistrictCenterRegistry _districtCenterRegistry;
        private readonly RootObjectProvider _rootObjectProvider;
        private GameObject _emitter;
        private float _lastHour = -1f;
        private float _playAt = -1f;
        private float _lastTwitter = -1000f;
        private bool _clapperFailed;

        public RingtailSounds(PandabornSounds sounds, RingtailService ringtailService, RingtailWorkday workday,
                              DistrictCenterRegistry districtCenterRegistry, RootObjectProvider rootObjectProvider)
        {
            _sounds = sounds;
            _ringtailService = ringtailService;
            _workday = workday;
            _districtCenterRegistry = districtCenterRegistry;
            _rootObjectProvider = rootObjectProvider;
        }

        /// <summary>What happened to the last clapper (tests): "played", "no clip", "no Ringtails".</summary>
        public static string LastClapper { get; private set; }

        public static int ClappersPlayed { get; private set; }

        /// <summary>Twitters played this session (tests).</summary>
        public static int TwittersPlayed { get; private set; }

        public void Load()
        {
            LastClapper = null;
            ClappersPlayed = 0;
            TwittersPlayed = 0;
            // the event only fires in a game where the feature is on
            _ringtailService.FamilyArrived += loft => Twitter(loft);
        }

        public bool Has(string id) => _sounds.Has(id);

        /// <summary>The twitter, heard at the place of <paramref name="at"/>, at most once every second and a half. It plays
        /// from this module's own object moved there, not from the entity: a selected entity's own object carries the UI
        /// mixer (sound.md section 8), and nothing is added to a colonist's or a building's object tree. Silent, never
        /// throwing, when the clip is missing.</summary>
        public void Twitter(BaseComponent at)
        {
            try
            {
                if (!at || Time.unscaledTime - _lastTwitter < TwitterIntervalSeconds || !_sounds.Has(RingtailTwitter)) return;
                if (!_emitter) _emitter = _rootObjectProvider.CreateRootObject("PandabornRingtailVoice");
                _emitter.transform.position = at.Transform.position + new Vector3(0f, 0.5f, 0f);
                if (!_sounds.Play3D(_emitter, RingtailTwitter)) return;
                _lastTwitter = Time.unscaledTime;
                TwittersPlayed++;
            }
            catch (Exception e) { Debug.LogWarning("[Pandaborn.Ringtails] twitter failed: " + e.Message); }
        }

        public void UpdateSingleton()
        {
            if (_clapperFailed || !_ringtailService.Enabled || !_ringtailService.Arrived) return;
            try
            {
                float hour = _workday.HoursSinceDawn;
                float start = _workday.ShiftStartHours;
                if (ShiftMath.CrossedShiftStart(_lastHour, hour, start))
                {
                    bool atBell = Mathf.Abs(start - _workday.WorkdayHours) < 0.01f;
                    _playAt = Time.unscaledTime + (atBell ? AnswerDelaySeconds : 0f);
                }
                _lastHour = hour;
                if (_playAt < 0f || Time.unscaledTime < _playAt) return;
                _playAt = -1f;
                if (RingtailsPopulationRow.Count(_districtCenterRegistry.FinishedDistrictCenters).Total == 0) { LastClapper = "no Ringtails"; return; }
                if (!_sounds.Has(NightClapper)) { LastClapper = "no clip"; return; }
                if (_sounds.Play2D(NightClapper))
                {
                    ClappersPlayed++;
                    LastClapper = "played";
                }
                else LastClapper = "failed";
            }
            catch (Exception e)
            {
                _clapperFailed = true;   // per frame: never twice
                LastClapper = "failed: " + e.Message;
                Debug.LogWarning("[Pandaborn.Ringtails] clapper failed and is off for this session: " + e.Message);
            }
        }
    }

    /// <summary>
    /// A Ringtail's own voice: the red panda twitter when it is selected (the faction's colonist call still plays under
    /// it: that one is vanilla's, chosen by faction, and cannot be told apart by kind without patching). On every
    /// Ringtail template (PandabornRingtailSpec).
    /// </summary>
    public class RingtailVoice : BaseComponent, ISelectionListener
    {
        private readonly RingtailSounds _sounds;
        private readonly RingtailService _ringtailService;

        public RingtailVoice(RingtailSounds sounds, RingtailService ringtailService)
        {
            _sounds = sounds;
            _ringtailService = ringtailService;
        }

        public void OnSelect()
        {
            // called from the game's selection code: never let anything out
            try
            {
                if (!_ringtailService.Enabled) return;
                var character = GetComponent<Character>();
                if (character != null && !character.Alive) return;
                _sounds.Twitter(this);
            }
            catch (Exception) { }

        }

        public void OnUnselect() { }
    }
}
