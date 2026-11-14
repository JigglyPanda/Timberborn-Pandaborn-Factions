"""Blender side of the plant previews (run by preview.py; Blender 4.5, headless, --factory-startup).

blender -b --factory-startup --python blender_field.py -- job.json

job.json (all positions in Unity space, converted here: (x, y, z) -> (-x, -z, y)):
  "materials": {name: {"D": png, "N": png|null, "Detail": png|null, "detail": bool, "detailUseColor": 0|1}}
  "models": {key: npz from mesh.to_blender_npz}
  "instances": [{"model": key, "pos": [x, y, z] (cell corner), "rot": deg about the cell centre, "w": s, "h": s}]
  "ground": [x0, z0, x1, z1], "groundColor": [r, g, b], "dry": [[x0, z0, x1, z1], ...] darker soil patches,
  "water": [{"rect": [x0, z0, x1, z1], "level": y}],
  "camera": {"target": [x, y, z], "yaw": deg, "pitch": deg, "distance": d, "focal": mm}, "size": [w, h],
  "samples": n, "night": bool, "out": png
The material emulates VegetationURP: albedo x vertex colour, cut out at alpha 0.5; with "detail" the detail map
(sampled with uv2) is laid over (alpha = max) as the game does for a gatherable that has its yield.
"""
import json
import math
import sys

import bpy
import numpy as np

job = json.load(open(sys.argv[sys.argv.index("--") + 1]))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene


def ub(p):
    return (-p[0], -p[2], p[1])


IMAGES = {}


def image(path, non_color=False):
    if path not in IMAGES:
        im = bpy.data.images.load(path)
        im.alpha_mode = "CHANNEL_PACKED"
        if non_color:
            im.colorspace_settings.name = "Non-Color"
        IMAGES[path] = im
    return IMAGES[path]


MATS = {}


def mix(nt, a, b, blend="MULTIPLY", fac=1.0):
    m = nt.nodes.new("ShaderNodeMix")
    m.data_type = "RGBA"
    m.blend_type = blend
    m.inputs["Factor"].default_value = fac
    if isinstance(a, tuple):
        m.inputs[6].default_value = a
    else:
        nt.links.new(a, m.inputs[6])
    if isinstance(b, tuple):
        m.inputs[7].default_value = b
    else:
        nt.links.new(b, m.inputs[7])
    return m


