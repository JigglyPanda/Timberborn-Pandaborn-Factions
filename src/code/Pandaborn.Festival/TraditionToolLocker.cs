using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using Pandaborn.Specs;
using Timberborn.BlockObjectTools;
using Timberborn.Buildings;
using Timberborn.CoreUI;
using Timberborn.EntitySystem;
using Timberborn.InputSystem;
using Timberborn.Localization;
using Timberborn.ScienceSystem;
using Timberborn.ToolSystem;
using UnityEngine;

namespace Pandaborn.Festival
{
    /// <summary>
    /// Tradition: decorations marked PandabornTraditionSpec stay locked in the toolbar until the village's Tradition (one step
    /// per Lantern Festival) reaches their level. The game's own tool-lock machinery (IToolLocker, as science uses), so the
    /// toolbar shows the lock and a click explains it. The game allows one locker per tool: this one only locks tools that
    /// science does not lock (ScienceCost 0 or already unlocked), so it never competes with BuildingToolLocker.
    /// Without the module there is no locker: the decorations are simply buildable.
    /// </summary>
    public class TraditionToolLocker : IToolLocker
    {
        private const string InstantUnlockKey = "InstantUnlock";

        private readonly FestivalService _festivalService;
        private readonly BuildingUnlockingService _buildingUnlockingService;
        private readonly DialogBoxShower _dialogBoxShower;
        private readonly InputService _inputService;
        private readonly ILoc _loc;
        private readonly Lazy<ToolUnlockingService> _toolUnlockingService;
        private readonly List<ITool> _locked = new List<ITool>();
        private bool _subscribed;

        public TraditionToolLocker(FestivalService festivalService, BuildingUnlockingService buildingUnlockingService, DialogBoxShower dialogBoxShower,
                                   InputService inputService, ILoc loc, Bindito.Core.IContainer container)
        {
            _festivalService = festivalService;
            _buildingUnlockingService = buildingUnlockingService;
            _dialogBoxShower = dialogBoxShower;
            _inputService = inputService;
            _loc = loc;
            // ToolUnlockingService is built from every IToolLocker, this one included: resolve it lazily.
            _toolUnlockingService = new Lazy<ToolUnlockingService>(() => container.GetInstance<ToolUnlockingService>());
        }

        /// <summary>Tools locked by Tradition right now (tests).</summary>
        public static int LockedCount { get; private set; }

        public bool ShouldLock(ITool tool)
        {
            try
            {
                if (!_festivalService.Active || !TryGetLevel(tool, out int level, out var building)) return false;
                if (_festivalService.Tradition >= level) return false;
                if (!_buildingUnlockingService.Unlocked(building)) return false;   // science locks it; never two lockers
                Subscribe();
                _locked.Add(tool);
                LockedCount = _locked.Count;
                return true;
            }
            catch (Exception e)
            {
                Debug.LogError("[Pandaborn.Festival] Tradition lock check failed: " + e);
                return false;
            }
        }

        public void TryToUnlock(ITool tool, Action successCallback, Action failCallback)
        {
            if (_inputService.IsKeyHeld(InstantUnlockKey) || !TryGetLevel(tool, out int level, out var building) || _festivalService.Tradition >= level)
            {
                _locked.Remove(tool);
                LockedCount = _locked.Count;
                successCallback();
                return;
            }
            string name = _loc.T(building.GetSpec<LabeledEntitySpec>().DisplayNameLocKey);
            _dialogBoxShower.Create()
                .SetMessage(_loc.T("Pandaborn.Festival.Tradition.Locked", name, level.ToString(CultureInfo.InvariantCulture),
                                   _festivalService.Tradition.ToString(CultureInfo.InvariantCulture)))
                .SetConfirmButton(failCallback)
                .Show();
        }

        private void Subscribe()
        {
            if (_subscribed) return;
            _subscribed = true;
            _festivalService.TraditionChanged += OnTraditionChanged;
        }

        private void OnTraditionChanged(int tradition)
        {
            var due = _locked.Where(t => TryGetLevel(t, out int level, out _) && level <= tradition).ToList();
            foreach (var tool in due)
            {
                _locked.Remove(tool);
                if (_toolUnlockingService.Value.IsLocked(tool)) _toolUnlockingService.Value.Unlock(tool);
            }
            LockedCount = _locked.Count;
            if (due.Count > 0)
                Debug.Log("[Pandaborn.Festival] Tradition " + tradition + " unlocked " + due.Count + " decoration(s)");
        }

        private static bool TryGetLevel(ITool tool, out int level, out BuildingSpec building)
        {
            level = 0;
            building = null;
            if (!(tool is BlockObjectTool blockObjectTool) || blockObjectTool.Template == null) return false;
            var spec = blockObjectTool.Template.GetSpec<PandabornTraditionSpec>();
            building = blockObjectTool.Template.GetSpec<BuildingSpec>();
            if (spec == null || building == null) return false;
            level = spec.Level;
            return level > 0;
        }
    }
}
