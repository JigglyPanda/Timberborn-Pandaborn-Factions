using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using Bindito.Core;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Timberborn.BaseComponentSystem;
using Timberborn.Beavers;
using Timberborn.Bots;
using Timberborn.EntitySystem;
using Timberborn.WorkSystem;
using Timberborn.CameraSystem;
using Timberborn.Carrying;
using Timberborn.CharacterModelSystem;
using Timberborn.Characters;
using Timberborn.Goods;
using Timberborn.SingletonSystem;
using Timberborn.TemplateSystem;
using Timberborn.Timbermesh;
using Timberborn.TimeSystem;
using Timberborn.UILayoutSystem;
using UnityEngine;

namespace Pandaborn.RingtailBody
{
    [Context("Game")]
    public class RingtailBodyConfigurator : Configurator
    {
        protected override void Configure()
        {
            if (!HarnessBridge.Active || !(HarnessBridge.RawRequest?["ringtailBody"] is JObject)) return;
            Bind<RingtailBodyProbe>().AsSingleton();
        }
    }

    /// <summary>
    /// Dev only. Pictures of the Ringtail body inside a harness run (request key "ringtailBody"), written as rb_*.png and
    /// ringtailBody.json next to result.json. Shot kinds:
    ///  * "lineup": an Inkpaw adult, a Ringtail adult, a Ringtail kit and an Inkpaw cub lifted high above the map, side by
    ///    side, rendered front 3/4, back 3/4 and side (studio background, the scene's lighting); then put back;
    ///  * "game": a Ringtail (preferably one carrying goods) seen with the game camera's settings, heading, a given pitch and
    ///    distance (several distances per shot);
    ///  * "group": as "game", with an Inkpaw adult's model set down next to the Ringtail for the picture.
    /// Shots are due at "day"/"hour" (in-game hours since the probe started); "night": true also waits for night;
    /// "prefer": "carrying" waits up to "waitHours" for a Ringtail with goods in its hands or on its back.
    /// Subjects (pass 3): "subject": "ringtail" (default) | "bot" | "Template[:Showing]" picks the character for "game" and
    /// "group" shots (Showing = part of the name of an attachment that must be shown, e.g. "ConicalHat"); "companions":
    /// [specs] set down next to it in "group" shots; "lineup": [specs] chooses the lineup. Set-up keys: "spawnBots": n
    /// (bots made by the game's BotFactory where an Inkpaw stands), "botWork": [workplace templates] (unlocked for bots
    /// ignoring cost and switched to the Bot worker type).
    /// </summary>
    public class RingtailBodyProbe : ILoadableSingleton, IUpdatableSingleton
    {
        private static readonly string[] LineupOrder = { "InkpawAdult.Inkpaws", "RingtailAdult.Inkpaws", "RingtailChild.Inkpaws", "InkpawChild.Inkpaws" };
        private readonly EventBus _eventBus;
        private readonly IDayNightCycle _dayNightCycle;
        private readonly CharacterPopulation _characterPopulation;
        private readonly CameraService _cameraService;
        private readonly Timberborn.SelectionSystem.EntitySelectionService _entitySelectionService;
        private readonly BotFactory _botFactory;
        private readonly EntityRegistry _entityRegistry;
        private readonly WorkplaceUnlockingService _workplaceUnlockingService;
        private bool _setUp;
        private readonly JObject _config;
        private readonly JObject _out = new JObject();
        private readonly JArray _taken = new JArray();
        private readonly List<JObject> _pending = new List<JObject>();
        private bool _primaryUi;
        private float _primaryUiAt;
        private float _startHours = -1f;
        private float _nextTry;

