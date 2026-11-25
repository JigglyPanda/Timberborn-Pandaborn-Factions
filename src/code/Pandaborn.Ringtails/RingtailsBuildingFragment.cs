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
        private readonly LoftNursery _nursery;
        private readonly ILoc _loc;
        private readonly System.Action _update;   // one delegate for the per-frame call, not a new closure every frame
        private float _nextLoftRefresh;
        private VisualElement _root;
        private VisualElement _icon;
        private Label _label;
        private Workplace _workplace;
        private NightPost _post;
        private MoonLoft _loft;
        private bool _night;

        public RingtailsBuildingFragment(VisualElementLoader visualElementLoader, RingtailService ringtailService, LoftNursery nursery, ILoc loc)
        {
            _visualElementLoader = visualElementLoader;
            _ringtailService = ringtailService;
            _nursery = nursery;
            _loc = loc;
            _update = UpdateCore;
        }

        public static string ShownText { get; private set; }

        /// <summary>"sun", "moon" or "" (tests).</summary>
        public static string ShownMark { get; private set; }

        /// <summary>Where the mark was laid out last ("x,y wxh" in panel pixels; tests).</summary>
        public static string ShownMarkBounds { get; private set; }

        public VisualElement InitializeFragment()
        {
            _root = SafeUi.Get(Piece, () =>
            {
                // the loader returns the vanilla label itself (a NineSliceLabel, the green text box); a child added inside a
                // text element is not drawn (seen in phase 3), so the label and the mark sit side by side in our own
                // container: the mark absolute over the label's widened left padding, drawn after it
                var loaded = _visualElementLoader.LoadVisualElement("Game/EntityPanel/GoodCarrierFragment");
                _label = loaded as Label ?? loaded.Q<Label>("GoodCarrierFragment");
                var root = new VisualElement { name = "PandabornRingtailsFragment" };
                root.Add(loaded);
                if (_label != null) _label.style.paddingLeft = 30;
                _icon = new VisualElement { name = "PandabornShiftMark", pickingMode = PickingMode.Ignore };
                _icon.style.position = Position.Absolute;
                _icon.style.width = 16;
                _icon.style.height = 16;
                _icon.style.left = 10;
                _icon.style.top = Length.Percent(50);
                _icon.style.marginTop = -8;
                _icon.generateVisualContent += DrawMark;
                root.Add(_icon);
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
            _nextLoftRefresh = 0f;
            if (_workplace == null && _post == null && _loft == null) Hide();
        }

        public void ClearFragment()
        {
            _workplace = null;
            _post = null;
            _loft = null;
            Hide();
        }

        /// <summary>Not through SafeUi: a piece that failed while it was on screen must still disappear.</summary>
        private void Hide()
        {
            try { if (_root != null) _root.style.display = DisplayStyle.None; }
            catch (System.Exception) { }
            ShownMark = "";
        }

        public void UpdateFragment()
        {
            if (_workplace == null && _post == null && _loft == null) return;   // hidden; nothing to do for other entities
            SafeUi.Run(Piece, _update);
            if (SafeUi.IsBroken(Piece)) Hide();
        }

        private void UpdateCore()
        {
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
                    else if (_loft)
                    {
                        // the nursery line is recounted about once a second while the loft is selected, so it is right
                        // after a load and for a loft built since dawn
                        if (Time.unscaledTime >= _nextLoftRefresh)
                        {
                            _nextLoftRefresh = Time.unscaledTime + 1f;
                            _nursery.Refresh(_loft);
                        }
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
                if (_label.text != text) _label.text = text;
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
                if (icon && _icon != null)
                {
                    var b = _icon.worldBound;
                    ShownMarkBounds = Mathf.RoundToInt(b.x) + "," + Mathf.RoundToInt(b.y) + " " + Mathf.RoundToInt(b.width) + "x" + Mathf.RoundToInt(b.height);
                }
            }
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
