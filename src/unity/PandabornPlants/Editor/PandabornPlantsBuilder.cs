// Builds the Pandaborn plants asset bundle from Assets/PandabornPlants/plants_spec.json (written by
// src/pipeline/plants/textures.py). No GUI: run it in batch mode (tools/build_plants.ps1), e.g.
//   Unity.exe -batchmode -quit -projectPath E:\PandabornDev\unity\PandabornPlants
//             -executeMethod PandabornPlantsBuilder.Build -plantsOut E:\PandabornDev\build\plants\AssetBundles
//             [-bundleName pandabornplants] [-mac]
// For every material in the spec it (re)configures the texture importers (sRGB albedo/detail, linear swizzled
// normals, BC7, mips, trilinear, aniso 16), creates Assets/PandabornPlants/Resources/Materials/Pandaborn/Plants/<name>.mat
// on the game's VegetationURP shader graph (imported from Timberborn_Data/StreamingAssets/Modding/Shaders.zip into
// Assets/TimberbornShaders), then builds <bundleName>_win (and <bundleName>_mac with -mac, if Mac Build Support is
// installed). The game indexes bundle assets by their path after "/Resources/", so the materials load as
// Materials/Pandaborn/Plants/<name>; the material *name* is what the plant timbermesh models look up. At load the game's
// VertexColorPrefabOptimizer re-creates every VegetationURP material with Shader.Find("Shader Graphs/VegetationURP") and
// copies the properties it knows (textures, sway, flutter, detail), so the bundle's copy of the shader is never drawn.
// This is a separate project and bundle from the look lane's (PandabornLook / pandabornlook): never merge them.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

public static class PandabornPlantsBuilder
{
    private const string Tag = "[PandabornPlants]";
    private const string SpecPath = "Assets/PandabornPlants/plants_spec.json";
    private const string MaterialDir = "Assets/PandabornPlants/Resources/Materials/Pandaborn/Plants";
    private const string ShaderName = "Shader Graphs/VegetationURP";

    [Serializable] public class KvS { public string key; public string value; }
    [Serializable] public class KvF { public string key; public float value; }
    [Serializable] public class KvC { public string key; public float[] value; }
    [Serializable] public class Mat { public string name; public string shader; public List<KvS> textures; public List<KvF> floats; public List<KvC> colors; }
    [Serializable] public class Tex { public string path; public bool linear; public bool readable; public int maxSize; }
    [Serializable] public class Spec { public List<Mat> materials; public List<Tex> textures; }

    public static void Build()
    {
        try
        {
            BuildInternal();
        }
        catch (Exception e)
        {
            Debug.LogError(Tag + " FAILED: " + e);
            if (Application.isBatchMode) EditorApplication.Exit(1);
            throw;
        }
    }

    /// <summary>Only imports the project (first-time setup): no spec needed.</summary>
    public static void ImportOnly()
    {
        AssetDatabase.Refresh();
        var shader = AssetDatabase.LoadAssetAtPath<Shader>("Assets/TimberbornShaders/VegetationURP.shadergraph");
        Debug.Log(Tag + " IMPORTED: VegetationURP " + (shader != null ? shader.name : "MISSING"));
    }

    private static string Arg(string name, string fallback)
    {
        var args = Environment.GetCommandLineArgs();
        int i = Array.IndexOf(args, name);
        return i >= 0 && i + 1 < args.Length ? args[i + 1] : fallback;
    }

    private static void BuildInternal()
    {
        AssetDatabase.Refresh();
        var spec = JsonUtility.FromJson<Spec>(File.ReadAllText(SpecPath));
        string outDir = Arg("-plantsOut", Environment.GetEnvironmentVariable("PANDABORN_PLANTS_OUT"));
        if (string.IsNullOrEmpty(outDir)) throw new Exception("no -plantsOut given");
        string bundleName = Arg("-bundleName", "pandabornplants");
        bool mac = Environment.GetCommandLineArgs().Contains("-mac");

        AssetDatabase.StartAssetEditing();
        try
        {
            foreach (var t in spec.textures) ConfigureTexture(t);
        }
        finally
        {
            AssetDatabase.StopAssetEditing();
        }
        AssetDatabase.Refresh();

        Directory.CreateDirectory(MaterialDir);
        var matPaths = new List<string>();
        foreach (var m in spec.materials) matPaths.Add(CreateMaterial(m));
        foreach (var guid in AssetDatabase.FindAssets("t:Material", new[] { MaterialDir }))
        {
            var p = AssetDatabase.GUIDToAssetPath(guid);
            if (!matPaths.Contains(p)) AssetDatabase.DeleteAsset(p);
        }
        AssetDatabase.SaveAssets();

        Directory.CreateDirectory(outDir);
        BuildFor(outDir, bundleName + "_win", matPaths, BuildTarget.StandaloneWindows64);
        if (mac)
        {
            if (BuildPipeline.IsBuildTargetSupported(BuildTargetGroup.Standalone, BuildTarget.StandaloneOSX))
                BuildFor(outDir, bundleName + "_mac", matPaths, BuildTarget.StandaloneOSX);
            else
                throw new Exception("-mac given but Mac Build Support (Mono) is not installed for this editor: install the "
                                    + "module (Unity Hub > Installs > 6000.5.11f1 > Add modules), then rerun");
        }
        foreach (var extra in new[] { Path.GetFileName(outDir.TrimEnd('/', '\\')), "AssetBundles" })
        {
            var f = Path.Combine(outDir, extra);
            if (File.Exists(f)) File.Delete(f);
            if (File.Exists(f + ".manifest")) File.Delete(f + ".manifest");
        }
        Debug.Log(Tag + " OK: " + matPaths.Count + " materials -> " + outDir);
    }

