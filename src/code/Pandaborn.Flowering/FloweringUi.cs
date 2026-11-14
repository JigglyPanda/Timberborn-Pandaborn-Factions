using System;
using System.Globalization;
using Pandaborn.Core;
using Timberborn.BaseComponentSystem;
using Timberborn.CoreUI;
using Timberborn.EntityPanelSystem;
using Timberborn.Localization;
using Timberborn.SingletonSystem;
using Timberborn.TooltipSystem;
using Timberborn.UILayoutSystem;
using UnityEngine.UIElements;

namespace Pandaborn.Flowering
{
    /// <summary>
    /// The per-save setting (normal, rare, off) in a game dialog: the setting needs no other mod. Opened from the line under
    /// the top bar and from any bamboo's panel. Three buttons in the vanilla dialog's own button style; OK closes.
    /// </summary>
    public class FloweringSettingDialog
    {
        private const string Piece = "Flowering.SettingDialog";
        private readonly DialogBoxShower _dialogBoxShower;
        private readonly FloweringService _floweringService;
        private readonly ILoc _loc;

        public FloweringSettingDialog(DialogBoxShower dialogBoxShower, FloweringService floweringService, ILoc loc)
        {
            _dialogBoxShower = dialogBoxShower;
            _floweringService = floweringService;
            _loc = loc;
        }

        public string SettingName(string setting) => _loc.T("Pandaborn.Flowering.Setting." + setting);

        public void Show()
        {
            SafeUi.Run(Piece, () =>
            {
                var message = new Label();
                message.style.whiteSpace = WhiteSpace.Normal;
                var row = new VisualElement();
                row.AddToClassList("content-row-centered");
                foreach (var setting in new[] { "normal", "rare", "off" })
                {
                    var button = new Button { text = SettingName(setting) };
                    button.AddToClassList("menu-button");
                    button.AddToClassList("menu-button--medium");
                    button.clicked += () => SafeUi.Run(Piece + ".Set", () =>
                    {
                        _floweringService.SetSetting(setting);
                        message.text = Title();
                    });
                    row.Add(button);
                }
                message.text = Title();
                var content = new VisualElement();
                content.Add(message);
                content.Add(row);
                _dialogBoxShower.Create().AddContent(content).SetConfirmButton(() => { }).Show();
            });
        }

        private string Title() => _loc.T("Pandaborn.Flowering.Setting.Title", SettingName(_floweringService.Setting));
    }

    /// <summary>
    /// A line under the top bar while a Flowering is announced, under way or resting: what flowers and when, with the
    /// preparation advice in its tooltip; a click opens the setting. A second copy of the vanilla working-hours panel's
    /// layout with its buttons hidden (as the bell's line), the vanilla panel untouched. Wrapped by SafeUi.
    /// </summary>
    public class FloweringIndicator : ILoadableSingleton, IUpdatableSingleton
    {
        private const string Piece = "Flowering.Indicator";
        private readonly FloweringService _floweringService;
        private readonly FloweringSettingDialog _settingDialog;
        private readonly UILayout _uiLayout;
        private readonly VisualElementLoader _visualElementLoader;
        private readonly ITooltipRegistrar _tooltipRegistrar;
        private readonly EventBus _eventBus;
        private readonly ILoc _loc;
        private bool _primaryUiShown;
        private bool _added;
        private VisualElement _root;
        private Label _text;
        private float _nextRefresh;

        public FloweringIndicator(FloweringService floweringService, FloweringSettingDialog settingDialog, UILayout uiLayout,
                                  VisualElementLoader visualElementLoader, ITooltipRegistrar tooltipRegistrar, EventBus eventBus, ILoc loc)
        {
            _floweringService = floweringService;
            _settingDialog = settingDialog;
            _uiLayout = uiLayout;
            _visualElementLoader = visualElementLoader;
            _tooltipRegistrar = tooltipRegistrar;
            _eventBus = eventBus;
            _loc = loc;
        }

        /// <summary>The text currently shown, empty when hidden (tests).</summary>
        public static string ShownText { get; private set; } = "";

        public void Load()
        {
            if (!_floweringService.Active) return;
            _eventBus.Register(this);
        }

        [OnEvent]
        public void OnShowPrimaryUI(ShowPrimaryUIEvent e) => _primaryUiShown = true;

        public void UpdateSingleton()
        {
            if (!_floweringService.Active || !_primaryUiShown) return;
            if (!_added)
            {
                _added = true;
                SafeUi.Run(Piece, () =>
                {
                    _root = _visualElementLoader.LoadVisualElement("Game/WorkingHoursPanel");
                    _root.name = "PandabornFloweringIndicator";
                    _root.Q<Button>("Minus").style.display = DisplayStyle.None;
                    _root.Q<Button>("Plus").style.display = DisplayStyle.None;
                    _text = _root.Q<Label>("Text");
                    _tooltipRegistrar.RegisterUpdatable(_root, Tooltip);
                    _root.RegisterCallback<ClickEvent>(_ => _settingDialog.Show());
                    _uiLayout.AddTopRight(_root, 4);
                });
            }
            if (_text == null || UnityEngine.Time.unscaledTime < _nextRefresh) return;
            _nextRefresh = UnityEngine.Time.unscaledTime + 0.5f;
            SafeUi.Run(Piece, Refresh);
        }

