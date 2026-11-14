using System;
using System.Collections.Generic;
using System.Linq;
using Bindito.Core;
using Newtonsoft.Json.Linq;
using Timberborn.BeaversUI;
using Timberborn.Buildings;
using Timberborn.GameSound;
using Timberborn.EntitySystem;
using Timberborn.SingletonSystem;
using Timberborn.SoundSystem;
using Timberborn.TemplateSystem;
using UnityEngine;

namespace PandabornDevHarness
{
    [Context("Game")]
    public class SoundProbeConfigurator : Configurator
    {
        protected override void Configure()
        {
            if (!Harness.Active || !(Harness.Request?.Raw?["soundProbe"] is JObject)) return;
            Bind<SoundProbe>().AsSingleton();
        }
    }

    /// <summary>
    /// Evidence that sounds load and play (the run is muted: AudioListener.volume = 0 silences the speakers, not the
    /// sources). Active only when request.json has a "soundProbe" object:
    /// <code>
    /// "soundProbe": {
    ///   "expect": [ "Environment.Pandaborn.ShiftBell.End", ... ],   // ids to look up in the game's AudioClipService
    ///   "bundle": "pandabornsounds",                               // a loaded AssetBundle whose name starts with this
    ///   "play":  [ { "id": "...", "at": 20, "mode": "2d" | "3d", "target": "PandabornVillageHall.Inkpaws" } ],
    ///   "loops": [ { "target": "PandabornSteamer.Inkpaws", "at": 25, "stopAt": 40 } ],  // BuildingSounds.ToggleSound
    ///   "select": [ { "target": "PandabornVillageHall.Inkpaws" | "InkpawAdult.Inkpaws", "at": 30 } ],  // the game's own
    ///              selection-sound components (BuildingSelectionSound, BeaverSelectionSound).OnSelect(): the data paths
    ///              BuildingSpec.SelectionSoundName and FactionSpec.SoundId
    ///   "wonderLaunch": [ 40 ],                                    // GameUISoundController.PlayWonderLaunchSound() at
    ///              these times: the data path FactionWonderSpec.WonderLaunchSound (no wonder is activated)
    ///   "sampleEvery": 0.5, "watch": "Pandaborn"                   // which playing clips get a detailed record
    ///   (every "at" counts real seconds from the game's first frame update, not from PostLoad)
    /// }
    /// </code>
    /// Result "soundProbe": "clips" (per expected id: the variants the game knows, length, channels, rate, load type and
    /// state, and whether each is the very object in the bundle), "bundle" (loaded bundle names and how many sound assets
    /// they hold), "actions" (each play / loop call and its outcome), "playing" (every clip seen playing on any
    /// AudioSource: first and last time, samples, max output RMS from AudioSource.GetOutputData, loop, spatial blend,
    /// mixer group, emitter), and "vanillaPlaying" (names of other clips seen, to show the probe sees the game's own).
    /// Checks (request.checks): "soundsKnown": [ids] every id has at least one clip in AudioClipService;
    /// "soundsPlayed": [ids] a clip of each id was seen playing: output RMS above zero, or its playback position advancing
    /// between samples (a 3D voice out of earshot is virtual and reads zeros);
    /// "soundsNotPlayed": "Pandaborn" no clip whose name contains it was seen playing (other factions' games).
    /// </summary>
    public class SoundProbe : IPostLoadableSingleton, IUpdatableSingleton
    {
        private readonly AudioClipService _audioClipService;
        private readonly ISoundSystem _soundSystem;
        private readonly EntityRegistry _entityRegistry;
        private readonly GameUISoundController _gameUISoundController;
        private JObject _spec;
        private float _loadedAt = -1f, _nextSample;
        private bool _ready;
        private readonly List<JObject> _pending = new List<JObject>();
        private readonly JObject _playing = new JObject();
        private readonly HashSet<string> _vanilla = new HashSet<string>();
        private readonly float[] _buffer = new float[1024];
        private readonly Dictionary<AudioSource, float> _lastTime = new Dictionary<AudioSource, float>();
        private GameObject _root2D;
        private string _watch;

