"""Builds every Pandaborn sound: synthesize -> normalise -> check -> WAV + spectrogram + report.

  python -I src/pipeline/sound/build_sounds.py                       # all, into E:/PandabornDev/build/sound
  python -I src/pipeline/sound/build_sounds.py --only Bell,Clapper   # ids containing any of these
  python -I src/pipeline/sound/build_sounds.py --unity E:/PandabornDev/unity/PandabornSounds   # + copy into the Unity project
  python -I src/pipeline/sound/build_sounds.py --sync-only --unity <project>   # only copy the last build's WAVs

Output (never in git):
  <out>/wav/<clip>.wav     16-bit PCM, 48 kHz, mono (stereo where marked); clip = id, or id_01.. for variants
  <out>/png/<clip>.png     waveform, RMS envelope and spectrogram (loops: plus the first second again after the seam)
  <out>/report.json        every measurement and check, the slot each sound is for, the vanilla reference's numbers
  <out>/report.md          the same as a table
With --unity the WAVs are mirrored into <project>/Assets/PandabornSounds/Resources/Sounds/Pandaborn/ (stale ones removed)
and <project>/Assets/PandabornSounds/sounds_spec.json lists them for the bundle builder (PandabornSoundsBuilder).
Exit code 1 if any check fails.
"""
import argparse
import json
import os
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True  # -I ignores PYTHONDONTWRITEBYTECODE; keep the repo free of __pycache__

import numpy as np  # noqa: E402

import analysis as A  # noqa: E402
import sounds as SND  # noqa: E402
import synth as S  # noqa: E402


def clip_names(entry):
    if entry["variants"] <= 1:
        return [entry["id"]]
    return ["%s_%02d" % (entry["id"], i + 1) for i in range(entry["variants"])]


def render(job):
    idx, v, out_dir = job
    e = SND.SOUNDS[idx]
    name = clip_names(e)[v]
    loop = e["kind"] == "loop"
    y = np.asarray(e["fn"](v), dtype=np.float64)
    if e["channels"] == 1 and y.ndim == 2:
        y = y.mean(axis=1)
    if not loop:
        y = S.remove_dc(y)
    y = S.normalize_lufs(y, e["lufs"], A.integrated_lufs, ceiling_db=e["ceiling"], loop=loop)
    path = os.path.join(out_dir, "wav", name + ".wav")
    A.write_wav(path, y, S.SR)
    x, sr = A.read_wav(path)  # measure what was written (after dither and quantisation)
    m = A.measure(x if x.shape[1] > 1 else x[:, 0], sr, loop=loop)
    A.spectrogram_png(x if x.shape[1] > 1 else x[:, 0], sr, os.path.join(out_dir, "png", name + ".png"),
                      "%s  (%s, target %.0f LUFS)" % (name, e["kind"], e["lufs"]), loop=loop)
    return idx, v, name, m


