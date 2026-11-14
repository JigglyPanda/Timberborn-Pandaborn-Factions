"""Writes the plants prototype's test requests (proto/plants/tests/*.request.json) for tools/run_game_test.ps1.

    python -I proto/plants/tools/gen_requests.py

states.request.json   every plant in every state, 2x2 blocks per state (columns) and plant (rows), plus a paddy of rice
                      standing in 0.3 water; day shots, then 12 in-game hours later night shots. The water lab
                      (src/devharness/WaterLab.cs) levels the area, makes the water, spawns and grows plants and films;
                      the plant lab (proto/plants/src/PlantLab.cs) forces the states (alive, dying, dead, ripe, cut).
terrace.request.json  a mixed Sichuan terrace with real water and soil moisture: a paddy at the bottom, a moist bench of
                      bamboo, cabbage and persimmons along a channel, a dry upper bench of tea rows and pepper; normal game
                      camera, day and night.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.join(os.path.dirname(HERE), "tests")

PLANTS = [  # id, gatherable, tree
    ("PandabornTimberBamboo", True, True),
    ("PandabornPersimmonTree", True, True),
    ("PandabornTeaBush", True, False),
    ("PandabornShootBamboo", False, False),
    ("PandabornCabbage", False, False),
    ("PandabornRice", False, False),
    ("PandabornSichuanPepper", False, False),
]
# column x0 per state; every block is 2x2
COLUMNS = [("seedling", 0, False, "alive"), ("seedlingDry", 3, False, "dying"), ("seedlingDead", 6, False, "dead"),
           ("mature", 9, True, "alive"), ("ripe", 12, True, "ripe"), ("matureDry", 15, True, "dying"),
           ("matureDead", 18, True, "dead"), ("cut", 21, True, "cut")]
OWN = ["PandabornFactions", "PandabornDevHarness", "Inkpaws", "PandabornProtoPlants", "PandabornPlants"]


def shot(name, focus, distance, pitch=50, yaw=0, w=1600, h=900):
    return {"op": "shot", "name": name, "focus": focus, "distance": distance, "pitch": pitch, "yaw": yaw,
            "width": w, "height": h}


def states():
    steps, rules = [], []
    # paddy: a basin one block down with a constant-head source at 0.3
    steps.append({"op": "flatten", "rect": [27, 0, 34, 8], "z": -1})
    steps.append({"op": "wait", "ticks": 3, "capSeconds": 300})
    steps.append({"op": "water", "id": "paddy", "at": [30, 4, -1], "rate": 3.0, "maxDepth": 0.3})
    for i, (pid, gather, tree) in enumerate(PLANTS):
        t = pid + ".Inkpaws"
        y = 3 * i
        for name, x, grown, state in COLUMNS:
            if name == "ripe" and not gather:
                continue
            if name == "cut" and not tree:
                continue
            rect = [x, y, x + 1, y + 1]
            steps.append({"op": "plant", "template": t, "rect": rect})
            if grown:
                steps.append({"op": "grow", "template": t, "rect": rect, "progress": 1.0})
            rules.append({"template": t, "rect": rect, "state": state})
    # rice in the paddy: seedlings (left) and mature (right), real water, no forced state
    steps.append({"op": "plant", "template": "PandabornRice.Inkpaws", "rect": [28, 1, 30, 7], "z": -1})
    steps.append({"op": "plant", "template": "PandabornRice.Inkpaws", "rect": [31, 1, 33, 7], "z": -1})
    steps.append({"op": "grow", "template": "PandabornRice.Inkpaws", "rect": [31, 1, 33, 7], "z": -1, "progress": 1.0})
    steps.append({"op": "wait", "hours": 0.5, "speed": 3, "capSeconds": 300})
    steps.append({"op": "plants", "label": "paddyRice", "template": "PandabornRice.Inkpaws", "rect": [28, 1, 33, 7], "z": -1})
    steps.append({"op": "probe", "label": "paddyDepth", "at": [30, 4, -1]})

    def shots(tag):
        out = [shot("matrix_" + tag, [11, 10, 0], 44, pitch=55)]
        for i, (pid, _, tree) in enumerate(PLANTS):
            out.append(shot("row_%s_%s" % (pid.replace("Pandaborn", ""), tag), [11, 3 * i + 0.5, 0], 21 if tree else 15,
                            pitch=42 if tree else 48))
        out.append(shot("paddy_" + tag, [30.5, 4, -1], 13, pitch=52))
        out.append(shot("game_" + tag, [16, 9, 0], 30, pitch=58, yaw=25))
        return out
    steps += shots("day")
    steps.append({"op": "wait", "hours": 12.5, "speed": 7, "capSeconds": 900})
    steps += shots("night")
    steps.append({"op": "plants", "label": "end", "rect": [0, 0, 34, 21], "detail": False})
    return {
        "faction": "Inkpaws", "map": "Plains", "speed": 0, "batchControl": False,
        "run": {"realSeconds": 2400, "settleSeconds": 2},
        "screenshots": [{"name": "screen_end", "kind": "screen", "at": "end"}],
        "ownPatterns": OWN,
        "water": {"name": "plants-states", "speed": 7, "area": [36, 22], "origin": "auto", "flattenMargin": 2,
                  "steps": steps},
        "plantLab": {"rules": rules},
    }


def terrace():
    I = ".Inkpaws"
    steps = [
        {"op": "flatten", "rect": [0, 0, 29, 5], "z": -1},          # paddy basin
        {"op": "flatten", "rect": [0, 9, 29, 9], "z": -1},          # irrigation ditch across the middle bench
        {"op": "flatten", "rect": [0, 15, 29, 21], "z": 1},         # dry upper bench
        {"op": "wait", "ticks": 3, "capSeconds": 300},
        {"op": "water", "id": "paddyW", "at": [6, 2, -1], "rate": 3.0, "maxDepth": 0.3},
        {"op": "water", "id": "paddyE", "at": [22, 3, -1], "rate": 3.0, "maxDepth": 0.3},
        {"op": "water", "id": "ditchW", "at": [1, 9, -1], "rate": 1.5, "maxDepth": 0.3},
        {"op": "water", "id": "ditchE", "at": [28, 9, -1], "rate": 1.5, "maxDepth": 0.3},
        {"op": "water", "id": "paddyM", "at": [14, 2, -1], "rate": 3.0, "maxDepth": 0.3},
        {"op": "wait", "hours": 3.0, "speed": 7, "capSeconds": 400},
    ]
    plantings = [  # template, rect, z, grow
        ("PandabornRice", [1, 1, 18, 4], -1, True), ("PandabornRice", [20, 1, 28, 4], -1, False),
        ("PandabornShootBamboo", [1, 6, 8, 8], 0, True), ("PandabornCabbage", [10, 6, 17, 8], 0, True),
        ("PandabornTimberBamboo", [20, 6, 29, 8], 0, True), ("PandabornTimberBamboo", [20, 10, 29, 13], 0, True),
        ("PandabornShootBamboo", [10, 10, 13, 12], 0, False), ("PandabornCabbage", [14, 10, 17, 12], 0, False),
        ("PandabornTeaBush", [1, 16, 14, 16], 1, True), ("PandabornTeaBush", [1, 18, 14, 18], 1, True),
        ("PandabornTeaBush", [1, 20, 14, 20], 1, False), ("PandabornSichuanPepper", [17, 16, 28, 17], 1, True),
        ("PandabornSichuanPepper", [17, 19, 28, 20], 1, False),
    ]
    for t, rect, z, grow in plantings:
        steps.append({"op": "plant", "template": t + I, "rect": rect, "z": z})
        if grow:
            steps.append({"op": "grow", "template": t + I, "rect": rect, "z": z, "progress": 1.0})
    for x in (1, 4, 7):           # an orchard: persimmons every third cell
        for y in (10, 13):
            steps.append({"op": "plant", "template": "PandabornPersimmonTree" + I, "at": [x, y, 0]})
            steps.append({"op": "grow", "template": "PandabornPersimmonTree" + I, "rect": [x, y, x, y], "z": 0, "progress": 1.0})
    rules = [{"template": "PandabornTeaBush" + I, "rect": [0, 15, 29, 21], "state": "ripe"},
             {"template": "PandabornPersimmonTree" + I, "rect": [0, 10, 9, 13], "state": "ripe"},
             {"template": "PandabornTimberBamboo" + I, "rect": [19, 6, 29, 13], "state": "ripe"}]
    steps.append({"op": "wait", "hours": 0.5, "speed": 3, "capSeconds": 300})
    steps.append({"op": "plants", "label": "start", "rect": [0, 0, 29, 21], "detail": False})

    def shots(tag):
        return [shot("terrace_" + tag, [15, 11, 0], 34, pitch=55, yaw=20),
                shot("terrace_grove_" + tag, [23, 10, 0], 16, pitch=48, yaw=-30),
                shot("terrace_tea_" + tag, [9, 18, 1], 13, pitch=50, yaw=10),
                shot("terrace_paddy_" + tag, [12, 3, -1], 13, pitch=50, yaw=0),
                shot("terrace_orchard_" + tag, [6, 10, 0], 14, pitch=50, yaw=15),
                shot("terrace_low_" + tag, [15, 9, 0], 26, pitch=38, yaw=200)]
    steps += shots("day")
    steps.append({"op": "wait", "hours": 16.0, "speed": 7, "capSeconds": 1200})
    steps.append({"op": "plants", "label": "night", "rect": [0, 0, 29, 21], "detail": False})
    steps += shots("night")
    return {
        "faction": "Inkpaws", "map": "Plains", "speed": 0, "batchControl": False,
        "run": {"realSeconds": 2400, "settleSeconds": 2},
        "screenshots": [{"name": "screen_end", "kind": "screen", "at": "end"}],
        "ownPatterns": OWN,
        "water": {"name": "plants-terrace", "speed": 7, "area": [30, 22], "origin": "auto", "flattenMargin": 2,
                  "steps": steps},
        "plantLab": {"rules": rules},
    }


def pass2():
    """Second pass: the reworked persimmon (ripe and unripe orchards), rice heads, the tea's third ring, taller rice
    seedlings in deeper water, the dead trees' narrower colliders (blueprints load), and a REAL dry/dead sequence:
    a paddy drained at high speed (rice: dying at once, dead after the flood rule's 1.5 days) and tea planted on wet soil
    beside the water (arid rule: dying, dead after 2 days)."""
    I = ".Inkpaws"
    steps = [
        {"op": "flatten", "rect": [0, 0, 7, 4], "z": -1},           # paddy A: will be drained
        {"op": "flatten", "rect": [9, 0, 15, 4], "z": -1},          # paddy B: kept at 0.45
        {"op": "flatten", "rect": [0, 8, 12, 12], "z": 1},          # dry bench for tea
        {"op": "wait", "ticks": 3, "capSeconds": 300},
        {"op": "water", "id": "A", "at": [3, 2, -1], "rate": 3.0, "maxDepth": 0.3},
        {"op": "water", "id": "B1", "at": [10, 2, -1], "rate": 3.0, "maxDepth": 0.45},
        {"op": "water", "id": "B2", "at": [14, 2, -1], "rate": 3.0, "maxDepth": 0.45},
        {"op": "wait", "hours": 3.0, "speed": 7, "capSeconds": 400},
    ]
    plantings = [("PandabornRice", [1, 1, 6, 3], -1, True), ("PandabornRice", [10, 1, 14, 3], -1, False),
                 ("PandabornTeaBush", [0, 5, 7, 5], 0, True),                         # wet roots: will die
                 ("PandabornTeaBush", [1, 9, 11, 9], 1, True), ("PandabornTeaBush", [1, 11, 11, 11], 1, True),
                 ("PandabornPersimmonTree", [17, 0, 19, 2], 0, True), ("PandabornPersimmonTree", [21, 0, 23, 2], 0, True),
                 ("PandabornPersimmonTree", [17, 4, 19, 4], 0, True), ("PandabornTimberBamboo", [21, 4, 23, 4], 0, True)]
    for t, rect, z, grow in plantings:
        steps.append({"op": "plant", "template": t + I, "rect": rect, "z": z})
        if grow:
            steps.append({"op": "grow", "template": t + I, "rect": rect, "z": z, "progress": 1.0})
    rules = [{"template": "PandabornPersimmonTree" + I, "rect": [17, 0, 19, 2], "state": "ripe"},
             {"template": "PandabornTeaBush" + I, "rect": [1, 9, 11, 9], "state": "ripe"},
             {"template": "PandabornPersimmonTree" + I, "rect": [17, 4, 19, 4], "state": "dead"},
             {"template": "PandabornTimberBamboo" + I, "rect": [21, 4, 23, 4], "state": "dead"}]
    steps.append({"op": "wait", "hours": 0.5, "speed": 3, "capSeconds": 300})
    probes = lambda tag: [{"op": "plants", "label": "%s_%s" % (tag, n), "template": t + I, "rect": r, "z": z, "detail": False}
                          for n, t, r, z in (("drainedRice", "PandabornRice", [1, 1, 6, 3], -1),
                                             ("wetTea", "PandabornTeaBush", [0, 5, 7, 5], 0),
                                             ("deepSeedlings", "PandabornRice", [10, 1, 14, 3], -1),
                                             ("dryTea", "PandabornTeaBush", [1, 9, 11, 11], 1))]
    steps += probes("start")
    steps += [{"op": "probe", "label": "depthB", "at": [12, 2, -1]},
              shot("p2_overview_day", [12, 6, 0], 30, pitch=55),
              shot("p2_persimmon_day", [20, 2, 0], 22, pitch=55),       # the default camera's distance and pitch
              shot("p2_persimmon_close", [20, 2, 0], 11, pitch=45, yaw=20),
              shot("p2_rice_day", [8, 2, -1], 12, pitch=50),
              shot("p2_rice_close", [3.5, 2, -1], 5, pitch=45, yaw=15),
              shot("p2_tea_day", [6, 9, 1], 11, pitch=50)]
    # cut paddy A off and drain it at high speed
    steps += [{"op": "waterOff", "id": "A"}, {"op": "water", "id": "drainA", "at": [3, 2, -1], "rate": -6.0, "maxDepth": 0.0},
              {"op": "wait", "hours": 6.0, "speed": 7, "capSeconds": 600}]
    steps += probes("after6h")
    steps += [shot("p2_drying", [6, 3, 0], 13, pitch=50)]
    steps += [{"op": "wait", "hours": 42.0, "speed": 7, "capSeconds": 1500}]
    steps += probes("after48h")
    steps += [shot("p2_dead", [6, 3, 0], 13, pitch=50), shot("p2_overview_end", [12, 6, 0], 30, pitch=55)]
    return {
        "faction": "Inkpaws", "map": "Plains", "speed": 0, "batchControl": False,
        "run": {"realSeconds": 3000, "settleSeconds": 2},
        "screenshots": [{"name": "screen_end", "kind": "screen", "at": "end"}],
        "ownPatterns": OWN,
        "water": {"name": "plants-pass2", "speed": 7, "area": [26, 14], "origin": "auto", "flattenMargin": 2,
                  "steps": steps},
        "plantLab": {"rules": rules},
    }


def flowering():
    """Pass 3: the Great Flowering's art. Needs the events prototype for the twin templates
    (-ExtraMods E:\PandabornDev\build\proto\events,E:\PandabornDev\build\proto\plants). Twins are spawned
    directly (the events lane proves the mechanics); the plant lab forces buds, dying, dead and the cut stump."""
    I = ".Inkpaws"
    SB, SF, TB, TF = ("PandabornShootBamboo" + I, "PandabornShootBambooInFlower" + I, "PandabornTimberBamboo" + I,
                      "PandabornTimberBambooInFlower" + I)
    blocks = [  # template, rect, state
        (SB, [0, 0, 5, 3], "alive"), (SB, [0, 4, 5, 4], "buds"), (SF, [7, 0, 12, 4], "alive"),
        (SF, [14, 0, 16, 4], "dying"), (SF, [18, 0, 20, 4], "dead"),
        (TB, [0, 7, 4, 11], "alive"), (TF, [6, 7, 10, 11], "alive"), (TF, [12, 7, 14, 11], "dying"),
        (TF, [16, 7, 18, 11], "dead"), (TF, [20, 7, 21, 8], "cut")]
    steps, rules = [], []
    for t, rect, state in blocks:
        steps.append({"op": "plant", "template": t, "rect": rect})
        steps.append({"op": "grow", "template": t, "rect": rect, "progress": 1.0})
        if state in ("buds", "cut"):      # keep them healthy on the test's dry ground, then the state
            rules.append({"template": t, "rect": rect, "state": "alive"})
        rules.append({"template": t, "rect": rect, "state": state})
    steps.append({"op": "wait", "hours": 0.3, "speed": 3, "capSeconds": 300})
    steps.append({"op": "plants", "label": "all", "rect": [0, 0, 21, 11], "detail": False})
    steps += [shot("fl_overview", [10.5, 5.5, 0], 30, pitch=55),
              shot("fl_shoot_field", [9, 2, 0], 16, pitch=52),
              shot("fl_buds", [2.5, 4, 0], 6, pitch=45, yaw=15),
              shot("fl_timber_grove", [9.5, 9, 0], 22, pitch=52),
              shot("fl_timber_close", [8, 9, 0], 12, pitch=40, yaw=-20),
              shot("fl_low", [10, 6, 0], 22, pitch=35, yaw=200)]
    return {
        "faction": "Inkpaws", "map": "Plains", "speed": 0, "batchControl": False,
        "run": {"realSeconds": 900, "settleSeconds": 2},
        "screenshots": [{"name": "screen_end", "kind": "screen", "at": "end"}],
        "ownPatterns": OWN + ["PandabornProtoEvents"],
        "water": {"name": "plants-flowering", "speed": 5, "area": [22, 12], "origin": "auto", "flattenMargin": 2,
                  "steps": steps},
        "plantLab": {"rules": rules},
    }


def main():
    os.makedirs(TESTS, exist_ok=True)
    for name, fn in (("states", states), ("terrace", terrace), ("pass2", pass2), ("flowering", flowering)):
        p = os.path.join(TESTS, name + ".request.json")
        json.dump(fn(), open(p, "w"), indent=1)
        print(p)


if __name__ == "__main__":
    main()
