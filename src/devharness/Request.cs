using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using Newtonsoft.Json.Linq;

namespace PandabornDevHarness
{
    /// <summary>One screenshot to take. Kind: overview | screen | adult | child | bot. At: start | end | seconds after the run phase began.</summary>
    public class ShotRequest
    {
        public string Name;
        public string Kind;
        public string At;
        /// <summary>Kind "building": template name of a building placed by this request, framed in close-up.</summary>
        public string Target;
        /// <summary>Kind "building": degrees added to the game camera's heading, camera pitch, and zoom (1 = building fills the frame).</summary>
        public float Yaw;
        public float Pitch = 35f;
        public float Zoom = 1f;
        /// <summary>Kind "building": switch the building's night lighting on before the shot (as when occupied).</summary>
        public bool Lit;

        public bool IsTimed(out float seconds)
        {
            return float.TryParse(At, NumberStyles.Float, CultureInfo.InvariantCulture, out seconds);
        }
    }

    /// <summary>A building to place near the district center. Offset is relative to the district center doorstep.</summary>
    public class BuildingRequest
    {
        public string Template;
        public bool Finished = true;
        public int[] Offset;
        public string Orientation;
    }

    /// <summary>
    /// The parsed test request (request.json). Every field is optional:
    /// <code>
    /// { "runId", "outputDir", "expiresUtc" (ISO; ignored after it), "faction": "Folktails", "map": "Diorama"
    ///   (builtin, user map name or .timber path), "gameMode": "Normal", "settlementName": "PB_AutoTest_...",
    ///   "speed": 3, "devMode": true, "mute": true, "quit": true,
    ///   "window": { "windowed": true, "width": 1280, "height": 720 },
    ///   "run": { "realSeconds": 60, "inGameDays": 0, "inGameHours": 0, "settleSeconds": 4, "startTimeoutSeconds": 240 },
    ///   "buildings": [ "Lodge.Folktails", { "template", "finished": true, "offset": [dx, dy, dz], "orientation": "Cw90" } ],
    ///   "screenshots": [ { "name", "kind": "overview|screen|adult|child|bot|building", "at": "start|end|&lt;seconds into run&gt;",
    ///                      "target": "Lodge.Folktails" (kind building), "yaw": 0, "pitch": 35, "zoom": 1, "lit": false } ],
    ///   "screenshotSize": [1280, 720], "closeupSize": 640, "samplePerKind": 3,
    ///   "ownPatterns": [ "PandabornFactions", "PandabornDevHarness", "Inkpaws" ],
    ///   "batchControl": true (open every batch-control tab at the end; a throwing tab fails the run),
    ///   "connectPaths": true (lay Path tiles from the district center doorstep to each placed building),
    ///   "factionPanelShots": false (screen captures of the main menu's new-game faction panel, one per faction),
    ///   "save": "PB_AutoTest" (save name; the game is saved to Saves/&lt;settlementName&gt;/ at the end),
    ///   "loadSave": false (the game was launched with -saveName/-settlementName: do not start a new game),
    ///   "then": { "faction": "Folktails", "name": "then", ... } (after this game, exit to the main menu and play a second new
    ///           game in the same launch with these keys overriding; its output goes to &lt;outputDir&gt;\&lt;name&gt;; see Chain.cs),
    ///   "materialProbe": [ material asset paths ] (texture names on loaded materials in result "materialProbe"; MaterialProbe.cs),
    ///   "checks": { "minAdults": 1, "minChildren": 0, "minBots": 0, "noOwnErrors": true, "maxErrors": n,
    ///               "adultTemplate", "childTemplate", "botTemplate", "adultMeshContains", "adultTextureContains",
    ///               "adultModel" (exact model asset path), "adultTextureAsset" (substring of the coat's asset path), ...,
    ///               "botTemplateExists": true, "templatesAvailable": [], "templatesUnavailable": [] } }
    /// </code>
    /// With an in-game duration, realSeconds is only a cap (default 900).
    /// </summary>
    public class Request
    {
        public JObject Raw;
        public string RunId;
        public string OutputDir;
        public DateTime ExpiresUtc;

        public string Faction = "Folktails";
        public string Map = "Diorama";
        public string GameMode = "";
        public string SettlementName;

        public float Speed = 3f;
        public bool DevMode = true;
        public bool Mute = true;
        public bool Windowed = true;
        public int Width = 1280;
        public int Height = 720;

        public float SettleSeconds = 4f;
        public float RunRealSeconds = 60f;
        public float RunInGameHours;
        public float MaxRealSeconds = 900f;
        public float StartTimeoutSeconds = 240f;

        public readonly List<BuildingRequest> Buildings = new List<BuildingRequest>();
        public readonly List<ShotRequest> Screenshots = new List<ShotRequest>();
        public int ShotWidth = 1280;
        public int ShotHeight = 720;
        public int CloseupSize = 640;
        public int SamplePerKind = 3;

        public readonly List<string> OwnPatterns = new List<string>();
        public JObject Checks = new JObject();
        public bool Quit = true;

        public bool BatchControl = true;
        public bool ConnectPaths = true;
        public bool FactionPanelShots;
        public string SaveName;
        public bool LoadSave;

