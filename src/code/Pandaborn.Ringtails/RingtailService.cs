using System;
using System.Collections.Generic;
using System.Linq;
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
using Timberborn.LifeSystem;
using Timberborn.Localization;
using Timberborn.ScienceSystem;
using Timberborn.SingletonSystem;
using Timberborn.TemplateInstantiation;
using Timberborn.TemplateSystem;
using UnityEngine;

namespace Pandaborn.Ringtails
{
    /// <summary>
    /// The Ringtails' switch, load-time compatibility check, factory, save registration and arrival
    /// (docs/tech/two-peoples.md section 17; DESIGN.md Pillar 4).
    ///
    /// A Ringtails game is one whose faction adult template carries <see cref="PandabornRingtailsSpec"/>. At load, before any
    /// Ringtail exists, the two private members the feature needs are checked once:
    ///  * TemplateNameMapper._templates (saves): missing means the feature is degraded to "off": saved Ringtails load as Inkpaws
    ///    through the BackwardCompatibleTemplateNames alias, night posts stay ordinary Inkpaw workplaces, no Ringtails arrive.
    ///  * BehaviorManager._rootBehaviors (the day rest): same.
    /// Either way Core posts one "falls back" notice (FeatureRegistry.ReportDegraded) and nothing throws.
    /// Saved state (PandabornStore "Ringtails" v1): arrived=0|1.
    /// </summary>
    public class RingtailService : ILoadableSingleton, IPostLoadableSingleton
    {
        public const string FeatureId = "Ringtails";
        private const string LogPrefix = "[Pandaborn.Ringtails] ";
        private const int StoreVersion = 1;

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

        private Blueprint _adult;
        private Blueprint _child;

        public RingtailService(TemplateService templateService, ISpecService specService, TemplateNameMapper templateNameMapper,
                               TemplateInstantiator templateInstantiator, EntityService entityService, LifeService lifeService,
                               BuildingUnlockingService buildingUnlockingService, PandabornStore store, Messenger messenger, ILoc loc)
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
        }

        /// <summary>The service of the running game (tests, the dev probe).</summary>
        public static RingtailService Current { get; private set; }

        public PandabornRingtailsSpec Spec { get; private set; }

        /// <summary>The faction carries Ringtails at all.</summary>
        public bool IsRingtailsGame => Spec != null;

        /// <summary>Everything checked out: Ringtails work, rest, save, arrive and are born.</summary>
        public bool Enabled { get; private set; }

        public string DisabledReason { get; private set; }

        public string WorkerType => Spec?.WorkerType ?? "PandabornRingtail";

        /// <summary>The first Moon Loft has brought the Ringtails in this save.</summary>
        public bool Arrived { get; private set; }

        public event Action ArrivedChanged;

        public void Load()
        {
            Current = this;
            try { Spec = _templateService.GetSingle<AdultSpec>().GetSpec<PandabornRingtailsSpec>(); }
            catch (Exception) { Spec = null; }
            if (!IsRingtailsGame) return;
            if (_store.TryGet(FeatureId, out int version, out string payload) && version == StoreVersion)
                Arrived = Payload.Parse(payload).TryGetValue("arrived", out var a) && a == "1";
            try
            {
                _adult = _specService.GetBlueprint(Spec.AdultBlueprint);
                _child = _specService.GetBlueprint(Spec.ChildBlueprint);
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
            if (Enabled && Arrived) UnlockNightPosts();
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

        // ------------------------------------------------------------------ arrival

        /// <summary>Called by a Moon Loft when it is finished. The first one in a save brings the family.</summary>
        public void OnMoonLoftFinished(MoonLoft loft)
        {
            if (!Enabled || Arrived) return;
            Arrived = true;
            _store.Set(FeatureId, StoreVersion, Payload.Write(new[] { new KeyValuePair<string, string>("arrived", "1") }));
            var names = new List<string>();
            for (int i = 0; i < Spec.ArrivalAdults; i++)
            {
                var c = CreateAdult(loft.Doorstep, 0.15f + 0.2f * i);
                if (c) { loft.TakeIn(c); names.Add(c.FirstName); }
            }
            for (int i = 0; i < Spec.ArrivalKits; i++)
            {
                var c = CreateChild(loft.Doorstep);
                if (c) { loft.TakeIn(c); names.Add(c.FirstName); }
            }
            UnlockNightPosts();
            _messenger.Post(_loc.T("Pandaborn.Ringtails.Arrived", string.Join(", ", names)));
            ArrivedChanged?.Invoke();
        }

        private void UnlockNightPosts()
        {
            foreach (var post in _templateService.GetAll<PandabornNightPostSpec>())
            {
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
