"""Bake Inkpaws trim sheets from modelled surfaces (Blender, headless, Cycles).

Each sheet is a small diorama of real geometry laid into the fixed regions of the vanilla sheet it replaces
(src/pipeline/sheet_regions.json): bamboo culms with nodes, sawn boards with bevelled edges, log ends, woven bamboo
panels with over-under strands, edge battens and repairs, clay pan-and-cover roof tiles in overlapping courses. An
orthographic camera looks straight down on the 1 x 1 unit sheet (1 unit = 1024 px; +X = u, +Y = v) and Cycles
renders the data passes. Geometry is extended past the sheet's edges and coloured by (index mod period) so every
sheet tiles seamlessly, AO included.

Writes, per set, into <out>/<Set>/: diffcol.npy (linear albedo), normal.npy (world = tangent space here), ao.npy,
each float32 HxWx3 with row 0 at the TOP of the image. look_textures.py turns them into the game's maps.

Run (bash; see CLAUDE.md for the env vars that keep Blender off C:):
  $BL -b --factory-startup --python src/pipeline/bake_sheets.py -- src/pipeline/sheet_regions.json E:/PandabornDev/build/look/bake [Set,Set]
Sets: Timber Bamboo Weave WeaveCoarse RoofTiles FlatTiles (modelled), and the heightfield sets Windows LatticePaper
Details Iron Banded PlasterLath (relief from look_textures.py --export-hf, baked only when that export exists)
"""
import json
import math
import os
import random
import sys

import bpy
import numpy as np

S = 1024
SAMPLES = 96


# ------------------------------------------------------------------------------------------------ scene
def reset():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.cameras):
        for x in list(coll):
            coll.remove(x)


def setup_render(res):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
            if any(d.type == kind for d in prefs.devices):
                for d in prefs.devices:
                    d.use = d.type == kind
                sc.cycles.device = "GPU"
                break
        except TypeError:
            continue
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = False
    sc.cycles.max_bounces = 1
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "Standard"
    if sc.world is None:
        sc.world = bpy.data.worlds.new("World")
    sc.world.color = (0, 0, 0)
    sc.world.light_settings.distance = 0.035
    vl = sc.view_layers[0]
    vl.use_pass_normal = True
    vl.use_pass_ambient_occlusion = True
    vl.use_pass_diffuse_color = True
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 1.0
    cam_data.clip_start, cam_data.clip_end = 0.01, 20
    cam = bpy.data.objects.new("cam", cam_data)
    cam.location = (0.5, 0.5, 5.0)
    bpy.context.collection.objects.link(cam)
    sc.camera = cam


def render_passes(outdir):
    sc = bpy.context.scene
    sc.use_nodes = True
    tree = sc.node_tree
    tree.nodes.clear()
    rl = tree.nodes.new("CompositorNodeRLayers")
    fo = tree.nodes.new("CompositorNodeOutputFile")
    fo.base_path = outdir
    fo.format.file_format = "OPEN_EXR"
    fo.format.color_depth = "32"
    fo.file_slots.clear()
    for name, socket in (("diffcol", "DiffCol"), ("normal", "Normal"), ("ao", "AO")):
        fo.file_slots.new(name)
        tree.links.new(rl.outputs[socket], fo.inputs[name])
    comp = tree.nodes.new("CompositorNodeComposite")
    tree.links.new(rl.outputs["Image"], comp.inputs["Image"])
    sc.frame_set(1)
    bpy.ops.render.render(write_still=False)
    for name in ("diffcol", "normal", "ao"):
        path = os.path.join(outdir, name + "0001.exr")
        img = bpy.data.images.load(path)
        w, h = img.size
        px = np.empty(w * h * 4, np.float32)
        img.pixels.foreach_get(px)
        arr = px.reshape(h, w, 4)[::-1, :, :3].copy()      # row 0 = top
        np.save(os.path.join(outdir, name + ".npy"), arr)
        bpy.data.images.remove(img)
        os.remove(path)


