"""What the scripted colony playtests measured (tools/run_game_test.ps1 with a `playtest` request; runs pt-*).

Reads <run>/playtest/daily.jsonl. Used only for calibration and for the careless/Hard outcomes: these colonies
stall at 13 to 18 colonists because the driver ran out of trees it could mark after day 6, so nothing here says
anything about growth, the mid game, tea, Ringtails or the festival. See docs/tech/balance.md, "What the runs can
and cannot tell us".
"""
import json
import os

ROOT = os.environ.get("PANDABORN_TEST", r"E:\PandabornDev\build\test")
TRUSTED = {
    "Folktails standard": ["pt-ft-base-m2", "pt-ft-base-m3", "pt-ft-base-m4"],
    "Inkpaws standard": ["pt-ink-std-m1", "pt-ink-std-m3"],
    "Folktails careless": ["pt-ft-care-m1", "pt-ft-care-m2", "pt-ft-care-m3"],
    "Inkpaws careless": ["pt-ink-care-m1", "pt-ink-care-m3"],
    "Folktails Hard": ["pt-ft-hard-m1"],
    "Inkpaws Hard": ["pt-ink-hard-m1", "pt-ink-hard-m2"],
}
FOOD = {"Berries", "Carrot", "PandabornBambooShoots", "PandabornCabbage", "PandabornBambooMushrooms"}


def days(run):
    path = os.path.join(ROOT, run, "playtest", "daily.jsonl")
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                if not d.get("final"):
                    out.append(d)
    return out


def good(day, name, index):
    """index: 1 stock, 3 made the day before, 4 used the day before."""
    return day["goods"].get(name, [0, 0, 0, 0, 0])[index]


def summary(run):
    ds = days(run)
    if not ds:
        return None
    s = {"run": run, "days": ds[-1]["day"], "start": ds[0]["pop"]["total"], "end": ds[-1]["pop"]["total"]}
    s["logs_per_cutter"] = sum(good(d, "Log", 3) for d in ds if 3 <= d["day"] <= 5) / 6.0      # two flags, three days
    early = [d for d in ds if 5 <= d["day"] <= 8 and d["weather"] == "temperate"]
    s["pump"] = sum(good(d, "Water", 3) for d in early) / max(1, len(early))
    settled = [d for d in ds if 8 <= d["day"] <= 14]
    heads = sum(d["pop"]["total"] for d in settled) or 1
    s["water_each"] = sum(good(d, "Water", 4) for d in settled) / heads
    s["food_each"] = sum(sum(v[4] for g, v in d["goods"].items() if g in FOOD) for d in settled) / heads
    science = [(b["science"] - a["science"]) for a, b in zip(ds, ds[1:]) if 8 <= a["day"] <= 30]
    gains = [x for x in science if x > 0]
    s["science"] = sum(gains) / max(1, len(gains))
    s["water_before_drought"] = next((good(d, "Water", 1) for d in ds if d["weather"] != "temperate"), None)
    s["food_before_drought"] = next((sum(v[1] for g, v in d["goods"].items() if g in FOOD) for d in ds
                                     if d["weather"] != "temperate"), None)
    s["wellbeing30"] = next((d["wellbeing"]["avg"] for d in ds if d["day"] == 30), None)
    deaths = {}
    for d in ds:
        for death in d.get("deaths", []):
            text = (death.get("message") or death.get("cause") or "").lower()
            cause = "thirst" if "thirst" in text else "hunger" if "hunger" in text or "starv" in text else "old age"
            deaths[cause] = deaths.get(cause, 0) + 1
    s["deaths"] = deaths
    s["critical_days"] = {n: sum(d["needs"][n][1] for d in ds if n in d["needs"]) for n in ("Hunger", "Thirst")}
    return s


def shoot_survival():
    """Share of shoot bamboo alive at the first dawn after a five-day Hard drought, per run."""
    out = []
    for run in TRUSTED["Inkpaws Hard"]:
        ds = days(run)
        key = "PandabornShootBamboo.Inkpaws"
        in_drought = [d for d in ds if d["weather"] != "temperate" and key in d["plants"]]
        if not in_drought:
            continue
        first = in_drought[0]
        length = 0
        for d in ds:
            if d["day"] >= first["day"] and d["weather"] != "temperate":
                length += 1
            elif d["day"] > first["day"]:
                after = d
                break
        else:
            continue
        before = max(d["plants"][key][0] for d in in_drought[:2])
        out.append((run, length, before, after["plants"][key][0]))
    return out
