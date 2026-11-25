#!/usr/bin/env python3
"""Static checks for a built Timberborn mod folder (by default the Pandaborn - Factions build). Standard library only.

    python tools/validate.py [--mod E:\\PandabornDev\\build\\PandabornFactions] [--schema schema/1.1.2.8.json]
    python tools/validate.py --mod <any mod folder, e.g. a prototype>      # generic rules: no lock, no Pandaborn id
    python tools/validate.py --self-test                                  # run the broken-fixture suite

Schema checks (v2), against schema/<game version>.json written by tools/schema (the game's own spec classes):
every blueprint key must be a spec the game knows (an unknown key throws when the blueprint is read, and goods,
needs, recipes, collections, decals, outfits and the faction file are read in every game); every field must be a
serialised field of that spec (an unknown or renamed field is silently ignored by the game) with a compatible JSON
type and exactly spelled enum values; asset references resolve (mod files with exact case and forward slashes, or
the game's resource index); custom (mod-defined) specs appear only in templates, never in globally indexed
blueprints or faction modifiers; the game's NeedVerifier rules; every good a template or recipe uses is in the
faction's good collections; recipe ids, template names, good/need ids and spec class names are unique against
vanilla and within the mod; ids match catalogue/ids.lock.json (append-only, checked against git HEAD) and the prefix
rules; every asset bundle has its _win/_mac pair; material coverage when a faction drops the vanilla collection.

Checks the installable mod folder against the vanilla blueprint dump, the vanilla localization and the game's own
resource index (the Unity ResourceManager table inside Timberborn_Data/globalgamemanagers, which lists every
built-in asset path: sprites, materials, models, prefabs, sounds and blueprints). The resource index proves that a
vanilla path exists, not what type of asset it is; those references are listed as "existence only".

Exit code: 0 when there are no errors, 1 otherwise. Warnings do not fail the run.
"""
import argparse
import csv
import difflib
import io
import json
import os
import re
import struct
import subprocess
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
# the only label keys CharacterBatchControlTab.GetSortingKey accepts (plus Beaver.Population.Contaminated)
CHARACTER_LABEL_KEYS = {"AdultSpec": "Beaver.Adult.TemplateName", "ChildSpec": "Beaver.Child.TemplateName",
                        "BotSpec": "Bot.TemplateName"}
SPRITE_FIELDS = ("Avatar", "ChildAvatar", "BotAvatar", "ContaminatedAdultAvatar", "ContaminatedChildAvatar", "Logo",
                 "NewGameFullAvatar")
ROOT_FILES_ALLOWED = ("manifest.json", "thumbnail.png", "thumbnail.jpg", "workshop_data.json", "readme.md")
PATH_RE = re.compile(r"^[A-Za-z0-9_\-]+(/[A-Za-z0-9_\-. ]+)+$")


class Report:
    def __init__(self):
        self.errors, self.warnings, self.infos = [], [], []
        self.existence_only, self.unchecked = set(), set()

    def error(self, msg):
        if msg not in self.errors:
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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mod", default=DEFAULT_MOD)
    ap.add_argument("--blueprints", default=DEFAULT_BLUEPRINTS)
    ap.add_argument("--localizations", default=DEFAULT_LOCALIZATIONS)
    ap.add_argument("--game-data", default=DEFAULT_GAME_DATA)
    ap.add_argument("--schema", default=None, help="schema JSON (default: schema/<installed game version>.json)")
    ap.add_argument("--mod-schema", action="append", default=[],
                    help="extra schema JSON holding the mod's own spec classes (tools/schema --include)")
    ap.add_argument("--lock", default=None, help="ids.lock.json (default: catalogue/ids.lock.json for this mod)")
    ap.add_argument("--no-lock", action="store_true", help="skip the id lock checks")
    ap.add_argument("--profile", choices=("auto", "pandaborn", "generic"), default="auto",
                    help="pandaborn: this mod's rules (manifest id, lock); generic: any mod; auto: by manifest Id")
    ap.add_argument("--template-suffix", action="append", default=[],
                    help="allowed template name suffix (default: '.<faction id>' for each faction in the mod)")
    ap.add_argument("--id-prefix", default="Pandaborn", help="required prefix of global ids (default Pandaborn)")
    ap.add_argument("--base-mod", action="append", default=[],
                    help="a mod this folder merges into (e.g. the faction build under a prototype that adds fragments "
                         "at the same paths); its files are merged under this mod's, as the game merges them")
    ap.add_argument("--release", action="store_true",
                    help="release rules: a missing _mac bundle twin is an error (dev builds only warn)")
    ap.add_argument("--quiet", action="store_true", help="only print problems and the summary")
    ap.add_argument("--self-test", action="store_true", help="run the broken-fixture suite (written from the vanilla "
                    "dump by tools/tests/validate/make_fixtures.py into --fixtures-dir)")
    ap.add_argument("--fixtures-dir", default=r"E:\PandabornDev\build\validate-fixtures")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test(a)

    global R
    R = Report()
    if not os.path.isdir(a.mod):
        print("ERROR   mod folder not found: " + a.mod)
        return 1
    c = Ctx()
    c.args = a
    c.files, c.keys = index_mod(a.mod)
    c.base_files = {}  # rel -> abs, files of --base-mod folders (merged under the mod, as the game merges same paths)
    for base in a.base_mod:
        bf, _ = index_mod(base)
        for rel, ab in bf.items():
            c.base_files.setdefault(rel, []).append(ab)
    if c.base_files:
        for rel in c.base_files:
            if rel not in c.files and rel.lower() not in ROOT_FILES_ALLOWED:
                c.files[rel] = c.base_files[rel][-1]
        c.keys = {}
        for rel in c.files:
            c.keys.setdefault(asset_key(rel), []).append(rel)
    c.vbp = index_vanilla_blueprints(a.blueprints)
    c.res = index_resources(a.game_data)
    if c.res is None:
        R.warn("game resource index not found; vanilla non-blueprint assets cannot be checked")
    else:
        R.info("vanilla resource index: %d paths; vanilla blueprint dump: %d blueprints" % (len(c.res), len(c.vbp)))
    c.sound_names = set()
    if c.res:
        c.sound_names = {p.rsplit("/", 1)[-1] for p in c.res if p.startswith("sounds/")}

    manifest_id = check_json_and_manifest(a, c)
    c.profile = a.profile if a.profile != "auto" else ("pandaborn" if manifest_id == MOD_ID else "generic")
    a.profile = c.profile
    R.info("profile: " + c.profile)
    c.schema = load_schema(a, c)
    check_paths(c)
    load_blueprints(c)
    check_schema(c)
    check_references(c)
    check_asset_refs(c)
    check_models(c)
    check_template_names(c)
    check_building_sounds(c)
    check_spec_dependencies(c)
    check_no_vanilla_side_effects(c)
    check_global_specs(c)
    check_unique_ids(c)
    check_needs(c)
    for fid, fspec in c.factions.items():
        check_faction(c, fid, fspec)
        check_faction_goods(c, fid, fspec)
        check_material_coverage(c, fid, fspec)
        check_economy(c, fid, fspec)
    check_localization(a, c)
    check_bundles(c)
    check_modules(c)
    check_lock(c)

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
    if R.unchecked and not a.quiet:
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
        return None
    m = load_json(c.files["manifest.json"])
    for k in ("Name", "Version", "Id", "MinimumGameVersion", "Description", "RequiredMods", "OptionalMods"):
        if k not in m:
            R.error("manifest.json: missing " + k)
    if a.profile == "pandaborn" and m.get("Id") != MOD_ID:
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
    return m.get("Id")


def check_paths(c):
    """No file may sit on a vanilla asset path, and new files live under a Pandaborn path segment."""
    for key, rels in c.keys.items():
        if len(rels) > 1:
            R.error("several files map to the same asset path %s: %s" % (key, ", ".join(rels)))
        if key in c.vbp or (c.res and key in c.res):
            R.error("file sits on a vanilla asset path (would override vanilla): " + ", ".join(rels))
    for rel in c.files:
        low = rel.lower()
        if low.startswith("assetbundles.parked/"):
            # a second enabled copy of the mod parks its own bundles here (docs/tech/stage0.md); never content
            msg = "%s: a parked bundle folder (left by a second enabled copy of the mod) must not ship" % rel
            if c.args.release:
                R.error(msg)
            else:
                R.warn(msg)
            continue
        if "/" not in low and low in ROOT_FILES_ALLOWED:
            continue
        if low.startswith("localizations/") and "pandaborn" in low.rsplit("/", 1)[-1]:
            continue
        if low.endswith(".dll") or low.startswith(("scripts/", "modules/", "assetbundles/")):
            continue
        if "pandaborn" not in [seg.lower() for seg in rel.split("/")[:-1]]:
            R.error("new file outside a Pandaborn path segment: " + rel)


