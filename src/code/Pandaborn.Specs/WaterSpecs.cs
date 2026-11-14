using System.Collections.Immutable;
using Timberborn.BlueprintSystem;
using UnityEngine;

namespace Pandaborn.Specs
{
    /// <summary>
    /// Water module (Pandaborn.Water): a flume piece. Every cell in <see cref="FlowCells"/> (local block coordinates) is
    /// direction-limited along the building's orientation, so water there only moves along the arrow and both side faces
    /// are watertight. Each flow cell must be a water-column floor (terrain, or a horizontal obstacle at its own z).
    /// Data contract for the module-off case: the piece also carries a vanilla full water obstacle over its flow cells
    /// (WaterObstacleSpec + FinishableWaterObstacleSpec), which makes it an inert block that holds no water; the module
    /// lifts it through the vanilla WaterObstacle component once the limiters are in place.
    /// </summary>
    public record PandabornFlumeSegmentSpec : ComponentSpec
    {
        [Serialize]
        public ImmutableArray<Vector3Int> FlowCells { get; init; }
    }

    /// <summary>
    /// Water module: full water obstacles at arbitrary local cells, added by the module only (a cap one block above a
    /// lidded piece, gate, corner or spout, so water backed up in an open flume cannot run over its top; the solid leg of
    /// a Flume Drop). Vanilla's WaterObstacleSpec can only stack obstacles from the base up.
    /// </summary>
    public record PandabornSolidCellsSpec : ComponentSpec
    {
        [Serialize]
        public ImmutableArray<Vector3Int> Cells { get; init; }
    }

    /// <summary>
    /// Water module: a Flume Gate (on a piece that also has PandabornFlumeSegmentSpec). Its first flow cell lets through at
    /// most the player's flow setting (saved per gate in the entity state), and shuts while the water behind it is
    /// contaminated above <see cref="ContaminationShutoff"/> (if the player leaves that switch on). Flows are the
    /// game's water units per second; the panel shows them in plain words.
    /// </summary>
    public record PandabornFlumeGateSpec : ComponentSpec
    {
        [Serialize]
        public float DefaultFlow { get; init; }

        [Serialize]
        public float MaxFlow { get; init; }

        [Serialize]
        public float FlowStep { get; init; }

        [Serialize]
        public float ContaminationShutoff { get; init; }
    }

    /// <summary>Water module: production efficiency of a workerless Dew Collector by weather.</summary>
    public record PandabornDewLimiterSpec : ComponentSpec
    {
        [Serialize]
        public float TemperateEfficiency { get; init; }

        [Serialize]
        public float DroughtEfficiency { get; init; }
    }

    /// <summary>
    /// Water module: a building powered by the current at its own wheel (Scoop Wheel, Water Trip-Hammer): a panel line
    /// with the current in plain words and a status when the current is too weak. The mechanics are vanilla data (one
    /// mechanical node that is both WaterPoweredGenerator and consumer, no transputs).
    /// </summary>
    public record PandabornCurrentDrivenSpec : ComponentSpec
    {
    }

    /// <summary>Water module: a Paddy Spout (vanilla fill valve): a panel line with the depth it keeps and the depth now.</summary>
    public record PandabornPaddySpoutSpec : ComponentSpec
    {
    }

    /// <summary>Water module: a Treadwheel Lift (vanilla walker generator + pump on one node): a panel line in plain words.</summary>
    public record PandabornTreadwheelSpec : ComponentSpec
    {
    }

    /// <summary>Water module: a Cistern Tap (vanilla water dump with its worker): a panel line in plain words.</summary>
    public record PandabornCisternTapSpec : ComponentSpec
    {
    }
}
