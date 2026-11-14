using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using Newtonsoft.Json.Linq;
using Timberborn.BlockObjectTools;
using Timberborn.BlockSystem;
using Timberborn.BuilderPrioritySystem;
using Timberborn.Buildings;
using Timberborn.Coordinates;
using Timberborn.EntitySystem;
using Timberborn.Forestry;
using Timberborn.Gathering;
using Timberborn.NaturalResourcesLifecycle;
using Timberborn.PrioritySystem;
using Timberborn.ScienceSystem;
using Timberborn.TemplateSystem;
using Timberborn.WaterBuildings;
using UnityEngine;

namespace PandabornDevHarness
{
    /// <summary>Placement rules, path laying, planting and cutting areas for the scripted colony.</summary>
    public partial class PlaytestDriver
    {
        private static readonly Orientation[] AllOrientations = { Orientation.Cw0, Orientation.Cw90, Orientation.Cw180, Orientation.Cw270 };
        private static readonly Vector2Int[] Steps4 = { new Vector2Int(1, 0), new Vector2Int(-1, 0), new Vector2Int(0, 1), new Vector2Int(0, -1) };

        private readonly Dictionary<string, PreviewPlacer> _placers = new Dictionary<string, PreviewPlacer>();
        private readonly HashSet<Vector2Int> _network = new HashSet<Vector2Int>();      // path cells (and the DC doorstep)
        private readonly HashSet<Vector2Int> _reserved = new HashSet<Vector2Int>();     // marked fields and groves: no buildings
        private readonly HashSet<Vector2Int> _keepClear = new HashSet<Vector2Int>();    // entrances and laid paths
        private List<PlaceableBlockObjectSpec> _specs;
        private Dictionary<Vector2Int, string> _resourceIndex;   // map cell -> "tree:<template>" / "bush:<template>" / "plant:<template>"
        private readonly Dictionary<Vector2Int, Vector3Int> _resourceCoords = new Dictionary<Vector2Int, Vector3Int>();
        private float _resourceIndexAt = -1e9f;
        private int _networkZ = int.MinValue;

        // ------------------------------------------------------------------ build

        private bool Build(Step step, float now)
        {
            var o = step.Raw;
            string template = Resolve(Request.Str(o, "template", null));
            var spec = FindSpec(template);
            if (spec == null) { step.Error = "template " + template + " not available to this faction"; step.Failed = true; return false; }
            var building = spec.GetSpec<BuildingSpec>();

            // science: unlock as the tool's unlock button does, or wait for the points
            if (building != null && building.ScienceCost > 0 && !_buildingUnlockingService.Unlocked(building))
            {
                string unlock = Request.Str(o, "unlock", "science");
                if (unlock == "grant" && !spec.HasSpec<UnlockableOnceSpec>()) _buildingUnlockingService.UnlockIgnoringCost(building);
                else if (_buildingUnlockingService.Unlockable(building))
                {
                    _buildingUnlockingService.Unlock(building);
                    Event("unlock", step.Id, new JObject { ["template"] = template, ["science"] = building.ScienceCost, ["left"] = _scienceService.SciencePoints });
                }
                else { step.Waiting = "science " + building.ScienceCost + " for " + template + " (have " + _scienceService.SciencePoints + ")"; return false; }
            }

            EnsureNetwork();
            var anchor = Anchor(Request.Str(o, "near", "dc"));
            if (!anchor.HasValue) { step.Waiting = "anchor " + Request.Str(o, "near", "dc") + " not placed"; return false; }
            var sw = Stopwatch.StartNew();
            var result = PlaceBest(spec, anchor.Value, o, out string why, out int tried);
            if (result == null)
            {
                step.Error = "no spot: " + why + " (" + tried + " candidates, " + sw.ElapsedMilliseconds + " ms)";
                Event("placeFailed", step.Id, new JObject { ["template"] = template, ["why"] = step.Error });
                return false;
            }
            string id = step.Max > 1 || step.Instances.Count > 0 ? step.Id + "." + (step.Instances.Count + 1) : step.Id;
            var placed = new Placed { Id = id, StepId = step.Id, Template = template, Bo = result.Value.bo, PlacedAt = now };
            _placed[id] = placed;
            step.Instances.Add(id);
            if (o["priority"] != null && Enum.TryParse(Request.Str(o, "priority", "Normal"), true, out Priority priority))
                result.Value.bo.GetComponent<BuilderPrioritizable>()?.SetPriority(priority);
            var c = result.Value.bo.Coordinates;
            Event("placed", id, new JObject
            {
                ["template"] = template, ["at"] = new JArray(c.x, c.y, c.z), ["orientation"] = result.Value.bo.Orientation.ToString(),
                ["distance"] = Math.Round(Vector2Int.Distance(new Vector2Int(c.x, c.y), new Vector2Int(anchor.Value.x, anchor.Value.y)), 1),
                ["pathTiles"] = result.Value.pathTiles, ["candidates"] = tried, ["ms"] = sw.ElapsedMilliseconds,
                ["finished"] = result.Value.bo.IsFinished
            });
            return true;
        }

