using System;
using System.Collections.Generic;
using System.Linq;
using Pandaborn.Core;
using Timberborn.BaseComponentSystem;
using Timberborn.BlockSystem;
using Timberborn.BuildingsNavigation;
using Timberborn.Demolishing;
using Timberborn.EntitySystem;
using Timberborn.Forestry;
using Timberborn.GameFactionSystem;
using Timberborn.Gathering;
using Timberborn.NaturalResourcesLifecycle;
using Timberborn.Planting;
using Timberborn.SingletonSystem;
using Timberborn.TickSystem;
using Timberborn.TimeSystem;
using UnityEngine;

namespace Pandaborn.Customs
{
    /// <summary>
    /// "A grove that dies comes back by itself." The game's replant option covers dead trees only: Forester.Validate
    /// accepts a blocked planting spot when the blocker has a TreeComponent. A dead bush (tea, Sichuan pepper: planted by
    /// the forester, picked by the gatherer, no TreeComponent) blocks its planting mark until the player demolishes it.
    ///
    /// In a game of our faction this service removes such a bush a day after it was first seen waiting, and the forester
    /// then plants the empty mark as it plants any other. A plant is removed only while all of this holds, at every look
    /// during that day:
    /// * it is the blocker of a planting mark (PlantingService.TryGetPlantingBlocker, what the game's own planters ask),
    ///   and the mark is for its own species: a wild bush off a mark, or one the player marked for something else, is
    ///   never touched;
    /// * it is dead, has a Gatherable and no TreeComponent (dead trees are the game's own business), and is not marked
    ///   for demolition (then a builder is already on the way);
    /// * a finished forester building whose range covers the tile plants that species and has "replant dead trees"
    ///   switched on: the player's one checkbox governs trees and bushes alike.
    /// Kinds are found by these data, never by name. It looks once per in-game hour and removes entities only inside
    /// the singleton tick. Nothing is saved (after a load the day starts over). Other factions' games: inactive.
    /// Module off: dead bushes stay until demolished, as in the plain game.
    /// </summary>
    public class DeadBushClearing : ILoadableSingleton, ITickableSingleton
    {
        /// <summary>How long a dead bush waits, in days.</summary>
        public const float DelayDays = 1f;
        private const float LookEveryDays = 1f / 24f;

        private readonly FactionService _factionService;
        private readonly PlantingService _plantingService;
        private readonly EntityService _entityService;
        private readonly IDayNightCycle _dayNightCycle;
        private readonly List<ForesterWatch> _foresters = new List<ForesterWatch>();
        private readonly DeadBushLedger _ledger = new DeadBushLedger();
        private readonly List<BlockObject> _due = new List<BlockObject>();
        private bool _active;
        private bool _failed;
        private float _nextLook;

        public DeadBushClearing(FactionService factionService, PlantingService plantingService, EntityService entityService, IDayNightCycle dayNightCycle)
        {
            _factionService = factionService;
            _plantingService = plantingService;
            _entityService = entityService;
            _dayNightCycle = dayNightCycle;
        }

        /// <summary>Dead bushes removed in this session, and how many wait now (for tests).</summary>
        public static int Cleared { get; private set; }

        public static int Waiting { get; private set; }

        public void Load()
        {
            try { _active = _factionService.Current?.Id == FeatureNotices.FactionId; }
            catch (Exception) { _active = false; }
        }

        internal void Add(ForesterWatch forester)
        {
            if (!_foresters.Contains(forester)) _foresters.Add(forester);
        }

        internal void Remove(ForesterWatch forester) => _foresters.Remove(forester);

        public void Tick()
        {
            if (!_active || _failed) return;
            try
            {
                float now = _dayNightCycle.PartialDayNumber;
                if (now < _nextLook && now > _nextLook - 2f * LookEveryDays) return;
                _nextLook = now + LookEveryDays;
                Look(now);
            }
            catch (Exception e)
            {
                // an exception in a tick is a crash of the game: this piece goes quiet instead
                _failed = true;
                _ledger.Clear();
                Debug.LogError("[Pandaborn.Customs] clearing dead bushes failed and is off until this game is left: " + e);
            }
        }

        private void Look(float now)
        {
            var replanting = _foresters.Where(f => f.Replants).ToList();
            if (replanting.Count == 0)
            {
                _ledger.Clear();
                Waiting = 0;
                return;
            }
            _due.Clear();
            _ledger.Begin();
            foreach (var tile in _plantingService.PlantingCoordinates.ToList())
            {
                string species = _plantingService.GetResourceAt(tile);
                if (species == null || !_plantingService.TryGetPlantingBlocker(tile, out var blocker) || !blocker) continue;
                if (!IsDeadBushOf(blocker, species)) continue;
                bool covered = false;
                for (int i = 0; i < replanting.Count && !covered; i++) covered = replanting[i].Covers(tile, species);
                if (!covered) continue;
                var entity = blocker.GetComponent<EntityComponent>();
                if (entity == null || entity.Deleted) continue;
                if (_ledger.Observe(entity.EntityId, now, DelayDays)) _due.Add(blocker);
            }
            _ledger.End();
            foreach (var bush in _due)
            {
                if (!bush) continue;
                var entity = bush.GetComponent<EntityComponent>();
                if (entity == null || entity.Deleted) continue;
                _ledger.Forget(entity.EntityId);
                _entityService.Delete(bush);
                Cleared++;
            }
            _due.Clear();
            Waiting = _ledger.Waiting;
        }

        /// <summary>A dead, gatherer-picked plant that is not a tree, standing on a planting mark for its own species.</summary>
        private static bool IsDeadBushOf(BlockObject plant, string markedSpecies)
        {
            var living = plant.GetComponent<LivingNaturalResource>();
            if (living == null || !living.IsDead) return false;
            if (plant.GetComponent<TreeComponent>() != null || plant.GetComponent<Gatherable>() == null) return false;
            var plantable = plant.GetComponent<PlantableSpec>();
            if (plantable == null || plantable.TemplateName != markedSpecies) return false;
            var demolishable = plant.GetComponent<Demolishable>();
            return demolishable == null || !demolishable.IsMarked;
        }
    }

    /// <summary>
    /// Tells DeadBushClearing about a finished forester building: whether its "replant dead trees" option is on, and
    /// whether it plants a species on a tile (its own range and its own list of plantables, both the game's). Decorates
    /// the game's Forester; does nothing by itself and saves nothing.
    /// </summary>
    public class ForesterWatch : BaseComponent, IAwakableComponent, IFinishedStateListener, IDeletableEntity
    {
        private readonly DeadBushClearing _clearing;
        private Forester _forester;
        private BuildingTerrainRange _range;
        private PlanterBuilding _planter;

        public ForesterWatch(DeadBushClearing clearing)
        {
            _clearing = clearing;
        }

        public void Awake()
        {
            _forester = GetComponent<Forester>();
            _range = GetComponent<BuildingTerrainRange>();
            _planter = GetComponent<PlanterBuilding>();
        }

        public bool Replants => _forester != null && _forester.ReplantDeadTrees;

        public bool Covers(Vector3Int tile, string species) =>
            _range != null && _planter != null && _planter.CanPlant(species) && _range.GetRange().Contains(tile);

        // The game treats an exception in a finished-state listener as a failed load: these only touch a list.
        public void OnEnterFinishedState()
        {
            if (_forester != null) _clearing.Add(this);
        }

        public void OnExitFinishedState() => _clearing.Remove(this);

        public void DeleteEntity() => _clearing.Remove(this);
    }
}
