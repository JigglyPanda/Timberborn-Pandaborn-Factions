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
using Timberborn.CameraSystem;
using Timberborn.Carrying;
using Timberborn.CharacterModelSystem;
using Timberborn.Characters;
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
    /// </summary>
    public class RingtailBodyProbe : ILoadableSingleton, IUpdatableSingleton
    {
        private static readonly string[] LineupOrder = { "InkpawAdult.Inkpaws", "RingtailAdult.Inkpaws", "RingtailChild.Inkpaws", "InkpawChild.Inkpaws" };
        private readonly EventBus _eventBus;
        private readonly IDayNightCycle _dayNightCycle;
        private readonly CharacterPopulation _characterPopulation;
        private readonly CameraService _cameraService;
        private readonly JObject _config;
        private readonly JObject _out = new JObject();
        private readonly JArray _taken = new JArray();
        private readonly List<JObject> _pending = new List<JObject>();
        private bool _primaryUi;
        private float _primaryUiAt;
        private float _startHours = -1f;
        private float _nextTry;

        public RingtailBodyProbe(EventBus eventBus, IDayNightCycle dayNightCycle, CharacterPopulation characterPopulation, CameraService cameraService)
        {
            _eventBus = eventBus;
            _dayNightCycle = dayNightCycle;
            _characterPopulation = characterPopulation;
            _cameraService = cameraService;
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
            if (!_primaryUi || _pending.Count == 0 || Time.unscaledTime < _nextTry) return;
            if (Time.unscaledTime - _primaryUiAt < (_config["startDelaySeconds"]?.Value<float>() ?? 25f)) return;
            if (_startHours < 0f) _startHours = Hours;
            _nextTry = Time.unscaledTime + 0.5f;
            float run = Hours - _startHours;
            for (int i = 0; i < _pending.Count; i++)
            {
                var s = _pending[i];
                float due = (s["day"]?.Value<float>() ?? 0f) * 24f + (s["hour"]?.Value<float>() ?? 0f);
                if (run < due) continue;
                bool night = s["night"]?.Value<bool>() ?? false;
                if (night && !_dayNightCycle.IsNighttime && run < due + 20f) continue;
                if (!night && (s["day_only"]?.Value<bool>() ?? false) && !_dayNightCycle.IsDaytime && run < due + 20f) continue;
                bool waitCarry = (string)s["prefer"] == "carrying" && run < due + (s["waitHours"]?.Value<float>() ?? 6f);
                if (waitCarry && !Ringtails().Any(IsCarrying)) continue;
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
            }
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
            var source = _cameraService.Transform ? _cameraService.Transform.GetComponent<Camera>() : Camera.main;
            if (kind == "lineup") Lineup(s, name, entry, source);
            else Game(s, name, entry, source, kind == "group");
            HarnessBridge.Info("shot " + name + " taken");
        }

        private void Lineup(JObject s, string name, JObject entry, Camera source)
        {
            var subjects = new List<Character>();
            foreach (var t in LineupOrder)
            {
                var c = Alive.Where(x => TemplateName(x) == t).OrderByDescending(IsCarrying).FirstOrDefault();
                if (c) subjects.Add(c);
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
                    float dist = (width * 0.5f + 0.25f) / Mathf.Tan(fov * 0.5f * Mathf.Deg2Rad);
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

        private void Game(JObject s, string name, JObject entry, Camera source, bool group)
        {
            var ringtail = Ringtails().OrderByDescending(IsCarrying).FirstOrDefault();
            if (!ringtail) { entry["error"] = "no visible Ringtail"; return; }
            entry["subject"] = Describe(ringtail);
            var model = ringtail.GetComponent<CharacterModel>().Model;
            var moved = new List<(Transform t, Vector3 p, Quaternion r)>();
            try
            {
                if (group)
                {
                    float heading0 = source ? source.transform.eulerAngles.y : 30f;
                    var right = Quaternion.Euler(0f, heading0, 0f) * Vector3.right;
                    var companions = new JArray();
                    var others = new[] { ("InkpawAdult.Inkpaws", -0.75f), ("RingtailChild.Inkpaws", 0.6f), ("InkpawChild.Inkpaws", 1.1f) };
                    foreach (var (template, offset) in others)
                    {
                        var c = Alive.FirstOrDefault(x => TemplateName(x) == template && x != ringtail);
                        if (!c) continue;
                        var m = c.GetComponent<CharacterModel>().Model;
                        moved.Add((m, m.position, m.rotation));
                        m.SetPositionAndRotation(model.position + right * offset, model.rotation);
                        companions.Add(Describe(c));
                    }
                    entry["companions"] = companions;
                }
                float heading = (source ? source.transform.eulerAngles.y : 30f) + (s["yaw"]?.Value<float>() ?? 0f);
                float pitch = s["pitch"]?.Value<float>() ?? 55f;
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
            _out["ringtails"] = new JArray(_characterPopulation.Characters.Where(c => c && (TemplateName(c) ?? "").StartsWith("Ringtail", StringComparison.Ordinal)).Select(Describe));
            _out["updatedUtc"] = DateTime.UtcNow.ToString("o", CultureInfo.InvariantCulture);
            File.WriteAllText(Path.Combine(dir, "ringtailBody.json"), _out.ToString(Formatting.Indented));
            var result = HarnessBridge.Result;
            if (result != null) result["ringtailBody"] = new JObject { ["file"] = "ringtailBody.json", ["shots"] = _taken.Count };
        }
    }
}
