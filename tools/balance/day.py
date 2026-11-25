"""A colonist's hours off duty: sleep, meals, and how many of the faction's rituals fit in what is left.

A time budget, not an agent simulation. The game's rules it rests on (game-mechanics.md 1.4, 2.2, 13.1):
* bedtime is reserved as 1.2 x (walk home + the time to refill a day's Sleep at 0.2 an hour);
* a colonist eats and drinks one unit per visit, FOOD_PER_DAY + WATER_PER_DAY units a day;
* an attraction need falls by its DailyDelta and is refilled at the attraction's points per hour, so it costs
  decay / rate hours in a seat every day, plus the walk there for each visit.
ASSUMED (not measured): 0.3 h of walking per visit, 1.2 h a day on meals, and that a colonist short of time keeps
the rituals worth most wellbeing per hour. MEASURED: four one-seat hammocks kept the Nap need of 13 to 15 colonists
above zero on a 16-hour day (playtest runs), which sets PACKING.
"""
from . import mech

SLEEP_BLOCK = 1.2 * (0.25 + 0.6 / 0.2)      # hours reserved for bed [1.4]
MEALS = 1.2                                  # ASSUMED hours a day eating and drinking, walking included
WALK_PER_VISIT = 0.3                         # ASSUMED hours walked per attraction visit (about 10 tiles each way)
PACKING = 0.75                               # share of seat-hours in the off-duty window that are really used


def leisure_hours(shift):
    return max(0.0, 24.0 - shift - SLEEP_BLOCK - MEALS)


def window_hours(shift):
    """Clock hours in which off-duty colonists are awake: when seats can be taken."""
    return max(0.0, 24.0 - shift - SLEEP_BLOCK)


def rituals(game):
    """Every attraction need of the faction: {need: (hours in a seat a day, visits a day, wellbeing, building, seats)}.
    A building that fills two needs at once (Nap Platform: nap and rooftop) charges its time to the first."""
    found = {}
    for name in game.buildings():
        t = game.templates[name]
        effects = t.get("AttractionSpec", {}).get("Effects", [])
        seats = t.get("EnterableSpec", {}).get("CapacityFinished", 0)
        for index, effect in enumerate(effects):
            need = game.needs.get(effect["NeedId"])
            if not need or need.get("FavorableWellbeing", 0) <= 0 or effect["PointsPerHour"] <= 0:
                continue
            decay = -need["DailyDelta"]
            if decay <= 0 or need.get("NeedGroupId") == "BasicNeeds":
                continue
            seat = decay / effect["PointsPerHour"]
            visit = max(0.5, 0.7 / effect["PointsPerHour"])                # a visit refills about 0.7 of the need
            visits = min(1.0, seat / visit)
            entry = (0.0 if index else seat, 0.0 if index else visits, need["FavorableWellbeing"], name, seats)
            if effect["NeedId"] not in found or seats > found[effect["NeedId"]][4]:
                found[effect["NeedId"]] = entry
    return found


def fits(game, shift, skip=()):
    """What a colonist keeps at this working day: (leisure hours, hours the full set needs, wellbeing kept, lost)."""
    have = leisure_hours(shift)
    items = [(n, seat + visits * WALK_PER_VISIT, wb) for n, (seat, visits, wb, _, _) in rituals(game).items()
             if n not in skip]
    need_all = sum(h for _, h, _ in items)
    kept, used, lost = 0, 0.0, []
    for name, hours, wb in sorted(items, key=lambda i: -(i[2] / i[1]) if i[1] else -1e9):
        if used + hours <= have + 1e-9:
            used += hours
            kept += wb
        else:
            lost.append(name)
    return have, need_all, kept, lost


def served(game, need, shift):
    """Colonists one building of this ritual serves at this working day."""
    seat, _, _, building, seats = rituals(game)[need]
    return seats * window_hours(shift) * PACKING / seat if seat else float("inf")


def output(game, kind, shift, base_wellbeing, skip=()):
    """Work done per colonist-day, in hours at speed 1, with the wellbeing this working day leaves. Averaged over
    ten wellbeing points above the base, so a result does not hang on where a tier boundary happens to fall."""
    _, _, kept, _ = fits(game, shift, skip)
    total = 0.0
    for extra in range(10):
        w = mech.Worker(game, kind, shift, base_wellbeing + kept + extra)
        total += w.on_post() * w.work_speed() / 10
    return total, base_wellbeing + kept
