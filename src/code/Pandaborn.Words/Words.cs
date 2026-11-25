using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using Bindito.Core;
using Pandaborn.Core;
using Timberborn.BlueprintSystem;
using Timberborn.GameSceneLoading;
using Timberborn.Localization;
using Timberborn.Persistence;
using Timberborn.SceneLoading;
using Timberborn.SingletonSystem;
using Timberborn.WorldPersistence;
using UnityEngine;

namespace Pandaborn.Words
{
    [Context("Game")]
    public class WordsConfigurator : Configurator
    {
        protected override void Configure()
        {
            Bind<WordsService>().AsSingleton();
            Bind<WordsEarlyHook>().AsSingleton();
            MultiBind<IBlueprintModifierProvider>().ToExisting<WordsEarlyHook>();
        }
    }

    [Context("MainMenu")]
    public class WordsMainMenuConfigurator : Configurator
    {
        protected override void Configure()
        {
            Bind<WordsMainMenuRestore>().AsSingleton();
        }
    }

    /// <summary>Safety net: if a game ended without WordsService.Unload (the game calls every singleton's Unload in a row
    /// with no guard, so another mod's exception skips ours), the vanilla texts go back when the main menu loads.</summary>
    public class WordsMainMenuRestore : ILoadableSingleton
    {
        private readonly ILoc _loc;

        public WordsMainMenuRestore(ILoc loc)
        {
            _loc = loc;
        }

        public void Load()
        {
            try { WordsService.RestoreLeftover(_loc, "on the main menu"); }
            catch (Exception e) { Debug.LogError("[Pandaborn.Words] restore on the main menu failed: " + e); }
        }
    }

    /// <summary>
    /// The earliest moment our code can act in a game scene: SpecService asks every blueprint-modifier provider for
    /// modifiers when it reads its first blueprint (the faction files, inside FactionSpecService.Load), before almost any
    /// other singleton has loaded and long before specs, panels and entities resolve their texts. This provider adds no
    /// modifier; on that first call it lets WordsService swap the texts, finding the game's faction the way
    /// FactionService.Load does (the save's FactionService singleton, else the new-game parameters). It cannot depend on
    /// FactionService itself (FactionService depends on SpecService, which depends on this provider).
    /// </summary>
    public class WordsEarlyHook : IBlueprintModifierProvider
    {
        private readonly WordsService _words;
        private bool _done;

        public WordsEarlyHook(WordsService words)
        {
            _words = words;
        }

        public string ModifierName => "Pandaborn words";

        public IEnumerable<string> GetModifiers(string blueprintPath)
        {
            if (!_done)
            {
                _done = true;
                try { _words.Apply(_words.FactionId(), "early"); }
                catch (Exception e) { Debug.LogError("[Pandaborn.Words] early swap failed; trying again at load: " + e); }
            }
            yield break;
        }

    }


    /// <summary>
    /// In a game of the table's faction (Inkpaws), replaces a reviewed list of vanilla enUS texts that call the colonists
    /// beavers (words.enUS.txt: key, replacement, the vanilla text it was reviewed against), and puts the vanilla texts back
    /// when the game unloads, so a Folktails game in the same session is untouched. A replacement is applied only if the
    /// game's current text still equals the reviewed vanilla text (a game update or another mod that changed the text wins).
    /// Other languages keep their texts unless words.&lt;language&gt;.txt exists.
    ///
    /// How: ILoc.Initialize(Dictionary) is public and clears the text cache; the dictionary it holds is a private field of
    /// the game's Loc class, read by reflection. Written fallback: if that field cannot be found (or the dev switch
    /// "simulate-missing-member: Words" is set), nothing is changed, the game shows vanilla words, and the feature report
    /// says so. Phrase objects cache their text forever, so keys used through Phrase.New must never be in the table
    /// (none are; tools/candidates.py lists them).
    /// </summary>
    public class WordsService : ILoadableSingleton, IUnloadableSingleton
    {
        private static readonly SingletonKey FactionServiceKey = new SingletonKey("FactionService");
        private static readonly PropertyKey<string> IdKey = new PropertyKey<string>("Id");
        private readonly ILoc _loc;
        private readonly ILocalizationService _localizationService;
        private readonly ISingletonLoader _singletonLoader;
        private readonly ISceneLoader _sceneLoader;
        private Dictionary<string, string> _original;
        private Dictionary<string, string> _applied;
        private FieldInfo _field;
        private bool _decided;

        // What is swapped in right now, whichever game did it. That game's Unload puts the vanilla texts back; if it never
        // ran, or another mod swapped its own table in and out around ours, the next game and the main menu do
        // (RestoreLeftover). ILoc lives for the whole session, so a swap left behind would show in every later game.
        private static Dictionary<string, string> _liveOriginal;
        private static Dictionary<string, string> _liveApplied;
        private static FieldInfo _liveField;

        // No FactionService here: SpecService depends on WordsEarlyHook, which depends on this class, and FactionService
        // depends on SpecService. The faction is read the way FactionService.Load reads it.
        public WordsService(ILoc loc, ILocalizationService localizationService, ISingletonLoader singletonLoader, ISceneLoader sceneLoader)
        {
            _loc = loc;
            _localizationService = localizationService;
            _singletonLoader = singletonLoader;
            _sceneLoader = sceneLoader;
        }

        public string FactionId()
        {
            if (_singletonLoader.TryGetSingleton(FactionServiceKey, out var loader) && loader.Has(IdKey)) return loader.Get(IdKey);
            return _sceneLoader.GetSceneParameters<GameSceneParameters>()?.NewGameConfiguration?.FactionId;
        }

