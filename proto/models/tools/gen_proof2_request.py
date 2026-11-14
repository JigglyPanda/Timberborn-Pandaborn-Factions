"""Writes proto/models/tests/proof2.request.json: the follow-up to models-pass3-6 for what that run did not show.

What models-pass3-6 taught (2026-11-14):
* `PartialDayNumber` fraction 0 is morning, not midnight: the run starts at day 1.176 in the late morning, dusk is near
  1.66, it is dark from about 1.70 and light again by 2.0. A 20-hour run therefore ended at dawn (the "night" shots
  were in daylight) and the hammock frames after hour 17 were deep in the night. Here the run is 16 in-game hours and
  ends at about 1.84, in the dark.
* Framed close-ups of small things in a crowded test village are blocked by their neighbours: here only the proof
  subjects are placed, the hammock is shot from above (pitch 55), and the Moon Loft from the angle that worked (yaw 25,
  pitch 35).

Proves: lit windows with occupants at night (unforced, next to forced `lit`), the hammock in use in the leisure hours
before dusk, colonists on the path under the Moon Loft (it stands over the district centre's door cell), the pinwheel
turning (away from the big windmills), the Festival Square lights at night.
"""
import json
import os

T = lambda i: f"PandabornModel{i}.PandabornProto"  # noqa: E731
SEC_PER_HOUR = 6.8            # speed 3


def at(h):
    return str(round(h * SEC_PER_HOUR, 1))     # h = in-game hours after the run starts (about 10:00)


buildings = [{"template": T("MoonLoft"), "relativeTo": "districtEntrance", "offset": [0, 0, 0]},
             {"template": T("MoonLoft"), "relativeTo": "districtEntrance", "offset": [-1, -1, 0]},
             T("Hammock"), T("Den"), T("Den"), T("Den"), T("CourtyardHouse"), T("TerraceHouse"), T("FestivalSquare"),
             T("LanternWorkshop"), T("BambooPinwheel"), T("LargeKiteWindmill")]
shots = [{"name": "day_overview", "kind": "overview", "at": "start"}]
for k, t in enumerate((1.0, 1.15, 1.3)):
    shots.append({"name": f"BambooPinwheel_turn_{k}", "kind": "building", "target": T("BambooPinwheel"), "at": at(t),
                  "front": True, "yaw": 20, "pitch": 45, "zoom": 1.0, "minDistance": 3.0})
# the Large Kite Windmill (one pale sail since pass 5, so the turning shows): three frames a second apart
for k, t in enumerate((2.0, 2.15, 2.3)):
    shots.append({"name": f"LargeKiteWindmill_turn_{k}", "kind": "building", "target": T("LargeKiteWindmill"),
                  "at": at(t), "front": True, "yaw": 20, "pitch": 50, "zoom": 1.0, "minDistance": 6.0})
# the walk home from work and the evening (colonists cross the district centre's door cell, under the loft)
for k, h in enumerate((0.5, 1.0, 1.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0)):
    shots.append({"name": f"MoonLoft_walk_{k}", "kind": "building", "target": T("MoonLoft"), "at": at(h), "front": True,
                  "yaw": 25, "pitch": 35, "zoom": 1.1, "minDistance": 5.0})
# the hammock through the leisure hours before dusk, from above
for k, h in enumerate((8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 12.5)):
    shots.append({"name": f"Hammock_leisure_{k:02d}", "kind": "building", "target": T("Hammock"), "at": at(h),
                  "front": True, "yaw": 30, "pitch": 55, "zoom": 1.0, "minDistance": 3.5})
shots.append({"name": "night_overview", "kind": "overview", "at": "end"})
for i in ("Den", "CourtyardHouse", "TerraceHouse", "MoonLoft", "FestivalSquare", "LanternWorkshop", "Hammock"):
    md = 3.5 if i == "Hammock" else 5.0
    for lit in (False, True):
        shots.append({"name": f"{i}_night" + ("_lit" if lit else ""), "kind": "building", "target": T(i), "at": "end",
                      "front": True, "yaw": 25, "pitch": 35, "zoom": 1.1, "minDistance": md, "lit": lit})
shots.append({"name": "night_screen", "kind": "screen", "at": "end"})
req = {"run": {"inGameHours": 16.0, "realSeconds": 600}, "speed": 3, "batchControl": False, "buildings": buildings,
       "screenshots": shots, "screenshotSize": [1600, 1000],
       "ownPatterns": ["PandabornFactions", "PandabornDevHarness", "Inkpaws", "PandabornProtoModels", "PandabornModel"]}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "proof2.request.json")
json.dump(req, open(out, "w"), indent=1)
print(out, len(buildings), len(shots))