def merge_json(base, over):
    """The game's JsonMerger: objects merge deeply, arrays and values replace; key#append / key#remove edit arrays,
    key#delete removes the key."""
    if not isinstance(base, dict) or not isinstance(over, dict):
        return over
    out = dict(base)
    for k, v in over.items():
        if k.endswith("#append"):
            name = k[:-7]
            out[name] = list(out.get(name) or []) + list(v or [])
        elif k.endswith("#remove"):
            name = k[:-7]
            out[name] = [x for x in out.get(name) or [] if x not in (v or [])]
        elif k.endswith("#delete"):
            out.pop(k[:-7], None)
        elif k in out:
            out[k] = merge_json(out[k], v)
        else:
            out[k] = v
    return out


def load_blueprints(c):
    c.mod_bp = {}  # key -> parsed (indexed blueprints)
    c.optional_bp = {}  # key -> parsed (.optional.blueprint.json: merge-only or faction modifiers, never indexed)
    for key, rels in c.keys.items():
        rel = rels[0]
        if rel.endswith(".blueprint.json"):
            try:
                data = load_json(c.files[rel])
                for base in reversed(c.base_files.get(rel, [])):
                    if base != c.files[rel]:
                        data = merge_json(load_json(base), data)
            except Exception:  # noqa: BLE001
                continue  # already reported
            if rel.endswith(".optional.blueprint.json"):
                c.optional_bp[key] = data
            else:
                c.mod_bp[key] = data
    c.vbp_cache = {}
    c.factions = {}
    c.faction_fragments = []
    for key, bp in c.mod_bp.items():
        if "FactionSpec" in bp:
            if bp["FactionSpec"].get("Id"):
                c.factions[bp["FactionSpec"]["Id"]] = bp
            else:
                # a merge fragment for a faction file of another mod (same path, merged by the game)
                c.faction_fragments.append(c.keys[key][0])
                R.info("%s: FactionSpec without Id: a merge fragment for another mod's faction file; faction checks "
                       "need the merged result (validate the base mod with this one installed)" % c.keys[key][0])
    if not c.factions and c.profile == "pandaborn":
        R.error("no FactionSpec in the mod")
    c.tutorial_factions = sorted(f for f, bp in c.factions.items() if "StartingFactionSpec" in bp)


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
            # The game turns any PNG into a Sprite when one is asked for (ModSpriteConverter); "isSprite" is only
            # a texture preset (no mipmaps, clamped). Goods icons are drawn small in the world, so they carry
            # mipmap settings instead, as the official BerryJam example does. House rule: every icon has a meta
            # file stating one or the other, because a bare PNG loads mipmapped with repeat wrapping.
            try:
                m = load_json(meta) if meta else None
                has_settings = isinstance(m, dict) and (m.get("isSprite") is True or m.get("generateMipmap") is True)
            except Exception:  # noqa: BLE001 - unparsable meta is reported by the JSON check
                has_settings = False
            if not has_settings:
                R.error("%s: %s is used as a sprite but has no {\"isSprite\": true} meta file "
                        "(or mipmap settings, for goods icons)" % (where, value))
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
        typed = {v for _, v, _ in getattr(c, "asset_refs", [])}   # checked with their asset type by the schema
        for path, value in walk_strings(bp):
            if path in handled or not PATH_RE.match(value) or value in typed:
                continue
            kind = "texture" if path.startswith("DecalSpec.Texture") else None
            resolve(c, value, rel + " " + path, kind)


BUNDLE_PY = r"E:\PandabornDev\tools\venv\Scripts\python.exe"   # has UnityPy (docs/tech/sound.md)
BUNDLE_LIST = r"""
import sys, UnityPy
for path in sys.argv[1:]:
    env = UnityPy.load(path)
    for name in env.container.keys():
        print(name)
"""


def mod_bundle_assets(c):
    """Asset paths inside the mod's own AssetBundles/*_win, as the game asks for them (the container path after
    "/resources/", lower case, no extension), read with UnityPy from the art venv. None when they cannot be read."""
    if hasattr(c, "bundle_assets"):
        return c.bundle_assets
    mod_bundle_sounds(c)
    return c.bundle_assets


def mod_bundle_sounds(c):
    """Clip names inside the mod's own AssetBundles/*_win (container paths .../resources/sounds/.../<clip>.wav), read
    with UnityPy from the art venv. None when they cannot be read (then such sounds are reported as unchecked)."""
    if hasattr(c, "bundle_sounds"):
        return c.bundle_sounds
    c.bundle_sounds = set()
    c.bundle_assets = set()
    bundles = [c.files[r] for r in c.files if r.lower().startswith("assetbundles/") and r.lower().endswith("_win")]
    if not bundles:
        return c.bundle_sounds
    if not os.path.isfile(BUNDLE_PY):
        c.bundle_sounds = None
        c.bundle_assets = None
        return None
    try:
        r = subprocess.run([BUNDLE_PY, "-I", "-c", BUNDLE_LIST] + bundles, capture_output=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired):
        c.bundle_sounds = None
        c.bundle_assets = None
        return None
    if r.returncode != 0:
        c.bundle_sounds = None
        c.bundle_assets = None
        return None
    for line in r.stdout.decode("utf-8", "replace").splitlines():
        low = line.strip().lower()
        if "/resources/" in low:
            c.bundle_assets.add(low.split("/resources/", 1)[1].rsplit(".", 1)[0])
        if "/resources/sounds/" in low and low.endswith(".wav"):
            c.bundle_sounds.add(low.rsplit("/", 1)[-1][:-4])
    return c.bundle_sounds


def sound_known(names, name):
    low = name.lower()
    return low in names or any(re.fullmatch(re.escape(low) + r"_\d+", s) for s in names)


def check_sound(c, name, where):
    if not name:
        R.error(where + " is empty")
        return
    own = mod_bundle_sounds(c)
    if own and sound_known(own, name):
        return
    if c.res is None or (own is None and "pandaborn" in name.lower()):
        R.unchecked.add("%s -> %s" % (where, name))
    elif not sound_known(c.sound_names, name):
        R.error("%s: no built-in sound or sound in the mod's bundles named %s (or %s_NN variants)" % (where, name, name))


# specs whose component looks up the Workshop component of the same building without a null check: without WorkshopSpec
# the building throws when finished (the workerless Dew Collector, gate run 2026-11-14)
NEEDS_WORKSHOP = ("WorkshopParticleControllerSpec", "WorkshopAnimationControllerSpec", "WorkshopWorkerHiderSpec",
                  "SimpleManufactoryBehaviorsSpec")


def check_spec_dependencies(c):
    for key, bp in sorted(c.mod_bp.items()):
        if "WorkshopSpec" in bp:
            continue
        for spec in NEEDS_WORKSHOP:
            if spec in bp:
                R.error("%s: %s without WorkshopSpec: its component needs the building's Workshop and throws when the "
                        "building is finished" % (c.keys[key][0], spec))


def check_building_sounds(c):
    """BuildingSpec sounds of our own (names starting Pandaborn.): looping Environment.Buildings.Loop.<name>, selection
    UI.Buildings.Selected.<name> must be a clip in the game or the mod's bundles (a missing clip throws when played)."""
    for key, bp in sorted(c.mod_bp.items()):
        bs = bp.get("BuildingSpec")
        if not bs:
            continue
        rel = c.keys[key][0]
        for field, prefix in (("LoopingSoundName", "Environment.Buildings.Loop."), ("SelectionSoundName", "UI.Buildings.Selected.")):
            v = bs.get(field) or ""
            if v.lower().startswith("pandaborn"):
                check_sound(c, prefix + v, "%s BuildingSpec.%s" % (rel, field))


