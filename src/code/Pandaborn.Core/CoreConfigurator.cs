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
            MultiBind<INightShiftClock>().To<NoNightShiftClock>().AsSingleton();
            MultiBind<IGatheringClock>().To<NoGatheringClock>().AsSingleton();


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
    /// game. The first failure of a named piece is logged once and the piece is switched off until the game is left: the
    /// next game (a new one, or a save loaded) builds its interface afresh and gets a fresh try.
    /// </summary>
    public static class SafeUi
    {
        private static readonly HashSet<string> Broken = new HashSet<string>(StringComparer.Ordinal);

        public static bool IsBroken(string piece) => Broken.Contains(piece);

        /// <summary>Called by Core when a game starts loading.</summary>
        internal static void StartGame() => Broken.Clear();

        public static void Run(string piece, Action action)
        {
            if (Broken.Contains(piece)) return;
            try { action(); }
            catch (Exception e)
            {
                Broken.Add(piece);
                Debug.LogError("[Pandaborn] interface piece '" + piece + "' failed and is off until this game is left: " + e);
            }
        }

        public static T Get<T>(string piece, Func<T> func, T fallback)
        {
            if (Broken.Contains(piece)) return fallback;
            try { return func(); }
            catch (Exception e)
            {
                Broken.Add(piece);
                Debug.LogError("[Pandaborn] interface piece '" + piece + "' failed and is off until this game is left: " + e);
                return fallback;
            }
        }
    }
}
