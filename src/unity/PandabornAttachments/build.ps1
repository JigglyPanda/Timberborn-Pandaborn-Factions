<#
.SYNOPSIS
  Builds the character attachments bundle (pandabornattachments_win, and _mac with -Mac): the Inkpaws' conical paddy
  hat and woven back-basket as prefabs at Characters/Pandaborn/Attachments/<Name> (docs/tech/ringtail-body.md 8.2).

.DESCRIPTION
  1. Models and paints them (src/pipeline/characters/make_attachments.py) into <Project>\Assets\PandabornAttachments\Source.
  2. Copies the editor builder (src/unity/PandabornAttachments/Editor) into the Unity project.
  3. Runs Unity 6000.5.11f1 in batch mode: PandabornAttachmentsBuilder.Build -> <Out>\pandabornattachments_win, or with
     -Mac <Out>\pandabornattachments_mac only, built in its own project (<Project>-mac) by an editor with Mac Build
     Support (tools\unity_editor.ps1, docs/tech/mac.md); run the script twice (in any order) for both.
  The materials are URP Lit (in the URP package; no game shader needed). Everything heavy stays on E:.
  A bundle file must keep the name it was built with: copy it unrenamed into a mod's AssetBundles folder.
  Exit code 0 = built.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File src\unity\PandabornAttachments\build.ps1
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File src\unity\PandabornAttachments\build.ps1 -Mac
#>
[CmdletBinding()]
param(
    [Alias('UnityExe')][string]$UnityPath = '',
    [string]$Project = 'E:\PandabornDev\unity\PandabornAttachments',
    [string]$MacProject = '',
    [string]$Out = 'E:\PandabornDev\build\characters\attachments',
    [string]$Python = 'E:\PandabornDev\tools\venv\Scripts\python.exe',
    [switch]$SkipModels,
    [switch]$Mac
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$logDir = 'E:\PandabornDev\build\characters'
New-Item -ItemType Directory -Force $logDir, $Out | Out-Null
. "$repo\tools\unity_editor.ps1"
$UnityExe = Resolve-UnityEditor $UnityPath -Mac:$Mac
$sfx = ''
$targetArgs = @()
if ($Mac) { $Project = Get-MacProject $Project $MacProject; $targetArgs = @('-buildTarget', 'OSXUniversal', '-macOnly'); $sfx = '_mac' }
Write-Host "Unity $UnityExe; project $Project"

$env:UPM_CACHE_ROOT = 'E:\PandabornDev\unity\cache\upm'
$env:UPM_NPM_CACHE_PATH = 'E:\PandabornDev\unity\cache\npm'
$env:TEMP = 'E:\PandabornDev\tools\tmp'
$env:TMP = 'E:\PandabornDev\tools\tmp'
$env:PYTHONDONTWRITEBYTECODE = '1'

if (-not (Test-Path "$Project\ProjectSettings")) {
    $tpl = 'E:\PandabornDev\unity\timberborn-modding'
    if (-not (Test-Path $tpl)) { git clone --depth 1 https://github.com/mechanistry/timberborn-modding.git $tpl }
    New-Item -ItemType Directory -Force "$Project\Packages", "$Project\Assets" | Out-Null
    Copy-Item -Recurse -Force "$tpl\ProjectSettings" $Project
    Copy-Item -Force "$tpl\Packages\manifest.json", "$tpl\Packages\packages-lock.json" "$Project\Packages"
    Copy-Item -Recurse -Force "$tpl\Assets\Rendering", "$tpl\Assets\Rendering.meta" "$Project\Assets"
}

if (-not $SkipModels) {
    & $Python -I "$repo\src\pipeline\characters\make_attachments.py" $Project
    if ($LASTEXITCODE -ne 0) { throw "make_attachments.py failed ($LASTEXITCODE)" }
}

$editorDst = "$Project\Assets\PandabornAttachments\Editor"
New-Item -ItemType Directory -Force $editorDst | Out-Null
Copy-Item -Force "$repo\src\unity\PandabornAttachments\Editor\*.cs" $editorDst

$log = "$logDir\unity_attach$sfx.log"
# -Mac builds into its own staging folder, so the Windows build's folder manifest is never touched
$unityOut = if ($Mac) { "$logDir\attach-mac-stage" } else { $Out }
New-Item -ItemType Directory -Force $unityOut | Out-Null
$uargs = @('-batchmode', '-quit', '-nographics', '-projectPath', $Project, '-logFile', $log,
          '-executeMethod', 'PandabornAttachmentsBuilder.Build', '-attachOut', $unityOut) + $targetArgs
$sw = [Diagnostics.Stopwatch]::StartNew()
$p = Start-Process -FilePath $UnityExe -ArgumentList $uargs -Wait -PassThru -NoNewWindow
$sw.Stop()
$ok = Select-String -Path $log -SimpleMatch '[PandabornAttachments] OK' -Quiet
Select-String -Path $log -Pattern '\[PandabornAttachments\]|error CS|Shader error' | ForEach-Object { Write-Host $_.Line }
Write-Host "Unity exit $($p.ExitCode) after $([int]$sw.Elapsed.TotalSeconds) s; log $log"
if (-not ($p.ExitCode -eq 0 -and $ok)) { exit 1 }
if ($Mac) { Copy-Item -Force "$unityOut\pandabornattachments_mac", "$unityOut\pandabornattachments_mac.manifest" $Out }
Get-ChildItem $Out -File | Select-Object Name, Length | Format-Table -AutoSize | Out-String | Write-Host
exit 0
