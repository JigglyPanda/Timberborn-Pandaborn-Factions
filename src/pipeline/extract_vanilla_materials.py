"""Dump the vanilla building materials (reference only; never commit the output).

Reads the game's Resources (resources.assets; materials matched by asset name) with UnityPy and, for
every material listed in the vanilla MaterialCollection blueprints plus the AutoAtlaser fragments, writes:

  <out>/materials.json        shader, keywords, render queue, every float/color/texture slot (texture name, size,
                              format, wrap/filter, sRGB/readable flags)
  <out>/textures/<name>.png   each referenced texture, decoded (alpha kept)

Usage (venv python, -I):
  python -I src/pipeline/extract_vanilla_materials.py <Timberborn_Data> <Blueprints dir> <out dir> [--no-png]
"""
import json
import os
import sys

import UnityPy


def collection_paths(blueprints):
    paths = set()
    mc = os.path.join(blueprints, "MaterialCollections")
    for f in os.listdir(mc):
        with open(os.path.join(mc, f), encoding="utf-8-sig") as fh:
            paths.update(json.load(fh)["MaterialCollectionSpec"]["Materials"])
    with open(os.path.join(blueprints, "Configurations", "AutoAtlaser.blueprint.json"), encoding="utf-8-sig") as fh:
        for atlas in json.load(fh)["AutoAtlaserSpec"]["AutoAtlases"]:
            paths.update(atlas["Fragments"])
    # faction path/base wood and a few common building helpers
    paths.update([
        "Materials/Common/Empty",
    ])
    # material asset names are unique (MaterialRepository keys them by name), so match on the file name
    return {p.rsplit("/", 1)[-1]: p for p in paths}


def tex_info(tex):
    d = {
        "name": tex.m_Name,
        "size": [tex.m_Width, tex.m_Height],
        "format": str(tex.m_TextureFormat),
        "mips": getattr(tex, "m_MipCount", None),
        "readable": bool(getattr(tex, "m_IsReadable", False)),
        "colorSpace": getattr(tex, "m_ColorSpace", None),  # 1 = sRGB, 0 = linear
    }
    ts = getattr(tex, "m_TextureSettings", None)
    if ts is not None:
        d["filter"] = ts.m_FilterMode
        d["aniso"] = ts.m_Aniso
        d["wrapU"] = ts.m_WrapU
        d["wrapV"] = getattr(ts, "m_WrapV", None)
    return d


def main():
    data_dir, blueprints, out = sys.argv[1:4]
    no_png = "--no-png" in sys.argv
    wanted = collection_paths(blueprints)
    os.makedirs(os.path.join(out, "textures"), exist_ok=True)

    env = UnityPy.load(os.path.join(data_dir, "resources.assets"))
    result = {}
    seen_tex = set()
    for obj in env.objects:
        if obj.type.name != "Material":
            continue
        mat = obj.read()
        key = mat.m_Name
        if key not in wanted:
            continue
        shader_name = None
        try:
            sh = mat.m_Shader.read()
            shader_name = sh.m_ParsedForm.m_Name if getattr(sh, "m_ParsedForm", None) else sh.m_Name
        except Exception as e:  # noqa: BLE001
            shader_name = "?" + repr(e)
        props = mat.m_SavedProperties
        texs = {}
        for name, te in props.m_TexEnvs:
            entry = {"scale": [te.m_Scale.x, te.m_Scale.y], "offset": [te.m_Offset.x, te.m_Offset.y]}
            if te.m_Texture.path_id != 0:
                try:
                    t = te.m_Texture.read()
                    entry.update(tex_info(t))
                    if not no_png and t.m_Name not in seen_tex:
                        seen_tex.add(t.m_Name)
                        t.image.save(os.path.join(out, "textures", t.m_Name + ".png"))
                except Exception as e:  # noqa: BLE001
                    entry["error"] = repr(e)
            texs[name] = entry
        floats = {n: v for n, v in props.m_Floats}
        colors = {n: [round(c.r, 4), round(c.g, 4), round(c.b, 4), round(c.a, 4)] for n, c in props.m_Colors}
        ints = {n: v for n, v in getattr(props, "m_Ints", [])}
        result[wanted[key]] = {
            "name": mat.m_Name,
            "shader": shader_name,
            "validKeywords": list(getattr(mat, "m_ValidKeywords", []) or []),
            "invalidKeywords": list(getattr(mat, "m_InvalidKeywords", []) or []),
            "shaderKeywords": getattr(mat, "m_ShaderKeywords", None),
            "renderQueue": mat.m_CustomRenderQueue,
            "enableInstancing": bool(getattr(mat, "m_EnableInstancingVariants", False)),
            "doubleSidedGI": bool(getattr(mat, "m_DoubleSidedGI", False)),
            "stringTags": dict(getattr(mat, "stringTagMap", []) or []),
            "textures": texs,
            "floats": floats,
            "colors": colors,
            "ints": ints,
        }
    missing = sorted(set(wanted.values()) - set(result))
    with open(os.path.join(out, "materials.json"), "w", encoding="utf-8") as fh:
        json.dump({"materials": result, "missing": missing}, fh, indent=1, default=str)
    print(f"{len(result)} materials, {len(seen_tex)} textures, missing {missing}")


if __name__ == "__main__":
    main()
