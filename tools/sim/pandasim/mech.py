"""Mechanics primitives: wellbeing tiers, walking, loads, a worker's context, weather.

All behaviour follows docs/tech/game-mechanics.md. Functions are small on purpose so a reader can check each one
against the reference.
"""
import math
import random
from dataclasses import dataclass, field, replace

from . import vanilla as V


def tier_delta(bonus, wellbeing):
    """Bonus delta for an integer wellbeing (WellbeingTier.TryGetTierBonus). Negative wellbeing gives nothing."""
    table, step, inc = V.TIERS[bonus]
    wb = int(math.floor(wellbeing))
    if wb < 0:
        return 0.0
    last_w, last_b = table[-1]
    if wb > last_w:
        return last_b + ((wb - last_w) // step) * inc
    delta = 0.0
    for w, b in table:
        if wb >= w:
            delta = b
    return delta


def rested_bonus_linear(hours, at=12.0, full=16.0, peak=1/3):
    """Draft curve: +peak at `at` hours or fewer, falling linearly to 0 at `full` hours."""
    if hours <= at:
        return peak
    if hours >= full:
        return 0.0
    return peak * (full - hours) / (full - at)


def rested_bonus_flat(hours, at=12.0, full=16.0):
    """Exactly flat curve: hours x (1 + bonus) = full for at <= hours <= full."""
    h = max(at, min(full, hours))
    return full / h - 1.0


@dataclass(frozen=True)
class Species:
    """Body and life stats of one kind of colonist. Speeds are tiles per game hour."""
    name: str
    walk: float = V.tiles_per_hour(V.WALK_TILES_PER_S)
    slow: float = V.tiles_per_hour(V.SLOWED_TILES_PER_S)
    lift: int = V.BEAVER_LIFT
    rested: object = None           # function(shift hours) -> bonus fraction, applied to working and walking speed
    multiplicative: bool = True     # bonus scales the whole multiplier (code) rather than adding a flat delta
    lifespan: float = V.AVERAGE_LIFESPAN
    childhood: float = V.DAYS_OF_CHILDHOOD
    ignores_hours: bool = False     # bots and oxen
    fixed_ws: float = 0.0           # bots: working speed from their own tier (0 = use beaver tiers)
    fixed_mv: float = 0.0


FOLKTAIL = Species("Folktail beaver")
BOT = Species("Folktails bot", lift=V.BOT_LIFT, ignores_hours=True, fixed_ws=1.65, fixed_mv=1.3,
              lifespan=V.BOT_LIFE_DAYS)

MV_CLAMP = (0.25, 2.0)          # BP/BonusTypes MovementSpeed clamp (3.4)


@dataclass
class Ctx:
    """One worker on one kind of day. All job maths takes a Ctx."""
    sp: Species
    hours: float = V.DEFAULT_WORK_HOURS     # length of the shift
    wb: float = 0.0                          # wellbeing
    commute: float = 15.0                    # tiles walked to the workplace at shift start (paid from work time)
    hungry: bool = False

    def bonus(self):
        return self.sp.rested(self.hours) if self.sp.rested else 0.0

    def ws(self):
        """WorkingSpeed multiplier (bonuses add, 4.3 / 3.4)."""
        if self.sp.fixed_ws:
            return self.sp.fixed_ws
        tier = tier_delta("WorkingSpeed", self.wb)
        b = self.bonus()
        base = (1 + tier) * (1 + b) if self.sp.multiplicative else 1 + tier + b
        return max(0.05, base - (0.5 if self.hungry else 0.0))

    def mv(self):
        if self.sp.fixed_mv:
            return self.sp.fixed_mv
        tier = tier_delta("MovementSpeed", self.wb)
        b = self.bonus()
        m = (1 + tier) * (1 + b) if self.sp.multiplicative else 1 + tier + b
        return min(MV_CLAMP[1], max(MV_CLAMP[0], m))

    def v_empty(self):
        return self.sp.walk * self.mv()

    def v_loaded(self):
        return self.sp.slow * self.mv()

    def round_trip(self, d):
        """Walk d tiles empty and d tiles loaded (a fetch or a delivery)."""
        return d / self.v_empty() + d / self.v_loaded()

    def load(self, good, carry_bonus=0.0, weight=None):
        w = weight if weight is not None else V.WEIGHT[good]
        lift = math.floor(self.sp.lift * (1 + carry_bonus))
        return max(1, int(lift // w))

    def shift_hours(self):
        return 24.0 if self.sp.ignores_hours else self.hours

    def work_hours(self):
        """Hours actually available for the job after the walk in."""
        if self.sp.ignores_hours:
            return 24.0 - 1.0     # bots: about an hour a day on their own needs
        return max(0.0, self.hours - self.commute / self.v_empty())


def with_(ctx, **kw):
    return replace(ctx, **kw)


# --- weather ---------------------------------------------------------------------------------------------------------

def hazard_multiplier(handicap, n_full, occurrence):
    """Duration growth for the n-th occurrence of a hazard type (12, HazardousWeatherHelper)."""
    if n_full <= 0:
        return 1.0
    t = min(1.0, (occurrence - 1) / n_full)
    return handicap + (1 - handicap) * t


def drought_range(mode, occurrence):
    m = V.MODES[mode]
    k = hazard_multiplier(m.drought_handicap, m.drought_handicap_n, occurrence)
    return (k * m.drought[0], k * m.drought[1])


def sample_drought(mode, occurrence, rng):
    lo, hi = drought_range(mode, occurrence)
    return max(1, int(round(rng.uniform(lo, hi))))


def sample_cycles(mode, n_cycles, rng):
    """List of (temperate_days, hazard, hazard_days). Badtide streak rules simplified to the base 0.4 chance."""
    m = V.MODES[mode]
    out, nd, nb = [], 0, 0
    for c in range(1, n_cycles + 1):
        temperate = rng.randint(m.temperate[0], m.temperate[1])
        if c >= m.badtide_from_cycle and rng.random() < V.BADTIDE_CHANCE:
            nb += 1
            k = hazard_multiplier(m.badtide_handicap, m.badtide_handicap_n, nb)
            days = max(1, int(round(rng.uniform(k * m.badtide[0], k * m.badtide[1]))))
            out.append((temperate, "badtide", days))
        else:
            nd += 1
            out.append((temperate, "drought", sample_drought(mode, nd, rng)))
    return out