        public SoundProbe(AudioClipService audioClipService, ISoundSystem soundSystem, EntityRegistry entityRegistry,
                          GameUISoundController gameUISoundController)
        {
            _gameUISoundController = gameUISoundController;
            _audioClipService = audioClipService;
            _soundSystem = soundSystem;
            _entityRegistry = entityRegistry;
        }

        public void PostLoad()
        {
            try
            {
                _spec = (JObject)Harness.Request.Raw["soundProbe"];
                _watch = (string)_spec["watch"] ?? "Pandaborn";
                var result = new JObject { ["playing"] = _playing, ["actions"] = new JArray() };
                Harness.Result["soundProbe"] = result;
                result["clips"] = DescribeClips();
                result["bundle"] = DescribeBundles((string)_spec["bundle"] ?? "pandabornsounds");
                if (_spec["wonderLaunch"] is JArray launches)
                    foreach (var at in launches) _pending.Add(new JObject { ["kind"] = "wonderLaunch", ["at"] = at });
                foreach (var key in new[] { "play", "loops", "select" })
                    if (_spec[key] is JArray list)
                        foreach (JObject a in list)
                        {
                            var copy = (JObject)a.DeepClone();
                            copy["kind"] = key;
                            _pending.Add(copy);
                            if (key == "loops" && a["stopAt"] != null)
                                _pending.Add(new JObject { ["kind"] = "stop", ["target"] = a["target"], ["at"] = a["stopAt"] });
                        }
                _root2D = new GameObject("PandabornSoundProbe2D");
                _ready = true;   // the clock starts at the first frame update: the scene can take a minute after PostLoad
                Harness.Info("sound probe: " + ((JObject)result["clips"]).Count + " ids looked up, " + _pending.Count + " actions queued");
            }
            catch (Exception e) { Harness.Warn("sound probe failed at load: " + e.GetType().Name + ": " + e.Message); }
        }

        public void UpdateSingleton()
        {
            if (!_ready || Harness.Finished) return;
            if (_loadedAt < 0f) _loadedAt = Time.unscaledTime;
            float now = Time.unscaledTime - _loadedAt;
            for (int i = _pending.Count - 1; i >= 0; i--)
            {
                var a = _pending[i];
                float at = (float?)a["at"] ?? 0f;
                if (now < at) continue;
                // a target building may not be placed yet (the harness places buildings a few seconds into the game):
                // wait for it up to 90 s, then run anyway and log "target not found"
                string target = (string)a["target"];
                if (!string.IsNullOrEmpty(target) && now < at + 90f && (Time.frameCount % 15 != 0 || Find(target) == null)) continue;
                _pending.RemoveAt(i);
                Run(a, now);
            }
            if (Time.unscaledTime >= _nextSample)
            {
                _nextSample = Time.unscaledTime + Request.Num(_spec, "sampleEvery", 0.5f);
                Sample(now);
            }
        }

