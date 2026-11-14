"""Kit core: geometry parts, trim-sheet regions, vertex colours and the .timbermesh writer.

Space: Unity, 1 unit = 1 tile edge. x right, y up, z forward. A building's footprint is x in [0, X], z in [0, Y]
(grid X and Y), height y = grid Z. The front (where the entrance is, grid -Y) is the z = 0 side, facing -z.

Materials are the vanilla Folktails names, which the faction's look swaps for its own textures (docs/tech/look.md):
models made here share one material set and one runtime atlas with the re-themed vanilla models. Every UV stays in
0..1 (the runtime atlaser remaps uv * 1/4 + offset) and every surface lands in the matching trim region.
"""
import math
import os
import sys
import zlib
from dataclasses import dataclass, field

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import model_pb2 as pb  # noqa: E402
import tmesh_static as ts  # noqa: E402

# ------------------------------------------------------------------------------------------- materials
TIMBER = "BaseWood_Brown.Folktails"          # dark timber: posts, beams, boards, frames
BAMBOO_GOLD = "BaseWood_LightBrown.Folktails"  # cured straw-gold bamboo
BAMBOO_GREEN = "BaseWood_Yellow.Folktails"     # fresh green bamboo
BAMBOO_GREY = "BaseWood_White.Folktails"       # weathered silver-grey bamboo
WEAVE = "IrregularPlanks_White.Folktails"      # woven bamboo panel, pale
WEAVE_GOLD = "IrregularPlanks_LightBrown.Folktails"
WEAVE_DARK = "IrregularPlanks_Brown.Folktails"
WEAVE_GREEN = "IrregularPlanks_Yellow.Folktails"
WEAVE_MOSSY = "IrregularPlanks_Mossy.Folktails"
TILE = "ThatchedRoof.Folktails"                # grey clay pan-and-cover tile (4 courses)
PLASTER = "Plaster_White.Folktails"            # white lime plaster; also a paintable base (vertex colour = colour)
PLASTER_LATH = "PlasteredWood_White.Folktails"  # lime plaster with spalls showing earth and laths
WINDOWS = "WindowsAtlas.Folktails"             # lattice windows (glow at night), dark doorways
PAPER = "Paper.Folktails"                      # lattice paper panels
DETAILS = "Details.Folktails"                  # indigo banner, hemp sack, rope, colour labels, bamboo crates
IRON = "BaseMetal.Folktails"                   # soot-dark iron
BANDED = "PaintedMetal.Folktails"              # cane binding over black iron
EARTH = "Sand.Folktails"                       # rammed earth with river pebbles
MOSS = "Moss.Folktails"

# ------------------------------------------------------------------------------------------- trim regions (u0, v0, u1, v1)
# BaseWood sheet (timber and the three bamboos share the layout; measured from the vanilla sheet's components)
# Regions come from the look lane's canonical map (src/pipeline/sheet_regions.json, docs/tech/look-regions.md),
# measured from the vanilla sheets, which the faction's baked sheets follow. Pixels [x0, y0, x1, y1) with y down.
_REGIONS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sheet_regions.json")


def _uv(rect, inset=2):
    x0, y0, x1, y1 = rect
    return ((x0 + inset) / 1024, 1 - (y1 - inset) / 1024, (x1 - inset) / 1024, 1 - (y0 + inset) / 1024)


def _load_wood():
    import json
    regs = json.load(open(_REGIONS))["sheets"]["BaseWood"]["regions"]
    block = strips = short = discs = plain = None
    strips, short, discs = [], [], []
    for r in regs:
        x0, y0, x1, y1 = r["rect"]
        k = r["kind"]
        if k.startswith("long-grain"):
            block = _uv(r["rect"])
        elif k.startswith("plank strip"):
            (strips if y1 - y0 > 450 else short).append(_uv(r["rect"]))
        elif k.startswith("end-grain"):
            discs.append(((x0 + x1) / 2048, 1 - (y0 + y1) / 2048, min(x1 - x0, y1 - y0) / 2048 * 0.9))
        elif k.startswith("plain"):
            plain = _uv(r["rect"])
    return strips, short, block, discs, plain


