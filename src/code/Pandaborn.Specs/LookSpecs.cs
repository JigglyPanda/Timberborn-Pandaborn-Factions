using System.Collections.Immutable;
using Timberborn.BlueprintSystem;

namespace Pandaborn.Specs
{
    /// <summary>
    /// The faction's building look. Placed on the faction blueprint (Factions/Pandaborn/Faction.Inkpaws), which only the
    /// Inkpaws use, so its presence is what makes a game a re-themed game. Read by Pandaborn.Look: in such a game every
    /// material of the named collections is copied into the loaded material of the same name (for example our
    /// "BaseWood_Brown.Folktails" into the vanilla one), so every model that uses it is re-themed. The collections are not
    /// listed by the faction itself. Without the module, or without the asset bundle, the faction keeps the vanilla look.
    /// </summary>
    public record PandabornLookSpec : ComponentSpec
    {
        /// <summary>Material collection ids whose materials replace the same-named loaded materials, e.g. "PandabornLook.Inkpaws".</summary>
        [Serialize]
        public ImmutableArray<string> MaterialCollectionIds { get; init; }
    }
}
