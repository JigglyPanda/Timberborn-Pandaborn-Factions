using System.Linq;
using Pandaborn.Specs;
using Timberborn.Buildings;
using Timberborn.EntitySystem;
using Timberborn.HazardousWeatherSystem;
using Timberborn.Localization;
using Timberborn.ScienceSystem;
using Timberborn.WeatherSystem;

namespace Pandaborn.Water
{
    /// <summary>
    /// The one-sentence drought hint added to a stopped Scoop Wheel's or a dry Flume Gate's status: stored Water can be
    /// poured into the line with the Cistern Tap. Only offered when the active faction has a building with
    /// PandabornCisternTapSpec and it is unlocked (never point the player at something hidden), and named by its own
    /// display name.
    /// </summary>
    public class CisternTapHint
    {
        private readonly BuildingService _buildingService;
        private readonly BuildingUnlockingService _unlocking;
        private readonly WeatherService _weatherService;
        private readonly HazardousWeatherService _hazardousWeatherService;
        private readonly ILoc _loc;
        private bool _searched;
        private BuildingSpec _tap;
        private string _sentence;

        public CisternTapHint(BuildingService buildingService, BuildingUnlockingService unlocking, WeatherService weatherService,
                              HazardousWeatherService hazardousWeatherService, ILoc loc)
        {
            _buildingService = buildingService;
            _unlocking = unlocking;
            _weatherService = weatherService;
            _hazardousWeatherService = hazardousWeatherService;
            _loc = loc;
        }

        public bool InDrought => _weatherService.IsHazardousWeather && _hazardousWeatherService.CurrentCycleHazardousWeather is DroughtWeather;

        /// <summary>The hint sentence naming the faction's tap, or null when the faction has none.</summary>
        public string Sentence
        {
            get
            {
                Find();
                return _sentence;
            }
        }

        /// <summary>True when the hint may be shown now: the faction has the tap and it is unlocked.</summary>
        public bool Available
        {
            get
            {
                Find();
                return _tap != null && _sentence != null && _unlocking.Unlocked(_tap);
            }
        }

        private void Find()
        {
            if (_searched) return;
            _searched = true;
            _tap = _buildingService.Buildings.FirstOrDefault(b => b.Blueprint != null && b.Blueprint.HasSpec<PandabornCisternTapSpec>());
            var label = _tap?.Blueprint.HasSpec<LabeledEntitySpec>() == true ? _tap.Blueprint.GetSpec<LabeledEntitySpec>() : null;
            if (label != null && !string.IsNullOrEmpty(label.DisplayNameLocKey))
                _sentence = _loc.T("Pandaborn.Water.Hint.CisternTap", _loc.T(label.DisplayNameLocKey));
        }
    }
}