try:
    WOOD_STRIPS, WOOD_SHORT, WOOD_BLOCK, WOOD_DISCS, WOOD_PLAIN = _load_wood()
except (OSError, KeyError, ValueError):   # the canonical map as of 2026-11-14
    WOOD_STRIPS = [_uv((516 + 64 * i, 4, 572 + 64 * i, 501)) for i in range(4)] + \
                  [_uv((4 + 64 * i, 516, 60 + 64 * i, 1020)) for i in range(8)]
    WOOD_SHORT = [_uv((772 + 64 * i, 132, 828 + 64 * i, 501)) for i in range(4)] + \
                 [_uv((516 + 64 * i, 516, 572 + 64 * i, 761)) for i in range(8)]
    WOOD_BLOCK = _uv((0, 0, 512, 500))
    WOOD_DISCS = [(0.5625, 0.1875, 0.056), (0.6875, 0.1875, 0.056), (0.5625, 0.0625, 0.056),
                  (0.703, 0.094, 0.028), (0.703, 0.031, 0.028)]
    WOOD_PLAIN = _uv((768, 768, 1024, 1024))
# WindowsAtlas sheet
WIN_LATTICE = (0.755, 0.006, 0.994, 0.240)   # square cracked-ice lattice, glows at night
WIN_PANES = (0.672, 0.885, 0.915, 0.978)     # four-pane strip, glows
WIN_TALL = (0.538, 0.865, 0.590, 0.990)      # tall narrow pane, glows
WIN_ROUND = (0.755, 0.255, 0.994, 0.495)     # round cracked-ice window, glows
LANTERN_GLOW = (0.76, 0.015, 0.84, 0.08)  # an even strip of the glass panel's paper cells (no dark gap): lantern paper
# Warm lantern glow (pass 5): the WindowsAtlas glow map is one pale amber everywhere and the shader's emission ignores
# vertex colour (EnvironmentURP: LightingMap x LightingColor x strength), so a lantern glows the colour of its patch of
# the glow map. Requested from the look lane (models.md, "Lantern glow colour"): two plain patches in the atlas's free
# right-hand column, red-orange [960,16,1024,80] and amber [960,96,1024,160] (pixels, y down). Until the sheet has
# them, PB_LANTERN_WARM stays unset and lanterns keep LANTERN_GLOW (a patch still blank would not glow at all).
LANTERN_RED = (0.9414, 0.9258, 0.9961, 0.9805)     # [964,20,1020,76]
LANTERN_AMBER = (0.9414, 0.8477, 0.9961, 0.9023)   # [964,100,1020,156]
WARM_LANTERNS = os.environ.get("PB_LANTERN_WARM") == "1"
WIN_DARK = (0.02, 0.02, 0.48, 0.48)          # dark doorway (warm glow at night in the lower part)
WIN_WALL = (0.52, 0.02, 0.73, 0.48)          # plain lime wall
# Details sheet
DET_BANNER = (0.02, 0.52, 0.48, 0.98)        # indigo cloth with an ink bamboo in a pale disc
DET_CLOTH = (0.02, 0.53, 0.10, 0.62)         # plain indigo cloth (banner corner)
DET_SACK = (0.51, 0.52, 0.74, 0.98)          # hemp sack
DET_ROPE = (0.755, 0.52, 0.790, 0.98)        # rice-straw rope, along v
DET_RED = (0.825, 0.845, 0.84, 0.995)        # red label border: lantern red
DET_GREEN = (0.82, 0.70, 0.99, 0.82)
DET_CRATE = (0.02, 0.02, 0.48, 0.48)         # bamboo crate faces
# ThatchedRoof sheet: 4 courses, lower edges at v = 0.055 + 0.25 k; tiles in 16 columns
TILE_COURSES = [(0.057 + 0.25 * k, 0.057 + 0.25 * k + 0.245) for k in range(3)]   # 3 full courses
TILE_COURSES.append(TILE_COURSES[1])
TILE_COLS = 16

TEXEL = 0.5   # vanilla density: about 500 px of a 1024 sheet per tile edge