        private void Refresh()
        {
            var s = _floweringService;
            string name = s.PlantName(s.Species);
            string text = s.Phase switch
            {
                FloweringPhase.Announced => _loc.T("Pandaborn.Flowering.Indicator.Announced", name, s.NextCycle.ToString(CultureInfo.InvariantCulture)),
                FloweringPhase.Flowering => _loc.T("Pandaborn.Flowering.Indicator.InFlower", name, FloweringService.Days(s.SeedDaysLeft)),
                FloweringPhase.Resting => _loc.T("Pandaborn.Flowering.Indicator.Dormant", name, FloweringService.Days(s.RestDaysLeft)),
                _ => ""
            };
            _root.ToggleDisplayStyle(text.Length > 0);
            _text.text = text;
            ShownText = text;
        }

        private string Tooltip() => SafeUi.Get(Piece + ".Tooltip", () =>
        {
            var s = _floweringService;
            string key = s.IsTimberSpecies(s.Species) ? "Pandaborn.Flowering.Tooltip.Timber" : "Pandaborn.Flowering.Tooltip.Shoot";
            return _loc.T(key, FloweringService.Days(s.Spec.SeedDays), FloweringService.Days(s.Spec.DormantDays));
        }, "");
    }

    /// <summary>
    /// A line on a bamboo's panel: how often bamboo flowers, or that this one is budding, in flower or resting; and a
    /// button with the setting. Built on the vanilla wonder fragment's layout (content root and a button underneath).
    /// </summary>
    public class FloweringPlantFragment : IEntityPanelFragment
    {
        private const string Piece = "Flowering.PlantFragment";
        private readonly VisualElementLoader _visualElementLoader;
        private readonly FloweringService _floweringService;
        private readonly FloweringSettingDialog _settingDialog;
        private readonly ILoc _loc;
        private VisualElement _root;
        private Label _label;
        private Button _button;
        private FloweringPlant _plant;
        private InFlowerPlant _inFlower;

        public FloweringPlantFragment(VisualElementLoader visualElementLoader, FloweringService floweringService, FloweringSettingDialog settingDialog, ILoc loc)
        {
            _visualElementLoader = visualElementLoader;
            _floweringService = floweringService;
            _settingDialog = settingDialog;
            _loc = loc;
        }

        public static string ShownText { get; private set; } = "";

        public VisualElement InitializeFragment()
        {
            _root = SafeUi.Get(Piece, () =>
            {
                // the wonder fragment's layout: a box with a content root and a button underneath (as the Festival Square's)
                var root = _visualElementLoader.LoadVisualElement("Game/EntityPanel/WonderFragment");
                root.name = "PandabornFloweringFragment";
                _label = new Label();
                _label.AddToClassList("entity-panel__text");
                _label.style.whiteSpace = WhiteSpace.Normal;
                root.Q<VisualElement>("InventoryRoot").Add(_label);
                _button = root.Q<Button>("ActivateButton");
                _button.clicked += () => _settingDialog.Show();
                root.ToggleDisplayStyle(false);
                return root;
            }, null) ?? new VisualElement();
            return _root;
        }

        public void ShowFragment(BaseComponent entity)
        {
            _plant = SafeUi.Get(Piece, () => _floweringService.Active ? entity.GetComponent<FloweringPlant>() : null, null);
            _inFlower = SafeUi.Get(Piece, () => _floweringService.Active ? entity.GetComponent<InFlowerPlant>() : null, null);
        }

        public void ClearFragment()
        {
            _plant = null;
            _inFlower = null;
            SafeUi.Run(Piece, () => _root.ToggleDisplayStyle(false));
        }

        public void UpdateFragment()
        {
            SafeUi.Run(Piece, () =>
            {
                bool show = (_plant != null || _inFlower != null) && _label != null;
                _root.ToggleDisplayStyle(show);
                if (!show) return;
                var s = _floweringService;
                string text;
                if (_inFlower != null)
                    text = _inFlower.IsDead ? "" : _loc.T("Pandaborn.Flowering.Plant.InFlower", FloweringService.Days(s.SeedDaysLeft));
                else if (s.Resting && _plant.Species == s.Species && !_plant.IsGrown)
                    text = _loc.T("Pandaborn.Flowering.Plant.Dormant", FloweringService.Days(s.RestDaysLeft));
                else if (s.Phase == FloweringPhase.Announced && _plant.Species == s.Species)
                    text = _loc.T("Pandaborn.Flowering.Plant.Announced", s.NextCycle.ToString(CultureInfo.InvariantCulture), FloweringService.Days(s.Spec.SeedDays));
                else if (s.Setting == "off")
                    text = _loc.T("Pandaborn.Flowering.Plant.IdleOff");
                else
                {
                    bool rare = s.Setting == "rare";
                    text = _loc.T("Pandaborn.Flowering.Plant.Idle",
                                  (rare ? s.Spec.RareMinCycles : s.Spec.NormalMinCycles).ToString(CultureInfo.InvariantCulture),
                                  (rare ? s.Spec.RareMaxCycles : s.Spec.NormalMaxCycles).ToString(CultureInfo.InvariantCulture),
                                  (s.Spec.FirstCycle + (rare ? s.Spec.RareDelayCycles : 0)).ToString(CultureInfo.InvariantCulture));
                }
                _label.text = text;
                _label.ToggleDisplayStyle(text.Length > 0);
                _button.text = _loc.T("Pandaborn.Flowering.Setting.Button", _settingDialog.SettingName(s.Setting));
                ShownText = text;
            });
        }
    }
}
