"""Opening build orders for the hourly simulator: vanilla Folktails and the proposed Inkpaws.

Both follow the reflexes the design counts on: pump, gatherer, woodcutters, a farm with the first crop, homes,
storage, an inventor. The filler at the end is a common basket of buildings (half logs, half planks or poles),
used to measure how much a colony builds by a given day.
"""
from dataclasses import replace

from . import vanilla as V
from .colony import Plot
from .mech import FOLKTAIL
from . import stats as S


def _plot(key, n, spec):
    def cb(sim):
        sim.plots[key] = Plot(key, n, spec["grow_d"], spec["dry_d"], spec.get("good", ""), spec.get("yield_n", 0))
    return cb


CARROT = dict(grow_d=4, dry_d=2, good="Carrot", yield_n=3, plant_h=0.2, harvest_h=1.2, d=6)


def _filler(plank):
    """Common basket after the opening: 50% logs, 50% planks/poles + a few gears' worth in planks."""
    out = []
    for i in range(6):
        out += [dict(name=f"Home {6 + i}", cost={"Log": 12}, beds=3),
                dict(name=f"Workshop {i}", cost={"Log": 15, plank: 25}),
                dict(name=f"Storage {i}", cost={"Log": 15}),
                dict(name=f"Post {i}", cost={"Log": 10, plank: 15})]
    return out


def folktails(n_fields=60, carrot=None):
    carrot = carrot or CARROT
    order = [
        dict(name="Lumberjack Flag", cost={}, jobs={"woodcutter": 1}),
        dict(name="Lumberjack Flag", cost={}, jobs={"woodcutter": 1}),
        dict(name="Gatherer Flag", cost={}, jobs={"gatherer": 1}),
        dict(name="Water Pump", cost={"Log": 12}, jobs={"pump": 1}, water_cap=15),
        dict(name="Efficient Farmhouse", cost={"Log": 25}, jobs={"farmer": 3},
             on_done=_plot("carrot", n_fields, carrot)),
        dict(name="Lodge 1", cost={"Log": 12}, beds=3),
        dict(name="Lodge 2", cost={"Log": 12}, beds=3),
        dict(name="Small Tank", cost={"Log": 15}, water_cap=30),
        dict(name="Lodge 3", cost={"Log": 12}, beds=3),
        dict(name="Lumber Mill", cost={"Log": 15}, jobs={"mill": 1}),
        dict(name="Lodge 4", cost={"Log": 12}, beds=3),
        dict(name="Inventor", cost={"Log": 12}, jobs={"inventor": 1}),
        dict(name="Lodge 5", cost={"Log": 12}, beds=3),
        dict(name="Small Tank 2", cost={"Log": 15}, water_cap=30),
    ] + _filler("Plank")
    return dict(species=FOLKTAIL, work_hours=16, builders=2, order_name="Folktails",
                build_order=order, priorities=["pump", "gatherer", "farmer", "woodcutter", "mill", "inventor"],
                fields=["carrot"], field_spec={"carrot": carrot}, dishes={"Carrot": 1},
                food_order=["Carrot", "Berries"], trees=dict(cut_h=1.5, logs=2, d=10), base_wellbeing=0)


def inkpaws(species=None, n_shoots=40, n_cabbage=12, n_timber=24, shoot=None, timber=None, pole_weight=3,
            steamer=True, cabbage=None):
    sp = species or S.INKPAW
    shoot = shoot or S.plant_model("PandabornShootBamboo")
    cabbage = cabbage or S.plant_model("PandabornCabbage")
    timber = timber or S.plant_model("PandabornTimberBamboo")
    shoot_spec = dict(grow_d=shoot["grow_d"], dry_d=shoot["dry_d"], good="Shoots", yield_n=shoot["yield_n"],
                      plant_h=shoot["plant_h"], harvest_h=shoot["harvest_h"], d=6)
    cab_spec = dict(grow_d=cabbage["grow_d"], dry_d=cabbage["dry_d"], good="Cabbage", yield_n=cabbage["yield_n"],
                    plant_h=cabbage["plant_h"], harvest_h=cabbage["harvest_h"], d=8)
    t_spec = dict(grow_d=timber["grow_d"], dry_d=timber["dry_d"], plant_h=timber["plant_h"], cut_h=timber["cut_h"],
                  poles=timber["poles"], weight=pole_weight, d=10)

    def farm(sim):
        _plot("shoots", n_shoots, shoot_spec)(sim)
        _plot("cabbage", n_cabbage, cab_spec)(sim)

    order = [
        dict(name="Lumberjack Flag", cost={}, jobs={"woodcutter": 1}),
        dict(name="Lumberjack Flag", cost={}, jobs={"woodcutter": 1}),
        dict(name="Gatherer Flag", cost={}, jobs={"gatherer": 1}),
        dict(name="Water Pump", cost={"Log": 12}, jobs={"pump": 1}, water_cap=15),
        dict(name="Farmstead", cost={"Log": 25}, jobs={"farmer": 3}, on_done=farm),
        dict(name="Den 1", cost={"Log": 12}, beds=3),
        dict(name="Forester", cost={"Log": 12}, jobs={"forester": 1},
             on_done=_plot("timber", n_timber, dict(grow_d=t_spec["grow_d"], dry_d=t_spec["dry_d"]))),
        dict(name="Den 2", cost={"Log": 12}, beds=3),
        dict(name="Small Cistern", cost={"Log": 15}, water_cap=30),
        dict(name="Den 3", cost={"Log": 12}, beds=3),
        dict(name="Den 4", cost={"Log": 12}, beds=3),
        dict(name="Inventor", cost={"Log": 12}, jobs={"inventor": 1}),
        dict(name="Den 5", cost={"Log": 12}, beds=3),
        dict(name="Small Cistern 2", cost={"Log": 15}, water_cap=30),
    ]
    if steamer:
        order.insert(9, dict(name="Steamer", cost={"Log": 20, "Pole": 5}, jobs={"cook": 1}))
    order += _filler("Pole")
    st = S.recipe("PandabornSteamedShoots")
    return dict(species=sp, work_hours=16, builders=2, order_name=sp.name, build_order=order,
                priorities=["pump", "farmer", "gatherer", "woodcutter", "forester", "cook", "inventor"],
                fields=["shoots", "cabbage"], field_spec={"shoots": shoot_spec, "cabbage": cab_spec},
                dishes={"Cabbage": 1, "SteamedShoots": 1}, strict_order=False,
                food_order=["SteamedShoots", "Cabbage", "Shoots", "Berries"], trees=dict(cut_h=1.5, logs=2, d=10),
                timber_spec=t_spec, weights={"Pole": pole_weight}, pole_target=40,
                cook_recipe=dict(**{"in": "Shoots", "out": "SteamedShoots"}, ratio=st["ratio"],
                                 cycle_h=st["cycle_h"], uptime=0.7), base_wellbeing=0)
