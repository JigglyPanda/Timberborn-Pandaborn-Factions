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
using Timberborn.Growing;
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
        private readonly JArray _pumpDiagnostics = new JArray();
        private readonly HashSet<Vector3Int> _pendingPath = new HashSet<Vector3Int>();
        private readonly Dictionary<Vector2Int, int> _pathCostCache = new Dictionary<Vector2Int, int>();
        private readonly Dictionary<string, int> _rejects = new Dictionary<string, int>();

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
            _rejects.Clear();
            var result = PlaceBest(spec, anchor.Value, o, out string why, out int tried);
            if (result == null)
            {
                step.Error = "no spot: " + why + " (" + tried + " candidates, " + sw.ElapsedMilliseconds + " ms)";
                Event("placeFailed", step.Id, new JObject { ["template"] = template, ["why"] = step.Error, ["rejects"] = JObject.FromObject(_rejects) });
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
                                // deeper water lasts longer into a drought: a metre of depth is worth 15 tiles of walking
                                score = d + 4f * w - 15f * Mathf.Min(1.5f, DeepestWater(cell, 3));
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
            var intakeSpec = rule == "nearWater" ? spec.Blueprint.GetSpec<WaterInputSpec>() : null;
            _pathCostCache.Clear();
            try
            {
                var clock = Stopwatch.StartNew();
                long searchMs = (long)Request.Num(o, "searchMs", 4000f);
                // with "pathThroughTrees", a spot reachable over open ground is still preferred: the first pass refuses
                // routes through trees, the second allows them
                bool allowTrees = Request.Bool(o, "pathThroughTrees", false);
                for (int pass = allowTrees ? 0 : 1; pass < 2; pass++)
                {
                bool throughTrees = pass == 1 && allowTrees;
                int passTried = 0;
                foreach (var (cell, _) in candidates)
                {
                    if (tried >= budget) { why = "tried " + budget + " candidates; last: " + why; break; }
                    if (clock.ElapsedMilliseconds > searchMs) { why = "search time out (" + searchMs + " ms); last: " + why; break; }
                    if (allowTrees && pass == 0 && (passTried >= budget / 2 || clock.ElapsedMilliseconds > searchMs / 2)) break;
                    foreach (var orientation in orientations)
                    {
                        var target = new Vector3Int(cell.x, cell.y, cell.z - baseZ);
                        // a water intake must land on water: predict it before asking the game (the post-check confirms)
                        if (intakeSpec != null)
                        {
                            var turned = Rotate(new Vector2Int(intakeSpec.WaterInputCoordinates.x, intakeSpec.WaterInputCoordinates.y), orientation);
                            var at = Ground(new Vector3Int(cell.x + turned.x, cell.y + turned.y, cell.z));
                            if (_waterMap.WaterDepth(at) < minDepth) continue;
                        }
                        var placement = Valid(placer, target, orientation);
                        if (!placement.HasValue) continue;
                        tried++;
                        passTried++;
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
                            // through trees only when the scenario says so (the lumberjacks must be able to clear them first)
                            var route = Route(bo.PositionedEntrance.Coordinates, (int)Request.Num(o, "maxPath", 60f), throughTrees);
                            if (route == null) reject = "no level path to the network";
                            else laid = LayPath(route);
                        }
                        else if (reject == null && !NearNetwork(bo.Coordinates, 8)) reject = "out of district reach (no entrance, far from paths)";
                        if (reject != null)
                        {
                            why = reject;
                            string rk = reject.Split('(')[0].Trim();
                            _rejects.TryGetValue(rk, out int rn);
                            _rejects[rk] = rn + 1;
                            _entityService.Delete(bo);
                            continue;
                        }
                        if (bo.HasEntrance) _keepClear.Add(new Vector2Int(bo.PositionedEntrance.Coordinates.x, bo.PositionedEntrance.Coordinates.y));
                        return new PlaceResult { bo = bo, pathTiles = laid };
                    }
                }
                }
            }
            finally { placer.HideAllPreviews(); }
            if (tried == 0) why = "no candidate passed the game's placement check (" + candidates.Count + " cells)";
            return null;
        }

        /// <summary>A footprint offset turned like the building tool turns it (clockwise; matches the game's transform for
        /// offsets on the pivot column, which is where water intakes sit).</summary>
        private static Vector2Int Rotate(Vector2Int v, Orientation o)
        {
            switch (o)
            {
                case Orientation.Cw90: return new Vector2Int(v.y, -v.x);
                case Orientation.Cw180: return new Vector2Int(-v.x, -v.y);
                case Orientation.Cw270: return new Vector2Int(-v.y, v.x);
                default: return v;
            }
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
                var inputSpec = bo.GetComponent<WaterInputSpec>();
                if (inputSpec == null) return null;
                // the building's own transform (the WaterInput component computes the same in PostInitializeEntity)
                var c = bo.TransformCoordinates(inputSpec.WaterInputCoordinates);
                // the pipe reaches down from the intake (WaterInputPipeSpec.MaxDepth 2): take the deepest water it can reach
                float depth = 0f;
                for (int z = c.z + 1; z >= c.z - 3 && z >= 0; z--) depth = Mathf.Max(depth, _waterMap.WaterDepth(new Vector3Int(c.x, c.y, z)));
                bool floorKnown = _waterMap.TryGetColumnFloor(c, out int floor);
                if (_pumpDiagnostics.Count < 40)
                    _pumpDiagnostics.Add(new JObject
                    {
                        ["at"] = new JArray(bo.Coordinates.x, bo.Coordinates.y, bo.Coordinates.z), ["o"] = bo.Orientation.ToString(),
                        ["intake"] = new JArray(c.x, c.y, c.z), ["depth"] = Math.Round(depth, 2), ["floor"] = floorKnown ? floor : -1,
                        ["terrain"] = _terrainService.GetTerrainHeightBelow(new Vector3Int(c.x, c.y, c.z + 6))
                    });
                if (depth < minDepth) return "intake not over water deep enough (" + depth.ToString("0.00") + ")";
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

        private float DeepestWater(Vector3Int cell, int radius)
        {
            float best = 0f;
            for (int dx = -radius; dx <= radius; dx++)
                for (int dy = -radius; dy <= radius; dy++)
                {
                    var xy = new Vector2Int(cell.x + dx, cell.y + dy);
                    if (!_terrainService.Contains(xy)) continue;
                    best = Mathf.Max(best, _waterMap.WaterDepth(Ground(new Vector3Int(xy.x, xy.y, cell.z))));
                }
            return best;
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

        /// <summary>
        /// Writes playtest\map.txt: rows of the area around the district center, one character per cell. Digit = terrain height
        /// relative to the center's level (0-9, 'A','B'.. one, two levels below), '~' water at least 0.3 deep (',' shallower), 'T' tree, 'b' bush,
        /// '#' building or path, '@' the district center doorstep.
        /// </summary>
        private void DumpMap(int radius)
        {
            if (radius <= 0) return;
            EnsureNetwork();
            var dc = Anchor("dc");
            if (!dc.HasValue) return;
            RefreshResourceIndex(true);
            var sb = new System.Text.StringBuilder();
            sb.Append("# origin " + dc.Value + ", radius " + radius + "; north (y+) at the top\n");
            for (int y = dc.Value.y + radius; y >= dc.Value.y - radius; y--)
            {
                for (int x = dc.Value.x - radius; x <= dc.Value.x + radius; x++)
                {
                    var xy = new Vector2Int(x, y);
                    if (!_terrainService.Contains(xy)) { sb.Append(' '); continue; }
                    var g = Ground(new Vector3Int(x, y, dc.Value.z + 8));
                    char ch;
                    float depth = _waterMap.WaterDepth(g);
                    if (x == dc.Value.x && y == dc.Value.y) ch = '@';
                    else if (depth >= 0.3f) ch = '~';
                    else if (depth > 0.02f) ch = ',';
                    else if (_resourceIndex.TryGetValue(xy, out var kind) && kind.StartsWith("tree:", StringComparison.Ordinal)) ch = 'T';
                    else if (_resourceIndex.TryGetValue(xy, out kind) && kind.StartsWith("bush:", StringComparison.Ordinal)) ch = 'b';
                    else if (_blockService.GetObjectsAt(g).Count > 0) ch = '#';
                    else
                    {
                        int dz = g.z - dc.Value.z;
                        ch = dz < 0 ? (dz < -9 ? '-' : (char)('A' + Math.Min(-dz, 25) - 1)) : (char)('0' + Math.Min(dz, 9));
                    }
                    sb.Append(ch);
                }
                sb.Append('\n');
            }
            System.IO.File.WriteAllText(System.IO.Path.Combine(_dir, "map.txt"), sb.ToString());
        }

        // ------------------------------------------------------------------ paths

        /// <summary>
        /// Cheapest route on the network's level from a building entrance to the nearest network cell (Dijkstra: an open cell
        /// costs 1, a cell holding a tree costs 4, as a player routes around a forest unless it is much shorter through it).
        /// </summary>
        private List<Vector3Int> Route(Vector3Int from, int maxLength, bool throughTrees)
        {
            if (_networkZ == int.MinValue) return null;
            var start = new Vector2Int(from.x, from.y);
            if (from.z != _networkZ) return null;
            if (_network.Contains(start)) return new List<Vector3Int>();
            var pathSpec = FindSpec("Path");
            if (pathSpec == null) return null;
            var placer = Placer(pathSpec);
            var previous = new Dictionary<Vector2Int, Vector2Int> { [start] = start };
            var cost = new Dictionary<Vector2Int, int> { [start] = 0 };
            var open = new SortedSet<(int cost, int x, int y)> { (0, start.x, start.y) };
            int Cost(Vector2Int c)
            {
                if (!_terrainService.Contains(c) || _reserved.Contains(c)) return -1;
                var cell = new Vector3Int(c.x, c.y, _networkZ);
                // open / blocked / tree, cached for one placement search (the expensive part is the game's path check)
                if (!_pathCostCache.TryGetValue(c, out int kind))
                {
                    if (Ground(cell).z != _networkZ) kind = -1;
                    else if (IsPath(cell) || Valid(placer, cell, Orientation.Cw0).HasValue) kind = 1;
                    else if (_pendingPath.Contains(cell)) kind = 3;
                    else kind = TreeAt(cell).HasValue ? 8 : -1;
                    _pathCostCache[c] = kind;
                }
                if (kind > 1 && !throughTrees) return -1;
                return kind;
            }
            try
            {
                if (Cost(start) < 0) return null;
                while (open.Count > 0)
                {
                    var top = open.Min;
                    open.Remove(top);
                    var c = new Vector2Int(top.x, top.y);
                    if (top.cost > cost[c]) continue;
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
                    if (top.cost >= maxLength) continue;
                    foreach (var step in Steps4)
                    {
                        var n = c + step;
                        int w = _network.Contains(n) ? 1 : Cost(n);
                        if (w < 0) continue;
                        int nc = top.cost + w;
                        if (cost.TryGetValue(n, out int known) && known <= nc) continue;
                        cost[n] = nc;
                        previous[n] = c;
                        open.Add((nc, n.x, n.y));
                    }
                }
            }
            finally { placer.HideAllPreviews(); }
            return null;
        }

        /// <summary>
        /// The coordinates of a tree a lumberjack can clear from this cell: grown (a sapling cannot be cut and would block the
        /// tile for days), or dead with logs still on it. Null for no tree or a tree that cannot be cut yet.
        /// </summary>
        private Vector3Int? TreeAt(Vector3Int cell)
        {
            foreach (var o in _blockService.GetObjectsAt(cell))
            {
                if (!o || o.GetComponent<TreeComponent>() == null) continue;
                var growable = o.GetComponent<Growable>();
                var living = o.GetComponent<LivingNaturalResource>();
                if (living != null && !living.IsDead && growable != null && !growable.IsGrown) return null;
                return o.Coordinates;
            }
            return null;
        }

        /// <summary>
        /// Lays finished path tiles along a route. A tile still holding a tree is marked for cutting and laid later, once the
        /// lumberjacks have cleared it (LayPendingPaths), as a player would; the cell joins the network now so later routes use it.
        /// </summary>
        private int LayPath(List<Vector3Int> route)
        {
            int laid = 0;
            var trees = new List<Vector3Int>();
            foreach (var cell in route)
            {
                var xy = new Vector2Int(cell.x, cell.y);
                _keepClear.Add(xy);
                bool already = IsPath(cell);
                if (already || TryLayPathTile(cell))
                {
                    if (!already) laid++;
                    _network.Add(xy);
                    continue;
                }
                // a tree stands here: the tile joins the network only when it is laid (LayPendingPaths), so a building
                // routed to it is not counted as connected before it really is
                if (TreeAt(cell) is Vector3Int tree) { trees.Add(tree); _pendingPath.Add(cell); }
            }
            RecomputeNetwork();
            if (trees.Count > 0)
            {
                _treeCuttingArea.AddCoordinates(trees);
                Event("pathThroughTrees", null, new JObject { ["trees"] = trees.Count });
            }
            return laid;
        }

        /// <summary>
        /// The network is the set of laid path tiles joined to the district center's doorstep: tiles laid beyond a tree that
        /// is still standing form an island, and a building routed to an island is not connected yet.
        /// </summary>
        private void RecomputeNetwork()
        {
            var dc = Anchor("dc");
            if (!dc.HasValue) return;
            var start = new Vector2Int(dc.Value.x, dc.Value.y);
            var seen = new HashSet<Vector2Int> { start };
            var queue = new Queue<Vector2Int>();
            queue.Enqueue(start);
            while (queue.Count > 0)
            {
                var c = queue.Dequeue();
                foreach (var step in Steps4)
                {
                    var n = c + step;
                    if (seen.Contains(n)) continue;
                    if (!IsPath(new Vector3Int(n.x, n.y, _networkZ))) continue;
                    seen.Add(n);
                    queue.Enqueue(n);
                }
            }
            _network.Clear();
            foreach (var c in seen) _network.Add(c);
        }

        private bool TryLayPathTile(Vector3Int cell)
        {
            var pathSpec = FindSpec("Path");
            var placer = Placer(pathSpec);
            try
            {
                var placement = Valid(placer, cell, Orientation.Cw0);
                if (!placement.HasValue) return false;
                var builder = new EntitySetup.Builder(pathSpec.Blueprint);
                if (pathSpec.HasSpec<BuildingSpec>()) _constructionFactory.CreateAsFinished(builder, placement.Value);
                else _blockObjectPlacerService.GetMatchingPlacer(pathSpec.GetSpec<BlockObjectSpec>()).Place(builder, placement.Value);
                return true;
            }
            finally { placer.HideAllPreviews(); }
        }

        private void LayPendingPaths()
        {
            if (_pendingPath.Count == 0) return;
            foreach (var cell in _pendingPath.ToList())
                if (IsPath(cell) || TryLayPathTile(cell)) { _pendingPath.Remove(cell); _network.Add(new Vector2Int(cell.x, cell.y)); }
            RecomputeNetwork();
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
