using System;
using System.Collections.Generic;
using System.Globalization;
using System.Reflection;
using Pandaborn.Core;
using Pandaborn.Specs;
using Timberborn.BaseComponentSystem;
using Timberborn.Beavers;
using Timberborn.BehaviorSystem;
using Timberborn.BlueprintSystem;
using Timberborn.Buildings;
using Timberborn.Characters;
using Timberborn.EntitySystem;
using Timberborn.GameFactionSystem;
using Timberborn.LifeSystem;
using Timberborn.Localization;
using Timberborn.ScienceSystem;
using Timberborn.SingletonSystem;
using Timberborn.TemplateInstantiation;
using Timberborn.TemplateSystem;
using Timberborn.TickSystem;
using UnityEngine;

namespace Pandaborn.Ringtails
{
    /// <summary>
    /// The Ringtails' switch, load-time compatibility check, factory, save registration, arrival and return
    /// (docs/tech/two-peoples.md sections 17 to 20; DESIGN.md Pillar 4).
    ///
    /// A Ringtails game is one whose faction adult template carries <see cref="PandabornRingtailsSpec"/>. At load, before any
    /// Ringtail exists, the two private members the feature needs are checked once:
    ///  * TemplateNameMapper._templates (saves): missing means the feature is degraded to "off": saved Ringtails load as Inkpaws
    ///    through the BackwardCompatibleTemplateNames alias, night posts stay ordinary Inkpaw workplaces, no Ringtails arrive.
    ///  * BehaviorManager._rootBehaviors (the day rest): same.
    /// Either way Core posts one "falls back" notice (FeatureRegistry.ReportDegraded) and nothing throws.
    ///
    /// Load order: the game loads singletons in the order it constructed them, and it constructs a singleton's
    /// constructor arguments first. So PandabornStore has loaded before this Load reads the arrival flag, the game's
    /// TemplateNameMapper has built its table before this adds to it, and every Ringtail singleton that takes this
    /// service in its constructor loads after it. World entities are loaded after every singleton's Load.
    ///
    /// Colonists are never created inside a building's finished-state step (on a load that step runs while the world is
    /// still being put together): a finished Moon Loft only queues the arrival, and the next tick carries it out.
    ///
    /// Saved state (PandabornStore "Ringtails" v1): arrived=0|1, and waits=&lt;district id&gt;:&lt;empty dawns&gt;,... for
    /// districts that have a Moon Loft and no living Ringtail (an older build ignores the second key).
    /// </summary>
    public class RingtailService : ILoadableSingleton, IPostLoadableSingleton, ITickableSingleton
    {
        public const string FeatureId = "Ringtails";
        private const string LogPrefix = "[Pandaborn.Ringtails] ";
        private const int StoreVersion = 1;
        private const int MaxArrivalFailures = 3;

        internal static readonly FieldInfo TemplatesField =
            typeof(TemplateNameMapper).GetField("_templates", BindingFlags.Instance | BindingFlags.NonPublic);
        internal static readonly FieldInfo RootBehaviorsField =
            typeof(BehaviorManager).GetField("_rootBehaviors", BindingFlags.Instance | BindingFlags.NonPublic);

        private readonly TemplateService _templateService;
        private readonly ISpecService _specService;
        private readonly TemplateNameMapper _templateNameMapper;
        private readonly TemplateInstantiator _templateInstantiator;
        private readonly EntityService _entityService;
        private readonly LifeService _lifeService;
        private readonly BuildingUnlockingService _buildingUnlockingService;
        private readonly PandabornStore _store;
        private readonly Messenger _messenger;
        private readonly ILoc _loc;
        private readonly FactionService _factionService;

        private readonly List<MoonLoft> _pendingLofts = new List<MoonLoft>();
        private readonly Dictionary<string, int> _emptyDawns = new Dictionary<string, int>(StringComparer.Ordinal);
        private Blueprint _adult;
        private Blueprint _child;
        private int _arrivalFailures;

        public RingtailService(TemplateService templateService, ISpecService specService, TemplateNameMapper templateNameMapper,
                               TemplateInstantiator templateInstantiator, EntityService entityService, LifeService lifeService,
                               BuildingUnlockingService buildingUnlockingService, PandabornStore store, Messenger messenger, ILoc loc,
                               FactionService factionService)
        {
            _templateService = templateService;
            _specService = specService;
            _templateNameMapper = templateNameMapper;
            _templateInstantiator = templateInstantiator;
            _entityService = entityService;
            _lifeService = lifeService;
            _buildingUnlockingService = buildingUnlockingService;
            _store = store;
            _messenger = messenger;
            _loc = loc;
            _factionService = factionService;
        }

