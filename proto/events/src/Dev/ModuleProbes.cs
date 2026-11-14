using System;
using System.Linq;
using Newtonsoft.Json.Linq;
using Pandaborn.Festival;
using Pandaborn.Flowering;
using Timberborn.BaseComponentSystem;
using Timberborn.TimeSystem;

namespace Pandaborn.Events.Dev
{
    /// <summary>Everything the probe does with the Festival module. Only called when Pandaborn.Festival is loaded.</summary>
    internal static class FestivalProbe
    {
        private static FestivalService F => FestivalService.Current != null && FestivalService.Current.Active ? FestivalService.Current : null;

        public static void Features(JObject features)
        {
            features["festivalActive"] = F != null;
            features["fireworks"] = F?.FireworksStatus;
            features["dayOff"] = FestivalGoer.InsertionError ?? "ok";
        }

        public static string Do(string what, JObject a, IDayNightCycle clock)
        {
            var f = F;
            switch (what)
            {
                case "resetCycleRule": if (f == null) return "festival off"; f.DevResetCycleRule(); return "ok";
                case "setTradition": if (f == null) return "festival off"; f.DevSetTradition(a["value"]?.Value<int>() ?? 0); return "Tradition " + f.Tradition;
                case "autoCall": if (f == null) return "festival off"; f.SetAutoCall(a["value"]?.Value<bool>() ?? true); return "auto " + f.AutoCall + ", phase " + f.Phase;
                case "callFestival":
                {
                    if (f == null) return "festival off";
                    var square = f.Squares.FirstOrDefault(s => s && s.IsFinished);
                    if (square == null) return "no finished square";
                    var stock = FestivalStock.Count(square.District, f.Spec);
                    string why = f.WhyNot(square, stock);
                    bool ok = f.Call(square, auto: false);
                    return (ok ? "called at hour " + clock.HoursPassedToday.ToString("0.0") + " for day " + f.FestivalDay + (f.Grand ? " (grand)" : "") : "refused: " + why)
                           + "; stock lanterns " + stock.Lanterns + ", dishes " + string.Join(" ", stock.Dishes.Select(d => d.Key + "=" + d.Value)) + ", fireworks " + stock.Fireworks;
                }
                default: return null;
            }
        }

        public static void Sample(JObject s)
        {
            var f = F;
            if (f == null) { s["festival"] = "inactive"; return; }
            var goers = f.Goers.Where(g => g).ToList();
            var doing = new JObject();
            foreach (var g in goers)
            {
                string d = f.IsHoliday && !string.IsNullOrEmpty(g.Doing) ? g.Doing : "-";
                doing[d] = (doing[d]?.Value<int>() ?? 0) + 1;
            }
            var festive = goers.Select(g => g.NeedPoints(f.Spec.FestiveNeedId)).Where(p => p >= 0f).ToList();
            var grand = goers.Select(g => g.NeedPoints(f.Spec.GrandNeedId)).Where(p => p >= 0f).ToList();
            s["festival"] = new JObject
            {
                ["phase"] = f.Phase.ToString(),
                ["festivalDay"] = f.FestivalDay,
                ["holiday"] = f.IsHoliday,
                ["show"] = f.IsShowTime,
                ["grand"] = f.Grand,
                ["auto"] = f.AutoCall,
                ["tradition"] = f.Tradition,
                ["lanterns"] = f.LanternsLaunched,
                ["bursts"] = f.BurstsLaunched,
                ["sounds"] = FestivalSounds.Played,
                ["goers"] = goers.Count,
                ["attended"] = goers.Count(g => f.HasAttended(g)),
                ["festiveAvg"] = festive.Count > 0 ? Math.Round(festive.Average(), 3) : -1,
                ["festiveMin"] = festive.Count > 0 ? Math.Round(festive.Min(), 3) : -1,
                ["grandAvg"] = grand.Count > 0 ? Math.Round(grand.Average(), 3) : -1,
                ["doing"] = doing,
                ["keepWorking"] = goers.Count(g => g.KeepsWorking),
                ["lockedByTradition"] = TraditionToolLocker.LockedCount,
                ["panel"] = FestivalSquareFragment.ShownText
            };
        }

        public static void Panels(JObject entry) => entry["festivalPanel"] = FestivalSquareFragment.ShownText;

        public static BaseComponent FindTarget(string what)
        {
            var f = F;
            if (f == null) return null;
            if (what == "square") return f.Squares.FirstOrDefault(s => s);
            if (what == "colonist")
                return (BaseComponent)f.Goers.FirstOrDefault(g => g && g.Doing.StartsWith("at the square", StringComparison.Ordinal)) ?? f.Goers.FirstOrDefault(g => g);
            return null;
        }
    }

    /// <summary>Everything the probe does with the Flowering module. Only called when Pandaborn.Flowering is loaded.</summary>
    internal static class FloweringProbe
    {
        private static FloweringService F => FloweringService.Current != null && FloweringService.Current.Active ? FloweringService.Current : null;

        public static void Features(JObject features)
        {
            features["floweringActive"] = F != null;
            features["growthHold"] = GrowthHold.Available ? "ok" : GrowthHold.Unavailable;
        }

        public static string Do(string what, JObject a, EventsProbe probe)
        {
            var f = F;
            switch (what)
            {
                case "announce": if (f == null) return "flowering off"; f.DevAnnounce(); return f.Phase + " " + f.Species;
                case "flowerNow": if (f == null) return "flowering off"; f.DevFlowerNow(); return f.Phase + " " + f.Species + "; twins " + f.TwinsMade + ", young died " + f.YoungKilled;
                case "setSetting": if (f == null) return "flowering off"; f.SetSetting((string)a["value"]); return f.Setting + ", next " + f.NextCycle;
                default: return null;
            }
        }

        public static void Sample(JObject s)
        {
            var f = F;
            if (f == null) { s["flowering"] = "inactive"; return; }
            var plants = f.Plants.Where(p => p).ToList();
            var twins = f.InFlower.Where(t => t).ToList();
            s["flowering"] = new JObject
            {
                ["setting"] = f.Setting,
                ["phase"] = f.Phase.ToString(),
                ["species"] = f.Species,
                ["nextCycle"] = f.NextCycle,
                ["twinsAlive"] = twins.Count(t => !t.IsDead),
                ["twinsDead"] = twins.Count(t => t.IsDead),
                ["seedOnPlants"] = twins.Sum(t => t.SeedLeft),
                ["seedCut"] = f.SeedCut,
                ["held"] = f.HeldNow,
                ["young"] = new JArray(plants.Where(p => !p.IsGrown && !p.IsDead).Take(8)
                                             .Select(p => (object)(p.Species + " " + p.Growable.GrowthProgress.ToString("0.000"))).ToArray()),
                ["indicator"] = FloweringIndicator.ShownText,
                ["plantPanel"] = FloweringPlantFragment.ShownText
            };
        }

        public static void Panels(JObject entry) => entry["plantPanel"] = FloweringPlantFragment.ShownText;

        public static BaseComponent FindTarget(string what)
        {
            var f = F;
            if (f == null) return null;
            if (what == "inflower") return f.InFlower.FirstOrDefault(t => t && !t.IsDead);
            if (what.StartsWith("plant:", StringComparison.Ordinal))
            {
                string t = what.Substring(6);
                return f.Plants.Where(p => p && p.Species == t).OrderBy(p => p.IsGrown ? 1 : 0).FirstOrDefault();
            }
            return null;
        }
    }
}
