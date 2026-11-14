"""Parametric parts. Every function adds Parts to a Geo and returns nothing important.

Conventions: points are Unity space (x right, y up, z forward); sizes in tile units. Deliberate irregularity comes
from geo.rng (a fixed seed per model), so the same script always makes the same model.
"""
import math

import numpy as np

from core import (Part, fix_winding, frame_from, quad_part, rot_axis, TEXEL, TIMBER, BAMBOO_GOLD, BAMBOO_GREEN,
                  PLASTER, PLASTER_LATH, TILE, WINDOWS, DETAILS, EARTH, WEAVE, IRON,
                  WOOD_STRIPS, WOOD_SHORT, WOOD_BLOCK, WOOD_DISCS, WIN_LATTICE, WIN_DARK, WIN_PANES, WIN_ROUND,
                  DET_ROPE, DET_RED, DET_CLOTH, TILE_COURSES, TILE_COLS)

V = np.asarray


def _pick(geo, regions):
    return regions[int(geo.rng.integers(len(regions)))]


def region_uv(local_u, local_v, region, density=TEXEL, rng=None):
    """Map local coordinates (units) into a region at the given density, compressing if they do not fit, with a
    random offset inside the slack so repeated parts do not show the same patch."""
    u0, v0, u1, v1 = region
    lu, lv = np.asarray(local_u, float), np.asarray(local_v, float)
    lu = lu - lu.min()
    lv = lv - lv.min()
    ru, rv = (u1 - u0), (v1 - v0)
    su = min(density, ru / max(lu.max(), 1e-6))
    sv = min(density, rv / max(lv.max(), 1e-6))
    ou = (ru - lu.max() * su) * (rng.uniform() if rng is not None else 0.5)
    ov = (rv - lv.max() * sv) * (rng.uniform() if rng is not None else 0.5)
    return np.stack([u0 + ou + lu * su, v0 + ov + lv * sv], 1)


# ------------------------------------------------------------------------------------------- tubes and poles
def tube(geo, path, radii, material, sides=6, strips=None, caps=True, twist=0.0, up=(0, 1, 0), tags=(),
         v_density=TEXEL, flat=False):
    """A prism swept along a polyline. Each segment maps its length along a wood strip (v) and the circumference
    across it (u), restarting where a strip runs out, so long poles keep the vanilla texel density. Caps use the
    log-end / culm cross-section discs."""
    path = [V(p, float) for p in path]
    radii = list(radii) if np.ndim(radii) else [radii] * len(path)
    strips = strips or WOOD_STRIPS
    strip = _pick(geo, strips)
    rings = []
    for i, p in enumerate(path):
        d = path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]
        F = frame_from(d, up)
        ang0 = twist + (math.pi / sides if sides == 4 else 0)
        ring = []
        for k in range(sides + 1):
            a = ang0 + 2 * math.pi * k / sides
            off = F[:, 0] * math.cos(a) + F[:, 1] * math.sin(a)
            ring.append((p + off * radii[i], off))
        rings.append(ring)
    P, N, UV, T = [], [], [], []
    vpos = strip[1] + geo.rng.uniform(0, 0.25) * (strip[3] - strip[1])
    for i in range(len(path) - 1):
        L = np.linalg.norm(path[i + 1] - path[i])
        dv = L * v_density
        if vpos + dv > strip[3]:
            strip = _pick(geo, strips)
            if dv > strip[3] - strip[1]:
                dv = strip[3] - strip[1]
            vpos = strip[1]
        base = len(P)
        for k in range(sides + 1):
            u = strip[0] + (strip[2] - strip[0]) * k / sides
            for j, vv in ((i, vpos), (i + 1, vpos + dv)):
                pos, off = rings[j][k]
                P.append(pos)
                N.append(off)
                UV.append((u, vv))
        for k in range(sides):
            a, b, c, d = base + 2 * k, base + 2 * k + 2, base + 2 * k + 3, base + 2 * k + 1
            T += [(a, b, c), (a, c, d)]
        vpos += dv
    P, N, UV, T = V(P), V(N), V(UV), V(T)
    if flat:   # faceted: duplicate per face with face normals (beams)
        P2, N2, UV2, T2 = [], [], [], []
        for t in T:
            g = np.cross(P[t[1]] - P[t[0]], P[t[2]] - P[t[0]])
            g /= max(np.linalg.norm(g), 1e-12)
            if np.dot(g, N[t[0]]) < 0:
                g = -g
            for v in t:
                P2.append(P[v])
                N2.append(g)
                UV2.append(UV[v])
            T2.append((len(P2) - 3, len(P2) - 2, len(P2) - 1))
        P, N, UV, T = V(P2), V(N2), V(UV2), V(T2)
    geo.add(Part(material, P, N, UV, fix_winding(P, N, T)), tags)
    if caps:
        ends = [(0, -1), (len(path) - 1, 1)]
        if caps == "start":
            ends = ends[:1]
        elif caps == "end":
            ends = ends[1:]
        for end, sgn in ends:
            d = path[end] - path[end - 1] if end else path[1] - path[0]
            d = d / np.linalg.norm(d) * sgn
            if material.startswith("BaseWood"):
                cu, cv, cr = WOOD_DISCS[int(geo.rng.integers(len(WOOD_DISCS)))]
            else:
                r0 = strips[0]
                cu, cv, cr = ((r0[0] + r0[2]) / 2, (r0[1] + r0[3]) / 2, 0.0)
            cp, cuv = [], []
            for k in range(sides):
                pos, off = rings[end][k]
                a = 2 * math.pi * k / sides
                cp.append(pos)
                cuv.append((cu + cr * math.cos(a), cv + cr * math.sin(a)))
            ct = [(0, k, k + 1) for k in range(1, sides - 1)]    # a fan: sides - 2 triangles, no centre vertex
            cP = V(cp)
            cN = np.tile(d, (len(cP), 1))
            geo.add(Part(material, cP, cN, V(cuv), fix_winding(cP, cN, V(ct))), tags)


def pole(geo, a, b, r=0.05, material=BAMBOO_GOLD, sides=6, bend=0.02, taper=0.85, segs=None, tags=(), caps=True):
    """A bamboo culm or a round timber pole from a to b with a slight random bend and taper."""
    a, b = V(a, float), V(b, float)
    L = np.linalg.norm(b - a)
    segs = segs or max(1, int(math.ceil(L / 0.9)))
    d = (b - a) / L
    side = np.cross(d, [0, 1, 0])
    if np.linalg.norm(side) < 1e-3:
        side = np.cross(d, [1, 0, 0])
    side /= np.linalg.norm(side)
    other = np.cross(d, side)
    bend_dir = side * geo.jitter(1) + other * geo.jitter(1)
    pts, radii = [], []
    for i in range(segs + 1):
        t = i / segs
        pts.append(a + (b - a) * t + bend_dir * bend * L * math.sin(math.pi * t))
        radii.append(r * (1 - (1 - taper) * t))
    tube(geo, pts, radii, material, sides, tags=tags, caps=caps)


def beam(geo, a, b, w=0.09, h=None, material=TIMBER, up=(0, 1, 0), tags=(), caps=True, sag=0.0, segs=1):
    """A squared timber from a to b (4 flat sides), optionally sagging in the middle."""
    a, b = V(a, float), V(b, float)
    h = h or w
    pts = [a + (b - a) * (i / segs) + V([0, -sag * math.sin(math.pi * i / segs), 0]) for i in range(segs + 1)]
    r = math.hypot(w, h) / 2
    tube(geo, pts, [r] * len(pts), material, 4, caps=caps, up=up, tags=tags, flat=True)


def lashing(geo, at, direction, r=0.06, tags=()):
    """A rope binding: a short thick ring around a pole at a joint."""
    d = V(direction, float)
    d /= np.linalg.norm(d)
    tube(geo, [V(at) - d * 0.025, V(at) + d * 0.025], [r * 1.12, r * 1.12], DETAILS, sides=6, strips=[DET_ROPE],
         caps=False, tags=tags)


# ------------------------------------------------------------------------------------------- boxes and panels
_FACES = [((1, 0, 0), (0, 0, -1), (0, 1, 0)), ((-1, 0, 0), (0, 0, 1), (0, 1, 0)),
          ((0, 1, 0), (1, 0, 0), (0, 0, -1)), ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
          ((0, 0, 1), (1, 0, 0), (0, 1, 0)), ((0, 0, -1), (-1, 0, 0), (0, 1, 0))]


