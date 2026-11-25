using System;

namespace Pandaborn.Flowering
{
    public enum FloweringPhase
    {
        Idle,
        /// <summary>Announced at the start of the cycle before; flowers at the start of NextCycle.</summary>
        Announced,
        /// <summary>The species is in flower: its grown plants bear seed for SeedDays, then die.</summary>
        Flowering,
        /// <summary>The flowered plants are dead; young plants of the species do not grow until DormantDays have passed.</summary>
        Resting
    }

    /// <summary>What the schedule asks for at a cycle start, a load or a change of the setting.</summary>
    public enum ScheduleStep
    {
        None,
        /// <summary>The setting is off and a Flowering is announced: withdraw it.</summary>
        Cancel,
        /// <summary>The announced Flowering is due and it is the first day of a cycle: it happens now.</summary>
        Flower,
        /// <summary>The announced Flowering is due but the cycle's first day has passed (a load, the code switched back
        /// on): it moves to the start of the next cycle.</summary>
        Postpone,
        /// <summary>The next Flowering is at most one cycle away: announce it.</summary>
        Announce
    }

    /// <summary>How a flowered plant's seed time ends.</summary>
    public enum TwinEnd
    {
        /// <summary>Not yet, or nothing to do: it was cut for its seed (a cut plant is dead already) or died before.</summary>
        None,
        /// <summary>On a tile with a planting mark: it dies where it stands and the farm or forester replants the tile
        /// from the mark, as any dead crop or cut tree.</summary>
        Dies,
        /// <summary>Wild (no planting mark) and still standing: it reseeds its own tile. A seedling of its species takes its
        /// place and rests like every other young plant until the rest days end.</summary>
        Reseeds
    }

    /// <summary>
    /// The Great Flowering's calendar, free of game types so it is tested without the game (src/code/tests/Events). The
    /// promises it keeps (DESIGN.md Pillar 5): never before FirstCycle; always on the first day of a cycle; announced at
    /// least one full cycle ahead; the next one MinCycles to MaxCycles after the last.
    /// </summary>
    public static class FloweringSchedule
    {
        /// <summary>The cycle the schedule aims at before the warning rule: the first Flowering's cycle, or the last one
        /// plus the drawn interval.</summary>
        public static int BaseCycle(int lastCycle, int firstCycle, int rareDelayCycles, bool rare, int drawnInterval) =>
            lastCycle < 0 ? firstCycle + (rare ? rareDelayCycles : 0) : lastCycle + drawnInterval;

        /// <summary>An interval between Flowerings, min to max cycles inclusive (the two may come in either order).</summary>
        public static int DrawInterval(Random random, int min, int max) => random.Next(Math.Min(min, max), Math.Max(min, max) + 1);

        /// <summary>
        /// The cycle the next Flowering is set for: the base cycle, but never so near that its announcement (at the start
        /// of the cycle before) could not give a full cycle of warning. On the first day of a cycle with nothing under way
        /// the announcement can still be made today for the next cycle; otherwise the earliest is the cycle after next.
        /// </summary>
        public static int Schedule(int baseCycle, int cycle, bool idleOnFirstDay) => Math.Max(baseCycle, cycle + (idleOnFirstDay ? 1 : 2));

        public static ScheduleStep Step(bool settingOff, FloweringPhase phase, int cycle, int cycleDay, int nextCycle)
        {
            if (settingOff) return phase == FloweringPhase.Announced ? ScheduleStep.Cancel : ScheduleStep.None;
            if (phase == FloweringPhase.Announced && cycle >= nextCycle) return cycleDay <= 1 ? ScheduleStep.Flower : ScheduleStep.Postpone;
            if (phase == FloweringPhase.Idle && cycle >= nextCycle - 1) return ScheduleStep.Announce;
            return ScheduleStep.None;
        }

        /// <summary>
        /// The cycle an announcement made now names. Made on the first day of a cycle it names the next cycle; made later
        /// (a load, a change of the setting) it names the cycle after next, so the warning is never shorter than a cycle.
        /// <paramref name="test"/>: a test announcement keeps the next cycle.
        /// </summary>
        public static int AnnouncedCycle(int nextCycle, int cycle, int cycleDay, bool test)
        {
            if (nextCycle <= cycle) nextCycle = cycle + 1;
            if (!test && cycleDay > 1 && nextCycle < cycle + 2) nextCycle = cycle + 2;
            return nextCycle;
        }

        /// <summary>When a flowered plant dies: spread over the last day of the seed time (over all of it when the seed
        /// time is shorter than a day), by a number in [0, 1) fixed for its tile.</summary>
        public static float DieAt(float floweringDay, float seedDays, float hash01)
        {
            float window = Math.Min(1f, Math.Max(0f, seedDays));
            return floweringDay + Math.Max(0f, seedDays) - window + hash01 * window;
        }

        /// <summary>
        /// What happens to a flowered plant now (ruling of 2026-11-25 on wild bamboo). Only a plant that is still alive
        /// when its time comes has an end to meet: one that was cut for its seed died at the cut and is gone, like any
        /// wild tree that is cut, whatever its tile. <paramref name="reseedingWorks"/>: false once replacing plants has
        /// failed in this game; wild plants then die where they stand, as marked ones do.
        /// </summary>
        public static TwinEnd EndOf(bool alive, bool markedTile, float now, float dieAt, bool reseedingWorks = true)
        {
            if (!alive || now < dieAt) return TwinEnd.None;
            return markedTile || !reseedingWorks ? TwinEnd.Dies : TwinEnd.Reseeds;
        }

        /// <summary>A number in [0, 1) fixed for a tile.</summary>
        public static float Hash01(int x, int y, int z)
        {
            unchecked
            {
                int h = x * 73856093 ^ y * 19349663 ^ z * 83492791;
                return ((h & 0x7fffffff) % 1000) / 1000f;
            }
        }

        /// <summary>Seed the players harvested: what the flowered plants bore minus what died with them.</summary>
        public static int Harvested(int borne, int lost) => Math.Max(0, borne - lost);
    }
}