        /// <summary>The service of the running game (tests, the dev probe).</summary>
        public static RingtailService Current { get; private set; }

        public PandabornRingtailsSpec Spec { get; private set; }

        /// <summary>The Ringtail adult's own spec (rest window limits), once the templates are read.</summary>
        public PandabornRingtailSpec AdultSpec { get; private set; }

        /// <summary>The faction carries Ringtails at all.</summary>
        public bool IsRingtailsGame => Spec != null;

        /// <summary>Everything checked out: Ringtails work, rest, save, arrive and are born.</summary>
        public bool Enabled { get; private set; }

        public string DisabledReason { get; private set; }

        public string WorkerType => Spec?.WorkerType ?? "PandabornRingtail";

        /// <summary>The first Moon Loft has brought the Ringtails in this save.</summary>
        public bool Arrived { get; private set; }

        /// <summary>Families that came back to a district that had lost its Ringtails, this session (tests).</summary>
        public static int Returns { get; private set; }

        public event Action ArrivedChanged;

        /// <summary>A family has moved into this loft (sounds, tests).</summary>
        public event Action<MoonLoft> FamilyArrived;

        public void Load()
        {
            Current = this;
            Returns = 0;
            RingtailRestRootBehavior.NewGame();

            try { Spec = _templateService.GetSingle<AdultSpec>().GetSpec<PandabornRingtailsSpec>(); }
            catch (Exception) { Spec = null; }
            if (!IsRingtailsGame)
            {
                // shipped but not switched on by data: say so in the feature report, only in games of our faction
                try
                {
                    if (_factionService.Current?.Id == FeatureNotices.FactionId)
                        FeatureRegistry.ReportNoData(FeatureId, "the faction's adult template has no PandabornRingtailsSpec");
                }
                catch (Exception) { }
                return;
            }
            ReadStore();
            try
            {
                _adult = _specService.GetBlueprint(Spec.AdultBlueprint);
                _child = _specService.GetBlueprint(Spec.ChildBlueprint);
                AdultSpec = _adult.GetSpec<PandabornRingtailSpec>();
                if (FeatureRegistry.DevFlag("simulate-missing-member", FeatureId))
                    Degrade("simulated: TemplateNameMapper._templates missing");
                else if (RootBehaviorsField == null || RootBehaviorsField.FieldType != typeof(List<RootBehavior>))
                    Degrade("BehaviorManager._rootBehaviors changed");
                else if (!RegisterTemplates())
                    Degrade("TemplateNameMapper._templates changed");
                else
                {
                    _templateInstantiator.CacheInstance(_adult);
                    _templateInstantiator.CacheInstance(_child);
                    Enabled = true;
                    Debug.Log(LogPrefix + "on" + (Arrived ? " (arrived)" : ""));
                }
            }
            catch (Exception e)
            {
                Degrade(e.GetType().Name + ": " + e.Message);
            }
        }

        public void PostLoad()
        {
            try { if (Enabled && Arrived) UnlockNightPosts(); }
            catch (Exception e) { Debug.LogError(LogPrefix + "unlocking the night posts failed: " + e); }
        }

        /// <summary>Carries out a queued arrival. Nothing to do on almost every tick.</summary>
        public void Tick()
        {
            if (_pendingLofts.Count == 0) return;
            var lofts = _pendingLofts.ToArray();
            _pendingLofts.Clear();
            if (!Enabled || Arrived) return;
            foreach (var loft in lofts)
            {
                if (!loft || !loft.IsFinished) continue;   // demolished in the same tick
                Arrive(loft);
                if (Arrived) return;
            }
        }

        private void Degrade(string reason)
        {
            Enabled = false;
            DisabledReason = reason;
            FeatureRegistry.ReportDegraded(FeatureId, reason);
            Debug.LogWarning(LogPrefix + "falls back to the plain game: " + reason);
        }

        private bool RegisterTemplates()
        {
            if (TemplatesField == null || !(TemplatesField.GetValue(_templateNameMapper) is Dictionary<string, TemplateSpec> templates))
                return false;
            foreach (var blueprint in new[] { _adult, _child })
            {
                var spec = blueprint.GetSpec<TemplateSpec>();
                templates[spec.TemplateName] = spec;   // overwrites the Inkpaw alias for the same name
            }
            return _templateNameMapper.TryGetTemplate(_adult.GetSpec<TemplateSpec>().TemplateName, out var check) && check.Blueprint == _adult;
        }

