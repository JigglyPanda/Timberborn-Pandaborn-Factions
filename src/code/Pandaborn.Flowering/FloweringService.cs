using System;
using System.Collections.Generic;
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

namespace Pandaborn.Flowering
{
    public enum FloweringPhase
    {
        Idle,
        /// <summary>Announced at the start of the cycle before; flowers at the start of NextCycle.</summary>
        Announced,
        /// <summary>The species is in flower: its grown plants bear seed for SeedDays, then die.</summary>
        Flowering,
        /// <summary>The flowered plants are dead; young plants of the species do not grow until DormantDays have passed.</summary>
        Resting
    }

    /// <summary>
    /// The Great Flowering (DESIGN.md, Pillar 5; docs/tech/events.md). Never before FirstCycle; announced at the start of
    /// the cycle before (a full cycle ahead); happens on day 1 of a cycle, which is always temperate weather, so never in a
    /// drought or badtide. One bamboo per Flowering, alternating in the spec's order: every grown plant of that species,
    /// planted or wild, turns into its "in flower" twin, whose harvest is bamboo seed; young plants die. The twins die
    /// SeedDays later. Young plants of the species do not grow until DormantDays after the Flowering (the planting marks
    /// stay, so farms and foresters replant on their own). Setting per save: normal, rare, off.
    ///
    /// The game is a Flowering game when the faction's adult template carries PandabornFloweringSpec (Inkpaws only).
    /// Saved state (store "Flowering", version 1): setting, phase, next cycle, next species, current species, flowering day,
    /// last cycle. The twins are ordinary saved plants; holds on growth are re-applied after a load.
    /// </summary>
    public class FloweringService : ILoadableSingleton, IPostLoadableSingleton, ITickableSingleton
    {
        public const string StoreFeature = "Flowering";
        private const int StoreVersion = 1;
        private const string Log = "[Pandaborn.Flowering] ";

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

        private readonly List<FloweringPlant> _plants = new List<FloweringPlant>();
        private readonly List<InFlowerPlant> _inFlower = new List<InFlowerPlant>();
        private readonly System.Random _random = new System.Random();
        private int _lastHour = -1;
        private int _seedBorne;
        private int _seedLost;

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

        public IReadOnlyList<FloweringPlant> Plants => _plants;

        public IReadOnlyList<InFlowerPlant> InFlower => _inFlower;

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
            CatchUp("load");
            ApplyHolds();
            ApplyBuds();
            _lastHour = (int)_dayNightCycle.HoursPassedToday;
            Debug.Log(Log + "active; setting " + Setting + ", phase " + Phase + ", next cycle " + NextCycle + " (" + SpeciesAt(NextSpecies)
                      + "), current " + (Species ?? "-") + "; growth hold " + (GrowthHold.Available ? "ok" : "off (" + GrowthHold.Unavailable + ")"));
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
            int hour = (int)_dayNightCycle.HoursPassedToday;
            if (hour == _lastHour) return;
            _lastHour = hour;
            try
            {
                Advance();
                ApplyHolds();
            }
            catch (Exception ex) { Debug.LogError(Log + "hourly update failed: " + ex); }
        }

        // ------------------------------------------------------------------ registration

        internal void AddPlant(FloweringPlant plant)
        {
            _plants.Add(plant);
            if (Resting && plant.Species == Species && GrowthHold.Hold(plant.Growable)) HeldNow++;
            if (Phase == FloweringPhase.Announced && plant.Species == Species) plant.ShowBuds(true);
        }

        internal void RemovePlant(FloweringPlant plant) => _plants.Remove(plant);

        internal void AddInFlower(InFlowerPlant plant) => _inFlower.Add(plant);

        internal void RemoveInFlower(InFlowerPlant plant) => _inFlower.Remove(plant);

        internal void OnSeedCut(int amount) => SeedCut += amount;

        // ------------------------------------------------------------------ schedule

        private void CatchUp(string why)
        {
            if (!Active) return;
            int cycle = _gameCycleService.Cycle;
            if (Setting == "off")
            {
                if (Phase == FloweringPhase.Announced) Cancel();
                return;
            }
            if (NextCycle < 0) Reschedule(cycle);
            if (Phase == FloweringPhase.Announced && cycle >= NextCycle && _gameCycleService.CycleDay <= 1) Flower(why);
            else if (Phase == FloweringPhase.Announced && cycle >= NextCycle) { NextCycle = cycle + 1; Persist(); }   // loaded mid-cycle past its date: next cycle start
            else if (Phase == FloweringPhase.Idle && cycle >= NextCycle - 1) Announce(why, cycle);
        }

