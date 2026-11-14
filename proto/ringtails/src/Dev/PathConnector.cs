using System;
using System.Collections.Generic;
using System.Linq;
using Timberborn.BlockObjectTools;
using Timberborn.BlockSystem;
using Timberborn.Buildings;
using Timberborn.ConstructionSites;
using Timberborn.Coordinates;
using Timberborn.EntitySystem;
using Timberborn.GameDistricts;
using Timberborn.TemplateSystem;
using Timberborn.TerrainSystem;
using UnityEngine;

namespace Pandaborn.Ringtails.Dev
{
    /// <summary>
    /// Dev only. The harness places buildings near the district center but lays no paths, so nothing it places joins the
    /// district (no workers, no dwellers). This connects every building entrance to the district center doorstep with
    /// finished Path tiles: a breadth-first search over level cells where the game's own placement validation accepts a path.
    /// </summary>
    public class PathConnector
    {
        private readonly TemplateService _templateService;
        private readonly PreviewPlacerFactory _previewPlacerFactory;
        private readonly ConstructionFactory _constructionFactory;
        private readonly ITerrainService _terrainService;
        private readonly EntityRegistry _entityRegistry;
        private readonly IBlockService _blockService;
        private readonly EntityService _entityService;

        public PathConnector(TemplateService templateService, PreviewPlacerFactory previewPlacerFactory, ConstructionFactory constructionFactory,
                             ITerrainService terrainService, EntityRegistry entityRegistry, IBlockService blockService,
                             EntityService entityService)
        {
            _entityService = entityService;
            _blockService = blockService;
            _templateService = templateService;
            _previewPlacerFactory = previewPlacerFactory;
            _constructionFactory = constructionFactory;
            _terrainService = terrainService;
            _entityRegistry = entityRegistry;
        }

        /// <summary>Returns a short report: buildings connected / not connected, path tiles laid.</summary>
        public string Connect(DistrictCenter center, int radius = 30)
        {
            var pathSpec = _templateService.GetAll<PlaceableBlockObjectSpec>()
                .FirstOrDefault(s => s.GetSpec<TemplateSpec>()?.TemplateName == "Path");
            if (pathSpec == null) return "no Path template";
            var placer = _previewPlacerFactory.Create(pathSpec);
            // PositionedEntrance.Coordinates is the tile just outside the door (DoorstepCoordinates is the tile inside it)
            var origin = center.GetComponent<BlockObject>().PositionedEntrance.Coordinates;
            var paths = new HashSet<Vector3Int>();
            var network = new HashSet<Vector3Int> { origin };
            if (!HasPath(origin) && CanPlace(placer, origin)) Place(pathSpec, origin, paths);
            string diagnostics = "origin " + origin + " " + Diagnose(placer, origin);
            int connected = 0, failed = 0, relocated = 0;
            var failures = new List<string>();
            var unconnected = new List<BlockObject>();
            try
            {
                var targets = _entityRegistry.Entities
                    .Select(e => e.GetComponent<BlockObject>())
                    .Where(b => b && b.HasEntrance && b.GetComponent<DistrictCenter>() == null && b.GetComponent<DistrictBuilding>() != null)
                    .OrderBy(b => (b.PositionedEntrance.Coordinates - origin).sqrMagnitude)
                    .ToList();
                foreach (var target in targets)
                {
                    var goal = target.PositionedEntrance.Coordinates;
                    List<Vector3Int> route = null;
                    for (int attempt = 0; attempt < 8; attempt++)
                    {
                        route = Search(placer, goal, network, paths, origin, radius);
                        if (route == null) break;
                        // the placement check and the real placement can disagree: a cell that refuses a path is blocked and we search again
                        Vector3Int? refused = null;
                        foreach (var cell in route)
                        {
                            if (network.Contains(cell) || paths.Contains(cell) || HasPath(cell)) continue;
                            if (!Place(pathSpec, cell, paths)) { refused = cell; break; }
                        }
                        if (refused == null) break;
                        _blocked.Add(refused.Value);
                        route = null;
                    }
                    if (route == null)
                    {
                        if (failed < 3) diagnostics += "; goal " + goal + " " + Diagnose(placer, goal);
                        failed++;
                        failures.Add(target.GetComponent<TemplateSpec>()?.TemplateName);
                        unconnected.Add(target);
                        continue;
                    }
                    foreach (var cell in route) network.Add(cell);
                    connected++;
                }
            }
            finally
            {
                placer.HideAllPreviews();
            }
            return "connected " + connected + ", relocated and connected " + relocated + ", not connected " + failed + (failures.Count > 0 ? " (" + string.Join(", ", failures) + ")" : "")
                   + ", path tiles " + paths.Count + " [" + diagnostics + "]";
        }