        public RingtailBodyProbe(EventBus eventBus, IDayNightCycle dayNightCycle, CharacterPopulation characterPopulation, CameraService cameraService,
                                 Timberborn.SelectionSystem.EntitySelectionService entitySelectionService, BotFactory botFactory,
                                 EntityRegistry entityRegistry, WorkplaceUnlockingService workplaceUnlockingService)
        {
            _botFactory = botFactory;
            _entityRegistry = entityRegistry;
            _workplaceUnlockingService = workplaceUnlockingService;
            _eventBus = eventBus;
            _dayNightCycle = dayNightCycle;
            _characterPopulation = characterPopulation;
            _cameraService = cameraService;
            _entitySelectionService = entitySelectionService;
            _config = HarnessBridge.Config;
        }

        public void Load()
        {
            _eventBus.Register(this);
            if (_config["shots"] is JArray shots)
                foreach (var s in shots.OfType<JObject>()) _pending.Add(s);
            _out["config"] = _config.DeepClone();
            HarnessBridge.Info("probe loaded, " + _pending.Count + " shot(s) requested");
        }

        [OnEvent]
        public void OnShowPrimaryUI(ShowPrimaryUIEvent e)
        {
            _primaryUi = true;
            _primaryUiAt = Time.unscaledTime;
        }

        private float Hours => _dayNightCycle.PartialDayNumber * 24f;

        public void UpdateSingleton()
        {
            if (_forced != null && Time.unscaledTime >= _forcedAt) { FinishForced(); return; }
            if (_forced != null) return;
            if (!_primaryUi || _pending.Count == 0 || Time.unscaledTime < _nextTry) return;
            if (Time.unscaledTime - _primaryUiAt < (_config["startDelaySeconds"]?.Value<float>() ?? 25f)) return;
            if (_startHours < 0f) _startHours = Hours;
            if (!_setUp)
            {
                _setUp = true;
                try { SetUp(); }
                catch (Exception e) { Debug.LogError("[Pandaborn.RingtailBody] set-up failed: " + e); _out["setUpError"] = e.Message; }
            }
            _nextTry = Time.unscaledTime + 0.5f;
            TrackMovement();
            float run = Hours - _startHours;
            for (int i = 0; i < _pending.Count; i++)
            {
                var s = _pending[i];
                float due = (s["day"]?.Value<float>() ?? 0f) * 24f + (s["hour"]?.Value<float>() ?? 0f);
                if (run < due) continue;
                if (s["window"] is JArray window && window.Count == 2)
                {
                    // [from, to] hours after dawn: wait for the window; inside it, wait for a carrying Ringtail until
                    // 0.5 h before its end, then take the picture anyway
                    float h = _dayNightCycle.HoursPassedToday, from = window[0].Value<float>(), to = window[1].Value<float>();
                    if (h < from || h >= to) continue;
                    if ((string)s["prefer"] == "carrying" && h < to - 0.5f && !Candidates(s).Any(IsCarrying)) continue;
                    _pending.RemoveAt(i);
                    try { Take(s); }
                    catch (Exception e)
                    {
                        Debug.LogError("[Pandaborn.RingtailBody] shot " + s["name"] + " failed: " + e);
                        _taken.Add(new JObject { ["name"] = s["name"], ["error"] = e.GetType().Name + ": " + e.Message });
                    }
                    Write();
                    return;
                }
                bool night = s["night"]?.Value<bool>() ?? false;
                if (night && !_dayNightCycle.IsNighttime && run < due + 20f) continue;
                if (!night && (s["day_only"]?.Value<bool>() ?? false) && !_dayNightCycle.IsDaytime && run < due + 20f) continue;
                bool waitCarry = (string)s["prefer"] == "carrying" && run < due + (s["waitHours"]?.Value<float>() ?? 6f);
                if (waitCarry && !Candidates(s).Any(IsCarrying)) continue;
                _pending.RemoveAt(i);
                try { Take(s); }
                catch (Exception e)
                {
                    Debug.LogError("[Pandaborn.RingtailBody] shot " + s["name"] + " failed: " + e);
                    _taken.Add(new JObject { ["name"] = s["name"], ["error"] = e.GetType().Name + ": " + e.Message });
                }
                Write();
                return;   // one shot per update
            }
        }

        // ------------------------------------------------------------------ subjects

