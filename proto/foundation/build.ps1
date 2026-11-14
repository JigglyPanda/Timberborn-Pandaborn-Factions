<#
.SYNOPSIS
  Builds a dev copy of the installed faction mod carrying the code under test (dev only, never shipped).
.DESCRIPTION
  The installed mod (E:\PandabornDev\build\PandabornFactions) now ships its own bootstrap, and a second bootstrap in a
  layered dev mod would only be reported as a duplicate. So foundation tests run on a full copy instead:
    1. src/code is built into a scratch folder (that file list = everything the code contributes);
    2. the installed mod is mirrored into E:\PandabornDev\build\proto\<Name> without those files (everything is copied
       (-HardLinks links files of 1 MB or more instead));
    3. the fresh code, proto/foundation/mod fragments, the dev test module Pandaborn.DevCarrier and the probe are added;
    4. manifest Id JigglyPanda.PandabornFactionsDev (same faction, Inkpaws), name "<Name>".
  Run with: tools\run_game_test.ps1 -DisableMods JigglyPanda.PandabornFactions -ExtraMods E:\PandabornDev\build\proto\<Name>
  Never touches the installed mod or the Mods folder.
#>
[CmdletBinding()]
param(
    [string]$Name = 'pbfoundation',
    [string]$Source = 'E:\PandabornDev\build\PandabornFactions',
    [string]$Id = 'JigglyPanda.PandabornFactionsDev',
    # lines for pandaborn.dev.txt, ';' separated, e.g. 'force-off: DevCarrier;simulate-missing-member: Words'
    [string]$DevSwitch = '',
    # extra fragment folders (same layout as mod/), applied after mod/, e.g. proto\foundation\variants\nodata
    [string[]]$Variant = @(),
    # the sound lane's bundle (copied, not linked); '' skips it
    [string]$Sounds = 'E:\PandabornDev\build\sound\AssetBundles',
    # hard-link big files instead of copying them: faster, but the content lane's next install rewrites linked files in
    # place, so a copy built earlier ends up with new meshes under old blueprints (a crash seen in p3-bell-tutorial-1)
    [switch]$HardLinks
)
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$repo = (Resolve-Path (Join-Path $here '..\..')).Path
$out = Join-Path 'E:\PandabornDev\build\proto' $Name
$scratch = "E:\PandabornDev\build\proto\$Name.code"
if (-not (Test-Path (Join-Path $Source 'manifest.json'))) { throw "no installed mod build at $Source" }
foreach ($d in $out, $scratch) {
    if (Test-Path -LiteralPath $d) {
        if ((Get-Item -LiteralPath $d -Force).LinkType) { throw "$d is a link; refusing to clear it" }
        Remove-Item -LiteralPath $d -Recurse -Force
    }
    New-Item -ItemType Directory -Force $d | Out-Null
}

# 1. the code under test
$log = & dotnet build (Join-Path $repo 'src\code\Pandaborn.Code.sln') -c Release -v q --nologo "-p:ModOut=$scratch" 2>&1
if ($LASTEXITCODE -ne 0) { $log | ForEach-Object { Write-Host $_ -ForegroundColor Red }; throw 'code build failed' }
$log = & dotnet build (Join-Path $here 'devmodule\Pandaborn.DevCarrier.csproj') -c Release -v q --nologo "-p:ModOut=$scratch" 2>&1
if ($LASTEXITCODE -ne 0) { $log | ForEach-Object { Write-Host $_ -ForegroundColor Red }; throw 'dev module build failed' }
Add-Content (Join-Path $scratch 'Modules\modules.txt') "DevCarrier  Pandaborn.DevCarrier.bin  Dev test of the per-entity save carrier (never shipped)"
$codeFiles = @{}
foreach ($f in Get-ChildItem -LiteralPath $scratch -Recurse -File) { $codeFiles[$f.FullName.Substring($scratch.Length + 1).ToLowerInvariant()] = $true }

# 2. the installed mod without what the code contributes
$linked = 0; $copied = 0
foreach ($f in Get-ChildItem -LiteralPath $Source -Recurse -File) {
    $rel = $f.FullName.Substring($Source.Length + 1)
    $low = $rel.ToLowerInvariant()
    if ($codeFiles.ContainsKey($low) -or $low.StartsWith('scripts\') -or $low.StartsWith('modules\') -or $low -eq 'manifest.json' -or $low -eq 'pandaborn.dev.txt') { continue }
    $to = Join-Path $out $rel
    New-Item -ItemType Directory -Force (Split-Path $to -Parent) | Out-Null
    if ($HardLinks -and $f.Length -ge 1MB) { New-Item -ItemType HardLink -Path $to -Target $f.FullName | Out-Null; $linked++ }
    else { Copy-Item -LiteralPath $f.FullName -Destination $to; $copied++ }
}

# 3. code, fragments, probe
Copy-Item -Path (Join-Path $scratch '*') -Destination $out -Recurse -Force
foreach ($frag in @((Join-Path $here 'mod')) + @($Variant | ForEach-Object { (Resolve-Path $_).Path })) {
foreach ($f in Get-ChildItem -LiteralPath $frag -Recurse -File) {
    $rel = $f.FullName.Substring($frag.Length + 1)
    $to = Join-Path $out ($rel -replace '\.fragment\.json$', '.json')
    New-Item -ItemType Directory -Force (Split-Path $to -Parent) | Out-Null
    if ($rel -like '*.fragment.json') {
        # merge fragment: written as its own same-path file is impossible inside one mod, so merge into the copy here
        & E:\PandabornDev\tools\venv\Scripts\python.exe -I (Join-Path $here 'tools\merge.py') $to $f.FullName
        if ($LASTEXITCODE -ne 0) { throw "merging $rel failed" }
    } else { Copy-Item -LiteralPath $f.FullName -Destination $to -Force }
}
}
if ($Sounds -and (Test-Path (Join-Path $Sounds 'pandabornsounds_win'))) {
    foreach ($b in 'pandabornsounds_win', 'pandabornsounds_mac') { if (Test-Path (Join-Path $Sounds $b)) { Copy-Item (Join-Path $Sounds $b) (Join-Path $out "AssetBundles\$b") -Force } }
}
$log = & dotnet build (Join-Path $here 'src\PandabornFoundationProbe.csproj') -c Release -v q --nologo "-p:ModOut=$out" 2>&1
if ($LASTEXITCODE -ne 0) { $log | ForEach-Object { Write-Host $_ -ForegroundColor Red }; throw 'probe build failed' }

# 4. manifest
$manifest = [ordered]@{
    Name = "Pandaborn - Factions dev copy ($Name)"; Version = '0.0.1'; Id = $Id; MinimumGameVersion = '1.1.0.0'
    Description = 'Development-only copy of Pandaborn - Factions carrying the code under test. Never shipped. Art and code are AI-generated.'
    RequiredMods = @(); OptionalMods = @()
}
[IO.File]::WriteAllText((Join-Path $out 'manifest.json'), ($manifest | ConvertTo-Json -Depth 4), (New-Object Text.UTF8Encoding($false)))
if ($DevSwitch) {
    [IO.File]::WriteAllText((Join-Path $out 'pandaborn.dev.txt'), ($DevSwitch -replace ';', "`n"))
    Write-Host "dev switch written: $DevSwitch" -ForegroundColor Yellow
}
Remove-Item -LiteralPath $scratch -Recurse -Force
Write-Host "Built $out ($linked hard links, $copied copies, $($codeFiles.Count) code files)" -ForegroundColor Green
