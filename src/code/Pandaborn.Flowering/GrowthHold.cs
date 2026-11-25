using System;
using System.Reflection;
using Pandaborn.Core;
using Timberborn.Growing;
using Timberborn.NaturalResourcesLifecycle;
using Timberborn.TimeSystem;
using UnityEngine;

namespace Pandaborn.Flowering
{
    /// <summary>
    /// Holds a young plant's growth during the rest after a Flowering, and lets it go again. The game has no public pause
    /// for growth (Growable pauses its own timer only while the plant is dying or dead), so this reaches the plant's growth
    /// timer, the private field Growable._timeTrigger (an ITimeTrigger, a public interface with Pause/Resume).
    /// Nothing is saved: the timer's progress is saved by the game as always; on load the game resumes it and the service
    /// holds it again.
    /// The timer is read from the plant at every call, never kept: the game resumes it by itself when a plant stops
    /// dying, and another mod may put a new timer object in the field (TimberCommons' GrowthRateModifier does when one of
    /// its growth modifiers registers, and resumes it). FloweringService therefore holds every resting plant again each
    /// in-game hour, after a load and when a plant is planted; such a plant grows for at most an hour in between (the
    /// Flowering is a little milder, never harsher).
    /// Fallback (ENGINEERING.md, code rule 4): if the field is gone or has another type, or the dev switch says
    /// "simulate-missing-member: Flowering.GrowthHold", young bamboo grows at once after a Flowering (the event is shorter
    /// and milder) and one warning is logged.
    /// </summary>
    public static class GrowthHold
    {
        private static readonly FieldInfo TimeTriggerField =
            typeof(Growable).GetField("_timeTrigger", BindingFlags.Instance | BindingFlags.NonPublic);
        private static string _failure;
        private static bool _checked;

        public static bool Available
        {
            get
            {
                if (!_checked)
                {
                    _checked = true;
                    if (FeatureRegistry.DevFlag("simulate-missing-member", "Flowering.GrowthHold")) _failure = "simulated: Growable._timeTrigger missing";
                    else if (TimeTriggerField == null) _failure = "Growable._timeTrigger not found";
                    else if (!typeof(ITimeTrigger).IsAssignableFrom(TimeTriggerField.FieldType)) _failure = "Growable._timeTrigger is no longer an ITimeTrigger";
                    if (_failure != null)
                        Debug.LogWarning("[Pandaborn.Flowering] young bamboo cannot be held after a Flowering: " + _failure
                                         + ". It regrows at once instead.");
                }
                return _failure == null;
            }
        }

        public static string Unavailable => Available ? null : _failure;

        /// <summary>Pauses the growth of a plant that is not grown yet. True when it is (now) held;
        /// <paramref name="wasGrowing"/> when its timer was running until this call.</summary>
        public static bool Hold(Growable growable, out bool wasGrowing)
        {
            wasGrowing = false;
            if (!Available || growable == null) return false;
            try
            {
                if (growable.IsGrown) return false;
                var trigger = Trigger(growable);
                if (trigger == null) return false;
                wasGrowing = trigger.InProgress;
                trigger.Pause();
                return true;
            }
            catch (Exception e) { return Broken(e); }
        }

        /// <summary>Lets a held plant grow again, unless it is dead or dying (then the game resumes it when it recovers).</summary>
        public static void Release(Growable growable)
        {
            if (!Available || growable == null) return;
            try
            {
                if (growable.IsGrown) return;
                var living = growable.GetComponent<LivingNaturalResource>();
                var dying = growable.GetComponent<DyingNaturalResource>();
                if ((living != null && living.IsDead) || (dying != null && dying.IsDying)) return;
                Trigger(growable)?.Resume();
            }
            catch (Exception e) { Broken(e); }
        }

        /// <summary>The timer no longer behaves as it did (the game changed, or another mod's timer throws): no more holds
        /// in this session, said once in the log and in the feature report.</summary>
        private static bool Broken(Exception e)
        {
            if (_failure == null)
            {
                _failure = e.GetType().Name + ": " + e.Message;
                Debug.LogError("[Pandaborn.Flowering] growth hold switched off: " + _failure);
                // per game: FloweringService.Load reports it again in every later game of the session
                var service = FloweringService.Current;
                if (service != null && service.Active) service.Fault("young bamboo regrows at once after a Flowering (" + _failure + ")");
            }
            return false;
        }

        private static ITimeTrigger Trigger(Growable growable)
        {
            try { return TimeTriggerField.GetValue(growable) as ITimeTrigger; }
            catch (Exception e)
            {
                Broken(e);
                return null;
            }
        }
    }
}
