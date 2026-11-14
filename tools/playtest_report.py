"""Turn scripted-colony playtest runs into a one-page verdict and a few charts.

Usage (the venv has matplotlib):
    E:\\PandabornDev\\tools\\venv\\Scripts\\python.exe -I tools/playtest_report.py <run dir> [<run dir> ...] [--out DIR] [--labels a,b]

A run dir is a tools/run_game_test.ps1 output folder whose request had a "playtest" object (src/devharness/Playtest):
it holds playtest/daily.jsonl (one line per dawn), playtest/events.jsonl and playtest/state.json.
Writes <out>/verdict.md (one section per run, then a comparison table) and <out>/*.png. Default out: the first run's
playtest folder when one run is given, else E:\\PandabornDev\\build\\playtest\\report-<labels>.
"""
import argparse
import json
import os
import sys

COOKED = {"GrilledPotato", "Bread", "MaplePastry", "CattailCracker", "GrilledChestnut", "GrilledSpadderdock",
          "PandabornSteamedShoots", "PandabornSteamedRice", "PandabornPickles", "PandabornSweetRiceBalls",
          "PandabornHotPot", "PandabornBambooSeedCakes"}
FOOD_NEEDS = {"Hunger"}
LEISURE_HINTS = ("Campfire", "RooftopTerrace", "Hammock", "Teahouse", "NapPlatform", "Lido", "SlideAndSwing", "Agora",
                 "Kindergarten", "ContemplationSpot", "InkStudio", "DanceHall", "Opera", "MudPit", "HotSpring",
                 "DomedGarden", "Shrub", "Statue", "Lantern", "Bench", "Pinwheel", "Weathervane")
# validated default categorical order (dataviz reference palette, light mode)
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"


def read_jsonl(path):
    out = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return out


def load_run(run_dir):
    pt = os.path.join(run_dir, "playtest")
    daily = read_jsonl(os.path.join(pt, "daily.jsonl"))
    events = read_jsonl(os.path.join(pt, "events.jsonl"))
    state = {}
    if os.path.exists(os.path.join(pt, "state.json")):
        state = json.load(open(os.path.join(pt, "state.json"), encoding="utf-8"))
    request, result = {}, {}
    for name, target in (("request.json", request), ("result.json", result)):
        p = os.path.join(run_dir, name)
        if os.path.exists(p):
            try:
                target.update(json.load(open(p, encoding="utf-8-sig")))
            except Exception:
                pass
    # one record per day number: keep the last (a final partial record replaces nothing unless it is a new day)
    by_day = {}
    for d in daily:
        if d.get("final") and d["day"] in by_day:
            by_day[d["day"]]["_final"] = d
            continue
        by_day[d["day"]] = d
    days = [by_day[k] for k in sorted(by_day)]
    return {"dir": run_dir, "days": days, "events": events, "state": state, "request": request, "result": result,
            "name": state.get("name") or os.path.basename(run_dir.rstrip("\\/"))}


def food_stock(day):
    goods = day.get("goods", {})
    edible = day.get("_edible")
    total = 0
    for g, v in goods.items():
        if edible is not None and g not in edible:
            continue
        total += v[0]
    return total


def edible_goods(run):
    """Goods that feed Hunger: anything a hungry colonist could eat, read from what was consumed while Hunger mattered.
    The telemetry does not carry consumption effects, so use a fixed list of every vanilla and Inkpaws food."""
    return {"Berries", "Carrot", "GrilledPotato", "Bread", "MaplePastry", "CattailCracker", "GrilledChestnut", "Chestnut",
            "GrilledSpadderdock", "Kohlrabi", "Soybean", "Cassava", "Corn", "Eggplant", "Canola",
            "PandabornBambooShoots", "PandabornCabbage", "PandabornPersimmons", "PandabornBambooMushrooms",
            "PandabornSteamedShoots", "PandabornSteamedRice", "PandabornPickles", "PandabornSweetRiceBalls",
            "PandabornHotPot", "PandabornBambooSeedCakes"}


def classify(behavior):
    b = behavior or ""
    if "WaitInsideIdly" in b or b.startswith("Wander") or b == "none":
        return "idle"
    if "NeedBehavior" in b or "Sleep" in b or "Eat" in b:
        return "needs"
    return "work"