def check_template_names(c):
    vanilla_names = set()
    for _, ts in all_vanilla_specs(c, "TemplateSpec"):
        vanilla_names.add(ts.get("TemplateName"))
        vanilla_names.update(ts.get("BackwardCompatibleTemplateNames") or [])
    seen = {}
    aliases = {}
    for key, bp in sorted(c.mod_bp.items()):
        ts = bp.get("TemplateSpec")
        if not ts:
            continue
        rel = c.keys[key][0]
        n = ts.get("TemplateName")
        if not n:
            R.error("%s: TemplateSpec without a TemplateName" % rel)
            continue
        if n in vanilla_names:
            R.error("%s: template name %s clashes with a vanilla template name or alias; the game throws" % (rel, n))
        if n in seen:
            R.error("%s: template name %s is also used by %s; template names must be unique game-wide" % (rel, n, seen[n]))
        seen[n] = rel
        suffixes = c.args.template_suffix or ["." + f for f in c.factions]
        if suffixes and not any(n.endswith(x) for x in suffixes):
            R.error("%s: template name %s must end in %s (collision-proof names; docs/ENGINEERING.md)"
                    % (rel, n, " or ".join(suffixes)))
        for al in ts.get("BackwardCompatibleTemplateNames") or []:
            if al in vanilla_names and not (al in TUTORIAL_ALIASES and c.tutorial_factions):
                R.error("%s: alias %s clashes with a vanilla template name or alias" % (rel, al))
            aliases.setdefault(al, []).append(rel)
    for al, rels in sorted(aliases.items()):
        if len(rels) > 1:
            R.error("alias %s is claimed by several templates: %s" % (al, ", ".join(rels)))
        if al in seen:
            # TemplateNameMapper adds aliases after names with throwIfDuplicated: false: the name wins, the alias is
            # only a fallback (the Ringtails prototype relies on this)
            R.warn("%s: alias %s equals the template name of %s; the alias only applies when that template is absent"
                   % (rels[0], al, seen[al]))
    R.info("mod template names: " + ", ".join(sorted(str(x) for x in seen)))


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
        for spec in ("NeedSpec", "GoodSpec", "RecipeSpec", "NeedGroupSpec", "WorkerTypeSpec"):
            if spec in bp:
                gid = bp[spec].get("Id", "")
                if not (gid.startswith(c.args.id_prefix) or any(f in gid for f in c.factions)):
                    R.error("%s: global id %s must start with %s or be scoped to this mod's faction (other mods have "
                            "crashed over shared ids such as Grapes)" % (rel, gid, c.args.id_prefix))
        for spec in ("TemplateCollectionSpec", "MaterialCollectionSpec", "NeedCollectionSpec", "GoodCollectionSpec"):
            if spec in bp:
                cid = bp[spec].get("CollectionId", "")
                if cid and not (cid.startswith(c.args.id_prefix)
                                or any(cid.endswith("." + f) or cid == f for f in c.factions)):
                    R.error("%s: collection id %s must start with %s or end with .<faction id>"
                            % (rel, cid, c.args.id_prefix))


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
    if "StartingFactionSpec" in bp and not any(r.lower().startswith("tutorials/") for r in c.files):
        R.warn(where + ": StartingFactionSpec switches the tutorial system on, but the mod ships no tutorial")
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

    # character labels: the Population tab of the batch-control window groups characters by
    # SimpleLabeledEntitySpec.EntityNameLocKey and CharacterBatchControlTab.GetSortingKey throws
    # ArgumentOutOfRangeException for anything but these vanilla keys
    for spec, wanted_key in CHARACTER_LABEL_KEYS.items():
        for k in counts[spec]:
            t = get_bp(c, k)
            label = specs_of(t).get("SimpleLabeledEntitySpec", {}).get("EntityNameLocKey") if t else None
            if label != wanted_key:
                R.error("%s: %s SimpleLabeledEntitySpec.EntityNameLocKey is %s; must be %s or the Population "
                        "batch-control tab throws" % (where, c.keys.get(k, [k])[0], label, wanted_key))

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


# ------------------------------------------------------------------------------------------- v2: schema checks

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OPS = ("#append", "#remove", "#delete")
# blueprints read in every game: anything that is not a template (templates are read only through the active
# faction's collections). A custom spec here would throw for Folktails and Iron Teeth players too.
LOOSE_ASSET_KINDS = {
    "Timberborn.BlueprintSystem.BlueprintAsset": "blueprint",
    "UnityEngine.Sprite": "sprite",
    "UnityEngine.Texture2D": "texture",
    "UnityEngine.Texture": "texture",
    "Timberborn.AssetSystem.BinaryData": "binary",
}


def split_op(key):
    for op in OPS:
        if key.endswith(op):
            return key[:-len(op)], op
    return key, None


def load_schema(a, c):
    path = a.schema
    if not path:
        version = None
        vfile = os.path.join(a.game_data, "StreamingAssets", "VersionNumbers.json")
        if os.path.isfile(vfile):
            version = load_json(vfile).get("CurrentVersion")
        path = os.path.join(REPO, "schema", "%s.json" % version)
    if not os.path.isfile(path):
        R.error("schema %s not found: blueprint keys and fields cannot be checked. Write it with "
                "`dotnet run --project tools/schema -c Release`" % path)
        return None
    schema = load_json(path)
    schema["_origin"] = {k: "game" for k in schema["specs"]}
    for extra in a.mod_schema:
        x = load_json(extra)
        for k, v in x.get("specs", {}).items():
            if v.get("origin") == "mod" or k not in schema["specs"]:
                schema["specs"][k] = v
                schema["_origin"][k] = v.get("origin", "mod")
        schema["types"].update(x.get("types", {}))
        schema["enums"].update(x.get("enums", {}))
    schema["_byFullName"] = {v["fullName"]: v for v in schema["specs"].values() if "fullName" in v}
    R.info("schema: game %s, %d spec keys, %d nested types, %d enums (%s)"
           % (schema.get("gameVersion"), len(schema["specs"]), len(schema["types"]), len(schema["enums"]),
              os.path.relpath(path, REPO) if path.startswith(REPO) else path))
    return schema


def spec_def(c, key):
    s = c.schema["specs"].get(key)
    if s and "aliasOf" in s:
        s = c.schema["specs"].get(s["aliasOf"])
    return s


def suggest(word, options):
    m = difflib.get_close_matches(word, list(options), n=1, cutoff=0.75)
    return " (did you mean %s?)" % m[0] if m else ""


def check_schema(c):
    if not c.schema:
        return
    c.asset_refs = []
    for key, bp in sorted(c.mod_bp.items()):
        check_blueprint_obj(c, bp, c.keys[key][0], top=True)
    for key, bp in sorted(c.optional_bp.items()):
        check_blueprint_obj(c, bp, c.keys[key][0], top=True)


def check_blueprint_obj(c, obj, where, top=False):
    if not isinstance(obj, dict):
        R.error("%s: expected an object of specs" % where)
        return
    for key, val in obj.items():
        base, op = split_op(key)
        if base == "Children":
            if not isinstance(val, dict):
                R.error("%s: Children must be an object" % where)
                continue
            for child, cval in val.items():
                cw = "%s Children.%s" % (where, child)
                if "#nested" in child:
                    if not isinstance(cval, dict) or not isinstance(cval.get("BlueprintPath"), str):
                        R.error("%s: a #nested child needs a BlueprintPath string" % cw)
                        continue
                    c.asset_refs.append((cw + ".BlueprintPath", cval["BlueprintPath"],
                                         "Timberborn.BlueprintSystem.BlueprintAsset"))
                    if "Modification" in cval:
                        check_blueprint_obj(c, cval["Modification"], cw + ".Modification")
                    extra = set(cval) - {"BlueprintPath", "Modification"}
                    if extra:
                        R.error("%s: unknown keys in a #nested child: %s" % (cw, ", ".join(sorted(extra))))
                else:
                    check_blueprint_obj(c, cval, cw)
            continue
        spec = spec_def(c, base)
        if spec is None:
            R.error("%s: unknown spec key %s%s. The game throws 'No type found for key' when it reads this blueprint%s. "
                    "If it is a spec class of this mod's own code, pass --mod-schema (tools/schema --include <dll>)"
                    % (where, base, suggest(base, c.schema["specs"]),
                       " - and this blueprint is not a template, so it is read in every game"
                       if top and "TemplateSpec" not in obj else ""))
            continue
        if op == "#delete":
            continue
        if not isinstance(val, dict):
            R.error("%s %s: a spec must be an object, got %s" % (where, base, type(val).__name__))
            continue
        check_fields(c, val, spec.get("fields", {}), "%s %s" % (where, base))


def check_fields(c, obj, fields, where):
    for k, v in obj.items():
        base, op = split_op(k)
        f = fields.get(base)
        if f is None:
            R.error("%s: unknown field %s%s. The game ignores it silently, so the value never applies. Known fields: %s"
                    % (where, base, suggest(base, fields), ", ".join(sorted(fields)) or "none"))
            continue
        if op == "#delete":
            continue
        t = f["type"]
        if op in ("#append", "#remove"):
            if t["kind"] != "array":
                R.error("%s.%s: %s only works on arrays; this field is %s" % (where, base, op, t["kind"]))
                continue
        check_value(c, v, t, "%s.%s" % (where, base))


INT_KINDS = {"vector2int": ("X", "Y"), "vector3int": ("X", "Y", "Z")}
FLOAT_KINDS = {"vector2": ("X", "Y"), "vector3": ("X", "Y", "Z"), "quaternion": ("X", "Y", "Z", "W"),
               "color": ("r", "g", "b", "a")}


