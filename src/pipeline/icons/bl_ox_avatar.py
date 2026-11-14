"""Blender side of the Wooden Ox bot avatar (see ox_avatar.py): builds a generic wooden ox from planks in code and
renders a three-quarter bust on a transparent film. Generic on purpose: the ox's game body is not built yet, so this
shows only what any Wooden Ox will have (plank body and head, horns, a rope harness, a lantern hung at a horn, a
wheel under the chest).

blender -b --factory-startup --python bl_ox_avatar.py -- OUT.png [samples]
"""
import math
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]
SAMPLES = int(argv[1]) if len(argv) > 1 else 96

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
            for d in prefs.devices:
                d.use = True
            sc.cycles.device = "GPU"
            break
        except Exception:  # noqa: BLE001
            continue
except Exception:  # noqa: BLE001
    pass
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = 1024
sc.view_settings.view_transform = "Standard"
sc.view_settings.exposure = -0.2
world = bpy.data.worlds.new("W")
sc.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.09, 0.10, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.6


def wood_mat(name, base, dark, scale=6.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 1.0, 8.0)
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = scale
    wave.inputs["Distortion"].default_value = 6.0
    wave.inputs["Detail"].default_value = 3.0
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 18.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = dark + (1,)
    ramp.color_ramp.elements[1].color = base + (1,)
    mix = nt.nodes.new("ShaderNodeMath")
    mix.operation = "MULTIPLY_ADD"
    mix.inputs[1].default_value = 0.7
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], wave.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], noise.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], mix.inputs[0])
    nt.links.new(noise.outputs["Fac"], mix.inputs[2])
    nt.links.new(mix.outputs[0], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.72
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    nt.links.new(wave.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def flat_mat(name, color, rough=0.8, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = color + (1,)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = emit + (1,)
        b.inputs["Emission Strength"].default_value = strength
    return m


WOOD = wood_mat("Wood", (0.42, 0.22, 0.09), (0.17, 0.08, 0.03))
WOOD_D = wood_mat("WoodDark", (0.26, 0.12, 0.05), (0.09, 0.04, 0.015), 9.0)
ROPE = flat_mat("Rope", (0.40, 0.28, 0.14), 0.95)
IRON = flat_mat("Iron", (0.10, 0.10, 0.11), 0.45)
PAPER = flat_mat("Paper", (0.70, 0.08, 0.04), 0.6, emit=(0.95, 0.22, 0.06), strength=1.6)
EYE = flat_mat("Eye", (0.02, 0.02, 0.02), 0.25)


def box(name, loc, size, mat, rot=(0, 0, 0), bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        m = o.modifiers.new("Bevel", "BEVEL")
        m.width = bevel
        m.segments = 2
    o.data.materials.append(mat)
    return o


def cyl(name, loc, r, depth, mat, rot=(0, 0, 0), verts=24):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return o


def tube(name, pts, r, mat, taper=None):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = 4
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts):
        p.co = (q[0], q[1], q[2], 1)
    if taper:
        for p, t in zip(sp.points, taper):
            p.radius = t
    sp.use_smooth = True
    o = bpy.data.objects.new(name, cu)
    sc.collection.objects.link(o)
    o.data.materials.append(mat)
    return o


# The ox faces -Y (towards the camera's left); z up. Body: planks laid lengthwise with small gaps.
for k, z in enumerate((0.70, 0.86, 1.02)):
    box("Plank%d" % k, (0, 0.25, z), (0.66, 1.30, 0.15), WOOD if k % 2 == 0 else WOOD_D)
box("Saddle", (0, 0.35, 1.12), (0.72, 0.40, 0.06), WOOD_D)
for x in (-0.36, 0.36):                                   # side boards with pegs
    box("Side", (x, 0.25, 0.86), (0.04, 1.20, 0.42), WOOD_D)
    for y in (-0.2, 0.25, 0.7):
        cyl("Peg", (x * 1.06, y, 0.86), 0.035, 0.03, IRON, rot=(0, math.pi / 2, 0), verts=12)
# Neck and head
box("Neck", (0, -0.42, 1.10), (0.42, 0.36, 0.40), WOOD, rot=(math.radians(-25), 0, 0))
box("Head", (0, -0.70, 1.30), (0.46, 0.44, 0.40), WOOD)
box("Snout", (0, -0.98, 1.20), (0.36, 0.26, 0.26), WOOD_D)
box("Brow", (0, -0.86, 1.44), (0.48, 0.06, 0.08), WOOD_D)
for x in (-0.12, 0.12):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, location=(x * 1.6, -0.91, 1.36))
    bpy.context.object.data.materials.append(EYE)
    bpy.ops.object.shade_smooth()
    cyl("Nostril", (x * 0.8, -1.115, 1.20), 0.03, 0.02, EYE, rot=(math.pi / 2, 0, 0), verts=12)
for sx in (-1, 1):                                        # ears and horns
    box("Ear", (sx * 0.30, -0.62, 1.42), (0.16, 0.05, 0.09), WOOD, rot=(0, sx * math.radians(25), 0))
    tube("Horn", [(sx * 0.18, -0.66, 1.48), (sx * 0.34, -0.66, 1.60), (sx * 0.44, -0.74, 1.76), (sx * 0.42, -0.86, 1.86)],
         0.05, WOOD_D, taper=[1.0, 0.85, 0.6, 0.3])
# Rope harness: a collar round the neck, a line along the back, a halter on the snout
tube("Collar", [(0.24 * math.cos(a), -0.42 + 0.20 * math.sin(a), 1.08 + 0.16 * math.sin(a)) for a in
                [i * math.pi / 8 for i in range(17)]], 0.02, ROPE)
tube("Halter", [(0.20 * math.cos(a), -0.98 + 0.15 * math.sin(a), 1.22 + 0.15 * math.sin(a)) for a in
                [i * math.pi / 8 for i in range(17)]], 0.022, ROPE)
tube("Rein", [(0.20, -0.98, 1.22), (0.26, -0.70, 1.10), (0.30, -0.30, 1.16), (0.30, 0.3, 1.18)], 0.022, ROPE)
# Legs and the wheel under the chest
for x in (-0.24, 0.24):
    for y in (-0.22, 0.75):
        box("Leg", (x, y, 0.32), (0.13, 0.15, 0.62), WOOD_D)
cyl("Wheel", (0, -0.20, 0.38), 0.36, 0.10, WOOD, rot=(0, math.pi / 2, 0), verts=32)
cyl("Tyre", (0, -0.20, 0.38), 0.37, 0.07, IRON, rot=(0, math.pi / 2, 0), verts=32)
cyl("Hub", (0, -0.20, 0.38), 0.07, 0.16, IRON, rot=(0, math.pi / 2, 0), verts=16)
# The lantern hung from the right horn
tube("String", [(0.42, -0.86, 1.84), (0.50, -0.92, 1.70), (0.52, -0.94, 1.56)], 0.008, ROPE)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(0.52, -0.94, 1.44), segments=16, ring_count=10)
lan = bpy.context.object
lan.scale = (1, 1, 1.15)
lan.data.materials.append(PAPER)
bpy.ops.object.shade_smooth()
for z in (1.575, 1.305):
    cyl("Cap", (0.52, -0.94, z), 0.06, 0.03, WOOD_D, verts=16)
pl = bpy.data.lights.new("LanternGlow", "POINT")
pl.energy = 12
pl.color = (1.0, 0.55, 0.25)
pl.shadow_soft_size = 0.1
po = bpy.data.objects.new("LanternGlow", pl)
po.location = (0.52, -0.94, 1.44)
sc.collection.objects.link(po)


def look(o, target):
    d = Vector(target) - o.location
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def area(name, loc, energy, size, color, target=(0, -0.4, 1.2)):
    L = bpy.data.lights.new(name, "AREA")
    L.energy, L.size, L.color = energy, size, color
    o = bpy.data.objects.new(name, L)
    o.location = loc
    sc.collection.objects.link(o)
    look(o, target)


area("Key", (-2.2, -2.6, 2.8), 260, 2.0, (1.0, 0.86, 0.68))
area("Rim", (2.0, 1.6, 2.2), 300, 1.4, (0.62, 0.80, 1.0))
area("Fill", (2.4, -2.2, 1.0), 50, 2.5, (0.85, 0.92, 1.0))
cam = bpy.data.cameras.new("Cam")
cam.lens = 66
co = bpy.data.objects.new("Cam", cam)
sc.collection.objects.link(co)
co.location = (-1.6, -3.3, 1.9)
look(co, (0.08, -0.5, 1.12))
sc.camera = co
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("rendered", OUT)
