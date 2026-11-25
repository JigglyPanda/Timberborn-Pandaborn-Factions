using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Pandaborn.Core;
using Pandaborn.Specs;
using Timberborn.BaseComponentSystem;
using Timberborn.BehaviorSystem;
using Timberborn.EntitySystem;
using Timberborn.NeedBehaviorSystem;
using Timberborn.NeedSystem;
using Timberborn.SleepSystem;
using Timberborn.TimeSystem;
using Timberborn.Wandering;
using Timberborn.WorkSystem;
using UnityEngine;

namespace Pandaborn.Ringtails
{
    /// <summary>
    /// The Ringtails' day rest. A root behaviour placed just above WorkerRootBehavior (so death, carrying, critical needs
    /// and stranding still win). Outside the rest window it does nothing and the Ringtail works: its worker type ignores
    /// working hours. Inside the window it keeps the Ringtail off work and runs, in order:
    ///   1. the game's own SleepNeedBehavior while Sleep is below SleepBelow (walk home, sleep until full; sleeps outside
    ///      when homeless, exactly as vanilla does),
    ///   2. the game's NeederRootBehavior (eat, drink, leisure),
    ///   3. the game's WanderRootBehavior,
    ///   4. otherwise idles for a tick.
    /// The insertion is the one private-field dependency of the rest behaviour (BehaviorManager._rootBehaviors).
    /// </summary>
    /// <summary>
    /// Every gathering clock registered through Core (Core always registers the inactive NoGatheringClock, so the list is
    /// never empty). A singleton, so the list is injected the way every other multi-bound list of the mod is.
    /// </summary>
    public class RingtailGatherings
    {
        private readonly IGatheringClock[] _clocks;

        public RingtailGatherings(IEnumerable<IGatheringClock> clocks)
        {
            _clocks = clocks != null ? clocks.ToArray() : new IGatheringClock[0];
        }

        public bool GathersNow(BaseComponent colonist)
        {
            for (int i = 0; i < _clocks.Length; i++)
            {
                try { if (_clocks[i] != null && _clocks[i].GathersNow(colonist)) return true; }
                catch (Exception) { }
            }
            return false;
        }
    }

    public class RingtailRestRootBehavior : RootBehavior, IAwakableComponent, IInitializableEntity

    {
        private const string SleepNeedId = "Sleep";
        private static readonly FieldInfo RootBehaviorsField =
            typeof(BehaviorManager).GetField("_rootBehaviors", BindingFlags.Instance | BindingFlags.NonPublic);
        private static bool _insertionErrorLogged;

        /// <summary>Set when inserting into the behaviour list failed (the game changed). Ringtails then work around the clock.</summary>
        public static string InsertionError { get; private set; }

        private readonly IDayNightCycle _dayNightCycle;
        private readonly RingtailWorkday _workday;
        private readonly RingtailService _ringtailService;

        private PandabornRingtailSpec _spec;
        private BehaviorManager _behaviorManager;
        private NeedManager _needManager;
        private SleepNeedBehavior _sleepNeedBehavior;
        private NeederRootBehavior _neederRootBehavior;
        private WanderRootBehavior _wanderRootBehavior;

        public bool Inserted { get; private set; }

        /// <summary>Above this, a Ringtail coming off the night shift does not bother going to bed at dawn.</summary>
        private const float NearlyRested = 0.75f;
        private int _dawnSleepDay = -1;

        private readonly RingtailGatherings _gatherings;

        public RingtailRestRootBehavior(IDayNightCycle dayNightCycle, RingtailWorkday workday, RingtailService ringtailService,
                                        RingtailGatherings gatherings)
        {
            _dayNightCycle = dayNightCycle;
            _workday = workday;
            _ringtailService = ringtailService;
            _gatherings = gatherings;
        }

        /// <summary>Forgets what an earlier game of this session found (RingtailService.Load).</summary>
        internal static void NewGame()
        {
            InsertionError = null;
            _insertionErrorLogged = false;
        }

        /// <summary>True while a gathering goes before the rest (Core's IGatheringClock: the Lantern Festival's evening at
        /// the square, in this Ringtail's district). The rest then steps aside, and the behaviour below it, the gathering's
        /// own, takes the Ringtail there. This module does not know which module that is.</summary>
        public bool GathersNow => _gatherings.GathersNow(this);

