using System;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;
using Pandaborn.Festival;
using Pandaborn.Flowering;
using Timberborn.BaseComponentSystem;
using Timberborn.TimeSystem;

namespace Pandaborn.Events.Dev
{
    // These two classes are the only probe code that names Festival or Flowering types. They are written WITHOUT lambdas,
    // LINQ or closures: the compiler would put module types in the fields of generated classes, and the game's
    // ModCodeStarter calls GetTypes() on this DLL at startup, which then fails (and stops every mod) when a module is forced
    // off and its assembly is not loaded (run events-backon-1). Method bodies are only compiled when called, and they are
    // only called when the module's assembly is loaded.

    /// <summary>Everything the probe does with the Festival module. Only called when Pandaborn.Festival is loaded.</summary>
    internal static class FestivalProbe
    {
        private static FestivalService F => FestivalService.Current != null && FestivalService.Current.Active ? FestivalService.Current : null;

        public static void Features(JObject features)
        {
            var f = F;
            features["festivalActive"] = f != null;
            features["fireworks"] = f != null ? f.FireworksStatus : null;
            features["dayOff"] = FestivalGoer.InsertionError ?? "ok";
        }

        private static FestivalSquare FirstSquare(FestivalService f, bool finished)
        {
            foreach (var s in f.Squares)
                if (s && (!finished || s.IsFinished)) return s;
            return null;
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
                    var square = FirstSquare(f, true);
                    if (square == null) return "no finished square";
                    var stock = FestivalStock.Count(square.District, f.Spec);
                    string why = f.WhyNot(square, stock);
                    bool ok = f.Call(square, auto: false);
                    var dishes = new List<string>();
                    foreach (var d in stock.Dishes) dishes.Add(d.Key + "=" + d.Value);
                    return (ok ? "called at hour " + clock.HoursPassedToday.ToString("0.0") + " for day " + f.FestivalDay + (f.Grand ? " (grand)" : "") : "refused: " + why)
                           + "; stock lanterns " + stock.Lanterns + ", dishes " + string.Join(" ", dishes) + ", fireworks " + stock.Fireworks;
                }
                default: return null;
            }
        }

        public static void Sample(JObject s)
        {
            var f = F;
            if (f == null) { s["festival"] = "inactive"; return; }
            var doing = new JObject();
            int goers = 0, attended = 0, keep = 0, festiveN = 0, grandN = 0;
            float festiveSum = 0f, festiveMin = 9f, grandSum = 0f;
            foreach (var g in f.Goers)
            {
                if (!g) continue;
                goers++;
                string d = f.IsHoliday && !string.IsNullOrEmpty(g.Doing) ? g.Doing : "-";
                doing[d] = (doing[d]?.Value<int>() ?? 0) + 1;
                if (f.HasAttended(g)) attended++;
                if (g.KeepsWorking) keep++;
                float p = g.NeedPoints(f.Spec.FestiveNeedId);
                if (p >= 0f) { festiveN++; festiveSum += p; if (p < festiveMin) festiveMin = p; }
                float q = g.NeedPoints(f.Spec.GrandNeedId);
                if (q >= 0f) { grandN++; grandSum += q; }
            }
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
                ["goers"] = goers,
                ["attended"] = attended,
                ["festiveAvg"] = festiveN > 0 ? Math.Round(festiveSum / festiveN, 3) : -1,
                ["festiveMin"] = festiveN > 0 ? Math.Round(festiveMin, 3) : -1,
                ["grandAvg"] = grandN > 0 ? Math.Round(grandSum / grandN, 3) : -1,
                ["doing"] = doing,
                ["onSquareSlots"] = OnSlots(f),
                ["keepWorking"] = keep,
                ["lockedByTradition"] = TraditionToolLocker.LockedCount,
                ["panel"] = FestivalSquareFragment.ShownText
            };
        }

        /// <summary>Colonists inside each square (on its dance slots) / its capacity.</summary>
        private static string OnSlots(FestivalService f)
        {
            string text = "";
            for (int i = 0; i < f.Squares.Count; i++)
            {
                var e = f.Squares[i] ? f.Squares[i].Enterable : null;
                text += (text.Length > 0 ? ", " : "") + (e ? e.NumberOfEnterersInside + "/" + e.Capacity : "no slots");
            }
            return text;
        }

        public static void Panels(JObject entry) => entry["festivalPanel"] = FestivalSquareFragment.ShownText;

        public static BaseComponent FindTarget(string what)
        {
            var f = F;
            if (f == null) return null;
            if (what == "square") return FirstSquare(f, false);
            if (what == "colonist")
            {
                FestivalGoer any = null;
                foreach (var g in f.Goers)
                {
                    if (!g) continue;
                    if (any == null) any = g;
                    if (g.Doing.StartsWith("at the square", StringComparison.Ordinal)) return g;
                }
                return any;
            }
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
            int alive = 0, dead = 0, seed = 0;
            foreach (var t in f.InFlower)
            {
                if (!t) continue;
                if (t.IsDead) dead++; else alive++;
                seed += t.SeedLeft;
            }
            var young = new JArray();
            foreach (var p in f.Plants)
            {
                if (!p || p.IsGrown || p.IsDead || young.Count >= 8) continue;
                young.Add(p.Species + " " + p.Growable.GrowthProgress.ToString("0.000"));
            }
            s["flowering"] = new JObject
            {
                ["setting"] = f.Setting,
                ["phase"] = f.Phase.ToString(),
                ["species"] = f.Species,
                ["nextCycle"] = f.NextCycle,
                ["twinsAlive"] = alive,
                ["twinsDead"] = dead,
                ["seedOnPlants"] = seed,
                ["seedCut"] = f.SeedCut,
                ["held"] = f.HeldNow,
                ["young"] = young,
                ["buds"] = Buds(f),
                ["indicator"] = FloweringIndicator.ShownText,
                ["plantPanel"] = FloweringPlantFragment.ShownText
            };
        }

        /// <summary>What the bud switch sees on the first grown plant that paints buds: each renderer under Mature, its
        /// material and shader, _EnableDetail, and the detail textures the material carries.</summary>
        private static JArray Buds(FloweringService f)
        {
            var list = new JArray();
            foreach (var p in f.Plants)
            {
                if (!p || p.Spec == null || !p.Spec.BudsUseDetail || !p.IsGrown || p.IsDead) continue;
                foreach (var t in p.GameObject.GetComponentsInChildren<UnityEngine.Transform>(true))
                {
                    if (t.name != "Mature") continue;
                    foreach (var r in t.GetComponentsInChildren<UnityEngine.Renderer>(true))
                    {
                        var m = r.sharedMaterial;
                        if (m == null) { list.Add(r.name + ": no material"); continue; }
                        string line = r.name + (r.gameObject.activeInHierarchy ? " (active)" : " (inactive)") + ": " + m.name + " / " + (m.shader != null ? m.shader.name : "-");
                        line += "; _EnableDetail " + (m.HasProperty("_EnableDetail") ? m.GetFloat("_EnableDetail").ToString("0") : "absent");
                        string[] props = { "_DetailAlbedoMap", "_DetailMap", "_DetailAlbedoMap2", "_DetailAlbedoMap3" };
                        for (int i = 0; i < props.Length; i++)
                        {
                            if (!m.HasProperty(props[i])) continue;
                            var tex = m.GetTexture(props[i]);
                            line += "; " + props[i] + " " + (tex != null ? tex.name : "none");
                        }
                        string[] kws = m.shaderKeywords;
                        if (kws != null && kws.Length > 0) line += "; keywords " + string.Join(" ", kws);
                        list.Add(line);
                    }
                }
                break;
            }
            return list;
        }

        public static void Panels(JObject entry) => entry["plantPanel"] = FloweringPlantFragment.ShownText;

        public static BaseComponent FindTarget(string what)
        {
            var f = F;
            if (f == null) return null;
            if (what == "inflower")
            {
                foreach (var t in f.InFlower) if (t && !t.IsDead) return t;
                return null;
            }
            if (what.StartsWith("plant:", StringComparison.Ordinal))
            {
                string name = what.Substring(6);
                FloweringPlant grown = null;
                foreach (var p in f.Plants)
                {
                    if (!p || p.Species != name) continue;
                    if (!p.IsGrown) return p;
                    if (grown == null) grown = p;
                }
                return grown;
            }
            return null;
        }
    }
}
