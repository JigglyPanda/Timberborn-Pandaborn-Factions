"""Regenerate every icon: render, write sprite + meta into the mod, previews and review sheets into the build dir.

Usage (venv python, from the repo root):
  E:\\PandabornDev\\tools\\venv\\Scripts\\python.exe -I src/pipeline/icons/build_icons.py [options] [id ...]

  id ...          only these icons (substring match on the id); review sheets still cover the whole set
  --mod DIR       mod root (default mod/PandabornFactions)
  --out DIR       build dir (default E:\\PandabornDev\\build\\icons)
  --vanilla DIR   extracted vanilla icons (default E:\\PandabornDev\\reference\\vanilla-icons)
  --no-mod        render to the build dir only; leave the mod untouched

Output:
  <mod>/Sprites/Pandaborn/<Group>/<Id>Icon.png (+ .png.meta.json)    shipped icons (IconDef.ship)
  <out>/rendered/<Group>/[unshipped/]<Id>Icon.png                    every icon; unshipped ones in a sub-folder
  <out>/preview/<Id>Icon.png                                          4x on the panel colour
  <out>/<group>_sheet.png, _large.png, _blind.png                     review sheets beside vanilla
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import ink  # noqa: E402
import goods  # noqa: E402,F401  (registers the goods icons)
import plants  # noqa: E402,F401  (registers the plant icons)
import buildings  # noqa: E402,F401  (registers the building icons)
import logo  # noqa: E402,F401  (registers the faction logo, proposal)
import contact_sheet  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

# Texture settings per group, as the game's ModTextureSettingLoader reads them (<file>.png.meta.json).
# Vanilla goods icons are 80x80 RGBA32, sRGB, mipmapped, trilinear (they are shown at many sizes).
# Vanilla building, plant and logo icons have no mipmaps and clamp: the sprite preset.
META = {
    "Goods": {"generateMipmap": True, "mipmapCount": -1, "ignoreMipmapLimits": True, "textureFormat": "RGBA32"},
    "default": {"isSprite": True},
}

# group -> (vanilla sub-folder to compare with, vanilla sample names or None for all)
REVIEW = {
    "Goods": ("sprites/goods", contact_sheet.VANILLA_GOODS),
    "Plants": ("naturalresources", None),
    "Buildings": ("buildings", ["lodge", "triplelodge", "farmhouse", "grill", "bakery", "gristmill", "waterwheel",
                                "windturbine", "smalltank", "largetank", "campfire", "inventor", "medicalbed",
                                "rooftopterrace", "powerwheel", "beehive", "lumberjackflag", "forester",
                                "teethgrindstone", "detailer"]),
    "Avatars": ("sprites/avatars", ["folktailslogo", "ironteethlogo"]),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--mod", default=os.path.join(REPO, "mod", "PandabornFactions"))
    ap.add_argument("--out", default=r"E:\PandabornDev\build\icons")
    ap.add_argument("--vanilla", default=r"E:\PandabornDev\reference\vanilla-icons")
    ap.add_argument("--no-mod", action="store_true")
    a = ap.parse_args()

    defs = [d for d in ink.REGISTRY.values() if not a.ids or any(s.lower() in d.id.lower() for s in a.ids)]
    os.makedirs(os.path.join(a.out, "preview"), exist_ok=True)
    for d in defs:
        img = d.render()
        name = d.filename
        rendered = os.path.join(a.out, "rendered", d.group, *([] if d.ship else ["unshipped"]))
        os.makedirs(rendered, exist_ok=True)
        img.save(os.path.join(rendered, name))
        ink.preview(img, scale=4).save(os.path.join(a.out, "preview", name))
        where = "build only"
        if d.ship and not a.no_mod:
            dest = os.path.join(a.mod, "Sprites", "Pandaborn", d.group)
            os.makedirs(dest, exist_ok=True)
            img.save(os.path.join(dest, name), optimize=True)
            with open(os.path.join(dest, name + ".meta.json"), "w", encoding="utf-8", newline="\n") as fh:
                json.dump(META.get(d.group, META["default"]), fh, indent=2)
                fh.write("\n")
            where = "mod"
        print(f"{d.group}/{name} ({where})")
    for group in sorted({d.group for d in ink.REGISTRY.values()}):
        sub, sample = REVIEW.get(group, (None, None))
        vdir = os.path.join(a.vanilla, *sub.split("/")) if sub else None
        if vdir and os.path.isdir(vdir):
            # the review sheets show what ships; logo candidates (unshipped) are shown beside the pick
            contact_sheet.make(os.path.join(a.out, "rendered", group), vdir, a.out, group.lower(), sample,
                               include_unshipped=(group == "Avatars"))
        else:
            print(f"{group}: no vanilla icons to compare with (run extract_vanilla_icons.py)")


if __name__ == "__main__":
    main()