        public static Request Parse(string path)
        {
            var raw = JObject.Parse(File.ReadAllText(path));
            var r = new Request { Raw = raw };
            r.RunId = Str(raw, "runId", DateTime.Now.ToString("yyyyMMdd-HHmmss", CultureInfo.InvariantCulture));
            r.OutputDir = Str(raw, "outputDir", Path.Combine(Path.GetDirectoryName(path) ?? ".", r.RunId));
            var expires = Str(raw, "expiresUtc", null);
            r.ExpiresUtc = expires != null
                ? DateTime.Parse(expires, CultureInfo.InvariantCulture, DateTimeStyles.AdjustToUniversal | DateTimeStyles.AssumeUniversal)
                : File.GetLastWriteTimeUtc(path).AddHours(1);

            r.Faction = Str(raw, "faction", r.Faction);
            r.Map = Str(raw, "map", r.Map);
            r.GameMode = Str(raw, "gameMode", r.GameMode);
            r.SettlementName = Str(raw, "settlementName", "PB_AutoTest_" + r.RunId);
            if (!r.SettlementName.StartsWith("PB_AutoTest", StringComparison.Ordinal)) r.SettlementName = "PB_AutoTest_" + r.SettlementName;
            r.Speed = Num(raw, "speed", r.Speed);
            r.DevMode = Bool(raw, "devMode", r.DevMode);
            r.Mute = Bool(raw, "mute", r.Mute);
            r.Quit = Bool(raw, "quit", r.Quit);
            r.BatchControl = Bool(raw, "batchControl", r.BatchControl);
            r.ConnectPaths = Bool(raw, "connectPaths", r.ConnectPaths);
            r.FactionPanelShots = Bool(raw, "factionPanelShots", r.FactionPanelShots);
            r.SaveName = Str(raw, "save", null);
            if (string.IsNullOrWhiteSpace(r.SaveName)) r.SaveName = null;
            r.LoadSave = Bool(raw, "loadSave", r.LoadSave);

            if (raw["window"] is JObject window)
            {
                r.Windowed = Bool(window, "windowed", r.Windowed);
                r.Width = (int)Num(window, "width", r.Width);
                r.Height = (int)Num(window, "height", r.Height);
            }

            if (raw["run"] is JObject run)
            {
                r.SettleSeconds = Num(run, "settleSeconds", r.SettleSeconds);
                r.RunInGameHours = Num(run, "inGameDays", 0f) * 24f + Num(run, "inGameHours", 0f);
                bool hasReal = run["realSeconds"] != null;
                r.RunRealSeconds = Num(run, "realSeconds", r.RunInGameHours > 0f ? r.MaxRealSeconds : r.RunRealSeconds);
                // with an in-game target, realSeconds is a cap; without one it is the run length
                if (r.RunInGameHours > 0f && !hasReal) r.RunRealSeconds = r.MaxRealSeconds;
                r.StartTimeoutSeconds = Num(run, "startTimeoutSeconds", r.StartTimeoutSeconds);
            }

            if (raw["buildings"] is JArray buildings)
            {
                foreach (var token in buildings)
                {
                    if (token.Type == JTokenType.String) { r.Buildings.Add(new BuildingRequest { Template = (string)token }); continue; }
                    if (!(token is JObject b)) continue;
                    var request = new BuildingRequest
                    {
                        Template = Str(b, "template", null),
                        Finished = Bool(b, "finished", true),
                        Orientation = Str(b, "orientation", null)
                    };
                    if (b["offset"] is JArray offset && offset.Count >= 2)
                        request.Offset = new[] { (int)offset[0], (int)offset[1], offset.Count > 2 ? (int)offset[2] : 0 };
                    if (!string.IsNullOrEmpty(request.Template)) r.Buildings.Add(request);
                }
            }

            if (raw["screenshots"] is JArray shots)
            {
                foreach (var token in shots)
                {
                    if (!(token is JObject s)) continue;
                    var kind = Str(s, "kind", "overview").ToLowerInvariant();
                    var at = Str(s, "at", "start").ToLowerInvariant();
                    r.Screenshots.Add(new ShotRequest
                    {
                        Kind = kind, At = at, Name = Str(s, "name", kind + "_" + at), Target = Str(s, "target", null),
                        Yaw = Num(s, "yaw", 0f), Pitch = Num(s, "pitch", 35f), Zoom = Num(s, "zoom", 1f),
                        Lit = Bool(s, "lit", false)
                    });
                }
            }
            else
            {
                r.Screenshots.Add(new ShotRequest { Kind = "overview", At = "start", Name = "overview_start" });
                r.Screenshots.Add(new ShotRequest { Kind = "adult", At = "start", Name = "adult_start" });
                r.Screenshots.Add(new ShotRequest { Kind = "child", At = "start", Name = "child_start" });
                r.Screenshots.Add(new ShotRequest { Kind = "overview", At = "end", Name = "overview_end" });
                r.Screenshots.Add(new ShotRequest { Kind = "screen", At = "end", Name = "screen_end" });
            }
            if (raw["screenshotSize"] is JArray size && size.Count >= 2) { r.ShotWidth = (int)size[0]; r.ShotHeight = (int)size[1]; }
            r.CloseupSize = (int)Num(raw, "closeupSize", r.CloseupSize);
            r.SamplePerKind = (int)Num(raw, "samplePerKind", r.SamplePerKind);

            if (raw["ownPatterns"] is JArray patterns)
                foreach (var p in patterns) r.OwnPatterns.Add((string)p);
            if (r.OwnPatterns.Count == 0) r.OwnPatterns.AddRange(new[] { "PandabornFactions", "PandabornDevHarness", "Inkpaws" });
            if (raw["checks"] is JObject checks) r.Checks = checks;
            return r;
        }

        public static string Str(JObject o, string key, string fallback)
        {
            var t = o[key];
            return t == null || t.Type == JTokenType.Null ? fallback : (string)t;
        }

        public static float Num(JObject o, string key, float fallback)
        {
            var t = o[key];
            return t == null || t.Type == JTokenType.Null ? fallback : (float)t;
        }

        public static bool Bool(JObject o, string key, bool fallback)
        {
            var t = o[key];
            return t == null || t.Type == JTokenType.Null ? fallback : (bool)t;
        }
    }
}
