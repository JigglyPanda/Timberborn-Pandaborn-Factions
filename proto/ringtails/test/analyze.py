"""Analyse a Ringtails prototype test run (dev only).

Reads <run>/ringtails.json (the probe's hourly samples), <run>/result.json and <run>/summary.json, plus <run>/reload/ when
the run used -SaveAndReload, and prints the gate checks and the measured behaviour. Writes <run>/ringtails_report.json.

Usage: python proto/ringtails/test/analyze.py E:\\PandabornDev\\build\\test\\<run id>
Standard library only.
"""
import json
import os
import sys
from collections import Counter, defaultdict

RINGTAIL_WORKPLACES = {"RingtailHaulingPost.Inkpaws", "RingtailGathererFlag.Inkpaws", "PandabornNightBuildersPost.Inkpaws",
                       "PandabornNightCourierPost.Inkpaws", "PandabornNightForagersPost.Inkpaws"}
WORK_EXECUTORS_IDLE = {"WaitInsideIdlyWorkplaceBehavior"}


def load(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


BELL = [16.0]


def phase(hour):
    """hour = hours after dawn. Rest/day: dawn to the bell (Inkpaws work); night: the bell to dawn (Ringtails work).
    The early part of the day (first 4 h) is reported separately as "morning" (Ringtails asleep)."""
    if hour < 4:
        return "morning"
    if hour < BELL[0]:
        return "afternoon"
    return "night"


def activity(c):
    b = c.get("behavior") or ""
    e = c.get("executor") or ""
    if b == "SleepNeedBehavior" and e == "ApplyEffectExecutor":
        return "sleeping"
    if b == "SleepNeedBehavior":
        return "going to bed"
    if c.get("jobRunning"):
        return "working"
    if b in ("WaitInsideIdlyWorkplaceBehavior",):
        return "idle at work"
    if b.endswith("WorkplaceBehavior") or b in ("HaulBehavior", "GathererFlagWorkplaceBehavior", "BuilderJobBehavior"):
        return "at work"
    if b in ("WanderRootBehavior",):
        return "wandering"
    if b in ("", None):
        return "none"
    if "Need" in b or "Attraction" in b or b in ("ConsumeGoodsBehavior",):
        return "needs/leisure"
    return b


def analyse_samples(probe, label):
    samples = probe.get("samples", []) if probe else []
    if samples and samples[-1].get("sliderHours"):
        BELL[0] = float(samples[-1]["sliderHours"])
    out = {"label": label, "samples": len(samples)}
    if not samples:
        return out, []
    problems = []
    # 1. job exclusivity
    wrong = []
    for s in samples:
        for c in s["colonists"]:
            wp = c.get("workplace")
            if not wp:
                continue
            if c["kind"] == "ringtail" and wp not in RINGTAIL_WORKPLACES:
                wrong.append((s["runHour"], c["name"], c["kind"], wp))
            if c["kind"] != "ringtail" and wp in RINGTAIL_WORKPLACES:
                wrong.append((s["runHour"], c["name"], c["kind"], wp))
        for w in s["workplaces"]:
            kinds = set(w.get("assignedKinds", []))
            if w.get("ringtailOnly") and kinds - {"ringtail"}:
                wrong.append((s["runHour"], w["template"], "staffed by", sorted(kinds)))
            if not w.get("ringtailOnly") and "ringtail" in kinds:
                wrong.append((s["runHour"], w["template"], "staffed by", sorted(kinds)))
    out["jobExclusivityViolations"] = wrong[:20]
    out["jobExclusivityViolationCount"] = len(wrong)
    if wrong:
        problems.append("%d job exclusivity violation(s)" % len(wrong))

    # 2. activity by kind and phase
    act = defaultdict(Counter)       # (kind, phase) -> activity counter
    loc = defaultdict(Counter)       # (kind, phase) -> location counter
    per_ringtail_day = defaultdict(Counter)   # (name, day) -> activity hours
    for s in samples:
        ph = phase(s["hour"])
        for c in s["colonists"]:
            k = c["kind"]
            a = activity(c)
            act[(k, ph)][a] += 1
            loc[(k, ph)][c.get("location", "?")] += 1
            if k == "ringtail":
                per_ringtail_day[(c["name"], s["day"])][a] += 1
    out["activityByKindAndPhase"] = {"%s/%s" % key: dict(v.most_common()) for key, v in sorted(act.items())}
    out["locationByKindAndPhase"] = {"%s/%s" % key: dict(v.most_common(6)) for key, v in sorted(loc.items())}
    out["ringtailHoursPerDay"] = {"%s day %s" % key: dict(v.most_common()) for key, v in sorted(per_ringtail_day.items())}

    def share(kind, ph, names):
        c = act.get((kind, ph))
        if not c:
            return None
        total = sum(c.values())
        return round(sum(c[n] for n in names) / total, 3)

    out["shares"] = {
        "ringtail working-or-at-work afternoon": share("ringtail", "afternoon", ["working", "at work", "idle at work"]),
        "ringtail working-or-at-work night": share("ringtail", "night", ["working", "at work", "idle at work"]),
        "ringtail working-or-at-work morning": share("ringtail", "morning", ["working", "at work", "idle at work"]),
        "ringtail sleeping morning": share("ringtail", "morning", ["sleeping", "going to bed"]),
        "inkpaw working-or-at-work morning": share("inkpaw", "morning", ["working", "at work", "idle at work"]),
        "inkpaw working-or-at-work afternoon": share("inkpaw", "afternoon", ["working", "at work", "idle at work"]),
        "inkpaw sleeping night": share("inkpaw", "night", ["sleeping", "going to bed"]),
    }

    # 3. needs
    minimum = defaultdict(lambda: 99.0)
    critical = Counter()
    for s in samples:
        for c in s["colonists"]:
            for n in ("sleep", "hunger", "thirst"):
                if n in c:
                    minimum[(c["kind"], n)] = min(minimum[(c["kind"], n)], c[n])
            for n in c.get("critical", []):
                critical[(c["kind"], n)] += 1
    out["needMinimum"] = {"%s/%s" % k: v for k, v in sorted(minimum.items())}
    out["criticalNeedSamples"] = {"%s/%s" % k: v for k, v in sorted(critical.items())}
    if any(k[0] == "ringtail" and k[1] == "Sleep" for k in critical):
        problems.append("a Ringtail was exhausted (critical Sleep)")

    # 4. throughput
    pick = defaultdict(lambda: Counter())
    for s in samples:
        ph = phase(s["hour"])
        for p in s.get("pickupsSinceLastSample", []):
            pick[(p["kind"], p["workplace"], ph)]["pickups"] += p["pickups"]
            pick[(p["kind"], p["workplace"], ph)]["goods"] += p["goods"]
    out["pickupsByKindWorkplacePhase"] = {"%s @ %s / %s" % k: dict(v) for k, v in sorted(pick.items())}

    # 5. player numbers
    numbers = []
    for s in samples:
        pn = s.get("playerNumbers") or {}
        kinds = Counter(c["kind"] for c in s["colonists"] if c.get("alive", True))
        numbers.append({"runHour": s["runHour"], "hour": s["hour"], "adultsShown": pn.get("adults"),
                        "inkpaws": kinds["inkpaw"], "ringtails": kinds["ringtail"], "kits": kinds["ringtailKit"],
                        "cubs": kinds["inkpawCub"], "employable": pn.get("beaverEmployable"),
                        "employed": pn.get("beaverEmployed"), "vacancies": pn.get("beaverVacancies"),
                        "unemployed": pn.get("beaverUnemployed"), "homeless": pn.get("homeless"),
                        "bedsOccupied": pn.get("bedsOccupied"), "bedsFree": pn.get("bedsFree")})
    out["playerNumbers"] = numbers
    # 6. homes
    last = samples[-1]
    out["finalColonists"] = [{k: c.get(k) for k in ("id", "name", "kind", "template", "workplace", "workplaceId", "home", "homeId", "homeIsLoft", "coat", "baseSpeed")}
                             for c in last["colonists"]]
    out["housing"] = last.get("housing")
    return out, problems


def compare_reload(first, reload):
    if not first or not reload or not first.get("samples") or not reload.get("samples"):
        return None, ["no samples to compare across the reload"]
    before = {c["id"]: c for c in first["samples"][-1]["colonists"]}
    after = {c["id"]: c for c in reload["samples"][0]["colonists"]}
    diffs = []
    for cid, b in before.items():
        a = after.get(cid)
        if a is None:
            diffs.append("%s (%s) missing after reload" % (b["name"], b["kind"]))
            continue
        for key in ("kind", "template", "workplaceId", "homeId"):
            if b.get(key) != a.get(key):
                diffs.append("%s: %s %s -> %s" % (b["name"], key, b.get(key), a.get(key)))
    for cid, a in after.items():
        if cid not in before:
            diffs.append("%s (%s) new after reload" % (a["name"], a["kind"]))
    return {"before": len(before), "after": len(after), "differences": diffs}, (["reload changed colonists: %d difference(s)" % len(diffs)] if diffs else [])


def main():
    run = sys.argv[1]
    report = {"run": run}
    problems = []
    probe = load(os.path.join(run, "ringtails.json"))
    summary = load(os.path.join(run, "summary.json"))
    result = load(os.path.join(run, "result.json"))
    a, p = analyse_samples(probe, "new game")
    report["newGame"] = a
    problems += p
    if probe:
        report["feature"] = probe.get("feature")
        report["events"] = probe.get("events")
        report["shots"] = probe.get("shots")
        report["restInsertionError"] = probe.get("restInsertionError")
    reload_probe = load(os.path.join(run, "reload", "ringtails.json"))
    if reload_probe:
        b, p = analyse_samples(reload_probe, "reload")
        report["reload"] = b
        problems += ["reload: " + x for x in p]
        cmp, p = compare_reload(probe, reload_probe)
        report["reloadComparison"] = cmp
        problems += p
    if summary:
        report["harnessVerdict"] = summary.get("verdict")
        report["harnessProblems"] = summary.get("problems")
    if result:
        report["batchControl"] = result.get("batchControl")
        report["characterTemplates"] = result.get("characterTemplates")
    report["problems"] = problems
    with open(os.path.join(run, "ringtails_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=1)[:20000])


if __name__ == "__main__":
    main()
