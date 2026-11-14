using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Timberborn.ErrorReporting;
using Timberborn.ModManagerScene;
using UnityEngine;

namespace PandabornDevHarness
{
    /// <summary>Entry point. Does nothing unless a non-expired request file exists.</summary>
    public class HarnessStarter : IModStarter
    {
        public void StartMod(IModEnvironment modEnvironment)
        {
            try { Harness.Initialize(modEnvironment.ModPath); }
            catch (Exception e) { Debug.LogWarning("[PandabornDevHarness] could not start: " + e); }
        }
    }

    public class LogEntry
    {
        public string Type;
        public string Message;
        public string Stack;
        public bool Ours;
        public float Time;
    }

    /// <summary>Static state shared by the main-menu and game drivers; survives scene changes.</summary>
    public static partial class Harness
    {
        public const string Version = "1.0.0";
        public const string DefaultRequestPath = @"E:\PandabornDev\build\test\request.json";
        private const string CommandLineKey = "-pbTestRequest";
        private const int MaxLogEntries = 300;

        public static bool Active { get; private set; }
        public static Request Request { get; private set; }
        public static string OutputDir { get; private set; }
        public static bool GameRequested;
        public static bool Finished { get; private set; }

        /// <summary>Sections filled in by the drivers as the run progresses.</summary>
        public static readonly JObject Result = new JObject();
        public static readonly JArray Warnings = new JArray();
        public static readonly JArray Screenshots = new JArray();

        /// <summary>Called from the crash path to collect whatever the game driver can still report.</summary>
        public static Action CollectOnCrash;

        private static readonly object LogLock = new object();
        private static readonly List<LogEntry> LogEntries = new List<LogEntry>();
        private static int _errors, _exceptions, _warnings, _ownErrors, _ownExceptions;
        private static string _crash;
        private static DateTime _startedUtc;

        public static void Initialize(string modPath)
        {
            string path = FindRequestPath();
            if (path == null || !File.Exists(path)) return;
            var request = Request.Parse(path);
            if (DateTime.UtcNow > request.ExpiresUtc)
            {
                Debug.Log("[PandabornDevHarness] ignoring expired request " + path);
                return;
            }
            Directory.CreateDirectory(request.OutputDir);
            // consume the request so a later normal launch of the game does nothing
            File.Copy(path, Path.Combine(request.OutputDir, "request.json"), true);
            File.Delete(path);

            Request = request;
            OutputDir = request.OutputDir;
            Active = true;
            _startedUtc = DateTime.UtcNow;
            Application.logMessageReceivedThreaded += OnLog;
            ExceptionListener.FirstUncaughtException += OnUncaughtException;
            ApplyRuntimeSettings();

            Result["harnessVersion"] = Version;
            Result["runId"] = request.RunId;
            Result["status"] = "running";
            Result["modPath"] = modPath;
            Result["startedUtc"] = _startedUtc.ToString("o", CultureInfo.InvariantCulture);
            Result["gameVersion"] = Application.version;
            Result["unityVersion"] = Application.unityVersion;
            Result["commandLine"] = string.Join(" ", Environment.GetCommandLineArgs());
            Info("active: run " + request.RunId + ", faction " + request.Faction + ", map " + request.Map + " -> " + OutputDir);
            WriteResult("running");
        }

        private static string FindRequestPath()
        {
            var args = Environment.GetCommandLineArgs();
            for (int i = 0; i < args.Length - 1; i++)
                if (args[i] == CommandLineKey) return args[i + 1];
            var env = Environment.GetEnvironmentVariable("PANDABORN_TEST_REQUEST");
            return string.IsNullOrEmpty(env) ? DefaultRequestPath : env;
        }

        /// <summary>Runtime-only tweaks; nothing here touches the player's saved settings.</summary>
        public static void ApplyRuntimeSettings()
        {
            if (!Active) return;
            Application.runInBackground = true;
            if (Request.Mute) AudioListener.volume = 0f;
        }

        public static void ApplyWindow()
        {
            if (!Active || !Request.Windowed) return;
            if (Screen.fullScreenMode != FullScreenMode.Windowed || Screen.width != Request.Width || Screen.height != Request.Height)
            {
                Screen.SetResolution(Request.Width, Request.Height, FullScreenMode.Windowed);
                Info("window set to " + Request.Width + "x" + Request.Height + " windowed");
            }
        }

        // ------------------------------------------------------------------ logging

        public static void Info(string message)
        {
            Debug.Log("[PandabornDevHarness] " + message);
            AppendHarnessLog("INFO  " + message);
        }

        public static void Warn(string message)
        {
            Debug.LogWarning("[PandabornDevHarness] " + message);
            AppendHarnessLog("WARN  " + message);
            lock (LogLock) Warnings.Add(message);
        }

        /// <summary>A harness failure. Logged as an error, so it also counts against "our" errors.</summary>
        public static void Error(string message, Exception e = null)
        {
            Debug.LogError("[PandabornDevHarness] " + message + (e != null ? "\n" + e : ""));
            AppendHarnessLog("ERROR " + message + (e != null ? " " + e : ""));
        }

