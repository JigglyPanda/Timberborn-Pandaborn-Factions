"""Merge a fragment into a blueprint in place, with the game's merge rules (objects deep-merge, arrays replace,
"key#append" appends to an array, "key#delete" removes the key):

    python -I merge.py BLUEPRINT FRAGMENT
"""
import json
import sys


def merge(base, add):
    for key, value in add.items():
        if key.endswith("#append"):
            k = key[: -len("#append")]
            base[k] = list(base.get(k) or []) + list(value)
        elif key.endswith("#delete"):
            base.pop(key[: -len("#delete")], None)
        elif isinstance(value, dict) and isinstance(base.get(key), dict):
            merge(base[key], value)
        else:
            base[key] = value
    return base


base = json.load(open(sys.argv[1], encoding="utf-8-sig"))
merge(base, json.load(open(sys.argv[2], encoding="utf-8-sig")))
with open(sys.argv[1], "w", encoding="utf-8", newline="\n") as fh:
    fh.write(json.dumps(base, indent=2, ensure_ascii=False) + "\n")
