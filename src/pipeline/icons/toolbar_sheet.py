"""The faction's whole building toolbar as the player meets it: every Inkpaws building icon, ours and the vanilla
ones kept by re-themed buildings, grouped and ordered as the bottom bar groups them, at menu sizes.

Reads the generated mod (tool group, order and icon of every building template). A building of ours whose icon file
exists under the naming rule (Sprites/Pandaborn/Buildings/<Name>Icon) is shown with it even if the generated data
still names the stand-in's icon, so the sheet shows the next build. Writes <out>/toolbar_sheet.png and prints the
coverage per group.

Usage (venv python):
  python -I src/pipeline/icons/toolbar_sheet.py [--gen DIR] [--icons DIR] [--vanilla DIR] [--out DIR]
"""
import argparse
import glob
import json
import os

from PIL import Image, ImageDraw, ImageFont

PANEL = (34, 53, 42)
BAR = (28, 41, 35)
LABEL = (205, 208, 181)
OURS = (132, 214, 160)
MISSING = (230, 120, 100)


def _font(size):
    for f in ("arial.ttf", "segoeui.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            continue
    return ImageFont.load_default()


def collect(gen, icons_dir, vanilla_dir):
    rows = []
    for p in glob.glob(os.path.join(gen, "Buildings", "**", "*.blueprint.json"), recursive=True):
        with open(p, encoding="utf-8-sig") as fh:
            d = json.load(fh)
        name = d.get("TemplateSpec", {}).get("TemplateName")
        pb = d.get("PlaceableBlockObjectSpec")
        if not name or pb is None:
            continue
        icon = d.get("LabeledEntitySpec", {}).get("Icon", "")
        base = name.split(".")[0]
        own = os.path.join(icons_dir, base + "Icon.png")
        if icon.startswith("Sprites/Pandaborn/"):       # ours by path, whatever the template is called (Pole Mill)
            own = os.path.join(icons_dir, icon.rsplit("/", 1)[1] + ".png")
        if os.path.isfile(own):
            src, kind = own, "ours"
        else:
            v = os.path.join(vanilla_dir, *icon.lower().split("/")) + ".png"
            src, kind = (v, "vanilla") if os.path.isfile(v) else (None, "missing")
            if base.startswith("Pandaborn"):
                kind = "stand-in" if src else "missing"
        rows.append(dict(group=pb.get("ToolGroupId") or "-", order=pb.get("ToolOrder", 0), name=base, icon=icon,
                         src=src, kind=kind))
    rows.sort(key=lambda r: (r["group"], r["order"], r["name"]))
    return rows


def sheet(rows, out, sizes=(56, 40)):
    f12, f15 = _font(11), _font(15)
    groups = []
    for r in rows:
        if not groups or groups[-1][0] != r["group"]:
            groups.append((r["group"], []))
        groups[-1][1].append(r)
    big = sizes[0]
    cell = big + 30
    cols = 14
    blocks = []
    for g, items in groups:
        n_rows = (len(items) + cols - 1) // cols
        h = 24 + n_rows * (big + 22 + sizes[1] + 8)
        im = Image.new("RGB", (cols * cell + 16, h), BAR)
        d = ImageDraw.Draw(im)
        d.text((8, 4), f"{g}  ({sum(1 for i in items if i['kind'] == 'ours')} ours / {len(items)})", fill=LABEL, font=f15)
        for k, r in enumerate(items):
            x = 8 + (k % cols) * cell
            y = 24 + (k // cols) * (big + 22 + sizes[1] + 8)
            if r["src"]:
                ic = Image.open(r["src"]).convert("RGBA")
                for s, (ox, oy) in zip(sizes, ((x + (cell - big) // 2, y), (x + (cell - sizes[1]) // 2, y + big + 16))):
                    t = ic.resize((s, s), Image.LANCZOS)
                    im.paste(t, (ox, oy), t)
            colour = {"ours": OURS, "missing": MISSING, "stand-in": MISSING}.get(r["kind"], LABEL)
            label = r["name"].replace("Pandaborn", "")[:14]
            tw = d.textlength(label, font=f12)
            d.text((x + (cell - tw) / 2, y + big + 2), label, fill=colour, font=f12)
        blocks.append(im)
    W = max(b.width for b in blocks)
    H = sum(b.height + 6 for b in blocks)
    sh = Image.new("RGB", (W, H), PANEL)
    y = 0
    for b in blocks:
        sh.paste(b, (0, y))
        y += b.height + 6
    sh.save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", default=r"E:\PandabornDev\build\gen\PandabornFactions")
    ap.add_argument("--icons", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..",
                                                     "mod", "PandabornFactions", "Sprites", "Pandaborn", "Buildings"))
    ap.add_argument("--vanilla", default=r"E:\PandabornDev\reference\vanilla-icons")
    ap.add_argument("--out", default=r"E:\PandabornDev\build\icons")
    a = ap.parse_args()
    rows = collect(a.gen, os.path.abspath(a.icons), a.vanilla)
    os.makedirs(a.out, exist_ok=True)
    sheet(rows, os.path.join(a.out, "toolbar_sheet.png"))
    counts = {}
    for r in rows:
        counts[r["kind"]] = counts.get(r["kind"], 0) + 1
    for r in rows:
        if r["kind"] in ("missing", "stand-in"):
            print(f"{r['kind']}: {r['name']} ({r['group']}) -> {r['icon']}")
    print("buildings:", len(rows), counts, "->", os.path.join(a.out, "toolbar_sheet.png"))


if __name__ == "__main__":
    main()
