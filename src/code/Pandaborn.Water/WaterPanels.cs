using System.Globalization;
using System.Linq;
using Pandaborn.Core;
using Pandaborn.Specs;
using Timberborn.BaseComponentSystem;
using Timberborn.CoreUI;
using Timberborn.EntityPanelSystem;
using Timberborn.Localization;
using Timberborn.WaterBuildings;
using Timberborn.WorkSystem;
using Timberborn.Workshops;
using UnityEngine;
using UnityEngine.UIElements;

namespace Pandaborn.Water
{
    /// <summary>
    /// The Flume Gate's panel: the flow setting as a slider with its value in plain words, the badwater switch, and a state
    /// line. A copy of the vanilla floodgate fragment's layout (height slider + synchronize toggle) with the automation part
    /// hidden; the vanilla fragment itself is not touched. Behind SafeUi: if the layout changes in an update, the panel
    /// disappears and the gate keeps working with its saved settings.
    /// </summary>
    public class FlumeGateFragment : IEntityPanelFragment
    {
        private const string Piece = "Water.GatePanel";
        private readonly VisualElementLoader _visualElementLoader;
        private readonly ILoc _loc;
        private VisualElement _root;
        private Label _flowLabel, _stateLabel;
        private Slider _slider;
        private Toggle _guard;
        private FlumeGate _gate;
        private bool _updating;

        public FlumeGateFragment(VisualElementLoader visualElementLoader, ILoc loc)
        {
            _visualElementLoader = visualElementLoader;
            _loc = loc;
        }

        /// <summary>The flow line currently shown (for tests).</summary>
        public static string ShownText { get; private set; }

        public VisualElement InitializeFragment()
        {
            _root = SafeUi.Get(Piece, () =>
            {
                var root = _visualElementLoader.LoadVisualElement("Game/EntityPanel/FloodgateFragment");
                root.Q<VisualElement>("AutomationHeightWrapper").ToggleDisplayStyle(false);
                _stateLabel = root.Q<Label>("HeightState");
                _flowLabel = root.Q<Label>("Height");
                _slider = root.Q<Slider>("HeightSlider");
                _guard = root.Q<Toggle>("Synchronize");
                _guard.text = _loc.T("Pandaborn.Water.Gate.GuardToggle");
                _slider.RegisterValueChangedCallback(e => { if (!_updating && _gate != null) _gate.SetFlow(e.newValue); });
                _guard.RegisterValueChangedCallback(e => { if (!_updating && _gate != null) _gate.SetGuardEnabled(e.newValue); });
                root.ToggleDisplayStyle(false);
                return root;
            }, null) ?? new VisualElement();
            return _root;
        }

        public void ShowFragment(BaseComponent entity)
        {
            _gate = SafeUi.Get(Piece, () => entity.GetComponent<FlumeGate>(), null);
            SafeUi.Run(Piece, () =>
            {
                if (_gate == null || _slider == null) return;
                _updating = true;
                _slider.lowValue = 0f;
                _slider.highValue = _gate.MaxFlow;
                _slider.SetValueWithoutNotify(_gate.Flow);
                _guard.SetValueWithoutNotify(_gate.GuardEnabled);
                _updating = false;
            });
        }

        public void ClearFragment()
        {
            _gate = null;
            SafeUi.Run(Piece, () => _root.ToggleDisplayStyle(false));
        }

        public void UpdateFragment()
        {
            SafeUi.Run(Piece, () =>
            {
                bool show = _gate != null && _flowLabel != null;
                _root.ToggleDisplayStyle(show);
                if (!show) return;
                string flow = _loc.T("Unit.CubicMeterPerSecond.NumberAndUnit", _gate.Flow.ToString("0.00", CultureInfo.InvariantCulture));
                _flowLabel.text = _gate.Flow > 0f ? _loc.T("Pandaborn.Water.Gate.Flow", flow) : _loc.T("Pandaborn.Water.Gate.FlowZero");
                _stateLabel.text = _gate.ClosedByBadwater ? _loc.T("Pandaborn.Water.Gate.StateBadwater")
                    : _gate.IsOpen ? _loc.T("Pandaborn.Water.Gate.StateOpen") : _loc.T("Pandaborn.Water.Gate.StateClosed");
                ShownText = _flowLabel.text;
            });
        }
    }

    /// <summary>
    /// One plain-words line on the panels of the Scoop Wheel and Water Trip-Hammer (the current at the wheel and what it
    /// gives), the Paddy Spout (the depth it keeps and the depth now), the Treadwheel Lift and the Cistern Tap. Reuses the
    /// vanilla carried-goods line's layout, as the bell does.
    /// </summary>
    public class WaterInfoFragment : IEntityPanelFragment
    {
        private const string Piece = "Water.InfoLine";
        private readonly VisualElementLoader _visualElementLoader;
        private readonly ILoc _loc;
        private VisualElement _root;
        private Label _label;
        private BaseComponent _entity;

        public WaterInfoFragment(VisualElementLoader visualElementLoader, ILoc loc)
        {
            _visualElementLoader = visualElementLoader;
            _loc = loc;
        }

        public static string ShownText { get; private set; }

