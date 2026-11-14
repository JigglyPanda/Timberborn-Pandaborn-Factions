"""Game-zoom contact sheet: every model at one fixed scale (about 110 px per tile, orthographic), from the high game
camera angle, by day, with names underneath, grouped so models a player must tell apart sit side by side.

    python -I src/pipeline/kit/game_zoom.py [--pitch 55] [--yaw 25] [--ppu 110] [--jobs 4] [--top] [Id ...]

Meshes come from E:\\PandabornDev\\build\\models\\<Id> (run the build.py files first). Output:
E:\\PandabornDev\\build\\models\\preview\\gamezoom\\<Id>.png and ..\\sheet_gamezoom.png (with --top: a near top-down
row too, sheet_gamezoom_top.png).
"""
import argparse
import concurrent.futures as cf
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import preview  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
ART = os.path.join(ROOT, "art", "models")
MODELS = r"E:\PandabornDev\build\models"
OUT = os.path.join(MODELS, "preview", "gamezoom")

GROUPS = [
    ("Workplaces", ["Steamer", "PickleYard", "TeaRoastery", "LanternWorkshop", "HotPotHall", "Kitchen", "SmokeKiln",
                    "TripHammerMill", "OxWorkshop", "PaddyHouse", "Teahouse", "InkStudio", "StarTower",
                    "NightBuildersPost", "NightCourierPost", "NightForagersPost", "DewCollector"]),
    ("Power and water", ["KiteWindmill", "LargeKiteWindmill", "BambooWaterWheel", "TreadwheelLift", "ScoopWheel",
                         "PaddySpout", "CisternTap", "Cistern", "CisternMedium", "CisternLarge", "Flume", "FlumeGate",
                         "FlumeBridge", "FlumeBridgeSpan", "FlumeDrop", "FlumeCorner"]),
    ("Homes and civic", ["Den", "MoonLoft", "CourtyardHouse", "TerraceHouse", "Kindergarten", "VillageHall",
                         "Hammock", "NapPlatform"]),
    ("Leisure and monuments", ["FestivalSquare", "OperaStage", "HotSpringBath", "SlideAndSwing", "MemorialArch",
                               "GreatSittingPanda", "SkyLantern"]),
    ("Decoration", ["StandingLantern", "HangingLantern", "StringLanterns", "PandaStatue", "PottedPine", "GoldfishBowl",
                    "GardenMoonGate", "BambooPinwheel", "BambooFence", "DryStoneWall"]),
]


def mesh(mid):
    p = os.path.join(MODELS, mid, f"{mid}.Model.timbermesh")
    if not os.path.exists(p):   # modular pieces (fence, wall) keep their straight variant
        alts = sorted(glob.glob(os.path.join(MODELS, mid, f"{mid}0101.Model.timbermesh"))
                      + glob.glob(os.path.join(MODELS, mid, f"{mid}*.Model.timbermesh")))
        alts = [a for a in alts if "ConstructionStage" not in a]
        p = alts[0] if alts else None
    return p


def one(mid, a, tag):
    p = mesh(mid)
    if not p:
        return mid, None
    name = mid + tag
    preview.render(p, None, OUT, name, yaw=a.yaw, pitch=a.top_pitch if tag else a.pitch, samples=20, night=False,
                   ppu=a.ppu)
    return mid, os.path.join(OUT, name + "_day.png")


def sheet(out, groups, done):
    from PIL import Image, ImageDraw
    W = 2400
    rows, x, y, rh = [], 0, 0, 0
    placed = []
    for title, ids in groups:
        ims = [(i, done[i]) for i in ids if done.get(i)]
        if not ims:
            continue
        if x:
            y += rh
            x, rh = 0, 0
        placed.append(("title", title, 0, y))
        y += 34
        for i, p in ims:
            im = Image.open(p).convert("RGB")
            if x + im.width > W:
                y += rh
                x, rh = 0, 0
            placed.append(("img", (i, im), x, y))
            x += im.width + 8
            rh = max(rh, im.height + 26)
    y += rh
    canvas = Image.new("RGB", (W, y + 8), (34, 34, 34))
    d = ImageDraw.Draw(canvas)
    for kind, v, px, py in placed:
        if kind == "title":
            d.text((px + 8, py + 10), v, fill=(255, 220, 120))
        else:
            i, im = v
            canvas.paste(im, (px, py))
            d.text((px + 4, py + im.height + 6), i, fill=(240, 240, 240))
    canvas.save(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--pitch", type=float, default=55.0)
    ap.add_argument("--top-pitch", type=float, default=80.0)
    ap.add_argument("--yaw", type=float, default=25.0)
    ap.add_argument("--ppu", type=float, default=110.0)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--top", action="store_true")
    ap.add_argument("--no-render", action="store_true")
    a = ap.parse_args()
    every = sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(ART, "*", "build.py")))
    grouped = [i for _, ids in GROUPS for i in ids]
    groups = GROUPS + [("Other", [i for i in every if i not in grouped])]
    ids = a.ids or every
    os.makedirs(OUT, exist_ok=True)
    for tag, out in (("", "sheet_gamezoom.png"), ("_top", "sheet_gamezoom_top.png")):
        if tag and not a.top:
            continue
        if not a.no_render:
            with cf.ThreadPoolExecutor(a.jobs) as ex:
                for mid, res in ex.map(lambda i: one(i, a, tag), ids):
                    print(mid, res)
        done = {i: os.path.join(OUT, i + tag + "_day.png") for i in every
                if os.path.exists(os.path.join(OUT, i + tag + "_day.png"))}
        print(sheet(os.path.join(MODELS, "preview", out), groups, done))


if __name__ == "__main__":
    main()
