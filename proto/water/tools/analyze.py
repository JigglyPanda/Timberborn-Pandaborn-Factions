"""Prints the water-lab part of a test run's result.json in a readable form.

    python -I proto/water/tools/analyze.py E:\\PandabornDev\\build\\test\\<run id> [--grids] [--plants] [--series]
"""
import json
import os
import sys


def main():
    run = sys.argv[1]
    flags = set(sys.argv[2:])
    path = os.path.join(run, "result.json")
    if not os.path.exists(path):
        path = os.path.join(run, "progress.json")
    r = json.load(open(path, encoding="utf-8"))
    w = r.get("water", {})
    print("status", r.get("status"), "| lab", w.get("status"), "| ticks", w.get("ticks"), "| origin", w.get("origin"),
          "| map", r.get("newGame", {}).get("map"), w.get("mapSize"), "| candidates", w.get("areaCandidates"))
    for l in w.get("log", []):
        if "text" in l:
            print(f"  [{l['tick']:>5} {l['hours']:>7}h] {l['text'][:160]}")
        elif l.get("error") or not l.get("placed"):
            print("  PLACE FAIL", l)
    for c in w.get("checks", []):
        print(("  ok  " if c["pass"] else "  FAIL"), c["label"], c["value"], c.get("min"), c.get("max"))
    for label, p in w.get("probes", {}).items():
        head = {k: p[k] for k in ("tick", "hours", "drought", "count", "healthy", "dying", "dead", "grown") if k in p}
        print("probe", label, head)
        if "sourceTotals" in p:
            print("   sources", p["sourceTotals"])
        for o in p.get("objects", []):
            print("   obj", o)
        if "goods" in p:
            print("   goods", p["goods"])
        for v in p.get("volumes", []):
            print("   vol", v)
        for c in p.get("cells", []):
            print("   cell", c)
        if "--grids" in flags:
            for g in p.get("grid", []):
                print("   ", g)
            for g in p.get("moistGrid", []):
                print("   m", g)
        if "--plants" in flags:
            for pl in p.get("plants") or []:
                print("   ", pl)
    if "--series" in flags:
        for sid, rows in w.get("series", {}).items():
            print("series", sid)
            for row in rows:
                print("   ", row)


if __name__ == "__main__":
    main()