        private PlaceableBlockObjectSpec FindSpec(string template)
        {
            if (template == null) return null;
            if (_specs == null) _specs = _templateService.GetAll<PlaceableBlockObjectSpec>().ToList();
            return _specs.FirstOrDefault(s => (s.Blueprint.GetSpec<TemplateSpec>()?.TemplateName ?? s.Blueprint.Name) == template);
        }

        private Vector3Int? Anchor(string near)
        {
            if (near == null || near == "dc")
            {
                var center = _districtCenterRegistry.AllDistrictCenters.FirstOrDefault();
                if (center == null) return null;
                var bo = center.GetComponent<BlockObject>();
                return bo != null && bo.HasEntrance ? bo.PositionedEntrance.Coordinates : center.GetComponent<BlockObject>().Coordinates;
            }
            var placed = Instances(near).FirstOrDefault(p => p.Bo);
            if (placed == null) return null;
            return placed.Bo.HasEntrance ? placed.Bo.PositionedEntrance.Coordinates : placed.Bo.Coordinates;
        }

        /// <summary>The district center's doorstep starts the path network; every laid path joins it.</summary>
        private void EnsureNetwork()
        {
            if (_networkZ != int.MinValue) return;
            var dc = Anchor("dc");
            if (!dc.HasValue) return;
            _networkZ = dc.Value.z;
            _network.Add(new Vector2Int(dc.Value.x, dc.Value.y));
            _keepClear.Add(new Vector2Int(dc.Value.x, dc.Value.y));
        }

        private struct PlaceResult { public BlockObject bo; public int pathTiles; }