        public void Awake()
        {
            _spec = GetComponent<PandabornRingtailSpec>();
            _behaviorManager = GetComponent<BehaviorManager>();
            _needManager = GetComponent<NeedManager>();
            _sleepNeedBehavior = GetComponent<SleepNeedBehavior>();
            _neederRootBehavior = GetComponent<NeederRootBehavior>();
            _wanderRootBehavior = GetComponent<WanderRootBehavior>();
        }

        /// <summary>Runs after every component's Awake, so BeaverBehaviorInitializer has filled the list by now.</summary>
        public void InitializeEntity()
        {
            if (_ringtailService.Enabled) Inserted = Insert();
        }

        private bool Insert()
        {
            try
            {
                if (RootBehaviorsField == null || !(RootBehaviorsField.GetValue(_behaviorManager) is List<RootBehavior> roots))
                    return Fail("BehaviorManager._rootBehaviors (List<RootBehavior>) not found");
                if (roots.Contains(this)) return true;
                int index = roots.FindIndex(r => r is WorkerRootBehavior);
                if (index < 0) index = roots.FindIndex(r => r is NeederRootBehavior);   // kits: no worker behaviour
                if (index < 0) return Fail("neither WorkerRootBehavior nor NeederRootBehavior is in the root behaviour list");
                roots.Insert(index, this);
                return true;
            }
            catch (Exception e)
            {
                return Fail(e.GetType().Name + ": " + e.Message);
            }
        }

        private static bool Fail(string reason)
        {
            InsertionError = reason;
            if (!_insertionErrorLogged)
            {
                _insertionErrorLogged = true;
                Debug.LogError("[Pandaborn.Ringtails] day rest unavailable: " + reason + ". Ringtails will work around the clock.");
            }
            return false;
        }

        /// <summary>Hours since the start of daytime (dawn), 0..24.</summary>
        public float HoursSinceDawn => _workday.HoursSinceDawn;

        /// <summary>
        /// End of the rest window in hours after dawn: the bell (RingtailWorkday: Bell's locked day when Bell is on, else the
        /// live slider) clamped to [RestMinEndHours, RestMaxEndHours] and to nightfall, so the rest ends exactly when the
        /// night posts open (ShiftMath.ShiftStart, the same call as RingtailWorkday.ShiftStartHours); or the fixed RestEndHours.
        /// </summary>
        public float RestEndHours
        {
            get
            {
                if (!_spec.RestEndsAtBell) return _spec.RestEndHours;
                return ShiftMath.ShiftStart(_workday.WorkdayHours, _spec.RestMinEndHours, _spec.RestMaxEndHours, _workday.Nightfall);
            }
        }

        public bool InRestWindow => ShiftMath.InWindow(HoursSinceDawn, _spec.RestStartHours, RestEndHours);


        public override Decision Decide(BehaviorAgent agent)
        {
            if (_broken) return Decision.ReleaseNow();
            // the game calls this from the colonist's tick: an exception here is a crash. If the rest ever throws, this
            // Ringtail goes back to the plain worker behaviour (it works around the clock and sleeps when exhausted).
            try { return DecideRest(agent); }
            catch (Exception e)
            {
                _broken = true;
                Fail("the rest behaviour threw " + e.GetType().Name + ": " + e.Message);
                return Decision.ReleaseNow();
            }
        }

        private bool _broken;

        private Decision DecideRest(BehaviorAgent agent)
        {
            if (!InRestWindow || GathersNow) return Decision.ReleaseNow();


            if (_sleepNeedBehavior != null && _needManager.HasNeed(SleepNeedId))
            {
                // first thing in the rest window: to bed unless nearly rested (a regular "sleep through the morning");
                // later in the window only when tired (SleepBelow)
                float points = _needManager.GetNeedPoints(SleepNeedId);
                bool dawnSleep = _dawnSleepDay != _dayNightCycle.DayNumber && points < NearlyRested;
                if (dawnSleep || points < _spec.SleepBelow)
                {
                    var sleep = _sleepNeedBehavior.Decide(agent);
                    if (!sleep.ShouldReleaseNow)
                    {
                        if (dawnSleep) _dawnSleepDay = _dayNightCycle.DayNumber;
                        return Decision.TransferNow(_sleepNeedBehavior, in sleep);
                    }
                }
            }
            if (_neederRootBehavior != null)
            {
                var need = _neederRootBehavior.Decide(agent);
                if (!need.ShouldReleaseNow) return need;
            }
            if (_wanderRootBehavior != null)
            {
                var wander = _wanderRootBehavior.Decide(agent);
                if (!wander.ShouldReleaseNow) return Decision.TransferNow(_wanderRootBehavior, in wander);
            }
            return Decision.ReleaseNextTick();
        }
    }
}
