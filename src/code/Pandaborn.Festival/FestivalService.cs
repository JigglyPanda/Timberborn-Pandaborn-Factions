using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using Pandaborn.Core;
using Pandaborn.Specs;
using Timberborn.Beavers;
using Timberborn.GameCycleSystem;
using Timberborn.GameDistricts;
using Timberborn.Goods;
using Timberborn.Localization;
using Timberborn.SingletonSystem;
using Timberborn.TemplateSystem;
using Timberborn.TickSystem;
using Timberborn.TimeSystem;
using Timberborn.WeatherSystem;
using UnityEngine;

namespace Pandaborn.Festival
{
    public enum FestivalPhase
    {
        None,
        /// <summary>Called; begins at the next dawn (FestivalDay).</summary>
        Called,
        /// <summary>Today is the festival: from dawn to the next dawn.</summary>
        Running
    }

    /// <summary>
    /// The Lantern Festival (DESIGN.md, Pillar 5; docs/tech/events.md). The player calls it from a Festival Square when the
    /// square's district has the lanterns and dishes in store (or lets it call itself); the goods are taken at once and the
    /// festival runs from the next dawn to the dawn after: nobody works except the crews of the KeepWorkingTemplates
    /// workplaces, everyone gathers at the square at dusk for the rising lanterns (and fireworks, if grand), and when it
    /// ends every colonist has festive spirit and the village's Tradition rises by one. At most one festival per cycle.
    ///
    /// The game is a festival game when the faction's adult template carries PandabornFestivalSpec (Inkpaws only).
    /// Saved state (store "Festival", version 1): phase, festival day, grand, last festival cycle, Tradition, auto-call,
    /// count. Nothing else is saved: the day off is a root behaviour (FestivalGoer), the show is computed from the clock.
    /// </summary>
    public class FestivalService : ILoadableSingleton, IPostLoadableSingleton, ITickableSingleton
    {
        public const string StoreFeature = "Festival";
        private const int StoreVersion = 1;
        private const string Log = "[Pandaborn.Festival] ";

        private readonly TemplateService _templateService;
        private readonly PandabornStore _store;
        private readonly Messenger _messenger;
        private readonly ILoc _loc;
        private readonly IDayNightCycle _dayNightCycle;
        private readonly GameCycleService _gameCycleService;
        private readonly WeatherService _weatherService;
        private readonly EventBus _eventBus;
        private readonly FestivalFireworks _fireworks;

        private readonly List<FestivalSquare> _squares = new List<FestivalSquare>();
        private readonly List<FestivalGoer> _goers = new List<FestivalGoer>();
        private readonly HashSet<FestivalGoer> _attended = new HashSet<FestivalGoer>();
        private HashSet<string> _keepWorking = new HashSet<string>(StringComparer.Ordinal);
        private int _lastHour = -1;
        private float _showClock = -1f;

        public FestivalService(TemplateService templateService, PandabornStore store, Messenger messenger, ILoc loc, IDayNightCycle dayNightCycle,
                               GameCycleService gameCycleService, WeatherService weatherService, EventBus eventBus, FestivalFireworks fireworks)
        {
            _templateService = templateService;
            _store = store;
            _messenger = messenger;
            _loc = loc;
            _dayNightCycle = dayNightCycle;
            _gameCycleService = gameCycleService;
            _weatherService = weatherService;
            _eventBus = eventBus;
            _fireworks = fireworks;
        }

        /// <summary>The service of the running game (tests, other modules' optional integrations).</summary>
        public static FestivalService Current { get; private set; }

        public PandabornFestivalSpec Spec { get; private set; }

        public bool Active => Spec != null;

        public FestivalPhase Phase { get; private set; }

        /// <summary>Day number (IDayNightCycle.DayNumber) of the called or running festival.</summary>
        public int FestivalDay { get; private set; } = -1;

        public bool Grand { get; private set; }

        /// <summary>Cycle of the last festival (its day), -1 if none.</summary>
        public int LastCycle { get; private set; } = -1;

        public int Tradition { get; private set; }

        public bool AutoCall { get; private set; }

        public int Count { get; private set; }

        /// <summary>Lanterns and bursts launched in this session (tests).</summary>
        public int LanternsLaunched { get; private set; }

        public int BurstsLaunched { get; private set; }

        public IReadOnlyList<FestivalSquare> Squares => _squares;

        /// <summary>"ok", or why the show's fireworks are off.</summary>
        public string FireworksStatus => _fireworks.Available ? "ok" : _fireworks.Unavailable;

        public IReadOnlyList<FestivalGoer> Goers => _goers;

        public event Action Changed;

        /// <summary>Raised with the new Tradition after a festival.</summary>
        public event Action<int> TraditionChanged;

