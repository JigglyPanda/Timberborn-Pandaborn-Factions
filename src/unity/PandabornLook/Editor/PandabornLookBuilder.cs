// Builds the Pandaborn look asset bundle from Assets/PandabornLook/look_spec.json (written by
// src/pipeline/look_textures.py). No GUI: run it in batch mode, e.g.
//   Unity.exe -batchmode -quit -projectPath E:\PandabornDev\unity\PandabornLook
//             -executeMethod PandabornLookBuilder.Build -lookOut E:\PandabornDev\build\proto\look\AssetBundles
//             [-bundleName pandabornprotolook] [-mac]
// For every material in the spec it (re)configures the texture importers (sRGB/linear, BC7, mips, trilinear,
// aniso 16, readable as the vanilla EnvironmentURP textures are), creates
// Assets/PandabornLook/Resources/Materials/Pandaborn/Look/<name>.mat on the game's EnvironmentURP shader graph
// (imported from Timberborn_Data/StreamingAssets/Modding/Shaders.zip into Assets/TimberbornShaders), then builds
// <bundleName>_win (and <bundleName>_mac with -mac, if Mac Build Support is installed).
// The game indexes bundle assets by their path after "/Resources/", so the materials load as
// Materials/Pandaborn/Look/<name>; the material *name* (file name) is what timbermesh models look up.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

public static class PandabornLookBuilder
{
    private const string SpecPath = "Assets/PandabornLook/look_spec.json";
    private const string MaterialDir = "Assets/PandabornLook/Resources/Materials/Pandaborn/Look";

    [Serializable] public class KvS { public string key; public string value; }
    [Serializable] public class KvF { public string key; public float value; }
    [Serializable] public class KvC { public string key; public float[] value; }
    [Serializable] public class Mat { public string name; public string set; public string shader; public List<KvS> textures; public List<KvF> floats; public List<KvC> colors; }
    [Serializable] public class Tex { public string path; public bool linear; public bool readable; }
    [Serializable] public class Spec { public List<Mat> materials; public List<Tex> textures; }

    public static void Build()
    {
        try
        {
            BuildInternal();
        }
        catch (Exception e)
        {
            Debug.LogError("[PandabornLook] FAILED: " + e);
            if (Application.isBatchMode) EditorApplication.Exit(1);
            throw;
        }
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
        string outDir = Arg("-lookOut", Environment.GetEnvironmentVariable("PANDABORN_LOOK_OUT"));
        if (string.IsNullOrEmpty(outDir)) throw new Exception("no -lookOut given");
        string bundleName = Arg("-bundleName", "pandabornprotolook");
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
        // drop stale materials that are no longer in the spec
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
                Debug.LogWarning("[PandabornLook] Mac Build Support is not installed: no _mac bundle");
        }
        foreach (var extra in new[] { Path.GetFileName(outDir.TrimEnd('/', '\\')), "AssetBundles" })
        {
            var f = Path.Combine(outDir, extra);
            if (File.Exists(f)) File.Delete(f);
            if (File.Exists(f + ".manifest")) File.Delete(f + ".manifest");
        }
        Debug.Log("[PandabornLook] OK: " + matPaths.Count + " materials -> " + outDir);
    }

    private static void BuildFor(string outDir, string name, List<string> assets, BuildTarget target)
    {
        var build = new AssetBundleBuild { assetBundleName = name, assetNames = assets.ToArray() };
        var manifest = BuildPipeline.BuildAssetBundles(outDir, new[] { build },
            BuildAssetBundleOptions.ChunkBasedCompression | BuildAssetBundleOptions.StrictMode, target);
        if (manifest == null) throw new Exception("bundle build failed for " + target);
        Debug.Log("[PandabornLook] built " + Path.Combine(outDir, name) + " for " + target);
    }

    private static void ConfigureTexture(Tex t)
    {
        var imp = AssetImporter.GetAtPath(t.path) as TextureImporter;
        if (imp == null) throw new Exception("texture not found / not imported: " + t.path);
        imp.textureType = TextureImporterType.Default;
        imp.sRGBTexture = !t.linear;
        imp.alphaSource = TextureImporterAlphaSource.FromInput;
        imp.alphaIsTransparency = false;
        imp.mipmapEnabled = true;
        imp.isReadable = t.readable;
        imp.wrapMode = TextureWrapMode.Repeat;
        imp.filterMode = FilterMode.Trilinear;
        imp.anisoLevel = 16;
        imp.maxTextureSize = 1024;
        imp.textureCompression = TextureImporterCompression.CompressedHQ;
        foreach (var platform in new[] { "Standalone" })
        {
            var s = imp.GetPlatformTextureSettings(platform);
            s.overridden = true;
            s.maxTextureSize = 1024;
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
        string path = MaterialDir + "/" + m.name + ".mat";
        if (AssetDatabase.LoadAssetAtPath<Material>(path) != null) AssetDatabase.DeleteAsset(path);
        var mat = new Material(shader) { name = m.name };
        foreach (var f in m.floats)
            if (mat.HasProperty(f.key)) mat.SetFloat(f.key, f.value);
        foreach (var c in m.colors)
            if (mat.HasProperty(c.key)) mat.SetColor(c.key, new Color(c.value[0], c.value[1], c.value[2], c.value[3]));
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
        if (mat.shader.name != "Shader Graphs/EnvironmentURP")
            throw new Exception("unexpected shader name " + mat.shader.name);
        return path;
    }
}
