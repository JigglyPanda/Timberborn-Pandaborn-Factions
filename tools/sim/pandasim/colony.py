"""Hour-by-hour opening simulator (the first two to four weeks of a game, including the first drought).

What it tracks: every colonist's Hunger and Thirst, the stock of each good, every marked tile (empty, growing,
grown, dying), wild berry bushes, a build queue, builders delivering and building, and workers in their jobs during
working hours. Every work action costs the time the mechanics reference gives it: walking empty and loaded, work
time divided by working speed. Colonists eat and drink one unit per bite after work, or at any hour when critical.

It is not an agent simulation: workers are pooled per job and spend each working hour on the job's next action.
That keeps it readable while keeping what limits an opening: logs, walking, growth timers, the build queue.
"""
import math
import random
from dataclasses import dataclass, field

from . import vanilla as V
from .mech import Ctx
from .jobs import build_hours


@dataclass
class Project:
    name: str
    cost: dict
    jobs: dict = field(default_factory=dict)      # job -> slots when finished
    beds: int = 0
    water_cap: int = 0
    on_done: object = None                        # callback(sim)
    deliver_left: float = None
    build_left: float = None
    started: bool = False
    done_at: float = None


@dataclass
class Plot:
    """Marked tiles of one plant. stage: 0 empty, 1 growing, 2 grown, 3 dead (must be cleared)."""
    key: str
    n: int
    grow_d: float
    dry_d: float
    harvest_good: str = ""
    harvest_n: int = 0
    fruit_good: str = ""
    fruit_n: int = 0
    fruit_d: float = 0.0

    def __post_init__(self):
        self.stage = [0] * self.n
        self.left = [0.0] * self.n
        self.fruit_left = [0.0] * self.n
        self.dry = [0.0] * self.n
        self.dry_limit = [self.dry_d] * self.n

    def tick(self, dt, drought, rng):
        for i in range(self.n):
            if self.stage[i] in (1, 2) and drought:
                if self.dry[i] == 0.0:
                    self.dry_limit[i] = self.dry_d * rng.uniform(0.9, 1.1)
                self.dry[i] += dt
                if self.dry[i] >= self.dry_limit[i]:
                    self.stage[i] = 3
                continue                          # dying: growth and fruit paused
            self.dry[i] = 0.0                     # timer resets fully when water returns
            if self.stage[i] == 1:
                self.left[i] -= dt
                if self.left[i] <= 0:
                    self.stage[i] = 2
                    self.fruit_left[i] = self.fruit_d
            elif self.stage[i] == 2 and self.fruit_d and self.fruit_left[i] > 0:
                self.fruit_left[i] -= dt

    def idx(self, st):
        return [i for i in range(self.n) if self.stage[i] == st]

    def ripe_fruit(self):
        return [i for i in range(self.n) if self.stage[i] == 2 and self.fruit_d and self.fruit_left[i] <= 0]


