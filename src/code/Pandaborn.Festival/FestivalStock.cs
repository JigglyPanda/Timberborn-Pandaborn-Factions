using System;
using System.Collections.Generic;
using System.Linq;
using Pandaborn.Specs;
using Timberborn.GameDistricts;
using Timberborn.Goods;
using Timberborn.InventorySystem;

namespace Pandaborn.Festival
{
    /// <summary>What a district has towards a festival, counted in its ordinary stores (every public inventory the district
    /// registers: warehouses, piles, workshop outputs, the district center), unreserved stock only.</summary>
    public sealed class FestivalStock
    {
        public int Lanterns;
        public int Fireworks;
        /// <summary>Every dish of the spec's list with its stock, most first.</summary>
        public readonly List<KeyValuePair<string, int>> Dishes = new List<KeyValuePair<string, int>>();

        public int LanternsNeeded;
        public int FireworksNeeded;
        public int DishKinds;
        public int DishAmount;

        /// <summary>Dish kinds with at least DishAmount in store.</summary>
        public int ReadyDishKinds => Dishes.Count(d => d.Value >= DishAmount);

        public bool LanternsReady => Lanterns >= LanternsNeeded;

        public bool DishesReady => ReadyDishKinds >= DishKinds;

        public bool Ready => LanternsReady && DishesReady;

        public bool GrandReady => FireworksNeeded > 0 && Fireworks >= FireworksNeeded;

        public static FestivalStock Count(DistrictCenter district, PandabornFestivalSpec spec)
        {
            var stock = new FestivalStock
            {
                LanternsNeeded = Math.Max(0, spec.Lanterns),
                FireworksNeeded = string.IsNullOrEmpty(spec.FireworksGoodId) ? 0 : Math.Max(0, spec.Fireworks),
                DishKinds = Math.Max(0, spec.DishKinds),
                DishAmount = Math.Max(1, spec.DishAmount)
            };
            var registry = district ? district.GetComponent<DistrictInventoryRegistry>() : null;
            if (registry == null) return stock;
            stock.Lanterns = Amount(registry, spec.LanternGoodId);
            if (stock.FireworksNeeded > 0) stock.Fireworks = Amount(registry, spec.FireworksGoodId);
            if (!spec.Dishes.IsDefaultOrEmpty)
                foreach (var dish in spec.Dishes.Distinct())
                    stock.Dishes.Add(new KeyValuePair<string, int>(dish, Amount(registry, dish)));
            // most first for the panel; equal amounts keep the spec's order (the same order the festival takes them in)
            var sorted = stock.Dishes.Select((d, i) => new { d, i }).OrderByDescending(x => x.d.Value).ThenBy(x => x.i).Select(x => x.d).ToList();
            stock.Dishes.Clear();
            stock.Dishes.AddRange(sorted);
            return stock;
        }

        /// <summary>Takes the festival's goods out of the district's stores: the lanterns, DishAmount of each of the
        /// DishKinds most plentiful dishes, and the fireworks when grand. Returns what was taken.</summary>
        public static List<GoodAmount> Take(DistrictCenter district, PandabornFestivalSpec spec, FestivalStock stock, bool grand)
        {
            var taken = new List<GoodAmount>();
            var registry = district.GetComponent<DistrictInventoryRegistry>();
            taken.Add(new GoodAmount(spec.LanternGoodId, Take(registry, spec.LanternGoodId, stock.LanternsNeeded)));
            foreach (string dish in FestivalRules.PickDishes(stock.Dishes, stock.DishKinds, stock.DishAmount))
                taken.Add(new GoodAmount(dish, Take(registry, dish, stock.DishAmount)));
            if (grand) taken.Add(new GoodAmount(spec.FireworksGoodId, Take(registry, spec.FireworksGoodId, stock.FireworksNeeded)));
            return taken;
        }

        private static int Amount(DistrictInventoryRegistry registry, string goodId)
        {
            if (string.IsNullOrEmpty(goodId)) return 0;
            int sum = 0;
            try
            {
                foreach (var inventory in registry.ActiveInventoriesWithStock(goodId))
                    sum += inventory.UnreservedAmountInStock(goodId);
            }
            catch (KeyNotFoundException) { return 0; }   // a good this game does not know
            return sum;
        }

        private static int Take(DistrictInventoryRegistry registry, string goodId, int amount)
        {
            int left = amount;
            if (string.IsNullOrEmpty(goodId) || left <= 0) return 0;
            var sources = new List<Inventory>();
            try { foreach (var inventory in registry.ActiveInventoriesWithStock(goodId)) sources.Add(inventory); }
            catch (KeyNotFoundException) { return 0; }
            foreach (var inventory in sources.OrderByDescending(i => i.UnreservedAmountInStock(goodId)))
            {
                if (left <= 0) break;
                int n = Math.Min(left, inventory.UnreservedAmountInStock(goodId));
                if (n <= 0) continue;
                inventory.TakeConsumed(new GoodAmount(goodId, n));
                left -= n;
            }
            return amount - left;
        }
    }
}
