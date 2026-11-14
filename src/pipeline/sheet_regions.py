"""Region map of the vanilla Folktails trim sheets (which rectangle of each 1024 x 1024 sheet is which surface) and
the texel density the vanilla models use on each material. This is what new Inkpaws models UV against, and what the
Blender bake lays its geometry into.

Inputs (reference only, never committed): E:\\PandabornDev\\reference\\vanilla-assets\\{textures,material_usage.json}
and the game's resources.assets (for the texel density pass).
Outputs:
  src/pipeline/sheet_regions.json                     committed: rectangles per sheet (pixels, top-left origin)
  E:\\PandabornDev\\build\\look\\preview\\regions_<sheet>.png  each sheet's rectangles drawn over our current albedo

Usage: python -I src/pipeline/sheet_regions.py [--density <Timberborn_Data>]
Rectangles are [x0, y0, x1, y1) in pixels of a 1024 sheet, y down (image rows). UV: u = x / 1024, v = 1 - y / 1024.
"""
import argparse
import collections
import gzip
import json
import os
import struct
import sys
import zlib

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
REF = r"E:\PandabornDev\reference\vanilla-assets"
VT = os.path.join(REF, "textures")
PREVIEW = r"E:\PandabornDev\build\look\preview"
OURS = r"E:\PandabornDev\unity\PandabornLook\Assets\PandabornLook\Textures"
S = 1024


def load(name, mode="RGB"):
    return np.asarray(Image.open(os.path.join(VT, name + ".png")).convert(mode)).astype(np.float32) / 255.0


