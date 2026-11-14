using Timberborn.BlueprintSystem;

namespace Pandaborn.Specs
{
    /// <summary>
    /// A tutorial step (a child of a TutorialStageSpec blueprint, like the vanilla step specs): achieved while the
    /// settlement holds at least Amount of GoodId in its districts' available stock (stockpiled, in output buffers, or on
    /// its way to storage; ResourceCountingService.GetGlobalResourceCount(..).AvailableStock). Read by Pandaborn.Tutorial;
    /// with that module off the game drops the step and the stage keeps its other steps.
    /// </summary>
    public record PandabornGoodAmountStepSpec : ComponentSpec
    {
        [Serialize]
        public string GoodId { get; init; }

        [Serialize]
        public int Amount { get; init; } = 1;
    }
}