        private readonly Dictionary<Character, Vector3> _lastPos = new Dictionary<Character, Vector3>();
        private readonly HashSet<Character> _moving = new HashSet<Character>();
        private Character _forced;
        private JObject _forcedShot, _forcedEntry;
        private float _forcedAt;

        private void TrackMovement()
        {
            foreach (var c in Alive.ToList())
            {
                var p = c.GetComponent<CharacterModel>().Model.position;
                if (_lastPos.TryGetValue(c, out var q) && (p - q).sqrMagnitude > 0.0025f) _moving.Add(c); else _moving.Remove(c);
                _lastPos[c] = p;
            }
        }

        /// <summary>True when nothing but the subject itself is between a camera at the given pose and the subject.</summary>
        private static bool Unoccluded(Character c, float pitch, float heading, float dist)
        {
            var focus = c.GetComponent<CharacterModel>().Model.position + new Vector3(0f, 0.2f, 0f);
            var rotation = Quaternion.Euler(pitch, heading, 0f);
            var from = focus - rotation * Vector3.forward * dist;
            if (!Physics.Raycast(from, focus - from, out var hit, dist - 0.35f)) return true;
            var hitCharacter = hit.collider ? hit.collider.GetComponentInParent<Character>() : null;
            return hitCharacter == c;
        }

        // ------------------------------------------------------------------ set-up and subject specs

        private void SetUp()
        {
            var log = new JObject();
            int bots = _config["spawnBots"]?.Value<int>() ?? 0;
            var anchor = Alive.FirstOrDefault(c => TemplateName(c) == "InkpawAdult.Inkpaws") ?? Alive.FirstOrDefault();
            for (int i = 0; i < bots && anchor; i++)
                _botFactory.Create(anchor.GetComponent<CharacterModel>().Model.position + new Vector3(0.3f * i, 0f, 0f));
            log["spawnedBots"] = anchor ? bots : 0;
            if (_config["botWork"] is JArray work)
            {
                var done = new JArray();
                foreach (var t in work.Values<string>())
                    foreach (var e in _entityRegistry.Entities.Where(x => TemplateName(x) == t))
                    {
                        var wt = e.GetComponent<WorkplaceWorkerType>();
                        if (wt == null) continue;
                        _workplaceUnlockingService.UnlockIgnoringCost(new UnlockableWorkerType(t, "Bot"));
                        wt.SetWorkerType("Bot");
                        done.Add(t + " -> " + wt.WorkerType);
                    }
                log["botWork"] = done;
            }
            _out["setUp"] = log;
            HarnessBridge.Info("set-up: " + log.ToString(Formatting.None));
        }

        /// <summary>"Template[:Showing]" (or "ringtail" / "bot"): the living, visible characters it matches.</summary>
        private IEnumerable<Character> Matching(string spec)
        {
            if (string.IsNullOrEmpty(spec) || spec == "ringtail") return Ringtails();
            if (spec == "bot") return Alive.Where(c => c.GetComponent<Bot>() != null);
            int k = spec.IndexOf(':');
            string template = k < 0 ? spec : spec.Substring(0, k), showing = k < 0 ? null : spec.Substring(k + 1);
            return Alive.Where(c => TemplateName(c) == template && (showing == null || Shows(c, showing)));
        }

        private IEnumerable<Character> Candidates(JObject s) => Matching((string)s["subject"]);

        private static bool Shows(Character c, string part) =>
            c.GameObject.GetComponentsInChildren<Renderer>(false).Any(r => r.enabled && r.name.IndexOf(part, StringComparison.OrdinalIgnoreCase) >= 0);

        private static readonly string[] AttachmentWords = { "Hat", "Basket", "Backpack", "Hammer" };

        private static JArray ShownAttachments(Character c) => new JArray(c.GameObject.GetComponentsInChildren<Renderer>(false)
            .Where(r => r.enabled).Select(r => r.name)
            .Where(n => AttachmentWords.Any(w => n.IndexOf(w, StringComparison.OrdinalIgnoreCase) >= 0)).Distinct());

