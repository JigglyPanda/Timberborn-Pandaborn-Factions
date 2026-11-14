using System;
using System.Collections.Generic;
using System.Linq;
using Pandaborn.Core;
using Timberborn.TimeSystem;
using Timberborn.WorkSystem;

namespace Pandaborn.Ringtails
{
    /// <summary>
    /// When the Ringtails' shift starts: the bell, i.e. the end of the Inkpaw working day, in hours after dawn. Uses the first
    /// Core IWorkdayClock with a locked day (Pandaborn.Bell registers one: the day length it locked at dawn, so both peoples
    /// agree and moving the slider changes tomorrow); otherwise the live working-hours slider. The shift start itself is
    /// clamped to [4 h, nightfall] by the callers (PandabornRingtailSpec.RestMinEndHours / RestMaxEndHours).
    /// </summary>
    public class RingtailWorkday
    {
        private readonly IDayNightCycle _dayNightCycle;
        private readonly WorkingHoursManager _workingHoursManager;
        private readonly List<IWorkdayClock> _clocks;

        public RingtailWorkday(IDayNightCycle dayNightCycle, WorkingHoursManager workingHoursManager, IEnumerable<IWorkdayClock> clocks)
        {
            _dayNightCycle = dayNightCycle;
            _workingHoursManager = workingHoursManager;
            _clocks = clocks.ToList();
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

        private IWorkdayClock Locked
        {
            get
            {
                foreach (var clock in _clocks)
                {
                    try { if (clock.HasLockedDay) return clock; }
                    catch (Exception) { }
                }
                return null;
            }
        }

        /// <summary>Length of the Inkpaw working day in hours (the bell, measured from dawn).</summary>
        public float WorkdayHours
        {
            get
            {
                var clock = Locked;
                return clock != null ? clock.LockedWorkdayHours : _workingHoursManager.EndHours - Dawn;
            }
        }

        /// <summary>The Ringtails' shift start in hours after dawn (the bell clamped to 4 h .. nightfall).</summary>
        public float ShiftStartHours => Math.Min(Math.Max(WorkdayHours, 4f), _dayNightCycle.DaytimeLengthInHours);

        public string Source => Locked != null ? "locked" : "slider";
    }
}
