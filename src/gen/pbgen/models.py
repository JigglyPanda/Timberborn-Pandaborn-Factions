"""Adopting the art lanes' models: a catalogue item names a model (`model = "Den"`), and everything the blueprint needs
from it comes from that model's model.json (written by art/models/<Id>/build.py, the building kit), never typed twice:
footprint and blocks, entrance, access point, colliders, the finished and construction-stage meshes, the construction
base, attachment positions, the connection anchor, and spec additions or removals the model asks for. Slots and
animated nodes live inside the mesh; the validator checks that the blueprint's slot keywords and animation drivers
match them.

The meshes themselves are built by `tools/pandaborn.ps1 models` into E:\\PandabornDev\\build\\models\\<Id>\\ (never in
git) and copied into the mod by `assemble` at Buildings/Pandaborn/Models/<Id>/ (plants: NaturalResources/Pandaborn/
Models/<Id>/), from the manifest this module records (Generator.model_files).

The same entry point serves plants (art/plants/<Id>/model.json) once that lane fixes its format: `kind="plant"`.
"""
import copy
import os

from .util import REPO, GenError, load_json

ROOTS = {"building": os.path.join(REPO, "art", "models"), "plant": os.path.join(REPO, "art", "plants")}
MOD_DIRS = {"building": "Buildings/Pandaborn/Models", "plant": "NaturalResources/Pandaborn/Models"}
DEFAULT_MESH_DIR = r"E:\PandabornDev\build\models"
# model.json keys this adopter understands; anything else is reported, so a new key in the kit is never ignored silently
KNOWN_KEYS = {"id", "standIn", "generatedBy", "models", "size", "blocks", "entrance", "access", "slots", "animatedNodes",
              "colliders", "attachments", "triangles", "materials", "notes", "removeSpecs", "addSpecs",
              "connectionAnchor", "windRotationAnimator", "walkUnder", "liquidPlane", "displayName"}
WATER_KEYS = {"waterCells", "solidCells", "flow", "outputCell", "waterOutput", "waterInput", "expectedWaterDirection"}


def load_model(kind, mid, item):
    path = os.path.join(ROOTS[kind], mid, "model.json")
    if not os.path.isfile(path):
        raise GenError("%s: model %s: %s not found (the art lane writes it with build.py)" % (item, mid, path))
    mj = load_json(path)
    if mj.get("id") != mid:
        raise GenError("%s: %s says id %r" % (item, path, mj.get("id")))
    return mj, path


def v3(d):
    return {"X": d["X"], "Y": d["Y"], "Z": d["Z"]}


