"""Procedural line-art icons in Timberborn's UI style.

Vanilla goods, building and plant icons are flat line drawings: one gold ink colour, a black drop shadow straight
below, transparent background (see docs/tech/icons.md for the measurements). This module draws such icons from code.

An icon is a function that draws on an `Icon` with a few path helpers, back to front:

    def tofu(c):
        c.shape(rrect(0, 20, 60, 40, 6))       # closed outline; hides whatever was drawn behind it
        c.stroke(line((10, 30), (50, 30)))      # open stroke
        c.dot(30, 45)                           # small solid dot

Geometry is in free "units" (design in a ~100 x 100 box, y down). The renderer fits the drawing to the canvas, so
units only need to be consistent within one icon. Pen widths are in output pixels and do not scale with the drawing:
the style decides them, so every icon gets the same line weight as the vanilla set.

Only numpy and Pillow are used (venv python). Rendering is 8x supersampled, then box-filtered down.
"""
from __future__ import annotations

import hashlib
import math
from contextlib import contextmanager
from dataclasses import dataclass, field

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


# ------------------------------------------------------------------------------------------------------ paths

@dataclass
class Path:
    pts: np.ndarray            # (N, 2) in drawing units
    closed: bool = False

    def __add__(self, other: "Path") -> "Path":
        """Concatenate two open paths into one (the second continues from the first)."""
        return Path(np.vstack([self.pts, other.pts]), False)

    def reversed(self) -> "Path":
        return Path(self.pts[::-1].copy(), self.closed)

    def close(self) -> "Path":
        return Path(self.pts, True)

    def moved(self, dx, dy) -> "Path":
        return Path(self.pts + (dx, dy), self.closed)

    def scaled(self, sx, sy=None, about=(0, 0)) -> "Path":
        sy = sx if sy is None else sy
        a = np.asarray(about, float)
        return Path((self.pts - a) * (sx, sy) + a, self.closed)

    def rotated(self, deg, about=(0, 0)) -> "Path":
        """Rotate counter-clockwise on screen by `deg` degrees."""
        t = math.radians(-deg)
        r = np.array([[math.cos(t), -math.sin(t)], [math.sin(t), math.cos(t)]])
        a = np.asarray(about, float)
        return Path((self.pts - a) @ r.T + a, self.closed)


def _as_path(p) -> Path:
    if isinstance(p, Path):
        return p
    return Path(np.asarray(p, float))


def line(*pts) -> Path:
    """Straight polyline through the given (x, y) points."""
    return Path(np.asarray(pts, float))


def poly(*pts) -> Path:
    """Closed straight polygon."""
    return Path(np.asarray(pts, float), True)


def _catmull(p0, p1, p2, p3, n):
    t = np.linspace(0, 1, n, endpoint=False)[:, None]
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)


def spline(*pts, closed=False) -> Path:
    """Smooth Catmull-Rom curve through the points (the most convenient way to draw organic shapes)."""
    p = np.asarray(pts, float)
    if closed:
        q = np.vstack([p[-1:], p, p[:2]])
        segs = range(len(p))
    else:
        q = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
        segs = range(len(p) - 1)
    out = []
    for i in segs:
        n = max(4, int(np.linalg.norm(q[i + 2] - q[i + 1]) * 1.5))
        out.append(_catmull(q[i], q[i + 1], q[i + 2], q[i + 3], n))
    if not closed:
        out.append(p[-1:])
    return Path(np.vstack(out), closed)


