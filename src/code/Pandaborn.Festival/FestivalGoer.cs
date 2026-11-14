using System;
using System.Collections.Generic;
using System.Reflection;
using Pandaborn.Core;
using Timberborn.BaseComponentSystem;
using Timberborn.BehaviorSystem;
using Timberborn.Common;
using Timberborn.EntitySystem;
using Timberborn.GameDistricts;
using Timberborn.Effects;
using Timberborn.Navigation;
using Timberborn.NeedBehaviorSystem;
using Timberborn.NeedSystem;
using Timberborn.TemplateSystem;
using Timberborn.WalkingSystem;
using Timberborn.Wandering;
using Timberborn.WorkSystem;
using UnityEngine;

namespace Pandaborn.Festival
{
    /// <summary>
    /// A colonist's festival day (decorates PandabornFestivalGoerSpec: Inkpaw adult and cub, Ringtail adult and kit). A
    /// root behaviour placed just above WorkerRootBehavior (above NeederRootBehavior for the young), so carrying, critical
    /// needs, death and stranding still come first. Outside a festival day it does nothing. On the festival day:
    ///   * a worker at a KeepWorkingTemplates workplace (pumps, lifts) works as usual;
    ///   * by day everyone else runs the game's own need loop first (eat, drink, leisure, sleep), and when it has nothing
    ///     to do walks to a spot near the district's Festival Square and celebrates there for a while;
    ///   * at show time (dusk to late evening) everyone goes to the square first;
    ///   * with no square in its district a colonist simply has the day off (needs, then wandering).
    /// The first arrival at the square gives festive spirit at once.
    ///
    /// Inserting into the behaviour list uses one private field, BehaviorManager._rootBehaviors (the Ringtails' day rest
    /// uses the same field). It happens in PostInitializeEntity, after every InitializeEntity, so a Ringtail's rest (inserted
    /// in InitializeEntity) stays above it: a Ringtail sleeps through its morning as always, then joins the festival.
    /// Fallback (code rule 4): if the field is gone, or "simulate-missing-member: Festival.RootBehaviors", nobody takes the
    /// day off: the festival keeps its evening show, festive spirit and Tradition, and the panel says so.
    /// Nothing is saved: a reload restarts the current walk.
    /// </summary>
    public class FestivalGoer : RootBehavior, IAwakableComponent, IPostInitializableEntity, IDeletableEntity
    {
        private static readonly FieldInfo RootBehaviorsField =
            typeof(BehaviorManager).GetField("_rootBehaviors", BindingFlags.Instance | BindingFlags.NonPublic);
        private static bool _errorLogged;

        /// <summary>Why the day off is unavailable (the game changed), or null.</summary>
        public static string InsertionError { get; private set; }

        private readonly FestivalService _festivalService;
        private readonly IDistrictService _districtService;
        private readonly IRandomNumberGenerator _random;

        private BehaviorManager _behaviorManager;
        private Worker _worker;
        private Citizen _citizen;
        private NeedManager _needManager;
        private NeederRootBehavior _neederRootBehavior;
        private WanderRootBehavior _wanderRootBehavior;
        private WalkToPositionExecutor _walkToPositionExecutor;
        private WaitExecutor _waitExecutor;
        private bool _walked;

        public FestivalGoer(FestivalService festivalService, IDistrictService districtService, IRandomNumberGenerator random)
        {
            _festivalService = festivalService;
            _districtService = districtService;
            _random = random;
        }

        public bool Inserted { get; private set; }

        /// <summary>What this colonist did last on a festival day (tests).</summary>
        public string Doing { get; private set; } = "";

        public void Awake()
        {
            _behaviorManager = GetComponent<BehaviorManager>();
            _worker = GetComponent<Worker>();
            _citizen = GetComponent<Citizen>();
            _needManager = GetComponent<NeedManager>();
            _neederRootBehavior = GetComponent<NeederRootBehavior>();
            _wanderRootBehavior = GetComponent<WanderRootBehavior>();
            _walkToPositionExecutor = GetComponent<WalkToPositionExecutor>();
            _waitExecutor = GetComponent<WaitExecutor>();
        }

        public void PostInitializeEntity()
        {
            if (!_festivalService.Active) return;
            _festivalService.AddGoer(this);
            Inserted = Insert();
        }

        public void DeleteEntity()
        {
            _festivalService.RemoveGoer(this);
        }

