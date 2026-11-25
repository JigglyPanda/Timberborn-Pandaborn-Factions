using System.Collections.Immutable;
using Timberborn.BlueprintSystem;
using UnityEngine;

namespace Pandaborn.Specs
{
    /// <summary>
    /// On the faction's adult character template (Inkpaws only): makes the game a Ringtails game and names the hidden Ringtail
    /// templates, which are in no template collection (so the vanilla BeaverFactory still finds one adult). Read by
    /// Pandaborn.Ringtails; no faction id is hard-coded.
    /// </summary>
    public record PandabornRingtailsSpec : ComponentSpec
    {
        [Serialize]
        public string AdultBlueprint { get; init; } = "Characters/Pandaborn/RingtailAdult.Inkpaws.blueprint";

        [Serialize]
        public string ChildBlueprint { get; init; } = "Characters/Pandaborn/RingtailChild.Inkpaws.blueprint";

        /// <summary>The worker type night posts are switched to while the feature is on (data default: Beaver).</summary>
        [Serialize]
        public string WorkerType { get; init; } = "PandabornRingtail";

        /// <summary>The family the first Moon Loft brings.</summary>
        [Serialize]
        public int ArrivalAdults { get; init; } = 2;

        [Serialize]
        public int ArrivalKits { get; init; } = 1;

        /// <summary>A district that has a finished Moon Loft and no living Ringtail (old age took the last of them, or a
        /// session with the module off turned them into Inkpaws) gets a new family after this many dawns in a row without
        /// one, so the people can never die out for good and never refills at once. Less than 1 counts as 1.</summary>
        [Serialize]
        public int ReturnAfterDays { get; init; } = 3;
    }

    /// <summary>
    /// Marks a Ringtail character template (adult or kit). Drives the Ringtail decorators: coat, rest, growth, badge.
    /// </summary>
    public record PandabornRingtailSpec : ComponentSpec
    {
        [Serialize]
        public string Kind { get; init; } = "Ringtail";

        /// <summary>Coat textures (beaver UV layout), one picked at random on every load like the faction coats.</summary>
        [Serialize]
        public ImmutableArray<AssetRef<Texture2D>> Textures { get; init; }

        /// <summary>Panel portraits: adult, contaminated adult (kits use the Kit ones).</summary>
        [Serialize]
        public AssetRef<Sprite> Avatar { get; init; }

        [Serialize]
        public AssetRef<Sprite> ContaminatedAvatar { get; init; }

        /// <summary>The daily rest window starts this many hours after dawn.</summary>
        [Serialize]
        public float RestStartHours { get; init; }

        /// <summary>Used only when RestEndsAtBell is false.</summary>
        [Serialize]
        public float RestEndHours { get; init; } = 8f;

        /// <summary>The rest ends at the bell (end of the Inkpaw working day), clamped to [RestMinEndHours, RestMaxEndHours].</summary>
        [Serialize]
        public bool RestEndsAtBell { get; init; } = true;

        [Serialize]
        public float RestMinEndHours { get; init; } = 4f;

        [Serialize]
        public float RestMaxEndHours { get; init; } = 16f;

        /// <summary>Later in the rest window a Ringtail goes back to bed while Sleep is below this.</summary>
        [Serialize]
        public float SleepBelow { get; init; } = 0.55f;
    }

    /// <summary>
    /// Marks a night post (Night Builders' Post, Night Courier Post, Night Gatherers' Post): the data keeps the vanilla
    /// worker type (Beaver), so without the Ringtails feature it is an ordinary Inkpaw workplace; with the feature the module
    /// switches it to the Ringtail worker type. Carries a science cost in data; the Ringtails' arrival unlocks it for free.
    /// </summary>
    public record PandabornNightPostSpec : ComponentSpec
    {
        /// <summary>The arrival of the Ringtails unlocks this post for free (default). False keeps its science cost: the
        /// post is a Ringtail workplace like the others but the player still has to buy it (the Star Tower).</summary>
        [Serialize]
        public bool UnlockOnArrival { get; init; } = true;
    }


    /// <summary>
    /// Marks the Moon Loft. Without the feature it is an ordinary home (no ProcreationHouseSpec in data). With the feature:
    /// the first one finished brings the Ringtails; Ringtails are moved into lofts; lofts raise kits while night jobs are open.
    /// </summary>
    public record PandabornMoonLoftSpec : ComponentSpec
    {
        /// <summary>At most this many kits a loft raises per day (checked at dawn).</summary>
        [Serialize]
        public int KitsPerDay { get; init; } = 1;
    }
}