def comps(mask, min_px=400):
    lab, _ = ndi.label(mask)
    out = []
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        if sl is None or (lab[sl] == i).sum() < min_px:
            continue
        out.append([int(sl[1].start), int(sl[0].start), int(sl[1].stop), int(sl[0].stop)])
    return sorted(out, key=lambda r: (r[1] // 64, r[0]))


def basewood():
    """Measured from BaseWood_1K_D_White (64 px strip pitch; each strip has ~4 px of gap on either side)."""
    regions = [{"rect": [0, 0, 512, 500], "kind": "long-grain block (long faces of beams and logs)"}]
    groups = [([512, 0, 768, 505], 4), ([768, 0, 1024, 125], 4), ([768, 128, 1024, 505], 4),
              ([0, 512, 512, 1024], 8), ([512, 512, 768, 765], 4), ([768, 512, 1024, 765], 4)]
    for (x0, y0, x1, y1), n in groups:
        pitch = (x1 - x0) // n
        for i in range(n):
            regions.append({"rect": [x0 + i * pitch + 4, y0 + 4, x0 + (i + 1) * pitch - 4, y1 - 4],
                            "kind": "plank strip %dx%d px, grain vertical" % (pitch - 8, y1 - y0 - 8)})
    regions += [
        {"rect": [512, 768, 640, 896], "kind": "end-grain disc, with hole (peg / hollow)"},
        {"rect": [640, 768, 768, 896], "kind": "end-grain disc, rings"},
        {"rect": [512, 896, 640, 1024], "kind": "end-grain disc, broken / splintered"},
        {"rect": [640, 896, 768, 960], "kind": "end-grain disc, small"},
        {"rect": [640, 960, 768, 1024], "kind": "end-grain disc, small"},
        {"rect": [768, 768, 1024, 1024], "kind": "plain fill (no grain)"},
    ]
    return regions


def planks():
    v = load("IrregularPlanks_D_White")
    lum = v.mean(2)
    col = ndi.uniform_filter1d(lum.mean(0), 9)
    # plank seams = darkest columns, roughly every 128 px
    seams = [0]
    for c in range(64, S, 128):
        lo, hi = c + 32, min(c + 96, S)
        seams.append(int(lo + np.argmin(col[lo:hi])))
    seams = sorted(set(seams))[:9]
    seams.append(S)
    return [{"rect": [seams[i], 0, seams[i + 1], S], "kind": "plank %d (full height, grain vertical)" % (i + 1)}
            for i in range(len(seams) - 1) if seams[i + 1] - seams[i] > 40]


def thatch():
    out = []
    for k in range(4):
        y_edge = 200 + 256 * k                      # lower edge of a course (strand tips), course hangs above it
        y0 = y_edge - 256
        out.append({"rect": [0, max(y0, 0), S, y_edge], "kind": "roof course %d (lower edge at bottom, slope runs up)" % (k + 1)})
    out.append({"rect": [0, 968, S, S], "kind": "top of course 1 continued (sheet tiles vertically)"})
    return out


def windows():
    """Measured from WindowsAtlas_D/E.Folktails. Glass = where the vanilla _LightingMap is bright."""
    return [
        {"rect": [0, 0, 256, 256], "kind": "round window, framed, with inner ring"},
        {"rect": [256, 0, 512, 256], "kind": "round window, framed"},
        {"rect": [0, 256, 256, 512], "kind": "round window, framed, with inner ring (2)"},
        {"rect": [256, 256, 512, 512], "kind": "round window, framed, one mullion"},
        {"rect": [0, 512, 512, 1024], "kind": "doorway interior: dark, with a soft glow gradient at night"},
        {"rect": [544, 32, 640, 200], "kind": "small tall window"},
        {"rect": [672, 32, 960, 160], "kind": "long window, four lights"},
        {"rect": [544, 256, 992, 496], "kind": "arched window with mullions"},
        {"rect": [768, 512, 1024, 768], "kind": "porthole / round light in a dark frame"},
        {"rect": [768, 768, 1024, 1024], "kind": "glass / light panel, vertical gradient"},
        {"rect": [512, 512, 768, 1024], "kind": "plain wall"},
        {"rect": [0, 0, 1024, 1024], "kind": "background = wall around windows (flat)", "background": True},
    ]


def details():
    return [
        {"rect": [0, 0, 512, 512], "kind": "banner cloth (faction emblem)"},
        {"rect": [512, 0, 768, 512], "kind": "sack"},
        {"rect": [768, 0, 832, 512], "kind": "rope (vertical)"},
        {"rect": [832, 0, 1024, 170], "kind": "good label 1 (red in vanilla: planks)"},
        {"rect": [832, 170, 1024, 340], "kind": "good label 2 (green: logs)"},
        {"rect": [832, 340, 1024, 512], "kind": "good label 3 (purple: berries)"},
        {"rect": [0, 512, 256, 768], "kind": "crate side with X brace"},
        {"rect": [256, 512, 512, 768], "kind": "crate side with X brace (2)"},
        {"rect": [0, 768, 256, 1024], "kind": "crate lid / framed panel"},
        {"rect": [256, 768, 512, 1024], "kind": "plain planks, horizontal"},
        {"rect": [512, 512, 1024, 1024], "kind": "vertical planks with two metal bands (now cane lashing)"},
    ]


def paper():
    v = load("Paper_D.Folktails")
    lum = v.mean(2)
    lines = ndi.binary_dilation((ndi.gaussian_filter(lum, 6) - lum) > 0.05, iterations=2)
    return [{"rect": r, "kind": "paper panel inside a frame"} for r in comps(~lines, 4000)]


def metal():
    vn = load("BaseMetal_N", "RGBA")
    dev = np.sqrt((vn[..., 3] - 0.5) ** 2 + (vn[..., 1] - 0.5) ** 2)
    seams = ndi.binary_dilation(ndi.gaussian_filter(dev, 1.0) > 0.12, iterations=2)
    return [{"rect": r, "kind": "plate"} for r in comps(~seams, 3000)]


def painted():
    v = load("PaintedMetal_D.Folktails")
    y = (v[..., 0] > 0.55) & (v[..., 1] > 0.45) & (v[..., 2] < 0.35)
    cols = ndi.binary_closing(y.mean(0) > 0.3, iterations=6)
    lab, n = ndi.label(cols)
    out = []
    for i in range(1, n + 1):
        xs = np.nonzero(lab == i)[0]
        out.append({"rect": [int(xs[0]), 0, int(xs[-1]) + 1, S], "kind": "stripe (yellow in vanilla, cane binding in ours)"})
    return out


SHEETS = {
    "BaseWood": (basewood, ["BaseWood_Brown", "BaseWood_White", "BaseWood_LightBrown", "BaseWood_Yellow"], "Timber (Brown), Bamboo (White, LightBrown, Yellow)"),
    "IrregularPlanks": (planks, ["IrregularPlanks_*"], "Weave (White, LightBrown, Yellow), WeaveCoarse (Brown), WeaveMossy (Mossy)"),
    "ThatchedRoof": (thatch, ["ThatchedRoof"], "RoofTiles"),
    "WindowsAtlas": (windows, ["WindowsAtlas"], "Windows"),
    "Details": (details, ["Details"], "Details"),
    "Paper": (paper, ["Paper"], "LatticePaper"),
    "BaseMetal": (metal, ["BaseMetal"], "Iron"),
    "PaintedMetal": (painted, ["PaintedMetal"], "Banded"),
}


# ------------------------------------------------------------------------------------------------ texel density
def density(data_dir):
    sys.path.insert(0, HERE)
    import UnityPy  # noqa: E402
    import model_pb2 as pb  # noqa: E402
    dt = {4: np.float32}
    env = UnityPy.load(os.path.join(data_dir, "resources.assets"))
    per = collections.defaultdict(list)
    for o in env.objects:
        if o.type.name != "MonoBehaviour":
            continue
        raw = o.get_raw_data()
        if len(raw) < 40 or struct.unpack_from("<i", raw, 28)[0] != 0:
            continue
        n = struct.unpack_from("<i", raw, 32)[0]
        blob = raw[36:36 + n]
        if n < 16 or (blob[:1] != b"\x78" and blob[:2] != b"\x1f\x8b"):
            continue
        try:
            data = gzip.decompress(blob) if blob[:2] == b"\x1f\x8b" else zlib.decompress(blob)
            m = pb.Model()
            m.ParseFromString(data)
        except Exception:  # noqa: BLE001
            continue
        for node in m.nodes:
            props = {p.name: p for p in node.vertexProperties}
            if "position" not in props or "uv0" not in props:
                continue
            pos = np.frombuffer(props["position"].data, np.float32).reshape(-1, 3)
            uv = np.frombuffer(props["uv0"].data, np.float32).reshape(-1, 2)
            for mesh in node.meshes:
                if not mesh.material.endswith(".Folktails"):
                    continue
                idx = np.array(mesh.indices).reshape(-1, 3)
                if len(idx) == 0:
                    continue
                p, t = pos[idx], uv[idx]
                wa = 0.5 * np.linalg.norm(np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]), axis=1)
                e1, e2 = t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]
                ta = 0.5 * np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0])
                ok = (wa > 1e-4) & (ta > 1e-9)
                d = np.sqrt(ta[ok] / wa[ok]) * S
                per[mesh.material].append(np.repeat(d, np.maximum((wa[ok] * 100).astype(int), 1)))
    out = {}
    for mat, arrs in per.items():
        a = np.concatenate(arrs)
        out[mat.replace(".Folktails", "")] = {"medianPxPerTile": round(float(np.median(a)), 1),
                                              "p10": round(float(np.percentile(a, 10)), 1),
                                              "p90": round(float(np.percentile(a, 90)), 1)}
    return out


