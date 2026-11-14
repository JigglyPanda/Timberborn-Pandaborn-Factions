"""Thin headless-Blender renderer for character previews (only numpy needed inside Blender).

usage: blender -b --factory-startup --python bl_render.py -- scene.npz [out_override.png]
The .npz comes from pose_export.py. Game space (x right, y up, z forward) -> Blender (bx=-x, by=-z, bz=y).
Each camera writes one PNG: {"out": "...png", "target": [x,y,z] (game), "az": deg, "el": deg, "dist": m, "lens": mm,
"ortho": scale (optional)}. az=0 looks at the characters' faces (they face +z in game space).
"""
import json
import math
import sys

import bpy
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
D = np.load(argv[0])
meta = json.loads(str(D['meta']))


def g2b(p):
    p = np.asarray(p, dtype=np.float64).reshape(-1, 3)
    return np.stack([-p[:, 0], -p[:, 2], p[:, 1]], 1)


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for dt in ('OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = dt
            prefs.get_devices()
            for d in prefs.devices:
                d.use = d.type != 'CPU'
            sc.cycles.device = 'GPU'
            break
        except Exception:
            continue
except Exception:
    pass
sc.cycles.samples = int(meta.get('samples', 32))
sc.cycles.use_denoising = True
sc.view_settings.view_transform = 'Standard'
sc.render.film_transparent = False
w = bpy.data.worlds.new('W')
sc.world = w
w.use_nodes = True
bg = w.node_tree.nodes['Background']
night = meta.get('night', False)
bgc = meta.get('background') or ((0.05, 0.07, 0.14) if night else (0.66, 0.74, 0.82))
bg.inputs[0].default_value = (*bgc, 1)
bg.inputs[1].default_value = 0.25 if night else 0.65


def look(o, d):
    o.rotation_euler = Vector(tuple(d)).to_track_quat('-Z', 'Y').to_euler()


for name, loc, en, size, col in ([('Key', (2.2, -2.6, 3.4), 520, 2.5, (1.0, 0.95, 0.88)),
                                  ('Rim', (-2.0, 2.4, 2.2), 260, 2.0, (0.85, 0.9, 1.0)),
                                  ('Fill', (-2.8, -1.6, 1.0), 120, 3.0, (0.9, 0.95, 1.0))] if not night else
                                 [('Moon', (-2.0, 2.0, 3.5), 120, 3.0, (0.55, 0.65, 1.0)),
                                  ('Lantern', (1.0, -1.2, 0.8), 40, 0.3, (1.0, 0.65, 0.3))]):
    L = bpy.data.lights.new(name, 'AREA')
    L.energy = en
    L.size = size
    L.color = col
    o = bpy.data.objects.new(name, L)
    o.location = loc
    look(o, -np.array(loc))
    sc.collection.objects.link(o)

if meta.get('ground', True):
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
    g = bpy.context.active_object
    gm = bpy.data.materials.new('Ground')
    gm.use_nodes = True
    gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.36, 0.42, 0.25, 1)
    gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.95
    g.data.materials.append(gm)

images = {}


def image(path, linear=False):
    if path not in images:
        im = bpy.data.images.load(path, check_existing=True)
        if linear:
            im.colorspace_settings.name = 'Non-Color'
        images[path] = im
    return images[path]


def material(tex, decal):
    m = bpy.data.materials.new('m')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.9
    try:
        b.inputs['Specular IOR Level'].default_value = 0.2
    except Exception:
        pass
    if not tex:
        b.inputs['Base Color'].default_value = (0.7, 0.7, 0.7, 1)
        return m
    uv = nt.nodes.new('ShaderNodeUVMap')
    uv.uv_map = 'uv0'
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = image(tex)
    nt.links.new(uv.outputs['UV'], t.inputs['Vector'])
    col = t.outputs['Color']
    if decal:
        uv1 = nt.nodes.new('ShaderNodeUVMap')
        uv1.uv_map = 'uv1'
        d = nt.nodes.new('ShaderNodeTexImage')
        d.image = image(decal)
        d.extension = 'CLIP'
        nt.links.new(uv1.outputs['UV'], d.inputs['Vector'])
        mix = nt.nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        nt.links.new(d.outputs['Alpha'], mix.inputs['Factor'])
        nt.links.new(col, mix.inputs[6])
        nt.links.new(d.outputs['Color'], mix.inputs[7])
        col = mix.outputs[2]
    nt.links.new(col, b.inputs['Base Color'])
    return m


for k, it in enumerate(meta['items']):
    P = g2b(D[f'P{k}'])
    T = D[f'T{k}'][:, [0, 2, 1]]
    me = bpy.data.meshes.new(f'c{k}')
    me.from_pydata(P.tolist(), [], T.tolist())
    for nm, key in (('uv0', f'UV{k}'), ('uv1', f'UVB{k}')):
        uvl = me.uv_layers.new(name=nm)
        lv = np.array([l.vertex_index for l in me.loops])
        uvl.data.foreach_set('uv', D[key][lv].astype(np.float32).ravel())
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(f'c{k}', me)
    sc.collection.objects.link(o)
    me.materials.append(material(it.get('texture'), it.get('decal')))
    if it.get('markers'):
        mk = bpy.data.materials.new('mk')
        mk.use_nodes = True
        mk.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (1, 0.1, 0.8, 1)
        for q in g2b(D[f'N{k}']):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012, location=tuple(q))
            bpy.context.active_object.data.materials.append(mk)

sizes = meta.get('size', [900, 700])
for cam in meta['cameras']:
    c = bpy.data.cameras.new('C')
    c.lens = cam.get('lens', 50)
    if cam.get('ortho'):
        c.type = 'ORTHO'
        c.ortho_scale = cam['ortho']
    o = bpy.data.objects.new('C', c)
    sc.collection.objects.link(o)
    tgt = g2b(cam.get('target', [0, 0.25, 0]))[0]
    a, e = math.radians(cam.get('az', 0)), math.radians(cam.get('el', 10))
    # az=0: camera in front of the characters (game +z -> blender -y)
    loc = tgt + cam.get('dist', 2.0) * np.array([-math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)])
    o.location = loc
    look(o, tgt - loc)
    sc.camera = o
    sz = cam.get('size', sizes)
    sc.render.resolution_x, sc.render.resolution_y = sz
    sc.render.filepath = cam['out']
    bpy.ops.render.render(write_still=True)
    print('rendered', cam['out'])