        private void Reschedule(int cycle)
        {
            bool rare = Setting == "rare";
            int first = Spec.FirstCycle + (rare ? Spec.RareDelayCycles : 0);
            int min = rare ? Spec.RareMinCycles : Spec.NormalMinCycles;
            int max = rare ? Spec.RareMaxCycles : Spec.NormalMaxCycles;
            int baseCycle = LastCycle < 0 ? first : LastCycle + _random.Next(Math.Min(min, max), Math.Max(min, max) + 1);
            // a full cycle of warning: announced at the start of NextCycle - 1, which must still be ahead
            NextCycle = Math.Max(baseCycle, cycle + (Phase == FloweringPhase.Idle && _gameCycleService.CycleDay <= 1 ? 1 : 2));
            Persist();
        }

        private void Announce(string why, int cycle)
        {
            if (NextCycle - 1 > cycle) return;
            if (NextCycle <= cycle) NextCycle = cycle + 1;
            // a full cycle of warning: announced later than the cycle's first day (a load, a setting change), it flowers a cycle later
            if (why != "dev" && _gameCycleService.CycleDay > 1 && NextCycle < cycle + 2) NextCycle = cycle + 2;
            Species = SpeciesAt(NextSpecies);
            Phase = FloweringPhase.Announced;
            Persist();
            Debug.Log(Log + "announced (" + why + "): " + Species + " flowers at the start of cycle " + NextCycle);
            _messenger.Post(_loc.T("Pandaborn.Flowering.Message.Announced", PlantName(Species), NextCycle.ToString(CultureInfo.InvariantCulture)));
            ApplyBuds();
            Changed?.Invoke();
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
            Changed?.Invoke();
        }

        /// <summary>Changes how often bamboo flowers (the per-save setting).</summary>
        public void SetSetting(string setting)
        {
            if (setting != "normal" && setting != "rare" && setting != "off") return;
            if (setting == Setting) return;
            Setting = setting;
            if (Phase == FloweringPhase.Idle && setting != "off") Reschedule(_gameCycleService.Cycle);
            Persist();
            Debug.Log(Log + "setting " + setting + "; next cycle " + NextCycle);
            CatchUp("setting changed");
            Changed?.Invoke();
        }