        /// <summary>
        /// Candidate cells around the anchor are scored by the rule (cheap), then tried in order with the game's own placement
        /// validity; a placed site must also keep clear of fields, satisfy the rule's post-check (pump intake over water) and be
        /// reachable by a level path from the network, or it is deleted and the next candidate is tried.
        /// </summary>
        private PlaceResult? PlaceBest(PlaceableBlockObjectSpec spec, Vector3Int anchor, JObject o, out string why, out int tried)
        {
            why = "no valid candidate";
            tried = 0;
            string rule = Request.Str(o, "rule", "any");
            int minD = (int)Request.Num(o, "minDistance", 3f), maxD = (int)Request.Num(o, "maxDistance", 30f);
            int radius = (int)Request.Num(o, "radius", rule == "trees" || rule == "bushes" ? 9f : 6f);
            int min = (int)Request.Num(o, "min", rule == "moist" || rule == "dry" ? 16f : rule == "trees" ? 12f : rule == "bushes" ? 4f : 0f);
            float minDepth = Request.Num(o, "minDepth", 0.5f);
            int budget = (int)Request.Num(o, "tries", 300f);
            int baseZ = spec.GetSpec<BlockObjectSpec>()?.BaseZ ?? 0;
            var orientations = new List<Orientation>();
            if (Request.Str(o, "orientation", null) is string os && Enum.TryParse(os, true, out Orientation wanted)) orientations.Add(wanted);
            else orientations.AddRange(AllOrientations);
            if (rule == "trees" || rule == "bushes") RefreshResourceIndex(true);

            var candidates = new List<(Vector3Int cell, float score)>();
            if (o["offset"] is JArray off && off.Count >= 2)
            {
                var c = new Vector3Int(anchor.x + (int)off[0], anchor.y + (int)off[1], anchor.z + (off.Count > 2 ? (int)off[2] : 0));
                candidates.Add((Ground(c), 0f));
            }
            else
            {
                for (int dx = -maxD; dx <= maxD; dx++)
                    for (int dy = -maxD; dy <= maxD; dy++)
                    {
                        float d = Mathf.Sqrt(dx * dx + dy * dy);
                        if (d < minD || d > maxD) continue;
                        var xy = new Vector2Int(anchor.x + dx, anchor.y + dy);
                        if (!_terrainService.Contains(xy) || _reserved.Contains(xy) || _keepClear.Contains(xy)) continue;
                        var cell = Ground(new Vector3Int(xy.x, xy.y, anchor.z));
                        if (_networkZ != int.MinValue && cell.z != _networkZ && Request.Bool(o, "sameLevel", true)) continue;
                        float score = d;
                        switch (rule)
                        {
                            case "nearWater":
                            {
                                int w = WaterDistance(cell, 4, minDepth);
                                if (w < 0) continue;
                                score = d + 4f * w;
                                break;
                            }
                            case "moist":
                            case "dry":
                            {
                                int n = SoilCount(cell, radius, rule == "moist");
                                if (n < min) continue;
                                score = d - 0.25f * n;
                                break;
                            }
                            case "trees":
                            case "bushes":
                            {
                                int n = ResourceCount(cell, radius, rule == "trees" ? "tree:" : "bush:");
                                if (n < min) continue;
                                score = d - 0.5f * n;
                                break;
                            }
                        }
                        candidates.Add((cell, score));
                    }
                candidates.Sort((a, b) => a.score.CompareTo(b.score));
            }
            if (candidates.Count == 0) { why = "no cell within " + minD + "-" + maxD + " tiles meets rule " + rule; return null; }

            var placer = Placer(spec);
            try
            {
                foreach (var (cell, _) in candidates)
                {
                    if (tried >= budget) { why = "tried " + budget + " candidates; last: " + why; break; }
                    foreach (var orientation in orientations)
                    {
                        var target = new Vector3Int(cell.x, cell.y, cell.z - baseZ);
                        var placement = Valid(placer, target, orientation);
                        if (!placement.HasValue) continue;
                        tried++;
                        var builder = new EntitySetup.Builder(spec.Blueprint);
                        BlockObject bo;
                        if (spec.HasSpec<BuildingSpec>())
                        {
                            bool finished = spec.GetSpec<BuildingSpec>().PlaceFinished;
                            bo = finished ? _constructionFactory.CreateAsFinished(builder, placement.Value)
                                          : _constructionFactory.CreateAsUnfinished(builder, placement.Value);
                        }
                        else
                        {
                            _blockObjectPlacerService.GetMatchingPlacer(spec.GetSpec<BlockObjectSpec>()).Place(builder, placement.Value);
                            bo = null;
                            foreach (var b in _blockService.GetObjectsAt(placement.Value.Coordinates))
                                if (b && (b.GetComponent<TemplateSpec>()?.TemplateName == spec.GetSpec<TemplateSpec>()?.TemplateName)) bo = b;
                        }
                        if (!bo) { why = "the game created nothing"; continue; }
                        string reject = PostCheck(bo, rule, minDepth);
                        int laid = 0;
                        if (reject == null && bo.HasEntrance)
                        {
                            var route = Route(bo.PositionedEntrance.Coordinates, (int)Request.Num(o, "maxPath", 60f));
                            if (route == null) reject = "no level path to the network";
                            else laid = LayPath(route);
                        }
                        else if (reject == null && !NearNetwork(bo.Coordinates, 8)) reject = "out of district reach (no entrance, far from paths)";
                        if (reject != null)
                        {
                            why = reject;
                            _entityService.Delete(bo);
                            continue;
                        }
                        if (bo.HasEntrance) _keepClear.Add(new Vector2Int(bo.PositionedEntrance.Coordinates.x, bo.PositionedEntrance.Coordinates.y));
                        return new PlaceResult { bo = bo, pathTiles = laid };
                    }
                }
            }
            finally { placer.HideAllPreviews(); }
            if (tried == 0) why = "no candidate passed the game's placement check (" + candidates.Count + " cells)";
            return null;
        }

