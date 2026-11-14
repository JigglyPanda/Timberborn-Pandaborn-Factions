using System;
using System.Collections.Generic;
using System.Reflection;
using Pandaborn.Core;
using Pandaborn.Specs;
using Timberborn.BaseComponentSystem;
using Timberborn.Beavers;
using Timberborn.BehaviorSystem;
using Timberborn.BlueprintSystem;
using Timberborn.Characters;
using Timberborn.EntitySystem;
using Timberborn.LifeSystem;
using Timberborn.SingletonSystem;
using Timberborn.TemplateInstantiation;
using Timberborn.TemplateSystem;
using UnityEngine;

namespace Pandaborn.Ringtails
{
    /// <summary>
    /// The Ringtails' feature switch, compatibility check, factory and save registration (prototype: proto/ringtails,
    /// results: docs/tech/two-peoples.md section 17).
    ///
    /// A Ringtails game is one whose faction adult template carries <see cref="PandabornRingtailsSpec"/>; no faction id is
    /// hard-coded. At load, before any Ringtail exists, the two private members the feature needs are checked once:
    ///  * TemplateNameMapper._templates (save/load of the hidden templates). Missing: Ringtails are off; saved Ringtails load
    ///    as Inkpaws through the BackwardCompatibleTemplateNames alias on the Inkpaw templates; no new Ringtails.
    ///  * BehaviorManager._rootBehaviors (the day rest). Missing: rest is off; no new Ringtails are created, existing ones
    ///    keep working (vanilla critical sleep keeps them alive).
    /// Either way one notice is posted and nothing throws.
    /// </summary>
    public class RingtailService : ILoadableSingleton, IPostLoadableSingleton
    {
        private const string LogPrefix = "[Pandaborn.Ringtails] ";

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
        private readonly Messenger _messenger;

        private Blueprint _adult;
        private Blueprint _child;
        private string _notice;

        public RingtailService(TemplateService templateService, ISpecService specService, TemplateNameMapper templateNameMapper,
                               TemplateInstantiator templateInstantiator, EntityService entityService, LifeService lifeService,
                               Messenger messenger)
        {
            _templateService = templateService;
            _specService = specService;
            _templateNameMapper = templateNameMapper;
            _templateInstantiator = templateInstantiator;
            _entityService = entityService;
            _lifeService = lifeService;
            _messenger = messenger;
        }

        /// <summary>The faction carries Ringtails at all.</summary>
        public bool IsRingtailsGame { get; private set; }

        /// <summary>Saved Ringtails load as Ringtails (registration worked).</summary>
        public bool SaveSupport { get; private set; }

        /// <summary>The day rest can be installed.</summary>
        public static bool RestSupport { get; private set; }

        /// <summary>New Ringtails may be created (both checks passed).</summary>
        public bool Enabled => SaveSupport && RestSupport;

        public void Load()
        {
            PandabornRingtailsSpec spec = null;
            try { spec = _templateService.GetSingle<AdultSpec>().GetSpec<PandabornRingtailsSpec>(); }
            catch (Exception) { }
            IsRingtailsGame = spec != null;
            if (!IsRingtailsGame) return;
            try
            {
                _adult = _specService.GetBlueprint(spec.AdultBlueprint);
                _child = _specService.GetBlueprint(spec.ChildBlueprint);
                RestSupport = RootBehaviorsField != null && RootBehaviorsField.FieldType == typeof(List<RootBehavior>);
                SaveSupport = RegisterTemplates();
                if (Enabled)
                {
                    _templateInstantiator.CacheInstance(_adult);
                    _templateInstantiator.CacheInstance(_child);
                    Debug.Log(LogPrefix + "on");
                }
                else
                {
                    _notice = !SaveSupport ? "Ringtails: this game version changed how saves find characters. Ringtails are paused and load as Inkpaws until the mod is updated."
                                           : "Ringtails: this game version changed character behaviour. No new Ringtails until the mod is updated.";
                    Debug.LogWarning(LogPrefix + "off: save support " + SaveSupport + ", rest support " + RestSupport);
                }
            }
            catch (Exception e)
            {
                SaveSupport = false;
                _notice = "Ringtails are paused until the mod is updated.";
                Debug.LogWarning(LogPrefix + "off: " + e.GetType().Name + ": " + e.Message);
            }
        }

        public void PostLoad()
        {
            if (_notice != null) _messenger.Post(_notice, warning: true);
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

        public Character CreateAdult(Vector3 position, float adulthoodProgress)
        {
            if (!Enabled) return null;
            float lifeProgress = _lifeService.AdulthoodProgressToLifeProgress(adulthoodProgress);
            return Create(_adult, new CharacterInit(_lifeService.CalculateDayOfBirth(lifeProgress), lifeProgress, null, position, Quaternion.identity));
        }

        /// <summary>A newborn kit (ChildInit is internal, so kits start at growth 0), e.g. for a loft nursery.</summary>
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