# ------------------------------------------------------------------------------------------------ geometry
def X(px):
    return px / S


def Y(py):
    return 1.0 - py / S


def add_mesh(name, verts, faces, colors, mat, smooth=True, origin=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    v = np.asarray(verts, np.float32).reshape(-1, 3)          # local to origin
    me.from_pydata(v.tolist(), [], np.asarray(faces).tolist())
    attr = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    c = np.ones((len(v), 4), np.float32)
    c[:, :3] = np.asarray(colors, np.float32).reshape(-1, 3)
    attr.data.foreach_set("color", c.ravel())
    me.polygons.foreach_set("use_smooth", [smooth] * len(me.polygons))
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    ob.location = origin
    bpy.context.collection.objects.link(ob)
    return ob


def grid_faces(nu, nv):
    f = []
    for i in range(nu - 1):
        for j in range(nv - 1):
            a = i * nv + j
            f.append((a, a + nv, a + nv + 1, a + 1))
    return f


def surface(name, nu, nv, fn, mat, origin=(0, 0, 0)):
    """fn(u, v) on [0,1]^2 grids -> (x, y, z, r, g, b) arrays (world units)."""
    u, v = np.meshgrid(np.linspace(0, 1, nu), np.linspace(0, 1, nv), indexing="ij")
    x, y, z, r, g, b = fn(u, v)
    verts = np.stack([x, y, z], -1).reshape(-1, 3)
    cols = np.stack([np.broadcast_to(r, u.shape), np.broadcast_to(g, u.shape), np.broadcast_to(b, u.shape)], -1)
    return add_mesh(name, verts, grid_faces(nu, nv), cols.reshape(-1, 3), mat, origin=origin)


def plane(name, x0, y0, x1, y1, z, col, mat):
    return surface(name, 2, 2, lambda u, v: (X(x0 + (x1 - x0) * u), Y(y0 + (y1 - y0) * v), z + 0 * u,
                                             col[0], col[1], col[2]), mat)


def srgb(c):
    """palette in sRGB 0-255 -> linear 0-1 (Cycles works in linear)"""
    c = np.asarray(c, np.float64) / 255.0
    return tuple(np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4))


def jitter(col, rnd, amount=0.08):
    k = 1 + rnd.uniform(-amount, amount)
    h = [rnd.uniform(-amount, amount) * 0.4 for _ in range(3)]
    return tuple(max(0.0, c * k * (1 + hh)) for c, hh in zip(col, h))


WEATHERED_BAMBOO = [((168, 146, 100), 4), ((148, 138, 98), 3), ((128, 132, 110), 2), ((184, 162, 112), 1)]


def bamboo_col(rnd):
    """Weathered culm colours: mostly honey- and olive-tan, some grey-green aged culms, the odd warmer straw one."""
    total = sum(w for _, w in WEATHERED_BAMBOO)
    pick = rnd.uniform(0, total)
    for c, w in WEATHERED_BAMBOO:
        pick -= w
        if pick <= 0:
            return jitter(srgb(c), rnd, 0.06)
    return jitter(srgb(WEATHERED_BAMBOO[0][0]), rnd, 0.06)


