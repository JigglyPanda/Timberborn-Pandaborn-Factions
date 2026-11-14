using System.Linq;
using Pandaborn.Core;
using Pandaborn.Specs;
using Timberborn.BaseComponentSystem;
using Timberborn.BeaverContaminationSystem;
using Timberborn.Beavers;
using Timberborn.Characters;
using Timberborn.CoreUI;
using Timberborn.EntityPanelSystem;
using Timberborn.GameDistricts;
using Timberborn.Localization;
using Timberborn.MortalSystem;
using Timberborn.SelectionSystem;
using Timberborn.SingletonSystem;
using Timberborn.UILayoutSystem;
using Timberborn.WorkSystem;
using UnityEngine;
using UnityEngine.UIElements;

namespace Pandaborn.Ringtails
{
    /// <summary>
    /// The Ringtail portrait and subtitle on the character panel ("Ringtail, age 4"). The vanilla BeaverEntityBadge has priority
    /// 10 and draws the faction (Inkpaw) avatar; this one has 11 and draws the template's own avatar. Falls back to the
    /// vanilla badge's look if anything is missing.
    /// </summary>
    public class RingtailBadge : BaseComponent, IAwakableComponent, IEntityBadge
    {
        private readonly ILoc _loc;
        private readonly EntitySelectionService _entitySelectionService;
        private PandabornRingtailSpec _spec;
        private Character _character;
        private Citizen _citizen;
        private Mortal _mortal;
        private Child _child;
        private Contaminable _contaminable;

        public RingtailBadge(ILoc loc, EntitySelectionService entitySelectionService)
        {
            _loc = loc;
            _entitySelectionService = entitySelectionService;
        }

        public int EntityBadgePriority => 11;

        public void Awake()
        {
            _spec = GetComponent<PandabornRingtailSpec>();
            _character = GetComponent<Character>();
            _citizen = GetComponent<Citizen>();
            _mortal = GetComponent<Mortal>();
            _child = GetComponent<Child>();
            _contaminable = GetComponent<Contaminable>();
        }

        public string GetEntitySubtitle() => SafeUi.Get("Ringtails.Badge", () =>
        {
            string text = _loc.T(_child ? "Pandaborn.Ringtails.KitAge" : "Pandaborn.Ringtails.Age", _character.Age);
            return _mortal != null && _mortal.Dead ? text + " " + _loc.T("Beaver.DeadNameSuffix") : text;
        }, "");

        public ClickableSubtitle GetEntityClickableSubtitle()
        {
            if (_citizen != null && _citizen.HasAssignedDistrict)
            {
                var district = _citizen.AssignedDistrict;
                return ClickableSubtitle.Create(() => _entitySelectionService.SelectAndFocusOn(district), district.DistrictName);
            }
            return ClickableSubtitle.CreateEmpty();
        }

        public Sprite GetEntityAvatar() => SafeUi.Get<Sprite>("Ringtails.Badge.Avatar", () =>
        {
            if (_spec == null) return null;
            bool contaminated = _contaminable != null && _contaminable.IsContaminated;
            var avatar = contaminated ? _spec.ContaminatedAvatar : _spec.Avatar;
            return avatar?.Asset;
        }, null);
    }

    /// <summary>
    /// The second population row, under the vanilla population panel: "Ringtails: 5 · working 4 · idle 1" for the selected
    /// district, or the whole colony. Needed because the vanilla workforce numbers only count the Beaver and Bot worker types.
    /// Shown only once the Ringtails have arrived. A copy of the vanilla working-hours panel layout is reused as the frame.
    /// </summary>
    public class RingtailsPopulationRow : ILoadableSingleton, IUpdatableSingleton
    {
        private const string Piece = "Ringtails.PopulationRow";
        private readonly RingtailService _ringtailService;
        private readonly UILayout _uiLayout;
        private readonly VisualElementLoader _visualElementLoader;
        private readonly DistrictContextService _districtContextService;
        private readonly DistrictCenterRegistry _districtCenterRegistry;
        private readonly EventBus _eventBus;
        private readonly ILoc _loc;
        private bool _primaryUiShown;
        private bool _added;
        private VisualElement _root;
        private Label _text;
        private float _nextUpdate;

        public RingtailsPopulationRow(RingtailService ringtailService, UILayout uiLayout, VisualElementLoader visualElementLoader,
                                      DistrictContextService districtContextService, DistrictCenterRegistry districtCenterRegistry,
                                      EventBus eventBus, ILoc loc)
        {
            _ringtailService = ringtailService;
            _uiLayout = uiLayout;
            _visualElementLoader = visualElementLoader;
            _districtContextService = districtContextService;
            _districtCenterRegistry = districtCenterRegistry;
            _eventBus = eventBus;
            _loc = loc;
        }

