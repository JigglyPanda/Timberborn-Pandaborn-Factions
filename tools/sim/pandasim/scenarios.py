"""Every scenario behind docs/tech/balance.md. Each function returns Markdown; run.py prints and saves it."""
import math
import random
import statistics
from dataclasses import replace

from . import vanilla as V
from . import mech as M
from . import jobs as J
from . import needs as N
from . import colony as C
from . import openings as O
from . import popsim as P
from . import stats as S


def table(rows, cols=None, fmt=None):
    cols = cols or list(rows[0].keys())
    fmt = fmt or {}

    def f(c, v):
        if c in fmt:
            return fmt[c](v)
        if isinstance(v, float):
            return f"{v:.2f}" if abs(v) < 10 else f"{v:.0f}"
        return str(v)
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join(f(c, r.get(c, "")) for c in cols) + " |")
    return "\n".join(out)


FT = M.FOLKTAIL
IP = S.INKPAW
RT = S.RINGTAIL


def basket(ctx, plank="Plank", weights=None):
    """Output per shift of one worker in each job type (units of that job's product)."""
    weights = weights or {}
    return {
        "Workshop, with haulers": J.workshop_steady(V.RECIPES["Bread"], ctx, haulers=True)["output"],
        "Workshop, self-supplied": J.workshop_steady(V.RECIPES["WheatFlour"], ctx)["output"],
        "Farmer": J.farmer_day(ctx, V.PLANTS["Carrot"])["units"],
        "Gatherer": J.gatherer_day(ctx, 0.8, 3),
        "Woodcutter": J.woodcutter_day(ctx, 1.5, 2),
        "Builder": J.builder_units_per_day(ctx, {"Log": .4, plank: .45, "Gear": .15}, weights=weights),
        "Hauler": J.hauler_day(ctx, 1),
        "Water pump": J.workshop_steady(V.RECIPES["Water"], ctx, d_out=4)["output"],
    }


# =====================================================================================================================
def calibrate():
    c = M.Ctx(FT, 16, 0, commute=0)
    rows = []
    rows.append(dict(item="Hauler, food / water / logs per day at 20 tiles", reference="386 / 193 / 55",
                     model=" / ".join(f"{J.hauler_day(c, w):.0f}" for w in (1, 2, 6))))
    b = J.build_hours(V.FT_BUILDINGS["Bakery"], c, 20)
    rows.append(dict(item="Bakery: builder trips, walking h, building h (20 tiles)", reference="15, ~17, 2",
                     model=f"{b['trips']}, {b['walk_h']:.1f}, {b['build_h']:.0f}"))
    up = {r: J.workshop_steady(V.RECIPES[r], c, d_in=20, d_out=20) for r in ("Plank", "Bread", "MetalBlock")}
    rows.append(dict(item="Uptime without haulers: lumber mill, bakery, smelter (20 tiles)",
                     reference="59%, 73%, <45%",
                     model=", ".join(f"{up[r]['uptime']:.0%}" for r in up)))
    cf = J.farmer_day(c, V.PLANTS["Carrot"])
    wf = J.farmer_day(c, V.PLANTS["Wheat"])
    per_beaver_carrot = cf["tiles"] / (cf["units"] / V.FOOD_PER_DAY)
    per_beaver_wheat = wf["tiles"] / (wf["units"] * 5 / V.FOOD_PER_DAY)
    rows.append(dict(item="Carrot tiles per beaver; wheat tiles per beaver (as bread)", reference="3.6; 1.8",
                     model=f"{per_beaver_carrot:.1f}; {per_beaver_wheat:.1f}"))
    rows.append(dict(item="Wheat tiles one farmer keeps", reference="~90", model=f"{wf['tiles']:.0f}"))
    pump = J.workshop_steady(V.RECIPES["Water"], c, d_out=4)["output"]
    rows.append(dict(item="Beavers per pump worker (tank next door)", reference="~20 (23 before walking)",
                     model=f"{pump / V.WATER_PER_DAY:.0f}"))
    # opening runway
    cfg = O.folktails()
    s = C.Opening(cfg, days=14).run()
    no_farm = O.folktails()
    no_farm["build_order"] = [p for p in no_farm["build_order"] if p["name"] != "Efficient Farmhouse"]
    s2 = C.Opening(no_farm, days=10).run()
    no_pump = O.folktails()
    no_pump["build_order"] = [p for p in no_pump["build_order"] if p["name"] != "Water Pump"]
    s3 = C.Opening(no_pump, days=3).run()
    rows.append(dict(item="Normal start, no farm: first colonist hungry (day)",
                     reference="3.7 d of berries + wild berries", model=f"{s2.first.get('hunger', '-')}"))
    rows.append(dict(item="Normal start, no pump: first critical thirst (day)", reference="1.43",
                     model=f"{s3.first.get('thirst', '-')}"))
    rows.append(dict(item="Normal start, vanilla opening: first carrots; lowest food stock", reference="tight",
                     model=f"day {s.first.get('Carrot')}; {s.min_food:.0f} items"))
    rows.append(dict(item="First Bakery (440 science: gear workshop, gristmill, bakery) with 1 / 2 inventors",
                     reference="mid first cycle to second cycle",
                     model=f"day {440 / 16 + 3:.0f} / day {440 / 32 + 3:.0f} (+ wheat 10 d)"))
    # Folktails working-day optimum
    plan = N.DayPlan(16, [N.LeisureNeed("Campfire", .1, .6, 1), N.LeisureNeed("Terrace", .15, .6, 1),
                          N.LeisureNeed("Agora", .1, .6, 3), N.LeisureNeed("Carousel", .1, .6, 3),
                          N.LeisureNeed("Lido", .15, .6, 1)])
    best = []
    for W in (14, 16, 17, 18, 20):
        st = N.steady(N.simulate(plan, FT, 24 - W, 40))
        out = (W - 0.3) * (1 + M.tier_delta("WorkingSpeed", st["wb"]))
        best.append(f"{W} h: wb {st['wb']:.0f}, output {out:.1f}")
    rows.append(dict(item="Folktails mid game, working day vs output (9 leisure wellbeing)",
                     reference="default 16 is about right", model="; ".join(best)))
    return "### Calibration on vanilla Folktails\n\n" + table(rows, ["item", "reference", "model"])


