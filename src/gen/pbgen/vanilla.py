"""Read-only index of the vanilla blueprint dump and vanilla localisation."""
import copy
import csv
import os

from .util import GenError, asset_key, load_json, read_bytes, sha256_bytes

# spec -> field that holds its global id
ID_SPECS = {
    "GoodSpec": "Id", "NeedSpec": "Id", "NeedGroupSpec": "Id", "RecipeSpec": "Id", "WorkerTypeSpec": "Id",
    "GoodGroupSpec": "Id", "ToolGroupSpec": "Id", "BonusTypeSpec": "Id", "FactionSpec": "Id",
    "BlockObjectToolGroupSpec": "Id", "TutorialSpec": "Id", "TutorialStageSpec": "Id",
}
COLLECTION_SPECS = ("TemplateCollectionSpec", "MaterialCollectionSpec", "NeedCollectionSpec", "GoodCollectionSpec")


class Vanilla:
    def __init__(self, blueprints_dir, localizations_dir=None):
        if not os.path.isdir(blueprints_dir):
            raise GenError("vanilla blueprint dump not found: " + blueprints_dir)
        self.dir = blueprints_dir
        self.paths = {}       # asset key -> (rel path with original case, without .json), abs path
        for dirpath, _, names in os.walk(blueprints_dir):
            for n in sorted(names):
                if n.endswith(".blueprint.json"):
                    ab = os.path.join(dirpath, n)
                    rel = os.path.relpath(ab, blueprints_dir).replace("\\", "/")
                    self.paths[asset_key(rel)] = (rel[:-len(".json")], ab)
        self._cache = {}
        self._raw = {}
        self.templates = {}   # template name -> asset key
        self.template_aliases = {}
        self.ids = {s: {} for s in ID_SPECS}  # spec -> id -> key
        self.collections = {s: {} for s in COLLECTION_SPECS}  # spec -> collection id -> [key]
        for key in sorted(self.paths):
            bp = self.get(key)
            ts = bp.get("TemplateSpec")
            if ts:
                self.templates[ts["TemplateName"]] = key
                for alias in ts.get("BackwardCompatibleTemplateNames") or []:
                    self.template_aliases[alias] = key
            for spec, field in ID_SPECS.items():
                if spec in bp:
                    self.ids[spec][bp[spec].get(field)] = key
            for spec in COLLECTION_SPECS:
                if spec in bp:
                    self.collections[spec].setdefault(bp[spec]["CollectionId"], []).append(key)
        self.loc = {}
        if localizations_dir:
            p = os.path.join(localizations_dir, "enUS.csv")
            if os.path.isfile(p):
                with open(p, encoding="utf-8-sig", newline="") as f:
                    for row in csv.reader(f):
                        if row:
                            self.loc[row[0]] = row[1] if len(row) > 1 else ""

    def key_of(self, path_or_name):
        """Accepts a blueprint path (with or without .blueprint/.json) or a template name."""
        if path_or_name in self.templates:
            return self.templates[path_or_name]
        p = path_or_name
        if p.endswith(".json"):
            p = p[:-5]
        if not p.endswith(".blueprint"):
            p += ".blueprint"
        k = asset_key(p + ".json")
        if k not in self.paths:
            raise GenError("vanilla blueprint or template not found: " + path_or_name)
        return k

    def rel(self, key):
        """Blueprint path as collections and modifiers spell it (original case, ends .blueprint)."""
        return self.paths[key][0]

    def raw(self, key):
        if key not in self._raw:
            self._raw[key] = read_bytes(self.paths[key][1])
        return self._raw[key]

    def sha(self, key):
        return sha256_bytes(self.raw(key))

    def get(self, key):
        if key not in self._cache:
            self._cache[key] = load_json(self.paths[key][1])
        return self._cache[key]

    def copy(self, key):
        return copy.deepcopy(self.get(key))

    def collection(self, spec, cid):
        out = []
        for key in self.collections[spec].get(cid, []):
            out.extend(self.get(key)[spec].get("Blueprints" if spec == "TemplateCollectionSpec" else
                                                   {"MaterialCollectionSpec": "Materials", "NeedCollectionSpec": "Needs",
                                                    "GoodCollectionSpec": "Goods"}[spec], []))
        return out

    def dump_fingerprint(self):
        """Hash of the whole dump: sorted (path, file hash) pairs. Used by the pin check."""
        h = []
        for key in sorted(self.paths):
            h.append(self.paths[key][0] + "\t" + self.sha(key))
        return sha256_bytes("\n".join(h).encode("utf-8")), len(h)