        /// <summary>Today is the festival day (dawn to the next dawn).</summary>
        public bool IsHoliday => Active && Phase == FestivalPhase.Running && _dayNightCycle.DayNumber == FestivalDay;

        public float HoursToday => _dayNightCycle.HoursPassedToday;

        /// <summary>The evening gathering: everyone off duty comes to the square for the lanterns.</summary>
        public bool IsShowTime => IsHoliday && HoursToday >= Spec.ShowStartHours && HoursToday < Spec.ShowEndHours;

        public int CurrentCycle => _gameCycleService.Cycle;

        /// <summary>The first cycle in which a festival may be called again.</summary>
        public int NextAllowedCycle => LastCycle < 0 ? 0 : LastCycle + 1;

        public bool CycleAllows => CurrentCycle >= NextAllowedCycle;

        public void Load()
        {
            Current = this;
            try
            {
                var adult = _templateService.GetAll<AdultSpec>().FirstOrDefault();
                Spec = adult?.Blueprint?.GetSpec<PandabornFestivalSpec>();
            }
            catch (Exception e)
            {
                Debug.LogError(Log + "reading the adult template failed; festivals are off: " + e);
                Spec = null;
            }
            if (!Active) return;
            _keepWorking = new HashSet<string>(Spec.KeepWorkingTemplates.IsDefault ? Enumerable.Empty<string>() : Spec.KeepWorkingTemplates, StringComparer.Ordinal);
            ReadState();
            _eventBus.Register(this);
        }

        public void PostLoad()
        {
            if (!Active) return;
            // A save made before a festival's day ended, loaded later (or with the module off in between): settle it now.
            if (Phase == FestivalPhase.Running && _dayNightCycle.DayNumber > FestivalDay) End("loaded after its day");
            else if (Phase == FestivalPhase.Called && _dayNightCycle.DayNumber > FestivalDay) End("its day passed while the festival code was off");
            else if (Phase == FestivalPhase.Called && _dayNightCycle.DayNumber == FestivalDay) Start("loaded on its day");
            _showClock = HoursToday;   // a reload never replays lanterns already launched
            _lastHour = (int)HoursToday;
            Debug.Log(Log + "active; phase " + Phase + ", festival day " + FestivalDay + ", last cycle " + LastCycle + ", Tradition "
                      + Tradition + ", auto-call " + AutoCall + "; fireworks " + (_fireworks.Available ? "available" : "off (" + _fireworks.Unavailable + ")")
                      + "; day off " + (FestivalGoer.InsertionError == null ? "ok" : "off (" + FestivalGoer.InsertionError + ")"));
        }

        [OnEvent]
        public void OnDaytimeStart(DaytimeStartEvent e)
        {
            try { Advance("dawn of day " + _dayNightCycle.DayNumber); }
            catch (Exception ex) { Debug.LogError(Log + "dawn update failed: " + ex); }
        }

        public void Tick()
        {
            if (!Active) return;
            try
            {
                int hour = (int)HoursToday;
                if (hour != _lastHour)
                {
                    _lastHour = hour;
                    Advance("hour " + hour);
                    TryAutoCall();
                    foreach (var square in _squares) square.UpdateLights();
                }
                RunShow();
            }
            catch (Exception ex) { Debug.LogError(Log + "tick failed: " + ex); }
        }

        // ------------------------------------------------------------------ registration

        internal void AddSquare(FestivalSquare square)
        {
            if (!_squares.Contains(square)) _squares.Add(square);
            Changed?.Invoke();
        }

        internal void RemoveSquare(FestivalSquare square)
        {
            if (_squares.Remove(square)) Changed?.Invoke();
        }

        internal void AddGoer(FestivalGoer goer)
        {
            if (!_goers.Contains(goer)) _goers.Add(goer);
        }

        internal void RemoveGoer(FestivalGoer goer)
        {
            _goers.Remove(goer);
            _attended.Remove(goer);
        }

        /// <summary>The finished square a colonist of this district celebrates at, if any.</summary>
        public FestivalSquare SquareFor(DistrictCenter district)
        {
            if (!district) return null;
            foreach (var s in _squares)
                if (s && s.IsFinished && s.District == district) return s;
            return null;
        }

        public bool KeepsWorking(string workplaceTemplate) => workplaceTemplate != null && _keepWorking.Contains(workplaceTemplate);

        // ------------------------------------------------------------------ calling