# =====================================================================================================================
def _opening_row(name, cfg, **kw):
    s = C.Opening(cfg, **kw).run()
    built = {d: max([l["built"] for l in s.log if l["day"] <= d] or [0]) for d in (5, 7, 10, 14)}
    return dict(case=name, first_food=s.first.get("Shoots", s.first.get("Carrot", "-")),
                low_food=round(s.min_food), hungry_h=s.hungry_colonist_hours, deaths=s.deaths,
                d5=built[5], d7=built[7], d10=built[10], d14=built[14], first_poles=s.first.get("poles", "-")), s


def q1_opening():
    out = ["### Q1. The opening\n"]
    rows = []
    for mode in ("Normal", "Hard"):
        rows.append(_opening_row(f"Folktails {mode}", O.folktails(), mode=mode, days=14)[0])
        rows.append(_opening_row(f"Inkpaws {mode}", O.inkpaws(), mode=mode, days=14)[0])
    rows.append(_opening_row("Inkpaws Normal, no steamer", O.inkpaws(steamer=False), days=14)[0])
    rows.append(_opening_row("Inkpaws Normal, lift 14", O.inkpaws(species=replace(IP, lift=14)), days=14)[0])
    out.append("Hour-by-hour opening, 9 adults + 4 children, 30 wild berry bushes, two woodcutters. 'built' = "
               "material units placed by that day.\n")
    out.append(table(rows, ["case", "first_food", "low_food", "hungry_h", "deaths", "first_poles", "d5", "d7", "d10",
                            "d14"]))
    # shoot sweep
    rows = []
    for g, y in [(2, 1), (2, 2), (3, 2), (3, 3), (4, 2), (4, 3)]:
        sh = dict(S.plant_model("PandabornShootBamboo"), grow_d=g, yield_n=y)
        r, s = _opening_row(f"grow {g} d, yield {y}", O.inkpaws(shoot=sh), days=14)
        c = M.Ctx(IP, 16, 5)
        lab = (sh["plant_h"] + sh["harvest_h"]) / c.ws() + 1.5 / c.v_empty() + c.round_trip(6)
        r.update(land=f"{g / y:.2f}", labour=f"{lab / y:.2f}", berries=int(s.eaten.get("Berries", 0)))
        rows.append(r)
    carrot = V.PLANTS["Carrot"]
    c = M.Ctx(FT, 16, 5)
    lab = (carrot.plant_h + carrot.harvest_h) / c.ws() + 1.5 / c.v_empty() + c.round_trip(6)
    rows.append(dict(case="(Folktails carrot: grow 4, yield 3)", land=f"{4 / 3:.2f}", labour=f"{lab / 3:.2f}"))
    out.append("\nShoot bamboo sweep (Inkpaws Normal). land = tile-days per shoot; labour = farmer hours per shoot "
               "(raw, before the steamer doubles it).\n")
    out.append(table(rows, ["case", "first_food", "low_food", "hungry_h", "berries", "land", "labour"]))
    # lift sweep where builders are the limit
    rows = []
    for lift in (14, 16, 18, 20, 24):
        sp = replace(IP, lift=lift)
        c = M.Ctx(sp, 16, 5)
        logs = J.builder_units_per_day(c, {"Log": 1})
        mid = J.builder_units_per_day(c, {"Log": .4, "Plank": .45, "Gear": .15})
        mid2 = J.builder_units_per_day(c, {"Log": .4, "Pole": .45, "Gear": .15}, weights={"Pole": 2})
        oak = J.woodcutter_day(c, 2.0, 8)
        rows.append(dict(lift=lift, log_trip=c.load("Log"), pole_trip=c.load("Plank"), logs_only=logs, mid=mid,
                         mid_pole2=mid2, oak_cutter=oak))
    c = M.Ctx(FT, 16, 5)
    base = dict(logs_only=J.builder_units_per_day(c, {"Log": 1}),
                mid=J.builder_units_per_day(c, {"Log": .4, "Plank": .45, "Gear": .15}),
                oak_cutter=J.woodcutter_day(c, 2.0, 8))
    for r in rows:
        r["logs_only"] = f"{r['logs_only'] / base['logs_only']:.2f}"
        r["mid_pole2"] = f"{r['mid_pole2'] / base['mid']:.2f}"
        r["mid"] = f"{r['mid'] / base['mid']:.2f}"
        r["oak_cutter"] = f"{r['oak_cutter'] / base['oak_cutter']:.2f}"
    out.append("\nCarrier strength where builders, not logs, are the limit (16 h day, x Folktails builder). mid = 40% "
               "logs, 45% planks or poles (weight 3), 15% gears; mid_pole2 = poles of weight 2.\n")
    out.append(table(rows, ["lift", "log_trip", "pole_trip", "logs_only", "mid", "mid_pole2", "oak_cutter"]))
    # more woodcutters: when do builders bind?
    rows = []
    for wc in (2, 4):
        for name, cfg in (("Folktails", O.folktails()), ("Inkpaws", O.inkpaws()),
                          ("Inkpaws lift 14", O.inkpaws(species=replace(IP, lift=14)))):
            cfg["build_order"] = [dict(name="Lumberjack Flag", cost={}, jobs={"woodcutter": 1})] * (wc - 2) + \
                cfg["build_order"]
            cfg["trees"] = dict(cut_h=2.0, logs=8, d=10)
            r, _ = _opening_row(f"{name}, {wc} woodcutters, oak", cfg, days=14)
            rows.append(r)
    out.append("\nOak forest (8 logs a tree) and more woodcutters, so carrying matters:\n")
    out.append(table(rows, ["case", "low_food", "hungry_h", "d5", "d7", "d10", "d14"]))
    return "\n".join(out)