        private Character PickRingtail(JObject s, Camera source)
        {
            float heading = (source ? source.transform.eulerAngles.y : 30f) + (s["yaw"]?.Value<float>() ?? 0f);
            float pitch = s["pitch"]?.Value<float>() ?? 55f;
            return Candidates(s).OrderByDescending(IsCarrying)
                .ThenByDescending(c => Enumerable.Range(0, 8).Any(k => Unoccluded(c, pitch, heading + 45f * k, 4f)))
                .ThenByDescending(c => _moving.Contains(c)).FirstOrDefault();
        }

        private void FinishForced()
        {
            var c = _forced; var s = _forcedShot; var entry = _forcedEntry;
            _forced = null;
            try
            {
                var source = _cameraService.Transform ? _cameraService.Transform.GetComponent<Camera>() : Camera.main;
                Game(s, (string)s["name"], entry, source, (string)s["kind"] == "group", c);
            }
            catch (Exception e)
            {
                Debug.LogError("[Pandaborn.RingtailBody] forced shot failed: " + e);
                entry["error"] = e.GetType().Name + ": " + e.Message;
            }
            finally
            {
                var carrier = c ? c.GetComponent<GoodCarrier>() : null;
                if (carrier != null && carrier.IsCarrying && carrier.CarriedGoodId == ((string)s["good"] ?? "Log")) carrier.EmptyHands();
                Write();
            }
        }

        private static string TemplateName(BaseComponent c) => c.GetComponent<TemplateSpec>()?.TemplateName;

        private IEnumerable<Character> Alive => _characterPopulation.Characters.Where(c => c && c.Alive && Visible(c));

        private IEnumerable<Character> Ringtails() => Alive.Where(c => TemplateName(c) == "RingtailAdult.Inkpaws");

        private static bool IsCarrying(Character c) => c.GetComponent<GoodCarrier>()?.IsCarrying == true;

        private static Renderer Body(Character c) => c.GameObject.GetComponentInChildren<Renderer>(true);

        private static bool Visible(Character c)
        {
            var body = Body(c);
            var model = c.GetComponent<CharacterModel>();
            return body && body.enabled && body.gameObject.activeInHierarchy && model != null && model.Model;
        }

        private static JObject Describe(Character c)
        {
            var o = new JObject { ["template"] = TemplateName(c), ["name"] = c.FirstName };
            var body = Body(c);
            if (body)
            {
                var filter = body.GetComponent<MeshFilter>();
                var mesh = filter ? filter.sharedMesh : null;
                o["mesh"] = mesh ? mesh.name : null;
                o["vertices"] = mesh ? mesh.vertexCount : 0;
                var description = body.GetComponentInParent<TimbermeshDescription>(true);
                o["modelAsset"] = description ? description.ModelName : null;
                var m = body.sharedMaterial;
                var tex = m && m.HasProperty("_BaseMap") ? m.GetTexture("_BaseMap") : null;
                o["material"] = m ? m.name : null;
                o["coat"] = tex ? tex.name : null;
                o["boundsHeight"] = Math.Round(body.bounds.size.y, 3);
                if (mesh && mesh.isReadable)
                {
                    // tells two builds of one mesh apart (same vertex count): the sum of all u coordinates
                    double sum = 0; foreach (var uv in mesh.uv) sum += uv.x;
                    o["uvSum"] = Math.Round(sum, 3);
                }
            }
            o["attachments"] = ShownAttachments(c);
            // every material drawn on the character (the Reskin's fur shells show up here, with the fur mask in use)
            o["materials"] = new JArray(c.GameObject.GetComponentsInChildren<Renderer>(false).Where(r => r.enabled)
                .SelectMany(r => r.sharedMaterials).Where(m => m).Select(m => m.name).Distinct());
            var fur = c.GameObject.GetComponentsInChildren<MonoBehaviour>(true)
                .Where(m => m && m.GetType().Name.IndexOf("Fur", StringComparison.OrdinalIgnoreCase) >= 0).ToList();
            o["components"] = new JArray(fur.Select(m => m.GetType().Name).Distinct());
            // the materials a fur component holds (by reflection, dev only): shows which fur mask a body got
            o["furMaterials"] = new JArray(fur.SelectMany(m => m.GetType().GetFields(System.Reflection.BindingFlags.Instance
                    | System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Public)
                .Where(f => typeof(Material).IsAssignableFrom(f.FieldType)).Select(f => f.GetValue(m) as Material))
                .Where(x => x).Select(x => x.name + (x.HasProperty("_FurMask") && x.GetTexture("_FurMask") ? " [mask " + x.GetTexture("_FurMask").name + "]" : "")).Distinct());
            var carrier = c.GetComponent<GoodCarrier>();
            if (carrier != null && carrier.IsCarrying) o["carrying"] = carrier.CarriedGoodId + " x" + carrier.CarriedGood.GoodAmount.Amount;
            var child = c.GetComponent<Child>();
            if (child != null) o["growth"] = Math.Round(child.GrowthProgress, 3);
            return o;
        }

