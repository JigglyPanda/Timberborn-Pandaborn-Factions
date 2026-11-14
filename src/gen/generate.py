#!/usr/bin/env python3
"""Catalogue -> mod data. Python 3.11+ (tomllib), standard library only.

    python src/gen/generate.py [--out DIR] [--dry-run] [--lock] [--accept-pin]
    python src/gen/generate.py pin [--accept]

generate (default):
  Reads catalogue/*.toml and catalogue/text/*.json and the vanilla blueprint dump, and writes the generated part of
  the mod into --out (default E:\\PandabornDev\\build\\gen\\PandabornFactions): blueprints, collections, faction-scoped
  modifiers and loc fragments. Next to it, <out>.provenance.json records for every file its vanilla source path and
  sha256, the catalogue item, and its own sha256; <out>.report.json lists stand-ins, retire plans and code needs; and
  <out>.grid.json is a ready "grid" test request listing every placeable template. Output is deterministic: running
  twice gives identical bytes. Files in --out that the catalogue no longer produces are removed (only there).
  --dry-run   write nothing; print what would be added, removed and changed (with a short diff per changed file).
  --lock      append ids that are new to catalogue/ids.lock.json (without it, a new id is an error).
  The run refuses to start if the vanilla dump differs from catalogue/vanilla.pin.json, unless --accept-pin.

pin:
  Compares the installed game, its Unity version and the vanilla dump with catalogue/vanilla.pin.json. --accept
  rewrites the pin to the current state.

Exit codes: 0 ok, 1 catalogue error (message says what to change), 2 pin mismatch.
"""
import argparse
import difflib
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pbgen import lock as lockmod  # noqa: E402
from pbgen.catalogue import Catalogue  # noqa: E402
from pbgen.generate import Generator  # noqa: E402
from pbgen.util import (DEFAULT_BLUEPRINTS, DEFAULT_BUILD, DEFAULT_GAME, DEFAULT_LOCALIZATIONS, REPO, GenError,  # noqa: E402
                        dumps, read_bytes, write_text)
from pbgen.vanilla import Vanilla  # noqa: E402

DEFAULT_OUT = os.path.join(DEFAULT_BUILD, "gen", "PandabornFactions")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", nargs="?", default="generate", choices=("generate", "pin"))
    ap.add_argument("--catalogue", default=os.path.join(REPO, "catalogue"))
    ap.add_argument("--blueprints", default=DEFAULT_BLUEPRINTS)
    ap.add_argument("--localizations", default=DEFAULT_LOCALIZATIONS)
    ap.add_argument("--game", default=DEFAULT_GAME)
    ap.add_argument("--schema-dir", default=os.path.join(REPO, "schema"))
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--lock", action="store_true")
    ap.add_argument("--accept", action="store_true", help="pin: accept the current game as the new pin")
    ap.add_argument("--accept-pin", action="store_true", help="generate even if the game differs from the pin")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--no-code", action="store_true",
                    help="data-only fallback build: leave out everything that needs the mod's code (e.g. name pools)")
    ap.add_argument("--plants", default=os.path.join(DEFAULT_BUILD, "plants"), help="built plant meshes and bundle")
    ap.add_argument("--models", default=os.path.join(DEFAULT_BUILD, "models"), help="built model meshes (models stage)")
    a = ap.parse_args(argv)
    try:
        v = Vanilla(a.blueprints, a.localizations)
        cur = lockmod.current_pin(v, a.game, a.schema_dir)
        diffs = lockmod.check_pin(a.catalogue, cur)
        if a.command == "pin":
            if a.accept:
                lockmod.write_pin(a.catalogue, cur)
                print("pin: wrote catalogue/vanilla.pin.json (game %s, Unity %s, %d blueprints)"
                      % (cur["gameVersion"], cur["unityVersion"], cur["blueprintDump"]["files"]))
                return 0
            if diffs:
                print("pin: the game differs from catalogue/vanilla.pin.json:\n  " + "\n  ".join(diffs))
                return 2
            print("pin: game %s, Unity %s, %d vanilla blueprints match the pin"
                  % (cur["gameVersion"], cur["unityVersion"], cur["blueprintDump"]["files"]))
            return 0
        if diffs and not a.accept_pin:
            print("generate: refusing to run, the game differs from catalogue/vanilla.pin.json:\n  " + "\n  ".join(diffs)
                  + "\nReview with tools/game_diff.py, then rerun with --accept-pin (or pin --accept).")
            return 2
        return generate(a, v)
    except GenError as e:
        print("generate: ERROR " + str(e))
        return 1