def q1_drought():
    """First droughts: what plants pausing vs dying means for the store; Hard start."""
    out = ["### Q1b. The first droughts (bamboo pauses or dies)\n"]
    rows = []
    sh, cb = S.plant_model("PandabornShootBamboo"), S.plant_model("PandabornCabbage")
    cases = (("Normal", 14, 3), ("Normal", 14, 5), ("Hard", 6, 3), ("Hard", 6, 4), ("Hard", 6, 6))
    for mode, start, length in cases:
        variants = (("Folktails (carrot 2 d)", O.folktails()),
                    ("Inkpaws, proposed (shoots 5 d, cabbage 7 d)", O.inkpaws()),
                    ("Inkpaws, bamboo dies at once (0.25 d)",
                     O.inkpaws(shoot=dict(sh, dry_d=0.25), cabbage=dict(cb, dry_d=0.25))))
        for label, cfg in variants:
            s_ = C.Opening(cfg, mode=mode, days=start + length + 10, drought=(start, length)).run()
            rows.append(dict(case=f"{mode}, drought day {start}, {length} d", colony=label,
                             low_food=round(s_.min_food), hungry_h=s_.hungry_colonist_hours,
                             thirsty_h=s_.thirsty_colonist_hours, deaths=s_.deaths,
                             cause="/".join(f"{k} {v}" for k, v in s_.death_cause.items() if v) or "-"))
    out.append("Hourly opening with a drought (pumps stop a day in; cisterns 15 + 30 + 30; no extra stocking "
               "behaviour). hungry_h / thirsty_h = colonist-hours at or below 0.\n")
    out.append(table(rows, ["case", "colony", "low_food", "hungry_h", "thirsty_h", "deaths", "cause"]))
    n = 18
    out.append(f"\nStore needed for {n} colonists (2.67 food each a day): pausing plants = drought days only: "
               f"3 d -> {n * 2.67 * 3:.0f}, 5 d -> {n * 2.67 * 5:.0f}. Dying plants = drought + replant + growth "
               f"(3 d) + about half a day of replanting: 3 d -> {n * 2.67 * 6.5:.0f}, the review's 290-340.\n")
    rows = []
    for mode in ("Normal", "Hard"):
        rng = random.Random(4)
        draws = [[M.sample_drought(mode, k, rng) for _ in range(4000)] for k in (1, 2, 3, 5)]
        for name, d in (("shoot bamboo", sh["dry_d"]), ("cabbage", cb["dry_d"]),
                        ("timber bamboo", S.plant_model("PandabornTimberBamboo")["dry_d"]), ("FT carrot", 2),
                        ("FT wheat", 0.5), ("blueberry", 9)):
            row = dict(mode=mode, plant=name, DaysToDieDry=d)
            for k, xs in zip((1, 2, 3, 5), draws):
                # dies if the drought outlasts DaysToDieDry x U(0.9, 1.1)
                row[f"drought {k}"] = f"{sum(1 for x in xs if x < d * random.uniform(0.9, 1.1)) / len(xs):.0%}"
            rows.append(row)
    out.append("Share of droughts an unirrigated plant survives, by occurrence:\n")
    out.append(table(rows))
    return "\n".join(out)


# =====================================================================================================================
def q2_bell():
    out = ["### Q2. The afternoon bell (rested bonus)\n"]
    variants = [
        ("Proposed: +33% at 12 h, linear to 0 at 16, x work and walk, multiplicative", IP),
        ("Same curve as a flat AddBonus delta (additive)", replace(IP, multiplicative=False)),
        ("Revision 3: +33% working speed only", None),
    ]
    rows = []
    for wb in (0, 20, 50, 80):
        ft = basket(M.Ctx(FT, 16, wb))
        for name, sp in variants:
            for W in (12, 14):
                if sp is None:
                    # working speed only: bonus on WorkingSpeed, none on walking (lift 14 as in the review)
                    sp2 = replace(FT, rested=lambda h: 1 / 3 if h <= 12 else 0)
                    c = M.Ctx(sp2, W, wb)
                    mv_fix = M.Ctx(FT, W, wb)
                    c.mv = mv_fix.mv
                    r = basket(c)
                else:
                    r = basket(M.Ctx(replace(sp, lift=14), W, wb))
                row = dict(wellbeing=wb, variant=name, hours=W)
                for k in ft:
                    row[k] = f"{r[k] / ft[k]:.2f}"
                rows.append(row)
    out.append("Output per worker against a Folktails worker on 16 h at the same wellbeing (lift 14 in all rows, "
               "so only the bonus differs).\n")
    out.append(table(rows))
    # curve table
    rows = [dict(hours=h, bonus=f"+{S.inkpaw_bonus(h):.0%}", effective_hours=f"{h * (1 + S.inkpaw_bonus(h)):.1f}",
                 flat_curve=f"+{M.rested_bonus_flat(h):.0%}") for h in (8, 10, 11, 12, 13, 14, 15, 16, 18)]
    out.append("\nThe curve. effective hours = hours x (1 + bonus); 16 means 'as much as a 16-hour beaver'.\n")
    out.append(table(rows))
    # rituals
    out.append("\n" + rituals())
    out.append("\n" + bell_balance())
    return "\n".join(out)


RITUALS = [
    N.LeisureNeed("Nap (daily)", 0.6, 0.6, 2, importance=1.2, walk_tiles=10, min_visit=0.5),
    N.LeisureNeed("Teahouse", 0.15, 0.6, 2, walk_tiles=15),
    N.LeisureNeed("Play", 0.2, 0.6, 2, walk_tiles=15),
    N.LeisureNeed("Cub-watching", 0.2, 0.6, 3, walk_tiles=15),
    N.LeisureNeed("Soak", 0.2, 0.6, 3, walk_tiles=20),
    N.LeisureNeed("Contemplation", 0.12, 0.6, 2, walk_tiles=15),
    N.LeisureNeed("Performance", 0.12, 0.6, 5, walk_tiles=20),
    N.LeisureNeed("Campfire", 0.1, 0.6, 1, walk_tiles=10),
]


def rituals():
    out = ["#### Rituals and leisure time\n"]
    rows = []
    for W in (10, 12, 13, 14, 15, 16, 18):
        res = N.simulate(N.DayPlan(0, RITUALS), IP, 24 - W, 40)
        st = N.steady(res)
        held = sum(1 for k, v in st["favourable"].items() if v > 0.95)
        rows.append(dict(hours=W, leisure_h=st["leisure"], used_h=st["leisure"] - st["idle"], idle_h=st["idle"],
                         rituals_held=f"{held}/{len(RITUALS)}", ritual_wellbeing=st["wb"],
                         nap_h=st["hours"].get("Nap (daily)", 0)))
    out.append("All eight leisure needs built; one representative Inkpaw. Tea is drunk on ordinary drinking trips, so "
               "it costs no leisure time.\n")
    out.append(table(rows))
    # seats per 100 colonists
    res = N.steady(N.simulate(N.DayPlan(0, RITUALS), IP, 12, 40))
    rows = []
    caps = {"Nap (daily)": ("Nap Platform", 6), "Teahouse": ("Teahouse", 12), "Play": ("Slide and Swing", 8),
            "Cub-watching": ("Kindergarten", 12), "Soak": ("Hot Spring Bath", 8), "Contemplation": ("Ink Studio", 4),
            "Performance": ("Opera Stage", 20), "Campfire": ("Campfire", 5)}
    window_i = 6.0     # usable Inkpaw hours after the bell and food, before bed (12 h bell)
    window_r = 5.0     # Ringtail morning after day sleep
    for k, h in res["hours"].items():
        b, seats = caps[k]
        seat_hours = 100 * h
        n_alone = seat_hours / (window_i * seats)
        n_shared = seat_hours / ((window_i + window_r) * seats)
        rows.append(dict(need=k, building=b, seats=seats, hours_per_colonist_day=h,
                         buildings_per_100=f"{n_alone:.1f}", with_ringtail_mornings=f"{n_shared:.1f}"))
    out.append("\nBuildings per 100 colonists at a 12-hour bell (seat-hours needed / usable window x seats). "
               "The second column assumes 30% Ringtails who use the same buildings in their morning.\n")
    out.append(table(rows))
    return "\n".join(out)