        /// <summary>Checks the private member once, before any colonist needs it; null when the day off is available.</summary>
        public static string CheckInsertion()
        {
            if (FeatureRegistry.DevFlag("simulate-missing-member", "Festival.RootBehaviors"))
                InsertionError = "simulated: BehaviorManager._rootBehaviors missing";
            else if (RootBehaviorsField == null || !typeof(List<RootBehavior>).IsAssignableFrom(RootBehaviorsField.FieldType))
                InsertionError = "BehaviorManager._rootBehaviors (List<RootBehavior>) not found";
            return InsertionError;
        }

        private bool Insert()
        {
            try
            {
                if (InsertionError != null) return Fail(InsertionError);
                if (!(RootBehaviorsField.GetValue(_behaviorManager) is List<RootBehavior> roots))
                    return Fail("BehaviorManager._rootBehaviors (List<RootBehavior>) not found");
                if (roots.Contains(this)) return true;
                int index = roots.FindIndex(r => r is WorkerRootBehavior);
                if (index < 0) index = roots.FindIndex(r => r is NeederRootBehavior);
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
            if (!_errorLogged)
            {
                _errorLogged = true;
                Debug.LogWarning("[Pandaborn.Festival] the festival day off is unavailable: " + reason
                                 + ". Festivals keep their evening show, festive spirit and Tradition; colonists keep working.");
            }
            return false;
        }

        /// <summary>This colonist works through the festival (a pump or lift crew).</summary>
        public bool KeepsWorking
        {
            get
            {
                if (_worker == null || !_worker.Employed || !_worker.Workplace) return false;
                var template = _worker.Workplace.GetComponent<TemplateSpec>();
                return template != null && _festivalService.KeepsWorking(template.TemplateName);
            }
        }

        public override Decision Decide(BehaviorAgent agent)
        {
            if (!_festivalService.IsHoliday) return Decision.ReleaseNow();
            if (KeepsWorking) { Doing = "working (keeps working)"; return Decision.ReleaseNow(); }
            bool show = _festivalService.IsShowTime;
            if (!show && _neederRootBehavior != null)
            {
                var need = _neederRootBehavior.Decide(agent);
                if (!need.ShouldReleaseNow) { Doing = "needs"; return need; }
            }
            var district = _citizen ? _citizen.AssignedDistrict : null;
            var square = _festivalService.SquareFor(district);
            if (square == null || district.District == null) return DayOff(agent, show);
            if (!_walked)
            {
                _walked = true;
                // the nearest of a few random spots around the square, so the crowd gathers on and beside it
                var target = _districtService.GetRandomDestinationInDistrict(district.District, square.Center);
                for (int i = 0; i < 4; i++)
                {
                    var other = _districtService.GetRandomDestinationInDistrict(district.District, square.Center);
                    if ((other - square.Center).sqrMagnitude < (target - square.Center).sqrMagnitude) target = other;
                }
                switch (_walkToPositionExecutor.Launch(target))
                {
                    case ExecutorStatus.Running:
                        Doing = "walking to the square";
                        return Decision.ReturnWhenFinished(_walkToPositionExecutor);
                    case ExecutorStatus.Failure:
                        _walked = false;
                        return DayOff(agent, show);
                }
            }
            _walked = false;
            _festivalService.Attend(this);
            Doing = show ? "at the square (show)" : "at the square";
            _waitExecutor.LaunchForSpecifiedTime(_random.Range(0.3f, 0.8f));
            return Decision.ReleaseWhenFinished(_waitExecutor);
        }

        private Decision DayOff(BehaviorAgent agent, bool show)
        {
            if (show && _neederRootBehavior != null)
            {
                var need = _neederRootBehavior.Decide(agent);
                if (!need.ShouldReleaseNow) { Doing = "needs"; return need; }
            }
            if (_wanderRootBehavior != null)
            {
                var wander = _wanderRootBehavior.Decide(agent);
                if (!wander.ShouldReleaseNow) { Doing = "day off"; return Decision.TransferNow(_wanderRootBehavior, in wander); }
            }
            Doing = "day off";
            return Decision.ReleaseNextTick();
        }

        /// <summary>Raises a need to its maximum (festive spirit). False when the colonist does not have that need.</summary>
        internal bool FillNeed(string needId)
        {
            if (string.IsNullOrEmpty(needId) || _needManager == null || !_needManager.HasNeed(needId)) return false;
            float points = _needManager.NeedPointsToMax(needId);
            if (points > 0f) _needManager.ApplyEffect(new InstantEffect(needId, points, 1));
            return true;
        }

        public float NeedPoints(string needId) =>
            !string.IsNullOrEmpty(needId) && _needManager != null && _needManager.HasNeed(needId) ? _needManager.GetNeedPoints(needId) : -1f;
    }
}
