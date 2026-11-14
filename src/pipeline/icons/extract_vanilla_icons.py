"""Extract vanilla UI icons from the game for style reference (never commit the output).

Reads the Resources path table (ResourceManager in globalgamemanagers) with UnityPy and writes every Sprite or
Texture2D whose path matches one of the prefixes below, as PNG, keeping the folder layout:

  <out>/sprites/goods/BerriesIcon.png
  <out>/buildings/food/.../XIcon.png
  ...
  <out>/index.json   container path -> {png, size of the sprite rect, texture size, texture format}

Usage (venv python):
  python -I src/pipeline/icons/extract_vanilla_icons.py <Timberborn_Data> <out dir> [prefix ...]
Default prefixes: sprites/goods/ sprites/bottombar/ sprites/avatars/ sprites/statusicons/ sprites/topbar/
                  buildings/ (only paths ending in "icon") environment/ naturalresources/ ui/images/game/
"""
import json
import os
import sys

import UnityPy
from PIL import Image

DEFAULT_PREFIXES = [
    "sprites/goods/", "sprites/bottombar/", "sprites/avatars/", "sprites/statusicons/", "sprites/topbar/",
    "sprites/bonuses/", "buildings/", "environment/", "naturalresources/", "ui/images/game/",
]


def wanted(path, prefixes):
    for p in prefixes:
        if path.startswith(p):
            if p in ("buildings/", "environment/", "naturalresources/"):
                return path.endswith("icon")
            return True
    return False


def main():
    data_dir, out = sys.argv[1], sys.argv[2]
    prefixes = [p.lower() for p in sys.argv[3:]] or DEFAULT_PREFIXES
    # The Resources path table lives in globalgamemanagers (ResourceManager.m_Container); its pointers resolve into
    # resources.assets, so both files are loaded into one environment.
    env = UnityPy.load(os.path.join(data_dir, "globalgamemanagers"), os.path.join(data_dir, "resources.assets"))
    rm = next(o for o in env.objects if o.type.name == "ResourceManager").read()
    index = {}
    for path, ptr in rm.m_Container:
        lp = path.lower()
        if not wanted(lp, prefixes):
            continue
        try:
            obj = ptr.deref()
        except Exception:  # noqa: BLE001
            continue
        tname = obj.type.name
        if tname not in ("Sprite", "Texture2D"):
            continue
        if lp in index and index[lp].get("type") == "Sprite":
            continue  # a path lists both the Texture2D and the Sprite; prefer the Sprite (its rect is what UI shows)
        data = obj.read()
        try:
            img = data.image
        except Exception as e:  # noqa: BLE001
            index[lp] = {"error": repr(e)}
            continue
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        if tname == "Sprite":
            # UnityPy crops a packed sprite to its textureRect; put it back on the sprite's full rect (what the UI
            # actually shows) so framing and padding can be measured. textureRect y is bottom-up.
            rect, tr = data.m_Rect, data.m_RD.textureRect
            full = Image.new("RGBA", (round(rect.width), round(rect.height)), (0, 0, 0, 0))
            full.paste(img, (round(tr.x - rect.x), round(rect.height - (tr.y - rect.y) - tr.height)))
            img = full
        dest = os.path.join(out, *lp.split("/")) + ".png"
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        img.save(dest)
        entry = {"png": os.path.relpath(dest, out), "type": tname, "size": list(img.size), "name": data.m_Name}
        if tname == "Sprite":
            try:
                tex = data.m_RD.texture.read()
                entry["texture"] = tex.m_Name
                entry["textureSize"] = [tex.m_Width, tex.m_Height]
                entry["textureFormat"] = str(tex.m_TextureFormat)
            except Exception:  # noqa: BLE001
                pass
        index[lp] = entry
    with open(os.path.join(out, "index.json"), "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=1, sort_keys=True)
    print(f"{len(index)} icons written to {out}")


if __name__ == "__main__":
    main()
