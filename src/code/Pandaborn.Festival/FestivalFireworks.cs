using System;
using System.Linq;
using System.Reflection;
using Pandaborn.Core;
using Timberborn.EntitySystem;
using Timberborn.FireworkSystem;
using UnityEngine;

namespace Pandaborn.Festival
{
    /// <summary>
    /// Launches the game's own fireworks (the 1.1 firework entities: trail, burst and their sounds) from any point, as the
    /// vanilla launcher does. The firework component (Timberborn.FireworkSystem.Firework) is internal, so its public
    /// Launch(Vector3, Quaternion, float) is reached by reflection: the one non-public dependency of the show.
    /// Fallback (ENGINEERING.md, code rule 4): if the type or method is gone, or the dev switch simulates that
    /// ("simulate-missing-member: Festival.Fireworks"), no firework is spawned and the festival runs without its show; one
    /// line is logged. A spawned entity whose component cannot be found is deleted at once.
    /// </summary>
    public class FestivalFireworks
    {
        private const string FireworkTypeName = "Timberborn.FireworkSystem.Firework";
        private static readonly Type FireworkType = typeof(FireworkSpecService).Assembly.GetType(FireworkTypeName);
        private static readonly MethodInfo LaunchMethod =
            FireworkType?.GetMethod("Launch", BindingFlags.Instance | BindingFlags.Public, null, new[] { typeof(Vector3), typeof(Quaternion), typeof(float) }, null);

        private readonly FireworkSpecService _fireworkSpecService;
        private readonly EntityService _entityService;
        private string _failure;

        public FestivalFireworks(FireworkSpecService fireworkSpecService, EntityService entityService)
        {
            _fireworkSpecService = fireworkSpecService;
            _entityService = entityService;
            if (FeatureRegistry.DevFlag("simulate-missing-member", "Festival.Fireworks")) _failure = "simulated missing " + FireworkTypeName + ".Launch (dev switch)";
            else if (FireworkType == null) _failure = FireworkTypeName + " not found";
            else if (LaunchMethod == null) _failure = FireworkTypeName + ".Launch(Vector3, Quaternion, float) not found";
            if (_failure != null) Debug.LogWarning("[Pandaborn.Festival] fireworks are off: " + _failure + ". Festivals run without their show.");
        }

        public bool Available => _failure == null;

        public string Unavailable => _failure;

        /// <summary>Launches one firework from a world position. Pitch in degrees from straight up, heading in degrees.</summary>
        public bool Launch(string fireworkId, Vector3 position, float pitch, float heading, float distance)
        {
            if (_failure != null || string.IsNullOrEmpty(fireworkId)) return false;
            try
            {
                if (!_fireworkSpecService.HasSpec(fireworkId)) return false;
                var spec = _fireworkSpecService.GetFireworkSpec(fireworkId);
                var entity = _entityService.Instantiate(spec.Blueprint);
                entity.GameObject.SetActive(true);
                var firework = entity.AllComponents.FirstOrDefault(c => c != null && FireworkType.IsInstanceOfType(c));
                if (firework == null)
                {
                    _entityService.Delete(entity);
                    Fail(FireworkTypeName + " component not found on " + fireworkId);
                    return false;
                }
                var rotation = Quaternion.Euler(-90f + pitch, heading, 0f);
                LaunchMethod.Invoke(firework, new object[] { position, rotation, Mathf.Clamp(distance, FireworkLimits.MinFlightDistance, FireworkLimits.MaxFlightDistance) });
                return true;
            }
            catch (Exception e)
            {
                Fail(e.GetType().Name + ": " + e.Message);
                return false;
            }
        }

        private void Fail(string reason)
        {
            if (_failure != null) return;
            _failure = reason;
            Debug.LogError("[Pandaborn.Festival] fireworks switched off for this game: " + reason);
            var service = FestivalService.Current;
            if (service != null && service.Active) service.Fault("no fireworks in the sky (" + reason + ")");
        }
    }
}
