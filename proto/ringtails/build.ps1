<#
.SYNOPSIS
  Builds the Ringtails test mod (dev only) into E:\PandabornDev\build\proto\ringtails.
.DESCRIPTION
  The Ringtails code ships in the faction mod (src/code/Pandaborn.Ringtails, Pandaborn.RingtailsFallback). This mod carries
  only what the catalogue lane will own later (Ringtail templates, worker type, outfits, merges onto the generated night
  posts, Moon Loft and Inkpaw templates), the red panda body meshes, and the dev-only test probe (Scripts\, inert without a
  harness request). It rides on the installed faction build (Buildings.Inkpaws).
  1. Mirrors proto/ringtails/mod into the build folder.
  2. Copies the Ringtail body meshes (not in git) from the ringtail-body lane's output, only when they changed.
  3. Builds the probe (proto/ringtails/src) into <build>\Scripts.
  4. Removes stale files. Never touches the Mods folder (run_game_test.ps1 -ExtraMods junctions it for a run).
#>
[CmdletBinding()]
param(
    [string]$BuildDir = 'E:\PandabornDev\build\proto\ringtails',
    [string]$MeshSource = 'E:\PandabornDev\build\characters\out'
)
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$source = Join-Path $here 'mod'
New-Item -ItemType Directory -Force $BuildDir | Out-Null
$expected = @{}
function Copy-IfChanged([string]$from, [string]$to) {
    $src = Get-Item -LiteralPath $from
    if (Test-Path -LiteralPath $to) {
        $dst = Get-Item -LiteralPath $to
        if ($dst.Length -eq $src.Length -and $dst.LastWriteTimeUtc -eq $src.LastWriteTimeUtc) { return }
    }
    New-Item -ItemType Directory -Force (Split-Path $to -Parent) | Out-Null
    Copy-Item -LiteralPath $from -Destination $to -Force
}
foreach ($f in Get-ChildItem -LiteralPath $source -Recurse -File) {
    $rel = $f.FullName.Substring($source.Length + 1)
    Copy-IfChanged $f.FullName (Join-Path $BuildDir $rel)
    $expected[$rel.ToLowerInvariant()] = $true
}
foreach ($name in 'RingtailAdult', 'RingtailChild') {
    $from = Join-Path $MeshSource "$name.Model.timbermesh"
    if (-not (Test-Path -LiteralPath $from)) { throw "Ringtail body mesh missing: $from (ringtail-body lane: src/pipeline/characters/make_ringtails.py)" }
    $rel = "Characters\Pandaborn\$name.Model.timbermesh"
    Copy-IfChanged $from (Join-Path $BuildDir $rel)
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
