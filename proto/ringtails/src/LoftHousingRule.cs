using System.Collections.Generic;
using System.Linq;
using Timberborn.Beavers;
using Timberborn.DwellingSystem;
using Timberborn.GameDistricts;
using Timberborn.SingletonSystem;
using Timberborn.TickSystem;

namespace Pandaborn.Ringtails
{
    /// <summary>
    /// The least invasive housing rule we found: vanilla decides who gets a bed (anyone may live anywhere; there is no hook to
    /// filter dwellers without patching AutoAssignableDwelling.CanAssignDweller). This rule only corrects afterwards, with public
    /// API, and never changes how many dwellers a home has, so vanilla's own "move to an emptier home" logic has nothing to undo:
    ///   * a Ringtail in a non-loft home and an Inkpaw in a loft swap homes;
    ///   * a homeless Ringtail takes a free loft bed, or else a loft bed held by an Inkpaw (who moves to a free non-loft bed,
    ///     or becomes homeless when there is none: loft beds belong to Ringtails).
    /// Runs every few ticks, a handful of moves at a time. Off unless the Ringtail feature is on.
    /// </summary>
    public class LoftHousingRule : ITickableSingleton, ILoadableSingleton
    {
        private const int TicksBetweenPasses = 10;
        private readonly RingtailService _ringtailService;
        private readonly DistrictCenterRegistry _districtCenterRegistry;
        private int _ticks;

        /// <summary>Dev switch (harness request "ringtails.housingRule": false) to watch plain vanilla housing.</summary>
        public static bool DisabledByDev;

        public int Swaps { get; private set; }
        public int MovesIntoLofts { get; private set; }
        public int Evictions { get; private set; }

        public LoftHousingRule(RingtailService ringtailService, DistrictCenterRegistry districtCenterRegistry)
        {
            _ringtailService = ringtailService;
            _districtCenterRegistry = districtCenterRegistry;
        }

        public void Load() { }

        public bool Active => _ringtailService.Enabled && !DisabledByDev;

        public void Tick()
        {
            if (!Active || ++_ticks < TicksBetweenPasses) return;
            _ticks = 0;
            foreach (var district in _districtCenterRegistry.FinishedDistrictCenters)
                Pass(district.DistrictPopulation);
        }

        private static bool IsLoft(Dwelling home) => home && home.GetComponent<PandabornLoftSpec>() != null;

        private void Pass(DistrictPopulation population)
        {
            List<Dweller> ringtailsOutside = null, inkpawsInLofts = null, homelessRingtails = null;
            foreach (Beaver adult in population.Adults)
            {
                var dweller = adult.GetComponent<Dweller>();
                if (dweller == null) continue;
                bool ringtail = RingtailService.IsRingtail(adult);
                if (ringtail && !dweller.HasHome) (homelessRingtails ??= new List<Dweller>()).Add(dweller);
                else if (ringtail && !IsLoft(dweller.Home)) (ringtailsOutside ??= new List<Dweller>()).Add(dweller);
                else if (!ringtail && dweller.HasHome && IsLoft(dweller.Home)) (inkpawsInLofts ??= new List<Dweller>()).Add(dweller);
            }
            if (ringtailsOutside != null && inkpawsInLofts != null)
            {
                int n = System.Math.Min(ringtailsOutside.Count, inkpawsInLofts.Count);
                for (int i = 0; i < n; i++) Swap(ringtailsOutside[i], inkpawsInLofts[i]);
            }
            if (homelessRingtails == null) return;
            var registry = population.GetComponent<DistrictBuildingRegistry>();
            if (registry == null) return;
            var dwellings = registry.GetEnabledBuildingsInstant<Dwelling>().ToList();
            int next = 0;
            foreach (var dweller in homelessRingtails)
            {
                var loft = dwellings.FirstOrDefault(d => IsLoft(d) && d.HasFreeSlots);
                if (loft == null && inkpawsInLofts != null && next < inkpawsInLofts.Count)
                {
                    // a loft bed held by an Inkpaw: move the Inkpaw to a free non-loft bed, or (none free) out; lofts are Ringtail homes
                    var inkpaw = inkpawsInLofts[next++];
                    loft = inkpaw.Home;
                    var den = dwellings.FirstOrDefault(d => !IsLoft(d) && d.HasFreeSlots);
                    loft.UnassignDweller(inkpaw);
                    if (den != null) den.AssignDweller(inkpaw);
                    else Evictions++;
                }
                if (loft == null) break;
                loft.AssignDweller(dweller);
                MovesIntoLofts++;
            }
        }

        private void Swap(Dweller ringtail, Dweller inkpaw)
        {
            var den = ringtail.Home;
            var loft = inkpaw.Home;
            if (!den || !loft || den == loft) return;
            loft.UnassignDweller(inkpaw);
            den.UnassignDweller(ringtail);
            loft.AssignDweller(ringtail);
            den.AssignDweller(inkpaw);
            Swaps++;
        }
    }
}
