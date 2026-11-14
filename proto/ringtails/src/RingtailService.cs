using System;
using System.Collections.Generic;
using System.Reflection;
using Timberborn.BlueprintSystem;
using Timberborn.Characters;
using Timberborn.EntitySystem;
using Timberborn.GameFactionSystem;
using Timberborn.LifeSystem;
using Timberborn.SingletonSystem;
using Timberborn.TemplateInstantiation;
using Timberborn.TemplateSystem;
using UnityEngine;

namespace Pandaborn.Ringtails
{
    /// <summary>
    /// The Ringtail feature switch, factory and save/load registration. Active only in an Inkpaws game.
    ///
    /// The Ringtail templates are deliberately in no template collection, so TemplateService.GetSingle&lt;AdultSpec&gt;()
    /// (BeaverFactory) still finds exactly one adult. Two consequences handled here:
    ///  * creating Ringtails needs our own factory (public API only, mirrors BeaverFactory.CreateBeaver);
    ///  * loading a save needs the Ringtail templates in TemplateNameMapper, which only lists collection templates.
    ///    That is the one private-field write (TemplateNameMapper._templates). If it fails, the feature switches itself
    ///    off: no new Ringtails are created, and the saved ones load as Inkpaws through the BackwardCompatibleTemplateNames
    ///    alias that this mod merges into the Inkpaw templates (nothing is lost, nothing crashes).
    /// </summary>
    public class RingtailService : ILoadableSingleton
    {
        public const string FactionId = "Inkpaws";
        public const string WorkerType = "PandabornRingtail";
        public const string AdultTemplateName = "RingtailAdult.Inkpaws";
        public const string ChildTemplateName = "RingtailChild.Inkpaws";
        private const string AdultBlueprintPath = "Characters/Pandaborn/RingtailAdult.Inkpaws.blueprint";
        private const string ChildBlueprintPath = "Characters/Pandaborn/RingtailChild.Inkpaws.blueprint";
        private const string LogPrefix = "[Pandaborn.Ringtails] ";

        private readonly FactionService _factionService;
        private readonly ISpecService _specService;
        private readonly TemplateNameMapper _templateNameMapper;
        private readonly TemplateInstantiator _templateInstantiator;
        private readonly EntityService _entityService;
        private readonly LifeService _lifeService;

        private Blueprint _adult;
        private Blueprint _child;

        /// <summary>True in an Inkpaws game when every Ringtail dependency checked out.</summary>
        public bool Enabled { get; private set; }

        /// <summary>Why the feature is off (null when on, or when this simply is not an Inkpaws game).</summary>
        public string DisabledReason { get; private set; }

        public bool IsInkpawsGame { get; private set; }

        /// <summary>Dev switch (harness request "ringtails.disableTemplateRegistration"): simulate a game update that broke the private field.</summary>
        public static bool SimulateRegistrationFailure;

        public RingtailService(FactionService factionService, ISpecService specService, TemplateNameMapper templateNameMapper,
                               TemplateInstantiator templateInstantiator, EntityService entityService, LifeService lifeService)
        {
            _factionService = factionService;
            _specService = specService;
            _templateNameMapper = templateNameMapper;
            _templateInstantiator = templateInstantiator;
            _entityService = entityService;
            _lifeService = lifeService;
        }

        public void Load()
        {
            IsInkpawsGame = _factionService.Current != null && _factionService.Current.Id == FactionId;
            if (!IsInkpawsGame) return;
            try
            {
                _adult = _specService.GetBlueprint(AdultBlueprintPath);
                _child = _specService.GetBlueprint(ChildBlueprintPath);
                if (!_adult.HasSpec<PandabornRingtailSpec>() || !_child.HasSpec<PandabornRingtailSpec>())
                {
                    Disable("the Ringtail templates lack PandabornRingtailSpec");
                    return;
                }
                if (!RegisterTemplates(out string reason))
                {
                    Disable(reason);
                    return;
                }
                _templateInstantiator.CacheInstance(_adult);
                _templateInstantiator.CacheInstance(_child);
                Enabled = true;
                Debug.Log(LogPrefix + "enabled: templates " + AdultTemplateName + ", " + ChildTemplateName + " registered for save/load");
            }
            catch (Exception e)
            {
                Disable("unexpected " + e.GetType().Name + ": " + e.Message);
            }
        }

