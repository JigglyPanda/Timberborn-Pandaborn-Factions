#!/usr/bin/env python3
"""Static checks for the built Pandaborn - Factions mod. Standard library only.

    python tools/validate.py [--mod E:\\PandabornDev\\build\\PandabornFactions]

Checks the installable mod folder against the vanilla blueprint dump, the vanilla localization and the game's own
resource index (the Unity ResourceManager table inside Timberborn_Data/globalgamemanagers, which lists every
built-in asset path: sprites, materials, models, prefabs, sounds and blueprints). The resource index proves that a
vanilla path exists, not what type of asset it is; those references are listed as "existence only".

Exit code: 0 when there are no errors, 1 otherwise. Warnings do not fail the run.
"""
import argparse
import csv
import io
import json
import os
import re
import struct
import sys
import zlib

DEFAULT_MOD = r"E:\PandabornDev\build\PandabornFactions"
DEFAULT_BLUEPRINTS = r"E:\PandabornDev\reference\Blueprints"
DEFAULT_LOCALIZATIONS = r"E:\PandabornDev\reference\Localizations"
DEFAULT_GAME_DATA = r"C:\Program Files (x86)\Steam\steamapps\common\Timberborn\Timberborn_Data"

MOD_ID = "JigglyPanda.PandabornFactions"
VANILLA_FACTIONS = ("Folktails", "IronTeeth")
VANILLA_COLLECTION_PREFIXES = ("Common",)
SINGLE_SPECS = ("AdultSpec", "ChildSpec", "BotSpec", "ModularShaftPartsSpec")
SPRITE_FIELDS = ("Avatar", "ChildAvatar", "BotAvatar", "ContaminatedAdultAvatar", "ContaminatedChildAvatar", "Logo",
                 "NewGameFullAvatar")
ROOT_FILES_ALLOWED = ("manifest.json", "thumbnail.png", "thumbnail.jpg", "workshop_data.json", "readme.md")
PATH_RE = re.compile(r"^[A-Za-z0-9_\-]+(/[A-Za-z0-9_\-. ]+)+$")


class Report:
    def __init__(self):
        self.errors, self.warnings, self.infos = [], [], []
        self.existence_only, self.unchecked = set(), set()

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def info(self, msg):
        self.infos.append(msg)


R = Report()


# ----------------------------------------------------------------------------------------------- paths and indexes

def asset_key(rel_path):
    """Game's AssetPathHelper: forward slashes, lowercase, last extension stripped."""
    p = rel_path.replace("\\", "/").lstrip("/")
    root, ext = os.path.splitext(p)
    return (root if ext else p).lower()


def ref_key(value):
    return value.replace("\\", "/").lstrip("/").lower()


def load_json(path, warn_bom=False):
    with open(path, "rb") as f:
        raw = f.read()
    if raw.startswith(b"\xef\xbb\xbf"):
        if warn_bom:
            R.warn("UTF-8 BOM in " + path)
        raw = raw[3:]
    return json.loads(raw.decode("utf-8"))


def index_mod(mod_dir):
    files = {}  # rel path (forward slashes) -> abs path
    for dirpath, _, names in os.walk(mod_dir):
        for n in names:
            ab = os.path.join(dirpath, n)
            rel = os.path.relpath(ab, mod_dir).replace("\\", "/")
            files[rel] = ab
    keys = {}
    for rel in files:
        keys.setdefault(asset_key(rel), []).append(rel)
    return files, keys


def index_vanilla_blueprints(bp_dir):
    blueprints = {}  # key -> abs path
    for dirpath, _, names in os.walk(bp_dir):
        for n in names:
            if n.endswith(".blueprint.json"):
                ab = os.path.join(dirpath, n)
                blueprints[asset_key(os.path.relpath(ab, bp_dir))] = ab
    return blueprints


def index_resources(game_data):
    """Every built-in asset path, read from the Unity ResourceManager container in globalgamemanagers."""
    path = os.path.join(game_data, "globalgamemanagers")
    if not os.path.isfile(path):
        return None
    data = open(path, "rb").read()
    out = set()
    for m in re.finditer(rb"[\x20-\x7e]{3,}", data):
        s = m.start()
        if s < 4:
            continue
        n = struct.unpack("<i", data[s - 4:s])[0]
        if 3 <= n <= len(m.group()):
            out.add(m.group()[:n].decode("ascii").lower())
    return out


