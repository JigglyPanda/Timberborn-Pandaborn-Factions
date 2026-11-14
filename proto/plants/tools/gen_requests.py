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


def main():
    os.makedirs(TESTS, exist_ok=True)
    for name, fn in (("states", states), ("terrace", terrace)):
        p = os.path.join(TESTS, name + ".request.json")
        json.dump(fn(), open(p, "w"), indent=1)
        print(p)


if __name__ == "__main__":
    main()
