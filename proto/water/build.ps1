<#
.SYNOPSIS
  Builds the water dev mod: a private copy of the generated faction build with the runtime code (including
  Pandaborn.Water) and the water prototype's data, under its own manifest Id. Never touches the shared install.
.DESCRIPTION
  The installed faction mod already carries the runtime code, without the water module, and two copies of the code must
  never run together. So tests switch the installed copy off for the run only and load this folder instead:
    tools\run_game_test.ps1 -Faction Inkpaws -DisableMods PandabornFactions -ExtraMods E:\PandabornDev\build\proto\water
  (the script restores the enable flags afterwards). Steps:
    1. mirror E:\PandabornDev\build\PandabornFactions (generated data, assets, bundles) without its Scripts/Modules;
    2. build src/code (bootstrap, Specs, Core and every module) into it;
    3. generate and copy proto/water/mod (water pieces on Buildings.Inkpaws, the test plant) and the kit meshes it uses
       (E:\PandabornDev\build\models\<Id>);
    4. write the manifest (Id JigglyPanda.PandabornProtoWater) and, with -DevSwitch, pandaborn.dev.txt.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File proto\water\build.ps1
  powershell -ExecutionPolicy Bypass -File proto\water\build.ps1 -DevSwitch 'force-off: Water'
#>
[CmdletBinding()]
param(
    [string]$Out = 'E:\PandabornDev\build\proto\water',
    [string]$Faction = 'E:\PandabornDev\build\PandabornFactions',
    [string]$Models = 'E:\PandabornDev\build\models',
    [string]$DevSwitch = ''
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$python = 'E:\PandabornDev\tools\venv\Scripts\python.exe'

if (Test-Path -LiteralPath $Out) {
    $item = Get-Item -LiteralPath $Out -Force
    if ($item.LinkType) { throw "$Out is a link; refusing to clear it" }
    Get-ChildItem -LiteralPath $Out -Force | Remove-Item -Recurse -Force
}
New-Item -ItemType Directory -Force $Out | Out-Null

# 1. the generated faction build, minus its code
& robocopy $Faction $Out /E /XD (Join-Path $Faction 'Scripts') (Join-Path $Faction 'Modules') /XF manifest.json pandaborn.dev.txt /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed ($LASTEXITCODE)" }

# 2. the runtime code with every module
$sln = Join-Path $repo 'src\code\Pandaborn.Code.sln'
$log = & dotnet build $sln -c Release -v q --nologo "-p:ModOut=$Out" 2>&1
if ($LASTEXITCODE -ne 0) { $log | ForEach-Object { Write-Host $_ -ForegroundColor Red }; throw 'code build failed' }

# 3. water prototype data and kit meshes
$env:PYTHONDONTWRITEBYTECODE = '1'
& $python -I (Join-Path $PSScriptRoot 'tools\gen_blueprints.py')
if ($LASTEXITCODE -ne 0) { throw 'gen_blueprints failed' }
& robocopy (Join-Path $PSScriptRoot 'mod') $Out /E /XF manifest.json /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed ($LASTEXITCODE)" }
foreach ($id in (Get-Content (Join-Path $PSScriptRoot 'tools\kit_models.txt') | Where-Object { $_.Trim() })) {
    $dest = Join-Path $Out "Buildings\Pandaborn\ProtoWater\Models\$id"
    New-Item -ItemType Directory -Force $dest | Out-Null
    $meshes = @(Get-ChildItem -LiteralPath (Join-Path $Models $id) -Filter '*.timbermesh')
    if ($meshes.Count -eq 0) { throw "no meshes for kit model $id in $Models" }
    $meshes | Copy-Item -Destination $dest
}

# 4. manifest and dev switch
$manifest = [ordered]@{
    Name = 'Pandaborn - Factions with the water module (dev only)'
    Version = '0.0.1'
    Id = 'JigglyPanda.PandabornProtoWater'
    MinimumGameVersion = '1.1.0.0'
    Description = 'Development-only: a copy of the generated Pandaborn - Factions build with the runtime code including the water module and the water prototype pieces. Load instead of the faction mod, never together with it. Never shipped. Art and code are AI-generated.'
    RequiredMods = @()
    OptionalMods = @()
}
[IO.File]::WriteAllText((Join-Path $Out 'manifest.json'), ($manifest | ConvertTo-Json -Depth 4), (New-Object Text.UTF8Encoding($false)))
if ($DevSwitch) {
    [IO.File]::WriteAllText((Join-Path $Out 'pandaborn.dev.txt'), ($DevSwitch -replace ';', "`n"))
    Write-Host "dev switch written: $DevSwitch" -ForegroundColor Yellow
}
# our own spec classes (Pandaborn.Specs) for the validator; template names ending .PandabornProto (dev suffix) are expected
$schema = 'E:\PandabornDev\build\obj\water-schema.json'
& dotnet run --project (Join-Path $repo 'tools\schema') -c Release -- --include (Join-Path $Out 'Scripts\Pandaborn.Specs.bin') --out $schema 2>&1 | Out-Null
$schemaArgs = @(); if ($LASTEXITCODE -eq 0 -and (Test-Path $schema)) { $schemaArgs = @('--mod-schema', $schema) } else { Write-Host 'schema dump failed; validating without our specs' -ForegroundColor Yellow }
& $python -I (Join-Path $repo 'tools\validate.py') --mod $Out @schemaArgs 2>&1 | Where-Object { $_ -notmatch "must end in '?\.Inkpaws" } | Select-Object -Last 15
Write-Host "Built $Out ($(@(Get-ChildItem -LiteralPath $Out -Recurse -File).Count) files)" -ForegroundColor Green
