<#
.SYNOPSIS
  Builds the sounds asset bundle: pandabornsounds_win, or with -Mac pandabornsounds_mac. Own Unity project, own builder,
  own bundle name (separate from pandabornlook and pandabornplants).

.DESCRIPTION
  1. Synthesizes every sound (src/pipeline/sound/build_sounds.py: WAVs, spectrograms and the loudness/loop report in
     E:\PandabornDev\build\sound) and mirrors the WAVs into the Unity project (Assets/PandabornSounds/Resources/Sounds/
     Pandaborn) with sounds_spec.json. -SkipSynth copies the last build's WAVs without synthesizing (use it for -Mac
     after a Windows build, so both bundles hold the same audio).
  2. Copies the editor builder (src/unity/PandabornSounds/Editor) into the Unity project.
  3. Runs Unity 6000.5.11f1 in batch mode: PandabornSoundsBuilder.Build -> <Out>\pandabornsounds_win, or with -Mac
     <Out>\pandabornsounds_mac only, built in its own project (<Project>-mac) by an editor with Mac Build Support
     (docs/tech/mac.md; tools\unity_editor.ps1 picks it); run the script twice (any order, also concurrently) for both.
  The bundle must keep the name it was built with (the game matches loaded bundles by file name; docs/tech/look.md
  problem 10): never rename one by hand. Exactly one enabled mod may ship a given bundle: if the faction ships
  pandabornsounds, no prototype may ship it too (two copies crash every game: "another AssetBundle with the same files").
  Do not wrap this script in a timeout: a killed Unity batch build can crash on shutdown and leave the old bundle.
  Everything heavy stays on E: (project + Library, logs). Exit code 0 = built.

  First-time setup (automatic, or -Setup to recreate): E:\PandabornDev\unity\PandabornSounds is a minimal project:
  Assets\ and Packages\manifest.json with only the built-in audio and asset-bundle modules (they ship inside the
  editor: no package download, no render pipeline, no shaders). Unity writes ProjectSettings on the first open.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\build_sound.ps1
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\build_sound.ps1 -SkipSynth -Mac
#>
[CmdletBinding()]
param(
    # Unity editor folder or Unity.exe; empty = auto (tools\unity_editor.ps1: C: install, or with -Mac the E: copy with Mac support)
    [Alias('UnityExe')][string]$UnityPath = '',
    [string]$Project = 'E:\PandabornDev\unity\PandabornSounds',
    # -Mac builds in its own project (default <Project>-mac) so the Windows project is never switched or locked
    [string]$MacProject = '',
    [string]$Out = 'E:\PandabornDev\build\sound\AssetBundles',
    [string]$BundleName = 'pandabornsounds',
    [string]$Python = 'E:\PandabornDev\tools\venv\Scripts\python.exe',
    # passed to build_sounds.py --only (ids containing any of these); empty = every sound
    [string]$Only = '',
    [switch]$SkipSynth,
    [switch]$Setup,
    [switch]$Mac
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$logDir = 'E:\PandabornDev\build\sound'
New-Item -ItemType Directory -Force $logDir | Out-Null
. "$PSScriptRoot\unity_editor.ps1"
$UnityExe = Resolve-UnityEditor $UnityPath -Mac:$Mac
$targetArgs = @()
$sfx = ''
if ($Mac) { $Project = Get-MacProject $Project $MacProject; $targetArgs = @('-buildTarget', 'OSXUniversal'); $sfx = '_mac' }
Write-Host "Unity $UnityExe; project $Project"

$env:UPM_CACHE_ROOT = 'E:\PandabornDev\unity\cache\upm'
$env:UPM_NPM_CACHE_PATH = 'E:\PandabornDev\unity\cache\npm'
$env:TEMP = 'E:\PandabornDev\tools\tmp'
$env:TMP = 'E:\PandabornDev\tools\tmp'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:MPLCONFIGDIR = 'E:\PandabornDev\tools\tmp\mpl'

$editorDst = "$Project\Assets\PandabornSounds\Editor"
New-Item -ItemType Directory -Force "$Project\Assets", "$Project\Packages", "$Project\ProjectSettings", $editorDst | Out-Null
# Built-in modules only (they ship inside the editor: nothing is downloaded). Unity treats a folder without
# ProjectSettings\ProjectVersion.txt as a brand-new project and replaces the manifest with its default template (two
# dozen registry packages), so the version file is written first and the manifest is put back whenever it differs.
$manifest = '{ "dependencies": { "com.unity.modules.audio": "1.0.0", "com.unity.modules.assetbundle": "1.0.0", "com.unity.modules.jsonserialize": "1.0.0" } }'
$manifestPath = "$Project\Packages\manifest.json"
if ($Setup -or -not (Test-Path $manifestPath) -or ([IO.File]::ReadAllText($manifestPath) -ne $manifest)) {
    [IO.File]::WriteAllText($manifestPath, $manifest)
    if (Test-Path "$Project\Packages\packages-lock.json") { Remove-Item -Force "$Project\Packages\packages-lock.json" }
}
if (-not (Test-Path "$Project\ProjectSettings\ProjectVersion.txt")) {
    [IO.File]::WriteAllText("$Project\ProjectSettings\ProjectVersion.txt",
        "m_EditorVersion: 6000.5.11f1`nm_EditorVersionWithRevision: 6000.5.11f1 (5c3a1087d8e4)`n")
}

if (-not $SkipSynth) {
    $a = @('-I', "$repo\src\pipeline\sound\build_sounds.py", '--unity', $Project)
    if ($Only) { $a += @('--only', $Only) }
    & $Python @a
    if ($LASTEXITCODE -ne 0) { throw "build_sounds.py failed or a sound check failed ($LASTEXITCODE); see $logDir\report.md" }
} else {
    # no synthesis: mirror the last build's WAVs (E:\PandabornDev\build\sound\wav, report.json) into this project
    & $Python -I "$repo\src\pipeline\sound\build_sounds.py" --sync-only --unity $Project
    if ($LASTEXITCODE -ne 0) { throw "-SkipSynth: no previous sound build to copy; run once without -SkipSynth" }
}

New-Item -ItemType Directory -Force $editorDst, $Out | Out-Null
Copy-Item -Force "$repo\src\unity\PandabornSounds\Editor\*.cs" $editorDst

$log = "$logDir\unity_build$sfx.log"
# -Mac builds into its own staging folder, so a concurrent Windows build's folder manifest is never touched
$unityOut = if ($Mac) { "$logDir\mac-stage" } else { $Out }
New-Item -ItemType Directory -Force $unityOut | Out-Null
$uargs = @('-batchmode', '-quit', '-nographics', '-projectPath', $Project, '-logFile', $log,
          '-executeMethod', 'PandabornSoundsBuilder.Build', '-soundsOut', $unityOut, '-bundleName', $BundleName)
if ($Mac) { $uargs += @('-mac', '-macOnly') + $targetArgs }
$sw = [Diagnostics.Stopwatch]::StartNew()
$p = Start-Process -FilePath $UnityExe -ArgumentList $uargs -Wait -PassThru -NoNewWindow
$sw.Stop()
$ok = Select-String -Path $log -SimpleMatch '[PandabornSounds] OK' -Quiet
Select-String -Path $log -Pattern '\[PandabornSounds\] (built|OK|FAILED|removed)|error CS' | ForEach-Object { Write-Host $_.Line }
Write-Host "Unity exit $($p.ExitCode) after $([int]$sw.Elapsed.TotalSeconds) s; log $log"
if ($p.ExitCode -ne 0 -or -not $ok) { exit 1 }
if ($Mac) { Copy-Item -Force "$unityOut\$($BundleName)_mac", "$unityOut\$($BundleName)_mac.manifest" $Out }
Get-ChildItem $Out | Select-Object Name, Length | Format-Table -AutoSize | Out-String | Write-Host
# decode what the game will decode and compare it with the WAVs (import settings, length, loudness, loop seams)
$built = Join-Path $Out ($BundleName + $(if ($Mac) { '_mac' } else { '_win' }))
& $Python -I "$repo\src\pipeline\sound\bundle_check.py" $built | Select-Object -Last 3 | ForEach-Object { Write-Host $_ }
if ($LASTEXITCODE -ne 0) { Write-Host "bundle check failed: $logDir\bundle_check_$(Split-Path -Leaf $built).json"; exit 1 }
"bundle $BundleName in $Out (copy it unrenamed into exactly one mod's AssetBundles folder; proto/sound/build.ps1 does)"
exit 0