# ------------------------------------------------------------------------------------------- transforms
def rot_axis(axis, ang):
    a = np.asarray(axis, float)
    a = a / np.linalg.norm(a)
    x, y, z = a
    c, s = math.cos(ang), math.sin(ang)
    C = 1 - c
    return np.array([[c + x * x * C, x * y * C - z * s, x * z * C + y * s],
                     [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
                     [z * x * C - y * s, z * y * C + x * s, c + z * z * C]])


def frame_from(direction, up=(0, 1, 0)):
    """3x3 whose columns are (side, up', direction): local z runs along direction."""
    d = np.asarray(direction, float)
    d = d / np.linalg.norm(d)
    u = np.asarray(up, float)
    if abs(np.dot(u, d)) > 0.95:
        u = np.array([1.0, 0, 0]) if abs(d[0]) < 0.9 else np.array([0, 0, 1.0])
    s = np.cross(u, d)
    s /= np.linalg.norm(s)
    u = np.cross(d, s)
    return np.stack([s, u, d], 1)


def quat_axis(axis, ang):
    a = np.asarray(axis, float)
    a = a / np.linalg.norm(a)
    s = math.sin(ang / 2)
    return (a[0] * s, a[1] * s, a[2] * s, math.cos(ang / 2))


# ------------------------------------------------------------------------------------------- parts
@dataclass
class Part:
    material: str
    P: np.ndarray
    N: np.ndarray
    UV: np.ndarray
    T: np.ndarray
    C: np.ndarray = None
    tags: set = field(default_factory=set)
    node: str = ""          # "" = the model's root node; otherwise an animated/child node name

    def transformed(self, R=None, t=(0, 0, 0)):
        R = np.eye(3) if R is None else np.asarray(R, float)
        P = self.P @ R.T + np.asarray(t, float)
        N = self.N @ R.T
        flip = np.linalg.det(R) < 0
        T = self.T[:, ::-1] if flip else self.T
        return Part(self.material, P, N, self.UV, T, None if self.C is None else self.C.copy(), set(self.tags), self.node)


def fix_winding(P, N, T):
    """Make every triangle's geometric normal agree with its vertex normals (the game's convention)."""
    a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    g = np.cross(b - a, c - a)
    s = np.einsum("ij,ij->i", g, N[T[:, 0]] + N[T[:, 1]] + N[T[:, 2]])
    T = T.copy()
    bad = s < 0
    T[bad] = T[bad][:, ::-1]
    return T


def quad_part(material, corners, uv_rect=(0, 0, 1, 1), normal=None, uvs=None):
    """One quad: corners in order (bottom-left, bottom-right, top-right, top-left) as seen from its front."""
    P = np.asarray(corners, float)
    n = np.cross(P[1] - P[0], P[3] - P[0]) if normal is None else np.asarray(normal, float)
    n = n / max(np.linalg.norm(n), 1e-12)
    u0, v0, u1, v1 = uv_rect
    UV = np.array([[u0, v0], [u1, v0], [u1, v1], [u0, v1]]) if uvs is None else np.asarray(uvs, float)
    T = fix_winding(P, np.tile(n, (4, 1)), np.array([[0, 1, 2], [0, 2, 3]]))
    return Part(material, P, np.tile(n, (4, 1)), UV, T)


def merge_parts(parts):
    P, N, UV, C, T = [], [], [], [], []
    base = 0
    for p in parts:
        P.append(p.P)
        N.append(p.N)
        UV.append(p.UV)
        C.append(np.ones((len(p.P), 4)) if p.C is None else p.C)
        T.append(p.T + base)
        base += len(p.P)
    return (np.concatenate(P), np.concatenate(N), np.concatenate(UV), np.concatenate(C), np.concatenate(T))


class Geo:
    """A bag of parts with a current transform stack, a seeded random generator and tags."""

    def __init__(self, seed=1):
        self.parts = []
        self.rng = np.random.default_rng(seed)
        self._tags = set()
        self._node = ""

    def add(self, part, tags=()):
        part.tags |= set(tags) | self._tags
        if not part.node:
            part.node = self._node
        self.parts.append(part)
        return part

    def tagged(self, *tags):
        geo = self

        class _Ctx:
            def __enter__(self_):
                self_.old = set(geo._tags)
                geo._tags |= set(tags)

            def __exit__(self_, *a):
                geo._tags = self_.old
        return _Ctx()

    def node(self, name):
        geo = self

        class _Ctx:
            def __enter__(self_):
                self_.old = geo._node
                geo._node = name

            def __exit__(self_, *a):
                geo._node = self_.old
        return _Ctx()

    def jitter(self, scale):
        return float(self.rng.uniform(-scale, scale))

    def extend(self, other, R=None, t=(0, 0, 0)):
        for p in other.parts:
            self.parts.append(p.transformed(R, t))

    def triangles(self, tag=None, exclude=None):
        return sum(len(p.T) for p in self.parts if (tag is None or tag in p.tags) and not (exclude and exclude in p.tags))

    def bounds(self, exclude_tags=()):
        ps = [p.P for p in self.parts if not (p.tags & set(exclude_tags))]
        P = np.concatenate(ps)
        return P.min(0), P.max(0)


# ------------------------------------------------------------------------------------------- vertex colour
def shade(parts, ground=0.0, seed=7, ao_height=0.7, ao_min=0.62, underside=0.72, baked=None, ao_floor=0.42):
    """Vertex colours: per-part brightness/hue jitter (hand-made look), ground occlusion near the base, darker
    undersides, and any colour a part already carries (tints, stones). White = unshaded."""
    rng = np.random.default_rng(seed)
    for i, p in enumerate(parts):
        base = np.ones((len(p.P), 4)) if p.C is None else p.C.copy()
        if "noshade" in p.tags:
            p.C = base
            continue
        j = 1.0 + rng.uniform(-0.05, 0.05)
        hue = np.array([1.0 + rng.uniform(-0.02, 0.02), 1.0, 1.0 + rng.uniform(-0.02, 0.02)])
        y = p.P[:, 1] - ground
        if "glow" in p.tags:
            occ = np.ones(len(p.P))
        elif baked is not None:          # Cycles-baked occlusion (ao.py), softened so nothing goes black
            occ = ao_floor + (1 - ao_floor) * np.clip(baked[i], 0, 1) ** 0.8
        else:
            occ = ao_min + (1 - ao_min) * np.clip(y / ao_height, 0, 1) ** 0.7
            occ *= np.where(p.N[:, 1] < -0.5, underside, 1.0)
        c = base[:, :3] * (j * hue)[None, :] * occ[:, None]
        p.C = np.concatenate([np.clip(c, 0, 1), np.ones((len(c), 1))], 1)


# ------------------------------------------------------------------------------------------- writer
def _node_from_parts(name, parent, parts, position=(0, 0, 0), rotation=(0, 0, 0, 1)):
    by_mat = {}
    for p in parts:
        by_mat.setdefault(p.material, []).append(p)
    allp = [p for ps in by_mat.values() for p in ps]
    if not allp:
        return ts.StaticNode(name, parent, position=position, rotation=rotation, meshes=[])
    P, N, UV, C, T = merge_parts(allp)
    meshes = []
    start = 0
    for mat, ps in by_mat.items():
        n = sum(len(p.T) for p in ps)
        meshes.append((mat, T[start:start + n]))
        start += n
    P = P - np.asarray(position, float)
    return ts.StaticNode(name, parent, position=tuple(position), rotation=rotation, positions=P.astype(np.float32),
                         normals=(N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)).astype(np.float32),
                         colors=C.astype(np.float32), uv0=np.clip(UV, 0, 1).astype(np.float32), meshes=meshes)