def bell_balance():
    """Colony output against the bell, for mixes of Inkpaws and Ringtails, including the wellbeing that rituals add
    or lose (base wellbeing 15 from food, decorations and basics, plus up to 20 from the eight leisure needs)."""
    out = ["#### Is 12/12 the balance point?\n"]
    ritual_i, ritual_r = {}, {}
    for bell in (10, 12, 13, 14, 16, 18):
        ritual_i[bell] = N.steady(N.simulate(N.DayPlan(0, RITUALS), IP, 24 - bell, 40))["wb"]
        # Ringtails are off duty from dawn to the bell: a day's sleep plus the morning
        ritual_r[bell] = N.steady(N.simulate(N.DayPlan(0, RITUALS), RT, bell, 40))["wb"]
    ref = 1 + M.tier_delta("WorkingSpeed", 15 + 20)
    rows = []
    for share in (0.0, 0.25, 0.4):
        row = dict(ringtail_share=f"{share:.0%}")
        for bell in (10, 12, 13, 14, 16, 18):
            wi = (1 + M.tier_delta("WorkingSpeed", 15 + ritual_i[bell])) / ref
            wr = (1 + M.tier_delta("WorkingSpeed", 15 + ritual_r[bell])) / ref
            i = (1 - share) * bell * (1 + S.inkpaw_bonus(bell)) * wi
            r_h = 24 - bell
            r = share * r_h * (1 + S.inkpaw_bonus(r_h)) * wr
            row[f"bell {bell}"] = f"{(i + r) / 16:.2f}"
        rows.append(row)
    rows.append(dict(ringtail_share="(Inkpaw ritual wellbeing)", **{f"bell {b}": f"{ritual_i[b]:.0f}" for b in ritual_i}))
    rows.append(dict(ringtail_share="(Ringtail ritual wellbeing)", **{f"bell {b}": f"{ritual_r[b]:.0f}" for b in ritual_r}))
    out.append("Colony work output per colonist, in 'beaver 16-hour days at wellbeing 35' (Ringtails at lift 14 "
               "equal Inkpaws per hour in their jobs, Q5). Leisure needs are re-simulated at each bell.\n")
    out.append(table(rows))
    return "\n".join(out)


# =====================================================================================================================
def chain_costs(ctx):
    """Per unit of each food: land (tile-days), labour (worker hours), from the job maths."""
    ws = ctx.ws()

    def crop(plant_h, harvest_h, yield_n, grow_d, d=6):
        per_tile = plant_h / ws + harvest_h / ws + 1.5 / ctx.v_empty() + ctx.round_trip(d)
        return grow_d / yield_n, per_tile / yield_n

    def gather(pick_h, n, d=10):
        return (pick_h / ws + ctx.round_trip(d)) / n

    def shop(cycle_h, ratio, uptime=0.75, fuel_every=10):
        per = cycle_h / ws / uptime / ratio
        if fuel_every:
            per += 1.0 / fuel_every / ratio * 1.0          # a log per N cycles, ~1 h of woodcutting per log
        return per

    def pm(pid, **kw):
        m = S.plant_model(pid)
        return crop(m["plant_h"], m["harvest_h"], m["yield_n"], m["grow_d"], **kw)
    shoots = pm("PandabornShootBamboo")
    cabbage = pm("PandabornCabbage")
    rice = pm("PandabornRice", d=8)
    pepper = pm("PandabornSichuanPepper")
    carrot = crop(0.2, 1.2, 3, 4)
    wheat = crop(0.2, 1.2, 3, 10)
    potato = crop(0.2, 1.2, 1, 6)
    pers_land = 6 / 3                                        # tile-days per persimmon (orchard, fruit every 6 d)
    pers_lab = gather(1.0, 3)
    tm = S.plant_model("PandabornTimberBamboo")
    mush_land = tm["mushroom_d"] / tm["mushrooms"]
    mush_lab = gather(tm["pick_h"], tm["mushrooms"], d=12)
    leaf_land = 3 / 3
    leaf_lab = gather(0.6, 3, d=8)
    rows = [
        dict(food="Berries (wild)", dish=0, land=4.0, labour=gather(0.8, 3, d=12), buildings="Gatherer Flag"),
        dict(food="Bamboo shoots", dish=0, land=shoots[0], labour=shoots[1], buildings="Farmstead"),
        dict(food="Cabbage", dish=1, land=cabbage[0], labour=cabbage[1], buildings="Farmstead"),
        dict(food="Persimmons", dish=1, land=pers_land, labour=pers_lab, buildings="Forester, Gatherer"),
        dict(food="Bamboo mushrooms", dish=1, land=mush_land, labour=mush_lab, buildings="Forester, Gatherer"),
        dict(food="Steamed shoots", dish=1, land=shoots[0] / 2, labour=shoots[1] / 2 + shop(0.5, 2),
             buildings="+ Steamer"),
        dict(food="Pickles", dish=2, land=cabbage[0] / 3, labour=cabbage[1] / 3 + shop(1.0, 3, fuel_every=0),
             buildings="+ Pickle Yard"),
        dict(food="Steamed rice", dish=2, land=rice[0] / 4, labour=rice[1] / 4 + shop(1.0, 4),
             buildings="Paddy House, Steamer"),
        dict(food="Sweet rice balls", dish=2, land=(rice[0] + pers_land) / 5,
             labour=(rice[1] + pers_lab) / 5 + shop(0.5, 1, fuel_every=0) / 5 + shop(1.0, 5),
             buildings="+ Trip-Hammer Mill, Kitchen"),
        dict(food="Hot pot", dish=3, land=(cabbage[0] + pepper[0] + mush_land) / 8,
             labour=(cabbage[1] + pepper[1] + mush_lab) / 8 + shop(1.5, 8), buildings="+ Hot Pot Hall"),
        dict(food="Tea (drink, per cup)", dish=2, land=leaf_land / 3, labour=leaf_lab / 3 + shop(0.75, 3, fuel_every=0),
             buildings="Tea Roastery (dry ground)"),
        dict(food="FT Carrot", dish=1, land=carrot[0], labour=carrot[1], buildings="Farmhouse"),
        dict(food="FT Grilled potato", dish=2, land=potato[0] / 4, labour=potato[1] / 4 + shop(0.52, 4),
             buildings="Farmhouse, Grill"),
        dict(food="FT Bread", dish=2, land=wheat[0] / 5,
             labour=wheat[1] / 5 + shop(0.5, 1, fuel_every=0) / 5 + shop(1.0, 5), buildings="Gristmill, Bakery"),
    ]
    return rows


