"""Extract the game's own AudioClips for measurement only (reference; never committed, never shipped).

Reads Timberborn_Data/resources.assets (+ resources.resource, FSB5/Vorbis) with UnityPy and fmod_toolkit (both in the
E: venv) and writes, outside the repo:
  <out>/<clip name>.wav        decoded PCM (music is skipped unless --music: long, and not a reference we match)
  <out>/clips.json             import settings of every clip: load type, channels, frequency, length, compression,
                               preload, legacy 3D, source size

Usage (E: venv, -I):
  python -I src/pipeline/sound/vanilla_extract.py [--game <Timberborn_Data>] [--out E:/PandabornDev/reference/vanilla-sounds]
"""
import argparse
import json
import os
import sys

LOAD_TYPES = {0: "DecompressOnLoad", 1: "CompressedInMemory", 2: "Streaming"}
COMPRESSION = {0: "PCM", 1: "Vorbis", 2: "ADPCM", 3: "MP3"}  # UnityEngine.AudioCompressionFormat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default=r"C:\Program Files (x86)\Steam\steamapps\common\Timberborn\Timberborn_Data")
    ap.add_argument("--out", default=r"E:\PandabornDev\reference\vanilla-sounds")
    ap.add_argument("--music", action="store_true", help="also decode the music tracks")
    a = ap.parse_args()

    import UnityPy  # noqa: E402  (venv only)

    os.makedirs(a.out, exist_ok=True)
    env = UnityPy.load(os.path.join(a.game, "resources.assets"))
    meta = {}
    written = 0
    for obj in env.objects:
        if obj.type.name != "AudioClip":
            continue
        c = obj.read()
        name = c.m_Name
        meta[name] = {
            "loadType": LOAD_TYPES.get(c.m_LoadType, c.m_LoadType),
            "channels": c.m_Channels,
            "frequency": c.m_Frequency,
            "length": round(float(c.m_Length), 4),
            "compression": COMPRESSION.get(c.m_CompressionFormat, c.m_CompressionFormat),
            "preload": bool(c.m_PreloadAudioData),
            "loadInBackground": bool(c.m_LoadInBackground),
            "legacy3D": bool(c.m_Legacy3D),
            "sourceBytes": int(c.m_Resource.m_Size),
        }
        if name.startswith("Music") and not a.music:
            continue
        try:
            samples = c.samples  # {name: wav bytes}
        except Exception as e:  # pragma: no cover - decoder issues are reported, not fatal
            meta[name]["decodeError"] = str(e)
            continue
        for _, data in samples.items():
            with open(os.path.join(a.out, name + ".wav"), "wb") as f:
                f.write(data)
            written += 1
            break
    with open(os.path.join(a.out, "clips.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1, sort_keys=True)
    print("clips: %d, wav written: %d -> %s" % (len(meta), written, a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
