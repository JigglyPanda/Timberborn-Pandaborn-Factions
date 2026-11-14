using Timberborn.BaseComponentSystem;
using Timberborn.BlockSystem;
using Timberborn.EntitySystem;
using Timberborn.Localization;
using Timberborn.StatusSystem;
using Timberborn.TickSystem;
using Timberborn.WaterSystem;

namespace Pandaborn.Water
{
    /// <summary>
    /// Badwater shut-off for a flume gate (spec ContaminationShutoff &gt; 0): while the water behind the gate is more
    /// contaminated than the threshold, the gate cell becomes a full obstacle; it reopens once the water behind has stayed
    /// below half the threshold for a few checks. <see cref="Enabled"/> is the player's switch (on by default; no panel
    /// yet in the prototype). Nothing is saved: the state is re-derived from the water within one check after loading.
    /// </summary>
    public class FlumeGateGuard : TickableComponent, IAwakableComponent, IInitializableEntity, IFinishedStateListener
    {
        private const int Interval = 5;
        private const int ClearChecksToReopen = 6;

        private readonly IWaterService _waterService;
        private readonly IThreadSafeWaterMap _waterMap;
        private readonly ILoc _loc;
        private BlockObject _blockObject;
        private FlumeSegment _segment;
        private StatusToggle _closedStatus;
        private int _countdown, _clearChecks;

        public bool GuardEnabled { get; set; } = true;
        public bool Closed { get; private set; }
        public float LastContamination { get; private set; }

        public FlumeGateGuard(IWaterService waterService, IThreadSafeWaterMap waterMap, ILoc loc)
        {
            _waterService = waterService;
            _waterMap = waterMap;
            _loc = loc;
        }

        public void Awake()
        {
            _blockObject = GetComponent<BlockObject>();
            _segment = GetComponent<FlumeSegment>();
            _closedStatus = StatusToggle.CreateNormalStatusWithFloatingIcon("BuildingBlockedByContamination", _loc.T("Status.Pandaborn.Flume.BadwaterClosed"));
            DisableComponent();
        }

        public void InitializeEntity()
        {
            GetComponent<StatusSubject>()?.RegisterStatus(_closedStatus);
        }

        public void OnEnterFinishedState()
        {
            if (_segment.Spec.ContaminationShutoff > 0f) EnableComponent();
        }

        public void OnExitFinishedState()
        {
            DisableComponent();
            SetClosed(false);
        }

        public override void Tick()
        {
            if (--_countdown > 0) return;
            _countdown = Interval;
            if (_segment.WorldFlowCells.Count == 0) return;
            var gate = _segment.WorldFlowCells[0];
            var behind = gate - _segment.Offset;
            float threshold = _segment.Spec.ContaminationShutoff;
            LastContamination = _waterMap.WaterDepth(behind) > 0.001f ? _waterMap.ColumnContamination(behind) : 0f;
            if (!GuardEnabled) { SetClosed(false); return; }
            if (LastContamination > threshold) { _clearChecks = 0; SetClosed(true); }
            else if (Closed && LastContamination < threshold * 0.5f && ++_clearChecks >= ClearChecksToReopen) SetClosed(false);
        }

        private void SetClosed(bool closed)
        {
            if (closed == Closed) return;
            Closed = closed;
            var gate = _segment.WorldFlowCells.Count > 0 ? _segment.WorldFlowCells[0] : _blockObject.Coordinates;
            if (closed) _waterService.AddFullObstacle(gate);
            else _waterService.RemoveFullObstacle(gate);
            _closedStatus.Toggle(closed);
        }
    }
}
