"""Writes proto/models/tests/stages.request.json: construction stages, occupancy at night, and moving parts.

Unfinished buildings are placed first (close-up shots frame the first placed of each template) and filmed as the
builders raise them; finished Dens are there to be lived in so their windows light at night; the Kite Windmill and
the Hammock are filmed twice a few seconds apart to show their nodes moving.
"""
import json
import os

T = lambda i: f"PandabornModel{i}.PandabornProto"  # noqa: E731
staged = ["Den", "MoonLoft", "Steamer", "Teahouse", "Kindergarten", "PickleYard", "Hammock", "Cistern"]
buildings = [{"template": T(i), "finished": False} for i in staged]
buildings += [T("KiteWindmill"), "PandabornModelDen.PandabornProto", "PandabornModelDen.PandabornProto",
              T("BambooWaterWheel")]
shots = [{"name": "overview_start", "kind": "overview", "at": "start"}]
for t in ("start", "45", "100"):
    for i in staged:
        shots.append({"name": f"stage_{i}_{t}", "kind": "building", "target": T(i), "at": t, "zoom": 1.4})
for k, t in enumerate(("20", "22", "24")):
    shots.append({"name": f"kite_{k}", "kind": "building", "target": T("KiteWindmill"), "at": t, "zoom": 1.3})
shots += [{"name": "overview_end", "kind": "overview", "at": "end"}]
for i in staged:
    shots.append({"name": f"end_{i}", "kind": "building", "target": T(i), "at": "end", "zoom": 1.4})
shots.append({"name": "night_screen", "kind": "screen", "at": "end"})
req = {"run": {"inGameHours": 15.0, "realSeconds": 420}, "speed": 3, "batchControl": False,
       "buildings": buildings, "screenshots": shots, "screenshotSize": [1600, 1000],
       "ownPatterns": ["PandabornFactions", "PandabornDevHarness", "Inkpaws", "PandabornProtoModels", "PandabornModel"]}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "stages.request.json")
json.dump(req, open(out, "w"), indent=1)
print(out, len(buildings), len(shots))
