"""Game-update alarm for the runtime code: fails when a module's game-API list changed and nobody acknowledged it.

    python -I tools/check_api_lists.py [--repo .] [--against HEAD] [--warn-only]

Every build of src/code rewrites the generated half of each module's FEATURE.md (between <!-- api:begin --> and
<!-- api:end -->) from the compiled module (tools/Pandaborn.ApiScan): the game types, methods and fields it references.
That list changes when our code starts touching something new, or when a game update changes what the compiler binds
to. This check compares each generated section in the working tree with the committed one (git, --against) and prints
the difference. Committing the regenerated FEATURE.md is the acknowledgement: review the diff (a new private member
needs its written fallback, a changed game signature needs a look), then commit.

Exit 1 when any section differs (0 with --warn-only), 2 when git or a file cannot be read.
Run it after the code build: tools/pandaborn.ps1 code (dev builds may pass --warn-only; release builds must not).
"""
import argparse
import difflib
import glob
import os
import subprocess
import sys

BEGIN, END = "<!-- api:begin -->", "<!-- api:end -->"


def section(text):
    if text is None:
        return None
    text = text.replace("\r\n", "\n")
    b, e = text.find(BEGIN), text.find(END)
    return text[b:e + len(END)] if b >= 0 and e > b else ""


def committed(repo, ref, rel):
    r = subprocess.run(["git", "-C", repo, "show", f"{ref}:{rel}"], capture_output=True)
    if r.returncode != 0:
        return None
    return r.stdout.decode("utf-8", errors="replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--against", default="HEAD")
    ap.add_argument("--warn-only", action="store_true")
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(a.repo, "src", "code", "*", "FEATURE.md")))
    if not files:
        print("no FEATURE.md under src/code")
        return 2
    changed = 0
    for path in files:
        rel = os.path.relpath(path, a.repo).replace("\\", "/")
        with open(path, encoding="utf-8") as fh:
            now = section(fh.read())
        was = section(committed(a.repo, a.against, rel))
        if was is None:
            print(f"NEW   {rel}: not committed yet; its API list needs a first review")
            changed += 1
            continue
        if now != was:
            changed += 1
            print(f"CHANGED {rel}:")
            for line in difflib.unified_diff(was.splitlines(), now.splitlines(), "committed", "built", lineterm="", n=0):
                if not line.startswith(("---", "+++", "@@")):
                    print("   " + line)
        else:
            print(f"ok    {rel}")
    if changed:
        print(f"\n{changed} module API list(s) changed. Review the lines above (game update? new private member?), then commit "
              "the FEATURE.md files to acknowledge.")
        return 0 if a.warn_only else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