DENSITY_KEYS = {"BaseWood": ["BaseWood_Brown", "BaseWood_White", "BaseWood_LightBrown", "BaseWood_Yellow"],
                "IrregularPlanks": ["IrregularPlanks_White", "IrregularPlanks_Brown", "IrregularPlanks_LightBrown"],
                "ThatchedRoof": ["ThatchedRoof"], "WindowsAtlas": ["WindowsAtlas"], "Details": ["Details"],
                "Paper": ["Paper"], "BaseMetal": ["BaseMetal"], "PaintedMetal": ["PaintedMetal"]}


def write_markdown(result, path):
    td = result.get("texelDensity", {})
    lines = ["# Trim-sheet region map", "",
             "Generated by `src/pipeline/sheet_regions.py` from the vanilla Folktails sheets; do not edit by hand.",
             "Every sheet is 1024 x 1024. Rectangles are `[x0, y0, x1, y1)` in pixels with y **down** (image rows);",
             "in UV terms u = x / 1024, v = 1 - y / 1024. New Inkpaws models UV onto these rectangles and use the vanilla",
             "material names; in an Inkpaws game `Pandaborn.Look` swaps our textures in, so the same UVs show our surfaces.",
             "Texel density: what the vanilla models use (median over every triangle, weighted by area; p10-p90 in",
             "brackets), in texture pixels per world tile (1 tile = 1 block). Aim new models at the median.", ""]
    for sheet, v in result["sheets"].items():
        dens = ["`%s` %s (%s-%s)" % (k, td[k]["medianPxPerTile"], td[k]["p10"], td[k]["p90"])
                for k in DENSITY_KEYS.get(sheet, []) if k in td]
        lines += ["## %s" % sheet, "",
                  "Materials: %s. Our texture sets: %s. Density: %s." % (
                      ", ".join("`%s.Folktails`" % m for m in v["materials"]), v["ourSet"], "; ".join(dens) or "n/a"),
                  "", "| # | Rect [x0, y0, x1, y1) | Surface |", "|---|---|---|"]
        for i, r in enumerate(v["regions"]):
            lines.append("| %s | %s | %s |" % ("–" if r.get("background") else i,
                                               "whole sheet" if r.get("background") else r["rect"], r["kind"]))
        lines.append("")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--density", default="")
    a = ap.parse_args()
    os.makedirs(PREVIEW, exist_ok=True)
    result = {"note": "pixels of a 1024 sheet, [x0, y0, x1, y1), y down; u = x/1024, v = 1 - y/1024", "sheets": {}}
    old = {}
    path = os.path.join(HERE, "sheet_regions.json")
    if os.path.exists(path):
        old = json.load(open(path, encoding="utf-8"))
    for sheet, (fn, mats, ourset) in SHEETS.items():
        regions = fn()
        result["sheets"][sheet] = {"materials": mats, "ourSet": ourset, "regions": regions}
        src = os.path.join(OURS, "PBLook_%s_D.png" % ourset.split(" ")[0])
        im = Image.open(src).convert("RGB") if os.path.exists(src) else Image.new("RGB", (S, S), (90, 90, 90))
        d = ImageDraw.Draw(im)
        for i, r in enumerate(regions):
            if r.get("background"):
                continue
            d.rectangle(r["rect"], outline=(255, 0, 255), width=3)
            d.text((r["rect"][0] + 6, r["rect"][1] + 4), str(i), fill=(255, 0, 255))
        im.save(os.path.join(PREVIEW, "regions_%s.png" % sheet))
    if a.density:
        result["texelDensity"] = density(a.density)
    elif "texelDensity" in old:
        result["texelDensity"] = old["texelDensity"]
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(result, fh, indent=1)
    write_markdown(result, os.path.join(HERE, "..", "..", "docs", "tech", "look-regions.md"))
    for sheet, v in result["sheets"].items():
        print(sheet, len(v["regions"]), "regions")
    if "texelDensity" in result:
        for k, v in sorted(result["texelDensity"].items()):
            print(f"  {k:28s} {v}")


if __name__ == "__main__":
    main()
