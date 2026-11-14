using System.Collections.Immutable;
using Timberborn.BlueprintSystem;

namespace Pandaborn.Specs
{
    /// <summary>
    /// Gives an entity the Core per-entity save carrier (Pandaborn.Core.PandabornEntityState): versioned text entries
    /// keyed by feature, saved with the entity and kept unchanged while their feature is off. Put it on every
    /// Inkpaws-only template whose entities a feature module keeps saved state for (characters, buildings, plants).
    /// The carrier itself is always loaded, so the entity's data survives a save made with the feature off.
    /// </summary>
    public record PandabornEntityStateSpec : ComponentSpec
    {
        /// <summary>Informational: the features expected to keep state here (not enforced; any feature may write).</summary>
        [Serialize]
        public ImmutableArray<string> Features { get; init; }
    }
}
