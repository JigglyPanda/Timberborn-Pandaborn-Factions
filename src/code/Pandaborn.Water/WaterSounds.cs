using System;
using System.Collections.Generic;
using Pandaborn.Core;
using Timberborn.CoreSound;
using Timberborn.RootProviders;
using Timberborn.SingletonSystem;
using Timberborn.SoundSystem;
using UnityEngine;

namespace Pandaborn.Water
{
    /// <summary>
    /// The flume's sound is its status (docs/tech/sound.md §8): one area sound for every flume, heard only near tiles where
    /// water is flowing along a run (a dry or standing run is quiet), and a bamboo "tok" when water first reaches the end
    /// of a run (once per run per fill, and about once every 20 real seconds game-wide). The flowing tiles are reported by
    /// each piece's FlumeMonitor. Silent when the clips are missing (PandabornSounds.Has); never throws.
    /// </summary>
    public class WaterSounds : ILoadableSingleton, IEmitterMap
    {
        public const string FlumeWater = "Environment.Pandaborn.FlumeWater";
        public const string BambooTok = "Environment.Pandaborn.BambooTok";
        private const float TokIntervalSeconds = 20f;

        private readonly PandabornSounds _sounds;
        private readonly ISoundSystem _soundSystem;
        private readonly RootObjectProvider _rootObjectProvider;
        // counted: a Bridge span and the flume under it share a tile, and one going quiet must not silence the other
        private readonly Dictionary<Vector2Int, int> _flowing = new Dictionary<Vector2Int, int>();
        private float _lastTok = -1000f;

        public WaterSounds(PandabornSounds sounds, ISoundSystem soundSystem, RootObjectProvider rootObjectProvider)
        {
            _sounds = sounds;
            _soundSystem = soundSystem;
            _rootObjectProvider = rootObjectProvider;
        }

        /// <summary>True once the flume loop is playing (for tests).</summary>
        public static bool AreaSoundActive { get; private set; }

        /// <summary>Tiles with flowing flume water right now (for tests).</summary>
        public int FlowingTiles => _flowing.Count;

        /// <summary>Toks played this session (for tests).</summary>
        public static int Toks { get; private set; }

        public void Load()
        {
            AreaSoundActive = false;
            Toks = 0;
            if (!_sounds.Has(FlumeWater)) return;
            try
            {
                var parent = _rootObjectProvider.CreateRootObject("PandabornFlumeSound").transform;
                _soundSystem.AddLargeAreaSound(parent, this, FlumeWater, 50, 10, MixerNames.BuildingMixerNameKey);
                AreaSoundActive = true;
            }
            catch (Exception e)
            {
                Debug.LogWarning("[Pandaborn] flume sound not started; flumes are silent: " + e.Message);
            }
        }

        public bool IsEmitterAt(Vector2Int coordinates) => _flowing.ContainsKey(coordinates);

        internal void SetFlowing(Vector2Int tile, bool flowing)
        {
            _flowing.TryGetValue(tile, out int pieces);
            pieces += flowing ? 1 : -1;
            if (pieces > 0) _flowing[tile] = pieces;
            else _flowing.Remove(tile);
        }

        /// <summary>The tok from a piece's child object (a selected building's own object carries the UI mixer).</summary>
        internal void Tok(GameObject emitter)
        {
            if (Time.unscaledTime - _lastTok < TokIntervalSeconds) return;
            if (_sounds.Play3D(emitter, BambooTok))
            {
                _lastTok = Time.unscaledTime;
                Toks++;
            }
        }
    }
}