def material(name):
    if name in MATS:
        return MATS[name]
    spec = job["materials"].get(name)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.blend_method = "CLIP" if hasattr(mat, "blend_method") else None
    nt = mat.node_tree
    out = nt.nodes["Material Output"]
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Specular IOR Level"].default_value = 0.2
    bsdf.inputs["Roughness"].default_value = 0.75
    vc = nt.nodes.new("ShaderNodeVertexColor")
    vc.layer_name = "Col"
    if spec is None:
        bsdf.inputs["Base Color"].default_value = (1, 0, 1, 1)
        MATS[name] = mat
        return mat
    uv0 = nt.nodes.new("ShaderNodeUVMap")
    uv0.uv_map = "UV0"
    d = nt.nodes.new("ShaderNodeTexImage")
    d.image = image(spec["D"])
    nt.links.new(uv0.outputs["UV"], d.inputs["Vector"])
    col = mix(nt, d.outputs["Color"], vc.outputs["Color"]).outputs[2]
    alpha = d.outputs["Alpha"]
    if spec.get("detail") and spec.get("Detail"):
        uv2 = nt.nodes.new("ShaderNodeUVMap")
        uv2.uv_map = "UV2"
        dt = nt.nodes.new("ShaderNodeTexImage")
        dt.image = image(spec["Detail"])
        nt.links.new(uv2.outputs["UV"], dt.inputs["Vector"])
        dcol = dt.outputs["Color"]
        if spec.get("detailUseColor"):
            dcol = mix(nt, dcol, vc.outputs["Color"]).outputs[2]
        m = nt.nodes.new("ShaderNodeMix")
        m.data_type = "RGBA"
        nt.links.new(dt.outputs["Alpha"], m.inputs["Factor"])
        nt.links.new(col, m.inputs[6])
        nt.links.new(dcol, m.inputs[7])
        col = m.outputs[2]
        mx = nt.nodes.new("ShaderNodeMath")
        mx.operation = "MAXIMUM"
        nt.links.new(alpha, mx.inputs[0])
        nt.links.new(dt.outputs["Alpha"], mx.inputs[1])
        alpha = mx.outputs[0]
    nt.links.new(col, bsdf.inputs["Base Color"])
    # the game culls back faces of vegetation (VegetationURP RenderFace = Front): so does the preview
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    front = nt.nodes.new("ShaderNodeMath")
    front.operation = "SUBTRACT"
    front.inputs[0].default_value = 1.0
    nt.links.new(geo.outputs["Backfacing"], front.inputs[1])
    cull = nt.nodes.new("ShaderNodeMath")
    cull.operation = "MULTIPLY"
    nt.links.new(alpha, cull.inputs[0])
    nt.links.new(front.outputs[0], cull.inputs[1])
    alpha = cull.outputs[0]
    gt = nt.nodes.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = 0.5
    nt.links.new(alpha, gt.inputs[0])
    nt.links.new(gt.outputs[0], bsdf.inputs["Alpha"])
    if spec.get("N"):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = image(spec["N"], True)
        nt.links.new(uv0.outputs["UV"], n.inputs["Vector"])
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(n.outputs["Color"], sep.inputs["Color"])
        comb = nt.nodes.new("ShaderNodeCombineColor")
        nt.links.new(n.outputs["Alpha"], comb.inputs[0])
        nt.links.new(sep.outputs[1], comb.inputs[1])
        comb.inputs[2].default_value = 1.0
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.uv_map = "UV0"
        nm.inputs["Strength"].default_value = 0.7
        nt.links.new(comb.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    MATS[name] = mat
    return mat


MESHES = {}


def mesh_for(key):
    if key in MESHES:
        return MESHES[key]
    z = np.load(job["models"][key])
    meta = json.loads(bytes(z["meta"]).decode())
    Ps, Ts, U0s, U2s, Cs, Ms, mats = [], [], [], [], [], [], []
    base = 0
    for e in meta:
        k = e["k"]
        P = z[f"P{k}"].astype(np.float64)
        P[:, 0] += 0.5     # recentre: the cell centre (Unity 0.5, 0, 0.5) is Blender (-0.5, -0.5, 0)
        P[:, 1] += 0.5
        Ps.append(P)
        Ts.append(z[f"T{k}"] + base)
        U0s.append(z[f"UV{k}"])
        U2s.append(z[f"UVD{k}"])
        Cs.append(z[f"C{k}"])
        Ms.append(np.full(len(z[f"T{k}"]), len(mats)))
        mats.append(e["mat"])
        base += len(P)
    P, T = np.concatenate(Ps), np.concatenate(Ts)
    me = bpy.data.meshes.new(key)
    me.vertices.add(len(P))
    me.vertices.foreach_set("co", P.ravel())
    me.loops.add(len(T) * 3)
    me.loops.foreach_set("vertex_index", T.ravel())
    me.polygons.add(len(T))
    me.polygons.foreach_set("loop_start", np.arange(0, len(T) * 3, 3))
    me.polygons.foreach_set("material_index", np.concatenate(Ms))
    me.update()
    for nm, U in (("UV0", np.concatenate(U0s)), ("UV2", np.concatenate(U2s))):
        uv = me.uv_layers.new(name=nm)
        uv.data.foreach_set("uv", U[T.ravel()].ravel())
    col = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
    col.data.foreach_set("color", np.concatenate(Cs)[T.ravel()].ravel())
    me.polygons.foreach_set("use_smooth", np.ones(len(T), bool))
    N = np.concatenate([z[f"N{e['k']}"] for e in meta])
    me.normals_split_custom_set_from_vertices([tuple(n) for n in N])
    for m in mats:
        me.materials.append(material(m))
    MESHES[key] = me
    return me


def flat_material(name, rgb, rough=1.0, emission=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    return m


def soil_material(name, rgb):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 1.0
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (rgb[0] * 0.8, rgb[1] * 0.8, rgb[2] * 0.8, 1)
    ramp.color_ramp.elements[1].color = (rgb[0] * 1.15, rgb[1] * 1.12, rgb[2] * 1.1, 1)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    return m


def box(name, lo, hi, mat):
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob = bpy.context.object
    ob.name = name
    ob.location = ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2)
    ob.scale = (hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])
    ob.data.materials.append(mat)
    return ob