def check_value(c, v, t, where):
    kind = t["kind"]
    if kind == "nullable":
        if v is not None:
            check_value(c, v, t["inner"], where)
        return
    if kind == "array":
        if not isinstance(v, list):
            R.error("%s: expected an array, got %s" % (where, jtype(v)))
            return
        for i, x in enumerate(v):
            check_value(c, x, t["element"], "%s[%d]" % (where, i))
        return
    if kind == "int":
        if isinstance(v, bool) or not isinstance(v, (int, float, str)):
            R.error("%s: expected an integer, got %s" % (where, jtype(v)))
        elif isinstance(v, float):
            R.error("%s: expected an integer, got %r (the game rounds it silently)" % (where, v))
        elif isinstance(v, str):
            R.warn("%s: integer written as a string %r" % (where, v))
        return
    if kind == "float":
        if isinstance(v, bool) or not isinstance(v, (int, float, str)):
            R.error("%s: expected a number, got %s" % (where, jtype(v)))
        elif isinstance(v, str):
            R.warn("%s: number written as a string %r" % (where, v))
        return
    if kind == "bool":
        if not isinstance(v, bool):
            R.error("%s: expected true or false, got %s" % (where, jtype(v)))
        return
    if kind in ("string", "guid"):
        if v is not None and not isinstance(v, str):
            R.error("%s: expected a string, got %s" % (where, jtype(v)))
        return
    if kind == "char":
        if not isinstance(v, str) or len(v) != 1:
            R.error("%s: expected a one-character string, got %r" % (where, v))
        return
    if kind == "enum":
        e = c.schema["enums"].get(t["enum"])
        if not isinstance(v, str):
            R.error("%s: expected an enum name (%s), got %s" % (where, t["enum"], jtype(v)))
            return
        if not e:
            R.unchecked.add("%s: enum %s not in the schema" % (where, t["enum"]))
            return
        names = [x["name"] for x in e["values"]]
        parts = [p.strip() for p in v.split(",")] if e.get("flags") else [v]
        for p in parts:
            if p not in names:
                R.error("%s: %r is not a value of %s%s. Values: %s"
                        % (where, p, t["enum"].rsplit(".", 1)[-1], suggest(p, names), ", ".join(names)))
        return
    if kind in INT_KINDS or kind in FLOAT_KINDS:
        keys = INT_KINDS.get(kind) or FLOAT_KINDS[kind]
        if not isinstance(v, dict):
            R.error("%s: expected an object with %s, got %s" % (where, ", ".join(keys), jtype(v)))
            return
        missing = [k for k in keys if k not in v]
        extra = [k for k in v if k not in keys]
        if missing or extra:
            R.error("%s: %s needs exactly the keys %s (missing %s, unknown %s); a missing key throws"
                    % (where, kind, ", ".join(keys), missing or "none", extra or "none"))
        for k in keys:
            x = v.get(k)
            if k in v and (isinstance(x, bool) or not isinstance(x, (int, float))
                           or (kind in INT_KINDS and isinstance(x, float))):
                R.error("%s.%s: expected %s, got %r" % (where, k, "an integer" if kind in INT_KINDS else "a number", x))
        return
    if kind == "assetref":
        if v is None or v == "":
            return
        if not isinstance(v, str):
            R.error("%s: expected an asset path string, got %s" % (where, jtype(v)))
            return
        c.asset_refs.append((where, v, t["asset"]))
        return
    if kind == "object":
        if not isinstance(v, dict):
            R.error("%s: expected an object (%s), got %s" % (where, t["type"].rsplit(".", 1)[-1], jtype(v)))
            return
        td = c.schema["types"].get(t["type"]) or c.schema["_byFullName"].get(t["type"])
        if td is None:
            R.unchecked.add("%s: type %s not in the schema" % (where, t["type"]))
            return
        check_fields(c, v, td.get("fields", {}), where)
        return
    if kind == "serializedobject":
        if not isinstance(v, dict):
            R.error("%s: expected an object, got %s" % (where, jtype(v)))
        return
    if kind == "unsupported":
        R.error("%s: the game cannot deserialise this field (%s); remove it" % (where, t.get("clr")))
        return
    R.unchecked.add("%s: field kind %s" % (where, kind))


def jtype(v):
    return {dict: "an object", list: "an array", str: "a string", bool: "a boolean", int: "an integer",
            float: "a number", type(None): "null"}.get(type(v), type(v).__name__)


def check_asset_refs(c):
    """Every typed asset reference the schema found: forward slashes, exact case, the right kind of file."""
    has_bundles = any(r.lower().startswith("assetbundles/") for r in c.files)
    for where, value, asset in getattr(c, "asset_refs", []):
        if "\\" in value:
            R.error("%s: %s uses a backslash; asset paths use forward slashes" % (where, value))
            continue
        k = ref_key(value)
        kind = LOOSE_ASSET_KINDS.get(asset)
        if k in c.keys:
            rel = c.keys[k][0]
            stem = rel[:-len(".json")] if rel.endswith(".blueprint.json") else os.path.splitext(rel)[0]
            if stem != value.lstrip("/"):
                R.error("%s: %s differs in case from the file %s; use the exact case (Mac file systems and the "
                        "id rules expect it)" % (where, value, rel))
            if kind is None:
                R.error("%s: %s is a loose file, but a %s only loads from an asset bundle"
                        % (where, value, asset.rsplit(".", 1)[-1]))
            elif kind == "blueprint" and not rel.endswith(".blueprint.json"):
                R.error("%s: %s is not a blueprint" % (where, value))
            elif kind in ("sprite", "texture"):
                resolve(c, value, where, kind)
            elif kind == "binary" and rel.lower().endswith((".png", ".jpg", ".json")):
                R.error("%s: %s should be a binary asset (e.g. .timbermesh), not %s" % (where, value, rel))
            continue
        if k in c.vbp or (c.res is not None and k in c.res):
            continue
        if c.res is None:
            R.unchecked.add("%s -> %s (no resource index)" % (where, value))
        elif kind is None and has_bundles:
            # a prefab, material or other bundle-only asset: it must be inside one of the staged bundles, or the game
            # throws at load (a dev copy without pandabornattachments crashed every game, 2026-11-14)
            inside = mod_bundle_assets(c)
            if inside is None:
                R.unchecked.add("%s -> %s (%s, may be in one of the mod's asset bundles)" % (where, value, asset))
            elif k not in inside:
                R.error("%s: %s (%s) is in none of the mod's asset bundles (%s): ship the bundle that holds it"
                        % (where, value, asset, ", ".join(sorted(r.rsplit("/", 1)[-1] for r in c.files
                                                                  if r.lower().startswith("assetbundles/")
                                                                  and r.lower().endswith("_win"))) or "none"))
        else:
            R.error("%s: %s does not resolve to a mod file or a game asset" % (where, value))


def global_blueprints(c):
    """(rel, bp, why) for every mod blueprint the game reads in every game, or reads into vanilla blueprints."""
    for key, bp in c.mod_bp.items():
        if "TemplateSpec" not in bp:
            yield c.keys[key][0], bp, "indexed and read in every game"
    for key, bp in c.optional_bp.items():
        yield c.keys[key][0], bp, "merged into a vanilla blueprint (faction modifier or optional merge)"


def check_global_specs(c):
    if not c.schema:
        return
    for rel, bp, why in global_blueprints(c):
        for key in bp:
            base, _ = split_op(key)
            if base != "Children" and c.schema["_origin"].get(base, "game") != "game":
                R.error("%s: custom spec %s in a blueprint that is %s. If the mod's code is missing or fails to load, "
                        "every game throws. Custom specs belong only in templates listed in the faction's own "
                        "collections (docs/ENGINEERING.md, data rule 1)" % (rel, base, why))


def vanilla_ids(c, spec):
    out = {}
    for key, s in all_vanilla_specs(c, spec):
        out[s.get("Id")] = key
        for b in s.get("BackwardCompatibleIds") or []:
            out[b] = key
    return out


def check_unique_ids(c):
    for spec in ("GoodSpec", "NeedSpec", "RecipeSpec", "NeedGroupSpec", "WorkerTypeSpec", "ToolGroupSpec",
                 "BonusTypeSpec", "GoodGroupSpec"):
        vids = vanilla_ids(c, spec)
        seen = {}
        for key, bp in sorted(c.mod_bp.items()):
            s = bp.get(spec)
            if not s:
                continue
            rel = c.keys[key][0]
            for i in [s.get("Id")] + list(s.get("BackwardCompatibleIds") or []):
                if i in vids:
                    R.error("%s: %s id %s is also a vanilla id (%s); the game throws on duplicates"
                            % (rel, spec, i, vids[i]))
                if i in seen:
                    R.error("%s: %s id %s is also defined in %s" % (rel, spec, i, seen[i]))
                seen[i] = rel
    if c.schema:
        game = {k for k, o in c.schema["_origin"].items() if o == "game"}
        for k, o in c.schema["_origin"].items():
            if o != "game":
                spec = c.schema["specs"][k]
                if k in game:
                    R.error("mod spec class %s has the same simple name as a game spec; SpecTypeCache throws" % k)
                if c.profile == "pandaborn" and not k.startswith("Pandaborn"):
                    R.error("mod spec class %s (%s) must be named Pandaborn...Spec" % (k, spec.get("fullName")))


