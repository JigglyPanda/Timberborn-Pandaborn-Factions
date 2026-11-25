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
    /// agree and moving the slider changes tomorrow); otherwise the live working-hours slider. The shift start is that bell
    /// clamped to the Ringtail adult's rest limits (PandabornRingtailSpec.RestMinEndHours / RestMaxEndHours, 4 h and 16 h)
    /// and to nightfall as the game has it (<see cref="ShiftMath.ShiftStart"/>): one number for the rest window, the
    /// "closed for the day" status, the clock arc and the clapper.
    ///
    /// It is also the Core <see cref="INightShiftClock"/>: the length of the night shift, which the Bell module reads to
    /// give Ringtails the rested bonus by their own shift. This module does not know the Bell exists.
    /// </summary>
    public class RingtailWorkday : INightShiftClock
    {
        private readonly IDayNightCycle _dayNightCycle;
        private readonly WorkingHoursManager _workingHoursManager;
        private readonly RingtailService _ringtailService;
        private readonly List<IWorkdayClock> _clocks;

        public RingtailWorkday(IDayNightCycle dayNightCycle, WorkingHoursManager workingHoursManager, IEnumerable<IWorkdayClock> clocks,
                               RingtailService ringtailService)
        {
            _dayNightCycle = dayNightCycle;
            _workingHoursManager = workingHoursManager;
            _ringtailService = ringtailService;
            _clocks = clocks.ToList();
        }

        public float Dawn => _dayNightCycle.BoundsInHours(TimeOfDay.Daytime).start;

        /// <summary>Nightfall in hours after dawn (16 in the vanilla day; another mod may change it).</summary>
        public float Nightfall => _dayNightCycle.DaytimeLengthInHours;

        public float HoursSinceDawn => ShiftMath.HoursSinceDawn(_dayNightCycle.HoursPassedToday, Dawn);

        private IWorkdayClock Locked
        {
            get
            {
                for (int i = 0; i < _clocks.Count; i++)
                {
                    try { if (_clocks[i].HasLockedDay) return _clocks[i]; }
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
        public float ShiftStartHours
        {
            get
            {
                var spec = _ringtailService.AdultSpec;
                return ShiftMath.ShiftStart(WorkdayHours, spec != null ? spec.RestMinEndHours : ShiftMath.DefaultMinStart,
                                            spec != null ? spec.RestMaxEndHours : ShiftMath.DefaultMaxStart, Nightfall);
            }
        }

        public string Source => Locked != null ? "locked" : "slider";

        // INightShiftClock (Core)
        public bool HasNightShift => _ringtailService.Enabled;

        public float NightShiftHours => ShiftMath.NightShiftHours(ShiftStartHours);
    }
}
