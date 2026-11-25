using System;
using Pandaborn.Specs;
using Timberborn.BaseComponentSystem;
using Timberborn.BlockSystem;
using Timberborn.Buildings;
using Timberborn.EntitySystem;
using Timberborn.HazardousWeatherSystem;
using Timberborn.Localization;
using Timberborn.MechanicalSystem;
using Timberborn.PowerGeneration;
using Timberborn.StatusSystem;
using Timberborn.TickSystem;
using Timberborn.WeatherSystem;
using Timberborn.Workshops;

namespace Pandaborn.Water
{
    /// <summary>
    /// Dew Collector: an IManufactoryLimiter (collected by Manufactory.Awake): full rate in temperate weather, a fraction in
    /// drought (PandabornDewLimiterSpec). Badtide counts as temperate air. With the module off the collector simply runs
    /// at its vanilla rate in every weather.
    /// </summary>
    public class DewLimiter : BaseComponent, IAwakableComponent, IManufactoryLimiter
    {
        private readonly WeatherService _weatherService;
        private readonly HazardousWeatherService _hazardousWeatherService;
        private PandabornDewLimiterSpec _spec;

        public DewLimiter(WeatherService weatherService, HazardousWeatherService hazardousWeatherService)
        {
            _weatherService = weatherService;
            _hazardousWeatherService = hazardousWeatherService;
        }

        public void Awake() => _spec = GetComponent<PandabornDewLimiterSpec>();

        public bool InDrought => _weatherService.IsHazardousWeather && _hazardousWeatherService.CurrentCycleHazardousWeather is DroughtWeather;

        public float ProductionEfficiency()
        {
            // the game calls this from the manufactory's tick: never throw, and answer "full rate" (the vanilla
            // building) when the weather cannot be read
            try { return InDrought ? _spec.DroughtEfficiency : _spec.TemperateEfficiency; }
            catch (Exception e)
            {
                WaterGuard.Report("the Dew Collector's weather check", e);
                return 1f;
            }
        }

        public float MaxProductionProgressChange(float expectedProductionProgressChange) => expectedProductionProgressChange;
    }

    /// <summary>
    /// Scoop Wheel / Water Trip-Hammer (PandabornCurrentDrivenSpec): reads the vanilla water-powered generator on the same
    /// building and raises "the current here is too weak" (with what to do) when it turns nothing.
    /// The building is its own power source (one mechanical node that is generator and consumer), so while it is becalmed
    /// vanilla's NoPowerStatus raises "Building needs power" as well: the same cause, said twice and the second time
    /// wrongly (no shaft can help). Our status is therefore a priority status, the game's own way to let one status
    /// stand for a building (as "Paused" does): while it is active the building shows only priority statuses, so the
    /// vanilla line, its floating icon and its alert are hidden without touching vanilla code. A paused wheel shows
    /// "Paused" only.
    /// </summary>
    public class CurrentDriven : TickableComponent, IAwakableComponent, IInitializableEntity
    {
        private const int Interval = 20;
        private readonly ILoc _loc;
        private readonly CisternTapHint _hint;
        private WaterPoweredGenerator _generator;
        private MechanicalNode _node;
        private BlockObject _blockObject;
        private PausableBuilding _pausable;
        private StatusSubject _subject;
        private StatusToggle _weak, _weakWithHint;
        private bool _hadCurrent;
        private int _countdown;

        public CurrentDriven(ILoc loc, CisternTapHint hint)
        {
            _loc = loc;
            _hint = hint;
        }

        /// <summary>True while the "needs a current" status carries the Cistern Tap hint (for tests).</summary>
        public bool ShowsTapHint => _weakWithHint != null && _weakWithHint.IsActive;

        /// <summary>The current at the wheel, as the generator reads it (0 below the generator's minimum).</summary>
        public float Current => _generator != null ? System.Math.Abs(_generator.GeneratorRotation) : 0f;

        /// <summary>Share of full speed (supply over demand of the building's own one-node graph), 0..1.</summary>
        public float Speed => _node != null && _node.Graph != null ? _node.PowerEfficiency : 0f;

        /// <summary>The current at which it runs at full speed (consumer power over generator power, from the data).</summary>
        public float RatedCurrent
        {
            get
            {
                var spec = GetComponent<MechanicalNodeSpec>();
                return spec != null && spec.PowerOutput > 0 ? (float)spec.PowerInput / spec.PowerOutput : 1f;
            }
        }

        public void Awake()
        {
            _generator = GetComponent<WaterPoweredGenerator>();
            _node = GetComponent<MechanicalNode>();
            _blockObject = GetComponent<BlockObject>();
            _pausable = GetComponent<PausableBuilding>();
            _weak = StatusToggle.CreatePriorityStatusWithFloatingIcon("NothingToDo", _loc.T("Pandaborn.Water.Status.WeakCurrent"));
        }

        public void InitializeEntity()
        {
            _subject = GetComponent<StatusSubject>();
            _subject?.RegisterStatus(_weak);
        }

        public override void Tick()
        {
            if (--_countdown > 0) return;
            _countdown = Interval;
            try
            {
                bool finished = _blockObject != null && _blockObject.IsFinished && _generator != null;
                bool paused = _pausable != null && _pausable.Paused;
                bool still = finished && !paused && Current <= 0f;
                if (finished && Current > 0f) _hadCurrent = true;
                // a wheel that turned before and stopped (its river dried up), or any wheel in a drought: stored water helps.
                // A wheel built in still water is in the wrong place, and the plain status says so.
                bool hinted = still && (_hadCurrent || _hint.InDrought) && _hint.Available && EnsureHinted();
                _weak.Toggle(still && !hinted);
                _weakWithHint?.Toggle(hinted);
            }
            catch (Exception e)
            {
                WaterGuard.Report("a wheel's current check", e);
                try { _weak.Deactivate(); _weakWithHint?.Deactivate(); } catch (Exception) { }
                DisableComponent();
            }
        }

        private bool EnsureHinted()
        {
            if (_weakWithHint != null) return true;
            if (_subject == null || _hint.Sentence == null) return false;
            _weakWithHint = StatusToggle.CreatePriorityStatusWithFloatingIcon("NothingToDo",
                _loc.T("Pandaborn.Water.Status.WeakCurrent") + " " + _hint.Sentence);
            _subject.RegisterStatus(_weakWithHint);
            return true;
        }
    }
}
