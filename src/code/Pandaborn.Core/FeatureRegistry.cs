using System;
using System.Collections.Generic;
using System.Linq;

namespace Pandaborn.Core
{
    public enum FeatureStatus
    {
        On,
        Off,
        ForcedOff
    }

    public sealed class FeatureState
    {
        public string Id { get; }
        public FeatureStatus Status { get; }
        public string Reason { get; }

        public FeatureState(string id, FeatureStatus status, string reason)
        {
            Id = id;
            Status = status;
            Reason = reason ?? "";
        }

        public bool IsOn => Status == FeatureStatus.On;

        public override string ToString() => Id + ": " + Status + (Reason.Length > 0 ? " (" + Reason + ")" : "");
    }

    /// <summary>
    /// Which code units the bootstrap loaded, and why the others are off. The bootstrap publishes its report in AppDomain
    /// data (no compile-time link), so this works whichever copy of the mod ran it. Feature modules can ask, but they
    /// only run when they are on anyway; the registry exists for notices, tests and other modules' optional integrations.
    /// </summary>
    public static class FeatureRegistry
    {
        private static List<FeatureState> _states;

        public static IReadOnlyList<FeatureState> All => States;

        /// <summary>The mod folder whose code is running.</summary>
        public static string Owner => AppDomain.CurrentDomain.GetData("Pandaborn.Boot.Owner") as string ?? "";

        /// <summary>Other enabled copies of this mod (their code is not loaded).</summary>
        public static IReadOnlyList<string> DuplicateCopies =>
            ((AppDomain.CurrentDomain.GetData("Pandaborn.Boot.Duplicates") as string) ?? "")
            .Split(new[] { '\n' }, StringSplitOptions.RemoveEmptyEntries);

        public static bool IsOn(string id) => Get(id)?.IsOn ?? false;

        /// <summary>True when the dev switch has a line "key: ..., id, ..." (or "key: *"). For tests only, e.g.
        /// DevFlag("simulate-missing-member", "Words") makes a module take its written fallback.</summary>
        public static bool DevFlag(string key, string id)
        {
            var text = AppDomain.CurrentDomain.GetData("Pandaborn.Boot.Dev") as string ?? "";
            foreach (var line in text.Split(new[] { '\n' }, StringSplitOptions.RemoveEmptyEntries))
            {
                int colon = line.IndexOf(':');
                if (colon < 0 || !string.Equals(line.Substring(0, colon).Trim(), key, StringComparison.OrdinalIgnoreCase)) continue;
                foreach (var part in line.Substring(colon + 1).Split(','))
                    if (part.Trim() == "*" || string.Equals(part.Trim(), id, StringComparison.OrdinalIgnoreCase)) return true;
            }
            return false;
        }

        private static readonly Dictionary<string, string> DegradedStates = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        private static readonly Dictionary<string, string> DegradedInGame = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);

        /// <summary>Features that loaded but run in a fallback mode (for example a private game member is gone), with why.
        /// Listed in the feature report and announced once per save. Holds what was reported for the session
        /// (ReportDegraded) and for the running game (ReportDegradedInGame).</summary>
        public static IReadOnlyDictionary<string, string> Degraded
        {
            get
            {
                if (DegradedInGame.Count == 0) return DegradedStates;
                var all = new Dictionary<string, string>(DegradedStates, StringComparer.OrdinalIgnoreCase);
                foreach (var kv in DegradedInGame) all[kv.Key] = kv.Value;
                return all;
            }
        }

        /// <summary>Set by Core's FeatureNotices of the running game: called when a feature reports a new state after
        /// load, so the player is told then and not at the next load. One slot, replaced by each game.</summary>
        internal static Action Reported;

        private static readonly Dictionary<string, string> NoDataStates = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);

        /// <summary>Features that are loaded but found no data in this game of our faction (a build whose catalogue does not
        /// switch them on yet), with what is missing. The feature report lists them as off with that reason.</summary>
        public static IReadOnlyDictionary<string, string> NoData => NoDataStates;

        /// <summary>A loaded feature found no data in a game of our faction: it does nothing, and the report says why. Call it
        /// once per game, in Load; it is cleared for the next game by FeatureNotices.</summary>
        public static void ReportNoData(string id, string what)
        {
            if (string.IsNullOrEmpty(id)) return;
            bool isNew = !NoDataStates.ContainsKey(id);
            NoDataStates[id] = what ?? "";
            UnityEngine.Debug.LogWarning("[Pandaborn] " + id + " has no data in this game: " + what);
            if (isNew) Tell();
        }

        /// <summary>A new game starts: what features said about the last game (no data, reduced in that game) is gone.
        /// What they reported for the session stays.</summary>
        internal static void StartGame()
        {
            NoDataStates.Clear();
            DegradedInGame.Clear();
        }

        /// <summary>A loaded feature reports that it runs in its written fallback mode (vanilla behaviour) and why. The
        /// state holds until the game is closed: for something that stays true in every game of the session (a game member
        /// that is gone, a failure the feature reports only once).</summary>
        public static void ReportDegraded(string id, string reason)
        {
            if (string.IsNullOrEmpty(id)) return;
            bool isNew = !DegradedStates.ContainsKey(id);
            DegradedStates[id] = reason ?? "";
            UnityEngine.Debug.LogWarning("[Pandaborn] " + id + " runs in its fallback mode: " + reason);
            if (isNew) Tell();
        }

        /// <summary>As ReportDegraded, for something that is true of the running game only (its data, its faction, a
        /// failure while it loaded): forgotten when the next game starts. Call it in Load or later, in every game.</summary>
        public static void ReportDegradedInGame(string id, string reason)
        {
            if (string.IsNullOrEmpty(id)) return;
            bool isNew = !DegradedInGame.ContainsKey(id);
            DegradedInGame[id] = reason ?? "";
            UnityEngine.Debug.LogWarning("[Pandaborn] " + id + " runs in a reduced mode in this game: " + reason);
            if (isNew) Tell();
        }

        private static void Tell()
        {
            try { Reported?.Invoke(); }
            catch (Exception e) { UnityEngine.Debug.LogWarning("[Pandaborn] telling the player about a feature state failed: " + e.Message); }
        }

        public static FeatureState Get(string id) => States.FirstOrDefault(s => string.Equals(s.Id, id, StringComparison.OrdinalIgnoreCase));

        private static List<FeatureState> States
        {
            get
            {
                if (_states != null) return _states;
                var list = new List<FeatureState>();
                var text = AppDomain.CurrentDomain.GetData("Pandaborn.Boot.Report") as string ?? "";
                foreach (var line in text.Split(new[] { '\n' }, StringSplitOptions.RemoveEmptyEntries))
                {
                    var p = line.Split('\t');
                    if (p.Length < 2) continue;
                    var status = p[1] == "on" ? FeatureStatus.On : p[1] == "forced-off" ? FeatureStatus.ForcedOff : FeatureStatus.Off;
                    list.Add(new FeatureState(p[0], status, p.Length > 2 ? p[2] : ""));
                }
                _states = list;
                return _states;
            }
        }
    }
}
