using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.Linq;
using Pandaborn.Core;
using Pandaborn.Specs;
using Timberborn.Beavers;
using Timberborn.EntitySystem;
using Timberborn.GameCycleSystem;
using Timberborn.GameFactionSystem;
using Timberborn.Growing;
using Timberborn.Localization;
using Timberborn.NaturalResources;
using Timberborn.Planting;
using Timberborn.SingletonSystem;
using Timberborn.TemplateSystem;
using Timberborn.TickSystem;
using Timberborn.TimeSystem;
using UnityEngine;
using Debug = UnityEngine.Debug;

namespace Pandaborn.Flowering
{
    /// <summary>
    /// The Great Flowering (DESIGN.md, Pillar 5; docs/tech/events.md). Never before FirstCycle; announced at the start of
    /// the cycle before (a full cycle ahead); happens on day 1 of a cycle, which is always temperate weather, so never in a
    /// drought or badtide. One bamboo per Flowering, alternating in the spec's order: every grown plant of that species,
    /// planted or wild, turns into its "in flower" twin, whose harvest is bamboo seed; young plants die. The twins die
    /// SeedDays later. Young plants of the species do not grow until DormantDays after the Flowering (the planting marks
    /// stay, so farms and foresters replant on their own). Setting per save: normal, rare, off. The calendar itself is
    /// FloweringSchedule (pure, unit-tested).
    ///
    /// The map-wide change is spread over game ticks (a few milliseconds of work in each): replacing a plant deletes one
    /// entity and creates another, and thousands in one tick would freeze the game for seconds. A small farm flowers
    /// within a tick or two; a map of thousands of bamboo comes into flower as a wave over the first hours of the day.
    /// No entity is touched outside a tick (never in Load, PostLoad or an event handler).
    ///
    /// The game is a Flowering game when the faction's adult template carries PandabornFloweringSpec (Inkpaws only).
    /// Saved state (store "Flowering", version 1): setting, phase, next cycle, next species, current species, flowering day,
    /// last cycle, seed borne and lost, and (added 2026-11-25, optional) how far the change into flower has got. The twins
    /// are ordinary saved plants; holds on growth are re-applied after a load, every in-game hour and to every new plant.
    /// </summary>
    public class FloweringService : ILoadableSingleton, IPostLoadableSingleton, ITickableSingleton
    {
        public const string StoreFeature = "Flowering";
        private const int StoreVersion = 1;
        private const string Log = "[Pandaborn.Flowering] ";

        /// <summary>Work on the change into flower per game tick: until this much time has gone, but never fewer than
        /// ConvertMinPerTick plants (so it always ends: 768 ticks a day).</summary>
        private const double ConvertBudgetMs = 5.0;
        private const int ConvertMinPerTick = 8;
        private const int ConvertMaxErrors = 5;

        // how far the change into flower has got (saved as "converting")
        private const int ConvertDone = 0;
        private const int ConvertGrown = 1;      // young plants dealt with; grown plants still turning
        private const int ConvertNotBegun = 2;   // nothing done yet: young plants die first

        private readonly TemplateService _templateService;
        private readonly TemplateNameMapper _templateNameMapper;
        private readonly PandabornStore _store;
        private readonly Messenger _messenger;
        private readonly ILoc _loc;
        private readonly IDayNightCycle _dayNightCycle;
        private readonly GameCycleService _gameCycleService;
        private readonly EventBus _eventBus;
        private readonly EntityService _entityService;
        private readonly NaturalResourceFactory _naturalResourceFactory;
        private readonly FactionService _factionService;
        private readonly PlantingService _plantingService;

        private readonly HashSet<FloweringPlant> _plants = new HashSet<FloweringPlant>();
        private readonly HashSet<InFlowerPlant> _inFlower = new HashSet<InFlowerPlant>();
        private readonly Queue<FloweringPlant> _toConvert = new Queue<FloweringPlant>();
        private readonly Stopwatch _stopwatch = new Stopwatch();
        private readonly System.Random _random = new System.Random();
        private int _lastHour = -1;
        private int _seedBorne;
        private int _seedLost;
        private int _convertStage;
        private bool _convertQueued;
        private int _convertErrors;
        private int _twins;
        private int _killed;
        private bool _reheldLogged;

