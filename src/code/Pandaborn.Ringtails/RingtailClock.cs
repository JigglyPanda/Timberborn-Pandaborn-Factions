using System;
using Pandaborn.Core;
using Timberborn.SingletonSystem;
using Timberborn.TimeSystem;
using Timberborn.UILayoutSystem;
using UnityEngine;
using UnityEngine.UIElements;

namespace Pandaborn.Ringtails
{
    /// <summary>
    /// The moon arc on the vanilla day clock (top right): the Ringtail shift, from its start (the bell, clamped) to dawn, drawn
    /// as a pale arc just inside the dial's rim, so one glance shows who works when. The vanilla clock is not changed: an extra
    /// child element is added to its "Clock" element and draws itself with the UI Toolkit vector API. The dial's angles follow
    /// the vanilla ClockPanel (hours/24 x 360 - 60 degrees, clockwise from the top). Shown once the Ringtails have arrived.
    /// Behind SafeUi: if the clock's layout changes in an update, the arc is simply not drawn.
    /// </summary>
    public class RingtailClockArc : ILoadableSingleton, IUpdatableSingleton
    {
        private const string Piece = "Ringtails.ClockArc";
        private const float StartingAngleOffset = -60f;   // ClockPanel.StartingAngleOffset
        private static readonly Color MoonColor = new Color(0.78f, 0.86f, 1f, 0.95f);
        private static readonly Color MoonShadow = new Color(0.08f, 0.1f, 0.22f, 0.8f);

        private readonly RingtailService _ringtailService;
        private readonly RingtailWorkday _workday;
        private readonly IDayNightCycle _dayNightCycle;
        private readonly UILayout _uiLayout;
        private readonly EventBus _eventBus;
        private bool _primaryUiShown;
        private VisualElement _anchor;
        private VisualElement _arc;
        private float _drawnStart = -1f;
        private float _nextCheck;

        public RingtailClockArc(RingtailService ringtailService, RingtailWorkday workday, IDayNightCycle dayNightCycle, UILayout uiLayout,
                                EventBus eventBus)
        {
            _ringtailService = ringtailService;
            _workday = workday;
            _dayNightCycle = dayNightCycle;
            _uiLayout = uiLayout;
            _eventBus = eventBus;
        }

        /// <summary>The arc currently drawn, in hours after dawn (tests); null when none.</summary>
        public static string Shown { get; private set; }

        public void Load()
        {
            if (!_ringtailService.Enabled) return;
            _eventBus.Register(this);
        }

        [OnEvent]
        public void OnShowPrimaryUI(ShowPrimaryUIEvent e) => _primaryUiShown = true;

        public void UpdateSingleton()
        {
            if (!_primaryUiShown || !_ringtailService.Enabled || SafeUi.IsBroken(Piece) || Time.unscaledTime < _nextCheck) return;
            _nextCheck = Time.unscaledTime + 0.5f;
            SafeUi.Run(Piece, () =>
            {
                if (_anchor == null)
                {
                    // a zero-size element only to reach the game's UI panel, where the vanilla clock lives
                    _anchor = new VisualElement { name = "PandabornRingtailClockAnchor", pickingMode = PickingMode.Ignore };
                    _anchor.style.width = 0;
                    _anchor.style.height = 0;
                    _uiLayout.AddAbsoluteItem(_anchor);
                }
                if (_arc == null || _arc.panel == null)
                {
                    var clock = _anchor.panel?.visualTree.Q<VisualElement>("Clock");
                    if (clock == null) return;
                    _arc = new VisualElement { name = "PandabornRingtailArc", pickingMode = PickingMode.Ignore };
                    _arc.style.position = Position.Absolute;
                    _arc.style.left = 0;
                    _arc.style.top = 0;
                    _arc.style.right = 0;
                    _arc.style.bottom = 0;
                    _arc.generateVisualContent += Draw;
                    clock.Add(_arc);
                }
                bool show = _ringtailService.Arrived;
                _arc.style.display = show ? DisplayStyle.Flex : DisplayStyle.None;
                float start = _workday.ShiftStartHours;
                if (Math.Abs(start - _drawnStart) > 0.01f)
                {
                    _drawnStart = start;
                    _arc.MarkDirtyRepaint();
                }
                Shown = show ? start.ToString("0.#") + " h to dawn" : null;
            });
        }

        /// <summary>Clockwise from the top, as the vanilla needle (hours since dawn).</summary>
        private float DialAngle(float hoursSinceDawn) => (hoursSinceDawn + _workday.Dawn) / 24f * 360f + StartingAngleOffset;

        private void Draw(MeshGenerationContext context)
        {
            SafeUi.Run(Piece + ".Draw", () =>
            {
                var rect = _arc.contentRect;
                float size = Mathf.Min(rect.width, rect.height);
                if (size <= 0f) return;
                var center = new Vector2(rect.width / 2f, rect.height / 2f);
                float radius = size / 2f - 4f;
                // Painter2D measures angles from +x (3 o'clock), clockwise on screen; the dial measures from the top
                float from = DialAngle(_drawnStart) - 90f;
                float to = DialAngle(_dayNightCycle.DaytimeLengthInHours + _dayNightCycle.NighttimeLengthInHours) - 90f;
                var painter = context.painter2D;
                painter.lineCap = LineCap.Round;
                painter.lineWidth = 4.5f;
                painter.strokeColor = MoonShadow;
                painter.BeginPath();
                painter.Arc(center, radius, Angle.Degrees(from), Angle.Degrees(to));
                painter.Stroke();
                painter.lineWidth = 2.5f;
                painter.strokeColor = MoonColor;
                painter.BeginPath();
                painter.Arc(center, radius, Angle.Degrees(from), Angle.Degrees(to));
                painter.Stroke();
            });
        }
    }
}
