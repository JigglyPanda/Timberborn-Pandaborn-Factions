using Timberborn.BaseComponentSystem;
using Timberborn.BlueprintSystem;
using Timberborn.HazardousWeatherSystem;
using Timberborn.WeatherSystem;
using Timberborn.Workshops;

namespace Pandaborn.Water
{
    /// <summary>Production efficiency of a workerless dew collector by weather.</summary>
    public record PandabornDewLimiterSpec : ComponentSpec
    {
        [Serialize]
        public float TemperateEfficiency { get; init; }

        [Serialize]
        public float DroughtEfficiency { get; init; }
    }

    /// <summary>
    /// An <see cref="IManufactoryLimiter"/> (collected by <c>Manufactory.Awake</c>): full rate in temperate weather, a
    /// fraction in drought. Badtide counts as temperate air. Saves nothing.
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

        public void Awake()
        {
            _spec = GetComponent<PandabornDewLimiterSpec>();
        }

        public bool InDrought => _weatherService.IsHazardousWeather && _hazardousWeatherService.CurrentCycleHazardousWeather is DroughtWeather;

        public float ProductionEfficiency()
        {
            return InDrought ? _spec.DroughtEfficiency : _spec.TemperateEfficiency;
        }

        public float MaxProductionProgressChange(float expectedProductionProgressChange)
        {
            return expectedProductionProgressChange;
        }
    }
}
