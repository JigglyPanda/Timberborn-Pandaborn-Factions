"""Shelf-size experiment (dev only): who carries what, by day and by night, in a run of workshops.

Reads <run>/ringtails.json (per-sample "workerHoursSinceLastSample": kind|workplace|behaviour|carrying -> in-game hours, and
"pickupsSinceLastSample") and prints, for the Inkpaw workshop workers, the share of their day spent fetching and carrying
versus working, and the Ringtail couriers' night pickups.
Usage: python proto/ringtails/test/shelves.py E:/PandabornDev/build/test/<run> [more runs]
"""
import json
import sys
from collections import defaultdict

WORKSHOPS = ("PaperMill.Inkpaws", "PandabornPickleYard.Inkpaws", "GearWorkshop.Inkpaws", "PandabornSteamer.Inkpaws",
             "PandabornLanternWorkshop.Inkpaws")


def classify(behaviour, carrying):
    b = behaviour or ""
    if "FillInput" in b or "Emptying" in b or "EmptyOutput" in b or carrying == "carrying":
        return "carrying"
    if b in ("WorkWorkplaceBehavior", "ProduceWorkplaceBehavior") or "Produce" in b or b.startswith("Work"):
        return "working"
    if "WaitInsideIdly" in b:
        return "idle at work"
    return "other"


def analyse(run):
    d = json.load(open(run + "/ringtails.json", encoding="utf-8"))
    day = defaultdict(float)
    behaviours = defaultdict(float)
    night_pickups = defaultdict(int)
    day_pickups = defaultdict(int)
    for s in d["samples"]:
        night = s["hour"] >= 16 or s["hour"] < 0.5
        for key, hours in s.get("workerHoursSinceLastSample", {}).items():
            kind, workplace, behaviour, carrying = key.split("|")
            if kind == "inkpaw" and workplace in WORKSHOPS and not night:
                day[classify(behaviour, carrying)] += hours
                behaviours[behaviour + ("+load" if carrying == "carrying" else "")] += hours
        for p in s.get("pickupsSinceLastSample", []):
            (night_pickups if night else day_pickups)[(p["kind"], p["workplace"])] += p["goods"]
    total = sum(day.values()) or 1
    return {
        "run": run.rstrip("/").split("/")[-1],
        "inkpawWorkshopDayHours": {k: round(v, 1) for k, v in day.items()},
        "inkpawShare": {k: round(v / total, 3) for k, v in day.items()},
        "inkpawBehaviours": {k: round(v, 1) for k, v in sorted(behaviours.items(), key=lambda kv: -kv[1])[:10]},
        "goodsPickedUpByDay": {"%s @ %s" % k: v for k, v in day_pickups.items()},
        "goodsPickedUpByNight": {"%s @ %s" % k: v for k, v in night_pickups.items()},
        "events": [e["detail"] for e in d.get("events", []) if e["what"] in ("place", "setup")],
    }


if __name__ == "__main__":
    for run in sys.argv[1:]:
        print(json.dumps(analyse(run), indent=1))
