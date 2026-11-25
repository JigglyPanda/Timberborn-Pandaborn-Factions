using System;
using System.Collections.Generic;
using Pandaborn.Festival;
using Pandaborn.Flowering;

namespace Pandaborn.Events.Tests
{
    /// <summary>
    /// The promises of DESIGN.md Pillar 5 that are pure arithmetic, checked without the game. The Flowering's calendar is
    /// played over many cycles with every interval the data allows, in each setting, with loads and setting changes in
    /// the middle of cycles; the festival's once-a-cycle rule, its dishes and the show's launch times are checked on
    /// small cases. What needs the game (plants, colonists, the sky) is listed in docs/tech/events.md.
    /// </summary>
    public static class Program
    {
        private static int _checks;
        private static int _failures;

        public static int Main()
        {
            FloweringNeverBeforeFirstCycle();
            FloweringAnnouncedAFullCycleAhead();
            FloweringLateAnnouncementsWaitACycleMore();
            FloweringOverdueMovesToNextCycleStart();
            FloweringOffCancels();
            FloweringLongRun();
            FloweringDeaths();
            FloweringWildGrove();
            FestivalOncePerCycle();
            FestivalDishes();
            FestivalShowTimes();
            FestivalSky();
            Console.WriteLine(_failures == 0 ? "OK: " + _checks + " checks" : "FAILED: " + _failures + " of " + _checks + " checks");
            return _failures == 0 ? 0 : 1;
        }

        private static void Check(bool ok, string what)
        {
            _checks++;
            if (ok) return;
            _failures++;
            Console.WriteLine("FAIL: " + what);
        }

        // ------------------------------------------------------------------ the Flowering's calendar

        // the catalogue's numbers (catalogue/faction.toml, PandabornFloweringSpec)
        private const int First = 6, NormalMin = 5, NormalMax = 7, RareMin = 9, RareMax = 11, RareDelay = 3;

        private static void FloweringNeverBeforeFirstCycle()
        {
            // a new game, cycle 1 day 1, nothing held yet
            int baseCycle = FloweringSchedule.BaseCycle(-1, First, RareDelay, false, 5);
            Check(baseCycle == 6, "first Flowering aims at cycle 6");
            Check(FloweringSchedule.Schedule(baseCycle, 1, true) == 6, "scheduled for cycle 6 from cycle 1");
            Check(FloweringSchedule.BaseCycle(-1, First, RareDelay, true, 9) == 9, "rare: first at cycle 9");
            for (int cycle = 1; cycle <= 4; cycle++)
                Check(FloweringSchedule.Step(false, FloweringPhase.Idle, cycle, 1, 6) == ScheduleStep.None, "nothing at the start of cycle " + cycle);
            Check(FloweringSchedule.Step(false, FloweringPhase.Idle, 5, 1, 6) == ScheduleStep.Announce, "announced at the start of cycle 5");
            Check(FloweringSchedule.AnnouncedCycle(6, 5, 1, false) == 6, "the announcement of cycle 5 names cycle 6");
            Check(FloweringSchedule.Step(false, FloweringPhase.Announced, 5, 9, 6) == ScheduleStep.None, "nothing more during cycle 5");
            Check(FloweringSchedule.Step(false, FloweringPhase.Announced, 6, 1, 6) == ScheduleStep.Flower, "flowers on day 1 of cycle 6");
            // a game first played with the mod in a late cycle: still a full cycle of warning
            Check(FloweringSchedule.Schedule(6, 20, true) == 21, "first seen on day 1 of cycle 20: cycle 21");
            Check(FloweringSchedule.Schedule(6, 20, false) == 22, "first seen later in cycle 20: cycle 22");
        }

        private static void FloweringAnnouncedAFullCycleAhead()
        {
            // right after a Flowering in cycle c the next one is drawn; even an interval of 1 leaves a whole cycle between
            // the announcement (start of next - 1) and the Flowering
            for (int c = 6; c < 40; c++)
                for (int interval = 1; interval <= 11; interval++)
                {
                    int next = FloweringSchedule.Schedule(FloweringSchedule.BaseCycle(c, First, RareDelay, false, interval), c, false);
                    Check(next - 1 > c, "after cycle " + c + " with interval " + interval + ": the announcing cycle " + (next - 1) + " is still ahead");
                    Check(next >= c + interval, "the interval is never shortened");
                }
        }