def apply_building_model(gen, data, mid, item, mesh_dir=None):
    """Applies model.json to a building blueprint (already copied from its basis). Returns the model.json dict."""
    mj, path = load_model("building", mid, item)
    unknown = sorted(set(mj) - KNOWN_KEYS - WATER_KEYS)
    if unknown:
        gen.note(item, "model %s: model.json keys not used by the generator: %s" % (mid, ", ".join(unknown)))
    water = sorted(set(mj) & WATER_KEYS)
    if water:
        raise GenError("%s: model %s describes a water piece (%s); water pieces are adopted with the water module, "
                       "not by data alone" % (item, mid, ", ".join(water)))
    folder = "%s/%s" % (MOD_DIRS["building"], mid)
    mesh_root = os.path.normpath(os.path.join(mesh_dir or DEFAULT_MESH_DIR, mid))

    def mesh(name):
        if not name.endswith(".Model") and not name.endswith(".Model.timbermesh"):
            raise GenError("%s: model %s: unexpected mesh name %s" % (item, mid, name))
        base = name[:-len(".timbermesh")] if name.endswith(".timbermesh") else name
        gen.model_files["%s/%s.timbermesh" % (folder, base)] = os.path.join(mesh_root, base + ".timbermesh")
        return "%s/%s" % (folder, base)

    for k in mj.get("removeSpecs") or []:
        data.pop(k, None)
    for k, v in (mj.get("addSpecs") or {}).items():
        data[k] = copy.deepcopy(v)

    bos = data.get("BlockObjectSpec")
    if bos is None:
        raise GenError("%s: basis has no BlockObjectSpec" % item)
    size = mj["size"]
    if mj.get("blocks"):
        if len(mj["blocks"]) != size["X"] * size["Y"] * size["Z"]:
            raise GenError("%s: model %s has %d blocks for size %s" % (item, mid, len(mj["blocks"]), size))
        bos["Size"] = v3(size)
        bos["Blocks"] = copy.deepcopy(mj["blocks"])
    elif bos.get("Size") != v3(size):
        raise GenError("%s: model %s keeps the stand-in's blocks (blocks: null) but its size %s differs from the "
                       "basis %s" % (item, mid, size, bos.get("Size")))
    if mj.get("entrance"):
        bos["Entrance"] = {"HasEntrance": True, "Coordinates": v3(mj["entrance"])}
    if mj.get("access"):
        if "BuildingAccessibleSpec" not in data:
            raise GenError("%s: model %s has an access point but the basis has no BuildingAccessibleSpec" % (item, mid))
        data["BuildingAccessibleSpec"]["LocalAccess"] = v3(mj["access"])

    children = data.get("Children") or {}
    fin = children.get("#Finished")
    if fin is None:
        raise GenError("%s: basis has no #Finished child" % item)
    fin["TimbermeshSpec"] = {"Model": mesh(mj["models"]["finished"])}
    if mj.get("colliders"):
        fin["CollidersSpec"] = {"BoxColliders": copy.deepcopy(mj["colliders"]), "SphereColliders": [],
                                "CapsuleColliders": []}

    unf_parent = children.get("#Unfinished")
    if unf_parent is not None and mj["models"].get("constructionStage0"):
        unf = unf_parent.setdefault("Children", {})
        base = "ConstructionBase%dx%d" % (size["X"], size["Y"])
        if not gen.v.paths.get(("constructionbases/%s/%s.blueprint" % (base, base)).lower()):
            base = "ConstructionBase1x1"   # no vanilla pad of this size (models.md: exactly one base is required)
        stage = {"TimbermeshSpec": {"Model": mesh(mj["models"]["constructionStage0"])},
                 "CollidersSpec": {"BoxColliders": [{"Center": {"X": size["X"] / 2, "Y": 0.05, "Z": size["Y"] / 2},
                                                     "Size": {"X": size["X"], "Y": 0.1, "Z": size["Y"]}}],
                                   "SphereColliders": [], "CapsuleColliders": []}}
        # models.md: exactly one ConstructionBase first, then ConstructionStage0 (child order drives the visualiser)
        unf.clear()
        unf[base + "#nested"] = {"BlueprintPath": "ConstructionBases/%s/%s.blueprint" % (base, base)}
        unf["ConstructionStage0"] = stage
        if "ConstructionSiteProgressVisualizerSpec" in data:
            data["ConstructionSiteProgressVisualizerSpec"]["ProgressThresholds"] = [0.0]

    for a in mj.get("attachments") or []:
        hits = [at for at in (data.get("TemplateAttachmentsSpec") or {}).get("Attachments", [])
                if at.get("AttachmentId") == a["AttachmentId"]]
        if not hits:
            raise GenError("%s: model %s places attachment %s, which the basis does not have"
                           % (item, mid, a["AttachmentId"]))
        for at in hits:
            at["Position"] = v3(a["Position"])
    if mj.get("connectionAnchor"):
        if "ConnectionAnchorPointSpec" not in data:
            raise GenError("%s: model %s has a connectionAnchor but the basis has no ConnectionAnchorPointSpec"
                           % (item, mid))
        data["ConnectionAnchorPointSpec"]["Position"] = v3(mj["connectionAnchor"])
    if mj.get("windRotationAnimator"):
        data["WindRotationAnimatorSpec"] = copy.deepcopy(mj["windRotationAnimator"])
    gen.adopted_models[mid] = {"item": item, "modelJson": os.path.relpath(path, REPO).replace("\\", "/"),
                               "standIn": mj.get("standIn")}
    return mj
