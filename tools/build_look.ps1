<#
.SYNOPSIS
  Builds the look asset bundle: for the Pandaborn.Look module (-BundleName pandabornlook) or, by default, for the
  data-only look prototype mod (proto/look, into E:\PandabornDev\build\proto\look).

.DESCRIPTION
  1. Paints the textures and writes the material spec (src/pipeline/look_textures.py) into the Unity project.
  2. Copies the editor builder (src/unity/PandabornLook/Editor) into the Unity project.
  3. Runs Unity 6000.5.11f1 in batch mode: PandabornLookBuilder.Build -> <BundleName>_win (and _mac with -Mac).
  4. Default (-BundleName pandabornprotolook): the bundle goes to <Out>\AssetBundles and proto/look/mod (the data-only
     "names" variant) is mirrored next to it.
     -BundleName pandabornlook (the shipping name): the bundle goes to -BundleOut (E:\PandabornDev\build\look\AssetBundles)
     only; the code build (src/code, Pandaborn.Look.csproj) copies it from there into the mod's AssetBundles folder, so
     run tools\build_code_devmod.ps1 (tests) or the code build afterwards. A bundle file must keep the name it was built
     with (after the mod manager screen the game matches already-loaded bundles by file name): never rename one by hand.
  The swap prototype (proto/look/src + mod-swap) is retired: it became the Pandaborn.Look module (src/code).
  Everything heavy stays on E: (project + Library, UPM cache, logs). Exit code 0 = built.

  First-time setup of the Unity project (done once, kept on E:):
    E:\PandabornDev\unity\PandabornLook = ProjectSettings, Packages and Assets\Rendering from
    https://github.com/mechanistry/timberborn-modding (cloned at E:\PandabornDev\unity\timberborn-modding) +
    Assets\TimberbornShaders = the contents of Timberborn_Data\StreamingAssets\Modding\Shaders.zip.
    Use -Setup to (re)create it.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\build_look.ps1
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\build_look.ps1 -SkipTextures -Mac
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\build_look.ps1 -SkipTextures -BundleName pandabornlook
#>
[CmdletBinding()]
param(
    [string]$UnityExe = 'C:\Program Files\Unity\Hub\Editor\6000.5.11f1\Editor\Unity.exe',
    [string]$Project = 'E:\PandabornDev\unity\PandabornLook',
    [string]$Out = 'E:\PandabornDev\build\proto\look',
    # bundle file name without _win/_mac; any other name than the prototype's builds the bundle only, into -BundleOut
    [string]$BundleName = 'pandabornprotolook',
    [string]$BundleOut = 'E:\PandabornDev\build\look\AssetBundles',
    [string]$Python = 'E:\PandabornDev\tools\venv\Scripts\python.exe',
    [string]$GameDir = 'C:\Program Files (x86)\Steam\steamapps\common\Timberborn',
    [string]$Only = '',
    [switch]$SkipTextures,
    [switch]$Setup,
    [switch]$Mac
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$logDir = 'E:\PandabornDev\build\look'
New-Item -ItemType Directory -Force $logDir | Out-Null

# keep Unity's package caches and temp files off C:
$env:UPM_CACHE_ROOT = 'E:\PandabornDev\unity\cache\upm'
$env:UPM_NPM_CACHE_PATH = 'E:\PandabornDev\unity\cache\npm'
$env:TEMP = 'E:\PandabornDev\tools\tmp'
$env:TMP = 'E:\PandabornDev\tools\tmp'
$env:PYTHONDONTWRITEBYTECODE = '1'

if ($Setup -or -not (Test-Path "$Project\ProjectSettings")) {
    $tpl = 'E:\PandabornDev\unity\timberborn-modding'
    if (-not (Test-Path $tpl)) { git clone --depth 1 https://github.com/mechanistry/timberborn-modding.git $tpl }
    New-Item -ItemType Directory -Force "$Project\Assets\TimberbornShaders", "$Project\Packages" | Out-Null
    Copy-Item -Recurse -Force "$tpl\ProjectSettings" $Project
    Copy-Item -Force "$tpl\Packages\manifest.json", "$tpl\Packages\packages-lock.json" "$Project\Packages"
    Copy-Item -Recurse -Force "$tpl\Assets\Rendering", "$tpl\Assets\Rendering.meta" "$Project\Assets"
    Expand-Archive -Force "$GameDir\Timberborn_Data\StreamingAssets\Modding\Shaders.zip" "$Project\Assets\TimberbornShaders"
}

if (-not $SkipTextures) {
    $a = @('-I', "$repo\src\pipeline\look_textures.py", '--unity', $Project)
    if ($Only) { $a += @('--only', $Only) }
    & $Python @a
    if ($LASTEXITCODE -ne 0) { throw "look_textures.py failed ($LASTEXITCODE)" }
}

$editorDst = "$Project\Assets\PandabornLook\Editor"
New-Item -ItemType Directory -Force $editorDst | Out-Null
Copy-Item -Force "$repo\src\unity\PandabornLook\Editor\*.cs" $editorDst

$prototype = $BundleName -eq 'pandabornprotolook'
if ($prototype) {
    # mod files first (the bundle folder is left alone), then the bundle
    New-Item -ItemType Directory -Force $Out | Out-Null
    robocopy "$repo\proto\look\mod" $Out /MIR /XD AssetBundles /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy failed ($LASTEXITCODE)" }
    $bundleDir = "$Out\AssetBundles"
} else {
    $bundleDir = $BundleOut
}
New-Item -ItemType Directory -Force $bundleDir | Out-Null

$log = "$logDir\unity_build.log"
$uargs = @('-batchmode', '-quit', '-nographics', '-projectPath', $Project, '-logFile', $log,
          '-executeMethod', 'PandabornLookBuilder.Build', '-lookOut', $bundleDir, '-bundleName', $BundleName)
if ($Mac) { $uargs += '-mac' }
$sw = [Diagnostics.Stopwatch]::StartNew()
$p = Start-Process -FilePath $UnityExe -ArgumentList $uargs -Wait -PassThru -NoNewWindow
$sw.Stop()
$ok = Select-String -Path $log -SimpleMatch '[PandabornLook] OK' -Quiet
Select-String -Path $log -Pattern '\[PandabornLook\]|error CS|Shader error' | ForEach-Object { $_.Line }
"Unity exit $($p.ExitCode) after $([int]$sw.Elapsed.TotalSeconds) s; log $log"
if ($p.ExitCode -ne 0 -or -not $ok) { exit 1 }
Get-ChildItem $bundleDir | Select-Object Name, Length | Format-Table -AutoSize | Out-String | Write-Host
if (-not $prototype) { "bundle $BundleName in $bundleDir; the code build copies it into a mod (tools\build_code_devmod.ps1 for tests)" }
exit 0
