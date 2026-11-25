using Bindito.Core;
using Pandaborn.Core;
using Pandaborn.Specs;
using Timberborn.BaseComponentSystem;
using Timberborn.BlockSystem;
using Timberborn.EntitySystem;
using Timberborn.TemplateInstantiation;
using Timberborn.WorkSystem;
using UnityEngine;

namespace Pandaborn.RingtailsFallback
{
    [Context("Game")]
    public class RingtailsFallbackConfigurator : Configurator
    {
        protected override void Configure()
        {
            Bind<NightPostFallback>().AsTransient();
            MultiBind<TemplateModule>().ToProvider(() =>
            {
                var builder = new TemplateModule.Builder();
                builder.AddDecorator<PandabornNightPostSpec, NightPostFallback>();
                return builder.Build();
            }).AsSingleton();
        }
    }

    /// <summary>
    /// The data-alone rule for night posts: when the Ringtails module is off (failed its API check, forced off) or degraded
    /// (failed its private-member check), a night post that a save left on the Ringtail worker type is switched back to the
    /// vanilla Beaver type with the public WorkplaceWorkerType.SetWorkerType, so it becomes an ordinary Inkpaw-staffed
    /// workplace instead of a dead building. (Saved Ringtails load as Inkpaws through the template alias in data.) When the
    /// Ringtails module is on, this does nothing.
    /// </summary>
    public class NightPostFallback : BaseComponent, IAwakableComponent, IPostInitializableEntity, IFinishedStateListener
    {
        public const string RingtailWorkerType = "PandabornRingtail";
        public const string BeaverWorkerType = "Beaver";
        private WorkplaceWorkerType _workerType;
        private BlockObject _blockObject;

        public static int Switched { get; private set; }

        public void Awake()
        {
            _workerType = GetComponent<WorkplaceWorkerType>();
            _blockObject = GetComponent<BlockObject>();
        }

        private static bool RingtailsWorking =>
            FeatureRegistry.IsOn("Ringtails") && !FeatureRegistry.Degraded.ContainsKey("Ringtails");

        public void PostInitializeEntity()
        {
            if (_blockObject != null && _blockObject.IsFinished) Release();
        }

        public void OnEnterFinishedState() => Release();

        public void OnExitFinishedState() { }

        private void Release()
        {
            // called from the building's load and finished-state steps, where an exception fails the load: contain it (the
            // post then keeps the Ringtail type and stands idle, which is what would have happened without this module)
            try
            {
                if (RingtailsWorking || _workerType == null || _workerType.WorkerType != RingtailWorkerType) return;
                _workerType.SetWorkerType(BeaverWorkerType);
                Switched++;
                Debug.Log("[Pandaborn.RingtailsFallback] night post " + Name + " switched to Inkpaw workers (Ringtails off)");
            }
            catch (System.Exception e)
            {
                Debug.LogError("[Pandaborn.RingtailsFallback] night post " + Name + " could not be switched to Inkpaw workers: " + e);
            }
        }

    }
}
