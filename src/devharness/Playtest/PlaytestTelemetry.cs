using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using Newtonsoft.Json.Linq;
using Timberborn.BehaviorSystem;
using Timberborn.BlockSystem;
using Timberborn.Characters;
using Timberborn.CharactersGame;
using Timberborn.ConstructionSites;
using Timberborn.Coordinates;
using Timberborn.DwellingSystem;
using Timberborn.EntitySystem;
using Timberborn.Forestry;
using Timberborn.GoodsSampling;
using Timberborn.Growing;
using Timberborn.MortalSystem;
using Timberborn.NaturalResourcesLifecycle;
using Timberborn.NeedSystem;
using Timberborn.SingletonSystem;
using Timberborn.StatusSystem;
using Timberborn.TemplateSystem;
using Timberborn.Wellbeing;
using Timberborn.WorkSystem;
using UnityEngine;

namespace PandabornDevHarness
{
    /// <summary>
    /// Daily telemetry of the scripted colony, one JSON line per dawn in playtest\daily.jsonl (after the game's own goods
    /// sampling, so production and consumption are the day that just ended), plus overview shots.
    /// </summary>
    public partial class PlaytestDriver
    {
        private float _sampleEvery, _nextSample, _lastDayReal;
        private int _shotsEvery, _shotW = 1280, _shotH = 720, _births, _grownUp, _lastScience, _lastShotKey = -1;
        private readonly JArray _deaths = new JArray();
        private readonly HashSet<Character> _known = new HashSet<Character>();
        private readonly List<Workplace> _workplaces = new List<Workplace>();
        private readonly List<Dwelling> _dwellings = new List<Dwelling>();
        private float _workplacesAt = -1e9f;
        private readonly Dictionary<Workplace, WorkSample> _work = new Dictionary<Workplace, WorkSample>();
        private int _daysRecorded;
        private static readonly FieldInfo DeathMessageField = typeof(Mortal).GetField("_deathMessage", BindingFlags.Instance | BindingFlags.NonPublic);

        private class WorkSample
        {
            public string Label;
            public int Samples, WorkerSamples, Understaffed;
            public readonly Dictionary<string, int> Behaviors = new Dictionary<string, int>();
            public readonly Dictionary<string, int> Statuses = new Dictionary<string, int>();
        }

        private void LoadTelemetry()
        {
            _sampleEvery = Mathf.Max(0.1f, Request.Num(_spec, "sampleEveryHours", 0.5f));
            _shotsEvery = (int)Request.Num(_spec, "shotsEveryDays", 3f);
            if (_spec["shotSize"] is JArray size && size.Count >= 2) { _shotW = (int)size[0]; _shotH = (int)size[1]; }
        }

        private void BeginTelemetry()
        {
            foreach (var c in _characterPopulation.Characters) if (c) _known.Add(c);
            _lastScience = _scienceService.SciencePoints;
            _lastDayReal = Time.unscaledTime;
            _nextSample = Hours();
            try { WriteDaily(false); }   // day-0 baseline
            catch (Exception e) { Harness.Error("playtest: first telemetry failed", e); }
        }

        private void EndTelemetry()
        {
            WriteDaily(true);
        }

        [OnEvent]
        public void OnGoodsSampled(GoodsSampledEvent e)
        {
            if (!_started || _ended) return;
            try { WriteDaily(false); }
            catch (Exception ex) { Harness.Error("playtest: daily telemetry failed", ex); }
        }

        [OnEvent]
        public void OnBirth(CharacterBirthEvent e)
        {
            if (_started) _births++;
        }

        [OnEvent]
        public void OnCharacterCreated(CharacterCreatedEvent e)
        {
            if (!_started || e.Character == null) return;
            if (_known.Add(e.Character) && e.Character.GetComponent<Timberborn.Beavers.Child>() == null
                && e.Character.GetComponent<Timberborn.Bots.Bot>() == null) _grownUp++;
        }

