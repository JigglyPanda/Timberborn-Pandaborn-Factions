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

    /// <summary>
    /// A gathering that goes before a colonist's own routine (the Lantern Festival's evening at the square). A module
    /// that keeps colonists to a routine of its own above the worker behaviour (the Ringtails' day rest) takes
    /// IEnumerable&lt;IGatheringClock&gt; in its per-colonist component and steps aside while any clock says the colonist
    /// gathers now; the module that runs the gathering registers the clock and takes the colonist from there with its own
    /// behaviour. With no such module only the inactive NoGatheringClock is there.
    /// </summary>
    public interface IGatheringClock
    {
        /// <summary>True while this colonist should be at the gathering now (its district's festival, in the hours of the
        /// show). Called from the colonist's behaviour: must be cheap and must not throw.</summary>
        bool GathersNow(Timberborn.BaseComponentSystem.BaseComponent colonist);
    }

    /// <summary>Always registered by Core: no gathering.</summary>
    public sealed class NoGatheringClock : IGatheringClock
    {
        public bool GathersNow(Timberborn.BaseComponentSystem.BaseComponent colonist) => false;
    }


}