def q3_food():
    out = ["### Q3. Food ladder\n"]
    c = M.Ctx(IP, 16, 20)
    rows = chain_costs(c)
    for r in rows:
        r["staple_land"] = r["land"] * V.FOOD_PER_DAY
        r["staple_labour"] = r["labour"] * V.FOOD_PER_DAY
        r["labour_per_wb_per_100"] = (25 * r["labour"] / r["dish"]) if r["dish"] else None
    out.append("Per unit at wellbeing 20, 16-hour day. staple_* = per colonist per day if eaten as the only food; "
               "labour_per_wb_per_100 = worker-hours a day to keep +1 wellbeing for 100 colonists (25 units a day "
               "keep a dish need, 0.2 a unit against 0.05 a day).\n")
    out.append(table(rows, ["food", "dish", "land", "labour", "staple_land", "staple_labour",
                            "labour_per_wb_per_100", "buildings"],
                     fmt={"labour_per_wb_per_100": lambda v: "-" if v is None else f"{v:.1f}",
                          "land": lambda v: f"{v:.2f}", "labour": lambda v: f"{v:.2f}",
                          "staple_land": lambda v: f"{v:.1f}", "staple_labour": lambda v: f"{v:.2f}"}))
    # unlock order and science
    order = [("Shoots, cabbage", "Farmstead", 0), ("Steamed shoots", "Steamer", 40), ("Persimmons", "Forester", 0),
             ("Pickles", "Pickle Yard", 120), ("Steamed rice", "Paddy House", 150), ("Tea", "Tea Roastery", 250),
             ("Sweet rice balls", "Trip-Hammer Mill + Kitchen", 500), ("Mushrooms", "timber grove + Gatherer", 0),
             ("Hot pot", "Hot Pot Hall", 800), ("Seed cakes", "a Flowering + Kitchen", 0)]
    total = 0
    rows = []
    for food, b, sci in order:
        total += sci
        rows.append(dict(step=food, needs=b, science=sci, cumulative=total,
                         days_two_inventors=f"{total / 32:.0f}"))
    out.append("\nUnlock order (science; days of two inventors at 16 SP a day each, wellbeing 0):\n")
    out.append(table(rows))
    return "\n".join(out)


# =====================================================================================================================
def q4_water():
    out = ["### Q4. Water\n"]
    rows = []
    for mode in ("Easy", "Normal", "Hard"):
        rng = random.Random(7)
        m = V.MODES[mode]
        for occ in (1, 2, 3, 5, 8, 13):
            xs = sorted(M.sample_drought(mode, occ, rng) for _ in range(4000))
            p95 = xs[int(0.95 * len(xs))]
            per = V.WATER_PER_DAY * m.consumption * p95
            rows.append(dict(mode=mode, drought=occ, days_p95=p95, water_per_colonist=f"{per:.0f}",
                             medium_cisterns_per_50=f"{per * 50 / 300:.1f}",
                             with_tea=f"{per * 50 * 0.745 / 300:.1f}"))
    out.append("Drought stores (95th percentile length; 2.12 water a colonist a day; Easy x0.4). with_tea: two cups "
               "of tea a day (Thirst 0.2 each, three cups per water) cut drinking water by 26%.\n")
    out.append(table(rows))
    # tea maths
    rows = []
    for thirst in (0.2, 0.25, 0.33):
        cups = 2.0
        water_drinks = max(0.0, V.THIRST_PER_DAY - cups * thirst) / V.WATER_POINTS
        total = water_drinks + cups / 3
        rows.append(dict(tea_thirst=thirst, cups_a_day=cups, water_a_day=f"{total:.2f}",
                         saving=f"{1 - total / V.WATER_PER_DAY:.0%}", leaves_a_day=f"{cups / 3:.2f}"))
    rows.append(dict(tea_thirst="0.25, need wastable", cups_a_day=2.8, water_a_day=f"{2.8 / 3:.2f}",
                     saving=f"{1 - 2.8 / 3 / V.WATER_PER_DAY:.0%}", leaves_a_day="0.93"))
    out.append("\nTea per colonist (Tea need non-wastable, +0.3 a cup, decay 0.6 a day = 2 cups):\n")
    out.append(table(rows))
    # dew collector
    rows = []
    for per_day, dr in ((6, 2), (3, 1), (2, 0.67)):
        for n in (20, 50):
            need = n * V.WATER_PER_DAY
            rows.append(dict(dew_per_day=per_day, in_drought=dr, colony=n,
                             collectors_for_all_water=f"{need / per_day:.0f}",
                             collectors_for_all_in_drought=f"{need / dr:.0f}",
                             poles_for_all=f"{need / per_day * 15:.0f}",
                             ten_collectors_cover=f"{10 * dr / need:.0%} in drought"))
    out.append("\nDew collector (Pole 15 + Paper 4, 2x2, no workers). A Water Pump worker makes ~45 a day.\n")
    out.append(table(rows))
    # paddies
    c = M.Ctx(IP, 16, 20)
    rice_per_tile = 3 / 8
    tiles = V.FOOD_PER_DAY / (rice_per_tile * 4)
    evap_tile_day = 0.0001 * 1.2 * V.REAL_SECONDS_PER_GAME_HOUR * 24 / V.WATER_GOOD_M3
    flume_tile_day = 0.0001 * 6.5 * V.REAL_SECONDS_PER_GAME_HOUR * 24 / V.WATER_GOOD_M3
    out.append(f"\nPaddy: rice 3 per 8 days, steamed x4 -> {tiles:.1f} paddy tiles per colonist on rice alone "
               f"(bread: 1.8 wheat tiles). Standing water evaporates about {evap_tile_day:.2f} Water a tile a day "
               f"(water.md constants, lake factor 1.2), so a paddy colonist costs about {tiles * evap_tile_day:.2f} "
               f"Water a day on top of drinking. A 1-wide flume loses about {flume_tile_day:.1f} Water a tile a day "
               f"(factor 6.5): a Cistern Tap at 1 Water an hour feeds about {24 / flume_tile_day:.0f} tiles of "
               f"ground flume, whose 1-2 tile moist strip keeps 20-30 bamboo tiles alive; a 6-day drought costs "
               f"{24 * 6} Water, half a Medium Cistern. Evaporation units are the least certain number here.")
    return "\n".join(out)


