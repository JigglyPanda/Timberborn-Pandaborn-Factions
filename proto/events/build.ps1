<#
.SYNOPSIS
  Builds the events dev mod (dev only) into E:\PandabornDev\build\proto\events.
.DESCRIPTION
  1. Mirrors proto/events/mod (data merged onto the faction's templates, manifest) into the build folder.
  2. Writes the two "in flower" bamboo twins from the installed faction mod's plant blueprints (tools/derive.py).
  3. Copies the modules' localization (src/code/Pandaborn.Festival/mod).
  4. Compiles the Festival and Flowering modules' sources plus the probe into Scripts\PandabornProtoEvents.dll, against
     the installed faction mod's own Pandaborn.Core (and Pandaborn.Specs when it already carries the event specs: then the
     spec records are not compiled in again, which would be a duplicate spec name).
  5. Removes stale files. Never touches the Mods folder: tools/run_game_test.ps1 -ExtraMods junctions it for a run.
  Also builds both modules on their own into a scratch folder so their required-API lists and FEATURE.md are refreshed.
#>
[CmdletBinding()]
param(
    [string]$BuildDir = 'E:\PandabornDev\build\proto\events',
    [string]$Installed = 'E:\PandabornDev\build\PandabornFactions',
    [string]$Python = 'E:\PandabornDev\tools\venv\Scripts\python.exe'
)
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$repo = Split-Path -Parent (Split-Path -Parent $here)
$source = Join-Path $here 'mod'
New-Item -ItemType Directory -Force $BuildDir | Out-Null
$expected = @{}
function Add-Expected([string]$path) { $script:expected[$path.Substring($BuildDir.Length + 1).ToLowerInvariant()] = $true }

foreach ($f in Get-ChildItem -LiteralPath $source -Recurse -File) {
    $rel = $f.FullName.Substring($source.Length + 1)
    $to = Join-Path $BuildDir $rel
    New-Item -ItemType Directory -Force (Split-Path $to -Parent) | Out-Null
    Copy-Item -LiteralPath $f.FullName -Destination $to -Force
    Add-Expected $to
}

& $Python -I (Join-Path $here 'tools\derive.py') $Installed $BuildDir
if ($LASTEXITCODE -ne 0) { throw 'derive.py failed' }
foreach ($f in Get-ChildItem -LiteralPath (Join-Path $BuildDir 'NaturalResources') -Recurse -File -Filter '*InFlower*') { Add-Expected $f.FullName }
foreach ($sub in 'Goods', 'GoodCollections') { $d = Join-Path $BuildDir $sub; if (Test-Path $d) { foreach ($f in Get-ChildItem -LiteralPath $d -Recurse -File -Filter '*PandabornBambooSeed*') { Add-Expected $f.FullName }; foreach ($f in Get-ChildItem -LiteralPath $d -Recurse -File -Filter '*PandabornProtoEvents*') { Add-Expected $f.FullName } } }
Add-Expected (Join-Path $BuildDir 'Buildings\Pandaborn\Wellbeing\PandabornFestivalSquare\PandabornFestivalSquare.Inkpaws.blueprint.json')

$locSource = Join-Path $repo 'src\code\Pandaborn.Festival\mod'
foreach ($f in Get-ChildItem -LiteralPath $locSource -Recurse -File) {
    $to = Join-Path $BuildDir $f.FullName.Substring($locSource.Length + 1)
    New-Item -ItemType Directory -Force (Split-Path $to -Parent) | Out-Null
    Copy-Item -LiteralPath $f.FullName -Destination $to -Force
    Add-Expected $to
}

# compile against exactly the Core (and Specs) that will run
$refDir = 'E:\PandabornDev\build\obj\proto-events-ref'
New-Item -ItemType Directory -Force $refDir | Out-Null
Copy-Item -LiteralPath (Join-Path $Installed 'Scripts\Pandaborn.Core.bin') -Destination (Join-Path $refDir 'Pandaborn.Core.dll') -Force
$specsBin = Join-Path $Installed 'Scripts\Pandaborn.Specs.bin'
Copy-Item -LiteralPath $specsBin -Destination (Join-Path $refDir 'Pandaborn.Specs.dll') -Force
$specsText = [Text.Encoding]::ASCII.GetString([IO.File]::ReadAllBytes($specsBin))
$shared = $specsText.Contains('PandabornFestivalSpec')
Write-Host ("event specs in the installed Pandaborn.Specs: " + $shared)

$project = Join-Path $here 'src\PandabornProtoEvents.csproj'
$log = & dotnet build $project -c Release -v q --nologo "-p:ModOut=$BuildDir" "-p:RefDir=$refDir" "-p:EventsSpecsInShared=$($shared.ToString().ToLowerInvariant())" 2>&1
if ($LASTEXITCODE -ne 0) { $log | ForEach-Object { Write-Host $_ -ForegroundColor Red }; throw 'events dev mod build failed' }
Add-Expected (Join-Path $BuildDir 'Scripts\PandabornProtoEvents.dll')

# the shipped modules on their own: required-API lists and the generated half of FEATURE.md
$scratch = 'E:\PandabornDev\build\proto\events-modules'
foreach ($m in 'Pandaborn.Festival', 'Pandaborn.Flowering') {
    $csproj = Join-Path $repo "src\code\$m\$m.csproj"
    $mlog = & dotnet build $csproj -c Release -v q --nologo "-p:ModOut=$scratch" 2>&1
    if ($LASTEXITCODE -ne 0) { $mlog | ForEach-Object { Write-Host $_ -ForegroundColor Red }; throw "$m build failed" }
}

foreach ($f in Get-ChildItem -LiteralPath $BuildDir -Recurse -File) {
    $rel = $f.FullName.Substring($BuildDir.Length + 1)
    if (-not $expected.ContainsKey($rel.ToLowerInvariant())) { Remove-Item -LiteralPath $f.FullName -Force; Write-Host "removed stale $rel" }
}
Write-Host "Built $BuildDir ($($expected.Count) files); modules in $scratch" -ForegroundColor Green