def bez(p0, c0, c1, p1, n=40) -> Path:
    """Cubic Bezier from p0 to p1 with control points c0, c1."""
    t = np.linspace(0, 1, n)[:, None]
    p0, c0, c1, p1 = (np.asarray(v, float) for v in (p0, c0, c1, p1))
    return Path((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * c0 + 3 * (1 - t) * t * t * c1 + t ** 3 * p1)


def ellipse(cx, cy, rx, ry=None, rot=0.0, a0=0.0, a1=360.0, n=None) -> Path:
    """Ellipse or elliptic arc. Angles in degrees, 0 = right, 90 = up (screen). Full turn -> closed path."""
    ry = rx if ry is None else ry
    full = abs(a1 - a0) >= 360
    if n is None:
        n = max(12, int(abs(a1 - a0) / 360 * (rx + ry) * 2.5))
    a = np.radians(np.linspace(a0, a1, n, endpoint=not full))
    x, y = rx * np.cos(a), -ry * np.sin(a)
    t = math.radians(-rot)
    pts = np.stack([cx + x * math.cos(t) - y * math.sin(t), cy + x * math.sin(t) + y * math.cos(t)], 1)
    return Path(pts, full)


def circle(cx, cy, r, n=None) -> Path:
    return ellipse(cx, cy, r, r, n=n)


def arc(cx, cy, r, a0, a1, ry=None, rot=0.0) -> Path:
    return ellipse(cx, cy, r, ry, rot, a0, a1)


def rrect(x, y, w, h, r=0.0) -> Path:
    """Rounded rectangle, top-left (x, y)."""
    r = min(r, w / 2, h / 2)
    if r <= 0:
        return poly((x, y), (x + w, y), (x + w, y + h), (x, y + h))
    parts = [arc(x + w - r, y + r, r, 90, 0), arc(x + w - r, y + h - r, r, 0, -90),
             arc(x + r, y + h - r, r, -90, -180), arc(x + r, y + r, r, 180, 90)]
    return Path(np.vstack([p.pts for p in parts]), True)


def inside(region: Path, pts: np.ndarray) -> np.ndarray:
    """Boolean mask: which points lie inside the closed region (even-odd rule)."""
    poly = region.pts
    x, y = pts[:, 0][:, None], pts[:, 1][:, None]
    x0, y0 = poly[:, 0][None, :], poly[:, 1][None, :]
    x1, y1 = np.roll(poly[:, 0], -1)[None, :], np.roll(poly[:, 1], -1)[None, :]
    cond = (y0 > y) != (y1 > y)
    with np.errstate(divide="ignore", invalid="ignore"):
        xc = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
    return (cond & (x < xc)).sum(1) % 2 == 1


def clip(path: Path, region: Path, margin: float = 0.0) -> list:
    """The parts of `path` that lie inside `region` (optionally `margin` units away from its edge)."""
    p = _as_path(path)
    pts = p.pts if not p.closed else np.vstack([p.pts, p.pts[:1]])
    fine = []
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(2, int(np.linalg.norm(b - a) / 0.5))
        fine.append(np.linspace(a, b, n, endpoint=False))
    fine.append(pts[-1:])
    fine = np.vstack(fine)
    ok = inside(region, fine)
    if margin > 0:
        rp = region.pts
        d = np.min(np.linalg.norm(fine[:, None, :] - rp[None, :, :], axis=2), axis=1)
        ok &= d > margin
    out, run = [], []
    for q, k in zip(fine, ok):
        if k:
            run.append(q)
        elif run:
            if len(run) > 2:
                out.append(Path(np.asarray(run)))
            run = []
    if len(run) > 2:
        out.append(Path(np.asarray(run)))
    return out


def hatch(region: Path, spacing: float, angle: float, margin: float = 0.0, offset: float = 0.0) -> list:
    """Parallel lines at `angle` degrees, `spacing` units apart, clipped to the region."""
    lo, hi = region.pts.min(0), region.pts.max(0)
    c = (lo + hi) / 2
    rad = np.linalg.norm(hi - lo) / 2 + spacing
    a = math.radians(-angle)
    d = np.array([math.cos(a), math.sin(a)])
    n = np.array([-d[1], d[0]])
    out = []
    k = -rad + offset % spacing
    while k <= rad:
        p0, p1 = c + n * k - d * rad, c + n * k + d * rad
        out.extend(clip(Path(np.stack([p0, p1])), region, margin))
        k += spacing
    return out


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


# ------------------------------------------------------------------------------------------------------ style

@dataclass
class Style:
    """Everything that makes an icon look vanilla. Measured from the game's own sprites (docs/tech/icons.md)."""
    name: str
    canvas: int                    # texture size in px (square)
    extent: float                  # longest side of the ink (without shadow), px, for a squarish drawing
    extent_tall: float             # ... for a drawing with aspect 1:2 or thinner (interpolated in between)
    pen: float                     # base stroke width, px
    ink: tuple                     # RGB of the line colour
    shadow_dy: float               # shadow offset straight down, px
    shadow_grow: float             # shadow dilation, px
    shadow_blur: float = 0.0       # gaussian blur radius of the shadow, px
    shadow_alpha: float = 1.0
    wobble: float = 0.0            # amplitude of hand-drawn wobble, px
    width_jitter: float = 0.0      # relative stroke-width variation along a line
    taper: float = 0.0             # 0 = round pen of constant width; 1 = brush strokes thinning to a point
    center_dy: float = 0.0         # vertical placement of the ink box centre, px from canvas centre (+ = down)


GOODS = Style("goods", canvas=80, extent=64, extent_tall=72, pen=3.5, ink=(202, 172, 107),
              shadow_dy=2.5, shadow_grow=0.5, wobble=0.22, width_jitter=0.06, center_dy=-1.5)

# Plant (planting tool) and building icons are drawn with a pen: thinner, slightly tapered and wobbly strokes,
# paler ink, a faint soft shadow. Plants sit low (ground lines at the bottom); buildings are smaller in the frame.
PLANT = Style("plant", canvas=112, extent=92, extent_tall=98, pen=2.8, ink=(187, 161, 108),
              shadow_dy=1.5, shadow_grow=0.5, shadow_blur=1.8, shadow_alpha=0.5, wobble=0.45,
              width_jitter=0.16, taper=0.5, center_dy=5.0)
BUILDING = Style("building", canvas=112, extent=82, extent_tall=92, pen=3.0, ink=(187, 161, 108),
                 shadow_dy=1.5, shadow_grow=0.5, shadow_blur=1.8, shadow_alpha=0.5, wobble=0.45,
                 width_jitter=0.16, taper=0.5, center_dy=-1.0)

# Faction logo (FactionSpec.Logo): one flat colour, diamond frame, solid emblem, 98 px.
LOGO = Style("logo", canvas=98, extent=66, extent_tall=66, pen=6.0, ink=(132, 214, 160),
             shadow_dy=1.0, shadow_grow=0.5, shadow_blur=1.0, shadow_alpha=0.45)


# ------------------------------------------------------------------------------------------------------ icon

@dataclass
class Op:
    kind: str                      # stroke | shape | fill | erase | erase_stroke
    pts: np.ndarray
    closed: bool
    w: float = 1.0                 # pen multiplier
    occlude: bool = True
    filled: bool = False
    halo: float = 0.0              # extra px erased around a stroke/shape before drawing it
    taper: float | None = None


@dataclass
class Icon:
    """A drawing: a list of operations in drawing units, plus framing hints."""
    name: str = ""
    ops: list = field(default_factory=list)
    extent: float | None = None    # override the style's ink extent (px)
    nudge: tuple = (0.0, 0.0)      # optical-centre correction, px
    _m: np.ndarray = field(default_factory=lambda: np.eye(3))

    # -- transforms ------------------------------------------------------------------------------------------
    @contextmanager
    def at(self, x=0.0, y=0.0, s=1.0, rot=0.0, sx=None, sy=None):
        """Draw the block in a moved / rotated (degrees, counter-clockwise) / scaled frame."""
        sx = s if sx is None else sx
        sy = s if sy is None else sy
        t = math.radians(-rot)
        m = np.array([[math.cos(t) * sx, -math.sin(t) * sy, x], [math.sin(t) * sx, math.cos(t) * sy, y], [0, 0, 1]])
        old = self._m
        self._m = old @ m
        try:
            yield self
        finally:
            self._m = old

    def _tf(self, p) -> tuple:
        p = _as_path(p)
        h = np.hstack([p.pts, np.ones((len(p.pts), 1))]) @ self._m.T
        return h[:, :2], p.closed

    # -- drawing ---------------------------------------------------------------------------------------------
    def stroke(self, p, w=1.0, halo=0.0, taper=None):
        """Draw a line along the path. `w` multiplies the style's pen width; `halo` (px) clears a gap around it
        first so it reads in front of what is behind."""
        pts, closed = self._tf(p)
        self.ops.append(Op("stroke", pts, closed, w, halo=halo, taper=taper))

    def shape(self, p, w=1.0, occlude=True, filled=False, halo=0.0):
        """A closed outline. By default it hides earlier ink inside it (draw back to front)."""
        pts, _ = self._tf(p)
        self.ops.append(Op("shape", pts, True, w, occlude, filled, halo))

    def fill(self, p):
        """Solid ink area (no extra outline width)."""
        pts, _ = self._tf(p)
        self.ops.append(Op("fill", pts, True))

    def erase(self, p, w=None):
        """Clear ink: inside a closed path, or along a path with pen multiplier `w`."""
        pts, closed = self._tf(p)
        if w is None:
            self.ops.append(Op("erase", pts, True))
        else:
            self.ops.append(Op("erase_stroke", pts, closed, w))

    def dot(self, x, y, r=0.62):
        """Small solid dot; `r` is the radius as a multiple of the pen width (so dots match line weight)."""
        pts, _ = self._tf(line((x, y)))
        self.ops.append(Op("dot", pts, False, r))


# ------------------------------------------------------------------------------------------------------ render

SS = 8  # supersampling factor


def _resample(pts, closed, step):
    """Even spacing along the polyline (px)."""
    if closed:
        pts = np.vstack([pts, pts[:1]])
    if len(pts) < 2:
        return pts, np.zeros(len(pts))
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    total = s[-1]
    if total < 1e-6:
        return pts[:1], np.zeros(1)
    n = max(2, int(total / step) + 1)
    t = np.linspace(0, total, n)
    x = np.interp(t, s, pts[:, 0])
    y = np.interp(t, s, pts[:, 1])
    out = np.stack([x, y], 1)
    return out, t


def _noise(t, rng, wavelength):
    """Smooth 1-D noise in [-1, 1] along arc length t."""
    v = np.zeros_like(t)
    for k in (1.0, 2.1, 4.3):
        v += np.sin(t / wavelength * k * 2 * math.pi + rng.uniform(0, 2 * math.pi)) / k
    return v / 1.6


def _normals(pts, closed):
    if len(pts) < 2:
        return np.zeros_like(pts)
    if closed:
        d = np.roll(pts, -1, 0) - np.roll(pts, 1, 0)
    else:
        d = np.gradient(pts, axis=0)
    n = np.stack([-d[:, 1], d[:, 0]], 1)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    return n / np.maximum(ln, 1e-9)


def _draw_stroke(draw, pts, radii, closed, value):
    if closed and len(pts) > 2:
        pts = np.vstack([pts, pts[:1]])
        radii = np.append(radii, radii[0])
    for i in range(len(pts) - 1):
        p, q = pts[i], pts[i + 1]
        d = q - p
        ln = math.hypot(d[0], d[1])
        if ln < 1e-6:
            continue
        n = np.array([-d[1], d[0]]) / ln
        rp, rq = radii[i], radii[i + 1]
        draw.polygon([tuple(p + n * rp), tuple(q + n * rq), tuple(q - n * rq), tuple(p - n * rp)], fill=value)
    for p, r in zip(pts, radii):
        draw.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=value)


