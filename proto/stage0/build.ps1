<#
.SYNOPSIS
  Builds the stage-0 prototype mod (dev only) into E:\PandabornDev\build\proto\stage0.
.DESCRIPTION
  1. Mirrors proto/stage0/mod (manifest, faction merge, modifiers, tutorial, loc) into the build folder.
  2. Derives the two test templates from the vanilla dump (tools/derive.py) and draws the test "Poles" icon.
  3. Builds the runtime code (src/code: bootstrap, Specs, Core, Bell, Names) into the same folder, so the prototype
     carries the whole code architecture without touching mod/PandabornFactions.
  4. Builds the stage-0 probe (src) into <build>\Scripts.
  5. Removes stale files, including any pandaborn.dev.txt left by a test (pass -DevSwitch to write a fresh one).
  Never touches the Mods folder: tools/run_game_test.ps1 -ExtraMods junctions the folder for a run.
#>
[CmdletBinding()]
param(
    [string]$BuildDir = 'E:\PandabornDev\build\proto\stage0',
    [string]$Vanilla = 'E:\PandabornDev\reference\Blueprints',
    [string]$Python = 'E:\PandabornDev\tools\venv\Scripts\python.exe',
    # lines for pandaborn.dev.txt, e.g. 'force-off: Bell;simulate-missing-api: Names'
    [string]$DevSwitch = ''
)
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$repo = (Resolve-Path (Join-Path $here '..\..')).Path
$source = Join-Path $here 'mod'
New-Item -ItemType Directory -Force $BuildDir | Out-Null
$expected = @{}
function Expect([string]$rel) { $expected[$rel.ToLowerInvariant()] = $true }

foreach ($f in Get-ChildItem -LiteralPath $source -Recurse -File) {
    $rel = $f.FullName.Substring($source.Length + 1)
    $to = Join-Path $BuildDir $rel
    New-Item -ItemType Directory -Force (Split-Path $to -Parent) | Out-Null
    Copy-Item -LiteralPath $f.FullName -Destination $to -Force
    Expect $rel
}

& $Python -I (Join-Path $here 'tools\derive.py') $Vanilla $BuildDir
if ($LASTEXITCODE -ne 0) { throw 'derive.py failed' }
Expect 'NaturalResources\Pandaborn\Stage0\PandabornStage0Bamboo.Inkpaws.blueprint.json'
Expect 'Buildings\Pandaborn\Stage0\PandabornStage0Teahouse.Inkpaws.blueprint.json'

# the test icon: three green poles on transparent, 128 px (proves a modifier can point a vanilla good at a mod sprite)
Add-Type -AssemblyName System.Drawing
$iconRel = 'Sprites\Pandaborn\Stage0\PolesIcon.png'
$icon = Join-Path $BuildDir $iconRel
New-Item -ItemType Directory -Force (Split-Path $icon -Parent) | Out-Null
$bmp = New-Object System.Drawing.Bitmap 128, 128
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = 'AntiAlias'
$g.Clear([System.Drawing.Color]::Transparent)
foreach ($i in 0..2) {
    $x = 26 + $i * 28
    $brush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 70 + 30 * $i, 150 + 20 * $i, 60))
    $g.FillRectangle($brush, $x, 14 + 6 * $i, 18, 100 - 6 * $i)
    $dark = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 40, 90, 35))
    foreach ($y in 40, 72) { $g.FillRectangle($dark, $x - 1, $y + 4 * $i, 20, 5) }
}
$g.Dispose()
$bmp.Save($icon, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
[IO.File]::WriteAllText("$icon.meta.json", '{"isSprite": true}')
Expect $iconRel
Expect "$iconRel.meta.json"

$sln = Join-Path $repo 'src\code\Pandaborn.Code.sln'
$log = & dotnet build $sln -c Release -v q --nologo "-p:ModOut=$BuildDir" 2>&1
if ($LASTEXITCODE -ne 0) { $log | ForEach-Object { Write-Host $_ -ForegroundColor Red }; throw 'code build failed' }
foreach ($rel in 'Scripts\Pandaborn.Bootstrap.dll', 'Scripts\Pandaborn.Specs.bin', 'Scripts\Pandaborn.Specs.api.txt', 'Scripts\Pandaborn.Core.bin',
                 'Scripts\Pandaborn.Core.api.txt', 'Modules\modules.txt', 'Modules\Pandaborn.Bell.bin', 'Modules\Pandaborn.Bell.api.txt',
                 'Modules\Pandaborn.Names.bin', 'Modules\Pandaborn.Names.api.txt', 'Localizations\enUS_PandabornCore.csv',
                 'Localizations\enUS_PandabornBell.csv') { Expect $rel }
# Pandaborn.Look: module, its data, and its bundle when tools/build_look.ps1 -BundleName pandabornlook has made one
foreach ($rel in 'Modules\Pandaborn.Look.bin', 'Modules\Pandaborn.Look.api.txt', 'Factions\Pandaborn\Faction.Inkpaws.optional.blueprint.json',
                 'MaterialCollections\Pandaborn\MaterialCollection.PandabornLook.Inkpaws.blueprint.json',
                 'AssetBundles\pandabornlook_win', 'AssetBundles\pandabornlook_mac') { Expect $rel }

$probe = Join-Path $here 'src\PandabornProtoStage0.csproj'
$log = & dotnet build $probe -c Release -v q --nologo "-p:ModOut=$BuildDir" 2>&1
if ($LASTEXITCODE -ne 0) { $log | ForEach-Object { Write-Host $_ -ForegroundColor Red }; throw 'probe build failed' }
Expect 'Scripts\PandabornProtoStage0.dll'

foreach ($f in Get-ChildItem -LiteralPath $BuildDir -Recurse -File) {
    $rel = $f.FullName.Substring($BuildDir.Length + 1)
    if (-not $expected.ContainsKey($rel.ToLowerInvariant())) { Remove-Item -LiteralPath $f.FullName -Force; Write-Host "removed stale $rel" }
}
if ($DevSwitch) {
    [IO.File]::WriteAllText((Join-Path $BuildDir 'pandaborn.dev.txt'), ($DevSwitch -replace ';', "`n"))
    Write-Host "dev switch written: $DevSwitch" -ForegroundColor Yellow
}
Write-Host "Built $BuildDir ($($expected.Count) files)" -ForegroundColor Green