        public FloweringService(TemplateService templateService, TemplateNameMapper templateNameMapper, PandabornStore store, Messenger messenger,
                                ILoc loc, IDayNightCycle dayNightCycle, GameCycleService gameCycleService, EventBus eventBus,
                                EntityService entityService, NaturalResourceFactory naturalResourceFactory, FactionService factionService,
                                PlantingService plantingService)
        {
            _templateService = templateService;
            _templateNameMapper = templateNameMapper;
            _store = store;
            _messenger = messenger;
            _loc = loc;
            _dayNightCycle = dayNightCycle;
            _gameCycleService = gameCycleService;
            _eventBus = eventBus;
            _entityService = entityService;
            _naturalResourceFactory = naturalResourceFactory;
            _factionService = factionService;
            _plantingService = plantingService;
        }

        public static FloweringService Current { get; private set; }

        public PandabornFloweringSpec Spec { get; private set; }

        public bool Active => Spec != null && !Spec.Species.IsDefaultOrEmpty;

        public string Setting { get; private set; } = "normal";

        public FloweringPhase Phase { get; private set; }

        /// <summary>The cycle at whose start the next Flowering happens (-1: none scheduled).</summary>
        public int NextCycle { get; private set; } = -1;

        /// <summary>Index into Spec.Species of the next species to flower.</summary>
        public int NextSpecies { get; private set; }

        /// <summary>The species announced, in flower, or resting.</summary>
        public string Species { get; private set; }

        /// <summary>When the current Flowering began (IDayNightCycle.PartialDayNumber).</summary>
        public float FloweringDay { get; private set; } = -1f;

        public int LastCycle { get; private set; } = -1;

        /// <summary>Seed counted in this session (tests and the closing message).</summary>
        public int SeedCut { get; private set; }

        public int TwinsMade { get; private set; }

        public int YoungKilled { get; private set; }

        public int HeldNow { get; private set; }

        /// <summary>Young plants found growing again at an hourly check and held again, in this session (tests; the game
        /// resumes a plant that stops dying, and another mod may swap the growth timer under us).</summary>
        public int HeldAgain { get; private set; }

        /// <summary>Grown plants are still turning into their flowering twins (spread over ticks).</summary>
        public bool Converting => _convertStage != ConvertDone;

        /// <summary>Grown plants still waiting for their turn (tests).</summary>
        public int ConvertQueue => _toConvert.Count;

        public IReadOnlyCollection<FloweringPlant> Plants => _plants;

        public IReadOnlyCollection<InFlowerPlant> InFlower => _inFlower;

        public event Action Changed;

        public float Now => _dayNightCycle.PartialDayNumber;

        public float SeedDaysLeft => Phase == FloweringPhase.Flowering ? Mathf.Max(0f, FloweringDay + Spec.SeedDays - Now) : 0f;

        public float RestDaysLeft => Phase == FloweringPhase.Flowering || Phase == FloweringPhase.Resting
            ? Mathf.Max(0f, FloweringDay + Spec.DormantDays - Now) : 0f;

        /// <summary>Young plants of the species are held now.</summary>
        public bool Resting => Phase == FloweringPhase.Flowering || Phase == FloweringPhase.Resting;

        public void Load()
        {
            Current = this;
            try
            {
                var adult = _templateService.GetAll<AdultSpec>().FirstOrDefault();
                Spec = adult?.Blueprint?.GetSpec<PandabornFloweringSpec>();
            }
            catch (Exception e)
            {
                Debug.LogError(Log + "reading the adult template failed; the Flowering is off: " + e);
                Spec = null;
            }
            if (!Active)
            {
                if (_factionService.Current?.Id == FeatureNotices.FactionId)
                    FeatureRegistry.ReportNoData("Flowering", "the faction's adult template has no PandabornFloweringSpec");
                return;
            }
            if (!GrowthHold.Available) FeatureRegistry.ReportDegraded("Flowering", "young bamboo regrows at once after a Flowering (" + GrowthHold.Unavailable + ")");
            ReadState();
            _eventBus.Register(this);
        }