def _ink_bounds(icon: Icon):
    pts = [op.pts for op in icon.ops if op.kind in ("stroke", "shape", "fill", "dot")]
    allp = np.vstack(pts)
    return allp.min(0), allp.max(0)


def render(icon: Icon, style: Style, seed_name: str | None = None) -> Image.Image:
    """Render to an RGBA image of style.canvas x style.canvas."""
    lo, hi = _ink_bounds(icon)
    size = hi - lo
    long_side, short_side = max(size), max(1e-6, min(size))
    aspect = short_side / long_side
    extent = icon.extent
    if extent is None:
        t = np.clip((1.0 - aspect) / 0.5, 0, 1)
        extent = style.extent + (style.extent_tall - style.extent) * t
    pen = style.pen
    scale = (extent - pen) / long_side                  # px per unit
    centre = (lo + hi) / 2
    origin = np.array([style.canvas / 2 + icon.nudge[0], style.canvas / 2 + style.center_dy + icon.nudge[1]])

    def to_px(pts):
        return ((pts - centre) * scale + origin) * SS

    N = style.canvas * SS
    ink = Image.new("L", (N, N), 0)
    draw = ImageDraw.Draw(ink)
    seed = int(hashlib.sha1((seed_name or icon.name).encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)

    def pen_line(op, value, extra_px=0.0, wmul=None):
        pts = to_px(op.pts)
        wm = op.w if wmul is None else wmul
        if op.kind == "dot":
            r = (pen * wm + extra_px * 2) * SS
            p = pts[0]
            draw.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=value)
            return
        rs, t = _resample(pts, op.closed, step=0.6 * SS)
        closed = op.closed
        if closed and len(rs) > 2:
            rs, t = rs[:-1], t[:-1]
        nrm = _normals(rs, closed)
        if style.wobble > 0 and len(rs) > 2:
            off = _noise(t, rng, 26 * SS) * style.wobble * SS
            rs = rs + nrm * off[:, None]
        base = (pen * wm / 2 + extra_px) * SS
        r = np.full(len(rs), base)
        if style.width_jitter > 0 and len(rs) > 2:
            r *= 1 + _noise(t, rng, 18 * SS) * style.width_jitter
        taper = style.taper if op.taper is None else op.taper
        if taper > 0 and not closed and len(rs) > 2:
            u = t / t[-1]
            prof = np.minimum(1, np.minimum(u, 1 - u) / 0.22)
            r *= (1 - taper) + taper * np.sqrt(np.clip(prof, 0, 1))
        _draw_stroke(draw, rs, r, closed, value)

    for op in icon.ops:
        if op.kind == "stroke":
            if op.halo:
                pen_line(op, 0, extra_px=op.halo)
            pen_line(op, 255)
        elif op.kind == "dot":
            pen_line(op, 255)
        elif op.kind == "shape":
            poly_px = [tuple(p) for p in to_px(op.pts)]
            if op.halo:
                pen_line(op, 0, extra_px=op.halo)
            if op.occlude or op.filled:
                draw.polygon(poly_px, fill=255 if op.filled else 0)
            pen_line(op, 255)
        elif op.kind == "fill":
            draw.polygon([tuple(p) for p in to_px(op.pts)], fill=255)
        elif op.kind == "erase":
            draw.polygon([tuple(p) for p in to_px(op.pts)], fill=0)
        elif op.kind == "erase_stroke":
            pen_line(op, 0)

    # shadow: the ink grown a little, moved straight down, black
    sh = ink
    grow = int(round(style.shadow_grow * SS))
    if grow > 0:
        sh = sh.filter(ImageFilter.MaxFilter(2 * grow + 1))
    dy = int(round(style.shadow_dy * SS))
    sh = sh.transform(sh.size, Image.AFFINE, (1, 0, 0, 0, 1, -dy))
    ink_s = ink.reduce(SS)
    sh_s = sh.reduce(SS)
    if style.shadow_blur > 0:
        sh_s = sh_s.filter(ImageFilter.GaussianBlur(style.shadow_blur))
    g = np.asarray(ink_s, float) / 255
    s = np.asarray(sh_s, float) / 255 * style.shadow_alpha
    a = g + s * (1 - g)
    rgb = np.zeros((style.canvas, style.canvas, 3))
    with np.errstate(invalid="ignore", divide="ignore"):
        for i in range(3):
            rgb[..., i] = np.where(a > 0, style.ink[i] * g / np.maximum(a, 1e-9), 0)
    out = np.dstack([np.clip(rgb, 0, 255), np.clip(a * 255, 0, 255)]).round().astype(np.uint8)
    return Image.fromarray(out, "RGBA")