# ---------------------------------------------------------------------------------------------------- timbermesh

def _varint(buf, i):
    shift = result = 0
    while True:
        b = buf[i]
        i += 1
        result |= (b & 0x7F) << shift
        if not b & 0x80:
            return result, i
        shift += 7


def _fields(buf, start, end):
    i = start
    while i < end:
        key, i = _varint(buf, i)
        field, wt = key >> 3, key & 7
        if wt == 0:
            v, i = _varint(buf, i)
            yield field, wt, v
        elif wt == 1:
            yield field, wt, None
            i += 8
        elif wt == 2:
            ln, i = _varint(buf, i)
            yield field, wt, (i, i + ln)
            i += ln
        elif wt == 5:
            yield field, wt, None
            i += 4
        else:
            raise ValueError("unsupported wire type %d at %d" % (wt, i))


def _str(buf, span):
    return bytes(buf[span[0]:span[1]]).decode("utf-8", "replace")


def read_timbermesh(path):
    raw = open(path, "rb").read()
    header = raw[:2]
    data = memoryview(zlib.decompress(raw))
    nodes = []
    for f, wt, v in _fields(data, 0, len(data)):
        if f != 3 or wt != 2:
            continue
        node = {"name": "", "vertexCount": 0, "materials": [], "vertexAnimations": [], "nodeAnimations": []}
        for nf, nwt, nv in _fields(data, *v):
            if nf == 2 and nwt == 2:
                node["name"] = _str(data, nv)
            elif nf == 6 and nwt == 0:
                node["vertexCount"] = nv
            elif nf == 8 and nwt == 2:
                for mf, mwt, mv in _fields(data, *nv):
                    if mf == 2 and mwt == 2:
                        node["materials"].append(_str(data, mv))
            elif nf in (9, 10) and nwt == 2:
                for af, awt, av in _fields(data, *nv):
                    if af == 1 and awt == 2:
                        node["vertexAnimations" if nf == 9 else "nodeAnimations"].append(_str(data, av))
                        break
        nodes.append(node)
    return header, nodes


# ------------------------------------------------------------------------------------------------- helpers

