"""Standard previews for one plant: a field of 20+ mature plants beside the vanilla plant of the same kind, and a state
row (seedling, seedling dry/dead, mature, ripe (detail), dry, dead, stump), by day; optionally a night field.

    python -I src/pipeline/plants/preview_plant.py <Id> [--night] [--only field|states]

Output: E:\\PandabornDev\\build\\plants\\preview\\<Id>_field.png, <Id>_states.png (and _night).
"""
import argparse
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from preview import Field, vanilla, label  # noqa: E402

BUILD = r"E:\PandabornDev\build\plants"
OUT = os.path.join(BUILD, "preview")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))

# vanilla neighbour per plant, its randomizer (h0, h1, w0, w1, rotation) and the field shape
SETUP = {
    "PandabornTimberBamboo": {"ref": ["BirchMature", "PineMature", "ChestnutTreeMature"], "rand": (0.9, 1.08, 0.9, 1.1, "free"),
                              "refrand": (0.85, 1.05, 0.9, 1.1, "free"), "size": (5, 5), "dist": 26, "detail": True},
    "PandabornPersimmonTree": {"ref": ["ChestnutTreeMature", "OakMature", "MapleMature"], "rand": (0.9, 1.1, 0.9, 1.1, "free"),
                               "refrand": (0.9, 1.1, 0.9, 1.1, "free"), "size": (5, 5), "dist": 26, "detail": True},
    "PandabornTeaBush": {"ref": ["BlueberryBushMature", "CoffeeBushMature"], "rand": (0.95, 1.05, 0.95, 1.05, "by90"),
                         "refrand": (0.8, 1.2, 0.8, 1.2, "free"), "size": (6, 4), "dist": 16, "detail": True},
    "PandabornShootBamboo": {"ref": ["CarrotMature", "PotatoMature"], "rand": (1, 1, 1, 1, "free"),
                             "refrand": (1, 1, 1, 1, "free"), "size": (6, 4), "dist": 15},
    "PandabornCabbage": {"ref": ["CarrotMature", "KohlrabiMature"], "rand": (1, 1, 1, 1, "by90"),
                         "refrand": (1, 1, 1, 1, "free"), "size": (6, 4), "dist": 15},
    "PandabornRice": {"ref": ["CattailMature", "WheatMature"], "rand": (0.95, 1.05, 0.95, 1.05, "by90"),
                      "refrand": (0.8, 1.2, 0.8, 1.2, "free"), "size": (6, 4), "dist": 16, "water": 0.3},
    "PandabornSichuanPepper": {"ref": ["SunflowerMature", "EggplantMature"], "rand": (0.9, 1.1, 0.9, 1.1, "free"),
                               "refrand": (0.9, 1.1, 0.9, 1.1, "free"), "size": (6, 4), "dist": 17},
}


def model(pid, stage):
    return os.path.join(BUILD, pid, pid + stage + ".timbermesh")


def field(pid, night=False, out=None):
    s = SETUP[pid]
    f = Field(seed=5)
    nx, nz = s["size"]
    h0, h1, w0, w1, rot = s["rand"]
    water = []
    f.block(model(pid, "Mature"), (0, 0), (nx, nz), (h0, h1, w0, w1), rot=rot)
    x = nx + 1
    for ref in s["ref"]:
        rh0, rh1, rw0, rw1, rrot = s["refrand"]
        f.block(vanilla(ref), (x, 0), (3, nz), (rh0, rh1, rw0, rw1), rot=rrot)
        x += 4
    if s.get("water"):
        water = [{"rect": [-1, -1, x, nz + 1], "level": s["water"]}]
    total_x = x - 1
    detail = [pid] if s.get("detail") else []
    out = out or os.path.join(OUT, "%s_field%s.png" % (pid, "_night" if night else ""))
    f.render(out, target=(total_x / 2, 0.3, nz / 2), yaw=0, pitch=50, distance=s["dist"] + total_x * 0.55,
             night=night, detail=detail, water=water, ground=[-2, -3, total_x + 2, nz + 3], size=(1800, 900))
    return out


def states(pid, out=None):
    s = SETUP[pid]
    f = Field(seed=9)
    names = ["Seedling", "SeedlingDry", "SeedlingDead", "Mature", "MatureDry", "MatureDead"]
    if os.path.exists(model(pid, "MatureStump")):
        names.append("MatureStump")
    for i, n in enumerate(names):
        f.block(model(pid, n), (i * 2, 0), (1, 2), (1, 1, 1, 1), rot=30)
    n_ripe = 0
    if s.get("detail"):
        # the ripe (yield) look needs the detail on: a second row of mature plants, rendered with detail
        pass
    water = [{"rect": [-1, -1, len(names) * 2, 3], "level": s["water"]}] if s.get("water") else []
    out = out or os.path.join(OUT, "%s_states.png" % pid)
    tall = 1.4 if SETUP[pid]["dist"] > 20 else 0.3
    f.render(out, target=(len(names) - 1, tall, 1.0), yaw=0, pitch=38, distance=(6 + len(names) * 2.4) * (1.25 if tall > 1 else 0.8), water=water,
             ground=[-2, -2, len(names) * 2 + 1, 4], size=(1800, 700), detail=[pid] if s.get("detail") else [])
    caps = []
    W = 1800
    for i, n in enumerate(names):
        caps.append((int(W * (0.08 + 0.84 * i / max(len(names) - 1, 1))) - 50, 12, n))
    label(out, caps)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="+")
    ap.add_argument("--night", action="store_true")
    ap.add_argument("--only")
    a = ap.parse_args()
    for pid in a.ids:
        if a.only in (None, "field"):
            print(field(pid))
            if a.night:
                print(field(pid, night=True))
        if a.only in (None, "states"):
            print(states(pid))


if __name__ == "__main__":
    main()
