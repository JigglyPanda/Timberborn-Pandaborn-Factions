<#
.SYNOPSIS
  Builds the plants prototype mod (dev only) into E:\PandabornDev\build\proto\plants.
.DESCRIPTION
  1. (optional, -Models) rebuilds every art/plants/<Id>/build.py into E:\PandabornDev\build\plants\<Id>.
  2. (optional, -Bundle) rebuilds the textures and the pandabornplants_win bundle (tools\build_plants.ps1).
  3. Builds the plant lab DLL (proto/plants/src) into <build>\Scripts.
  4. Assembles the mod (proto/plants/tools/gen_mod.py): data, models, optional merges onto the plant blueprints, bundle.
  Never touches the Mods folder: tools/run_game_test.ps1 -ExtraMods junctions it for a run.
#>
[CmdletBinding()]
param(
    [string]$BuildDir = 'E:\PandabornDev\build\proto\plants',
    [string]$Python = 'E:\PandabornDev\tools\venv\Scripts\python.exe',
    [switch]$Models,
    [switch]$Bundle
)
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$repo = Split-Path -Parent (Split-Path -Parent $here)
$env:PYTHONDONTWRITEBYTECODE = '1'
if ($Models) {
    foreach ($s in Get-ChildItem "$repo\art\plants\*\build.py") {
        & $Python -I $s.FullName | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "model build failed: $($s.FullName)" }
    }
}
if ($Bundle) {
    & powershell -ExecutionPolicy Bypass -File "$repo\tools\build_plants.ps1"
    if ($LASTEXITCODE -ne 0) { throw 'bundle build failed' }
}
$project = Join-Path $here 'src\PandabornProtoPlants.csproj'
$log = & dotnet build $project -c Release -v q --nologo "-p:ModOut=$BuildDir" 2>&1
if ($LASTEXITCODE -ne 0) { $log | ForEach-Object { Write-Host $_ -ForegroundColor Red }; throw 'prototype build failed' }
& $Python -I "$here\tools\gen_mod.py" --out $BuildDir
if ($LASTEXITCODE -ne 0) { throw 'gen_mod failed' }
Write-Host "Built $BuildDir" -ForegroundColor Green
