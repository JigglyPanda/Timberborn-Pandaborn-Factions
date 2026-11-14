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

        private const float FlowingSpeed = 0.03f;   // a backed-up, standing line moves about 0.01; a running one 0.1 and more

        private readonly IThreadSafeWaterMap _waterMap;
        private readonly IBlockService _blockService;
        private readonly ILoc _loc;
        private readonly WaterSounds _sounds;
        private readonly CisternTapHint _hint;
        private FlumeSegment _segment;
        private FlumeGate _gate;
        private StatusSubject _subject;
        private StatusToggle _blocked, _misaligned, _intakeDry, _intakeDryWithHint, _endDry;
        private int _countdown, _dryChecks;
        private bool _hadWater, _endWet;
        private GameObject _emitter;

        public FlumeMonitor(IThreadSafeWaterMap waterMap, IBlockService blockService, ILoc loc, WaterSounds sounds, CisternTapHint hint)
        {
            _waterMap = waterMap;
            _blockService = blockService;
            _loc = loc;
            _sounds = sounds;
            _hint = hint;
        }

        /// <summary>True while this piece reports flowing water to the flume sound (for tests).</summary>
        public bool Flowing { get; private set; }

        /// <summary>True while the dry-intake status carries the Cistern Tap hint (for tests).</summary>
        public bool ShowsTapHint => _intakeDryWithHint != null && _intakeDryWithHint.IsActive;

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
            _subject = subject;
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
            _intakeDryWithHint?.Deactivate();
            _endDry.Deactivate();
            SetFlowing(false);
            _endWet = false;
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
            bool firstWet = _waterMap.WaterDepth(first) >= WetDepth;
            if (firstWet) _hadWater = true;
            bool intakeDry = isIntake && !gateClosed && !firstWet && _waterMap.WaterHeightOrFloor(behind) <= first.z + 0.001f;
            // a Flume Gate whose water has gone (a dried-up source, a drought): stored water can be poured in
            bool hinted = intakeDry && _gate != null && (_hadWater || _hint.InDrought) && _hint.Available && EnsureHinted();
            _intakeDry.Toggle(intakeDry && !hinted);
            _intakeDryWithHint?.Toggle(hinted);

            bool isEnd = !nextIsFlume;
            bool lastWet = _waterMap.WaterDepth(last) >= WetDepth;
            if (isEnd && !lastWet) _dryChecks++;
            else _dryChecks = 0;
            _endDry.Toggle(isEnd && !isIntake && _dryChecks >= DryChecksBeforeAlarm);

            // sound: the loop where water runs; the tok when water first reaches the end of a run (once per fill)
            bool flowing = false;
            foreach (var c in cells)
                if (_waterMap.WaterDepth(c) >= WetDepth && _waterMap.WaterFlowDirection(c).magnitude >= FlowingSpeed) { flowing = true; break; }
            SetFlowing(flowing);
            if (isEnd && !isIntake && lastWet && !_endWet) _sounds.Tok(Emitter);
            _endWet = isEnd && lastWet;
        }

        private void SetFlowing(bool flowing)
        {
            if (Flowing == flowing || _segment == null) return;
            Flowing = flowing;
            foreach (var c in _segment.WorldFlowCells) _sounds.SetFlowing(new Vector2Int(c.x, c.y), flowing);
        }

        /// <summary>A child object for the tok: a selected building's own object carries the UI mixer.</summary>
        private GameObject Emitter
        {
            get
            {
                if (!_emitter)
                {
                    _emitter = new GameObject("PandabornFlumeSounds");
                    _emitter.transform.SetParent(Transform, false);
                    _emitter.transform.localPosition = new Vector3(0.5f, 0.5f, 0.5f);
                }
                return _emitter;
            }
        }

        private bool EnsureHinted()
        {
            if (_intakeDryWithHint != null) return true;
            if (_subject == null || _hint.Sentence == null) return false;
            _intakeDryWithHint = StatusToggle.CreateNormalStatusWithFloatingIcon("BuildingNeedsWater",
                _loc.T("Pandaborn.Water.Status.IntakeDry") + " " + _hint.Sentence);
            _subject.RegisterStatus(_intakeDryWithHint);
            return true;
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
