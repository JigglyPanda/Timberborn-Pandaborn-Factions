"""Writes proto/models/tests/pass3.request.json, the model proof run (`models-pass3-3`):

* every placeable prototype model placed finished, framed from its entrance side at the start (game paused, day);
* the Moon Loft placed over the district centre's entrance cell (harness `relativeTo: districtEntrance`), so the first
  path tile lies under it and every colonist leaving the district centre walks under the loft; day frames of it;
* a row and an L of Bamboo Fence pieces (`relativeTo: previous`) to show the mergeable variants joining;
* two frames each of the Bamboo Pinwheel and Kite Windmill a few seconds apart (wind-turned rotors);
* the Sky Lantern's `Default` (rise) animation started by the harness as WonderAnimationController does on activation
  (no real activation: that would post wonder events and Steam achievements), slowed, with frames through it;
* hammock frames through the evening leisure hours;
* at night (the end) each home and lit building twice: as occupied (unforced) and with `"lit": true`.

Timing: speed 3 runs about 6.8 real seconds per in-game hour, and the run starts near 04:00 (pass 2: day 1.176);
"at" values are real seconds into the run, so 20 in-game hours end near midnight after about 136 s.
"""
import json
import os

T = lambda i: f"PandabornModel{i}.PandabornProto"  # noqa: E731
SEC_PER_HOUR = 6.8
START_HOUR = 4.2


def at_hour(h):
    return round((h - START_HOUR) * SEC_PER_HOUR, 1)


# every placeable prototype except the Village Hall (a second district centre joined by a path crashes the game) and
# the water machines that need a river (Scoop Wheel, Bamboo Water Wheel, Paddy Spout, Treadwheel Lift)
ids = ["Den", "Hammock", "Teahouse", "Kindergarten", "CourtyardHouse", "TerraceHouse", "PaddyHouse",
       "NightBuildersPost", "NightCourierPost", "NightForagersPost", "StarTower", "FestivalSquare", "HotSpringBath",
       "InkStudio", "OperaStage", "Steamer", "PickleYard", "TeaRoastery", "LanternWorkshop",
       "HotPotHall", "SmokeKiln", "Kitchen", "TripHammerMill", "OxWorkshop", "KiteWindmill", "LargeKiteWindmill",
       "NapPlatform", "DryStoneWall", "CisternTap", "FlumeBridgeSpan", "BambooPinwheel", "DewCollector", "MemorialArch",
       "GreatSittingPanda", "SkyLantern", "CisternLarge", "CisternMedium", "Cistern", "StandingLantern",
       "HangingLantern", "StringLanterns", "PandaStatue", "PottedPine", "GoldfishBowl", "GardenMoonGate",
       "Flume", "FlumeGate", "FlumeBridge", "FlumeDrop", "FlumeCorner"]
small = {"DryStoneWall", "CisternTap", "FlumeBridgeSpan", "Hammock", "InkStudio", "Cistern", "StandingLantern", "HangingLantern", "StringLanterns", "Flume",
         "FlumeGate", "FlumeBridge", "NightForagersPost", "BambooPinwheel", "PandaStatue", "PottedPine",
         "GoldfishBowl", "BambooFence"}

# the biggest footprints go first, before the ring search has filled the space round the district centre (the 7x7 Sky
# Lantern found no spot in models-pass3-4)
BIG_FIRST = ["SkyLantern", "GreatSittingPanda", "FestivalSquare", "OperaStage"]
buildings = [
    # over the district centre's door: tried in all four orientations at the entrance cell, then one cell aside
    {"template": T("MoonLoft"), "relativeTo": "districtEntrance", "offset": [0, 0, 0]},
    {"template": T("MoonLoft"), "relativeTo": "districtEntrance", "offset": [-1, -1, 0]},
    # fence: one free spot, then a row of three and a turn of two
    {"template": T("BambooFence"), "orientation": "Cw0"},
    {"template": T("BambooFence"), "relativeTo": "previous", "offset": [1, 0, 0], "orientation": "Cw0"},
    {"template": T("BambooFence"), "relativeTo": "previous", "offset": [1, 0, 0], "orientation": "Cw0"},
    {"template": T("BambooFence"), "relativeTo": "previous", "offset": [0, 1, 0], "orientation": "Cw0"},
    {"template": T("BambooFence"), "relativeTo": "previous", "offset": [0, 1, 0], "orientation": "Cw0"},
] + [T(i) for i in BIG_FIRST] + [T(i) for i in ids if i not in BIG_FIRST] + [T("Den"), T("Den")]

