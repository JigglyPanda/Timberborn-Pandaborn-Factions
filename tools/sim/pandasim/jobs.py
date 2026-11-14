"""What one worker produces in one shift, job by job.

Workshops are simulated action by action in the vanilla order (produce > empty output > fill input > idle, 4.2), so
self-supply, buffer sizes and night couriers come out of the rules rather than being assumed. Field, forest and
carrying jobs are closed-form: walking at the empty and the loaded speed, plus work time divided by working speed.
"""
import math
from dataclasses import dataclass, field

from . import vanilla as V


# --- workshops -------------------------------------------------------------------------------------------------------

@dataclass
class ShopState:
    inp: dict = field(default_factory=dict)
    out: float = 0.0
    prog: float = 0.0
    active: bool = False


def caps(recipe):
    cin = {g: n * recipe.cycles_capacity for g, n in recipe.inputs.items()}
    if recipe.fuel:
        cin[recipe.fuel[0]] = max(1, math.ceil(recipe.cycles_capacity / recipe.fuel[1]))
    cout = sum(recipe.outputs.values()) * recipe.cycles_capacity
    return cin, cout


def per_cycle_inputs(recipe):
    need = dict(recipe.inputs)
    if recipe.fuel:
        need[recipe.fuel[0]] = need.get(recipe.fuel[0], 0) + 1.0 / recipe.fuel[1]
    return need


def workshop_shift(recipe, ctx, state=None, d_in=15.0, d_out=15.0, haulers=False, weights=None, workers=1):
    """Run one shift of a workshop. Returns (stats, end state).

    haulers=True: a day hauling crew keeps inputs topped and outputs drained (the worker only produces; 5% lag).
    weights: override good weights (for new goods).
    """
    weights = weights or {}
    w = lambda g: weights.get(g, V.WEIGHT.get(g, 1))
    cin, cout = caps(recipe)
    need = per_cycle_inputs(recipe)
    out_amt = sum(recipe.outputs.values())
    st = state or ShopState(inp={g: 0.0 for g in cin})
    for g in cin:
        st.inp.setdefault(g, 0.0)
    H = ctx.work_hours()
    ws = ctx.ws() * workers
    t = prod_h = walk_h = 0.0
    cycles = 0
    delivered = 0.0
    fetched = {g: 0.0 for g in cin}
    if haulers:
        prod_hours = H * 0.95
        n = prod_hours * ws / recipe.cycle_h
        stats = dict(cycles=n, output=n * out_amt, prod_h=prod_hours, walk_h=0.0, uptime=0.95 * H / max(H, 1e-9),
                     used={g: n * a for g, a in need.items()})
        return stats, st
    while t < H - 1e-9:
        have_inputs = st.active or all(st.inp[g] + 1e-9 >= a for g, a in need.items())
        if have_inputs and st.out + out_amt <= cout + 1e-9:
            if not st.active:
                for g, a in need.items():
                    st.inp[g] -= a
                st.active = True
            dt = min(0.25, H - t, (1 - st.prog) * recipe.cycle_h / ws)
            st.prog += dt * ws / recipe.cycle_h
            t += dt
            prod_h += dt
            if st.prog >= 1 - 1e-9:
                st.prog = 0.0
                st.active = False
                st.out += out_amt
                cycles += 1
            continue
        if st.out > 1e-9:
            good = next(iter(recipe.outputs))
            carry = min(st.out, ctx.load(good, weight=w(good)))
            trip = ctx.round_trip(d_out)
            t += trip
            walk_h += trip
            st.out -= carry
            delivered += carry
            continue
        low = [(st.inp[g] / c, g) for g, c in cin.items() if st.inp[g] < c - 1e-9]
        if low:
            _, g = min(low)
            amount = min(ctx.load(g, weight=w(g)), cin[g] - st.inp[g])
            trip = ctx.round_trip(d_in)
            t += trip
            walk_h += trip
            st.inp[g] += amount
            fetched[g] += amount
            continue
        break  # nothing to do: idle
    stats = dict(cycles=cycles, output=cycles * out_amt, prod_h=prod_h, walk_h=walk_h,
                 uptime=prod_h / H if H else 0.0, fetched=fetched, delivered=delivered)
    return stats, st