    private static void BuildFor(string outDir, string name, List<string> assets, BuildTarget target)
    {
        var build = new AssetBundleBuild { assetBundleName = name, assetNames = assets.ToArray() };
        var manifest = BuildPipeline.BuildAssetBundles(outDir, new[] { build },
            BuildAssetBundleOptions.ChunkBasedCompression | BuildAssetBundleOptions.StrictMode, target);
        if (manifest == null) throw new Exception("bundle build failed for " + target);
        Debug.Log(Tag + " built " + Path.Combine(outDir, name) + " for " + target);
    }

    private static void ConfigureTexture(Tex t)
    {
        var imp = AssetImporter.GetAtPath(t.path) as TextureImporter;
        if (imp == null) throw new Exception("texture not found / not imported: " + t.path);
        int size = t.maxSize > 0 ? t.maxSize : 1024;
        imp.textureType = TextureImporterType.Default;
        imp.sRGBTexture = !t.linear;
        imp.alphaSource = TextureImporterAlphaSource.FromInput;
        imp.alphaIsTransparency = false;
        imp.mipmapEnabled = true;
        // cut-out leaves: keep coverage in the small mips so distant fields do not thin out
        imp.mipMapsPreserveCoverage = !t.linear;
        imp.alphaTestReferenceValue = 0.5f;
        imp.isReadable = t.readable;
        imp.wrapMode = TextureWrapMode.Repeat;
        imp.filterMode = FilterMode.Trilinear;
        imp.anisoLevel = 16;
        imp.maxTextureSize = size;
        imp.textureCompression = TextureImporterCompression.CompressedHQ;
        foreach (var platform in new[] { "Standalone" })
        {
            var s = imp.GetPlatformTextureSettings(platform);
            s.overridden = true;
            s.maxTextureSize = size;
            s.format = TextureImporterFormat.BC7;
            s.textureCompression = TextureImporterCompression.CompressedHQ;
            imp.SetPlatformTextureSettings(s);
        }
        imp.SaveAndReimport();
    }

    private static string CreateMaterial(Mat m)
    {
        var shader = AssetDatabase.LoadAssetAtPath<Shader>(m.shader);
        if (shader == null) throw new Exception("shader not found: " + m.shader);
        if (ShaderUtil.ShaderHasError(shader)) throw new Exception("shader has errors: " + m.shader);
        if (shader.name != ShaderName) throw new Exception("unexpected shader name " + shader.name);
        if (!m.name.StartsWith("Pandaborn", StringComparison.Ordinal)) throw new Exception("plant material names start with Pandaborn: " + m.name);
        string path = MaterialDir + "/" + m.name + ".mat";
        if (AssetDatabase.LoadAssetAtPath<Material>(path) != null) AssetDatabase.DeleteAsset(path);
        var mat = new Material(shader) { name = m.name };
        foreach (var f in m.floats)
        {
            if (!mat.HasProperty(f.key)) throw new Exception(m.shader + " has no float " + f.key);
            mat.SetFloat(f.key, f.value);
        }
        foreach (var c in m.colors)
        {
            if (!mat.HasProperty(c.key)) throw new Exception(m.shader + " has no colour " + c.key);
            mat.SetColor(c.key, new Color(c.value[0], c.value[1], c.value[2], c.value[3]));
        }
        foreach (var t in m.textures)
        {
            var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(t.value);
            if (tex == null) throw new Exception("texture missing: " + t.value);
            if (!mat.HasProperty(t.key)) throw new Exception(m.shader + " has no " + t.key);
            mat.SetTexture(t.key, tex);
        }
        mat.renderQueue = -1;
        mat.enableInstancing = false;
        AssetDatabase.CreateAsset(mat, path);
        var props = string.Join(", ", m.floats.Select(f => f.key + "=" + mat.GetFloat(f.key)));
        Debug.Log(Tag + " material " + m.name + ": " + props);
        return path;
    }
}
