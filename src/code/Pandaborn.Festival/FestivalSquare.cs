using System;
using Timberborn.BaseComponentSystem;
using Timberborn.BlockSystem;
using Timberborn.EntitySystem;
using Timberborn.GameDistricts;
using UnityEngine;

namespace Pandaborn.Festival
{
    /// <summary>
    /// The Festival Square (decorates PandabornFestivalSquareSpec). Registers the finished square with the festival, launches
    /// its lanterns and fireworks, and drives the art lane's named hooks on its model when they exist:
    ///   #FestivalLights  shown from the call until the festival ends, hidden otherwise (lantern strings, lit stalls);
    ///   #LanternRise     a particle system played at each lantern launch (replaces the comet firework when present);
    ///   #FireworkMount   the launch point (default: the square's centre, 1.5 above the ground).
    /// Without the module the building is its vanilla basis and the nodes keep their authored state.
    /// </summary>
    public class FestivalSquare : BaseComponent, IAwakableComponent, IFinishedStateListener, IDeletableEntity
    {
        private const string LightsNode = "#FestivalLights";
        private const string LanternRiseNode = "#LanternRise";
        private const string MountNode = "#FireworkMount";

        private readonly FestivalService _festivalService;
        private DistrictBuilding _districtBuilding;
        private BlockObjectCenter _center;
        private Transform _lights;
        private ParticleSystem _lanternRise;
        private Transform _mount;
        private bool _nodesSearched;
        private readonly System.Random _random = new System.Random();

        public FestivalSquare(FestivalService festivalService)
        {
            _festivalService = festivalService;
        }

        public bool IsFinished { get; private set; }

        public DistrictCenter District => _districtBuilding ? _districtBuilding.District : null;

        public Vector3 Center => _center ? _center.WorldCenterGrounded : Transform.position;

        public void Awake()
        {
            _districtBuilding = GetComponent<DistrictBuilding>();
            _center = GetComponent<BlockObjectCenter>();
        }

        public void OnEnterFinishedState()
        {
            IsFinished = true;
            if (!_festivalService.Active) return;
            _festivalService.AddSquare(this);
            UpdateLights();
        }

        public void OnExitFinishedState()
        {
            IsFinished = false;
            _festivalService.RemoveSquare(this);
        }

        public void DeleteEntity()
        {
            IsFinished = false;
            _festivalService.RemoveSquare(this);
        }

        /// <summary>Shows the festival lights from the call to the end of the festival.</summary>
        public void UpdateLights()
        {
            try
            {
                FindNodes();
                if (_lights) _lights.gameObject.SetActive(_festivalService.Phase != FestivalPhase.None);
            }
            catch (Exception e) { Debug.LogError("[Pandaborn.Festival] festival lights failed: " + e.Message); }
        }

        private GameObject _soundEmitter;

        /// <summary>A child object of the square for the festival's sounds. The building's own sound system loops its sound
        /// on the square's object when visitors enter, and a sound emitter loops only one sound at a time (it throws on a
        /// second), so the festival never plays on the building's own object.</summary>
        public GameObject SoundEmitter
        {
            get
            {
                if (!_soundEmitter)
                {
                    _soundEmitter = new GameObject("PandabornFestivalSounds");
                    _soundEmitter.transform.SetParent(Transform, false);
                    _soundEmitter.transform.position = Center + Vector3.up * 1.5f;
                }
                return _soundEmitter;
            }
        }

        internal bool Launch(FestivalFireworks fireworks, string fireworkId, bool lantern)
        {
            FindNodes();
            if (lantern && _lanternRise)
            {
                _lanternRise.Play();
                return true;
            }
            var origin = _mount ? _mount.position : Center + Vector3.up * 1.5f;
            var offset = new Vector3((float)(_random.NextDouble() - 0.5) * 2.5f, 0f, (float)(_random.NextDouble() - 0.5) * 2.5f);
            float pitch = (float)(_random.NextDouble() - 0.5) * (lantern ? 16f : 30f);
            float heading = (float)_random.NextDouble() * 360f;
            float distance = lantern ? 14f + (float)_random.NextDouble() * 10f : 22f + (float)_random.NextDouble() * 14f;
            return fireworks.Launch(fireworkId, origin + offset, pitch, heading, distance);
        }

        private void FindNodes()
        {
            if (_nodesSearched) return;
            _nodesSearched = true;
            foreach (var t in GameObject.GetComponentsInChildren<Transform>(true))
            {
                if (t.name == LightsNode) _lights = t;
                else if (t.name == LanternRiseNode) _lanternRise = t.GetComponentInChildren<ParticleSystem>(true);
                else if (t.name == MountNode) _mount = t;
            }
        }
    }
}
