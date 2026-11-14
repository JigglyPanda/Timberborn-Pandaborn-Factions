"""Plant models: stages, the parts every plant is made of, colour grading, the build and the report.

A plant script (art/plants/<Id>/build.py) defines one function per stage that fills a Mesh, and calls Plant.build():

    p = Plant("PandabornTeaBush", kind="Bushes")
    p.stage("Seedling", seedling)            # seedling(m, state) with state in alive | dry | dead
    p.stage("Mature", mature)
    p.build()

For every stage it writes <Id><Stage>.timbermesh (alive), <Id><Stage>Dry and <Id><Stage>Dead to
E:\\PandabornDev\\build\\plants\\<Id>\\, plus <Id>MatureStump for trees (p.stump(fn)), and model.json beside the script with
everything the blueprint needs (see Plant.model_json). The node layout follows the vanilla plants exactly
(docs/tech/plants.md): one root node named like the file, one submesh, one material.
"""
import json
import math
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import atlas  # noqa: E402
import mesh as pm  # noqa: E402
from mesh import Mesh  # noqa: E402

BUILD = r"E:\PandabornDev\build\plants"
COLLECTION = "PandabornPlants.Inkpaws"
MATERIAL_ASSET_DIR = "Materials/Pandaborn/Plants"

# Vanilla triangle counts (E:\PandabornDev\reference\vanilla-plants\index.json), the budget reference per kind.
VANILLA = {
    "Crops": {"Seedling": (27, 141), "Mature": (57, 232)},
    "Bushes": {"Seedling": (37, 117), "Mature": (61, 198)},
    "Trees": {"Seedling": (40, 153), "Mature": (126, 285), "MatureStump": (18, 48)},
}

# ------------------------------------------------------------------------------------------- colour
# Vertex colours multiply the near-grey atlas (leaves about 0.8). Vanilla leaves sit at about (0.21, 0.29, 0.12) after
# the multiply; ours stay in that value range so they sit with birch, pine and chestnut, each with its own hue.
DRY = np.array([1.55, 1.12, 0.62])      # multiplies a fresh green toward straw
DEAD = np.array([1.35, 0.98, 0.78])


def state_tint(rgb, state, dry_to=None, dead_to=None):
    rgb = np.asarray(rgb, float)
    if state == "dry":
        return np.clip(rgb * DRY if dry_to is None else np.asarray(dry_to), 0, 1)
    if state == "dead":
        return np.clip(np.full(3, rgb.mean()) * DEAD * 0.9 if dead_to is None else np.asarray(dead_to), 0, 1)
    return rgb


def jitter(rng, rgb, amount=0.08, hue=0.04):
    rgb = np.asarray(rgb, float)
    j = 1 + rng.uniform(-amount, amount)
    h = np.array([1 + rng.uniform(-hue, hue), 1.0, 1 + rng.uniform(-hue, hue)])
    return np.clip(rgb * j * h, 0, 1)


def ambient(m, height, floor=0.55, power=0.7):
    """Ground occlusion: darker toward the base, as vanilla's painted vertex colours are."""
    def fn(P, N, U0, U1, C):
        occ = floor + (1 - floor) * np.clip(P[:, 1] / max(height, 1e-6), 0, 1) ** power
        C = C.copy()
        C[:, :3] *= occ[:, None]
        return C
    m.map_colors(fn)


def auto_sway(m, height, exponent=1.0, seed=0):
    """uv1.y = normalised height (0 rooted .. 1 at the top), uv1.x = a stable per-vertex random. Parts that set their
    own sway (non-zero uv1.y) keep the larger of the two."""
    rng = np.random.default_rng(seed)
    P, N, U0, U1, U2, C, T = m.arrays()
    h = np.clip(P[:, 1] / max(height, 1e-6), 0, 1) ** exponent
    U1 = U1.copy()
    U1[:, 1] = np.maximum(U1[:, 1], h)
    U1[:, 0] = rng.random(len(P))
    m._set(P, N, U0, U1, U2, C, T)