shots = [{"name": "day_overview", "kind": "overview", "at": "start"}]
for i in ["MoonLoft", "BambooFence"] + ids:
    md = 3.0 if i in small else 6.0
    shots.append({"name": f"{i}_front", "kind": "building", "target": T(i), "at": "start", "front": True, "yaw": 0,
                  "pitch": 42, "zoom": 1.0, "minDistance": md})
    shots.append({"name": f"{i}_3q", "kind": "building", "target": T(i), "at": "start", "front": True, "yaw": 35,
                  "pitch": 30, "zoom": 1.25, "minDistance": md * 0.8})
# rotors: two frames a few seconds apart
for i in ("BambooPinwheel", "KiteWindmill", "LargeKiteWindmill"):
    for k, t in enumerate((8.0, 9.5)):
        shots.append({"name": f"{i}_turn_{k}", "kind": "building", "target": T(i), "at": str(t), "front": True,
                      "yaw": 20, "pitch": 30, "zoom": 1.1, "minDistance": 3.0 if i in small else 5.0})
# colonists under the Moon Loft through the working day (low camera so the space under the loft shows)
for k, h in enumerate((6.0, 6.5, 7.0, 9.0, 12.0, 15.0, 16.0, 17.0)):
    shots.append({"name": f"MoonLoft_walk_{k}", "kind": "building", "target": T("MoonLoft"), "at": str(at_hour(h)),
                  "front": True, "yaw": 50, "pitch": 18, "zoom": 0.8, "minDistance": 5.0})
# the Sky Lantern rise, slowed to a fifth (about 21 game seconds, 7 real seconds at speed 3)
SKY_AT = 30.0
animations = [{"target": T("SkyLantern"), "at": SKY_AT, "name": "Default", "speed": 0.2, "looped": False}]
for k, dt in enumerate((0.0, 1.2, 2.4, 3.6, 4.8, 6.0, 7.5)):
    shots.append({"name": f"SkyLantern_rise_{k}", "kind": "building", "target": T("SkyLantern"),
                  "at": str(SKY_AT + 0.2 + dt), "front": True, "yaw": 25, "pitch": 15, "zoom": 0.55,
                  "minDistance": 9.0})
# the hammock through the evening leisure hours
for k, h in enumerate((16.0, 16.5, 17.0, 17.5, 18.0, 18.5, 19.0, 19.5, 20.0, 20.5, 21.0, 22.0)):
    shots.append({"name": f"Hammock_evening_{k:02d}", "kind": "building", "target": T("Hammock"),
                  "at": str(at_hour(h)), "front": True, "yaw": 30, "pitch": 30, "zoom": 1.1, "minDistance": 2.5})
shots.append({"name": "night_overview", "kind": "overview", "at": "end"})
for i in ("Den", "CourtyardHouse", "TerraceHouse", "MoonLoft", "Teahouse", "Kindergarten", "NightBuildersPost",
          "NightCourierPost", "StarTower", "FestivalSquare", "StandingLantern", "StringLanterns", "LanternWorkshop",
          "SkyLantern", "Hammock"):
    md = 3.0 if i in small else 5.0
    shots.append({"name": f"{i}_night", "kind": "building", "target": T(i), "at": "end", "front": True, "yaw": 25,
                  "pitch": 35, "zoom": 1.1, "minDistance": md})
    shots.append({"name": f"{i}_night_lit", "kind": "building", "target": T(i), "at": "end", "front": True, "yaw": 25,
                  "pitch": 35, "zoom": 1.1, "minDistance": md, "lit": True})
shots.append({"name": "night_screen", "kind": "screen", "at": "end"})
req = {"run": {"inGameHours": 20.0, "realSeconds": 700}, "speed": 3, "batchControl": False, "buildings": buildings,
       "animations": animations, "screenshots": shots, "screenshotSize": [1600, 1000],
       "ownPatterns": ["PandabornFactions", "PandabornDevHarness", "Inkpaws", "PandabornProtoModels", "PandabornModel"]}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "pass3.request.json")
json.dump(req, open(out, "w"), indent=1)
print(out, len(buildings), len(shots))