        private string PostCheck(BlockObject bo, string rule, float minDepth)
        {
            if (bo.PositionedBlocks != null)
                foreach (var c in bo.PositionedBlocks.GetOccupiedCoordinates())
                {
                    var xy = new Vector2Int(c.x, c.y);
                    if (_reserved.Contains(xy)) return "would cover a field";
                    if (_keepClear.Contains(xy) || _network.Contains(xy)) return "would cover a path or entrance";
                }
            if (bo.HasEntrance)
            {
                var e = bo.PositionedEntrance.Coordinates;
                if (_reserved.Contains(new Vector2Int(e.x, e.y))) return "entrance on a field";
            }
            if (rule == "nearWater")
            {
                var input = bo.GetComponent<WaterInput>();
                if (input == null) return null;
                var c = input.Coordinates;
                float best = 0f;
                for (int z = c.z; z >= c.z - 6 && z >= 0; z--) best = Mathf.Max(best, _waterMap.WaterDepth(new Vector3Int(c.x, c.y, z)));
                if (best < minDepth) return "intake not over water deep enough (" + best.ToString("0.00") + ")";
            }
            return null;
        }

        private PreviewPlacer Placer(PlaceableBlockObjectSpec spec)
        {
            string key = spec.Blueprint.Name;
            if (!_placers.TryGetValue(key, out var placer)) _placers[key] = placer = _previewPlacerFactory.Create(spec);
            return placer;
        }

        private static Placement? Valid(PreviewPlacer placer, Vector3Int cell, Orientation orientation)
        {
            var buildable = placer.GetBuildableCoordinates(new[] { new Placement(cell, orientation, FlipMode.Unflipped) }).ToList();
            return buildable.Count > 0 ? buildable[0] : (Placement?)null;
        }

        private Vector3Int Ground(Vector3Int c)
        {
            if (!_terrainService.Contains(new Vector2Int(c.x, c.y))) return c;
            int z = _terrainService.GetTerrainHeightBelow(new Vector3Int(c.x, c.y, c.z + 4));
            return new Vector3Int(c.x, c.y, z);
        }

        /// <summary>Tiles to the nearest column with standing water at least minDepth deep, within max; -1 if none.</summary>
        private int WaterDistance(Vector3Int cell, int max, float minDepth)
        {
            for (int r = 1; r <= max; r++)
                for (int dx = -r; dx <= r; dx++)
                    for (int dy = -r; dy <= r; dy++)
                    {
                        if (Math.Max(Math.Abs(dx), Math.Abs(dy)) != r) continue;
                        var xy = new Vector2Int(cell.x + dx, cell.y + dy);
                        if (!_terrainService.Contains(xy)) continue;
                        var g = Ground(new Vector3Int(xy.x, xy.y, cell.z));
                        if (g.z > cell.z) continue;
                        if (_waterMap.WaterDepth(g) >= minDepth) return r;
                    }
            return -1;
        }

        private int SoilCount(Vector3Int cell, int radius, bool moist)
        {
            int n = 0;
            for (int dx = -radius; dx <= radius; dx++)
                for (int dy = -radius; dy <= radius; dy++)
                {
                    if (dx * dx + dy * dy > radius * radius) continue;
                    var xy = new Vector2Int(cell.x + dx, cell.y + dy);
                    if (!_terrainService.Contains(xy) || _reserved.Contains(xy)) continue;
                    var g = Ground(new Vector3Int(xy.x, xy.y, cell.z));
                    if (Math.Abs(g.z - cell.z) > 1) continue;
                    if (_waterMap.CellIsUnderwater(g)) continue;
                    if (_soilMoistureService.SoilIsMoist(g) == moist) n++;
                }
            return n;
        }

        private int ResourceCount(Vector3Int cell, int radius, string prefix)
        {
            int n = 0;
            for (int dx = -radius; dx <= radius; dx++)
                for (int dy = -radius; dy <= radius; dy++)
                {
                    if (dx * dx + dy * dy > radius * radius) continue;
                    if (_resourceIndex.TryGetValue(new Vector2Int(cell.x + dx, cell.y + dy), out var kind) && kind.StartsWith(prefix, StringComparison.Ordinal)) n++;
                }
            return n;
        }

        private void RefreshResourceIndex(bool force)
        {
            float now = Hours();
            if (!force && _resourceIndex != null && now - _resourceIndexAt < 6f) return;
            if (_resourceIndex != null && now - _resourceIndexAt < 0.5f) return;
            _resourceIndexAt = now;
            _resourceIndex = new Dictionary<Vector2Int, string>();
            _resourceCoords.Clear();
            foreach (var entity in _entityRegistry.Entities)
            {
                if (!entity) continue;
                var living = entity.GetComponent<LivingNaturalResource>();
                if (living == null || living.IsDead) continue;
                var bo = entity.GetComponent<BlockObject>();
                if (bo == null) continue;
                string name = entity.GetComponent<TemplateSpec>()?.TemplateName ?? "?";
                string kind = entity.GetComponent<TreeComponent>() != null ? "tree:" : entity.GetComponent<Gatherable>() != null ? "bush:" : "plant:";
                var key = new Vector2Int(bo.Coordinates.x, bo.Coordinates.y);
                _resourceIndex[key] = kind + name;
                _resourceCoords[key] = bo.Coordinates;
            }
        }