def box(geo, lo, hi, material, region=(0, 0, 1, 1), R=None, t=None, tags=(), skip=(), density=TEXEL, jitter=0.0):
    """Axis-aligned box (then rotated by R about the origin and moved by t). Each face is planar-mapped into region.
    skip: face indices to omit (0 +x, 1 -x, 2 +y, 3 -y, 4 +z, 5 -z)."""
    lo, hi = V(lo, float), V(hi, float)
    c, h = (lo + hi) / 2, (hi - lo) / 2
    P, N, UV, T = [], [], [], []
    for fi, (n, ua, va) in enumerate(_FACES):
        if fi in skip:
            continue
        n, ua, va = V(n, float), V(ua, float), V(va, float)
        corners = [c + h * (n + su * ua + sv * va) for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        lu = [np.dot(p, ua) for p in corners]
        lv = [np.dot(p, va) for p in corners]
        uv = region_uv(lu, lv, region, density, geo.rng)
        base = len(P)
        for k in range(4):
            p = corners[k]
            if jitter:
                p = p + V([geo.jitter(jitter), geo.jitter(jitter), geo.jitter(jitter)]) * (p[1] > lo[1] + 1e-6)
            P.append(p)
            N.append(n)
            UV.append(uv[k])
        T += [(base, base + 1, base + 2), (base, base + 2, base + 3)]
    P, N = V(P), V(N)
    if R is not None:
        P, N = P @ V(R).T, N @ V(R).T
    if t is not None:
        P = P + V(t)
    geo.add(Part(material, P, N, V(UV), fix_winding(P, N, V(T))), tags)


def panel(geo, corners, material, region=(0, 0, 1, 1), density=TEXEL, both=False, tags=(), uvs=None):
    """A flat quad (bottom-left, bottom-right, top-right, top-left seen from the front) planar-mapped into region."""
    P = V(corners, float)
    ua = P[1] - P[0]
    ua /= np.linalg.norm(ua)
    va = P[3] - P[0]
    va = va - ua * np.dot(va, ua)
    va /= np.linalg.norm(va)
    uv = uvs if uvs is not None else region_uv([np.dot(p, ua) for p in P], [np.dot(p, va) for p in P], region,
                                               density, geo.rng)
    geo.add(quad_part(material, P, uvs=uv), tags)
    if both:
        Q = P[[1, 0, 3, 2]]
        geo.add(quad_part(material, Q, uvs=V(uv)[[1, 0, 3, 2]]), tags)


def boards(geo, origin, along, across, length, width, n, material=TIMBER, thick=0.04, gap=0.008, tags=(), warp=0.012):
    """n boards side by side (a floor, a door leaf, a shutter): each a thin flat beam with a little random warp."""
    o, al, ac = V(origin, float), V(along, float), V(across, float)
    al /= np.linalg.norm(al)
    ac /= np.linalg.norm(ac)
    up = np.cross(al, ac)
    bw = (width - gap * (n - 1)) / n
    for i in range(n):
        s = o + ac * (i * (bw + gap) + bw / 2) + up * geo.jitter(warp)
        lw = length * (1 + geo.jitter(0.03))
        beam(geo, s, s + al * lw, w=bw, h=thick, material=material, up=up, tags=tags)


# ------------------------------------------------------------------------------------------- walls, windows, doors
def frame_ring(geo, c, n, s, w, h, f, depth=0.04, material=TIMBER, tags=()):
    """A flat picture frame around a w x h opening centred at c in the plane (s, up), facing n: front face, outer
    edge and inner reveal, 3 quads per side (24 triangles)."""
    c, n, s = V(c, float), V(n, float), V(s, float)
    up = np.cross(n, s)
    if up[1] < 0:
        up = -up
    hw, hh = w / 2, h / 2
    inner = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    outer = [(-hw - f, -hh - f), (hw + f, -hh - f), (hw + f, hh + f), (-hw - f, hh + f)]

    def P(xy, dz):
        return c + s * xy[0] + up * xy[1] + n * dz
    for i in range(4):
        j = (i + 1) % 4
        mid_dir = s * (inner[i][0] + inner[j][0]) / 2 + up * (inner[i][1] + inner[j][1]) / 2
        mid_dir /= np.linalg.norm(mid_dir)
        quads = [([P(inner[i], depth), P(inner[j], depth), P(outer[j], depth), P(outer[i], depth)], n),
                 ([P(outer[i], depth), P(outer[j], depth), P(outer[j], -0.01), P(outer[i], -0.01)], mid_dir),
                 ([P(inner[i], depth), P(inner[j], depth), P(inner[j], -0.01), P(inner[i], -0.01)], -mid_dir)]
        for q, nn in quads:
            strip = _pick(geo, WOOD_STRIPS)
            L = np.linalg.norm(q[1] - q[0])
            uv = V([(strip[0], strip[1]), (strip[0], strip[1] + L * TEXEL), (strip[2], strip[1] + L * TEXEL),
                    (strip[2], strip[1])])
            geo.add(quad_part(material, q, uvs=uv, normal=nn), tags)


def window(geo, center, normal, w=0.42, h=0.42, frame=0.06, region=WIN_LATTICE, sill=True, shutters=False, tags=()):
    """A lattice window: glowing lattice paper set into a dark timber surround, a sill below."""
    c, n = V(center, float), V(normal, float)
    n /= np.linalg.norm(n)
    s = np.cross([0, 1, 0], n)
    s /= np.linalg.norm(s)
    up = V([0, 1, 0.0])
    corners = [c - s * w / 2 - up * h / 2, c + s * w / 2 - up * h / 2, c + s * w / 2 + up * h / 2,
               c - s * w / 2 + up * h / 2]
    u0, v0, u1, v1 = region
    geo.add(quad_part(WINDOWS, [p - n * 0.01 for p in corners],
                      uvs=V([[u0, v0], [u1, v0], [u1, v1], [u0, v1]])), set(tags) | {"glow"})
    frame_ring(geo, c, n, s, w, h, frame, tags=tags)
    # one central mullion so the lattice reads as a Chinese window, not a single pane
    beam(geo, (corners[0] + corners[1]) / 2, (corners[3] + corners[2]) / 2, w=frame * 0.5, h=frame * 0.5,
         material=TIMBER, tags=tags, caps=False)
    if sill:
        sc = c - up * (h / 2 + frame) + n * 0.03
        box(geo, (-w / 2 - frame * 1.4, -0.02, -0.035), (w / 2 + frame * 1.4, 0.02, 0.05), TIMBER,
            WOOD_STRIPS[0], R=np.stack([s, up, n], 1), t=sc, tags=tags, skip=(3, 5))
    if shutters:
        for sg in (-1, 1):
            hinge = c + s * sg * (w / 2 + f)
            o = hinge + n * 0.02 - up * h / 2
            al = up
            ac = (s * sg * 0.55 + n * 0.85)
            boards(geo, o, al, ac / np.linalg.norm(ac), h, w * 0.5, 2, TIMBER, thick=0.025, tags=tags)


def door(geo, center_bottom, normal, w=0.42, h=0.62, frame=0.075, leaf="ajar", tags=()):
    """A doorway: dark opening, timber posts and lintel, a stone step; leaf 'ajar' adds a plank door swung in."""
    c, n = V(center_bottom, float), V(normal, float)
    n /= np.linalg.norm(n)
    s = np.cross([0, 1, 0], n)
    s /= np.linalg.norm(s)
    up = V([0, 1.0, 0])
    corners = [c - s * w / 2, c + s * w / 2, c + s * w / 2 + up * h, c - s * w / 2 + up * h]
    u0, v0, u1, v1 = WIN_DARK
    geo.add(quad_part(WINDOWS, [p - n * 0.012 for p in corners],
                      uvs=V([[0.11, 0.05], [0.40, 0.05], [0.40, 0.39], [0.11, 0.39]])), set(tags) | {"glow"})
    for sg in (-1, 1):
        p = c + s * sg * (w / 2 + frame / 2) + n * 0.01
        beam(geo, p, p + up * (h + frame * 0.6), w=frame, h=frame, material=TIMBER, tags=tags)
    lp = c + up * (h + frame * 0.5) + n * 0.02
    beam(geo, lp - s * (w / 2 + frame * 2.2), lp + s * (w / 2 + frame * 2.2), w=frame * 1.4, h=frame * 1.3,
         material=TIMBER, tags=tags)
    step = c + n * 0.09
    box(geo, (-w / 2 - 0.05, -0.0, -0.08), (w / 2 + 0.05, 0.05, 0.08), PLASTER, R=np.stack([s, up, n], 1), t=step,
        tags=set(tags) | {"stone"})
    if leaf == "ajar":
        hinge = c - s * (w / 2) - n * 0.01
        ac = -n * 0.97 - s * 0.25        # swung right in, so the lit doorway shows
        boards(geo, hinge, up, ac, h * 0.98, w * 0.92, 2, TIMBER, thick=0.03, tags=tags)


def wall(geo, p0, p1, y0, y1, openings=(), post=0.1, rail=True, infill=PLASTER_LATH, frame_mat=TIMBER,
         inset=0.025, braces=False, tags=()):
    """A timber-frame wall from p0 to p1 (xz at y0..y1), facing outwards to the left of p0->p1 seen from above
    (i.e. normal = up x direction). Posts at both ends, sill and top plate, a mid rail, lime-plaster infill set
    back from the frame. openings: [("window"|"door"|"panes", s centre 0..1, width, bottom, top)] in units above y0."""
    p0, p1 = V([p0[0], 0, p0[1]], float), V([p1[0], 0, p1[1]], float)
    d = p1 - p0
    L = np.linalg.norm(d)
    d /= L
    n = np.cross([0, 1, 0], d)
    n /= np.linalg.norm(n)
    up = V([0, 1.0, 0])

    def at(s, y):
        return p0 + d * s + up * y

    with geo.tagged(*tags):
        with geo.tagged("frame"):
            for s in (0.0, L):
                beam(geo, at(s, y0) + n * 0.0, at(s, y1 + 0.02), w=post, h=post, material=frame_mat, caps="end")
            beam(geo, at(-0.02, y0 + post / 2) + n * 0.005, at(L + 0.02, y0 + post / 2) + n * 0.005, w=post * 0.95,
                 material=frame_mat, caps=False)
            beam(geo, at(-0.04, y1 - post / 2) + n * 0.005, at(L + 0.04, y1 - post / 2) + n * 0.005, w=post,
                 material=frame_mat, caps=False)
        ym = y0 + (y1 - y0) * 0.42
        if rail:
            beam(geo, at(0.0, ym) + n * 0.0, at(L, ym), w=post * 0.7, material=frame_mat, tags={"frame"},
                 caps=False)
        if braces and L > 0.9:
            beam(geo, at(post, y0 + post), at(min(L * 0.35, 0.6), ym), w=post * 0.6, material=frame_mat,
                 caps=False)
        # infill: plaster rectangles around the openings
        holes = []
        for kind, sc, w, ob, ot in openings:
            holes.append((sc * L - w / 2 - 0.04, sc * L + w / 2 + 0.04, y0 + ob - 0.03, y0 + ot + 0.04, kind))
        cuts_s = sorted({0.0, L} | {h[0] for h in holes} | {h[1] for h in holes})
        cuts_y = sorted({y0, y1} | ({ym} if rail else set()) | {h[2] for h in holes} | {h[3] for h in holes})
        for i in range(len(cuts_s) - 1):
            for j in range(len(cuts_y) - 1):
                s0, s1, ya, yb = cuts_s[i], cuts_s[i + 1], cuts_y[j], cuts_y[j + 1]
                if s1 - s0 < 1e-4 or yb - ya < 1e-4:
                    continue
                sm, ymid = (s0 + s1) / 2, (ya + yb) / 2
                if any(h[0] <= sm <= h[1] and h[2] <= ymid <= h[3] for h in holes):
                    continue
                q = [at(s0, ya) - n * inset, at(s1, ya) - n * inset, at(s1, yb) - n * inset, at(s0, yb) - n * inset]
                lu = [s0, s1, s1, s0]
                lv = [ya, ya, yb, yb]
                u0 = (geo.rng.uniform(0, 0.4))
                uv = np.stack([u0 + V(lu) * TEXEL * 0.5, 0.05 + V(lv) * TEXEL * 0.5], 1)
                uv = np.clip(uv, 0, 1)
                geo.add(quad_part(infill, q, uvs=uv))
        for kind, sc, w, ob, ot in openings:
            cx = at(sc * L, y0 + (ob + ot) / 2)
            if kind == "window":
                window(geo, cx - n * inset, n, w, ot - ob)
            elif kind == "panes":
                window(geo, cx - n * inset, n, w, ot - ob, region=WIN_PANES)
            elif kind == "door":
                door(geo, at(sc * L, y0 + ob) - n * inset, n, w, ot - ob)


# ------------------------------------------------------------------------------------------- roofs
def _tile_patch(geo, E0, E1, R1, R0, rows, cols, sag, lift_fn, thick, rib=0.035, under=TIMBER, tags=(),
                col_offset=0, eave_drip=True, under_band=0.45):
    """One roof slope: a bilinear patch from the eave edge (E0->E1) up to the ridge edge (R0->R1), cut into tile
    columns (one cover-tile ridge each, aligned with the texture's columns) and courses (one texture course each).
    The slope sags gently (Sichuan farmhouse curve), eaves may lift at the corners."""
    E0, E1, R1, R0 = (V(p, float) for p in (E0, E1, R1, R0))

    def pt(s, t):
        e = E0 + (E1 - E0) * s
        r = R0 + (R1 - R0) * s
        p = e + (r - e) * t
        p[1] += -sag * math.sin(math.pi * t) * (1 - 0.3 * t) + lift_fn(s) * (1 - t) ** 2
        return p

    P, N, UV, T = [], [], [], []
    ridge_vec = []
    for ci in range(cols):
        s0, s1 = ci / cols, (ci + 1) / cols
        sm = (s0 + s1) / 2
        col = (ci + col_offset) % TILE_COLS
        cu0, cu1 = col / TILE_COLS, (col + 1) / TILE_COLS
        for ri in range(rows):
            t0, t1 = ri / rows, (ri + 1) / rows
            cv0, cv1 = TILE_COURSES[(ri + ci // 3) % 4]
            a, b, c, d = pt(s0, t0), pt(s1, t0), pt(s1, t1), pt(s0, t1)
            m0, m1 = pt(sm, t0), pt(sm, t1)
            nrm = np.cross(b - a, d - a)
            nrm /= max(np.linalg.norm(nrm), 1e-9)
            if nrm[1] < 0:
                nrm = -nrm
            m0 = m0 + nrm * rib
            m1 = m1 + nrm * rib
            base = len(P)
            um = (cu0 + cu1) / 2
            for p, uv in ((a, (cu0, cv0)), (m0, (um, cv0)), (b, (cu1, cv0)), (c, (cu1, cv1)), (m1, (um, cv1)),
                          (d, (cu0, cv1))):
                P.append(p)
                UV.append(uv)
                N.append(nrm)
            # two sloped faces per cell: left half and right half of the cover tile
            T += [(base, base + 1, base + 4), (base, base + 4, base + 5), (base + 1, base + 2, base + 3),
                  (base + 1, base + 3, base + 4)]
            # per-vertex normals tilted to the side of the rib for a rounded look
            sd = (b - a)
            sd /= max(np.linalg.norm(sd), 1e-9)
            for k, w in ((0, -0.45), (1, 0.0), (2, 0.45), (3, 0.45), (4, 0.0), (5, -0.45)):
                nn = nrm + sd * w
                N[base + k] = nn / np.linalg.norm(nn)
    P, N, T = V(P), V(N), V(T)
    geo.add(Part(TILE, P, N, V(UV), fix_winding(P, N, T)), tags)
    # underside (dark boards), offset down by the roof's thickness, and the eave fascia
    us = 4
    band = min(1.0, under_band)
    Pu, Nu, UVu, Tu = [], [], [], []
    for ci in range(us + 1):
        for ri in range(rows + 1):
            p = pt(ci / us, band * ri / rows) - V([0, thick, 0])
            Pu.append(p)
            Nu.append((0, -1.0, 0))
            UVu.append((WOOD_BLOCK[0] + 0.5 * ci / us, WOOD_BLOCK[1] + 0.9 * ri / rows))
    for ci in range(us):
        for ri in range(rows):
            a = ci * (rows + 1) + ri
            b = a + rows + 1
            Tu += [(a, b, b + 1), (a, b + 1, a + 1)]
    Pu, Nu = V(Pu), V(Nu)
    geo.add(Part(under, Pu, Nu, V(UVu), fix_winding(Pu, Nu, V(Tu))), tags)
    # fascia along the eave: a board from top to underside
    pts = [pt(i / us, 0) for i in range(us + 1)]
    outward = E0 - R0
    outward[1] = 0
    outward /= max(np.linalg.norm(outward), 1e-9)
    strip = WOOD_STRIPS[1]
    Pf, Nf, UVf, Tf = [], [], [], []
    for i, p in enumerate(pts):
        Pf += [p + V([0, rib * 0.6, 0]), p - V([0, thick, 0])]
        Nf += [outward, outward]
        vv = strip[1] + (strip[3] - strip[1]) * i / us
        UVf += [(strip[0], vv), (strip[2], vv)]
    for i in range(us):
        a = 2 * i
        Tf += [(a, a + 2, a + 3), (a, a + 3, a + 1)]
    Pf, Nf = V(Pf), V(Nf)
    geo.add(Part(TIMBER, Pf, Nf, V(UVf), fix_winding(Pf, Nf, V(Tf))), tags)
    return pt


def roof(geo, x0, z0, x1, z1, y_eave, y_ridge, kind="gable", overhang=0.22, sag=0.07, lift=0.06, thick=0.07,
         tile=0.3, course=0.36, ridge=True, ridge_ends=0.07, axis="x", tags=(), hip_inset=None):
    """A grey clay tile roof over the rectangle x0..x1, z0..z1. kind: 'gable' (ridge along `axis`), 'hip',
    'lean' (single slope, high side at z1 or x1), 'pyramid' (hip with a point). Tile columns are about `tile`
    wide and courses `course` long. Returns the ridge's ends."""
    o = overhang
    X0, X1, Z0, Z1 = x0 - o, x1 + o, z0 - o, z1 + o
    tags = set(tags) | {"roof"}

    def cols_for(length):
        return max(2, int(round(length / tile)))

    def rows_for(a, b):
        return max(2, int(round(np.linalg.norm(V(a) - V(b)) / course)))

    def corner_lift(s):
        return lift * (abs(2 * s - 1) ** 3)

    ends = []
    if axis == "z":    # build along x and rotate the result 90 degrees about the centre
        sub = type(geo)(int(geo.rng.integers(1 << 30)))
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        hw, hd = (x1 - x0) / 2, (z1 - z0) / 2
        e = roof(sub, cx - hd, cz - hw, cx + hd, cz + hw, y_eave, y_ridge, kind, overhang, sag, lift, thick, tile,
                 course, ridge, ridge_ends, "x", tags, hip_inset)
        R = rot_axis((0, 1, 0), math.pi / 2)
        c = V([cx, 0, cz])
        for p in sub.parts:
            q = p.transformed(R, c - R @ c)
            geo.add(q)
        return [R @ (V(p) - c) + c for p in e]
    if kind == "lean":
        _tile_patch(geo, (X0, y_eave, Z0), (X1, y_eave, Z0), (X1, y_ridge, Z1), (X0, y_ridge, Z1),
                    rows_for((0, y_eave, Z0), (0, y_ridge, Z1)), cols_for(X1 - X0), sag * 0.6, corner_lift, thick,
                    tags=tags)
        # the high edge gets a capping board
        beam(geo, (X0, y_ridge + 0.02, Z1), (X1, y_ridge + 0.02, Z1), w=0.07, h=0.06, tags=tags)
        return [(X0, y_ridge, Z1), (X1, y_ridge, Z1)]
    zm = (Z0 + Z1) / 2
    if kind == "xieshan":
        # hip-and-gable: short hipped ends below, a small plastered gable above them, the long slopes run to the
        # ridge. The rural hall roof of the Chengdu plain (gentle, not the palace version).
        i = hip_inset if hip_inset is not None else min(0.5, (Z1 - Z0) * 0.3)
        f = 0.42
        ym = y_eave + (y_ridge - y_eave) * f
        zf0, zf1 = Z0 + (zm - Z0) * f, Z1 - (Z1 - zm) * f
        o2 = 0.1
        rl = max(2, rows_for((0, y_eave, Z0), (0, ym, zf0)))
        ru = max(2, rows_for((0, ym, zf0), (0, y_ridge, zm)))
        for (Za, zf, off) in ((Z0, zf0, 0), (Z1, zf1, 5)):
            sgn = 1 if Za == Z0 else -1
            xa, xb = (X0, X1) if sgn > 0 else (X1, X0)
            ia, ib = (X0 + i, X1 - i) if sgn > 0 else (X1 - i, X0 + i)
            ea, eb = (X0 + i - o2, X1 - i + o2) if sgn > 0 else (X1 - i + o2, X0 + i - o2)
            _tile_patch(geo, (xa, y_eave, Za), (xb, y_eave, Za), (ib, ym, zf), (ia, ym, zf), rl, cols_for(X1 - X0),
                        sag * 0.4, corner_lift, thick, tags=tags, col_offset=off)
            _tile_patch(geo, (ea, ym - 0.02, zf), (eb, ym - 0.02, zf), (eb, y_ridge, zm), (ea, y_ridge, zm), ru,
                        cols_for(X1 - X0 - 2 * i), sag * 0.5, lambda s: 0.0, thick, tags=tags, col_offset=off + 2,
                        under_band=0.0)
        for (xa, xi, sg) in ((X0, X0 + i, -1), (X1, X1 - i, 1)):
            if sg < 0:
                E0, E1, R1, R0 = (xa, y_eave, Z1), (xa, y_eave, Z0), (xi, ym, zf0), (xi, ym, zf1)
            else:
                E0, E1, R1, R0 = (xa, y_eave, Z0), (xa, y_eave, Z1), (xi, ym, zf1), (xi, ym, zf0)
            _tile_patch(geo, E0, E1, R1, R0, rl, cols_for(Z1 - Z0), sag * 0.4, corner_lift, thick, tags=tags,
                        col_offset=3 if sg < 0 else 9)
            gable_end(geo, xi + sg * 0.03, zf0 + 0.02, zf1 - 0.02, ym - 0.02, y_ridge, outward=sg, sag=0.0,
                      post=0.06, tags=tags)
        for (cx_, cz_) in ((X0, Z0), (X1, Z0), (X1, Z1), (X0, Z1)):
            a = V([cx_, y_eave + lift + 0.03, cz_])
            b = V([X0 + i if cx_ == X0 else X1 - i, ym + 0.02, zf0 if cz_ == Z0 else zf1])
            tube(geo, [a, b], [0.045, 0.05], TILE, sides=5,
                 strips=[(c / TILE_COLS, TILE_COURSES[0][0], (c + 1) / TILE_COLS, TILE_COURSES[0][1]) for c in range(4)],
                 caps=False, tags=tags, v_density=0.25)
        ends = [V([X0 + i - o2, y_ridge, zm]), V([X1 - i + o2, y_ridge, zm])]
    elif kind == "gable":
        R0, R1 = (X0, y_ridge, zm), (X1, y_ridge, zm)
        rows = rows_for((0, y_eave, Z0), (0, y_ridge, zm))
        cols = cols_for(X1 - X0)
        _tile_patch(geo, (X0, y_eave, Z0), (X1, y_eave, Z0), R1, R0, rows, cols, sag, corner_lift, thick, tags=tags)
        _tile_patch(geo, (X1, y_eave, Z1), (X0, y_eave, Z1), R0, R1, rows, cols, sag, corner_lift, thick, tags=tags,
                    col_offset=5)
        # verge boards along the gable edges
        for xx, sg in ((X0, -1), (X1, 1)):
            for zz in (Z0, Z1):
                beam(geo, (xx, y_eave - 0.02, zz), (xx, y_ridge - 0.01, zm), w=0.06, h=0.07, sag=sag * 0.7, segs=2,
                     tags=tags, caps=False)
        ends = [V(R0), V(R1)]
    else:   # hip / pyramid
        inset = hip_inset if hip_inset is not None else (Z1 - Z0) / 2
        if kind == "pyramid":
            inset = (X1 - X0) / 2
        rx0, rx1 = X0 + inset, X1 - inset
        if rx1 < rx0:
            rx0 = rx1 = (X0 + X1) / 2
        R0, R1 = (rx0, y_ridge, zm), (rx1, y_ridge, zm)
        rows = rows_for((0, y_eave, Z0), (0, y_ridge, zm))
        _tile_patch(geo, (X0, y_eave, Z0), (X1, y_eave, Z0), R1, R0, rows, cols_for(X1 - X0), sag, corner_lift,
                    thick, tags=tags)
        _tile_patch(geo, (X1, y_eave, Z1), (X0, y_eave, Z1), R0, R1, rows, cols_for(X1 - X0), sag, corner_lift,
                    thick, tags=tags, col_offset=5)
        _tile_patch(geo, (X0, y_eave, Z1), (X0, y_eave, Z0), R0, R0, rows, cols_for(Z1 - Z0), sag, corner_lift,
                    thick, tags=tags, col_offset=3)
        _tile_patch(geo, (X1, y_eave, Z0), (X1, y_eave, Z1), R1, R1, rows, cols_for(Z1 - Z0), sag, corner_lift,
                    thick, tags=tags, col_offset=9)
        # hip ridges: rounded tile rolls from each corner up to the ridge
        for cx_, cz_, rr in ((X0, Z0, R0), (X1, Z0, R1), (X1, Z1, R1), (X0, Z1, R0)):
            a = V([cx_, y_eave + lift + 0.03, cz_])
            b = V(rr) + V([0, 0.03, 0])
            tube(geo, [a, (a + b) / 2 - V([0, sag * 0.5, 0]), b], [0.045, 0.05, 0.05], TILE, sides=5,
                 strips=[(c / TILE_COLS, TILE_COURSES[0][0], (c + 1) / TILE_COLS, TILE_COURSES[0][1]) for c in range(4)],
                 caps=False, tags=tags, v_density=0.25)
        ends = [V(R0), V(R1)]
    if ridge and np.linalg.norm(ends[1] - ends[0]) > 0.05:
        ridge_course(geo, ends[0], ends[1], ends_lift=ridge_ends, tags=tags)
    elif ridge:
        # pyramid: a little finial pot on the point
        lathe(geo, [(0.0, 0.0), (0.07, 0.0), (0.08, 0.05), (0.05, 0.11), (0.06, 0.14), (0.0, 0.16)],
              ends[0] - V([0, 0.03, 0]), 6, TILE, uv_region=(0.0, TILE_COURSES[1][0], 0.25, TILE_COURSES[1][1]),
              tags=tags)
    return ends


def ridge_course(geo, a, b, h=0.09, w=0.13, ends_lift=0.07, tags=()):
    """The ridge: a rounded roll of stacked tiles with the ends turned up a little (gently, never palace-sharp)."""
    a, b = V(a, float), V(b, float)
    d = b - a
    L = np.linalg.norm(d)
    d /= L
    n = 6
    pts, radii = [], []
    ext = 0.08
    for i in range(n + 1):
        t = i / n
        p = a - d * ext + (b - a + 2 * d * ext) * t
        e = abs(2 * t - 1)
        p = p + V([0, h * 0.5 + ends_lift * (e ** 4), 0])
        pts.append(p)
        radii.append(w / 2 * (1 + 0.15 * e ** 4))
    regions = [(c / TILE_COLS, TILE_COURSES[2][0], (c + 2) / TILE_COLS, TILE_COURSES[2][1]) for c in range(0, 14, 2)]
    tube(geo, pts, radii, TILE, sides=6, strips=regions, caps=True, tags=tags, v_density=0.35)
    # a plaster band under the roll (Sichuan ridges are often bedded in lime)
    tube(geo, [p - V([0, h * 0.42, 0]) for p in pts[1:-1]], [w * 0.42] * (n - 1), PLASTER, sides=4, caps=True,
         strips=[(0.1, 0.1, 0.4, 0.9)], tags=tags, flat=True)


# ------------------------------------------------------------------------------------------- lathes and objects
def lathe(geo, profile, base, sides, material, uv_region=None, axis=(0, 1, 0), tags=(), cap_top=True, smooth=True,
          strips=None):
    """Revolve a profile [(radius, height)] about axis through base. Used for jars, barrels, buckets, lanterns,
    pots and finials. UV: around -> u across the region, up the profile -> v."""
    base = V(base, float)
    F = frame_from(axis)
    s, u, d = F[:, 0], F[:, 1], F[:, 2]   # local z = axis
    region = uv_region or _pick(geo, strips or WOOD_STRIPS)
    u0, v0, u1, v1 = region
    prof = [(float(r), float(h)) for r, h in profile]
    lens = [0.0]
    for i in range(1, len(prof)):
        lens.append(lens[-1] + math.hypot(prof[i][0] - prof[i - 1][0], prof[i][1] - prof[i - 1][1]))
    tot = max(lens[-1], 1e-6)
    vscale = min(TEXEL, (v1 - v0) / tot)
    P, N, UV, T = [], [], [], []
    for k in range(sides + 1):
        a = 2 * math.pi * k / sides
        radial = s * math.cos(a) + u * math.sin(a)
        for i, (r, h) in enumerate(prof):
            P.append(base + radial * r + d * h)
            i0, i1 = max(i - 1, 0), min(i + 1, len(prof) - 1)
            dr, dh = prof[i1][0] - prof[i0][0], prof[i1][1] - prof[i0][1]
            nn = radial * dh - d * dr
            nn /= max(np.linalg.norm(nn), 1e-9)
            N.append(nn)
            UV.append((u0 + (u1 - u0) * k / sides, v0 + lens[i] * vscale))
    m = len(prof)
    for k in range(sides):
        for i in range(m - 1):
            a = k * m + i
            b = (k + 1) * m + i
            if prof[i][0] < 1e-6 and prof[i + 1][0] < 1e-6:
                continue
            T += [(a, b, b + 1), (a, b + 1, a + 1)]
    P, N = V(P), V(N)
    T = V(T)
    # drop triangles collapsed at the axis
    keep = [t for t in T if np.linalg.norm(np.cross(P[t[1]] - P[t[0]], P[t[2]] - P[t[0]])) > 1e-10]
    geo.add(Part(material, P, N, V(UV), fix_winding(P, N, V(keep))), tags)
    if cap_top and prof[-1][0] > 1e-3:
        r, h = prof[-1]
        c = base + d * h
        cu, cv, cr = WOOD_DISCS[0] if material.startswith("BaseWood") else ((u0 + u1) / 2, (v0 + v1) / 2,
                                                                              min(u1 - u0, v1 - v0) / 2)
        cp, cuv = [c], [(cu, cv)]
        for k in range(sides):
            a = 2 * math.pi * k / sides
            cp.append(c + (s * math.cos(a) + u * math.sin(a)) * r)
            cuv.append((cu + cr * math.cos(a), cv + cr * math.sin(a)))
        cP = V(cp)
        cN = np.tile(d, (len(cP), 1))
        ct = V([(0, 1 + k, 1 + (k + 1) % sides) for k in range(sides)])
        geo.add(Part(material, cP, cN, V(cuv), fix_winding(cP, cN, ct)), tags)


def jar(geo, base, h=0.32, r=0.13, material=EARTH, lid=True, tags=()):
    """A glazed storage jar (pickles, water): fat belly, narrow neck; earthen or iron."""
    prof = [(0.0, 0.0), (r * 0.65, 0.0), (r, h * 0.35), (r * 0.95, h * 0.62), (r * 0.6, h * 0.86), (r * 0.62, h)]
    lathe(geo, prof, base, 6, material, uv_region=(0.05, 0.05, 0.95, 0.95), tags=tags)
    if lid:
        lathe(geo, [(r * 0.7, 0), (r * 0.66, 0.03), (0.0, 0.065)], V(base) + V([0, h, 0]), 6, TIMBER,
              tags=tags, cap_top=False)


def barrel(geo, base, h=0.4, r=0.16, material=BAMBOO_GOLD, hoops=2, tags=()):
    prof = [(0.0, 0.0), (r * 0.9, 0.0), (r, h * 0.5), (r * 0.9, h)]
    lathe(geo, prof, base, 8, TIMBER, tags=tags, strips=[WOOD_BLOCK])
    for k in range(hoops):
        y = h * (0.2 + 0.6 * k / max(hoops - 1, 1))
        rr = r * (0.9 + 0.1 * math.sin(math.pi * y / h)) + 0.01
        lathe(geo, [(rr, y - 0.025), (rr + 0.006, y), (rr, y + 0.025)], base, 8, material, tags=tags, cap_top=False)


def basket(geo, base, h=0.22, r=0.16, material="IrregularPlanks_LightBrown.Folktails", tags=()):
    prof = [(0.0, 0.0), (r * 0.7, 0.0), (r, h), (r * 0.9, h * 0.4)]
    lathe(geo, prof, base, 6, material, uv_region=(0.05, 0.05, 0.95, 0.95), tags=tags, cap_top=False)


def lantern(geo, at, r=0.09, h=0.2, hanging=True, tags=()):
    """A red paper lantern: glowing round body (window paper glows at night), red caps, a tassel."""
    at = V(at, float)
    body = [(r * 0.62, 0.0), (r, h * 0.3), (r, h * 0.7), (r * 0.62, h)]
    lathe(geo, body, at - V([0, h, 0]) if hanging else at, 6, WINDOWS, uv_region=(0.80, 0.03, 0.95, 0.20),
          tags=set(tags) | {"glow"}, cap_top=False)
    # red paper: the glowing window paper tinted by vertex colour (red by day, warm red glow by night)
    geo.parts[-1].C = np.tile([0.95, 0.42, 0.3, 1.0], (len(geo.parts[-1].P), 1))
    for k, y in enumerate(((0.03, -0.0), (h - 0.03, h + 0.005))):
        base = (at - V([0, h, 0]) if hanging else at) + V([0, y[0], 0])
        # red rings capping the body; closed on the outside so neither end shows a hole
        lathe(geo, [(r * 0.64, 0), (r * 0.64, y[1] - y[0])], base, 6, DETAILS,
              uv_region=DET_RED, tags=tags, cap_top=True)
    if hanging:
        beam(geo, at, at + V([0, 0.08, 0]), w=0.012, material=DETAILS, tags=tags)


def lantern_string(geo, a, b, n=4, sag=0.12, tags=()):
    """A rope with n small lanterns hanging along its sag."""
    a, b = V(a, float), V(b, float)
    pts = [a + (b - a) * (i / 8) - V([0, sag * math.sin(math.pi * i / 8), 0]) for i in range(9)]
    tube(geo, pts, [0.01] * 9, DETAILS, sides=3, strips=[DET_ROPE], caps=False, tags=tags)
    for i in range(n):
        t = (i + 1) / (n + 1)
        p = a + (b - a) * t - V([0, sag * math.sin(math.pi * t), 0])
        lantern(geo, p, r=0.05, h=0.1, tags=tags)


def cloth(geo, corners, material=DETAILS, region=DET_CLOTH, sag=0.06, nu=4, nv=3, tags=(), wave=0.02):
    """A sagging cloth (awning, banner) between four corners, both sides."""
    c = [V(p, float) for p in corners]
    P, UV, T = [], [], []
    for j in range(nv + 1):
        for i in range(nu + 1):
            s, t = i / nu, j / nv
            p = (c[0] * (1 - s) + c[1] * s) * (1 - t) + (c[3] * (1 - s) + c[2] * s) * t
            p = p - V([0, sag * math.sin(math.pi * s) * math.sin(math.pi * t) * 1.0, 0]) + \
                V([0, 0, 0]) + np.cross(c[1] - c[0], c[3] - c[0]) / max(np.linalg.norm(np.cross(c[1] - c[0], c[3] - c[0])), 1e-9) * wave * math.sin(3 * s + 2 * t)
            P.append(p)
            UV.append((region[0] + (region[2] - region[0]) * s, region[1] + (region[3] - region[1]) * t))
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            T += [(a, a + 1, a + nu + 2), (a, a + nu + 2, a + nu + 1)]
    P = V(P)
    T = V(T)
    n = np.cross(c[1] - c[0], c[3] - c[0])
    n /= np.linalg.norm(n)
    N = np.tile(n, (len(P), 1))
    geo.add(Part(material, P, N, V(UV), fix_winding(P, N, T)), tags)
    geo.add(Part(material, P.copy(), -N, V(UV), fix_winding(P, -N, T[:, ::-1])), tags)


def stones(geo, x0, z0, x1, z1, y=0.0, size=0.16, h=0.12, gap=0.02, ring=True, tags=(), tone=(0.62, 0.62, 0.6),
           skip=0.0):
    """River stones laid along the rectangle's edge (ring) or filling it: chunky irregular low boxes, grey-blue,
    each a little different. Plaster_White + vertex colour = stone colour."""
    pts = []
    if ring:
        for (ax, az, bx, bz) in ((x0, z0, x1, z0), (x1, z0, x1, z1), (x1, z1, x0, z1), (x0, z1, x0, z0)):
            L = math.hypot(bx - ax, bz - az)
            n = max(1, int(L / (size + gap)))
            for i in range(n):
                t = (i + 0.5) / n
                pts.append((ax + (bx - ax) * t, az + (bz - az) * t, math.atan2(bz - az, bx - ax)))
    else:
        nx, nz = max(1, int((x1 - x0) / (size + gap))), max(1, int((z1 - z0) / (size + gap)))
        for i in range(nx):
            for j in range(nz):
                pts.append((x0 + (i + 0.5) * (x1 - x0) / nx + geo.jitter(gap), z0 + (j + 0.5) * (z1 - z0) / nz, 0))
    for (px, pz, ang) in pts:
        sx = size * (0.5 + geo.rng.uniform(0, 0.12)) * 1.15
        sz = size * (0.42 + geo.rng.uniform(0, 0.1))
        hh = h * (0.8 + geo.rng.uniform(0, 0.4))
        R = rot_axis((0, 1, 0), -ang + geo.jitter(0.25))
        before = len(geo.parts)
        if skip and geo.rng.uniform() < skip:
            continue
        box(geo, (-sx, 0, -sz), (sx, hh, sz), PLASTER, (0.1, 0.1, 0.9, 0.9), R=R, t=(px, y, pz), jitter=0.025,
            tags=set(tags) | {"stone"}, skip=(3,))
        p = geo.parts[-1]
        # bevel-ish: pull the top face in
        top = p.P[:, 1] > y + hh * 0.5
        cen = p.P[top].mean(0)
        p.P[top] = cen + (p.P[top] - cen) * 0.78
        p.N = p.N + V([0, 0.35, 0])
        p.N /= np.linalg.norm(p.N, axis=1, keepdims=True)
        k = geo.rng.uniform(0.82, 1.08)
        tint = V(tone) * k * V([1 + geo.jitter(0.04), 1, 1 + geo.jitter(0.05)])
        p.C = np.tile(np.append(np.clip(tint, 0, 1), 1.0), (len(p.P), 1))
        assert len(geo.parts) == before + 1


def plinth(geo, x0, z0, x1, z1, h=0.14, tags=()):
    """A rammed-earth platform under a building, edged with river stones."""
    box(geo, (x0, 0, z0), (x1, h, z1), EARTH, (0.02, 0.02, 0.98, 0.98), tags=set(tags) | {"base"}, skip=(3,))
    stones(geo, x0 + 0.04, z0 + 0.04, x1 - 0.04, z1 - 0.04, y=-0.02, size=0.3, h=h * 0.9, tags=set(tags) | {"base"},
           skip=0.35)


def stairs(geo, a, b, width=0.5, steps=4, material=TIMBER, tags=()):
    """Plank steps from a (bottom front) to b (top back) with two stringers."""
    a, b = V(a, float), V(b, float)
    d = b - a
    flat = V([d[0], 0, d[2]])
    flat /= np.linalg.norm(flat)
    side = np.cross([0, 1, 0], flat)
    for sg in (-1, 1):
        o = side * sg * width / 2
        beam(geo, a + o, b + o, w=0.05, h=0.09, material=material, tags=tags)
    for i in range(steps):
        t = (i + 0.5) / steps
        p = a + d * t
        beam(geo, p - side * width / 2, p + side * width / 2, w=0.13, h=0.03, material=material, tags=tags)


def ladder(geo, a, b, width=0.3, rungs=5, material=BAMBOO_GOLD, tags=()):
    a, b = V(a, float), V(b, float)
    d = b - a
    flat = V([d[0], 0, d[2]])
    if np.linalg.norm(flat) < 1e-6:
        flat = V([0, 0, 1.0])
    flat /= np.linalg.norm(flat)
    side = np.cross([0, 1, 0], flat)
    for sg in (-1, 1):
        pole(geo, a + side * sg * width / 2, b + side * sg * width / 2, r=0.022, material=material, tags=tags,
             bend=0.005)
    for i in range(rungs):
        p = a + d * (i + 0.7) / (rungs + 0.4)
        pole(geo, p - side * width / 2, p + side * width / 2, r=0.014, material=material, sides=5, tags=tags,
             bend=0.0, caps=False)


def wheel(geo, center, axis, radius, width=0.3, spokes=8, rim_r=0.035, material=BAMBOO_GOLD, buckets=0,
          bucket_material=BAMBOO_GREEN, tags=(), node=None, paddles=0, paddle_depth=0.3,
          paddle_material="IrregularPlanks_LightBrown.Folktails"):
    """A bamboo wheel: two rims, spokes from a hub, cross-bars; optional tube buckets (bamboo sections lashed to
    the rim at an angle, open end up on the rising side) for a scoop wheel."""
    c = V(center, float)
    ax = V(axis, float)
    ax /= np.linalg.norm(ax)
    F = frame_from(ax)
    s, u = F[:, 0], F[:, 1]
    segs = 14 if radius > 0.8 else 10
    for side in (-1, 1):
        off = ax * side * width / 2
        ring = [c + off + (s * math.cos(2 * math.pi * k / segs) + u * math.sin(2 * math.pi * k / segs)) * radius
                for k in range(segs + 1)]
        tube(geo, ring, [rim_r] * len(ring), material, sides=5, caps=False, tags=tags)
        for k in range(spokes):
            a = 2 * math.pi * (k + 0.5 * (side > 0)) / spokes
            p = c + off * 0.9 + (s * math.cos(a) + u * math.sin(a)) * (radius * 0.98)
            pole(geo, c + off * 0.5, p, r=rim_r * 0.7, material=material, sides=5, bend=0.01, tags=tags, caps=False)
    # hub
    tube(geo, [c - ax * (width / 2 + 0.12), c + ax * (width / 2 + 0.12)], [0.07, 0.07], TIMBER, sides=8, tags=tags)
    # cross bars / paddles between the rims
    for k in range(spokes * 2):
        a = 2 * math.pi * k / (spokes * 2)
        radial = s * math.cos(a) + u * math.sin(a)
        p = c + radial * radius
        has_paddle = paddles and k % max(1, (spokes * 2) // paddles) == (1 if (spokes * 2) // paddles > 1 else 0)
        if not has_paddle:      # a paddle is its own cross-member; bars everywhere read as a cage
            beam(geo, p - ax * width / 2, p + ax * width / 2, w=0.04, h=0.04, material=TIMBER, tags=tags)
        if has_paddle:
            a_ = c + radial * (radius + 0.04)
            b_ = c + radial * (radius - paddle_depth)
            panel(geo, [b_ - ax * width * 0.55, b_ + ax * width * 0.55, a_ + ax * width * 0.55, a_ - ax * width * 0.55],
                  paddle_material, both=True, tags=tags)
        if buckets and k % max(1, (spokes * 2) // buckets) == 0:
            tang = np.cross(ax, radial)
            bc = p + radial * 0.07
            tube(geo, [bc - tang * 0.13 + radial * 0.04, bc + tang * 0.13 - radial * 0.02], [0.06, 0.055],
                 bucket_material, sides=6, caps=True, tags=tags)
            lashing(geo, bc, tang, r=0.062, tags=tags)


def channel(geo, z0, z1, y_floor, x_center=0.5, r_in=0.36, wall=0.045, material=BAMBOO_GREEN, around=7, rim_y=None,
            sleeve=True, tags=(), tilt=0.0):
    """An open flume channel: a split giant bamboo (half-pipe) running along z from z0 to z1 (or along x), its inner
    floor at y_floor (the water cell's floor, so water shows from its first centimetre), rims flattened on top, and a
    lashed sleeve at the upstream end (z0) so a run of pieces reads as nested in the direction of flow. tilt raises
    the upstream end (for drops and spouts). Build along z; rotate the Geo for other directions."""
    def P(t, ang, r):
        z = z0 + (z1 - z0) * t
        y = y_floor + r_in + tilt * (1 - t) + math.sin(ang) * r
        x = x_center + math.cos(ang) * r
        return V([x, y, z])
    rim = (rim_y - y_floor - r_in) / r_in if rim_y is not None else 0.0
    a0 = math.pi - math.asin(max(-1.0, min(1.0, rim)))
    a_start, a_end = a0, 3 * math.pi - a0   # from the left rim, under, to the right rim
    angs = [a_start + (a_end - a_start) * k / around for k in range(around + 1)]
    strip = _pick(geo, WOOD_STRIPS)
    L = abs(z1 - z0)
    vlen = min(L * TEXEL, strip[3] - strip[1])
    for r, sgn in ((r_in + wall, 1), (r_in, -1)):
        Pp, Nn, UV, T = [], [], [], []
        for ti, t in enumerate((0.0, 1.0)):
            for k, a in enumerate(angs):
                Pp.append(P(t, a, r))
                Nn.append(V([math.cos(a), math.sin(a), 0.0]) * sgn)
                UV.append((strip[0] + (strip[2] - strip[0]) * k / around, strip[1] + vlen * t))
        m_ = around + 1
        for k in range(around):
            T += [(k, k + 1, m_ + k + 1), (k, m_ + k + 1, m_ + k)]
        Pp, Nn = V(Pp), V(Nn)
        geo.add(Part(material, Pp, Nn, V(UV), fix_winding(Pp, Nn, V(T))), tags)
    # flat rims along both edges
    for a in (a_start, a_end):
        q = [P(0, a, r_in), P(0, a, r_in + wall), P(1, a, r_in + wall), P(1, a, r_in)]
        n = V([0, 1.0, 0])
        geo.add(quad_part(material, q, uvs=V([[strip[0], strip[1]], [strip[0] + 0.02, strip[1]],
                                              [strip[0] + 0.02, strip[1] + vlen], [strip[0], strip[1] + vlen]]),
                          normal=n), tags)
    # end faces (the cut culm wall) at both ends
    for t, nz in ((0.0, -1.0), (1.0, 1.0)):
        Pp, UV, T = [], [], []
        for k, a in enumerate(angs):
            Pp += [P(t, a, r_in), P(t, a, r_in + wall)]
            UV += [(0.03, 0.03), (0.06, 0.06)]
        for k in range(around):
            b = 2 * k
            T += [(b, b + 2, b + 3), (b, b + 3, b + 1)]
        Pp = V(Pp)
        Nn = np.tile(V([0, 0, nz * (1 if z1 > z0 else -1)]), (len(Pp), 1))
        geo.add(Part(material, Pp, Nn, V(UV), fix_winding(Pp, Nn, V(T))), tags)
    if sleeve:
        ring = (0.0, 0.1 / max(L, 1e-6))
        Pp, Nn, UV, T = [], [], [], []
        for ti, t in enumerate(ring):
            for k, a in enumerate(angs):
                Pp.append(P(t, a, r_in + wall + 0.022))
                Nn.append(V([math.cos(a), math.sin(a), 0.0]))
                UV.append((DET_ROPE[0] + (DET_ROPE[2] - DET_ROPE[0]) * (k % 2), DET_ROPE[1] + 0.05 * ti))
        m_ = around + 1
        for k in range(around):
            T += [(k, k + 1, m_ + k + 1), (k, m_ + k + 1, m_ + k)]
        Pp, Nn = V(Pp), V(Nn)
        geo.add(Part(DETAILS, Pp, Nn, V(UV), fix_winding(Pp, Nn, V(T))), tags)


def cradle(geo, z, y_top, x0=0.08, x1=0.92, material=TIMBER, legs=True, tags=()):
    """A timber saddle under a flume: a cross-beam with two short stakes."""
    beam(geo, (x0, y_top - 0.04, z), (x1, y_top - 0.04, z), w=0.07, h=0.06, material=material, tags=tags)
    if legs:
        for x in (x0 + 0.05, x1 - 0.05):
            beam(geo, (x, y_top - 0.07, z), (x, -0.02, z), w=0.06, material=material, tags=tags, caps="start")


def gable_end(geo, x, z0, z1, y_eave, y_ridge, outward=-1, infill=PLASTER_LATH, sag=0.07, post=0.08, tags=()):
    """The triangle under a gable at x (facing -x if outward=-1): lime-plaster infill with a king post, a tie beam
    and two struts in dark timber, the typical Sichuan chuan-dou frame showing on the gable."""
    zm = (z0 + z1) / 2
    n = V([outward, 0, 0.0])
    xi = x - outward * 0.02
    a, b, c = V([xi, y_eave, z0]), V([xi, y_eave, z1]), V([xi, y_ridge - 0.04, zm])
    P = V([a, b, c])
    uv = V([[0.05, 0.05], [0.05 + (z1 - z0) * TEXEL * 0.5, 0.05], [0.05 + (zm - z0) * TEXEL * 0.5,
                                                                   0.05 + (y_ridge - y_eave) * TEXEL * 0.5]])
    N = np.tile(n, (3, 1))
    geo.add(Part(infill, P, N, np.clip(uv, 0, 1), fix_winding(P, N, V([[0, 1, 2]]))), tags)
    xf = x + outward * 0.01
    with geo.tagged(*tags, "frame"):
        beam(geo, (xf, y_eave, z0 - 0.03), (xf, y_eave, z1 + 0.03), w=post, material=TIMBER, caps=False)
        beam(geo, (xf, y_eave, zm), (xf, y_ridge - 0.02, zm), w=post * 0.9, material=TIMBER, caps=False)
    for zz in (z0 + (zm - z0) * 0.5, z1 - (z1 - zm) * 0.5):
        yt = y_eave + (y_ridge - y_eave) * 0.5 - sag * 0.5
        beam(geo, (xf, y_eave, zz), (xf, yt, zz), w=post * 0.7, material=TIMBER, tags=tags, caps=False)


def chilli_string(geo, top, length=0.45, n=7, tags=()):
    """A string of dried red chillies hanging from an eave: a rope with small red pods (Sichuan farmhouse charm,
    one of the few places red belongs)."""
    top = V(top, float)
    beam(geo, top, top - V([0, length, 0]), w=0.012, material=DETAILS, caps=False, tags=tags)
    for i in range(n):
        y = 0.06 + (length - 0.08) * i / max(n - 1, 1)
        a = 2.4 * i
        c = top - V([0, y, 0]) + V([math.cos(a), 0, math.sin(a)]) * 0.025
        tip = c + V([math.cos(a) * 0.02, -0.07, math.sin(a) * 0.02])
        tube(geo, [c, tip], [0.024, 0.006], DETAILS, sides=3, strips=[DET_RED], caps="start", tags=tags)


def gear(geo, center, axis, radius, teeth=12, width=0.08, tooth=0.06, material=TIMBER, tags=()):
    """A wooden cog wheel: a thick disc with square pegs round its rim (lantern-gear style), on its axis."""
    c, ax = V(center, float), V(axis, float)
    ax /= np.linalg.norm(ax)
    lathe(geo, [(0.0, -width / 2), (radius, -width / 2), (radius, width / 2), (0.0, width / 2)], c - ax * 0.0, 10,
          material, axis=ax, tags=tags, strips=[WOOD_BLOCK])
    F = frame_from(ax)
    for k in range(teeth):
        a = 2 * math.pi * k / teeth
        radial = F[:, 0] * math.cos(a) + F[:, 1] * math.sin(a)
        p = c + radial * (radius + tooth / 2)
        beam(geo, p - radial * tooth / 2, p + radial * tooth / 2, w=tooth * 0.8, h=width * 0.9, material=material,
             up=ax, tags=tags, caps="end")


def standing_lantern(geo, base, h=0.75, tags=()):
    """A lantern on a post: a river-stone foot, a timber post, a crossbar with the lantern hanging from it."""
    b = V(base, float)
    stones(geo, b[0] - 0.08, b[2] - 0.08, b[0] + 0.08, b[2] + 0.08, y=b[1], size=0.16, h=0.08, ring=False, tags=tags)
    beam(geo, b, b + V([0, h, 0]), w=0.05, tags=tags, caps="end")
    beam(geo, b + V([0, h - 0.04, 0]), b + V([0.18, h - 0.04, 0]), w=0.03, tags=tags)
    lantern(geo, b + V([0.16, h - 0.06, 0]), r=0.06, h=0.14, tags=tags)


def screen(geo, a, b, y0, y1, material="IrregularPlanks_LightBrown.Folktails", frame=BAMBOO_GOLD, tags=()):
    """A woven bamboo screen in a bamboo frame between two posts, both faces."""
    a, b = V([a[0], 0, a[1]], float), V([b[0], 0, b[1]], float)
    up = V([0, 1.0, 0])
    panel(geo, [a + up * y0, b + up * y0, b + up * y1, a + up * y1], material, both=True, tags=tags)
    for p in (a, b):
        pole(geo, p + up * (y0 - 0.02), p + up * (y1 + 0.04), r=0.025, material=frame, sides=5, bend=0.0, tags=tags)
    for y in (y0, y1):
        pole(geo, a + up * y, b + up * y, r=0.016, material=frame, sides=4, bend=0.0, tags=tags, caps=False)


def round_roof(geo, center, radius, y_eave, y_apex, sides=8, sag=0.06, thick=0.06, tags=()):
    """A round (many-sided) tiled roof rising to a point with a little finial: kiosks, pavilions, well houses."""
    c = V(center, float)
    apex = c + V([0, y_apex, 0])
    lift = lambda s: 0.03 * abs(2 * s - 1) ** 2  # noqa: E731
    for k in range(sides):
        a0, a1 = 2 * math.pi * k / sides, 2 * math.pi * (k + 1) / sides
        e0 = c + V([math.cos(a0) * radius, y_eave, math.sin(a0) * radius])
        e1 = c + V([math.cos(a1) * radius, y_eave, math.sin(a1) * radius])
        _tile_patch(geo, e1, e0, apex, apex, max(2, int(radius / 0.3)), 2, sag, lift, thick, tags=tags,
                    col_offset=2 * k)
    lathe(geo, [(0.0, 0.0), (0.07, 0.0), (0.08, 0.05), (0.05, 0.11), (0.06, 0.14), (0.0, 0.16)], apex - V([0, 0.03, 0]),
          6, TILE, uv_region=(0.0, TILE_COURSES[1][0], 0.25, TILE_COURSES[1][1]), tags=tags)


def moon_window(geo, center, normal, r=0.3, tags=()):
    """The Ringtail buildings' mark: a round 'moon' window, the glowing round cracked-ice light in a white lime disc
    with a dark timber ring, set flat on a wall facing `normal`."""
    c, n = V(center, float), V(normal, float)
    n = n / np.linalg.norm(n)
    F = frame_from(n)
    before = len(geo.parts)
    lathe(geo, [(r * 1.25, 0.0), (0.0, 0.0)], (0, 0, 0), 14, PLASTER, uv_region=(0.1, 0.1, 0.9, 0.9), cap_top=False,
          tags=tags)
    lathe(geo, [(r * 0.92, 0.0), (r * 0.94, 0.04), (r * 1.06, 0.03), (r * 1.04, 0.0)], (0, 0, 0), 14, TIMBER,
          cap_top=False, tags=tags)
    M = np.stack([F[:, 0], n, F[:, 1]], 0)       # lathe x -> side, lathe y (height) -> out of the wall, lathe z -> up
    for p in geo.parts[before:]:
        p.P = c + p.P @ M + n * 0.004
        p.N = p.N @ M
        p.T = fix_winding(p.P, p.N, p.T)
    u0, v0, u1, v1 = WIN_ROUND
    k = 12
    P = [c + n * 0.008]
    UV = [((u0 + u1) / 2, (v0 + v1) / 2)]
    for i in range(k):
        a = 2 * math.pi * i / k
        P.append(c + (F[:, 0] * math.cos(a) + F[:, 1] * math.sin(a)) * r * 0.93 + n * 0.008)
        UV.append(((u0 + u1) / 2 + (u1 - u0) / 2 * 0.96 * math.cos(a), (v0 + v1) / 2 + (v1 - v0) / 2 * 0.96 * math.sin(a)))
    P = V(P)
    N = np.tile(n, (len(P), 1))
    T = V([(0, 1 + i, 1 + (i + 1) % k) for i in range(k)])
    geo.add(Part(WINDOWS, P, N, V(UV), fix_winding(P, N, T)), set(tags) | {"glow"})
