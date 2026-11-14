#!/usr/bin/env python3
"""What a game update changed, and which of our items it touches. Standard library only.

    python tools/game_diff.py --old-blueprints A --new-blueprints B [--old-schema X.json --new-schema Y.json]
                              [--old-loc DIR --new-loc DIR] [--provenance E:\\PandabornDev\\build\\gen\\PandabornFactions.provenance.json]
                              [--generated E:\\PandabornDev\\build\\gen\\PandabornFactions] [--json out.json]

Reports
  * vanilla blueprints added, removed, renamed (same content or same template name / id at a new path) and changed,
    with the changed JSON paths; for each, the generated files and catalogue items built from it (via provenance);
  * vanilla template names and global ids (goods, needs, recipes...) that disappeared;
  * schema: specs added/removed, fields added/removed/retyped, enum values removed, Unity version; for each, the
    generated blueprints that use the spec or field (a removed field there is silently ignored by the new game);
  * loc keys removed or changed that generated blueprints reference.
Exit code: 0 nothing affects us, 3 something we use changed (review before `pandaborn.ps1 pin -Accept`).
"""
import argparse
import hashlib
import json
import os
import sys

ID_SPECS = ("GoodSpec", "NeedSpec", "RecipeSpec", "NeedGroupSpec", "WorkerTypeSpec", "ToolGroupSpec", "BonusTypeSpec")


def load_json(path):
    with open(path, "rb") as f:
        raw = f.read()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    return json.loads(raw.decode("utf-8"))


def dump_index(root):
    out = {}
    for dp, _, names in os.walk(root):
        for n in names:
            if n.endswith(".blueprint.json"):
                ab = os.path.join(dp, n)
                rel = os.path.relpath(ab, root).replace("\\", "/")[:-len(".json")]
                with open(ab, "rb") as f:
                    raw = f.read()
                out[rel] = (hashlib.sha256(raw).hexdigest(), ab)
    return out


def identity(bp):
    """Names that identify a blueprint across a move: template name or global id."""
    out = set()
    ts = bp.get("TemplateSpec")
    if ts and ts.get("TemplateName"):
        out.add("template:" + ts["TemplateName"])
    for s in ID_SPECS:
        if s in bp and bp[s].get("Id"):
            out.add(s + ":" + bp[s]["Id"])
    return out


def json_diff(a, b, path="", out=None, limit=60):
    out = [] if out is None else out
    if len(out) >= limit:
        return out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            p = path + "." + k if path else k
            if k not in a:
                out.append("+ " + p)
            elif k not in b:
                out.append("- " + p)
            else:
                json_diff(a[k], b[k], p, out, limit)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            json_diff(x, y, "%s[%d]" % (path, i), out, limit)
    elif a != b:
        out.append("~ %s: %s -> %s" % (path, json.dumps(a)[:80], json.dumps(b)[:80]))
    return out


def walk_keys(bp, prefix=""):
    """(spec, field) pairs used in a blueprint, children included."""
    for k, v in bp.items():
        base = k.split("#")[0] if "#" in k and not k.startswith("#") else k
        if k == "Children" and isinstance(v, dict):
            for child in v.values():
                if isinstance(child, dict):
                    yield from walk_keys(child)
        elif isinstance(v, dict):
            yield base, None
            for f in v:
                yield base, f.split("#")[0]


