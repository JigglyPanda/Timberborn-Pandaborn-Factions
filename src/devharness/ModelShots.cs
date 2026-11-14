using System;
using System.IO;
using System.Linq;
using Bindito.Core;
using Newtonsoft.Json.Linq;
using Timberborn.BlockSystem;
using Timberborn.CameraSystem;
using Timberborn.ConstructionSites;
using Timberborn.EntitySystem;
using Timberborn.SingletonSystem;
using Timberborn.TemplateSystem;
using Timberborn.UILayoutSystem;
using UnityEngine;

namespace PandabornDevHarness
{
    [Context("Game")]
    public class ModelShotsConfigurator : Configurator
    {
        protected override void Configure()
        {
            if (!Harness.Active || !(Harness.Request?.Raw?["modelShots"] is JObject)) return;
            Bind<ModelShots>().AsSingleton();
        }
    }

    /// <summary>
    /// Close-ups of placed buildings, finished and under construction, for checking adopted models. Active only when
    /// request.json has a "modelShots" object:
    /// <code>
    /// "modelShots": { "afterGrid": true, "delaySeconds": 3,
    ///                 "stage": [ "PandabornDen.Inkpaws" ],           // unfinished copies (placed through "buildings" with
    ///                                                                // "finished": false) are started: a little build time
    ///                                                                // is added, so the construction-stage model shows
    ///                 "shots": [ { "template": "PandabornDen.Inkpaws", "finished": true, "name": "den",
    ///                              "yaw": 0, "pitch": 35, "zoom": 1 } ] }
    /// </code>
    /// Waits for the grid scenario to complete when "afterGrid" is set. Result under "modelShots": stage starts (build
    /// progress, whether construction was started) and the shots taken (files &lt;name&gt;.png in the output folder).
    /// </summary>
    public class ModelShots : ILoadableSingleton, IUpdatableSingleton
    {
        private readonly EventBus _eventBus;
        private readonly EntityRegistry _entityRegistry;
        private readonly CameraService _cameraService;
        private JObject _spec, _out;
        private float _readyAt = -1f, _nextAt;
        private int _step, _shotIndex;
        private bool _done;

        public ModelShots(EventBus eventBus, EntityRegistry entityRegistry, CameraService cameraService)
        {
            _eventBus = eventBus;
            _entityRegistry = entityRegistry;
            _cameraService = cameraService;
        }

        public void Load()
        {
            _spec = (JObject)Harness.Request.Raw["modelShots"];
            _out = new JObject { ["stage"] = new JObject(), ["shots"] = new JArray(), ["complete"] = false };
            Harness.Result["modelShots"] = _out;
            _eventBus.Register(this);
        }

        [OnEvent]
        public void OnShowPrimaryUI(ShowPrimaryUIEvent e)
        {
            if (_readyAt < 0f) _readyAt = Time.unscaledTime;
        }

        public void UpdateSingleton()
        {
            if (_done || Harness.Finished || _readyAt < 0f) return;
            float now = Time.unscaledTime;
            if (now < _readyAt + Request.Num(_spec, "delaySeconds", 3f) || now < _nextAt) return;
            if (Request.Bool(_spec, "afterGrid", false) && !((Harness.Result["grid"] as JObject)?["complete"]?.Value<bool>() ?? false)) return;
            try
            {
                if (_step == 0) { StartStages(); _step = 1; _nextAt = now + Request.Num(_spec, "stageWaitSeconds", 2f); return; }
                var shots = (_spec["shots"] as JArray) ?? new JArray();
                if (_shotIndex < shots.Count) { TakeShot((JObject)shots[_shotIndex++]); _nextAt = now + 0.3f; return; }
                RecordStages();
                _out["complete"] = true;
                _done = true;
                Harness.Info("model shots complete: " + shots.Count + " shot(s)");
            }
            catch (Exception ex)
            {
                Harness.Error("model shots failed", ex);
                _done = true;
            }
        }

        private EntityComponent Find(string template, bool? finished)
        {
            foreach (var entity in _entityRegistry.Entities)
            {
                if (!entity) continue;
                var ts = entity.GetComponent<TemplateSpec>();
                if (ts == null || ts.TemplateName != template) continue;
                var bo = entity.GetComponent<BlockObject>();
                if (finished.HasValue && bo != null && bo.IsFinished != finished.Value) continue;
                return entity;
            }
            return null;
        }

        private void StartStages()
        {
            var stage = (JObject)_out["stage"];
            foreach (var token in (_spec["stage"] as JArray) ?? new JArray())
            {
                var name = (string)token;
                var entry = new JObject();
                stage[name] = entry;
                var entity = Find(name, false);
                var site = entity ? entity.GetComponent<ConstructionSite>() : null;
                if (site == null) { entry["error"] = "no unfinished copy placed (add it to \"buildings\" with \"finished\": false)"; continue; }
                site.IncreaseBuildTime(Request.Num(_spec, "stageHours", 0.25f));
                entry["started"] = true;
            }
        }

        private void RecordStages()
        {
            foreach (var p in ((JObject)_out["stage"]).Properties())
            {
                var entry = (JObject)p.Value;
                var entity = Find(p.Name, null);
                var site = entity ? entity.GetComponent<ConstructionSite>() : null;
                if (site == null) continue;
                entry["wasStarted"] = site.WasStarted;
                entry["buildTimeProgress"] = Math.Round(site.BuildTimeProgress, 3);
                var bo = entity.GetComponent<BlockObject>();
                entry["finished"] = bo != null && bo.IsFinished;
            }
        }

        private void TakeShot(JObject shot)
        {
            var template = Request.Str(shot, "template", null);
            bool finished = Request.Bool(shot, "finished", true);
            var name = Request.Str(shot, "name", template + (finished ? "_finished" : "_stage"));
            var record = new JObject { ["name"] = name, ["template"] = template, ["finished"] = finished };
            ((JArray)_out["shots"]).Add(record);
            var entity = Find(template, finished);
            if (!entity) { record["error"] = "no " + (finished ? "finished" : "unfinished") + " " + template + " placed"; return; }
            var camera = _cameraService.Transform ? _cameraService.Transform.GetComponent<Camera>() : Camera.main;
            var file = Path.Combine(Harness.OutputDir, name + ".png");
            Capture.RenderFramed(camera, entity.GameObject, Request.Num(shot, "yaw", 0f), Request.Num(shot, "pitch", 35f),
                                 Request.Num(shot, "zoom", 1f), Harness.Request.ShotWidth, Harness.Request.ShotHeight, file);
            record["file"] = Path.GetFileName(file);
            Harness.RecordScreenshot(name, "building", file, new JObject { ["template"] = template, ["finished"] = finished }, null);
        }
    }
}
