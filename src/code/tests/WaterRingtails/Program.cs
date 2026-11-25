using System;
using System.Collections.Generic;
using Pandaborn.Ringtails;
using Pandaborn.Water;

namespace Pandaborn.WaterRingtails.Tests
{
    /// <summary>
    /// The promises of DESIGN.md Pillars 1 and 4 that are pure arithmetic, checked without the game: a flume never fails
    /// silently and one cause gives one status; the gate shuts on badwater and opens only after the water has stayed
    /// clean; Ringtails start between four hours after dawn and nightfall; kits only while night jobs are open and
    /// nobody starves; a district that lost its Ringtails gets a family back after a wait. What needs the game (water,
    /// colonists, statuses on screen) is listed in docs/tech/water.md and docs/tech/two-peoples.md, "Review 2026-11-25".
    /// </summary>
    public static class Program
    {
        private static int _checks;
        private static int _failures;

        public static int Main()
        {
            FlumeOneCauseOneStatus();
            FlumeRunWalk();
            FlumeDryCounter();
            FlumeWaterPutBack();
            GateLatch();
            GateFlowSetting();
            ShiftWindow();
            ShiftClapper();
            KitValveRules();
            ReturnOfTheRingtails();
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

        private static void Eq(float actual, float expected, string what) =>
            Check(Math.Abs(actual - expected) < 1e-4f, what + ": " + actual + " instead of " + expected);

        // ------------------------------------------------------------------ flumes

        /// <summary>A middle piece of a healthy, running line.</summary>
        private static FlumeFacts Middle() => new FlumeFacts
        {
            NextIsChannel = true, PrevIsChannel = true, HasFeeder = true, HasTaker = true,
            FirstCellWet = true, LastCellWet = true, WaterBehindAboveBed = true
        };

        private static void FlumeOneCauseOneStatus()
        {
            Check(FlumeRules.Resolve(Middle()) == FlumeStatus.None, "a running middle piece shows nothing");

            // the intake: dry, and the pond behind it is below its bed
            var intake = Middle();
            intake.PrevIsChannel = false; intake.HasFeeder = false; intake.FirstCellWet = false; intake.LastCellWet = false; intake.WaterBehindAboveBed = false;
            Check(FlumeRules.Resolve(intake) == FlumeStatus.IntakeDry, "a dry intake says so");
            intake.WaterBehindAboveBed = true;
            Check(FlumeRules.Resolve(intake) == FlumeStatus.None, "an intake with water above its bed behind it is filling, not dry");
            intake.WaterBehindAboveBed = false; intake.GateClosed = true;
            Check(FlumeRules.Resolve(intake) == FlumeStatus.None, "a closed gate is not a dry intake");

            // the end of the same run: dry for long enough, but the intake already says why
            var end = Middle();
            end.NextIsChannel = false; end.HasTaker = false; end.FirstCellWet = false; end.LastCellWet = false;
            end.DryChecks = FlumeRules.DryChecksBeforeAlarm;
            Check(FlumeRules.Resolve(end) == FlumeStatus.EndDry, "a starved end says so when nothing upstream explains it");
            end.UpstreamShowsCause = true;
            Check(FlumeRules.Resolve(end) == FlumeStatus.None, "one cause, one status: a dry intake silences the end of its run");
            end.UpstreamShowsCause = false; end.DryChecks = FlumeRules.DryChecksBeforeAlarm - 1;
            Check(FlumeRules.Resolve(end) == FlumeStatus.None, "the end waits before it complains");

            // the last flume before a Paddy Spout is the end of its run (the spout is a channel, not a taker)
            var beforeSpout = Middle();
            beforeSpout.HasTaker = false; beforeSpout.LastCellWet = false; beforeSpout.DryChecks = 10;
            Check(FlumeRules.Resolve(beforeSpout) == FlumeStatus.EndDry, "the flume before a spout reports a starved run");

            // a corner: the piece before it has a taker, the piece after it a feeder; neither is an end or an intake
            var beforeCorner = Middle();
            beforeCorner.NextIsChannel = false; beforeCorner.LastCellWet = false; beforeCorner.DryChecks = 10;
            Check(FlumeRules.Resolve(beforeCorner) == FlumeStatus.None, "the piece before a corner is not the end of the run");
            var afterCorner = Middle();
            afterCorner.PrevIsChannel = false; afterCorner.FirstCellWet = false; afterCorner.WaterBehindAboveBed = false;
            Check(FlumeRules.Resolve(afterCorner) == FlumeStatus.None, "the piece after a corner is not an intake");

            // build faults sit on the piece itself and come first
            var bend = Middle();
            bend.NextMisaligned = true;
            Check(FlumeRules.Resolve(bend) == FlumeStatus.Misaligned, "a bend without a corner says so");
            bend.SolidAhead = true; bend.LastCellWet = false; bend.DryChecks = 10;
            Check(FlumeRules.Resolve(bend) == FlumeStatus.Misaligned, "a piece shows one status even with several faults");
            var wall = Middle();
            wall.NextIsChannel = false; wall.HasTaker = false; wall.SolidAhead = true;
            Check(FlumeRules.Resolve(wall) == FlumeStatus.Blocked, "a walled-off outlet says so");
            wall.NextIsChannel = true;
            Check(FlumeRules.Resolve(wall) != FlumeStatus.Blocked, "a valve channel ahead is not a wall");

            Check(FlumeRules.IsCause(FlumeStatus.IntakeDry, false) && FlumeRules.IsCause(FlumeStatus.Misaligned, false)
                  && FlumeRules.IsCause(FlumeStatus.Blocked, false) && FlumeRules.IsCause(FlumeStatus.None, true),
                  "a dry intake, a missing corner, a wall and a badwater shut-off explain a dry run");
            Check(!FlumeRules.IsCause(FlumeStatus.EndDry, false) && !FlumeRules.IsCause(FlumeStatus.None, false),
                  "a dry end and a healthy piece explain nothing downstream");
        }

        private sealed class Piece
        {
            public Piece Upstream;
            public bool Cause;
        }

        private static void FlumeRunWalk()
        {
            // gate -> 30 flumes -> end
            var pieces = new List<Piece>();
            for (int i = 0; i < 32; i++) pieces.Add(new Piece { Upstream = i > 0 ? pieces[i - 1] : null });
            var end = pieces[31];
            Func<Piece, Piece> up = p => p.Upstream;
            Func<Piece, bool> cause = p => p.Cause;
            Check(!FlumeRules.AnyUpstream(end, up, cause), "a healthy run has no cause upstream");
            pieces[0].Cause = true;
            Check(FlumeRules.AnyUpstream(end, up, cause), "the cause at the head of the run is found from its end");
            pieces[0].Cause = false; end.Cause = true;
            Check(!FlumeRules.AnyUpstream(end, up, cause), "the piece itself is not its own upstream");
            end.Cause = false; pieces[17].Cause = true;
            Check(FlumeRules.AnyUpstream(end, up, cause) && !FlumeRules.AnyUpstream(pieces[10], up, cause),
                  "a cause in the middle is seen downstream of it only");

            // a ring of flumes (corners all the way round) ends the walk
            var ring = new List<Piece>();
            for (int i = 0; i < 8; i++) ring.Add(new Piece());
            for (int i = 0; i < 8; i++) ring[i].Upstream = ring[(i + 7) % 8];
            Check(!FlumeRules.AnyUpstream(ring[0], up, cause), "a ring without a cause ends the walk");
            ring[3].Cause = true;
            Check(FlumeRules.AnyUpstream(ring[0], up, cause), "a cause in a ring is found");

            // a chain longer than any real run stops at the bound instead of walking for ever
            var head = new Piece();
            var tail = head;
            for (int i = 0; i < FlumeRules.MaxRunSteps * 3; i++) tail = new Piece { Upstream = tail };
            head.Cause = true;
            Check(!FlumeRules.AnyUpstream(tail, up, cause), "the walk is bounded");
        }

        private static void FlumeDryCounter()
        {
            var end = Middle();
            end.HasTaker = false; end.NextIsChannel = false; end.LastCellWet = false;
            int n = 0;
            for (int i = 0; i < 3; i++) n = FlumeRules.NextDryChecks(n, end);
            Check(n == 3, "the dry counter counts checks");
            end.UpstreamShowsCause = true;
            n = FlumeRules.NextDryChecks(n, end);
            Check(n == 0, "the counter starts again while a cause upstream explains the drought");
            end.UpstreamShowsCause = false; end.LastCellWet = true;
            Check(FlumeRules.NextDryChecks(7, end) == 0, "water at the end resets the counter");
            Check(FlumeRules.NextDryChecks(7, Middle()) == 0, "a middle piece never counts");
            Check(FlumeRules.NextDryChecks(int.MaxValue - 1, new FlumeFacts()) == int.MaxValue - 1, "the counter cannot overflow");
        }

        private static void FlumeWaterPutBack()
        {
            Eq(FlumeRules.MissingWater(0.8f, 0.8f), 0f, "nothing missing, nothing added");
            Eq(FlumeRules.MissingWater(0.8f, 0.2f), 0.6f, "the missing part is put back");
            Eq(FlumeRules.MissingWater(1.9f, 0.1f), 1f, "at most one block (the obstacle cuts no more)");
            Eq(FlumeRules.MissingWater(0.3f, 0.9f), 0f, "a fuller cell is left alone");
            Eq(FlumeRules.MissingWater(0.305f, 0.3f), 0f, "a hair of difference is slosh, not loss");
            Eq(FlumeRules.MissingWater(float.NaN, 0.3f), 0f, "a broken number adds nothing");
        }

        private static void GateLatch()
        {
            const float shutoff = 0.05f;
            const int checks = 6;
            var latch = new BadwaterLatch();
            Check(!latch.Update(0.04f, shutoff, checks) && !latch.Closed, "below the threshold the gate stays open");
            Check(latch.Update(0.06f, shutoff, checks) && latch.Closed, "above the threshold it shuts at once");
            for (int i = 0; i < 5; i++) latch.Update(0.01f, shutoff, checks);
            Check(latch.Closed, "five clean checks are not enough");
            latch.Update(0.03f, shutoff, checks);   // between half and the threshold: not clean
            for (int i = 0; i < 5; i++) latch.Update(0.01f, shutoff, checks);
            Check(latch.Closed, "a reading in between starts the count again (stayed clean means in a row)");
            Check(latch.Update(0.01f, shutoff, checks) && !latch.Closed, "the sixth clean check in a row opens it");
            Check(!latch.Update(0.02f, shutoff, checks) && !latch.Closed, "open and clean: no change");

            latch.Closed = true;   // as read from a save ("bad=1")
            latch.Update(0.9f, shutoff, checks);
            Check(latch.Closed, "a gate loaded shut stays shut while the water is bad");
            for (int i = 0; i < 6; i++) latch.Update(0f, shutoff, checks);
            Check(!latch.Closed, "and opens after six clean checks");

            var off = new BadwaterLatch();
            Check(!off.Update(1f, 0f, checks) && !off.Closed, "a threshold of zero switches the guard off");
            Check(!off.Update(float.NaN, shutoff, checks) && !off.Closed, "a broken reading changes nothing");
        }

        private static void GateFlowSetting()
        {
            Eq(GateFlow.Snap(0.32f, 0.05f, 1f), 0.3f, "the flow snaps to the step");
            Eq(GateFlow.Snap(0.33f, 0.05f, 1f), 0.35f, "the flow snaps to the nearest step");
            Eq(GateFlow.Snap(7f, 0.05f, 1f), 1f, "never above the gate's maximum");
            Eq(GateFlow.Snap(-1f, 0.05f, 1f), 0f, "never below zero");
            Eq(GateFlow.Snap(float.NaN, 0.05f, 1f), 0f, "a broken saved value closes the gate");
            Eq(GateFlow.Snap(0.45f, 0f, 1f), 0.45f, "a saved value is kept as it is (no step)");
            Eq(GateFlow.Snap(0.6f, 0.05f, 0f), 0.6f, "data without a maximum falls back to 1");
        }

        // ------------------------------------------------------------------ Ringtails

        private static void ShiftWindow()
        {
            const float nightfall = 16f;
            Eq(ShiftMath.ShiftStart(12f, 4f, 16f, nightfall), 12f, "the shift starts at the bell");
            Eq(ShiftMath.ShiftStart(2f, 4f, 16f, nightfall), 4f, "never earlier than four hours after dawn");
            Eq(ShiftMath.ShiftStart(20f, 4f, 16f, nightfall), 16f, "never later than nightfall");
            Eq(ShiftMath.ShiftStart(24f, 4f, 16f, nightfall), 16f, "Inkpaws worked around the clock: Ringtails still hold the night");
            Eq(ShiftMath.ShiftStart(18f, 4f, 20f, 14f), 14f, "nightfall as the game has it wins over the data's limit");
            Eq(ShiftMath.ShiftStart(18f, 4f, 16f, 0f), 16f, "an unknown nightfall leaves the data's limit");
            Eq(ShiftMath.ShiftStart(10f, 9f, 6f, nightfall), 6f, "limits the wrong way round do not make an empty window");
            Eq(ShiftMath.ShiftStart(float.NaN, 4f, 16f, nightfall), 16f, "a broken clock means the default day");
            Eq(ShiftMath.ShiftStart(10f, -3f, 99f, nightfall), 10f, "limits out of range fall back to the defaults");

            // M2: the night shift the rested bonus is read at
            Eq(ShiftMath.NightShiftHours(12f), 12f, "twelve and twelve");
            Eq(ShiftMath.NightShiftHours(16f), 8f, "a sixteen-hour day leaves an eight-hour night");
            Eq(ShiftMath.NightShiftHours(4f), 20f, "a four-hour day leaves a twenty-hour night");
            Eq(ShiftMath.NightShiftHours(30f), 0f, "never negative");

            Eq(ShiftMath.HoursSinceDawn(3f, 0f), 3f, "hours since dawn");
            Eq(ShiftMath.HoursSinceDawn(2f, 6f), 20f, "before dawn wraps to the end of the night");
            Eq(ShiftMath.HoursSinceDawn(float.NaN, 0f), 0f, "a broken clock reads dawn");

            // the rest window: dawn to the shift start
            Check(ShiftMath.InWindow(0f, 0f, 12f) && ShiftMath.InWindow(11.9f, 0f, 12f), "resting from dawn to the bell");
            Check(!ShiftMath.InWindow(12f, 0f, 12f) && !ShiftMath.InWindow(23f, 0f, 12f), "working from the bell to dawn");
            Check(ShiftMath.InWindow(23f, 22f, 4f) && ShiftMath.InWindow(1f, 22f, 4f) && !ShiftMath.InWindow(12f, 22f, 4f), "a window over dawn wraps");
            Check(!ShiftMath.InWindow(5f, 5f, 5f), "an empty window holds nothing");
        }

        private static void ShiftClapper()
        {
            Check(ShiftMath.CrossedShiftStart(11.9f, 12.1f, 12f), "the clapper sounds as the clock passes the shift start");
            Check(!ShiftMath.CrossedShiftStart(12.1f, 12.2f, 12f), "once");
            Check(!ShiftMath.CrossedShiftStart(-1f, 12.1f, 12f), "not on the first frame after a load");
            Check(!ShiftMath.CrossedShiftStart(3f, 13f, 12f), "not on a jump of hours");
            Check(!ShiftMath.CrossedShiftStart(23.9f, 0.1f, 12f), "not at dawn");
        }

        private static void KitValveRules()
        {
            Check(KitValve.OpenJobs(5, 2, 1) == 2, "open jobs = worker slots minus adults minus kits growing");
            Check(KitValve.OpenJobs(2, 4, 0) == -2, "idle Ringtails make it negative");

            Check(KitValve.Decide(2, 1, false, 2, true) == KitState.Raising, "jobs open, nobody starving, room: a kit");
            Check(KitValve.Decide(2, 1, false, 0, true) == KitState.WaitingForJobs, "no open job: no kit");
            Check(KitValve.Decide(2, 1, false, -3, true) == KitState.WaitingForJobs, "idle Ringtails: no kit");
            Check(KitValve.Decide(2, 1, true, 5, true) == KitState.Hungry, "nobody is born into a famine");
            Check(KitValve.Decide(2, 1, false, 2, false) == KitState.NoRoom, "no room: no kit");
            Check(KitValve.Decide(0, 2, false, 5, true) == KitState.NoParents, "kits without an adult wait to grow up");
            Check(KitValve.Decide(0, 0, false, 5, true) == KitState.Inviting, "no Ringtail at all: the lantern invites");

            Check(KitValve.KitsToRaise(KitState.Raising, 1, 3) == 1, "one kit a loft a day");
            Check(KitValve.KitsToRaise(KitState.Raising, 3, 2) == 2, "never more kits than open jobs");
            Check(KitValve.KitsToRaise(KitState.Raising, 0, 2) == 1, "data with zero kits a day still means one");
            Check(KitValve.KitsToRaise(KitState.WaitingForJobs, 1, 3) == 0 && KitValve.KitsToRaise(KitState.Hungry, 1, 3) == 0, "no kit in any other state");

            // ten lofts raise no more than the jobs: the open count goes down with each kit
            int open = KitValve.OpenJobs(5, 2, 1), kits = 1, raised = 0;
            for (int loft = 0; loft < 10; loft++)
            {
                int n = KitValve.KitsToRaise(KitValve.Decide(2, kits, false, open, true), 1, open);
                raised += n; kits += n; open -= n;
            }
            Check(raised == 2 && open == 0, "ten lofts, two open jobs: two kits");

            foreach (KitState state in Enum.GetValues(typeof(KitState)))
                Check(state == KitState.None ? KitValve.LocKey(state) == "" : KitValve.LocKey(state).StartsWith("Pandaborn.Ringtails.Loft."),
                      "every nursery state has its text: " + state);
        }

        private static void ReturnOfTheRingtails()
        {
            const int wait = 3;
            bool invite;
            int n = 0;
            n = KitValve.NextEmptyDawns(n, true, 0, false, wait, out invite);
            Check(n == 1 && !invite, "first empty dawn: wait");
            n = KitValve.NextEmptyDawns(n, true, 0, false, wait, out invite);
            Check(n == 2 && !invite, "second empty dawn: wait");
            n = KitValve.NextEmptyDawns(n, true, 0, false, wait, out invite);
            Check(n == 0 && invite, "third empty dawn: a family is invited and the count starts again");

            n = KitValve.NextEmptyDawns(2, true, 1, false, wait, out invite);
            Check(n == 0 && !invite, "one living Ringtail ends the wait");
            n = KitValve.NextEmptyDawns(2, false, 0, false, wait, out invite);
            Check(n == 0 && !invite, "no finished loft: nobody is invited");

            n = KitValve.NextEmptyDawns(2, true, 0, true, wait, out invite);
            Check(n == 3 && !invite, "nobody is invited into a famine; the wait is kept");
            n = KitValve.NextEmptyDawns(n, true, 0, false, wait, out invite);
            Check(invite, "they come at the first dawn after it");

            n = KitValve.NextEmptyDawns(0, true, 0, false, 0, out invite);
            Check(invite, "a wait of zero days in the data means the next dawn");
            n = KitValve.NextEmptyDawns(-5, true, 0, false, wait, out invite);
            Check(n == 1 && !invite, "a broken saved count starts at one");
        }
    }
}
