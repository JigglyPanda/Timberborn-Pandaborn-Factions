using System;
using System.Linq;
using System.Reflection;
using Timberborn.BaseComponentSystem;
using Timberborn.Characters;
using Timberborn.TemplateSystem;
using UnityEngine;

namespace Pandaborn.Ringtails.Dev
{
    /// <summary>
    /// Dev only. Reaches the shipped Pandaborn.Ringtails module (loaded by the faction mod's bootstrap with Assembly.Load) by
    /// name, so this test mod has no compile-time reference to it and carries no spec or game code of its own.
    /// </summary>
    public static class ModuleBridge
    {
        private static Type _service;
        private static Type _nursery;
        private static bool _resolved;

        private static void Resolve()
        {
            if (_resolved) return;
            _resolved = true;
            var assembly = AppDomain.CurrentDomain.GetAssemblies().FirstOrDefault(a => a.GetName().Name == "Pandaborn.Ringtails");
            _service = assembly?.GetType("Pandaborn.Ringtails.RingtailService");
            _nursery = assembly?.GetType("Pandaborn.Ringtails.LoftNursery");
        }

        public static object Service
        {
            get
            {
                Resolve();
                return _service?.GetProperty("Current", BindingFlags.Public | BindingFlags.Static)?.GetValue(null);
            }
        }

        private static T Get<T>(string name, T fallback)
        {
            var s = Service;
            var v = s?.GetType().GetProperty(name)?.GetValue(s);
            return v is T t ? t : fallback;
        }

        public static bool Loaded
        {
            get { Resolve(); return _service != null; }
        }

        public static bool Enabled => Get("Enabled", false);
        public static bool IsRingtailsGame => Get("IsRingtailsGame", false);
        public static bool Arrived => Get("Arrived", false);
        public static string DisabledReason => Get<string>("DisabledReason", null);

        public static int KitsRaised
        {
            get
            {
                Resolve();
                return _nursery?.GetProperty("KitsRaised", BindingFlags.Public | BindingFlags.Static)?.GetValue(null) is int n ? n : -1;
            }
        }

        public static Character CreateAdult(Vector3 position, float progress)
        {
            var s = Service;
            return s?.GetType().GetMethod("CreateAdult")?.Invoke(s, new object[] { position, progress }) as Character;
        }

        public static Character CreateChild(Vector3 position)
        {
            var s = Service;
            return s?.GetType().GetMethod("CreateChild")?.Invoke(s, new object[] { position }) as Character;
        }

        /// <summary>By template name: the module's spec types are not visible here.</summary>
        public static bool IsRingtail(BaseComponent c)
        {
            var name = c ? c.GetComponent<TemplateSpec>()?.TemplateName : null;
            return name != null && name.StartsWith("Ringtail", StringComparison.Ordinal);
        }

        public static bool IsNightPost(BaseComponent b)
        {
            var name = b ? b.GetComponent<TemplateSpec>()?.TemplateName : null;
            return name != null && name.StartsWith("PandabornNight", StringComparison.Ordinal);
        }

        public static bool IsMoonLoft(BaseComponent b)
        {
            var name = b ? b.GetComponent<TemplateSpec>()?.TemplateName : null;
            return name != null && name.StartsWith("PandabornMoonLoft", StringComparison.Ordinal);
        }

        /// <summary>The text a module UI piece last showed (its static ShownText).</summary>
        public static string Shown(string typeName) => Static(typeName, "ShownText")?.ToString();

        /// <summary>Any public static property of a module type (tests read the UI and sound pieces' last state).</summary>
        public static object Static(string typeName, string property)
        {
            Resolve();
            var t = _service?.Assembly.GetType("Pandaborn.Ringtails." + typeName);
            return t?.GetProperty(property, BindingFlags.Public | BindingFlags.Static)?.GetValue(null);
        }

        /// <summary>A Moon Loft's nursery state (its loc key, "" before the first dawn after load).</summary>
        public static string LoftKitState(BaseComponent loft)
        {
            Resolve();
            var t = _service?.Assembly.GetType("Pandaborn.Ringtails.MoonLoft");
            if (t == null || !loft) return null;
            var component = loft.AllComponents.FirstOrDefault(c => c != null && c.GetType() == t);
            return component == null ? null : t.GetProperty("KitState")?.GetValue(component) as string;
        }
    }
}