class Opening:
    def __init__(self, cfg, mode="Normal", seed=1, wild_bushes=30, days=14, work_hours=None, drought=None):
        """drought: (start_day, length_days) in days since the game started, or None."""
        self.cfg = cfg
        self.mode = V.MODES[mode]
        self.rng = random.Random(seed)
        self.days = days
        self.sp = cfg["species"]
        self.W = work_hours or cfg["work_hours"]
        self.drought = drought
        n_ad, n_ch = V.START_ADULTS, V.START_CHILDREN
        self.adult = [True] * n_ad + [False] * n_ch
        self.child_left = [0.0] * n_ad + [V.DAYS_OF_CHILDHOOD * (1 - self.rng.uniform(*V.START_CHILD_PROGRESS))
                                          for _ in range(n_ch)]
        n = n_ad + n_ch
        self.hunger = [1.0] * n
        self.thirst = [1.0] * n
        self.alive = [True] * n
        self.stock = {"Berries": self.mode.start_berries, "Water": self.mode.start_water, "Log": 0}
        self.last_eaten = {}
        self.wild_ripe = wild_bushes
        self.wild_regrow = []
        self.plots = {}
        self.projects = [Project(**p) for p in cfg["build_order"]]
        self.slots = {"builder": cfg.get("builders", V.DC_BUILDERS_DEFAULT)}
        self.beds = 0
        self.water_cap = 0
        self.log = []
        self.events = []
        self.first = {}
        self.t = 0.0
        self.deaths = 0
        self.eaten = {}
        self.hungry_colonist_hours = 0
        self.min_food = 1e9
        self.units_built = 0
        self.death_cause = {"hunger": 0, "thirst": 0}
        self.thirsty_colonist_hours = 0

    # --- helpers ------------------------------------------------------------------------------------------------
    def hour(self):
        return (V.NEW_GAME_HOUR + self.t) % 24

    def day(self):
        """Days since game start (day 1 hour 4 = 0)."""
        return self.t / 24.0

    def in_drought(self):
        if not self.drought:
            return False
        s, n = self.drought
        return s <= self.day() < s + n

    def alive_idx(self):
        return [i for i in range(len(self.alive)) if self.alive[i]]

    def adults(self):
        return [i for i in self.alive_idx() if self.adult[i]]

    def wellbeing(self):
        idx = self.alive_idx()
        if not idx:
            return 0
        housed = min(1.0, self.beds / len(idx))
        dishes = sum(wb for g, wb in self.cfg["dishes"].items()
                     if g in self.last_eaten and self.day() - self.last_eaten[g] <= 4)
        total = 0.0
        for i in idx:
            w = (1 if self.hunger[i] > 0 else -10) + (1 if self.thirst[i] > 0 else -10) + 1
            w += housed * 1 + (1 - housed) * -3 + dishes + self.cfg.get("base_wellbeing", 0)
            total += w
        return total / len(idx)

    def ctx(self):
        ad = self.adults()
        hungry = sum(1 for i in ad if self.hunger[i] <= 0) > len(ad) / 2
        return Ctx(self.sp, hours=self.W, wb=max(0, self.wellbeing()), hungry=hungry,
                   commute=self.cfg.get("commute", 15))

    def note_first(self, key):
        if key not in self.first:
            self.first[key] = round(self.day(), 2)

    def food_total(self):
        return sum(self.stock.get(g, 0) for g in self.cfg["food_order"])

    # --- one hour ---------------------------------------------------------------------------------------------------
    def step(self):
        dt = 1 / 24
        dr = self.in_drought()
        for p in self.plots.values():
            p.tick(dt, dr, self.rng)
        if not dr:
            self.wild_regrow = [d - dt for d in self.wild_regrow]
            self.wild_ripe += sum(1 for d in self.wild_regrow if d <= 0)
            self.wild_regrow = [d for d in self.wild_regrow if d > 0]
        # the first day starts at hour 4, so it has W - 4 working hours (1.1)
        working = self.hour() < self.W and not (self.t < 24 - V.NEW_GAME_HOUR and self.hour() < V.NEW_GAME_HOUR)
        employed = set()
        if working:
            employed = self.work_hour(self.ctx())
        self.consume(employed)
        self.grow_children(dt)
        self.min_food = min(self.min_food, self.food_total())
        self.t += 1

    def assign(self):
        """Adults to jobs: builders first, then the faction's priority list (4.1: priority, then age)."""
        free = self.adults()
        out = {}
        for job in ["builder"] + self.cfg["priorities"]:
            k = min(self.slots.get(job, 0), len(free))
            if k:
                out[job] = free[:k]
                free = free[k:]
        return out

    def work_hour(self, c):
        employed = set()
        for job, workers in self.assign().items():
            employed.update(workers)
            for _ in workers:
                getattr(self, "job_" + job)(c)
        return employed

    def chance(self, frac):
        return frac >= 1.0 or self.rng.random() < frac

    # --- jobs (each call spends one worker-hour) ----------------------------------------------------------------
    def job_builder(self, c):
        budget = 1.0
        for p in self.projects:
            if p.done_at is not None:
                continue
            if not p.started:
                if not all(self.stock.get(g, 0) >= n for g, n in p.cost.items()):
                    # wait for logs in queue order; skip ahead only past a project that needs a good not yet made
                    if all(self.stock.get(g, 0) >= n for g, n in p.cost.items() if g == "Log"):
                        continue
                    break
                for g, n in p.cost.items():
                    self.stock[g] -= n
                bh = build_hours(p.cost, c, d_src=self.cfg.get("build_distance", 15), weights=self.cfg.get("weights"))
                p.deliver_left, p.build_left, p.started = bh["walk_h"], bh["build_h"], True
            use = min(budget, p.deliver_left + p.build_left)
            take = min(use, p.deliver_left)
            p.deliver_left -= take
            p.build_left -= use - take
            budget -= use
            if p.deliver_left <= 1e-9 and p.build_left <= 1e-9:
                self.finish(p)
            if budget <= 1e-9:
                break

    def finish(self, p):
        p.done_at = self.day()
        self.units_built += sum(p.cost.values())
        for j, n in p.jobs.items():
            self.slots[j] = self.slots.get(j, 0) + n
        self.beds += p.beds
        self.water_cap += p.water_cap
        if p.on_done:
            p.on_done(self)
        self.events.append((round(p.done_at, 2), p.name))

    def job_pump(self, c):
        if self.in_drought() and self.day() - self.drought[0] > 1.0:
            return                                 # the river at the intake has drained
        if self.stock["Water"] < self.water_cap:
            rate = c.ws() / 0.33 * 0.88            # 12% of the hour carrying to the tank next door
            self.stock["Water"] = min(self.water_cap, self.stock["Water"] + rate)

    def job_woodcutter(self, c):
        budget = 1.0
        timber = self.plots.get("timber")
        while budget > 1e-6:
            if timber and self.stock.get("Pole", 0) < self.cfg.get("pole_target", 40) and timber.idx(2):
                i = timber.idx(2)[0]
                ts = self.cfg["timber_spec"]
                load = c.load("", weight=ts["weight"])
                cost = ts["cut_h"] / c.ws() + math.ceil(ts["poles"] / load) * c.round_trip(ts["d"])
                frac = min(1.0, budget / cost)
                budget -= cost * frac
                if self.chance(frac):
                    timber.stage[i] = 0
                    self.stock["Pole"] = self.stock.get("Pole", 0) + ts["poles"]
                    self.note_first("poles")
                continue
            tr = self.cfg["trees"]
            load = c.load("Log")
            cost = tr["cut_h"] / c.ws() + math.ceil(tr["logs"] / load) * c.round_trip(tr["d"])
            self.stock["Log"] += tr["logs"] * budget / cost
            budget = 0

    def job_gatherer(self, c):
        budget = 1.0
        while budget > 1e-6 and self.wild_ripe > 0:
            cost = 0.8 / c.ws() + c.round_trip(self.cfg.get("berry_distance", 12))
            frac = min(1.0, budget / cost)
            self.stock["Berries"] += 3 * frac
            budget -= cost * frac
            if self.chance(frac):
                self.wild_ripe -= 1
                self.wild_regrow.append(12.0)

    def job_forester(self, c):
        budget = 1.0
        timber = self.plots.get("timber")
        if not timber or self.in_drought():
            return
        ph = self.cfg["timber_spec"]["plant_h"]
        for i in timber.idx(3) + timber.idx(0):
            cost = ph / c.ws() + 3 / c.v_empty()
            if budget < cost:
                return
            budget -= cost
            timber.stage[i], timber.left[i] = 1, timber.grow_d

    def job_farmer(self, c):
        """Farmhouse worker: plant first, else harvest (4.4). Dead crops are cleared and replanted after drought."""
        budget = 1.0
        while budget > 1e-6:
            done = False
            for key in self.cfg["fields"]:
                plot = self.plots.get(key)
                if not plot:
                    continue
                fs = self.cfg["field_spec"][key]
                empty = [] if self.in_drought() else plot.idx(0) + plot.idx(3)
                if empty:
                    cost = fs["plant_h"] / c.ws() + 1.5 / c.v_empty()
                    frac = min(1.0, budget / cost)
                    budget -= cost * frac
                    if self.chance(frac):
                        i = empty[0]
                        plot.stage[i], plot.left[i] = 1, plot.grow_d
                    done = True
                    break
            if done:
                continue
            for key in self.cfg["fields"]:
                plot = self.plots.get(key)
                if not plot or not plot.idx(2):
                    continue
                fs = self.cfg["field_spec"][key]
                cost = fs["harvest_h"] / c.ws() + c.round_trip(fs["d"])
                frac = min(1.0, budget / cost)
                budget -= cost * frac
                if self.chance(frac):
                    plot.stage[plot.idx(2)[0]] = 0
                    self.stock[plot.harvest_good] = self.stock.get(plot.harvest_good, 0) + plot.harvest_n
                    self.note_first(plot.harvest_good)
                done = True
                break
            if not done:
                break

    def job_cook(self, c):
        """A kitchen next to the farmstead: converts a raw food to a cooked one (self-supplied, short trips)."""
        rc = self.cfg["cook_recipe"]
        if self.stock.get(rc["in"], 0) < 1:
            return
        cycles = min(c.ws() * rc["uptime"] / rc["cycle_h"], self.stock[rc["in"]])
        self.stock[rc["in"]] -= cycles
        self.stock[rc["out"]] = self.stock.get(rc["out"], 0) + cycles * rc["ratio"]
        self.note_first(rc["out"])

    def job_mill(self, c):
        rate = self.cfg.get("mill_rate_per_h", 0.42)
        n = min(rate * c.ws(), self.stock.get("Log", 0))
        self.stock["Log"] -= n
        self.stock["Plank"] = self.stock.get("Plank", 0) + n

    def job_inventor(self, c):
        self.stock["Science"] = self.stock.get("Science", 0) + c.ws()

    # --- people -------------------------------------------------------------------------------------------------
    def consume(self, employed):
        k = self.mode.consumption
        for i in self.alive_idx():
            self.hunger[i] -= V.HUNGER_PER_DAY * k / 24
            self.thirst[i] -= V.THIRST_PER_DAY * k / 24
            free = i not in employed
            if (free or self.hunger[i] <= 0) and self.hunger[i] <= 0.7:
                for g in self.cfg["food_order"]:
                    if self.stock.get(g, 0) >= 1:
                        self.stock[g] -= 1
                        self.hunger[i] += V.FOOD_POINTS
                        self.eaten[g] = self.eaten.get(g, 0) + 1
                        self.last_eaten[g] = self.day()
                        break
            if (free or self.thirst[i] <= 0) and self.thirst[i] <= 0.67 and self.stock.get("Water", 0) >= 1:
                self.stock["Water"] -= 1
                self.thirst[i] += V.WATER_POINTS
            if self.hunger[i] <= 0:
                self.hungry_colonist_hours += 1
                self.note_first("hunger")
            if self.thirst[i] <= 0:
                self.thirsty_colonist_hours += 1
                self.note_first("thirst")
            if self.hunger[i] <= V.HUNGER_MIN or self.thirst[i] <= V.THIRST_MIN:
                self.alive[i] = False
                self.deaths += 1
                self.death_cause["thirst" if self.thirst[i] <= V.THIRST_MIN else "hunger"] += 1
                self.note_first("death")

    def grow_children(self, dt):
        for i in self.alive_idx():
            if not self.adult[i]:
                self.child_left[i] -= dt * (0.6 if self.hunger[i] <= 0 else 1.0)
                if self.child_left[i] <= 0:
                    self.adult[i] = True

    def run(self):
        for _ in range(int(self.days * 24)):
            self.step()
            if int(self.t) % 12 == 0:
                self.log.append(dict(day=round(self.day(), 1), food=round(self.food_total()),
                                     water=round(self.stock["Water"]), logs=round(self.stock["Log"]),
                                     poles=round(self.stock.get("Pole", 0)), wb=round(self.wellbeing(), 1),
                                     alive=len(self.alive_idx()), built=self.units_built))
        return self
