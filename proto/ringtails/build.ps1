<#
.SYNOPSIS
  Builds the Ringtails prototype mod (dev only) into E:\PandabornDev\build\proto\ringtails.
.DESCRIPTION
  1. Mirrors proto/ringtails/mod (blueprints, localization, manifest) into the build folder.
  2. Copies the red panda coats from the Reskin release (not in git) under Ringtail names.
  3. Builds proto/ringtails/src into <build>\Scripts.
  4. Removes stale files. Never touches the Mods folder: tools/run_game_test.ps1 -ExtraMods junctions it for a run.
#>
[CmdletBinding()]
param(
    [string]$BuildDir = 'E:\PandabornDev\build\proto\ringtails',
    [string]$CoatSource = 'E:\PandabornDev\assets\Pandaborn-Reskin-release\Materials\Beavers\IronTeeth'
)
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$source = Join-Path $here 'mod'
New-Item -ItemType Directory -Force $BuildDir | Out-Null
$expected = @{}
foreach ($f in Get-ChildItem -LiteralPath $source -Recurse -File) {
    $rel = $f.FullName.Substring($source.Length + 1)
    $to = Join-Path $BuildDir $rel
    New-Item -ItemType Directory -Force (Split-Path $to -Parent) | Out-Null
    Copy-Item -LiteralPath $f.FullName -Destination $to -Force
    $expected[$rel.ToLowerInvariant()] = $true
}
$coats = @{}
for ($i = 1; $i -le 5; $i++) { $coats["Materials\Pandaborn\Ringtails\Adult\RingtailAdult$i.png"] = Join-Path $CoatSource "Adult\BeaverAdult$i.IronTeeth.png" }
for ($i = 1; $i -le 3; $i++) { $coats["Materials\Pandaborn\Ringtails\Child\RingtailChild$i.png"] = Join-Path $CoatSource "Child\BeaverChild$i.IronTeeth.png" }
foreach ($rel in $coats.Keys) {
    if (-not (Test-Path -LiteralPath $coats[$rel])) { throw "coat missing: $($coats[$rel])" }
    $to = Join-Path $BuildDir $rel
    New-Item -ItemType Directory -Force (Split-Path $to -Parent) | Out-Null
    Copy-Item -LiteralPath $coats[$rel] -Destination $to -Force
    $expected[$rel.ToLowerInvariant()] = $true
}
$project = Join-Path $here 'src\PandabornProtoRingtails.csproj'
$log = & dotnet build $project -c Release -v q --nologo "-p:ModOut=$BuildDir" 2>&1
if ($LASTEXITCODE -ne 0) { $log | ForEach-Object { Write-Host $_ -ForegroundColor Red }; throw 'prototype build failed' }
$expected['scripts\pandabornprotoringtails.dll'] = $true
foreach ($f in Get-ChildItem -LiteralPath $BuildDir -Recurse -File) {
    $rel = $f.FullName.Substring($BuildDir.Length + 1)
    if (-not $expected.ContainsKey($rel.ToLowerInvariant())) { Remove-Item -LiteralPath $f.FullName -Force; Write-Host "removed stale $rel" }
}
Write-Host "Built $BuildDir ($($expected.Count) files)" -ForegroundColor Green