def load_loc(d):
    import csv
    p = os.path.join(d, "enUS.csv")
    out = {}
    if os.path.isfile(p):
        with open(p, encoding="utf-8-sig", newline="") as f:
            for row in csv.reader(f):
                if row:
                    out[row[0]] = row[1] if len(row) > 1 else ""
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--old-blueprints", required=True)
    ap.add_argument("--new-blueprints", required=True)
    ap.add_argument("--old-schema")
    ap.add_argument("--new-schema")
    ap.add_argument("--old-loc")
    ap.add_argument("--new-loc")
    ap.add_argument("--provenance", default=r"E:\PandabornDev\build\gen\PandabornFactions.provenance.json")
    ap.add_argument("--generated", default=r"E:\PandabornDev\build\gen\PandabornFactions")
    ap.add_argument("--json", help="also write the report as JSON")
    a = ap.parse_args(argv)

    old, new = dump_index(a.old_blueprints), dump_index(a.new_blueprints)
    prov = load_json(a.provenance) if a.provenance and os.path.isfile(a.provenance) else {}
    by_source = {}
    for out_path, meta in prov.items():
        if meta.get("source"):
            by_source.setdefault(meta["source"], []).append((out_path, meta.get("item")))
    report = {"blueprints": {"added": [], "removed": [], "renamed": [], "changed": []}, "ids_removed": [],
              "schema": {}, "loc": {}, "affects_us": []}

    removed = sorted(set(old) - set(new))
    added = sorted(set(new) - set(old))
    # renames: identical content, or the same template name / id at another path
    new_by_hash = {}
    for p in added:
        new_by_hash.setdefault(new[p][0], []).append(p)
    new_ident = {}
    for p in added:
        for i in identity(load_json(new[p][1])):
            new_ident[i] = p
    for p in list(removed):
        target = None
        if new_by_hash.get(old[p][0]):
            target = new_by_hash[old[p][0]].pop(0)
        else:
            for i in identity(load_json(old[p][1])):
                if i in new_ident:
                    target = new_ident[i]
                    break
        if target:
            removed.remove(p)
            if target in added:
                added.remove(target)
            report["blueprints"]["renamed"].append({"from": p, "to": target, "uses": by_source.get(p, [])})
    for p in removed:
        report["blueprints"]["removed"].append({"path": p, "uses": by_source.get(p, [])})
    report["blueprints"]["added"] = added
    for p in sorted(set(old) & set(new)):
        if old[p][0] != new[p][0]:
            report["blueprints"]["changed"].append({"path": p, "uses": by_source.get(p, []),
                                                    "diff": json_diff(load_json(old[p][1]), load_json(new[p][1]))})

    old_ids, new_ids = set(), set()
    for p in old:
        old_ids |= identity(load_json(old[p][1]))
    for p in new:
        new_ids |= identity(load_json(new[p][1]))
    report["ids_removed"] = sorted(old_ids - new_ids)

    # what our generated blueprints use
    used_specs, used_fields, used_loc = {}, {}, {}
    if a.generated and os.path.isdir(a.generated):
        for dp, _, names in os.walk(a.generated):
            for n in names:
                if not n.endswith(".blueprint.json"):
                    continue
                ab = os.path.join(dp, n)
                rel = os.path.relpath(ab, a.generated).replace("\\", "/")
                bp = load_json(ab)
                for spec, field in walk_keys(bp):
                    used_specs.setdefault(spec, set()).add(rel)
                    if field:
                        used_fields.setdefault((spec, field), set()).add(rel)
                for k, v in walk_strings(bp):
                    if k.endswith("LocKey") and v:
                        used_loc.setdefault(v, set()).add(rel)
    # ids of vanilla things our outputs reference by name (template names, goods, recipes)
    for rid in report["ids_removed"]:
        kind, name = rid.split(":", 1)
        users = sorted(rel for rel in iter_generated_mentions(a.generated, name))
        if users:
            report["affects_us"].append("vanilla %s %s is gone; referenced by %s" % (kind, name, ", ".join(users[:5])))

    if a.old_schema and a.new_schema:
        so, sn = load_json(a.old_schema), load_json(a.new_schema)
        sch = {"gameVersion": [so.get("gameVersion"), sn.get("gameVersion")],
               "unityVersion": [so.get("unityVersion"), sn.get("unityVersion")],
               "specsAdded": sorted(set(sn["specs"]) - set(so["specs"])),
               "specsRemoved": sorted(set(so["specs"]) - set(sn["specs"])), "fields": [], "enums": []}
        for k in sorted(set(so["specs"]) & set(sn["specs"])):
            fo, fn = so["specs"][k].get("fields", {}), sn["specs"][k].get("fields", {})
            for f in sorted(set(fo) | set(fn)):
                if f not in fn:
                    sch["fields"].append({"spec": k, "field": f, "change": "removed",
                                          "usedBy": sorted(used_fields.get((k, f), []))[:10]})
                elif f not in fo:
                    sch["fields"].append({"spec": k, "field": f, "change": "added", "usedBy": []})
                elif fo[f]["type"] != fn[f]["type"]:
                    sch["fields"].append({"spec": k, "field": f, "change": "type %s -> %s" % (
                        json.dumps(fo[f]["type"]), json.dumps(fn[f]["type"])), "usedBy": sorted(used_fields.get((k, f), []))[:10]})
                elif fo[f].get("default") != fn[f].get("default"):
                    sch["fields"].append({"spec": k, "field": f, "change": "default %s -> %s" % (
                        fo[f].get("default"), fn[f].get("default")), "usedBy": sorted(used_fields.get((k, f), []))[:10]})
        for e in sorted(set(so.get("enums", {})) & set(sn.get("enums", {}))):
            vo = {x["name"] for x in so["enums"][e]["values"]}
            vn = {x["name"] for x in sn["enums"][e]["values"]}
            if vo - vn:
                sch["enums"].append({"enum": e, "removed": sorted(vo - vn)})
        for k in sch["specsRemoved"]:
            if k in used_specs:
                report["affects_us"].append("spec %s was removed and is used by %d generated blueprint(s): the game "
                                            "now throws reading them" % (k, len(used_specs[k])))
        for f in sch["fields"]:
            if f["usedBy"] and f["change"] != "added":
                report["affects_us"].append("%s.%s %s; used by %s" % (f["spec"], f["field"], f["change"],
                                                                       ", ".join(f["usedBy"][:3])))
        if sch["unityVersion"][0] != sch["unityVersion"][1]:
            report["affects_us"].append("Unity %s -> %s: rebuild every asset bundle with the new editor"
                                        % tuple(sch["unityVersion"]))
        report["schema"] = sch

    if a.old_loc and a.new_loc:
        lo, ln = load_loc(a.old_loc), load_loc(a.new_loc)
        gone = sorted(k for k in lo if k not in ln)
        changed = sorted(k for k in lo if k in ln and lo[k] != ln[k])
        report["loc"] = {"removed": gone, "changed": changed, "added": sorted(set(ln) - set(lo))}
        for k in gone:
            if k in used_loc:
                report["affects_us"].append("loc key %s was removed; used by %s" % (k, ", ".join(sorted(used_loc[k])[:3])))

    for kind in ("removed", "renamed", "changed"):
        for e in report["blueprints"][kind]:
            if e.get("uses"):
                what = e.get("path") or "%s -> %s" % (e["from"], e["to"])
                items = sorted({str(i) for _, i in e["uses"]})
                report["affects_us"].append("vanilla blueprint %s %s; feeds %d generated file(s) from %s"
                                            % (what, kind, len(e["uses"]), "; ".join(items[:3])))

    print_report(report)
    if a.json:
        with open(a.json, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return 3 if report["affects_us"] else 0


def walk_strings(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_strings(v, k)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_strings(v, path)
    elif isinstance(obj, str):
        yield path, obj


_mention_cache = {}


def iter_generated_mentions(root, name):
    if not root or not os.path.isdir(root):
        return []
    if root not in _mention_cache:
        texts = {}
        for dp, _, names in os.walk(root):
            for n in names:
                if n.endswith(".blueprint.json"):
                    ab = os.path.join(dp, n)
                    with open(ab, encoding="utf-8") as f:
                        texts[os.path.relpath(ab, root).replace("\\", "/")] = f.read()
        _mention_cache[root] = texts
    needle = '"%s"' % name
    return [rel for rel, t in _mention_cache[root].items() if needle in t]


def print_report(r):
    b = r["blueprints"]
    print("blueprints: %d added, %d removed, %d renamed, %d changed" % (len(b["added"]), len(b["removed"]),
                                                                        len(b["renamed"]), len(b["changed"])))
    for e in b["removed"]:
        print("  - %s%s" % (e["path"], "  <- feeds us" if e["uses"] else ""))
    for e in b["renamed"]:
        print("  > %s -> %s%s" % (e["from"], e["to"], "  <- feeds us" if e["uses"] else ""))
    for e in b["changed"]:
        print("  ~ %s%s" % (e["path"], "  <- feeds us" if e["uses"] else ""))
        for line in e["diff"][:8]:
            print("      " + line)
    if r["ids_removed"]:
        print("ids gone: " + ", ".join(r["ids_removed"][:30]))
    s = r.get("schema")
    if s:
        print("schema %s -> %s (Unity %s -> %s): %d specs added, %d removed, %d field changes, %d enum changes"
              % (s["gameVersion"][0], s["gameVersion"][1], s["unityVersion"][0], s["unityVersion"][1],
                 len(s["specsAdded"]), len(s["specsRemoved"]), len(s["fields"]), len(s["enums"])))
        for f in s["fields"][:40]:
            print("  %s.%s: %s%s" % (f["spec"], f["field"], f["change"], "  <- used by us" if f["usedBy"] else ""))
    if r.get("loc"):
        print("loc: %d removed, %d changed, %d added" % (len(r["loc"]["removed"]), len(r["loc"]["changed"]),
                                                         len(r["loc"]["added"])))
    print("\nAFFECTS US (%d):" % len(r["affects_us"]))
    for line in r["affects_us"]:
        print("  * " + line)
    if not r["affects_us"]:
        print("  nothing")


if __name__ == "__main__":
    sys.exit(main())