        /// <summary>For tests: how the last game went ("early", "load", "not our faction", "degraded: ...", "restored").</summary>
        public static string State { get; private set; } = "idle";
        public static int AppliedCount { get; private set; }
        public static readonly List<string> Skipped = new List<string>();

        public void Load()
        {
            // the early hook normally decided already (swapped, or not our faction, or no table); this is its second try
            if (_decided) return;
            try { Apply(FactionId(), "load"); }
            catch (Exception e) { Degrade("swap failed: " + e.Message, e); }
        }

        public void Unload()
        {
            try { Restore(); }
            catch (Exception e) { Debug.LogError("[Pandaborn.Words] restoring vanilla texts failed: " + e); }
        }

        public void Apply(string factionId, string when)
        {
            if (_applied != null || _decided) return;
            RestoreLeftover(_loc, "before a new game");
            Skipped.Clear();
            AppliedCount = 0;
            // The table is per language and only enUS ships: in any other language nothing is swapped and the player
            // reads the game's own translation (which says beaver), never an English line in the middle of it. A
            // translated table is words.<language>.txt, reviewed against that language's vanilla texts.
            string language = SafeLanguage();
            var table = WordsTable.Load(FeatureRegistry.Owner, language);
            if (table == null)
            {
                State = "no table for " + language;
                _decided = true;
                // other languages have no table by design; a missing enUS table is a build without the module's data
                if (language == "enUS" && factionId == "Inkpaws") FeatureRegistry.ReportNoData("Words", "no Pandaborn/Words/words.enUS.txt in the mod");
                return;
            }
            if (factionId == null || !string.Equals(factionId, table.Faction, StringComparison.Ordinal)) { State = "not our faction"; _decided = true; return; }
            if (FeatureRegistry.DevFlag("simulate-missing-member", "Words")) { Degrade("simulated: Loc._localization missing", null); return; }
            _field = FindField(_loc);
            if (_field == null) { Degrade("Loc._localization missing", null); return; }
            var original = _field.GetValue(_loc) as Dictionary<string, string>;
            if (original == null) { Degrade("Loc._localization empty", null); return; }
            var copy = new Dictionary<string, string>(original, original.Comparer);
            foreach (var e in table.Effective(id => FeatureRegistry.IsOn(id)))
            {
                if (!original.TryGetValue(e.Key, out var current) || Plain(current) != Plain(TextColors.ColorizeText(e.Vanilla)))
                {
                    Skipped.Add(e.Key);
                    continue;
                }
                copy[e.Key] = TextColors.ColorizeText(e.Text);
                AppliedCount++;
            }
            _original = original;
            _applied = copy;
            _liveOriginal = original;
            _liveApplied = copy;
            _liveField = _field;
            _loc.Initialize(copy);
            _decided = true;
            State = when;
            Debug.Log("[Pandaborn.Words] " + AppliedCount + " texts in Inkpaw words (" + when + ", " + language + ")"
                      + (Skipped.Count > 0 ? "; kept vanilla because the game's text differs from the reviewed one: " + string.Join(", ", Skipped) : ""));
        }

        private static string Plain(string s) => (s ?? "").Replace("\r", "");

        private void Restore()
        {
            if (_applied == null) return;
            var current = _field?.GetValue(_loc);
            if (ReferenceEquals(current, _applied))
            {
                _loc.Initialize(_original);
                if (ReferenceEquals(_liveApplied, _applied)) ForgetLive();
            }
            // not ours any more: the language was changed (the game loaded fresh texts), a later game already took over,
            // or another mod swapped its own table in on top of ours. In the last case our table comes back when that
            // mod restores what it found, and RestoreLeftover takes it out at the next game or on the main menu.
            else Debug.Log("[Pandaborn.Words] the game's texts are not the ones this game swapped in; nothing to restore now");
            _applied = null;
            _original = null;
            State = "restored";
        }

        /// <summary>Puts the vanilla texts back if a swap of an earlier game is still in place. Safe at any time.</summary>
        public static void RestoreLeftover(ILoc loc, string when)
        {
            if (_liveApplied == null) return;
            var current = _liveField?.GetValue(loc);
            if (ReferenceEquals(current, _liveApplied))
            {
                loc.Initialize(_liveOriginal);
                Debug.LogWarning("[Pandaborn.Words] vanilla texts restored " + when + " (the last game ended without putting them back)");
            }
            ForgetLive();
        }

        private static void ForgetLive()
        {
            _liveApplied = null;
            _liveOriginal = null;
            _liveField = null;
        }

        private void Degrade(string why, Exception e)
        {
            State = "degraded: " + why;
            _decided = true;
            FeatureRegistry.ReportDegradedInGame("Words", "vanilla words shown: " + why);
            if (e != null) Debug.LogError("[Pandaborn.Words] " + e);
        }

        private string SafeLanguage()
        {
            try { return _localizationService.CurrentLanguage ?? "enUS"; }
            catch (Exception) { return "enUS"; }
        }

        private static FieldInfo FindField(ILoc loc)
        {
            const BindingFlags flags = BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public;
            var type = loc.GetType();
            var named = type.GetField("_localization", flags);
            if (named != null && named.FieldType == typeof(Dictionary<string, string>)) return named;
            var candidates = type.GetFields(flags).Where(f => f.FieldType == typeof(Dictionary<string, string>)).ToList();
            return candidates.Count == 1 ? candidates[0] : null;
        }
    }
}
