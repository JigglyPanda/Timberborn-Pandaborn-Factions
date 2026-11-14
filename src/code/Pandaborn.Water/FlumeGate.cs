using System;
using System.Globalization;
using Pandaborn.Core;
using Pandaborn.Specs;
using Timberborn.BaseComponentSystem;
using Timberborn.BlockSystem;
using Timberborn.EntitySystem;
using Timberborn.Localization;
using Timberborn.StatusSystem;
using Timberborn.TickSystem;
using Timberborn.WaterSystem;
using UnityEngine;

namespace Pandaborn.Water
{
    /// <summary>
    /// A Flume Gate (PandabornFlumeGateSpec on a flume piece). Its first flow cell lets through at most the player's flow
    /// setting (an inflow limit); flow 0 closes it. With the badwater switch on (default), it closes while the water right
    /// behind it is contaminated above the spec's threshold and reopens after the water there has stayed below half of it
    /// for six checks. Closed means the vanilla inert obstacle of the piece is put back (and lifted again on opening), so
    /// with the module off a gate is always closed.
    /// Saved in the entity state, entry "Water" v1: "flow=0.30;guard=1". Contamination state is not saved: it is read
    /// again from the water within one check after loading.
    /// </summary>
    public class FlumeGate : TickableComponent, IAwakableComponent, IInitializableEntity, IFinishedStateListener
    {
        private const string Feature = "Water";
        private const int Version = 1;
        private const int Interval = 5;
        private const int ClearChecksToReopen = 6;

        private readonly IWaterService _waterService;
        private readonly IThreadSafeWaterMap _waterMap;
        private readonly ILoc _loc;
        private FlumeSegment _segment;
        private PandabornFlumeGateSpec _spec;
        private PandabornEntityState _state;
        private StatusToggle _closedStatus;
        private int _countdown, _clearChecks;
        private bool _limitApplied;

        public FlumeGate(IWaterService waterService, IThreadSafeWaterMap waterMap, ILoc loc)
        {
            _waterService = waterService;
            _waterMap = waterMap;
            _loc = loc;
        }

        /// <summary>The player's flow setting, in the game's water units per second.</summary>
        public float Flow { get; private set; }

        public float MaxFlow => _spec.MaxFlow;

        public float FlowStep => _spec.FlowStep > 0f ? _spec.FlowStep : 0.05f;

        /// <summary>The player's badwater switch.</summary>
        public bool GuardEnabled { get; private set; } = true;

        public bool ClosedByBadwater { get; private set; }

        public float LastContamination { get; private set; }

        public bool IsOpen => _segment != null && _segment.Active && !ClosedByBadwater && Flow > 0f;

        public void Awake()
        {
            _segment = GetComponent<FlumeSegment>();
            _spec = GetComponent<PandabornFlumeGateSpec>();
            _state = GetComponent<PandabornEntityState>();
            Flow = _spec.DefaultFlow;
            _closedStatus = StatusToggle.CreateNormalStatusWithAlertAndFloatingIcon("BuildingBlockedByContamination",
                _loc.T("Pandaborn.Water.Status.GateBadwater"), _loc.T("Pandaborn.Water.Status.GateBadwater.Short"));
            DisableComponent();
        }

        public void InitializeEntity()
        {
            GetComponent<StatusSubject>()?.RegisterStatus(_closedStatus);
            if (_state == null) return;
            if (_state.TryGet(Feature, out int version, out string payload) && version == Version) Read(payload);
            _state.SetWriter(Feature, Version, Write);
            if (_segment != null && _segment.Active) Apply();   // opened before the saved settings were read
        }

        public void OnEnterFinishedState()
        {
            _segment.Activated += Apply;
            EnableComponent();
            if (_segment.Active) Apply();   // the segment may have opened already in its own finished-state listener
        }

        public void OnExitFinishedState()
        {
            _segment.Activated -= Apply;
            DisableComponent();
            if (_limitApplied && _segment.WorldFlowCells.Count > 0) _waterService.RemoveInflowLimit(_segment.WorldFlowCells[0]);
            _limitApplied = false;
            ClosedByBadwater = false;
            _closedStatus.Deactivate();
        }

        public void SetFlow(float flow)
        {
            Flow = Mathf.Clamp(Mathf.Round(flow / FlowStep) * FlowStep, 0f, MaxFlow);
            Apply();
        }

        public void SetGuardEnabled(bool enabled)
        {
            GuardEnabled = enabled;
            if (!enabled && ClosedByBadwater) { ClosedByBadwater = false; _clearChecks = 0; }
            Apply();
        }

        public override void Tick()
        {
            if (--_countdown > 0 || !_segment.Active || _segment.WorldFlowCells.Count == 0) return;
            _countdown = Interval;
            var gate = _segment.WorldFlowCells[0];
            var behind = gate - _segment.Offset;
            LastContamination = _waterMap.WaterDepth(behind) > 0.001f ? _waterMap.ColumnContamination(behind) : 0f;
            if (!GuardEnabled || _spec.ContaminationShutoff <= 0f) return;
            if (LastContamination > _spec.ContaminationShutoff)
            {
                _clearChecks = 0;
                if (!ClosedByBadwater) { ClosedByBadwater = true; Apply(); }
            }
            else if (ClosedByBadwater && LastContamination < _spec.ContaminationShutoff * 0.5f && ++_clearChecks >= ClearChecksToReopen)
            {
                ClosedByBadwater = false;
                Apply();
            }
        }

        /// <summary>Puts the cell in the state the settings ask for: closed (inert obstacle back), or open with the flow limit.</summary>
        private void Apply()
        {
            if (_segment == null || !_segment.Active || _segment.WorldFlowCells.Count == 0) return;
            var gate = _segment.WorldFlowCells[0];
            bool open = !ClosedByBadwater && Flow > 0f;
            if (open)
            {
                _segment.OpenInertObstacle();
                _waterService.SetInflowLimit(gate, Flow);
                _limitApplied = true;
            }
            else
            {
                if (_limitApplied) _waterService.RemoveInflowLimit(gate);
                _limitApplied = false;
                if (_segment.HasInertObstacle) _segment.CloseWithInertObstacle(1f);
                else _waterService.SetInflowLimit(gate, 0f);
            }
            _closedStatus.Toggle(ClosedByBadwater);
        }

        private string Write() => "flow=" + Flow.ToString("0.###", CultureInfo.InvariantCulture) + ";guard=" + (GuardEnabled ? "1" : "0");

        private void Read(string payload)
        {
            try
            {
                foreach (var part in (payload ?? "").Split(';'))
                {
                    var kv = part.Split('=');
                    if (kv.Length != 2) continue;
                    if (kv[0] == "flow" && float.TryParse(kv[1], NumberStyles.Float, CultureInfo.InvariantCulture, out float f))
                        Flow = Mathf.Clamp(f, 0f, _spec.MaxFlow);
                    else if (kv[0] == "guard") GuardEnabled = kv[1] != "0";
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning("[Pandaborn] flume gate settings unreadable, using defaults: " + e.Message);
                Flow = _spec.DefaultFlow;
                GuardEnabled = true;
            }
        }
    }
}
