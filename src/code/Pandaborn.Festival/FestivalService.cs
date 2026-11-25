using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using Pandaborn.Core;
using Pandaborn.Specs;
using Timberborn.BaseComponentSystem;
using Timberborn.Beavers;
using Timberborn.EntitySystem;
using Timberborn.GameCycleSystem;
using Timberborn.GameDistricts;
using Timberborn.GameFactionSystem;
using Timberborn.Localization;
using Timberborn.SingletonSystem;
using Timberborn.TemplateSystem;
using Timberborn.TickSystem;
using Timberborn.TimeSystem;
using Timberborn.WeatherSystem;
using Timberborn.WindSystem;
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
    /// festival runs from the next dawn to the dawn after.
    ///
    /// A festival belongs to ONE district, the district of the square that called it: its colonists take the day off
    /// (except the crews of the KeepWorkingTemplates workplaces, in their working hours), gather at that square at dusk
    /// for the rising lanterns (and fireworks, if grand), and end festive. Other districts work as usual and are not
    /// festive. The village's Tradition rises by one, and there is at most one festival per cycle in the whole village
    /// (one counter, so a second district cannot double Tradition). A colony with one district sees no difference from
    /// "the whole village".
    ///
    /// The game is a festival game when the faction's adult template carries PandabornFestivalSpec (Inkpaws only).
    /// Saved state (store "Festival", version 1): phase, festival day, grand, last festival cycle, Tradition, auto-call,
    /// count, and (added 2026-11-25, optional) the festival's district and calling square by entity id. A save without a
    /// district (written before the district rule) is a village-wide festival, as it was then. Nothing else is saved:
    /// the day off is a root behaviour (FestivalGoer), the show is computed from the clock.
    /// </summary>
    public class FestivalService : ILoadableSingleton, IPostLoadableSingleton, ITickableSingleton
    {
        public const string StoreFeature = "Festival";
        private const int StoreVersion = 1;
        private const string Log = "[Pandaborn.Festival] ";

        /// <summary>Lanterns leaving the square all evening, per second of the particles' own time: 0.65 with the prefab's
        /// 25 to 40 s life keeps about 21 in the sky at once (FestivalRules.SteadySkyLanterns), a new one every 1.5 s.</summary>
        public const float SkyLanternsPerSecond = 0.65f;

        /// <summary>The prefab's longest lantern life in its own seconds (PandabornAttachmentsBuilder.MakeLanternRise):
        /// how much of the evening a sky is filled with when it starts late (a load in the middle of the show).</summary>
        public const float SkyLanternMaxLife = 40f;

        /// <summary>The dense release starts this long after the gathering does (15.5 + 0.25 = 15.75 h).</summary>
        public const float ReleaseDelayHours = 0.25f;

        /// <summary>The dense release: Spec.LanternRises lanterns over this many game hours (0.3 h is 5.8 s at game
        /// speed 1).</summary>
        public const float ReleaseSpanHours = 0.3f;

        /// <summary>The comet rockets (the lanterns' stand-in without the lantern art, and a Grand Festival's extra):
        /// Spec.LanternRises of them over this many game hours.</summary>
        public const float CometSpanHours = 1.75f;

        /// <summary>The bursts of a Grand Festival: Spec.Bursts over this many game hours from FireworksStartHours.</summary>
        public const float BurstSpanHours = 2.5f;

        private readonly TemplateService _templateService;
        private readonly PandabornStore _store;
        private readonly Messenger _messenger;
        private readonly ILoc _loc;
        private readonly IDayNightCycle _dayNightCycle;
        private readonly GameCycleService _gameCycleService;
        private readonly WeatherService _weatherService;
        private readonly EventBus _eventBus;
        private readonly FestivalFireworks _fireworks;
        private readonly FestivalSounds _sounds;
        private readonly FactionService _factionService;
        private readonly WindService _windService;
        private readonly NonlinearAnimationManager _nonlinearAnimationManager;
        private readonly EntityRegistry _entityRegistry;
        private readonly DistrictCenterRegistry _districtCenterRegistry;

        private readonly List<FestivalSquare> _squares = new List<FestivalSquare>();
        private readonly List<FestivalGoer> _goers = new List<FestivalGoer>();
        private readonly HashSet<FestivalGoer> _attended = new HashSet<FestivalGoer>();
        private readonly List<int> _due = new List<int>();
        private HashSet<string> _keepWorking = new HashSet<string>(StringComparer.Ordinal);
        private int _lastHour = -1;
        private float _showClock = -1f;
        private bool _skyTail;
        private Guid _districtId = Guid.Empty;
        private Guid _squareId = Guid.Empty;
        private DistrictCenter _district;
        private readonly List<string> _faults = new List<string>();

        public FestivalService(TemplateService templateService, PandabornStore store, Messenger messenger, ILoc loc, IDayNightCycle dayNightCycle,
                               GameCycleService gameCycleService, WeatherService weatherService, EventBus eventBus, FestivalFireworks fireworks,
                               FestivalSounds sounds, FactionService factionService, WindService windService,
                               NonlinearAnimationManager nonlinearAnimationManager, EntityRegistry entityRegistry,
                               DistrictCenterRegistry districtCenterRegistry)
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
            _sounds = sounds;
            _factionService = factionService;
            _windService = windService;
            _nonlinearAnimationManager = nonlinearAnimationManager;
            _entityRegistry = entityRegistry;
            _districtCenterRegistry = districtCenterRegistry;
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

        /// <summary>Lanterns (lantern particles, or their comet stand-ins), a Grand Festival's extra comets and its
        /// bursts launched in this session (tests).</summary>
        public int LanternsLaunched { get; private set; }

        public int CometsLaunched { get; private set; }

        public int BurstsLaunched { get; private set; }

        public IReadOnlyList<FestivalSquare> Squares => _squares;

        /// <summary>"ok", or why the show's fireworks are off.</summary>
        public string FireworksStatus => _fireworks.Available ? "ok" : _fireworks.Unavailable;

        public IReadOnlyList<FestivalGoer> Goers => _goers;

        public event Action Changed;

        /// <summary>Raised with the new Tradition after a festival.</summary>
        public event Action<int> TraditionChanged;

        /// <summary>Today is the festival day (dawn to the next dawn) somewhere in the village.</summary>
        public bool IsHoliday => Active && Phase == FestivalPhase.Running && _dayNightCycle.DayNumber == FestivalDay;

        public float HoursToday => _dayNightCycle.HoursPassedToday;

        /// <summary>The evening gathering: everyone off duty comes to the square for the lanterns.</summary>
        public bool IsShowTime => IsHoliday && HoursToday >= Spec.ShowStartHours && HoursToday < Spec.ShowEndHours;

        public int CurrentCycle => _gameCycleService.Cycle;

        /// <summary>The first cycle in which a festival may be called again.</summary>
        public int NextAllowedCycle => FestivalRules.NextAllowedCycle(LastCycle);

        public bool CycleAllows => CurrentCycle >= NextAllowedCycle;

        // ------------------------------------------------------------------ the festival's district

        /// <summary>The festival has no district on record (a save from before the district rule): everyone celebrates.</summary>
        public bool VillageWide => _districtId == Guid.Empty;

        /// <summary>The district of the called or running festival (after it, of the last one); null when village-wide or
        /// when that district centre is gone (then nobody is on holiday and no square hosts).</summary>
        public DistrictCenter FestivalDistrict
        {
            get
            {
                if (_districtId == Guid.Empty) return null;
                if (!_district)
                {
                    _district = null;
                    try
                    {
                        var entity = _entityRegistry.GetEntity(_districtId);
                        if (entity) _district = entity.GetComponent<DistrictCenter>();
                    }
                    catch (Exception) { }
                }
                return _district;
            }
        }

        /// <summary>Colonists of this district have the day off today.</summary>
        public bool IsHolidayFor(DistrictCenter district)
        {
            if (!IsHoliday) return false;
            if (VillageWide) return true;
            return district && district == FestivalDistrict;
        }

        /// <summary>The called or running festival is held at this square: it is finished and in the festival's district.</summary>
        public bool Hosts(FestivalSquare square)
        {
            if (!Active || Phase == FestivalPhase.None || !square || !square.IsFinished) return false;
            if (VillageWide) return true;
            var district = square.District;
            return district && district == FestivalDistrict;
        }

        /// <summary>More than one district: the texts name the festival's district.</summary>
        public bool ManyDistricts
        {
            get
            {
                try { return _districtCenterRegistry.FinishedDistrictCenters.Count > 1; }
                catch (Exception) { return false; }
            }
        }

        /// <summary>The festival district's name for texts ("" when village-wide or gone).</summary>
        public string FestivalDistrictName
        {
            get
            {
                try { var d = FestivalDistrict; return d ? d.DistrictName : ""; }
                catch (Exception) { return ""; }
            }
        }

        /// <summary>The texts name the district: there are several, and the festival has one.</summary>
        public bool NamesDistrict => !VillageWide && ManyDistricts && FestivalDistrictName.Length > 0;

        // ------------------------------------------------------------------ lifecycle

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
            if (!Active)
            {
                // shipped but its data not switched on: say so in the feature report (games of our faction only)
                if (_factionService.Current?.Id == FeatureNotices.FactionId)
                    FeatureRegistry.ReportNoData("Festival", "the faction's adult template has no PandabornFestivalSpec");
                return;
            }
            // every check is made again in each game, so each fault is this game's (forgotten when the next one starts)
            _faults.Clear();
            FestivalGoer.ResetForGame();
            if (FestivalGoer.CheckInsertion() != null) Fault("no day off (" + FestivalGoer.InsertionError + ")");
            if (!_fireworks.Available) Fault("no fireworks in the sky (" + _fireworks.Unavailable + ")");
            _keepWorking = new HashSet<string>(Spec.KeepWorkingTemplates.IsDefault ? Enumerable.Empty<string>() : Spec.KeepWorkingTemplates, StringComparer.Ordinal);
            ReadState();
            _eventBus.Register(this);
        }

        public void PostLoad()
        {
            if (!Active) return;
            try
            {
                // A save made before a festival's day ended, loaded later (or with the module off in between): settle it now.
                if (Phase == FestivalPhase.Running && _dayNightCycle.DayNumber > FestivalDay) End("loaded after its day");
                else if (Phase == FestivalPhase.Called && _dayNightCycle.DayNumber > FestivalDay) End("its day passed while the festival code was off");
                else if (Phase == FestivalPhase.Called && _dayNightCycle.DayNumber == FestivalDay) Start("loaded on its day");
            }
            catch (Exception e) { Debug.LogError(Log + "settling the saved festival failed: " + e); }
            _showClock = HoursToday;   // a reload never replays lanterns already launched
            _lastHour = (int)HoursToday;
            Debug.Log(Log + "active; phase " + Phase + ", festival day " + FestivalDay + ", district "
                      + (VillageWide ? "(village-wide)" : FestivalDistrict ? FestivalDistrictName : "(gone)") + ", last cycle " + LastCycle
                      + ", Tradition " + Tradition + ", auto-call " + AutoCall + "; fireworks "
                      + (_fireworks.Available ? "available" : "off (" + _fireworks.Unavailable + ")")
                      + "; day off " + (FestivalGoer.InsertionError == null ? "ok" : "off (" + FestivalGoer.InsertionError + ")"));
        }

        /// <summary>Dawn. Not DaytimeStartEvent: GameCycleService moves the cycle on in its own handler of that event, and
        /// whether it runs before ours is only load order; it posts this one once the cycle and the cycle day are current,
        /// so a festival held on the first day of a cycle is booked to that cycle (the once-a-cycle rule).</summary>
        [OnEvent]
        public void OnCycleDayStarted(CycleDayStartedEvent e)
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
                    UpdateLights();
                }
                RunShow();
            }
            catch (Exception ex) { Debug.LogError(Log + "tick failed: " + ex); }
        }

        // ------------------------------------------------------------------ registration

        internal void AddSquare(FestivalSquare square)
        {
            if (!_squares.Contains(square)) _squares.Add(square);
            RaiseChanged();
        }

        internal void RemoveSquare(FestivalSquare square)
        {
            if (_squares.Remove(square)) RaiseChanged();
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

        /// <summary>Something of the festival does not work in this game: said in the feature report, every fault of the
        /// game in one line.</summary>
        internal void Fault(string what)
        {
            if (!_faults.Contains(what)) _faults.Add(what);
            FeatureRegistry.ReportDegradedInGame("Festival", string.Join("; ", _faults));
        }

        /// <summary>What a festival notice is about in the notification log: the square it is held at, else its district's
        /// centre; null (the Core's default) only for a village-wide festival of an old save without a square.</summary>
        private BaseComponent NoticeSubject
        {
            get
            {
                try
                {
                    var district = FestivalDistrict;
                    if (district)
                    {
                        var square = SquareFor(district);
                        return square ? (BaseComponent)square : district;
                    }
                    foreach (var s in _squares)
                        if (s && s.IsFinished && (_squareId == Guid.Empty || s.EntityId == _squareId)) return s;
                }
                catch (Exception) { }
                return null;
            }
        }

        /// <summary>A listener's failure must never stop the festival, or a building being finished or removed.</summary>
        private void RaiseChanged()
        {
            try { Changed?.Invoke(); }
            catch (Exception e) { Debug.LogError(Log + "a festival listener failed: " + e); }
        }

        private void UpdateLights()
        {
            foreach (var square in _squares)
                if (square) square.UpdateLights();
        }

        /// <summary>The finished square a colonist of this district celebrates at, if any: the square that called the
        /// festival when it stands in that district, else the district's first.</summary>
        public FestivalSquare SquareFor(DistrictCenter district)
        {
            if (!district) return null;
            FestivalSquare first = null;
            foreach (var s in _squares)
            {
                if (!s || !s.IsFinished || s.District != district) continue;
                if (_squareId != Guid.Empty && s.EntityId == _squareId) return s;
                if (first == null) first = s;
            }
            return first;
        }

        public bool KeepsWorking(string workplaceTemplate) => workplaceTemplate != null && _keepWorking.Contains(workplaceTemplate);

        // ------------------------------------------------------------------ calling

        /// <summary>Why the festival cannot be called from this square now, as player text; null when it can.</summary>
        public string WhyNot(FestivalSquare square, FestivalStock stock)
        {
            if (!Active) return _loc.T("Pandaborn.Festival.Off");
            // a festival called or held in another district: say where (one festival a cycle for the whole village)
            bool elsewhere = Phase != FestivalPhase.None && !VillageWide && square != null && FestivalDistrictName.Length > 0
                             && square.District != FestivalDistrict;
            if (Phase == FestivalPhase.Called)
                return elsewhere ? _loc.T("Pandaborn.Festival.Status.CalledElsewhere", FestivalDistrictName, Hours(HoursUntilStart))
                                 : _loc.T("Pandaborn.Festival.Status.Called", Hours(HoursUntilStart));
            if (Phase == FestivalPhase.Running)
                return elsewhere ? _loc.T("Pandaborn.Festival.Status.RunningElsewhere", FestivalDistrictName)
                                 : _loc.T("Pandaborn.Festival.Status.Running");
            if (!CycleAllows) return _loc.T("Pandaborn.Festival.Status.NextCycle", NextAllowedCycle.ToString(CultureInfo.InvariantCulture));
            if (square == null || !square.IsFinished) return _loc.T("Pandaborn.Festival.Status.Unfinished");
            if (!square.District) return _loc.T("Pandaborn.Festival.Status.NoDistrict");
            if (stock == null || !stock.Ready) return _loc.T("Pandaborn.Festival.Status.NotStocked");
            return null;
        }

        public float HoursUntilStart => Phase == FestivalPhase.Called ? Mathf.Max(0f, (FestivalDay - _dayNightCycle.PartialDayNumber) * 24f) : 0f;

        /// <summary>Calls the festival from a square: takes the goods from its district, and the festival begins there at
        /// the next dawn.</summary>
        public bool Call(FestivalSquare square, bool auto)
        {
            if (!Active || square == null) return false;
            var district = square.District;
            var stock = FestivalStock.Count(district, Spec);
            if (WhyNot(square, stock) != null) return false;
            bool grand = stock.GrandReady;
            var taken = FestivalStock.Take(district, Spec, stock, grand);
            Phase = FestivalPhase.Called;
            FestivalDay = FestivalRules.FestivalDayFor(_dayNightCycle.DayNumber);
            Grand = grand;
            _district = district;
            _districtId = IdOf(district);
            _squareId = square.EntityId;
            Persist();
            Debug.Log(Log + (auto ? "auto-" : "") + "called for day " + FestivalDay + (grand ? " (grand)" : "") + " in district '"
                      + FestivalDistrictName + "'; took " + string.Join(", ", taken.Select(t => t.GoodId + " " + t.Amount)));
            _messenger.Post(_loc.T(grand ? "Pandaborn.Festival.Message.CalledGrand" : "Pandaborn.Festival.Message.Called"), square);
            UpdateLights();
            RaiseChanged();
            return true;
        }

        public void SetAutoCall(bool on)
        {
            if (AutoCall == on) return;
            AutoCall = on;
            Persist();
            RaiseChanged();
            if (on) TryAutoCall();
        }

        private void TryAutoCall()
        {
            if (!AutoCall || Phase != FestivalPhase.None || !CycleAllows) return;
            // never in bad weather, nor the day before it starts: the festival is a fair-weather holiday when no one chose it
            if (_weatherService.IsHazardousWeather || _weatherService.NextDayIsHazardousWeather()) return;
            // with several districts the turn passes on: squares of the district that held the last festival are asked last
            var last = FestivalDistrict;
            for (int pass = 0; pass < 2; pass++)
            {
                foreach (var square in _squares.ToList())
                {
                    if (!square || !square.IsFinished || !square.District) continue;
                    bool lastHost = last && square.District == last;
                    if (lastHost != (pass == 1)) continue;
                    var stock = FestivalStock.Count(square.District, Spec);
                    if (stock.Ready && Call(square, auto: true)) return;
                }
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
            if (NamesDistrict)
                _messenger.Post(_loc.T(Grand ? "Pandaborn.Festival.Message.StartedGrandDistrict" : "Pandaborn.Festival.Message.StartedDistrict",
                                       FestivalDistrictName), NoticeSubject);
            else
                _messenger.Post(_loc.T(Grand ? "Pandaborn.Festival.Message.StartedGrand" : "Pandaborn.Festival.Message.Started"), NoticeSubject);
            _sounds.Play2D(FestivalSounds.Firecrackers);
            UpdateLights();
            RaiseChanged();
        }

        private void End(string why)
        {
            // everyone of the festival's district ends festive, whether or not they reached the square
            int granted = 0;
            bool everyone = VillageWide;
            var district = FestivalDistrict;
            foreach (var goer in _goers.ToList())
            {
                try
                {
                    if (!goer || !(everyone || (district && goer.District == district))) continue;
                    if (GrantFestive(goer)) granted++;
                }
                catch (Exception e) { Debug.LogError(Log + "festive spirit for one colonist failed: " + e.Message); }
            }
            bool named = NamesDistrict;
            string districtName = FestivalDistrictName;
            var subject = NoticeSubject;
            _attended.Clear();
            Phase = FestivalPhase.None;
            Tradition++;
            Count++;
            Grand = false;
            Persist();
            Debug.Log(Log + "ended (" + why + "); festive spirit for " + granted + " colonists; Tradition " + Tradition);
            if (named)
                _messenger.Post(_loc.T("Pandaborn.Festival.Message.EndedDistrict", districtName, Tradition.ToString(CultureInfo.InvariantCulture)), subject);
            else
                _messenger.Post(_loc.T("Pandaborn.Festival.Message.Ended", Tradition.ToString(CultureInfo.InvariantCulture)), subject);
            UpdateLights();
            try { TraditionChanged?.Invoke(Tradition); }
            catch (Exception e) { Debug.LogError(Log + "Tradition update failed: " + e); }
            RaiseChanged();
        }

        /// <summary>A colonist reached the square: festive spirit now (the end of the festival gives it to everyone else
        /// of the district).</summary>
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

        private static Guid IdOf(BaseComponent component)
        {
            try
            {
                var entity = component ? component.GetComponent<EntityComponent>() : null;
                return entity ? entity.EntityId : Guid.Empty;
            }
            catch (Exception) { return Guid.Empty; }
        }

        // ------------------------------------------------------------------ the show

        /// <summary>The drum at each hosting square through the gathering, firecrackers as it starts. Kept per square, so
        /// a square finished, removed or reconnected during the show is right at the next tick.</summary>
        private void UpdateShowSounds()
        {
            bool show = IsShowTime;
            foreach (var square in _squares)
            {
                if (!square) continue;
                bool on = show && Hosts(square);
                if (on == square.ShowSoundOn) continue;
                square.ShowSoundOn = on;
                if (on) _sounds.Play3D(square.SoundEmitter, FestivalSounds.Firecrackers);
                _sounds.Loop(square.SoundEmitter, FestivalSounds.Drum, on);
            }
        }

        /// <summary>
        /// The lantern sky over every hosting square that has the lantern art: on through the show, a lantern leaving the
        /// square every second or two; off after it, and the last ones fade. The particles run on the game's nonlinear
        /// animation clock (the square root of the game speed, as the game runs its own smoke and sparks, see
        /// NonLinearParticlesSpeedMultiplier): they rise 1.7 times as fast at speed 2 and 2.6 times at speed 3, stand
        /// still when the game is paused, and the sky holds the same number at every speed (rate and life are both in
        /// the particles' own seconds). Real, unscaled time was rejected: lanterns would keep rising through a pause,
        /// and at speed 3 the whole show lasts 18 real seconds, less than one lantern's life.
        /// </summary>
        private void UpdateSky()
        {
            bool show = IsShowTime;
            if (!show && !_skyTail) return;
            float speed = 1f;
            try { speed = _nonlinearAnimationManager.SpeedMultiplier; } catch (Exception) { }
            if (speed <= 0f) speed = 1f;   // paused: the scaled clock stands still anyway
            var drift = Vector3.zero;
            try
            {
                var w = _windService.WindDirection;
                // 0.10 to 0.30 m/s: 3 to 10 m downwind over a lantern's life, less than its climb (9 to 26 m)
                float strength = 0.10f + 0.20f * Mathf.Clamp01(_windService.WindStrength);
                drift = new Vector3(w.x, 0f, w.y) * strength;
            }
            catch (Exception) { }
            // a sky that starts late (a load in the middle of the show, a square finished during it) starts filled
            float prewarm = 0f;
            if (show) prewarm = Mathf.Clamp((HoursToday - Spec.ShowStartHours) / 24f * _dayNightCycle.DayLengthInSeconds, 0f, SkyLanternMaxLife);
            bool tail = false;
            foreach (var square in _squares)
            {
                if (!square) continue;
                bool on = show && Hosts(square);
                if (!on && !square.SkyActive) continue;
                square.UpdateSky(on, SkyLanternsPerSecond, drift, speed, prewarm);
                tail |= square.SkyActive;
            }
            _skyTail = tail;
        }

        /// <summary>
        /// The launches due since the last tick, from the clock (so nothing is launched twice and a reload launches only
        /// what is still due):
        ///   * a square with the lantern art: the dense release, LanternRises lanterns over ReleaseSpanHours from
        ///     15.75 h, with the lantern-rise sound (three times across the release, never in the steady sky);
        ///   * a square without it: one comet rocket per lantern over CometSpanHours instead (the fallback);
        ///   * a Grand Festival: the comets at every square, and the bursts from FireworksStartHours.
        /// </summary>
        private void RunShow()
        {
            UpdateShowSounds();
            UpdateSky();
            if (!IsHoliday) { _showClock = -1f; return; }
            float now = HoursToday;
            if (_showClock < 0f) _showClock = now;
            float from = _showClock;
            _showClock = now;
            if (now <= from || _squares.Count == 0) return;
            int lanterns = Math.Max(0, Spec.LanternRises);
            float start = Spec.ShowStartHours + ReleaseDelayHours;

            FestivalRules.Due(start, ReleaseSpanHours, lanterns, from, now, _due);
            foreach (int i in _due)
            {
                foreach (var square in _squares)
                {
                    if (!Hosts(square) || !square.HasLanternSky || !square.Release(1)) continue;
                    LanternsLaunched++;
                    if (i % 8 == 0) _sounds.Play3D(square.SoundEmitter, FestivalSounds.LanternRise);
                }
            }

            if (!Spec.LanternFireworkIds.IsDefaultOrEmpty)
            {
                FestivalRules.Due(start, CometSpanHours, lanterns, from, now, _due);
                foreach (int i in _due)
                {
                    for (int s = 0; s < _squares.Count; s++)
                    {
                        var square = _squares[s];
                        if (!Hosts(square)) continue;
                        bool standIn = !square.HasLanternSky;
                        if (!standIn && !Grand) continue;
                        string id = Spec.LanternFireworkIds[(i + s) % Spec.LanternFireworkIds.Length];
                        if (!square.Launch(_fireworks, id, lantern: true)) continue;
                        if (standIn) LanternsLaunched++;
                        else CometsLaunched++;
                    }
                }
            }

            if (!Grand || Spec.BurstFireworkIds.IsDefaultOrEmpty) return;
            FestivalRules.Due(Spec.FireworksStartHours, BurstSpanHours, Math.Max(0, Spec.Bursts), from, now, _due);
            foreach (int i in _due)
            {
                for (int s = 0; s < _squares.Count; s++)
                {
                    var square = _squares[s];
                    if (!Hosts(square)) continue;
                    string id = Spec.BurstFireworkIds[(i + s) % Spec.BurstFireworkIds.Length];
                    if (square.Launch(_fireworks, id, lantern: false)) BurstsLaunched++;
                }
            }
        }

        // ------------------------------------------------------------------ state

        private void ReadState()
        {
            Phase = FestivalPhase.None;
            FestivalDay = -1;
            _districtId = Guid.Empty;
            _squareId = Guid.Empty;
            _district = null;
            if (!_store.TryGet(StoreFeature, out int version, out string payload) || version != StoreVersion) return;
            var v = Payload.Parse(payload);
            Phase = Enum.TryParse(Get(v, "phase"), out FestivalPhase p) && Enum.IsDefined(typeof(FestivalPhase), p) ? p : FestivalPhase.None;
            FestivalDay = Int(v, "day", -1);
            Grand = Get(v, "grand") == "1";
            LastCycle = Int(v, "last", -1);
            Tradition = Math.Max(0, Int(v, "tradition", 0));
            AutoCall = Get(v, "auto") == "1";
            Count = Math.Max(0, Int(v, "count", 0));
            _districtId = Guid.TryParse(Get(v, "district"), out var d) ? d : Guid.Empty;
            _squareId = Guid.TryParse(Get(v, "square"), out var q) ? q : Guid.Empty;
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
                new KeyValuePair<string, string>("count", Count.ToString(CultureInfo.InvariantCulture)),
                new KeyValuePair<string, string>("district", _districtId == Guid.Empty ? "" : _districtId.ToString("N")),
                new KeyValuePair<string, string>("square", _squareId == Guid.Empty ? "" : _squareId.ToString("N"))
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
            try { TraditionChanged?.Invoke(Tradition); }
            catch (Exception e) { Debug.LogError(Log + "Tradition update failed: " + e); }
            RaiseChanged();
        }

        /// <summary>Test hook: forgets the once-per-cycle rule.</summary>
        public void DevResetCycleRule()
        {
            LastCycle = -1;
            Persist();
            RaiseChanged();
        }
    }
}