def ground():
    gc = job.get("groundColor", [0.33, 0.27, 0.18])
    soil = soil_material("soil", gc)
    for i, g in enumerate(job.get("grounds", [])):   # [x0, z0, x1, z1, top y] terraces
        x0, z0, x1, z1, top = g
        b0, b1 = ub((x0, 0, z0)), ub((x1, 0, z1))
        box("g%d" % i, (min(b0[0], b1[0]), min(b0[1], b1[1]), top - 6), (max(b0[0], b1[0]), max(b0[1], b1[1]), top), soil)
    if job.get("ground"):
        x0, z0, x1, z1 = job["ground"]
        b0, b1 = ub((x0, 0, z0)), ub((x1, 0, z1))
        box("ground", (min(b0[0], b1[0]), min(b0[1], b1[1]), -6), (max(b0[0], b1[0]), max(b0[1], b1[1]), 0), soil)
    wet = soil_material("wet", [c * 0.62 for c in gc])
    for i, r in enumerate(job.get("wet", [])):
        x0, z0, x1, z1 = r[:4]
        top = r[4] if len(r) > 4 else 0.0
        b0, b1 = ub((x0, 0, z0)), ub((x1, 0, z1))
        box("wet%d" % i, (min(b0[0], b1[0]), min(b0[1], b1[1]), top - 0.02), (max(b0[0], b1[0]), max(b0[1], b1[1]), top + 0.003), wet)
    for i, w in enumerate(job.get("water", [])):
        x0, z0, x1, z1 = w["rect"]
        b0, b1 = ub((x0, 0, z0)), ub((x1, 0, z1))
        m = bpy.data.materials.new("water%d" % i)
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (0.16, 0.28, 0.30, 1)
        b.inputs["Roughness"].default_value = 0.08
        b.inputs["Alpha"].default_value = 0.72
        box("water%d" % i, (min(b0[0], b1[0]), min(b0[1], b1[1]), w.get("floor", 0.0) - 0.01),
            (max(b0[0], b1[0]), max(b0[1], b1[1]), w["level"]), m)


def lights(night):
    sc.render.engine = "CYCLES"
    sc.cycles.samples = job.get("samples", 48)
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.cycles.transparent_max_bounces = 16
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "OPTIX"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type == "OPTIX"
        sc.cycles.device = "GPU"
    except Exception as ex:  # noqa: BLE001
        print("GPU setup failed", ex)
    sc.render.resolution_x, sc.render.resolution_y = job.get("size", [1600, 1000])
    sc.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bpy.ops.object.light_add(type="SUN")
    sun = bpy.context.object
    if night:
        bg.inputs["Color"].default_value = (0.05, 0.07, 0.15, 1)
        bg.inputs["Strength"].default_value = 1.2
        sun.data.energy = 0.35
        sun.data.color = (0.6, 0.7, 1.0)
    else:
        bg.inputs["Color"].default_value = (0.62, 0.70, 0.85, 1)
        bg.inputs["Strength"].default_value = 0.95
        sun.data.energy = 3.4
        sun.data.color = (1.0, 0.95, 0.85)
    sun.data.angle = math.radians(4)
    sun.rotation_euler = (math.radians(-40), math.radians(0), math.radians(-35))


def camera():
    c = job["camera"]
    tgt = ub(c["target"])
    yaw, pitch = math.radians(c.get("yaw", 0)), math.radians(c.get("pitch", 50))
    d = c.get("distance", 20)
    # the game camera looks from the south-ish side of the map down at the target; yaw 0 = looking along Unity +z
    fwd_u = (math.sin(yaw) * math.cos(pitch), -math.sin(pitch), math.cos(yaw) * math.cos(pitch))
    pos_u = (c["target"][0] - fwd_u[0] * d, c["target"][1] - fwd_u[1] * d, c["target"][2] - fwd_u[2] * d)
    bpy.ops.object.camera_add(location=ub(pos_u))
    cam = bpy.context.object
    cam.data.lens = c.get("focal", 50)
    cam.data.sensor_width = 36
    cam.data.clip_end = 2000
    from mathutils import Vector
    direction = Vector(tgt) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam


lights(job.get("night", False))
ground()
for i, inst in enumerate(job["instances"]):
    me = mesh_for(inst["model"])
    ob = bpy.data.objects.new("i%d" % i, me)
    x, y, z = inst["pos"]
    ob.location = ub((x + 0.5, y, z + 0.5))
    ob.rotation_euler = (0, 0, math.radians(inst.get("rot", 0)))
    w, h = inst.get("w", 1.0), inst.get("h", 1.0)
    ob.scale = (w, w, h)
    sc.collection.objects.link(ob)
camera()
sc.render.filepath = job["out"]
bpy.ops.render.render(write_still=True)
print("WROTE", job["out"])
