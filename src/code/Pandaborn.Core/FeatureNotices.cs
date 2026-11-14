using System;
using System.Collections.Generic;
using System.Linq;
using Timberborn.GameDistricts;
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

        /// <summary>The notices posted in this session (for tests and logs).</summary>
        public static readonly List<string> Posted = new List<string>();

        public FeatureNotices(EventBus eventBus, ILoc loc, Messenger messenger, PandabornStore store)
        {
            _eventBus = eventBus;
            _loc = loc;
            _messenger = messenger;
            _store = store;
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
            if (FeatureRegistry.DuplicateCopies.Count > 0)
                messages.Add(new KeyValuePair<string, string>("Duplicate", _loc.T("Pandaborn.Core.Duplicate", FeatureRegistry.Owner)));

            foreach (var m in messages)
            {
                if (shown.Contains(m.Key)) continue;
                shown.Add(m.Key);
                Posted.Add(m.Value);
                _messenger.Post(m.Value, warning: true);
            }
            _store.Set(StoreFeature, 1, string.Join(",", shown.OrderBy(s => s, StringComparer.Ordinal)));
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

        public void Post(string text, bool warning = false)
        {
            Log.Add(text);
            Debug.Log("[Pandaborn] message: " + text);
            try
            {
                if (warning) _quickNotificationService.SendWarningNotification(text);
                else _quickNotificationService.SendNotification(text);
            }
            catch (Exception e) { Debug.LogWarning("[Pandaborn] toast failed: " + e.Message); }
            try
            {
                var center = _districtCenterRegistry.FinishedDistrictCenters.FirstOrDefault() ?? _districtCenterRegistry.AllDistrictCenters.FirstOrDefault();
                if (center != null) _notificationBus.Post(text, center);
            }
            catch (Exception e) { Debug.LogWarning("[Pandaborn] notification failed: " + e.Message); }
        }
    }
}