def workshop_steady(recipe, ctx, days=8, d_in=15.0, d_out=15.0, couriers=False, haulers=False, weights=None,
                    courier_load=None):
    """Average daily output over several shifts after a warm-up. couriers=True: between shifts a night crew fills
    every input to its cap and empties the output (what a Courier Loft does). Returns dict incl. courier loads/day."""
    weights = weights or {}
    cin, cout = caps(recipe)
    st = ShopState(inp={g: 0.0 for g in cin})
    outs, upt, courier_loads = [], [], []
    for day in range(days):
        if couriers:
            loads = 0
            for g, c in cin.items():
                gap = c - st.inp[g]
                if gap > 0 and courier_load:
                    loads += math.ceil(gap / courier_load(g))
                st.inp[g] = c
            if st.out > 0 and courier_load:
                loads += math.ceil(st.out / courier_load(next(iter(recipe.outputs))))
            st.out = 0.0
            courier_loads.append(loads)
        s, st = workshop_shift(recipe, ctx, st, d_in, d_out, haulers=haulers, weights=weights)
        outs.append(s["output"])
        upt.append(s["uptime"])
    k = max(1, days // 3)
    return dict(output=sum(outs[k:]) / len(outs[k:]), uptime=sum(upt[k:]) / len(upt[k:]),
                courier_loads=(sum(courier_loads[k:]) / len(courier_loads[k:])) if courier_loads else 0)


# --- fields and forests ----------------------------------------------------------------------------------------------

def gatherer_day(ctx, pick_h, yield_per_plant, good_weight=1, d_plant=8.0, d_store=10.0, flag_inventory=20):
    """A gatherer: one plant per trip (7.1), output kept at the flag, flag emptied when full."""
    per_trip_units = min(ctx.load("", weight=good_weight), yield_per_plant)
    trip = ctx.round_trip(d_plant) + pick_h / ctx.ws()
    empty = ctx.round_trip(d_store) / ctx.load("", weight=good_weight)   # per unit, flag to storage
    per_unit = trip / per_trip_units + empty
    return ctx.work_hours() / per_unit


def farmer_day(ctx, plant, d_field=6.0, d_store=10.0, inventory=50):
    """A farmer on one crop: plant (short hop between tiles), walk out, harvest, carry back; empty the farmhouse."""
    ws = ctx.ws()
    plant_walk = 1.5 / ctx.v_empty()
    per_tile = plant.plant_h / ws + plant_walk + plant.harvest_h / ws + ctx.round_trip(d_field)
    per_unit_store = ctx.round_trip(d_store) / ctx.load(plant.good or "", weight=1)
    units_per_tile = plant.yield_n
    per_unit = per_tile / units_per_tile + per_unit_store
    return dict(units=ctx.work_hours() / per_unit, tiles=ctx.work_hours() / per_unit / units_per_tile * plant.grow_d,
                per_tile_h=per_tile)


def planter_day(ctx, plant_h, d_hop=3.0):
    """Forester / grove keeper: plants marked spots in range, short hops between spots."""
    return ctx.work_hours() / (plant_h / ctx.ws() + d_hop / ctx.v_empty())


def woodcutter_day(ctx, cut_h, logs, log_weight=6, d_tree=10.0, d_store=12.0):
    """Cut one tree per trip; extra logs stay as a stack and need more trips (7.1); the flag is emptied to storage."""
    load = ctx.load("", weight=log_weight)
    trips = math.ceil(logs / load)
    per_tree = cut_h / ctx.ws() + trips * ctx.round_trip(d_tree)
    per_unit = per_tree / logs + ctx.round_trip(d_store) / load
    return ctx.work_hours() / per_unit


def build_hours(cost, ctx, d_src=15.0, weights=None, build_time=None):
    """Builder-hours for one building: deliver every unit at normal lifting, then build (6)."""
    weights = weights or {}
    trips = 0
    for g, n in cost.items():
        wt = weights.get(g, V.WEIGHT.get(g, 1))
        trips += math.ceil(n / ctx.load(g, weight=wt))
    units = sum(cost.values())
    bh = build_time if build_time is not None else max(1, math.ceil(units / V.UNITS_PER_BUILD_HOUR))
    return dict(trips=trips, walk_h=trips * ctx.round_trip(d_src), build_h=bh / ctx.ws(),
                total=trips * ctx.round_trip(d_src) + bh / ctx.ws())


def builder_units_per_day(ctx, mix, d_src=15.0, weights=None):
    """Material units a builder delivers and builds per shift for a cost mix {good: share}."""
    weights = weights or {}
    h_per_unit = 0.0
    for g, share in mix.items():
        wt = weights.get(g, V.WEIGHT.get(g, 1))
        h_per_unit += share * (ctx.round_trip(d_src) / ctx.load(g, weight=wt) + 1 / V.UNITS_PER_BUILD_HOUR / ctx.ws())
    return ctx.work_hours() / h_per_unit


def hauler_day(ctx, good_weight, d=20.0, carry_bonus=V.HAULER_CARRY_BONUS):
    load = ctx.load("", carry_bonus=carry_bonus, weight=good_weight)
    return ctx.work_hours() / ctx.round_trip(d) * load
