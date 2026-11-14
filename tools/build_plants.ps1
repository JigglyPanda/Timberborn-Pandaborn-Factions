<#
.SYNOPSIS
  Builds the plants asset bundle (pandabornplants_win, and _mac with -Mac): the VegetationURP materials and textures of
  the Inkpaws' seven plants. Separate from the look lane's bundle (tools/build_look.ps1, pandabornlook): own Unity
  project, own builder, own bundle name.

.DESCRIPTION
  1. Paints the plant textures and writes the material spec (src/pipeline/plants/textures.py) into the Unity project.
  2. Copies the editor builder (src/unity/PandabornPlants/Editor) into the Unity project.
  3. Runs Unity 6000.5.11f1 in batch mode: PandabornPlantsBuilder.Build -> <Out>\pandabornplants_win (+ _mac with -Mac).
  The bundle must keep the name it was built with (the game matches loaded bundles by file name; see docs/tech/look.md,
  problem 10): never rename one by hand. Everything heavy stays on E: (project + Library, UPM cache, logs).
  Do not wrap this script in a timeout: a killed Unity batch build can crash on shutdown and leave the old bundle.
  Exit code 0 = built.

  First-time setup (done once, kept on E:): E:\PandabornDev\unity\PandabornPlants = ProjectSettings, Packages and
  Assets\Rendering from the official template (cloned at E:\PandabornDev\unity\timberborn-modding) + Assets\TimberbornShaders
  = Timberborn_Data\StreamingAssets\Modding\Shaders.zip. -Setup (re)creates it and imports it once (about 5 minutes).

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\build_plants.ps1
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\build_plants.ps1 -SkipTextures -Mac
#>
[CmdletBinding()]
param(
    [string]$UnityExe = 'C:\Program Files\Unity\Hub\Editor\6000.5.11f1\Editor\Unity.exe',
    [string]$Project = 'E:\PandabornDev\unity\PandabornPlants',
    [string]$Out = 'E:\PandabornDev\build\plants\AssetBundles',
    [string]$BundleName = 'pandabornplants',
    [string]$Python = 'E:\PandabornDev\tools\venv\Scripts\python.exe',
    [string]$GameDir = 'C:\Program Files (x86)\Steam\steamapps\common\Timberborn',
    [switch]$SkipTextures,
    [switch]$Setup,
    [switch]$Mac
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$logDir = 'E:\PandabornDev\build\plants'
New-Item -ItemType Directory -Force $logDir | Out-Null

$env:UPM_CACHE_ROOT = 'E:\PandabornDev\unity\cache\upm'
$env:UPM_NPM_CACHE_PATH = 'E:\PandabornDev\unity\cache\npm'
$env:TEMP = 'E:\PandabornDev\tools\tmp'
$env:TMP = 'E:\PandabornDev\tools\tmp'
$env:PYTHONDONTWRITEBYTECODE = '1'

function Invoke-Unity([string[]]$UArgs, [string]$Log, [string]$OkPattern) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $p = Start-Process -FilePath $UnityExe -ArgumentList $UArgs -Wait -PassThru -NoNewWindow
    $sw.Stop()
    $ok = Select-String -Path $Log -SimpleMatch $OkPattern -Quiet
    Select-String -Path $Log -Pattern '\[PandabornPlants\]|error CS|Shader error' | ForEach-Object { Write-Host $_.Line }
    Write-Host "Unity exit $($p.ExitCode) after $([int]$sw.Elapsed.TotalSeconds) s; log $Log"
    return ($p.ExitCode -eq 0 -and $ok)
}

$editorDst = "$Project\Assets\PandabornPlants\Editor"
$fresh = -not (Test-Path "$Project\ProjectSettings")
if ($Setup -or $fresh) {
    $tpl = 'E:\PandabornDev\unity\timberborn-modding'
    if (-not (Test-Path $tpl)) { git clone --depth 1 https://github.com/mechanistry/timberborn-modding.git $tpl }
    New-Item -ItemType Directory -Force "$Project\Assets\TimberbornShaders", "$Project\Packages", $editorDst | Out-Null
    Copy-Item -Recurse -Force "$tpl\ProjectSettings" $Project
    Copy-Item -Force "$tpl\Packages\manifest.json", "$tpl\Packages\packages-lock.json" "$Project\Packages"
    Copy-Item -Recurse -Force "$tpl\Assets\Rendering", "$tpl\Assets\Rendering.meta" "$Project\Assets"
    Expand-Archive -Force "$GameDir\Timberborn_Data\StreamingAssets\Modding\Shaders.zip" "$Project\Assets\TimberbornShaders"
    Copy-Item -Force "$repo\src\unity\PandabornPlants\Editor\*.cs" $editorDst
    $log = "$logDir\unity_import.log"
    $ok = Invoke-Unity @('-batchmode', '-quit', '-nographics', '-projectPath', $Project, '-logFile', $log,
                         '-executeMethod', 'PandabornPlantsBuilder.ImportOnly') $log '[PandabornPlants] IMPORTED: VegetationURP Shader Graphs/VegetationURP'
    if (-not $ok) { throw "Unity project import failed; see $log" }
    if ($Setup) { exit 0 }
}

if (-not $SkipTextures) {
    & $Python -I "$repo\src\pipeline\plants\textures.py" --unity $Project
    if ($LASTEXITCODE -ne 0) { throw "textures.py failed ($LASTEXITCODE)" }
}

New-Item -ItemType Directory -Force $editorDst, $Out | Out-Null
Copy-Item -Force "$repo\src\unity\PandabornPlants\Editor\*.cs" $editorDst

$log = "$logDir\unity_build.log"
$uargs = @('-batchmode', '-quit', '-nographics', '-projectPath', $Project, '-logFile', $log,
          '-executeMethod', 'PandabornPlantsBuilder.Build', '-plantsOut', $Out, '-bundleName', $BundleName)
if ($Mac) { $uargs += '-mac' }
$ok = Invoke-Unity $uargs $log '[PandabornPlants] OK'
if (-not $ok) { exit 1 }
Get-ChildItem $Out | Select-Object Name, Length | Format-Table -AutoSize | Out-String | Write-Host
"bundle $BundleName in $Out (copy it unrenamed into a mod's AssetBundles folder; proto/plants/build.ps1 does)"
exit 0
