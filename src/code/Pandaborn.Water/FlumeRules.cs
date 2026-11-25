using System;

namespace Pandaborn.Water
{
    /// <summary>The one status a flume piece shows (one cause, one status).</summary>
    public enum FlumeStatus
    {
        None,
        Misaligned,
        Blocked,
        IntakeDry,
        EndDry
    }

    /// <summary>What a flume piece found at one check. Plain values, so the rules below can be tested without the game.</summary>
    public struct FlumeFacts
    {
        /// <summary>The cell after the piece is solid (terrain, a levee, a post).</summary>
        public bool SolidAhead;
        /// <summary>The cell after the piece belongs to a flume or a valve channel.</summary>
        public bool NextIsChannel;
        /// <summary>That channel runs another way.</summary>
        public bool NextMisaligned;
        /// <summary>The cell before the piece belongs to a flume or a valve channel.</summary>
        public bool PrevIsChannel;
        public bool PrevMisaligned;
        /// <summary>A flume piece takes the water on: directly ahead, or out of the open cell ahead (a Flume Corner).</summary>
        public bool HasTaker;
        /// <summary>A flume piece brings the water: directly behind, or into the open cell behind (a Flume Corner).</summary>
        public bool HasFeeder;
        /// <summary>The piece is a Flume Gate that lets nothing through (set to zero, or shut by badwater).</summary>
        public bool GateClosed;
        public bool FirstCellWet;
        public bool LastCellWet;
        /// <summary>The water behind the first cell stands above the piece's bed.</summary>
        public bool WaterBehindAboveBed;
        /// <summary>A piece upstream already shows why no water comes (dry intake, badwater, missing corner, blocked).</summary>
        public bool UpstreamShowsCause;
        /// <summary>Checks in a row the end of the run has been dry (see <see cref="FlumeRules.NextDryChecks"/>).</summary>
        public int DryChecks;
    }

    /// <summary>
    /// The flume status rules, free of game types. A run is a chain of pieces from an intake (nothing brings it water but
    /// the pond behind it) to an end (nothing takes its water on). Each fault is reported once, on the piece where the
    /// player can fix it: a bend without a corner and a walled-off outlet on the piece itself, a dry intake on the first
    /// piece, a starved run on the last piece and only when nothing upstream already explains it.
    /// </summary>
    public static class FlumeRules
    {
        /// <summary>Dry checks (30 ticks apart) before the end of a run complains: about four game hours.</summary>
        public const int DryChecksBeforeAlarm = 4;

        /// <summary>No run is longer than this many pieces; also stops a walk around a loop of flumes.</summary>
        public const int MaxRunSteps = 512;

        public static bool IsIntake(in FlumeFacts f) => !f.HasFeeder;

        public static bool IsEnd(in FlumeFacts f) => !f.HasTaker;

        /// <summary>The dry counter of the end piece: it only counts while nothing upstream explains the drought, so the
        /// alarm waits its full delay again after a dry intake or a badwater shut-off clears and the water is on its way.</summary>
        public static int NextDryChecks(int previous, in FlumeFacts f)
        {
            if (!IsEnd(f) || f.LastCellWet || f.UpstreamShowsCause) return 0;
            return previous >= int.MaxValue - 1 ? previous : previous + 1;
        }

        public static FlumeStatus Resolve(in FlumeFacts f)
        {
            if ((f.NextIsChannel && f.NextMisaligned) || (f.PrevIsChannel && f.PrevMisaligned)) return FlumeStatus.Misaligned;
            if (f.SolidAhead && !f.NextIsChannel) return FlumeStatus.Blocked;
            bool intake = IsIntake(f);
            // a closed gate is its own state (its panel says so; badwater has its own status): its intake is not "dry"
            if (intake && !f.GateClosed && !f.FirstCellWet && !f.WaterBehindAboveBed) return FlumeStatus.IntakeDry;
            if (IsEnd(f) && !intake && !f.UpstreamShowsCause && f.DryChecks >= DryChecksBeforeAlarm) return FlumeStatus.EndDry;
            return FlumeStatus.None;
        }

        /// <summary>True when a status explains to the player why the pieces downstream are dry.</summary>
        public static bool IsCause(FlumeStatus status, bool gateClosedByBadwater) =>
            gateClosedByBadwater || status == FlumeStatus.Misaligned || status == FlumeStatus.Blocked || status == FlumeStatus.IntakeDry;

        /// <summary>Walks upstream from a piece (not counting the piece itself) and says whether any piece shows a cause.
        /// Bounded, so a ring of flumes ends the walk.</summary>
        public static bool AnyUpstream<T>(T start, Func<T, T> upstreamOf, Func<T, bool> showsCause) where T : class
        {
            var node = upstreamOf(start);
            for (int steps = 0; node != null && steps < MaxRunSteps; steps++)
            {
                if (ReferenceEquals(node, start)) return false;
                if (showsCause(node)) return true;
                node = upstreamOf(node);
            }
            return false;
        }

        /// <summary>Water to put back into a flow cell after a load: only what is missing, and at most one block (the
        /// inert obstacle that vanilla re-adds for a moment cuts no more than that).</summary>
        public static float MissingWater(float saved, float current)
        {
            if (float.IsNaN(saved) || float.IsNaN(current)) return 0f;
            float missing = saved - current;
            if (missing <= 0.01f) return 0f;
            return missing > 1f ? 1f : missing;
        }
    }

    /// <summary>
    /// The Flume Gate's badwater latch: shuts as soon as the water behind it is above the threshold, opens again only
    /// after it has stayed below half the threshold for a number of checks in a row.
    /// </summary>
    public struct BadwaterLatch
    {
        public bool Closed;
        public int ClearChecks;

        /// <summary>Feeds one reading. True when <see cref="Closed"/> changed.</summary>
        public bool Update(float contamination, float shutoff, int checksToReopen)
        {
            if (shutoff <= 0f || float.IsNaN(contamination)) return false;
            if (contamination > shutoff)
            {
                ClearChecks = 0;
                if (Closed) return false;
                Closed = true;
                return true;
            }
            if (!Closed) return false;
            if (contamination >= shutoff * 0.5f)
            {
                ClearChecks = 0;   // "stayed below": a reading in between starts the count again
                return false;
            }
            if (++ClearChecks < checksToReopen) return false;
            Closed = false;
            ClearChecks = 0;
            return true;
        }

        public void Reset()
        {
            Closed = false;
            ClearChecks = 0;
        }
    }

    /// <summary>The player's flow setting, snapped to the gate's step and kept inside its range.</summary>
    public static class GateFlow
    {
        public static float Snap(float flow, float step, float max)
        {
            if (float.IsNaN(flow) || float.IsInfinity(flow)) return 0f;
            if (max <= 0f) max = 1f;
            if (step > 0f) flow = (float)Math.Round(flow / step) * step;
            return flow < 0f ? 0f : flow > max ? max : flow;
        }
    }
}
