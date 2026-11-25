using System;
using Pandaborn.Core;
using UnityEngine;

namespace Pandaborn.Water
{
    /// <summary>
    /// Failure containment for the water module's game callbacks. The game treats an exception in a finished-state
    /// listener as a failed load ("Exception while initializing") and an exception in a tick as a crash, so every
    /// callback of this module catches, reports here and leaves its piece in the state it had: a flume that could not be
    /// opened stays the solid block its data makes it. The first failure marks the feature as reduced in the feature
    /// report; the log gets the first few stack traces only.
    /// </summary>
    internal static class WaterGuard
    {
        private const int MaxLogged = 8;
        private static int _logged;
        private static bool _reported;

        /// <summary>Failures caught this session (for tests).</summary>
        public static int Failures { get; private set; }

        public static void Report(string where, Exception e)
        {
            Failures++;
            if (_logged < MaxLogged)
            {
                _logged++;
                Debug.LogError("[Pandaborn.Water] " + where + " failed; the piece keeps its last state: " + e);
            }
            if (_reported) return;
            _reported = true;
            try { FeatureRegistry.ReportDegraded("Water", where + " failed (" + e.GetType().Name + ")"); }
            catch (Exception) { }
        }
    }
}
