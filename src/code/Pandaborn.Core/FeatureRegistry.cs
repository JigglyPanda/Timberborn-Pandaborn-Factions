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