        [OnEvent]
        public void OnDied(PreMortalDiedEvent e)
        {
            if (!_started) return;
            try
            {
                var mortal = e.Mortal;
                var character = mortal.GetComponent<Character>();
                var needs = mortal.GetComponent<NeedManager>();
                var atMinimum = new JArray();
                if (needs != null)
                    foreach (var spec in needs.NeedSpecs)
                        if (needs.NeedIsActive(spec.Id) && needs.NeedIsAtMinimumPoints(spec.Id)) atMinimum.Add(spec.Id);
                var death = new JObject
                {
                    ["day"] = Math.Round(Day(), 2),
                    ["name"] = character?.FirstName,
                    ["age"] = character?.Age,
                    ["kind"] = character != null ? Kind(character) : "?",
                    ["template"] = mortal.GetComponent<TemplateSpec>()?.TemplateName,
                    ["message"] = DeathMessageField?.GetValue(mortal) as string,
                    ["needsAtMinimum"] = atMinimum
                };
                _deaths.Add(death);
                AppendLine("events.jsonl", new JObject { ["day"] = death["day"], ["type"] = "death", ["death"] = death });
            }
            catch (Exception ex) { Harness.Warn("playtest: recording a death failed: " + ex.Message); }
        }

        private static string Kind(Character c)
        {
            if (c.GetComponent<Timberborn.Bots.Bot>() != null) return "bot";
            return c.GetComponent<Timberborn.Beavers.Child>() != null ? "child" : "adult";
        }

        private void UpdateTelemetry(float now)
        {
            if (now >= _nextSample)
            {
                _nextSample = now + _sampleEvery;
                SampleWork(now);
            }
            if (_shotsEvery > 0)
            {
                int day = _dayNightCycle.DayNumber;
                float hour = _dayNightCycle.HoursPassedToday;
                if (day % _shotsEvery == 0)
                {
                    int key = -1;
                    if (hour >= 1f && hour < 3f) key = day * 2;
                    else if (hour >= 21f) key = day * 2 + 1;
                    if (key >= 0 && key != _lastShotKey)
                    {
                        _lastShotKey = key;
                        Shot("day" + day.ToString("00") + (key % 2 == 0 ? "_dawn" : "_night"));
                    }
                }
            }
        }

        private void Shot(string name)
        {
            try
            {
                var camera = _cameraService.Transform ? _cameraService.Transform.GetComponent<Camera>() : Camera.main;
                if (!camera) return;
                // centre on the colony: the district center and every building placed so far
                var points = _placed.Values.Where(p => p.Bo).Select(p => p.Bo.Coordinates).ToList();
                var dc = Anchor("dc");
                if (dc.HasValue) points.Add(dc.Value);
                if (points.Count > 0)
                {
                    var mean = new Vector3((float)points.Average(p => p.x), (float)points.Average(p => p.y), (float)points.Average(p => p.z));
                    _cameraService.MoveTargetTo(CoordinateSystem.GridToWorld(mean));
                }
                string file = Path.Combine(_dir, name + ".png");
                Capture.RenderView(camera, _shotW, _shotH, file);
                Harness.RecordScreenshot("playtest_" + name, "overview", Path.Combine("playtest", name + ".png"),
                                         new JObject { ["inGameDay"] = Math.Round(Day(), 2) }, null);
            }
            catch (Exception e) { Harness.Warn("playtest: shot " + name + " failed: " + e.Message); }
        }

        // ------------------------------------------------------------------ workplace activity

        private void RefreshWorkplaces(float now)
        {
            if (now - _workplacesAt < 6f) return;
            _workplacesAt = now;
            _workplaces.Clear();
            _dwellings.Clear();
            foreach (var entity in _entityRegistry.Entities)
            {
                if (!entity) continue;
                var w = entity.GetComponent<Workplace>();
                if (w != null) _workplaces.Add(w);
                var d = entity.GetComponent<Dwelling>();
                if (d != null) _dwellings.Add(d);
            }
        }

