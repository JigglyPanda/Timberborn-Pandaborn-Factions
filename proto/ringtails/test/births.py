"""Births, growth and the population valve from a probe run (ringtails.json, and reload/ringtails.json if present).

Usage: python births.py <run dir>
Prints one line per in-game hour where something changed (Ringtail adults, kits, night jobs wanted, loft states,
kits raised, colonists in critical thirst/hunger, UI and sound state), then a summary of what was seen.
"""
import json
import os
import sys
from collections import Counter


def load(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def short(state):
    return (state or "-").replace("Pandaborn.Ringtails.Loft.", "")


def rows(data, part):
    out = []
    for s in data.get("samples", []):
        cols = s.get("colonists", [])
        kinds = Counter(c.get("kind") for c in cols)
        jobs = sum(w.get("desired", 0) for w in s.get("workplaces", []) if w.get("ringtailOnly") and w.get("workerType") == "PandabornRingtail")
        employed = sum(1 for c in cols if c.get("kind") == "ringtail" and c.get("workplace", "").startswith("PandabornNight"))
        critical = sum(1 for c in cols if c.get("critical"))
        dead = sum(1 for c in cols if c.get("alive") is False)
        lofts = Counter(short(l.get("kitState")) for l in s.get("lofts", []))
        ui = s.get("ui") or {}
        out.append({
            "part": part, "day": s.get("day"), "hour": s.get("hour"), "ringtails": kinds.get("ringtail", 0),
            "kits": kinds.get("ringtailKit", 0), "inkpaws": kinds.get("inkpaw", 0), "cubs": kinds.get("inkpawCub", 0),
            "nightJobs": jobs, "employed": employed, "critical": critical, "dead": dead,
            "lofts": dict(sorted(lofts.items())), "kitsRaised": (s.get("feature") or {}).get("kitsRaised"),
            "clock": ui.get("clockArc"), "mark": ui.get("buildingMark"), "clapper": ui.get("clapper"),
            "clappers": ui.get("clappersPlayed"),
        })
    return out


def main():
    run = sys.argv[1]
    first = load(os.path.join(run, "ringtails.json"))
    if first is None:
        sys.exit("no ringtails.json in " + run)
    table = rows(first, "first")
    second = load(os.path.join(run, "reload", "ringtails.json"))
    if second is not None:
        table += rows(second, "reload")
    keys = ("ringtails", "kits", "nightJobs", "employed", "critical", "lofts", "kitsRaised", "clapper", "clappers")
    last = None
    for r in table:
        sig = tuple(json.dumps(r[k], sort_keys=True) for k in keys)
        if sig != last:
            print("{part:6} day {day:>3} h{hour:>6}  ringtails {ringtails:>2} kits {kits:>2} | jobs {nightJobs:>2} employed {employed:>2}"
                  " | inkpaws {inkpaws:>2} cubs {cubs:>2} | critical {critical:>2} | lofts {lofts} | raised {kitsRaised}"
                  " | clock {clock} mark {mark} clapper {clapper}/{clappers}".format(**r))
            last = sig
    states = Counter()
    for r in table:
        for k in r["lofts"]:
            states[k] += 1
    print()
    print("loft states seen (loft-hours):", dict(states))
    over = [r for r in table if r["ringtails"] + r["kits"] > r["nightJobs"] and r["nightJobs"] > 0]
    print("hours with more Ringtails than night jobs:", len(over), "of", len(table))
    print("max Ringtails+kits:", max((r["ringtails"] + r["kits"] for r in table), default=0),
          "max night jobs:", max((r["nightJobs"] for r in table), default=0))
    print("min Ringtail adults after arrival:", min((r["ringtails"] for r in table if r["ringtails"] or r["kits"]), default=0))
    for part, data in (("first", first), ("reload", second)):
        if data:
            for e in data.get("events", []):
                if e.get("what") in ("laterGoods", "laterPlace", "laterDelete", "spawn", "place"):
                    print(part, "event", e.get("day"), e.get("what"), str(e.get("detail"))[:160])
            for s in data.get("shots", []):
                print(part, "shot", s.get("name"), s.get("file"), s.get("target"))


if __name__ == "__main__":
    main()
