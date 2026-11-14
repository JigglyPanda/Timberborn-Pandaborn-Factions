// Builds the character attachments bundle: the Inkpaws' conical paddy hat and woven back-basket as prefabs.
//   Unity.exe -batchmode -quit -nographics -projectPath E:\PandabornDev\unity\PandabornAttachments
//             -executeMethod PandabornAttachmentsBuilder.Build -attachOut <dir> [-buildTarget OSXUniversal -macOnly]
// Input (written by src/pipeline/characters/make_attachments.py into Assets/PandabornAttachments/Source):
//   <Name>.mesh.json (vertices, normals, uv, one triangle list per material), <Material>_D.png / _N.png, materials.json.
// Prefabs go to Assets/PandabornAttachments/Resources/Characters/Pandaborn/Attachments/<Name>.prefab; the game indexes
// bundle assets by their path after "/Resources/", so they load as AssetRef<GameObject>
// "Characters/Pandaborn/Attachments/<Name>" (TemplateAttachmentsSpec Prefab).
// Frames: the hat in the #Head node's frame (y up, as the vanilla hats); the basket in the #Backpack node's frame
// (+y away from the back, -z up the spine, as the vanilla backpack).
// Without -macOnly: pandabornattachments_win (StandaloneWindows64). With -macOnly (the separate <project>-mac project,
// src/unity/PandabornAttachments/build.ps1 -Mac): pandabornattachments_mac (StandaloneOSX).
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

public static class PandabornAttachmentsBuilder
{
    private const string Root = "Assets/PandabornAttachments";
    private const string Source = Root + "/Source";
    private const string PrefabDir = Root + "/Resources/Characters/Pandaborn/Attachments";
    private const string BundleName = "pandabornattachments";

    [Serializable] private class MaterialDef { public string name; public string diffuse; public string normal; public bool cutout; public float smoothness; }
    [Serializable] private class MaterialList { public MaterialDef[] items; }
    [Serializable] private class MeshDef { public string name; public float[] vertices; public float[] normals; public float[] uv; public string[] materials; }

    public static void Build()
    {
        var args = Environment.GetCommandLineArgs();
        int i = Array.IndexOf(args, "-attachOut");
        string outDir = i >= 0 && i + 1 < args.Length ? args[i + 1] : "E:/PandabornDev/build/characters/attachments";
        bool macOnly = args.Contains("-macOnly");
        Directory.CreateDirectory(outDir);
        Directory.CreateDirectory(PrefabDir);
        Directory.CreateDirectory(Root + "/Generated");
        AssetDatabase.Refresh();

        var defs = JsonUtility.FromJson<MaterialList>("{\"items\":" + File.ReadAllText(Source + "/materials.json") + "}").items;
        var materials = new Dictionary<string, Material>();
        foreach (var d in defs) materials[d.name] = MakeMaterial(d);

        var paths = new List<string>();
        foreach (var file in Directory.GetFiles(Source, "*.mesh.json").OrderBy(f => f, StringComparer.Ordinal))
            paths.Add(MakePrefab(file.Replace('\\', '/'), materials));
        AssetDatabase.SaveAssets();

        string name = BundleName + (macOnly ? "_mac" : "_win");
        var target = macOnly ? BuildTarget.StandaloneOSX : BuildTarget.StandaloneWindows64;
        if (macOnly && !BuildPipeline.IsBuildTargetSupported(BuildTargetGroup.Standalone, target))
        {
            Debug.LogError("[PandabornAttachments] FAILED: no Mac Build Support in this editor");
            return;
        }
        var build = new AssetBundleBuild { assetBundleName = name, assetNames = paths.ToArray() };
        var manifest = BuildPipeline.BuildAssetBundles(outDir, new[] { build }, BuildAssetBundleOptions.ChunkBasedCompression, target);
        Debug.Log(manifest != null ? "[PandabornAttachments] OK " + name + " -> " + outDir + " (" + paths.Count + " prefabs)" : "[PandabornAttachments] FAILED");
    }

