"""Render the proposed stat sheet (stats.py) as Markdown tables and as JSON for the catalogue generator."""
from . import stats as S


def _cost(c):
    if isinstance(c, str):
        return c
    return ", ".join(f"{g} {n}" for g, n in c.items()) or "free"


def _basis(b):
    if isinstance(b, dict):
        return "; ".join(f"{k}: {v}" for k, v in b.items())
    return str(b)


def _t(rows, cols, heads=None):
    heads = heads or cols
    out = ["| " + " | ".join(heads) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join(str(r.get(c, "")).replace("|", "/") for c in cols) + " |")
    return "\n".join(out)


def markdown():
    o = ["## Proposed stat sheet (first pass)\n",
         "Basis: **M** derived from the model (question in brackets), **V** copied from the vanilla analogue in "
         "`basis_template`, **G** a guess to tune in play. Re-themed buildings not listed keep their Folktails "
         "analogue with Plank -> PandabornPole and TreatedPlank -> PandabornCuredPole.\n"]
    o.append("### Colonists\n")
    o.append(_t(S.COLONISTS, ["stat", "spec", "Inkpaw", "Ringtail", "Folktail", "basis"]))
    rb = S.REST_BONUS
    o.append(f"\nRested bonus: +{rb['bonus']:.0%} at {rb['full_at_hours']} working hours or fewer, falling linearly "
             f"to 0 at {rb['zero_at_hours']}; applies to {', '.join(rb['applies_to'])}; {rb['form']}.\n")
    o.append("### Plants\n")
    o.append(_t([dict(p, basis_s=_basis(p["basis"])) for p in S.PLANTS],
                ["id", "kind", "basis_template", "planter", "zone", "PlantTimeInHours", "GrowthTimeInDays", "harvest",
                 "RemovalTimeInHours", "DaysToDieDry", "Water", "ReproductionChance", "basis_s"],
                ["id", "kind", "basis", "planter", "zone", "plant h", "grow d", "harvest", "harvest h", "dry d",
                 "water", "spread", "basis of numbers"]))
    o.append("\n### Goods\n")
    o.append(_t([dict(g, eff=", ".join(f"{k} {v}" for k, v in g["ConsumptionEffects"].items()) or "-")
                 for g in S.GOODS], ["id", "GoodType", "Weight", "eff", "dish", "basis"],
                ["id", "type", "weight", "consumption effects", "dish wellbeing", "basis"]))
    o.append("\n### Recipes\n")
    o.append(_t([dict(r, i=_cost(r["Ingredients"]), p=_cost(r["Products"])) for r in S.RECIPES],
                ["id", "building", "CycleDurationInHours", "i", "p", "CyclesCapacity", "Fuel", "power", "basis"],
                ["id", "building", "cycle h", "ingredients", "products", "cycles capacity", "fuel", "power", "basis"]))
    o.append("\n### Needs (new)\n")
    o.append(_t(S.NEEDS, ["id", "group", "DailyDelta", "FavorableWellbeing", "ImportanceMultiplier", "Wastable",
                          "satisfied_by", "rhythm", "basis"],
                ["id", "group", "daily", "wellbeing", "importance", "wastable", "satisfied by", "rhythm", "basis"]))
    o.append("\nWellbeing ceiling by group: " + "; ".join(
        f"{k}: " + ", ".join(f"{g} {v}" for g, v in d.items()) + f" = {sum(d.values())}" for k, d in S.CEILING.items()))
    o.append("\n\n### Buildings\n")
    o.append(_t([dict(b, c=_cost(b["cost"]), r=", ".join(b["recipes"]) or "-") for b in S.BUILDINGS],
                ["id", "basis_template", "who", "c", "science", "workers", "r", "capacity", "basis"],
                ["id", "basis", "who", "cost", "science", "workers max (default)", "recipes", "capacity / notes",
                 "basis of numbers"]))
    o.append("\n### Events and oxen\n")
    for name, d in (("Great Flowering", S.FLOWERING), ("Lantern Festival", S.FESTIVAL), ("Wooden Ox", S.OX_STATS)):
        o.append(f"**{name}.** " + "; ".join(f"{k}: {v}" for k, v in d.items()) + "\n")
    return "\n".join(o)


def as_json():
    return dict(version="first pass, design revision 4", basis_legend=dict(M="model", V="vanilla analogue", G="guess"),
                rested_bonus=S.REST_BONUS, colonists=S.COLONISTS, plants=[{k: v for k, v in p.items() if k != "model"}
                                                                         for p in S.PLANTS],
                goods=S.GOODS, recipes=[{k: v for k, v in r.items() if k not in ("ratio", "cycle_h")}
                                        for r in S.RECIPES],
                needs=S.NEEDS, ceiling=S.CEILING, buildings=S.BUILDINGS,
                events=dict(flowering=S.FLOWERING, festival=S.FESTIVAL), wooden_ox=S.OX_STATS,
                retheme_rule=dict(Plank="PandabornPole", TreatedPlank="PandabornCuredPole",
                                  note="science and workers as the Folktails analogue unless listed"))