        public VisualElement InitializeFragment()
        {
            _root = SafeUi.Get(Piece, () =>
            {
                var root = _visualElementLoader.LoadVisualElement("Game/EntityPanel/GoodCarrierFragment");
                _label = root.Q<Label>("GoodCarrierFragment");
                _label.style.whiteSpace = WhiteSpace.Normal;
                root.ToggleDisplayStyle(false);
                return root;
            }, null) ?? new VisualElement();
            return _root;
        }

        public void ShowFragment(BaseComponent entity)
        {
            _entity = SafeUi.Get(Piece, () =>
                entity.GetComponent<PandabornCurrentDrivenSpec>() != null || entity.GetComponent<PandabornPaddySpoutSpec>() != null
                || entity.GetComponent<PandabornTreadwheelSpec>() != null || entity.GetComponent<PandabornCisternTapSpec>() != null
                    ? entity : null, null);
        }

        public void ClearFragment()
        {
            _entity = null;
            SafeUi.Run(Piece, () => _root.ToggleDisplayStyle(false));
        }

        public void UpdateFragment()
        {
            SafeUi.Run(Piece, () =>
            {
                string text = _entity != null ? Text(_entity) : null;
                bool show = !string.IsNullOrEmpty(text) && _label != null;
                _root.ToggleDisplayStyle(show);
                if (!show) return;
                _label.text = text;
                ShownText = text;
            });
        }

        /// <summary>The line for an entity, or null (public for tests).</summary>
        public string Text(BaseComponent e)
        {
            var mover = e.GetComponent<WaterMover>();
            var input = e.GetComponent<WaterInput>();
            var output = e.GetComponent<WaterOutput>();
            string rate = mover != null ? Cms(mover.CanMoveWater ? mover.EffectiveFlowRate : 0f) : null;

            var current = e.GetComponent<CurrentDriven>();
            if (current != null && e.GetComponent<PandabornCurrentDrivenSpec>() != null)
            {
                string c = current.Current.ToString("0.00", CultureInfo.InvariantCulture);
                string rated = current.RatedCurrent.ToString("0.00", CultureInfo.InvariantCulture);
                if (current.Current <= 0f) return _loc.T("Pandaborn.Water.Info.CurrentNone", rated);
                if (mover != null)
                {
                    // a zero lift in a good current is a state, not a fault: name it
                    if (!mover.CanMoveWater && output != null && !output.HasSpaceForWater) return _loc.T("Pandaborn.Water.Info.CurrentFull", c, rated);
                    if (!mover.CanMoveWater && input != null && !input.IsUnderwater) return _loc.T("Pandaborn.Water.Info.CurrentNoReach", c, rated);
                    return _loc.T("Pandaborn.Water.Info.CurrentLift", c, rated, rate);
                }
                return _loc.T("Pandaborn.Water.Info.CurrentWork", c, rated, Pct(current.Speed));
            }
            var spout = e.GetComponent<FillValve>();
            if (spout != null && e.GetComponent<PandabornPaddySpoutSpec>() != null)
            {
                float now = Mathf.Max(0f, spout.ActualHeight - spout.MinTargetHeight);
                if (now < 0.01f && input != null && !input.IsUnderwater) return _loc.T("Pandaborn.Water.Info.SpoutDry", Depth(spout.TargetDepth));
                return _loc.T("Pandaborn.Water.Info.Spout", Depth(spout.TargetDepth), Depth(now));
            }
            if (e.GetComponent<PandabornTreadwheelSpec>() != null && mover != null)
            {
                var workplace = e.GetComponent<Workplace>();
                bool staffed = workplace != null && workplace.NumberOfAssignedWorkers > 0;
                if (mover.CanMoveWater) return _loc.T("Pandaborn.Water.Info.TreadwheelLifting", rate);
                if (output != null && !output.HasSpaceForWater) return _loc.T("Pandaborn.Water.Info.TreadwheelFull");
                if (input != null && !input.IsUnderwater) return _loc.T("Pandaborn.Water.Info.TreadwheelNoReach");
                return staffed ? _loc.T("Pandaborn.Water.Info.TreadwheelIdle") : _loc.T("Pandaborn.Water.Info.TreadwheelNoWorker");
            }
            if (e.GetComponent<PandabornCisternTapSpec>() != null)
            {
                var manufactory = e.GetComponent<Manufactory>();
                var recipe = manufactory?.CurrentRecipe;
                int goods = recipe?.Ingredients.Sum(i => i.Amount) ?? 0;
                if (recipe == null || goods == 0) return null;
                float hours = recipe.CycleDurationInHours;
                // vanilla ManufactoryWaterProducer: one Water good becomes 0.2 of water
                return _loc.T("Pandaborn.Water.Info.CisternTap", goods.ToString(CultureInfo.InvariantCulture),
                              hours.ToString("0.#", CultureInfo.InvariantCulture), (goods * 0.2f).ToString("0.0", CultureInfo.InvariantCulture));
            }
            return null;
        }

        private string Cms(float v) => _loc.T("Unit.CubicMeterPerSecond.NumberAndUnit", v.ToString("0.00", CultureInfo.InvariantCulture));

        private static string Depth(float v) => v.ToString("0.00", CultureInfo.InvariantCulture);

        private static string Pct(float v) => Mathf.RoundToInt(Mathf.Clamp01(v) * 100f).ToString(CultureInfo.InvariantCulture) + "%";
    }
}