def check_needs(c):
    """Mirror of the game's NeedVerifier (it runs in every game) plus our rule: every need of this mod sits in a need
    collection one of the mod's factions lists."""
    needs = {}
    for key, s in all_vanilla_specs(c, "NeedSpec"):
        needs[s.get("Id")] = ("vanilla", s)
    for key, bp in c.mod_bp.items():
        if "NeedSpec" in bp:
            needs[bp["NeedSpec"].get("Id")] = (c.keys[key][0], bp["NeedSpec"])
    colls = []  # (where, spec)
    for key, s in all_vanilla_specs(c, "NeedCollectionSpec"):
        colls.append(("vanilla " + key, s))
    for key, bp in c.mod_bp.items():
        if "NeedCollectionSpec" in bp:
            colls.append((c.keys[key][0], bp["NeedCollectionSpec"]))
    factions = [s for _, s in all_vanilla_specs(c, "FactionSpec")] + [b["FactionSpec"] for b in c.factions.values()]
    groups = {s.get("Id") for _, s in all_vanilla_specs(c, "NeedGroupSpec")}
    groups |= {bp["NeedGroupSpec"].get("Id") for bp in c.mod_bp.values() if "NeedGroupSpec" in bp}
    used_ids = set()
    for f in factions:
        used_ids.update(f.get("NeedCollectionIds") or [])
    for nid, (where, s) in sorted(needs.items(), key=lambda x: str(x[0])):
        if not any(nid in (cs.get("Needs") or []) for _, cs in colls):
            R.error("%s: NeedSpec %s is in no need collection; NeedVerifier throws in every game" % (where, nid))
        if s.get("NeedGroupId") not in groups:
            R.error("%s: NeedSpec %s has NeedGroupId %s, which does not exist; NeedVerifier throws in every game"
                    % (where, nid, s.get("NeedGroupId")))
    for where, cs in colls:
        cid = cs.get("CollectionId")
        if cid != "Common" and cid not in used_ids:
            R.error("%s: need collection %s is used by no faction; NeedVerifier throws in every game" % (where, cid))
        for n in cs.get("Needs") or []:
            if n not in needs:
                R.error("%s: need collection %s lists need %s, which does not exist; NeedVerifier throws in every game"
                        % (where, cid, n))
    mod_fac_colls = {"Common"}
    for b in c.factions.values():
        mod_fac_colls.update(b["FactionSpec"].get("NeedCollectionIds") or [])
    for nid, (where, s) in needs.items():
        if where == "vanilla" or not c.factions:
            continue
        if not any(nid in (cs.get("Needs") or []) and cs.get("CollectionId") in mod_fac_colls for _, cs in colls):
            R.error("%s: need %s is not in a need collection this mod's faction always lists (ENGINEERING data rule 4)"
                    % (where, nid))


def faction_templates(c, fs):
    out = []
    for cid in list(fs.get("TemplateCollectionIds", [])) + ["Common"]:
        for src, tcs in collection_members(c, "TemplateCollectionSpec", cid):
            for b in tcs.get("Blueprints", []):
                t = get_bp(c, ref_key(b))
                if t is not None:
                    out.append((b, t))
    return out


def check_faction_goods(c, fid, bp):
    """GoodService.GetGood throws for a good outside the active faction's good collections, and a missing recipe id
    throws when the building's panel or manufactory reads it."""
    fs = bp["FactionSpec"]
    goods = set()
    for cid in list(fs.get("GoodCollectionIds", [])) + ["Common"]:
        for _, gcs in collection_members(c, "GoodCollectionSpec", cid):
            goods.update(gcs.get("Goods") or [])
    if not goods:
        return
    recipes = {}
    for key, s in all_vanilla_specs(c, "RecipeSpec"):
        recipes[s.get("Id")] = s
    for key, b in c.mod_bp.items():
        if "RecipeSpec" in b:
            recipes[b["RecipeSpec"].get("Id")] = b["RecipeSpec"]
    for path, t in faction_templates(c, fs):
        sp = specs_of(t)
        name = (sp.get("TemplateSpec") or {}).get("TemplateName", path)
        for cost in (sp.get("BuildingSpec") or {}).get("BuildingCost") or []:
            if cost.get("Id") not in goods:
                R.error("Faction %s: %s costs %s, which is not in the faction's good collections (%s); placing it "
                        "throws in an %s game" % (fid, name, cost.get("Id"), ", ".join(fs.get("GoodCollectionIds", [])),
                                                    fid))
        for where_, gid in goods_used_by(t):
            if gid not in goods:
                R.error("Faction %s: %s uses good %s (%s), which is not in the faction's good collections (%s)"
                        % (fid, name, gid, where_, ", ".join(fs.get("GoodCollectionIds", []))))
        for rid in (sp.get("ManufactorySpec") or {}).get("ProductionRecipeIds") or []:
            r = recipes.get(rid)
            if r is None:
                R.error("Faction %s: %s uses recipe %s, which does not exist" % (fid, name, rid))
                continue
            used = [g.get("Id") for g in (r.get("Ingredients") or []) + (r.get("Products") or [])]
            if r.get("Fuel"):
                used.append(r["Fuel"])
            for g in used:
                if g and g not in goods:
                    R.error("Faction %s: %s recipe %s uses %s, which is not in the faction's good collections"
                            % (fid, name, rid, g))


def goods_used_by(bp):
    """Goods a template names outside its cost and recipes: consumed supplies (GoodId) and plant or tree yields."""
    out = []

    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "GoodId" and isinstance(v, str) and v:
                    out.append((path + "." + k, v))
                elif k == "Yield" and isinstance(v, dict) and isinstance(v.get("Id"), str):
                    out.append((path + ".Yield", v["Id"]))
                else:
                    walk(v, path + "." + k if path else k)
        elif isinstance(o, list):
            for x in o:
                walk(x, path)
    walk(bp, "")
    return out


def check_material_coverage(c, fid, bp):
    fs = bp["FactionSpec"]
    mats = fs.get("MaterialCollectionIds") or []
    if "Folktails" in mats or "IronTeeth" in mats:
        return
    uses_vanilla_models = any("Folktails" in str(m) for _, t in faction_templates(c, fs)
                              for _, m in walk_strings(t) if m.endswith(".Model"))
    if not uses_vanilla_models:
        return
    need = set()
    for _, mcs in collection_members(c, "MaterialCollectionSpec", "Folktails"):
        need.update(m.replace("\\", "/").rsplit("/", 1)[-1] for m in mcs.get("Materials", []))
    have = set()
    for cid in mats + ["Common"]:
        for _, mcs in collection_members(c, "MaterialCollectionSpec", cid):
            have.update(m.replace("\\", "/").rsplit("/", 1)[-1] for m in mcs.get("Materials", []))
    missing = sorted(need - have)
    if missing:
        R.error("Faction %s drops the Folktails material collection but uses Folktails models; %d Folktails materials "
                "have no same-named material in its collections (placing such a building throws 'Material not "
                "found'): %s" % (fid, len(missing), ", ".join(missing[:20]) + (" ..." if len(missing) > 20 else "")))


# bundles whose file name is fixed by a recorded decision (docs/ENGINEERING.md asks for pandabornfactions*)
BUNDLE_NAME_EXCEPTIONS = {"pandabornlook": "docs/tech/look.md (the Look module loads its materials from this bundle)",
                          "pandabornplants": "docs/tech/plants.md (never renamed: look.md problem 10)",
                          "pandabornsounds": "docs/tech/sound.md (built and checked under this name)",
                          "pandabornattachments": "docs/tech/ringtail-body.md 7.3 (planned: hats and baskets)"}


def check_bundles(c):
    bundles = {}
    for rel in c.files:
        low = rel.lower()
        if not low.startswith("assetbundles/") or low.endswith((".manifest", ".meta", ".json", ".txt")):
            continue
        name = rel.rsplit("/", 1)[-1]
        m = re.match(r"^(.*)_(win|mac)$", name)
        if not m:
            R.warn("%s: asset bundle without _win/_mac suffix loads on both platforms; build both platforms instead"
                   % rel)
            continue
        bundles.setdefault(m.group(1), set()).add(m.group(2))
        if c.profile == "pandaborn" and not m.group(1).lower().startswith("pandabornfactions"):
            if m.group(1).lower() in BUNDLE_NAME_EXCEPTIONS:
                R.info("%s: bundle name kept by decision: %s" % (rel, BUNDLE_NAME_EXCEPTIONS[m.group(1).lower()]))
            else:
                R.error("%s: bundle names must start with pandabornfactions (distinct from the Reskin's)" % rel)
    for base, plats in sorted(bundles.items()):
        for p in ("win", "mac"):
            if p not in plats:
                msg = "asset bundle %s has no _%s build; every bundle ships as a _win/_mac pair" % (base, p)
                if p == "mac" and not c.args.release:
                    # dev builds may lack the Mac twin until Mac bundle builds exist; a release (--release, the
                    # package stage) may not
                    R.warn(msg + " (allowed for a dev build; the package stage refuses it)")
                else:
                    R.error(msg)