def analyse(run):
    days = run["days"]
    edible = edible_goods(run)
    a = {"name": run["name"], "days": len(days)}
    if not days:
        return a
    a["faction"] = run["request"].get("faction") or run["result"].get("activeFaction", {}).get("id")
    a["map"] = run["request"].get("map")
    a["mode"] = run["request"].get("gameMode")
    a["lastDay"] = days[-1]["day"]
    pops = [(d["day"], d["pop"]["total"]) for d in days]
    a["popStart"], a["popEnd"] = pops[0][1], pops[-1][1]
    a["popPeak"] = max(p for _, p in pops)
    a["popMin"] = min(p for _, p in pops)
    for target in (20, 30, 50):
        a["dayPop%d" % target] = next((day for day, p in pops if p >= target), None)
    deaths = [x for d in days for x in d.get("deaths", [])]
    a["deaths"] = len(deaths)
    causes = {}
    for x in deaths:
        cause = ",".join(x.get("needsAtMinimum") or []) or (x.get("message") or "?")
        causes[cause] = causes.get(cause, 0) + 1
    a["deathCauses"] = causes
    a["firstDeathDay"] = deaths[0]["day"] if deaths else None
    a["births"] = sum(d.get("births", 0) for d in days)
    # weather
    hazards, cur = [], None
    for d in days:
        if d["weather"] != "temperate":
            if cur is None or cur["kind"] != d["weather"]:
                cur = {"kind": d["weather"], "start": d["day"], "days": 0, "planned": d.get("hazardDays")}
                hazards.append(cur)
            cur["days"] += 1
        else:
            cur = None
    a["hazards"] = hazards
    # food and water
    for d in days:
        d["_edible"] = edible
    food = [(d["day"], food_stock(d)) for d in days]
    water = [(d["day"], d.get("goods", {}).get("Water", [0, 0, 0, 0, 0])[0]) for d in days]
    a["foodMin"] = min(food[1:] or food, key=lambda x: x[1]) if food else None
    a["waterMin"] = min(water[1:] or water, key=lambda x: x[1]) if water else None
    a["waterCapEnd"] = days[-1].get("goods", {}).get("Water", [0, 0, 0])[2]
    crit = {}
    for d in days:
        for need, v in d.get("needs", {}).items():
            if v[1] > 0:
                crit.setdefault(need, []).append((d["day"], v[1]))
    a["critical"] = {k: {"colonistDays": sum(n for _, n in v), "firstDay": v[0][0], "worstDay": max(v, key=lambda x: x[1])}
                     for k, v in crit.items()}
    wb = [(d["day"], d["wellbeing"]["avg"]) for d in days]
    a["wellbeingEnd"] = wb[-1][1]
    a["wellbeingMax"] = max(w for _, w in wb)
    a["wellbeingByDay"] = {day: w for day, w in wb}
    # first cooked food
    first_cooked = None
    for d in days:
        for g, v in d.get("goods", {}).items():
            if g in COOKED and (v[3] > 0 or v[1] > 0):
                first_cooked = (d["day"], g)
                break
        if first_cooked:
            break
    a["firstCooked"] = first_cooked
    fin = [e for e in run["events"] if e.get("type") == "finished"]
    leisure = [e for e in fin if any(h in (e.get("template") or "") for h in LEISURE_HINTS)]
    a["firstLeisure"] = (round(leisure[0]["day"], 1), leisure[0]["template"]) if leisure else None
    a["buildingsFinished"] = len(fin)
    # jobs and homes
    a["unemployedMaxDays"] = sum(1 for d in days if d["jobs"]["unemployed"] > 0)
    a["homelessDays"] = sum(1 for d in days if d["homes"]["homeless"] > 0)
    a["homelessMax"] = max(d["homes"]["homeless"] for d in days)
    a["unemployedMax"] = max(d["jobs"]["unemployed"] for d in days)
    # workplaces: share of worker-samples working / idle / at needs, summed over the run
    wp = {}
    for d in days:
        for w in d.get("work", []):
            r = wp.setdefault(w["id"], {"template": w.get("template"), "samples": 0, "work": 0, "idle": 0, "needs": 0,
                                        "statuses": {}, "behaviors": {}, "understaffed": 0, "empty": 0})
            r["samples"] += w["samples"]
            r["understaffed"] += w.get("understaffed", 0)
            if w["workerSamples"] == 0:
                r["empty"] += w["samples"]
            for b, n in w.get("behaviors", {}).items():
                r[classify(b)] += n
                r["behaviors"][b] = r["behaviors"].get(b, 0) + n
            for s, n in w.get("statuses", {}).items():
                r["statuses"][s] = r["statuses"].get(s, 0) + n
    a["workplaces"] = wp
    # goods produced but never consumed, consumed but never produced
    prod, cons = {}, {}
    for d in days:
        for g, v in d.get("goods", {}).items():
            prod[g] = prod.get(g, 0) + v[3]
            cons[g] = cons.get(g, 0) + v[4]
    a["produced"] = prod
    a["consumed"] = cons
    a["neverConsumed"] = sorted(g for g in prod if prod[g] > 0 and cons.get(g, 0) == 0)
    # plan steps
    st = run["state"].get("stepStates", [])
    a["stepsFailed"] = [(s["id"], s.get("error")) for s in st if s.get("failed")]
    a["stepsWaiting"] = [(s["id"], s.get("waiting") or s.get("error")) for s in st if s["done"] == 0 and not s.get("failed")]
    secs = [d.get("realSecondsThisDay") for d in days[1:] if d.get("realSecondsThisDay")]
    a["realSecondsPerDay"] = round(sum(secs) / len(secs), 1) if secs else None
    a["speeds"] = sorted({d.get("speed") for d in days})
    return a


