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
    ///   #FestivalLights  shown from the call until the festival ends at a square of the festival's district, hidden
    ///                    otherwise (lantern strings, lit stalls);
    ///   LanternRise      a template attachment (TemplateAttachmentsSpec, parent #LanternRise) with one ParticleSystem:
    ///                    the rising paper lanterns. The module drives it (emission rate, single releases, wind drift,
    ///                    simulation speed); a particle system placed directly under a #LanternRise node works too;
    ///   #FireworkMount   the launch point of comets and bursts (default: the square's centre, 1.5 above the ground).
    /// Every hook is optional: a missing node or attachment, or one without a particle system, degrades to nothing (the
    /// lanterns to the game's comet rockets). Without the module the building is its vanilla basis and the nodes keep
    /// their authored state.
    /// </summary>
    public class FestivalSquare : BaseComponent, IAwakableComponent, IFinishedStateListener, IDeletableEntity
    {
        private const string LightsNode = "#FestivalLights";
        private const string LanternRiseNode = "#LanternRise";
        private const string MountNode = "#FireworkMount";
        private const string LanternRiseAttachment = "LanternRise";
        private const string Log = "[Pandaborn.Festival] ";

        private readonly FestivalService _festivalService;
        private DistrictBuilding _districtBuilding;
        private BlockObjectCenter _center;
        private EntityComponent _entity;
        private Transform _lights;
        private ParticleSystem _lanternRise;
        private Transform _mount;
        private GameObject _soundEmitter;
        private bool _nodesSearched;
        private bool _skyOn;
        private float _skySpeed = -1f;
        private Vector3 _skyDrift = new Vector3(float.NaN, 0f, 0f);
        private readonly System.Random _random = new System.Random();

        public FestivalSquare(FestivalService festivalService)
        {
            _festivalService = festivalService;
        }

        public bool IsFinished { get; private set; }

        public DistrictCenter District => _districtBuilding ? _districtBuilding.District : null;

        public Vector3 Center => _center ? _center.WorldCenterGrounded : Transform.position;

        /// <summary>The square's saved identity (the festival remembers which square called it).</summary>
        public Guid EntityId => _entity ? _entity.EntityId : Guid.Empty;

        /// <summary>The square's dance floor (its basis' enterable slots), or null if its data has none.</summary>
        public Enterable Enterable { get; private set; }

        /// <summary>The square's attraction effects (Campfire), applied to festival dancers as to any visitor; or null.</summary>
        public Attraction Attraction { get; private set; }

        /// <summary>The festival's drum is looping here (kept by FestivalService).</summary>
        internal bool ShowSoundOn { get; set; }

        public void Awake()
        {
            _districtBuilding = GetComponent<DistrictBuilding>();
            _center = GetComponent<BlockObjectCenter>();
            _entity = GetComponent<EntityComponent>();
            Enterable = GetComponent<Enterable>();
            Attraction = GetComponent<Attraction>();
        }

        public void OnEnterFinishedState()
        {
            IsFinished = true;
            try
            {
                if (!_festivalService.Active) return;
                _festivalService.AddSquare(this);
                UpdateLights();
            }
            catch (Exception e) { Debug.LogError(Log + "registering a Festival Square failed: " + e); }
        }

        public void OnExitFinishedState()
        {
            IsFinished = false;
            try { _festivalService.RemoveSquare(this); }
            catch (Exception e) { Debug.LogError(Log + "removing a Festival Square failed: " + e); }
        }

        public void DeleteEntity()
        {
            IsFinished = false;
            try { _festivalService.RemoveSquare(this); }
            catch (Exception e) { Debug.LogError(Log + "removing a Festival Square failed: " + e); }
        }

        /// <summary>Shows the festival lights from the call to the end of a festival held here.</summary>
        public void UpdateLights()
        {
            try
            {
                FindNodes();
                if (_lights) _lights.gameObject.SetActive(_festivalService.Hosts(this));
            }
            catch (Exception e) { Debug.LogError(Log + "festival lights failed: " + e.Message); }
        }

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

        // ------------------------------------------------------------------ the lantern sky

        /// <summary>The square has the art lane's lantern particles (the LanternRise attachment or a particle system under
        /// #LanternRise).</summary>
        public bool HasLanternSky
        {
            get { FindNodes(); return _lanternRise; }
        }

        /// <summary>Lanterns in the sky now (tests), or -1 without the art.</summary>
        public int SkyLanterns => _lanternRise ? _lanternRise.particleCount : -1;

        /// <summary>The sky is being fed, or lanterns of it are still aloft: keep its speed in step with the game's.</summary>
        internal bool SkyActive => _lanternRise && (_skyOn || _lanternRise.particleCount > 0);

        /// <summary>
        /// The sky over the square. On: lanterns leave it at <paramref name="perSecond"/> (in the particles' own
        /// seconds), drifting with the wind; a sky switched on late starts as if it had been fed for
        /// <paramref name="prewarmSeconds"/> already. Off: it stops emitting and the last lanterns rise on and fade out.
        /// <paramref name="simulationSpeed"/> is the game's nonlinear animation multiplier (FestivalService.UpdateSky).
        /// Everything is written to the particle system only when it changes. No-op without the art; any failure
        /// switches the art off for this square (the comets take over) and is logged once.
        /// </summary>
        internal void UpdateSky(bool on, float perSecond, Vector3 drift, float simulationSpeed, float prewarmSeconds)
        {
            FindNodes();
            if (!_lanternRise) return;
            try
            {
                var main = _lanternRise.main;
                float speed = Mathf.Clamp(simulationSpeed, 0.05f, 4f);
                if (!Mathf.Approximately(speed, _skySpeed))
                {
                    main.simulationSpeed = speed;
                    _skySpeed = speed;
                }
                if (on)
                {
                    if (drift != _skyDrift)
                    {
                        var vel = _lanternRise.velocityOverLifetime;
                        if (vel.enabled)
                        {
                            // each lantern keeps its own slight drift round the wind's
                            vel.x = new ParticleSystem.MinMaxCurve(drift.x - 0.08f, drift.x + 0.08f);
                            vel.z = new ParticleSystem.MinMaxCurve(drift.z - 0.08f, drift.z + 0.08f);
                        }
                        _skyDrift = drift;
                    }
                    if (_skyOn) return;
                    _skyOn = true;
                    bool empty = _lanternRise.particleCount == 0;
                    main.loop = true;
                    var emission = _lanternRise.emission;
                    emission.enabled = true;
                    emission.rateOverTime = perSecond;
                    _lanternRise.Play(true);
                    if (empty && prewarmSeconds > 1f)
                    {
                        // fast-forward at the prefab's own speed (as the game's ParticlesObject.FastForward does), then run on
                        main.simulationSpeed = 1f;
                        _lanternRise.Simulate(prewarmSeconds, true, false, true);
                        main.simulationSpeed = speed;
                        _lanternRise.Play(true);
                    }
                }
                else if (_skyOn)
                {
                    _skyOn = false;
                    var emission = _lanternRise.emission;
                    emission.rateOverTime = 0f;
                    _lanternRise.Stop(true, ParticleSystemStopBehavior.StopEmitting);
                }
            }
            catch (Exception e) { DropLanternArt("lantern sky", e); }
        }

        /// <summary>Sends up <paramref name="count"/> lanterns at once from the square (the dense release at the start of
        /// the show). Emit, not Play: Play does nothing while earlier lanterns are still aloft.</summary>
        internal bool Release(int count)
        {
            FindNodes();
            if (!_lanternRise || count <= 0) return false;
            try
            {
                if (!_lanternRise.isPlaying) _lanternRise.Play(true);
                _lanternRise.Emit(count);
                return true;
            }
            catch (Exception e) { DropLanternArt("lantern release", e); return false; }
        }

        private void DropLanternArt(string what, Exception e)
        {
            Debug.LogWarning(Log + what + " failed; this square uses the comet rockets instead: " + e.Message);
            _lanternRise = null;
            _skyOn = false;
        }

        /// <summary>Launches one of the game's fireworks from the square: a comet rocket (lantern: gentle pitch, short
        /// flight) or a burst.</summary>
        internal bool Launch(FestivalFireworks fireworks, string fireworkId, bool lantern)
        {
            try
            {
                FindNodes();
                var origin = _mount ? _mount.position : Center + Vector3.up * 1.5f;
                var offset = new Vector3((float)(_random.NextDouble() - 0.5) * 2.5f, 0f, (float)(_random.NextDouble() - 0.5) * 2.5f);
                float pitch = (float)(_random.NextDouble() - 0.5) * (lantern ? 16f : 30f);
                float heading = (float)_random.NextDouble() * 360f;
                float distance = lantern ? 14f + (float)_random.NextDouble() * 10f : 22f + (float)_random.NextDouble() * 14f;
                return fireworks.Launch(fireworkId, origin + offset, pitch, heading, distance);
            }
            catch (Exception e)
            {
                Debug.LogWarning(Log + "launch from the square failed: " + e.Message);
                return false;
            }
        }

        private void FindNodes()
        {
            if (_nodesSearched) return;
            _nodesSearched = true;
            try
            {
                foreach (var t in GameObject.GetComponentsInChildren<Transform>(true))
                {
                    if (t.name == LightsNode) _lights = t;
                    else if (t.name == LanternRiseNode) _lanternRise = t.GetComponentInChildren<ParticleSystem>(true);
                    else if (t.name == MountNode) _mount = t;
                }
            }
            catch (Exception e) { Debug.LogWarning(Log + "the square's festival nodes could not be read: " + e.Message); }
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
            catch (Exception e) { Debug.LogWarning(Log + "LanternRise attachment unusable, comets instead: " + e.Message); }
        }
    }
}
