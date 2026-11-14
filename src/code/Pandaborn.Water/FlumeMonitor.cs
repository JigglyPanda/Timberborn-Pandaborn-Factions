using System.Linq;
using Timberborn.BaseComponentSystem;
using Timberborn.BlockSystem;
using Timberborn.EntitySystem;
using Timberborn.Localization;
using Timberborn.StatusSystem;
using Timberborn.TickSystem;
using Timberborn.WaterBuildings;
using Timberborn.WaterSystem;
using UnityEngine;

namespace Pandaborn.Water
{
    /// <summary>
    /// Makes flume failures visible with the game's own building status icons (no silent failure). Each status says what
    /// to do next:
    /// <list type="bullet">
    /// <item>Blocked: the tile after the piece is solid (terrain, a levee, a corner post).</item>
    /// <item>Misaligned: the flume ahead or behind runs another way (a bend without a Flume Corner).</item>
    /// <item>No water can enter: first piece of a run, dry, and the water behind it is not above its bed.</item>
    /// <item>Dry end: last piece of a run, dry for about a minute, while water does enter the run.</item>
    /// </list>
    /// Reads only the thread-safe water snapshot; checks every 30 ticks, spread over pieces.
    /// </summary>
    public class FlumeMonitor : TickableComponent, IAwakableComponent, IInitializableEntity, IFinishedStateListener
    {
        private const int Interval = 30;
        private const int DryChecksBeforeAlarm = 4;
        private const float WetDepth = 0.005f;

        private readonly IThreadSafeWaterMap _waterMap;
        private readonly IBlockService _blockService;
        private readonly ILoc _loc;
        private FlumeSegment _segment;
        private FlumeGate _gate;
        private StatusToggle _blocked, _misaligned, _intakeDry, _endDry;
        private int _countdown, _dryChecks;

        public FlumeMonitor(IThreadSafeWaterMap waterMap, IBlockService blockService, ILoc loc)
        {
            _waterMap = waterMap;
            _blockService = blockService;
            _loc = loc;
        }

        public bool Blocked => _blocked.IsActive;
        public bool Misaligned => _misaligned.IsActive;
        public bool IntakeDry => _intakeDry.IsActive;
        public bool EndDry => _endDry.IsActive;

        public void Awake()
        {
            _segment = GetComponent<FlumeSegment>();
            _gate = GetComponent<FlumeGate>();
            _blocked = Make("UnreachableObject", "Blocked");
            _misaligned = Make("GenericError", "Misaligned");
            _intakeDry = Make("BuildingNeedsWater", "IntakeDry");
            _endDry = Make("NotEnoughWater", "EndDry");
            DisableComponent();
        }

        private StatusToggle Make(string sprite, string key) =>
            StatusToggle.CreateNormalStatusWithFloatingIcon(sprite, _loc.T("Pandaborn.Water.Status." + key));

        public void InitializeEntity()
        {
            var subject = GetComponent<StatusSubject>();
            if (subject == null) return;
            subject.RegisterStatus(_blocked);
            subject.RegisterStatus(_misaligned);
            subject.RegisterStatus(_intakeDry);
            subject.RegisterStatus(_endDry);
        }

        public void OnEnterFinishedState()
        {
            _countdown = 1 + Mathf.Abs(GetComponent<BlockObject>().Coordinates.GetHashCode()) % Interval;
            EnableComponent();
        }

        public void OnExitFinishedState()
        {
            DisableComponent();
            _blocked.Deactivate();
            _misaligned.Deactivate();
            _intakeDry.Deactivate();
            _endDry.Deactivate();
        }

        public override void Tick()
        {
            if (--_countdown > 0) return;
            _countdown = Interval;
            if (!_segment.Active || _segment.WorldFlowCells.Count == 0) return;
            Evaluate();
        }

        private void Evaluate()
        {
            var cells = _segment.WorldFlowCells;
            var dir = _segment.Offset;
            var first = cells[0];
            var last = cells[cells.Count - 1];
            var ahead = last + dir;
            var behind = first - dir;

            var nextDir = DirectionAt(ahead, out bool nextIsFlume);
            var prevDir = DirectionAt(behind, out bool prevIsFlume);
            bool solidAhead = !_waterMap.TryGetColumnFloor(ahead, out int floorAhead) || floorAhead > ahead.z;
            _blocked.Toggle(solidAhead && !nextIsFlume);
            _misaligned.Toggle((nextIsFlume && nextDir != dir) || (prevIsFlume && prevDir != dir));

            // a closed gate is its own status; its intake is not "dry"
            bool gateClosed = _gate != null && !_gate.IsOpen;
            bool isIntake = !prevIsFlume;
            _intakeDry.Toggle(isIntake && !gateClosed && _waterMap.WaterDepth(first) < WetDepth
                              && _waterMap.WaterHeightOrFloor(behind) <= first.z + 0.001f);

            bool isEnd = !nextIsFlume;
            if (isEnd && _waterMap.WaterDepth(last) < WetDepth) _dryChecks++;
            else _dryChecks = 0;
            _endDry.Toggle(isEnd && !isIntake && _dryChecks >= DryChecksBeforeAlarm);
        }

        /// <summary>Flow direction of a flume flow cell or vanilla valve channel cell at (or one level below) the cell.</summary>
        private Vector3Int DirectionAt(Vector3Int cell, out bool found)
        {
            for (int dz = 0; dz >= -1; dz--)
            {
                var c = cell + new Vector3Int(0, 0, dz);
                if (!_blockService.Contains(c)) continue;
                foreach (var bo in _blockService.GetObjectsAt(c))
                {
                    var segment = bo.GetComponent<FlumeSegment>();
                    if (segment != null && segment.WorldFlowCells.Contains(c)) { found = true; return segment.Offset; }
                    if ((bo.GetComponent<ThrottlingValve>() != null || bo.GetComponent<FillValve>() != null) && bo.Coordinates == c)
                    {
                        found = true;
                        return FlumeSegment.OffsetOf(bo.Orientation.ToFlowDirection());
                    }
                }
            }
            found = false;
            return Vector3Int.zero;
        }
    }
}