def produced_ids(c):
    out = {k: set() for k in ("faction", "template", "template_alias", "collection", "good", "need", "need_group",
                              "recipe", "worker_type", "tool_group", "tutorial")}
    for key, bp in c.mod_bp.items():
        ts = bp.get("TemplateSpec")
        if ts:
            out["template"].add(ts.get("TemplateName"))
            out["template_alias"].update(ts.get("BackwardCompatibleTemplateNames") or [])
        for spec, kind in (("FactionSpec", "faction"), ("GoodSpec", "good"), ("NeedSpec", "need"),
                           ("NeedGroupSpec", "need_group"), ("RecipeSpec", "recipe"), ("WorkerTypeSpec", "worker_type"),
                           ("BlockObjectToolGroupSpec", "tool_group"), ("TutorialSpec", "tutorial"),
                           ("TutorialStageSpec", "tutorial")):
            if spec in bp:
                out[kind].add(bp[spec].get("Id"))
                if kind in ("good", "need", "recipe"):
                    out[kind].update(bp[spec].get("BackwardCompatibleIds") or [])
        for spec in ("TemplateCollectionSpec", "MaterialCollectionSpec", "NeedCollectionSpec", "GoodCollectionSpec"):
            if spec in bp:
                out["collection"].add(bp[spec].get("CollectionId"))
    return out


def check_lock(c):
    if c.profile != "pandaborn" or c.args.no_lock:
        return
    path = c.args.lock or os.path.join(REPO, "catalogue", "ids.lock.json")
    if not os.path.isfile(path):
        R.error("id lock %s not found (generate with src/gen/generate.py --lock)" % path)
        return
    lock = load_json(path)
    ids = lock.get("ids", {})
    prod = produced_ids(c)
    for kind, values in prod.items():
        for v in sorted(x for x in values if x):
            if v not in ids.get(kind, {}):
                R.error("%s id %s is not in catalogue/ids.lock.json: ids are frozen once shipped, so every id must be "
                        "registered (src/gen/generate.py --lock)" % (kind, v))
    aliases = prod["template_alias"]
    for kind, entries in ids.items():
        for v, meta in entries.items():
            if meta.get("retired") or meta.get("external") or meta.get("gatedBy"):
                continue
            if v not in prod.get(kind, set()) and not (kind == "template" and v in aliases):
                R.error("locked %s id %s is no longer produced: saves that contain it lose it. Keep it, or give its "
                        "replacement an alias and mark it retired in the lock" % (kind, v))
    try:
        rel = os.path.relpath(path, REPO).replace("\\", "/")
        r = subprocess.run(["git", "-C", REPO, "show", "HEAD:" + rel], capture_output=True, timeout=30)
        old = json.loads(r.stdout.decode("utf-8-sig")) if r.returncode == 0 else None
    except (OSError, ValueError, subprocess.TimeoutExpired):
        old = None
    if old is None:
        R.info("id lock: no committed version to compare with (append-only check skipped)")
        return
    for kind, entries in old.get("ids", {}).items():
        for v, meta in entries.items():
            cur = ids.get(kind, {}).get(v)
            if cur is None:
                R.error("catalogue/ids.lock.json: %s id %s was removed since the last commit; the lock is append-only"
                        % (kind, v))
            elif cur.get("since") != meta.get("since"):
                R.error("catalogue/ids.lock.json: %s id %s changed since the last commit" % (kind, v))
    R.info("id lock: %d ids, append-only vs HEAD ok" % sum(len(e) for e in ids.values()))



# ------------------------------------------------------------------------------- v2: adopted models (art lanes)

MODEL_PREFIXES = {"buildings/pandaborn/models/": ("art", "models"), "naturalresources/pandaborn/models/": ("art", "plants")}


def model_of(path):
    low = path.replace("\\", "/").lower()
    for prefix, root in MODEL_PREFIXES.items():
        if low.startswith(prefix):
            rest = path.replace("\\", "/")[len(prefix):]
            return root, rest.split("/", 1)[0]
    return None, None


def blueprint_meshes(bp, path=""):
    """(child path, model asset path) for every TimbermeshSpec in a blueprint."""
    for k, v in bp.items():
        if k == "Children" and isinstance(v, dict):
            for child, node in v.items():
                if isinstance(node, dict):
                    yield from blueprint_meshes(node, path + "/" + child)
        elif k == "TimbermeshSpec" and isinstance(v, dict) and v.get("Model"):
            yield path, v["Model"]


def check_models(c):
    """A blueprint that uses a model from the art lanes must agree with that model's model.json (footprint, blocks,
    entrance, access, construction base and stage order, attachments) and with the mesh itself (slot nodes for every
    slot keyword, animated nodes and their driver specs)."""
    checked = 0
    for key, bp in sorted(c.mod_bp.items()):
        rel = c.keys[key][0]
        meshes = list(blueprint_meshes(bp))
        ids = {model_of(m)[1]: model_of(m)[0] for _, m in meshes if model_of(m)[1]}
        for mid, root in ids.items():
            mj_path = os.path.join(REPO, root[0], root[1], mid, "model.json")
            if not os.path.isfile(mj_path):
                R.error("%s: uses model %s but %s does not exist" % (rel, mid, mj_path))
                continue
            mj = load_json(mj_path)
            checked += 1
            where = "%s (model %s)" % (rel, mid)
            bos = bp.get("BlockObjectSpec") or {}
            size = mj.get("size") or {}
            if bos.get("Size") != {"X": size.get("X"), "Y": size.get("Y"), "Z": size.get("Z")}:
                R.error("%s: BlockObjectSpec.Size %s differs from model.json size %s" % (where, bos.get("Size"), size))
            if mj.get("blocks") and bos.get("Blocks") != mj["blocks"]:
                def _no_occ(bl):
                    return [{k: v for k, v in x.items() if k != "Occupations"} for x in bl or []]
                if _no_occ(bos.get("Blocks")) == _no_occ(mj["blocks"]):
                    # the catalogue sets occupations on purpose (a flume leaves its corners free for a bridge span)
                    R.info("%s: block occupations set by the catalogue, differ from model.json" % where)
                else:
                    R.error("%s: BlockObjectSpec.Blocks differ from model.json blocks" % where)
            if mj.get("entrance"):
                e = (bos.get("Entrance") or {})
                if not e.get("HasEntrance") or e.get("Coordinates") != mj["entrance"]:
                    R.error("%s: entrance %s differs from model.json %s" % (where, e, mj["entrance"]))
            if mj.get("access"):
                la = (bp.get("BuildingAccessibleSpec") or {}).get("LocalAccess")
                if la != mj["access"]:
                    R.error("%s: LocalAccess %s differs from model.json access %s (colonists would vanish away from "
                            "the door)" % (where, la, mj["access"]))
            unf = ((bp.get("Children") or {}).get("#Unfinished") or {}).get("Children") or {}
            if unf:
                names = list(unf)
                bases = [n for n in names if "ConstructionBase" in n]
                if len(bases) != 1 or not names[0].startswith("ConstructionBase"):
                    R.error("%s: #Unfinished must hold exactly one ConstructionBase as its first child (models.md), "
                            "has %s" % (where, names))
                if mj.get("models", {}).get("constructionStage0") and "ConstructionStage0" not in names:
                    R.error("%s: model has a construction stage but #Unfinished has no ConstructionStage0" % where)
            for a in mj.get("attachments") or []:
                hits = [at for at in (bp.get("TemplateAttachmentsSpec") or {}).get("Attachments", [])
                        if at.get("AttachmentId") == a.get("AttachmentId")]
                # no hit: the basis has no such effect and the generator left it out (it says so in its report)
                if hits and any(at.get("Position") != a.get("Position") for at in hits):
                    R.error("%s: attachment %s is not at the model's position %s" % (where, a.get("AttachmentId"),
                                                                                       a.get("Position")))
            # the mesh: slot nodes for every slot keyword; animated nodes and their drivers
            # slots may sit in any of the model's meshes (the Sky Lantern's builders' slots are in its construction
            # stage, models.md pass 3)
            fin = [m for child, m in meshes if model_of(m)[1] == mid]
            nodes = set()
            finished_animated = None   # None: the finished mesh was not read
            for child, m in meshes:
                if model_of(m)[1] != mid or ref_key(m) not in c.keys:
                    continue
                try:
                    _, mesh_nodes = read_timbermesh(c.files[c.keys[ref_key(m)][0]])
                except Exception:  # noqa: BLE001
                    continue   # reported below
                if child.startswith("/#Finished"):
                    finished_animated = bool(finished_animated) or any(n["nodeAnimations"] for n in mesh_nodes)
            for m in fin:
                if ref_key(m) in c.keys:
                    try:
                        _, mesh_nodes = read_timbermesh(c.files[c.keys[ref_key(m)][0]])
                        nodes |= {n["name"] for n in mesh_nodes}
                    except Exception as ex:  # noqa: BLE001
                        R.error("%s: cannot read %s: %s" % (where, m, ex))
                else:
                    R.unchecked.add("%s: mesh %s not in this folder (assemble copies it)" % (where, m))
            if nodes:
                # every node a spec of the building looks up by name ("#Name": progress steps, animated parts, particle
                # and sound emitters, lights...) must be in the adopted model: a missing one throws "Child ... not
                # found" when the building is created and crashes the game (OxWorkshop, 2026-11-14). Children and
                # attachment parents are blueprint nodes, not mesh nodes.
                wanted, child_names = set(), set()
                hash_names(dict((k, v) for k, v in bp.items() if k not in NODE_CHECK_SKIP), wanted)
                child_keys(bp.get("Children") or {}, child_names)
                for n in sorted(wanted - nodes - child_names):
                    R.error("%s: a spec looks up node %s, which the model's meshes lack (\"Child not found\" crashes the "
                            "game): add the node to the model or drop the spec with removeSpecs" % (where, n))
                # controllers that take the model's IAnimator (GetComponentInChildren<IAnimator>) throw without an
                # animated node (Smoke Kiln, 2026-11-14); a wonder gets its animation controller from WonderSpec
                needs_animator = [k for k in ANIMATOR_SPECS if k in bp]
                if "WonderSpec" in bp:
                    needs_animator.append("WonderSpec (its WonderAnimationController)")
                if needs_animator and finished_animated is False:
                    R.error("%s: %s needs an animated node in the finished model and the model has none (it throws "
                            "when the building is finished and on every speed change)" % (where, ", ".join(needs_animator)))
                for slot in (bp.get("TransformSlotInitializerSpec") or {}).get("Slots", []):
                    kw = slot.get("SlotKeyword")
                    if kw and not any(n.startswith("#Slot#" + kw) for n in nodes):
                        R.error("%s: slot keyword %s has no #Slot#%s node in the mesh (colonists would sit at the "
                                "origin)" % (where, kw, kw))
                for an in mj.get("animatedNodes") or []:
                    if an.get("node") not in nodes:
                        R.error("%s: animated node %s is not in the mesh" % (where, an.get("node")))
                    driver = [an["driver"]] if an.get("driver") else re.findall(r"([A-Z][A-Za-z]+Spec)",
                                                                                     an.get("drivenBy") or "")
                    if driver and driver[0] not in bp and DECORATOR_DRIVERS.get(driver[0]) not in bp:
                        R.error("%s: animated node %s is driven by %s, which the blueprint lacks (it would never move)"
                                % (where, an.get("node"), driver[0]))
    if checked:
        R.info("models: %d blueprint(s) checked against their model.json" % checked)


