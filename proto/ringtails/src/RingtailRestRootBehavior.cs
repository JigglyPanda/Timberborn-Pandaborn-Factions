using System;
using System.Collections.Generic;
using System.Reflection;
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
    public class RingtailRestRootBehavior : RootBehavior, IAwakableComponent, IInitializableEntity
    {
        private const string SleepNeedId = "Sleep";
        private static readonly FieldInfo RootBehaviorsField =
            typeof(BehaviorManager).GetField("_rootBehaviors", BindingFlags.Instance | BindingFlags.NonPublic);
        private static bool _insertionErrorLogged;

        /// <summary>Set when inserting into the behaviour list failed (the game changed). Ringtails then work around the clock.</summary>
        public static string InsertionError { get; private set; }

        private readonly IDayNightCycle _dayNightCycle;

        private PandabornRingtailSpec _spec;
        private BehaviorManager _behaviorManager;
        private NeedManager _needManager;
        private SleepNeedBehavior _sleepNeedBehavior;
        private NeederRootBehavior _neederRootBehavior;
        private WanderRootBehavior _wanderRootBehavior;

        public bool Inserted { get; private set; }

        public RingtailRestRootBehavior(IDayNightCycle dayNightCycle)
        {
            _dayNightCycle = dayNightCycle;
        }

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
            Inserted = Insert();
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
        public float HoursSinceDawn
        {
            get
            {
                float dawn = _dayNightCycle.BoundsInHours(TimeOfDay.Daytime).start;
                float h = _dayNightCycle.HoursPassedToday - dawn;
                return h < 0f ? h + 24f : h;
            }
        }

        public bool InRestWindow
        {
            get
            {
                float h = HoursSinceDawn;
                float start = _spec.RestStartHours, end = _spec.RestEndHours;
                return start <= end ? h >= start && h < end : h >= start || h < end;
            }
        }

        public override Decision Decide(BehaviorAgent agent)
        {
            if (!InRestWindow) return Decision.ReleaseNow();
            if (_sleepNeedBehavior != null && _needManager.HasNeed(SleepNeedId) && _needManager.GetNeedPoints(SleepNeedId) < _spec.SleepBelow)
            {
                var sleep = _sleepNeedBehavior.Decide(agent);
                if (!sleep.ShouldReleaseNow) return Decision.TransferNow(_sleepNeedBehavior, in sleep);
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
