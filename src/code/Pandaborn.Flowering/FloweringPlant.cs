using System;
using Pandaborn.Specs;
using Timberborn.BaseComponentSystem;
using Timberborn.BlockSystem;
using Timberborn.Cutting;
using Timberborn.EntitySystem;
using Timberborn.Growing;
using Timberborn.NaturalResourcesLifecycle;
using Timberborn.TemplateSystem;
using UnityEngine;

namespace Pandaborn.Flowering
{
    /// <summary>
    /// A bamboo that can flower (decorates PandabornFloweringPlantSpec). Registers with the Flowering, is held from growing
    /// while its species rests after a Flowering, and shows buds while a Flowering of its species is announced (when the
    /// plant's spec says the buds are painted in its detail map). Nothing is saved.
    /// </summary>
    public class FloweringPlant : BaseComponent, IAwakableComponent, IPostInitializableEntity, IDeletableEntity
    {
        private const string MatureNode = "Mature";
        private readonly FloweringService _floweringService;
        private bool _budsShown;

        public FloweringPlant(FloweringService floweringService)
        {
            _floweringService = floweringService;
        }

        public PandabornFloweringPlantSpec Spec { get; private set; }

        public string Species { get; private set; }

        public Growable Growable { get; private set; }

        public LivingNaturalResource Living { get; private set; }

        public Cuttable Cuttable { get; private set; }

        public BlockObject BlockObject { get; private set; }

        public void Awake()
        {
            Spec = GetComponent<PandabornFloweringPlantSpec>();
            Species = GetComponent<TemplateSpec>()?.TemplateName;
            Growable = GetComponent<Growable>();
            Living = GetComponent<LivingNaturalResource>();
            Cuttable = GetComponent<Cuttable>();
            BlockObject = GetComponent<BlockObject>();
        }

        public void PostInitializeEntity()
        {
            if (_floweringService.Active) _floweringService.AddPlant(this);
        }

        public void DeleteEntity()
        {
            _floweringService.RemovePlant(this);
        }

        public bool IsDead => Living != null && Living.IsDead;

        public bool IsGrown => Growable != null && Growable.IsGrown;

        /// <summary>Cut but its harvest still lies on the tile (the entity goes once the pile is carried away).</summary>
        public bool IsHarvestedPile => Cuttable != null && Cuttable.RemoveOnCut && Cuttable.Yielder != null && Cuttable.Yielder.IsYieldRemoved;

        /// <summary>Shows or hides the buds (the material's detail map on the grown model), if this plant paints them there.</summary>
        public void ShowBuds(bool show)
        {
            if (Spec == null || !Spec.BudsUseDetail || show == _budsShown) return;
            try
            {
                foreach (var t in GameObject.GetComponentsInChildren<Transform>(true))
                {
                    if (t.name != MatureNode) continue;
                    foreach (var r in t.GetComponentsInChildren<Renderer>(true))
                        r.material.SetFloat("_EnableDetail", show ? 1f : 0f);
                }
                _budsShown = show;
            }
            catch (Exception e) { Debug.LogError("[Pandaborn.Flowering] buds failed: " + e.Message); }
        }
    }

    /// <summary>
    /// A bamboo in flower (decorates PandabornInFlowerSpec): bears bamboo seed as its harvest (data: its cut yield) and dies
    /// SeedDays after the Flowering. Counts the seed taken from it. Nothing is saved.
    /// </summary>
    public class InFlowerPlant : BaseComponent, IAwakableComponent, IPostInitializableEntity, IDeletableEntity
    {
        private readonly FloweringService _floweringService;

        public InFlowerPlant(FloweringService floweringService)
        {
            _floweringService = floweringService;
        }

        public string Species { get; private set; }

        public LivingNaturalResource Living { get; private set; }

        public Cuttable Cuttable { get; private set; }

        public BlockObject BlockObject { get; private set; }

        public bool IsDead => Living != null && Living.IsDead;

        /// <summary>Seed still on the plant.</summary>
        public int SeedLeft => Cuttable != null && Cuttable.Yielder != null && !IsDead ? Cuttable.Yielder.Yield.Amount : 0;

        public void Awake()
        {
            Species = GetComponent<PandabornInFlowerSpec>()?.Species;
            Living = GetComponent<LivingNaturalResource>();
            Cuttable = GetComponent<Cuttable>();
            BlockObject = GetComponent<BlockObject>();
        }

        public void PostInitializeEntity()
        {
            if (!_floweringService.Active) return;
            _floweringService.AddInFlower(this);
            if (Cuttable != null) Cuttable.WasCut += OnCut;
        }

        public void DeleteEntity()
        {
            if (Cuttable != null) Cuttable.WasCut -= OnCut;
            _floweringService.RemoveInFlower(this);
        }

        private void OnCut(object sender, EventArgs e)
        {
            int amount = Cuttable.YielderSpec?.Yield.Amount ?? 0;
            _floweringService.OnSeedCut(amount);
        }
    }
}