        // ------------------------------------------------------------------ saved state

        private void ReadStore()
        {
            try
            {
                if (!_store.TryGet(FeatureId, out int version, out string payload) || version != StoreVersion) return;
                var values = Payload.Parse(payload);
                Arrived = values.TryGetValue("arrived", out var a) && a == "1";
                if (!values.TryGetValue("waits", out var waits) || string.IsNullOrEmpty(waits)) return;
                foreach (var part in waits.Split(','))
                {
                    int colon = part.LastIndexOf(':');
                    if (colon > 0 && int.TryParse(part.Substring(colon + 1), NumberStyles.Integer, CultureInfo.InvariantCulture, out int n) && n > 0)
                        _emptyDawns[part.Substring(0, colon)] = n;
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning(LogPrefix + "saved state unreadable, starting fresh: " + e.Message);
            }
        }

        private void Persist()
        {
            try
            {
                var waits = new List<string>();
                foreach (var w in _emptyDawns) if (w.Value > 0) waits.Add(w.Key + ":" + w.Value.ToString(CultureInfo.InvariantCulture));
                waits.Sort(StringComparer.Ordinal);
                _store.Set(FeatureId, StoreVersion, Payload.Write(new[]
                {
                    new KeyValuePair<string, string>("arrived", Arrived ? "1" : "0"),
                    new KeyValuePair<string, string>("waits", string.Join(",", waits))
                }));
            }
            catch (Exception e) { Debug.LogError(LogPrefix + "saving state failed: " + e); }
        }

        // ------------------------------------------------------------------ arrival and return

        /// <summary>Called by a Moon Loft when it is finished (also when a finished one is loaded). The first one in a save
        /// brings the family, on the next tick.</summary>
        public void OnMoonLoftFinished(MoonLoft loft)
        {
            if (!Enabled || Arrived || loft == null) return;
            if (!_pendingLofts.Contains(loft)) _pendingLofts.Add(loft);
        }

        private void Arrive(MoonLoft loft)
        {
            if (!BringFamily(loft, "Pandaborn.Ringtails.Arrived"))
            {
                // nothing was created: stay "not arrived" so the next finished loft (or the next load) tries again; after a
                // few failures the feature says it is reduced instead of failing silently for ever
                if (++_arrivalFailures >= MaxArrivalFailures && Enabled)
                    FeatureRegistry.ReportDegraded(FeatureId, "the Ringtail family could not be created");
                return;
            }
            Arrived = true;
            Persist();
            try { UnlockNightPosts(); }
            catch (Exception e) { Debug.LogError(LogPrefix + "unlocking the night posts failed: " + e); }
            try { ArrivedChanged?.Invoke(); }
            catch (Exception e) { Debug.LogError(LogPrefix + "an arrival listener failed: " + e); }
        }

        /// <summary>
        /// The count of empty dawns for a district that has a finished Moon Loft (<see cref="KitValve.NextEmptyDawns"/>):
        /// called once per district at each dawn by the nursery. When the wait is over a new family moves into
        /// <paramref name="loft"/>. True when a family came.
        /// </summary>
        public bool DawnWithoutRingtails(string districtId, MoonLoft loft, int livingRingtails, bool anyoneStarving)
        {
            if (!Enabled || !Arrived || string.IsNullOrEmpty(districtId)) return false;
            _emptyDawns.TryGetValue(districtId, out int before);
            int wait = Spec != null ? Spec.ReturnAfterDays : 3;
            bool hasLoft = loft != null && loft.IsFinished;
            int after = KitValve.NextEmptyDawns(before, hasLoft, livingRingtails, anyoneStarving, wait, out bool invite);
            bool came = false;
            if (invite)
            {
                came = BringFamily(loft, "Pandaborn.Ringtails.Returned");
                if (came)
                {
                    Returns++;
                    Debug.Log(LogPrefix + "a new family answered the lantern (district " + districtId + ")");
                }
                else after = Math.Max(1, wait - 1);   // could not be created: try again at the next dawn
            }
            if (after != before)
            {
                if (after > 0) _emptyDawns[districtId] = after;
                else _emptyDawns.Remove(districtId);
                Persist();
            }
            return came;
        }

        /// <summary>Dawns a district with a loft has been without Ringtails (the loft's panel line), 0 when it has some.</summary>
        public int EmptyDawns(string districtId)
        {
            return districtId != null && _emptyDawns.TryGetValue(districtId, out int n) ? n : 0;
        }

        /// <summary>Forgets districts that no longer exist (called by the nursery with the districts it saw this dawn).</summary>
        public void KeepWaitsOnlyFor(HashSet<string> districtIds)
        {
            List<string> gone = null;
            foreach (var id in _emptyDawns.Keys) if (!districtIds.Contains(id)) (gone ??= new List<string>()).Add(id);
            if (gone == null) return;
            foreach (var id in gone) _emptyDawns.Remove(id);
            Persist();
        }

        /// <summary>Creates the family at the loft's door and moves it in. False when nobody could be created.</summary>
        private bool BringFamily(MoonLoft loft, string messageKey)
        {
            var names = new List<string>();
            try
            {
                int adults = Mathf.Clamp(Spec.ArrivalAdults, 0, 8), kits = Mathf.Clamp(Spec.ArrivalKits, 0, 8);
                for (int i = 0; i < adults; i++)
                {
                    var c = CreateAdult(loft.Doorstep, Mathf.Min(0.15f + 0.2f * i, 0.75f));
                    if (c) { loft.TakeIn(c); names.Add(c.FirstName); }
                }
                for (int i = 0; i < kits; i++)
                {
                    var c = CreateChild(loft.Doorstep);
                    if (c) { loft.TakeIn(c); names.Add(c.FirstName); }
                }
            }
            catch (Exception e)
            {
                Debug.LogError(LogPrefix + "creating the Ringtail family failed: " + e);
            }
            if (names.Count == 0) return false;
            try
            {
                // the notification's subject is the loft: clicking the entry in the log takes the camera to its door
                _messenger.Post(_loc.T(messageKey, string.Join(", ", names)), loft);
            }
            catch (Exception e) { Debug.LogWarning(LogPrefix + "arrival message failed: " + e.Message); }
            try { FamilyArrived?.Invoke(loft); }
            catch (Exception e) { Debug.LogWarning(LogPrefix + "an arrival listener failed: " + e.Message); }
            return true;
        }

        /// <summary>The night posts unlock for free when the family arrives, except those whose data says to keep their
        /// science cost (PandabornNightPostSpec.UnlockOnArrival = false: the Star Tower).</summary>
        private void UnlockNightPosts()
        {
            foreach (var post in _templateService.GetAll<PandabornNightPostSpec>())
            {
                if (!post.UnlockOnArrival) continue;
                var building = post.GetSpec<BuildingSpec>();
                if (building != null && !_buildingUnlockingService.Unlocked(building)) _buildingUnlockingService.UnlockIgnoringCost(building);
            }
        }

        // ------------------------------------------------------------------ factory

        public Character CreateAdult(Vector3 position, float adulthoodProgress)
        {
            if (!Enabled) return null;
            float lifeProgress = _lifeService.AdulthoodProgressToLifeProgress(adulthoodProgress);
            return Create(_adult, new CharacterInit(_lifeService.CalculateDayOfBirth(lifeProgress), lifeProgress, null, position, Quaternion.identity));
        }

        /// <summary>A newborn kit (ChildInit is internal, so kits start at growth 0).</summary>
        public Character CreateChild(Vector3 position)
        {
            if (!Enabled) return null;
            float lifeProgress = _lifeService.ChildhoodProgressToLifeProgress(0f);
            return Create(_child, new CharacterInit(_lifeService.CalculateDayOfBirth(lifeProgress), lifeProgress, null, position, Quaternion.identity));
        }

        public Character CreateAdultFromChild(Character child, float lifeProgress)
        {
            if (!Enabled) return null;
            return Create(_adult, new CharacterInit(_lifeService.CalculateDayOfBirth(lifeProgress), lifeProgress, child, child.Transform.position, Quaternion.identity));
        }

        private Character Create(Blueprint blueprint, CharacterInit init)
        {
            var builder = new EntitySetup.Builder(blueprint);
            builder.AddInitComponent(init);
            return _entityService.Instantiate(builder).GetComponent<Character>();
        }

        public static bool IsRingtail(BaseComponent character)
        {
            return character != null && character.GetComponent<PandabornRingtailSpec>() != null;
        }
    }
}
