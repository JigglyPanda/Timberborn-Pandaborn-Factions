using System;
using System.Linq;

namespace Pandaborn.Festival
{
    /// <summary>
    /// Test-only switch for the reflection fallbacks (ENGINEERING.md, code rule 4): a line
    /// "simulate-missing-member: Festival.RootBehaviors, Festival.Fireworks" in the dev switch (pandaborn.dev.txt in the
    /// mod folder, or the PANDABORN_DEV environment variable, lines separated by ';') makes the module behave as if that
    /// private member had gone in a game update. The bootstrap publishes the dev lines in AppDomain data.
    /// </summary>
    internal static class DevFlags
    {
        /// <summary>"force-off: &lt;Id&gt;" in the dev switch. The bootstrap then never loads the module; a test build that
        /// loads the module another way asks this so the module still stays off.</summary>
        public static bool ForcedOff(string id) => Has("force-off:", id);

        public static bool SimulatesMissing(string member) => Has("simulate-missing-member:", member);

        private static bool Has(string key, string member)
        {
            try
            {
                string lines = (AppDomain.CurrentDomain.GetData("Pandaborn.Boot.Dev") as string ?? "") + "\n"
                               + (Environment.GetEnvironmentVariable("PANDABORN_DEV") ?? "").Replace(';', '\n');
                foreach (var raw in lines.Split('\n'))
                {
                    var line = raw.Trim();
                    if (!line.StartsWith(key, StringComparison.OrdinalIgnoreCase)) continue;
                    if (line.Substring(key.Length).Split(',').Any(p => string.Equals(p.Trim(), member, StringComparison.OrdinalIgnoreCase) || p.Trim() == "*"))
                        return true;
                }
            }
            catch (Exception) { }
            return false;
        }
    }
}
