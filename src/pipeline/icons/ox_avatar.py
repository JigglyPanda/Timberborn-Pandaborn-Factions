"""The Wooden Ox bot avatar (FactionSpec.BotAvatar): a three-quarter studio render of a generic wooden ox, built from
planks in code (bl_ox_avatar.py), on the same painted teal plate as the Inkpaw and Ringtail avatars
(characters/make_portraits.plate). Replaces the Folktails robot (`Sprites/Avatars/FolktailsBot`).

usage (venv python): python -I src/pipeline/icons/ox_avatar.py [--samples 96] [--out FILE]
default --out mod/PandabornFactions/Sprites/Pandaborn/Avatars/InkpawsBot.png (+ .meta.json {"isSprite": true})
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(HERE, "..", "characters"))

BLENDER = os.environ.get("BLENDER", r"E:\PandabornDev\tools\blender-4.5-lts\blender-4.5.16-windows-x64\blender.exe")
BENV = dict(os.environ, BLENDER_USER_RESOURCES=r"E:\PandabornDev\tools\blender-userdata",
            TEMP=r"E:\PandabornDev\tools\tmp", TMP=r"E:\PandabornDev\tools\tmp")
WORK = r"E:\PandabornDev\build\icons\ox"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=96)
    ap.add_argument("--out", default=os.path.join(REPO, "mod", "PandabornFactions", "Sprites", "Pandaborn", "Avatars",
                                                  "InkpawsBot.png"))
    a = ap.parse_args()
    os.makedirs(WORK, exist_ok=True)
    raw = os.path.join(WORK, "ox_raw.png")
    r = subprocess.run([BLENDER, "-b", "--factory-startup", "--python", os.path.join(HERE, "bl_ox_avatar.py"), "--",
                        raw, str(a.samples)], env=BENV, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(raw):
        print(r.stdout[-3000:], r.stderr[-3000:])
        raise SystemExit("ox render failed")
    from make_portraits import plate  # the shared avatar plate (teal, torn edge)
    plate(raw, a.out, seed=21)
    with open(a.out + ".meta.json", "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"isSprite": True}, fh)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