# ---------------------------------------------------------------------------------------------------------- charts

def charts(runs, analyses, out, labels):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                         "ytick.color": INK2, "axes.facecolor": SURFACE, "figure.facecolor": SURFACE,
                         "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
                         "grid.linewidth": 0.6, "legend.frameon": False})
    panels = [
        ("Population", lambda d: d["pop"]["total"]),
        ("Food in stock (all edible goods)", lambda d: food_stock(d)),
        ("Water in stock", lambda d: d.get("goods", {}).get("Water", [0])[0]),
        ("Average wellbeing", lambda d: d["wellbeing"]["avg"]),
        ("Colonists critical in hunger or thirst", lambda d: sum(d.get("needs", {}).get(n, [0, 0])[1] for n in ("Hunger", "Thirst"))),
        ("Unemployed adults", lambda d: d["jobs"]["unemployed"]),
        ("Homeless", lambda d: d["homes"]["homeless"]),
        ("Logs in stock", lambda d: d.get("goods", {}).get("Log", [0])[0]),
        ("Planks / poles in stock", lambda d: d.get("goods", {}).get("Plank", [0])[0]),
    ]
    files = []
    fig, axes = plt.subplots(3, 3, figsize=(13, 9.5))
    for ax, (title, fn) in zip(axes.flat, panels):
        for i, run in enumerate(runs):
            days = run["days"]
            if not days:
                continue
            xs = [d["day"] for d in days]
            ys = [fn(d) for d in days]
            ax.plot(xs, ys, color=SERIES[i % len(SERIES)], linewidth=2, label=labels[i])
            # hazard days as a light band (first run's bands only, to keep it readable; per-run bands differ)
            if i == 0 or len(runs) == 1:
                for d in days:
                    if d["weather"] != "temperate":
                        ax.axvspan(d["day"] - 1, d["day"], color="#f0efec" if d["weather"] == "drought" else "#e7e1f7",
                                   zorder=0, linewidth=0)
        ax.set_title(title, color=INK, fontsize=10, loc="left")
        ax.set_xlabel("day")
    if len(runs) > 1:
        handles, lbls = axes.flat[0].get_legend_handles_labels()
        fig.legend(handles, lbls, loc="upper center", ncol=min(4, len(runs)), fontsize=10)
    fig.text(0.01, 0.005, "Shaded: hazard days of %s (grey drought, lilac badtide)." % labels[0], color=INK2, fontsize=8)
    fig.tight_layout(rect=(0, 0.02, 1, 0.95 if len(runs) > 1 else 1))
    path = os.path.join(out, "colony.png")
    fig.savefig(path, dpi=110)
    plt.close(fig)
    files.append(path)

    # workplace activity of each run: share of worker time working / idle / at needs, top 18 workplaces
    for i, (run, a) in enumerate(zip(runs, analyses)):
        wp = a.get("workplaces") or {}
        rows = sorted(wp.items(), key=lambda kv: -kv[1]["samples"])[:18]
        if not rows:
            continue
        fig, ax = plt.subplots(figsize=(9, 0.32 * len(rows) + 1.2))
        names = [k for k, _ in rows][::-1]
        vals = [v for _, v in rows][::-1]
        left = [0.0] * len(vals)
        for key, color, label in (("work", SERIES[0], "working"), ("idle", SERIES[1], "idle / waiting"), ("needs", SERIES[3], "needs during shift")):
            share = []
            for v in vals:
                tot = v["work"] + v["idle"] + v["needs"]
                share.append(v[key] / tot if tot else 0)
            ax.barh(names, share, left=left, color=color, label=label, height=0.7, edgecolor=SURFACE, linewidth=1)
            left = [l + s for l, s in zip(left, share)]
        ax.set_xlim(0, 1)
        ax.set_title("%s: workplace time in working hours" % labels[i], color=INK, loc="left")
        ax.legend(loc="lower right", fontsize=8)
        fig.tight_layout()
        path = os.path.join(out, "work_%s.png" % safe(labels[i]))
        fig.savefig(path, dpi=110)
        plt.close(fig)
        files.append(path)
    return files


