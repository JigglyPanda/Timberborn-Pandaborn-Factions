using System;
using System.Collections.Generic;
using System.Linq;
using Timberborn.GameDistricts;
using Timberborn.GameFactionSystem;
using Timberborn.Localization;
using Timberborn.NotificationSystem;
using Timberborn.QuickNotificationSystem;
using Timberborn.SingletonSystem;
using Timberborn.UILayoutSystem;
using UnityEngine;

namespace Pandaborn.Core
{
    /// <summary>
    /// Tells the player, once per save, that a Pandaborn feature is off (its game API changed, or a dev switch) or that the
    /// mod is enabled twice. Posted when the game's interface first appears, as a warning toast and as an entry in the
    /// notification log (subject: the first district center, so clicking it goes somewhere sensible).
    /// </summary>
    public class FeatureNotices : ILoadableSingleton
    {
        public const string StoreFeature = "Core.Notices";
        private readonly EventBus _eventBus;
        private readonly ILoc _loc;
        private readonly Messenger _messenger;
        private readonly PandabornStore _store;
        private readonly FactionService _factionService;

        /// <summary>The faction whose games get the feature report.</summary>
        public const string FactionId = "Inkpaws";

        /// <summary>The notices posted in this session (for tests and logs).</summary>
        public static readonly List<string> Posted = new List<string>();

        /// <summary>The last feature report text (for tests).</summary>
        public static string LastReport { get; private set; }

        public FeatureNotices(EventBus eventBus, ILoc loc, Messenger messenger, PandabornStore store, FactionService factionService)
        {
            _eventBus = eventBus;
            _loc = loc;
            _messenger = messenger;
            _store = store;
            _factionService = factionService;
            FeatureRegistry.ClearNoData();   // constructed before any module's Load in this game
        }

        public void Load()
        {
            _eventBus.Register(this);
            Debug.Log("[Pandaborn] features: " + string.Join("; ", FeatureRegistry.All.Select(s => s.ToString())));
        }

        [OnEvent]
        public void OnShowPrimaryUI(ShowPrimaryUIEvent e)
        {
            try { PostDue(); }
            catch (Exception ex) { Debug.LogError("[Pandaborn] posting feature notices failed: " + ex); }
        }

        private void PostDue()
        {
            var shown = new HashSet<string>(StringComparer.Ordinal);
            if (_store.TryGet(StoreFeature, out _, out var payload) && payload.Length > 0)
                foreach (var k in payload.Split(',')) shown.Add(k);
            var messages = new List<KeyValuePair<string, string>>();
            foreach (var state in FeatureRegistry.All.Where(s => !s.IsOn))
            {
                string key = state.Id + ":" + state.Status;
                string name = FeatureName(state.Id);
                string text = state.Status == FeatureStatus.ForcedOff
                    ? _loc.T("Pandaborn.Core.FeatureForcedOff", name)
                    : _loc.T("Pandaborn.Core.FeatureOff", name, state.Reason);
                messages.Add(new KeyValuePair<string, string>(key, text));
            }
            foreach (var d in FeatureRegistry.Degraded)
                messages.Add(new KeyValuePair<string, string>(d.Key + ":Degraded", _loc.T("Pandaborn.Core.FeatureDegraded", FeatureName(d.Key), d.Value)));
            if (FeatureRegistry.DuplicateCopies.Count > 0)
                messages.Add(new KeyValuePair<string, string>("Duplicate", _loc.T("Pandaborn.Core.Duplicate", FeatureRegistry.Owner)));

            foreach (var m in messages)
            {
                if (shown.Contains(m.Key)) continue;
                shown.Add(m.Key);
                Posted.Add(m.Value);
                _messenger.Post(m.Value, warning: true);
            }
            // The feature report: one notification-log entry per save (and again whenever the states change) in games of
            // our faction, listing every unit and why any is off, so a player can see what runs without dev mode.
            string report = Report();
            LastReport = report;
            string reportKey = "Report#" + Signature();
            if (IsOurFaction() && !shown.Contains(reportKey))
            {
                foreach (var old in shown.Where(s => s.StartsWith("Report#", StringComparison.Ordinal)).ToList()) shown.Remove(old);
                shown.Add(reportKey);
                _messenger.Post(report, warning: false, toast: false);
            }
            _store.Set(StoreFeature, 1, string.Join(",", shown.OrderBy(s => s, StringComparer.Ordinal)));
        }

