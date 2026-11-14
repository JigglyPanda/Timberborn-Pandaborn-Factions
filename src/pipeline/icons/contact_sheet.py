"""Review sheets: our icons next to vanilla ones on the game's UI colours.

Writes into <out dir> (file names start with <name>, e.g. "goods"):
  <name>_sheet.png   a vanilla reference block, then ours at texture size, then everything at two smaller
                     display sizes on the inventory-slot and dark colours (first row vanilla, then ours)
  <name>_large.png   ours at 3x (nearest neighbour) with labels, to judge pixels
  <name>_blind.png   ours and vanilla shuffled together without labels: can you tell which are modded?

Usage: python -I contact_sheet.py <our icons dir> <vanilla icons dir> <out dir> [name]
Vanilla icons come from extract_vanilla_icons.py (E:\\PandabornDev\\reference\\vanilla-icons\\...); the vanilla dir
is searched recursively.
"""
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFont

PANEL = (34, 53, 42)        # UI/Images/Backgrounds/bg-3 (entity panel)
SLOT = (64, 70, 53)         # UI/Images/Backgrounds/bg-square-1 (inventory slot)
DARK = (20, 39, 35)         # bg-pixel-1
LABEL = (205, 208, 181)
# a spread of vanilla goods: raw, processed, materials, and the ones nearest to ours in subject
VANILLA_GOODS = ["berries", "bread", "carrot", "log", "plank", "treatedplank", "paper", "maplesyrup", "coffee",
                 "mushroom", "wheatflour", "fermentedmushroom", "potato", "grilledpotato", "soybean", "corn",
                 "chestnut", "gear", "metalblock", "fireworks"]


def _font(size):
    for f in ("arial.ttf", "segoeui.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _load(dirpath, recursive=False):
    out = []
    walk = os.walk(dirpath) if recursive else [(dirpath, [], os.listdir(dirpath))]
    for root, _, files in walk:
        for f in sorted(files):
            if f.lower().endswith(".png"):
                name = f[:-4]
                if name.lower().endswith("icon"):
                    name = name[:-4]
                out.append((name, Image.open(os.path.join(root, f)).convert("RGBA")))
    return sorted(out, key=lambda t: t[0].lower())


def _shrink(img, px):
    return img.resize((px, px), Image.LANCZOS)   # the game samples a trilinear mip chain; close enough


def _grid(items, cell, cols, bg, label_h=0, font=None, pad=8):
    rows = max(1, (len(items) + cols - 1) // cols)
    sheet = Image.new("RGBA", (cols * cell + 2 * pad, rows * (cell + label_h) + 2 * pad), bg + (255,))
    d = ImageDraw.Draw(sheet)
    for i, (name, im) in enumerate(items):
        x = pad + (i % cols) * cell
        y = pad + (i // cols) * (cell + label_h)
        sheet.alpha_composite(im, (x + (cell - im.width) // 2, y + (cell - im.height) // 2))
        if label_h and font:
            tw = d.textlength(name, font=font)
            d.text((x + (cell - tw) / 2, y + cell), name, fill=LABEL, font=font)
    return sheet


def _stack(parts, bg):
    w = max(p.width for p in parts)
    out = Image.new("RGBA", (w, sum(p.height for p in parts)), bg + (255,))
    y = 0
    for p in parts:
        out.alpha_composite(p, (0, y))
        y += p.height
    return out


def _title(text, width, bg, font):
    im = Image.new("RGBA", (width, 26), bg + (255,))
    ImageDraw.Draw(im).text((8, 5), text, fill=LABEL, font=font)
    return im


def make(ours_dir, vanilla_dir, out_dir, name="goods", sample=None):
    os.makedirs(out_dir, exist_ok=True)
    ours = [(n.replace("Pandaborn", ""), im) for n, im in _load(ours_dir)]
    if not ours:
        return
    vanilla_all = dict(_load(vanilla_dir, recursive=True))
    vanilla = [(n, vanilla_all[n]) for n in sample if n in vanilla_all] if sample else list(vanilla_all.items())
    vanilla = vanilla[:20]
    size = ours[0][1].width
    cell = size + 12
    cols = max(6, 920 // cell)
    W = cols * cell + 16
    f12, f14 = _font(12), _font(15)
    parts = [_title(f"Vanilla (reference, {size} px)", W, PANEL, f14),
             _grid(vanilla, cell, cols, PANEL, 16, f12),
             _title(f"Pandaborn ({size} px, texture size)", W, PANEL, f14),
             _grid(ours, cell, cols, PANEL, 16, f12)]
    for px, bg, label in ((size // 2, SLOT, "on the inventory slot colour"), (int(size * 0.35), DARK, "small")):
        n_v = (W - 16) // (px + 12)
        mix = [(n, _shrink(im, px)) for n, im in vanilla[:n_v]] + [(n, _shrink(im, px)) for n, im in ours]
        parts.append(_title(f"{px} px {label}: first row vanilla, then ours", W, bg, f14))
        parts.append(_grid(mix, px + 12, n_v, bg))
    _stack(parts, PANEL).convert("RGB").save(os.path.join(out_dir, f"{name}_sheet.png"))

    big = [(n, im.resize((im.width * 3, im.height * 3), Image.NEAREST)) for n, im in ours]
    _grid(big, size * 3 + 10, 6, PANEL, 20, f14).convert("RGB").save(os.path.join(out_dir, f"{name}_large.png"))

    rnd = random.Random(7)
    same = [(n, im) for n, im in vanilla_all.items() if im.width == size]
    pool = [im for _, im in ours] + [im for _, im in rnd.sample(same, min(len(ours), len(same)))]
    rnd.shuffle(pool)
    px = int(size * 0.6)
    _grid([("", _shrink(im, px)) for im in pool], px + 10, 12, SLOT).convert("RGB").save(
        os.path.join(out_dir, f"{name}_blind.png"))
    print(f"{name}: review sheets written to {out_dir}")


if __name__ == "__main__":
    make(*sys.argv[1:5])
