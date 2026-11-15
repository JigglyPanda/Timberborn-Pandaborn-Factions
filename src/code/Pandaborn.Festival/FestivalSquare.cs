using System;
using Timberborn.Attractions;
using Timberborn.BaseComponentSystem;
using Timberborn.EnterableSystem;
using Timberborn.BlockSystem;
using Timberborn.EntitySystem;
using Timberborn.GameDistricts;
using Timberborn.TemplateAttachmentSystem;
using UnityEngine;

namespace Pandaborn.Festival
{
    /// <summary>
    /// The Festival Square (decorates PandabornFestivalSquareSpec). Registers the finished square with the festival, launches
    /// its lanterns and fireworks, and drives the art lane's named hooks on its model when they exist:
    ///   #FestivalLights  shown from the call until the festival ends, hidden otherwise (lantern strings, lit stalls);
    ///   LanternRise      a template attachment (TemplateAttachmentsSpec, parent #LanternRise) whose ParticleSystem is
    ///                    played at each lantern launch instead of a comet firework; a particle system placed directly
    ///                    under a #LanternRise node works too;
    ///   #FireworkMount   the launch point (default: the square's centre, 1.5 above the ground).
    /// Every hook is optional: a missing node or attachment, or one without a particle system, degrades to nothing.
    /// Without the module the building is its vanilla basis and the nodes keep their authored state.
    /// </summary>
    public class FestivalSquare : BaseComponent, IAwakableComponent, IFinishedStateListener, IDeletableEntity
    {
        private const string LightsNode = "#FestivalLights";
        private const string LanternRiseNode = "#LanternRise";
        private const string MountNode = "#FireworkMount";
        private const string LanternRiseAttachment = "LanternRise";

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

        /// <summary>The square's dance floor (its basis' enterable slots), or null if its data has none.</summary>
        public Enterable Enterable { get; private set; }

        /// <summary>The square's attraction effects (Campfire), applied to festival dancers as to any visitor; or null.</summary>
        public Attraction Attraction { get; private set; }

        public void Awake()
        {
            _districtBuilding = GetComponent<DistrictBuilding>();
            _center = GetComponent<BlockObjectCenter>();
            Enterable = GetComponent<Enterable>();
            Attraction = GetComponent<Attraction>();
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

        /// <summary>The square has the art lane's lantern particles (the LanternRise attachment or a particle system under
        /// #LanternRise).</summary>
        public bool HasLanternSky
        {
            get { FindNodes(); return _lanternRise; }
        }

        /// <summary>
        /// The sky over the square during the show: lanterns leave it all evening at <paramref name="perSecond"/> (in the
        /// particles' own seconds), drifting with the wind; off, it stops emitting and the last lanterns fade out. Particle
        /// time follows the game's nonlinear animation speed (as the game's own swaying plants), so the sky holds the same
        /// number of lanterns at every game speed and stands still when the game is paused. No-op without the art.
        /// </summary>
        internal void UpdateSky(bool on, float perSecond, Vector3 drift, float simulationSpeed)
        {
            FindNodes();
            if (!_lanternRise) return;
            try
            {
                var main = _lanternRise.main;
                main.simulationSpeed = Mathf.Clamp(simulationSpeed, 0.05f, 4f);
                var vel = _lanternRise.velocityOverLifetime;
                if (vel.enabled)
                {
                    vel.x = new ParticleSystem.MinMaxCurve(drift.x - 0.08f, drift.x + 0.08f);
                    vel.z = new ParticleSystem.MinMaxCurve(drift.z - 0.08f, drift.z + 0.08f);
                }
                var emission = _lanternRise.emission;
                emission.enabled = true;
                emission.rateOverTime = on ? perSecond : 0f;
                if (on && !_lanternRise.isPlaying)
                {
                    main.loop = true;
                    _lanternRise.Play(true);
                }
                else if (!on && _lanternRise.isEmitting)
                    _lanternRise.Stop(true, ParticleSystemStopBehavior.StopEmitting);
            }
            catch (Exception e) { Debug.LogWarning("[Pandaborn.Festival] lantern sky failed: " + e.Message); _lanternRise = null; }
        }

        /// <summary>Lanterns in the sky now (tests), or -1 without the art.</summary>
        public int SkyLanterns => _lanternRise ? _lanternRise.particleCount : -1;

        /// <summary>Sends up <paramref name="count"/> lanterns at once (the release at the start of the show).</summary>
        internal bool Release(int count)
        {
            FindNodes();
            if (!_lanternRise || count <= 0) return false;
            try
            {
                if (!_lanternRise.isPlaying) { var main = _lanternRise.main; main.loop = true; _lanternRise.Play(true); }
                _lanternRise.Emit(count);
                return true;
            }
            catch (Exception e) { Debug.LogWarning("[Pandaborn.Festival] lantern release failed: " + e.Message); _lanternRise = null; return false; }
        }

        internal bool Launch(FestivalFireworks fireworks, string fireworkId, bool lantern)
        {
            FindNodes();
            if (lantern && _lanternRise) return Release(1);
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
            try
            {
                // TemplateAttachmentsSpec is internal: ask for the attachment and treat "not found" as "no lantern art"
                var attachments = GetComponent<TemplateAttachments>();
                if (attachments != null)
                {
                    var attachment = attachments.GetOrCreateAttachment(LanternRiseAttachment);
                    attachment.GameObject.SetActive(true);
                    var particles = attachment.GameObject.GetComponentInChildren<ParticleSystem>(true);
                    if (particles) _lanternRise = particles;
                }
            }
            catch (System.Collections.Generic.KeyNotFoundException) { }
            catch (Exception e) { Debug.LogWarning("[Pandaborn.Festival] LanternRise attachment unusable, comets instead: " + e.Message); }
        }
    }
}
