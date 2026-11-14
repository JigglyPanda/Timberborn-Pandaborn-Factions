"""Writes the water-toolkit scenario requests (proto/water/tests/*.json) for tools/run_game_test.ps1 -RequestJson.

Each file's "water" section is run by the dev harness's WaterLab (src/devharness/WaterLab.cs). Coordinates are relative
to the auto-chosen, flattened test area: x, y tiles; z relative to the flattened ground (z = 0 is where a building on
the ground stands). Orientation of a flume piece = its flow: Cw0 +y, Cw90 +x, Cw180 -y, Cw270 -x.

    python -I proto/water/tools/gen_tests.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "tests"))
P = ".PandabornProto"
PADDY, MOIST, DRY = "PandabornPaddyCrop" + P, "PandabornMoistCrop" + P, "PandabornDryCrop" + P
BAMBOO, SHOOT, TIMBER = "PandabornBamboo" + P, "PandabornShootBamboo" + P, "PandabornTimberBamboo" + P


def request(name, steps, area, speed=7, real_seconds=1500, faction="Folktails", map_name="Plains", origin="auto"):
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
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(r, f, indent=1)
        f.write("\n")


def flat(x0, y0, x1, y1, z):
    return {"op": "flatten", "rect": [x0, y0, x1, y1], "z": z}


def place(t, at, o="Cw90", id=None, **kw):
    s = {"op": "place", "template": t if t.endswith((".Folktails", ".Inkpaws")) or t == "Path" else t + P, "at": at, "orientation": o}
    if id:
        s["id"] = id
    s.update(kw)
    return s


def line(t, frm, count, step=(1, 0, 0), o="Cw90", prefix=None):
    s = {"op": "placeLine", "template": t + P, "from": frm, "count": count, "step": list(step), "orientation": o}
    if prefix:
        s["idPrefix"] = prefix
    return s


def water(id, at, rate, max_depth=None, contaminated=False):
    s = {"op": "water", "id": id, "at": at, "rate": rate}
    if max_depth is not None:
        s["maxDepth"] = max_depth
    if contaminated:
        s["contaminated"] = True
    return s


def off(*ids):
    return [{"op": "waterOff", "id": i} for i in ids]


def wait(ticks, cap=900):
    return {"op": "wait", "ticks": ticks, "capSeconds": cap}


def wait_hours(h, cap=900):
    return {"op": "wait", "hours": h, "capSeconds": cap}


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


def pond(y0, y1, gap_y, x1=4, floor=0):
    """A pond x=1..x1 with walls 2 above its floor; its outlet gap at x=x1+1."""
    return [flat(0, y0 - 1, x1 + 1, y1 + 1, floor + 2), flat(1, y0, x1, y1, floor), flat(x1 + 1, gap_y, x1 + 1, gap_y, floor)]


# ---------------------------------------------------------------------------------------------------------------- flume
def flume():
    """Three parallel 16-cell lines from constant-head ponds (surface 1.0 above the flume bed) into drained basins:
    A component route with the sealed Flume Drop (y=7), B valve route over a plain terrain step (y=13), C component
    route with the open-leg drop (y=19). Upper run x=5..14 on ground z=0; drop at x=15; lower run to x=21 at z=-1;
    basin x=22..25 floor z=-2 with a drain at its inlet. Phase 2 shuts the ponds; phase 3 floods the terrace from the
    basins to height -0.4 to test side sealing, one-way flow and the drop's leg.
    """
    lines = {"A": 7, "B": 13, "C": 19}
    s = [flat(15, -1, 28, 26, -1)]                        # lower terrace, rimmed by the z=0 margin
    for y in lines.values():
        s += pond(y - 1, y + 1, y) + [flat(22, y - 2, 25, y + 2, -2)]
    s += [flat(15, 13, 15, 13, 0)]                        # B: terrain step one tile later
    s += [place("PandabornFlumeGate", [5, 7, 0], id="gateA"), line("PandabornFlume", [6, 7, 0], 9, prefix="a"),
          place("PandabornFlumeDrop", [15, 7, -1], id="dropA"), line("PandabornFlume", [17, 7, -1], 5, prefix="b"),
          place("PandabornFlumeValveGate", [5, 13, 0], id="gateB"), line("PandabornFlumeValveOpen", [6, 13, 0], 10, prefix="c"),
          line("PandabornFlumeValveOpen", [16, 13, -1], 6, prefix="d"),
          place("PandabornFlumeGate", [5, 19, 0], id="gateC"), line("PandabornFlume", [6, 19, 0], 9, prefix="e"),
          place("PandabornFlumeDropOpen", [15, 19, -1], id="dropC"), line("PandabornFlume", [17, 19, -1], 5, prefix="f")]
    for lbl, y in lines.items():
        s += [water("pond" + lbl, [2, y, 0], 2.0, 1.0), water("drain" + lbl, [22, y, -2], -3.0)]
        cells = [[3, y, 0], [5, y, 0], [6, y, 0], [8, y, 0], [10, y, 0], [12, y, 0], [14, y, 0], [15, y, 0], [16, y, -1],
                 [17, y, -1], [19, y, -1], [21, y, -1], [10, y - 1, 0], [10, y + 1, 0], [19, y - 1, -1], [19, y + 1, -1]]
        s += [{"op": "series", "id": "line" + lbl, "every": 25, "cells": cells, "volumes": [[22, y - 2, 25, y + 2, -2]]}]
    s += [shot("flume_setup", [13, 13, 0], 34)]
    rows = [[y, 0, 27, 0] for y in range(4, 23)] + [[y, 14, 27, -1] for y in range(4, 23)]
    moist = [[y, 0, 27, 0] for y in range(3, 24)] + [[y, 15, 27, -1] for y in range(3, 24)]
    objs = ["gateA", "gateB", "gateC", "dropA", "dropC", "a0", "a8", "b4", "e8", "f4"]
    probe_cells = {"rows": rows, "moistRows": moist, "objects": objs}
    s += [wait(300), {"op": "probe", "label": "t300", **probe_cells}, shot("flume_t300", [13, 13, 0], 34)]
    s += [wait(600), {"op": "probe", "label": "t900", **probe_cells}, shot("flume_t900", [13, 13, 0], 34),
          shot("flume_t900_close", [10, 9, 0], 12, 40, 0)]
    for lbl, y in lines.items():
        s += [expect(f"{lbl} flume start wet", "depth", [6, y, 0], 0.01),
              expect(f"{lbl} flume end wet", "depth", [21, y, -1], 0.005),
              expect(f"{lbl} side strip dry (upper)", "depth", [10, y - 1, 0], None, 0.001),
              expect(f"{lbl} side strip dry (upper, other side)", "depth", [10, y + 1, 0], None, 0.001),
              expect(f"{lbl} side strip dry (lower)", "depth", [19, y + 1, -1], None, 0.001)]
    s += off(*["pond" + l for l in lines]) + [wait(400), {"op": "probe", "label": "drained", **probe_cells}]
    s += off(*["drain" + l for l in lines])
    s += [water("flood" + l, [24, y, -2], 3.0, 1.6) for l, y in lines.items()]
    s += [wait(500), {"op": "probe", "label": "flooded", **probe_cells}, shot("flume_flooded", [16, 13, -1], 30)]
    for lbl, y in lines.items():
        s += [expect(f"{lbl} terrace flooded beside flume", "depth", [19, y + 1, -1], 0.2),
              expect(f"{lbl} upstream pond does not rise", "height", [3, y, 0], None, 0.2)]
    s += [expect("A lower flume stays dry in flood (sealed drop)", "depth", [19, 7, -1], None, 0.02),
          expect("B lower flume stays dry in flood (terrain step)", "depth", [19, 13, -1], None, 0.02)]
    request("flume", s, [30, 26])


# ---------------------------------------------------------------------------------------------------------------- longrun
def longrun():
    """Level flumes of 10, 20, 40 and 60 tiles from identical constant-head ponds into drained sinks; delivered flow
    against length, depth profile, and the moisture strip beside a long flume."""
    lengths = {"L10": (2, 10), "L20": (7, 20), "L40": (12, 40), "L60": (17, 60)}
    s = []
    for lbl, (y, n) in lengths.items():
        s += pond(y - 1, y + 1, y)
        s += [place("PandabornFlumeGate", [5, y, 0], id="gate" + lbl), line("PandabornFlume", [6, y, 0], n, prefix=lbl + "_"),
              flat(6 + n, y - 1, 8 + n, y + 1, -1), water("pond" + lbl, [2, y, 0], 2.0, 1.0),
              water("sink" + lbl, [6 + n, y, -1], -3.0)]
        pts = sorted(set([6, 6 + n // 4, 6 + n // 2, 6 + 3 * n // 4, 5 + n]))
        s += [{"op": "series", "id": lbl, "every": 30, "cells": [[x, y, 0] for x in pts]}]
    s += [shot("longrun_setup", [36, 10, 0], 60, 60, 0)]
    rows = [[y, 0, 69, 0] for y in range(0, 21)]
    s += [wait(400), {"op": "probe", "label": "t400"}, wait(800), {"op": "probe", "label": "t1200", "rows": rows, "moistRows": rows},
          shot("longrun_t1200", [36, 10, 0], 60, 60, 0), shot("longrun_far_end", [62, 17, 0], 14, 50, 0)]
    request("longrun", s, [70, 20])


# ---------------------------------------------------------------------------------------------------------------- parts
def parts():
    """Flume Corners, a covered segment under a path, a Flume Bridge, the status icons, and the badwater shut-off.
    Line 1: pond (1..4, 2..4) -> Flume Gate (5,3) -> east -> Corner (9,3) north -> (9,4..7) -> Corner (9,8) east ->
    (10..12,8) -> covered (13,8) under a path -> (14,8) -> Paddy Spout (15,8) -> paddy x16..19 y6..10 z-1.
    Line 2 (the control: a valve gate without shut-off): plateau pond (floor +1) -> gate (5,13,+1) -> bridges
    (6..12,13) -> Drop (13..14,13) -> Paddy Spout (15,13) -> paddy x16..19 y11..15 z-1.
    Status row y=18: misaligned pair at (2..3,18), blocked flume at (6,18) facing raised ground, dry intake at (10,18).
    Phases: clean 900 ticks; both ponds turn contaminated for 500 ticks; ponds drained and refilled clean for a day.
    """
    s = [flat(0, 1, 5, 5, 2), flat(1, 2, 4, 4, 0), flat(5, 3, 5, 3, 0),
         flat(0, 11, 5, 15, 3), flat(1, 12, 4, 14, 1), flat(5, 13, 5, 13, 1),
         flat(16, 6, 19, 10, -1), flat(16, 11, 19, 15, -1), flat(16, 10, 19, 11, 0), flat(7, 18, 7, 18, 1),
         wait(3),   # let the water map pick up the new terrain before anything reads column floors
         place("PandabornFlumeGate", [5, 3, 0], id="gate1"), line("PandabornFlume", [6, 3, 0], 3),
         place("PandabornFlumeCorner", [9, 3, 0], "Cw90", id="corner1"), line("PandabornFlume", [9, 4, 0], 4, (0, 1, 0), "Cw0"),
         place("PandabornFlumeCorner", [9, 8, 0], "Cw270", id="corner2"), line("PandabornFlume", [10, 8, 0], 3),
         place("PandabornFlumeLidded", [13, 8, 0], id="covered"), place("Path", [13, 8, 1], "Cw0", id="coveredPath"),
         place("PandabornFlume", [14, 8, 0], id="end1"), place("PandabornPaddySpout", [15, 8, 0], "Cw90", id="spout1"),
         place("PandabornFlumeValveGate", [5, 13, 1], id="gate2"), line("PandabornFlumeBridge", [6, 13, 0], 7, prefix="br"),
         place("PandabornFlumeDrop", [13, 13, 0], id="drop2"), place("PandabornPaddySpout", [15, 13, 0], "Cw90", id="spout2"),
         place("PandabornFlume", [2, 18, 0], id="mis1"), place("PandabornFlume", [3, 18, 0], "Cw0", id="mis2"),
         place("PandabornFlume", [6, 18, 0], id="blocked"), place("PandabornFlumeGate", [10, 18, 0], id="dryIntake"),
         place("PandabornFlume", [11, 18, 0], id="dryEnd"),
         {"op": "plant", "template": PADDY, "rect": [17, 7, 18, 9, -1]},
         {"op": "plant", "template": PADDY, "rect": [17, 12, 18, 14, -1]},
         wait(3), {"op": "set", "id": "spout1", "targetDepth": 0.3}, {"op": "set", "id": "spout2", "targetDepth": 0.3},
         water("pond1", [2, 3, 0], 2.0, 1.0), water("pond2", [2, 13, 1], 2.0, 1.0)]
    cells = [[6, 3, 0], [9, 3, 0], [10, 3, 0], [9, 2, 0], [9, 6, 0], [8, 6, 0], [10, 6, 0], [9, 8, 0], [8, 8, 0], [9, 9, 0],
             [12, 8, 0], [13, 8, 0], [14, 8, 0], [12, 7, 0], [12, 9, 0], [17, 8, -1], [3, 3, 0],
             [6, 13, 1], [9, 13, 1], [12, 13, 1], [13, 13, 1], [14, 13, 0], [9, 13, 0], [17, 13, -1], [3, 13, 1]]
    rows = [[y, 0, 20, 0] for y in range(0, 19)] + [[y, 14, 20, -1] for y in range(5, 17)] + [[y, 4, 15, 1] for y in (12, 13, 14)]
    objs = ["gate1", "gate2", "corner1", "corner2", "covered", "coveredPath", "end1", "drop2", "spout1", "spout2",
            "mis1", "mis2", "blocked", "dryIntake", "dryEnd"]
    probe = {"op": "probe", "cells": cells, "rows": rows, "objects": objs}
    plants = {"op": "plants", "rect": [16, 6, 19, 15, -1]}
    s += [{"op": "series", "id": "parts", "every": 25, "cells": [[13, 8, 0], [17, 8, -1], [12, 13, 1], [17, 13, -1], [3, 3, 0], [3, 13, 1]],
           "volumes": [[16, 6, 19, 10, -1], [16, 11, 19, 15, -1]]},
          {"op": "series", "id": "badwater", "every": 5, "cells": [[5, 3, 0], [6, 3, 0], [14, 8, 0]],
           "contamination": [[4, 3, 0], [5, 3, 0], [6, 3, 0], [14, 8, 0], [17, 8, -1], [12, 13, 1], [17, 13, -1]]},
          shot("parts_setup", [10, 9, 0], 28), wait(300), dict(probe, label="t300"), wait(600), dict(probe, label="t900"),
          dict(plants, label="plants_t900"),
          shot("parts_t900", [10, 9, 0], 28), shot("parts_corners", [9, 5, 0], 12, 55, 0), shot("parts_bridge", [10, 13, 0], 12, 35, 60),
          shot("parts_status_row", [6, 18, 0], 12, 50, 0)]
    s += [expect("water turns twice", "depth", [12, 8, 0], 0.01),
          expect("corner post dry", "depth", [10, 3, 0], None, 0.001),
          expect("vertical run sides dry", "depth", [8, 6, 0], None, 0.001),
          expect("covered segment carries water", "depth", [13, 8, 0], 0.01),
          expect("bridge carries water", "depth", [12, 13, 1], 0.01),
          expect("spout 1 holds the paddy", "depth", [17, 8, -1], 0.2, 0.45)]
    s += off("pond1", "pond2") + [water("pond1bad", [2, 3, 0], 2.0, 1.0, True), water("pond2bad", [2, 13, 1], 2.0, 1.0, True),
                                  wait(150), dict(probe, label="bad_t150"), wait(350), dict(probe, label="bad_t500"),
                                  dict(plants, label="plants_bad_t500"), shot("parts_badwater", [12, 10, 0], 22)]
    s += [expect("guarded paddy stays clean", "contamination", [17, 8, -1], None, 0.02)]
    s += off("pond1bad", "pond2bad") + [water("empty1", [2, 3, 0], -3.0), water("empty2", [2, 13, 1], -3.0), wait(300)]
    s += off("empty1", "empty2") + [dict(probe, label="emptied"), water("pond1", [2, 3, 0], 2.0, 1.0), water("pond2", [2, 13, 1], 2.0, 1.0),
                                    wait(400), dict(probe, label="clear_t400"), wait_hours(24), dict(plants, label="plants_end"),
                                    dict(probe, label="end")]
    s += [expect("guarded gate reopened", "depth", [12, 8, 0], 0.01)]
    request("parts", s, [21, 20], faction="Inkpaws")


# ---------------------------------------------------------------------------------------------------------------- scoop
def scoop():
    """Channel A (y=5, floor -2) with set throughflow: Scoop Wheel at x=12 lifting into a walled basin (floor 0, behind
    a +1 lip at y=6) and a Water Trip-Hammer at x=20. Flow steps 0 -> 0.3 -> 0.8 -> 1.6 -> 3.0.
    Loop B (closed channel y=14): a Scoop Wheel at x=12 lifts into basin y16..18 whose Flume Gate (9,16) returns the
    water by flume and a Flume Corner into the channel upstream at (4,14): is it self-sustaining after a kick?
    Then a Dew Collector over a temperate day and a drought day.
    """
    s = [flat(0, 3, 27, 7, 1), flat(0, 5, 27, 5, -2), flat(9, 6, 15, 11, 1), flat(10, 7, 14, 10, -1),
         flat(0, 13, 27, 15, 1), flat(0, 14, 27, 14, -2), flat(9, 15, 15, 19, 1), flat(10, 16, 14, 18, -1),
         flat(3, 15, 8, 17, 0), flat(5, 16, 9, 16, -1), flat(3, 16, 4, 17, -1), flat(4, 15, 4, 15, -1), wait(3),
         place("PandabornScoopWheel", [12, 5, -2], "Cw0", id="scoop"),
         place("PandabornTripHammer", [20, 5, -2], "Cw0", id="hammer"),
         place("PandabornScoopWheel", [12, 14, -2], "Cw0", id="loopScoop"),
         place("PandabornFlumeGate", [9, 16, -1], "Cw270", id="loopGate"), line("PandabornFlume", [8, 16, -1], 4, (-1, 0, 0), "Cw270"),
         place("PandabornFlumeCorner", [4, 16, -1], "Cw270", id="loopCorner"), place("PandabornFlume", [4, 15, -1], "Cw180", id="loopOut"),
         place("PandabornDewCollector", [22, 9, 0], "Cw0", id="dew"),
         shot("scoop_setup", [12, 10, 0], 28)]
    s += [water("fill", [6, 5, -2], 2.0, 0.8), water("fillB", [20, 14, -2], 2.0, 0.8), wait(150)] + off("fill", "fillB") + [wait(100)]
    cells = [[12, 5, -2], [6, 5, -2], [20, 5, -2], [12, 7, -1], [12, 9, -1]]
    loop_cells = [[12, 14, -2], [4, 14, -2], [6, 16, -1], [12, 16, -1]]
    objs = ["scoop", "hammer", "loopScoop", "loopGate", "loopOut", "dew"]
    vols = [[10, 7, 14, 10, -1], [10, 16, 14, 18, -1]]
    s += [{"op": "series", "id": "scoop", "every": 20, "cells": cells + loop_cells, "volumes": vols,
           "objects": ["scoop", "hammer", "loopScoop"]}]
    s += [wait(200), {"op": "probe", "label": "flow0", "cells": cells, "volumes": vols, "objects": objs}]
    for q in (0.3, 0.8, 1.6, 3.0):
        s += [water("in", [1, 5, -2], q, 1.6), water("out", [26, 5, -2], -q * 1.5), wait(250),
              {"op": "probe", "label": f"flow{q}", "cells": cells, "volumes": vols, "objects": objs}]
    s += [shot("scoop_running", [12, 6, -1], 16, 45, 60)]
    s += [expect("scoop wheel lifts in a strong current", "flowRate", id="scoop", mn=0.01)]
    s += off("in", "out")
    s += [water("kickIn", [1, 14, -2], 1.5, 1.6), water("kickOut", [26, 14, -2], -2.0), wait(250),
          {"op": "probe", "label": "loop_kicked", "cells": loop_cells, "volumes": vols, "objects": objs}]
    s += off("kickIn", "kickOut") + [wait(300), {"op": "probe", "label": "loop_t300", "cells": loop_cells, "volumes": vols, "objects": objs},
                                     wait(500), {"op": "probe", "label": "loop_t800", "cells": loop_cells, "volumes": vols, "objects": objs},
                                     shot("scoop_loop", [8, 15, 0], 18, 50, 20)]
    s += [{"op": "probe", "label": "dew_t0", "objects": ["dew"]}, {"op": "wait", "days": 1, "capSeconds": 400},
          {"op": "probe", "label": "dew_temperate_day", "objects": ["dew"]},
          {"op": "drought"}, {"op": "probe", "label": "dew_drought_start", "objects": ["dew"]},
          {"op": "wait", "days": 1, "capSeconds": 400},
          {"op": "probe", "label": "dew_drought_day", "objects": ["dew", "loopScoop"], "volumes": vols}]
    request("scoop", s, [28, 21])


# ---------------------------------------------------------------------------------------------------------------- crops
def crops(days_wet=3, days_dry=2, days_rewet=1.5, days_tap=1.5):
    """Paddy Spout cascade, crop-zone matrix, moisture reach, cistern tap.
    Reservoir y=0..3 (walls +2) -> Paddy Spout 1 (6,4) -> paddy 1 x2..13 y5..8 z-1 -> Spout 2 (6,9,-1) -> paddy 2
    y10..13 z-2 -> Spout 3 (6,14,-2) -> paddy 3 y15..17 z-3. Each crop planted in paddy 1, beside it at 1, 3, 5 and
    8 tiles east (x=15,17,19,22), and on far dry ground (x32..37, y18..21). A water strip (y=22, x24..33, floor -1,
    kept 0.15 deep) measures what a moist strip costs per day. Phases: wet, dry (spouts shut, paddies drained), rewet,
    short re-dry (does the dying countdown restart full?), then a workerless Cistern Tap pours Water goods onto the
    far dry zone.
    """
    s = [flat(1, -1, 11, 4, 2), flat(2, 0, 10, 3, 0), flat(6, 4, 6, 4, 0),
         flat(2, 5, 13, 8, -1), flat(6, 9, 6, 9, -1), flat(2, 10, 13, 13, -2), flat(6, 14, 6, 14, -2), flat(2, 15, 13, 17, -3),
         flat(24, 22, 33, 22, -1), flat(34, 17, 34, 17, -1), wait(3),
         place("PandabornPaddySpout", [6, 4, 0], "Cw0", id="spout1"),
         place("PandabornPaddySpout", [6, 9, -1], "Cw0", id="spout2"),
         place("PandabornPaddySpout", [6, 14, -2], "Cw0", id="spout3"),
         wait(3)] + [{"op": "set", "id": f"spout{i}", "targetDepth": 0.3} for i in (1, 2, 3)] + [
         water("reservoir", [6, 1, 0], 2.0, 0.8), water("strip", [24, 22, -1], 0.5, 0.15)]
    for x0, crop in ((3, PADDY), (8, MOIST), (11, DRY)):
        s += [{"op": "plant", "template": crop, "rect": [x0, 6, x0 + 1, 7, -1]}]
    s += [{"op": "plant", "template": PADDY, "rect": [4, 11, 5, 12, -2]}, {"op": "plant", "template": PADDY, "rect": [4, 16, 5, 16, -3]}]
    for x in (15, 17, 19, 22):
        s += [{"op": "plant", "template": MOIST, "at": [x, 5, 0]}, {"op": "plant", "template": DRY, "at": [x, 6, 0]},
              {"op": "plant", "template": PADDY, "at": [x, 7, 0]}]
    s += [{"op": "plant", "template": MOIST, "rect": [32, 18, 33, 18, 0]}, {"op": "plant", "template": DRY, "rect": [32, 20, 37, 20, 0]},
          {"op": "plant", "template": PADDY, "rect": [36, 18, 37, 18, 0]}]
    zones = {"rect": [0, 0, 39, 23, 0]}
    moist_rows = [[y, 0, 39, 0] for y in range(0, 24)]

    def snapshot(tag):
        return [{"op": "plants", "label": "zones_" + tag, **zones},
                {"op": "plants", "label": "p1_" + tag, "rect": [2, 5, 13, 8, -1]},
                {"op": "plants", "label": "p2_" + tag, "rect": [2, 10, 13, 13, -2]},
                {"op": "plants", "label": "p3_" + tag, "rect": [2, 15, 13, 17, -3]},
                {"op": "probe", "label": "water_" + tag, "rows": [[6, 0, 14, -1], [11, 0, 14, -2], [16, 0, 14, -3]],
                 "moistRows": moist_rows, "objects": ["spout1", "spout2", "spout3", "tap"]}]

    s += [shot("crops_setup", [16, 10, 0], 36),
          {"op": "series", "id": "paddies", "every": 40, "cells": [[6, 5, -1], [3, 7, -1], [13, 8, -1], [6, 10, -2], [3, 12, -2],
                                                                   [6, 15, -3], [3, 17, -3], [6, 2, 0], [28, 22, -1]],
           "objects": ["spout1", "tap"]}] + snapshot("d0")
    s += [wait_hours(12)] + snapshot("h12") + [shot("crops_h12", [8, 10, -1], 22, 55, 0)]
    s += [wait_hours(days_wet * 24 - 12)] + snapshot("wet")
    s += [expect("paddy 1 held at spout depth", "depth", [3, 7, -1], 0.2, 0.45),
          expect("paddy 2 held by cascade spout", "depth", [3, 12, -2], 0.2, 0.45),
          expect("paddy 3 held by cascade spout", "depth", [3, 16, -3], 0.2, 0.45),
          expect("paddy crop healthy in paddy", "healthy", template=PADDY, rect=[3, 6, 4, 7, -1], mn=4),
          shot("crops_wet", [16, 10, 0], 36), shot("crops_wet_paddy", [8, 10, -1], 16, 50, 0)]
    drains = [water(f"drain{i}", at, -1.0) for i, at in enumerate([[2, 5, -1], [13, 8, -1], [8, 7, -1], [2, 10, -2], [13, 13, -2],
                                                                     [2, 15, -3], [13, 17, -3]])]
    s += off("reservoir") + [{"op": "set", "id": f"spout{i}", "targetDepth": 0.0} for i in (1, 2, 3)] + drains
    s += [wait_hours(6)] + snapshot("dry_h6")
    s += [wait_hours(days_dry * 24 - 6)] + snapshot("dry") + [shot("crops_dry", [16, 10, 0], 36)]
    s += off(*[f"drain{i}" for i in range(7)])
    s += [water("reservoir", [6, 1, 0], 2.0, 0.8)] + [{"op": "set", "id": f"spout{i}", "targetDepth": 0.3} for i in (1, 2, 3)]
    s += [wait_hours(days_rewet * 24)] + snapshot("rewet")
    s += off("reservoir") + [{"op": "set", "id": f"spout{i}", "targetDepth": 0.0} for i in (1, 2, 3)] + drains
    s += [wait_hours(8)] + snapshot("redry_h8")
    s += [shot("crops_end", [16, 10, 0], 36), shot("crops_end_dry", [35, 19, 0], 14, 50, 0)]
    request("crops", s, [40, 24], real_seconds=3000)


# ---------------------------------------------------------------------------------------------------------------- district
def district():
    """Needs beavers: the area sits next to the district center, levelled to its doorstep, with a path to it.
    Treadwheel (3,2) facing the path row y=1: pit (3,3) floor -2 kept 1.5 deep; ledge basin x4..7 y4..6 floor +1.
    A water strip (y=6, x9..30, floor -1, kept 0.5 deep) keeps the plants' soil moist until it is switched off.
    Combined bamboo (cut + gather) at (11,7),(13,7) inside a cutting area; lumberjack and gatherer flags.
    Farmhouse (16,2) with Shoot Bamboo on planting-marked tiles x16..19 y7..8; Forester (22,2) with Timber Bamboo on
    planting-marked tiles x22..24 y7..8, plus one wild (unmarked) Timber Bamboo at (28,7) for spreading.
    After 2 days the strip is switched off so everything dries and dies; after 3 dry days it is switched back on to see
    who clears and replants the dead plants.
    """
    s = [{"op": "pathFromDistrict", "to": [1, 1, 0]},
         {"op": "placeLine", "template": "Path", "from": [1, 1, 0], "count": 30, "step": [1, 0, 0], "orientation": "Cw0"},
         flat(3, 3, 8, 7, 2), flat(4, 4, 7, 6, 1), flat(3, 3, 3, 3, -2),
         place("PandabornTreadwheel", [3, 2, 0], "Cw0", id="tread"),
         water("pit", [3, 3, -2], 1.0, 1.5),
         flat(9, 6, 30, 6, -1), water("strip", [20, 6, -1], 1.0, 0.5),
         place("LumberjackFlag.Folktails", [10, 2, 0], "Cw0", id="lumberjack"),
         place("GathererFlag.Folktails", [13, 2, 0], "Cw0", id="gatherer"),
         place("EfficientFarmHouse.Folktails", [16, 2, 0], "Cw0", id="farm"),
         place("Forester.Folktails", [22, 2, 0], "Cw0", id="forester"),
         {"op": "set", "id": "forester", "replantDeadTrees": True},
         {"op": "plant", "template": BAMBOO, "cells": [[11, 7, 0], [13, 7, 0]]},
         {"op": "markCut", "rect": [10, 7, 14, 9, 0]},
         {"op": "markPlant", "template": SHOOT, "rect": [16, 7, 19, 8, 0]},
         {"op": "plant", "template": SHOOT, "rect": [16, 7, 19, 7, 0]},
         {"op": "markPlant", "template": TIMBER, "rect": [22, 7, 24, 8, 0]},
         {"op": "plant", "template": TIMBER, "rect": [22, 7, 24, 7, 0]},
         {"op": "plant", "template": TIMBER, "at": [28, 7, 0]},
         {"op": "grow", "rect": [9, 7, 30, 9, 0], "progress": 1.0}]
    objs = ["tread", "lumberjack", "gatherer", "farm", "forester"]
    field = {"rect": [9, 5, 30, 10, 0]}
    goods = ["Log", "Berries", "Carrot"]
    s += [{"op": "series", "id": "tread", "every": 40, "cells": [[3, 3, -2], [5, 4, 1]], "volumes": [[4, 4, 7, 6, 1]], "objects": ["tread"]},
          shot("district_setup", [14, 5, 0], 32), {"op": "plants", "label": "plants_h0", **field},
          {"op": "probe", "label": "h0", "objects": objs, "goods": goods, "moistRows": [[y, 8, 30, 0] for y in range(3, 11)]}]
    t = 0
    for h in (6, 12, 24, 48):
        s += [wait_hours(h - t), {"op": "probe", "label": f"h{h}", "objects": objs, "goods": goods, "volumes": [[4, 4, 7, 6, 1]]},
              {"op": "plants", "label": f"plants_h{h}", **field}]
        t = h
        if h == 12:
            s += [shot("district_h12", [8, 4, 0], 16, 45, 10)]
    s += [expect("treadwheel lifted water", "volume", rect=[4, 4, 7, 6, 1], mn=0.05)]
    s += off("strip") + [water("stripDrain", [20, 6, -1], -2.0)]
    for h in (60, 72, 96, 120):
        s += [wait_hours(h - t), {"op": "plants", "label": f"plants_h{h}", **field},
              {"op": "probe", "label": f"h{h}", "objects": objs, "goods": goods, "moistRows": [[y, 8, 30, 0] for y in range(5, 10)]}]
        t = h
    s += [shot("district_dead", [20, 6, 0], 22)]
    s += off("stripDrain") + [water("strip", [20, 6, -1], 1.0, 0.5)]
    for h in (132, 144, 168):
        s += [wait_hours(h - t), {"op": "plants", "label": f"plants_h{h}", **field},
              {"op": "probe", "label": f"h{h}", "objects": objs, "goods": goods}]
        t = h
    s += [shot("district_end", [20, 6, 0], 22)]
    request("district", s, [32, 12], speed=5, real_seconds=3600, origin={"nearDistrict": True})


# ---------------------------------------------------------------------------------------------------------------- dew
def dew():
    """Dew Collector stock over one temperate day, then one drought day."""
    s = [place("PandabornDewCollector", [4, 4, 0], "Cw0", id="dew"), shot("dew_setup", [5, 5, 0], 14),
         {"op": "series", "id": "dew", "every": 64, "objects": ["dew"]},
         {"op": "probe", "label": "dew_t0", "objects": ["dew"]}, {"op": "wait", "days": 1, "capSeconds": 400},
         {"op": "probe", "label": "dew_temperate_day", "objects": ["dew"]},
         {"op": "drought"}, {"op": "probe", "label": "dew_drought_start", "objects": ["dew"]},
         {"op": "wait", "days": 1, "capSeconds": 400},
         {"op": "probe", "label": "dew_drought_day", "objects": ["dew"]}]
    request("dew", s, [10, 10], speed=10)


# ---------------------------------------------------------------------------------------------------------------- combo
def shift(steps, dy):
    """Moves every coordinate in a step list by dy tiles along y (to put two scenarios in one test area)."""
    out = []
    for st in steps:
        st = json.loads(json.dumps(st))
        for k in ("at", "from", "focus"):
            if k in st:
                st[k][1] += dy
        if "rect" in st:
            st["rect"][1] += dy
            st["rect"][3] += dy
        for k in ("cells", "contamination"):
            for c in st.get(k, []):
                c[1] += dy
        for v in st.get("volumes", []):
            v[1] += dy
            v[3] += dy
        for k in ("rows", "moistRows"):
            for r in st.get(k, []):
                r[0] += dy
        out.append(st)
    return out


def combo():
    """The scoop-wheel scenario (without its dew part) and the crops scenario in one game, to need one test slot."""
    sc = json.load(open(os.path.join(OUT, "scoop.json"), encoding="utf-8"))["water"]["steps"]
    cut = next(i for i, st in enumerate(sc) if st.get("label") == "dew_t0")
    cr = json.load(open(os.path.join(OUT, "crops.json"), encoding="utf-8"))["water"]["steps"]
    steps = shift(sc[:cut], 26) + [{"op": "note", "text": "--- crops part ---"}] + cr
    request("combo", steps, [40, 48], real_seconds=4200)


# ---------------------------------------------------------------------------------------------------------------- district2
def district2():
    """Second district run, fixing the first: storages for Log, Berries and Carrot (yield workers idle without them),
    the water strip north of the plants (y=10) so the fields are reachable from the path, and the Treadwheel ledge one
    block below its outlet. Same plants and phases, shorter: wet to h24, dry to h96, rewet to h144."""
    s = [{"op": "pathFromDistrict", "to": [1, 1, 0]},
         {"op": "placeLine", "template": "Path", "from": [1, 1, 0], "count": 30, "step": [1, 0, 0], "orientation": "Cw0"},
         flat(3, 3, 8, 7, 1), flat(4, 4, 7, 6, 0), flat(3, 3, 3, 3, -2), flat(9, 10, 30, 10, -1), wait(3),
         place("PandabornTreadwheel", [3, 2, 0], "Cw0", id="tread"),
         water("pit", [3, 3, -2], 1.0, 1.5), water("strip", [20, 10, -1], 1.0, 0.5),
         place("LumberjackFlag.Folktails", [10, 2, 0], "Cw0", id="lumberjack"),
         place("GathererFlag.Folktails", [13, 2, 0], "Cw0", id="gatherer"),
         place("EfficientFarmHouse.Folktails", [16, 2, 0], "Cw0", id="farm"),
         place("Forester.Folktails", [22, 2, 0], "Cw0", id="forester"),
         {"op": "set", "id": "forester", "replantDeadTrees": True},
         place("SmallWarehouse.Folktails", [26, 2, 0], "Cw0", id="storeCarrot"), {"op": "set", "id": "storeCarrot", "allowGood": "Carrot"},
         place("SmallWarehouse.Folktails", [27, 2, 0], "Cw0", id="storeBerries"), {"op": "set", "id": "storeBerries", "allowGood": "Berries"},
         place("SmallPile.Folktails", [28, 2, 0], "Cw0", id="storeLog"), {"op": "set", "id": "storeLog", "allowGood": "Log"},
         {"op": "plant", "template": BAMBOO, "cells": [[11, 7, 0], [13, 7, 0]]},
         {"op": "markCut", "rect": [10, 6, 14, 9, 0]},
         {"op": "markPlant", "template": SHOOT, "rect": [16, 7, 19, 8, 0]},
         {"op": "plant", "template": SHOOT, "rect": [16, 7, 19, 7, 0]},
         {"op": "markPlant", "template": TIMBER, "rect": [22, 7, 24, 8, 0]},
         {"op": "plant", "template": TIMBER, "rect": [22, 7, 24, 7, 0]},
         {"op": "plant", "template": TIMBER, "at": [28, 7, 0]},
         {"op": "grow", "rect": [9, 6, 30, 9, 0], "progress": 1.0}]
    objs = ["tread", "lumberjack", "gatherer", "farm", "forester"]
    field = {"rect": [9, 5, 30, 9, 0]}
    goods = ["Log", "Berries", "Carrot"]
    s += [{"op": "series", "id": "tread", "every": 40, "cells": [[3, 3, -2], [5, 4, 0]], "volumes": [[4, 4, 7, 6, 0]], "objects": ["tread"]},
          shot("district2_setup", [14, 5, 0], 32), {"op": "plants", "label": "plants_h0", **field},
          {"op": "probe", "label": "h0", "objects": objs, "goods": goods}]
    t = 0
    for h in (4, 8, 12, 24):
        s += [wait_hours(h - t), {"op": "probe", "label": f"h{h}", "objects": objs, "goods": goods, "volumes": [[4, 4, 7, 6, 0]]},
              {"op": "plants", "label": f"plants_h{h}", **field}]
        t = h
        if h == 8:
            s += [shot("district2_h8", [8, 4, 0], 16, 45, 10), shot("district2_grove_h8", [12, 7, 0], 12, 45, 200)]
    s += [expect("treadwheel lifted water", "volume", rect=[4, 4, 7, 6, 0], mn=0.05)]
    s += off("strip") + [water("stripDrain", [20, 10, -1], -2.0)]
    for h in (48, 72, 96):
        s += [wait_hours(h - t), {"op": "plants", "label": f"plants_h{h}", **field},
              {"op": "probe", "label": f"h{h}", "objects": objs, "goods": goods}]
        t = h
    s += [shot("district2_dead", [20, 6, 0], 22)]
    s += off("stripDrain") + [water("strip", [20, 10, -1], 1.0, 0.5)]
    for h in (108, 120, 144):
        s += [wait_hours(h - t), {"op": "plants", "label": f"plants_h{h}", **field},
              {"op": "probe", "label": f"h{h}", "objects": objs, "goods": goods}]
        t = h
    s += [shot("district2_end", [20, 6, 0], 22)]
    request("district2", s, [32, 12], speed=5, real_seconds=3600, origin={"nearDistrict": True})


# ================================================================================================ phase 2: Inkpaws + module
CABBAGE, RICE, TEA = "PandabornCabbage.Inkpaws", "PandabornRice.Inkpaws", "PandabornTeaBush.Inkpaws"
DEV_SWITCH = r"E:\PandabornDev\build\proto\water\pandaborn.dev.txt"
OWN = ["PandabornFactions", "PandabornDevHarness", "Inkpaws", "Pandaborn.", "PandabornProto"]


def request2(name, steps, reload, area, speed, real_seconds, origin, **extra):
    """An Inkpaws request for the water dev mod (run with -Faction Inkpaws -DisableMods JigglyPanda.PandabornFactions
    -ExtraMods E:\\PandabornDev\\build\\proto\\water -SaveAndReload)."""
    water_spec = {"name": name, "speed": speed, "area": area, "origin": origin, "flattenMargin": 2,
                  "steps": steps, "reloadSteps": reload}
    water_spec.update(extra)
    r = {"faction": "Inkpaws", "map": "Plains", "speed": 0, "batchControl": False,
         "run": {"realSeconds": real_seconds, "settleSeconds": 2},
         "screenshots": [{"name": "screen_end", "kind": "screen", "at": "end"}],
         "ownPatterns": OWN, "water": water_spec}
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(r, f, indent=1)
        f.write("\n")


def w1():
    """Inkpaws (generated build + the module), next to the district; saved, reloaded with the module on.
    L2: plateau pond (floor +1) -> Flume Gate g2 (6,8,+1) -> Flume Bridges x7..20 on y=8 (flow at +1) with a Bridge span
    over L1 at (12,8); L2 pours over basin B2 (x21..24, floor -1, kept at 0.3).
    L1: pond (x11..13 y3..5) -> Flume Gate g1 (12,6) -> Flumes (12,7..12) north, under the span -> Paddy Spout (12,13)
    -> paddy x10..14 y14..17 (floor -1) with rice.
    Channel y=20 (floor -2) with a current; Scoop Wheel (16,20,-2) lifts into basin x15..17 y22..24 (floor -1).
    Beavers: Cistern Tap (26,2) with a worker over a pit (x25..27 y3..5, floor -1); farmhouse (29,2) with a cabbage field
    in a shallow pit (x28..33 y7..8, floor -1) kept moist by a strip (y=10). The field is flooded h6..h66 (2.5 days; the
    cabbage dies after 2 days under water), then drained: do farmers clear and replant?
    Before saving, g1 is set to 0.45 m3/s with the badwater guard off; after reload both must have survived.
    """
    s = [{"op": "pathFromDistrict", "to": [1, 1, 0]},
         {"op": "placeLine", "template": "Path", "from": [1, 1, 0], "count": 34, "step": [1, 0, 0], "orientation": "Cw0"},
         flat(1, 5, 6, 11, 3), flat(2, 6, 5, 10, 1), flat(6, 8, 6, 8, 1), flat(21, 6, 24, 10, -1),
         flat(10, 2, 14, 6, 2), flat(11, 3, 13, 5, 0), flat(12, 6, 12, 6, 0), flat(10, 14, 14, 17, -1),
         flat(0, 19, 31, 21, 1), flat(0, 20, 31, 20, -2), flat(14, 21, 18, 25, 1), flat(15, 22, 17, 24, -1),
         flat(25, 3, 27, 5, -1), flat(28, 7, 33, 8, -1), flat(26, 10, 34, 10, -1), wait(3),
         place("PandabornFlumeGate", [6, 8, 1], "Cw90", id="g2"),
         line("PandabornFlumeBridge", [7, 8, 0], 5, prefix="br"),
         place("PandabornFlumeBridgeSpan", [12, 8, 0], "Cw90", id="span"),
         line("PandabornFlumeBridge", [13, 8, 0], 8, prefix="bs"),
         place("PandabornFlumeGate", [12, 6, 0], "Cw0", id="g1"),
         line("PandabornFlume", [12, 7, 0], 6, (0, 1, 0), "Cw0", prefix="f"),
         place("PandabornPaddySpout", [12, 13, 0], "Cw0", id="sp"),
         place("PandabornScoopWheel", [16, 20, -2], "Cw0", id="sc"),
         place("PandabornCisternTap", [26, 2, 0], "Cw0", id="tap"),
         place("EfficientFarmHouse.Inkpaws", [29, 2, 0], "Cw0", id="farm"),
         place("SmallWarehouse.Inkpaws", [33, 2, 0], "Cw0", id="store"), {"op": "set", "id": "store", "allowGood": "PandabornCabbage"},
         # stairs down into the field pit (run water-w1-0809: a pit with no way down is out of the farmers' reach);
         # both orientations, one of them climbs towards the farmhouse
         place("Stairs.Inkpaws", [28, 7, -1], "Cw0", id="stairsA"), place("Stairs.Inkpaws", [33, 7, -1], "Cw180", id="stairsB"),
         wait(3), {"op": "set", "id": "sp", "targetDepth": 0.3},
         {"op": "plant", "template": RICE, "rect": [11, 15, 13, 16, -1]},
         {"op": "markPlant", "template": CABBAGE, "rect": [28, 7, 33, 8, -1]},
         {"op": "plant", "template": CABBAGE, "rect": [28, 7, 33, 8, -1]},
         {"op": "grow", "rect": [28, 7, 33, 8, -1], "progress": 0.6},
         water("p1", [12, 4, 0], 2.0, 0.8), water("p2", [3, 8, 1], 2.0, 0.8), water("keepB2", [23, 8, -1], -3.0, 0.3),
         water("chIn", [1, 20, -2], 1.6, 1.6), water("chOut", [30, 20, -2], -2.4), water("strip", [30, 10, -1], 1.0, 0.5)]
    objs = ["g1", "g2", "span", "f0", "f5", "sp", "sc", "tap", "farm", "br0", "bs7", "stairsA", "stairsB"]
    cells = [[12, 7, 0], [12, 8, 0], [12, 10, 0], [11, 10, 0], [13, 10, 0], [12, 8, 1], [9, 8, 1], [9, 8, 0], [9, 7, 0],
             [19, 8, 1], [22, 8, -1], [12, 15, -1], [16, 20, -2], [16, 23, -1], [26, 4, -1], [30, 7, -1], [5, 8, 1], [11, 6, 0]]
    vols = [[15, 22, 17, 24, -1], [25, 3, 27, 5, -1], [21, 6, 24, 10, -1]]
    probe = {"op": "probe", "cells": cells, "objects": objs, "volumes": vols, "goods": ["Water", "PandabornCabbage"]}
    field = {"rect": [28, 7, 33, 8, -1]}
    s += [{"op": "series", "id": "w1", "every": 40, "cells": [[12, 10, 0], [12, 8, 1], [12, 15, -1], [16, 23, -1], [26, 4, -1], [30, 7, -1]],
           "volumes": vols[:2], "objects": ["sc", "tap"]},
          shot("w1_setup", [16, 12, 0], 36), wait(300), dict(probe, label="t300"),
          shot("w1_crossing", [12, 8, 0], 12, 40, 30), shot("w1_t300", [16, 12, 0], 36)]
    s += [expect("L1 flume carries water", "depth", [12, 10, 0], 0.01),
          expect("L1 side dry", "depth", [11, 10, 0], None, 0.001),
          expect("bridge carries water over L1", "depth", [12, 8, 1], 0.01),
          expect("flume under the bridge carries water", "depth", [12, 8, 0], 0.01),
          expect("no water beside the bridge leg", "depth", [9, 7, 0], None, 0.001),
          expect("bridge end pours into the basin", "depth", [22, 8, -1], 0.05),
          expect("spout holds the paddy", "depth", [12, 15, -1], 0.2, 0.45),
          expect("scoop wheel lifts", "volume", rect=[15, 22, 17, 24, -1], mn=0.05)]
    s += [{"op": "uiText", "id": i, "label": "ui_" + i} for i in ("g1", "sp", "sc", "tap")]
    t = 0
    for h, act in ((2, "flood"), (24, None), (48, None), (58, "drain"), (62, "stop"), (72, None), (84, None)):
        s += [wait_hours(h - t), {"op": "plants", "label": f"field_h{h}", **field}, dict(probe, label=f"h{h}")]
        t = h
        if act == "flood":
            s += [water("flood", [30, 8, -1], 0.6, 0.3)]
        elif act == "drain":
            s += off("flood") + [water("dr1", [28, 7, -1], -1.0), water("dr2", [33, 8, -1], -1.0)]
        elif act == "stop":
            s += off("dr1", "dr2")
        if h == 48:
            s += [shot("w1_flooded", [30, 6, 0], 16, 50, 0)]
        if h == 24:
            s += [{"op": "uiText", "id": "tap", "label": "ui_tap_h24"}]
    s += [expect("cabbage replanted after the flood", "healthy", template=CABBAGE, rect=field["rect"], mn=5),
          shot("w1_field", [30, 6, 0], 16, 50, 0), shot("w1_tap", [26, 3, 0], 12, 45, 30), shot("w1_end", [16, 12, 0], 36),
          {"op": "invoke", "id": "g1", "component": "FlumeGate", "method": "SetFlow", "args": [0.45]},
          {"op": "invoke", "id": "g1", "component": "FlumeGate", "method": "SetGuardEnabled", "args": [False]},
          wait(30), dict(probe, label="before_save")]
    binds = [{"op": "bind", "id": k, "at": at} for k, at in
             (("g1", [12, 6, 0]), ("g2", [6, 8, 1]), ("sp", [12, 13, 0]), ("sc", [16, 20, 0]), ("tap", [26, 2, 0]),
              ("span", [12, 8, 1]), ("f0", [12, 7, 0]), ("br0", [7, 8, 1]))]
    rprobe = {"op": "probe", "cells": cells, "objects": ["g1", "g2", "sp", "sc", "tap", "span", "f0", "br0"], "volumes": vols}
    reload = binds + [dict(rprobe, label="reload_t0"),
                      water("p1", [12, 4, 0], 2.0, 0.8), water("p2", [3, 8, 1], 2.0, 0.8), water("keepB2", [23, 8, -1], -3.0, 0.3),
                      water("chIn", [1, 20, -2], 1.6, 1.6), water("chOut", [30, 20, -2], -2.4), wait(300),
                      dict(rprobe, label="reload_t300"),
                      expect("after reload: L1 flume carries water", "depth", [12, 10, 0], 0.01),
                      expect("after reload: L1 side dry", "depth", [11, 10, 0], None, 0.001),
                      expect("after reload: bridge carries water", "depth", [12, 8, 1], 0.01),
                      expect("after reload: spout holds the paddy", "depth", [12, 15, -1], 0.2, 0.45),
                      expect("after reload: scoop wheel lifts", "volume", rect=[15, 22, 17, 24, -1], mn=0.05),
                      shot("w1_reload", [16, 12, 0], 36)]
    reload += [{"op": "uiText", "id": i, "label": "reload_ui_" + i} for i in ("g1", "sp", "sc")]
    request2("w1", s, reload, [36, 26], 5, 4200, {"nearDistrict": True})


def w2():
    """Inkpaws with TimberCommons switched off for the run; saved, then reloaded with the module's API check failing
    (dev switch "simulate-missing-api: Water", the same path as an old game: the module is not loaded).
    Mini line: pond -> Flume Gate (4,4) -> Flumes x5..9 -> Paddy Spout (10,4) -> paddy x11..13 y3..5 (floor -1).
    Channel y=10 with a current; Scoop Wheel (8,10,-2) lifts into basin x7..9 y12..14 (floor -1).
    Dry-crop rule: rows of the test dry crop (DaysToDieWet 3) and the catalogue tea bush (2):
    D1 truly dry (y2..3, 9+ tiles from any water); D2 two tiles from a strip that runs 36 h, then is drained;
    D3 two tiles from a strip that runs to the end.
    """
    s = [flat(0, 2, 4, 6, 2), flat(1, 3, 3, 5, 0), flat(4, 4, 4, 4, 0), flat(11, 3, 13, 5, -1),
         flat(0, 9, 22, 11, 1), flat(0, 10, 22, 10, -2), flat(6, 11, 10, 15, 1), flat(7, 12, 9, 14, -1),
         flat(28, 12, 38, 12, -1), flat(28, 19, 38, 19, -1), wait(3),
         place("PandabornFlumeGate", [4, 4, 0], "Cw90", id="g"), line("PandabornFlume", [5, 4, 0], 5, prefix="f"),
         place("PandabornPaddySpout", [10, 4, 0], "Cw90", id="sp"),
         place("PandabornScoopWheel", [8, 10, -2], "Cw0", id="sc"), wait(3), {"op": "set", "id": "sp", "targetDepth": 0.3}]
    for y in (2, 3, 10, 17):
        s += [{"op": "plant", "template": DRY, "rect": [30, y, 33, y, 0]}, {"op": "plant", "template": TEA, "rect": [34, y, 37, y, 0]}]
    s += [water("p", [2, 4, 0], 2.0, 0.8), water("chIn", [1, 10, -2], 1.6, 1.6), water("chOut", [21, 10, -2], -2.4),
          water("s2", [33, 12, -1], 1.0, 0.5), water("s3", [33, 19, -1], 1.0, 0.5)]
    dry = {"op": "plants", "rect": [28, 0, 39, 20, 0]}
    cells = [[5, 4, 0], [8, 4, 0], [8, 3, 0], [8, 5, 0], [5, 3, 0], [12, 4, -1], [14, 4, 0], [3, 4, 0], [8, 10, -2], [8, 13, -1]]
    probe = {"op": "probe", "cells": cells, "objects": ["g", "sp", "sc", "f0", "f4"], "volumes": [[7, 12, 9, 14, -1], [11, 3, 13, 5, -1]],
             "moistRows": [[y, 28, 39, 0] for y in (2, 3, 10, 17)]}
    s += [shot("w2_setup", [18, 10, 0], 34), wait(300), dict(probe, label="t300"), dict(dry, label="dry_t300"),
          expect("flume carries water (TimberCommons off)", "depth", [8, 4, 0], 0.01),
          expect("flume side dry (TimberCommons off)", "depth", [8, 5, 0], None, 0.001),
          expect("scoop wheel lifts (TimberCommons off)", "volume", rect=[7, 12, 9, 14, -1], mn=0.05),
          {"op": "uiText", "id": "g", "label": "ui_g"}, {"op": "uiText", "id": "sc", "label": "ui_sc"}]
    t = 0
    for h in (12, 24, 36, 48, 60, 72, 84, 96, 120):
        s += [wait_hours(h - t), dict(dry, label=f"dry_h{h}"), dict(probe, label=f"h{h}")]
        t = h
        if h == 36:
            s += off("s2") + [water("d2", [33, 12, -1], -1.0)]
        if h == 48:
            s += off("d2")
    s += [expect("dry crop thrives on truly dry ground", "healthy", template=DRY, rect=[30, 2, 33, 3, 0], mn=8),
          expect("dry crop survives 36 h of wet roots", "healthy", template=DRY, rect=[30, 10, 33, 10, 0], mn=3),
          expect("dry crop dies after 5 days of wet roots", "dead", template=DRY, rect=[30, 17, 33, 17, 0], mn=3),
          shot("w2_dry", [33, 10, 0], 22, 55, 0), shot("w2_end", [18, 10, 0], 34),
          dict(probe, label="before_save")]
    binds = [{"op": "bind", "id": k, "at": at} for k, at in (("g", [4, 4, 0]), ("sp", [10, 4, 0]), ("sc", [8, 10, 0]), ("f0", [5, 4, 0]), ("f4", [9, 4, 0]))]
    reload = binds + [dict(probe, label="moduleoff_t0"),
                      water("p", [2, 4, 0], 2.0, 0.8), water("chIn", [1, 10, -2], 1.6, 1.6), water("chOut", [21, 10, -2], -2.4),
                      wait(400), dict(probe, label="moduleoff_t400"), shot("w2_moduleoff", [8, 6, 0], 20, 50, 20),
                      expect("module off: nothing in the flume", "depth", [8, 4, 0], None, 0.001),
                      expect("module off: nothing beside the gate", "depth", [5, 3, 0], None, 0.001),
                      expect("module off: nothing beside the flume", "depth", [8, 5, 0], None, 0.001),
                      expect("module off: the pond still holds", "depth", [2, 4, 0], 0.3),
                      {"op": "uiText", "id": "g", "label": "moduleoff_ui_g"}, {"op": "uiText", "id": "sc", "label": "moduleoff_ui_sc"}]
    request2("w2", s, reload, [40, 22], 7, 4200, "auto",
             devSwitchFile=DEV_SWITCH, devSwitchNextLaunch="simulate-missing-api: Water")


def w3():
    """First drought, as a player would meet it (DESIGN "first two hours": days 5-8, then the first drought).
    A current in channel y=1 turns a Scoop Wheel (13,1,-2) that lifts into a small basin x8..14 y3..5 (floor -1); a
    Flume Gate (11,6,-1) and 18 Flumes run north in a trench to a Paddy Spout (11,25,-1) over a rice paddy x8..14 y26..28.
    Along the flume: shoot bamboo 1-2 tiles west, timber bamboo 1-2 east, cabbage 4-5 east (y14..23).
    Day 1 everything runs. Then drought: the current stops (sources off) and the weather turns. What dries in what order?
    Two days into the drought a Cistern Tap (8,2) with a worker gets 40 Water (one small cistern) and pours it into the
    basin: what does it keep alive, and for how long?
    """
    s = [{"op": "pathFromDistrict", "to": [8, 1, 0]},
         flat(10, 1, 29, 1, -2), flat(8, 3, 14, 5, -1), flat(11, 6, 11, 25, -1), flat(8, 26, 14, 28, -2), wait(3),
         place("PandabornScoopWheel", [13, 1, -2], "Cw0", id="sc"),
         place("PandabornFlumeGate", [11, 6, -1], "Cw0", id="g"),
         line("PandabornFlume", [11, 7, -1], 18, (0, 1, 0), "Cw0", prefix="f"),
         place("PandabornPaddySpout", [11, 25, -1], "Cw0", id="sp"),
         place("PandabornCisternTap", [8, 2, 0], "Cw0", id="tap"),
         wait(3), {"op": "set", "id": "sp", "targetDepth": 0.3},
         {"op": "plant", "template": "PandabornShootBamboo.Inkpaws", "rect": [9, 14, 10, 23, 0]},
         {"op": "plant", "template": "PandabornTimberBamboo.Inkpaws", "rect": [12, 14, 13, 23, 0]},
         {"op": "plant", "template": CABBAGE, "rect": [15, 14, 16, 23, 0]},
         {"op": "plant", "template": RICE, "rect": [9, 27, 13, 27, -2]},
         {"op": "grow", "rect": [8, 14, 16, 27, -2], "progress": 0.5},
         water("chIn", [11, 1, -2], 1.6, 1.6), water("chOut", [28, 1, -2], -2.4)]
    cells = [[13, 1, -2], [11, 4, -1], [11, 7, -1], [11, 15, -1], [11, 24, -1], [11, 27, -2], [9, 18, 0], [16, 18, 0]]
    objs = ["sc", "g", "f0", "f17", "sp", "tap"]
    probe = {"op": "probe", "cells": cells, "objects": objs, "volumes": [[8, 3, 14, 5, -1], [8, 26, 14, 28, -2]],
             "moistRows": [[y, 0, 29, 0] for y in (8, 14, 18, 23)], "goods": ["Water"]}
    grove = {"op": "plants", "rect": [8, 13, 17, 28, -2]}
    s += [{"op": "series", "id": "w3", "every": 40, "cells": [[13, 1, -2], [11, 4, -1], [11, 15, -1], [11, 24, -1], [11, 27, -2]],
           "volumes": [[8, 3, 14, 5, -1]], "objects": ["sc", "tap"]},
          shot("w3_setup", [12, 14, 0], 34), wait(300), dict(probe, label="t300"),
          expect("scoop wheel feeds the line", "depth", [11, 15, -1], 0.01),
          {"op": "uiText", "id": "sc", "label": "ui_sc_running"}, {"op": "uiText", "id": "g", "label": "ui_g_running"},
          wait_hours(24), dict(probe, label="day1"), dict(grove, label="grove_day1"), shot("w3_day1", [12, 14, 0], 34)]
    s += [{"op": "drought"}] + off("chIn", "chOut") + [wait(60), dict(probe, label="drought_t60"),
          {"op": "uiText", "id": "sc", "label": "ui_sc_drought"}, {"op": "uiText", "id": "g", "label": "ui_g_drought"},
          {"op": "uiText", "id": "f17", "label": "ui_end_drought"}]
    t = 0
    for h in (2, 6, 12, 24, 36, 48):
        s += [wait_hours(h - t), dict(probe, label=f"d_h{h}"), dict(grove, label=f"grove_d_h{h}")]
        t = h
    s += [shot("w3_drought_h48", [12, 14, 0], 34),
          {"op": "giveGoods", "id": "tap", "good": "Water", "amount": 40}, {"op": "uiText", "id": "tap", "label": "ui_tap"}]
    for h in (52, 60, 72, 96, 120, 144):
        s += [wait_hours(h - t), dict(probe, label=f"d_h{h}"), dict(grove, label=f"grove_d_h{h}")]
        t = h
        if h == 72:
            s += [shot("w3_tap_h72", [12, 14, 0], 34)]
    s += [shot("w3_end", [12, 14, 0], 34)]
    request2("w3", s, [], [30, 30], 7, 3600, {"nearDistrict": True})


def w4():
    """Save and reload of standing water: run water-w1b-0934 showed that loading cuts the water out of every flume cell
    (the inert obstacle is re-added on load before the module lifts it), and the refill surge then over-filled the paddy.
    The module now saves each flow cell's depth and puts it back. Line A: pond with a high head (surface 1.6 above the
    flume bed, so the backed-up line stands more than one block deep) -> gate (12,6) -> 6 flumes -> spout -> paddy.
    Line B crosses over A on Bridges with a span at (12,8). Short: fill, save, reload, compare tick 0/1/30/300.
    """
    s = [flat(1, 5, 6, 11, 3), flat(2, 6, 5, 10, 1), flat(6, 8, 6, 8, 1), flat(21, 6, 24, 10, -1),
         flat(10, 2, 14, 6, 3), flat(11, 3, 13, 5, 0), flat(12, 6, 12, 6, 0), flat(10, 14, 14, 17, -1), wait(3),
         place("PandabornFlumeGate", [6, 8, 1], "Cw90", id="g2"),
         line("PandabornFlumeBridge", [7, 8, 0], 5, prefix="br"),
         place("PandabornFlumeBridgeSpan", [12, 8, 0], "Cw90", id="span"),
         line("PandabornFlumeBridge", [13, 8, 0], 8, prefix="bs"),
         place("PandabornFlumeGate", [12, 6, 0], "Cw0", id="g1"),
         line("PandabornFlume", [12, 7, 0], 6, (0, 1, 0), "Cw0", prefix="f"),
         place("PandabornPaddySpout", [12, 13, 0], "Cw0", id="sp"),
         wait(3), {"op": "set", "id": "sp", "targetDepth": 0.3},
         water("p1", [12, 4, 0], 2.0, 1.6), water("p2", [3, 8, 1], 2.0, 0.8), water("keepB2", [23, 8, -1], -3.0, 0.3)]
    cells = [[12, 7, 0], [12, 8, 0], [12, 10, 0], [12, 12, 0], [11, 10, 0], [13, 10, 0], [11, 7, 0], [13, 12, 0],
             [12, 10, 1], [11, 10, 1], [12, 8, 1], [9, 8, 1], [9, 8, 0], [12, 15, -1], [12, 13, 0]]
    objs = ["g1", "g2", "span", "f0", "f3", "f5", "sp", "br4", "bs0"]
    probe = {"op": "probe", "cells": cells, "objects": objs, "volumes": [[10, 14, 14, 17, -1], [12, 7, 12, 12, 0]]}
    s += [wait(600), dict(probe, label="t600"), shot("w4_before", [12, 10, 0], 14, 45, 30),
          expect("line A backed up", "depth", [12, 10, 0], 0.5),
          expect("line A sides dry", "depth", [11, 10, 0], None, 0.001),
          expect("crossing carries line B", "depth", [12, 8, 1], 0.01),
          expect("paddy at the spout depth", "depth", [12, 15, -1], 0.2, 0.45),
          wait(30), dict(probe, label="before_save")]
    binds = [{"op": "bind", "id": k, "at": at} for k, at in
             (("g1", [12, 6, 0]), ("g2", [6, 8, 1]), ("span", [12, 8, 1]), ("f0", [12, 7, 0]), ("f3", [12, 10, 0]),
              ("f5", [12, 12, 0]), ("sp", [12, 13, 0]), ("br4", [11, 8, 1]), ("bs0", [13, 8, 1]))]
    reload = binds + [dict(probe, label="reload_t0"),
                      water("p1", [12, 4, 0], 2.0, 1.6), water("p2", [3, 8, 1], 2.0, 0.8), water("keepB2", [23, 8, -1], -3.0, 0.3),
                      {"op": "wait", "ticks": 1, "capSeconds": 60}, dict(probe, label="reload_t1"),
                      {"op": "wait", "ticks": 2, "capSeconds": 60}, dict(probe, label="reload_t3"),
                      wait(30), dict(probe, label="reload_t33"),
                      expect("after reload: water back in the flume at once", "depth", [12, 10, 0], 0.5),
                      expect("after reload: sides dry", "depth", [11, 10, 0], None, 0.001),
                      expect("after reload: nothing on top beside", "depth", [11, 10, 1], None, 0.001),
                      wait(300), dict(probe, label="reload_t333"),
                      expect("after reload: paddy not over-filled", "depth", [12, 15, -1], 0.2, 0.45),
                      expect("after reload: crossing carries line B", "depth", [12, 8, 1], 0.01),
                      shot("w4_reload", [12, 10, 0], 14, 45, 30)]
    request2("w4", s, reload, [26, 20], 3, 1500, "auto")


if __name__ == "__main__":
    w4()
    w1()
    w2()
    w3()
    flume()
    longrun()
    parts()
    scoop()
    crops()
    district()
    dew()
    combo()
    district2()
    print("wrote", sorted(os.listdir(OUT)))