# ------------------------------------------------------------------------------------------------------ registry

@dataclass
class IconDef:
    id: str              # output file name without "Icon.png", e.g. PandabornRice
    group: str           # output sub-folder / set name, e.g. Goods
    style: Style
    draw: object         # function(Icon) -> None
    extent: float | None = None
    nudge: tuple = (0.0, 0.0)
    note: str = ""       # what it shows; goes into the review sheet
    ship: bool = True    # False: render to the build dir only (proposals not yet wired into the mod)
    suffix: str = "Icon"  # file name = id + suffix + ".png" (vanilla: BerriesIcon; avatars have none)

    @property
    def filename(self) -> str:
        return f"{self.id}{self.suffix}.png"

    def build(self) -> Icon:
        ic = Icon(name=self.id, extent=self.extent, nudge=self.nudge)
        self.draw(ic)
        return ic

    def render(self) -> Image.Image:
        return render(self.build(), self.style)


REGISTRY: dict[str, IconDef] = {}


def icon(id, group="Goods", style=GOODS, extent=None, nudge=(0.0, 0.0), note="", ship=True, suffix="Icon"):
    """Decorator: register a drawing function as an icon."""
    def deco(fn):
        REGISTRY[f"{group}/{id}"] = IconDef(id, group, style, fn, extent, nudge,
                                            note or (fn.__doc__ or "").strip(), ship, suffix)
        return fn
    return deco


def preview(img: Image.Image, bg=(34, 53, 42), scale=1) -> Image.Image:
    """The icon on a UI-coloured background, optionally enlarged (nearest neighbour, to see pixels)."""
    base = Image.new("RGBA", img.size, bg + (255,))
    base.alpha_composite(img)
    if scale != 1:
        base = base.resize((img.width * scale, img.height * scale), Image.NEAREST)
    return base