        private List<Vector3Int> Search(PreviewPlacer placer, Vector3Int goal, HashSet<Vector3Int> network, HashSet<Vector3Int> paths,
                                        Vector3Int origin, int radius)
        {
            if (network.Contains(goal)) return new List<Vector3Int>();
            if (!paths.Contains(goal) && !HasPath(goal) && !CanPlace(placer, goal)) return null;
            var previous = new Dictionary<Vector3Int, Vector3Int> { [goal] = goal };
            var queue = new Queue<Vector3Int>();
            queue.Enqueue(goal);
            var steps = new[] { new Vector3Int(1, 0, 0), new Vector3Int(-1, 0, 0), new Vector3Int(0, 1, 0), new Vector3Int(0, -1, 0) };
            while (queue.Count > 0)
            {
                var cell = queue.Dequeue();
                if (network.Contains(cell))
                {
                    var route = new List<Vector3Int>();
                    for (var c = cell; ; c = previous[c])
                    {
                        route.Add(c);
                        if (c == goal) break;
                    }
                    return route;
                }
                foreach (var step in steps)
                {
                    var next = cell + step;
                    if (previous.ContainsKey(next)) continue;
                    if (Math.Abs(next.x - origin.x) > radius || Math.Abs(next.y - origin.y) > radius) continue;
                    if (!_terrainService.Contains(new Vector2Int(next.x, next.y))) continue;
                    if (!network.Contains(next) && !paths.Contains(next) && !HasPath(next) && !CanPlace(placer, next)) continue;
                    previous[next] = cell;
                    queue.Enqueue(next);
                }
            }
            return null;
        }

        /// <summary>
        /// Places buildings on the district center's terrace (same height, so a path can reach them), at least 2 tiles apart,
        /// checked with the game's own placement validation. Nothing is ever deleted (deleting and re-placing during the same
        /// frame left objects that failed validation when the save was loaded).
        /// </summary>
        public string PlaceOnDistrictLevel(DistrictCenter center, IEnumerable<KeyValuePair<string, bool>> buildings, int radius = 30)
        {
            var origin = center.GetComponent<BlockObject>().PositionedEntrance.Coordinates;
            var used = new List<Vector3Int>();
            int placed = 0, failed = 0;
            var failures = new List<string>();
            foreach (var request in buildings)
            {
                var spec = _templateService.GetAll<PlaceableBlockObjectSpec>().FirstOrDefault(s => s.GetSpec<TemplateSpec>()?.TemplateName == request.Key);
                if (spec == null) { failed++; failures.Add(request.Key + " (not available)"); continue; }
                var placer = _previewPlacerFactory.Create(spec);
                bool done = false;
                try
                {
                    for (int r = 4; r <= radius && !done; r++)
                        for (int dx = -r; dx <= r && !done; dx++)
                            for (int dy = -r; dy <= r && !done; dy++)
                            {
                                if (Math.Max(Math.Abs(dx), Math.Abs(dy)) != r) continue;
                                var cell = new Vector3Int(origin.x + dx, origin.y + dy, origin.z);
                                if (!_terrainService.Contains(new Vector2Int(cell.x, cell.y))) continue;
                                if (_terrainService.GetTerrainHeightBelow(new Vector3Int(cell.x, cell.y, cell.z + 4)) != origin.z) continue;
                                if (used.Any(u => Math.Abs(u.x - cell.x) < 4 && Math.Abs(u.y - cell.y) < 4)) continue;
                                if (!ClearAround(cell, 1)) continue;   // keeps entrances off bushes and trees
                                foreach (var o in new[] { Orientation.Cw0, Orientation.Cw90, Orientation.Cw180, Orientation.Cw270 })
                                {
                                    var placement = placer.GetBuildableCoordinates(new[] { new Placement(cell, o, FlipMode.Unflipped) }).FirstOrDefault();
                                    if (placement.Coordinates != cell) continue;
                                    var builder = new EntitySetup.Builder(spec.Blueprint);
                                    if (request.Value) _constructionFactory.CreateAsFinished(builder, placement);
                                    else _constructionFactory.CreateAsUnfinished(builder, placement);
                                    used.Add(cell);
                                    placed++;
                                    done = true;
                                    break;
                                }
                            }
                }
                finally
                {
                    placer.HideAllPreviews();
                }
                if (!done) { failed++; failures.Add(request.Key); }
            }
            return "placed " + placed + ", not placed " + failed + (failures.Count > 0 ? " (" + string.Join(", ", failures) + ")" : "");
        }