        private void Disable(string reason)
        {
            Enabled = false;
            DisabledReason = reason;
            Debug.LogError(LogPrefix + "Ringtail features disabled: " + reason
                           + ". Saved Ringtails load as Inkpaws; no new Ringtails are created.");
        }

        /// <summary>The only private-field dependency of save/load: add the hidden templates to TemplateNameMapper._templates.</summary>
        private bool RegisterTemplates(out string reason)
        {
            reason = null;
            if (SimulateRegistrationFailure) { reason = "simulated registration failure (dev switch)"; return false; }
            var field = typeof(TemplateNameMapper).GetField("_templates", BindingFlags.Instance | BindingFlags.NonPublic);
            if (field == null || !(field.GetValue(_templateNameMapper) is Dictionary<string, TemplateSpec> templates))
            {
                reason = "TemplateNameMapper._templates (Dictionary<string, TemplateSpec>) not found; the game changed";
                return false;
            }
            foreach (var blueprint in new[] { _adult, _child })
            {
                var spec = blueprint.GetSpec<TemplateSpec>();
                // overwrite: the Inkpaw templates carry the Ringtail names as a backward-compatible alias (the safe fallback)
                templates[spec.TemplateName] = spec;
            }
            if (!_templateNameMapper.TryGetTemplate(AdultTemplateName, out var check) || check.Blueprint != _adult)
            {
                reason = "TemplateNameMapper did not return the registered Ringtail template";
                return false;
            }
            return true;
        }

        /// <summary>Creates a Ringtail adult at a position (on the nav mesh), like BeaverFactory.CreateAdult. Null when disabled.</summary>
        public Character CreateAdult(Vector3 position, float adulthoodProgress)
        {
            if (!Enabled) return null;
            float lifeProgress = _lifeService.AdulthoodProgressToLifeProgress(adulthoodProgress);
            var builder = new EntitySetup.Builder(_adult);
            builder.AddInitComponent(new CharacterInit(_lifeService.CalculateDayOfBirth(lifeProgress), lifeProgress, null, position, Quaternion.identity));
            return _entityService.Instantiate(builder).GetComponent<Character>();
        }

        /// <summary>Creates a Ringtail adult from a grown-up Ringtail kit (mirrors BeaverFactory.CreateAdultFromChild).</summary>
        public Character CreateAdultFromChild(Character child, float lifeProgress)
        {
            if (!Enabled) return null;
            var builder = new EntitySetup.Builder(_adult);
            builder.AddInitComponent(new CharacterInit(_lifeService.CalculateDayOfBirth(lifeProgress), lifeProgress, child, child.Transform.position, Quaternion.identity));
            return _entityService.Instantiate(builder).GetComponent<Character>();
        }

        /// <summary>Creates a newborn Ringtail kit (ChildInit is internal, so kits always start at growth 0). Null when disabled.</summary>
        public Character CreateChild(Vector3 position)
        {
            if (!Enabled) return null;
            float lifeProgress = _lifeService.ChildhoodProgressToLifeProgress(0f);
            var builder = new EntitySetup.Builder(_child);
            builder.AddInitComponent(new CharacterInit(_lifeService.CalculateDayOfBirth(lifeProgress), lifeProgress, null, position, Quaternion.identity));
            return _entityService.Instantiate(builder).GetComponent<Character>();
        }

        public static bool IsRingtail(Timberborn.BaseComponentSystem.BaseComponent character)
        {
            return character != null && character.GetComponent<PandabornRingtailSpec>() != null;
        }
    }
}
