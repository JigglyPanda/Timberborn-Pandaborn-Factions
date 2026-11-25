"""A colonist at work: speeds from wellbeing and the bell, loads, trips, and what one shift of each job yields.

Rules are docs/tech/game-mechanics.md (section numbers in brackets). Numbers come from data.py, never from this file,
except the three marked CALIBRATED, which are measured in the scripted playtests (playtest.py prints them).
"""
import math
from dataclasses import dataclass, replace

TILES_PER_HOUR = 19.2            # one game hour is 19.2 s at speed 1 [1.1]; walking speeds are tiles per second
ON_TASK = 0.97                   # CALIBRATED: share of the working day spent at the post (31-32 of 32 half-hour samples)
PUMP_EFFICIENCY = 0.85           # CALIBRATED: a staffed water pump makes 85% of its recipe rate (40-41 a day at speed 1)
FOOD_PER_DAY = 2.57              # CALIBRATED: food items a colonist eats a day (the rule says 0.8 / 0.3 = 2.67)
WATER_PER_DAY = 2.11             # CALIBRATED: water a colonist drinks a day (the rule says 0.7 / 0.33 = 2.12)
BUILD_UNITS_PER_HOUR = 20        # build time = units / 20 hours [6]


def tier(game, kind, wellbeing, who="Adult"):
    """Bonus delta of a wellbeing tier table (WellbeingTierSpec): the last threshold reached; nothing below zero."""
    key = "wellbeingtiers/wellbeingtier.%s.%s.blueprint" % (who.lower(), kind.lower())
    spec = next(iter(game.files[key].values()))
    wellbeing = math.floor(wellbeing)
    if wellbeing < 0:
        return 0.0
    steps = spec["Bonuses"]
    last = steps[-1]
    if wellbeing > last["Wellbeing"] and spec.get("WellbeingThreshold"):
        extra = (wellbeing - last["Wellbeing"]) // spec["WellbeingThreshold"]
        return last["Multiplier"] + extra * spec.get("MultiplierIncrement", 0.0)
    best = 0.0
    for step in steps:
        if wellbeing >= step["Wellbeing"]:
            best = step["Multiplier"]
    return best


def curve(points, hours):
    """Piecewise-linear bell curve, flat beyond its ends (BellService.Curve)."""
    pts = sorted(points, key=lambda p: p["Hours"])
    if not pts:
        return 0.0
    if hours <= pts[0]["Hours"]:
        return pts[0]["Bonus"]
    for a, b in zip(pts, pts[1:]):
        if hours <= b["Hours"]:
            return a["Bonus"] + (b["Bonus"] - a["Bonus"]) * (hours - a["Hours"]) / (b["Hours"] - a["Hours"])
    return pts[-1]["Bonus"]


@dataclass(frozen=True)
class Kind:
    """One kind of colonist, read from its character template."""
    name: str
    walk: float                  # tiles per game hour, empty
    slow: float                  # tiles per game hour, carrying
    lift: int
    bell: tuple = ()             # the rested-bonus curve, as (work points, walk points); empty = no bonus
    fixed: tuple = ()            # bots: (working speed, movement) multipliers of their own tier
    all_day: bool = False        # bots ignore working hours


def kind(game, template, name=None, bell_override=None, **changes):
    t = game.template(template)
    speed = t["WalkerSpeedManagerSpec"]
    bell = ()
    if "PandabornBellSpec" in t:
        bell = (tuple(map(_freeze, t["PandabornBellSpec"]["WorkingSpeedCurve"])),
                tuple(map(_freeze, t["PandabornBellSpec"]["MovementSpeedCurve"])))
    if bell_override is not None:
        bell = bell_override
    k = Kind(name or template, speed["BaseWalkingSpeed"] * TILES_PER_HOUR, speed["BaseSlowedSpeed"] * TILES_PER_HOUR,
             t["GoodCarrierSpec"]["BaseLiftingCapacity"], bell)
    if "BotSpec" in t:
        k = replace(k, fixed=(1 + tier(game, "WorkingSpeed", 0, "Bot"), 1 + tier(game, "MovementSpeed", 0, "Bot")),
                    all_day=True)
    return replace(k, **changes)


def _freeze(point):
    return (("Hours", point["Hours"]), ("Bonus", point["Bonus"]))


def _thaw(points):
    return [dict(p) for p in points]


