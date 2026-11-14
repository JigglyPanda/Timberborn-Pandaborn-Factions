import bpy, sys
print("=== BLEND", bpy.data.filepath, "version", bpy.data.version)
sc=bpy.context.scene
print("scene", sc.name, "unit", sc.unit_settings.system, sc.unit_settings.scale_length, "frames", sc.frame_start, sc.frame_end, "fps", sc.render.fps, "engine", sc.render.engine)
print("scenes", [s.name for s in bpy.data.scenes])
def tree(coll, ind=0):
    print("  "*ind+f"[C] {coll.name!r} objs={len(coll.objects)} hide_viewport={coll.hide_viewport} hide_render={coll.hide_render}")
    for o in coll.objects:
        extra=""
        if o.type=='MESH':
            d=o.data
            extra=f" verts={len(d.vertices)} polys={len(d.polygons)} uv={[u.name for u in d.uv_layers]} col={[c.name for c in d.color_attributes]} mats={[s.material.name if s.material else None for s in o.material_slots]} mods={[m.type for m in o.modifiers]}"
        print("  "*(ind+1)+f"- {o.name!r} {o.type} parent={o.parent.name if o.parent else None} loc={tuple(round(v,3) for v in o.location)} rot={tuple(round(v,3) for v in o.rotation_euler)} scale={tuple(round(v,3) for v in o.scale)} dim={tuple(round(v,3) for v in o.dimensions)}{extra}")
    for c in coll.children: tree(c, ind+1)
for s in bpy.data.scenes: tree(s.collection)
print("orphan objects not in scene:", [o.name for o in bpy.data.objects if not o.users_scene])
print("collections:", [c.name for c in bpy.data.collections])
print("MATERIALS", len(bpy.data.materials))
for m in bpy.data.materials:
    info=""
    if m.use_nodes:
        info=" nodes="+",".join(sorted({n.type+(":"+n.image.name if n.type=='TEX_IMAGE' and n.image else "") for n in m.node_tree.nodes}))
    print(f"  {m.name!r} users={m.users} diffuse={tuple(round(v,2) for v in m.diffuse_color)}{info}")
print("IMAGES", [(i.name,i.size[:],i.filepath) for i in bpy.data.images])
print("TEXTS", [(t.name, t.as_string()[:800]) for t in bpy.data.texts])
print("ACTIONS", [a.name for a in bpy.data.actions][:20])
print("ARMATURES", [a.name for a in bpy.data.armatures])
print("custom props on scene:", {k:str(v) for k,v in sc.items() if not k.startswith('_')})
for c in bpy.data.collections:
    if len(c.keys()): print("coll props", c.name, dict(c.items()))
for o in bpy.data.objects:
    ks=[k for k in o.keys() if not k.startswith('_')]
    if ks: print("obj props", o.name, {k:str(o[k]) for k in ks})
print("addons enabled:", list(bpy.context.preferences.addons.keys()))
