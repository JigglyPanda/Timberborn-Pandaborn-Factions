using Timberborn.BlueprintSystem;

namespace Pandaborn.Specs
{
    /// <summary>
    /// A faction's own colonist names. Placed on the faction's adult and child character templates (Inkpaws-only), read by
    /// Pandaborn.Names. The pool is one localisation entry, one name per line, like the vanilla Beaver.NamePool. A name may
    /// carry a gloss, e.g. "Le Le (Joy)". Without the module the vanilla pool is used.
    /// </summary>
    public record PandabornNamePoolSpec : ComponentSpec
    {
        [Serialize]
        public string NamePoolLocKey { get; init; }
    }
}
