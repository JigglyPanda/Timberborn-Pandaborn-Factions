"""Writes proto/models/tests/lanterns.request.json: the warm-lantern check (pass 6) with the look bundle that has the
LanternPaperRed / LanternPaperAmber patches (look 2ea9691), run on a dev copy of the faction:

    proto/foundation/build.ps1 -Name models-look
    tools/run_game_test.ps1 -NoBuild -HarnessDir E:\\PandabornDev\\build\\PandabornDevHarness-models -Faction Inkpaws
        -DisableMods JigglyPanda.PandabornFactions
        -ExtraMods E:\\PandabornDev\\build\\proto\\models-look,E:\\PandabornDev\\build\\proto\\models
        -RequestJson proto/models/tests/lanterns.request.json -RunId models-lanterns-1

Night shots (the run ends in the dark, day ~1.84) of the Festival Square, Lantern Workshop, the three lantern
decorations, a Den and the Sky Lantern caught mid-rise (its one-shot rise started by the harness just before the end):
lanterns should glow red-orange, the Sky Lantern amber, windows still pale amber.
"""
import json
import os

T = lambda i: f"PandabornModel{i}.PandabornProto"  # noqa: E731
SEC_PER_HOUR = 6.8
RUN_HOURS = 16.0


def at(h):
    return round(h * SEC_PER_HOUR, 1)


ids = ["SkyLantern", "FestivalSquare", "LanternWorkshop", "StandingLantern", "HangingLantern", "StringLanterns",
       "Den", "Den", "Den"]
buildings = [T(i) for i in ids]
end = at(RUN_HOURS)
animations = [{"target": T("SkyLantern"), "at": end - 9.0, "name": "Default", "speed": 0.2, "looped": False}]
shots = [{"name": "day_overview", "kind": "overview", "at": "start"}]
for k, dt in enumerate((4.0, 6.0, 8.0)):
    shots.append({"name": f"SkyLantern_rise_night_{k}", "kind": "building", "target": T("SkyLantern"),
                  "at": str(end - 9.0 + dt), "front": True, "yaw": 25, "pitch": 18, "zoom": 0.55, "minDistance": 9.0})
shots.append({"name": "night_overview", "kind": "overview", "at": "end"})
for i in ("FestivalSquare", "LanternWorkshop", "StandingLantern", "HangingLantern", "StringLanterns", "Den",
          "SkyLantern"):
    md = 3.0 if i in ("StandingLantern", "HangingLantern", "StringLanterns") else 5.0
    for lit in (False, True):
        shots.append({"name": f"{i}_night" + ("_lit" if lit else ""), "kind": "building", "target": T(i), "at": "end",
                      "front": True, "yaw": 25, "pitch": 35, "zoom": 1.1, "minDistance": md, "lit": lit})
shots.append({"name": "night_screen", "kind": "screen", "at": "end"})
req = {"run": {"inGameHours": RUN_HOURS, "realSeconds": 600}, "speed": 3, "batchControl": False,
       "buildings": buildings, "animations": animations, "screenshots": shots, "screenshotSize": [1600, 1000],
       "ownPatterns": ["PandabornFactions", "PandabornDevHarness", "Inkpaws", "PandabornProtoModels", "PandabornModel"]}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "lanterns.request.json")
json.dump(req, open(out, "w"), indent=1)
print(out, len(buildings), len(shots))
