"""Writes proto/models/tests/water.request.json: the flume set, spout and scoop wheel with real water (WaterLab)."""
import json
import os

T = lambda i: f"PandabornModel{i}.PandabornProto"  # noqa: E731
steps = []
A = steps.append
# --- 1. scoop wheel in a river (the water prototype's proven layout), its trough into a basin two levels up
A({"op": "flatten", "rect": [0, 3, 27, 7], "z": 1})
A({"op": "flatten", "rect": [0, 5, 27, 5], "z": -2})
A({"op": "flatten", "rect": [9, 6, 15, 11], "z": 1})
A({"op": "flatten", "rect": [10, 7, 14, 10], "z": 0})
A({"op": "place", "template": T("ScoopWheel"), "at": [12, 5, -2], "orientation": "Cw0", "id": "scoop"})
# --- 1b. the Bamboo Water Wheel in a two-wide river of its own (vanilla Water Wheel blocks: generator cells x+1)
A({"op": "flatten", "rect": [0, 0, 27, 1], "z": -2})
A({"op": "place", "template": T("BambooWaterWheel"), "at": [16, 0, -2], "orientation": "Cw0", "id": "wheel"})
# --- 2. a flume line from a pond on a terrace: gate, flume, two bridge pieces over a dip, flume, drop, flume, spout
#        into a field one level down, and a corner turning a branch
A({"op": "flatten", "rect": [0, 14, 27, 26], "z": 1})
A({"op": "flatten", "rect": [1, 17, 4, 21], "z": 0})          # pond, floor below the flume bed
A({"op": "flatten", "rect": [8, 17, 9, 21], "z": 0})          # dip under the bridge
A({"op": "flatten", "rect": [11, 15, 27, 26], "z": 0})        # lower terrace from the drop on
A({"op": "flatten", "rect": [16, 16, 23, 22], "z": -1})       # the paddy field
A({"op": "place", "template": T("FlumeGate"), "at": [5, 19, 1], "orientation": "Cw90", "id": "gate"})
A({"op": "place", "template": T("Flume"), "at": [6, 19, 1], "orientation": "Cw90", "id": "f1"})
A({"op": "place", "template": T("Flume"), "at": [7, 19, 1], "orientation": "Cw90", "id": "f2"})
A({"op": "place", "template": T("FlumeBridge"), "at": [8, 19, 0], "orientation": "Cw90", "id": "b1"})
A({"op": "place", "template": T("FlumeBridge"), "at": [9, 19, 0], "orientation": "Cw90", "id": "b2"})
A({"op": "place", "template": T("Flume"), "at": [10, 19, 1], "orientation": "Cw90", "id": "f3"})
A({"op": "place", "template": T("FlumeDrop"), "at": [11, 19, 0], "orientation": "Cw90", "id": "drop"})
A({"op": "place", "template": T("Flume"), "at": [13, 19, 0], "orientation": "Cw90", "id": "f4"})
A({"op": "place", "template": T("Flume"), "at": [14, 19, 0], "orientation": "Cw90", "id": "f5"})
A({"op": "place", "template": T("PaddySpout"), "at": [15, 19, 0], "orientation": "Cw90", "id": "spout"})
# walk-under check: a Moon Loft on the upper terrace, then Path tiles through the cells under it
A({"op": "place", "template": T("MoonLoft"), "at": [2, 23, 1], "orientation": "Cw0", "id": "loft"})
for y in (22, 23, 24, 25):
    A({"op": "place", "template": "Path", "at": [2, y, 1], "orientation": "Cw0", "id": f"pathUnder{y}"})