        private bool NearNetwork(Vector3Int c, int distance)
        {
            foreach (var n in _network)
                if (Math.Abs(n.x - c.x) <= distance && Math.Abs(n.y - c.y) <= distance) return true;
            return false;
        }

        // ------------------------------------------------------------------ paths

        /// <summary>Breadth-first search on the network's level from a building entrance to the nearest network cell.</summary>
        private List<Vector3Int> Route(Vector3Int from, int maxLength)
        {
            if (_networkZ == int.MinValue) return null;
            var start = new Vector2Int(from.x, from.y);
            if (from.z != _networkZ) return null;
            if (_network.Contains(start)) return new List<Vector3Int>();
            var pathSpec = FindSpec("Path");
            if (pathSpec == null) return null;
            var placer = Placer(pathSpec);
            var previous = new Dictionary<Vector2Int, Vector2Int> { [start] = start };
            var depth = new Dictionary<Vector2Int, int> { [start] = 0 };
            var queue = new Queue<Vector2Int>();
            queue.Enqueue(start);
            bool Open(Vector2Int c)
            {
                if (!_terrainService.Contains(c)) return false;
                if (_reserved.Contains(c)) return false;
                var cell = new Vector3Int(c.x, c.y, _networkZ);
                if (Ground(cell).z != _networkZ) return false;
                if (IsPath(cell)) return true;
                return Valid(placer, cell, Orientation.Cw0).HasValue;
            }
            try
            {
                if (!Open(start) && !IsPath(new Vector3Int(start.x, start.y, _networkZ))) return null;
                while (queue.Count > 0)
                {
                    var c = queue.Dequeue();
                    if (_network.Contains(c))
                    {
                        var route = new List<Vector3Int>();
                        for (var at = c; ; at = previous[at])
                        {
                            route.Add(new Vector3Int(at.x, at.y, _networkZ));
                            if (at == start) break;
                        }
                        return route;
                    }
                    if (depth[c] >= maxLength) continue;
                    foreach (var step in Steps4)
                    {
                        var n = c + step;
                        if (previous.ContainsKey(n)) continue;
                        if (!_network.Contains(n) && !Open(n)) continue;
                        previous[n] = c;
                        depth[n] = depth[c] + 1;
                        queue.Enqueue(n);
                    }
                }
            }
            finally { placer.HideAllPreviews(); }
            return null;
        }

        private int LayPath(List<Vector3Int> route)
        {
            var pathSpec = FindSpec("Path");
            var placer = Placer(pathSpec);
            int laid = 0;
            try
            {
                foreach (var cell in route)
                {
                    var xy = new Vector2Int(cell.x, cell.y);
                    if (!IsPath(cell))
                    {
                        var placement = Valid(placer, cell, Orientation.Cw0);
                        if (placement.HasValue)
                        {
                            var builder = new EntitySetup.Builder(pathSpec.Blueprint);
                            if (pathSpec.HasSpec<BuildingSpec>()) _constructionFactory.CreateAsFinished(builder, placement.Value);
                            else _blockObjectPlacerService.GetMatchingPlacer(pathSpec.GetSpec<BlockObjectSpec>()).Place(builder, placement.Value);
                            laid++;
                        }
                    }
                    _network.Add(xy);
                    _keepClear.Add(xy);
                }
            }
            finally { placer.HideAllPreviews(); }
            return laid;
        }

        private bool IsPath(Vector3Int cell)
        {
            foreach (var o in _blockService.GetObjectsAt(cell))
                if (o && o.GetComponent<TemplateSpec>()?.TemplateName == "Path") return true;
            return false;
        }

        // ------------------------------------------------------------------ fields and cutting

