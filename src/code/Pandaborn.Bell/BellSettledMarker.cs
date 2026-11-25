using Timberborn.BaseComponentSystem;
using Timberborn.BlockSystem;
using Timberborn.EntitySystem;

namespace Pandaborn.Bell
{
    /// <summary>
    /// Decorates PandabornBellSettledMarkerSpec (hammock, teahouse): when the first such building is finished, the bell
    /// posts its one-time suggestion. Without the module the building is just its vanilla basis.
    /// </summary>
    public class BellSettledMarker : BaseComponent, IFinishedStateListener
    {
        private readonly BellService _bellService;

        public BellSettledMarker(BellService bellService)
        {
            _bellService = bellService;
        }

        public void OnEnterFinishedState()
        {
            // the game treats an exception in a finished-state listener as a failed load: never let one out
            string what = "a leisure building was finished";
            try
            {
                var label = GetComponent<LabeledEntity>();
                if (label != null) what = "finished " + label.DisplayName;
            }
            catch (System.Exception) { }
            _bellService.OnSettledBuildingFinished(what);
        }

        public void OnExitFinishedState()
        {
        }
    }
}