        private static void FloweringLateAnnouncementsWaitACycleMore()
        {
            // the code was off at the start of cycle 5 and is back on day 4 of cycle 7: announced now, for cycle 9
            Check(FloweringSchedule.Step(false, FloweringPhase.Idle, 7, 4, 6) == ScheduleStep.Announce, "overdue and idle: announce");
            Check(FloweringSchedule.AnnouncedCycle(6, 7, 4, false) == 9, "announced on day 4 of cycle 7: cycle 9");
            Check(FloweringSchedule.AnnouncedCycle(8, 7, 4, false) == 9, "a date one cycle away moves on when announced late");
            Check(FloweringSchedule.AnnouncedCycle(8, 7, 1, false) == 8, "announced on day 1: the next cycle");
            Check(FloweringSchedule.AnnouncedCycle(12, 7, 4, false) == 12, "a date far enough stays");
            Check(FloweringSchedule.AnnouncedCycle(8, 7, 4, true) == 8, "a test announcement keeps the next cycle");
            for (int cycle = 1; cycle < 30; cycle++)
                for (int day = 1; day <= 20; day++)
                    for (int next = 0; next <= cycle + 1; next++)
                    {
                        int named = FloweringSchedule.AnnouncedCycle(next, cycle, day, false);
                        Check(named > cycle && (day <= 1 || named >= cycle + 2), "cycle " + cycle + " day " + day + " next " + next + ": warning of a full cycle");
                    }
        }

        private static void FloweringOverdueMovesToNextCycleStart()
        {
            Check(FloweringSchedule.Step(false, FloweringPhase.Announced, 6, 3, 6) == ScheduleStep.Postpone, "announced, loaded on day 3 of its cycle: postponed");
            Check(FloweringSchedule.Step(false, FloweringPhase.Announced, 8, 1, 6) == ScheduleStep.Flower, "announced, overdue, day 1: flowers");
            Check(FloweringSchedule.Step(false, FloweringPhase.Flowering, 9, 1, 12) == ScheduleStep.None, "in flower: the calendar waits");
            Check(FloweringSchedule.Step(false, FloweringPhase.Resting, 12, 1, 12) == ScheduleStep.None, "resting: the calendar waits, even when the next is due");
        }

        private static void FloweringOffCancels()
        {
            Check(FloweringSchedule.Step(true, FloweringPhase.Announced, 5, 1, 6) == ScheduleStep.Cancel, "off while announced: cancelled");
            Check(FloweringSchedule.Step(true, FloweringPhase.Idle, 9, 1, 6) == ScheduleStep.None, "off and idle: nothing, however overdue");
            Check(FloweringSchedule.Step(true, FloweringPhase.Flowering, 6, 2, 6) == ScheduleStep.None, "off while in flower: it runs its course");
        }

        /// <summary>The calendar played for 400 cycles as FloweringService plays it, per setting and seed.</summary>
        private static void FloweringLongRun()
        {
            foreach (bool rare in new[] { false, true })
                for (int seed = 0; seed < 25; seed++)
                {
                    var random = new Random(seed);
                    int min = rare ? RareMin : NormalMin, max = rare ? RareMax : NormalMax;
                    var phase = FloweringPhase.Idle;
                    int next = -1, last = -1, announcedIn = -1, flowerings = 0, species = 0, lastSpecies = -1;
                    for (int cycle = 1; cycle <= 400; cycle++)
                    {
                        // start of the cycle (CycleStartedEvent): day 1
                        if (next < 0)
                            next = FloweringSchedule.Schedule(FloweringSchedule.BaseCycle(last, First, RareDelay, rare, FloweringSchedule.DrawInterval(random, min, max)),
                                                              cycle, phase == FloweringPhase.Idle);
                        switch (FloweringSchedule.Step(false, phase, cycle, 1, next))
                        {
                            case ScheduleStep.Announce:
                                next = FloweringSchedule.AnnouncedCycle(next, cycle, 1, false);
                                phase = FloweringPhase.Announced;
                                announcedIn = cycle;
                                break;
                            case ScheduleStep.Flower:
                                Check(cycle >= First + (rare ? RareDelay : 0), "never before the first cycle (" + cycle + ")");
                                Check(announcedIn == cycle - 1, "announced exactly one cycle ahead (announced " + announcedIn + ", flowered " + cycle + ")");
                                if (last >= 0) Check(cycle - last >= min && cycle - last <= max, "interval " + (cycle - last) + " within " + min + ".." + max);
                                Check(species != lastSpecies, "one species at a time, alternating");
                                lastSpecies = species;
                                species = (species + 1) % 2;
                                last = cycle;
                                flowerings++;
                                // FloweringService.Flower: the next one is drawn while this one is in flower
                                next = FloweringSchedule.Schedule(FloweringSchedule.BaseCycle(last, First, RareDelay, rare, FloweringSchedule.DrawInterval(random, min, max)),
                                                                  cycle, false);
                                phase = FloweringPhase.Idle;   // the rest (9 days) ends within the cycle in this run
                                break;
                            case ScheduleStep.Postpone:
                                Check(false, "nothing is postponed in an unbroken game");
                                break;
                        }
                    }
                    Check(flowerings >= 400 / max - 2 && flowerings <= 400 / min + 1, (rare ? "rare" : "normal") + " seed " + seed + ": " + flowerings + " Flowerings in 400 cycles");
                }
        }