        private void Run(JObject a, float now)
        {
            var log = (JArray)Harness.Result["soundProbe"]["actions"];
            var entry = new JObject { ["kind"] = a["kind"], ["at"] = Math.Round(now, 1) };
            foreach (var p in a.Properties()) if (p.Name != "kind" && p.Name != "at") entry[p.Name] = p.Value.DeepClone();
            log.Add(entry);
            try
            {
                string kind = (string)a["kind"];
                string target = (string)a["target"];
                if (kind == "play")
                {
                    string id = (string)a["id"];
                    if (((string)a["mode"] ?? "2d") == "3d")
                    {
                        var e = Find(target);
                        if (e == null) { entry["error"] = "target not found: " + target; return; }
                        _soundSystem.PlaySound3D(e.GameObject, id, 30);
                        entry["emitter"] = e.GameObject.name;
                    }
                    else
                    {
                        _soundSystem.PlaySound2D(_root2D, id, 10);
                    }
                    entry["ok"] = true;
                }
                else if (kind == "wonderLaunch")
                {
                    _gameUISoundController.PlayWonderLaunchSound();
                    entry["ok"] = true;
                }
                else if (kind == "select")
                {
                    var e = Find(target);
                    if (e == null) { entry["error"] = "target not found: " + target; return; }
                    var building = e.GetComponent<BuildingSelectionSound>();
                    var beaver = e.GetComponent<BeaverSelectionSound>();
                    if (building != null) { building.OnSelect(); entry["component"] = "BuildingSelectionSound"; }
                    else if (beaver != null) { beaver.OnSelect(); entry["component"] = "BeaverSelectionSound"; }
                    else { entry["error"] = "no selection sound component on " + target; return; }
                    entry["selectionSoundName"] = e.GetComponent<BuildingSpec>()?.SelectionSoundName;
                    entry["ok"] = true;
                }
                else if (kind == "loops" || kind == "stop")
                {
                    var e = Find(target);
                    if (e == null) { entry["error"] = "target not found: " + target; return; }
                    var sounds = e.GetComponent<BuildingSounds>();
                    var spec = e.GetComponent<BuildingSpec>();
                    entry["loopingSoundName"] = spec?.LoopingSoundName;
                    if (sounds == null) { entry["error"] = "no BuildingSounds on " + target; return; }
                    sounds.ToggleSound(kind == "loops");
                    entry["ok"] = true;
                }
                Harness.Info("sound probe: " + kind + " " + (string)a["id"] + " " + target);
            }
            catch (Exception e)
            {
                entry["error"] = e.GetType().Name + ": " + e.Message;
                Harness.Warn("sound probe action failed: " + entry["error"]);
            }
        }

        private EntityComponent Find(string template)
        {
            if (string.IsNullOrEmpty(template)) return null;
            foreach (var entity in _entityRegistry.Entities)
            {
                if (!entity) continue;
                var ts = entity.GetComponent<TemplateSpec>();
                if (ts != null && ts.TemplateName == template) return entity;
            }
            return null;
        }

        private void Sample(float now)
        {
            try
            {
                foreach (var src in UnityEngine.Object.FindObjectsByType<AudioSource>(FindObjectsInactive.Exclude, FindObjectsSortMode.None))
                {
                    if (!src || !src.clip || !src.isPlaying) continue;
                    string name = src.clip.name;
                    if (_watch.Length > 0 && name.IndexOf(_watch, StringComparison.Ordinal) < 0)
                    {
                        _vanilla.Add(name);
                        continue;
                    }
                    double rms = 0;
                    try
                    {
                        src.GetOutputData(_buffer, 0);
                        double s = 0;
                        for (int i = 0; i < _buffer.Length; i++) s += _buffer[i] * _buffer[i];
                        rms = Math.Sqrt(s / _buffer.Length);
                    }
                    catch (Exception) { rms = -1; }
                    if (!(_playing[name] is JObject o))
                    {
                        o = new JObject
                        {
                            ["firstSeen"] = Math.Round(now, 1), ["samples"] = 0, ["maxOutputRms"] = 0.0,
                            ["loop"] = src.loop, ["spatialBlend"] = src.spatialBlend,
                            ["mixer"] = src.outputAudioMixerGroup ? src.outputAudioMixerGroup.name : null,
                            ["emitter"] = src.transform.parent ? src.transform.parent.name : src.gameObject.name,
                            ["minDistance"] = src.minDistance, ["maxDistance"] = src.maxDistance,
                            ["clipLength"] = Math.Round(src.clip.length, 3), ["pitch"] = Math.Round(src.pitch, 3)
                        };
                        _playing[name] = o;
                    }
                    o["lastSeen"] = Math.Round(now, 1);
                    o["samples"] = (int)o["samples"] + 1;
                    o["maxOutputRms"] = Math.Max((double)o["maxOutputRms"], Math.Round(rms, 6));
                    o["volume"] = Math.Round(src.volume, 3);
                    // playback position moving between samples: the clip is being played even when the voice is virtual
                    // (out of earshot of the listener, where GetOutputData reads zeros)
                    if (_lastTime.TryGetValue(src, out float last) && Math.Abs(src.time - last) > 1e-3f) o["advanced"] = true;
                    _lastTime[src] = src.time;
                }
                Harness.Result["soundProbe"]["vanillaPlaying"] = new JArray(_vanilla.OrderBy(s => s).ToArray());
            }
            catch (Exception e) { Harness.Warn("sound probe sample: " + e.GetType().Name + ": " + e.Message); }
        }

