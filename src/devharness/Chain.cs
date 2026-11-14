using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using Bindito.Core;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Timberborn.MainMenuSceneLoading;
using Timberborn.SingletonSystem;
using UnityEngine;

namespace PandabornDevHarness
{
    /// <summary>
    /// A second new game in the same launch. Request field "then": { "faction": "Folktails", ... } (any request keys; they
    /// override the first game's request, "name" names the subfolder, default "then"). When the first game completes, its
    /// result is kept (also written as result.first.json), the harness exits to the main menu without saving, and the main
    /// menu driver starts the second game, which writes everything (request, harness.log, result.json, screenshots) into
    /// &lt;run&gt;\&lt;name&gt;\. When that game finishes, the first game's result.json is written with a "then" summary and a check
    /// "then" that fails if the second game's verdict is not pass. One level only: a "then" inside "then" is ignored.
    /// result.json in the run folder only appears at the very end, so tools/run_game_test.ps1 waits for both games
    /// (give it -TimeoutSeconds for two runs).
    /// </summary>
    public static partial class Harness
    {
        private static JObject _parentResult;
        private static string _parentDir;
        internal static bool MainMenuRequested;

        /// <summary>True when a chained game was set up (the caller must neither write the final result nor quit).</summary>
        private static bool TryChain(string status)
        {
            if (status != "completed" || _parentResult != null || Request == null || !(Request.Raw["then"] is JObject then)) return false;
            Request next;
            JObject parent;
            try
            {
                var raw = (JObject)Request.Raw.DeepClone();
                foreach (var key in new[] { "then", "save", "loadSave", "factionPanelShots" }) raw.Remove(key);
                foreach (var p in then.Properties()) if (p.Name != "then") raw[p.Name] = p.Value.DeepClone();
                string name = Request.Str(then, "name", "then");
                string dir = Path.Combine(OutputDir, name);
                raw["runId"] = Request.RunId + "-" + name;
                raw["outputDir"] = dir;
                raw["settlementName"] = Request.SettlementName;
                raw["expiresUtc"] = DateTime.UtcNow.AddHours(1).ToString("o", CultureInfo.InvariantCulture);
                Directory.CreateDirectory(dir);
                string path = Path.Combine(dir, "request.json");
                File.WriteAllText(path, raw.ToString(Formatting.Indented));
                next = Request.Parse(path);
                WriteResult(status, "result.first.json");
                lock (LogLock) parent = (JObject)Result.DeepClone();
            }
            catch (Exception e)
            {
                Error("setting up the chained game failed; finishing after the first game", e);
                return false;
            }

            _parentResult = parent;
            _parentDir = OutputDir;
            lock (LogLock)
            {
                Result.RemoveAll();
                Warnings.RemoveAll();
                Screenshots.RemoveAll();
                LogEntries.Clear();
                _errors = _exceptions = _warnings = _ownErrors = _ownExceptions = 0;
                _crash = null;
            }
            Info("first game done (verdict " + parent["verdict"] + "); next: " + next.Faction + " in " + next.OutputDir);
            Request = next;
            OutputDir = next.OutputDir;
            _startedUtc = DateTime.UtcNow;
            GameRequested = false;
            Finished = false;
            Result["harnessVersion"] = Version;
            Result["runId"] = next.RunId;
            Result["status"] = "running";
            Result["chainedFrom"] = _parentDir;
            Result["startedUtc"] = _startedUtc.ToString("o", CultureInfo.InvariantCulture);
            Result["gameVersion"] = Application.version;
            Result["unityVersion"] = Application.unityVersion;
            Info("chained game: run " + next.RunId + ", faction " + next.Faction + ", map " + next.Map + " -> " + OutputDir);
            WriteResult("running");
            MainMenuRequested = true;   // ChainHook opens the main menu on the next frame
            return true;
        }

        /// <summary>After a chained game: the first game's result.json, with the second game's summary folded in.</summary>
        private static void MergeIntoParent(string status)
        {
            var parent = _parentResult;
            if (parent == null) return;
            _parentResult = null;
            JObject child;
            lock (LogLock) child = (JObject)Result.DeepClone();
            string verdict = (string)child["verdict"] ?? "none";
            var failed = new List<string>();
            if (child["checks"] is JArray checks)
                foreach (var c in checks) if ((bool?)c["pass"] != true) failed.Add((string)c["name"] + ": " + (string)c["detail"]);
            parent["then"] = new JObject
            {
                ["outputDir"] = OutputDir, ["faction"] = Request.Faction, ["activeFaction"] = child["activeFaction"]?["id"],
                ["status"] = status, ["verdict"] = verdict, ["failedChecks"] = new JArray(failed.ToArray()),
                ["materialProbe"] = child["materialProbe"], ["pandabornBoot"] = child["pandabornBoot"]
            };
            bool pass = verdict == "pass";
            if (!(parent["checks"] is JArray parentChecks)) parent["checks"] = parentChecks = new JArray();
            parentChecks.Add(new JObject
            {
                ["name"] = "then", ["pass"] = pass,
                ["detail"] = "chained " + Request.Faction + " game in " + OutputDir + ": " + status + ", verdict " + verdict
                             + (failed.Count > 0 ? " (" + string.Join("; ", failed.ToArray()) + ")" : "")
            });
            if (!pass) parent["verdict"] = "fail";
            parent["updatedUtc"] = DateTime.UtcNow.ToString("o", CultureInfo.InvariantCulture);
            string target = Path.Combine(_parentDir, "result.json");
            File.WriteAllText(target + ".tmp", parent.ToString(Formatting.Indented));
            if (File.Exists(target)) File.Delete(target);
            File.Move(target + ".tmp", target);
            Info("chained game finished (" + verdict + "); wrote " + target);
        }
    }

    [Context("Game")]
    public class ChainConfigurator : Configurator
    {
        protected override void Configure()
        {
            if (!Harness.Active) return;   // no request: bind nothing at all
            Bind<ChainHook>().AsSingleton();
        }
    }

    /// <summary>Leaves the game for the main menu (no save) when the harness asks for a chained game.</summary>
    public class ChainHook : IUpdatableSingleton
    {
        private readonly MainMenuSceneLoader _mainMenuSceneLoader;

        public ChainHook(MainMenuSceneLoader mainMenuSceneLoader)
        {
            _mainMenuSceneLoader = mainMenuSceneLoader;
        }

        public void UpdateSingleton()
        {
            if (!Harness.MainMenuRequested) return;
            Harness.MainMenuRequested = false;
            try
            {
                Harness.Info("exiting to the main menu for the chained game");
                _mainMenuSceneLoader.OpenMainMenu();
            }
            catch (Exception e)
            {
                Harness.Error("exiting to the main menu failed", e);
                Harness.Finish("error");
            }
        }
    }
}
