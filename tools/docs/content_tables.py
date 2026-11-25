#!/usr/bin/env python3
"""Writes the generated half of docs/CONTENT.md from the catalogue.

    python -I tools/docs/content_tables.py            # rewrite the block between the markers in docs/CONTENT.md
    python -I tools/docs/content_tables.py --check    # exit 1 if docs/CONTENT.md is out of date (writes nothing)
    python -I tools/docs/content_tables.py --stdout   # print the block, touch nothing

Reads only: catalogue/*.toml, catalogue/text/*.json, src/code/modules.txt, art/models/<Id>/model.json,
art/plants/<Id>/model.json, the icon files under mod/PandabornFactions/Sprites/Pandaborn and (for a basis's toolbar
group, vanilla name, cost and science, and a plant's planter) the pinned vanilla dump
E:\\PandabornDev\\reference\\Blueprints with ..\\Localizations\\enUS.csv beside it (--vanilla; without the dump those
cells say "as basis", so always run it with the dump before committing). Writes only docs/CONTENT.md, and only
between the two markers. Output is deterministic: no dates, no absolute paths.

Works on Python 3.11+ (tomllib) and on the art venv's 3.10 (the tomli that pip vendors).
"""
import argparse
import csv
import json
import os
import re
import sys

try:
    import tomllib as _toml
except ImportError:  # the E: venv is Python 3.10
    from pip._vendor import tomli as _toml

BEGIN = "<!-- generated:begin (tools/docs/content_tables.py; do not edit by hand) -->"
END = "<!-- generated:end -->"
REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
MOD = os.path.join(REPO, "mod", "PandabornFactions")


def load_toml(name):
    with open(os.path.join(REPO, "catalogue", name + ".toml"), "rb") as f:
        return _toml.loads(f.read().decode("utf-8"))


def load_text(name):
    p = os.path.join(REPO, "catalogue", "text", name + ".json")
    if not os.path.isfile(p):
        return {}
    with open(p, encoding="utf-8") as f:
        return json.load(f).get("items", {})


def words(ident):
    """PandabornNightForagersPost -> Night Foragers Post (only when no text entry names the thing)."""
    s = ident[len("Pandaborn"):] if ident.startswith("Pandaborn") else ident
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Za-z])(?=[0-9])", " ", s)


