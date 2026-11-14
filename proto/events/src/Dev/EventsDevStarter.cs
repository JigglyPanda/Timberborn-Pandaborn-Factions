using System;
using System.IO;
using Timberborn.ModManagerScene;
using UnityEngine;

namespace Pandaborn.Events.Dev
{
    /// <summary>
    /// Dev only. Lets one test launch set the dev switch of the next: the probe's "writeDevSwitch" action writes
    /// events.dev.txt into this mod's folder; at the next start this starter appends its lines to the bootstrap's published
    /// dev lines (AppDomain "Pandaborn.Boot.Dev", read by the modules' DevFlags) and deletes the file (one launch only).
    /// Used to load a save made mid-event with the modules forced off ("force-off: Festival, Flowering"), as a player
    /// whose game update switched them off would. Runs after the faction mod's starter (this mod requires it).
    /// </summary>
    public class EventsDevStarter : IModStarter
    {
        public const string FileName = "events.dev.txt";

        public static string ModPath { get; private set; }

        public void StartMod(IModEnvironment modEnvironment)
        {
            try
            {
                ModPath = modEnvironment.ModPath;
                AppDomain.CurrentDomain.SetData("Pandaborn.Events.ModPath", ModPath);
                string file = Path.Combine(ModPath, FileName);
                if (!File.Exists(file)) return;
                string lines = File.ReadAllText(file).Replace("\r", "");
                string previous = AppDomain.CurrentDomain.GetData("Pandaborn.Boot.Dev") as string ?? "";
                AppDomain.CurrentDomain.SetData("Pandaborn.Boot.Dev", previous + "\n" + lines);
                File.Delete(file);
                Debug.LogWarning("[Pandaborn.Events.Dev] dev switch for this launch: " + lines.Replace("\n", "; "));
            }
            catch (Exception e) { Debug.LogError("[Pandaborn.Events.Dev] dev starter failed: " + e.Message); }
        }
    }
}
