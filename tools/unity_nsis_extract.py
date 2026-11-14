"""Unpacks a Unity target-support installer (UnitySetup-<Platform>-Support-for-Editor-<version>.exe) without running it.

Used to give the private editor copy on E: its Mac Build Support (docs/tech/mac.md). No elevation, no registry, no
installer code runs: the script only reads the file.

Unity builds these installers with its own NSIS ("Nullsoft Install System v15-May-2025.cvs", first-header flags 0x70),
which 7-Zip 26.06 cannot open. Its layout, worked out from the 6000.5.11f1 Mac Mono installer:
  * the NSIS first header (flags, 0xDEADBEEF, "NullsoftInst", header length, total length) sits at a 512-byte
    boundary after the PE stub;
  * then an 8-byte uncompressed size, then the solid data stream as independent LZMA chunks:
    [3-byte LE compressed length][5-byte LZMA props][LZMA data with end marker], repeated;
  * the decompressed stream is standard NSIS solid data except that block lengths are 8 bytes:
    [u64 len][header][u64 len][file 1][u64 len][file 2]...;
  * header entries are 36 bytes (opcode + 8 params): EW_CREATEDIR = 11 (p0 path, p1 = set $OUTDIR),
    EW_EXTRACTFILE = 20 (p1 name, p2 | p3 << 32 data offset, p4 | p5 << 32 FILETIME); strings are UTF-16 with NSIS 3
    codes (1 lang, 2 shell, 3 var, 4 skip).
The install section does SetOutPath $INSTDIR\\Editor\\Data\\PlaybackEngines\\<Engine> and keeps that folder in a user
variable ($31 in the Mac installer), so every file under either prefix is written below <out>, keeping the tree.
Files of $PLUGINSDIR (the installer's own UI DLLs) are skipped.

Checks: the sum of the extracted sizes must equal the module's installedSize in Unity's release metadata (pass it with
--expect-bytes); Authenticode signatures of the signed Windows binaries inside can be checked afterwards.

usage: python -I tools/unity_nsis_extract.py <installer.exe> <out dir> --temp <scratch dir on E:> [--expect-bytes N]
"""
import argparse
import lzma
import os
import struct

ap = argparse.ArgumentParser()
ap.add_argument("installer")
ap.add_argument("out")
ap.add_argument("--temp", required=True, help="scratch folder for the ~2 GB decompressed stream (deleted afterwards)")
ap.add_argument("--expect-bytes", type=int, default=0)
a = ap.parse_args()


def find_first_header(f):
    pos = 0
    while True:
        f.seek(pos)
        b = f.read(28)
        if len(b) < 28:
            raise SystemExit("no NSIS first header found")
        if b[4:8] == b"\xef\xbe\xad\xde" and b[8:20] == b"NullsoftInst":
            return pos, b
        pos += 512


src = open(a.installer, "rb")
off, fh = find_first_header(src)
flags, _, = struct.unpack_from("<II", fh, 0)
hdrlen, total = struct.unpack_from("<II", fh, 20)
ulen = struct.unpack("<Q", src.read(8))[0]
print("first header at %d, flags 0x%x, total %d, declared data %d" % (off, flags, total, ulen))

os.makedirs(a.temp, exist_ok=True)
stream = os.path.join(a.temp, "nsis_stream.bin")
end = off + total
n = chunks = 0
with open(stream, "wb") as o:
    while src.tell() < end:
        lb = src.read(3)
        if len(lb) < 3:
            break
        clen = lb[0] | lb[1] << 8 | lb[2] << 16
        if clen == 0:
            break
        raw = src.read(clen)
        p = raw[0]
        d = lzma.LZMADecompressor(lzma.FORMAT_RAW, filters=[{
            "id": lzma.FILTER_LZMA1, "lc": p % 9, "lp": (p // 9) % 5, "pb": p // 45,
            "dict_size": struct.unpack_from("<I", raw, 1)[0]}])
        out = d.decompress(raw[5:])
        if not d.eof:
            raise SystemExit("LZMA chunk %d has no end marker: not the layout this script knows" % chunks)
        o.write(out)
        n += len(out)
        chunks += 1
print("%d LZMA chunks, %d bytes decompressed" % (chunks, n))

f = open(stream, "rb")
hl = struct.unpack("<Q", f.read(8))[0]
h = f.read(hl)
data0 = 8 + hl
blocks = [struct.unpack_from("<II", h, 4 + 8 * i) for i in range(8)]
eo, en = blocks[2]
S = h[blocks[3][0]:blocks[4][0]]


def dec(soff):
    b = S[soff * 2:]
    out, i = [], 0
    while i + 1 < len(b):
        c = b[i] | b[i + 1] << 8
        i += 2
        if c == 0:
            return "".join(out)
        if c in (1, 2, 3, 4):
            v = b[i] | b[i + 1] << 8
            i += 2
            out.append(chr(v) if c == 4 else "{%d:%d}" % (c, (v & 0x7F) | ((v >> 8) & 0x7F) << 7))
        else:
            out.append(chr(c))
    return None   # not a string offset


# $INSTDIR is variable 21; the engine folder is "$INSTDIR<var>" and then kept in another variable
engine_vars = set()
roots = []
for i in range(en):
    e = struct.unpack_from("<9I", h, eo + 36 * i)
    if e[0] == 11 and e[2]:
        pth = dec(e[1]) or ""
        if pth.startswith("{3:21}{3:") and pth.endswith("}") and pth.count("{") == 2:
            roots.append(pth)
    if e[0] == 27 and dec(e[2]) == "{3:22}":   # StrCpy $N $OUTDIR right after SetOutPath
        engine_vars.add("{3:%d}" % e[1])
roots += sorted(engine_vars)
print("install roots:", roots)

outdir, files, size, seen = None, 0, 0, set()
for i in range(en):
    e = struct.unpack_from("<9I", h, eo + 36 * i)
    if e[0] == 11 and e[2]:
        pth, outdir = dec(e[1]) or "", None
        for r in roots:
            if pth == r or pth.startswith(r + "\\"):
                outdir = pth[len(r):].lstrip("\\")
    elif e[0] == 20 and outdir is not None:
        name = dec(e[2])
        if name.startswith("{"):
            continue
        rel = os.path.join(outdir, name) if outdir else name
        if rel in seen:
            continue
        seen.add(rel)
        f.seek(data0 + (e[3] | e[4] << 32))
        ln = struct.unpack("<Q", f.read(8))[0]
        dst = os.path.join(a.out, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "wb") as o:
            left = ln
            while left:
                b = f.read(min(left, 1 << 24))
                o.write(b)
                left -= len(b)
        if e[5] != 0xFFFFFFFF:
            t = (e[5] | e[6] << 32) / 1e7 - 11644473600
            os.utime(dst, (t, t))
        files += 1
        size += ln
f.close()
os.remove(stream)
print("extracted %d files, %d bytes -> %s" % (files, size, a.out))
if a.expect_bytes and size != a.expect_bytes:
    raise SystemExit("size mismatch: expected %d bytes (installedSize), got %d" % (a.expect_bytes, size))