        // ------------------------------------------------------------------ shots

        private void Take(JObject s)
        {
            string name = (string)s["name"] ?? "shot";
            string kind = (string)s["kind"] ?? "game";
            var entry = new JObject
            {
                ["name"] = name, ["kind"] = kind, ["runHours"] = Math.Round(Hours - _startHours, 2),
                ["hourOfDay"] = Math.Round(_dayNightCycle.HoursPassedToday, 2), ["daytime"] = _dayNightCycle.IsDaytime
            };
            _taken.Add(entry);
            try { _entitySelectionService.Unselect(); } catch (Exception) { }   // no selection tint in the pictures
            var source = _cameraService.Transform ? _cameraService.Transform.GetComponent<Camera>() : Camera.main;
            if (kind == "lineup") { Lineup(s, name, entry, source); HarnessBridge.Info("shot " + name + " taken"); return; }
            var ringtail = PickRingtail(s, source);
            if (ringtail && (s["force"]?.Value<bool>() ?? false) && !IsCarrying(ringtail))
            {
                // dev only: no Ringtail had goods during the window; hand one a good for the picture, take it back after
                string good = (string)s["good"] ?? "Log";
                ringtail.GetComponent<GoodCarrier>().PutGoodsInHands(new CarriedGood(new GoodAmount(good, 1), CarriedGoodType.Uncountable));
                entry["forcedCarry"] = good;
                _forced = ringtail; _forcedShot = s; _forcedEntry = entry;
                _forcedAt = Time.unscaledTime + (s["forceSeconds"]?.Value<float>() ?? 1.2f);
                return;
            }
            Game(s, name, entry, source, kind == "group", ringtail);
            HarnessBridge.Info("shot " + name + " taken");
        }

