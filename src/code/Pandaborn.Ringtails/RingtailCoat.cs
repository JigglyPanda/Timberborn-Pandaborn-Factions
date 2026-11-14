using Pandaborn.Specs;
using Timberborn.BaseComponentSystem;
using Timberborn.Characters;
using Timberborn.Common;
using Timberborn.EntitySystem;
using UnityEngine;

namespace Pandaborn.Ringtails
{
    /// <summary>
    /// Puts a Ringtail coat on the body. The vanilla BeaverTextureSetter sets a faction coat in InitializeEntity; this runs
    /// later (PostInitializeEntity) and replaces it. Like the vanilla coat it is picked again on every load.
    /// </summary>
    public class RingtailCoat : BaseComponent, IAwakableComponent, IPostInitializableEntity
    {
        private static readonly int BaseMapId = Shader.PropertyToID("_BaseMap");
        private readonly IRandomNumberGenerator _randomNumberGenerator;
        private PandabornRingtailSpec _spec;

        public string CoatName { get; private set; }

        public RingtailCoat(IRandomNumberGenerator randomNumberGenerator)
        {
            _randomNumberGenerator = randomNumberGenerator;
        }

        public void Awake()
        {
            _spec = GetComponent<PandabornRingtailSpec>();
        }

        public void PostInitializeEntity()
        {
            if (_spec == null || _spec.Textures.IsDefaultOrEmpty) return;
            var texture = _spec.Textures[_randomNumberGenerator.Range(0, _spec.Textures.Length)].Asset;
            if (!texture) return;
            GetComponent<CharacterMaterialModifier>().SetTexture(BaseMapId, texture);
            CoatName = texture.name;
        }
    }
}
