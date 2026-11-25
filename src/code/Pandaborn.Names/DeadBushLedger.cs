using System;
using System.Collections.Generic;

namespace Pandaborn.Customs
{
    /// <summary>
    /// Remembers since when each dead bush has been waiting to be cleared, and says when one is due. A bush is due once
    /// it has been seen waiting, at every look, for the whole delay: one that stops qualifying in between (the forester's
    /// option was switched off, the planting mark was removed, the bush came back to life) is forgotten and starts again
    /// from nothing if it qualifies later. Nothing here is saved: after a load the wait starts over, which costs a bush
    /// at most one more delay. No game types: tests/Foundation reads this file directly.
    /// </summary>
    internal sealed class DeadBushLedger
    {
        private readonly Dictionary<Guid, float> _waitingSince = new Dictionary<Guid, float>();
        private readonly HashSet<Guid> _seenThisLook = new HashSet<Guid>();
        private readonly List<Guid> _forget = new List<Guid>();

        public int Waiting => _waitingSince.Count;

        /// <summary>Starts a look over the map (time in days).</summary>
        public void Begin() => _seenThisLook.Clear();

        /// <summary>A bush qualifies at this look. True when it has waited the whole delay.</summary>
        public bool Observe(Guid bush, float now, float delayDays)
        {
            _seenThisLook.Add(bush);
            if (!_waitingSince.TryGetValue(bush, out float since) || now < since)     // now < since: the clock went back
            {
                _waitingSince[bush] = now;
                return delayDays <= 0f;
            }
            return now - since >= delayDays;
        }

        /// <summary>Ends the look: bushes that did not qualify this time are forgotten.</summary>
        public void End()
        {
            _forget.Clear();
            foreach (var bush in _waitingSince.Keys)
                if (!_seenThisLook.Contains(bush)) _forget.Add(bush);
            foreach (var bush in _forget) _waitingSince.Remove(bush);
        }

        public void Forget(Guid bush) => _waitingSince.Remove(bush);

        public void Clear()
        {
            _waitingSince.Clear();
            _seenThisLook.Clear();
        }
    }
}
