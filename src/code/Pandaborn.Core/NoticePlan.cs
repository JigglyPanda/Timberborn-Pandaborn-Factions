using System;
using System.Collections.Generic;
using System.Linq;

namespace Pandaborn.Core
{
    internal enum ProblemKind
    {
        Off,
        ForcedOff,
        Degraded,
        NoData,
        Duplicate
    }

    internal sealed class Problem
    {
        public readonly ProblemKind Kind;
        public readonly string Id;
        public readonly string Detail;

        public Problem(ProblemKind kind, string id, string detail)
        {
            Kind = kind;
            Id = id;
            Detail = detail ?? "";
        }
    }

    /// <summary>
    /// What the player is told about the mod's features, and when. The rule: nothing while everything works; one message
    /// when something does not.
    /// * A feature that is switched off (it failed its check against this game version, or its file is missing) is
    ///   announced at every load: its buildings are still in the toolbar and behave as plainer ones, and a player who
    ///   opens the save a week later must not have to remember why.
    /// * Everything else (a reduced mode, no data, a developer setting, the mod enabled twice) is announced once per
    ///   save, and again only when the set of problems changes.
    /// No game types here: tests/Foundation reads this file directly.
    /// </summary>
    internal static class NoticePlan
    {
        public static List<Problem> Problems(IEnumerable<FeatureState> states, IReadOnlyDictionary<string, string> degraded,
                                             IReadOnlyDictionary<string, string> noData, int duplicateCopies)
        {
            var problems = new List<Problem>();
            var off = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (var s in states)
            {
                if (s.IsOn) continue;
                off.Add(s.Id);
                problems.Add(new Problem(s.Status == FeatureStatus.ForcedOff ? ProblemKind.ForcedOff : ProblemKind.Off, s.Id, s.Reason));
            }
            // a feature that has no data does nothing, so "reduced" says nothing more about it
            foreach (var n in noData.Where(n => !off.Contains(n.Key)).OrderBy(n => n.Key, StringComparer.Ordinal))
                problems.Add(new Problem(ProblemKind.NoData, n.Key, n.Value));
            foreach (var d in degraded.Where(d => !off.Contains(d.Key) && !noData.ContainsKey(d.Key)).OrderBy(d => d.Key, StringComparer.Ordinal))
                problems.Add(new Problem(ProblemKind.Degraded, d.Key, d.Value));
            if (duplicateCopies > 0) problems.Add(new Problem(ProblemKind.Duplicate, "", duplicateCopies.ToString(System.Globalization.CultureInfo.InvariantCulture)));
            return problems;
        }

        /// <summary>Which problems there are, without their reasons ("" when there are none): what a save remembers having
        /// been told. A reason that changes its wording is not news; a feature that joins or leaves the list is.</summary>
        public static string Signature(IEnumerable<Problem> problems) =>
            string.Join(";", problems.Select(p => p.Kind == ProblemKind.Duplicate ? "Duplicate" : p.Id + "=" + p.Kind).OrderBy(s => s, StringComparer.Ordinal));

        public static bool EveryLoad(IEnumerable<Problem> problems) => problems.Any(p => p.Kind == ProblemKind.Off);

        /// <summary>True when the message is due now.</summary>
        /// <param name="signature">the problems of this game</param>
        /// <param name="toldInSave">the signature the save was last told ("" or null: none)</param>
        /// <param name="toldThisLoad">the signature already posted since this game was loaded (null: none)</param>
        public static bool Due(string signature, bool everyLoad, string toldInSave, string toldThisLoad)
        {
            if (string.IsNullOrEmpty(signature)) return false;
            if (signature == toldThisLoad) return false;
            return everyLoad || signature != (toldInSave ?? "");
        }
    }
}
