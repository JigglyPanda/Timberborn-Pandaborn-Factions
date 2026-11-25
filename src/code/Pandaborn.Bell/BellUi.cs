using System.Globalization;
using Pandaborn.Core;
using Timberborn.BaseComponentSystem;
using Timberborn.CoreUI;
using Timberborn.EntityPanelSystem;
using Timberborn.Localization;
using Timberborn.SingletonSystem;
using Timberborn.TooltipSystem;
using Timberborn.UILayoutSystem;
using Timberborn.WorkSystem;
using UnityEngine.UIElements;

namespace Pandaborn.Bell
{
    /// <summary>
    /// A line under the vanilla working-hours panel: "Rested +33%", or "Rested +33%, tomorrow +0%" while the slider differs
    /// from the hours locked at dawn, with a tooltip that explains the rule. It is a second copy of the vanilla panel's
    /// layout (Game/WorkingHoursPanel) with the buttons hidden, inserted right after the vanilla panel; the vanilla panel
    /// itself is not touched. Wrapped by SafeUi: if the layout changes in an update, the line disappears and nothing else.
    /// </summary>
    public class BellHoursHint : ILoadableSingleton, IUpdatableSingleton
    {
        private const string Piece = "Bell.HoursHint";
        private readonly BellService _bellService;
        private readonly UILayout _uiLayout;
        private readonly VisualElementLoader _visualElementLoader;
        private readonly ITooltipRegistrar _tooltipRegistrar;
        private readonly EventBus _eventBus;
        private readonly ILoc _loc;
        private bool _primaryUiShown;
        private bool _added;
        private Label _text;

        public BellHoursHint(BellService bellService, UILayout uiLayout, VisualElementLoader visualElementLoader, ITooltipRegistrar tooltipRegistrar,
                             EventBus eventBus, ILoc loc)
        {
            _bellService = bellService;
            _uiLayout = uiLayout;
            _visualElementLoader = visualElementLoader;
            _tooltipRegistrar = tooltipRegistrar;
            _eventBus = eventBus;
            _loc = loc;
        }

        /// <summary>The text currently shown (for tests).</summary>
        public static string ShownText { get; private set; }

        public void Load()
        {
            if (!_bellService.Active) return;
            _eventBus.Register(this);
            _bellService.Changed += UpdateText;
        }

        [OnEvent]
        public void OnShowPrimaryUI(ShowPrimaryUIEvent e) => _primaryUiShown = true;

        [OnEvent]
        public void OnWorkingHoursChanged(WorkingHoursChangedEvent e) => UpdateText();

        /// <summary>Adds the line one frame after the interface appears, so it lands after the vanilla panel (same order).</summary>
        public void UpdateSingleton()
        {
            if (_added || !_primaryUiShown || !_bellService.Active) return;
            _added = true;
            SafeUi.Run(Piece, () =>
            {
                var root = _visualElementLoader.LoadVisualElement("Game/WorkingHoursPanel");
                root.name = "PandabornBellHint";
                root.Q<Button>("Minus").style.display = DisplayStyle.None;
                root.Q<Button>("Plus").style.display = DisplayStyle.None;
                _text = root.Q<Label>("Text");
                _tooltipRegistrar.RegisterUpdatable(root, Tooltip);
                _uiLayout.AddTopRight(root, 3);
                UpdateText();
            });
        }

        private void UpdateText()
        {
            if (_text == null) return;
            SafeUi.Run(Piece, () =>
            {
                int locked = _bellService.LockedHours, slider = _bellService.SliderHours;
                string today = BellService.Pct(_bellService.WorkingBonus);
                string text = slider == locked
                    ? _loc.T("Pandaborn.Bell.PanelText", today)
                    : _loc.T("Pandaborn.Bell.PanelTextTomorrow", today, BellService.Pct(_bellService.WorkingBonusAt(slider)));
                _text.text = text;
                ShownText = text;
            });
        }

        private string Tooltip() => SafeUi.Get(Piece + ".Tooltip", () => _loc.T("Pandaborn.Bell.Tooltip",
            _bellService.LockedHours.ToString(CultureInfo.InvariantCulture), BellService.Pct(_bellService.WorkingBonus),
            BellService.Pct(_bellService.MovementBonus)), "");
    }

    /// <summary>
    /// A line on an Inkpaw's panel, next to the vanilla wellbeing bonuses (whose totals already include the rested bonus):
    /// "Rested (12 h day): working and walking speed x1.33". Reuses the vanilla carried-goods line's layout.
    /// </summary>
    public class BellColonistFragment : IEntityPanelFragment
    {
        private const string Piece = "Bell.ColonistFragment";
        private readonly VisualElementLoader _visualElementLoader;
        private readonly BellService _bellService;
        private readonly ILoc _loc;
        private VisualElement _root;
        private Label _label;
        private BellRestedBonus _bonus;
        private BellNightRestedBonus _nightBonus;   // a Ringtail: the same line, by its night shift

        public BellColonistFragment(VisualElementLoader visualElementLoader, BellService bellService, ILoc loc)
        {
            _visualElementLoader = visualElementLoader;
            _bellService = bellService;
            _loc = loc;
        }

        public static string ShownText { get; private set; }

        public VisualElement InitializeFragment()
        {
            _root = SafeUi.Get(Piece, () =>
            {
                var root = _visualElementLoader.LoadVisualElement("Game/EntityPanel/GoodCarrierFragment");
                _label = root.Q<Label>("GoodCarrierFragment");
                root.ToggleDisplayStyle(false);
                return root;
            }, null) ?? new VisualElement();
            return _root;
        }

        public void ShowFragment(BaseComponent entity)
        {
            _bonus = SafeUi.Get(Piece, () => entity.GetComponent<BellRestedBonus>(), null);
            _nightBonus = _bonus == null ? SafeUi.Get(Piece, () => entity.GetComponent<BellNightRestedBonus>(), null) : null;
        }

        public void ClearFragment()
        {
            _bonus = null;
            _nightBonus = null;
            SafeUi.Run(Piece, () => _root.ToggleDisplayStyle(false));
        }

        public void UpdateFragment()
        {
            SafeUi.Run(Piece, () =>
            {
                bool night = _nightBonus != null && _nightBonus.IsActive;
                bool show = ((_bonus != null && _bonus.IsActive) || night) && _label != null;
                _root.ToggleDisplayStyle(show);
                if (!show) return;
                // {0} = the length of the shift the bonus comes from: the working day for an Inkpaw, the night for a Ringtail
                string text = night
                    ? _loc.T("Pandaborn.Bell.ColonistLine", ((int)System.Math.Round(_nightBonus.ShiftHours)).ToString(CultureInfo.InvariantCulture),
                             BellService.Pct(_nightBonus.WorkingFactor), BellService.Pct(_nightBonus.MovementFactor))
                    : _loc.T("Pandaborn.Bell.ColonistLine", _bellService.LockedHours.ToString(CultureInfo.InvariantCulture),
                             BellService.Pct(_bellService.WorkingBonus), BellService.Pct(_bellService.MovementBonus));

                _label.text = text;
                ShownText = text;
            });
        }
    }
}