        private JObject DescribeClips()
        {
            var clips = new JObject();
            foreach (var token in (_spec["expect"] as JArray) ?? new JArray())
            {
                string id = (string)token;
                var list = new JArray();
                foreach (var name in _audioClipService.GetAudioClipNames(id).OrderBy(n => n))
                {
                    var c = _audioClipService.GetAudioClip(name);
                    list.Add(new JObject
                    {
                        ["name"] = name, ["length"] = Math.Round(c.length, 3), ["channels"] = c.channels, ["frequency"] = c.frequency,
                        ["loadType"] = c.loadType.ToString(), ["loadState"] = c.loadState.ToString(),
                        ["inBundle"] = InBundle(c)
                    });
                }
                clips[id] = list;
            }
            return clips;
        }

        private static string InBundle(AudioClip clip)
        {
            foreach (var b in AssetBundle.GetAllLoadedAssetBundles())
            {
                if (!b || b.isStreamedSceneAssetBundle) continue;
                foreach (var path in b.GetAllAssetNames())
                {
                    if (!path.EndsWith("/" + clip.name.ToLowerInvariant() + ".wav", StringComparison.Ordinal)) continue;
                    var loaded = b.LoadAsset<AudioClip>(path);
                    return loaded == clip ? b.name : b.name + " (a different object)";
                }
            }
            return null;
        }

        private static JArray DescribeBundles(string prefix)
        {
            var list = new JArray();
            foreach (var b in AssetBundle.GetAllLoadedAssetBundles())
            {
                if (!b || !b.name.StartsWith(prefix, StringComparison.OrdinalIgnoreCase)) continue;
                var names = b.isStreamedSceneAssetBundle ? new string[0] : b.GetAllAssetNames();
                list.Add(new JObject
                {
                    ["name"] = b.name, ["assets"] = names.Length,
                    ["soundAssets"] = names.Count(n => n.Contains("/resources/sounds/"))
                });
            }
            return list;
        }

        /// <summary>Adds the sound checks named in request.checks (see the class comment).</summary>
        public static void AddChecks(JObject result, JObject options, Action<string, bool, string> add)
        {
            var probe = result["soundProbe"] as JObject;
            if (options["soundsKnown"] is JArray known)
                foreach (var t in known)
                {
                    var list = probe?["clips"]?[(string)t] as JArray;
                    add("soundKnown", list != null && list.Count > 0, (string)t + ": " + (list == null ? "not looked up" :
                        list.Count + " clip(s)" + (list.Count > 0 ? ", in bundle " + (string)list[0]["inBundle"] : "")));
                }
            if (options["soundsPlayed"] is JArray played)
                foreach (var t in played)
                {
                    string id = (string)t;
                    var hits = new List<string>();
                    bool ok = false;
                    if (probe?["playing"] is JObject playing)
                        foreach (var p in playing.Properties())
                            if (p.Name == id || p.Name.StartsWith(id + "_", StringComparison.Ordinal))
                            {
                                double rms = (double)p.Value["maxOutputRms"];
                                bool advanced = (bool?)p.Value["advanced"] == true;
                                ok |= rms > 0 || advanced;
                                hits.Add(p.Name + " rms " + rms.ToString("0.0000") + (advanced ? " advancing" : "") + " mixer " + (string)p.Value["mixer"]);
                            }
                    add("soundPlayed", ok, id + ": " + (hits.Count > 0 ? string.Join("; ", hits.ToArray()) : "never seen playing"));
                }
            if (options["soundsNotPlayed"]?.Type == JTokenType.String)
            {
                string pattern = (string)options["soundsNotPlayed"];
                var seen = new List<string>();
                if (probe?["playing"] is JObject playing)
                    foreach (var p in playing.Properties()) if (p.Name.Contains(pattern)) seen.Add(p.Name);
                add("soundsNotPlayed", seen.Count == 0, seen.Count == 0 ? "no clip containing " + pattern + " played"
                    : "played: " + string.Join(", ", seen.ToArray()));
            }
        }
    }
}
