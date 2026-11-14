using System.Collections.Immutable;
using Timberborn.BlueprintSystem;
using UnityEngine;

namespace Pandaborn.Ringtails
{
    /// <summary>
    /// Marks a character template as a Ringtail (the hidden second colonist kind of the Inkpaws faction).
    /// Spec type names are global across all loaded assemblies, hence the Pandaborn prefix.
    /// </summary>
    public record PandabornRingtailSpec : ComponentSpec
    {
        [Serialize]
        public string Kind { get; init; } = "Ringtail";

        /// <summary>Coat textures (beaver UV layout), one picked at random on every load like the faction coats.</summary>
        [Serialize]
        public ImmutableArray<AssetRef<Texture2D>> Textures { get; init; }

        /// <summary>The daily rest window, in hours after the start of daytime (dawn). Ringtails do not work inside it.</summary>
        [Serialize]
        public float RestStartHours { get; init; }

        [Serialize]
        public float RestEndHours { get; init; } = 8f;

        /// <summary>Inside the rest window a Ringtail goes to bed while its Sleep need is below this many points.</summary>
        [Serialize]
        public float SleepBelow { get; init; } = 0.55f;

        /// <summary>Net Hunger and Thirst rate as a fraction of the vanilla rate (light eaters).</summary>
        [Serialize]
        public float AppetiteFactor { get; init; } = 1f;
    }

    /// <summary>Marks a workplace that only Ringtails staff (its WorkplaceSpec says so too; this is for our own code and the UI).</summary>
    public record PandabornRingtailWorkplaceSpec : ComponentSpec
    {
    }

    /// <summary>Marks a dwelling as a loft, the Ringtails' kind of home.</summary>
    public record PandabornLoftSpec : ComponentSpec
    {
    }
}