        private string Label(Workplace w)
        {
            var bo = w.GetComponent<BlockObject>();
            foreach (var p in _placed.Values) if (p.Bo == bo) return p.Id;
            string t = w.GetComponent<TemplateSpec>()?.TemplateName ?? "?";
            return bo != null ? t + "@" + bo.Coordinates.x + "," + bo.Coordinates.y : t;
        }

        private void SampleWork(float now)
        {
            RefreshWorkplaces(now);
            if (!_workingHoursManager.AreWorkingHours) return;
            foreach (var w in _workplaces)
            {
                if (!w) continue;
                var bo = w.GetComponent<BlockObject>();
                if (bo == null || !bo.IsFinished) continue;
                if (!_work.TryGetValue(w, out var s)) _work[w] = s = new WorkSample { Label = Label(w) };
                s.Samples++;
                if (w.NumberOfAssignedWorkers < w.DesiredWorkers) s.Understaffed++;
                foreach (var worker in w.AssignedWorkers)
                {
                    if (!worker) continue;
                    var bm = worker.GetComponent<BehaviorManager>();
                    string name = bm != null ? bm.RunningBehavior.Name ?? "none" : "none";
                    s.WorkerSamples++;
                    s.Behaviors.TryGetValue(name, out int n);
                    s.Behaviors[name] = n + 1;
                }
                var status = w.GetComponent<StatusSubject>();
                if (status != null)
                    foreach (var st in status.ActiveStatuses)
                        if (st != null && st.IsActive && !string.IsNullOrEmpty(st.StatusDescription))
                        {
                            s.Statuses.TryGetValue(st.StatusDescription, out int m);
                            s.Statuses[st.StatusDescription] = m + 1;
                        }
            }
        }

        // ------------------------------------------------------------------ daily record

