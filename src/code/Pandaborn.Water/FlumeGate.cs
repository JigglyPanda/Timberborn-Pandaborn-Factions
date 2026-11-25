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
    /// for six checks in a row (<see cref="BadwaterLatch"/>). Closed means the vanilla inert obstacle of the piece is put
    /// back (and lifted again on opening), so with the module off a gate is always closed.
    /// Saved in the entity state, entry "Water" v1: "flow=0.30;guard=1;bad=1". "bad" (shut by badwater when saved) was
    /// added later and is optional: a gate that was shut stays shut across a load instead of opening for a tick; an older
    /// build ignores the key.
    /// Every game callback is contained (WaterGuard): a gate without a flume segment in its data does nothing.
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
        private BadwaterLatch _latch;
        private int _countdown;
        private bool _limitApplied;
        private bool _subscribed;

        public FlumeGate(IWaterService waterService, IThreadSafeWaterMap waterMap, ILoc loc)
        {
            _waterService = waterService;
            _waterMap = waterMap;
            _loc = loc;
        }

        /// <summary>The player's flow setting, in the game's water units per second.</summary>
        public float Flow { get; private set; }

        public float MaxFlow => _spec != null && _spec.MaxFlow > 0f ? _spec.MaxFlow : 1f;

        public float FlowStep => _spec != null && _spec.FlowStep > 0f ? _spec.FlowStep : 0.05f;

        /// <summary>The player's badwater switch.</summary>
        public bool GuardEnabled { get; private set; } = true;

        public bool ClosedByBadwater => _latch.Closed;

        public float LastContamination { get; private set; }

        public bool IsOpen => _segment != null && _segment.Active && !ClosedByBadwater && Flow > 0f;

        public void Awake()
        {
            _segment = GetComponent<FlumeSegment>();
            _spec = GetComponent<PandabornFlumeGateSpec>();
            _state = GetComponent<PandabornEntityState>();
            Flow = GateFlow.Snap(_spec.DefaultFlow, 0f, MaxFlow);
            _closedStatus = StatusToggle.CreateNormalStatusWithAlertAndFloatingIcon("BuildingBlockedByContamination",
                _loc.T("Pandaborn.Water.Status.GateBadwater"), _loc.T("Pandaborn.Water.Status.GateBadwater.Short"));
            DisableComponent();
        }

        public void InitializeEntity()
        {
            try
            {
                GetComponent<StatusSubject>()?.RegisterStatus(_closedStatus);
                if (_state == null) return;
                if (_state.TryGet(Feature, out int version, out string payload) && version == Version) Read(payload);
                _state.SetWriter(Feature, Version, Write);
                if (_segment != null && _segment.Active) Apply();   // opened before the saved settings were read
            }
            catch (Exception e) { WaterGuard.Report("reading a Flume Gate's settings", e); }
        }

        public void OnEnterFinishedState()
        {
            if (_segment == null) return;   // data without a flume segment: nothing to gate
            try
            {
                if (!_subscribed)
                {
                    _segment.Activated += Apply;
                    _subscribed = true;
                }
                EnableComponent();
                if (_segment.Active) Apply();   // the segment may have opened already in its own finished-state listener
            }
            catch (Exception e) { WaterGuard.Report("opening a Flume Gate", e); }
        }

        public void OnExitFinishedState()
        {
            if (_segment == null) return;
            try
            {
                if (_subscribed)
                {
                    _segment.Activated -= Apply;
                    _subscribed = false;
                }
                DisableComponent();
                if (_limitApplied && _segment.WorldFlowCells.Count > 0) _waterService.RemoveInflowLimit(_segment.WorldFlowCells[0]);
                _limitApplied = false;
                _latch.Reset();
                _closedStatus.Deactivate();
            }
            catch (Exception e) { WaterGuard.Report("closing a Flume Gate", e); }
        }

        public void SetFlow(float flow)
        {
            Flow = GateFlow.Snap(flow, FlowStep, MaxFlow);
            Apply();
        }

        public void SetGuardEnabled(bool enabled)
        {
            GuardEnabled = enabled;
            if (!enabled) _latch.Reset();
            Apply();
        }

        public override void Tick()
        {
            if (--_countdown > 0) return;
            _countdown = Interval;
            try
            {
                if (_segment == null || !_segment.Active || _segment.WorldFlowCells.Count == 0) return;
                var gate = _segment.WorldFlowCells[0];
                var behind = gate - _segment.Offset;   // one cell outside the map at most: the water map has a margin
                LastContamination = _waterMap.WaterDepth(behind) > 0.001f ? _waterMap.ColumnContamination(behind) : 0f;
                if (!GuardEnabled) return;
                if (_latch.Update(LastContamination, _spec.ContaminationShutoff, ClearChecksToReopen)) Apply();
            }
            catch (Exception e)
            {
                WaterGuard.Report("a Flume Gate's badwater check", e);
                DisableComponent();   // the gate keeps its flow setting; only the guard stops
            }
        }

        /// <summary>Puts the cell in the state the settings ask for: closed (inert obstacle back), or open with the flow limit.</summary>
        private void Apply()
        {
            try
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
                else if (_segment.HasInertObstacle)
                {
                    if (_limitApplied) _waterService.RemoveInflowLimit(gate);
                    _limitApplied = false;
                    _segment.CloseWithInertObstacle(1f);
                }
                else
                {
                    // data without the inert obstacle: a zero limit closes the cell, and is ours to remove on demolition
                    _waterService.SetInflowLimit(gate, 0f);
                    _limitApplied = true;
                }
                _closedStatus.Toggle(ClosedByBadwater);
            }
            catch (Exception e) { WaterGuard.Report("setting a Flume Gate", e); }
        }

        private string Write() => "flow=" + Flow.ToString("0.###", CultureInfo.InvariantCulture) + ";guard=" + (GuardEnabled ? "1" : "0")
                                  + (GuardEnabled && ClosedByBadwater ? ";bad=1" : "");

        private void Read(string payload)
        {
            try
            {
                bool bad = false;
                foreach (var part in (payload ?? "").Split(';'))
                {
                    var kv = part.Split('=');
                    if (kv.Length != 2) continue;
                    if (kv[0] == "flow" && float.TryParse(kv[1], NumberStyles.Float, CultureInfo.InvariantCulture, out float f)
                        && !float.IsNaN(f) && !float.IsInfinity(f))
                        Flow = GateFlow.Snap(f, 0f, MaxFlow);
                    else if (kv[0] == "guard") GuardEnabled = kv[1] != "0";
                    else if (kv[0] == "bad") bad = kv[1] == "1";
                }
                _latch.Reset();
                _latch.Closed = bad && GuardEnabled;
            }
            catch (Exception e)
            {
                Debug.LogWarning("[Pandaborn] flume gate settings unreadable, using defaults: " + e.Message);
                Flow = GateFlow.Snap(_spec.DefaultFlow, 0f, MaxFlow);
                GuardEnabled = true;
                _latch.Reset();
            }
        }
    }
}
