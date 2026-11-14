using System;
using System.Collections.Generic;
using Bindito.Core;
using Pandaborn.Specs;
using Timberborn.TemplateInstantiation;
using UnityEngine;

namespace Pandaborn.Core
{
    [Context("Game")]
    public class PandabornCoreConfigurator : Configurator
    {
        protected override void Configure()
        {
            Bind<PandabornStore>().AsSingleton();
            Bind<Messenger>().AsSingleton();
            Bind<PandabornSounds>().AsSingleton();
            Bind<FeatureNotices>().AsSingleton();
            Bind<PandabornEntityState>().AsTransient();
            MultiBind<IWorkdayClock>().To<NoWorkdayClock>().AsSingleton();
            MultiBind<TemplateModule>().ToProvider(ProvideTemplateModule).AsSingleton();
        }

        private static TemplateModule ProvideTemplateModule()
        {
            var builder = new TemplateModule.Builder();
            builder.AddDecorator<PandabornEntityStateSpec, PandabornEntityState>();
            return builder.Build();
        }
    }

    /// <summary>
    /// Guard for interface code (ENGINEERING.md, code rule 7): an exception in one of our panels must never break the
    /// game. The first failure of a named piece is logged once and the piece is switched off for the session.
    /// </summary>
    public static class SafeUi
    {
        private static readonly HashSet<string> Broken = new HashSet<string>(StringComparer.Ordinal);

        public static bool IsBroken(string piece) => Broken.Contains(piece);

        public static void Run(string piece, Action action)
        {
            if (Broken.Contains(piece)) return;
            try { action(); }
            catch (Exception e)
            {
                Broken.Add(piece);
                Debug.LogError("[Pandaborn] interface piece '" + piece + "' failed and is off for this session: " + e);
            }
        }

        public static T Get<T>(string piece, Func<T> func, T fallback)
        {
            if (Broken.Contains(piece)) return fallback;
            try { return func(); }
            catch (Exception e)
            {
                Broken.Add(piece);
                Debug.LogError("[Pandaborn] interface piece '" + piece + "' failed and is off for this session: " + e);
                return fallback;
            }
        }
    }
}
