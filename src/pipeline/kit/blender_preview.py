"""Blender side of the model preview (run by preview.py; Blender 4.5, headless, --factory-startup).

blender -b --factory-startup --python blender_preview.py -- job.json

job.json: {"items": [{"npz": path}], "textures": dir, "spec": look_spec.json, "out": {"day": png, "night": png},
           "size": [w, h], "yaw": deg, "pitch": deg, "focal": mm, "samples": n, "frame": [x0, y0, x1, y1] (Blender XY
           bounds to frame; default: everything), "grid": [x0, y0, x1, y1] tile grid drawn on the ground}
Materials are looked up by the vanilla name in the look spec: albedo x _Color x vertex colour x AO, the swizzled
normal map (R=1, G=y, A=x), smoothness from M.a, and the WindowsAtlas glow map (emission at night only), so a
preview looks like the faction's materials in game. Unknown names get a flat colour.
"""
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

job = json.load(open(sys.argv[sys.argv.index("--") + 1]))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

FLAT = {"Dirt": (0.36, 0.28, 0.2), "Path.Folktails": (0.62, 0.52, 0.38), "Water": (0.2, 0.35, 0.45),
        "BeaverCarryingModels": (0.6, 0.5, 0.4), "": (1, 0, 1)}


def load_spec():
    spec = json.load(open(job["spec"]))
    out = {}
    for m in spec["materials"]:
        tex = {t["key"]: os.path.join(job["textures"], os.path.basename(t["value"])) for t in m["textures"]}
        col = {c["key"]: c["value"] for c in m.get("colors", [])}
        tint = col.get("_Color", [1, 1, 1, 1])
        if isinstance(tint, dict):
            tint = [tint.get(k, 1) for k in "rgba"]
        out[m["name"]] = (tex, tint)
    return out


SPEC = load_spec()
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


