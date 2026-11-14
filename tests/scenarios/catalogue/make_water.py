"""Writes the gate's water scenarios from the water lane's (proto/water/tests): the same steps on the catalogue's
.Inkpaws templates, in an Inkpaws game.
  * water_w4_inkpaws.json    - pond, gate, flume line crossing another on a Bridge Span, spout, paddy; saved and
                               reloaded by the gate (-SaveAndReload)
  * water_scoop_inkpaws.json - scoop wheels in a current, a cistern-tap loop, a dew collector. The prototype's trip
                               hammer was a 1x1 water-wheel shell; the catalogue's Trip-Hammer Mill is the 3x2x3
                               Gristmill with a worker, so it is left out here and needs its own scenario (water lane).
Usage: python tests/scenarios/catalogue/make_water.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, "..", "..", "..", "proto", "water", "tests"))


def convert(name, out, drop_ids=()):
    with open(os.path.join(SRC, name), encoding="utf-8") as f:
        d = json.loads(f.read().replace('.PandabornProto"', '.Inkpaws"'))
    d["faction"] = "Inkpaws"
    d.pop("ownPatterns", None)
    d["note"] = "generated from proto/water/tests/%s by tests/scenarios/catalogue/make_water.py" % name
    for key in ("steps", "reloadSteps"):
        steps = []
        for s in d["water"].get(key) or []:
            if s.get("id") in drop_ids and s.get("op") == "place":
                continue
            if isinstance(s.get("objects"), list):
                s["objects"] = [o for o in s["objects"] if o not in drop_ids]
            steps.append(s)
        if key in d["water"]:
            d["water"][key] = steps
    with open(os.path.join(HERE, out), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(d, indent=1) + "\n")
    print("wrote", out)


convert("w4.json", "water_w4_inkpaws.json")
convert("scoop.json", "water_scoop_inkpaws.json", drop_ids=("hammer",))