        private static void AppendHarnessLog(string line)
        {
            if (OutputDir == null) return;
            try
            {
                lock (LogLock)
                    File.AppendAllText(Path.Combine(OutputDir, "harness.log"),
                        DateTime.Now.ToString("HH:mm:ss.fff", CultureInfo.InvariantCulture) + " " + line + "\r\n");
            }
            catch (Exception) { }
        }

        private static void OnLog(string condition, string stackTrace, LogType type)
        {
            if (type == LogType.Log) return;
            lock (LogLock)
            {
                if (type == LogType.Warning) { _warnings++; return; }
                bool ours = IsOurs(condition) || IsOurs(stackTrace);
                if (type == LogType.Exception) { _exceptions++; if (ours) _ownExceptions++; }
                else { _errors++; if (ours) _ownErrors++; }
                if (LogEntries.Count < MaxLogEntries)
                    LogEntries.Add(new LogEntry
                    {
                        Type = type.ToString(),
                        Message = Truncate(condition, 2000),
                        Stack = Truncate(stackTrace, 3000),
                        Ours = ours,
                        Time = (float)(DateTime.UtcNow - _startedUtc).TotalSeconds
                    });
            }
        }

        public static bool IsOurs(string text)
        {
            if (string.IsNullOrEmpty(text) || Request == null) return false;
            foreach (var pattern in Request.OwnPatterns)
                if (!string.IsNullOrEmpty(pattern) && text.IndexOf(pattern, StringComparison.OrdinalIgnoreCase) >= 0) return true;
            return false;
        }

        private static string Truncate(string s, int max)
        {
            if (s == null) return "";
            return s.Length <= max ? s : s.Substring(0, max) + "...";
        }

        private static void OnUncaughtException(object sender, EventArgs e)
        {
            if (Finished) return;
            _crash = ErrorReporter.LogString;
            try { CollectOnCrash?.Invoke(); }
            catch (Exception ex) { AppendHarnessLog("ERROR collecting after crash: " + ex); }
            Finish("crashed");
        }

        // ------------------------------------------------------------------ result

        public static void RecordScreenshot(string name, string kind, string file, JObject subject, string error)
        {
            var o = new JObject { ["name"] = name, ["kind"] = kind, ["file"] = file };
            if (subject != null) o["subject"] = subject;
            if (error != null) o["error"] = error;
            lock (LogLock) Screenshots.Add(o);
        }

        /// <summary>Writes the final result.json and quits the game (unless the request says not to).</summary>
        public static void Finish(string status)
        {
            if (Finished) return;
            Finished = true;
            MaterialProbe.ProbeAtEnd();
            if (TryChain(status)) return;   // a second game follows in this launch (request "then", Chain.cs)
            try
            {
                WriteResult(status);
                Info("finished with status " + status + "; verdict " + Result["verdict"]);
            }
            catch (Exception e) { AppendHarnessLog("ERROR writing result: " + e); }
            try { MergeIntoParent(status); }
            catch (Exception e) { AppendHarnessLog("ERROR writing the first game's result: " + e); }
            if (Request == null || Request.Quit)
            {
                Info("quitting");
                Application.Quit();
            }
        }

        public static void WriteResult(string status, string fileName = null)
        {
            if (OutputDir == null) return;
            JObject snapshot;
            lock (LogLock)
            {
                Result["status"] = status;
                Result["updatedUtc"] = DateTime.UtcNow.ToString("o", CultureInfo.InvariantCulture);
                Result["realSecondsSinceStart"] = Math.Round((DateTime.UtcNow - _startedUtc).TotalSeconds, 1);
                if (_crash != null) Result["uncaughtException"] = _crash;
                Result["screenshots"] = Screenshots.DeepClone();
                Result["warnings"] = Warnings.DeepClone();
                var entries = new JArray();
                foreach (var entry in LogEntries)
                    entries.Add(new JObject
                    {
                        ["type"] = entry.Type, ["ours"] = entry.Ours, ["t"] = Math.Round(entry.Time, 1),
                        ["message"] = entry.Message, ["stack"] = entry.Stack
                    });
                Result["log"] = new JObject
                {
                    ["errors"] = _errors, ["exceptions"] = _exceptions, ["warnings"] = _warnings,
                    ["ownErrors"] = _ownErrors, ["ownExceptions"] = _ownExceptions,
                    ["ownPatterns"] = new JArray(Request.OwnPatterns.ToArray()),
                    ["entries"] = entries
                };
                if (status != "running") Checks.Evaluate(Result, Request, status, _ownErrors + _ownExceptions, _errors + _exceptions);
                snapshot = (JObject)Result.DeepClone();
            }
            string target = Path.Combine(OutputDir, fileName ?? (status == "running" ? "progress.json" : "result.json"));
            string tmp = target + ".tmp";
            File.WriteAllText(tmp, snapshot.ToString(Formatting.Indented));
            if (File.Exists(target)) File.Delete(target);
            File.Move(tmp, target);
        }
    }
}
