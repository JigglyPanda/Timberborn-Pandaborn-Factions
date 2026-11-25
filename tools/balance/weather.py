"""Droughts as the game draws them (game-mechanics.md 12), and which plants live through them.

The n-th drought lasts round(U(k x min, k x max)) days, k = lerp(handicap, 1, (n - 1) / handicap cycles), at least 1.
A plant on dry soil dies after DaysToDieDry x U(0.9, 1.1). The scripted Hard playtests calibrate the one free
parameter, how long the soil stays moist after the drought starts: about nothing (a five-day drought killed 42% and
48% of five-day shoot bamboo; this module says 50%).
"""
SOIL_LAG_DAYS = 0.0


def mode(game, name):
    spec = game.files["newgamemodes/gamemode.%s.blueprint" % name.lower()]["GameModeSpec"]
    return {
        "temperate": (spec["TemperateWeatherDuration"]["Min"], spec["TemperateWeatherDuration"]["Max"]),
        "drought": (spec["DroughtDuration"]["Min"], spec["DroughtDuration"]["Max"]),
        "handicap": spec["DroughtDurationHandicapMultiplier"],
        "cycles": spec["DroughtDurationHandicapCycles"],
        "badtide": (spec["BadtideDuration"]["Min"], spec["BadtideDuration"]["Max"]),
        "badtide_handicap": spec["BadtideDurationHandicapMultiplier"],
        "badtide_cycles": spec["BadtideDurationHandicapCycles"],
        "food": spec["StartingFood"],
    }


def lengths(m, n, steps=400, hazard="drought"):
    """Distribution {days: probability} of the n-th hazard of its kind."""
    handicap = m["handicap"] if hazard == "drought" else m["badtide_handicap"]
    cycles = m["cycles"] if hazard == "drought" else m["badtide_cycles"]
    k = handicap + (1 - handicap) * min(1.0, (n - 1) / cycles)
    lo, hi = k * m[hazard][0], k * m[hazard][1]
    dist = {}
    for i in range(steps):
        days = max(1, round(lo + (hi - lo) * (i + 0.5) / steps))
        dist[days] = dist.get(days, 0.0) + 1.0 / steps
    return dist


def percentile(dist, p):
    total = 0.0
    for days in sorted(dist):
        total += dist[days]
        if total >= p - 1e-9:
            return days
    return max(dist)


def survives(dry_days, drought_days):
    """Probability that an unwatered plant with this DaysToDieDry is alive when the water returns."""
    if dry_days is None:
        return 1.0
    dry = drought_days - SOIL_LAG_DAYS
    lo, hi = 0.9 * dry_days, 1.1 * dry_days
    return max(0.0, min(1.0, (hi - dry) / (hi - lo)))


def survival(m, n, dry_days):
    return sum(p * survives(dry_days, days) for days, p in lengths(m, n).items())
