"""Headless driver for Mechanistry's timbermesh exporter.
blender -b --factory-startup FILE.blend --python tm_export_headless.py -- PLUGIN_DIR OUT_DIR [collection names...]
PLUGIN_DIR = .../src/timbermesh_blender_plugin   (added to sys.path; we import timbermesh_exporter directly,
so the add-on's register()/UI code is never used)."""
import bpy, sys, os
a = sys.argv[sys.argv.index('--')+1:]
plugin, out, names = a[0], a[1], a[2:]
sys.path.insert(0, plugin)
import timbermesh_exporter as tx
os.makedirs(out, exist_ok=True)
ctx = bpy.context
def _unexclude(lc):
    lc.exclude = False
    for ch in lc.children: _unexclude(ch)
# Collections excluded from the view layer are not evaluated (matrix_world stays identity, modifiers not applied).
for _lc in ctx.view_layer.layer_collection.children: _unexclude(_lc)
ctx.view_layer.update()
settings = tx.ExportSettings(ctx, merge_meshes=True, single_animation=True, use_vertex_animations=False)
cols = [c for c in bpy.data.collections if (not names or c.name in names)]
for c in cols:
    p = os.path.join(out, c.name.strip() + ".timbermesh")
    tx.Exporter.export_collection(c, p, settings)
    print("EXPORTED", repr(c.name), "->", p, os.path.getsize(p))
