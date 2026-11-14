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

        public PathConnector(TemplateService templateService, PreviewPlacerFactory previewPlacerFactory, ConstructionFactory constructionFactory,
                             ITerrainService terrainService, EntityRegistry entityRegistry)
        {
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
            var origin = center.CenterCoordinates;
            var paths = new HashSet<Vector3Int>();
            var network = new HashSet<Vector3Int> { origin };
            if (CanPlace(placer, origin)) Place(pathSpec, origin, paths);
            int connected = 0, failed = 0;
            var failures = new List<string>();
            try
            {
                var targets = _entityRegistry.Entities
                    .Select(e => e.GetComponent<BlockObject>())
                    .Where(b => b && b.HasEntrance && b.GetComponent<DistrictCenter>() == null && b.GetComponent<DistrictBuilding>() != null)
                    .OrderBy(b => (b.PositionedEntrance.DoorstepCoordinates - origin).sqrMagnitude)
                    .ToList();
                foreach (var target in targets)
                {
                    var goal = target.PositionedEntrance.DoorstepCoordinates;
                    var route = Search(placer, goal, network, paths, origin, radius);
                    if (route == null)
                    {
                        failed++;
                        failures.Add(target.GetComponent<TemplateSpec>()?.TemplateName);
                        continue;
                    }
                    foreach (var cell in route)
                    {
                        if (!paths.Contains(cell)) Place(pathSpec, cell, paths);
                        network.Add(cell);
                    }
                    connected++;
                }
            }
            finally
            {
                placer.HideAllPreviews();
            }
            return "connected " + connected + ", not connected " + failed + (failures.Count > 0 ? " (" + string.Join(", ", failures) + ")" : "")
                   + ", path tiles " + paths.Count;
        }

        private List<Vector3Int> Search(PreviewPlacer placer, Vector3Int goal, HashSet<Vector3Int> network, HashSet<Vector3Int> paths,
                                        Vector3Int origin, int radius)
        {
            if (network.Contains(goal)) return new List<Vector3Int>();
            if (!paths.Contains(goal) && !CanPlace(placer, goal)) return null;
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
                    if (!network.Contains(next) && !paths.Contains(next) && !CanPlace(placer, next)) continue;
                    previous[next] = cell;
                    queue.Enqueue(next);
                }
            }
            return null;
        }

        private static bool CanPlace(PreviewPlacer placer, Vector3Int cell)
        {
            return placer.GetBuildableCoordinates(new[] { new Placement(cell, Orientation.Cw0, FlipMode.Unflipped) }).Any();
        }

        private void Place(PlaceableBlockObjectSpec spec, Vector3Int cell, HashSet<Vector3Int> paths)
        {
            _constructionFactory.CreateAsFinished(new EntitySetup.Builder(spec.Blueprint), new Placement(cell, Orientation.Cw0, FlipMode.Unflipped));
            paths.Add(cell);
        }
    }
}
