"""Measures the extracted vanilla clips (vanilla_extract.py) so our sounds can be matched to them.

Writes <ref>/report.json (every decoded clip) and, for the reference set below, spectrogram PNGs into <ref>/png and a
markdown table on stdout. Everything stays on E: (game audio is never committed).

  python -I src/pipeline/sound/vanilla_report.py [--ref E:/PandabornDev/reference/vanilla-sounds]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analysis as A  # noqa: E402

# kind -> clips that our sounds of that kind are compared with
REFERENCE = {
    "building loop": ["Environment.Buildings.Loop.WaterWheel", "Environment.Buildings.Loop.Gristmill",
                      "Environment.Buildings.Loop.Grill", "Environment.Buildings.Loop.Bakery",
                      "Environment.Buildings.Loop.PaperMill", "Environment.Buildings.Loop.WaterPump",
                      "Environment.Buildings.Loop.LumberMill", "Environment.Buildings.Loop.GearWorkshop",
                      "Environment.Buildings.Loop.WateringPlace", "Environment.Buildings.ShaftWorking",
                      "Environment.Buildings.Fire"],
    "attraction loop": ["Environment.Buildings.Loop.DanceHall", "Environment.Buildings.Loop.Agora",
                        "Environment.Buildings.Loop.Carousel"],
    "ambient": ["Environment.Ambient.Water", "Environment.Ambient.Day", "Environment.Ambient.Night",
                "Environment.Ambient.Wind"],
    "one-shot (world)": ["Environment.Buildings.BellToll", "Environment.Fireworks.Trail_01",
                         "Environment.Fireworks.Burst_01", "Environment.Fireworks.BigBurst_01",
                         "Environment.Buildings.Speaker.Chime_01", "Environment.Buildings.DynamiteExplosion"],
    "UI": ["UI.Buildings.Wonder.EarthRecultivator", "UI.Buildings.Wonder.EarthRepopulator",
           "UI.Buildings.Wonder.Congratulations", "UI.Buildings.Selected.Bell", "UI.Buildings.Selected.DistrictCenter",
           "UI.Buildings.Selected.WaterWheel", "UI.Buildings.Selected.Bakery", "UI.Beavers.Common.Selected.Adult_Content_01",
           "UI.Beavers.Common.Selected.Adult_Content_02", "UI.Beavers.Common.Selected.Child_Content_01",
           "UI.Beavers.Common.Selected.Adult_Sleeping_01", "UI.Bots.Selected.Timberbot_Content_01",
           "UI.BasicSelection.Tree", "UI.BasicSelection.Bush", "UI.Click", "UI.Weather.DroughtStarted"],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default=r"E:\PandabornDev\reference\vanilla-sounds")
    a = ap.parse_args()
    meta = json.load(open(os.path.join(a.ref, "clips.json"), encoding="utf-8"))
    loops = set(REFERENCE["building loop"] + REFERENCE["attraction loop"] + REFERENCE["ambient"])
    report = {}
    for n in sorted(meta):
        p = os.path.join(a.ref, n + ".wav")
        if not os.path.isfile(p):
            continue
        x, sr = A.read_wav(p)
        is_loop = n in loops or ".Loop." in n
        r = A.measure(x, sr, loop=is_loop)
        r["import"] = meta[n]
        report[n] = r
    with open(os.path.join(a.ref, "report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    png = os.path.join(a.ref, "png")
    os.makedirs(png, exist_ok=True)
    print("| kind | clip | s | LUFS-I | M max | S max | peak dBFS | centroid Hz | presence+air | load |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for kind, names in REFERENCE.items():
        for n in names:
            if n not in report:
                print("| %s | %s | missing | | | | | | | |" % (kind, n))
                continue
            r = report[n]
            x, sr = A.read_wav(os.path.join(a.ref, n + ".wav"))
            A.spectrogram_png(x, sr, os.path.join(png, n + ".png"), "vanilla " + n, loop=n in loops)
            print("| %s | %s | %.2f | %.1f | %.1f | %.1f | %.1f | %d | %.2f | %s |" % (
                kind, n, r["seconds"], r["lufs_integrated"], r["lufs_momentary_max"], r["lufs_short_term_max"],
                r["peak_db"], r["centroid_hz"], r["bands"]["presence"] + r["bands"]["air"], r["import"]["loadType"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
