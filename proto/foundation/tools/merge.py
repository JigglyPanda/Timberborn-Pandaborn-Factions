"""Merge a fragment's top-level spec keys into a blueprint in place: python -I merge.py BLUEPRINT FRAGMENT"""
import json
import sys

base = json.load(open(sys.argv[1], encoding="utf-8-sig"))
base.update(json.load(open(sys.argv[2], encoding="utf-8-sig")))
with open(sys.argv[1], "w", encoding="utf-8", newline="\n") as fh:
    fh.write(json.dumps(base, indent=2, ensure_ascii=False) + "\n")
