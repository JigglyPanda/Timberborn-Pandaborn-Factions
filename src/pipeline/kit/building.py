"""Assembly helpers for a building script: grid, footprint, entrance and slot markers, construction stage, budget
report, writing the model files and model.json.

A building script (art/models/<Id>/build.py) does:

    from building import Model
    m = Model("Den", size=(2, 2, 2), seed=11, stand_in="Lodge.Folktails")
    g = m.geo
    ...compose parts...
    m.entrance(1, door=(1.0, 0.0))            # grid entrance cell x (in front of the building at y = -1)
    m.slot("Spot", (0.5, 0.2, 0.5), yaw=180)
    m.build()

Outputs go to E:\\PandabornDev\\build\\models\\<Id>\\ (<Id>.Model.timbermesh, <Id>.ConstructionStage0.Model.timbermesh,
report.json); model.json is written beside the script (it is the hand-off to the blueprint generator).
"""
import json
import math
import zlib
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core  # noqa: E402
from core import Geo, shade, write, TIMBER, BAMBOO_GOLD  # noqa: E402
import parts as K  # noqa: E402

OUT_ROOT = r"E:\PandabornDev\build\models"

# vanilla triangle counts by footprint area (tiles), p50 and p90 of the Folktails building models
BUDGET = [(1, 300, 520), (2, 520, 660), (4, 900, 1200), (6, 1250, 1700), (9, 1600, 2200), (12, 1900, 2500),
          (25, 2900, 6400)]


def budget_for(area):
    for a, mid, hi in BUDGET:
        if area <= a:
            return mid, hi
    return BUDGET[-1][1:]


