"""Building models beside their icons: does the icon show the building the player will place?

For each pair, the left part of the model preview (E:\\PandabornDev\\build\\models\\preview\\<Model>_day.png, the
model is on the left, its vanilla counterpart on the right) and the icon at 224, 56 and 39 px. Writes
<out>/models_<n>.png, six pairs per sheet. Pairs default to every building icon whose model preview exists (the
model id is the icon id without "Pandaborn"; the table below maps the exceptions).

Usage (venv python): python -I src/pipeline/icons/model_compare.py [--icons DIR] [--previews DIR] [--out DIR]
"""
import argparse
import glob
import os

from PIL import Image, ImageDraw, ImageFont

# icon name (without Pandaborn/Icon) -> model id, where they differ
MODEL_OF = {"CisternSmall": "Cistern", "KiteWindmillSmall": "KiteWindmill", "KiteWindmillLarge": "KiteWindmill",
            "PandaKindergarten": "Kindergarten"}


def _font(size):
    for f in ("arial.ttf", "segoeui.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            continue
    return ImageFont.load_default()


def cell(preview, icon_png, label, font):
    im = Image.open(preview).convert("RGB") if preview else Image.new("RGB", (1200, 800), (90, 90, 90))
    im = im.crop((0, 60, 720, 780)).resize((360, 360))
    c = Image.new("RGB", (610, 380), (34, 53, 42))
    c.paste(im, (0, 10))
    ic = Image.open(icon_png).convert("RGBA")
    for size, pos in ((224, (372, 10)), (56, (372, 250)), (39, (450, 258))):
        t = ic.resize((size, size), Image.LANCZOS)
        c.paste(t, pos, t)
    ImageDraw.Draw(c).text((372, 330), label, fill=(220, 220, 200), font=font)
    return c


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--icons", default=os.path.join(here, "..", "..", "..", "mod", "PandabornFactions", "Sprites",
                                                     "Pandaborn", "Buildings"))
    ap.add_argument("--previews", default=r"E:\PandabornDev\build\models\preview")
    ap.add_argument("--out", default=r"E:\PandabornDev\build\icons")
    a = ap.parse_args()
    f = _font(16)
    cells = []
    for png in sorted(glob.glob(os.path.join(a.icons, "Pandaborn*Icon.png"))):
        name = os.path.basename(png)[len("Pandaborn"):-len("Icon.png")]
        prev = os.path.join(a.previews, MODEL_OF.get(name, name) + "_day.png")
        cells.append(cell(prev if os.path.isfile(prev) else None, png,
                          "%s / %s" % (MODEL_OF.get(name, name) if os.path.isfile(prev) else "no model", name), f))
    os.makedirs(a.out, exist_ok=True)
    for k in range(0, len(cells), 6):
        part = cells[k:k + 6]
        sh = Image.new("RGB", (3 * 610, ((len(part) + 2) // 3) * 380), (20, 30, 25))
        for i, c in enumerate(part):
            sh.paste(c, ((i % 3) * 610, (i // 3) * 380))
        sh.save(os.path.join(a.out, "models_%d.png" % (k // 6 + 1)))
    print(len(cells), "pairs ->", a.out)


if __name__ == "__main__":
    main()
