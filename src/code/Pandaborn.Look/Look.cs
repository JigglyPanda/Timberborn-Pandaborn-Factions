using System;
using System.Collections.Generic;
using System.Linq;
using Bindito.Core;
using Pandaborn.Specs;
using Timberborn.BlueprintSystem;
using Timberborn.GameFactionSystem;
using Timberborn.SingletonSystem;
using Timberborn.TimbermeshMaterials;
using UnityEngine;

namespace Pandaborn.Look
{
    [Context("Game")]
    public class LookConfigurator : Configurator
    {
        protected override void Configure()
        {
            Bind<MaterialSwap>().AsSingleton();
            MultiBind<IMaterialCollectionIdsProvider>().ToExisting<MaterialSwap>();
        }
    }

    [Context("MainMenu")]
    public class LookMainMenuConfigurator : Configurator
    {
        protected override void Configure()
        {
            Bind<MainMenuRestore>().AsSingleton();
        }
    }

    /// <summary>
    /// Re-themes vanilla building models for a faction whose blueprint carries PandabornLookSpec. The faction keeps listing
    /// the vanilla material collection (so other mods that add to it or inject its materials keep working); this provider is
    /// enumerated by MaterialRepository.Load before any model is built, and on that first enumeration it copies every
    /// material of the spec's collections into the loaded material of the same name (Material.CopyPropertiesFromMaterial:
    /// textures, colours, floats; the game's own shader stays), keeping a backup of each. It yields no collection ids itself.
    /// The originals are put back when the game scene unloads, and again on the main menu as a safety net. Any failure
    /// restores what was changed, logs once and switches the look off for the rest of the session.
    /// </summary>
    public class MaterialSwap : IMaterialCollectionIdsProvider, IUnloadableSingleton
    {
        private const string Tag = "[Pandaborn.Look] ";
        private static readonly List<(Material Target, Material Backup)> Swapped = new List<(Material, Material)>();
        private static bool _failed;

        private readonly FactionService _factionService;
        private readonly ISpecService _specService;
        private bool _done;

        public MaterialSwap(FactionService factionService, ISpecService specService)
        {
            _factionService = factionService;
            _specService = specService;
        }

        /// <summary>Number of materials currently re-themed (for tests).</summary>
        public static int SwappedCount => Swapped.Count;

        public IEnumerable<string> GetMaterialCollectionIds()
        {
            if (!_done)
            {
                _done = true;
                Run();
            }
            yield break;
        }

        public void Unload()
        {
            Restore("on game unload");
        }

        private void Run()
        {
            // a previous game that ended without Unload (exception) must not leave its look behind
            Restore("before a new game");
            if (_failed) return;
            try
            {
                Swap();
            }
            catch (Exception e)
            {
                _failed = true;
                Debug.LogError(Tag + "re-theming failed; the vanilla look is kept for the rest of this session: " + e);
                Restore("after a failed swap");
            }
        }

        private void Swap()
        {
            var faction = _factionService.Current;
            var spec = faction?.Blueprint?.GetSpec<PandabornLookSpec>();
            if (spec == null || spec.MaterialCollectionIds.IsDefaultOrEmpty) return;
            var ours = new HashSet<string>(spec.MaterialCollectionIds.Where(id => !string.IsNullOrEmpty(id)), StringComparer.Ordinal);
            var listed = new HashSet<string>(faction.MaterialCollectionIds, StringComparer.Ordinal);
            listed.ExceptWith(ours);

            var collections = _specService.GetSpecs<MaterialCollectionSpec>().ToList();
            var loaded = new Dictionary<string, Material>(StringComparer.Ordinal);
            foreach (var collection in collections.Where(c => listed.Contains(c.CollectionId)))
                foreach (var reference in collection.Materials)
                {
                    var material = reference?.Asset;
                    if (material != null && !loaded.ContainsKey(material.name)) loaded[material.name] = material;
                }

            int unavailable = 0, unmatched = 0;
            var done = new HashSet<string>(StringComparer.Ordinal);
            foreach (var collection in collections.Where(c => ours.Contains(c.CollectionId)))
                foreach (var reference in collection.Materials)
                {
                    if (reference == null) continue;
                    Material replacement;
                    try { replacement = reference.Asset; }
                    catch (Exception) { replacement = null; }
                    if (replacement == null) { unavailable++; continue; }
                    if (!loaded.TryGetValue(replacement.name, out var target)) { unmatched++; continue; }
                    if (!done.Add(replacement.name)) continue;
                    var backup = new Material(target) { name = target.name + " (Pandaborn backup)" };
                    Swapped.Add((target, backup));
                    target.CopyPropertiesFromMaterial(replacement);
                }

            Debug.Log(Tag + "re-themed " + Swapped.Count + " materials for faction " + faction.Id + " from " + string.Join(", ", ours)
                      + (unavailable > 0 ? "; " + unavailable + " not available (asset bundle missing?)" : "")
                      + (unmatched > 0 ? "; " + unmatched + " match no loaded material" : ""));
        }

        /// <summary>Puts every re-themed material back as it was. Safe to call at any time.</summary>
        public static void Restore(string when)
        {
            if (Swapped.Count == 0) return;
            int n = Swapped.Count, failed = 0;
            foreach (var (target, backup) in Swapped)
            {
                try
                {
                    if (target != null && backup != null) target.CopyPropertiesFromMaterial(backup);
                    if (backup != null) UnityEngine.Object.Destroy(backup);
                }
                catch (Exception e)
                {
                    if (failed++ == 0) Debug.LogError(Tag + "restoring a material failed: " + e);
                }
            }
            Swapped.Clear();
            Debug.Log(Tag + "restored " + n + " materials " + when + (failed > 0 ? " (" + failed + " failed)" : ""));
        }
    }

    /// <summary>Safety net: if a game scene ended without Unload, put the vanilla materials back on the main menu.</summary>
    public class MainMenuRestore : ILoadableSingleton
    {
        public void Load()
        {
            try { MaterialSwap.Restore("on main menu"); }
            catch (Exception e) { Debug.LogError("[Pandaborn.Look] restore on the main menu failed: " + e); }
        }
    }
}