        /// <summary>Why the festival cannot be called from this square now, as player text; null when it can.</summary>
        public string WhyNot(FestivalSquare square, FestivalStock stock)
        {
            if (!Active) return _loc.T("Pandaborn.Festival.Off");
            if (Phase == FestivalPhase.Called) return _loc.T("Pandaborn.Festival.Status.Called", Hours(HoursUntilStart));
            if (Phase == FestivalPhase.Running) return _loc.T("Pandaborn.Festival.Status.Running");
            if (!CycleAllows) return _loc.T("Pandaborn.Festival.Status.NextCycle", NextAllowedCycle.ToString(CultureInfo.InvariantCulture));
            if (square == null || !square.IsFinished) return _loc.T("Pandaborn.Festival.Status.Unfinished");
            if (!square.District) return _loc.T("Pandaborn.Festival.Status.NoDistrict");
            if (stock == null || !stock.Ready) return _loc.T("Pandaborn.Festival.Status.NotStocked");
            return null;
        }

        public float HoursUntilStart => Phase == FestivalPhase.Called ? Mathf.Max(0f, (FestivalDay - _dayNightCycle.PartialDayNumber) * 24f) : 0f;

        /// <summary>Calls the festival from a square: takes the goods from its district, the festival begins at the next dawn.</summary>
        public bool Call(FestivalSquare square, bool auto)
        {
            if (!Active || square == null) return false;
            var stock = FestivalStock.Count(square.District, Spec);
            if (WhyNot(square, stock) != null) return false;
            bool grand = stock.GrandReady;
            var taken = FestivalStock.Take(square.District, Spec, stock, grand);
            Phase = FestivalPhase.Called;
            FestivalDay = _dayNightCycle.DayNumber + 1;
            Grand = grand;
            Persist();
            Debug.Log(Log + (auto ? "auto-" : "") + "called for day " + FestivalDay + (grand ? " (grand)" : "") + "; took "
                      + string.Join(", ", taken.Select(t => t.GoodId + " " + t.Amount)));
            _messenger.Post(_loc.T(grand ? "Pandaborn.Festival.Message.CalledGrand" : "Pandaborn.Festival.Message.Called"));
            Changed?.Invoke();
            return true;
        }

        public void SetAutoCall(bool on)
        {
            if (AutoCall == on) return;
            AutoCall = on;
            Persist();
            Changed?.Invoke();
            if (on) TryAutoCall();
        }

        private void TryAutoCall()
        {
            if (!AutoCall || Phase != FestivalPhase.None || !CycleAllows) return;
            // never in bad weather, nor the day before it starts: the festival is a fair-weather holiday when no one chose it
            if (_weatherService.IsHazardousWeather || _weatherService.NextDayIsHazardousWeather()) return;
            foreach (var square in _squares.ToList())
            {
                if (!square || !square.IsFinished) continue;
                var stock = FestivalStock.Count(square.District, Spec);
                if (stock.Ready && Call(square, auto: true)) return;
            }
        }

        // ------------------------------------------------------------------ the day itself

        private void Advance(string why)
        {
            if (!Active) return;
            if (Phase == FestivalPhase.Called && _dayNightCycle.DayNumber >= FestivalDay) Start(why);
            if (Phase == FestivalPhase.Running && _dayNightCycle.DayNumber > FestivalDay) End(why);
        }

        private void Start(string why)
        {
            Phase = FestivalPhase.Running;
            FestivalDay = _dayNightCycle.DayNumber;
            LastCycle = _gameCycleService.Cycle;
            _attended.Clear();
            _showClock = HoursToday;
            Persist();
            Debug.Log(Log + "started (" + why + "), day " + FestivalDay + ", cycle " + LastCycle + (Grand ? ", grand" : ""));
            _messenger.Post(_loc.T(Grand ? "Pandaborn.Festival.Message.StartedGrand" : "Pandaborn.Festival.Message.Started"));
            foreach (var square in _squares) square.UpdateLights();
            Changed?.Invoke();
        }

        private void End(string why)
        {
            int granted = 0;
            foreach (var goer in _goers.ToList())
                if (goer && GrantFestive(goer)) granted++;
            _attended.Clear();
            Phase = FestivalPhase.None;
            Tradition++;
            Count++;
            bool grand = Grand;
            Grand = false;
            Persist();
            Debug.Log(Log + "ended (" + why + "); festive spirit for " + granted + " colonists; Tradition " + Tradition);
            _messenger.Post(_loc.T("Pandaborn.Festival.Message.Ended", Tradition.ToString(CultureInfo.InvariantCulture)));
            foreach (var square in _squares) square.UpdateLights();
            try { TraditionChanged?.Invoke(Tradition); }
            catch (Exception e) { Debug.LogError(Log + "Tradition update failed: " + e); }
            Changed?.Invoke();
        }

        /// <summary>A colonist reached the square: festive spirit now (the end of the festival gives it to everyone else).</summary>
        internal void Attend(FestivalGoer goer)
        {
            if (_attended.Add(goer)) GrantFestive(goer);
        }

