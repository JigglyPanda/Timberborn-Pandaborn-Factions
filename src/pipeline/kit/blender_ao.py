"""Blender side of the vertex ambient-occlusion bake (run by ao.py; Blender 4.5, headless, --factory-startup).

blender -b --factory-startup --python blender_ao.py -- in.npz out.npz [samples] [distance]

in.npz: P (N,3) Blender-space positions, T (M,3) triangles (Blender winding). A large ground plane is added at z=0 so
the bottoms of walls and posts get contact shadow. Cycles bakes AO into a per-vertex colour attribute; out.npz holds
ao (N,) in 0..1.
"""
import sys

import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
src, dst = args[0], args[1]
samples = int(args[2]) if len(args) > 2 else 64
distance = float(args[3]) if len(args) > 3 else 0.5

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "OPTIX"
    sc.cycles.device = "GPU"
except Exception as ex:  # noqa: BLE001
    print("GPU setup failed", ex)
sc.cycles.samples = samples

z = np.load(src)
P, T = z["P"], z["T"]
me = bpy.data.meshes.new("m")
me.vertices.add(len(P))
me.vertices.foreach_set("co", P.ravel())
me.loops.add(len(T) * 3)
me.loops.foreach_set("vertex_index", T.ravel())
me.polygons.add(len(T))
me.polygons.foreach_set("loop_start", np.arange(0, len(T) * 3, 3))
me.update()
col = me.color_attributes.new("AO", "FLOAT_COLOR", "POINT")
me.color_attributes.active_color = col
ob = bpy.data.objects.new("m", me)
sc.collection.objects.link(ob)
mat = bpy.data.materials.new("m")
mat.use_nodes = True
me.materials.append(mat)
# ground: occludes, is not baked
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, -0.005))
for o in bpy.context.selected_objects:
    o.select_set(False)
ob.select_set(True)
bpy.context.view_layer.objects.active = ob
sc.world = bpy.data.worlds.new("w")
sc.render.bake.target = "VERTEX_COLORS"
sc.render.bake.margin = 0
bpy.context.scene.cycles.bake_type = "AO"
sc.world.light_settings.distance = distance
bpy.ops.object.bake(type="AO", target="VERTEX_COLORS")
c = np.zeros(len(P) * 4, np.float32)
me.color_attributes["AO"].data.foreach_get("color", c)
np.savez(dst, ao=c.reshape(-1, 4)[:, 0])
print("AO DONE", len(P))
