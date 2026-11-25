using System;

namespace Pandaborn.Bell
{
    /// <summary>The bell's arithmetic, free of game types so tests/Foundation can run it without the game.</summary>
    internal static class BellCurve
    {
        /// <summary>
        /// The bonus at a day length: piecewise linear through the points (hours[i], bonuses[i]), flat beyond the first
        /// and the last, 0 for no points. The points may come in any order; a point exactly at the asked hour gives its own
        /// bonus (so a curve with a point for every whole hour is a plain table). Two points at the same hour: the later
        /// one in the data holds from that hour on.
        /// </summary>
        public static float At(float[] hours, float[] bonuses, float at)
        {
            int n = hours == null || bonuses == null ? 0 : Math.Min(hours.Length, bonuses.Length);
            if (n == 0 || float.IsNaN(at)) return 0f;
            var order = new int[n];
            for (int i = 0; i < n; i++) order[i] = i;
            // insertion sort by hours, stable: curves have a handful of points
            for (int i = 1; i < n; i++)
            {
                int k = order[i], j = i - 1;
                while (j >= 0 && hours[order[j]] > hours[k]) { order[j + 1] = order[j]; j--; }
                order[j + 1] = k;
            }
            if (at <= hours[order[0]]) return Clean(bonuses[order[0]]);
            for (int i = 1; i < n; i++)
            {
                float h1 = hours[order[i]];
                if (at > h1) continue;
                float h0 = hours[order[i - 1]], b0 = bonuses[order[i - 1]], b1 = bonuses[order[i]];
                float t = h1 > h0 ? (at - h0) / (h1 - h0) : 1f;
                return Clean(b0 + (b1 - b0) * t);
            }
            return Clean(bonuses[order[n - 1]]);
        }

        /// <summary>The longest day, in whole hours from 0 to 24, that still gives the curve's largest bonus (shortening the
        /// day further gains nothing); -1 when the curve gives no bonus at any length.</summary>
        public static int CeilingHours(float[] hours, float[] bonuses)
        {
            float best = 0f;
            for (int h = 0; h <= 24; h++) best = Math.Max(best, At(hours, bonuses, h));
            if (best <= 0f) return -1;
            for (int h = 24; h >= 0; h--)
                if (At(hours, bonuses, h) >= best - 1e-4f) return h;
            return -1;
        }

        private static float Clean(float bonus) => float.IsNaN(bonus) || float.IsInfinity(bonus) ? 0f : bonus;
    }

    /// <summary>One bonus sum of one colonist, as the game's BonusManager keeps it: additive, clamped when read.</summary>
    internal interface IBonusSum
    {
        /// <summary>The multiplier as the game uses it (the sum, clamped to the bonus type's limits).</summary>
        float Multiplier();

        void Add(float delta);

        void Remove(float delta);
    }

    /// <summary>
    /// The additive share that makes a bonus multiply. With every other bonus summed into m, the share is m x factor, so
    /// the colonist ends at m x (1 + factor). Apply is called whenever m or the factor may have changed: it takes the old
    /// share out, reads m, and puts the new share in.
    ///
    /// The book-keeping survives a thrower: BonusManager changes its sum first and then tells its listeners, any of
    /// which (another mod's) may throw through Add or Remove. So Delta is written before each call: after an exception
    /// it still says what the sum holds, and the next Apply neither takes the share out twice nor leaves it in twice.
    /// </summary>
    internal sealed class RestedShare
    {
        /// <summary>The share currently in the sum.</summary>
        public float Delta { get; private set; }

        /// <summary>The multiplier without the share, as last read.</summary>
        public float Base { get; private set; } = 1f;

        private bool _applying;

        public void Apply(IBonusSum sum, float factor)
        {
            // Add and Remove tell the sum's listeners, the caller of this among them: a second Apply inside the first
            // would read a multiplier that is half way and leave its share in the sum for good
            if (_applying) return;
            _applying = true;
            try
            {
                float old = Delta;
                if (old != 0f)
                {
                    Delta = 0f;
                    sum.Remove(old);
                }
                float baseMultiplier = sum.Multiplier();
                float delta = baseMultiplier * factor;
                if (float.IsNaN(delta) || float.IsInfinity(delta) || Math.Abs(delta) < 1e-5f) delta = 0f;
                Base = baseMultiplier;
                if (delta != 0f)
                {
                    Delta = delta;
                    sum.Add(delta);
                }
            }
            finally
            {
                _applying = false;
            }
        }
    }
}