def walk_strings(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_strings(v, path + "." + k if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_strings(v, "%s[%d]" % (path, i))
    elif isinstance(obj, str):
        yield path, obj


def specs_of(bp):
    """Top-level specs plus specs of Children (the game flattens both into one template)."""
    out = {k: v for k, v in bp.items() if k != "Children" and isinstance(v, dict)}
    for child in (bp.get("Children") or {}).values():
        if isinstance(child, dict):
            for k, v in child.items():
                if isinstance(v, dict):
                    out.setdefault(k, v)
    return out


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def read_loc_csv(path, game_rules):
    """Return {id: text}. With game_rules, apply the checks of the game's LocalizationCsvValidator."""
    text = open(path, "rb").read()
    if text.startswith(b"\xef\xbb\xbf"):
        R.warn("UTF-8 BOM in " + path)
        text = text[3:]
    text = text.decode("utf-8")
    name = os.path.basename(path)
    rows = list(csv.reader(io.StringIO(text, newline="")))
    if not rows or rows[0] != ["ID", "Text", "Comment"]:
        R.error("%s: header must be exactly ID,Text,Comment" % name)
    out = {}
    if game_rules:
        lines = text.split("\n")
        for n, line in enumerate(lines):
            if '\r' in line:
                R.warn("%s line %d: CRLF line ending" % (name, n + 1))
            stripped = line.replace('""', "")
            if ', "' in stripped or '" ,' in stripped:
                R.error("%s line %d: space between comma and quote (the game rejects the whole file)" % (name, n + 1))
        # empty lines between records (the game treats them as critical errors)
        reader = csv.reader(io.StringIO(text, newline=""))
        for row in reader:
            if not row:
                R.error("%s line %d: empty line" % (name, reader.line_num))
    for i, row in enumerate(rows[1:], start=2):
        if not row:
            continue
        if game_rules:
            if len(row) > 3:
                R.error("%s record %d: more than 3 columns" % (name, i))
            if len(row) < 3:
                R.error("%s record %d: fewer than 3 columns" % (name, i))
            for col in row:
                if col.endswith(" "):
                    R.error("%s record %d: trailing space in a column" % (name, i))
        key = row[0]
        if key in out:
            R.error("%s: duplicate key %s" % (name, key))
        out[key] = row[1] if len(row) > 1 else ""
        if game_rules and not out[key]:
            R.error("%s: empty text for %s" % (name, key))
    return out


# ---------------------------------------------------------------------------------------------------- checks

class Ctx:
    pass


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mod", default=DEFAULT_MOD)
    ap.add_argument("--blueprints", default=DEFAULT_BLUEPRINTS)
    ap.add_argument("--localizations", default=DEFAULT_LOCALIZATIONS)
    ap.add_argument("--game-data", default=DEFAULT_GAME_DATA)
    ap.add_argument("--quiet", action="store_true", help="only print problems and the summary")
    a = ap.parse_args()

    if not os.path.isdir(a.mod):
        sys.exit("mod folder not found: " + a.mod)
    c = Ctx()
    c.files, c.keys = index_mod(a.mod)
    c.vbp = index_vanilla_blueprints(a.blueprints)
    c.res = index_resources(a.game_data)
    if c.res is None:
        R.warn("game resource index not found; vanilla non-blueprint assets cannot be checked")
    else:
        R.info("vanilla resource index: %d paths; vanilla blueprint dump: %d blueprints" % (len(c.res), len(c.vbp)))
    c.sound_names = set()
    if c.res:
        c.sound_names = {p.rsplit("/", 1)[-1] for p in c.res if p.startswith("sounds/")}

    check_json_and_manifest(a, c)
    check_paths(c)
    load_blueprints(c)
    check_references(c)
    check_template_names(c)
    check_no_vanilla_side_effects(c)
    for fid, fspec in c.factions.items():
        check_faction(c, fid, fspec)
    check_localization(a, c)

    for m in R.infos if not a.quiet else []:
        print("INFO   ", m)
    for m in R.warnings:
        print("WARNING", m)
    for m in R.errors:
        print("ERROR  ", m)
    if R.existence_only and not a.quiet:
        print("\nVanilla references verified for existence only (type not checkable statically):")
        for m in sorted(R.existence_only):
            print("   ", m)
    if R.unchecked:
        print("\nReferences that could not be checked statically:")
        for m in sorted(R.unchecked):
            print("   ", m)
    print("\nvalidate: %d error(s), %d warning(s)" % (len(R.errors), len(R.warnings)))
    return 1 if R.errors else 0


def check_json_and_manifest(a, c):
    for rel, ab in c.files.items():
        if rel.endswith(".json"):
            try:
                load_json(ab, warn_bom=True)
            except Exception as e:  # noqa: BLE001
                R.error("JSON does not parse: %s (%s)" % (rel, e))
        if rel.endswith(".png.meta.json"):
            if rel[:-len(".meta.json")] not in c.files:
                R.error("meta file without its image: " + rel)
    if "manifest.json" not in c.files:
        R.error("manifest.json missing")
        return
    m = load_json(c.files["manifest.json"])
    for k in ("Name", "Version", "Id", "MinimumGameVersion", "Description", "RequiredMods", "OptionalMods"):
        if k not in m:
            R.error("manifest.json: missing " + k)
    if m.get("Id") != MOD_ID:
        R.error("manifest.json: Id must be " + MOD_ID)
    if m.get("RequiredMods"):
        R.warn("manifest.json: RequiredMods is not empty")
    vfile = os.path.join(a.game_data, "StreamingAssets", "VersionNumbers.json")
    if os.path.isfile(vfile):
        cur = load_json(vfile).get("CurrentVersion", "0")
        mv = m.get("MinimumGameVersion", "0")
        if tuple(int(x) for x in mv.split(".")) > tuple(int(x) for x in cur.split(".")):
            R.error("MinimumGameVersion %s is newer than the installed game %s" % (mv, cur))
        R.info("installed game %s, MinimumGameVersion %s" % (cur, mv))


def check_paths(c):
    """No file may sit on a vanilla asset path, and new files live under a Pandaborn path segment."""
    for key, rels in c.keys.items():
        if len(rels) > 1:
            R.error("several files map to the same asset path %s: %s" % (key, ", ".join(rels)))
        if key in c.vbp or (c.res and key in c.res):
            R.error("file sits on a vanilla asset path (would override vanilla): " + ", ".join(rels))
    for rel in c.files:
        low = rel.lower()
        if "/" not in low and low in ROOT_FILES_ALLOWED:
            continue
        if low.startswith("localizations/") and "pandaborn" in low.rsplit("/", 1)[-1]:
            continue
        if low.endswith(".dll") or low.startswith("scripts/") or low.startswith("assetbundles/"):
            continue
        if "pandaborn" not in [seg.lower() for seg in rel.split("/")[:-1]]:
            R.error("new file outside a Pandaborn path segment: " + rel)


def load_blueprints(c):
    c.mod_bp = {}  # key -> parsed
    for key, rels in c.keys.items():
        rel = rels[0]
        if rel.endswith(".blueprint.json"):
            try:
                c.mod_bp[key] = load_json(c.files[rel])
            except Exception:  # noqa: BLE001
                pass  # already reported
    c.vbp_cache = {}
    c.factions = {}
    for key, bp in c.mod_bp.items():
        if "FactionSpec" in bp:
            c.factions[bp["FactionSpec"]["Id"]] = bp
    if not c.factions:
        R.error("no FactionSpec in the mod")


def vanilla_bp(c, key):
    if key not in c.vbp_cache:
        try:
            c.vbp_cache[key] = load_json(c.vbp[key])
        except Exception as e:  # noqa: BLE001
            R.error("vanilla blueprint unreadable %s: %s" % (key, e))
            c.vbp_cache[key] = {}
    return c.vbp_cache[key]


def get_bp(c, key):
    """Blueprint as the game sees it: vanilla merged with a mod file at the same path (we forbid that anyway)."""
    if key in c.mod_bp:
        return c.mod_bp[key]
    if key in c.vbp:
        return vanilla_bp(c, key)
    return None


def all_vanilla_specs(c, spec_name):
    for key in c.vbp:
        bp = vanilla_bp(c, key)
        if spec_name in bp:
            yield key, bp[spec_name]


def resolve(c, value, where, kind=None):
    """kind: None, 'sprite', 'texture', 'timbermesh', 'blueprint'."""
    k = ref_key(value)
    if k in c.keys:
        rel = c.keys[k][0]
        ext = rel.lower()
        if kind == "blueprint" and not ext.endswith(".blueprint.json"):
            R.error("%s: %s is not a blueprint" % (where, value))
        if kind in ("sprite", "texture") and not (ext.endswith(".png") or ext.endswith(".jpg")):
            R.error("%s: %s is not an image" % (where, value))
        if kind == "timbermesh" and not ext.endswith(".timbermesh"):
            R.error("%s: %s is not a .timbermesh" % (where, value))
        if kind == "sprite":
            meta = c.files.get(rel + ".meta.json")
            try:
                is_sprite = bool(meta) and load_json(meta).get("isSprite") is True
            except Exception:  # noqa: BLE001 - unparsable meta is reported by the JSON check
                is_sprite = False
            if not is_sprite:
                R.error("%s: %s is used as a sprite but has no {\"isSprite\": true} meta file" % (where, value))
        if kind in ("sprite", "texture") and png_size(c.files[rel]) is None and ext.endswith(".png"):
            R.error("%s: %s is not a valid PNG" % (where, value))
        return "mod"
    if k in c.vbp:
        return "vanilla"
    if c.res is None:
        R.unchecked.add("%s -> %s (no resource index)" % (where, value))
        return "unknown"
    if k in c.res:
        R.existence_only.add(value)
        return "vanilla"
    R.error("%s: reference does not resolve: %s" % (where, value))
    return None


def check_references(c):
    for key, bp in c.mod_bp.items():
        rel = c.keys[key][0]
        fs = bp.get("FactionSpec")
        handled = set()
        if fs:
            for f in SPRITE_FIELDS:
                if fs.get(f):
                    resolve(c, fs[f], rel + " FactionSpec." + f, "sprite")
                    handled.add("FactionSpec." + f)
                else:
                    R.error("%s: FactionSpec.%s is empty" % (rel, f))
            for f in ("Textures", "ChildTextures"):
                if not fs.get(f):
                    R.error("%s: FactionSpec.%s is empty" % (rel, f))
                for i, t in enumerate(fs.get(f) or []):
                    resolve(c, t, rel + " FactionSpec.%s[%d]" % (f, i), "texture")
                    handled.add("FactionSpec.%s[%d]" % (f, i))
        fw = bp.get("FactionWonderSpec")
        if fw:
            resolve(c, fw.get("WonderCompletionImage", ""), rel + " FactionWonderSpec.WonderCompletionImage", "sprite")
            handled.add("FactionWonderSpec.WonderCompletionImage")
            check_sound(c, fw.get("WonderLaunchSound", ""), rel + " FactionWonderSpec.WonderLaunchSound")
        tc = bp.get("TemplateCollectionSpec")
        if tc:
            for i, b in enumerate(tc.get("Blueprints", [])):
                resolve(c, b, rel + " TemplateCollectionSpec.Blueprints[%d]" % i, "blueprint")
                handled.add("TemplateCollectionSpec.Blueprints[%d]" % i)
        for child_name, child in (bp.get("Children") or {}).items():
            tm = child.get("TimbermeshSpec") if isinstance(child, dict) else None
            if tm:
                resolve(c, tm.get("Model", ""), rel + " %s.TimbermeshSpec.Model" % child_name, "timbermesh")
                handled.add("Children.%s.TimbermeshSpec.Model" % child_name)
        for path, value in walk_strings(bp):
            if path in handled or not PATH_RE.match(value):
                continue
            kind = "texture" if path.startswith("DecalSpec.Texture") else None
            resolve(c, value, rel + " " + path, kind)


def check_sound(c, name, where):
    if not name:
        R.error(where + " is empty")
    elif c.res is None:
        R.unchecked.add("%s -> %s" % (where, name))
    elif name.lower() not in c.sound_names and not any(
            re.fullmatch(re.escape(name.lower()) + r"_\d+", s) for s in c.sound_names):
        R.error("%s: no built-in sound named %s (or %s_NN variants)" % (where, name, name))


def check_template_names(c):
    vanilla_names = set()
    for _, ts in all_vanilla_specs(c, "TemplateSpec"):
        vanilla_names.add(ts.get("TemplateName"))
        vanilla_names.update(ts.get("BackwardCompatibleTemplateNames") or [])
    seen = {}
    for key, bp in c.mod_bp.items():
        ts = bp.get("TemplateSpec")
        if not ts:
            continue
        rel = c.keys[key][0]
        for n in [ts.get("TemplateName")] + list(ts.get("BackwardCompatibleTemplateNames") or []):
            if n in vanilla_names:
                R.error("%s: template name %s clashes with a vanilla template" % (rel, n))
            if n in seen:
                R.error("%s: template name %s also used by %s" % (rel, n, seen[n]))
            seen[n] = rel
        if not str(ts.get("TemplateName", "")).endswith(".Inkpaws"):
            R.error("%s: template name %s does not end in .Inkpaws" % (rel, ts.get("TemplateName")))
    R.info("mod template names: " + ", ".join(sorted(seen)))


def check_no_vanilla_side_effects(c):
    """Nothing in the mod may join a collection or keyed spec that a vanilla faction loads."""
    vanilla_ids = {"template": {"Common"}, "material": {"Common"}, "need": {"Common"}, "good": {"Common"}}
    for _, fs in all_vanilla_specs(c, "FactionSpec"):
        vanilla_ids["template"].update(fs.get("TemplateCollectionIds", []))
        vanilla_ids["material"].update(fs.get("MaterialCollectionIds", []))
        vanilla_ids["need"].update(fs.get("NeedCollectionIds", []))
        vanilla_ids["good"].update(fs.get("GoodCollectionIds", []))
    for key, bp in c.mod_bp.items():
        rel = c.keys[key][0]
        for spec, kind in (("TemplateCollectionSpec", "template"), ("MaterialCollectionSpec", "material"),
                           ("NeedCollectionSpec", "need"), ("GoodCollectionSpec", "good")):
            if spec in bp and bp[spec].get("CollectionId") in vanilla_ids[kind]:
                R.error("%s: adds to vanilla %s collection %s (changes vanilla factions)"
                        % (rel, kind, bp[spec]["CollectionId"]))
        for spec in ("DecalSpec", "WorkerOutfitSpec"):
            if spec in bp:
                fid = bp[spec].get("FactionId", "")
                if not fid or fid in VANILLA_FACTIONS:
                    R.error("%s: %s.FactionId '%s' would apply to vanilla factions" % (rel, spec, fid))
                elif fid not in c.factions:
                    R.error("%s: %s.FactionId '%s' is not a faction of this mod" % (rel, spec, fid))
        for spec in ("NeedSpec", "GoodSpec", "RecipeSpec", "NeedGroupSpec"):
            if spec in bp:
                gid = bp[spec].get("Id", "")
                if not (gid.startswith("Pandaborn") or "Inkpaws" in gid):
                    R.error("%s: global id %s should start with Pandaborn or be Inkpaws-scoped" % (rel, gid))


def collection_members(c, spec_name, collection_id):
    out = []
    for key, bp in c.mod_bp.items():
        s = bp.get(spec_name)
        if s and s.get("CollectionId") == collection_id:
            out.append((c.keys[key][0], s))
    for key, s in all_vanilla_specs(c, spec_name):
        if s.get("CollectionId") == collection_id:
            out.append((key, s))
    return out


def check_faction(c, fid, bp):
    fs = bp["FactionSpec"]
    where = "Faction %s" % fid
    if "FactionWonderSpec" not in bp:
        R.error(where + ": FactionWonderSpec missing (the UI sound controller reads it without a null check)")
    if "StartingFactionSpec" in bp:
        R.warn(where + ": StartingFactionSpec is tutorial-only")
    if "UnlockableFactionSpec" in bp:
        R.warn(where + ": UnlockableFactionSpec makes the faction locked at start")
    check_sound(c, "UI.Beavers.%s.Selected.Adult_Content" % fs.get("SoundId", ""), where + " SoundId")

    # collections exist (mirrors the game's FactionSpec*Validator)
    for field, spec in (("TemplateCollectionIds", "TemplateCollectionSpec"),
                        ("MaterialCollectionIds", "MaterialCollectionSpec"),
                        ("NeedCollectionIds", "NeedCollectionSpec"), ("GoodCollectionIds", "GoodCollectionSpec")):
        for cid in fs.get(field, []):
            if not collection_members(c, spec, cid):
                R.error("%s: %s %s not found" % (where, spec, cid))

    # the faction's active templates: its template collections plus Common
    templates = []  # (key, bp)
    for cid in list(fs.get("TemplateCollectionIds", [])) + ["Common"]:
        for src, tcs in collection_members(c, "TemplateCollectionSpec", cid):
            for b in tcs.get("Blueprints", []):
                k = ref_key(b)
                t = get_bp(c, k)
                if t is None:
                    R.error("%s: collection %s (%s) lists missing blueprint %s" % (where, cid, src, b))
                else:
                    templates.append((k, t))
    counts = {s: [] for s in SINGLE_SPECS + ("PlaneSpec",)}
    names = {}
    by_spec = {}
    for k, t in templates:
        sp = specs_of(t)
        for s in counts:
            if s in sp:
                counts[s].append(k)
                by_spec.setdefault(s, t)
        ts = sp.get("TemplateSpec")
        if ts:
            n = ts.get("TemplateName")
            if n in names and names[n] != k:
                R.error("%s: duplicate template name %s in %s and %s" % (where, n, names[n], k))
            names[n] = k
    for s in SINGLE_SPECS:
        if len(counts[s]) != 1:
            R.error("%s: expected exactly one %s across its collections + Common, found %d: %s"
                    % (where, s, len(counts[s]), counts[s]))
        else:
            R.info("%s: %s from %s" % (where, s, counts[s][0]))
    if counts["PlaneSpec"]:
        R.warn("%s: PlaneSpec present (only the Iron Teeth wonder uses one): %s" % (where, counts["PlaneSpec"]))
    R.info("%s: %d active templates" % (where, len(templates)))

    # starting building
    sb = fs.get("StartingBuildingId")
    if sb not in names:
        R.error("%s: StartingBuildingId %s is not among the faction's templates" % (where, sb))

    # decals for both categories (the decal service indexes them without a check)
    cats = {}
    for key, b in list(c.mod_bp.items()):
        d = b.get("DecalSpec")
        if d and d.get("FactionId") == fid:
            cats.setdefault(d.get("Category"), []).append(d.get("Texture"))
    for cat in ("Banners", "Tails"):
        if not cats.get(cat):
            R.error("%s: no DecalSpec for category %s" % (where, cat))
        else:
            R.info("%s: %d %s decals" % (where, len(cats[cat]), cat))

    # worker outfits: unique per (Id, WorkerType); every outfit used by a workplace exists; attachments exist
    outfits = {}
    for key, b in c.mod_bp.items():
        o = b.get("WorkerOutfitSpec")
        if o and o.get("FactionId") == fid:
            k2 = (o.get("Id"), o.get("WorkerType"))
            if k2 in outfits:
                R.error("%s: duplicate WorkerOutfitSpec %s (the game builds a dictionary and throws)" % (where, k2))
            outfits[k2] = (c.keys[key][0], o)
    used = set()
    for k, t in templates:
        w = specs_of(t).get("WorkplaceWorkerOutfitSpec")
        if w and w.get("WorkerOutfit"):
            used.add(w["WorkerOutfit"])
    for u in sorted(used):
        if (u, "Beaver") not in outfits:
            R.error("%s: workplaces use outfit %s but there is no Beaver WorkerOutfitSpec for it" % (where, u))
        if (u, "Bot") not in outfits:
            R.info("%s: no Bot outfit for %s (vanilla Folktails has none for some outfits either)" % (where, u))
    attach_sets = {}
    for worker, spec in (("Beaver", "AdultSpec"), ("Bot", "BotSpec")):
        t = by_spec.get(spec)
        if t:
            attach_sets[worker] = {a.get("AttachmentId") for a in
                                   specs_of(t).get("TemplateAttachmentsSpec", {}).get("Attachments", [])}
    for (oid, wt), (rel, o) in sorted(outfits.items()):
        for att in o.get("Attachments", []):
            if wt in attach_sets and att not in attach_sets[wt]:
                R.error("%s: outfit attachment %s is not defined on the %s template" % (rel, att, wt))
    R.info("%s: %d worker outfits, %d outfit ids used by workplaces" % (where, len(outfits), len(used)))

    # materials available to this faction's meshes
    material_names = set()
    for cid in list(fs.get("MaterialCollectionIds", [])) + ["Common"]:
        for _, mcs in collection_members(c, "MaterialCollectionSpec", cid):
            for m in mcs.get("Materials", []):
                material_names.add(m.replace("\\", "/").rsplit("/", 1)[-1])

    # character bodies: mesh exists, animations, attachment points and materials match the blueprint
    for spec in ("AdultSpec", "ChildSpec"):
        for k in counts[spec]:
            check_character_mesh(c, where, k, get_bp(c, k), material_names)


def check_character_mesh(c, where, key, bp, material_names):
    model = None
    for child in (bp.get("Children") or {}).values():
        if isinstance(child, dict) and "TimbermeshSpec" in child:
            model = child["TimbermeshSpec"].get("Model")
    rel = c.keys.get(key, [key])[0]
    if not model:
        R.error("%s: %s has no TimbermeshSpec" % (where, rel))
        return
    if not model.lower().replace("\\", "/").startswith("characters/pandaborn/"):
        R.error("%s: %s uses a body outside Characters/Pandaborn (%s): not faction-only" % (where, rel, model))
    mk = ref_key(model)
    if mk not in c.keys:
        R.error("%s: body mesh %s is not in the mod (is the build missing the large meshes?)" % (where, model))
        return
    path = c.files[c.keys[mk][0]]
    try:
        header, nodes = read_timbermesh(path)
    except Exception as e:  # noqa: BLE001
        R.error("%s: cannot read %s: %s" % (where, model, e))
        return
    if header != b"\x78\x9c":
        R.error("%s: %s zlib header is %s, the game requires 78 9C" % (where, model, header.hex()))
    node_names = {n["name"] for n in nodes}
    anims = set()
    mats = set()
    for n in nodes:
        anims.update(n["vertexAnimations"])
        anims.update(n["nodeAnimations"])
        mats.update(m for m in n["materials"] if m)
    sp = specs_of(bp)
    wanted = set()
    for st in sp.get("TimbermeshAnimatorControllerSpec", {}).get("AnimatorStates", []):
        wanted.add(st.get("AnimationName"))
    wanted.update(sp.get("VariedIdleAnimationSpec", {}).get("Variants", []))
    for a in sp.get("AnimationParticlesTriggerSpec", {}).get("AnimationParticles", []):
        wanted.add(a.get("AnimationName"))
    for w in sp.get("WorkerOutfitAnimationAttachmentVisibilitySpec", {}).get("WorkerOutfitAnimationAttachments", []):
        wanted.update(w.get("AnimationNames", []))
    missing = sorted(x for x in wanted if x and x not in anims)
    if missing:
        R.error("%s: %s lacks animations used by %s: %s" % (where, model, rel, ", ".join(missing)))
    parents = {a.get("Parent") for a in sp.get("TemplateAttachmentsSpec", {}).get("Attachments", [])}
    for p in sorted(x for x in parents if x):
        if p.lstrip("#") not in node_names and p not in node_names:
            R.error("%s: %s has no attachment node %s used by %s" % (where, model, p, rel))
    for m in sorted(mats):
        if m not in material_names:
            R.error("%s: %s uses material %s, which is not in the faction's material collections or Common"
                    % (where, model, m))
    body = max(nodes, key=lambda n: n["vertexCount"]) if nodes else None
    R.info("%s: %s OK: %d nodes, %d animations (%d used), materials %s, body vertices %d"
           % (where, model, len(nodes), len(anims), len(wanted), sorted(mats), body["vertexCount"] if body else 0))


def check_localization(a, c):
    mod_locs = {}
    for rel, ab in c.files.items():
        low = rel.lower()
        if low.startswith("localizations/") and low.endswith(".csv"):
            lang = os.path.basename(rel).split("_", 1)[0].split(".", 1)[0]
            recs = read_loc_csv(ab, game_rules=(lang == "enUS"))
            mod_locs.setdefault(lang, {}).update(recs)
    vanilla = {}
    vpath = os.path.join(a.localizations, "enUS.csv")
    if os.path.isfile(vpath):
        with open(vpath, encoding="utf-8-sig", newline="") as f:
            for row in csv.reader(f):
                if row:
                    vanilla[row[0]] = row[1] if len(row) > 1 else ""
    else:
        R.warn("vanilla enUS.csv not found; loc keys checked against the mod only")
    en = mod_locs.get("enUS", {})
    for k in en:
        if k in vanilla:
            R.error("loc key %s overrides vanilla text (changes vanilla factions)" % k)
    referenced = set()
    for key, bp in c.mod_bp.items():
        for path, value in walk_strings(bp):
            if path.split(".")[-1].split("[")[0].endswith("LocKey") and value:
                referenced.add((c.keys[key][0], value))
    for rel, k in sorted(referenced):
        if k not in en and k not in vanilla:
            R.error("%s: loc key %s not found in the mod's enUS or vanilla enUS" % (rel, k))
    unused = set(en) - {k for _, k in referenced}
    if unused:
        R.info("mod loc keys not referenced by mod blueprints (may be used elsewhere): " + ", ".join(sorted(unused)))
    R.info("loc: %d mod enUS keys, %d referenced keys" % (len(en), len(referenced)))


if __name__ == "__main__":
    sys.exit(main())
