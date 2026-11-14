"""Catalogue -> mod data. Pure: reads the catalogue and the vanilla dump, returns every output file in memory.
Writing, diffing and the lock live in cli.py.

Every output blueprint is "a vanilla basis + transforms" or built from catalogue fields alone; each carries its
provenance (vanilla source path and its sha256, catalogue item). Nothing is guessed: an unknown basis, a reference to a
template the faction does not have, a loc key that would overwrite vanilla text, a duplicate id all raise GenError.
"""
import copy
import os
import re

from . import content, models
from .util import REPO, GenError, dumps, sha256_bytes

LOC_COMMENT_MAX = 400
MARKER_RE = re.compile(r"\[(sun|moon)\]")


class Output:
    __slots__ = ("path", "data", "source", "source_sha", "item", "kind")

    def __init__(self, path, data, source, source_sha, item, kind):
        self.path, self.data, self.source, self.source_sha, self.item, self.kind = path, data, source, source_sha, item, kind


class Generator:
    def __init__(self, catalogue, vanilla, mod_src=None):
        self.cat = catalogue
        self.v = vanilla
        self.mod_src = mod_src or os.path.join(REPO, "mod", "PandabornFactions")
        self.good_plural = {}   # generated good id -> plural name loc key
        self.good_icon = {}
        self.building_name_key = {}   # building id -> display name loc key
        self.generated_collections = {"good": set(), "need": set()}
        self.model_files = {}     # mod rel path -> built mesh (E:\PandabornDev\build\models), copied by assemble
        self.adopted_models = {}  # model id -> {item, modelJson, standIn}
        self.mesh_dir = None
        self.code_waits = {}      # code module -> buildings that are vanilla-behaving stand-ins until it ships
        self.rules = catalogue["rules"]
        self.suffix = self.rules.get("names", {}).get("template_suffix", ".Inkpaws")
        self.source_faction = self.rules.get("names", {}).get("source_faction", "Folktails")
        self.faction_id = catalogue["faction"]["faction"]["id"]
        self.outputs = {}      # rel path (with .blueprint.json) -> Output
        self.loc = {}          # fragment file name -> {key: (text, comment, item)}
        self.ids = {}          # kind -> {id: item}
        self.modifiers = []    # (original path, modifier path)
        self.collections = {}  # collection id -> [blueprint paths]
        self.notes = []        # (item, note) for the report: stand-ins, retire plans, needs_code
        self.template_map = {}  # vanilla template name -> our template name (for cross references)
        self.substitute = dict(self.rules.get("costs", {}).get("substitute") or {})
        poles = self.rules.get("poles", {})
        self.pole_mode = poles.get("mode", "plank")
        if self.pole_mode not in ("plank", "rename", "good"):
            raise GenError("catalogue/rules.toml [poles] mode must be plank, rename or good, not %r" % self.pole_mode)
        if self.pole_mode == "good":
            self.substitute.setdefault("Plank", poles.get("good", "PandabornPole"))
            self.substitute.setdefault("TreatedPlank", poles.get("cured_good", "PandabornCuredPole"))

    def sub_goods(self, value):
        """Applies [costs].substitute to a good id, a list of {Id, Amount} or a {good: n} table."""
        if isinstance(value, str):
            return self.substitute.get(value, value)
        if isinstance(value, list):
            return [dict(x, Id=self.substitute.get(x["Id"], x["Id"])) if isinstance(x, dict) and "Id" in x else x
                    for x in value]
        return value

    # ------------------------------------------------------------------------------------------------- plumbing
    def add_id(self, kind, value, item):
        bucket = self.ids.setdefault(kind, {})
        if value in bucket and bucket[value] != item:
            raise GenError("%s id %s is produced twice: by %s and by %s" % (kind, value, bucket[value], item))
        bucket[value] = item

    def emit(self, path, data, item, kind, source_key=None):
        if not path.endswith(".blueprint.json"):
            path += ".blueprint.json"
        low = path.lower()
        for other in self.outputs:
            if other.lower() == low:
                raise GenError("%s and %s both write %s" % (self.outputs[other].item, item, path))
        src = self.v.rel(source_key) if source_key else None
        sha = self.v.sha(source_key) if source_key else None
        self.outputs[path] = Output(path, data, src, sha, item, kind)
        return path[:-len(".json")]   # as collections and modifiers spell it

    def add_loc(self, fragment, key, text, comment, item):
        if key in self.v.loc:
            raise GenError("%s: loc key %s is a vanilla key; writing it would change the text in every faction's games. "
                           "Use a Pandaborn key." % (item, key))
        if MARKER_RE.search(text or ""):
            raise GenError("%s: text for %s contains a [sun]/[moon] marker; decide its sprite tag in rules.toml first"
                           % (item, key))
        frag = self.loc.setdefault(fragment, {})
        for f, entries in self.loc.items():
            if key in entries and (f != fragment or entries[key][0] != text):
                raise GenError("loc key %s gets two texts (%s in %s, %s in %s)" % (key, entries[key][2], f, item, fragment))
        frag[key] = (text, (comment or "")[:LOC_COMMENT_MAX], item)

    def note(self, item, text):
        self.notes.append((item, text))

    def vanilla_template_key(self, basis, where):
        try:
            return self.v.key_of(basis)
        except GenError as e:
            raise GenError("%s: %s" % (where, e)) from None

    # ---------------------------------------------------------------------------------------------------- run
    def run(self):
        self.plan_buildings()
        self.gen_characters()
        self.gen_shaft_parts()
        self.gen_faction_keyed("Decals", "DecalSpec", self.cat["faction"].get("decals", {}))
        self.gen_faction_keyed("WorkerOutfits", "WorkerOutfitSpec", self.cat["faction"].get("outfits", {}))
        content.gen_goods(self)
        self.gen_buildings()
        content.gen_needs(self)
        content.gen_recipes(self)
        content.gen_plants(self)
        self.gen_poles()
        self.gen_collections()
        self.gen_faction()
        return self

    # ------------------------------------------------------------------------------------------- characters
    def gen_characters(self):
        chars = self.cat["faction"].get("characters") or {}
        coll = []
        for cid, c in chars.items():
            item = self.cat.where("faction", "characters." + cid)
            key = self.vanilla_template_key(c["basis"], item)
            data = self.v.copy(key)
            self.set_template(data, c["template"], c.get("aliases"), item)
            self.apply_models(data, c.get("models"), item)
            self.apply_set(data, c.get("set"), item)
            coll.append(self.emit(c["path"], data, item, "character", key))
        if coll:
            self.collections["Characters." + self.faction_id] = coll

    def gen_shaft_parts(self):
        s = self.cat["faction"].get("shaft_parts")
        if not s:
            return
        item = self.cat.where("faction", "shaft_parts")
        key = self.vanilla_template_key(s["basis"], item)
        data = self.v.copy(key)
        self.collections["ModularShaftParts." + self.faction_id] = [self.emit(s["path"], data, item, "shaft", key)]

    def gen_faction_keyed(self, folder, spec, conf):
        src = conf.get("copy_faction")
        if not src:
            return
        n = 0
        for key in sorted(self.v.paths):
            bp = self.v.get(key)
            if spec in bp and bp[spec].get("FactionId") == src:
                rel = self.v.rel(key)
                name = rel.rsplit("/", 1)[-1]
                if not name.endswith("." + src + ".blueprint"):
                    raise GenError("%s: %s is keyed to %s but not named *.%s; rename rule unclear" % (folder, rel, src, src))
                new_name = name[:-len("." + src + ".blueprint")] + "." + self.faction_id
                data = self.v.copy(key)
                data[spec]["FactionId"] = self.faction_id
                self.emit("%s/Pandaborn/%s" % (folder, new_name), data, self.cat.where("faction", folder.lower()),
                          folder.lower(), key)
                n += 1
        if not n:
            raise GenError("catalogue/faction.toml: no %s with FactionId %s in the vanilla dump" % (spec, src))

    # -------------------------------------------------------------------------------------------- buildings
    def building_items(self):
        return self.cat["buildings"].get("buildings") or {}

    def plan_buildings(self):
        """First pass: decide every building's basis and template name, so cross references can be remapped."""
        self.plan = {}
        # vanilla templates the faction keeps: everything in Common plus the vanilla collections it still lists
        self.available_vanilla = set()
        for cid in ["Common"] + list(self.cat["faction"]["faction"]["template_collections"]):
            for path in self.v.collection("TemplateCollectionSpec", cid):
                ts = self.v.get(self.v.key_of(path)).get("TemplateSpec")
                if ts:
                    self.available_vanilla.add(ts["TemplateName"])
        for bid, b in self.building_items().items():
            item = self.cat.where("buildings", "buildings." + bid)
            if b.get("vanilla"):
                key = self.vanilla_template_key(b["vanilla"], item)
                self.plan[bid] = {"vanilla": key, "item": item}
                continue
            basis = b.get("basis") or (bid + "." + self.source_faction)
            if b.get("model") and not b.get("basis"):
                # an adopted model brings its stand-in: the blueprint whose specs the model was made for
                basis = models.load_model("building", b["model"], item)[0]["standIn"]
            elif b.get("archetype"):
                arch = (self.cat["archetypes"].get("archetypes") or {}).get(b["archetype"])
                if arch is None:
                    raise GenError("%s: archetype %s is not defined in catalogue/archetypes.toml" % (item, b["archetype"]))
                basis = b.get("basis") or arch["basis"]
            key = self.vanilla_template_key(basis, item)
            template = b.get("template") or (bid + self.suffix)
            if not template.endswith(self.suffix):
                raise GenError("%s: template name %s must end with %s" % (item, template, self.suffix))
            vname = self.v.get(key).get("TemplateSpec", {}).get("TemplateName")
            if not vname:
                raise GenError("%s: basis %s has no TemplateSpec" % (item, basis))
            if vname in self.template_map:
                # two of ours on the same basis: references to the basis are ambiguous unless one is the plain re-theme
                prev = self.template_map[vname]
                if not b.get("basis"):
                    self.template_map[vname] = template
                elif prev is None or prev.split(".")[0] != vname.split(".")[0]:
                    self.template_map[vname] = None  # ambiguous; only an error if something refers to it
            else:
                self.template_map[vname] = template
            self.plan[bid] = {"key": key, "template": template, "item": item, "vname": vname}

    def merged_stats(self, bid, b, item):
        """Numbers from catalogue/building_stats.toml (the balance lane's file) joined to a building; a field set in
        both files is an error, so nobody wonders which one wins."""
        st = self.stats.get(bid)
        if not st:
            return b
        allowed = {"cost", "science", "workers", "default_workers", "capacity", "src"}
        unknown = set(st) - allowed
        if unknown:
            raise GenError("catalogue/building_stats.toml [stats.%s]: unknown field(s) %s" % (bid, ", ".join(sorted(unknown))))
        both = sorted(k for k in st if k != "src" and k in b)
        if both:
            raise GenError("%s: %s set both here and in catalogue/building_stats.toml [stats.%s]; keep one"
                           % (item, ", ".join(both), bid))
        merged = dict(b)
        merged.update({k: v for k, v in st.items() if k != "src"})
        return merged

    def gen_buildings(self):
        text = self.cat.text_by_id("buildings")
        coll = []
        self.stats = (self.cat["building_stats"].get("stats") or {})
        orphans = sorted(set(self.stats) - set(self.building_items()))
        if orphans:
            raise GenError("catalogue/building_stats.toml has numbers for buildings that buildings.toml does not "
                           "have: %s" % ", ".join(orphans))
        for bid, b in self.building_items().items():
            p = self.plan[bid]
            item = p["item"]
            if "vanilla" in p:
                coll.append(self.v.rel(p["vanilla"]))   # a vanilla blueprint listed as is (not ours: not locked)
                continue
            key = p["key"]
            data = self.v.copy(key)
            b = self.merged_stats(bid, b, item)
            if b.get("archetype"):
                b = self.with_archetype(b, data, item)
            if b.get("model"):
                models.apply_building_model(self, data, b["model"], item, self.mesh_dir)
            self.set_template(data, p["template"], b.get("aliases"), item)
            self.remap_template_refs(data, item)
            self.apply_building_text(data, bid, b, text, item)
            self.apply_costs(data, b, item)
            self.apply_workplace(data, b, item)
            if "recipes" in b:
                self.require(data, "ManufactorySpec", item, "recipes")["ProductionRecipeIds"] = list(b["recipes"])
            if "needs_map" in b:
                self.retarget_needs(data, b["needs_map"], item)
            if "effects" in b:
                spec = next((x for x in ("AttractionSpec", "ContinuousEffectBuildingSpec") if x in data), None)
                if spec is None:
                    raise GenError("%s: effects needs an AttractionSpec or ContinuousEffectBuildingSpec on the basis "
                                   "(pick an attraction or decoration basis or archetype)" % item)
                data[spec]["Effects"] = [{"NeedId": n, "PointsPerHour": float(v), "SatisfyToMaxValue": False}
                                         for n, v in b["effects"].items()]
            for spec, body in (b.get("add") or {}).items():
                if spec in data:
                    raise GenError("%s: add %s: the basis already has it" % (item, spec))
                data[spec] = body
            if "capacity" in b:
                self.apply_capacity(data, b["capacity"], item)
            pb = data.get("PlaceableBlockObjectSpec")
            if "tool_group" in b:
                self.require(data, "PlaceableBlockObjectSpec", item, "tool_group")["ToolGroupId"] = b["tool_group"]
            if "tool_order" in b:
                self.require(data, "PlaceableBlockObjectSpec", item, "tool_order")["ToolOrder"] = b["tool_order"]
            if b.get("retire"):
                if not pb:
                    raise GenError("%s: retire needs a PlaceableBlockObjectSpec" % item)
                pb["DevModeTool"] = True   # still loads (saved instances survive), hidden from the toolbar
            icon = b.get("icon") or (content.find_icon(self, "building", bid, None) if bid.startswith("Pandaborn") else None)
            if icon:
                self.require(data, "LabeledEntitySpec", item, "icon")["Icon"] = icon
            elif bid.startswith("Pandaborn"):
                self.note(item, "no icon Sprites/Pandaborn/Buildings/%sIcon; keeps the %s icon" % (bid, p["vname"]))
            if data.get("LabeledEntitySpec", {}).get("DisplayNameLocKey"):
                self.building_name_key[bid] = data["LabeledEntitySpec"]["DisplayNameLocKey"]
            self.apply_models(data, b.get("models"), item)
            self.apply_set(data, b.get("set"), item)
            self.apply_delete(data, b.get("delete"), item)
            category = self.v.rel(key).split("/")[1] if self.v.rel(key).startswith("Buildings/") else "Misc"
            path = b.get("path") or "Buildings/Pandaborn/%s/%s/%s" % (category, bid, p["template"])
            coll.append(self.emit(path, data, item, "building", key))
            if b.get("standin") and not b.get("model"):
                self.note(item, "stand-in on %s; replace with %s" % (p["vname"], b["standin"]))
            if b.get("needs_code") or b.get("waits_for"):
                if not (b.get("needs_code") and b.get("waits_for")):
                    raise GenError("%s: needs_code and waits_for (the code module) go together" % item)
                self.note(item, "needs code: " + b["needs_code"])
                self.code_waits.setdefault(b["waits_for"], []).append(
                    {"building": p["template"], "until_then": b["needs_code"]})
            if b.get("retire_when"):
                self.note(item, "temporary; retire when " + b["retire_when"])
        if coll:
            self.collections["Buildings." + self.faction_id] = coll

    def with_archetype(self, b, data, item):
        """An archetype (catalogue/archetypes.toml) is a named set of defaults on a vanilla basis that has the right
        specs: the building's own fields win; `requires` lists specs the (possibly overridden) basis must have."""
        arch = self.cat["archetypes"]["archetypes"][b["archetype"]]
        for spec in arch.get("requires") or []:
            if spec not in data:
                raise GenError("%s: archetype %s needs %s, which the basis lacks" % (item, b["archetype"], spec))
        merged = {k: v for k, v in arch.items() if k not in ("basis", "requires", "about", "fields")}
        for k, v in b.items():
            if isinstance(v, dict) and isinstance(merged.get(k), dict):
                merged[k] = dict(merged[k], **v)
            else:
                merged[k] = v
        return merged

    def set_template(self, data, name, aliases, item):
        ts = data.get("TemplateSpec")
        if ts is None:
            raise GenError("%s: basis has no TemplateSpec" % item)
        ts["TemplateName"] = name
        ts["BackwardCompatibleTemplateNames"] = list(aliases or [])   # never inherit vanilla aliases (they would clash)
        self.add_id("template", name, item)
        for a in aliases or []:
            self.add_id("template_alias", a, item)

    def remap_template_refs(self, data, item):
        """Fields that name other templates (TunnelSupportTemplateName, UnderstructureTemplateNames...) must point at
        our copies, or the building would look for a Folktails template the Inkpaws do not have."""
        def walk(obj, path):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if "TemplateName" in k and k != "TemplateName" and k != "BackwardCompatibleTemplateNames":
                        obj[k] = remap(v, path + "." + k)
                    else:
                        walk(v, path + "." + k)
            elif isinstance(obj, list):
                for x in obj:
                    walk(x, path)

        def remap(v, path):
            if isinstance(v, list):
                return [remap(x, path) for x in v]
            if not isinstance(v, str) or not v:
                return v
            if v in self.template_map:
                if self.template_map[v] is None:
                    raise GenError("%s: %s names %s, which two Inkpaws buildings use as their basis; set it explicitly "
                                   "with set = { ... }" % (item, path, v))
                return self.template_map[v]
            if v in self.available_vanilla:
                return v
            if v in self.v.templates or v in self.v.template_aliases:
                raise GenError("%s: %s names the vanilla template %s, which the Inkpaws do not have. Add it to "
                               "buildings.toml or override the field with set = { ... }" % (item, path, v))
            return v
        walk(data, "")

    def apply_building_text(self, data, bid, b, text, item):
        tid = b.get("text") or bid
        entry = text.get(tid)
        les = data.get("LabeledEntitySpec")
        if entry is None:
            if b.get("basis") and bid.startswith("Pandaborn"):
                raise GenError("%s: no entry with id %s in text/buildings.json; a building of our own needs its name"
                               % (item, tid))
            return  # re-themed with no text entry: vanilla keys
        if les is None:
            raise GenError("%s: has text but its basis has no LabeledEntitySpec" % item)
        stem = tid[len("Pandaborn"):] if tid.startswith("Pandaborn") else tid
        reuse = entry.get("reuse") or {}
        for field, spec_field, suffix in (("name", "DisplayNameLocKey", "DisplayName"),
                                          ("description", "DescriptionLocKey", "Description"),
                                          ("flavor", "FlavorDescriptionLocKey", "FlavorDescription")):
            if field in reuse:
                les[spec_field] = reuse[field]
                continue
            value = entry.get(field)
            if value is None:
                continue   # keep the vanilla key (already translated into every language)
            key = "Pandaborn.Building.%s.%s" % (stem, suffix)
            les[spec_field] = key
            comment = entry.get("translator_comment") or ("%s of the Inkpaws building %s" % (field, entry["_english"]))
            self.add_loc("Buildings", key, value, comment, item)

    def retarget_needs(self, data, mapping, item):
        """Every NeedId equal to a key of mapping becomes its value (a stand-in attraction or decoration that should
        satisfy one of our needs instead of the vanilla one). A mapping that matches nothing is an error."""
        hits = set()

        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == "NeedId" and v in mapping:
                        o[k] = mapping[v]
                        hits.add(v)
                    else:
                        walk(v)
            elif isinstance(o, list):
                for x in o:
                    walk(x)
        walk(data)
        missing = set(mapping) - hits
        if missing:
            raise GenError("%s: needs_map: the basis has no NeedId %s" % (item, ", ".join(sorted(missing))))

    def require(self, data, spec, item, field):
        if spec not in data:
            raise GenError("%s: field %s needs a %s on the basis, which has none" % (item, field, spec))
        return data[spec]

    def apply_costs(self, data, b, item):
        bs = data.get("BuildingSpec")
        if "cost" in b:
            bs = self.require(data, "BuildingSpec", item, "cost")
            bs["BuildingCost"] = [{"Id": g, "Amount": int(a)} for g, a in b["cost"].items()]
        if "science" in b:
            self.require(data, "BuildingSpec", item, "science")["ScienceCost"] = int(b["science"])
        if bs and self.substitute:
            bs["BuildingCost"] = self.sub_goods(bs.get("BuildingCost", []))

    def apply_workplace(self, data, b, item):
        if "workers" in b:
            w = self.require(data, "WorkplaceSpec", item, "workers")
            w["MaxWorkers"] = int(b["workers"])
            w["DefaultWorkers"] = int(b.get("default_workers", b["workers"]))
        if "worker_type" in b:
            self.require(data, "WorkplaceSpec", item, "worker_type")["DefaultWorkerType"] = b["worker_type"]
        if "disallow_other_workers" in b:
            self.require(data, "WorkplaceSpec", item, "disallow_other_workers")["DisallowOtherWorkerTypes"] = \
                bool(b["disallow_other_workers"])

    def apply_capacity(self, data, value, item):
        for spec, field in (("DwellingSpec", "MaxBeavers"), ("StockpileSpec", "MaxCapacity"),
                            ("AttractionSpec", "Capacity"), ("EnterableSpec", "CapacityFinished")):
            if spec in data:
                data[spec][field] = int(value)
                return
        raise GenError("%s: capacity given but the basis has no dwelling, stockpile or attraction spec" % item)

    def apply_models(self, data, models, item):
        for child, model in (models or {}).items():
            node = (data.get("Children") or {}).get(child)
            if not node or "TimbermeshSpec" not in node:
                raise GenError("%s: models: the basis has no child %s with a TimbermeshSpec (children: %s)"
                               % (item, child, ", ".join(data.get("Children") or {})))
            node["TimbermeshSpec"]["Model"] = model

    def apply_set(self, data, sets, item):
        for path, value in (sets or {}).items():
            parts = path.split(".")
            node = data
            for i, p in enumerate(parts[:-1]):
                if not isinstance(node, dict) or p not in node:
                    raise GenError("%s: set %s: %s does not exist on the basis" % (item, path, ".".join(parts[:i + 1])))
                node = node[p]
            if not isinstance(node, dict):
                raise GenError("%s: set %s: parent is not an object" % (item, path))
            node[parts[-1]] = copy.deepcopy(value)

    def apply_delete(self, data, keys, item):
        for path in keys or []:
            parts = path.split(".")
            node = data
            for p in parts[:-1]:
                node = node.get(p) if isinstance(node, dict) else None
            if not isinstance(node, dict) or parts[-1] not in node:
                raise GenError("%s: delete %s: not on the basis" % (item, path))
            del node[parts[-1]]

    # -------------------------------------------------------------------------------------------------- poles
    def gen_poles(self):
        """rules.toml [poles]: "plank" changes nothing; "good" needs the pole goods in goods.toml (costs and recipes
        are rewritten through [costs].substitute); "rename" turns the vanilla Plank / TreatedPlank into poles / cured
        poles for this faction only, through faction blueprint modifiers (name, plural, icon; the id stays)."""
        poles = self.rules["poles"]
        item = "catalogue/rules.toml [poles]"
        if self.pole_mode == "good":
            goods = self.cat["goods"].get("goods") or {}
            for gid in (poles.get("good", "PandabornPole"), poles.get("cured_good", "PandabornCuredPole")):
                if gid not in goods:
                    raise GenError("%s: mode is 'good' but goods.toml has no %s" % (item, gid))
            return
        if self.pole_mode != "rename":
            return
        text = self.cat.text_items("goods")
        for vanilla_id, english in (poles.get("rename") or {"Plank": "Poles", "TreatedPlank": "Cured poles"}).items():
            entry = text.get(english)
            if not entry:
                raise GenError("%s: text/goods.json has no entry %r" % (item, english))
            st = entry["id"][len("Pandaborn"):] if entry["id"].startswith("Pandaborn") else entry["id"]
            k1, k2 = "Pandaborn.Good.%s.DisplayName" % st, "Pandaborn.Good.%s.PluralDisplayName" % st
            self.add_loc("Goods", k1, entry["singular"], entry.get("translator_comment"), item)
            self.add_loc("Goods", k2, entry["plural"], entry.get("translator_comment"), item)
            spec = {"DisplayNameLocKey": k1, "PluralDisplayNameLocKey": k2}
            icon = content.find_icon(self, "good", entry["id"], None)
            if icon:
                spec["Icon"] = icon
            key = self.v.ids["GoodSpec"].get(vanilla_id)
            if key is None:
                raise GenError("%s: rename: %s is not a vanilla good" % (item, vanilla_id))
            self.add_modifier(key, "Good." + vanilla_id, {"GoodSpec": spec}, item)

    def add_modifier(self, original_key, name, data, item):
        path = self.emit("Modifiers/Pandaborn/%s.optional" % name, data, item, "modifier", original_key)
        self.modifiers.append((self.v.rel(original_key), path))

    # ---------------------------------------------------------------------------------------------- collections
    def gen_collections(self):
        for cid, items in self.collections.items():
            self.add_id("collection", cid, "generated")
            self.emit("TemplateCollections/Pandaborn/TemplateCollection.%s" % cid,
                      {"TemplateCollectionSpec": {"CollectionId": cid, "Blueprints": items}},
                      "generated: collection " + cid, "collection")

    # ------------------------------------------------------------------------------------------------- faction
    def gen_faction(self):
        f = self.cat["faction"]["faction"]
        item = self.cat.where("faction", "faction")
        sb = f["starting_building"]
        plan = self.plan.get(sb)
        if not plan or "template" not in plan:
            raise GenError("%s: starting_building %s is not a generated building in buildings.toml" % (item, sb))
        for cid in f["template_collections"]:
            if cid not in self.collections and cid not in self.v.collections["TemplateCollectionSpec"]:
                raise GenError("%s: template collection %s is neither generated nor vanilla" % (item, cid))
        for field, kind, spec in (("good_collections", "good", "GoodCollectionSpec"),
                                  ("need_collections", "need", "NeedCollectionSpec")):
            for cid in f[field]:
                if cid not in self.generated_collections[kind] and cid not in self.v.collections[spec]:
                    raise GenError("%s: %s %s is neither generated nor vanilla" % (item, field, cid))
        missing = [c for c in self.collections if c not in f["template_collections"]]
        if missing:
            raise GenError("%s: generated collections %s are not listed in template_collections" % (item, missing))
        fs = {
            "Id": f["id"], "Order": f["order"], "Avatar": f["avatar"], "ChildAvatar": f["child_avatar"],
            "BotAvatar": f["bot_avatar"], "ContaminatedAdultAvatar": f["contaminated_adult_avatar"],
            "ContaminatedChildAvatar": f["contaminated_child_avatar"], "Logo": f["logo"],
            "NewGameFullAvatar": f["new_game_full_avatar"], "Textures": list(f["textures"]),
            "ChildTextures": list(f["child_textures"]), "MaterialCollectionIds": list(f["material_collections"]),
            "TemplateCollectionIds": list(f["template_collections"]), "PathMaterial": f["path_material"],
            "BaseWoodMaterial": f["base_wood_material"], "NeedCollectionIds": list(f["need_collections"]),
            "GoodCollectionIds": list(f["good_collections"]),
            "BlueprintModifiers": [{"Original": o, "Modifier": m} for o, m in self.modifiers],
            "StartingBuildingId": plan["template"], "SoundId": f["sound_id"],
            "DisplayNameLocKey": f["display_name"], "DescriptionLocKey": f["description"],
            "GameOverMessageLocKey": f["game_over_message"], "GameOverFlavorLocKey": f["game_over_flavor"],
        }
        w = f["wonder"]
        data = {"FactionSpec": fs, "FactionWonderSpec": {
            "WonderCompletionImage": w["completion_image"], "WonderLaunchSound": w["launch_sound"],
            "WonderCompletionFlavorLocKey": w["completion_flavor"],
            "WonderCompletionMessageLocKey": w["completion_message"]}}
        self.add_id("faction", f["id"], item)
        self.emit("Factions/Pandaborn/Faction.%s" % f["id"], data, item, "faction")
        # faction texts from text/faction.json "core"
        core = (self.cat.text.get("faction") or {}).get("core") or {}
        wanted = {fs["DisplayNameLocKey"], fs["DescriptionLocKey"], fs["GameOverMessageLocKey"],
                  fs["GameOverFlavorLocKey"], w["completion_flavor"], w["completion_message"]}
        for e in core.values():
            if isinstance(e, dict) and e.get("key"):
                self.add_loc("Faction", e["key"], e["text"], e.get("translator_comment"), "catalogue/text/faction.json")
                wanted.discard(e["key"])
        if wanted:
            raise GenError("%s: no text in text/faction.json core for %s" % (item, ", ".join(sorted(wanted))))

    # ------------------------------------------------------------------------------------------------- results
    def outputs_by_template(self, name):
        for o in self.outputs.values():
            if (o.data.get("TemplateSpec") or {}).get("TemplateName") == name:
                return o.data
        return {}

    def files(self):
        """rel path -> bytes, for every generated file (blueprints and loc fragments)."""
        out = {p: dumps(o.data).encode("utf-8") for p, o in self.outputs.items()}
        for frag, entries in self.loc.items():
            out["Localizations/enUS_Pandaborn%s.csv" % frag] = loc_csv(entries).encode("utf-8")
        return out

    def provenance(self, files):
        prov = {}
        for p, o in sorted(self.outputs.items()):
            prov[p] = {"kind": o.kind, "item": o.item, "source": o.source, "sourceSha256": o.source_sha,
                       "sha256": sha256_bytes(files[p])}
        for frag, entries in sorted(self.loc.items()):
            p = "Localizations/enUS_Pandaborn%s.csv" % frag
            prov[p] = {"kind": "loc", "item": sorted({e[2] for e in entries.values()}), "source": None,
                       "sourceSha256": None, "sha256": sha256_bytes(files[p])}
        return prov


def loc_csv(entries):
    """ID,Text,Comment; every field quoted; LF; sorted by key; checked against the game's LocalizationCsvValidator
    rules (no empty line, no ', "' or '" ,' outside doubled quotes, no trailing space)."""
    lines = ["ID,Text,Comment"]
    for key in sorted(entries):
        text, comment, item = entries[key]
        if not text or text != text.strip():
            raise GenError("%s: text for %s is empty or has leading/trailing space" % (item, key))
        comment = (comment or "").strip()
        row = ",".join('"' + s.replace('"', '""') + '"' for s in (key, text, comment))
        stripped = row.replace('""', "")
        if ', "' in stripped or '" ,' in stripped:
            raise GenError("%s: text for %s produces ', \"' in the CSV, which the game rejects" % (item, key))
        if "\n\n" in row or "\r" in row:
            raise GenError("%s: text for %s has an empty line or CR, which the game rejects" % (item, key))
        lines.append(row)
    return "\n".join(lines) + "\n"