@dataclass(frozen=True)
class Worker:
    """One worker on one kind of day. Every job function takes a Worker."""
    game: object
    kind: Kind
    hours: float = 16.0          # the length of this worker's shift
    wellbeing: float = 0.0
    bell_hours: float = None     # the hours the bell bonus is read at (None = the shift length)
    commute: float = 12.0        # tiles walked to the post at the start of the shift, paid from working time
    carry_bonus: float = 0.0     # Hauling Post and Courier Post: +1.0

    def _bonus(self, which):
        if not self.kind.bell:
            return 0.0
        return curve(_thaw(self.kind.bell[which]), self.hours if self.bell_hours is None else self.bell_hours)

    def work_speed(self):
        if self.kind.fixed:
            return self.kind.fixed[0]
        return (1 + tier(self.game, "WorkingSpeed", self.wellbeing)) * (1 + self._bonus(0))

    def move(self):
        if self.kind.fixed:
            return self.kind.fixed[1]
        cap = self.game.bonus_types["MovementSpeed"]["MaximumValue"]
        return min(cap, (1 + tier(self.game, "MovementSpeed", self.wellbeing)) * (1 + self._bonus(1)))

    def trip(self, tiles):
        """Hours to walk `tiles` empty and `tiles` carrying: one fetch or one delivery [5.6]."""
        return tiles / (self.kind.walk * self.move()) + tiles / (self.kind.slow * self.move())

    def load(self, good):
        lift = math.floor(self.kind.lift * (1 + self.carry_bonus))
        return max(1, lift // self.game.weight(good))

    def on_post(self):
        """Hours at the post in one shift."""
        if self.kind.all_day:
            return 23.0
        return max(0.0, self.hours * ON_TASK - self.commute / (self.kind.walk * self.move()))


# --- one shift of each job (units per worker per day) ----------------------------------------------------------------

def hauling(w, good, tiles=20.0):
    """Goods moved by a full-time carrier over `tiles` each way."""
    return w.on_post() / w.trip(tiles) * w.load(good)


def building(w, cost, tiles=15.0):
    """Material units delivered and built per shift for a cost mix {good: amount} [6]."""
    total = sum(cost.values())
    hours = sum(n * (w.trip(tiles) / w.load(g)) for g, n in cost.items()) + total / BUILD_UNITS_PER_HOUR / w.work_speed()
    return w.on_post() / hours * total


def cutting(w, plant, tiles=10.0):
    """Units a woodcutter brings to the flag: one tree per trip, the rest of its yield in further trips [7.1]."""
    good, amount = plant["cut"]
    trips = math.ceil(amount / w.load(good))
    return w.on_post() / (plant["cut_h"] / w.work_speed() + trips * w.trip(tiles)) * amount


def farming(w, plant, tiles=6.0):
    """Units a farmer harvests a day, planting included, and the tiles that keeps busy [7.1]."""
    good, amount = plant["cut"]
    per_tile = (plant["plant_h"] + plant["cut_h"]) / w.work_speed() + w.trip(tiles) + 1.5 / (w.kind.walk * w.move())
    units = w.on_post() / per_tile * amount
    return units, units / amount * plant["grow_d"]


def gathering(w, plant, tiles=8.0):
    good, amount = plant["gather"]
    return w.on_post() / (plant["gather_h"] / w.work_speed() + w.trip(tiles)) * min(amount, w.load(good))


def workshop(w, recipe, tiles=12.0, supplied=False, workers=1):
    """Cycles per shift of a workshop. supplied=True: haulers or night couriers keep inputs full and outputs clear,
    so the worker only produces. Otherwise the vanilla order runs action by action: produce, else carry one load of
    output out, else fetch one load of the emptiest input [4.2]."""
    hours, speed = w.on_post(), w.work_speed() * workers
    if supplied:
        return hours * speed / recipe["hours"]
    need = dict(recipe["in"])
    if recipe["fuel"]:
        need[recipe["fuel"]] = need.get(recipe["fuel"], 0) + 1.0 / recipe["cycles_per_fuel"]
    stock = {g: 0.0 for g in need}
    out_good = next(iter(recipe["out"]), None)
    out_amount = sum(recipe["out"].values())
    out_cap = out_amount * recipe["shelf"]
    out = t = cycles = 0.0
    while t < hours:
        if all(stock[g] >= a - 1e-9 for g, a in need.items()) and (out_good is None or out + out_amount <= out_cap):
            for g, a in need.items():
                stock[g] -= a
            t += recipe["hours"] / speed
            out += out_amount
            cycles += 1
        elif out > 0 and out_good:
            out -= min(out, w.load(out_good))
            t += w.trip(tiles)
        elif need:
            g = min(need, key=lambda x: stock[x] / need[x])
            stock[g] += w.load(g)
            t += w.trip(tiles)
        else:
            break
    return cycles * min(1.0, hours / t) if t else 0.0
