"""The plant atlases: one shared albedo/normal sheet (2048 px) and one detail sheet (1024 px) for all seven plants.

Regions are pixel rectangles [x0, y0, x1, y1) with y running down the image, as painted by textures.py. Models ask for
UV rectangles with `uv(name)` (u0, v0, u1, v1; v = 1 at the top of the image, so a sprite's bottom edge is v0) and for
discs with `disc(name)`. Painter and models share this file, so a moved region moves both.

Leaves are painted near-grey (value carries the shading, hue comes from the vertex colour, as the vanilla plant sheets
do); bark, culm sheaths, rice heads and pepper berries are painted in colour.
"""
MAIN = 2048
DETAIL = 1024

# --------------------------------------------------------------------------------------------- main sheet
REGIONS = {
    # strips (u across the circumference, v along the length; bottom of the strip = base of the stem)
    "culm": (0, 0, 96, 2048),              # timber bamboo culm, neutral, nodes every 160 px
    "culm_thin": (96, 0, 160, 2048),       # thin culms and branches (shoot bamboo, twigs), nodes every 96 px
    "bark": (160, 0, 256, 1024),           # persimmon bark, dark grey-brown blocks
    "pepper_stem": (160, 1024, 256, 1536),  # grey-brown thorny stem
    "sheath": (160, 1536, 256, 2048),      # bamboo shoot sheath: tan with dark speckles, green-yellow tip at the top
    # bamboo
    "bamboo_spray_a": (256, 0, 768, 512),
    "bamboo_spray_b": (768, 0, 1280, 512),
    "bamboo_spray_c": (1280, 0, 1536, 256),
    "bamboo_spray_d": (1536, 0, 1792, 256),
    "bamboo_spray_e": (1792, 0, 2048, 256),
    "bamboo_dry": (1280, 256, 1536, 512),
    "culm_discs": (1536, 256, 1792, 512),  # two discs: hollow cut culm (left), closed node (right), bottom half: sheath tip
    "twigs_dead": (1792, 256, 2048, 512),
    # persimmon
    "persimmon_leaves_a": (256, 512, 768, 1024),
    "persimmon_leaves_b": (768, 512, 1024, 768),
    "persimmon_leaves_c": (1024, 512, 1280, 768),
    "persimmon_branch": (768, 768, 1280, 1024),
    "persimmon_discs": (1792, 768, 2048, 1024),  # stump top (end grain) left, a smaller one right
    # tea
    "tea_leaves": (1280, 512, 1792, 1024),
    "tea_top": (1792, 512, 2048, 768),
    # cabbage
    "cabbage_leaf": (256, 1024, 768, 1536),
    "cabbage_young": (768, 1024, 1024, 1280),
    "withered": (1024, 1024, 1280, 1280),
    # rice
    "rice_panicle_a": (768, 1280, 1024, 1536),
    "rice_panicle_b": (1024, 1280, 1280, 1536),
    "rice_tuft_a": (1280, 1024, 1536, 1536),
    "rice_tuft_b": (1536, 1024, 1792, 1536),
    "rice_tuft_dry": (1792, 1024, 2048, 1536),
    # Sichuan pepper
    "pepper_leaves": (256, 1536, 768, 2048),
    "pepper_berries_a": (768, 1536, 1024, 1792),
    "pepper_berries_b": (1024, 1536, 1280, 1792),
    "pepper_branch": (768, 1792, 1280, 2048),
    # ground
    "soil_mound": (1280, 1536, 1536, 1792),
    "soil_mound_dry": (1280, 1792, 1536, 2048),
    "shoot_leaves": (1536, 1536, 1792, 1792),
    "seedling_sprig": (1536, 1792, 1792, 2048),
    # the Great Flowering (2026-11-14): pale straw seed plumes hanging from bamboo sprays
    "bamboo_flower_a": (1792, 1536, 2048, 1792),
    "bamboo_flower_b": (1792, 1792, 2048, 1984),
    "blank": (1984, 1984, 2048, 2048),     # fully transparent: uv0 of parts that only show their detail (fruit)
}

# --------------------------------------------------------------------------------------------- detail sheet
DETAIL_REGIONS = {
    "persimmon_fruit_a": (0, 0, 256, 256),
    "persimmon_fruit_b": (256, 0, 512, 256),
    "persimmon_fruit_c": (512, 0, 768, 256),
    "tea_flush": (0, 256, 512, 768),        # bright young tips laid over the tea leaf cluster (same footprint)
    "tea_flush_top": (512, 256, 768, 512),  # over tea_top
    "mushrooms": (512, 512, 768, 768),      # bamboo fungus (white lace veils) at the culm bases
    "mushrooms_b": (768, 512, 1024, 768),
    # buds a cycle before the Great Flowering, laid over the shoot bamboo's leaf sprays (uv2; never the bottom-left
    # corner, where UV2_NONE samples)
    "bamboo_buds": (256, 768, 512, 1024),
    "bamboo_buds_b": (512, 768, 768, 1024),
}


def _rect_uv(rect, size, inset):
    x0, y0, x1, y1 = rect
    return ((x0 + inset) / size, 1 - (y1 - inset) / size, (x1 - inset) / size, 1 - (y0 + inset) / size)


def uv(name, inset=1.5):
    return _rect_uv(REGIONS[name], MAIN, inset)


def duv(name, inset=1.5):
    return _rect_uv(DETAIL_REGIONS[name], DETAIL, inset)


def sub(rect_uv, fx0, fy0, fx1, fy1):
    """A sub-rectangle of a UV rect by fractions (fy measured from the bottom, v up)."""
    u0, v0, u1, v1 = rect_uv
    return (u0 + (u1 - u0) * fx0, v0 + (v1 - v0) * fy0, u0 + (u1 - u0) * fx1, v0 + (v1 - v0) * fy1)


def disc(name, which=0, half="top"):
    """(cx, cy, r) in UV of disc `which` (0 left, 1 right) in a two-disc region; half: the discs sit in the top half."""
    x0, y0, x1, y1 = REGIONS[name]
    w = (x1 - x0) / 2
    cx = x0 + w * (which + 0.5)
    cy = y0 + w / 2
    r = w * 0.44
    return (cx / MAIN, 1 - cy / MAIN, r / MAIN)


BLANK_UV = ((REGIONS["blank"][0] + 32) / MAIN, 1 - (REGIONS["blank"][1] + 32) / MAIN)