# ------------------------------------------------------------------------- v2: the faction's economy and honesty
# "Nothing in the toolbar lies" (docs/DESIGN.md, Quality bar). Errors with --release, warnings in dev builds.

# module -> spec (or bundle) whose presence means "this module's data ships"
MODULE_DATA = {"Bell": ("spec", "PandabornBellSpec"), "Names": ("spec", "PandabornNamePoolSpec"),
               "Look": ("bundle", "pandabornlook"), "Water": ("spec", "PandabornFlumeSegmentSpec"),
               "Ringtails": ("spec", "PandabornRingtailsSpec"), "RingtailsFallback": ("spec", "PandabornNightPostSpec"),
               "Festival": ("spec", "PandabornFestivalSpec"), "Flowering": ("spec", "PandabornFloweringSpec")}
SELF_CONTAINED_MODULES = {"Words"}   # ship their own data with the code
DWELLING_NEEDS = ("Sleep", "Shelter")
TUTORIAL_TEMPLATE_FIELDS = ("TemplateName", "TemplateNames", "HighlightableBuildingIds")
# BuildingModelSpec names are blueprint children or optional (FindChildIfNameNotEmpty): src/pipeline/kit/check_nodes.py
NODE_CHECK_SKIP = {"Children", "TemplateAttachmentsSpec", "WaterInputPipeSpec", "BuildingModelSpec"}
ANIMATOR_SPECS = ("WorkshopAnimationControllerSpec", "EnterableAnimationControllerSpec", "WonderAnimationControllerSpec")


def hash_names(o, out):
    if isinstance(o, dict):
        for v in o.values():
            hash_names(v, out)
    elif isinstance(o, list):
        for v in o:
            hash_names(v, out)
    elif isinstance(o, str) and o.startswith("#") and len(o) > 1:
        out.add(o)


def child_keys(children, out):
    for k, v in children.items():
        out.add(k.split("#nested")[0] if k.endswith("#nested") else k)
        if isinstance(v, dict) and isinstance(v.get("Children"), dict):
            child_keys(v["Children"], out)


# components the game adds by itself to every entity with the given spec (decorators, no spec of their own)
DECORATOR_DRIVERS = {"WonderAnimationControllerSpec": "WonderSpec"}
# vanilla template names a tutorial faction must answer to (StairsUnlockedTrigger asks for Stairs.Folktails by name in
# any faction with StartingFactionSpec; docs/tech/tutorial.md): an alias for one of them is required, not a clash
TUTORIAL_ALIASES = {"Stairs.Folktails"}


def gate(c, msg):
    if c.args.release:
        R.error(msg)
    else:
        R.warn(msg + " (an error with --release)")


def walk_effects(obj):
    """(NeedId, points) of every effect-like object in a template (attractions, decorations, wonders...)."""
    if isinstance(obj, dict):
        if isinstance(obj.get("NeedId"), str):
            pts = obj.get("PointsPerHour", obj.get("Points", 0)) or 0
            yield obj["NeedId"], pts
        for k, v in obj.items():
            if k != "Children":
                yield from walk_effects(v)
    elif isinstance(obj, list):
        for x in obj:
            yield from walk_effects(x)


def faction_world(c, fs):
    """Everything an Inkpaws game can use: templates, goods, needs, recipes; producers, consumers, satisfiers."""
    w = Ctx()
    w.templates = []   # (path, bp)
    seen = set()
    for cid in list(fs.get("TemplateCollectionIds", [])) + ["Common"]:
        for _, tcs in collection_members(c, "TemplateCollectionSpec", cid):
            for b in tcs.get("Blueprints", []):
                k = ref_key(b)
                if k in seen:
                    continue
                seen.add(k)
                t = get_bp(c, k)
                if t is not None:
                    w.templates.append((b, t))
    w.goods = set()
    for cid in list(fs.get("GoodCollectionIds", [])) + ["Common"]:
        for _, g in collection_members(c, "GoodCollectionSpec", cid):
            w.goods.update(g.get("Goods") or [])
    w.own_goods = set()
    for cid in fs.get("GoodCollectionIds", []):
        for src, g in collection_members(c, "GoodCollectionSpec", cid):
            if not src.startswith("vanilla"):
                w.own_goods.update(g.get("Goods") or [])
    w.needs = set()
    for cid in list(fs.get("NeedCollectionIds", [])) + ["Common"]:
        for _, n in collection_members(c, "NeedCollectionSpec", cid):
            w.needs.update(n.get("Needs") or [])
    recipes = {s.get("Id"): s for _, s in all_vanilla_specs(c, "RecipeSpec")}
    for b in c.mod_bp.values():
        if "RecipeSpec" in b:
            recipes[b["RecipeSpec"].get("Id")] = b["RecipeSpec"]
    goodspecs = {s.get("Id"): s for _, s in all_vanilla_specs(c, "GoodSpec")}
    for b in c.mod_bp.values():
        if "GoodSpec" in b:
            goodspecs[b["GoodSpec"].get("Id")] = b["GoodSpec"]
    w.producers, w.consumers, w.satisfiers = {}, {}, {}
    w.yields, w.removers = [], set()

    def add(table, key, who):
        table.setdefault(key, []).append(who)
    for path, t in w.templates:
        sp = specs_of(t)
        name = (sp.get("TemplateSpec") or {}).get("TemplateName", path)
        for cost in (sp.get("BuildingSpec") or {}).get("BuildingCost") or []:
            add(w.consumers, cost.get("Id"), name + " (cost)")
        for rid in (sp.get("ManufactorySpec") or {}).get("ProductionRecipeIds") or []:
            r = recipes.get(rid) or {}
            for g in r.get("Ingredients") or []:
                add(w.consumers, g.get("Id"), "%s:%s" % (name, rid))
            if r.get("Fuel"):
                add(w.consumers, r["Fuel"], "%s:%s (fuel)" % (name, rid))
            for g in r.get("Products") or []:
                add(w.producers, g.get("Id"), "%s:%s" % (name, rid))
        for g in (sp.get("GoodConsumingBuildingSpec") or {}).get("ConsumedGoods") or []:
            add(w.consumers, g.get("GoodId"), name + " (upkeep)")
        for g in (sp.get("WonderInventorySpec") or {}).get("RequiredGoods") or []:
            add(w.consumers, g.get("Id"), name + " (launch)")
        for ys in ("CuttableSpec", "GatherableSpec"):
            yielder = (sp.get(ys) or {}).get("Yielder") or {}
            y = yielder.get("Yield") or {}
            if y.get("Id"):
                # a yield counts only if a building of the faction removes yields of that group (a pine's resin needs
                # a tapper, which the Inkpaws do not have)
                w.yields.append((y["Id"], yielder.get("ResourceGroup"), "%s (%s)" % (name, ys[:-4].lower())))
        group = (sp.get("YieldRemovingBuildingSpec") or {}).get("ResourceGroup")
        if group:
            w.removers.add(group)
        for spec in ("FireworkLauncherSpec",):
            if spec in sp:
                add(w.consumers, "Fireworks", name)
        if "DwellingSpec" in sp:
            for n in DWELLING_NEEDS:
                add(w.satisfiers, n, name + " (home)")
        for k, v in sp.items():
            if k in ("WorkshopRandomNeedApplierSpec", "YieldRemoverWorkplaceEffectsSpec"):
                continue
            if k.startswith("Pandaborn") and isinstance(v, dict):
                # our own code raises needs it names (the festival's FestiveNeedId, GrandNeedId)
                for fk, fv in v.items():
                    if fk.endswith("NeedId") and isinstance(fv, str) and fv:
                        add(w.satisfiers, fv, "%s (%s, code)" % (name, k))
            for nid, pts in walk_effects(v):
                if pts and pts > 0:
                    add(w.satisfiers, nid, "%s (%s)" % (name, k))
    for gid, group, who in w.yields:
        if group in w.removers:
            add(w.producers, gid, who)
    for gid in w.goods:
        gs = goodspecs.get(gid) or {}
        for e in gs.get("ConsumptionEffects") or []:
            if e.get("NeedId") in w.needs and (e.get("Points") or 0) > 0:
                add(w.consumers, gid, "colonists (%s)" % e["NeedId"])
                if gid in w.producers:
                    add(w.satisfiers, e["NeedId"], "good " + gid)
    return w


