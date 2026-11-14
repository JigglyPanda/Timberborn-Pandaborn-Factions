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
    /// Makes flume failures visible with the game's own building status icons (no silent failure):
    /// <list type="bullet">
    /// <item>Blocked: the tile ahead is solid (terrain, a levee, a corner post) so water cannot leave.</item>
    /// <item>Misaligned: the flume ahead or behind runs in a different direction (a bend needs a Flume Corner).</item>
    /// <item>Intake dry: this is the first piece of a run and the water behind it is below its bed.</item>
    /// <item>End dry: this is the last piece of a run and no water has reached it for a while.</item>
    /// </list>
    /// Reads only the thread-safe water snapshot; re-evaluates every <see cref="Interval"/> ticks.
    /// </summary>
    public class FlumeMonitor : TickableComponent, IAwakableComponent, IInitializableEntity, IFinishedStateListener
    {
        private const int Interval = 30;
        private const int DryChecksBeforeAlarm = 4;     // about 72 game seconds without water at the end
        private const float WetDepth = 0.005f;

        private readonly IThreadSafeWaterMap _waterMap;
        private readonly IBlockService _blockService;
        private readonly ILoc _loc;
        private BlockObject _blockObject;
        private FlumeSegment _segment;
        private StatusToggle _blocked, _misaligned, _intakeDry, _endDry;
        private int _countdown;
        private int _dryChecks;

        public FlumeMonitor(IThreadSafeWaterMap waterMap, IBlockService blockService, ILoc loc)
        {
            _waterMap = waterMap;
            _blockService = blockService;
            _loc = loc;
        }

        public void Awake()
        {
            _blockObject = GetComponent<BlockObject>();
            _segment = GetComponent<FlumeSegment>();
            _blocked = StatusToggle.CreateNormalStatusWithFloatingIcon("UnreachableObject", _loc.T("Status.Pandaborn.Flume.Blocked"));
            _misaligned = StatusToggle.CreateNormalStatusWithFloatingIcon("GenericError", _loc.T("Status.Pandaborn.Flume.Misaligned"));
            _intakeDry = StatusToggle.CreateNormalStatusWithFloatingIcon("BuildingNeedsWater", _loc.T("Status.Pandaborn.Flume.IntakeDry"));
            _endDry = StatusToggle.CreateNormalStatusWithFloatingIcon("NotEnoughWater", _loc.T("Status.Pandaborn.Flume.EndDry"));
            DisableComponent();
        }

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
            _countdown = Mathf.Abs(_blockObject.Coordinates.GetHashCode()) % Interval;   // spread the checks over ticks
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
            Evaluate();
        }

        private void Evaluate()
        {
            var cells = _segment.WorldFlowCells;
            if (cells.Count == 0) return;
            var dir = _segment.Offset;
            var first = cells[0];
            var last = cells[cells.Count - 1];
            var ahead = last + dir;
            var behind = first - dir;

            // ahead: solid? another flume in another direction?
            bool solidAhead = !_waterMap.TryGetColumnFloor(ahead, out int floorAhead) || floorAhead > ahead.z;
            var nextDir = DirectionAt(ahead, out bool nextIsFlume);
            var prevDir = DirectionAt(behind, out bool prevIsFlume);
            bool misaligned = (nextIsFlume && nextDir != dir) || (prevIsFlume && prevDir != dir);
            _blocked.Toggle(solidAhead && !nextIsFlume);
            _misaligned.Toggle(misaligned);

            // intake: first piece of a run, water behind below the bed
            bool isIntake = !prevIsFlume;
            float behindHeight = _waterMap.WaterHeightOrFloor(behind);
            _intakeDry.Toggle(isIntake && _waterMap.WaterDepth(first) < WetDepth && behindHeight <= first.z + 0.001f);

            // end: last piece of a run that stays dry
            bool isEnd = !nextIsFlume;
            if (isEnd && _waterMap.WaterDepth(last) < WetDepth) _dryChecks++;
            else _dryChecks = 0;
            _endDry.Toggle(isEnd && _dryChecks >= DryChecksBeforeAlarm && !_intakeDry.IsActive);
        }

        /// <summary>Flow direction of a flume or vanilla valve channel cell at (or one level below) the cell.</summary>
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
