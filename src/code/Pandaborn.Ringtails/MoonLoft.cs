using System;
using System.Collections.Generic;
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

        /// <summary>The loc key of what the loft's panel line says about kits ("" = nothing). Set by the nursery at each
        /// dawn and whenever the panel asks (<see cref="LoftNursery.Refresh"/>).</summary>
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
            // only queues the arrival (RingtailService.Tick carries it out): on a load this step runs while the world is
            // still being put together, and an exception here would fail the load
            try { _ringtailService.OnMoonLoftFinished(this); }
            catch (Exception e) { Debug.LogError("[Pandaborn.Ringtails] a finished Moon Loft could not announce itself: " + e); }
        }

        public void OnExitFinishedState() { }

        public int RingtailAdultDwellers
        {
            get
            {
                int n = 0;
                if (_dwelling != null) foreach (var d in _dwelling.AdultDwellers) if (RingtailService.IsRingtail(d)) n++;
                return n;
            }
        }

        /// <summary>Moves a new Ringtail into this loft if there is room (the housing rule sorts the rest out).</summary>
        public void TakeIn(Character character)
        {
            var dweller = character.GetComponent<Dweller>();
            // only the total is checked (the nursery checks HasFreeChildSlots itself)
            if (dweller == null || _dwelling == null || !IsFinished || !_dwelling.HasFreeSlots) return;
            _dwelling.AssignDweller(dweller);
        }

        /// <summary>True when a kit could be raised here now, or after an Inkpaw lodger has given way.</summary>
        public bool CouldMakeRoomForKit()
        {
            if (_dwelling == null || _dwelling.ChildSlots <= 0) return false;
            if (_dwelling.HasFreeSlots && _dwelling.HasFreeChildSlots) return true;
            foreach (var d in _dwelling.ChildDwellers) if (!RingtailService.IsRingtail(d)) return true;
            if (_dwelling.HasFreeSlots || _dwelling.NumberOfChildDwellers >= _dwelling.ChildSlots) return false;
            foreach (var d in _dwelling.AdultDwellers) if (!RingtailService.IsRingtail(d)) return true;
            return false;
        }

        /// <summary>
        /// Lofts are Ringtail homes: when the nursery has a kit to raise here, an Inkpaw lodger gives way (an Inkpaw cub in
        /// the kit slot first, else an Inkpaw adult in a full loft) and looks for another home as any homeless colonist does.
        /// Ringtails are never moved. Found in phase 3: homeless Inkpaws fill a new loft before its first dawn, and without
        /// this the loft would say "no room" for ever. True when there is room for a kit now.
        /// </summary>
        public bool MakeRoomForKit()
        {
            if (_dwelling == null) return false;
            if (_dwelling.HasFreeSlots && _dwelling.HasFreeChildSlots) return true;
            Dweller lodger = null;
            foreach (var d in _dwelling.ChildDwellers) if (!RingtailService.IsRingtail(d)) { lodger = d; break; }
            if (lodger == null && !_dwelling.HasFreeSlots)
                foreach (var d in _dwelling.AdultDwellers) if (!RingtailService.IsRingtail(d)) { lodger = d; break; }
            if (lodger == null) return false;
            _dwelling.UnassignDweller(lodger);
            return _dwelling.HasFreeSlots && _dwelling.HasFreeChildSlots;
        }
    }

    /// <summary>
    /// The population valve (DESIGN.md: "kits are raised in the Moon Loft while there is work for them"); the rules are in
    /// <see cref="KitValve"/>. At every dawn, per district: open night jobs = desired workers of the finished, Ringtail-typed
    /// night posts minus Ringtail adults minus Ringtail kits already growing. While that is above zero, and no colonist in
    /// the district is critically hungry or thirsty, and the district has a Ringtail adult, each Moon Loft with a free kit
    /// slot raises one kit (KitsPerDay). So kits never outnumber the jobs waiting for them, a demolished post stops births
    /// at once, and ten lofts raise no more Ringtails than one loft would. Ringtails left without a job (a post
    /// demolished) stay, rest and take leisure; they are shown as idle.
    /// A district that has a finished loft and no living Ringtail at all (old age took the last of them, or a session with
    /// the module off turned them into Inkpaws) is not lost: after PandabornRingtailsSpec.ReturnAfterDays empty dawns a new
    /// family answers the lantern (RingtailService.DawnWithoutRingtails).
    /// </summary>
    public class LoftNursery : ILoadableSingleton
    {
        private readonly RingtailService _ringtailService;
        private readonly DistrictCenterRegistry _districtCenterRegistry;
        private readonly EventBus _eventBus;
        private readonly Messenger _messenger;
        private readonly ILoc _loc;
        private readonly List<MoonLoft> _lofts = new List<MoonLoft>();
        private bool _errorLogged;

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
            // an exception in an event handler would surface in the game's day-night tick: contain it
            try
            {
                var districts = new List<DistrictCenter>();
                foreach (var d in _districtCenterRegistry.FinishedDistrictCenters) districts.Add(d);
                var seen = new HashSet<string>(StringComparer.Ordinal);
                foreach (var district in districts)
                {
                    if (!district) continue;
                    string id = DistrictId(district);
                    if (id != null) seen.Add(id);
                    RaiseKits(district);
                }
                _ringtailService.KeepWaitsOnlyFor(seen);
            }
            catch (Exception ex)
            {
                if (_errorLogged) return;
                _errorLogged = true;
                Debug.LogError("[Pandaborn.Ringtails] the Moon Loft nursery failed at dawn; no kit is raised today: " + ex);
            }
        }

        /// <summary>The district's saved id (its entity id), or null.</summary>
        public static string DistrictId(DistrictCenter district)
        {
            var entity = district ? district.GetComponent<EntityComponent>() : null;
            return entity != null ? entity.EntityId.ToString("N") : null;
        }

        /// <summary>What the valve sees in one district.</summary>
        public struct Census
        {
            public int Adults, Kits, DesiredWorkers;
            public bool Starving;
            public int OpenJobs => KitValve.OpenJobs(DesiredWorkers, Adults, Kits);
        }

        /// <summary>Counts the district's living Ringtails, the worker slots of its Ringtail posts, and whether anyone is
        /// critically hungry or thirsty; fills <paramref name="lofts"/> with its finished, working Moon Lofts.</summary>
        public Census Count(DistrictCenter district, List<MoonLoft> lofts)
        {
            var census = new Census();
            lofts?.Clear();
            var registry = district.GetComponent<DistrictBuildingRegistry>();
            if (registry == null) return census;
            if (lofts != null)
                foreach (var dwelling in registry.GetEnabledBuildingsInstant<Dwelling>())
                {
                    var loft = dwelling.GetComponent<MoonLoft>();
                    if (loft != null) lofts.Add(loft);
                }
            foreach (var workplace in registry.GetEnabledBuildingsInstant<Workplace>())
            {
                var post = workplace.GetComponent<NightPost>();
                if (post != null && post.IsRingtailTyped) census.DesiredWorkers += workplace.DesiredWorkers;
            }
            var population = district.DistrictPopulation;
            var adults = population.Adults;
            for (int i = 0; i < adults.Count; i++) if (IsLivingRingtail(adults[i])) census.Adults++;
            var children = population.Children;
            for (int i = 0; i < children.Count; i++) if (IsLivingRingtail(children[i])) census.Kits++;
            var beavers = population.Beavers;
            for (int i = 0; i < beavers.Count && !census.Starving; i++)
            {
                var needs = beavers[i].GetComponent<NeedManager>();
                if (needs == null) continue;
                census.Starving = (needs.HasNeed("Hunger") && needs.NeedIsInCriticalState("Hunger"))
                                  || (needs.HasNeed("Thirst") && needs.NeedIsInCriticalState("Thirst"));
            }
            return census;
        }

        private static bool IsLivingRingtail(Beaver beaver)
        {
            if (!RingtailService.IsRingtail(beaver)) return false;
            var character = beaver.GetComponent<Character>();
            return character == null || character.Alive;
        }

        /// <summary>Open night jobs in a district (can be negative: idle Ringtails).</summary>
        public int OpenNightJobs(DistrictCenter district) => Count(district, null).OpenJobs;

        /// <summary>Brings a loft's panel line up to date (the panel calls it about once a second while a loft is selected, so
        /// the line is right after a load and for a loft built since dawn). Changes nothing else.</summary>
        public void Refresh(MoonLoft loft)
        {
            if (loft == null || !_ringtailService.Enabled || !_ringtailService.Arrived) return;
            var building = loft.GetComponent<DistrictBuilding>();
            var district = building != null ? building.InstantDistrict : null;
            if (!district || !loft.IsFinished)
            {
                loft.KitState = "";
                return;
            }
            var census = Count(district, null);
            loft.KitState = KitValve.LocKey(KitValve.Decide(census.Adults, census.Kits, census.Starving, census.OpenJobs, loft.CouldMakeRoomForKit()));
        }

        public void RaiseKits(DistrictCenter district)
        {
            var census = Count(district, _lofts);
            if (_lofts.Count == 0)
            {
                // no loft: no wait is counted (and a running count is dropped)
                _ringtailService.DawnWithoutRingtails(DistrictId(district), null, census.Adults + census.Kits, census.Starving);
                return;
            }
            var lofts = _lofts.ToArray();   // raising a kit must not disturb the list being walked
            if (_ringtailService.DawnWithoutRingtails(DistrictId(district), lofts[0], census.Adults + census.Kits, census.Starving))
                census = Count(district, null);   // a family came back this dawn
            int open = census.OpenJobs;
            foreach (var loft in lofts)
            {
                if (!loft) continue;
                // parents: any Ringtail adult of the district (the first family fills its loft, so "a Ringtail lives here"
                // would stop every other loft from ever raising a kit)
                var state = KitValve.Decide(census.Adults, census.Kits, census.Starving, open, loft.CouldMakeRoomForKit());
                if (state == KitState.Raising && !loft.MakeRoomForKit()) state = KitState.NoRoom;
                int kits = KitValve.KitsToRaise(state, loft.Spec != null ? loft.Spec.KitsPerDay : 1, open);
                for (int i = 0; i < kits && loft.Dwelling.HasFreeChildSlots && loft.Dwelling.HasFreeSlots; i++)
                {
                    var kit = _ringtailService.CreateChild(loft.Doorstep);
                    if (!kit) break;
                    loft.TakeIn(kit);
                    open--;
                    census.Kits++;
                    KitsRaised++;
                    _messenger.Post(_loc.T("Pandaborn.Ringtails.KitBorn", kit.FirstName), kit, toast: false);
                }
                loft.KitState = KitValve.LocKey(state);
            }
        }
    }
}
