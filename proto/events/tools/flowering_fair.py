"""How long may the rest after the first Great Flowering be? (docs/tech/events.md, section 5)

Colony model (tools/sim popsim): 60 colonists, shoots 35% of food, crops pause in a drought, the Flowering on cycle day 1
(day 96) and a 7-day drought on cycle day 13 or 17, pantries of 2, 6 and 11 days, 10 seeds each.

    E:\\PandabornDev\\tools\\venv\\Scripts\\python.exe proto/events/tools/flowering_fair.py
"""
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "tools" / "sim"))
from pandasim import popsim as P  # noqa: E402
from pandasim import scenarios as S  # noqa: E402

FLOWERING_DAY = 96


def main() -> None:
    print("gap_days drought_on_cycle_day pantry_days pop_before lowest starved min_food")
    for gap, cycle_day in ((0, 13), (9, 13), (12, 13), (12, 17), (15, 13), (15, 17)):
        for stock in (2, 6, 11):
            res = []
            for seed in range(10):
                cfg = P.PopConfig("x", wellbeing=S._wb_ramp, stock_days_target=stock, max_population=60,
                                  food_per_worker_day=20, food_worker_share=0.25, plants_die_after=99, food_drought_factor=0.1)
                flowering = (FLOWERING_DAY, 0.35, gap) if gap else None
                r = P.run(cfg, days=140, seed=seed, droughts=[(FLOWERING_DAY + cycle_day, 7)], flowering=flowering)
                h = r["hist"]
                res.append((h[FLOWERING_DAY - 1]["pop"], min(x["pop"] for x in h[FLOWERING_DAY:]), r["deaths_starve"],
                            min(x["food"] for x in h[FLOWERING_DAY:FLOWERING_DAY + 29])))
            print(gap, cycle_day, stock, *(statistics.median(x[i] for x in res) for i in range(4)))


if __name__ == "__main__":
    main()
