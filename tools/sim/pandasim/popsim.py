"""Day-by-day population model: births by the home rules, childhood, ageing with wellbeing, deaths by old age and
starvation, a food economy that scales with workers, and hazards (drought, Flowering).

Each colonist is tracked (kind, adult or child, life progress). Housing is built by a builder pool whose capacity
grows with the number of adults (calibrated on the opening simulator: about 0.3 beds per adult per day early on).
"""
import random
from dataclasses import dataclass, field

from . import vanilla as V
from .mech import tier_delta


@dataclass
class Person:
    kind: str                 # "I" Inkpaw / beaver, "R" Ringtail
    adult: bool
    life: float               # progress 0..longevity
    longevity: float
    child: float = 0.0        # childhood progress 0..1
    hunger_days: float = 0.0  # days with Hunger at or below 0


@dataclass
class PopConfig:
    name: str
    lifespan: float = V.AVERAGE_LIFESPAN
    childhood: float = V.DAYS_OF_CHILDHOOD
    birth_chance: float = V.FT_BIRTH_CHANCE_PER_ENTRY
    entries_per_adult_day: float = 2.0
    beds_per_adult_day: float = 0.12
    free_beds_target: float = 0.1          # player builds to keep this share of beds free
    max_population: int = 400
    wellbeing: object = None               # function(day, pop) -> average wellbeing
    food_per_worker_day: float = 9.0       # food a food worker makes a day (net of walking)
    food_worker_share: float = 0.30        # share of adults on food
    food_drought_factor: float = 0.0       # production share kept in a drought (irrigated / hardy crops)
    plants_die_after: float = 99.0         # drought days after which crops die (then regrow lag applies)
    regrow_lag: float = 4.0                # days after a drought ends before fields yield again, if they died
    stock_days_target: float = 6.0         # the player keeps this many days of food in store when possible
    store_cap_per_capita: float = 40.0
    ringtail_jobs: object = None           # function(day, n_inkpaw_adults) -> Ringtail job slots, or None
    ringtails_arrive: float = 1e9          # day the first Moon Loft brings 3 adults + 1 kit
    gated_births_wellbeing: float = None   # optional: no births below this wellbeing


