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

  -Staged (the install gate, tools\pandaborn.ps1 gate): the copy is the source folder as it is. Nothing is built from
  src/code, no module is added, no fragment is merged, no probe and no bundle is brought in: Scripts, Modules (with the
  source's own modules.txt) and AssetBundles are the source's files, byte for byte. Only what a second copy needs to
  load next to the installed mod is changed: manifest.json (Id and Name). The gate then tests the code that install
  will copy. Every file that differs from the source is listed in E:\PandabornDev\build\proto\<Name>.devcopy.json
  (written next to the copy, not inside it), with the hash of the source's code files.
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
    [switch]$HardLinks,
    # the copy is the source as it is, with only the manifest changed (see the description)
    [switch]$Staged,
    # where copies are built; only for trials of this script in a scratch folder
    [string]$ProtoRoot = 'E:\PandabornDev\build\proto'
)
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$repo = (Resolve-Path (Join-Path $here '..\..')).Path
# The target folder is cleared below: the name must be one plain folder name, and the folder must sit directly in the
# proto root (an empty name would clear the whole root, '..\x' a folder outside it).
if ([string]::IsNullOrWhiteSpace($Name) -or [IO.Path]::IsPathRooted($Name) -or $Name -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$' -or $Name.EndsWith('.')) {
    throw "-Name '$Name' refused: one folder name of letters, digits, '.', '_' and '-' (no path, not empty)"
}
$protoRootFull = [IO.Path]::GetFullPath($ProtoRoot).TrimEnd('\')
$out = Join-Path $protoRootFull $Name
$scratch = Join-Path $protoRootFull "$Name.code"
foreach ($d in $out, $scratch) {
    if ((Split-Path ([IO.Path]::GetFullPath($d)) -Parent).TrimEnd('\') -ne $protoRootFull) { throw "$d is not directly in $protoRootFull; refusing to clear it" }
}
if (-not (Test-Path (Join-Path $Source 'manifest.json'))) { throw "no installed mod build at $Source" }
$Source = (Resolve-Path -LiteralPath $Source).Path.TrimEnd('\')
if ($out -eq $Source -or $Source.StartsWith($out + '\', [StringComparison]::OrdinalIgnoreCase)) { throw "the source $Source is the target itself" }

# relative path and SHA-256 of files under $root (optionally only those whose lowercased relative path starts with one
# of $only, and without $skip), as one hash, sorted by relative path (the same function is in tools\pandaborn.ps1)
function Get-TreeHash([string]$root, [string[]]$only = @(), [string[]]$skip = @()) {
    $root = (Resolve-Path -LiteralPath $root).Path.TrimEnd('\')
    $lines = @(foreach ($f in Get-ChildItem -LiteralPath $root -Recurse -File) {
        $rel = $f.FullName.Substring($root.Length + 1)
        if ($rel -match '(^|\\)AssetBundles\.parked(\\|$)') { continue }
        $low = $rel.ToLowerInvariant()
        if ($skip -contains $low) { continue }
        if ($only.Count -gt 0 -and -not @($only | Where-Object { $low.StartsWith($_) })) { continue }
        $low + ':' + (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash
    })
    $lines = [string[]]$lines
    [Array]::Sort($lines, [StringComparer]::Ordinal)
    $sha =[Security.Cryptography.SHA256]::Create()
    return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes(($lines -join "`n")))) -replace '-', '')
}

if ($Staged) {
    if ($Variant.Count -gt 0 -or $HardLinks) { throw '-Staged takes the source as it is: no -Variant, no -HardLinks' }
    if (Test-Path -LiteralPath $out) {
        if ((Get-Item -LiteralPath $out -Force).LinkType) { throw "$out is a link; refusing to clear it" }
        Remove-Item -LiteralPath $out -Recurse -Force
    }
    New-Item -ItemType Directory -Force $out | Out-Null
    $copied = 0
    foreach ($f in Get-ChildItem -LiteralPath $Source -Recurse -File) {
        $rel = $f.FullName.Substring($Source.Length + 1)
        if ($rel -match '(^|\\)AssetBundles\.parked(\\|$)') { continue }   # never content (a second enabled copy parks its bundles)
        $to = Join-Path $out $rel
        New-Item -ItemType Directory -Force (Split-Path $to -Parent) | Out-Null
        Copy-Item -LiteralPath $f.FullName -Destination $to; $copied++
    }
    # the one substitution: a second copy cannot carry the installed mod's Id
    $substitutions = @()
    $sourceManifest = Get-Content -LiteralPath (Join-Path $Source 'manifest.json') -Raw -Encoding UTF8
    $manifest = [ordered]@{
        Name = "Pandaborn - Factions dev copy ($Name)"; Version = '0.0.1'; Id = $Id; MinimumGameVersion = '1.1.0.0'
        Description = 'Development-only copy of Pandaborn - Factions (the staged build as it is). Never shipped. Art and code are AI-generated.'
        RequiredMods = @(); OptionalMods = @()
    }
    [IO.File]::WriteAllText((Join-Path $out 'manifest.json'), ($manifest | ConvertTo-Json -Depth 4), (New-Object Text.UTF8Encoding($false)))
    $substitutions += [ordered]@{ file = 'manifest.json'; change = "replaced: Id $Id and a dev-copy Name, so the copy loads next to the installed mod (switched off for the run). With an Id that is not the released one the bootstrap also reads pandaborn.dev.txt, if there is one." }
    if ($DevSwitch) {
        [IO.File]::WriteAllText((Join-Path $out 'pandaborn.dev.txt'), ($DevSwitch -replace ';', "`n"))
        $substitutions += [ordered]@{ file = 'pandaborn.dev.txt'; change = "written: $DevSwitch" }
    }
    # proof that nothing else differs: the copy without the substituted files hashes like the source without them
    $skip = @($substitutions | ForEach-Object { $_.file.ToLowerInvariant() })
    $sourceRest = Get-TreeHash $Source @() $skip
    $copyRest = Get-TreeHash $out @() $skip
    if ($sourceRest -ne $copyRest) { throw "the copy differs from $Source in more than $($skip -join ', ') (the source changed during the copy?)" }
    $codeParts = @('scripts\', 'modules\', 'assetbundles\')
    $info = [ordered]@{
        mode = 'staged'; name = $Name; source = $Source; copy = $out; builtUtc = (Get-Date).ToUniversalTime().ToString('o')
        manifestId = $Id
        substitutions = $substitutions
        restHash = $copyRest                                  # everything but the substituted files; equal in source and copy
        codeHash = (Get-TreeHash $out $codeParts)             # Scripts, Modules, AssetBundles as the copy carries them
        codeFiles = @(Get-ChildItem -LiteralPath $out -Recurse -File | ForEach-Object { $_.FullName.Substring($out.Length + 1) } |
                      Where-Object { $l = $_.ToLowerInvariant(); @($codeParts | Where-Object { $l.StartsWith($_) }).Count -gt 0 } | Sort-Object)
    }
    [IO.File]::WriteAllText("$out.devcopy.json", ($info | ConvertTo-Json -Depth 6), (New-Object Text.UTF8Encoding($false)))
    Write-Host "Built $out (staged: $copied files as they are; substituted: $($skip -join ', '); code hash $($info.codeHash.Substring(0, 12)))" -ForegroundColor Green
    exit 0
}
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
