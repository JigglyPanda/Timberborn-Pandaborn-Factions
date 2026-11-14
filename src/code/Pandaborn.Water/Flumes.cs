using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using Pandaborn.Core;
using Pandaborn.Specs;
using Timberborn.BaseComponentSystem;
using Timberborn.BlockSystem;
using Timberborn.SingletonSystem;
using Timberborn.TickSystem;
using Timberborn.TimeSystem;
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
        private readonly List<FlumeSegment> _restores = new List<FlumeSegment>();

        public void Enqueue(FlumeSegment segment)
        {
            if (!_segments.Contains(segment)) _segments.Add(segment);
        }

        public void Enqueue(SolidCells solid)
        {
            if (!_solids.Contains(solid)) _solids.Add(solid);
        }

        public void Dequeue(FlumeSegment segment)
        {
            _segments.Remove(segment);
            _restores.Remove(segment);
        }

        internal void EnqueueRestore(FlumeSegment segment)
        {
            if (!_restores.Contains(segment)) _restores.Add(segment);
        }

        public void Dequeue(SolidCells solid) => _solids.Remove(solid);

        public void Tick()
        {
            // water restores first: they were queued by last tick's activations, whose obstacle removals are applied by now
            if (_restores.Count > 0)
            {
                var restores = _restores.ToList();
                _restores.Clear();
                foreach (var s in restores) if (s) s.RestoreWater();
            }
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
    /// Loading cuts the water out of the flow cells: the game re-adds the inert obstacle when the piece enters its finished
    /// state, which deletes up to one block of water in each cell, before this module lifts it again. So when the piece
    /// has a PandabornEntityStateSpec, the depth and contamination of each flow cell are saved (entry "Water.Flume", with
    /// the game time) and put back one tick after the lift, but only if that entry was written by the save being loaded
    /// (same game time), never from an older save made while the module was on.
    /// </summary>
    public class FlumeSegment : BaseComponent, IAwakableComponent, IFinishedStateListener
    {
        private const string StateKey = "Water.Flume";
        private readonly IWaterService _waterService;
        private readonly FlumeService _flumeService;
        private readonly IThreadSafeWaterMap _waterMap;
        private readonly IDayNightCycle _dayNightCycle;
        private readonly List<Vector3Int> _worldCells = new List<Vector3Int>();
        private BlockObject _blockObject;
        private PandabornFlumeSegmentSpec _spec;
        private WaterObstacle _inertObstacle;
        private PandabornEntityState _state;
        private bool _restoreChecked;
        private bool _closed;
        private List<(float Depth, float Contamination)> _toRestore;

        public FlumeSegment(IWaterService waterService, FlumeService flumeService, IThreadSafeWaterMap waterMap,
                            IDayNightCycle dayNightCycle)
        {
            _waterService = waterService;
            _flumeService = flumeService;
            _waterMap = waterMap;
            _dayNightCycle = dayNightCycle;
        }

        /// <summary>Water put back into the flow cells after the last load (m3), for tests.</summary>
        public float RestoredWater { get; private set; }

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
            _state = GetComponent<PandabornEntityState>();
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
            _closed = false;
            Active = true;
            if (!_restoreChecked)
            {
                _restoreChecked = true;
                ReadSavedWater();
            }
            _state?.SetWriter(StateKey, 1, WriteWater);
            Activated?.Invoke();
        }

        private string WriteWater()
        {
            // only an open piece holds water; a closed gate keeps its obstacle and has nothing to put back
            if (!Active || _closed) return "";
            var parts = new List<string> { "t=" + _dayNightCycle.PartialDayNumber.ToString("R", CultureInfo.InvariantCulture) };
            foreach (var cell in _worldCells)
            {
                float depth = _waterMap.WaterDepth(cell);
                float c = depth > 0f ? _waterMap.ColumnContamination(cell) : 0f;
                parts.Add(depth.ToString("0.####", CultureInfo.InvariantCulture) + "," + c.ToString("0.####", CultureInfo.InvariantCulture));
            }
            return string.Join(";", parts);
        }

        private void ReadSavedWater()
        {
            if (_state == null || !_state.LoadedFromSave || !_state.TryGet(StateKey, out int version, out string payload) || version != 1
                || string.IsNullOrEmpty(payload)) return;
            var parts = payload.Split(';');
            if (parts.Length != _worldCells.Count + 1 || !parts[0].StartsWith("t=")
                || !float.TryParse(parts[0].Substring(2), NumberStyles.Float, CultureInfo.InvariantCulture, out float savedAt)) return;
            // written by the save being loaded? (an older entry survives sessions with the module off)
            if (Mathf.Abs(_dayNightCycle.PartialDayNumber - savedAt) > 0.01f) return;
            var list = new List<(float, float)>();
            for (int i = 1; i < parts.Length; i++)
            {
                var dc = parts[i].Split(',');
                if (dc.Length != 2 || !float.TryParse(dc[0], NumberStyles.Float, CultureInfo.InvariantCulture, out float d)
                    || !float.TryParse(dc[1], NumberStyles.Float, CultureInfo.InvariantCulture, out float c)) return;
                list.Add((Mathf.Clamp(d, 0f, 1f), Mathf.Clamp01(c)));   // the obstacle cut at most one block per cell
            }
            _toRestore = list;
            _flumeService.EnqueueRestore(this);
        }

        internal void RestoreWater()
        {
            var list = _toRestore;
            _toRestore = null;
            if (list == null || !Active || _closed || !_blockObject.IsFinished) return;
            float total = 0f;
            for (int i = 0; i < list.Count && i < _worldCells.Count; i++)
            {
                var (depth, c) = list[i];
                if (depth <= 0.0001f) continue;
                if (c < 1f) _waterService.AddCleanWater(_worldCells[i], depth * (1f - c));
                if (c > 0f) _waterService.AddContaminatedWater(_worldCells[i], depth * c);
                total += depth;
            }
            RestoredWater = total;
        }

        /// <summary>Puts the vanilla inert obstacle back (a closed gate). Safe to call repeatedly.</summary>
        internal void CloseWithInertObstacle(float height)
        {
            _inertObstacle?.AddToWaterService(height);
            _closed = _inertObstacle != null;
        }

        internal void OpenInertObstacle()
        {
            _inertObstacle?.RemoveFromWaterService();
            _closed = false;
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
