using System.Collections.Immutable;
using Timberborn.BaseComponentSystem;
using Timberborn.BlockSystem;
using Timberborn.BlueprintSystem;
using Timberborn.WaterSystem;
using UnityEngine;

namespace Pandaborn.Water
{
    /// <summary>
    /// A flume segment: every cell in <see cref="FlowCells"/> (local block coordinates) gets a direction limiter along the
    /// building's orientation, so water there only moves along the arrow and both side faces are watertight. The cell
    /// must be a water-column floor (terrain, or a horizontal obstacle at its own z from the same blueprint).
    /// <see cref="InflowLimit"/> &gt; 0 also caps the flow into the first cell (a fixed-rate intake gate); -1 = none.
    /// </summary>
    public record PandabornFlumeSegmentSpec : ComponentSpec
    {
        [Serialize]
        public ImmutableArray<Vector3Int> FlowCells { get; init; }

        [Serialize]
        public float InflowLimit { get; init; }
    }

    /// <summary>
    /// Applies the limiters when the building is finished (also on load: the game does not save limiter arrays) and
    /// removes them when it is demolished. Not tickable and saves nothing.
    /// </summary>
    public class FlumeSegment : BaseComponent, IAwakableComponent, IFinishedStateListener
    {
        private readonly IWaterService _waterService;
        private BlockObject _blockObject;
        private PandabornFlumeSegmentSpec _spec;
        private bool _applied;

        public FlumeSegment(IWaterService waterService)
        {
            _waterService = waterService;
        }

        public void Awake()
        {
            _blockObject = GetComponent<BlockObject>();
            _spec = GetComponent<PandabornFlumeSegmentSpec>();
        }

        public void OnEnterFinishedState()
        {
            if (_applied) return;
            var direction = _blockObject.Orientation.ToFlowDirection();
            for (int i = 0; i < _spec.FlowCells.Length; i++)
            {
                var cell = _blockObject.TransformCoordinates(_spec.FlowCells[i]);
                _waterService.AddDirectionLimiter(cell, direction);
                if (i == 0 && _spec.InflowLimit > 0f) _waterService.SetInflowLimit(cell, _spec.InflowLimit);
            }
            _applied = true;
        }

        public void OnExitFinishedState()
        {
            if (!_applied) return;
            for (int i = 0; i < _spec.FlowCells.Length; i++)
            {
                var cell = _blockObject.TransformCoordinates(_spec.FlowCells[i]);
                _waterService.RemoveDirectionLimiter(cell);
                if (i == 0 && _spec.InflowLimit > 0f) _waterService.RemoveInflowLimit(cell);
            }
            _applied = false;
        }
    }
}