        /// <summary>True when no object (bush, tree, building) stands within this many tiles at the cell's height.</summary>
        private bool ClearAround(Vector3Int cell, int margin)
        {
            for (int x = -margin; x <= margin; x++)
                for (int y = -margin; y <= margin; y++)
                {
                    var c = new Vector3Int(cell.x + x, cell.y + y, cell.z);
                    if (!_blockService.Contains(c) || _blockService.AnyObjectAt(c)) return false;
                    // same ground height all around, so the entrance tile is on the district's level too
                    if (_terrainService.GetTerrainHeightBelow(new Vector3Int(c.x, c.y, c.z + 4)) != c.z) return false;
                }
            return true;
        }

        private bool HasPath(Vector3Int cell)
        {
            if (!_blockService.Contains(cell)) return false;
            var path = _blockService.GetPathObjectAt(cell);
            return path != null && path.GetComponent<Timberborn.PathSystem.PathSpec>() != null;
        }

        private string Diagnose(PreviewPlacer placer, Vector3Int cell)
        {
            var parts = new List<string> { "terrain " + _terrainService.GetTerrainHeightBelow(new Vector3Int(cell.x, cell.y, cell.z + 4)) };
            for (int dz = -1; dz <= 1; dz++)
            {
                var c = new Vector3Int(cell.x, cell.y, cell.z + dz);
                if (!_blockService.Contains(c)) continue;
                var objects = _blockService.GetObjectsAt(c);
                parts.Add("z" + c.z + ":" + (CanPlace(placer, c) ? "ok" : "no") + (HasPath(c) ? "+path" : "")
                          + (objects.Count > 0 ? "[" + string.Join("|", objects.Select(o => o.GetComponent<TemplateSpec>()?.TemplateName)) + "]" : ""));
            }
            return string.Join(" ", parts);
        }

        private bool CanPlace(PreviewPlacer placer, Vector3Int cell)
        {
            if (_blocked.Contains(cell) || !_blockService.Contains(cell) || _blockService.AnyObjectAt(cell)) return false;
            // the preview check accepted paths floating one tile above lower ground; those fail validation when the save is
            // loaded (deleted with a loading-issue dialog), so only ground-level cells are allowed
            if (_terrainService.GetTerrainHeightBelow(new Vector3Int(cell.x, cell.y, cell.z + 4)) != cell.z) return false;
            return placer.GetBuildableCoordinates(new[] { new Placement(cell, Orientation.Cw0, FlipMode.Unflipped) }).Any();
        }

        private readonly HashSet<Vector3Int> _blocked = new HashSet<Vector3Int>();

        private bool Place(PlaceableBlockObjectSpec spec, Vector3Int cell, HashSet<Vector3Int> paths)
        {
            try { PlaceUnchecked(spec, cell, paths); return true; }
            catch (Exception e) { Debug.LogWarning("[Pandaborn.Ringtails] path at " + cell + " not placed: " + e.Message); return false; }
        }

        private void PlaceUnchecked(PlaceableBlockObjectSpec spec, Vector3Int cell, HashSet<Vector3Int> paths)
        {
            _constructionFactory.CreateAsFinished(new EntitySetup.Builder(spec.Blueprint), new Placement(cell, Orientation.Cw0, FlipMode.Unflipped));
            paths.Add(cell);
        }
    }
}