        private void WriteDaily(bool final)
        {
            float day = Day();
            var o = new JObject
            {
                ["day"] = _dayNightCycle.DayNumber,
                ["t"] = Math.Round(day, 3),
                ["final"] = final,
                ["cycle"] = _gameCycleService.Cycle,
                ["cycleDay"] = _gameCycleService.CycleDay,
                ["weather"] = WeatherName(),
                ["temperateDays"] = _weatherService.TemperateWeatherDuration,
                ["hazardDays"] = _weatherService.HazardousWeatherDuration,
                ["hazardKind"] = _hazardousWeatherService.CurrentCycleHazardousWeather?.GetType().Name,
                ["workingHours"] = WorkingHours(),
                ["speed"] = _speedManager.CurrentSpeed,
                ["realSeconds"] = Math.Round(Time.unscaledTime - _startReal, 1),
                ["realSecondsThisDay"] = Math.Round(Time.unscaledTime - _lastDayReal, 1),
                ["science"] = _scienceService.SciencePoints
            };
            _lastDayReal = Time.unscaledTime;

            // population, needs, wellbeing, jobs, homes
            int adults = 0, children = 0, bots = 0, employed = 0, unemployed = 0, homeless = 0;
            var wb = new List<int>();
            var needSum = new Dictionary<string, float>();
            var needN = new Dictionary<string, int>();
            var needCrit = new Dictionary<string, int>();
            var needLow = new Dictionary<string, int>();
            foreach (var c in _characterPopulation.Characters)
            {
                if (!c) continue;
                string kind = Kind(c);
                if (kind == "bot") { bots++; continue; }
                if (kind == "child") children++; else adults++;
                var worker = c.GetComponent<Worker>();
                if (kind == "adult" && worker != null) { if (worker.Workplace) employed++; else unemployed++; }
                var dweller = c.GetComponent<Dweller>();
                if (dweller != null && !dweller.HasHome) homeless++;
                var tracker = c.GetComponent<WellbeingTracker>();
                if (tracker != null) wb.Add(tracker.Wellbeing);
                var needs = c.GetComponent<NeedManager>();
                if (needs == null) continue;
                foreach (var spec in needs.NeedSpecs)
                {
                    if (!needs.NeedIsActive(spec.Id)) continue;
                    needSum.TryGetValue(spec.Id, out float sum); needSum[spec.Id] = sum + needs.GetNeedPoints(spec.Id);
                    needN.TryGetValue(spec.Id, out int n); needN[spec.Id] = n + 1;
                    if (needs.NeedIsInCriticalState(spec.Id)) { needCrit.TryGetValue(spec.Id, out int k); needCrit[spec.Id] = k + 1; }
                    else if (needs.NeedIsBelowWarningThreshold(spec.Id)) { needLow.TryGetValue(spec.Id, out int k); needLow[spec.Id] = k + 1; }
                }
            }
            o["pop"] = new JObject { ["adults"] = adults, ["children"] = children, ["bots"] = bots, ["total"] = adults + children };
            o["births"] = _births;
            o["grownUp"] = _grownUp;
            o["deaths"] = _deaths.DeepClone();
            _births = 0; _grownUp = 0; _deaths.RemoveAll();

            var needJson = new JObject();
            foreach (var id in needSum.Keys.OrderBy(k => k))
            {
                needCrit.TryGetValue(id, out int crit);
                needLow.TryGetValue(id, out int low);
                needJson[id] = new JArray(Math.Round(needSum[id] / Math.Max(1, needN[id]), 3), crit, low, needN[id]);
            }
            o["needs"] = needJson;   // [average points, critical, below warning, colonists with the need]
            wb.Sort();
            var hist = new int[6];
            foreach (var w in wb) hist[Mathf.Clamp(w / 5, 0, 5)]++;
            o["wellbeing"] = new JObject
            {
                ["avg"] = wb.Count > 0 ? Math.Round(wb.Average(), 2) : 0,
                ["globalAvg"] = _wellbeingService.AverageGlobalWellbeing,
                ["min"] = wb.Count > 0 ? wb[0] : 0, ["max"] = wb.Count > 0 ? wb[wb.Count - 1] : 0,
                ["median"] = wb.Count > 0 ? wb[wb.Count / 2] : 0,
                ["hist5"] = new JArray(hist.Cast<object>().ToArray())   // 0-4, 5-9, ..., 25+
            };

            int beds = 0, used = 0, vacancies = 0;
            foreach (var entity in _entityRegistry.Entities)
            {
                if (!entity) continue;
                var dwelling = entity.GetComponent<Dwelling>();
                if (dwelling != null)
                {
                    var bo = entity.GetComponent<BlockObject>();
                    if (bo != null && bo.IsFinished) { beds += dwelling.MaxBeavers; used += dwelling.NumberOfDwellers; }
                }
                var w = entity.GetComponent<Workplace>();
                if (w != null)
                {
                    var bo = entity.GetComponent<BlockObject>();
                    if (bo != null && bo.IsFinished) vacancies += Math.Max(0, w.DesiredWorkers - w.NumberOfAssignedWorkers);
                }
            }
            o["jobs"] = new JObject { ["employed"] = employed, ["unemployed"] = unemployed, ["vacancies"] = vacancies };
            o["homes"] = new JObject { ["beds"] = beds, ["used"] = used, ["free"] = beds - used, ["homeless"] = homeless };

            // goods: [available, all incl. inputs, capacity, produced, consumed] for the day that just ended
            var goods = new JObject();
            foreach (var good in _goodService.Goods)
            {
                var count = _resourceCountingService.GetGlobalResourceCount(good);
                int prod = 0, cons = 0;
                try
                {
                    var registry = _globalGoodSamplingRegistry.GoodSamplingRegistry;
                    var samples = registry != null ? registry.GetGoodSampleHistory(good).GoodSamples : default;
                    if (registry != null && samples.Count > 0) { prod = samples[samples.Count - 1].Production; cons = samples[samples.Count - 1].Consumption; }
                }
                catch (Exception) { }
                if (count.AllStock == 0 && count.TotalCapacity == 0 && prod == 0 && cons == 0) continue;
                goods[good] = new JArray(count.AvailableStock, count.AllStock, count.TotalCapacity, prod, cons);
            }
            o["goods"] = goods;

            // where the water and the staple foods are actually held (stock and limit per building template)
            var holders = new JObject();
            var holderGoods = Request.Str(_spec, "holderGoods", "Water");
            var invs = new List<Timberborn.InventorySystem.Inventory>();
            foreach (var entity in _entityRegistry.Entities)
            {
                if (!entity) continue;
                invs.Clear();
                entity.GetComponents(invs);   // never GetComponent<Inventory>: it throws on a building with two inventories
                if (invs.Count == 0 || entity.GetComponent<LivingNaturalResource>() != null) continue;   // not the trees' log stacks
                string t = entity.GetComponent<TemplateSpec>()?.TemplateName ?? "?";
                foreach (var good in holderGoods.Split(','))
                    foreach (var inv in invs)
                    {
                        int limit = inv.LimitedAmount(good), stock = inv.AmountInStock(good);
                        if (limit == 0 && stock == 0) continue;
                        if (!(holders[good] is JObject g)) holders[good] = g = new JObject();
                        var key = t + "/" + inv.ComponentName;
                        var cur = g[key] as JArray ?? new JArray(0, 0, 0);
                        g[key] = new JArray((int)cur[0] + stock, (int)cur[1] + limit, (int)cur[2] + 1);
                    }
            }
            o["holders"] = holders;   // good -> "template/inventory": [stock, limit, buildings]

            // workplaces over the day: worker-samples by running behavior, statuses seen
            var work = new JArray();
            foreach (var kv in _work.OrderBy(k => k.Value.Label))
            {
                var s = kv.Value;
                if (s.Samples == 0) continue;
                var w = kv.Key;
                work.Add(new JObject
                {
                    ["id"] = s.Label,
                    ["template"] = w ? w.GetComponent<TemplateSpec>()?.TemplateName : null,
                    ["workers"] = w ? w.NumberOfAssignedWorkers : 0,
                    ["desired"] = w ? w.DesiredWorkers : 0,
                    ["samples"] = s.Samples, ["workerSamples"] = s.WorkerSamples, ["understaffed"] = s.Understaffed,
                    ["behaviors"] = JObject.FromObject(s.Behaviors.OrderByDescending(b => b.Value).Take(8).ToDictionary(b => b.Key, b => b.Value)),
                    ["statuses"] = JObject.FromObject(s.Statuses.OrderByDescending(b => b.Value).Take(6).ToDictionary(b => b.Key, b => b.Value))
                });
            }
            o["work"] = work;
            _work.Clear();

            // construction
            int unfinished = 0;
            var waiting = new JArray();
            foreach (var p in _placed.Values)
            {
                if (!p.Bo || p.Bo.IsFinished) continue;
                unfinished++;
                var site = p.Bo.GetComponent<ConstructionSite>();
                if (site != null && waiting.Count < 12)
                    waiting.Add(new JObject { ["id"] = p.Id, ["materials"] = Math.Round(site.MaterialProgress, 2), ["built"] = Math.Round(site.BuildTimeProgress, 2) });
            }
            var pending = new JArray();
            foreach (var cell in _pendingPath.Take(10))
            {
                var t = TreeAt(cell);
                var tree = t.HasValue ? _blockService.GetBottomObjectAt(t.Value) : null;
                var living = tree ? tree.GetComponent<LivingNaturalResource>() : null;
                pending.Add(new JObject
                {
                    ["cell"] = new JArray(cell.x, cell.y, cell.z), ["tree"] = tree ? tree.GetComponent<TemplateSpec>()?.TemplateName : null,
                    ["dead"] = living != null && living.IsDead, ["marked"] = t.HasValue && _treeCuttingArea.IsInCuttingArea(t.Value)
                });
            }
            o["sites"] = new JObject { ["unfinished"] = unfinished, ["list"] = waiting, ["pathTilesWaitingForTrees"] = _pendingPath.Count, ["pendingPath"] = pending };

            // plants by template: [alive, grown, dying, dead]
            var plants = new Dictionary<string, int[]>();
            foreach (var entity in _entityRegistry.Entities)
            {
                if (!entity) continue;
                var living = entity.GetComponent<LivingNaturalResource>();
                if (living == null) continue;
                string t = entity.GetComponent<TemplateSpec>()?.TemplateName ?? "?";
                if (!plants.TryGetValue(t, out var a)) plants[t] = a = new int[4];
                if (living.IsDead) { a[3]++; continue; }
                a[0]++;
                var growable = entity.GetComponent<Growable>();
                if (growable != null && growable.IsGrown) a[1]++;
                var dying = entity.GetComponent<DyingNaturalResource>();
                if (dying != null && dying.IsDying) a[2]++;
            }
            var plantJson = new JObject();
            foreach (var kv in plants.OrderBy(k => k.Key)) plantJson[kv.Key] = new JArray(kv.Value.Cast<object>().ToArray());
            o["plants"] = plantJson;

            // steps still waiting, so a reader sees what the plan is blocked on
            var blocked = new JObject();
            foreach (var s in _steps)
                if (s.Done < s.Max && !s.Failed && (s.Waiting != null || s.Error != null) && s.Done == 0)
                    blocked[s.Id] = s.Waiting ?? s.Error;
            o["blocked"] = blocked;

            AppendLine("daily.jsonl", o);
            _daysRecorded++;
            if (!final && adults + children == 0 && Request.Bool(_spec, "endWhenExtinct", true))
            {
                // nobody left: end the run now instead of idling to the planned day (the game driver reads this field)
                Harness.Request.RunInGameHours = Mathf.Max(0.01f, Hours() - _gameDriverStartHours() + 0.05f);
                Event("extinct", null, null);
            }
            WriteState();
            if (!final)
                Harness.Info("playtest: day " + o["day"] + " pop " + (adults + children) + " wb " + o["wellbeing"]["avg"] + " " + o["weather"]
                             + " food/water " + FoodStock() + "/" + Stock("Water") + " unemployed " + unemployed + " homeless " + homeless);
        }