        // ------------------------------------------------------------------ the Flowering

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
            SeedCut = 0;
            int twins = 0, killed = 0, failed = 0;
            foreach (var plant in _plants.Where(p => p && p.Species == Species).ToList())
            {
                plant.ShowBuds(false);
                if (plant.IsDead || plant.IsHarvestedPile) continue;
                if (plant.IsGrown && TryTurnIntoTwin(plant, ref failed)) { twins++; continue; }
                plant.Living?.Die();
                killed++;
            }
            TwinsMade += twins;
            YoungKilled += killed;
            Reschedule(_gameCycleService.Cycle);
            Persist();
            ApplyHolds();
            _seedBorne = _inFlower.Where(t => t && t.Species == Species).Sum(t => t.SeedLeft);
            Persist();
            Debug.Log(Log + "flowered (" + why + "): " + Species + "; " + twins + " in flower bearing " + _seedBorne + " seed, " + killed
                      + " young plants died" + (failed > 0 ? ", " + failed + " could not be replaced and died" : "") + "; next " + NextCycle);
            _messenger.Post(string.Format(CultureInfo.InvariantCulture, _loc.T("Pandaborn.Flowering.Message.Flowered"), PlantName(Species),
                                          twins, _seedBorne, Days(Spec.SeedDays)));
            Changed?.Invoke();
        }

        private bool TryTurnIntoTwin(FloweringPlant plant, ref int failed)
        {
            string twin = plant.Spec?.InFlowerTemplate;
            if (string.IsNullOrEmpty(twin) || !_templateNameMapper.TryGetTemplate(twin, out _)) return false;
            var coordinates = plant.BlockObject.Coordinates;
            // the game clears a planting mark under any block of another template (PlantingCoordinatesUnsetter): keep the
            // farm's or forester's mark so the tile is replanted on its own once the twin is gone
            string mark = _plantingService.GetResourceAt(coordinates);
            _entityService.Delete(plant);
            var made = _naturalResourceFactory.SpawnIgnoringConstraints(twin, coordinates);
            if (mark != null && _plantingService.GetResourceAt(coordinates) == null) _plantingService.SetPlantingCoordinates(coordinates, mark);
            if (made == null) { failed++; return true; }   // the original is gone either way: counted as died
            made.GetComponent<Growable>()?.IncreaseGrowthProgress(1f);
            return true;
        }

        private void Advance()
        {
            if (Phase == FloweringPhase.Flowering)
            {
                // the flowered plants die over the last day of the seed time, a few each hour
                float end = FloweringDay + Spec.SeedDays;
                foreach (var twin in _inFlower.Where(t => t && t.Species == Species && !t.IsDead).ToList())
                {
                    float dieAt = end - 1f + Hash01(twin.BlockObject.Coordinates);
                    if (Now >= dieAt || Now >= end)
                    {
                        _seedLost += twin.SeedLeft;
                        twin.Living?.Die();
                        Persist();
                    }
                }
                if (Now >= end)
                {
                    Phase = FloweringPhase.Resting;
                    Persist();
                    int harvested = Math.Max(0, _seedBorne - _seedLost);
                    Debug.Log(Log + "seed time over: " + harvested + " of " + _seedBorne + " seed harvested, " + _seedLost + " lost");
                    _messenger.Post(_loc.T("Pandaborn.Flowering.Message.SeedOver", PlantName(Species), harvested.ToString(CultureInfo.InvariantCulture),
                                           Days(RestDaysLeft)));
                    Changed?.Invoke();
                }
            }
            if (Phase == FloweringPhase.Resting && Now >= FloweringDay + Spec.DormantDays)
            {
                string species = Species;
                Phase = FloweringPhase.Idle;
                Species = null;
                Persist();
                foreach (var plant in _plants.Where(p => p && p.Species == species)) GrowthHold.Release(plant.Growable);
                HeldNow = 0;
                Debug.Log(Log + species + " rests no more");
                _messenger.Post(_loc.T("Pandaborn.Flowering.Message.Regrows", PlantName(species)));
                CatchUp("rest over");
                Changed?.Invoke();
            }
        }

        private void ApplyHolds()
        {
            if (!Resting) return;
            int held = 0;
            foreach (var plant in _plants)
                if (plant && plant.Species == Species && !plant.IsDead && GrowthHold.Hold(plant.Growable)) held++;
            HeldNow = held;
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
                    var label = spec.GetSpec<Timberborn.EntitySystem.LabeledEntitySpec>();
                    if (label != null) return _loc.T(label.DisplayNameLocKey);
                }
            }
            catch (Exception) { }
            return template;
        }

        public bool IsTimberSpecies(string template) => template != null && _templateNameMapper.TryGetTemplate(template, out var spec)
                                                          && spec.GetSpec<Timberborn.Forestry.TreeComponentSpec>() != null;

        internal static string Days(float days) => Mathf.CeilToInt(Mathf.Max(0f, days)).ToString(CultureInfo.InvariantCulture);

        private static float Hash01(Vector3Int c)
        {
            unchecked
            {
                int h = c.x * 73856093 ^ c.y * 19349663 ^ c.z * 83492791;
                return ((h & 0x7fffffff) % 1000) / 1000f;
            }
        }

        // ------------------------------------------------------------------ state

        private void ReadState()
        {
            Setting = NormalizeSetting(Spec.DefaultSetting);
            Phase = FloweringPhase.Idle;
            if (!_store.TryGet(StoreFeature, out int version, out string payload) || version != StoreVersion) return;
            var v = Payload.Parse(payload);
            Setting = NormalizeSetting(Get(v, "setting") ?? Setting);
            Phase = Enum.TryParse(Get(v, "phase"), out FloweringPhase p) ? p : FloweringPhase.Idle;
            NextCycle = Int(v, "next", -1);
            NextSpecies = Math.Max(0, Int(v, "nextSpecies", 0));
            Species = Get(v, "species");
            if (string.IsNullOrEmpty(Species)) Species = null;
            FloweringDay = float.TryParse(Get(v, "day"), NumberStyles.Float, CultureInfo.InvariantCulture, out float d) ? d : -1f;
            LastCycle = Int(v, "last", -1);
            _seedBorne = Math.Max(0, Int(v, "borne", 0));
            _seedLost = Math.Max(0, Int(v, "lost", 0));
            if (Phase != FloweringPhase.Idle && (Species == null || !Spec.Species.Contains(Species))) { Phase = FloweringPhase.Idle; Species = null; }
            if ((Phase == FloweringPhase.Flowering || Phase == FloweringPhase.Resting) && FloweringDay < 0f) { Phase = FloweringPhase.Idle; Species = null; }
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
                new KeyValuePair<string, string>("lost", _seedLost.ToString(CultureInfo.InvariantCulture))
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

        /// <summary>Test hook: the announced (or next) species flowers now, whatever the day.</summary>
        public void DevFlowerNow()
        {
            if (!Active) return;
            if (Phase == FloweringPhase.Idle) DevAnnounce();
            if (Phase == FloweringPhase.Announced) Flower("dev");
        }
    }
}
