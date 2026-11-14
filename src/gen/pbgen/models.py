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
              "connectionAnchor", "windRotationAnimator", "walkUnder", "liquidPlane", "displayName", "bell",
              "observatoryAnimator"}
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
    elif bos.get("Size") != v3(size) and mj.get("standIn") in gen.v.templates:
        # blocks: null means "the stand-in's blocks"; the catalogue put the model on another basis, so take them
        # from the stand-in the model was made for
        sbos = gen.v.get(gen.v.templates[mj["standIn"]]).get("BlockObjectSpec") or {}
        if sbos.get("Size") != v3(size):
            raise GenError("%s: model %s size %s differs from its stand-in %s" % (item, mid, size, mj["standIn"]))
        bos["Size"] = copy.deepcopy(sbos["Size"])
        bos["Blocks"] = copy.deepcopy(sbos["Blocks"])
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
    if mj.get("observatoryAnimator"):
        if "ObservatoryAnimatorSpec" not in data:
            raise GenError("%s: model %s names observatory nodes but the basis has no ObservatoryAnimatorSpec" % (item, mid))
        data["ObservatoryAnimatorSpec"].update(copy.deepcopy(mj["observatoryAnimator"]))
    if mj.get("windRotationAnimator"):
        data["WindRotationAnimatorSpec"] = copy.deepcopy(mj["windRotationAnimator"])
    gen.adopted_models[mid] = {"item": item, "modelJson": os.path.relpath(path, REPO).replace("\\", "/"),
                               "standIn": mj.get("standIn")}
    return mj



# ------------------------------------------------------------------------------------------------------- plants
PLANT_KEYS = {"id", "template", "kind", "material", "materialAsset", "materialCollection", "bundle", "modelDir", "models",
              "PlantablePreviewModelSpec.Model", "builtTo", "stats", "budgetFlags", "basis", "blockHeight", "water",
              "randomizer", "colliders", "treeCuttingRadius", "gatherableDetail", "notes", "generatedBy"}
DEFAULT_PLANT_DIR = r"E:\PandabornDev\build\plants"


def _colliders(spec):
    out = {"BoxColliders": [], "SphereColliders": [], "CapsuleColliders": []}
    if "box" in spec:
        b = spec["box"]
        out["BoxColliders"].append({"Center": dict(zip("XYZ", b["center"])), "Size": dict(zip("XYZ", b["size"]))})
    if "capsule" in spec:
        c = spec["capsule"]
        out["CapsuleColliders"].append({"Center": dict(zip("XYZ", c["center"])), "Radius": c["radius"],
                                        "Height": c["height"], "Axis": "Y"})
    return out


def _merge(base, over):
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _merge(base[k], v)
        else:
            base[k] = copy.deepcopy(v)


def apply_plant_model(gen, data, mid, item):
    """Applies art/plants/<Id>/model.json (docs/tech/plants.md, "What the catalogue lane must change"): the model of
    every growth stage and state under #Models (Seedling|Mature / #Alive|#Dying|#Dead, #Leftover for trees), each
    stage's colliders, the preview model, the randomizer (replaces or adds NaturalResourceModelRandomizerSpec) and the
    tree cutting radius, merged over the basis as the plant prototype's optional merge did. The meshes are copied from
    the plant build folder; the material collection and the bundle are registered for the faction."""
    mj, path = load_model("plant", mid, item)
    unknown = sorted(set(mj) - PLANT_KEYS)
    if unknown:
        gen.note(item, "plant model %s: model.json keys not used by the generator: %s" % (mid, ", ".join(unknown)))
    built = os.path.join(gen.plant_dir or DEFAULT_PLANT_DIR, mid)
    col = mj.get("colliders") if isinstance(mj.get("colliders"), dict) else {}
    tree = {}
    for key, mpath in mj["models"].items():
        gen.model_files[mpath + ".timbermesh"] = os.path.normpath(
            os.path.join(built, mpath.rsplit("/", 1)[-1] + ".timbermesh"))
        node = {"TimbermeshSpec": {"Model": mpath}}
        if key == "#Leftover":
            if "#Leftover" in col:
                node["CollidersSpec"] = _colliders(col["#Leftover"])
            tree["#Leftover"] = node
            continue
        stage, state = key.split("/")
        if stage in col:
            node["CollidersSpec"] = _colliders(col[stage])
        tree.setdefault(stage, {"Children": {}})["Children"][state] = node
    if "#Models" not in (data.get("Children") or {}):
        raise GenError("%s: basis has no #Models child for plant model %s" % (item, mid))
    _merge(data, {"Children": {"#Models": {"Children": tree}}})
    if mj.get("PlantablePreviewModelSpec.Model"):
        data.setdefault("PlantablePreviewModelSpec", {})["Model"] = mj["PlantablePreviewModelSpec.Model"]
    if mj.get("randomizer"):
        data["NaturalResourceModelRandomizerSpec"] = {k: v for k, v in mj["randomizer"].items() if k != "note"}
    if mj.get("treeCuttingRadius"):
        if "TreeCuttingRadiusSpec" not in data:
            raise GenError("%s: model %s sets a tree cutting radius but the basis has no TreeCuttingRadiusSpec"
                           % (item, mid))
        data["TreeCuttingRadiusSpec"]["Radius"] = mj["treeCuttingRadius"]
    if mj.get("materialCollection") and mj.get("materialAsset"):
        mats = gen.material_collections.setdefault(mj["materialCollection"], [])
        if mj["materialAsset"] not in mats:
            mats.append(mj["materialAsset"])
    if mj.get("bundle"):
        gen.bundles_needed.add(mj["bundle"])
    gen.adopted_models["plant:" + mid] = {"item": item, "modelJson": os.path.relpath(path, REPO).replace(chr(92), "/"),
                                         "standIn": mj.get("basis")}
    return mj