        private void Lineup(JObject s, string name, JObject entry, Camera source)
        {
            var subjects = new List<Character>();
            var order = s["lineup"] is JArray specs ? specs.Values<string>().ToArray() : LineupOrder;
            foreach (var t in order)
            {
                var c = Matching(t).Where(x => !subjects.Contains(x)).OrderByDescending(IsCarrying).FirstOrDefault();
                if (c) subjects.Add(c);
                else entry["missing"] = (entry["missing"]?.ToString() ?? "") + t + " ";
            }
            entry["subjects"] = new JArray(subjects.Select(Describe));
            if (subjects.Count == 0) { entry["error"] = "no subjects"; return; }
            var models = subjects.Select(c => c.GetComponent<CharacterModel>().Model).ToList();
            var saved = models.Select(m => (m.position, m.rotation)).ToList();
            float spacing = s["spacing"]?.Value<float>() ?? 0.62f;
            var basePos = models[0].position + new Vector3(0f, 80f, 0f);
            var facing = Quaternion.Euler(0f, s["facing"]?.Value<float>() ?? 0f, 0f);
            try
            {
                for (int i = 0; i < models.Count; i++)
                    models[i].SetPositionAndRotation(basePos + facing * new Vector3((i - (models.Count - 1) / 2f) * spacing, 0f, 0f), facing);
                var focus = basePos + new Vector3(0f, 0.24f, 0f);
                float width = models.Count * spacing;
                var views = new[] { ("front", new Vector3(0.30f, 0.22f, 1f)), ("back", new Vector3(-0.30f, 0.40f, -1f)), ("side", new Vector3(1f, 0.18f, 0.12f)), ("top", new Vector3(0.25f, 1.2f, 0.9f)) };
                var files = new JArray();
                foreach (var (view, dir) in views)
                {
                    float fov = 22f;
                    int w = s["width"]?.Value<int>() ?? 1600, h = s["height"]?.Value<int>() ?? 760;
                    float halfH = Mathf.Atan(Mathf.Tan(fov * 0.5f * Mathf.Deg2Rad) * w / h);   // horizontal half-angle
                    float dist = (width * 0.5f + 0.15f) / Mathf.Tan(halfH);
                    var position = focus + facing * dir.normalized * dist;
                    var rotation = Quaternion.LookRotation(focus - position, Vector3.up);
                    string file = Path.Combine(HarnessBridge.OutputDir, "rb_" + name + "_" + view + ".png");
                    Render(source, s["width"]?.Value<int>() ?? 1600, s["height"]?.Value<int>() ?? 760, position, rotation, fov, new Color(0.36f, 0.42f, 0.5f, 1f), file);
                    files.Add(Path.GetFileName(file));
                }
                entry["files"] = files;
            }
            finally
            {
                for (int i = 0; i < models.Count; i++) models[i].SetPositionAndRotation(saved[i].position, saved[i].rotation);
            }
        }

        private void Game(JObject s, string name, JObject entry, Camera source, bool group, Character ringtail)
        {
            entry["moving"] = ringtail && _moving.Contains(ringtail);
            if (!ringtail) { entry["error"] = "no visible subject " + ((string)s["subject"] ?? "ringtail"); return; }
            entry["subject"] = Describe(ringtail);
            var model = ringtail.GetComponent<CharacterModel>().Model;
            var moved = new List<(Transform t, Vector3 p, Quaternion r)>();
            try
            {
                // the game camera's heading if the Ringtail can be seen from there, else the first of 7 other headings
                // (45 degree steps) with nothing in the way at the closest distance
                float pitch = s["pitch"]?.Value<float>() ?? 55f;
                float baseHeading = (source ? source.transform.eulerAngles.y : 30f) + (s["yaw"]?.Value<float>() ?? 0f);
                float near = s["distances"] is JArray dd && dd.Count > 0 ? dd[0].Value<float>() : 5f;
                float heading = baseHeading;
                for (int k = 0; k < 8; k++)
                {
                    float h = baseHeading + 45f * k;
                    if (Unoccluded(ringtail, pitch, h, near)) { heading = h; entry["headingSearch"] = k; break; }
                }
                if (group)
                {
                    float heading0 = heading;
                    var right = Quaternion.Euler(0f, heading0, 0f) * Vector3.right;
                    var companions = new JArray();
                    var others = s["companions"] is JArray cs
                        ? cs.Values<string>().Select((t, i) => (t, (i % 2 == 0 ? -1f : 1f) * (0.65f + 0.55f * (i / 2)))).ToArray()
                        : new[] { ("InkpawAdult.Inkpaws", -0.75f), ("RingtailChild.Inkpaws", 0.6f), ("InkpawChild.Inkpaws", 1.1f) };
                    var used = new HashSet<Character> { ringtail };
                    foreach (var (template, offset) in others)
                    {
                        var c = Matching(template).FirstOrDefault(x => !used.Contains(x));
                        if (c) used.Add(c);
                        if (!c) continue;
                        var m = c.GetComponent<CharacterModel>().Model;
                        moved.Add((m, m.position, m.rotation));
                        m.SetPositionAndRotation(model.position + right * offset, model.rotation);
                        companions.Add(Describe(c));
                    }
                    entry["companions"] = companions;
                }
                var distances = s["distances"] is JArray d ? d.Select(x => x.Value<float>()).ToArray() : new[] { 5f, 11f };
                var files = new JArray();
                foreach (float dist in distances)
                {
                    var rotation = Quaternion.Euler(pitch, heading, 0f);
                    var focus = model.position + new Vector3(0f, 0.2f, 0f);
                    var position = focus - rotation * Vector3.forward * dist;
                    string file = Path.Combine(HarnessBridge.OutputDir, "rb_" + name + "_d" + dist.ToString("0.#", CultureInfo.InvariantCulture) + ".png");
                    Render(source, s["width"]?.Value<int>() ?? 1280, s["height"]?.Value<int>() ?? 720, position, rotation, null, null, file);
                    files.Add(Path.GetFileName(file));
                }
                entry["files"] = files;
                entry["pitch"] = pitch;
                entry["heading"] = Math.Round(heading, 1);
            }
            finally
            {
                foreach (var (t, p, r) in moved) t.SetPositionAndRotation(p, r);
            }
        }