        public void PostLoad()
        {
            if (!Active) return;
            try
            {
                CatchUp("load");
                ApplyHolds(false);
                ApplyBuds();
            }
            catch (Exception e) { Debug.LogError(Log + "catching up after the load failed: " + e); }
            _lastHour = (int)_dayNightCycle.HoursPassedToday;
            Debug.Log(Log + "active; setting " + Setting + ", phase " + Phase + ", next cycle " + NextCycle + " (" + SpeciesAt(NextSpecies)
                      + "), current " + (Species ?? "-") + (Converting ? ", still coming into flower" : "") + "; growth hold "
                      + (GrowthHold.Available ? "ok" : "off (" + GrowthHold.Unavailable + ")"));
        }

        [OnEvent]
        public void OnCycleStarted(CycleStartedEvent e)
        {
            try { CatchUp("cycle " + e.Cycle + " started"); }
            catch (Exception ex) { Debug.LogError(Log + "cycle update failed: " + ex); }
        }

        public void Tick()
        {
            if (!Active) return;
            if (_convertStage != ConvertDone)
            {
                try { ConvertSome(); }
                catch (Exception ex) { ConvertFailed(ex); }
            }
            int hour = (int)_dayNightCycle.HoursPassedToday;
            if (hour == _lastHour) return;
            _lastHour = hour;
            try
            {
                Advance();
                ApplyHolds(true);
            }
            catch (Exception ex) { Debug.LogError(Log + "hourly update failed: " + ex); }
        }

        // ------------------------------------------------------------------ registration

        internal void AddPlant(FloweringPlant plant)
        {
            _plants.Add(plant);
            if (Resting && plant.Species == Species && GrowthHold.Hold(plant.Growable, out _)) HeldNow++;
            if (Phase == FloweringPhase.Announced && plant.Species == Species) plant.ShowBuds(true);
        }

        internal void RemovePlant(FloweringPlant plant) => _plants.Remove(plant);

        internal void AddInFlower(InFlowerPlant plant) => _inFlower.Add(plant);

        internal void RemoveInFlower(InFlowerPlant plant) => _inFlower.Remove(plant);

        internal void OnSeedCut(int amount) => SeedCut += amount;

        private void RaiseChanged()
        {
            try { Changed?.Invoke(); }
            catch (Exception e) { Debug.LogError(Log + "a Flowering listener failed: " + e); }
        }

        // ------------------------------------------------------------------ schedule

        private void CatchUp(string why)
        {
            if (!Active) return;
            int cycle = _gameCycleService.Cycle;
            bool off = Setting == "off";
            if (!off && NextCycle < 0) Reschedule(cycle);
            switch (FloweringSchedule.Step(off, Phase, cycle, _gameCycleService.CycleDay, NextCycle))
            {
                case ScheduleStep.Cancel: Cancel(); break;
                case ScheduleStep.Flower: Flower(why); break;
                case ScheduleStep.Postpone: NextCycle = cycle + 1; Persist(); break;   // loaded mid-cycle past its date: next cycle start
                case ScheduleStep.Announce: Announce(why, cycle); break;
            }
        }

        private void Reschedule(int cycle)
        {
            bool rare = Setting == "rare";
            int interval = FloweringSchedule.DrawInterval(_random, rare ? Spec.RareMinCycles : Spec.NormalMinCycles,
                                                          rare ? Spec.RareMaxCycles : Spec.NormalMaxCycles);
            int baseCycle = FloweringSchedule.BaseCycle(LastCycle, Spec.FirstCycle, Spec.RareDelayCycles, rare, interval);
            // a full cycle of warning: announced at the start of NextCycle - 1, which must still be ahead
            NextCycle = FloweringSchedule.Schedule(baseCycle, cycle, Phase == FloweringPhase.Idle && _gameCycleService.CycleDay <= 1);
            Persist();
        }

