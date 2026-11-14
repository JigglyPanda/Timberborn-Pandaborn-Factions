using System.Collections.Generic;
using System.Collections.Immutable;
using Timberborn.BaseComponentSystem;
using Timberborn.BlockSystem;
using Timberborn.BlueprintSystem;
using Timberborn.WaterSystem;
using UnityEngine;

namespace Pandaborn.Water
{
    /// <summary>
    /// Full water obstacles at arbitrary local cells (vanilla <c>WaterObstacleSpec</c> can only stack them from the base
    /// up). Used as a cap one block above lidded flume pieces, spouts, gates and corners, so water backed up more than
    /// one block deep in an open flume cannot run over their tops.
    /// </summary>
    public record PandabornSolidCellsSpec : ComponentSpec
    {
        [Serialize]
        public ImmutableArray<Vector3Int> Cells { get; init; }
    }

    public class SolidCells : BaseComponent, IAwakableComponent, IFinishedStateListener
    {
        private readonly IWaterService _waterService;
        private readonly List<Vector3Int> _added = new List<Vector3Int>();
        private BlockObject _blockObject;
        private PandabornSolidCellsSpec _spec;

        public SolidCells(IWaterService waterService)
        {
            _waterService = waterService;
        }

        public void Awake()
        {
            _blockObject = GetComponent<BlockObject>();
            _spec = GetComponent<PandabornSolidCellsSpec>();
        }

        public void OnEnterFinishedState()
        {
            if (_added.Count > 0) return;
            foreach (var c in _spec.Cells)
            {
                var cell = _blockObject.TransformCoordinates(c);
                _waterService.AddFullObstacle(cell);
                _added.Add(cell);
            }
        }

        public void OnExitFinishedState()
        {
            foreach (var cell in _added) _waterService.RemoveFullObstacle(cell);
            _added.Clear();
        }
    }
}