        private bool Plant(Step step)
        {
            var o = step.Raw;
            string plant = Resolve(Request.Str(o, "plant", null));
            var origin = Anchor(Request.Str(o, "target", "dc"));
            if (!origin.HasValue) { step.Waiting = "target " + Request.Str(o, "target", null) + " not placed"; return false; }
            int count = (int)Request.Num(o, "count", 20f);
            int radius = (int)Request.Num(o, "radius", 9f);
            int minFromTarget = (int)Request.Num(o, "minDistance", 2f);
            string soil = Request.Str(o, "soil", "moist");
            var cells = new List<(Vector3Int c, float d)>();
            for (int dx = -radius; dx <= radius; dx++)
                for (int dy = -radius; dy <= radius; dy++)
                {
                    float d = Mathf.Sqrt(dx * dx + dy * dy);
                    if (d > radius || d < minFromTarget) continue;
                    var xy = new Vector2Int(origin.Value.x + dx, origin.Value.y + dy);
                    if (!_terrainService.Contains(xy) || _reserved.Contains(xy) || _keepClear.Contains(xy) || _network.Contains(xy)) continue;
                    var g = Ground(new Vector3Int(xy.x, xy.y, origin.Value.z));
                    if (Math.Abs(g.z - origin.Value.z) > 2) continue;
                    if (_plantingService.IsResourceAt(g)) continue;
                    if (!_plantingAreaValidator.CanPlant(g, plant)) continue;
                    if (soil == "moist" && !_soilMoistureService.SoilIsMoist(g)) continue;
                    if (soil == "dry" && _soilMoistureService.SoilIsMoist(g)) continue;
                    // prefer a compact block: distance first, then a mild preference for cells beside cells already chosen
                    cells.Add((g, d));
                }
            cells.Sort((a, b) => a.d.CompareTo(b.d));
            int marked = 0;
            foreach (var (c, _) in cells)
            {
                if (marked >= count) break;
                _plantingService.SetPlantingCoordinates(c, plant);
                _reserved.Add(new Vector2Int(c.x, c.y));
                step.Cells.Add(c);
                marked++;
            }
            if (marked == 0)
            {
                step.Error = "no " + soil + " plantable cell for " + plant + " within " + radius + " of " + Request.Str(o, "target", "dc");
                Event("plantFailed", step.Id, new JObject { ["plant"] = plant, ["why"] = step.Error });
                return false;
            }
            Event("plant", step.Id, new JObject { ["plant"] = plant, ["cells"] = marked, ["wanted"] = count, ["candidates"] = cells.Count });
            return true;
        }

        private bool Cut(Step step)
        {
            var o = step.Raw;
            var list = new List<Vector3Int>();
            string field = Request.Str(o, "field", null);
            if (field != null)
            {
                var source = _steps.FirstOrDefault(s => s.Id == field);
                if (source == null || source.Cells.Count == 0) { step.Waiting = "field " + field + " not marked"; return false; }
                list.AddRange(source.Cells);
            }
            else
            {
                var origin = Anchor(Request.Str(o, "target", "dc"));
                if (!origin.HasValue) { step.Waiting = "target " + Request.Str(o, "target", null) + " not placed"; return false; }
                RefreshResourceIndex(true);
                int count = (int)Request.Num(o, "count", 30f);
                int radius = (int)Request.Num(o, "radius", 12f);
                var only = o["trees"] is JArray t ? new HashSet<string>(t.Select(x => Resolve((string)x))) : null;
                var trees = new List<(Vector3Int c, float d)>();
                foreach (var kv in _resourceIndex)
                {
                    if (!kv.Value.StartsWith("tree:", StringComparison.Ordinal)) continue;
                    if (only != null && !only.Contains(kv.Value.Substring(5))) continue;
                    float d = Vector2Int.Distance(kv.Key, new Vector2Int(origin.Value.x, origin.Value.y));
                    if (d > radius) continue;
                    // the cutting area is keyed by the tree's own block coordinates
                    trees.Add((_resourceCoords[kv.Key], d));
                }
                trees.Sort((a, b) => a.d.CompareTo(b.d));
                foreach (var (c, _) in trees.Take(count)) list.Add(c);
            }
            if (list.Count == 0) { step.Error = "no trees to mark"; Event("cutFailed", step.Id, null); return false; }
            _treeCuttingArea.AddCoordinates(list);
            step.Cells.AddRange(list);
            Event("cut", step.Id, new JObject { ["cells"] = list.Count, ["field"] = field });
            return true;
        }
    }
}