        private void Announce(string why, int cycle)
        {
            if (NextCycle - 1 > cycle) return;
            // a full cycle of warning: announced later than the cycle's first day (a load, a setting change), it flowers a cycle later
            NextCycle = FloweringSchedule.AnnouncedCycle(NextCycle, cycle, _gameCycleService.CycleDay, why == "dev");
            Species = SpeciesAt(NextSpecies);
            Phase = FloweringPhase.Announced;
            Persist();
            Debug.Log(Log + "announced (" + why + "): " + Species + " flowers at the start of cycle " + NextCycle);
            _messenger.Post(_loc.T("Pandaborn.Flowering.Message.Announced", PlantName(Species), NextCycle.ToString(CultureInfo.InvariantCulture)));
            ApplyBuds();
            RaiseChanged();
        }

        private void Cancel()
        {
            string species = Species;
            Phase = FloweringPhase.Idle;
            Species = null;
            Persist();
            ApplyBuds();
            Debug.Log(Log + "announcement cancelled (setting off)");
            _messenger.Post(_loc.T("Pandaborn.Flowering.Message.Cancelled", PlantName(species)));
            RaiseChanged();
        }

        /// <summary>Changes how often bamboo flowers (the per-save setting).</summary>
        public void SetSetting(string setting)
        {
            if (!Active) return;
            if (setting != "normal" && setting != "rare" && setting != "off") return;
            if (setting == Setting) return;
            Setting = setting;
            if (Phase == FloweringPhase.Idle && setting != "off") Reschedule(_gameCycleService.Cycle);
            Persist();
            Debug.Log(Log + "setting " + setting + "; next cycle " + NextCycle);
            CatchUp("setting changed");
            RaiseChanged();
        }

        // ------------------------------------------------------------------ the Flowering

        /// <summary>The Flowering begins: only state here (this runs in an event handler or in PostLoad); the plants turn
        /// in the ticks that follow (ConvertSome).</summary>
        private void Flower(string why)
        {
            Species = Species ?? SpeciesAt(NextSpecies);
            Phase = FloweringPhase.Flowering;
            FloweringDay = Now;
            LastCycle = _gameCycleService.Cycle;
            NextSpecies = (NextSpecies + 1) % Spec.Species.Length;
            NextCycle = -1;
            _seedBorne = 0;
            _seedLost = 0;
            _twins = 0;
            _killed = 0;
            SeedCut = 0;
            _toConvert.Clear();
            _convertQueued = false;
            _convertErrors = 0;
            _convertStage = ConvertNotBegun;
            Reschedule(_gameCycleService.Cycle);
            Persist();
            Debug.Log(Log + "the Flowering begins (" + why + "): " + Species + "; next " + NextCycle);
            RaiseChanged();
        }

        /// <summary>One tick's share of the change into flower.</summary>
        private void ConvertSome()
        {
            if (Phase != FloweringPhase.Flowering || Species == null) { _convertStage = ConvertDone; _toConvert.Clear(); Persist(); return; }
            if (!_convertQueued)
            {
                // first tick (or first tick after a load in the middle of it): young plants die, grown ones queue up
                bool cull = _convertStage == ConvertNotBegun;
                var grown = new List<FloweringPlant>();
                foreach (var plant in _plants.Where(p => p && p.Species == Species).ToList())
                {
                    plant.ShowBuds(false);
                    if (plant.IsDead || plant.IsHarvestedPile) continue;
                    if (plant.IsGrown) grown.Add(plant);
                    else if (cull) { plant.Living?.Die(); _killed++; YoungKilled++; }
                }
                // a wave across the map rather than a scatter
                grown.Sort((a, b) => WaveOrder(a).CompareTo(WaveOrder(b)));
                _toConvert.Clear();
                foreach (var plant in grown) _toConvert.Enqueue(plant);
                _convertQueued = true;
                _convertStage = ConvertGrown;
                Persist();
                ApplyHolds(false);
            }
            _stopwatch.Restart();
            int done = 0;
            while (_toConvert.Count > 0 && (done < ConvertMinPerTick || _stopwatch.Elapsed.TotalMilliseconds < ConvertBudgetMs))
            {
                var plant = _toConvert.Dequeue();
                done++;
                if (!plant || plant.IsDead || plant.IsHarvestedPile || !plant.IsGrown) continue;
                if (TryTurnIntoTwin(plant, out int seed))
                {
                    _twins++;
                    TwinsMade++;
                    _seedBorne += seed;
                }
                else
                {
                    plant.Living?.Die();
                    _killed++;
                    YoungKilled++;
                }
            }
            if (_toConvert.Count > 0) { Persist(); return; }
            _convertStage = ConvertDone;
            Persist();
            Debug.Log(Log + "in flower: " + Species + "; " + _twins + " in flower bearing " + _seedBorne + " seed, " + _killed
                      + " plants died");
            _messenger.Post(string.Format(CultureInfo.InvariantCulture, _loc.T("Pandaborn.Flowering.Message.Flowered"), PlantName(Species),
                                          _twins, _seedBorne, Days(Spec.SeedDays)));
            RaiseChanged();
        }