    private static Texture2D ImportTexture(string file, bool normal, bool alpha)
    {
        string path = Source + "/" + file;
        AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport);
        var imp = (TextureImporter)AssetImporter.GetAtPath(path);
        if (imp == null) throw new Exception("Missing texture " + path);
        imp.textureType = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
        imp.sRGBTexture = !normal;
        imp.alphaSource = alpha ? TextureImporterAlphaSource.FromInput : TextureImporterAlphaSource.None;
        imp.alphaIsTransparency = alpha;
        imp.mipmapEnabled = true;
        imp.wrapMode = TextureWrapMode.Repeat;
        imp.filterMode = FilterMode.Trilinear;
        imp.anisoLevel = 4;
        imp.maxTextureSize = 1024;
        imp.textureCompression = TextureImporterCompression.Compressed;
        imp.SaveAndReimport();
        return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
    }

    private static Material MakeMaterial(MaterialDef d)
    {
        var shader = Shader.Find("Universal Render Pipeline/Lit");
        var m = new Material(shader) { name = d.name };
        m.SetTexture("_BaseMap", ImportTexture(d.diffuse, false, d.cutout));
        m.SetColor("_BaseColor", Color.white);
        m.SetTexture("_BumpMap", ImportTexture(d.normal, true, false));
        m.SetFloat("_BumpScale", 1f);
        m.EnableKeyword("_NORMALMAP");
        m.SetFloat("_Smoothness", d.smoothness);
        m.SetFloat("_Metallic", 0f);
        if (d.cutout)
        {
            m.SetFloat("_AlphaClip", 1f);
            m.SetFloat("_Cutoff", 0.5f);
            m.EnableKeyword("_ALPHATEST_ON");
            m.renderQueue = (int)RenderQueue.AlphaTest;
            m.SetOverrideTag("RenderType", "TransparentCutout");
        }
        m.SetFloat("_Cull", 2f);   // back faces culled: both sides of thin shells are modelled
        string p = Root + "/Generated/" + d.name + ".mat";
        AssetDatabase.DeleteAsset(p);
        AssetDatabase.CreateAsset(m, p);
        return AssetDatabase.LoadAssetAtPath<Material>(p);
    }

    private static string MakePrefab(string jsonPath, Dictionary<string, Material> materials)
    {
        string text = File.ReadAllText(jsonPath);
        var def = JsonUtility.FromJson<MeshDef>(text);
        var subs = ParseSubmeshes(text);
        var mesh = new Mesh { name = def.name };
        int n = def.vertices.Length / 3;
        var v = new Vector3[n]; var nr = new Vector3[n]; var uv = new Vector2[n];
        for (int k = 0; k < n; k++)
        {
            v[k] = new Vector3(def.vertices[3 * k], def.vertices[3 * k + 1], def.vertices[3 * k + 2]);
            nr[k] = new Vector3(def.normals[3 * k], def.normals[3 * k + 1], def.normals[3 * k + 2]);
            uv[k] = new Vector2(def.uv[2 * k], def.uv[2 * k + 1]);
        }
        if (n > 65535) mesh.indexFormat = IndexFormat.UInt32;
        mesh.vertices = v; mesh.normals = nr; mesh.uv = uv;
        mesh.subMeshCount = subs.Count;
        // the generator winds every triangle so that Vector3.Cross(b - a, c - a) runs along the outward normal, which is
        // Unity's front face (clockwise seen from outside in Unity's left-handed space, as in .timbermesh files)
        for (int s = 0; s < subs.Count; s++) mesh.SetTriangles(subs[s], s);
        mesh.RecalculateTangents();
        mesh.RecalculateBounds();
        string meshPath = Root + "/Generated/" + def.name + ".asset";
        AssetDatabase.DeleteAsset(meshPath);
        AssetDatabase.CreateAsset(mesh, meshPath);
        var go = new GameObject(def.name);
        go.AddComponent<MeshFilter>().sharedMesh = AssetDatabase.LoadAssetAtPath<Mesh>(meshPath);
        var r = go.AddComponent<MeshRenderer>();
        r.sharedMaterials = def.materials.Select(m => materials[m]).ToArray();
        r.shadowCastingMode = ShadowCastingMode.On;
        string p = PrefabDir + "/" + def.name + ".prefab";
        PrefabUtility.SaveAsPrefabAsset(go, p);
        UnityEngine.Object.DestroyImmediate(go);
        return p;
    }

    // JsonUtility cannot read int[][]: read "submeshes": [[...], [...]] by hand
    private static List<int[]> ParseSubmeshes(string json)
    {
        int at = json.IndexOf("\"submeshes\"", StringComparison.Ordinal);
        int start = json.IndexOf('[', at);
        var result = new List<int[]>();
        int depth = 0; var cur = new List<int>(); var num = new System.Text.StringBuilder();
        for (int k = start; k < json.Length; k++)
        {
            char c = json[k];
            if (c == '[') { depth++; if (depth == 2) cur = new List<int>(); }
            else if (c == ']')
            {
                if (num.Length > 0) { cur.Add(int.Parse(num.ToString())); num.Clear(); }
                if (depth == 2) result.Add(cur.ToArray());
                depth--;
                if (depth == 0) break;
            }
            else if (c == ',') { if (num.Length > 0) { cur.Add(int.Parse(num.ToString())); num.Clear(); } }
            else if (char.IsDigit(c) || c == '-') num.Append(c);
        }
        return result;
    }
}