# ------------------------------------------------------------------------------------------------ materials
def material(name, fine="streak", scale=(1, 1, 1), bump=0.3, rough=0.6, grain=None):
    """Colour = vertex colour x fine detail; bump from the same detail. fine: streak (fibres along local Y),
    grain (wood, bands along local Y), mottle (isotropic), none."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Roughness"].default_value = rough
    nt.links.new(bs.outputs[0], out.inputs[0])
    vc = nt.nodes.new("ShaderNodeVertexColor")
    vc.layer_name = "Col"
    if fine == "none":
        nt.links.new(vc.outputs["Color"], bs.inputs["Base Color"])
        return m
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = scale
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    if fine == "grain":
        tex = nt.nodes.new("ShaderNodeTexWave")
        tex.wave_type = "BANDS"
        tex.bands_direction = "X"
        tex.inputs["Scale"].default_value = grain or 6.0
        tex.inputs["Distortion"].default_value = 12.0
        tex.inputs["Detail"].default_value = 1.5
        fac = tex.outputs["Fac"]
    else:
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = 1.0
        tex.inputs["Detail"].default_value = 6.0
        tex.inputs["Roughness"].default_value = 0.6
        fac = tex.outputs["Fac"]
    nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeMapRange")
    ramp.inputs["From Min"].default_value = 0.35 if fine == "grain" else 0.25
    ramp.inputs["From Max"].default_value = 0.70 if fine == "grain" else 0.75
    ramp.inputs["To Min"].default_value = 0.42 if fine == "grain" else 0.80
    ramp.inputs["To Max"].default_value = 1.12
    nt.links.new(fac, ramp.inputs["Value"])
    mul = nt.nodes.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 1.0
    nt.links.new(vc.outputs["Color"], mul.inputs[6])
    nt.links.new(ramp.outputs["Result"], mul.inputs[7])
    nt.links.new(mul.outputs[2], bs.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = bump
    bp.inputs["Distance"].default_value = 0.002
    nt.links.new(fac, bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], bs.inputs["Normal"])
    return m


# ------------------------------------------------------------------------------------------------ parts
def culm(name, x0, y0, x1, y1, col, mat, rnd, horizontal=False, node_gap=(110, 190), split=False, nseg=12, z0=0.0):
    """A bamboo culm (or split half culm) lying in the rect, axis along its long side. Nodes bulge and darken."""
    if horizontal:
        length, width = x1 - x0, y1 - y0
    else:
        length, width = y1 - y0, x1 - x0
    r = width / 2.0
    nodes = []
    p = rnd.uniform(10, node_gap[0])
    while p < length - 4:
        nodes.append(p)
        p += rnd.uniform(*node_gap)
    nodes = np.array(nodes) if nodes else np.array([-1e3])
    nu = max(int(length / 1.5), 4)
    rnd_k = (rnd.uniform(0.6, 2.2), rnd.uniform(0, 6.28), rnd.uniform(0, 6.28))

    def fn(u, v):
        s = u * length                                          # along axis, px
        d = s[..., None] - nodes[None, None, :]
        ridge = np.exp(-(d ** 2) / (2 * 1.6 ** 2)).sum(-1)
        groove = np.exp(-((d - 3.5) ** 2) / (2 * 1.2 ** 2)).sum(-1)
        band = np.exp(-(d ** 2) / (2 * 10.0 ** 2)).sum(-1)
        rr = r * (1 + 0.06 * ridge - 0.03 * groove)
        th = math.pi * v                                         # upper half only: the camera looks down
        across = rr * np.cos(th)
        zz = rr * np.sin(th) * (0.35 if split else 1.0)
        # value varies along the culm (weathering blotches) and nodes are clearly darker
        blot = 0.88 + 0.12 * np.sin(s / length * 2 * math.pi * rnd_k[0] + rnd_k[1])             + 0.06 * np.sin(s / 37.0 + rnd_k[2])
        shade = (1 - 0.30 * np.clip(band, 0, 1) - 0.40 * np.clip(groove, 0, 1)) * blot
        if horizontal:
            x, y = X(x0 + s), Y((y0 + y1) / 2 + across)
        else:
            x, y = X((x0 + x1) / 2 + across), Y(y0 + s)
        return x, y, (zz + z0) / S, col[0] * shade, col[1] * shade, col[2] * shade

    return surface(name, nu, nseg, fn, mat)


def tube_end(name, cx, cy, rad, col, mat, rnd, broken=False):
    """Cut bamboo seen end-on: a ring of wall around a dark hollow."""
    nr, nt = 10, 64
    jag = rnd.uniform(0, 6)

    def fn(u, v):
        th = 2 * math.pi * v
        ro = rad * (1 + (0.10 * np.sin(7 * th + jag) * (u > 0.5) if broken else 0))
        rin = rad * 0.6
        rr = rin + (ro - rin) * u
        x, y = X(cx + rr * np.cos(th)), Y(cy + rr * np.sin(th))
        z = (0.012 * S - 2.0 * (u - 0.5) ** 2 * rad * 0.1) / S + 0 * u
        shade = 0.95 - 0.18 * u
        return x, y, z, col[0] * shade, col[1] * shade, col[2] * shade

    surface(name, nr, nt, fn, mat)
    dark = srgb((40, 34, 28))
    surface(name + "_hole", 6, nt, lambda u, v: (X(cx + rad * 0.6 * u * np.cos(2 * math.pi * v)),
                                                 Y(cy + rad * 0.6 * u * np.sin(2 * math.pi * v)),
                                                 (0.002 + 0 * u) / 1.0, dark[0], dark[1], dark[2]), mat)


def board(name, x0, y0, x1, y1, col, mat, rnd, horizontal=False):
    """A sawn board: flat top, rounded bevelled edges, slight cup, its own object so the grain is local."""
    w, h = (x1 - x0), (y1 - y0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    height = rnd.uniform(5, 8)
    cup = rnd.uniform(-1.0, 1.0)

    def fn(u, v):
        if horizontal:
            across, along = v, u
        else:
            across, along = u, v
        e = np.minimum(across, 1 - across) * (h if horizontal else w)
        e2 = np.minimum(along, 1 - along) * (w if horizontal else h)
        bev = np.clip(np.minimum(e, e2 * 0.6) / 4.0, 0, 1)
        z = height * np.sqrt(bev) + cup * (across - 0.5) ** 2 * 4
        x, y = X(x0 + w * u) - X(cx), Y(y0 + h * v) - Y(cy)
        shade = 0.8 + 0.2 * bev
        return x, y, z / S, col[0] * shade, col[1] * shade, col[2] * shade

    nu = max(int(w / 2), 4)
    nv = max(int(h / 2), 4)
    ob = surface(name, nu, nv, fn, mat, origin=(X(cx), Y(cy), 0))
    if horizontal:
        ob.rotation_euler[2] = 0.0   # grain runs along local Y; horizontal boards use a rotated material below
    return ob


def log_end(name, cx, cy, rad, col, mat):
    ob = surface(name, 12, 64, lambda u, v: (rad * u * np.cos(2 * math.pi * v) / S, -rad * u * np.sin(2 * math.pi * v) / S,
                                             (8 - 3 * u ** 4) / S + 0 * u, col[0] * (1 - 0.3 * u ** 6),
                                             col[1] * (1 - 0.3 * u ** 6), col[2] * (1 - 0.3 * u ** 6)), mat,
                 origin=(X(cx), Y(cy), 0))
    return ob


# ------------------------------------------------------------------------------------------------ sets
def regions(sheet):
    return [r for r in REG["sheets"][sheet]["regions"] if not r.get("background")]


def set_wood(name, kind):
    rnd = random.Random(7 if kind == "timber" else 11)
    if kind == "timber":
        base, gap = srgb((96, 70, 50)), srgb((36, 28, 22))
        wood = material("wood", "grain", scale=(30, 2, 30), bump=0.45, grain=2.0)
        wood_h = material("wood_h", "grain", scale=(2, 30, 30), bump=0.45, grain=2.0)
        endm = material("end", "grain", scale=(1, 1, 1), bump=0.2, grain=1.0)
        # end grain rings: replace the band wave with rings
        endm.node_tree.nodes["Wave Texture"].wave_type = "RINGS"
        endm.node_tree.nodes["Wave Texture"].inputs["Scale"].default_value = 260.0
    else:
        base, gap = srgb((168, 146, 100)), srgb((200, 194, 180))
        wood = material("bamboo", "streak", scale=(900, 6, 900), bump=0.15)
        wood_h = material("bamboo_h", "streak", scale=(6, 900, 900), bump=0.15)
    plane("bg", -20, -20, S + 20, S + 20, 0.0, gap, material("bg", "mottle", scale=(40, 40, 40), bump=0.05))
    for i, r in enumerate(regions("BaseWood")):
        x0, y0, x1, y1 = r["rect"]
        k = r["kind"]
        col = jitter(base, rnd, 0.18) if kind == "timber" else bamboo_col(rnd)
        if k.startswith("long-grain"):
            x = x0
            j = 0
            while x < x1 - 4:
                bw = rnd.randint(52, 86) if kind == "timber" else rnd.randint(24, 40)
                xe = min(x + bw, x1)
                c = jitter(base, rnd, 0.18) if kind == "timber" else bamboo_col(rnd)
                if kind == "timber":
                    board("blk%d" % j, x + 1, y0 + 2, xe - 1, y1 - 2, c, wood, rnd)
                else:
                    culm("blk%d" % j, x, y0, xe, y1, c, wood, rnd, node_gap=(70, 150))
                x = xe
                j += 1
        elif k.startswith("plank strip"):
            if kind == "timber":
                board("s%d" % i, x0, y0, x1, y1, col, wood_h if "horizontal" in k else wood, rnd, horizontal="horizontal" in k)
            else:
                culm("s%d" % i, x0, y0, x1, y1, col, wood, rnd, split=True)
        elif k.startswith("end-grain"):
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            rad = min(x1 - x0, y1 - y0) / 2 - 6
            if kind == "timber":
                log_end("e%d" % i, cx, cy, rad, srgb((150, 112, 78)), endm)
            else:
                tube_end("e%d" % i, cx, cy, rad, col, wood, rnd, broken="broken" in k)
        elif k.startswith("plain"):
            plane("plain", x0, y0, x1, y1, 0.001, jitter(gap if kind != "timber" else srgb((70, 54, 40)), rnd, 0.02),
                  material("plainm", "mottle", scale=(25, 25, 25), bump=0.1))


def set_weave(name, strand=16, tones=None, moss=0.0, seed=3, patches=2):
    """Plain-weave bamboo panels, one per vanilla plank column, with bamboo battens on the seams, a binding batten
    across the middle, a few repaired patches in fresher strands."""
    rnd = random.Random(seed)
    # muted tan / grey-brown / grey-olive panels; straw (fresh) only for a minority
    tones = tones or [srgb(c) for c in ((150, 132, 100), (126, 118, 98), (142, 128, 100), (118, 116, 98),
                                        (176, 156, 108), (126, 118, 98), (146, 130, 100), (120, 118, 100))]
    warp_m = material("warp", "streak", scale=(900, 8, 900), bump=0.12)
    weft_m = material("weft", "streak", scale=(8, 900, 900), bump=0.12)
    batten_m = material("batten", "streak", scale=(900, 6, 900), bump=0.15)
    plane("bg", -40, -40, S + 40, S + 40, -0.004, srgb((60, 52, 40)), material("bgw", "none"))
    cols = [r["rect"] for r in regions("IrregularPlanks")]
    amp = strand * 0.18
    for pi_, (x0, _, x1, _) in enumerate(cols):
        tone = tones[pi_ % len(tones)]
        patch = []
        if rnd.random() < patches / len(cols) * 2:
            py0 = rnd.randint(80, 760)
            patch = [(py0, py0 + rnd.randint(120, 220))]
        nwarp = max(int((x1 - x0 - 8) // strand), 1)
        xs = x0 + 4 + (x1 - x0 - 8 - nwarp * strand) / 2
        # warp: vertical strands
        for i in range(nwarp):
            c = jitter(tone, rnd, 0.06)
            ax = xs + (i + 0.5) * strand

            def fw(u, v, ax=ax, i=i, c=c):
                yy = -strand + (S + 2 * strand) * u
                across = (v - 0.5) * strand * 0.92
                ph = math.pi * (yy / strand) + math.pi * i
                z = amp * np.sin(ph) + 1.2 * np.sin(math.pi * v)
                k = 0.66 + 0.34 * (0.5 + 0.5 * np.sin(ph))     # darker where the strand dives under
                for (a, b) in patch:
                    k = np.where((yy > a) & (yy < b), 1.12, k)
                g = 1 + moss * 0 * u
                return X(ax + across), Y(yy), (z + 6) / S, c[0] * k, c[1] * k * g, c[2] * k * 0.95

            surface("w%d_%d" % (pi_, i), int((S + 2 * strand) / 3), 5, fw, warp_m)
        # weft: horizontal strands, alternating phase
        nweft = int(S / strand) + 2
        for j in range(-1, nweft):
            yc = (j + 0.5) * strand
            c = jitter(tone, rnd, 0.07)
            fresh = any(a < yc < b for a, b in patch)
            if fresh:
                c = jitter(srgb((160, 150, 112)), rnd, 0.04)

            def ff(u, v, yc=yc, j=j, c=c):
                xx = x0 + 2 + (x1 - x0 - 4) * u
                across = (v - 0.5) * strand * 0.92
                ph = math.pi * ((xx - xs) / strand) + math.pi * (j + 1)
                z = amp * np.sin(ph) + 1.2 * np.sin(math.pi * v)
                k = 0.66 + 0.34 * (0.5 + 0.5 * np.sin(ph))
                return X(xx), Y(yc + across), (z + 6) / S, c[0] * k, c[1] * k, c[2] * k

            surface("f%d_%d" % (pi_, j), max(int((x1 - x0) / 3), 4), 5, ff, weft_m)
    # battens on the seams and a binding batten across the middle
    for i, (x0, _, x1, _) in enumerate(cols):
        for xe in (x0,) if i else (x0, x1):
            culm("bat%d_%d" % (i, xe), xe - 7, -40, xe + 7, S + 40, jitter(srgb((150, 132, 92)), rnd, 0.1),
                 batten_m, rnd, node_gap=(140, 220), z0=8)
    culm("bind", -40, 500, S + 40, 516, srgb((140, 120, 84)), batten_m, rnd, horizontal=True, node_gap=(160, 240), z0=9)
    if moss > 0:
        mm = material("moss", "mottle", scale=(120, 120, 120), bump=0.4)
        for k in range(int(70 * moss)):
            cx, cy, rr = rnd.uniform(0, S), rnd.uniform(0, S), rnd.uniform(5, 18)
            c = jitter(srgb((96, 120, 60)), rnd, 0.15)
            surface("moss%d" % k, 8, 24, lambda u, v, cx=cx, cy=cy, rr=rr, c=c: (
                X(cx + rr * u * np.cos(2 * math.pi * v) * (1 + 0.3 * np.sin(5 * v * 6.28))),
                Y(cy + rr * u * np.sin(2 * math.pi * v)), (10 + 2 * (1 - u)) / S + 0 * u, c[0], c[1], c[2]), mm)


def set_tiles(course=256.0, edge0=200.0, per_course=3, rise_step=6.0, moss_p=0.22, tile_rgb=(84, 72, 60), seed=5):
    """Clay pan-and-cover tiles. Default: courses 256 px tall with their lower lip at y = 200 + 256k (the vanilla thatch
    rhythm), 16 pan/cover pairs across (64 px), three tiles per course with a small step at each tile's lower end.
    The flat-roof variant (FlatTiles) lays shorter, flatter courses with more moss."""
    rnd = random.Random(seed)
    pan_m = material("pan", "mottle", scale=(90, 90, 90), bump=0.25, rough=0.7)
    cov_m = material("cover", "mottle", scale=(90, 90, 90), bump=0.25, rough=0.6)
    moss_m = material("moss", "mottle", scale=(150, 150, 150), bump=0.5)
    plane("bg", -80, -300, S + 80, S + 300, -0.02, srgb((30, 30, 34)), material("bgt", "none"))
    tile = srgb(tile_rgb)
    pitch = 64.0
    ncourse = int(round(S / course))
    for k in range(-1, ncourse + 1):
        lip = edge0 + course * k
        for t in range(per_course):
            ya = lip - course + t * course / per_course      # upper end of this tile
            yb = ya + course / per_course + 10               # lower end, overlapping the next one down
            for col in range(-1, 17):
                key = (col % 16, k % ncourse, t, seed)
                r2 = random.Random(hash(key) & 0xFFFF)
                c = jitter(tile, r2, 0.09)                             # per-tile value variation
                if r2.random() < 0.03:
                    c = jitter(srgb((68, 60, 52)), r2, 0.05)           # an odd newer, darker tile
                cx = col * pitch + pitch / 2
                rise = 3 + rise_step * t                               # tiles further down a course sit higher

                def fpan(u, v, cx=cx, ya=ya, yb=yb, c=c, rise=rise):
                    xx = cx - pitch / 2 + pitch * v - 0.5
                    yy = ya + (yb - ya) * u
                    z = rise + 10 * u - 3.5 * np.sin(math.pi * v)        # shallow concave channel, rising to its lip
                    shade = (0.86 + 0.08 * u) * (0.92 + 0.08 * np.abs(np.cos(math.pi * v)))   # low pan/cover contrast
                    return X(xx), Y(yy), z / S, c[0] * shade, c[1] * shade, c[2] * shade

                surface("p%d_%d_%d" % (k, t, col), 24, 12, fpan, pan_m)
                rc = 15.0

                def fcov(u, v, cx=cx + pitch / 2, ya=ya, yb=yb, c=c, rise=rise):
                    th = math.pi * v
                    yy = ya + (yb - ya) * u
                    z = rise + 10 * u + 2 + rc * np.sin(th) * 0.55            # flatter covers: rows catch less light
                    shade = (0.80 + 0.05 * u) * (0.97 + 0.05 * np.sin(th) ** 2)   # covers a touch darker and warmer
                    return X(cx + rc * np.cos(th)), Y(yy), z / S, c[0] * shade, c[1] * shade * 0.97, c[2] * shade * 0.92

                cc = jitter(c, r2, 0.05)
                surface("c%d_%d_%d" % (k, t, col), 24, 16, fcov, cov_m)
                # end cap disc of the cover tile at its lip
                if t == per_course - 1:
                    surface("cap%d_%d" % (k, col), 4, 16, lambda u, v, cx=cx + pitch / 2, yb=yb, cc=cc, rise=rise: (
                        X(cx + rc * 1.05 * np.cos(math.pi * v) * u), Y(yb - 1 + 0 * u),
                        (rise + 12 + rc * 1.05 * np.sin(math.pi * v) * u) / S, cc[0] * 0.7, cc[1] * 0.7, cc[2] * 0.7), cov_m)
                # moss in the channel near the lip
                if r2.random() < moss_p:
                    mc = jitter(srgb((92, 112, 64)), r2, 0.2)
                    my = yb - r2.uniform(8, 40)
                    mr = r2.uniform(3, 7)
                    surface("m%d_%d_%d" % (k, t, col), 6, 16, lambda u, v, cx=cx, my=my, mr=mr, mc=mc, rise=rise: (
                        X(cx + mr * u * np.cos(2 * math.pi * v)), Y(my + mr * 1.6 * u * np.sin(2 * math.pi * v)),
                        (rise + 9) / S + 0 * u, mc[0], mc[1], mc[2]), moss_m)


def set_heightfield(name, depth=18.0, grid=1024):
    """A painter set (look_textures.py --export-hf) turned into real relief: its height map displaces a full-resolution
    grid and its albedo becomes the vertex colours; Cycles then gives proper AO and normals for window frames,
    lattice bars, crate seams, plate edges and plaster spalls."""
    data = np.load(os.path.join(OUT, name + "_hf.npz"))
    h = data["h"].astype(np.float32)
    h = (h - h.min()) / max(float(h.max() - h.min()), 1e-6)
    d = np.clip(data["d"].astype(np.float32), 0, 1)
    lin = np.where(d <= 0.04045, d / 12.92, ((d + 0.055) / 1.055) ** 2.4).astype(np.float32)
    n = grid
    gy, gx = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    # pixel centres; extend one pixel beyond each edge with wrapped data so border normals and AO stay seamless
    verts = np.stack([(gx + 0.5) / n, 1 - (gy + 0.5) / n, h[gy, gx] * depth / S], -1).reshape(-1, 3).astype(np.float32)
    cols = np.ones((n * n, 4), np.float32)
    cols[:, :3] = lin[gy, gx].reshape(-1, 3)
    me = bpy.data.meshes.new(name)
    me.vertices.add(n * n)
    me.vertices.foreach_set("co", verts.ravel())
    i = np.arange((n - 1) * (n - 1))
    r, c = i // (n - 1), i % (n - 1)
    a0 = r * n + c
    quads = np.stack([a0, a0 + n, a0 + n + 1, a0 + 1], -1).astype(np.int32)
    me.loops.add(quads.size)
    me.loops.foreach_set("vertex_index", quads.ravel())
    me.polygons.add(len(quads))
    me.polygons.foreach_set("loop_start", (np.arange(len(quads)) * 4).astype(np.int32))
    me.polygons.foreach_set("loop_total", np.full(len(quads), 4, np.int32))
    me.update(calc_edges=True)
    attr = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    attr.data.foreach_set("color", cols.ravel())
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    me.materials.append(material("hf", "none"))
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)


SETS = {
    "Windows": lambda: set_heightfield("Windows", 16.0),
    "LatticePaper": lambda: set_heightfield("LatticePaper", 10.0),
    "Details": lambda: set_heightfield("Details", 18.0),
    "Iron": lambda: set_heightfield("Iron", 10.0),
    "Banded": lambda: set_heightfield("Banded", 8.0),
    "PlasterLath": lambda: set_heightfield("PlasterLath", 10.0),
    "Timber": lambda: set_wood("Timber", "timber"),
    "Bamboo": lambda: set_wood("Bamboo", "bamboo"),
    "Weave": lambda: set_weave("Weave", 28, seed=3),
    "WeaveCoarse": lambda: set_weave("WeaveCoarse", 40, tones=[srgb((118, 100, 76)), srgb((104, 94, 78)),
                                                                srgb((112, 98, 74))], seed=4),
    # flat roofs (IrregularPlanks_Mossy: lodge, warehouse, mine roofs): grey clay tile laid flat, mossy
    "FlatTiles": lambda: set_tiles(course=128.0, edge0=0.0, per_course=2, rise_step=2.0, moss_p=0.45,
                                   tile_rgb=(80, 69, 58), seed=9),
    "RoofTiles": set_tiles,
}


HF_SETS = ("Windows", "LatticePaper", "Details", "Iron", "Banded", "PlasterLath")


def main():
    global REG, OUT
    argv = sys.argv[sys.argv.index("--") + 1:]
    REG = json.load(open(argv[0], encoding="utf-8"))
    out = OUT = argv[1]
    names = argv[2].split(",") if len(argv) > 2 and argv[2] else [
        n for n in SETS if n not in HF_SETS or os.path.exists(os.path.join(out, n + "_hf.npz"))]
    for name in names:
        reset()
        setup_render(S)
        SETS[name]()
        d = os.path.join(out, name)
        os.makedirs(d, exist_ok=True)
        render_passes(d)
        print("[bake] %s -> %s (%d objects)" % (name, d, len(bpy.data.objects)), flush=True)


main()
