<#
.SYNOPSIS
  Builds the Ringtails test probe (dev only) into E:\PandabornDev\build\proto\ringtails.
.DESCRIPTION
  Everything the Ringtails need ships in the faction mod: the code (src/code/Pandaborn.Ringtails, Pandaborn.RingtailsFallback)
  and the data (catalogue: Ringtail templates, worker type, outfits, night posts, Moon Loft, name pool; body meshes from the
  ringtail-body lane via assemble). This mod carries only the dev-only test probe (Scripts\, inert without a harness
  request), which reaches the module by reflection. It rides on the installed faction build or a dev copy of it
  (proto/foundation/build.ps1).
  1. Copies proto/ringtails/mod (the manifest) into the build folder.
  2. Builds the probe (proto/ringtails/src) into <build>\Scripts.
  3. Removes stale files (the data this mod used to carry). Never touches the Mods folder (run_game_test.ps1 -ExtraMods
     junctions it for a run).
#>
[CmdletBinding()]
param(
    [string]$BuildDir = 'E:\PandabornDev\build\proto\ringtails'
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
$project = Join-Path $here 'src\PandabornProtoRingtails.csproj'
$log = & dotnet build $project -c Release -v q --nologo "-p:ModOut=$BuildDir" 2>&1
if ($LASTEXITCODE -ne 0) { $log | ForEach-Object { Write-Host $_ -ForegroundColor Red }; throw 'probe build failed' }
$expected['scripts\pandabornprotoringtails.dll'] = $true
foreach ($f in Get-ChildItem -LiteralPath $BuildDir -Recurse -File) {
    $rel = $f.FullName.Substring($BuildDir.Length + 1)
    if (-not $expected.ContainsKey($rel.ToLowerInvariant())) { Remove-Item -LiteralPath $f.FullName -Force; Write-Host "removed stale $rel" }
}
Get-ChildItem -LiteralPath $BuildDir -Recurse -Directory | Sort-Object { $_.FullName.Length } -Descending |
    Where-Object { -not (Get-ChildItem -LiteralPath $_.FullName -Force) } | Remove-Item -Force
Write-Host "Built $BuildDir ($($expected.Count) files)" -ForegroundColor Green
