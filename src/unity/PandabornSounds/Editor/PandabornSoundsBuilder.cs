// Builds the Pandaborn sounds asset bundle from Assets/PandabornSounds/sounds_spec.json (written by
// src/pipeline/sound/build_sounds.py --unity <project>, which also puts the WAVs into
// Assets/PandabornSounds/Resources/Sounds/Pandaborn/). No GUI: run it in batch mode (tools/build_sound.ps1), e.g.
//   Unity.exe -batchmode -quit -nographics -projectPath E:\PandabornDev\unity\PandabornSounds
//             -executeMethod PandabornSoundsBuilder.Build -soundsOut E:\PandabornDev\build\sound\AssetBundles
//             [-bundleName pandabornsounds] [-mac] [-macOnly]
// Import settings match the game's own sound effects (extracted 1.1.2.8: 204 of 254 clips are ADPCM, CompressedInMemory,
// preloaded, mono; only the music is Vorbis, streamed): CompressedInMemory, ADPCM (cheap to decode for many looping
// voices), sample rate preserved (48 kHz), preload on, load in background off, force-to-mono except where the spec
// marks a clip stereo (the wonder launch). Loops are not marked in
// the importer (Unity has no loop flag on AudioClip); the game sets AudioSource.loop itself.
// The game indexes bundle assets by their path after "/Resources/", so a clip lands at sounds/pandaborn/<name> and is
// found by AudioClipService.LoadAudioClips (IAssetLoader.LoadAll<AudioClip>("Sounds")), which keys clips by their *asset
// name*: the file name without .wav, e.g. "Environment.Pandaborn.ShiftBell.End_01".
// This is its own project and bundle (pandabornsounds): never merge it with the look or plants bundles.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

public static class PandabornSoundsBuilder
{
    private const string Tag = "[PandabornSounds]";
    private const string SpecPath = "Assets/PandabornSounds/sounds_spec.json";
    private const string ClipDir = "Assets/PandabornSounds/Resources/Sounds/Pandaborn";

    [Serializable] public class Clip { public string file; public bool loop; public bool stereo; }
    [Serializable] public class Spec { public List<Clip> clips; }

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
        string outDir = Arg("-soundsOut", Environment.GetEnvironmentVariable("PANDABORN_SOUNDS_OUT"));
        if (string.IsNullOrEmpty(outDir)) throw new Exception("no -soundsOut given");
        string bundleName = Arg("-bundleName", "pandabornsounds");
        bool mac = Environment.GetCommandLineArgs().Contains("-mac");
        bool macOnly = Environment.GetCommandLineArgs().Contains("-macOnly");

        // stale clips (in the folder but not in the spec) are removed, so the bundle holds exactly the spec
        var wanted = new HashSet<string>(spec.clips.Select(c => c.file));
        foreach (var guid in AssetDatabase.FindAssets("t:AudioClip", new[] { ClipDir }))
        {
            var p = AssetDatabase.GUIDToAssetPath(guid);
            if (!wanted.Contains(p)) { AssetDatabase.DeleteAsset(p); Debug.Log(Tag + " removed stale " + p); }
        }

        AssetDatabase.StartAssetEditing();
        try
        {
            foreach (var c in spec.clips) Configure(c);
        }
        finally
        {
            AssetDatabase.StopAssetEditing();
        }
        AssetDatabase.Refresh();

        var paths = new List<string>();
        foreach (var c in spec.clips)
        {
            var clip = AssetDatabase.LoadAssetAtPath<AudioClip>(c.file);
            if (clip == null) throw new Exception("clip did not import: " + c.file);
            paths.Add(c.file);
            Debug.Log(string.Format("{0} clip {1}: {2:0.000} s, {3} ch, {4} Hz, {5}", Tag, clip.name, clip.length, clip.channels,
                clip.frequency, clip.loadType));
        }

        Directory.CreateDirectory(outDir);
        if (!macOnly) BuildFor(outDir, bundleName + "_win", paths, BuildTarget.StandaloneWindows64);
        if (mac || macOnly)
        {
            if (BuildPipeline.IsBuildTargetSupported(BuildTargetGroup.Standalone, BuildTarget.StandaloneOSX))
                BuildFor(outDir, bundleName + "_mac", paths, BuildTarget.StandaloneOSX);
            else
                throw new Exception("-mac given but Mac Build Support (Mono) is not installed for this editor: use the "
                                    + "E: editor copy that has it (docs/tech/mac.md), then rerun");
        }
        // Unity also writes a folder manifest bundle named after the output folder: never ship it (any file in a mod's
        // AssetBundles folder that is not *.manifest is loaded as a bundle)
        foreach (var extra in new[] { Path.GetFileName(outDir.TrimEnd('/', '\\')), "AssetBundles", "mac-stage" })
        {
            var f = Path.Combine(outDir, extra);
            if (File.Exists(f)) File.Delete(f);
            if (File.Exists(f + ".manifest")) File.Delete(f + ".manifest");
        }
        Debug.Log(Tag + " OK: " + paths.Count + " clips -> " + outDir);
    }

    private static void Configure(Clip c)
    {
        var imp = AssetImporter.GetAtPath(c.file) as AudioImporter;
        if (imp == null) throw new Exception("not an audio asset: " + c.file);
        imp.forceToMono = !c.stereo;
        imp.loadInBackground = false;
        imp.ambisonic = false;
        var s = imp.defaultSampleSettings;
        s.loadType = AudioClipLoadType.CompressedInMemory;
        s.compressionFormat = AudioCompressionFormat.ADPCM;
        s.sampleRateSetting = AudioSampleRateSetting.PreserveSampleRate;
        s.preloadAudioData = true;
        imp.defaultSampleSettings = s;
        imp.ClearSampleSettingOverride("Standalone");
        EditorUtility.SetDirty(imp);
        imp.SaveAndReimport();
    }

    private static void BuildFor(string outDir, string name, List<string> assets, BuildTarget target)
    {
        var build = new AssetBundleBuild { assetBundleName = name, assetNames = assets.ToArray() };
        var manifest = BuildPipeline.BuildAssetBundles(outDir, new[] { build },
            BuildAssetBundleOptions.ChunkBasedCompression | BuildAssetBundleOptions.StrictMode, target);
        if (manifest == null) throw new Exception("BuildAssetBundles failed for " + name);
        var file = new FileInfo(Path.Combine(outDir, name));
        Debug.Log(string.Format("{0} built {1} ({2}): {3:N0} bytes, {4} clips", Tag, name, target, file.Exists ? file.Length : -1, assets.Count));
    }
}
