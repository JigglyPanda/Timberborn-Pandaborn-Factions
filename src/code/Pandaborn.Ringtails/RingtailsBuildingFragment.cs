using Pandaborn.Core;
using Timberborn.BaseComponentSystem;
using Timberborn.CoreUI;
using Timberborn.EntityPanelSystem;
using Timberborn.Localization;
using Timberborn.WorkSystem;
using UnityEngine;
using UnityEngine.UIElements;

namespace Pandaborn.Ringtails
{
    /// <summary>
    /// The sun or moon mark on every workplace's panel, once the Ringtails have arrived: a small drawn sun and "Day shift:
    /// Inkpaws work here from dawn to the afternoon bell." on Inkpaw workplaces; a crescent and "Night shift: Ringtails work
    /// here from the afternoon bell to dawn." on night posts. On a Moon Loft: what its nursery is doing. The icons are drawn
    /// with the UI Toolkit vector API (no sprite needed). Behind SafeUi.
    /// </summary>
    public class RingtailsBuildingFragment : IEntityPanelFragment
    {
        private const string Piece = "Ringtails.BuildingFragment";
        private static readonly Color SunColor = new Color(1f, 0.82f, 0.35f, 1f);
        private static readonly Color MoonColor = new Color(0.78f, 0.86f, 1f, 1f);
        private readonly VisualElementLoader _visualElementLoader;
        private readonly RingtailService _ringtailService;
        private readonly ILoc _loc;
        private VisualElement _root;
        private VisualElement _icon;
        private Label _label;
        private Workplace _workplace;
        private NightPost _post;
        private MoonLoft _loft;
        private bool _night;

        public RingtailsBuildingFragment(VisualElementLoader visualElementLoader, RingtailService ringtailService, ILoc loc)
        {
            _visualElementLoader = visualElementLoader;
            _ringtailService = ringtailService;
            _loc = loc;
        }

        public static string ShownText { get; private set; }

        /// <summary>"sun", "moon" or "" (tests).</summary>
        public static string ShownMark { get; private set; }

        public VisualElement InitializeFragment()
        {
            _root = SafeUi.Get(Piece, () =>
            {
                var root = _visualElementLoader.LoadVisualElement("Game/EntityPanel/GoodCarrierFragment");
                _label = root.Q<Label>("GoodCarrierFragment");
                _icon = new VisualElement { name = "PandabornShiftMark", pickingMode = PickingMode.Ignore };
                _icon.style.width = 16;
                _icon.style.height = 16;
                _icon.style.flexShrink = 0;
                _icon.style.marginRight = 4;
                _icon.style.alignSelf = Align.Center;
                _icon.generateVisualContent += DrawMark;
                var parent = _label?.parent ?? root;
                parent.style.flexDirection = FlexDirection.Row;
                parent.Insert(0, _icon);
                root.ToggleDisplayStyle(false);
                return root;
            }, null) ?? new VisualElement();
            return _root;
        }

        public void ShowFragment(BaseComponent entity)
        {
            _workplace = SafeUi.Get(Piece, () => entity.GetComponent<Workplace>(), null);
            _post = SafeUi.Get(Piece, () => entity.GetComponent<NightPost>(), null);
            _loft = SafeUi.Get(Piece, () => entity.GetComponent<MoonLoft>(), null);
        }

        public void ClearFragment()
        {
            _workplace = null;
            _post = null;
            _loft = null;
            SafeUi.Run(Piece, () => _root.ToggleDisplayStyle(false));
        }

        public void UpdateFragment()
        {
            SafeUi.Run(Piece, () =>
            {
                string text = null;
                bool icon = false, night = false;
                if (_ringtailService.Enabled && _ringtailService.Arrived)
                {
                    if (_post != null && _post.IsRingtailTyped)
                    {
                        text = _loc.T("Pandaborn.Ringtails.Panel.NightPost");
                        icon = true;
                        night = true;
                    }
                    else if (_workplace != null && _workplace.GetComponent<WorkplaceWorkerType>()?.WorkerType == "Beaver")
                    {
                        text = _loc.T("Pandaborn.Ringtails.Panel.DayShift");
                        icon = true;
                    }
                    else if (_loft != null)
                    {
                        text = _loc.T("Pandaborn.Ringtails.Panel.Loft") + (string.IsNullOrEmpty(_loft.KitState) ? "" : " " + _loc.T(_loft.KitState));
                    }
                }
                bool show = text != null && _label != null;
                _root.ToggleDisplayStyle(show);
                if (!show)
                {
                    ShownMark = "";
                    return;
                }
                _label.text = text;
                ShownText = text;
                if (_icon != null)
                {
                    _icon.style.display = icon ? DisplayStyle.Flex : DisplayStyle.None;
                    if (night != _night)
                    {
                        _night = night;
                        _icon.MarkDirtyRepaint();
                    }
                }
                ShownMark = icon ? (night ? "moon" : "sun") : "";
            });
        }

        private void DrawMark(MeshGenerationContext context)
        {
            SafeUi.Run(Piece + ".Draw", () =>
            {
                var r = _icon.contentRect;
                float size = Mathf.Min(r.width, r.height);
                if (size <= 0f) return;
                var c = new Vector2(r.width / 2f, r.height / 2f);
                var p = context.painter2D;
                if (_night)
                {
                    // crescent: the outer arc of a disc, closed by the inner arc of a second disc offset to the upper right
                    float big = size * 0.45f;
                    var inner = c + new Vector2(big * 0.45f, -big * 0.35f);
                    p.fillColor = MoonColor;
                    p.BeginPath();
                    p.Arc(c, big, Angle.Degrees(-60f), Angle.Degrees(240f));
                    p.Arc(inner, big * 0.78f, Angle.Degrees(220f), Angle.Degrees(-40f), ArcDirection.CounterClockwise);
                    p.ClosePath();
                    p.Fill();
                }
                else
                {
                    float disc = size * 0.26f;
                    p.fillColor = SunColor;
                    p.BeginPath();
                    p.Arc(c, disc, Angle.Degrees(0f), Angle.Degrees(360f));
                    p.Fill();
                    p.strokeColor = SunColor;
                    p.lineWidth = 1.6f;
                    p.lineCap = LineCap.Round;
                    for (int i = 0; i < 8; i++)
                    {
                        float a = i * Mathf.PI / 4f;
                        var d = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
                        p.BeginPath();
                        p.MoveTo(c + d * (disc + 1.8f));
                        p.LineTo(c + d * (size * 0.48f));
                        p.Stroke();
                    }
                }
            });
        }
    }
}
