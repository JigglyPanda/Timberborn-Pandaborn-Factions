using Pandaborn.Specs;
using Timberborn.BaseComponentSystem;
using Timberborn.Beavers;
using Timberborn.Characters;
using Timberborn.LifeSystem;
using Timberborn.TickSystem;

namespace Pandaborn.Ringtails
{
    /// <summary>
    /// Makes a Ringtail kit grow into a Ringtail adult. Vanilla growth (Child.GrowUp) always makes the faction's single
    /// adult template, an Inkpaw. Vanilla only grows a child once GrowthProgress reaches 1.0, and only from inside its
    /// behaviour (ChildRootBehavior); this acts a little earlier, at 0.995, so vanilla never gets there. No private field.
    /// The adult's CharacterInit carries the kit, so Adult.InitializeEntity hands over the selection and destroys the kit
    /// exactly as it does for vanilla growth.
    /// </summary>
    public class RingtailGrowth : TickableComponent, IAwakableComponent
    {
        private const float GrowUpAt = 0.995f;
        private readonly RingtailService _ringtailService;
        private Child _child;
        private Character _character;
        private LifeProgressor _lifeProgressor;
        private bool _grownUp;

        public RingtailGrowth(RingtailService ringtailService)
        {
            _ringtailService = ringtailService;
        }

        public void Awake()
        {
            _child = GetComponent<Child>();
            _character = GetComponent<Character>();
            _lifeProgressor = GetComponent<LifeProgressor>();
            if (_child == null) DisableComponent();   // adults: nothing to do
        }

        public override void Tick()
        {
            if (_grownUp || _child == null || _child.GrowthProgress < GrowUpAt || !_character.Alive) return;
            if (!_ringtailService.Enabled) return;   // feature off: vanilla growth makes an Inkpaw, which is the safe fallback
            _grownUp = true;   // one attempt only
            float lifeProgress = _lifeProgressor ? _lifeProgressor.LifeProgress : 0f;
            // As vanilla Child.GrowUp: hide the kit, create the adult, whose Adult.InitializeEntity destroys the kit. If the
            // adult cannot be created the kit must not stay hidden for ever: show it again and leave it to vanilla growth
            // (an Inkpaw adult at 1.0), the same fallback as with the feature off.
            Character adult = null;
            try
            {
                GameObject.SetActive(false);
                adult = _ringtailService.CreateAdultFromChild(_character, lifeProgress);
            }
            catch (System.Exception e)
            {
                UnityEngine.Debug.LogError("[Pandaborn.Ringtails] a kit could not grow into a Ringtail; it will grow up as an Inkpaw: " + e);
            }
            if (!adult && this && _character.Alive)
            {
                try { GameObject.SetActive(true); }
                catch (System.Exception) { }
            }
        }

    }
}