        private bool IsOurFaction()
        {
            try { return _factionService.Current?.Id == FactionId; }
            catch (Exception) { return false; }
        }

        private static string Signature() =>
            string.Join("/", FeatureRegistry.All.Select(s => s.Id + "=" + s.Status)) + (FeatureRegistry.Degraded.Count > 0 ? "/degraded" : "") + (FeatureRegistry.NoData.Count > 0 ? "/nodata:" + string.Join(",", FeatureRegistry.NoData.Keys) : "")
            + (FeatureRegistry.DuplicateCopies.Count > 0 ? "/duplicate" : "");

        /// <summary>"Pandaborn - Factions features: The afternoon bell: on; Inkpaw names: off (reason); ..."</summary>
        public string Report()
        {
            var parts = new List<string>();
            foreach (var s in FeatureRegistry.All.Where(s => s.Id != "Specs" && s.Id != "Core"))
            {
                string state = s.Status == FeatureStatus.On && FeatureRegistry.NoData.TryGetValue(s.Id, out var missing)
                    ? _loc.T("Pandaborn.Core.Report.NoData", missing)
                    : s.Status == FeatureStatus.On
                    ? (FeatureRegistry.Degraded.TryGetValue(s.Id, out var why) ? _loc.T("Pandaborn.Core.Report.Degraded", why) : _loc.T("Pandaborn.Core.Report.On"))
                    : s.Status == FeatureStatus.ForcedOff ? _loc.T("Pandaborn.Core.Report.ForcedOff") : _loc.T("Pandaborn.Core.Report.Off", s.Reason);
                parts.Add(FeatureName(s.Id) + ": " + state);
            }
            var core = FeatureRegistry.All.Where(s => (s.Id == "Specs" || s.Id == "Core") && !s.IsOn).Select(s => FeatureName(s.Id) + ": " + _loc.T("Pandaborn.Core.Report.Off", s.Reason));
            parts.InsertRange(0, core);
            if (FeatureRegistry.DuplicateCopies.Count > 0) parts.Add(_loc.T("Pandaborn.Core.Report.Duplicate", FeatureRegistry.DuplicateCopies.Count));
            return _loc.T("Pandaborn.Core.Report", string.Join("; ", parts));
        }

        private string FeatureName(string id)
        {
            string key = "Pandaborn.Feature." + id;
            string text = _loc.T(key);
            return string.IsNullOrEmpty(text) || text.Contains(key) ? id : text;
        }
    }

    /// <summary>
    /// Posts a player message as a toast (top of the screen) and as an entry in the notification log, whose subject is the
    /// first district center so clicking it goes somewhere sensible. Never throws.
    /// </summary>
    public class Messenger
    {
        private readonly QuickNotificationService _quickNotificationService;
        private readonly NotificationBus _notificationBus;
        private readonly DistrictCenterRegistry _districtCenterRegistry;

        /// <summary>Every message posted in this session (for tests and logs).</summary>
        public static readonly List<string> Log = new List<string>();

        public Messenger(QuickNotificationService quickNotificationService, NotificationBus notificationBus, DistrictCenterRegistry districtCenterRegistry)
        {
            _quickNotificationService = quickNotificationService;
            _notificationBus = notificationBus;
            _districtCenterRegistry = districtCenterRegistry;
        }

        public void Post(string text, bool warning = false, bool toast = true) => Post(text, null, warning, toast);

        /// <summary>The same with a subject: clicking the entry in the notification log takes the camera to it (a new
        /// colonist, the building it happened at). Without one, or when it is gone, the first district center.</summary>
        public void Post(string text, Timberborn.BaseComponentSystem.BaseComponent subject, bool warning = false, bool toast = true)
        {
            Log.Add(text);
            Debug.Log("[Pandaborn] message: " + text);
            if (toast) try
            {
                if (warning) _quickNotificationService.SendWarningNotification(text);
                else _quickNotificationService.SendNotification(text);
            }
            catch (Exception e) { Debug.LogWarning("[Pandaborn] toast failed: " + e.Message); }
            try
            {
                if (!subject) subject = _districtCenterRegistry.FinishedDistrictCenters.FirstOrDefault() ?? _districtCenterRegistry.AllDistrictCenters.FirstOrDefault();
                if (subject) _notificationBus.Post(text, subject);

            }
            catch (Exception e) { Debug.LogWarning("[Pandaborn] notification failed: " + e.Message); }
        }
    }
}