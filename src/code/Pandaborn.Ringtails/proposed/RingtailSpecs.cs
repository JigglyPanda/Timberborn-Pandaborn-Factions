// PROPOSED for src/code/Pandaborn.Specs/RingtailSpecs.cs (owned by the code-foundation agent). Not compiled here.
using System.Collections.Immutable;
using Timberborn.BlueprintSystem;
using UnityEngine;

namespace Pandaborn.Specs
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

        /// <summary>
        /// When true the rest window ends at the bell (the end of the Inkpaw working hours, the working-hours slider),
        /// clamped to [RestMinEndHours, RestMaxEndHours] after dawn; RestEndHours is then ignored. The handover at the bell
        /// is the faction's pitch: Inkpaws stop, Ringtails start.
        /// </summary>
        [Serialize]
        public bool RestEndsAtBell { get; init; } = true;

        /// <summary>Earliest shift start: time to sleep after the night shift.</summary>
        [Serialize]
        public float RestMinEndHours { get; init; } = 4f;

        /// <summary>Latest shift start: nightfall, so Ringtails always hold the night.</summary>
        [Serialize]
        public float RestMaxEndHours { get; init; } = 16f;
    }

    /// <summary>
    /// On the faction's adult character template (Inkpaws only): makes the game a Ringtails game and names the hidden
    /// Ringtail templates, which are in no template collection. Read by Pandaborn.Ringtails; no faction id is hard-coded.
    /// </summary>
    public record PandabornRingtailsSpec : ComponentSpec
    {
        [Serialize]
        public string AdultBlueprint { get; init; } = "Characters/Pandaborn/RingtailAdult.Inkpaws.blueprint";

        [Serialize]
        public string ChildBlueprint { get; init; } = "Characters/Pandaborn/RingtailChild.Inkpaws.blueprint";
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