def generate(a, v):
    cat = Catalogue(a.catalogue)
    g = Generator(cat, v)
    g.mesh_dir = a.models
    g.code_enabled = not a.no_code
    g.plant_dir = a.plants
    g.run()
    files = g.files()
    lock = lockmod.read_lock(a.catalogue)
    new, missing, lock_changed = lockmod.check_and_extend(lock, g.ids, allow_new=a.lock or a.dry_run, gated=g.gated)
    if missing:
        print("generate: WARNING ids in the lock that the catalogue no longer produces (retire them with an alias):")
        for kind, i in missing:
            print("   ", kind, i)
    prov = g.provenance(files)
    report = {"adoptedModels": dict(sorted(g.adopted_models.items())),
              "standIns": sorted({i for i, n in g.notes if n.startswith("stand-in on")}),
              "waitingForCode": {k: v for k, v in sorted(g.code_waits.items())},
              "modules": {"shipped": sorted(g.shipped_modules), "switches": g.module_switch,
                          "on": sorted(m for m in g.shipped_modules if g.module_switch.get(m))},
              "leftOut": {k: dict(sorted(v.items())) for k, v in sorted(g.gated.items())},
              "notes": [{"item": i, "note": n} for i, n in g.notes],
              "counts": {k: len(x) for k, x in sorted(g.ids.items())}}
    placeable = []
    for p, o in g.outputs.items():
        if o.kind == "building" and "PlaceableBlockObjectSpec" in o.data and not o.data[
                "PlaceableBlockObjectSpec"].get("DevModeTool"):
            placeable.append(o.data["TemplateSpec"]["TemplateName"])
    # every placeable template placed and finished, then recipes on, a speed ladder and a few in-game hours, so
    # finished-state and working-state code runs (the install gate, CLAUDE.md)
    grid = {"speed": 3, "grid": {"templates": placeable,
                                 "exercise": {"recipes": True, "speeds": [1, 3, 0, 2, 3], "everySeconds": 4,
                                              "holdHours": 3}}}

    existing = {}
    if os.path.isdir(a.out):
        for dp, _, names in os.walk(a.out):
            for n in names:
                ab = os.path.join(dp, n)
                existing[os.path.relpath(ab, a.out).replace("\\", "/")] = ab
    added = sorted(set(files) - set(existing))
    removed = sorted(set(existing) - set(files))
    changed = sorted(p for p in set(files) & set(existing) if read_bytes(existing[p]) != files[p])
    print("generate: %d files (%d blueprints, %d loc fragments); %d new, %d changed, %d removed vs %s"
          % (len(files), len(g.outputs), len(g.loc), len(added), len(changed), len(removed), a.out))
    if a.dry_run:
        for p in added:
            print("  + " + p)
        for p in removed:
            print("  - " + p)
        for p in changed:
            print("  ~ " + p)
            old = read_bytes(existing[p]).decode("utf-8").splitlines()
            new_ = files[p].decode("utf-8").splitlines()
            d = list(difflib.unified_diff(old, new_, "old", "new", n=1, lineterm=""))
            for line in d[2:40]:
                print("      " + line)
            if len(d) > 40:
                print("      ... (%d more diff lines)" % (len(d) - 40))
        if new:
            print("generate: %d id(s) would be new to the lock (rerun with --lock to freeze them)" % len(new))
        return 0
    for p in removed:
        os.remove(existing[p])
    for p in added + changed:
        target = os.path.join(a.out, *p.split("/"))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "wb") as f:
            f.write(files[p])
    for dp, dirs, names in sorted(os.walk(a.out, topdown=False), reverse=False):
        if dp != a.out and not os.listdir(dp):
            shutil.rmtree(dp)
    write_text(a.out + ".provenance.json", dumps(prov))
    write_text(a.out + ".report.json", dumps(report))
    write_text(a.out + ".grid.json", dumps(grid))
    # a ready test request for the adopted models: each placed and finished (grid), one unfinished copy per model
    # started so its construction stage shows, close-ups of both (src/devharness/ModelShots.cs)
    adopted = []
    for p_, o in g.outputs.items():
        mesh = (((o.data.get("Children") or {}).get("#Finished") or {}).get("TimbermeshSpec") or {}).get("Model", "")
        if o.kind == "building" and mesh.startswith("Buildings/Pandaborn/Models/"):
            adopted.append(o.data["TemplateSpec"]["TemplateName"])
    adopted.sort()
    staged = [t for t in adopted if "DistrictCenterSpec" not in json.dumps(g.outputs_by_template(t))]
    model_request = {
        "grid": {"templates": adopted},
        "buildings": [{"template": t, "finished": False} for t in staged],
        "modelShots": {"afterGrid": True, "stage": staged,
                       "shots": [{"template": t, "finished": True, "name": "model_" + t.split(".")[0]} for t in adopted]
                                + [{"template": t, "finished": False, "name": "stage_" + t.split(".")[0]} for t in staged]},
    }
    write_text(a.out + ".models.request.json", dumps(model_request))
    # meshes of adopted models: assemble copies them into the mod (built by the models stage, never in git)
    missing = sorted(src for src in g.model_files.values() if not os.path.isfile(src))
    write_text(a.out + ".models.json", dumps({"files": dict(sorted(g.model_files.items())),
                                               "bundles": sorted(g.bundles_needed),
                                               "adopted": dict(sorted(g.adopted_models.items()))}))
    if missing:
        print("generate: WARNING %d model mesh(es) not built yet (run: tools/pandaborn.ps1 models): %s"
              % (len(missing), ", ".join(missing[:5])))
    if new or (lock_changed and not a.dry_run):
        lockmod.write_lock(a.catalogue, lock)
        print("generate: appended %d id(s) to catalogue/ids.lock.json" % len(new))
    if not a.quiet:
        for i, n in g.notes:
            pass
        print("generate: %d templates, %d stand-ins/notes (see %s.report.json)"
              % (len(g.ids.get("template", {})), len(g.notes), a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