class Model:
    def __init__(self, model_id, size, seed=1, stand_in="", script_dir=None, overhang=0.35):
        self.id = model_id
        self.size = tuple(size)
        self.geo = Geo(seed)
        self.stand_in = stand_in
        self.overhang = overhang
        self.script_dir = script_dir or os.path.dirname(os.path.abspath(sys.argv[0]))
        self.out = os.path.join(OUT_ROOT, model_id)
        self.slots = []
        self.animated = {}
        self.colliders = []
        self.attachments = []
        self.blocks = None
        self.entrance_cell = None
        self.notes = []
        self.extra = {}
        self.stage_extra = None
        self.stage_slots = []         # [(name, pos, yaw)]: slots on the construction stage (builders at a wonder)
        self.stage_height = None

    # -- grid helpers ------------------------------------------------------------------------------------------
    @staticmethod
    def cell(x, y, z=0):
        """Unity position of the centre of grid cell (x, y) at height z (bottom of the cell)."""
        return np.array([x + 0.5, z, y + 0.5])

    def entrance(self, x, y=-1, z=0):
        """The entrance cell in grid coordinates (in front of the door, outside the footprint)."""
        self.entrance_cell = (x, y, z)

    def slot(self, name, pos, yaw=0.0, keyword=None):
        """'#Slot#<name>' empty: where a colonist sits/works. yaw in degrees about up (0 = facing +z)."""
        self.slots.append((name, tuple(float(v) for v in pos), yaw))

    def animate(self, node, pivot, axis, frames=100, fps=24.0, turns=1, driver="", direction=1, kind="turn",
                amplitude=0.25, pivot_rot=None, parent=None, height=30.0):
        """Parts added inside `with geo.node(node):` become a child node animated about pivot: kind 'turn' (wheels:
        `turns` full turns per loop) or 'swing' (+-amplitude radians). pivot_rot puts the node under a rotated
        'Pivot' node so `axis` is in that local frame (as the vanilla hammock does)."""
        self.animated[node] = {"pivot": tuple(float(v) for v in pivot), "axis": tuple(float(v) for v in axis),
                               "frames": frames, "fps": fps, "turns": turns, "driver": driver,
                               "direction": direction, "kind": kind, "amplitude": amplitude,
                               "pivot_rot": pivot_rot, "parent": parent, "height": height}

    def collider(self, center, size):
        self.colliders.append({"Center": dict(zip("XYZ", map(float, center))),
                               "Size": dict(zip("XYZ", map(float, size)))})

    def attach(self, attachment_id, position, note=""):
        self.attachments.append({"AttachmentId": attachment_id, "Position": dict(zip("XYZ", map(float, position))),
                                 "note": note})

    # -- construction stage --------------------------------------------------------------------------------------
    def _stage_parts(self):
        sg = Geo(1234)
        X, Y = self.size[0], self.size[1]
        frame = [p for p in self.geo.parts if (p.tags & {"frame", "base", "stage"}) and not p.node]
        top = self.stage_height
        if top is None:
            top = max([float(p.P[:, 1].max()) for p in frame] + [0.8])
        top = min(top, 2.2)
        small = X * Y <= 2
        # scaffold: bamboo poles at the corners (two diagonal ones on small pieces), ties, lashings
        pts = [(-0.06, -0.06), (X + 0.06, -0.06), (X + 0.06, Y + 0.06), (-0.06, Y + 0.06)]
        if small:
            pts = [pts[0], pts[2]]
        if X >= 3:
            pts += [(X / 2, -0.06), (X / 2, Y + 0.06)]
        for (x, z) in pts:
            K.pole(sg, (x, 0, z), (x + sg.jitter(0.03), top + 0.25, z + sg.jitter(0.03)), r=0.035,
                   material=BAMBOO_GOLD, sides=5 if not small else 4, bend=0.01)
        ring = [(-0.06, -0.06), (X + 0.06, -0.06), (X + 0.06, Y + 0.06), (-0.06, Y + 0.06)]
        for y in ((top,) if small else (top * 0.5, top)):
            for i in range(4):
                a, b = ring[i], ring[(i + 1) % 4]
                K.pole(sg, (a[0], y + sg.jitter(0.03), a[1]), (b[0], y + sg.jitter(0.03), b[1]), r=0.025,
                       material=BAMBOO_GOLD, sides=4, bend=0.0, caps=False)
                if not small:
                    K.lashing(sg, (a[0], y, a[1]), (0, 1, 0), r=0.04)
        # a little stack of poles on the ground
        for k in range(2 if small else 3):
            z = Y * 0.15 + 0.07 * k
            K.pole(sg, (0.15, 0.03 + (k % 2) * 0.05, z), (max(min(X, 2) * 0.75, 0.7), 0.03 + (k % 2) * 0.05, z),
                   r=0.032,
                   material=core.BAMBOO_GREEN if k == 1 else BAMBOO_GOLD, sides=5, bend=0.0)
        out = [p.transformed() for p in frame] + sg.parts
        if self.stage_extra:
            sg2 = Geo(99)
            self.stage_extra(sg2)
            out += sg2.parts
        return out

    # -- checks and output ---------------------------------------------------------------------------------------
    def report(self, finished, stage):
        X, Y, Z = self.size
        allp = [p for p in finished]
        P = np.concatenate([p.P for p in allp])
        lo, hi = P.min(0), P.max(0)
        tris = {}
        for p in finished:
            tris[p.material] = tris.get(p.material, 0) + len(p.T)
        total = sum(tris.values())
        stage_tris = sum(len(p.T) for p in stage)
        mid, top = budget_for(X * Y)
        uv = np.concatenate([p.UV for p in allp])
        o = self.overhang
        foot_ok = bool(lo[0] >= -o and lo[2] >= -o and hi[0] <= X + o and hi[2] <= Y + o)
        bytag = {}
        for p in finished:
            k = ",".join(sorted(p.tags)) or "-"
            bytag[k] = bytag.get(k, 0) + len(p.T)
        r = {"id": self.id, "triangles": total, "perTag": dict(sorted(bytag.items(), key=lambda t: -t[1])), "perMaterial": dict(sorted(tris.items(), key=lambda t: -t[1])),
             "vertices": int(len(P)), "stageTriangles": stage_tris,
             "budget": {"vanillaMedian": mid, "vanillaHigh": top, "ratioToMedian": round(total / mid, 2),
                        "ok": total <= top * 1.1},
             "bounds": {"min": [round(float(v), 3) for v in lo], "max": [round(float(v), 3) for v in hi]},
             "footprint": {"size": [X, Y, Z], "overhangAllowed": o, "ok": foot_ok,
                           "heightBlocks": round(float(hi[1]), 2)},
             "uvRange": [round(float(uv.min()), 3), round(float(uv.max()), 3)],
             "materials": sorted(tris)}
        return r

    def build(self, write_json=True, ao=True):
        os.makedirs(self.out, exist_ok=True)
        stage = self._stage_parts()
        baked = baked_stage = None
        if ao:
            import ao as AO
            try:
                baked = AO.bake(self.geo.parts)
                baked_stage = AO.bake(stage)
            except Exception as ex:  # noqa: BLE001 - fall back to the height-based guess
                print("AO bake failed, using height occlusion:", str(ex)[:300])
        shade(self.geo.parts, seed=zlib.crc32(self.id.encode()) % 1000, baked=baked)
        shade(stage, seed=5, baked=baked_stage)
        fin_path = os.path.join(self.out, f"{self.id}.Model.timbermesh")
        st_path = os.path.join(self.out, f"{self.id}.ConstructionStage0.Model.timbermesh")
        write(fin_path, self.id, self.geo.parts, self.animated, self.slots)
        write(st_path, self.id + ".ConstructionStage0", [p.transformed() for p in stage if not p.node],
              slots=self.stage_slots)
        rep = self.report(self.geo.parts, stage)
        rep["files"] = {"finished": fin_path, "stage": st_path}
        json.dump(rep, open(os.path.join(self.out, "report.json"), "w"), indent=1)
        if write_json:
            self.write_model_json(rep)
        print(json.dumps({k: rep[k] for k in ("id", "triangles", "stageTriangles", "budget", "footprint")}, indent=None))
        return rep

    def write_model_json(self, rep):
        X, Y, Z = self.size
        doc = {
            "id": self.id,
            "standIn": self.stand_in,
            "generatedBy": "art/models/%s/build.py (src/pipeline/kit); AI-generated, code-made" % self.id,
            "models": {"finished": f"{self.id}.Model", "constructionStage0": f"{self.id}.ConstructionStage0.Model"},
            "size": {"X": X, "Y": Y, "Z": Z},
            "blocks": self.blocks,
            "entrance": None if self.entrance_cell is None else dict(zip("XYZ", self.entrance_cell)),
            "slots": [{"node": "#Slot#" + s[0], "position": dict(zip("XYZ", s[1])), "yaw": s[2]} if not isinstance(s, dict)
                      else {"node": (s["name"] if s.get("raw") else "#Slot#" + s["name"]), "parent": s.get("parent"),
                            "localPosition": s["local_pos"], "localRotation": s.get("local_rot")} for s in self.slots],
            "animatedNodes": [{"node": k, "driver": _spec_name(v["driver"]),
                               "pivot": dict(zip("XYZ", v["pivot"])), "axis": dict(zip("XYZ", v["axis"])),
                               "animation": "Default", "kind": v["kind"], "frames": v["frames"], "fps": v["fps"],
                               "turns": v["turns"],
                               "drivenBy": v["driver"]} for k, v in self.animated.items()],
            "colliders": self.colliders,
            "attachments": self.attachments,
            "triangles": {"finished": rep["triangles"], "constructionStage0": rep["stageTriangles"],
                          "vanillaMedianForFootprint": rep["budget"]["vanillaMedian"]},
            "materials": rep["materials"],
            "notes": self.notes,
        }
        doc.update(self.extra)
        json.dump(doc, open(os.path.join(self.script_dir, "model.json"), "w"), indent=1)


def _spec_name(text):
    """The blueprint spec that drives an animated node, as data: the first '...Spec' word of the driver text."""
    import re
    m = re.search(r"[A-Za-z]+Spec", text or "")
    return m.group(0) if m else ""


def block(matter="GroundOrStackable", occ="Bottom, Top, Corners, Path, Middle", stackable="None"):
    return {"MatterBelow": matter, "Occupations": occ, "Stackable": stackable, "OccupyAllBelow": False,
            "Underground": False}


def solid_blocks(X, Y, Z, top_stackable="None", top_occ="Bottom, Top, Corners, Path, Middle"):
    """Blocks list in the game's order (z outer, then y, then x): every cell occupied."""
    out = []
    for z in range(Z):
        for y in range(Y):
            for x in range(X):
                out.append(block("GroundOrStackable" if z == 0 else "Any",
                                 top_occ if z == Z - 1 and Z > 1 else "Bottom, Top, Corners, Path, Middle",
                                 top_stackable if z == Z - 1 else "None"))
    return out