        private static void FloweringDeaths()
        {
            // 3 seed days from day 100: every flowered plant dies in the last day, none before day 102
            var seen = new HashSet<int>();
            for (int x = 0; x < 60; x++)
                for (int y = 0; y < 60; y++)
                {
                    float h = FloweringSchedule.Hash01(x, y, 3);
                    Check(h >= 0f && h < 1f, "hash in [0,1)");
                    float dieAt = FloweringSchedule.DieAt(100f, 3f, h);
                    Check(dieAt >= 102f && dieAt < 103f, "dies in the last day");
                    seen.Add((int)(h * 24));
                }
            Check(seen.Count == 24, "deaths fall in every hour of the last day (" + seen.Count + " of 24)");
            Check(FloweringSchedule.DieAt(100f, 0.5f, 0.5f) >= 100f && FloweringSchedule.DieAt(100f, 0.5f, 0.999f) < 100.5f, "a seed time under a day: spread over all of it");
            Check(FloweringSchedule.Harvested(168, 17) == 151 && FloweringSchedule.Harvested(3, 9) == 0, "seed harvested = borne - lost, never negative");
        }

        /// <summary>The ruling of 2026-11-25 on wild bamboo, on a grove played hour by hour: 3 seed days from day 100;
        /// 40 flowered plants on marked tiles (a farm), 60 wild ones, of which every third is cut for its seed on day 101.</summary>
        private static void FloweringWildGrove()
        {
            // the rule itself
            Check(FloweringSchedule.EndOf(true, false, 102.5f, 102.4f) == TwinEnd.Reseeds, "wild, standing, due: reseeds its tile");
            Check(FloweringSchedule.EndOf(true, true, 102.5f, 102.4f) == TwinEnd.Dies, "marked tile, due: dies where it stands (the farm replants)");
            Check(FloweringSchedule.EndOf(true, false, 102.3f, 102.4f) == TwinEnd.None, "not due yet: nothing");
            Check(FloweringSchedule.EndOf(false, false, 102.5f, 102.4f) == TwinEnd.None, "cut for its seed (dead at the cut): gone, no seedling");
            Check(FloweringSchedule.EndOf(false, true, 102.5f, 102.4f) == TwinEnd.None, "cut on a marked tile: nothing more to do");
            Check(FloweringSchedule.EndOf(true, false, 102.5f, 102.4f, false) == TwinEnd.Dies, "reseeding broken in this game: wild ones die as before");

            const float day = 100f, seedDays = 3f;
            int reseeded = 0, diedStanding = 0, cutGone = 0, early = 0;
            var alive = new bool[100];
            var marked = new bool[100];
            for (int i = 0; i < 100; i++) { alive[i] = true; marked[i] = i < 40; }
            for (int hour = 0; hour <= 3 * 24 + 1; hour++)
            {
                float now = day + hour / 24f;
                if (hour == 30)
                    for (int i = 40; i < 100; i += 3) { alive[i] = false; cutGone++; }   // lumberjacks and farmers: a cut plant dies at the cut
                for (int i = 0; i < 100; i++)
                {
                    float dieAt = FloweringSchedule.DieAt(day, seedDays, FloweringSchedule.Hash01(i % 10, i / 10, 2));
                    switch (FloweringSchedule.EndOf(alive[i], marked[i], now, dieAt))
                    {
                        case TwinEnd.Reseeds: alive[i] = false; reseeded++; if (now < day + 2f) early++; Check(!marked[i], "only wild tiles reseed"); break;
                        case TwinEnd.Dies: alive[i] = false; diedStanding++; if (now < day + 2f) early++; Check(marked[i], "marked tiles die standing"); break;
                    }
                }
            }
            Check(cutGone == 20, "20 wild plants cut for their seed");
            Check(reseeded == 40, "the 40 wild plants still standing reseed their tiles (" + reseeded + ")");
            Check(diedStanding == 40, "the 40 on marked tiles die where they stand (" + diedStanding + ")");
            Check(early == 0, "none before the last seed day");
            bool anyAlive = false;
            foreach (bool a in alive) anyAlive |= a;
            Check(!anyAlive, "no flowered plant outlives the seed time");
        }

