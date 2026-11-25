// Builds the character attachments bundle: the Inkpaws' conical paddy hat and woven back-basket as prefabs.
//   Unity.exe -batchmode -quit -nographics -projectPath E:\PandabornDev\unity\PandabornAttachments
//             -executeMethod PandabornAttachmentsBuilder.Build -attachOut <dir> [-buildTarget OSXUniversal -macOnly]
// Input (written by src/pipeline/characters/make_attachments.py into Assets/PandabornAttachments/Source):
//   <Name>.mesh.json (vertices, normals, uv, one triangle list per material), <Material>_D.png / _N.png, materials.json.
// Prefabs go to Assets/PandabornAttachments/Resources/Characters/Pandaborn/Attachments/<Name>.prefab; the game indexes
// bundle assets by their path after "/Resources/", so they load as AssetRef<GameObject>
// "Characters/Pandaborn/Attachments/<Name>" (TemplateAttachmentsSpec Prefab).
// Also the Festival's rising sky lanterns: Assets/PandabornAttachments/Resources/Effects/Pandaborn/LanternRise.prefab
// (asset path "Effects/Pandaborn/LanternRise"), one ParticleSystem; see MakeLanternRise.
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
        if (File.Exists(Source + "/PandabornSkyLantern_D.png")) paths.Add(MakeLanternRise());
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

    // ------------------------------------------------------------------ the Festival's rising sky lanterns
    // Effects/Pandaborn/LanternRise: ONE ParticleSystem on the Festival Square's #LanternRise node (the square's
    // TemplateAttachmentsSpec entry "LanternRise"), driven by the Festival module (src/code/Pandaborn.Festival:
    // FestivalSquare.UpdateSky / Release, FestivalService.UpdateSky / RunShow). Material: "Universal Render
    // Pipeline/Particles/Unlit", the shader the game's own firework trails and sparks use (CometRed_Trail, Sparks:
    // transparent, alpha blend, _EMISSION), so it compiles into the bundle exactly like theirs.
    //
    // The prefab emits nothing by itself (rate 0, no bursts, no Play on Awake). The module:
    //   * sets the looping system's rate for the whole show (FestivalService.SkyLanternsPerSecond = 0.65 a second:
    //     with the 25 to 40 s life below, about 21 lanterns aloft at once, a new one every 1.5 s);
    //   * Emit(1)s the dense release of 24 over 0.3 game hours from 15.75 h;
    //   * adds the game's wind to the drift, and sets the simulation speed to the game's nonlinear animation multiplier,
    //     so the numbers below are at game speed 1 and the sky holds the same count at every speed;
    //   * stops emitting at the end of the show: the last lanterns rise on and fade.
    // PAIRED NUMBERS: startLifetime's maximum is FestivalService.SkyLanternMaxLife (40), and the rate above assumes
    // this life range (FestivalRules.SteadySkyLanterns); change them together. The module works with an older bundle
    // too (it sets loop and rate itself), only with that bundle's sizes and speeds.
    private const string EffectDir = Root + "/Resources/Effects/Pandaborn";

    private static string MakeLanternRise()
    {
        Directory.CreateDirectory(EffectDir);
        var shader = Shader.Find("Universal Render Pipeline/Particles/Unlit");
        if (shader == null) throw new Exception("Universal Render Pipeline/Particles/Unlit not found");
        var m = new Material(shader) { name = "PandabornSkyLantern" };
        m.SetTexture("_BaseMap", ImportTexture("PandabornSkyLantern_D.png", false, true, TextureWrapMode.Clamp, 256));
        m.SetColor("_BaseColor", Color.white);
        m.SetTexture("_EmissionMap", ImportTexture("PandabornSkyLantern_E.png", false, false, TextureWrapMode.Clamp, 256));
        m.SetColor("_EmissionColor", new Color(1.1f, 1.1f, 1.1f, 1f));
        m.EnableKeyword("_EMISSION");
        // URP re-derives the keywords on import; a new material's GI flags say "emissive is black", which would drop
        // _EMISSION again (MaterialEditor.FixupEmissiveFlag)
        m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.None;
        // transparent, alpha blended, no depth write: as the vanilla CometRed_Trail / Sparks materials
        m.SetFloat("_Surface", 1f); m.SetFloat("_Blend", 0f); m.SetFloat("_ColorMode", 0f);
        m.SetFloat("_SrcBlend", (float)BlendMode.SrcAlpha); m.SetFloat("_DstBlend", (float)BlendMode.OneMinusSrcAlpha);
        m.SetFloat("_ZWrite", 0f); m.SetFloat("_Cull", 2f);
        m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
        m.SetOverrideTag("RenderType", "Transparent");
        m.renderQueue = 3035;
        string mp = Root + "/Generated/PandabornSkyLantern.mat";
        AssetDatabase.DeleteAsset(mp);
        m.SetFloat("_EmissionEnabled", 1f);
        AssetDatabase.CreateAsset(m, mp);
        m = AssetDatabase.LoadAssetAtPath<Material>(mp);
        // the import re-derives keywords; put emission back on the saved asset (as the vanilla trails have it)
        m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.None;
        m.EnableKeyword("_EMISSION");
        m.renderQueue = 3035;
        EditorUtility.SetDirty(m);
        AssetDatabase.SaveAssets();
        if (!m.IsKeywordEnabled("_EMISSION")) Debug.LogError("[PandabornAttachments] PandabornSkyLantern lost _EMISSION");

        var go = new GameObject("LanternRise");
        var ps = go.AddComponent<ParticleSystem>();
        ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
        var main = ps.main;
        main.duration = 10f;
        main.loop = true;                                       // runs through the show; the rate is set from code
        main.playOnAwake = false;
        main.startLifetime = new ParticleSystem.MinMaxCurve(25f, 40f);
        main.startSpeed = 0f;                                   // the rise comes from velocity over lifetime (world up)
        main.startSize = new ParticleSystem.MinMaxCurve(0.70f, 0.90f);   // quad incl. halo; the paper is ~60 % of it
        main.startRotation = new ParticleSystem.MinMaxCurve(-0.07f, 0.07f);
        // a little brightness and warmth variation between lanterns
        main.startColor = new ParticleSystem.MinMaxGradient(Color.white, new Color(0.86f, 0.80f, 0.74f, 1f));
        main.gravityModifier = 0f;
        main.simulationSpace = ParticleSystemSimulationSpace.World;
        main.scalingMode = ParticleSystemScalingMode.Local;
        main.maxParticles = 160;
        main.cullingMode = ParticleSystemCullingMode.AlwaysSimulate;
        main.stopAction = ParticleSystemStopAction.None;

        var em = ps.emission;
        em.enabled = true;
        em.rateOverTime = 0f;
        em.rateOverDistance = 0f;

        var sh = ps.shape;
        sh.enabled = true;
        sh.shapeType = ParticleSystemShapeType.Box;
        sh.scale = new Vector3(3.8f, 0.4f, 3.8f);              // released from all over the square, among the dancers
        sh.position = new Vector3(0f, 1.1f, 0f);                // at hand height above #LanternRise (near the centre)
        sh.randomDirectionAmount = 0f;

        var vel = ps.velocityOverLifetime;
        vel.enabled = true;
        vel.space = ParticleSystemSimulationSpace.World;
        vel.x = new ParticleSystem.MinMaxCurve(-0.16f, 0.16f);  // each its own drift; the module adds the wind (and resets both ranges)
        vel.y = new ParticleSystem.MinMaxCurve(0.5f, 0.9f);
        vel.z = new ParticleSystem.MinMaxCurve(-0.16f, 0.16f);
        // they leave the hands slowly, climb, then slow as they cool and drift: the sky holds them at every height
        // (the mean of this curve is 0.72, so a lantern ends 9 to 26 m up, 16 m on average, after 25 to 40 s at game
        // speed 1) instead of losing them all off the top of the screen
        vel.speedModifier = new ParticleSystem.MinMaxCurve(1f, new AnimationCurve(
            new Keyframe(0f, 0.35f), new Keyframe(0.12f, 0.85f), new Keyframe(0.3f, 1f), new Keyframe(0.6f, 0.7f),
            new Keyframe(1f, 0.45f)));

        var noise = ps.noise;                                  // a gentle sway in the night air
        noise.enabled = true;
        noise.strength = 0.30f;
        noise.frequency = 0.18f;
        noise.scrollSpeed = 0.06f;
        noise.damping = true;
        noise.octaveCount = 1;
        noise.quality = ParticleSystemNoiseQuality.Medium;

        // no spin: a lantern stays upright (a rotation rate adds up over a 30 s life and tips them over)
        var rot = ps.rotationOverLifetime;
        rot.enabled = false;

        // the fades, as fractions of a 25 to 40 s life: in over the first 2 % (0.5 to 0.8 s, as it is lit and let go),
        // out over the last 12 % (3 to 5 s), cooling a little redder as it goes
        var col = ps.colorOverLifetime;
        col.enabled = true;
        var g = new Gradient();
        g.SetKeys(new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 0.75f),
                          new GradientColorKey(new Color(1f, 0.82f, 0.72f), 1f) },
                  new[] { new GradientAlphaKey(0f, 0f), new GradientAlphaKey(1f, 0.02f), new GradientAlphaKey(1f, 0.88f),
                          new GradientAlphaKey(0f, 1f) });
        col.color = new ParticleSystem.MinMaxGradient(g);

        var size = ps.sizeOverLifetime;
        size.enabled = true;
        size.size = new ParticleSystem.MinMaxCurve(1f, new AnimationCurve(new Keyframe(0f, 0.9f), new Keyframe(0.1f, 1f),
                                                                           new Keyframe(1f, 0.92f)));

        var r = go.GetComponent<ParticleSystemRenderer>();
        r.renderMode = ParticleSystemRenderMode.Billboard;
        r.alignment = ParticleSystemRenderSpace.View;
        r.sortMode = ParticleSystemSortMode.Distance;
        r.sharedMaterial = m;
        r.shadowCastingMode = ShadowCastingMode.Off;
        r.receiveShadows = false;
        r.minParticleSize = 0f;
        r.maxParticleSize = 0.5f;

        string p = EffectDir + "/LanternRise.prefab";
        PrefabUtility.SaveAsPrefabAsset(go, p);
        UnityEngine.Object.DestroyImmediate(go);
        return p;
    }

    private static Texture2D ImportTexture(string file, bool normal, bool alpha, TextureWrapMode wrap, int maxSize)
    {
        string path = Source + "/" + file;
        AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport);
        var imp = (TextureImporter)AssetImporter.GetAtPath(path);
        if (imp == null) throw new Exception("Missing texture " + path);
        imp.textureType = TextureImporterType.Default;
        imp.sRGBTexture = true;
        imp.alphaSource = alpha ? TextureImporterAlphaSource.FromInput : TextureImporterAlphaSource.None;
        imp.alphaIsTransparency = alpha;
        imp.mipmapEnabled = true;
        imp.wrapMode = wrap;
        imp.filterMode = FilterMode.Trilinear;
        imp.maxTextureSize = maxSize;
        imp.textureCompression = TextureImporterCompression.CompressedHQ;
        imp.SaveAndReimport();
        return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
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
