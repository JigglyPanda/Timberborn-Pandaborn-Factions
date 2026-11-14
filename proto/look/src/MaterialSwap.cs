using System;
using System.Collections.Generic;
using System.Linq;
using Bindito.Core;
using Timberborn.BlueprintSystem;
using Timberborn.GameFactionSystem;
using Timberborn.SingletonSystem;
using Timberborn.TimbermeshMaterials;
using UnityEngine;

namespace PandabornProtoLook
{
    /// <summary>
    /// "Swap" variant of the look prototype. The faction keeps listing the vanilla "Folktails" material collection
    /// (so every mod that adds materials or buildings to Folktails, or that injects Folktails materials into other
    /// factions like ChooChoo, keeps working). In a game of a faction that has a material collection called
    /// "PandabornLook.&lt;FactionId&gt;", each material in it is copied *into* the loaded material of the same name
    /// (Material.CopyPropertiesFromMaterial: textures, colours, floats; the game's own shader stays). The originals
    /// are restored when the game scene unloads, and again on the main menu as a safety net.
    ///
    /// Ordering: this provider is enumerated inside MaterialRepository.Load (which asks every
    /// IMaterialCollectionIdsProvider for ids while it fills its dictionary), i.e. before any model is built. It
    /// yields no ids itself.
    /// </summary>
    internal class MaterialSwap : IMaterialCollectionIdsProvider, IUnloadableSingleton
    {
        private const string CollectionPrefix = "PandabornLook.";
        internal static readonly List<(Material Target, Material Backup)> Swapped = new List<(Material, Material)>();

        private readonly FactionService _factionService;
        private readonly ISpecService _specService;
        private bool _done;

        public MaterialSwap(FactionService factionService, ISpecService specService)
        {
            _factionService = factionService;
            _specService = specService;
        }

        public IEnumerable<string> GetMaterialCollectionIds()
        {
            if (!_done)
            {
                _done = true;
                try
                {
                    Swap();
                }
                catch (Exception e)
                {
                    Debug.LogError("[PandabornProtoLook] material swap failed: " + e);
                    Restore("after a failed swap");
                }
            }
            yield break;
        }

        private void Swap()
        {
            var faction = _factionService.Current;
            if (faction == null) return;
            string id = CollectionPrefix + faction.Id;
            var specs = _specService.GetSpecs<MaterialCollectionSpec>().ToList();
            var ours = specs.Where(s => s.CollectionId == id).SelectMany(s => s.Materials).Select(r => r.Asset)
                            .Where(m => m != null).ToList();
            if (ours.Count == 0) return;
            var loaded = specs.Where(s => faction.MaterialCollectionIds.Contains(s.CollectionId))
                              .SelectMany(s => s.Materials).Select(r => r.Asset).Where(m => m != null)
                              .GroupBy(m => m.name).ToDictionary(g => g.Key, g => g.First());
            Restore("before a new swap");
            int n = 0;
            foreach (var replacement in ours)
            {
                if (!loaded.TryGetValue(replacement.name, out var target))
                {
                    Debug.LogWarning("[PandabornProtoLook] no loaded material named " + replacement.name);
                    continue;
                }
                var backup = new Material(target) { name = target.name + " (Pandaborn backup)" };
                Swapped.Add((target, backup));
                target.CopyPropertiesFromMaterial(replacement);
                n++;
            }
            Debug.Log("[PandabornProtoLook] re-themed " + n + " materials for faction " + faction.Id + " from " + id);
        }

        public void Unload()
        {
            Restore("on game unload");
        }

        internal static void Restore(string when)
        {
            if (Swapped.Count == 0) return;
            foreach (var (target, backup) in Swapped)
            {
                if (target != null && backup != null) target.CopyPropertiesFromMaterial(backup);
                if (backup != null) UnityEngine.Object.Destroy(backup);
            }
            Debug.Log("[PandabornProtoLook] restored " + Swapped.Count + " materials " + when);
            Swapped.Clear();
        }
    }

    /// <summary>Safety net: if a game scene ended without Unload (exception), put the vanilla materials back.</summary>
    internal class MainMenuRestore : ILoadableSingleton
    {
        public void Load()
        {
            MaterialSwap.Restore("on main menu");
        }
    }

    [Context("Game")]
    internal class GameConfigurator : Configurator
    {
        protected override void Configure()
        {
            Bind<MaterialSwap>().AsSingleton();
            MultiBind<IMaterialCollectionIdsProvider>().ToExisting<MaterialSwap>();
        }
    }

    [Context("MainMenu")]
    internal class MainMenuConfigurator : Configurator
    {
        protected override void Configure()
        {
            Bind<MainMenuRestore>().AsSingleton();
        }
    }
}
