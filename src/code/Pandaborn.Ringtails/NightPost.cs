using System;
using Pandaborn.Specs;
using Timberborn.BaseComponentSystem;
using Timberborn.BlockSystem;
using Timberborn.EntitySystem;
using Timberborn.Localization;
using Timberborn.StatusSystem;
using Timberborn.TickSystem;
using Timberborn.WorkSystem;
using UnityEngine;

namespace Pandaborn.Ringtails
{
    /// <summary>
    /// A night post (PandabornNightPostSpec). Its data keeps the vanilla worker type (Beaver), so with the feature off or degraded
    /// it is an ordinary Inkpaw workplace. With the feature on this switches it to the Ringtail worker type when it is
    /// finished or loaded, with the public WorkplaceWorkerType.SetWorkerType (which unassigns any Inkpaw), and keeps it there:
    /// a change made elsewhere (the vanilla beaver/bot toggle once bots exist, copy-settings) is switched back.
    ///
    /// The switch back happens on the next tick, never inside the game's WorkerTypeChanged event. The game's
    /// DistrictWorkplaceAssigner files each workplace under its worker type and moves it by the event's (previous,
    /// current) pair; a second SetWorkerType from inside a handler reaches the assigner before the first event does, it
    /// adds the post to the Ringtail list a second time (SortedList.Add throws ArgumentException: a crash on one click of
    /// the beaver/bot toggle), and without the exception it would leave the post filed under the wrong type.
    ///
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
        private bool _reclaim;
        private bool _failed;

        public NightPost(RingtailService ringtailService, RingtailWorkday workday, ILoc loc)
        {
            _ringtailService = ringtailService;
            _workday = workday;
            _loc = loc;
        }

        public bool IsRingtailTyped => _workerType != null && _workerType.WorkerType == _ringtailService.WorkerType;

        /// <summary>By day, until the bell (clamped like the Ringtails' rest window).</summary>
        public bool ClosedForTheDay => _workday.HoursSinceDawn < _workday.ShiftStartHours;

        /// <summary>Times this post took itself back from another worker type (tests).</summary>
        public int Reclaims { get; private set; }

        public void Awake()
        {
            _workerType = GetComponent<WorkplaceWorkerType>();
            _blockObject = GetComponent<BlockObject>();
            if (_workerType != null) _workerType.WorkerTypeChanged += OnWorkerTypeChanged;
        }

        public void InitializeEntity()
        {
            if (!_ringtailService.Enabled) return;
            try
            {
                _closedStatus = StatusToggle.CreateNormalStatus("NoUnemployed", _loc.T("Pandaborn.Ringtails.Status.ClosedForTheDay"));
                GetComponent<StatusSubject>()?.RegisterStatus(_closedStatus);
            }
            catch (Exception e) { Fail("its day status", e); }
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
            _reclaim = false;
            try { _closedStatus?.Deactivate(); }
            catch (Exception) { }
        }

        /// <summary>Switches the post to the Ringtail worker type. Never called from inside a WorkerTypeChanged event.</summary>
        private void Claim()
        {
            if (_failed || !_ringtailService.Enabled || _workerType == null || IsRingtailTyped) return;

            // a finished-state step that throws fails the load: contain it, the post then stays an Inkpaw workplace
            try { _workerType.SetWorkerType(_ringtailService.WorkerType); }
            catch (Exception e) { Fail("switching to Ringtail workers", e); }
        }

        private void OnWorkerTypeChanged(object sender, WorkerTypeChangedEventArgs e)
        {
            if (_failed || !_ringtailService.Enabled || IsRingtailTyped) return;
            if (_finished || (_blockObject != null && _blockObject.IsFinished)) _reclaim = true;   // carried out by the next Tick
        }

        public override void Tick()
        {
            if (_reclaim)
            {
                _reclaim = false;
                if (!IsRingtailTyped)
                {
                    Claim();
                    if (IsRingtailTyped) Reclaims++;
                }
            }
            if (_closedStatus == null) return;
            bool finished = _finished || (_blockObject != null && _blockObject.IsFinished);
            _closedStatus.Toggle(finished && IsRingtailTyped && ClosedForTheDay);
        }

        private void Fail(string what, Exception e)
        {
            _failed = true;
            Debug.LogError("[Pandaborn.Ringtails] night post " + Name + ": " + what + " failed; it stays an Inkpaw workplace: " + e);
        }
    }
}
