using System.Collections.Immutable;
using Timberborn.BlueprintSystem;

namespace Pandaborn.Specs
{
    // The two signature events (DESIGN.md, Pillar 5). Read by Pandaborn.Festival and Pandaborn.Flowering; design and
    // test results in docs/tech/events.md. Every spec here goes only on Inkpaws-only templates (data rule 1).

    /// <summary>
    /// The Lantern Festival's rules. On the faction's adult character template (Inkpaws only): its presence makes a game a
    /// festival game, as PandabornBellSpec does for the bell. Every number is data.
    /// </summary>
    public record PandabornFestivalSpec : ComponentSpec
    {
        /// <summary>Paper lanterns needed for any festival.</summary>
        [Serialize]
        public string LanternGoodId { get; init; } = "PandabornPaperLantern";

        [Serialize]
        public int Lanterns { get; init; } = 40;

        /// <summary>The goods that count as cooked dishes. A festival needs DishKinds of them with DishAmount each.</summary>
        [Serialize]
        public ImmutableArray<string> Dishes { get; init; }

        [Serialize]
        public int DishKinds { get; init; } = 3;

        [Serialize]
        public int DishAmount { get; init; } = 20;

        /// <summary>With this many fireworks in store as well, the festival is a Grand Festival. 0 or an empty id: no Grand.</summary>
        [Serialize]
        public string FireworksGoodId { get; init; } = "Fireworks";

        [Serialize]
        public int Fireworks { get; init; } = 20;

        /// <summary>Set to its maximum for every colonist by any festival (+4 wellbeing, decays over about 20 days).</summary>
        [Serialize]
        public string FestiveNeedId { get; init; } = "PandabornFestive";

        /// <summary>Set to its maximum as well by a Grand Festival. Empty, or a need the faction lacks: nothing.</summary>
        [Serialize]
        public string GrandNeedId { get; init; } = "";

        /// <summary>Workplaces whose crews keep working through the festival (template names): the ones that keep water
        /// reaching people and fields.</summary>
        [Serialize]
        public ImmutableArray<string> KeepWorkingTemplates { get; init; }

        /// <summary>Hours after dawn when everyone gathers at the square for the lanterns (nightfall is 16).</summary>
        [Serialize]
        public float ShowStartHours { get; init; } = 15.5f;

        /// <summary>Hours after dawn when the gathering ends and colonists go about their night.</summary>
        [Serialize]
        public float ShowEndHours { get; init; } = 22f;

        /// <summary>Hours after dawn when the fireworks of a Grand Festival start.</summary>
        [Serialize]
        public float FireworksStartHours { get; init; } = 19f;

        /// <summary>Rising lanterns per square (drawn with the vanilla trail-only "comet" fireworks until the art exists).</summary>
        [Serialize]
        public int LanternRises { get; init; } = 24;

        [Serialize]
        public ImmutableArray<string> LanternFireworkIds { get; init; }

        [Serialize]
        public ImmutableArray<string> BurstFireworkIds { get; init; }

        /// <summary>Bursts per square in a Grand Festival.</summary>
        [Serialize]
        public int Bursts { get; init; } = 20;
    }

    /// <summary>Marks the Festival Square, where the festival is called and celebrated. Without the module the building is
    /// whatever its vanilla basis is (a village square attraction).</summary>
    public record PandabornFestivalSquareSpec : ComponentSpec
    {
    }

    /// <summary>Marks a colonist template that takes part in festivals (Inkpaw adult and cub, Ringtail adult and kit).</summary>
    public record PandabornFestivalGoerSpec : ComponentSpec
    {
    }

    /// <summary>
    /// On a decoration: buildable only once the village's Tradition (one step per Lantern Festival) reaches Level. The
    /// building's ScienceCost must be 0 (the game allows one lock per tool). Without the module it is simply buildable.
    /// </summary>
    public record PandabornTraditionSpec : ComponentSpec
    {
        [Serialize]
        public int Level { get; init; } = 1;
    }

    /// <summary>
    /// The Great Flowering's schedule. On the faction's adult character template (Inkpaws only): its presence makes a game a
    /// Flowering game. Species flower in the order listed, alternating, one per Flowering.
    /// </summary>
    public record PandabornFloweringSpec : ComponentSpec
    {
        /// <summary>Plant template names, in flowering order (the first is the first to flower).</summary>
        [Serialize]
        public ImmutableArray<string> Species { get; init; }

        /// <summary>Never before this cycle (setting "normal"); the setting "rare" adds RareDelayCycles.</summary>
        [Serialize]
        public int FirstCycle { get; init; } = 6;

        [Serialize]
        public int NormalMinCycles { get; init; } = 5;

        [Serialize]
        public int NormalMaxCycles { get; init; } = 7;

        [Serialize]
        public int RareMinCycles { get; init; } = 9;

        [Serialize]
        public int RareMaxCycles { get; init; } = 11;

        [Serialize]
        public int RareDelayCycles { get; init; } = 3;

        /// <summary>Days the flowering plants hold their seed before they die.</summary>
        [Serialize]
        public float SeedDays { get; init; } = 3f;

        /// <summary>Days after the Flowering during which young plants of that species do not grow (counted from the
        /// Flowering; the gap without a harvest is this plus the plant's growth time).</summary>
        [Serialize]
        public float DormantDays { get; init; } = 9f;

        /// <summary>"normal", "rare" or "off" for a new game.</summary>
        [Serialize]
        public string DefaultSetting { get; init; } = "normal";
    }

    /// <summary>On a bamboo that can flower: the template it turns into while in flower (bearing seed, then dying).</summary>
    public record PandabornFloweringPlantSpec : ComponentSpec
    {
        [Serialize]
        public string InFlowerTemplate { get; init; }

        /// <summary>While a Flowering of this plant is announced, switch on the material's detail map on the grown model
        /// (the plant lane paints the buds there). False: no visible change before the Flowering.</summary>
        [Serialize]
        public bool BudsUseDetail { get; init; }
    }

    /// <summary>On the "in flower" twin of a bamboo: the species it came from. It bears seed (its cut yield) and dies
    /// SeedDays after the Flowering.</summary>
    public record PandabornInFlowerSpec : ComponentSpec
    {
        [Serialize]
        public string Species { get; init; }
    }
}