# =====================================================================================================================
def q5_ringtails():
    out = ["### Q5. Ringtails\n"]
    rows = []
    for bell in (12, 14, 16):
        r_h = 24 - bell
        ci = M.Ctx(IP, bell, 20)
        cr = M.Ctx(RT, r_h, 20)
        cf = M.Ctx(FT, 16, 20)
        mix = {"Log": .4, "Plank": .45, "Gear": .15}
        b_i, b_r, b_f = (J.builder_units_per_day(x, mix) for x in (ci, cr, cf))
        h_i = J.hauler_day(ci, 2)
        h_r = J.hauler_day(cr, 2)
        g_i, g_r = J.gatherer_day(ci, 0.5, 1, d_plant=10), J.gatherer_day(cr, 0.5, 1, d_plant=10)
        sci_r = cr.work_hours() * cr.ws() * 3
        rows.append(dict(bell=bell, ringtail_shift=r_h, builder_R=b_r, builder_I=b_i, builder_FT16=b_f,
                         courier_R_water=h_r, porter_I_water=h_i, forager_R=g_r, forager_I=g_i,
                         star_tower_R_SP=sci_r))
    out.append("Per worker per shift at wellbeing 20. Builder = material units delivered and built; courier/porter = "
               "water units moved at 20 tiles (carry x2); forager = mushrooms (one a stalk, 10 tiles); Star Tower "
               "= science (Observatory rate, 3 SP an hour a worker).\n")
    out.append(table(rows))
    # courier value: Inkpaw workshops self-supplied by day, topped up at night
    rows = []
    ci = M.Ctx(IP, 12, 20)
    for rname, w in (("Plank", None), ("WheatFlour", None), ("Bread", None), ("MetalBlock", None), ("Gear", None)):
        rec = V.RECIPES[rname]
        base = J.workshop_steady(rec, ci, d_in=15, d_out=15)
        cr = M.Ctx(RT, 12, 20)
        night = J.workshop_steady(rec, ci, d_in=15, d_out=15, couriers=True,
                                  courier_load=lambda g: cr.load("", carry_bonus=1.0, weight=V.WEIGHT.get(g, 1)))
        hauled = J.workshop_steady(rec, ci, haulers=True)
        loads = night["courier_loads"]
        courier_h = loads * cr.round_trip(15)
        gain_h = (night["output"] - base["output"]) / (hauled["output"] / (ci.work_hours() * 0.95))
        rows.append(dict(workshop=rname, uptime_alone=f"{base['uptime']:.0%}", with_night_couriers=f"{night['uptime']:.0%}",
                         with_day_porters=f"{hauled['uptime']:.0%}", courier_hours=f"{courier_h:.1f}",
                         inkpaw_hours_gained=f"{gain_h:.1f}",
                         workshops_per_courier=f"{cr.work_hours() / max(courier_h, 0.1):.1f}"))
    out.append("\nNight Courier Post: Inkpaw workshop (12 h) that supplies itself by day, with Ringtail couriers "
               "filling every input and emptying the output overnight (15 tiles).\n")
    out.append(table(rows))
    out.append("\n" + ringtail_mix())
    return "\n".join(out)


def ringtail_mix():
    """Colony output against the Ringtail share, with Ringtail jobs limited to their buildings."""
    out = ["#### Best mix\n"]
    # share of a mid colony's labour in each job (vanilla-like 60-colonist colony, estimated)
    jobs = {"food": .30, "water": .05, "wood and poles": .12, "workshops": .15, "building": .12, "hauling": .10,
            "gathering": .04, "science": .08, "other": .04}
    ringtail_jobs = {"building": 1.35, "hauling": 1.4, "gathering": 1.15, "science": 1.0}  # per-head vs Inkpaw
    rows = []
    for share in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5):
        need = sum(jobs[j] for j in ringtail_jobs)
        r = share
        # Ringtails fill their jobs (each Ringtail does `eff` Inkpaw-equivalents); surplus Ringtails idle
        eq = 0.0
        left = r
        demand = {j: jobs[j] * 1.5 for j in ringtail_jobs}      # night work is worth up to 1.5x the day's share
        for j, eff in sorted(ringtail_jobs.items(), key=lambda kv: -kv[1]):
            use = min(left, demand[j] / eff)
            eq += use * eff
            left -= use
        out_total = (1 - r) + eq
        rows.append(dict(ringtail_share=f"{share:.0%}", inkpaw_equivalents=f"{out_total:.2f}",
                         idle_ringtails=f"{left:.0%}"))
    out.append("Colony output in Inkpaw-worker equivalents per colonist (bell 12; Ringtail jobs: building, hauling, "
               "gathering, science, up to 1.5x their share of a day colony's labour).\n")
    out.append(table(rows))
    return "\n".join(out)


# =====================================================================================================================
def _wb_ramp(day, pop):
    return min(25, 4 + day * 0.25)


