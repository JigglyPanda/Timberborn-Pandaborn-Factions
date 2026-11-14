<#
.SYNOPSIS
  One command for the Pandaborn - Factions build: pin, generate, validate, code, bundles, assemble, install, test,
  package, all.

.DESCRIPTION
  powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 <stage> [options]

  pin       Compare the installed game, its Unity version and the vanilla blueprint dump with catalogue/vanilla.pin.json.
            -Accept rewrites the pin (after reviewing tools/game_diff.py).
  generate  catalogue/ -> E:\PandabornDev\build\gen\PandabornFactions (blueprints, collections, modifiers, loc), with
            .provenance.json, .report.json and .grid.json next to it. -Lock appends new ids to catalogue/ids.lock.json;
            -DryRun prints the diff and writes nothing; -AcceptPin generates against a game that differs from the pin.
  models    Runs every art/models/<Id>/build.py (the building kit; -Plants adds art/plants/<Id>/build.py) with the
            art venv into E:\PandabornDev\build\models\<Id>. The meshes never enter git; assemble copies the
            ones the catalogue adopts (model = "<Id>") into the mod, from <GenDir>.models.json.
  code      Builds src/code (Bootstrap, Specs, Core, every module; the Look module brings the pandabornlook bundle)
            into E:\PandabornDev\build\code, and dumps the mod's own spec classes for the validator. On by default;
            -NoCode builds the data-only fallback (the mod must still be playable, with the Folktails look).
  bundles   Copies every built Pandaborn asset bundle (pandaborn*_win / _mac, never renamed) from -BundleDirs into the
            staging folder: today the plants (E:\PandabornDev\build\plants\AssetBundles, tools/build_plants.ps1).
            The look bundle comes with the code. Fails when an adopted model needs a bundle that is not built.
  assemble  Mirrors mod/PandabornFactions (hand-written files), the generated data, the two panda body meshes (not in
            git) and the code/bundle outputs into the staging folder E:\PandabornDev\build\stage\PandabornFactions.
            A generated file landing on a hand-written one is an error. Nothing installed is touched.
  validate  tools/validate.py on the staging folder (schema, ids, lock, needs, assets...).
  install   Mirrors the validated staging folder into E:\PandabornDev\build\PandabornFactions (the folder the game's Mods
            junction points at) and makes the junction, exactly as tools/build.ps1 always did. Refuses if validation
            failed in this run. Never touches any other Mods entry and never replaces a real folder.
  test      tools/run_game_test.ps1 -Faction Inkpaws with the generated grid request (every placeable template),
            on Plains with -OnlyMods JigglyPanda.PandabornFactions. -TestArgs passes more arguments.
  package   Copies the staging folder to E:\PandabornDev\build\package\PandabornFactions and zips it (mod.io).
  all       pin, models, generate, code, bundles, assemble, validate, install. (test and package only when named.)

  Exit code 0 when every requested stage passed.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 all
  powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 generate -DryRun
  powershell -ExecutionPolicy Bypass -File tools\pandaborn.ps1 generate,assemble,validate
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)][string[]]$Stage = @('all'),
    [switch]$Accept,
    [switch]$AcceptPin,
    [switch]$Lock,
    [switch]$DryRun,
    [switch]$NoCode,
    [switch]$WithCode,      # kept for old callers: code is on by default now
    [switch]$WithBundles,   # kept for old callers: bundles are always copied
    [switch]$NoLink,
    [switch]$Plants,
    [string]$ArtPython = 'E:\PandabornDev\tools\venv\Scripts\python.exe',
    [string]$Catalogue = '',
    [string]$GenDir = 'E:\PandabornDev\build\gen\PandabornFactions',
    [string]$StageDir = 'E:\PandabornDev\build\stage\PandabornFactions',
    [string]$InstallDir = 'E:\PandabornDev\build\PandabornFactions',
    [string]$PackageDir = 'E:\PandabornDev\build\package',
    [string[]]$BundleDirs = @('E:\PandabornDev\build\plants\AssetBundles'),
    [string]$MeshSource = 'E:\PandabornDev\assets\Pandaborn-Reskin-release\Characters\Beaver',
    [string]$RingtailMeshSource = 'E:\PandabornDev\build\characters\out',
    [string]$ModsDir = 'C:\Users\Israel Gonzalez\Documents\Timberborn\Mods',
    [string]$LinkName = 'PandabornFactions',
    [string[]]$TestArgs = @()
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$source = Join-Path $repo 'mod\PandabornFactions'
$env:PYTHONDONTWRITEBYTECODE = '1'
$stages = @($Stage | ForEach-Object { $_ -split ',' } | Where-Object { $_ } | ForEach-Object { $_.Trim().ToLowerInvariant() })
if ($stages -contains 'all') { $stages = @('pin', 'models', 'generate', 'code', 'bundles', 'assemble', 'validate', 'install') + @($stages | Where-Object { $_ -ne 'all' }) }
$known = 'pin', 'models', 'generate', 'validate', 'code', 'bundles', 'assemble', 'install', 'test', 'package'
foreach ($s in $stages) { if ($known -notcontains $s) { throw "unknown stage '$s' (stages: $($known -join ', '), all)" } }

