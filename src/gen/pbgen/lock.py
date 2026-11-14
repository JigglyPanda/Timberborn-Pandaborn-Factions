"""catalogue/ids.lock.json (append-only id register) and catalogue/vanilla.pin.json (the game the catalogue was derived
against)."""
import datetime
import json
import os
import subprocess

from .util import GenError, REPO, dumps, load_json

LOCK_KINDS = ("faction", "template", "template_alias", "collection", "good", "need", "need_group", "recipe",
              "worker_type", "spec_class", "save_key", "bundle")
LOCK_NOTE = ("Append-only register of every id this mod has ever shipped or generated (docs/ENGINEERING.md). Never "
             "delete or rename an entry: a removed id breaks saves. A replaced id stays here and lives on as an alias "
             "(BackwardCompatibleTemplateNames / BackwardCompatibleIds); a retired building keeps its template. "
             "src/gen adds new ids only with --lock; tools/validate.py checks the build against this file and this "
             "file against its committed version.")


def lock_path(cat_dir):
    return os.path.join(cat_dir, "ids.lock.json")


def read_lock(cat_dir):
    p = lock_path(cat_dir)
    if not os.path.isfile(p):
        return {"_note": LOCK_NOTE, "ids": {k: {} for k in LOCK_KINDS}}
    data = load_json(p)
    for k in LOCK_KINDS:
        data.setdefault("ids", {}).setdefault(k, {})
    return data


def check_and_extend(lock, produced, allow_new, today=None):
    """produced: kind -> {id: item}. Returns (new ids, missing ids). Raises if new ids appear without allow_new."""
    today = today or datetime.date.today().isoformat()
    new, missing = [], []
    for kind, ids in produced.items():
        if kind not in lock["ids"]:
            raise GenError("ids.lock.json has no kind %s" % kind)
        for i in sorted(ids):
            if i not in lock["ids"][kind]:
                new.append((kind, i, ids[i]))
    for kind, entries in lock["ids"].items():
        for i, meta in entries.items():
            if i not in produced.get(kind, {}) and not meta.get("retired") and not meta.get("external"):
                missing.append((kind, i))
    if new and not allow_new:
        lines = "\n".join("  %s %s (%s)" % n for n in new[:40])
        raise GenError("%d new id(s) not in catalogue/ids.lock.json. Ids are frozen forever once locked; check the "
                       "names, then rerun with --lock to append them:\n%s%s"
                       % (len(new), lines, "\n  ..." if len(new) > 40 else ""))
    for kind, i, item in new:
        lock["ids"][kind][i] = {"since": today}
    return new, missing


def write_lock(cat_dir, lock):
    out = {"_note": LOCK_NOTE, "ids": {k: dict(sorted(lock["ids"][k].items())) for k in LOCK_KINDS}}
    with open(lock_path(cat_dir), "w", encoding="utf-8", newline="\n") as f:
        f.write(dumps(out))


def committed_lock(cat_dir, rev="HEAD"):
    """The lock file as committed at rev, or None (not in git yet / no git)."""
    rel = os.path.relpath(lock_path(cat_dir), REPO).replace("\\", "/")
    try:
        r = subprocess.run(["git", "-C", REPO, "show", "%s:%s" % (rev, rel)], capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    return json.loads(r.stdout.decode("utf-8-sig"))


def append_only_violations(old, new):
    """Entries in old that are gone or changed in new (a retired flag may be added; nothing may be removed)."""
    out = []
    for kind, entries in (old or {}).get("ids", {}).items():
        for i, meta in entries.items():
            cur = new.get("ids", {}).get(kind, {}).get(i)
            if cur is None:
                out.append("%s %s was removed" % (kind, i))
            elif cur.get("since") != meta.get("since"):
                out.append("%s %s: 'since' changed" % (kind, i))
    return out


# ------------------------------------------------------------------------------------------------------ pin
def pin_path(cat_dir):
    return os.path.join(cat_dir, "vanilla.pin.json")


def game_versions(game_dir):
    vfile = os.path.join(game_dir, "Timberborn_Data", "StreamingAssets", "VersionNumbers.json")
    version = load_json(vfile).get("CurrentVersion") if os.path.isfile(vfile) else None
    unity = None
    ggm = os.path.join(game_dir, "Timberborn_Data", "globalgamemanagers")
    if os.path.isfile(ggm):
        with open(ggm, "rb") as f:
            head = f.read(256)
        import re
        m = re.search(rb"(\d{4}\.\d+\.\d+[abfp]\d+)", head)
        unity = m.group(1).decode() if m else None
    return version, unity


def current_pin(vanilla, game_dir, schema_dir):
    fp, count = vanilla.dump_fingerprint()
    version, unity = game_versions(game_dir)
    schema = os.path.join(schema_dir, "%s.json" % version) if version else None
    return {
        "gameVersion": version,
        "unityVersion": unity,
        "blueprintDump": {"path": vanilla.dir, "files": count, "sha256": fp},
        "schema": os.path.relpath(schema, REPO).replace("\\", "/") if schema and os.path.isfile(schema) else None,
    }


def check_pin(cat_dir, cur):
    """Returns a list of differences between the pinned and the current game (empty = same)."""
    p = pin_path(cat_dir)
    if not os.path.isfile(p):
        return ["no catalogue/vanilla.pin.json yet (run: tools/pandaborn.ps1 pin -Accept)"]
    pin = load_json(p)
    diffs = []
    for k in ("gameVersion", "unityVersion"):
        if pin.get(k) != cur.get(k):
            diffs.append("%s: pinned %s, now %s" % (k, pin.get(k), cur.get(k)))
    a, b = pin.get("blueprintDump", {}), cur["blueprintDump"]
    if a.get("sha256") != b["sha256"]:
        diffs.append("vanilla blueprint dump changed: pinned %s files sha %s..., now %s files sha %s... "
                     "(run tools/game_diff.py to see what changed)" % (a.get("files"), str(a.get("sha256"))[:12],
                                                                         b["files"], b["sha256"][:12]))
    return diffs


def write_pin(cat_dir, cur):
    with open(pin_path(cat_dir), "w", encoding="utf-8", newline="\n") as f:
        f.write(dumps(cur))
