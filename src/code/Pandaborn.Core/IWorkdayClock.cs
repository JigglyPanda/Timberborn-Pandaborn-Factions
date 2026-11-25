namespace Pandaborn.Core
{
    /// <summary>
    /// The working day as locked at dawn (Pandaborn.Bell registers one). Modules that follow the Inkpaws' day (the
    /// Ringtails' shift) take IEnumerable&lt;IWorkdayClock&gt; and use the first with HasLockedDay; when the Bell module is off
    /// only the inactive NoWorkdayClock is there and they fall back to the vanilla working hours.
    /// </summary>
    /// <remarks>Core always registers NoWorkdayClock, so the sequence is never empty and injecting it never fails; pick the
    /// first clock with HasLockedDay.</remarks>
    public interface IWorkdayClock
    {
        /// <summary>True in a game where the clock is active and has locked a day length.</summary>
        bool HasLockedDay { get; }

        /// <summary>The working-day length (hours) in force today; meaningful only when HasLockedDay.</summary>
        int LockedWorkdayHours { get; }
    }

    /// <summary>Always registered by Core: no locked day.</summary>
    public sealed class NoWorkdayClock : IWorkdayClock
    {
        public bool HasLockedDay => false;

        public int LockedWorkdayHours => -1;
    }

    /// <summary>
    /// The night shift of a second people (Pandaborn.Ringtails registers one). Modules that reward a rested shift (the
    /// Bell's bonus for Ringtails) take IEnumerable&lt;INightShiftClock&gt; and use the first with HasNightShift; when no
    /// module provides one only the inactive NoNightShiftClock is there and nobody has a night shift.
    /// The provider must not take the consumer's singletons in its constructor chain and the consumer must not take
    /// this in a singleton's constructor if the provider reads IWorkdayClock (the Ringtails do, the Bell provides it):
    /// the two would need each other. Inject it into per-entity components, which are created after every singleton.
    /// </summary>
    public interface INightShiftClock
    {
        /// <summary>True in a game where the night people exists and its shift is defined.</summary>
        bool HasNightShift { get; }

        /// <summary>Length of the night shift in hours (from its start to dawn); meaningful only when HasNightShift.</summary>
        float NightShiftHours { get; }
    }

    /// <summary>Always registered by Core: no night shift.</summary>
    public sealed class NoNightShiftClock : INightShiftClock
    {
        public bool HasNightShift => false;

        public float NightShiftHours => 0f;
    }

}