        /// <summary>The text currently shown (tests).</summary>
        public static string ShownText { get; private set; }

        public static (int Total, int Working, int Idle, int Kits) Count(System.Collections.Generic.IEnumerable<DistrictCenter> districts)
        {
            int adults = 0, working = 0, kits = 0;
            foreach (var d in districts)
            {
                foreach (var b in d.DistrictPopulation.Adults)
                {
                    if (!RingtailService.IsRingtail(b)) continue;
                    adults++;
                    var w = b.GetComponent<Worker>();
                    if (w != null && w.Employed) working++;
                }
                kits += d.DistrictPopulation.Children.Count(b => RingtailService.IsRingtail(b));
            }
            return (adults + kits, working, adults - working, kits);
        }

        public void Load()
        {
            if (!_ringtailService.Enabled) return;
            _eventBus.Register(this);
        }

        [OnEvent]
        public void OnShowPrimaryUI(ShowPrimaryUIEvent e) => _primaryUiShown = true;

        public void UpdateSingleton()
        {
            if (!_primaryUiShown || !_ringtailService.Enabled || SafeUi.IsBroken(Piece)) return;
            if (!_added)
            {
                _added = true;
                SafeUi.Run(Piece, () =>
                {
                    _root = _visualElementLoader.LoadVisualElement("Game/WorkingHoursPanel");
                    _root.name = "PandabornRingtailsRow";
                    _root.Q<Button>("Minus").style.display = DisplayStyle.None;
                    _root.Q<Button>("Plus").style.display = DisplayStyle.None;
                    _text = _root.Q<Label>("Text");
                    _uiLayout.AddTopLeft(_root, 3);
                });
            }
            if (Time.unscaledTime < _nextUpdate || _root == null) return;
            _nextUpdate = Time.unscaledTime + 1f;
            SafeUi.Run(Piece, () =>
            {
                bool show = _ringtailService.Arrived;
                _root.style.display = show ? DisplayStyle.Flex : DisplayStyle.None;
                if (!show) return;
                var selected = _districtContextService.SelectedDistrict;
                var c = Count(selected ? new[] { selected } : _districtCenterRegistry.FinishedDistrictCenters.ToArray());
                string text = _loc.T("Pandaborn.Ringtails.PopulationRow", c.Total, c.Working, c.Idle);
                _text.text = text;
                ShownText = text;
            });
        }
    }

    /// <summary>
    /// A line on the panel of a night post or a Moon Loft: the moon mark and the one rule ("Night post: Ringtails work here from
    /// the bell to dawn."), and on a loft what its nursery is doing ("Kits: waiting for open night jobs").
    /// </summary>
    public class RingtailsBuildingFragment : IEntityPanelFragment
    {
        private const string Piece = "Ringtails.BuildingFragment";
        private readonly VisualElementLoader _visualElementLoader;
        private readonly RingtailService _ringtailService;
        private readonly LoftNursery _nursery;
        private readonly ILoc _loc;
        private VisualElement _root;
        private Label _label;
        private NightPost _post;
        private MoonLoft _loft;

        public RingtailsBuildingFragment(VisualElementLoader visualElementLoader, RingtailService ringtailService, LoftNursery nursery, ILoc loc)
        {
            _visualElementLoader = visualElementLoader;
            _ringtailService = ringtailService;
            _nursery = nursery;
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
            _post = SafeUi.Get(Piece, () => entity.GetComponent<NightPost>(), null);
            _loft = SafeUi.Get(Piece, () => entity.GetComponent<MoonLoft>(), null);
        }

        public void ClearFragment()
        {
            _post = null;
            _loft = null;
            SafeUi.Run(Piece, () => _root.ToggleDisplayStyle(false));
        }

        public void UpdateFragment()
        {
            SafeUi.Run(Piece, () =>
            {
                string text = null;
                if (_ringtailService.Enabled && _post != null && _post.IsRingtailTyped)
                    text = _loc.T("Pandaborn.Ringtails.Panel.NightPost");
                else if (_ringtailService.Enabled && _loft != null)
                    text = _ringtailService.Arrived && !string.IsNullOrEmpty(_loft.KitState)
                        ? _loc.T("Pandaborn.Ringtails.Panel.Loft") + " " + _loc.T(_loft.KitState)
                        : _loc.T("Pandaborn.Ringtails.Panel.Loft");
                bool show = text != null && _label != null;
                _root.ToggleDisplayStyle(show);
                if (!show) return;
                _label.text = text;
                ShownText = text;
            });
        }
    }
}