# ------------------------------------------------------------------------------------------- parts
def card(m, hinge, azimuth, tilt, length, width, uv, color, uv2=None, sway=(None, None), lift_normal=0.35,
         roll=0.0, back_offset=0.0, two_sided=False, flip_v=False):
    """A leaf card hinged at `hinge` (its bottom-centre), pointing outward along `azimuth` (radians in the xz plane,
    0 = +x) and raised by `tilt` (0 = flat, pi/2 = upright, negative = drooping). The sprite's bottom edge is at the
    hinge, its top at the far end (flip_v: the other way round). One-sided, its front facing up.

    Back faces are culled (VegetationURP renders front faces only) and the camera looks down at 40-70 degrees, so a card
    that rises outward steeper than about 45 degrees shows its back on the near side of the plant. Rising cards stay
    under ~40 degrees; steep sides are built from drooping cards (negative tilt, see shingle), whose up face is also their
    outer face, as the vanilla canopies are."""
    if flip_v:
        uv = (uv[0], uv[3], uv[2], uv[1])
        if uv2 is not None:
            uv2 = (uv2[0], uv2[3], uv2[2], uv2[1])
    d = np.array([math.cos(azimuth) * math.cos(tilt), math.sin(tilt), math.sin(azimuth) * math.cos(tilt)])
    side = np.array([-math.sin(azimuth), 0.0, math.cos(azimuth)])
    if roll:
        side = pm.rot_axis(d, roll) @ side
    h = np.asarray(hinge, float) - d * back_offset
    bl, br = h - side * width / 2, h + side * width / 2
    tr, tl = br + d * length, bl + d * length
    n = np.cross(d, side)
    if n[1] < 0:
        n = -n
    n = n + np.array([0, lift_normal, 0])
    s0, s1 = sway
    sw = (0, 0, 0, 0) if s0 is None else (s0, s0, s1, s1)
    m.quad([bl, br, tr, tl], uv, normal=n, sway=sw, uv2=uv2, color=color, two_sided=two_sided)


def shingle(m, centre, radii, phi, theta, length, width, uv, color, uv2=None, sway=(0.6, 1.0), inset=0.3,
            lift_normal=0.25, flip_v=True, droop=0.0):
    """A card laid like a roof tile on an ellipsoid (centre, radii (rx, ry, rz)) at polar angle phi (0 = top) and azimuth
    theta: hinged up-slope (pulled in by `inset` of its length) and running down the surface, so its front faces out
    and up wherever it is, and lower cards are overlapped by the ones above. droop bends it further down (radians)."""
    rx, ry, rz = radii
    pt = np.asarray(centre, float) + np.array([rx * math.sin(phi) * math.cos(theta), ry * math.cos(phi),
                                               rz * math.sin(phi) * math.sin(theta)])
    # tangent running down the meridian
    t = np.array([rx * math.cos(phi) * math.cos(theta), -ry * math.sin(phi), rz * math.cos(phi) * math.sin(theta)])
    t /= np.linalg.norm(t)
    tilt = math.asin(max(-1.0, min(1.0, t[1]))) - droop
    hinge = pt - t * length * inset
    card(m, hinge, theta, tilt, length, width, uv, color, uv2=uv2, sway=sway, lift_normal=lift_normal, flip_v=flip_v)


def upright(m, base, yaw, height, width, uv, color, uv2=None, two_sided=True, lean=(0.0, 0.0), sway=None):
    """A vertical card standing on `base`, facing along yaw; lean (dx, dz) offsets its top."""
    side = np.array([math.cos(yaw), 0.0, math.sin(yaw)])
    b = np.asarray(base, float)
    top = b + np.array([lean[0], height, lean[1]])
    bl, br = b - side * width / 2, b + side * width / 2
    tl, tr = top - side * width / 2, top + side * width / 2
    n = np.cross(side, top - b)
    n = n / np.linalg.norm(n)
    sw = (0, 0, 0, 0) if sway is None else (sway[0], sway[0], sway[1], sway[1])
    m.quad([bl, br, tr, tl], uv, normal=n + np.array([0, 0.25, 0]), sway=sw, uv2=uv2, color=color, two_sided=two_sided)


def crossed(m, base, yaw, height, width, uv, color, uv2=None, count=2, lean=(0.0, 0.0), sway=None):
    for k in range(count):
        upright(m, base, yaw + math.pi * k / count, height, width, uv, color, uv2=uv2, lean=lean, sway=sway)


def stem(m, base, top, r0, r1, uv, color, sides=5, segments=2, bend=(0.0, 0.0, 0.0), v_range=(0.0, 1.0), cap=None):
    """A tapered stem (culm, trunk, branch) from base to top, bowed by `bend` at the middle."""
    b, t = np.asarray(base, float), np.asarray(top, float)
    pts = []
    for i in range(segments + 1):
        f = i / segments
        pts.append(b + (t - b) * f + np.asarray(bend) * 4 * f * (1 - f))
    u0, v0, u1, v1 = uv
    vv0, vv1 = v_range
    m.tube(pts, np.linspace(r0, r1, segments + 1), sides, (u0, v0 + (v1 - v0) * vv0, u1, v0 + (v1 - v0) * vv1),
           sway=np.zeros(segments + 1), color=color, cap_top=cap)