def quat_mat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def write(path, root_name, parts, animated=None, slots=None):
    """parts: Parts of this model. animated: {node name: {"pivot": xyz, "axis": xyz, "kind": "turn"|"swing",
    "amplitude": radians (swing), "frames": 100, "fps": 24, "turns": 1, "pivot_rot": quaternion or None}}: parts
    whose .node is that name become a child node about the pivot (under an extra 'Pivot' node rotated by pivot_rot
    when given, so the axis is local), with one looped node animation 'Default' (the game plays the first animation;
    vanilla wheels: 100 frames at 24 fps, one turn per loop). slots: [(name, position, yaw_degrees)] at the root, or
    dicts {"name", "parent": animated node, "local_pos", "local_rot"} -> '#Slot#<name>' empty nodes."""
    animated = animated or {}
    nodes = [_node_from_parts(root_name, -1, [p for p in parts if not p.node])]
    anims, index = [], {}
    for name, a in animated.items():
        mine = [p for p in parts if p.node == name]
        if a.get("pivot_rot"):
            R = quat_mat(a["pivot_rot"])
            local = [p.transformed(R.T, -R.T @ np.asarray(a["pivot"], float)) for p in mine]
            nodes.append(ts.StaticNode("Pivot" + name.strip("#"), 0, position=tuple(a["pivot"]),
                                       rotation=tuple(a["pivot_rot"]), meshes=[]))
            nd = _node_from_parts(name, len(nodes) - 1, local)
            nodes.append(nd)
            a = dict(a, _pos=(0.0, 0.0, 0.0))
        elif a.get("parent"):
            # child of another (non-rotated-pivot) node: local position relative to the parent's pivot
            pp = np.asarray(animated[a["parent"]]["pivot"], float)
            loc = [p.transformed(None, -pp) for p in mine]
            nodes.append(_node_from_parts(name, index[a["parent"]], loc,
                                          position=tuple(np.asarray(a["pivot"], float) - pp)))
            a = dict(a, _pos=tuple(np.asarray(a["pivot"], float) - pp))
        else:
            nodes.append(_node_from_parts(name, 0, mine, position=a["pivot"]))
            a = dict(a, _pos=tuple(a["pivot"]))
        index[name] = len(nodes) - 1
        if a.get("kind") != "static":     # static: turned by game code by name (wind rotators), no animation
            anims.append((len(nodes) - 1, a))
    for sl in (slots or []):
        if isinstance(sl, dict):
            # raw: an empty marker node named exactly (e.g. the Lido's '#MiscStart1' patrol ends), under the root
            name = sl["name"] if sl.get("raw") else "#Slot#" + sl["name"]
            parent = index[sl["parent"]] if sl.get("parent") else 0
            nodes.append(ts.StaticNode(name, parent, position=tuple(sl["local_pos"]),
                                       rotation=tuple(sl.get("local_rot", (0.0, 0.0, 0.0, 1.0))), meshes=[]))
        else:
            sname, pos, yaw = sl
            q = quat_axis((0, 1, 0), math.radians(yaw))
            nodes.append(ts.StaticNode("#Slot#" + sname, 0, position=tuple(pos), rotation=q, meshes=[]))
    model = ts.build_model(nodes)
    for idx, a in anims:
        nd = model.nodes[idx]
        an = nd.nodeAnimations.add()
        an.name = a.get("name", "Default")
        an.framerate = a.get("fps", 24.0)
        frames = a.get("frames", 100)
        for f in range(frames):
            fr = an.frames.add()
            fr.position.x, fr.position.y, fr.position.z = a["_pos"]
            t = (f + 1) / frames
            if a.get("kind", "turn") == "swing":
                ang = a.get("amplitude", 0.25) * math.sin(2 * math.pi * t)
            elif a.get("kind") == "trip":
                # a trip hammer: a cam lifts the beam slowly, then lets it fall; `turns` lifts per loop, `phase` offset
                ph = (t * a.get("turns", 1) + a.get("phase", 0.0)) % 1.0
                ang = a.get("amplitude", 0.25) * (ph / 0.7 if ph < 0.7 else max(0.0, 1 - (ph - 0.7) / 0.08))
            elif a.get("kind") == "rise":
                # a one-shot launch (wonders play their animation once): up and away with a slow turn, and back home
                # on the last frame so the model rests at its start pose when the animator stops
                k = 0.0 if f == frames - 1 else (t / 0.97) ** 1.6
                fr.position.y = a["_pos"][1] + a.get("height", 30.0) * k
                fr.position.x = a["_pos"][0] + 1.5 * k * k
                ang = 1.5 * math.pi * k
            else:
                ang = 2 * math.pi * a.get("turns", 1) * t * a.get("direction", 1)
            fr.rotation.x, fr.rotation.y, fr.rotation.z, fr.rotation.w = quat_axis(a["axis"], ang)
            fr.scale.x = fr.scale.y = fr.scale.z = 1.0
    data = zlib.compress(model.SerializeToString(), 6)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    return model
