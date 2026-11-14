using System;
using System.Collections.Generic;
using System.Reflection;
using Pandaborn.Core;
using Timberborn.BaseComponentSystem;
using Timberborn.BehaviorSystem;
using Timberborn.Common;
using Timberborn.EnterableSystem;
using Timberborn.EntitySystem;
using Timberborn.GameDistricts;
using Timberborn.Effects;
using Timberborn.Navigation;
using Timberborn.NeedBehaviorSystem;
using Timberborn.NeedSystem;
using Timberborn.TemplateSystem;
using Timberborn.TimeSystem;
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
    ///     to do goes to the district's Festival Square: onto a free dance slot (the square's enterable slots, entered as
    ///     the game's attractions are, with the square's attraction effects), or, when all are taken, to a spot just
    ///     outside its edge, and celebrates there for a while;
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
        private WalkInsideExecutor _walkInsideExecutor;
        private Enterer _enterer;
        private ApplyEffectExecutor _applyEffectExecutor;
        private readonly List<ContinuousEffect> _effects = new List<ContinuousEffect>();
        private readonly IDayNightCycle _dayNightCycle;
        private bool _walked;

        public FestivalGoer(FestivalService festivalService, IDistrictService districtService, IRandomNumberGenerator random,
                            IDayNightCycle dayNightCycle)
        {
            _festivalService = festivalService;
            _districtService = districtService;
            _random = random;
            _dayNightCycle = dayNightCycle;
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
            _walkInsideExecutor = GetComponent<WalkInsideExecutor>();
            _enterer = GetComponent<Enterer>();
            _applyEffectExecutor = GetComponent<ApplyEffectExecutor>();
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
            // first onto the square's own dance slots (the Dance Hall basis: 20 slots in rings round the pole), as the
            // game's attractions do; only the overflow gathers around its edges
            var dance = Dance(square, show);
            if (dance.HasValue) return dance.Value;
            if (!_walked)
            {
                _walked = true;
                var near = NearSpot(district, square);
                var status = _walkToPositionExecutor.Launch(EdgeSpot(square, near));
                if (status == ExecutorStatus.Failure) status = _walkToPositionExecutor.Launch(near);
                switch (status)
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

        /// <summary>
        /// Onto a free dance slot of the square, as the game's attraction behaviour enters one (WalkInsideExecutor; the
        /// slots carry the Dance Hall basis' "Dancing" animation, which both peoples' bodies have), then a stay there with
        /// the square's attraction effects. Null when the square has no slots, all are taken, or the colonist cannot enter.
        /// </summary>
        private Decision? Dance(FestivalSquare square, bool show)
        {
            var enterable = square.Enterable;
            if (!enterable || !_walkInsideExecutor || !_enterer || !_waitExecutor) return null;
            if (_enterer.CurrentBuilding != enterable && (_enterer.IsInside || !enterable.CanReserveSlot)) return null;
            switch (_walkInsideExecutor.Launch(enterable))
            {
                case ExecutorStatus.Running:
                    Doing = "walking to the square";
                    return Decision.ReturnWhenFinished(_walkInsideExecutor);
                case ExecutorStatus.Failure:
                    return null;
            }
            if (_enterer.CurrentBuilding != enterable) return null;
            _walked = false;
            _festivalService.Attend(this);
            Doing = show ? "dancing (show)" : "dancing";
            float hours = _random.Range(0.5f, 1.0f);
            if (square.Attraction && _applyEffectExecutor)
            {
                _effects.Clear();
                square.Attraction.GetEfficiencyAdjustedEffects(_effects);
                _applyEffectExecutor.LaunchToTimestamp(_effects, _dayNightCycle.DayNumberHoursFromNow(hours));
                _effects.Clear();
                return Decision.ReleaseWhenFinished(_applyEffectExecutor);
            }
            _waitExecutor.LaunchForSpecifiedTime(hours);
            return Decision.ReleaseWhenFinished(_waitExecutor);
        }

        /// <summary>The nearest of a few random reachable spots in the district around the square.</summary>
        private Vector3 NearSpot(DistrictCenter district, FestivalSquare square)
        {
            var center = square.Center;
            var best = _districtService.GetRandomDestinationInDistrict(district.District, center);
            for (int i = 0; i < 4; i++)
            {
                var other = _districtService.GetRandomDestinationInDistrict(district.District, center);
                if ((other - center).sqrMagnitude < (best - center).sqrMagnitude) best = other;
            }
            return best;
        }

        /// <summary>A spot just outside the square's edge: the near spot if it is already within a step of the square,
        /// else a point on a ring 3.2 to 3.8 m from its centre (the caller falls back to the near spot if the ring point
        /// cannot be reached).</summary>
        private Vector3 EdgeSpot(FestivalSquare square, Vector3 near)
        {
            var center = square.Center;
            if ((near - center).sqrMagnitude <= 4.5f * 4.5f) return near;
            float angle = _random.Range(0f, 2f * Mathf.PI);
            float radius = _random.Range(3.2f, 3.8f);
            return center + new Vector3(Mathf.Cos(angle) * radius, 0f, Mathf.Sin(angle) * radius);
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
