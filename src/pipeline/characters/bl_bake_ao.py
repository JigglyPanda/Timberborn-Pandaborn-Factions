"""Bake ambient occlusion of a rest mesh (from a .paint.npz) into its uv0 layout with Cycles.

usage: blender -b --factory-startup --python bl_bake_ao.py -- MODEL.paint.npz OUT.npy [size]
Adapted from the Pandaborn Reskin's bake_ao.py (same owner); self-contained (Blender's numpy only).
"""
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
d = np.load(argv[0])
out = argv[1]
S = int(argv[2]) if len(argv) > 2 else 1024
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    for dv in prefs.devices:
        dv.use = dv.type != 'CPU'
    sc.cycles.device = 'GPU'
except Exception:
    pass
w = bpy.data.worlds.new('W'); sc.world = w
mat = bpy.data.materials.new('bk'); mat.use_nodes = True
img = bpy.data.images.new('ao', S, S, float_buffer=True)
tn = mat.node_tree.nodes.new('ShaderNodeTexImage'); tn.image = img; mat.node_tree.nodes.active = tn
tri = d['tri']
keep = ~(d['teeth'][tri] > 0.5).any(1)
P = d['P']
Pb = np.stack([-P[:, 0], -P[:, 2], P[:, 1]], 1)
me = bpy.data.meshes.new('m')
me.from_pydata(Pb.tolist(), [], tri[keep][:, [0, 2, 1]].tolist())
uvl = me.uv_layers.new(name='uv0')
lv = np.array([l.vertex_index for l in me.loops])
uvl.data.foreach_set('uv', d['uv0'][lv].astype(np.float32).ravel())
me.update()
for p in me.polygons:
    p.use_smooth = True
o = bpy.data.objects.new('m', me); sc.collection.objects.link(o)
me.materials.append(mat)
bpy.context.view_layer.objects.active = o; o.select_set(True)
sc.cycles.samples = 128
sc.world.light_settings.distance = float(argv[3]) if len(argv) > 3 else 0.12
sc.render.bake.margin = 16
bpy.ops.object.bake(type='AO')
a = np.array(img.pixels[:]).reshape(S, S, 4)[::-1, :, 0]
np.save(out, a)
print('ao', float(a.min()), float(a.mean()))