def mound(m, centre, radius, height, uv, color, sides=10):
    """A low soil mound: a very flat cone with the soil sprite on top (one fan); the sprite's ragged alpha edge, not the
    polygon, makes the outline, so the rim sits at ground level and the rise is small."""
    c = np.asarray(centre, float)
    cx, cy = (uv[0] + uv[2]) / 2, (uv[1] + uv[3]) / 2
    ru, rv = (uv[2] - uv[0]) / 2 * 1.0, (uv[3] - uv[1]) / 2 * 1.0
    P = [c + np.array([0, height, 0])]
    UV = [(cx, cy)]
    for j in range(sides):
        a = 2 * math.pi * j / sides
        P.append(c + np.array([math.cos(a) * radius, 0.002, math.sin(a) * radius]))
        UV.append((cx + ru * math.cos(a), cy + rv * math.sin(a)))
    P = np.array(P)
    T = np.array([[0, 1 + (j + 1) % sides, 1 + j] for j in range(sides)])
    g = np.cross(P[T[0, 1]] - P[T[0, 0]], P[T[0, 2]] - P[T[0, 0]])
    if g[1] < 0:
        T = T[:, ::-1]
    N = np.tile([0, 1.0, 0], (len(P), 1)) + np.concatenate([[[0, 0, 0]], (P[1:] - c) * 0.6])
    m.add(P, N, np.array(UV), T, None, None, color)


# ------------------------------------------------------------------------------------------- the plant
class Plant:
    def __init__(self, pid, kind, material=None, script_dir=None, height=1.0):
        self.id = pid
        self.kind = kind                         # Crops | Bushes | Trees: the generated blueprint's folder
        self.material = material or pid
        self.stages = {}
        self.stump_fn = None
        self.height = height
        self.script_dir = script_dir
        self.extra = {}

    def stage(self, name, fn):
        self.stages[name] = fn

    def stump(self, fn):
        self.stump_fn = fn

    @property
    def asset_dir(self):
        return "NaturalResources/Pandaborn/%s/%s" % (self.kind, self.id)

    def make(self, stage, state):
        m = Mesh(self.material)
        self.stages[stage](m, state)
        return m

    def build(self, out=None):
        out = out or os.path.join(BUILD, self.id)
        os.makedirs(out, exist_ok=True)
        stats, files = {}, {}
        for stage in self.stages:
            for state, suffix in (("alive", ""), ("dry", "Dry"), ("dead", "Dead")):
                name = self.id + stage + suffix
                m = self.make(stage, state)
                stats[name] = pm.write(os.path.join(out, name + ".timbermesh"), m, name)
                files["%s/#%s" % (stage, {"alive": "Alive", "dry": "Dying", "dead": "Dead"}[state])] = \
                    self.asset_dir + "/" + name
        if self.stump_fn:
            name = self.id + "MatureStump"
            m = Mesh(self.material)
            self.stump_fn(m, "alive")
            stats[name] = pm.write(os.path.join(out, name + ".timbermesh"), m, name)
            files["#Leftover"] = self.asset_dir + "/" + name
        report = self.report(stats)
        info = self.model_json(files, stats, report)
        if self.script_dir:
            with open(os.path.join(self.script_dir, "model.json"), "w", encoding="utf-8") as fh:
                json.dump(info, fh, indent=1)
        with open(os.path.join(out, "report.json"), "w", encoding="utf-8") as fh:
            json.dump({"stats": stats, "budget": report}, fh, indent=1)
        for line in report["lines"]:
            print(line)
        return info

    def report(self, stats):
        lines, flags = [], []
        ref = VANILLA[self.kind]
        for name, s in stats.items():
            stage = "MatureStump" if name.endswith("MatureStump") else ("Seedling" if "Seedling" in name else "Mature")
            lo, hi = ref.get(stage, (0, 9999))
            cap = int(hi * 1.25)
            ok = s["triangles"] <= cap
            if not ok:
                flags.append("%s: %d triangles > %d (1.25 x vanilla max %d)" % (name, s["triangles"], cap, hi))
            lines.append("%-40s %4d tris %4d verts  bbox %s..%s  %s" % (name, s["triangles"], s["vertices"], s["bboxMin"],
                                                                     s["bboxMax"], "ok" if ok else "OVER BUDGET"))
            if s["uv0"] and (s["uv0"][0] < 0 or s["uv0"][1] > 1):
                flags.append("%s: uv0 outside 0..1" % name)
        return {"lines": lines, "flags": flags}

    def model_json(self, files, stats, report):
        mature = self.asset_dir + "/" + self.id + "Mature"
        info = {
            "id": self.id,
            "template": self.id + ".Inkpaws",
            "kind": self.kind,
            "material": self.material,
            "materialAsset": MATERIAL_ASSET_DIR + "/" + self.material,
            "materialCollection": COLLECTION,
            "bundle": "pandabornplants",
            "modelDir": self.asset_dir,
            "models": files,
            "PlantablePreviewModelSpec.Model": mature,
            "builtTo": os.path.join(BUILD, self.id),
            "stats": {k: {"triangles": v["triangles"], "vertices": v["vertices"], "bboxMin": v["bboxMin"],
                          "bboxMax": v["bboxMax"]} for k, v in stats.items()},
            "budgetFlags": report["flags"],
        }
        info.update(self.extra)
        return info