# large binaries that live outside git: staging-relative path -> source file
$meshes = [ordered]@{
    'Characters\Pandaborn\InkpawAdult.Model.timbermesh' = Join-Path $MeshSource 'BeaverAdult.Model.timbermesh'
    'Characters\Pandaborn\InkpawChild.Model.timbermesh' = Join-Path $MeshSource 'BeaverChild.Model.timbermesh'
}
# the Ringtail bodies (ringtail-body lane, docs/tech/ringtail-body.md), shipped only when the generated data has the
# Ringtail templates (catalogue/rules.toml [modules] Ringtails)
$ringtailMeshes = [ordered]@{
    'Characters\Pandaborn\RingtailAdult.Model.timbermesh' = Join-Path $RingtailMeshSource 'RingtailAdult.Model.timbermesh'
    'Characters\Pandaborn\RingtailChild.Model.timbermesh' = Join-Path $RingtailMeshSource 'RingtailChild.Model.timbermesh'
}

function Say([string]$text, [string]$color = 'Gray') { Write-Host $text -ForegroundColor $color }

function Get-Python {
    foreach ($name in 'python', 'py') {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        $pre = @(); if ($name -eq 'py') { $pre = @('-3') }
        $v = & $cmd.Source @pre -c "import sys; print(sys.version_info >= (3, 11))" 2>$null
        if ($v -eq 'True') { return , @($cmd.Source) + $pre }
    }
    throw 'Python 3.11 or newer not found (the generator needs tomllib)'
}
$py = Get-Python
function Invoke-Py([string[]]$arguments) {
    $exe = $py[0]; $pre = @($py | Select-Object -Skip 1)
    & $exe @pre -I @arguments | Out-Host
    return $LASTEXITCODE
}

function Copy-IfChanged([string]$from, [string]$to) {
    $src = Get-Item -LiteralPath $from
    if (Test-Path -LiteralPath $to) {
        $dst = Get-Item -LiteralPath $to
        if ($dst.Length -eq $src.Length -and $dst.LastWriteTimeUtc -eq $src.LastWriteTimeUtc) { return $false }
    }
    $dir = Split-Path $to -Parent
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force $dir | Out-Null }
    Copy-Item -LiteralPath $from -Destination $to -Force
    return $true
}