def q6_population():
    out = ["### Q6. Population\n"]
    rows = []
    base = P.PopConfig("Folktails", wellbeing=_wb_ramp, food_per_worker_day=20, food_worker_share=0.25)
    ink = P.PopConfig("Inkpaws (vanilla births)", wellbeing=_wb_ramp, food_per_worker_day=20, food_worker_share=0.25)
    ink_r = P.PopConfig("Inkpaws + Ringtails (loft day 18, 1 Ringtail job per 4 Inkpaws)", wellbeing=_wb_ramp,
                        ringtails_arrive=18, ringtail_jobs=lambda d, n: 4 + n // 4, food_per_worker_day=20,
                        food_worker_share=0.25)
    slow = P.PopConfig("Revision-3 slow breeding (chance 0.06, life 70, childhood 8)", wellbeing=_wb_ramp,
                       birth_chance=0.06, lifespan=70, childhood=8, food_per_worker_day=20, food_worker_share=0.25)
    for cfg in (base, ink, ink_r, slow):
        t50, t100 = [], []
        for seed in range(12):
            r = P.run(cfg, days=150, seed=seed)
            t50.append(P.first_day(r["hist"], 50) or 999)
            t100.append(P.first_day(r["hist"], 100) or 999)
        rows.append(dict(case=cfg.name, days_to_50=statistics.median(t50), days_to_100=statistics.median(t100)))
    out.append("Median of 12 runs; homes built as needed by a builder pool (1 + 0.12 beds per adult a day); wellbeing "
               "rising from 4 to 25 by day 84; food not limiting.\n")
    out.append(table(rows))
    # drought death spiral
    rows = []
    for label, kw in (("plants pause (proposed)", dict(plants_die_after=99, food_drought_factor=0.1)),
                      ("plants die after 4 d, 4 d regrow", dict(plants_die_after=4, food_drought_factor=0.1)),
                      ("plants die at once", dict(plants_die_after=0.3, food_drought_factor=0.05))):
        for stock_days in (2, 6):
            cfg = P.PopConfig(label, wellbeing=_wb_ramp, stock_days_target=stock_days, max_population=60,
                              food_per_worker_day=20, food_worker_share=0.25, **kw)
            res = []
            for seed in range(8):
                r = P.run(cfg, days=110, seed=seed, droughts=[(60, 9)])
                h = r["hist"]
                before = h[59]["pop"]
                low = min(x["pop"] for x in h[60:])
                back = next((x["day"] for x in h[70:] if x["pop"] >= before), None)
                res.append((before, low, r["deaths_starve"], (back - 69) if back else 99))
            rows.append(dict(case=label, stock_days=stock_days, pop_before=statistics.median(x[0] for x in res),
                             low=statistics.median(x[1] for x in res),
                             starved=statistics.median(x[2] for x in res),
                             days_to_recover=statistics.median(x[3] for x in res)))
    out.append("\nA 9-day drought at day 60 (Normal's longest) with 2 or 6 days of food in store:\n")
    out.append(table(rows))
    return "\n".join(out)


# =====================================================================================================================
def q7_flowering():
    out = ["### Q7. Great Flowering and the Festival\n"]
    rows = []
    for pop in (40, 80, 150):
        shoot_share = 0.35 if pop < 60 else 0.2
        food_day = pop * V.FOOD_PER_DAY * shoot_share
        # shoots: plants die; replant needs seed cleared first (1 gather each), then 3 days growth
        tiles = food_day * 3 / 2
        c = M.Ctx(IP, 12, 20)
        clear_and_plant = tiles * (0.5 / c.ws() + c.round_trip(6) + 0.2 / c.ws()) / (3 * c.work_hours())
        recovery = 3 + max(1.0, clear_and_plant)
        poles_day = pop * 0.35
        timber_recovery = 5 + max(1.0, clear_and_plant)
        seed = tiles * 3
        season = 15.0
        rows.append(dict(colonists=pop, shoot_share=f"{shoot_share:.0%}", shoot_tiles=f"{tiles:.0f}",
                         food_replant_now=f"{food_day * recovery:.0f}", recovery_days=f"{recovery:.1f}",
                         food_season=f"{food_day * season:.0f}",
                         poles_replant_now=f"{poles_day * timber_recovery:.0f}",
                         poles_season=f"{poles_day * season:.0f}",
                         seed=f"{seed:.0f}", seed_cakes=f"{seed * 4:.0f}",
                         cake_days_for_all=f"{seed * 4 / (pop * 0.25):.0f}"))
    out.append("Shoot flowering: shoots are 35% of food under 60 colonists, 20% above; dead plants are cleared by "
               "gathering their seed (3 each). *_replant_now: replanting allowed at once (growth + clearing); "
               "*_season: that bamboo cannot be replanted for the rest of the temperate season (~15 days), which is "
               "what 'a food season to bridge' needs. Poles at 0.35 a colonist a day. Seed cakes keep the +3 dish "
               "need for everyone for cake_days.\n")
    out.append(table(rows))
    # frequency: cumulative expected
    out.append("\nFrequency: with the first at cycle 6 and then every 5-7 cycles (alternating), a 30-cycle game sees "
               "about 4-5 Flowerings, 2-3 of each bamboo; each costs one temperate season of adjustment.")
    # festival
    sci = 40 + 120 + 150 + 250 + 200 + 300
    out.append(f"\nSmall Festival in cycle 2: science for Steamer, Pickle Yard, Paddy House (three cooked dishes: "
               f"steamed shoots, pickles, steamed rice), Paper Mill, Lantern Workshop, Festival Square = {sci}; two "
               f"inventors at wellbeing 10 (x1.4) make 45 a day, so about day {sci / 45 + 4:.0f}, i.e. the start of "
               f"cycle 2 (cycle 1 = 13-17 temperate + 2-3 drought). 40 lanterns = 40 paper + 20 poles = 40 poles.")
    rows = []
    for fav, decay in ((3, 0.06), (4, 0.06), (4, 0.05), (3, 0.04)):
        days = 1 / decay
        gain = days * fav / 5 * 0.2 / 1.8
        rows.append(dict(festive_wellbeing=fav, decay=decay, lasts_days=f"{days:.0f}",
                         work_days_gained=f"{gain:.2f}", cost_days=1.0))
    out.append("\nFestival payoff at wellbeing ~20 (multiplier 1.8; +1 wellbeing = 0.04 working speed on average "
               "across tier steps):\n")
    out.append(table(rows))
    return "\n".join(out)