        private int FoodStock()
        {
            int n = 0;
            foreach (var good in _goodService.Goods)
            {
                // edible = anything that feeds Hunger; read from the good's consumption effects
                var spec = _goodService.GetGood(good);
                if (spec == null) continue;
                foreach (var effect in spec.ConsumptionEffects)
                    if (effect.NeedId == "Hunger") { n += Stock(good); break; }
            }
            return n;
        }

        private (int beds, int free, int homeless) Housing()
        {
            int beds = 0, used = 0, homeless = 0;
            RefreshWorkplaces(Hours());
            foreach (var dwelling in _dwellings)
            {
                if (!dwelling) continue;
                var bo = dwelling.GetComponent<BlockObject>();
                if (bo != null && bo.IsFinished) { beds += dwelling.MaxBeavers; used += dwelling.NumberOfDwellers; }
            }
            // finished homes placed since the last refresh
            foreach (var p in _placed.Values)
                if (p.Bo && p.Bo.IsFinished && p.Bo.GetComponent<Dwelling>() is Dwelling d && !_dwellings.Contains(d)) { beds += d.MaxBeavers; used += d.NumberOfDwellers; }
            foreach (var c in _characterPopulation.Characters)
            {
                if (!c) continue;
                var d = c.GetComponent<Dweller>();
                if (d != null && !d.HasHome) homeless++;
            }
            // beds still under construction count as planned: a player does not build more while some are going up
            foreach (var p in _placed.Values)
                if (p.Bo && !p.Bo.IsFinished && p.Bo.GetComponent<Dwelling>() is Dwelling planned) beds += planned.MaxBeavers;
            return (beds, beds - used, homeless);
        }

        private (int employed, int unemployed) Employment()
        {
            int e = 0, u = 0;
            foreach (var c in _characterPopulation.Characters)
            {
                if (!c || Kind(c) != "adult") continue;
                var worker = c.GetComponent<Worker>();
                if (worker == null) continue;
                if (worker.Workplace) e++; else u++;
            }
            return (e, u);
        }
    }
}