A({"op": "place", "template": "Path", "at": [3, 24, 1], "orientation": "Cw0", "id": "pathUnderB"})
A({"op": "place", "template": T("VillageHall"), "at": [22, 23, 0], "orientation": "Cw0", "id": "hall"})
A({"op": "shot", "name": "line_setup", "focus": [11, 19, 0], "distance": 22, "pitch": 50, "yaw": 15})
A({"op": "shot", "name": "scoop_setup", "focus": [12, 7, 0], "distance": 14, "pitch": 40, "yaw": 25})
A({"op": "water", "id": "pond", "at": [2, 19, 0], "rate": 0.8, "maxDepth": 1.32})
A({"op": "water", "id": "fill", "at": [6, 5, -2], "rate": 2.0, "maxDepth": 0.8})
A({"op": "wait", "ticks": 150, "capSeconds": 600})
A({"op": "waterOff", "id": "fill"})
A({"op": "water", "id": "in", "at": [1, 5, -2], "rate": 1.6, "maxDepth": 1.6})
A({"op": "water", "id": "out", "at": [26, 5, -2], "rate": -2.4})
A({"op": "water", "id": "in2", "at": [1, 0, -2], "rate": 1.6, "maxDepth": 1.6})
A({"op": "water", "id": "in3", "at": [1, 1, -2], "rate": 1.6, "maxDepth": 1.6})
A({"op": "water", "id": "out2", "at": [26, 0, -2], "rate": -2.4})
A({"op": "water", "id": "out3", "at": [26, 1, -2], "rate": -2.4})
A({"op": "wait", "ticks": 120, "capSeconds": 600})
cells = [[5, 19, 1], [6, 19, 1], [7, 19, 1], [8, 19, 1], [9, 19, 1], [10, 19, 1], [11, 19, 1], [12, 19, 0], [13, 19, 0],
         [14, 19, 0], [15, 19, 0], [16, 19, -1], [18, 19, -1], [12, 5, -2], [12, 7, 0]]
A({"op": "probe", "label": "running", "cells": cells, "volumes": [[10, 7, 14, 10, 0], [16, 16, 23, 22, -1]],
   "objects": ["scoop", "gate", "drop", "spout", "b1", "wheel", "hall"]})
A({"op": "shot", "name": "line_running", "focus": [11, 19, 0], "distance": 20, "pitch": 50, "yaw": 15})
A({"op": "shot", "name": "line_close_gate", "focus": [6, 19, 1], "distance": 7, "pitch": 40, "yaw": 30})
A({"op": "shot", "name": "line_close_bridge", "focus": [9, 19, 1], "distance": 7, "pitch": 35, "yaw": 30})
A({"op": "shot", "name": "line_close_drop", "focus": [12, 19, 0], "distance": 7, "pitch": 40, "yaw": 30})
A({"op": "shot", "name": "line_close_spout", "focus": [15, 19, 0], "distance": 7, "pitch": 45, "yaw": 30})
A({"op": "shot", "name": "scoop_a", "focus": [12, 5, 0], "distance": 7, "pitch": 40, "yaw": 160})
A({"op": "wait", "ticks": 3, "capSeconds": 60})
A({"op": "shot", "name": "scoop_b", "focus": [12, 5, 0], "distance": 7, "pitch": 40, "yaw": 160})
A({"op": "wait", "ticks": 3, "capSeconds": 60})
A({"op": "shot", "name": "scoop_c", "focus": [12, 5, 0], "distance": 7, "pitch": 40, "yaw": 160})
A({"op": "shot", "name": "wheel_a", "focus": [17, 1, 0], "distance": 8, "pitch": 40, "yaw": 160})
A({"op": "wait", "ticks": 3, "capSeconds": 60})
A({"op": "shot", "name": "wheel_b", "focus": [17, 1, 0], "distance": 8, "pitch": 40, "yaw": 160})
A({"op": "shot", "name": "loft_paths", "focus": [3, 24, 1], "distance": 8, "pitch": 35, "yaw": 30})
A({"op": "shot", "name": "hall_day", "focus": [23, 24, 1], "distance": 10, "pitch": 45, "yaw": 20})
A({"op": "shot", "name": "overview_all", "focus": [13, 13, 0], "distance": 34, "pitch": 55, "yaw": 15})
A({"op": "expect", "label": "scoop wheel lifts in a strong current", "what": "flowRate", "min": 0.01, "id": "scoop"})
req = {"faction": "Inkpaws", "map": "Plains", "speed": 0, "batchControl": False,
       "run": {"realSeconds": 900, "settleSeconds": 2},
       "screenshots": [{"name": "screen_end", "kind": "screen", "at": "end"}],
       "screenshotSize": [1600, 1000],
       "ownPatterns": ["PandabornFactions", "PandabornDevHarness", "Inkpaws", "PandabornProtoModels", "PandabornModel"],
       "water": {"name": "models", "speed": 7, "area": [28, 28], "origin": "auto", "flattenMargin": 2, "steps": steps}}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "water.request.json")
json.dump(req, open(out, "w"), indent=1)
print(out, len(steps))
