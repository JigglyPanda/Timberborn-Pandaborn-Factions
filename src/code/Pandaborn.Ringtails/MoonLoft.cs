using System.Collections.Generic;
using System.Linq;
using Pandaborn.Core;
using Pandaborn.Specs;
using Timberborn.BaseComponentSystem;
using Timberborn.Beavers;
using Timberborn.BlockSystem;
using Timberborn.Characters;
using Timberborn.Coordinates;
using Timberborn.DwellingSystem;
using Timberborn.EntitySystem;
using Timberborn.GameDistricts;
using Timberborn.Localization;
using Timberborn.NeedSystem;
using Timberborn.SingletonSystem;
using Timberborn.TimeSystem;
using Timberborn.WorkSystem;
using UnityEngine;

namespace Pandaborn.Ringtails
{
    /// <summary>
    /// The Moon Loft (PandabornMoonLoftSpec). The first one finished in a save brings the Ringtails (RingtailService). Its
    /// kits come from <see cref="LoftNursery"/>. Without the feature it is an ordinary home.
    /// </summary>
    public class MoonLoft : BaseComponent, IAwakableComponent, IFinishedStateListener
    {
        private readonly RingtailService _ringtailService;
        private Dwelling _dwelling;
        private BlockObject _blockObject;

        public MoonLoft(RingtailService ringtailService)
        {
            _ringtailService = ringtailService;
        }

        public PandabornMoonLoftSpec Spec { get; private set; }

        public Dwelling Dwelling => _dwelling;

        public bool IsFinished => _blockObject != null && _blockObject.IsFinished;

        /// <summary>What the loft's panel line says about kits (set by the nursery each dawn, and on demand).</summary>
        public string KitState { get; set; } = "";

        public Vector3 Doorstep => _blockObject != null && _blockObject.HasEntrance
            ? CoordinateSystem.GridToWorldCentered(_blockObject.PositionedEntrance.Coordinates)
            : Transform.position;

        public void Awake()
        {
            _dwelling = GetComponent<Dwelling>();
            _blockObject = GetComponent<BlockObject>();
            Spec = GetComponent<PandabornMoonLoftSpec>();
        }

        public void OnEnterFinishedState()
        {
            _ringtailService.OnMoonLoftFinished(this);
        }

        public void OnExitFinishedState() { }

        public int RingtailAdultDwellers => _dwelling == null ? 0 : _dwelling.AdultDwellers.Count(d => RingtailService.IsRingtail(d));

        /// <summary>Moves a new Ringtail into this loft if there is room (the housing rule sorts the rest out).</summary>
        public void TakeIn(Character character)
        {
            var dweller = character.GetComponent<Dweller>();
            // only the total is checked: the arrival runs inside the loft's own "finished" step, before the dwelling has
            // worked out its child slots (the nursery checks HasFreeChildSlots itself)
            if (dweller == null || _dwelling == null || !_dwelling.HasFreeSlots) return;
            _dwelling.AssignDweller(dweller);
        }
    }

    /// <summary>
    /// The population valve (DESIGN.md: "kits are raised in the Moon Loft while there is work for them"). At every dawn, per
    /// district: open night jobs = desired workers of the finished, Ringtail-typed night posts minus Ringtail adults minus
    /// Ringtail kits already growing. While that is above zero, and no colonist in the district is critically hungry or
    /// thirsty, and the district has a Ringtail adult, each Moon Loft with a free kit slot raises one kit (KitsPerDay). So kits never
    /// outnumber the jobs waiting for them, a demolished post stops births at once, and ten lofts raise no more Ringtails than
    /// one loft would. Ringtails left without a job (a post demolished) stay, rest and take leisure; they are shown as idle.
    /// </summary>
    public class LoftNursery : ILoadableSingleton
    {
        private readonly RingtailService _ringtailService;
        private readonly DistrictCenterRegistry _districtCenterRegistry;
        private readonly EventBus _eventBus;
        private readonly Messenger _messenger;
        private readonly ILoc _loc;

