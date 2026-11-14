"""Writes the catalogue lane's phase-5 proof requests (docs: the coordinator's phase 5, PROOF) from the playtest lane's
scenarios, so the quality of play stays theirs:
  * phase5_played_inkpaws.json  - inkpaws-standard, the working day set to 12 h on day 2 (the afternoon bell), plus a
                                  goods/bonus watch: rested multipliers per template, poles, tea, every Ringtail building
  * phase5_played_folktails.json - folktails-baseline with the same 12 h day and watch: Folktails beavers must stay at
                                  vanilla multipliers (the bell is an Inkpaw thing)
Usage: python tests/scenarios/catalogue/make_phase5.py
"""
import copy
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PLAY = os.path.join(HERE, "..", "playtest")


def load(name):
    with open(os.path.join(PLAY, name), encoding="utf-8") as f:
        return json.load(f)


def bell_step():
    return {"id": "bell12", "op": "hours", "hours": 12, "when": {"day": 2, "hour": 4}}


def watch(goods, templates):
    return {"goods": [], "templates": [], "watch": {"everySeconds": 30, "goods": goods, "templates": templates,
                                                    "bonuses": ["WorkingSpeed", "MovementSpeed"]}}


def write(name, data):
    with open(os.path.join(HERE, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(data, indent=1) + "\n")
    print("wrote", name)


ink = copy.deepcopy(load("inkpaws-standard.json"))
ink["playtest"]["name"] = "phase5-inkpaws"
ink["playtest"]["note"] = "inkpaws-standard with the working day set to 12 h on day 2 (the bell) and a bonus watch"
ink["playtest"]["steps"].insert(1, bell_step())
ink["goodsProbe"] = watch(["Log", "Plank", "PandabornBambooShoots", "PandabornSteamedShoots", "PandabornTea", "Water"],
                          ["PandabornHammock.Inkpaws", "PandabornTeahouse.Inkpaws", "PandabornDen.Inkpaws",
                           "PandabornMoonLoft.Inkpaws", "RingtailAdult.Inkpaws"])
ink["checks"] = {"pandabornFeatures": {"Bell": "on", "Names": "on", "Look": "on", "Ringtails": "on"}}
write("phase5_played_inkpaws.json", ink)

ft = copy.deepcopy(load("folktails-baseline.json"))
ft["playtest"]["name"] = "phase5-folktails"
ft["playtest"]["note"] = "folktails-baseline with a 12 h day and a bonus watch: the bell must not touch beavers"
ft["playtest"]["steps"].insert(1, bell_step())
ft["goodsProbe"] = watch(["Log", "Plank"], ["Lodge.Folktails"])
ft["checks"] = {"materialMainTexNotPrefix": "PBLook_"}
write("phase5_played_folktails.json", ft)