        public bool HasAttended(FestivalGoer goer) => _attended.Contains(goer);

        private bool GrantFestive(FestivalGoer goer)
        {
            bool any = goer.FillNeed(Spec.FestiveNeedId);
            if (Grand && !string.IsNullOrEmpty(Spec.GrandNeedId)) any |= goer.FillNeed(Spec.GrandNeedId);
            return any;
        }

        // ------------------------------------------------------------------ the show

        private void RunShow()
        {
            if (!IsHoliday) { _showClock = -1f; return; }
            float now = HoursToday;
            if (_showClock < 0f) _showClock = now;
            float from = _showClock;
            _showClock = now;
            if (now <= from || _squares.Count == 0) return;
            int lanterns = Math.Max(0, Spec.LanternRises);
            const float lanternSpan = 1.75f;
            for (int i = 0; i < lanterns; i++)
            {
                float t = Spec.ShowStartHours + 0.25f + i * lanternSpan / lanterns;
                if (t > from && t <= now) LaunchEverywhere(Spec.LanternFireworkIds, i, lantern: true);
            }
            if (!Grand) return;
            int bursts = Math.Max(0, Spec.Bursts);
            const float burstSpan = 2.5f;
            for (int i = 0; i < bursts; i++)
            {
                float t = Spec.FireworksStartHours + i * burstSpan / bursts;
                if (t > from && t <= now) LaunchEverywhere(Spec.BurstFireworkIds, i, lantern: false);
            }
        }

        private void LaunchEverywhere(System.Collections.Immutable.ImmutableArray<string> ids, int index, bool lantern)
        {
            if (ids.IsDefaultOrEmpty) return;
            for (int s = 0; s < _squares.Count; s++)
            {
                var square = _squares[s];
                if (!square || !square.IsFinished) continue;
                string id = ids[(index + s) % ids.Length];
                if (square.Launch(_fireworks, id, lantern))
                {
                    if (lantern) LanternsLaunched++;
                    else BurstsLaunched++;
                }
            }
        }

        // ------------------------------------------------------------------ state

        private void ReadState()
        {
            Phase = FestivalPhase.None;
            if (!_store.TryGet(StoreFeature, out int version, out string payload) || version != StoreVersion) return;
            var v = Payload.Parse(payload);
            Phase = Enum.TryParse(Get(v, "phase"), out FestivalPhase p) ? p : FestivalPhase.None;
            FestivalDay = Int(v, "day", -1);
            Grand = Get(v, "grand") == "1";
            LastCycle = Int(v, "last", -1);
            Tradition = Math.Max(0, Int(v, "tradition", 0));
            AutoCall = Get(v, "auto") == "1";
            Count = Math.Max(0, Int(v, "count", 0));
            if (Phase != FestivalPhase.None && FestivalDay < 0) Phase = FestivalPhase.None;
        }

        private void Persist()
        {
            _store.Set(StoreFeature, StoreVersion, Payload.Write(new[]
            {
                new KeyValuePair<string, string>("phase", Phase.ToString()),
                new KeyValuePair<string, string>("day", FestivalDay.ToString(CultureInfo.InvariantCulture)),
                new KeyValuePair<string, string>("grand", Grand ? "1" : "0"),
                new KeyValuePair<string, string>("last", LastCycle.ToString(CultureInfo.InvariantCulture)),
                new KeyValuePair<string, string>("tradition", Tradition.ToString(CultureInfo.InvariantCulture)),
                new KeyValuePair<string, string>("auto", AutoCall ? "1" : "0"),
                new KeyValuePair<string, string>("count", Count.ToString(CultureInfo.InvariantCulture))
            }));
        }

        private static string Get(Dictionary<string, string> v, string key) => v.TryGetValue(key, out var s) ? s : null;

        private static int Int(Dictionary<string, string> v, string key, int fallback) =>
            int.TryParse(Get(v, key), NumberStyles.Integer, CultureInfo.InvariantCulture, out int i) ? i : fallback;

        internal static string Hours(float hours) => Mathf.CeilToInt(hours).ToString(CultureInfo.InvariantCulture);

        // ------------------------------------------------------------------ tests

        /// <summary>Test hook: sets Tradition (and unlocks what it earns).</summary>
        public void DevSetTradition(int value)
        {
            Tradition = Math.Max(0, value);
            Persist();
            TraditionChanged?.Invoke(Tradition);
            Changed?.Invoke();
        }

        /// <summary>Test hook: forgets the once-per-cycle rule.</summary>
        public void DevResetCycleRule()
        {
            LastCycle = -1;
            Persist();
            Changed?.Invoke();
        }
    }
}
