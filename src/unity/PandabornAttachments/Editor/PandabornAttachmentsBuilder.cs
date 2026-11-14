// Builds the character attachments bundle (proof: real hat/basket geometry with no game code).
//   Unity.exe -batchmode -quit -nographics -projectPath E:\PandabornDev\unity\PandabornAttachments
//             -executeMethod PandabornAttachmentsBuilder.Build -attachOut <dir>
// Prefabs go to Assets/PandabornAttachments/Resources/Characters/Pandaborn/Attachments/<Name>.prefab; the game indexes
// bundle assets by their path after "/Resources/", so they load as AssetRef<GameObject>
// "Characters/Pandaborn/Attachments/<Name>" (TemplateAttachmentsSpec Prefab).
// Frames: #Head attachments are modelled y up around the node (as the vanilla hats); #Backpack attachments in the
// node's frame where +y points away from the back and -z runs up the spine (as the vanilla backpack).
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

public static class PandabornAttachmentsBuilder
{
    private const string Root = "Assets/PandabornAttachments";
    private const string PrefabDir = Root + "/Resources/Characters/Pandaborn/Attachments";

    public static void Build()
    {
        var args = Environment.GetCommandLineArgs();
        int i = Array.IndexOf(args, "-attachOut");
        string outDir = i >= 0 && i + 1 < args.Length ? args[i + 1] : "E:/PandabornDev/build/characters/attachments";
        Directory.CreateDirectory(outDir);
        Directory.CreateDirectory(PrefabDir);
        Directory.CreateDirectory(Root + "/Generated");
        var straw = MakeMaterial("PandabornStraw", new Color(0.78f, 0.66f, 0.40f));
        var bamboo = MakeMaterial("PandabornBambooWeave", new Color(0.60f, 0.48f, 0.28f));
        var paths = new List<string>
        {
            MakePrefab("ConicalHat", ConicalHat(0.155f, 0.075f, -0.025f, 28), straw),
            MakePrefab("BackBasket", Basket(0.072f, 0.096f, 0.12f, -0.17f, 0.10f, 20), bamboo)
        };
        AssetDatabase.SaveAssets();
        var build = new AssetBundleBuild { assetBundleName = "pandabornattachments_win", assetNames = paths.ToArray() };
        var manifest = BuildPipeline.BuildAssetBundles(outDir, new[] { build },
            BuildAssetBundleOptions.ChunkBasedCompression, BuildTarget.StandaloneWindows64);
        Debug.Log(manifest != null ? "[PandabornAttachments] OK " + outDir : "[PandabornAttachments] FAILED");
    }

    private static Material MakeMaterial(string name, Color color)
    {
        var shader = Shader.Find("Universal Render Pipeline/Lit");
        var m = new Material(shader) { name = name };
        m.SetColor("_BaseColor", color);
        m.SetFloat("_Smoothness", 0.15f);
        m.SetFloat("_Cull", 0f);   // two-sided: hats and baskets are thin shells
        string p = Root + "/Generated/" + name + ".mat";
        AssetDatabase.CreateAsset(m, p);
        return AssetDatabase.LoadAssetAtPath<Material>(p);
    }

    private static string MakePrefab(string name, Mesh mesh, Material material)
    {
        string meshPath = Root + "/Generated/" + name + ".asset";
        AssetDatabase.CreateAsset(mesh, meshPath);
        var go = new GameObject(name);
        go.AddComponent<MeshFilter>().sharedMesh = AssetDatabase.LoadAssetAtPath<Mesh>(meshPath);
        go.AddComponent<MeshRenderer>().sharedMaterial = material;
        string p = PrefabDir + "/" + name + ".prefab";
        PrefabUtility.SaveAsPrefabAsset(go, p);
        UnityEngine.Object.DestroyImmediate(go);
        return p;
    }

    /// <summary>A shallow cone (paddy hat) with a slight lip; y up.</summary>
    private static Mesh ConicalHat(float radius, float height, float baseY, int seg)
    {
        var v = new List<Vector3> { new Vector3(0, baseY + height, 0) };
        for (int k = 0; k <= seg; k++)
        {
            float a = 2 * Mathf.PI * k / seg;
            v.Add(new Vector3(Mathf.Cos(a) * radius, baseY, Mathf.Sin(a) * radius));
            v.Add(new Vector3(Mathf.Cos(a) * radius * 1.02f, baseY - 0.006f, Mathf.Sin(a) * radius * 1.02f));
        }
        var t = new List<int>();
        for (int k = 0; k < seg; k++)
        {
            int r0 = 1 + 2 * k, r1 = 1 + 2 * (k + 1);
            t.AddRange(new[] { 0, r1, r0 });
            t.AddRange(new[] { r0, r1, r1 + 1, r0, r1 + 1, r0 + 1 });
        }
        return Finish("ConicalHat", v, t);
    }

    /// <summary>An open tapered basket on the back: axis along -z (up the spine), centred dist out along +y.</summary>
    private static Mesh Basket(float r0, float r1, float z0, float z1, float dist, int seg)
    {
        var v = new List<Vector3>();
        int rings = 6;
        for (int j = 0; j <= rings; j++)
        {
            float s = j / (float)rings;
            float z = Mathf.Lerp(z0, z1, s), r = Mathf.Lerp(r0, r1, s) * (1 + 0.04f * Mathf.Sin(s * Mathf.PI * rings));
            for (int k = 0; k <= seg; k++)
            {
                float a = 2 * Mathf.PI * k / seg;
                v.Add(new Vector3(Mathf.Cos(a) * r, dist + Mathf.Sin(a) * r, z));
            }
        }
        int bottom = v.Count;
        v.Add(new Vector3(0, dist, z0));
        var t = new List<int>();
        for (int j = 0; j < rings; j++)
            for (int k = 0; k < seg; k++)
            {
                int a = j * (seg + 1) + k, b = a + seg + 1;
                t.AddRange(new[] { a, b, a + 1, a + 1, b, b + 1 });
            }
        for (int k = 0; k < seg; k++) t.AddRange(new[] { bottom, k, k + 1 });
        return Finish("BackBasket", v, t);
    }

    private static Mesh Finish(string name, List<Vector3> v, List<int> t)
    {
        var m = new Mesh { name = name };
        m.SetVertices(v);
        m.SetTriangles(t, 0);
        m.RecalculateNormals();
        m.RecalculateBounds();
        return m;
    }
}
