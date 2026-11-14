using System;
using System.Linq;
using Timberborn.RootProviders;
using Timberborn.SingletonSystem;
using Timberborn.SoundSystem;
using UnityEngine;

namespace Pandaborn.Core
{
    /// <summary>
    /// Plays the mod's sounds (bundle pandabornsounds, ids "Environment.Pandaborn.*", docs/tech/sound.md) and never throws:
    /// the game throws "No sound files for: id" when an id has no clip (a platform without the bundle, an old copy), so
    /// every call checks first and returns false when silent. The mixer comes from the id's first segment, so the
    /// game's volume sliders apply. For the Bell's shift bell and the Ringtails' night clapper.
    /// </summary>
    public class PandabornSounds : ILoadableSingleton
    {
        private readonly ISoundSystem _soundSystem;
        private readonly AudioClipService _audioClipService;
        private readonly RootObjectProvider _rootObjectProvider;
        private GameObject _root;

        public PandabornSounds(ISoundSystem soundSystem, AudioClipService audioClipService, RootObjectProvider rootObjectProvider)
        {
            _soundSystem = soundSystem;
            _audioClipService = audioClipService;
            _rootObjectProvider = rootObjectProvider;
        }

        public void Load()
        {
            try { _root = _rootObjectProvider.CreateRootObject("PandabornSounds"); }
            catch (Exception e) { Debug.LogWarning("[Pandaborn] sound root not created; mod sounds are silent: " + e.Message); }
        }

        /// <summary>True when the sound id has at least one loaded clip.</summary>
        public bool Has(string id)
        {
            if (string.IsNullOrEmpty(id)) return false;
            try { return _audioClipService.GetAudioClipNames(id).Any(); }
            catch (Exception) { return false; }
        }

        /// <summary>Heard everywhere at full level.</summary>
        public bool Play2D(string id, int priority = 10)
        {
            if (!_root || !Has(id)) return false;
            try { _soundSystem.PlaySound2D(_root, id, priority); return true; }
            catch (Exception e) { Debug.LogWarning("[Pandaborn] sound " + id + " failed: " + e.Message); return false; }
        }

        /// <summary>From an object in the world (full level within about 2 units of the listener, silent beyond 10).</summary>
        public bool Play3D(GameObject emitter, string id, int priority = 30)
        {
            if (!emitter || !Has(id)) return false;
            try { _soundSystem.PlaySound3D(emitter, id, priority); return true; }
            catch (Exception e) { Debug.LogWarning("[Pandaborn] sound " + id + " failed: " + e.Message); return false; }
        }
    }
}