def cell(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "|".join(["---"] * len(head)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(cell(c) for c in r) + " |")
    return out


def goods_list(d):
    return ", ".join("%s %s" % (n, g) for g, n in d.items()) if d else "nothing"


class Vanilla:
    """The pinned vanilla dump, indexed by blueprint file name. Optional."""

    def __init__(self, root):
        self.files = {}
        self.ok = bool(root) and os.path.isdir(root)
        if not self.ok:
            return
        for sub in ("Buildings", "NaturalResources"):
            for d, _, names in os.walk(os.path.join(root, sub)):
                for n in names:
                    if n.endswith(".blueprint.json"):
                        self.files.setdefault(n[:-len(".blueprint.json")], os.path.join(d, n))
        self._cache = {}
        self.loc = {}
        csv_path = os.path.join(os.path.dirname(os.path.normpath(root)), "Localizations", "enUS.csv")
        if os.path.isfile(csv_path):
            with open(csv_path, encoding="utf-8-sig", newline="") as f:
                for row in csv.reader(f):
                    if len(row) >= 2:
                        self.loc[row[0]] = row[1]

    def name(self, template):
        b = self.get(template)
        key = (b or {}).get("LabeledEntitySpec", {}).get("DisplayNameLocKey") if b else None
        return self.loc.get(key) if key else None

    def cost(self, template):
        b = self.get(template)
        spec = (b or {}).get("BuildingSpec") if b else None
        if spec is None:
            return None, None
        return {c["Id"]: c["Amount"] for c in spec.get("BuildingCost", [])}, spec.get("ScienceCost")

    def get(self, template):
        if not self.ok or template not in self.files:
            return None
        if template not in self._cache:
            with open(self.files[template], encoding="utf-8-sig") as f:
                self._cache[template] = json.load(f)
        return self._cache[template]

    def tool_group(self, template):
        b = self.get(template)
        return (b or {}).get("PlaceableBlockObjectSpec", {}).get("ToolGroupId") if b else None

    def planter(self, template):
        b = self.get(template)
        return (b or {}).get("PlantableSpec", {}).get("ResourceGroup") if b else None


def building_sections():
    """buildings.toml groups its lines under '# ---- <name>' comment rules: id -> section name."""
    sec, out = "Other", {}
    with open(os.path.join(REPO, "catalogue", "buildings.toml"), encoding="utf-8") as f:
        for line in f:
            m = re.match(r"#\s*-{5,}\s*(.+?)\s*$", line)
            if m:
                sec = re.sub(r"\s*\(.*\)\s*$", "", m.group(1)).strip()
                sec = sec[:1].upper() + sec[1:]
                continue
            m = re.match(r"([A-Za-z0-9_]+)\s*=\s*\{", line)
            if m:
                out[m.group(1)] = sec
    return out


def shipped_modules():
    out = []
    p = os.path.join(REPO, "src", "code", "modules.txt")
    if os.path.isfile(p):
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    out.append(line.split()[0])
    return out


def has_sprite(rel):
    return os.path.isfile(os.path.join(MOD, rel.replace("/", os.sep) + ".png"))


def build(vanilla_root):
    rules = load_toml("rules")
    switches = rules.get("modules", {})
    shipped = shipped_modules()
    poles_mode = rules.get("poles", {}).get("mode", "plank")
    van = Vanilla(vanilla_root)

    def waits(item):
        """waits_for names one module or several (all must be on)."""
        m = item.get("waits_for")
        return [] if not m else ([m] if isinstance(m, str) else list(m))

    def module_on(m):
        return bool(switches.get(m)) and m in shipped

    def gate(item):
        """([], True) when not gated; (['Water'], True) gated and visible; (['X'], False) hidden."""
        ms = waits(item)
        return ms, all(module_on(m) for m in ms)

    def gate_cell(item):
        ms, on = gate(item)
        if not ms:
            return ""
        return ", ".join(ms) if on else "**%s (hidden)**" % ", ".join(
            m if module_on(m) else m + " off" for m in ms)

    buildings = load_toml("buildings").get("buildings", {})
    stats = load_toml("building_stats").get("stats", {})
    archetypes = load_toml("archetypes").get("archetypes", {})
    goods = load_toml("goods")
    needs = load_toml("needs")
    recipes = load_toml("recipes").get("recipes", {})
    plants = load_toml("plants")
    faction = load_toml("faction")
    t_build, t_goods, t_needs, t_plants = (load_text(n) for n in ("buildings", "goods", "needs", "plants"))

    def by_id(items):
        return {v.get("id"): (k, v) for k, v in items.items() if isinstance(v, dict) and v.get("id")}

    tb, tg, tn, tp = by_id(t_build), by_id(t_goods), by_id(t_needs), by_id(t_plants)

    def good_name(gid):
        if gid in tg:
            return tg[gid][1].get("plural") or tg[gid][0]
        if poles_mode == "rename" and gid in rules.get("poles", {}).get("rename", {}):
            return rules["poles"]["rename"][gid]
        return words(gid)

    def building_name(bid):
        b = buildings.get(bid, {})
        if "vanilla" in b:
            return words(bid) + " (dev)"
        key = b.get("text", bid)
        if key in tb and tb[key][1].get("name"):
            return tb[key][1]["name"]
        # no name of our own: the vanilla loc key is kept, so the player reads the vanilla name
        vanilla_name = van.name(basis_of(bid, b) or bid) if van.ok else None
        if vanilla_name:
            return vanilla_name
        return tb[key][0] if key in tb else words(bid)

    sections = building_sections()
    lines = []

    # ---------------------------------------------------------------- modules
    lines += ["### Code modules and what they hide", "",
              "A catalogue item with `waits_for = \"<Module>\"` is generated only when that module ships "
              "(`src/code/modules.txt`) and its switch in `catalogue/rules.toml [modules]` is on. Hidden items keep "
              "their locked ids. That is the build's choice. A player can also switch a shipped module off for "
              "themselves with a text file `PandabornFactions.txt` in the game's user data folder (the folder that "
              "holds Saves and Mods), holding lines such as `off: Water, Festival`: the module is then not loaded and "
              "its items behave as their vanilla shells (nothing is generated for this).", ""]
    waiting = {}
    for kind, items in (("building", buildings), ("good", goods.get("goods", {})), ("need", needs.get("needs", {})),
                        ("recipe", recipes), ("plant", plants.get("plants", {})),
                        ("character", faction.get("characters", {}))):
        for iid, it in items.items():
            for m in (waits(it) if isinstance(it, dict) else []):
                waiting.setdefault(m, {}).setdefault(kind, []).append(iid)
    rows = []
    for m in sorted(set(list(switches) + shipped + list(waiting))):
        on = module_on(m)
        w = waiting.get(m, {})
        what = "; ".join("%d %s%s" % (len(v), k, "" if len(v) == 1 else "s") for k, v in w.items()) or "nothing"
        rows.append([m, "yes" if m in shipped else "**no**", "on" if switches.get(m) else "**off**",
                     "visible" if on else "**hidden**", what])
    lines += table(["Module", "In `modules.txt`", "Switch", "Its items are", "Items that wait for it"], rows) + [""]

    # ---------------------------------------------------------------- buildings
    def basis_of(bid, b):
        if "vanilla" in b:
            return None
        if "basis" in b:
            return b["basis"]
        if "archetype" in b and b["archetype"] in archetypes:
            return archetypes[b["archetype"]].get("basis")
        if "model" in b:
            p = os.path.join(REPO, "art", "models", b["model"], "model.json")
            if os.path.isfile(p):
                with open(p, encoding="utf-8") as f:
                    s = json.load(f).get("standIn")
                if s:
                    return s
        return bid + ".Folktails"

    def model_cell(bid, b):
        if "vanilla" in b:
            return "vanilla dev building, unchanged"
        if "model" in b:
            ok = os.path.isfile(os.path.join(REPO, "art", "models", b["model"], "model.json"))
            return "own: `art/models/%s`%s" % (b["model"], "" if ok else " **(model.json missing)**")
        if bid.startswith("Pandaborn"):
            kit = bid[len("Pandaborn"):]
            extra = (" (a kit model `art/models/%s` exists, not adopted)" % kit
                     if os.path.isfile(os.path.join(REPO, "art", "models", kit, "model.json")) else "")
            return "**stand-in**: the basis's vanilla model" + extra
        return "vanilla, re-themed"

    def icon_cell(bid, b):
        if "vanilla" in b:
            return "vanilla"
        if "icon" in b:
            return "own" if has_sprite(b["icon"]) else "**missing: %s**" % b["icon"]
        if bid.startswith("Pandaborn"):
            return "own" if has_sprite("Sprites/Pandaborn/Buildings/%sIcon" % bid) else "**basis's vanilla icon**"
        return "vanilla"

    def group_cell(bid, b, basis):
        if b.get("tool_group"):
            return b["tool_group"]
        if basis and van.ok:
            return van.tool_group(basis) or "?"
        return "as basis"

    order, per = [], {}
    for bid, b in buildings.items():
        s = sections.get(bid, "Other")
        if s not in per:
            per[s] = []
            order.append(s)
        per[s].append((bid, b))
    n_all = len(buildings)
    n_hidden = sum(1 for b in buildings.values() if not gate(b)[1])
    n_dev = sum(1 for b in buildings.values() if "vanilla" in b)
    n_own = sum(1 for bid in buildings if bid.startswith("Pandaborn"))
    n_model = sum(1 for b in buildings.values() if "model" in b)
    n_standin = sum(1 for bid, b in buildings.items()
                    if bid.startswith("Pandaborn") and "model" not in b and "vanilla" not in b)
    lines += ["### Buildings", "",
              "%d entries in `catalogue/buildings.toml`: %d re-themed vanilla buildings, %d of our own "
              "(`Pandaborn…`: %d on their own model, %d on a vanilla stand-in model) and %d vanilla dev buildings. "
              "%d are hidden today (their module is off or not shipped); %d are generated." % (
                  n_all, n_all - n_own - n_dev, n_own, n_model, n_standin, n_dev, n_hidden, n_all - n_hidden), "",
              "*Basis* is the vanilla blueprint the generator copies (template name; `—` for our own id on the same "
              "vanilla name). *Toolbar* is the bottom-bar group. *Model*: `own` = adopted from the building kit; "
              "`vanilla, re-themed` = the vanilla model in the Inkpaws' materials; **stand-in** = one of our own "
              "buildings still on a vanilla model. *Waits for* names the code module; bold = hidden today. "
              "*Icon*: `own` = a sprite under `mod/PandabornFactions/Sprites/Pandaborn/Buildings`.", ""]
    for s in order:
        lines += ["#### " + s, ""]
        rows = []
        for bid, b in per[s]:
            basis = basis_of(bid, b)
            st = stats.get(bid, {})
            cost = b.get("cost", st.get("cost"))
            sci = b.get("science", st.get("science"))
            if van.ok and basis and (cost is None or sci is None):
                v_cost, v_sci = van.cost(basis)
                cost = v_cost if cost is None else cost
                sci = v_sci if sci is None else sci
            for k, v in (b.get("module_set") or {}).items():   # e.g. Tradition decorations: science 0 with Festival on
                if "BuildingSpec.ScienceCost" in v and module_on(k):
                    sci = v["BuildingSpec.ScienceCost"]
            cost_s = "as basis" if cost is None else (goods_list({good_name(g): n for g, n in cost.items()})
                                                      if cost else "free")
            rows.append([building_name(bid), "`%s`" % bid,
                         "—" if basis is None else ("re-theme" if basis == bid + ".Folktails" else "`%s`" % basis),
                         group_cell(bid, b, basis), model_cell(bid, b), gate_cell(b), icon_cell(bid, b),
                         cost_s, "as basis" if sci is None else sci,
                         ", ".join("`%s`" % r for r in b.get("recipes", []))])
        lines += table(["Building", "Id", "Basis", "Toolbar", "Model", "Waits for", "Icon", "Cost", "Science",
                        "Recipes"], rows) + [""]

    # ---------------------------------------------------------------- goods
    made, used = {}, {}
    for rid, r in recipes.items():
        for g in r.get("products", {}):
            made.setdefault(g, []).append("recipe `%s`" % rid)
        for g in list(r.get("ingredients", {})) + ([r["fuel"]] if r.get("fuel") else []):
            used.setdefault(g, []).append("recipe `%s`" % rid)
    for pid, p in plants.get("plants", {}).items():
        for k in ("cut_yield", "gather_yield"):
            for g in p.get(k, {}):
                made.setdefault(g, []).append("plant `%s`" % pid)
    for bid, b in buildings.items():
        st = stats.get(bid, {})
        for g in (b.get("cost") or st.get("cost") or {}):
            used.setdefault(g, []).append("cost")
        for spec in (b.get("add") or {}).values():
            for cg in (spec.get("ConsumedGoods") or []) if isinstance(spec, dict) else []:
                used.setdefault(cg.get("GoodId"), []).append("`%s`" % bid)
        for k, v in (b.get("set") or {}).items():
            if k.endswith("ConsumedGoods") or k.endswith("RequiredGoods"):
                for cg in v:
                    used.setdefault(cg.get("GoodId") or cg.get("Id"), []).append("`%s`" % bid)
    fest = (faction.get("characters", {}).get("adult", {}).get("module_specs", {}).get("Festival", {})
            .get("PandabornFestivalSpec", {}))
    for g in [fest.get("LanternGoodId"), fest.get("FireworksGoodId")] + list(fest.get("Dishes", [])):
        if g:
            used.setdefault(g, []).append("Lantern Festival")

    def uniq(xs):
        seen, out = set(), []
        for x in xs:
            if x == "cost":
                x = "building costs"
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    rows = []
    for gid, g in goods.get("goods", {}).items():
        if g.get("when_poles") and g["when_poles"] != poles_mode:
            state = "not generated (poles mode is `%s`)" % poles_mode
        else:
            state = gate_cell(g)
        eaten = ", ".join("%s %s" % (n, v) for n, v in g.get("consumption", {}).items()) or "not eaten"
        icon = "own" if (has_sprite("Sprites/Pandaborn/Goods/%sIcon" % gid)
                         or has_sprite("Sprites/Pandaborn/Goods/%ssIcon" % gid)) else "**none**"
        skipped = state.startswith("not generated")
        rows.append([good_name(gid), "`%s`" % gid, "`%s`" % g.get("basis", ""), eaten,
                     "—" if skipped else "; ".join(uniq(made.get(gid, []))) or "**nothing**",
                     "—" if skipped else "; ".join(uniq(used.get(gid, []))) or (
                         "eaten" if g.get("consumption") else "**nothing**"),
                     state, icon])
    lines += ["### Goods", "",
              "%d goods of our own in `catalogue/goods.toml`. Poles mode is `%s`%s. Vanilla goods kept beyond the "
              "Common collection: %s." % (
                  len(goods.get("goods", {})), poles_mode,
                  " (Poles and Cured poles are the vanilla `Plank` and `TreatedPlank`, renamed and re-iconed for "
                  "Inkpaws only)" if poles_mode == "rename" else "",
                  ", ".join("`%s`" % v for v in goods.get("collection", {}).get("vanilla", []))), ""]
    lines += table(["Good", "Id", "Basis", "Eating it gives", "Made by", "Used by", "Waits for", "Icon"], rows) + [""]

    # ---------------------------------------------------------------- needs
    met = {}
    for gid, g in goods.get("goods", {}).items():
        for n in g.get("consumption", {}):
            met.setdefault(n, []).append("eating %s" % good_name(gid).lower())
    for bid, b in buildings.items():
        targets = list((b.get("effects") or {}).keys()) + list((b.get("needs_map") or {}).values())
        for spec in (b.get("add") or {}).values():
            if isinstance(spec, dict):
                targets += [e.get("NeedId") for e in spec.get("Effects", []) if isinstance(e, dict)]
        for n in targets:
            if n:
                met.setdefault(n, []).append(building_name(bid))
    for k in ("FestiveNeedId", "GrandNeedId"):
        if fest.get(k):
            met.setdefault(fest[k], []).append("a Lantern Festival" if k == "FestiveNeedId" else "a Grand Festival")

    def need_name(nid, n):
        src = n.get("name_from", "own")
        if src.startswith("good:"):
            return good_name(src[5:])
        if src.startswith("building:"):
            return building_name(src[9:])
        if nid in tn:
            return tn[nid][1].get("name") or tn[nid][0]
        return words(nid)

    rows = []
    for nid, n in needs.get("needs", {}).items():
        rows.append([need_name(nid, n), "`%s`" % nid, n.get("group", "as `%s`" % n.get("basis", "")),
                     n.get("daily_delta", "as basis"), n.get("favorable_wellbeing", "as basis"),
                     "; ".join(uniq(met.get(nid, []))) or "**nothing**", gate_cell(n)])
    lines += ["### Needs", "",
              "%d needs of our own in `catalogue/needs.toml`, all in the collection `%s`. Vanilla needs kept beyond "
              "Common: %s. *Per day* is the daily change; *Wellbeing* the points when satisfied." % (
                  len(needs.get("needs", {})), needs.get("collection", {}).get("id", ""),
                  ", ".join("`%s`" % v for v in needs.get("collection", {}).get("vanilla", []))), ""]
    lines += table(["Need", "Id", "Group", "Per day", "Wellbeing", "Met by", "Waits for"], rows) + [""]

    # ---------------------------------------------------------------- recipes
    at = {}
    for bid, b in buildings.items():
        for r in b.get("recipes", []):
            at.setdefault(r, []).append(building_name(bid))
    rows = []
    for rid, r in recipes.items():
        rows.append(["`%s`" % rid, goods_list({good_name(g): n for g, n in r.get("ingredients", {}).items()}),
                     goods_list({good_name(g): n for g, n in r.get("products", {}).items()}),
                     r.get("cycle_hours", ""), good_name(r["fuel"]) if r.get("fuel") else "",
                     ", ".join(at.get(rid, [])) or "**no building**", gate_cell(r)])
    lines += ["### Recipes", "",
              "%d recipes in `catalogue/recipes.toml`. Workshop stores are sized by `rules.toml [shelves]` "
              "(`workshop_hours = %s`), not by the recipe's own capacity." % (
                  len(recipes), rules.get("shelves", {}).get("workshop_hours", "?")), ""]
    lines += table(["Recipe", "Ingredients", "Products", "Hours", "Fuel", "Made at", "Waits for"], rows) + [""]

    # ---------------------------------------------------------------- plants
    rows = []
    for pid, p in plants.get("plants", {}).items():
        planter = p.get("planter") or (van.planter(p.get("basis", "")) if van.ok else None) or "as basis"
        if "waits_for" in p and "plant_hours" not in p and "planter" not in p:
            planter = "nobody (appears in a Flowering)"
        name = (tp[pid][1].get("name") or tp[pid][0]) if pid in tp else words(pid)
        parts = []
        if "wet_days" in p:
            parts.append("dry ground only: dies after %g days on moist soil" % p["wet_days"])
        if "dry_days" in p:
            parts.append("dies after %g dry days" % p["dry_days"])
        if p.get("flood_min") or p.get("flood_max"):
            parts.append("needs standing water (`flood_min` %g, `flood_max` %g), dies after %g days outside it" % (
                p.get("flood_min", 0), p.get("flood_max", 0), p.get("flood_days", 0)))
        elif "flood_days" in p:
            parts.append("dies after %g days under water" % p["flood_days"])
        water = "; ".join(parts) or "as basis"
        ok = os.path.isfile(os.path.join(REPO, "art", "plants", p.get("model", ""), "model.json")) if p.get("model") else False
        rows.append([name, "`%s`" % pid, "`%s`" % p.get("basis", ""), planter, p.get("growth_days", "as basis"),
                     "; ".join(x for x in (
                         "cut: " + goods_list({good_name(g): n for g, n in p["cut_yield"].items()}) if p.get("cut_yield") else "",
                         "gathered every %g days: %s" % (p.get("gather_days", 0), goods_list(
                             {good_name(g): n for g, n in p["gather_yield"].items()})) if p.get("gather_yield") else "") if x),
                     water, ("own: `art/plants/%s`" % p["model"]) if ok else "**stand-in: the basis's model**",
                     gate_cell(p)])
    lines += ["### Plants", "",
              "%d plants in `catalogue/plants.toml`, collection `%s`. Vanilla plants kept beyond Common: %s." % (
                  len(plants.get("plants", {})), plants.get("collection", {}).get("id", ""),
                  ", ".join("`%s`" % v for v in plants.get("collection", {}).get("vanilla", []))), ""]
    lines += table(["Plant", "Id", "Basis", "Planted by", "Grows (days)", "Yield", "Water rule", "Model", "Waits for"],
                   rows) + [""]

    # ---------------------------------------------------------------- characters
    rows = []
    for cid, c in faction.get("characters", {}).items():
        model = (c.get("models") or {}).get("Model_Preserved", "as basis")
        rows.append([cid, "`%s`" % c.get("template", ""), "`%s`" % c.get("basis", ""), "`%s`" % model,
                     "yes" if c.get("in_collection", True) else "no (made by code)", gate_cell(c)])
    lines += ["### Characters", ""]
    lines += table(["Character", "Template", "Basis", "Body mesh", "In `Characters.Inkpaws`", "Waits for"], rows) + [""]
    return "\n".join(lines).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if docs/CONTENT.md is out of date")
    ap.add_argument("--stdout", action="store_true", help="print the generated block, write nothing")
    ap.add_argument("--vanilla", default=r"E:\PandabornDev\reference\Blueprints", help="the pinned vanilla dump")
    ap.add_argument("--doc", default=os.path.join(REPO, "docs", "CONTENT.md"))
    a = ap.parse_args()
    block = build(a.vanilla)
    if a.stdout:
        sys.stdout.buffer.write(block.encode("utf-8"))
        return 0
    with open(a.doc, encoding="utf-8", newline="") as f:
        doc = f.read()
    nl = "\r\n" if "\r\n" in doc else "\n"
    doc_n = doc.replace("\r\n", "\n")
    if BEGIN not in doc_n or END not in doc_n:
        sys.stderr.write("%s has no generated block markers:\n  %s\n  %s\n" % (a.doc, BEGIN, END))
        return 2
    head, rest = doc_n.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    new = head + BEGIN + "\n\n" + block + "\n" + END + tail
    if new == doc_n:
        print("docs/CONTENT.md is up to date")
        return 0
    if a.check:
        print("docs/CONTENT.md is out of date: run tools/docs/content_tables.py")
        return 1
    with open(a.doc, "w", encoding="utf-8", newline="") as f:
        f.write(new.replace("\n", nl))
    print("docs/CONTENT.md rewritten")
    return 0


if __name__ == "__main__":
    sys.exit(main())
