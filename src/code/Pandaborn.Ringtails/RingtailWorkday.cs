using System;
using System.Linq;
using System.Reflection;
using Pandaborn.Core;
using Timberborn.TimeSystem;
using Timberborn.WorkSystem;

namespace Pandaborn.Ringtails
{
    /// <summary>
    /// When the Ringtails' shift starts: the bell, i.e. the end of the Inkpaw working day, in hours after dawn.
    /// With Pandaborn.Bell on, the day length Bell locked at dawn (so both modules agree, and moving the slider changes
    /// tomorrow, as for the Inkpaws); otherwise the live working-hours slider.
    ///
    /// Bell is reached without a compile-time reference: by name, through its public static BellService.Current.LockedHours.
    /// Proposed replacement (src/code/README.md terms): a Core interface
    ///   namespace Pandaborn.Core { public interface IWorkdayClock { bool HasLockedDay { get; } int LockedWorkdayHours { get; } } }
    /// bound by Bell with MultiBind&lt;IWorkdayClock&gt;(); Ringtails would take IEnumerable&lt;IWorkdayClock&gt; and fall back to the
    /// slider when it is empty. Until Core has it, this bridge reads Bell by name and falls back silently.
    /// </summary>
    public class RingtailWorkday
    {
        private readonly IDayNightCycle _dayNightCycle;
        private readonly WorkingHoursManager _workingHoursManager;
        private PropertyInfo _bellCurrent;
        private PropertyInfo _bellLocked;
        private bool _resolved;

        public RingtailWorkday(IDayNightCycle dayNightCycle, WorkingHoursManager workingHoursManager)
        {
            _dayNightCycle = dayNightCycle;
            _workingHoursManager = workingHoursManager;
        }

        public float Dawn => _dayNightCycle.BoundsInHours(TimeOfDay.Daytime).start;

        public float HoursSinceDawn
        {
            get
            {
                float h = _dayNightCycle.HoursPassedToday - Dawn;
                return h < 0f ? h + 24f : h;
            }
        }

        /// <summary>Length of the Inkpaw working day in hours (the bell, measured from dawn).</summary>
        public float WorkdayHours
        {
            get
            {
                int locked = BellLockedHours();
                if (locked >= 0) return locked;
                return _workingHoursManager.EndHours - Dawn;
            }
        }

        public string Source => BellLockedHours() >= 0 ? "bell" : "slider";

        private int BellLockedHours()
        {
            try
            {
                if (!FeatureRegistry.IsOn("Bell")) return -1;
                if (!_resolved)
                {
                    _resolved = true;
                    var type = AppDomain.CurrentDomain.GetAssemblies().FirstOrDefault(a => a.GetName().Name == "Pandaborn.Bell")
                        ?.GetType("Pandaborn.Bell.BellService");
                    _bellCurrent = type?.GetProperty("Current", BindingFlags.Public | BindingFlags.Static);
                    _bellLocked = type?.GetProperty("LockedHours", BindingFlags.Public | BindingFlags.Instance);
                }
                var bell = _bellCurrent?.GetValue(null);
                var active = bell?.GetType().GetProperty("Active")?.GetValue(bell) as bool?;
                if (bell == null || active != true || _bellLocked == null) return -1;
                return (int)_bellLocked.GetValue(bell);
            }
            catch (Exception)
            {
                return -1;
            }
        }
    }
}