def material(name, night):
    if name in MATS:
        return MATS[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Specular IOR Level"].default_value = 0.25
    vc = nt.nodes.new("ShaderNodeVertexColor")
    vc.layer_name = "Col"
    if name in SPEC:
        tex, tint = SPEC[name]
        d = nt.nodes.new("ShaderNodeTexImage")
        d.image = image(tex["_MainTex"])
        mul = nt.nodes.new("ShaderNodeMix")
        mul.data_type = "RGBA"
        mul.blend_type = "MULTIPLY"
        mul.inputs["Factor"].default_value = 1.0
        nt.links.new(d.outputs["Color"], mul.inputs[6])
        nt.links.new(vc.outputs["Color"], mul.inputs[7])
        mul2 = nt.nodes.new("ShaderNodeMix")
        mul2.data_type = "RGBA"
        mul2.blend_type = "MULTIPLY"
        mul2.inputs["Factor"].default_value = 1.0
        nt.links.new(mul.outputs[2], mul2.inputs[6])
        mul2.inputs[7].default_value = (tint[0], tint[1], tint[2], 1)
        last = mul2
        if "_AmbientOcclusion" in tex:
            ao = nt.nodes.new("ShaderNodeTexImage")
            ao.image = image(tex["_AmbientOcclusion"], True)
            mul3 = nt.nodes.new("ShaderNodeMix")
            mul3.data_type = "RGBA"
            mul3.blend_type = "MULTIPLY"
            mul3.inputs["Factor"].default_value = 1.0
            nt.links.new(last.outputs[2], mul3.inputs[6])
            nt.links.new(ao.outputs["Color"], mul3.inputs[7])
            last = mul3
        nt.links.new(last.outputs[2], bsdf.inputs["Base Color"])
        if "_BumpMap" in tex:
            n = nt.nodes.new("ShaderNodeTexImage")
            n.image = image(tex["_BumpMap"], True)
            sep = nt.nodes.new("ShaderNodeSeparateColor")
            nt.links.new(n.outputs["Color"], sep.inputs["Color"])
            comb = nt.nodes.new("ShaderNodeCombineColor")
            nt.links.new(n.outputs["Alpha"], comb.inputs[0])
            nt.links.new(sep.outputs[1], comb.inputs[1])
            comb.inputs[2].default_value = 1.0
            nm = nt.nodes.new("ShaderNodeNormalMap")
            nm.inputs["Strength"].default_value = 0.8
            nt.links.new(comb.outputs["Color"], nm.inputs["Color"])
            nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
        if "_MetallicGlossMap" in tex:
            m = nt.nodes.new("ShaderNodeTexImage")
            m.image = image(tex["_MetallicGlossMap"], True)
            inv = nt.nodes.new("ShaderNodeMath")
            inv.operation = "SUBTRACT"
            inv.inputs[0].default_value = 1.0
            nt.links.new(m.outputs["Alpha"], inv.inputs[1])
            nt.links.new(inv.outputs[0], bsdf.inputs["Roughness"])
        else:
            bsdf.inputs["Roughness"].default_value = 0.8
        if night and "_LightingMap" in tex:
            e = nt.nodes.new("ShaderNodeTexImage")
            e.image = image(tex["_LightingMap"])
            nt.links.new(e.outputs["Color"], bsdf.inputs["Emission Color"])
            bsdf.inputs["Emission Strength"].default_value = 6.0
    else:
        c = FLAT.get(name, (1.0, 0.0, 1.0))
        mul = nt.nodes.new("ShaderNodeMix")
        mul.data_type = "RGBA"
        mul.blend_type = "MULTIPLY"
        mul.inputs["Factor"].default_value = 1.0
        mul.inputs[6].default_value = (*c, 1)
        nt.links.new(vc.outputs["Color"], mul.inputs[7])
        nt.links.new(mul.outputs[2], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.9
    MATS[name] = mat
    return mat


def add_npz(path, night):
    z = np.load(path)
    meta = json.loads(bytes(z["meta"]).decode())
    objs, slots = [], []
    for e in meta:
        if "slot" in e:
            slots.append(e)
            continue
        k = e["k"]
        P, N, UV, C = z[f"P{k}"], z[f"N{k}"], z[f"UV{k}"], z[f"C{k}"]
        tris, mids = [], []
        for j, mname in enumerate(e["mats"]):
            t = z[f"i{k}_{j}"]
            tris.append(t)
            mids.append(np.full(len(t), j))
        if not tris:
            continue
        T = np.concatenate(tris)
        M = np.concatenate(mids)
        me = bpy.data.meshes.new(e["node"])
        me.vertices.add(len(P))
        me.vertices.foreach_set("co", P.ravel())
        me.loops.add(len(T) * 3)
        me.loops.foreach_set("vertex_index", T.ravel())
        me.polygons.add(len(T))
        me.polygons.foreach_set("loop_start", np.arange(0, len(T) * 3, 3))
        me.polygons.foreach_set("material_index", M)
        me.update()
        uv = me.uv_layers.new(name="UVMap")
        uv.data.foreach_set("uv", UV[T.ravel()].ravel())
        col = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
        col.data.foreach_set("color", C[T.ravel()].ravel())
        me.polygons.foreach_set("use_smooth", np.ones(len(T), bool))
        me.normals_split_custom_set_from_vertices([tuple(n) for n in N])
        for mname in e["mats"]:
            me.materials.append(material(mname, night))
        ob = bpy.data.objects.new(e["node"], me)
        sc.collection.objects.link(ob)
        objs.append(ob)
    return objs, slots


def ground(grid):
    x0, y0, x1, y1 = grid
    bpy.ops.mesh.primitive_plane_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, -0.002))
    g = bpy.context.object
    g.scale = (x1 - x0, y1 - y0, 1)
    mat = bpy.data.materials.new("ground")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 1.0
    # grass with a faint tile grid (tiles are 1 unit)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    lines = []
    for ax, scale in ((0, x1 - x0), (1, y1 - y0)):
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = scale
        nt.links.new(sep.outputs[ax], mul.inputs[0])
        add = nt.nodes.new("ShaderNodeMath")
        add.operation = "ADD"
        add.inputs[1].default_value = (x0 if ax == 0 else y0) + scale / 2
        nt.links.new(mul.outputs[0], add.inputs[0])
        fr = nt.nodes.new("ShaderNodeMath")
        fr.operation = "PINGPONG"
        fr.inputs[1].default_value = 0.5
        nt.links.new(add.outputs[0], fr.inputs[0])
        lt = nt.nodes.new("ShaderNodeMath")
        lt.operation = "LESS_THAN"
        lt.inputs[1].default_value = 0.015
        nt.links.new(fr.outputs[0], lt.inputs[0])
        lines.append(lt)
    mx = nt.nodes.new("ShaderNodeMath")
    mx.operation = "MAXIMUM"
    nt.links.new(lines[0].outputs[0], mx.inputs[0])
    nt.links.new(lines[1].outputs[0], mx.inputs[1])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(mx.outputs[0], mix.inputs["Factor"])
    mix.inputs[6].default_value = (0.20, 0.34, 0.10, 1)
    mix.inputs[7].default_value = (0.15, 0.25, 0.08, 1)
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    g.data.materials.append(mat)


