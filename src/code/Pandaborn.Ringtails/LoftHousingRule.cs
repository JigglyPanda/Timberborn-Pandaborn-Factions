using System.Collections.Generic;
using System.Linq;
using Pandaborn.Specs;
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

        // before the first Moon Loft has brought the family there is no Ringtail to house: the rule costs nothing until then
        public bool Active => _ringtailService.Enabled && _ringtailService.Arrived && !DisabledByDev && !_failed;

        private bool _failed;

        public void Tick()
        {
            if (++_ticks < TicksBetweenPasses) return;
            _ticks = 0;
            if (!Active) return;
            // an exception in a tick is a crash: if the rule ever throws it switches itself off for the session and vanilla
            // housing (anyone may live anywhere) carries on
            try
            {
                var districts = _districtCenterRegistry.FinishedDistrictCenters;
                for (int i = 0; i < districts.Count; i++)
                    if (districts[i]) Pass(districts[i].DistrictPopulation);
            }
            catch (System.Exception e)
            {
                _failed = true;
                UnityEngine.Debug.LogError("[Pandaborn.Ringtails] the loft housing rule failed and is off for this session: " + e);
                Pandaborn.Core.FeatureRegistry.ReportDegraded(RingtailService.FeatureId, "the loft housing rule failed (" + e.GetType().Name + ")");
            }
        }

        private static bool IsLoft(Dwelling home) => home && home.GetComponent<PandabornMoonLoftSpec>() != null;

        private void Pass(DistrictPopulation population)
        {
            List<Dweller> ringtailsOutside = null, inkpawsInLofts = null, homelessRingtails = null;
            bool anyKit = false;
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
            // the homes are only listed when there is something to sort: a homeless Ringtail, or a child that may be in the
            // wrong kind of home (most passes end here)
            var children = population.Children;
            for (int i = 0; i < children.Count && !anyKit; i++)
            {
                var d = children[i].GetComponent<Dweller>();
                if (d == null) continue;
                bool ringtail = RingtailService.IsRingtail(children[i]);
                anyKit = ringtail ? !d.HasHome : d.HasHome && IsLoft(d.Home);
            }
            if (homelessRingtails == null && !anyKit) return;
            var registry = population.GetComponent<DistrictBuildingRegistry>();
            if (registry == null) return;
            var dwellings = registry.GetEnabledBuildingsInstant<Dwelling>().ToList();
            if (anyKit) SortKits(population, dwellings);
            if (homelessRingtails == null) return;
            int next = 0;
            foreach (var dweller in homelessRingtails)
            {
                var loft = dwellings.FirstOrDefault(d => IsLoft(d) && d.HasFreeSlots);
                Dweller inkpaw = null;
                while (loft == null && inkpawsInLofts != null && next < inkpawsInLofts.Count)
                {
                    // only an Inkpaw still in a loft: the swaps above have already moved some of the list into dens (taking
                    // one of those would put the Ringtail in a den and the Inkpaw on the street)
                    var candidate = inkpawsInLofts[next++];
                    if (!candidate.HasHome || !IsLoft(candidate.Home)) continue;
                    inkpaw = candidate;
                    loft = candidate.Home;
                }
                if (inkpaw != null)
                {
                    // a loft bed held by an Inkpaw: move the Inkpaw to a free non-loft bed, or (none free) out; lofts are Ringtail homes
                    var den = dwellings.FirstOrDefault(d => !IsLoft(d) && d.HasFreeSlots);
                    loft.UnassignDweller(inkpaw);
                    if (den != null) den.AssignDweller(inkpaw);
                    else Evictions++;
                }
                if (loft == null) break;
                if (!loft.HasFreeSlots) continue;   // AssignDweller throws on a full home
                loft.AssignDweller(dweller);
                MovesIntoLofts++;
            }
        }

        /// <summary>
        /// The young: a loft's kit slot is where its nursery raises the next kit, so an Inkpaw cub in a loft moves to a free
        /// cub slot in a home that wants a cub (never to nowhere), and a homeless Ringtail kit takes a free loft kit slot. A kit
        /// that vanilla moved to a den to live with adults stays there (kits are born in lofts, not confined to them).
        /// </summary>
        private void SortKits(DistrictPopulation population, List<Dwelling> dwellings)
        {
            foreach (Beaver child in population.Children.ToList())
            {
                var dweller = child.GetComponent<Dweller>();
                if (dweller == null) continue;
                bool ringtail = RingtailService.IsRingtail(child);
                if (!ringtail && dweller.HasHome && IsLoft(dweller.Home))
                {
                    // only to a home that wants a cub (vanilla would otherwise move it straight back)
                    var den = dwellings.FirstOrDefault(d => !IsLoft(d) && d.HasFreeChildSlots && d.UnderpopulatedByChildren);
                    if (den == null) continue;
                    dweller.Home.UnassignDweller(dweller);
                    den.AssignDweller(dweller);
                    CubsMovedOut++;
                }
                else if (ringtail && !dweller.HasHome)
                {
                    var loft = dwellings.FirstOrDefault(d => IsLoft(d) && d.HasFreeSlots && d.HasFreeChildSlots);
                    if (loft == null) continue;
                    if (dweller.HasHome) dweller.Home.UnassignDweller(dweller);
                    loft.AssignDweller(dweller);
                    MovesIntoLofts++;
                }
            }
        }

        public int CubsMovedOut { get; private set; }

        private void Swap(Dweller ringtail, Dweller inkpaw)
        {
            var den = ringtail.Home;
            var loft = inkpaw.Home;
            if (!den || !loft || den == loft) return;
            loft.UnassignDweller(inkpaw);
            den.UnassignDweller(ringtail);
            // both homes have the bed just freed (AssignDweller throws on a full home; nothing else runs in between)
            if (loft.HasFreeSlots) loft.AssignDweller(ringtail);
            if (den.HasFreeSlots) den.AssignDweller(inkpaw);
            Swaps++;

        }
    }
}