# Makes $dest an exact mirror of the given (relative path -> source file) map. Returns counts.
function Sync-Tree([string]$dest, $map) {
    if (-not (Test-Path $dest)) { New-Item -ItemType Directory -Force $dest | Out-Null }
    $dest = (Resolve-Path $dest).Path
    $copied = 0; $removed = 0
    foreach ($rel in $map.Keys) { if (Copy-IfChanged $map[$rel] (Join-Path $dest $rel)) { $copied++ } }
    $want = @{}; foreach ($rel in $map.Keys) { $want[$rel.ToLowerInvariant()] = $true }
    foreach ($f in Get-ChildItem -LiteralPath $dest -Recurse -File -Force) {
        $rel = $f.FullName.Substring($dest.Length + 1)
        if (-not $want.ContainsKey($rel.ToLowerInvariant())) { Remove-Item -LiteralPath $f.FullName -Force; $removed++ }
    }
    Get-ChildItem -LiteralPath $dest -Recurse -Directory | Sort-Object { $_.FullName.Length } -Descending |
        Where-Object { -not (Get-ChildItem -LiteralPath $_.FullName -Force) } |
        ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force }
    return @{ files = $map.Count; copied = $copied; removed = $removed }
}

function Add-Tree($map, [string]$root, [string]$origin, $origins) {
    if (-not (Test-Path -LiteralPath $root)) { return }
    $root = (Resolve-Path $root).Path
    foreach ($f in Get-ChildItem -LiteralPath $root -Recurse -File) {
        $rel = $f.FullName.Substring($root.Length + 1)
        $k = $rel.ToLowerInvariant()
        if ($origins.ContainsKey($k)) { throw "assemble: $rel comes from both $($origins[$k]) and $origin. Generated files must not be hand-written too." }
        $origins[$k] = $origin
        $map[$rel] = $f.FullName
    }
}

$failed = @()
$validated = $false
$codeOut = Join-Path (Split-Path $StageDir -Parent) 'code\PandabornFactions'
$bundleOut = Join-Path (Split-Path $StageDir -Parent) 'bundles\PandabornFactions'