# =====================================================================================================================
def material_labour(sp, hours=16, wb=30):
    """Worker-hours to make and deliver one unit of each material (mid/late game, with haulers)."""
    c = M.Ctx(sp, hours, wb)
    ws = c.ws()
    log = 1.0 / (J.woodcutter_day(c, 1.5, 2) / c.work_hours()) + 0.75 / 2 / ws          # cut + replant (pine)
    plank = log + 1.25 / ws / 0.95
    tm = S.plant_model("PandabornTimberBamboo")
    pole = (tm["cut_h"] / ws + c.round_trip(10) * math.ceil(tm["poles"] / c.load("Plank")) + tm["plant_h"] / ws + 0.1) / tm["poles"]
    gear_ft = plank + 3 / ws / 0.95
    gear_ip = pole + 3 / ws / 0.95
    resin = (1.2 / ws + c.round_trip(10)) / 2
    treated = plank + resin + 3 / ws / 0.95
    cured = pole + 0.25 * log + 3 / ws / 0.95
    scrap = 18 / 5 / ws / 10 * 10 + treated / 5      # mine: 10 workers, 18 h -> 5 scrap from 1 treated plank
    metal = 2 * scrap + 2 / ws / 0.95 + log / 5
    paper = pole / 2 + 1.56 / 2 / ws / 0.95
    deliver = {g: c.round_trip(15) / c.load("", weight=w) + 0.05 / ws
               for g, w in (("Log", 6), ("Plank", 3), ("Gear", 3), ("TreatedPlank", 4), ("MetalBlock", 5),
                            ("Paper", 1))}
    return dict(Log=log + deliver["Log"], Plank=plank + deliver["Plank"], PandabornPole=pole + deliver["Plank"],
                Gear=(gear_ft if sp is FT else gear_ip) + deliver["Gear"],
                TreatedPlank=treated + deliver["TreatedPlank"], PandabornCuredPole=cured + deliver["TreatedPlank"],
                MetalBlock=metal + deliver["MetalBlock"], Paper=paper + deliver["Paper"], Dirt=2.0, ScrapMetal=scrap)


def q8_late():
    out = ["### Q8. Late game\n"]
    # worker-days: a Folktails worker-day is 16 h, an Inkpaw worker-day 12 h (same output per day, Q2)
    lf = {k: v / 16 for k, v in material_labour(FT).items()}
    li = {k: v / 12 for k, v in material_labour(IP, hours=12).items()}
    out.append("Worker-DAYS per unit made and delivered (wellbeing 30; Folktails 16 h, Inkpaws 12 h with the bonus; "
               "a worker-day is the comparable unit because both produce the same per day, Q2):\n")
    out.append(table([dict(material=k, Folktails=f"{lf.get(k, 0):.3f}", Inkpaws=f"{li.get(k, 0):.3f}",
                           ratio=f"{li.get(k, 0) / lf.get(k, 1):.2f}")
                      for k in ("Log", "Plank", "PandabornPole", "Gear", "TreatedPlank", "PandabornCuredPole",
                                "MetalBlock", "Paper")]))

    def cost_d(cost, lab):
        return sum(n * lab.get(g, lab.get("Plank")) for g, n in cost.items())
    rows = []
    ft_b = V.FT_BUILDINGS
    wonder_days = V.WONDER_BUILD_HOURS / 2.2 / 16
    pairs = [("Farmer Monument + Brazier of Bonding",
              cost_d(ft_b["FarmerMonument"], lf) + cost_d(ft_b["BrazierOfBonding"], lf), "PandabornMemorialArch"),
             ("Fountain of Joy + Hall of Abundance",
              cost_d(ft_b["FountainOfJoy"], lf) + cost_d(ft_b["HallOfAbundance"], lf), "PandabornGreatSittingPanda"),
             ("Earth Recultivator", cost_d(ft_b["EarthRecultivator"], lf) + wonder_days, "PandabornSkyLantern")]
    for ft_name, ft_d, ip_id in pairs:
        b = next(x for x in S.BUILDINGS if x["id"] == ip_id)
        extra = wonder_days if "Sky" in ip_id else 0
        ip_d = cost_d(b["cost"], li) + extra
        k = (ft_d - extra) / max(1e-9, ip_d - extra)
        rows.append(dict(folktails=ft_name, ft_worker_days=f"{ft_d:.0f}", inkpaws=ip_id,
                         ip_worker_days=f"{ip_d:.0f}", ratio=f"{ip_d / ft_d:.2f}",
                         cost_to_match=", ".join(f"{g} {int(round(n * k, -1))}" for g, n in b["cost"].items())))
    out.append("\nMonuments and the wonder, worker-days of materials (+ wonder build at x2.2 working speed). "
               "cost_to_match scales the listed Inkpaw cost to the Folktails labour:\n")
    out.append(table(rows))
    # oxen vs bots
    rows = []
    bot = M.Ctx(M.BOT, 16, 0)
    bot_full = M.Ctx(replace(M.BOT, fixed_ws=2.7, fixed_mv=1.8), 16, 0)
    ox = M.Ctx(S.OX, 16, 0)
    for name, c, life, upkeep_h in (("FT bot, no supplies (tier 0)", bot, 70, 0.0),
                                    ("FT bot, biofuel + catalyst + punch cards (tier 2)", bot_full, 70, 3.0),
                                    ("Wooden Ox (no needs, tier 0)", ox, 90, 0.0)):
        haul = J.hauler_day(c, 3)
        build = J.builder_units_per_day(c, {"Log": .4, "Plank": .45, "Gear": .15})
        shop = J.workshop_steady(V.RECIPES["Bread"], c, haulers=True)["output"]
        rows.append(dict(unit=name, haul_planks_day=f"{haul:.0f}", build_units_day=f"{build:.0f}",
                         bakery_bread_day=f"{shop:.0f}", life_days=life, upkeep_worker_h_day=upkeep_h))
    out.append("\nBots and oxen, per unit per day (24 h):\n")
    out.append(table(rows))
    ox_cost = cost_d({"PandabornCuredPole": 10, "Gear": 15, "MetalBlock": 2}, li) + 72 / 2.0 / 12
    bot_cost = cost_d({"Plank": 10, "Gear": 15, "MetalBlock": 2}, lf) + V.BOT_WORKER_HOURS_TO_MAKE / 1.8 / 16
    out.append(f"\nMaking one: Folktails bot ~{bot_cost:.1f} worker-days (parts + 126 h of factory work at x1.8); "
               f"Wooden Ox ~{ox_cost:.1f} worker-days (one recipe, 72 h at x2).")
    return "\n".join(out)
