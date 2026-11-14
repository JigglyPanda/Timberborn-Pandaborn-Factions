"""Writes the water-toolkit scenario requests (proto/water/tests/*.json) for tools/run_game_test.ps1 -RequestJson.

Each file's "water" section is run by the dev harness's WaterLab (src/devharness/WaterLab.cs). Coordinates are relative
to the auto-chosen, flattened test area: x, y tiles; z relative to the flattened ground (z = 0 is where a building on
the ground stands). Flow "Cw90" = towards +x.

    python -I proto/water/tools/gen_tests.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "tests"))
P = ".PandabornProto"


def request(name, steps, area, speed=7, real_seconds=1500, faction="Folktails", map_name="Plains", origin="auto", extra=None):
    r = {
        "faction": faction,
        "map": map_name,
        "speed": 0,
        "batchControl": False,
        "run": {"realSeconds": real_seconds, "settleSeconds": 2},
        "screenshots": [{"name": "screen_end", "kind": "screen", "at": "end"}],
        "ownPatterns": ["PandabornFactions", "PandabornDevHarness", "Inkpaws", "Pandaborn.Water", "PandabornProto"],
        "water": {"name": name, "speed": speed, "area": area, "origin": origin, "flattenMargin": 2, "steps": steps},
    }
    if extra:
        r.update(extra)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(r, f, indent=1)
        f.write("\n")


def flat(x0, y0, x1, y1, z):
    return {"op": "flatten", "rect": [x0, y0, x1, y1], "z": z}


def place(t, at, o="Cw90", id=None, **kw):
    s = {"op": "place", "template": t + P, "at": at, "orientation": o}
    if id:
        s["id"] = id
    s.update(kw)
    return s


def line(t, frm, count, step=(1, 0, 0), o="Cw90", prefix=None):
    s = {"op": "placeLine", "template": t + P, "from": frm, "count": count, "step": list(step), "orientation": o}
    if prefix:
        s["idPrefix"] = prefix
    return s


def wait(ticks, cap=900):
    return {"op": "wait", "ticks": ticks, "capSeconds": cap}


def expect(label, what, at=None, mn=None, mx=None, **kw):
    s = {"op": "expect", "label": label, "what": what}
    if at is not None:
        s["at"] = at
    if mn is not None:
        s["min"] = mn
    if mx is not None:
        s["max"] = mx
    s.update(kw)
    return s


def shot(name, focus, distance=26, pitch=55, yaw=20):
    return {"op": "shot", "name": name, "focus": focus, "distance": distance, "pitch": pitch, "yaw": yaw}


# ---------------------------------------------------------------------------------------------------------------- flume
def pond(y0, y1, gap_y):
    """A 4-wide pond with 2-high walls, its outlet gap at x=5."""
    return [flat(0, y0 - 1, 5, y1 + 1, 2), flat(1, y0, 4, y1, 0), flat(5, gap_y, 5, gap_y, 0)]


def flume():
    """Three parallel 16-cell lines from constant-head ponds (surface 1.0 above the flume bed) into drained basins:
    A code route with the sealed step-down piece (y=7), B valve route over a plain terrain step (y=13), C code route
    with the open-leg step-down (y=19). Upper run x=5..14 on ground z=0; drop at x=15; lower run to x=21 at z=-1;
    basin x=22..25 floor z=-2 with a drain at its inlet. Phase 2 shuts the ponds; phase 3 floods the terrace from the
    basins to height -0.4 to test side sealing, one-way flow and the step-down's leg.
    """
    lines = {"A": 7, "B": 13, "C": 19}
    s = [flat(15, -1, 28, 26, -1)]                        # lower terrace, rimmed by the z=0 margin
    for y in lines.values():
        s += pond(y - 1, y + 1, y) + [flat(22, y - 2, 25, y + 2, -2)]
    s += [flat(15, 13, 15, 13, 0)]                        # B: terrain step one tile later
    s += [place("PandabornFlumeGate", [5, 7, 0], id="gateA"), line("PandabornFlume", [6, 7, 0], 9, prefix="a"),
          place("PandabornFlumeStep", [15, 7, -1], id="stepA"), line("PandabornFlume", [17, 7, -1], 5, prefix="b"),
          place("PandabornFlumeValveGate", [5, 13, 0], id="gateB"), line("PandabornFlumeValveOpen", [6, 13, 0], 10, prefix="c"),
          line("PandabornFlumeValveOpen", [16, 13, -1], 6, prefix="d"),
          place("PandabornFlumeGate", [5, 19, 0], id="gateC"), line("PandabornFlume", [6, 19, 0], 9, prefix="e"),
          place("PandabornFlumeStepOpen", [15, 19, -1], id="stepC"), line("PandabornFlume", [17, 19, -1], 5, prefix="f")]
    for lbl, y in lines.items():
        s += [{"op": "water", "id": "pond" + lbl, "at": [2, y, 0], "rate": 2.0, "maxDepth": 1.0},
              {"op": "water", "id": "drain" + lbl, "at": [22, y, -2], "rate": -3.0}]
        cells = [[3, y, 0], [5, y, 0], [6, y, 0], [8, y, 0], [10, y, 0], [12, y, 0], [14, y, 0], [15, y, 0], [16, y, -1],
                 [17, y, -1], [19, y, -1], [21, y, -1], [10, y - 1, 0], [10, y + 1, 0], [19, y - 1, -1], [19, y + 1, -1]]
        s += [{"op": "series", "id": "line" + lbl, "every": 25, "cells": cells, "volumes": [[22, y - 2, 25, y + 2, -2]]}]
    s += [shot("flume_setup", [13, 13, 0], 34)]
    rows = [[y, 0, 27, 0] for y in range(4, 23)] + [[y, 14, 27, -1] for y in range(4, 23)]
    moist = [[y, 0, 27, 0] for y in range(3, 24)] + [[y, 15, 27, -1] for y in range(3, 24)]
    probe_cells = {"rows": rows, "moistRows": moist, "objects": ["gateA", "gateB", "gateC", "stepA", "stepC"]}
    s += [wait(300), {"op": "probe", "label": "t300", **probe_cells}, shot("flume_t300", [13, 13, 0], 34)]
    s += [wait(600), {"op": "probe", "label": "t900", **probe_cells}, shot("flume_t900", [13, 13, 0], 34),
          shot("flume_t900_close", [10, 9, 0], 12, 40, 0)]
    for lbl, y in lines.items():
        s += [expect(f"{lbl} flume start wet", "depth", [6, y, 0], 0.01),
              expect(f"{lbl} flume end wet", "depth", [21, y, -1], 0.005),
              expect(f"{lbl} side strip dry (upper)", "depth", [10, y - 1, 0], None, 0.001),
              expect(f"{lbl} side strip dry (upper, other side)", "depth", [10, y + 1, 0], None, 0.001),
              expect(f"{lbl} side strip dry (lower)", "depth", [19, y + 1, -1], None, 0.001)]
    # phase 2: ponds off, lines drain
    s += [{"op": "waterOff", "id": "pond" + l} for l in lines] + [wait(400), {"op": "probe", "label": "drained", **probe_cells}]
    s += [{"op": "waterOff", "id": "drain" + l} for l in lines]
    # phase 3: flood the terrace from the basins up to height -0.4 (0.6 above the lower flume bed)
    s += [{"op": "water", "id": "flood" + l, "at": [24, y, -2], "rate": 3.0, "maxDepth": 1.6} for l, y in lines.items()]
    s += [wait(500), {"op": "probe", "label": "flooded", **probe_cells}, shot("flume_flooded", [16, 13, -1], 30)]
    for lbl, y in lines.items():
        s += [expect(f"{lbl} terrace flooded beside flume", "depth", [19, y + 1, -1], 0.2),
              expect(f"{lbl} upstream pond does not rise", "height", [3, y, 0], None, 0.2)]
    s += [expect("A lower flume stays dry in flood (sealed step)", "depth", [19, 7, -1], None, 0.02),
          expect("B lower flume stays dry in flood (terrain step)", "depth", [19, 13, -1], None, 0.02)]
    request("flume", s, [30, 26], map_name="Plains")


# ---------------------------------------------------------------------------------------------------------------- noria
def noria():
    """A 1-wide channel (y=5, floor z=-2) with a set throughflow; a noria at x=12 lifts into a walled basin on the
    bank (floor z=0, behind a z=+1 lip at y=6). Phases step the channel flow 0 -> 0.3 -> 0.8 -> 1.6 -> 3.0 and
    record the current at the wheel, the generator rotation, the power efficiency and the lift rate. A dew collector
    sits on the side and is read over a temperate day and a drought day.
    """
    s = [flat(0, 3, 27, 7, 1), flat(0, 5, 27, 5, -2),          # channel cut between raised banks
         flat(9, 6, 15, 11, 1), flat(10, 7, 14, 10, 0),       # basin behind the lip row y=6
         place("PandabornNoria", [12, 5, -2], "Cw0", id="noria"),
         place("PandabornDewCollector", [20, 12, 0], "Cw0", id="dew"),
         shot("noria_setup", [12, 7, 0], 18)]
    # still water first: fill the channel to ~0.8 deep with no throughflow
    s += [{"op": "water", "id": "fill", "at": [6, 5, -2], "rate": 2.0, "maxDepth": 0.8}, wait(150),
          {"op": "waterOff", "id": "fill"}, wait(100)]
    cells = [[12, 5, -2], [6, 5, -2], [20, 5, -2], [12, 7, 0], [12, 9, 0]]
    s += [{"op": "series", "id": "noria", "every": 20, "cells": cells, "volumes": [[10, 7, 14, 10, 0]], "objects": ["noria", "dew"]}]
    s += [wait(200), {"op": "probe", "label": "flow0", "cells": cells, "volumes": [[10, 7, 14, 10, 0]], "objects": ["noria", "dew"]}]
    for q in (0.3, 0.8, 1.6, 3.0):
        s += [{"op": "water", "id": "in", "at": [1, 5, -2], "rate": q, "maxDepth": 1.6},
              {"op": "water", "id": "out", "at": [26, 5, -2], "rate": -q * 1.5},
              wait(250),
              {"op": "probe", "label": f"flow{q}", "cells": cells, "volumes": [[10, 7, 14, 10, 0]], "objects": ["noria", "dew"]}]
    s += [shot("noria_running", [12, 7, -1], 16, 45, 60)]
    s += [expect("noria lifts in a strong current", "flowRate", id="noria", mn=0.01)]
    # dew collector: one temperate day, then one drought day
    s += [{"op": "waterOff", "id": "in"}, {"op": "waterOff", "id": "out"},
          {"op": "probe", "label": "dew_t0", "objects": ["dew"]}, {"op": "wait", "days": 1, "capSeconds": 400},
          {"op": "probe", "label": "dew_temperate_day", "objects": ["dew"]},
          {"op": "drought"}, {"op": "probe", "label": "dew_drought_start", "objects": ["dew"]},
          {"op": "wait", "days": 1, "capSeconds": 400},
          {"op": "probe", "label": "dew_drought_day", "objects": ["dew"]}]
    request("noria", s, [28, 16])


# ---------------------------------------------------------------------------------------------------------------- crops
PADDY, MOIST, DRY, BAMBOO = "PandabornPaddyCrop" + P, "PandabornMoistCrop" + P, "PandabornDryCrop" + P, "PandabornBamboo" + P


def crops(days_wet=3, days_dry=2, days_rewet=1.5, days_irrigate=2):
    """Spout-fed paddy plus a 3x3 zone matrix: each test crop planted in the paddy water, on the moist rim and on
    far dry ground. Bamboo groves (unmarked, planting-marked, cut-marked) beside the paddy. Phases: wet (spout on),
    dry (spout off, paddy drained), rewet (spout on), irrigate the dry zone.
    Layout: reservoir y=0..3 (walls z=+2), spout at (6,4) flowing +y, paddy x=2..13 y=5..9 floor z=-1,
    rim row y=11, bamboo east of the paddy at x=16..22, dry zone x=32..38 y=18..21.
    """
    s = [flat(1, -1, 11, 4, 2), flat(2, 0, 10, 3, 0), flat(6, 4, 6, 4, 0),      # reservoir and spout gap
         flat(2, 5, 13, 9, -1),                                               # paddy basin
         place("PandabornSpout", [6, 4, 0], "Cw0", id="spout"),
         {"op": "water", "id": "reservoir", "at": [6, 1, 0], "rate": 2.0, "maxDepth": 0.8}]
    zones = {"paddy": (7, -1), "rim": (11, 0), "dry": (20, 0)}
    xs = {"paddy": (3, 8, 11), "rim": (3, 8, 11), "dry": (32, 35, 37)}
    for zone, (y, z) in zones.items():
        x0, x1, x2 = xs[zone]
        s += [{"op": "plant", "template": PADDY, "rect": [x0, y, x0 + 2, y, z]},
              {"op": "plant", "template": MOIST, "rect": [x1, y, x1 + 1, y, z]},
              {"op": "plant", "template": DRY, "rect": [x2, y, x2 + 1, y, z]}]
    # bamboo: grove A unmarked; grove B on planting-marked tiles; grove C unmarked parents with marked empty neighbours;
    # grove D marked for cutting
    s += [{"op": "plant", "template": BAMBOO, "cells": [[17, 6, 0], [17, 8, 0]]},
          {"op": "markPlant", "template": BAMBOO, "rect": [19, 5, 21, 9, 0]},
          {"op": "plant", "template": BAMBOO, "cells": [[20, 6, 0], [20, 8, 0]]},
          {"op": "plant", "template": BAMBOO, "cells": [[17, 12, 0], [17, 14, 0]]},
          {"op": "markPlant", "template": BAMBOO, "rect": [16, 11, 18, 11, 0]},
          {"op": "markPlant", "template": BAMBOO, "rect": [16, 15, 18, 15, 0]},
          {"op": "plant", "template": BAMBOO, "cells": [[21, 12, 0], [21, 14, 0]]},
          {"op": "markCut", "rect": [20, 11, 22, 15, 0]},
          {"op": "grow", "template": BAMBOO, "rect": [15, 4, 23, 16, 0], "progress": 1.0}]
    everything = {"rect": [0, 0, 39, 23, 0]}
    paddy_cells = {"rect": [2, 5, 13, 9, -1]}
    moist_rows = [[y, 0, 39, 0] for y in range(0, 24, 1)]
    s += [shot("crops_setup", [16, 10, 0], 34),
          {"op": "series", "id": "paddy", "every": 40, "cells": [[6, 5, -1], [3, 7, -1], [13, 9, -1], [6, 2, 0]],
           "objects": ["spout"]},
          {"op": "plants", "label": "plants_d0", "rect": [0, 0, 39, 23, 0], "detail": True},
          {"op": "plants", "label": "paddy_d0", **paddy_cells}]

    def snapshot(tag):
        return [{"op": "plants", "label": "plants_" + tag, **everything},
                {"op": "plants", "label": "paddy_" + tag, **paddy_cells},
                {"op": "probe", "label": "water_" + tag, "rows": [[y, 0, 14, -1] for y in (5, 7, 9)], "moistRows": moist_rows,
                 "objects": ["spout"]}]

    s += [{"op": "wait", "hours": 12, "capSeconds": 600}] + snapshot("h12")
    s += [{"op": "wait", "hours": days_wet * 24 - 12, "capSeconds": 900}] + snapshot("wet")
    s += [expect("paddy held at spout depth", "depth", [3, 7, -1], 0.2, 0.45),
          expect("paddy crop healthy in paddy", "healthy", template=PADDY, rect=[3, 7, 5, 7, -1], mn=3),
          shot("crops_wet", [16, 10, 0], 34), shot("crops_wet_paddy", [8, 8, -1], 14, 50, 0)]
    # dry phase: reservoir off, spout closed, paddy drained
    s += [{"op": "waterOff", "id": "reservoir"}, {"op": "set", "id": "spout", "targetDepth": 0.0}]   # depth 0 = shut (a disabled target means fully open)
    s += [{"op": "water", "id": f"drain{i}", "at": [x, y, -1], "rate": -1.0} for i, (x, y) in enumerate([(2, 5), (13, 9), (8, 7), (2, 9), (13, 5)])]
    s += [{"op": "wait", "hours": 6, "capSeconds": 600}] + snapshot("dry_h6")
    s += [{"op": "wait", "hours": days_dry * 24 - 6, "capSeconds": 900}] + snapshot("dry")
    s += [shot("crops_dry", [16, 10, 0], 34)]
    # rewet
    s += [{"op": "waterOff", "id": f"drain{i}"} for i in range(5)]
    s += [{"op": "water", "id": "reservoir", "at": [6, 1, 0], "rate": 2.0, "maxDepth": 0.8},
          {"op": "set", "id": "spout", "targetDepth": 0.3},
          {"op": "wait", "hours": days_rewet * 24, "capSeconds": 900}] + snapshot("rewet")
    # irrigate the dry zone: a puddle source among the dry-zone plants
    s += [{"op": "water", "id": "irrigate", "at": [36, 21, 0], "rate": 0.05},
          {"op": "wait", "hours": days_irrigate * 24, "capSeconds": 900}] + snapshot("irrigated")
    s += [shot("crops_end", [16, 10, 0], 34), shot("crops_end_dry", [35, 20, 0], 14, 50, 0)]
    request("crops", s, [40, 24], real_seconds=3000)


# ---------------------------------------------------------------------------------------------------------------- district
def district():
    """Needs beavers, so the area sits next to the district center, levelled to its doorstep, with a path to it.
    Treadwheel at (3,2) facing the path row y=1: pit (3,3) floor -2 fed to 1.5 deep; ledge basin x=4..7 y=4..6 floor +1.
    Bamboo by a shallow water strip (y=5, x=10..20): grove W (11,7),(13,7) unmarked but inside a cutting area; grove P
    (17,7),(18,7) on planting-marked tiles. Lumberjack and gatherer flags on the path row.
    """
    s = [{"op": "pathFromDistrict", "to": [1, 1, 0]},
         {"op": "placeLine", "template": "Path", "from": [1, 1, 0], "count": 20, "step": [1, 0, 0], "orientation": "Cw0"},
         flat(3, 3, 8, 7, 2), flat(4, 4, 7, 6, 1), flat(3, 3, 3, 3, -2),
         place("PandabornTreadwheel", [3, 2, 0], "Cw0", id="tread"),
         {"op": "water", "id": "pit", "at": [3, 3, -2], "rate": 1.0, "maxDepth": 1.5},
         flat(10, 5, 20, 5, -1), {"op": "water", "id": "strip", "at": [15, 5, -1], "rate": 0.5, "maxDepth": 0.6},
         {"op": "place", "template": "LumberjackFlag.Folktails", "at": [10, 2, 0], "orientation": "Cw0", "id": "lumberjack"},
         {"op": "place", "template": "GathererFlag.Folktails", "at": [13, 2, 0], "orientation": "Cw0", "id": "gatherer"},
         {"op": "plant", "template": BAMBOO, "cells": [[11, 7, 0], [13, 7, 0]]},
         {"op": "markPlant", "template": BAMBOO, "rect": [16, 6, 19, 8, 0]},
         {"op": "plant", "template": BAMBOO, "cells": [[17, 7, 0], [18, 7, 0]]},
         {"op": "grow", "template": BAMBOO, "rect": [9, 4, 21, 10, 0], "progress": 1.0},
         {"op": "markCut", "rect": [10, 6, 14, 9, 0]}]
    objs = ["tread", "lumberjack", "gatherer"]
    grove = {"rect": [8, 3, 22, 11, 0]}
    s += [{"op": "series", "id": "tread", "every": 40, "cells": [[3, 3, -2], [5, 4, 1]], "volumes": [[4, 4, 7, 6, 1]], "objects": ["tread"]},
          shot("district_setup", [10, 5, 0], 30), {"op": "plants", "label": "bamboo_h0", **grove},
          {"op": "probe", "label": "h0", "objects": objs, "goods": ["Log", "Berries"], "moistRows": [[y, 8, 22, 0] for y in range(3, 11)]}]
    for h in (6, 12, 24, 48, 72):
        prev = {6: 0, 12: 6, 24: 12, 48: 24, 72: 48}[h]
        s += [{"op": "wait", "hours": h - prev, "capSeconds": 900},
              {"op": "probe", "label": f"h{h}", "objects": objs, "goods": ["Log", "Berries"], "volumes": [[4, 4, 7, 6, 1]]},
              {"op": "plants", "label": f"bamboo_h{h}", **grove}]
        if h == 12:
            s += [shot("district_h12", [8, 4, 0], 16, 45, 10)]
    s += [shot("district_end", [10, 5, 0], 30), expect("treadwheel staffed", "volume", rect=[4, 4, 7, 6, 1], mn=0.05)]
    request("district", s, [24, 14], speed=5, real_seconds=3000, origin={"nearDistrict": True})


if __name__ == "__main__":
    flume()
    noria()
    crops()
    district()
    print("wrote", sorted(os.listdir(OUT)))
