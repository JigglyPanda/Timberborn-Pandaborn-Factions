using System;
using System.Linq;
using Timberborn.SoundSystem;
using UnityEngine;

namespace Pandaborn.Festival
{
    /// <summary>
    /// The festival's sounds from the sound lane's bundle (docs/tech/sound.md 8): firecrackers when the festival begins and
    /// as the gathering starts, a drum loop at each square through the show. Played through the game's own sound system; a
    /// clip that is not loaded (no bundle) is simply silent. Never throws.
    /// </summary>
    public class FestivalSounds
    {
        public const string Drum = "Environment.Pandaborn.FestivalDrum";
        public const string Firecrackers = "Environment.Pandaborn.Firecrackers";

        private readonly ISoundSystem _soundSystem;
        private readonly AudioClipService _audioClipService;
        private GameObject _root;

        public FestivalSounds(ISoundSystem soundSystem, AudioClipService audioClipService)
        {
            _soundSystem = soundSystem;
            _audioClipService = audioClipService;
        }

        /// <summary>Sounds played in this session (tests).</summary>
        public static int Played { get; private set; }

        public bool Has(string id)
        {
            try { return _audioClipService.GetAudioClipNames(id).Any(); }
            catch (Exception) { return false; }
        }

        public void Play2D(string id)
        {
            if (!Has(id)) return;
            try
            {
                if (!_root) _root = new GameObject("PandabornFestivalSounds");
                _soundSystem.PlaySound2D(_root, id, 10);
                Played++;
            }
            catch (Exception e) { Debug.LogWarning("[Pandaborn.Festival] sound " + id + " failed: " + e.Message); }
        }

        public void Play3D(GameObject emitter, string id)
        {
            if (!emitter || !Has(id)) return;
            try { _soundSystem.PlaySound3D(emitter, id, 30); Played++; }
            catch (Exception e) { Debug.LogWarning("[Pandaborn.Festival] sound " + id + " failed: " + e.Message); }
        }

        public void Loop(GameObject emitter, string id, bool on)
        {
            if (!emitter || !Has(id)) return;
            try
            {
                if (on) { _soundSystem.LoopSingle3DSound(emitter, id, 30); Played++; }
                else _soundSystem.StopSound(emitter, id);
            }
            catch (Exception e) { Debug.LogWarning("[Pandaborn.Festival] sound " + id + " failed: " + e.Message); }
        }
    }
}