        public LoftNursery(RingtailService ringtailService, DistrictCenterRegistry districtCenterRegistry, EventBus eventBus,
                           Messenger messenger, ILoc loc)
        {
            _ringtailService = ringtailService;
            _districtCenterRegistry = districtCenterRegistry;
            _eventBus = eventBus;
            _messenger = messenger;
            _loc = loc;
        }

        public static int KitsRaised { get; private set; }

        public void Load()
        {
            _eventBus.Register(this);
        }

        [OnEvent]
        public void OnDaytimeStart(DaytimeStartEvent e)
        {
            if (!_ringtailService.Enabled || !_ringtailService.Arrived) return;
            foreach (var district in _districtCenterRegistry.FinishedDistrictCenters) RaiseKits(district);
        }

        /// <summary>Open night jobs in a district (can be negative: idle Ringtails).</summary>
        public int OpenNightJobs(DistrictCenter district)
        {
            var registry = district.GetComponent<DistrictBuildingRegistry>();
            if (registry == null) return 0;
            int desired = registry.GetEnabledBuildingsInstant<Workplace>()
                .Where(w => w.GetComponent<NightPost>() is NightPost p && p.IsRingtailTyped)
                .Sum(w => w.DesiredWorkers);
            var population = district.DistrictPopulation;
            int adults = population.Adults.Count(b => RingtailService.IsRingtail(b));
            int kits = population.Children.Count(b => RingtailService.IsRingtail(b));
            return desired - adults - kits;
        }

        private static bool AnyoneStarving(DistrictCenter district)
        {
            foreach (var beaver in district.DistrictPopulation.Beavers)
            {
                var needs = beaver.GetComponent<NeedManager>();
                if (needs == null) continue;
                if ((needs.HasNeed("Hunger") && needs.NeedIsInCriticalState("Hunger")) || (needs.HasNeed("Thirst") && needs.NeedIsInCriticalState("Thirst")))
                    return true;
            }
            return false;
        }

        public void RaiseKits(DistrictCenter district)
        {
            var registry = district.GetComponent<DistrictBuildingRegistry>();
            if (registry == null) return;
            var lofts = registry.GetEnabledBuildingsInstant<Dwelling>().Select(d => d.GetComponent<MoonLoft>()).Where(l => l != null).ToList();
            if (lofts.Count == 0) return;
            int open = OpenNightJobs(district);
            bool starving = AnyoneStarving(district);
            // parents: any Ringtail adult of the district (the first family fills its loft, so "a Ringtail lives here" would
            // stop every other loft from ever raising a kit)
            bool parents = district.DistrictPopulation.Adults.Any(b => RingtailService.IsRingtail(b));
            foreach (var loft in lofts)
            {
                if (!parents) { loft.KitState = "Pandaborn.Ringtails.Loft.NoParents"; continue; }
                if (starving) { loft.KitState = "Pandaborn.Ringtails.Loft.Hungry"; continue; }
                if (open <= 0) { loft.KitState = "Pandaborn.Ringtails.Loft.WaitingForJobs"; continue; }
                if (!loft.Dwelling.HasFreeChildSlots || !loft.Dwelling.HasFreeSlots) { loft.KitState = "Pandaborn.Ringtails.Loft.NoRoom"; continue; }
                int perDay = loft.Spec != null ? Mathf.Max(1, loft.Spec.KitsPerDay) : 1;
                for (int i = 0; i < perDay && open > 0 && loft.Dwelling.HasFreeChildSlots && loft.Dwelling.HasFreeSlots; i++)
                {
                    var kit = _ringtailService.CreateChild(loft.Doorstep);
                    if (!kit) break;
                    loft.TakeIn(kit);
                    open--;
                    KitsRaised++;
                    _messenger.Post(_loc.T("Pandaborn.Ringtails.KitBorn", kit.FirstName), toast: false);
                }
                loft.KitState = "Pandaborn.Ringtails.Loft.Raising";
            }
        }
    }
}
