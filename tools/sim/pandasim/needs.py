"""A representative colonist's off-duty time (1.2-1.4, 2.2, 13.1).

After the shift the colonist eats and drinks, then visits attractions picked by the Appraiser score (room to max x
importance x (1 + 0.1 room)), then must head home: bedtime is when hours to dawn < 1.2 x (walk home + time to fill
Sleep). Every leisure need decays all day. The result is which needs stay favourable at a given working day, so
wellbeing can be compared between working days and between peoples.
"""
from dataclasses import dataclass

from . import vanilla as V
from .mech import Ctx


@dataclass
class LeisureNeed:
    name: str
    decay: float            # per day (positive number)
    fill: float             # points per hour while visiting
    wellbeing: int          # when favourable
    importance: float = 1.0
    max: float = 1.0
    start: float = 0.5
    walk_tiles: float = 15.0
    min_visit: float = 0.5


@dataclass
class DayPlan:
    base_wellbeing: float          # needs not simulated here: basic, nutrition, decorations, awe
    leisure: list                  # LeisureNeed
    sleep_per_h: float = V.HOME_SLEEP_PER_HOUR
    home_tiles: float = 15.0
    food_tiles: float = 12.0
    food_visits: float = 3.0
    bite_h: float = 0.1
    bites: float = V.FOOD_PER_DAY + V.WATER_PER_DAY


def sleep_block_hours(plan, ctx):
    """Bedtime: hours to dawn < 1.2 x (walk home + time to fill Sleep) (1.4)."""
    return 1.2 * (plan.home_tiles / ctx.v_empty() + V.SLEEP_PER_DAY / plan.sleep_per_h)


def food_hours(plan, ctx):
    return plan.food_visits * 2 * plan.food_tiles / ctx.v_empty() + plan.bites * plan.bite_h


def simulate(plan, sp, off_hours, days=30, wb_for_walk=10):
    """off_hours: awake-or-asleep hours off duty per day (24 - shift). Returns per-day dicts."""
    needs = {n.name: n.start for n in plan.leisure}
    spec = {n.name: n for n in plan.leisure}
    c = Ctx(sp, hours=24 - off_hours, wb=wb_for_walk)
    sleep_h = sleep_block_hours(plan, c)
    food_h = food_hours(plan, c)
    out = []

    def decay_all(hours, skip=None):
        for k, s in spec.items():
            if k != skip:
                needs[k] = max(0.0, needs[k] - s.decay * hours / 24.0)

    for day in range(days):
        decay_all(24 - off_hours)               # the shift
        decay_all(min(off_hours, food_h))
        leisure = max(0.0, off_hours - sleep_h - food_h)
        t = 0.0
        visits = {}
        while leisure - t > 0.0:
            best, best_score = None, 0.0
            for k, s in spec.items():
                room = s.max - needs[k]
                if room <= 0.05:
                    continue
                walk = s.walk_tiles / c.v_empty()
                if walk + 0.3 > leisure - t:
                    continue
                score = min(s.fill, room) * s.importance * (1 + 0.1 * room)
                if score > best_score:
                    best, best_score = k, score
            if best is None:
                break
            s = spec[best]
            walk = s.walk_tiles / c.v_empty()
            stay = min(max(s.min_visit, (s.max - needs[best]) / s.fill), leisure - t - walk)
            decay_all(walk)
            decay_all(stay, skip=best)
            needs[best] = min(s.max, needs[best] + s.fill * stay)
            t += walk + stay
            visits[best] = visits.get(best, 0) + stay
        decay_all(max(0.0, leisure - t))
        decay_all(sleep_h)
        wb = plan.base_wellbeing + sum(spec[k].wellbeing for k, v in needs.items() if v > 0)
        out.append(dict(day=day, wb=wb, leisure=leisure, idle=max(0.0, leisure - t), visits=visits,
                        needs=dict(needs)))
    return out


def steady(results, skip=10):
    tail = results[skip:]
    n = len(tail)
    hours = {}
    for r in tail:
        for k, v in r["visits"].items():
            hours[k] = hours.get(k, 0) + v / n
    favourable = {k: sum(1 for r in tail if r["needs"][k] > 0) / n for k in tail[0]["needs"]}
    return dict(wb=sum(r["wb"] for r in tail) / n, leisure=tail[-1]["leisure"],
                idle=sum(r["idle"] for r in tail) / n, hours=hours, favourable=favourable)
