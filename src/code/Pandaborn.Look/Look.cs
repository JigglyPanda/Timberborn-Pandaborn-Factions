using System;
using System.Collections.Generic;
using System.Linq;
using Bindito.Core;
using Pandaborn.Core;
using Timberborn.AssetSystem;
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
    /// Re-themes vanilla building models in an Inkpaws game. No blueprint data is involved (the faction file is read in every
    /// game, so it stays plain): the module activates when the loaded faction's Id is "Inkpaws", and its replacements are
    /// simply every material our asset bundle holds under Materials/Pandaborn/Look/. The faction keeps listing the vanilla
    /// material collection (so other mods that add to it or inject its materials keep working); this provider is enumerated
    /// by MaterialRepository.Load before any model is built, and on that first enumeration it copies each of our materials
    /// into the loaded material of the same name from the faction's collections (Material.CopyPropertiesFromMaterial:
    /// textures, colours, floats; the game's own shader stays), keeping a backup of each. It yields no collection ids itself.
    /// The originals are put back when the game scene unloads, and again on the main menu as a safety net. Any failure
    /// restores what was changed, logs once and switches the look off for the rest of the session.
    /// </summary>
    public class MaterialSwap : IMaterialCollectionIdsProvider, IUnloadableSingleton
    {
        private const string Tag = "[Pandaborn.Look] ";
        private const string FactionId = "Inkpaws";
        /// <summary>Bundle asset folder of the replacement materials (asset path after /Resources/).</summary>
        private const string MaterialFolder = "Materials/Pandaborn/Look";
        private static readonly List<(Material Target, Material Backup)> Swapped = new List<(Material, Material)>();
        private static bool _failed;
        /// <summary>The game whose swap is in place. Its Unload restores; an older game's late Unload must not undo a
        /// newer game's swap (the materials are shared by the whole session).</summary>
        private static MaterialSwap _owner;

        private readonly FactionService _factionService;
        private readonly ISpecService _specService;
        private readonly IAssetLoader _assetLoader;
        private bool _done;

        public MaterialSwap(FactionService factionService, ISpecService specService, IAssetLoader assetLoader)
        {
            _factionService = factionService;
            _specService = specService;
            _assetLoader = assetLoader;
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
            if (_owner != null && !ReferenceEquals(_owner, this)) return;
            Restore("on game unload");
        }

        private void Run()
        {
            // a previous game that ended without Unload (exception) must not leave its look behind
            Restore("before a new game");
            if (_failed)
            {
                ReportFailed();
                return;
            }
            try
            {
                Swap();
                if (Swapped.Count > 0) _owner = this;
            }
            catch (Exception e)
            {
                _failed = true;
                Debug.LogError(Tag + "re-theming failed; the vanilla look is kept for the rest of this session: " + e);
                Restore("after a failed swap");
                ReportFailed();
            }
        }

        private void ReportFailed()
        {
            try
            {
                if (_factionService.Current?.Id == FactionId)
                    FeatureRegistry.ReportDegradedInGame("Look", "re-theming failed earlier in this session; buildings keep the Folktails look until the game is restarted");
            }
            catch (Exception) { }
        }

        private void Swap()
        {
            var faction = _factionService.Current;
            if (faction == null || faction.Id != FactionId) return;

            var loaded = new Dictionary<string, Material>(StringComparer.Ordinal);
            var listed = new HashSet<string>(faction.MaterialCollectionIds, StringComparer.Ordinal);
            foreach (var collection in _specService.GetSpecs<MaterialCollectionSpec>().Where(c => listed.Contains(c.CollectionId)))
                foreach (var reference in collection.Materials)
                {
                    Material material;
                    try { material = reference?.Asset; }
                    catch (Exception) { material = null; }       // another mod's broken entry is not our business
                    if (material != null && !loaded.ContainsKey(material.name)) loaded[material.name] = material;
                }

            // only mod-provided assets: an empty resource list keeps the game's own Resources out of the search
            var ours = _assetLoader.LoadAll<Material>(MaterialFolder, Array.Empty<string>())
                                   .Where(a => !a.IsBuiltIn && a.Asset != null)
                                   .Select(a => a.Asset)
                                   .ToList();
            if (ours.Count == 0)
            {
                Debug.Log(Tag + "no replacement materials under " + MaterialFolder + " (asset bundle missing?): vanilla look");
                FeatureRegistry.ReportNoData("Look", "the pandabornlook asset bundle is not loaded; buildings keep the Folktails look");
                return;
            }

            int unmatched = 0;
            var done = new HashSet<string>(StringComparer.Ordinal);
            foreach (var replacement in ours)
            {
                if (!loaded.TryGetValue(replacement.name, out var target)) { unmatched++; continue; }
                if (!done.Add(replacement.name)) continue;
                var backup = new Material(target) { name = target.name + " (Pandaborn backup)" };
                Swapped.Add((target, backup));
                target.CopyPropertiesFromMaterial(replacement);
            }

            Debug.Log(Tag + "re-themed " + Swapped.Count + " materials for faction " + faction.Id + " from " + MaterialFolder
                      + (unmatched > 0 ? "; " + unmatched + " match no loaded material" : ""));
        }

        /// <summary>Puts every re-themed material back as it was. Safe to call at any time.</summary>
        public static void Restore(string when)
        {
            if (Swapped.Count == 0) { _owner = null; return; }
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
            _owner = null;
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