        private static void Render(Camera source, int width, int height, Vector3 position, Quaternion rotation, float? fov, Color? background, string path)
        {
            var go = new GameObject("PandabornRingtailBodyCamera");
            var camera = go.AddComponent<Camera>();
            camera.enabled = false;
            if (source) camera.CopyFrom(source);
            camera.transform.SetPositionAndRotation(position, rotation);
            if (fov.HasValue) camera.fieldOfView = fov.Value;
            if (background.HasValue)
            {
                camera.clearFlags = CameraClearFlags.SolidColor;
                camera.backgroundColor = background.Value;
            }
            camera.nearClipPlane = 0.05f;
            camera.farClipPlane = 400f;
            camera.ResetProjectionMatrix();
            camera.aspect = width / (float)height;
            var target = RenderTexture.GetTemporary(width, height, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
            var texture = new Texture2D(width, height, TextureFormat.RGBA32, false);
            var previous = RenderTexture.active;
            try
            {
                camera.targetTexture = target;
                camera.Render();
                RenderTexture.active = target;
                texture.ReadPixels(new Rect(0, 0, width, height), 0, 0);
                texture.Apply(false);
                Directory.CreateDirectory(Path.GetDirectoryName(path));
                File.WriteAllBytes(path, ImageConversion.EncodeToPNG(texture));
            }
            finally
            {
                RenderTexture.active = previous;
                camera.targetTexture = null;
                RenderTexture.ReleaseTemporary(target);
                UnityEngine.Object.Destroy(go);
                UnityEngine.Object.Destroy(texture);
            }
        }

        private void Write()
        {
            string dir = HarnessBridge.OutputDir;
            if (dir == null) return;
            _out["shots"] = _taken;
            _out["pending"] = new JArray(_pending.Select(p => p["name"]));
            _out["population"] = new JArray(_characterPopulation.Characters.Where(c => c).GroupBy(TemplateName)
                .Select(g => new JObject { ["template"] = g.Key, ["count"] = g.Count() }));
            _out["bots"] = new JArray(_characterPopulation.Characters.Where(c => c && c.GetComponent<Bot>() != null).Select(Describe));
            _out["ringtails"] = new JArray(_characterPopulation.Characters.Where(c => c && (TemplateName(c) ?? "").StartsWith("Ringtail", StringComparison.Ordinal)).Select(Describe));
            _out["updatedUtc"] = DateTime.UtcNow.ToString("o", CultureInfo.InvariantCulture);
            File.WriteAllText(Path.Combine(dir, "ringtailBody.json"), _out.ToString(Formatting.Indented));
            var result = HarnessBridge.Result;
            if (result != null) result["ringtailBody"] = new JObject { ["file"] = "ringtailBody.json", ["shots"] = _taken.Count };
        }
    }
}
