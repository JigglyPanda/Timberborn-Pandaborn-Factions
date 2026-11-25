using System;
using System.Collections.Generic;

namespace Pandaborn.Festival
{
    /// <summary>
    /// The festival's arithmetic, free of game types so it is tested without the game (src/code/tests/Events): the
    /// once-a-cycle rule, which dishes a festival takes, and which of the show's evenly spaced launches fall due between
    /// two readings of the clock.
    /// </summary>
    public static class FestivalRules
    {
        /// <summary>The first cycle in which a festival may be called again (-1: none held yet).</summary>
        public static int NextAllowedCycle(int lastCycle) => lastCycle < 0 ? 0 : lastCycle + 1;

        /// <summary>The day a festival called on <paramref name="today"/> is held: always the next dawn.</summary>
        public static int FestivalDayFor(int today) => today + 1;

        /// <summary>
        /// The dishes a festival takes: the <paramref name="kinds"/> most plentiful of those with at least
        /// <paramref name="amount"/> in store (ties keep the order given). Fewer than <paramref name="kinds"/> qualify:
        /// the list is shorter and the festival is not ready.
        /// </summary>
        public static List<string> PickDishes(IEnumerable<KeyValuePair<string, int>> stock, int kinds, int amount)
        {
            var qualifying = new List<KeyValuePair<string, int>>();
            foreach (var dish in stock)
                if (dish.Value >= amount && !qualifying.Exists(q => q.Key == dish.Key)) qualifying.Add(dish);
            // a stable sort: List.Sort is not, and the choice must not depend on the runtime
            for (int i = 1; i < qualifying.Count; i++)
            {
                var item = qualifying[i];
                int j = i - 1;
                while (j >= 0 && qualifying[j].Value < item.Value) { qualifying[j + 1] = qualifying[j]; j--; }
                qualifying[j + 1] = item;
            }
            var picked = new List<string>();
            for (int i = 0; i < qualifying.Count && i < kinds; i++) picked.Add(qualifying[i].Key);
            return picked;
        }

        /// <summary>
        /// Of <paramref name="count"/> launches spread evenly over <paramref name="span"/> hours from
        /// <paramref name="start"/> (launch i at start + i * span / count), the indices that fall in (from, now]. Reading
        /// the clock twice never yields a launch twice, and a reload (from = the hour of the load) yields only what is
        /// still due.
        /// </summary>
        public static void Due(float start, float span, int count, float from, float now, List<int> due)
        {
            due.Clear();
            if (count <= 0 || now <= from) return;
            for (int i = 0; i < count; i++)
            {
                float t = start + i * span / count;
                if (t > from && t <= now) due.Add(i);
            }
        }

        /// <summary>
        /// Lanterns the sky holds once it has filled: the release rate times the mean life (both in the particles' own
        /// seconds, so the number is the same at every game speed).
        /// </summary>
        public static float SteadySkyLanterns(float perSecond, float minLife, float maxLife) =>
            Math.Max(0f, perSecond) * (minLife + maxLife) * 0.5f;
    }
}
