using System;
using Pandaborn.Specs;
using Timberborn.BaseComponentSystem;
using Timberborn.BlockSystem;
using Timberborn.EntitySystem;
using Timberborn.Localization;
using Timberborn.StatusSystem;
using Timberborn.TickSystem;
using Timberborn.WorkSystem;

namespace Pandaborn.Ringtails
{
    /// <summary>
    /// A night post (PandabornNightPostSpec). Its data keeps the vanilla worker type (Beaver), so with the feature off or degraded
    /// it is an ordinary Inkpaw workplace. With the feature on this switches it to the Ringtail worker type when it is
    /// finished or loaded, with the public WorkplaceWorkerType.SetWorkerType (which unassigns any Inkpaw), and keeps it there:
    /// a change made elsewhere (the vanilla beaver/bot toggle once bots exist, copy-settings) is switched back.
    /// By day it shows "Closed for the day. Ringtails start at the afternoon bell." (a plain status, no alert). Ringtails stay
    /// assigned while they rest, so the vanilla no-workers alert only appears when the post really has no Ringtails.
    /// </summary>
    public class NightPost : TickableComponent, IAwakableComponent, IInitializableEntity, IPostInitializableEntity, IFinishedStateListener
    {
        private readonly RingtailService _ringtailService;
        private readonly RingtailWorkday _workday;
        private readonly ILoc _loc;
        private WorkplaceWorkerType _workerType;
        private BlockObject _blockObject;
        private StatusToggle _closedStatus;
        private bool _finished;
        private bool _switching;

        public NightPost(RingtailService ringtailService, RingtailWorkday workday, ILoc loc)
        {
            _ringtailService = ringtailService;
            _workday = workday;
            _loc = loc;
        }

        public bool IsRingtailTyped => _workerType != null && _workerType.WorkerType == _ringtailService.WorkerType;

        /// <summary>By day, until the bell (clamped like the Ringtails' rest window).</summary>
        public bool ClosedForTheDay
        {
            get
            {
                float end = Math.Min(Math.Max(_workday.WorkdayHours, 4f), 16f);
                return _workday.HoursSinceDawn < end;
            }
        }

        public void Awake()
        {
            _workerType = GetComponent<WorkplaceWorkerType>();
            _blockObject = GetComponent<BlockObject>();
            if (_workerType != null) _workerType.WorkerTypeChanged += OnWorkerTypeChanged;
        }

        public void InitializeEntity()
        {
            if (!_ringtailService.Enabled) return;
            _closedStatus = StatusToggle.CreateNormalStatus("NoUnemployed", _loc.T("Pandaborn.Ringtails.Status.ClosedForTheDay"));
            GetComponent<StatusSubject>()?.RegisterStatus(_closedStatus);
        }

        public void PostInitializeEntity()
        {
            if (_blockObject != null && _blockObject.IsFinished) Claim();
        }

        public void OnEnterFinishedState()
        {
            _finished = true;
            Claim();
        }

        public void OnExitFinishedState()
        {
            _finished = false;
            _closedStatus?.Deactivate();
        }

        private void Claim()
        {
            if (!_ringtailService.Enabled || _workerType == null || IsRingtailTyped) return;
            _switching = true;
            try { _workerType.SetWorkerType(_ringtailService.WorkerType); }
            finally { _switching = false; }
        }

        private void OnWorkerTypeChanged(object sender, WorkerTypeChangedEventArgs e)
        {
            if (_switching || !_ringtailService.Enabled || IsRingtailTyped) return;
            if (_blockObject != null && _blockObject.IsFinished) Claim();
        }

        public override void Tick()
        {
            if (_closedStatus == null) return;
            bool finished = _finished || (_blockObject != null && _blockObject.IsFinished);
            _closedStatus.Toggle(finished && IsRingtailTyped && ClosedForTheDay);
        }
    }
}
