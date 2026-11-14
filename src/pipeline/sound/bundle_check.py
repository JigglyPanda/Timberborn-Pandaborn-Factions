"""Checks a built pandabornsounds bundle against the WAVs it was made from, by decoding what the game will decode.

For every AudioClip in the bundle (UnityPy reads the bundle, fmod_toolkit decodes its FSB5/ADPCM data, both in the E:
venv): the import settings (load type, compression, channels, rate, preload), the decoded length against the source WAV
(a loop that grew by an encoder's padding would click or gap at the seam), loudness and peak after compression, and for
loops the seam measures of analysis.loop_stats on the *decoded* audio. Writes <out>/bundle_check_<bundle>.json and
prints a table; exit code 1 on any failure.

  python -I src/pipeline/sound/bundle_check.py E:/PandabornDev/build/sound/AssetBundles/pandabornsounds_win
"""
import argparse
import io
import json
import os
import sys
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True

import numpy as np  # noqa: E402

import analysis as A  # noqa: E402

LOAD = {0: "DecompressOnLoad", 1: "CompressedInMemory", 2: "Streaming"}
COMP = {0: "PCM", 1: "Vorbis", 2: "ADPCM", 3: "MP3"}


def decode(wav_bytes):
    with wave.open(io.BytesIO(wav_bytes), "rb") as w:
        ch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if sw == 2:
        x = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif sw == 4:
        x = np.frombuffer(raw, dtype="<f4").astype(np.float64)
    else:
        raise ValueError("sample width %d" % sw)
    return x.reshape(-1, ch), sr


def loop_kind(report, name):
    return report.get(name, {}).get("kind") == "loop"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle")
    ap.add_argument("--wav", default=r"E:\PandabornDev\build\sound\wav")
    ap.add_argument("--out", default=r"E:\PandabornDev\build\sound")
    a = ap.parse_args()
    import UnityPy

    report = json.load(open(os.path.join(a.out, "report.json"), encoding="utf-8"))
    env = UnityPy.load(a.bundle)
    rows, fails = {}, 0
    for path, obj in sorted(env.container.items()):
        if obj.type.name != "AudioClip":
            continue
        clip = obj.read()
        name = clip.m_Name
        r = {"path": path, "loadType": LOAD.get(clip.m_LoadType), "compression": COMP.get(clip.m_CompressionFormat),
             "channels": clip.m_Channels, "rate": clip.m_Frequency, "preload": bool(clip.m_PreloadAudioData)}
        problems = []
        src_path = os.path.join(a.wav, name + ".wav")
        if not os.path.isfile(src_path):
            problems.append("no source WAV")
        x, sr = decode(next(iter(clip.samples.values())))
        src, ssr = A.read_wav(src_path)
        r["decodedSamples"], r["sourceSamples"] = int(x.shape[0]), int(src.shape[0])
        if x.shape[0] != src.shape[0]:
            # ADPCM pads to a whole 64-sample block: harmless after a one-shot's silent tail, a gap in a loop
            extra = x.shape[0] - src.shape[0]
            tail = float(np.max(np.abs(x[src.shape[0]:]))) if extra > 0 else 1.0
            if loop_kind(report, name) or not (0 < extra < 64 and tail < 1e-3):
                problems.append("length %d samples, source %d" % (x.shape[0], src.shape[0]))
            else:
                r["paddedSilentSamples"] = extra
        if sr != ssr:
            problems.append("rate %d vs %d" % (sr, ssr))
        loop = report.get(name, {}).get("kind") == "loop"
        m = A.measure(x if x.shape[1] > 1 else x[:, 0], sr, loop=loop)
        ref = report.get(name, {}).get("measure", {})
        r["lufs"], r["lufsSource"] = m["lufs_integrated"], ref.get("lufs_integrated")
        r["truePeak"], r["truePeakSource"] = m["true_peak_db"], ref.get("true_peak_db")
        if ref and abs(m["lufs_integrated"] - ref["lufs_integrated"]) > 0.5:
            problems.append("loudness changed by %.2f LU" % (m["lufs_integrated"] - ref["lufs_integrated"]))
        if m["true_peak_db"] > 0.0:
            problems.append("true peak %.2f dBTP after encoding" % m["true_peak_db"])
        if loop:
            lp = m["loop"]
            r["seamStep"], r["seamRms"] = lp["seam_jump_vs_p99.9_step"], lp["seam_rms_vs_median"]
            if lp["seam_jump_vs_p99.9_step"] > 1.0:
                problems.append("seam step %.2f x the 99.9th-percentile step" % lp["seam_jump_vs_p99.9_step"])
        if r["loadType"] != "CompressedInMemory" or not r["preload"]:
            problems.append("import settings %s preload=%s" % (r["loadType"], r["preload"]))
        r["problems"] = problems
        fails += bool(problems)
        rows[name] = r
        print("%-58s %-18s %-6s %dch %6d Hz  %7.2f LUFS (src %7.2f)  %s" % (
            name, r["loadType"], r["compression"], r["channels"], r["rate"], r["lufs"], r["lufsSource"] or 0,
            "; ".join(problems) if problems else ("seam %.2f" % r["seamStep"] if loop else "ok")))
    missing = sorted(set(report) - set(rows))
    if missing:
        fails += len(missing)
        print("missing from the bundle: " + ", ".join(missing))
    out = os.path.join(a.out, "bundle_check_%s.json" % os.path.basename(a.bundle))
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"bundle": a.bundle, "bytes": os.path.getsize(a.bundle), "clips": rows, "missing": missing}, f, indent=1)
    print("%d clips, %d with problems, %d missing -> %s" % (len(rows), fails - len(missing), len(missing), out))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