        /// <summary>A plant that cannot be replaced is skipped (it was already taken off the queue); if it keeps failing the
        /// rest of the bamboo is left as it is: an ordinary plant, never a broken tile.</summary>
        private void ConvertFailed(Exception e)
        {
            _convertErrors++;
            Debug.LogError(Log + "turning a plant into its flowering twin failed (" + _convertErrors + "): " + e);
            if (_convertErrors < ConvertMaxErrors) return;
            _toConvert.Clear();
            _convertStage = ConvertDone;
            try { Persist(); } catch (Exception) { }
            FeatureRegistry.ReportDegraded("Flowering", "some bamboo could not come into flower (" + e.GetType().Name + ")");
        }

        private static int WaveOrder(FloweringPlant plant)
        {
            var c = plant.BlockObject ? plant.BlockObject.Coordinates : Vector3Int.zero;
            return c.x + c.y;
        }

        /// <summary>Replaces a grown plant by its flowering twin on the same tile. False when the species has no twin (the
        /// caller lets the plant die); true once the original is gone, with the seed the twin bears (0 if the twin could
        /// not be placed: the tile is then empty and is replanted from its mark).</summary>
        private bool TryTurnIntoTwin(FloweringPlant plant, out int seed)
        {
            seed = 0;
            string twin = plant.Spec?.InFlowerTemplate;
            if (string.IsNullOrEmpty(twin) || !_templateNameMapper.TryGetTemplate(twin, out _)) return false;
            var coordinates = plant.BlockObject.Coordinates;
            // the game clears a planting mark under any block of another template (PlantingCoordinatesUnsetter): keep the
            // farm's or forester's mark so the tile is replanted on its own once the twin is gone
            string mark = _plantingService.GetResourceAt(coordinates);
            _entityService.Delete(plant);
            var made = _naturalResourceFactory.SpawnIgnoringConstraints(twin, coordinates);
            if (mark != null && _plantingService.GetResourceAt(coordinates) == null) _plantingService.SetPlantingCoordinates(coordinates, mark);
            if (made == null) return true;   // the original is gone either way
            made.GetComponent<Growable>()?.IncreaseGrowthProgress(1f);
            var inFlower = made.GetComponent<InFlowerPlant>();
            if (inFlower != null) seed = inFlower.SeedLeft;
            return true;
        }

