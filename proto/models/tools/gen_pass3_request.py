"""Writes proto/models/tests/pass3.request.json: every model placed finished, framed from its entrance side (front
view and a closer three-quarter view, minimum camera distance so small objects stay in frame), then night shots at
the end: homes and lit buildings unforced (occupants) and forced ("lit"), and three hammock frames in the evening."""
import json
import os

T = lambda i: f"PandabornModel{i}.PandabornProto"  # noqa: E731
ids = ["Den", "MoonLoft", "Hammock", "Teahouse", "Kindergarten", "CourtyardHouse", "TerraceHouse", "PaddyHouse",
       "NightBuildersPost", "NightCourierPost", "NightForagersPost", "StarTower", "FestivalSquare", "HotSpringBath",
       "InkStudio", "CisternLarge", "CisternMedium", "Cistern", "StandingLantern", "HangingLantern", "StringLanterns",
       "Flume", "FlumeGate", "FlumeBridge", "FlumeDrop", "FlumeCorner", "GreatSittingPanda", "SkyLantern"]
small = {"Hammock", "InkStudio", "Cistern", "StandingLantern", "HangingLantern", "StringLanterns", "Flume",
         "FlumeGate", "FlumeBridge", "NightForagersPost"}
buildings = [T(i) for i in ids] + [T("Den"), T("Den")]
shots = [{"name": "day_overview", "kind": "overview", "at": "start"}]
for i in ids:
    md = 3.0 if i in small else 6.0
    shots.append({"name": f"{i}_front", "kind": "building", "target": T(i), "at": "3", "front": True, "yaw": 0,
                  "pitch": 42, "zoom": 1.0, "minDistance": md})
    shots.append({"name": f"{i}_3q", "kind": "building", "target": T(i), "at": "4", "front": True, "yaw": 35,
                  "pitch": 30, "zoom": 1.25, "minDistance": md * 0.8})
for k, t in enumerate(("230", "231", "232")):
    shots.append({"name": f"hammock_evening_{k}", "kind": "building", "target": T("Hammock"), "at": t, "front": True,
                  "yaw": 30, "pitch": 30, "zoom": 1.1, "minDistance": 2.5})
shots.append({"name": "night_overview", "kind": "overview", "at": "end"})
for i in ("Den", "CourtyardHouse", "TerraceHouse", "MoonLoft", "Teahouse", "NightBuildersPost", "StarTower",
          "FestivalSquare", "StandingLantern", "SkyLantern"):
    shots.append({"name": f"{i}_night", "kind": "building", "target": T(i), "at": "end", "front": True, "yaw": 25,
                  "pitch": 35, "zoom": 1.1, "minDistance": 3.0 if i in small else 5.0})
    shots.append({"name": f"{i}_night_lit", "kind": "building", "target": T(i), "at": "end", "front": True, "yaw": 25,
                  "pitch": 35, "zoom": 1.1, "minDistance": 3.0 if i in small else 5.0, "lit": True})
shots.append({"name": "night_screen", "kind": "screen", "at": "end"})
req = {"run": {"inGameHours": 17.0, "realSeconds": 700}, "speed": 3, "batchControl": False, "buildings": buildings,
       "screenshots": shots, "screenshotSize": [1600, 1000],
       "ownPatterns": ["PandabornFactions", "PandabornDevHarness", "Inkpaws", "PandabornProtoModels", "PandabornModel",
                       "PandabornCodeDev"]}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "pass3.request.json")
json.dump(req, open(out, "w"), indent=1)
print(out, len(buildings), len(shots))