def run(cfg, days=120, seed=1, droughts=(), flowering=None, start_food=130):
    """droughts: list of (start_day, length). flowering: (day, share of food production lost, recovery days)."""
    rng = random.Random(seed)
    people = []
    for _ in range(V.START_ADULTS):
        people.append(Person("I", True, rng.uniform(*V.START_ADULT_LIFE_PROGRESS), rng.uniform(0.9, 1.1)))
    for _ in range(V.START_CHILDREN):
        p = Person("I", False, 0.0, rng.uniform(0.9, 1.1), child=rng.uniform(*V.START_CHILD_PROGRESS))
        p.life = p.child * cfg.childhood / cfg.lifespan
        people.append(p)
    beds = 15.0
    food = float(start_food)
    hist = []
    regrow_until = -1
    deaths_age = deaths_starve = births = 0
    for day in range(days):
        n = len(people)
        if n == 0:
            hist.append(dict(day=day, pop=0, adults=0, children=0, food=food, ringtails=0, wb=0))
            continue
        adults = [p for p in people if p.adult]
        wb = cfg.wellbeing(day, n) if cfg.wellbeing else 8
        # --- food -------------------------------------------------------------------------------------------
        in_drought = any(s <= day < s + l for s, l in droughts)
        died_now = any(s + cfg.plants_die_after <= day < s + l for s, l in droughts)
        for s, l in droughts:
            if l > cfg.plants_die_after and day == s + l:
                regrow_until = day + cfg.regrow_lag
        factor = 1.0
        if died_now or day < regrow_until:
            factor = cfg.food_drought_factor
        elif in_drought:
            factor = max(cfg.food_drought_factor, 0.15)    # ripe crops still harvested while plants pause
        if flowering and flowering[0] <= day < flowering[0] + flowering[2]:
            factor *= 1 - flowering[1]
        hungry_share = sum(1 for p in adults if p.hunger_days > 0) / max(1, len(adults))
        workers = len(adults) * cfg.food_worker_share * (1 - 0.5 * hungry_share)
        target = n * V.FOOD_PER_DAY * (1 + cfg.stock_days_target / 30.0)
        produced = min(workers * cfg.food_per_worker_day, target) * factor
        food = min(food + produced, cfg.store_cap_per_capita * n)
        need = n * V.FOOD_PER_DAY
        eaten = min(food, need)
        food -= eaten
        short = 1 - eaten / need
        # starvation: the hungriest go without; Hunger reaches 0 after 1.25 days, death 3.75 days later
        k = int(round(short * n))
        order = sorted(people, key=lambda p: -p.hunger_days)
        for i, p in enumerate(order):
            if i < k:
                p.hunger_days += 1
            else:
                p.hunger_days = 0.0
        starving = [p for p in people if p.hunger_days >= 5.0]
        for p in starving:
            people.remove(p)
            deaths_starve += 1
        # --- ageing -------------------------------------------------------------------------------------------
        life_mult = 1 + tier_delta("LifeExpectancy", wb)
        grow_mult = 1 + tier_delta("GrowthSpeed", wb)
        for p in list(people):
            p.life += 1.0 / (cfg.lifespan * life_mult)
            if not p.adult:
                p.child += grow_mult * (0.6 if p.hunger_days > 1.25 else 1.0) / cfg.childhood
                if p.child >= 1:
                    p.adult = True
            if p.life >= p.longevity:
                people.remove(p)
                deaths_age += 1
        # --- housing ------------------------------------------------------------------------------------------
        adults = [p for p in people if p.adult]
        n = len(people)
        if beds < n * (1 + cfg.free_beds_target) and n < cfg.max_population:
            beds += 1.0 + cfg.beds_per_adult_day * len(adults)
        # --- births -------------------------------------------------------------------------------------------
        children = [p for p in people if not p.adult]
        child_slots = int(beds // 3)
        hungry = sum(1 for p in adults if p.hunger_days > 1.25) > len(adults) / 2
        gate_ok = cfg.gated_births_wellbeing is None or wb >= cfg.gated_births_wellbeing
        if day == int(cfg.ringtails_arrive):
            for _ in range(3):
                people.append(Person("R", True, rng.uniform(0.2, 0.4), rng.uniform(0.9, 1.1)))
            people.append(Person("R", False, 0.0, rng.uniform(0.9, 1.1)))
        if not hungry and gate_ok and n < cfg.max_population:
            in_homes = [p for p in adults if p.kind == "I"]
            pairs = len(in_homes) // 2
            free_slots = min(child_slots - len([c for c in children if c.kind == "I"]), pairs)
            p_day = 1 - (1 - cfg.birth_chance) ** (cfg.entries_per_adult_day * 2)
            for _ in range(max(0, free_slots)):
                if rng.random() < p_day and len(people) < min(beds, cfg.max_population):
                    people.append(Person("I", False, 0.0, rng.uniform(0.9, 1.1)))
                    births += 1
            if cfg.ringtail_jobs and day >= cfg.ringtails_arrive:
                r_ad = [p for p in adults if p.kind == "R"]
                r_kids = [p for p in people if p.kind == "R" and not p.adult]
                open_jobs = cfg.ringtail_jobs(day, len(in_homes)) - len(r_ad) - len(r_kids)
                lofts = max(1, len(r_ad) // 3)
                for _ in range(min(lofts - len(r_kids), max(0, open_jobs))):
                    if len(r_ad) >= 2 and rng.random() < p_day:
                        people.append(Person("R", False, 0.0, rng.uniform(0.9, 1.1)))
                        births += 1
        hist.append(dict(day=day, pop=len(people), adults=sum(p.adult for p in people),
                         children=sum(not p.adult for p in people), food=round(food),
                         ringtails=sum(p.kind == "R" for p in people), wb=wb, beds=round(beds)))
    return dict(hist=hist, deaths_age=deaths_age, deaths_starve=deaths_starve, births=births)


def first_day(hist, pop):
    for h in hist:
        if h["pop"] >= pop:
            return h["day"]
    return None