def checks(e, m):
    out = []

    def add(name, ok, detail):
        out.append({"check": name, "ok": bool(ok), "detail": detail})

    add("loudness", abs(m["lufs_integrated"] - e["lufs"]) <= 0.8, "%.2f LUFS vs target %.1f" % (m["lufs_integrated"], e["lufs"]))
    add("truePeak", m["true_peak_db"] <= e["ceiling"] + 0.6, "%.2f dBTP vs ceiling %.1f" % (m["true_peak_db"], e["ceiling"]))
    add("noClipping", m["clipped_samples"] == 0, "%d clipped samples" % m["clipped_samples"])
    add("dc", abs(m["dc"]) < 0.002, "DC %.5f" % m["dc"])
    add("notShrill", m["bands"]["presence"] + m["bands"]["air"] < 0.45,
        "presence+air share %.2f" % (m["bands"]["presence"] + m["bands"]["air"]))
    if e["kind"] == "loop":
        lp = m["loop"]
        add("loopSeamStep", lp["seam_jump_vs_p99.9_step"] <= 1.0,
            "seam step %.3f x the 99.9th-percentile step" % lp["seam_jump_vs_p99.9_step"])
        add("loopSeamLevel", 0.25 <= lp["seam_rms_vs_median"] <= 4.0,
            "10 ms RMS at the seam %.2f x the median" % lp["seam_rms_vs_median"])
        per, strength = lp["envelope_period_s"], lp["envelope_period_prominence"]
        expected = e.get("period")
        # an obvious short period: the envelope repeats (autocorrelation peak prominence > 0.35) faster than every 2 s,
        # unless it is the mechanism's own rhythm (a wheel's turn, a toss, a drum bar) declared in the registry
        if per is not None and strength is not None and strength > 0.35 and per < 2.0 and \
                not (expected and min(abs(per - expected * k) for k in (0.25, 0.5, 1, 2)) < 0.15):
            add("noShortPeriod", False, "envelope repeats every %.2f s (prominence %.2f)" % (per, strength))
        else:
            add("noShortPeriod", True, "most prominent envelope repeat %s s (prominence %s)%s" % (
                per, strength, "; expected mechanical period %.1f s" % expected if expected else ""))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=r"E:\PandabornDev\build\sound")
    ap.add_argument("--only", default="")
    ap.add_argument("--unity", default="")
    ap.add_argument("--ref", default=r"E:\PandabornDev\reference\vanilla-sounds\report.json")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--sync-only", action="store_true",
                    help="no synthesis: mirror the WAVs of the last build (report.json) into --unity")
    a = ap.parse_args()
    if a.sync_only:
        rpath = os.path.join(a.out, "report.json")
        if not a.unity or not os.path.isfile(rpath):
            print("--sync-only needs --unity and a previous build's %s" % rpath)
            return 1
        sync_unity(a.out, a.unity, json.load(open(rpath, encoding="utf-8")))
        return 0

    for d in ("wav", "png"):
        os.makedirs(os.path.join(a.out, d), exist_ok=True)
    only = [s for s in a.only.split(",") if s]
    jobs = []
    for i, e in enumerate(SND.SOUNDS):
        if only and not any(o.lower() in e["id"].lower() for o in only):
            continue
        for v in range(e["variants"]):
            jobs.append((i, v, a.out))
    ref = json.load(open(a.ref, encoding="utf-8")) if os.path.isfile(a.ref) else {}

    results = {}
    with ProcessPoolExecutor(max_workers=a.jobs) as ex:
        for idx, v, name, m in ex.map(render, jobs):
            results[name] = (idx, m)
            print("%-62s %6.1f LUFS  peak %6.1f  %5.2f s" % (name, m["lufs_integrated"], m["true_peak_db"], m["seconds"]))

    # report (merge with an existing one so --only keeps the others)
    rpath = os.path.join(a.out, "report.json")
    report = json.load(open(rpath, encoding="utf-8")) if (only and os.path.isfile(rpath)) else {}
    failed = 0
    for name, (idx, m) in sorted(results.items()):
        e = SND.SOUNDS[idx]
        cs = checks(e, m)
        failed += sum(1 for c in cs if not c["ok"])
        rv = ref.get(e["ref"]) if e.get("ref") else None
        report[name] = {"id": e["id"], "kind": e["kind"], "priority": e["priority"], "slot": e["slot"],
                        "target_lufs": e["lufs"], "ceiling_db": e["ceiling"], "measure": m, "checks": cs,
                        "reference": None if not rv else {"clip": e["ref"], "lufs_integrated": rv["lufs_integrated"],
                                                          "lufs_momentary_max": rv["lufs_momentary_max"],
                                                          "peak_db": rv["peak_db"], "centroid_hz": rv["centroid_hz"],
                                                          "seconds": rv["seconds"], "bands": rv["bands"]}}
    with open(rpath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    write_md(report, os.path.join(a.out, "report.md"))
    print("checks failed: %d (report %s)" % (failed, rpath))
    for name, r in sorted(report.items()):
        for c in r["checks"]:
            if not c["ok"]:
                print("  FAIL %s %s: %s" % (name, c["check"], c["detail"]))

    if a.unity:
        sync_unity(a.out, a.unity, report)
    return 1 if failed else 0


def write_md(report, path):
    lines = ["| clip | kind | s | LUFS-I | M max | true peak | centroid Hz | presence+air | loop seam (step x, rms x) | ref clip: LUFS / centroid | checks |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, r in sorted(report.items()):
        m = r["measure"]
        lp = m.get("loop")
        seam = "%.2f, %.2f" % (lp["seam_jump_vs_p99.9_step"], lp["seam_rms_vs_median"]) if lp else ""
        rf = r.get("reference")
        rs = "%s: %.1f / %d" % (rf["clip"].split(".")[-1], rf["lufs_integrated"], rf["centroid_hz"]) if rf else ""
        ok = all(c["ok"] for c in r["checks"])
        lines.append("| %s | %s | %.2f | %.1f | %.1f | %.1f | %d | %.2f | %s | %s | %s |" % (
            name, r["kind"], m["seconds"], m["lufs_integrated"], m["lufs_momentary_max"], m["true_peak_db"],
            m["centroid_hz"], m["bands"]["presence"] + m["bands"]["air"], seam, rs,
            "ok" if ok else "FAIL: " + ", ".join(c["check"] for c in r["checks"] if not c["ok"])))
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def sync_unity(out, project, report):
    dst = os.path.join(project, "Assets", "PandabornSounds", "Resources", "Sounds", "Pandaborn")
    os.makedirs(dst, exist_ok=True)
    wanted = {name + ".wav" for name in report}
    for f in os.listdir(dst):
        if f.endswith(".wav") and f not in wanted:
            os.remove(os.path.join(dst, f))
            if os.path.exists(os.path.join(dst, f + ".meta")):
                os.remove(os.path.join(dst, f + ".meta"))
    for name in sorted(report):
        src = os.path.join(out, "wav", name + ".wav")
        d = os.path.join(dst, name + ".wav")
        if not os.path.exists(d) or open(src, "rb").read() != open(d, "rb").read():
            shutil.copyfile(src, d)
    spec = {"clips": [{"file": "Assets/PandabornSounds/Resources/Sounds/Pandaborn/%s.wav" % n,
                       "loop": report[n]["kind"] == "loop",
                       "stereo": report[n]["measure"]["channels"] > 1} for n in sorted(report)]}
    with open(os.path.join(project, "Assets", "PandabornSounds", "sounds_spec.json"), "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=1)
    print("unity: %d clips in %s" % (len(spec["clips"]), dst))


if __name__ == "__main__":
    sys.exit(main())
