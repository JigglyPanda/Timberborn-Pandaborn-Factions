using System.Collections.Generic;
using System.Linq;
using Pandaborn.Specs;
using Timberborn.BaseComponentSystem;
using Timberborn.BlockSystem;
using Timberborn.SingletonSystem;
using Timberborn.TickSystem;
using Timberborn.WaterObjects;
using Timberborn.WaterSystem;
using UnityEngine;

namespace Pandaborn.Water
{
    /// <summary>
    /// Applies flume pieces one tick after they are finished (or loaded). The delay matters: every piece also carries a
    /// vanilla full water obstacle over its flow cells (the module-off fallback, an inert block), which vanilla adds in
    /// its own finished-state listener; we lift it through the vanilla <see cref="WaterObstacle"/> component (so vanilla's
    /// own bookkeeping stays right when the piece is later demolished) only after it has certainly been added. Openings
    /// run first, solid cells second, so a Drop's leg is re-solidified after the vanilla obstacle over it is lifted.
    /// </summary>
    public class FlumeService : ITickableSingleton
    {
        private readonly List<FlumeSegment> _segments = new List<FlumeSegment>();
        private readonly List<SolidCells> _solids = new List<SolidCells>();

        public void Enqueue(FlumeSegment segment)
        {
            if (!_segments.Contains(segment)) _segments.Add(segment);
        }

        public void Enqueue(SolidCells solid)
        {
            if (!_solids.Contains(solid)) _solids.Add(solid);
        }

        public void Dequeue(FlumeSegment segment) => _segments.Remove(segment);

        public void Dequeue(SolidCells solid) => _solids.Remove(solid);

        public void Tick()
        {
            if (_segments.Count > 0)
            {
                var segments = _segments.ToList();
                _segments.Clear();
                foreach (var s in segments) if (s) s.Activate();
            }
            if (_solids.Count > 0)
            {
                var solids = _solids.ToList();
                _solids.Clear();
                foreach (var s in solids) if (s) s.Activate();
            }
        }
    }

    /// <summary>
    /// A flume piece: direction limiters on its flow cells (PandabornFlumeSegmentSpec), so water moves only along the
    /// arrow and never through the side faces; the vanilla inert obstacle over the flow cells is lifted. Limiters are not
    /// saved by the game: they are re-applied on every load. Not tickable.
    /// </summary>
    public class FlumeSegment : BaseComponent, IAwakableComponent, IFinishedStateListener
    {
        private readonly IWaterService _waterService;
        private readonly FlumeService _flumeService;
        private readonly List<Vector3Int> _worldCells = new List<Vector3Int>();
        private BlockObject _blockObject;
        private PandabornFlumeSegmentSpec _spec;
        private WaterObstacle _inertObstacle;

        public FlumeSegment(IWaterService waterService, FlumeService flumeService)
        {
            _waterService = waterService;
            _flumeService = flumeService;
        }

        /// <summary>True once the limiters are in place and the inert obstacle is lifted.</summary>
        public bool Active { get; private set; }

        /// <summary>World coordinates of the flow cells (valid while active).</summary>
        public IReadOnlyList<Vector3Int> WorldFlowCells => _worldCells;

        /// <summary>One tile along the flow.</summary>
        public Vector3Int Offset => OffsetOf(_blockObject.Orientation.ToFlowDirection());

        public BlockObject BlockObject => _blockObject;

        public static Vector3Int OffsetOf(FlowDirection direction)
        {
            switch (direction)
            {
                case FlowDirection.Top: return new Vector3Int(0, 1, 0);
                case FlowDirection.Right: return new Vector3Int(1, 0, 0);
                case FlowDirection.Bottom: return new Vector3Int(0, -1, 0);
                case FlowDirection.Left: return new Vector3Int(-1, 0, 0);
                default: return Vector3Int.zero;
            }
        }

        public void Awake()
        {
            _blockObject = GetComponent<BlockObject>();
            _spec = GetComponent<PandabornFlumeSegmentSpec>();
            _inertObstacle = GetComponent<WaterObstacle>();
        }

        public void OnEnterFinishedState()
        {
            _worldCells.Clear();
            foreach (var c in _spec.FlowCells) _worldCells.Add(_blockObject.TransformCoordinates(c));
            _flumeService.Enqueue(this);
        }

        public void OnExitFinishedState()
        {
            _flumeService.Dequeue(this);
            if (!Active) return;
            foreach (var cell in _worldCells) _waterService.RemoveDirectionLimiter(cell);
            Active = false;
            Deactivated?.Invoke();
        }

        public event System.Action Activated;

        public event System.Action Deactivated;

        internal void Activate()
        {
            if (Active || !_blockObject.IsFinished) return;
            var direction = _blockObject.Orientation.ToFlowDirection();
            foreach (var cell in _worldCells) _waterService.AddDirectionLimiter(cell, direction);
            _inertObstacle?.RemoveFromWaterService();   // no-op if the data has no inert obstacle
            Active = true;
            Activated?.Invoke();
        }

        /// <summary>Puts the vanilla inert obstacle back (a closed gate). Safe to call repeatedly.</summary>
        internal void CloseWithInertObstacle(float height)
        {
            _inertObstacle?.AddToWaterService(height);
        }

        internal void OpenInertObstacle()
        {
            _inertObstacle?.RemoveFromWaterService();
        }

        internal bool HasInertObstacle => _inertObstacle != null;
    }

    /// <summary>
    /// Full water obstacles at the cells of PandabornSolidCellsSpec, added by the module only (one tick after finishing, after
    /// any flume opening on the same piece) and removed when the piece is demolished.
    /// </summary>
    public class SolidCells : BaseComponent, IAwakableComponent, IFinishedStateListener
    {
        private readonly IWaterService _waterService;
        private readonly FlumeService _flumeService;
        private readonly List<Vector3Int> _added = new List<Vector3Int>();
        private BlockObject _blockObject;
        private PandabornSolidCellsSpec _spec;

        public SolidCells(IWaterService waterService, FlumeService flumeService)
        {
            _waterService = waterService;
            _flumeService = flumeService;
        }

        public void Awake()
        {
            _blockObject = GetComponent<BlockObject>();
            _spec = GetComponent<PandabornSolidCellsSpec>();
        }

        public void OnEnterFinishedState() => _flumeService.Enqueue(this);

        public void OnExitFinishedState()
        {
            _flumeService.Dequeue(this);
            foreach (var cell in _added) _waterService.RemoveFullObstacle(cell);
            _added.Clear();
        }

        internal void Activate()
        {
            if (_added.Count > 0 || !_blockObject.IsFinished) return;
            foreach (var c in _spec.Cells)
            {
                var cell = _blockObject.TransformCoordinates(c);
                _waterService.AddFullObstacle(cell);
                _added.Add(cell);
            }
        }
    }
}
