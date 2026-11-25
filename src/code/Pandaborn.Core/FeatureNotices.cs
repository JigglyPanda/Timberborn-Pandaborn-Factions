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
    /// Tells the player when a Pandaborn feature does not run as it should. Silent while everything works. Otherwise one
    /// message (a warning toast plus an entry in the notification log, whose subject is the first district center so
    /// clicking it goes somewhere sensible), posted when the game's interface first appears, in games of our faction only:
    /// in a Folktails game none of our features does anything, so there is nothing to say and nothing is saved.
    /// The message names each feature in player words and says what will not work (NoticePlan has the rule for when:
    /// a switched-off feature at every load, the rest once per save).
    /// The full state of every unit, with the technical reasons, goes to the log at every load ("feature report").
    /// </summary>
    public class FeatureNotices : ILoadableSingleton
    {
        public const string StoreFeature = "Core.Notices";

        /// <summary>The player's feature switch file, as the bootstrap names it in the reason of a forced-off feature.</summary>
        public const string PlayerSwitchFile = "PandabornFactions.txt";

        /// <summary>Entry version 2: the payload is the signature the save was last told (NoticePlan.Signature). Version 1
        /// (a list of keys of single notices and a report) is read as "told nothing".</summary>
        private const int StoreVersion = 2;
        private const int KeptMessages = 100;

        private readonly EventBus _eventBus;
        private readonly ILoc _loc;
        private readonly Messenger _messenger;
        private readonly PandabornStore _store;
        private readonly FactionService _factionService;
        private bool _interfaceShown;
        private string _toldThisLoad;

        /// <summary>The faction whose games get the notices.</summary>
        public const string FactionId = "Inkpaws";

        /// <summary>The notices posted in this session (for tests and logs; the last hundred).</summary>
        public static readonly List<string> Posted = new List<string>();

        /// <summary>The last feature report text (for tests): every unit and its state, as written to the log.</summary>
        public static string LastReport { get; private set; }

        public FeatureNotices(EventBus eventBus, ILoc loc, Messenger messenger, PandabornStore store, FactionService factionService)
        {
            _eventBus = eventBus;
            _loc = loc;
            _messenger = messenger;
            _store = store;
            _factionService = factionService;
            // constructed before any module's Load in this game: what the last game reported is gone
            FeatureRegistry.StartGame();
            SafeUi.StartGame();
            FeatureRegistry.Reported = OnReported;
        }

        public void Load()
        {
            _eventBus.Register(this);
            Debug.Log("[Pandaborn] features: " + string.Join("; ", FeatureRegistry.All.Select(s => s.ToString())));
        }

        [OnEvent]
        public void OnShowPrimaryUI(ShowPrimaryUIEvent e)
        {
            _interfaceShown = true;
            try
            {
                LastReport = Report();
                if (IsOurFaction()) Debug.Log("[Pandaborn] " + LastReport);
                PostDue();
            }
            catch (Exception ex) { Debug.LogError("[Pandaborn] posting feature notices failed: " + ex); }
        }

        /// <summary>A feature reported a new state while the game runs (FeatureRegistry.Reported).</summary>
        private void OnReported()
        {
            if (!_interfaceShown) return;       // still loading: the message goes out when the interface appears
            try { PostDue(); }
            catch (Exception ex) { Debug.LogError("[Pandaborn] posting feature notices failed: " + ex); }
        }

        private void PostDue()
        {
            if (!IsOurFaction()) return;
            var problems = NoticePlan.Problems(FeatureRegistry.All, FeatureRegistry.Degraded, FeatureRegistry.NoData, FeatureRegistry.DuplicateCopies.Count);
            string signature = NoticePlan.Signature(problems);
            bool hasEntry = _store.TryGet(StoreFeature, out int version, out var payload);
            string toldInSave = hasEntry && version == StoreVersion ? payload : "";
            if (signature.Length == 0)
            {
                // all is well: forget what the save was told, so the same trouble is news again if it comes back
                if (hasEntry) _store.Remove(StoreFeature);
                return;
            }
            if (!NoticePlan.Due(signature, NoticePlan.EveryLoad(problems), toldInSave, _toldThisLoad)) return;
            string text = Compose(problems);
            _toldThisLoad = signature;
            Posted.Add(text);
            if (Posted.Count > KeptMessages) Posted.RemoveAt(0);
            _messenger.Post(text, warning: true);
            _store.Set(StoreFeature, StoreVersion, signature);
        }

        private bool IsOurFaction()
        {
            try { return _factionService.Current?.Id == FactionId; }
            catch (Exception) { return false; }
        }

        /// <summary>"Pandaborn - Factions: The afternoon bell is switched off until the mod is updated for this game
        /// version: pandas get no Rested bonus. Everything else works as usual."</summary>
        private string Compose(List<Problem> problems)
        {
            var sentences = new List<string>();
            foreach (var p in problems)
            {
                string name = p.Kind == ProblemKind.Duplicate ? "" : FeatureName(p.Id);
                switch (p.Kind)
                {
                    case ProblemKind.Off:
                    {
                        string effect = Optional("Pandaborn.Feature." + p.Id + ".Off");
                        sentences.Add(effect != null ? _loc.T("Pandaborn.Core.Notice.Off", name, effect) : _loc.T("Pandaborn.Core.Notice.OffPlain", name));
                        break;
                    }
                    case ProblemKind.ForcedOff:
                        // the player's own switch (PandabornFactions.txt in the game's user data folder) or a dev switch
                        sentences.Add(p.Detail.IndexOf(PlayerSwitchFile, StringComparison.OrdinalIgnoreCase) >= 0
                            ? _loc.T("Pandaborn.Core.Notice.PlayerOff", name, PlayerSwitchFile)
                            : _loc.T("Pandaborn.Core.Notice.ForcedOff", name));
                        break;
                    case ProblemKind.Degraded: sentences.Add(_loc.T("Pandaborn.Core.Notice.Degraded", name, p.Detail)); break;
                    case ProblemKind.NoData: sentences.Add(_loc.T("Pandaborn.Core.Notice.NoData", name, p.Detail)); break;
                    case ProblemKind.Duplicate: sentences.Add(_loc.T("Pandaborn.Core.Notice.Duplicate")); break;
                }
            }
            return _loc.T("Pandaborn.Core.Notice", string.Join(" ", sentences));
        }

        /// <summary>"Pandaborn - Factions: The afternoon bell: on; Panda names: off (reason); ...", for the log.</summary>
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

        private string FeatureName(string id) => Optional("Pandaborn.Feature." + id) ?? id;

        /// <summary>A text that may not exist (a module without a name or an effect line): null then, and no error in the
        /// log (ILoc.T logs an error for a missing key, so ask only for keys this file ships).</summary>
        private string Optional(string key)
        {
            if (!KnownKeys.Contains(key)) return null;
            string text = _loc.T(key);
            return string.IsNullOrEmpty(text) || text == key ? null : text;
        }

        /// <summary>The feature names (Localizations/enUS_PandabornCore.csv and each module's own file) and effect lines
        /// (enUS_PandabornCoreNotices.csv) that exist. A module added to modules.txt gets its two lines and its id here.</summary>
        private static readonly string[] Modules = { "Bell", "Names", "Look", "Words", "Water", "Ringtails", "RingtailsFallback", "Tutorial", "Festival", "Flowering" };

        private static readonly HashSet<string> KnownKeys = new HashSet<string>(
            new[] { "Pandaborn.Feature.Specs", "Pandaborn.Feature.Core" }
                .Concat(Modules.Select(id => "Pandaborn.Feature." + id)).Concat(Modules.Select(id => "Pandaborn.Feature." + id + ".Off")), StringComparer.Ordinal);
    }

    /// <summary>
    /// Posts a player message as a toast (top of the screen) and as an entry in the notification log, whose subject is the
    /// first district center so clicking it goes somewhere sensible. Never throws.
    /// </summary>
    public class Messenger
    {
        private const int KeptMessages = 200;
        private readonly QuickNotificationService _quickNotificationService;
        private readonly NotificationBus _notificationBus;
        private readonly DistrictCenterRegistry _districtCenterRegistry;

        /// <summary>The messages posted in this session (for tests and logs; the last two hundred).</summary>
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
            if (string.IsNullOrEmpty(text)) return;
            Log.Add(text);
            if (Log.Count > KeptMessages) Log.RemoveAt(0);
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