foreach ($s in $stages) {
    Say "== $s" 'Cyan'
    switch ($s) {
        'pin' {
            $a = @((Join-Path $repo 'src\gen\generate.py'), 'pin'); if ($Accept) { $a += '--accept' }
            $code = Invoke-Py $a
            if ($code -ne 0) { $failed += $s; if (-not $AcceptPin) { break } }
        }
        'generate' {
            $a = @((Join-Path $repo 'src\gen\generate.py'), '--out', $GenDir)
            if ($Catalogue) { $a += @('--catalogue', $Catalogue) }
            if ($Lock) { $a += '--lock' }; if ($DryRun) { $a += '--dry-run' }; if ($NoCode) { $a += '--no-code' }; if ($AcceptPin -or $Accept) { $a += '--accept-pin' }
            if ((Invoke-Py $a) -ne 0) { $failed += $s; break }
        }
        'models' {
            if (-not (Test-Path -LiteralPath $ArtPython)) { Say "models: art Python not found: $ArtPython" 'Red'; $failed += $s; break }
            $env:TEMP = 'E:\PandabornDev\tools\tmp'; $env:TMP = $env:TEMP
            $roots = @('art' + [IO.Path]::DirectorySeparatorChar + 'models'); if ($Plants) { $roots += 'art' + [IO.Path]::DirectorySeparatorChar + 'plants' }
            $built = 0; $bad = @()
            foreach ($root in $roots) {
                foreach ($script in Get-ChildItem -Path (Join-Path $repo $root) -Filter build.py -Recurse -Depth 1 -ErrorAction SilentlyContinue) {
                    $out = & $ArtPython $script.FullName 2>&1
                    if ($LASTEXITCODE -ne 0) { $bad += $script.Directory.Name; $out | Select-Object -Last 5 | ForEach-Object { Say "  $_" 'Red' } }
                    else { $built++ }
                }
            }
            Say "models: $built built into E:\PandabornDev\build\models$(if ($bad) { '; FAILED: ' + ($bad -join ', ') })"
            if ($bad) { $failed += $s; break }
        }
        'code' {
            if ($NoCode) { Say 'code: skipped (-NoCode: data-only fallback build)' 'DarkYellow'; continue }
            if (Test-Path $codeOut) { Remove-Item -Recurse -Force $codeOut }
            New-Item -ItemType Directory -Force $codeOut | Out-Null
            $log = & dotnet build (Join-Path $repo 'src\code\Pandaborn.Code.sln') -c Release -v q --nologo "-p:ModOut=$codeOut" 2>&1
            if ($LASTEXITCODE -ne 0) { $log | ForEach-Object { Say "  $_" 'Red' }; $failed += $s; break }
            Say "code: built into $codeOut"
            # ship only the modules whose data the catalogue has switched on (rules.toml [modules]); a module without
            # its data would do nothing, and validate --release refuses it
            $reportFile = "$GenDir.report.json"
            if (Test-Path -LiteralPath $reportFile) {
                $on = @((Get-Content -LiteralPath $reportFile -Raw | ConvertFrom-Json).modules.on)
                $mt = Join-Path $codeOut 'Modules\modules.txt'
                if (Test-Path -LiteralPath $mt) {
                    $kept = @(); $dropped = @()
                    foreach ($line in Get-Content -LiteralPath $mt) {
                        $id = ($line -split '\s+')[0]
                        if ($line.Trim() -eq '' -or $line.TrimStart().StartsWith('#') -or $on -contains $id) { $kept += $line; continue }
                        $dropped += $id
                        $file = ($line -split '\s+')[1]
                        foreach ($f in @($file, ($file -replace '\.bin$', '.api.txt'))) {
                            $pth = Join-Path $codeOut ('Modules\' + $f); if (Test-Path -LiteralPath $pth) { Remove-Item -LiteralPath $pth -Force }
                        }
                    }
                    [IO.File]::WriteAllLines($mt, [string[]]$kept)
                    if ($dropped) { Say "code: modules left out until their data is switched on: $($dropped -join ', ')" 'DarkYellow' }
                }
            }
            # the mod's own spec classes, for the validator (.bin files are assemblies loaded from bytes)
            $dlls = Join-Path (Split-Path $codeOut -Parent) 'code-dlls'
            if (Test-Path $dlls) { Remove-Item -Recurse -Force $dlls }
            New-Item -ItemType Directory -Force $dlls | Out-Null
            foreach ($f in Get-ChildItem -LiteralPath $codeOut -Recurse -File | Where-Object { $_.Extension -in '.bin', '.dll' }) {
                Copy-Item -LiteralPath $f.FullName (Join-Path $dlls ($f.BaseName + '.dll'))
            }
            $modSchema = Join-Path (Split-Path $codeOut -Parent) 'code-schema.json'
            $log = & dotnet run --project (Join-Path $repo 'tools\schema') -c Release -- --include $dlls --out $modSchema 2>&1
            if ($LASTEXITCODE -ne 0) { $log | ForEach-Object { Say "  $_" 'Red' }; $failed += $s; break }
            Say "code: spec schema with the mod's own classes in $modSchema"
        }
        'bundles' {
            if (Test-Path $bundleOut) { Remove-Item -Recurse -Force $bundleOut }
            New-Item -ItemType Directory -Force (Join-Path $bundleOut 'AssetBundles') | Out-Null
            $n = 0; $have = @{}
            foreach ($dir in $BundleDirs) {
                foreach ($f in Get-ChildItem -LiteralPath $dir -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^pandaborn.*_(win|mac)$' -and $_.Name -notmatch '^pandabornlook_' }) {
                    Copy-Item -LiteralPath $f.FullName (Join-Path $bundleOut "AssetBundles\$($f.Name)"); $n++
                    $have[($f.Name -replace '_(win|mac)$', '')] = $true
                }
            }
            $manifest = "$GenDir.models.json"
            $needed = @(); if (Test-Path -LiteralPath $manifest) { $needed = @((Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json).bundles) }
            $missingB = @($needed | Where-Object { $_ -and -not $have.ContainsKey($_) })
            Say "bundles: $n file(s) from $($BundleDirs -join ', ')"
            if ($missingB.Count -gt 0) { Say "bundles: adopted models need bundle(s) not built: $($missingB -join ', ') (tools/build_plants.ps1)" 'Red'; $failed += $s; break }
        }
        'assemble' {
            if (-not (Test-Path (Join-Path $GenDir 'Factions'))) { Say "assemble: no generated data in $GenDir (run generate first)" 'Red'; $failed += $s; break }
            $map = [ordered]@{}; $origins = @{}
            Add-Tree $map $source 'mod/PandabornFactions' $origins
            Add-Tree $map $GenDir 'generated' $origins
            if (-not $NoCode) {
                if (-not (Test-Path (Join-Path $codeOut 'Scripts'))) { Say "assemble: no code build in $codeOut (run the code stage, or pass -NoCode)" 'Red'; $failed += $s; break }
                Add-Tree $map $codeOut 'code' $origins
            }
            # meshes of the models the catalogue adopts (built by the models stage, outside git)
            $manifest = "$GenDir.models.json"
            if (Test-Path -LiteralPath $manifest) {
                $mm = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
                $missingMesh = @()
                foreach ($p in $mm.files.PSObject.Properties) {
                    $rel = $p.Name.Replace('/', [string][IO.Path]::DirectorySeparatorChar)
                    if (-not (Test-Path -LiteralPath $p.Value)) { $missingMesh += $p.Value; continue }
                    $k = $rel.ToLowerInvariant()
                    if ($origins.ContainsKey($k)) { throw "assemble: $rel comes from both $($origins[$k]) and models" }
                    $origins[$k] = 'models'; $map[$rel] = $p.Value
                }
                if ($missingMesh) { Say ("assemble: {0} model mesh(es) missing; run the models stage first: {1}" -f $missingMesh.Count, ($missingMesh | Select-Object -First 3) -join ', ') 'Red'; $failed += $s; break }
            }
            if (Test-Path $bundleOut) { Add-Tree $map $bundleOut 'bundles' $origins }
            $allMeshes = [ordered]@{}; foreach ($k in $meshes.Keys) { $allMeshes[$k] = $meshes[$k] }
            if (Test-Path -LiteralPath (Join-Path $GenDir 'Characters\Pandaborn\RingtailAdult.Inkpaws.blueprint.json')) {
                foreach ($k in $ringtailMeshes.Keys) { $allMeshes[$k] = $ringtailMeshes[$k] }
            }
            foreach ($rel in $allMeshes.Keys) {
                $from = $allMeshes[$rel]
                if (-not (Test-Path -LiteralPath $from)) { throw "large mesh missing: $from" }
                $fs = [IO.File]::OpenRead($from); try { $b0 = $fs.ReadByte(); $b1 = $fs.ReadByte() } finally { $fs.Dispose() }
                if ($b0 -ne 0x78 -or $b1 -ne 0x9C) { throw "$from does not start with zlib header 78 9C" }
                $map[$rel] = $from
            }
            $r = Sync-Tree $StageDir $map
            Say ("assemble: {0} files in {1} ({2} copied, {3} removed)" -f $r.files, $StageDir, $r.copied, $r.removed)
        }
        'validate' {
            $a = @((Join-Path $repo 'tools\validate.py'), '--mod', $StageDir, '--quiet')
            if ($Catalogue) { $a += @('--lock', (Join-Path $Catalogue 'ids.lock.json')) }
            $modSchema = Join-Path (Split-Path $codeOut -Parent) 'code-schema.json'
            if (-not $NoCode -and (Test-Path $modSchema)) { $a += @('--mod-schema', $modSchema) }
            if ((Invoke-Py $a) -ne 0) { $failed += $s; break }
            $validated = $true
            # report only: numbers in the balance model's stat sheet the catalogue has not carried over
            $null = Invoke-Py @((Join-Path $repo 'src\gen\import_statsheet.py'), '--check')
        }
        'install' {
            if ($failed.Count -gt 0) { Say "install: refused, earlier stages failed: $($failed -join ', ')" 'Red'; $failed += $s; break }
            if (-not $validated) {
                $a = @((Join-Path $repo 'tools\validate.py'), '--mod', $StageDir, '--quiet')
                $modSchema = Join-Path (Split-Path $codeOut -Parent) 'code-schema.json'
                if (-not $NoCode -and (Test-Path $modSchema)) { $a += @('--mod-schema', $modSchema) }
                if ((Invoke-Py $a) -ne 0) { Say 'install: refused, the staging folder does not validate' 'Red'; $failed += $s; break }
                $validated = $true
            }
            $map = [ordered]@{}; $origins = @{}
            Add-Tree $map $StageDir 'stage' $origins
            $r = Sync-Tree $InstallDir $map
            Say ("install: {0} files in {1} ({2} copied, {3} removed)" -f $r.files, $InstallDir, $r.copied, $r.removed)
            if ($NoLink) { continue }
            if (-not (Test-Path -LiteralPath $ModsDir -PathType Container)) { throw "Mods folder not found: $ModsDir" }
            $InstallDirFull = (Resolve-Path $InstallDir).Path
            $link = Join-Path $ModsDir $LinkName
            $item = Get-Item -LiteralPath $link -Force -ErrorAction SilentlyContinue
            if ($item) {
                if (-not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
                    throw "$link exists and is a real folder, not a junction. Not touching it; move it away by hand if it is stale."
                }
                $target = @($item.Target)[0]
                if ($target -and ($target -eq $InstallDirFull -or (Resolve-Path -LiteralPath $target -ErrorAction SilentlyContinue).Path -eq $InstallDirFull)) {
                    Say "link: $link -> $InstallDirFull (already in place)"; continue
                }
                cmd /c rmdir "$link" | Out-Null
                if (Test-Path -LiteralPath $link) { throw "could not remove the old junction $link" }
            }
            New-Item -ItemType Junction -Path $link -Target $InstallDirFull | Out-Null
            Say "link: $link -> $InstallDirFull (created)"
        }
        'test' {
            $grid = "$GenDir.grid.json"
            if (-not (Test-Path $grid)) { Say "test: $grid missing (run generate)" 'Red'; $failed += $s; break }
            $a = @('-ExecutionPolicy', 'Bypass', '-File', (Join-Path $repo 'tools\run_game_test.ps1'), '-Faction', 'Inkpaws',
                   '-Map', 'Plains', '-OnlyMods', 'JigglyPanda.PandabornFactions', '-RequestJson', $grid, '-RunSeconds', '300',
                   '-NoBatchControl', '-Screenshots', 'overview@end', '-TimeoutSeconds', '1200', '-WaitForGameSeconds', '7200') + $TestArgs
            & powershell @a
            if ($LASTEXITCODE -ne 0) { $failed += $s }
        }
        'package' {
            # release rules: a missing _mac bundle twin is an error here (dev stages only warn)
            $a = @((Join-Path $repo 'tools\validate.py'), '--mod', $StageDir, '--quiet', '--release')
            $modSchema = Join-Path (Split-Path $codeOut -Parent) 'code-schema.json'
            if (-not $NoCode -and (Test-Path $modSchema)) { $a += @('--mod-schema', $modSchema) }
            if ((Invoke-Py $a) -ne 0) { Say 'package: refused, the staging folder fails the release rules' 'Red'; $failed += $s; break }
            $out = Join-Path $PackageDir 'PandabornFactions'
            $map = [ordered]@{}; $origins = @{}
            Add-Tree $map $StageDir 'stage' $origins
            $r = Sync-Tree $out $map
            $zip = Join-Path $PackageDir 'PandabornFactions.zip'
            if (Test-Path $zip) { Remove-Item -Force $zip }
            Compress-Archive -Path $out -DestinationPath $zip
            Say ("package: {0} files in {1}; {2}" -f $r.files, $out, $zip)
        }
    }
    if ($failed.Count -gt 0) { break }   # a failed stage stops the run
}
if ($failed.Count -gt 0) { Say "FAILED: $($failed -join ', ')" 'Red'; exit 1 }
Say "OK: $($stages -join ', ')" 'Green'
exit 0
