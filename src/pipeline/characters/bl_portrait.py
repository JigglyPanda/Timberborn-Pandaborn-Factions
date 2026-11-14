"""Blender side of make_portraits.py: posed Ringtail mesh, subdivision, real hair coloured from the coat, studio
lights, transparent render. Adapted from the Pandaborn Reskin's portrait2.py (same owner). Needs only numpy.

usage: blender -b --factory-startup --python bl_portrait.py -- PORTRAIT.npz
"""
import json
import math
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

D = np.load(sys.argv[sys.argv.index('--') + 1])
S = json.loads(str(D['meta']))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type != 'CPU'
    sc.cycles.device = 'GPU'
except Exception:
    pass
sc.cycles.samples = int(S['samples'])
sc.cycles.use_denoising = True
sc.render.film_transparent = True
sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.20, 0.30, 0.32, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = 0.35

img = bpy.data.images.load(S['tex'])
m = bpy.data.materials.new('fur'); m.use_nodes = True
nt = m.node_tree; bsdf = nt.nodes['Principled BSDF']
bsdf.inputs['Roughness'].default_value = 0.85
for k, v in (('Specular IOR Level', 0.12), ('Sheen Weight', 0.25), ('Sheen Roughness', 0.5)):
    try:
        bsdf.inputs[k].default_value = v
    except Exception:
        pass
uvn = nt.nodes.new('ShaderNodeUVMap'); uvn.uv_map = 'uv0'
t = nt.nodes.new('ShaderNodeTexImage'); t.image = img
nt.links.new(uvn.outputs['UV'], t.inputs['Vector']); nt.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.25; bump.inputs['Distance'].default_value = 0.002
nt.links.new(t.outputs['Color'], bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

P = D['P'].astype(np.float64)
Pb = np.stack([-P[:, 0], -P[:, 2], P[:, 1]], 1)
me = bpy.data.meshes.new('rt')
me.from_pydata(Pb.tolist(), [], D['T'][:, [0, 2, 1]].tolist())
uvl = me.uv_layers.new(name='uv0')
lv = np.array([l.vertex_index for l in me.loops])
uvl.data.foreach_set('uv', D['UV'][lv].astype(np.float32).ravel())
me.update()
ob = bpy.data.objects.new('rt', me); sc.collection.objects.link(ob)
me.materials.append(m)
vg = ob.vertex_groups.new(name='fur')
W = D['W']
for i, wv in enumerate(W):
    vg.add([i], float(wv), 'REPLACE')
# weld UV-seam duplicates (vertex groups follow the merged vertex), then subdivide: a soft, round animal
bm = bmesh.new(); bm.from_mesh(ob.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.to_mesh(ob.data); bm.free()
for poly in ob.data.polygons:
    poly.use_smooth = True
sub = ob.modifiers.new('sub', 'SUBSURF'); sub.levels = 2; sub.render_levels = 2
ps = ob.modifiers.new('hair', 'PARTICLE_SYSTEM').particle_system
st = ps.settings
st.type = 'HAIR'; st.count = 60000; st.hair_length = S['hair_len']
st.child_type = 'INTERPOLATED'; st.rendered_child_count = 6; st.child_percent = 6
st.clump_factor = 0.15; st.roughness_2 = 0.002; st.roughness_endpoint = 0.004
st.use_advanced_hair = False
st.root_radius = S['root_radius']; st.tip_radius = 0.0; st.radius_scale = 1.0
try:
    st.display_step = 3; st.render_step = 4
except Exception:
    pass
ps.vertex_group_density = 'fur'; ps.vertex_group_length = 'fur'
hm = bpy.data.materials.new('hair'); hm.use_nodes = True
hn = hm.node_tree; hb = hn.nodes['Principled BSDF']
hb.inputs['Roughness'].default_value = 0.7
try:
    hb.inputs['Specular IOR Level'].default_value = 0.15
except Exception:
    pass
huv = hn.nodes.new('ShaderNodeUVMap'); huv.uv_map = 'uv0'
ht = hn.nodes.new('ShaderNodeTexImage'); ht.image = img
hn.links.new(huv.outputs['UV'], ht.inputs['Vector'])
hi = hn.nodes.new('ShaderNodeHairInfo'); mix = hn.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
ramp = hn.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = (0.72, 0.72, 0.72, 1); ramp.color_ramp.elements[1].color = (1.05, 1.05, 1.05, 1)
hn.links.new(hi.outputs['Intercept'], ramp.inputs['Fac'])
hn.links.new(ht.outputs['Color'], mix.inputs[6]); hn.links.new(ramp.outputs['Color'], mix.inputs[7]); mix.inputs['Factor'].default_value = 1.0
hn.links.new(mix.outputs[2], hb.inputs['Base Color'])
ob.data.materials.append(hm); st.material = 2

tz = S['tz']


def look(o, d):
    o.rotation_euler = Vector(tuple(d)).to_track_quat('-Z', 'Y').to_euler()


def light(name, loc, energy, size, color):
    L = bpy.data.lights.new(name, 'AREA'); L.energy = energy; L.size = size; L.color = color
    o = bpy.data.objects.new(name, L); o.location = loc
    look(o, -np.array(loc) + np.array([0, 0, tz]))
    sc.collection.objects.link(o)


light('Key', (-1.4, -2.0, tz + 1.6), 300, 1.8, (1.0, 0.90, 0.76))
light('Rim', (1.6, 1.8, tz + 1.0), 420, 1.2, (0.62, 0.80, 1.0))
light('Fill', (1.8, -1.6, tz + 0.2), 70, 2.5, (0.85, 0.92, 1.0))
cam = bpy.data.cameras.new('Cam'); cam.lens = S['lens']
co = bpy.data.objects.new('Cam', cam); sc.collection.objects.link(co)
a, e = math.radians(S['az']), math.radians(S['el'])
target = np.array([0, 0, tz])
loc = target + S['dist'] * np.array([math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)])
co.location = loc
look(co, target - loc)
sc.camera = co
sc.render.resolution_x = S['width']; sc.render.resolution_y = S['height']
sc.render.filepath = S['out']
bpy.ops.render.render(write_still=True)
print('rendered', S['out'])
