using System;

namespace Pandaborn.Ringtails
{
    /// <summary>
    /// The Ringtails' clock arithmetic, free of game types (hours are hours after dawn, 0..24).
    /// The one rule: Inkpaws work from dawn to the bell, Ringtails from the bell to dawn. The Ringtail shift never starts
    /// earlier than four hours after dawn (time to sleep) and never later than nightfall (Ringtails always hold the night).
    /// </summary>
    public static class ShiftMath
    {
        public const float DefaultMinStart = 4f;
        public const float DefaultMaxStart = 16f;

        /// <summary>Hours since dawn for a clock that counts from midnight-of-the-game-day.</summary>
        public static float HoursSinceDawn(float hoursPassedToday, float dawn)
        {
            float h = hoursPassedToday - dawn;
            if (float.IsNaN(h)) return 0f;
            h %= 24f;
            return h < 0f ? h + 24f : h;
        }

        /// <summary>The shift start: the bell (length of the Inkpaw working day) clamped to [min, max] and to nightfall.
        /// Bad data (min above max, a nightfall of zero) falls back to the defaults instead of an empty window.</summary>
        public static float ShiftStart(float workdayHours, float minStart, float maxStart, float nightfall)
        {
            if (float.IsNaN(workdayHours)) workdayHours = DefaultMaxStart;
            if (!(minStart >= 0f) || minStart >= 24f) minStart = DefaultMinStart;
            if (!(maxStart > 0f) || maxStart > 24f) maxStart = DefaultMaxStart;
            if (nightfall > 0f && nightfall < maxStart) maxStart = nightfall;
            if (minStart > maxStart) minStart = maxStart;
            return Math.Min(Math.Max(workdayHours, minStart), maxStart);
        }

        /// <summary>Length of the night shift that starts at <paramref name="shiftStart"/> and ends at dawn.</summary>
        public static float NightShiftHours(float shiftStart)
        {
            float h = 24f - shiftStart;
            return h < 0f ? 0f : h > 24f ? 24f : h;
        }

        /// <summary>True when <paramref name="hour"/> lies in [start, end); a window whose end is before its start wraps
        /// over dawn; an empty window (start == end) holds nothing.</summary>
        public static bool InWindow(float hour, float start, float end)
        {
            if (start == end) return false;
            return start < end ? hour >= start && hour < end : hour >= start || hour < end;
        }

        /// <summary>True on the frame the clock passes the shift start (not on a jump of two hours or more: a load, a skipped
        /// night, the clock wrapping at dawn).</summary>
        public static bool CrossedShiftStart(float lastHour, float hour, float start)
        {
            return lastHour >= 0f && lastHour < start && hour >= start && hour - lastHour < 2f;
        }
    }

    /// <summary>What a Moon Loft's nursery does at dawn, and says on its panel.</summary>
    public enum KitState
    {
        /// <summary>The loft is not in a district (unconnected), or the Ringtails have not arrived: nothing to say.</summary>
        None,
        /// <summary>No Ringtail lives in the district at all: the loft's lantern invites a new family after a wait.</summary>
        Inviting,
        /// <summary>Kits are growing but no adult lives in the district yet.</summary>
        NoParents,
        Hungry,
        WaitingForJobs,
        NoRoom,
        Raising
    }

    /// <summary>
    /// The population valve (DESIGN.md: "kits are raised in the Moon Loft while there is work for them"), free of game
    /// types. Open night jobs = desired workers of the district's finished Ringtail posts minus Ringtail adults minus kits
    /// already growing. Kits never outnumber the jobs waiting for them, nobody is born into a famine, and a district that
    /// has lost every Ringtail gets a new family rather than staying empty for ever.
    /// </summary>
    public static class KitValve
    {
        public static int OpenJobs(int desiredWorkers, int ringtailAdults, int ringtailKits) => desiredWorkers - ringtailAdults - ringtailKits;

        public static KitState Decide(int ringtailAdults, int ringtailKits, bool anyoneStarving, int openJobs, bool roomForKit)
        {
            if (ringtailAdults <= 0) return ringtailKits > 0 ? KitState.NoParents : KitState.Inviting;
            if (anyoneStarving) return KitState.Hungry;
            if (openJobs <= 0) return KitState.WaitingForJobs;
            return roomForKit ? KitState.Raising : KitState.NoRoom;
        }

        /// <summary>Kits one loft raises this dawn.</summary>
        public static int KitsToRaise(KitState state, int kitsPerDay, int openJobs)
        {
            if (state != KitState.Raising) return 0;
            return Math.Max(0, Math.Min(Math.Max(1, kitsPerDay), openJobs));
        }

        /// <summary>
        /// The return of the Ringtails. A district with a finished Moon Loft and no living Ringtail counts its empty dawns;
        /// after <paramref name="waitDays"/> of them in a row (and while nobody starves) a new family is invited. Returns the
        /// new count; <paramref name="invite"/> is set on the dawn the family comes. Any Ringtail in the district resets it.
        /// </summary>
        public static int NextEmptyDawns(int emptyDawns, bool districtHasLoft, int ringtailsInDistrict, bool anyoneStarving, int waitDays, out bool invite)
        {
            invite = false;
            if (!districtHasLoft || ringtailsInDistrict > 0) return 0;
            if (waitDays < 1) waitDays = 1;
            int next = emptyDawns < 0 ? 1 : emptyDawns >= int.MaxValue - 1 ? emptyDawns : emptyDawns + 1;
            if (next >= waitDays && !anyoneStarving)
            {
                invite = true;
                return 0;
            }
            return next;
        }

        public static string LocKey(KitState state)
        {
            switch (state)
            {
                case KitState.Inviting: return "Pandaborn.Ringtails.Loft.Inviting";
                case KitState.NoParents: return "Pandaborn.Ringtails.Loft.NoParents";
                case KitState.Hungry: return "Pandaborn.Ringtails.Loft.Hungry";
                case KitState.WaitingForJobs: return "Pandaborn.Ringtails.Loft.WaitingForJobs";
                case KitState.NoRoom: return "Pandaborn.Ringtails.Loft.NoRoom";
                case KitState.Raising: return "Pandaborn.Ringtails.Loft.Raising";
                default: return "";
            }
        }
    }
}
