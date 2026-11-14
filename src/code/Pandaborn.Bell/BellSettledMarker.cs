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
            var label = GetComponent<LabeledEntity>();
            _bellService.OnSettledBuildingFinished(label != null ? "finished " + label.DisplayName : "a leisure building was finished");
        }

        public void OnExitFinishedState()
        {
        }
    }
}
