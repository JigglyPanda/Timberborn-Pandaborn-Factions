using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using Pandaborn.Core;
using Timberborn.BaseComponentSystem;
using Timberborn.CoreUI;
using Timberborn.EntityPanelSystem;
using Timberborn.Goods;
using Timberborn.Localization;
using UnityEngine;
using UnityEngine.UIElements;

namespace Pandaborn.Festival
{
    /// <summary>
    /// The festival on the Festival Square's panel: what the district has in store towards it, the Call button, the
    /// auto-call toggle, the next allowed festival and Tradition. Built on the vanilla wonder fragment's layout (a box with a
    /// content root and a red button), so it looks like the game's own panels; the vanilla layout is not changed.
    /// Wrapped by SafeUi: if the layout changes in an update, this fragment disappears and nothing else.
    /// </summary>
    public class FestivalSquareFragment : IEntityPanelFragment
    {
        private const string Piece = "Festival.SquareFragment";
        private readonly VisualElementLoader _visualElementLoader;
        private readonly FestivalService _festivalService;
        private readonly IGoodService _goodService;
        private readonly ILoc _loc;
        private VisualElement _root;
        private Label _status;
        private Label _lanterns;
        private Label _dishes;
        private Label _dishList;
        private Label _fireworks;
        private Label _tradition;
        private Label _rule;
        private Button _call;
        private Toggle _auto;
        private FestivalSquare _square;
        private float _nextRefresh;

        public FestivalSquareFragment(VisualElementLoader visualElementLoader, FestivalService festivalService, IGoodService goodService, ILoc loc)
        {
            _visualElementLoader = visualElementLoader;
            _festivalService = festivalService;
            _goodService = goodService;
            _loc = loc;
        }

        /// <summary>The lines currently shown (tests).</summary>
        public static string ShownText { get; private set; }

        public VisualElement InitializeFragment()
        {
            _root = SafeUi.Get(Piece, () =>
            {
                var root = _visualElementLoader.LoadVisualElement("Game/EntityPanel/WonderFragment");
                root.name = "PandabornFestivalFragment";
                var content = root.Q<VisualElement>("InventoryRoot");
                _status = AddLabel(content, true);
                _lanterns = AddLabel(content, false);
                _dishes = AddLabel(content, false);
                _dishList = AddLabel(content, false);
                _fireworks = AddLabel(content, false);
                _tradition = AddLabel(content, false);
                _rule = AddLabel(content, false);
                _rule.style.whiteSpace = WhiteSpace.Normal;
                _call = root.Q<Button>("ActivateButton");
                _call.text = _loc.T("Pandaborn.Festival.Call");
                _call.clicked += OnCall;
                _auto = new Toggle(_loc.T("Pandaborn.Festival.AutoCall"));
                _auto.AddToClassList("game-toggle");
                _auto.AddToClassList("entity-panel__text");
                _auto.AddToClassList("entity-panel__toggle");
                _auto.RegisterValueChangedCallback(e => SafeUi.Run(Piece + ".Auto", () => _festivalService.SetAutoCall(e.newValue)));
                root.Add(_auto);
                root.ToggleDisplayStyle(false);
                return root;
            }, null) ?? new VisualElement();
            return _root;
        }

        public void ShowFragment(BaseComponent entity)
        {
            _square = SafeUi.Get(Piece, () => _festivalService.Active ? entity.GetComponent<FestivalSquare>() : null, null);
            _nextRefresh = 0f;
        }

        public void ClearFragment()
        {
            _square = null;
            SafeUi.Run(Piece, () => _root.ToggleDisplayStyle(false));
        }

        public void UpdateFragment()
        {
            SafeUi.Run(Piece, () =>
            {
                bool show = _square != null && _status != null;
                _root.ToggleDisplayStyle(show);
                if (!show || Time.unscaledTime < _nextRefresh) return;
                _nextRefresh = Time.unscaledTime + 0.3f;
                Refresh();
            });
        }

        private void Refresh()
        {
            if (!_square) { _square = null; return; }   // demolished while its panel was open
            var spec = _festivalService.Spec;
            var stock = FestivalStock.Count(_square.District, spec);
            string why = _festivalService.WhyNot(_square, stock);
            _status.text = why ?? _loc.T(stock.GrandReady ? "Pandaborn.Festival.Status.ReadyGrand" : "Pandaborn.Festival.Status.Ready");
            _lanterns.text = _loc.T("Pandaborn.Festival.Lanterns", stock.Lanterns.ToString(CultureInfo.InvariantCulture),
                                    stock.LanternsNeeded.ToString(CultureInfo.InvariantCulture));
            _dishes.text = _loc.T("Pandaborn.Festival.Dishes", stock.ReadyDishKinds.ToString(CultureInfo.InvariantCulture),
                                  stock.DishKinds.ToString(CultureInfo.InvariantCulture), stock.DishAmount.ToString(CultureInfo.InvariantCulture));
            var listed = stock.Dishes.Where(d => d.Value > 0).Take(5).Select(d => GoodName(d.Key) + " " + d.Value.ToString(CultureInfo.InvariantCulture)).ToList();
            _dishList.text = listed.Count > 0 ? string.Join(", ", listed) : _loc.T("Pandaborn.Festival.NoDishes");
            _fireworks.ToggleDisplayStyle(stock.FireworksNeeded > 0);
            _fireworks.text = _loc.T("Pandaborn.Festival.Fireworks", stock.Fireworks.ToString(CultureInfo.InvariantCulture),
                                     stock.FireworksNeeded.ToString(CultureInfo.InvariantCulture));
            _tradition.text = _loc.T("Pandaborn.Festival.TraditionLine", _festivalService.Tradition.ToString(CultureInfo.InvariantCulture));
            // with several districts the rule says whose festival it is (the district of the calling square)
            bool dayOff = FestivalGoer.InsertionError == null;
            _rule.text = _festivalService.ManyDistricts
                ? _loc.T(dayOff ? "Pandaborn.Festival.RuleDistrict" : "Pandaborn.Festival.RuleNoDayOffDistrict")
                : _loc.T(dayOff ? "Pandaborn.Festival.Rule" : "Pandaborn.Festival.RuleNoDayOff");
            _call.SetEnabled(why == null);
            _auto.SetValueWithoutNotify(_festivalService.AutoCall);
            ShownText = string.Join(" | ", new[] { _status.text, _lanterns.text, _dishes.text, _dishList.text, _fireworks.text, _tradition.text });
        }

        private void OnCall()
        {
            SafeUi.Run(Piece + ".Call", () =>
            {
                if (_square != null) _festivalService.Call(_square, auto: false);
                _nextRefresh = 0f;
            });
        }

        private string GoodName(string goodId)
        {
            var good = _goodService.GetGoodOrNull(goodId);
            return good != null ? good.PluralDisplayName.Value : goodId;
        }

        private static Label AddLabel(VisualElement parent, bool title)
        {
            var label = new Label();
            label.AddToClassList("entity-panel__text");
            if (title) label.AddToClassList("entity-panel__heading");
            parent.Add(label);
            return label;
        }
    }
}