def safe(s):
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in s)


# ---------------------------------------------------------------------------------------------------------- verdict

def fmt_day(x):
    return "never" if x is None else "day %s" % x


def verdict(a):
    if not a.get("days"):
        return "No telemetry."
    lines = []
    deaths = a["deaths"]
    starving = sum(n for c, n in a["deathCauses"].items() if "Hunger" in c or "Thirst" in c)
    if a["popEnd"] == 0:
        lines.append("**Colony died out** by day %s." % a["lastDay"])
    elif starving:
        lines.append("**Survived with losses:** %d deaths from hunger or thirst." % starving)
    elif a["popEnd"] < a["popStart"]:
        lines.append("**Survived but shrank** (%d to %d)." % (a["popStart"], a["popEnd"]))
    else:
        lines.append("**Thriving:** %d to %d colonists, no starvation." % (a["popStart"], a["popEnd"]))
    return " ".join(lines)


def section(a, run):
    if not a.get("days"):
        return "## %s\n\nNo daily telemetry in %s.\n" % (a["name"], run["dir"])
    out = ["## %s" % a["name"], ""]
    out.append("%s. %s on %s, %s; %d days recorded (to day %s); run `%s`." % (
        verdict(a), a.get("faction"), a.get("map"), a.get("mode") or "default mode", a["days"], a["lastDay"], run["dir"]))
    out.append("")
    hz = ", ".join("%s day %d-%d (%d of %s)" % (h["kind"], h["start"], h["start"] + h["days"] - 1, h["days"], h["planned"]) for h in a["hazards"]) or "none"
    out.append("| | |\n|---|---|")
    rows = [
        ("Population start / peak / end", "%d / %d / %d (lowest %d)" % (a["popStart"], a["popPeak"], a["popEnd"], a["popMin"])),
        ("Births / deaths", "%d / %d %s" % (a["births"], a["deaths"], json.dumps(a["deathCauses"]) if a["deaths"] else "")),
        ("First death", fmt_day(a["firstDeathDay"])),
        ("Population 20 / 30 / 50", "%s / %s / %s" % (fmt_day(a["dayPop20"]), fmt_day(a["dayPop30"]), fmt_day(a["dayPop50"]))),
        ("Hazards", hz),
        ("Lowest food / water stock", "%s on day %s / %s on day %s" % (a["foodMin"][1], a["foodMin"][0], a["waterMin"][1], a["waterMin"][0])),
        ("Critical needs (colonist-days, first day)", "; ".join("%s %d from day %s" % (k, v["colonistDays"], v["firstDay"]) for k, v in sorted(a["critical"].items())) or "none"),
        ("Wellbeing end / max", "%s / %s" % (a["wellbeingEnd"], a["wellbeingMax"])),
        ("First cooked food", "%s (%s)" % (fmt_day(a["firstCooked"][0]), a["firstCooked"][1]) if a["firstCooked"] else "never"),
        ("First leisure building", "day %s (%s)" % a["firstLeisure"] if a["firstLeisure"] else "never"),
        ("Buildings finished", str(a["buildingsFinished"])),
        ("Days with unemployed / homeless", "%d (max %d) / %d (max %d)" % (a["unemployedMaxDays"], a["unemployedMax"], a["homelessDays"], a["homelessMax"])),
        ("Produced, never consumed", ", ".join(a["neverConsumed"]) or "none"),
        ("Real seconds per game day", "%s at speed %s" % (a["realSecondsPerDay"], a["speeds"])),
    ]
    for k, v in rows:
        out.append("| %s | %s |" % (k, v))
    out.append("")
    wp = a.get("workplaces") or {}
    if wp:
        out.append("Workplaces (share of worker time in working hours; top statuses):")
        out.append("")
        out.append("| workplace | work | idle | needs | unstaffed samples | statuses |\n|---|---|---|---|---|---|")
        for k, v in sorted(wp.items(), key=lambda kv: -kv[1]["samples"])[:25]:
            tot = v["work"] + v["idle"] + v["needs"]
            pct = lambda x: "%d%%" % round(100 * x / tot) if tot else "-"
            st = ", ".join("%s (%d)" % (s, n) for s, n in sorted(v["statuses"].items(), key=lambda x: -x[1])[:3])
            out.append("| %s | %s | %s | %s | %d of %d | %s |" % (k, pct(v["work"]), pct(v["idle"]), pct(v["needs"]), v["empty"], v["samples"], st))
        out.append("")
    if a["stepsFailed"] or a["stepsWaiting"]:
        out.append("Plan steps that never ran: " + "; ".join("%s (%s)" % (i, e) for i, e in a["stepsFailed"] + a["stepsWaiting"]))
        out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--out")
    ap.add_argument("--labels")
    args = ap.parse_args()
    runs = [load_run(r) for r in args.runs]
    labels = args.labels.split(",") if args.labels else [r["name"] for r in runs]
    out = args.out or (os.path.join(args.runs[0], "playtest") if len(runs) == 1 else
                       os.path.join(r"E:\PandabornDev\build\playtest", "report-" + "-".join(safe(l) for l in labels)))
    os.makedirs(out, exist_ok=True)
    analyses = [analyse(r) for r in runs]
    md = ["# Playtest verdict", ""]
    for a, r in zip(analyses, runs):
        md.append(section(a, r))
    if len(runs) > 1:
        md.append("## Comparison\n")
        keys = [("popEnd", "pop end"), ("popPeak", "pop peak"), ("deaths", "deaths"), ("dayPop30", "pop 30"),
                ("dayPop50", "pop 50"), ("wellbeingEnd", "wellbeing end"), ("firstCooked", "first cooked"),
                ("firstLeisure", "first leisure")]
        md.append("| run | " + " | ".join(k[1] for k in keys) + " |")
        md.append("|---" * (len(keys) + 1) + "|")
        for l, a in zip(labels, analyses):
            md.append("| %s | " % l + " | ".join(str(a.get(k[0])) for k in keys) + " |")
        md.append("")
    try:
        files = charts(runs, analyses, out, labels)
        md.append("Charts: " + ", ".join(os.path.basename(f) for f in files))
    except ImportError:
        md.append("(matplotlib not available: no charts)")
    with open(os.path.join(out, "verdict.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    with open(os.path.join(out, "analysis.json"), "w", encoding="utf-8") as f:
        json.dump([{k: v for k, v in a.items() if k != "workplaces"} for a in analyses], f, indent=1, default=str)
    print(os.path.join(out, "verdict.md"))


if __name__ == "__main__":
    sys.exit(main())