        // ------------------------------------------------------------------ the festival

        private static void FestivalOncePerCycle()
        {
            Check(FestivalRules.NextAllowedCycle(-1) == 0, "no festival yet: any cycle");
            Check(FestivalRules.NextAllowedCycle(3) == 4, "held in cycle 3: again from cycle 4");
            Check(FestivalRules.FestivalDayFor(41) == 42, "called on day 41: held on day 42, whatever the hour");
        }

        private static KeyValuePair<string, int> Dish(string id, int amount) => new KeyValuePair<string, int>(id, amount);

        private static void FestivalDishes()
        {
            var stock = new[] { Dish("Rice", 45), Dish("Pickles", 23), Dish("Shoots", 12), Dish("HotPot", 80), Dish("Cakes", 20) };
            var picked = FestivalRules.PickDishes(stock, 3, 20);
            Check(string.Join(",", picked) == "HotPot,Rice,Pickles", "the three most plentiful with 20 or more: " + string.Join(",", picked));
            Check(FestivalRules.PickDishes(stock, 3, 30).Count == 2, "only two kinds with 30: not ready");
            Check(FestivalRules.PickDishes(new[] { Dish("A", 20), Dish("B", 20), Dish("C", 20), Dish("D", 20) }, 3, 20)[2] == "C", "ties keep the order given");
            Check(FestivalRules.PickDishes(new[] { Dish("A", 20), Dish("A", 50), Dish("B", 20) }, 3, 20).Count == 2, "a dish listed twice counts once");
            Check(FestivalRules.PickDishes(stock, 0, 20).Count == 0, "no dishes asked: none taken");
        }

        private static void FestivalShowTimes()
        {
            var due = new List<int>();
            // 24 lanterns over 0.3 h from 15.75 h, read every game tick (24 h / 768)
            const float tick = 24f / 768f;
            var launched = new int[24];
            float from = 15.4f;
            for (float now = from + tick; now < 22.5f; now += tick)
            {
                FestivalRules.Due(15.75f, 0.3f, 24, from, now, due);
                foreach (int i in due) launched[i]++;
                from = now;
            }
            bool once = true;
            foreach (int n in launched) once &= n == 1;
            Check(once, "every lantern of the release exactly once, ticking through it");

            FestivalRules.Due(15.75f, 0.3f, 24, 15.0f, 23.0f, due);
            Check(due.Count == 24, "a jump over the whole release launches all 24");
            FestivalRules.Due(15.75f, 0.3f, 24, 15.9f, 23.0f, due);
            Check(due.Count == 11 && due[0] == 13, "a load at 15.9 h launches only the 11 still due (" + due.Count + ")");
            FestivalRules.Due(15.75f, 0.3f, 24, 16.2f, 23.0f, due);
            Check(due.Count == 0, "a load after the release launches none");
            FestivalRules.Due(19f, 2.5f, 20, 19f, 21.5f, due);
            Check(due.Count == 19 && due[0] == 1, "bursts: the one at exactly 19 h belongs to the tick that reaches 19 h");
            FestivalRules.Due(19f, 2.5f, 20, 18.99f, 19f, due);
            Check(due.Count == 1 && due[0] == 0, "and is launched by it");
            FestivalRules.Due(15.75f, 1.75f, 0, 0f, 24f, due);
            Check(due.Count == 0, "none asked: none");
            FestivalRules.Due(15.75f, 1.75f, 24, 20f, 20f, due);
            Check(due.Count == 0, "the clock did not move: none");
        }

        private static void FestivalSky()
        {
            // the numbers the module and the prefab share (FestivalService.SkyLanternsPerSecond, MakeLanternRise's life)
            float aloft = FestivalRules.SteadySkyLanterns(0.65f, 25f, 40f);
            Check(aloft >= 15f && aloft <= 30f, "the sky holds 15 to 30 lanterns once it has filled (" + aloft + ")");
            Check(1f / 0.65f >= 1f && 1f / 0.65f <= 4f, "a new lantern every few seconds");
        }
    }
}