        private void Advance()
        {
            if (Phase == FloweringPhase.Flowering)
            {
                // the flowered plants die over the last day of the seed time, a few each hour
                float end = FloweringDay + Spec.SeedDays;
                bool any = false;
                foreach (var twin in _inFlower.Where(t => t && t.Species == Species && !t.IsDead).ToList())
                {
                    var c = twin.BlockObject ? twin.BlockObject.Coordinates : Vector3Int.zero;
                    float dieAt = FloweringSchedule.DieAt(FloweringDay, Spec.SeedDays, FloweringSchedule.Hash01(c.x, c.y, c.z));
                    if (Now >= dieAt || Now >= end)
                    {
                        _seedLost += twin.SeedLeft;
                        twin.Living?.Die();
                        any = true;
                    }
                }
                if (any) Persist();
                if (Now >= end && !Converting)
                {
                    Phase = FloweringPhase.Resting;
                    Persist();
                    int harvested = FloweringSchedule.Harvested(_seedBorne, _seedLost);
                    Debug.Log(Log + "seed time over: " + harvested + " of " + _seedBorne + " seed harvested, " + _seedLost + " lost");
                    _messenger.Post(_loc.T("Pandaborn.Flowering.Message.SeedOver", PlantName(Species), harvested.ToString(CultureInfo.InvariantCulture),
                                           Days(RestDaysLeft)));
                    RaiseChanged();
                }
            }
            if (Phase == FloweringPhase.Resting && Now >= FloweringDay + Spec.DormantDays)
            {
                string species = Species;
                Phase = FloweringPhase.Idle;
                Species = null;
                Persist();
                foreach (var plant in _plants)
                    if (plant && plant.Species == species) GrowthHold.Release(plant.Growable);
                HeldNow = 0;
                Debug.Log(Log + species + " rests no more");
                _messenger.Post(_loc.T("Pandaborn.Flowering.Message.Regrows", PlantName(species)));
                CatchUp("rest over");
                RaiseChanged();
            }
        }

        /// <summary>
        /// Holds every young plant of the resting species. Run after a load, every in-game hour and when the Flowering
        /// begins (new plants are held as they register): a hold is not a state we set once, it is re-read from the
        /// plant's own growth timer each time, because the game resumes growth by itself when a plant stops dying, and
        /// another mod may replace the timer object altogether (TimberCommons' growth modifiers do: the audit of
        /// 2026-11-25, m6). Either way the plant grows for at most an hour before it is held again.
        /// </summary>
        private void ApplyHolds(bool hourly)
        {
            if (!Resting) return;
            int held = 0, again = 0;
            foreach (var plant in _plants)
            {
                if (!plant || plant.Species != Species || plant.IsDead) continue;
                if (!GrowthHold.Hold(plant.Growable, out bool wasGrowing)) continue;
                held++;
                if (wasGrowing) again++;
            }
            HeldNow = held;
            if (!hourly || again == 0) return;
            HeldAgain += again;
            if (_reheldLogged) return;
            _reheldLogged = true;
            Debug.Log(Log + again + " resting plant(s) were growing again and are held again (a plant that stopped dying, or another mod "
                      + "that changes growth); this is checked every in-game hour");
        }

        private void ApplyBuds()
        {
            foreach (var plant in _plants)
                if (plant) plant.ShowBuds(Phase == FloweringPhase.Announced && plant.Species == Species);
        }

        // ------------------------------------------------------------------ text helpers

        public string SpeciesAt(int index) => Active ? Spec.Species[((index % Spec.Species.Length) + Spec.Species.Length) % Spec.Species.Length] : null;

        public string PlantName(string template)
        {
            if (string.IsNullOrEmpty(template)) return "";
            try
            {
                if (_templateNameMapper.TryGetTemplate(template, out var spec))
                {
                    var label = spec.GetSpec<LabeledEntitySpec>();
                    if (label != null) return _loc.T(label.DisplayNameLocKey);
                }
            }
            catch (Exception) { }
            return template;
        }

        public bool IsTimberSpecies(string template) => template != null && _templateNameMapper.TryGetTemplate(template, out var spec)
                                                          && spec.GetSpec<Timberborn.Forestry.TreeComponentSpec>() != null;

        internal static string Days(float days) => Mathf.CeilToInt(Mathf.Max(0f, days)).ToString(CultureInfo.InvariantCulture);

        // ------------------------------------------------------------------ state

