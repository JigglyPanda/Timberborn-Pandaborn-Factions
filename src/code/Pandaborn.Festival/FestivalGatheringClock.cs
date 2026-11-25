using System;
using Pandaborn.Core;
using Timberborn.BaseComponentSystem;

namespace Pandaborn.Festival
{
    /// <summary>
    /// Tells routines that sit above the festival in a colonist's behaviour list (the Ringtails' day rest, through Core's
    /// IGatheringClock) to step aside while the colonist should be at the square: during the hours of the show, for a
    /// colonist whose district holds the festival, who has the festival behaviour (so there is something to hand it to)
    /// and is not on a keep-working crew in its hours. Outside the show it never claims anyone: a Ringtail still sleeps
    /// through its festival morning. A Ringtail whose rest runs past the start of the show (a long working day) no longer
    /// misses the release of the lanterns. Cheap (a few field reads) and never throws.
    /// </summary>
    public class FestivalGatheringClock : IGatheringClock
    {
        private readonly FestivalService _festivalService;

        public FestivalGatheringClock(FestivalService festivalService)
        {
            _festivalService = festivalService;
        }

        public bool GathersNow(BaseComponent colonist)
        {
            try
            {
                if (!_festivalService.IsShowTime || !colonist) return false;
                var goer = colonist.GetComponent<FestivalGoer>();
                return goer != null && goer.Inserted && _festivalService.IsHolidayFor(goer.District) && !goer.KeepsWorking;
            }
            catch (Exception)
            {
                return false;
            }
        }
    }
}
