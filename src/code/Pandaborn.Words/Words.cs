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
            if (_applied == null && State != "not our faction" && !State.StartsWith("degraded"))
            {
                try { Apply(FactionId(), "load"); }
                catch (Exception e) { Degrade("swap failed: " + e.Message, e); }
            }
        }

        public void Unload()
        {
            try { Restore(); }
            catch (Exception e) { Debug.LogError("[Pandaborn.Words] restoring vanilla texts failed: " + e); }
        }

        public void Apply(string factionId, string when)
        {
            if (_applied != null) return;
            Skipped.Clear();
            AppliedCount = 0;
            string language = SafeLanguage();
            var table = WordsTable.Load(FeatureRegistry.Owner, language);
            if (table == null)
            {
                State = "no table for " + language;
                // other languages have no table by design; a missing enUS table is a build without the module's data
                if (language == "enUS" && FactionId() == "Inkpaws") FeatureRegistry.ReportNoData("Words", "no Pandaborn/Words/words.enUS.txt in the mod");
                return;
            }
            if (factionId == null || !string.Equals(factionId, table.Faction, StringComparison.Ordinal)) { State = "not our faction"; return; }
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
            _loc.Initialize(copy);
            State = when;
            Debug.Log("[Pandaborn.Words] " + AppliedCount + " texts in Inkpaw words (" + when + ", " + language + ")"
                      + (Skipped.Count > 0 ? "; kept vanilla because the game's text differs from the reviewed one: " + string.Join(", ", Skipped) : ""));
        }

        private static string Plain(string s) => (s ?? "").Replace("\r", "");

        private void Restore()
        {
            if (_applied == null) return;
            var current = _field?.GetValue(_loc);
            if (ReferenceEquals(current, _applied)) _loc.Initialize(_original);
            else Debug.Log("[Pandaborn.Words] the texts were reloaded meanwhile (language change); nothing to restore");
            _applied = null;
            _original = null;
            State = "restored";
        }

        private void Degrade(string why, Exception e)
        {
            State = "degraded: " + why;
            FeatureRegistry.ReportDegraded("Words", "vanilla words shown: " + why);
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

    /// <summary>
    /// words.&lt;language&gt;.txt in the mod's Pandaborn/Words folder. Lines: "faction: Id"; "KEY TAB replacement TAB vanilla";
    /// "@Feature TAB KEY TAB replacement TAB vanilla" (only while that Pandaborn feature is on; wins over the plain line);
    /// '#' comments; \n \t \\ escapes.
    /// </summary>
    public class WordsTable
    {
        public string Faction = "Inkpaws";
        public readonly List<Entry> Entries = new List<Entry>();

        public class Entry
        {
            public string Feature;
            public string Key;
            public string Text;
            public string Vanilla;
        }

        public static WordsTable Load(string modPath, string language)
        {
            if (string.IsNullOrEmpty(modPath)) return null;
            string file = Path.Combine(modPath, "Pandaborn", "Words", "words." + language + ".txt");
            if (!File.Exists(file)) return null;
            var table = new WordsTable();
            foreach (var raw in File.ReadAllLines(file))
            {
                string line = raw.TrimEnd('\r');
                if (line.Length == 0 || line[0] == '#') continue;
                if (line.StartsWith("faction:", StringComparison.Ordinal)) { table.Faction = line.Substring(8).Trim(); continue; }
                var p = line.Split('\t');
                string feature = null;
                if (p[0].StartsWith("@", StringComparison.Ordinal)) { feature = p[0].Substring(1); p = p.Skip(1).ToArray(); }
                if (p.Length < 3) continue;
                table.Entries.Add(new Entry { Feature = feature, Key = p[0], Text = Unescape(p[1]), Vanilla = Unescape(p[2]) });
            }
            return table;
        }

        /// <summary>One entry per key: the feature-specific line when its feature is on, else the plain line.</summary>
        public IEnumerable<Entry> Effective(Func<string, bool> featureOn)
        {
            var byKey = new Dictionary<string, Entry>(StringComparer.Ordinal);
            foreach (var e in Entries.Where(e => e.Feature == null)) byKey[e.Key] = e;
            foreach (var e in Entries.Where(e => e.Feature != null && featureOn(e.Feature))) byKey[e.Key] = e;
            return byKey.Values;
        }

        public static string Unescape(string s)
        {
            if (s.IndexOf('\\') < 0) return s;
            var sb = new System.Text.StringBuilder(s.Length);
            for (int i = 0; i < s.Length; i++)
            {
                char c = s[i];
                if (c == '\\' && i + 1 < s.Length)
                {
                    char n = s[++i];
                    sb.Append(n == 'n' ? '\n' : n == 'r' ? '\r' : n == 't' ? '\t' : n);
                }
                else sb.Append(c);
            }
            return sb.ToString();
        }
    }
}
