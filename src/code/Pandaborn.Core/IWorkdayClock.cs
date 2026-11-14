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
}