def setup(night):
    sc.render.engine = "CYCLES"
    sc.cycles.samples = job.get("samples", 48)
    sc.cycles.use_denoising = True
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "OPTIX"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type == "OPTIX"
        sc.cycles.device = "GPU"
    except Exception as ex:  # noqa: BLE001
        print("GPU setup failed", ex)
    sc.render.resolution_x, sc.render.resolution_y = job.get("size", [1200, 800])
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bpy.ops.object.light_add(type="SUN")
    sun = bpy.context.object
    if night:
        bg.inputs["Color"].default_value = (0.03, 0.04, 0.09, 1)
        bg.inputs["Strength"].default_value = 1.0
        sun.data.energy = 0.25
        sun.data.color = (0.6, 0.7, 1.0)
    else:
        bg.inputs["Color"].default_value = (0.55, 0.65, 0.85, 1)
        bg.inputs["Strength"].default_value = 0.9
        sun.data.energy = 3.2
        sun.data.color = (1.0, 0.96, 0.88)
    sun.data.angle = math.radians(3)
    sun.rotation_euler = (math.radians(-42), math.radians(0), math.radians(-30))


def camera(objs):
    pts = [ob.matrix_world @ Vector(c) for ob in objs for c in ob.bound_box]
    if job.get("frame"):
        x0, y0, x1, y1 = job["frame"]
        zmax = max(p.z for p in pts) if pts else 2
        pts = [Vector((x, y, z)) for x in (x0, x1) for y in (y0, y1) for z in (0, zmax)]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    c = (lo + hi) / 2
    yaw, pitch = math.radians(job.get("yaw", 25)), math.radians(job.get("pitch", 50))
    # the model's front (Unity -Z, the grid's -Y where entrances are) is Blender +Y: look from there, like the game
    d = Vector((-math.sin(yaw) * math.cos(pitch), math.cos(yaw) * math.cos(pitch), math.sin(pitch)))
    bpy.ops.object.camera_add()
    cam = bpy.context.object
    cam.data.lens = job.get("focal", 85)
    cam.data.sensor_width = 36
    sc.camera = cam
    rot = (-d).to_track_quat("-Z", "Y")
    cam.rotation_euler = rot.to_euler()
    # fit: project points on the camera plane and find the distance that fits them
    right = rot @ Vector((1, 0, 0))
    up = rot @ Vector((0, 1, 0))
    w, h = sc.render.resolution_x, sc.render.resolution_y
    fx = cam.data.lens / cam.data.sensor_width * (1 if w >= h else w / h)
    fy = fx * w / h
    need = 0.0
    for p in pts:
        v = p - c
        x, y, z = v.dot(right), v.dot(up), v.dot(d)
        need = max(need, abs(x) / (0.5 / fx) * 1.08 + z, abs(y) / (0.5 / fy) * 1.08 + z)
    cam.location = c + d * need
    cam.data.clip_end = 1000


items = job["items"]
for mode in ("day", "night"):
    out = job["out"].get(mode)
    if not out:
        continue
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    MATS.clear()
    for m in list(bpy.data.materials):
        bpy.data.materials.remove(m)
    night = mode == "night"
    setup(night)
    allobjs = []
    for it in items:
        objs, slots = add_npz(it["npz"], night)
        allobjs += objs
        if job.get("showSlots"):
            for s in slots:
                bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06, location=s["pos"])
                m = bpy.data.materials.new("slot")
                m.use_nodes = True
                m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (1, 0, 0.6, 1)
                bpy.context.object.data.materials.append(m)
    if job.get("grid"):
        ground(job["grid"])
    if night:
        # a weak warm fill so night shots are readable, like the game's night grading
        bpy.ops.object.light_add(type="AREA", location=(0, -6, 8))
        bpy.context.object.data.energy = 60
        bpy.context.object.data.color = (0.5, 0.55, 0.9)
        bpy.context.object.data.size = 12
    camera(allobjs)
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("WROTE", out)