def check_economy(c, fid, bp):
    fs = bp["FactionSpec"]
    w = faction_world(c, fs)
    report = {"needsWithoutSatisfier": [], "goodsWithoutSource": [], "goodsWithoutUse": [], "toolClashes": []}
    for n in sorted(w.needs):
        if not w.satisfiers.get(n):
            report["needsWithoutSatisfier"].append(n)
            gate(c, "Faction %s: need %s is in the faction's collections but nothing the faction has can satisfy it "
                    "(no good, attraction, decoration or home raises it)" % (fid, n))
    for g in sorted(w.consumers):
        if g and not w.producers.get(g) and g not in ("Water", "Badwater"):
            uses = [u for u in w.consumers[g] if not u.startswith("colonists")]
            if uses:
                report["goodsWithoutSource"].append(g)
                gate(c, "Faction %s: %s is needed (%s) but nothing the faction has produces or gathers it"
                        % (fid, g, "; ".join(uses[:4])))
    for g in sorted(w.own_goods):
        if not w.consumers.get(g):
            report["goodsWithoutUse"].append(g)
            gate(c, "Faction %s: good %s has no use: no cost, recipe, upkeep, launch or need consumes it" % (fid, g))
    slots = {}
    for path, t in w.templates:
        sp = specs_of(t)
        pb = sp.get("PlaceableBlockObjectSpec")
        if not pb or pb.get("DevModeTool") or "BuildingSpec" not in sp:
            continue
        key = (pb.get("ToolGroupId"), pb.get("ToolOrder"))
        name = (sp.get("TemplateSpec") or {}).get("TemplateName", path)
        if key in slots:
            report["toolClashes"].append([slots[key], name, key[0], key[1]])
            gate(c, "Faction %s: %s and %s share tool group %s order %s (the toolbar order is ambiguous)"
                    % (fid, slots[key], name, key[0], key[1]))
        else:
            slots[key] = name
    c.economy = report
    R.info("Faction %s economy: %d needs, %d goods, %d templates; %d unmet needs, %d unsourced goods, %d unused goods, "
           "%d tool clashes" % (fid, len(w.needs), len(w.goods), len(w.templates), len(report["needsWithoutSatisfier"]),
                                len(report["goodsWithoutSource"]), len(report["goodsWithoutUse"]),
                                len(report["toolClashes"])))
    check_tutorial(c, fid, bp, w)


def check_tutorial(c, fid, bp, w):
    if "StartingFactionSpec" not in bp:
        return
    names = set()
    for _, t in w.templates:
        ts = specs_of(t).get("TemplateSpec") or {}
        names.add(ts.get("TemplateName"))
        names.update(ts.get("BackwardCompatibleTemplateNames") or [])
    names.add("Path")
    if "Stairs.Folktails" not in names:
        R.error("Faction %s has StartingFactionSpec but no template named or aliased Stairs.Folktails: "
                "StairsUnlockedTrigger throws at load (docs/tech/tutorial.md)" % fid)
    for key, t in list(c.mod_bp.items()) + list(c.optional_bp.items()):
        rel = c.keys[key][0]
        if not rel.lower().startswith(("tutorials/", "modifiers/")):
            continue

        def walk(o, path):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k in TUTORIAL_TEMPLATE_FIELDS:
                        for n in (v if isinstance(v, list) else [v]):
                            if isinstance(n, str) and n and n not in names:
                                R.error("%s %s: tutorial step names %s, which faction %s does not have: "
                                        "TutorialService.Load throws at the start of every game" % (rel, path, n, fid))
                    else:
                        walk(v, path + "." + k)
            elif isinstance(o, list):
                for x in o:
                    walk(x, path)
        if any(k.endswith("TutorialStepSpec") or k.endswith("StepSpec") for k in specs_of(t)) or "Children" in t:
            walk(t, "")


def check_modules(c):
    """The shipped code modules (Modules/modules.txt) and the data that switches them on must match; a catalogue item
    that waits for a module must not ship unless that module and its data do."""
    if c.profile != "pandaborn":
        return
    mf = next((r for r in c.files if r.lower() == "modules/modules.txt"), None)
    shipped = set()
    if mf:
        for line in open(c.files[mf], encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#"):
                shipped.add(line.split()[0])
    specs = set()
    for b in c.mod_bp.values():
        specs.update(specs_of(b))
        for child in (b.get("Children") or {}).values():
            if isinstance(child, dict):
                specs.update(child)
    bundles = {r.rsplit("/", 1)[-1].rsplit("_", 1)[0].lower() for r in c.files if r.lower().startswith("assetbundles/")}
    data_on = set()
    for mod, (kind, what) in MODULE_DATA.items():
        present = what in specs if kind == "spec" else what in bundles
        if present:
            data_on.add(mod)
        if mod in shipped and not present:
            gate(c, "module %s ships (Modules/modules.txt) but its data (%s %s) does not: the module would do nothing"
                    % (mod, kind, what))
        if present and mod not in shipped:
            R.error("%s %s ships but module %s does not: the data needs that module" % (kind, what, mod))
    for mod in shipped - set(MODULE_DATA) - SELF_CONTAINED_MODULES:
        R.info("module %s ships; no data rule known for it" % mod)
    # catalogue items waiting for a module
    try:
        import tomllib
    except ImportError:
        return
    cat = os.path.join(REPO, "catalogue", "buildings.toml")
    if not os.path.isfile(cat):
        return
    with open(cat, "rb") as f:
        buildings = tomllib.load(f).get("buildings", {})
    present_templates = {(b.get("TemplateSpec") or {}).get("TemplateName") for b in c.mod_bp.values()}
    for bid, b in buildings.items():
        waits = b.get("waits_for") or []
        tname = (b.get("template") or bid + ".Inkpaws")
        for mod in ([waits] if isinstance(waits, str) else waits):   # one module id, or a list: all must be on
            if tname in present_templates and not (mod in shipped and mod in data_on):
                gate(c, "%s ships but waits for module %s, whose code or data is absent: its text promises what its "
                        "stand-in does not do" % (tname, mod))

# ------------------------------------------------------------------------------------------------ self test

def self_test(a):
    """tools/tests/validate/make_fixtures.py writes one folder per case (mod/ and expect.json: {"errors": [substrings
    each found in an ERROR line], "args": [extra validate args], "clean": bool}) from the vanilla dump into the build
    area first: the fixtures are copies of game files, so they stay out of git."""
    sys.path.insert(0, os.path.join(REPO, "tools", "tests", "validate"))
    try:
        import make_fixtures
    finally:
        sys.path.pop(0)
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        root = make_fixtures.main(["--blueprints", a.blueprints, "--out", a.fixtures_dir])
    finally:
        sys.stdout = old
    failed = 0
    cases = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
    for case in cases:
        d = os.path.join(root, case)
        exp = load_json(os.path.join(d, "expect.json"))
        argv = ["--mod", os.path.join(d, "mod"), "--blueprints", a.blueprints, "--localizations", a.localizations,
                "--game-data", a.game_data] + [x.replace("{fixtures}", root) for x in exp.get("args", [])]
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            code = main(argv)
        finally:
            sys.stdout = old
        out = buf.getvalue()
        errors = [line for line in out.splitlines() if line.startswith("ERROR")]
        problems = []
        for sub in exp.get("errors", []):
            if not any(sub in e for e in errors):
                problems.append("expected an error containing %r" % sub)
        if exp.get("clean") and errors:
            problems.append("expected no errors, got %d: %s" % (len(errors), errors[:3]))
        if not exp.get("clean") and code == 0:
            problems.append("exit code 0, expected 1")
        if problems:
            failed += 1
            print("FAIL %s\n  %s\n  --- output ---\n%s" % (case, "\n  ".join(problems), "\n".join(errors) or out[-2000:]))
        else:
            print("ok   %s (%d error line(s))" % (case, len(errors)))
    print("\nself-test: %d case(s), %d failed" % (len(cases), failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
