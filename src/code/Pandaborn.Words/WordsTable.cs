using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace Pandaborn.Words
{
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
                // "@Feature"; a table built before the builder was fixed says "@@Feature"
                if (p[0].StartsWith("@", StringComparison.Ordinal)) { feature = p[0].TrimStart('@').Trim(); p = p.Skip(1).ToArray(); }
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
