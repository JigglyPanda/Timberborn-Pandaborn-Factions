using System.Collections.Immutable;
using Timberborn.BlueprintSystem;

namespace Pandaborn.Specs
{
    /// <summary>
    /// The afternoon bell (DESIGN.md, Pillar 3). Placed on the faction's adult character template, which is listed only in
    /// Inkpaws collections, so its presence is what makes a game an "afternoon bell" game. Read by Pandaborn.Bell.
    /// Every number is data so the balance model can tune it without code.
    /// </summary>
    public record PandabornBellSpec : ComponentSpec
    {
        /// <summary>Working-speed bonus (multiplier delta) by length of the working day in hours. Piecewise linear between
        /// points, flat beyond the first and last point. Default: +0.33 at 12 h or fewer, tapering to 0 at 16 h.</summary>
        [Serialize]
        public ImmutableArray<PandabornBellPointSpec> WorkingSpeedCurve { get; init; }

        /// <summary>Movement-speed bonus by length of the working day, same shape as WorkingSpeedCurve.</summary>
        [Serialize]
        public ImmutableArray<PandabornBellPointSpec> MovementSpeedCurve { get; init; }

        /// <summary>The one-time suggestion is posted at the dawn of this day number, or earlier when the first building
        /// with PandabornBellSettledMarkerSpec is finished. 0 or less: never by day.</summary>
        [Serialize]
        public int SuggestionDay { get; init; } = 4;

        /// <summary>Loc key of the one-time suggestion.</summary>
        [Serialize]
        public string SuggestionLocKey { get; init; }
    }

    /// <summary>One point of a bell curve: at this many working hours a day, this bonus (0.33 = +33%).</summary>
    public record PandabornBellPointSpec
    {
        [Serialize]
        public float Hours { get; init; }

        [Serialize]
        public float Bonus { get; init; }
    }

    /// <summary>Marks a leisure building (hammock, teahouse) whose first completion means "the village is settled": the
    /// bell's one-time suggestion is posted then. Without Pandaborn.Bell it does nothing.</summary>
    public record PandabornBellSettledMarkerSpec : ComponentSpec
    {
    }
}
