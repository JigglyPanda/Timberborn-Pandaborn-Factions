using Pandaborn.Specs;
using Timberborn.BaseComponentSystem;
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

        public float ProductionEfficiency() => InDrought ? _spec.DroughtEfficiency : _spec.TemperateEfficiency;

        public float MaxProductionProgressChange(float expectedProductionProgressChange) => expectedProductionProgressChange;
    }

    /// <summary>
    /// Scoop Wheel / Water Trip-Hammer (PandabornCurrentDrivenSpec): reads the vanilla water-powered generator on the same
    /// building and raises "the current here is too weak" (with what to do) when it turns nothing. The vanilla "needs
    /// power" status still shows too: it is vanilla's and cannot be removed without patching.
    /// </summary>
    public class CurrentDriven : TickableComponent, IAwakableComponent, IInitializableEntity
    {
        private const int Interval = 20;
        private readonly ILoc _loc;
        private readonly CisternTapHint _hint;
        private WaterPoweredGenerator _generator;
        private MechanicalNode _node;
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
            _weak = StatusToggle.CreateNormalStatusWithFloatingIcon("NothingToDo", _loc.T("Pandaborn.Water.Status.WeakCurrent"));
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
            var blockObject = GetComponent<Timberborn.BlockSystem.BlockObject>();
            bool still = blockObject != null && blockObject.IsFinished && _generator != null && Current <= 0f;
            if (!still && Current > 0f) _hadCurrent = true;
            // a wheel that turned before and stopped (its river dried up), or any wheel in a drought: stored water helps.
            // A wheel built in still water is in the wrong place, and the plain status says so.
            bool hinted = still && (_hadCurrent || _hint.InDrought) && _hint.Available && EnsureHinted();
            _weak.Toggle(still && !hinted);
            _weakWithHint?.Toggle(hinted);
        }

        private bool EnsureHinted()
        {
            if (_weakWithHint != null) return true;
            if (_subject == null || _hint.Sentence == null) return false;
            _weakWithHint = StatusToggle.CreateNormalStatusWithFloatingIcon("NothingToDo",
                _loc.T("Pandaborn.Water.Status.WeakCurrent") + " " + _hint.Sentence);
            _subject.RegisterStatus(_weakWithHint);
            return true;
        }
    }
}