        private void ReadState()
        {
            Setting = NormalizeSetting(Spec.DefaultSetting);
            Phase = FloweringPhase.Idle;
            _convertStage = ConvertDone;
            _convertQueued = false;
            _toConvert.Clear();
            if (!_store.TryGet(StoreFeature, out int version, out string payload) || version != StoreVersion) return;
            var v = Payload.Parse(payload);
            Setting = NormalizeSetting(Get(v, "setting") ?? Setting);
            Phase = Enum.TryParse(Get(v, "phase"), out FloweringPhase p) && Enum.IsDefined(typeof(FloweringPhase), p) ? p : FloweringPhase.Idle;
            NextCycle = Int(v, "next", -1);
            NextSpecies = Math.Max(0, Int(v, "nextSpecies", 0));
            Species = Get(v, "species");
            if (string.IsNullOrEmpty(Species)) Species = null;
            FloweringDay = float.TryParse(Get(v, "day"), NumberStyles.Float, CultureInfo.InvariantCulture, out float d) ? d : -1f;
            LastCycle = Int(v, "last", -1);
            _seedBorne = Math.Max(0, Int(v, "borne", 0));
            _seedLost = Math.Max(0, Int(v, "lost", 0));
            _twins = Math.Max(0, Int(v, "twins", 0));
            _killed = Math.Max(0, Int(v, "killed", 0));
            int stage = Int(v, "converting", ConvertDone);
            if (Phase != FloweringPhase.Idle && (Species == null || !Spec.Species.Contains(Species))) { Phase = FloweringPhase.Idle; Species = null; }
            if ((Phase == FloweringPhase.Flowering || Phase == FloweringPhase.Resting) && FloweringDay < 0f) { Phase = FloweringPhase.Idle; Species = null; }
            if (Phase == FloweringPhase.Flowering && (stage == ConvertGrown || stage == ConvertNotBegun)) _convertStage = stage;
        }

        private void Persist()
        {
            _store.Set(StoreFeature, StoreVersion, Payload.Write(new[]
            {
                new KeyValuePair<string, string>("setting", Setting),
                new KeyValuePair<string, string>("phase", Phase.ToString()),
                new KeyValuePair<string, string>("next", NextCycle.ToString(CultureInfo.InvariantCulture)),
                new KeyValuePair<string, string>("nextSpecies", NextSpecies.ToString(CultureInfo.InvariantCulture)),
                new KeyValuePair<string, string>("species", Species ?? ""),
                new KeyValuePair<string, string>("day", FloweringDay.ToString("0.###", CultureInfo.InvariantCulture)),
                new KeyValuePair<string, string>("last", LastCycle.ToString(CultureInfo.InvariantCulture)),
                new KeyValuePair<string, string>("borne", _seedBorne.ToString(CultureInfo.InvariantCulture)),
                new KeyValuePair<string, string>("lost", _seedLost.ToString(CultureInfo.InvariantCulture)),
                new KeyValuePair<string, string>("twins", _twins.ToString(CultureInfo.InvariantCulture)),
                new KeyValuePair<string, string>("killed", _killed.ToString(CultureInfo.InvariantCulture)),
                new KeyValuePair<string, string>("converting", _convertStage.ToString(CultureInfo.InvariantCulture))
            }));
        }

        private static string NormalizeSetting(string s) => s == "rare" || s == "off" ? s : "normal";

        private static string Get(Dictionary<string, string> v, string key) => v.TryGetValue(key, out var s) ? s : null;

        private static int Int(Dictionary<string, string> v, string key, int fallback) =>
            int.TryParse(Get(v, key), NumberStyles.Integer, CultureInfo.InvariantCulture, out int i) ? i : fallback;

        // ------------------------------------------------------------------ tests

        /// <summary>Test hook: announce the next Flowering now (it would happen at the next cycle start).</summary>
        public void DevAnnounce()
        {
            if (!Active || Phase != FloweringPhase.Idle) return;
            NextCycle = _gameCycleService.Cycle + 1;
            Announce("dev", _gameCycleService.Cycle);
        }

        /// <summary>Test hook: the announced (or next) species flowers now, whatever the day. As at a cycle start, the
        /// plants turn over the ticks that follow (Converting).</summary>
        public void DevFlowerNow()
        {
            if (!Active) return;
            if (Phase == FloweringPhase.Idle) DevAnnounce();
            if (Phase == FloweringPhase.Announced) Flower("dev");
        }
    }
}
