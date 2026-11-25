using System;
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
    /// Makes flume failures visible with the game's own building status icons (no silent failure). One cause gives one
    /// status, on the piece where the player can fix it (the rules are in <see cref="FlumeRules"/>):
    /// <list type="bullet">
    /// <item>Misaligned: the flume ahead or behind runs another way (a bend without a Flume Corner).</item>
    /// <item>Blocked: the tile after the piece is solid (terrain, a levee, a corner post).</item>
    /// <item>No water can enter: first piece of a run, dry, and the water behind it is not above its bed.</item>
    /// <item>Dry end: last piece of a run, dry for about four game hours, and no piece upstream already says why (a dry
    /// intake, a gate shut by badwater, a missing corner, a blocked piece).</item>
    /// </list>
    /// A run goes on through a Flume Corner's open cell: the piece that pours into the cell feeds the piece that leaves
    /// it, so the piece before a corner is not an end and the piece after it is not an intake. The last flume before a
    /// Paddy Spout is the end of its run.
    /// Reads only the thread-safe water snapshot; checks every 30 ticks, spread over pieces.
    /// </summary>
    public class FlumeMonitor : TickableComponent, IAwakableComponent, IInitializableEntity, IFinishedStateListener
    {
        private const int Interval = 30;
        private const float WetDepth = 0.005f;

        private const float FlowingSpeed = 0.03f;   // a backed-up, standing line moves about 0.01; a running one 0.1 and more

        private static readonly Vector3Int[] Sides =
        {
            new Vector3Int(1, 0, 0), new Vector3Int(-1, 0, 0), new Vector3Int(0, 1, 0), new Vector3Int(0, -1, 0)
        };

        private static readonly Func<FlumeMonitor, FlumeMonitor> UpstreamOf = m => m._upstream ? m._upstream : null;
        private static readonly Func<FlumeMonitor, bool> CauseOf = m => m.ShowsCause;

        private readonly IThreadSafeWaterMap _waterMap;
        private readonly IBlockService _blockService;
        private readonly ILoc _loc;
        private readonly WaterSounds _sounds;
        private readonly CisternTapHint _hint;
        private FlumeSegment _segment;
        private FlumeGate _gate;
        private StatusSubject _subject;
        private StatusToggle _blocked, _misaligned, _intakeDry, _intakeDryWithHint, _endDry;
        private FlumeMonitor _upstream;
        private FlumeStatus _status;
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

        /// <summary>The status shown at the last check.</summary>
        public FlumeStatus Status => _status;

        /// <summary>True while this piece shows the player why the pieces downstream get no water.</summary>
        public bool ShowsCause => FlumeRules.IsCause(_status, _gate != null && _gate.ClosedByBadwater);

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
            try
            {
                // spread the checks over pieces (never Math.Abs: it throws on int.MinValue)
                int hash = GetComponent<BlockObject>().Coordinates.GetHashCode() & 0x7fffffff;
                _countdown = 1 + hash % Interval;
                EnableComponent();
            }
            catch (Exception e) { WaterGuard.Report("starting a flume's status check", e); }
        }

        public void OnExitFinishedState()
        {
            try
            {
                DisableComponent();
                ClearStatuses();
                SetFlowing(false);
                _endWet = false;
                _upstream = null;
            }
            catch (Exception e) { WaterGuard.Report("stopping a flume's status check", e); }
        }

        private void ClearStatuses()
        {
            _status = FlumeStatus.None;
            _dryChecks = 0;
            _blocked.Deactivate();
            _misaligned.Deactivate();
            _intakeDry.Deactivate();
            _intakeDryWithHint?.Deactivate();
            _endDry.Deactivate();
        }

        public override void Tick()
        {
            if (--_countdown > 0) return;
            _countdown = Interval;
            try
            {
                if (_segment == null || !_segment.Active || _segment.WorldFlowCells.Count == 0) return;
                Evaluate();
            }
            catch (Exception e)
            {
                // a check that throws once would throw every time: this piece stops reporting, the flume itself works on
                WaterGuard.Report("a flume's status check", e);
                try { ClearStatuses(); SetFlowing(false); } catch (Exception) { }
                DisableComponent();
            }
        }

        private void Evaluate()
        {
            var cells = _segment.WorldFlowCells;
            var dir = _segment.Offset;
            var first = cells[0];
            var last = cells[cells.Count - 1];
            var ahead = last + dir;
            var behind = first - dir;

            var next = ChannelAt(ahead, out bool nextIsChannel, out var nextDir);
            var prev = ChannelAt(behind, out bool prevIsChannel, out var prevDir);
            // through an open cell (a Flume Corner): who pours into the cell behind, who leaves the cell ahead
            var feeder = prev != null ? prev : prevIsChannel ? null : FeederInto(behind);
            bool taker = next != null || (!nextIsChannel && AnyTakerFrom(ahead));
            _upstream = feeder != null ? feeder.GetComponent<FlumeMonitor>() : null;

            var facts = new FlumeFacts
            {
                SolidAhead = !_waterMap.TryGetColumnFloor(ahead, out int floorAhead) || floorAhead > ahead.z,
                NextIsChannel = nextIsChannel,
                NextMisaligned = nextIsChannel && nextDir != dir,
                PrevIsChannel = prevIsChannel,
                PrevMisaligned = prevIsChannel && prevDir != dir,
                HasFeeder = feeder != null,
                HasTaker = taker,
                GateClosed = _gate != null && !_gate.IsOpen,
                FirstCellWet = _waterMap.WaterDepth(first) >= WetDepth,
                LastCellWet = _waterMap.WaterDepth(last) >= WetDepth
            };
            if (facts.FirstCellWet) _hadWater = true;
            bool isIntake = FlumeRules.IsIntake(facts);
            bool isEnd = FlumeRules.IsEnd(facts);
            // read only where it matters (the cell behind an intake is one cell off the map at most: the water map has a margin)
            facts.WaterBehindAboveBed = !isIntake || facts.FirstCellWet || _waterMap.WaterHeightOrFloor(behind) > first.z + 0.001f;
            // walk upstream only for a dry end: a handful of steps, once every 30 ticks, on one piece per run
            facts.UpstreamShowsCause = isEnd && !isIntake && !facts.LastCellWet && FlumeRules.AnyUpstream(this, UpstreamOf, CauseOf);
            _dryChecks = FlumeRules.NextDryChecks(_dryChecks, facts);
            facts.DryChecks = _dryChecks;

            _status = FlumeRules.Resolve(facts);
            _blocked.Toggle(_status == FlumeStatus.Blocked);
            _misaligned.Toggle(_status == FlumeStatus.Misaligned);
            bool intakeDry = _status == FlumeStatus.IntakeDry;
            // a Flume Gate whose water has gone (a dried-up source, a drought): stored water can be poured in
            bool hinted = intakeDry && _gate != null && (_hadWater || _hint.InDrought) && _hint.Available && EnsureHinted();
            _intakeDry.Toggle(intakeDry && !hinted);
            _intakeDryWithHint?.Toggle(hinted);
            _endDry.Toggle(_status == FlumeStatus.EndDry);

            // sound: the loop where water runs; the tok when water first reaches the end of a run (once per fill)
            bool flowing = false;
            for (int i = 0; i < cells.Count; i++)
            {
                var c = cells[i];
                if (_waterMap.WaterDepth(c) >= WetDepth && _waterMap.WaterFlowDirection(c).magnitude >= FlowingSpeed) { flowing = true; break; }
            }
            SetFlowing(flowing);
            if (isEnd && !isIntake && facts.LastCellWet && !_endWet) _sounds.Tok(Emitter);
            _endWet = isEnd && facts.LastCellWet;
        }

        private void SetFlowing(bool flowing)
        {
            if (Flowing == flowing || _segment == null) return;
            Flowing = flowing;
            var cells = _segment.WorldFlowCells;
            for (int i = 0; i < cells.Count; i++) _sounds.SetFlowing(new Vector2Int(cells[i].x, cells[i].y), flowing);
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

        /// <summary>
        /// What carries water at (or one level below) the cell: a flume piece (returned), or a vanilla valve channel
        /// (returned null with <paramref name="isChannel"/> set). <paramref name="direction"/> is the way it runs.
        /// </summary>
        private FlumeSegment ChannelAt(Vector3Int cell, out bool isChannel, out Vector3Int direction)
        {
            for (int dz = 0; dz >= -1; dz--)
            {
                var c = new Vector3Int(cell.x, cell.y, cell.z + dz);
                if (!_blockService.Contains(c)) continue;
                var objects = _blockService.GetObjectsAt(c);
                for (int i = 0; i < objects.Count; i++)
                {
                    var bo = objects[i];
                    var segment = bo.GetComponent<FlumeSegment>();
                    if (segment != null && segment != _segment && Holds(segment, c))
                    {
                        isChannel = true;
                        direction = segment.Offset;
                        return segment;
                    }
                    if (bo.Coordinates == c && (bo.GetComponent<ThrottlingValve>() != null || bo.GetComponent<FillValve>() != null))
                    {
                        isChannel = true;
                        direction = FlumeSegment.OffsetOf(bo.Orientation.ToFlowDirection());
                        return null;
                    }
                }
            }
            isChannel = false;
            direction = Vector3Int.zero;
            return null;
        }

        /// <summary>The flume piece that pours into an open cell: its last flow cell is beside the cell (level with it or
        /// one above) and its arrow points at the cell.</summary>
        private FlumeSegment FeederInto(Vector3Int open)
        {
            for (int s = 0; s < Sides.Length; s++)
            {
                var from = open - Sides[s];
                for (int dz = 0; dz <= 1; dz++)
                {
                    var c = new Vector3Int(from.x, from.y, from.z + dz);
                    var segment = SegmentAt(c);
                    if (segment == null || !segment.Active || segment.WorldFlowCells.Count == 0) continue;
                    if (segment.Offset == Sides[s] && segment.WorldFlowCells[segment.WorldFlowCells.Count - 1] == c) return segment;
                }
            }
            return null;
        }

        /// <summary>True when a flume piece takes water out of an open cell: its first flow cell is beside the cell and its
        /// arrow points away from it.</summary>
        private bool AnyTakerFrom(Vector3Int open)
        {
            for (int s = 0; s < Sides.Length; s++)
            {
                var to = open + Sides[s];
                var segment = SegmentAt(to);
                if (segment == null || !segment.Active || segment.WorldFlowCells.Count == 0) continue;
                if (segment.Offset == Sides[s] && segment.WorldFlowCells[0] == to) return true;
            }
            return false;
        }

        /// <summary>Another flume piece with a flow cell exactly here.</summary>
        private FlumeSegment SegmentAt(Vector3Int c)
        {
            if (!_blockService.Contains(c)) return null;
            var objects = _blockService.GetObjectsAt(c);
            for (int i = 0; i < objects.Count; i++)
            {
                var segment = objects[i].GetComponent<FlumeSegment>();
                if (segment != null && segment != _segment && Holds(segment, c)) return segment;
            }
            return null;
        }

        private static bool Holds(FlumeSegment segment, Vector3Int cell)
        {
            var cells = segment.WorldFlowCells;
            for (int i = 0; i < cells.Count; i++) if (cells[i] == cell) return true;
            return false;
        }
    }
}
